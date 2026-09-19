#!/usr/bin/env python3
"""Build or check the bounded environmental/Indigenous extension, offline.

Original research packets and production bytes are pinned, never rewritten.
The coverage view is an index of partial research, not an acceptance adapter.
"""
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

OUT = ROOT / 'data/extension-2026/earth-indigenous-03'
GRAPH = ROOT / 'historiography-1920-2000.json'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialized(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def build():
    research = read(OUT / 'research.json')
    graph = read(GRAPH)
    people = {p['id']: p for p in graph['people']}
    works = {w['id']: w for w in research['works']}
    sources = {s['id']: s for s in research['sources']}
    batch = dict(schema_version='0.2', fixture_only=True, status='staging_only',
                 production_graph_imports=0, research_cutoff=research['cutoff'],
                 entities=[], source_records=[], claims=[], identity_mappings=[])
    for p in research['people']:
        entity = dict(id='person:'+p['id'], type='person', label=p['label'],
                      identity_status=p['identity_status'], gender=p['gender'])
        if p['reuse_legacy']:
            assert people[p['id']]['label'] == p['label'], 'Legacy person mismatch'
            entity['legacy_person_id'] = p['id']
        else:
            assert p['id'] not in people, 'Candidate collides with production identity'
        batch['entities'].append(entity)
    for w in research['works']:
        batch['entities'].append(dict(id='work:'+w['id'], type='work', label=w['title'],
            identity_status='local_work_proposal', author_ids=['person:'+p for p in w['authors']],
            publication_year_observation=w['year'], date_note=w['date_note'],
            field_navigation_ids=w['entry_ids'], candidate_navigation_ids=w['candidate_ids']))
    for c in research['concepts']:
        batch['entities'].append(dict(id='concept:earth:'+c['id'], type='concept', label=c['label'],
            concept_kind=['topic'], classification_status='provisional',
            field_navigation_ids=c['entry_ids'], candidate_navigation_ids=c['candidate_ids']))
    for s in sources.values():
        path = OUT / s['capture']
        batch['source_records'].append(dict(id='source:earth:'+s['id'], provider=s['provider'],
            url=s['url'], snapshot_path=str(path.relative_to(ROOT)), snapshot_sha256=digest(path),
            observed_at=research['observed_at'], capture_scope='Partial web extraction; only cited sections reviewed'))

    def evidence(work, locator=None, metadata=False):
        check = 'metadata_checked' if metadata else work['check']
        scope = {'passage_checked':'passage', 'abstract_checked':'abstract'}.get(check, 'metadata')
        return dict(source_record_id='source:earth:'+work['source'], locator=locator or work['locator'],
                    scope=scope, check_status=check, checked_on=research['cutoff'],
                    support_assessment='supports_bounded_attribution',
                    limitation='Only indicated evidence reviewed; no whole-work reading or wider reception inferred.')

    for row in research['claims']:
        work = works[row['work']]
        ev = evidence(work, row['locator'])
        ev.update(support=row['statement'], limitation=row['qualification'])
        batch['claims'].append(dict(id='claim:earth:'+row['id'], subject=row['subject'],
            predicate=row['predicate'], object=row['object'], statement=row['statement'],
            attributed_to='work:'+work['id'], basis='editorial_interpretation',
            qualification=row['qualification'], intervention_year=work['year'], valid_time=None,
            review=dict(status='needs_review', rationale='Bounded research proposal; editorial acceptance pending.'),
            history=[dict(date=research['cutoff'], action='proposed', reason='Post-2000 extension research')],
            evidence=[ev]))
    for work in works.values():
        for person in work['authors']:
            ev = evidence(work, metadata=True)
            ev['support'] = 'Named author credit for this work, not for other publications.'
            ev['locator'] = {
                'rose_2004':'Publisher lines 12–17',
                'cruikshank_2005':'Publisher lines 53–56',
                'morrison_2015':'Printed p. 75 byline; rendered lines 57–63',
                'davis_todd_2017':'ACME publisher Authors section; PDF p. 761 byline',
                'sivasundaram_2024':'Publisher lines 437–447',
                'kearns_2025':'Article byline, rendered lines 112–118'
            }[work['id']]
            # Publisher page supplies bibliographic credit; sample introduction has no title page.
            if work['id'] == 'cruikshank_2005':
                ev.update(source_record_id='source:earth:cruikshank_metadata', locator='Publisher lines 53–56')
            batch['claims'].append(dict(id='claim:earth:authored:'+person+':'+work['id'],
                subject='person:'+person, predicate='authored', object='work:'+work['id'],
                attributed_to=ev['source_record_id'], basis='source_assertion', valid_time=None,
                review=dict(status='needs_review', rationale='Local author credit; external authority match not accepted.'),
                evidence=[ev]))

    original = read(OUT.parent/'existing-topics.json')
    old = {r['entry_id']:r for r in original}
    dossiers = read(OUT.parent/'breadth-01/field-dossiers.json')
    surveys = read(OUT.parent/'breadth-01/survey-selection.json')
    coverage = dict(research_cutoff=research['cutoff'], graph_revision='1.120',
        original_topic_count=len(original), topics=[], field_candidates=[],
        interpretation='Navigation to research only. Partial evidence never completes a field review.')
    bins = ['2001_2009','2010_2019','2020_cutoff']
    for node in graph['nodes']:
        if node['entry_kind'] != 'group':
            continue
        row = dict(entry_id=node['id'], label=node['label'],
            original_ledger_row=deepcopy(old.get(node['id'])),
            current_scope_note=node.get('scope_note'),
            earlier_packet_links=[], new_work_ids=[], review_outcome='pending', reviewed_through=None,
            research_bins={b:dict(status='not_researched', work_ids=[]) for b in bins})
        if node['id'] in old:
            for b in bins:
                row['research_bins'][b]['status'] = old[node['id']][b]
        for d in dossiers:
            if d.get('existing_entry_id') == node['id']:
                row['earlier_packet_links'].append('data/extension-2026/breadth-01/dossiers/'+d['id']+'.md')
                for survey in surveys:
                    if survey['field_id'] == d['id']:
                        b = bins[0] if survey['year']<=2009 else bins[1] if survey['year']<=2019 else bins[2]
                        row['research_bins'][b]['status'] = 'partial_evidence'
                        row['research_bins'][b]['work_ids'].append('work:'+survey['id'])
        if node['id'] in ('gender','racial_formation','intersectionality'):
            row['scope_reconciliation'] = 'Revision 1.120 scope; old combined gender research is not automatically inherited.'
        for w in works.values():
            if node['id'] not in w['entry_ids']:
                continue
            row['new_work_ids'].append('work:'+w['id'])
            b = bins[0] if w['year']<=2009 else bins[1] if w['year']<=2019 else bins[2]
            row['research_bins'][b]['status'] = 'partial_evidence'
            row['research_bins'][b]['work_ids'].append('work:'+w['id'])
        row['next_action'] = ('Broader field survey, independent reception and regional/language review; see packet README.'
            if row['new_work_ids'] else 'Continue explicit period-by-period review; prior packets remain partial.')
        coverage['topics'].append(row)
    for candidate in read(OUT.parent/'field-candidates.json'):
        cid = candidate['candidate_id']
        selected = ['work:'+w['id'] for w in works.values() if cid in w['candidate_ids']]
        earlier=['data/extension-2026/breadth-01/dossiers/'+d['id']+'.md'
                 for d in dossiers if cid in d['candidate_ledger_ids']]
        coverage['field_candidates'].append(dict(candidate_id=cid,
            original_ledger_row=deepcopy(candidate), new_work_ids=selected,
            earlier_packet_links=earlier,
            disposition='partial_research_no_field_decision' if selected or earlier else 'pending',
            production_ready=False))
    footprint=[]
    for p in research['people']:
        pid = p['id']
        footprint.append(dict(person_id=pid, label=p['label'], identity_status=p['identity_status'],
            gender=p['gender'], full_node_id=people.get(pid,{}).get('node_id'),
            existing_roster_entry_ids=[n['id'] for n in graph['nodes']
                if any(x['person_id']==pid for x in n.get('representative_people',[]))],
            authorship_claim_ids=[c['id'] for c in batch['claims'] if c['subject']=='person:'+pid and c['predicate']=='authored'],
            substantive_claim_ids=[c['id'] for c in batch['claims'] if c['predicate']!='authored' and
                (c['subject']=='person:'+pid or c['subject'] in {'work:'+w['id'] for w in works.values() if pid in w['authors']})]))
    summary=dict(status='staging_only', production_imports=0, works=len(works), people=len(footprint),
        reused_people=sum(p['reuse_legacy'] for p in research['people']),
        historical_proposals=len(research['claims']), authorship_credits=len(batch['claims'])-len(research['claims']),
        historical_evidence_checks=dict(Counter(c['evidence'][0]['check_status'] for c in batch['claims'] if c['predicate']!='authored')),
        current_topics=len(coverage['topics']), candidate_rows=len(coverage['field_candidates']),
        fully_reviewed_fields=0, production_ready=False)
    return {'batch.json':batch, 'coverage-current.json':coverage, 'people-review.json':footprint, 'summary.json':summary}


def check(outputs):
    errors = validate(outputs['batch.json'], read(ROOT/'ontology/contract-v0.2.json'), ROOT)
    graph = read(GRAPH)
    ids = {n['id'] for n in graph['nodes']}
    candidates = {r['candidate_id'] for r in read(OUT.parent/'field-candidates.json')}
    for entity in outputs['batch.json']['entities']:
        if not set(entity.get('field_navigation_ids',[])) <= ids:
            errors.append('Unknown field navigation: '+entity['id'])
        if not set(entity.get('candidate_navigation_ids',[])) <= candidates:
            errors.append('Unknown candidate navigation: '+entity['id'])
    for path, expected in read(OUT/'baseline.json')['files'].items():
        # Fable owns a concurrent website rebuild. Keep the observation, but
        # do not treat another session's asset edits as this data batch failing.
        if path.startswith(('site/', 'docs/')):
            continue
        if not (ROOT/path).is_file() or digest(ROOT/path) != expected:
            errors.append('Protected baseline changed: '+path)
    for c in outputs['batch.json']['claims']:
        if c['review']['status'] != 'needs_review' or c['valid_time'] is not None:
            errors.append('Unexpected acceptance or inferred historical validity: '+c['id'])
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check saved outputs and pinned bytes without writing')
    args=parser.parse_args()
    outputs=build()
    errors=check(outputs)
    if args.check:
        for name,value in outputs.items():
            if not (OUT/name).exists() or (OUT/name).read_text()!=serialized(value):
                errors.append('Rebuild mismatch: '+name)
        for path,expected in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/path).is_file() or digest(ROOT/path)!=expected:
                errors.append('Packet manifest mismatch: '+path)
    elif not errors:
        for name,value in outputs.items():
            (OUT/name).write_text(serialized(value))
        paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
        paths += [Path(__file__).resolve(), ROOT/'tests/test_earth_indigenous_batch.py']
        (OUT/'manifest.json').write_text(serialized(dict(files={str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)})))
    external_changes=[p for p,h in read(OUT/'baseline.json')['files'].items()
        if p.startswith(('site/','docs/')) and (not (ROOT/p).is_file() or digest(ROOT/p)!=h)]
    print(serialized(dict(errors=errors, concurrent_asset_changes=external_changes,
                          **outputs['summary.json'])), end='')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
