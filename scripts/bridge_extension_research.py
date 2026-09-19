#!/usr/bin/env python3
"""Lossless staging adapter for the two original research packets.

Consulted witnesses become source records. No issued publication is invented.
Discovery-only rows remain tasks; their complete inputs are retained.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate

DATA = ROOT / 'data/extension-2026'
OUT = DATA / 'breadth-01'
PREDICATES = {'critique': 'critiques', 'revision': 'revises',
    'contribution': 'contributes_to', 'qualification': 'qualifies',
    'boundary_assessment': 'assesses_scope', 'programme': 'proposes_programme',
    'field_definition': 'defines_scope'}


def read(p):
    return json.loads(p.read_text())


def build():
    graph = read(ROOT / 'historiography-1920-2000.json')
    people = {p['id']: p for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    candidates = {r['candidate_id']: r for r in read(DATA / 'field-candidates.json')}
    data = dict(schema_version='0.2', fixture_only=True, status='staging_only',
        production_graph_imports=0, entities=[], source_records=[], claims=[],
        discovery_tasks=[], input_packets=[])
    entities = {}

    def entity(id, label, type, **extra):
        entities.setdefault(id, dict(id=id, label=label, type=type, **extra))
        return id

    def reference(ref):
        kind = ref['kind']
        if kind == 'person':
            p = people[ref['id']]
            return entity('person:'+p['id'], p['label'], 'person', legacy_id=p['id'])
        if kind == 'work':
            return 'work:'+ref['id']
        if kind == 'candidate':
            r = candidates[ref['id']]
            # Concept identity is provisional; field admission remains a different decision.
            return entity('candidate-concept:'+ref['id'], r['label'], 'concept',
                concept_kind=['topic'], candidate_ledger_id=ref['id'],
                classification_note='Provisional referent of an attributed claim, not an accepted field classification.')
        if kind == 'strand':
            node = nodes[ref['entry_id']]
            strand = next(s for s in node['strands'] if s['id'] == ref['strand_id'])
            return entity('strand:'+ref['entry_id']+'/'+ref['strand_id'], strand['title'],
                'concept', concept_kind=['topic'], legacy_address=copy.deepcopy(ref))
        raise ValueError('Unsupported endpoint; manual scope review required: '+str(ref))

    for name in ['pilot-evidence.json', 'capitalism-evidence.json']:
        packet = read(DATA/name)
        data['input_packets'].append(dict(path=str((DATA/name).relative_to(ROOT)),
            sha256=hashlib.sha256((DATA/name).read_bytes()).hexdigest()))
        for work in packet['works']:
            entity('work:'+work['id'], work['title'], 'work', legacy_research_id=work['id'],
                input_record=copy.deepcopy(work), identity_status='unreviewed_work_proposal')
        publications = {r['id']: r for r in packet['publications']}
        for pub in publications.values():
            data['source_records'].append(dict(id='source:witness:'+pub['id'],
                provider='Preserved research witness; original provider and access scope in input_record',
                snapshot_path=str((DATA/name).relative_to(ROOT)),
                observed_at='2026-09-18T00:00:00+00:00',
                observation_time_precision='day; original check date, not invented endpoint retrieval time',
                describes_work='work:'+pub['work_id'], input_record=copy.deepcopy(pub),
                witness_identity_note='Consulted HTML/PDF metadata, distinct from an issued publication; original captures/paths/hashes preserved.'))
        for original in packet['claims']:
            citations = [copy.deepcopy(e) for e in packet['citations'] if e['claim_id'] == original['id']]
            if original['kind'] in ('field_discovery', 'programme_lead'):
                data['discovery_tasks'].append(dict(id='task:'+original['id'],
                    input_claim=copy.deepcopy(original), input_citations=citations,
                    disposition='research_lead_not_historical_assertion'))
                continue
            evidence=[]
            for e in citations:
                evidence.append(dict(source_record_id='source:witness:'+e['publication_id'],
                    locator=e['locator'], scope={'passage_checked':'passage','abstract_checked':'abstract','metadata_checked':'metadata'}[e['check_status']],
                    support=original['statement'], check_status=e['check_status'], checked_on=e['checked_on'],
                    limitation=e['limitation'], support_assessment=e['support_assessment'],
                    input_citation=copy.deepcopy(e)))
            data['claims'].append(dict(id='claim:extension:'+original['id'],
                subject=reference(original['actor']), predicate=PREDICATES[original['kind']],
                object=reference(original['target']), statement=original['statement'],
                attributed_to=reference(original['actor']), basis='editorial_interpretation',
                qualification='Attribution and target scope are limited to the preserved statement and its citation-specific evidence.',
                intervention_year=original['intervention_year'], valid_time=None,
                review=dict(status='needs_review', rationale='Format adaptation preserves a research proposal; no fresh scholarly acceptance.'),
                evidence=evidence, history=copy.deepcopy(original['history']), input_claim=copy.deepcopy(original)))
    data['entities']=list(entities.values())
    errors=validate(data,read(ROOT/'ontology/contract-v0.2.json'),ROOT)
    if errors: raise ValueError('\n'.join(errors))
    return data


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    data=build()
    (OUT/'legacy-bridge.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(data["claims"])} claims; {len(data["discovery_tasks"])} discovery tasks; no production imports')
