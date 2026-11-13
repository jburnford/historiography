"""Works listed twice on a person page (ARCHITECTURE.md section 8, class 11; pass seven, 2026-11-12).

Two forms:
  A  two key-log claims for one person and one work (two routes each wrote a claim). Measured here; the build collapses
     them to one AUTHORED / EDITED row that keeps every claim (`claims`, `n_claims`), so no key-log change is needed.
  B  one work under two work keys. Pairs, by general rules only:
     exact identifier   the same DOI once folded (case, a doi.org prefix, trailing punctuation), the same OpenAlex id, or
                        the same ISBN on two book nodes;
     title-year-person  one person credited (role author, key log or linked) on two works whose folded titles agree
                        (statement of responsibility and a '(Preprint)' marker removed; at least 3 words and 15
                        letters), same year (a preprint one year apart), kinds compatible (a thesis never pairs with a
                        non-thesis, a review never with a non-review), and not in two different journals (two reviews
                        of one book by one reviewer in two journals are two works).
     The shown key of a pair: a key-log key before an unkeyed node, a version before a preprint, more anchors, then the
     smaller key.
     2026-11-13 (pass ten): an unkeyed record of a keyed work (one shown, the keyed work, per unkeyed record):
     same-volume-title            the same folded title (over 15 characters) and PART_OF the same volume;
     title-year-candidate-credit  the same folded title (over 20 characters, not generic: GENERIC_WORDS or a stop title
                                  borne by 20+ work nodes), years within one, compatible kinds, not two journals, and a
                                  person who is a name candidate on the unkeyed record holds a key-log credit on the
                                  keyed work.
     Their DOIs, where the keyed work has none, go to doi-attach-candidates.csv (key, doi, basis) for a later key-log
     attach proposal (none is built here).

Outputs (no key-log change; the proposal is NOT applied):
  data/identifiers/work-dup-merges-2026-11-12/pairs.csv.gz   every pair with its evidence (review file)
  data/identifiers/work-dup-merges-2026-11-12/proposal.json  merges for exact-identifier pairs of two key-log keys only
                                                             (dry-run validated against the key-log cache)
  data/identifiers/work-dup-merges-2026-11-12/report.json    counts of both forms
  data/graph/work-duplicates.csv.gz                          hidden, shown, basis: the build loads it as SAME_WORK and
                                                             the explorer lists the pair once on a person page

    python3 scripts/work_dup_pairs.py [--graph build/graph] [--no-validate]
"""
import argparse
import csv
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
OUT = ROOT / 'data/identifiers/work-dup-merges-2026-11-12'
TABLE = ROOT / 'data/graph/work-duplicates.csv.gz'
PREPRINT = re.compile(r'\s*[\(\[]\s*preprint\s*[\)\]]\s*$', re.I)
SIMILAR_KINDS = {'article', 'other', 'chapter', 'preprint', None, ''}


def fold_title(t):
    """folded title: statement of responsibility (' / ...') and a trailing '(Preprint)' removed, ASCII, lower case,
    letters and digits only"""
    t = re.split(r'\s+/\s+', t or '', 1)[0]
    t = PREPRINT.sub('', t)
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', t)).strip()


def is_preprint(label, anchors):
    return bool(PREPRINT.search(re.split(r'\s+/\s+', label or '', 1)[0])) or any(
        re.search(r'(?i)preprint|arxiv|ssrn|biorxiv|medrxiv|osf\.io|zenodo', a) for a in anchors or () if a.startswith('doi:'))


def fold_doi(a):
    x = re.sub(r'^doi:(https?://(dx\.)?doi\.org/)?', '', a.lower())
    return re.sub(r'[.,;)\]]+$', '', x)


def kinds_compatible(k1, k2):
    if (k1 == 'thesis') != (k2 == 'thesis') or (k1 == 'review') != (k2 == 'review'):
        return False
    return k1 == k2 or (k1 in SIMILAR_KINDS and k2 in SIMILAR_KINDS)


def title_pair_ok(t1, y1, p1, t2, y2, p2):
    """same folded title, long enough, same year (one year apart when one is a preprint)"""
    if not t1 or t1 != t2 or len(t1.split()) < 3 or len(t1.replace(' ', '')) < 15:
        return False
    if y1 is None or y2 is None:
        return False
    return y1 == y2 or ((p1 != p2) and abs(y1 - y2) <= 1)


