"""Verify preservation and append-only IDs without writing browser exports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('exporter', ROOT/'scripts/build_dissertation_site.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

def load(p):
    return json.loads(p.read_text())

def sha(v):
    return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def main():
    baseline = load(HERE/'baseline.json')
    current = load(ROOT/'data/dissertation-layer/site/index.json')
    indexed = {r['key']: r for r in current['sources']}
    shards = {}
    # New records may enter old shards. Compare old records individually.
    for old in baseline['sources']:
        row = old['index']
        assert indexed[row['key']] == row, row['key']
        assert current['sources'][old['index_position']] == row, row['key']
        if row['asset'] not in shards:
            shards[row['asset']] = load(ROOT/'data/dissertation-layer/site'/row['asset'])
        source = shards[row['asset']]['sources'][str(row['id'])]
        assert sha({k: source[k] for k in ('n', 'series', 'n_region')}) == old['numeric_sha256'], row['key']
        assert sha({k:v for k,v in source.items() if k != 'works'}) == old['source_without_works_sha256'], row['key']
        assert set(old['work_ids']) <= set(source['works']), row['key']
    assert sha({k:v for k,v in current.items() if k not in ('sources','reviewed_selection_count')}) == baseline['index_context_sha256']
    links = load(ROOT/'data/dissertation-layer/links.json')
    for pid, old in baseline['links']['people'].items():
        assert links['people'][pid] == old, pid
    for name in ('entries','entry_comparisons'):
        assert links[name] == baseline['links'][name], name
    original = load(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')
    graph = load(ROOT/'historiography-1920-2000.json')
    work_metadata = {w['work_id']:w for w in exporter.rows('works') if w['work_id'] in {k for r in links['people'].values() for k in r['works']}}
    registry = load(exporter.REVIEWED_IDS)
    data = copy.deepcopy(original)
    added = exporter.add_reviewed_sources(data, links, graph, work_metadata, registry)
    by_key = {r['key']:i for i,r in enumerate(data['labels'])}
    for old in registry['sources']:
        assert by_key[old['key']] == old['id']
    # Regression: alphabetically earlier new work must append, never shift Berg.
    synthetic = dict(work_id='W:aaa|new reviewed work', title='New Reviewed Work', year='2000', first_author='AAA, New', first_author_key='aaa|new')
    test_links = copy.deepcopy(links)
    first = next(iter(test_links['people']))
    test_links['people'][first]['works'].append(synthetic['work_id'])
    test_registry = copy.deepcopy(registry)
    test_registry['sources'].append(dict(key=synthetic['work_id'], short='AAA, New Reviewed Work', full='New Reviewed Work', year=2000, author='AAA, New', id=len(data['labels']), source_index=len(data['sources'])))
    test_data = copy.deepcopy(original)
    exporter.add_reviewed_sources(test_data, test_links, graph, {**work_metadata, synthetic['work_id']:synthetic}, test_registry)
    for old in registry['sources']:
        assert test_data['labels'][old['id']]['key'] == old['key']
    failures = 0
    for change in ('missing_registry_row','id_drift','metadata_drift','base_drift','order_drift'):
        bad = copy.deepcopy(test_registry)
        if change == 'missing_registry_row': bad['sources'].pop()
        if change == 'id_drift': bad['sources'][0]['id'] += 1
        if change == 'metadata_drift': bad['sources'][0]['full'] += ' changed'
        if change == 'base_drift': bad['base_label_count'] += 1
        if change == 'order_drift': bad['sources'][-1], bad['sources'][-2] = bad['sources'][-2], bad['sources'][-1]
        try:
            exporter.add_reviewed_sources(copy.deepcopy(original), test_links, graph, {**work_metadata, synthetic['work_id']:synthetic}, bad)
        except ValueError:
            failures += 1
        else:
            raise AssertionError('Unexpectedly accepted '+change)
    report = dict(status='pass', old_sources_checked=len(baseline['sources']), old_reviewed_ids_checked=sum(bool(s['index'].get('reviewed_selection')) for s in baseline['sources']), current_reviewed_ids_checked=len(registry['sources']), old_people_links_checked=25, old_field_selections_checked=5, negative_registry_cases=failures, alphabetically_earlier_append_preserves_old_ids=True, public_exports_written=False)
    (HERE/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
