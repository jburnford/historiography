#!/usr/bin/env python3
"""Bounded public DSpace metadata harvest; no credentials or thesis PDF downloads.

Keep repository coverage, degree and dating evidence distinct. This produces a
feasibility corpus, not accepted historiographical classifications or graph data.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STREAMS = [
    ('york', 'https://yorkspace.library.yorku.ca', 'c78c1a40-9669-4b44-a0b7-b392f66dfcf1', None, None, 'History collection'),
    ('usask', 'https://harvest.usask.ca', 'c58530ca-7de1-416a-81bc-4b715d1ddf2e', 'degreeDepartment', 'History', 'Graduate theses, exact History department'),
    ('queens', 'https://queensu.scholaris.ca', '1694b951-714f-4aa9-8edc-e4d286401ee9', None, None, 'History graduate theses collection'),
    ('toronto', 'https://utoronto.scholaris.ca', '68d2b06c-86d1-4923-8545-66abbd105d96', 'department', 'History', 'Doctoral collection 2009 onward, exact History department'),
    ('toronto-older', 'https://utoronto.scholaris.ca', '4d1d0cec-c1be-4cb2-a357-13245710c711', 'department', 'History', 'Selected digitized pre-mandate theses, exact History department'),
    ('western', 'https://uwo.scholaris.ca', '0dc18082-11d8-472c-9cbb-0c254914435a', 'discipline', 'History', 'Theses collection, exact History discipline'),
    ('western-older', 'https://uwo.scholaris.ca', '4327e040-5ebf-4a23-b121-1632eaeac0d0', 'discipline', 'History', 'Digitized theses collection, exact History discipline'),
]


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def values(metadata, *keys):
    return [x['value'] for k in keys for x in metadata.get(k, [])]


def normalize(item, stream, base):
    md = item['metadata']
    degree = values(md, 'dc.degree.name', 'dc.description.degree', 'thesis.degree.name')
    level = values(md, 'dc.degree.level', 'thesis.degree.level')
    text = ' '.join(degree + level).lower()
    # Avoid treating every thesis or History subject as a doctorate.
    doctoral = bool(re.search(r'\bdoctoral\b|\bdoctor of philosophy\b|\bph\s*\.?\s*d\b', text))
    masters = bool(re.search(r'\bmaster|\bma\b|\bm\.?\s*a\b', text))
    classification = 'conflicting_degree' if doctoral and masters else ('doctoral' if doctoral else 'masters' if masters else 'unspecified')
    departments = values(md, 'dc.degree.discipline', 'dc.contributor.department', 'thesis.degree.department', 'thesis.degree.discipline')
    return dict(institution=stream.split('-')[0], stream=stream, id=item['uuid'],
                title='; '.join(values(md, 'dc.title')), authors=values(md, 'dc.creator', 'dc.contributor.author'),
                degree=degree, degree_level=level, degree_classification=classification,
                department_discipline=departments, history_metadata_exact=any(v.strip().lower() == 'history' for v in departments),
                issued_dates=values(md, 'dc.date.issued'), accession_dates=values(md, 'dc.date.accessioned'),
                created_dates=values(md, 'dc.date.created'), submitted_dates=values(md, 'dc.date.submitted'),
                copyright_dates=values(md, 'dc.date.copyright'), other_dates=values(md, 'dc.date'),
                degree_year=None, degree_year_status='not established by this normalization',
                abstract=values(md, 'dc.description.abstract'), subjects=values(md, 'dc.subject', 'dc.subject.keywords'),
                advisors=values(md, 'dc.contributor.advisor', 'dc.contributor.supervisor'),
                committee=values(md, 'dc.contributor.committeeMember'),
                rights=values(md, 'dc.rights', 'dc.rights.uri'),
                embargo_metadata={k: values(md, k) for k in md if 'embargo' in k.lower()},
                item_url=f'{base}/items/{item["uuid"]}', handles=values(md, 'dc.identifier.uri'),
                fulltext_status='not individually checked', metadata=md)


def harvest(out):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'raw').mkdir()
    records, requests, streams, errors = [], [], [], []
    for name, base, scope, facet, term, description in STREAMS:
        collected, pages, first = [], 0, None
        try:
            for page in range(10):
                params = dict(scope=scope, size=100, page=page, sort='dc.title,ASC')
                if facet:
                    params[f'f.{facet}'] = f'{term},equals'
                url = f'{base}/server/api/discover/search/objects?{urlencode(params)}'
                with urlopen(Request(url, headers={'User-Agent': 'HistoriographyMetadataPilot/1.0 (public metadata research)'}), timeout=45) as response:
                    raw = response.read()
                    final_url = response.url
                path = out / 'raw' / f'{name}-{page:02}.json'
                path.write_bytes(raw)
                data = json.loads(raw)
                result = data['_embedded']['searchResult']
                first = first or data
                requests.append(dict(url=url, final_url=final_url, file=str(path.relative_to(out)),
                                     sha256=hashlib.sha256(raw).hexdigest(), checked_at=datetime.now(timezone.utc).isoformat()))
                objects = result.get('_embedded', {}).get('objects', [])
                items = [h['_embedded']['indexableObject'] for h in objects]
                assert all(i['type'] == 'item' for i in items), 'Unexpected non-item result'
                collected.extend(normalize(i, name, base) for i in items)
                pages += 1
                if page + 1 >= result['page']['totalPages']:
                    break
                time.sleep(.3)
            expected = first['_embedded']['searchResult']['page']['totalElements']
            assert len({r['id'] for r in collected}) == len(collected), 'Duplicate paging results'
            assert len(collected) == expected, f'Page cap or changing result set: {len(collected)} of {expected}'
            facet_counts = {f['name']: {v['label']: v['count'] for v in f.get('_embedded', {}).get('values', [])}
                            for f in first['_embedded'].get('facets', [])}
            streams.append(dict(stream=name, collection_url=f'{base}/collections/{scope}',
                                scope=description, complete_query=True, reported_total=expected,
                                harvested=len(collected), degree_counts=dict(Counter(r['degree_classification'] for r in collected)),
                                exact_history_metadata=sum(r['history_metadata_exact'] for r in collected),
                                abstracts=sum(bool(r['abstract']) for r in collected),
                                issued_years=sorted({d[:4] for r in collected for d in r['issued_dates'] if re.match(r'^\d{4}', d)}),
                                first_page_access_facets=facet_counts.get('access_status', {})))
            records.extend(collected)
            print(json.dumps(streams[-1]), flush=True)
        except Exception as exc:
            errors.append(dict(stream=name, error=str(exc), completed_pages=pages))
            print(json.dumps(errors[-1]), flush=True)
    # Retain all stream memberships while counting a thesis once per institution.
    unique = {}
    for row in records:
        key = (row['institution'], row['id'])
        if key not in unique:
            unique[key] = dict(row, streams=[row['stream']])
        elif row['stream'] not in unique[key]['streams']:
            unique[key]['streams'].append(row['stream'])
    rows = list(unique.values())
    with (out / 'records.jsonl').open('w') as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')
    fields = ['institution', 'id', 'title', 'authors', 'degree_classification', 'degree',
              'department_discipline', 'issued_dates', 'accession_dates', 'copyright_dates',
              'degree_year', 'degree_year_status', 'subjects', 'abstract', 'item_url', 'fulltext_status']
    with (out / 'records.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(r[k], ensure_ascii=False) if isinstance(r[k], list) else r[k] for k in fields} for r in rows)
    write_json(out / 'requests.json', requests)
    write_json(out / 'summary.json', dict(checked_at=datetime.now(timezone.utc).isoformat(),
               status='complete bounded metadata pilot' if not errors else 'partial pilot with errors',
               streams=streams, errors=errors, unique_records=len(rows),
               degree_counts=dict(Counter(r['degree_classification'] for r in rows)),
               qualifications=['Complete query results do not establish complete institutional degree coverage.',
                               'Issued, deposit, copyright and degree dates remain distinct.',
                               'Access facets describe the retrieved set; individual PDF access is untested.',
                               'No historiographical labels, author identities or influence edges are inferred.',
                               'Pre-mandate digitization is a selected subset, not a comparable graduation cohort.']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    harvest(parser.parse_args().out)
