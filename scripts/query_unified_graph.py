#!/usr/bin/env python3
"""Query the Ladybug graph and render an offline, source-linked person page."""
import argparse
from html import escape
import json
from pathlib import Path

try:
    from .build_unified_graph import OUT, ROOT, connect_ladybug, key
except ImportError:
    from build_unified_graph import OUT, ROOT, connect_ladybug, key


def rows(conn,cypher,params=None):
    result=conn.execute(cypher,params or {})
    try:
        return list(result.rows_as_dict())
    finally:
        result.close()


def search(conn,term,limit=20,kind=None):
    return rows(conn,'''MATCH (n:Entity) WHERE contains(n.name_key,$term)
        AND ($kind='' OR n.kind=$kind) RETURN n.id AS id,n.kind AS kind,n.label AS label,n.origin AS origin
        ORDER BY n.label,n.id LIMIT $limit''',{'term':key(term),'kind':kind or '', 'limit':limit})


def node(conn,nid):
    found=rows(conn,'''MATCH (n:Entity {id:$id}) RETURN n.id AS id,n.kind AS kind,
                      n.label AS label,n.origin AS origin,n.data AS data''',{'id':nid})
    if not found:
        raise ValueError('Unknown graph ID: '+nid)
    found[0]['data']=json.loads(found[0]['data'])
    return found[0]


def expand_mentions(conn,mentions):
    result=[]
    for mention in mentions:
        data=json.loads(mention['data']);meta=data['metadata']
        review=node(conn,meta['review_id']);review_meta=review['data']['metadata']
        source=node(conn,review_meta['source_id'])
        item=node(conn,meta['item_id']) if meta.get('item_id') else None
        network=node(conn,review_meta['network_id']) if review_meta.get('network_id') else None
        result.append(dict(mention_id=mention['id'],recorded_name=mention['label'],role=meta['role'],
                           source=mention['id'].split(':')[0],response_id=meta.get('response_id'),
                           affiliation=meta.get('affiliation'),review_id=review['id'],
                           review_date=review_meta.get('date_month'),review_date_raw=review_meta.get('date_raw'),
                           item_id=item['id'] if item else None,item_title=item['label'] if item else None,
                           network=network['label'] if network else None,source_url=source['data'].get('source_url'),
                           archive_url=source['data'].get('wayback_url'),source_record_id=source['id'],
                           source_json_sha256=data.get('source_json_sha256'),source_raw_sha256=data.get('source_raw_sha256')))
    return result


