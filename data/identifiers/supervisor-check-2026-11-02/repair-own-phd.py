"""Detach namesakes' dissertations from supervisor keys before Sol's verdicts merge them (2026-11-02).

For a `yes` verdict, the supervisor's key merges with the candidate's. Where the key also holds the AHA record
the genealogy linked as the supervisor's own dissertation (`aha-phd:<record>`) on name and date alone, and
Sol's description of the supervisor gives a doctorate elsewhere, the merge would hand a namesake's thesis to
the historian. `own-phd-disagrees.json` lists the 25 yes verdicts whose description does not name the linked
school. Read one by one, 16 agree after all (USC, 'University of California' for Berkeley, LSU, Penn State, UBC,
Radcliffe for Harvard, no school stated), and 9 do not (listed below). For those nine the record's anchors (its author
anchor and any harvested-thesis author of the same dissertation) are detached and minted as their own person,
as key_aha_mislinks does. apply-verdicts.py then rebuilds the merges.

    python3 data/identifiers/supervisor-check-2026-11-02/repair-own-phd.py
    python3 scripts/identifiers.py apply data/identifiers/supervisor-check-2026-11-02/repair-proposal.json
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State, materialise  # noqa: E402
from key_aha import AHA  # noqa: E402

NOT_THEIRS = {   # supervisor id -> Sol's statement of their doctorate
    'p-45395': 'John Whitney Hall: doctorate, Harvard',
    'p-71460': 'Judith E. Smith: PhD Brown 1980',
    'p-60044': 'David O. Morgan: PhD London 1977',
    'p-90772': 'Matthew J. B. Butler: PhD Bristol',
    'p-45768': 'James R. Hansen: PhD Ohio State 1981',
    'p-56575': 'Harry M. Marks: PhD political science, MIT, 1987',
    'p-69624': 'Jonathan Scott: PhD Cambridge',
    'p-45519': 'Pekka Hämäläinen: doctorate Helsinki',
    'p-41593': 'Mary Frank Fox: PhD sociology, Michigan, 1978',
}

state = State.load(ROOT / 'data/identifiers')
with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
    records = {r['id']: r for r in csv.DictReader(f)}
flags = {f['id']: f for f in json.loads((HERE / 'own-phd-disagrees.json').read_text())}
ops, done = [], []
for sid, doctorate in NOT_THEIRS.items():
    live = state.lookup(sid)
    if len(live) != 1:
        continue
    k = live[0]
    for rec, school, year in flags[sid]['own']:
        author = f'aha-phd:{rec}'
        if state.anchor.get(author) != k:
            continue
        work = state.lookup(f'aha-diss:{rec}')
        theirs = {author} | {a for a in state.keys[k]['anchors'] if a.startswith('diss-author:')
                             and state.lookup('diss-thesis:' + a.split(':', 1)[1]) == work}
        r = records[rec]
        ops.append(dict(event='detach', key=k, anchors=sorted(theirs), members=[],
                        basis=f'AHA record {rec} ({r["dissertator"]}, {school}, {year}) is a namesake\'s: Sol\'s check of the '
                              f'supervisor ({doctorate}) gives a doctorate elsewhere'))
        ops.append(dict(event='mint', key=f'new:{rec}', type='person', label=r['dissertator'], resolution='recorded',
                        anchors=sorted(theirs), aliases=[], members=[], basis=f'author of AHA dissertation record {rec}'))
        done.append((sid, rec))
materialise(state, dict(basis='own phd repair', ops=ops), 'dry-run', 'dry-run')
(HERE / 'repair-proposal.json').write_text(json.dumps(dict(
    basis="namesakes' dissertations detached from supervisor keys before Sol's verdicts merge them",
    decided_by='review', ops=ops), ensure_ascii=False, indent=1) + '\n')
print(len(done), 'records detached:', done)
