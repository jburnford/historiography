"""Analysis 7: robustness of the headline numbers.

Each headline number is recomputed under five switches, one at a time:
- base: the key log's authored + edited credits, thesis citations of translations / later editions rolled up to the
  original, JSTOR edition links kept, all people, all LC matches;
- + linked credits: AUTHORED / EDITED rows with evidence = 'linked' (cited-works linker, work-people, JSTOR-matched LC
  main entries, compilations; outside the key log) added;
- no roll-up: a thesis citing a translation or later edition cites the node it was matched to as cited (one that was
  unmatched before the roll-up stays unmatched); + linked, no roll-up: both switches;
- no editions (JSTOR): JSTOR CITES flagged edition = true (a later edition or translation was cited) left out;
- no primary-source people: person keys with role 'primary source' dropped;
- no comma-title LC matches: the LC matches whose title form was audited at about 97% (basis lc-/corpus-/both-comma)
  dropped;
- authored only: EDITED credits dropped (an edition's modern editor is otherwise credited with the classic text's
  citations: see 08-edited-heavy-top500.csv).
Concentration figures carry 95% intervals from a bootstrap over citing documents (500 Poisson resamples; estimate
+/- 1.96 bootstrap SD, see conc.boot). The others are point values; their intervals are in the analysis tables.
Also: article concentration by decade reweighted by the inverse thesis match rate of kind x cited decade.
"""
import json
from itertools import combinations

import numpy as np
import pandas as pd

from common import connect, out
from conc import boot, equalised, fetch, measures, pairs, reach

VARIANTS = {
    'base': dict(linked=False, rollup=True),
    '+ linked credits': dict(linked=True, rollup=True),
    'no roll-up': dict(linked=False, rollup=False),
    '+ linked, no roll-up': dict(linked=True, rollup=False),
    'no editions (JSTOR)': dict(editions=False),
    'no primary-source people': dict(drop_primary_people=True),
    'no comma-title LC matches': dict(drop_comma=True),
    'authored only (no EDITED credits)': dict(authored_only=True),
}
CC = ['CA', 'US', 'GB', 'FR', 'BR', 'MX']


def cosine(a, b):
    u = a.index.union(b.index)
    va, vb = a.reindex(u).fillna(0).values, b.reindex(u).fillna(0).values
    return float(va @ vb / np.sqrt((va @ va) * (vb @ vb)))


