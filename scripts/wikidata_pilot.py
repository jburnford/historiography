"""Wikidata pilot 2026-11-14: new items for people with a history signal and no Wikidata id. Prepares; publishes nothing.

Pool (explorer DB, read-only): person keys with no `wd:` anchor, an `lcnaf:` anchor, an AUTHORED book, and a history
signal: an `aha-phd:` anchor (AHA dissertation record), an AHA directory `aha:` anchor, a History thesis in the graph
(a thesis node with an `aha-diss:` anchor or a corpus `diss-thesis:` whose eligibility is history_phd), or a SUPERVISED
edge to such a thesis. Ranked by the person node's `cited` (descending), then key.

In rank order each row goes through
1. internal exclusions (wrong-anchor and duplicate lists, possibly-same edges, how the LC authority came to be tied to
   the history record (event `basis` in the key log), label form, LC record state, namesake signs in the dates),
2. a Wikidata screen on QLever: the item citing the LC id (P244), the item LC itself names, then VIAF/ISNI/ORCID/GND
   items, then humans whose label or alias is one of the person's name forms, judged on birth year, death year,
   occupation, description and their own LC id,
until 500 rows survive with no item. Those are the pilot. Existing items found by identifier become an attach
proposal (dry-run validated, never applied); same-name humans not ruled out are held.

    python3 scripts/wikidata_pilot.py pool      # pool + exclusions -> build/wikidata-pilot-2026-11-14/pool.json
    python3 scripts/wikidata_pilot.py screen    # Wikidata screen in rank order (cached)
    python3 scripts/wikidata_pilot.py write     # pilot-500.csv, QuickStatements batches, proposals, README counts
"""
import argparse
import csv
import glob
import gzip
import io
import json
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
OUT = ROOT / 'data/identifiers/wikidata-pilot-2026-11-14'
CACHE = ROOT / 'build/wikidata-pilot-2026-11-14'
EXPLORER = ROOT / 'build/graph/explorer.duckdb'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
LC_NOTES = '/mnt/e/lc-authorities/personal-notes.parquet'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
AHA_URL = 'https://secure.historians.org/members/services/cgi-bin/memberdll.dll/info?wrp=dissertations.htm'
TARGET = 500
# verified on QLever 2026-11-14 (labels read back): P244 LC, P214 VIAF, P213 ISNI, P496 ORCID, P227 GND, P6782 ROR,
# P69 educated at, P512 academic degree, P582 end time, P184 doctoral advisor, P108 employer, P106 occupation,
# P31 instance of, P569 birth, P570 death, P800 notable work, P248 stated in, P854 reference URL, P813 retrieved,
# Q5 human, Q201788 historian, Q752297 Doctor of Philosophy, Q18912790 LC Name Authority File
LC_NAF, PHD, HISTORIAN = 'Q18912790', 'Q752297', 'Q201788'
TODAY = '+2026-11-14T00:00:00Z/11'
QLEVER = 'https://qlever.dev/api/wikidata'
UA = 'kg-research-client/0.1'
PREFIX = ('PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> '
          'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> '
          'PREFIX schema: <http://schema.org/> PREFIX owl: <http://www.w3.org/2002/07/owl#> ')
DOCTORATE = re.compile(r'ph\.?\s?d\b|d\.?\s?phil|doctora|thesis|\bdiss\b|dissertation', re.I)
JOB = re.compile(r'prof|lectur|faculty|taught|teach|instructor|\bchair', re.I)


# ---------------------------------------------------------------- helpers

def qlever(q, tries=6):
    t = waits = 0
    while t < tries:
        t += 1
        try:
            req = urllib.request.Request(QLEVER, data=urllib.parse.urlencode({'query': PREFIX + q}).encode(),
                                         headers={'Accept': 'application/sparql-results+json', 'User-Agent': UA})
            rows = json.load(urllib.request.urlopen(req, timeout=240))['results']['bindings']
            time.sleep(1.5)
            return rows
        except urllib.error.HTTPError as e:
            body = e.read()[:400].decode('utf-8', 'replace')
            print('qlever retry', t, str(e)[:100], re.sub(r'\s+', ' ', body)[:200], file=sys.stderr, flush=True)
            if e.code == 429 and 'timed out' not in body and waits < 10:   # rate limit, not a timeout: wait it out
                waits += 1
                time.sleep(int(e.headers.get('Retry-After') or 0) or 60)
                t -= 1
                continue
            time.sleep(10 * (t + 1))
        except Exception as e:  # noqa: BLE001 — network: back off, then give up loudly
            print('qlever retry', t, str(e)[:200], file=sys.stderr, flush=True)
            time.sleep(10 * (t + 1))
    raise SystemExit('QLever failed')


def val(b, k):
    x = b.get(k)
    if not x:
        return None
    s = x['value']
    return s.rsplit('/', 1)[1] if s.startswith('http://www.wikidata.org/entity/') else s


def lit(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def year_of(s):
    m = re.search(r'(\d{4})', s or '')
    return int(m.group(1)) if m else None


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).lower()


# ---------------------------------------------------------------- names

def split_heading(h):
    """LC heading 'Palmer, R. R. (Robert Roswell), 1909-2002' -> (family, given, fuller, dates)."""
    h = (h or '').strip()
    dates = ''
    m = re.search(r',\s*((?:approximately |active |b\. |d\. |-)?\d{3,4}\??-?(?:\d{3,4})?\??)\s*$', h)
    if m:
        dates, h = m.group(1), h[:m.start()]
    fuller = ''
    m = re.search(r'\(([^)]*)\)', h)
    if m:
        fuller, h = m.group(1).strip(), (h[:m.start()] + h[m.end():]).strip()
    h = re.sub(r'\s+', ' ', h).strip(' ,')
    fam, _, giv = h.partition(', ')
    giv = re.sub(r',\s*(Jr\.?|Sr\.?|III|II|IV)$', r' \1', giv).strip(' ,')
    return fam.strip(), giv.strip(), fuller, dates


def natural(fam, giv):
    suffix = ''
    m = re.match(r'^(.*?)(?:,)?\s+(Jr\.?|Sr\.?|III|II|IV)$', giv)
    if m:
        giv, suffix = m.group(1), ', ' + m.group(2) if m.group(2).startswith(('Jr', 'Sr')) else ' ' + m.group(2)
    return re.sub(r'\s+', ' ', f'{giv} {fam}{suffix}').strip()


def initials_only(giv):
    toks = [t for t in re.split(r'[\s.\-]+', giv) if t]
    return bool(toks) and all(len(t) == 1 for t in toks)


def name_forms(lc_label, variants, key_label):
    fam, giv, fuller, _ = split_heading(lc_label)
    forms = []
    if giv:
        forms.append(natural(fam, giv))
        first = giv.split()[0]
        if not initials_only(first):
            forms.append(natural(fam, first))
        if re.search(r'\b[A-Z]\.\s?[A-Z]\.', giv):
            forms.append(natural(fam, giv.replace('. ', '.')))
    if fuller and giv:
        forms.append(natural(fam, fuller))
        forms.append(natural(fam, fuller.split()[0]))
        # 'Kenneth A. (Kenneth Alan)': fuller form of the middle initials
        g0 = giv.split()[0]
        if not initials_only(g0) and fuller.split()[0] == g0:
            forms.append(natural(fam, fuller))
    if key_label:
        f2, comma, g2 = key_label.partition(', ')
        forms.append(natural(f2, g2) if comma else key_label)
    for v in variants or []:
        f2, g2, ful2, _ = split_heading(v)
        if g2 and not initials_only(g2) and len(forms) < 10:
            forms.append(natural(f2, g2))
    seen, out = set(), []
    for f in forms:
        f = re.sub(r'\s+', ' ', f).strip()
        if f and f not in seen and len(f.split()) >= 2:
            seen.add(f)
            out.append(f)
    return out[:10]


