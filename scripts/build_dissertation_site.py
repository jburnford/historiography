"""Export the frozen dissertation explorer as small, public metadata assets.

No PDFs, raw citation strings, local paths or research graph are published.
The normal site build copies these checked-in exports; rebuilding them requires
the local explorer and the dated release. Source URLs use stable bibliography
keys; numeric label IDs belong only to this snapshot.
"""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
RELEASE = RESEARCH / 'release/2026-10-23'
DEST = ROOT / 'data/dissertation-layer/site'
REVIEWED_IDS = ROOT / 'data/dissertation-layer/reviewed-source-ids.json'
BUCKETS = 32
REGIONS = ('CA', 'US', 'EUROPE', 'OTHER')
EUROPE = set('AT BE BG CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LI LT LU LV MC ME MK MT NL NO PL PT RO RS SE SI SK UA'.split())


def region(country):
    return country if country in ('CA', 'US') else 'EUROPE' if country in EUROPE else 'OTHER'


def bucket(key):
    return f'{int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % BUCKETS:02x}.json'


def rows(name):
    with gzip.open(RELEASE / f'{name}.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        yield from csv.DictReader(f)


def serial(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n'


def add_reviewed_sources(data, decisions, graph, work_metadata, registry=None):
    """Include reviewed sources even when a search-frequency cutoff hid them.

    Existing source statistics are untouched. New sources get presence counts
    from the release below, without inventing companion or family analyses.
    """
    labels = data['labels']
    label_ids = {label['key']: i for i, label in enumerate(labels)}
    existing = {labels[s['id']]['key'] for s in data['sources']}
    people = {p['id']: p for p in graph['people']}
    chosen = {row['source'] for row in decisions['people'].values()}
    chosen |= {key for row in decisions['people'].values() for key in row['works']}
    person_labels = {row['source']: people[pid]['label'] for pid, row in decisions['people'].items()}
    registry = json.loads(REVIEWED_IDS.read_text()) if registry is None else registry
    base_hash = hashlib.sha256(json.dumps(labels, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':')).encode()).hexdigest()
    if (registry['base_label_count'] != len(labels)
            or registry['base_labels_sha256'] != base_hash):
        raise ValueError('Frozen explorer labels differ from the reviewed source-ID registry')
    registered = registry['sources']
    registered_keys = [row['key'] for row in registered]
    if len(set(registered_keys)) != len(registered_keys):
        raise ValueError('Duplicate reviewed source-ID registry key')
    if set(registered_keys) != chosen - existing:
        raise ValueError('Reviewed selections differ from the append-only source-ID registry: '
                         + repr(sorted(set(registered_keys) ^ (chosen - existing))))
    added = []
    for registered_label in registered:
        key = registered_label['key']
        if registered_label['source_index'] != len(data['sources']):
            raise ValueError('Reviewed source index/order drift: ' + key)
        if key.startswith('W:') and key not in work_metadata:
            raise ValueError('Reviewed work absent from the release: ' + key)
        if key not in label_ids:
            if key.startswith('P:'):
                label = dict(key=key, short=person_labels[key], full=person_labels[key], year=None, author='')
            else:
                row = work_metadata[key]
                label = dict(key=key, short=row['first_author'].split(',')[0]+', '+row['title'].split(':')[0],
                             full=row['title'], year=int(row['year']) if row['year'].isdigit() else None,
                             author=row['first_author'])
            if registered_label['id'] != len(labels):
                raise ValueError('Reviewed source label ID/order drift: ' + key)
            label_ids[key] = len(labels)
            labels.append(label)
        sid = label_ids[key]
        if {k: v for k, v in registered_label.items() if k != 'source_index'} != {**labels[sid], 'id': sid}:
            raise ValueError('Reviewed source label metadata/ID drift: ' + key)
        data['sources'].append(dict(id=sid, n=0, series=[], n_region={}, n_period=[], rows=[], regional={},
                                    analysis_scope='counts_only'))
        added.append(key)
    return set(added)


def validate_links(decisions, graph, source_keys, work_authors=None):
    """A reading bridge requires named works and an existing roster placement.

    This validates an editorial selection, not every attribution behind a person
    key. The release's first-author credit must agree when rebuilding exports.
    """
    people = {p['id'] for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    for pid, decision in decisions['people'].items():
        if pid not in people or decision['source'] not in source_keys or not decision['source'].startswith('P:'):
            raise ValueError('Unknown person reading link: ' + pid)
        works = decision['works']
        if not works or len(set(works)) != len(works):
            raise ValueError('Named works required without duplicates: ' + pid)
        for key in works:
            if key not in source_keys or not key.startswith('W:'):
                raise ValueError('Unknown work reading link: ' + key)
            if work_authors is not None and work_authors.get(key) != decision['source'][2:]:
                raise ValueError('First-author credit differs: ' + key)
    for nid, pids in decisions['entries'].items():
        if nid not in nodes or not pids or len(set(pids)) != len(pids):
            raise ValueError('Unknown or duplicate field selection: ' + nid)
        roster = {r['person_id'] for r in nodes[nid].get('representative_people', [])}
        if not set(pids) <= roster or not set(pids) <= set(decisions['people']):
            raise ValueError('Reading selection is outside the reviewed roster: ' + nid)
    for nid, comparison in decisions.get('entry_comparisons', {}).items():
        if nid not in decisions['entries'] or not comparison['intro'] or not comparison['question']:
            raise ValueError('Comparison needs a reviewed field and reading question: ' + nid)
        works = comparison['works']
        if not works or len({row['work'] for row in works}) != len(works):
            raise ValueError('Comparison needs distinct selected works: ' + nid)
        if {row['person_id'] for row in works} != set(decisions['entries'][nid]):
            raise ValueError('Comparison and field author selections differ: ' + nid)
        for row in works:
            if row['work'] not in decisions['people'][row['person_id']]['works']:
                raise ValueError('Comparison work is outside the reviewed author selection: ' + row['work'])
    for pid, comparison in decisions.get('person_comparisons', {}).items():
        if pid not in decisions['people'] or not comparison.get('intro') or not comparison.get('question'):
            raise ValueError('Person comparison needs a reviewed profile and reading question: ' + pid)
        works = comparison.get('works', [])
        if not works or len({row['work'] for row in works}) != len(works):
            raise ValueError('Person comparison needs distinct selected works: ' + pid)
        for row in works:
            if row['person_id'] != pid or row['work'] not in decisions['people'][pid]['works']:
                raise ValueError('Person comparison work is outside this author selection: ' + row['work'])


def comparison_payload(comparison, pids, decisions, people, by_key, labels):
    return {**{k: v for k, v in comparison.items() if k != 'works'},
        'authors': [{'key': decisions['people'][pid]['source'], 'person_id': pid,
            'label': people[pid]['label'],
            **{k: by_key[decisions['people'][pid]['source']][k] for k in ('n', 'n_region', 'series')}} for pid in pids],
        'sources': [{'key': row['work'], 'person_id': row['person_id'],
            'label': labels[by_key[row['work']]['id']]['short'],
            **{k: by_key[row['work']][k] for k in ('n', 'n_region', 'series')}} for row in comparison['works']]}


def main():
    explorer_path = RESEARCH / 'summary/explorer/explorer.json'
    data = json.loads(explorer_path.read_text())
    labels = data['labels']
    by_key = {labels[s['id']]['key']: s for s in data['sources']}
    decisions = json.loads((ROOT / 'data/dissertation-layer/links.json').read_text())
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    people = {p['id']: p for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    # Check the dated release against the explorer's actual time/region denominator.
    theses = {}
    total = 0
    denominators = [[0] * len(REGIONS) for _ in data['periods']]
    coverage = Counter()
    notes = 0
    years = []
    for row in rows('dissertations'):
        if row['in_analysis'] != 'True':
            continue
        total += 1
        if not row['year']:
            continue
        year = int(row['year'])
        p = 0 if year < 1990 else min(7, 1 + (year - 1990) // 5)
        reg = region(row['country'])
        denominators[p][REGIONS.index(reg)] += 1
        coverage[(reg, row['country'], row['institution'])] += 1
        notes += row['bibliography_source'] == 'notes'
        years.append(year)
        theses[row['dissertation_id']] = {k: row[k] for k in
            ('dissertation_id', 'title', 'authors', 'institution', 'country', 'bibliography_source', 'item_url')}
        theses[row['dissertation_id']]['year'] = year
    assert denominators == data['denominators'], 'Release and explorer denominators differ; rebuild the explorer first.'
    # The research explorer labels its last, open bin 2020–25, but the
    # frozen release also contains 2026 degrees. Name the actual interval.
    data['periods'][-1] = f'2020–{max(years)}'
    # Sample source-linked dissertations, up to two per region. The examples are
    # illustrative, not a representative sample or a replacement for the counts.
    author = {}
    works_by_person = defaultdict(list)
    work_ids = {}
    work_authors = {}
    selected_work_keys = {key for row in decisions['people'].values() for key in row['works']}
    work_metadata = {}
    for row in rows('works'):
        work_authors[row['work_id']] = row['first_author_key']
        if row['work_id'] in selected_work_keys:
            work_metadata[row['work_id']] = row
    curated = add_reviewed_sources(data, decisions, graph, work_metadata)
    by_key = {labels[s['id']]['key']: s for s in data['sources']}
    for work_id, first_author in work_authors.items():
        key = 'P:' + first_author
        if key in by_key:
            author[work_id] = by_key[key]['id']
        if work_id in by_key:
            work_ids[work_id] = by_key[work_id]['id']
            if key in by_key:
                works_by_person[by_key[key]['id']].append(by_key[work_id]['id'])
    validate_links(decisions, graph, set(by_key), work_authors)
    samples = defaultdict(lambda: defaultdict(dict))
    cited = defaultdict(set)
    for row in rows('citations'):
        tid = row['dissertation_id']
        if tid not in theses:
            continue
        for sid in {author.get(row['work_id']), work_ids.get(row['work_id'])} - {None}:
            cited[sid].add(tid)
            reg = region(theses[tid]['country'])
            if tid in samples[sid][reg] or len(samples[sid][reg]) < 2:
                samples[sid][reg][tid] = {**theses[tid], 'via': row['via']}
    for key in curated:
        source = by_key[key]
        sid = source['id']
        series = [[0] * len(REGIONS) for _ in data['periods']]
        for tid in cited[sid]:
            thesis = theses[tid]
            year = thesis['year']
            p = 0 if year < 1990 else min(7, 1 + (year - 1990) // 5)
            series[p][REGIONS.index(region(thesis['country']))] += 1
        source.update(n=len(cited[sid]), series=series,
                      n_period=[sum(row) for row in series],
                      n_region={r: sum(row[j] for row in series) for j, r in enumerate(REGIONS)})
    index = []
    shards = {f'{i:02x}.json': {'sources': {}, 'labels': {}} for i in range(BUCKETS)}
    for source in data['sources']:
        sid = source['id']
        label = labels[sid]
        key = label['key']
        assert len(cited[sid]) == source['n'], f'Citation count mismatch: {key}'
        filename = bucket(key)
        index.append({**label, 'id': sid, 'n': source['n'], 'asset': filename,
                      **({'reviewed_selection': True} if key in curated else {})})
        refs = {sid} | {r[0] for r in source['rows']}
        refs |= {r[0] for values in source['regional'].values() for r in values}
        shard = shards[filename]
        shard['sources'][str(sid)] = {**source,
            'works': sorted(works_by_person[sid], key=lambda i: -by_key[labels[i]['key']]['n'])[:12],
            'examples': [row for reg in REGIONS for row in samples[sid][reg].values()]}
        refs.update(shard['sources'][str(sid)]['works'])
        shard['labels'].update({str(i): labels[i] for i in sorted(refs)})
    public_links = {**{k: v for k, v in decisions.items() if k not in ('entry_comparisons', 'person_comparisons')},
        'snapshot': '2026-10-23', 'periods': data['periods'], 'regions': data['regions'],
        'denominators': denominators,
        'coverage': {'in_analysis': total, 'with_year': len(theses), 'missing_year': total - len(theses)},
        'search_thresholds': {'works': data['params']['min_work'], 'people': data['params']['min_person']},
        'people': {pid: {**row, 'label': people[pid]['label'],
            'n': by_key[row['source']]['n'], 'series': by_key[row['source']]['series'],
            'n_region': by_key[row['source']]['n_region'],
            'work_labels': {key: labels[by_key[key]['id']]['short'] for key in row['works']},
            **({'comparison': comparison_payload(decisions['person_comparisons'][pid], [pid],
                decisions, people, by_key, labels)} if pid in decisions.get('person_comparisons', {}) else {})}
        for pid, row in decisions['people'].items()},
        'entries': {nid: {'label': nodes[nid]['label'], 'people': pids,
                         **({'comparison': comparison_payload(decisions['entry_comparisons'][nid],
                            pids, decisions, people, by_key, labels)}
                            if nid in decisions.get('entry_comparisons', {}) else {})}
                    for nid, pids in decisions['entries'].items()}}
    payload = {k: data[k] for k in ('periods', 'regions', 'denominators', 'families', 'baseline')}
    payload.update(schema_version='1.0', snapshot='2026-10-23', sources=index,
        reviewed_selection_count=len(curated),
        params={k: v for k, v in data['params'].items() if k != 'out'},
        coverage={'in_analysis': total, 'with_year': len(theses), 'missing_year': total - len(theses),
                  'from_notes_with_year': notes, 'years': [min(years), max(years)],
                  'institutions': [{'region': reg, 'country': cc, 'institution': inst, 'n': n}
                                   for (reg, cc, inst), n in sorted(coverage.items())]})
    DEST.mkdir(parents=True, exist_ok=True)
    outputs = {'index.json': payload, 'links.json': public_links, **shards}
    for name, value in outputs.items():
        (DEST / name).write_text(serial(value))
    manifest = {'snapshot': '2026-10-23',
        'inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [explorer_path, ROOT / 'data/dissertation-layer/links.json', REVIEWED_IDS,
                             *(RELEASE / f'{n}.csv.gz' for n in ('dissertations', 'works', 'citations'))]},
        'outputs': {name: hashlib.sha256((DEST / name).read_bytes()).hexdigest() for name in outputs}}
    (DEST.parent / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Exported {len(index):,} sources, {len(theses):,} dated dissertations in {len(outputs)} assets; '
          f'{sum((DEST / name).stat().st_size for name in outputs) / 1e6:.2f} MB total.')


if __name__ == '__main__':
    main()
