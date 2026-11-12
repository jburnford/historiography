"""Analysis 3: national canons (theses by country: CA, US, GB, FR, BR, MX).

Share of a country's theses that cite a person (distinct theses citing any work credited to the person, divided by
the country's theses in the strict corpus) or a work.

Three routes from a citation to a person, so that unequal match rates can be seen:
- A  graph: corpus work matched to a graph work, credited through authored + edited (the main route);
- A-books: route A restricted to books (the kind with the most even match rates across countries is still uneven, but
  articles and chapters are where Brazil and France lose most);
- B  parsed name: the author name the corpus parser read from the bibliography, when it is an anchor (diss-person:)
  of a graph person key; needs no catalogue match, so translations and post-2016 books count.
Overlap between two countries: cosine similarity of the two countries' full share vectors (1 = the same profile of
who is cited how often, 0 = no one in common; no selection step), rank-biased overlap at depth 500 (RBO: agreement of
the two ranked lists weighted toward the top), and the Jaccard index (shared / union) of the top-100 and top-500
sets. (A Spearman correlation on the union of the two top-100 lists was tried and dropped: choosing the items by
'top in either country' makes it negative by construction.) Point values use all theses; intervals come from 50
equal draws of 500 theses per country, which also removes the advantage large countries have in stable top lists.
Universal vs local: people cited in all six countries vs only in one; computed on equal draws of 500 theses per
country (50 draws), because bigger countries mechanically have more local names.
"""
import json
from itertools import combinations

import numpy as np
import pandas as pd

from common import CORPUS, GRAPH, INITIAL_ONLY, connect, out
from conc import hows, pairs

CC = ['CA', 'US', 'GB', 'FR', 'BR', 'MX']
B = 500
TOPN = 50


def counts(con, table, where='true'):
    return con.execute(f"""SELECT country, item, count(DISTINCT doc) n FROM {table}
                           WHERE country IN {tuple(CC)} AND {where} GROUP BY 1,2""").df()


def rbo(la, lb, p=0.99, depth=500):
    """Rank-biased overlap (Webber et al. 2010), truncated at depth: a top-weighted agreement of two ranked lists,
    0 = disjoint, 1 = identical; p=0.99 puts about 86% of the weight on the first 200 ranks. Truncation makes it a
    lower bound."""
    sa, sb, s = set(), set(), 0.0
    for d in range(1, depth + 1):
        if d <= len(la):
            sa.add(la[d - 1])
        if d <= len(lb):
            sb.add(lb[d - 1])
        s += p ** (d - 1) * len(sa & sb) / d
    return (1 - p) * s


def overlap(shares):
    """shares: dict country -> Series(item -> share). Selection-free and top-weighted overlap measures:
    cosine similarity of the full share vectors (1 = same profile), RBO@500, Jaccard of top-100 / top-500 sets."""
    rows = []
    for a, b in combinations(CC, 2):
        sa, sb = shares[a], shares[b]
        u = sa.index.union(sb.index)
        va, vb = sa.reindex(u).fillna(0).values, sb.reindex(u).fillna(0).values
        cos = float(va @ vb / np.sqrt((va @ va) * (vb @ vb)))
        la, lb = list(sa.nlargest(500).index), list(sb.nlargest(500).index)
        ta, tb = set(la[:100]), set(lb[:100])
        rows.append(dict(a=a, b=b, cosine=cos, rbo500=rbo(la, lb), jaccard_top100=len(ta & tb) / len(ta | tb),
                         jaccard_top500=len(set(la) & set(lb)) / len(set(la) | set(lb))))
    return rows


def draws_overlap(p, R=50, n=500):
    """p: DataFrame doc, item, country. Overlap on equal draws of n theses per country (mean, 2.5/97.5 pct)."""
    docs_by_c = {c: p.loc[p.country == c, 'doc'].unique() for c in CC}
    acc = {}
    for s in range(R):
        g = np.random.default_rng(200 + s)
        sh = {}
        for c in CC:
            take = g.choice(docs_by_c[c], size=min(n, len(docs_by_c[c])), replace=False)
            q = p[p.doc.isin(set(take))]
            sh[c] = q.groupby('item')['doc'].nunique() / len(take)
        for r in overlap(sh):
            for k in ('cosine', 'rbo500', 'jaccard_top100', 'jaccard_top500'):
                acc.setdefault((r['a'], r['b'], k), []).append(r[k])
    rows = {}
    for (a, b, k), v in acc.items():
        d = rows.setdefault((a, b), dict(a=a, b=b))
        d[k], d[k + '_lo'], d[k + '_hi'] = np.mean(v), np.percentile(v, 2.5), np.percentile(v, 97.5)
    return list(rows.values())


