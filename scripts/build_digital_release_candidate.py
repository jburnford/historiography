#!/usr/bin/env python3
"""Reconcile digital-history research and prepare a bounded, unapplied graph delta."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate as validate_research
from scripts.validate_graph import validate as validate_graph

OUT = ROOT / 'data/extension-2026/digital-release-10'
GRAPH = ROOT / 'historiography-1920-2000.json'
FIELDS = ('digital_history', 'web_history')
DAY = '2026-09-19'


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(serial(value).encode()).hexdigest()


def verify_inputs():
    return ['Pinned input changed: ' + name for name, expected in read(OUT/'baseline.json')['files'].items()
            if not (ROOT/name).is_file() or sha(ROOT/name) != expected]


def reconcile():
    r = read(OUT/'research-reconciliation.json')
    b = deepcopy(read(ROOT/r['prior_digital_packet']))
    old = read(ROOT/r['prior_breadth_packet'])
    actions = []
    inherited = [deepcopy(c) for c in old['claims'] if c['id'] in r['breadth_claim_ids']]
    if len(inherited) != len(r['breadth_claim_ids']):
        raise ValueError('Missing breadth claim')
    b['claims'].extend(inherited)
    sids = {e['source_record_id'] for c in inherited for e in c['evidence']}
    sources = [deepcopy(s) for s in old['source_records'] if s['id'] in sids]
    b['source_records'].extend(sources)
    eids = {c[k] for c in inherited for k in ('subject', 'object', 'attributed_to')}
    eids |= {s['describes_work'] for s in sources if s.get('describes_work')}
    current = {e['id']:e for e in b['entities']}
    for e in old['entities']:
        if e['id'] not in eids:
            continue
        if e['id'] in current:
            actions.append(dict(entity_id=e['id'], action='retain_digital07_concept_record',
                                previous_breadth_record=deepcopy(e), retained_record=deepcopy(current[e['id']])))
        else:
            b['entities'].append(deepcopy(e))
    for e in r['people'] + r['works']:
        b['entities'].append({k:deepcopy(v) for k,v in e.items() if k not in ('source','credit_locator')})
    for a in r['work_annotations']:
        e = next(e for e in b['entities'] if e['id'] == a['work_id'])
        actions.append(dict(entity_id=e['id'], action='add_author_date_navigation_metadata', previous_record=deepcopy(e)))
        for key in ('author_ids','publication_year_observation','candidate_navigation_ids','publication_note'):
            e[key] = deepcopy(a[key])
    for s in r['sources']:
        path = OUT/s['capture']
        b['source_records'].append({**{k:v for k,v in s.items() if k != 'capture'},
                                   'snapshot_path':str(path.relative_to(ROOT)), 'snapshot_sha256':sha(path),
                                   'observed_at':r['assembled_at']})
    for ev in r['evidence_additions']:
        c = next(c for c in b['claims'] if c['id'] == ev['claim_id'])
        actions.append(dict(claim_id=c['id'], action='append_evidence_without_rewriting_prior_claim', previous_record=deepcopy(c)))
        c['evidence'].append({k:v for k,v in ev.items() if k != 'claim_id'})
    b['claims'].extend(deepcopy(r['new_claims']))
    for w in r['works'] + [dict(a, id=a['work_id']) for a in r['work_annotations']]:
        for pid in w['author_ids']:
            b['claims'].append(dict(id='claim:digital10:authored:'+w['id'][5:]+':'+pid[7:],
                subject=pid, predicate='authored', object=w['id'], attributed_to=w['source'],
                basis='source_assertion', valid_time=None,
                review=dict(status='needs_review', rationale='Explicit author credit; no production import.'),
                history=[dict(date=DAY, action='proposed', reason='Complete coauthor metadata')],
                evidence=[dict(source_record_id=w['source'], locator=w['credit_locator'], scope='metadata',
                    check_status='metadata_checked', checked_on=DAY, support='Named author of this work.',
                    limitation='Authorship credit only; no demographic classification or full-work reading.',
                    support_assessment='supports_bounded_attribution')]))
    b['research_cutoff'] = DAY
    b['derivation'] = dict(digital_packet=r['prior_digital_packet'], breadth_packet=r['prior_breadth_packet'],
                          breadth_claim_ids=r['breadth_claim_ids'], review_actions='review-actions.json',
                          note='Consolidation supersedes entry drafts, not the frozen evidence packets.')
    return b, actions


def prepare(before, batch, decisions=None):
    d = read(OUT/'review-decisions.json') if decisions is None else decisions
    cs = {c['id']:c for c in batch['claims']}
    es = {e['id']:e for e in batch['entities']}
    historical = {c['id'] for c in batch['claims'] if c['predicate'] not in ('authored','realizes')}
    decision_ids = [x['claim_id'] for x in d['claims']]
    if set(decision_ids) != historical or len(decision_ids) != len(set(decision_ids)):
        raise ValueError('Every historical claim needs one explicit decision')
    chosen = {x['claim_id'] for x in d['claims'] if x['decision'] == 'recommend_bounded_acceptance'}
    for cid in chosen:
        if not any(e['check_status'] in ('passage_checked','abstract_checked') for e in cs[cid]['evidence']):
            raise ValueError('Description-only admission: ' + cid)
    works = {cs[cid]['subject'] for cid in chosen}
    versions = {e['id'] for e in batch['entities'] if e['type'] == 'version' and e['work_id'] in works}
    claims = deepcopy([c for c in batch['claims'] if c['id'] in chosen or
                       (c['predicate'] == 'authored' and c['object'] in works) or
                       (c['predicate'] == 'realizes' and c['subject'] in versions)])
    sids = {ev['source_record_id'] for c in claims for ev in c['evidence']}
    sources = deepcopy([s for s in batch['source_records'] if s['id'] in sids])
    eids = works | versions | {c[k] for c in claims for k in ('subject','object','attributed_to')}
    eids |= {s['describes_work'] for s in sources if s.get('describes_work')}
    entities = deepcopy([e for e in batch['entities'] if e['id'] in eids])
    existing_people = {p['id']:p for p in before['people']}
    new_people = []
    for e in entities:
        if e['type'] != 'person':
            continue
        pid = e['id'][7:]
        same_label = [p['id'] for p in before['people'] if p['label'].casefold() == e['label'].casefold()]
        if (same_label and same_label != [pid]) or (pid in existing_people and existing_people[pid]['label'] != e['label']):
            raise ValueError('Unresolved identity: ' + e['label'])
        e['legacy_person_id'] = pid
        e['identity_status'] = 'existing_local_person' if pid in existing_people else 'proposed_local_person'
        if pid not in existing_people:
            new_people.append(dict(id=pid,label=e['label'],identity_note='Local credited author; no inferred demographics or external authority.'))
    for c in claims:
        c['history'].append(dict(date=DAY, action='recommended_for_bounded_release',
                                decision_record='data/extension-2026/digital-release-10/review-decisions.json'))
    smap = {s['id']:'digital10_'+s['id'].replace(':','_') for s in sources}
    prior_urls = {s['claim_source_record_id']:s['url'] for s in read(ROOT/'data/extension-2026/digital-web-07/source-proposals.json')}
    url_additions = []
    for s in sources:
        if not s.get('url'):
            s['url'] = prior_urls[s['id']]
            url_additions.append(dict(source_record_id=s['id'], url=s['url'],
                from_record='data/extension-2026/digital-web-07/source-proposals.json',
                note='Add a browser-resolvable witness URL; retained source ID, capture and citation joins are unchanged.'))
    graph_sources = []
    for s in sources:
        limits = list(dict.fromkeys(ev['limitation'] for c in claims for ev in c['evidence'] if ev['source_record_id'] == s['id']))
        graph_sources.append(dict(id=smap[s['id']], title=es[s['describes_work']]['label']+' — consulted witness',
            url=s.get('url') or prior_urls[s['id']], claim_source_record_id=s['id'], scope_note=' '.join(limits)))
    recipes = read(OUT/'research-reconciliation.json')
    draft_nodes = {x['candidate_id']:x['node'] for x in read(ROOT/'data/extension-2026/digital-web-07/entry-proposals.json')}
    nodes = []
    for field in FIELDS:
        node = deepcopy(draft_nodes[field])
        ws = [e for e in entities if e['id'] in works and field in e.get('candidate_navigation_ids', [])]
        ordering = ['work:'+wid for wid in recipes['entry_work_order'][field]]
        ws.sort(key=lambda w:ordering.index(w['id']) if w['id'] in ordering else len(ordering))
        roster, strands = {}, []
        for w in ws:
            related = [c for c in claims if c['id'] in chosen and c['subject'] == w['id']]
            sources_for_work = list(dict.fromkeys(smap[ev['source_record_id']] for c in related for ev in c['evidence']))
            focus = ' '.join(c['statement']+' '+c['qualification'] for c in related)
            for pid in w['author_ids']:
                local = pid[7:]
                role = 'contributor' if local in ('kim_gallon','jessica_ogden','emily_maemura','kieran_hegarty','leisa_gibbons') else 'historian'
                row = roster.setdefault(local, dict(person_id=local, role=role, context='', works='', source_ids=[], basis='source_review'))
                row['context'] = (row['context']+' '+focus).strip()
                row['works'] = (row['works']+'; '+w['label']).strip('; ')
                row['source_ids'] = list(dict.fromkeys(row['source_ids']+sources_for_work))
            for year in sorted({c['intervention_year'] for c in related}):
                subset = [c for c in related if c['intervention_year'] == year]
                strands.append(dict(id='digital10_'+w['id'][5:]+'_'+str(year), title=w['label'],
                    focus=' '.join(c['statement']+' '+c['qualification'] for c in subset),
                    person_ids=[pid[7:] for pid in w['author_ids']], works=w['label'], work_ids=[w['id']],
                    claim_ids=[c['id'] for c in subset],
                    source_ids=list(dict.fromkeys(smap[ev['source_record_id']] for c in subset for ev in c['evidence'])),
                    work_publication_year=w['publication_year_observation'], intervention_year=year,
                    basis='editorial_distinction', review_status='needs_review'))
        years = sorted({w['publication_year_observation'] for w in ws})
        node.update(representative_people=list(roster.values()), strands=strands,
            representative_figures_and_works='; '.join(w['label']+' ('+str(w['publication_year_observation'])+')' for w in ws),
            source_ids=list(dict.fromkeys(s for row in strands for s in row['source_ids'])),
            work_ids=[w['id'] for w in ws], claim_ids=list(dict.fromkeys(c for row in strands for c in row['claim_ids'])),
            date_label=f'Earlier roots · selected publications {years[0]}–{years[-1]}; field chronology unresolved',
            date_span=dict(start=years[0], start_kind='earlier_roots', end=years[-1], end_kind='unstated', precision='year',
                           basis='Selected publication milestones only; neither endpoint defines the field’s existence.'),
            scope_note='Bounded selection of projects, methods, public practice and critical reflection. No founding year, complete genealogy or comprehensive field review through 2026 is asserted.')
        if field == 'digital_history':
            node['description'] = ('Historical inquiry using digital media to assemble and interpret evidence, develop arguments, '
                'publish scholarship, teach and involve public audiences. This selection spans digital projects, computational '
                'exploration, preservation and source criticism, including debates over participation, race, gender and scholarly credit. '
                'Digital history overlaps with quantitative history, public history and digital humanities without being equivalent to any of them.')
        node['extension_coverage'] = dict(status='release_candidate',baseline_through=2000,research_cutoff=DAY,
            field_review_complete=False, publication_years=years, work_ids=node['work_ids'],claim_ids=node['claim_ids'])
        # Authorship/version witnesses belong in the bibliography as well as in citation joins.
        node['source_ids'] = list(dict.fromkeys(node['source_ids'] +
            [smap[s['id']] for s in sources if s.get('describes_work') in node['work_ids']]))
        nodes.append(node)
    scope = deepcopy(before['scope']['extension'])
    scope.update(status='release_candidate', research_cutoff=DAY,
                 latest_selected_publication=max(es[w]['publication_year_observation'] for w in works),
                 field_ids=list(dict.fromkeys(scope['field_ids']+list(FIELDS))),
                 candidate_record='data/extension-2026/digital-release-10/candidate.json',
                 note='Preview combines the accepted medical/geographical subset with unapplied digital/web additions; no field is fully reviewed.')
    return dict(schema_version='extension_release_candidate/1', status='prepared_not_applied',
        baseline_revision='1.122', baseline_sha256=sha(GRAPH), people_additions=new_people, source_additions=graph_sources,
        catalogue_additions=dict(entities=entities,source_records=sources,claims=claims), node_additions=nodes,
        selected_work_ids=sorted(works), source_id_map=smap, source_url_additions=url_additions,
        extension_scope=scope, previous_extension_scope=before['scope']['extension'])


def project(before, candidate):
    if fingerprint(before) != candidate['baseline_sha256']:
        raise ValueError('Candidate does not match the exact production baseline')
    after = deepcopy(before)
    for key in ('nodes','people','sources'):
        additions = candidate[{'nodes':'node_additions','people':'people_additions','sources':'source_additions'}[key]]
        ids = {x['id'] for x in after[key]}
        for row in additions:
            if row['id'] in ids:
                raise ValueError('ID collision: '+row['id'])
            ids.add(row['id'])
            after[key].append(deepcopy(row))
    for key, rows in candidate['catalogue_additions'].items():
        ids = {x['id'] for x in after['claim_catalogue'][key]}
        for row in rows:
            if row['id'] in ids:
                raise ValueError('Catalogue collision: '+row['id'])
            ids.add(row['id'])
            after['claim_catalogue'][key].append(deepcopy(row))
    after['scope']['extension'] = deepcopy(candidate['extension_scope'])
    return after


def audit(before, after, batch, candidate):
    errors = validate_research(batch, read(ROOT/'ontology/contract-v0.2.json'), ROOT)
    graph_errors, warnings = validate_graph(after, read(ROOT/'seminar-pathways.json'))
    errors.extend(graph_errors)
    for key in before:
        if key in ('nodes','people','sources'):
            if after[key][:len(before[key])] != before[key]:
                errors.append('Prior '+key+' changed')
        elif key == 'claim_catalogue':
            for part, value in before[key].items():
                actual = after[key][part][:len(value)] if part in ('entities','claims','source_records') else after[key][part]
                if actual != value:
                    errors.append('Prior catalogue changed: '+part)
        elif key == 'scope':
            if {k:v for k,v in after[key].items() if k != 'extension'} != {k:v for k,v in before[key].items() if k != 'extension'}:
                errors.append('Baseline scope changed')
            for k in ('baseline_graph','baseline_revision','baseline_sha256','acceptance_record'):
                if after[key]['extension'][k] != before[key]['extension'][k]:
                    errors.append('Frozen baseline/acceptance pointer changed: '+k)
        elif after[key] != before[key]:
            errors.append('Unrelated object changed: '+key)
    claims = {c['id']:c for c in candidate['catalogue_additions']['claims']}
    for node in candidate['node_additions']:
        for strand in node['strands']:
            for cid in strand['claim_ids']:
                if strand['intervention_year'] != claims[cid]['intervention_year']:
                    errors.append('Lost intervention/reception date: '+strand['id'])
    return errors, warnings


def outputs():
    before = read(GRAPH)
    batch, actions = reconcile()
    candidate = prepare(before,batch)
    after = project(before,candidate)
    errors,warnings = audit(before,after,batch,candidate)
    claims = candidate['catalogue_additions']['claims']
    historical = [c for c in claims if c['predicate'] not in ('authored','realizes')]
    coverage_path = ROOT/'data/extension-2026/transnational-mobility-09/coverage-current.json'
    coverage = deepcopy(read(coverage_path))
    coverage['derived_from'] = str(coverage_path.relative_to(ROOT))
    coverage['supplement_packet'] = str((OUT/'reconciled-research.json').relative_to(ROOT))
    for row in coverage['field_candidates']:
        if row['candidate_id'] not in FIELDS:
            continue
        node = next(n for n in candidate['node_additions'] if n['id'] == row['candidate_id'])
        row['disposition'] = 'release_candidate_pending_acceptance'
        row['production_ready'] = False
        row['release_candidate'] = str((OUT/'candidate.json').relative_to(ROOT))
        row['new_work_ids'] = list(dict.fromkeys(row['new_work_ids']+node['work_ids']))
        selected = {e['id']:e for e in candidate['catalogue_additions']['entities']}
        for wid in node['work_ids']:
            year = selected[wid]['publication_year_observation']
            key = '2001_2009' if year < 2010 else '2010_2019' if year < 2020 else '2020_cutoff'
            part = row['research_bins'][key]
            part['work_ids'] = list(dict.fromkeys(part['work_ids']+[wid]))
            part['status'] = 'partial_evidence'
    summary = dict(status='prepared_not_applied', errors=errors,warnings=warnings,
        selected_works=len(candidate['selected_work_ids']), work_referents=sum(e['type']=='work' for e in candidate['catalogue_additions']['entities']),
        historical_claims=len(historical), historical_evidence=dict(Counter('passage_checked' if any(e['check_status']=='passage_checked' for e in c['evidence']) else 'abstract_checked' for c in historical)),
        authorship_credits=sum(c['predicate']=='authored' for c in claims), version_links=sum(c['predicate']=='realizes' for c in claims),
        candidate_claims=len(claims), new_shared_people=len(candidate['people_additions']), new_entries=len(candidate['node_additions']),
        new_strands=sum(len(n['strands']) for n in candidate['node_additions']), new_teaching_edges=0,
        candidate_totals={k:len(after[k]) for k in ('nodes','edges','sources','people')}, fully_reviewed_fields=0, production_imports=0)
    return {'reconciled-research.json':batch,'review-actions.json':actions,'candidate.json':candidate,'coverage-current.json':coverage,
            'entry-proposals.json':candidate['node_additions'],'summary.json':summary},after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    errors = verify_inputs()
    if errors:
        raise SystemExit('\n'.join(errors))
    generated,after = outputs()
    errors.extend(generated['summary.json']['errors'])
    if args.check:
        for name,value in generated.items():
            if not (OUT/name).is_file() or (OUT/name).read_text() != serial(value):
                errors.append('Rebuild mismatch: '+name)
        for name,expected in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name) != expected:
                errors.append('Manifest mismatch: '+name)
    elif not errors:
        for name,value in generated.items():
            (OUT/name).write_text(serial(value))
        files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json']
        files += [Path(__file__).resolve(),ROOT/'tests/test_digital_release_candidate.py',ROOT/'tests/test_digital_release_browser.py']
        (OUT/'manifest.json').write_text(serial(dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files) if p.is_file()})))
    if args.preview and not errors:
        dest = args.preview.resolve()
        if not dest.is_relative_to(Path('/tmp')):
            raise SystemExit('Preview destination must be under /tmp')
        dest.write_text(serial(after))
    print(serial({**generated['summary.json'],'errors':errors}),end='')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
