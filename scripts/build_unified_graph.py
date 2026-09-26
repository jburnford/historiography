#!/usr/bin/env python3
"""Build the unified Ladybug property graph from frozen local source inputs.

SQLite is used only as a disposable, bounded-memory staging index. The output
database and all graph queries use Ladybug; existing source databases are read-only.
"""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/unified-graph/generated'
WD = ROOT/'data/wikidata/historians-qlever-2026-09-17/historians-with-date-evidence.jsonl.gz'
VERSION = '1.1'
BUFFER_MIB = 512


def serial(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def key(label):
    return unicodedata.normalize('NFC',' '.join((label or '').split())).casefold()


def uid(prefix,*parts):
    return prefix+hashlib.sha256(serial(parts).encode()).hexdigest()[:24]


def hnet_id(value):
    # H-Net's atlas reference nodes describe pointers, not additional people.
    return 'hnet:reference:'+value if value.startswith('atlas:') else value


class Stage:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.executescript('''
          PRAGMA cache_size=-16384; PRAGMA temp_store=FILE;
          CREATE TABLE nodes(id TEXT PRIMARY KEY,kind TEXT,label TEXT,name_key TEXT,origin TEXT,data TEXT);
          CREATE INDEX node_kind ON nodes(kind);
          CREATE INDEX node_name ON nodes(name_key,kind);
          CREATE TABLE links(subject TEXT,object TEXT,id TEXT PRIMARY KEY,predicate TEXT,origin TEXT,
                             status TEXT,directed TEXT,evidence TEXT,data TEXT);
          CREATE INDEX link_subject ON links(subject,predicate);
          CREATE INDEX link_object ON links(object,predicate);
          CREATE TABLE names(id TEXT,name_key TEXT,origin TEXT,PRIMARY KEY(id,name_key));
          CREATE INDEX names_key ON names(name_key,origin);
          CREATE TABLE issues(code TEXT,record_id TEXT,detail TEXT);
        ''')

    def node(self,nid,kind,label,origin,data):
        self.db.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?)',(nid,kind,label,key(label),origin,serial(data)))
        if kind in ('person','wikidata_item','name_candidate'):
            self.name(nid,label,origin)
        return nid

    def name(self,nid,label,origin):
        if label:
            self.db.execute('INSERT OR IGNORE INTO names VALUES(?,?,?)',(nid,key(label),origin))

    def exists(self,nid):
        return self.db.execute('SELECT 1 FROM nodes WHERE id=?',(nid,)).fetchone() is not None

    def edge(self,subject,predicate,obj,origin,status='source_recorded',evidence=(),data=None,eid=None,directed=True):
        eid=eid or uid('unified:edge:',subject,predicate,obj,origin)
        self.db.execute('INSERT INTO links VALUES(?,?,?,?,?,?,?,?,?)',
                        (subject,obj,eid,predicate,origin,status,str(bool(directed)).lower(),serial(evidence),serial(data or {})))

    def issue(self,code,record,detail):
        self.db.execute('INSERT INTO issues VALUES(?,?,?)',(code,record,detail))


