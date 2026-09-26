#!/usr/bin/env python3
"""Summarize the frozen full collection and refresh its unreviewed ORCID list."""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import duckdb

WORK = Path(__file__).resolve().parent
PRIOR = WORK.parent / 'history-journal-profession-review-2026-09-22/orcid-candidates.csv'
DEMO = '0000-0002-1825-0097'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def valid_orcid(value):
    if not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dxX]', value):
        return False
    digits = value.replace('-', '').upper()
    total = 0
    for digit in digits[:15]:
        total = (total + int(digit)) * 2
    result = (12 - total % 11) % 11
    return digits[-1] == ('X' if result == 10 else str(result))


def main():
    output = WORK / 'orcid-candidates.csv'
    summary_path = WORK / 'metadata-summary.json'
    if output.exists() or summary_path.exists():
        raise ValueError('Completed summary exists; preserve this snapshot')
    with PRIOR.open() as f:
        prior = {r['orcid_id']: r for r in csv.DictReader(f)}
    database = WORK / 'generated/v1/catalog.duckdb'
    before = sha(database)
    with duckdb.connect(str(database), read_only=True) as c:
        rows = c.execute("""
            SELECT orcid_id, string_agg(DISTINCT name, ' | ' ORDER BY name),
              count(DISTINCT record_id), count(*), max(publication_year),
              count(DISTINCT record_id) FILTER (WHERE publication_year >= 2020),
              coalesce(bool_or(json_extract_string(raw_credit_json, '$."authenticated-orcid"') = 'true'), false)
            FROM normalized_orcids JOIN records USING(record_id)
            WHERE orcid_id != ? GROUP BY orcid_id ORDER BY orcid_id
        """, [DEMO]).fetchall()
        fields = ['orcid_id', 'selected_deposited_names', 'selected_publication_records',
                  'selected_contributor_credits', 'latest_selected_publication_year',
                  'selected_records_since_2020', 'any_selected_deposited_authenticated_flag',
                  'identity_status', 'quality_flags']
        candidates = [dict(zip(fields, [*r, 'unreviewed', prior.get(r[0], {}).get('quality_flags', '[]')])) for r in rows]
        ids = {r['orcid_id'] for r in candidates}
        if len(ids) != len(candidates) or not all(valid_orcid(i) for i in ids):
            raise ValueError('Duplicate or malformed candidate ORCID')
        new_ids, missing = sorted(ids - prior.keys()), sorted(prior.keys() - ids)
        summary = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'database_sha256': before, 'prior_candidates_sha256': sha(PRIOR),
            'script_sha256': sha(Path(__file__)),
            'non_demo_orcid_candidates': len(candidates),
            'new_candidate_ids_since_prior_snapshot': new_ids,
            'prior_ids_absent_from_full_harvest': missing,
            'inherited_quality_flag_ids': [r['orcid_id'] for r in candidates if json.loads(r['quality_flags'])],
            'records_with_affiliations': c.execute("SELECT count(DISTINCT record_id) FROM contributors WHERE affiliation_json != '[]'").fetchone()[0],
            'records_with_calculated_page_length': c.execute('SELECT count(page_count) FROM records').fetchone()[0],
            'at_least_ten_page_article_candidates': c.execute('SELECT count(*) FROM research_candidates_by_length').fetchone()[0],
            'test_records': c.execute('SELECT count(*) FROM records WHERE is_test_record').fetchone()[0],
            'record_types': dict(c.execute('SELECT record_type,count(*) FROM records GROUP BY 1 ORDER BY 1').fetchall()),
            'length_bands': dict(c.execute('SELECT length_band,count(*) FROM records GROUP BY 1 ORDER BY 1').fetchall()),
            'excluded_demo_id': DEMO,
            'records_with_demo_id': c.execute('SELECT count(DISTINCT record_id) FROM normalized_orcids WHERE orcid_id=?', [DEMO]).fetchone()[0],
            'new_candidate_evidence': [],
            'limitations': [
                'ORCIDs and names are deposited identity assertions, not accepted person groundings.',
                'Existing quality flags are inherited unchanged; no new identity adjudication was performed.',
                'Genre is unclassified; page length is a screening aid.',
                'DOI rows are not deduplicated publications; title-query memberships overlap.',
            ],
        }
        for identifier in new_ids:
            query = c.execute('SELECT orcid_id,name,records.doi,title_text,publication_date FROM normalized_orcids JOIN records USING(record_id) WHERE orcid_id=?', [identifier])
            names = [d[0] for d in query.description]
            summary['new_candidate_evidence'].extend(dict(zip(names, r)) for r in query.fetchall())
    if sha(database) != before:
        raise ValueError('Source database changed')
    with output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    summary['candidate_csv_sha256'] = sha(output)
    summary['validation'] = {'database_unchanged': True, 'unique_candidate_ids': True,
                             'orcid_checksums_valid': True, 'demo_excluded': DEMO not in ids}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
