"""Duplicate person keys -> a tiered merge PROPOSAL (2026-11-11; §8 class 9). Writes, never applies.

Candidate pairs come from three places:
- the work-people linker's duplicate groups (data/identifiers/work-people-2026-11-11/candidate-duplicates.csv.gz:
  every pair inside a group);
- the cited-work author linker's pairs (data/identifiers/cited-work-authors-2026-11-10/candidate-duplicates.csv.gz);
- review-credit-only keys (every anchor `review-credit:`) whose name agrees in full with exactly one established key.

Each pair is judged on the two keys' own facts (build/graph of the day for works, affiliations and anchors; the key-log
cache for the current status, anchors and `not-same:` marks; data/person-facts/life-years.csv.gz):
- **C, rejected**: the names do not agree in full (family name, a written-out first given name identical on both sides,
  no short forms or transliterations: Jim never agrees with James; every second given name printed on both sides
  agrees, an initial with the name it begins); different LC, Wikidata, ISNI or IdRef identifiers (GND and VIAF keep
  duplicate records); birth or death years more than a year apart; activity on one key before the other's birth + 18
  or reviews/articles/posts after its death + 3; a `not-same:` mark or an outside-review 'different' verdict.
- **B, review queue**: names agree and nothing clashes, but one of: two different ORCIDs (one person can have two:
  a review list, never an automatic merge); two PhD years more than two apart; a key behind the merge guard; an
  outside-review 'unclear' verdict; another established key outside the candidate group, or an LC name authority on
  no key of the group, bearing an agreeing full name; no positive fact. B1 = the last reason only (a unique name with
  nothing against it; the owner may accept B1 wholesale); B2 = any other.
- **A, merge now**: names agree in full, no clash, dates compatible, unique (no other established key, no other LC
  authority), and a positive fact:
  shared work (both credited by key-log claims on one work key), or a shared title (normalised, 20+ characters and
  3+ words, years within two), or the same institution in an overlapping period (dated affiliations, review-credit
  institutions dated by their reviews, the awarding institution of a key's thesis in its year; intervals widened by
  two years), with the printed institution strings compared on their distinctive words
  (key_review_credit_merges.agree) when not grounded to one institution key.
A-pairs join into clusters; a cluster whose keys would bring two identifiers of a clashing scheme or two birth years
together goes back to B. The survivor is the key with most public identifier families, then most works, then the
oldest number. Topic or field is never read.

Gold test (report.json `gold`): negatives are `not-same:` pairs, outside-review 'different' pairs, and namesake pairs
of established keys with two LC authorities whose identifiers and life years are masked (the rule then sees only
names, works, affiliations and uniqueness); positives are artificial splits of keys holding two or more public
identifier families and six or more works (works and affiliations dealt alternately, identifiers divided by family).

    python3 scripts/propose_person_dup_merges.py --out data/identifiers/person-dup-merges-2026-11-11
    # after review:  flock .keylog.lock python3 scripts/identifiers.py apply data/identifiers/person-dup-merges-2026-11-11/proposal.json
"""
import argparse
import csv
import glob
import gzip
import json
import random
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
from link_cited_work_authors import forms, heading_dates, nfold  # noqa: E402
from key_review_credit_merges import agree as inst_agree  # noqa: E402

ROOT = I.ROOT
G = ROOT / 'build/graph'
IDS = ROOT / 'data/identifiers'
WP = IDS / 'work-people-2026-11-11/candidate-duplicates.csv.gz'
CW = IDS / 'cited-work-authors-2026-11-10/candidate-duplicates.csv.gz'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
CACHE = ROOT / 'build/keylog-state.sqlite'
WPS = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/workpeople')
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/proposals')
CLASH = ('lcnaf', 'wd', 'isni', 'idref')
PUBLIC = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'atlas', 'ol')
SLACK = 2


# ------------------------------------------------------------------ names

def strict_agree(ga, gb):
    """Given names agree in full: the first written-out given name identical (a leading initial may precede it:
    'J. Garry' / 'Garry'), every other given name of the shorter list equal to one of the longer's or an initial of
    one. No short forms or transliterations."""
    if not ga or not gb:
        return False
    a, b = list(ga), list(gb)
    wa = [w for w in a if len(w) > 1]
    wb = [w for w in b if len(w) > 1]
    if not wa or not wb:
        return False
    # the first written-out name of each must be the same name, and nothing written before it on either side may
    # disagree (an initial before it must be an initial of a name on the other side)
    if wa[0] != wb[0]:
        return False
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    rest = list(long_)
    for w in short:
        hit = next((t for t in rest if t == w or (len(w) == 1 and t[0] == w) or (len(t) == 1 and w[0] == t)), None)
        if hit is None:
            return False
        rest.remove(hit)
    return True


def name_forms(label):
    return [(f, g) for f, _, g in forms(label)]


