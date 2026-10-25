"""Compile separate sourced life metadata for newly accepted theorist biographies."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.historian_life_review import validate_review
from scripts.life_review_inputs import accepted_life_paths

REVIEW = ROOT / 'data/field-research/remaining-canon-2026-10-25'
OUT = ROOT / 'data/theorist-life-review.json'


def compile_review(graph, baseline, source_paths):
    original = set(baseline['table_ids']['nodes'])
    required = {n['id'] for n in graph['nodes'] if n.get('entry_kind') == 'person'
                and n['layer'] == 'intellectual_connections' and n['id'] not in original}
    rows, hashes = {}, {}
    for path in source_paths:
        row = json.loads(path.read_text())
        pid = row.get('person_id')
        if pid not in required:
            continue
        if pid in rows:
            raise ValueError('Duplicate accepted theorist life record: ' + pid)
        rows[pid] = row
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if required - set(rows):
        raise ValueError('New theorist biographies lack reviewed life records: ' + ', '.join(sorted(required - set(rows))))
    result = {'schema_version': '1.0', 'checked_on': '2026-10-25',
        'scope': {'layer': 'intellectual_connections', 'entry_kind': 'person',
                  'baseline_revision': baseline['revision'],
                  'graph_revision': graph['revision_history'][-1]['version'],
                  'people': len(required)},
        'source_report_sha256': hashes,
        'method': 'Primary/institutional identity and life evidence in accepted theory biographies. '
                  'Missing death does not establish life. Dates are reference metadata, not career or influence intervals.',
        'people': [rows[pid] for pid in sorted(rows)]}
    validate_review(result)
    return result


def main():
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    baseline = json.loads((REVIEW / 'baseline.json').read_text())
    theory = {n['id'] for n in graph['nodes'] if n.get('layer') == 'intellectual_connections'
              and n.get('entry_kind') == 'person'}
    result = compile_review(graph, baseline, accepted_life_paths(graph, theory))
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    counts = {s: sum(r['status'] == s for r in result['people']) for s in ('deceased', 'living', 'unresolved')}
    print(f"Compiled {len(result['people'])} new theorist life reviews: {counts}")


if __name__ == '__main__':
    main()
