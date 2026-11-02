"""The dissertation graph's own theses and their authors -> the key log (PID-PLAN.md v2, rollout step 6). Writes a proposal; never mints.

Reads data/field-research/dissertation-citations-2026-10-11/dissertations.csv (the theses whose bibliographies
build the graph) and, for US theses, the AHA record each harvest matched (`aha_id` in the harvest
records.jsonl files, by surname, year and title; see harvest_us_history_dissertations.match_aha).

- **Works.** Each thesis judged a History PhD (`eligibility` history_phd), or in the graph's analysis set,
  is a work anchored on `diss-thesis:<id>`. A thesis matched to an AHA record also carries `aha-diss:<record>`,
  so it joins that record's work key: one dissertation, two descriptions. Members: `year:<y>` and
  `awarded-by:i-N` when the institution slug reaches an institution key (`diss-inst:` aliases). 3,016
  theses came through repository sources (`base:theses.hal.science` and the like) whose awarding
  university the table does not hold; they get no institution yet.
- **Crosswalk by the record itself** (2026-11-01): a thesis with no harvested AHA id joins the one AHA record
  awarded by the same institution key, within a year, sharing at least 80% of the shorter title's words of
  four or more letters (two or more). 2,133 theses, mostly Canadian, were the same dissertation as an AHA
  record under two keys (Michael Childs, McGill 1986). The author joins too when the names agree on family
  name and first initial (short forms: Doug / Douglas Hunter); otherwise only the work joins and the pair is
  queued. An AHA record reached by two theses joins neither.
- A work merge is allowed when the two keys are one harvested thesis and one AHA record (the crosswalk has
  decided they are one dissertation); person merges follow key_aha.
- **People.** Each thesis's author is a person anchored on `diss-author:<id>`, joining
  - the AHA record's author (`aha-phd:<record>`), and so whatever that key already holds (registry, advisor
    token), and
  - a canon key whose cited works include the thesis as published (key_aha.own_book: identity by works;
    a canon key claimed by several theses is a pooled name and joins none).
- Merges between keys follow key_aha (names agree in full, no pooled key, at most one LC authority).

    python3 scripts/key_theses.py --out data/identifiers/theses-2026-11-01
"""
import argparse
import csv
import glob
import json
from collections import Counter
from pathlib import Path

from aha_links import same_listed_name, title_words
from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_aha import AHA, author_merge_ok, canon_works, drop_shared, own_book
from key_registry import names_compatible
from key_canon_map import D
from merge_guard import guarded

HARVESTS = ROOT / 'data/field-research'
KEYED = {'history_phd'}


