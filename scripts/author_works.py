"""A historian's works absent from the graph (defect class 8, 2026-11-11) -> data/graph/author-works/.

The OpenAlex History/HPS harvest (scripts/openalex_history_harvest.py) is topic-scoped, so a historian's article in
Nature, a public-health paper with a co-author, or a Zenodo dataset never came in. Identity is by exact identifier
only: a work is credited to a person key when an authorship on its OpenAlex record carries an ORCID that is an
`orcid:` anchor of exactly that key (the ORCID printed in the publisher's record, `raw_orcid`, or the ORCID of the
OpenAlex author entity: an OpenAlex author id proven by ORCID). No name-only attribution: the printed name is only a
guard (a non-printed ORCID whose name disagrees with the key's family name is held, not credited).

Two-layer rule: nothing is minted; the works are a tracked table and become unkeyed Work nodes in the build.
Dead-end rule: works by a historian are in scope whatever the venue; what they cite is not pulled in, and co-authors'
other works are not pulled in (the fetch is by the historians' own ORCIDs; co-authors are kept as printed).

    python3 scripts/author_works.py people              # historian keys with an ORCID (person_roles: historian, strong/supported)
    python3 scripts/author_works.py fetch [--max 150000] # OpenAlex works by those ORCIDs -> build/openalex-author-works-2026-11-11/
    python3 scripts/author_works.py snapshot            # what the graph holds (DOIs, OpenAlex ids, credited titles) -> scratch
    python3 scripts/author_works.py scan                # every held OpenAlex record (harvest, DOI lookup, fetch) with a keyed ORCID
    python3 scripts/author_works.py export              # -> data/graph/author-works/{works,authors,existing}.csv.gz + report.json
    python3 scripts/author_works.py panel               # probe p-24137 + 20 random strong historians with an ORCID

Outputs (data/graph/author-works/):
- works.csv.gz: id (doi:<doi>, else openalex:W..), openalex, doi, title, year, oa_type, kind (article/book/chapter/
  review/dataset/preprint/other), journal, issn_l, publisher, language, authorships (JSON list as printed: pos, name,
  OpenAlex author id, ORCID, institutions with ROR), twin_of, twin_basis, flags.
- authors.csv.gz: work, position, person_key, basis (raw-orcid / openalex-author-orcid), state (credited / held),
  name, orcid, oa_author, name_check.
- existing.csv.gz: the same credits on works the graph already holds as unkeyed nodes (doi: ids from the Crossref,
  cited-works or JSTOR-cited tables) where the key is not credited.
"""
import argparse, collections, csv, glob, gzip, io, json, multiprocessing as mp, os, random, re, sqlite3, sys, time
import unicodedata, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
SQLITE = ROOT / 'build/keylog-state.sqlite'
ROLES = ROOT / 'data/person-facts/person-roles.csv.gz'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
OUT = ROOT / 'data/graph/author-works'
FETCH = ROOT / 'build/openalex-author-works-2026-11-11'
SCRATCH = Path(os.environ.get('AW_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/authorworks'))
HARVEST = [Path('/mnt/e/openalex-history-2026-11-08/history'), Path('/mnt/e/openalex-history-2026-11-08/dissertations'),
           Path('/mnt/e/openalex-people-2026-11-09/doi-lookup')]
KEYFILE = Path(os.path.expanduser('~/.config/openalex/key'))
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography; mailto:jic823@usask.ca)'
SELECT = ('id,doi,title,display_name,publication_year,publication_date,type,language,authorships,primary_location,'
          'locations,ids,biblio,primary_topic,referenced_works_count,cited_by_count,is_retracted')
ORCID_RE = re.compile(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])')
KIND = {'article': 'article', 'review': 'article', 'letter': 'article', 'editorial': 'article', 'erratum': 'other',
        'book-review': 'review', 'book': 'book', 'book-chapter': 'chapter', 'reference-entry': 'chapter',
        'dataset': 'dataset', 'preprint': 'preprint', 'dissertation': 'thesis'}
