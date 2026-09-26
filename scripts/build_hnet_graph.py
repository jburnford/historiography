#!/usr/bin/env python3
"""Build a local, metadata-only H-Net graph; never merge people by name.

Standard library only. Processes one source at a time into SQLite. Raw corpus
and teaching graph are read-only inputs; outputs are built in a temporary
directory and replace the previous generated files only after validation.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path('/home/jic823/hnet-reviews/data')
DEFAULT_OUT = ROOT / 'data/hnet-graph/generated'
POLICY = ROOT / 'data/hnet-graph/decisions.json'
VERSION = '1.0'


def serial(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def stable(kind, *parts):
    return 'hnet:' + kind + ':' + digest(serial(parts).encode())[:24]


def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def normalized(value):
    # Retain accents, initials, punctuation and word order. This key is still
    # ONLY a candidate grouping, never a resolved person identifier.
    return unicodedata.normalize('NFC', clean(value)).casefold()


def isbn13(raw):
    code = re.sub(r'[-\s]', '', raw).upper()
    if len(code) == 10 and re.fullmatch(r'\d{9}[\dX]', code):
        if sum((10-i) * (10 if c == 'X' else int(c)) for i, c in enumerate(code)) % 11:
            return None
        code = '978' + code[:9]
        return code + str((-sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(code))) % 10)
    if len(code) == 13 and code.isdigit() and code.startswith(('978', '979')):
        if sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(code)) % 10 == 0:
            return code
    return None


class HeaderDone(Exception):
    pass


class CitationParser(HTMLParser):
    """Read citation blocks up to and including the byline; ignore essay body."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.active = None
        self.depth = 0
        self.mark = None
        self.meta = {}
        self.header_found = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name', '').startswith('DC.'):
            self.meta[attrs['name']] = attrs.get('content', '')
        if self.active is None and 'revtext' in attrs.get('class', '').split():
            self.active = dict(text=[], strong=[], em=[], links=[])
            self.depth = 1
        elif self.active is not None and tag not in ('br', 'img', 'hr', 'meta', 'input', 'link'):
            self.depth += 1
        if self.active is not None:
            if tag in ('strong', 'em'):
                self.mark = tag
            if tag in ('br', 'p', 'div'):
                self.active['text'].append('\n')
            if tag == 'a':
                self.active['links'].append(attrs.get('href', ''))

    def handle_endtag(self, tag):
        if self.active is None or tag in ('br', 'img', 'hr', 'meta', 'input', 'link'):
            return
        if tag == self.mark:
            self.mark = None
        self.depth -= 1
        if self.depth == 0:
            block = {k: clean(''.join(v)) for k, v in self.active.items() if k != 'links'}
            block['links'] = self.active['links']
            self.blocks.append(block)
            self.active = None
            if re.match(r'^(?:Reviewed by|Published on)\b', block['text']):
                self.header_found = True
                raise HeaderDone()

    def handle_data(self, data):
        if self.active is not None:
            self.active['text'].append(data)
            if self.mark:
                self.active[self.mark].append(data)


def citations(html, record):
    parser = CitationParser()
    if html:
        try:
            parser.feed(html)
        except HeaderDone:
            pass
    found = []
    for block in parser.blocks if parser.header_found else []:
        if re.match(r'^(?:Reviewed by|Published on)\b', block['text']):
            break
        if not block['em']:
            continue
        text = block['text']
        # Year following a publisher/city citation, not a period in the title.
        tail = text.split(block['em'], 1)[-1]
        year = re.search(r',\s*(\d{4})\.', tail)
        found.append(dict(title=block['em'].strip(' .'), credit=block['strong'].strip(' .'),
                          citation=text, publication_year=int(year[1]) if year else None,
                          isbns_raw=re.findall(r'ISBN(?:-1[03])?\s*:?\s*([\dXx][\dXx\-]+)', tail),
                          locator=f'HTML revtext citation {len(found)+1}', extraction='raw_html_header'))
    if not found and record.get('book_title'):
        year = str(record.get('pub_year') or '')
        found.append(dict(title=record['book_title'], credit=record.get('book_author') or '',
                          citation=record.get('citation') or '',
                          publication_year=int(year) if re.fullmatch(r'\d{4}', year) else None,
                          isbns_raw=[record['isbn']] if record.get('isbn') else [],
                          locator='JSON book_title/book_author/citation', extraction='parsed_json_fallback'))
    return found, parser.meta


