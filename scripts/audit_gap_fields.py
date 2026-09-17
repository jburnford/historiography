#!/usr/bin/env python3
"""Verify the 1.117 field additions, preservation and offline journal rebuild."""
import copy
import hashlib
import json
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue
    from .journal_venue_batches import correct_venues
    from .validate_graph import validate
except ImportError:
    from build_journal_catalogue import make_catalogue
    from journal_venue_batches import correct_venues
    from validate_graph import validate

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    before = read('drafts/historiography-1920-2000.v1.116.json')
    after = read('historiography-1920-2000.json')
    manifest = read('feedback/gap-fields-v1.117-additions.json')
    batch = read('data/journal-catalogue/venue-batches/founding-006.json')
    ledger = read('feedback/journals/principal-venues-v1.117-review.json')
    assert after['revision_history'][-1]['version'] == '1.117'
    assert after['revision_history'][:-1] == before['revision_history']
    baseline = ROOT / 'drafts/historiography-1920-2000.v1.116.json'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == manifest['baseline_sha256']
    for key, additions in manifest['additions'].items():
        assert after[key] == before[key] + additions, key
    protected = set(before) - set(manifest['additions']) - {'revision_history', 'journal_catalogue'}
    assert set(before) == set(after)
    assert all(before[k] == after[k] for k in protected)
    old, new = before['journal_catalogue'], after['journal_catalogue']
    assert new == correct_venues(old, batch)
    assert not batch['withdrawals']
    for key in ('edges', 'sources', 'title_relationships'):
        assert new[key] == old[key] + batch['added_' + key]
    assert all(old[k] == new[k] for k in old if k not in ('nodes', 'edges', 'sources', 'title_relationships'))
    expected = copy.deepcopy(old['nodes'] + batch['added_nodes'])
    checks = {r['journal_id']: r for r in batch['research_venue_checks']}
    for node in expected:
        if node['id'] in checks:
            node['publication_role'] = 'research_journal'
            node['source_ids'] = list(dict.fromkeys(node['source_ids'] + checks[node['id']]['source_ids']))
    assert expected == new['nodes']
    assert new == make_catalogue() == read('data/journal-catalogue/catalogue.json')
    errors, warnings = validate(after, read('seminar-pathways.json'))
    assert not errors, errors
    assert warnings == validate(before, read('seminar-pathways.json'))[1]
    groups = {n['id'] for n in after['nodes'] if n['entry_kind'] == 'group'}
    assert len(groups) == len(ledger['field_reviews']) == 69
    assert groups == {r['field_id'] for r in ledger['field_reviews']}
    prior_rows = read('feedback/journals/principal-venues-v1.116-review.json')['field_reviews']
    assert ledger['field_reviews'][:len(prior_rows)] == prior_rows
    for row in ledger['field_reviews']:
        actual = {e['id'] for e in new['edges'] if e['target'] == row['field_id']}
        assert actual == set(row['accepted_principal_edge_ids'] + row['other_accepted_edge_ids'])
    assert {r['target_id'] for r in ledger['gap_candidates']} == {'publichistory', 'medicalhistory', 'urbanhistory'}
    assert all(r['status'] == 'implemented_with_explicit_coverage_limits' for r in ledger['gap_candidates'])
    evidence = read('data/journal-catalogue/venue-research/v1.117/manifest.json')
    for row in evidence['files']:
        raw = (ROOT / row['path']).read_bytes()
        assert raw.startswith(b'%PDF-') and len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
    assets = {'site/index.html': 'index.html', 'site/styles.css': 'styles.css',
              'site/app.js': 'app.js', 'site/core.mjs': 'core.mjs',
              'historiography-1920-2000.json': 'data/graph.json',
              'seminar-pathways.json': 'data/pathways.json'}
    dest = ROOT / 'site/dist'
    assert {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()} == set(assets.values())
    for source, target in assets.items():
        assert (ROOT / source).read_bytes() == (dest / target).read_bytes()
    principal = [e for e in new['edges'] if e['relationship_kind'] == 'principal_venue']
    report = dict(revision='1.117', historical_additions={k: len(v) for k, v in manifest['additions'].items()},
                  all_prior_historical_records_preserved=True,
                  prior_journal_metadata_classifications_edges_and_title_relations_preserved=True,
                  catalogue_reproduces=True, ledger_entries=len(groups), structural_errors=errors,
                  unchanged_warnings=warnings, principal_edges=len(principal),
                  principal_title_records=len({e['source'] for e in principal}),
                  principal_fields=len({e['target'] for e in principal}),
                  any_venue_fields=len({e['target'] for e in new['edges']}),
                  research_pdf_hashes_verified=len(evidence['files']), exact_public_assets=6,
                  limitation='Preservation and structural checks do not establish historical truth or comprehensive coverage.')
    (ROOT / 'feedback/gap-fields-v1.117-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
