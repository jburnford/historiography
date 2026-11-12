"""Two family names and changed family names: duplicate keys and alternate printed forms (2026-11-12; ARCHITECTURE.md
section 8, class 37). Writes a proposal and tables; never applies.

Owner (2026-11-12): "do your best to solve the two family name issue; divorce could be another issue like Martha
Smith at USask". Standard of caution: the nickname ruling of the same day (no loose name forms). Standing rulings: no
false matches, but no conservatism where only one possible match exists; a printed second given name that disagrees
excludes; dates must fit; topic may support, never exclude; nothing is inferred about a person from a name; the
current name is the label and an earlier name is never a label or alias.

Record linkage. Name-form compatibility (scripts/name_forms.py) only makes a candidate pair; evidence decides.
- **Candidate pairs** of live person keys:
  - structural: one key's name with a family name dropped is the other's name (name_forms.relation: drops-second-family
    'Chust Calero, Manuel' / 'Manuel Chust'; drops-first-family 'Souza Santos' / 'Santos'; hyphen-part-dropped
    'Smith-Norris' / 'Smith'), given names agreeing in full (no short forms) and no written given name on the short
    side that the long side lacks; plus same-words pairs (one name printed without a comma and read with the wrong
    family: 'Díaz del Castillo, Bernal' / 'Bernal Díaz del Castillo');
  - stated: a form the key's own identifier records state (an LC heading or 400 cross-reference of an authority on
    the key or tied to it by evidence, data/graph/lc-authority-ties.csv.gz; an ORCID record's name; the AHA
    dissertation record's name and the AHA directory name; key-log aliases) is another key's name.
- **Stated tie** (the strongest evidence): one key's stated forms include the other key's name.
- **Clash** (pair refused, tier C): scripts/propose_person_dup_merges.clash (different LC, Wikidata, ISNI or IdRef;
  birth or death years apart; activity before adulthood or after death); a `not-same:` mark; an outside-review
  'different' verdict.
- **Facts** (propose_person_dup_merges.positive: shared work, shared title, the same OpenAlex author with one ORCID,
  a shared co-author, the same institution in an overlapping period), and `phd-school`: the AHA dissertation record
  of one key and the AHA directory PhD school of the other name the same school, PhD year before the directory.
- **Short-form contest**: other live keys (outside the pair) and LC authorities (on neither key and not stated for
  them) bearing the short form, whose dates let them be the person. Common short forms ('Manuel Santos', 'Martha
  Smith') are the danger.
- **Tiers**: A (merge): a stated tie, no clash, PhD years within two, and either an uncontested short form or a fact;
  or no stated tie and the fact combination that met >=99.5% precision on gold (report.json `gold`), uncontested.
  B (review, with the evidence): anything else without a clash. C: a clash.

Gold (report.json `gold`): positives are stated-tie pairs whose short form is uncontested (the facts are measured on
them with the stated tie hidden); negatives are pairs with a family-name relation whose keys hold different LC
authorities or Wikidata items (proven different people), and the proven-namesake pairs of
data/identifiers/person-dup-merges-2026-11-12/gold-negatives.csv (`masked-namesake`), with identifiers and life
years masked.

Outputs (data/identifiers/name-form-merges-2026-11-12/): proposal.json (merge ops, decided_by rule, dry-run
validated), tier-b-review.csv, rejected.csv.gz, report.json, hand-check.csv; data/graph/name-form-ties.csv.gz
((key, alternate printed form) pairs with their source: candidate generation for the works linkers only).

    python3 scripts/name_form_ties.py pairs        # candidate pairs, evidence, tiers, proposal, ties table
    python3 scripts/name_form_ties.py works        # works printed under a tied form: candidates and simulated links
"""
import argparse
import csv
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
import name_forms as N  # noqa: E402
from link_cited_work_authors import forms, heading_dates  # noqa: E402

ROOT = I.ROOT
G = ROOT / 'build/graph'
IDS = ROOT / 'data/identifiers'
OUT = IDS / 'name-form-merges-2026-11-12'
TIES = ROOT / 'data/graph/name-form-ties.csv.gz'
CACHE = ROOT / 'build/keylog-state.sqlite'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
LC_TIES = ROOT / 'data/graph/lc-authority-ties.csv.gz'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
AHA_DIR = ROOT / 'data/field-research/aha-historians-2026-10-29/historians.csv'
ORCID_FILES = [ROOT / 'data/orcid-2026-09-21/journal-orcids-enriched.csv',
               ROOT / 'data/orcid-2026-09-21/historians-orcid-enriched.csv']
DISS = ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'
GOLD_NEG = IDS / 'person-dup-merges-2026-11-12/gold-negatives.csv'
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/nameforms')
PUBLIC = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'atlas', 'ol')
TIE_RELATIONS = (N.DROPS_SECOND, N.DROPS_FIRST, N.HYPHEN_DROPPED, N.MIDDLE_AS_FAMILY, N.SUFFIX_DROPPED, 'family-changed')


def db_connect():
    db = duckdb.connect()
    db.execute(f"SET memory_limit='3GB'; SET threads=3; SET temp_directory='{SCRATCH}/duck'")
    return db


# ------------------------------------------------------------------ people and their stated forms

def load_people():
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    people = {}
    for k, l, res, a, al in con.execute("""SELECT key, label, resolution, anchors, aliases FROM keys WHERE type = 'person'
            AND status NOT IN ('merged', 'split', 'withdrawn', 'retyped')"""):
        people[k] = dict(label=l or '', resolution=res, anchors=json.loads(a or '[]'), aliases=json.loads(al or '[]'))
    notsame = defaultdict(set)
    for k, m in con.execute("SELECT key, member FROM members WHERE member >= 'not-same:' AND member < 'not-same;'"):
        notsame[k].add(m[len('not-same:'):])
    seq = int(dict(con.execute('SELECT k, v FROM meta').fetchall())['seq'])
    con.close()
    return people, notsame, seq


