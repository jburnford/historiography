"""Validate the bounded production claim catalogue without weakening staging rules."""
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ontology.validate_research import validate as validate_research


def validate_catalogue(catalogue, graph):
    errors=[]
    if catalogue.get('schema_version')!='1.0' or catalogue.get('vocabulary_version')!='0.2':
        errors.append('Unknown production claim catalogue version')
    if catalogue.get('status')!='production' or catalogue.get('fixture_only') is not False:
        errors.append('Production claim catalogue cannot be a staging fixture')
    # Reuse the research vocabulary's evidence/type checks on a validation copy.
    # This is not an export path from a fixture: production acceptance is explicit.
    checking=copy.deepcopy(catalogue)
    checking.update(schema_version='0.2',status='staging_only',fixture_only=True)
    errors.extend(validate_research(checking,json.loads((ROOT/'ontology/contract-v0.2.json').read_text()),ROOT))
    nodes={n['id']:n for n in graph['nodes']}
    people={p['id']:p for p in graph.get('people',[])}
    entities={e['id']:e for e in catalogue['entities']}
    claims={c['id']:c for c in catalogue['claims']}
    for entity in entities.values():
        pid=entity.get('legacy_person_id')
        if pid and (pid not in people or people[pid]['label']!=entity['label']):
            errors.append('Claim person does not match shared identity: '+entity['id'])
        nid=entity.get('node_id')
        if nid and nid not in nodes:
            errors.append('Claim presentation has no node: '+entity['id'])
        address=entity.get('legacy_strand_address')
        if address:
            parent,_,strand=address.partition('/')
            if parent not in nodes or strand not in {s['id'] for s in nodes[parent].get('strands',[])}:
                errors.append('Unknown compound strand: '+address)
        if entity['type']=='work':
            credits={c['subject'] for c in claims.values() if c['predicate']=='authored' and c['object']==entity['id']}
            if credits!=set(entity.get('author_ids',[])):
                errors.append('Incomplete authorship for '+entity['id'])
    for source in catalogue['source_records']:
        if source.get('url') and not source['url'].startswith(('https://','http://')):
            errors.append('Unsafe claim source URL')
        if 'verification' in source or 'check_status' in source:
            errors.append('Check status must remain on the citation join')
    for edge in graph['edges']:
        if not edge.get('claim_ids'):
            continue
        linked=[claims.get(cid) for cid in edge['claim_ids']]
        if any(c is None for c in linked):
            errors.append('Unknown edge claim: '+edge['id'])
            continue
        status='accepted' if all(c['review']['status']=='accepted' for c in linked) else 'needs_review'
        if edge.get('review_status')!=status:
            errors.append('Edge review status disagrees with claim: '+edge['id'])
        if status!='accepted' and 'provisional' not in edge['relationship'].lower():
            errors.append('Provisional connection must be labelled: '+edge['id'])
        projection=edge.get('claim_projection',{})
        if len(linked)!=1 or (projection.get('subject'),projection.get('object'))!=(linked[0]['subject'],linked[0]['object']):
            errors.append('Edge loses exact claim endpoints: '+edge['id'])
        strand=edge.get('target_strand')
        if strand and (not strand.startswith(edge['target']+'/') or
                       entities[linked[0]['object']].get('legacy_strand_address')!=strand):
            errors.append('Edge loses strand qualification: '+edge['id'])
    for node in graph['nodes']:
        if any(w not in entities or entities[w]['type']!='work' for w in node.get('work_ids',[])):
            errors.append('Unknown node work: '+node['id'])
        if any(cid not in claims for cid in node.get('claim_ids',[])):
            errors.append('Unknown node claim: '+node['id'])
    return errors
