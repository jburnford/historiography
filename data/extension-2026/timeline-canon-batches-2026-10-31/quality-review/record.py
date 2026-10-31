"""Small writer for passage-reviewed upgrades; does not apply the graph."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def source(sid,title,url,scope):
    return dict(id=sid,title=title,citation=title,url=url,verification=dict(status='supporting_page_checked',checked_on='2026-10-31',note=scope))

def edge(pid,key,origin,target,text,sids,locator,kind='contribution'):
    return dict(proposal_id='tq_'+pid+'_'+key,source=origin,target=target,relationship=text,source_ids=[sids] if isinstance(sids,str) else sids,evidence_note=locator,relationship_kind=kind,type='critique' if kind=='critique' else 'connection',directed=kind!='comparison',classification_basis='editorial_review')

def replace(pid,number,origin,target,text,sids,locator,kind='contribution',batch=3):
    e=edge(pid,'replace',origin,target,text,sids,locator,kind);e['proposal_id']=f'tc{231+batch}_{pid}_{number}';return e

def record(pid,description,scope,sources=None,edges=None,replacements=None,existing=None,reads=None,holds=None):
    p=HERE/'upgrades.json';all_upgrades=json.loads(p.read_text()) if p.exists() else {}
    all_upgrades[pid]=dict(node_fields=dict(description=description,scope_note=scope),sources=sources or [],edges=edges or [],replace_edges=replacements or [],existing_source_ids=existing or [],review=dict(status='passages_strengthened_pending_final_audit',checked_on='2026-10-31',researcher='Codex primary agent',independent_review='Pending Claude; no independent-review pass asserted',passage_reads=reads or [],remaining_limits=holds or []))
    p.write_text(json.dumps(all_upgrades,ensure_ascii=False,indent=2)+'\n')
    progress_path=HERE/'progress.json';progress=json.loads(progress_path.read_text())
    for x in progress['people']:
        if x['person_id']==pid:x['status']='passages_strengthened_pending_final_audit'
    progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
