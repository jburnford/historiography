"""Apply reviewed research upgrades to the owned, unaccepted draft packets."""
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DAY='2026-10-31'


def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def apply_batch(number):
    upgrades=HERE/'quality-review/upgrades.json'
    if not upgrades.exists():return
    patches=read(upgrades)
    folder=ROOT/f'data/extension-2026/timeline-canon-batch{number}-2026-10-31'
    cfg=read(folder/'batch.json')
    for pid in cfg['persons']:
        if pid not in patches:continue
        q=patches[pid];d=read(folder/pid/'entry-draft.json');n=read(folder/pid/'research-notes.json')
        d['node'].update(q.get('node_fields',{}))
        replacements={e['proposal_id']:e for e in q.get('replace_edges',[])}
        d['proposed_edges']=[replacements.get(e['proposal_id'],e) for e in d['proposed_edges'] if e['proposal_id'] not in q.get('remove_edge_ids',[])]
        for e in q.get('edges',[]):
            if e['proposal_id'] not in {x['proposal_id'] for x in d['proposed_edges']}:d['proposed_edges'].append(deepcopy(e))
        for s in q.get('sources',[]):
            if s['id'] not in {x['id'] for x in d['new_sources']}:d['new_sources'].append(deepcopy(s))
        # Corrections are restricted to this person's unaccepted new sources.
        # Earlier canonical source records are never edited by this writer.
        for s in d['new_sources']:
            s.update(deepcopy(q.get('new_source_updates',{}).get(s['id'],{})))
        d['node']['source_ids']=list(dict.fromkeys(d['node']['source_ids']+[s['id'] for s in q.get('sources',[])]+q.get('existing_source_ids',[])))
        for row in d.get('roster_additions',[]):
            replacement=replacements.get(row['proposal_id'])
            if replacement:row['row'].update(context=replacement['relationship'],source_ids=replacement['source_ids'])
        n['relations']=deepcopy(d['proposed_edges'])
        n['new_source_scopes']=deepcopy(d['new_sources'])
        n['reading_limit']=d['node']['scope_note']
        n['events']=deepcopy(d['node']['chronology']['events'])
        n['existing_source_ids_reused']=list(dict.fromkeys(n.get('existing_source_ids_reused',[])+q.get('existing_source_ids',[])))
        n['passage_checks']=[dict(source_ids=e['source_ids'],locator_and_scope=e['evidence_note'],support=e['relationship']) for e in d['proposed_edges']]
        n['quality_review']=q['review']
        d['quality_review']=q['review']
        if q.get('life_addenda'):
            life=read(folder/pid/'life-status.json')
            for item in q['life_addenda']:
                if item not in life['sources']:life['sources'].append(item)
            life['quality_review_note']=q.get('life_note','Additional life evidence retained without silently discarding earlier witnesses.')
            write(folder/pid/'life-status.json',life)
        write(folder/pid/'entry-draft.json',d);write(folder/pid/'research-notes.json',n)
    apply_claude_review(number)


def apply_claude_review(number):
    """Second overlay: Claude's independent verification (quality-review/claude-review.json).

    Applied after the researcher upgrades. Every change is a partial update keyed by
    person, so the researcher text stays recoverable from upgrades.json. Fields:
    node_fields, remove_edge_ids (their roster rows go too), edge_updates, edges,
    sources, remove_source_ids, source_updates, roster_updates, event_updates,
    life_update, verification, review.
    """
    path=HERE/'quality-review/claude-review.json'
    if not path.exists():return
    patches=read(path)
    folder=ROOT/f'data/extension-2026/timeline-canon-batch{number}-2026-10-31'
    for pid in read(folder/'batch.json')['persons']:
        q=patches.get(pid)
        if not q:continue
        d=read(folder/pid/'entry-draft.json');n=read(folder/pid/'research-notes.json')
        node=d['node']
        node.update(deepcopy(q.get('node_fields',{})))
        gone=set(q.get('remove_edge_ids',[]))
        held=[e for e in d['proposed_edges'] if e['proposal_id'] in gone]
        d['proposed_edges']=[e for e in d['proposed_edges'] if e['proposal_id'] not in gone]
        d['roster_additions']=[r for r in d.get('roster_additions',[]) if r['proposal_id'] not in gone]
        for e in d['proposed_edges']:
            e.update(deepcopy(q.get('edge_updates',{}).get(e['proposal_id'],{})))
        for e in q.get('edges',[]):
            if e['proposal_id'] not in {x['proposal_id'] for x in d['proposed_edges']}:d['proposed_edges'].append(deepcopy(e))
        drop=set(q.get('remove_source_ids',[]))
        d['new_sources']=[s for s in d['new_sources'] if s['id'] not in drop]
        for s in q.get('sources',[]):
            if s['id'] not in {x['id'] for x in d['new_sources']}:d['new_sources'].append(deepcopy(s))
        for s in d['new_sources']:
            s.update(deepcopy(q.get('source_updates',{}).get(s['id'],{})))
        used=[sid for e in d['proposed_edges'] for sid in e['source_ids']]
        node['source_ids']=[sid for sid in dict.fromkeys(node['source_ids']+[s['id'] for s in q.get('sources',[])]+q.get('add_source_ids',[])+used) if sid not in drop]
        for row in d.get('roster_additions',[]):
            upd=q.get('roster_updates',{}).get(row['proposal_id'])
            if upd:row['row'].update(deepcopy(upd))
            else:
                e=next((x for x in d['proposed_edges'] if x['proposal_id']==row['proposal_id']),None)
                if e and row['proposal_id'] in q.get('edge_updates',{}):row['row'].update(context=e['relationship'],source_ids=e['source_ids'])
        for ev in node.get('chronology',{}).get('events',[]):
            ev.update(deepcopy(q.get('event_updates',{}).get(ev['id'],{})))
        if held:
            d['edges_considered_not_proposed']=d.get('edges_considered_not_proposed',[])+[
                f"{e['proposal_id']}: held at Claude verification 2026-10-31. {q.get('hold_reasons',{}).get(e['proposal_id'],'Cited passage could not be read through an allowed route.')}" for e in held]
        n['relations']=deepcopy(d['proposed_edges'])
        n['new_source_scopes']=deepcopy(d['new_sources'])
        n['reading_limit']=node['scope_note']
        n['events']=deepcopy(node['chronology']['events'])
        n['passage_checks']=[dict(source_ids=e['source_ids'],locator_and_scope=e['evidence_note'],support=e['relationship']) for e in d['proposed_edges']]
        n['claude_verification']=q.get('verification','')
        d['claude_review']=q.get('review','')
        if q.get('life_update'):
            life=read(folder/pid/'life-status.json')
            u=deepcopy(q['life_update'])
            life['sources']=life['sources']+[s for s in u.pop('add_sources',[]) if s not in life['sources']]
            life.update(u)
            write(folder/pid/'life-status.json',life)
        write(folder/pid/'entry-draft.json',d);write(folder/pid/'research-notes.json',n)


if __name__=='__main__':
    for number in ([int(sys.argv[1])] if len(sys.argv)>1 else [1,2,3]):apply_batch(number)
