#!/usr/bin/env python3
"""Stage LOC/Harvard serial metadata and triangulation reports; offline by default."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
from xml.etree.ElementTree import ParseError, fromstring

try:
    from .library_journal_records import assess, compare, issn, parse_page
except ImportError:
    from library_journal_records import assess, compare, issn, parse_page

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.json'
OA = ROOT / 'data/journal-catalogue/openalex-metadata-staging'
BASE = ROOT / 'data/journal-catalogue/library-metadata'
ENDPOINTS = {'loc': 'https://lx2.loc.gov/sru/lcdb',
             'harvard': 'https://api.lib.harvard.edu/v2/items'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    tmp.replace(path)


def prepare():
    raw = CATALOGUE.read_bytes()
    queue = []
    for node in json.loads(raw)['nodes']:
        if node['entry_kind'] != 'periodical':
            continue
        path = OA / (node['id']+'.json')
        candidates, provenance = [], None
        if path.exists():
            staged_raw = path.read_bytes()
            staged = json.loads(staged_raw)
            if staged.get('catalogue_sha256') == sha(raw) and staged.get('retrieval_status') == 'retrieved':
                ids = staged['assessment']['candidate_source_ids']
                # A single proposed source is a search aid, not an accepted identity.
                if len(ids) == 1 and not staged['assessment']['truncated']:
                    candidates = [r for r in staged['response']['results'] if r['id'] in ids]
                provenance = {'path': str(path.relative_to(ROOT)), 'sha256': sha(staged_raw)}
        hints = sorted({n for s in candidates for v in (s.get('issn') or []) if (n := issn(v))})
        queue.append({'node': node, 'hint_issns': hints, 'openalex_candidates': candidates,
                      'openalex_snapshot': provenance})
    queue.sort(key=lambda q: (q['node']['publication_role'] != 'research_journal', q['node']['label'].casefold()))
    return {'schema_version': '1.0', 'prepared_at': datetime.now(timezone.utc).isoformat(),
            'catalogue_sha256': sha(raw), 'candidate_count': len(queue), 'queue': queue,
            'date_policy': 'Preserve better dates; OpenAlex may supply an attributed indexed-range fallback only.',
            'integration_policy': 'No graph edits, auto-merges, subject promotions or numeric confidence scores.'}


class FetchError(RuntimeError):
    pass


class Client:
    def __init__(self, cache, max_requests=60):
        self.cache = cache
        self.max_requests = max_requests
        self.requests = 0
        self.cache_hits = 0
        self.last = {}

    def get(self, provider, params):
        url = ENDPOINTS[provider]+'?'+urllib.parse.urlencode(sorted(params.items()))
        key = sha(url.encode())
        raw_path, meta_path = self.cache/(key+'.xml'), self.cache/(key+'.json')
        if raw_path.exists() and meta_path.exists():
            raw, meta = raw_path.read_bytes(), read(meta_path)
            if sha(raw) != meta['sha256'] or meta['url'] != url:
                raise FetchError('cache_integrity_error')
            self.cache_hits += 1
            return raw, meta
        for attempt in range(3):
            if self.requests >= self.max_requests:
                raise FetchError('request_budget')
            # Harvard asks for at most one request/second; apply that to both providers.
            delay = 1.1 - (time.monotonic()-self.last.get(provider, 0))
            if delay > 0:
                time.sleep(delay)
            self.last[provider] = time.monotonic()
            self.requests += 1
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'HistoriographySerialMetadata/1.0',
                                                               'Accept': 'application/xml'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read()
            except urllib.error.HTTPError as error:
                code = error.code
                retry = error.headers.get('Retry-After', '')
                error.close()
                if code == 429:
                    if retry and not retry.isdigit():
                        try:
                            retry = str(max(0, int((parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())+1))
                        except (TypeError, ValueError, OverflowError):
                            retry = ''
                    raise FetchError('http_429_retry_after_'+(retry if retry.isdigit() else 'unspecified')) from None
                if code not in (500, 502, 503, 504) or attempt == 2:
                    raise FetchError('http_'+str(code)) from None
                time.sleep(2**attempt)
                continue
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise FetchError('network_error') from None
                time.sleep(2**attempt)
                continue
            meta = {'provider': provider, 'url': url, 'params': params,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(), 'sha256': sha(raw),
                    'raw_file': str(raw_path.relative_to(ROOT)) if raw_path.is_relative_to(ROOT) else str(raw_path)}
            self.cache.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(raw)
            write(meta_path, meta)
            return raw, meta


def queries(entry, provider):
    node = entry['node']
    identifiers = sorted({n for v in node.get('issns', []) if (n := issn(v))})
    identifiers += [n for n in entry['hint_issns'] if n not in identifiers]
    terms = [('issn', n) for n in identifiers]
    terms += [('title', t) for t in dict.fromkeys([node['label'], *node.get('aliases', [])])][:3]
    for kind, value in terms:
        quoted = '"'+value.replace('\\', '\\\\').replace('"', '\\"')+'"'
        if provider == 'loc':
            params = {'version': '1.1', 'operation': 'searchRetrieve', 'recordSchema': 'marcxml',
                      'query': ('bath.issn = ' if kind == 'issn' else 'dc.title = ')+quoted}
        else:
            # Quoting avoids tokenized partial-ISSN matches. Title fallback remains necessary.
            # LibraryCloud still interprets unescaped colons inside quoted titles.
            quoted = quoted.replace(':', '\\:')
            params = {'identifier' if kind == 'issn' else 'title': quoted, 'issuance': 'serial'}
        yield {'kind': kind, 'value': value, 'params': params}


def fetch_provider(entry, provider, client, page_size=25, max_pages=2):
    records, attempts = {}, []
    query_errors = []
    truncated = False
    for query in queries(entry, provider):
        retrieved = 0
        for page in range(max_pages):
            params = dict(query['params'])
            params.update({'maximumRecords': page_size, 'startRecord': page*page_size+1}
                          if provider == 'loc' else {'limit': page_size, 'start': page*page_size})
            raw, provenance = client.get(provider, params)
            try:
                parsed = parse_page(raw, provider)
            except (ValueError, ParseError) as error:
                # LC sometimes finds a hit set but cannot retrieve a MARC record.
                # Preserve this query failure and try remaining identifiers/titles.
                if provider == 'loc' and not isinstance(error, ParseError):
                    diagnostic = fromstring(raw).find('.//{http://www.loc.gov/zing/srw/diagnostic/}diagnostic')
                    if diagnostic is not None:
                        values = {e.tag.rsplit('}', 1)[-1]: e.text for e in diagnostic}
                        if values.get('uri') == 'info:srw/diagnostic/1/1' and 'missing MARC record' in (values.get('details') or ''):
                            query_errors.append({'kind': query['kind'], 'value': query['value'],
                                                 'page': page+1, 'diagnostic': values,
                                                 'provenance': provenance})
                            break
                # Do not confuse diagnostics/HTML/invalid XML with a zero-result query.
                raise FetchError('invalid_catalogue_response') from error
            retrieved += len(parsed['records'])
            attempts.append({'kind': query['kind'], 'value': query['value'], 'page': page+1,
                             'total_reported': parsed['total'], 'returned': len(parsed['records']),
                             'provenance': provenance})
            for record in parsed['records']:
                record_id = [i for i in record['record_identifiers'] if i['value']] or [
                    i for i in record['identifiers'] if i['value']]
                key = provider+':'+sha(json.dumps(record_id or record, sort_keys=True).encode())[:24]
                if key not in records:
                    record.update(record_key=key, identity=assess(entry['node'], record, entry['hint_issns']),
                                  retrieved_via=[])
                    records[key] = record
                records[key]['retrieved_via'].append(provenance['sha256'])
            if retrieved >= parsed['total']:
                break
            if not parsed['records'] or page == max_pages-1:
                truncated = True
                break
        # Once an exact ISSN has located serial record(s), avoid adding unrelated title hits.
        if any(r['identity']['status'] in ('catalogue_issn_match', 'openalex_identifier_hint_match') for r in records.values()):
            break
    return {'status': 'retrieved_with_query_errors' if query_errors else 'retrieved',
            'provider': provider, 'attempts': attempts, 'query_errors': query_errors,
            'truncated': truncated, 'records': list(records.values())}


def report(plan, output):
    summaries, states = [], Counter()
    nodes = {n['id']: n for n in read(CATALOGUE)['nodes']}
    classifications = read(CATALOGUE)['subject_classifications']
    for entry in plan['queue']:
        jid = entry['node']['id']
        records, statuses = [], {}
        for provider in ENDPOINTS:
            path = output/'records'/provider/(jid+'.json')
            if not path.exists():
                continue
            result = read(path)
            if result['catalogue_sha256'] != plan['catalogue_sha256'] or result['plan_fingerprint'] != fingerprint(entry):
                raise ValueError('Staging snapshot mismatch')
            statuses[provider] = result['status']
            states[provider+':'+result['status']] += 1
            records.extend(result.get('records', []))
        if statuses:
            summaries.append({'journal_id': jid, 'title': nodes[jid]['label'], 'providers': statuses,
                              'existing_classifications': [r for r in classifications if r['journal_id'] == jid],
                              'comparison': compare(nodes[jid], records, entry['openalex_candidates'])})
    result = {'catalogue_sha256': plan['catalogue_sha256'], 'created_at': datetime.now(timezone.utc).isoformat(),
              'planned_candidates': len(plan['queue']), 'candidates_with_attempts': len(summaries),
              'provider_status_counts': dict(states), 'journals': summaries,
              'note': 'Missing providers and unresolved identities are not negative evidence. No automatic graph changes.'}
    write(output/'triangulation.json', result)
    lines = ['# Journal metadata triangulation', '', '| Journal | LOC | Harvard | Curated start | Library date comparisons |',
             '| --- | --- | --- | --- | --- |']
    for row in summaries:
        comp = row['comparison']
        comparisons = '; '.join(f"{o['provider']} {o['point']} {o['year']}: {o['comparison_with_curated']} ({o['identity_status']})"
                                for o in comp['date_observations']) or 'No matched date observations'
        lines.append('| '+' | '.join(str(v).replace('|', '\\|').replace('\n', ' ') for v in (
            row['title'], row['providers'].get('loc', 'not queried'), row['providers'].get('harvard', 'not queried'),
            comp['existing_start'] if comp['existing_start'] is not None else 'unknown', comparisons))+' |')
    lines += ['', 'Consult triangulation.json and raw responses for identifiers, subjects, title succession, shared cataloguing provenance and evidence limits. No dates or subjects are automatically imported.']
    (output/'triangulation.md').write_text('\n'.join(lines)+'\n')
    return result


def fingerprint(entry):
    return sha(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode())


def run(plan, client, output, journal_ids=(), limit=5, providers=tuple(ENDPOINTS), max_pages=2, reprocess=False):
    selected = [e for e in plan['queue'] if not journal_ids or e['node']['id'] in journal_ids]
    if journal_ids and set(journal_ids) - {e['node']['id'] for e in selected}:
        raise ValueError('Unknown journal ID')
    completed = 0
    for entry in selected:
        if completed >= limit:
            break
        worked = False
        for provider in providers:
            path = output/'records'/provider/(entry['node']['id']+'.json')
            if reprocess and not path.exists():
                continue
            if path.exists():
                previous = read(path)
                if previous['catalogue_sha256'] != plan['catalogue_sha256'] or previous['plan_fingerprint'] != fingerprint(entry):
                    raise ValueError('Staging belongs to another plan; use a new output directory')
                if previous['status'] in ('retrieved', 'retrieved_with_query_errors') and not reprocess:
                    continue
            worked = True
            result = {'journal_id': entry['node']['id'], 'catalogue_sha256': plan['catalogue_sha256'],
                      'plan_fingerprint': fingerprint(entry)}
            try:
                result.update(fetch_provider(entry, provider, client, max_pages=max_pages))
            except FetchError as error:
                result.update(status='interrupted', failure_kind=str(error), provider=provider)
                # A missing offline cache page must not replace previously normalized data.
                if reprocess:
                    write(output/'reprocess-interrupted.json', result)
                else:
                    write(path, result)
                return {'status': 'interrupted', 'failure_kind': str(error), 'completed_candidates': completed,
                        'network_requests': client.requests, 'cache_hits': client.cache_hits}
            write(path, result)
        completed += int(worked)
    return {'status': 'batch_finished', 'completed_candidates': completed,
            'network_requests': client.requests, 'cache_hits': client.cache_hits}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--report-only', action='store_true')
    p.add_argument('--reprocess', action='store_true', help='Reparse saved queries from cache; network is disabled.')
    p.add_argument('--output', type=Path, default=BASE)
    p.add_argument('--journal-id', action='append', default=[])
    p.add_argument('--limit', type=int, default=5)
    p.add_argument('--max-requests', type=int, default=60)
    p.add_argument('--max-pages', type=int, default=2)
    p.add_argument('--provider', choices=['both', 'loc', 'harvard'], default='both')
    args = p.parse_args(argv)
    if min(args.limit, args.max_requests, args.max_pages) < 1:
        p.error('Limits must be positive')
    if args.reprocess and args.execute:
        p.error('--reprocess is offline; do not combine it with --execute')
    output = args.output.resolve()
    if output.is_relative_to(ROOT/'site') or output.is_relative_to(ROOT/'prototype'):
        p.error('Research output must not be placed in browser assets')
    path = output/'plan.json'
    if not path.exists():
        write(path, prepare())
    plan = read(path)
    if plan['catalogue_sha256'] != sha(CATALOGUE.read_bytes()):
        p.error('Catalogue changed; preserve this run and prepare a new output directory')
    if args.report_only:
        print(json.dumps(report(plan, output)['provider_status_counts']))
        return
    if not args.execute and not args.reprocess:
        print(f"Prepared {plan['candidate_count']} candidates offline. No network or credential access.")
        return
    providers = tuple(ENDPOINTS) if args.provider == 'both' else (args.provider,)
    client = Client(output/'raw', 0 if args.reprocess else args.max_requests)
    result = run(plan, client, output, args.journal_id, args.limit, providers, args.max_pages, args.reprocess)
    write(output/'last-run.json', result)
    report(plan, output)
    print(json.dumps(result))
    if result['status'] == 'interrupted':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
