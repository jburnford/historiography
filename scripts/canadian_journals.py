"""Whole runs of the history journals of and about Canada: list, gap table, metadata harvest (2026-11-14).

Why (owner's probe, 2026-11-14, Guillaume Teasdale): most of a Canadian historian's articles and reviews are absent as
work nodes because the graph holds Canadian history journals only incidentally (cited articles, ORCID author-works,
JSTOR), never as whole runs. A person with no ORCID never reached the author-works route.

Subcommands (each re-runnable; done work is skipped):
  resolve   the journal list (JOURNALS below: name, scope, seed ISSNs) -> OpenAlex source records (filter issn:, else a
            title search) and Crossref journal records (/journals/{issn}); an ISSN is `verified` when the OpenAlex source
            record or the Crossref journal record lists it under a title that agrees with the journal's name.
            Writes data/journal-catalogue/canadian-journals-2026-11-14/journals.csv (+ resolve.json).
  harvest   OpenAlex works by source id (cursor paging, per-page 200, the project key in the api_key parameter, never
            printed, logged or stored), then Crossref works by ISSN (cursor, rows 1000, generic User-Agent, no contact
            details, stops on 429/403) for every journal; raw pages to /mnt/e/canadian-journals-2026-11-14/{openalex,
            crossref}/<jid>.jsonl.gz (written as .part, renamed when complete).
  normalise one record per work (OpenAlex first, Crossref for what OpenAlex lacks, matched by DOI) ->
            /mnt/e/canadian-journals-2026-11-14/records.parquet: authors with positions, ORCID, printed affiliations,
            type (article / review / editorial / front-matter), reviewed-book string, volume/issue/pages, DOI.
  gap       held (graph works of the journal, by ISSN or title key) vs available (OpenAlex, Crossref) by year ->
            data/journal-catalogue/canadian-journals-2026-11-14/gap-by-journal.csv, gap-by-year.csv.gz
  load      dedupe against the graph (DOI, then journal + year + title key + first page), classify reviews, write the
            missing works in the author-works works.csv.gz schema to data/graph/journal-runs/works.csv.gz and their
            printed author positions (no credits, no person minted) to data/graph/journal-runs/positions.csv.gz;
            reviews of graph books to data/graph/journal-runs/review-books.csv.gz (review-books.csv.gz schema).
  payoff    projection for named keys and a random sample of people with a Canadian History PhD.

Reads build/graph/*.parquet read-only. Never touches the key log, never builds the graph, never takes build/.heavy.lock.
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
OUT = Path('/mnt/e/canadian-journals-2026-11-14')
TRACK = ROOT / 'data/journal-catalogue/canadian-journals-2026-11-14'
GRAPH = ROOT / 'build/graph'
LOAD = ROOT / 'data/graph/journal-runs'
UA = 'historiography-kg-research/1.0'            # generic client name, no contact details
KEY_RE = re.compile(r'(api_key=)[^&\s]+')

# name, scope (history / near / adjacent), seed ISSNs (checked by `resolve`, never trusted as given), note
JOURNALS = [
    ('Canadian Historical Review', 'history', ['0008-3755', '1710-1093'], ''),
    ('Journal of the Canadian Historical Association', 'history', ['0847-4478', '1712-6274'], 'Revue de la Société historique du Canada'),
    ('Historical Papers / Communications historiques', 'history', ['0068-8878'], 'CHA annual report / papers before 1990'),
    ('Histoire sociale / Social History', 'history', ['0018-2257', '1918-6576'], ''),
    ("Revue d'histoire de l'Amérique française", 'history', ['0035-2357', '1492-1383'], ''),
    ('Acadiensis', 'history', ['0044-5851', '1712-7432'], ''),
    ('Labour / Le Travail', 'history', ['0700-3862', '1911-4842'], ''),
    ('BC Studies', 'history', ['0005-2949'], ''),
    ('Ontario History', 'history', ['0030-2953'], ''),
    ('Manitoba History', 'history', ['0226-5044'], ''),
    ('Prairie Forum', 'history', ['0317-6282'], ''),
    ('Saskatchewan History', 'history', ['0036-4908'], ''),
    ('Alberta History', 'history', ['0316-1552'], 'Alberta Historical Review before 1975'),
    ('Urban History Review', 'history', ['0703-0428', '1918-5138'], ''),
    ('Scientia Canadensis', 'history', ['0829-2507', '1918-7750'], ''),
    ('Canadian Bulletin of Medical History', 'history', ['0823-2105', '2371-0179'], ''),
    ('Historical Studies in Education', 'history', ['0843-5057', '1911-9674'], ''),
    ('Journal of Canadian Studies', 'history', ['0021-9495', '1911-0251'], 'interdisciplinary Canadian studies'),
    ('International Journal of Canadian Studies', 'history', ['1180-3991', '1923-5291'], 'interdisciplinary Canadian studies'),
    ('American Review of Canadian Studies', 'history', ['0272-2011', '1943-9954'], 'interdisciplinary Canadian studies'),
    ('British Journal of Canadian Studies', 'history', ['0269-9222', '1757-8078'], 'interdisciplinary Canadian studies'),
    ('Canadian Journal of History', 'history', ['0008-4107', '2292-8502'], 'Canadian journal, history of all regions'),
    ('Left History', 'history', ['1192-1927', '1913-9632'], ''),
    ('Material Culture Review', 'history', ['1718-1259', '1927-9264'], 'Material History Review before 2005'),
    ('Newfoundland and Labrador Studies', 'history', ['1719-1726', '1715-1430'], 'Newfoundland Studies before 2005'),
    ('The Northern Review', 'history', ['1183-3459', '1929-6657'], ''),
    ('Native Studies Review', 'history', ['0831-585X'], 'Indigenous studies: metadata of scholarship only (OCAP practice)'),
    ('Canadian Journal of Native Studies', 'history', ['0715-3244'], 'Indigenous studies: metadata of scholarship only (OCAP practice)'),
    ('Recherches amérindiennes au Québec', 'history', ['0318-4137', '1923-5151'], 'Indigenous studies: metadata of scholarship only (OCAP practice)'),
    ("Bulletin d'histoire politique", 'history', ['1201-0421', '1929-7653'], ''),
    ("Mens : revue d'histoire intellectuelle et culturelle", 'history', ['1492-8647', '1927-9299'], ''),
    ('Les Cahiers des dix', 'history', ['0575-089X', '1920-437X'], ''),
    ("Études d'histoire religieuse / Historical Studies", 'history', ['1193-199X', '1920-6267'], 'CCHA; earlier Sessions d\'étude / Study Sessions'),
    ('Globe : revue internationale d\'études québécoises', 'history', ['1481-5869', '1923-1903'], 'interdisciplinary Quebec studies'),
    ("Francophonies d'Amérique", 'history', ['1183-2487', '1710-1158'], 'interdisciplinary'),
    ('Recherches sociographiques', 'history', ['0034-1282', '1705-6225'], 'sociology and history of Quebec'),
    ('Quebec Studies', 'history', ['0737-3759', '2052-9198'], 'interdisciplinary Quebec studies'),
    ("Sessions d'étude (Société canadienne d'histoire de l'Église catholique)", 'history', ['0318-6172', '1927-7067'], 'CCHA French series, 1966-2012; Études d\'histoire religieuse from 1993'),
    ('HSTC Bulletin', 'history', ['0228-0086', '1918-7742'], 'Scientia Canadensis before 1987'),
    ('Canadian Journal of Health History (2022-)', 'history', ['2816-6469', '2816-6477'], 'Canadian Bulletin of Medical History renamed; new ISSNs'),
    ('Journal of the Canadian Church Historical Society', 'history', ['0008-3208'], ''),
    ('Canadian Military History', 'history', ['1195-8472'], ''),
    ('Michigan Historical Review', 'near', ['0890-1686'], 'near-Canada regional (Great Lakes)'),
    ('French Colonial History', 'near', ['1539-3402', '1543-7787'], 'near-Canada (French empire)'),
    ('Journal of Early American History', 'near', ['1877-0223', '1877-0703'], 'near-Canada (early America)'),
    ('Cahiers de géographie du Québec', 'adjacent', ['0007-9766', '1708-8968'], 'geography'),
    ('Anthropologie et Sociétés', 'adjacent', ['0702-8997', '1703-7921'], 'anthropology'),
    ('Studies in Religion / Sciences religieuses', 'adjacent', ['0008-4298', '2042-0587'], 'religious studies'),
]


def log(msg):
    msg = KEY_RE.sub(r'\1<redacted>', str(msg))
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + msg
    print(line, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / 'harvest.log', 'a') as f:
        f.write(line + '\n')


def jid(name):
    k = tkey(name)
    return re.sub(r'[^a-z0-9]+', '-', k).strip('-')[:40]


def tkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


STOP = {'the', 'of', 'de', 'd', 'l', 'la', 'le', 'les', 'du', 'des', 'and', 'et', 'revue', 'journal', 'review', 'a', 'au',
        'en', 'in', 'on', 'for', 'une'}


def name_words(s):
    return {w for w in tkey(s).split() if w not in STOP and len(w) > 1}


def titles_agree(a, b):
    wa, wb = name_words(a), name_words(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.6


_last = {}


def fetch(url, host_gap=0.25, tries=6):
    """GET JSON; polite gap per host; back-off on 5xx/timeouts; raises Refused on 429/403/401."""
    host = urllib.parse.urlparse(url).netloc
    for attempt in range(tries):
        wait = _last.get(host, 0) + host_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            if code == 404:
                return None
            if code in (429, 403, 401):
                raise Refused(f'HTTP {code} from {host}')
            if attempt == tries - 1:
                raise RuntimeError(f'HTTP {code} from {host}')
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == tries - 1:
                raise RuntimeError(f'{type(e).__name__} from {host}')
        time.sleep(2 ** attempt)


class Refused(Exception):
    pass


def oa_key():
    from openalex_ingest import load_api_key
    return load_api_key()


def oa_get(path, params, key):
    q = dict(params)
    if key:
        q['api_key'] = key
    return fetch('https://api.openalex.org/' + path + '?' + urllib.parse.urlencode(q), host_gap=0.12)


# ------------------------------------------------------------------ resolve

def resolve(args):
    key = oa_key()
    TRACK.mkdir(parents=True, exist_ok=True)
    rows, raw = [], {}
    for name, scope, seeds, note in JOURNALS:
        j = jid(name)
        rec = {'jid': j, 'name': name, 'scope': scope, 'seed_issns': seeds, 'note': note}
        # OpenAlex sources by ISSN, then by title search
        sel = 'id,display_name,issn_l,issn,works_count,host_organization_name,type,alternate_titles,first_publication_year,last_publication_year'
        d = oa_get('sources', {'filter': 'issn:' + '|'.join(seeds), 'select': sel, 'per-page': 25}, key) or {}
        srcs = [s for s in d.get('results', []) if titles_agree(name, s['display_name'])
                or any(titles_agree(name, t) for t in s.get('alternate_titles') or [])]
        if not srcs:
            d = oa_get('sources', {'search': name, 'select': sel, 'per-page': 10}, key) or {}
            srcs = [s for s in d.get('results', []) if titles_agree(name, s['display_name'])][:2]
            rec['openalex_by'] = 'title-search' if srcs else 'none'
        else:
            rec['openalex_by'] = 'issn'
        rec['openalex'] = srcs
        # Crossref journal records for each seed ISSN and each OpenAlex ISSN
        cand = list(dict.fromkeys(seeds + [i for s in srcs for i in (s.get('issn') or [])]))
        cr = {}
        for issn in cand:
            try:
                x = fetch(f'https://api.crossref.org/journals/{issn}', host_gap=0.3)
            except Refused as e:
                log(f'crossref refused: {e}; stopping Crossref lookups')
                x = None
            if x and x.get('message'):
                m = x['message']
                cr[issn] = {'title': m.get('title'), 'issn': [i.get('value') for i in m.get('issn-type') or []],
                            'publisher': m.get('publisher'), 'total_dois': (m.get('counts') or {}).get('total-dois'),
                            'agrees': titles_agree(name, m.get('title') or '')}
        rec['crossref'] = cr
        verified = {}
        for s in srcs:
            for i in s.get('issn') or []:
                verified.setdefault(i, []).append('openalex')
        for i, m in cr.items():
            if m['agrees']:
                for x in m['issn']:
                    verified.setdefault(x, []).append('crossref')
        rec['issns_verified'] = {i: sorted(set(v)) for i, v in verified.items()}
        rec['seeds_unverified'] = [i for i in seeds if i not in verified]
        raw[j] = rec
        log(f"{name}: OpenAlex {[(s['id'].rsplit('/', 1)[-1], s['display_name'], s.get('works_count')) for s in srcs]} "
            f"Crossref {[(i, m['title'], m['total_dois']) for i, m in cr.items() if m['agrees']]} unverified seeds {rec['seeds_unverified']}")
    (TRACK / 'resolve.json').write_text(json.dumps(raw, ensure_ascii=False, indent=1) + '\n')
    with open(TRACK / 'journals.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['jid', 'name', 'scope', 'issns_verified', 'verified_by', 'seed_issns_unverified', 'openalex_sources',
                    'openalex_names', 'openalex_works', 'openalex_by', 'crossref_titles', 'crossref_dois', 'publisher', 'note'])
        for j, r in raw.items():
            iv = r['issns_verified']
            crs = {i: m for i, m in r['crossref'].items() if m['agrees']}
            w.writerow([j, r['name'], r['scope'], ';'.join(sorted(iv)), ';'.join(f"{i}:{'+'.join(v)}" for i, v in sorted(iv.items())),
                        ';'.join(r['seeds_unverified']),
                        ';'.join(s['id'].rsplit('/', 1)[-1] for s in r['openalex']),
                        ' | '.join(s['display_name'] for s in r['openalex']),
                        ';'.join(str(s.get('works_count')) for s in r['openalex']), r['openalex_by'],
                        ' | '.join(sorted({m['title'] for m in crs.values()})),
                        max([m['total_dois'] or 0 for m in crs.values()], default=0),
                        ' | '.join(sorted(({m['publisher'] or '' for m in crs.values()} | {s.get('host_organization_name') or '' for s in r['openalex']}) - {''})),
                        r['note']])
    log(f'resolve: {len(raw)} journals -> {TRACK / "journals.csv"}')


# ------------------------------------------------------------------ harvest

OA_SELECT = ('id,doi,title,publication_year,publication_date,type,language,authorships,biblio,primary_location,'
             'is_retracted,cited_by_count')
CR_SELECT = 'DOI,title,subtitle,author,issued,published-print,published-online,container-title,ISSN,type,volume,issue,page'


def journal_rows():
    with open(TRACK / 'journals.csv', newline='') as f:
        return list(csv.DictReader(f))


def write_pages(path, it):
    part = path.with_name(path.name + '.part')
    n = 0
    with gzip.open(part, 'wt', encoding='utf-8') as o:
        for rec in it:
            o.write(json.dumps(rec, ensure_ascii=False) + '\n')
            n += 1
    part.rename(path)
    return n


def oa_works(src, key, stats):
    cursor = '*'
    while cursor:
        d = oa_get('works', {'filter': f'primary_location.source.id:{src}', 'select': OA_SELECT, 'per-page': 200,
                             'cursor': cursor}, key)
        stats['oa_requests'] += 1
        if not d:
            return
        for r in d.get('results', []):
            yield r
        cursor = (d.get('meta') or {}).get('next_cursor')
        if not d.get('results'):
            return


def cr_works(issn, stats, union=None):
    cursor = '*'
    while cursor:
        if union:       # every ISSN of the title at once: /journals/{issn}/works misses records deposited under the other
            url = ('https://api.crossref.org/works?' + urllib.parse.urlencode(
                {'rows': 1000, 'cursor': cursor, 'select': CR_SELECT, 'filter': ','.join(f'issn:{i}' for i in union)}))
        else:
            url = (f'https://api.crossref.org/journals/{issn}/works?' +
                   urllib.parse.urlencode({'rows': 1000, 'cursor': cursor, 'select': CR_SELECT}))
        d = fetch(url, host_gap=0.4)
        stats['cr_requests'] += 1
        if not d:
            return
        items = d['message'].get('items') or []
        for r in items:
            yield r
        if not items:
            return
        cursor = d['message'].get('next-cursor')


def harvest(args):
    key = oa_key()
    stats = Counter()
    (OUT / 'openalex').mkdir(parents=True, exist_ok=True)
    (OUT / 'crossref').mkdir(parents=True, exist_ok=True)
    counts = json.loads((OUT / 'counts.json').read_text()) if (OUT / 'counts.json').exists() else {}
    cr_stopped = False
    for j in journal_rows():
        c = counts.setdefault(j['jid'], {})
        for src in filter(None, j['openalex_sources'].split(';')):
            path = OUT / 'openalex' / f"{j['jid']}__{src}.jsonl.gz"
            if path.exists():
                continue
            n = write_pages(path, oa_works(src, key, stats))
            c[f'openalex:{src}'] = n
            log(f"openalex {j['name']} {src}: {n}")
        cr_issns = [x.split(':')[0] for x in j['verified_by'].split(';') if 'crossref' in x]
        if cr_issns and not cr_stopped:
            path = OUT / 'crossref' / f"{j['jid']}.jsonl.gz"
            if not path.exists():
                try:
                    n = write_pages(path, cr_works(cr_issns[0], stats))
                    c[f'crossref:{cr_issns[0]}'] = n
                    log(f"crossref {j['name']} {cr_issns[0]}: {n}")
                except Refused as e:
                    log(f'crossref stopped: {e}')
                    cr_stopped = True
        # second pass: a title whose Crossref count falls short of the journal record's DOI total, by all its ISSNs
        if cr_issns and not cr_stopped and c.get(f'crossref:{cr_issns[0]}', 0) < 0.95 * int(j['crossref_dois'] or 0):
            path = OUT / 'crossref' / f"{j['jid']}__union.jsonl.gz"
            if not path.exists():
                try:
                    n = write_pages(path, cr_works(None, stats, union=cr_issns))
                    c['crossref:union'] = n
                    log(f"crossref union {j['name']} {cr_issns}: {n}")
                except Refused as e:
                    log(f'crossref stopped: {e}')
                    cr_stopped = True
        (OUT / 'counts.json').write_text(json.dumps(counts, indent=1) + '\n')
    log(f'harvest done: {dict(stats)}')


# ------------------------------------------------------------------ normalise

FRONT = re.compile(r"^\s*(?:front matter|back matter|table des mati[eè]res|sommaire|contents|table of contents|index|"
                   r"liste des (?:collaborat|auteur)|notes? (?:sur les|biographiques|on contributors)|contributors|"
                   r"collaborat(?:eurs|rices)|books received|publications re[çc]ues|livres re[çc]us|errat(?:um|a)|"
                   r"corrigendum|issue information|masthead|cover|couverture|pages? (?:liminaires|de garde)|"
                   r"advertis|annonces?|notes and comments|recent publications|publications r[ée]centes|"
                   r"bibliographie d'histoire de l'am[ée]rique fran[çc]aise|recent publications relating to canada|"
                   r"chronique|nouvelles|news and notes|[ée]v[ée]nements|announcements?)\b", re.I)
EDITORIAL = re.compile(r"^\s*(?:editorial|[ée]ditorial|editor'?s'? (?:note|introduction|preface)|note de la r[ée]daction|"
                       r"mot de la r[ée]daction|mot du directeur|pr[ée]sentation|avant-propos|foreword|preface|"
                       r"introduction(?: to the (?:special|theme) (?:issue|section))?|liminaire|in memoriam|obituar|"
                       r"n[ée]crologie|hommage)\b", re.I)


# reviews the shared review_like test misses (hand-checked samples, 2026-11-14): 'Title by Given Family' (Project MUSE
# labels, Canadian Journal of History 'Title, by Name'), and 'Given Family, Title, Place, Publisher, year' when the label
# names a press / pages or prints the family in capitals ('Gustave LANCTÔT, Montréal sous Maisonneuve')
BY_END = re.compile(r"\s(?:by|par|edited by|ed\. by)\s+(?:[A-ZÀ-Þ][\w.'’\-]*\s+){0,4}[A-ZÀ-Þ][\w'’\-]+(?:\s*(?:,|and|et|&)\s*"
                    r"(?:[A-ZÀ-Þ][\w.'’\-]*\s+){0,4}[A-ZÀ-Þ][\w'’\-]+)*\s*(?:\((?:review|eds?\.?)\))?\s*$")
PUB = re.compile(r"\b(?:Press|Presses|University|Universit[éy]|Universitaires|[ÉE]ditions?|Verlag|Publishers?|Publishing|Books|Fides|"
                 r"Bor[ée]al|Septentrion|Hurtubise|Gallimard|Seuil|PUF|PUL|PUQ|Leméac|VLB|Hachette|Routledge|Palgrave|pp\.|pages)(?=\W|$)")
CAPS = re.compile(r"^[^,:]{0,40}\b[A-ZÀ-Þ]{3,}\b")


DECADE = re.compile(r'\b(\d{2,4})[sS]\b')


def review_extra(t):
    from review_label_parse import parse
    if BY_END.search(t):
        return True
    p = parse(t)
    return bool(p and p['reads'] and (PUB.search(t) or CAPS.search(t)))


def classify(title, oa_type=None, cr_type=None):
    from review_books import review_like
    t = (title or '').strip()
    if oa_type in ('book-review',):
        return 'review'
    if oa_type in ('paratext', 'erratum', 'supplementary-materials', 'retraction') or cr_type in ('journal-issue', 'component'):
        return 'front-matter'
    if not t:
        return 'front-matter'
    if FRONT.match(t):
        return 'front-matter'
    if oa_type == 'editorial' or EDITORIAL.match(t):
        return 'editorial'
    # review_books.CITATION reads a decade ('1850s') as a page count ('S.'); strip the decade's 's' first (defect found
    # 2026-11-14: 15,613 graph labels are review-like only by a decade)
    if review_like(DECADE.sub(r'\1', t), None) or review_extra(t):
        return 'review'
    if oa_type == 'letter':
        return 'other'
    return 'article'


def reviewed_book(title, kind):
    if kind != 'review':
        return ''
    from review_books import clean_label
    body, _ = clean_label(title or '')
    return re.sub(r'\s+', ' ', body).strip()[:500]


def oa_record(d, j):
    b = d.get('biblio') or {}
    auths = []
    for i, a in enumerate(d.get('authorships') or []):
        au = a.get('author') or {}
        auths.append(dict(pos=i + 1, name=au.get('display_name') or a.get('raw_author_name') or '',
                          raw=a.get('raw_author_name') or '', oa_author=(au.get('id') or '').rsplit('/', 1)[-1],
                          orcid=(au.get('orcid') or a.get('raw_orcid') or '').rsplit('/', 1)[-1],
                          institutions=[x.get('display_name') for x in a.get('institutions') or [] if x.get('display_name')],
                          rors=[(x.get('ror') or '').rsplit('/', 1)[-1] for x in a.get('institutions') or [] if x.get('ror')],
                          raw_aff=(a.get('raw_affiliation_strings') or [])[:3]))
    doi = (d.get('doi') or '').replace('https://doi.org/', '').lower()
    kind = classify(d.get('title'), oa_type=d.get('type'))
    return dict(jid=j['jid'], journal=j['name'], scope=j['scope'], issn_l=(j['issns_verified'].split(';') or [''])[0],
                openalex=d['id'].rsplit('/', 1)[-1], doi=doi, title=(d.get('title') or '').strip(),
                year=d.get('publication_year'), date=d.get('publication_date') or '', oa_type=d.get('type') or '',
                cr_type='', kind=kind, reviewed_book=reviewed_book(d.get('title'), kind), volume=b.get('volume') or '',
                issue=b.get('issue') or '', first_page=b.get('first_page') or '', last_page=b.get('last_page') or '',
                language=d.get('language') or '', authors=auths, author_source='openalex' if auths else '',
                source='openalex')


def cr_year(d):
    for k in ('issued', 'published-print', 'published-online'):
        p = ((d.get(k) or {}).get('date-parts') or [[None]])[0]
        if p and p[0]:
            return int(p[0])
    return None


def cr_authors(d):
    out = []
    for i, a in enumerate(d.get('author') or []):
        nm = ' '.join(x for x in (a.get('given'), a.get('family')) if x) or a.get('name') or ''
        out.append(dict(pos=i + 1, name=nm, raw=nm, given=a.get('given') or '', family=a.get('family') or '', oa_author='',
                        orcid=(a.get('ORCID') or '').rsplit('/', 1)[-1], institutions=[], rors=[],
                        raw_aff=[x.get('name') for x in a.get('affiliation') or [] if x.get('name')][:3]))
    return out


def cr_record(d, j):
    title = ' '.join((d.get('title') or [''])[:1]).strip()
    if d.get('subtitle'):
        title = f"{title}: {d['subtitle'][0]}" if title else d['subtitle'][0]
    kind = classify(title, cr_type=d.get('type'))
    pages = (d.get('page') or '').split('-')
    auths = cr_authors(d)
    return dict(jid=j['jid'], journal=j['name'], scope=j['scope'], issn_l=(j['issns_verified'].split(';') or [''])[0],
                openalex='', doi=(d.get('DOI') or '').lower(), title=title, year=cr_year(d), date='', oa_type='',
                cr_type=d.get('type') or '', kind=kind, reviewed_book=reviewed_book(title, kind),
                volume=d.get('volume') or '', issue=d.get('issue') or '', first_page=pages[0] if pages else '',
                last_page=pages[1] if len(pages) > 1 else '', language=d.get('language') or '', authors=auths,
                author_source='crossref' if auths else '', source='crossref')


def normalise(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    recs, stats = [], Counter()
    for j in journal_rows():
        by_doi = {}
        for fn in sorted((OUT / 'openalex').glob(f"{j['jid']}__*.jsonl.gz")):
            with gzip.open(fn, 'rt', encoding='utf-8') as f:
                for line in f:
                    r = oa_record(json.loads(line), j)
                    recs.append(r)
                    stats['openalex'] += 1
                    if r['doi']:
                        by_doi[r['doi']] = r
        for fn in sorted((OUT / 'crossref').glob(f"{j['jid']}*.jsonl.gz")):
            if not (fn.name == f"{j['jid']}.jsonl.gz" or fn.name == f"{j['jid']}__union.jsonl.gz"):
                continue
            with gzip.open(fn, 'rt', encoding='utf-8') as f:
                for line in f:
                    d = json.loads(line)
                    doi = (d.get('DOI') or '').lower()
                    r = by_doi.get(doi)
                    if r:
                        stats['crossref_on_openalex'] += 1
                        ca = cr_authors(d)
                        if not r['authors'] and ca:              # OpenAlex lacks the author list: Crossref's
                            r['authors'], r['author_source'] = ca, 'crossref'
                            stats['authors_from_crossref'] += 1
                        elif r['authors'] and ca and len(ca) == len(r['authors']):
                            for a, c in zip(r['authors'], ca):      # Crossref ORCIDs / affiliations as printed
                                a['orcid'] = a['orcid'] or c['orcid']
                                a['raw_aff'] = a['raw_aff'] or c['raw_aff']
                                a['given'], a['family'] = c['given'], c['family']
                        r['cr_type'] = d.get('type') or ''
                        for k in ('volume', 'issue'):
                            r[k] = r[k] or d.get(k) or ''
                        continue
                    r = cr_record(d, j)
                    recs.append(r)
                    stats['crossref_only'] += 1
                    if r['doi']:
                        by_doi[r['doi']] = r
    for i, r in enumerate(recs):
        r['rid'] = i
        for a in r['authors']:
            a.setdefault('given', '')
            a.setdefault('family', '')
        r['n_authors'] = len(r['authors'])
        r['authors'] = json.dumps(r['authors'], ensure_ascii=False)
        stats[f"kind|{r['kind']}"] += 1
    pq.write_table(pa.Table.from_pylist(recs), OUT / 'records.parquet')
    stats['records'] = len(recs)
    log(f'normalise: {json.dumps(dict(stats))}')
    (OUT / 'normalise-stats.json').write_text(json.dumps(dict(stats), indent=1) + '\n')


# ------------------------------------------------------------------ gap and dedupe

def journal_keys(rows):
    """title key -> jid for the list names and the OpenAlex / Crossref titles that agree with them (two content words
    or more, so 'Journal of History' never claims other journals); ISSN -> jid"""
    tk, iss = {}, {}
    raw = json.loads((TRACK / 'resolve.json').read_text())
    for j in rows:
        r = raw[j['jid']]
        names = [j['name']]       # never the halves of a bilingual title: 'Social History' is another journal
        names += [s['display_name'] for s in r['openalex']] + [m['title'] for m in r['crossref'].values() if m['agrees'] and m['title']]
        for n in names:
            if n == j['name'] or len(name_words(n)) >= 2:
                tk.setdefault(tkey(n), j['jid'])
        for n in [t for s in r['openalex'] for t in s.get('alternate_titles') or []]:
            a, b = name_words(n), name_words(j['name'])
            if len(a) >= 2 and len(a & b) / max(len(a), len(b)) >= 0.6:     # alternates must agree both ways
                tk.setdefault(tkey(n), j['jid'])
        for i in filter(None, j['issns_verified'].split(';')):
            iss.setdefault(i, j['jid'])
    return tk, iss


def wtitle(t):
    """title key: no HTML, no 'Review of' / '(review)' markers (JSTOR labels a review 'Review of <book>', Project MUSE
    '<book> (review)', OpenAlex often just '<book>')"""
    from review_books import clean_label
    body, _ = clean_label(re.sub(r'<[^>]+>', ' ', t or ''))
    return tkey(body)[:90]


def mtitle(t):
    """main-title key (before the first colon / ' by ' / ', by'), 3 words or more, else ''"""
    k = wtitle(re.split(r':|\s[-–—]\s|,?\s+by\s+', re.sub(r'<[^>]+>', ' ', t or ''), maxsplit=1)[0])
    return k if len(k.split()) >= 3 else ''


def graph_side(db, rows):
    """graph works per jid (by ISSN or journal title key) -> table gj(key, jid, year, tk, kind); DOI and OpenAlex anchors
    -> table ga(a, key)"""
    import pyarrow as pa
    tk, iss = journal_keys(rows)
    pairs = db.execute(f"SELECT DISTINCT journal, issn FROM '{GRAPH}/work.parquet' WHERE journal IS NOT NULL OR issn IS NOT NULL").fetchall()
    jj, ji, jv = [], [], []
    for jn, isn in pairs:
        v = iss.get(isn) if isn else None
        v = v or tk.get(tkey(jn)) if jn else v
        if v:
            jj.append(jn); ji.append(isn); jv.append(v)
    db.register('jmap', pa.table({'journal': jj, 'issn': ji, 'jid': jv}))
    db.execute(f"""CREATE OR REPLACE TABLE gj AS SELECT w.key, m.jid, w.year, w.kind, w.label FROM '{GRAPH}/work.parquet' w
                   JOIN jmap m ON m.journal IS NOT DISTINCT FROM w.journal AND m.issn IS NOT DISTINCT FROM w.issn""")
    keys = db.execute('SELECT key, label FROM gj').fetchall()
    db.register('gjt', pa.table({'key': [k for k, _ in keys], 'tk': [wtitle(l) for _, l in keys],
                                 'mk': [mtitle(l) for _, l in keys]}))
    db.execute('CREATE OR REPLACE TABLE gj2 AS SELECT gj.*, gjt.tk, gjt.mk FROM gj JOIN gjt USING (key)')
    db.execute(f"""CREATE OR REPLACE TABLE ga AS SELECT lower(a) AS a, key FROM (SELECT key, unnest(anchors) AS a
                   FROM '{GRAPH}/work.parquet') WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'""")


