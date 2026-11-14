"""Thin person keys of one career -> a tiered merge PROPOSAL (2026-11-13; ARCHITECTURE.md §8 class 39). Writes, never applies.

Probe: Daniel Macfarlane was split over six keys (LC/Wikidata key, his Ottawa thesis key, two review-credit keys minted
per printed affiliation, two H-Net review keys). The earlier merge rules fire only on a shared identifier, or on the
same name form plus the same institution; they never read what a reader reads: one name, one topic, one career. The
owner ruled the group one person (data/identifiers/macfarlane-ruling-2026-11-13) and asked for the general rule.

Class: several live person keys with the same normalised full name where the "thin" ones hold one source each:
review credits (`review-credit:` with an affiliation or an H-Net review id), a harvested thesis (`diss-author:`), an AHA
PhD record (`aha-phd:` with or without `aha:`), a repository advisor token, or no anchor / a co-author mention (name
only). A thin key joins its name group (an anchored key, or other thin keys) when ALL of:
1. Names: the family name agrees after folding (case, accents, punctuation, 'Surname, Given' order, Mac/Mc spacing)
   and the given names agree in full (propose_person_dup_merges.names_agree: the first written-out given name identical,
   an extra middle name or initial on one side allowed when compatible, conflicting initials or Jr/Sr block). Never a
   nickname. A thin key printed with initials only never qualifies.
2. The group is closed: every live key of a compatible name is in it, except keys separated by hard evidence (different
   LC/Wikidata/ORCID/ISNI identifiers, life years that rule out the thin key's activity, a `not-same:` mark or an outside
   'different' verdict). Two or more anchored keys that could be the person: not closed (review tier). An anchored key
   printed with initials only that fits counts against closure. Name frequency (bearers: date-possible LC authorities
   not on the group + 1, or OpenAlex History author ids, the larger, as in the works linker) bands the rule.
3. Dates fit one career: a thesis year T bounds all dated activity of the group to T-9..T+50; no review, article or
   thesis before birth + 20 or after death + 3; a span of dated activity over 55 years blocks. Two keys each holding a
   thesis (two thesis works, or AHA PhD years more than two apart), two different LC/Wikidata/ORCID/ISNI/IdRef
   identifiers: never.
4. A positive tie between the thin key and the rest of the group, beyond the name: topic (the works linker's pass-nine
   likelihood ratio of the thin key's titles under the rest of the group's profile: subject `lrs`, subfield `lrf`;
   topic only ever supports), same venue (`vrep`: a journal or H-Net list both publish in), a network tie (REVIEWED,
   COAUTHORED, COEDITED or ADVISED partners in common, key-log evidence), or an institution printed on the thin key
   that appears on another key of the group or on the group's AHA/LC/ORCID records (institutions differing never block).
Ties are grown from the anchor outwards (a thin key may tie to a thin key already tied), never chained through an
untied key. Identity reads key-log rows only (graph_tables.keylog); linked credits are never evidence.

Tiers: `strict` (proposal.json): a strict tie (institution, network partner, topic ratio >= TOPIC_MIN, or a shared
venue for a name with <= 5 bearers; never a name with 26+ bearers), grown from the anchor through strict ties only, the
strict set fitting one career with no clash; `review` (review-tier.csv.gz): a weaker tie, two anchored keys that fit, or
the merge guard; `none`: no tie, or the career or a clash fails. Measurement (hand check, 2026-11-13): first rule
(any tie) 18 wrong of 190; final strict tier 0 wrong of 156 (README.md in the output folder).

    python3 scripts/key_career_merges.py --out data/identifiers/career-merges-2026-11-13
    python3 scripts/key_career_merges.py --graph <pre-merge snapshot> --no-validate --out <scratch>   # recall test
"""
import argparse
import csv
import gzip
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
from link_cited_work_authors import forms, heading_dates, population_counts  # noqa: E402
from propose_person_dup_merges import names_agree, strict_agree, review_verdicts  # noqa: E402
from key_review_credit_merges import agree as inst_agree  # noqa: E402
from key_review_reviewers import journal_key  # noqa: E402
from link_work_people import p9_tokens, p9_terms, thash, SUBFIELD  # noqa: E402

ROOT = I.ROOT
IDS = ROOT / 'data/identifiers'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
CACHE = ROOT / 'build/keylog-state.sqlite'
WPDUP = IDS / 'work-people-2026-11-11/candidate-duplicates.csv.gz'
PUBLIC = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'atlas', 'ol')
CLASH = ('lcnaf', 'wd', 'orcid', 'isni', 'idref')
THIN_FAMILY = {'review-credit': 'review', 'diss-author': 'thesis', 'aha-phd': 'aha', 'aha': 'aha',
               'repo-advisor': 'advisor', 'coauthor-mention': 'name'}
