"""Scored record linkage of works to people (Fellegi-Sunter, 2026-11-12).

Owner (2026-11-12): "think about this as a linking project; if Kris Inwood can link random people in different
countries in the census, we have enough data (held and potential) to do a much better job in this more bounded
project", and "yes, move on to scored linking". The rule linker (scripts/link_work_people.py, states
exact / linked / possible / ambiguous / none) decides with yes/no facts; this script scores the same name blocks.

Unit: one printed name at one position of one work (author, JSTOR author, reviewer, name-only author) and one person
key whose name is compatible with it (the name block of link_work_people / link_cited_work_authors: family name with
particles and compound readings, first given name or initial compatible, a disagreeing printed second given name
refused by name_level_wp). Identity rules are imported from those two modules, never copied.

Hard exclusions come first and are never scored (standing rulings):
  - dates: the work outside the key's career window (link_work_people.date_filter: life years, PhD - 10, own dated
    works; reviews before PhD - 9, phd_window);
  - L.HARD proofs (a different LC authority, birth or death years apart, works before birth ...);
  - the reviewed book's own author printed as a review's author (link_work_people.own_book_check).
Then each surviving pair gets a comparison vector (FIELDS below; levels, not booleans) and a match weight, the sum of
log2(m/u) over the fields. m (P(level | match)) comes from key-log credits whose record prints a name, with the credit
hidden and every fact derived from that work hidden with it (link_work_people.HIDE, the masked-gold test); u
(P(level | non-match)) from the other candidates of the same blocks (proven or likely different people) and from
impersonated namesakes (a random person key active in the work's decade given the hidden key's name: the case of a
printed namesake who is not the keyed person). Topic, venue, citation and network fields are positive-only: no
overlap carries zero weight (owner: topic may support a link, never exclude one).

Decision (thresholds from measured error on a calibration split, never by hand):
  link     the best candidate clears the upper threshold and, with others alive, beats the runner-up by the margin;
           a single surviving candidate with no negative evidence has its own (band-specific) threshold;
  review   between the lower and the upper threshold: the clerical band, kept with the score and the top fields;
  none     below.
The estimated false-link rate mixes the measured error on held-out gold (author present) with the measured link rate
when the true author is absent (hidden key dropped; impersonated namesake), weighted by the share of absent authors
in the production positions, estimated as a mixture proportion from their score distributions.

Subcommands (scratch: SL_SCRATCH; graph snapshot: SL_GRAPH)
  prep      unify the positions (work-people, name-only, journal-metadata residue), gold flags, auxiliary tables
            (per-work keys, references, citing theses, volume people) and population counts -> scratch
  pairs     comparison vectors for the gold tests and every uncredited position, rule decisions on the same input
  fit       m/u per level, three model forms (naive, grouped context, logistic), weights -> scratch
  decide    thresholds on the calibration split, evaluation on the test split, model choice, production decisions,
            data/graph/scored-links/{links.csv.gz, weights.json, report.json}
  probes    gold publication lists of probe people against the decisions
  sample    hand-read sheets (new links the rule did not make; rule links the scorer rejects)

Reads build/graph through a snapshot, the key-log cache read-only, E: read-only. Writes no proposal, touches no key log.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import random
import re
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
S = Path(os.environ.get('SL_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                        'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/scored'))
GRAPH = Path(os.environ.get('SL_GRAPH', S / 'graph'))
os.environ.setdefault('WP_GRAPH', str(GRAPH))
os.environ.setdefault('WP_SCRATCH', str(S / 'wpscratch'))
OUT = ROOT / 'data/graph/scored-links'
NB = 24                         # work buckets for streaming
MAX_BLOCK = 40                  # candidate cap per position (reported)
GOLD_CAP = {('wp', 'author'): 50000, ('wp', 'jstor-author'): 20000, ('wp', 'reviewer'): 45000,
            ('no', 'author'): 50000}
TARGET_FDR = 0.005


def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024


def duck():
    import duckdb
    (S / 'tmp').mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='3GB'; SET threads=3; SET temp_directory='{S / 'tmp'}'; "
               "SET max_temp_directory_size='20GB'; SET enable_progress_bar=false")
    return db


def split_of(key):
    """fit (0) / calib (1, 2) / test (3) by the hidden person key, so one person never sits in two splits"""
    return int(hashlib.md5(('sl:' + key).encode()).hexdigest()[:8], 16) % 4


def _modules():
    import link_cited_work_authors as L
    import link_work_people as W
    L.GRAPH = GRAPH
    W.GRAPH = GRAPH
    return L, W


# ------------------------------------------------------------------------------------------------ prep

JM_DIR = ROOT / 'build/journal-meta-2026-11-11'


def _jm_records(want):
    """journal-metadata harvest records (Crossref, OpenAlex) of the residue DOIs -> {doi: (title, year, journal, names)}"""
    got, family_only = {}, set()
    for sub in ('crossref', 'openalex', 'oai'):
        for fn in sorted((JM_DIR / sub).glob('*')):
            op = gzip.open if fn.name.endswith('.gz') else open
            with op(fn, 'rt', encoding='utf-8') as f:
                for line in f:
                    d = json.loads(line)
                    ids = {(d.get('doi') or '').lower(), (d.get('sid') or '').lower()}
                    hit = next((x for x in ids if x in want), None)
                    if not hit:
                        continue
                    names = [a for a in d.get('authors') or [] if a and a.strip(', ')]
                    # Crossref records in this harvest often carry family names only ('Luby'): no given name, no block
                    full = [a for a in names if len(a.replace(',', ' ').split()) >= 2]
                    if not full:
                        if names:
                            family_only.add(hit)
                        continue
                    if hit not in got or len(full) > len(got[hit][3]):
                        got[hit] = (d.get('title') or '', d.get('year'), d.get('journal') or '', full, [''] * len(full))
    return got, family_only


def prep(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    L, W = _modules()
    from graph_tables import keylog
    t0 = time.time()
    db = duck()
    G = GRAPH
    files = [(S / 'wp/positions.parquet', 'wp'), (S / 'wp/positions-title.parquet', 'wp'),
             (S / 'wp/positions-crossref.parquet', 'wp'), (S / 'no/positions.parquet', 'no')]
    union = ' UNION ALL '.join(f"SELECT '{t}' tbl, * FROM '{f}'" for f, t in files)
    db.execute(f"CREATE TABLE pos0 AS {union}")
    n, nd = db.execute("SELECT count(*), count(DISTINCT pid) FROM pos0").fetchone()
    assert n == nd, (n, nd)
    # residue of the cited works whose matchers add authors nobody read: journal-metadata records (Luby probe class)
    res = db.execute(f"""SELECT w.id, w.source, w.title, w.year, w.kind FROM read_csv('{ROOT / 'data/graph/cited-works/works.csv.gz'}',
            all_varchar=true) w WHERE w.source IN ('crossref-meta', 'crossref', 'journal-meta', 'lc-translations')
            AND w.id NOT IN (SELECT DISTINCT work FROM pos0)""").fetchall()
    by_src = Counter(r[1] for r in res)
    want = {r[0][4:].lower() for r in res if r[0].startswith('doi:')} | {r[0].lower() for r in res}
    jm, family_only = _jm_records(want)
    rows = []
    pid = 20_000_000
    for wid, src, title, year, kind in res:
        rec = jm.get(wid[4:].lower()) or jm.get(wid.lower())
        if not rec:
            continue
        rt, ry, rj, names, orcids = rec
        for i, (nm, oc) in enumerate(zip(names, orcids)):
            rows.append(dict(tbl='jm', role='author', source='journal-meta-' + src, work=wid, pos=i, n_auth=len(names),
                             name=nm, year=int(year) if year and str(year).isdigit() else ry, journal=rj, kind=kind or 'article',
                             title=title or rt, orcid=oc or '', oa_author='', rors=[], insts=[], raw_aff=[], oa_work='',
                             inst_printed='', inst_ror='', inst_ror_name='', sig_conf=0.0, credited='', credited_how='', pid=pid))
            pid += 1
    residue = dict(works_by_source=dict(by_src), works_with_a_record=len({r['work'] for r in rows}), positions=len(rows),
                   works_family_names_only=len(family_only),
                   note='journal-metadata harvest only (build/journal-meta-2026-11-11); the Crossref metadata harvest on E: '
                        'was read by link_work_people nameonly-extract, so its residue has no record there; lc-translations '
                        'have no printed-name source here')
    print('residue', residue, round(time.time() - t0), flush=True)
    if rows:
        tj = pa.Table.from_pylist(rows, schema=db.execute("SELECT * FROM pos0 LIMIT 0").arrow().schema)
        db.register('tj', tj)
        db.execute("INSERT INTO pos0 SELECT * FROM tj")
    db.execute(f"""CREATE TABLE pos AS SELECT p.*, coalesce(nullif(w.journal, ''), nullif(p.journal, '')) AS wjournal,
                   w.resolution AS wres, hash(p.work) % {NB} AS b
                   FROM pos0 p LEFT JOIN (SELECT key, journal, resolution FROM '{G}/work.parquet') w ON w.key = p.work""")
    db.execute("DROP TABLE pos0")
    # gold: credited positions; route-a (OpenAlex-profile) credits flagged; a sample per (table, role)
    ca = S / 'claims_a.parquet'
    db.execute(f"""CREATE TABLE goldpairs AS SELECT DISTINCT credited k, work w FROM pos WHERE credited <> ''""")
    db.execute(f"""CREATE TABLE gclaims AS SELECT g.k, g.w, count(a.claim) n, count(c.claim) na
                   FROM goldpairs g JOIN {keylog(G, 'authored')} a ON a."from" = g.k AND a."to" = g.w
                   LEFT JOIN (SELECT DISTINCT claim FROM '{ca}') c ON c.claim = a.claim GROUP BY 1, 2""")
    caps = ' OR '.join(f"(tbl = '{t}' AND role = '{r}' AND rn <= {n})" for (t, r), n in GOLD_CAP.items())
    db.execute(f"""CREATE TABLE pos2 AS SELECT p.*, coalesce(gc.na > 0 AND gc.na = gc.n, false) AS route_a,
                   coalesce(gc.n, 0) AS keylog_claims,
                   p.credited <> '' AND ({caps}) AS gold_sel
                   FROM (SELECT *, row_number() OVER (PARTITION BY tbl, role, credited <> '' ORDER BY hash(pid::VARCHAR || 'g')) rn FROM pos) p
                   LEFT JOIN gclaims gc ON gc.k = p.credited AND gc.w = p.work""")
    db.execute(f"COPY (SELECT * EXCLUDE (rn) FROM pos2 ORDER BY b, work, pos) TO '{S / 'positions.parquet'}' (FORMAT parquet)")
    st = db.execute("SELECT tbl, role, count(*), sum((credited <> '')::int), sum(gold_sel::int), sum((gold_sel AND route_a)::int) "
                    "FROM pos2 GROUP BY ALL ORDER BY 1, 2").fetchall()
    print(st, round(time.time() - t0), flush=True)
    db.execute("DROP TABLE pos; DROP TABLE goldpairs; DROP TABLE gclaims")
    db.execute(f"CREATE TABLE pw AS SELECT DISTINCT work, oa_work, b FROM '{S / 'positions.parquet'}'")
    # per-work tables (all bucketed by the same hash)
    db.execute(f"""COPY (SELECT DISTINCT a."to" AS work, a."from" AS key, hash(a."to") % {NB} AS b FROM {keylog(G, 'authored')} a
                   WHERE a."to" IN (SELECT work FROM pw)
                   UNION SELECT DISTINCT work, key, hash(work) % {NB} AS b FROM '{S / 'no/credited-extra.parquet'}' WHERE work <> '')
                   TO '{S / 'aux-wauth.parquet'}' (FORMAT parquet)""")
    db.execute(f"""COPY (SELECT DISTINCT c."from" AS work, a."from" AS key, hash(c."from") % {NB} AS b FROM '{G}/cites.parquet' c
                   JOIN {keylog(G, 'authored')} a ON a."to" = c."to"
                   WHERE (c.source LIKE '%jstor%' OR c.source LIKE '%crossref%') AND c."from" IN (SELECT work FROM pw))
                   TO '{S / 'aux-ref1.parquet'}' (FORMAT parquet)""")
    # OpenAlex references of the positions' records -> graph works -> their key-log authors
    oa_rows = '/mnt/e/openalex-people-2026-11-09/rows/*.parquet'
    ow_l, r_l = [], []
    for fn in (S / 'wp/oa-refs.jsonl', S / 'no/oa-refs.jsonl'):
        for line in open(fn, encoding='utf-8'):
            ow, rs = json.loads(line)
            ow_l.extend([ow] * len(rs))
            r_l.extend(rs)
    pq.write_table(pa.table({'ow': ow_l, 'r': r_l}), S / 'tmp-oarefs.parquet')
    del ow_l, r_l
    db.execute(f"CREATE TABLE oar AS SELECT DISTINCT ow, r FROM '{S / 'tmp-oarefs.parquet'}' WHERE ow IN (SELECT oa_work FROM pw)")
    db.execute(f"""CREATE TABLE oag AS SELECT DISTINCT work, graph_work FROM read_parquet('{oa_rows}', union_by_name=true)
                   WHERE graph_work <> '' AND work IN (SELECT r FROM oar)""")
    db.execute(f"""COPY (SELECT DISTINCT pw.work, a."from" AS key, pw.b FROM oar JOIN pw ON pw.oa_work = oar.ow
                   JOIN oag ON oag.work = oar.r JOIN {keylog(G, 'authored')} a ON a."to" = oag.graph_work)
                   TO '{S / 'aux-ref2.parquet'}' (FORMAT parquet)""")
    db.execute("DROP TABLE oar; DROP TABLE oag")
    db.execute(f"""COPY (SELECT DISTINCT c."to" AS work, replace(a, 'diss-thesis:', '') AS d, hash(c."to") % {NB} AS b
                   FROM '{G}/cites.parquet' c JOIN (SELECT key, unnest(anchors) a FROM '{G}/work.parquet' WHERE kind = 'thesis') t
                   ON t.key = c."from" WHERE a LIKE 'diss-thesis:%' AND c."to" IN (SELECT work FROM pw))
                   TO '{S / 'aux-citers.parquet'}' (FORMAT parquet)""")
    db.execute(f"""COPY (SELECT r."from" AS work, a."from" AS key, hash(r."from") % {NB} AS b FROM '{G}/reviews.parquet' r
                   JOIN {keylog(G, 'authored')} a ON a."to" = r."to" WHERE r."from" IN (SELECT work FROM pw)
                   UNION SELECT r."from", e."from", hash(r."from") % {NB} FROM '{G}/reviews.parquet' r
                   JOIN {keylog(G, 'edited')} e ON e."to" = r."to" WHERE r."from" IN (SELECT work FROM pw))
                   TO '{S / 'aux-revauth.parquet'}' (FORMAT parquet)""")
    db.execute(f"""COPY (SELECT DISTINCT work, key, how, hash(work) % {NB} AS b FROM read_parquet(['{S / 'no/volume-people.parquet'}',
                   '{S / 'wp/volume-people.parquet'}'])
                   WHERE work IN (SELECT work FROM pw) AND key <> '')
                   TO '{S / 'aux-vp.parquet'}' (FORMAT parquet)""")
    print('aux tables', round(time.time() - t0), rss(), 'MB', flush=True)
    # records outside the History population (their names' rarity is not measured there)
    outside = set()
    for d in (Path(str(S).replace('/scored', '/workpeople')), Path(str(S).replace('/scored', '/nameonly'))):
        for sub in ('oa', 'oa-title'):
            for fn in (d / sub).glob('doi-lookup-*.jsonl'):
                for line in open(fn, encoding='utf-8'):
                    outside.add(line[10:40].split('"')[0])
    pq.write_table(pa.table({'oa_work': sorted(outside)}), S / 'aux-outside.parquet')
    # population counts of the printed names and the keys' names
    needed = set()
    for (nm,) in db.execute(f"SELECT DISTINCT name FROM '{S / 'positions.parquet'}'").fetchall():
        for f, _, g in L.forms(W.apos(nm))[:1]:
            needed.add((f, g[0]))
    for (lab,) in db.execute(f"SELECT label FROM '{G}/person.parquet'").fetchall():
        for f, _, g in L.forms(W.apos(lab or '')):
            needed.add((f, g[0]))
    pop = L.population_counts(db, needed)
    del needed
    out = []
    for i, c in enumerate(pop):
        for k, v in c.items():
            out.append((i, k[0], k[1], k[2] if len(k) > 2 else '', v))
    pq.write_table(pa.table({'t': [x[0] for x in out], 'f': [x[1] for x in out], 'g0': [x[2] for x in out],
                             'g1': [x[3] for x in out], 'n': [x[4] for x in out]}), S / 'aux-pop.parquet')
    json.dump(dict(stats=[list(x) for x in st], residue=residue, outside=len(outside), pop_rows=len(out),
                   graph=str(GRAPH), graph_built=time.ctime((GRAPH / 'person.parquet').stat().st_mtime)),
              open(S / 'prep.json', 'w'), indent=1, default=str)
    print('prep done', round(time.time() - t0), rss(), 'MB', flush=True)


# ------------------------------------------------------------------------------------------------ comparison fields

FIELDS = ('name', 'freq', 'date', 'aff', 'network', 'venue', 'topic', 'cites', 'neg')
POSITIVE_ONLY = {'network': 'none', 'venue': 'none', 'topic': 'none', 'cites': 'none', 'oa_tie': 'none'}
CONTEXT = ('network', 'venue', 'topic', 'cites')
NEGATIVE_ONLY = {'neg': 'none'}   # negative evidence that is not proof: never a reason to link (its 'none' level carries 0)
NET_FACTS = ('coauthor', 'coauthor-network', 'coauthor-colleague', 'volume-network', 'volume-editor')


def name_level(c):
    """printed-name specificity against the key's name: the base level of name_level plus the second given name"""
    lev, g, kg = c['lev'], c['g'], c['kg']
    mid = 'na'
    if len(g) >= 2 and len(kg) >= 2:
        a, b = g[1], kg[1]
        mid = 'full' if (len(a) > 1 and a == b) else 'init' if a[0] == b[0] else 'other'
    if lev == 'full':
        return 'full+mid' if mid == 'full' else 'full+init' if mid == 'init' else 'full'
    if lev == 'initial':
        return 'initials2' if mid in ('full', 'init') else 'initial'
    return lev            # variant, surname-variant


