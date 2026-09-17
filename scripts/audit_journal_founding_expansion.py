#!/usr/bin/env python3
"""Verify the 1.113 founding expansion against its preserved 1.112 snapshot."""
import copy
import json
from collections import Counter
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue
    from .journal_venue_batches import merge_venues
    from .validate_journal_catalogue import validate_catalogue
except ImportError:
    from build_journal_catalogue import make_catalogue
    from journal_venue_batches import merge_venues
    from validate_journal_catalogue import validate_catalogue

ROOT = Path(__file__).resolve().parents[1]


def main():
    before = json.loads((ROOT / 'drafts/historiography-1920-2000.v1.112.json').read_text())
    after = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    batch = json.loads((ROOT / 'data/journal-catalogue/venue-batches/founding-002.json').read_text())
    assert after['revision_history'][-1]['version'] == '1.113'
    assert after['revision_history'][:-1] == before['revision_history']
    assert {k: v for k, v in before.items() if k not in ('journal_catalogue', 'revision_history')} == {
        k: v for k, v in after.items() if k not in ('journal_catalogue', 'revision_history')}
    old, new = before['journal_catalogue'], after['journal_catalogue']
    assert new == merge_venues(old, batch)
    assert new['edges'] == old['edges'] + batch['edges']
    assert new['sources'] == old['sources'] + batch['sources']
    assert {k: v for k, v in old.items() if k not in ('nodes', 'edges', 'sources')} == {
        k: v for k, v in new.items() if k not in ('nodes', 'edges', 'sources')}
    assert [n['id'] for n in old['nodes']] == [n['id'] for n in new['nodes']]
    changes = []
    for prev, node in zip(old['nodes'], new['nodes']):
        expected = copy.deepcopy(prev)
        edges = [e for e in batch['edges'] if e['source'] == prev['id']]
        check = batch.get('publication_start_checks', {}).get(prev['id'])
        if check:
            assert prev['publication_start'] is None and prev['publication_end'] is None
            assert prev['publication_status'] == 'unknown' and not prev.get('date_span')
            expected.update(publication_start=check['year'], chronology_note=check['note'],
                            date_span=dict(start=check['year'], end=None, precision='year',
                                           start_kind='publication_start', end_kind='unknown',
                                           open_end=None, basis='source_check', source_ids=check['source_ids']))
            expected['source_ids'] = list(dict.fromkeys([*expected['source_ids'], *check['source_ids']]))
        for edge in edges:
            expected['publication_role'] = 'research_journal'
            expected['source_ids'] = list(dict.fromkeys([*expected['source_ids'], *edge['source_ids']]))
        assert expected == node, node['id']
        if prev != node:
            changes.append(dict(journal_id=node['id'], label=node['label'],
                                fields=sorted(k for k in prev.keys() | node.keys() if prev.get(k) != node.get(k))))
    assert not validate_catalogue(new, after['nodes'])
    assert new == make_catalogue()
    assert new == json.loads((ROOT / 'data/journal-catalogue/catalogue.json').read_text())
    report = dict(revision='1.113', reviewed_on='2026-09-16',
                  historical_content_unchanged=True, previous_venue_edges_unchanged=True,
                  existing_dates_unchanged=True, identities_bibliography_subjects_unchanged=True,
                  catalogue_reproduces=True, candidate_ids_unchanged=True,
                  journal_edges_before=len(old['edges']), journal_edges_after=len(new['edges']),
                  relationship_kinds=dict(Counter(e['relationship_kind'] for e in new['edges'])),
                  added_edges=batch['edges'], added_source_ids=[s['id'] for s in batch['sources']],
                  filled_publication_starts=batch['publication_start_checks'], changed_journals=changes,
                  report='feedback/journals/founding-expansion-v1.113.md',
                  review_ledger='feedback/journals/founding-expansion-v1.113-review.json',
                  limitations=['Targeted programme review, not a completed worldwide journal census.',
                               'Journal foundation/consolidation is not the date of origin of a whole field.',
                               'Gap findings are editorial assessments, not automatic new atlas entries.'])
    (ROOT / 'feedback/journals/founding-expansion-v1.113.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Preservation, validation and offline rebuild passed: {len(batch["edges"])} additions; {len(new["edges"])} venue edges.')


if __name__ == '__main__':
    main()