REVIEW_PREFIX = re.compile(r'^\s*(review of|reviewed work\(s\):|rezension zu|compte rendu de)\s*', re.I)
HNET = re.compile(r'\((H-[A-Za-z][A-Za-z\-]*)[,)]')
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/career')
MU, CAP = 2.0, 3.0
# German, French, Spanish and Italian function words the pass-nine stop list lacks (hand check: 'zum fur' made a topic
# tie between a historian of psychiatry and a historian of the Peasants' War)
EXTRA_STOP = {w[:7] for w in '''zum zur fur fuer auf bis als aus bei beim vom einer eines einem einen im ins zwischen seit gegen
uber ueber nach unter sowie oder wie sie ihr ihre sich nicht sur aux une les par pour dans entre avec sous del las los por
para con sobre entre degli della delle dei nel nella sul sulla tra fra'''.split()}
TOPIC_MIN = 6.0     # subject + subfield ratio for a topic tie in the strict tier (hand check: weaker scores misled)


def fam_key(f):
    return f.replace(' ', '')       # 'mac farlane' = 'macfarlane'


def hyphen_given(label):
    """hyphenated given names as printed ('Peter-Michael'), folded"""
    l = label or ''
    giv = l.split(',', 1)[1] if ',' in l else ' '.join(l.split()[:-1])
    return {w.lower() for w in re.findall(r"[^\W\d_]+-[^\W\d_]+", giv)}


def band(b):
    return 'unique' if b <= 1 else '2-5' if b <= 5 else '6-25' if b <= 25 else '26+'


def initials_only(label):
    fs = forms(label)
    return bool(fs) and all(all(len(w) == 1 for w in g) for _, _, g in fs)


def thin_type(anchors):
    """the thin source of a key, or None for an anchored key (a public identifier, or two source families)"""
    fams = set()
    for a in anchors:
        s = a.split(':', 1)[0]
        if s in PUBLIC:
            return None
        if s == 'review-credit':
            fams.add('review')
        elif s in THIN_FAMILY:
            fams.add(THIN_FAMILY[s])
        else:
            fams.add(s)
    if not fams:
        return 'name'
    if len(fams) == 1 and next(iter(fams)) in set(THIN_FAMILY.values()):
        return next(iter(fams))
    return None


def doc_title(label):
    t = REVIEW_PREFIX.sub('', label or '')
    t = re.sub(r'\((H-[^)]*)\)\s*$', '', t)
    return t


