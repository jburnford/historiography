"""Read-only guard: run immediately before applying the 1.178 packet."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
people = {person['id']: person for person in graph['people']}
corrections = json.loads((HERE / 'identity-note-restorations.json').read_text())
for record in corrections['records']:
    person = people[record['person_id']]
    if person.get('identity_note') != record['expect_identity_note']:
        raise SystemExit('Identity note guard failed: ' + record['person_id'])
    if person.get('node_id') != record['expect_node_id']:
        raise SystemExit('Person node_id guard failed: ' + record['person_id'])
    if not record['value_identity_note'].startswith(record['prior_note'] + ' Addendum 2026-10-25'):
        raise SystemExit('Restored prior qualification missing: ' + record['person_id'])
print('PASS: five exact identity-note and node_id guards; no files modified.')
