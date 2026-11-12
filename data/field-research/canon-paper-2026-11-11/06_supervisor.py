"""Analysis 6: the supervisor effect. How often does a thesis cite its own supervisor, compared with how often
theses from the same institution and decade, supervised by someone else, cite that same person?

Unit: a (thesis, supervisor) pair from SUPERVISED edges, for theses in the strict corpus. Comparison pairs: every
other thesis of the same institution and decade (not supervised by that person) with the same supervisor. Holding
the supervisor fixed holds fixed how findable their works are in the graph (match rates differ a lot by person).
Field is not available for most theses (the subfield topic model covers Canada only), so it is not matched on.

Citation detection, two routes: A graph (matched works credited by authored + edited); A+linked; A or B (B = the
author name parsed from the bibliography is an anchor of the supervisor's key: no catalogue match needed).
Effect sizes: own rate, peer rate, difference (percentage points) and ratio (own / peer). 95% intervals from a
bootstrap over theses (500 Poisson resamples; a thesis's own and peer rows move together).
Restriction: supervisors with at least one detectable work (cited by any corpus thesis by that route), since
otherwise neither rate can be above zero.
"""
import json

import numpy as np
import pandas as pd

from common import CORPUS, GRAPH, INITIAL_ONLY, SMALL, connect, out
from conc import pairs

B = 500