class Graph:
    """the facts of the keys that matter, from build/graph (key-log rows only) and the side files"""

    def __init__(self, G, keys, people):
        self.G = G
        db = self.db = duckdb.connect()
        db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH}/duck'")
        db.execute('CREATE TEMP TABLE want(key VARCHAR)')
        db.executemany('INSERT INTO want VALUES (?)', [(k,) for k in keys])
        ins = dict(db.execute(f"SELECT key, label FROM '{G}/institution.parquet'").fetchall())
        self.inst_label = ins
        self.works = defaultdict(dict)      # key -> work -> (title, year, kind, venue)
        for k, w, lab, y, fy, kind, j in db.execute(f"""
                SELECT a."from", a."to", w.label, w.year, w.first_year, w.kind, w.journal FROM (
                  SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
                  UNION SELECT "from", "to" FROM '{G}/edited.parquet' WHERE evidence = 'keylog') a
                JOIN want ON want.key = a."from" JOIN '{G}/work.parquet' w ON w.key = a."to" """).fetchall():
            m = HNET.search(lab or '')
            venue = journal_key(j) if j else (m.group(1).lower() if m else '')
            yr = fy if (kind == 'book' and fy) else y
            self.works[k][w] = (lab or '', yr, kind or '', venue)
        self.affs = defaultdict(list)       # key -> (inst key or None, label, year)
        for k, i, src, lo, hi in db.execute(f"""SELECT a."from", a."to", a.source, a.first_year, a.last_year
                FROM '{G}/affiliated_with.parquet' a JOIN want ON want.key = a."from" """).fetchall():
            self.affs[k].append((i, ins.get(i, ''), lo or hi, src))
        for k, i, y in db.execute(f"""SELECT a."from", b."to", w.year FROM (SELECT "from", "to" FROM '{G}/authored.parquet'
                WHERE evidence = 'keylog') a JOIN want ON want.key = a."from" JOIN '{G}/work.parquet' w ON w.key = a."to"
                JOIN '{G}/awarded_by.parquet' b ON b."from" = a."to" WHERE w.kind = 'thesis'""").fetchall():
            self.affs[k].append((i, ins.get(i, ''), y, 'thesis'))
        self.partners = defaultdict(set)    # network partners (key-log evidence)
        for t, cols in (('reviewed', '"from", "to"'), ('coauthored', '"from", "to"'), ('coedited', '"from", "to"'),
                        ('advised', '"from", "to"')):
            try:
                rows = db.execute(f"""SELECT {cols} FROM '{G}/{t}.parquet' WHERE evidence = 'keylog'
                        AND ("from" IN (SELECT key FROM want) OR "to" IN (SELECT key FROM want))""").fetchall()
            except duckdb.Error:
                continue
            for a, b in rows:
                if a != b:
                    self.partners[a].add((t, b))
                    self.partners[b].add((t, a))
        self.life = {}
        with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                b = int(r['birth']) if r['birth'].lstrip('-').isdigit() else None
                d = int(r['death']) if r['death'].lstrip('-').isdigit() else None
                if b or d:
                    self.life[r['key']] = (b, d)
        self.aha = {}
        need = {a.split(':', 1)[1] for k in keys for a in people[k]['anchors'] if a.startswith('aha-phd:')}
        for line in open(AHA, encoding='utf-8'):
            r = json.loads(line)
            if r['id'] in need:
                self.aha[r['id']] = (r.get('year'), re.sub(r',?\s*(Dept|Department)\.? of .*$', '', r.get('department') or ''),
                                     r.get('title') or '')

    def facts(self, k, anchors, label=''):
        ids = defaultdict(set)
        insts = []
        phd = set()
        theses = set()
        years = []
        for a in anchors:
            s, _, v = a.partition(':')
            ids[s].add(v)
            if s == 'review-credit' and '|' in v and not v.startswith('hnet-review:'):
                insts.append((None, v.split('|', 1)[1], None, 'review-credit'))
            if s == 'aha-phd' and v in self.aha:
                y, dept, title = self.aha[v]
                if y:
                    phd.add(int(y))
                if dept:
                    insts.append((None, dept, y, 'aha-phd'))
        for w, (lab, y, kind, venue) in self.works.get(k, {}).items():
            if kind == 'thesis':
                theses.add(w)
                if y:
                    phd.add(y)
            if y:
                years.append((y, kind))
        insts += self.affs.get(k, [])
        life = self.life.get(k)
        if not life:            # life years printed in the heading ('Elliott, Charles, 1792-1869') count too
            life = heading_dates(label) if re.search(r'\d{4}', label or '') else (None, None)
        return dict(key=k, ids=ids, insts=insts, phd=phd, theses=theses, years=years,
                    works=self.works.get(k, {}), life=life,
                    partners=self.partners.get(k, set()))


# ------------------------------------------------------------------ topic (pass-nine ratio, key against key)

class Topic:
    def __init__(self, db, G, vocab):
        """document frequency over all graph work titles of the terms in `vocab`"""
        self.df = Counter()
        n = 0
        cur = db.execute(f"SELECT label FROM '{G}/work.parquet' WHERE label IS NOT NULL")
        while True:
            rows = cur.fetchmany(200000)
            if not rows:
                break
            for (lab,) in rows:
                n += 1
                for t in p9_terms(p9_tokens(lab)):
                    if t in vocab:
                        self.df[t] += 1
        self.N = n

    def pbg(self, t):
        return (self.df.get(t, 0) + 0.5) / self.N

    @staticmethod
    def docs(works, skip=()):
        out = []
        for w, (lab, y, kind, venue) in works.items():
            if w in skip:
                continue
            toks = tuple(t for t in p9_tokens(doc_title(lab)) if t not in EXTRA_STOP)
            if toks:
                out.append(p9_terms(toks))
        return out

    def score(self, ctx_docs, prof_docs):
        """(subject, subfield, top terms) of the context's terms under the profile; profile size"""
        prof = Counter()
        for d in prof_docs:
            prof.update(d)
        n = len(prof_docs)
        if not n:
            return 0.0, 0.0, [], 0
        terms = set().union(*ctx_docs) if ctx_docs else set()
        s1 = s2 = 0.0
        top = []
        for t in terms:
            c = prof.get(t)
            if not c:
                continue
            pb = self.pbg(t)
            v = math.log((c + MU * pb) / (n + MU) / pb)
            if v <= 0:
                continue
            v = min(CAP, v)
            parts = t.split(' ')
            if any(x in SUBFIELD for x in parts) and all(x in SUBFIELD or x.startswith('histor') for x in parts):
                s2 += v
            else:
                s1 += v
            top.append((round(v, 2), t))
        top.sort(reverse=True)
        return s1, s2, top[:6], n