def form_relation(label, form):
    """How a stated form relates to the key's label: a name_forms relation (with 'long' = 'label' or 'form'),
    'family-changed' (given names agree in full, the families share nothing), 'same' or None (no tie form)."""
    if not form or N.same_form(label, form):
        return 'same', None
    rs = N.relation(label, form, middle=True)
    rs = [r for r in rs if r.relation != N.SAME_WORDS]
    if rs:
        r = rs[0]
        return r.relation, ('label' if r.long == label else 'form')
    if N.relation(label, form) and N.relation(label, form)[0].relation == N.SAME_WORDS:
        return 'same', None
    sl, sf = N.structure(label), N.structure(form)
    fams_l = {p for s in sl for p in s.parts}
    fams_f = {p for s in sf for p in s.parts}
    if sl and sf and not (fams_l & fams_f) and any(N.given_agree(a.given, b.given) and N.short_given_ok(b.given, a.given)
                                                   and N.short_given_ok(a.given, b.given) for a in sl for b in sf):
        if any(N.spelling_variant(a.family, b.family) for a in sl for b in sf):
            return N.FAMILY_SPELLING, None
        return 'family-changed', None
    return None, None


def stated_forms(db, people):
    """key -> [(form, source, source_id)] from the key's own identifier records."""
    out = defaultdict(list)
    # LC: anchored authorities and authorities tied by evidence (class 34)
    lc_of = defaultdict(set)
    for k, p in people.items():
        for a in p['anchors']:
            if a.startswith('lcnaf:'):
                lc_of[a[6:]].add((k, 'lc'))
    if LC_TIES.exists():
        with gzip.open(LC_TIES, 'rt', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['person'] in people:
                    lc_of[r['lcnaf']].add((r['person'], 'lc-tied'))
    db.execute('CREATE OR REPLACE TEMP TABLE wantlc(lcid VARCHAR)')
    db.executemany('INSERT INTO wantlc VALUES (?)', [(x,) for x in lc_of])
    lc_rec = {}
    for lcid, label, variants, b, d in db.execute(f"""SELECT n.lcid, n.label, n.variants, n.birth, n.death
            FROM '{LC_NAMES}' n JOIN wantlc USING (lcid)""").fetchall():
        lc_rec[lcid] = (label, list(variants or []), b, d)
        for k, how in lc_of[lcid]:
            out[k].append((label, f'{how}-heading', lcid))
            for v in variants or []:
                out[k].append((v, f'{how}-400', lcid))
    # ORCID record names (given + family as the record prints them, and the credit name)
    orc_key = defaultdict(set)
    for k, p in people.items():
        for a in p['anchors']:
            if a.startswith('orcid:'):
                orc_key[a[6:]].add(k)
    for fn in ORCID_FILES:
        if not fn.exists():
            continue
        with open(fn, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                ks = orc_key.get(r.get('orcid', ''))
                if not ks:
                    continue
                giv = r.get('given') or r.get('orcid_given') or ''
                fam = r.get('family') or r.get('orcid_family') or ''
                cred = r.get('credit') or r.get('orcid_credit') or ''
                for k in ks:
                    if giv and fam:
                        out[k].append((f'{fam}, {giv}', 'orcid-name', r['orcid']))
                    if cred:
                        out[k].append((cred, 'orcid-credit', r['orcid']))
                    for o in (r.get('other_names') or '').split('|'):
                        if o.strip():
                            out[k].append((o.strip(), 'orcid-other', r['orcid']))
    # the public ORCID person record fetched for keys on candidate pairs (cmd_orcid_fetch): name, credit, other names
    for o, r in orcid_records().items():
        for k in orc_key.get(o, ()):
            if r.get('given') and r.get('family'):
                out[k].append((f"{r['family']}, {r['given']}", 'orcid-record', o))
            if r.get('credit'):
                out[k].append((r['credit'], 'orcid-record-credit', o))
            for x in r.get('other') or []:
                out[k].append((x, 'orcid-record-other', o))
    # AHA dissertation record and AHA directory
    aha_phd, aha_dir = {}, {}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        aha_phd[r['id']] = r
    with open(AHA_DIR, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            aha_dir[r['token']] = r
    for k, p in people.items():
        for a in p['anchors']:
            if a.startswith('aha-phd:') and a[8:] in aha_phd:
                out[k].append((aha_phd[a[8:]]['dissertator'], 'aha-dissertation', a[8:]))
            elif a.startswith('aha:') and a[4:] in aha_dir:
                out[k].append((aha_dir[a[4:]]['name'], 'aha-directory', a[4:]))
        for al in p['aliases']:
            out[k].append((al, 'keylog-alias', ''))
    return out, lc_rec, aha_phd, aha_dir


# ------------------------------------------------------------------ candidates

def family_index(people):
    idx = defaultdict(list)
    for k, p in people.items():
        for f, _, g in forms(p['label']):
            idx[f].append((k, g))
    return idx


def structural_pairs(people, idx):
    pairs = {}
    words_idx = defaultdict(list)
    for k, p in people.items():
        lab = p['label']
        for f in N.shorter_forms(lab):
            for k2, g2 in idx.get(f.family, ()):
                if k2 == k or (k, k2) in pairs or not N.given_agree(f.given, g2):
                    continue
                rs = [r for r in N.relation(lab, people[k2]['label']) if r.long == lab]
                if rs:
                    pairs[(k, k2)] = rs[0]
        w = N.words(lab)
        if len(w) >= 3:
            words_idx[tuple(w)].append(k)
    for w, ks in words_idx.items():
        for a, b in combinations(ks, 2):
            if (a, b) in pairs or (b, a) in pairs:
                continue
            rs = N.relation(people[a]['label'], people[b]['label'])
            if rs and rs[0].relation == N.SAME_WORDS:
                pairs[(a, b)] = rs[0]
    return pairs


def stated_pairs(people, idx, stated):
    """(key, other) where a stated form of key is other's name -> [(form, source, source_id, relation)]"""
    out = defaultdict(list)
    for k, lst in stated.items():
        lab = people[k]['label']
        for form, src, sid in lst:
            rel, _ = form_relation(lab, form)
            if rel in (None, 'same'):
                continue
            for f, _, g in forms(form):
                for k2, g2 in idx.get(f, ()):
                    if k2 != k and N.same_form(form, people[k2]['label']) and \
                            N.short_given_ok(g2, g) and N.short_given_ok(g, g2):
                        out[(k, k2)].append((form, src, sid, rel))
    return out


# ------------------------------------------------------------------ the pass

def cmd_pairs(args):
    import propose_person_dup_merges as PD
    SCRATCH.mkdir(parents=True, exist_ok=True)
    R = Counter()
    db = db_connect()
    people, notsame, seq = load_people()
    R['keylog_seq'] = seq
    R['live_person_keys'] = len(people)
    idx = family_index(people)
    stated, lc_rec, aha_phd, aha_dir = stated_forms(db, people)
    R['keys_with_stated_forms'] = len(stated)

    # ---- class sizes: structure of every live key's name
    kinds = Counter()
    for k, p in people.items():
        sts = N.structure(p['label'])
        kinds[(sts[0].reading if sts else 'none', sts[0].kind if sts else 'none')] += 1
        if len(sts) > 1:
            kinds[('plain-double-reading', sts[1].kind)] += 1
    R['label_structure'] = {f'{a}|{b}': n for (a, b), n in kinds.items()}

    # ---- (key, alternate printed form) ties from the key's own records
    tie_rows = []
    for k, lst in stated.items():
        lab = people[k]['label']
        seen = set()
        for form, src, sid in lst:
            rel, long_ = form_relation(lab, form)
            if rel in TIE_RELATIONS:
                fk = (form.strip().rstrip('.'), src.split('-')[0])
                if fk in seen:
                    continue
                seen.add(fk)
                tie_rows.append(dict(key=k, label=lab, form=form, relation=rel, long=long_ or '', source=src,
                                     source_id=sid))
    R['stated_alternate_forms'] = len(tie_rows)
    R['stated_alternate_forms_by_relation'] = Counter(r['relation'] for r in tie_rows)
    R['stated_alternate_forms_by_source'] = Counter(r['source'] for r in tie_rows)
    R['keys_with_stated_alternate_form'] = len({r['key'] for r in tie_rows})

    # ---- candidate pairs
    sp = structural_pairs(people, idx)
    st = stated_pairs(people, idx, stated)
    R['structural_pairs'] = len(sp)
    R['structural_pairs_by_relation'] = Counter(f'{r.relation}|{r.reading}' for r in sp.values())
    R['stated_pairs'] = len(st)
    pairs = {}
    for (a, b), r in sp.items():
        pairs[frozenset((a, b))] = dict(rel=r, stated=[])
    for (a, b), lst in st.items():
        d = pairs.setdefault(frozenset((a, b)), dict(rel=None, stated=[]))
        d['stated'] += [(a,) + x for x in lst]
    R['candidate_pairs'] = len(pairs)
    R['candidate_keys'] = len({k for p in pairs for k in p})

    # ---- facts (propose_person_dup_merges machinery, read-only)
    need = {k for p in pairs for k in p}
    PD.load_common_titles(db)
    pd_people = {k: dict(label=p['label'], resolution=p['resolution'], anchors=p['anchors']) for k, p in people.items()}
    # gold negatives from the 11-12 dup-merge run (proven namesakes, masked)
    gneg = []
    with open(GOLD_NEG, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['set'] == 'masked-namesake' and r['a'] in people and r['b'] in people:
                gneg.append((r['a'], r['b']))
    random.seed(20261112)
    random.shuffle(gneg)
    gneg = gneg[:4000]
    need |= {k for p in gneg for k in p}
    F = PD.Facts(db, pd_people, need)
    verdicts = PD.review_verdicts()
    inst_cache = {}

    # PhD school (AHA dissertation record) and the directory's degree school
    def phd_schools(k):
        out = []
        for a in people[k]['anchors']:
            if a.startswith('aha-phd:') and a[8:] in aha_phd:
                r = aha_phd[a[8:]]
                out.append(('phd', r['department'], r.get('year')))
            elif a.startswith('aha:') and a[4:] in aha_dir:
                r = aha_dir[a[4:]]
                if r.get('degree_school'):
                    out.append(('dir', r['degree_school'], None))
        return out

    from key_review_credit_merges import agree as inst_agree

    def phd_school_fact(a, b):
        sa, sb = phd_schools(a), phd_schools(b)
        for x, y in ((sa, sb), (sb, sa)):
            for kind1, s1, y1 in x:
                for kind2, s2, y2 in y:
                    if {kind1, kind2} == {'phd', 'dir'} and s1 and s2:
                        dept = s1 if kind1 == 'phd' else s2
                        school = s2 if kind1 == 'phd' else s1
                        dept = re.sub(r'(?i),?\s*dept\.? of .*$', '', dept).replace('Univ.', 'University')
                        if inst_agree(dept, school) or inst_agree(school, dept):
                            return f'phd-school:{school}'
        return None

    # LC authorities bearing a short form (for the contest test)
    short_fams = set()
    for p, d in pairs.items():
        for k in p:
            for f, _, g in forms(people[k]['label']):
                short_fams.add(f)
    last = {f.split()[-1] for f in short_fams if f}
    db.execute('CREATE OR REPLACE TEMP TABLE lastw(w VARCHAR)')
    db.executemany('INSERT INTO lastw VALUES (?)', [(w,) for w in last])
    lc_by_family = defaultdict(list)
    for lcid, label, lb_, ld_ in db.execute(f"""SELECT lcid, label, birth, death FROM (SELECT lcid, label, deprecated, birth, death,
            regexp_extract(lower(strip_accents(split_part(label, ',', 1))), '([a-z]+)[^a-z]*$', 1) AS w
            FROM read_parquet('{LC_NAMES}')) WHERE NOT coalesce(deprecated, false) AND w IN (SELECT w FROM lastw)""").fetchall():
        hb, hd = heading_dates(label)
        yb = int(lb_[:4]) if lb_ and lb_[:4].isdigit() else hb
        yd = int(ld_[:4]) if ld_ and ld_[:4].isdigit() else hd
        for fam, _, g in forms(label):
            if fam in short_fams:
                lc_by_family[fam].append((lcid, g, yb, yd))

    def window(f):
        ys = [y for y, kind in f['years'] if kind != 'book'] + [x for _, _, lo, hi, src in f['affs'] if src != 'lc_373'
                                                                  for x in (lo, hi) if x]
        ys = ys or [y for y, _ in f['years']]
        return (min(ys), max(ys)) if ys else None

    def could_be(life, win):
        if not win:
            return True
        b, d = life
        return not ((b and b + 16 > win[1]) or (d and d + 3 < win[0]))

    def lcids(k):
        return {a[6:] for a in people[k]['anchors'] if a.startswith('lcnaf:')}

    def contest(short_key, pair, fa, fb, own_lc):
        """other live keys and LC authorities bearing the short key's name that could be the person"""
        others, lcs = set(), set()
        wins = [window(fa), window(fb)]
        for fam, _, g in forms(people[short_key]['label']):
            for k2, g2 in idx.get(fam, ()):
                if k2 not in pair and N.given_agree(g, g2) and any(could_be(F.life.get(k2, (None, None)), w) for w in wins):
                    others.add(k2)
            for lcid, g2, lb, ld in lc_by_family.get(fam, ()):
                if lcid not in own_lc and N.given_agree(g, g2) and any(could_be((lb, ld), w) for w in wins):
                    lcs.add(lcid)
        return others, lcs

    def judge(a, b, d, fa, fb, mask_stated=False, use_marks=True, mask_ids=False):
        la, lb = people[a]['label'], people[b]['label']
        ev = dict(a=a, b=b, label_a=la, label_b=lb)
        rel = d['rel']
        if rel is not None:
            ev['relation'] = rel.relation
            ev['reading'] = rel.reading
            long_key = a if rel.long == la else b
        else:
            x = d['stated'][0]
            ev['relation'] = x[4]
            ev['reading'] = 'stated'
            form_rel, long_side = form_relation(people[x[0]]['label'], x[1])
            long_key = x[0] if long_side == 'label' else (b if x[0] == a else a)
        short_key = b if long_key == a else a
        ev['long'], ev['short'] = long_key, short_key
        stated_tie = [] if mask_stated else sorted({f'{s[2]}:{s[3]}' for s in d['stated']})
        ev['stated'] = stated_tie
        if use_marks and (b in notsame.get(a, ()) or a in notsame.get(b, ())):
            return 'C', 'not-same-recorded', ev
        v = verdicts.get(frozenset((a, b))) if use_marks else None
        if v and v.startswith('different'):
            return 'C', f'outside-review-{v}', ev
        c = PD.clash(fa, fb) or lifetime_clash(fa, fb)
        if c:
            return 'C', c, ev
        pos = PD.positive(fa, fb, inst_cache)
        ps = phd_school_fact(a, b)
        if ps:
            pos.append(ps)
        ev['facts'] = pos
        own_lc = lcids(a) | lcids(b) | {s[3] for s in d['stated'] if s[2].startswith('lc')}
        if mask_stated:
            own_lc = set(fa['ids'].get('lcnaf', ())) | set(fb['ids'].get('lcnaf', ()))
        elif mask_ids:          # the keys' anchors hidden: only the stated authority is known to be the person's
            own_lc = {s[3] for s in d['stated'] if s[2].startswith('lc')}
        # the contest is measured on the form that joins the pair: for a stated tie, the other key's name that the
        # stated form matched ('Smith-Norris, Martha', rare, not the holder's current 'Smith, Martha'); otherwise the
        # short form
        if stated_tie:
            best = None
            for s_ in d['stated']:
                matched = b if s_[0] == a else a
                o_, l_ = contest(matched, frozenset((a, b)), fa, fb, own_lc)
                if best is None or len(o_) + len(l_) < len(best[0]) + len(best[1]):
                    best = (o_, l_)
            others, lcs = best
        else:
            others, lcs = contest(short_key, frozenset((a, b)), fa, fb, own_lc)
        ev['other_keys'] = sorted(others)[:5]
        ev['other_lc'] = sorted(lcs)[:5]
        ev['n_contest'] = len(others) + len(lcs)
        ya = [y for y, _ in fa['years']]
        yb = [y for y, _ in fb['years']]
        la_y, sh_y = (ya, yb) if long_key == a else (yb, ya)
        ev['direction'] = N.direction(la_y, sh_y) or ''
        why = []
        oa, ob = fa['ids'].get('orcid', set()), fb['ids'].get('orcid', set())
        if oa and ob and not (oa & ob):
            why.append('two-orcids')
        if fa['phd'] and fb['phd'] and min(abs(x - y) for x in fa['phd'] for y in fb['phd']) > 2:
            why.append('two-phd-years')
        if v:
            why.append(f'outside-review-{v}')
        kinds = {p.split(':')[0] for p in pos}
        if ev['relation'] == N.FAMILY_SPELLING:
            why.append('family-spelling-out-of-scope')      # one name spelled two ways: the general folding rules
        if stated_tie:
            if ev['n_contest'] and not pos:
                why.append('stated-tie-but-short-form-contested-no-fact')
        else:
            # facts without a stated tie: admitted only for a fact kind that met >=99.5% on gold (FACTS_ALONE), on an
            # uncontested short form; none did on 2026-11-12 (two fact kinds together included), so these are B
            if not pos:
                why.append('no-stated-tie-no-fact')
            elif ev['n_contest']:
                why.append('no-stated-tie-contested')
            elif not (kinds & FACTS_ALONE[0]):
                why.append('no-stated-tie-facts-below-measured-bar')
        bad_orcid = orcid_name_disagrees(a, b)
        if bad_orcid:
            why.append(f'orcid-record-name-disagrees:{bad_orcid}')
        if why:
            return 'B', ';'.join(why), ev
        return 'A', ('stated:' + '+'.join(sorted({s.split(':')[0] for s in stated_tie})) if stated_tie else 'facts') + \
            (';facts:' + '+'.join(sorted(kinds)) if kinds else ''), ev

    def facts(k, mask=False):
        return F.of(k, people[k]['anchors'], mask)

    orc_rec = orcid_records()

    def orcid_name_disagrees(a, b):
        """An ORCID on either key whose public record names someone neither key's name fits (hand check 2026-11-12:
        'Carmen Castañeda' carried the ORCID of Carmen A. Morales, a Guatemalan dentist, through an OpenAlex profile):
        the merge would move another person's identifier. -> the ORCID, or None."""
        labs = [people[a]['label'], people[b]['label']]
        for k in (a, b):
            for x in people[k]['anchors']:
                if not x.startswith('orcid:') or x[6:] not in orc_rec:
                    continue
                r = orc_rec[x[6:]]
                nm = ([f"{r['family']}, {r['given']}"] if r.get('family') and r.get('given') else []) + \
                    ([r['credit']] if r.get('credit') else []) + list(r.get('other') or [])
                if nm and not any(N.same_form(n, l) or N.relation(n, l, middle=True) for n in nm for l in labs):
                    return x[6:]
        return None

    # ---- gold: measure each fact on positives (stated-tie pairs, uncontested) and negatives (masked)
    gold = Counter()
    fact_pos, fact_neg = Counter(), Counter()
    pos_pairs, neg_pairs = [], []
    for p, d in pairs.items():
        a, b = sorted(p)
        if d['stated']:
            pos_pairs.append((a, b, d))
        else:
            ida = {s: v for s, v in facts(a)['ids'].items() if s in ('lcnaf', 'wd')}
            idb = {s: v for s, v in facts(b)['ids'].items() if s in ('lcnaf', 'wd')}
            if any(ida.get(s) and idb.get(s) and not (ida[s] & idb[s]) for s in ('lcnaf', 'wd')):
                neg_pairs.append((a, b, d, 'cross-form-lc-or-wd-differs'))
    stated_neg = []
    for p, d in pairs.items():
        if d['stated']:
            a, b = sorted(p)
            ida, idb = facts(a)['ids'].get('lcnaf', set()), facts(b)['ids'].get('lcnaf', set())
            if ida and idb and not (ida & idb):
                stated_neg.append((a, b, d))
    for a, b, d in stated_neg:
        fa, fb = facts(a, mask=True), facts(b, mask=True)
        t, w, ev = judge(a, b, d, fa, fb, use_marks=False, mask_ids=True)
        gold[f'neg_stated_lc_differs_masked_{t}'] += 1
        if t == 'A':
            gold.setdefault('neg_stated_lc_differs_masked_A_pairs', [])
            gold['neg_stated_lc_differs_masked_A_pairs'] = gold['neg_stated_lc_differs_masked_A_pairs'] + [f'{a}~{b}']
        gold['neg_stated_lc_differs_masked'] += 1
    for a, b in gneg:
        neg_pairs.append((a, b, dict(rel=N.Relation('same-form-namesake', people[a]['label'], people[b]['label'], '', None,
                                                    'gold'), stated=[]), 'masked-namesake'))
    FACTS_ALONE[0] = set()      # first pass: no fact admitted alone
    gp_rows = []
    for a, b, d in pos_pairs:
        t, w, ev = judge(a, b, d, facts(a), facts(b))
        if t == 'C' or ev['n_contest']:
            continue
        kinds = {x.split(':')[0] for x in ev['facts']}
        gold['positives'] += 1
        for kk in kinds:
            fact_pos[kk] += 1
        fact_pos['any'] += bool(kinds)
        fact_pos['two-kinds'] += len(kinds) >= 2
        gp_rows.append((a, b, sorted(kinds)))
    for a, b, d, src in neg_pairs:
        fa, fb = facts(a, mask=True), facts(b, mask=True)
        t, w, ev = judge(a, b, d, fa, fb, mask_stated=True, use_marks=False)
        if t == 'C':
            gold[f'neg_{src}_clash_even_masked'] += 1
            continue
        kinds = {x.split(':')[0] for x in ev.get('facts', [])}
        gold[f'negatives_{src}'] += 1
        gold['negatives'] += 1
        for kk in kinds:
            fact_neg[kk] += 1
            fact_neg[f'{kk}|{src}'] += 1
        fact_neg['any'] += bool(kinds)
        fact_neg['two-kinds'] += len(kinds) >= 2
        if kinds and not ev['n_contest']:
            fact_neg['any-uncontested'] += 1
            for kk in kinds:
                fact_neg[f'{kk}-uncontested'] += 1
    npos, nneg = gold['positives'], gold['negatives']
    measure = {}
    for kk in sorted(set(fact_pos) | {x for x in fact_neg if '|' not in x}):
        m = fact_pos.get(kk, 0) / npos if npos else None
        u = fact_neg.get(kk, 0) / nneg if nneg else None
        measure[kk] = dict(pos=fact_pos.get(kk, 0), neg=fact_neg.get(kk, 0), m=round(m, 4) if m is not None else None,
                           u=round(u, 5) if u is not None else None,
                           u_upper95=round((fact_neg.get(kk, 0) + 3) / nneg, 5) if nneg else None)
    # a fact may decide alone (no stated tie, uncontested short form) only if no negative fired it and its upper
    # bound keeps precision >= 99.5% at the observed share of stated pairs among candidates (prior)
    prior = len(pos_pairs) / max(1, len(pairs))
    alone = set()
    for kk, mm in measure.items():
        if kk in ('any', 'two-kinds', 'any-uncontested') or kk.endswith('-uncontested'):
            continue
        if mm['m'] and mm['neg'] == 0 and nneg:
            prec = prior * mm['m'] / (prior * mm['m'] + (1 - prior) * mm['u_upper95'])
            mm['precision_lower_at_prior'] = round(prec, 4)
            if prec >= 0.995:
                alone.add(kk)
        elif mm['m'] is not None and nneg:
            prec = prior * mm['m'] / (prior * mm['m'] + (1 - prior) * max(mm['u'], 1e-9))
            mm['precision_at_prior'] = round(prec, 4)
    FACTS_ALONE[0] = alone
    gold.update({'prior_stated_share': round(prior, 4)})
    R['gold'] = dict(gold)
    R['gold_fact_measure'] = measure
    R['facts_admitted_alone'] = sorted(alone)

    # ---- judge every candidate pair
    rows = []
    for p, d in pairs.items():
        a, b = sorted(p, key=lambda k: int(k[2:]))
        t, w, ev = judge(a, b, d, facts(a), facts(b))
        ev.update(tier=t, why=w)
        rows.append(ev)
    R['tiers'] = Counter(r['tier'] for r in rows)
    R['tiers_by_relation'] = Counter(f"{r['tier']}|{r.get('relation')}" for r in rows)
    R['why_B'] = Counter(x for r in rows if r['tier'] == 'B' for x in r['why'].split(';'))
    R['why_C'] = Counter(r['why'] for r in rows if r['tier'] == 'C')
    R['why_A'] = Counter(r['why'] for r in rows if r['tier'] == 'A')

    # ---- clusters of A pairs; refuse clusters that bring clashing ids or two names of the same family together
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
    from merge_guard import SINGLE_KEY_CHECKS, blocked_keys
    import keylog_snapshot as KS
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    state = KS.read_state()
    blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
    ops, merges = [], []
    fam_count = lambda k: len({a.split(':')[0] for a in people[k]['anchors'] if a.split(':')[0] in PUBLIC})  # noqa: E731
    for cl in clusters.values():
        fs = {k: facts(k) for k in cl}
        bad = None
        for s_ in PD.CLASH + ('orcid',):
            vals = {v for k in cl for v in fs[k]['ids'].get(s_, ())}
            if len(vals) > 1:
                bad = f'cluster-{s_}-differs'
        births = {fs[k]['life'][0] for k in cl if fs[k]['life'][0]}
        if births and max(births) - min(births) > 1:
            bad = 'cluster-birth-differs'
        if not bad and cl & blocked:
            bad = 'merge-guard'
        if not bad:
            for x, y in combinations(sorted(cl), 2):
                if not (N.same_form(people[x]['label'], people[y]['label']) or N.relation(people[x]['label'], people[y]['label'])
                        or any(frozenset((x, y)) == frozenset((r['a'], r['b'])) for r in rows if r['tier'] == 'A')):
                    bad = 'cluster-names-unrelated'
                    break
        if bad:
            for r in rows:
                if r['tier'] == 'A' and r['a'] in cl:
                    r.update(tier='B', why=bad)
            R['clusters_back_to_B'] += 1
            continue
        into = sorted(cl, key=lambda k: (-fam_count(k), -len(F.works.get(k, ())), int(k[2:])))[0]
        for k in sorted(cl):
            if k == into:
                continue
            ev = next((r for r in rows if r['tier'] == 'A' and k in (r['a'], r['b']) and {r['a'], r['b']} <= cl), None)
            ev_txt = (f"{ev['relation']}; stated: {', '.join(ev['stated']) or 'none'}; facts: "
                      f"{'; '.join(ev['facts']) or 'none'}; short form borne by {ev['n_contest']} other keys or LC "
                      f"authorities") if ev else ''
            basis = (f"one person under two family-name forms ({OUT.name}, tier A): {people[k]['label']} and "
                     f"{people[into]['label']}: {ev_txt}")[:900]
            ops.append(dict(event='merge', key=k, into=into, decided_by='rule', basis=basis))
            merges.append(dict(key=k, into=into, label=people[k]['label'], into_label=people[into]['label'],
                               relation=ev['relation'] if ev else '', stated=ev['stated'] if ev else [],
                               facts=ev['facts'] if ev else [], n_contest=ev['n_contest'] if ev else None,
                               direction=ev.get('direction') if ev else '',
                               label_note=label_note(people, k, into, ev, stated)))
    R['tierA_merges'] = len(ops)
    R['tiers_final'] = Counter(r['tier'] for r in rows)
    R['tiers_final_by_relation'] = Counter(f"{r['tier']}|{r.get('relation')}" for r in rows)
    R['merges_with_label_note'] = sum(1 for m in merges if m['label_note'])

    # ---- outputs
    OUT.mkdir(parents=True, exist_ok=True)
    proposal = dict(basis=f'one person under two family-name forms ({OUT.name}): a stated tie (LC 400 or heading, ORCID '
                          'record, AHA record) with an uncontested short form or a fact, or measured facts; no '
                          'identifier or date clash', decided_by='rule', ops=ops)
    events, _ = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
    R['dry_run_events'] = len(events)
    (OUT / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False) + '\n')
    (OUT / 'merges.json').write_text(json.dumps(merges, ensure_ascii=False, indent=1) + '\n')
    cols = ['tier', 'why', 'relation', 'reading', 'a', 'label_a', 'b', 'label_b', 'long', 'stated', 'facts', 'n_contest',
            'other_keys', 'other_lc', 'direction']
    for name, sel in (('tier-a-pairs.csv', lambda r: r['tier'] == 'A'), ('tier-b-review.csv', lambda r: r['tier'] == 'B'),
                      ('rejected.csv.gz', lambda r: r['tier'] == 'C')):
        op = gzip.open if name.endswith('.gz') else open
        with op(OUT / name, 'wt', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for r in sorted((r for r in rows if sel(r)), key=lambda r: (r['why'], r['label_a'])):
                w.writerow([r.get('tier'), r.get('why'), r.get('relation'), r.get('reading'), r['a'], r['label_a'],
                            r['b'], r['label_b'], r.get('long'), ' '.join(r.get('stated', [])),
                            ' ; '.join(r.get('facts', [])), r.get('n_contest'), ' '.join(r.get('other_keys', [])),
                            ' '.join(r.get('other_lc', [])), r.get('direction')])
    # ties table: stated alternate forms of each key, and stated pairs left unmerged (B with a stated tie)
    merged_away = {o['key'] for o in ops}
    with gzip.open(TIES, 'wt', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['key', 'form', 'family', 'given', 'relation', 'long', 'source', 'source_id'])
        n = 0
        for t in sorted(tie_rows, key=lambda t: (int(t['key'][2:]), t['form'])):
            if t['key'] in merged_away:
                continue
            for s_ in N.structure(t['form'])[:1]:
                w.writerow([t['key'], t['form'], s_.family, ' '.join(s_.given), t['relation'], t['long'], t['source'],
                            t['source_id']])
                n += 1
        for r in rows:
            if r['tier'] == 'B' and r['stated']:
                for k, o in ((r['a'], r['b']), (r['b'], r['a'])):
                    s_ = N.structure(people[o]['label'])[:1]
                    if s_:
                        w.writerow([k, people[o]['label'], s_[0].family, ' '.join(s_[0].given), r['relation'],
                                    '', 'pair-stated-unmerged', o])
                        n += 1
        R['ties_rows'] = n
    with open(OUT / 'gold-positives.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['a', 'b', 'facts'])
        for a, b, k in gp_rows:
            w.writerow([a, b, ' '.join(k)])
    # probes
    PROBES = ('p-253598', 'p-6329', 'p-256246', 'p-18131', 'p-88959', 'p-71685', 'p-53033', 'p-179250')
    R['probes'] = {k: [dict(other=r['b'] if r['a'] == k else r['a'], tier=r['tier'], why=r['why'], relation=r.get('relation'),
                            stated=r.get('stated'), facts=r.get('facts'), n_contest=r.get('n_contest'))
                       for r in rows if k in (r['a'], r['b'])] for k in PROBES}
    R['probe_stated_forms'] = {k: [t for t in tie_rows if t['key'] == k] for k in PROBES}
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sorted(R.items())}
    (OUT / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('probes', 'probe_stated_forms')}, indent=1, default=list)[:6000])


FACTS_ALONE = [set()]


def lifetime_clash(fa, fb):
    """Dates must fit (hand check 2026-11-12: 'Sarah Morgan', a 1992 diary edition and a 1996 review, joined to the
    diarist Sarah Morgan Dawson, 1842-1909): when one key has life years, the other key's dated works must include at
    least one inside the adult life (birth + 15 to death + 3). PropDupMerges.clash reads only reviews and theses
    after death, because an edition can carry a late year; one posthumous item does not refuse a pair here, a key whose
    every dated work falls outside the life does."""
    for x, y in ((fa, fb), (fb, fa)):
        b, d = x['life']
        if not (b or d):
            continue
        ys = [v for v, _ in y['years'] if v]
        if ys and not any((not b or v >= b + 15) and (not d or v <= d + 3) for v in ys):
            return 'no-activity-in-lifetime'
    return None


def label_note(people, k, into, ev, stated):
    """The current name is the label (owner's rule): note when the survivor's label is the older form, read from the
    AHA directory (the current listing) or the later works (direction)."""
    lab_into, lab_k = people[into]['label'], people[k]['label']
    dir_names = [f for f, s, _ in stated.get(into, []) + stated.get(k, []) if s == 'aha-directory']
    if dir_names and any(N.same_form(d, lab_k) for d in dir_names) and not any(N.same_form(d, lab_into) for d in dir_names):
        return (f'the AHA directory (the current listing) prints {lab_k!r}, the merged-away key\'s name; the owner may '
                f'relabel {into} (no relabel op proposed: a shorter Hispanic form is not a change of name)')
    return ''


# ------------------------------------------------------------------ works under a tied form

def cmd_works(args):
    """Printed author positions whose name agrees with a tied alternate form of a key (data/graph/name-form-ties.csv.gz)
    but not with the key's label: (1) how many are uncredited and become candidates for the key; (2) how many the
    work-people rule linker would link with the tied forms added to its family index (the proposed change), simulated
    read-only by importing link_work_people (WPPeople, make_pos, L.features, rule_wp, guard's own-book check); (3) the
    change's error on a masked test: positions credited by an ORCID (to the tied key: should come back; to another key:
    must not move to the tied key) with the ORCID hidden. Writes report.json `works` and a scratch list; no linker
    output is written."""
    import link_work_people as W
    L = W.L
    S = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/scored')
    db = W.duck()
    db.execute("SET memory_limit='3GB'")
    people_c, _, _ = load_people()
    ties = defaultdict(list)
    n_ties = 0
    with gzip.open(TIES, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['key'] in people_c and r['relation'] in TIE_RELATIONS:
                for fam, form, g in forms(r['form']):
                    ties[fam].append((r['key'], tuple(g), form, r['relation'], r['source']))
                    n_ties += 1
    R = Counter()
    R['tie_forms_indexed'] = n_ties
    db.execute("CREATE OR REPLACE TEMP TABLE fams AS SELECT unnest(?) AS w", [sorted({f.split()[-1] for f in ties})])
    cols = """pid, tbl, role, source, work, pos, name, year, kind, title, orcid, oa_author, rors, insts, raw_aff, oa_work,
              inst_ror, credited, credited_how"""
    sel = f"""SELECT * FROM (SELECT {cols}, NULL::VARCHAR[] AS lc, NULL::INTEGER AS sb, NULL::INTEGER AS sd, false AS book
              FROM '{S}/positions.parquet' UNION ALL SELECT {cols}, lc, sb, sd, book FROM '{S}/positions-extra.parquet')
              WHERE regexp_extract(lower(strip_accents(name)), '([a-z]+)[^a-z]*$', 1) IN (SELECT w FROM fams)
                 OR regexp_extract(lower(strip_accents(split_part(name, ',', 1))), '([a-z]+)[^a-z]*$', 1) IN (SELECT w FROM fams)"""
    cur = db.execute(sel)
    names = [d[0] for d in cur.description]
    rows = [dict(zip(names, r)) for r in cur.fetchall()]
    dec = dict(((p, (st, k, d_, dk)) for p, st, k, d_, dk in db.execute(f"""SELECT pid, rule_state, rule_key, decision, key
              FROM '{S}/decided.parquet' WHERE pid IN (SELECT unnest(?))""", [[r['pid'] for r in rows]]).fetchall()))
    cand = []
    for r in rows:
        hit = {}
        for f, _, g in forms(r['name']):
            for k, tg, form, rel, src in ties.get(f, ()):
                if not N.given_agree(g, tg) or not N.short_given_ok(g, tg) and not N.short_given_ok(tg, g):
                    continue
                if any(kf == f2 and N.given_agree(g2, kg) for kf, _, kg in forms(people_c[k]['label'])
                       for f2, _, g2 in forms(r['name'])):
                    continue        # already name-compatible with the key's label: the linker saw this key
                hit[k] = (form, rel, src)
        for k, (form, rel, src) in hit.items():
            cand.append(dict(r, key=k, form=form, relation=rel, source_tie=src, dec=dec.get(r['pid'])))
    # works credited in the current graph (any evidence) to each tied key
    db.execute("CREATE OR REPLACE TEMP TABLE ck AS SELECT unnest(?) AS k", [sorted({c['key'] for c in cand})])
    credited = defaultdict(set)
    for k, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE "from" IN (SELECT k FROM ck)
              UNION SELECT "from", "to" FROM '{G}/edited.parquet' WHERE "from" IN (SELECT k FROM ck)""").fetchall():
        credited[k].add(w)
    R['positions_matching_a_tied_form'] = len({c['pid'] for c in cand})
    R['keys_with_matching_positions'] = len({c['key'] for c in cand})
    open_ = []
    for c in cand:
        st, k2, d_, dk = c['dec'] or ('', '', '', '')
        if c['work'] in credited[c['key']]:
            R['already_credited_to_the_tied_key'] += 1
        elif c['credited'] or st in ('exact', 'linked') or d_ in ('exact', 'link'):
            R['credited_to_another_key'] += 1
        else:
            open_.append(c)
    R['uncredited_candidate_positions'] = len({c['pid'] for c in open_})
    R['uncredited_candidate_works'] = len({c['work'] for c in open_})
    R['uncredited_candidate_keys'] = len({c['key'] for c in open_})
    R['uncredited_by_relation'] = Counter(c['relation'] for c in open_)
    R['uncredited_by_tie_source'] = Counter(c['source_tie'] for c in open_)
    R['uncredited_by_table'] = Counter(c['tbl'] for c in open_)
    # ---- simulate the linker with the tied forms in its index
    people = W.WPPeople(db)
    for fam, lst in ties.items():
        for k, g, form, rel, src in lst:
            if k in people.label:
                people.index[fam].append((k, form, g))
    needed = set()
    for c in cand:
        for f, _, g in forms(c['name'])[:1]:
            needed.add((f, g[0]))
    pop = L.population_counts(db, needed)
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'] = tuple(P['FACTS'])
    P['XDATE'] = tuple(P['XDATE'])
    L.PARAMS.update({k: v for k, v in P.items() if k in L.PARAMS})
    authors = defaultdict(set)
    db.execute("CREATE OR REPLACE TEMP TABLE cw AS SELECT unnest(?) AS w", [sorted({c['work'] for c in cand})])
    for k, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
              AND "to" IN (SELECT w FROM cw)""").fetchall():
        authors[w].add(k)

    def run(c, hide_orcid=False):
        p = W.make_pos(dict(c, orcid='' if hide_orcid else (c['orcid'] or ''), source=c['source'] or c['tbl']))
        if c.get('book'):
            p['book'] = True
        if c.get('lc') and not hide_orcid:
            p['lc'] = list(c['lc'])
        p['sb'], p['sd'] = c.get('sb'), c.get('sd')
        ex = authors.get(c['work'], set()) - ({c['credited']} if hide_orcid else set())
        fe = L.features(people, p, exacts=ex)
        st, k, br, cands, sig = W.rule_wp(people, p, fe, pop, P)
        return st, k, br, len(cands)
    out = []
    for c in open_:
        st, k, br, n = run(c)
        out.append(dict(pid=c['pid'], work=c['work'], name=c['name'], year=c['year'], title=(c['title'] or '')[:90],
                        tbl=c['tbl'], key=c['key'], label=people_c[c['key']]['label'], relation=c['relation'],
                        tie=c['source_tie'], state=st, linked=k or '', branch=br))
        R[f'sim_{st}' + ('_to_tied_key' if k == c['key'] else ('_to_other' if k else ''))] += 1
    R['sim_linked_positions'] = sum(1 for o in out if o['state'] in ('linked', 'exact') and o['linked'] == o['key'])
    R['sim_linked_works'] = len({o['work'] for o in out if o['state'] in ('linked', 'exact') and o['linked'] == o['key']})
    R['sim_linked_keys'] = len({o['key'] for o in out if o['state'] in ('linked', 'exact') and o['linked'] == o['key']})
    # ---- masked test of the change: ORCID-credited positions printed under a tied form
    masked = []
    for c in cand:
        if c['credited_how'] != 'orcid' or not c['credited']:
            continue
        st, k, br, n = run(c, hide_orcid=True)
        tag = 'masked_same_key' if c['credited'] == c['key'] else 'masked_other_key'
        R[f'{tag}_n'] += 1
        masked.append(dict(pid=c['pid'], name=c['name'], year=c['year'], title=(c['title'] or '')[:80], credited=c['credited'],
                           tied_key=c['key'], tied_label=people_c[c['key']]['label'], form=c['form'],
                           relation=c['relation'], tie=c['source_tie'], state=st, linked=k or '', branch=br))
        if st in ('linked', 'exact'):
            R[f'{tag}_linked_{"right" if k == c["credited"] else ("to_tied_key" if k == c["key"] else "elsewhere")}'] += 1
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with open(SCRATCH / 'works-simulated.json', 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, default=str)
    with open(SCRATCH / 'works-masked.json', 'w') as fh:
        json.dump(masked, fh, ensure_ascii=False, default=str)
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in R.items()}
    print(json.dumps(rep, indent=1, default=str))
    rp = OUT / 'report.json'
    d = json.loads(rp.read_text()) if rp.exists() else {}
    d['works'] = rep
    rp.write_text(json.dumps(d, ensure_ascii=False, indent=1, default=list) + '\n')


ORCID_CACHE = SCRATCH / 'orcid-person.jsonl'


def orcid_records():
    """orcid -> {'names': [printed forms], 'other': [other names]} from the fetch cache"""
    out = {}
    if ORCID_CACHE.exists():
        for line in open(ORCID_CACHE, encoding='utf-8'):
            r = json.loads(line)
            out[r['orcid']] = r
    return out


def cmd_orcid_fetch(args):
    """The public ORCID person record (name, credit name, other names) of every ORCID on a key of a candidate pair
    (tier A and B of the last `pairs` run): the record's own statement of the person's names. Generic client name, no
    contact address, one request a second, cached; stops after five refusals in a row."""
    import time
    import urllib.request
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    keys = set()
    for fn in ('tier-a-pairs.csv', 'tier-b-review.csv'):
        with open(OUT / fn, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                keys |= {r['a'], r['b']}
    want = set()
    for k in keys:
        row = con.execute('SELECT anchors FROM keys WHERE key = ?', (k,)).fetchone()
        want |= {a[6:] for a in json.loads(row[0] or '[]') if a.startswith('orcid:')} if row else set()
    have = set(orcid_records())
    todo = sorted(want - have)
    print(len(want), 'orcids,', len(todo), 'to fetch', flush=True)
    bad = 0
    with open(ORCID_CACHE, 'a', encoding='utf-8') as fh:
        for i, o in enumerate(todo):
            req = urllib.request.Request(f'https://pub.orcid.org/v3.0/{o}/person',
                                         headers={'Accept': 'application/json', 'User-Agent': 'historiography-kg/0.1'})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    d = json.loads(resp.read())
                bad = 0
            except Exception as e:                      # noqa: BLE001
                bad += 1
                print('refused', o, e, flush=True)
                if bad >= 5:
                    print('five refusals in a row: stopping', flush=True)
                    break
                time.sleep(5)
                continue
            nm = d.get('name') or {}
            giv = ((nm.get('given-names') or {}).get('value') or '').strip()
            fam = ((nm.get('family-name') or {}).get('value') or '').strip()
            cred = ((nm.get('credit-name') or {}).get('value') or '').strip()
            other = [(x.get('content') or '').strip() for x in ((d.get('other-names') or {}).get('other-name') or [])]
            fh.write(json.dumps(dict(orcid=o, given=giv, family=fam, credit=cred, other=[x for x in other if x]),
                                ensure_ascii=False) + '\n')
            fh.flush()
            if i % 100 == 0:
                print(i, flush=True)
            time.sleep(1.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pairs')
    sub.add_parser('works')
    sub.add_parser('orcid-fetch')
    args = ap.parse_args()
    {'pairs': cmd_pairs, 'works': cmd_works, 'orcid-fetch': cmd_orcid_fetch}[args.cmd](args)


if __name__ == '__main__':
    main()
