"""Audit of defect class 'OpenAlex author profiles trusted as identity' (2026-11-12; probe: Andrew Watson, p-4256 /
p-21351). Read-only: reads the key log (streamed), the key-log cache, build/graph, data/graph/author-works and the
OpenAlex work folders on E:; writes only to the scratch folder and the output folders named below. Applies nothing.

OpenAlex author ids (A5...) merge namesakes and split people. Two routes took them as identity:
  route a  key-log authored claims minted by scripts/openalex_people_works.py (2026-11-09 and 11-10 rounds): an OpenAlex
           author tied to a key through a shared work (family name) or the profile's ORCID, then the author's other works
           claimed for the key;
  route b  linked AUTHORED credits in data/graph/author-works/ with basis openalex-author-orcid: the work was listed
           under an OpenAlex author profile that carries the key's ORCID, but the work itself does not print it.

Phases (run in order; each writes parquet to SCRATCH):
  claims     stream data/identifiers/events-*.jsonl[.gz] for route-a claim mints -> claims_a.parquet (claim, subject and
             object anchors, OpenAlex author id and name, OpenAlex work id, the tie person, seq), resolved through the
             cache (claim status, person key after merges, work key)
  credits    one table of route-a and route-b credits (person, work, route, OpenAlex author, printed name, printed ORCID,
             entity ORCID) with the facts used by the tests -> credits.parquet
  tests      contradiction tests and support facts per credit; profile anatomy -> tested.parquet, anatomy.json
  sample     stratified audit sample -> SAMPLE csv (the judgments are typed by hand into the csv's 'judgment' column)
  outputs    rule, withdraw proposal (route a), held list, re-credit candidates, route-b unsafe table, report.json

Name agreement uses link_cited_work_authors.forms / name_level as patched by link_work_people (no new name rule);
date windows use career_window's constants (age 20, PhD - 10, death + 2), PhD years without route-a claims.

    python3 scripts/audit_openalex_profiles.py claims; ... oarecs; ... credits; ... tests
    python3 scripts/audit_openalex_profiles.py sample --tag 1 [--where 'namesake_keys >= 2' --exclude sample1.csv --tag 2]
    python3 scripts/audit_openalex_profiles.py outputs --judged 1=<scratch>/sample1-judged.csv,2=<scratch>/sample2-judged.csv
    python3 scripts/audit_openalex_profiles.py probes --keys p-21351,p-4256
"""
import argparse, collections, csv, glob, gzip, json, os, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
G = ROOT / 'build/graph'
SQLITE = ROOT / 'build/keylog-state.sqlite'
SCRATCH = Path(os.environ.get('OAP_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/profiles'))
OUT = ROOT / 'data/identifiers/openalex-profile-claims-2026-11-12'
AW = ROOT / 'data/graph/author-works'
ROWS = {'2026-11-09': '/mnt/e/openalex-people-2026-11-08', '2026-11-10': '/mnt/e/openalex-people-2026-11-09'}
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
BASIS_RE = re.compile(r'^OpenAlex author (A\d+) \((.*)\) wrote (W\d+); the same OpenAlex author wrote works the graph '
                      r'credits to (p-\d+) \(identity by works\)')


def duck():
    import duckdb
    (SCRATCH / 'duck').mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET enable_progress_bar=false; "
               f"SET temp_directory='{SCRATCH}/duck'; SET max_temp_directory_size='8GB'")
    return db


def event_files():
    fs = sorted(glob.glob(str(ROOT / 'data/identifiers/events-*.jsonl.gz')) + glob.glob(str(ROOT / 'data/identifiers/events-*.jsonl')))
    return sorted(fs, key=lambda p: int(re.search(r'events-(\d+)', p).group(1)))