def person(conn,term,limit=50):
    # Name search never selects an arbitrary homonym. Prefer an explicit local
    # identity; otherwise require a single exact person label.
    pid=term if ':' in term else 'atlas:person:'+term
    found=rows(conn,'MATCH (p:Entity {id:$id}) WHERE p.kind=\'person\' RETURN p.id AS id',{'id':pid})
    if not found:
        found=rows(conn,'''MATCH (p:Entity) WHERE p.kind='person' AND p.name_key=$name
                          RETURN p.id AS id''',{'name':key(term)})
    if len(found)!=1:
        return {'status':'choose_identity','matches':search(conn,term,limit,'person')}
    pid=found[0]['id'];record=node(conn,pid)
    authority=rows(conn,'''MATCH (p:Entity {id:$id})-[r:Link]->(w:Entity)
        WHERE r.predicate='same_person' AND r.status='accepted'
        RETURN w.id AS id,w.label AS label,w.data AS record,r.data AS decision''',{'id':pid})
    for row in authority:
        row['record']=json.loads(row['record']);row['decision']=json.loads(row['decision'])
    entries=rows(conn,'''MATCH (e:Entity)-[r:Link]->(p:Entity {id:$id})
        WHERE r.predicate='presents_person' RETURN e.id AS id,e.label AS label,e.data AS data''',{'id':pid})
    for entry in entries:entry['data']=json.loads(entry['data'])
    contexts=rows(conn,'''MATCH (e:Entity)-[r:Link]->(p:Entity {id:$id})
        WHERE r.predicate='selects_person' RETURN e.id AS id,e.label AS label,
        r.data AS selection,r.evidence AS evidence ORDER BY e.label''',{'id':pid})
    for row in contexts:
        row['selection']=json.loads(row['selection']);row['evidence']=json.loads(row['evidence'])
    groups=rows(conn,'''MATCH (c:Entity)-[a:Link]->(ref:Entity)-[b:Link]->(p:Entity {id:$id})
        WHERE c.kind='name_candidate' AND a.predicate='candidate_atlas_identity'
        AND b.predicate='local_person_reference' RETURN DISTINCT c.id AS id,c.label AS label''',{'id':pid})
    groups+=rows(conn,'''MATCH (p:Entity {id:$id})-[a:Link]->(w:Entity)<-[b:Link]-(c:Entity)
        WHERE a.predicate='same_person' AND a.status='accepted' AND c.kind='name_candidate'
        AND b.predicate='candidate_wikidata_identity' RETURN DISTINCT c.id AS id,c.label AS label''',{'id':pid})
    groups+=rows(conn,'''MATCH (c:Entity)-[r:Link]->(p:Entity {id:$id})
        WHERE c.kind='name_candidate' AND r.predicate='candidate_atlas_identity'
        RETURN DISTINCT c.id AS id,c.label AS label''',{'id':pid})
    groups=list({g['id']:g for g in groups}.values());group_ids=[g['id'] for g in groups]
    mention_query='''MATCH (m:Entity)-[r:Link]->(c:Entity) WHERE r.predicate='has_name_candidate'
        AND c.id IN $groups
        OPTIONAL MATCH (m)-[resolved:Link]->(target:Entity)
          WHERE resolved.predicate='resolved_as' AND resolved.status='accepted'
        WITH m,count(resolved) AS resolutions WHERE resolutions=0
        OPTIONAL MATCH (m)-[rejected:Link]->(person:Entity {id:$person})
          WHERE rejected.predicate='rejected_identity' AND rejected.status='rejected'
        WITH m,count(rejected) AS rejections WHERE rejections=0
        RETURN m.id AS id,m.label AS label,m.data AS data ORDER BY id LIMIT $limit'''
    possible=rows(conn,mention_query,{'groups':group_ids,'person':pid,'limit':limit+1}) if groups else []
    confirmed=rows(conn,'''MATCH (m:Entity)-[r:Link]->(p:Entity {id:$id})
        WHERE r.predicate='resolved_as' AND r.status='accepted'
        RETURN m.id AS id,m.label AS label,m.data AS data ORDER BY m.id LIMIT $limit''',{'id':pid,'limit':limit+1})
    bibliography=rows(conn,'''MATCH (c:Entity)-[a:Link]->(p:Entity {id:$id}), (c)-[r:Link]->(w:Entity)
        WHERE a.predicate='local_person_reference' AND r.predicate='claim_authored'
        RETURN w.id AS id,w.label AS label,w.data AS data,r.status AS status,r.data AS claim
        ORDER BY w.label''',{'id':pid})
    for row in bibliography:
        row['data']=json.loads(row['data']);row['claim']=json.loads(row['claim'])
    evidence_ids=sorted({sid for c in contexts for sid in c['evidence']})
    sources=rows(conn,'''MATCH (s:Entity) WHERE s.id IN $ids RETURN s.id AS id,s.label AS label,s.data AS data
                         ORDER BY s.id''',{'ids':evidence_ids}) if evidence_ids else []
    for row in sources:row['data']=json.loads(row['data'])
    accepted=expand_mentions(conn,confirmed[:limit]);candidate=expand_mentions(conn,possible[:limit])
    return dict(status='found',person=record,atlas_entries=entries,atlas_contexts=contexts,
                wikidata_identities=authority,catalogue_works=bibliography,
                accepted_review_credits=accepted,candidate_review_credits=candidate,
                accepted_hnet_credits=[c for c in accepted if c['source']=='hnet'],
                candidate_hnet_credits=[c for c in candidate if c['source']=='hnet'],candidate_name_groups=groups,
                truncated={'accepted_reviews':len(confirmed)>limit,'candidate_reviews':len(possible)>limit},
                sources=sources,qualification='Candidate review credits are not attributed to this person until identity review.')


def neighbors(conn,nid,limit=50,include_candidates=False):
    focus=node(conn,nid)
    links=rows(conn,'''MATCH (n:Entity)-[r:Link]-(m:Entity) WHERE n.id=$id
        AND ($candidates OR (r.status<>'candidate_only' AND r.status<>'rejected'))
        RETURN DISTINCT r.id AS id,r.predicate AS predicate,r.status AS status,r.directed AS directed,
        r.data AS data,r.evidence AS evidence,m.id AS neighbor_id,m.label AS neighbor_label,m.kind AS neighbor_kind
        ORDER BY id LIMIT $limit''',{'id':nid,'candidates':include_candidates,'limit':limit+1})
    for row in links:
        row['data']=json.loads(row['data']);row['evidence']=json.loads(row['evidence'])
    return {'node':focus,'links':links[:limit],'truncated':len(links)>limit,'include_candidates':include_candidates}


