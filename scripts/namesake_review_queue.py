#!/usr/bin/env python3
"""Review queue of cited-person name keys that may merge namesakes (2026-10-23).

The citation graph identifies a cited person by a name key (surname, first name, middle
initial) merged by catalogue evidence; nothing splits a key that gathers several people
('Richard White' of Stanford, Toronto and Sydney). Splits are decided by a person, in
``person-splits.csv``; this script only ranks candidates for that review.

Signal: within one person's works (as first author, each cited by ``--min-work`` or more strict
History PhDs), two works are linked when at least one strict PhD cites both. A key whose works
fall into two or more groups with no shared citing PhD, the second group cited by at least
``--min-minor`` PhDs, is a candidate. For each group the queue lists its PhDs, top works, citing
regions and dominant TF-IDF family. Disjoint readerships alone are weak evidence (one author writes for two communities; French and
English editions have different readers), so keys grounded in Wikidata are checked against that
person's own Wikidata works (P50, titles in every language, with editions): when every group has a
work the person wrote, the key is dropped as one author; when the main group matches and another
group does not, ``verdict`` = namesake_likely; other keys are ``unverified``. Read the titles and decide.

Input: a public release directory (``build_public_release.py``) and the main TF-IDF mixtures.
Output: ``summary/identity/namesake-review.csv``.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dissertation_citation_graph import title_key  # noqa: E402
from ground_cited_people_wikidata import literal, post, qid as qid_of  # noqa: E402
from network_layout import region  # noqa: E402

D = Path(__file__).resolve().parents[1] / 'data/field-research/dissertation-citations-2026-10-11'


STOP = {
    'fr': {'le', 'la', 'les', 'des', 'du', 'de', 'et', 'en', 'une', 'un', 'sur', 'dans', 'pour', 'aux', 'au'},
    'es': {'el', 'los', 'las', 'del', 'y', 'una', 'para', 'por', 'como', 'sobre'},
    'pt': {'o', 'os', 'as', 'do', 'da', 'dos', 'das', 'e', 'uma', 'para', 'sobre', 'como'},
    'de': {'der', 'die', 'das', 'und', 'des', 'ein', 'eine', 'zur', 'zum', 'im', 'von', 'mit', 'über'},
    'sv': {'och', 'att', 'av', 'för', 'om', 'med', 'på', 'till'},
    'en': {'the', 'and', 'of', 'in', 'a', 'an', 'to', 'for', 'on', 'from', 'with', 'how', 'its'},
}


def language(titles):
    """Most likely language of a group's titles by stopwords ('en' when unclear)."""
    score = Counter()
    for t in titles:
        words = re.findall(r"[^\W\d_]+", t.lower())
        for lang, stop in STOP.items():
            score[lang] += sum(w in stop for w in words)
    return score.most_common(1)[0][0] if score and score.most_common(1)[0][1] else 'en'


def divergence(a, b):
    """Jensen-Shannon divergence (base 2, 0-1) between two count profiles."""
    keys = set(a) | set(b)
    ta, tb = sum(a.values()) or 1, sum(b.values()) or 1
    js = 0.0
    for k in keys:
        p, q = a.get(k, 0) / ta, b.get(k, 0) / tb
        m = (p + q) / 2
        js += (p * math.log2(p / m) if p else 0) + (q * math.log2(q / m) if q else 0)
    return js / 2


DRAFT_FIELDS = ['decision', 'suggestion', 'person', 'work_title', 'new_person', 'new_name', 'qid', 'evidence', 'decided_by', 'date',
                'rank', 'stays_with_key', 'moves']


