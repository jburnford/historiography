"""Data checks behind the findings memo: things that could inflate or deflate a person or work count.

- duplicate labels among the 1,000 most-cited person keys (route A), with the theses each key gets;
- people among the top 500 whose citing theses come mostly through EDITED credits (series editors, editions of
  older authors credited to the modern editor, or the reverse);
- top-200 people with role 'primary source' (check the role classifier) and theorists labelled 'historian';
- the most-cited corpus works that no crosswalk matched (where the biggest holes are);
- matched works dated after the thesis citing them, and works credited to many people;
- citation pairs whose cited graph year is later than the citing thesis year (2026-11-12: by first_year, and by the
  key year as before).
"""
import pandas as pd

from common import connect, out
from conc import hows, pairs


def main():
    con = connect()
    pairs(con)
    pd.set_option('display.width', 250)
    # theses per person, by credit type
    con.execute(f"""CREATE TEMP TABLE pc AS SELECT t.doc, c.person, min(c.how) how FROM thesis_work t
                   JOIN cred c ON c.work=t.item WHERE c.how IN {hows()} GROUP BY 1,2""")
    top = con.execute("""SELECT p.key, p.label, p.role, p.confidence, count(*) theses,
            sum((how IN ('edited','linked_edited'))::INT) via_edited_only, p.lcnaf, p.wd
        FROM pc JOIN person p ON p.key=pc.person GROUP BY ALL ORDER BY theses DESC LIMIT 1000""").df()
    top['rank'] = range(1, len(top) + 1)
    # duplicate labels: normalise to lower-case letters of the label
    top['norm'] = top['label'].str.lower().str.replace(r'[^a-z]', '', regex=True)
    allp = con.execute("""SELECT p.key, p.label, count(*) theses FROM pc JOIN person p ON p.key=pc.person
                          GROUP BY ALL HAVING count(*) >= 5""").df()
    allp['norm'] = allp['label'].str.lower().str.replace(r'[^a-z]', '', regex=True)
    dup = allp[allp.norm.isin(top.norm)].groupby('norm').filter(lambda g: len(g) > 1).sort_values(
        ['norm', 'theses'], ascending=[True, False])
    dup.to_csv(out('08-duplicate-labels-top1000.csv'), index=False)
    print('duplicate-label groups among top 1000:', dup.norm.nunique())
    print(dup.head(40).to_string())
    # edited-heavy
    ed = top[(top['rank'] <= 500) & (top.via_edited_only >= 0.5 * top.theses)]
    ed.to_csv(out('08-edited-heavy-top500.csv'), index=False)
    print('top-500 people with >= half their theses through EDITED only:', len(ed))
    print(ed[['rank', 'key', 'label', 'theses', 'via_edited_only', 'role']].head(30).to_string())
    # roles
    ps = top[(top['rank'] <= 200) & (top.role == 'primary source')]
    ps.to_csv(out('08-primary-source-role-top200.csv'), index=False)
    print('top-200 with role primary source:', len(ps))
    print(ps[['rank', 'key', 'label', 'theses', 'confidence']].to_string())
    rolemix = top.head(100).groupby('role').size()
    print('roles of the top 100:', rolemix.to_dict())
    top.drop(columns=['norm']).to_csv(out('08-top1000-people.csv'), index=False)
    # most-cited unmatched corpus works
    um = con.execute("""SELECT w.work_id, w.title, w.authors, w.year, w.kind, count(DISTINCT c.did) theses
        FROM cit c JOIN cw w USING (work_id) ANTI JOIN xw USING (work_id) GROUP BY ALL ORDER BY theses DESC
        LIMIT 100""").df()
    um.to_csv(out('08-top-unmatched-works.csv'), index=False)
    print(um.head(30)[['title', 'authors', 'year', 'kind', 'theses']].to_string())
    # works credited to many people
    many = con.execute(f"""SELECT work, count(DISTINCT person) n FROM cred WHERE how IN {hows()}
        GROUP BY 1 HAVING n >= 10""").df()
    mw = con.execute("""SELECT m.work, m.n people, gw.label, gw.year, count(DISTINCT t.doc) theses
        FROM many m JOIN gw ON gw.key=m.work LEFT JOIN thesis_work t ON t.item=m.work GROUP BY ALL
        ORDER BY theses DESC LIMIT 50""").df()
    mw.to_csv(out('08-works-many-credits.csv'), index=False)
    print('works with >=10 credited people:', len(many))
    print(mw.head(15).to_string())
    # anachronisms
    an = con.execute("""SELECT count(*) pairs, count(DISTINCT t.item) works FROM thesis_work t JOIN gw ON gw.key=t.item
        WHERE gw.year > t.year + 1""").fetchone()
    tot = con.execute("SELECT count(*) FROM thesis_work").fetchone()[0]
    print('graph-matched pairs where the cited work is dated 2+ years after the thesis:', an, 'of', tot)
    # 2026-11-12 rerun: gw.year is the first publication year (first_year) where the build has one; the key's own year
    # (key_year, sometimes a reprint year, class 17) gives the earlier measure
    an_k = con.execute("""SELECT count(*) pairs, count(DISTINCT t.item) works FROM thesis_work t JOIN gw ON gw.key=t.item
        WHERE gw.key_year > t.year + 1""").fetchone()
    print('the same by the key year:', an_k)
    ex = con.execute("""SELECT gw.key, gw.label, gw.year, min(t.year) first_citing, count(*) theses
        FROM thesis_work t JOIN gw ON gw.key=t.item WHERE gw.year > t.year + 1 GROUP BY ALL
        ORDER BY theses DESC LIMIT 30""").df()
    ex.to_csv(out('08-anachronistic-matches.csv'), index=False)
    print(ex.head(15).to_string())
    pd.DataFrame([dict(check='anachronistic pairs', value=an[0], of=tot),
                  dict(check='anachronistic works', value=an[1], of=None),
                  dict(check='anachronistic pairs by key year', value=an_k[0], of=tot),
                  dict(check='anachronistic works by key year', value=an_k[1], of=None),
                  dict(check='duplicate-label groups in top 1000', value=dup.norm.nunique(), of=1000),
                  dict(check='top-500 mostly via EDITED', value=len(ed), of=500),
                  dict(check='top-200 role primary source', value=len(ps), of=200)]).to_csv(
        out('08-checks-summary.csv'), index=False)


if __name__ == '__main__':
    main()