SUFFIX_RE = re.compile(r'(?i)(?:,|\s)\s*(jr|sr|ii|iii|iv)\.?(?=,|\s|$)')


def suffix(label):
    m = SUFFIX_RE.search(label or '')
    return m.group(1).lower() if m else ''


def names_agree(la, lb):
    if suffix(la) != suffix(lb) and (suffix(la) or suffix(lb)) and {suffix(la), suffix(lb)} != {'', 'jr'} or \
            {suffix(la), suffix(lb)} == {'jr', 'sr'}:
        return False                    # father and son: 'Jr.' against 'Sr.', 'II' against 'III'
    return any(fa == fb and strict_agree(ga, gb) for fa, ga in name_forms(la) for fb, gb in name_forms(lb))


def names_identical(la, lb):
    """The same given names printed on both sides (no extra name or initial on one): 'Amy' is not identical to
    'Amy Dru', 'Ari' not to 'Ari Y.'"""
    return suffix(la) == suffix(lb) and any(fa == fb and ga == gb for fa, ga in name_forms(la) for fb, gb in name_forms(lb))


def norm_title(t):
    t = nfold(t or '')
    t = re.sub(r'^(review of|rezension zu|reviewed work\(s\):)\s*', '', t)
    t = re.sub(r'[^a-z0-9 ]+', ' ', t)
    t = ' '.join(t.split())
    return t if len(t) >= 20 and len(t.split()) >= 3 else None


# ------------------------------------------------------------------ facts

def load_people(db):
    rows = db.execute(f"SELECT key, label, resolution, anchors FROM '{G}/person.parquet'").fetchall()
    return {k: dict(label=l or '', resolution=r, anchors=list(a or [])) for k, l, r, a in rows}


def cache_state(keys):
    """Current status, label, anchors and not-same marks of `keys` from the key-log cache (read-only)."""
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    out = {}
    keys = list(keys)
    for i in range(0, len(keys), 900):
        chunk = keys[i:i + 900]
        q = ','.join('?' * len(chunk))
        for k, typ, label, status, res, anchors, rep in con.execute(
                f'SELECT key, type, label, status, resolution, anchors, replaced_by FROM keys WHERE key IN ({q})', chunk):
            out[k] = dict(type=typ, label=label, status=status, resolution=res, anchors=json.loads(anchors or '[]'),
                          replaced_by=json.loads(rep or '[]'))
    notsame = defaultdict(set)
    for k, m in con.execute("SELECT key, member FROM members WHERE member >= 'not-same:' AND member < 'not-same;'"):
        notsame[k].add(m[len('not-same:'):])
    seq = int(dict(con.execute('SELECT k, v FROM meta').fetchall())['seq'])
    con.close()
    return out, notsame, seq


def review_verdicts():
    """Outside-review verdicts on pairs that were not merged: (a, b) -> 'different'/'unclear' (+ confidence)."""
    out = {}
    for p in glob.glob(str(IDS / 'possible-same*/applied-*/held.json')) + glob.glob(str(IDS / 'possible-same*/held.json')):
        try:
            items = json.loads(Path(p).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict) and it.get('a') and it.get('b') and it.get('verdict') in ('different', 'unclear'):
                out[frozenset((it['a'], it['b']))] = f"{it['verdict']}:{it.get('confidence')}"
    return out


COMMON_TITLES = set()      # titles on five or more work keys ('Reviews in History', 'Introduction'): no fact


def load_common_titles(db):
    c = Counter()
    for (lab,) in db.execute(f"SELECT label FROM '{G}/work.parquet'").fetchall():
        t = norm_title(lab)
        if t:
            c[t] += 1
    COMMON_TITLES.update(t for t, n in c.items() if n >= 5)