def write_drafts(out, top):
    """Draft ledger rows for the top candidates (person-splits-drafts.csv): one row per work title in the
    group that would move, with a blank decision. Rows already decided (accept or reject) are kept as
    they are; the builder applies only accepted rows. The group that moves is the one the grounded
    person's Wikidata works miss, else the smaller one."""
    path = D / 'person-splits-drafts.csv'
    kept, notes = [], {}
    if path.exists():
        with path.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get('decision', '').strip():
                    kept.append(r)
                elif r.get('suggestion'):
                    notes[r['person']] = r['suggestion']  # a reviewer's reading survives a rerun
    decided = {(r['person'], r['work_title']) for r in kept}
    new_rows = []
    for rank, r in enumerate([r for r in out if r['verdict'] != 'translation_likely'][:top], 1):
        surname = r['name'].split(',')[0].strip()
        given = r['name'].split(',', 1)[1].strip() if ',' in r['name'] else ''
        new_person = f"{r['person_key']}#{rank}"
        stays = f"{r['group1_works']} [{r['group1_regions']}; {r['group1_family']}]"
        moves = f"{r['group2_works']} [{r['group2_regions']}; {r['group2_family']}]"
        for t in r['_group2_all']:
            if (r['person_key'], t) in decided:
                continue
            new_rows.append(dict(decision='', suggestion=notes.get(r['person_key'], ''), person=r['person_key'], work_title=t[:120], new_person=new_person,
                                 new_name=f'{surname}, {given} (second person: rename)'.replace(',  (', ' ('), qid='',
                                 evidence=f"Namesake queue rank {rank} ({r['verdict']}, score {r['score']}): the works share no citing PhD; "
                                          f"group 2 is read by {r['group2_regions']}, group 1 by {r['group1_regions']}.",
                                 decided_by='', date='', rank=rank, stays_with_key=stays, moves=moves))
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=DRAFT_FIELDS)
        w.writeheader()
        w.writerows(kept + new_rows)
    print(f'draft ledger rows: {len(new_rows)} new for the top {top} candidates, {len(kept)} already decided -> {path.name}')