# ------------------------------------------------------------------ judging

def window(f):
    ys = [y for y, kind in f['years'] if kind in ('review', 'article', 'thesis', 'chapter', 'other')]
    ys += [y for _, _, y, src in f['insts'] if y and src not in ('lc_373', 'wikidata')]
    ys += list(f['phd'])
    ys = ys or [y for y, _ in f['years']]
    return (min(ys), max(ys)) if ys else None


def could_be(life, win):
    if not win:
        return True
    b, d = life
    return not ((b and b + 20 > win[1]) or (d and d + 3 < win[0]))


def hard_clash(fa, fb):
    for s in CLASH:
        va, vb = fa['ids'].get(s, set()), fb['ids'].get(s, set())
        if va and vb and not (va & vb):
            return f'{s}-differs'
    (ba, da), (bb, db_) = fa['life'], fb['life']
    if ba and bb and abs(ba - bb) > 1:
        return 'birth-differs'
    if da and db_ and abs(da - db_) > 1:
        return 'death-differs'
    if fa['theses'] and fb['theses'] and not (fa['theses'] & fb['theses']):
        return 'two-theses'
    if fa['phd'] and fb['phd'] and min(abs(x - y) for x in fa['phd'] for y in fb['phd']) > 2:
        return 'two-phd-years'
    return None


def career_fits(fs):
    """None if the dated facts of the keys `fs` fit one working life, else the reason"""
    life_b = [f['life'][0] for f in fs if f['life'][0]]
    life_d = [f['life'][1] for f in fs if f['life'][1]]
    phd = sorted({y for f in fs for y in f['phd']})
    act = [y for f in fs for y, kind in f['years'] if kind in ('review', 'article', 'thesis', 'chapter')]
    allys = act + [y for f in fs for y, kind in f['years'] if kind not in ('review', 'article', 'thesis', 'chapter')]
    if phd:
        T = phd[0]
        if any(y < T - 9 or y > T + 50 for y in act):
            return 'outside-thesis-window'
    if life_b and any(y < min(life_b) + 20 for y in act):
        return 'before-adulthood'
    if life_d and any(y > max(life_d) + 3 for y in act if True):
        return 'after-death'
    if act and max(act) - min(act) > 55:
        return 'span-over-55'
    return None


def inst_tie(ft, frest, cache):
    for ia, la, _, sa in ft['insts']:
        for f in frest:
            for ib, lb, _, sb in f['insts']:
                if ia and ib:
                    same = ia == ib
                else:
                    kk = (la, lb)
                    if kk not in cache:
                        cache[kk] = bool(la and lb and inst_agree(la, lb))
                    same = cache[kk]
                if same:
                    return f'{(la or lb)[:50]}|{sa}~{sb}'
    return None


def venue_tie(ft, frest):
    vt = Counter(v for (_, _, _, v) in ft['works'].values() if v)
    vr = Counter(v for f in frest for (_, _, _, v) in f['works'].values() if v)
    common = set(vt) & set(vr)
    return sorted(common)[0] if common else None