SKIP_TYPES = {'paratext', 'retraction', 'supplementary-materials', 'peer-review', 'erratum'}
PREPRINT_DOI = re.compile(r'^10\.(31235|1101|2139|21203|20944|48550|31219|31234|31237|35542|36227|22541|32942|26434|'
                          r'1590/scielopreprints|2196/preprints|33774|5194/egusphere|7287/peerj\.preprints)')
ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'los', 'las', 'il', 'lo', 'o', 'os', 'as'}


def duck():
    import duckdb
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET enable_progress_bar=false; SET temp_directory='{SCRATCH}/duck'")
    return db


def tkey(t):
    """full normalised title: unlike key_lc_works.title_key, dashes and slashes separate words ('1914–1918' stays two
    numbers) and there is no 10-word cut; HTML tags dropped"""
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = re.sub(r"['’‘ʼ`]", '', t)
    t = re.sub(r'\s*&\s*', ' and ', t)
    t = re.sub(r'[‐-―−/]', ' ', t)
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    w = re.sub(r'[^a-z0-9 ]+', ' ', t).split()
    while w and w[0] in ARTICLES:
        w = w[1:]
    return ' '.join(w)


def main_key(t):
    """main title (before ':' / '.' / '?'), normalised: for twins whose subtitle changed"""
    t = re.sub(r'<[^>]+>', ' ', t or '')
    return tkey(re.split(r'[:.?!]\s', t + ' ', maxsplit=1)[0])


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def family(label):
    """family name(s) of a key label ('Smith, John, 1950-' or 'John Smith')"""
    lab = re.sub(r',?\s*\d{3,4}\s*-\s*(\d{3,4})?\.?$', '', label or '').strip()
    if ',' in lab:
        fam = lab.split(',')[0]
    else:
        ws = lab.split()
        fam = ws[-1] if ws else ''
    return [w for w in re.sub(r'[^a-z ]+', ' ', fold(fam)).split() if len(w) > 1]


def name_check(label, printed):
    fam = family(label)
    toks = set(re.sub(r'[^a-z ]+', ' ', fold(' '.join(printed))).split())
    if not fam:
        return 'unknown'
    if all(f in toks for f in fam):
        return 'family'
    if any(f in toks for f in fam):
        return 'part'
    return 'differs'


# ---------------------------------------------------------------- people

def resolver(c):
    rep = dict(c.execute("SELECT key, replaced_by FROM keys WHERE type = 'person' AND status = 'merged'").fetchall())

    def res(k):
        seen = 0
        while k in rep and rep[k] and seen < 20:
            k = rep[k]; seen += 1
        return k
    return res


def keyed_orcids():
    """orcid -> person key, from the key log's live orcid: anchors"""
    c = sqlite3.connect(f'file:{SQLITE}?mode=ro', uri=True)
    live = {k for (k,) in c.execute("SELECT key FROM keys WHERE type = 'person' AND status IN ('active', 'provisional')")}
    out = {}
    for a, k in c.execute("SELECT anchor, key FROM anchor WHERE anchor LIKE 'orcid:%'"):
        if k in live:
            out[a[6:].upper()] = k
    return out, c


