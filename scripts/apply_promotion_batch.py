#!/usr/bin/env python3
"""Apply the explicitly authorized, bounded promotion batch as revision 1.119."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

PACKET = ROOT/'data/extension-2026/promotions-01'
OUT = ROOT/'data/production-batches/promotions-01'
BASELINE = 'drafts/historiography-1920-2000.v1.118.json'
DAY = '2026-09-18'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(before, batch, proposals):
    graph = copy.deepcopy(before)
    if before['revision_history'][-1]['version'] != '1.118':
        raise ValueError('Requires the reviewed 1.118 baseline')
    catalogue = copy.deepcopy(batch)
    catalogue['schema_version'] = '1.0'
    catalogue['vocabulary_version'] = '0.2'
    catalogue['status'] = 'production'
    catalogue['fixture_only'] = False
    catalogue.pop('production_graph_imports', None)
    catalogue['acceptance_record'] = 'data/production-batches/promotions-01/acceptance.json'
    catalogue['scope'] = 'Bounded claims from the first promotion batch; not a migration or re-verification of older relationships.'
    catalogue['interpretation_note'] = 'Teaching connections are qualified views of these claims. Count a claim once, not once per view or coauthor. Pending claims are explicitly provisional.'
    for c in catalogue['claims']:
        provisional = c['id'] == 'claim:promotions01:davis_biography'
        c['review'] = {
            'status': 'needs_review' if provisional else 'accepted', 'reviewer': 'Codex editorial review',
            'reviewed_on': DAY,
            'rationale': ('Published as a provisional, description-supported connection; body-text verification remains open.' if provisional else
                          'Accepted within its stated evidence scope after the user explicitly requested production integration. Acceptance does not upgrade the citation check.')}
        c['history'].append({'on':DAY, 'status':c['review']['status'], 'action':c['review']['rationale'], 'revision':'1.119'})
    for e in catalogue['entities']:
        if e['type'] == 'atlas_entry':
            e['node_id'] = e.pop('proposed_node_id')
    graph['claim_catalogue'] = catalogue
    witness_sources = {}
    added_sources = []
    work_by_id = {e['id']:e for e in catalogue['entities'] if e['type']=='work'}
    for s in catalogue['source_records']:
        key=s['id'].split(':')[-1]
        sid='promotion01_'+key
        witness_sources[s['id']]=sid
        work=work_by_id[s['describes_work']]
        added_sources.append({'id':sid,'title':work['label']+' — consulted witness',
                              'url':s['url'], 'citation':work['label']+f" ({work['first_publication_year']}); {s['provider']}.",
                              'scope_note':s['access_note'],
                              'claim_source_record_id':s['id']})
    graph['sources'].extend(added_sources)
    people={p['id']:p for p in graph['people']}
    added_nodes=[]
    for proposal in proposals:
        pid=proposal['person_id']
        if people[pid].get('node_id') or any(n['id']==pid for n in graph['nodes']):
            raise ValueError('Already promoted: '+pid)
        n=copy.deepcopy(proposal['node'])
        n['work_ids']=proposal['work_ids']
        n['claim_ids']=proposal['claim_ids']
        n['scope_note']=n['scope_note'].replace('This draft covers', 'This entry covers').replace('This draft is supported', 'This entry is supported')
        n['source_ids'] += [witness_sources[s['id']] for s in catalogue['source_records'] if s['describes_work'] in n['work_ids']]
        added_nodes.append(n)
        people[pid]['node_id']=pid
    graph['nodes'].extend(added_nodes)
    # Explicit reviewed views: a work is not silently equated with its author,
    # and a strand is never silently equated with its parent teaching umbrella.
    views = [
        ('scott_gender','joan_wallach_scott','gender','Gender as historical analysis','gender/gender'),
        ('foucault_scott','foucault','joan_wallach_scott','Foucault’s conception of power in Scott’s 1986 article',None),
        ('davis_biography','natalie_zemon_davis','biography','Provisional: comparative lives in Women on the Margins','biography/comparative_margins'),
        ('hunt_culture','lynn_hunt','culture','Cultural interpretation and social explanation in Hunt’s 1989 introduction',None),
        ('catherine_hall_class','catherine_hall','social','With Davidoff: gender, family and middle-class formation','social/gender_family_class'),
        ('leonore_davidoff_class','leonore_davidoff','social','With Hall: gender, family and middle-class formation','social/gender_family_class'),
        ('higginbotham_race','evelyn_brooks_higginbotham','black','Race, gender and historical explanation','black/racial_analysis'),
        ('smith_authority','linda_tuhiwai_smith','indigenous','Self-determination and authority over research','indigenous/methods'),
        ('lorraine_daston_objectivity','lorraine_daston','science','With Galison: historical forms of scientific objectivity','science/objectivity_images'),
    ]
    claims={c['id']:c for c in catalogue['claims']}
    added_edges=[]
    for num,(suffix,source,target,label,strand) in enumerate(views,753):
        cid='claim:promotions01:'+suffix
        c=claims[cid]
        mapping = ('The target is the named strand, displayed under its parent entry.' if strand else
                   'The target entry displays the particular work or explanatory topic named in this relationship; it does not broaden the claim to an entire career or field.')
        edge={'id':f'edge_{num:03}', 'source':source,'target':target,'type':'connection',
              'relationship_kind':'influence' if suffix=='foucault_scott' else 'contribution','directed':True,
              'relationship':label, 'map_label':label,
              'evidence_note':c['statement']+' '+c['qualification']+' '+mapping,
              'source_ids':list(dict.fromkeys(witness_sources[e['source_record_id']] for e in c['evidence'])),
              'classification_basis':'editorial_review', 'claim_ids':[cid],
              'review_status':c['review']['status'], 'claim_projection':{'subject':c['subject'],'object':c['object'],'note':mapping}}
        if strand:
            edge['target_strand']=strand
        added_edges.append(edge)
    graph['edges'].extend(added_edges)
    graph['revision_history'].append({'version':'1.119','date':DAY,
        'summary':'Promote eight existing people; preserve first-class works and citation-specific claims in a bounded catalogue; add nine qualified teaching connections, including one explicitly provisional description-supported connection.',
        'added_node_ids':[n['id'] for n in added_nodes], 'promoted_person_ids':[n['id'] for n in added_nodes],
        'added_edge_ids':[e['id'] for e in added_edges], 'added_source_ids':[s['id'] for s in added_sources],
        'acceptance_record':catalogue['acceptance_record']})
    return graph


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    path=ROOT/'historiography-1920-2000.json'
    if read(path)['revision_history'][-1]['version']=='1.119':
        raise SystemExit('Revision 1.119 is already applied; use audit_promotion_import.py to verify it.')
    manifest=read(PACKET/'manifest.json')
    for name, expected in manifest['files'].items():
        if sha(ROOT/name)!=expected:
            raise ValueError('Reviewed input changed: '+name)
    snapshot=ROOT/BASELINE
    if snapshot.exists() and snapshot.read_bytes()!=path.read_bytes():
        raise ValueError('Refusing to replace an existing different snapshot')
    before=read(path)
    batch=read(PACKET/'batch.json')
    proposals=read(PACKET/'node-proposals.json')['proposals']
    after=transform(before,batch,proposals)
    errors,_=validate(after,read(ROOT/'seminar-pathways.json'))
    if errors:
        raise ValueError('\n'.join(errors))
    snapshot.write_bytes(path.read_bytes())
    baseline=read(ROOT/'data/extension-2026/baseline.json')
    archive=ROOT/'drafts/extension-browser-v1.118'
    for name, expected in baseline['browser_asset_hashes'].items():
        src=ROOT/name
        if sha(src)!=expected:
            raise ValueError('Browser baseline changed before archive: '+name)
        dest=archive/Path(name).relative_to('docs')
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=src.read_bytes():
            raise ValueError('Refusing to overwrite archived browser file')
        shutil.copyfile(src,dest)
    acceptance={'revision':'1.119','date':DAY,'authorization':'User: add it to the production graph',
        'baseline':BASELINE,'baseline_sha256':sha(snapshot),'research_packet':'data/extension-2026/promotions-01/batch.json',
        'research_packet_sha256':sha(PACKET/'batch.json'), 'research_manifest_sha256':sha(PACKET/'manifest.json'),
        'browser_baseline_archive':str(archive.relative_to(ROOT)),
        'node_ids':[p['person_id'] for p in proposals],
        'claim_decisions':[{'claim_id':c['id'],**c['review']} for c in after['claim_catalogue']['claims']],
        'teaching_edge_ids':[e['id'] for e in after['edges'][len(before['edges']):]],
        'scope':'Only this batch is imported. Earlier packets remain staging; historical baselines are preserved rather than reset.'}
    path.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    acceptance['production_graph_sha256']=sha(path)
    (OUT/'acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n')
    print('Applied revision 1.119: 8 nodes, 9 teaching connections, 7 works, 35 claims (one provisional).')


if __name__=='__main__':
    main()
