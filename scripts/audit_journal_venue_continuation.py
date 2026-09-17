#!/usr/bin/env python3
"""Audit revision 1.116 additions against the preserved 1.115 snapshot."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue
    from .journal_venue_batches import correct_venues
    from .validate_journal_catalogue import validate_catalogue
except ImportError:
    from build_journal_catalogue import make_catalogue
    from journal_venue_batches import correct_venues
    from validate_journal_catalogue import validate_catalogue

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    before = read('drafts/historiography-1920-2000.v1.115.json')
    after = read('historiography-1920-2000.json')
    batch = read('data/journal-catalogue/venue-batches/founding-005.json')
    ledger = read('feedback/journals/principal-venues-v1.116-review.json')
    assert after['revision_history'][-1]['version'] == '1.116'
    assert after['revision_history'][:-1] == before['revision_history']
    protected = set(before) - {'journal_catalogue', 'revision_history'}
    assert protected == set(after) - {'journal_catalogue', 'revision_history'}
    assert all(before[k] == after[k] for k in protected)
    old, new = before['journal_catalogue'], after['journal_catalogue']
    assert new == correct_venues(old, batch)
    assert not batch['withdrawals']
    assert set(old) == set(new)
    changed_keys = {'nodes', 'edges', 'sources', 'title_relationships'}
    assert all(old[k] == new[k] for k in old if k not in changed_keys)
    for key in ('edges', 'sources', 'title_relationships'):
        assert new[key] == old[key] + batch['added_' + key]
    checks = {r['journal_id']: r for r in batch['research_venue_checks']}
    expected_nodes = copy.deepcopy(old['nodes'] + batch['added_nodes'])
    for node in expected_nodes:
        check = checks.get(node['id'])
        if check:
            node['publication_role'] = 'research_journal'
            node['source_ids'] = list(dict.fromkeys([*node['source_ids'], *check['source_ids']]))
    assert new['nodes'] == expected_nodes
    assert not validate_catalogue(new, after['nodes'])
    assert new == make_catalogue() == read('data/journal-catalogue/catalogue.json')
    groups = {n['id'] for n in after['nodes'] if n.get('entry_kind') == 'group'}
    rows = ledger['field_reviews']
    assert len(rows) == len(groups) == 66
    assert {r['field_id'] for r in rows} == groups
    by_id = {e['id']: e for e in new['edges']}
    journals = {n['id'] for n in new['nodes'] if n['entry_kind'] == 'periodical'}
    for row in rows:
        actual = {e['id'] for e in new['edges'] if e['target'] == row['field_id']}
        assert actual == set(row['accepted_principal_edge_ids'] + row['other_accepted_edge_ids'])
        assert all(by_id[i]['relationship_kind'] == 'principal_venue' for i in row['accepted_principal_edge_ids'])
        selected = {by_id[i]['source'] for i in row['accepted_principal_edge_ids']}
        for lead in row['discovery_leads']:
            assert lead['status'] == 'unaccepted_discovery_lead'
            assert set(lead['catalogue_candidate_ids']) <= journals
            assert not selected.intersection(lead['catalogue_candidate_ids'])
    for edge in batch['added_edges']:
        assert edge['relationship_kind'] == 'principal_venue'
        assert edge['selection_note']
        assert edge['temporal_scope']['start'] < edge['temporal_scope']['end'] <= 2000
    evidence = read('data/journal-catalogue/venue-research/v1.116/manifest.json')
    for row in evidence['files']:
        raw = (ROOT / row['path']).read_bytes()
        assert raw.startswith(b'%PDF-')
        assert len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
    principal = [e for e in new['edges'] if e['relationship_kind'] == 'principal_venue']
    report = dict(revision='1.116', historical_content_unchanged=True,
                  prior_journal_identities_dates_bibliography_subjects_unchanged=True,
                  prior_title_relationships_sources_and_edges_unchanged=True,
                  catalogue_reproduces=True, field_ledger_entries=len(rows),
                  principal_edges=len(principal),
                  principal_title_records=len({e['source'] for e in principal}),
                  fields_with_principal_selection=len({e['target'] for e in principal}),
                  fields_with_any_specific_venue=len({e['target'] for e in new['edges']}),
                  relationship_kinds=dict(Counter(e['relationship_kind'] for e in new['edges'])),
                  added_edges=len(batch['added_edges']), added_title_records=len(batch['added_nodes']),
                  added_title_relationships=len(batch['added_title_relationships']),
                  research_pdf_hashes_verified=len(evidence['files']),
                  evidence_limit='Structural checks establish preservation and reproducibility, not historical truth or comprehensive coverage.')
    path = ROOT / 'feedback/journals/principal-venues-v1.116-validation.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Preservation, ledger, research hashes and offline rebuild passed: {len(principal)} principal edges, {len(new['edges'])} total.")


if __name__ == '__main__':
    main()
