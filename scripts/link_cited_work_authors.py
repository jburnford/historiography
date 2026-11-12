"""Cited works matched today (LC 2016 books, OpenAlex articles/chapters) -> the person keys that wrote them (2026-11-10).

The two matchers of 2026-11-10 (data/identifiers/cited-works-lc-full-2026-11-10, cited-works-openalex-2026-11-10) add
cited works the key log does not hold. Their sources name authors, sometimes with an identifier we hold (an LC name
authority or an ORCID that is on a key) and mostly without. This script decides, for each (source, work, author
position), whether the author is a person key of the graph, and keeps the gaps visible as numbers.

Owner (2026-11-10): "we don't want false matches; but we also don't want to be conservative where there is only one
possible match." The cautionary case is p-8481 James Lockhart (2016 PhD) once credited with the 1969-2003 reviews of
the senior Latin Americanist: one candidate among OUR keys is not uniqueness, so dates and rarity outside the graph
decide (memory: identity by works; dates for matching; topic never merges).

States
  exact     the source's identifier (LC authority, ORCID) is on a key. Credited.
  linked    no shared identifier; the rule below holds. Credited, signals recorded.
  possible  one or more name-compatible keys, rule not satisfied. Not credited; candidates listed.
  none      no keyed person is name-compatible.

The rule (RULE_TEXT in the code, also written to report.json 'rule'):
  - exact needs the identifier only; an OpenAlex ORCID also needs the name to agree and the work inside the key's
    dates (OpenAlex profiles mix people: p-8481's ORCID sits on the senior James Lockhart's 1977-1985 articles);
  - names: same family name; first given names written out and identical ('full', name_level); a short form or
    transliteration ('variant': Ben/Benjamin, also Norma/Norman) or an initial on either side ('initial') needs a
    second fact; Jim and James do not agree;
  - proven different (state none): an LC authority on the key other than the source's; LC dates of the source against
    the key's life years (more than a year apart), PhD year or works; the ORCID owner whose dates exclude the work;
  - not passing (kept possible): a pooled key (merge_guard: LC's books disagree), birth and PhD contradicting
    (career_window.INCONSISTENT), a different ORCID on the key (in OpenAlex mostly one person with two ORCIDs);
  - date: the work's year inside the key's career window (career_window.py: birth+20, else PhD-10; to death+2, no
    upper bound for books, since editions and translations follow death), else inside the key's own dated works widened
    SPAN_BEFORE/SPAN_AFTER years; a key with no dated work fails;
  - 'unique-rare': one candidate, dated, names 'full', and no other LC authority bears the family + first given name
    (RARE_LC) and at most RARE_OA OpenAlex History author ids do;
  - 'unique-second-fact' / 'several-one-survives': one candidate (or exactly one of several) passes the date test and
    has an independent fact: printed institution ROR = a dated affiliation of the key; a co-author exact-linked on the
    work is a known co-author; the OpenAlex author id is tied to the key through another credited work; the work cites
    the key's own works. Co-citation by the same theses is support only (topic never links).
  Parameters are tuned on half the gold set (identifiers on keys, hidden) under a proven-namesake test (two
  different LC authorities, the keyed one hidden); report.json holds both and the held-out half's measures.

Subcommands
  oa-extract   stream the OpenAlex harvest for the crosswalk's works: authorships with institutions (ROR), raw
               affiliations, referenced works -> CACHE/oa (jsonl). Reads E: only.
  run          build people, sources, gold and namesake tests, tune, links, report. Writes OUT; keeps a state pickle
               in CACHE for `finish` (re-tune and rewrite without recomputing features).

    python3 scripts/link_cited_work_authors.py oa-extract
    python3 scripts/link_cited_work_authors.py run
    python3 scripts/link_cited_work_authors.py finish

Reads build/graph (person keys as of that build), the key-log cache read-only (not-same marks), E: read-only. Writes
no proposal and touches no key log.
"""
import argparse
import csv
import gzip
import json
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

HARVEST = Path('/mnt/e/openalex-history-2026-11-08/history')
OA_ROWS = '/mnt/e/openalex-people-2026-11-09/rows/history*.parquet'
OA_TIES = '/mnt/e/openalex-people-2026-11-09/ties.parquet'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
LC_XW = ROOT / 'data/identifiers/cited-works-lc-full-2026-11-10/crosswalk.csv.gz'
OA_XW = ROOT / 'data/identifiers/cited-works-openalex-2026-11-10/crosswalk.csv.gz'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'
OUT = ROOT / 'data/identifiers/cited-work-authors-2026-11-10'
CACHE = Path(os.environ.get('LINKER_CACHE', '/tmp/claude-1000/-home-jic823-historiography/'
                            'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/linker'))

ID_RE = re.compile(r'"id":\s*"https://openalex\.org/W(\d+)"')


# ---------------------------------------------------------------- oa-extract

def _extract_one(args):
    path, want_file, out = args
    want = set(open(want_file).read().split())
    n = 0
    with gzip.open(path, 'rt', encoding='utf-8') as f, open(out, 'w', encoding='utf-8') as o:
        for line in f:
            m = ID_RE.search(line, 0, 200)
            if not m or m.group(1) not in want:
                continue
            d = json.loads(line)
            wid = 'W' + m.group(1)
            auths = []
            for i, a in enumerate(d.get('authorships') or []):
                au = a.get('author') or {}
                auths.append(dict(
                    pos=i, author=(au.get('id') or '').rsplit('/', 1)[-1], name=au.get('display_name'),
                    raw=a.get('raw_author_name'), orcid=(au.get('orcid') or a.get('raw_orcid') or '').rsplit('/', 1)[-1],
                    rors=[(x.get('ror') or '').rsplit('/', 1)[-1] for x in a.get('institutions') or [] if x.get('ror')],
                    insts=[x.get('display_name') for x in a.get('institutions') or [] if x.get('display_name')],
                    raw_aff=a.get('raw_affiliation_strings') or []))
            refs = [r.rsplit('/', 1)[-1] for r in d.get('referenced_works') or []]
            o.write(json.dumps(dict(work=wid, year=d.get('publication_year'), authorships=auths, refs=refs),
                               ensure_ascii=False) + '\n')
            n += 1
    return path.name, n


def oa_extract(args):
    import duckdb
    out = CACHE / 'oa'
    out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    ids = [r[0] for r in db.execute(f"SELECT DISTINCT openalex_id FROM read_csv('{OA_XW}', all_varchar=true)").fetchall()]
    ids = [i[1:] if i.startswith('W') else i for i in ids if i]
    want = out / 'want.txt'
    want.write_text('\n'.join(ids))
    files = sorted(HARVEST.glob('*.jsonl.gz'))
    jobs = [(p, str(want), str(out / (p.name.replace('.jsonl.gz', '.jsonl')))) for p in files]
    with mp.Pool(args.workers) as pool:
        tot = 0
        for name, n in pool.imap_unordered(_extract_one, jobs):
            tot += n
            print(name, n, tot, flush=True)
    print('extracted', tot)


# ---------------------------------------------------------------- names

import hashlib
import random
import unicodedata
from collections import Counter, defaultdict

from namesake_check_groups import LETTERS, PARTICLES
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

SUFFIX = re.compile(r',?\s+(jr|sr|ii|iii|iv)\.?$', re.I)


def nfold(s):
    return unicodedata.normalize('NFKD', (s or '').translate(LETTERS)).encode('ascii', 'ignore').decode().lower()


def fam_norm(s):
    ws = [w for w in re.split(r'[^a-z]+', nfold(s)) if w]
    while len(ws) > 1 and ws[0] in PARTICLES:
        ws = ws[1:]
    return ' '.join(ws)


TITLES = {'sir', 'dr', 'rev', 'prof', 'mr', 'mrs', 'ms', 'miss', 'jr', 'sr', 'ii', 'iii', 'iv', 'hon', 'lord', 'lady',
          'dame', 'fr', 'baron', 'baroness', 'count', 'countess', 'graf', 'freiherr', 'saint', 'st', 'father', 'sister',
          'brother', 'mother', 'dom', 'dona', 'don', 'mme', 'mlle', 'm', 'herr', 'frau', 'esq', 'phd', 'md'}


def gwords(form):
    """Given names of a 'Family, Given' form, in order, folded; initials kept as one letter. LC's fuller form in
    parentheses is used ('Clifford, N. J. (Nicholas J.)' -> nicholas j); the given part ends at the next comma or
    at dates; lower-case particles (de, da, van) and the joining 'e'/'y' are dropped; hyphenated names split."""
    _, _, giv = form.partition(',')
    m = re.search(r'\(([^)]*)\)', giv)
    if m and re.search(r'[A-Za-z]{2}', m.group(1)):
        giv = m.group(1)
    else:
        giv = re.sub(r'\(.*?\)', ' ', giv)
    giv = giv.split(',')[0]
    giv = re.sub(r'\b(1[0-9]{3}|20[0-9]{2}|approximately|active|born|died|fl\.|b\.|d\.).*', '', giv)
    out = []
    for t in re.split(r"[\s\-\u2010.]+", giv.translate(LETTERS)):
        raw = t.strip("'\u2019`\"")
        f = re.sub('[^a-z]', '', nfold(raw))
        if not f or f in TITLES and len(f) > 1:
            continue
        if raw[:1].islower() and (f in PARTICLES or f in ('e', 'y', 'd', 'l')):
            continue
        out.append(f)
    return out


def forms(label):
    """(family, 'Family, Given' form, given names) readings of a name; a name without a comma is read 'Given Family'
    and, with three or more words, also 'Given Family1 Family2' (García Márquez, van Wyk)."""
    label = SUFFIX.sub('', (label or '').strip().rstrip('.'))
    out = []
    if ',' in label:
        fam, _, giv = label.partition(',')
        out.append((fam_norm(fam), label))
    else:
        ws = label.split()
        if len(ws) < 2:
            return []
        out.append((fam_norm(ws[-1]), ws[-1] + ', ' + ' '.join(ws[:-1])))
        if len(ws) >= 3:
            out.append((fam_norm(' '.join(ws[-2:])), ' '.join(ws[-2:]) + ', ' + ' '.join(ws[:-2])))
    seen, res = set(), []
    for f, form in out:
        g = gwords(form)
        if f and g and f not in seen:
            seen.add(f)
            res.append((f, form, tuple(g)))
    return res


def initial_only(g):
    return all(len(w) == 1 for w in g)


def _close(a, b):
    """Written-out given names that may be one name: a short form (Pat/Patricia, Ben/Benjamin) or a transliteration
    (same consonants). Also catches Norma/Norman, Georges/George, Fernanda/Fernando: so only ever a 'variant'."""
    lo, hi = sorted((a, b), key=len)
    return len(lo) >= 3 and hi.startswith(lo) or len(lo) >= 4 and re.sub(r'[aeiouy]+', '', a) == re.sub(r'[aeiouy]+', '', b)