def match_records(db):
    """records -> graph node: DOI, then OpenAlex id, then the same journal + year (within one) + title key; then a
    graph work with no journal of the same title key and year (titles of five words or more)."""
    import pyarrow as pa
    recs = db.execute(f"SELECT rid, jid, doi, openalex, title, year, kind, first_page FROM '{OUT}/records.parquet'").fetchall()
    db.register('rt', pa.table({'rid': [r[0] for r in recs], 'tk': [wtitle(r[4]) for r in recs],
                                'mk': [mtitle(r[4]) for r in recs]}))
    db.execute(f"""CREATE OR REPLACE TABLE rec AS SELECT r.*, rt.tk, rt.mk FROM '{OUT}/records.parquet' r
                   JOIN rt USING (rid)""")
    db.execute("""CREATE OR REPLACE TABLE m1 AS SELECT rid, min(ga.key) AS node, 'doi' AS basis, count(DISTINCT ga.key) AS n
                  FROM rec JOIN ga ON ga.a = 'doi:' || rec.doi WHERE rec.doi <> '' GROUP BY rid""")
    db.execute("""INSERT INTO m1 SELECT rid, min(ga.key), 'openalex', count(DISTINCT ga.key) FROM rec
                  JOIN ga ON ga.a = 'openalex:' || lower(rec.openalex) WHERE rec.openalex <> '' AND rid NOT IN (SELECT rid FROM m1)
                  GROUP BY rid""")
    db.execute("""INSERT INTO m1 SELECT rid, min(gj2.key), 'journal-year-title', count(DISTINCT gj2.key) FROM rec
                  JOIN gj2 ON gj2.jid = rec.jid AND gj2.tk = rec.tk AND abs(coalesce(gj2.year, 0) - coalesce(rec.year, 0)) <= 1
                  WHERE length(rec.tk) >= 12 AND rid NOT IN (SELECT rid FROM m1) GROUP BY rid""")
    # the same main title in the same journal within a year (a JSTOR 'Review of X' and a MUSE 'X: subtitle by Y')
    db.execute("""INSERT INTO m1 SELECT rid, min(gj2.key), 'journal-year-main-title', count(DISTINCT gj2.key) FROM rec
                  JOIN gj2 ON gj2.jid = rec.jid AND gj2.mk = rec.mk AND abs(coalesce(gj2.year, 0) - coalesce(rec.year, 0)) <= 1
                  WHERE rec.mk <> '' AND rid NOT IN (SELECT rid FROM m1) GROUP BY rid""")
    return db.execute('SELECT basis, count(*) FROM m1 GROUP BY 1').fetchall()


