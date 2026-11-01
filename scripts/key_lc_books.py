"""Key the authors of reviewed books through LC (Fable review 2026-11-01, step 4). Writes a proposal; never mints.

Input: the reviewed-book resolution (scripts/lc_resolve_authorities.py, credits.csv and authorities.csv). A
credit reaches an LC name authority only through the same book's LC record (LCCN or ISBN) and a heading
whose name agrees with the credit, so the authority is the book's author by LC's own cataloguing: identity
by works.

One person cluster per LC authority:
- anchor `lcnaf:<id>` (a public identifier: `established`);
- the registry individuals behind its credits (registry v12, any tier) as members `registry-v12:<id>`, and
  each individual's people (ORCID, QID, Open Library, atlas) that are already anchors in the log as anchors,
  so the cluster joins the key that holds them;
- a key whose Wikidata item names this LC authority (member `lcnaf-wikidata:<id>`) is joined when the
  names agree: two independent routes (LC's catalogue and Wikidata's P244) reach one authority. Keys that
  rejected a QID are left out (the claim may be the namesake's).

Refused (queued in review-queue.json, the authority left unkeyed):
- the cluster reaches a key that already holds a different LC authority, or that rejected this one;
- two authorities reach one key (one Open Library author, two LC people);
- the key's name is incompatible with the heading (`names_compatible`).
A cluster reaching two keys merges them only when every name agrees and no key holds another LC authority,
through the merge guard (pooled keys and keys in open review conflicts never merge).

**AHA dissertations by works.** An AHA dissertation author joins the authority when one of the authority's
catalogued reviewed books, or the first source its LC record cites (670), is that dissertation as published:
key_aha's `own_book` rule (compatible names, three or more shared content words making up 60% of the
shorter title, published no earlier than the year before the PhD). An authority matching several AHA
records, or an AHA record matching several authorities, joins none (queued).

    python3 scripts/key_lc_books.py --resolved data/field-research/lc-authorities-2026-10-30/reviews-2026-11-01 \\
        --out data/identifiers/lc-books-2026-11-01
"""
import argparse
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise, plan
from key_aha import AHA, own_book
from key_registry import names_compatible
from lc_authority_pilot import REGISTRY, UPSTREAM
from lc_canon_people import content
from merge_guard import guarded

KEYED = {'new_for_known_individual', 'new_for_unresolved_credit', 'agrees_with_registry'}
PEOPLE = ('orcid:', 'wd:', 'ol:', 'atlas:')


def label_of(heading):
    """'Siegel, Jonah, 1963-' -> 'Siegel, Jonah'."""
    h = re.sub(r',?\s*(approximately\s+|ca\.\s*)?\d{3,4}\??-(\d{3,4}\??)?\.?$', '', heading.strip())
    return h.rstrip(' .,')


