"""One person, two records of one doctorate -> a tiered merge PROPOSAL (2026-11-14; ARCHITECTURE.md §8). Writes, never applies.

Probe: Scott Berthelette. The AHA directory (aha-phd:9812, thesis w-64995, a working title) and the Saskatchewan
repository (diss-author:..., thesis w-70842, the deposited title) each minted a person and a thesis: same awarding
institution (i-219), same supervisor (p-39805), same year (2020). The career rule of 2026-11-13
(scripts/key_career_merges.py, hard_clash) separates any two keys that each hold a thesis with no thesis in common
('two-theses'), so the pair was never judged: the second record of one doctorate read as a second doctorate.

Class: two live person keys, each the key-log author of a thesis node, whose theses are one doctorate:
1. Names: full-name agreement (key_career_merges.compatible: names_agree, the first written-out given name identical,
   an extra middle name or initial allowed, conflicting initials, Jr/Sr or a hyphenated given name block; never a
   nickname). Initials-only keys never qualify.
2. The doctorate: the same awarding institution key (AWARDED_BY) and degree years within YEAR_WINDOW (measured: see
   the offset table in report.json; AHA years are conferral years, repository years deposit years).
3. Strict tier: (a) a shared supervisor key; or (b) neither side contradicts (one or both theses carry no supervisor)
   and the name has at most 5 bearers; or (c) 6-25 bearers, no supervisor contradiction and a title overlap (support
   only: never alone, never a block). Names with 26+ bearers are never strict. Review tier: the doctorate matches but
   the supervisors on both records are disjoint, 26+ bearers, 6-25 without title support, a 'same year, different
   institution' pair, or a component of three or more keys that does not hold together.
4. Guards (all tiers): different LC/Wikidata/ORCID/ISNI/IdRef on the two keys, life years that disagree (birth or
   death more than one year apart, a degree before age 20), a not-same mark or an outside 'different' verdict, the merge
   guard (keys in an open conflict). Two doctorates (different institutions, or years beyond the window) stay separate.

Works side: the two thesis nodes are one work. Like scripts/work_dup_pairs.py's exact-identifier pairs of two key-log
keys, the tie is a key-log `merge` of work keys: the record whose title was deposited (repository `diss-thesis:`,
then OpenAlex/DOI, then AHA `aha-diss:`) survives and keeps its label; the other title is kept on the survivor as a
`variant-title:` member; when the two years differ, the merged-in year member is detached (the build takes the
smallest `year:` member, which would otherwise be the AHA year). Both supervision claims then point at one work; the
explorer groups SUPERVISED rows by the other node, so the supervisor and the thesis show once (n = 2). One person key
holding both records of one doctorate (same institution, years within the window) gets the same work merge.

    python3 scripts/key_thesis_twins.py --out data/identifiers/thesis-twin-merges-2026-11-14
"""
import argparse
import csv
import gzip
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
from key_career_merges import (fam_key, hyphen_given, initials_only, thin_type, band, CLASH, LIFE, AHA,  # noqa: E402
                               LC_NAMES)
from link_cited_work_authors import forms, heading_dates, population_counts  # noqa: E402
from propose_person_dup_merges import names_agree, strict_agree, review_verdicts  # noqa: E402
from link_work_people import p9_tokens  # noqa: E402

ROOT = I.ROOT
IDS = ROOT / 'data/identifiers'
CACHE = ROOT / 'build/keylog-state.sqlite'
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/thesis-twins')
YEAR_WINDOW = 1         # widened only if the measured offsets support it (report.json: offsets)
SOURCE_RANK = {'diss-thesis': 0, 'openalex': 1, 'doi': 1, 'orcid-work': 2, 'prizework': 3, 'aha-diss': 4}
GENERIC = {'histor', 'history', 'histori', 'century', 'centuri', 'america', 'american', 'united', 'states', 'state',
           'nineteen', 'twentie', 'eightee', 'social', 'politic', 'cultura', 'culture', 'nation', 'nationa', 'study',
           'studies', 'dissert', 'thesis', 'new', 'early', 'modern', 'world', 'during', 'between', 'toward', 'towards'}


def source_of(anchors):
    ss = {a.split(':', 1)[0] for a in anchors}
    return min(ss, key=lambda s: SOURCE_RANK.get(s, 3)) if ss else ''


