"""Repository supervisors joined to keyed historians by career facts (2026-11-03). Writes a proposal.

key_repository_supervisors minted a key for each thesis supervisor it could not join on the same thesis
(anchors `repo-advisor:<institution>|<name>` or `capes-person:<id>`, nothing else). Many are historians the log
already holds under a PID through another route (Nicholas Purcell and John Ma, Oxford; Till van Rahden,
Montréal). As key_aha_career does for AHA advisors, such a key joins a person key holding a public PID when
- the names agree as names (key_aha_lc_notes.name_agrees: given names or nicknames, no initials alone);
- an employment of that person names the institution of a thesis the supervisor supervised (the thesis's
  awarding institution key: its label and source names): Wikidata P108, a teaching clause or 373 affiliation in
  their LC authority's notes, or an employment in their cached ORCID record;
- no birth year makes them younger than 25 or older than 90 at the supervision;
- exactly one such person passes. The keys merge through key_aha_career's merge rule behind the merge guard;
  several supervisor keys reaching one person (spellings: 'S Heathorn', 'Stephen Heathorn') merge together.

    python3 scripts/key_repository_advisor_career.py --out data/identifiers/repository-advisor-career-2026-11-03
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_aha_career import lc_facts, merge_rule, orcid_facts, surname, wikidata_facts
from key_aha_lc_notes import by_letter, lc_school_agrees, letters, name_agrees
from merge_guard import guarded

SOURCE_ONLY = {'repo-advisor', 'capes-person'}
PIDS = ('wd', 'lcnaf', 'orcid', 'gnd', 'idref')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/field-research/aha-career-2026-11-02/raw')
    ap.add_argument('--lc', default='/mnt/e/lc-authorities')
    args = ap.parse_args()
    state = State.load(args.state)
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}

    def schemes(v):
        return {a.split(':', 1)[0] for a in v['anchors']}

    supervisors = {k for k, v in live.items() if schemes(v) and schemes(v) <= SOURCE_ONLY}
    institutions, years = defaultdict(set), defaultdict(set)   # supervisor key -> institution names, thesis years
    for claim, subj, pred, obj in state.relations('supervised'):
        if len(subj) != 1 or subj[0] not in supervisors or len(obj) != 1:
            continue
        for m in state.members.get(obj[0], ()):
            if m.startswith('awarded-by:'):
                for i in state.lookup(m.split(':', 1)[1]):
                    institutions[subj[0]].add(state.keys[i]['label'])
                    institutions[subj[0]] |= {a for a in state.keys[i]['aliases'] if not a.startswith('diss-inst:')}
            elif m.startswith('year:') and m[5:].isdigit():
                years[subj[0]].add(int(m[5:]))
    pid_keys = [(v['label'], k) for k, v in live.items() if schemes(v) & set(PIDS)]
    index = by_letter(pid_keys)
    candidates = {}
    for k in supervisors:
        label = live[k]['label']
        cands = {c for l in letters(label) for _, c in index.get((surname(label), l), ())}
        candidates[k] = sorted(c for c in cands if name_agrees(live[c]['label'], label))
    wanted = {c for cs in candidates.values() for c in cs}

    def ids(k, scheme):
        return sorted(a.split(':', 1)[1] for a in live[k]['anchors'] if a.startswith(scheme + ':'))

    wd = wikidata_facts({q for c in wanted for q in ids(c, 'wd')}, args.cache)
    lc = lc_facts({x for c in wanted for x in ids(c, 'lcnaf')}, args.lc)
    report, by_target, rows = Counter(), defaultdict(set), []
    for k in sorted(supervisors, key=lambda x: int(x[2:])):
        if not candidates[k]:
            report['no_named_candidate'] += 1
            continue
        if not institutions[k]:
            report['no_institution'] += 1
            continue
        passing = []
        for c in candidates[k]:
            emp, birth = set(), set()
            for f in [wd[q] for q in ids(c, 'wd')] + [lc[x] for x in ids(c, 'lcnaf')] + [orcid_facts(o) for o in ids(c, 'orcid')]:
                emp |= f['emp']
                birth |= f['birth']
            agree = sorted({e for e in emp for i in institutions[k] if lc_school_agrees(i, e)})
            age_ok = not (birth and years[k]) or any(25 <= y - b <= 90 for y in years[k] for b in birth)
            if agree and age_ok:
                passing.append((c, agree))
        rows.append(dict(key=k, label=live[k]['label'], institutions=sorted(institutions[k]), candidates=candidates[k],
                         passing=[dict(key=c, label=live[c]['label'], employer=a[:3]) for c, a in passing]))
        if len(passing) == 1:
            by_target[passing[0][0]].add(k)
            report['joined'] += 1
        else:
            report['several_pass' if passing else 'no_fact_agrees'] += 1
    clusters = []
    for c, ks in sorted(by_target.items()):
        why = next(r for r in rows if r['key'] in ks)['passing'][0]['employer'][0]
        clusters.append(dict(type='person', label=live[c]['label'],
                             anchors={a for k in ks for a in live[k]['anchors']} | {sorted(live[c]['anchors'])[0]},
                             members=set(), aliases=set(), resolution='established',
                             basis=f'thesis supervisor at the institution where {live[c]["label"]} is employed ({why}); names agree'))
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    materialise(state, dict(basis='repository advisor career', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='repository supervisors joined to keyed historians employed at the thesis institution', decided_by='rule',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'candidates.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(supervisor_keys=len(supervisors), **dict(sorted(report.items())),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