def historian_orcids():
    orcid_key, c = keyed_orcids()
    res = resolver(c)
    keys = set()
    n_roles = collections.Counter()
    with gzip.open(ROLES, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['role'] == 'historian' and r['confidence'] in ('strong', 'supported'):
                keys.add(res(r['key']))
                n_roles[r['confidence']] += 1
    by_key = collections.defaultdict(list)
    for o, k in orcid_key.items():
        if k in keys:
            by_key[k].append(o)
    return keys, by_key, n_roles


def people(args):
    keys, by_key, n_roles = historian_orcids()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    d = dict(role_rows=n_roles, historian_keys=len(keys), with_orcid=len(by_key),
             orcids=sum(len(v) for v in by_key.values()))
    (SCRATCH / 'people.json').write_text(json.dumps(d, indent=1))
    print(d)


# ---------------------------------------------------------------- fetch

def fetch(args):
    keys, by_key, _ = historian_orcids()
    orcids = sorted({o for v in by_key.values() for o in v})
    FETCH.mkdir(parents=True, exist_ok=True)
    key = KEYFILE.read_text().strip() if KEYFILE.exists() else None
    batches = [orcids[i:i + args.batch] for i in range(0, len(orcids), args.batch)]
    log = open(FETCH / 'fetch.log', 'a')
    calls = int((FETCH / 'calls.txt').read_text()) if (FETCH / 'calls.txt').exists() else 0
    print(len(orcids), 'ORCIDs in', len(batches), 'batches; calls so far', calls, flush=True)
    last = 0.0
    for bi, b in enumerate(batches):
        dest = FETCH / f'batch-{bi:04d}.jsonl.gz'
        if dest.exists():
            continue
        tmp = dest.with_suffix('.tmp')
        cursor, n, pages = '*', 0, 0
        with gzip.open(tmp, 'wt', encoding='utf-8') as o:
            while cursor:
                if calls >= args.max:
                    print('STOP: request cap reached', calls, flush=True)
                    log.write(f'stop at cap {calls}\n'); return
                q = dict(filter='author.orcid:' + '|'.join(b), per_page=200, cursor=cursor, select=SELECT,
                         mailto='jic823@usask.ca')
                if key:
                    q['api_key'] = key
                url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(q)
                for i in range(8):
                    wait = 0.21 - (time.time() - last)
                    if wait > 0:
                        time.sleep(wait)
                    last = time.time()
                    try:
                        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
                            d = json.load(r)
                        calls += 1
                        break
                    except Exception as e:
                        calls += 1
                        code = getattr(e, 'code', None)
                        if code in (400, 401, 403):
                            raise RuntimeError(f'OpenAlex refused (HTTP {code})')
                        time.sleep(min(120, 2 * 2 ** i))
                else:
                    raise RuntimeError('gave up after retries')
                for w in d['results']:
                    o.write(json.dumps(w, ensure_ascii=False) + '\n')
                    n += 1
                pages += 1
                cursor = d['meta'].get('next_cursor') if d['results'] else None
        tmp.rename(dest)
        (FETCH / 'calls.txt').write_text(str(calls))
        log.write(f'batch {bi} orcids {len(b)} works {n} pages {pages} calls {calls}\n'); log.flush()
        if bi % 10 == 0:
            print(f'batch {bi}/{len(batches)} works {n} calls {calls}', flush=True)
    (FETCH / 'calls.txt').write_text(str(calls))
    print('done; calls', calls, flush=True)


# ---------------------------------------------------------------- snapshot of the graph

def snapshot(args):
    """the graph's DOIs, OpenAlex ids and credited titles, copied to scratch (build/graph may be rebuilt meanwhile)"""
    db = duck()
    S = SCRATCH
    import pyarrow.parquet as pq
    cols = pq.read_schema(G / 'authored.parquet').names
    db.execute(f"""COPY (SELECT key, resolution, kind, year, label, journal, anchors FROM '{G}/work.parquet')
                   TO '{S}/work.parquet' (FORMAT parquet)""")
    parts = [f"""SELECT "from" k, "to" w, {"evidence" if 'evidence' in cols else "'keylog'"} ev FROM '{G}/authored.parquet'"""]
    if (G / 'linked_authored.parquet').exists() and 'evidence' not in cols:
        parts.append(f"""SELECT "from", "to", 'linked' FROM '{G}/linked_authored.parquet'""")
    parts.append(f"""SELECT "from", "to", 'edited' FROM '{G}/edited.parquet'""")
    db.execute(f"COPY ({' UNION ALL '.join(parts)}) TO '{S}/credits.parquet' (FORMAT parquet)")
    # graph ids: anchors of every work node (keyed and unkeyed in this build) + the tracked unkeyed tables
    db.execute(f"""CREATE TABLE ids AS SELECT DISTINCT lower(a) id, key, resolution FROM
                   (SELECT key, resolution, unnest(anchors) a FROM '{S}/work.parquet') WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'""")
    db.execute(f"""INSERT INTO ids SELECT DISTINCT lower(key), key, resolution FROM '{S}/work.parquet'
                   WHERE key LIKE 'doi:%' OR key LIKE 'openalex:%'""")
    tracked = []
    for p in sorted(glob.glob(str(ROOT / 'data/graph/crossref-cites/articles/part-*.csv.gz'))):
        tracked.append(f"SELECT 'doi:' || lower(doi) id FROM read_csv('{p}', all_varchar=true, header=true)")
    for p in [ROOT / 'data/graph/cited-works/works.csv.gz', ROOT / 'data/graph/jstor-cited-works/works.csv.gz']:
        if p.exists():
            tracked.append(f"SELECT lower(id) id FROM read_csv('{p}', all_varchar=true, header=true)")
    db.execute(f"""INSERT INTO ids SELECT DISTINCT id, id, 'unkeyed-table' FROM ({' UNION ALL '.join(tracked)})
                   WHERE id LIKE 'doi:%' OR id LIKE 'openalex:%'""")
    # cited-works alias ids (all identifiers of a cited work)
    cw = ROOT / 'data/graph/cited-works/works.csv.gz'
    names = db.execute(f"SELECT * FROM read_csv('{cw}', all_varchar=true, header=true) LIMIT 0").description
    names = [n[0] for n in names]
    if 'alias_ids' in names:
        db.execute(f"""INSERT INTO ids SELECT DISTINCT lower(trim(a)), id, 'unkeyed-table' FROM
                       (SELECT id, unnest(string_split(alias_ids, ';')) a FROM read_csv('{cw}', all_varchar=true, header=true))
                       WHERE lower(trim(a)) LIKE 'doi:%' OR lower(trim(a)) LIKE 'openalex:%'""")
    db.execute(f"COPY (SELECT DISTINCT * FROM ids) TO '{S}/ids.parquet' (FORMAT parquet)")
    print(db.execute(f"SELECT resolution, count(*) FROM '{S}/ids.parquet' GROUP BY 1").fetchall())
    print(db.execute(f"SELECT ev, count(*) FROM '{S}/credits.parquet' GROUP BY 1").fetchall())
    (S / 'snapshot.json').write_text(json.dumps(dict(graph_mtime=os.path.getmtime(G / 'work.parquet'), time=time.time())))


# ---------------------------------------------------------------- scan held records

ORCIDS = None


def _scan_one(job):
    path, dest = job
    import orjson
    n = kept = 0
    with gzip.open(path, 'rb') as f, gzip.open(dest + '.tmp', 'wt', encoding='utf-8') as o:
        for line in f:
            n += 1
            hits = set(ORCID_RE.findall(line.decode('utf-8', 'ignore')))
            if not hits or not (hits & ORCIDS):
                continue
            d = orjson.loads(line)
            loc = d.get('primary_location') or {}
            src = loc.get('source') or {}
            auths = []
            mine = []
            for i, a in enumerate(d.get('authorships') or []):
                au = a.get('author') or {}
                oid = (au.get('orcid') or '').rsplit('/', 1)[-1].upper()
                raw = (a.get('raw_orcid') or '').rsplit('/', 1)[-1].upper()
                insts = [dict(name=x.get('display_name'), ror=(x.get('ror') or '').rsplit('/', 1)[-1] or None)
                         for x in a.get('institutions') or []]
                auths.append(dict(pos=i + 1, name=a.get('raw_author_name') or au.get('display_name'),
                                  display=au.get('display_name'), oa_author=(au.get('id') or '').rsplit('/', 1)[-1] or None,
                                  orcid=oid or None, raw_orcid=raw or None, institutions=insts))
                for x, basis in ((raw, 'raw-orcid'), (oid, 'openalex-author-orcid')):
                    if x and x in ORCIDS:
                        mine.append((i + 1, x, basis))
                        break
            if not mine:
                continue
            kept += 1
            ids = d.get('ids') or {}
            rec = dict(oa=(d.get('id') or '').rsplit('/', 1)[-1], doi=(d.get('doi') or '').replace('https://doi.org/', '').lower(),
                       title=d.get('title') or d.get('display_name'), year=d.get('publication_year'), type=d.get('type'),
                       journal=src.get('display_name'), issn_l=src.get('issn_l'), source_type=src.get('type'), raw_source=loc.get('raw_source_name'),
                       publisher=src.get('host_organization_name'), language=d.get('language'),
                       raw_type=loc.get('raw_type'), version=loc.get('version'),
                       pmid=(ids.get('pmid') or '').rsplit('/', 1)[-1] or None,
                       domain=((d.get('primary_topic') or {}).get('domain') or {}).get('display_name'),
                       field=((d.get('primary_topic') or {}).get('field') or {}).get('display_name'),
                       authorships=auths, mine=mine, file=Path(path).parent.name + '/' + Path(path).name)
            o.write(json.dumps(rec, ensure_ascii=False) + '\n')
    os.rename(dest + '.tmp', dest)
    return path, n, kept


def scan(args):
    global ORCIDS
    orcid_key, _ = keyed_orcids()
    ORCIDS = set(orcid_key)
    out = SCRATCH / 'scan'
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for d in HARVEST:
        files += sorted(d.glob('*.jsonl.gz'))
    files += sorted(FETCH.glob('batch-*.jsonl.gz'))
    jobs = []
    for p in files:
        dest = out / (p.parent.name + '--' + p.name.replace('.jsonl.gz', '.jsonl.gz'))
        if not dest.exists():
            jobs.append((str(p), str(dest)))
    print(len(files), 'files,', len(jobs), 'to scan', flush=True)
    tot = kept = 0
    with mp.get_context('fork').Pool(args.workers) as pool:
        for i, (p, n, k) in enumerate(pool.imap_unordered(_scan_one, jobs)):
            tot += n; kept += k
            if i % 50 == 0:
                print(i, p, tot, kept, flush=True)
    print('scanned', tot, 'kept', kept)


# ---------------------------------------------------------------- export

def export(args):
    import pyarrow as pa, pyarrow.parquet as pq
    S = SCRATCH
    orcid_key, c = keyed_orcids()
    labels = dict(c.execute("SELECT key, label FROM keys WHERE type = 'person' AND status IN ('active', 'provisional')").fetchall())
    life = {}
    with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            b = int(r['birth']) if (r['birth'] or '').lstrip('-').isdigit() else None
            dd = int(r['death']) if (r['death'] or '').lstrip('-').isdigit() else None
            life[r['key']] = (b, dd)
    db = duck()
    # graph ids
    gid = {}
    for i, k, res in db.execute(f"SELECT id, key, resolution FROM '{S}/ids.parquet'").fetchall():
        if i not in gid or (gid[i][1] == 'unkeyed-table' and res != 'unkeyed-table') or (gid[i][1] == 'unkeyed' and res not in ('unkeyed', 'unkeyed-table')):
            gid[i] = (k, res)
    keyed_kinds = dict(db.execute(f"SELECT key, kind FROM '{S}/work.parquet'").fetchall())
    # credited titles per person: (person, full title key) -> [(year, work key, kind)], (person, main key) -> ...
    cred_full = collections.defaultdict(list)
    cred_main = collections.defaultdict(list)
    credited_pairs = set()
    q = db.execute(f"""SELECT DISTINCT c.k, w.key, w.label, w.year, w.kind FROM '{S}/credits.parquet' c
                       JOIN '{S}/work.parquet' w ON w.key = c.w""")
    want_people = set(orcid_key.values())
    while True:
        rows = q.fetchmany(200000)
        if not rows:
            break
        for k, w, lab, y, kind in rows:
            if k not in want_people:
                continue
            credited_pairs.add((k, w))
            tk = tkey(lab)
            if len(tk) >= 8:
                cred_full[k, tk].append((y, w, kind))
                mk = main_key(lab)
                if len(mk) >= 12:
                    cred_main[k, mk].append((y, w, kind))
    print('credited title keys', len(cred_full), flush=True)
    # read scanned records; one record per OpenAlex id (fetch, harvest and DOI lookup overlap)
    recs = {}
    for p in sorted((S / 'scan').glob('*.jsonl.gz')):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                src = 'api' if r['file'].startswith('openalex-author-works') else 'disk'
                old = recs.get(r['oa'])
                if old is None:
                    r['held'] = {src}
                    recs[r['oa']] = r
                else:
                    old['held'].add(src)
    print('records with a keyed ORCID', len(recs), flush=True)
    stats = collections.Counter()
    works, authors, existing = [], [], []
    by_doi = {}
    for oa, r in recs.items():
        doi = r['doi'] or ''
        stats['records'] += 1
        t = r['type'] or 'other'
        if t in SKIP_TYPES:
            stats[f'skip_type:{t}'] += 1
            continue
        if not (r['title'] or '').strip():
            stats['skip_no_title'] += 1
            continue
        # credits by exact ORCID
        cr = []
        for pos, orc, basis in r['mine']:
            k = orcid_key.get(orc)
            a = r['authorships'][pos - 1]
            printed = [a['name'] or '', a['display'] or '']
            nc = name_check(labels.get(k, ''), printed)
            state = 'credited'
            if basis == 'openalex-author-orcid' and nc == 'differs':
                state = 'held'
            # OpenAlex author entities merge namesakes (a historian's ORCID on a cardiology paper): outside the
            # History harvest and outside the Social Sciences domain (which holds Arts and Humanities), an
            # entity ORCID is not enough; the ORCID printed by the publisher (raw-orcid) still is
            if basis == 'openalex-author-orcid' and 'disk' not in r['held'] and r.get('domain') not in (None, 'Social Sciences'):
                state = 'held'; nc += ';entity-orcid-outside-social-sciences'
            b, dd = life.get(k, (None, None))
            y = r['year']
            if y and b and y < b + 15:
                state = 'held'; nc += ';before-age-15'
            elif y and not b and y < 1940:
                state = 'held'; nc += ';pre-1940-no-birth-year'
            cr.append(dict(position=pos, person_key=k, basis=basis, state=state, name=a['name'], orcid=orc,
                           oa_author=a['oa_author'], name_check=nc))
        if not cr:
            continue
        ids = (['doi:' + doi] if doi else []) + ['openalex:' + oa.lower()]
        hit = next((gid[i] for i in ids if i in gid), None)
        if hit:
            k, res = hit
            if res in ('unkeyed', 'unkeyed-table'):
                newc = [x for x in cr if (x['person_key'], k) not in credited_pairs]
                if newc:
                    stats['existing_unkeyed_records'] += 1
                    for x in newc:
                        existing.append(dict(work=k, **x))
                else:
                    stats['in_graph_unkeyed_already_credited'] += 1
            else:
                stats['in_graph_keyed_id'] += 1
                if any((x['person_key'], k) not in credited_pairs for x in cr):
                    stats['in_graph_keyed_id_person_not_credited'] += 1
            continue
        # title + year + author
        title_hit = None
        for x in cr:
            for y, w, kind in cred_full.get((x['person_key'], tkey(r['title'])), []):
                if r['year'] is None or y is None or abs(y - r['year']) <= 1:
                    title_hit = w
                    break
            if title_hit:
                break
        if title_hit:
            stats['in_graph_title_year_author'] += 1
            continue
        wid = 'doi:' + doi if doi else 'openalex:' + oa
        if doi and doi in by_doi:
            stats['dup_doi_records'] += 1
            continue
        if doi:
            by_doi[doi] = wid
        kind = KIND.get(t, 'other')
        flags = []
        if doi and PREPRINT_DOI.match(doi) and t != 'preprint':
            flags.append('preprint-server-doi')
        if r.get('version') == 'submittedVersion':
            flags.append('submitted-version')
        if 'api' in r['held'] and 'disk' not in r['held']:
            flags.append('via-api')
        if r.get('source_type') == 'repository':
            flags.append('repository')
        works.append(dict(id=wid, openalex=oa, doi=doi, title=r['title'], year=r['year'], oa_type=t, kind=kind,
                          journal=r['journal'] if r.get('source_type') in ('journal', 'conference') or (t == 'article' and r.get('source_type') != 'repository') else '',
                          source=r['journal'], source_type=r.get('source_type'),
                          container_title=(r.get('raw_source') or '') if t in ('book-chapter', 'reference-entry') else '',
                          issn_l=r['issn_l'], publisher=r['publisher'], language=r['language'],
                          n_authors=len(r['authorships']),
                          # very long author lists (consortium papers) keep the first 50 and the keyed positions
                          authorships=json.dumps([{k2: v for k2, v in a.items() if k2 != 'display'} for a in r['authorships']
                                                  if len(r['authorships']) <= 100 or a['pos'] <= 50 or a['pos'] in {x['position'] for x in cr}],
                                                 ensure_ascii=False),
                          twin_of='', twin_basis='', flags=';'.join(flags), _cr=cr, _held=r['held']))
        for x in cr:
            authors.append(dict(work=wid, **x))
    print(stats, flush=True)
    # a person with many datasets (digitisation records, corpus files): each dataset is flagged as part of a series
    nds = collections.Counter(x['person_key'] for w in works if w['oa_type'] == 'dataset' for x in w['_cr'])
    for w in works:
        if w['oa_type'] == 'dataset' and any(nds[x['person_key']] > 20 for x in w['_cr']):
            w['flags'] = ';'.join(filter(None, [w['flags'], 'dataset-series']))
    # twins: preprint / published and dataset versions, within the table and against the graph
    idx = collections.defaultdict(list)
    for w in works:
        for x in w['_cr']:
            idx[x['person_key'], tkey(w['title'])].append(w)
    pre = lambda w: w['oa_type'] == 'preprint' or 'preprint-server-doi' in w['flags'] or 'submitted-version' in w['flags']
    rank = lambda w: (0 if w['oa_type'] in ('article', 'book', 'book-chapter') and not pre(w) else 1 if not pre(w) else 2,
                      -(w['year'] or 0), w['id'])
    tw = collections.Counter()
    for w in works:
        if len(tkey(w['title'])) < 12:
            continue
        for x in w['_cr']:
            # against the graph: a credited graph work with the same full title (any year) or main title (same year)
            g = cred_full.get((x['person_key'], tkey(w['title'])), [])
            if not g:
                mk = main_key(w['title'])
                g = [z for z in cred_main.get((x['person_key'], mk), []) if w['year'] and z[0] and abs(z[0] - w['year']) <= 1] if len(mk) >= 12 else []
            if g and not w['twin_of']:
                w['twin_of'] = g[0][1]
                w['twin_basis'] = ('graph-title' if tkey(w['title']) and cred_full.get((x['person_key'], tkey(w['title']))) else 'graph-main-title') + \
                    (':preprint' if pre(w) else ':dataset' if w['oa_type'] == 'dataset' else ':version')
                tw[w['twin_basis']] += 1
            # within the table: same person and full title -> all but the best record point at it
            grp = idx[x['person_key'], tkey(w['title'])]
            if len(grp) > 1 and not w['twin_of']:
                best = min(grp, key=rank)
                if best is not w:
                    w['twin_of'] = best['id']
                    w['twin_basis'] = 'table-title' + (':preprint' if pre(w) else ':dataset' if w['oa_type'] == 'dataset' else ':version')
                    tw[w['twin_basis']] += 1
    OUT.mkdir(parents=True, exist_ok=True)
    wcols = ['id', 'openalex', 'doi', 'title', 'year', 'oa_type', 'kind', 'journal', 'issn_l', 'source', 'source_type',
             'publisher', 'language', 'container_title', 'n_authors', 'authorships', 'twin_of', 'twin_basis', 'flags']
    acols = ['work', 'position', 'person_key', 'basis', 'state', 'name', 'orcid', 'oa_author', 'name_check']

    def write(path, rows, cols):
        with gzip.open(path, 'wt', newline='', encoding='utf-8', compresslevel=9) as f:
            wr = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            wr.writeheader()
            for r in rows:
                wr.writerow(r)
    works.sort(key=lambda w: w['id'])
    authors.sort(key=lambda a: (a['work'], a['position']))
    existing.sort(key=lambda a: (a['work'], a['position']))
    write(OUT / 'works.csv.gz', works, wcols)
    write(OUT / 'authors.csv.gz', authors, acols)
    write(OUT / 'existing.csv.gz', existing, acols)
    by_type = collections.Counter(w['oa_type'] for w in works)
    cred_people = {a['person_key'] for a in authors if a['state'] == 'credited'}
    hist_keys, hist_by_key, _ = historian_orcids()
    rep = dict(
        date='2026-11-11', rule='exact ORCID only (raw_orcid printed by the publisher, or the OpenAlex author entity ORCID); '
             'held: entity-ORCID rows whose printed name lacks the key family name, works before age 15 or before 1940 without a birth year',
        sources=dict(disk=[str(p) for p in HARVEST], api=str(FETCH)),
        historian_keys_strong_supported=len(hist_keys), historian_keys_with_orcid=len(hist_by_key),
        keyed_orcids=len(orcid_key), stats=dict(stats),
        works=len(works), works_via_api_only=sum(1 for w in works if 'via-api' in w['flags']),
        works_by_type=dict(by_type.most_common()), works_by_kind=dict(collections.Counter(w['kind'] for w in works).most_common()),
        twins=dict(tw), works_without_twin=sum(1 for w in works if not w['twin_of']),
        author_rows=len(authors), author_rows_by_state=dict(collections.Counter(a['state'] for a in authors)),
        author_rows_by_basis=dict(collections.Counter(a['basis'] for a in authors)),
        people_credited=len(cred_people), historians_credited=len(cred_people & hist_keys),
        existing_unkeyed_credit_rows=len(existing),
        calls=int((FETCH / 'calls.txt').read_text()) if (FETCH / 'calls.txt').exists() else 0)
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1))


