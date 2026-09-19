#!/usr/bin/env python3
"""Append evidence and bounded proposals to batch 03 without rewriting it."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate

OUT = ROOT/'data/extension-2026/evidence-recovery-04'
BASE = ROOT/'data/extension-2026/earth-indigenous-03'


def read(path):
    return json.loads(path.read_text())


def serialized(value):
    return json.dumps(value, ensure_ascii=False, indent=2)+'\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build(recipe=None):
    recipe=read(OUT/'research.json') if recipe is None else recipe
    original=read(ROOT/recipe['base_packet'])
    batch=deepcopy(original)
    batch['derivation']=dict(base_packet=recipe['base_packet'], base_sha256=digest(ROOT/recipe['base_packet']),
                            operation='additive research overlay; same IDs are not new claims')
    sources={s['id']:s for s in batch['source_records']}
    entities={e['id']:e for e in batch['entities']}
    claims={c['id']:c for c in batch['claims']}
    actions=[]
    for source in recipe['sources']:
        if source['id'] in sources:
            raise ValueError('Source ID collision: '+source['id'])
        path=OUT/source['capture']
        row={k:v for k,v in source.items() if k!='capture'}
        row.update(snapshot_path=str(path.relative_to(ROOT)), snapshot_sha256=digest(path),
            observed_at=recipe['assembled_at'], observation_note='Capture assembly time; retrieval in same local research session.',
            capture_scope='Partial web extraction; only cited paragraphs reviewed')
        batch['source_records'].append(row)
        sources[row['id']]=row
    for entity in recipe['people']+recipe['works']+recipe['concepts']:
        if entity['id'] in entities:
            raise ValueError('Entity ID collision: '+entity['id'])
        row={k:deepcopy(v) for k,v in entity.items() if k not in ('source','credit_locator')}
        batch['entities'].append(row)
        entities[row['id']]=row
    version=dict(id='version:whyte_climate_studies_2017_february', type='version',
        label='Whyte, author-uploaded February 2017 manuscript',
        version_status='author_manuscript_not_collated_with_version_of_record',
        source_record_id='source:recovery04:whyte_draft')
    batch['entities'].append(version)
    entities[version['id']]=version

    def evidence(source, locator, support, limitation, check='passage_checked'):
        return dict(source_record_id=source, locator=locator, support=support, limitation=limitation,
            scope='passage' if check=='passage_checked' else 'metadata', check_status=check,
            checked_on=recipe['cutoff'], support_assessment='supports_bounded_attribution')

    for update in recipe['evidence_updates']:
        claim=claims[update['claim_id']]
        previous=deepcopy(claim)
        ev=evidence(update['source_record_id'],update['locator'],claim['statement'],update['qualification'])
        claim['evidence'].append(ev)
        claim['qualification']=update['qualification']
        claim['history'].append(dict(date=recipe['cutoff'], action='evidence_added', reason=update['reason'],
                                    previous_record_sha256=fingerprint(previous)))
        actions.append(dict(kind='evidence_supplement',claim_id=claim['id'],previous_record=previous,
            previous_record_sha256=fingerprint(previous),added_evidence=ev,review_status_changed=False))
    for review in recipe['metadata_reviews']:
        entity=entities[review['entity_id']]
        previous=deepcopy(entity)
        entity.setdefault('metadata_reviews',[]).append({k:v for k,v in review.items() if k!='entity_id'})
        actions.append(dict(kind='metadata_annotation',entity_id=entity['id'],previous_record=previous,
                            previous_record_sha256=fingerprint(previous),review_status_changed=False))

    for row in recipe['claims']:
        if row['id'] in claims:
            raise ValueError('Claim ID collision: '+row['id'])
        claim={k:deepcopy(v) for k,v in row.items() if k not in ('source_record_id','locator')}
        claim.update(basis='editorial_interpretation',valid_time=None,
            review=dict(status='needs_review',rationale='Scoped source reading; editorial acceptance remains pending.'),
            history=[dict(date=recipe['cutoff'],action='proposed',reason='Evidence recovery and regional review')],
            evidence=[evidence(row['source_record_id'],row['locator'],row['statement'],row['qualification'])])
        batch['claims'].append(claim)
        claims[claim['id']]=claim
    for work in recipe['works']:
        for person in work['author_ids']:
            source=work['source']
            if work['id']=='work:gallini_environment_2009':
                source='source:recovery04:gallini_frontmatter'
            batch['claims'].append(dict(id='claim:recovery04:authored:'+work['id'].split(':',1)[1],
                subject=person,predicate='authored',object=work['id'],attributed_to=source,
                basis='source_assertion',valid_time=None,
                review=dict(status='needs_review',rationale='Named author credit, no external authority accepted.'),
                evidence=[evidence(source,work['credit_locator'],'Named author of this work.',
                    'Credit metadata only; not a demographic assertion.',check='metadata_checked')]))
    batch['claims'].append(dict(id='claim:recovery04:whyte_manuscript_version',subject=version['id'],
        predicate='realizes',object='work:whyte_climate_studies_2017',attributed_to='source:recovery04:whyte_draft',
        basis='source_assertion',valid_time=None,
        review=dict(status='needs_review',rationale='Same author/title; exact textual relation to final publication not collated.'),
        evidence=[evidence('source:recovery04:whyte_draft','Manuscript p. 1; rendered lines 35–49',
            'Author-uploaded manuscript bears this title and forthcoming 2017 ELN notice.',
            'Do not use final publication page numbers for manuscript passages.',check='metadata_checked')]))

    coverage=read(BASE/'coverage-current.json')
    coverage['derived_from']='data/extension-2026/earth-indigenous-03/coverage-current.json'
    coverage['supplement_packet']='data/extension-2026/evidence-recovery-04/batch.json'
    for row in coverage['topics']:
        for w in recipe['works']:
            if row['entry_id'] not in w['field_navigation_ids']:
                continue
            row['new_work_ids'].append(w['id'])
            year=w['publication_year_observation']
            b='2001_2009' if year<=2009 else '2010_2019' if year<=2019 else '2020_cutoff'
            row['research_bins'][b]['work_ids'].append(w['id'])
            row['research_bins'][b]['status']='partial_evidence'
    for row in coverage['field_candidates']:
        for w in recipe['works']:
            if row['candidate_id'] in w['candidate_navigation_ids']:
                row['new_work_ids'].append(w['id'])
                row['disposition']='partial_research_no_field_decision'
    history=[c for c in batch['claims'] if c['predicate'] not in ('authored','realizes')]
    summary=dict(status='staging_only',production_imports=0,new_works=len(recipe['works']),
        new_people=len(recipe['people']),new_historical_proposals=len(recipe['claims']),
        rechecked_existing_claims=len(recipe['evidence_updates']),new_authorship_credits=4,new_version_links=1,
        cumulative_works=sum(e['type']=='work' for e in batch['entities']),cumulative_claims=len(batch['claims']),
        cumulative_historical_proposals=len(history),
        cumulative_historical_claims_with_passage_evidence=sum(any(e['check_status']=='passage_checked' for e in c['evidence']) for c in history),
        current_topics=len(coverage['topics']),candidate_rows=len(coverage['field_candidates']),
        fully_reviewed_fields=0,production_ready=False)
    return {'batch.json':batch,'review-actions.json':actions,'coverage-current.json':coverage,'summary.json':summary}


def check(outputs):
    batch=outputs['batch.json']
    errors=validate(batch,read(ROOT/'ontology/contract-v0.2.json'),ROOT)
    old=read(BASE/'batch.json')
    actions=outputs['review-actions.json']
    mutable={a.get('claim_id') or a.get('entity_id'):a for a in actions}
    for section in ['entities','claims','source_records']:
        now={r['id']:r for r in batch[section]}
        for row in old[section]:
            action=mutable.get(row['id'])
            if action:
                if action['previous_record']!=row or action['previous_record_sha256']!=fingerprint(row):
                    errors.append('Incorrect preserved prior record: '+row['id'])
                current=now.get(row['id'],{})
                allowed={'qualification','evidence','history'} if section=='claims' else {'metadata_reviews'}
                if {k:v for k,v in current.items() if k not in allowed}!={k:v for k,v in row.items() if k not in allowed}:
                    errors.append('Unapproved prior-record change: '+row['id'])
                if section=='claims' and (current.get('evidence',[])[:len(row['evidence'])]!=row['evidence'] or
                    current.get('history',[])[:len(row['history'])]!=row['history']):
                    errors.append('Earlier evidence/history erased: '+row['id'])
            elif now.get(row['id'])!=row:
                errors.append('Prior record altered: '+row['id'])
    for c in batch['claims']:
        if c['review']['status']!='needs_review' or c['valid_time'] is not None:
            errors.append('Unintended acceptance/date inference: '+c['id'])
    versions={e['id'] for e in batch['entities'] if e['type']=='version'}
    for source in batch['source_records']:
        path=ROOT/source['snapshot_path']
        if not path.is_file() or digest(path)!=source['snapshot_sha256']:
            errors.append('Source capture mismatch: '+source['id'])
        if source.get('describes_version') and source['describes_version'] not in versions:
            errors.append('Unknown consulted version: '+source['id'])
    graph=read(ROOT/'historiography-1920-2000.json')
    node_ids={n['id'] for n in graph['nodes']}
    candidate_ids={c['candidate_id'] for c in read(OUT.parent/'field-candidates.json')}
    for entity in batch['entities']:
        if not set(entity.get('field_navigation_ids',[]))<=node_ids:
            errors.append('Unknown field navigation: '+entity['id'])
        if not set(entity.get('candidate_navigation_ids',[]))<=candidate_ids:
            errors.append('Unknown candidate navigation: '+entity['id'])
    for path,sha in read(OUT/'baseline.json')['files'].items():
        if not (ROOT/path).is_file() or digest(ROOT/path)!=sha:
            errors.append('Protected baseline changed: '+path)
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    outputs=build()
    errors=check(outputs)
    if args.check:
        for name,data in outputs.items():
            if not (OUT/name).is_file() or (OUT/name).read_text()!=serialized(data):
                errors.append('Rebuild mismatch: '+name)
        for path,sha in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/path).is_file() or digest(ROOT/path)!=sha:
                errors.append('Manifest mismatch: '+path)
    elif not errors:
        for name,data in outputs.items():
            (OUT/name).write_text(serialized(data))
        paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
        paths += [Path(__file__).resolve(),ROOT/'tests/test_evidence_recovery.py']
        (OUT/'manifest.json').write_text(serialized(dict(files={str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)})))
    print(serialized(dict(errors=errors,**outputs['summary.json'])),end='')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