ROLE_SUFFIX = re.compile(r'(?:[,;]\s*|\s+\()(?P<role>eds?\.?|editors?|Hrsg\.?|photographer|translator|trans\.?)\)?\.?$', re.I)
SUFFIX = re.compile(r',\s*(Jr\.?|Sr\.?|II|III|IV|PhD|S\.J\.?|C\.S\.C\.?)$', re.I)


def split_credit(raw, reviewer=False):
    """Split only clear natural-order lists. Ambiguous strings stay statements."""
    value = clean(raw).strip(' .')
    if not value:
        return [], 'missing', None
    role = 'reviewer' if reviewer else 'contributor_unspecified'
    m = ROLE_SUFFIX.search(value)
    if m and not reviewer:
        marker = m['role'].lower().rstrip('.')
        role = 'editor' if marker in ('ed', 'eds', 'editor', 'editors', 'hrsg') else ('translator' if marker.startswith('trans') else marker)
        value = value[:m.start()].strip(' ,;.')
    suffix = SUFFIX.search(value)
    if suffix:
        # Protect a single name suffix; ambiguous suffixes in a multi-name list
        # are deliberately deferred rather than attached to the wrong person.
        core = value[:suffix.start()]
        if not re.search(r',|;|\band\b|\bund\b| & ', core):
            return [(value, role)], 'single_with_suffix', None
    if re.search(r'\d|[()<>:]|\bet al\b|\b(?:university|committee|association|institute|society|press)\b', value, re.I):
        return [], 'unresolved', 'complex_or_corporate_credit'
    parts = re.split(r'\s*;\s*|\s*,\s*|\s+(?:and|und|&)\s+', value)
    if len(parts) == 1:
        return [(value, role)], 'single', None
    if all(len(p.split()) >= 2 and any(c.isalpha() for c in p) for p in parts):
        return [(p.strip(' .'), role) for p in parts], 'clear_list', None
    return [], 'unresolved', 'ambiguous_comma_or_name_order'


def review_date(raw):
    value = clean(raw)
    m = re.fullmatch(r'([A-Za-z]+),?\s+(\d{4})', value)
    if not m:
        return None, 'missing_or_unparsed'
    year = int(m[2])
    if year < 1993:
        return None, 'suspect_default_date'
    try:
        month = datetime.strptime(m[1], '%B').month
    except ValueError:
        return None, 'missing_or_unparsed'
    return f'{year:04d}-{month:02d}', 'source_recorded'


def text_fingerprint(body):
    # Footer citations contain the local review URL and would make identical
    # essays appear unique. Remove only the known structural footer; no text
    # interpretation, paraphrase, or fuzzy duplicate matching takes place.
    core = re.split(r'\n\n(?:If there is additional discussion of this review,|Citation:\s*\n)',
                    body, maxsplit=1)[0]
    return digest(core.encode())


def valid_source(record, era, rid):
    url = urlparse(record.get('source_url') or '')
    values = parse_qs(url.query).get('id', [])
    return (era in ('classic','email') and record.get('era') == era and str(record.get('review_id')) == rid
            and url.hostname in ('h-net.org', 'www.h-net.org')
            and url.path == '/reviews/showrev.php' and values == [rid])