def gap(args):
    import duckdb
    rows = journal_rows()
    db = duckdb.connect()
    db.execute("SET memory_limit='5GB'; SET threads=4")
    graph_side(db, rows)
    by_basis = match_records(db)
    # the no-journal title twin pass (graph works with no journal; whole title key of 5+ words, same year)
    db.execute(f"""CREATE OR REPLACE TABLE nj AS SELECT key, year, label FROM '{GRAPH}/work.parquet'
                   WHERE journal IS NULL AND kind IN ('article', 'review', 'other') AND year >= 1900""")
    tks = db.execute("SELECT DISTINCT tk FROM rec WHERE rid NOT IN (SELECT rid FROM m1) AND length(tk) >= 25").fetchall()
    want = {t for (t,) in tks if len(t.split()) >= 5}
    hits = [(k, y, wtitle(l)) for k, y, l in db.execute('SELECT key, year, label FROM nj').fetchall() if wtitle(l) in want]
    import pyarrow as pa
    db.register('njt', pa.table({'key': [h[0] for h in hits], 'year': [h[1] for h in hits], 'tk': [h[2] for h in hits]}))
    db.execute("""INSERT INTO m1 SELECT rid, min(njt.key), 'title-year-no-journal', count(DISTINCT njt.key) FROM rec
                  JOIN njt ON njt.tk = rec.tk AND njt.year = rec.year WHERE rid NOT IN (SELECT rid FROM m1) GROUP BY rid""")
    by_basis = db.execute('SELECT basis, count(*) FROM m1 GROUP BY 1 ORDER BY 2 DESC').fetchall()
    db.execute('CREATE OR REPLACE TABLE recm AS SELECT rec.*, m1.node, m1.basis FROM rec LEFT JOIN m1 USING (rid)')
    db.execute(f"COPY (SELECT rid, jid, doi, openalex, node, basis FROM recm WHERE node IS NOT NULL) TO '{OUT}/matched.parquet'")
    TRACK.mkdir(parents=True, exist_ok=True)
    out = []
    held = dict(db.execute('SELECT jid, count(*) FROM gj GROUP BY 1').fetchall())
    for j in rows:
        x = db.execute("""SELECT count(*), count(*) FILTER (WHERE source = 'openalex'), count(*) FILTER (WHERE source = 'crossref'),
                          count(*) FILTER (WHERE node IS NOT NULL),
                          count(*) FILTER (WHERE node IS NULL AND kind = 'article'),
                          count(*) FILTER (WHERE node IS NULL AND kind = 'review'),
                          count(*) FILTER (WHERE node IS NULL AND kind NOT IN ('article', 'review')),
                          min(year), max(year) FROM recm WHERE jid = ?""", [j['jid']]).fetchone()
        hy = db.execute('SELECT min(year), max(year) FROM gj WHERE jid = ?', [j['jid']]).fetchone()
        out.append(dict(jid=j['jid'], name=j['name'], scope=j['scope'], graph_held_by_journal=held.get(j['jid'], 0),
                        graph_years=f'{hy[0]}-{hy[1]}' if hy[0] else '', available_records=x[0], openalex_records=x[1],
                        crossref_only_records=x[2], available_in_graph=x[3], missing_articles=x[4], missing_reviews=x[5],
                        missing_other=x[6], available_years=f'{x[7]}-{x[8]}' if x[7] else ''))
    with open(TRACK / 'gap-by-journal.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    yr = db.execute("""WITH a AS (SELECT jid, year, count(*) AS available, count(node) AS in_graph,
                                  count(*) FILTER (WHERE node IS NULL AND kind = 'review') AS missing_reviews
                                  FROM recm GROUP BY 1, 2),
                            h AS (SELECT jid, year, count(*) AS held FROM gj GROUP BY 1, 2)
                       SELECT coalesce(a.jid, h.jid) AS jid, coalesce(a.year, h.year) AS year, coalesce(h.held, 0) AS held_by_journal,
                              coalesce(a.available, 0) AS available, coalesce(a.in_graph, 0) AS available_in_graph,
                              coalesce(a.missing_reviews, 0) AS missing_reviews
                       FROM a FULL JOIN h ON a.jid = h.jid AND a.year IS NOT DISTINCT FROM h.year ORDER BY 1, 2""").fetchall()
    with gzip.open(TRACK / 'gap-by-year.csv.gz', 'wt', newline='') as f:
        w = csv.writer(f)
        w.writerow(['jid', 'year', 'held_by_journal', 'available', 'available_in_graph', 'missing_reviews'])
        w.writerows(yr)
    tot = Counter()
    for r in out:
        for k, v in r.items():
            if isinstance(v, int):
                tot[(r['scope'], k)] += v
    rep = {'match_basis': dict(by_basis), 'totals_by_scope': {f'{a}|{b}': v for (a, b), v in sorted(tot.items())}}
    (TRACK / 'gap-report.json').write_text(json.dumps(rep, indent=1) + '\n')
    log(f'gap: {json.dumps(rep)}')


# ------------------------------------------------------------------ load (tables only; nothing applied)

AW_COLS = ['id', 'openalex', 'doi', 'title', 'year', 'oa_type', 'kind', 'journal', 'issn_l', 'source', 'source_type',
           'publisher', 'language', 'container_title', 'container_isbn', 'container_editors', 'volume_work', 'volume_basis',
           'n_authors', 'authorships', 'twin_of', 'twin_basis', 'flags',
           # added for this table (the build reads columns by name)
           'volume', 'issue', 'pages', 'reviewed_book', 'jid', 'scope', 'author_source', 'alias_ids']
POS_COLS = ['role', 'source', 'work', 'pos', 'n_auth', 'name', 'given', 'family', 'year', 'journal', 'kind', 'title', 'orcid',
            'oa_author', 'rors', 'insts', 'raw_aff']
RB_COLS = ['review', 'book', 'rule', 'basis', 'review_kind', 'review_resolution', 'book_title', 'book_year', 'book_lccn',
           'lc_main_lcnaf', 'book_families']


def main_tkey(t):
    t = re.split(r'\s+[:;=]\s+|:\s|\s\[|\s\(', t or '', maxsplit=1)[0]
    return tkey(t)


def missing_records(db):
    """records the graph lacks (not front matter, a title), one per journal + year + title key (OpenAlex with authors
    first, then a DOI)"""
    db.execute(f"CREATE OR REPLACE TABLE matched AS SELECT * FROM '{OUT}/matched.parquet'")
    recs = db.execute(f"""SELECT r.* FROM '{OUT}/records.parquet' r
                          ANTI JOIN matched m ON m.rid = r.rid
                          WHERE r.kind <> 'front-matter' AND coalesce(r.title, '') <> ''""").fetch_df()
    recs['tk'] = recs['title'].map(wtitle)
    recs['rank'] = (recs['n_authors'] == 0).astype(int) * 4 + (recs['source'] != 'openalex').astype(int) * 2 + (recs['doi'] == '').astype(int)
    recs = recs.sort_values(['rank', 'rid'])
    key = ['jid', 'year', 'tk', 'first_page']
    long_t = recs['tk'].str.len() >= 12
    first = recs[long_t].groupby(key, dropna=False)['rid'].transform('first')
    recs['keep_rid'] = recs['rid']
    recs.loc[long_t, 'keep_rid'] = first
    dup = recs['keep_rid'] != recs['rid']
    ids = lambda r: f'doi:{r.doi}' if r.doi else f'openalex:{r.openalex}'
    alias = defaultdict(list)
    for r in recs[dup].itertuples():
        alias[r.keep_rid].append(ids(r))
    recs['alias_ids'] = recs['rid'].map(lambda x: ';'.join(alias.get(x, [])))
    return recs[~dup].copy(), int(dup.sum())


def review_ties(db, recs):
    """missing reviews whose book the graph holds: the review_label_parse readings (book title + reviewed author) or,
    for records the source types as book reviews with the book's title as their title, the whole title; a graph book
    (kind book) with the same main-title key (3+ words), dated 0-6 years before the review, the only such book;
    a parsed author family must be a credited author's family of that book."""
    from review_label_parse import parse
    import pyarrow as pa
    want = {}
    for r in recs.itertuples():
        if r.kind != 'review' or not r.year:
            continue
        reads = []
        p = parse(r.title)
        if p:
            reads += [(x['title'], [n.split(',')[0] for n in x['names']]) for x in p['reads']]
        if r.oa_type == 'book-review' or not reads:
            reads.append((r.reviewed_book or r.title, []))
        for t, fams in reads:
            k = main_tkey(t)
            if len(k.split()) >= 3:
                want.setdefault(k, []).append((r.Index, int(r.year), fams))
    books = defaultdict(list)
    for key, label, year in db.execute(f"SELECT key, label, year FROM '{GRAPH}/work.parquet' WHERE kind = 'book'").fetchall():
        k = main_tkey(label)
        if k in want:
            books[k].append((key, year, label))
    cand_keys = sorted({b[0] for v in books.values() for b in v})
    fams = defaultdict(set)
    if cand_keys:
        db.register('ck', pa.table({'k': cand_keys}))
        for w, lab in db.execute(f"""SELECT a."to", p.label FROM '{GRAPH}/authored.parquet' a JOIN '{GRAPH}/person.parquet' p
                                     ON p.key = a."from" WHERE a."to" IN (SELECT k FROM ck)""").fetchall():
            fams[w].add(tkey((lab or '').split(',')[0]))
    ties, held = {}, Counter()
    for k, uses in want.items():
        for idx, ry, fm in uses:
            if idx in ties:
                continue
            c = [b for b in books.get(k, []) if b[1] and 0 <= ry - b[1] <= 6]
            if fm:
                c = [b for b in c if fams[b[0]] & {tkey(f) for f in fm}]
            if len(c) == 1:
                ties[idx] = (c[0], 'label' if fm else 'title')
            elif len(c) > 1:
                held['several_books'] += 1
    return ties, held