def import_atlas(s,atlas):
    s.node('source:atlas','source_record','Teaching atlas revision 1.123','atlas',
           {k:v for k,v in atlas.items() if k not in ('nodes','edges','people','sources','journal_catalogue','claim_catalogue')})
    for record in atlas.get('sources',[]):
        s.node('atlas:source:'+record['id'],'source_record',record.get('title',record['id']),'atlas',record)
    for person in atlas['people']:
        s.node('atlas:person:'+person['id'],'person',person['label'],'atlas',person)
    for node in atlas['nodes']:
        nid='atlas:entry:'+node['id']
        s.node(nid,'atlas_entry',node['label'],'atlas',node)
        for position,selection in enumerate(node.get('representative_people',[])):
            s.edge(nid,'selects_person','atlas:person:'+selection['person_id'],'atlas','curated_selection',
                   ['atlas:source:'+sid for sid in selection.get('source_ids',[])],selection,
                   eid=uid('atlas:selection:',node['id'],position,selection['person_id']))
        for strand in node.get('strands',[]):
            strand_id='atlas:strand:'+node['id']+'/'+strand['id']
            s.node(strand_id,'atlas_strand',strand.get('title',strand['id']),'atlas',strand)
            s.edge(nid,'has_strand',strand_id,'atlas','curated_structure',['source:atlas'])
            for person in strand.get('person_ids',[]):
                s.edge(strand_id,'contextual_person','atlas:person:'+person,'atlas','curated_selection',
                       ['atlas:source:'+sid for sid in strand.get('source_ids',[])],
                       {'qualification':'Contextual selection, not school membership.'})
    for person in atlas['people']:
        if person.get('node_id'):
            s.edge('atlas:entry:'+person['node_id'],'presents_person','atlas:person:'+person['id'],
                   'atlas','accepted_local_reference',['source:atlas'])
    for edge in atlas['edges']:
        s.edge('atlas:entry:'+edge['source'],'historical_'+edge['relationship_kind'],
               'atlas:entry:'+edge['target'],'atlas',edge.get('review_status','curated'),
               ['atlas:source:'+sid for sid in edge.get('source_ids',[])],edge,
               eid='atlas:'+edge['id'],directed=edge.get('directed',True))
    catalogue=atlas.get('claim_catalogue',{})
    for record in catalogue.get('source_records',[]):
        s.node('atlas:witness:'+record['id'],'source_record',record.get('provider',record['id']),'atlas',record)
    for entity in catalogue.get('entities',[]):
        nid='atlas:catalogue:'+entity['id']
        s.node(nid,'catalogue_'+entity['type'],entity['label'],'atlas',entity)
        targets=[]
        if entity.get('legacy_person_id'):
            targets.append(('local_person_reference','atlas:person:'+entity['legacy_person_id']))
        if entity.get('node_id'):
            targets.append(('local_entry_reference','atlas:entry:'+entity['node_id']))
        if entity.get('legacy_entry_id'):
            targets.append(('entry_context','atlas:entry:'+entity['legacy_entry_id']))
        if entity.get('legacy_strand_address'):
            targets.append(('strand_context','atlas:strand:'+entity['legacy_strand_address']))
        for predicate,target in targets:
            if s.exists(target):
                s.edge(nid,predicate,target,'atlas','accepted_local_reference',['source:atlas'],
                       {'qualification':entity.get('qualification')})
            else:
                s.issue('unresolved_legacy_reference',nid,target)
    for claim in catalogue.get('claims',[]):
        s.edge('atlas:catalogue:'+claim['subject'],'claim_'+claim['predicate'],
               'atlas:catalogue:'+claim['object'],'atlas',claim.get('review',{}).get('status','needs_review'),
               ['atlas:witness:'+e['source_record_id'] for e in claim.get('evidence',[])],claim,
               eid='atlas:'+claim['id'])
    journal=atlas.get('journal_catalogue',{})
    for record in journal.get('sources',[]):
        s.node('atlas:journal_source:'+record['id'],'source_record',record.get('title',record['id']),'atlas',record)
    for node in journal.get('nodes',[]):
        s.node('atlas:journal:'+node['id'],node['entry_kind'],node['label'],'atlas',node)
    for edge in journal.get('edges',[]):
        s.edge('atlas:journal:'+edge['source'],edge['relationship_kind'],'atlas:entry:'+edge['target'],
               'atlas','curated',['atlas:journal_source:'+i for i in edge.get('source_ids',[])],edge,
               eid='atlas:'+edge['id'])
    for row in journal.get('subject_classifications',[]):
        subject='atlas:journal:'+row['subject_id']
        if not s.exists(subject):
            subject='atlas:entry:'+row['subject_id']
        s.edge('atlas:journal:'+row['journal_id'],'classified_under',subject,
               'atlas',row.get('status','source_recorded'),
               ['atlas:journal_source:'+i for i in row.get('source_ids',[])],row,eid='atlas:'+row['id'])
    for row in journal.get('title_relationships',[]):
        s.edge('atlas:journal:'+row['predecessor'],'title_successor','atlas:journal:'+row['successor'],
               'atlas','source_recorded',['atlas:journal_source:'+i for i in row.get('source_ids',[])],row,
               eid='atlas:'+row['id'])