def title_overlap(a, b):
    """shared content stems of two titles (generic history words removed), and their share of the shorter title"""
    ta = {t for t in p9_tokens(a) if t not in GENERIC and not t.isdigit()}
    tb = {t for t in p9_tokens(b) if t not in GENERIC and not t.isdigit()}
    sh = ta & tb
    return sorted(sh), (len(sh) / min(len(ta), len(tb)) if ta and tb else 0.0)


def fold(t):
    return re.sub(r'[^a-z0-9]', '', (t or '').lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--graph', type=Path, default=ROOT / 'build/graph')
    ap.add_argument('--out', type=Path, default=IDS / 'thesis-twin-merges-2026-11-14')
    ap.add_argument('--window', type=int, default=YEAR_WINDOW)
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    W = args.window
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'duck').mkdir(exist_ok=True)
    G = args.graph
    R = Counter()
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH}/duck'")
    people = {k: dict(label=l or '', anchors=list(a or [])) for k, l, a in
              db.execute(f"SELECT key, label, anchors FROM '{G}/person.parquet'").fetchall()}
    inst_label = dict(db.execute(f"SELECT key, label FROM '{G}/institution.parquet'").fetchall())

    # ---- thesis works, their key-log authors, institutions, supervisors
    works = {}
    for k, lab, y, anc in db.execute(f"SELECT key, label, year, anchors FROM '{G}/work.parquet' WHERE kind = 'thesis'").fetchall():
        works[k] = dict(label=lab or '', year=y, anchors=list(anc or []), src=source_of(anc or []), inst=set(), sup=set(),
                        authors=set())
    for w, i in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/awarded_by.parquet'").fetchall():
        if w in works:
            works[w]['inst'].add(i)
    for p, w in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/supervised.parquet'").fetchall():
        if w in works:
            works[w]['sup'].add(p)
    theses_of = defaultdict(set)
    for p, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
                               AND coalesce(role, 'author') = 'author'""").fetchall():
        if w in works and p in people:
            works[w]['authors'].add(p)
            theses_of[p].add(w)
    R['thesis_works'] = len(works)
    R['thesis_authors'] = len(theses_of)
    aha = {}
    need_aha = {a.split(':', 1)[1] for w in works.values() for a in w['anchors'] if a.startswith('aha-diss:')}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        if r['id'] in need_aha:
            aha[r['id']] = r

    # ---- marks, verdicts, life years, possibly-same pairs
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    seq = int(dict(con.execute('SELECT k, v FROM meta').fetchall())['seq'])
    R['keylog_seq'] = seq
    notsame = defaultdict(set)
    for k, m in con.execute("SELECT key, member FROM members WHERE member >= 'not-same:' AND member < 'not-same;'"):
        notsame[k].add(m[len('not-same:'):])
    verdicts = review_verdicts()
    life = {}
    with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            b = int(r['birth']) if r['birth'].lstrip('-').isdigit() else None
            d = int(r['death']) if r['death'].lstrip('-').isdigit() else None
            if b or d:
                life[r['key']] = (b, d)
    for k in theses_of:
        if k not in life and re.search(r'\d{4}', people[k]['label']):
            hb, hd = heading_dates(people[k]['label'])
            if hb or hd:
                life[k] = (hb, hd)
    psame = {frozenset(x) for x in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/possibly_same.parquet'").fetchall()}

    # ---- name blocks over thesis authors
    block = defaultdict(set)
    nforms = {}
    placeholder = re.compile(r'(?i)^\s*author of\b|thesesfr-')     # 411 unnamed theses.fr keys share no name
    R['placeholder_name_keys_skipped'] = sum(1 for k in theses_of if placeholder.search(people[k]['label']))
    for k in theses_of:
        if placeholder.search(people[k]['label']):
            continue
        fs = forms(people[k]['label'])
        nforms[k] = fs
        for f, _, g in fs:
            wr = [x for x in g if len(x) > 1]
            if wr:
                block[fam_key(f), wr[0]].add(k)

    def compatible(a, b):
        la, lb = people[a]['label'], people[b]['label']
        if initials_only(la) or initials_only(lb) or hyphen_given(la) != hyphen_given(lb):
            return False
        return names_agree(la, lb)

    def ids(k, s):
        return {a.split(':', 1)[1] for a in people[k]['anchors'] if a.startswith(s + ':')}

    def clash(a, b, ya, yb):
        if b in notsame.get(a, ()) or a in notsame.get(b, ()):
            return 'not-same'
        v = verdicts.get(frozenset((a, b)))
        if v and v.startswith('different'):
            return 'outside-review-different'
        for s in CLASH:
            va, vb = ids(a, s), ids(b, s)
            if va and vb and not (va & vb):
                return f'{s}-differs'
        (ba, da), (bb, db_) = life.get(a, (None, None)), life.get(b, (None, None))
        if ba and bb and abs(ba - bb) > 1:
            return 'birth-differs'
        if da and db_ and abs(da - db_) > 1:
            return 'death-differs'
        for bx in (ba, bb):
            if bx and any(y and y < bx + 20 for y in (ya, yb)):
                return 'degree-before-20'
        for dx in (da, db_):
            if dx and any(y and y > dx + 1 for y in (ya, yb)):
                return 'degree-after-death'
        return None

    # ---- candidate pairs: distinct keys, compatible full names, each the author of a thesis
    pairs = {}
    for bk, ks in block.items():
        if len(ks) < 2:
            continue
        for a, b in combinations(sorted(ks, key=lambda k: int(k[2:])), 2):
            if (a, b) in pairs or not compatible(a, b):
                continue
            best = None
            for wa in theses_of[a]:
                for wb in theses_of[b]:
                    if wa == wb:
                        continue
                    A, B = works[wa], works[wb]
                    dy = abs(A['year'] - B['year']) if A['year'] and B['year'] else None
                    same_inst = bool(A['inst'] & B['inst'])
                    sup = A['sup'] & B['sup']
                    score = (same_inst, bool(sup), -(dy if dy is not None else 99))
                    if best is None or score > best[0]:
                        best = (score, wa, wb, dy, same_inst, sup)
            if best:
                pairs[a, b] = best[1:]
    R['compatible_pairs_with_two_thesis_nodes'] = len(pairs)

    # ---- offsets: name agreement + same institution + shared supervisor, any year gap (the measuring set)
    offs = Counter()
    offs_src = defaultdict(Counter)
    for (a, b), (wa, wb, dy, si, sup) in pairs.items():
        if si and sup and dy is not None:
            offs[dy] += 1
            sp = '+'.join(sorted((works[wa]['src'], works[wb]['src'])))
            offs_src[sp][dy] += 1
    R['offsets_same_inst_shared_supervisor'] = dict(sorted(offs.items()))
    R['offsets_by_sources'] = {k: dict(sorted(v.items())) for k, v in offs_src.items()}

    # ---- name frequency (bearers), as in the career rule: date-possible LC authorities beyond the pair, OpenAlex ids
    cand = {p for p, x in pairs.items() if x[3] or (x[2] is not None and x[2] <= W)}   # same institution, or years close
    keys_c = {k for p in cand for k in p}
    famw = {nforms[k][0][0] for k in keys_c if nforms[k]}
    lc_by = defaultdict(list)
    cur = db.execute(f"SELECT lcid, label, birth, death FROM '{LC_NAMES}' WHERE NOT coalesce(deprecated, false)")
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for lcid, label, lb_, ld_ in rows:
            if not label or ',' not in label:
                continue
            fs = forms(label)
            if not fs or fs[0][0] not in famw:
                continue
            hb, hd = heading_dates(label)
            yb = int(lb_[:4]) if lb_ and lb_[:4].isdigit() else hb
            yd = int(ld_[:4]) if ld_ and ld_[:4].isdigit() else hd
            lc_by[fs[0][0]].append((lcid, fs[0][2], yb, yd))
    pop = population_counts(db, {(nforms[k][0][0], nforms[k][0][2][0]) for k in keys_c if nforms[k] and nforms[k][0][2]})

    def bearers(a, b, y):
        own = ids(a, 'lcnaf') | ids(b, 'lcnaf')
        f, _, g = nforms[a][0]
        g2 = nforms[b][0][2]
        g = g if len(g) >= len(g2) else g2
        n = 0
        for lcid, gl, yb, yd in lc_by.get(f, ()):
            if lcid in own or not strict_agree(g, gl):
                continue
            if y and ((yb and yb + 20 > y) or (yd and yd < y - 3)):
                continue
            n += 1
        return max(n + 1, pop[1].get((f, g[0]), 0)), n

    # ---- judge
    rows = []
    for (a, b), (wa, wb, dy, si, sup) in sorted(pairs.items(), key=lambda x: (int(x[0][0][2:]), int(x[0][1][2:]))):
        A, B = works[wa], works[wb]
        within = dy is not None and dy <= W
        cross = A['src'] != B['src']        # one record from each source (AHA directory, repository, OpenAlex ...)
        if si and within:
            cls = 'shared-supervisor' if sup else 'same-institution-year'
        elif within and A['inst'] and B['inst']:
            cls = 'same-year-other-institution'
        elif si and dy == W + 1 and cross:
            cls = 'same-institution-offset-2'
        elif si and dy is not None and dy <= 5:
            cls = 'same-institution-years-2-5'
        else:
            continue
        sh, share = title_overlap(A['label'], B['label'])
        y = min(x for x in (A['year'], B['year']) if x) if (A['year'] or B['year']) else None
        nb, lc_o = bearers(a, b, y)
        c = clash(a, b, A['year'], B['year'])
        sup_conflict = bool(A['sup'] and B['sup'] and not sup)
        title_support = share >= 0.5
        if c:
            tier, why = 'none', c
        elif cls == 'same-year-other-institution':
            tier, why = 'review', 'other-institution'
        elif cls == 'same-institution-years-2-5':
            tier, why = 'review', 'years-apart-beyond-offset'
        elif nb >= 26:
            tier, why = 'review', 'name-26+-bearers'
        elif sup_conflict:
            tier, why = 'review', 'supervisors-disjoint'
        elif not cross and not title_support:
            # one source listing the name twice at one institution is two doctorates unless the titles agree
            # (AHA: Montgomery, Peterson, Miller, Sullivan at one department within a year or two, different topics)
            tier, why = 'review', 'same-source-titles-differ'
        elif cls == 'same-institution-offset-2':
            tier, why = (('strict', 'offset-2-shared-supervisor') if sup else ('strict', 'offset-2-title-support')
                         if title_support else ('review', 'offset-2-no-supervisor-no-title'))
        elif sup:
            tier, why = 'strict', 'shared-supervisor'
        elif nb <= 5:
            tier, why = 'strict', 'uncommon-name-no-supervisor-conflict'
        elif title_support:
            tier, why = 'strict', '6-25-bearers-title-support'
        else:
            tier, why = 'review', '6-25-bearers-no-title-support'
        rows.append(dict(a=a, b=b, a_label=people[a]['label'], b_label=people[b]['label'],
                         a_thin=thin_type(people[a]['anchors']) or 'anchored', b_thin=thin_type(people[b]['anchors']) or 'anchored',
                         wa=wa, wb=wb, wa_title=A['label'], wb_title=B['label'], wa_src=A['src'], wb_src=B['src'],
                         wa_year=A['year'], wb_year=B['year'], dy=dy, inst_a='|'.join(sorted(A['inst'])),
                         inst_b='|'.join(sorted(B['inst'])), inst_label='; '.join(sorted({inst_label.get(i, i) for i in A['inst'] | B['inst']})),
                         sup_a='|'.join(sorted(A['sup'])), sup_b='|'.join(sorted(B['sup'])), shared_sup='|'.join(sorted(sup)),
                         cls=cls, bearers=nb, band=band(nb), lc_others=lc_o, title_shared=' '.join(sh), title_share=round(share, 2),
                         possibly_same=frozenset((a, b)) in psame, tier=tier, why=why))
    R['class_by_tier'] = Counter(f"{r['cls']}|{r['tier']}" for r in rows)
    R['class'] = Counter(r['cls'] for r in rows)
    R['class_possibly_same'] = Counter(r['cls'] for r in rows if r['possibly_same'])

    # ---- components of strict pairs must hold together
    strict = [r for r in rows if r['tier'] == 'strict']
    adj = defaultdict(set)
    for r in strict:
        adj[r['a']].add(r['b'])
        adj[r['b']].add(r['a'])
    comp_of, comps = {}, []
    for k in adj:
        if k in comp_of:
            continue
        todo, cc = [k], set()
        while todo:
            x = todo.pop()
            if x in cc:
                continue
            cc.add(x)
            todo += adj[x] - cc
        for x in cc:
            comp_of[x] = len(comps)
        comps.append(cc)
    bad = set()
    for i, cc in enumerate(comps):
        if len(cc) > 2:
            for x, y in combinations(cc, 2):
                if not compatible(x, y) or clash(x, y, None, None):
                    bad.add(i)
    for r in strict:
        if comp_of[r['a']] in bad:
            r.update(tier='review', why='component-does-not-hold')
    R['components_over_two'] = sum(1 for cc in comps if len(cc) > 2)

    # ---- merge guard
    import keylog_snapshot as KS
    from merge_guard import SINGLE_KEY_CHECKS, blocked_keys
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    state = KS.read_state()
    blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
    for r in rows:
        if r['tier'] == 'strict' and (r['a'] in blocked or r['b'] in blocked):
            r.update(tier='review', why='merge-guard')
    R['tiers'] = Counter(r['tier'] for r in rows)
    R['strict_by_why'] = Counter(r['why'] for r in rows if r['tier'] == 'strict')
    R['review_by_why'] = Counter(r['why'] for r in rows if r['tier'] == 'review')
    R['none_by_why'] = Counter(r['why'] for r in rows if r['tier'] == 'none')
    R['strict_by_band'] = Counter(r['band'] for r in rows if r['tier'] == 'strict')

    # ---- person survivors: per strict component, the anchored key, else the key with the deposited record
    strict = [r for r in rows if r['tier'] == 'strict']
    adj = defaultdict(set)
    for r in strict:
        adj[r['a']].add(r['b'])
        adj[r['b']].add(r['a'])
    seen, pmerge = set(), {}
    for k in sorted(adj, key=lambda k: int(k[2:])):
        if k in seen:
            continue
        todo, cc = [k], set()
        while todo:
            x = todo.pop()
            if x not in cc:
                cc.add(x)
                todo += adj[x] - cc
        seen |= cc

        def rank(x):
            pub = sum(1 for a in people[x]['anchors'] if a.split(':', 1)[0] in CLASH)
            dep = min(SOURCE_RANK.get(works[w]['src'], 3) for w in theses_of[x])
            return (-pub, dep, -len(people[x]['anchors']), int(x[2:]))
        surv = min(cc, key=rank)
        for x in cc - {surv}:
            pmerge[x] = surv

    # ---- works: each strict pair's two thesis records -> one work; plus one key holding two records of one doctorate
    def work_rank(w):
        return (SOURCE_RANK.get(works[w]['src'], 3), -len(works[w]['anchors']), int(w[2:]))
    wpairs = []
    for r in strict:
        wpairs.append((r['wa'], r['wb'], 'person-pair', r))
    same_key = []
    for p, ws in theses_of.items():
        for wa, wb in combinations(sorted(ws), 2):
            A, B = works[wa], works[wb]
            dyk = abs(A['year'] - B['year']) if A['year'] and B['year'] else None
            cross = A['src'] != B['src']
            if A['inst'] & B['inst'] and dyk is not None and (dyk <= W or (dyk == W + 1 and cross)):
                sh, share = title_overlap(A['label'], B['label'])
                sup = A['sup'] & B['sup']
                if A['sup'] and B['sup'] and not sup:
                    ok, why = False, 'supervisors-disjoint'
                elif not cross and share < 0.5:
                    ok, why = False, 'same-source-titles-differ'
                elif dyk > W and not (sup or share >= 0.5):
                    ok, why = False, 'offset-2-no-supervisor-no-title'
                else:
                    ok, why = True, 'one-key' if dyk <= W else 'one-key-offset-2'
                same_key.append(dict(person=p, label=people[p]['label'], wa=wa, wb=wb, wa_title=A['label'],
                                     wb_title=B['label'], wa_src=A['src'], wb_src=B['src'], wa_year=A['year'],
                                     wb_year=B['year'], inst_label='; '.join(sorted({inst_label.get(i, i) for i in A['inst'] | B['inst']})),
                                     shared_sup='|'.join(sorted(sup)), title_shared=' '.join(sh),
                                     dy=dyk, tier='strict' if ok else 'review', why=why))
                if ok:
                    wpairs.append((wa, wb, 'one-key', None))
    R['one_key_two_records'] = Counter(r['tier'] for r in same_key)
    # union of work pairs, survivor per component
    wadj = defaultdict(set)
    for wa, wb, _, _ in wpairs:
        wadj[wa].add(wb)
        wadj[wb].add(wa)
    wmerge, seen = {}, set()
    for w in sorted(wadj, key=lambda w: int(w[2:])):
        if w in seen:
            continue
        todo, cc = [w], set()
        while todo:
            x = todo.pop()
            if x not in cc:
                cc.add(x)
                todo += wadj[x] - cc
        seen |= cc
        surv = min(cc, key=work_rank)
        for x in cc - {surv}:
            wmerge[x] = surv
    R['work_components_over_two'] = sum(1 for _ in [])
    wm = {}
    for x in wmerge:
        wm.setdefault(wmerge[x], []).append(x)
    R['work_components_over_two'] = sum(1 for v in wm.values() if len(v) > 1)

    # members of the works (year) for the detach step
    wkeys = set(wmerge) | set(wmerge.values())
    wmem = defaultdict(set)
    q = ','.join('?' * 500)
    wl = sorted(wkeys)
    for i in range(0, len(wl), 500):
        chunk = wl[i:i + 500]
        for k, m in con.execute(f"SELECT key, member FROM members WHERE key IN ({','.join('?' * len(chunk))})", chunk):
            wmem[k].add(m)
    con.close()

    # ---- proposal
    ops = []
    rowby = {}
    for r in strict:
        rowby[r['a']] = r
        rowby[r['b']] = r
    for x in sorted(pmerge, key=lambda k: int(k[2:])):
        r = rowby[x]
        s = pmerge[x]
        ops.append(dict(event='merge', key=x, into=s, decided_by='rule', basis=(
            f"one person, two records of one doctorate ({args.out.name}, strict: {r['why']}): {people[x]['label']} and "
            f"{people[s]['label']}: full names agree (bearers {r['bearers']}); theses {r['wa']} ({r['wa_src']}, {r['wa_year']}) "
            f"and {r['wb']} ({r['wb_src']}, {r['wb_year']}) awarded by {r['inst_label']}"
            + (f"; shared supervisor {r['shared_sup']}" if r['shared_sup'] else '')
            + (f"; title words {r['title_shared']}" if r['title_shared'] else ''))[:900]))
    for x in sorted(wmerge, key=lambda k: int(k[2:])):
        s = wmerge[x]
        X, S = works[x], works[s]
        ops.append(dict(event='merge', key=x, into=s, decided_by='rule', basis=(
            f"one doctorate on two thesis records ({args.out.name}): {x} ({X['src']}, {X['year']}) into {s} "
            f"({S['src']}, {S['year']}), the deposited title kept as the label; same author, same awarding institution, "
            f"years {abs((X['year'] or 0) - (S['year'] or 0))} apart")[:900]))
        extra = {}
        if fold(X['label']) and fold(X['label']) != fold(S['label']):
            extra['members'] = [f"variant-title:{X['label'][:400]}"]
        if extra:
            ops.append(dict(event='attach', key=s, decided_by='rule', basis=f'title of the merged record {x} ({X["src"]}) kept as a variant', **extra))
        xy = {m for m in wmem.get(x, ()) if m.startswith('year:')}
        sy = {m for m in wmem.get(s, ()) if m.startswith('year:')}
        drop = sorted(xy - sy) if sy else []
        if drop:
            ops.append(dict(event='detach', key=s, members=drop, decided_by='rule',
                            basis=f'year of the merged record {x} ({X["src"]}) set aside; the deposited record {s} gives {sorted(sy)}'))
    proposal = dict(basis=f'one person, two records of one doctorate ({args.out.name}, strict tier; ARCHITECTURE.md §8): '
                          'full-name agreement, the same awarding institution, degree years within '
                          f'{W} ({W + 1} for one record from each source with a shared supervisor or agreeing titles), and a shared '
                          'supervisor, or an uncommon name with no supervisor contradiction (two records from one source '
                          'also need agreeing titles); '
                          'the two thesis records merged into the deposited one',
                    decided_by='rule', ops=ops)
    R['person_merges'] = len(pmerge)
    R['work_merges'] = len(wmerge)
    R['ops'] = Counter(o['event'] for o in ops)
    if not args.no_validate:
        events, _ = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(events)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys()) if rows else []
    for name, sel in (('strict-tier.csv.gz', 'strict'), ('review-tier.csv.gz', 'review'), ('none-tier.csv.gz', 'none')):
        with gzip.open(out / name, 'wt', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols + (['into'] if sel == 'strict' else []), extrasaction='ignore')
            w.writeheader()
            for r in rows:
                if r['tier'] == sel:
                    w.writerow(dict(r, into=pmerge.get(r['a']) or pmerge.get(r['b']) or ''))
    with gzip.open(out / 'one-key-two-records.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(same_key[0].keys()) if same_key else ['person'])
        w.writeheader()
        w.writerows(same_key)
    (out / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=0) + '\n')
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sorted(R.items())}
    rep['year_window'] = W
    (out / 'run-report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list) + '\n')
    print(json.dumps(rep, indent=1, default=list))


if __name__ == '__main__':
    main()