def registry_people(registry, individuals):
    db = duckdb.connect(str(registry), read_only=True)
    db.execute('CREATE TEMP TABLE want(i VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(i,) for i in individuals])
    out = defaultdict(set)
    for i, node in db.execute('SELECT individual_id, node FROM individuals WHERE individual_id IN (SELECT i FROM want)').fetchall():
        out[i].add(node)
    return out


def anchor_of(node):
    return f'atlas:person:{node[6:]}' if node.startswith('atlas:') else node


def family_key(family):
    return ' '.join(content(family)) or family.lower()


def lc_works(credits, sources):
    """lcnaf -> [(content words, year)] of its reviewed books (the upstream book table) and its 670 first source."""
    db = duckdb.connect()
    books = {b: (t, int(y) if (y or '').isdigit() else None) for b, t, y in db.execute(
        f"SELECT book_id, coalesce(ol_title, book_title), pub_year4 FROM read_parquet('{UPSTREAM / 'books.parquet'}')").fetchall()}
    out = defaultdict(list)
    for c in credits:
        if c['book_id'] in books:
            t, y = books[c['book_id']]
            out[c['lcnaf']].append((set(content(t or '')), y))
    for lc, src in sources.items():
        m = re.match(r'(.+?),\s*(?:c|©)?(\d{4})\b', src or '')
        if m:
            out[lc].append((set(content(m.group(1))), int(m.group(2))))
    return {lc: [w for w in ws if len(w[0]) >= 3] for lc, ws in out.items()}


def aha_by_works(state, labels, works, records):
    """lcnaf -> AHA author anchor, where exactly one AHA dissertation is one of the authority's books."""
    cands = defaultdict(list)
    for lc, ws in works.items():
        label = label_of(labels.get(lc, ''))
        if ws and ', ' in label:
            cands[family_key(label.partition(', ')[0])].append((lc, label, ws))
    hits = defaultdict(set)
    for r in records:
        a = f'aha-phd:{r["id"]}'
        if a in state.anchor:
            for lc in own_book(r, cands):
                hits[lc].add(a)
    by_anchor = defaultdict(set)
    for lc, ans in hits.items():
        for a in ans:
            by_anchor[a].add(lc)
    out, queue = {}, []
    for lc, ans in sorted(hits.items()):
        if len(ans) == 1 and len(by_anchor[next(iter(ans))]) == 1:
            out[lc] = next(iter(ans))
        else:
            queue.append(dict(kind='aha_by_works_ambiguous', lcnaf=lc, aha=sorted(ans),
                              lcnaf_per_aha={a: sorted(by_anchor[a]) for a in ans}))
    return out, queue


def clusters_for(state, credits, labels, people, aha=None):
    by_lc = defaultdict(lambda: dict(individuals=set(), names=set()))
    for c in credits:
        by_lc[c['lcnaf']]['names'].add(c['credit_name'])
        if c['individual_id']:
            by_lc[c['lcnaf']]['individuals'].add(c['individual_id'])
    wd_claim = defaultdict(set)
    for k, ms in state.members.items():
        for m in ms:
            if m.startswith('lcnaf-wikidata:') and state.keys[k]['status'] in ('active', 'provisional') \
                    and not any(x.startswith('rejected:wd:') for x in ms):
                wd_claim[m.split(':', 1)[1]].add(k)
    rejected = {(m.split(':', 1)[1], k) for k, ms in state.members.items() for m in ms if m.startswith('lcnaf-rejected:')}
    rejected |= {(m.split(':', 2)[2], k) for k, ms in state.members.items() for m in ms if m.startswith('rejected:lcnaf:')}
    queue, report, out = [], Counter(), []
    for lc, v in sorted(by_lc.items()):
        label = label_of(labels.get(lc, ''))
        if not label:
            report['no_heading_label'] += 1
            continue
        anchor = f'lcnaf:{lc}'
        anchors, members = {anchor}, {f'registry-v12:{i}' for i in sorted(v['individuals'])}
        for i in v['individuals']:
            anchors |= {anchor_of(n) for n in people.get(i, ()) if n.startswith(PEOPLE) and anchor_of(n) in state.anchor}
        for k in sorted(wd_claim.get(lc, ())):
            if names_compatible(label, state.keys[k]['label']):
                anchors |= {a for a in state.keys[k]['anchors']} if anchor not in state.anchor else set()
                report['joined_by_wikidata_lc_claim'] += 1
            else:
                queue.append(dict(kind='wikidata_lc_claim_name_differs', lcnaf=lc, label=label, key=k,
                                  key_label=state.keys[k]['label']))
        if (aha or {}).get(lc):
            anchors.add(aha[lc])
            report['joined_aha_dissertation_by_works'] += 1
        if anchor in state.anchor:
            anchors = {anchor} | {a for a in anchors if state.anchor.get(a) == state.anchor[anchor]}
            report['lcnaf_already_keyed'] += 1
        keys = sorted({state.anchor[a] for a in anchors if a in state.anchor})
        problem = None
        for k in keys:
            held = {a for a in state.keys[k]['anchors'] if a.startswith('lcnaf:')}
            if held - {anchor}:
                problem = dict(kind='key_holds_different_lcnaf', key_lcnaf=sorted(held))
            elif (lc, k) in rejected:
                problem = dict(kind='key_rejected_this_lcnaf')
            elif not names_compatible(label, state.keys[k]['label']):
                problem = dict(kind='lcnaf_name_differs_from_key')
            if problem:
                problem.update(lcnaf=lc, label=label, key=k, key_label=state.keys[k]['label'], credits=sorted(v['names']))
                break
        if problem:
            queue.append(problem)
            report[problem['kind']] += 1
            continue
        out.append(dict(type='person', label=label, anchors=anchors, members=members, aliases=set(),
                        resolution='established', basis=f'LC catalogue: author of reviewed books ({lc})'))
    # two LC authorities reaching one key: one source person, two LC people; neither joins
    reach = defaultdict(list)
    for i, c in enumerate(out):
        for k in {state.anchor[a] for a in c['anchors'] if a in state.anchor}:
            reach[k].append(i)
    drop = set()
    for k, idx in reach.items():
        lcs = {a for i in idx for a in out[i]['anchors'] if a.startswith('lcnaf:')}
        if len(lcs) > 1:
            queue.append(dict(kind='several_lcnaf_reach_one_key', key=k, key_label=state.keys[k]['label'],
                              lcnaf=sorted(lcs), labels=[out[i]['label'] for i in idx]))
            drop |= set(idx)
            report['several_lcnaf_reach_one_key'] += 1
    out = [c for i, c in enumerate(out) if i not in drop]
    # an anchor new to the log, or an existing one, claimed by two clusters
    owners = defaultdict(list)
    for i, c in enumerate(out):
        for a in c['anchors']:
            if not a.startswith('lcnaf:'):
                owners[a].append(i)
    for a, idx in owners.items():
        if len(idx) > 1:
            for i in idx:
                out[i]['anchors'].discard(a)
            report['shared_person_anchor_dropped'] += 1
    report['clusters'] = len(out)
    return out, queue, report


def merge_rule(state):
    def ok(cluster, keys):
        lcs = {a for k in keys for a in state.keys[k]['anchors'] if a.startswith('lcnaf:')} | \
              {a for a in cluster['anchors'] if a.startswith('lcnaf:')}
        labels = [state.keys[k]['label'] for k in keys] + [cluster['label']]
        return len(lcs) == 1 and all(names_compatible(a, b) for a in labels for b in labels)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--resolved', type=Path, required=True, help='lc_resolve_authorities.py output directory')
    ap.add_argument('--registry', type=Path, default=REGISTRY)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with (args.resolved / 'credits.csv').open(encoding='utf-8') as f:
        credits = [r for r in csv.DictReader(f) if r['lcnaf'] and r['outcome'] in KEYED]
    with (args.resolved / 'authorities.csv').open(encoding='utf-8') as f:
        authorities = list(csv.DictReader(f))
    labels = {r['lcnaf']: r['label'] for r in authorities}
    people = registry_people(args.registry, {c['individual_id'] for c in credits if c['individual_id']})
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = list(csv.DictReader(f))
    aha, aha_queue = aha_by_works(state, labels, lc_works(credits, {r['lcnaf']: r['first_source'] for r in authorities}),
                                  records)
    clusters, queue, report = clusters_for(state, credits, labels, people, aha)
    queue = aha_queue + queue
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state)))
    materialise(state, dict(basis='lc books', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis=f'LC catalogue records of reviewed books ({args.resolved.name})', decided_by='build', ops=ops),
        ensure_ascii=False).encode() + b'\n'))
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(credits=len(credits), authorities=len({c['lcnaf'] for c in credits}), **dict(sorted(report.items())),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held), review_queue=len(queue) + len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
