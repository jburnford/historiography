#!/usr/bin/env python3
"""Resume the entire frozen library plan, with durable progress and exception queues."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from . import library_journal_metadata as lib
except ImportError:
    import library_journal_metadata as lib

DONE = {'retrieved', 'retrieved_with_query_errors'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def retryable(kind):
    return kind == 'network_error' or kind.startswith(('http_429_', 'http_500', 'http_502', 'http_503', 'http_504'))


def cooldown(kind):
    if kind.startswith('http_429_'):
        value = kind.rsplit('_', 1)[-1]
        return max(300, int(value)) if value.isdigit() else 300
    return 60


def pending(plan, output, retry_pass):
    jobs = []
    for entry in plan['queue']:
        for provider in lib.ENDPOINTS:
            path = output/'records'/provider/(entry['node']['id']+'.json')
            if path.exists():
                previous = lib.read(path)
                if previous['catalogue_sha256'] != plan['catalogue_sha256'] or previous['plan_fingerprint'] != lib.fingerprint(entry):
                    raise ValueError('Staging snapshot mismatch')
                if previous['status'] in DONE:
                    continue
                if previous['status'] == 'failed' and (not retryable(previous['failure_kind']) or retry_pass == 0):
                    continue
            elif retry_pass:
                continue
            jobs.append((entry, provider, path))
    return jobs


def progress(plan, output, client, status, **extra):
    counts, both, attempted = Counter(), 0, 0
    if not hasattr(client, 'worker_states'):
        client.worker_states = {}
    for entry in plan['queue']:
        states = []
        for provider in lib.ENDPOINTS:
            path = output/'records'/provider/(entry['node']['id']+'.json')
            if str(path) not in client.worker_states:
                client.worker_states[str(path)] = lib.read(path)['status'] if path.exists() else 'pending'
            state = client.worker_states[str(path)]
            counts[provider+':'+state] += 1
            states.append(state)
        both += all(s in DONE for s in states)
        attempted += all(s in DONE or s == 'failed' for s in states)
    result = {'status': status, 'updated_at': utc(), 'pid': os.getpid(),
              'planned_candidates': len(plan['queue']), 'both_provider_lookups_completed': both,
              'both_providers_attempted': attempted, 'provider_status_counts': dict(counts),
              'process_network_requests': client.requests, 'process_cache_hits': client.cache_hits, **extra}
    lib.write(output/'worker-state.json', result)
    return result


def work(plan, output, client, max_pages=2, retry_passes=2):
    if lib.sha(lib.CATALOGUE.read_bytes()) != plan['catalogue_sha256']:
        raise ValueError('Catalogue changed; preserve staging and use a new plan')
    progress(plan, output, client, 'running')
    count = 0
    consecutive_failures = Counter()
    for retry_pass in range(retry_passes+1):
        for entry, provider, path in pending(plan, output, retry_pass):
            if lib.sha(lib.CATALOGUE.read_bytes()) != plan['catalogue_sha256']:
                raise ValueError('Catalogue changed during retrieval')
            base = {'journal_id': entry['node']['id'], 'provider': provider,
                    'catalogue_sha256': plan['catalogue_sha256'], 'plan_fingerprint': lib.fingerprint(entry)}
            progress(plan, output, client, 'running', current_journal=entry['node']['label'],
                     current_provider=provider, retry_pass=retry_pass)
            try:
                result = {**base, **lib.fetch_provider(entry, provider, client, max_pages=max_pages)}
            except lib.FetchError as error:
                kind = str(error)
                if kind in ('cache_integrity_error', 'request_budget'):
                    raise
                # Failed queries are exceptions, not empty catalogue results.
                result = {**base, 'status': 'failed', 'failure_kind': kind, 'failed_at': utc()}
            lib.write(path, result)
            client.worker_states[str(path)] = result['status']
            with (output/'worker-events.jsonl').open('a') as events:
                events.write(json.dumps({'at': utc(), 'journal_id': base['journal_id'],
                    'provider': provider, 'status': result['status'], 'retry_pass': retry_pass,
                    'failure_kind': result.get('failure_kind'), 'network_requests': client.requests})+'\n')
            count += 1
            if count % 50 == 0:
                lib.report(plan, output)
            state = progress(plan, output, client, 'running', retry_pass=retry_pass)
            if result['status'] == 'failed' and retryable(result['failure_kind']):
                consecutive_failures[provider] += 1
                if consecutive_failures[provider] >= 5:
                    lib.report(plan, output)
                    raise lib.FetchError(provider+'_unavailable_after_5_consecutive_failures; resume after service recovery')
                remaining = cooldown(result['failure_kind'])
                while remaining > 0:
                    progress(plan, output, client, 'cooldown', seconds_remaining=remaining,
                             provider=provider, reason=result['failure_kind'])
                    delay = min(60, remaining)
                    time.sleep(delay)
                    remaining -= delay
            else:
                consecutive_failures[provider] = 0
    lib.report(plan, output)
    # Validate all cached evidence and original catalogue before declaring the pass finished.
    for meta_path in (output/'raw').glob('*.json'):
        meta = lib.read(meta_path)
        if lib.sha(meta_path.with_suffix('.xml').read_bytes()) != meta['sha256']:
            raise ValueError('Raw evidence hash mismatch')
    if lib.sha(lib.CATALOGUE.read_bytes()) != plan['catalogue_sha256']:
        raise ValueError('Catalogue changed during retrieval')
    exceptions = []
    for path in (output/'records').glob('*/*.json'):
        result = lib.read(path)
        if result['status'] not in DONE or result.get('query_errors') or result.get('truncated'):
            exceptions.append({'journal_id': result['journal_id'], 'provider': result['provider'],
                               'status': result['status'], 'failure_kind': result.get('failure_kind'),
                               'truncated': result.get('truncated', False),
                               'query_errors': result.get('query_errors', [])})
    lib.write(output/'worker-exceptions.json', exceptions)
    return progress(plan, output, client, 'finished_with_exceptions' if exceptions else 'finished',
                    exception_lookups=len(exceptions), raw_hashes_verified=True,
                    catalogue_sha256_unchanged=plan['catalogue_sha256'], automatic_imports=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--output', type=Path, default=lib.BASE)
    parser.add_argument('--max-requests', type=int, default=30000)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(lib.ROOT/'site') or output.is_relative_to(lib.ROOT/'prototype'):
        parser.error('Research output must not be in browser assets')
    if args.max_requests < 1:
        parser.error('Request budget must be positive')
    plan = lib.read(output/'plan.json')
    if not args.execute:
        print(json.dumps({'planned_candidates': len(plan['queue']), 'pending_lookups': len(pending(plan, output, 0)),
                          'network_requests': 0}))
        return
    if lib.sha(lib.CATALOGUE.read_bytes()) != plan['catalogue_sha256']:
        parser.error('Catalogue changed; use a new plan')
    # Retain the lock in the detached child; a duplicate launch cannot race it.
    with (output/'worker.lock').open('a') as lock:
        inherited = os.environ.pop('LIBRARY_WORKER_LOCK_FD', None)
        if inherited is None:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                parser.error('A library worker is already running')
        if args.background:
            with (output/'worker.log').open('a') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--execute',
                    '--output', str(output), '--max-requests', str(args.max_requests)],
                    cwd=lib.ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
                    pass_fds=(lock.fileno(),), env={**os.environ, 'LIBRARY_WORKER_LOCK_FD': str(lock.fileno())})
            print(json.dumps({'status': 'launched', 'pid': child.pid, 'log': str(output/'worker.log')}))
            return
        client = lib.Client(output/'raw', args.max_requests)
        try:
            result = work(plan, output, client)
        except Exception as error:
            progress(plan, output, client, 'stopped', reason=str(error))
            raise
        print(json.dumps(result))


if __name__ == '__main__':
    main()
