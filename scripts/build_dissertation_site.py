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


def main():
    explorer_path = RESEARCH / 'summary/explorer/explorer.json'
    data = json.loads(explorer_path.read_text())
    labels = data['labels']
    by_key = {labels[s['id']]['key']: s for s in data['sources']}
    decisions = json.loads((ROOT / 'data/dissertation-layer/links.json').read_text())
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    people = {p['id']: p for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    for pid, decision in decisions['people'].items():
        assert pid in people and decision['source'] in by_key, pid
        for key in decision['works']:
            assert key in by_key, key
    for nid, pids in decisions['entries'].items():
        roster = {r['person_id'] for r in nodes[nid]['representative_people']}
        assert set(pids) <= roster
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
    for row in rows('works'):
        key = 'P:' + row['first_author_key']
        if key in by_key:
            author[row['work_id']] = by_key[key]['id']
        if row['work_id'] in by_key:
            work_ids[row['work_id']] = by_key[row['work_id']]['id']
            if key in by_key:
                works_by_person[by_key[key]['id']].append(by_key[row['work_id']]['id'])
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
    index = []
    shards = {f'{i:02x}.json': {'sources': {}, 'labels': {}} for i in range(BUCKETS)}
    for source in data['sources']:
        sid = source['id']
        label = labels[sid]
        key = label['key']
        assert len(cited[sid]) == source['n'], f'Citation count mismatch: {key}'
        filename = bucket(key)
        index.append({**label, 'id': sid, 'n': source['n'], 'asset': filename})
        refs = {sid} | {r[0] for r in source['rows']}
        refs |= {r[0] for values in source['regional'].values() for r in values}
        shard = shards[filename]
        shard['sources'][str(sid)] = {**source,
            'works': sorted(works_by_person[sid], key=lambda i: -by_key[labels[i]['key']]['n'])[:12],
            'examples': [row for reg in REGIONS for row in samples[sid][reg].values()]}
        refs.update(shard['sources'][str(sid)]['works'])
        shard['labels'].update({str(i): labels[i] for i in sorted(refs)})
    public_links = {**decisions, 'snapshot': '2026-10-23', 'periods': data['periods'],
        'denominators': denominators,
        'people': {pid: {**row, 'label': people[pid]['label'],
            'n': by_key[row['source']]['n'], 'series': by_key[row['source']]['series'],
            'n_region': by_key[row['source']]['n_region'],
            'work_labels': {key: labels[by_key[key]['id']]['short'] for key in row['works']}}
        for pid, row in decisions['people'].items()},
        'entries': {nid: {'label': nodes[nid]['label'], 'people': pids}
                    for nid, pids in decisions['entries'].items()}}
    payload = {k: data[k] for k in ('periods', 'regions', 'denominators', 'families', 'baseline')}
    payload.update(schema_version='1.0', snapshot='2026-10-23', sources=index,
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
                   for p in [explorer_path, ROOT / 'data/dissertation-layer/links.json',
                             *(RELEASE / f'{n}.csv.gz' for n in ('dissertations', 'works', 'citations'))]},
        'outputs': {name: hashlib.sha256((DEST / name).read_bytes()).hexdigest() for name in outputs}}
    (DEST.parent / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Exported {len(index):,} sources, {len(theses):,} dated dissertations in {len(outputs)} assets; '
          f'{sum((DEST / name).stat().st_size for name in outputs) / 1e6:.2f} MB total.')


if __name__ == '__main__':
    main()
