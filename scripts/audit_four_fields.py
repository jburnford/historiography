#!/usr/bin/env python3
"""Audit revision 1.118 additions, unchanged records, ledger and public assets."""
import hashlib
import json
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue
    from .validate_graph import validate
except ImportError:
    from build_journal_catalogue import make_catalogue
    from validate_graph import validate

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    manifest = read('feedback/four-fields-v1.118-additions.json')
    before = read(manifest['baseline'])
    after = read('historiography-1920-2000.json')
    assert hashlib.sha256((ROOT / manifest['baseline']).read_bytes()).hexdigest() == manifest['baseline_sha256']
    assert after['revision_history'][-1]['version'] == '1.118'
    assert after['revision_history'][:-1] == before['revision_history']
    assert set(before) == set(after)
    for key, rows in manifest['additions'].items():
        assert after[key] == before[key] + rows, key
    protected = set(before) - set(manifest['additions']) - {'revision_history'}
    assert all(after[key] == before[key] for key in protected)
    assert after['journal_catalogue'] == make_catalogue() == read('data/journal-catalogue/catalogue.json')
    pathways = read('seminar-pathways.json')
    errors, warnings = validate(after, pathways)
    assert not errors, errors
    assert warnings == validate(before, pathways)[1]
    new_nodes = manifest['additions']['nodes']
    assert {n['id'] for n in new_nodes} == {'spatialhistory', 'intellectualhistory', 'labourhistory', 'ethnohistory'}
    for node in new_nodes:
        assert node['entry_kind'] == 'group' and node['period'] is None
        assert 'coverage through 2000' in node['date_label']
        assert all(r['works'].strip() and r['context'].strip() for r in node['representative_people'])
    ledger = read('feedback/journals/principal-venues-v1.118-review.json')
    previous_ledger = read('feedback/journals/principal-venues-v1.117-review.json')
    assert ledger['field_reviews'][:len(previous_ledger['field_reviews'])] == previous_ledger['field_reviews']
    groups = {n['id'] for n in after['nodes'] if n['entry_kind'] == 'group'}
    assert groups == {r['field_id'] for r in ledger['field_reviews']}
    for row in ledger['field_reviews']:
        accepted = {e['id'] for e in after['journal_catalogue']['edges'] if e['target'] == row['field_id']}
        assert accepted == set(row['accepted_principal_edge_ids'] + row['other_accepted_edge_ids'])
    evidence = read('data/field-research/v1.118/manifest.json')
    for row in evidence['files']:
        raw = (ROOT / row['path']).read_bytes()
        assert raw.startswith(b'%PDF-') and len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
    assets = {'site/index.html': 'index.html', 'site/styles.css': 'styles.css',
              'site/app.js': 'app.js', 'site/core.mjs': 'core.mjs',
              'historiography-1920-2000.json': 'data/graph.json',
              'seminar-pathways.json': 'data/pathways.json'}
    dest = ROOT / 'site/dist'
    assert not dest.is_symlink()
    assert not any(p.is_symlink() for p in dest.rglob('*'))
    assert {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()} == set(assets.values())
    for source, target in assets.items():
        assert (ROOT / source).read_bytes() == (dest / target).read_bytes()
    report = dict(revision='1.118', additions={k: len(v) for k, v in manifest['additions'].items()},
                  added_approaches=sum(len(n['strands']) for n in new_nodes),
                  added_people_selections=sum(len(n['representative_people']) for n in new_nodes),
                  all_prior_historical_records_preserved=True, entire_journal_catalogue_preserved=True,
                  catalogue_reproduces=True, ledger_entries=len(groups), structural_errors=errors,
                  unchanged_warnings=warnings, research_pdf_hashes_verified=len(evidence['files']),
                  exact_public_assets=len(assets),
                  limitation='Structure and preservation checks do not certify historical accuracy or comprehensive coverage.')
    (ROOT / 'feedback/four-fields-v1.118-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