class Facts:
    def __init__(self, db, people, keys):
        self.people = people
        db.execute('CREATE OR REPLACE TEMP TABLE want(key VARCHAR)')
        db.executemany('INSERT INTO want VALUES (?)', [(k,) for k in keys])
        self.works = defaultdict(set)
        self.titles = defaultdict(dict)
        self.years = defaultdict(list)          # (year, kind)
        for k, w, label, y, kind in db.execute(f"""
                SELECT a."from", a."to", w.label, w.year, w.kind FROM (
                    SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
                    UNION ALL SELECT "from", "to" FROM '{G}/edited.parquet' WHERE evidence = 'keylog') a
                JOIN want ON want.key = a."from" JOIN '{G}/work.parquet' w ON w.key = a."to" """).fetchall():
            self.works[k].add(w)
            t = norm_title(label)
            if t and t not in COMMON_TITLES:
                self.titles[k].setdefault(t, y)
            if y:
                self.years[k].append((y, kind))
        inst_label = dict(db.execute(f"SELECT key, label FROM '{G}/institution.parquet'").fetchall())
        self.affs = defaultdict(list)           # (inst key or None, label, lo, hi, source)
        for k, i, src, lo, hi in db.execute(f"""SELECT a."from", a."to", a.source, a.first_year, a.last_year
                FROM '{G}/affiliated_with.parquet' a JOIN want ON want.key = a."from" """).fetchall():
            self.affs[k].append((i, inst_label.get(i, ''), lo, hi, src))
        for k, i, y in db.execute(f"""SELECT a."from", b."to", w.year FROM (SELECT "from", "to" FROM '{G}/authored.parquet'
                WHERE evidence = 'keylog') a JOIN want ON want.key = a."from" JOIN '{G}/work.parquet' w ON w.key = a."to"
                JOIN '{G}/awarded_by.parquet' b ON b."from" = a."to" WHERE w.kind = 'thesis' AND w.year IS NOT NULL""").fetchall():
            self.affs[k].append((i, inst_label.get(i, ''), y - 6, y, 'thesis'))
        # printed review-credit institutions, dated by the key's reviews
        rev_years = defaultdict(list)
        for k, y in db.execute(f"""SELECT a."from", w.year FROM (SELECT "from", "to" FROM '{G}/authored.parquet'
                WHERE evidence = 'keylog') a JOIN want ON want.key = a."from" JOIN '{G}/work.parquet' w ON w.key = a."to"
                WHERE w.kind = 'review' AND w.year IS NOT NULL""").fetchall():
            rev_years[k].append(y)
        self.rev_years = rev_years
        # OpenAlex/JSTOR author positions credited to the key (key-log credit or an ORCID exact): the OpenAlex author
        # id with the ORCIDs printed there, and the institution printed with the work, in its year
        self.oa = defaultdict(lambda: defaultdict(set))
        P = f"read_parquet('{WPS}/positions*.parquet', union_by_name=true)"
        for k, oa, orc, y, insts, ip in db.execute(f"""
                SELECT p.credited, p.oa_author, p.orcid, p.year, p.insts, p.inst_printed FROM {P} p JOIN want ON want.key = p.credited
                UNION ALL
                SELECT r.key, p.oa_author, p.orcid, p.year, p.insts, p.inst_printed FROM '{WPS}/results.parquet' r
                JOIN {P} p USING (pid) JOIN want ON want.key = r.key WHERE r.state = 'exact'""").fetchall():
            if oa:
                self.oa[k][oa].add(orc or '')
            for nm in (list(insts or []) + ([ip] if ip else []))[:3]:
                if nm and y:
                    self.affs[k].append((None, nm, y, y, 'printed-with-work'))
        self.coauthors = defaultdict(set)
        for a, b in db.execute(f"""SELECT "from", "to" FROM '{G}/coauthored.parquet' c WHERE evidence = 'keylog'
                AND ("from" IN (SELECT key FROM want) OR "to" IN (SELECT key FROM want))""").fetchall():
            self.coauthors[a].add(b)
            self.coauthors[b].add(a)
        self.life = {}
        with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                b = int(r['birth']) if r['birth'].lstrip('-').isdigit() else None
                d = int(r['death']) if r['death'].lstrip('-').isdigit() else None
                if b or d:
                    self.life[r['key']] = (b, d)
        self.aha = {}
        for line in open(AHA, encoding='utf-8'):
            r = json.loads(line)
            if r.get('year'):
                self.aha['aha-phd:' + r['id']] = int(r['year'])

    def of(self, k, anchors, mask=False):
        """A key's facts as one dict (mask=True drops identifiers and life years: the namesake gold test)."""
        ids = defaultdict(set)
        rc = []
        for a in anchors:
            s, _, v = a.partition(':')
            ids[s].add(v)
            if s == 'review-credit' and '|' in v and not v.startswith('hnet-review:'):
                rc.append(v.split('|', 1)[1])
        ry = self.rev_years.get(k, [])
        affs = list(self.affs.get(k, []))
        for s in rc:
            affs.append((None, s, min(ry) if ry else None, max(ry) if ry else None, 'review-credit-string'))
        phd = {self.aha[a] for a in anchors if a in self.aha} | {y for y, kind in self.years.get(k, []) if kind == 'thesis'}
        f = dict(key=k, ids={} if mask else dict(ids), works=self.works.get(k, set()), titles=self.titles.get(k, {}),
                 years=self.years.get(k, []), affs=affs, life=(None, None) if mask else self.life.get(k, (None, None)),
                 phd=phd, oa={} if mask else {a: set(v) for a, v in self.oa.get(k, {}).items()},
                 coauthors=self.coauthors.get(k, set()))
        return f


def nyears(f):
    return [y for y, _ in f['years']] + [x for _, _, lo, hi, _ in f['affs'] for x in (lo, hi) if x]