SCHEMA = '''
PRAGMA foreign_keys=ON;
PRAGMA cache_size=-16384;
PRAGMA temp_store=FILE;
CREATE TABLE nodes(id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, properties TEXT NOT NULL);
CREATE INDEX node_kind ON nodes(kind);
CREATE TABLE sources(id TEXT PRIMARY KEY, relative_path TEXT UNIQUE, json_sha256 TEXT NOT NULL,
 raw_relative_path TEXT, raw_sha256 TEXT, source_url TEXT, wayback_url TEXT, wayback_timestamp TEXT,
 status TEXT NOT NULL, reason TEXT);
CREATE TABLE edges(id TEXT PRIMARY KEY, subject TEXT REFERENCES nodes(id), predicate TEXT NOT NULL,
 object TEXT REFERENCES nodes(id), source_id TEXT REFERENCES sources(id), status TEXT NOT NULL,
 properties TEXT NOT NULL);
CREATE INDEX edge_subject ON edges(subject,predicate);
CREATE INDEX edge_object ON edges(object,predicate);
CREATE INDEX edge_type ON edges(predicate);
CREATE TABLE reviews(id TEXT PRIMARY KEY REFERENCES nodes(id), source_id TEXT REFERENCES sources(id),
 network_id TEXT REFERENCES nodes(id), date_raw TEXT, date_month TEXT, date_status TEXT,
 text_sha256 TEXT, metadata_sha256 TEXT);
CREATE TABLE items(id TEXT PRIMARY KEY REFERENCES nodes(id), title TEXT, credit TEXT,
 publication_year INTEGER, isbns TEXT, identity_status TEXT);
CREATE TABLE mentions(id TEXT PRIMARY KEY REFERENCES nodes(id), review_id TEXT REFERENCES nodes(id),
 item_id TEXT REFERENCES nodes(id), role TEXT, name TEXT, name_key TEXT,
 affiliation TEXT, candidate_id TEXT REFERENCES nodes(id), locator TEXT);
CREATE INDEX mention_key ON mentions(name_key);
CREATE INDEX mention_candidate ON mentions(candidate_id);
CREATE INDEX review_network ON reviews(network_id);
CREATE TABLE issues(source_id TEXT REFERENCES sources(id), code TEXT, detail TEXT);
CREATE TABLE atlas_matches(candidate_id TEXT REFERENCES nodes(id), atlas_person_id TEXT,
 label TEXT, status TEXT);
CREATE VIEW item_networks AS
 SELECT DISTINCT e.subject AS review_id,e.object AS item_id,r.network_id
 FROM edges e JOIN reviews r ON r.id=e.subject
 WHERE e.predicate='reviews_item' AND r.network_id IS NOT NULL;
CREATE VIEW mention_networks AS
 SELECT m.id AS mention_id,m.candidate_id,m.name,m.role,m.review_id,r.network_id
 FROM mentions m JOIN reviews r ON r.id=m.review_id WHERE r.network_id IS NOT NULL;
CREATE VIEW name_candidates AS
 SELECT candidate_id,name_key,COUNT(*) AS mention_count,COUNT(DISTINCT review_id) AS review_count,
 COUNT(DISTINCT NULLIF(affiliation,'')) AS affiliation_count,COUNT(DISTINCT role) AS role_count
 FROM mentions GROUP BY candidate_id,name_key;
CREATE VIEW duplicate_review_candidates AS
 SELECT text_sha256,metadata_sha256,COUNT(*) AS record_count
 FROM reviews GROUP BY text_sha256,metadata_sha256 HAVING COUNT(*)>1;
'''