BAD_LABEL = re.compile(r'\d|&|\bet al\b|\b(inc|ltd|society|association|university|college|press|committee|'
                       r'department|institute|museum|library|council|company|commission)\b', re.I)


# ---------------------------------------------------------------- stage 1: pool and internal exclusions

def history_theses(con):
    ok = set()
    for r in csv.DictReader(open(CORPUS / 'dissertations.csv', encoding='utf-8')):
        if r['eligibility'] == 'history_phd':
            ok.add(r['id'])
    con.execute('create temp table histdiss(id varchar)')
    con.executemany('insert into histdiss values (?)', [(x,) for x in ok])
    con.execute("""create temp table hthesis as select distinct n.key from nodes n, unnest(n.anchors) u(a)
        where n.kind='thesis' and (a like 'aha-diss:%' or (a like 'diss-thesis:%' and substr(a, 13) in (select id from histdiss)))""")


def scan_events(keys):
    """Every key-log event on these person keys and on keys merged into them (three generations)."""
    pat = re.compile(r'"(?:key|into)": "(p-\d+)"')
    events, want = {}, set(keys)
    for _ in range(3):
        merged = set()
        for f in sorted(glob.glob(str(ROOT / 'data/identifiers/events-*.jsonl*'))):
            op = gzip.open if f.endswith('.gz') else open
            with op(f, 'rt', encoding='utf-8') as fh:
                for line in fh:
                    if '"key": "p-' not in line:
                        continue
                    ks = pat.findall(line)
                    if not any(k in want for k in ks):
                        continue
                    e = json.loads(line)
                    events[e['seq']] = e
                    if e['event'] == 'merge' and e.get('into') in want and e['key'] not in want:
                        merged.add(e['key'])
        if not merged:
            break
        want |= merged
    return [events[s] for s in sorted(events)]


HIST_ANCHORS = ('aha-phd', 'aha', 'diss-author', 'repo-advisor')


def ties(events):
    """key -> the event after which one key first held both an lcnaf: anchor and a history anchor."""
    anc, tie = defaultdict(dict), {}

    def summ(e):
        return dict(seq=e['seq'], event=e['event'], basis=e.get('basis', ''), decided_by=e.get('decided_by'),
                    evidence=e.get('evidence'), date=e.get('date', '')[:10])

    def check(k, e):
        if k not in tie and any(a.startswith('lcnaf:') for a in anc[k]) and any(a.split(':')[0] in HIST_ANCHORS for a in anc[k]):
            tie[k] = summ(e)
    for e in events:
        k, t = e['key'], e['event']
        if t in ('mint', 'attach'):
            for a in e.get('anchors', []):
                anc[k][a] = summ(e)
            check(k, e)
        elif t == 'detach':
            for a in e.get('anchors', []):
                anc[k].pop(a, None)
        elif t == 'merge':
            into = e['into']
            for a, s in anc.pop(k, {}).items():
                anc[into].setdefault(a, s)
            if k in tie and into not in tie:
                tie[into] = tie[k]
            check(into, e)
    return tie, anc


def tie_class(t):
    """How the LC authority was tied to the history record: title / identifier / review / name / none."""
    if not t:
        return 'none'
    b = t['basis'] or ''
    ev = t.get('evidence') or {}
    if re.search(r'one career on several keys|two family-name forms|name-form-merges', b):
        return 'name'
    if re.search(r'medium:|\(medium', b) and 'outside review' not in b:
        return 'name'
    if re.search(r"LC's notes \(degree\)", b):
        return 'degree note'
    if re.search(r'outside review|reviewed|Sol check|hand review|verdict', b):
        return 'review'
    if re.search(r'deterministic anchor link|ORCID record claims|ISBN|identifier', b):
        return 'identifier'
    if re.search(r'published as a book|thesis of a book|reviewed books|by works|identity by works|titles agree|same works|'
                 r'cited works|cited book|cited person|strong:|its books|same title|dissertation as published|'
                 r'author of AHA dissertation record|reviewed in JSTOR|dissertation published|share their title words|670 names|'
                 r"LC's notes \(title\)|its 670|thesis of", b):
        return 'title'
    if 'canon-map' in b:
        return 'title' if (ev.get('works') and any(ev.get('works'))) or ev.get('lc_record_title') else 'name'
    return 'other'


def open_lists():
    """Person keys on open duplicate, twin, held, possible-same, wrong-anchor or conflict lists. A pair or twin entry
    counts only while another key it names is still a separate active key (an entry whose other keys have since been
    merged into this one is settled); wrong-anchor and conflict lists count as they stand."""
    import sqlite3
    I = ROOT / 'data/identifiers'
    sq = sqlite3.connect(f'file:{ROOT}/build/keylog-state.sqlite?mode=ro', uri=True)
    memo = {}

    def resolve(k):
        if k not in memo:
            cur, seen = k, set()
            while cur not in seen:
                seen.add(cur)
                row = sq.execute('select status, replaced_by from keys where key=?', (cur,)).fetchone()
                if not row:
                    break
                nxt = json.loads(row[1] or '[]')
                if row[0] == 'merged' and len(nxt) == 1:
                    cur = nxt[0]
                else:
                    break
            row = sq.execute('select status from keys where key=?', (cur,)).fetchone()
            memo[k] = (cur, row[0] if row else None)
        return memo[k]
    hits = defaultdict(set)
    pk = re.compile(r'\bp-\d+\b')

    def records(p):
        t = gzip.open(p, 'rt', encoding='utf-8').read() if p.suffix == '.gz' else p.read_text(encoding='utf-8')
        if p.name.endswith(('.json', '.json.gz')):
            d = json.loads(t)
            if isinstance(d, dict) and 'ops' in d:
                d = d['ops']
            items = d if isinstance(d, list) else list(d.values()) if isinstance(d, dict) else [d]
            return [json.dumps(x) for x in items]
        return t.splitlines()[1:]

    def add(path, label, pairwise):
        p = Path(path)
        if not p.exists():
            return
        for rec in records(p):
            ks = set(pk.findall(rec))
            for k in ks:
                if not pairwise:
                    hits[k].add(label)
                    continue
                me = resolve(k)[0]
                if any(resolve(o)[0] != me and resolve(o)[1] in ('active', 'provisional') for o in ks - {k}):
                    hits[me].add(label)
    for f in ['note-review-books-2026-11-14/wrong-anchors.csv', 'note-review-books-2026-11-14/note-books-wrong-anchor.csv']:
        add(I / f, 'wrong-anchor list', False)
    rs = I / 'note-review-books-2026-11-14/note-books-recheck-sample.csv'
    if rs.exists():
        for r in csv.DictReader(open(rs, encoding='utf-8')):
            if any((v or '').strip().lower().startswith('wrong') for v in r.values()):
                for k in pk.findall(' '.join(v or '' for v in r.values())):
                    hits[k].add('wrong-anchor list')
    add(I / 'wikidata-orcid-read-2026-11-14/conflicts.csv', 'wikidata-orcid-read conflict', False)
    add(I / 'wikidata-orcid-read-2026-11-14/possible-duplicates.csv', 'open duplicate review list', True)
    for f in ['career-merges-2026-11-13/review-tier.csv.gz', 'person-dup-merges-2026-11-12/tier-b-review.csv',
              'person-dup-merges-2026-11-12/proposal.json', 'person-dup-merges-2026-11-11/tier-b-review.csv',
              'name-form-merges-2026-11-12/tier-b-review.csv', 'possible-same-nicknames-2026-11-12/pairs.csv']:
        add(I / f, 'open duplicate review list', True)
    for f in glob.glob(str(I / '*/held*.json')):
        if re.search(r'dup|twin|held-lc|wd-lc|review-books-lc|person|namesake|mixed|review-credit|aha-phd-by-works|shared-work', f):
            add(f, 'held twin/duplicate list', True)
    return hits


