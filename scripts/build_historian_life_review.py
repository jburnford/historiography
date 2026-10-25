"""Combine source-reviewed life records for every current historian biography.

Reads the frozen three-part review and the research packets for new biographies.
Refuses missing or conflicting records. No life data enter the canonical graph.
"""
import hashlib
import json
from pathlib import Path

from historian_life_review import validate_review

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/field-research/historian-life-review-2026-10-25'
OUT = ROOT / 'data/historian-life-review.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    historians = {n['id']: n for n in graph['nodes']
                  if n['entry_kind'] == 'person' and n['layer'] == 'historians'}
    rows, reports = {}, {}
    for part in range(1, 4):
        path = REVIEW / f'results-{part}.json'
        source = json.loads(path.read_text())
        for row in source['people']:
            if row['person_id'] in rows:
                raise ValueError('Duplicate identity in independent life audit')
            rows[row['person_id']] = row
        reports[str(path.relative_to(ROOT))] = sha(path)
    packets = ROOT / 'data/extension-2026'
    paths = sorted(packets.glob('historian-canon-lane*-2026-10-25/*/life-status.json'))
    paths += sorted((packets / 'dissertation-sarah-carter-2026-10-25').rglob('life-status.json'))
    for path in paths:
        source = json.loads(path.read_text())
        # New packet authors use the independent review's per-person schema.
        if 'person_id' not in source:
            continue
        pid = source['person_id']
        if pid not in historians or pid in rows:
            continue
        rows[pid] = source
        reports[str(path.relative_to(ROOT))] = sha(path)
    follow_up = REVIEW / 'follow-up-decisions.json'
    if follow_up.exists():
        decisions = json.loads(follow_up.read_text())
        for decision in decisions['decisions']:
            pid = decision['person_id']
            if pid not in historians:
                continue  # A prepared biography may not have been applied yet.
            if rows.get(pid) != decision['previous_record']:
                raise ValueError('Life follow-up no longer matches its prior record: ' + pid)
            replacement = decision['replacement_record']
            if replacement['person_id'] != pid:
                raise ValueError('Life follow-up cannot merge identities: ' + pid)
            rows[pid] = replacement
        reports[str(follow_up.relative_to(ROOT))] = sha(follow_up)
    missing = sorted(set(historians) - set(rows))
    if missing:
        raise ValueError('Historian biographies still lack reviewed life records: ' + ', '.join(missing))
    selected = [rows[pid] for pid in sorted(historians)]
    review = {'schema_version': '1.0', 'checked_on': '2026-10-25',
        'scope': {'layer': 'historians', 'entry_kind': 'person',
                  'graph_revision': graph['revision_history'][-1]['version'],
                  'people': len(selected)},
        'source_report_sha256': reports,
        'method': 'Independent institutional/authority/family-obituary review of existing biographies; primary identity and life evidence in the new biography packets. Missing death is not a living-status decision. Dates are reference metadata and do not imply work, career or influence intervals.',
        'people': selected}
    validate_review(review)
    OUT.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
    counts = {status: sum(r['status'] == status for r in selected)
              for status in ('deceased', 'living', 'unresolved')}
    print(f'Compiled {len(selected)} historian life reviews: {counts}')


if __name__ == '__main__':
    main()
