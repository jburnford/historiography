"""Analysis 4: the thesis canon vs the journal-article canon, 2008-2020.

Citing documents: theses dated 2008-2020 and JSTOR articles dated 2008-2020, each counted when it has at least one
citation in the comparison universe. Comparison universe: keyed graph works only (the JSTOR matcher could only reach
works the key log held; the 2026-11-10 unkeyed `lccn:`/`doi:` works are reachable only from theses).
Person share = distinct documents citing any work credited to the person (authored + edited) / documents.
Agreement: cosine similarity of the full share vectors (1 = same profile); rank-biased overlap at depth 500 (RBO,
top-weighted list agreement); Jaccard of the top-100 / top-500 sets; Spearman rank correlation among people cited by
20+ documents on both sides (do the two corpora rank the people both know alike?).
Over-representation: log2 of (thesis share / article share), add-one smoothed, for people cited by 20+ documents on
either side. Split by role (historian / other scholar / primary source / unknown).
Variants: all theses vs all articles; English-language only (theses from the US, GB and English Canada vs articles
in journals not on the French / Italian / German / Spanish lists of canon_compare.py).
Intervals: bootstrap over documents (500 resamples, both corpora resampled).
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import connect, out
from conc import hows, pairs

FR = ['Revue', 'Annales', 'Vingti', 'Mouvement social', 'Clio. Femmes', '20 & 21', "L'Actualit", 'Etudes d', 'Mélanges',
      'Bulletin annuel']
IT = ['Archivio', 'Studi Storici', 'Quaderni']
DE = ['Geschichte und', 'Zeitschrift für', 'Historical Social Research', 'QUANTUM']
ES = ['Historia Social']
NONEN = FR + IT + DE + ES
B = 500


def rbo(la, lb, p=0.99, depth=500):
    """Rank-biased overlap truncated at depth (0 = disjoint, 1 = identical; top-weighted)."""
    sa, sb, acc = set(), set(), 0.0
    for d in range(1, depth + 1):
        if d <= len(la):
            sa.add(la[d - 1])
        if d <= len(lb):
            sb.add(lb[d - 1])
        acc += p ** (d - 1) * len(sa & sb) / d
    return (1 - p) * acc


def agree(st, sa, nt=None, na=None):
    """cosine of the full share vectors; RBO@500; Jaccard top-100/500; Spearman among people cited by 20+ documents
    on both sides (a common set chosen without favouring either side's top list)."""
    u = st.index.union(sa.index)
    vt, va = st.reindex(u).fillna(0).values, sa.reindex(u).fillna(0).values
    cos = float(vt @ va / np.sqrt((vt @ vt) * (va @ va)))
    lt, la = list(st.nlargest(500).index), list(sa.nlargest(500).index)
    j100 = len(set(lt[:100]) & set(la[:100])) / len(set(lt[:100]) | set(la[:100]))
    j500 = len(set(lt) & set(la)) / len(set(lt) | set(la))
    rho = np.nan
    if nt is not None:
        common = nt[nt >= 20].index.intersection(na[na >= 20].index)
        if len(common) > 10:
            rho = spearmanr(st.reindex(common).values, sa.reindex(common).values).statistic
    return cos, rbo(lt, la), j100, j500, rho


def main():
    con = connect()
    pairs(con)
    en_journal = ' AND '.join(f"position('{k.replace(chr(39), chr(39)*2)}' IN coalesce(ci.journal,''))=0" for k in NONEN)
    con.execute(f"""CREATE TEMP TABLE a_en AS SELECT key FROM citing ci WHERE ctype='article' AND {en_journal}""")
    con.execute("""CREATE TEMP TABLE t_en AS SELECT id FROM diss WHERE country IN ('US','GB')
                   OR country_detail='CA-other'""")
    variants = {
        'all': ("TRUE", "TRUE"),
        'English only': ("t.doc IN (SELECT id FROM t_en)", "a.doc IN (SELECT key FROM a_en)"),
    }
    people = con.execute("SELECT key, label, role FROM person").df().set_index('key')
    res, over_rows, role_rows, work_res = [], [], [], []
    for vname, (tw, aw) in variants.items():
        con.execute(f"""CREATE OR REPLACE TEMP TABLE tp AS SELECT DISTINCT t.doc, c.person item FROM thesis_work t
            JOIN gw ON gw.key=t.item AND gw.layer='keyed' JOIN cred c ON c.work=t.item
            WHERE c.how IN {hows()} AND t.year BETWEEN 2008 AND 2020 AND {tw}""")
        con.execute(f"""CREATE OR REPLACE TEMP TABLE ap AS SELECT DISTINCT a.doc, c.person item FROM article_work a
            JOIN gw ON gw.key=a.item AND gw.layer='keyed' JOIN cred c ON c.work=a.item
            WHERE c.how IN {hows()} AND a.year BETWEEN 2008 AND 2020 AND {aw}""")
        con.execute(f"""CREATE OR REPLACE TEMP TABLE twk AS SELECT DISTINCT t.doc, t.item FROM thesis_work t
            JOIN gw ON gw.key=t.item AND gw.layer='keyed' WHERE t.year BETWEEN 2008 AND 2020 AND {tw}""")
        con.execute(f"""CREATE OR REPLACE TEMP TABLE awk AS SELECT DISTINCT a.doc, a.item FROM article_work a
            JOIN gw ON gw.key=a.item AND gw.layer='keyed' WHERE a.year BETWEEN 2008 AND 2020 AND {aw}""")
        Nt = con.execute("SELECT count(DISTINCT doc) FROM twk").fetchone()[0]
        Na = con.execute("SELECT count(DISTINCT doc) FROM awk").fetchone()[0]
        pt = con.execute("SELECT count(*)::DOUBLE/count(DISTINCT doc) FROM twk").fetchone()[0]
        pa = con.execute("SELECT count(*)::DOUBLE/count(DISTINCT doc) FROM awk").fetchone()[0]
        for level, (T, A) in (('person', ('tp', 'ap')), ('work', ('twk', 'awk'))):
            t = con.execute(f"SELECT item, count(*) n FROM {T} GROUP BY 1").df().set_index('item')['n']
            a = con.execute(f"SELECT item, count(*) n FROM {A} GROUP BY 1").df().set_index('item')['n']
            st, sa = t / Nt, a / Na
            row = dict(variant=vname, level=level, theses=Nt, articles=Na, matched_works_per_thesis=round(pt, 1),
                       matched_works_per_article=round(pa, 1))
            K = ('cosine', 'rbo500', 'jaccard_top100', 'jaccard_top500', 'spearman_common20')
            row.update(dict(zip(K, agree(st, sa, t, a))))
            row['common20_people'] = len(t[t >= 20].index.intersection(a[a >= 20].index))
            # bootstrap over documents
            td = con.execute(f"SELECT dense_rank() OVER (ORDER BY doc)-1 d, item FROM {T}").df()
            ad = con.execute(f"SELECT dense_rank() OVER (ORDER BY doc)-1 d, item FROM {A}").df()
            cats = pd.Index(sorted(set(td['item']) | set(ad['item'])))
            ti, ai = cats.get_indexer(td['item']), cats.get_indexer(ad['item'])
            tdd, add = td['d'].values, ad['d'].values
            rng = np.random.default_rng(9)
            bs = []
            for _ in range(B):
                wt, wa = rng.poisson(1.0, tdd.max() + 1), rng.poisson(1.0, add.max() + 1)
                s1 = pd.Series(np.bincount(ti, weights=wt[tdd], minlength=len(cats)) / wt.sum(), index=cats)
                s2 = pd.Series(np.bincount(ai, weights=wa[add], minlength=len(cats)) / wa.sum(), index=cats)
                s1, s2 = s1[s1 > 0], s2[s2 > 0]
                bs.append(agree(s1, s2, s1 * wt.sum(), s2 * wa.sum()))
            bs = np.array(bs)
            for j, k in enumerate(K):
                row[k + '_lo'], row[k + '_hi'] = np.percentile(bs[:, j], [2.5, 97.5])
            res.append(row)
            print(row)
            if level == 'person':
                df = pd.DataFrame({'t': t, 'a': a}).fillna(0)
                df = df[(df.t >= 20) | (df.a >= 20)]
                df['thesis_share'] = df.t / Nt
                df['article_share'] = df.a / Na
                df['log2_ratio'] = np.log2(((df.t + 1) / (Nt + 1)) / ((df.a + 1) / (Na + 1)))
                df = df.join(people[['label', 'role']])
                df['role'] = df['role'].fillna('unknown')
                for side, d in (('thesis-heavy', df.nlargest(40, 'log2_ratio')),
                                ('article-heavy', df.nsmallest(40, 'log2_ratio'))):
                    for k, r in d.iterrows():
                        over_rows.append(dict(variant=vname, side=side, key=k, label=r.label, role=r.role,
                                              thesis_docs=int(r.t), thesis_share=round(r.thesis_share, 4),
                                              article_docs=int(r.a), article_share=round(r.article_share, 4),
                                              log2_ratio=round(r.log2_ratio, 2)))
                # role composition: share of person-document pairs and of top-500 slots, and median log ratio
                full = pd.DataFrame({'t': t, 'a': a}).fillna(0).join(people[['role']])
                full['role'] = full['role'].fillna('unknown')
                top_t = set(st.nlargest(500).index)
                top_a = set(sa.nlargest(500).index)
                for role, g in full.groupby('role'):
                    gg = g[(g.t >= 20) | (g.a >= 20)]
                    role_rows.append(dict(variant=vname, role=role,
                                          thesis_pair_share=round(g.t.sum() / full.t.sum(), 4),
                                          article_pair_share=round(g.a.sum() / full.a.sum(), 4),
                                          thesis_top500=len(top_t & set(g.index)),
                                          article_top500=len(top_a & set(g.index)),
                                          median_log2_ratio_20plus=round(float(np.median(np.log2(
                                              ((gg.t + 1) / (Nt + 1)) / ((gg.a + 1) / (Na + 1))))), 3) if len(gg) else None,
                                          people_20plus=len(gg)))
    pd.DataFrame(res).round(4).to_csv(out('04-agreement.csv'), index=False)
    pd.DataFrame(over_rows).to_csv(out('04-over-represented.csv'), index=False)
    pd.DataFrame(role_rows).to_csv(out('04-roles.csv'), index=False)
    out('04-summary.json').write_text(json.dumps(dict(agreement=res, roles=role_rows), indent=1, default=float))
    print(pd.DataFrame(role_rows).to_string())


if __name__ == '__main__':
    main()