def build_pool(args):
    import duckdb
    CACHE.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(EXPLORER), read_only=True)
    con.execute("SET memory_limit='6GB'")
    history_theses(con)
    con.execute("""create temp table pers as select key, label, cited from nodes where type='person'
        and key not in (select key from anchors where anchor like 'wd:%')
        and key in (select key from anchors where anchor like 'lcnaf:%')
        and key in (select a."from" from e_authored_f a join nodes n on n.key=a."to" where n.kind='book')""")
    con.execute("""create temp table sig as select key, label, coalesce(cited,0) cited,
        key in (select key from anchors where anchor like 'aha-phd:%') aha_phd,
        key in (select key from anchors where anchor like 'aha:%') aha_dir,
        key in (select a."from" from e_authored_f a where a."to" in (select key from hthesis)) thesis,
        key in (select s."from" from e_supervised_f s where s."to" in (select key from hthesis)) supervised
        from pers""")
    rows = con.execute('select * from sig order by cited desc, key').fetchall()
    cols = ['key', 'label', 'cited', 'aha_phd', 'aha_dir', 'thesis', 'supervised']
    allp = [dict(zip(cols, r)) for r in rows]
    pool = [r for r in allp if r['aha_phd'] or r['aha_dir'] or r['thesis'] or r['supervised']]
    nohs = [r for r in allp if not (r['aha_phd'] or r['aha_dir'] or r['thesis'] or r['supervised']) and r['cited'] >= 50]
    for i, r in enumerate(pool, 1):
        r['rank'] = i
    keys = [r['key'] for r in pool] + [r['key'] for r in nohs]
    con.execute('create temp table k(key varchar)')
    con.executemany('insert into k values (?)', [(x,) for x in keys])
    anchors = defaultdict(list)
    for a, k in con.execute('select anchor, key from anchors where key in (select key from k)').fetchall():
        anchors[k].append(a)
    # own works (years) and roles
    works = defaultdict(list)
    for p, w, kind, y, fy, cited, reviewed, role, ev, lab in con.execute("""select a."from", a."to", n.kind, n.year, n.first_year,
            coalesce(n.cited,0), coalesce(n.reviewed,0), a.role, a.evidence, n.label from e_authored_f a join nodes n on n.key=a."to"
            where a."from" in (select key from k)""").fetchall():
        works[p].append(dict(w=w, kind=kind, year=fy or y, cited=cited, reviewed=reviewed, role=role, ev=ev, label=lab))
    edited = defaultdict(list)
    for p, w, cited, role in con.execute("""select a."from", a."to", coalesce(n.cited,0), a.role from e_edited_f a join nodes n
            on n.key=a."to" where a."from" in (select key from k)""").fetchall():
        edited[p].append(dict(w=w, cited=cited, role=role))
    # theses: own (with institution, year, advisors) — key-log or linked authorship
    theses = defaultdict(list)
    for p, w, y, lab, anc, ev in con.execute("""select a."from", n.key, n.year, n.label, n.anchors, a.evidence from e_authored_f a
            join nodes n on n.key=a."to" where n.key in (select key from hthesis) and a."from" in (select key from k)""").fetchall():
        inst = con.execute("""select i.key, i.label, list_filter(i.anchors, x -> x like 'ror:%') from e_awarded_by_f b join nodes i
            on i.key=b."to" where b."from"=?""", [w]).fetchall()
        adv = con.execute("""select s."from", n.label, list_filter(n.anchors, x -> x like 'wd:%'), s.resolution from e_supervised_f s
            join nodes n on n.key=s."from" where s."to"=?""", [w]).fetchall()
        theses[p].append(dict(w=w, year=y, title=lab, anchors=list(anc), ev=ev,
                              inst=[dict(key=i[0], label=i[1], ror=[x[4:] for x in i[2]]) for i in inst],
                              advisors=[dict(key=a[0], label=a[1], wd=[x[3:] for x in a[2]], res=a[3]) for a in adv]))
    possibly = set(x for (x,) in con.execute("""select "from" from e_possibly_same_f union select "to" from e_possibly_same_f""").fetchall())
    hidden = set(x for (x,) in con.execute('select person from dup_hide union select hidden from dup_hide union select shown from dup_hide').fetchall())
    # LC records
    lcids = sorted({a[6:] for k in keys for a in anchors[k] if a.startswith('lcnaf:')})
    lc = {}
    c2 = duckdb.connect()
    c2.execute('create temp table l(lcid varchar)')
    c2.executemany('insert into l values (?)', [(x,) for x in lcids])
    for r in c2.execute(f"select lcid,label,variants,birth,death,undifferentiated,deprecated,use_instead,external,sources from '{LC_NAMES}' where lcid in (select lcid from l)").fetchall():
        lc[r[0]] = dict(label=r[1], variants=list(r[2] or []), birth=r[3], death=r[4], undiff=r[5], deprecated=r[6],
                        use_instead=list(r[7] or []), external=list(r[8] or []), sources=list(r[9] or []))
    for r in c2.execute(f"select lcid, notes, affiliations, fields from '{LC_NOTES}' where lcid in (select lcid from l)").fetchall():
        if r[0] in lc:
            lc[r[0]].update(notes=list(r[1] or []), affiliations=[dict(x) for x in (r[2] or [])], fields=list(r[3] or []))
    # members (possible-same marks) from the key-log cache, read-only
    import sqlite3
    sq = sqlite3.connect(f'file:{ROOT}/build/keylog-state.sqlite?mode=ro', uri=True)
    marks = defaultdict(list)
    for k in keys:
        for (m,) in sq.execute("select member from members where key=? and (member like 'possible-same:%' or member like 'very-likely-same:%')", (k,)):
            marks[k].append(m)
    print('scanning key-log events', len(pool), flush=True)
    tie, _ = ties(scan_events([r['key'] for r in pool]))
    lists = open_lists()

    out = []
    for r in pool + nohs:
        k = r['key']
        a = anchors[k]
        r['anchors'] = sorted(a)
        r['lcnaf'] = sorted(x[6:] for x in a if x.startswith('lcnaf:'))
        r['lc'] = lc.get(r['lcnaf'][0]) if r['lcnaf'] else None
        r['theses'] = theses.get(k, [])
        own = [w for w in works[k] if w['kind'] in ('book', 'article', 'chapter') and (w['role'] in (None, 'author', 'unknown'))]
        ys = sorted(w['year'] for w in own if w['year'] and 1700 < w['year'] < 2030)
        r['work_years'] = [ys[0], ys[-1]] if ys else []
        r['books'] = sorted([dict(w=w['w'], label=w['label'], year=w['year'], reviewed=w['reviewed'], cited=w['cited'], role=w['role'], ev=w['ev'])
                             for w in works[k] if w['kind'] == 'book'], key=lambda x: (-x['reviewed'] - x['cited'], x['year'] or 0))[:8]
        EDN = ('edition-editor', 'translator', 'introducer', 'series-editor', 'contributor')
        cited_own = sum(w['cited'] for w in works[k] if w['role'] not in EDN)
        cited_other = sum(w['cited'] for w in works[k] if w['role'] in EDN) + \
            sum(w['cited'] for w in edited[k] if w['role'] in ('edition-editor', 'translator', 'introducer', 'series-editor'))
        r['cited_own'], r['cited_edition_roles'] = cited_own, cited_other
        t = tie.get(k)
        r['tie'] = dict(cls=tie_class(t), basis=(t or {}).get('basis', '')[:400], event=(t or {}).get('event'), seq=(t or {}).get('seq'))
        r['excl'] = exclusions(r, lists.get(k, set()), k in possibly or bool(marks[k]), k in hidden)
        out.append(r)
    json.dump(dict(pool=out[:len(pool)], nohs=out[len(pool):]), open(CACHE / 'pool.json', 'w'), default=str)
    c = Counter(x for r in out[:len(pool)] for x in r['excl'])
    print(len(pool), 'pool;', len(nohs), 'no-signal cited>=50;', 'exclusion reasons (any):', c.most_common())
    print('tie classes', Counter(r['tie']['cls'] for r in out[:len(pool)]).most_common())


