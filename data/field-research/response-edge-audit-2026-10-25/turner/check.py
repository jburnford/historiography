"""Read-only canonical audit and an in-memory proposal preview; owned reports only."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.validate_graph import validate,pathways_within

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 baseline=read(P/'baseline.json'); canonical=ROOT/'historiography-1920-2000.json'
 assert sha(canonical)==baseline['sha256']
 G=read(canonical); A=read(ROOT/'data/field-research/response-edge-audit-2026-10-25/all-node-assignments.json')
 R=read(P/'node-review.json'); proposals=read(P/'proposals.json'); sources=read(P/'sources.json'); fragment=read(P/'entry-draft-fragment.json')
 expected={x['node_id']:x for x in A['lanes']['turner']};rows={x['node_id']:x for x in R['nodes']}
 assert len(rows)==len(R['nodes'])==90 and set(rows)==set(expected)
 for id,r in rows.items():
  incident=[e['id'] for e in G['edges'] if id in (e['source'],e['target'])]
  assert r['existing_edge_count']==len(incident)==expected[id]['existing_edge_count'],id
  assert set(incident)==set(r['existing_edge_ids']),id
  assert r['current_represented_relations'] and r['candidate_gaps_and_limits'] and r['read_extent'],id
 assert len({x['proposal_id'] for x in proposals['proposals']})==len(proposals['proposals'])==17
 old={e['id']:e for e in G['edges']};nodes={n['id'] for n in G['nodes']};source_ids={s['id'] for s in G['sources']}
 fresh={s['id']:s for s in sources['sources']}
 assert len(fresh)==len(sources['sources']) and not source_ids&fresh.keys()
 for x in fresh.values():assert x['id'].startswith('rea_turner_') and x['verification']['note']
 for p in proposals['proposals']:
  assert p['source'] in nodes and p['target'] in nodes and p['source']!=p['target']
  assert all(s in fresh or s in source_ids for s in p['source_ids'])
  assert not [e for e in G['edges'] if {p['source'],p['target']}=={e['source'],e['target']}],p['proposal_id']
  assert p['directed']==(p['relationship_kind']!='comparison')
 for p in proposals['edge_revision_proposals']:
  assert p['previous_record']==old[p['edge_id']],p['edge_id']
  assert set(p['changes'])<={'source','target','evidence_note'}
  assert set(p['source_ids'])==set(old[p['edge_id']]['source_ids'])
  for node in G['nodes']:
   assert not any(row.get('edge_id')==p['edge_id'] for row in node.get('representative_people',[])),p['edge_id']
 # No node, life or chronology change is needed for this preview.
 after=deepcopy(G)
 for p in proposals['edge_revision_proposals']:next(e for e in after['edges'] if e['id']==p['edge_id']).update(p['changes'])
 after['sources'].extend(fragment['new_sources'])
 first=max(int(e['id'].split('_')[1]) for e in G['edges'])+1
 for i,e in enumerate(fragment['proposed_edges'],first):
  after['edges'].append(dict(id=f'edge_{i:03d}',**{k:v for k,v in e.items() if k!='include'}))
 assert after['nodes']==G['nodes'] and after['people']==G['people']
 path=read(ROOT/'seminar-pathways.json');err0,warn0=validate(G,pathways_within(G,path));err,warn=validate(after,pathways_within(after,path))
 assert not err0 and not err,(err0,err)
 assert sha(canonical)==baseline['sha256']
 # Graded screening holds stay explicit, including unavailable person endpoints.
 holdrows=[]
 for r in R['nodes']:
  for h in r['held_case_ids']:holdrows.append({'id':h,'node_id':r['node_id'],'decision':'held_screening_lead_not_verified_edge','reason':r['candidate_gaps_and_limits'],'scope':r['read_extent']})
 (P/'screening-holds.json').write_text(json.dumps({'checked_on':'2026-10-25','holds':holdrows},ensure_ascii=False,indent=2)+'\n')
 report={'status':'pass','baseline_revision':'1.191','checked_on':'2026-10-25','node_rows':90,'fresh_witness_nodes':sum(bool(r['fresh_source_ids']) for r in R['nodes']),'proposed_new_edges':17,'proposed_existing_edge_revisions':7,'new_source_records_used_by_fragment':len(fragment['new_sources']),'research_witness_records':len(fresh),'grade_counts':dict(Counter(p['grade'] for p in proposals['proposals'])),'baseline_counts':baseline['counts'],'hypothetical_counts':{k:len(after[k]) for k in ('nodes','edges','sources','people')},'baseline_warnings':warn0,'preview_warnings':warn,'validation_errors':err,'canonical_sha256_unchanged':sha(canonical),'applied':False,'limits':'Research preview only, pending coordinator and independent substantive review. Every assigned node received a reasoned bounded screen; this does not certify every source body or a complete response network.'}
 (P/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('baseline_warnings','preview_warnings')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
