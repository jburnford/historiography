"""Journals and containers of keyed works from records already held (defect class 12, 2026-11-11).

Keyed article/other works lack a journal, chapters lack their volume, and many ORCID-only works are typed `other`
although the ORCID record names a type and a container. Every fact here comes from a record matched by an exact id:
- ORCID: the work's own `orcid-work:<orcid>:<put-code>` anchor -> that work summary in data/orcid-2026-09-21/records
  (type, journal-title = the container, year);
- OpenAlex: the work's `doi:` or `openalex:` anchor -> a held record (History harvest, DOI lookup, the 2026-11-11
  author-works fetch): type, primary source, ISSN-L;
- Crossref: `doi:` -> the Crossref metadata harvest of 2026-11-11 or a Crossref REST record fetched here (chapter
  DOIs only): type, container-title, ISSN, ISBN, editors;
- JSTOR: `doi:` -> the JSTOR records table (journal title, ISSNs, genre).
No title matching decides a work's record. Title matching is used only to find a chapter's volume among graph works
(normalised container title = volume title, years within one, kind book/other; one candidate, or one candidate with
EDITED credits or an LCCN; held when two or more remain).

    python3 scripts/export_work_containers.py targets     # the keyed works in scope (scratch)
    python3 scripts/export_work_containers.py extract     # OpenAlex + Crossref-meta + JSTOR records for them (scratch)
    python3 scripts/export_work_containers.py crossref [--max 100000]   # Crossref REST for chapter DOIs (build/)
    python3 scripts/export_work_containers.py export      # data/graph/work-journals.csv.gz, work-containers.csv.gz,
                                                          # author-works/volumes.csv.gz, work-containers-report.json

Outputs:
- data/graph/work-journals.csv.gz: work, journal, issn, source, basis, source_type, kind, proposed_kind
  (journal containers for keyed article/other works with no journal; proposed_kind 'article' where the source says
  article and the graph says other).
- data/graph/work-containers.csv.gz: work, kind, proposed_kind, container_title, container_isbn, container_doi,
  container_editors, container_year, container_publisher, source, basis, volume_work, volume_basis, volume_candidates.
  volume_work is a graph work key, or the id of an unkeyed volume in author-works/volumes.csv.gz.
- data/graph/author-works/volumes.csv.gz: id, title, year, isbn, doi, editors (as printed), publisher, source,
  chapters, keyed_contributors.
"""
import argparse, collections, csv, glob, gzip, hashlib, json, multiprocessing as mp, os, re, sqlite3, time
import urllib.parse, urllib.request
from pathlib import Path

csv.field_size_limit(1 << 30)
from author_works import SCRATCH as AW_SCRATCH, tkey, main_key, HARVEST, FETCH, duck
from graph_tables import keylog   # PART_OF has linked rows since 2026-11-11: the key log's only

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
S = AW_SCRATCH / 'containers'
ORCID_RECORDS = ROOT / 'data/orcid-2026-09-21/records'
CR_META = Path('/mnt/e/crossref-meta-2026-11-11/works')
JSTOR_RECORDS = '/mnt/e/JSTOR_history_citation_graph/records.sqlite'
CR_FETCH = ROOT / 'build/crossref-containers-2026-11-11'
OUT_J = ROOT / 'data/graph/work-journals.csv.gz'
OUT_C = ROOT / 'data/graph/work-containers.csv.gz'
OUT_V = ROOT / 'data/graph/author-works/volumes.csv.gz'
REPORT = ROOT / 'data/graph/work-containers-report.json'
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography; mailto:jic823@usask.ca)'
ARTICLE = {'journal-article', 'article'}
CHAPTER = {'book-chapter', 'chapter', 'reference-entry', 'encyclopedia-entry', 'book-part', 'book-section'}
ORCID_KIND = {'journal-article': 'article', 'book-chapter': 'chapter', 'encyclopedia-entry': 'chapter', 'book-review': 'review',
              'book': 'book', 'edited-book': 'book', 'dissertation-thesis': 'thesis', 'conference-paper': 'article',
              'report': 'other', 'working-paper': 'other', 'preprint': 'other'}