def exclusions(r, lists, possibly, hidden):
    ex = []
    lcr = r['lc']
    if lists:
        ex.extend(sorted(lists))
    if possibly:
        ex.append('possibly-same edge or mark')
    if hidden:
        ex.append('duplicate-hide pair')
    if len(r['lcnaf']) != 1:
        ex.append('two LC authorities on the key')
    if not lcr:
        ex.append('LC authority not in the LC file')
        return ex
    if lcr['undiff']:
        ex.append('LC authority undifferentiated')
    if lcr['deprecated'] or lcr['use_instead']:
        ex.append('LC authority deprecated')
    if len([a for a in r['anchors'] if a.startswith('aha-phd:')]) > 1:
        ex.append('two AHA PhD records on the key')
    fam, giv, fuller, dates = split_heading(lcr['label'])
    if not giv or BAD_LABEL.search(fam + ' ' + giv):
        ex.append('label not a clean personal name')
    elif initials_only(giv) and not fuller:
        ex.append('initial-only name')
    if r['tie']['cls'] in ('name', 'none', 'other'):
        ex.append(f"LC tie {r['tie']['cls']}")
    by, dy = year_of(lcr.get('birth')) or year_of(dates.split('-')[0] if dates else ''), year_of(lcr.get('death'))
    if not dy and dates and re.search(r'-\d{4}', dates):
        dy = year_of(dates.split('-')[1])
    if dy and dy < 1900:
        ex.append('dead before 1900')
    ys = r['work_years']
    if ys and ys[1] - ys[0] > 55:
        ex.append('works span over 55 years')
    phd = [t['year'] for t in r['theses'] if t['year']]
    if by and phd and not (20 <= min(phd) - by <= 75):
        ex.append('LC birth year does not fit the PhD year')
    if by and ys and ys[0] < by + 18:
        ex.append('work before LC birth + 18')
    if dy and phd and min(phd) > dy:
        ex.append('PhD after LC death')
    if phd and ys and ys[0] < min(phd) - 25:
        ex.append('works start 25+ years before the PhD')
    if r['cited_edition_roles'] > r['cited_own']:
        ex.append('citations mostly through edition/translator roles')
    return ex


# ---------------------------------------------------------------- stage 2: Wikidata screen

def load_cache(name):
    p = CACHE / name
    return json.load(open(p)) if p.exists() else {}


def save_cache(name, d):
    tmp = CACHE / (name + '.tmp')
    json.dump(d, open(tmp, 'w'))
    tmp.replace(CACHE / name)


def id_screen(rows, cache):
    """LC id (P244), LC's own Wikidata link, VIAF/ISNI/ORCID/GND -> items (humans only, redirects followed by QLever's
    current data: redirected items carry no statements)."""
    todo = [r for r in rows if r['key'] not in cache]
    props = dict(lcnaf='P244', viaf='P214', isni='P213', orcid='P496', gnd='P227')
    for i in range(0, len(todo), 150):
        chunk = todo[i:i + 150]
        found = defaultdict(set)
        for scheme, prop in props.items():
            want = defaultdict(set)
            for r in chunk:
                vals = [a.split(':', 1)[1] for a in r['anchors'] if a.startswith(scheme + ':')]
                if scheme == 'viaf' and r['lc']:
                    vals += [re.sub(r'\D', '', e.rsplit('/', 1)[1]) for e in r['lc']['external'] if re.search(r'viaf\.org/viaf/\d+$', e)]
                if scheme == 'isni' and r['lc']:
                    vals += [e.rsplit('/', 1)[1] for e in r['lc']['external'] if 'isni.org/isni/' in e]
                for v in vals:
                    if scheme == 'isni':
                        v = re.sub(r'\s', '', v)
                    want[v].add(r['key'])
            if not want:
                continue
            vs = ' '.join(lit(v) for v in want)
            if scheme == 'isni':   # Wikidata writes ISNI with spaces
                vs = ' '.join(lit(' '.join(v[j:j + 4] for j in range(0, 16, 4))) for v in want if len(v) == 16)
            for b in qlever('SELECT ?v ?i WHERE { VALUES ?v {%s} ?i wdt:%s ?v ; wdt:P31 wd:Q5 }' % (vs, prop)):
                v = val(b, 'v').replace(' ', '') if scheme == 'isni' else val(b, 'v')
                for k in want.get(v, ()):
                    found[k].add((val(b, 'i'), scheme))
        for r in chunk:
            hits = defaultdict(list)
            for q, s in found.get(r['key'], ()):
                hits[q].append(s)
            if r['lc']:
                for e in r['lc']['external']:
                    m = re.search(r'wikidata\.org/entity/(Q\d+)$', e)
                    if m:
                        hits[m.group(1)].append('lc-record-link')
            cache[r['key']] = {q: sorted(set(s)) for q, s in hits.items()}
        save_cache('id_screen.json', cache)
        print('id screen', i + len(chunk), '/', len(todo), flush=True)
    return cache


LANGS = ('en', 'mul', 'de', 'fr', 'es', 'pt', 'it', 'nl', 'sv', 'da', 'nb')


def name_query(chunk):
    want = defaultdict(set)
    for r in chunk:
        for f in name_forms(r['lc']['label'], r['lc']['variants'], r['label']):
            want[f].add(r['key'])
    vals = [f'{lit(n)}@{l}' for n in want for l in LANGS]
    rows_ = []
    for j in range(0, len(vals), 200):              # the endpoint refuses request bodies over about 12 kB
        vs = ' '.join(vals[j:j + 200])
        for pred in ('rdfs:label', 'skos:altLabel'):    # one query each: the UNION form makes QLever sort every label
            rows_ += qlever('SELECT DISTINCT ?n ?i WHERE { VALUES ?n {%s} ?i %s ?n . ?i wdt:P31 wd:Q5 }' % (vs, pred), tries=3)
        # items with no 'instance of' at all (empty or half-made items: hand check 2026-11-14, Delgado)
        rows_ += qlever('SELECT DISTINCT ?n ?i WHERE { VALUES ?n {%s} ?i rdfs:label ?n . '
                        'FILTER NOT EXISTS { ?i wdt:P31 ?c } FILTER(STRSTARTS(STR(?i), "http://www.wikidata.org/entity/Q")) }' % vs, tries=3)
    got = defaultdict(set)
    for b in rows_:
        for k in want.get(val(b, 'n'), ()):
            got[k].add(val(b, 'i'))
    return got


