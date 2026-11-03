"""Apply Sol's verdicts on advisor -> own-dissertation links (2026-11-03).

85 links checked (groups.json, BRIEF.md): 83 `own` (the doubts were first degrees, posts and postdoctoral
fellowships), 2 `namesake`. For a namesake, the record's anchors (its author anchor and any harvested-thesis
author of the same dissertation) are detached from the supervisor's key, as key_aha_mislinks does, and
- attached to the key of the person whose dissertation it is, where that person is keyed (Arthur M.
  Schlesinger Sr., p-89397: Q4799614, LC n79007439, the Harvard advisor token), or
- minted as their own person (Peter Bowman Brown's Chicago 1978 dissertation; the Princeton historian holds
  no earned doctorate).

    python3 data/identifiers/own-thesis-check-2026-11-03/apply-verdicts.py
    python3 scripts/identifiers.py apply data/identifiers/own-thesis-check-2026-11-03/proposal.json
"""
import csv
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State, materialise  # noqa: E402
from key_aha import AHA  # noqa: E402

THEIRS = {'p-3560': 'p-89397'}      # supervisor key -> key of the dissertation's author, where keyed

state = State.load(ROOT / 'data/identifiers')
with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
    records = {r['id']: r for r in csv.DictReader(f)}
audit = {x['key']: x for x in json.loads((ROOT / 'data/identifiers/aha-own-link-audit-2026-11-03/audit.json').read_text())
         if x['record_on_key']}
verdicts = [v for f in sorted(HERE.glob('g*/verdicts.json')) for v in json.loads(f.read_text())]
ops = []
for v in verdicts:
    if v['verdict'] != 'namesake':
        continue
    live = state.lookup(v['id'])
    rec = audit[v['id']]['record']
    author = f'aha-phd:{rec}'
    if len(live) != 1 or state.anchor.get(author) != live[0]:
        continue
    k = live[0]
    work = state.lookup(f'aha-diss:{rec}')
    theirs = {author} | {a for a in state.keys[k]['anchors'] if a.startswith('diss-author:')
                         and state.lookup('diss-thesis:' + a.split(':', 1)[1]) == work}
    r = records[rec]
    src = '; '.join(e['url'] for e in v.get('evidence', [])[:3])
    ops.append(dict(event='detach', key=k, anchors=sorted(theirs), members=[],
                    basis=f'AHA record {rec} ({r["dissertator"]}, {r["department"]}, {r["year"]}) is a namesake\'s: '
                          f'{v["notes"]} (Sol check 2026-11-03: {src})'))
    if k in THEIRS:
        ops.append(dict(event='attach', key=THEIRS[k], anchors=sorted(theirs), aliases=[], members=[],
                        basis=f'author of AHA dissertation record {rec}: {state.keys[THEIRS[k]]["label"]} (Sol check 2026-11-03)'))
    else:
        ops.append(dict(event='mint', key=f'new:{rec}', type='person', label=r['dissertator'], resolution='recorded',
                        anchors=sorted(theirs), aliases=[], members=[], basis=f'author of AHA dissertation record {rec}'))
materialise(state, dict(basis='own thesis check', ops=ops), 'dry-run', 'dry-run')
(HERE / 'proposal.json').write_text(json.dumps(dict(
    basis="namesakes' dissertations detached from supervisor keys (Sol check of the audit's doubted links)",
    decided_by='review', ops=ops), ensure_ascii=False, indent=1) + '\n')
print(len(ops), 'ops')