def main():
    con = connect()
    pairs(con)
    ntheses = dict(con.execute("""SELECT d.country, count(DISTINCT c.did) FROM cit c JOIN diss d ON d.id=c.did
                                  GROUP BY 1""").fetchall())
    # route B: parsed author name -> graph person via diss-person anchors
    con.execute(f"""CREATE TEMP TABLE dpmap AS SELECT substr(a, 13) pk, key FROM
        (SELECT key, unnest(anchors) a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    con.execute(f"""CREATE TEMP TABLE route_b AS SELECT DISTINCT c.did AS doc, m.key AS item, d.country
        FROM cit c JOIN diss d ON d.id=c.did
        JOIN read_csv('{CORPUS}/authored.csv.gz', all_varchar=true) a ON a.work_id=c.work_id
        JOIN dpmap m ON m.pk=a.person_key WHERE NOT {INITIAL_ONLY.replace('person_key', 'a.person_key')}""")
    con.execute(f"""CREATE TEMP TABLE route_a_books AS SELECT DISTINCT t.doc, c.person AS item, t.country
        FROM thesis_work t JOIN cred c ON c.work=t.item WHERE c.how IN {hows()} AND t.kind2='book'""")
    con.execute("""CREATE TEMP TABLE route_ab AS SELECT doc, item, country FROM thesis_person
                   UNION SELECT doc, item, country FROM route_b""")
    people = con.execute("SELECT key, label, role, confidence, birth, death FROM person").df().set_index('key')
    works = None

    R = {'theses_per_country': ntheses}
    routes = {'A graph': 'thesis_person', 'A books only': 'route_a_books', 'B parsed name': 'route_b',
              'A or B': 'route_ab'}
    all_overlap, top_rows, uni_rows = [], [], []
    shares_by_route = {}
    for rname, table in routes.items():
        df = counts(con, table)
        df['share'] = df['n'] / df['country'].map(ntheses)
        shares = {c: df[df.country == c].set_index('item')['share'] for c in CC}
        shares_by_route[rname] = shares
        for r in overlap(shares):
            all_overlap.append(dict(route=rname, **r))
        for c in CC:
            top = shares[c].nlargest(TOPN)
            for rank, (k, s) in enumerate(top.items(), 1):
                p = people.loc[k] if k in people.index else None
                top_rows.append(dict(route=rname, country=c, rank=rank, key=k,
                                     label=None if p is None else p['label'], role=None if p is None else p['role'],
                                     share=round(s, 4), theses=int(round(s * ntheses[c]))))

    # route A with a historian-only role filter
    con.execute("""CREATE TEMP TABLE route_a_hist AS SELECT t.* FROM thesis_person t JOIN person p ON p.key=t.item
                   WHERE p.role='historian'""")
    df = counts(con, 'route_a_hist')
    df['share'] = df['n'] / df['country'].map(ntheses)
    sh = {c: df[df.country == c].set_index('item')['share'] for c in CC}
    for r in overlap(sh):
        all_overlap.append(dict(route='A graph, historians only', **r))

    # equal draws of 500 theses per country (size-fair overlap with intervals)
    draw_rows = []
    for rname, table in (('A graph', 'thesis_person'), ('B parsed name', 'route_b'), ('A or B', 'route_ab'),
                         ('A graph, historians only', 'route_a_hist')):
        p = con.execute(f"SELECT doc, item, country FROM {table} WHERE country IN {tuple(CC)}").df()
        for r in draws_overlap(p):
            draw_rows.append(dict(route=rname, **r))
    pd.DataFrame(draw_rows).round(4).to_csv(out('03-overlap-equal-draws.csv'), index=False)
    R['overlap_equal_draws'] = draw_rows
    pd.DataFrame(all_overlap).round(4).to_csv(out('03-overlap.csv'), index=False)
    pd.DataFrame(top_rows).to_csv(out('03-top-people-by-country.csv'), index=False)

    # universal vs local on equal draws of 500 theses per country
    for rname, table in (('A graph', 'thesis_person'), ('B parsed name', 'route_b'), ('A or B', 'route_ab'),
                         ('A graph, historians only', 'route_a_hist')):
        p = con.execute(f"""SELECT doc, item, country FROM {table} WHERE country IN {tuple(CC)}""").df()
        p['i'] = p['item'].astype('category').cat.codes
        docs_by_c = {c: p.loc[p.country == c, 'doc'].unique() for c in CC}
        acc = {c: [] for c in CC}
        for s in range(50):
            g = np.random.default_rng(100 + s)
            take = set()
            for c in CC:
                take.update(g.choice(docs_by_c[c], size=min(500, len(docs_by_c[c])), replace=False))
            q = p[p.doc.isin(take)]
            ncty = q.groupby('i')['country'].nunique()
            for c in CC:
                qc = q[q.country == c]
                k = ncty.reindex(qc['i'].values).values
                acc[c].append(((k == 6).mean(), (k == 1).mean(), len(qc) / qc.doc.nunique()))
        for c in CC:
            v = np.array(acc[c])
            uni_rows.append(dict(route=rname, country=c, universal_share=v[:, 0].mean(),
                                 universal_lo=np.percentile(v[:, 0], 2.5), universal_hi=np.percentile(v[:, 0], 97.5),
                                 local_share=v[:, 1].mean(), local_lo=np.percentile(v[:, 1], 2.5),
                                 local_hi=np.percentile(v[:, 1], 97.5), person_pairs_per_thesis=v[:, 2].mean()))
    pd.DataFrame(uni_rows).round(4).to_csv(out('03-universal-local.csv'), index=False)

    # named check: share of theses citing a few canon names, by route
    names = {'Foucault': "label ILIKE 'Michel Foucault'", 'Hobsbawm': "label ILIKE 'Eric Hobsbawm%' OR label ILIKE 'E. J. Hobsbawm'",
             'Bourdieu': "label ILIKE 'Pierre Bourdieu'", 'E. P. Thompson': "label ILIKE 'E. P. Thompson' OR label ILIKE 'Edward P. Thompson' OR label ILIKE 'E.P. Thompson'",
             'Le Goff': "label ILIKE 'Jacques Le Goff'", 'Chartier': "label ILIKE 'Roger Chartier'",
             'Anderson (Benedict)': "label ILIKE 'Benedict Anderson'", 'Said': "label ILIKE 'Edward W. Said' OR label ILIKE 'Edward Said'"}
    chk = []
    for nm, pred in names.items():
        keys = con.execute(f"SELECT key FROM person WHERE {pred}").fetchall()
        ks = tuple(k[0] for k in keys) + ('',)
        for rname, table in (('A graph', 'thesis_person'), ('B parsed name', 'route_b'), ('A or B', 'route_ab')):
            for c, n in con.execute(f"""SELECT country, count(DISTINCT doc) FROM {table} WHERE item IN {ks}
                                        AND country IN {tuple(CC)} GROUP BY 1""").fetchall():
                chk.append(dict(name=nm, keys=';'.join(ks[:-1]), route=rname, country=c, theses=n,
                                share=round(n / ntheses[c], 4)))
    pd.DataFrame(chk).to_csv(out('03-named-check.csv'), index=False)

    # works: top works per country (route A) + overlap
    wdf = counts(con, 'thesis_work')
    wdf['share'] = wdf['n'] / wdf['country'].map(ntheses)
    wsh = {c: wdf[wdf.country == c].set_index('item')['share'] for c in CC}
    wl = con.execute("SELECT key, label, year, kind FROM gw WHERE key IN (SELECT DISTINCT item FROM thesis_work)").df()
    wl = wl.set_index('key')
    wrows = []
    for c in CC:
        for rank, (k, s) in enumerate(wsh[c].nlargest(TOPN).items(), 1):
            wrows.append(dict(country=c, rank=rank, key=k, label=wl.label.get(k), year=wl.year.get(k),
                              share=round(s, 4)))
    pd.DataFrame(wrows).to_csv(out('03-top-works-by-country.csv'), index=False)
    # works overlap with the edition roll-up (the run's setting) and without it (each translation / later edition its
    # own node), all theses and on equal draws of 500 theses per country
    wov = [dict(rollup='as run', **r) for r in overlap(wsh)]
    wdraw = [dict(rollup='as run', **r) for r in draws_overlap(con.execute(
        f"SELECT doc, item, country FROM thesis_work WHERE country IN {tuple(CC)}").df())]
    pairs(con, rollup=False)
    w0 = counts(con, 'thesis_work')
    w0['share'] = w0['n'] / w0['country'].map(ntheses)
    wov += [dict(rollup='no roll-up', **r) for r in overlap({c: w0[w0.country == c].set_index('item')['share'] for c in CC})]
    wdraw += [dict(rollup='no roll-up', **r) for r in draws_overlap(con.execute(
        f"SELECT doc, item, country FROM thesis_work WHERE country IN {tuple(CC)}").df())]
    pairs(con)
    pd.DataFrame(wov).round(4).to_csv(out('03-overlap-works.csv'), index=False)
    pd.DataFrame(wdraw).round(4).to_csv(out('03-overlap-works-equal-draws.csv'), index=False)
    R['overlap_works'] = wov
    R['overlap_works_equal_draws'] = wdraw
    R['overlap'] = all_overlap
    R['universal_local'] = uni_rows
    out('03-summary.json').write_text(json.dumps(R, indent=1, default=float))
    print(pd.DataFrame(all_overlap).round(3).to_string())
    print(pd.DataFrame(uni_rows).round(3).to_string())
    print(pd.DataFrame(chk).to_string())


if __name__ == '__main__':
    main()
