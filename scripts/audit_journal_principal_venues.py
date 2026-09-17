#!/usr/bin/env python3
"""Audit the revision 1.115 venue review against its preserved 1.114 snapshot."""
import copy
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
    before = read('drafts/historiography-1920-2000.v1.114.json')
    after = read('historiography-1920-2000.json')
    batch = read('data/journal-catalogue/venue-batches/founding-004.json')
    ledger = read('feedback/journals/principal-venues-v1.115-review.json')
    assert after['revision_history'][-1]['version'] == '1.115'
    assert after['revision_history'][:-1] == before['revision_history']
    protected = set(before) - {'journal_catalogue', 'revision_history'}
    assert protected == set(after) - {'journal_catalogue', 'revision_history'}
    assert all(before[k] == after[k] for k in protected)
    old, new = before['journal_catalogue'], after['journal_catalogue']
    assert new == correct_venues(old, batch)
    assert set(old) == set(new)
    assert all(old[k] == new[k] for k in old if k not in ('nodes', 'edges', 'sources'))
    assert new['sources'] == old['sources'] + batch['added_sources']
    withdrawn = {w['edge']['id'] for w in batch['withdrawals']}
    assert new['edges'] == [e for e in old['edges'] if e['id'] not in withdrawn] + batch['added_edges']
    assert not ({e['id'] for e in batch['added_edges']} & {e['id'] for e in old['edges']})
    assert len(old['nodes']) == len(new['nodes'])
    checks = {c['journal_id']: c for c in batch['research_venue_checks']}
    changes = []
    for prev, node in zip(old['nodes'], new['nodes']):
        expected = copy.deepcopy(prev)
        check = checks.get(prev['id'])
        if check:
            expected['publication_role'] = 'research_journal'
            expected['source_ids'] = list(dict.fromkeys([*prev['source_ids'], *check['source_ids']]))
        assert node == expected, prev['id']
        if prev != node:
            changes.append(node['id'])
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
        for lead in row['discovery_leads']:
            assert lead['status'] == 'unaccepted_discovery_lead'
            assert set(lead['catalogue_candidate_ids']) <= journals
    for edge in batch['added_edges']:
        assert edge['temporal_scope']['end'] <= 2000
        if edge['relationship_kind'] == 'principal_venue':
            assert edge['selection_note'] and edge['temporal_scope']['start'] < edge['temporal_scope']['end']
    decisions = read('feedback/journals/founding-reappraisal-v1.115.json')['decisions']
    pending = {r['edge_id'] for r in read('feedback/journals/founding-criterion-reappraisal-v1.114.json')['records']
               if r['status'] == 'requires_historical_reappraisal'}
    assert pending <= {r['edge_id'] for r in decisions}
    assert all(r['status'] in ('retained_with_qualification', 'withdrawn') for r in decisions if r['edge_id'] in pending)
    principal = [e for e in new['edges'] if e['relationship_kind'] == 'principal_venue']
    report = dict(revision='1.115', historical_content_unchanged=True,
                  journal_identities_dates_bibliography_subjects_unchanged=True,
                  title_relationships_unchanged=True, prior_sources_unchanged=True,
                  unwithdrawn_venue_edges_unchanged=True, catalogue_reproduces=True,
                  field_entries_screened=len(rows), principal_edges=len(principal),
                  principal_title_records=len({e['source'] for e in principal}),
                  fields_with_principal_selection=len({e['target'] for e in principal}),
                  fields_with_any_specific_venue=len({e['target'] for e in new['edges']}),
                  relationship_kinds=dict(Counter(e['relationship_kind'] for e in new['edges'])),
                  withdrawals=len(withdrawn), added_edges=len(batch['added_edges']),
                  changed_journal_role_or_source_records=changes,
                  evidence_limit='Structural and preservation checks do not establish historical accuracy or comprehensive journal coverage.')
    path = ROOT / 'feedback/journals/principal-venues-v1.115-validation.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Preservation, 66-field ledger and offline rebuild passed: {len(principal)} principal edges, {len(new['edges'])} total.")


if __name__ == '__main__':
    main()
