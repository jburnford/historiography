#!/usr/bin/env python3
"""Offline scope/date audit and source-linked index of both dissertation batches.

No topic-based programme inference. Original metadata and the first pilot stay
unchanged; the index points to exact JSONL source rows rather than duplicating them.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

from expand_canadian_dissertation_metadata import expand_normalization, folded, EXACT_HISTORY
from harvest_canadian_history_dissertations import values, write_json

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / 'data/field-research/canadian-dissertations-2026-10-10'
BATCH = ROOT / 'data/field-research/canadian-dissertations-2026-10-11'
PROGRAM_KEYS = ['dc.degree.discipline', 'thesis.degree.discipline', 'dc.degree.programme',
                'uws-etd.degree.discipline', 'etdms.degree.discipline', 'etd.degree.discipline']
LAVAL_QUERY = ('etdms.degree.discipline:"Doctorat en histoire" OR '
               'etdms.degree.discipline:"Maîtrise en histoire" OR '
               'etdms.degree.name:"Thèse. Histoire" OR '
               'etdms.degree.name:"Mémoire. Histoire"')
LAVAL_BASE = ('https://corpus.ulaval.ca/server/api/discover/search/objects?'
              'scope=32fa194e-af6e-41d8-bde3-fae02aed6899&query=')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def history_label(value):
    # Full labels only: art history and history of science remain distinct.
    return folded(value) in EXACT_HISTORY | {'maitrise en histoire - avec memoire'}


def scope_review(row):
    md = row['metadata']
    programmes = values(md, *PROGRAM_KEYS)
    # Ottawa uses "Arts" in degree.discipline for the degree/faculty family;
    # its separate uottawa.department and dc.faculty.department name History.
    if row['institution'] == 'ottawa':
        programmes = [p for p in programmes if folded(p) != 'arts']
    # Laval mixes programme labels and catalogue call numbers in this field.
    if row['institution'] == 'laval':
        programmes = [p for p in programmes if re.match(r'^(doctorat|ma[iî]trise)\b', p, re.I)]
    degree_history = any(re.fullmatch(r'(doctor of philosophy|master[s]? of arts) in history', folded(d))
                         or re.fullmatch(r'(these|memoire)\.\s*histoire\.?', folded(d))
                         for d in row['degree'])
    degree_other = any(re.search(r'\bin (classics|classical studies)\b', folded(d)) for d in row['degree'])
    explicit_history = any(history_label(p) for p in programmes) or degree_history
    other_programme = any(not history_label(p) for p in programmes)
    if explicit_history and (other_programme or degree_other):
        status = 'conflicting_programme_requires_review'
    elif explicit_history:
        status = 'explicit_history'
    elif other_programme or degree_other:
        status = ('conflicting_programme_requires_review' if row['history_metadata_exact']
                  else 'other_or_adjacent_programme')
    elif row['history_metadata_exact']:
        status = 'explicit_history'
    elif row['history_scope'] == 'combined_department_requires_program_review':
        status = 'combined_department_requires_review'
    else:
        status = 'unresolved_collection_only'
    kind = row['degree_classification']
    types = values(md, 'dc.type')
    doctoral_type = any(folded(t) in {'these de doctorat', 'doctoral thesis'} for t in types)
    masters_type = any(folded(t) in {'memoire de maitrise', 'master thesis'} for t in types)
    # Explicit repository types resolve legacy Laval degree labels; contradictions
    # in a record remain unresolved, including UNB's M.A./doctoral mismatch.
    if doctoral_type and masters_type:
        kind = 'conflicting_degree'
    elif doctoral_type:
        kind = 'conflicting_degree' if kind in {'masters', 'conflicting_degree'} else 'doctoral'
    elif masters_type:
        kind = 'conflicting_degree' if kind in {'doctoral', 'conflicting_degree'} else 'masters'
    non_thesis = bool(types) and all(folded(t) in {
        'article', 'technical report', 'conference paper', 'book', 'other',
        'book chapter', 'white paper'} for t in types)
    if non_thesis:
        status = 'non_thesis_material'
    return dict(scope_status=status, degree_review=kind, programme_labels=programmes,
                degree_name_history=degree_history, repository_types=types,
                doctoral_history_eligible=(kind == 'doctoral' and status == 'explicit_history'))


def normalize_laval():
    folder = BATCH / 'laval-public'
    rows, streams, logs = {}, [], []
    for prefix, query in [('laval-doctorat-histoire', '"Doctorat en histoire"'),
                          ('laval-history-fields', LAVAL_QUERY)]:
        paths = sorted((folder / 'raw').glob(prefix + '-*.json'))
        assert paths, prefix
        seen, expected = [], None
        for page, path in enumerate(paths):
            data = json.loads(path.read_text())['_embedded']['searchResult']
            assert data['page']['number'] == page
            expected = expected if expected is not None else data['page']['totalElements']
            assert data['page']['totalElements'] == expected
            logs.append(dict(file=str(path.relative_to(folder)), sha256=sha(path),
                url=LAVAL_BASE + quote(query, safe='') + f'&size=100&page={page}',
                checked_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                client='curl; public API; no authentication'))
            for hit in data.get('_embedded', {}).get('objects', []):
                item = hit['_embedded']['indexableObject']
                assert item['type'] == 'item'
                row = expand_normalization(item, 'laval', 'https://corpus.ulaval.ca')
                seen.append(row['id'])
                if row['id'] in rows:
                    assert rows[row['id']]['metadata'] == row['metadata']
                    rows[row['id']]['streams'].append(prefix)
                else:
                    rows[row['id']] = dict(row, streams=[prefix])
        assert len(paths) == data['page']['totalPages']
        assert len(seen) == len(set(seen)) == expected
        streams.append(dict(id=prefix, query=query, reported_total=expected, complete_query=True))
    # Avoid repeating provenance when a record was returned by both queries.
    for row in rows.values():
        row['streams'] = list(dict.fromkeys(row['streams']))
    with (folder / 'records.jsonl').open('w') as file:
        for row in rows.values():
            file.write(json.dumps(row, ensure_ascii=False) + '\n')
    write_json(folder / 'requests.json', logs)
    write_json(folder / 'summary.json', dict(streams=streams, unique_records=len(rows)))


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    normalize_laval()
    first_acceptance = json.loads((FIRST / 'acceptance.json').read_text())
    for name, expected in first_acceptance['outputs'].items():
        assert sha(FIRST / name) == expected, f'First pilot changed: {name}'
    protected = first_acceptance['input_hashes']
    for name, expected in protected.items():
        assert sha(ROOT / name) == expected, f'Protected source/public input changed: {name}'
    raw_count = 0
    for folder in [FIRST / 'metadata', BATCH / 'metadata', BATCH / 'laval-retry', BATCH / 'laval-public']:
        for req in json.loads((folder / 'requests.json').read_text()):
            assert sha(folder / req['file']) == req['sha256']
            raw_count += 1
    main_summary = json.loads((BATCH / 'metadata/summary.json').read_text())
    for stream in main_summary['streams']:
        if 'reported_total' not in stream:
            continue
        pages = sorted((BATCH / 'metadata/raw').glob(stream['id'] + '-*.json'))
        ids = []
        for page, path in enumerate(pages):
            result = json.loads(path.read_text())['_embedded']['searchResult']
            assert result['page']['number'] == page
            assert result['page']['totalElements'] == stream['reported_total']
            ids.extend(hit['_embedded']['indexableObject']['uuid']
                       for hit in result.get('_embedded', {}).get('objects', []))
        assert len(pages) == max(1, result['page']['totalPages'])
        assert len(ids) == len(set(ids)) == stream['reported_total']
    files = [FIRST / 'metadata/records.jsonl', BATCH / 'metadata/records.jsonl',
             BATCH / 'laval-public/records.jsonl']
    index, seen, totals, date_audit, issues = [], set(), defaultdict(Counter), defaultdict(Counter), []
    degree_dates = []
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    for source in files:
        for line, text in enumerate(source.open(), 1):
            row = json.loads(text)
            key = (row['institution'], row['id'])
            assert key not in seen
            seen.add(key)
            # First pilot lacks the expanded convenience fields: derive a review
            # view from its raw metadata without editing that pilot's outputs.
            current = expand_normalization(dict(uuid=row['id'], metadata=row['metadata']),
                                           row['institution'], '')
            result = scope_review(current)
            entry = dict(institution=row['institution'], id=row['id'], title=row['title'],
                authors=row['authors'], item_url=row['item_url'],
                source_file=str(source.relative_to(ROOT)), source_line=line,
                **result)
            index.append(entry)
            t, d = totals[row['institution']], date_audit[row['institution']]
            t['metadata_records'] += 1
            t[result['degree_review']] += 1
            t['scope:' + result['scope_status']] += 1
            if result['doctoral_history_eligible']:
                t['doctoral_history_eligible'] += 1
                if current['graduation_dates']:
                    d['with_explicit_graduation_or_convocation'] += 1
                    degree_dates.append(dict(institution=row['institution'], id=row['id'],
                        date_fields={k: values(row['metadata'], k) for k in
                                     ['ual.date.graduation','dc.date.convocation'] if k in row['metadata']},
                        source_file=entry['source_file'], source_line=line))
                if not row['issued_dates']:
                    d['missing_issued_dates'] += 1
                if not row['abstract']:
                    d['missing_abstracts'] += 1
                    if values(row['metadata'], 'dc.description', 'dcterms.description'):
                        d['with_unreviewed_description_candidate'] += 1
                if row['issued_dates'] and row['accession_dates'] and row['issued_dates'][0][:10] == row['accession_dates'][0][:10]:
                    d['issued_matches_accession_day'] += 1
                years = [re.match(r'^\d{4}', v).group() for v in row['issued_dates'] if re.match(r'^\d{4}', v)]
                for year in years:
                    d['issued_year:' + year] += 1
            if result['degree_review'] == 'doctoral':
                t['doctoral_scope:' + result['scope_status']] += 1
            if result['scope_status'] not in {'explicit_history', 'combined_department_requires_review'} or result['degree_review'] in {'conflicting_degree','unspecified'}:
                issues.append(entry)
    # The original accepted doctoral set must retain its membership count.
    assert sum(totals[i]['doctoral_history_eligible'] for i in ['york','usask','queens','toronto','western']) == 614
    with (out / 'combined-index.jsonl').open('w') as file:
        for entry in index:
            file.write(json.dumps(entry, ensure_ascii=False) + '\n')
    with (out / 'combined-index.csv').open('w', newline='') as file:
        fields = ['institution','id','title','degree_review','scope_status',
                  'doctoral_history_eligible','item_url','source_file','source_line']
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in index)
    write_json(out / 'scope-issues.json', issues)
    write_json(out / 'date-audit.json', dict(institutions=dict(date_audit), explicit_degree_dates=degree_dates,
        qualifications=['Issued-year counts are retrieval descriptions, not graduation or historiographical trend estimates.',
                        'Explicit graduation/convocation fields remain separate from publication, copyright and deposit dates.',
                        'Missing abstracts means absent normalized abstract fields; generic description fields remain unreviewed candidates.',
                        'Laurier availability dates of 1900 are placeholders; OAI datestamps are repository changes.']))
    write_json(out / 'summary.json', dict(unique_records=len(index), institutions=dict(totals),
        doctoral_history_eligible=sum(v['doctoral_history_eligible'] for v in totals.values()),
        doctoral_combined_department_candidates=sum(v['doctoral_scope:combined_department_requires_review'] for v in totals.values()),
        full_dissertation_pdfs_downloaded=0, ubc_status='pending access; not an absent cohort',
        unit='unique institution/repository-ID records; joint programmes may duplicate an underlying degree across repositories'))
    write_json(out / 'validation.json', dict(status='passed', raw_response_hashes_verified=raw_count,
        first_pilot_outputs_verified=len(first_acceptance['outputs']), protected_inputs=protected,
        normalized_source_hashes=source_hashes, unique_institution_record_keys=len(seen),
        first_pilot_doctoral_history_retained=614,
        checks=['Laval complete stable scoped pagination and no duplicates',
                'Exact programme labels; adjacent disciplines and conflicting departmental tags retained separately',
                'French degree levels and repository types checked; contradictory degrees remain unresolved',
                'No title/topic inference for programme or identity; no thesis bodies downloaded']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