def rows(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, help='release directory (default: the latest under release/)')
    ap.add_argument('--min-work', type=int, default=2)
    ap.add_argument('--min-minor', type=int, default=5)
    ap.add_argument('--drafts', type=int, default=25, help='write draft ledger rows for the top N candidates (0: none)')
    args = ap.parse_args()
    rel = args.release or sorted((D / 'release').iterdir())[-1]
    strict = {r['dissertation_id']: region(r['country']) for r in rows(rel / 'dissertations.csv.gz') if r['in_analysis'] == 'True'}
    first = {}
    for r in rows(rel / 'authorship.csv.gz'):
        if r['position'] == '1':
            first[r['work_id']] = r['person_key']
    citing = defaultdict(set)
    for r in rows(rel / 'citations.csv.gz'):
        if r['dissertation_id'] in strict and r['work_id'] in first:
            citing[r['work_id']].add(r['dissertation_id'])
    title = {r['work_id']: r['title'] for r in rows(rel / 'works.csv.gz') if r['work_id'] in citing}
    people = {r['person_key']: r for r in rows(rel / 'people.csv.gz')}
    fam_dir = D / 'summary' / 'tfidf-families'
    fam_name = {f['id']: f['provisional_label'].split(' — ')[0] for f in json.load((fam_dir / 'families.json').open())['families']}
    dominant = {}
    with (fam_dir / 'dissertation-mixtures.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            dominant[r['dissertation_id'][2:]] = int(r['dominant_family'])
    works_of = defaultdict(list)
    for w, p in first.items():
        if len(citing[w]) >= args.min_work:
            works_of[p].append(w)
    out = []
    for p, ws in works_of.items():
        if len(ws) < 2:
            continue
        parent = {w: w for w in ws}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        holder = {}
        for w in ws:
            for d in citing[w]:
                if d in holder:
                    parent[find(w)] = find(holder[d])
                else:
                    holder[d] = w
        groups = defaultdict(list)
        for w in ws:
            groups[find(w)].append(w)
        comps = sorted(({'works': g, 'phds': set().union(*(citing[w] for w in g))} for g in groups.values()), key=lambda c: -len(c['phds']))
        if len(comps) < 2 or len(comps[1]['phds']) < args.min_minor:
            continue
        row = dict(person_key=p, name=people.get(p, {}).get('name', ''), qid=people.get(p, {}).get('qid', ''),
                   citing_phds=len(set().union(*(c['phds'] for c in comps))), groups=len(comps), minor_group_phds=len(comps[1]['phds']))
        row['_group_titles'] = [[title.get(w, '') for w in sorted(c['works'], key=lambda w: -len(citing[w]))[:8]] for c in comps[:3]]
        regs1, regs2 = Counter(strict[d] for d in comps[0]['phds']), Counter(strict[d] for d in comps[1]['phds'])
        fam1 = Counter(dominant[d] for d in comps[0]['phds'] if d in dominant)
        fam2 = Counter(dominant[d] for d in comps[1]['phds'] if d in dominant)
        lang1 = language(title.get(w, '') for w in comps[0]['works'])
        lang2 = language(title.get(w, '') for w in comps[1]['works'])
        row['region_divergence'] = round(divergence(regs1, regs2), 3)
        row['field_divergence'] = round(divergence(fam1, fam2), 3) if fam1 and fam2 else ''
        row['languages'] = f'{lang1}/{lang2}'
        for k, c in enumerate(comps[:3], 1):
            top = sorted(c['works'], key=lambda w: -len(citing[w]))[:3]
            regs = Counter(strict[d] for d in c['phds'])
            fams = Counter(fam_name.get(dominant[d], '') for d in c['phds'] if d in dominant)
            row[f'group{k}_phds'] = len(c['phds'])
            row[f'group{k}_works'] = ' | '.join(title.get(w, w)[:60] for w in top)
            row[f'group{k}_regions'] = ', '.join(f'{r} {n}' for r, n in regs.most_common(3))
            row[f'group{k}_family'] = fams.most_common(1)[0][0] if fams else ''
            row[f'_group{k}_all'] = sorted({title.get(w, '') for w in c['works'] if title.get(w)}, key=len)
        out.append(row)
    # Wikidata check: does each group contain a work the grounded person wrote?
    def same(a, b):
        short, long_ = sorted((a, b), key=len)
        return a == b or (len(short.split()) >= 3 and long_.startswith(short + ' '))
    qids = sorted({r['qid'] for r in out if r['qid']})
    own = defaultdict(set)
    for i in range(0, len(qids), 150):
        vals = ' '.join(f'wd:{q}' for q in qids[i:i + 150])
        for r in post(f"""SELECT ?h ?t WHERE {{ VALUES ?h {{ {vals} }} ?w wdt:P50 ?h .
            {{ ?w rdfs:label ?t }} UNION {{ ?w wdt:P1476 ?t }} UNION {{ ?e wdt:P629 ?w . ?e wdt:P1476 ?t }} }}"""):
            tk = title_key(literal(r['t']))
            if len(tk) >= 3:
                own[qid_of(r['h'])].add(tk)
        print(f'  Wikidata works for {min(i + 150, len(qids))}/{len(qids)} grounded keys', flush=True)
    kept = []
    for r in out:
        group_titles = r.pop('_group_titles')
        if not r['qid']:
            r['verdict'] = 'unverified'
            kept.append(r)
            continue
        titles = own.get(r['qid'], set())
        hit = [any(same(title_key(w), t) for w in g for t in titles) for g in group_titles]
        if all(hit):
            continue  # every group holds a work the grounded person wrote: one author
        r['verdict'] = 'wikidata_misses_minor' if hit[0] and not all(hit[1:]) else 'unverified'
        kept.append(r)
    out = kept
    for r in out:
        l1, l2 = r['languages'].split('/')
        if l1 != l2:
            r['verdict'] = 'translation_likely'  # the groups' titles are in different languages
        # review priority: different readerships (region, field), a Wikidata miss, and size of the minor group
        r['score'] = round(r['region_divergence'] + 0.5 * (r['field_divergence'] or 0)
                           + (0.3 if r['verdict'] == 'wikidata_misses_minor' else 0)
                           + 0.1 * math.log10(r['minor_group_phds']), 3)
    out.sort(key=lambda r: (r['verdict'] == 'translation_likely', -r['score']))
    dest = D / 'summary' / 'identity'
    dest.mkdir(parents=True, exist_ok=True)
    if args.drafts:
        write_drafts(out, args.drafts)
    for r in out:
        for k in [k for k in r if k.startswith('_group')]:
            r.pop(k)
    lead = ['verdict', 'score', 'region_divergence', 'field_divergence', 'languages']
    fields = lead + [k for k in dict.fromkeys(k for r in out for k in r) if k not in lead]
    with (dest / 'namesake-review.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f'{len(out)} candidate keys from {rel.name} ({Counter(r["verdict"] for r in out)}); written to {dest / "namesake-review.csv"}')
    for r in out[:25]:
        print(f"{r['score']:5} {r['verdict'][:10]:10} {r['minor_group_phds']:>4} {r['name'][:26]:26} {r['qid'] or '-':10} | {r['group1_works'][:50]} [{r['group1_regions']}] || {r['group2_works'][:50]} [{r['group2_regions']}]")


if __name__ == '__main__':
    main()
