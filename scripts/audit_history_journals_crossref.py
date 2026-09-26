#!/usr/bin/env python3
"""Offline audit of a completed full Crossref journal collection and its exports."""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import duckdb

from harvest_history_journals_crossref import FIELDS, ROOT, sha, write_json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(work, build):
    selection = json.loads((work / 'selection.json').read_text())
    manifest = json.loads((work / 'manifest.json').read_text())
    report = json.loads((build / 'report.json').read_text())
    require(manifest['status'] == 'complete', 'Incomplete combined manifest')
    require(manifest['selection_sha256'] == sha(work / 'selection.json'), 'Selection changed')
    require(report['manifest_sha256'] == sha(work / 'manifest.json'), 'Combined manifest changed')
    if selection.get('approved_selection_path'):
        approved = ROOT / selection['approved_selection_path']
        require(sha(approved) == selection['approved_selection_sha256'], 'Approved selection changed')
        accepted = json.loads(approved.read_text())['journals']
        require(len(accepted) == len(selection['journals']), 'Selection length differs')
        for current, original in zip(selection['journals'], accepted):
            require(all(current.get(k) == v for k, v in original.items()), 'Approved journal context changed')
            require(current['key'] == original['journal_key'], 'Approved journal key changed')

    combined = {(e['journal_key'], e['path']): e for e in manifest['pages']}
    require(len(combined) == len(manifest['pages']), 'Duplicate combined page')
    source_journals = {j['key']: j for j in manifest['journals']}
    require(len(source_journals) == len(selection['journals']), 'Journal count mismatch')
    source_counts = {}
    page_count = occurrences = 0
    issn_status = Counter()
    with duckdb.connect(str(build / 'catalog.duckdb'), read_only=True) as c:
        c.execute("SET memory_limit='768MB'")
        c.execute('SET threads=1')
        for journal in selection['journals']:
            key = journal['key']
            source_info = source_journals[key]
            path = work / source_info['manifest_path']
            require(sha(path) == source_info['manifest_sha256'], 'Source manifest changed: ' + key)
            source = json.loads(path.read_text())
            expected_filter = ','.join('issn:' + i for i in journal['issns']) + ',until-pub-date:' + selection['cutoff']
            require(source['status'] == 'complete', 'Incomplete source: ' + key)
            require(source['filter'] == expected_filter and source['select'] == FIELDS, 'Different source query: ' + key)
            require(bool(source['pages']), 'No terminating source page: ' + key)
            # Keep each source occurrence's hash: canonical DOI rows may have a
            # different version when an earlier selected query returned that DOI.
            expected_memberships = {}
            cursor = '*'
            total = source['records']
            for index, entry in enumerate(source['pages']):
                page_path = path.parent / entry['path']
                require(sha(page_path) == entry['sha256'], 'Source page changed: ' + str(page_path))
                with gzip.open(page_path, 'rt') as f:
                    page = json.load(f)
                request = urlsplit(page['request'])
                require(request.scheme == 'https' and request.netloc == 'api.crossref.org' and request.path == '/works', 'Unexpected source endpoint')
                require(parse_qs(request.query) == {'filter': [expected_filter], 'select': [FIELDS], 'rows': ['1000'], 'cursor': [cursor]}, 'Broken cursor chain: ' + str(page_path))
                items = page['items']
                require(len(items) == entry['records'], 'Page count mismatch')
                require(page['total_results'] == entry['reported_total'] == total, 'Source totals disagree')
                require(bool(items) == (index < len(source['pages']) - 1), 'Missing or premature empty terminal page')
                relative = str(page_path.relative_to(work)) if page_path.is_relative_to(work) else None
                if relative is not None:
                    require(combined.get((key, relative), {}).get('sha256') == entry['sha256'], 'Combined page mismatch')
                for record in items:
                    require(not set(record) - set(FIELDS.split(',')), 'Metadata allowlist violation')
                    record_id = 'crossref:' + record['DOI'].lower()
                    require(record_id not in expected_memberships, 'Repeated source DOI: ' + record_id)
                    raw = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                    digest = hashlib.sha256(raw.encode()).hexdigest()
                    deposited = set(record.get('ISSN') or [])
                    status = 'matching_deposited_issn' if deposited & set(journal['issns']) else ('missing_deposited_issn' if not deposited else 'different_deposited_issn')
                    expected_memberships[record_id] = (digest, entry['sha256'], page['retrieved_at'], status)
                    issn_status[status] += 1
                cursor = page['next_cursor']
                page_count += 1
            require(len(expected_memberships) == total == source_info['harvest_records'], 'Journal source count mismatch')
            require(source['initial_total_results'] == source['last_total_results'] == total, 'Manifest total mismatch')
            actual = c.execute('SELECT record_id,metadata_sha256,source_page_sha256,retrieved_at,issn_match_status FROM memberships WHERE journal_key=?', [key]).fetchall()
            require(len(actual) == total and {r[0]: tuple(r[1:]) for r in actual} == expected_memberships, 'Exported source memberships differ: ' + key)
            source_counts[key] = total
            occurrences += total

        require(page_count == len(manifest['pages']), 'Combined page count mismatch')
        require(occurrences == manifest['records'] == report['metrics']['source_memberships'], 'Combined occurrence count mismatch')
        for table, key in [('records', 'record_id'), ('contributors', 'credit_id'), ('memberships', "journal_key || ':' || record_id"), ('journals', 'journal_key')]:
            n, unique = c.execute(f'SELECT count(*),count(DISTINCT {key}) FROM {table}').fetchone()
            require(n == unique, 'Duplicate/null key: ' + table)
            for left, right in [(table, 'read_parquet(?)'), ('read_parquet(?)', table)]:
                difference = c.execute(f'SELECT count(*) FROM (SELECT * FROM {left} EXCEPT ALL SELECT * FROM {right})', [str(build / (table + '.parquet'))]).fetchone()[0]
                require(difference == 0, 'Parquet differs: ' + table)
        require(c.execute('SELECT count(*) FROM records WHERE sha256(raw_metadata_json) != metadata_sha256').fetchone()[0] == 0, 'Raw metadata hash mismatch')
        require(c.execute('SELECT count(*) FROM records r WHERE NOT EXISTS (SELECT 1 FROM memberships m WHERE m.record_id=r.record_id AND m.metadata_sha256=r.metadata_sha256)').fetchone()[0] == 0, 'Canonical metadata lacks source membership')
        require(c.execute("SELECT count(*) FROM contributors WHERE identity_status != 'unreviewed'").fetchone()[0] == 0, 'Unexpected identity acceptance')
        require(c.execute("SELECT count(*) FROM records WHERE genre_status != 'unclassified'").fetchone()[0] == 0, 'Unexpected genre acceptance')
        # Credits must reproduce every author/editor/translator occurrence from
        # the saved canonical metadata, including empty arrays and raw ORCIDs.
        credit_count = c.execute("""
            WITH roles AS (
              SELECT record_id,role,raw_metadata_json
              FROM records CROSS JOIN (VALUES ('author'),('editor'),('translator')) t(role)
            )
            SELECT coalesce(sum(json_array_length(json_extract(raw_metadata_json,'$.' || role))),0) FROM roles
        """).fetchone()[0]
        require(credit_count == c.execute('SELECT count(*) FROM contributors').fetchone()[0], 'Raw contributor count differs')
        rows = c.execute("""
            SELECT c.raw_credit_json,json_extract(r.raw_metadata_json,
                '$.' || c.role_array || '[' || cast(c.position - 1 AS VARCHAR) || ']')
            FROM contributors c LEFT JOIN records r USING(record_id)
        """)
        while batch := rows.fetchmany(10000):
            for exported, original in batch:
                require(original is not None and json.loads(exported) == json.loads(original), 'Raw contributor occurrence differs')
        metrics = dict(report['metrics'])

    export_hashes = json.loads((build / 'export-hashes.json').read_text())
    for name, digest in export_hashes.items():
        require(sha(build / name) == digest, 'Frozen export changed: ' + name)
    result = {
        'status': 'passed', 'audited_at': datetime.now(timezone.utc).isoformat(),
        'audit_script_sha256': sha(Path(__file__)), 'selection_sha256': sha(work / 'selection.json'),
        'manifest_sha256': sha(work / 'manifest.json'), 'metrics': metrics,
        'pages_checked': page_count, 'source_occurrences_checked': occurrences,
        'membership_issn_status': dict(issn_status),
        'zero_result_journals': [j['key'] for j in selection['journals'] if source_counts[j['key']] == 0],
        'checks': ['approved_selection', 'source_manifest_and_page_hashes', 'exact_metadata_queries',
                   'cursor_chains_and_empty_terminal_pages', 'stable_source_totals', 'source_membership_equality',
                   'unique_keys', 'all_four_parquet_tables_equal_database', 'raw_metadata_hashes',
                   'raw_contributor_occurrences', 'unreviewed_genres_and_identities', 'frozen_export_hashes'],
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--build', type=Path)
    args = parser.parse_args()
    result = audit(args.work.resolve(), (args.build or args.work / 'generated/v1').resolve())
    write_json(args.work / 'audit.json', result)
    print(json.dumps(result, indent=2))