def name_level(gs, gk):
    """How two lists of given names agree: 'full' (the first given names written out and identical), 'variant'
    (written out, a short form or transliteration of each other), 'initial' (one side only an initial), or None
    (they disagree). Leading initials before a written name may stand for it ('J. Garry' / 'Garry'). Every other
    given name of the shorter list must agree with one of the longer's (an initial agrees with a name it begins)."""
    if not gs or not gk:
        return None
    a, b = list(gs), list(gk)
    if len(a[0]) > 1 and len(b[0]) > 1:
        lev = 'full' if a[0] == b[0] else 'variant' if _close(a[0], b[0]) else None
        ra, rb = a[1:], b[1:]
    elif len(a[0]) == 1 and len(b[0]) == 1:
        lev = 'initial' if a[0] == b[0] else None
        ra, rb = a[1:], b[1:]
    else:
        x, y = (a, b) if len(a[0]) == 1 else (b, a)
        i = next((j for j, w in enumerate(x) if len(w) > 1), None)
        if i is not None and x[i] == y[0]:
            lev, ra, rb = 'full', x[i + 1:], y[1:]
        elif y[0].startswith(x[0]):
            lev, ra, rb = 'initial', x[1:], y[1:]
        else:
            return None
    if lev is None:
        return None
    short, long_ = (ra, rb) if len(ra) <= len(rb) else (rb, ra)
    def agree(w, t):
        lo, hi = sorted((w, t), key=len)
        return w == t or len(lo) == 1 and hi.startswith(lo) or _close(w, t)
    for w in short:
        if not any(agree(w, t) for t in long_):
            return None
    return lev


def yr(v):
    m = re.match(r'^\s*-?(\d{3,4})', str(v or ''))
    return int(m.group(1)) if m else None


def heading_dates(h):
    """'Freyre, Gilberto, 1900-1987.' -> (1900, 1987); 'b. 1950', '1944-' handled; 'active'/'fl.' dates ignored."""
    h = h or ''
    if re.search(r'\b(active|fl\.|flourished|approximately|ca\.)', h):
        return None, None
    m = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\??-(1[0-9]{3}|20[0-2][0-9])?', h)
    if m:
        return int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
    m = re.search(r'\bb\. ?(1[0-9]{3}|20[0-2][0-9])', h)
    if m:
        return int(m.group(1)), None
    m = re.search(r'\bd\. ?(1[0-9]{3}|20[0-2][0-9])', h)
    if m:
        return None, int(m.group(1))
    return None, None


# ---------------------------------------------------------------- parameters (tuned on half the gold set)

PARAMS = dict(          # defaults (and the ORCID guard's dates); `run` tunes the rule's and writes them to report.json
    RARE_LC=0,          # other LC personal name authorities with the same family + first given name, at most
    RARE_OA=10,         # OpenAlex History author ids with the same family + first given name, at most
    SPAN_BEFORE=10,     # key without life/PhD years: its own dated works, widened this far before ...
    SPAN_AFTER=20,      # ... and after
    SPAN_MIN=1,         # ... when it has at least this many dated works
    COCITE_FACT=0,      # theses citing both the work and the key's works that count as a second fact (0 = never)
)
NAMESAKE_MAX = 0.002   # proven-namesake links tolerated in tuning (target: about none)
ADD_MAX = 0.0004       # round 2: namesake links an addition may add, as a share of each test's rows
LIFE_TOL = 1           # LC dates of the source person and the key's life years may differ by a year (Peter J. Burke 1939 is not Peter Burke 1937)
SLACK = 10             # a dated affiliation places the person this many years either side
ADULT, BEFORE_PHD, AFTER_DEATH = 20, 10, 2     # scripts/career_window.py
HARD = {'lcnaf-differs', 'orcid-owner-out-of-window', 'birth-differs', 'death-differs', 'phd-vs-birth', 'works-before-birth',
        'works-after-death', 'phd-after-death', 'activity-before-birth', 'activity-after-death'}


# ---------------------------------------------------------------- the graph's people

NAME_FORM_TIES = ROOT / 'data/graph/name-form-ties.csv.gz'   # scripts/name_form_ties.py (2026-11-12, class 37)
TIE_RELATIONS = ('drops-second-family', 'drops-first-family', 'hyphen-part-dropped', 'middle-as-family', 'suffix-dropped',
                 'family-changed')