class Graph:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def node(self, nid, kind, label, **props):
        self.db.execute('INSERT OR IGNORE INTO nodes VALUES(?,?,?,?)', (nid, kind, label, serial(props)))
        return nid

    def edge(self, subject, predicate, obj, source_id=None, status='source_recorded', **props):
        eid = stable('edge', subject, predicate, obj, source_id)
        self.db.execute('INSERT OR IGNORE INTO edges VALUES(?,?,?,?,?,?,?)',
                        (eid, subject, predicate, obj, source_id, status, serial(props)))

    def issue(self, source, code, detail):
        self.db.execute('INSERT INTO issues VALUES(?,?,?)', (source, code, detail))

    def credit(self, raw, rid, sid, item=None, affiliation='', locator='JSON reviewer'):
        names, parsing, issue = split_credit(raw, reviewer=item is None)
        if issue:
            nid = self.node(stable('credit', rid, item, raw), 'credit_statement', raw,
                            parsing_status='unresolved', reason=issue)
            self.edge(item or rid, 'has_credit_statement', nid, sid, locator=locator)
            self.issue(sid, issue, raw)
        if not names and not raw:
            self.issue(sid, 'missing_reviewer' if item is None else 'missing_item_credit', locator)
        for position, (name, role) in enumerate(names, 1):
            key = normalized(name)
            cid = self.node(stable('name', key), 'name_candidate', name,
                            normalized_name=key, identity_status='unresolved_name_bucket',
                            warning='May contain different people; not a person identity.')
            mid = self.node(stable('mention', rid, item, locator, position, name, role), 'person_mention', name,
                            identity_status='unresolved', role=role, affiliation_raw=affiliation,
                            parsing=parsing, credit_position=position)
            self.db.execute('INSERT INTO mentions VALUES(?,?,?,?,?,?,?,?,?)',
                            (mid, rid, item, role, name, key, affiliation, cid, locator))
            self.edge(item or rid, 'credited_to' if item else 'reviewed_by', mid, sid,
                      role=role, locator=locator, raw_credit=raw)
            self.edge(mid, 'has_name_candidate', cid, sid, status='candidate_only')
            if re.search('[\ufffdÃÂÖ]', name):
                self.issue(sid, 'possible_name_encoding_issue', name)


def load_source(graph, source_root, path):
    raw_json = path.read_bytes()
    rel = path.relative_to(source_root).as_posix()
    era, rid = path.parent.name, path.stem
    sid = f'hnet:source:{era}:{rid}'
    record = json.loads(raw_json)
    body = record.get('body_text') or ''
    reason = ('empty_body' if not body.strip() else
              'content_flag_false' if not record.get('content_ok') else
              'invalid_source_identity' if not valid_source(record, era, rid) else None)
    raw_rel = f'html/{era}/{rid}.html.gz'
    raw_path = source_root / raw_rel
    html_bytes = None
    if not reason and raw_path.exists():
        with gzip.open(raw_path, 'rb') as handle:
            html_bytes = handle.read()
    graph.db.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)',
                     (sid, rel, digest(raw_json), raw_rel if raw_path.exists() else None,
                      digest(html_bytes) if html_bytes is not None else None,
                      record.get('source_url'), record.get('wayback_url'), record.get('wayback_timestamp'),
                      'excluded' if reason else 'included', reason))
    if reason:
        return
    html = html_bytes.decode('utf-8', errors='replace') if html_bytes else ''
    if '\ufffd' in html:
        graph.issue(sid, 'raw_html_decode_replacement', 'UTF-8 decoding introduced replacement characters; inspect source.')
    if not html:
        graph.issue(sid, 'missing_raw_html', 'Only parsed JSON available; additional reviewed items may be missing.')
    books, dc = citations(html, record)
    review_id = f'hnet:review:{era}:{rid}'
    title = record.get('review_title') or ''
    # Existing parser often confuses additional citation authors with essay titles.
    # No essay title extraction or semantic analysis is needed for this graph.
    graph.node(review_id, 'review_record', f'H-Net review {rid}',
               reported_title=title, title_status='unverified_parser_value',
               record_type='review_or_report', dc_metadata=dc)
    net = clean(record.get('network'))
    network_id = None
    if net:
        network_id = graph.node(stable('network', net), 'network', net,
                                field_context='source_network', atlas_mapping_status='separate_editorial_crosswalk')
        graph.edge(review_id, 'published_on', network_id, sid, locator='JSON network')
    else:
        graph.issue(sid, 'missing_network', 'No field affiliation inferred.')
    month, date_status = review_date(record.get('review_date'))
    if date_status != 'source_recorded':
        graph.issue(sid, date_status, record.get('review_date') or '')
    meta_key = [record.get(k) for k in ('reviewer','reviewer_affiliation','review_date','network')]
    meta_key.append(books)
    graph.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)',
                     (review_id, sid, network_id, record.get('review_date'), month, date_status,
                      text_fingerprint(body), digest(serial(meta_key).encode())))
    graph.credit(record.get('reviewer') or '', review_id, sid,
                 affiliation=record.get('reviewer_affiliation') or '')
    if len(books) > 1:
        graph.issue(sid, 'multiple_reviewed_items_recovered', str(len(books)))
    for index, book in enumerate(books, 1):
        codes = sorted({isbn13(code) for code in book['isbns_raw']} - {None})
        invalid = [code for code in book['isbns_raw'] if isbn13(code) is None]
        if invalid:
            graph.issue(sid, 'invalid_isbn', serial(invalid))
        if codes:
            # Corroborated exact citation grouping; no cross-edition work merge.
            key = (normalized(book['title']), normalized(book['credit']), book['publication_year'], codes)
            item_id = stable('item', key)
            identity = 'matching_isbn_title_credit_year'
            kind = 'bibliographic_item'
        else:
            item_id = stable('item', review_id, index)
            identity = 'unresolved_source_occurrence'
            kind = 'reviewed_item'
        graph.node(item_id, kind, book['title'], identity_status=identity,
                   book_status='isbn_bearing_publication' if codes else 'type_unresolved')
        graph.db.execute('INSERT OR IGNORE INTO items VALUES(?,?,?,?,?,?)',
                         (item_id, book['title'], book['credit'], book['publication_year'], serial(codes), identity))
        graph.edge(review_id, 'reviews_item', item_id, sid, locator=book['locator'],
                   citation=book['citation'], credit_raw=book['credit'], isbns_raw=book['isbns_raw'],
                   extraction=book['extraction'])
        graph.credit(book['credit'], review_id, sid, item=item_id, locator=book['locator']+' credit')
    if not books:
        graph.issue(sid, 'no_reviewed_item', 'Record retained without fabricated book.')