def claims(args):
    import pyarrow as pa, pyarrow.parquet as pq
    cols = collections.defaultdict(list)
    later = collections.Counter()
    n_events = n_work = 0
    ckeys = set()
    for p in event_files():
        op = gzip.open if p.endswith('.gz') else open
        with op(p, 'rt', encoding='utf-8') as f:
            for line in f:
                if 'openalex_people_works' not in line and '"withdraw"' not in line and '"merge"' not in line:
                    continue
                e = json.loads(line)
                if 'openalex_people_works' in (e.get('basis') or ''):
                    n_events += 1
                if e.get('event') == 'mint' and e.get('type') == 'claim' and 'openalex_people_works' in (e.get('basis') or ''):
                    m = BASIS_RE.match(e['basis'])
                    rel = e.get('relation') or {}
                    for k, v in (('claim', e['key']), ('subj', rel.get('subject')), ('obj', rel.get('object')),
                                 ('predicate', rel.get('predicate')), ('oa_author', m.group(1) if m else None),
                                 ('oa_name', m.group(2) if m else None), ('oa_work', m.group(3) if m else None),
                                 ('tie_person', m.group(4) if m else None), ('seq', e.get('seq')),
                                 ('round', (e.get('date') or '')[:10])):
                        cols[k].append(v)
                    ckeys.add(e['key'])
                elif e.get('event') == 'mint' and e.get('type') == 'work' and 'openalex_people_works' in (e.get('basis') or ''):
                    n_work += 1
                elif e.get('event') in ('withdraw', 'merge') and e.get('key') in ckeys:
                    later[e['event']] += 1
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(dict(cols)), SCRATCH / 'claims_raw.parquet')
    # resolve through the cache
    c = sqlite3.connect(f'file:{SQLITE}?mode=ro', uri=True)
    db = duck()
    db.execute(f"ATTACH '{SQLITE}' AS s (TYPE sqlite, READ_ONLY)")
    db.execute(f"""CREATE TABLE ca AS SELECT r.*, k.status AS claim_status, rel.subject AS cur_subj, rel.object AS cur_obj
                   FROM '{SCRATCH}/claims_raw.parquet' r LEFT JOIN s.keys k ON k.key = r.claim
                   LEFT JOIN s.relation rel ON rel.claim = r.claim""")
    # anchors -> keys, then follow merges
    rep = dict(c.execute("SELECT key, replaced_by FROM keys WHERE status = 'merged' AND replaced_by IS NOT NULL").fetchall())

    def res(k):
        n = 0
        while k in rep and n < 30:
            k = rep[k]; n += 1
        return k
    anc = {}
    for (a,) in db.execute("SELECT DISTINCT coalesce(cur_subj, subj) FROM ca UNION SELECT DISTINCT coalesce(cur_obj, obj) FROM ca").fetchall():
        if a is None:
            continue
        if re.match(r'^[pw]-\d+$', a):
            anc[a] = res(a)
            continue
        r = c.execute("SELECT key FROM anchor WHERE anchor = ?", (a,)).fetchone()
        anc[a] = res(r[0]) if r else None
    db.execute("CREATE TABLE amap(a VARCHAR, k VARCHAR)")
    db.executemany("INSERT INTO amap VALUES (?, ?)", list(anc.items()))
    db.execute(f"""COPY (SELECT ca.*, ps.k AS person, wo.k AS work FROM ca
                   LEFT JOIN amap ps ON ps.a = coalesce(ca.cur_subj, ca.subj)
                   LEFT JOIN amap wo ON wo.a = coalesce(ca.cur_obj, ca.obj)) TO '{SCRATCH}/claims_a.parquet'""")
    out = dict(events_with_basis=n_events, work_mints=n_work, claim_mints=len(cols['claim']), later_events=dict(later),
               status=dict(db.execute(f"SELECT claim_status, count(*) FROM '{SCRATCH}/claims_a.parquet' GROUP BY 1").fetchall()),
               basis_unparsed=db.execute(f"SELECT count(*) FROM '{SCRATCH}/claims_a.parquet' WHERE oa_author IS NULL").fetchone()[0],
               person_moved=db.execute(f"SELECT count(*) FROM '{SCRATCH}/claims_a.parquet' WHERE person <> tie_person").fetchone()[0],
               rounds=dict(db.execute(f"SELECT round, count(*) FROM '{SCRATCH}/claims_a.parquet' GROUP BY 1").fetchall()))
    (SCRATCH / 'claims.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


HARVEST = ['/mnt/e/openalex-history-2026-11-08/history', '/mnt/e/openalex-history-2026-11-08/dissertations',
           '/mnt/e/openalex-people-2026-11-09/doi-lookup']
ID_RE = re.compile(r'"id":\s*"https://openalex\.org/(W\d+)"')
WANT = None


def _rec_one(job):
    path, dest = job
    n = 0
    with gzip.open(path, 'rt', encoding='utf-8') as f, open(dest + '.tmp', 'w', encoding='utf-8') as o:
        for line in f:
            m = ID_RE.search(line, 0, 300)
            if not m or m.group(1) not in WANT:
                continue
            d = json.loads(line)
            src = ((d.get('primary_location') or {}).get('source') or {})
            pt = d.get('primary_topic') or {}
            auths = []
            for i, a in enumerate(d.get('authorships') or []):
                au = a.get('author') or {}
                auths.append([i + 1, (au.get('id') or '').rsplit('/', 1)[-1], au.get('display_name'), a.get('raw_author_name'),
                              (au.get('orcid') or '').rsplit('/', 1)[-1], (a.get('raw_orcid') or '').rsplit('/', 1)[-1],
                              [(x.get('ror') or '').rsplit('/', 1)[-1] for x in a.get('institutions') or [] if x.get('ror')]])
            o.write(json.dumps([m.group(1), d.get('publication_year'), d.get('type'), (d.get('title') or '')[:300],
                                src.get('display_name'), (pt.get('field') or {}).get('display_name'),
                                (pt.get('domain') or {}).get('display_name'), auths], ensure_ascii=False) + '\n')
            n += 1
    os.replace(dest + '.tmp', dest)
    return n


def oarecs(args):
    """OpenAlex records of the route-a works (harvest + DOI lookup on E:) -> SCRATCH/oarecs/*.jsonl (compact)"""
    global WANT
    import multiprocessing as mp
    db = duck()
    WANT = {w for (w,) in db.execute(f"SELECT DISTINCT oa_work FROM '{SCRATCH}/claims_a.parquet'").fetchall()}
    db.close()
    out = SCRATCH / 'oarecs'
    out.mkdir(exist_ok=True)
    jobs = []
    for d in HARVEST:
        for p in sorted(glob.glob(d + '/*.jsonl.gz')):
            dest = out / (Path(d).name + '--' + Path(p).name.replace('.jsonl.gz', '.jsonl'))
            if not dest.exists():
                jobs.append((p, str(dest)))
    print(len(WANT), 'works wanted;', len(jobs), 'files', flush=True)
    n = 0
    with mp.get_context('fork').Pool(3) as pool:
        for i, k in enumerate(pool.imap_unordered(_rec_one, jobs)):
            n += k
            if i % 50 == 0:
                print(i, n, flush=True)
    print('records', n)


AW_SCAN = Path(os.environ.get('AW_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/authorworks')) / 'scan'
# credits that rest on something other than an OpenAlex author profile (independent of this class)
STRONG_LINKED = ('author-works:raw-orcid', 'lc', 'jstor-matched:lc', 'edition-roles:lc-main-entry')


def credits(args):
    """route-a and route-b credits with the record facts the tests need -> credits.parquet; the OpenAlex authorship
    table of every profile involved -> profile_works.parquet; independent credits -> strong.parquet"""
    import pyarrow as pa, pyarrow.parquet as pq
    db = duck()
    S = SCRATCH
    # 1. the author-works scan (records with a keyed ORCID: History harvest, DOI lookup, per-ORCID fetch) as authorships
    if not (S / 'scan_auth.parquet').exists():
        cols = collections.defaultdict(list)
        writer = None
        for p in sorted(AW_SCAN.glob('*.jsonl.gz')):
            with gzip.open(p, 'rt', encoding='utf-8') as f:
                for line in f:
                    r = json.loads(line)
                    for a in r['authorships']:
                        for k, v in (('oa_work', r['oa']), ('doi', r['doi'] or ''), ('year', r['year']), ('type', r['type']),
                                     ('domain', r.get('domain')), ('pos', a['pos']), ('oa_author', a['oa_author'] or ''),
                                     ('name', a['name'] or ''), ('display', a['display'] or ''), ('orcid', a['orcid'] or ''),
                                     ('raw_orcid', a['raw_orcid'] or ''),
                                     ('rors', [x['ror'] for x in a['institutions'] if x.get('ror')])):
                            cols[k].append(v)
            if len(cols['oa_work']) > 2_000_000:
                t = pa.table(dict(cols)); writer = writer or pq.ParquetWriter(S / 'scan_auth.parquet', t.schema)
                writer.write_table(t); cols = collections.defaultdict(list)
        t = pa.table(dict(cols)); writer = writer or pq.ParquetWriter(S / 'scan_auth.parquet', t.schema)
        writer.write_table(t); writer.close()
        print('scan authorships written', flush=True)
    # 2. route-a OpenAlex records (compact) -> authorships
    if not (S / 'reca_auth.parquet').exists():
        cols = collections.defaultdict(list)
        seen = set()
        for p in sorted((S / 'oarecs').glob('*.jsonl')):
            for line in open(p, encoding='utf-8'):
                w, year, typ, title, venue, field, domain, auths = json.loads(line)
                if w in seen:
                    continue
                seen.add(w)
                n = len(auths)
                for pos, aid, disp, raw, orc, rorc, rors in auths:
                    for k, v in (('oa_work', w), ('year', year), ('type', typ), ('field', field), ('domain', domain),
                                 ('n_authors', n), ('pos', pos), ('oa_author', aid), ('display', disp or ''), ('name', raw or ''),
                                 ('orcid', orc or ''), ('raw_orcid', rorc or ''), ('rors', rors)):
                        cols[k].append(v)
        pq.write_table(pa.table(dict(cols)), S / 'reca_auth.parquet')
        print('route-a authorships written', flush=True)
    # 3. graph work anchors (doi / openalex) -> key
    db.execute(f"""CREATE TABLE wanc AS SELECT key, lower(a) AS a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet')
                   WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'""")
    # 4. the profiles involved: route a authors, route b authors
    db.execute(f"""CREATE TABLE rb AS SELECT a."from" AS person, a."to" AS work, a.claim,
                     CAST(regexp_extract(a.claim, ':(\\d+)$', 1) AS INT) AS position, a.role
                   FROM '{G}/authored.parquet' a WHERE a.source = 'author-works:openalex-author-orcid'""")
    db.execute(f"""CREATE TABLE rb2 AS SELECT rb.*, x.name AS printed, x.orcid AS entity_orcid, x.oa_author, x.name_check
                   FROM rb LEFT JOIN (SELECT * FROM read_csv('{AW}/authors.csv.gz', all_varchar=true)
                                      UNION ALL SELECT * FROM read_csv('{AW}/existing.csv.gz', all_varchar=true)) x
                   ON x.work = rb.work AND x.person_key = rb.person AND CAST(x.position AS INT) = rb.position""")
    print('route b rows', db.execute("SELECT count(*), count(oa_author) FROM rb2").fetchone(), flush=True)
    db.execute(f"""CREATE TABLE wks AS SELECT id, openalex, title, TRY_CAST(year AS INT) AS year, oa_type, kind, journal,
                     TRY_CAST(n_authors AS INT) AS n_authors, authorships, flags
                   FROM read_csv('{AW}/works.csv.gz', all_varchar=true, max_line_size=20000000)""")
    db.execute(f"""CREATE TABLE ca AS SELECT * FROM '{S}/claims_a.parquet'""")
    db.execute("""CREATE TABLE prof AS SELECT DISTINCT oa_author FROM ca UNION SELECT DISTINCT oa_author FROM rb2 WHERE oa_author IS NOT NULL""")
    # 5. every work of those profiles we hold: History-harvest rows (both rounds) and the scan
    rows = ' UNION ALL '.join(f"SELECT author AS oa_author, work AS oa_work, doi, year, name AS display, family, orcid "
                              f"FROM read_parquet('{d}/rows/*.parquet', union_by_name=true)" for d in ROWS.values())
    db.execute(f"""COPY (SELECT oa_author, oa_work, any_value(doi) AS doi, any_value(year) AS year, any_value(display) AS display,
                          any_value(orcid) AS orcid
                   FROM (SELECT oa_author, oa_work, doi, year, display, orcid FROM ({rows}) WHERE oa_author IN (SELECT oa_author FROM prof)
                         UNION ALL SELECT oa_author, oa_work, doi, year, display, orcid FROM '{S}/scan_auth.parquet'
                         WHERE oa_author IN (SELECT oa_author FROM prof))
                   GROUP BY oa_author, oa_work) TO '{S}/profile_works.parquet'""")
    print('profile works', db.execute(f"SELECT count(*), count(DISTINCT oa_author) FROM '{S}/profile_works.parquet'").fetchone(), flush=True)
    # 6. independent credits: key-log claims other than route a, and linked credits by a printed ORCID or LC
    db.execute(f"""COPY (SELECT DISTINCT a."from" AS person, a."to" AS work, CASE WHEN a.evidence = 'keylog' THEN 'keylog' ELSE a.source END AS ev
                   FROM '{G}/authored.parquet' a
                   WHERE (a.evidence = 'keylog' AND a.claim NOT IN (SELECT claim FROM ca)) OR a.source IN {STRONG_LINKED}
                   UNION SELECT DISTINCT e."from", e."to", 'keylog-edited' FROM '{G}/edited.parquet' e WHERE e.evidence = 'keylog')
                   TO '{S}/strong.parquet'""")
    # 7. the credits
    db.execute(f"""CREATE TABLE cra AS SELECT 'a' AS route, ca.claim, ca.person, ca.work, ca.oa_author, ca.oa_work, ca.round,
                     ca.oa_name, r.pos AS position, r.name AS printed, r.display, r.orcid AS entity_orcid, r.raw_orcid, r.rors,
                     r.n_authors, r.type AS oa_type, r.field, r.domain
                   FROM ca LEFT JOIN (SELECT * FROM '{S}/reca_auth.parquet') r ON r.oa_work = ca.oa_work AND r.oa_author = ca.oa_author""")
    db.execute(f"""CREATE TABLE crb AS SELECT 'b' AS route, rb2.claim, rb2.person, rb2.work, rb2.oa_author, wks.openalex AS oa_work,
                     NULL AS round, NULL AS oa_name, rb2.position, rb2.printed, NULL AS display, rb2.entity_orcid,
                     json_extract_string(wks.authorships, '$[' || (rb2.position - 1) || '].raw_orcid') AS raw_orcid,
                     NULL AS rors, wks.n_authors, wks.oa_type, NULL AS field, NULL AS domain
                   FROM rb2 LEFT JOIN wks ON wks.id = rb2.work""")
    db.execute(f"""COPY (SELECT c.*, w.year, w.kind, w.label AS title, w.journal FROM
                   (SELECT * FROM cra UNION ALL BY NAME SELECT * FROM crb) c
                   LEFT JOIN (SELECT key, year, kind, label, journal FROM '{G}/work.parquet') w ON w.key = c.work)
                   TO '{S}/credits.parquet'""")
    print(db.execute(f"""SELECT route, count(*), count(year), count(printed), count(DISTINCT person), count(DISTINCT oa_author)
                         FROM '{S}/credits.parquet' GROUP BY 1""").fetchall())


HARD = ('date-before-window', 'date-after-death', 'name-given-differs', 'name-family-differs', 'printed-orcid-differs',
        'profile-orcid-differs', 'profile-orcid-other-key', 'other-key-holds-position')
INDEPENDENT_AFF = ('aha_directory', 'aha_advisor', 'ihr', 'orcid', 'wikidata', 'lc_373')   # link_work_people.INDEPENDENT_AFF
SLACK = 10                                                                                 # link_cited_work_authors.SLACK


def tests(args):
    """contradiction tests, support facts and profile anatomy per credit -> tested.parquet, anatomy.json"""
    import pyarrow as pa, pyarrow.parquet as pq
    import link_work_people as W            # name rules: forms + name_level (with the linker's refusal)
    from career_window import BEFORE_PHD, ADULT, AFTER_DEATH
    L = W.L
    S = SCRATCH
    db = duck()
    db.execute(f"CREATE TABLE cr AS SELECT * FROM '{S}/credits.parquet' QUALIFY row_number() OVER (PARTITION BY route, claim, person, work ORDER BY position) = 1")
    db.execute("ALTER TABLE cr ADD COLUMN cid VARCHAR; UPDATE cr SET cid = CASE WHEN route = 'a' THEN claim ELSE person || '|' || work || '|' || position END")
    people = {p for (p,) in db.execute("SELECT DISTINCT person FROM cr").fetchall()}
    c = sqlite3.connect(f'file:{SQLITE}?mode=ro', uri=True)
    # person facts
    label, aliases, orcids, anchors = {}, {}, collections.defaultdict(set), {}
    for k, lab, als, an in c.execute("SELECT key, label, aliases, anchors FROM keys WHERE type = 'person' AND status IN ('active', 'provisional')"):
        for a in json.loads(an or '[]'):
            if a.startswith('orcid:'):
                orcids[k].add(a[6:].upper())
        if k in people:
            label[k] = lab or ''
            aliases[k] = [x for x in json.loads(als or '[]') if isinstance(x, str)]
            anchors[k] = json.loads(an or '[]')
    orcid_key = collections.defaultdict(set)
    for k, os_ in orcids.items():
        for o in os_:
            orcid_key[o].add(k)
    life = {}
    with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['key'] in people:
                life[r['key']] = (int(r['birth']) if r['birth'].lstrip('-').isdigit() else None,
                                  int(r['death']) if r['death'].lstrip('-').isdigit() else None)
    aha = {}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        if r.get('year'):
            aha['aha-phd:' + r['id']] = int(r['year'])
    phd = {}
    for k in people:
        ys = [aha[a] for a in anchors.get(k, ()) if a in aha]
        if ys:
            phd[k] = min(ys)
    for k, y in db.execute(f"""SELECT s.person, min(w.year) FROM '{S}/strong.parquet' s JOIN '{G}/work.parquet' w ON w.key = s.work
                               WHERE w.kind = 'thesis' AND w.year IS NOT NULL AND s.ev = 'keylog' AND s.person IN (SELECT person FROM cr)
                               GROUP BY 1""").fetchall():
        phd[k] = min(phd.get(k, y), y)
    # the key's own dated works by independent evidence: the linker's span fallback (link_cited_work_authors.date_test,
    # SPAN_BEFORE) for keys with no life or PhD years
    span_lo = dict(db.execute(f"""SELECT s.person, min(coalesce(w.first_year, w.year)) FROM '{S}/strong.parquet' s
                                  JOIN '{G}/work.parquet' w ON w.key = s.work
                                  WHERE coalesce(w.first_year, w.year) BETWEEN 1500 AND 2030 AND s.person IN (SELECT person FROM cr)
                                  GROUP BY 1""").fetchall())
    # the linker's SPAN_BEFORE (10) is tuned for linking; as a contradiction the gap must be wide: audited at 10 years
    # most hits were the key's own early works (keys known only from recent works), at 40 years about two thirds were
    # another person (2026-11-12 sample of 25), so 50
    SPAN_GAP = 50
    window, inconsistent = {}, set()
    for k in people:
        b, d = life.get(k, (None, None))
        p = phd.get(k)
        if b is not None and p is not None and not b + 20 <= p <= b + 75:
            inconsistent.add(k); continue
        lo = b + ADULT if b is not None else (p - BEFORE_PHD if p is not None else None)
        window[k] = (lo, d + AFTER_DEATH if d is not None else None)
    print('people', len(people), 'windows', sum(1 for v in window.values() if v[0] or v[1]), 'inconsistent', len(inconsistent), flush=True)
    # strong credits: per work, per person; independent co-author pairs; venues
    strong_on = collections.defaultdict(set)
    for p, w in db.execute(f"""SELECT person, work FROM '{S}/strong.parquet' WHERE work IN (SELECT work FROM cr)""").fetchall():
        strong_on[w].add(p)
    for w in list(strong_on):
        strong_on[w] = frozenset(strong_on[w])
    db.execute(f"""CREATE TABLE st AS SELECT DISTINCT person, work FROM '{S}/strong.parquet'""")
    db.execute("""CREATE TABLE stw AS SELECT work FROM st GROUP BY work HAVING count(*) BETWEEN 2 AND 25""")
    pairs = set()
    q = db.execute("""SELECT DISTINCT a.person, b.person FROM st a JOIN st b ON a.work = b.work AND a.person <> b.person
                      WHERE a.work IN (SELECT work FROM stw) AND a.person IN (SELECT person FROM cr)""")
    while True:
        rows = q.fetchmany(500000)
        if not rows:
            break
        pairs.update(rows)
    for a, b in db.execute(f"""SELECT "from", "to" FROM {W.keylog(G, 'advised')}""").fetchall():
        pairs.add((a, b)); pairs.add((b, a))
    print('independent co-author pairs', len(pairs), flush=True)
    # titles held by independent credits: a namesake key may already hold the same title under another work key
    # (a twin: the chapter and its repository copy); author_works.tkey is the normalised full title
    import author_works as AWM
    db.create_function('tkey', AWM.tkey, ['VARCHAR'], 'VARCHAR')
    db.execute(f"""CREATE TABLE ct AS SELECT DISTINCT tkey(w.label) AS t FROM cr JOIN '{G}/work.parquet' w ON w.key = cr.work
                   WHERE length(w.label) >= 20""")
    title_holders = collections.defaultdict(set)
    for t, p in db.execute(f"""SELECT x.t, st.person FROM (SELECT DISTINCT person, work FROM '{S}/strong.parquet') st
                               JOIN (SELECT key, tkey(label) AS t FROM '{G}/work.parquet' WHERE length(label) >= 20) x ON x.key = st.work
                               WHERE x.t IN (SELECT t FROM ct) AND length(x.t) >= 15""").fetchall():
        title_holders[t].add(p)
    print('titles held independently', len(title_holders), flush=True)
    venues = collections.defaultdict(set)
    for p, j in db.execute(f"""SELECT s.person, lower(w.journal) FROM st s JOIN '{G}/work.parquet' w ON w.key = s.work
                               WHERE w.journal IS NOT NULL AND s.person IN (SELECT person FROM cr)""").fetchall():
        venues[p].add(j)
    # dated independent affiliations (ROR)
    ror_of = dict(db.execute(f"SELECT key, ror FROM '{G}/institution.parquet' WHERE ror IS NOT NULL").fetchall())
    aff = collections.defaultdict(list)
    with gzip.open(ROOT / 'data/graph/affiliations.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['person'] in people and r['source'] in INDEPENDENT_AFF and r['institution'] in ror_of and (r['first_year'] or r['last_year']):
                y0 = int(r['first_year'] or r['last_year']); y1 = int(r['last_year'] or r['first_year'])
                aff[r['person']].append((ror_of[r['institution']], y0, y1))
    # route-b institutions from the works table
    rb_rors = {}
    q = db.execute(f"""SELECT id, authorships FROM read_csv('{AW}/works.csv.gz', all_varchar=true, max_line_size=20000000)
                       WHERE id IN (SELECT work FROM cr WHERE route = 'b')""")
    while True:
        rows = q.fetchmany(50000)
        if not rows:
            break
        for w, js in rows:
            for au in json.loads(js or '[]'):
                rors = [i.get('ror') for i in au.get('institutions') or [] if i.get('ror')]
                if rors:
                    rb_rors[w, au.get('pos')] = rors
    # profiles: works, years, keys
    prof_years = collections.defaultdict(list)
    for a, y in db.execute(f"SELECT oa_author, year FROM '{S}/profile_works.parquet' WHERE year IS NOT NULL").fetchall():
        prof_years[a].append(y)
    db.execute(f"""CREATE TABLE wanc AS SELECT key, lower(a) AS a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet')
                   WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'""")
    # independent works of a profile for a key: a profile work the key holds by independent evidence
    indep = collections.Counter()
    db.execute(f"""CREATE TABLE pwa AS SELECT DISTINCT oa_author, 'openalex:' || lower(oa_work) AS a FROM '{S}/profile_works.parquet'
                   UNION SELECT DISTINCT oa_author, 'doi:' || lower(doi) FROM '{S}/profile_works.parquet' WHERE doi <> ''""")
    db.execute("CREATE TABLE pw2 AS SELECT DISTINCT pwa.oa_author, coalesce(wanc.key, pwa.a) AS wk FROM pwa LEFT JOIN wanc ON wanc.a = pwa.a")
    for a, p, n in db.execute(f"""
            SELECT pw2.oa_author, st.person, count(DISTINCT pw2.wk) FROM pw2 JOIN st ON st.work = pw2.wk
            JOIN (SELECT DISTINCT oa_author, person FROM cr) ap ON ap.oa_author = pw2.oa_author AND ap.person = st.person
            GROUP BY 1, 2""").fetchall():
        indep[a, p] = n
    print('indep pairs', len(indep), flush=True)
    prof_keys = collections.defaultdict(set)
    for a, p in db.execute("SELECT DISTINCT oa_author, person FROM cr").fetchall():
        prof_keys[a].add(p)
    for d in ROWS.values():
        for a, p in db.execute(f"SELECT DISTINCT author, person FROM '{d}/ties.parquet'").fetchall():
            if a in prof_keys:
                prof_keys[a].add(p)
    def prof_shape(a):
        ys = sorted(prof_years.get(a, ()))
        if not ys:
            return None, None, 0
        span = ys[-1] - ys[0]
        gap = 0
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] > gap and i >= 2 and len(ys) - i >= 2:
                gap = ys[i] - ys[i - 1]
        return span, gap, len(ys)
    shape = {a: prof_shape(a) for a in prof_keys}
    # name forms
    kforms = {}
    def key_forms(k):
        if k not in kforms:
            fs = []
            for nm in [label.get(k, '')] + aliases.get(k, []):
                # a label qualifier with a lower-case word ('(Gender historian)') is not LC's fuller form of the name
                nm = re.sub(r'\s*\((?=[^)]*\b[a-z]{3,})[^)]*\)', ' ', nm or '').strip()
                fs += L.forms(nm)
            kforms[k] = fs
        return kforms[k]
    def name_test(k, printed):
        # input cleaning, not a matching rule: a printed affiliation or role in parentheses ('Stacey Hynd (University of
        # Cambridge)', 'Simon Devereaux (Lecturer in History)') is not part of the name
        printed = re.sub(r'\s*\([^)]*\)', ' ', printed or '').strip()
        pf = L.forms(printed or '')
        ws = (printed or '').split()
        if ',' not in (printed or '') and len(ws) == 2:          # 'Catto Michela', 'Fedinec Csilla': family first
            pf = pf + L.forms(ws[1] + ' ' + ws[0])
        if not pf:
            return 'name-unread', None
        kf = key_forms(k)
        if not kf:
            return 'name-unread', None
        fam_hit, best = False, None
        order = ('full', 'variant', 'initial')
        for f, _, g in pf:
            for f2, _, g2 in kf:
                # compound and reordered family names ('Teira Serrano' / 'Teira', 'Catto Michela', 'Windsor-Liscombe'):
                # a shared family word is a family match (audit 2026-11-12: 10 of 10 'family differs' were these)
                # not 'e miller' (an initial read as a family word); Catalan / Spanish joining 'i' / 'y' dropped; a typo
                # or transliteration of the family name (Leersen / Leerssen, Hggoy / Heggoy: the linker's lev_dist <= 2)
                fw, fw2 = f.split(), f2.split()
                one = any(len(x) == 1 and x not in ('i', 'y') for x in fw + fw2)
                shared = not one and {x for x in fw if len(x) > 1} & {x for x in fw2 if len(x) > 1}
                a, b = f.replace(' ', ''), f2.replace(' ', '')
                close = not one and min(len(a), len(b)) >= 5 and L.lev_dist(a, b) <= 2
                if f == f2 or a == b or shared or close:
                    fam_hit = True
                    lev = W.name_level(g, g2)
                    if lev and (best is None or order.index(lev) < order.index(best)):
                        best = lev
        if not fam_hit:
            return 'name-family-differs', None
        if best is None:
            return 'name-given-differs', None
        return None, best
    def first_key(lab):
        fs = L.forms(lab or '')
        return (fs[0][0], fs[0][2][0]) if fs and fs[0][2] else None
    namesakes = collections.Counter()
    key_name = {}
    for k, lab in c.execute("SELECT key, label FROM keys WHERE type = 'person' AND status IN ('active', 'provisional')"):
        nk = first_key(lab)
        if nk:
            namesakes[nk] += 1
            if k in people:
                key_name[k] = nk
    rows = db.execute("SELECT * FROM cr").fetchall()
    cols = [d[0] for d in db.description]
    out = collections.defaultdict(list)
    for r in rows:
        r = dict(zip(cols, r))
        k, w, y = r['person'], r['work'], r['year']
        hard, desc, sup = [], [], []
        if k in strong_on.get(w, ()):
            sup.append('already-independent')
        ko = orcids.get(k, set())
        raw = (r['raw_orcid'] or '').upper()
        ent = (r['entity_orcid'] or '').upper()
        if raw and raw in ko:
            sup.append('printed-orcid-same')
        elif raw:
            other = orcid_key.get(raw, set()) - {k}
            if ko or other:
                hard.append('printed-orcid-differs')
            else:
                desc.append('printed-orcid-unkeyed')
        if ent and ent not in ko:
            if orcid_key.get(ent, set()) - {k}:
                hard.append('profile-orcid-other-key')
            elif ko:
                hard.append('profile-orcid-differs')
            else:
                desc.append('profile-orcid-unkeyed')
        # dates (career_window; reviews from PhD - 9 as the linker's PHD_START)
        if k in inconsistent:
            desc.append('window-inconsistent')
        elif y:
            lo, hi = window.get(k, (None, None))
            if r['kind'] == 'review' and k in phd and (lo is None or phd[k] - 9 > lo):
                lo = phd[k] - 9
            if lo is not None and y < lo:
                hard.append('date-before-window')
            elif lo is None and k in span_lo and y < span_lo[k] - SPAN_GAP:
                hard.append('date-before-span')
            if hi is not None and y > hi:
                if r['kind'] in ('book', 'chapter'):
                    desc.append('after-death-book')
                else:
                    hard.append('date-after-death')
        nt, lev = name_test(k, r['printed'] or r['display'])
        if nt == 'name-family-differs' and r['display'] and r['printed']:     # not for given names: the display name is the profile's
            nt2, lev2 = name_test(k, r['display'])
            if nt2 is None:                      # a truncated or mis-encoded printed name ('Jill Ker', 'Jan RÃ¼ger')
                nt, lev = None, lev2
        if nt == 'name-family-differs':
            # author_works.name_check, the route's own guard, on the printed name alone: a family word of the key anywhere
            # in it ('Laurent, Cesari', 'Rosa Congost i Colomer') is a parse problem, not another person
            # and no word of the key's name other than its first given name is in the printed name, give or take a typo
            # (Simon i Tarres / 'Antoni Simon', Prott / 'Prot', Michlic / 'Michlic-Coren')
            pr = re.sub(r'\s*\([^)]*\)', ' ', r['printed'] or r['display'] or '')
            pw = set(re.findall(r'[a-z]{2,}', L.nfold(re.sub(r'[^\w]', ' ', pr))))      # U+2010 hyphens split words
            kw = set()
            for nm in [label.get(k, '')] + aliases.get(k, []):
                fs = L.forms(nm)
                first = fs[0][2][0] if fs and fs[0][2] else None
                kw |= {x for x in re.findall(r'[a-z]{3,}', L.nfold(re.sub(r'[\d\W]', ' ', nm or ''))) if x != first}
            if any(AWM.name_check(nm, [pr]) != 'differs' for nm in [label.get(k, '')] + aliases.get(k, [])) or \
                    any(x == y or (min(len(x), len(y)) >= 5 and L.lev_dist(x, y) <= (1 if min(len(x), len(y)) < 7 else 2))
                        for x in kw for y in pw):
                nt = 'name-unparsed'
        if nt in ('name-family-differs', 'name-given-differs'):
            hard.append(nt)
        elif nt:
            desc.append(nt)
        # another key holds this printed position by independent evidence
        others = [q for q in strong_on.get(w, ()) if q != k]
        holder = [q for q in others if name_test(q, r['printed'] or r['display'])[0] is None]
        if holder and 'already-independent' not in sup:
            hard.append('other-key-holds-position')
        if r['title'] and len(r['title']) >= 20 and len(AWM.tkey(r['title'])) >= 15:   # Latin-script titles only
            th = [q for q in title_holders.get(AWM.tkey(r['title']), ()) if q != k and q not in holder]
            th = [q for q in th if name_test(q, r['printed'] or r['display'])[0] is None]
            if th and 'already-independent' not in sup and k not in title_holders.get(AWM.tkey(r['title']), ()):
                hard.append('other-key-holds-title')
                holder = holder + th
        if any((k, q) in pairs for q in others):
            sup.append('coauthor')
        rors = r['rors'] if r['route'] == 'a' else rb_rors.get((w, r['position']))
        if rors and y:
            if any(ro in rors and y0 - SLACK <= y <= y1 + SLACK for ro, y0, y1 in aff.get(k, ())):
                sup.append('inst')
        if r['journal'] and r['journal'].lower() in venues.get(k, ()):
            desc.append('venue-shared')
        a = r['oa_author']
        span, gap, n = shape.get(a, (None, None, 0))
        if span is not None and span >= 60:
            desc.append('profile-span-60')
        if gap and gap >= 25:
            desc.append('profile-gap-25')
        if len(prof_keys.get(a, ())) >= 2:
            desc.append('profile-multi-key')
        ind = indep.get((a, k), 0)
        for kk, v in (('route', r['route']), ('cid', r['cid']), ('claim', r['claim']), ('person', k), ('work', w), ('oa_author', a),
                      ('oa_work', r['oa_work']), ('round', r['round']), ('printed', r['printed']), ('display', r['display']),
                      ('raw_orcid', raw), ('entity_orcid', ent), ('year', y), ('kind', r['kind']), ('oa_type', r['oa_type']),
                      ('title', r['title']), ('journal', r['journal']), ('field', r['field']), ('n_authors', r['n_authors']),
                      ('name_level', lev), ('indep_works', ind), ('profile_span', span), ('profile_gap', gap), ('profile_n', n),
                      ('profile_keys', len(prof_keys.get(a, ()))), ('hard', ';'.join(hard)), ('support', ';'.join(sup)),
                      ('desc', ';'.join(desc)), ('holder', ';'.join(holder)), ('label', label.get(k, '')),
                      ('key_orcid', ';'.join(sorted(ko))), ('birth', life.get(k, (None, None))[0]), ('death', life.get(k, (None, None))[1]),
                      ('phd', phd.get(k)), ('namesake_keys', namesakes.get(key_name.get(k), 1))):
            out[kk].append(v)
    # a profile that brings this key two or more date-contradicted works is a merged profile for this key: its other
    # works without a positive fact are suspect too (career-span test at the level of the profile)
    bad = collections.Counter()
    for a, k, h in zip(out['oa_author'], out['person'], out['hard']):
        if 'date-before-window' in h or 'date-before-span' in h:
            bad[a, k] += 1
    for i, (a, k, h, sp) in enumerate(zip(out['oa_author'], out['person'], out['hard'], out['support'])):
        if bad[a, k] >= 2 and 'date-before' not in h and not ({'printed-orcid-same', 'already-independent', 'coauthor', 'inst'} & set(sp.split(';'))):
            out['hard'][i] = ';'.join(filter(None, [h, 'profile-contaminated']))
    pq.write_table(pa.table(dict(out)), S / 'tested.parquet')
    print('tested', len(out['claim']), flush=True)


def klass(hard, sup, ind):
    """the stratum of a credit (before any rule): which test decides it"""
    sup = set(filter(None, (sup or '').split(';')))
    hard = [h for h in (hard or '').split(';') if h]
    if 'printed-orcid-same' in sup:
        return 'safe:printed-orcid'
    if 'already-independent' in sup:
        return 'safe:already-independent'
    if hard:
        return 'hard:' + hard[0]
    if ind >= 2:
        return 'clean:indep2+'
    if sup & {'coauthor', 'inst'}:
        return 'clean:fact'
    return f'clean:indep{ind}'


def sample(args):
    """stratified audit sample with a dossier per credit -> SCRATCH/sample.csv, SCRATCH/dossiers.txt"""
    import random
    S = SCRATCH
    db = duck()
    db.execute(f"CREATE TABLE t AS SELECT * FROM '{S}/tested.parquet'")
    db.create_function('klass', klass, ['VARCHAR', 'VARCHAR', 'BIGINT'], 'VARCHAR')
    db.execute("ALTER TABLE t ADD COLUMN stratum VARCHAR; UPDATE t SET stratum = route || '/' || klass(hard, support, indep_works)")
    if args.where:                       # a risk-targeted draw (e.g. namesake_keys >= 2), strata suffixed '+'
        db.execute(f"DELETE FROM t WHERE NOT ({args.where})")
        db.execute("UPDATE t SET stratum = stratum || '+'")
    if args.exclude:
        ex = {r['cid'] for f in args.exclude.split(',') for r in csv.DictReader(open(f, encoding='utf-8'))}
        db.execute("CREATE TABLE ex(cid VARCHAR)"); db.executemany("INSERT INTO ex VALUES (?)", [(x,) for x in ex])
        db.execute("DELETE FROM t WHERE cid IN (SELECT cid FROM ex)")
    counts = db.execute("SELECT stratum, count(*) FROM t GROUP BY 1 ORDER BY 1").fetchall()
    print(counts)
    per = dict(x.split('=') for x in (args.per or '').split(',') if x)
    rng = random.Random(20261112)
    picks = []
    for st, n in counts:
        want = int(per.get(st, args.n))
        ids = [r[0] for r in db.execute("SELECT cid FROM t WHERE stratum = ? ORDER BY cid", [st]).fetchall()]
        picks += [(st, c) for c in rng.sample(ids, min(want, len(ids)))]
    db.execute("CREATE TABLE pk(stratum VARCHAR, cid VARCHAR)")
    db.executemany("INSERT INTO pk VALUES (?, ?)", picks)
    db.execute("CREATE TABLE s AS SELECT t.* FROM t JOIN pk USING (stratum, cid) ORDER BY stratum, cid")
    # the key's independent works and the credit's printed authors
    own = collections.defaultdict(list)
    for p, y, kind, lab, j in db.execute(f"""SELECT st.person, w.year, w.kind, w.label, w.journal FROM '{S}/strong.parquet' st
                                            JOIN '{G}/work.parquet' w ON w.key = st.work WHERE st.person IN (SELECT person FROM s)
                                            ORDER BY w.year""").fetchall():
        own[p].append((y, kind, (lab or '')[:90], (j or '')[:40]))
    auths = {}
    for w, js in db.execute(f"""SELECT id, authorships FROM read_csv('{AW}/works.csv.gz', all_varchar=true, max_line_size=20000000)
                               WHERE id IN (SELECT work FROM s WHERE route = 'b')""").fetchall():
        auths[w] = [(a.get('name'), a.get('raw_orcid') or '', [i.get('name') for i in a.get('institutions') or []][:1]) for a in json.loads(js)]
    for w, pos, nm, ro, ror in db.execute(f"""SELECT oa_work, pos, name, raw_orcid, rors FROM '{S}/reca_auth.parquet'
                                             WHERE oa_work IN (SELECT oa_work FROM s WHERE route = 'a') ORDER BY oa_work, pos""").fetchall():
        auths.setdefault(w, []).append((nm, ro, ror[:1]))
    prof = collections.defaultdict(list)
    for a, y, d in db.execute(f"""SELECT oa_author, year, any_value(display) FROM '{S}/profile_works.parquet'
                                 WHERE oa_author IN (SELECT oa_author FROM s) GROUP BY 1, 2 ORDER BY 1, 2""").fetchall():
        prof[a].append(y)
    cols = [d[0] for d in db.execute("SELECT * FROM s LIMIT 0").description]
    rows = [dict(zip(cols, r)) for r in db.execute("SELECT * FROM s").fetchall()]
    with open(S / f'dossiers{args.tag}.txt', 'w', encoding='utf-8') as f:
        for i, r in enumerate(rows, 1):
            key = r['work'] if r['route'] == 'b' else r['oa_work']
            f.write(f"\n#{i} [{r['stratum']}] {r['claim']} {r['person']} '{r['label']}' orcid={r['key_orcid'] or '-'} "
                    f"life={r['birth']}-{r['death']} phd={r['phd']}\n")
            f.write(f"  CREDIT {r['year']} {r['kind']}/{r['oa_type']} '{(r['title'] or '')[:150]}' in '{r['journal'] or ''}' field={r['field']}\n")
            f.write(f"  printed='{r['printed']}' display='{r['display']}' raw_orcid={r['raw_orcid'] or '-'} entity_orcid={r['entity_orcid'] or '-'} "
                    f"n_auth={r['n_authors']}\n")
            f.write(f"  authors: {auths.get(key, [])[:8]}\n")
            ys = prof.get(r['oa_author'], [])
            f.write(f"  profile {r['oa_author']} works={r['profile_n']} span={r['profile_span']} gap={r['profile_gap']} keys={r['profile_keys']} "
                    f"years={ys[:3]}..{ys[-3:]} indep={r['indep_works']}\n")
            f.write(f"  hard={r['hard']} support={r['support']} desc={r['desc']} holder={r['holder']}\n")
            ow = own.get(r['person'], [])
            f.write(f"  key's independent works ({len(ow)}):\n")
            step = max(1, len(ow) // 12)
            for x in ow[::step][:12]:
                f.write(f"     {x}\n")
    with open(S / f'sample{args.tag}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        keep = ['stratum', 'route', 'cid', 'claim', 'person', 'label', 'work', 'oa_author', 'year', 'kind', 'title', 'journal', 'printed',
                'raw_orcid', 'entity_orcid', 'key_orcid', 'indep_works', 'hard', 'support', 'desc', 'holder']
        w.writerow(['n'] + keep + ['judgment', 'note'])
        for i, r in enumerate(rows, 1):
            w.writerow([i] + [r[k] for k in keep] + ['', ''])
    print(len(rows), 'sampled')


# ---------------------------------------------------------------- the rule

WITHDRAW_A = {'date-before-window'}
HOLD_A = {'profile-orcid-differs', 'profile-orcid-other-key', 'printed-orcid-differs', 'name-family-differs',
          'name-given-differs', 'other-key-holds-title', 'date-before-span', 'profile-contaminated'}
DEMOTE_B = {'date-before-window', 'name-family-differs', 'printed-orcid-differs', 'date-before-span'}
FLAG_B = {'name-given-differs', 'other-key-holds-title', 'profile-contaminated'}
RULE_TEXT = [
    'A credit that rests on an OpenAlex author profile (route a: key-log claim minted by openalex_people_works.py; route b: '
    'linked credit author-works:openalex-author-orcid) is tested against facts the project already trusts; topic and venue '
    'never decide.',
    'Safe whatever else: the work prints the key\'s ORCID on that authorship, or the key holds the work by independent evidence.',
    'Contradictions: date-before-window (the work is older than the key\'s career window: birth + 20, else PhD - 10, reviews '
    'PhD - 9; career_window.py and the linker\'s PHD_START); printed name disagrees (link_cited_work_authors.forms / name_level as '
    'patched by link_work_people; family differs = no family word in common); an ORCID printed on the authorship that is not the '
    'key\'s; the profile\'s own ORCID is not the key\'s (or is another key\'s); a namesake key holds the same title by independent '
    'evidence; date-before-span (a key with no life or PhD years: the work is 50+ years older than the key\'s earliest '
    'independently held work; the linker\'s span fallback widened, as its 10 years flagged mostly the key\'s own early '
    'works); profile-contaminated (the same profile brings this key two or more date-contradicted works: its other '
    'unsupported works for this key are suspect).',
    'Route a: withdraw on date-before-window; hold for review on any other contradiction (date-after-death is not used: in the '
    'audit it marked posthumous items and wrong life years, never another person).',
    'Route b: demote to author_candidates on date-before-window, date-before-span, family differs, printed ORCID differs, or '
    'when the profile is tied to the key by its ORCID alone (no work of the profile is the key\'s by independent evidence: '
    'indep_works = 0); name-given-differs, title-holder and profile-contaminated credits stay credited and are listed (most '
    'name-given hits are initials, nicknames and name-order artefacts of the shared name parser; title holders are mostly '
    'duplicate keys; contaminated profiles are about half right).',
]


def decide(route, hard, support, indep):
    H = set(filter(None, (hard or '').split(';')))
    S = set(filter(None, (support or '').split(';')))
    if S & {'printed-orcid-same', 'already-independent'}:
        return 'keep', ''
    if route == 'a':
        if H & WITHDRAW_A:
            return 'withdraw', ';'.join(sorted(H & WITHDRAW_A))
        if H & HOLD_A:
            return 'hold', ';'.join(sorted(H & HOLD_A))
        return 'keep', ''
    why = sorted(H & DEMOTE_B) + (['profile-only'] if not indep else [])
    if why:
        return 'demote', ';'.join(why)
    if H & FLAG_B:
        return 'flag', ';'.join(sorted(H & FLAG_B))
    return 'keep', ''


def outputs(args):
    """rule, proposal (route a withdraws), held list, re-credit candidates, route-b unsafe table, audit sample, report"""
    import pyarrow as pa, pyarrow.parquet as pq
    S = SCRATCH
    OUT.mkdir(parents=True, exist_ok=True)
    db = duck()
    db.create_function('klass', klass, ['VARCHAR', 'VARCHAR', 'BIGINT'], 'VARCHAR')
    db.create_function('decide', lambda r, h, s, i: '|'.join(decide(r, h, s, i)), ['VARCHAR', 'VARCHAR', 'VARCHAR', 'BIGINT'], 'VARCHAR')
    db.execute(f"""CREATE TABLE t AS SELECT *, route || '/' || klass(hard, support, indep_works) AS stratum,
                   split_part(decide(route, hard, support, indep_works), '|', 1) AS decision,
                   split_part(decide(route, hard, support, indep_works), '|', 2) AS why,
                   namesake_keys >= 2 AS namesake FROM '{S}/tested.parquet'""")
    rep = collections.OrderedDict(date='2026-11-12', script='scripts/audit_openalex_profiles.py', rule=RULE_TEXT)
    claims_json = json.loads((S / 'claims.json').read_text())
    # ---- anatomy
    an = rep['anatomy'] = collections.OrderedDict()
    an['keylog_events_with_route_a_basis'] = claims_json['events_with_basis']
    an['route_a_work_mints'] = claims_json['work_mints']
    an['route_a_claims'] = claims_json['claim_mints']
    an['route_a_claims_active'] = claims_json['status'].get('active')
    an['route_a_claims_by_round'] = claims_json['rounds']
    an['route_a_claims_person_moved_by_merge'] = claims_json['person_moved']
    an['route_b_linked_credits'] = db.execute("SELECT count(*) FROM t WHERE route = 'b'").fetchone()[0]
    an['route_b_raw_orcid_credits_for_comparison'] = db.execute(
        f"SELECT count(*) FROM '{G}/authored.parquet' WHERE source = 'author-works:raw-orcid'").fetchone()[0]
    for rt in ('a', 'b'):
        an[f'route_{rt}_people'] = db.execute(f"SELECT count(DISTINCT person) FROM t WHERE route = '{rt}'").fetchone()[0]
        an[f'route_{rt}_openalex_ids'] = db.execute(f"SELECT count(DISTINCT oa_author) FROM t WHERE route = '{rt}'").fetchone()[0]
    an['people_either_route'] = db.execute("SELECT count(DISTINCT person) FROM t").fetchone()[0]
    # ids tied to keys: credits of both routes plus the tie tables of both rounds (resolved keys as of the tie run)
    ties = ' UNION '.join(f"SELECT DISTINCT author AS a, person AS p FROM '{d}/ties.parquet'" for d in ROWS.values())
    db.execute(f"CREATE TABLE tie AS SELECT DISTINCT oa_author AS a, person AS p FROM t UNION {ties}")
    an['openalex_ids_tied_to_a_key'] = db.execute("SELECT count(DISTINCT a) FROM tie").fetchone()[0]
    an['openalex_ids_tied_to_2plus_keys'] = db.execute("SELECT count(*) FROM (SELECT a FROM tie GROUP BY a HAVING count(DISTINCT p) >= 2)").fetchone()[0]
    an['openalex_ids_crediting_2plus_keys'] = db.execute(
        "SELECT count(*) FROM (SELECT oa_author FROM t GROUP BY 1 HAVING count(DISTINCT person) >= 2)").fetchone()[0]
    an['keys_with_2plus_openalex_ids'] = db.execute("SELECT count(*) FROM (SELECT p FROM tie GROUP BY p HAVING count(DISTINCT a) >= 2)").fetchone()[0]
    an['keys_crediting_from_2plus_ids'] = db.execute(
        "SELECT count(*) FROM (SELECT person FROM t GROUP BY 1 HAVING count(DISTINCT oa_author) >= 2)").fetchone()[0]
    an['credits_by_stratum'] = {f'{a}': n for a, n in db.execute("SELECT stratum, count(*) FROM t GROUP BY 1 ORDER BY 1").fetchall()}
    an['contradictions_any'] = {f'{r}/{h}': n for r, h, n in db.execute(
        "SELECT route, h, count(*) FROM (SELECT route, unnest(string_split(hard, ';')) h FROM t) WHERE h <> '' GROUP BY 1, 2 ORDER BY 1, 3 DESC").fetchall()}
    an['descriptive_signals'] = {f'{r}/{h}': n for r, h, n in db.execute(
        "SELECT route, h, count(*) FROM (SELECT route, unnest(string_split(\"desc\", ';')) h FROM t) WHERE h <> '' GROUP BY 1, 2 ORDER BY 1, 3 DESC").fetchall()}
    an['support_facts'] = {f'{r}/{h}': n for r, h, n in db.execute(
        "SELECT route, h, count(*) FROM (SELECT route, unnest(string_split(support, ';')) h FROM t) WHERE h <> '' GROUP BY 1, 2 ORDER BY 1, 3 DESC").fetchall()}
    an['independent_works_of_profile'] = {f'{r}/{k}': n for r, k, n in db.execute(
        "SELECT route, CASE WHEN indep_works >= 5 THEN '5+' ELSE CAST(indep_works AS VARCHAR) END, count(*) FROM t GROUP BY 1, 2 ORDER BY 1, 2").fetchall()}
    # ---- decisions
    rep['decisions'] = {f'{r}/{d}': n for r, d, n in db.execute("SELECT route, decision, count(*) FROM t GROUP BY 1, 2 ORDER BY 1, 2").fetchall()}
    rep['decision_reasons'] = {f'{r}/{d}/{w}': n for r, d, w, n in db.execute(
        "SELECT route, decision, why, count(*) FROM t WHERE decision <> 'keep' GROUP BY 1, 2, 3 ORDER BY 1, 2, 4 DESC").fetchall()}
    rep['decision_people'] = {f'{r}/{d}': n for r, d, n in db.execute(
        "SELECT route, decision, count(DISTINCT person) FROM t GROUP BY 1, 2 ORDER BY 1, 2").fetchall()}
    # ---- audit sample: judged credits with the decision of the final rule
    judged = []
    for tag, f in (x.split('=') for x in args.judged.split(',')):
        for r in csv.DictReader(open(f, encoding='utf-8')):
            r['draw'] = tag
            judged.append(r)
    db.execute("CREATE TABLE j(cid VARCHAR, draw VARCHAR, n INT, judgment VARCHAR, note VARCHAR)")
    db.executemany("INSERT INTO j VALUES (?, ?, ?, ?, ?)", [(r['cid'], r['draw'], int(r['n']), r['judgment'], r['note']) for r in judged])
    db.execute("""CREATE TABLE jt AS SELECT j.draw, j.n, t.route, t.stratum, t.namesake, t.decision, t.why, j.judgment, j.note,
                  t.cid, t.claim, t.person, t.label, t.work, t.oa_author, t.year, t.kind, t.title, t.journal, t.printed,
                  t.raw_orcid, t.entity_orcid, t.key_orcid, t.indep_works, t.hard, t.support, t."desc", t.holder
                  FROM j JOIN t USING (cid) ORDER BY j.draw, j.n""")
    db.execute(f"COPY jt TO '{OUT}/audit-sample.csv' (HEADER)")
    # error rates: per stratum (draw 1, uniform within strata), per cell (stratum x namesake, both draws), per decision
    def rates(group):
        out = {}
        for row in db.execute(f"""SELECT {group}, count(*), sum((judgment = 'W')::INT), sum((judgment = 'M')::INT),
                                  sum((judgment = 'U')::INT) FROM jt GROUP BY ALL ORDER BY ALL""").fetchall():
            *k, n, w, m, u = row
            out['/'.join(str(x) for x in k)] = dict(n=n, wrong=w, mixed_key=m, unclear=u)
        return out
    rep['audit'] = collections.OrderedDict(
        judged=len(judged), draws={'1': 'uniform within route x stratum', '2': 'uniform within route x stratum, namesake keys >= 2'},
        judgments='R: the key\'s person wrote it; W: another person; M: the key itself mixes people and the work is one of '
                  'theirs (defect class 9, not counted as wrong here); U: unclear from the metadata',
        by_draw_stratum=rates("draw, stratum"), by_cell=rates("stratum, namesake"), by_decision=rates("route, decision"),
        by_decision_reason=rates("route, decision, why"))
    # weighted estimates: cell rate (both draws) x cell size; a cell with no judged credit takes its stratum's rate
    est = collections.defaultdict(lambda: [0.0, 0])
    cell_rate = {(s, ns): (w, n) for s, ns, n, w in db.execute(
        "SELECT stratum, namesake, count(*), sum((judgment = 'W')::INT) FROM jt WHERE judgment <> 'U' GROUP BY 1, 2").fetchall()}
    strat_rate = {s: (w, n) for s, n, w in db.execute(
        "SELECT stratum, count(*), sum((judgment = 'W')::INT) FROM jt WHERE judgment <> 'U' GROUP BY 1").fetchall()}
    unjudged = 0
    for s, ns, d, size in db.execute("SELECT stratum, namesake, decision, count(*) FROM t GROUP BY 1, 2, 3").fetchall():
        w, n = cell_rate.get((s, ns)) or strat_rate.get(s) or (None, None)
        key = s.split('/')[0] + '/' + d
        if not n:
            unjudged += size
            est[key][1] += size
            continue
        est[key][0] += size * w / n
        est[key][1] += size
    rep['audit']['estimated_wrong'] = {k: dict(credits=v[1], est_wrong=round(v[0]), est_rate=round(v[0] / v[1], 4) if v[1] else None)
                                       for k, v in sorted(est.items())}
    rep['audit']['credits_in_cells_without_a_judgment'] = unjudged
    # ---- route a: proposal (withdraw), held list
    rows = db.execute("""SELECT claim, person, label, work, title, year, journal, why, oa_author, printed, entity_orcid, key_orcid
                         FROM t WHERE route = 'a' AND decision = 'withdraw' ORDER BY claim""").fetchall()
    ops = [dict(event='withdraw', key=c,
                basis=f"OpenAlex author {oa} credited this work to {p} ('{lab}') through a shared work (identity by works, "
                      f"scripts/openalex_people_works.py); the work ({y}) is older than the key's career window "
                      f"(birth + 20, else PhD - 10; career_window.py): another person under the same OpenAlex profile "
                      f"(scripts/audit_openalex_profiles.py, 2026-11-12)")
           for c, p, lab, w, ti, y, j, why, oa, pr, eo, ko in rows]
    (OUT / 'proposal.json').write_text(json.dumps(dict(
        basis='authored claims minted from OpenAlex author profiles (scripts/openalex_people_works.py) that a trusted date '
              'test contradicts (defect class: OpenAlex profiles trusted as identity; audit 2026-11-12)',
        decided_by='rule', ops=ops), ensure_ascii=False, indent=0) + '\n')
    db.execute(f"""COPY (SELECT claim, person, label, work, title, year, kind, journal, why AS reasons, oa_author, printed,
                        entity_orcid, key_orcid, indep_works, holder, "desc" AS signals FROM t WHERE route = 'a' AND decision = 'hold'
                        ORDER BY why, person, year) TO '{OUT}/held.csv' (HEADER)""")
    db.execute(f"""COPY (SELECT claim, person, label, work, title, year, kind, journal, why AS reasons, oa_author, printed,
                        entity_orcid, key_orcid, indep_works FROM t WHERE route = 'a' AND decision = 'withdraw'
                        ORDER BY person, year) TO '{OUT}/withdraw.csv' (HEADER)""")
    # ---- re-credit candidates: another key on the same work (the linkers' candidate list) or holding the same title
    db.execute(f"""CREATE TABLE rc AS
        SELECT t.route, t.cid, t.claim, t.work, t.title, t.year, t.printed, t.person AS current_person, t.label AS current_label,
               t.decision, t.why, c."from" AS candidate, 'author_candidates:' || coalesce(c.source, '') AS via, c.signals
        FROM t JOIN '{G}/author_candidates.parquet' c ON c."to" = t.work AND c."from" <> t.person
        WHERE t.decision IN ('withdraw', 'hold', 'demote')
        UNION ALL
        SELECT t.route, t.cid, t.claim, t.work, t.title, t.year, t.printed, t.person, t.label, t.decision, t.why,
               unnest(string_split(t.holder, ';')), 'independent-credit-same-title-or-work', ''
        FROM t WHERE t.decision IN ('withdraw', 'hold', 'demote', 'flag') AND t.holder <> ''""")
    # only candidates whose name agrees with the printed name (the candidate lists also hold the work's other authors)
    import author_works as AWM
    import link_work_people as W
    def agrees(lab, printed):
        if AWM.name_check(lab, [printed or '']) != 'family':
            return False
        pf, kf = W.L.forms(printed or ''), W.L.forms(lab or '')
        return any(W.name_level(g, g2) for f, _, g in pf for f2, _, g2 in kf if f == f2) or not pf
    q = db.execute(f"""SELECT DISTINCT rc.*, p.label AS candidate_label FROM rc JOIN '{G}/person.parquet' p ON p.key = rc.candidate
                       WHERE rc.candidate <> '' ORDER BY rc.route, rc.current_person, rc.work""")
    cols = [d[0] for d in q.description]
    rows = [r for r in q.fetchall() if agrees(r[-1], r[cols.index('printed')])]
    with open(OUT / 'recredit-candidates.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f); wr.writerow(cols); wr.writerows(rows)
    rep['recredit_candidates'] = db.execute(f"SELECT count(*), count(DISTINCT cid) FROM read_csv('{OUT}/recredit-candidates.csv')").fetchone()
    # ---- route b: derived table for the loader
    dest = ROOT / 'data/graph/author-works/unsafe-profile-credits.csv.gz'
    db.execute(f"""COPY (SELECT person, work, CAST(split_part(cid, '|', 3) AS INT) AS position, why AS reason, oa_author FROM t WHERE route = 'b' AND decision = 'demote'
                        ORDER BY person, work, position) TO '{dest}' (HEADER, COMPRESSION gzip)""")
    db.execute(f"""COPY (SELECT person, work, CAST(split_part(cid, '|', 3) AS INT) AS position, why AS reason, oa_author FROM t WHERE route = 'b' AND decision = 'flag'
                        ORDER BY person, work, position) TO '{OUT}/route-b-flagged.csv.gz' (HEADER, COMPRESSION gzip)""")
    rep['outputs'] = dict(proposal_withdraw_ops=len(ops),
                          held=db.execute("SELECT count(*) FROM t WHERE route = 'a' AND decision = 'hold'").fetchone()[0],
                          route_b_unsafe=db.execute("SELECT count(*) FROM t WHERE route = 'b' AND decision = 'demote'").fetchone()[0],
                          route_b_flagged=db.execute("SELECT count(*) FROM t WHERE route = 'b' AND decision = 'flag'").fetchone()[0])
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps({k: rep[k] for k in ('decisions', 'outputs')}, indent=1))
    print(json.dumps(rep['audit']['by_decision'], indent=1))
    print(json.dumps(rep['audit']['estimated_wrong'], indent=1))


def probes(args):
    """before/after of named keys under the rule -> SCRATCH/probes.txt"""
    db = duck()
    db.create_function('decide', lambda r, h, s, i: '|'.join(decide(r, h, s, i)), ['VARCHAR', 'VARCHAR', 'VARCHAR', 'BIGINT'], 'VARCHAR')
    keys = args.keys.split(',')
    q = ','.join(f"'{k}'" for k in keys)
    lines = []
    for k in keys:
        lab = db.execute(f"SELECT label FROM '{G}/person.parquet' WHERE key = '{k}'").fetchone()
        n_auth = db.execute(f"SELECT evidence, count(*) FROM '{G}/authored.parquet' WHERE \"from\" = '{k}' GROUP BY 1").fetchall()
        lines.append(f"\n== {k} {lab[0] if lab else ''}  AUTHORED now: {dict(n_auth)}")
        for r in db.execute(f"""SELECT route, decide(route, hard, support, indep_works) d, year, kind, title, journal, printed,
                                oa_author, indep_works, hard, support FROM '{SCRATCH}/tested.parquet' WHERE person = '{k}'
                                ORDER BY route, year""").fetchall():
            lines.append(f"  [{r[0]}] {r[1]:<38} {r[2]} {r[3]:<8} {(r[4] or '')[:70]!r} {(r[5] or '')[:30]!r} printed={r[6]!r} "
                         f"{r[7]} indep={r[8]} hard={r[9]} support={r[10]}")
        cands = db.execute(f"""SELECT c."to", w.label, w.year, c.n_candidates, c.signals FROM '{G}/author_candidates.parquet' c
                              JOIN '{G}/work.parquet' w ON w.key = c."to" WHERE c."from" = '{k}' ORDER BY w.year""").fetchall()
        lines.append(f"  candidates (unconfirmed) {len(cands)}: " + '; '.join(f"{w} {y} {(t or '')[:40]!r}" for w, t, y, n, s in cands[:12]))
    (SCRATCH / 'probes.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


PHASES = {'claims': claims, 'oarecs': oarecs, 'credits': credits, 'tests': tests, 'sample': sample, 'outputs': outputs,
          'probes': probes}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=sorted(PHASES))
    ap.add_argument('--n', type=int, default=8, help='sample: credits per stratum')
    ap.add_argument('--per', default='', help='sample: stratum=n,... overrides')
    ap.add_argument('--where', default='', help='sample: SQL filter on tested.parquet columns')
    ap.add_argument('--exclude', default='', help='sample: csv files whose cids are not drawn again')
    ap.add_argument('--tag', default='', help='sample: output name suffix')
    ap.add_argument('--judged', default='', help='outputs: draw=csv,... judged audit samples')
    ap.add_argument('--keys', default='p-21351,p-4256', help='probes: person keys')
    args = ap.parse_args()
    PHASES[args.phase](args)


if __name__ == '__main__':
    main()
