import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());G=read(ROOT/'historiography-1920-2000.json');edges={e['id']:e for e in G['edges']};sources={s['id']:s for s in G['sources']}
routes=[]
for eid,pid,reason,extent,loc in [
 ('edge_096','dipesh_chakrabarty','The claim and primary introduction name Chakrabarty alone; retain its qualified engagement with European concepts.','Fresh publisher introduction pp3–10 read.','Provincializing Europe introduction pp3–6'),
 ('edge_124','dipesh_chakrabarty','The historical-difference argument is Chakrabarty’s. The mapping to global history remains an editorial conceptual comparison, with no claim of reception by every global historian. Existing edge1145 instead concerns the later globe/planet argument.','Fresh publisher introduction pp3–10 read; whole book unread.','Provincializing Europe introduction pp3–10'),
 ('edge_359','frederick_cooper','The current claim specifically concerns Cooper’s colonial labour inquiry; no other author supplies this arrow.','Inherited accepted primary PartI introduction and Mombasa partial reading; this audit inspected the current source verification and exact edge note, not a new whole-book reading.','Decolonization and African Society pp23–24 and234–241')]:
 before=edges[eid];after=dict(before,source=pid)
 routes.append(dict(proposal_id='rea_canadian_route_'+eid.split('_')[1],disposition='include_source_endpoint_repair',edge_id=eid,before=before,after=after,allowed_changes=['source'],reason=reason,read_extent=extent,primary_locator=loc,source_ids=before['source_ids'],same_pair_after=[e['id'] for e in G['edges'] if e['id']!=eid and {e['source'],e['target']}=={after['source'],after['target']}]))
retained=[dict(edge_id='edge_397',disposition='retain_field_bridge',reason='Cooper already has an individual African-history contribution at edge1340. This record additionally connects social-history methods to African decolonization through a named example; no new direct response or intellectual debt was found here. Preserve its primary Mombasa evidence and reconsider only if the parent chooses a consistent field/person routing policy.'),dict(edge_id='edge_730',disposition='retain_identity_guard',reason='The author is Paul Carter, not Sarah Carter. The publisher page confirms The Road to Botany Bay, original1987 and later reissue. Paul Carter has no individual node. Do not reroute to Sarah.',source_id='carter_botany_1987',primary_url='https://www.upress.umn.edu/9780816669974/the-road-to-botany-bay/',read_extent='Fresh publisher author/title/original-versus-reissue metadata only; book body unread.')]
(HERE/'field-route-review.json').write_text(json.dumps(dict(schema='response_field_route_review/1',baseline_revision='1.191',repairs=routes,retained=retained),ensure_ascii=False,indent=2)+'\n')
# Keep normal spacing in newly written human prose without touching URLs, IDs or inherited claims.
def prose(s):
 s=re.sub(r'(?<=[A-Za-z])(?=\d{4}\b)',' ',s)
 s=re.sub(r'\b([ap])(?=\d{2,3}\b)',r'\1. ',s)
 return s
p=read(HERE/'proposals.json')
for item in p['proposals']:
 for key in ['relationship','evidence_note','read_extent','date_scope']:
  if item.get(key):item[key]=prose(item[key])
 item['primary_locators']=[prose(x) for x in item['primary_locators']]
for row in p['holds']:
 for key in ['reason','read_extent']:row[key]=prose(row[key])
(HERE/'proposals.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
n=read(HERE/'node-review.json')
for row in n['rows']:
 row['assessment']=prose(row['assessment']);row['possible_missing_debts_critiques_reception']=prose(row['possible_missing_debts_critiques_reception'])
 incident=[x['proposal_id'] for x in routes if row['node_id'] in (x['before']['source'],x['before']['target'],x['after']['source'],x['after']['target'])]
 row['field_route_proposal_ids']=incident
 if row['node_id']=='dipesh_chakrabarty':row['read_extent']['fresh_primary_source_ids']=sorted(set(row['read_extent']['fresh_primary_source_ids'])|{'post'})
 if row['node_id']=='liberal_order_framework':row['assessment']+=' This is a route-visibility proposal, not evidence that the existing field critique is absent.'
 if row['node_id']=='sarah_carter':row['assessment']+=' Paul Carter’s Australian spatial-history work is a distinct identity and is not assigned here.'
n['status']='ready_for_parent_review_and_deduplication';n['new_edge_proposals']=len(p['proposals']);n['source_endpoint_repairs']=len(routes)
(HERE/'node-review.json').write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n')
print('Finalized16 new-edge candidates,3 source endpoint repairs,2 retained field checks,90 node reviews')