def import_hnet(s,path):
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        for row in db.execute('SELECT * FROM sources ORDER BY id'):
            record=dict(row)
            s.node(row['id'],'source_record',row['relative_path'],'hnet',record)
        for row in db.execute('SELECT * FROM nodes ORDER BY id'):
            props=json.loads(row['properties'])
            props['original_id']=row['id']
            table={'review_record':'reviews','person_mention':'mentions','reviewed_item':'items','bibliographic_item':'items'}.get(row['kind'])
            if table:
                extra=db.execute(f'SELECT * FROM {table} WHERE id=?',(row['id'],)).fetchone()
                if extra:
                    props['metadata']=dict(extra)
                if table=='mentions':
                    record=db.execute('SELECT r.source_id,s.json_sha256 FROM reviews r JOIN sources s ON s.id=r.source_id WHERE r.id=?',(extra['review_id'],)).fetchone()
                    props['source_record_id']=record['source_id']
                    props['source_json_sha256']=record['json_sha256']
            nid=hnet_id(row['id'])
            s.node(nid,row['kind'],row['label'],'hnet',props)
            target=None
            if row['kind']=='atlas_person_reference':
                target='atlas:person:'+props['atlas_person_id'];predicate='local_person_reference'
            elif row['kind']=='atlas_field_reference':
                target='atlas:entry:'+props['atlas_field_id'];predicate='local_entry_reference'
            if target:
                if not s.exists(target):
                    raise ValueError('H-Net references an unknown atlas identity: '+target)
                s.edge(nid,predicate,target,'hnet','accepted_local_reference',[],
                       {'basis':'Explicit existing atlas ID, not a name match.'})
        for row in db.execute('SELECT * FROM edges ORDER BY id'):
            s.edge(hnet_id(row['subject']),row['predicate'],hnet_id(row['object']),'hnet',row['status'],
                   [row['source_id']] if row['source_id'] else [],json.loads(row['properties']),eid=row['id'])
        for row in db.execute('SELECT * FROM issues'):
            s.issue('hnet:'+row['code'],row['source_id'],row['detail'])


def import_wikidata(s,path):
    source='source:wikidata:historians'
    s.node(source,'source_record','Wikidata historian discovery extraction, 2026-09-17','wikidata',
           {'path':str(path),'sha256':sha(path),'scope':'Exact P106=Q201788; no human-instance filter. Dates and occupation statements retained as reported, not independently verified. Statement references were not downloaded.'})
    s.node('wd:Q201788','wikidata_concept','historian','wikidata',{'qid':'Q201788'})
    with gzip.open(path,'rt') as handle:
        for i,line in enumerate(handle,1):
            row=json.loads(line);nid='wd:'+row['qid']
            s.node(nid,'wikidata_item',row['label'],'wikidata',row)
            for field in ('label_en','label_mul'):
                s.name(nid,row.get(field),'wikidata')
            for statement in row.get('occupation_statements',[]):
                rank=statement.get('rank','unknown')
                s.edge(nid,'occupation','wd:Q201788','wikidata','deprecated' if rank=='deprecated' else 'source_recorded',
                       [source],statement,eid='wd:statement:'+statement['uri'].rsplit('/',1)[-1])
            for person in row.get('atlas_person_match_candidates',[]):
                target='atlas:person:'+person
                if s.exists(target):
                    s.edge(nid,'candidate_atlas_identity',target,'wikidata','candidate_only',[source],
                           {'basis':'Preserved unreviewed name match from original Wikidata extraction.'})
            if i%25000==0:
                s.db.commit();print(f'Imported {i} Wikidata records',flush=True)


def import_authorities(s,people,fields):
    for source,label,rows in [('source:authority:people','Accepted atlas person identities',people),
                              ('source:authority:fields','Atlas field correspondences',fields)]:
        s.node(source,'source_record',label,'authority',rows)
    seen_qids={}
    for row in people.get('people',[]):
        if row['status']!='accepted':
            continue
        person='atlas:person:'+row['person_id'];qid=row['wikidata']['qid'];target='wd:'+qid
        if not s.exists(person):
            raise ValueError('Authority sheet references missing person '+person)
        if qid in seen_qids and seen_qids[qid]!=person:
            raise ValueError('Conflicting accepted identities for '+qid)
        seen_qids[qid]=person
        if not s.exists(target):
            s.node(target,'wikidata_item',row['wikidata']['label'],'wikidata',
                   {'qid':qid,'authority_sheet_only':True,'wikidata':row['wikidata']})
        s.edge(person,'same_person',target,'authority','accepted',['source:authority:people'],row)
    for row in fields.get('entries',[]):
        if row['status']!='accepted':
            continue
        entry='atlas:entry:'+row['node_id'];target='wd:'+row['wikidata']['qid']
        if not s.exists(entry):
            raise ValueError('Authority sheet references missing field '+entry)
        if not s.exists(target):
            s.node(target,'wikidata_concept',row['wikidata']['label'],'wikidata',row['wikidata'])
        predicates={'same_concept':'maps_to_same_concept','broader_concept':'maps_to_broader_concept'}
        predicate=predicates[row['match_kind']]
        s.edge(entry,predicate,target,'authority','accepted',['source:authority:fields'],row)