def load(args):
    import duckdb
    db = duckdb.connect()
    db.execute("SET memory_limit='5GB'; SET threads=4")
    recs, n_dup = missing_records(db)
    ties, held = review_ties(db, recs)
    LOAD.mkdir(parents=True, exist_ok=True)
    stats = Counter(within_harvest_duplicates=n_dup)
    files = {'history': gzip.open(LOAD / 'works.csv.gz', 'wt', newline='', encoding='utf-8'),
             'adjacent': gzip.open(LOAD / 'works-adjacent.csv.gz', 'wt', newline='', encoding='utf-8')}
    ws = {k: csv.DictWriter(f, fieldnames=AW_COLS) for k, f in files.items()}
    for w in ws.values():
        w.writeheader()
    pf = gzip.open(LOAD / 'positions.csv.gz', 'wt', newline='', encoding='utf-8')
    pw = csv.DictWriter(pf, fieldnames=POS_COLS)
    pw.writeheader()
    rb = []
    for r in recs.itertuples():
        wid = f'doi:{r.doi}' if r.doi else f'openalex:{r.openalex}'
        bucket = 'adjacent' if r.scope == 'adjacent' else 'history'
        auths = json.loads(r.authors)
        kind = {'editorial': 'other', 'other': 'other'}.get(r.kind, r.kind)
        flags = [x for x in (r.kind if r.kind in ('editorial',) else '', r.scope if r.scope != 'history' else '') if x]
        ws[bucket].writerow(dict(
            id=wid, openalex=r.openalex, doi=r.doi, title=r.title, year=r.year or '', oa_type=r.oa_type or r.cr_type, kind=kind,
            journal=r.journal, issn_l=r.issn_l, source=r.source, source_type='journal', publisher='', language=r.language,
            container_title='', container_isbn='', container_editors='', volume_work='', volume_basis='', n_authors=len(auths),
            authorships=json.dumps([dict(pos=a['pos'], name=a['name'], oa_author=a['oa_author'], orcid=a['orcid'],
                                         raw_orcid=a['orcid'], institutions=a['institutions'], raw_aff=a['raw_aff'])
                                    for a in auths], ensure_ascii=False),
            twin_of='', twin_basis='', flags=';'.join(flags), volume=r.volume, issue=r.issue,
            pages='-'.join(x for x in (r.first_page, r.last_page) if x), reviewed_book=r.reviewed_book, jid=r.jid, scope=r.scope,
            author_source=r.author_source, alias_ids=r.alias_ids))
        stats[f'works|{bucket}|{kind}'] += 1
        if bucket == 'history':
            for a in auths:
                if not (a['name'] or '').strip():
                    continue
                pw.writerow(dict(role='reviewer' if kind == 'review' else 'author', source='journal-runs', work=wid,
                                 pos=a['pos'], n_auth=len(auths), name=a['name'], given=a.get('given', ''),
                                 family=a.get('family', ''), year=r.year or '', journal=r.journal, kind=kind,
                                 title=r.title[:200], orcid=a['orcid'], oa_author=a['oa_author'], rors=';'.join(a['rors']),
                                 insts=';'.join(a['institutions']), raw_aff=' | '.join(a['raw_aff'])))
                stats['positions'] += 1
                stats['positions_with_orcid'] += bool(a['orcid'])
                stats['positions_with_affiliation'] += bool(a['raw_aff'] or a['institutions'])
            if r.Index in ties:
                (bk, by, bl), rule = ties[r.Index]
                rb.append(dict(review=wid, book=bk, rule=rule, basis=f'journal-runs:{rule}', review_kind='review',
                               review_resolution='unkeyed', book_title=bl, book_year=by, book_lccn='', lc_main_lcnaf='',
                               book_families=''))
    # records the graph holds as a node that no one is credited on (an unkeyed cited article, a JSTOR record): their
    # printed authors as positions on that node, for the same linkers (the author-works `existing` idea)
    ex = db.execute(f"""SELECT r.*, m.node FROM '{OUT}/records.parquet' r JOIN matched m USING (rid)
                         WHERE r.scope <> 'adjacent' AND r.n_authors > 0 AND m.node NOT IN
                         (SELECT DISTINCT "to" FROM '{GRAPH}/authored.parquet') AND m.node NOT IN
                         (SELECT DISTINCT "to" FROM '{GRAPH}/edited.parquet')""").fetch_df()
    seen = set()
    for r in ex.itertuples():
        if r.node in seen:
            continue
        seen.add(r.node)
        auths = json.loads(r.authors)
        kind = {'editorial': 'other', 'front-matter': 'other'}.get(r.kind, r.kind)
        for a in auths:
            if (a['name'] or '').strip():
                pw.writerow(dict(role='reviewer' if kind == 'review' else 'author', source='journal-runs-existing', work=r.node,
                                 pos=a['pos'], n_auth=len(auths), name=a['name'], given=a.get('given', ''),
                                 family=a.get('family', ''), year=r.year or '', journal=r.journal, kind=kind,
                                 title=r.title[:200], orcid=a['orcid'], oa_author=a['oa_author'], rors=';'.join(a['rors']),
                                 insts=';'.join(a['institutions']), raw_aff=' | '.join(a['raw_aff'])))
                stats['positions_existing_nodes'] += 1
        stats['existing_nodes_uncredited'] += 1
    for f in list(files.values()) + [pf]:
        f.close()
    with gzip.open(LOAD / 'review-books.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=RB_COLS)
        w.writeheader()
        w.writerows(rb)
    stats['review_ties'] = len(rb)
    stats.update({f'review_ties_held|{k}': v for k, v in held.items()})
    stats['review_ties_by_rule'] = dict(Counter(x['rule'] for x in rb))
    (LOAD / 'report.json').write_text(json.dumps(dict(stats), indent=1, sort_keys=True) + '\n')
    log(f'load: {json.dumps(dict(stats))}')


# ------------------------------------------------------------------ payoff

def payoff(args):
    """Projection, not the linker: for each printed position of the load (data/graph/journal-runs/positions.csv.gz),
    the person keys whose label agrees with the printed name (link_work_people.agree_level, the linker's name test).
    exact   the printed ORCID is the key's ORCID;
    linked  one candidate, or several keys bearing the identical label (the linker's duplicate group), and the name
            agrees in full (a written given name);
    possible otherwise (several people, or initials only).
    The linker adds the date window, rarity and the second facts; this count ignores them, so `linked` is an upper bound
    for unique names and `possible` a lower bound for what a fact could still settle."""
    import duckdb
    import random
    from link_work_people import agree_level
    from link_cited_work_authors import forms
    db = duckdb.connect()
    people = db.execute(f"SELECT key, label, orcid FROM '{GRAPH}/person.parquet'").fetchall()
    fam = defaultdict(list)
    for k, lab, orc in people:
        for f, _, _ in forms(lab or ''):
            fam[f].append((k, lab, orc))
    # the sample: people credited with a Canadian History PhD thesis of the corpus
    ids = set()
    with open(ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv', newline='') as f:
        for r in csv.DictReader(f):
            if r['country'] == 'CA' and r['eligibility'] == 'history_phd':
                ids.add('diss-thesis:' + r['id'])
    import pyarrow as pa
    db.register('ids', pa.table({'a': sorted(ids)}))
    ca = [k for (k,) in db.execute(f"""SELECT DISTINCT a."from" FROM '{GRAPH}/authored.parquet' a WHERE a.evidence = 'keylog'
            AND a."to" IN (SELECT key FROM (SELECT key, unnest(anchors) x FROM '{GRAPH}/work.parquet') WHERE x IN (SELECT a FROM ids))
            ORDER BY 1""").fetchall()]
    random.seed(20261114)
    sample = random.sample(ca, 50)
    targets = list(dict.fromkeys(args.keys + sample))
    label = {k: lab for k, lab, _ in people}
    orcid = {k: o for k, _, o in people}
    before = dict(db.execute(f"""SELECT "from", count(DISTINCT "to") FROM '{GRAPH}/authored.parquet'
                                 WHERE "from" IN (SELECT unnest(?)) GROUP BY 1""", [targets]).fetchall())
    res = {k: Counter() for k in targets}
    works_of = {k: defaultdict(set) for k in targets}
    tset = set(targets)
    states = Counter()
    with gzip.open(LOAD / 'positions.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            cands = []
            for fm, _, _ in forms(r['name']):
                for k, lab, orc in fam.get(fm, ()):
                    lev = agree_level(r['name'], lab)
                    if lev:
                        cands.append((k, lab, orc, lev))
            if not cands:
                states['none'] += 1
                continue
            exact = [c for c in cands if r['orcid'] and c[2] == r['orcid']]
            labels = {c[1] for c in cands}
            if exact:
                st, who = 'exact', {exact[0][0]}
            elif len(labels) == 1 and all(c[3] == 'full' for c in cands):
                st, who = 'linked', {c[0] for c in cands}
            else:
                st, who = 'possible', {c[0] for c in cands}
            states[st] += 1
            for k in who & tset:
                res[k][st] += 1
                works_of[k][st].add((r['work'], r['kind'], r['year'], r['journal'], r['title'][:90]))
    rows = []
    for k in targets:
        wk = works_of[k]
        rows.append(dict(key=k, label=label.get(k), in_sample='named' if k in args.keys else 'random-CA-PhD',
                         works_before=before.get(k, 0), new_exact=len(wk['exact']), new_linked=len(wk['linked']),
                         new_reviews_attached=sum(1 for x in wk['exact'] | wk['linked'] if x[1] == 'review'),
                         new_possible=len(wk['possible'])))
    TRACK.mkdir(parents=True, exist_ok=True)
    with open(TRACK / 'payoff-sample.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for k in args.keys:
        print(k, label.get(k), json.dumps({s: sorted(v) for s, v in works_of[k].items()}, ensure_ascii=False, indent=0)[:6000])
    smp = [r for r in rows if r['in_sample'] != 'named']
    summ = dict(states=dict(states), sample=len(smp), sample_with_new=sum(1 for r in smp if r['new_exact'] + r['new_linked']),
                sample_new_works=sum(r['new_exact'] + r['new_linked'] for r in smp),
                sample_works_before=sum(r['works_before'] for r in smp),
                sample_possible=sum(r['new_possible'] for r in smp))
    (TRACK / 'payoff-report.json').write_text(json.dumps(summ, indent=1) + '\n')
    print(json.dumps(summ, indent=1))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('resolve')
    sub.add_parser('harvest')
    sub.add_parser('normalise')
    sub.add_parser('gap')
    sub.add_parser('load')
    x = sub.add_parser('payoff')
    x.add_argument('--keys', nargs='*', default=['p-123542', 'p-74171'])
    a = p.parse_args()
    {'resolve': resolve, 'harvest': harvest, 'normalise': normalise, 'gap': gap, 'load': load, 'payoff': payoff}[a.cmd](a)


if __name__ == '__main__':
    main()