def clash(fa, fb):
    """A reason the two keys cannot be one person, or None."""
    for s in CLASH:
        va, vb = fa['ids'].get(s, set()), fb['ids'].get(s, set())
        if va and vb and not (va & vb):
            return f'{s}-differs'
    (ba, da), (bb, db_) = fa['life'], fb['life']
    if ba and bb and abs(ba - bb) > 1:
        return 'birth-differs'
    if da and db_ and abs(da - db_) > 1:
        return 'death-differs'
    for x, y in ((fa, fb), (fb, fa)):
        b, d = x['life']
        if b:       # reviews, articles, theses and dated posts (not books: an edition can carry an old year)
            early = [v for v, kind in y['years'] if v < b + 16 and kind in ('review', 'article', 'thesis')]
            early += [hi for _, _, lo, hi, src in y['affs'] if hi and src not in ('lc_373', 'wikidata') and hi < b + 16]
            if early:
                return 'activity-before-adulthood'
        if d:
            late = [v for v, kind in y['years'] if v > d + 3 and kind in ('review', 'thesis')]
            late += [lo for _, _, lo, _, src in y['affs'] if lo and lo > d + 3 and src != 'printed-with-work']
            if late:
                return 'activity-after-death'
    return None


def positive(fa, fb, inst_cache):
    """The positive facts joining two keys (list of strings)."""
    out = []
    shared = fa['works'] & fb['works']
    if shared:
        out.append(f"shared-work:{sorted(shared)[0]}" + (f" (+{len(shared) - 1})" if len(shared) > 1 else ''))
    for t, y in fa['titles'].items():
        y2 = fb['titles'].get(t, -1)
        if y2 != -1 and (y is None or y2 is None or abs(y - y2) <= 2) and not (fa['works'] & fb['works']):
            out.append(f'shared-title:{t[:60]}|{y}|{y2}')
            break
    orc = fa['ids'].get('orcid', set()) | fb['ids'].get('orcid', set())
    for oa in set(fa['oa']) & set(fb['oa']):
        printed = {o for o in fa['oa'][oa] | fb['oa'][oa] if o}
        if len(printed) == 1 and printed <= orc:
            out.append(f'same-openalex-author:{oa}|orcid:{next(iter(printed))}')
            break
    co = (fa['coauthors'] & fb['coauthors']) - {fa['key'], fb['key']}
    if co:
        out.append(f"shared-coauthor:{sorted(co)[0]}" + (f" (+{len(co) - 1})" if len(co) > 1 else ''))
    for ia, la, loa, hia, sa in fa['affs']:
        if loa is None and hia is None:
            continue
        for ib, lb, lob, hib, sb in fb['affs']:
            if lob is None and hib is None:
                continue
            a0, a1 = (loa or hia) - SLACK, (hia or loa) + SLACK
            b0, b1 = (lob or hib) - SLACK, (hib or lob) + SLACK
            if a1 < b0 or b1 < a0:
                continue
            if ia and ib:
                same = ia == ib
            else:
                kk = (la, lb)
                if kk not in inst_cache:
                    inst_cache[kk] = bool(la and lb and inst_agree(la, lb))
                same = inst_cache[kk]
            if same:
                out.append(f'same-institution:{(la or lb)[:50]}|{sa}:{loa}-{hia}|{sb}:{lob}-{hib}')
                return out
    return out


# ------------------------------------------------------------------ candidate pairs

