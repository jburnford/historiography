"""Place layer: place names in work titles, measured against LC subject headings (2026-11-26).

The other title sources cover a few dozen names (title-rule, title-checked) or one tag per title read (title-read-sol).
This one takes every name of every grounded place in places.csv.gz (label, LC heading, Wikidata/LC variants, the
LC-qualified form "Victoria, B.C."), finds them in work titles (titles only: whole words, case-sensitive,
leftmost-longest, so "New South Wales" is not "Wales" and "Victoria, B.C." is not bare "Victoria"), and keeps a name
only after measuring it:

- Ground truth: works that already carry an LC place heading (lc-651 / lc-z / lc-610, any LC confidence). For a name,
  the support is the number of LC-tagged works whose title holds it (after the context rules); the precision is the
  share of them whose LC places include the name's place, a place inside it, or its period polity / territory
  (strict). The loose share also counts a place containing it; it is reported, never used (books on the Huron
  people are catalogued under Ontario, which contains Huron County).
- A name with several grounded holders is measured against each and the best is kept as its candidate; it is marked
  shared.
- Accepted (tier `measured`): precision >= MIN_PRECISION with support >= MIN_SUPPORT and none of the flags below.
- Low-support tier (`low-support`, separate label): support LOW_SUPPORT..MIN_SUPPORT-1 with every supported work
  right, no flags, and a multi-word or LC-qualified name (single words are held). Its own sampled precision is
  reported.
- Held, with the reason: below the bar; too little evidence; a flag (shared by two or more grounded places,
  personal-name-like, common word, a people's name); or governed already (a name with its own hand-read title rule or
  Sol title reads, whose negative verdicts this rule cannot see).

Context rules (a match is dropped): text after " / " (statement of responsibility); a place of publication or press
("London: Routledge, 1999", "(Toronto, 1982)", "University of Toronto Press"); an institution or title word after the
name (Press, University, Society, Journal, Star, Treaty, Conference ...); a title of office or treaty before it (Duke
of, Earl of, Bishop of, Treaty of, Queen ...); a given name or an initial before it ("Isaiah Berlin", "J. London").

Tags go only to works with no LC place heading (the cataloguer has decided those) and never repeat a place the work
already has (or a place inside it). Reviews do not inherit these tags (graph_places.py): a review's title is matched
on its own.

    python3 scripts/places_title_names.py measure     # per-name evidence -> data/graph/places/title-names/
    python3 scripts/places_title_names.py tag         # tags -> data/graph/places/title-name-tags.csv.gz
    python3 scripts/places_title_names.py sample      # stratified audit draw -> build/places/title-names/audit-draw.csv
Reads build/graph/work.parquet and about_place.parquet (the current build) and the tracked place tables.
"""
import argparse
import csv
import gzip
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
P = ROOT / 'data/graph/places'
OUTD = P / 'title-names'
WORK = ROOT / 'build/places/title-names'
TAGS = P / 'title-name-tags.csv.gz'
SOURCE = 'title-name'

MIN_PRECISION = 0.90       # loose: the place, a place inside it, its period polity/territory, or a place containing it
MIN_STRICT = 0.60          # strict (no containers): the guard against a sense catalogued only at a wider level
MIN_SUPPORT = 10
LOW_SUPPORT = 2

CONTAIN = {'lc-qualifier', 'wd-p131', 'wd-country', 'region-contains (wd-p131)'}

# names already governed by a hand-read rule (scripts/places_titles.py RULES/CANDIDATES) or read title by title by the
# outside reviewer (title-readings/sol-2026-11-19): their negative readings are not visible here, so no second rule
# names the outside reviewer read title by title (title-readings/sol-2026-11-19; README): its negative verdicts
# (another place, incidental, a person) live in data/identifiers/, which this rule does not read, so no second rule
SOL_READ = {
    'London', 'Sydney', 'Victoria', 'Great Lakes', 'Montreal', 'Montréal', 'Toronto', 'Vancouver',
    'British North America', 'Halifax', 'Hamilton', 'Kingston', 'Saint John', "St. John's", 'St John s', 'Yukon',
    'Ottawa', 'Windsor', 'Calgary', 'Quebec City', 'Edmonton', 'Colombo', 'Regina', 'Prince Albert', 'Galle',
    'Trincomalee', 'Batticaloa', 'Polonnaruwa',
}
GOVERNED = SOL_READ
# names with a hand-read title rule (places_titles.py: Upper Canada, Manitoba ...) are measured like any other name:
# the rule covers non-book works only, so this source fills books without LC headings and titles the rule's
# citation-tail cut; a work the 40-title readings found wrong is never tagged to that place (read_wrong())