def aha_matches(ids):
    """thesis id -> (AHA record id, match basis) from the US harvests' records.jsonl files."""
    out = {}
    for path in sorted(glob.glob(str(HARVESTS / 'us-dissertations*/**/records.jsonl'), recursive=True)):
        with open(path, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get('aha_id') and r.get('id') in ids:
                    out[r['id']] = (str(r['aha_id']), (r.get('aha_match') or {}).get('match_basis') or 'recorded')
    return out


def aha_by_record(state, theses, inst_of, matched):
    """thesis id -> AHA record for theses without a harvested AHA id: same institution key, year within one,
    the titles largely shared, exactly one candidate, and the record reached by no other thesis."""
    inst = {m[len('inst-name:'):]: k for k, ms in state.members.items() if state.keys[k]['type'] == 'institution'
            for m in ms if m.startswith('inst-name:')}
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        by_inst = {}
        for r in csv.DictReader(f):
            if r['department'] in inst and (r['year'] or '').isdigit() and r['title'] and r['title'] != '[No title]':
                by_inst.setdefault(inst[r['department']], []).append((r, title_words(r['title'])))
    taken = {rid for rid, _ in matched.values()}
    hits = {}
    for t in theses:
        if t['id'] in matched or not t['year'].isdigit() or t['id'] not in inst_of:
            continue
        w = title_words(t['title'])
        c = [r for r, w2 in by_inst.get(inst_of[t['id']], ()) if abs(int(r['year']) - int(t['year'])) <= 1
             and len(w & w2) >= 2 and len(w & w2) >= 0.8 * min(len(w), len(w2))]
        if len(c) == 1 and c[0]['id'] not in taken:
            hits[t['id']] = c[0]
    reached = Counter(r['id'] for r in hits.values())
    return {tid: r for tid, r in hits.items() if reached[r['id']] == 1}


def institution_key(state, slug, country):
    for alias in (f'diss-inst:{slug}', f'diss-inst:{country.lower()}:{slug}', f'diss-inst:uk:{slug}'):
        if alias in state.alias:
            return state.alias[alias]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with (D / 'dissertations.csv').open(newline='', encoding='utf-8') as f:
        theses = list(csv.DictReader(f))
    aha = aha_matches({t['id'] for t in theses})
    inst_of = {t['id']: k for t in theses if (k := institution_key(state, t['institution'], t['country'] or ''))}
    by_record = aha_by_record(state, [t for t in theses if t['eligibility'] in KEYED or t['in_analysis'] == 'True'],
                              inst_of, aha)
    canon = canon_works(state)
    report, queue, clusters = Counter(), [], []
    for t in theses:
        if t['eligibility'] not in KEYED and t['in_analysis'] != 'True':
            report['not_keyed_eligibility'] += 1
            continue
        tid, title = t['id'], (t['title'] or '').strip()
        members = {f'year:{t["year"]}'} if t['year'] else set()
        inst = institution_key(state, t['institution'], t['country'] or '')
        if inst:
            members.add(f'awarded-by:{inst}')
            report['works_with_institution_key'] += 1
        else:
            report['works_without_institution_key'] += 1
        work, author = {f'diss-thesis:{tid}'}, {f'diss-author:{tid}'}
        if tid in aha:
            rid, basis = aha[tid]
            work.add(f'aha-diss:{rid}')
            author.add(f'aha-phd:{rid}')
            report[f'aha_match:{basis}'] += 1
        elif tid in by_record:
            rid, basis = by_record[tid]['id'], 'institution, year and title'
            work.add(f'aha-diss:{rid}')
            if same_listed_name(t['author'] or '', by_record[tid]['dissertator']) or \
                    names_compatible(t['author'] or '', by_record[tid]['dissertator']):
                author.add(f'aha-phd:{rid}')
            else:
                queue.append(dict(kind='same_thesis_author_names_differ', thesis=tid, record=rid, author=t['author'],
                                  dissertator=by_record[tid]['dissertator']))
                report['aha_record_author_names_differ'] += 1
            report['aha_match:institution, year and title'] += 1
        clusters.append(dict(type='work', label=title or f'Dissertation {tid}', anchors=work, members=members,
                             aliases=set(), resolution='established',
                             basis=f'dissertation graph thesis ({t["institution"]}, {t["year"]})'
                                   + (f'; AHA record {rid} by {basis}' if len(work) > 1 else '')))
        books = own_book(dict(dissertator=t['author'], title=title, year=t['year']), canon)
        if len(books) == 1:
            k = next(iter(books))
            author |= {a for a in state.keys[k]['anchors'] if a.startswith('diss-person:')}
            report['author_joined_canon_by_own_book'] += 1
        elif books:
            queue.append(dict(kind='own_book_on_several_canon_keys', thesis=tid, author=t['author'], keys=sorted(books)))
        clusters.append(dict(type='person', label=t['author'] or f'Author of dissertation {tid}', anchors=author,
                             members=set(), aliases=set(), resolution='established',
                             basis=f'author of dissertation graph thesis {tid}'))
    clusters = drop_shared(clusters, state, queue, report, 'canon_key_claimed_by_several_theses', 'anchor_on_several_theses')
    authors_ok = author_merge_ok(state)

    def merge_ok(cluster, keys):
        if cluster['type'] == 'work':
            kinds = sorted(tuple(sorted({a.split(':', 1)[0] for a in state.keys[k]['anchors']})) for k in keys)
            return kinds == [('aha-diss',), ('diss-thesis',)]
        return authors_ok(cluster, keys)
    ops, assign, held = plan(state, clusters, guarded(state, merge_ok, exclude=args.out))
    materialise(state, dict(basis='thesis keying', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='dissertation graph theses (works) and their authors (people)', decided_by='build', ops=ops),
        ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(theses=len(theses), **dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
