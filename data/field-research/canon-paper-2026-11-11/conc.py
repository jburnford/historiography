"""Concentration measures and the citing-pair tables the analyses share (imported by 02-07).

A 'pair' is one citing document and one cited item (a work or a person), counted once however many of the item's
works the document cites. An item's count = the number of distinct documents citing it.

Pair tables (built as temp tables on a connection by `pairs`):
  thesis_work      (doc, item, country, year, kind2, band, cited_year, cited_as, route, comma, edition, translation,
                    graph_year)   corpus -> graph work. cited_year = the year as printed in the bibliography (the
                    edition cited); graph_year = the graph work's year (with the roll-up, the original's key year)
  thesis_person    (doc, item, country, year, how)                                              via credits of those works
  article_work     (doc, item, year, journal, kind2, cited_year, edition)                       JSTOR CITES
  article_person   (doc, item, year, how, edition)
  corpus_work      (doc, item, country, year, ...)  the corpus work as cited, no matching needed
  corpus_person    (doc, item, country, year)       the author name as parsed, no matching needed
"""
import numpy as np

from common import CORPUS, CREDITS, INITIAL_ONLY, ROLLUP

SCHOLARSHIP_THESIS = ("kind2 IN ('book','article','chapter') AND cited_as <> 'primary' "
                      "AND cited_year IS NOT NULL AND cited_year <= 2015")
SCHOLARSHIP_ARTICLE = "kind2 IN ('book','article','chapter') AND cited_year IS NOT NULL AND cited_year <= 2015"


def measures(item, w=None, ks=(100, 1000)):
    """item: int array of the cited item of each pair (pairs already distinct); w: optional per-pair weights."""
    counts = np.bincount(item, weights=w)
    counts = counts[counts > 0]
    n = len(counts)
    tot = counts.sum()
    s = np.sort(counts)[::-1]
    res = dict(items=n, pairs=float(tot))
    res['top1pct_share'] = s[:max(1, int(np.ceil(n / 100)))].sum() / tot
    for k in ks:
        res[f'top{k}_share'] = s[:k].sum() / tot
    x = s[::-1]
    i = np.arange(1, n + 1)
    res['gini'] = (2 * (i * x).sum()) / (n * tot) - (n + 1) / n
    res['single_doc_items'] = float((counts <= 1).mean()) if w is None else float('nan')
    return res


def doc_weights_boot(doc, B, seed=7):
    """Poisson(1) weight per document for each of B bootstrap replicates (a bootstrap over citing documents)."""
    rng = np.random.default_rng(seed)
    nd = doc.max() + 1
    for _ in range(B):
        yield rng.poisson(1.0, nd)[doc]


def boot(item, doc, B=500, w=None, keys=('top1pct_share', 'top100_share', 'top1000_share', 'gini')):
    """Bootstrap over citing documents (B Poisson resamples). Returns, per measure, estimate +/- 1.96 bootstrap SD.
    Percentile intervals are not used: resampling documents changes which items are cited at all (a third of the
    once-cited items drop out, others are doubled), which biases Gini and the top-1% share; the bootstrap is used for
    the spread only."""
    point = measures(item, w)
    vals = {k: [] for k in keys}
    for wd in doc_weights_boot(doc, B):
        ww = wd if w is None else wd * w
        sel = ww > 0
        m = measures(item[sel], ww[sel])
        for k in keys:
            vals[k].append(m[k])
    return {k: (point[k] - 1.96 * float(np.std(v)), point[k] + 1.96 * float(np.std(v))) for k, v in vals.items()}


def reach(doc, item, k=100):
    """Share of documents citing at least one of the k most-cited items of the same pair set."""
    counts = np.bincount(item)
    top = np.argsort(counts)[::-1][:k]
    hit = np.isin(item, top)
    return len(np.unique(doc[hit])) / len(np.unique(doc))


def equalised(item, doc, target_pairs, R=50, seed=3,
              keys=('top1pct_share', 'top100_share', 'top1000_share', 'gini', 'reach_top100')):
    """Draw whole documents in random order until target_pairs pairs are reached; R draws; mean and 2.5/97.5 pct.
    Puts groups of different size and bibliography length on the same footing (top-k shares depend on both)."""
    rng = np.random.default_rng(seed)
    udocs, inv = np.unique(doc, return_inverse=True)
    per_doc = np.bincount(inv)
    order_idx = np.argsort(inv, kind='stable')
    starts = np.concatenate([[0], np.cumsum(per_doc)])
    vals = {k: [] for k in keys}
    ndocs = []
    for _ in range(R):
        perm = rng.permutation(len(udocs))
        cum = np.cumsum(per_doc[perm])
        take = perm[:np.searchsorted(cum, target_pairs) + 1]
        idx = np.concatenate([order_idx[starts[d]:starts[d + 1]] for d in take])
        m = measures(item[idx])
        m['reach_top100'] = reach(doc[idx], item[idx], 100)
        ndocs.append(len(take))
        for k in keys:
            vals[k].append(m[k])
    res = {k: float(np.mean(v)) for k, v in vals.items()}
    res.update({k + '_lo': float(np.percentile(v, 2.5)) for k, v in vals.items()})
    res.update({k + '_hi': float(np.percentile(v, 97.5)) for k, v in vals.items()})
    res['docs_drawn'] = float(np.mean(ndocs))
    return res


def hows(linked=None, authored_only=False):
    """The credit kinds a person count uses: the key log's AUTHORED/EDITED claims, plus evidence='linked' credits when
    linked (default: the PAPER_CREDITS switch)."""
    if linked is None:
        linked = CREDITS == 'linked'
    if authored_only:      # edition editors (Lerner for Machiavelli, Skinner for Adam Smith ...) get no credit
        return "('authored','linked_authored')" if linked else "('authored')"
    return "('authored','edited','linked_authored','linked_edited')" if linked else "('authored','edited')"