def network_tie(ft, frest, rest_keys):
    pt = {b for _, b in ft['partners']} - rest_keys - {ft['key']}
    for f in frest:
        pr = {b for _, b in f['partners']} - {ft['key'], f['key']}
        both = pt & pr
        if both:
            return sorted(both)[0]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--graph', type=Path, default=ROOT / 'build/graph')
    ap.add_argument('--out', type=Path, default=IDS / 'career-merges-2026-11-13')
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'duck').mkdir(exist_ok=True)
    G = args.graph
    R = Counter()
    db0 = duckdb.connect()
    db0.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH}/duck'")
    people = {k: dict(label=l or '', anchors=list(a or []), resolution=r) for k, l, r, a in
              db0.execute(f"SELECT key, label, resolution, anchors FROM '{G}/person.parquet'").fetchall()}
    R['person_keys'] = len(people)
    # not-same marks (key-log cache)
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    notsame = defaultdict(set)
    for k, m in con.execute("SELECT key, member FROM members WHERE member >= 'not-same:' AND member < 'not-same;'"):
        notsame[k].add(m[len('not-same:'):])
    seq = int(dict(con.execute('SELECT k, v FROM meta').fetchall())['seq'])
    con.close()
    R['keylog_seq'] = seq
    verdicts = review_verdicts()

    # ---- name blocks: (family key, first written given name) -> keys; initials-only keys by (family key, initial)
    thin = {k: thin_type(p['anchors']) for k, p in people.items()}
    block = defaultdict(set)
    init_block = defaultdict(set)
    nforms = {}
    for k, p in people.items():
        fs = forms(p['label'])
        nforms[k] = fs
        for f, _, g in fs:
            wr = [w for w in g if len(w) > 1]
            if wr:
                block[fam_key(f), wr[0]].add(k)
            elif g:
                init_block[fam_key(f), g[0]].add(k)
    R['thin_keys'] = Counter(v for v in thin.values() if v)
    # thin keys with a full given name sharing a block with another key
    cand_groups = []
    seen_thin = set()
    for bk, ks in block.items():
        if len(ks) < 2:
            continue
        thins = [k for k in ks if thin[k] and not initials_only(people[k]['label'])]
        if not thins:
            continue
        cand_groups.append((bk, ks))
        seen_thin.update(thins)
    R['thin_keys_sharing_a_name_block'] = len(seen_thin)
    need = set()
    for bk, ks in cand_groups:
        need |= ks
        need |= init_block.get((bk[0], bk[1][0]), set())
    R['keys_read'] = len(need)
    print('blocks', len(cand_groups), 'keys', len(need), flush=True)
    GR = Graph(G, need, people)
    facts = {k: GR.facts(k, people[k]['anchors'], people[k]['label']) for k in need}

    # ---- LC authorities by family key and OpenAlex counts (name frequency)
    famw = {bk[0] for bk, _ in cand_groups}
    lc_by = defaultdict(list)
    cur = db0.execute(f"SELECT lcid, label, birth, death FROM '{LC_NAMES}' WHERE NOT coalesce(deprecated, false)")
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for lcid, label, lb_, ld_ in rows:
            if not label or ',' not in label:
                continue
            fs = forms(label)
            if not fs or fam_key(fs[0][0]) not in famw:
                continue
            hb, hd = heading_dates(label)
            yb = int(lb_[:4]) if lb_ and lb_[:4].isdigit() else hb
            yd = int(ld_[:4]) if ld_ and ld_[:4].isdigit() else hd
            lc_by[fam_key(fs[0][0])].append((lcid, label, fs[0][2], yb, yd))
    needed_nk = {(f, g[0]) for k in need for f, _, g in nforms[k][:1] if g}
    pop = population_counts(db0, needed_nk)
    print('lc read', sum(len(v) for v in lc_by.values()), flush=True)

    # ---- topic background over the vocabulary of the keys read
    vocab = set()
    docs_of = {}
    for k in need:
        docs_of[k] = Topic.docs(facts[k]['works'])
        for d in docs_of[k]:
            vocab |= d
    TP = Topic(db0, G, vocab)
    print('topic df', len(TP.df), 'over', TP.N, 'titles', flush=True)

    def compatible(a, b):
        la, lb = people[a]['label'], people[b]['label']
        if hyphen_given(la) != hyphen_given(lb):    # 'Peter-Michael' is one given name, not Peter + Michael
            return False
        return names_agree(la, lb)

    def separated(t, k):
        """hard evidence that key k cannot be the person of thin key t"""
        if k in notsame.get(t, ()) or t in notsame.get(k, ()):
            return 'not-same'
        v = verdicts.get(frozenset((t, k)))
        if v and v.startswith('different'):
            return 'outside-review-different'
        c = hard_clash(facts[t], facts[k])
        if c:
            return c
        if not could_be(facts[k]['life'], window(facts[t])):
            return 'life-years'
        return None

    # ---- per thin key: its name group, closure, frequency
    rows = []
    done_thin = set()
    inst_cache = {}
    for bk, ks in cand_groups:
        for t in sorted(ks):
            if not thin[t] or initials_only(people[t]['label']) or t in done_thin:
                continue
            f0, _, g0 = nforms[t][0]
            if (fam_key(f0), next((w for w in g0 if len(w) > 1), '')) != bk:
                continue            # judged under its first reading ('Given Family' for a name without a comma)
            done_thin.add(t)        # a three-word name reads under two family forms: judged once, under the first
            ft = facts[t]
            comp = [k for k in ks if k != t and compatible(t, k)]
            if not comp:
                continue
            comp_init = [k for k in init_block.get((bk[0], bk[1][0]), ()) if compatible(t, k)]
            sep = {k: separated(t, k) for k in comp + comp_init}
            inside = [k for k in comp if not sep[k]]
            anchored = [k for k in inside if not thin[k]]
            init_anch = [k for k in comp_init if not thin[k] and not sep[k]]
            ev = dict(thin=t, thin_type=thin[t], label=people[t]['label'], block=f'{bk[0]}|{bk[1]}',
                      compatible=len(comp), separated=sum(1 for k in comp if sep[k]),
                      separated_why=';'.join(sorted({sep[k] for k in comp if sep[k]})))
            # frequency: date-possible LC authorities of the name not anchored on an inside key
            own_lc = {a.split(':', 1)[1] for k in inside for a in people[k]['anchors'] if a.startswith('lcnaf:')}
            own_lc |= {a.split(':', 1)[1] for a in people[t]['anchors'] if a.startswith('lcnaf:')}
            win = window(ft)
            lc_dp = 0
            for lcid, lab, g2, yb, yd in lc_by.get(bk[0], ()):
                if lcid in own_lc:
                    continue
                if strict_agree(ft_g := (nforms[t][0][2] if nforms[t] else ()), g2) and could_be((yb, yd), win):
                    lc_dp += 1
            nk = (nforms[t][0][0], nforms[t][0][2][0]) if nforms[t] and nforms[t][0][2] else None
            n_oa = pop[1].get(nk, 0) if nk else 0
            bearers = max(lc_dp + 1, n_oa)
            ev.update(lc_others=lc_dp, oa_n=n_oa, bearers=bearers, band=band(bearers))
            if not inside:
                ev.update(status='blocked', why='every compatible key separated')
                rows.append(ev)
                continue
            if len(anchored) >= 2:
                ev.update(status='review', why='two-or-more-anchored-keys', targets='|'.join(sorted(anchored)))
            elif init_anch:
                ev.update(status='review', why='anchored-initials-key-fits', targets='|'.join(sorted(anchored + init_anch)))
            else:
                ev.update(status='candidate', targets='|'.join(sorted(anchored)))
            ev['group'] = sorted(inside + [t])
            ev['anchor'] = anchored[0] if len(anchored) == 1 else ''
            rows.append(ev)
    R['thin_rows'] = len(rows)
    R['thin_rows_status'] = Counter(r['status'] + ':' + r.get('why', '') for r in rows)

    # ---- groups: one per (block, anchor) for candidate rows; ties grown outwards from the anchor
    by_group = defaultdict(set)
    for r in rows:
        if r['status'] == 'candidate':
            by_group[tuple(r['group'])].add(r['thin'])
    rowmap = {r['thin']: r for r in rows}

    def tie(t, S):
        ft = facts[t]
        frest = [facts[k] for k in S]
        out = {}
        it = inst_tie(ft, frest, inst_cache)
        if it:
            out['institution'] = it
        vt = venue_tie(ft, frest)
        if vt:
            out['venue'] = vt
        nt = network_tie(ft, frest, set(S))
        if nt:
            out['network'] = nt
        ctx = docs_of[t]
        prof = [d for k in S for d in docs_of[k]]
        s1, s2, top, n = TP.score(ctx, prof)
        out['lrs'] = round(s1, 2)
        out['lrf'] = round(s2, 2)
        out['psz'] = n
        out['top'] = ' '.join(t_ for _, t_ in top[:4])
        return out

    def strong(x, band_):
        """the measured strict tie (sample-checked.csv): an institution, a network partner, topic (subject + subfield
        ratio >= TOPIC_MIN), or a shared venue when the name is not common (bearers <= 5); never for a name with 26+ bearers. A weak topic score alone
        (under TOPIC_MIN) and a venue alone for a common name failed the hand check."""
        if band_ == '26+':
            return False        # hand check: 3 of 13 strict rows in the 26+ band were other people (review tier)
        if x.get('institution') or x.get('network'):
            return True
        if x['lrs'] + x['lrf'] >= TOPIC_MIN:
            return True
        return bool(x.get('venue')) and band_ in ('unique', '2-5')

    def any_tie(x):
        return bool(x.get('institution') or x.get('venue') or x.get('network') or x['lrs'] + x['lrf'] > 0)

    def grow(seed, pend, ok):
        S, pend, info = [seed], list(pend), {}
        changed = True
        while changed and pend:
            changed = False
            for t in list(pend):
                x = tie(t, S)
                info[t] = x
                if ok(t, x):
                    S.append(t)
                    pend.remove(t)
                    changed = True
        return S, pend, info

    def clash_in(S):
        for i, a in enumerate(S):
            for b in S[i + 1:]:
                if not compatible(a, b):
                    return f'names-disagree:{a}~{b}'
                c = hard_clash(facts[a], facts[b])
                if c:
                    return f'{c}:{a}~{b}'
        return None

    merges = {}           # thin key -> survivor (strict)
    for grp, thins in by_group.items():
        grp = list(grp)
        anch = [k for k in grp if not thin[k]]
        # only the thin keys whose own name group is this one are judged here (a 'Daniel' key and a 'Daniel W.' key
        # can have different groups); the seed of a thin-only group is one of them
        seed = anch[0] if anch else sorted(thins, key=lambda k: (
            {'thesis': 0, 'aha': 1, 'review': 2, 'advisor': 3, 'name': 4}[thin[k]], -len(facts[k]['works']), int(k[2:])))[0]
        others = [k for k in sorted(thins) if k != seed]
        Ss, rest, info_s = grow(seed, others, lambda t, x: strong(x, rowmap[t]['band']))
        # a strict member must also fit one career with the strict set and clash with nobody in it
        cf_s, bad_s = career_fits([facts[k] for k in Ss]), clash_in(Ss)
        Sw, never, info_w = grow(seed, others, lambda t, x: any_tie(x))
        cf_w, bad_w = career_fits([facts[k] for k in Sw]), clash_in(Sw)
        for t in others:
            r = rowmap[t]
            x = info_s.get(t) if t in Ss else (info_w.get(t) or tie(t, Ss))
            r.update(seed=seed, n_group=len(grp), **{f't_{k}': v for k, v in x.items()})
            r['strict_tie'] = t in Ss
            r['career'] = (cf_s if t in Ss else cf_w) or 'fits'
            r['group_clash'] = (bad_s if t in Ss else bad_w) or ''
            if t in Ss and not cf_s and not bad_s:
                r['tier'] = 'strict'
                merges[t] = seed
            elif t in Sw and r['career'] == 'fits' and not r['group_clash']:
                r['tier'] = 'review'
                r['why'] = 'tie-below-strict-bar' if t not in Ss else 'group-career-or-clash'
            else:
                r['tier'] = 'none'
                r['why'] = 'no-tie' if t in never else (r['career'] if r['career'] != 'fits' else r['group_clash'])
    for r in rows:
        if r['status'] == 'review':
            r['tier'] = 'review'
        elif r['status'] == 'blocked':
            r['tier'] = 'none'
        elif 'tier' not in r:
            r['tier'] = 'survivor'
    # merge guard: a strict merge touching a pooled key or an open conflict goes to review
    import keylog_snapshot as KS
    from merge_guard import SINGLE_KEY_CHECKS, blocked_keys
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    state = KS.read_state()
    blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
    for t in list(merges):
        if t in blocked or merges[t] in blocked:
            rowmap[t].update(tier='review', why='merge-guard')
            del merges[t]
    # a survivor that is itself merged away is impossible (seeds are never thin members of another group), but check
    assert not (set(merges) & set(merges.values()))
    R['groups'] = len(by_group)
    R['tiers'] = Counter(r['tier'] for r in rows)
    R['strict_by_band'] = Counter(rowmap[t]['band'] for t in merges)
    R['strict_by_thin_type'] = Counter(rowmap[t]['thin_type'] for t in merges)
    R['strict_into_anchored'] = sum(1 for t, s in merges.items() if not thin[s])
    R['strict_into_thin'] = sum(1 for t, s in merges.items() if thin[s])
    R['strict_by_tie'] = Counter(
        'institution' if r.get('t_institution') else 'network' if r.get('t_network') else
        f'topic>={TOPIC_MIN:g}' if r['t_lrs'] + r['t_lrf'] >= TOPIC_MIN else 'venue' for r in (rowmap[t] for t in merges))
    R['review_by_why'] = Counter(r.get('why') for r in rows if r['tier'] == 'review')
    R['person_keys_removed_if_applied'] = len(merges)

    # ---- what it would change
    db0.execute('CREATE OR REPLACE TEMP TABLE mm(k VARCHAR, s VARCHAR)')
    db0.executemany('INSERT INTO mm VALUES (?, ?)', list(merges.items()))
    pos = db0.execute(f"""WITH c AS (SELECT "to" w, role, "from" k FROM '{G}/author_candidates.parquet'),
            m AS (SELECT c.w, c.role, c.k, coalesce(mm.s, c.k) k2 FROM c LEFT JOIN mm ON mm.k = c.k)
            SELECT count(*) FILTER (WHERE n1 >= 2 AND n2 = 1), count(*) FILTER (WHERE n2 < n1), count(*) FROM
            (SELECT w, role, count(DISTINCT k) n1, count(DISTINCT k2) n2 FROM m GROUP BY ALL)""").fetchone()
    R['candidate_positions_single_after'] = pos[0]
    R['candidate_positions_fewer_claimants'] = pos[1]
    R['candidate_positions_total'] = pos[2]
    cluster = {k: merges.get(k, k) for k in people}
    ps = db0.execute(f"SELECT \"from\", \"to\" FROM '{G}/possibly_same.parquet'").fetchall()
    R['possibly_same_pairs'] = len(ps)
    R['possibly_same_pairs_resolved'] = sum(1 for a, b in ps if cluster.get(a, a) == cluster.get(b, b))
    ng = nfull = npart = 0
    with gzip.open(WPDUP, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ks = [k for k in r['keys'].split('|') if k in people]
            if len(ks) < 2:
                continue
            ng += 1
            cs = {cluster[k] for k in ks}
            nfull += len(cs) == 1
            npart += 1 < len(cs) < len(ks)
    R['duplicate_groups_live'] = ng
    R['duplicate_groups_fully_resolved'] = nfull
    R['duplicate_groups_partly_resolved'] = npart
    probes = ('p-151402', 'p-151403', 'p-171364', 'p-173252', 'p-96495')
    R['probe_macfarlane'] = {k: dict(tier=rowmap[k].get('tier'), into=merges.get(k), why=rowmap[k].get('why'),
                                     institution=rowmap[k].get('t_institution'), venue=rowmap[k].get('t_venue'),
                                     network=rowmap[k].get('t_network'), lrs=rowmap[k].get('t_lrs'),
                                     lrf=rowmap[k].get('t_lrf')) for k in probes if k in rowmap}

    # ---- outputs
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    cols = ['thin', 'thin_type', 'label', 'tier', 'why', 'seed', 'anchor', 'targets', 'n_group', 'band', 'bearers',
            'lc_others', 'oa_n', 'compatible', 'separated', 'separated_why', 'strict_tie', 'career', 'group_clash',
            't_institution', 't_venue', 't_network', 't_lrs', 't_lrf', 't_psz', 't_top']
    with gzip.open(SCRATCH / 'all-rows.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with gzip.open(out / 'review-tier.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols + ['seed_label'], extrasaction='ignore')
        w.writeheader()
        for r in sorted((r for r in rows if r['tier'] == 'review'), key=lambda r: r['label']):
            w.writerow(dict(r, seed_label=people.get(r.get('seed') or '', {}).get('label', '')))
    with gzip.open(out / 'strict-tier.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols + ['seed_label'], extrasaction='ignore')
        w.writeheader()
        for t in sorted(merges, key=lambda t: rowmap[t]['label']):
            w.writerow(dict(rowmap[t], seed_label=people[merges[t]]['label']))
    ops = []
    for t in sorted(merges, key=lambda t: int(t[2:])):
        r, s = rowmap[t], merges[t]
        tie_txt = '; '.join(f'{k}:{r[f"t_{k}"]}' for k in ('institution', 'network', 'venue') if r.get(f't_{k}'))
        tie_txt += f"; topic lrs={r['t_lrs']} lrf={r['t_lrf']}" + (f" ({r['t_top']})" if r.get('t_top') else '')
        ops.append(dict(event='merge', key=t, into=s, decided_by='rule', basis=(
            f"one career on several keys ({out.name}, strict): {r['label']} ({r['thin_type']} key) and "
            f"{people[s]['label']}: full names agree, the name group is closed (bearers {r['bearers']}), dates fit one "
            f"career; tie: {tie_txt.strip('; ')}")[:900]))
    proposal = dict(basis=f'thin person keys of one career ({out.name}, strict tier; ARCHITECTURE.md §8 class 39): '
                          'full-name agreement, closed name group, dates fit one working life, and a measured tie '
                          '(institution, network partner, topic ratio, or shared venue for an uncommon name)',
                    decided_by='rule', ops=ops)
    if not args.no_validate:
        events, _ = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(events)
    (out / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=0) + '\n')
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sorted(R.items())}
    rep['topic_min'] = TOPIC_MIN
    (out / 'run-report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list) + '\n')
    json.dump(dict(rows=[{k: v for k, v in r.items()} for r in rows], people={k: people[k] for k in need}),
              gzip.open(SCRATCH / f'state-{out.name}.json.gz', 'wt', encoding='utf-8'), default=list)
    print(json.dumps(rep, indent=1, default=list))


if __name__ == '__main__':
    main()