def decisions(graph, policy, atlas):
    """Explicit identity decisions only; source fingerprints reject stale edits."""
    known_people = {p['id']:p for p in atlas.get('people', [])}
    by_name = {}
    for pid, p in known_people.items():
        by_name.setdefault(normalized(p['label']), []).append((pid, p['label']))
    for cid, key in graph.db.execute('SELECT candidate_id,name_key FROM name_candidates'):
        for pid, label in by_name.get(key, []):
            nid = graph.node('atlas:person:'+pid, 'atlas_person_reference', label, atlas_person_id=pid)
            graph.edge(cid, 'candidate_atlas_identity', nid, status='candidate_only',
                       basis='exact_normalized_name_only')
            graph.db.execute('INSERT INTO atlas_matches VALUES(?,?,?,?)', (cid,pid,label,'candidate_only'))
    fields = {n['id']: n for n in atlas.get('nodes', []) if n.get('entry_kind') == 'group'}
    for mapping in policy.get('network_field_candidates', []):
        network = stable('network', mapping['network'])
        if mapping['field_id'] not in fields:
            raise ValueError('Unknown atlas field: '+mapping['field_id'])
        if not graph.db.execute('SELECT 1 FROM nodes WHERE id=?', (network,)).fetchone():
            continue
        field = fields[mapping['field_id']]
        target = graph.node('atlas:field:'+field['id'], 'atlas_field_reference', field['label'], atlas_field_id=field['id'])
        graph.edge(network, 'candidate_field_correspondence', target, status='candidate_only',
                   basis='network_label', rationale=mapping['rationale'],
                   qualification='Navigation candidate, not identity, membership, or classification of every item.')
    seen = set()
    for person in policy.get('resolved_people', []):
        if not person.get('rationale') or not person.get('evidence') or not person.get('mentions'):
            raise ValueError('Person resolution requires rationale, evidence and pinned mentions')
        pid = 'hnet:person:'+person['id']
        if graph.db.execute('SELECT 1 FROM nodes WHERE id=?',(pid,)).fetchone():
            raise ValueError('Duplicate resolved person ID')
        graph.node(pid, 'person', person['label'], identity_status='editorially_resolved',
                   rationale=person['rationale'], evidence=person['evidence'])
        for decision in person['mentions']:
            mid = decision['id']
            row = graph.db.execute('SELECT r.source_id,s.json_sha256 FROM mentions m JOIN reviews r ON r.id=m.review_id JOIN sources s ON s.id=r.source_id WHERE m.id=?',(mid,)).fetchone()
            if mid in seen or not row or row[1] != decision['source_json_sha256']:
                raise ValueError('Duplicate, missing or stale identity decision: '+mid)
            seen.add(mid)
            graph.edge(mid, 'identified_as', pid, row[0], status='editorially_resolved',
                       rationale=person['rationale'], evidence=person['evidence'])