def journals_agree(a, b):
    """folded journal names: equal, or one contains the other ('historical methods' / 'historical methods a journal of
    ...')"""
    return a == b or a in b or b in a


# 2026-11-13 (class 11, pass ten): an unkeyed record of a keyed work. Rule 1a: the same folded title (over 15
# characters) and PART_OF the same volume (both chapters). Rule 1b: the same folded title (over 20 characters, not a
# generic title), years within one, and a person who is a name candidate on the unkeyed record holds a key-log credit on
# the keyed work. The keyed work is shown; the unkeyed record is hidden.
BASIS_VOLUME = 'same-volume-title'
BASIS_CANDIDATE = 'title-year-candidate-credit'
NEW_BASES = (BASIS_VOLUME, BASIS_CANDIDATE)
GENERIC_WORDS = re.compile(
    r'^(\d+ |[ivx]+ )?(untitled|introduction|introductions|general introduction|editors? s? ?introduction|conclusions?|'
    r'concluding remarks|preface|prefatory|foreword|afterword|epilogue|prologue|postscript|editorial|editors? s? ?note|'
    r'reviews?|book reviews?|reviews of books|review of|review essay|notes|notes on contributors|list of contributors|'
    r'contributors|index|bibliography|select bibliography|selected bibliography|sources|letters?|letters to the editor|'
    r'correspondence|obituary|in memoriam|response|reply|comment|commentary|erratum|corrigendum|acknowledg\w*|'
    r'front matter|back matter|contents|table of contents|abstracts?|appendix|appendices|glossary|chronology|'
    r'shorter notices|short notices|book notes|communications|queries)\b')
STOP_MIN_NODES = 20          # a folded title borne by this many work nodes or more is a stop title (data-derived)


def generic_title(t, stop=()):
    """a title that names a kind of text rather than one work: on the data-derived stop list (titles borne by
    STOP_MIN_NODES or more work nodes), or a generic heading ('introduction to ...', 'book reviews', 'notes on
    contributors') of six words or fewer"""
    return t in stop or (bool(GENERIC_WORDS.match(t)) and len(t.split()) <= 6)


def rule_volume_ok(t_unkeyed, t_keyed):
    """rule 1a: the same folded title, over 15 characters (the volume is the join)"""
    return bool(t_unkeyed) and t_unkeyed == t_keyed and len(t_unkeyed) > 15


def family(label):
    """folded family name of a person label ('Last, First' or 'First Last')"""
    lab = re.sub(r'\s*\(.*?\)|,?\s*\d{4}-(\d{4})?\.?$', '', label or '').strip()
    f = lab.split(',', 1)[0] if ',' in lab else (lab.split() or [''])[-1]
    return fold_title(f)


def rule_volume_refusal(t, volume_title, hidden_people, keyed_people, fam):
    """None when rule 1a pairs an unkeyed chapter with a keyed chapter of the same volume (same folded title), else the
    reason: 'title' (15 characters or fewer), 'volume_title' (the chapter record carries the volume's title),
    'no_people' (nobody on the unkeyed record), 'people_disagree' (no person on the unkeyed record is a key-log author of
    the keyed work or bears the family name of one)"""
    if not rule_volume_ok(t, t):
        return 'title'
    if volume_title and volume_title == t:
        return 'volume_title'
    if not hidden_people:
        return 'no_people'
    if set(hidden_people) & set(keyed_people):
        return None
    kf = {fam.get(k) for k in keyed_people} - {None, ''}
    return None if any(fam.get(p) in kf for p in hidden_people) else 'people_disagree'


def rule_candidate_ok(t_unkeyed, y_unkeyed, t_keyed, y_keyed, stop=()):
    """rule 1b: the same folded title, over 20 characters, not generic, years within one"""
    if not t_unkeyed or t_unkeyed != t_keyed or len(t_unkeyed) <= 20 or generic_title(t_unkeyed, stop):
        return False
    return y_unkeyed is not None and y_keyed is not None and abs(y_unkeyed - y_keyed) <= 1


def sibling_twin(title, volume_title, printed_families, keyed_chapters):
    """rule 1a for a chapter fetched from a volume's chapter list (the name-only loader, link_work_people.py): the keyed
    chapter of the same volume it duplicates, or None. keyed_chapters: [(key, folded title, family names of its key-log
    authors)]. The same tests as rule 1a: the same folded title over 15 characters, not the volume's own title, and a
    printed author bears the family name of a key-log author of the keyed chapter; exactly one keyed chapter."""
    t = fold_title(title)
    if not rule_volume_ok(t, t) or (volume_title and fold_title(volume_title) == t):
        return None
    pf = {fold_title(f) for f in printed_families} - {''}
    hits = sorted({k for k, kt, fams in keyed_chapters if kt == t and pf & set(fams)})
    return hits[0] if len(hits) == 1 else None


