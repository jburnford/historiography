#!/usr/bin/env python3
"""Reproduce the bounded transnational/mobility packet without production writes."""
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

OUT = ROOT / 'data/extension-2026/transnational-mobility-09'
COVERAGE = ROOT / 'data/extension-2026/borderlands-disability-08/coverage-current.json'
FIELDS = ('transnational',)


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(recipe=None):
    r = read(OUT / 'research.json') if recipe is None else recipe
    old = read(ROOT / r['prior_packet'])
    claims = [deepcopy(c) for c in old['claims'] if c['id'] in r['prior_claim_ids']]
    if len(claims) != len(r['prior_claim_ids']):
        raise ValueError('Missing or duplicate inherited claim')
    source_ids = {ev['source_record_id'] for c in claims for ev in c['evidence']}
    sources = [deepcopy(s) for s in old['source_records'] if s['id'] in source_ids]
    entity_ids = {c[k] for c in claims for k in ('subject', 'object', 'attributed_to')}
    entities = [deepcopy(e) for e in old['entities'] if e['id'] in entity_ids]
    actions = []
    for a in r['prior_work_annotations']:
        e = next(e for e in entities if e['id'] == a['work_id'])
        actions.append(dict(entity_id=e['id'], previous_record=deepcopy(e),
                            action='Add explicit authors, publication year and navigation; retain older claim unchanged.',
                            source_record_id=a['source']))
        e.update({k: deepcopy(a[k]) for k in ('author_ids', 'publication_year_observation', 'candidate_navigation_ids', 'roster_eligible')})
        for key in ('attribution_note', 'publication_note'):
            if key in a:
                e[key] = deepcopy(a[key])
    for s in r['sources']:
        path = OUT / s['capture']
        sources.append({**{k:v for k,v in s.items() if k != 'capture'},
                        'snapshot_path': str(path.relative_to(ROOT)), 'snapshot_sha256': sha(path),
                        'observed_at': r['assembled_at'], 'observation_note': 'Packet assembly timestamp; selected reading scope on each citation.'})
    for e in r['people'] + r['works'] + r['versions'] + r['concepts']:
        entities.append({k:deepcopy(v) for k,v in e.items() if k not in ('source', 'credit_locator')})

    def add(row, source, locator, status, support, limit, basis):
        row.update(basis=basis, valid_time=None,
                   review=dict(status='needs_review', rationale='Bounded research proposal; field and production acceptance remain pending.'),
                   history=[dict(date=r['cutoff'], action='proposed', reason='Transnational/mobility continuation and contributor review')],
                   evidence=[dict(source_record_id=source, locator=locator, check_status=status,
                                  scope={'passage_checked':'passage','abstract_checked':'abstract','metadata_checked':'metadata'}[status],
                                  support=support, limitation=limit, checked_on=r['cutoff'],
                                  support_assessment='supports_bounded_attribution')])
        claims.append(row)

    for c in r['claims']:
        row = {k:deepcopy(v) for k,v in c.items() if k not in ('source_record_id','locator','check_status')}
        add(row, c['source_record_id'], c['locator'], c['check_status'], c['statement'], c['qualification'], 'editorial_interpretation')
    for w in r['works'] + [dict(a, id=a['work_id']) for a in r['prior_work_annotations']]:
        for pid in w['author_ids']:
            add(dict(id='claim:transmob09:authored:'+w['id'].split(':',1)[1]+':'+pid.split(':',1)[1],
                     subject=pid, predicate='authored', object=w['id'], attributed_to=w['source']),
                w['source'], w['credit_locator'], 'metadata_checked', 'Named author of this specific work.',
                'Authorship only; contributors to a translation or other chapters are not automatically coauthors.', 'source_assertion')
    for v in r['versions']:
        add(dict(id='claim:transmob09:realizes:'+v['id'].split(':')[-1], subject=v['id'],
                 predicate='realizes', object=v['work_id'], attributed_to=v['source_record_id']),
            v['source_record_id'], v['credit_locator'], 'metadata_checked',
            v['label'], v['version_note'], 'source_assertion')
        for citation in v.get('additional_metadata_evidence', []):
            claims[-1]['evidence'].append(dict(
                source_record_id=citation['source_record_id'], locator=citation['locator'],
                check_status='metadata_checked', scope='metadata', support=citation['support'],
                limitation='Version metadata only; no first-publication or translator inference.',
                checked_on=r['cutoff'], support_assessment='supports_bounded_attribution'))
    batch = dict(schema_version='0.2', fixture_only=True, status='staging_only', production_graph_imports=0,
                 research_cutoff=r['cutoff'], entities=entities, claims=claims, source_records=sources,
                 derivation=dict(prior_packet=r['prior_packet'], prior_claim_ids=r['prior_claim_ids'],
                                 note='Two inherited works/claims overlap breadth-01; not additional unique discoveries.'))
    historical = [c for c in claims if c['predicate'] not in ('authored','realizes')]
    works = [e for e in entities if e['type'] == 'work']
    people = {e['id']:e for e in entities if e['type'] == 'person'}
    mapping = {s['id']: 'transmob09_' + s['id'].split(':')[-1] for s in sources}
    source_proposals = [dict(id=mapping[s['id']], title=next(w['label'] for w in works if w['id']==s['describes_work'])+' — consulted witness',
                             url=s['url'], claim_source_record_id=s['id'],
                             scope_note='Read only the cited passages/abstract or metadata; citation joins retain their limits.') for s in sources]
    drafts = []
    for field in FIELDS:
        ws = [w for w in works if field in w['candidate_navigation_ids']]
        roster, strands = {}, []
        for w in ws:
            cs = [c for c in historical if c['subject'] == w['id']]
            sids = list(dict.fromkeys(mapping[ev['source_record_id']] for c in cs for ev in c['evidence']))
            for pid in (w['author_ids'] if w.get('roster_eligible', True) else []):
                roster[pid] = dict(person_id=pid.split(':',1)[1], role='contributor',
                                   context='Author of the selected work; contextual contribution, not a claim of founding, influence or an exclusive profession.',
                                   works=w['label'], source_ids=sids, basis='source_review')
            strands.append(dict(id='transmob09_'+w['id'].split(':',1)[1], title=w['label'],
                                focus=' '.join(c['statement']+' '+c['qualification'] for c in cs),
                                person_ids=[p.split(':',1)[1] for p in w['author_ids']] if w.get('roster_eligible', True) else [], works=w['label'],
                                attribution_note=w.get('attribution_note', 'Work-level attribution; evidence limits retained.'),
                                work_ids=[w['id']], claim_ids=[c['id'] for c in cs], source_ids=sids,
                                work_publication_year=w['publication_year_observation'],
                                intervention_years=sorted({c['intervention_year'] for c in cs}),
                                basis='editorial_distinction', review_status='needs_review'))
        scope = r['entry_scopes'][field]
        years = sorted({y for s in strands for y in s['intervention_years']})
        node = dict(id=field, **scope, entry_kind='group', entry_type='Method or approach',
                    layer='historiographical_developments', period=None, hunt_core_paradigm=False,
                    date_label=f'Earlier roots unresolved · selected interventions {years[0]}–{years[-1]}',
                    representative_people=list(roster.values()), strands=strands,
                    representative_figures_and_works='; '.join(w['label'] for w in ws),
                    work_ids=[w['id'] for w in ws], claim_ids=[cid for s in strands for cid in s['claim_ids']],
                    source_ids=list(dict.fromkeys(sid for s in strands for sid in s['source_ids'])))
        drafts.append(dict(candidate_id=field, status='needs_review', proposed_disposition='separate_entry',
                           node=node, production_import=False, acceptance_requirements=[
                               'Review earlier roots, regional coverage and exact field boundaries',
                               'Reconcile identities and map claims/sources in a production adapter',
                               'Preserve revision, translation, online-posting and intervention chronology',
                               'Do not treat the separate-entry proposal as a completed field review']))
    coverage = deepcopy(read(COVERAGE))
    coverage.update(research_cutoff=r['cutoff'], graph_revision='1.122',
                    derived_from=str(COVERAGE.relative_to(ROOT)), supplement_packet=str((OUT/'batch.json').relative_to(ROOT)))
    for row in coverage['field_candidates']:
        if row['candidate_id'] not in FIELDS:
            continue
        ws = [w for w in works if row['candidate_id'] in w['candidate_navigation_ids']]
        row.update(disposition='separate_entry_draft_pending_review', production_ready=False,
                   new_work_ids=list(dict.fromkeys(row['new_work_ids']+[w['id'] for w in ws])),
                   research_bins={k:dict(status='not_researched', work_ids=[]) for k in ('2001_2009','2010_2019','2020_cutoff')})
        for w in ws:
            # Bin witnessed interventions, keeping the work's original publication date separate.
            for y in {c['intervention_year'] for c in historical if c['subject'] == w['id']}:
                key = '2001_2009' if y < 2010 else '2010_2019' if y < 2020 else '2020_cutoff'
                row['research_bins'][key]['status'] = 'partial_evidence'
                row['research_bins'][key]['work_ids'].append(w['id'])
        row['research_bin_note'] = 'Bins date witnessed interventions; descriptions are leads, and versions do not establish an argument origin.'
    summary = dict(status='staging_only', new_works=len(r['works']), reused_works=len(r['prior_work_annotations']),
                   works_total=len(works), new_historical_claims=len(r['claims']), reused_historical_claims=len(r['prior_claim_ids']),
                   historical_claims=len(historical), evidence_scopes=dict(Counter(c['evidence'][0]['check_status'] for c in historical)),
                   author_credits=sum(c['predicate']=='authored' for c in claims), version_links=len(r['versions']),
                   people=len(people), credited_authors=len({c['subject'] for c in claims if c['predicate']=='authored'}),
                   claims_total=len(claims), entry_drafts=len(drafts), fully_reviewed_fields=0, production_imports=0)
    return {'batch.json':batch,'review-actions.json':actions,'source-proposals.json':source_proposals,
            'entry-proposals.json':drafts,'coverage-current.json':coverage,'summary.json':summary,'boundary-review.json':deepcopy(r['boundary_review'])}


