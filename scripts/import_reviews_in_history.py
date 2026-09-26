"""Read-only Reviews in History adapter for the unified graph.

Recover bibliographic headers from saved HTML, never infer identities or
interpret review arguments. Source text stays in the external corpus.
"""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

try:
    from .build_hnet_graph import clean, isbn13, split_credit, review_date
except ImportError:
    from build_hnet_graph import clean, isbn13, split_credit, review_date

ORIGIN = 'reviews_in_history'
DEFAULT_SOURCE = Path('/home/jic823/hnet-reviews/data/rih')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text(node):
    return clean(node.get_text(' ', strip=True)) if node else ''


def parse_header(html):
    soup = BeautifulSoup(html, 'html.parser')
    node = soup.select_one('.node-review')
    wordpress = node is None
    if wordpress:
        node=soup.select_one('.review-content')
        if node:
            # The desktop table and mobile block repeat identical metadata.
            # Consume table rows only; never double their book/credit counts.
            for row in node.select('table.book-details tr'):
                label=text(row.select_one('th')).rstrip(':').casefold()
                cell=row.select_one('td')
                if cell and label in ('book','reviewer'):
                    row['class']=['view-display-id-summary' if label=='book' else 'view-display-id-reviewer']
                    cell['class']=['book-details-content']
    if node is None:
        return None
    books = []
    for block in node.select('.view-display-id-summary .book-details-content'):
        title = block.select_one('strong')
        # Split only actual HTML line breaks. Inline emphasis cannot split a
        # title or turn part of a credit into the publication imprint.
        fragments = ['']
        for child in block.children:
            if getattr(child, 'name', None) == 'br':
                fragments.append('')
            else:
                fragments[-1] += child.get_text(' ') if hasattr(child, 'get_text') else str(child)
        lines = [clean(v) for v in fragments if clean(v)]
        date = text(block.select_one('.date-display-single'))
        if not date and lines:
            year=re.search(r'\b((?:1[5-9]|20)\d{2})(?=\s*[,;]|\s*$)',lines[-1])
            date=year[1] if year else ''
        credit = ' '.join(lines[1:-1]) if len(lines) >= 3 else ''
        raw = text(block)
        books.append(dict(title=text(title) or (lines[0] if lines else ''), credit=credit,
                          publication_year=int(date) if re.fullmatch(r'\d{4}', date) else None,
                          citation=raw, imprint=lines[-1] if len(lines)>1 else '',
                          isbns_raw=re.findall(r'ISBN(?:-1[03])?\s*:?\s*([\dXx][\dXx\-]+)',raw)))
    reviewer = node.select_one('.view-display-id-reviewer .book-details-content')
    name = reviewer.select_one('strong') if reviewer else None
    recorded = text(name)
    if name:
        name.extract()
    affiliation = text(reviewer)
    date = text(node.select_one('.field-name-field-review-publication-date'))
    responses = []
    for section in node.select('.author-response-card' if wordpress else '#author-response'):
        content = section.select_one('.card-content' if wordpress else '.content')
        if not content:
            continue
        author = text(section.select_one('p strong')) if wordpress else text(content.select_one('.title'))
        timestamp = text(section.select_one('p span')) if wordpress else text(content.select_one('.timestamp'))
        for metadata in content.select('.title,.timestamp'):
            metadata.extract()
        body = text(content)
        if body:
            responses.append(dict(author=author, posted_raw=timestamp,
                                  text_sha256=digest(body.encode()), text_length=len(body)))
        section.extract()
    footer = node.select_one('section.content' if wordpress else '.group-footer')
    if wordpress and footer:
        for paragraph in reversed(footer.find_all('p',recursive=False)):
            value=text(paragraph)
            if review_date(value)[0]:
                date=value;paragraph.extract();break
    if footer:
        for metadata in footer.select('.field-name-field-review-publication-date,.view,script,style'):
            metadata.extract()
    body = text(footer)
    subjects = []
    related = soup.find(['h2','h3'], string=re.compile(r'^\s*Related terms\s*$'))
    if related:
        for link in related.parent.select('a[href]'):
            query = parse_qs(urlparse(link['href']).query)
            terms = [v for values in query.values() for v in values if re.fullmatch(r'taxonomy_vocabulary_\d+:\d+',v)]
            for term in terms:
                subjects.append(dict(key=term,label=text(link),href=link['href']))
    if wordpress:
        for link in node.select('.related-terms-list a[href]'):
            for term in parse_qs(urlparse(link['href']).query).get('taxonomies',[]):
                if re.fullmatch(r'[a-z0-9_-]+',term):
                    subjects.append(dict(key='wp:'+term,label=text(link),href=link['href']))
    return dict(books=books, reviewer=recorded, affiliation=affiliation, date_raw=date,
                review_title=text(soup.select_one('.review-header h1') or soup.select_one('h1')),
                layout='wordpress' if wordpress else 'drupal',
                responses=responses, subjects=subjects, body_length=len(body),
                body_sha256=digest(body.encode()))