def export(graph, destination):
    db = graph.db
    for table in ('nodes','edges'):
        cursor = db.execute(f'SELECT * FROM {table} ORDER BY id')
        columns = [d[0] for d in cursor.description]
        with (destination/(table+'.jsonl')).open('w') as handle:
            for values in cursor:
                row = dict(zip(columns, values))
                row['properties'] = json.loads(row['properties'])
                handle.write(serial(row)+'\n')
    import csv
    queues = {
        'identity-candidates.csv': '''SELECT c.*,n.label,
          (SELECT group_concat(DISTINCT m.affiliation) FROM mentions m
           WHERE m.candidate_id=c.candidate_id AND m.affiliation!='') AS affiliations
          FROM name_candidates c JOIN nodes n ON n.id=c.candidate_id
          ORDER BY c.mention_count DESC,c.candidate_id''',
        'network-coverage.csv': '''SELECT n.id,n.label,COUNT(r.id) AS review_records
          FROM nodes n JOIN reviews r ON r.network_id=n.id GROUP BY n.id ORDER BY review_records DESC,n.id''',
        'atlas-person-candidates.csv': 'SELECT * FROM atlas_matches ORDER BY candidate_id,atlas_person_id',
        'issues.csv': 'SELECT * FROM issues ORDER BY source_id,code,detail',
        'sources.csv': 'SELECT * FROM sources ORDER BY id',
        'isbn-reconciliation.csv': '''WITH shared AS (
          SELECT j.value AS isbn,COUNT(*) AS item_count FROM items i,json_each(i.isbns) j
          GROUP BY j.value HAVING COUNT(*)>1)
          SELECT s.isbn,s.item_count,i.id,i.title,i.credit,i.publication_year
          FROM shared s JOIN items i JOIN json_each(i.isbns) j ON j.value=s.isbn
          ORDER BY s.isbn,i.id''',
        'duplicate-review-candidates.csv': '''SELECT d.*,r.id AS review_id FROM duplicate_review_candidates d
          JOIN reviews r USING(text_sha256,metadata_sha256) ORDER BY text_sha256,metadata_sha256,r.id''',
    }
    for filename, query in queues.items():
        cur = db.execute(query)
        with (destination/filename).open('w',newline='') as handle:
            writer=csv.writer(handle);writer.writerow([d[0] for d in cur.description]);writer.writerows(cur)


def validate(db):
    errors = []
    if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
        errors.append('SQLite integrity failure')
    if db.execute('PRAGMA foreign_key_check').fetchone():
        errors.append('Dangling graph reference')
    if db.execute("SELECT COUNT(*) FROM reviews r JOIN sources s ON s.id=r.source_id WHERE s.status!='included'").fetchone()[0]:
        errors.append('Excluded source entered graph')
    if db.execute("SELECT COUNT(*) FROM edges WHERE predicate='identified_as' AND status!='editorially_resolved'").fetchone()[0]:
        errors.append('Unreviewed person merge')
    if errors:
        raise ValueError('; '.join(errors))
    return dict(structural_errors=[], foreign_keys='passed', sqlite_integrity='passed')