def norm_doi(d):
    return (d or '').strip().lower().replace('https://doi.org/', '').replace('http://dx.doi.org/', '')


# ---------------------------------------------------------------- targets

def targets(args):
    S.mkdir(parents=True, exist_ok=True)
    db = duck()
    W = AW_SCRATCH / 'work.parquet'
    db.execute(f"""COPY (SELECT w.key, w.kind, w.year, w.journal, w.label, w.anchors,
                    w.key IN (SELECT "from" FROM {keylog(G, 'part_of')}) has_part_of
                   FROM '{W}' w WHERE w.resolution <> 'unkeyed' AND w.kind IN ('article', 'other', 'chapter'))
                   TO '{S}/targets.parquet' (FORMAT parquet)""")
    db.execute(f"""COPY (SELECT DISTINCT key, lower(a) a FROM (SELECT key, unnest(anchors) a FROM '{S}/targets.parquet')
                   WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%' OR a LIKE 'orcid-work:%') TO '{S}/target-ids.parquet' (FORMAT parquet)""")
    print(db.execute(f"SELECT kind, count(*), count(journal), count(*) FILTER (WHERE has_part_of) FROM '{S}/targets.parquet' GROUP BY 1").fetchall())
    print(db.execute(f"SELECT split_part(a, ':', 1), count(*) FROM '{S}/target-ids.parquet' GROUP BY 1").fetchall())


# ---------------------------------------------------------------- extract

WANT_DOI = WANT_OA = None
ID_RE = re.compile(r'"id":\s*"https://openalex\.org/(W\d+)"')
DOI_RE = re.compile(r'"doi":\s*"https://doi\.org/([^"]+)"')


def _oa_one(job):
    path, dest = job
    import orjson
    rows = []
    with gzip.open(path, 'rb') as f:
        for line in f:
            s = line[:600].decode('utf-8', 'ignore')
            m = ID_RE.search(s)
            md = DOI_RE.search(s)
            oa = m.group(1) if m else ''
            doi = md.group(1).lower() if md else ''
            if not ((doi and doi in WANT_DOI) or (oa and oa.lower() in WANT_OA)):
                continue
            d = orjson.loads(line)
            loc = d.get('primary_location') or {}
            src = loc.get('source') or {}
            rows.append(dict(oa=oa, doi=norm_doi(d.get('doi')), type=d.get('type'), raw_type=loc.get('raw_type'),
                             raw_source=loc.get('raw_source_name'), source=src.get('display_name'), source_type=src.get('type'), issn_l=src.get('issn_l'),
                             issn=';'.join(src.get('issn') or []), publisher=src.get('host_organization_name'),
                             year=d.get('publication_year'), title=d.get('title')))
    with open(dest + '.tmp', 'w', encoding='utf-8') as o:
        for r in rows:
            o.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.rename(dest + '.tmp', dest)
    return path, len(rows)


def extract(args):
    global WANT_DOI, WANT_OA
    db = duck()
    ids = [a for (a,) in db.execute(f"SELECT DISTINCT a FROM '{S}/target-ids.parquet' WHERE a NOT LIKE 'orcid-work:%'").fetchall()]
    WANT_DOI = {a[4:] for a in ids if a.startswith('doi:')}
    WANT_OA = {a[9:] for a in ids if a.startswith('openalex:')}
    print(len(WANT_DOI), 'DOIs', len(WANT_OA), 'OpenAlex ids', flush=True)
    out = S / 'oa2'
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for d in HARVEST:
        files += sorted(d.glob('*.jsonl.gz'))
    files += sorted(FETCH.glob('batch-*.jsonl.gz'))
    jobs = [(str(p), str(out / (p.parent.name + '--' + p.name + '.jsonl'))) for p in files
            if not (out / (p.parent.name + '--' + p.name + '.jsonl')).exists()]
    print(len(jobs), 'OpenAlex files to read', flush=True)
    n = 0
    with mp.get_context('fork').Pool(args.workers) as pool:
        for i, (p, k) in enumerate(pool.imap_unordered(_oa_one, jobs)):
            n += k
            if i % 100 == 0:
                print(i, n, flush=True)
    print('OpenAlex rows', n, flush=True)
    # Crossref metadata harvest
    import orjson
    with open(S / 'crossref-meta.jsonl', 'w', encoding='utf-8') as o:
        k = 0
        for p in sorted(CR_META.glob('*.jsonl.gz')):
            with gzip.open(p, 'rb') as f:
                for line in f:
                    md = re.search(rb'"DOI":\s*"([^"]+)"', line)
                    if not md or md.group(1).decode('utf-8', 'ignore').lower() not in WANT_DOI:
                        continue
                    o.write(json.dumps(cr_row(orjson.loads(line)), ensure_ascii=False) + '\n'); k += 1
    print('Crossref meta rows', k, flush=True)
    c = sqlite3.connect(f'file:{JSTOR_RECORDS}?mode=ro', uri=True)
    with open(S / 'jstor.jsonl', 'w', encoding='utf-8') as o:
        k = 0
        for iid, doi, genre, journal, issns in c.execute("SELECT item_id, doi, genre, journal_title, issns FROM records WHERE doi IS NOT NULL"):
            d = norm_doi(doi)
            if d in WANT_DOI:
                o.write(json.dumps(dict(doi=d, iid=iid, genre=genre, journal=journal, issns=issns), ensure_ascii=False) + '\n'); k += 1
    print('JSTOR rows', k, flush=True)


