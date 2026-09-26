#!/usr/bin/env python3
"""Frozen, occurrence-level grounding repair; never writes to the upstream corpus.

The reviewed ledger is the authority. Names only select a pilot / suggest legacy
IDs. Existing graph extractors provide stable occurrence IDs and source locators.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import duckdb

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'data/grounding-repair'
PILOT = {'peter schafer','jorg arnold','anika walke','julia angster','guido muller',
         'r b bernstein','sumit ganguly','michael mann','ute schneider','mark harrison'}


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def key(name):
    name = re.sub(r'^(?:(?:Dr|Prof|Professor)\.?\s+)+', '', name or '', flags=re.I)
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z\s]', ' ', name).split())


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(db, query, params=None):
    result = db.execute(query, params or [])
    names = [c[0] for c in result.description]
    return [dict(zip(names, r)) for r in result.fetchall()]


def row_hashes(db, table, columns, params=None):
    """Compare all content without materializing/spilling full review bodies."""
    fields=','.join('"'+n+'" := "'+n+'"' for n in columns)
    result=db.execute('SELECT source,era,review_id,sha256(to_json(struct_pack('+fields+'))) FROM '+table,params or []).fetchall()
    hashes={tuple(r[:3]):r[3] for r in result}
    if len(hashes)!=len(result):raise ValueError('Duplicate catalog key during validation')
    return hashes


def record_key(row):
    return tuple(row[k] for k in ('source','era','review_id'))


def freeze(upstream, work):
    frozen = work / 'generated/frozen'
    if frozen.exists():
        raise ValueError('Frozen input already exists; use a new work directory')
    frozen.mkdir(parents=True)
    # Holding the read-only connection prevents a concurrent DuckDB writer.
    with duckdb.connect(str(upstream/'data/export/catalog.duckdb'), read_only=True) as c:
        before = sha(upstream/'data/export/catalog.duckdb')
        shutil.copy2(upstream/'data/export/catalog.duckdb', frozen/'catalog.duckdb')
        if sha(frozen/'catalog.duckdb') != before:
            raise ValueError('Catalog changed while copying')
        catalog = rows(c, 'SELECT * EXCLUDE(body_text,author_response) FROM reviews')
    if len({record_key(r) for r in catalog}) != len(catalog):
        raise ValueError('Non-unique source/era/review_id catalog keys')
    shutil.copytree(upstream/'data/grounding', frozen/'grounding')
    code = frozen/'code';code.mkdir()
    for name in ('ground_local.py','integrate_grounding.py'):
        shutil.copy2(upstream/name, code/name)
    for name in ('build_hnet_graph.py','import_reviews_in_history.py'):
        shutil.copy2(ROOT/'scripts'/name, code/name)
    audit=json.loads((ROOT/'data/grounding-audit-2026-09-21/candidates.json').read_text())
    write_json(frozen/'mcp-overlay-order.json',[Path(r['path']).name for r in audit['inputs'] if '/mcp_results/' in r['path']])
    legacy = load_module(code/'ground_local.py', 'frozen_ground_local')
    hnet = load_module(code/'build_hnet_graph.py', 'frozen_hnet')
    selected = []
    for row in catalog:
        authors = row.get('book_author') or ''
        names = legacy.split_authors(authors) + [n for n,_ in hnet.split_credit(authors)[0]]
        if key(row.get('reviewer')) in PILOT or any(key(n) in PILOT for n in names):
            selected.append(row)
    for row in selected:
        rid, era = row['review_id'], row['era']
        for rel in ([f'rih/json/{rid}.json',f'rih/html/{rid}.html.gz'] if row['source']=='reviews_in_history'
                    else [f'json/{era}/{rid}.json',f'html/{era}/{rid}.html.gz']):
            src=upstream/'data'/rel; dst=frozen/'corpus'/rel
            if not src.exists():
                raise ValueError('Missing source '+str(src))
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
            if rel.endswith('.json'):
                record=json.loads(dst.read_text())
                for field in ('reviewer','reviewer_affiliation','book_author','book_title'):
                    if (record.get(field) or '')!=(row.get(field) or ''):
                        raise ValueError('Catalog/source disagreement: '+rid+' '+field)
    write_json(frozen/'catalog-selection.json', selected)
    files=[{'path':str(p.relative_to(frozen)), 'sha256':sha(p)} for p in sorted(frozen.rglob('*')) if p.is_file()]
    manifest={'schema_version':'1.0','upstream':str(upstream),'catalog_rows':len(catalog),
              'selected_rows':len(selected),'catalog_sha256':before,'files':files,
              'scope':'Ten normalized pilot names selected from catalog reviewer and author fields; not all uncatalogued HTML credits.'}
    write_json(work/'baseline-manifest.json',manifest)
    print('Frozen',len(selected),'pilot catalog rows from',len(catalog))


def verify_frozen(work):
    manifest=json.loads((work/'baseline-manifest.json').read_text())
    frozen=work/'generated/frozen'
    for f in manifest['files']:
        p=frozen/f['path']
        if not p.is_file() or sha(p)!=f['sha256']:
            raise ValueError('Stale frozen input: '+f['path'])
    return frozen,manifest


def legacy_maps(frozen):
    maps={}; histories={}
    for role in ('reviewer','author'):
        for r in csv.DictReader((frozen/'grounding'/f'{role}_grounding.csv').open()):
            maps[role,r['name']]=r['qid'] if r['status']=='matched' else None
            histories[role,r['name']]=[dict(r,file=f'{role}_grounding.csv')]
    # Frozen order from the original audit (glob order is not an authority).
    # Prefer the order recorded in the audit; validate reconstruction below.
    order=json.loads((frozen/'mcp-overlay-order.json').read_text())
    actual={p.name for p in (frozen/'grounding/mcp_results').glob('*.csv')}
    if actual!=set(order):
        raise ValueError('MCP input set changed; review overlay ordering before freezing decisions')
    for name in order:
        for r in csv.DictReader((frozen/'grounding/mcp_results'/name).open()):
            role='reviewer' if r['role']=='reviewer' else 'author'
            histories.setdefault((role,r['name']),[]).append(dict(r,file='mcp_results/'+name))
            if r['decided_qid'] and r['decided_qid']!='none' and r['confidence']!='low':
                maps[role,r['name']]=r['decided_qid']
    return maps,histories


class Collector:
    """Minimal sink for the existing RiH credit extractor."""
    def __init__(self): self.nodes={}
    def exists(self,nid): return nid in self.nodes
    def node(self,nid,kind,label,origin,data): self.nodes[nid]=(kind,label,data)
    def edge(self,*args,**kwargs): pass
    def issue(self,*args,**kwargs): pass


def extract(work):
    frozen,manifest=verify_frozen(work)
    sys.path.insert(0,str(frozen/'code'))
    # Existing imports retain graph ID algorithms, without importing the native DB.
    import build_hnet_graph as hnet
    import import_reviews_in_history as rih
    legacy=load_module(frozen/'code/ground_local.py','frozen_legacy')
    maps,histories=legacy_maps(frozen)
    catalog=json.loads((frozen/'catalog-selection.json').read_text())
    graph=hnet.Graph(':memory:')
    result=[]; issues=[]
    for row in catalog:
        source,era,rid=record_key(row)
        oldnames=legacy.split_authors(row.get('book_author') or '')
        oldqids=[maps.get(('author',n)) for n in oldnames]
        if ('|'.join(q for q in oldqids if q) or None)!=(row['author_qids'] or None):
            raise ValueError('Legacy author reconstruction mismatch: '+rid)
        if maps.get(('reviewer',row.get('reviewer')))!=(row['reviewer_qid'] or None):
            raise ValueError('Legacy reviewer reconstruction mismatch: '+rid)
        base={'source':source,'era':era,'review_id':rid,'catalog_fingerprint':digest(row),
              'catalog_title':row.get('book_title'),'catalog_is_real':row['is_real']}
        if source=='hnet':
            jp=frozen/'corpus/json'/era/f'{rid}.json';hp=frozen/'corpus/html'/era/f'{rid}.html.gz'
            hnet.load_source(graph,frozen/'corpus',jp)
            graph.db.row_factory=sqlite3.Row
            data=graph.db.execute('''SELECT m.*,n.properties,i.title AS item_title,e.properties AS credit_properties
              FROM mentions m JOIN nodes n ON n.id=m.id LEFT JOIN items i ON i.id=m.item_id
              JOIN edges e ON e.object=m.id AND e.predicate IN ('reviewed_by','credited_to')
              WHERE m.review_id=? ORDER BY m.id''',('hnet:review:'+era+':'+rid,)).fetchall()
            for r in data:
                r=dict(r); props=json.loads(r.pop('properties')); cp=json.loads(r.pop('credit_properties'))
                result.append(dict(base,occurrence_id=r.pop('id'),source_record_id=f'hnet:source:{era}:{rid}',
                  source_json_sha256=sha(jp),source_raw_sha256=hashlib.sha256(gzip.decompress(hp.read_bytes())).hexdigest(),
                  source_raw_file_sha256=sha(hp),json_path=str(jp.relative_to(frozen)),raw_path=str(hp.relative_to(frozen)),
                  name=r['name'],role=r['role'],item_id=r['item_id'],item_title=r['item_title'],
                  locator=r['locator'],position=props['credit_position'],affiliation=r['affiliation'],
                  raw_credit=cp['raw_credit']))
        else:
            jp=frozen/'corpus/rih/json'/f'{rid}.json';hp=frozen/'corpus/rih/html'/f'{rid}.html.gz'
            header=rih.parse_header(gzip.decompress(hp.read_bytes()).decode('utf-8'))
            if not header: raise ValueError('Unrecognized RiH header '+rid)
            sink=Collector();review='rih:review:'+rid;sid='rih:source:'+rid
            rih.add_credit(sink,header['reviewer'],review,sid,sha(jp),'.view-display-id-reviewer',
                           affiliation=header['affiliation'],reviewer=True,raw_fingerprint=sha(hp))
            for i,b in enumerate(header['books'],1):
                rih.add_credit(sink,b['credit'],review,sid,sha(jp),f'.view-display-id-summary block {i}',
                               item_id=f'rih:item:{rid}:{i}',raw_fingerprint=sha(hp))
            for mid,(kind,label,data) in sink.nodes.items():
                if kind!='person_mention':continue
                m=data['metadata'];item=m['item_id'];book=header['books'][int(item.rsplit(':',1)[1])-1] if item else None
                result.append(dict(base,occurrence_id=mid,source_record_id=sid,source_json_sha256=sha(jp),
                  source_raw_sha256=sha(hp),source_raw_file_sha256=sha(hp),json_path=str(jp.relative_to(frozen)),raw_path=str(hp.relative_to(frozen)),
                  name=label,role=m['role'],item_id=item,item_title=book['title'] if book else None,
                  locator=m['locator'],position=None,affiliation=m['affiliation'],raw_credit=data['recorded_credit']))
        current=[o for o in result if record_key(o)==record_key(row)]
        for o in current:
            o['display_name']=o['name']
            o['name_preparation']='unchanged'
            if o['role']!='reviewer' and o['name'].startswith('and ') and ', and '+o['name'][4:] in o['raw_credit']:
                o['display_name']=o['name'][4:]
                o['name_preparation']='Removed conjunction after explicit comma-and list delimiter; original name and graph ID retained.'
            o['pilot']=key(o['display_name']) in PILOT
            if o['role']=='reviewer':
                o['legacy_qid']=row['reviewer_qid'];o['legacy_status']=row['reviewer_wd_status']
                o['legacy_names']=[row['reviewer']]
            else:
                # Only transfer an original stored author QID when its name is
                # uniquely associated with the exact catalog book credit.
                hits=[n for n in oldnames if key(n)==key(o['display_name'])]
                o['legacy_names']=hits
                o['legacy_qid']=maps.get(('author',hits[0])) if len(hits)==1 else None
                o['legacy_status']='legacy_unreviewed' if o['legacy_qid'] else 'unmatched_or_unaligned'
            o['legacy_evidence']=[h for n in o['legacy_names'] for h in histories.get(('reviewer' if o['role']=='reviewer' else 'author',n),[])]
            o['occurrence_fingerprint']=digest({k:v for k,v in o.items() if k!='legacy_evidence'})
        for raw_role,raw_name in [('reviewer',row.get('reviewer')), *[('author',n) for n in oldnames]]:
            if key(raw_name) in PILOT and not any(key(o['display_name'])==key(raw_name) and (o['role']=='reviewer')==(raw_role=='reviewer') for o in current):
                issues.append({'source':source,'era':era,'review_id':rid,'role':raw_role,'name':raw_name,'issue':'Pilot catalog credit not recovered as a source person occurrence'})
    graph.db.close()
    result.sort(key=lambda o:o['occurrence_id'])
    write_json(work/'occurrences.json',result);write_json(work/'extraction-issues.json',issues)
    print('Extracted',len(result),'credits;',sum(o['pilot'] for o in result),'pilot credits;',len(issues),'unresolved extraction issues')


def active_decisions(ledger):
    """Explicit supersession, independent of file ordering; preserve old records."""
    all_decisions={d['id']:d for d in ledger['decisions']}
    if len(all_decisions)!=len(ledger['decisions']):raise ValueError('Duplicate decision ID')
    superseded=set();done=set();visiting=set()
    def visit(did):
        if did in visiting:raise ValueError('Cyclic decision supersession')
        if did in done:return
        visiting.add(did);d=all_decisions[did]
        for old in d.get('supersedes',[]):
            if old not in all_decisions:raise ValueError('Unknown superseded decision')
            if all_decisions[old]['occurrence_id']!=d['occurrence_id']:
                raise ValueError('Supersession crosses occurrences')
            superseded.add(old);visit(old)
        visiting.remove(did);done.add(did)
    for did in all_decisions:visit(did)
    return [all_decisions[did] for did in sorted(all_decisions) if did not in superseded]


def resolve(occurrences, ledger):
    by_id={o['occurrence_id']:o for o in occurrences}
    if len(by_id)!=len(occurrences):raise ValueError('Duplicate occurrence ID')
    people={p['id']:p for p in ledger['people']}
    if len(people)!=len(ledger['people']):raise ValueError('Duplicate person ID')
    qids=[p['preferred_qid'] for p in people.values() if p.get('preferred_qid')]
    if len(set(qids))!=len(qids):raise ValueError('One QID assigned to multiple local people')
    evidence={e['id']:e for e in ledger['evidence']}
    if len(evidence)!=len(ledger['evidence']):raise ValueError('Duplicate evidence ID')
    decisions={};seen=set()
    for d in active_decisions(ledger):
        if d['id'] in seen:raise ValueError('Duplicate decision ID')
        seen.add(d['id'])
        if d['occurrence_id'] in decisions:raise ValueError('Conflicting active decisions')
        o=by_id.get(d['occurrence_id'])
        if not o or o['occurrence_fingerprint']!=d['occurrence_fingerprint']:
            raise ValueError('Stale occurrence fingerprint')
        if d.get('legacy_qid')!=o['legacy_qid']:raise ValueError('Stale legacy assignment')
        if d['status'] not in ('accepted','unresolved','rejected'):raise ValueError('Unknown decision status')
        if not d.get('rationale') or not d.get('evidence') or any(e not in evidence for e in d['evidence']):
            raise ValueError('Decision lacks reviewed evidence')
        if d['status']=='accepted':
            if d['person_id'] not in people:raise ValueError('Unknown person')
            qid=people[d['person_id']].get('preferred_qid')
            if qid and not re.fullmatch('Q[0-9]+',qid):raise ValueError('Invalid QID')
            if qid in d.get('rejected_qids',[]):raise ValueError('Accepted rejected QID')
        elif d.get('person_id'):raise ValueError('Unresolved/rejected credit has accepted person')
        decisions[d['occurrence_id']]=d
    output=[]
    for o in occurrences:
        d=decisions.get(o['occurrence_id']);r=dict(o)
        r.update(person_id=None,effective_qid=o['legacy_qid'],identity_status='legacy_unreviewed')
        if d:
            r['identity_status']=d['status']
            if d['status']=='accepted':
                r['person_id']=d['person_id'];r['effective_qid']=people[d['person_id']].get('preferred_qid')
            elif d['status']=='rejected':r['effective_qid']=None
            # Unresolved legacy suggestions stay visible, explicitly unaccepted.
        output.append(r)
    return output


def build(work, out):
    builder_hash=sha(Path(__file__))
    frozen,manifest=verify_frozen(work)
    if out.exists():raise ValueError('Output already exists; choose a new build directory')
    destination=out
    out=out.with_name(out.name+'.building')
    if out.exists():raise ValueError('An unfinished build already exists: '+str(out))
    occurrences=json.loads((work/'occurrences.json').read_text())
    ledger=json.loads((work/'decisions.json').read_text())
    if ledger['baseline_manifest_sha256']!=sha(work/'baseline-manifest.json'):
        raise ValueError('Ledger belongs to another baseline')
    for e in ledger['evidence']:
        if e.get('snapshot_path') and sha(work/e['snapshot_path'])!=e['snapshot_sha256']:
            raise ValueError('Changed evidence snapshot '+e['id'])
    for o in occurrences:
        if sha(frozen/o['json_path'])!=o['source_json_sha256'] or sha(frozen/o['raw_path'])!=o['source_raw_file_sha256']:
            raise ValueError('Source fingerprint mismatch')
        check={k:v for k,v in o.items() if k not in ('legacy_evidence','occurrence_fingerprint')}
        if digest(check)!=o['occurrence_fingerprint']:raise ValueError('Changed occurrence extraction')
    resolved=resolve(occurrences,ledger)
    out.mkdir(parents=True)
    shutil.copy2(Path(__file__),out/'builder.py')
    shutil.copy2(frozen/'catalog.duckdb',out/'catalog.duckdb')
    write_json(out/'person-occurrences.json',resolved)
    identifiers=[]
    for p in ledger['people']:
        if p.get('preferred_qid'):
            identifiers.append({'person_id':p['id'],'qid':p['preferred_qid'],'status':'accepted_preferred', 'evidence':p.get('evidence',[])})
        for alternate in p.get('alternate_qids',[]):
            identifiers.append(dict(alternate,person_id=p['id'],evidence=p.get('evidence',[])))
    write_json(out/'person-identifiers.json',identifiers)
    changes=[];projection_issues=[]
    catalog=json.loads((frozen/'catalog-selection.json').read_text())
    for row in catalog:
        group=[o for o in resolved if record_key(o)==record_key(row)]
        reviewers=[o for o in group if o['role']=='reviewer']
        if len(reviewers)==1 and reviewers[0]['identity_status'] in ('accepted','rejected'):
            qid=reviewers[0]['effective_qid']
            changes.append(dict(zip(('source','era','review_id'),record_key(row)),column='reviewer_qid',before=row['reviewer_qid'],after=qid))
        authors=[o for o in group if o['role']!='reviewer']
        acted=[o for o in authors if o['identity_status'] in ('accepted','rejected')]
        if acted:
            # Flatten only when the extracted single book and legacy credits can
            # be reconciled unambiguously. Structured decisions always survive.
            items={o['item_id'] for o in authors}
            ordered=sorted(authors,key=lambda o:o['position'] or 0)
            old='|'.join(o['legacy_qid'] for o in ordered if o['legacy_qid']) or None
            if len(items)!=1 or old!=(row['author_qids'] or None):
                projection_issues.append(dict(zip(('source','era','review_id'),record_key(row)),reason='Author compatibility projection needs manual reconciliation'))
            else:
                new='|'.join(o['effective_qid'] for o in ordered if o['effective_qid']) or None
                changes.append(dict(zip(('source','era','review_id'),record_key(row)),column='author_qids',before=row['author_qids'],after=new))
                if row['n_authors']!=len(ordered):
                    changes.append(dict(zip(('source','era','review_id'),record_key(row)),column='n_authors',before=row['n_authors'],after=len(ordered)))
    with duckdb.connect(str(out/'catalog.duckdb')) as c:
        c.execute("SET memory_limit='768MB'")
        c.execute('SET threads=1')
        c.execute('SET preserve_insertion_order=false')
        c.execute('BEGIN TRANSACTION')
        c.execute('CREATE TABLE person_occurrences AS SELECT * FROM read_json_auto(?, maximum_object_size=16777216)',[str(out/'person-occurrences.json')])
        c.execute('CREATE TABLE grounding_people AS SELECT * FROM read_json_auto(?)',[str(work/'decisions.json')])
        # Flat ledger tables keep the reviewed authority inspectable in SQL.
        c.execute('CREATE TABLE identity_decisions AS SELECT unnest(decisions, recursive := true) FROM grounding_people')
        c.execute('CREATE TABLE people AS SELECT unnest(people, recursive := true) FROM grounding_people')
        c.execute('CREATE TABLE grounding_evidence AS SELECT unnest(evidence, recursive := true) FROM grounding_people')
        c.execute('CREATE TABLE person_identifiers AS SELECT * FROM read_json_auto(?)',[str(out/'person-identifiers.json')])
        c.execute('DROP TABLE grounding_people')
        for ch in changes:
            where=[ch['source'],ch['era'],ch['review_id']]
            column=ch['column']
            c.execute(f'UPDATE reviews SET {column}=? WHERE source=? AND era=? AND review_id=?',[ch['after'],*where])
            if column=='reviewer_qid':
                status='reviewed_accepted' if ch['after'] else 'reviewed_rejected'
                c.execute('UPDATE reviews SET reviewer_wd_status=? WHERE source=? AND era=? AND review_id=?',[status,*where])
            elif column=='author_qids':
                n=len(ch['after'].split('|')) if ch['after'] else 0
                c.execute('UPDATE reviews SET n_authors_grounded=? WHERE source=? AND era=? AND review_id=?',[n,*where])
        c.execute('COMMIT')
        c.execute('COPY reviews TO ? (FORMAT PARQUET, ROW_GROUP_SIZE 2048)',[str(out/'reviews.parquet')])
        c.execute('COPY person_occurrences TO ? (FORMAT PARQUET)',[str(out/'person-occurrences.parquet')])
        # Verify every source field and every unselected row against the baseline.
        baseline_literal="'"+str(frozen/'catalog.duckdb').replace("'","''")+"'"
        c.execute('ATTACH '+baseline_literal+' AS baseline (READ_ONLY)')
        ignored={'reviewer_qid','reviewer_wd_status','author_qids','n_authors_grounded','n_authors'}
        columns=[r[0] for r in c.execute('DESCRIBE reviews').fetchall() if r[0] not in ignored]
        if row_hashes(c,'reviews',columns)!=row_hashes(c,'baseline.reviews',columns):
            raise ValueError('Unrelated catalog fields changed')
        expected={}
        for ch in changes:
            k=record_key(ch)
            expected.setdefault(k,{})[ch['column']]=ch['after']
            if ch['column']=='reviewer_qid':
                expected[k]['reviewer_wd_status']='reviewed_accepted' if ch['after'] else 'reviewed_rejected'
            elif ch['column']=='author_qids':
                expected[k]['n_authors_grounded']=len(ch['after'].split('|')) if ch['after'] else 0
        # Verify the exact expected value of every mutable field on every row,
        # including unselected rows. This also detects unexpected extra writes.
        selected_cols='source,era,review_id,'+','.join(sorted(ignored))
        originals={record_key(r):r for r in rows(c,'SELECT '+selected_cols+' FROM baseline.reviews')}
        after=rows(c,'SELECT '+selected_cols+' FROM reviews')
        if len(after)!=len(originals):raise ValueError('Catalog row count changed')
        full_diff=[]
        for r in after:
            k=record_key(r);want=dict(originals[k]);want.update(expected.get(k,{}))
            if r!=want:raise ValueError('Unexpected grounding projection: '+str(k))
            for field in sorted(ignored):
                if r[field]!=originals[k][field]:
                    full_diff.append(dict(zip(('source','era','review_id'),k),column=field,before=originals[k][field],after=r[field]))
        # Cryptographic full-row comparison, including all bodies and metadata.
        all_columns=[r[0] for r in c.execute('DESCRIBE reviews').fetchall()]
        if row_hashes(c,'reviews',all_columns)!=row_hashes(c,'read_parquet(?)',all_columns,[str(out/'reviews.parquet')]):
            raise ValueError('Parquet differs from corrected DB')
        c.execute('CHECKPOINT')
    diff=sorted(full_diff,key=lambda d:(record_key(d),d['column']))
    write_json(out/'catalog-diff.json',diff)
    write_json(out/'projection-issues.json',projection_issues)
    write_json(out/'occurrence-diff.json',[{k:o[k] for k in ('occurrence_id','source','era','review_id','name','role','item_title','legacy_qid','effective_qid','identity_status','person_id')} for o in resolved if o['legacy_qid']!=o['effective_qid']])
    # This is an import candidate, not an applied mutation to the graph ledger.
    decisions=[]
    byid={o['occurrence_id']:o for o in occurrences}
    for d in active_decisions(ledger):
        if d['status']!='accepted':continue
        o=byid[d['occurrence_id']]
        decisions.append(dict(d,person_id='unified:person:'+d['person_id'],source_json_sha256=o['source_json_sha256'],source_raw_sha256=o['source_raw_sha256']))
    write_json(out/'graph-decisions-candidate.json',{'schema_version':'1.0','people':ledger['people'],'decisions':decisions})
    report={'catalog_rows':manifest['catalog_rows'],'pilot_catalog_rows':len(catalog),'source_occurrences':len(resolved),
            'pilot_occurrences':sum(o['pilot'] for o in resolved),'decision_statuses':dict(Counter(d['status'] for d in active_decisions(ledger))),
            'superseded_decisions':len(ledger['decisions'])-len(active_decisions(ledger)),
            'changed_catalog_cells':len(diff),'changed_occurrence_qids':sum(o['legacy_qid']!=o['effective_qid'] for o in resolved),
            'changed_catalog_qid_cells':sum(d['column'] in ('reviewer_qid','author_qids') for d in diff),
            'projection_issues':len(projection_issues),'baseline_catalog_sha256':manifest['catalog_sha256'],
            'ledger_sha256':sha(work/'decisions.json'),'occurrences_sha256':sha(work/'occurrences.json'),
            'builder_sha256':builder_hash,
            'assignment_digest':digest([(o['occurrence_id'],o['person_id'],o['effective_qid'],o['identity_status']) for o in resolved]),
            'validation':'All original source fields preserved by per-record SHA-256 comparison; every mutable cell checked against intended decisions; DuckDB/Parquet full-row SHA-256 equality verified; reviewed decisions fingerprint checked.'}
    if sha(Path(__file__))!=builder_hash:raise ValueError('Builder changed during execution')
    write_json(out/'report.json',report)
    out.rename(destination)
    print(json.dumps(report,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['freeze','extract','build'])
    p.add_argument('--work',type=Path,default=DEFAULT)
    p.add_argument('--upstream',type=Path,default=Path('/home/jic823/hnet-reviews'))
    p.add_argument('--out',type=Path)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    if a.command=='freeze':freeze(a.upstream,a.work)
    elif a.command=='extract':extract(a.work)
    else:build(a.work,a.out or a.work/'generated/pilot-v1')


if __name__=='__main__':main()
