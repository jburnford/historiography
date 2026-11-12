"""Analysis 2: concentration of citation on works and on people.

Measures (on distinct citing-document x item pairs):
- Gini: 0 when every cited item is cited by equally many documents, 1 when one item takes them all; computed over
  items cited at least once (uncited items are unobserved);
- top-1% share, top-100 share, top-1000 share: the share of all pairs that go to the most-cited 1% / 100 / 1,000
  items.
Top-k shares and Gini depend on how many documents and pairs a group has, so group comparisons are 'equalised':
whole documents are drawn at random until every group has the same number of pairs (50 draws; mean and 2.5-97.5
percentile of the draws).

Two levels bracket the truth:
- graph level (matched works, people through authored + edited): editions and spellings merged, but 58% of citations
  are missing and the missing ones are mostly rarely cited works -> concentration is overstated;
- corpus level (works as cited, authors as parsed; no matching): complete, but one work or person can be split over
  spelling and edition variants -> concentration is understated.
Loss simulations on the graph level: random thinning (keep 75% / 50%), thinning by the Table 1 pattern (keep a
citation with the match rate of its kind x citing band), and inverse-probability weighting (each matched citation
weighted by 1 / that rate) as an estimate of the unthinned value.
"""
import json

import numpy as np
import pandas as pd

from common import SMALL, connect, out
from conc import SCHOLARSHIP_ARTICLE, SCHOLARSHIP_THESIS, boot, corpus_pairs, equalised, fetch, hows, measures, pairs, reach

BINS = [(1, 1), (2, 2), (3, 4), (5, 9), (10, 49), (50, 99), (100, 499), (500, 10 ** 9)]
KEYS = ('top1pct_share', 'top100_share', 'top1000_share', 'gini')


def rnd(d):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}


def distribution(con, table, where='true'):
    rows = con.execute(f"SELECT n, count(*) FROM (SELECT item, count(*) n FROM {table} WHERE {where} GROUP BY 1) "
                       f"GROUP BY 1").fetchall()
    tot_items = sum(c for _, c in rows)
    tot_pairs = sum(n * c for n, c in rows)
    res = []
    for lo, hi in BINS:
        it = sum(c for n, c in rows if lo <= n <= hi)
        pr = sum(n * c for n, c in rows if lo <= n <= hi)
        res.append(dict(bin=f'{lo}' if lo == hi else (f'{lo}+' if hi > 10 ** 8 else f'{lo}-{hi}'), items=it,
                        item_share=round(it / tot_items, 4), pair_share=round(pr / tot_pairs, 4)))
    return res


