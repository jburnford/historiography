"""Check audit identity, scope, endpoints and duplicate-record guards; no network."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());G=read(ROOT/'historiography-1920-2000.json');N={n['id']:n for n in G['nodes']};E={e['id']:e for e in G['edges']};S={s['id']:s for s in G['sources']}
n=read(HERE/'node-review.json');p=read(HERE/'proposals.json');f=read(HERE/'field-route-review.json')
assigned={r['node_id'] for r in read(HERE.parent/'all-node-assignments.json')['lanes']['canadian-colonial']}
assert len(n['rows'])==len(assigned)==90 and {r['node_id'] for r in n['rows']}==assigned
assert n['baseline_graph_sha256']==p['baseline_graph_sha256']==hashlib.sha256((ROOT/'historiography-1920-2000.json').read_bytes()).hexdigest()
new_sources={s['source_id'] for s in p['sources'] if not s['existing']};assert all(s.startswith('rea_canadian_') for s in new_sources)
seen=set()
for row in p['proposals']:
 assert row['source'] in N and row['target'] in N
 assert row['proposal_id'] not in seen;seen.add(row['proposal_id'])
 assert all(s in S or s in new_sources for s in row['source_ids'])
 assert all(e in E for e in row['existing_edge_check']['related_existing_edges'])
 assert not [e for e in G['edges'] if {e['source'],e['target']}=={row['source'],row['target']}]
 assert row['evidence_note'] and row['read_extent'] and row['primary_locators']
for row in n['rows']:
 incident=[e for e in G['edges'] if row['node_id'] in (e['source'],e['target'])]
 assert row['existing_degree']==len(incident)
 assert row['assessment'] and row['completeness_claim'] is False
 assert set(row['proposal_ids'])<=seen
for row in f['repairs']:
 assert row['before']==E[row['edge_id']]
 assert row['after']==dict(row['before'],source=row['after']['source'])
 assert row['after']['source'] in N
out=dict(status='pass',baseline_revision=G['revision_history'][-1]['version'],graph_sha256=n['baseline_graph_sha256'],node_reviews=90,new_edge_candidates=len(p['proposals']),source_endpoint_repairs=len(f['repairs']),holds=len(p['holds']),new_sources=len(new_sources),existing_source_addenda=len(p['sources'])-len(new_sources),current_pair_duplicates=0,canonical_mutations=False,public_assets_added=False)
(HERE/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