# ---------------------------------------------------------------- panel

def panel(args):
    """the probe key and 20 random strong historians with an ORCID: OpenAlex works under their ORCID (held records)
    vs graph credits + this table"""
    S = SCRATCH
    db = duck()
    orcid_key, c = keyed_orcids()
    key_orcids = collections.defaultdict(set)
    for o, k in orcid_key.items():
        key_orcids[k].add(o)
    strong = []
    res = resolver(c)
    with gzip.open(ROLES, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['role'] == 'historian' and r['confidence'] == 'strong' and key_orcids.get(res(r['key'])):
                strong.append(res(r['key']))
    random.seed(20261111)
    keys = [args.probe] + random.sample(sorted(set(strong)), 20)
    # OpenAlex works per key from the scan (all held records, any type)
    oa = collections.defaultdict(dict)
    for p in sorted((S / 'scan').glob('*.jsonl.gz')):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                for pos, orc, basis in r['mine']:
                    k = orcid_key.get(orc)
                    if k in keys:
                        oa[k][r['oa']] = r
    aw = collections.defaultdict(set)
    with gzip.open(OUT / 'authors.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['person_key'] in keys:
                aw[r['person_key']].add(r['work'])
    ex = collections.defaultdict(set)
    with gzip.open(OUT / 'existing.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['person_key'] in keys:
                ex[r['person_key']].add(r['work'])
    gid = {}
    for i, k, res_ in db.execute(f"SELECT id, key, resolution FROM '{S}/ids.parquet'").fetchall():
        gid.setdefault(i, k)
    cred = collections.defaultdict(set)
    for k, w in db.execute(f"SELECT DISTINCT k, w FROM '{S}/credits.parquet' WHERE k IN ({','.join(repr(x) for x in keys)})").fetchall():
        cred[k].add(w)
    labels = dict(c.execute(f"SELECT key, label FROM keys WHERE key IN ({','.join(repr(x) for x in keys)})").fetchall())
    rows = []
    for k in keys:
        n_oa = len(oa[k])
        covered = held_out = 0
        missing = []
        for o, r in oa[k].items():
            ids = (['doi:' + r['doi']] if r['doi'] else []) + ['openalex:' + o.lower()]
            g = next((gid[i] for i in ids if i in gid), None)
            if (g and (g in cred[k] or g in ex[k])) or any(i in aw[k] or i.replace('openalex:w', 'openalex:W') in aw[k] for i in ids):
                covered += 1
            elif r['type'] in SKIP_TYPES:
                held_out += 1
            else:
                missing.append((r['type'], r['year'], (r['title'] or '')[:70], g or ''))
        rows.append(dict(key=k, label=labels.get(k), orcids=';'.join(sorted(key_orcids[k])), openalex_works=n_oa,
                         graph_credits=len(cred[k]), table_works=len(aw[k]), existing_credits=len(ex[k]),
                         oa_covered=covered, oa_skipped_type=held_out, oa_not_covered=len(missing),
                         not_covered_examples=missing[:6]))
    (S / 'panel.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('people')
    f = sp.add_parser('fetch'); f.add_argument('--max', type=int, default=150000); f.add_argument('--batch', type=int, default=50)
    sp.add_parser('snapshot')
    s = sp.add_parser('scan'); s.add_argument('--workers', type=int, default=3)
    sp.add_parser('export')
    p = sp.add_parser('panel'); p.add_argument('--probe', default='p-24137')
    a = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'duck').mkdir(exist_ok=True)
    dict(people=people, fetch=fetch, snapshot=snapshot, scan=scan, export=export, panel=panel)[a.cmd](a)


if __name__ == '__main__':
    main()
