#!/usr/bin/env python3
"""Additional public thesis metadata, with bilingual and joint-department limits.

Preserves the first five-university pilot. Does not download thesis bodies or use
subscription credentials. All selected metadata remains separate from the atlas.
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
import unicodedata
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from harvest_canadian_history_dissertations import normalize, values, write_json

ROOT = Path(__file__).resolve().parents[1]
DEGREE_KEYS = ['dc.degree.name', 'dc.description.degree', 'thesis.degree.name',
               'uws-etd.degree', 'etdms.degree.name', 'etd.degree.name']
LEVEL_KEYS = ['dc.degree.level', 'thesis.degree.level', 'etd.degree.level']
PROGRAM_KEYS = ['dc.degree.discipline', 'dc.contributor.department', 'thesis.degree.department',
                'thesis.degree.discipline', 'dc.degree.department', 'dc.degree.programme',
                'uws-etd.degree.department', 'uws-etd.degree.discipline', 'mcgill.department',
                'uottawa.department', 'dc.faculty.department', 'ual.department',
                'etdms.degree.discipline', 'etd.degree.discipline', 'dc.subject.discipline']
EXACT_HISTORY = {'history', 'histoire', 'histoire / history', 'history / histoire',
                 'department of history', 'maitrise en histoire', 'doctorat en histoire'}
COMBINED_DEPARTMENTS = {'department of history and classical studies',
    'department of history and classics', 'department of history, classics, and religion',
    'history and classics', 'history, classics, and religion'}


def folded(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c)).strip()


def expand_normalization(item, stream, base):
    r = normalize(item, stream, base)
    md = item['metadata']
    r['degree'] = list(dict.fromkeys(values(md, *DEGREE_KEYS)))
    r['degree_level'] = list(dict.fromkeys(values(md, *LEVEL_KEYS)))
    text = folded(' '.join(r['degree'] + r['degree_level']))
    doctoral = bool(re.search(r'\bdoctoral\b|\bdoctorat\b|\bdoctorate\b|\bdoctor of philosophy\b|\bph\s*\.?\s*d\b', text))
    masters = bool(re.search(r'\bmaster|\bmaitrise\b|\bma\b|\bm\.?\s*a\b', text))
    r['degree_classification'] = 'conflicting_degree' if doctoral and masters else 'doctoral' if doctoral else 'masters' if masters else 'unspecified'
    r['department_discipline'] = list(dict.fromkeys(values(md, *PROGRAM_KEYS)))
    names = {folded(v) for v in r['department_discipline']}
    r['history_metadata_exact'] = bool(names & EXACT_HISTORY)
    r['history_scope'] = ('explicit_history_program_or_department' if r['history_metadata_exact'] else
                          'combined_department_requires_program_review' if names & COMBINED_DEPARTMENTS else
                          'collection_only_requires_program_review')
    r['language'] = values(md, 'dc.language.iso', 'dc.language', 'dcterms.language')
    r['subjects'] = values(md, 'dc.subject', 'dc.subject.keywords', 'dc.subject.rvm', 'dc.subject.classification')
    r['abstract'] = values(md, 'dc.description.abstract', 'bul.abstract.anglais')
    r['rights'] = values(md, 'dc.rights', 'dc.rights.uri', 'dc.rights.license', 'oaire.license.condition')
    r['graduation_dates'] = values(md, 'ual.date.graduation', 'dc.date.convocation')
    return r


def fetch(url, out, name, logs):
    with urlopen(Request(url, headers={'User-Agent': 'HistoriographyMetadataPilot/1.0 (public metadata research)'}), timeout=45) as response:
        body = response.read()
        final = response.url
    path = out / 'raw' / name
    path.write_bytes(body)
    logs.append(dict(url=url, final_url=final, file=str(path.relative_to(out)),
                     sha256=hashlib.sha256(body).hexdigest(), checked_at=datetime.now(timezone.utc).isoformat()))
    return body


def dspace(stream, out, logs):
    rows, first, expected = [], None, None
    for page in range(15):
        params = dict(scope=stream['collection'], size=100, page=page, sort='dc.title,ASC')
        if stream.get('omit_sort'):
            params.pop('sort')
        if stream.get('query'):
            params['query'] = stream['query']
        for key, value in stream.get('filters', {}).items():
            params[f'f.{key}'] = value
        url = stream['api_base'] + '/server/api/discover/search/objects?' + urlencode(params, quote_via=quote)
        data = json.loads(fetch(url, out, f'{stream["id"]}-{page:02}.json', logs))
        result = data['_embedded']['searchResult']
        first = first or data
        total = result['page']['totalElements']
        expected = total if expected is None else expected
        assert total == expected, 'Changing pagination total'
        if expected > 1500:
            raise ValueError(f'Query exceeds bounded 1500-record limit: {expected}')
        for hit in result.get('_embedded', {}).get('objects', []):
            item = hit['_embedded']['indexableObject']
            assert item['type'] == 'item'
            rows.append(expand_normalization(item, stream['institution'], stream['item_base']))
        if page + 1 >= result['page']['totalPages']:
            break
        time.sleep(.2)
    assert len(rows) == expected
    assert len({r['id'] for r in rows}) == len(rows)
    facets = {f['name']: {v['label']: v['count'] for v in f.get('_embedded', {}).get('values', [])}
              for f in first['_embedded'].get('facets', [])}
    return rows, dict(reported_total=expected, complete_query=True, access_facets=facets.get('access_status', {}))


def laurier(out, logs):
    ns = {'o': 'http://www.openarchives.org/OAI/2.0/', 'd': 'http://purl.org/dc/elements/1.1/'}
    params = dict(verb='ListRecords', metadataPrefix='qualified-dublin-core', set='publication:hist_etd')
    rows, deleted = [], []
    for page in range(15):
        url = 'https://scholars.wlu.ca/do/oai/?' + urlencode(params)
        tree = ET.fromstring(fetch(url, out, f'laurier-{page:02}.xml', logs))
        error = tree.find('o:error', ns)
        assert error is None, ET.tostring(error, encoding='unicode') if error is not None else ''
        for record in tree.findall('.//o:record', ns):
            header = record.find('o:header', ns)
            rid = header.findtext('o:identifier', namespaces=ns)
            if header.get('status') == 'deleted':
                deleted.append(rid)
                continue
            payload = record.find('o:metadata', ns)
            raw = {}
            for element in payload.iter():
                if element.tag.startswith('{http://purl.org/dc/elements/1.1/}'):
                    name = element.tag.split('}')[1]
                    raw.setdefault(name, []).append(element.text or '')
            mapping = {'title': 'dc.title', 'creator': 'dc.creator', 'name': 'thesis.degree.name',
                       'discipline': 'thesis.degree.discipline', 'date': 'dc.date.issued',
                       'date.available': 'dc.date.available', 'subject': 'dc.subject',
                       'description': 'dc.description.abstract', 'rights': 'dc.rights',
                       'identifier': 'dc.identifier.uri', 'language': 'dc.language.iso'}
            md = {target: [dict(value=v) for v in raw[source]] for source, target in mapping.items() if source in raw}
            md['oai.datestamp'] = [dict(value=header.findtext('o:datestamp', namespaces=ns))]
            item = dict(uuid=rid, metadata=md)
            r = expand_normalization(item, 'laurier', 'https://scholars.wlu.ca')
            r['item_url'] = next((u for u in raw.get('identifier', []) if '/etd/' in u), None)
            r['raw_oai_fields'] = raw
            r['oai_sets'] = [s.text for s in header.findall('o:setSpec', ns)]
            # Supervisors remain role-qualified; generic contributors are not converted.
            r['advisors'] = []
            r['oai_contributors'] = raw.get('contributor', [])
            r['oai_contributor_roles'] = raw.get('contributor.role', [])
            r['date_warning'] = '1900-01-01 availability values are placeholders, not completion dates.'
            rows.append(r)
        token = tree.find('.//o:resumptionToken', ns)
        if token is None or not token.text:
            break
        params = dict(verb='ListRecords', resumptionToken=token.text)
    else:
        raise ValueError('OAI page cap reached')
    assert len({r['id'] for r in rows}) == len(rows)
    return rows, dict(complete_query=True, active_records=len(rows), deleted_records=deleted,
                      scope='OAI History Theses and Dissertations set; all active returned records')


def main(config, out):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'raw').mkdir()
    setup = json.loads(config.read_text())
    all_rows, logs, summaries, errors = [], [], [], []
    for stream in setup['dspace_streams']:
        try:
            rows, info = dspace(stream, out, logs)
            all_rows.extend(dict(r, stream_id=stream['id']) for r in rows)
            summaries.append(dict(**stream, **info, degree_counts=dict(Counter(r['degree_classification'] for r in rows)),
                                   doctoral_scope_counts=dict(Counter(r['history_scope'] for r in rows if r['degree_classification'] == 'doctoral'))))
            print(json.dumps(summaries[-1], ensure_ascii=False), flush=True)
        except Exception as exc:
            errors.append(dict(stream=stream['id'], error=str(exc)))
            print(json.dumps(errors[-1]), flush=True)
    try:
        if setup.get('skip_laurier'):
            raise StopIteration
        rows, info = laurier(out, logs)
        all_rows.extend(dict(r, stream_id='laurier-oai') for r in rows)
        summaries.append(dict(id='laurier-oai', institution='laurier', **info,
            degree_counts=dict(Counter(r['degree_classification'] for r in rows)),
            doctoral_scope_counts=dict(Counter(r['history_scope'] for r in rows if r['degree_classification'] == 'doctoral'))))
        print(json.dumps(summaries[-1]), flush=True)
    except StopIteration:
        pass
    except Exception as exc:
        errors.append(dict(stream='laurier-oai', error=str(exc)))
    unique = {}
    for row in all_rows:
        key = (row['institution'], row['id'])
        if key not in unique:
            unique[key] = dict(row, streams=[row['stream_id']])
        else:
            prior = unique[key]
            assert prior['metadata'] == row['metadata'], 'Conflicting metadata in overlapping streams'
            if row['stream_id'] not in prior['streams']:
                prior['streams'].append(row['stream_id'])
    rows = list(unique.values())
    with (out / 'records.jsonl').open('w') as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')
    fields = ['institution', 'id', 'title', 'degree_classification', 'degree', 'department_discipline',
              'history_scope', 'issued_dates', 'accession_dates', 'graduation_dates', 'item_url']
    with (out / 'records.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(r[k], ensure_ascii=False) if isinstance(r[k], list) else r[k] for k in fields} for r in rows)
    write_json(out / 'requests.json', logs)
    write_json(out / 'summary.json', dict(checked_at=datetime.now(timezone.utc).isoformat(),
        streams=summaries, errors=errors, retrieval_limits=setup['retrieval_limits'],
        unique_records=len(rows), degree_counts=dict(Counter(r['degree_classification'] for r in rows)),
        doctoral_scope_counts=dict(Counter(r['history_scope'] for r in rows if r['degree_classification'] == 'doctoral')),
        qualifications=['Complete scoped queries do not establish complete institutional graduation coverage.',
                        'Combined departmental affiliation is not an item-level History programme determination.',
                        'Literal phrases are discovery queries; exact local programme checks control eligibility.',
                        'No thesis PDF, full-text body, identity assertion or influence relationship downloaded or inferred.']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.config, args.out)