def name_screen(rows, cache):
    """Same-name humans; a chunk that fails is split until the failing person is found (kept as 'error': held)."""
    todo = [r for r in rows if r['key'] not in cache or cache[r['key']] == ['ERROR']]

    def run(chunk):
        try:
            got = name_query(chunk)
            for r in chunk:
                cache[r['key']] = sorted(got.get(r['key'], ()))
        except SystemExit:
            if len(chunk) == 1:
                cache[chunk[0]['key']] = ['ERROR']
                return
            run(chunk[:len(chunk) // 2])
            run(chunk[len(chunk) // 2:])
    for i in range(0, len(todo), 20):
        run(todo[i:i + 20])
        save_cache('name_screen-v2.json', cache)
        print('name screen', i + 20, '/', len(todo), flush=True)
    return cache


def item_facts(qids, cache):
    todo = sorted(set(qids) - set(cache))
    for i in range(0, len(todo), 200):
        chunk = todo[i:i + 200]
        vs = ' '.join(f'wd:{q}' for q in chunk)
        d = {q: dict(label='', desc='', birth=[], death=[], occ=[], lc=[], p69=[], p108=[], orcid=[], viaf=[]) for q in chunk}
        for b in qlever('SELECT ?i ?l ?d WHERE { VALUES ?i {%s} OPTIONAL { ?i rdfs:label ?l FILTER(lang(?l)="en" || lang(?l)="mul") } '
                        'OPTIONAL { ?i schema:description ?d FILTER(lang(?d)="en") } }' % vs):
            q = val(b, 'i')
            d[q]['label'] = d[q]['label'] or (val(b, 'l') or '')
            d[q]['desc'] = d[q]['desc'] or (val(b, 'd') or '')
        for prop, f in (('P569', 'birth'), ('P570', 'death'), ('P244', 'lc'), ('P69', 'p69'), ('P108', 'p108'), ('P496', 'orcid'), ('P214', 'viaf')):
            for b in qlever('SELECT ?i ?v WHERE { VALUES ?i {%s} ?i wdt:%s ?v }' % (vs, prop)):
                v = val(b, 'v')
                if f in ('birth', 'death'):
                    # QLever writes low-precision dates (century, millennium) as Jan 1 of a round year: not a year
                    if not (v and re.match(r'^\d{4}-', v)) or (re.match(r'^\d{2}00-01-01T', v)):
                        continue
                    v = v[:4]
                d[val(b, 'i')][f].append(v)
        for b in qlever('SELECT ?i ?o ?ol WHERE { VALUES ?i {%s} ?i wdt:P106 ?o OPTIONAL { ?o rdfs:label ?ol FILTER(lang(?ol)="en") } }' % vs):
            d[val(b, 'i')]['occ'].append(val(b, 'ol') or val(b, 'o'))
        cache.update(d)
        save_cache('items-v2.json', cache)
    return cache


ACADEMIC = re.compile(r'histor|professor|scholar|academic|research|writer|author|lecturer|teacher|educator|archivist|librar|'
                      r'economist|sociolog|anthropolog|politic(al)? scien|philosoph|archaeolog|editor|university|geograph|'
                      r'theolog|classic|linguist|critic|biograph|essayist|translator|scientist|curator|'
                      r'humanist|demograph|orientalist|egyptolog|byzantin|medievalist|sinolog|japanolog|art histor|musicolog', re.I)


def judge_name(r, it, institutions):
    """A same-name human: 'namesake' when a fact rules it out, else 'possible' (held); 'possible+fact' when the birth
    year agrees and a second fact (school or employer QID, or historian) agrees too."""
    lcr = r['lc']
    by = year_of(lcr.get('birth')) or year_of(split_heading(lcr['label'])[3])
    phd = min([t['year'] for t in r['theses'] if t['year']] or [None]) if r['theses'] else None
    ys = r['work_years']
    reasons = []
    if it['lc'] and r['lcnaf'] and r['lcnaf'][0] not in it['lc']:
        reasons.append('item has another LC authority')
    ib = sorted({int(x) for x in it['birth'] if x and x.isdigit()})
    idd = sorted({int(x) for x in it['death'] if x and x.isdigit()})
    if by and ib and all(abs(b - by) > 1 for b in ib):
        reasons.append(f'birth {ib} vs LC {by}')
    if ib and phd and all(phd - b < 20 or phd - b > 75 for b in ib):
        reasons.append(f'birth {ib} does not fit PhD {phd}')
    if ib and ys and all(ys[0] < b + 16 for b in ib):
        reasons.append(f'born {ib} after first work {ys[0]} - 16')
    if idd and ys and all(d < ys[0] for d in idd):
        reasons.append(f'died {idd} before first work {ys[0]}')
    ours = [a[6:] for a in r['anchors'] if a.startswith('orcid:')]
    if ours and it.get('orcid') and not set(ours) & set(it['orcid']):
        reasons.append('item has another ORCID')
    fam, giv, fuller, _ = split_heading(lcr['label'])
    g_ours = (fuller or giv).replace('.', ' ').split()
    g_it = [t for t in re.sub(r'[.,]', ' ', it['label']).split() if fold(t) not in fold(fam).split()]
    if len(g_ours) >= 2 and len(g_it) >= 2 and g_ours[0][0].lower() == g_it[0][0].lower() and g_ours[1][0].lower() != g_it[1][0].lower():
        reasons.append(f'middle name differs ({" ".join(g_ours)} / {" ".join(g_it)})')
    occ_txt = ' '.join(it['occ']) + ' ' + it['desc']
    if (it['occ'] or it['desc']) and not ACADEMIC.search(occ_txt):
        reasons.append('occupation/description not scholarly: ' + occ_txt[:80])
    if reasons:
        return 'namesake', reasons
    fact = []
    if by and by in ib:
        fact.append('birth year agrees')
    schools = {i for t in r['theses'] for x in t['inst'] for i in institutions.get(x['key'], [])}
    if schools & set(it['p69'] + it['p108']):
        fact.append('school or employer agrees')
    if re.search(r'histor', occ_txt, re.I):
        fact.append('historian')
    if len(fact) >= 2:
        return 'possible+fact', fact
    return 'possible', fact


def institution_qids(rows, cache):
    rors = {x['key']: x['ror'] for r in rows for t in r['theses'] for x in t['inst']}
    want = sorted({ror for v in rors.values() for ror in v} - set(cache.get('ror', {})))
    cache.setdefault('ror', {})
    for i in range(0, len(want), 300):
        chunk = want[i:i + 300]
        got = defaultdict(set)
        for b in qlever('SELECT ?r ?i WHERE { VALUES ?r {%s} ?i wdt:P6782 ?r }' % ' '.join(lit(x) for x in chunk)):
            got[val(b, 'r')].add(val(b, 'i'))
        for x in chunk:
            cache['ror'][x] = sorted(got.get(x, ()))
    save_cache('institutions.json', cache)
    return {k: sorted({q for ror in v for q in cache['ror'].get(ror, [])}) for k, v in rors.items()}


def screen(args):
    P = json.load(open(CACHE / 'pool.json'))
    pool, nohs = P['pool'], P['nohs']
    idc, nmc, itc, instc = load_cache('id_screen.json'), load_cache('name_screen-v2.json'), load_cache('items-v2.json'), load_cache('institutions.json')
    keyed_wd = keyed_qids()
    res, n_noitem = {}, 0
    step = 600
    pos = 0
    while n_noitem < TARGET and pos < len(pool):
        block = [r for r in pool[pos:pos + step] if not r['excl']]
        pos += step
        id_screen(block, idc)
        rest = [r for r in block if not idc[r['key']]]
        name_screen(rest, nmc)
        item_facts([q for r in block for q in list(idc[r['key']]) + nmc.get(r['key'], []) if q != 'ERROR'], itc)
        inst = institution_qids(block, instc)
        for r in block:
            res[r['key']] = classify(r, idc, nmc, itc, inst, keyed_wd)
        n_noitem = sum(1 for r in pool[:pos] if r['key'] in res and res[r['key']]['status'] == 'no item')
        print('screened to rank', min(pos, len(pool)), 'no-item', n_noitem, flush=True)
    # no-history-signal people cited >= 50: identifier screen only (for the attach proposal)
    nb = [r for r in nohs if 'two LC authorities on the key' not in r['excl']]
    id_screen(nb, idc)
    item_facts([q for r in nb for q in idc[r['key']]], itc)
    res_nohs = {r['key']: classify(r, idc, {}, itc, {}, keyed_wd, names=False) for r in nb}
    json.dump(dict(res=res, res_nohs=res_nohs, screened_to=pos), open(CACHE / 'screen.json', 'w'))


def keyed_qids():
    import duckdb
    con = duckdb.connect(str(EXPLORER), read_only=True)
    return {a[3:]: k for a, k in con.execute("select anchor, key from anchors where anchor like 'wd:%'").fetchall()}


def classify(r, idc, nmc, itc, inst, keyed_wd, names=True):
    hits = idc.get(r['key'], {})
    if hits:
        qs = sorted(hits)
        taken = {q: keyed_wd[q] for q in qs if q in keyed_wd}
        det = {q: dict(via=hits[q], label=itc.get(q, {}).get('label', ''), desc=itc.get(q, {}).get('desc', ''),
                       lc=itc.get(q, {}).get('lc', []), keyed_on=taken.get(q)) for q in qs}
        if len(qs) > 1:
            return dict(status='existing: several items', items=det)
        if taken:
            return dict(status='existing: item already on another key', items=det)
        it = itc.get(qs[0], {})
        if it.get('lc') and r['lcnaf'] and r['lcnaf'][0] not in it['lc'] and 'lcnaf' not in hits[qs[0]]:
            return dict(status='existing: item carries another LC id', items=det)
        return dict(status='existing by identifier', items=det)
    if not names:
        return dict(status='no identifier match', items={})
    cands = {}
    if nmc.get(r['key']) == ['ERROR']:
        return dict(status='held: name screen failed', items={})
    for q in nmc.get(r['key'], []):
        it = itc.get(q)
        if not it:
            continue
        verdict, why = judge_name(r, it, inst)
        cands[q] = dict(verdict=verdict, why=why, label=it['label'], desc=it['desc'], birth=it['birth'], occ=it['occ'][:5],
                        keyed_on=keyed_wd.get(q))
    live = {q: c for q, c in cands.items() if c['verdict'] != 'namesake'}
    if any(c['verdict'] == 'possible+fact' for c in live.values()):
        return dict(status='same-name item with agreeing facts', items=cands)
    if live:
        return dict(status='held: possible same-name item', items=cands)
    return dict(status='no item', items=cands, institutions=inst)


# ---------------------------------------------------------------- stage 3: statements, batches, proposals

def ref_lc(lcid):
    return f'S248|{LC_NAF}|S244|"{lcid}"|S813|{TODAY}'


def ref_url(url):
    return f'S854|"{url}"|S813|{TODAY}'


def repository_urls():
    urls = {}
    for f in glob.glob(str(CORPUS / 'downloads*.jsonl')):
        for line in open(f, encoding='utf-8'):
            if '"item_url"' in line:
                r = json.loads(line)
                urls[r['id']] = r['item_url']
    return urls


def thesis_ref(t, urls):
    for a in t['anchors']:
        if a.startswith('diss-thesis:') and a[12:] in urls:
            return urls[a[12:]], 'thesis repository record'
    return AHA_URL, 'AHA Directory of History Dissertations'


def lobid_gnd(gnd, cache):
    if gnd in cache:
        return cache[gnd]
    try:
        req = urllib.request.Request(f'https://lobid.org/gnd/{gnd}.json', headers={'User-Agent': UA})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        same = [s.get('id', '') for s in d.get('sameAs', [])]
    except Exception:  # noqa: BLE001
        same = None
    time.sleep(0.5)
    cache[gnd] = same
    return same


def orcid_public(orcid, cache):
    if orcid in cache:
        return cache[orcid]
    try:
        req = urllib.request.Request(f'https://pub.orcid.org/v3.0/{orcid}/person', headers={'User-Agent': UA, 'Accept': 'application/json'})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        n = d.get('name') or {}
        name = ' '.join(filter(None, [(n.get('given-names') or {}).get('value'), (n.get('family-name') or {}).get('value')]))
    except Exception:  # noqa: BLE001
        name = None
    time.sleep(0.5)
    cache[orcid] = name
    return name


def employer_clauses(notes):
    clauses = [c for n in notes for c in re.split(r'[;()]', n.split(' :: ', 1)[-1])]
    return ' '.join(c for c in clauses if JOB.search(c) and not DOCTORATE.search(c)).replace(' Press', ' PRESS')


def write(args):
    import duckdb
    P = json.load(open(CACHE / 'pool.json'))
    S = json.load(open(CACHE / 'screen.json'))
    pool, res = P['pool'], S['res']
    instc, itc = load_cache('institutions.json'), load_cache('items-v2.json')
    gndc, orcc = load_cache('gnd.json'), load_cache('orcid.json')
    urls = repository_urls()
    con = duckdb.connect(str(EXPLORER), read_only=True)
    insts = [(k, re.sub(r'^The ', '', lab), [a[4:] for a in anc if a.startswith('ror:')])
             for k, lab, anc in con.execute("select key, label, anchors from nodes where type='institution'").fetchall()]
    ror_q = {r: q for r, q in instc.get('ror', {}).items()}
    # walk the ranking
    counts, pilot, existing, held, excluded, conflicts = Counter(), [], [], [], [], []
    last = None
    for r in pool:
        if len(pilot) >= TARGET:
            break
        last = r
        if r['excl']:
            counts['excluded'] += 1
            for x in r['excl']:
                counts['excluded: ' + x] += 1
            counts['excluded (first reason): ' + r['excl'][0]] += 1
            excluded.append(r)
            continue
        s = res.get(r['key'])
        if s is None:
            raise SystemExit(f"rank {r['rank']} not screened; run the screen stage further")
        counts[s['status']] += 1
        if s['status'] == 'no item':
            pilot.append((r, s))
        elif s['status'] == 'existing by identifier':
            existing.append((r, s))
        elif s['status'].startswith('existing'):
            conflicts.append((r, s))
        else:
            held.append((r, s))
    counts['rank of the last row met'] = last['rank']
    counts['cited of the last row met'] = last['cited']
    OUT.mkdir(parents=True, exist_ok=True)

    # statements
    out_rows, qs_batches = [], []
    lines_all = []
    for idx, (r, s) in enumerate(pilot):
        lcid = r['lcnaf'][0]
        lcr = r['lc']
        fam, giv, fuller, dates = split_heading(lcr['label'])
        label = natural(fam, giv)
        aliases = []
        if fuller:
            fg = fuller if not initials_only(giv) or len(fuller.split()) >= len(giv.split()) else fuller
            aliases.append(natural(fam, fg))
        f2, comma, g2 = r['label'].partition(', ')
        kl = natural(f2, g2) if comma else r['label']
        if kl != label:
            aliases.append(kl)
        norm = lambda x: re.sub(r'[\W_]+', '', fold(x))
        aliases = [a for i, a in enumerate(aliases) if norm(a) != norm(label) and norm(a) not in [norm(y) for y in aliases[:i]]]
        occ_basis = 'aha-phd' if r['aha_phd'] else 'history thesis' if r['thesis'] else None
        sig = ';'.join(x for x in ('aha_phd', 'aha_dir', 'thesis', 'supervised') if r[x])
        theses = [t for t in r['theses'] if t['inst']]
        th = sorted(theses, key=lambda t: t['year'] or 9999)[0] if theses else (r['theses'][0] if r['theses'] else None)
        desc = 'historian' if occ_basis else ''
        same_label_desc = [q for q, c in s['items'].items() if c.get('label') == label and c.get('desc') == desc]
        if desc and same_label_desc:
            desc = f'historian (PhD {th["year"]})' if th and th.get('year') else 'historian and author'
        st = []   # (prop, value, qualifiers, reference, note)
        st.append(('P31', 'Q5', '', ref_lc(lcid), 'LC name authority'))
        if occ_basis:
            u, what = thesis_ref(th, urls) if th else (AHA_URL, 'AHA')
            st.append(('P106', HISTORIAN, '', ref_url(u), f'history PhD ({what})'))
        st.append(('P244', f'"{lcid}"', '', f'S248|{LC_NAF}|S813|{TODAY}', 'LC name authority'))
        for e in lcr['external']:
            m = re.search(r'viaf\.org/viaf/(\d+)$', e)
            if m:
                st.append(('P214', f'"{m.group(1)}"', '', ref_lc(lcid), 'VIAF id printed in the LC record'))
            m = re.search(r'isni\.org/isni/(\d{15}[\dX])$', e)
            if m:
                v = m.group(1)
                st.append(('P213', '"' + ' '.join(v[j:j + 4] for j in range(0, 16, 4)) + '"', '', ref_lc(lcid), 'ISNI printed in the LC record'))
        for a in r['anchors']:
            if a.startswith('gnd:'):
                same = lobid_gnd(a[4:], gndc)
                if same and any(x.rstrip('/').endswith('/' + lcid) for x in same):
                    st.append(('P227', f'"{a[4:]}"', '', f'S248|Q36578|S227|"{a[4:]}"|S813|{TODAY}', 'GND record names this LC authority'))
            if a.startswith('orcid:'):
                nm = orcid_public(a[6:], orcc)
                if nm and fold(fam).split()[-1] in fold(nm):
                    st.append(('P496', f'"{a[6:]}"', '', ref_url(f'https://orcid.org/{a[6:]}'), f'public ORCID record ({nm})'))
        thesis_note = ''
        if th:
            u, what = thesis_ref(th, urls)
            qids = sorted({q for x in th['inst'] for ror in x['ror'] for q in ror_q.get(ror, [])})
            if len(qids) == 1:
                qual = f'|P512|{PHD}' + (f'|P582|+{th["year"]}-00-00T00:00:00Z/9' if th.get('year') else '')
                st.append(('P69', qids[0], qual, ref_url(u), f'doctorate {th["inst"][0]["label"]} {th.get("year") or ""} ({what})'))
            else:
                thesis_note = f'school QID not unique ({qids})'
            for adv in th['advisors']:
                if len(adv['wd']) == 1:
                    st.append(('P184', adv['wd'][0], '', ref_url(u), f'advisor {adv["label"]} ({what})'))
        # employer: institutions named in LC job clauses
        emp = employer_clauses(lcr.get('notes', []))
        seen_emp, spans = set(), []
        for k, name, rors in insts:
            short = name.replace('University of ', 'Univ. of ')
            if len(name) <= 8:
                continue
            for m in re.finditer(rf'(?<![A-Za-z])(?:{re.escape(name)}|{re.escape(short)})(?! PRESS)', emp):
                spans.append((m.start(), m.end(), name, rors))
        for a, b, name, rors in spans:
            if any(a2 <= a and b <= b2 and (b2 - a2) > (b - a) for a2, b2, _, _ in spans):
                continue      # 'York University' inside 'New York University'
            before = emp[max(0, a - 90):a]
            jobs = list(JOB.finditer(before))
            if not jobs or re.search(r'\b(?:B\.\s?A|M\.\s?A|B\.\s?S|M\.\s?S|Ph\.?\s?D|degree|educat|graduat|studied|alumn)', before[jobs[-1].end():], re.I):
                continue      # a post must be named right before the institution, with no degree between them
            qids = sorted({q for ror in rors for q in ror_q.get(ror, [])})
            if len(qids) == 1 and qids[0] not in seen_emp:
                seen_emp.add(qids[0])
                st.append(('P108', qids[0], '', ref_lc(lcid), f'employer {name} (LC note job clause)'))
        by = year_of(lcr.get('birth')) or (year_of(dates) if dates and not dates.startswith('-') else None)
        if by:
            st.append(('P569', f'+{by}-00-00T00:00:00Z/9', '', ref_lc(lcid), 'birth year printed in the LC authority'))
        lines = ['CREATE', f'LAST|Len|"{label}"']
        if desc:
            lines.append(f'LAST|Den|"{desc}"')
        for a in aliases:
            lines.append(f'LAST|Aen|"{a}"')
        for p, v, q, ref, _ in st:
            lines.append(f'LAST|{p}|{v}{q}|{ref}')
        lines_all.append(lines)
        out_rows.append(dict(
            pilot_rank=idx + 1, pool_rank=r['rank'], key=r['key'], cited=r['cited'], label=label, aliases=' | '.join(aliases),
            description=desc, signals=sig, occupation_basis=occ_basis or 'NONE: AHA directory listing or supervision only (question for the user)',
            lcnaf=lcid, lc_heading=lcr['label'], lc_tie=r['tie']['cls'], lc_tie_basis=r['tie']['basis'][:300],
            thesis=(f'{th["title"]} ({th["inst"][0]["label"] if th and th["inst"] else "?"}, {th.get("year")})' if th else ''),
            books='; '.join(f'{b["label"][:80]} ({b["year"]})' for b in r['books'][:3]),
            statements=' || '.join(f'{p}={v}{q} [{note}]' for p, v, q, ref, note in st),
            references=' || '.join(f'{p}: {ref}' for p, v, q, ref, note in st),
            name_candidates_ruled_out='; '.join(f'{q} {c["label"]} ({"; ".join(c["why"])[:120]})' for q, c in s['items'].items()),
            notes=thesis_note))
    save_cache('gnd.json', gndc)
    save_cache('orcid.json', orcc)
    with open(OUT / 'pilot-500.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    for b in range(0, len(lines_all), 100):
        (OUT / f'pilot-batch-{b // 100 + 1:02d}.qs').write_text('\n'.join(l for ls in lines_all[b:b + 100] for l in ls) + '\n', encoding='utf-8')

    # held same-name
    with open(OUT / 'held-same-name.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['pool_rank', 'key', 'cited', 'label', 'lcnaf', 'lc_heading', 'status', 'item', 'item_label', 'item_desc', 'item_birth', 'item_occupations', 'verdict', 'why'])
        for r, s in held:
            for q, c in s['items'].items():
                if c['verdict'] != 'namesake':
                    w.writerow([r['rank'], r['key'], r['cited'], r['label'], r['lcnaf'][0], r['lc']['label'], s['status'], q, c['label'], c['desc'],
                                ','.join(c['birth']), ','.join(c['occ']), c['verdict'], '; '.join(c['why'])])
    # existing items: attach proposal (identifier tier) + conflicts
    ops, prow = [], []
    nohs_ok = [(r, S['res_nohs'][r['key']]) for r in P['nohs'] if S['res_nohs'].get(r['key'], {}).get('status') == 'existing by identifier']
    for group, items in (('history signal', existing), ('no history signal, cited>=50', nohs_ok)):
        for r, s in items:
            (q, d), = s['items'].items()
            if not {'lcnaf', 'lc-record-link'} & set(d['via']):
                # VIAF/GND/ISNI alone: our own VIAF/GND anchors are sometimes another person's (Sager, Clark, Thomas,
                # Holmes): listed for review, not proposed
                prow.append([group + ' | REVIEW: VIAF/GND/ISNI only, not proposed', r['key'], r['label'], r['cited'], q, d['label'], d['desc'], ','.join(d['via'])])
                continue
            ops.append(dict(event='attach', key=r['key'], anchors=[f'wd:{q}'], aliases=[], members=['wd-via:wikidata-pilot-2026-11-14'],
                            basis=f"Wikidata {q} ({d['label']}) carries this key's identifier ({', '.join(d['via'])}): "
                                  f"read on QLever 2026-11-14 (wikidata-pilot-2026-11-14)"))
            prow.append([group, r['key'], r['label'], r['cited'], q, d['label'], d['desc'], ','.join(d['via'])])
    proposal = dict(basis='Wikidata items that carry the key\'s LC authority (P244) or that the LC record itself links, '
                          'found by the Wikidata pilot screen 2026-11-14; NOT applied',
                    decided_by='rule', ops=ops)
    (OUT / 'existing-items-proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    with open(OUT / 'existing-items.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['group', 'key', 'label', 'cited', 'item', 'item_label', 'item_desc', 'via'])
        w.writerows(prow)
        for r, s in conflicts:
            for q, d in s['items'].items():
                w.writerow(['CONFLICT: ' + s['status'], r['key'], r['label'], r['cited'], q, d['label'], d['desc'], ','.join(d['via']) + (f" keyed on {d['keyed_on']}" if d.get('keyed_on') else '')])
    fact_rows = [(r, s) for r, s in held if s['status'] == 'same-name item with agreeing facts']
    with open(OUT / 'excluded.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['pool_rank', 'key', 'cited', 'label', 'reasons', 'lc_tie_basis'])
        for r in excluded:
            w.writerow([r['rank'], r['key'], r['cited'], r['label'], '; '.join(r['excl']), r['tie']['basis'][:200]])
    nohs_counts = Counter()
    for r in P['nohs']:
        st_ = S['res_nohs'].get(r['key'], {}).get('status', 'not screened (two LC ids)')
        band = '100+' if r['cited'] >= 100 else '50-99'
        nohs_counts[f'{band}: {st_}'] += 1
    rep = dict(pool=len(pool), counts=dict(counts), pilot=len(pilot), existing_identifier=len(existing), conflicts=len(conflicts),
               held=len(held), same_name_with_facts=len(fact_rows), proposal_ops=len(ops),
               existing_review_only=dict(Counter(x[0] for x in prow if 'REVIEW' in x[0])),
               proposal_ops_by_group=dict(Counter(x[0] for x in prow if 'REVIEW' not in x[0])), no_signal_cited50=dict(nohs_counts),
               signals_in_pilot=dict(Counter(x['signals'] for x in out_rows)),
               occupation_basis_in_pilot=dict(Counter(x['occupation_basis'] for x in out_rows)),
               statements_in_pilot=dict(Counter(p for x in out_rows for p in re.findall(r'(P\d+)=', x['statements']))),
               tie_classes_in_pilot=dict(Counter(x['lc_tie'] for x in out_rows)),
               tie_classes_in_pool=dict(Counter(r['tie']['cls'] for r in pool)),
               exclusions_whole_pool=dict(Counter(x for r in pool for x in r['excl'])))
    try:
        sys.path.insert(0, str(ROOT / 'scripts'))
        import identifiers as I
        import keylog_snapshot as KS
        I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
        state = KS.read_state()
        events, _ = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
        rep['proposal_dry_run_events'] = len(events)
    except Exception as e:  # noqa: BLE001
        rep['proposal_dry_run_error'] = repr(e)[:500]
    (OUT / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(rep, indent=1))


def verify(args):
    """Every item a pilot statement points to (school, employer, advisor) read back from Wikidata: its English label
    beside the name in our data, and whether a school/employer item carries a ROR id and an advisor item is human."""
    rows = list(csv.DictReader(open(OUT / 'pilot-500.csv', encoding='utf-8')))
    uses = []
    for r in rows:
        for part in r['statements'].split(' || '):
            m = re.match(r'(P69|P108|P184)=(Q\d+)\S* \[(.*)\]$', part)
            if m:
                uses.append((r['key'], r['label'], m.group(1), m.group(2), m.group(3)))
    qids = sorted({u[3] for u in uses})
    lab, ror, human = {}, defaultdict(list), set()
    for i in range(0, len(qids), 200):
        vs = ' '.join(f'wd:{q}' for q in qids[i:i + 200])
        for b in qlever('SELECT ?i ?l WHERE { VALUES ?i {%s} ?i rdfs:label ?l FILTER(lang(?l)="en" || lang(?l)="mul") }' % vs):
            lang = b['l'].get('xml:lang')
            if lang == 'en' or val(b, 'i') not in lab:
                lab[val(b, 'i')] = val(b, 'l')
        for b in qlever('SELECT ?i ?r WHERE { VALUES ?i {%s} ?i wdt:P6782 ?r }' % vs):
            ror[val(b, 'i')].append(val(b, 'r'))
        for b in qlever('SELECT ?i WHERE { VALUES ?i {%s} ?i wdt:P31 wd:Q5 }' % vs):
            human.add(val(b, 'i'))
    bad = 0
    with open(OUT / 'statement-items-check.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['key', 'label', 'property', 'item', 'item_label_on_wikidata', 'our_name', 'check'])
        for k, l, p, q, note in uses:
            ours = re.sub(r'^(doctorate|employer|advisor) ', '', note.split(' (')[0])
            ours = re.sub(r' \d{4}$', '', ours).strip()
            ok = (bool(ror.get(q)) if p != 'P184' else q in human)
            a, b = set(re.findall(r'[a-z]{4,}', fold(lab.get(q, '')))), set(re.findall(r'[a-z]{4,}', fold(ours)))
            same = bool(a & b)
            chk = 'ok' if ok and same else ('NO ROR/NOT HUMAN' if not ok else 'NAME DIFFERS')
            bad += chk != 'ok'
            w.writerow([k, l, p, q, lab.get(q, ''), ours, chk])
    print(len(uses), 'statement items checked;', bad, 'flagged')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('stage', choices=['pool', 'screen', 'write', 'verify'])
    args = ap.parse_args()
    if args.stage == 'pool':
        build_pool(args)
    elif args.stage == 'screen':
        screen(args)
    elif args.stage == 'write':
        write(args)
    else:
        verify(args)


if __name__ == '__main__':
    main()
