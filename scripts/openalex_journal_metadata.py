#!/usr/bin/env python3
"""Prepare offline by default; retrieve source metadata only with --execute."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.error
import urllib.request

try:
    from .openalex_ingest import Client, load_api_key, write_json
except ImportError:
    from openalex_ingest import Client, load_api_key, write_json

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.json'
PLAN = ROOT / 'feedback/journals/openalex-metadata-plan.json'
STAGING = ROOT / 'data/journal-catalogue/openalex-metadata-staging'
FIELDS = ('id', 'display_name', 'issn_l', 'issn', 'alternate_titles',
          'host_organization', 'host_organization_name', 'country_code',
          'homepage_url', 'type', 'is_oa', 'is_in_doaj',
          'first_publication_year', 'last_publication_year', 'topics',
          'topic_share', 'updated_date')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def title_key(value):
    # Keep accents and all scripts; do not erase subtitles or merge Labor/Labour.
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value).casefold()).strip()


def prepare(catalogue_path=CATALOGUE):
    raw = catalogue_path.read_bytes()
    catalogue = json.loads(raw)
    periodicals = [n for n in catalogue['nodes'] if n['entry_kind'] == 'periodical']
    periodicals.sort(key=lambda n: (n.get('publication_role') != 'research_journal',
                                   not bool(n.get('issns')), n['label'].casefold(), n['id']))
    queue = []
    for n in periodicals:
        params = {'per_page': 25, 'select': ','.join(FIELDS)}
        if n.get('issns'):
            params['filter'] = 'issn:' + '|'.join(n['issns'])
        else:
            params['search'] = n['label']
        queue.append({'journal_id': n['id'], 'label': n['label'],
                      'aliases': n.get('aliases', []), 'issns': n.get('issns', []),
                      'identity_status': n.get('identity_status'),
                      'publication_role': n.get('publication_role'),
                      'endpoint': 'sources', 'params': params})
    return {'schema_version': '1.0', 'status': 'prepared_waiting_for_user_start',
            'catalogue_sha256': digest(raw), 'candidate_count': len(queue),
            'candidates_with_issn': sum(bool(q['issns']) for q in queue),
            'initial_batch_size': 24, 'default_request_limit': 30,
            'scope': 'Source metadata only; no works, citations, graph merges or venue edges.',
            'date_policy': 'Indexed publication years are observations, never automatic founding or cessation dates.',
            'subject_policy': 'OpenAlex topics remain attributed inferred metadata, not checked publisher remit.',
            'queue': queue}


def assess(entry, page):
    rows = page['results']
    total = page.get('meta', {}).get('count')
    truncated = total is None or total > len(rows)
    wanted = set(entry['issns'])
    names = {title_key(t) for t in [entry['label'], *entry['aliases']]}
    matches = []
    for row in rows:
        issns = set(row.get('issn') or []) | {row.get('issn_l')}
        titles = [row.get('display_name') or '', *(row.get('alternate_titles') or [])]
        matches_identity = bool(wanted & issns) if wanted else any(title_key(t) in names for t in titles)
        if matches_identity:
            matches.append(row)
    status = 'needs_identity_review'
    if not rows:
        status = 'no_result'
    elif (wanted and len(matches) == 1 and not truncated
          and entry.get('identity_status') != 'ambiguous_title'
          and matches[0].get('type') == 'journal'):
        status = 'unique_issn_candidate'
    elif len(matches) == 1 and not wanted:
        status = 'title_candidate_needs_review'
    return {'status': status, 'candidate_source_ids': [r['id'] for r in matches],
            'truncated': truncated, 'accepted': False,
            'note': 'No automatic identity merge, date import, subject promotion or venue claim.'}


def retrieve(plan, client, output=STAGING, limit=24):
    completed = 0
    for entry in plan['queue']:
        if completed >= limit:
            break
        path = output / (entry['journal_id'] + '.json')
        if path.exists():
            previous = json.loads(path.read_text())
            if previous['catalogue_sha256'] != plan['catalogue_sha256']:
                raise ValueError('Staging belongs to another catalogue; review before resuming.')
            if previous.get('retrieval_status') == 'retrieved':
                continue
        record = {'catalogue_sha256': plan['catalogue_sha256'], 'candidate': entry}
        try:
            page = client.get(entry['params'], endpoint='sources')
        except RuntimeError as error:
            # Retain only allowlisted diagnostics, never response bodies or arbitrary text.
            message = str(error)
            http = re.fullmatch(r'OpenAlex returned HTTP (\d{3}); response body omitted\.', message)
            failure = ('http_' + http.group(1)) if http else (
                'request_budget' if message.startswith('Request budget reached;') else 'network_or_unknown')
            record.update(retrieval_status='interrupted',
                          failure_kind=failure,
                          note='Request failed or budget exhausted. Cached responses remain resumable.')
            write_json(path, record)
            return {'completed_this_run': completed, 'status': 'interrupted', 'failure_kind': failure,
                    'network_requests': client.requests, 'cache_hits': client.cache_hits}
        record.update(retrieval_status='retrieved', response=page, assessment=assess(entry, page))
        write_json(path, record)
        completed += 1
    return {'completed_this_run': completed, 'status': 'batch_finished',
            'network_requests': client.requests, 'cache_hits': client.cache_hits}


def check_usage():
    """Read quota numbers only; never emit identity, credentials or arbitrary messages."""
    key = load_api_key()
    headers = {'Authorization': 'Bearer ' + key} if key else {}
    request = urllib.request.Request('https://api.openalex.org/rate-limit', headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            payload = json.load(response)
            rate_headers = {k: response.headers.get(k) for k in (
                'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset')}
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        return {'status': 'http_' + str(status)}
    except (urllib.error.URLError, TimeoutError):
        return {'status': 'network_error'}
    def numbers_only(value):
        if not isinstance(value, dict):
            return None
        result = {}
        for k, v in value.items():
            if any(word in k.lower() for word in ('key', 'token', 'email', 'user', 'account')):
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                result[k] = v
            elif isinstance(v, dict):
                child = numbers_only(v)
                if child:
                    result[k] = child
        return result
    return {'status': 'checked', 'credential_present': bool(key),
            'numeric_usage': numbers_only(payload),
            'rate_headers': {k: int(v) for k, v in rate_headers.items() if v and v.isdigit()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true',
                        help='Network access: use only after the user explicitly says to start.')
    parser.add_argument('--limit', type=int, default=24)
    parser.add_argument('--max-requests', type=int, default=30)
    parser.add_argument('--check-usage', action='store_true',
                        help='Read the API usage endpoint; requires --execute.')
    args = parser.parse_args(argv)
    if args.limit < 1 or args.max_requests < 1:
        parser.error('Limits must be positive.')
    if args.check_usage:
        if not args.execute:
            parser.error('--check-usage requires --execute for network access.')
        result = check_usage()
        write_json(ROOT / 'feedback/journals/openalex-usage.json', result)
        print(json.dumps(result))
        return
    if not args.execute:
        plan = prepare()
        write_json(PLAN, plan)
        print(f"Prepared {plan['candidate_count']} candidates; {plan['candidates_with_issn']} with ISSNs. No network or credential access.")
        return
    plan = json.loads(PLAN.read_text())
    if plan['catalogue_sha256'] != digest(CATALOGUE.read_bytes()):
        raise ValueError('Catalogue changed since preparation; regenerate and review the plan.')
    client = Client(load_api_key(), ROOT / '.cache/openalex-journal-metadata',
                    max_requests=args.max_requests)
    result = retrieve(plan, client, limit=args.limit)
    write_json(STAGING / 'last-run.json', result)
    print(json.dumps(result))
    if result['status'] == 'interrupted':
        sys.exit(1)


if __name__ == '__main__':
    main()
