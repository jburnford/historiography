#!/usr/bin/env python3
"""Audit staged source queries locally, without network or graph changes."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def audit():
    base = ROOT / 'data/journal-catalogue/openalex-metadata-staging'
    plan = read(ROOT / 'feedback/journals/openalex-metadata-plan.json')
    catalogue_path = ROOT / 'data/journal-catalogue/catalogue.json'
    assert hashlib.sha256(catalogue_path.read_bytes()).hexdigest() == plan['catalogue_sha256']
    catalogue = read(catalogue_path)
    graph = read(ROOT / 'historiography-1920-2000.json')
    assert graph['journal_catalogue'] == catalogue
    nodes = {n['id']: n for n in catalogue['nodes']}
    outcomes, fields = Counter(), Counter()
    sources_to_candidates = defaultdict(list)
    rows, hashes, pending, conflicts = [], {}, [], []
    for candidate in plan['queue']:
        path = base / (candidate['journal_id'] + '.json')
        if not path.exists():
            pending.append(candidate['journal_id'])
            continue
        record = read(path)
        assert record['catalogue_sha256'] == plan['catalogue_sha256']
        assert record['candidate'] == candidate
        if record['retrieval_status'] != 'retrieved':
            pending.append(candidate['journal_id'])
            continue
        response, assessment = record['response'], record['assessment']
        assert response['request']['endpoint'] == 'https://api.openalex.org/sources'
        assert response['request']['params'] == candidate['params']
        assert assessment['accepted'] is False
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        outcomes[assessment['status']] += 1
        selected = [r for r in response['results'] if r['id'] in assessment['candidate_source_ids']]
        for source in selected:
            sources_to_candidates[source['id']].append(candidate['journal_id'])
        node = nodes[candidate['journal_id']]
        existing_date = node.get('date_span') or {}
        better_start = existing_date.get('start')
        if better_start is None:
            better_start = node.get('publication_start')
        row = {'journal_id': candidate['journal_id'], 'title': candidate['label'],
               'assessment': assessment, 'reported_results': response['meta'].get('count'),
               'source_candidates': [{'id': s['id'], 'title': s.get('display_name'),
                                      'issns': s.get('issn'), 'publisher': s.get('host_organization_name'),
                                      'first_indexed_year': s.get('first_publication_year'),
                                      'last_indexed_year': s.get('last_publication_year')}
                                     for s in selected],
               'existing_date_span': existing_date or None,
               'existing_publication_start': node.get('publication_start'),
               'existing_publication_end': node.get('publication_end'),
               'date_action': 'preserve_existing_dates' if (existing_date or node.get('publication_start') or node.get('publication_end'))
                              else 'indexed_range_fallback_only_after_identity_review'}
        if len(selected) == 1:
            source = selected[0]
            for field in ('issn', 'host_organization_name', 'homepage_url', 'country_code',
                          'first_publication_year', 'last_publication_year', 'topics'):
                if source.get(field):
                    fields[field] += 1
            if better_start is not None and better_start != source.get('first_publication_year'):
                conflicts.append({'journal_id': candidate['journal_id'], 'title': candidate['label'],
                                  'existing_start': better_start,
                                  'openalex_first_indexed_year': source.get('first_publication_year'),
                                  'action': 'preserve_existing_dates'})
        rows.append(row)
    collisions = {source: sorted(set(jids)) for source, jids in sources_to_candidates.items()
                  if len(set(jids)) > 1}
    return {'status': 'complete' if not pending else 'incomplete',
            'catalogue_revision': graph['revision_history'][-1]['version'],
            'catalogue_sha256': plan['catalogue_sha256'], 'planned_candidates': len(plan['queue']),
            'completed_queries': len(rows), 'pending_queries': len(pending),
            'assessment_counts': dict(outcomes),
            'truncated_queries': sum(r['assessment']['truncated'] for r in rows),
            'single_candidate_field_availability': dict(fields),
            'cross_candidate_source_collisions': collisions,
            'known_start_conflicts': conflicts,
            'date_policy': 'User: only use OpenAlex dates where better dates are absent. Preserve sourced publication chronology; any fallback is an attributed indexed range, not verified founding or cessation.',
            'remaining_work': 'Identity review, alternate-query research for misses, reconciliation of collisions, and separately reviewed metadata import. A completed query is not a verified journal match.',
            'automatically_accepted_matches': 0, 'graph_catalogue_equal': True,
            'pending_journal_ids': pending, 'staging_sha256': hashes, 'journals': rows}


if __name__ == '__main__':
    report = audit()
    path = ROOT / 'feedback/journals/openalex-metadata-full-audit.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'completed_queries', 'pending_queries',
                                            'assessment_counts', 'truncated_queries')}, indent=2))