def add_name_form_ties(people, norm=lambda s: s):
    """Stated alternate family-name forms of a key (LC 400 cross-references, ORCID, AHA; class 37) join the family index:
    they only make the key a candidate for a name printed in that form. people.tied_kform[(key, form)] = 'source:id'
    marks the index entries that came from a tie (a form the key's own label also gives is not a tie). A tied candidate
    never enters an identifier route and its authorities do not count in the rarity test; the facts and date tests decide
    (rule_wp in link_work_people.py: a tied candidate links only with a fact). WP_NO_NAME_TIES=1 turns it off."""
    people.tied_kform = {}
    if not NAME_FORM_TIES.exists() or os.environ.get('WP_NO_NAME_TIES'):
        return
    with gzip.open(NAME_FORM_TIES, 'rt', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            k = r['key']
            if k not in people.label or r['relation'] not in TIE_RELATIONS:
                continue
            mine = {(f, form) for f, form, _ in forms(norm(people.label[k]))}
            for f, form, g in forms(norm(r['form'])):
                if (f, form) in mine or (k, form) in people.tied_kform:
                    continue
                people.index[f].append((k, form, g))
                people.tied_kform[(k, form)] = f"{r['source']}:{r['source_id']}"


class People:
    def __init__(self, db):
        self.db = db
        G = GRAPH
        self.label, self.lcnaf, self.orcid, self.aha = {}, {}, {}, {}
        anchor_key = {}
        for k, label, anchors in db.execute(f"SELECT key, label, anchors FROM '{G}/person.parquet'").fetchall():
            self.label[k] = label or ''
            an = anchors or []
            self.lcnaf[k] = {a[6:] for a in an if a.startswith('lcnaf:')}
            self.orcid[k] = {a[6:] for a in an if a.startswith('orcid:')}
            self.aha[k] = [a for a in an if a.startswith('aha-phd:')]
            for a in an:
                anchor_key[a] = k
        self.lc_key = defaultdict(set)
        self.orcid_key = defaultdict(set)
        for k, s in self.lcnaf.items():
            for x in s:
                self.lc_key[x].add(k)
        for k, s in self.orcid.items():
            for x in s:
                self.orcid_key[x].add(k)
        # family index
        self.index = defaultdict(list)
        for k, label in self.label.items():
            for f, form, g in forms(label):
                self.index[f].append((k, form, g))
        add_name_form_ties(self)
        # life years with their sources
        self.life = {}
        with gzip.open(ROOT / 'data/person-facts/life-years.csv.gz', 'rt', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                self.life[r['key']] = (yr(r['birth']), yr(r['death']), r['birth_sources'] or '', r['death_sources'] or '')
        # PhD year: AHA records on aha-phd anchors, thesis works authored
        aha_year = {}
        for line in open(ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl', encoding='utf-8'):
            r = json.loads(line)
            if r.get('year'):
                aha_year['aha-phd:' + r['id']] = int(r['year'])
        self.phd = {}
        for k, an in self.aha.items():
            ys = [aha_year[a] for a in an if a in aha_year]
            if ys:
                self.phd[k] = min(ys)
        for k, y in db.execute(f"""SELECT a."from", min(w.year) FROM {keylog(G, 'authored')} a JOIN '{G}/work.parquet' w
                ON w.key = a."to" WHERE w.kind = 'thesis' AND w.year IS NOT NULL GROUP BY 1""").fetchall():
            self.phd[k] = min(self.phd.get(k, y), y)
        # the span of the key's own dated works (authored or edited), all kinds and non-book kinds
        self.span, self.span_short = {}, {}
        for k, lo, hi, n, slo, shi in db.execute(f"""SELECT p, min(y), max(y), count(*), min(y) FILTER (WHERE kind IN ('article', 'review', 'thesis', 'chapter')),
                    max(y) FILTER (WHERE kind IN ('article', 'review', 'thesis', 'chapter'))
                FROM (SELECT a."from" p, w.year y, w.kind kind FROM (SELECT "from", "to" FROM {keylog(G, 'authored')}
                      UNION ALL SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to"
                      WHERE w.year BETWEEN 1000 AND 2027) GROUP BY p""").fetchall():
            self.span[k] = (lo, hi, n)
            if slo is not None:
                self.span_short[k] = (slo, shi)
        # pooled keys (merge_guard.pooled_keys, read from the graph's anchors)
        self.pooled = set()
        pooled_run = ROOT / 'data/field-research/lc-authorities-2026-10-30/canon-rerun5-2026-10-31/canon-people-lc.csv'
        with pooled_run.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['outcome'] == 'books_disagree' and f"diss-person:{r['graph_key']}" in anchor_key:
                    self.pooled.add(anchor_key[f"diss-person:{r['graph_key']}"])
        if 'diss-person:miller|james' in anchor_key:
            self.pooled.add(anchor_key['diss-person:miller|james'])
        # not-same marks (key-log cache, read-only)
        import sqlite3
        self.not_same = defaultdict(set)
        c = sqlite3.connect(f"file:{ROOT / 'build/keylog-state.sqlite'}?mode=ro", uri=True)
        for k, m in c.execute("SELECT key, member FROM members WHERE member LIKE 'not-same:%'"):
            self.not_same[k].add(m.split(':', 1)[1])
            self.not_same[m.split(':', 1)[1]].add(k)
        c.close()
        # dated affiliations with ROR (system-level institutions dropped: a bare system name places nobody)
        from key_review_credit_merges import is_system
        self.aff = defaultdict(list)
        for k, ror, label, fy, ly in db.execute(f"""SELECT a."from", i.ror, i.label, a.first_year, a.last_year
                FROM '{G}/affiliated_with.parquet' a JOIN '{G}/institution.parquet' i ON i.key = a."to" WHERE i.ror IS NOT NULL""").fetchall():
            if not is_system(label or ''):
                self.aff[k].append((ror.rsplit('/', 1)[-1], label, fy, ly))
        # OpenAlex author ids tied to keys through a work the graph credits (not ORCID-only ties)
        # An OpenAlex author id tied to two keys mixes people (A5046219782 holds a Columbia philologist and a
        # Massachusetts bishop, both William Lawrence): its ties are dropped. A tie through a single work places the
        # person only near that work's years (A5057463100: one 1987 work of the Drew book historian, then the Arizona
        # legal historian's 2017 book).
        self.ties = defaultdict(dict)
        for a, p, kinds, n, y0, y1 in db.execute(f"SELECT author, person, tie_kinds, works, y0, y1 FROM '{OA_TIES}'").fetchall():
            if any('work' in x for x in kinds or []):
                self.ties[a][p] = (n or 0, y0, y1)
        self.ties = {a: v for a, v in self.ties.items() if len(v) == 1}
        self.coauth = set()
        for a, b in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'coauthored')}").fetchall():
            self.coauth.add((a, b))
            self.coauth.add((b, a))
        # ---- round 2 (2026-11-10): more facts and more dating
        from key_review_reviewers import journal_key
        # journals the key has published in or reviewed in (its own authored or edited works with a journal)
        self.journals = defaultdict(set)
        for k, j in db.execute(f"""SELECT DISTINCT a."from", w.journal FROM (SELECT "from", "to" FROM {keylog(G, 'authored')}
                UNION ALL SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to"
                WHERE w.journal IS NOT NULL""").fetchall():
            jk = journal_key(j)
            if jk:
                self.journals[k].add(jk)
        # corpus theses (diss-thesis anchors): who wrote each, who supervised it, and the supervision years
        self.thesis_auth, self.thesis_sup = defaultdict(set), defaultdict(set)
        sup_years = defaultdict(list)
        for rel, k, d, y in db.execute(f"""WITH t AS (SELECT key, year, replace(a, 'diss-thesis:', '') d FROM
                    (SELECT key, year, unnest(anchors) a FROM '{G}/work.parquet' WHERE kind = 'thesis') WHERE a LIKE 'diss-thesis:%')
                SELECT 'a', s."from", t.d, t.year FROM {keylog(G, 'authored')} s JOIN t ON t.key = s."to"
                UNION ALL SELECT 's', s."from", t.d, t.year FROM '{G}/supervised.parquet' s JOIN t ON t.key = s."to" """).fetchall():
            (self.thesis_auth if rel == 'a' else self.thesis_sup)[d].add(k)
        for k, y in db.execute(f"""SELECT s."from", w.year FROM '{G}/supervised.parquet' s JOIN '{G}/work.parquet' w
                ON w.key = s."to" WHERE w.year IS NOT NULL""").fetchall():
            sup_years[k].append(y)
        # dated affiliations, not the 2026 directory snapshot
        aff_years = defaultdict(list)
        for k, fy, ly in db.execute(f"""SELECT "from", first_year, last_year FROM '{G}/affiliated_with.parquet'
                WHERE source <> 'aha_directory' AND (first_year IS NOT NULL OR last_year IS NOT NULL)""").fetchall():
            aff_years[k] += [y for y in (fy, ly) if y]
        self.supaff = {}
        for k in set(sup_years) | set(aff_years):
            ys = sup_years.get(k, []) + aff_years.get(k, [])
            self.supaff[k] = (min(ys), max(ys))
        # all dated affiliations with their names (for printed-name agreement where OpenAlex gives no ROR)
        self.aff_named = defaultdict(list)
        for k, label, fy, ly in db.execute(f"""SELECT a."from", i.label, a.first_year, a.last_year
                FROM '{G}/affiliated_with.parquet' a JOIN '{G}/institution.parquet' i ON i.key = a."to" """).fetchall():
            if label and not is_system(label):
                self.aff_named[k].append((label, fy, ly))
        # the key's works as the dissertation corpus cites them (diss-person anchors): their years (a span for keys
        # whose own works the graph does not date) and the first year a thesis cites any of the key's works
        dp = [(a[len('diss-person:'):], k) for k, an in db.execute(f"SELECT key, anchors FROM '{G}/person.parquet'").fetchall()
              for a in (an or []) if a.startswith('diss-person:')]
        db.register('dp', db.execute('SELECT unnest(?) AS pk, unnest(?) AS pkey', [[a for a, _ in dp], [b for _, b in dp]]).df())
        self.cspan = {}
        for k, lo, hi, n in db.execute(f"""
                WITH a AS (SELECT DISTINCT person_key, work_id FROM read_csv('{CORPUS / 'authored.csv.gz'}', all_varchar=true)
                           WHERE person_key IN (SELECT pk FROM dp)),
                     w AS (SELECT work_id, TRY_CAST(year AS INTEGER) y FROM read_csv('{CORPUS / 'works.csv'}', all_varchar=true)
                           WHERE work_id IN (SELECT work_id FROM a))
                SELECT dp.pkey, min(y), max(y), count(*) FROM a JOIN w USING (work_id) JOIN dp ON dp.pk = a.person_key
                WHERE y BETWEEN 1000 AND 2027 GROUP BY 1""").fetchall():
            self.cspan[k] = (lo, hi, n)
        self.cite_lo = {}
        for k, y in db.execute(f"""
                WITH dy AS (SELECT id d, TRY_CAST(year AS INTEGER) y FROM read_csv('{CORPUS / 'dissertations.csv'}', all_varchar=true)),
                     c1 AS (SELECT dp.pkey, dy.y FROM read_csv('{CORPUS / 'authored.csv.gz'}', all_varchar=true) a
                            JOIN dp ON dp.pk = a.person_key
                            JOIN read_csv('{CORPUS / 'strict-citations.csv.gz'}', all_varchar=true) s ON s.work_id = a.work_id
                            JOIN dy ON dy.d = s.dissertation_id),
                     c2 AS (SELECT a."from" pkey, dy.y FROM read_csv('{ROOT / 'data/graph/cites.csv.gz'}', all_varchar=true) c
                            JOIN {keylog(G, 'authored')} a ON a."to" = c.work_key JOIN dy ON dy.d = c.dissertation_id)
                SELECT pkey, min(y) FROM (SELECT * FROM c1 UNION ALL SELECT * FROM c2) WHERE y BETWEEN 1900 AND 2027 GROUP BY 1""").fetchall():
            self.cite_lo[k] = y

    # -- facts under a mask (gold tests hide the identifier and what came from it)
    def lifeyears(self, k, mask_lc=()):
        """Life years, without those that came only from the hidden LC authorities (gold tests)."""
        r = self.life.get(k)
        if not r:
            return None, None
        b, d, bs, ds = r
        if mask_lc:
            pre = tuple(f'lcnaf:{a}=' for a in mask_lc)
            if b is not None and not [s for s in bs.split() if not s.startswith(pre)]:
                b = None
            if d is not None and not [s for s in ds.split() if not s.startswith(pre)]:
                d = None
        return b, d

    def window(self, k, mask_lc=()):
        """career_window.py on this key: (lo, hi, how) or 'inconsistent' or None."""
        b, d = self.lifeyears(k, mask_lc)
        p = self.phd.get(k)
        if b is not None and p is not None and not b + 20 <= p <= b + 75:
            return 'inconsistent'
        lo = b + ADULT if b is not None else (p - BEFORE_PHD if p is not None else None)
        hi = d + AFTER_DEATH if d is not None else None
        if lo is None and hi is None:
            return None
        return (lo, hi, 'life' if b is not None else ('phd' if p is not None else 'death'))


# ---------------------------------------------------------------- population rarity

def population_counts(db, needed):
    """(family, first given) -> (LC authorities, OpenAlex History author ids) bearing that name; and the same counts
    by (family, first given, second given as printed: a name or an initial), for full-name rarity."""
    lc, oa = Counter(), Counter()
    lc2, oa2 = Counter(), Counter()
    cur = db.execute(f"SELECT label FROM '{LC_NAMES}' WHERE NOT deprecated")
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for (label,) in rows:
            if not label or ',' not in label:
                continue
            fam, _, giv = label.partition(',')
            f = fam_norm(fam)
            g = gwords(label)
            if g and (f, g[0]) in needed:
                lc[f, g[0]] += 1
                if len(g) >= 2:
                    lc2[f, g[0], g[1]] += 1
    cur = db.execute(f"SELECT DISTINCT author, name FROM read_parquet('{OA_ROWS}') WHERE name IS NOT NULL")
    seen = set()
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for a, name in rows:
            for f, form, g in forms(name)[:1]:
                if (f, g[0]) in needed and (a, f, g[0]) not in seen:
                    seen.add((a, f, g[0]))
                    oa[f, g[0]] += 1
                    if len(g) >= 2:
                        oa2[f, g[0], g[1]] += 1
    lc2i, oa2i = Counter(), Counter()
    for (f, g0, g1), n in lc2.items():
        lc2i[f, g0, g1[0]] += n
    for (f, g0, g1), n in oa2.items():
        oa2i[f, g0, g1[0]] += n
    return lc, oa, lc2, oa2, lc2i, oa2i


# ---------------------------------------------------------------- sources

def load_sources(db, people):
    """Author positions: dicts with src, swork, work_id, pos, role, name, forms, year, book, lc (authorities), orcid,
    oa_author, rors, insts, sb, sd (source person's dates), citing."""
    pos = []
    # LC: the heading of each crosswalk work; its authority (URI, else the heading as LC prints it)
    rows = db.execute(f"""SELECT work_id, lccns, lc_title, lc_year, lc_author_heading, lc_author_uri, basis,
            cited_by_dissertations, initial FROM read_csv('{LC_XW}', all_varchar=true)""").fetchall()
    unresolved = {re.sub(r'[.,\s]+$', '', r[4]) for r in rows if r[4] and not r[5]}
    db.register('hd', db.execute('SELECT unnest(?) AS label', [sorted(unresolved)]).df())
    by_label = defaultdict(list)
    for lcid, label in db.execute(f"SELECT n.lcid, hd.label FROM '{LC_NAMES}' n JOIN hd ON n.label = hd.label WHERE NOT n.deprecated").fetchall():
        by_label[label].append(lcid)
    for w, lccns, title, year, heading, uri, basis, cited, initial in rows:
        if not heading:
            continue
        ids = [u.rsplit('/', 1)[-1] for u in (uri or '').split(';') if u.strip()]
        how = 'uri'
        if not ids:
            c = by_label.get(re.sub(r'[.,\s]+$', '', heading), [])
            if len(c) == 1:
                ids, how = c, 'heading'
        role = (basis or '').split('/')[1] if (basis or '').count('/') >= 1 else ''
        pos.append(dict(src='lc', swork=(lccns or '').split(';')[0], work_id=w, pos=0, role=role, name=heading,
                        title=title, year=yr(year), book=True, lc=ids, lc_how=how, orcid='', oa_author='', rors=[],
                        insts=[], citing=int(cited or 0), initial_check=initial, venue=''))
    # authority dates for the LC authorities named (LC record, else the heading)
    ids = sorted({i for p in pos for i in p['lc']})
    db.register('want', db.execute('SELECT unnest(?) AS lcid', [ids]).df())
    lcd = {i: (yr(b), yr(d)) for i, b, d in db.execute(f"SELECT n.lcid, n.birth, n.death FROM '{LC_NAMES}' n JOIN want USING (lcid)").fetchall()}
    for p in pos:
        hb, hd_ = heading_dates(p['name'])
        b = d = None
        for i in p['lc']:
            b0, d0 = lcd.get(i, (None, None))
            b, d = b or b0, d or d0
        p['sb'], p['sd'] = b or hb, d or hd_
    # OpenAlex: authorships of each crosswalk work
    xw = defaultdict(list)
    for w, oid, doi, title, year, typ, venue, cited in db.execute(f"""SELECT work_id, openalex_id, doi, oa_title, oa_year,
            oa_type, oa_source, cited_by_dissertations FROM read_csv('{OA_XW}', all_varchar=true)""").fetchall():
        xw[oid].append((w, doi, title, yr(year), typ, venue, int(cited or 0)))
    refs = {}
    for fn in sorted((CACHE / 'oa').glob('*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            refs[r['work']] = r['refs']
            for w, doi, title, year, typ, venue, cited in xw.get(r['work'], []):
                for a in r['authorships']:
                    name = a['name'] or a['raw'] or ''
                    if a['raw'] and forms(name) and initial_only(forms(name)[0][2]) and forms(a['raw']) and not initial_only(forms(a['raw'])[0][2]):
                        name = a['raw']
                    pos.append(dict(src='openalex', swork=doi or r['work'], oa_id=r['work'], work_id=w, pos=a['pos'],
                                    role='author', name=name, title=title, year=year, book=typ == 'book', lc=[],
                                    lc_how='', orcid=a['orcid'] or '', oa_author=a['author'] or '', rors=a['rors'],
                                    insts=a['insts'], raw_aff=a['raw_aff'], citing=cited, sb=None, sd=None,
                                    initial_check='', venue=venue or '', oa_type=typ))
    for p in pos:
        p['forms'] = forms(p['name'])
    return pos, refs


# ---------------------------------------------------------------- features and the rule

def candidates(people, p):
    """Keys whose names agree with the source's. A name printed without a comma is read 'Given Family'; when it has
    three or more words and the key lacks the source's last written given name, that word may be the first of two
    family names ('Cristina Borreguero Beltrán' is not 'Beltrán, Cristina'): the agreement is only a 'variant'."""
    out = {}
    plain = ',' not in (p['name'] or '')
    src_words = set(re.split(r'[^a-z]+', nfold(p['name'])))
    for n, (f, form, g) in enumerate(p['forms']):
        for k, kform, kg in people.index.get(f, ()):
            lev = name_level(g, kg) if k not in out else None
            # 'surname-variant': as weak as a variant, but never a spelling variant (no rarity link)
            if lev == 'full' and plain and n == 0 and len(g) >= 2 and len(g[-1]) > 1 and g[-1] not in kg:
                lev = 'surname-variant'
            if lev == 'full' and particle_differs(form, kform, src_words, people.label.get(k, '')):
                lev = 'surname-variant'
            if lev:
                out[k] = (form, kform, g, kg, lev)
    return out


def raw_fam(form):
    return [w for w in re.split(r'[^a-z]+', nfold(form.split(',')[0])) if w]


def particle_differs(form, kform, src_words, klabel):
    """One family name carries a particle the other name lacks altogether ('Van Dover, J. Kenneth' is not 'Dover,
    K. J.'); fam_norm drops leading particles so that 'de Mattos' meets 'Mattos', which is right only when the other
    name carries the particle somewhere ('Mattos, Ilmar Rohloff de')."""
    a, b = raw_fam(form), raw_fam(kform)
    if a == b:
        return False
    k_words = set(re.split(r'[^a-z]+', nfold(klabel)))
    extra_a = {w for w in a if w in PARTICLES} - k_words
    extra_b = {w for w in b if w in PARTICLES} - src_words
    return bool(extra_a or extra_b)


def features(people, p, mask=None, exacts=None, refkeys=None, citers_of=None):
    """Everything the rule needs for one author position, computed once.
    mask: dict(key=G, lc=authorities hidden from G, orcid=ORCIDs hidden from G, src_lc=bool keep the source's
          authority for excluding keys with a different one, src_orcid=bool likewise)."""
    mask = mask or {}
    fe = dict(cands={}, exact=None)
    src_lc = [] if mask and not mask.get('src_lc') else p['lc']
    src_orcid = '' if mask and not mask.get('src_orcid') else p['orcid']
    orcid_out = set()
    if not mask:
        hit = {k for i in p['lc'] for k in people.lc_key.get(i, ())}
        if not hit and p['orcid']:
            # OpenAlex puts an ORCID on a whole author profile, which can mix people: the junior James Lockhart's
            # ORCID sits on the senior's 1977-1985 articles. An ORCID credits only when the name agrees and the work
            # falls inside the key's dates; otherwise the position is decided as if it had no identifier, and a key
            # whose dates exclude the work is set aside for it.
            others = None
            for k in people.orcid_key.get(p['orcid'], ()):
                levs = {name_level(g, kg) for f, _, g in p['forms'] for kf, _, kg in forms(people.label.get(k, '')) if f == kf} - {None}
                if not levs:
                    fe.setdefault('orcid_rejected', []).append(f'{k}:name')
                    continue
                if 'full' not in levs:
                    # the ORCID owner agrees only by an initial or a variant while another key carries the printed name
                    # in full: OpenAlex has put L. H. Roper's ORCID on Lyndal Roper's articles
                    if others is None:
                        others = {k2 for k2, v in candidates(people, p).items() if v[-1] == 'full'}
                    if others - {k}:
                        fe.setdefault('orcid_rejected', []).append(f'{k}:name-weaker-than-{sorted(others)[0]}')
                        orcid_out.add(k)
                        continue
                c = dict(win=people.window(k), span=people.span.get(k))
                if c['win'] == 'inconsistent':
                    c['win'] = None
                ok, how = date_test(c, p['year'], p['book'], PARAMS)
                if not ok and how not in ('undated', 'thin-span', 'no-year'):
                    fe.setdefault('orcid_rejected', []).append(f'{k}:{how}')
                    orcid_out.add(k)
                    continue
                hit.add(k)
        if hit:
            fe['exact'] = sorted(hit)
            return fe
    cs = candidates(people, p)
    for k in mask.get('drop', ()):
        cs.pop(k, None)
    if not p['forms']:
        return fe
    f0, form0, g0 = p['forms'][0]
    fe['src_initial'] = initial_only(g0)
    fe['src'] = p['src']
    fe['name_key'] = (f0, g0[0])
    year = p['year']
    for k, (form, kform, g, kg, lev) in cs.items():
        mlc = set(mask.get('lc') or ()) if mask.get('key') == k else set()
        morc = set(mask.get('orcid') or ()) if mask.get('key') == k else set()
        klc = people.lcnaf.get(k, set()) - mlc
        korc = people.orcid.get(k, set()) - morc
        why = []
        if src_lc and klc and not klc & set(src_lc):
            why.append('lcnaf-differs')
        if src_orcid and korc and src_orcid not in korc:
            why.append('orcid-differs')
        kb, kd = people.lifeyears(k, mlc)
        sb, sd = p['sb'], p['sd']
        ph = people.phd.get(k)
        sp = people.span.get(k)
        ss = people.span_short.get(k)
        if sb and kb and abs(sb - kb) > LIFE_TOL:
            why.append('birth-differs')
        if sd and kd and abs(sd - kd) > LIFE_TOL:
            why.append('death-differs')
        if sb and ph and not sb + 20 <= ph <= sb + 75:
            why.append('phd-vs-birth')
        if sd and ph and ph > sd:
            why.append('phd-after-death')
        if sb and sp and sp[0] < sb + 15 and not (kb and abs(sb - kb) <= LIFE_TOL):
            why.append('works-before-birth')
        if sd and ss and ss[1] > sd + 3:
            why.append('works-after-death')
        # the key's supervision, dated affiliations and corpus-cited works must fall in the source person's life
        # (Eric D. Widmer, b. 1966, is not the Eric Widmer who supervised at Brown in 1975)
        sa, csp = people.supaff.get(k), people.cspan.get(k)
        if sb and ((sa and sa[0] < sb + 20) or (csp and csp[0] < sb + 15)) and not (kb and abs(sb - kb) <= LIFE_TOL):
            why.append('activity-before-birth')
        if sd and sa and sa[1] > sd + 3:
            why.append('activity-after-death')
        if k in people.pooled:
            why.append('pooled')
        if k in orcid_out:
            why.append('orcid-owner-out-of-window')
        w = people.window(k, mlc)
        if w == 'inconsistent':
            why.append('inconsistent-dates')
            w = None
        # second facts
        facts = []
        if p['rors'] and year:
            for ror, ilabel, fy, ly in people.aff.get(k, ()):
                if ror in p['rors'] and (fy is None and ly is None or (fy or ly) - SLACK <= year <= (ly or fy) + SLACK):
                    facts.append(f'inst:{ilabel}')
                    break
        if exacts:
            for k2 in exacts:
                if k2 != k and (k, k2) in people.coauth:
                    facts.append(f'coauthor:{k2}')
                    break
        t = people.ties.get(p['oa_author'], {}).get(k) if p['oa_author'] else None
        if t and (t[0] >= 2 or year and t[1] and t[2] and t[1] - SLACK <= year <= t[2] + SLACK):
            facts.append('oa-author-tie')
        if refkeys and k in refkeys:
            facts.append('selfcite')
        # round 2 facts (each admitted only if it holds on gold and the namesake tests; see finish)
        if p.get('venue') and p.get('oa_type') in ('article', 'review', 'book-review') and not REPOSITORY.search(p['venue']):
            jk = JOURNAL_KEY(p['venue'])
            if jk and jk in people.journals.get(k, ()):
                facts.append('journal')
        citers = (citers_of or {}).get(p['work_id'], ())
        if any(k in people.thesis_auth.get(d, ()) for d in citers):
            facts.append('own-thesis-cites')
        if any(k in people.thesis_sup.get(d, ()) for d in citers):
            facts.append('student-thesis-cites')
        if not p['rors'] and p.get('raw_aff') and year:
            from key_review_credit_merges import agree, is_system
            hit = next((label for raw in p['raw_aff'] if raw and not is_system(raw) for label, fy, ly in people.aff_named.get(k, ())
                        if (fy is None and ly is None or (fy or ly) - SLACK <= year <= (ly or fy) + SLACK) and agree(raw, label)), None)
            if hit:
                facts.append(f'inst-name:{hit}')
        tied = getattr(people, 'tied_kform', {}).get((k, kform))
        fe['cands'][k] = dict(why=why, win=w, span=sp, facts=facts, lev=lev, label=people.label[k], klc=set() if tied else klc,
                              tied=tied,
                              ns=people.not_same.get(k, set()), g=tuple(g), kg=tuple(kg), fam=form and fam_norm(form.split(',')[0]),
                              cspan=people.cspan.get(k), supaff=people.supaff.get(k), cite_lo=people.cite_lo.get(k))
    return fe


def date_test(c, year, book, P):
    """(ok, how)"""
    if year is None:
        return False, 'no-year'
    w, sp = c['win'], c['span']
    lo = hi = None
    how = None
    if w:
        lo, hi, how = w
        if book:
            hi = None
        if lo is None and sp:
            lo = sp[0] - P['SPAN_BEFORE']
    if lo is None and hi is None:
        xd = P.get('XDATE', ())
        if not sp and 'corpus-span' in xd and c.get('cspan'):
            sp, how = c['cspan'], 'corpus-span'
        if sp:
            if sp[2] < P.get('SPAN_MIN', 1):
                return False, 'thin-span'
            after = P.get('SPAN_AFTER_1', P['SPAN_AFTER']) if sp[2] == 1 else P['SPAN_AFTER']
            lo, hi, how = sp[0] - P['SPAN_BEFORE'], sp[1] + after, how or 'span'
        elif 'sup-aff' in xd and c.get('supaff'):
            lo, hi, how = c['supaff'][0] - 35, (None if book else c['supaff'][1] + 25), 'sup-aff'
        elif 'cites' in xd and c.get('cite_lo'):
            lo, hi, how = c['cite_lo'] - 50, None, 'cites'
        else:
            return False, 'undated'
    if (lo is not None and year < lo) or (hi is not None and year > hi):
        return False, f'out-of-window:{lo}-{hi}'
    return True, how


def rarity(fe, pop, P, live=()):
    """LC authorities bearing the name besides the source's own (an LC heading is one) and those the candidate keys
    hold: other people of that name in the wider population; and OpenAlex History author ids of the name (OpenAlex
    splits a person over several ids, so this one is noisy and its threshold higher)."""
    n_lc, n_oa = pop[0].get(fe['name_key'], 0), pop[1].get(fe['name_key'], 0)
    own = (1 if fe.get('src') == 'lc' else 0) + len({a for k in live for a in fe['cands'][k].get('klc', ())})
    others = max(0, n_lc - own)
    return others, n_oa, others <= P['RARE_LC'] and n_oa <= P['RARE_OA']


BASE_FACTS = ('inst', 'coauthor', 'oa-author-tie', 'selfcite')
NEW_FACTS = ('journal', 'own-thesis-cites', 'student-thesis-cites', 'inst-name')
REPOSITORY = re.compile(r'(?i)repositor|\bHAL\b|dialnet|ebooks|pers[ée]e|zenodo|philpapers|researchgate|research portal|doaj|'
                        r'digital|archive|bibliography|scholarsarchive|e-?prints|white rose|discovery|depot|dépôt|openedition|'
                        r'ssrn|cairn|jstor|ssoar|university of|universit')


def JOURNAL_KEY(v):
    from key_review_reviewers import journal_key
    return journal_key(v)


def lev_dist(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def safe_variant(a, b):
    """A spelling or transliteration of one given name (Sebastián/Sebastiaan, Mahmoud/Mahmud), not a short form or a
    different name sharing letters (Norma/Norman, Daniel/Daniela, Fernanda/Fernando, Mauricio/Marco)."""
    if len(a) < 5 or len(b) < 5 or a[0] != b[0] or not _close(a, b):     # Kate/Katie are two names
        return False
    lo, hi = sorted((a, b), key=len)
    if hi.startswith(lo):
        return False
    if a[:-1] == b[:-1] and a[-1] in 'aeiouy' and b[-1] in 'aeiouy':
        return False
    return lev_dist(a, b) <= 2


def own_lc(fe, live):
    return (1 if fe.get('src') == 'lc' else 0) + len({a for k in live for a in fe['cands'][k].get('klc', ())})


def full_rare(fe, c, pop, P, live):
    """The full given names (first two) printed alike on both sides, unique in LC and rare in OpenAlex History
    (Daniel Delis Hill, Jean-Marie André). A middle initial on one side and a full name on the other counts only when
    no other LC authority bears that first name + initial + family."""
    if len(pop) < 6 or c['lev'] != 'full':
        return None
    g, kg, f = c['g'], c['kg'], c['fam']
    if len(g) < 2 or len(kg) < 2 or g[0] != kg[0] or len(g[0]) == 1:
        return None
    a, b = g[1], kg[1]
    lc2, oa2, lc2i, oa2i = pop[2], pop[3], pop[4], pop[5]
    if a == b and len(a) > 1:
        n_lc = lc2.get((f, g[0], a), 0) + lc2.get((f, g[0], a[0]), 0)
        n_oa = oa2.get((f, g[0], a), 0) + oa2.get((f, g[0], a[0]), 0)
    elif a[0] == b[0] and (len(a) == 1 or len(b) == 1):
        n_lc, n_oa = lc2i.get((f, g[0], a[0]), 0), oa2i.get((f, g[0], a[0]), 0)
    else:
        return None
    return max(0, n_lc - own_lc(fe, live)) <= 0 and n_oa <= P.get('RARE_OA_FULL', 3)


def variant_rare(fe, c, pop, P, live, p=None):
    """A safe spelling variant of the first given name, rare counting both spellings. Not when a name printed
    without a comma has a written given name the key lacks: it may be a first family name (Jaume Sastre Moll is not
    Jaime Moll)."""
    if c['lev'] != 'variant' or not c['g'] or not c['kg']:
        return None
    g = c['g']
    if p is not None and ',' not in (p['name'] or '') and len(g) >= 2 and any(len(w) > 1 and w not in c['kg'] for w in g[1:]):
        return None
    a, b, f = c['g'][0], c['kg'][0], c['fam']
    if not safe_variant(a, b):
        return None
    n_lc = pop[0].get((f, a), 0) + pop[0].get((f, b), 0)
    n_oa = pop[1].get((f, a), 0) + pop[1].get((f, b), 0)
    return max(0, n_lc - own_lc(fe, live)) <= P['RARE_LC'] and n_oa <= P['RARE_OA']


def rule(p, fe, pop, P, cocite=None):
    """-> (state, key or None, branch, candidates, signals)"""
    if fe.get('exact'):
        return 'exact', ';'.join(fe['exact']), 'identifier', fe['exact'], []
    cs = fe['cands']
    pre = [f'orcid-rejected:{x}' for x in fe.get('orcid_rejected', ())]
    if not cs:
        return 'none', None, 'no-compatible-name', [], pre
    hard = {k for k, c in cs.items() if set(c['why']) & HARD}
    live = [k for k in cs if k not in hard]
    if not live:
        return 'none', None, 'only-proven-namesakes', sorted(cs), pre + sorted({w for c in cs.values() for w in c['why']})
    n_lc, n_oa, rare = rarity(fe, pop, P, live)
    sig = pre + [f'lc_others={n_lc}', f'oa_n={n_oa}']
    ok = {}
    for k in live:
        c = cs[k]
        good, how = date_test(c, p['year'], p['book'], P)
        allowed = P.get('FACTS', BASE_FACTS)
        facts = [x for x in c['facts'] if x.split(':')[0] in allowed]
        if P.get('TOPICAL_FULL_ONLY') and c['lev'] != 'full':
            # citing the key's works (self-citation, a student's thesis) is close to topic: for a variant or initial
            # name it does not separate a namesake in the same field (Sergio Eduardo Carrera Quezada citing Sergio Quezada)
            facts = [x for x in facts if x.split(':')[0] not in ('selfcite', 'student-thesis-cites')]
        cc = (cocite or {}).get((p['work_id'], k), 0)
        if P['COCITE_FACT'] and cc >= P['COCITE_FACT']:
            facts.append(f'cocite:{cc}')
        # a different ORCID on the key blocks unless a second fact ties the key to the work (2026-11-10 decision)
        block = [w for w in c['why'] if not (w == 'orcid-differs' and facts and P.get('ORCID_SOFT'))]
        ok[k] = (good and not block, how, facts, cc)
    dated = [k for k in live if ok[k][0]]
    if len(dated) == 1:
        k = dated[0]
        _, how, facts, cc = ok[k]
        init = cs[k]['lev'] != 'full'
        s = sig + [f'date:{how}'] + facts + ([f'cocited:{cc}'] if cc else []) + ([f"name:{cs[k]['lev']}"] if init else [])
        if len(live) == 1:
            if not init and rare:
                return 'linked', k, 'unique-rare' + ('' if how in ('life', 'phd', 'death') else '-' + how), [k], s
            if P.get('FULLNAME') and full_rare(fe, cs[k], pop, P, live):
                return 'linked', k, 'unique-rare-fullname', [k], s + ['fullname-rare']
            if P.get('VARIANT') and variant_rare(fe, cs[k], pop, P, live, p):
                return 'linked', k, 'unique-rare-variant', [k], s + ['variant-rare']
            if facts:
                return 'linked', k, 'unique-second-fact', [k], s
            return 'possible', None, 'one-candidate-' + (cs[k]['lev'] + '-name' if init else 'common-name'), [k], s
        if facts:
            return 'linked', k, 'several-one-survives', live, s + [f'others={len(live) - 1}']
        return 'possible', None, 'several-one-dated-no-fact', live, s
    reasons = sorted({ok[k][1] if not ok[k][0] else 'dated' for k in live} | {w for k in live for w in cs[k]['why']})
    return 'possible', None, ('one-candidate-' if len(live) == 1 else 'several-') + ('none-dated' if not dated else 'several-dated'), live, sig + reasons


# ---------------------------------------------------------------- run

def stable_half(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % 2


def run(args):
    import duckdb
    tmp = CACHE / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB'; SET temp_directory='{tmp}'; SET enable_progress_bar=false")
    print('people ...', flush=True)
    people = People(db)
    print('sources ...', flush=True)
    pos, refs = load_sources(db, people)
    print(len(pos), 'positions', flush=True)
    # corpus author strings
    db.register('ws', db.execute('SELECT unnest(?) AS work_id', [sorted({p['work_id'] for p in pos})]).df())
    corpus = dict(db.execute(f"SELECT c.work_id, c.authors FROM read_csv('{CORPUS / 'works.csv'}', all_varchar=true) c JOIN ws USING (work_id)").fetchall())
    # self-citation: keys credited with a work the source work cites (OpenAlex works matched to graph works)
    pairs = [(w, r) for w, rs in refs.items() for r in rs]
    db.register('refs', db.execute('SELECT unnest(?) AS work, unnest(?) AS ref', [[a for a, _ in pairs], [b for _, b in pairs]]).df())
    refkeys = defaultdict(set)
    for w, k in db.execute(f"""SELECT DISTINCT refs.work, a."from" FROM refs
            JOIN (SELECT DISTINCT work, graph_work FROM read_parquet('{OA_ROWS}') WHERE graph_work <> '') g ON g.work = refs.ref
            JOIN {keylog(GRAPH, 'authored')} a ON a."to" = g.graph_work""").fetchall():
        refkeys[w].add(k)
    # the theses citing each work (for the own-thesis and student-thesis facts)
    citers_of = defaultdict(set)
    for w, d in db.execute(f"""SELECT DISTINCT s.work_id, s.dissertation_id FROM read_csv('{CORPUS / 'strict-citations.csv.gz'}', all_varchar=true) s
            JOIN ws USING (work_id)""").fetchall():
        citers_of[w].add(d)
    # exact links of each work's positions (for the co-author fact)
    by_work = defaultdict(list)
    for i, p in enumerate(pos):
        by_work[p['src'], p['work_id'], p.get('oa_id')].append(i)
    print('features ...', flush=True)
    feats = [features(people, p, refkeys=refkeys.get(p.get('oa_id')), citers_of=citers_of) for p in pos]
    exact_of = defaultdict(set)
    for i, p in enumerate(pos):
        if feats[i].get('exact'):
            exact_of[p['src'], p['work_id'], p.get('oa_id')].update(feats[i]['exact'])
    for i, p in enumerate(pos):
        if not feats[i].get('exact') and len(by_work[p['src'], p['work_id'], p.get('oa_id')]) > 1:
            feats[i] = features(people, p, exacts=exact_of[p['src'], p['work_id'], p.get('oa_id')],
                                refkeys=refkeys.get(p.get('oa_id')), citers_of=citers_of)
    # gold: identifiers on keys, hidden; namesake test: identifiers not on keys, one compatible key with another one
    print('gold ...', flush=True)
    gold, names = [], []
    for i, p in enumerate(pos):
        fe = feats[i]
        ex = fe.get('exact')
        if ex and len(ex) == 1:
            g = ex[0]
            if p['src'] == 'lc':
                hid = {i_ for i_ in p['lc'] if g in people.lc_key.get(i_, ())}
                for mode, keep in (('lc-authority-known', True), ('lc-no-authority', False)):
                    m = dict(key=g, lc=hid, src_lc=keep)
                    gold.append((mode, i, g, features(people, p, mask=m, citers_of=citers_of)))
            else:
                m = dict(key=g, orcid={p['orcid']}, src_orcid=False)
                ex2 = exact_of[p['src'], p['work_id'], p.get('oa_id')] - {g}
                gold.append(('openalex-orcid-hidden', i, g, features(people, p, mask=m, exacts=ex2, refkeys=refkeys.get(p.get('oa_id')), citers_of=citers_of)))
        elif not ex and (p['lc'] or p['orcid']):
            cs = candidates(people, p)
            if len(cs) != 1:
                continue
            k = next(iter(cs))
            # a proven namesake: the source's identifier is on no key, the one name-compatible key holds another one;
            # hide the key's identifiers (and the life years that came only from them) and run the rule
            if p['lc'] and people.lcnaf.get(k) and not people.lcnaf[k] & set(p['lc']):
                m = dict(key=k, lc=set(people.lcnaf[k]), src_lc=False)
                names.append(('lc-namesake', i, k, features(people, p, mask=m, citers_of=citers_of)))
            elif p['orcid'] and people.orcid.get(k) and p['orcid'] not in people.orcid[k]:
                m = dict(key=k, orcid=set(people.orcid[k]), src_orcid=False)
                ex2 = exact_of[p['src'], p['work_id'], p.get('oa_id')]
                names.append(('openalex-namesake', i, k, features(people, p, mask=m, exacts=ex2, refkeys=refkeys.get(p.get('oa_id')), citers_of=citers_of)))
    # Masked true author (round 2): the work's identifier puts it on key K1; another name-compatible key K2 is proven
    # a different person from K1 (two different LC authorities, birth years or PhD years apart, or a not-same mark).
    # Drop K1 as if it were not keyed, hide the source's identifier and K2's own identifiers, and run the rule: a link
    # to a proven K2 is a false link. This tests the OpenAlex facts (journal, institution, ties), which the LC test
    # cannot.
    proven = {}
    for i, p in enumerate(pos):
        ex = feats[i].get('exact')
        if not ex or len(ex) != 1:
            continue
        k1 = ex[0]
        b1 = people.life.get(k1, (None,))[0]
        for k2 in candidates(people, p):
            if k2 == k1:
                continue
            b2 = people.life.get(k2, (None,))[0]
            p1, p2 = people.phd.get(k1), people.phd.get(k2)
            if not ((people.lcnaf.get(k1) and people.lcnaf.get(k2) and not people.lcnaf[k1] & people.lcnaf[k2])
                    or (b1 and b2 and abs(b1 - b2) > 1) or (p1 and p2 and abs(p1 - p2) > 1) or k2 in people.not_same.get(k1, ())):
                continue
            proven.setdefault(i, set()).add(k2)
    for i, ks in proven.items():
        p = pos[i]
        k1 = feats[i]['exact'][0]
        ex2 = exact_of[p['src'], p['work_id'], p.get('oa_id')] - {k1}
        for k2 in sorted(ks):
            m = dict(drop={k1}, key=k2, lc=set(people.lcnaf.get(k2, ())), orcid=set(people.orcid.get(k2, ())), src_lc=False, src_orcid=False)
            names.append((f"{'lc' if p['src'] == 'lc' else 'openalex'}-masked-author", i, k2,
                          features(people, p, mask=m, exacts=ex2, refkeys=refkeys.get(p.get('oa_id')), citers_of=citers_of)))
    print(len(gold), 'gold rows', len(names), 'namesake rows', flush=True)
    # population rarity for every source name
    needed = {fe['name_key'] for fe in feats if fe.get('name_key')} | {fe['name_key'] for _, _, _, fe in gold + names if fe.get('name_key')}
    needed |= {(c['fam'], c['kg'][0]) for fe in feats + [r[3] for r in gold + names] for c in fe['cands'].values() if c.get('kg')}
    print('population ...', len(needed), flush=True)
    pop = population_counts(db, needed)
    # co-citation (support): theses citing both the work and a work credited to the candidate
    print('co-citation ...', flush=True)
    cand_pairs = {(pos[i]['work_id'], k) for i, fe in enumerate(feats) for k in fe['cands']}
    cand_pairs |= {(pos[i]['work_id'], k) for _, i, _, fe in gold + names for k in fe['cands']}
    cp = sorted(cand_pairs)
    db.register('cp', db.execute('SELECT unnest(?) AS work_id, unnest(?) AS pk', [[a for a, _ in cp], [b for _, b in cp]]).df())
    cocite = {(w, k): n for w, k, n in db.execute(f"""
        WITH sw AS (SELECT DISTINCT dissertation_id d, work_id FROM read_csv('{CORPUS / 'strict-citations.csv.gz'}', all_varchar=true)
                    WHERE work_id IN (SELECT DISTINCT work_id FROM cp)),
             kw AS (SELECT DISTINCT c.dissertation_id d, a."from" pk FROM read_csv('{ROOT / 'data/graph/cites.csv.gz'}', all_varchar=true) c
                    JOIN (SELECT "from", "to" FROM {keylog(GRAPH, 'authored')} UNION ALL SELECT "from", "to" FROM {keylog(GRAPH, 'edited')}) a
                    ON a."to" = c.work_key WHERE a."from" IN (SELECT DISTINCT pk FROM cp))
        SELECT cp.work_id, cp.pk, count(DISTINCT sw.d) FROM cp JOIN sw USING (work_id) JOIN kw ON kw.d = sw.d AND kw.pk = cp.pk
        GROUP BY 1, 2""").fetchall()}
    state = dict(people=people, pos=pos, feats=feats, gold=gold, names=names, pop=pop, cocite=cocite, corpus=corpus,
                 refkeys=refkeys, proven={i: sorted(v) for i, v in proven.items()})
    import pickle
    with open(CACHE / 'state.pkl', 'wb') as f:
        pickle.dump({k: v for k, v in state.items() if k != 'people'}, f)
    finish(args, state)


# ---------------------------------------------------------------- finish: tune, evaluate, write

def band(n):
    return '0' if n == 0 else '1' if n == 1 else '2' if n == 2 else '3-5' if n <= 5 else '6-20' if n <= 20 else '21+'


JUDGE = None    # (linked key, true key) -> 'right' | 'dup' | 'wrong'; set by finish()


def evaluate(rows, pos, pop, P, cocite, namesake=False):
    """rows: (mode, i, true key, features). -> per-row outcomes (..., state, linked key, branch, class, ...);
    class: 'right', 'dup' (another key of the same person: same names, no conflicting LC authority or ORCID), 'wrong'."""
    out = []
    for mode, i, g, fe in rows:
        st, k, br, cands, sig = rule(pos[i], fe, pop, P, cocite)
        cls = None if st != 'linked' else 'right' if k == g else JUDGE(k, g) if JUDGE else 'wrong'
        out.append((mode, i, g, st, k, br, cls, sig, fe))
    return out


def summarise(outs, by=None):
    """precision / recall of 'linked' over gold outcomes, grouped by a function of the outcome."""
    agg = defaultdict(lambda: Counter())
    for o in outs:
        mode, i, g, st, k, br, right, sig, fe = o
        keys = ['all'] if by is None else by(o)
        for key in (keys if isinstance(keys, list) else [keys]):
            a = agg[key]
            a['gold'] += 1
            if st == 'linked':
                a['linked'] += 1
                a[right] += 1
            a['state:' + st] += 1
    res = {}
    for key, a in sorted(agg.items(), key=lambda x: str(x[0])):
        res[str(key)] = dict(gold=a['gold'], linked=a['linked'], right=a['right'], duplicate_key=a['dup'], wrong=a['wrong'],
                             precision=round((a['right'] + a['dup']) / a['linked'], 4) if a['linked'] else None,
                             precision_strict_key=round(a['right'] / a['linked'], 4) if a['linked'] else None,
                             recall=round((a['right'] + a['dup']) / a['gold'], 4) if a['gold'] else None,
                             possible=a['state:possible'], none=a['state:none'])
    return res


GRID = dict(RARE_LC=[-1, 0, 1, 2], RARE_OA=[1, 2, 3, 5, 10, 20, 10 ** 6], SPAN=[(5, 10), (10, 20), (10, 40)],
            SPAN_MIN=[1, 2, 3], COCITE_FACT=[0, 2, 5])


def tune(gold_tune, names, pos, pop, cocite):
    """Every grid point on the tuning half: gold precision/recall of 'linked' and the proven-namesake link rate."""
    import itertools
    res = []
    for rl, ro, (sb, sa), sm, cf in itertools.product(GRID['RARE_LC'], GRID['RARE_OA'], GRID['SPAN'], GRID['SPAN_MIN'], GRID['COCITE_FACT']):
        if rl == -1 and ro != GRID['RARE_OA'][0]:
            continue
        P = dict(RARE_LC=rl, RARE_OA=ro, SPAN_BEFORE=sb, SPAN_AFTER=sa, SPAN_MIN=sm, COCITE_FACT=cf)
        g = evaluate(gold_tune, pos, pop, P, cocite)
        n = evaluate(names, pos, pop, P, cocite)
        linked = sum(o[3] == 'linked' for o in g)
        right = sum(o[6] in ('right', 'dup') for o in g)
        nl = sum(o[3] == 'linked' for o in n)
        res.append(dict(P=P, linked=linked, right=right, gold=len(g), precision=right / linked if linked else 1.0,
                        recall=right / len(g), namesake_linked=nl, namesake_n=len(n), namesake_rate=nl / len(n) if n else 0))
    return res


def finish(args, state):
    people, pos, feats, gold, names, pop, cocite = (state[k] for k in ('people', 'pos', 'feats', 'gold', 'names', 'pop', 'cocite'))
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if getattr(args, 'reuse_tuning', False):
        # rewrite the outputs with the parameters and measures already in report.json (no re-tuning)
        report = json.loads((out / 'report.json').read_text())
        report = {k: report[k] for k in ('date', 'graph', 'round1', 'gold', 'round2_trials', 'tuning', 'held_out',
                                         'held_out_detail_at_99') if k in report}
        P = dict(report['tuning']['chosen'])
        state['results'] = [rule(p, feats[i], pop, P, cocite) for i, p in enumerate(pos)]
        state['P'] = P
        write_outputs(args, state, report)
        return
    report = dict(date='2026-11-10', graph='build/graph as built 2026-11-10 10:32 (a few hours behind the key log; '
                  'duplicate merges were being applied meanwhile): person keys are as of that build')
    r1 = CACHE / 'round1' / 'report.json'
    if r1.exists():
        # the first round's numbers (rule of round 1, span margin 40), kept so the change is visible
        old = json.loads(r1.read_text())
        old_link = {k: v for k, v in old.get('linkage', {}).items() if k != 'top_possible'}
        report['round1'] = dict(params=old.get('tuning', {}).get('chosen'), gold=old.get('gold'),
                                held_out=old.get('held_out', {}).get('chosen'), linkage=old_link,
                                candidate_duplicates=old.get('candidate_duplicates'), hand_checks=old.get('hand_checks'))
    global JUDGE

    def judge(k, g):
        """A link to another key than the gold one: the same person under a duplicate key when the names agree and
        no LC authority or ORCID conflicts; else wrong."""
        fk, fg = forms(people.label.get(k, '')), forms(people.label.get(g, ''))
        if not any(a[0] == b[0] and name_level(a[2], b[2]) for a in fk for b in fg):
            return 'wrong'
        for a, b in ((people.lcnaf, people.lcnaf), (people.orcid, people.orcid)):
            if a.get(k) and b.get(g) and not a[k] & b[g]:
                return 'wrong'
        return 'dup'
    JUDGE = judge
    # gold rows whose source name does not agree with the gold key's name: the identifier is likely misassigned
    # (OpenAlex puts Luis Navarro García's articles under Jesús R. Navarro-García's ORCID); left out of the measure
    mismatch = [r for r in gold if r[2] not in r[3]['cands']]
    gold = [r for r in gold if r[2] in r[3]['cands']]
    report['gold'] = dict(rows=Counter(r[0] for r in gold), left_out_name_disagrees=Counter(r[0] for r in mismatch),
                          namesake_rows=Counter(r[0] for r in names))
    # ---- round 2 (2026-11-10, coordinator's decisions): the round-1 choice is the base (LC: no other authority of
    # the name; OpenAlex: at most 20 author ids; span margins 10 before / 20 after, not 40; co-citation support only;
    # a different ORCID on the key blocks unless a second fact exists). Each addition is tried alone on the tuning half
    # of the gold set and on every namesake test, and admitted only if the links it adds are >= 99% right on gold and
    # add at most ADD_MAX of each namesake test's rows (the round-1 rate was 0.11%; ceiling 0.15%).
    real_modes = ('lc-authority-known', 'openalex-orcid-hidden')
    tune_rows = [r for r in gold if r[0] in real_modes and stable_half(r[2]) == 0]
    held_rows = [r for r in gold if stable_half(r[2]) == 1]
    tests = sorted({r[0] for r in names} - {'openalex-namesake'})
    # base also: a key dated by a single work is placed only 10 years after it (Sweetman: 3 false links at 20, 478 of
    # 24,362 held-out gold links lost), and self-citation / a student's thesis citing do not tie a variant or initial
    # name (Carrera Quezada; 2 gold links lost) -- both measured on the round-2 state before this run
    base = dict(RARE_LC=0, RARE_OA=20, SPAN_BEFORE=10, SPAN_AFTER=20, SPAN_AFTER_1=10, SPAN_MIN=1, COCITE_FACT=0,
                FACTS=BASE_FACTS, TOPICAL_FULL_ONLY=True, ORCID_SOFT=True, FULLNAME=False, RARE_OA_FULL=3, VARIANT=False, XDATE=())
    additions = {'fullname (OpenAlex <= 3)': dict(FULLNAME=True, RARE_OA_FULL=3),
                 'fullname (OpenAlex <= 10)': dict(FULLNAME=True, RARE_OA_FULL=10),
                 'variant spelling rare': dict(VARIANT=True),
                 'dating: corpus span': dict(XDATE=('corpus-span',)),
                 'dating: supervision/affiliation years': dict(XDATE=('sup-aff',)),
                 'dating: first citing year - 50': dict(XDATE=('cites',))}
    for f in NEW_FACTS:
        additions[f'fact: {f}'] = dict(FACTS=BASE_FACTS + (f,))

    def measure(P, rows_g, rows_n):
        g = evaluate(rows_g, pos, pop, P, cocite)
        n = evaluate(rows_n, pos, pop, P, cocite)
        return g, n

    def ns_links(n):
        """namesake links: in the masked-author tests only links to the proven namesake count; elsewhere any link"""
        c = Counter()
        for o in n:
            if o[3] == 'linked' and ('masked' not in o[0] or o[4] == o[2]):
                c[o[0]] += 1
        return c
    n_rows = Counter(r[0] for r in names)
    g0, n0 = measure(base, tune_rows, names)
    base_links = {(o[0], o[1], o[2]) for o in g0 if o[3] == 'linked'}
    base_ns = {(o[0], o[1], o[2]) for o in n0 if o[3] == 'linked' and ('masked' not in o[0] or o[4] == o[2])}
    trial = {}
    for name, add in additions.items():
        P = dict(base, **add)
        g, n = measure(P, tune_rows, names)
        new = [o for o in g if o[3] == 'linked' and (o[0], o[1], o[2]) not in base_links]
        lost = sum(1 for o in g if o[3] != 'linked' and (o[0], o[1], o[2]) in base_links)
        new_ns = Counter(o[0] for o in n if o[3] == 'linked' and ('masked' not in o[0] or o[4] == o[2]) and (o[0], o[1], o[2]) not in base_ns)
        right = sum(o[6] in ('right', 'dup') for o in new)
        ok = (not new or right / len(new) >= 0.99) and all(new_ns[t] / n_rows[t] <= ADD_MAX for t in tests if n_rows[t])
        if name.startswith('fact:') and not new:
            ok = False          # a fact that adds no gold link cannot be shown to hold: not admitted (inst-name)
        trial[name] = dict(add={k: v for k, v in add.items() if k != 'FACTS'} or {'FACTS': '+' + add['FACTS'][-1]},
                           gold_new_links=len(new), gold_new_right=right, gold_lost=lost,
                           namesake_new_links={t: new_ns[t] for t in tests}, admitted=ok)
        print(name, trial[name], flush=True)
    # the admitted additions together (of the two fullname thresholds, the looser one if both pass)
    P = dict(base)
    facts = list(BASE_FACTS)
    for name, t in trial.items():
        if not t['admitted']:
            continue
        add = additions[name]
        if 'FACTS' in add:
            facts.append(add['FACTS'][-1])
        elif 'XDATE' in add:
            P['XDATE'] = tuple(P['XDATE']) + add['XDATE']
        else:
            P.update(add)
    P['FACTS'] = tuple(facts)
    report['round2_trials'] = dict(base=base, tuning_rows=len(tune_rows), namesake_rows=dict(n_rows), add_max=ADD_MAX,
                                   base_namesake_links=dict(ns_links(n0)), trials=trial)
    choice = {'base (round-1 choice, span after 20)': dict(P=base), 'chosen': dict(P=P)}
    report['tuning'] = dict(chosen=P, base=base)
    # ---- held-out evaluation
    ev = {}
    for t, c in choice.items():
        outs = evaluate(held_rows, pos, pop, c['P'], cocite)
        ns = evaluate(names, pos, pop, c['P'], cocite)
        ev[t] = dict(P=c['P'], by_mode=summarise(outs, by=lambda o: o[0]),
                     namesake_rows=dict(n_rows), namesake_links=dict(ns_links(ns)),
                     namesake_links_by_branch=dict(Counter(f'{o[0]}|{o[5]}' for o in ns if o[3] == 'linked' and ('masked' not in o[0] or o[4] == o[2]))))
        if t == 'chosen':
            held, nso = outs, ns
    report['held_out'] = ev
    real = [o for o in held if o[0] in real_modes]
    stress = [o for o in held if o[0] == 'lc-no-authority']

    def br(o):
        return o[5] if o[3] == 'linked' else 'not-linked'

    def rb(o):
        fe = o[8]
        return [f"{o[0]}|lc_n {band(pop[0].get(fe.get('name_key'), 0))}"] if fe.get('name_key') else [f'{o[0]}|unparsed']

    def oab(o):
        fe = o[8]
        return [f"{o[0]}|oa_n {band(pop[1].get(fe.get('name_key'), 0))}"] if fe.get('name_key') else [f'{o[0]}|unparsed']

    def dec(o):
        y = pos[o[1]]['year']
        return f"{o[0]}|{(y // 10 * 10) if y else 'no year'}"

    def ini(o):
        levs = {c['lev'] for c in o[8]['cands'].values()}
        return f"{o[0]}|{'initial' if o[8].get('src_initial') else 'no candidate' if not levs else 'full' if 'full' in levs else sorted(levs)[0]}"
    report['held_out_detail_at_99'] = dict(
        by_mode=summarise(held, by=lambda o: o[0]),
        branch_precision={m: summarise([o for o in held if o[0] == m and o[3] == 'linked'], by=lambda o: o[5]) for m in
                          ('lc-authority-known', 'openalex-orcid-hidden', 'lc-no-authority')},
        by_lc_rarity=summarise(held, by=rb), by_oa_rarity=summarise(held, by=oab), by_decade=summarise(held, by=dec),
        by_initial=summarise(held, by=ini),
        by_branch_all=summarise(held, by=lambda o: f'{o[0]}|{o[3]}|{o[5]}'),
        branch_recall={m: summarise([o for o in held if o[0] == m], by=lambda o: o[5] if o[3] == 'linked' else 'not linked') for m in
                       ('lc-authority-known', 'openalex-orcid-hidden', 'lc-no-authority')})
    # wrong links on the held-out half, for reading
    wrong = [o for o in held if o[6] in ('wrong', 'dup')]
    with open(out / 'gold-wrong.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['mode', 'class', 'branch', 'source_name', 'title', 'year', 'true_key', 'true_label', 'linked_key', 'linked_label', 'signals'])
        for o in wrong:
            p = pos[o[1]]
            w.writerow([o[0], o[6], o[5], p['name'], p['title'], p['year'], o[2], people.label.get(o[2]), o[4], people.label.get(o[4]), ' '.join(o[7])])
    with open(out / 'namesake-links.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['test', 'branch', 'source_name', 'source_id', 'title', 'year', 'key', 'key_label', 'key_lcnaf', 'key_orcid', 'signals'])
        for o in nso:
            if o[3] == 'linked' and ('masked' not in o[0] or o[4] == o[2]):
                p = pos[o[1]]
                w.writerow([o[0], o[5], p['name'], ';'.join(p['lc']) or p['orcid'], p['title'], p['year'], o[2], people.label.get(o[2]),
                            ';'.join(people.lcnaf.get(o[2], ())), ';'.join(people.orcid.get(o[2], ())), ' '.join(o[7])])
    # ---- the real run
    results = []
    for i, p in enumerate(pos):
        results.append(rule(p, feats[i], pop, P, cocite))
    state['results'] = results
    state['P'] = P
    write_outputs(args, state, report)


def write_outputs(args, state, report):
    people, pos, feats, pop, cocite, corpus, results = (state[k] for k in ('people', 'pos', 'feats', 'pop', 'cocite', 'corpus', 'results'))
    out = args.out
    rows = []
    for i, p in enumerate(pos):
        st, k, br, cands, sig = results[i]
        sid = ';'.join(p['lc']) if p['src'] == 'lc' else ';'.join(x for x in (p['orcid'] and 'orcid:' + p['orcid'], p['oa_author'] and 'openalex:' + p['oa_author']) if x)
        rows.append(dict(source=p['src'], source_work_id=p['swork'], work_id=p['work_id'], position=p['pos'], role=p['role'],
                         raw_name=p['name'], corpus_authors=corpus.get(p['work_id'], ''), source_person_id=sid, state=st,
                         branch=br, key=k or '', candidates='|'.join(cands if st != 'exact' else []), n_candidates=len(cands) if st != 'exact' else 1,
                         signals=' '.join(sig), year=p['year'] or '', title=p['title'] or '', citing_theses=p['citing']))
    cols = list(rows[0])
    with gzip.open(out / 'links.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    # ---- linkage counts (positions, works, citing theses at stake), per source
    link = {}
    for src in ('lc', 'openalex'):
        R = [r for r in rows if r['source'] == src]
        d = dict(positions=len(R))
        st = defaultdict(lambda: [0, set(), 0])
        for r in R:
            key = r['state'] + (':one-candidate' if r['state'] == 'possible' and r['n_candidates'] == 1 else ':several' if r['state'] == 'possible' else '')
            for kk in (r['state'], key) if key != r['state'] else (r['state'],):
                a = st[kk]
                a[0] += 1
                if r['work_id'] not in a[1]:
                    a[1].add(r['work_id'])
                    a[2] += int(r['citing_theses'])
        d['states'] = {k: dict(positions=v[0], works=len(v[1]), citing_theses=v[2]) for k, v in sorted(st.items())}
        d['branches'] = dict(Counter(r['branch'] for r in R if r['state'] in ('linked', 'possible', 'none')).most_common())
        works = defaultdict(set)
        cit = {}
        for r in R:
            works[r['work_id']].add(r['state'])
            cit[r['work_id']] = int(r['citing_theses'])
        best = Counter()
        bcit = Counter()
        for w_, ss in works.items():
            b = next(s for s in ('exact', 'linked', 'possible', 'none') if s in ss)
            best[b] += 1
            bcit[b] += cit[w_]
        d['works_by_best_state'] = {k: dict(works=best[k], citing_theses=bcit[k]) for k in ('exact', 'linked', 'possible', 'none')}
        d['works_with_an_author_credited'] = best['exact'] + best['linked']
        d['works'] = len(works)
        link[src] = d
    poss = sorted([r for r in rows if r['state'] == 'possible'], key=lambda r: -int(r['citing_theses']))
    with gzip.open(out / 'possible-ranked.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols + ['candidate_labels'])
        w.writeheader()
        for r in poss:
            w.writerow(dict(r, candidate_labels='|'.join(people.label.get(k, '') for k in r['candidates'].split('|') if k)))
    link['top_possible'] = [dict(source=r['source'], work_id=r['work_id'], title=r['title'], year=r['year'], name=r['raw_name'],
                                 citing_theses=int(r['citing_theses']), branch=r['branch'],
                                 candidates={k: people.label.get(k, '') for k in r['candidates'].split('|') if k})
                            for r in poss[:50]]
    report['linkage'] = link
    report['rule'] = dict(params=state['P'], text=RULE_TEXT)
    # ---- candidate duplicates: several live candidates that look like one person
    dup = defaultdict(lambda: dict(works=set(), citing=0))
    for i, p in enumerate(pos):
        st, k, br, cands, sig = results[i]
        if st not in ('possible', 'linked') or len(cands) < 2:
            continue
        cs = feats[i]['cands']
        for a in cands:
            for b in cands:
                if a >= b or b in people.not_same.get(a, ()):
                    continue
                la, lb = people.label[a], people.label[b]
                fa, fb = forms(la), forms(lb)
                same = [x for x in fa for y in fb if x[0] == y[0] and x[2] == y[2]]
                if not same:
                    continue        # the same family and the same given names, word for word
                f, _, g = same[0]
                # a common name alone ('Smith, Donald' x5, AHA namesakes) is no sign of one person: two written given
                # names, or a name no other LC authority bears
                if len(g[0]) == 1 or sum(len(w) > 1 for w in g) < 2 and pop[0].get((f, g[0]), 0) > 1:
                    continue
                pa, pb = people.phd.get(a), people.phd.get(b)
                if pa and pb and abs(pa - pb) > 1:
                    continue        # two PhDs, two people
                if people.lcnaf[a] and people.lcnaf[b] and not people.lcnaf[a] & people.lcnaf[b]:
                    continue
                if people.orcid[a] and people.orcid[b] and not people.orcid[a] & people.orcid[b]:
                    continue
                wa, wb = people.window(a), people.window(b)
                if isinstance(wa, tuple) and isinstance(wb, tuple) and wa[0] and wb[0] and abs(wa[0] - wb[0]) > 15:
                    continue
                d = dup[a, b]
                if p['work_id'] not in d['works']:
                    d['works'].add(p['work_id'])
                    d['citing'] += p['citing']
    with gzip.open(out / 'candidate-duplicates.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key_a', 'label_a', 'key_b', 'label_b', 'pids_a', 'pids_b', 'window_a', 'window_b', 'works_a', 'works_b',
                    'possibly_same_marked', 'source_works', 'citing_theses_at_stake'])
        ps = set()
        import duckdb
        for a, b in duckdb.connect().execute(f"SELECT \"from\", \"to\" FROM '{GRAPH}/possibly_same.parquet'").fetchall():
            ps.add((a, b))
            ps.add((b, a))
        for (a, b), d in sorted(dup.items(), key=lambda x: -x[1]['citing']):
            pid = lambda k: ';'.join(sorted(['lcnaf:' + x for x in people.lcnaf[k]] + ['orcid:' + x for x in people.orcid[k]]))
            w.writerow([a, people.label[a], b, people.label[b], pid(a), pid(b), people.window(a), people.window(b),
                        (people.span.get(a) or (None, None, 0))[2], (people.span.get(b) or (None, None, 0))[2],
                        (a, b) in ps, len(d['works']), d['citing']])
    report['candidate_duplicates'] = dict(pairs=len(dup), already_possibly_same=sum(1 for ab in dup if ab in ps),
                                          citing_theses_at_stake=sum(d['citing'] for d in dup.values()))
    # hand checks, when present (written by hand, not by this script): audit-sample.csv, namesake-judged.csv
    hc = {}
    if (out / 'audit-sample.csv').exists():
        with open(out / 'audit-sample.csv', newline='', encoding='utf-8') as f:
            a = list(csv.DictReader(f))
        hc['audit'] = {smp: dict(Counter(r['verdict'] for r in a if r['sample'] == smp)) for smp in sorted({r['sample'] for r in a})}
        hc['audit_by_state_now'] = {smp: dict(Counter(f"{r['state_now']}|{r['verdict']}" for r in a if r['sample'] == smp))
                                    for smp in sorted({r['sample'] for r in a})}
        hc['audit_note'] = ("round 2: 'round2-newly-linked' was drawn from links new in round 2 before the last three fixes, "
                            "which were designed from its three wrong rows (state_now shows them no longer linked); the "
                            "round-1 audits are under round1.hand_checks")
    if (out / 'namesake-judged.csv').exists():
        with open(out / 'namesake-judged.csv', newline='', encoding='utf-8') as f:
            hc['namesake_links_judged'] = dict(Counter(f"{r['test']}|{r['verdict']}" for r in csv.DictReader(f)))
    if hc:
        report['hand_checks'] = hc
    (out / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(dict(linkage={k: v for k, v in link.items() if k != 'top_possible'}), indent=1, default=str))


RULE_TEXT = [
    "exact: the source's LC name authority (its URI, or its heading as LC prints it) or ORCID is on a key.",
    "Candidates: keys with the same family name whose given names agree (name_level): 'full' = first given names "
    "written out and identical; 'variant' = a short form or transliteration (Ben/Benjamin, also Norma/Norman); "
    "'initial' = an initial on either side. Jim and James do not agree at all.",
    "A candidate is set aside as a different person (state none, 'only-proven-namesakes') when it holds an LC "
    "authority other than the source's, or its life years differ from the LC dates of the source by more than a year, "
    "or its PhD/works fall before the source person's age 15/20 or its articles after the source person's death.",
    "Date test: the work's year inside the key's career window (birth+20, else PhD-10; to death+2, no upper bound for "
    "books); a key with neither, inside its own dated works widened SPAN_BEFORE/SPAN_AFTER years (SPAN_MIN works at "
    "least); a key with no dated work fails. A pooled key, a key whose birth and PhD contradict, or a key holding a "
    "different ORCID never passes (kept as possible).",
    "linked 'unique-rare': exactly one candidate, it passes the date test, the names agree 'full', and the name is rare "
    "outside the graph: no other LC name authority bears the family + first given name (RARE_LC others) and at most "
    "RARE_OA OpenAlex History author ids do.",
    "linked 'unique-second-fact': exactly one candidate, it passes the date test, and an independent fact ties it to "
    "the work: the printed institution's ROR is one of the key's dated affiliations (system names excluded), a "
    "co-author exact-linked on the same work is a known co-author of the key, the OpenAlex author id is tied to the key "
    "through another work the graph credits to it, or the work cites the key's own works. Needed when the name is "
    "common, 'variant' or 'initial'.",
    "linked 'several-one-survives': several candidates, exactly one passes the date and contradiction tests, and it has "
    "such a fact.",
    "Co-citation (theses citing both the work and the key's works) is recorded as support only: topic never links.",
    "Everything else with a candidate is possible (candidates listed); no name-compatible key is none.",
    "Round 2 (2026-11-10): span margin after 20 years, 10 for a key dated by a single work; 'unique-rare-fullname': the "
    "first two given names printed alike on both sides (or an initial against a name, when LC holds no other "
    "authority with that first name + initial), no other LC authority and at most 10 OpenAlex ids with them; "
    "'unique-rare-variant': a spelling variant of 5+ letters (Sebastián/Sebastiaan), rare counting both spellings; "
    "dating for keys without window or span: the years of their works as the dissertation corpus cites them, their "
    "supervision and dated affiliations (-35/+25), or the first year a thesis cites them (-50, lower bound only); "
    "a key's supervision/affiliations/cited works before the source person was 20 prove two people; "
    "second fact added: a thesis the key supervised cites the work (not for variant/initial names, nor self-citation); "
    "a different ORCID on the key yields to a second fact; an OpenAlex ORCID whose owner agrees only by initial or "
    "variant while another key carries the printed name in full does not credit (L. H. / Lyndal Roper). "
    "Tried and not admitted: same journal (a proven namesake link), cited by the key's own thesis (a proven namesake "
    "link), printed institution name without ROR (no gold yield).",
]


def finish_cached(args):
    import duckdb
    import pickle
    with open(CACHE / 'state.pkl', 'rb') as f:
        state = pickle.load(f)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET enable_progress_bar=false")
    state['people'] = People(db)
    finish(args, state)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('oa-extract')
    a.add_argument('--workers', type=int, default=3)
    for name in ('run', 'finish'):
        a = sub.add_parser(name)
        a.add_argument('--out', type=Path, default=OUT)
        if name == 'finish':
            a.add_argument('--reuse-tuning', action='store_true', help="keep report.json's parameters and measures")
    args = ap.parse_args()
    if args.cmd == 'oa-extract':
        oa_extract(args)
    elif args.cmd == 'finish':
        finish_cached(args)
    else:
        run(args)


if __name__ == '__main__':
    main()