STOP_GIVEN = {'New', 'North', 'South', 'East', 'West', 'Upper', 'Lower', 'Great', 'Greater', 'Little', 'Old', 'Saint',
              'San', 'Santa', 'St', 'Ste', 'Fort', 'Port', 'Mount', 'Lake', 'Cape', 'Isle', 'Grand', 'Central',
              'Northern', 'Southern', 'Eastern', 'Western', 'The', 'La', 'Le', 'Los', 'Las', 'El', 'Al', 'De', 'Van',
              'Von', 'Del', 'Della', 'Di', 'Da', 'Du', 'Des', 'Ben', 'Abu', 'Bin', 'Mac', 'Mc', 'Sir', 'Dr', 'Mr', 'Mrs',
              'Rev', 'Colonial', 'British', 'French', 'Spanish', 'Early', 'Modern', 'Medieval', 'Imperial', 'Royal',
              'Rural', 'Urban', 'Black', 'White', 'Red', 'Green', 'Blue', 'Golden', 'Holy', 'Inner', 'Outer', 'Middle',
              'Victorian', 'Edwardian', 'Georgian', 'Elizabethan', 'Tudor', 'Stuart', 'Roman', 'Greek', 'Ancient',
              'Post', 'Pre', 'Anglo', 'Indo', 'Afro', 'Latin', 'Native', 'Indigenous', 'Mexican', 'American', 'Canadian',
              'Irish', 'Scottish', 'English', 'German', 'Italian', 'Chinese', 'Japanese', 'Russian', 'Soviet', 'Dutch'}

TOKEN = re.compile(r"[^\W_]+")
GAP_OK = re.compile(r"^[\s\-'’.,()]*$")
PREV_BLOCK = re.compile(
    r"(\b(Universit(y|é|à|ät|ad|eit)|Bank|Treaty|Treaties|Peace|Congress|Council|Edict|Synod|Concordat|Convention|"
    r"Protocol|Declaration|Duke|Duchess|Earl|Countess|Marquis|Marquess|Marchioness|Baron|Baroness|Viscount|Lord|Lady|"
    r"Bishop|Archbishop|Dean|Prince|Princess|Count|Archduke|Margrave|Elector|Bishopric|Diocese|Archdiocese|"
    r"Statute|Agreement|Accord|Pact|Conference|Ordinance)\s+(of|de|di|du|von|zu)\s+(the\s+)?|"
    r"\b(Queen|King|Saint|St\.?|Ste\.?|Lake|Mount|Mt\.?|Fort|Port|Cape|Kaiser|Emperor|Empress|Pope|Princess|Prince|"
    r"Lady|Lord|Sir|Dame|Mrs?\.?|Miss|Dr\.?|Rev\.?|Father|Brother|Sister|General|Gen\.?|Colonel|Col\.?|Captain|Capt\.?|"
    r"Admiral|Governor|President|Senator|Bishop|Archbishop|Cardinal)\s+|"
    r"(^|[\s(])[A-Z]\.\s*)$")
NEXT_BLOCK = re.compile(
    r"^['’]?s?\s*(Press|University|Universit|College|School|Institute|Institution|Society|Museum|Library|Archives?|"
    r"Journal|Review|Gazette|Times|Herald|Star|Post|Globe|Mail|Chronicle|Courier|Telegraph|Tribune|Mercury|Advertiser|"
    r"Observer|Guardian|Daily|Evening|Morning|Weekly|Quarterly|Magazine|Conference|Convention|Agreements?|Treaty|"
    r"Protocol|Declaration|Accords?|Consensus|Club|Company|Co\b|Corporation|Ltd|Inc|Hospital|Infirmary|Board|"
    r"Symphony|Orchestra|Zoo|Group|Circle|Workshop|Seminar|Meetings?|Lectures?|Series|Studies|Papers|Records|"
    r"Proceedings|Transactions|Bulletin|Yearbook|Annual|Report|Commission|Committee|Conventions?|Rules|Principles|"
    r"Plan|System|Process|School|Codex|Manuscript|Ms\b|MS\b|Psalter|Gospels|Bible|Missal|Hours|Papyrus|Tablet|Stele)\b")
