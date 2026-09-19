"""Read-only inventory of the neighbouring research corpus; no graph imports.

Run from any directory. Writes discovery artifacts under data/extension-2026.
Source text hits and existing-person name matches are unverified leads.
"""
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/home/jic823/capitalism')
DEST = ROOT / 'data/extension-2026/capitalism-mining'
QUERIES = {
    'new_capitalism': '"new history of capitalism"',
    'great_divergence': '"great divergence"',
    'anthropocene': '"Anthropocene"',
    'capitalocene': '"Capitalocene"',
    'world_ecology': '"world ecology"',
    'racial_capitalism': '"racial capitalism"',
    'settler_colonial': '"settler colonial"',
    'more_than_human': '"more than human"',
    'animal': '"animal history" OR "animal studies"',
    'climate': '"climate history" OR "history of climate" OR "historical climatology"',
    'oceanic': '"oceanic" OR "marine environment" OR "Pacific world"',
    'energy_history': '"energy history" OR "fossil capital"',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value):
    return re.sub(r'[^\w]+', ' ', value.casefold()).strip()


def write_json(name, value):
    (DEST / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(name, rows):
    if not rows:
        return
    with (DEST / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict))
                             else v for k, v in row.items()})


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    inputs = ['corpus/CATALOG.tsv', 'corpus/corpus.db', 'field_graph/sources.json',
              'field_graph/works.jsonl', 'field_graph/edges.jsonl', 'field_graph/stances.json',
              'reading_list/works.json', 'field_graph/claims_register.md']
    before = {rel: sha(SOURCE / rel) for rel in inputs}
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    with (SOURCE / 'corpus/CATALOG.tsv').open() as stream:
        catalog = list(csv.DictReader(stream, delimiter='\t'))
    holdings = []
    for row in catalog:
        text_path = SOURCE / row['source_dir'] / (Path(row['slug']).name + '.txt')
        holdings.append({**row, 'local_text_path': str(text_path),
                         'text_exists': text_path.is_file(),
                         'text_sha256': sha(text_path) if text_path.is_file() else None,
                         'review_status': 'inventory_only'})
    write_json('corpus-holdings.json', holdings)
    write_csv('corpus-holdings.csv', holdings)

    source_rows = []
    for source in json.loads((SOURCE / 'field_graph/sources.json').read_text()):
        resource = SOURCE / source['pdf'] if source.get('pdf') else None
        source_rows.append({
            'source_id': source['id'], 'citation': source['citation'],
            'kind': source.get('kind'), 'declared_resource': str(resource) if resource else None,
            'resource_state': 'file' if resource and resource.is_file() else
                              'directory' if resource and resource.is_dir() else
                              'missing' if resource else 'not_declared',
            'resource_sha256': sha(resource) if resource and resource.is_file() else None,
            'inherited_work_id': source.get('work_id'),
            'existing_person_name_leads': [p['id'] for p in graph['people']
                                          if len(p['label']) > 8 and norm(p['label']) in norm(source['citation'])],
            'review_status': 'unverified_metadata_and_name_leads',
            'warning': 'Declared proxy/excerpt/preprint and corpus processing status do not prove full-text verification.',
        })
    write_json('source-register.json', source_rows)
    write_csv('source-register.csv', source_rows)

    reading = json.loads((SOURCE / 'reading_list/works.json').read_text())
    reading_rows = []
    for work in reading['works']:
        reading_rows.append({k: work.get(k) for k in ['id', 'cat', 'strand', 'tags', 'type', 'year',
                                                     'authors', 'title', 'venue']})
    # Deliberately omit model/editorial annotations: those are not verified claims.
    write_json('reading-list-leads.json', reading_rows)
    write_csv('reading-list-leads.csv', reading_rows)

    db = sqlite3.connect(f'file:{SOURCE / "corpus/corpus.db"}?mode=ro', uri=True)
    hits = []
    counts = {}
    for candidate, query in QUERIES.items():
        found = db.execute('''SELECT c.slug, a.source_dir, c.line_start, c.line_end
            FROM chunk_fts JOIN chunks c ON c.id=chunk_fts.id
            JOIN catalog a ON a.slug=c.slug WHERE chunk_fts MATCH ?
            ORDER BY c.slug, c.line_start''', (query,)).fetchall()
        counts[candidate] = {'matching_chunks': len(found),
                             'distinct_source_slugs': len({r[0] for r in found})}
        for slug, directory, start, end in found:
            hits.append({'candidate_id': candidate, 'query': query, 'slug': slug,
                         'local_path': str(SOURCE / directory / (Path(slug).name + '.txt')),
                         'line_start_hint': start, 'line_end_hint': end,
                         'evidence_status': 'search_hit_only'})
    chunk_count = db.execute('select count(*) from chunks').fetchone()[0]
    db.close()
    write_csv('topic-search-leads.csv', hits)
    raw_counts = {name: sum(1 for line in (SOURCE / f'field_graph/{name}.jsonl').open() if line.strip())
                  for name in ['works', 'edges']}
    after = {rel: sha(SOURCE / rel) for rel in inputs}
    if before != after:
        raise RuntimeError('Source inputs changed during mining; inspect before treating output as a fixed capture.')
    write_json('summary.json', {
        'as_of': '2026-09-18', 'source_root': str(SOURCE), 'input_sha256': before,
        'source_inputs_unchanged': True, 'catalog_entries': len(catalog),
        'existing_text_files': sum(r['text_exists'] for r in holdings), 'indexed_chunks': chunk_count,
        'registered_sources': len(source_rows), 'resource_states': dict(Counter(r['resource_state'] for r in source_rows)),
        'reading_list_entries': len(reading_rows), 'reading_list_categories': len(reading['categories']),
        'inherited_raw_record_counts': raw_counts, 'query_counts': counts,
        'graph_imports': 0, 'limitations': [
            'Counts describe this selected corpus, not the field.',
            'Catalogue includes duplicates, excerpts and source variants.',
            'Raw bibliography has malformed records; no automatic work or authority reconciliation.',
            'Search locators are finding aids; verify passages in context before making claims.',
            'No scholarly citation-service data merged and no OpenAlex requests made.',
        ],
    })
    print(json.dumps({'catalog_entries': len(catalog), 'sources': len(source_rows),
                      'reading_list_entries': len(reading_rows), 'search_hits': len(hits),
                      'raw_counts': raw_counts, 'source_inputs_unchanged': before == after}))


if __name__ == '__main__':
    main()
