"""Check amendment candidates/public preservation without changing exports."""
from copy import deepcopy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text())

def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def main():
    spec = importlib.util.spec_from_file_location('exporter', ROOT/'scripts/build_dissertation_site.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    baseline = read(HERE/'baseline.json')
    candidate = read(HERE/'candidate-links.json')
    registry = read(HERE/'candidate-reviewed-source-ids.json')
    counts = read(HERE/'count-witnesses.json')
    review = read(ROOT/'data/dissertation-layer/reviews/historian-amendment-2026-10-25.json')
    index = read(ROOT/'data/dissertation-layer/site/index.json')
    current_links = read(ROOT/'data/dissertation-layer/links.json')
    public_links = read(ROOT/'data/dissertation-layer/site/links.json')
    indexed = {r['key']:r for r in index['sources']}
    exported = 'benedict_anderson' in public_links['people']
    actual_links_expected = candidate if 'benedict_anderson' in current_links['people'] else baseline['links']
    assert current_links == actual_links_expected
    assert len(candidate['people']) == 116
    assert candidate['entries'] == baseline['links']['entries']
    assert candidate['entry_comparisons'] == baseline['links']['entry_comparisons']
    assert registry['sources'][:16] == baseline['registry']['sources']
    assert len(registry['sources']) == 18
    assert registry['sources'][16]['id'] == 5953 and registry['sources'][16]['source_index'] == 4053
    assert registry['sources'][17]['id'] == 12158 and registry['sources'][17]['source_index'] == 4054
    for pid, row in baseline['links']['people'].items():
        assert candidate['people'][pid] == row
        assert public_links['people'][pid] == baseline['public_links']['people'][pid]
    assert public_links['entries'] == baseline['public_links']['entries']
    assert sha({k:v for k,v in index.items() if k not in ('sources','reviewed_selection_count')}) == baseline['index_context_sha256']
    shards, old_work_changes = {}, []
    for old in baseline['sources']:
        row = old['index']
        assert indexed[row['key']] == row, row['key']
        assert index['sources'][old['index_position']] == row, row['key']
        if row['asset'] not in shards:
            shards[row['asset']] = read(ROOT/'data/dissertation-layer/site'/row['asset'])
        source = shards[row['asset']]['sources'][str(row['id'])]
        assert sha({k:source[k] for k in ('n','series','n_region')}) == old['numeric_sha256'], row['key']
        assert sha({k:v for k,v in source.items() if k != 'works'}) == old['source_without_works_sha256'], row['key']
        expected = old['work_ids']
        if exported and row['key'] == 'P:anderson|benedict r':
            expected = [3,5953,12158]
        assert source['works'] == expected, row['key']
        if source['works'] != old['work_ids']:
            old_work_changes.append(row['key'])
    graph = read(ROOT/'historiography-1920-2000.json')
    selected = {k for p in candidate['people'].values() for k in p['works']}
    metadata = {w['work_id']:w for w in exporter.rows('works') if w['work_id'] in selected}
    authors = {k:w['first_author_key'] for k,w in metadata.items()}
    data = read(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')
    exporter.add_reviewed_sources(data, candidate, graph, metadata, registry)
    by_key = {data['labels'][s['id']]['key']:s for s in data['sources']}
    exporter.validate_links(candidate, graph, set(by_key), authors)
    for old in baseline['sources']:
        assert by_key[old['index']['key']]['id'] == old['index']['id']
    for key in candidate['people']['benedict_anderson']['works']:
        for field in ('n','series','n_region'):
            by_key[key][field] = counts['sources'][key][field]
    comparison = exporter.comparison_payload(candidate['person_comparisons']['benedict_anderson'],
        ['benedict_anderson'], candidate, {p['id']:p for p in graph['people']}, by_key, data['labels'])
    assert comparison['default_view'] == 'works'
    assert [p['person_id'] for p in comparison['authors']] == ['benedict_anderson']
    assert comparison['authors'][0]['n'] == 716
    assert [s['key'] for s in comparison['sources']] == candidate['people']['benedict_anderson']['works']
    assert [s['n'] for s in comparison['sources']] == [641,16,14]
    assert '89.5%' in comparison['intro']
    assert '685' in comparison['observation'] and '95.7%' in comparison['observation']
    audit = HERE.parent/'anderson-book-identity'
    union_records = read(audit/'citation-unions.json')
    decisions = read(audit/'decisions.json')
    positive = {r['work_id'] for r in decisions['decisions'] if r['assigned_to_book_union']}
    assert len(positive) == 16
    family = set().union(*(set(r['dated_in_analysis_dissertation_ids']) for r in union_records['per_work']
                          if r['work_id'] in positive))
    assert family == set(union_records['dated_in_analysis_confirmed_book_union_dissertation_ids'])
    main = set(union_records['dated_in_analysis_main_book_key_dissertation_ids'])
    person = set(union_records['dated_in_analysis_first_author_P_dissertation_ids'])
    assert len(family) == 685 and len(main) == 641 and len(person) == 716
    assert main <= family <= person
    assert family-main == set(union_records['additional_book_dissertation_ids_beyond_main_key'])
    assert len(family-main) == 44
    family_regions = Counter()
    for row in exporter.rows('dissertations'):
        if row['dissertation_id'] in family:
            assert row['in_analysis'] == 'True' and row['year']
            family_regions[exporter.region(row['country'])] += 1
    assert dict(family_regions) == {'CA':280,'US':251,'EUROPE':121,'OTHER':33}
    for name, expected in counts['source_file_sha256'].items():
        assert hashlib.sha256((exporter.RELEASE/(name+'.csv.gz')).read_bytes()).hexdigest() == expected
    source_ids = {s['id'] for s in read(audit/'sources.json')['sources']}
    assert all(r['source_ids'] and set(r['source_ids']) <= source_ids
               for r in decisions['decisions'] if r['assigned_to_book_union'])
    for filename, expected in review['anderson_book_family_review']['input_sha256'].items():
        assert hashlib.sha256((audit/filename).read_bytes()).hexdigest() == expected
    for record in comparison['sources']+comparison['authors']:
        for field in ('n','series','n_region'):
            assert record[field] == counts['sources'][record['key']][field]
    negatives = 0
    for kind in ('cross_person','unselected_work','duplicate_work','missing_intro'):
        wrong = deepcopy(candidate)
        c = wrong['person_comparisons']['benedict_anderson']
        if kind == 'cross_person': c['works'][0]['person_id'] = 'sidney_mintz'
        if kind == 'unselected_work': c['works'][0]['work'] = 'W:mintz|sweetness and power'
        if kind == 'duplicate_work': c['works'].append(deepcopy(c['works'][0]))
        if kind == 'missing_intro': c['intro'] = ''
        try:
            exporter.validate_links(wrong, graph, set(by_key), authors)
        except ValueError:
            negatives += 1
        else:
            raise AssertionError('Invalid personal comparison accepted: '+kind)
    if exported:
        assert len(index['sources']) == 4055 and index['reviewed_selection_count'] == 18
        assert public_links['people']['benedict_anderson']['comparison'] == comparison
        assert len(public_links['people']) == 116
    report = dict(status='pass' if not review['unresolved'] else 'count_checks_pass_primary_evidence_pending',
        old_sources_checked=4053, old_profiles_preserved=113, old_field_panels_preserved=5,
        old_registry_rows_preserved=16, proposed_source_count=4055, proposed_profiles=116,
        proposed_reviewed_exceptions=18, comparison_negative_cases=negatives,
        comparison_work_counts=[641,16,14], comparison_author_key_count=716,
        separate_book_family_union=685, family_positive_work_keys=16,
        additional_family_dissertations_beyond_main_key=44,
        exact_release_work_credits_checked=len(metadata), old_source_work_list_changes=old_work_changes,
        exported=exported, unresolved=review['unresolved'])
    (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (HERE/'candidate-comparison-payload.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