def main():
    con = connect()
    rows = []
    n_all = dict(con.execute("SELECT d.country, count(DISTINCT c.did) FROM cit c JOIN diss d ON d.id=c.did GROUP BY 1").fetchall())
    for vname, kw in VARIANTS.items():
        pairs(con, **kw)
        r = dict(variant=vname)
        for lvl, table, where in (('thesis work', 'thesis_work', 'true'), ('thesis person', 'thesis_person', 'true'),
                                  ('article work', 'article_work', 'true'),
                                  ('article person', 'article_person', 'true')):
            a = fetch(con, table, where)
            m = measures(a['i'])
            ci = boot(a['i'], a['d'], B=500, keys=('top100_share',))
            r[f'{lvl} pairs'] = len(a['i'])
            r[f'{lvl} top100 share'] = round(m['top100_share'], 4)
            r[f'{lvl} top100 share lo'] = round(ci['top100_share'][0], 4)
            r[f'{lvl} top100 share hi'] = round(ci['top100_share'][1], 4)
            r[f'{lvl} reach top100'] = round(reach(a['d'], a['i'], 100), 4)
        # thesis vs article person profile, 2008-2020, keyed universe
        t = con.execute("""SELECT item, count(DISTINCT doc) n FROM thesis_person tp WHERE year BETWEEN 2008 AND 2020
                           AND EXISTS (SELECT 1 FROM thesis_work tw JOIN gw ON gw.key=tw.item AND gw.layer='keyed'
                                       WHERE tw.doc=tp.doc) GROUP BY 1""").df().set_index('item')['n']
        a = con.execute("""SELECT item, count(DISTINCT doc) n FROM article_person WHERE year BETWEEN 2008 AND 2020
                           GROUP BY 1""").df().set_index('item')['n']
        r['thesis-vs-article person cosine 2008-20'] = round(cosine(t, a), 4)
        # national profiles: cosine CA-US, GB-US, FR-BR (route A), universal share by country on 500-thesis draws
        p = con.execute(f"SELECT doc, item, country FROM thesis_person WHERE country IN {tuple(CC)}").df()
        n_c = p.groupby('country')['doc'].nunique()
        sh = {c: p[p.country == c].groupby('item')['doc'].nunique() / n_c[c] for c in CC}
        for x, y in (('CA', 'US'), ('GB', 'US'), ('CA', 'GB'), ('FR', 'BR')):
            r[f'cosine {x}-{y} (route A)'] = round(cosine(sh[x], sh[y]), 4)
        for x, y in (('CA', 'US'), ('GB', 'US'), ('CA', 'GB')):
            ta, tb = set(sh[x].nlargest(100).index), set(sh[y].nlargest(100).index)
            r[f'top-100 people shared {x}-{y} (route A)'] = len(ta & tb)
        # works profiles
        pw = con.execute(f"SELECT doc, item, country FROM thesis_work WHERE country IN {tuple(CC)}").df()
        nw = pw.groupby('country')['doc'].nunique()
        shw = {c: pw[pw.country == c].groupby('item')['doc'].nunique() / nw[c] for c in CC}
        for x, y in (('CA', 'US'), ('GB', 'US'), ('FR', 'BR')):
            r[f'works cosine {x}-{y}'] = round(cosine(shw[x], shw[y]), 4)
        # top-100 people share of person pairs by country, on equal pair draws (10 draws)
        arrs = {c: fetch(con, 'thesis_person', f"country='{c}'") for c in CC}
        tgt = int(0.8 * min(len(a['i']) for a in arrs.values()))
        for c in CC:
            r[f'top100 people share {c} (equal draws)'] = round(equalised(arrs[c]['i'], arrs[c]['d'], tgt, R=10)['top100_share'], 4)
        # named shares of Brazilian and French theses (route A)
        for nm, pred in (('Hobsbawm', "label ILIKE 'Eric Hobsbawm%' OR label ILIKE 'E. J. Hobsbawm'"),
                         ('E. P. Thompson', "label ILIKE 'E. P. Thompson' OR label ILIKE 'Edward P. Thompson'"),
                         ('Le Goff', "label ILIKE 'Jacques Le Goff'"), ('Bourdieu', "label ILIKE 'Pierre Bourdieu'"),
                         ('Foucault', "label ILIKE 'Michel Foucault'")):
            for c in ('BR', 'FR', 'US'):
                v = con.execute(f"""SELECT count(DISTINCT doc) FROM thesis_person WHERE country='{c}'
                    AND item IN (SELECT key FROM person WHERE {pred})""").fetchone()[0]
                r[f'{nm} share of {c} theses (route A)'] = round(v / n_all[c], 4)
        docs_by_c = {c: p.loc[p.country == c, 'doc'].unique() for c in CC}
        acc = {c: [] for c in CC}
        for s in range(20):
            g = np.random.default_rng(100 + s)
            take = set()
            for c in CC:
                take.update(g.choice(docs_by_c[c], size=min(500, len(docs_by_c[c])), replace=False))
            q = p[p.doc.isin(take)]
            ncty = q.groupby('item')['country'].nunique()
            for c in CC:
                k = ncty.reindex(q.loc[q.country == c, 'item'].values).values
                acc[c].append((k == 6).mean())
        for c in ('CA', 'BR', 'FR'):
            r[f'universal share {c} (route A)'] = round(float(np.mean(acc[c])), 4)
        # supervisor: own vs institution-decade peers (route A), point values
        sv = con.execute("""
            WITH th AS (SELECT DISTINCT d.id did, d.institution, d.decade FROM diss d
                        WHERE d.id IN (SELECT did FROM cit) AND d.decade IS NOT NULL AND d.institution IS NOT NULL),
                 sp AS (SELECT DISTINCT tk.did, s.person sup FROM supervised s JOIN tk ON tk.key=s.thesis
                        JOIN th ON th.did=tk.did),
                 cs AS (SELECT DISTINCT th.institution, th.decade, sp.sup FROM sp JOIN th USING (did)),
                 rw AS (SELECT th.did, cs.sup, (sp.did IS NOT NULL) own FROM cs JOIN th USING (institution, decade)
                        LEFT JOIN sp ON sp.did=th.did AND sp.sup=cs.sup),
                 det AS (SELECT DISTINCT c.item FROM thesis_person c ANTI JOIN sp ON sp.did=c.doc AND sp.sup=c.item)
            SELECT own, avg((tp.doc IS NOT NULL)::INT) FROM rw JOIN det ON det.item=rw.sup
            LEFT JOIN thesis_person tp ON tp.doc=rw.did AND tp.item=rw.sup GROUP BY 1""").fetchall()
        sv = dict(sv)
        r['supervisor own rate (A)'] = round(sv[True], 4)
        r['supervisor inst-decade peer rate (A)'] = round(sv[False], 5)
        # age: graph-matched restricted median, cohorts 2010-14 and 2015-18
        for lo, hi in ((2010, 2014), (2015, 2018)):
            med = con.execute(f"""SELECT median(t.year - w.year) FROM thesis_work t JOIN gw w ON w.key=t.item
                WHERE w.year <= 2015 AND t.year BETWEEN {lo} AND {hi} AND t.year - w.year >= 3""").fetchone()[0]
            r[f'median age graph-restricted {lo}-{hi}'] = med
            med = con.execute(f"""SELECT median(t.year - t.cited_year) FROM thesis_work t
                WHERE t.cited_year <= 2015 AND t.year BETWEEN {lo} AND {hi} AND t.year - t.cited_year >= 3""").fetchone()[0]
            r[f'median age graph-restricted, printed year {lo}-{hi}'] = med
        rows.append(r)
        print(r, flush=True)
    df = pd.DataFrame(rows).set_index('variant').T
    df.to_csv(out('07-robustness.csv'))

    # article concentration by decade, reweighted by inverse thesis match rate of kind x cited decade
    pairs(con)
    con.execute("""CREATE OR REPLACE TEMP TABLE agerate AS SELECT CASE WHEN w.kind IN ('book','book_or_serial')
            THEN 'book' ELSE w.kind END kind2, (w.year//10)*10 AS cdec, avg((x.work_id IS NOT NULL)::INT) r
        FROM cit c JOIN cw w USING (work_id) LEFT JOIN xw x USING (work_id) WHERE w.year IS NOT NULL GROUP BY ALL""")
    dec = []
    for d in (1960, 1970, 1980, 1990, 2000, 2010):
        a = con.execute(f"""SELECT dense_rank() OVER (ORDER BY a.doc)-1 d, dense_rank() OVER (ORDER BY a.item)-1 i,
                coalesce(r.r, 0.2) r FROM article_work a LEFT JOIN agerate r ON r.kind2=a.kind2
                AND r.cdec=(a.cited_year//10)*10 WHERE a.year//10*10={d}""").fetchnumpy()
        rr = np.clip(a['r'], 0.05, 1)
        # equalise the number of pairs across decades: draw whole articles until 21,725 pairs (as in 02)
        rng = np.random.default_rng(1)
        vals_o, vals_w = [], []
        udocs = np.unique(a['d'])
        for _ in range(20):
            perm = rng.permutation(udocs)
            cnt = np.bincount(a['d'])[perm]
            take = set(perm[:np.searchsorted(np.cumsum(cnt), 21725) + 1].tolist())
            sel = np.isin(a['d'], list(take))
            vals_o.append(measures(a['i'][sel])['top100_share'])
            vals_w.append(measures(a['i'][sel], 1 / rr[sel])['top100_share'])
        dec.append(dict(decade=f'{d}s', articles=len(udocs), observed_top100=round(float(np.mean(vals_o)), 4),
                        reweighted_top100=round(float(np.mean(vals_w)), 4),
                        reweighted_lo=round(float(np.percentile(vals_w, 2.5)), 4),
                        reweighted_hi=round(float(np.percentile(vals_w, 97.5)), 4)))
    pd.DataFrame(dec).to_csv(out('07-article-decade-reweighted.csv'), index=False)
    out('07-summary.json').write_text(json.dumps(dict(variants=rows, article_decades=dec), indent=1, default=float))
    print(df.to_string())
    print(pd.DataFrame(dec).to_string())


if __name__ == '__main__':
    main()