def candidates(s):
    # Candidate generation never writes an accepted identity. Equal labels can
    # produce several different QIDs. Do not collapse them or select the first.
    rows=s.db.execute('''SELECT DISTINCT h.id,w.id FROM nodes h JOIN names w ON w.name_key=h.name_key
       WHERE h.kind='name_candidate' AND w.origin='wikidata' ORDER BY h.id,w.id''')
    for hn,wd in rows:
        s.edge(hn,'candidate_wikidata_identity',wd,'reconciliation','candidate_only',
               ['source:wikidata:historians'],{'basis':'Equal normalized label; not a resolved person.'})
    rows=s.db.execute('''SELECT a.id,h.id FROM nodes a JOIN nodes h ON a.name_key=h.name_key
       WHERE a.kind='catalogue_work' AND h.kind IN ('bibliographic_item','reviewed_item') ORDER BY a.id,h.id''')
    for work,item in rows:
        s.edge(item,'candidate_publication_of',work,'reconciliation','candidate_only',[],
               {'basis':'Exact normalized title only; authorship, work identity and edition need review.'})


def identity_decisions(s,policy):
    s.node('source:identity-decisions','source_record','Reviewed unified identity decisions','reconciliation',policy)
    for person in policy.get('people',[]):
        s.node('unified:person:'+person['id'],'person',person['label'],'reconciliation',person)
    assigned=set()
    for decision in policy.get('decisions',[]):
        mid=decision['occurrence_id'];pid=decision['person_id']
        row=s.db.execute('SELECT kind,data FROM nodes WHERE id=?',(mid,)).fetchone()
        target=s.db.execute('SELECT kind FROM nodes WHERE id=?',(pid,)).fetchone()
        if not row or row[0]!='person_mention' or not target or target[0]!='person':
            raise ValueError('Invalid identity decision endpoints')
        props=json.loads(row[1])
        if props.get('source_json_sha256')!=decision['source_json_sha256']:
            raise ValueError('Stale identity source fingerprint')
        if props.get('source_raw_sha256') and props['source_raw_sha256']!=decision.get('source_raw_sha256'):
            raise ValueError('Stale or missing identity raw source fingerprint')
        if not decision.get('rationale') or not decision.get('evidence'):
            raise ValueError('Identity decision requires rationale and evidence')
        if decision['status']=='accepted':
            if mid in assigned:
                raise ValueError('Occurrence assigned to multiple people')
            assigned.add(mid);predicate='resolved_as'
        elif decision['status']=='rejected':
            predicate='rejected_identity'
        else:
            raise ValueError('Unknown identity decision status')
        s.edge(mid,predicate,pid,'reconciliation',decision['status'],
               ['source:identity-decisions',props['source_record_id']],decision,
               eid='unified:decision:'+decision['id'])


def validate_stage(s):
    missing=s.db.execute('''SELECT l.id FROM links l LEFT JOIN nodes a ON a.id=l.subject
        LEFT JOIN nodes b ON b.id=l.object WHERE a.id IS NULL OR b.id IS NULL LIMIT 5''').fetchall()
    if missing:
        raise ValueError('Dangling graph endpoints: '+repr(missing))
    missing=s.db.execute('''SELECT l.id,j.value FROM links l,json_each(l.evidence) j
        LEFT JOIN nodes n ON n.id=j.value WHERE n.id IS NULL LIMIT 5''').fetchall()
    if missing:
        raise ValueError('Missing evidence records: '+repr(missing))
    if s.db.execute("SELECT 1 FROM links WHERE predicate LIKE 'candidate_%' AND status!='candidate_only' LIMIT 1").fetchone():
        raise ValueError('Candidate promoted without review')
    return {'dangling_endpoints':0,'missing_evidence':0,'candidate_status_errors':0}


