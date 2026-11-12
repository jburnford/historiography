"""Analysis 5: the age of what is cited.

Age of a citation = year of the citing document - year of the cited work. Summaries per citing cohort: median age (a
'cited half-life': half of the citations are to works younger than this), interquartile range, share of citations to
works under 10 years old and to works 50+ years old. Intervals: weighted bootstrap over citing documents (500).

Three versions, so the catalogue cut-off can be seen doing its work:
- NAIVE: graph-matched thesis citations, all citing and cited years. Books after 2016 are mostly unmatched (the LC
  book catalogue ends in 2016), so recent theses look as if they cite old work;
- RESTRICTED (the brief's frame): graph-matched, cited works <= 2015, citing documents <= 2018, and every cohort
  left-truncated at 3 years (ages < 3 dropped everywhere, since a 2018 thesis cannot show an age < 3 in this frame);
- CORPUS: the year as printed in the bibliography for every citation, matched or not (no catalogue cut-off), in the
  scholarship frame (books, articles, chapters not mostly labelled primary). The year is that of the edition cited,
  so translations and reprints make works look younger than their first publication (affects Brazil and France most);
  the graph year is the earliest year of the matched edition cluster.
Articles (JSTOR): graph level only, by decade; same restriction (cited <= 2015, articles <= 2018, age >= 3).

Which year (2026-11-11 evening): NAIVE / RESTRICTED use the graph work's year (gw.year). With the edition roll-up a
thesis citing a translation or later edition cites the original work, so its graph year is the original's key year
(itself sometimes a reprint year, ARCHITECTURE.md §8 class 17). CORPUS uses the year printed in the bibliography. Both
are shown, with two added versions: RESTRICTED on the printed year of the same matched pairs, and CORPUS with the
printed year replaced by the original's graph year for the corpus works rolled up to an original (translations and
later editions only, and only when the graph year is not later than the printed one; everything else keeps its printed
year).

2026-11-12 rerun: the graph year (gw.year) is now the work's first publication year where the build has one (Work
`first_year`, data/graph/work-years.csv.gz: LC notes, 008 reprint dates, edition clusters, class 17), else the key
year; the key's own year is gw.key_year. NAIVE, RESTRICTED, the IPW version, the JSTOR versions and the CORPUS
original-year version all read gw.year, so all now use first_year.
"""
import json

import numpy as np
import pandas as pd

from common import SMALL, connect, out
from conc import pairs

B = 500


def wquant(x, w, qs):
    """weighted quantiles of x, which must already be sorted"""
    c = np.cumsum(w)
    c = c / c[-1]
    return [x[np.searchsorted(c, q)] for q in qs]


def summarise(df, group, label):
    """df: doc, age, group col, optional weight col w (inverse match probability). Point values and a bootstrap over
    citing documents (500 Poisson resamples) for the median and the under-10 share."""
    rows = []
    rng = np.random.default_rng(13)
    for g, d in df.groupby(group):
        docs, inv = np.unique(d['doc'].values, return_inverse=True)
        age = d['age'].values.astype(float)
        w0 = d['w'].values.astype(float) if 'w' in d else np.ones(len(age))
        o = np.argsort(age, kind='stable')
        age, inv, w0 = age[o], inv[o], w0[o]
        med = float(wquant(age, w0, [0.5])[0])
        q1, q3 = wquant(age, w0, [0.25, 0.75])
        u10 = float((w0 * (age < 10)).sum() / w0.sum())
        o50 = float((w0 * (age >= 50)).sum() / w0.sum())
        meds, u10s = [], []
        for _ in range(B):
            w = rng.poisson(1.0, len(docs))[inv] * w0
            if w.sum() == 0:
                continue
            meds.append(wquant(age, w, [0.5])[0])
            u10s.append(float((w * (age < 10)).sum() / w.sum()))
        rows.append(dict(version=label, group=g, docs=len(docs), citations=len(age), small=len(docs) < SMALL,
                         median_age=med, median_lo=float(np.percentile(meds, 2.5)),
                         median_hi=float(np.percentile(meds, 97.5)), q1=q1, q3=q3, share_under10=round(u10, 4),
                         under10_lo=round(float(np.percentile(u10s, 2.5)), 4),
                         under10_hi=round(float(np.percentile(u10s, 97.5)), 4), share_50plus=round(o50, 4)))
    return rows