def choose_shown(hidden, matches, rank):
    """one shown work for an unkeyed record matched to several keyed works: the first by `rank` (shown_first)"""
    return sorted(matches, key=rank)[0] if matches else None


def doi_attach_rows(pairs, anchors_of):
    """[(key, doi, basis)]: an unkeyed record's DOI for a keyed work with no DOI anchor (review file for a later key-log
    attach proposal; nothing is applied)"""
    out = []
    for shown, hidden, basis in pairs:
        if any(a.startswith('doi:') for a in anchors_of.get(shown, ())):
            continue
        for d in sorted({a for a in list(anchors_of.get(hidden, ())) + [hidden] if a.startswith('doi:')}):
            out.append((shown, d[4:], basis))
    return out


def shown_first(w):
    """sort key: the work shown of a pair comes first"""
    return (w['resolution'] == 'unkeyed', w['preprint'], -len(w['anchors'] or ()), w['key'])


def stop_titles(db, G):
    """folded titles borne by STOP_MIN_NODES or more work nodes (the most frequent titles in the graph)"""
    return {t for (t,) in db.execute(f"""SELECT t FROM (SELECT fold_title(label) t FROM '{G}/work.parquet' WHERE label IS NOT NULL)
            WHERE t <> '' GROUP BY t HAVING count(*) >= {STOP_MIN_NODES}""").fetchall()}