def write_csv(s,dest):
    queries={'nodes.csv':'SELECT * FROM nodes ORDER BY id','links.csv':'SELECT * FROM links ORDER BY id',
             'issues.csv':'SELECT * FROM issues ORDER BY code,record_id,detail',
             'identity-review-seeds.csv':'''SELECT n.label AS person,p.id AS person_id,w.id AS wikidata_id,
                 c.id AS name_candidate_id,c.label AS recorded_name FROM links a
                 JOIN nodes p ON p.id=a.subject JOIN nodes w ON w.id=a.object
                 JOIN links b ON b.object=p.id AND b.predicate='local_person_reference'
                 JOIN links d ON d.object=b.subject AND d.predicate='candidate_atlas_identity'
                 JOIN nodes c ON c.id=d.subject JOIN nodes n ON n.id=p.id
                 WHERE a.predicate='same_person' AND a.status='accepted'
                 ORDER BY p.id,c.id'''}
    for filename,sql in queries.items():
        cur=s.db.execute(sql)
        with (dest/filename).open('w',newline='') as handle:
            writer=csv.writer(handle);writer.writerow([x[0] for x in cur.description]);writer.writerows(cur)


def connect_ladybug(path,read_only=True,buffer_mib=BUFFER_MIB):
    import ladybug
    db=ladybug.Database(str(path),buffer_pool_size=buffer_mib*1024*1024,max_num_threads=1,read_only=read_only)
    return db,ladybug.Connection(db,num_threads=1)


def ladybug_import(dest,buffer_mib,chunk_rows=25000):
    import ladybug
    db,conn=connect_ladybug(dest/'graph.lbdb',False,buffer_mib)
    try:
        conn.execute('CREATE NODE TABLE Entity(id STRING PRIMARY KEY,kind STRING,label STRING,name_key STRING,origin STRING,data STRING)').close()
        conn.execute('CREATE REL TABLE Link(FROM Entity TO Entity,id STRING,predicate STRING,origin STRING,status STRING,directed BOOLEAN,evidence STRING,data STRING)').close()
        for table,filename in [('Entity','nodes.csv'),('Link','links.csv')]:
            print('Loading Ladybug '+table,flush=True)
            # Bound each COPY transaction and checkpoint between batches so
            # growth in corpus size does not require an ever larger buffer.
            csv.field_size_limit(32*1024*1024)
            chunk=dest/'import-chunk.csv'
            from itertools import islice
            with (dest/filename).open(newline='') as handle:
                reader=csv.reader(handle);header=next(reader)
                while True:
                    batch=list(islice(reader,chunk_rows))
                    if not batch:break
                    with chunk.open('w',newline='') as output:
                        writer=csv.writer(output);writer.writerow(header);writer.writerows(batch)
                    del batch
                    path=str(chunk).replace('\\','\\\\').replace("'","\\'")
                    conn.execute(f'''COPY {table} FROM '{path}' (HEADER=true, ESCAPE='"')''').close()
                    conn.execute('CHECKPOINT').close()
            chunk.unlink()
        counts={}
        for name,query in [('nodes','MATCH (n:Entity) RETURN count(n)'),('links','MATCH ()-[r:Link]->() RETURN count(r)')]:
            result=conn.execute(query);counts[name]=result.get_next()[0];result.close()
        conn.execute('CHECKPOINT').close()
        return ladybug.__version__,counts
    finally:
        conn.close();db.close()