def check(outputs):
    r = read(OUT/'research.json'); b = outputs['batch.json']
    errors = validate(b, read(ROOT/'ontology/contract-v0.2.json'), ROOT)
    old = read(ROOT/r['prior_packet'])
    claims = {c['id']:c for c in b['claims']}; entities = {e['id']:e for e in b['entities']}
    for c in old['claims']:
        if c['id'] in r['prior_claim_ids'] and claims.get(c['id']) != c:
            errors.append('Inherited claim changed: '+c['id'])
    for action in outputs['review-actions.json']:
        original = next(e for e in old['entities'] if e['id']==action['entity_id'])
        if action['previous_record'] != original or any(entities[original['id']].get(k)!=v for k,v in original.items()):
            errors.append('Inherited work metadata lost: '+original['id'])
    for e in b['entities']:
        if e['type']=='work' and {c['subject'] for c in b['claims'] if c['predicate']=='authored' and c['object']==e['id']} != set(e['author_ids']):
            errors.append('Incomplete authorship: '+e['id'])
        for credit in e.get('contributor_credits', []):
            if entities.get(credit['person_id'],{}).get('type') != 'person':
                errors.append('Unresolved translation credit')
    for c in b['claims']:
        if c['review']['status']!='needs_review' or c['valid_time'] is not None:
            errors.append('Unreviewed acceptance or temporal inference: '+c['id'])
        version = entities.get(c.get('consulted_version_id'))
        if version and version.get('work_id') != c['subject']:
            errors.append('Wrong consulted version: '+c['id'])
    for s in b['source_records']:
        if sha(ROOT/s['snapshot_path']) != s.get('snapshot_sha256',s.get('sha256')):
            errors.append('Capture hash mismatch: '+s['id'])
    for name, expected in read(OUT/'baseline.json')['files'].items():
        path = ROOT/name
        if name=='historiography-1920-2000.json' and sha(path)!=expected:
            path=ROOT/'drafts/historiography-1920-2000.v1.122.json'
        if not path.is_file() or sha(path)!=expected:
            errors.append('Protected input changed: '+name)
    prior = read(COVERAGE); current=outputs['coverage-current.json']
    if prior['topics'] != current['topics']:
        errors.append('Unrelated existing-topic coverage changed')
    if len(prior['field_candidates'])!=len(current['field_candidates']):
        errors.append('Discovery candidates lost')
    for a,z in zip(prior['field_candidates'],current['field_candidates']):
        if a['original_ledger_row']!=z['original_ledger_row'] or (a['candidate_id'] not in FIELDS and a!=z):
            errors.append('Unrelated or original discovery row changed: '+a['candidate_id'])
    source_ids = {s['id'] for s in outputs['source-proposals.json']}
    for d in outputs['entry-proposals.json']:
        n=d['node']
        if not set(n['source_ids'])<=source_ids or not set(n['work_ids'])<=set(entities):
            errors.append('Unresolved draft sources/works: '+n['id'])
        for strand in n['strands']:
            years=sorted({claims[cid]['intervention_year'] for cid in strand['claim_ids']})
            if strand['intervention_years']!=years:
                errors.append('Lost intervention chronology: '+strand['id'])
            if any('person:'+pid not in entities for pid in strand['person_ids']):
                errors.append('Unresolved draft person: '+strand['id'])
    if b.get('status') != 'staging_only' or b.get('production_graph_imports') != 0:
        errors.append('Unreviewed production admission')
    if outputs['boundary-review.json'] != r['boundary_review']:
        errors.append('Boundary decision changed without research recipe')
    for expected in r['claims']:
        actual = claims.get(expected['id'], {})
        if any(actual.get(k) != expected[k] for k in ('subject','object','statement','qualification','intervention_year')) or actual.get('evidence', [{}])[0].get('check_status') != expected['check_status']:
            errors.append('Evidence scope or attribution drift: '+expected['id'])
    for d in outputs['entry-proposals.json']:
        if d['production_import'] or d['status'] != 'needs_review':
            errors.append('Unreviewed entry acceptance')
        for strand in d['node']['strands']:
            work = entities[strand['work_ids'][0]]
            if strand['work_publication_year'] != work['publication_year_observation']:
                errors.append('Lost work/version chronology: '+strand['id'])
            if not work.get('roster_eligible', True) and strand['person_ids']:
                errors.append('Unread contributors promoted to argument roster')
        disallowed = {pid.split(':',1)[1] for w in entities.values() if w['type']=='work' and not w.get('roster_eligible', True) for pid in w['author_ids']}
        if any(p['person_id'] in disallowed for p in d['node']['representative_people']):
            errors.append('Unread contributors promoted to argument roster')
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--check',action='store_true'); args=p.parse_args()
    outputs=build(); errors=check(outputs)
    if args.check:
        for name,value in outputs.items():
            if not (OUT/name).exists() or (OUT/name).read_text()!=serial(value): errors.append('Rebuild mismatch: '+name)
        for name,digest in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name)!=digest: errors.append('Manifest mismatch: '+name)
    elif not errors:
        for name,value in outputs.items(): (OUT/name).write_text(serial(value))
        files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
        files += [Path(__file__).resolve(),ROOT/'tests/test_transnational_mobility_batch.py']
        (OUT/'manifest.json').write_text(serial(dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})))
    print(serial(dict(errors=errors,**outputs['summary.json'])),end='')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