def pairs(con, linked=None, editions=True, drop_comma=False, drop_primary_people=False, authored_only=False,
          rollup=None):
    """Create the pair temp tables on con. Options are the robustness switches of analysis 7. linked / rollup default
    to the PAPER_CREDITS / PAPER_ROLLUP switches. rollup=False: a thesis citing a translation or later edition cites
    the node it was matched to as cited (gkey_cited); one that was unmatched before the roll-up stays unmatched."""
    hw = hows(linked, authored_only)
    if rollup is None:
        rollup = ROLLUP
    gk = 'm.gkey' if rollup else 'm.gkey_cited'
    con.execute(f"""CREATE OR REPLACE TEMP TABLE band AS SELECT work_id, count(DISTINCT did) n FROM cit GROUP BY 1""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE thesis_work0 AS
        SELECT c.did AS doc, {gk} AS item, d.country, d.year,
               CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book' ELSE w.kind END AS kind2,
               min(b.n) AS band, min(w.year) AS cited_year,
               min(CASE WHEN w.prim > 0 AND w.prim >= 0.5*(w.prim+w.sec+w.unsp) THEN 'primary' ELSE 'not' END) cited_as,
               min(m.route) AS route, bool_and(m.comma) AS comma,
               bool_and(m.edition_moved) AS edition, bool_and(coalesce(t.relation='translation', false)) AS translation
        FROM cit c JOIN cmap m USING (work_id) JOIN diss d ON d.id=c.did JOIN cw w USING (work_id)
        JOIN band b USING (work_id) LEFT JOIN tx t USING (work_id)
        WHERE {gk} IS NOT NULL {"AND NOT m.comma" if drop_comma else ""}
        GROUP BY c.did, {gk}, d.country, d.year, kind2""")
    # one row per (doc, item): a doc citing the same graph work under two kinds keeps one row. edition / translation:
    # every corpus work behind the pair was a translation (or later edition) rolled up to this original
    con.execute("""CREATE OR REPLACE TEMP TABLE thesis_work AS SELECT t.doc, t.item, any_value(t.country) country,
        any_value(t.year) AS year, min(t.kind2) kind2, min(t.band) band, min(t.cited_year) cited_year,
        min(t.cited_as) cited_as, min(t.route) route, bool_and(t.comma) comma, bool_and(t.edition) edition,
        bool_and(t.translation) translation, any_value(g.year) graph_year
        FROM thesis_work0 t LEFT JOIN gw g ON g.key=t.item GROUP BY t.doc, t.item""")
    pfilter = ("AND coalesce(p.role,'unknown') <> 'primary source'" if drop_primary_people else "")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE thesis_person AS
        SELECT t.doc, c.person AS item, any_value(t.country) country, any_value(t.year) AS year,
               min(c.how) how, bool_or(t.kind2 IN ('book','article','chapter') AND t.cited_as <> 'primary'
                   AND t.cited_year <= 2015) AS in_frame
        FROM thesis_work t JOIN cred c ON c.work=t.item JOIN person p ON p.key=c.person
        WHERE c.how IN {hw} {pfilter} GROUP BY t.doc, c.person""")
    ed = "" if editions else "AND NOT g.edition"
    con.execute(f"""CREATE OR REPLACE TEMP TABLE article_work AS
        SELECT g.src AS doc, g.dst AS item, ci.year, ci.journal,
               CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book' ELSE w.kind END kind2, w.year cited_year,
               bool_and(g.edition) edition
        FROM gc g JOIN citing ci ON ci.key=g.src AND ci.ctype='article' JOIN gw w ON w.key=g.dst
        WHERE g.ctype='article' {ed} GROUP BY ALL""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE article_person AS
        SELECT a.doc, c.person AS item, any_value(a.year) AS year, min(c.how) how,
               bool_or(a.kind2 IN ('book','article','chapter') AND a.cited_year <= 2015) AS in_frame
        FROM article_work a JOIN cred c ON c.work=a.item JOIN person p ON p.key=c.person
        WHERE c.how IN {hw} {pfilter} GROUP BY a.doc, c.person""")


def corpus_pairs(con):
    con.execute(f"""CREATE OR REPLACE TEMP TABLE corpus_work AS
        SELECT c.did AS doc, c.work_id AS item, d.country, d.year,
               CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book' ELSE w.kind END kind2, w.year cited_year,
               CASE WHEN w.prim > 0 AND w.prim >= 0.5*(w.prim+w.sec+w.unsp) THEN 'primary' ELSE 'not' END cited_as
        FROM cit c JOIN diss d ON d.id=c.did JOIN cw w USING (work_id)""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE corpus_person AS
        SELECT t.doc, a.person_key AS item, any_value(t.country) country, any_value(t.year) AS year,
               bool_or(t.kind2 IN ('book','article','chapter') AND t.cited_as <> 'primary' AND t.cited_year <= 2015) in_frame
        FROM corpus_work t JOIN read_csv('{CORPUS}/authored.csv.gz', all_varchar=true) a ON a.work_id=t.item
        WHERE NOT {INITIAL_ONLY.replace('person_key', 'a.person_key')}
        GROUP BY t.doc, a.person_key""")


def fetch(con, table, where='true', extra=()):
    """Integer-coded arrays (doc, item, *extra) of a pair table subset."""
    cols = ', '.join(['doc', 'item'] + list(extra))
    r = con.execute(f"""SELECT dense_rank() OVER (ORDER BY doc) - 1 AS d, dense_rank() OVER (ORDER BY item) - 1 AS i
                        {''.join(', ' + e for e in extra)} FROM {table} WHERE {where}""").fetchnumpy()
    return r