def build(atlas_path,hnet_path,wd_path,people_path,fields_path,decisions_path,out,buffer_mib=BUFFER_MIB,rih_path=None):
    paths=dict(atlas=atlas_path,hnet=hnet_path,wikidata=wd_path,people_authority=people_path,
               field_authority=fields_path,identity_decisions=decisions_path)
    hashes={name:sha(path) for name,path in paths.items()}
    # Require the H-Net snapshot manifest to match if present, including its
    # atlas baseline. Do not silently consume a partially rebuilt source graph.
    manifest=hnet_path.parent/'summary.json'
    if manifest.exists():
        hnet_summary=json.loads(manifest.read_text())
        if hnet_summary['files']['graph.sqlite']!=hashes['hnet']:
            raise ValueError('H-Net database differs from its completed snapshot manifest')
        if hnet_summary['atlas_sha256']!=hashes['atlas']:
            raise ValueError('H-Net atlas references need review against changed atlas input')
    out=out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix='.unified-build-',dir=out.parent) as tmp:
        dest=Path(tmp);s=Stage(dest/'staging.sqlite')
        print('Importing atlas',flush=True);import_atlas(s,json.loads(atlas_path.read_text()))
        print('Importing H-Net snapshot',flush=True);import_hnet(s,hnet_path);s.db.commit()
        rih_counts=None
        if rih_path is not None:
            try:
                from . import import_reviews_in_history as rih
            except ImportError:
                import import_reviews_in_history as rih
            print('Importing Reviews in History',flush=True)
            rih_counts=rih.import_corpus(s,rih_path,dest/'rih-inputs.csv')
            rih.reconcile(s);s.db.commit()
        print('Importing Wikidata snapshot',flush=True);import_wikidata(s,wd_path)
        import_authorities(s,json.loads(people_path.read_text()),json.loads(fields_path.read_text()))
        candidates(s);identity_decisions(s,json.loads(decisions_path.read_text()));s.db.commit()
        validation=validate_stage(s)
        counts={'nodes':s.db.execute('SELECT count(*) FROM nodes').fetchone()[0],
                'links':s.db.execute('SELECT count(*) FROM links').fetchone()[0],
                'node_kinds':dict(s.db.execute('SELECT kind,count(*) FROM nodes GROUP BY kind')),
                'predicates':dict(s.db.execute('SELECT predicate,count(*) FROM links GROUP BY predicate')),
                'link_statuses':dict(s.db.execute('SELECT status,count(*) FROM links GROUP BY status')),
                'origins':dict(s.db.execute('SELECT origin,count(*) FROM nodes GROUP BY origin'))}
        print('Exporting portable graph tables',flush=True);write_csv(s,dest);s.db.close()
        version,actual=ladybug_import(dest,buffer_mib)
        if actual!={k:counts[k] for k in ('nodes','links')}:
            raise ValueError('Ladybug import counts differ from validated staging graph')
        for name,path in paths.items():
            if sha(path)!=hashes[name]:
                raise ValueError('Source changed during build: '+name)
        files=['graph.lbdb','nodes.csv','links.csv','issues.csv','identity-review-seeds.csv']
        if rih_path is not None:
            rih.verify_inventory(rih_path,dest/'rih-inputs.csv')
            files.append('rih-inputs.csv')
        report=dict(schema_version=VERSION,backend='ladybug',backend_version=version,started_at=started,
                    built_at=datetime.now(timezone.utc).isoformat(),buffer_mib=buffer_mib,threads=1,
                    inputs={name:{'path':str(path.resolve()),'sha256':hashes[name]} for name,path in paths.items()},
                    builder_sha256=sha(Path(__file__)),counts=counts,validation=validation,
                    files={name:sha(dest/name) for name in files},
                    scope='Unified source graph; no H-Net review-argument analysis and no automatic person merges.')
        if rih_path is not None:
            report['reviews_in_history']=dict(path=str(rih_path.resolve()),counts=rih_counts,
                                             adapter_sha256=sha(Path(rih.__file__)))
        (dest/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        out.mkdir(parents=True,exist_ok=True)
        for filename in files+['summary.json']:
            (dest/filename).replace(out/filename)
    return report


def check(out):
    report=json.loads((out/'summary.json').read_text())
    for filename,expected in report['files'].items():
        if sha(out/filename)!=expected:
            raise ValueError('Generated output changed: '+filename)
    db,conn=connect_ladybug(out/'graph.lbdb')
    try:
        for table,pattern in [('nodes','(n:Entity)'),('links','()-[n:Link]->()')]:
            result=conn.execute(f'MATCH {pattern} RETURN count(n)')
            if result.get_next()[0]!=report['counts'][table]:
                raise ValueError('Graph count mismatch: '+table)
            result.close()
    finally:
        conn.close();db.close()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas',type=Path,default=ROOT/'historiography-1920-2000.json')
    p.add_argument('--hnet',type=Path,default=ROOT/'data/hnet-graph/generated/graph.sqlite')
    p.add_argument('--wikidata',type=Path,default=WD)
    p.add_argument('--people-authority',type=Path,default=ROOT/'data/people-wikidata.json')
    p.add_argument('--field-authority',type=Path,default=ROOT/'data/entries-wikidata.json')
    p.add_argument('--decisions',type=Path,default=ROOT/'data/unified-graph/identity-decisions.json')
    p.add_argument('--rih',type=Path,default=Path('/home/jic823/hnet-reviews/data/rih'))
    p.add_argument('--without-rih',action='store_true',help='Reproduce the earlier three-source scope')
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--buffer-mib',type=int,default=BUFFER_MIB)
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    if not 64<=a.buffer_mib<=1024:p.error('--buffer-mib must be between 64 and 1024')
    report=check(a.out) if a.check else build(a.atlas,a.hnet,a.wikidata,a.people_authority,a.field_authority,a.decisions,a.out,a.buffer_mib,None if a.without_rih else a.rih)
    print(json.dumps(report['counts'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