COHORT = """CASE WHEN year < 2000 THEN '1-before 2000' WHEN year < 2005 THEN '2-2000-04' WHEN year < 2010 THEN '3-2005-09'
            WHEN year < 2015 THEN '4-2010-14' WHEN year < 2019 THEN '5-2015-18' ELSE '6-2019-26' END"""


def main():
    con = connect()
    pairs(con)
    rows = []
    # NAIVE: graph-matched, all years (graph year of the matched work)
    naive = con.execute(f"""SELECT t.doc, t.year - w.year AS age, {COHORT.replace('year', 't.year')} AS cohort
        FROM thesis_work t JOIN gw w ON w.key=t.item
        WHERE w.year IS NOT NULL AND t.year IS NOT NULL AND t.year - w.year >= 0""").df()
    rows += summarise(naive, 'cohort', 'NAIVE graph-matched, all years')
    # RESTRICTED
    restr = con.execute(f"""SELECT t.doc, t.year - w.year AS age, {COHORT.replace('year', 't.year')} AS cohort
        FROM thesis_work t JOIN gw w ON w.key=t.item
        WHERE w.year <= 2015 AND t.year <= 2018 AND t.year - w.year >= 3""").df()
    rows += summarise(restr, 'cohort', 'RESTRICTED graph-matched, cited<=2015, citing<=2018, age>=3')
    # the same matched pairs on the printed year (the year of the edition the thesis cites)
    restr_p = con.execute(f"""SELECT t.doc, t.year - t.cited_year AS age, {COHORT.replace('year', 't.year')} AS cohort
        FROM thesis_work t WHERE t.cited_year <= 2015 AND t.year <= 2018 AND t.year - t.cited_year >= 3""").df()
    rows += summarise(restr_p, 'cohort', 'RESTRICTED graph-matched, printed year, cited<=2015, citing<=2018, age>=3')
    # CORPUS, scholarship frame, all years and with the same truncation
    corp = con.execute(f"""SELECT c.did AS doc, d.year - w.year AS age, {COHORT.replace('year', 'd.year')} AS cohort,
            d.country, d.year AS ty, w.year AS wy,
            CASE WHEN m.edition_moved AND g.year BETWEEN 1400 AND w.year THEN g.year ELSE w.year END AS oy,
            coalesce(m.edition_moved, false) AS moved
        FROM cit c JOIN diss d ON d.id=c.did JOIN cw w USING (work_id)
        LEFT JOIN cmap m USING (work_id) LEFT JOIN gw g ON g.key=m.gkey
        WHERE w.kind IN ('book','book_or_serial','article','chapter')
          AND NOT (w.prim > 0 AND w.prim >= 0.5*(w.prim+w.sec+w.unsp))
          AND w.year IS NOT NULL AND d.year IS NOT NULL AND d.year - w.year >= 0""").df()
    rows += summarise(corp, 'cohort', 'CORPUS as cited (scholarship frame), all years')
    corp_o = corp.assign(age=corp.ty - corp.oy)
    rows += summarise(corp_o, 'cohort', 'CORPUS original year for rolled-up editions (scholarship frame), all years')
    ct = corp[(corp.wy <= 2015) & (corp.ty <= 2018) & (corp.age >= 3)]
    rows += summarise(ct, 'cohort', 'CORPUS as cited, cited<=2015, citing<=2018, age>=3')
    # matched vs unmatched within the corpus version (how the matched subset is older)
    cm = con.execute(f"""SELECT c.did AS doc, d.year - w.year AS age,
            CASE WHEN x.work_id IS NULL THEN 'unmatched' ELSE 'matched' END || ' ' || {COHORT.replace('year', 'd.year')} AS g
        FROM cit c JOIN diss d ON d.id=c.did JOIN cw w USING (work_id) LEFT JOIN xw x USING (work_id)
        WHERE w.kind IN ('book','book_or_serial','article','chapter')
          AND NOT (w.prim > 0 AND w.prim >= 0.5*(w.prim+w.sec+w.unsp))
          AND w.year IS NOT NULL AND d.year IS NOT NULL AND d.year - w.year >= 0 AND d.year >= 2000""").df()
    rows += summarise(cm, 'g', 'CORPUS split by match status (theses 2000+)')
    # by country, theses 2010-2018, corpus version truncated
    cc = ct[(ct.ty >= 2010) & ct.country.isin(['CA', 'US', 'GB', 'FR', 'BR', 'MX'])]
    rows += summarise(cc, 'country', 'CORPUS by country, theses 2010-18, cited<=2015, age>=3')
    cco = corp_o[(corp_o.oy <= 2015) & (corp_o.ty <= 2018) & (corp_o.age >= 3) & (corp_o.ty >= 2010)
                 & corp_o.country.isin(['CA', 'US', 'GB', 'FR', 'BR', 'MX'])]
    rows += summarise(cco, 'country', 'CORPUS by country, original year for rolled-up editions, theses 2010-18, '
                                      'cited<=2015, age>=3')
    # the rolled-up citations alone: printed vs original year, by country (theses 2000+)
    mv = corp[corp.moved & (corp.ty >= 2000) & corp.country.isin(['CA', 'US', 'GB', 'FR', 'BR', 'MX'])]
    rows += summarise(mv, 'country', 'ROLLED-UP editions only, printed year, theses 2000+')
    rows += summarise(mv.assign(age=mv.ty - mv.oy), 'country', 'ROLLED-UP editions only, original year, theses 2000+')
    # Articles (JSTOR), graph level
    art = con.execute("""SELECT a.doc, a.year - a.cited_year AS age, CAST((a.year//10)*10 AS VARCHAR) || 's' AS decade
        FROM article_work a WHERE a.cited_year <= 2015 AND a.year <= 2018 AND a.year - a.cited_year >= 3
          AND a.year >= 1950""").df()
    rows += summarise(art, 'decade', 'ARTICLES graph-matched, cited<=2015, citing<=2018, age>=3')
    # theses by decade on the same footing as articles (graph, restricted)
    tdec = con.execute("""SELECT t.doc, t.year - w.year AS age, CAST((t.year//10)*10 AS VARCHAR) || 's' AS decade
        FROM thesis_work t JOIN gw w ON w.key=t.item
        WHERE w.year <= 2015 AND t.year <= 2018 AND t.year - w.year >= 3 AND t.year >= 1950""").df()
    rows += summarise(tdec, 'decade', 'THESES graph-matched by decade, cited<=2015, citing<=2018, age>=3')
    # inverse-probability weights: 1 / thesis match rate of the cited work's kind x cited decade (Table 1 pattern)
    con.execute("""CREATE TEMP TABLE agerate AS SELECT CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book'
            ELSE w.kind END kind2, (w.year//10)*10 AS cdec, avg((x.work_id IS NOT NULL)::INT) r
        FROM cit c JOIN cw w USING (work_id) LEFT JOIN xw x USING (work_id) WHERE w.year IS NOT NULL GROUP BY ALL""")
    ipw_t = con.execute(f"""SELECT t.doc, t.year - w.year AS age, {COHORT.replace('year', 't.year')} AS cohort, 1.0/r.r AS w
        FROM thesis_work t JOIN gw w ON w.key=t.item JOIN agerate r ON r.kind2=t.kind2 AND r.cdec=(w.year//10)*10
        WHERE w.year <= 2015 AND t.year <= 2018 AND t.year - w.year >= 3 AND r.r > 0.02""").df()
    rows += summarise(ipw_t, 'cohort', 'RESTRICTED + inverse-probability weighted (kind x cited decade)')
    ipw_a = con.execute("""SELECT a.doc, a.year - a.cited_year AS age, CAST((a.year//10)*10 AS VARCHAR) || 's' AS decade,
            1.0/r.r AS w
        FROM article_work a JOIN agerate r ON r.kind2=a.kind2 AND r.cdec=(a.cited_year//10)*10
        WHERE a.cited_year <= 2015 AND a.year <= 2018 AND a.year - a.cited_year >= 3 AND a.year >= 1950
          AND r.r > 0.02""").df()
    rows += summarise(ipw_a, 'decade', 'ARTICLES + inverse-probability weighted (kind x cited decade)')
    # composition: corpus version by country x cohort (all years)
    cc2 = corp[corp.country.isin(['CA', 'US', 'GB', 'BR'])].copy()
    cc2['cc'] = cc2['country'] + ' ' + cc2['cohort']
    rows += summarise(cc2, 'cc', 'CORPUS as cited, by country x cohort, all years')
    df = pd.DataFrame(rows)
    df.to_csv(out('05-age.csv'), index=False)
    out('05-summary.json').write_text(json.dumps(rows, indent=1, default=float))
    pd.set_option('display.width', 250)
    print(df.drop(columns=['q1', 'q3']).to_string())


if __name__ == '__main__':
    main()