def add_credit(s, raw, review_id, source_id, fingerprint, locator, item_id=None,
               response_id=None, affiliation=None, reviewer=False, raw_fingerprint=None):
    from_key = re.sub(r'^(?:(?:Professor|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+)+','',raw,flags=re.I)
    explicit_editor = bool(re.match(r'^edited by\s*:',from_key,re.I))
    from_key = re.sub(r'^edited by\s*:\s*','',from_key,flags=re.I)
    names, status, issue = split_credit(from_key, reviewer=reviewer)
    target = response_id or item_id or review_id
    if not names:
        if raw:
            cid='rih:credit:'+digest((target+locator).encode())[:24]
            s.node(cid,'credit_statement',raw,ORIGIN,{'raw':raw,'locator':locator})
            s.edge(target,'has_credit_statement',cid,ORIGIN,evidence=[source_id])
            s.issue('rih:unresolved_credit',source_id,issue or status)
        return
    for i,(name,role) in enumerate(names,1):
        if explicit_editor: role='editor'
        if response_id: role='respondent'
        mid='rih:mention:'+digest((target+locator+str(i)).encode())[:24]
        candidate='rih:name:'+digest(s_key(name).encode())[:24]
        if not s.exists(candidate):
            s.node(candidate,'name_candidate',name,ORIGIN,{'qualification':'Name bucket, not an identity.'})
        meta=dict(review_id=review_id,item_id=item_id,response_id=response_id,role=role,name=name,
                  affiliation=affiliation,locator=locator,candidate_id=candidate)
        s.node(mid,'person_mention',name,ORIGIN,dict(metadata=meta,source_record_id=source_id,
               source_json_sha256=fingerprint,source_raw_sha256=raw_fingerprint,recorded_credit=raw,extraction='saved_html_header',
               name_preparation='Leading honorifics removed for candidate lookup only.'))
        predicate='response_by' if response_id else ('credited_to' if item_id else 'reviewed_by')
        s.edge(target,predicate,mid,ORIGIN,evidence=[source_id],data={'locator':locator,'role':role})
        s.edge(mid,'has_name_candidate',candidate,ORIGIN,'candidate_only',[source_id])


def s_key(value):
    import unicodedata
    return unicodedata.normalize('NFC',clean(value)).casefold()