def unkeyed_record_pairs(db, G, R):
    """rules 1a and 1b: [(shown keyed work, hidden unkeyed record, basis, evidence, person)], one shown per hidden"""
    db.execute(f"""CREATE OR REPLACE TABLE uk AS SELECT key, fold_title(label) t, year, kind, journal, resolution res, anchors
                   FROM '{G}/work.parquet' WHERE label IS NOT NULL AND (resolution = 'unkeyed'
                   OR key IN (SELECT "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog')
                   OR key IN (SELECT "from" FROM '{G}/part_of.parquet'))""")
    stop = stop_titles(db, G)
    R['stop_titles'] = len(stop)
    found = defaultdict(dict)       # hidden -> {shown: (basis, evidence, person)}
    # 1a: both PART_OF the same volume; tightened after the hand check (2026-11-13: 13 of 30 were two chapters of a
    # dictionary or a book whose records carry the volume's title, or another author's chapter): the title is not the
    # volume's, and a person on the unkeyed record (any credit or a name candidate) is a key-log author of the keyed
    # work or bears the family name of one
    db.execute(f"""CREATE OR REPLACE TABLE hp AS SELECT DISTINCT "from" p, "to" w FROM '{G}/authored.parquet'
                   WHERE "to" IN (SELECT key FROM uk WHERE res = 'unkeyed')
                   UNION SELECT DISTINCT "from", "to" FROM '{G}/author_candidates.parquet' WHERE "to" IN (SELECT key FROM uk WHERE res = 'unkeyed')""")
    cand = db.execute(f"""WITH po AS (SELECT DISTINCT "from" c, "to" v FROM '{G}/part_of.parquet')
            SELECT u.key, k.key, u.t, pu.v, u.year, k.year, fold_title(vw.label) FROM po pu JOIN uk u ON u.key = pu.c AND u.res = 'unkeyed'
            JOIN po pk ON pk.v = pu.v AND pk.c <> pu.c JOIN uk k ON k.key = pk.c AND k.res <> 'unkeyed' AND k.t = u.t
            LEFT JOIN '{G}/work.parquet' vw ON vw.key = pu.v""").fetchall()
    ks = sorted({x[0] for x in cand} | {x[1] for x in cand})
    db.register('ks', __import__('pyarrow').table({'k': ks}))
    hidden_people, keyed_people = defaultdict(set), defaultdict(set)
    for p, w in db.execute("SELECT p, w FROM hp WHERE w IN (SELECT k FROM ks)").fetchall():
        hidden_people[w].add(p)
    for p, w in db.execute(f"""SELECT DISTINCT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
                               AND "to" IN (SELECT k FROM ks)""").fetchall():
        keyed_people[w].add(p)
    pl = {k for v in list(hidden_people.values()) + list(keyed_people.values()) for k in v}
    db.register('pl', __import__('pyarrow').table({'k': sorted(pl)}))
    fam = {k: family(l) for k, l in db.execute(f"SELECT key, label FROM '{G}/person.parquet' WHERE key IN (SELECT k FROM pl)").fetchall()}
    for u, k, t, v, uy, ky, vt in cand:
        why = rule_volume_refusal(t, vt, hidden_people.get(u, ()), keyed_people.get(k, ()), fam)
        if why:
            R[f'rule_1a_refused_{why}'] = R.get(f'rule_1a_refused_{why}', 0) + 1
            continue
        found[u].setdefault(k, (BASIS_VOLUME, f'title={t[:120]}; volume={v}; year={uy}/{ky}', ''))
    db.execute('DROP TABLE hp')
    # 1b: a name candidate on the unkeyed record holds a key-log credit on the keyed work
    for u, k, p, t, uy, ky, uj, kj, uk_, kk in db.execute(f"""WITH c AS (SELECT DISTINCT "from" p, "to" w FROM '{G}/author_candidates.parquet'),
                 kl AS (SELECT DISTINCT "from" p, "to" w FROM '{G}/authored.parquet' WHERE evidence = 'keylog')
            SELECT u.key, k.key, c.p, u.t, u.year, k.year, u.journal, k.journal, u.kind, k.kind
            FROM c JOIN uk u ON u.key = c.w AND u.res = 'unkeyed' JOIN kl ON kl.p = c.p
            JOIN uk k ON k.key = kl.w AND k.res <> 'unkeyed' AND k.t = u.t""").fetchall():
        if not rule_candidate_ok(t, uy, t, ky, stop):
            R['rule_1b_refused_title_or_year'] = R.get('rule_1b_refused_title_or_year', 0) + 1
            continue
        if not kinds_compatible(uk_, kk):
            R['rule_1b_refused_kinds'] = R.get('rule_1b_refused_kinds', 0) + 1
            continue
        if uj and kj and not journals_agree(fold_title(uj), fold_title(kj)):
            R['rule_1b_refused_two_journals'] = R.get('rule_1b_refused_two_journals', 0) + 1
            continue
        prev = found[u].get(k)
        if not prev or prev[0] != BASIS_CANDIDATE:      # the person tie is the stronger evidence
            found[u][k] = (BASIS_CANDIDATE, f'title={t[:120]}; year={uy}/{ky}', p)
    anc = dict(db.execute("SELECT key, anchors FROM uk").fetchall())
    out = []
    for u, m in found.items():
        # rule 1b matches first (a person tie), then the usual order (more anchors, smaller key)
        s = choose_shown(u, list(m), lambda k: (m[k][0] != BASIS_CANDIDATE, -len(anc.get(k) or ()), k))
        out.append((s, u) + m[s])
        if len(m) > 1:
            R['new_rule_hidden_with_several_keyed_matches'] = R.get('new_rule_hidden_with_several_keyed_matches', 0) + 1
    R['new_rule_pairs_by_basis'] = dict(Counter(x[2] for x in out))
    db.execute('DROP TABLE uk')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--graph', type=Path, default=ROOT / 'build/graph')
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    G = args.graph
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3")
    R = {}
    # form A
    for t in ('authored', 'edited'):
        n_pairs, n_extra = db.execute(f"""SELECT count(*), coalesce(sum(n - 1), 0) FROM (SELECT "from", "to", count(*) n
            FROM '{G}/{t}.parquet' WHERE evidence = 'keylog' GROUP BY ALL HAVING n > 1)""").fetchone()
        R[f'A_{t}_pairs_with_two_or_more_keylog_claims'] = n_pairs
        R[f'A_{t}_extra_claim_rows'] = n_extra
        cols = [c[0] for c in db.execute(f"DESCRIBE SELECT * FROM '{G}/{t}.parquet'").fetchall()]
        if 'n_claims' in cols:      # a build that collapses them
            R[f'A_{t}_rows_with_n_claims_gt_1'] = db.execute(f"SELECT count(*) FROM '{G}/{t}.parquet' WHERE n_claims > 1").fetchone()[0]
    # B, exact identifiers (SQL: only the works involved are read into memory)
    db.create_function('fold_doi', fold_doi, ['VARCHAR'], 'VARCHAR')
    db.create_function('fold_title', fold_title, ['VARCHAR'], 'VARCHAR')
    ident = db.execute(f"""WITH a AS (
            SELECT key, CASE WHEN a LIKE 'doi:%' THEN 'doi:' || fold_doi(a) ELSE a END x
              FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'
            UNION SELECT key, 'isbn:' || i FROM (SELECT key, unnest(string_split(regexp_replace(upper(isbn), '[^0-9X;, ]', '', 'g'),
              ';')) i FROM '{G}/work.parquet' WHERE kind = 'book' AND isbn IS NOT NULL) WHERE length(trim(i)) IN (10, 13))
        SELECT x, list(DISTINCT key ORDER BY key) FROM a GROUP BY x HAVING count(DISTINCT key) > 1""").fetchall()
    # B, title-year-person (credited with role author, any evidence)
    db.execute(f"""CREATE TABLE cr AS SELECT DISTINCT a."from" p, a."to" w FROM '{G}/authored.parquet' a
                   WHERE coalesce(a.role, 'author') IN ('author', 'author-editor')""")
    db.execute(f"""CREATE TABLE wt AS SELECT w.key, fold_title(w.label) t FROM '{G}/work.parquet' w
                   WHERE w.key IN (SELECT w FROM cr) AND w.label IS NOT NULL""")
    tgroups = db.execute("""SELECT cr.p, wt.t, list(DISTINCT cr.w) FROM cr JOIN wt ON wt.key = cr.w
            WHERE length(wt.t) >= 15 GROUP BY 1, 2 HAVING count(DISTINCT cr.w) BETWEEN 2 AND 6""").fetchall()
    need = {k for _, ks in ident for k in ks} | {k for _, _, ks in tgroups for k in ks}
    db.register('need', __import__('pyarrow').table({'k': sorted(need)}))
    W = {}
    for k, label, kind, year, res, anchors, isbn, journal in db.execute(
            f"SELECT key, label, kind, year, resolution, anchors, isbn, journal FROM '{G}/work.parquet' WHERE key IN (SELECT k FROM need)").fetchall():
        W[k] = dict(key=k, label=label, kind=kind, year=year, resolution=res, anchors=anchors or [], isbn=isbn,
                    journal=fold_title(journal) if journal else '')
    pairs = {}

    def add(a, b, basis, evidence, person=''):
        if a == b or a not in W or b not in W:
            return
        x, y = sorted((W[a], W[b]), key=lambda w: shown_first(dict(w, preprint=is_preprint(w['label'], w['anchors']))))
        key = (x['key'], y['key'])
        if key in pairs:
            if basis.startswith('exact') and not pairs[key]['basis'].startswith('exact'):
                pairs[key].update(basis=basis, evidence=evidence)
            return
        pairs[key] = dict(shown=x['key'], hidden=y['key'], basis=basis, evidence=evidence, person=person)
    for x, ks in ident:
        if len(ks) <= 5:
            for b in ks[1:]:
                add(ks[0], b, 'exact-' + x.split(':', 1)[0], x)
        else:
            R['exact_identifier_groups_over_5_skipped'] = R.get('exact_identifier_groups_over_5_skipped', 0) + 1
    for p, t, g in tgroups:
        if len(t.split()) < 3:
            continue
        g = sorted(g)
        for i, a in enumerate(g):
            for b in g[i + 1:]:
                wa, wb = W[a], W[b]
                pa_, pb = is_preprint(wa['label'], wa['anchors']), is_preprint(wb['label'], wb['anchors'])
                if wa['journal'] and wb['journal'] and not journals_agree(wa['journal'], wb['journal']):
                    R['title_pairs_skipped_two_journals'] = R.get('title_pairs_skipped_two_journals', 0) + 1
                    continue
                if kinds_compatible(wa['kind'], wb['kind']) and title_pair_ok(t, wa['year'], pa_, t, wb['year'], pb):
                    add(a, b, 'title-year-person' + (':preprint' if pa_ != pb else ''), f"title={t[:120]}; year={wa['year']}/{wb['year']}", p)
    new_pairs = unkeyed_record_pairs(db, G, R)
    need2 =sorted({k for sh in new_pairs for k in sh[:2]} - set(W))
    if need2:
        db.register('need2', __import__('pyarrow').table({'k': need2}))
        for k, label, kind, year, res, anchors, isbn, journal in db.execute(
                f"SELECT key, label, kind, year, resolution, anchors, isbn, journal FROM '{G}/work.parquet' WHERE key IN (SELECT k FROM need2)").fetchall():
            W[k] = dict(key=k, label=label, kind=kind, year=year, resolution=res, anchors=anchors or [], isbn=isbn,
                        journal=fold_title(journal) if journal else '')
    for shown, hidden, basis, evidence, person in new_pairs:
        if (shown, hidden) in pairs or (hidden, shown) in pairs:
            R['new_rule_pairs_already_paired'] = R.get('new_rule_pairs_already_paired', 0) + 1
            continue
        pairs[(shown, hidden)] = dict(shown=shown, hidden=hidden, basis=basis, evidence=evidence, person=person)
    # the unkeyed record's DOI for a keyed work with no DOI anchor (review file; no proposal is built or applied)
    att = doi_attach_rows([(r['shown'], r['hidden'], r['basis']) for r in pairs.values() if r['basis'] in NEW_BASES],
                          {k: W[k]['anchors'] for k in W})
    # chapters the name-only loader did not add because rule 1a found the keyed chapter (link_work_people.py)
    tw = ROOT / 'data/graph/name-only/chapter-twins.csv.gz'
    if tw.exists():
        with gzip.open(tw, 'rt', encoding='utf-8') as f:
            att += [(r['keyed_work'], r['doi'], BASIS_VOLUME + ':name-only-twin') for r in csv.DictReader(f)
                    if r.get('keyed_has_doi') != '1']
    att = sorted(set(att))
    R['doi_attach_candidates'] = len(att)
    rows = []
    for (s, h), r in sorted(pairs.items()):
        ws, wh = W[s], W[h]
        rows.append(dict(shown=s, hidden=h, basis=r['basis'], evidence=r['evidence'], person=r['person'],
                         shown_label=(ws['label'] or '')[:200], hidden_label=(wh['label'] or '')[:200],
                         shown_year=ws['year'], hidden_year=wh['year'], shown_kind=ws['kind'], hidden_kind=wh['kind'],
                         shown_resolution=ws['resolution'], hidden_resolution=wh['resolution'],
                         keylog_pair=ws['resolution'] != 'unkeyed' and wh['resolution'] != 'unkeyed'))
    R['B_pairs'] = len(rows)
    R['B_pairs_by_basis'] = dict(Counter(r['basis'] for r in rows))
    R['B_pairs_two_keylog_keys_by_basis'] = dict(Counter(r['basis'] for r in rows if r['keylog_pair']))
    # people with a pair on their page (credited on both works)
    db.register('pp', __import__('pyarrow').table({'s': [k[0] for k in pairs], 'h': [k[1] for k in pairs]}))
    R['B_person_pages_rows_doubled'] = db.execute("""SELECT count(*) FROM pp JOIN cr a ON a.w = pp.s JOIN cr b ON b.w = pp.h
                                                     AND b.p = a.p""").fetchone()[0]
    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0]) if rows else ['shown', 'hidden', 'basis']
    with gzip.open(OUT / 'pairs.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(OUT / 'doi-attach-candidates.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'doi', 'basis'])
        w.writerows(att)
    with gzip.open(TABLE, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['hidden', 'shown', 'basis'])
        for r in rows:
            w.writerow([r['hidden'], r['shown'], r['basis']])
    # merge proposal: exact identifiers, two key-log keys
    ops = [dict(event='merge', key=r['hidden'], into=r['shown'], decided_by='rule',
                basis=f"one work on two keys (work-dup-merges-2026-11-12): {r['basis']} {r['evidence']}")
           for r in rows if r['keylog_pair'] and r['basis'].startswith('exact')]
    proposal = dict(basis='one work on two work keys, exact identifier (work-dup-merges-2026-11-12): the same DOI once '
                          'folded, the same OpenAlex id or the same ISBN on two book keys', decided_by='rule', ops=ops)
    R['proposal_merges'] = len(ops)
    if ops and not args.no_validate:
        import identifiers as I
        import keylog_snapshot as KS
        state = KS.read_state()
        events, _ = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(events)
    (OUT / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=1) + '\n')
    (OUT / 'report.json').write_text(json.dumps(dict(date='2026-11-12', graph=str(G), counts=R), indent=1) + '\n')
    print(json.dumps(R, indent=1))


if __name__ == '__main__':
    main()