def main():
    con = connect()
    pairs(con)
    con.execute(f"""CREATE TEMP TABLE dpmap AS SELECT substr(a, 13) pk, key FROM
        (SELECT key, unnest(anchors) a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    con.execute(f"""CREATE TEMP TABLE route_b AS SELECT DISTINCT c.did AS doc, m.key AS item FROM cit c
        JOIN read_csv('{CORPUS}/authored.csv.gz', all_varchar=true) a ON a.work_id=c.work_id
        JOIN dpmap m ON m.pk=a.person_key WHERE NOT {INITIAL_ONLY.replace('person_key', 'a.person_key')}""")
    con.execute("""CREATE TEMP TABLE linked_p AS SELECT DISTINCT t.doc, c.person item FROM thesis_work t
        JOIN cred c ON c.work=t.item""")
    routes = {'A graph': "SELECT doc, item FROM thesis_person",
              'A+linked': "SELECT doc, item FROM linked_p",
              'A or B': "SELECT doc, item FROM thesis_person UNION SELECT doc, item FROM route_b"}
    # theses in the strict corpus with institution + decade, and their supervisors
    con.execute("""CREATE TEMP TABLE th AS SELECT DISTINCT d.id did, d.institution, d.decade FROM diss d
                   WHERE d.id IN (SELECT did FROM cit) AND d.decade IS NOT NULL AND d.institution IS NOT NULL""")
    con.execute("""CREATE TEMP TABLE sp AS SELECT DISTINCT tk.did, s.person sup FROM supervised s
                   JOIN tk ON tk.key=s.thesis JOIN th ON th.did=tk.did""")
    nsp = con.execute("SELECT count(*), count(DISTINCT did), count(DISTINCT sup) FROM sp").fetchone()
    print('supervised pairs, theses, supervisors:', nsp)
    con.execute("""CREATE TEMP TABLE cell_sup AS SELECT DISTINCT th.institution, th.decade, sp.sup
                   FROM sp JOIN th USING (did)""")
    # all (thesis, supervisor) rows in the cell: own = supervised by sup, peer = not
    con.execute("""CREATE TEMP TABLE rows_ AS
        SELECT th.did, cs.sup, th.institution, th.decade, (sp.did IS NOT NULL) AS own
        FROM cell_sup cs JOIN th USING (institution, decade) LEFT JOIN sp ON sp.did=th.did AND sp.sup=cs.sup""")
    nrows = con.execute("SELECT own, count(*) FROM rows_ GROUP BY 1").fetchall()
    print('rows', nrows)
    # topical peers: a peer thesis sharing >= 3 cited graph works (not counting the supervisor's own works) with one
    # of the supervisor's students in the same institution and decade (bibliographic coupling as a stand-in for field)
    con.execute("""CREATE TEMP TABLE pairs_ AS SELECT DISTINCT o.sup, o.did own_did, p.did peer_did FROM rows_ o
        JOIN rows_ p ON o.sup=p.sup AND o.institution=p.institution AND o.decade=p.decade WHERE o.own AND NOT p.own""")
    con.execute("""CREATE TEMP TABLE supworks AS SELECT DISTINCT c.person sup, c.work FROM cred c
        WHERE c.person IN (SELECT sup FROM sp)""")
    con.execute("""CREATE TEMP TABLE coup AS SELECT pr.sup, pr.peer_did, max(n) shared FROM (
            SELECT pr.sup, pr.own_did, pr.peer_did, count(*) n FROM pairs_ pr
            JOIN thesis_work a ON a.doc=pr.own_did JOIN thesis_work b ON b.doc=pr.peer_did AND b.item=a.item
            ANTI JOIN supworks sw ON sw.sup=pr.sup AND sw.work=a.item
            GROUP BY ALL) pr GROUP BY ALL""")
    print('coupled peer rows (>=3 shared works):', con.execute("SELECT count(*) FROM coup WHERE shared>=3").fetchone())
    res = []
    by_country = []
    designs = [(r, det, peers) for r in routes for det in ('any citation', 'cited outside own students')
               for peers in ('institution-decade', 'topical (>=3 shared works)')]
    for rname, det, peers in designs:
        sql = routes[rname]
        con.execute(f"CREATE OR REPLACE TEMP TABLE cites_ AS {sql}")
        if det == 'any citation':
            con.execute("""CREATE OR REPLACE TEMP TABLE detectable AS SELECT DISTINCT item FROM cites_""")
        else:   # the supervisor is cited by at least one thesis they did not supervise (no selection on the outcome)
            con.execute("""CREATE OR REPLACE TEMP TABLE detectable AS SELECT DISTINCT c.item FROM cites_ c
                           ANTI JOIN sp ON sp.did=c.doc AND sp.sup=c.item""")
        pf = '' if peers == 'institution-decade' else """AND (r.own OR EXISTS (SELECT 1 FROM coup k
                 WHERE k.sup=r.sup AND k.peer_did=r.did AND k.shared >= 3))"""
        df = con.execute(f"""SELECT r.did, r.sup, r.own, (c.doc IS NOT NULL) AS cited, r.institution, r.decade,
                                   d.country
            FROM rows_ r JOIN detectable dt ON dt.item=r.sup
            LEFT JOIN cites_ c ON c.doc=r.did AND c.item=r.sup JOIN diss d ON d.id=r.did WHERE TRUE {pf}""").df()
        scopes = [('all', df)]
        if det == 'cited outside own students' and peers == 'institution-decade':
            scopes += [(c, df[df.country == c]) for c in ('CA', 'US', 'GB', 'FR', 'BR', 'MX')]
        for scope, d in scopes:
            own, peer = d[d.own], d[~d.own]
            if len(own) == 0 or len(peer) == 0:
                continue
            ro, rp = own.cited.mean(), peer.cited.mean()
            # bootstrap over theses
            docs, inv = np.unique(d['did'].values, return_inverse=True)
            isown, cited = d['own'].values, d['cited'].values.astype(float)
            rng = np.random.default_rng(17)
            diffs, ratios, ros, rps = [], [], [], []
            for _ in range(B):
                w = rng.poisson(1.0, len(docs))[inv].astype(float)
                a = (w * cited * isown).sum() / max((w * isown).sum(), 1e-9)
                b = (w * cited * ~isown).sum() / max((w * ~isown).sum(), 1e-9)
                ros.append(a)
                rps.append(b)
                diffs.append(a - b)
                ratios.append(a / b if b > 0 else np.nan)
            row = dict(route=rname, detectable=det, peers=peers, scope=scope, own_pairs=len(own), own_theses=own.did.nunique(),
                       supervisors=own.sup.nunique(), peer_pairs=len(peer), small=own.did.nunique() < SMALL,
                       own_rate=round(ro, 4), own_lo=round(np.percentile(ros, 2.5), 4),
                       own_hi=round(np.percentile(ros, 97.5), 4), peer_rate=round(rp, 5),
                       peer_lo=round(np.percentile(rps, 2.5), 5), peer_hi=round(np.percentile(rps, 97.5), 5),
                       diff_points=round(100 * (ro - rp), 2), diff_lo=round(100 * np.percentile(diffs, 2.5), 2),
                       diff_hi=round(100 * np.percentile(diffs, 97.5), 2),
                       ratio=round(ro / rp, 1) if rp > 0 else None,
                       ratio_lo=round(np.nanpercentile(ratios, 2.5), 1), ratio_hi=round(np.nanpercentile(ratios, 97.5), 1))
            (res if scope == 'all' else by_country).append(row)
            print(row)
    # Does the effect depend on how cited the supervisor is overall? (A or B route, all)
    con.execute("CREATE OR REPLACE TEMP TABLE cites_ AS " + routes['A or B'])
    df = con.execute("""WITH pop AS (SELECT item, count(*) n FROM cites_ GROUP BY 1)
        SELECT r.did, r.own, (c.doc IS NOT NULL) cited, p.n,
               CASE WHEN p.n < 5 THEN '1-4' WHEN p.n < 20 THEN '5-19' WHEN p.n < 100 THEN '20-99' ELSE '100+' END band
        FROM rows_ r JOIN pop p ON p.item=r.sup LEFT JOIN cites_ c ON c.doc=r.did AND c.item=r.sup""").df()
    pop_rows = []
    for band, d in df.groupby('band'):
        pop_rows.append(dict(supervisor_citing_theses=band, own_theses=d[d.own].did.nunique(),
                             own_rate=round(d[d.own].cited.mean(), 4), peer_rate=round(d[~d.own].cited.mean(), 5)))
    pd.DataFrame(res).to_csv(out('06-supervisor.csv'), index=False)
    pd.DataFrame(by_country).to_csv(out('06-supervisor-by-country.csv'), index=False)
    pd.DataFrame(pop_rows).to_csv(out('06-supervisor-by-popularity.csv'), index=False)
    out('06-summary.json').write_text(json.dumps(dict(pairs=nsp, rows=nrows, all=res, by_country=by_country,
                                                      by_popularity=pop_rows), indent=1, default=str))
    print(pd.DataFrame(pop_rows))


if __name__ == '__main__':
    main()