def import_corpus(s, root, inventory_path):
    root=Path(root).resolve()
    paths=sorted((root/'json').glob('*.json'))
    if not paths:
        raise ValueError('No Reviews in History JSON at '+str(root))
    counts=Counter(files=len(paths))
    with inventory_path.open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['relative_path','sha256'])
        for n,path in enumerate(paths,1):
            raw=path.read_bytes(); fingerprint=digest(raw)
            writer.writerow([str(path.relative_to(root)),fingerprint])
            rid=path.stem;sid='rih:source:'+rid
            row=json.loads(raw)
            html_path=root/'html'/f'{rid}.html.gz'
            html_bytes=html_path.read_bytes() if html_path.exists() else None
            raw_hash=digest(html_bytes) if html_bytes is not None else None
            # Missing expected paths are inventoried too: appearing during a
            # build is source drift, not an unnoticed partial import.
            writer.writerow([str(html_path.relative_to(root)),raw_hash or 'MISSING'])
            source=dict(relative_path=str(path.relative_to(root)),json_sha256=fingerprint,
                        raw_relative_path=str(html_path.relative_to(root)),raw_sha256=raw_hash,
                        source_url=row.get('source_url'),wayback_url=row.get('wayback_url'),
                        wayback_timestamp=row.get('wayback_timestamp'),source=ORIGIN)
            s.node(sid,'source_record','Reviews in History '+rid,ORIGIN,source)
            url=urlparse(row.get('source_url') or '')
            if (not rid.isdigit() or str(row.get('review_id'))!=rid or row.get('source')!=ORIGIN
                or url.hostname!='reviews.history.ac.uk' or url.path.rstrip('/')!='/review/'+rid):
                counts['excluded_identity']+=1;s.issue('rih:source_identity_mismatch',sid,'Source/path/record ID disagreement');continue
            if not row.get('content_ok') or not (row.get('body_text') or '').strip():
                counts['excluded_empty']+=1;s.issue('rih:empty_source',sid,'Source lacks usable review content');continue
            header=parse_header(gzip.decompress(html_bytes).decode('utf-8',errors='replace')) if html_bytes else None
            if not header or header['body_length']<100:
                counts['excluded_unverified_layout']+=1;s.issue('rih:unverified_layout',sid,'No supported saved review-body container');continue
            review='rih:review:'+rid; month,date_status=review_date(header['date_raw'])
            metadata=dict(source_id=sid,network_id=None,date_raw=header['date_raw'],date_month=month,date_status=date_status)
            s.node(review,'review_record',header['review_title'] or row.get('review_title') or 'Review '+rid,ORIGIN,
                   dict(metadata=metadata,original_id=rid,source=ORIGIN,body_sha256=header['body_sha256'],
                        body_length=header['body_length'],extraction='saved_html_sections'))
            counts['reviews']+=1
            counts['layout_'+header['layout']]+=1
            if month: counts['dated_reviews']+=1
            else:s.issue('rih:unparsed_review_date',sid,header['date_raw'])
            add_credit(s,header['reviewer'],review,sid,fingerprint,'.view-display-id-reviewer',
                       affiliation=header['affiliation'],reviewer=True,raw_fingerprint=raw_hash)
            if header['reviewer']:counts['reviews_with_reviewer']+=1
            for index,book in enumerate(header['books'],1):
                if not book['title']:continue
                item=f'rih:item:{rid}:{index}'
                codes=sorted({isbn13(v) for v in book['isbns_raw']}-{None})
                for code in book['isbns_raw']:
                    if not isbn13(code):s.issue('rih:invalid_isbn',sid,code)
                # Separate publication occurrence even where another review
                # names the same book. Matching is an explicit candidate edge.
                meta=dict(title=book['title'],credit=book['credit'],publication_year=book['publication_year'],
                          isbns=json.dumps(codes),identity_status='unresolved_source_occurrence')
                s.node(item,'bibliographic_item' if codes else 'reviewed_item',book['title'],ORIGIN,
                       dict(metadata=meta,source_record_id=sid,citation=book['citation'],imprint=book['imprint']))
                s.edge(review,'reviews_item',item,ORIGIN,evidence=[sid],data=book)
                counts['reviewed_items']+=1
                if book['credit']:counts['items_with_credit']+=1
                add_credit(s,book['credit'],review,sid,fingerprint,f'.view-display-id-summary block {index}',item_id=item,raw_fingerprint=raw_hash)
            for index,response in enumerate(header['responses'],1):
                response_id=f'rih:response:{rid}:{index}'
                s.node(response_id,'author_response','Response to review '+rid,ORIGIN,
                       dict(response,review_id=review,source_record_id=sid,locator='#author-response',
                            date_qualification='Posted timestamp as recorded; not assumed original response date.'))
                s.edge(response_id,'responds_to',review,ORIGIN,evidence=[sid])
                add_credit(s,response['author'],review,sid,fingerprint,f'#author-response {index}',response_id=response_id,raw_fingerprint=raw_hash)
                counts['author_responses']+=1
            seen=set()
            for subject in header['subjects']:
                if subject['key'] in seen:continue
                seen.add(subject['key']);nid='rih:subject:'+subject['key']
                if not s.exists(nid):s.node(nid,'review_subject',subject['label'],ORIGIN,subject)
                s.edge(review,'classified_under',nid,ORIGIN,evidence=[sid],data={'scope':'Source review classification, not person membership.'})
            if n%500==0:
                s.db.commit();print(f'Imported {n} Reviews in History source files',flush=True)
    return dict(counts)