def read_pairs(people, cur):
    pairs = defaultdict(set)              # frozenset -> sources
    groups = []
    with gzip.open(WP, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ks = r['keys'].split('|')
            groups.append(ks)
            for a, b in combinations(ks, 2):
                pairs[frozenset((a, b))].add('work-people-group' + (':strict' if r['test'].startswith('strict') else ':loose'))
    with gzip.open(CW, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pairs[frozenset((r['key_a'], r['key_b']))].add('cited-work-authors')
    return pairs, groups


def review_credit_pairs(people, live, by_family):
    """review-credit-only keys whose name agrees in full with exactly one established key."""
    out, R = {}, Counter()
    for k, p in people.items():
        if k not in live or not p['anchors'] or not all(a.startswith('review-credit:') for a in p['anchors']):
            continue
        R['review_credit_only_keys'] += 1
        est = set()
        for fam, g in name_forms(p['label']):
            for k2, g2, res in by_family.get(fam, ()):
                if k2 != k and res == 'established' and k2 in live and strict_agree(g, g2):
                    est.add(k2)
        R[f'established_namesakes_{min(len(est), 2)}'] += 1
        if len(est) == 1:
            out[k] = next(iter(est))
    return out, R


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=IDS / 'person-dup-merges-2026-11-11')
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH}/duck'")
    R = Counter()
    people = load_people(db)
    pairs, groups = read_pairs(people, None)
    allkeys = set(people) | {k for p in pairs for k in p}
    cur, notsame, seq = cache_state(allkeys)
    R['keylog_seq'] = seq
    live = {k for k, v in cur.items() if v['type'] == 'person' and v['status'] not in I.RETIRED}
    for k in list(people):                   # current label and anchors (merges since the build moved anchors)
        if k in cur:
            people[k].update(label=cur[k]['label'], anchors=cur[k]['anchors'], resolution=cur[k]['resolution'])
    by_family = defaultdict(list)
    for k, p in people.items():
        if k in live:
            for fam, g in name_forms(p['label']):
                by_family[fam].append((k, g, p['resolution']))
    rc_pairs, rcR = review_credit_pairs(people, live, by_family)
    R.update({f'rc_{k}': v for k, v in rcR.items()})
    for a, b in rc_pairs.items():
        pairs[frozenset((a, b))].add('review-credit-only')
    R['candidate_pairs'] = len(pairs)
    R['candidate_pairs_by_source'] = Counter('+'.join(sorted({s.split(':')[0] for s in v})) for v in pairs.values())
    # candidate groups = connected components of all candidate pairs (keys believed to be one person)
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for p in pairs:
        a, b = tuple(p)
        parent[find(a)] = find(b)
    comp = defaultdict(set)
    for k in parent:
        comp[find(k)].add(k)
    group_of = {k: frozenset(comp[find(k)]) for k in parent}

    # LC authorities by family (last word), for the uniqueness test
    fams = {fam for p in pairs for k in p if k in people for fam, _ in name_forms(people[k]['label'])}
    last = {f.split()[-1] for f in fams if f}
    db.execute('CREATE OR REPLACE TEMP TABLE lastw(w VARCHAR)')
    db.executemany('INSERT INTO lastw VALUES (?)', [(w,) for w in last])
    lc_by_family = defaultdict(list)
    for lcid, label, lb_, ld_ in db.execute(f"""SELECT lcid, label, birth, death FROM (SELECT lcid, label, deprecated, birth, death,
            regexp_extract(lower(strip_accents(split_part(label, ',', 1))), '([a-z]+)[^a-z]*$', 1) AS w
            FROM read_parquet('{LC_NAMES}')) WHERE NOT coalesce(deprecated, false) AND w IN (SELECT w FROM lastw)""").fetchall():
        hb, hd = heading_dates(label)
        yb = int(lb_[:4]) if lb_ and lb_[:4].isdigit() else hb
        yd = int(ld_[:4]) if ld_ and ld_[:4].isdigit() else hd
        for fam, g in name_forms(label):
            if fam in fams:
                lc_by_family[fam].append((lcid, g, yb, yd))
    R['lc_authorities_read'] = sum(len(v) for v in lc_by_family.values())

    PROBES = ('p-143231', 'p-151402', 'p-151403', 'p-171364', 'p-173252', 'p-96495', 'p-4256', 'p-21351', 'p-133302')
    need = {k for p in pairs for k in p} | set(PROBES)
    load_common_titles(db)
    R['common_titles_ignored'] = len(COMMON_TITLES)
    F = Facts(db, people, need)
    verdicts = review_verdicts()
    from merge_guard import SINGLE_KEY_CHECKS, blocked_keys
    import keylog_snapshot as KS
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    state = KS.read_state()
    blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
    R['merge_guard_blocked_keys'] = len(blocked)
    inst_cache = {}

    def facts(k, mask=False):
        return F.of(k, people[k]['anchors'], mask)

    def window(f):
        ys = [y for y, kind in f['years'] if kind != 'book'] + [x for _, _, lo, hi, src in f['affs'] if src != 'lc_373'
                                                                  for x in (lo, hi) if x]
        ys = ys or [y for y, _ in f['years']]
        return (min(ys), max(ys)) if ys else None

    def could_be(life, win):
        """A namesake with these life years could have done what the key did (adult and alive in its window)."""
        if not win:
            return True
        b, d = life
        return not ((b and b + 16 > win[1]) or (d and d + 3 < win[0]))

    def uniqueness(a, b, grp, excl_lcids, fa, fb):
        """Other established keys (outside the group) and LC authorities (on no key of the group) with the name, whose
        dates let them be the person of either key."""
        others, lcs = set(), set()
        wins = [window(fa), window(fb)]
        for k in (a, b):
            for fam, g in name_forms(people[k]['label']):
                for k2, g2, res in by_family.get(fam, ()):
                    if k2 not in grp and res == 'established' and strict_agree(g, g2) and \
                            any(could_be(F.life.get(k2, (None, None)), w) for w in wins):
                        others.add(k2)
                for lcid, g2, lb, ld in lc_by_family.get(fam, ()):
                    if lcid not in excl_lcids and strict_agree(g, g2) and any(could_be((lb, ld), w) for w in wins):
                        lcs.add(lcid)
        return others, lcs

    def judge(a, b, fa, fb, grp, excl_lcids, use_marks=True):
        la, lb = people[a]['label'], people[b]['label']
        ev = dict(a=a, b=b, label_a=la, label_b=lb)
        if not names_agree(la, lb):
            return 'C', 'names-do-not-agree-in-full', ev
        if use_marks and (b in notsame.get(a, ()) or a in notsame.get(b, ())):
            return 'C', 'not-same-recorded', ev
        v = verdicts.get(frozenset((a, b))) if use_marks else None
        if v and v.startswith('different'):
            return 'C', f'outside-review-{v}', ev
        c = clash(fa, fb)
        if c:
            return 'C', c, ev
        pos = positive(fa, fb, inst_cache)
        if pos and not names_identical(la, lb):
            # one side prints a given name or initial the other lacks: an institution alone does not join them (two
            # people of one surname and first name at one university: Ari Kelman / Ari Y. Kelman, UC Davis)
            dropped = [p for p in pos if p.startswith('same-institution')]
            pos = [p for p in pos if not p.startswith('same-institution')]
            if dropped and not pos:
                ev['facts_not_counted'] = dropped
        ev['facts'] = pos
        others, lcs = uniqueness(a, b, grp, excl_lcids, fa, fb)
        ev['other_established'] = sorted(others)[:5]
        ev['other_lc'] = sorted(lcs)[:5]
        why = []
        oa, ob = fa['ids'].get('orcid', set()), fb['ids'].get('orcid', set())
        if oa and ob and not (oa & ob):
            why.append('two-orcids')
        if fa['phd'] and fb['phd'] and min(abs(x - y) for x in fa['phd'] for y in fb['phd']) > 2:
            why.append('two-phd-years')
        if suffix(la) != suffix(lb):
            why.append('name-suffix-differs')
        if use_marks and (a in blocked or b in blocked):
            why.append('merge-guard')
        if v:
            why.append(f'outside-review-{v}')
        if others:
            why.append('other-established-key-same-name')
        if lcs:
            why.append('other-lc-authority-same-name')
        if not pos:
            why.append('no-positive-fact')
        if why:
            return ('B1' if why == ['no-positive-fact'] else 'B2'), ';'.join(why), ev
        return 'A', 'facts:' + ';'.join(p.split(':')[0] for p in pos), ev

    def lcids_of(keys):
        return {a[len('lcnaf:'):] for k in keys if k in people for a in people[k]['anchors'] if a.startswith('lcnaf:')}

    # ---- judge every candidate pair
    rows = []
    for p, srcs in pairs.items():
        a, b = sorted(p, key=I._num if hasattr(I, '_num') else str)
        if a not in live or b not in live or a not in people or b not in people:
            R['pairs_key_gone'] += 1
            continue
        grp = group_of[a]
        tier, why, ev = judge(a, b, facts(a), facts(b), grp, lcids_of(grp))
        ev.update(tier=tier, why=why, sources='+'.join(sorted(srcs)))
        rows.append(ev)
    R['pairs_judged'] = len(rows)
    R['tiers_pairs'] = Counter(r['tier'] for r in rows)
    R['why_C'] = Counter(r['why'] for r in rows if r['tier'] == 'C')
    R['why_B'] = Counter(x for r in rows if r['tier'].startswith('B') for x in r['why'].split(';'))

    # ---- A clusters
    par = {}

    def fd(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for r in rows:
        if r['tier'] == 'A':
            par[fd(r['a'])] = fd(r['b'])
    clusters = defaultdict(set)
    for k in par:
        clusters[fd(k)].add(k)
    ops, merges = [], []
    fam_count = lambda k: len({a.split(':')[0] for a in people[k]['anchors'] if a.split(':')[0] in PUBLIC})  # noqa: E731
    for cl in clusters.values():
        fs = {k: facts(k) for k in cl}
        bad = None
        for s in CLASH + ('orcid',):
            vals = {v for k in cl for v in fs[k]['ids'].get(s, ())}
            if len(vals) > 1:
                bad = f'cluster-{s}-differs'
        births = {fs[k]['life'][0] for k in cl if fs[k]['life'][0]}
        if births and max(births) - min(births) > 1:
            bad = 'cluster-birth-differs'
        if not bad:
            for x, y in combinations(sorted(cl), 2):
                if not names_agree(people[x]['label'], people[y]['label']):
                    bad = 'cluster-names-disagree'
                    break
        if bad:
            for r in rows:
                if r['tier'] == 'A' and r['a'] in cl:
                    r.update(tier='B2', why=bad)
            R['clusters_back_to_B'] += 1
            continue
        into = sorted(cl, key=lambda k: (-fam_count(k), -len(F.works.get(k, ())), int(k[2:])))[0]
        for k in sorted(cl):
            if k == into:
                continue
            ev = next((r for r in rows if r['tier'] == 'A' and {r['a'], r['b']} & {k} and ({r['a'], r['b']} & cl)), None)
            basis = (f"duplicate person keys (person-dup-merges-2026-11-11, tier A): {people[k]['label']} and "
                     f"{people[into]['label']}: names agree in full, no identifier or date clash, no other established key "
                     f"or LC authority with the name; facts: {'; '.join(ev['facts']) if ev else ''}")[:900]
            ops.append(dict(event='merge', key=k, into=into, decided_by='rule', basis=basis))
            merges.append(dict(key=k, into=into, label=people[k]['label'], into_label=people[into]['label'],
                               facts=ev['facts'] if ev else []))
    R['tierA_merges'] = len(ops)
    R['tierA_clusters'] = len(clusters) - R['clusters_back_to_B']
    R['tiers_pairs_final'] = Counter(r['tier'] for r in rows)

    # ---- gold test
    random.seed(20261111)
    gold = Counter()
    neg_rows = []
    seen = set()
    for k, os_ in notsame.items():
        for o in os_:
            p = frozenset((k, o))
            if p in seen or k not in live or o not in live or k not in people or o not in people:
                continue
            seen.add(p)
            t, w, _ = judge(k, o, facts(k), facts(o), frozenset(p), lcids_of(p), use_marks=False)
            gold[f'neg_notsame_{t}'] += 1
            neg_rows.append(('notsame', k, o, t, w))
    for p, v in verdicts.items():
        if not v.startswith('different'):
            continue
        k, o = sorted(p)
        if k not in live or o not in live or k not in people or o not in people:
            continue
        t, w, _ = judge(k, o, facts(k), facts(o), frozenset(p), lcids_of(p), use_marks=False)
        gold[f'neg_review_different_{t}'] += 1
        neg_rows.append(('review-different', k, o, t, w))
    # masked namesakes: established keys of one full name with two different LC authorities
    nm = []
    for fam, lst in by_family.items():
        est = [(k, g) for k, g, res in lst if res == 'established' and any(a.startswith('lcnaf:') for a in people[k]['anchors'])]
        for (x, gx), (y, gy) in combinations(est, 2):
            if strict_agree(gx, gy):
                lx = {a for a in people[x]['anchors'] if a.startswith('lcnaf:')}
                ly = {a for a in people[y]['anchors'] if a.startswith('lcnaf:')}
                if lx and ly and not (lx & ly):
                    nm.append((x, y))
    random.shuffle(nm)
    nm = nm[:6000]
    db.execute('CREATE OR REPLACE TEMP TABLE want2(key VARCHAR)')
    F2 = Facts(db, people, {k for p in nm for k in p} | set())
    for x, y in nm:
        p = frozenset((x, y))
        fx, fy = F2.of(x, people[x]['anchors'], mask=True), F2.of(y, people[y]['anchors'], mask=True)
        excl = {a[len('lcnaf:'):] for k in p for a in people[k]['anchors'] if a.startswith('lcnaf:')}
        t, w, ev = judge(x, y, fx, fy, p, excl, use_marks=False)
        gold[f'neg_masked_namesake_{t}'] += 1
        neg_rows.append(('masked-namesake', x, y, t, w + ' ' + ';'.join(ev.get('facts', []))))
    # positives: artificial splits
    rich = [k for k, p in people.items() if k in live and len({a.split(':')[0] for a in p['anchors'] if a.split(':')[0] in PUBLIC}) >= 2]
    random.shuffle(rich)
    F3 = Facts(db, people, set(rich[:20000]))
    npos = 0
    for k in rich[:20000]:
        if len(F3.works.get(k, ())) < 6:
            continue
        f = F3.of(k, people[k]['anchors'])
        ws = sorted(f['works'])
        wa, wb = set(ws[0::2]), set(ws[1::2])
        ids_a = {s: v for s, v in f['ids'].items() if s in ('lcnaf', 'wd', 'viaf', 'gnd', 'isni', 'idref')}
        ids_b = {s: v for s, v in f['ids'].items() if s not in ids_a}
        if not ids_a or not ids_b:
            continue
        ta = {t: y for t, y in f['titles'].items()}
        items = sorted(ta)
        fa = dict(f, ids=ids_a, works=wa, titles={t: ta[t] for t in items[0::2]}, affs=f['affs'][0::2],
                  years=[x for i, x in enumerate(f['years']) if i % 2 == 0])
        fb = dict(f, ids=ids_b, works=wb, titles={t: ta[t] for t in items[1::2]}, affs=f['affs'][1::2],
                  years=[x for i, x in enumerate(f['years']) if i % 2 == 1], life=(None, None) if not ids_b.get('orcid') else f['life'])
        grp = frozenset((k,))
        t, w, ev = judge(k, k, fa, fb, grp, {v for v in f['ids'].get('lcnaf', ())}, use_marks=False)
        gold[f'pos_split_{t}'] += 1
        gold[f'pos_split_why_{w.split(";")[0] if t != "A" else "A"}'] += 1
        npos += 1
        if npos >= 3000:
            break
    negs = sum(v for k, v in gold.items() if k.startswith('neg_'))
    negA = sum(v for k, v in gold.items() if k.startswith('neg_') and k.endswith('_A'))
    gold['negatives'] = negs
    gold['negatives_tier_A'] = negA
    gold['precision_on_negatives'] = round(1 - negA / negs, 5) if negs else None
    gold['positives'] = npos
    gold['recall_on_splits'] = round(gold['pos_split_A'] / npos, 4) if npos else None
    negAB1 = negA + sum(v for k, v in gold.items() if k.startswith('neg_') and k.endswith('_B1'))
    gold['negatives_tier_A_or_B1'] = negAB1
    gold['precision_on_negatives_if_B1_also_merged'] = round(1 - negAB1 / negs, 5) if negs else None
    gold['recall_on_splits_A_or_B1'] = round((gold['pos_split_A'] + gold['pos_split_B1']) / npos, 4) if npos else None
    R['gold'] = dict(gold)

    # ---- outputs
    args.out.mkdir(parents=True, exist_ok=True)
    proposal = dict(basis='duplicate person keys, tier A (person-dup-merges-2026-11-11): full-name agreement, no clash, '
                          'dates compatible, a positive fact (shared work, shared title, same institution in an '
                          'overlapping period), no other established key or LC authority with the name', decided_by='rule',
                    ops=ops)
    if not args.no_validate:
        events, names = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(events)
    (args.out / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False) + '\n')
    cols = ['tier', 'why', 'a', 'label_a', 'b', 'label_b', 'facts', 'other_established', 'other_lc', 'sources']
    for name, sel in (('tier-a-pairs.csv', lambda r: r['tier'] == 'A'), ('tier-b-review.csv', lambda r: r['tier'].startswith('B')),
                      ('tier-c-rejected.csv.gz', lambda r: r['tier'] == 'C')):
        op = gzip.open if name.endswith('.gz') else open
        with op(args.out / name, 'wt', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for r in sorted((r for r in rows if sel(r)), key=lambda r: (r['tier'], r['why'], r['label_a'])):
                w.writerow([r.get('tier'), r.get('why'), r['a'], r['label_a'], r['b'], r['label_b'],
                            ' ; '.join(r.get('facts', [])), ' '.join(r.get('other_established', [])),
                            ' '.join(r.get('other_lc', [])), r.get('sources')])
    with open(args.out / 'gold-negatives.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['set', 'a', 'b', 'tier', 'why'])
        w.writerows(neg_rows)
    sample = random.sample(merges, min(100, len(merges)))
    wl = {}
    sk = {k for m in sample for k in (m['key'], m['into'])}
    db.execute('CREATE OR REPLACE TEMP TABLE sk(k VARCHAR)')
    db.executemany('INSERT INTO sk VALUES (?)', [(k,) for k in sk])
    for k, lab, y, kind in db.execute(f"""SELECT a."from", w.label, w.year, w.kind FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE a.evidence = 'keylog' AND a."from" IN (SELECT k FROM sk)
            ORDER BY w.year""").fetchall():
        wl.setdefault(k, []).append(f'{y} {kind}: {(lab or "")[:90]}')
    for m in sample:
        for side in ('key', 'into'):
            k = m[side]
            f = facts(k)
            m[side + '_detail'] = dict(
                ids={s_: sorted(v) for s_, v in f['ids'].items() if s_ in PUBLIC or s_ in ('aha-phd', 'review-credit', 'diss-author')},
                life=f['life'], phd=sorted(f['phd']), works=len(wl.get(k, [])), work_sample=wl.get(k, [])[:6],
                affs=sorted({f'{l} {lo}-{hi} ({src})' for _, l, lo, hi, src in f['affs']})[:6])
    (args.out / 'sample-100-tier-a.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    probes = {}
    for k in PROBES:
        probes[k] = [dict(other=r['b'] if r['a'] == k else r['a'], tier=r['tier'], why=r['why'], facts=r.get('facts'))
                     for r in rows if k in (r['a'], r['b'])]
    for a, b in (('p-4256', 'p-21351'), ('p-4256', 'p-133302'), ('p-21351', 'p-133302')):
        grp = frozenset((a, b))
        t, w, ev = judge(a, b, facts(a), facts(b), group_of.get(a, grp) | grp, lcids_of(group_of.get(a, grp) | grp))
        probes[f'{a}~{b}'] = dict(tier=t, why=w, facts=ev.get('facts'), other_lc=ev.get('other_lc'),
                                  in_candidates=frozenset((a, b)) in pairs)
    R['probes'] = probes
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sorted(R.items())}
    rep['rule'] = __doc__.split('\n\n')[1:5]
    (args.out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('rule', 'probes')}, indent=1, default=list))


if __name__ == '__main__':
    main()