def main():
    con = connect()
    pairs(con)
    corpus_pairs(con)
    con.execute(f"CREATE TEMP VIEW tw_f AS SELECT * FROM thesis_work WHERE {SCHOLARSHIP_THESIS}")
    con.execute(f"CREATE TEMP VIEW aw_f AS SELECT * FROM article_work WHERE {SCHOLARSHIP_ARTICLE}")
    con.execute(f"CREATE TEMP VIEW cw_f AS SELECT * FROM corpus_work WHERE {SCHOLARSHIP_THESIS}")
    R = {}

    # 1. distributions
    dist = []
    for name, table, where in (('thesis graph work', 'thesis_work', 'true'), ('thesis graph person', 'thesis_person', 'true'),
                               ('article graph work', 'article_work', 'true'),
                               ('article graph person', 'article_person', 'true'),
                               ('thesis corpus work', 'corpus_work', 'true'),
                               ('thesis corpus person', 'corpus_person', 'true')):
        for r in distribution(con, table, where):
            dist.append(dict(level=name, **r))
    pd.DataFrame(dist).to_csv(out('02-distribution.csv'), index=False)

    # 2. headline measures with a bootstrap over citing documents (500 resamples)
    head = []
    for name, table, where in (('thesis graph work', 'thesis_work', 'true'),
                               ('thesis graph work, scholarship frame', 'tw_f', 'true'),
                               ('thesis graph person', 'thesis_person', 'true'),
                               ('thesis graph person, scholarship frame', 'thesis_person', 'in_frame'),
                               ('article graph work', 'article_work', 'true'),
                               ('article graph work, scholarship frame', 'aw_f', 'true'),
                               ('article graph person', 'article_person', 'true'),
                               ('article graph person, scholarship frame', 'article_person', 'in_frame'),
                               ('thesis corpus work', 'corpus_work', 'true'),
                               ('thesis corpus work, scholarship frame', 'cw_f', 'true'),
                               ('thesis corpus person', 'corpus_person', 'true'),
                               ('thesis corpus person, scholarship frame', 'corpus_person', 'in_frame')):
        a = fetch(con, table, where)
        m = measures(a['i'])
        ci = boot(a['i'], a['d'], B=500)
        row = dict(level=name, docs=int(a['d'].max() + 1), reach_top100=round(reach(a['d'], a['i'], 100), 4),
                   reach_top10=round(reach(a['d'], a['i'], 10), 4), **rnd(m))
        for k in KEYS:
            row[k + '_lo'], row[k + '_hi'] = round(ci[k][0], 4), round(ci[k][1], 4)
        head.append(row)
        print(row, flush=True)
    pd.DataFrame(head).to_csv(out('02-headline.csv'), index=False)

    # 3. equalised comparisons
    comp = []

    def family(fam, groups, level):
        arrs = {g: fetch(con, t, w) for g, (t, w) in groups.items()}
        sizes = {g: len(a['i']) for g, a in arrs.items()}
        target = int(0.8 * min(sizes.values()))
        for g, a in arrs.items():
            e = equalised(a['i'], a['d'], target)
            ndocs = int(a['d'].max() + 1) if len(a['d']) else 0
            comp.append(dict(family=fam, level=level, group=g, docs=ndocs, pairs=sizes[g], target_pairs=target,
                             small=ndocs < SMALL, **rnd(e)))

    yrs_t, yrs_a = 'year BETWEEN 2008 AND 2020', 'year BETWEEN 2008 AND 2020'
    for lvl, tt, at, tf, af in (('work', 'thesis_work', 'article_work', 'tw_f', 'aw_f'),
                                ('person', 'thesis_person', 'article_person', 'thesis_person', 'article_person')):
        family('theses vs articles 2008-2020', {'theses': (tt, yrs_t), 'articles': (at, yrs_a)}, lvl)
        family('theses vs articles 2008-2020, scholarship frame',
               {'theses': (tf, yrs_t + (' AND in_frame' if lvl == 'person' else '')),
                'articles': (af, yrs_a + (' AND in_frame' if lvl == 'person' else ''))}, lvl)
    for lvl, t, frame in (('graph work', 'thesis_work', SCHOLARSHIP_THESIS), ('graph person', 'thesis_person', 'in_frame'),
                          ('corpus work', 'corpus_work', SCHOLARSHIP_THESIS), ('corpus person', 'corpus_person', 'in_frame')):
        family('thesis country', {c: (t, f"country='{c}'") for c in ('CA', 'US', 'GB', 'FR', 'BR', 'MX')}, lvl)
        family('thesis country, scholarship frame', {c: (t, f"country='{c}' AND {frame}")
                                                    for c in ('CA', 'US', 'GB', 'FR', 'BR', 'MX')}, lvl)
    for lvl, t in (('graph work', 'thesis_work'), ('graph person', 'thesis_person'), ('corpus work', 'corpus_work')):
        family('thesis decade', {f'{d}s': (t, f'year//10*10={d}') for d in (2000, 2010, 2020)}, lvl)
    for lvl, t in (('graph work', 'article_work'), ('graph person', 'article_person')):
        family('article decade', {f'{d}s': (t, f'year//10*10={d}') for d in (1960, 1970, 1980, 1990, 2000, 2010)}, lvl)
    pd.DataFrame(comp).to_csv(out('02-equalised-comparisons.csv'), index=False)

    # 4. loss simulations on the thesis graph level (pooled)
    rates = {(k, b): r for k, b, r in con.execute("""
        WITH t AS (SELECT CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book' ELSE w.kind END kind2,
                          CASE WHEN b.n=1 THEN 1 WHEN b.n<5 THEN 2 WHEN b.n<10 THEN 5 WHEN b.n<50 THEN 10 ELSE 50 END bb,
                          (x.work_id IS NOT NULL) m
                   FROM cit c JOIN cw w USING (work_id) JOIN band b USING (work_id) LEFT JOIN xw x USING (work_id))
        SELECT kind2, bb, avg(m::INT) FROM t GROUP BY ALL""").fetchall()}
    con.execute("CREATE OR REPLACE TEMP TABLE rate AS SELECT * FROM (VALUES " +
                ','.join(f"('{k}',{b},{r})" for (k, b), r in rates.items()) + ") v(kind2, bb, r)")
    con.execute("""CREATE OR REPLACE TEMP TABLE tw_r AS SELECT t.*, r.r FROM thesis_work t JOIN rate r ON r.kind2=t.kind2
                   AND r.bb = CASE WHEN t.band=1 THEN 1 WHEN t.band<5 THEN 2 WHEN t.band<10 THEN 5 WHEN t.band<50 THEN 10
                   ELSE 50 END""")
    sims = []
    base_w = measures(fetch(con, 'tw_r')['i'])
    base_p = measures(fetch(con, 'thesis_person')['i'])
    sims.append(dict(scenario='observed', level='work', **rnd(base_w)))
    sims.append(dict(scenario='observed', level='person', **rnd(base_p)))
    for scen, keep in (('random keep 75%', '0.75'), ('random keep 50%', '0.5'), ('Table-1 pattern thinning', 'r')):
        accw, accp = [], []
        for s in range(10):
            con.execute(f"SELECT setseed({0.1 + s / 100})")
            con.execute(f"CREATE OR REPLACE TEMP TABLE th AS SELECT doc, item FROM tw_r WHERE random() < {keep}")
            accw.append(measures(fetch(con, 'th')['i']))
            con.execute(f"""CREATE OR REPLACE TEMP TABLE thp AS SELECT DISTINCT th.doc, c.person AS item FROM th
                           JOIN cred c ON c.work=th.item WHERE c.how IN {hows()}""")
            accp.append(measures(fetch(con, 'thp')['i']))
        for lvl, acc in (('work', accw), ('person', accp)):
            sims.append(dict(scenario=scen, level=lvl, **rnd({k: float(np.mean([a[k] for a in acc])) for k in acc[0]})))
    a = fetch(con, 'tw_r', extra=('r',))
    ipw = measures(a['i'], 1.0 / a['r'])
    sims.append(dict(scenario='inverse-probability weighted (estimate of the unthinned value)', level='work', **rnd(ipw)))
    cols = ['scenario', 'level', 'items', 'pairs', 'top1pct_share', 'top100_share', 'top1000_share', 'gini',
            'single_doc_items']
    pd.DataFrame(sims)[cols].to_csv(out('02-loss-simulation.csv'), index=False)

    # 4b. does the country ranking of concentration survive pattern thinning by country rates?
    crates = {(c, k, b): r for c, k, b, r in con.execute("""
        WITH t AS (SELECT CASE WHEN d.country IN ('CA','US','GB','FR','BR','MX') THEN d.country ELSE 'other' END c,
                          CASE WHEN w.kind IN ('book','book_or_serial') THEN 'book' ELSE w.kind END kind2,
                          CASE WHEN b.n=1 THEN 1 WHEN b.n<5 THEN 2 WHEN b.n<10 THEN 5 WHEN b.n<50 THEN 10 ELSE 50 END bb,
                          (x.work_id IS NOT NULL) m
                   FROM cit c JOIN diss d ON d.id=c.did JOIN cw w USING (work_id) JOIN band b USING (work_id)
                   LEFT JOIN xw x USING (work_id))
        SELECT c, kind2, bb, avg(m::INT) FROM t GROUP BY ALL""").fetchall()}
    con.execute("CREATE OR REPLACE TEMP TABLE crate AS SELECT * FROM (VALUES " +
                ','.join(f"('{c}','{k}',{b},{r})" for (c, k, b), r in crates.items()) + ") v(country, kind2, bb, r)")
    con.execute("""CREATE OR REPLACE TEMP TABLE tw_c AS SELECT t.*, r.r FROM thesis_work t JOIN crate r
                   ON r.country=t.country AND r.kind2=t.kind2 AND r.bb = CASE WHEN t.band=1 THEN 1 WHEN t.band<5 THEN 2
                   WHEN t.band<10 THEN 5 WHEN t.band<50 THEN 10 ELSE 50 END""")
    cc = []
    for c in ('CA', 'US', 'GB', 'FR', 'BR', 'MX'):
        a = fetch(con, 'tw_c', f"country='{c}'", extra=('r',))
        obs = measures(a['i'])
        ip = measures(a['i'], 1.0 / a['r'])
        cc.append(dict(country=c, docs=int(a['d'].max() + 1), observed_top100=round(obs['top100_share'], 4),
                       ipw_top100=round(ip['top100_share'], 4), observed_gini=round(obs['gini'], 4),
                       ipw_gini=round(ip['gini'], 4), observed_top1pct=round(obs['top1pct_share'], 4),
                       ipw_top1pct=round(ip['top1pct_share'], 4)))
    pd.DataFrame(cc).to_csv(out('02-country-ipw.csv'), index=False)
    R.update(headline=head, simulations=sims, country_ipw=cc)
    out('02-summary.json').write_text(json.dumps(R, indent=1, default=float))
    for r in sims:
        print(r)
    for r in cc:
        print(r)


if __name__ == '__main__':
    main()