def verify_inventory(root, inventory_path):
    expected=[]
    with inventory_path.open() as handle:
        for row in csv.DictReader(handle):
            path=root/row['relative_path']
            current=digest(path.read_bytes()) if path.exists() else 'MISSING'
            if current!=row['sha256']:raise ValueError('Reviews in History source changed: '+str(path))
            if row['relative_path'].startswith('json/'):expected.append(row['relative_path'])
    actual=sorted(str(p.relative_to(root)) for p in (root/'json').glob('*.json'))
    if sorted(expected)!=actual:raise ValueError('Reviews in History file inventory changed during build')


def reconcile(s):
    for cid,pid in s.db.execute("""SELECT c.id,p.id FROM nodes c JOIN nodes p ON p.name_key=c.name_key
            WHERE c.origin=? AND c.kind='name_candidate' AND p.kind='person' ORDER BY c.id,p.id""",(ORIGIN,)):
        s.edge(cid,'candidate_atlas_identity',pid,'reconciliation','candidate_only',
               data={'basis':'Equal normalized name after explicit honorific removal; not a resolved identity.'})
    for cid,hid in s.db.execute("""SELECT c.id,h.id FROM nodes c JOIN nodes h ON h.name_key=c.name_key
            WHERE c.origin=? AND c.kind='name_candidate' AND h.origin='hnet' AND h.kind='name_candidate'
            ORDER BY c.id,h.id""",(ORIGIN,)):
        s.edge(cid,'candidate_same_person',hid,'reconciliation','candidate_only',
               data={'basis':'Equal normalized names in two sources; both remain unresolved buckets.'})
    s.db.execute('CREATE TEMP TABLE publication_isbns(id TEXT,origin TEXT,isbn TEXT)')
    s.db.execute("""INSERT INTO publication_isbns SELECT n.id,n.origin,j.value FROM nodes n,
        json_each(json_extract(n.data,'$.metadata.isbns')) j
        WHERE n.kind IN ('bibliographic_item','reviewed_item')""")
    s.db.execute('CREATE INDEX publication_isbn ON publication_isbns(isbn,origin)')
    for rid,hid,codes in s.db.execute("""SELECT r.id,h.id,json_group_array(DISTINCT r.isbn)
            FROM publication_isbns r JOIN publication_isbns h ON h.isbn=r.isbn
            WHERE r.origin=? AND h.origin='hnet' GROUP BY r.id,h.id ORDER BY r.id,h.id""",(ORIGIN,)):
        s.edge(rid,'candidate_same_publication',hid,'reconciliation','candidate_only',
               data={'basis':'Shared checksum-valid ISBN; title, credits and edition still need review.',
                     'isbns':json.loads(codes)})
    s.db.execute('DROP TABLE publication_isbns')
