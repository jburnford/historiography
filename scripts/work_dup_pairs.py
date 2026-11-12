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


def shown_first(w):
    """sort key: the work shown of a pair comes first"""
    return (w['resolution'] == 'unkeyed', w['preprint'], -len(w['anchors'] or ()), w['key'])


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
