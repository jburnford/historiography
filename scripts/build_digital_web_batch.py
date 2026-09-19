#!/usr/bin/env python3
"""Build a source-scoped digital/web-history packet without changing production."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate

OUT = ROOT / 'data/extension-2026/digital-web-07'
COVERAGE = ROOT / 'data/extension-2026/health-geography-05/coverage-current.json'


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_baseline(name, expected):
    path = ROOT / name
    if path.is_file() and sha(path) == expected:
        return path
    if name == 'historiography-1920-2000.json':
        version = read(OUT/'baseline.json')['production_revision']
        archived = ROOT / f'drafts/historiography-1920-2000.v{version}.json'
        if archived.is_file() and sha(archived) == expected:
            return archived
    raise ValueError('Protected baseline changed without matching archive: ' + name)


def build(recipe=None):
    r = read(OUT/'research.json') if recipe is None else recipe
    old = read(ROOT/r['prior_packet'])
    selected = [deepcopy(c) for c in old['claims'] if c['id'] in r['prior_claim_ids']]
    if len(selected) != len(r['prior_claim_ids']):
        raise ValueError('Missing or repeated prior claim')
    source_ids = {e['source_record_id'] for c in selected for e in c['evidence']}
    sources = [deepcopy(s) for s in old['source_records'] if s['id'] in source_ids]
    entity_ids = {c[k] for c in selected for k in ('subject', 'object', 'attributed_to')}
    entity_ids |= {s['describes_work'] for s in sources if s.get('describes_work')}
    entities = [deepcopy(e) for e in old['entities'] if e['id'] in entity_ids]
    b = dict(schema_version='0.2', fixture_only=True, status='staging_only', production_graph_imports=0,
             research_cutoff=r['cutoff'], entities=entities, source_records=sources, claims=selected,
             derivation=dict(prior_packet=r['prior_packet'], prior_claim_ids=r['prior_claim_ids'],
                             note='Selected prior records, not a cumulative copy of the entire recovery packet. Counts overlap.'))
    actions = []
    for annotation in r['prior_work_annotations']:
        work = next(e for e in entities if e['id'] == annotation['work_id'])
        actions.append(dict(entity_id=work['id'], previous_record=deepcopy(work),
                            action='add_explicit_author_date_and_navigation_metadata', source_record_id=annotation['source']))
        work.update({k:deepcopy(annotation[k]) for k in ('author_ids', 'publication_year_observation', 'candidate_navigation_ids')})
    for s in r['sources']:
        p = OUT/s['capture']
        sources.append({**{k:v for k,v in s.items() if k != 'capture'},
                        'snapshot_path':str(p.relative_to(ROOT)), 'snapshot_sha256':sha(p),
                        'observed_at':r['assembled_at'],
                        'observation_note':'Assembly timestamp; actual citation scope is recorded separately.'})
    for e in r['people'] + r['concepts'] + r['versions'] + r['works']:
        entities.append({k:deepcopy(v) for k,v in e.items() if k not in ('source', 'credit_source', 'credit_locator')})

    def evidence(source, locator, statement, limitation, check):
        return dict(source_record_id=source, locator=locator, support=statement,
                    limitation=limitation, check_status=check,
                    scope={'passage_checked':'passage', 'abstract_checked':'abstract', 'metadata_checked':'metadata'}[check],
                    checked_on=r['cutoff'], support_assessment='supports_bounded_attribution')

    def add(row, ev, basis):
        b['claims'].append({**row, 'basis':basis, 'valid_time':None,
                            'review':dict(status='needs_review', rationale='Scoped research proposal; no production acceptance.'),
                            'history':[dict(date=r['cutoff'], action='proposed', reason='Digital/web continuation and contributor review')],
                            'evidence':[ev]})
    for c in r['claims']:
        add({k:deepcopy(v) for k,v in c.items() if k not in ('source_record_id', 'locator', 'check_status')},
            evidence(c['source_record_id'], c['locator'], c['statement'], c['qualification'], c['check_status']),
            'editorial_interpretation')
    for w in r['works'] + [dict(a, id=a['work_id']) for a in r['prior_work_annotations']]:
        source = w.get('credit_source', w['source'])
        for pid in w['author_ids']:
            add(dict(id='claim:digital07:authored:'+w['id'].split(':',1)[1]+':'+pid.split(':',1)[1],
                     subject=pid, predicate='authored', object=w['id'], attributed_to=source),
                evidence(source, w['credit_locator'], 'Named author of this work.',
                         'Authorship metadata only; no demographic or whole-work reading claim.', 'metadata_checked'), 'source_assertion')
    for v in r['versions']:
        add(dict(id='claim:digital07:realizes:'+v['id'].split(':')[-1], subject=v['id'], predicate='realizes',
                 object=v['work_id'], attributed_to=v['source_record_id']),
            evidence(v['source_record_id'], 'Repository citation or publisher issue/online metadata',
                     v['label'], v['version_note'], 'metadata_checked'), 'source_assertion')

    allworks = [e for e in entities if e['type'] == 'work']
    history = [c for c in b['claims'] if c['predicate'] not in ('authored', 'realizes')]
    coverage = deepcopy(read(COVERAGE))
    coverage['derived_from'] = str(COVERAGE.relative_to(ROOT))
    coverage['supplement_packet'] = str((OUT/'batch.json').relative_to(ROOT))
    for row in coverage['field_candidates']:
        matching = [w for w in allworks if row['candidate_id'] in w.get('candidate_navigation_ids', [])]
        if not matching:
            continue
        row['new_work_ids'] = list(dict.fromkeys(row['new_work_ids'] + [w['id'] for w in matching]))
        row['disposition'] = ('separate_entry_draft_pending_review' if row['candidate_id'] in ('digital_history','web_history')
                              else 'partial_research_no_field_decision')
        row['production_ready'] = False
        row['research_bins'] = {key:dict(status='not_researched', work_ids=[]) for key in ('2001_2009','2010_2019','2020_cutoff')}
        for w in matching:
            y = w['publication_year_observation']
            key = '2001_2009' if y < 2010 else '2010_2019' if y < 2020 else '2020_cutoff'
            row['research_bins'][key]['work_ids'].append(w['id'])
            row['research_bins'][key]['status'] = 'partial_evidence'
    drafts = []
    labels = {'digital_history':'Digital history', 'web_history':'Web history / Archived-web research'}
    scopes = {
        'digital_history':'Historical research, interpretation, preservation, teaching and public communication using digital media. This overlaps with quantitative, computational and public history without being equivalent to any of them or to all digital humanities.',
        'web_history':'Historical inquiry into the web and inquiry using archived web evidence. These overlap but differ: web archives also inform political, social and cultural histories whose object is not the web itself. Archival and information scholars contribute contextual methods without being assigned an exclusive historian profession.'}
    for field, label in labels.items():
        ws = [w for w in allworks if field in w.get('candidate_navigation_ids', [])]
        wids = {w['id'] for w in ws}
        cs = [c for c in history if c['subject'] in wids]
        roster, strands = {}, []
        for w in ws:
            related = [c for c in cs if c['subject'] == w['id']]
            sids = list(dict.fromkeys(ev['source_record_id'] for c in related for ev in c['evidence']))
            focus = ' '.join(c['statement']+' '+c['qualification'] for c in related)
            for pid in w['author_ids']:
                local = pid.split(':',1)[1]
                if local not in roster:
                    role = 'contributor' if local in ('kim_gallon','jessica_ogden','emily_maemura','kieran_hegarty','leisa_gibbons') else 'historian'
                    roster[local] = dict(person_id=local, role=role, context=focus, works=w['label'],
                                         source_ids=['digital07_'+s.split(':')[-1] for s in sids], basis='source_review')
            intervention_years = sorted({c['intervention_year'] for c in related})
            strands.append(dict(id='digital07_'+w['id'].split(':',1)[1], title=w['label'], focus=focus,
                                person_ids=[p.split(':',1)[1] for p in w['author_ids']], works=w['label'],
                                work_ids=[w['id']], claim_ids=[c['id'] for c in related],
                                source_ids=['digital07_'+s.split(':')[-1] for s in sids],
                                work_publication_year=w['publication_year_observation'],
                                intervention_years=intervention_years, basis='editorial_distinction', review_status='needs_review'))
        years = sorted({c['intervention_year'] for c in cs})
        node = dict(id=field, label=label, entry_kind='group', entry_type='Research field',
                    layer='historiographical_developments', period=None, hunt_core_paradigm=False,
                    date_label='Earlier roots unresolved · selected interventions '+str(years[0])+'–'+str(years[-1]),
                    description=scopes[field], scope_note='Partial entry draft, not a founding chronology or comprehensive field survey through 2026. Older breadth-packet works remain separate research and must be reconciled before acceptance.',
                    representative_people=list(roster.values()), strands=strands,
                    representative_figures_and_works='; '.join(w['label']+' ('+str(w['publication_year_observation'])+')' for w in ws),
                    source_ids=list(dict.fromkeys(s for strand in strands for s in strand['source_ids'])),
                    work_ids=[w['id'] for w in ws], claim_ids=[c['id'] for c in cs])
        drafts.append(dict(candidate_id=field, status='needs_review', proposed_disposition='separate_entry', node=node,
                           production_import=False, acceptance_requirements=['Reconcile earlier breadth works and shared identities', 'Map source IDs and catalogue claims through a production adapter', 'Review regional/language gaps and field boundaries']))
    summary = dict(status='staging_only', new_works=len(r['works']), reused_work_referents=len(allworks)-len(r['works']),
                   works_total=len(allworks), new_historical_claims=len(r['claims']), reused_historical_claims=len(r['prior_claim_ids']),
                   historical_claims=len(history), historical_evidence=dict(Counter(c['evidence'][0]['check_status'] for c in history)),
                   authorship_credits=sum(c['predicate']=='authored' for c in b['claims']),
                   version_links=len(r['versions']), claims_total=len(b['claims']), people=len(r['people']),
                   entry_drafts=len(drafts), fully_reviewed_fields=0, production_imports=0)
    source_proposals = []
    old_urls = {
        'source:recovery:leon':'https://dhdebates.gc.cuny.edu/read/untitled-4e08b137-aec5-49a4-83c0-38258425f145/section/53838061-eb08-4f46-ace0-e6b15e4bf5bf',
        'source:recovery:reception':'https://ahropenreview.com/HistoryCanBeOpenSource/authors-response/',
        'source:recovery:gallon':'https://dhdebates.gc.cuny.edu/read/untitled/section/fa10e2e1-0c3d-4519-a958-d823aac989eb',
        'source:recovery:putnam':'https://academic.oup.com/ahr/article-abstract/121/2/377/2581842'}
    names = {e['id']:e['label'] for e in entities}
    for s in sources:
        source_proposals.append(dict(id='digital07_'+s['id'].split(':')[-1],
            title=names[s['describes_work']]+' — consulted witness', url=s.get('url') or old_urls[s['id']],
            claim_source_record_id=s['id'], scope_note='Evidence scope and locator remain on each claim citation; this source is not a whole-work verification.'))
    return {'batch.json':b, 'review-actions.json':actions, 'entry-proposals.json':drafts,
            'source-proposals.json':source_proposals,
            'coverage-current.json':coverage, 'summary.json':summary}


def check(outputs):
    b = outputs['batch.json']; r = read(OUT/'research.json')
    errors = validate(b, read(ROOT/'ontology/contract-v0.2.json'), ROOT)
    old = read(ROOT/r['prior_packet'])
    current = {c['id']:c for c in b['claims']}
    for c in old['claims']:
        if c['id'] in r['prior_claim_ids'] and current.get(c['id']) != c:
            errors.append('Prior claim changed: '+c['id'])
    old_entities = {e['id']:e for e in old['entities']}
    annotations = {a['entity_id']:a for a in outputs['review-actions.json']}
    for e in b['entities']:
        if e['id'] in old_entities:
            prior = old_entities[e['id']]
            if e['id'] in annotations:
                if annotations[e['id']]['previous_record'] != prior or any(e.get(k) != v for k,v in prior.items()):
                    errors.append('Prior entity metadata erased: '+e['id'])
            elif e != prior:
                errors.append('Prior entity changed: '+e['id'])
        if e['type'] == 'work' and 'author_ids' in e:
            credits = {c['subject'] for c in b['claims'] if c['predicate']=='authored' and c['object']==e['id']}
            if credits != set(e['author_ids']):
                errors.append('Incomplete authorship: '+e['id'])
    for c in b['claims']:
        if c['review']['status'] != 'needs_review' or c['valid_time'] is not None:
            errors.append('Unexpected acceptance/date inference: '+c['id'])
    for s in b['source_records']:
        p = ROOT/s['snapshot_path']
        expected = s.get('snapshot_sha256', s.get('sha256'))
        if not p.is_file() or sha(p) != expected:
            errors.append('Source capture mismatch: '+s['id'])
    baseline = read(OUT/'baseline.json')
    for name, expected in baseline['files'].items():
        try:
            resolve_baseline(name, expected)
        except ValueError as exc:
            errors.append(str(exc))
    prior_cov = read(COVERAGE)
    source_ids = {s['id'] for s in outputs['source-proposals.json']}
    entity_ids = {e['id'] for e in b['entities']}
    people_ids = {e['id'].split(':',1)[1] for e in b['entities'] if e['type']=='person'}
    for proposal in outputs['entry-proposals.json']:
        n = proposal['node']
        if not set(n['source_ids']) <= source_ids or not set(n['work_ids']) <= entity_ids:
            errors.append('Unresolved draft sources or works: '+n['id'])
        if not {p['person_id'] for p in n['representative_people']} <= people_ids:
            errors.append('Unresolved draft people: '+n['id'])
        for strand in n['strands']:
            years = sorted({current[cid]['intervention_year'] for cid in strand['claim_ids']})
            if strand['intervention_years'] != years:
                errors.append('Strand loses intervention/reception chronology: '+strand['id'])
    if outputs['coverage-current.json']['topics'] != prior_cov['topics']:
        errors.append('Unrelated existing-topic coverage changed')
    for oldrow, newrow in zip(prior_cov['field_candidates'], outputs['coverage-current.json']['field_candidates']):
        if oldrow['original_ledger_row'] != newrow['original_ledger_row']:
            errors.append('Frozen discovery row changed')
        if oldrow['candidate_id'] not in ('digital_history','web_history','digital_humanities') and oldrow != newrow:
            errors.append('Unrelated candidate changed')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build(); errors = check(outputs)
    if args.check:
        for name, data in outputs.items():
            if not (OUT/name).is_file() or (OUT/name).read_text() != serial(data):
                errors.append('Rebuild mismatch: '+name)
        for name, expected in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name) != expected:
                errors.append('Manifest mismatch: '+name)
    elif not errors:
        for name, data in outputs.items():
            (OUT/name).write_text(serial(data))
        files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json']
        files += [Path(__file__).resolve(), ROOT/'tests/test_digital_web_batch.py']
        (OUT/'manifest.json').write_text(serial(dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})))
    print(serial(dict(errors=errors, **outputs['summary.json'])), end='')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