def html_profile(profile):
    if profile.get('status')!='found':
        raise ValueError('Choose an unambiguous person before rendering a page')
    esc=lambda value:escape(str(value or ''),quote=True)
    def link(url,label):
        if not url or not url.startswith(('https://','http://')):return esc(label)
        return f'<a href="{esc(url)}">{esc(label)}</a>'
    p=profile['person'];parts=[f'<h1>{esc(p["label"])}</h1>',
        '<p class="muted">Atlas · H-Net · Reviews in History · Wikidata — local research preview</p>',
        f'<p><code>{esc(p["id"])}</code></p>']
    for entry in profile['atlas_entries']:
        data=entry['data'];parts+=[f'<p>{esc(data.get("description"))}</p>',f'<p class="note">{esc(data.get("scope_note"))}</p>']
    parts.append('<h2>Accepted Wikidata identity</h2>')
    for w in profile['wikidata_identities']:
        parts.append('<p>'+link('https://www.wikidata.org/wiki/'+w['id'].split(':')[-1],w['id'])+'</p>')
        life=w['decision'].get('life',{})
        if life:parts.append(f'<p>Recorded life dates: {esc(life.get("birth"))} – {esc(life.get("death"))}</p>')
        parts.append('<details><summary>Identity evidence and recorded date statements</summary><pre>'+esc(json.dumps(w,ensure_ascii=False,indent=2))+'</pre></details>')
    if not profile['wikidata_identities']:parts.append('<p>No accepted Wikidata identity recorded.</p>')
    parts.append('<h2>Atlas contexts</h2>')
    for context in profile['atlas_contexts']:
        selection=context['selection'];parts.append(f'<article><h3>{esc(context["label"])}</h3><p class="muted">Role in this selection: {esc(selection.get("role"))}</p><p>{esc(selection.get("context"))}</p><p>{esc(selection.get("works"))}</p></article>')
    parts.append('<h2>Recorded catalogue works</h2>')
    for work in profile['catalogue_works']:parts.append(f'<p>{esc(work["label"])} <span class="muted">({esc(work["status"])})</span></p>')
    for name,title,legacy in [('accepted_review_credits','Resolved review-corpus credits','accepted_hnet_credits'),('candidate_review_credits','Review-corpus identity candidates','candidate_hnet_credits')]:
        parts.append('<h2>'+title+'</h2>')
        if name=='candidate_review_credits':parts.append('<p class="note">These records share a candidate name. They may concern different people. They are not accepted credits for this person.</p>')
        credits=profile.get(name,profile.get(legacy,[]))
        if not credits:parts.append('<p>No records in this category.</p>')
        for credit in credits:
            title=credit.get('item_title') or (('Author response to ' if credit.get('response_id') else 'Reviewer credit on ')+credit['review_id'])
            parts.append(f'<article><h3>{esc(title)}</h3><p>{esc(credit["recorded_name"])} · {esc(credit["role"])} · {esc(credit.get("network"))} · {esc(credit.get("review_date_raw"))}</p><p>{esc(credit.get("affiliation"))}</p><p>'+link(credit.get('source_url'),'Reviews in History source' if credit.get('source')=='rih' else 'H-Net source')+' · '+link(credit.get('archive_url'),'Archived source')+f'</p><small>{esc(credit["mention_id"])}</small></article>')
    if any(profile['truncated'].values()):parts.append('<p class="note">This bounded preview is truncated. Increase the query limit to inspect more records.</p>')
    parts.append('<h2>Atlas source records</h2>')
    for source in profile['sources']:
        parts.append('<p>'+link(source['data'].get('url'),source['label'])+'</p>')
    css='body{font:17px/1.6 system-ui,sans-serif;max-width:960px;margin:3rem auto;padding:0 1.3rem;color:#243139;background:#f7f5ef}h1{font-size:2.5rem;line-height:1.2}h2{margin-top:2.5rem}article{padding:1rem 1.3rem;margin:1rem 0;background:white;border:1px solid #d9dfdf;border-radius:8px}h3{margin-top:0}a{color:#195d76}.muted,small{color:#56636b}.note{padding:1rem;border-left:4px solid #bd8b35;background:#fff8e6}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}small,code{overflow-wrap:anywhere}'
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+esc(p['label'])+' — Unified graph</title><style>'+css+'</style><main>'+''.join(parts)+'</main></html>'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['summary','search','person','neighbors'])
    p.add_argument('term',nargs='?',default='')
    p.add_argument('--db',type=Path,default=OUT/'graph.lbdb')
    p.add_argument('--limit',type=int,default=50)
    p.add_argument('--kind')
    p.add_argument('--include-candidates',action='store_true')
    p.add_argument('--html',type=Path)
    a=p.parse_args()
    if not 1<=a.limit<=200:p.error('--limit must be between 1 and 200')
    if a.command!='summary' and not a.term:p.error('A search term or ID is required')
    db,conn=connect_ladybug(a.db)
    try:
        if a.command=='summary':value=rows(conn,'MATCH (n:Entity) RETURN n.kind AS kind,count(n) AS count ORDER BY n.kind')
        elif a.command=='search':value=search(conn,a.term,a.limit,a.kind)
        elif a.command=='person':value=person(conn,a.term,a.limit)
        else:value=neighbors(conn,a.term,a.limit,a.include_candidates)
    finally:
        conn.close();db.close()
    if a.html:
        target=a.html.resolve()
        if not (target.is_relative_to(Path('/tmp')) or target.is_relative_to(OUT.resolve())):
            p.error('HTML previews must stay under /tmp or data/unified-graph/generated')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(html_profile(value))
        print('Saved '+str(target))
    else:print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