CITE_AFTER = re.compile(
    r"^[\s.)]*(\([^)]{0,30}\))?[\s.)]*(,\s*[A-Z][\w.]+(\s[A-Z][\w.]+)?[\s.]*)?((and|&)\s*[A-Z][\w.]+([,\s]+[A-Z][\w.]+){0,3}[\s.]*)?:\s*"
    r"([^:;]{0,50}?\b(Press|Publish\w*|Verlag|Books|[ÉE]ditions|Editorial|Ltd|Inc|& Co|and Co)\b"
    r"|[A-Z][^:;,]{1,40},\s*(1[5-9]|20)\d\d\b(?!\s*[-–])"
    r"|[A-Z][\w&'’ -]{1,40}[.,]?\s*$)"
    r"|^\s*,\s*[A-Z][\w'’.&-]+( [A-Z&][\w'’.&-]+){0,3},\s*(1[5-9]|20)\d\d\b(?!\s*[-–])"
    r"|^\s*,?\s*(1[5-9]|20)\d\d\s*\)"
    r"|^\s*,?\s*(1[5-9]|20)\d\d\s*[.)]?\s*$")
# a meeting, lecture or exhibition: the place in the title is the venue (places_titles.py PATTERN_DROP, widened)
VENUE = re.compile(r"(?i)\b(annual meeting|meetings? (held )?(in|at)|conference|congress|symposium|colloque|colloquium|"
                   r"proceedings|delivered (at|in|before)|lectures? (delivered|given)|discourses?,? delivered)\b|\bGallery\b")
# a person 'of' a place: 'Chrétien de Troyes', 'Otto von Braunschweig'
OF_PLACE = re.compile(r"\b([A-Z][\w'’-]+)\s+(de|von|van|zu|da|di|d['’]|of)\s*$")
CITE_BEFORE = re.compile(r"\b(Press|Publishers?|Verlag|Books)\s*,\s*$")
TITLE_CUT = re.compile(r"\s/\s")


def tokens(s):
    return [(m.group(), m.start(), m.end()) for m in TOKEN.finditer(s)]


def name_key(s):
    return tuple(t for t, _, _ in tokens(s))


def valid_name(s):
    s = s.strip()
    if len(s) < 3 or re.search(r"[\d:/=\[\]]", s) or not s[0].isupper():
        return False
    toks = name_key(s)
    if not toks or sum(len(t) for t in toks) < 3:
        return False
    if all(t.isupper() and len(t) <= 4 for t in toks):     # CAN, ONT, CA-ON, UN/LOCODE codes
        return False
    if len(toks) == 1 and len(toks[0]) < 3:
        return False
    return True