def freq_band(bearers):
    return 'unique' if bearers <= 1 else '2-5' if bearers <= 5 else '6-25' if bearers <= 25 else '26+'


def topic_band(sc):
    return 'none' if sc <= 0 else 'low' if sc < 8 else 'mid' if sc < 15 else 'high' if sc < 30 else 'vhigh'


def date_level(ok, how, year, phd):
    if not ok:
        return 'undated'
    if phd and year:
        d = year - phd
        return 'pre-phd' if d < -2 else 'phd0-10' if d <= 10 else 'phd10-25' if d <= 25 else 'phd25+'
    return how if how in ('life', 'death', 'span') else 'weak'


def score_of(lv, weights, model):
    """match weight of one comparison vector (dict field -> level) under a model of weights.json"""
    w = weights[model]
    if model == 'logistic':
        s = w['intercept']
        for f, l in lv.items():
            s += w['coef'].get(f'{f}={l}', 0.0)
        return s
    s = 0.0
    for f in w['fields']:
        if f == 'context':
            s += w['w']['context'].get('|'.join(lv[x] for x in CONTEXT), 0.0)
        else:
            s += w['w'][f].get(lv[f], 0.0)
    return s


# ------------------------------------------------------------------------------------------------ pairs

class Ctx:
    """per-run lookups the comparison needs beyond link_cited_work_authors.People"""
    def __init__(self, db, people, W, L):
        from key_review_reviewers import journal_key
        from graph_tables import keylog
        from key_review_credit_merges import is_system
        G = GRAPH
        self.journal_key = journal_key
        t0 = time.time()
        # journals of each key's key-log works, as counts per work (the hidden work is subtracted in the gold test)
        self.jw = defaultdict(Counter)
        self.work_j = {}
        for k, w, j in db.execute(f"""SELECT DISTINCT a."from", a."to", w.journal FROM (SELECT "from", "to" FROM {keylog(G, 'authored')}
                UNION SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to"
                WHERE w.journal IS NOT NULL AND w.journal <> ''""").fetchall():
            jk = journal_key(j)
            if jk:
                self.jw[k][jk] += 1
        people.journals = {}            # not read for these positions (make_pos sets no venue); frees memory
        # every ROR of each key's affiliations, any date (circular sources out: review credits, review signatures)
        self.rors_any = defaultdict(set)
        for k, ror, lab in db.execute(f"""SELECT a."from", i.ror, i.label FROM '{G}/affiliated_with.parquet' a
                JOIN '{G}/institution.parquet' i ON i.key = a."to" WHERE i.ror IS NOT NULL
                AND a.source NOT IN ('review_credit', 'jstor_signature')""").fetchall():
            if not is_system(lab or ''):
                self.rors_any[k].add(ror.rsplit('/', 1)[-1])
        self.coed, self.adv = set(), set()
        for a, b in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'coedited')}").fetchall():
            self.coed.update(((a, b), (b, a)))
        for a, b in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'advised')}").fetchall():
            self.adv.update(((a, b), (b, a)))
        # keys active in each decade (impersonated namesakes)
        self.decade = defaultdict(list)
        for k, sp in people.span.orig.items():
            lo, hi, n = sp
            if n >= 2 and hi - lo <= 70:
                for d in range(lo // 10, hi // 10 + 1):
                    self.decade[d].append(k)
        # book titles of each key (own-book check), PhD country
        self.book_titles = defaultdict(set)
        for k, t in db.execute(f"""SELECT a."from", w.label FROM (SELECT "from", "to" FROM {keylog(G, 'authored')} UNION
                SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'book'""").fetchall():
            tn = W.tnorm(t)
            if tn:
                self.book_titles[tn].add(k)
        self.country = {}
        dc = dict(db.execute(f"""SELECT id, country FROM read_csv('{ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'}',
                all_varchar=true)""").fetchall())
        for k, d in db.execute(f"""SELECT a."from", replace(x, 'diss-thesis:', '') FROM {keylog(G, 'authored')} a JOIN
                (SELECT key, unnest(anchors) x FROM '{G}/work.parquet' WHERE kind = 'thesis') t ON t.key = a."to"
                WHERE x LIKE 'diss-thesis:%'""").fetchall():
            if dc.get(d):
                self.country[k] = dc[d]
        for k, an in people.aha.items():
            if an and k not in self.country:
                self.country[k] = 'AHA(US/CA)'
        self.outside = {x for (x,) in db.execute(f"SELECT oa_work FROM '{S / 'aux-outside.parquet'}'").fetchall()}
        oa = defaultdict(int)
        # OpenAlex author ids the 2026-11-12 profile audit found contradicted (merged profiles): ties through them unused
        self.bad_oa = {a for (a,) in db.execute(f"""SELECT DISTINCT oa_author FROM '{S / 'tested.parquet'}'
                WHERE coalesce(hard, '') <> '' OR coalesce("desc", '') LIKE '%contaminated%' OR coalesce(hard, '') LIKE '%contaminated%'
                   OR profile_keys > 1""").fetchall()}
        print('ctx', round(time.time() - t0), rss(), 'MB', flush=True)


def load_pop(db):
    pop = tuple(Counter() for _ in range(6))
    for t, f, g0, g1, n in db.execute(f"SELECT t, f, g0, g1, n FROM '{S / 'aux-pop.parquet'}'").fetchall():
        pop[t][(f, g0, g1) if t >= 2 else (f, g0)] = n
    return pop


def bearers(fe, c, pop, live, L):
    """people in the wider population bearing the printed name: LC authorities besides those the live candidates hold
    (and the source's own), OpenAlex History author ids; the first two given names when both are written and agree"""
    own = L.own_lc(fe, live)
    g, kg, f = c['g'], c['kg'], c['fam']
    if c['lev'] == 'full' and len(g) >= 2 and len(kg) >= 2 and len(g[1]) > 1 and g[1] == kg[1]:
        n_lc = pop[2].get((f, g[0], g[1]), 0) + pop[2].get((f, g[0], g[1][0]), 0)
        n_oa = pop[3].get((f, g[0], g[1]), 0) + pop[3].get((f, g[0], g[1][0]), 0)
    else:
        n_lc, n_oa = pop[0].get(fe['name_key'], 0), pop[1].get(fe['name_key'], 0)
    return max(max(0, n_lc - own) + 1, n_oa), max(0, n_lc - own), n_oa


def compare(people, ctx, L, W, p, r, k, c, fe, live, pop, P, ex, vp, ved, topics, hidden):
    """comparison vector of one (position, candidate key) pair -> dict of levels and raw values"""
    year = p['year']
    hw, hk = hidden if hidden else (None, None)
    # name and its frequency
    nl = name_level(c)
    if all(len(x) == 1 for x in c['g']):
        band, nb, nlc, noa = 'initials', None, None, None
    else:
        nb, nlc, noa = bearers(fe, c, pop, live, L)
        band = freq_band(nb)
        if r['oa_work'] in ctx.outside and p['role'] == 'author' and not W.REVIEWISH.search(p['title'] or ''):
            band = 'unmeasured'
    # date
    ok, how = L.date_test(c, year, p['book'], P)
    dl = date_level(ok, how, year, people.phd.get(k))
    # affiliation
    facts = c['facts']
    fk = {f.split(':')[0] for f in facts}
    rors = set(p['rors'])
    printed_aff = bool(rors or p.get('raw_aff') or p.get('insts'))
    if fk & {'inst', 'inst-name'}:
        aff = 'same-window'
    elif rors and rors & ctx.rors_any.get(k, set()):
        aff = 'same-any'
    elif printed_aff and year and any((fy or ly) - L.SLACK <= year <= (ly or fy) + L.SLACK for _, _, fy, ly in people.aff.get(k, ())):
        aff = 'different'
    else:
        aff = 'absent'
    # network: known co-authors (key log) among the work's credited people, and the name-only facts
    nco = sum(1 for k2 in ex if k2 != k and (k, k2) in people.coauth)
    other = {f for f in fk if f in NET_FACTS and f != 'coauthor'}
    strength = nco + len(other)
    net = 'none' if strength == 0 else 'multi' if strength >= 2 else 'coauthor1' if nco == 1 else 'network1'
    # venue: the candidate's other key-log works in the same journal
    jk = ctx.journal_key(r['wjournal']) if r['wjournal'] and not L.REPOSITORY.search(r['wjournal']) else ''
    if not jk:
        venue = 'na'
    else:
        n = ctx.jw.get(k, {}).get(jk, 0)
        if hk == k and hw and r['wjournal']:
            n -= 1               # the hidden work itself is in that journal
        venue = 'j3+' if n >= 3 else 'j1-2' if n >= 1 else 'none'
    # topic (owner: supports only): rarity-weighted shared title words with the key's key-log works and thesis
    sc, shared = topics.score(k, p['title'], p['title'] if hk == k else None)
    tb = topic_band(sc)
    cites = 'cites' if fk & {'selfcite', 'own-thesis-cites', 'student-thesis-cites'} else 'none'
    # negative evidence that is not proof
    why = set(c['why'])
    neg = 'orcid-differs' if 'orcid-differs' in why else 'pooled' if 'pooled' in why else \
        'inconsistent' if 'inconsistent-dates' in why else 'own-title' if c.get('own_title') else 'none'
    oat = 'tie' if 'oa-author-tie' in fk and p['oa_author'] and p['oa_author'] not in ctx.bad_oa else 'none'
    return dict(name=nl, freq=band, date=dl, aff=aff, network=net, venue=venue, topic=tb, cites=cites, neg=neg,
                oa_tie=oat, topic_sc=round(sc, 2), bearers=nb, lc_others=nlc, oa_n=noa, nco=nco,
                facts=' '.join(sorted(set(facts))))


def add_name_only_facts(people, ctx, p, fe, ex, vp, ved, topics, hidden, with_topic_fact):
    """the facts link_work_people.nameonly_features adds (coauthor-network, coauthor-colleague, volume-network,
    volume-editor; topic for the name-only rule run), here from per-bucket volume people (memory), same definitions"""
    import link_cited_work_authors as L
    w = p['work_id']
    hw, hk = hidden if hidden else (None, None)
    for k, c in fe['cands'].items():
        if with_topic_fact and c.get('lev') in ('full', 'variant'):
            sc, _ = topics.score(k, p['title'], p['title'] if hk == k else None)
            if sc >= 20:
                c['facts'].append(f'topic:{sc:.1f}')
        for k2 in ex:
            if k2 != k and ((k, k2) in ctx.coed or (k, k2) in ctx.adv):
                c['facts'].append(f'coauthor-network:{k2}')
                break
        y = p['year']
        if y and ex:
            mine = [(ror, fy, ly) for ror, _, fy, ly in people.aff.get(k, ()) if (fy or ly) - L.SLACK <= y <= (ly or fy) + L.SLACK]
            if mine:
                rs = {ror for ror, _, _ in mine}
                for k2 in ex:
                    if k2 != k and any(ror in rs and (fy or ly) - L.SLACK <= y <= (ly or fy) + L.SLACK
                                       for ror, _, fy, ly in people.aff.get(k2, ())):
                        c['facts'].append(f'coauthor-colleague:{k2}')
                        break
        for k2 in vp.get(w, ()):
            if k2 != k and not (hw == w and hk == k2) and (
                    (k, k2) in people.coauth or (k, k2) in ctx.coed or (k, k2) in ctx.adv):
                c['facts'].append(f'volume-network:{k2}')
                break
        if k in ved.get(w, ()):
            c['facts'].append('volume-editor')


def rule_params(L, W, tbl):
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'] = tuple(P['FACTS']) + W.FACTS_NAMEONLY + (('topic',) if tbl == 'no' else ())
    P['XDATE'] = tuple(P['XDATE'])
    P['ONE_NETWORK_FACT'] = True
    L.PARAMS.update({k: v for k, v in P.items() if k in L.PARAMS})
    return P


def judge(people, L, k, g):
    """a link to k when g is the credited key: 'dup' when the two keys' names agree word for word (initials may stand
    for names) and no identifier or not-same mark separates them, else 'wrong'"""
    fk, fg = L.forms(people.label.get(k, '')), L.forms(people.label.get(g, ''))
    if not fk or not fg or fk[0][0] != fg[0][0]:
        return 'wrong'
    a, b = fk[0][2], fg[0][2]
    sh, lo = (a, b) if len(a) <= len(b) else (b, a)
    if any(not (x == y or (len(x) == 1 and y.startswith(x)) or (len(y) == 1 and x.startswith(y))) for x, y in zip(sh, lo)):
        return 'wrong'
    for d in (people.lcnaf, people.orcid):
        if d.get(k) and d.get(g) and not d[k] & d[g]:
            return 'wrong'
    if g in people.not_same.get(k, ()):
        return 'wrong'
    pa_, pb = people.phd.get(k), people.phd.get(g)
    if pa_ and pb and abs(pa_ - pb) > 1:
        return 'wrong'
    return 'dup'


def pairs(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    L, W = _modules()
    t0 = time.time()
    db = duck()
    people = W.WPPeople(db)
    print('people', round(time.time() - t0), rss(), 'MB', flush=True)
    ctx = Ctx(db, people, W, L)
    topics = W.Topics(db, people)
    pop = load_pop(db)
    print('ready', round(time.time() - t0), rss(), 'MB', flush=True)
    Ps = {t: rule_params(L, W, t) for t in ('wp', 'no', 'jm')}
    P = Ps['wp']
    rnd = random.Random(1112)
    out_dir = S / 'pairs'
    out_dir.mkdir(exist_ok=True)
    buckets = [int(x) for x in args.buckets.split(',')] if args.buckets else range(NB)
    for b in buckets:
        if (out_dir / f'cand-{b:02d}.parquet').exists() and not args.force:
            continue
        tb = time.time()
        T = db.execute(f"SELECT * FROM '{S / 'positions.parquet'}' WHERE b = {b}" + (f" AND hash(pid) % {args.sample} = 0" if args.sample else '')).fetch_arrow_table()
        wauth = defaultdict(set)
        for w, k in db.execute(f"SELECT work, key FROM '{S / 'aux-wauth.parquet'}' WHERE b = {b}").fetchall():
            wauth[w].add(k)
        refk = defaultdict(set)
        for w, k in db.execute(f"SELECT work, key FROM read_parquet(['{S / 'aux-ref1.parquet'}', '{S / 'aux-ref2.parquet'}']) WHERE b = {b}").fetchall():
            refk[w].add(k)
        citers = defaultdict(set)
        for w, d in db.execute(f"SELECT work, d FROM '{S / 'aux-citers.parquet'}' WHERE b = {b}").fetchall():
            citers[w].add(d)
        revauth = defaultdict(set)
        for w, k in db.execute(f"SELECT work, key FROM '{S / 'aux-revauth.parquet'}' WHERE b = {b}").fetchall():
            revauth[w].add(k)
        vp, ved = defaultdict(set), defaultdict(set)
        for w, k, how in db.execute(f"SELECT work, key, how FROM '{S / 'aux-vp.parquet'}' WHERE b = {b}").fetchall():
            vp[w].add(k)
            if how == 'volume-editor':
                ved[w].add(k)
        rows = T.to_pylist()
        del T
        # pass 1: identifier (ORCID) exacts on each work, for the co-author facts
        exact_of = defaultdict(set)
        for r in rows:
            if r['credited'] == '' and r['orcid'] and people.orcid_key.get(r['orcid']):
                fe = L.features(people, W.make_pos(r))
                if fe.get('exact'):
                    exact_of[r['work']].update(fe['exact'])
        cand_rows, pos_rows = [], []

        def run(r, p, mode, mask, ex, hidden, g=None, imp=None):
            """features, rule decision and comparison vectors for one variant of one position"""
            W.HIDE[0] = hidden
            fe = L.features(people, p, mask=mask, exacts=ex, refkeys=refk.get(r['work']), citers_of=citers)
            if not fe.get('exact'):
                add_name_only_facts(people, ctx, p, fe, ex, vp, ved, topics, hidden, r['tbl'] == 'no')
            Pt = Ps[r['tbl']]
            st, rk, br, rc, sig = W.rule_wp(people, p, fe, pop, Pt)
            st, rk, br, sig = W.guard(r, st, rk, br, sig, fe, Pt, ctx.book_titles, revauth, ctx.outside)
            res = dict(pid=r['pid'], mode=mode, rule_state=st, rule_key=rk or '', rule_branch=br, rule_drop_state=None,
                       rule_drop_key=None, rule_drop_branch=None, gold=None, split=None, imp_key=None)
            if mode == 'present':
                fd = dict(fe, cands={k: c for k, c in fe['cands'].items() if k != g})
                st2, rk2, br2, _, sig2 = W.rule_wp(people, p, fd, pop, Pt)
                st2, rk2, br2, _ = W.guard(r, st2, rk2, br2, sig2, fd, Pt, ctx.book_titles, revauth, ctx.outside)
                res.update(rule_drop_state=st2, rule_drop_key=rk2 or '', rule_drop_branch=br2)
            if fe.get('exact'):
                res.update(exact='|'.join(fe['exact']), n_live=0, n_date_out=0, n_hard=0, capped=False, g_status='')
                W.HIDE[0] = None
                return res
            fe2 = W.phd_window(people, p, fe)
            fe2, gone = W.date_filter(p, fe2, Pt)
            hard = {k for k, c in fe2['cands'].items() if set(c['why']) & L.HARD}
            live = {}
            for k, c in fe2['cands'].items():
                if k in hard:
                    continue
                ob = W.own_book_check(r, k, ctx.book_titles, revauth)
                if ob and ob[0] == 'none':
                    hard.add(k)
                    continue
                if ob:
                    c = dict(c, own_title=True)
                live[k] = c
            gs = ''
            if g:
                gs = 'live' if g in live else 'date-excluded' if g in gone else 'hard' if g in hard else 'not-in-block'
            res.update(exact='', n_live=len(live), n_date_out=len(gone), n_hard=len(hard), capped=len(live) > MAX_BLOCK,
                       g_status=gs)
            if len(live) > MAX_BLOCK:
                W.HIDE[0] = None
                return res
            lk = list(live)
            for k, c in live.items():
                lv = compare(people, ctx, L, W, p, r, k, c, fe2, lk, pop, Pt, ex, vp, ved, topics, hidden)
                lab = -1
                if g:
                    lab = 1 if k == g else (2 if judge(people, L, k, g) == 'dup' else 0)
                if imp:
                    lab = 0
                cand_rows.append(dict(pid=r['pid'], mode=mode, key=k, label=lab, **lv))
            W.HIDE[0] = None
            return res

        for r in rows:
            p = W.make_pos(r)
            p['book'] = False
            if r['credited'] == '':
                ex = wauth.get(r['work'], set()) | exact_of.get(r['work'], set())
                pos_rows.append(run(r, p, 'prod', None, ex, None))
                continue
            if not r['gold_sel']:
                continue
            g = r['credited']
            by_orcid = r['credited_how'] == 'orcid'
            mask = dict(key=g, orcid={r['orcid']} if by_orcid else set(), src_orcid=not by_orcid)
            ex = (wauth.get(r['work'], set()) | exact_of.get(r['work'], set())) - {g}
            res = run(r, p, 'present', mask, ex, (r['work'], g), g=g)
            res.update(gold=g, split=split_of(g))
            pos_rows.append(res)
            # impersonated namesake: a person key active in the work's decade bears the hidden key's name
            if r['year'] and p['forms']:
                ent = next(((f, kf, kg) for f, _, _ in p['forms'] for (k, kf, kg) in people.index.get(f, ()) if k == g), None)
                pool = ctx.decade.get(r['year'] // 10, ())
                if ent and pool:
                    for _ in range(5):
                        ki = pool[rnd.randrange(len(pool))]
                        if ki != g and ki not in ex and people.label.get(ki):
                            break
                    else:
                        ki = None
                    if ki:
                        saved = people.index
                        people.index = {ent[0]: [(ki, ent[1], ent[2])]}
                        try:
                            res2 = run(r, p, 'imp', dict(mask, drop={g}), ex, None, imp=ki)
                        finally:
                            people.index = saved
                        res2.update(gold=g, split=split_of(g), imp_key=ki)
                        pos_rows.append(res2)
        pq.write_table(pa.Table.from_pylist(pos_rows), out_dir / f'pos-{b:02d}.parquet')
        pq.write_table(pa.Table.from_pylist(cand_rows), out_dir / f'cand-{b:02d}.parquet')
        print(f'bucket {b}: {len(rows)} rows, {len(pos_rows)} position variants, {len(cand_rows)} pairs, '
              f'{round(time.time() - tb)} s, {rss()} MB', flush=True)
        del rows, cand_rows, pos_rows, wauth, refk, citers, revauth, vp, ved, exact_of


# ------------------------------------------------------------------------------------------------ fit

NAME_FIELDS = ('name', 'freq')   # u from same-block non-matches only: an impersonated namesake bears the printed name by construction
BANDS = ('unique', '2-5', '6-25', '26+', 'initials', 'unmeasured')
STR_COLS = ('mode', 'key') + FIELDS + ('oa_tie',)


def read_pairs(where, cols=None):
    """candidate pairs as a pandas frame with categorical string columns (memory)"""
    import pyarrow.compute as pc
    cols = cols or ['pid', 'mode', 'key', 'label'] + list(FIELDS) + ['oa_tie']
    db = duck()
    t = db.execute(f"SELECT {', '.join(cols)} FROM read_parquet('{S / 'pairs'}/cand-*.parquet') WHERE {where}").to_arrow_table()
    for i, n in enumerate(t.schema.names):
        if n in STR_COLS:
            t = t.set_column(i, n, pc.dictionary_encode(t.column(n).combine_chunks()))
    return t.to_pandas()


def read_pos(where):
    db = duck()
    return db.execute(f"SELECT * FROM read_parquet('{S / 'pairs'}/pos-*.parquet', union_by_name=true) WHERE {where}").df()


def mu_table(pos, neg, f, alpha=1.0):
    levels = sorted(set(pos[f].astype(str)) | set(neg[f].astype(str)))
    mc, uc = pos[f].astype(str).value_counts(), neg[f].astype(str).value_counts()
    w, tab = {}, {}
    for lv in levels:
        m = (mc.get(lv, 0) + alpha) / (len(pos) + alpha * len(levels))
        u = (uc.get(lv, 0) + alpha) / (len(neg) + alpha * len(levels))
        x = math.log2(m / u)
        if f in POSITIVE_ONLY:
            x = 0.0 if lv in (POSITIVE_ONLY[f], 'na') else max(0.0, x)
        if f in NEGATIVE_ONLY:
            x = 0.0 if lv == NEGATIVE_ONLY[f] else min(0.0, x)
        w[lv] = round(x, 3)
        tab[lv] = dict(m=round(m, 5), u=round(u, 5), n_match=int(mc.get(lv, 0)), n_nonmatch=int(uc.get(lv, 0)), weight=round(x, 3))
    return w, tab


def fit_weights(df, grouped=False, extra=(), alpha=1.0):
    """Fellegi-Sunter weights log2(m/u) per level (Laplace smoothing); positive-only fields clamped at 0 with their
    absence level at 0; grouped: one joint field for network x venue x topic x cites (their dependence)"""
    pos = df[df.label == 1]
    neg_all = df[df.label == 0]
    neg_blk = df[(df.label == 0) & (df['mode'].astype(str) == 'present')]
    use = [f for f in FIELDS if not (grouped and f in CONTEXT)] + list(extra)
    out, tables = {}, {}
    for f in use:
        out[f], tables[f] = mu_table(pos, neg_blk if f in NAME_FIELDS else neg_all, f, alpha)
    if grouped:
        kp = pos.groupby(list(CONTEXT), observed=True).size()
        kn = neg_all.groupby(list(CONTEXT), observed=True).size()
        cells = sorted(set(kp.index) | set(kn.index))
        w, tab = {}, {}
        a2 = 0.5
        for cell in cells:
            m = (kp.get(cell, 0) + a2) / (len(pos) + a2 * len(cells))
            u = (kn.get(cell, 0) + a2) / (len(neg_all) + a2 * len(cells))
            absent = all(x in ('none', 'na') for x in cell)
            x = 0.0 if absent else max(0.0, math.log2(m / u))
            key = '|'.join(cell)
            w[key] = round(x, 3)
            tab[key] = dict(m=round(m, 6), u=round(u, 6), n_match=int(kp.get(cell, 0)), n_nonmatch=int(kn.get(cell, 0)), weight=round(x, 3))
        out['context'], tables['context'] = w, tab
        use = use + ['context']
    return dict(kind='fs', fields=use, w=out), tables


def fit_logistic(df, C=0.3):
    """L2 logistic regression on one-hot levels of the fields other than the name fields (which keep their
    Fellegi-Sunter weights from same-block non-matches); coefficients in log2 units; positive-only fields clamped"""
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    fs, _ = fit_weights(df)
    d = df[df.label.isin([0, 1])]
    other = [f for f in FIELDS if f not in NAME_FIELDS]
    X = pd.get_dummies(d[other].astype(str), prefix_sep='=')
    m = LogisticRegression(C=C, max_iter=3000)
    m.fit(X.values.astype(np.float32), d.label.values)
    coef = {c: round(float(v) / math.log(2), 4) for c, v in zip(X.columns, m.coef_[0])}
    for c in list(coef):
        f, lv = c.split('=', 1)
        if f in POSITIVE_ONLY:
            coef[c] = 0.0 if lv in (POSITIVE_ONLY[f], 'na') else max(0.0, coef[c])
        if f in NEGATIVE_ONLY:
            coef[c] = min(0.0, coef[c] - coef.get(f'{f}={NEGATIVE_ONLY[f]}', 0.0))
    for c in [c for c in coef if c.split('=', 1)[0] in NEGATIVE_ONLY and c.split('=', 1)[1] == NEGATIVE_ONLY[c.split('=', 1)[0]]]:
        coef[c] = 0.0
    # the intercept carries the training mix of matches and non-matches; thresholds absorb it
    return dict(kind='logistic', fields=list(NAME_FIELDS) + other, w={f: fs['w'][f] for f in NAME_FIELDS},
                intercept=round(float(m.intercept_[0]) / math.log(2), 4), coef=coef, C=C)


def score_vec(cd, wm):
    """match weights of a pairs frame under one model -> (total, context part)"""
    import numpy as np

    def part(f, table):
        c = cd[f]
        if not hasattr(c, 'cat'):
            c = c.astype('category')
        arr = np.append(np.array([table.get(str(x), 0.0) for x in c.cat.categories], dtype=np.float64), 0.0)
        return arr[c.cat.codes.values]
    s = np.zeros(len(cd))
    ctx = np.zeros(len(cd))
    if wm['kind'] == 'logistic':
        for f in NAME_FIELDS:
            s += part(f, wm['w'][f])
        s += wm['intercept']
        for f in wm['fields']:
            if f in NAME_FIELDS:
                continue
            x = part(f, {k.split('=', 1)[1]: v for k, v in wm['coef'].items() if k.startswith(f + '=')})
            s += x
            if f in CONTEXT:
                ctx += x
        return s, ctx
    for f in wm['fields']:
        if f == 'context':
            codes = np.zeros(len(cd), dtype=np.int64)
            cats = []
            for f2 in CONTEXT:
                c = cd[f2].cat
                codes = codes * (len(c.categories) + 1) + (c.codes.values + 1)
                cats.append(list(c.categories))
            uniq, inv = np.unique(codes, return_inverse=True)
            vals = []
            for u in uniq:
                parts = []
                for cl in reversed(cats):
                    n = len(cl) + 1
                    parts.append(cl[u % n - 1] if u % n else 'na')
                    u //= n
                vals.append(wm['w']['context'].get('|'.join(reversed(parts)), 0.0))
            x = np.array(vals)[inv]
            s += x
            ctx += x
        else:
            x = part(f, wm['w'][f])
            s += x
            if f in CONTEXT:
                ctx += x
    return s, ctx


def fit(args):
    t0 = time.time()
    cd = read_pairs("mode IN ('present', 'imp')", ['pid', 'mode', 'key', 'label'] + list(FIELDS) + ['oa_tie'])
    pv = read_pos("mode IN ('present', 'imp')")[['pid', 'mode', 'split']]
    cd = cd.merge(pv, on=['pid', 'mode'], how='left')
    import duckdb
    ra = duckdb.connect().execute(f"SELECT pid, route_a FROM '{S / 'positions.parquet'}' WHERE gold_sel").df()
    cd = cd.merge(ra, on='pid', how='left')
    fitd = cd[(cd.split < 1) & (~cd.route_a.fillna(False).astype(bool)) & cd.label.isin([0, 1])]
    n = dict(pairs=len(fitd), matches=int((fitd.label == 1).sum()),
             nonmatches_block=int(((fitd.label == 0) & (fitd['mode'].astype(str) == 'present')).sum()),
             nonmatches_impersonated=int(((fitd.label == 0) & (fitd['mode'].astype(str) == 'imp')).sum()),
             route_a_gold_excluded=int(cd[(cd.split < 1)].route_a.fillna(False).astype(bool).sum()))
    print('fit', n, round(time.time() - t0), flush=True)
    models, tables = {}, {}
    models['naive'], tables['naive'] = fit_weights(fitd)
    models['grouped'], tables['grouped'] = fit_weights(fitd, grouped=True)
    models['grouped+oa'], tables['grouped+oa'] = fit_weights(fitd, grouped=True, extra=('oa_tie',))
    models['logistic'] = fit_logistic(fitd)
    # dependence among the context fields: observed joint 'present' rate against the independence prediction
    dep = {}
    for lab in (1, 0):
        d = fitd[fitd.label == lab]
        for a, b in (('network', 'venue'), ('network', 'topic'), ('venue', 'topic'), ('topic', 'cites'), ('aff', 'network')):
            pa_ = ~d[a].astype(str).isin(['none', 'na', 'absent'])
            pb_ = ~d[b].astype(str).isin(['none', 'na', 'absent'])
            obs, exp = float((pa_ & pb_).mean()), float(pa_.mean() * pb_.mean())
            dep[f'{"match" if lab else "nonmatch"}:{a}&{b}'] = dict(observed=round(obs, 4), independent=round(exp, 4),
                                                                   ratio=round(obs / exp, 2) if exp else None)
    json.dump(dict(models=models, tables=tables, dependence=dep, n_fit=n), open(S / 'weights-all.json', 'w'), indent=1)
    print(json.dumps(dep, indent=1))
    print('fit done', round(time.time() - t0), flush=True)


# ------------------------------------------------------------------------------------------------ decide

def best_two(cd):
    """per (pid, mode): best key and its levels, best score, runner-up score, number of live candidates"""
    cd = cd.sort_values(['pid', 'mode', 'score'], ascending=[True, True, False], kind='stable')
    rank = cd.groupby(['pid', 'mode'], observed=True, sort=False).cumcount()
    first = cd[rank.values == 0]
    second = cd[rank.values == 1][['pid', 'mode', 'score']].rename(columns={'score': 'runner'})
    n = cd.groupby(['pid', 'mode'], observed=True).size().rename('n').reset_index()
    out = first.merge(second, on=['pid', 'mode'], how='left').merge(n, on=['pid', 'mode'], how='left')
    out['mode'] = out['mode'].astype(str)
    return out


ROLE_GROUPS = ('author', 'jstor-author', 'reviewer')
AUDIT = ROOT / 'data/identifiers/work-people-2026-11-11/audit-verdicts.csv'


def role_group(role):
    return role if role in ('jstor-author', 'reviewer') else 'author'


def decision(df, th):
    """link / review / none; th is one threshold set, or one per role group ({'author': {...}, 'reviewer': {...}, ...})"""
    import numpy as np
    if 'single' not in th:
        rg = df['role'].map(role_group).values
        out = np.full(len(df), 'none', dtype=object)
        for g, t in th.items():
            m = rg == g
            if m.any():
                out[m] = decision(df[m], t)
        return out
    sc = df['score'].fillna(-1e9).values
    single = ((df['n'] == 1) & (df['neg'].astype(str) == 'none')).values
    tsingle = df['freq'].astype(str).map(th['single']).fillna(th['multi']).values
    T = np.where(single, tsingle, th['multi'])
    margin_ok = (df['n'] == 1).values | ((df['score'] - df['runner'].fillna(-1e9)) >= th['margin']).values
    ctx_ok = ~df['review_record'].fillna(False).astype(bool).values | (df['ctx_w'].fillna(0).values > 0)
    link = (sc >= T) & margin_ok & ctx_ok
    review = ~link & (sc >= th['review'])
    return np.where(link, 'link', np.where(review, 'review', 'none'))


def mixture_pi(prod, present, absent, bins):
    """share of absent-author positions in a production stratum: EM on the score histogram with the two component
    densities fixed (held-out present and absent simulations, half-count smoothing)"""
    import numpy as np
    f, _ = np.histogram(np.clip(present, bins[0], bins[-1] - 1e-6), bins=bins)
    g, _ = np.histogram(np.clip(absent, bins[0], bins[-1] - 1e-6), bins=bins)
    h, _ = np.histogram(np.clip(prod, bins[0], bins[-1] - 1e-6), bins=bins)
    f = (f + 0.5) / (f.sum() + 0.5 * len(f))
    g = (g + 0.5) / (g.sum() + 0.5 * len(g))
    pi = 0.5
    for _ in range(1000):
        post = pi * g / (pi * g + (1 - pi) * f)
        new = float((h * post).sum() / max(1, h.sum()))
        if abs(new - pi) < 1e-8:
            break
        pi = new
    return pi


def strata(d):
    """stratum of each position row: single-<band> (one live candidate, no negative evidence) or multi"""
    import numpy as np
    single = ((d['n'] == 1) & (d['neg'].astype(str) == 'none')).values
    return np.where(single, 'single-' + d['freq'].astype(str).values, 'multi')


def est_fdr(pr, ab, pis, dec_p, dec_a):
    """production-weighted false-link share: per stratum, measured present outcomes and absent link rate, mixed by
    the stratum's absent share and weighted by its production count"""
    import numpy as np
    tl = fl = 0.0
    sp, sa = strata(pr), strata(ab)
    for st, v in pis.items():
        mp, ma = sp == st, sa == st
        if not mp.any():
            continue
        lab = pr['label'].values[mp]
        dp = dec_p[mp]
        R = float(((dp == 'link') & (lab == 1)).mean())
        Wr = float(((dp == 'link') & (lab == 0)).mean())
        A = float(((dec_a[ma] == 'link') & (ab['label'].values[ma] != 2)).mean()) if ma.any() else 0.0
        tl += v['n_prod'] * (1 - v['pi']) * R
        fl += v['n_prod'] * ((1 - v['pi']) * Wr + v['pi'] * A)
    return fl / max(1e-12, tl + fl), tl


def est_fdr_rg(pr, ab, pis_rg, dec_p, dec_a):
    """est_fdr summed over role groups (each with its own absent shares)"""
    TL = FL = 0.0
    gp, ga = pr['role'].map(role_group).values, ab['role'].map(role_group).values
    for g, pis in pis_rg.items():
        mp, ma = gp == g, ga == g
        if not mp.any():
            continue
        f, tl = est_fdr(pr[mp], ab[ma], pis, dec_p[mp], dec_a[ma])
        TL += tl
        FL += f * tl / max(1e-12, 1 - f) if f < 1 else 0.0
    return FL / max(1e-12, TL + FL), TL


def audit_pi(cal):
    """absent-author share implied by the 2026-11-11 hand audit of the rule's links (audit-verdicts.csv): with the rule's
    held-out recall R (author present) and link rate A on impersonated namesakes (author absent), its audited precision p
    means pi = R(1-p) / (R(1-p) + A p); p at the lower 5% Jeffreys bound (so pi is an upper bound)"""
    from scipy.stats import beta
    out = {}
    v = list(csv.DictReader(open(AUDIT, encoding='utf-8')))
    for g in ROLE_GROUPS:
        # the audited rows the current rule still links (state_now): R and A below are measured on the current rule
        rows = [r for r in v if r['sample'] == f'{g}|linked' and r.get('state_now') == 'linked']
        c = sum(r['verdict'] == 'correct' for r in rows)
        w = sum(r['verdict'] == 'wrong' for r in rows)
        rg = cal['role'].map(role_group)
        pr = cal[(cal['mode'] == 'present') & (rg == g)]
        im = cal[(cal['mode'] == 'imp') & (rg == g)]
        R = float(((pr.rule_state == 'linked') & (pr.rule_key == pr.gold)).mean()) if len(pr) else 0.0
        A = float((im.rule_state == 'linked').mean()) if len(im) else 0.0
        p_lo = float(beta.ppf(0.05, c + 0.5, w + 0.5)) if c + w else 0.0
        pi = R * (1 - p_lo) / max(1e-12, R * (1 - p_lo) + A * p_lo)
        out[g] = dict(audit_correct=c, audit_wrong=w, precision_lower_5pct=round(p_lo, 4), rule_recall=round(R, 4),
                      rule_absent_link_rate=round(A, 4), pi=round(pi, 4))
    return out


def calibrate(P, pis, grid):
    """thresholds on the calibration positions P (present, dropg, imp rows): per band for single candidates, (T, margin)
    for the rest, each stratum's estimated false-link share <= TARGET_FDR; then the review floor"""
    import numpy as np
    from scipy.stats import beta as _beta
    th = dict(single={}, multi=1e9, margin=0, review=1e9)
    pr_all = P[P['mode'] == 'present']
    ab_all = P[P['mode'].isin(['dropg', 'imp'])]
    st_p, st_a = strata(pr_all), strata(ab_all)

    def stratum_fdr(pr, ab, pi, T, margin=None):
        def linked(d):
            ok = d['score'].fillna(-1e9).values >= T
            if margin is not None:
                ok &= (d['n'] == 1).values | ((d['score'] - d['runner'].fillna(-1e9)) >= margin).values
            ok &= ~d['review_record'].fillna(False).astype(bool).values | (d['ctx_w'].fillna(0).values > 0)
            return ok
        lp, la = linked(pr), linked(ab)
        lab = pr['label'].values
        r, wr = float((lp & (lab == 1)).sum()), float((lp & (lab == 0)).sum())
        a = float((la & (ab['label'].values != 2)).sum())
        npres, nabs = max(1, len(pr)), max(1, len(ab))
        # upper 95% Jeffreys bounds on the two error rates (small cells must not set bars on luck)
        R = r / npres
        Wr = float(_beta.ppf(0.95, wr + 0.5, npres - wr + 0.5))
        A = float(_beta.ppf(0.95, a + 0.5, nabs - a + 0.5))
        tl, fl = (1 - pi) * R, (1 - pi) * Wr + pi * A
        return fl / max(1e-12, tl + fl), tl
    for band in BANDS:
        st = 'single-' + band
        pr, ab = pr_all[st_p == st], ab_all[st_a == st]
        pi = pis.get(st, {}).get('pi', 1.0)
        T = 1e9
        if len(pr):
            for t in grid[::-1]:
                f, tl = stratum_fdr(pr, ab, pi, t)
                if tl > 0 and f <= TARGET_FDR:
                    T = float(t)      # the lowest bar on the grid whose estimated false share meets the target
        th['single'][band] = T
    pr, ab = pr_all[st_p == 'multi'], ab_all[st_a == 'multi']
    pi = pis.get('multi', {}).get('pi', 1.0)
    best = (1e9, 0, -1.0)
    for margin in (0, 1, 2, 3, 4, 6, 8, 10):
        T = None
        for t in grid[::-1]:
            f, tl = stratum_fdr(pr, ab, pi, t, margin)
            if tl > 0 and f <= TARGET_FDR:
                T = (float(t), tl)
        if T and T[1] > best[2]:
            best = (T[0], margin, T[1])
    th['multi'], th['margin'] = best[0], best[1]
    # review floor: below the lowest link bar, down to where the best candidate is right at least half the time
    # (present and absent simulations mixed by the production-weighted absent share)
    lo = min([th['multi']] + [v for v in th['single'].values() if v < 1e9])
    npd = sum(v['n_prod'] for v in pis.values())
    pib = sum(v['pi'] * v['n_prod'] for v in pis.values()) / max(1, npd)
    sc, lab = pr_all['score'].values, pr_all['label'].values
    sca = ab_all['score'].values
    rv = lo
    for t in grid[::-1]:
        if t >= lo:
            continue
        m, ma = (sc >= t) & (sc < lo), (sca >= t) & (sca < lo)
        right = (1 - pib) * (lab[m] == 1).sum() / max(1, len(sc))
        other = (1 - pib) * (lab[m] != 1).sum() / max(1, len(sc)) + pib * ma.sum() / max(1, len(sca))
        if right + other > 0 and right / (right + other) >= 0.5:
            rv = float(t)
        else:
            break
    th['review'] = max(0.0, rv) if rv < 1e9 else rv     # the clerical band starts at positive evidence
    return th


def positions_frame(cd, pv, meta):
    """one row per position variant (prod, present, imp) plus the dropg view of each present position (the hidden
    key's own pair removed): best candidate, runner-up, n live; positions with no live candidate kept (score NaN)"""
    import pandas as pd
    bt = best_two(cd)
    keep = ['pid', 'mode', 'key', 'score', 'runner', 'n', 'label', 'freq', 'neg', 'ctx_w', 'name', 'date', 'aff', 'network',
            'venue', 'topic', 'cites']
    bt = bt[keep]
    dg = cd[(cd['mode'].astype(str) == 'present') & (cd.label != 1)].copy()
    dg['mode'] = 'dropg'
    bd = best_two(dg)[keep]
    pvd = pv[pv['mode'] == 'present'].copy()
    pvd['mode'] = 'dropg'
    pvd['n_live'] = pvd['n_live'] - (pvd['g_status'] == 'live').astype(int)
    P = pd.concat([pv, pvd], ignore_index=True).merge(pd.concat([bt, bd], ignore_index=True), on=['pid', 'mode'], how='left')
    P = P.merge(meta, on='pid', how='left')
    P['n'] = P['n'].fillna(0)
    P['label'] = P['label'].fillna(-9)
    return P


def calibrate_all(P, grid, bins, author_scale=1.0, mixture_only=False):
    """per role group: absent shares by stratum (mixture estimate; the audit bound for reviewer and JSTOR author, the
    larger of the two for author), thresholds, calibration measures"""
    import numpy as np
    cal = P[P.split.isin([1, 2]) & ~P.route_a.fillna(False).astype(bool)]
    prod = P[P['mode'] == 'prod']
    ap = audit_pi(cal)
    th, pis_rg, em_rg = {}, {}, {}
    for g in ROLE_GROUPS:
        c = cal[cal['role'].map(role_group) == g]
        pdg = prod[prod['role'].map(role_group) == g]
        sp, sc_ = strata(pdg), strata(c)
        pis, em = {}, {}
        for st in ['single-' + b for b in BANDS] + ['multi']:
            pr = c[(c['mode'] == 'present') & (sc_ == st) & (c.g_status == 'live')]
            ab = c[c['mode'].isin(['dropg', 'imp']) & (sc_ == st) & c.score.notna()]
            pd_ = pdg[(sp == st) & pdg.score.notna()]
            e = mixture_pi(pd_.score.values, pr.score.values, ab.score.values, bins) if len(pd_) and len(pr) and len(ab) else 1.0
            em[st] = round(e, 4)
            if mixture_only:
                pi = e
            elif g == 'author':
                pi = min(1.0, max(e, ap[g]['pi']) * author_scale)
            elif st in ('single-unique', 'single-2-5'):
                pi = ap[g]['pi']          # the bands the audited rule links come from (rarity branches)
            else:
                pi = max(e, ap[g]['pi'])  # the audit does not speak for common names, initials or several candidates
            pis[st] = dict(pi=round(pi, 4), n_prod=int(len(pd_)), n_present=int(len(pr)), n_absent=int(len(ab)))
        cp = c[c.score.notna() | (c['mode'] == 'present')]
        th[g] = calibrate(cp, pis, grid)
        pis_rg[g], em_rg[g] = pis, em
    prc, abc = cal[cal['mode'] == 'present'], cal[cal['mode'].isin(['dropg', 'imp'])]
    dp, da = decision(prc, th), decision(abc, th)
    f, tl = est_fdr_rg(prc, abc, pis_rg, dp, da)
    nprod = sum(v['n_prod'] for p_ in pis_rg.values() for v in p_.values())
    return dict(thresholds=th, pi=pis_rg, pi_em=em_rg, audit_pi=ap, calib_est_fdr=round(f, 5),
                calib_expected_true_links_per_1000_scored_positions=round(1000 * tl / max(1, nprod), 2),
                calib_recall_present=round(float(((dp == 'link') & (prc.label.values == 1)).mean()), 4))


def decide(args):
    import numpy as np
    import pandas as pd
    t0 = time.time()
    allw = json.load(open(S / 'weights-all.json'))
    models = allw['models']
    db = duck()
    meta = db.execute(f"""SELECT pid, tbl, role, kind, year, route_a,
            role = 'author' AND regexp_matches(coalesce(title, ''), '(?i)^\\s*review of|\\breviews?\\b|besprechung|rezension|reseñas?\\b|recensioni?\\b|comptes? rendus?')
            AS review_record FROM '{S / 'positions.parquet'}' WHERE credited = '' OR gold_sel""").df()
    pv = read_pos("true")
    pv = pv[['pid', 'mode', 'split', 'gold', 'n_live', 'g_status', 'rule_state', 'rule_key', 'rule_branch', 'rule_drop_state',
             'rule_drop_key', 'exact', 'capped', 'n_date_out', 'n_hard', 'imp_key']]
    cd = read_pairs('true')
    print('loaded', len(cd), 'pairs', len(pv), 'position variants', round(time.time() - t0), rss(), 'MB', flush=True)
    grid = np.arange(-15, 80.5, 0.5)
    bins = np.arange(-40, 90, 1.0)
    res = {}
    for model in ('naive', 'grouped', 'grouped+oa', 'logistic'):
        cd['score'], cd['ctx_w'] = score_vec(cd, models[model])
        P = positions_frame(cd, pv, meta)
        res[model] = calibrate_all(P, grid, bins)
        print(model, json.dumps({k: v for k, v in res[model].items() if k not in ('pi', 'audit_pi', 'pi_em')}), round(time.time() - t0), rss(), 'MB', flush=True)
    best = max(('naive', 'grouped', 'logistic'), key=lambda m: res[m]['calib_expected_true_links_per_1000_scored_positions'])
    # sensitivity: the author group's absent share (the mixture estimate, not audited at that rate) halved / quartered,
    # and every group at the mixture estimate
    cd['score'], cd['ctx_w'] = score_vec(cd, models[best])
    P = positions_frame(cd, pv, meta)
    res[best]['pi_sensitivity'] = {
        'author_pi_x0.5': {k: v for k, v in calibrate_all(P, grid, bins, author_scale=0.5).items() if k in ('thresholds', 'calib_recall_present', 'calib_expected_true_links_per_1000_scored_positions')},
        'all_groups_mixture_pi': {k: v for k, v in calibrate_all(P, grid, bins, mixture_only=True).items() if k in ('thresholds', 'calib_recall_present', 'calib_expected_true_links_per_1000_scored_positions')}}
    oa = dict(with_oa_tie=res['grouped+oa']['calib_expected_true_links_per_1000_scored_positions'],
              without=res['grouped']['calib_expected_true_links_per_1000_scored_positions'])
    json.dump(dict(models=res, chosen=best, oa_tie=oa), open(S / 'decide-models.json', 'w'), indent=1, default=float)
    print('chosen', best, oa, flush=True)
    # final: the chosen model, its thresholds; test evaluation; production decisions
    wm = models[best]
    th = res[best]['thresholds']
    pis = res[best]['pi']
    cd['score'], cd['ctx_w'] = score_vec(cd, wm)
    P = positions_frame(cd, pv, meta)
    P['decision'] = decision(P, th)
    P.loc[P['exact'].fillna('') != '', 'decision'] = 'exact'
    keep_cols = ['pid', 'mode', 'split', 'gold', 'key', 'score', 'runner', 'n', 'label', 'freq', 'neg', 'ctx_w', 'name', 'date',
                 'aff', 'network', 'venue', 'topic', 'cites', 'decision', 'rule_state', 'rule_key', 'rule_branch',
                 'rule_drop_state', 'rule_drop_key', 'g_status', 'exact', 'capped', 'n_live', 'tbl', 'role', 'kind', 'year',
                 'route_a', 'review_record']
    P[keep_cols].to_parquet(S / 'decided.parquet')
    # candidate rows of review positions (clerical band: up to three candidates at or above the review floor)
    cdp = cd[cd['mode'].astype(str) == 'prod'][['pid', 'key', 'score', 'ctx_w'] + list(FIELDS)]
    cdp[['pid', 'score']].assign(key=cdp.key.astype(str)).to_parquet(S / 'cand-scores.parquet')
    rv = set(P[(P['mode'] == 'prod') & (P.decision == 'review')].pid)
    cr = cdp[cdp.pid.isin(rv) & (cdp.score >= min(t['review'] for t in th.values()))].sort_values(['pid', 'score'], ascending=[True, False])
    cr = cr.groupby('pid').head(3)
    for f in FIELDS:
        cr[f] = cr[f].astype(str)
    cr['key'] = cr['key'].astype(str)
    cr.to_parquet(S / 'review-candidates.parquet')
    json.dump(dict(model=best, weights=wm, tables=allw['tables'].get(best), thresholds=th, pi=pis,
                   pi_em=res[best]['pi_em'], audit_pi=res[best]['audit_pi'], pi_sensitivity=res[best]['pi_sensitivity'],
                   models_compared={k: {kk: vv for kk, vv in v.items() if kk not in ('pi', 'pi_em')} for k, v in res.items()},
                   oa_tie=oa, dependence=allw['dependence'], n_fit=allw['n_fit']),
              open(S / 'weights-chosen.json', 'w'), indent=1, default=float)
    print('decide done', round(time.time() - t0), rss(), 'MB', flush=True)



# ------------------------------------------------------------------------------------------------ report and outputs

def contributions(row, wm):
    """per-field weight of one candidate row under the chosen model"""
    out = {}
    if wm['kind'] == 'logistic':
        for f in wm['fields']:
            out[f] = wm['w'][f].get(str(row[f]), 0.0) if f in NAME_FIELDS else wm['coef'].get(f'{f}={row[f]}', 0.0)
        return out
    for f in wm['fields']:
        if f == 'context':
            out['context(' + '|'.join(str(row[x]) for x in CONTEXT) + ')'] = wm['w']['context'].get('|'.join(str(row[x]) for x in CONTEXT), 0.0)
        else:
            out[f] = wm['w'][f].get(str(row[f]), 0.0)
    return out


def top_fields(row, wm, n=3):
    c = contributions(row, wm)
    lv = {f: row[f] for f in FIELDS}
    items = sorted(c.items(), key=lambda x: -abs(x[1]))
    out = []
    for f, w in items:
        if w == 0:
            continue
        lab = f if f.startswith('context') else f'{f}={lv[f]}'
        out.append(f'{lab}:{w:+.1f}')
        if len(out) >= n:
            break
    return '; '.join(out)


def rates(d):
    """outcome counts of decided position rows (present: right / wrong / dup; absent: false links)"""
    import numpy as np
    lk = (d.decision == 'link').values
    lab = d.label.values
    right, dup = int((lk & (lab == 1)).sum()), int((lk & (lab == 2)).sum())
    wrong = int((lk & (lab == 0)).sum())
    n = len(d)
    return dict(positions=n, link=int(lk.sum()), review=int((d.decision == 'review').sum()), right=right, wrong=wrong,
                dup_key=dup, precision=round(right / max(1, right + wrong), 4) if right + wrong else None,
                precision_dup_as_wrong=round(right / max(1, right + wrong + dup), 4) if right + wrong + dup else None,
                recall=round(right / max(1, n), 4))


def rule_rates(d, kind):
    """the rule linker's outcomes on the same rows: present (rule_state/rule_key), dropg (rule_drop_*), imp"""
    import numpy as np
    if kind == 'present':
        lk = (d.rule_state == 'linked').values
        right = lk & (d.rule_key == d.gold).values
        lab_other = d['rule_label'].values
        wrong = lk & ~right & (lab_other != 2)
        dup = lk & ~right & (lab_other == 2)
    elif kind == 'dropg':
        lk = (d.rule_drop_state == 'linked').values
        right = np.zeros(len(d), bool)
        wrong = lk & (d['rule_drop_label'].values != 2)
        dup = lk & (d['rule_drop_label'].values == 2)
    else:
        lk = (d.rule_state == 'linked').values
        right = np.zeros(len(d), bool)
        wrong, dup = lk, np.zeros(len(d), bool)
    n = len(d)
    r, w, u = int(right.sum()), int(wrong.sum()), int(dup.sum())
    return dict(positions=n, link=int(lk.sum()), right=r, wrong=w, dup_key=u,
                precision=round(r / max(1, r + w), 4) if r + w else None, recall=round(r / max(1, n), 4))


def report(args):
    import numpy as np
    import pandas as pd
    t0 = time.time()
    W8 = json.load(open(S / 'weights-chosen.json'))
    wm, th, pis = W8['weights'], W8['thresholds'], W8['pi']
    D = pd.read_parquet(S / 'decided.parquet')
    db = duck()
    G = GRAPH
    # labels of the rule's linked key among the same block (dup / wrong), from the present pairs
    lab = db.execute(f"""SELECT pid, key, label FROM read_parquet('{S / 'pairs'}/cand-*.parquet') WHERE mode = 'present'""").df()
    labd = {(p, k): l for p, k, l in lab.itertuples(index=False)}
    D['rule_label'] = [labd.get((p, k), 0) for p, k in zip(D.pid, D.rule_key.fillna(''))]
    D['rule_drop_label'] = [labd.get((p, k), 0) for p, k in zip(D.pid, D.rule_drop_key.fillna(''))]
    # subgroup attributes of the hidden key: ORCID, PhD country
    orc = {k for (k,) in db.execute(f"SELECT key FROM '{G}/person.parquet' WHERE orcid IS NOT NULL AND len(orcid) > 0").fetchall()}
    dc = dict(db.execute(f"""SELECT id, country FROM read_csv('{ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'}',
            all_varchar=true)""").fetchall())
    from graph_tables import keylog
    country = {}
    for k, d in db.execute(f"""SELECT a."from", replace(x, 'diss-thesis:', '') FROM {keylog(G, 'authored')} a JOIN
            (SELECT key, unnest(anchors) x FROM '{G}/work.parquet' WHERE kind = 'thesis') t ON t.key = a."to"
            WHERE x LIKE 'diss-thesis:%'""").fetchall():
        if dc.get(d):
            country[k] = dc[d]
    for k, an in db.execute(f"SELECT key, anchors FROM '{G}/person.parquet'").fetchall():
        if k not in country and any(a.startswith('aha-phd:') for a in an or []):
            country[k] = 'US/CA (AHA)'
    gold = D[D['mode'] != 'prod'].copy()
    gold['orcid'] = np.where(gold.gold.isin(orc), 'key has ORCID', 'no ORCID')
    gold['country'] = gold.gold.map(country).fillna('unknown')
    gold['decade'] = (gold.year.fillna(0) // 10 * 10).astype(int).astype(str).replace('0', 'undated')
    gold['band'] = gold.freq.astype(object).fillna('no live candidate')
    gold['kind'] = gold.kind.fillna('?')
    out = dict(model=W8['model'], thresholds=th, target_false_link_share=TARGET_FDR,
               absent_share_by_stratum=pis, models_compared=W8['models_compared'], oa_tie_test=W8['oa_tie'])
    for split, nm in ((2, 'calibration'), (3, 'test')):
        g = gold[(gold.split.isin([1, 2]) if split == 2 else gold.split == 3) & ~gold.route_a.fillna(False).astype(bool)]
        pr, dg, im = g[g['mode'] == 'present'], g[(g['mode'] == 'dropg') & (g.n_live > 0)], g[(g['mode'] == 'imp')]
        ab = pd.concat([dg, im])
        f, tl = est_fdr_rg(pr, ab, pis, pr.decision.values, ab.decision.values)
        block = dict(present=rates(pr), absent_dropped_key=rates(dg), absent_impersonated=rates(im),
                     est_false_link_share_production_weighted=round(f, 5),
                     hidden_key_status=pr.g_status.value_counts().to_dict(),
                     rule_linker_same_rows=dict(present=rule_rates(pr, 'present'), absent_dropped_key=rule_rates(dg, 'dropg'),
                                                absent_impersonated=rule_rates(im, 'imp')))
        if split == 3:
            subs = {}
            for col in ('orcid', 'band', 'role', 'kind', 'country', 'decade', 'tbl', 'route_a'):
                subs[col] = {}
                for v in sorted(pr[col].astype(str).unique()):
                    p_ = pr[pr[col].astype(str) == v]
                    a_ = ab[ab[col].astype(str) == v]
                    if len(p_) < 30:
                        continue
                    ff, _ = est_fdr_rg(p_, a_, pis, p_.decision.values, a_.decision.values)
                    rr = rates(p_)
                    subs[col][v] = dict(present=rr, absent_positions=len(a_),
                                        absent_false_links=int(((a_.decision == 'link') & (a_.label != 2)).sum()),
                                        est_false_link_share=round(ff, 5),
                                        rule_present=rule_rates(p_, 'present'))
            block['subgroups'] = subs
            # head-to-head on the same held-out rows
            sr = (pr.decision == 'link') & (pr.label == 1)
            rr_ = (pr.rule_state == 'linked') & (pr.rule_key == pr.gold)
            sw = (pr.decision == 'link') & (pr.label == 0)
            rw = (pr.rule_state == 'linked') & (pr.rule_key != pr.gold) & (pr.rule_label != 2)
            block['head_to_head_present'] = dict(both_right=int((sr & rr_).sum()), scorer_only_right=int((sr & ~rr_).sum()),
                                                 rule_only_right=int((~sr & rr_).sum()), scorer_wrong=int(sw.sum()), rule_wrong=int(rw.sum()))
            sa = ((ab.decision == 'link') & (ab.label != 2))
            ra = np.where(ab['mode'] == 'dropg', (ab.rule_drop_state == 'linked') & (ab.rule_drop_label != 2), ab.rule_state == 'linked')
            block['head_to_head_absent'] = dict(positions=len(ab), scorer_false=int(sa.sum()), rule_false=int(ra.sum()),
                                                both=int((sa & ra).sum()))
        out[nm] = block
    ra = gold[(gold.split == 3) & gold.route_a.fillna(False).astype(bool) & (gold['mode'] == 'present')]
    out['route_a_gold_test'] = dict(note='held-out credits resting only on an OpenAlex-profile key-log claim; not used for '
                                    'estimation or thresholds', scorer=rates(ra), rule=rule_rates(ra, 'present'))
    # production
    pr = D[D['mode'] == 'prod']
    out['production'] = dict(positions=len(pr), by_decision=pr.decision.value_counts().to_dict(),
                             by_table_decision={f'{t}|{r}': v.decision.value_counts().to_dict() for (t, r), v in pr.groupby(['tbl', 'role'])},
                             capped_blocks=int(pr.capped.fillna(False).astype(bool).sum()),
                             no_live_candidate=int((pr.n_live.fillna(0) == 0).sum()))
    # against the rule on the same positions (recomputed here) and against the rule's own exported results
    off = db.execute(f"""SELECT pid, state AS off_state, key AS off_key FROM read_parquet(['{S / 'wp/results.parquet'}', '{S / 'no/results.parquet'}'])""").df()
    pr = pr.merge(off, on='pid', how='left')
    agree = (pr.rule_state == pr.off_state) & (pr.rule_key.fillna('') == pr.off_key.fillna(''))
    sl = pr.decision == 'link'
    rl = pr.rule_state == 'linked'
    out['production_vs_rule'] = dict(
        rule_recomputed_agrees_with_exported=round(float(agree[pr.off_state.notna()].mean()), 4),
        exported_rows_matched=int(pr.off_state.notna().sum()),
        scorer_link_rule_linked_same_key=int((sl & rl & (pr.key == pr.rule_key)).sum()),
        scorer_link_rule_linked_other_key=int((sl & rl & (pr.key != pr.rule_key)).sum()),
        scorer_link_rule_not_linked=int((sl & ~rl).sum()),
        scorer_link_rule_states=pr[sl & ~rl].rule_state.value_counts().to_dict(),
        rule_linked_scorer_not=int((rl & ~sl).sum()),
        rule_linked_scorer_decision=pr[rl & ~sl].decision.value_counts().to_dict(),
        scorer_review_by_rule_state=pr[pr.decision == 'review'].rule_state.value_counts().to_dict())
    # outputs: links.csv.gz (link, exact, review rows of production positions)
    meta = db.execute(f"SELECT pid, work, role, pos, name AS printed, source, tbl FROM '{S / 'positions.parquet'}' WHERE credited = ''").df()
    pr = pr.merge(meta[['pid', 'work', 'pos', 'printed', 'source']], on='pid', how='left')
    rc = pd.read_parquet(S / 'review-candidates.parquet')
    OUT.mkdir(parents=True, exist_ok=True)
    nrow = Counter()
    with gzip.open(OUT / 'links.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work', 'role', 'position', 'printed_name', 'person_key', 'score', 'runner_up_score', 'decision',
                    'n_candidates', 'top_fields', 'rule_state', 'rule_key', 'source'])
        lr = pr[pr.decision.isin(['link', 'exact'])]
        for r in lr.itertuples(index=False):
            if r.decision == 'exact':
                for k in str(r.exact).split('|'):
                    w.writerow([r.work, r.role, r.pos, r.printed, k, '', '', 'exact', 0, 'identifier', r.rule_state, r.rule_key, r.source])
                    nrow['exact'] += 1
                continue
            row = {f: getattr(r, f) for f in FIELDS}
            w.writerow([r.work, r.role, r.pos, r.printed, r.key, round(r.score, 2), '' if pd.isna(r.runner) else round(r.runner, 2),
                        'link', int(r.n), top_fields(row, wm), r.rule_state, r.rule_key, r.source])
            nrow['link'] += 1
        rv = pr[pr.decision == 'review'][['pid', 'work', 'role', 'pos', 'printed', 'n', 'rule_state', 'rule_key', 'source']].merge(rc, on='pid')
        best = rv.groupby('pid').score.transform('max')
        rv = rv.assign(runner=rv.groupby('pid').score.transform(lambda x: x.nlargest(2).iloc[-1] if len(x) > 1 else np.nan))
        for r in rv.itertuples(index=False):
            row = {f: getattr(r, f) for f in FIELDS}
            w.writerow([r.work, r.role, r.pos, r.printed, r.key, round(r.score, 2), '' if pd.isna(r.runner) else round(r.runner, 2),
                        'review', int(r.n), top_fields(row, wm), r.rule_state, r.rule_key, r.source])
            nrow['review'] += 1
    out['links_csv_rows'] = dict(nrow)
    json.dump(dict(model=W8['model'], fields={f: sorted(W8['weights']['w'].get(f, {}).keys()) for f in W8['weights']['fields']},
                   weights=W8['weights'], m_u_tables=W8['tables'], thresholds=th, absent_share_by_stratum=pis,
                   positive_only_fields=sorted(POSITIVE_ONLY), name_fields_u_from='same-block non-matches only',
                   dependence_check=W8['dependence'], n_fit=W8['n_fit'], target_false_link_share=TARGET_FDR,
                   built=time.strftime('%Y-%m-%d %H:%M'), graph_snapshot=json.load(open(S / 'prep.json')).get('graph_built')),
              open(OUT / 'weights.json', 'w'), indent=1, default=float)
    out['prep'] = json.load(open(S / 'prep.json'))
    out['built'] = time.strftime('%Y-%m-%d %H:%M')
    json.dump(out, open(OUT / 'report.json', 'w'), indent=1, default=lambda x: int(x) if hasattr(x, 'item') else str(x))
    pr.to_parquet(S / 'prod-decided.parquet')
    print(json.dumps({k: v for k, v in out.items() if k in ('test', 'production', 'production_vs_rule', 'links_csv_rows')},
                     indent=1, default=str)[:12000])
    print('report done', round(time.time() - t0), rss(), 'MB', flush=True)



def dossier(db, keys):
    """what the graph knows of each key: label, identifiers, PhD, life years, affiliations, key-log works"""
    from graph_tables import keylog
    G = GRAPH
    db.register('kk', db.execute('SELECT unnest(?) AS key', [sorted(keys)]).df())
    info = {}
    for k, lab, an in db.execute(f"SELECT p.key, label, anchors FROM '{G}/person.parquet' p JOIN kk USING (key)").fetchall():
        kinds = Counter(a.split(':')[0] for a in an or [])
        info[k] = dict(label=lab, ids=' '.join(f'{a}x{n}' if n > 1 else a for a, n in sorted(kinds.items())), aff=[], works=[])
    for k, il, src, fy, ly in db.execute(f"""SELECT a."from", i.label, a.source, a.first_year, a.last_year FROM '{G}/affiliated_with.parquet' a
            JOIN '{G}/institution.parquet' i ON i.key = a."to" JOIN kk ON kk.key = a."from" """).fetchall():
        info[k]['aff'].append(f'{il} ({src} {fy or ""}-{ly or ""})')
    for k, t, y, kind, j in db.execute(f"""SELECT a."from", w.label, w.year, w.kind, w.journal FROM {keylog(G, 'authored')} a
            JOIN '{G}/work.parquet' w ON w.key = a."to" JOIN kk ON kk.key = a."from" ORDER BY w.year""").fetchall():
        info[k]['works'].append(f'{y} {kind}: {(t or "")[:90]}' + (f' [{j[:40]}]' if j else ''))
    return info


def sample(args):
    """hand-read sheets: new scorer links the rule did not make (stratified by score margin over the bar and name
    frequency band), and rule links the scorer rejects"""
    import pandas as pd
    W8 = json.load(open(S / 'weights-chosen.json'))
    th = W8['thresholds']
    D = pd.read_parquet(S / 'prod-decided.parquet')
    db = duck()
    single = (D.n == 1) & (D.neg.astype(str) == 'none')
    bar = [th[role_group(r)]['single'].get(f, th[role_group(r)]['multi']) if s_ else th[role_group(r)]['multi']
           for f, s_, r in zip(D.freq.astype(str), single, D.role)]
    D['over'] = D.score - pd.Series(bar, index=D.index)
    new = D[(D.decision == 'link') & (D.rule_state != 'linked')].copy()
    new['sband'] = pd.cut(new.over, [-1, 3, 8, 1e9], labels=['0-3', '3-8', '8+']).astype(str)
    new['fb'] = new.freq.astype(str).replace({'initials': 'other', 'unmeasured': 'other'})
    rnd = random.Random(7)
    picks = []
    cells = sorted(new.groupby(['sband', 'fb']).groups.items())
    per = max(1, args.n_new // max(1, len(cells)))
    for _, idx in cells:
        idx = list(idx)
        rnd.shuffle(idx)
        picks += idx[:per]
    picks = picks[:args.n_new]
    lost = D[(D.rule_state == 'linked') & (D.decision != 'link')]
    li = list(lost.index)
    rnd.shuffle(li)
    sel = [('NEW', i) for i in picks] + [('REJ', i) for i in li[:args.n_rej]]
    keys = {D.at[i, 'key'] for _, i in sel if isinstance(D.at[i, 'key'], str)} | {D.at[i, 'rule_key'] for _, i in sel if D.at[i, 'rule_key']}
    info = dossier(db, keys)
    pids = [int(D.at[i, 'pid']) for _, i in sel]
    pos = {r['pid']: r for r in db.execute(f"SELECT pid, work, name, title, year, wjournal, kind, role, insts, raw_aff FROM '{S / 'positions.parquet'}' "
                                              f"WHERE pid IN ({','.join(map(str, pids))})").df().to_dict('records')}
    works = {r['work'] for r in pos.values()}
    co = defaultdict(list)
    db.register('ww', db.execute('SELECT unnest(?) AS work', [sorted(works)]).df())
    for w, nm, ps in db.execute(f"SELECT work, name, pos FROM '{S / 'positions.parquet'}' JOIN ww USING (work) ORDER BY pos").fetchall():
        co[w].append(nm)
    with open(S / 'handread.txt', 'w') as f:
        for n, (tag, i) in enumerate(sel):
            r = D.loc[i]
            p = pos[int(r.pid)]
            f.write(f"=== {tag}-{n:02d} pid {r.pid} decision {r.decision} score {r.score:.1f} over-bar {r.over:.1f} runner {r.runner} n {r.n} "
                    f"| rule {r.rule_state} {r.rule_key} {r.rule_branch}\n")
            f.write(f"  printed '{p['name']}' ({p['role']}, {p['kind']}, {p['year']}) in '{(p['title'] or '')[:120]}' [{p['wjournal']}]\n")
            f.write(f"  co-printed: {'; '.join(x for x in co[p['work']] if x != p['name'])[:200]}\n  insts: {list(p['insts'] if p['insts'] is not None else [])[:2]} {list(p['raw_aff'] if p['raw_aff'] is not None else [])[:1]}\n")
            f.write('  levels: ' + ' '.join(f'{x}={r[x]}' for x in FIELDS) + '\n')
            for kk, nm in ((r.key, 'scorer'), (r.rule_key, 'rule')):
                if not isinstance(kk, str) or not kk or (nm == 'rule' and kk == r.key):
                    continue
                d = info.get(kk, {})
                f.write(f"  [{nm}] {kk} {d.get('label')} | {d.get('ids')}\n    aff: {'; '.join(d.get('aff', [])[:4])}\n")
                for x in d.get('works', [])[:8]:
                    f.write(f'    {x}\n')
            f.write('\n')
    print('sheet', S / 'handread.txt', len(sel))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('prep')
    a = sub.add_parser('pairs')
    a.add_argument('--buckets', default='')
    a.add_argument('--sample', type=int, default=0, help='keep about one position in SAMPLE (testing)')
    a.add_argument('--force', action='store_true')
    sub.add_parser('fit')
    sub.add_parser('decide')
    sub.add_parser('report')
    a = sub.add_parser('sample')
    a.add_argument('--n-new', type=int, default=60)
    a.add_argument('--n-rej', type=int, default=30)
    args = ap.parse_args()
    {'prep': prep, 'pairs': pairs, 'fit': fit, 'decide': decide, 'report': report, 'sample': sample}[args.cmd](args)


if __name__ == '__main__':
    main()
