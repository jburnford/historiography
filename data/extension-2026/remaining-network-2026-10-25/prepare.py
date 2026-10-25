"""Prepare the approved endpoint-only amendment; no canonical application."""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parent
REVIEW = ROOT / 'data/field-research/remaining-canon-2026-10-25/network-review.json'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not (ROOT / 'data/production-batches/person-links-1.191/acceptance.json').exists(), 'Accepted packet is frozen'
    baseline = read(OWN / 'baseline.json')
    graph_path = ROOT / baseline['canonical_path']
    assert hashlib.sha256(graph_path.read_bytes()).hexdigest() == baseline['canonical_sha256']
    review = read(REVIEW)
    assert review['baseline_revision'] == '1.190'
    assert review['baseline_sha256'] == baseline['canonical_sha256']
    assert review['reviewer'] == 'Astra'
    assert len(review['endpoint_revisions']) == review['endpoint_revision_count'] == 74
    edges = {e['id']: e for e in read(graph_path)['edges']}
    revisions = []
    deltas = {}
    for item in review['endpoint_revisions']:
        eid, old = item['edge_id'], item['before_edge']
        assert old == edges[eid], f'Stale source edge {eid}'
        assert item['before'] == {k: old[k] for k in ('source', 'target')}
        delta = {k: v for k, v in item['after'].items() if old[k] != v}
        delta.update(item.get('field_updates', {}))
        if item.get('evidence_note_after') is not None:
            delta['evidence_note'] = item['evidence_note_after']
        assert delta and set(delta) <= {'source', 'target', 'target_strand', 'evidence_note'}
        old_note = old.get('evidence_note', '')
        new_note = delta.get('evidence_note', old_note)
        prefix = os.path.commonprefix([old_note, new_note])
        if eid == 'edge_1291':
            fragments = ['Selected Clues pages 96–101, own text read through scan/OCR.',
                         'A comparison made by Ginzburg;',
                         'no Freud-to-Ginzburg transmission is inferred',
                         'His proposed Morelli-to-Freud connection is not independently checked here.']
        else:
            assert new_note == old_note, eid
            fragments = [old_note]
        deltas[eid] = delta
        revisions.append({'id': eid, 'previous_record': old, 'changes': delta,
                          'preserved_evidence_prefix': prefix,
                          'preserved_evidence_fragments': fragments,
                          'rationale': item['rationale'],
                          'inherited_citations_and_reading_scopes': item['evidence'],
                          'independent_review_locator': f'endpoint_revisions[{review["endpoint_revisions"].index(item)}]'})
    clears = []
    for row in review['dependent_roster_pointer_clears']:
        change = {key: row[key] for key in ('node', 'person_id', 'field', 'old', 'new')}
        assert change['field'] == 'edge_id' and change['new'] == ''
        clears.append({'text_revision': change, 'previous_row': row['before_row'], 'rationale': row['rationale']})
    assert {(r['text_revision']['node'], r['text_revision']['person_id'], r['text_revision']['old']) for r in clears} == {('durkheim', 'latour', 'edge_1155'), ('practice', 'philip_huang', 'edge_1047')}
    approval = {'status': 'approved_by_astra', 'checked_on': '2026-10-25',
                'approval_basis': 'Direct reviewer messages approve the bounded 74-edge list and both exact guarded empty-string roster-pointer clears. Only edge_1155 target_strand:null and edge_1291 obsolete contextual-routing clause are dependent edge-field corrections.',
                'source': str(REVIEW.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(REVIEW.read_bytes()).hexdigest(),
                'source_hash_scope': 'Snapshot of the review when approved decisions were copied. The mutable external review may later gain independent verification notes; the frozen owned decisions are pinned separately.',
                'revisions': revisions,
                'roster_pointer_clears': clears,
                'limits': review['scope']}
    write(OWN / 'correction/approved-revisions.json', approval)
    batch = read(OWN / 'batch.json')
    batch['edge_revisions'] = deltas
    batch['text_revisions'] = [row['text_revision'] for row in clears]
    batch['summary'] = 'Route 74 already-evidenced person-specific relationships to available individual entries; retain claims, citations, full substantive qualifications and genuinely collective field relationships.'
    batch['rationale'] = 'Astra independently reviewed the inherited claims and approved 74 endpoint corrections. This changes no historical claim or reading extent. Edge_1155 clears an obsolete field-strand pointer with null. Edge_1291 removes only an obsolete contextual-routing clause, preserving comparison, no-transmission and unchecked Morelli qualifications. Two obsolete roster edge_id pointers are cleared with guarded string revisions, preserving all other row fields. Full previous edge records, prior roster rows and source-reading scopes are retained in the correction provenance and subsequent acceptance receipt. No new nodes, edges, sources, people, chronology or life records.'
    write(OWN / 'batch.json', batch)
    write(OWN / 'correction/entry-draft.json', {'status': 'independently_approved_endpoint_revisions_prepared_for_review', 'prepared': '2026-10-25', 'proposed_edges': [], 'new_sources': []})
    print(f'Prepared {len(deltas)} approved endpoint revisions; no release or canonical graph written')


if __name__ == '__main__':
    main()
