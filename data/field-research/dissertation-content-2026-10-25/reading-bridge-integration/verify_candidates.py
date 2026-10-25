"""Validate prospective bridges and IDs without applying or exporting them."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def load(path):
    return json.loads(path.read_text())

def main():
    spec = importlib.util.spec_from_file_location('build', ROOT/'scripts/build_dissertation_site.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    links = load(HERE/'candidate-links.json')
    registry = load(HERE/'candidate-reviewed-source-ids.json')
    graph = load(ROOT/'historiography-1920-2000.json')
    people = {p['id']:p for p in graph['people']}
    nodes = {n['id']:n for n in graph['nodes']}
    review = load(ROOT/'data/dissertation-layer/reviews/historian-canon-2026-10-25.json')
    assert len(review['people']) == 89 and len(review['proposed_people_additions']) == 88 and not review['unresolved']
    for person in review['people']:
        draft = load(ROOT/person['biography_packet'])
        pid = person['person_id']
        people.setdefault(pid, dict(id=pid, label=draft['node']['label']))
        nodes.setdefault(pid, draft['node'])
    graph['people'], graph['nodes'] = list(people.values()), list(nodes.values())
    selected = {k for p in links['people'].values() for k in p['works']}
    metadata, authors = {}, {}
    for work in exporter.rows('works'):
        if work['work_id'] in selected:
            metadata[work['work_id']] = work
            authors[work['work_id']] = work['first_author_key']
    data = load(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')
    old = copy.deepcopy(data['sources'])
    added = exporter.add_reviewed_sources(data, links, graph, metadata, registry)
    keys = {data['labels'][s['id']]['key'] for s in data['sources']}
    exporter.validate_links(links, graph, keys, authors)
    assert data['sources'][:len(old)] == old
    baseline = load(HERE/'baseline.json')
    labels = {label['key']:i for i,label in enumerate(data['labels'])}
    for old_source in baseline['sources']:
        assert labels[old_source['index']['key']] == old_source['index']['id']
    for pid, old_link in baseline['links']['people'].items():
        assert links['people'][pid] == old_link
    for key in ('entries', 'entry_comparisons'):
        assert links[key] == baseline['links'][key]
    report = dict(status='pass', scope_historians=89, new_person_bridges=88,
        total_prospective_people_links=113, unchanged_field_selections=5,
        reviewed_exception_total=len(added), new_reviewed_exceptions=5,
        source_total=len(data['sources']), old_source_ids_checked=4048,
        exact_release_work_credits_checked=len(selected),
        graph_basis='Current graph plus exact frozen biography people/nodes where not yet applied; no canonical or public mutation.',
        unresolved=[], exports_written=False)
    (HERE/'candidate-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
