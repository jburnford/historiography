#!/usr/bin/env python3
"""Prepare and validate a bounded extension delta; never modify production."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

OUT = ROOT / 'data/extension-2026/release-candidate-06'
PACKET = ROOT / 'data/extension-2026/health-geography-05'
GRAPH = ROOT / 'historiography-1920-2000.json'
FIELDS = ('medicalhistory', 'spatialhistory')
DAY = '2026-09-18'


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(serial(value).encode()).hexdigest()


def verify_inputs():
    errors = []
    for name, expected in read(OUT / 'baseline.json')['files'].items():
        p = ROOT / name
        if not p.is_file() or sha(p) != expected:
            errors.append('Pinned input changed: ' + name)
    for name, expected in read(PACKET / 'manifest.json')['files'].items():
        p = ROOT / name
        if not p.is_file() or sha(p) != expected:
            errors.append('Research input changed: ' + name)
    return errors


def prepare(before=None, batch=None, decisions=None):
    before = read(GRAPH) if before is None else before
    batch = read(PACKET / 'batch.json') if batch is None else batch
    decisions = read(OUT / 'review-decisions.json') if decisions is None else decisions
    if before['revision_history'][-1]['version'] != '1.121':
        raise ValueError('Review is pinned to revision 1.121; rebase explicitly.')
    cs = {c['id']: c for c in batch['claims']}
    es = {e['id']: e for e in batch['entities']}
    chosen = [d['claim_id'] for d in decisions['claims'] if d['decision'] == 'recommend_bounded_acceptance']
    if len(chosen) != len(set(chosen)):
        raise ValueError('Duplicate claim decision')
    works = {cs[cid]['subject'] for cid in chosen}
    for cid in chosen:
        c = cs[cid]
        if c['predicate'] in ('authored', 'realizes') or c['intervention_year'] <= 2000:
            raise ValueError('Not a post-2000 historical proposal: ' + cid)
        if not any(e['check_status'] in ('passage_checked', 'abstract_checked') for e in c['evidence']):
            raise ValueError('Description-only relation cannot be recommended: ' + cid)
        if not set(es[c['subject']]['field_navigation_ids']) <= set(FIELDS):
            raise ValueError('Outside the reviewed two-field release: ' + cid)
    versions = {e['id'] for e in batch['entities'] if e['type'] == 'version' and e['work_id'] in works}
    selected = [c for c in batch['claims'] if c['id'] in chosen or
                (c['predicate'] == 'authored' and c['object'] in works) or
                (c['predicate'] == 'realizes' and c['subject'] in versions)]
    entity_ids = works | versions | {c[k] for c in selected for k in ('subject', 'object')}
    source_ids = {e['source_record_id'] for c in selected for e in c['evidence']}
    sources = [deepcopy(s) for s in batch['source_records'] if s['id'] in source_ids]
    source_map = {s['id']: 'healthgeo05_' + s['describes_work'].split(':', 1)[1] for s in sources}
    people = {p['id']: p for p in before['people']}
    entities, new_people = [], []
    for original in batch['entities']:
        if original['id'] not in entity_ids:
            continue
        e = deepcopy(original)
        if e['type'] == 'person':
            pid = e['id'].split(':', 1)[1]
            same_label = [p['id'] for p in people.values() if p['label'].casefold() == e['label'].casefold()]
            if same_label and same_label != [pid]:
                raise ValueError('Unresolved shared-person identity: ' + e['label'])
            if pid in people and people[pid]['label'] != e['label']:
                raise ValueError('Person ID collision: ' + pid)
            if pid not in people:
                new_people.append({'id': pid, 'label': e['label'],
                                   'identity_note': 'Local author identity; no external authority or demographic assertion.'})
            e['legacy_person_id'] = pid
            e['identity_status'] = 'existing_local_person' if pid in people else 'proposed_local_person'
        entities.append(e)
    claims = deepcopy(selected)
    for c in claims:
        c['review'] = {'status': 'needs_review', 'reviewed_on': DAY,
                       'rationale': 'Recommended within the recorded evidence scope; release candidate only, not accepted in production.'}
        c['history'].append({'date': DAY, 'action': 'recommended_for_bounded_release',
                             'decision_record': 'data/extension-2026/release-candidate-06/review-decisions.json'})
    graph_sources = []
    for s in sources:
        w = es[s['describes_work']]
        limits = list(dict.fromkeys(e['limitation'] for c in claims for e in c['evidence']
                                  if e['source_record_id'] == s['id']))
        graph_sources.append({'id': source_map[s['id']], 'title': w['label'] + ' — consulted witness',
                              'url': s['url'], 'citation': w['label'] + ' (' + str(w['publication_year_observation']) + ').',
                              'scope_note': ' '.join(limits), 'claim_source_record_id': s['id']})
    original_nodes = {n['id']: n for n in before['nodes']}
    drafts = {d['entry_id']: d for d in read(PACKET / 'entry-proposals.json')}
    updated = []
    for field in FIELDS:
        node = deepcopy(original_nodes[field])
        field_works = [e for e in entities if e['type'] == 'work' and field in e['field_navigation_ids']]
        pids = {pid.split(':', 1)[1] for w in field_works for pid in w['author_ids']}
        old_pids = {p['person_id'] for p in node['representative_people']}
        proposal = drafts[field]['node']
        for row in proposal['representative_people']:
            if row['person_id'] in pids - old_pids:
                node['representative_people'].append(deepcopy(row))
                old_pids.add(row['person_id'])
        for w in field_works:
            sid = 'healthgeo05_' + w['id'].split(':', 1)[1]
            strand_id = 'extension05_' + w['id'].split(':', 1)[1]
            strand = deepcopy(next(s for s in proposal['strands'] if s['id'] == strand_id))
            strand['claim_ids'] = [cid for cid in strand['claim_ids'] if cid in chosen]
            if not strand['claim_ids']:
                raise ValueError('Work has no selected historical claim')
            strand['intervention_year'] = w['publication_year_observation']
            strand['work_ids'] = [w['id']]
            node['strands'].append(strand)
            node['source_ids'].append(sid)
        field_cids = [c['id'] for c in claims if c['id'] in chosen and c['subject'] in {w['id'] for w in field_works}]
        node.setdefault('work_ids', []).extend(w['id'] for w in field_works)
        node.setdefault('claim_ids', []).extend(field_cids)
        node['extension_coverage'] = {'status': 'release_candidate', 'baseline_through': 2000,
                                      'research_cutoff': DAY, 'field_review_complete': False,
                                      'publication_years': sorted({w['publication_year_observation'] for w in field_works}),
                                      'work_ids': [w['id'] for w in field_works], 'claim_ids': field_cids}
        # Baseline label/prose is preserved: the renderer must display the separate extension.
        updated.append({'entry_id': field, 'expected_node_sha256': fingerprint(original_nodes[field]), 'node': node})
    return {'schema_version': 'extension_release_candidate/1', 'status': 'prepared_not_applied',
            'baseline_revision': '1.121', 'baseline_sha256': sha(GRAPH),
            'research_packet': str((PACKET / 'batch.json').relative_to(ROOT)),
            'review_decisions': str((OUT / 'review-decisions.json').relative_to(ROOT)),
            'people_additions': new_people, 'source_additions': graph_sources,
            'catalogue_additions': {'entities': entities, 'source_records': sources, 'claims': claims},
            'updated_nodes': updated, 'source_id_map': source_map,
            'extension_scope': {'status': 'release_candidate', 'baseline_period': [1920, 2000],
                                'proposed_view_period': [1920, 2026], 'research_cutoff': DAY,
                                'latest_selected_publication': max(es[w]['publication_year_observation'] for w in works),
                                'field_ids': list(FIELDS), 'fully_reviewed_fields': 0,
                                'note': 'Selected post-2000 interventions only. The 2026 cutoff is not a publication date or a claim of field completeness.'}}


def project(before, candidate):
    if fingerprint(before) != candidate['baseline_sha256']:
        raise ValueError('Candidate does not match the exact production baseline')
    graph = deepcopy(before)
    nodes = {n['id']: n for n in before['nodes']}
    for change in candidate['updated_nodes']:
        if fingerprint(nodes[change['entry_id']]) != change['expected_node_sha256']:
            raise ValueError('Stale entry draft: ' + change['entry_id'])
    replacements = {c['entry_id']: c['node'] for c in candidate['updated_nodes']}
    graph['nodes'] = [deepcopy(replacements.get(n['id'], n)) for n in before['nodes']]
    for key, addition in [('people', 'people_additions'), ('sources', 'source_additions')]:
        ids = {x['id'] for x in graph[key]}
        for row in candidate[addition]:
            if row['id'] in ids:
                raise ValueError('Duplicate ' + key + ': ' + row['id'])
            ids.add(row['id'])
            graph[key].append(deepcopy(row))
    for key, rows in candidate['catalogue_additions'].items():
        ids = {x['id'] for x in graph['claim_catalogue'][key]}
        for row in rows:
            if row['id'] in ids:
                raise ValueError('Catalogue collision: ' + row['id'])
            ids.add(row['id'])
            graph['claim_catalogue'][key].append(deepcopy(row))
    graph['scope']['extension'] = deepcopy(candidate['extension_scope'])
    return graph


def audit(before, after, candidate):
    errors, warnings = validate(after, read(ROOT / 'seminar-pathways.json'))
    if any(c['review']['status'] != 'needs_review' for c in candidate['catalogue_additions']['claims']):
        errors.append('Candidate must not silently accept research claims')
    for key in before:
        if key not in ('nodes', 'people', 'sources', 'claim_catalogue', 'scope') and after[key] != before[key]:
            errors.append('Unrelated production object changed: ' + key)
    for key in ('people', 'sources'):
        if before[key] != after[key][:len(before[key])]:
            errors.append('Prior ' + key + ' changed')
    for key, value in before['claim_catalogue'].items():
        if key in ('entities', 'source_records', 'claims'):
            if value != after['claim_catalogue'][key][:len(value)]:
                errors.append('Prior catalogue ' + key + ' changed')
        elif value != after['claim_catalogue'][key]:
            errors.append('Prior catalogue metadata changed: ' + key)
    if {k:v for k,v in after['scope'].items() if k != 'extension'} != before['scope']:
        errors.append('Baseline scope changed')
    new_nodes = {n['id']: n for n in after['nodes']}
    for old in before['nodes']:
        new = new_nodes[old['id']]
        if old['id'] not in FIELDS:
            if old != new:
                errors.append('Unrelated entry changed: ' + old['id'])
            continue
        for key, value in old.items():
            if key in ('representative_people', 'strands', 'source_ids', 'work_ids', 'claim_ids'):
                if value != new[key][:len(value)]:
                    errors.append('Prior node ' + key + ' changed: ' + old['id'])
            elif value != new[key]:
                errors.append('Prior node metadata changed: ' + old['id'] + '/' + key)
        for strand in new['strands'][len(old['strands']):]:
            for cid in strand['claim_ids']:
                c = next(c for c in candidate['catalogue_additions']['claims'] if c['id'] == cid)
                if c['intervention_year'] != strand['intervention_year']:
                    errors.append('Strand intervention date mismatch: ' + strand['id'])
    return errors, warnings


def outputs():
    before = read(GRAPH)
    candidate = prepare(before)
    after = project(before, candidate)
    errors, warnings = audit(before, after, candidate)
    catalogue = candidate['catalogue_additions']
    substantive = [c for c in catalogue['claims'] if c['predicate'] not in ('authored', 'realizes')]
    coverage = read(PACKET / 'coverage-current.json')
    summary = {'status': 'prepared_not_applied', 'errors': errors, 'warnings': warnings,
               'works': sum(e['type'] == 'work' for e in catalogue['entities']),
               'historical_claims': len(substantive),
               'evidence_scopes': dict(Counter(c['evidence'][0]['check_status'] for c in substantive)),
               'author_credits': sum(c['predicate'] == 'authored' for c in catalogue['claims']),
               'version_links': sum(c['predicate'] == 'realizes' for c in catalogue['claims']),
               'new_shared_people': len(candidate['people_additions']),
               'new_strands': sum(len(c['node']['extension_coverage']['work_ids']) for c in candidate['updated_nodes']),
               'new_teaching_edges': 0, 'production_imports': 0,
               'candidate_totals': {k:len(after[k]) for k in ('nodes', 'edges', 'people', 'sources')},
               'full_phase': {'topics': len(coverage['topics']),
                              'topic_outcomes': dict(Counter(r['review_outcome'] for r in coverage['topics'])),
                              'candidate_fields': len(coverage['field_candidates']),
                              'candidate_dispositions': dict(Counter(r['disposition'] for r in coverage['field_candidates'])),
                              'note': 'Ledger outcomes, not an estimate of research hours or percentage complete.'}}
    return {'candidate.json': candidate, 'summary.json': summary}, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--preview', type=Path, help='Write a simulated graph under /tmp only')
    args = parser.parse_args()
    errors = verify_inputs()
    if errors:
        raise SystemExit('\n'.join(errors))
    generated, after = outputs()
    errors.extend(generated['summary.json']['errors'])
    if args.check:
        for name, value in generated.items():
            if not (OUT/name).is_file() or (OUT/name).read_text() != serial(value):
                errors.append('Rebuild mismatch: ' + name)
        for name, expected in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name) != expected:
                errors.append('Manifest mismatch: ' + name)
    elif not errors:
        for name, value in generated.items():
            (OUT/name).write_text(serial(value))
        files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json']
        files += [Path(__file__).resolve(), ROOT/'tests/test_extension_release_candidate.py']
        (OUT/'manifest.json').write_text(serial({'files': {str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}}))
    if args.preview and not errors:
        dest = args.preview.resolve()
        if not dest.is_relative_to(Path('/tmp')):
            raise SystemExit('Preview output must be under /tmp; this tool cannot write production or website assets.')
        dest.write_text(serial(after))
    print(serial({**generated['summary.json'], 'errors':errors}), end='')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
