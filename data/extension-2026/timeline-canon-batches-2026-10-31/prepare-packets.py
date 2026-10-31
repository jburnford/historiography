"""Research-packet writer for batches 2/3; canonical data is read-only."""
import csv
import hashlib
import json
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DAY='2026-10-31'


def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main(number):
    g=json.loads((ROOT/'historiography-1920-2000.json').read_text())
    if g['revision_history'][-1]['version']!='1.231':raise ValueError('Rebase/renumber explicitly after any accepted revision.')
    qpath=ROOT/f'data/field-research/timeline-candidates-2026-10-30/work-queues/batch-{number}.json'
    queue=json.loads(qpath.read_text())['persons']; prefix=f'tc{231+number}_';rev=f'1.{231+number}'
    out=ROOT/f'data/extension-2026/timeline-canon-batch{number}-2026-10-31'
    sources={s['id']:s for s in g['sources']};people={p['id']:p for p in g['people']};specs={}
    cachepath=ROOT/'data/wikidata/historians-qlever-2026-09-17/historians-with-dates.csv'
    with cachepath.open() as h: cached={r['qid']:r for r in csv.DictReader(h)}
    broadpath=ROOT/'data/wikidata/scholars-broad.csv'
    with broadpath.open() as h: broad={r['qid']:r for r in csv.DictReader(h)}
    sid=lambda key:key if key in sources or key.startswith('tc') else prefix+key
    ids=lambda keys:[sid(k) for k in ([keys] if isinstance(keys,str) else keys)]
    def S(key,title,url,note,metadata=False):
        return dict(id=sid(key),title=title,citation=title,url=url,verification=dict(status='bibliographic_metadata_checked' if metadata else 'supporting_page_checked',checked_on=DAY,note=note))
    def E(title,year,keys,support='Original publication metadata; complete book unread.'):
        return dict(label=title,kind='publication',track='contributions',date=dict(year=year,precision='year'),source_ids=['graph:'+s for s in ids(keys)],support=support)
    def R(target,text,keys,evidence,kind='contribution',origin=None):
        return dict(target=target,relationship=text,source_ids=ids(keys),evidence_note=evidence,relationship_kind=kind,origin=origin)
    def P(pid,description,works,scope,**kw):specs[pid]=dict(description=description,works=works,scope=scope,**kw)
    runpy.run_path(str(HERE/f'specs-batch{number}.py'),init_globals=dict(S=S,E=E,R=R,P=P))
    if set(specs)!={p['person_id'] for p in queue}:raise ValueError('Queue mismatch')
    bridge=[]
    for p in queue:
        pid=p['person_id'];s=specs[pid];new=pid not in people;edges=[]
        for i,r0 in enumerate(s['edges'],1):
            r=dict(r0);origin=r.pop('origin') or pid;r.update(source=origin,proposal_id=prefix+pid+'_'+str(i),directed=r['relationship_kind']!='comparison',type='critique' if r['relationship_kind']=='critique' else 'connection',classification_basis='editorial_review');edges.append(r)
        events=[]
        for i,e0 in enumerate(s['events'],1):e=dict(e0);e['id']=prefix+pid+'_'+str(i);events.append(e)
        src=s['sources'];old=s.get('old',[])
        node=dict(id=pid,label=p['name'],entry_kind='person',entry_type=p['entry_type'],layer='intellectual_connections' if p['entry_type']=='Individual theorist' else 'historians',period=None,hunt_core_paradigm=False,
                  description=s['description'],representative_figures_and_works=s['works'],scope_note=s['scope'],source_ids=list(dict.fromkeys(old+[x['id'] for x in src])),
                  date_label=' · '.join(f"{e['label']} ({e['date']['year']})" for e in events),
                  chronology=dict(version=1,label='Selected publications and editions',selection_note='Selected work milestones, not life dates, a continuous career or an exhaustive bibliography. Edition and translation dates remain distinct.',events=events,intervals=[],continuation=dict(status='not_asserted',basis='Selected publications do not establish continuous activity or an endpoint.'),interpretation='Primary passages, institutional testimony, named readers and metadata retain their separate reading scopes.',prepared_on=DAY,editorial_record=f'data/production-batches/person-entries-{rev}/acceptance.json'))
        update=dict(id=pid,label=p['name'],node_id=pid,new=new)
        if new:update['identity_note']='Queue identity retained and grounded through the matching institutional professional account and publications in this research packet. No namesake union inferred.'
        additions=[]
        for ctx,decision in s['contexts'].items():
            if not decision.startswith('accept') or ctx in p['existing_context_ids']:continue
            hit=[r for r in edges if r['source']==pid and r['target']==ctx and r['relationship_kind']=='contribution']
            if len(hit)!=1:raise ValueError('Roster needs one supported contribution: '+pid+'/'+ctx)
            r=hit[0];additions.append(dict(node=ctx,proposal_id=r['proposal_id'],row=dict(person_id=pid,role='contributor' if p['entry_type']=='Individual theorist' else 'historian',context=r['relationship'],works=s['works'],source_ids=r['source_ids'],basis='source_review')))
        write(out/pid/'entry-draft.json',dict(status='proposal_for_review',prepared=DAY,review_status='needs_independent_review',node=node,people_update=update,proposed_edges=edges,new_sources=src,source_addenda={},roster_additions=additions,edges_considered_not_proposed=[f'{k}: {v}' for k,v in s['contexts'].items() if not v.startswith('accept')]))
        existing=[dict(node=n['id'],rows=[r for r in n.get('representative_people',[]) if r['person_id']==pid]) for n in g['nodes'] if any(r['person_id']==pid for r in n.get('representative_people',[]))]
        cache=cached.get(p['qid']);birth=s.get('birth');death=s.get('death');life_sources=[]
        if not cache and p['qid'] in broad:
            raw=broad[p['qid']]
            if birth is None and raw['birth']:birth=int(raw['birth'].split('-')[0])
            if death is None and raw['death']:death=int(raw['death'].split('-')[0])
            life_sources.append(dict(url='https://www.wikidata.org/wiki/'+p['qid'],title='Prior local broad-scholar Wikidata assertion cache',locator=str(broadpath.relative_to(ROOT))+': '+p['qid'],support='Unreviewed cached assertions; this CSV does not preserve Wikidata precision, so only year is summarized. Not a fresh authority check or proof of present living status.',local_sha256=hashlib.sha256(broadpath.read_bytes()).hexdigest(),raw_date_evidence=raw,identity_review_status='unreviewed cached match; institutional professional identity checked separately'))
        if cache:
            if birth is None and cache['birth_dates']:birth=int(cache['birth_dates'].split('-')[0])
            if death is None and cache['death_dates']:death=int(cache['death_dates'].split('-')[0])
            life_sources.append(dict(url=cache['wikidata_url'],title='Prior local SPARQL date-evidence snapshot, 17 September 2026',locator=str(cachepath.relative_to(ROOT))+': '+p['qid'],support='Cached source assertions, not a fresh external authority check or proof of present living status.',local_sha256=hashlib.sha256(cachepath.read_bytes()).hexdigest(),raw_date_evidence=cache))
        life_sources.append(dict(url=s['life_url'],title='Checked professional or memorial witness',locator=s['life_locator'],support=s['life_note'],checked_on=DAY))
        status=s.get('status','deceased' if death else 'not_established')
        ls=dict(person_id=pid,label=p['name'],status=status,birth_year=birth,birth_precision='year' if birth else None,death_year=death,death_precision='year' if death else None,checked_on=DAY,sources=life_sources,limits='Cached assertions retain original precision and harvest review status below; year summary does not certify an exact day. Present life status uses the separately checked witness. No inference of living status from a missing death.',export_rule='Withhold birth year when no death is recorded unless born more than 120 years ago. Do not put such birth years in entry prose.')
        write(out/pid/'life-status.json',ls)
        write(out/pid/'research-notes.json',dict(person_id=pid,label=p['name'],selection=p,identity=dict(qid=p['qid'],origin='User queue; institutional professional identity and matching works checked',fresh_wikidata_check=False,limits='No live authority request or authority merge; existing cached SPARQL date assertions kept separately with their original provenance.'),existing_coverage=existing,existing_source_ids_reused=old,new_source_scopes=src,reading_limit=s['scope'],passage_checks=[dict(source_ids=r['source_ids'],locator_and_scope=r['evidence_note'],support=r['relationship']) for r in edges],context_decisions=s['contexts'],relations=edges,events=events,life_status_record=f'{pid}/life-status.json',reading_bridge_keys=p['keys_with_counted_works'],review_boundaries=s.get('review',[]),review_status='needs_independent_review'))
        for key in p['keys_with_counted_works']:bridge.append(dict(key=key,person_id=pid,entry_id=pid,work_leads=p['bibliography_leads'],namesake_qualification=p['note'],entry_draft=f'{pid}/entry-draft.json',counting_scope='Dated strict History PhDs, first-author works, 2026-10-30 queue build. Selection only, never influence evidence.'))
    deps=[f'data/extension-2026/timeline-canon-batch{i}-2026-10-31' for i in range(1,number)]
    write(out/'batch.json',dict(revision=rev,baseline_revision=f'1.{230+number}',date=DAY,batch_dir=f'person-entries-{rev}',persons=[p['person_id'] for p in queue],extras=[],unaccepted_dependencies=deps,
          summary=f'Add {len(queue)} individually sourced timeline entries with bounded contributions, criticism, additive contexts, selected publication milestones and separate life evidence.',authorization='User authorized continuation of SOL-BRIEF on 31 October. Research proposals only; Claude reviews and accepts each batch. No graph application, site build, commit or push.',rationale='Queue counts are selection evidence, never influence. Earlier IDs, prose, edges, sources and snapshots stay. Proposed contexts are reviewed individually; unread-evidence holds remain. OpenAlex stays paused.'))
    write(out/'reading-bridge.json',dict(schema='timeline_reading_bridge/1',status='proposal_for_review',source_queue=str(qpath.relative_to(ROOT)),rows=bridge))
    write(out/'research-notes.json',dict(status='proposal_for_review',baseline_revision=f'1.{230+number}',revision=rev,unaccepted_dependencies=deps,independent_review='Pending Claude acceptance; later baselines are simulations of preceding unaccepted releases, not production revisions.',source_policy='Authorized publisher, institutional, repository or author routes only. No denial bypasses. Prior reading is explicitly distinguished from fresh access.',life_policy='All life evidence remains separately sourced; birth years of people without recorded deaths stay out of entry prose.',reading_bridge='Every keys_with_counted_works value is listed, with namesake resolutions retained.'))
    manifest=json.loads((ROOT/'data/extension-2026/timeline-canon-batch1-2026-10-31/protected-manifest.json').read_text());write(out/'protected-manifest.json',manifest)
    runpy.run_path(str(HERE/'apply-quality-upgrades.py'),run_name='quality_upgrade')['apply_batch'](number)
    print('Prepared batch',number,len(queue),'entries; dependencies',deps)


if __name__=='__main__':main(int(sys.argv[1]))