def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build(source, out, policy_path=POLICY, atlas_path=ROOT/'historiography-1920-2000.json'):
    source, out = source.resolve(), out.resolve()
    if out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Output and external source must be separate')
    policy = json.loads(policy_path.read_text())
    atlas_hash = sha_file(atlas_path)
    atlas = json.loads(atlas_path.read_text())
    out.parent.mkdir(parents=True, exist_ok=True)
    paths=sorted((source/'json').glob('*/*.json'))
    started_at=datetime.now(timezone.utc).isoformat()
    if not paths:
        raise ValueError('No source JSON files')
    with tempfile.TemporaryDirectory(prefix='.hnet-build-',dir=out.parent) as tmp:
        dest=Path(tmp)
        graph=Graph(dest/'graph.sqlite')
        observed_stats={}
        for i,path in enumerate(paths,1):
            load_source(graph,source,path)
            observed_stats[path]=(path.stat().st_size,path.stat().st_mtime_ns)
            if i%5000==0:
                graph.db.commit()
                print(f'Processed {i}/{len(paths)} source records',flush=True)
        decisions(graph,policy,atlas)
        graph.db.commit()
        validation=validate(graph.db)
        stats={table:graph.db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
               for table in ('sources','nodes','edges','reviews','items','mentions','atlas_matches')}
        stats['node_kinds']=dict(graph.db.execute('SELECT kind,COUNT(*) FROM nodes GROUP BY kind'))
        stats['edge_types']=dict(graph.db.execute('SELECT predicate,COUNT(*) FROM edges GROUP BY predicate'))
        stats['exclusions']=dict(graph.db.execute("SELECT reason,COUNT(*) FROM sources WHERE status='excluded' GROUP BY reason"))
        stats['issues']=dict(graph.db.execute('SELECT code,COUNT(*) FROM issues GROUP BY code'))
        stats['duplicate_review_groups']=graph.db.execute('SELECT COUNT(*) FROM duplicate_review_candidates').fetchone()[0]
        stats['multiple_affiliation_name_candidates']=graph.db.execute('SELECT COUNT(*) FROM name_candidates WHERE affiliation_count>1').fetchone()[0]
        export(graph,dest)
        fingerprint=hashlib.sha256()
        for row in graph.db.execute('SELECT relative_path,json_sha256,raw_sha256 FROM sources ORDER BY relative_path'):
            fingerprint.update((serial(row)+'\n').encode())
        graph.db.close()
        if sha_file(atlas_path)!=atlas_hash:
            raise ValueError('Atlas changed during build')
        end_paths=set((source/'json').glob('*/*.json'))
        start_paths=set(paths)
        changed=[p for p in start_paths & end_paths
                 if observed_stats[p]!=(p.stat().st_size,p.stat().st_mtime_ns)]
        inventory=dict(enumerated_files=len(paths),files_at_end=len(end_paths),
                       added_during_build=len(end_paths-start_paths),removed_during_build=len(start_paths-end_paths),
                       changed_after_read=len(changed),
                       note='Graph records the enumerated source snapshot; later files require a rebuild.')
        report=dict(schema_version=VERSION,started_at=started_at,built_at=datetime.now(timezone.utc).isoformat(),
                    source_root=str(source),source_fingerprint=fingerprint.hexdigest(),
                    source_inventory=inventory,
                    atlas_sha256=atlas_hash,policy_sha256=sha_file(policy_path),
                    builder_sha256=sha_file(Path(__file__)),counts=stats,validation=validation,
                    person_policy='Occurrences and name candidates; no automatic person merges.',
                    interpretation='Bibliographic participation only; no review-argument analysis.',
                    files={p.name:sha_file(p) for p in sorted(dest.iterdir()) if p.is_file()})
        (dest/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        # A failed build leaves the preceding outputs intact. Summary is written
        # last; hashes detect any interrupted publication of the output set.
        out.mkdir(parents=True,exist_ok=True)
        for p in sorted(dest.iterdir(),key=lambda p:p.name=='summary.json'):
            p.replace(out/p.name)
    return report


def check(out):
    report=json.loads((out/'summary.json').read_text())
    for name,expected in report['files'].items():
        if sha_file(out/name)!=expected:
            raise ValueError('Output hash mismatch: '+name)
    with sqlite3.connect((out/'graph.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        validate(db)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    parser.add_argument('--out',type=Path,default=DEFAULT_OUT)
    parser.add_argument('--decisions',type=Path,default=POLICY)
    parser.add_argument('--atlas',type=Path,default=ROOT/'historiography-1920-2000.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    report=check(args.out) if args.check else build(args.source,args.out,args.decisions,args.atlas)
    print(json.dumps(report['counts'],indent=2))


if __name__=='__main__':
    main()