def cr_row(it):
    def yr(it):
        for k in ('issued', 'published-print', 'published-online', 'created'):
            try:
                return int(it[k]['date-parts'][0][0])
            except Exception:
                pass
    ed = [' '.join(x for x in (e.get('given'), e.get('family')) if x) or e.get('name') or '' for e in it.get('editor') or []]
    au = [dict(name=' '.join(x for x in (a.get('given'), a.get('family')) if x) or a.get('name') or '',
               orcid=(a.get('ORCID') or '').rsplit('/', 1)[-1] or None) for a in it.get('author') or []]
    return dict(doi=norm_doi(it.get('DOI')), type=it.get('type'), title=(it.get('title') or [''])[0],
                container=(it.get('container-title') or [None])[0], issn=';'.join(it.get('ISSN') or []),
                isbn=';'.join(it.get('ISBN') or []), editors=ed, authors=au, publisher=it.get('publisher'), year=yr(it))


# ---------------------------------------------------------------- Crossref REST for chapter DOIs

def crossref(args):
    """chapter DOIs (graph kind chapter, or a held record typed book-chapter) of keyed works with no PART_OF and no
    held Crossref record: one GET per DOI, ≤5 per second, raw records under build/"""
    # one chapter DOI per volume that the graph lacks or holds ambiguously (editors and ISBN for the volume record),
    # volumes with the most chapters first; work-containers.csv.gz must exist (run export once before)
    crm = {r['doi'] for r in jl(S / 'crossref-meta.jsonl')}
    db = duck()
    doi_of = collections.defaultdict(list)
    for k, a in db.execute(f"SELECT key, a FROM '{S}/target-ids.parquet' WHERE a LIKE 'doi:%'").fetchall():
        doi_of[k].append(a[4:])
    per_vol = collections.defaultdict(list)
    with gzip.open(OUT_C, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['volume_basis'] == 'new-unkeyed-volume' or r['volume_basis'].endswith(':held'):
                vid = r['volume_work'] or ('held:' + tkey(r['container_title']) + '|' + r['container_year'])
                per_vol[vid] += [d for d in doi_of.get(r['work'], []) if d not in crm]
    aw = ROOT / 'data/graph/author-works/works.csv.gz'
    if aw.exists():
        with gzip.open(aw, 'rt', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['kind'] == 'chapter' and r['doi'] and r.get('volume_basis', 'new-unkeyed-volume') in ('new-unkeyed-volume', '') and r['doi'] not in crm:
                    per_vol[r.get('volume_work') or r['doi']].append(r['doi'])
    want = [sorted(v)[0] for _, v in sorted(per_vol.items(), key=lambda kv: -len(kv[1])) if v]
    print(len(per_vol), 'volumes;', len(want), 'with a chapter DOI to ask', flush=True)
    CR_FETCH.mkdir(parents=True, exist_ok=True)
    done = set()
    for p in CR_FETCH.glob('part-*.jsonl'):
        for r in jl(p):
            done.add(r['_doi'])
    todo = [d for d in want if d not in done]
    print(len(want), 'chapter DOIs;', len(todo), 'to fetch', flush=True)
    if len(todo) > args.max:
        print('STOP: more than the cap', args.max); todo = todo[:args.max]
    part = CR_FETCH / f'part-{len(list(CR_FETCH.glob("part-*.jsonl"))):03d}.jsonl'
    last = 0.0
    n = 0
    with open(part, 'a', encoding='utf-8') as o:
        for d in todo:
            url = 'https://api.crossref.org/works/' + urllib.parse.quote(d, safe='/') + '?mailto=jic823@usask.ca'
            rec = None
            for i in range(5):
                wait = 0.22 - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.time()
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                        rec = json.load(r).get('message')
                    break
                except Exception as e:
                    code = getattr(e, 'code', None)
                    if code == 404:
                        rec = {'_missing': True}
                        break
                    time.sleep(min(60, 2 * 2 ** i))
            n += 1
            if rec is not None:
                rec['_doi'] = d
                o.write(json.dumps(rec, ensure_ascii=False) + '\n')
            if n % 500 == 0:
                o.flush(); print(n, flush=True)
    print('fetched', n)


# ---------------------------------------------------------------- export

def jl(p):
    if not Path(p).exists():
        return
    with open(p, encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def load_oa():
    out = {}
    for p in sorted((S / 'oa2').glob('*.jsonl')):
        for r in jl(p):
            if r['doi']:
                out.setdefault(('doi', r['doi']), r)
            out.setdefault(('oa', r['oa'].lower()), r)
    return out


def book_doi_candidates(d):
    """the book DOI a chapter DOI implies, by publisher pattern (JSTOR, De Gruyter, Oxford Handbooks, generic suffixes)"""
    out = []
    m = re.match(r'^(10\.2307/j\.ctv?[0-9a-z]+)\.\d+$', d)
    if m:
        out.append(m.group(1))
    m = re.match(r'^(10\.1515/\d{9,13}[\dx]?)-\w+$', d)
    if m:
        out.append(m.group(1))
    m = re.match(r'^(10\.1093/(?:oxfordhb|acprof|oso|acrefore|med)/\d{13})\.\d{3}\.\d+$', d)
    if m:
        out.append(m.group(1) + '.001.0001')
    m = re.match(r'^(10\.1007/978-[\d-]+)_\d+$', d)
    if m:
        out.append(m.group(1))
    m = re.match(r'^(10\.4324/\d{13})-\d+$', d)
    if m:
        out.append(m.group(1))
    m = re.match(r'^(10\.1017/\d{13})\.\d+$', d)
    if m:
        out.append(m.group(1))
    return out


def strip_label(lab):
    return re.split(r'\s+/\s+', lab or '', maxsplit=1)[0]


def export(args):
    db = duck()
    # ---- sources
    oa = load_oa()
    cr = {}
    for r in jl(S / 'crossref-meta.jsonl'):
        cr[r['doi']] = dict(r, src='crossref-meta')
    for p in sorted(CR_FETCH.glob('part-*.jsonl')):
        for it in jl(p):
            if it.get('_missing'):
                continue
            r = cr_row(it)
            r['doi'] = it['_doi']
            cr.setdefault(r['doi'], dict(r, src='crossref-api'))
    js = {r['doi']: r for r in jl(S / 'jstor.jsonl')}
    print('held: OpenAlex', len(oa), 'Crossref', len(cr), 'JSTOR', len(js), flush=True)
    tg = {k: dict(kind=kind, year=y, journal=j, label=lab, has_po=po, ids=[])
          for k, kind, y, j, lab, po in db.execute(f"SELECT key, kind, year, journal, label, has_part_of FROM '{S}/targets.parquet'").fetchall()}
    for k, a in db.execute(f"SELECT key, a FROM '{S}/target-ids.parquet'").fetchall():
        tg[k]['ids'].append(a)
    # ORCID summaries for orcid-work anchors
    need = collections.defaultdict(set)
    for k, t in tg.items():
        for a in t['ids']:
            if a.startswith('orcid-work:'):
                _, o, pc = a.split(':', 2)
                need[o.upper()].add(pc)
    osum = {}
    for o, pcs in need.items():
        p = ORCID_RECORDS / f'{o}.json'
        if not p.exists():
            continue
        groups = ((json.loads(p.read_text()).get('activities-summary') or {}).get('works') or {}).get('group') or []
        for g in groups:
            for s in g.get('work-summary') or []:
                pc = str(s.get('put-code'))
                if pc in pcs:
                    y = (((s.get('publication-date') or {}).get('year')) or {}).get('value')
                    osum[f'orcid-work:{o.lower()}:{pc}'] = dict(type=s.get('type'), container=(s.get('journal-title') or {}).get('value'),
                                                                 year=int(y) if (y or '').isdigit() else None)
    print('ORCID summaries', len(osum), 'of', sum(len(v) for v in need.values()), flush=True)
    # ---- graph volume index
    vol_full = collections.defaultdict(list)
    vol_main = collections.defaultdict(list)
    edited = {w for (w,) in db.execute(f"SELECT DISTINCT \"to\" FROM '{G}/edited.parquet'").fetchall()}
    gid = {}
    for i, k in db.execute(f"SELECT id, key FROM '{AW_SCRATCH}/ids.parquet' WHERE resolution NOT IN ('unkeyed-table')").fetchall():
        gid.setdefault(i, k)
    isbn_key = {}
    q = db.execute(f"""SELECT key, kind, year, label, anchors, resolution FROM '{AW_SCRATCH}/work.parquet'
                       WHERE kind IN ('book', 'other') AND label NOT ILIKE 'review of%'""")
    while True:
        rows = q.fetchmany(200000)
        if not rows:
            break
        for k, kind, y, lab, anchors, res in rows:
            lab = strip_label(lab)
            has_lccn = any(a.startswith('lccn:') for a in anchors)
            info = (k, y, kind, k in edited, has_lccn)
            fk = tkey(lab)
            if len(fk) >= 6:
                vol_full[fk].append(info)
            mk = main_key(lab)
            if len(mk) >= 12:
                vol_main[mk].append(info)
            for a in anchors:
                if a.startswith('isbn:'):
                    isbn_key.setdefault(re.sub(r'[^0-9x]', '', a[5:].lower()), k)
    print('volume index', len(vol_full), flush=True)

    def find_volume(title, year, self_key):
        if not title:
            return None, 'no-container', 0
        for basis, cands in (('title', vol_full.get(tkey(strip_label(title)), [])),
                             ('main-title', vol_main.get(main_key(title), []) if len(main_key(title)) >= 12 else [])):
            c = [x for x in cands if x[0] != self_key and (year is None or x[1] is None or abs(x[1] - year) <= 1)]
            c = list({x[0]: x for x in c}.values())
            if len(c) == 1:
                return c[0][0], basis, 1
            if len(c) > 1:
                pref = [x for x in c if x[3] or x[4]]
                if len(pref) == 1:
                    return pref[0][0], basis + ':edited-or-lccn', len(c)
                return None, basis + ':held', len(c)
        return None, 'not-in-graph', 0

    # ---- per work
    J, C = [], []
    vols = {}
    stats = collections.Counter()
    orcid_only = collections.Counter()
    for k, t in tg.items():
        dois = [a[4:] for a in t['ids'] if a.startswith('doi:')]
        oas = [a[9:] for a in t['ids'] if a.startswith('openalex:')]
        ows = [a for a in t['ids'] if a.startswith('orcid-work:')]
        rec_oa = next((oa[('doi', d)] for d in dois if ('doi', d) in oa), None) or next((oa[('oa', x)] for x in oas if ('oa', x) in oa), None)
        rec_cr = next((cr[d] for d in dois if d in cr), None)
        rec_js = next((js[d] for d in dois if d in js), None)
        rec_or = next((osum[a] for a in ows if a in osum), None)
        if ows and not dois and not oas:
            orcid_only[(rec_or or {}).get('type') or 'no-summary'] += 1
        # source type -> chapter / article
        types = []
        if rec_cr: types.append(('crossref', rec_cr['type']))
        if rec_oa: types.append(('openalex', rec_oa['type']))
        if rec_js: types.append(('jstor', rec_js['genre']))
        if rec_or: types.append(('orcid', rec_or['type']))
        is_ch = next(((s, ty) for s, ty in types if ty in CHAPTER), None)
        is_art = next(((s, ty) for s, ty in types if ty in ARTICLE or (s == 'jstor' and ty == 'article')), None)
        first = types[0] if types else None
        chapter = t['kind'] == 'chapter' or (first and first[1] in CHAPTER) or (not first and False)
        # journal container
        if not chapter and t['kind'] in ('article', 'other'):
            jn = issn = src = basis = stype = None
            if rec_oa and rec_oa['source'] and (rec_oa['source_type'] in ('journal', 'conference') or
                                                (rec_oa['source_type'] == 'book series' and rec_oa['type'] == 'article')):
                jn, issn, src, basis, stype = rec_oa['source'], rec_oa['issn_l'], 'openalex', 'doi' if dois else 'openalex-id', rec_oa['source_type']
            elif rec_cr and rec_cr['container'] and rec_cr['type'] in ('journal-article', 'proceedings-article'):
                jn, issn, src, basis, stype = rec_cr['container'], (rec_cr['issn'] or '').split(';')[0] or None, rec_cr['src'], 'doi', 'journal'
            elif rec_js and rec_js['journal']:
                jn, issn, src, basis, stype = rec_js['journal'], (rec_js['issns'] or '').split(';')[0].strip() or None, 'jstor', 'doi', 'journal'
            elif rec_or and rec_or['container'] and rec_or['type'] in ('journal-article', 'book-review', 'conference-paper'):
                v, vb, nc = find_volume(rec_or['container'], rec_or['year'] or t['year'], k)
                if v and rec_or['type'] == 'journal-article':
                    chapter = True          # ORCID calls it an article but its container is a volume in the graph
                    stats['orcid_article_container_is_volume'] += 1
                else:
                    jn, src, basis, stype = rec_or['container'], 'orcid', 'orcid-work', 'journal-title'
            if not chapter and jn:
                pk = ''
                if t['kind'] == 'other' and is_art:
                    pk = 'article'
                elif t['kind'] == 'other' and rec_or and rec_or['type'] == 'book-review':
                    pk = 'review'
                if t['journal'] is None:
                    J.append(dict(work=k, journal=jn, issn=issn or '', source=src, basis=basis, source_type=stype or '',
                                  kind=t['kind'], proposed_kind=pk))
                    stats[f'journal_from:{src}'] += 1
            elif not chapter and t['kind'] == 'other' and is_art and t['journal'] is None:
                stats['article_type_no_container'] += 1
        if chapter and not t['has_po']:
            title = isbn = cdoi = year = pub = src = basis = None
            editors = []
            if rec_cr and rec_cr['container'] and rec_cr['type'] in CHAPTER | {'book-chapter'}:
                title, isbn, editors, year, pub, src, basis = rec_cr['container'], rec_cr['isbn'], rec_cr['editors'], rec_cr['year'], rec_cr['publisher'], rec_cr['src'], 'doi'
            elif rec_oa and rec_oa['type'] in ('book-chapter', 'reference-entry') and (rec_oa.get('raw_source') or (
                    rec_oa['source'] and rec_oa['source_type'] not in ('repository', 'journal', 'ebook platform', 'book series'))):
                # the record's raw_source_name is the volume ('Moving Natures'); the source is often a platform
                # ('University of Calgary Press eBooks') or a series
                title = rec_oa.get('raw_source') or rec_oa['source']
                year, pub, src, basis = rec_oa['year'], rec_oa['publisher'], 'openalex', 'doi' if dois else 'openalex-id'
            elif rec_or and rec_or['container']:
                title, year, src, basis = rec_or['container'], rec_or['year'], 'orcid', 'orcid-work'
            year = year or t['year']
            # volume: by implied book DOI, ISBN, then title
            vw = vb = None
            nc = 0
            for d in dois:
                for bd in book_doi_candidates(d):
                    cdoi = cdoi or bd
                    if 'doi:' + bd in gid and gid['doi:' + bd] != k:
                        vw, vb = gid['doi:' + bd], 'book-doi'
                        break
                if vw:
                    break
            if not vw and isbn:
                for x in isbn.split(';'):
                    x = re.sub(r'[^0-9x]', '', x.lower())
                    if x in isbn_key:
                        vw, vb = isbn_key[x], 'isbn'
                        break
            if not vw:
                vw, vb, nc = find_volume(title, year, k)
            if not vw and title and not (vb or '').endswith(':held'):
                vid = ('doi:' + cdoi) if cdoi else \
                    'volume:' + hashlib.sha1(f'{tkey(title)}|{year or ""}'.encode()).hexdigest()[:12]
                v = vols.setdefault(vid, dict(id=vid, title=title, year=year, isbn=isbn or '', doi=cdoi or '', editors=editors,
                                              publisher=pub or '', source=src, chapters=set()))
                v['chapters'].add(k)
                if editors and not v['editors']:
                    v['editors'] = editors
                if isbn and not v['isbn']:
                    v['isbn'] = isbn
                vw, vb = vid, 'new-unkeyed-volume'
            pk = 'chapter' if t['kind'] != 'chapter' else ''
            C.append(dict(work=k, kind=t['kind'], proposed_kind=pk, container_title=title or '', container_isbn=isbn or '',
                          container_doi=cdoi or '', container_editors='; '.join(editors), container_year=year or '',
                          container_publisher=pub or '', source=src or '', basis=basis or '', volume_work=vw or '',
                          volume_basis=vb or '', volume_candidates=nc))
            stats[f'chapter:{vb}'] += 1
    # chapters in author-works (unkeyed): the same volume step; columns added to that table
    AW = ROOT / 'data/graph/author-works/works.csv.gz'
    aw_stats = collections.Counter()
    if AW.exists():
        with gzip.open(AW, 'rt', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            acols = [c for c in rd.fieldnames if c not in ('container_isbn', 'container_editors', 'volume_work', 'volume_basis')]
            arows = list(rd)
        for r in arows:
            r['container_isbn'] = r['container_editors'] = r['volume_work'] = r['volume_basis'] = ''
            if r['kind'] != 'chapter':
                continue
            d = r['doi']
            rc = cr.get(d) if d else None
            title = (rc or {}).get('container') or r['container_title']
            isbn = (rc or {}).get('isbn') or ''
            editors = (rc or {}).get('editors') or []
            year = int(r['year']) if r['year'] else None
            r['container_title'], r['container_isbn'], r['container_editors'] = title or '', isbn, '; '.join(editors)
            vw = vb = cdoi = None
            for bd in book_doi_candidates(d or ''):
                cdoi = cdoi or bd
                if 'doi:' + bd in gid:
                    vw, vb = gid['doi:' + bd], 'book-doi'
                    break
            if not vw and isbn:
                for x in isbn.split(';'):
                    x = re.sub(r'[^0-9x]', '', x.lower())
                    if x in isbn_key:
                        vw, vb = isbn_key[x], 'isbn'
                        break
            if not vw:
                vw, vb, _ = find_volume(title, year, None)
            if not vw and title and not (vb or '').endswith(':held'):
                vid = ('doi:' + cdoi) if cdoi else \
                    'volume:' + hashlib.sha1(f'{tkey(title)}|{year or ""}'.encode()).hexdigest()[:12]
                v = vols.setdefault(vid, dict(id=vid, title=title, year=year, isbn=isbn, doi=cdoi or '', editors=editors,
                                              publisher=r['publisher'] or '', source='author-works', chapters=set()))
                v['chapters'].add(r['id'])
                if editors and not v['editors']:
                    v['editors'] = editors
                if isbn and not v['isbn']:
                    v['isbn'] = isbn
                vw, vb = vid, 'new-unkeyed-volume'
            r['volume_work'], r['volume_basis'] = vw or '', vb or ''
            aw_stats[vb or 'none'] += 1
        cols = acols[:acols.index('container_title') + 1] + ['container_isbn', 'container_editors', 'volume_work', 'volume_basis'] + \
            acols[acols.index('container_title') + 1:]
        with gzip.open(AW, 'wt', newline='', encoding='utf-8', compresslevel=9) as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(arows)
    stats.update({f'author_works_chapter:{k}': v for k, v in aw_stats.items()})
    # keyed contributors per new volume
    cred = collections.defaultdict(set)
    for p_, w in db.execute(f"SELECT DISTINCT k, w FROM '{AW_SCRATCH}/credits.parquet' WHERE ev <> 'edited'").fetchall():
        cred[w].add(p_)
    for v in vols.values():
        v['keyed_contributors'] = len(set().union(*[cred.get(c, set()) for c in v['chapters']]))
        v['chapters_n'] = len(v['chapters'])

    def write(path, rows, cols):
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wt', newline='', encoding='utf-8', compresslevel=9) as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            for r in sorted(rows, key=lambda r: r[cols[0]]):
                w.writerow(r)
    write(OUT_J, J, ['work', 'journal', 'issn', 'source', 'basis', 'source_type', 'kind', 'proposed_kind'])
    write(OUT_C, C, ['work', 'kind', 'proposed_kind', 'container_title', 'container_isbn', 'container_doi', 'container_editors',
                     'container_year', 'container_publisher', 'source', 'basis', 'volume_work', 'volume_basis', 'volume_candidates'])
    vrows = [dict(v, editors='; '.join(v['editors']), chapters=v['chapters_n']) for v in vols.values()]
    write(OUT_V, vrows, ['id', 'title', 'year', 'isbn', 'doi', 'editors', 'publisher', 'source', 'chapters', 'keyed_contributors'])
    # coverage
    nojournal = sum(1 for t in tg.values() if t['kind'] in ('article', 'other') and t['journal'] is None)
    filled = {r['work'] for r in J}
    chap_rows = [r for r in C]
    vol_in_graph = [r for r in C if r['volume_work'] and r['volume_basis'] != 'new-unkeyed-volume']
    rep = dict(
        date='2026-11-11',
        keyed_article_other_without_journal=nojournal, journal_filled=len(filled),
        still_without_journal=nojournal - len(filled) - sum(1 for r in C if r['kind'] in ('article', 'other') and r['proposed_kind'] == 'chapter'),
        journal_rows_by_source=dict(collections.Counter(r['source'] for r in J)),
        proposed_kind=dict(collections.Counter((r['kind'], r['proposed_kind']) for r in J + C if r['proposed_kind']).most_common()) if False else
            {f"{a}->{b}": n for (a, b), n in collections.Counter((r['kind'], r['proposed_kind']) for r in J + C if r['proposed_kind']).most_common()},
        orcid_only_works_by_orcid_type=dict(orcid_only.most_common()),
        chapters_without_part_of=len(chap_rows),
        chapters_with_container_title=sum(1 for r in C if r['container_title']),
        chapters_by_volume_basis=dict(collections.Counter(r['volume_basis'] for r in C).most_common()),
        chapters_by_source=dict(collections.Counter(r['source'] for r in C).most_common()),
        chapters_linkable_to_graph_volume=len(vol_in_graph),
        graph_volumes_linked=len({r['volume_work'] for r in vol_in_graph}),
        graph_volumes_linked_with_keyed_editor=len({r['volume_work'] for r in vol_in_graph} & edited),
        new_unkeyed_volumes=len(vols), new_volumes_with_editors=sum(1 for v in vols.values() if v['editors']),
        top_new_volumes=[dict(id=v['id'], title=v['title'], year=v['year'], chapters=v['chapters_n'], keyed=v['keyed_contributors'])
                         for v in sorted(vols.values(), key=lambda v: (-v['keyed_contributors'], -v['chapters_n']))[:25]],
        stats=dict(stats))
    REPORT.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'top_new_volumes'}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('targets')
    e = sp.add_parser('extract'); e.add_argument('--workers', type=int, default=3)
    c = sp.add_parser('crossref'); c.add_argument('--max', type=int, default=100000)
    sp.add_parser('export')
    a = ap.parse_args()
    S.mkdir(parents=True, exist_ok=True)
    dict(targets=targets, extract=extract, crossref=crossref, export=export)[a.cmd](a)


if __name__ == '__main__':
    main()
