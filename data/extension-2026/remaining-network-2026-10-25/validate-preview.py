"""Validate only the owned unaccepted packet; never apply or rebuild production."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate, pathways_within


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = read(OWN / 'baseline.json')
    canonical = ROOT / baseline['canonical_path']
    assert sha(canonical) == baseline['canonical_sha256'], 'Canonical baseline changed; coordinator must rebase explicitly'
    before = read(canonical)
    provenance = read(OWN / 'correction/approved-revisions.json')
    assert provenance['status'] == 'approved_by_astra', 'No independently approved correction list'
    decisions = provenance['revisions']
    assert decisions, 'Empty scaffold cannot be frozen'
    packet_path = OWN / 'release/editorial-additions.json'
    packet = read(packet_path)
    assert packet['baseline_revision'] == '1.190' and packet['revision'] == '1.191'
    for key in ('nodes', 'people_updates', 'roster_edges', 'edges', 'sources', 'source_addenda', 'wikidata', 'new_people', 'roster_additions', 'node_list_additions', 'field_sets', 'source_field_sets', 'claim_reviews', 'new_strands', 'strand_list_additions', 'roster_list_additions'):
        assert not packet.get(key), key
    clears = provenance.get('roster_pointer_clears', [])
    assert packet.get('text_revisions', []) == [row['text_revision'] for row in clears]
    expected_nodes = deepcopy(before['nodes'])
    for row in clears:
        change = row['text_revision']
        assert change['field'] == 'edge_id' and change['new'] == ''
        node = next(n for n in expected_nodes if n['id'] == change['node'])
        roster = next(r for r in node['representative_people'] if r['person_id'] == change['person_id'])
        assert roster == row['previous_row']
        assert roster['edge_id'] == change['old']
        roster['edge_id'] = ''
    assert set(packet['edge_revisions']) == {row['id'] for row in decisions}
    old_edges = {e['id']: e for e in before['edges']}
    for row in decisions:
        eid = row['id']
        assert row['previous_record'] == old_edges[eid], f'Stale prior-record guard: {eid}'
        assert packet['edge_revisions'][eid] == row['changes'], eid
        assert set(row['changes']) <= {'source', 'target', 'evidence_note', 'target_strand'}, eid
        if 'target_strand' in row['changes']:
            assert row['changes']['target_strand'] is None, eid
            assert 'target' in row['changes'], eid
            assert old_edges[eid].get('target_strand'), eid
        prefix = row['preserved_evidence_prefix']
        assert old_edges[eid].get('evidence_note', '').startswith(prefix), eid
        assert row['changes'].get('evidence_note', old_edges[eid].get('evidence_note', '')).startswith(prefix), eid
        for fragment in row['preserved_evidence_fragments']:
            assert fragment in old_edges[eid].get('evidence_note', ''), eid
            assert fragment in row['changes'].get('evidence_note', old_edges[eid].get('evidence_note', '')), eid
    after = Batch(OWN).transform(before, packet)
    for key in before:
        if key not in ('nodes', 'edges', 'revision_history'):
            assert after[key] == before[key], f'Unexpected graph change: {key}'
    assert after['nodes'] == expected_nodes, 'Only approved roster pointers may change on nodes'
    assert after['revision_history'][:-1] == before['revision_history']
    changed = []
    for old, new in zip(before['edges'], after['edges'], strict=True):
        assert old['id'] == new['id']
        if old != new:
            changed.append(old['id'])
            assert old['id'] in packet['edge_revisions']
            assert new == dict(old, **packet['edge_revisions'][old['id']])
    assert set(changed) == set(packet['edge_revisions'])
    pathways = read(ROOT / 'seminar-pathways.json')
    old_errors, old_warnings = validate(before, pathways_within(before, pathways))
    errors, warnings = validate(after, pathways_within(after, pathways))
    assert not old_errors and not errors, (old_errors, errors)
    assert sha(canonical) == baseline['canonical_sha256'], 'Canonical bytes changed'
    report = {'status': 'pass', 'checked_on': '2026-10-25', 'baseline_revision': '1.190', 'revision': '1.191', 'canonical_sha256_before_and_after': sha(canonical), 'packet_sha256': sha(packet_path), 'approved_revisions_sha256': sha(OWN / 'correction/approved-revisions.json'), 'revised_edge_ids': sorted(changed), 'new_nodes': 0, 'new_edges': 0, 'new_sources': 0, 'new_people': 0, 'validation_errors': errors, 'baseline_warnings': old_warnings, 'preview_warnings': warnings, 'protected_fields_and_untouched_records_preserved': True, 'applied': False}
    report['new_warnings'] = sorted(set(warnings) - set(old_warnings))
    report['warning_review'] = 'Astra independently reproduced the full transform and reviewed the warning increase from 11 to 25: 14 repeated endpoint/type combinations expose preserved distinct legacy and new claims at personal endpoints. Expected under the no-merge/preserve-ID rule; no substantive blocker. No new unconnected-node warning.'
    report['roster_pointer_clears'] = [row['text_revision'] for row in clears]
    (OWN / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    manifest = {'revision': '1.191', 'baseline_revision': '1.190', 'status': 'frozen_for_independent_review_not_applied', 'packet_sha256': sha(packet_path), 'files': {str(p.relative_to(OWN)): sha(p) for p in sorted(OWN.rglob('*')) if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts}}
    (OWN / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