# ---- names ------------------------------------------------------------------------------------------------------
def read_places():
    with gzip.open(P / 'places.csv.gz', 'rt', encoding='utf-8') as fh:
        places = {r['qid']: r for r in csv.DictReader(fh)}
    parents, children, period = defaultdict(set), defaultdict(set), defaultdict(set)
    with gzip.open(P / 'place-hierarchy.csv.gz', 'rt', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            b = r['basis']
            if b in CONTAIN:
                parents[r['child']].add(r['parent'])
                children[r['parent']].add(r['child'])
            elif b.startswith('period-of'):
                period[r['parent']].add(r['child'])     # territory -> its period polities
                period[r['child']].add(r['parent'])     # and back
    return places, parents, children, period


def split_qualifier(s):
    m = re.match(r"^(.*?)\s*\(([^()]+)\)$", s.strip())
    return (m.group(1), m.group(2)) if m else (s.strip(), None)


def build_index(places):
    """token tuple -> {qid: role}; role 'primary' (label or LC heading base), 'qualified' (base + LC qualifier),
    'alias' (any other variant). Variants a place inherits from its period polities stay aliases."""
    idx = defaultdict(dict)
    rank = {'qualified': 3, 'primary': 2, 'alias': 1}

    def add(s, q, role):
        if not valid_name(s):
            return
        k = name_key(s)
        if rank[role] > rank.get(idx[k].get(q), 0):
            idx[k][q] = role
    for q, r in places.items():
        base, qual = split_qualifier(r['lc_heading'] or '')
        add(r['label'], q, 'primary')
        if base:
            add(base, q, 'primary')
            if qual:
                add(f'{base}, {qual}', q, 'qualified')
        for v in (r['variants'] or '').split('|'):
            if not v or ')' in v and not v.endswith(')') or '. ' in v and '(' in v:
                continue                    # 'London (England). West Ham' and similar catalogue forms
            b, ql = split_qualifier(v)
            add(b, q, 'alias')
            if ql:
                add(f'{b}, {ql}', q, 'qualified')
    return dict(idx)


def resolve(holders):
    """Holders a name may tag: the qualified holders if any, else the primary holders if any, else all."""
    for role in ('qualified', 'primary'):
        hs = sorted(q for q, r in holders.items() if r == role)
        if hs:
            return hs
    return sorted(holders)


def firsts(idx):
    f = {}
    for k in idx:
        f[k[0]] = max(f.get(k[0], 0), len(k))
    return f


# ---- matching ---------------------------------------------------------------------------------------------------
def title_case(text):
    """Most longer words capitalised ('West Ham and the River Lea: A Social History'): a capital there is no sign of
    a proper noun."""
    ws = [w for w in TOKEN.findall(text) if len(w) >= 4 and w.isalpha()]
    return len(ws) >= 3 and sum(w[0].isupper() for w in ws) >= 0.6 * len(ws)


INITIAL = re.compile(r"(^|[:.?!;—–]\s*|\s[-–]\s*|[\"“‘'(\[]\s*)$")


class Matcher:
    def __init__(self, idx, given=(), common=()):
        self.idx = idx
        self.first = firsts(idx)
        self.given = set(given)
        self.common = set(common)      # single-word names that are also common words: sentence-case titles only

    def find(self, title):
        """Leftmost-longest whole-word, case-sensitive matches -> [(name tuple, start, end, kept, why)]."""
        cut = TITLE_CUT.search(title)
        text = title[:cut.start()] if cut and cut.start() > 10 else title
        toks = tokens(text)
        out, i = [], 0
        while i < len(toks):
            ml = self.first.get(toks[i][0])
            hit = None
            if ml:
                for n in range(min(ml, len(toks) - i), 0, -1):
                    span = toks[i:i + n]
                    if any(not GAP_OK.match(text[a[2]:b[1]]) for a, b in zip(span, span[1:])):
                        continue
                    k = tuple(t for t, _, _ in span)
                    if k in self.idx:
                        hit = (k, span[0][1], span[-1][2], n)
                        break
            if hit:
                k, s, e, n = hit
                why = self.blocked(text, s, e, toks, i)
                if why is None and k in self.common and (title_case(text) or INITIAL.search(text[:s])):
                    why = 'common-word-context'
                out.append((k, s, e, why is None, why))
                i += n
            else:
                i += 1
        return out

    def blocked(self, text, s, e, toks, i):
        before, after = text[:s], text[e:]
        if CITE_AFTER.match(after) or CITE_BEFORE.search(before):
            return 'citation'
        if VENUE.search(text):
            return 'venue'
        m = OF_PLACE.search(before)
        if m and m.group(1) in self.given:
            return 'person-of-place'
        k = tuple(t for t, _, _ in toks[i:i + len(TOKEN.findall(text[s:e]))])
        for j in range(i - 1, max(-1, i - 4), -1):   # 'History Council of new South Wales'
            if toks[j][0].islower():
                if (toks[j][0].capitalize(),) + tuple(t for t, _, _ in toks[j + 1:i]) + k in self.idx:
                    return 'lower-case-longer-name'
                break
        if NEXT_BLOCK.match(after):
            return 'institution-after'
        if PREV_BLOCK.search(before):
            return 'title-before'
        if i > 0 and toks[i - 1][0] in self.given and text[toks[i - 1][2]:s] == ' ':
            return 'given-name-before'
        j = i + len(TOKEN.findall(text[s:e]))
        if (toks[i][0] in self.given and j < len(toks) and toks[j][0][:1].isupper() and text[e:toks[j][1]] == ' '
                and j == i + 1):
            return 'given-name-use'           # 'Florence Nightingale', 'Chad Smith'
        return None


def kept_names(matcher, title):
    return [k for k, s, e, ok, why in matcher.find(title) if ok]


# ---- data -------------------------------------------------------------------------------------------------------
def con():
    import duckdb
    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'; SET threads=4")
    return c


def load(c):
    works = c.execute(f"SELECT key, label, kind FROM '{G}/work.parquet' WHERE label IS NOT NULL").fetchall()
    tags = defaultdict(set)
    lc = defaultdict(set)
    for w, q, src in c.execute(f"""SELECT "from", substr("to", 7), source FROM '{G}/about_place.parquet'""").fetchall():
        tags[w].add(q)
        if src.startswith('lc-'):
            lc[w].add(q)
    return works, tags, lc


def given_names(c, title_lower):
    """Given names: first words of person labels used by 25+ people, not a geographic/adjective word and not a common
    lower-case word in titles."""
    cnt = Counter()
    for (lab,) in c.execute("SELECT label FROM nodes WHERE type = 'person' AND label IS NOT NULL").fetchall():
        t = TOKEN.match(lab)
        if t and len(t.group()) >= 3 and t.group()[0].isupper():
            cnt[t.group()] += 1
    return {n for n, k in cnt.items() if k >= 25 and n not in STOP_GIVEN and title_lower.get(n.lower(), 0) < 200}


def person_tokens(c):
    cnt = Counter()
    for (lab,) in c.execute("SELECT label FROM nodes WHERE type = 'person' AND label IS NOT NULL").fetchall():
        for t in set(TOKEN.findall(lab)):
            cnt[t] += 1
    return cnt


def explorer():
    import duckdb
    c = duckdb.connect(str(G / 'explorer.duckdb'), read_only=True)
    c.execute("SET memory_limit='4GB'; SET threads=4")
    return c


def common_words(idx, low, cap):
    """Single-word names whose lower-case form is a word in titles (10+ times and 5%+ of the capitalised count
    outside the first position): Reading, Bath, Nice, Mobile. They match only in sentence-case titles, not first."""
    out = set()
    for k in idx:
        if len(k) == 1:
            lo = low.get(k[0].lower(), 0)
            if lo >= 10 and lo >= 0.05 * max(1, cap.get(k[0], 0)):
                out.add(k)
    return out


def word_counts(works):
    low, cap = Counter(), Counter()
    for _, t, _ in works:
        for i, w in enumerate(TOKEN.findall(t)):
            if w.islower():
                low[w] += 1
            elif i > 0 and w[0].isupper():
                cap[w] += 1
    return low, cap


# ---- measure ----------------------------------------------------------------------------------------------------
def related(q, parents, children, period, loose=False):
    """The place, its period polities or territory (one hop), and every place inside those; loose adds containers."""
    out = {q} | set(period.get(q, ()))
    todo = list(out)
    while todo:
        x = todo.pop()
        for y in children.get(x, ()):
            if y not in out:
                out.add(y)
                todo.append(y)
    if loose:
        todo = [q] + list(period.get(q, ()))
        while todo:
            x = todo.pop()
            for y in parents.get(x, ()):
                if y not in out:
                    out.add(y)
                    todo.append(y)
    return out


def flags_for(name, other_sense, support, places, low, cap, ptok, peoples):
    f = []
    if other_sense >= max(2, 0.03 * support):
        f.append('shared')
    toks = name.split()
    if len(toks) == 1:
        w = toks[0]
        if ptok.get(w, 0) >= 20 and ptok.get(w, 0) >= 0.05 * max(1, cap.get(w, 0)):
            f.append('personal-name')
    if name in peoples:
        f.append('people-name')
    return f


def peoples_names():
    """Headings read as peoples, nations or bands (ungrounded.csv.gz reasons): never a place name here."""
    out = set()
    with gzip.open(P / 'ungrounded.csv.gz', 'rt', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['reason'].startswith('a people'):
                out.add(split_qualifier(r['heading'])[0])
    return out


def measure():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTD.mkdir(parents=True, exist_ok=True)
    places, parents, children, period = read_places()
    idx = build_index(places)
    c = con()
    works, tags, lc = load(c)
    low, cap = word_counts(works)
    ex = explorer()
    given = given_names(ex, low)
    ptok = person_tokens(ex)
    ex.close()
    common = common_words(idx, low, cap)
    m = Matcher(idx, given, common)
    peoples = peoples_names()
    print(len(works), 'titles;', len(idx), 'names;', len(given), 'given names;', len(lc), 'works with LC places')
    support = Counter()
    hit_s = defaultdict(Counter)
    hit_l = defaultdict(Counter)
    total = Counter()           # every kept match, all works
    untagged = Counter()        # kept matches on works with no LC place
    blocked = Counter()
    rel_s, rel_l = {}, {}
    lcsets = defaultdict(list)
    for w, title, kind in works:
        for k, s, e, ok, why in m.find(title):
            if not ok:
                blocked[(k, why)] += 1
                continue
            total[k] += 1
            L = lc.get(w)
            if not L:
                untagged[k] += 1
                continue
            support[k] += 1
            hs = resolve(idx[k])
            if len(hs) > 1:
                lcsets[k].append(L)
            for q in hs:
                if q not in rel_s:
                    rel_s[q] = related(q, parents, children, period)
                    rel_l[q] = related(q, parents, children, period, loose=True)
                if L & rel_s[q]:
                    hit_s[k][q] += 1
                if L & rel_l[q]:
                    hit_l[k][q] += 1
    rows = []
    for k in set(total) | {k for k, _ in blocked}:
        name = ' '.join(k)
        hs = resolve(idx[k])
        sup = support[k]
        best = max(hs, key=lambda q: (hit_s[k][q], hit_l[k][q], -int(q[1:]))) if hs else ''
        for q in hs:
            if q not in rel_s:
                rel_s[q] = related(q, parents, children, period)
                rel_l[q] = related(q, parents, children, period, loose=True)
        prec = hit_s[k][best] / sup if sup else None
        precl = hit_l[k][best] / sup if sup else None
        second = sorted((hit_s[k][q] for q in hs), reverse=True)[1] if len(hs) > 1 else 0
        role = idx[k][best]
        # LC works another holder (not related to the best one) explains and the best one does not
        others = [q for q in hs if q != best and q in rel_s and q not in rel_l[best] and best not in rel_l[q]]
        other_sense = sum(1 for L in lcsets.get(k, ()) if not (L & rel_l[best]) and any(L & rel_s[q] for q in others))
        fl = flags_for(name, other_sense, sup, places, low, cap, ptok, peoples)
        rows.append(dict(name=name, qid=best, place_label=places[best]['label'], kind=places[best]['kind'],
                         role=role, holders=len(hs), holder_qids='|'.join(hs[:8]), support=sup,
                         right=hit_s[k][best], precision=round(prec, 4) if prec is not None else '',
                         precision_loose=round(precl, 4) if precl is not None else '', second_holder_right=second, other_sense=other_sense,
                         matches=total[k], matches_untagged=untagged[k],
                         blocked=sum(v for (kk, _), v in blocked.items() if kk == k), flags='|'.join(fl),
                         lower_count=low.get(name.lower(), 0) if len(k) == 1 else '',
                         person_tokens=ptok.get(name, 0) if len(k) == 1 else '',
                         context='sentence-case title, not first word' if k in common else ''))
    for r in rows:
        r['tier'], r['reason'] = decide(r)
    rows.sort(key=lambda r: (-r['matches_untagged'], r['name']))
    fields = list(rows[0])
    with open(WORK / 'measure.csv', 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, fields)
        wr.writeheader()
        wr.writerows(rows)
    json.dump(sorted(given), open(WORK / 'given-names.json', 'w'))
    json.dump(sorted(' '.join(k) for k in common), open(WORK / 'common-words.json', 'w'), ensure_ascii=False)
    write_lists(rows)
    curve(rows)


def decide(r):
    """Tier for a measured name: 'measured' or 'low-support' (accepted), else 'held' with the reason."""
    name, sup, fl = r['name'], r['support'], [f for f in r['flags'].split('|') if f]
    prec, strict = r['precision_loose'], r['precision']
    if name in GOVERNED or name.replace('’', "'") in GOVERNED:
        return 'held', 'governed: read title by title by the outside reviewer (Sol 2026-11-19); its negative reads are not visible here'
    if r['matches_untagged'] == 0:
        return 'held', 'no untagged titles to tag'
    if sup >= MIN_SUPPORT:
        if prec < MIN_PRECISION:
            return 'held', f'precision {prec:.2f} < {MIN_PRECISION} on {sup} LC-tagged works'
        if strict < MIN_STRICT:
            return 'held', (f'precision {prec:.2f} only through wider places: {strict:.2f} name the place itself '
                            f'(< {MIN_STRICT}; another sense catalogued at a wider level)')
        if fl:
            return 'held', f'passes ({prec:.2f} on {sup}) but flagged: {", ".join(fl)}'
        return 'measured', f'precision {prec:.2f} ({strict:.2f} the place itself) on {sup} LC-tagged works'
    single = len(name.split()) == 1 and r['role'] != 'qualified'
    if (LOW_SUPPORT <= sup and strict == 1.0 and not fl
            and (not single or (r['lower_count'] == 0 and r['person_tokens'] <= 2))):
        return 'low-support', f'{r["right"]}/{sup} LC-tagged works name the place (below the {MIN_SUPPORT}-work floor)'
    why = f'too little LC evidence ({sup} LC-tagged works'
    why += f', {r["right"]} right)' if sup else ')'
    if fl:
        why += '; flagged: ' + ', '.join(fl)
    return 'held', why


def write_lists(rows):
    acc = [r for r in rows if r['tier'] in ('measured', 'low-support')]
    held = [r for r in rows if r['tier'] == 'held' and r['matches_untagged'] > 0]
    cols_a = ['name', 'qid', 'place_label', 'kind', 'role', 'tier', 'context', 'support', 'right', 'precision',
              'precision_loose', 'holders', 'other_sense', 'matches_untagged']
    cols_h = ['name', 'qid', 'place_label', 'role', 'reason', 'flags', 'support', 'right', 'precision', 'holders',
              'holder_qids', 'matches_untagged']
    with open(OUTD / 'accepted-names.csv', 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, cols_a, extrasaction='ignore')
        wr.writeheader()
        wr.writerows(sorted(acc, key=lambda r: (r['tier'], -r['matches_untagged'], r['name'])))
    with gzip.open(OUTD / 'held-names.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, cols_h, extrasaction='ignore')
        wr.writeheader()
        wr.writerows(held)
    print('accepted', Counter(r['tier'] for r in acc), 'held (with untagged matches)', len(held))


def curve(rows):
    """Accepted names and untagged matches by threshold (flags and governed names left out)."""
    base = [r for r in rows if r['support'] and not r['flags'] and r['name'] not in GOVERNED and r['matches_untagged']
            and r['precision'] >= MIN_STRICT]
    out = []
    for ms in (5, 10, 20, 50):
        for mp in (0.8, 0.85, 0.9, 0.95, 0.98):
            sel = [r for r in base if r['support'] >= ms and r['precision_loose'] >= mp]
            w = sum(r['support'] for r in sel)
            exp = sum(r['precision_loose'] * r['support'] for r in sel) / w if w else 0
            out.append(dict(min_support=ms, min_precision=mp, names=len(sel),
                            untagged_matches=sum(r['matches_untagged'] for r in sel),
                            lc_weighted_precision=round(exp, 4)))
    with open(OUTD / 'threshold-curve.csv', 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, list(out[0]))
        wr.writeheader()
        wr.writerows(out)
    for r in out:
        print(r)


# ---- tag --------------------------------------------------------------------------------------------------------
def accepted():
    with open(OUTD / 'accepted-names.csv', encoding='utf-8') as fh:
        return {name_key(r['name']): (r['qid'], r['tier']) for r in csv.DictReader(fh)}


def read_wrong():
    """(work, QID) pairs the 40-title hand readings found wrong (title-readings/*.csv; places_titles.py)."""
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from places_titles import CANDIDATES, RULES
    qids = {n: v[0] for n, v in list(CANDIDATES.items()) + list(RULES.items())}
    out = set()
    for path in (P / 'title-readings').glob('*.csv'):
        q = qids.get(path.stem.rsplit('-', 1)[0].replace('_', ' '))
        for r in csv.DictReader(open(path, encoding='utf-8')):
            if q and r.get('verdict') != 'right':
                out.add((r['key'], q))
    return out


def tag_name(k, idx, acc):
    """The accepted name a match tags by: itself, else (a longer form of one place: 'County Westmeath') the accepted
    shorter name inside it with the same single holder."""
    if k in acc:
        return k
    hs = resolve(idx[k])
    if len(hs) != 1:
        return None
    for n in range(len(k) - 1, 0, -1):
        for i in range(len(k) - n + 1):
            sub = k[i:i + n]
            if sub in acc and acc[sub][0] == hs[0]:
                return sub
    return None


def tag():
    places, parents, children, period = read_places()
    idx = build_index(places)
    acc = accepted()
    wrong = read_wrong()
    given = json.load(open(WORK / 'given-names.json'))
    common = {name_key(n) for n in json.load(open(WORK / 'common-words.json'))}
    m = Matcher(idx, given, common)
    c = con()
    works, tags, lc = load(c)
    rel = {}
    rows, first = [], 0
    for w, title, kind in works:
        if w in lc:
            continue
        have = tags.get(w, set())
        new = {}
        for k in kept_names(m, title):
            a = tag_name(k, idx, acc)
            if a is None:
                continue
            q, tier = acc[a]
            if q not in rel:
                rel[q] = related(q, parents, children, period) - period.get(q, set())
            if have & rel[q] or q in new or (w, q) in wrong:
                continue
            new[q] = (' '.join(k), tier)
        if new and not have:
            first += 1
        for q, (name, tier) in sorted(new.items()):
            rows.append((w, q, places[q]['label'], name, tier, kind or ''))
    with gzip.open(TAGS, 'wt', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work', 'qid', 'place_label', 'matched_name', 'tier', 'work_kind'])
        wr.writerows(sorted(rows))
    rep = dict(rows=len(rows), works=len({r[0] for r in rows}), works_first_tag=first,
               rows_by_tier=dict(Counter(r[4] for r in rows)),
               top_names=Counter(r[3] for r in rows).most_common(30))
    json.dump(rep, open(OUTD / 'tag-report.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


def sample(n=150, seed=20261127):
    """Audit draw: new tags stratified by the name's frequency (quartiles of tags per name), plus the low tier."""
    with gzip.open(TAGS, 'rt', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    freq = Counter(r['matched_name'] for r in rows)
    rnd = random.Random(seed)
    meas = [r for r in rows if r['tier'] == 'measured']
    low = [r for r in rows if r['tier'] == 'low-support']
    names = sorted({r['matched_name'] for r in meas}, key=lambda x: freq[x])
    bands = [names[i * len(names) // 4:(i + 1) * len(names) // 4] for i in range(4)]
    draw = []
    per = (n - 30) // 4
    for b, band in enumerate(bands):
        bs = set(band)
        pool = [r for r in meas if r['matched_name'] in bs]
        # one tag per name first, so rare names are not swamped by the frequent ones in the band
        by = defaultdict(list)
        for r in pool:
            by[r['matched_name']].append(r)
        picks = [rnd.choice(by[x]) for x in rnd.sample(sorted(by), min(per, len(by)))]
        draw += [dict(r, stratum=f'measured-q{b + 1}') for r in picks]
    draw += [dict(r, stratum='low-support') for r in rnd.sample(low, min(30, len(low)))]
    titles = dict(con().execute(f"SELECT key, label FROM '{G}/work.parquet' WHERE key IN (SELECT unnest(?))",
                                [[r['work'] for r in draw]]).fetchall())
    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / 'audit-draw.csv', 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, ['stratum', 'work', 'qid', 'place_label', 'matched_name', 'tier', 'work_kind', 'title'])
        wr.writeheader()
        for r in draw:
            wr.writerow(dict(r, title=titles.get(r['work'], '')))
    print(len(draw), 'rows ->', WORK / 'audit-draw.csv')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=['measure', 'tag', 'sample'])
    a = ap.parse_args()
    {'measure': measure, 'tag': tag, 'sample': sample}[a.cmd]()


if __name__ == '__main__':
    main()
