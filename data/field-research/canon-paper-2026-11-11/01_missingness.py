"""Analysis 1: missingness (the paper's Table 1) and the analysis frames.

Unit: one strict citation = one (thesis, cited corpus work) row of strict-citations.csv.gz (3,050,449 rows).
'Matched' = the cited work reached a graph work through the older crosswalks, the LC / Crossref / OpenAlex /
Crossref-metadata crosswalks or a translation recovered to its original (reproduces export_cited_works.py of
2026-11-11 evening: 1,280,027 rows, 41.96%; compilations, corpus: works, are not counted, as in report.json).

Dimensions: thesis country, thesis decade, cited kind (as the bibliography parser typed it), cited decade (year as
cited), how theses label the cited work (cited_as: the label most of its citing theses give it, primary / secondary /
unspecified / mixed), and citing band (how many strict theses cite the work).

Frames (subsets in which comparisons are fairer), each with its match rate overall, by country and by kind.
Intervals: 95%, bootstrap over theses (500 Poisson resamples). Cells with < 100 citing theses are flagged.

Also: a person route that does not need a catalogue match: the corpus parses an author name for every citation
(authored.csv.gz); the share of citations whose parsed author is an anchor (diss-person:) of a graph person key.
"""
import json

import numpy as np

from common import CORPUS, GRAPH, INITIAL_ONLY, SMALL, boot_ratio, connect, out

T = """CREATE TEMP TABLE t AS
WITH band AS (SELECT work_id, count(DISTINCT did) n FROM cit GROUP BY 1)
SELECT c.did, c.work_id,
  CASE WHEN d.country IN ('CA','US','GB','FR','BR','MX') THEN d.country ELSE 'other' END AS country,
  coalesce(CAST(d.decade AS VARCHAR), 'no year') AS thesis_decade, d.year AS thesis_year,
  w.kind AS cited_kind, w.year AS cited_year,
  CASE WHEN w.year IS NULL THEN 'no year' WHEN w.year < 1800 THEN 'before 1800'
       WHEN w.year < 1900 THEN '1800s' WHEN w.year < 1950 THEN '1900-1949' ELSE CAST((w.year//10)*10 AS VARCHAR) END
       AS cited_decade,
  CASE WHEN w.prim > 0 AND w.prim >= 0.5*(w.prim+w.sec+w.unsp) THEN 'primary'
       WHEN w.sec > 0 AND w.sec >= 0.5*(w.prim+w.sec+w.unsp) THEN 'secondary'
       WHEN w.unsp > 0 AND w.unsp >= 0.5*(w.prim+w.sec+w.unsp) THEN 'unspecified' ELSE 'mixed' END AS cited_as,
  CASE WHEN b.n=1 THEN '1' WHEN b.n<5 THEN '2-4' WHEN b.n<10 THEN '5-9' WHEN b.n<50 THEN '10-49' ELSE '50+' END
       AS citing_band, b.n AS band_n,
  (x.work_id IS NOT NULL) AS m, coalesce(x.route,'unmatched') AS route, coalesce(x.comma,false) AS comma
FROM cit c JOIN diss d ON d.id=c.did JOIN cw w USING (work_id) JOIN band b USING (work_id)
LEFT JOIN xw x USING (work_id)"""

DIMS = ['country', 'thesis_decade', 'cited_kind', 'cited_decade', 'cited_as', 'citing_band']

# Frames: a SQL predicate on t
FRAMES = {
    'F0 all citations': 'true',
    'F1 not-primary works cited by 2+ theses': "cited_as <> 'primary' AND band_n >= 2",
    'F2 cited works published <=2015': 'cited_year <= 2015',
    'F3 books only (book, book_or_serial)': "cited_kind IN ('book','book_or_serial')",
    'F4 = F1 and F2 (scholarship frame)': "cited_as <> 'primary' AND band_n >= 2 AND cited_year <= 2015",
    'F5 = F4, books only': ("cited_as <> 'primary' AND band_n >= 2 AND cited_year <= 2015 "
                            "AND cited_kind IN ('book','book_or_serial')"),
    'F6 = F4, cited works 1950-2015, theses 2008+': ("cited_as <> 'primary' AND band_n >= 2 AND cited_year "
                                                     "BETWEEN 1950 AND 2015 AND thesis_year >= 2008"),
}


def cell_rates(con, where, dim):
    """rows: (value, citations, matched, theses, lo, hi) with bootstrap over theses."""
    rows = con.execute(f"""SELECT {dim} v, did, count(*) n, sum(m::INT) k FROM t WHERE {where}
                           GROUP BY ALL""").fetchnumpy()
    res = []
    vals = rows['v']
    for v in sorted(set(vals.tolist()), key=str):
        sel = vals == v
        n, k = rows['n'][sel], rows['k'][sel]
        lo, hi = boot_ratio(k, n)
        res.append(dict(value=v, citations=int(n.sum()), matched=int(k.sum()), rate=round(k.sum() / n.sum(), 4),
                        lo=round(lo, 4), hi=round(hi, 4), theses=int(sel.sum()), small=int(sel.sum()) < SMALL))
    return res


def write_rows(name, rows, keys):
    import csv
    with open(out(name + '.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})


def main():
    con = connect()
    con.execute(T)
    total = con.execute('SELECT count(*), sum(m::INT), count(DISTINCT did) FROM t').fetchone()
    print('total', total)
    keys = ['dimension', 'value', 'citations', 'matched', 'rate', 'lo', 'hi', 'theses', 'small']

    # Table 1: one dimension at a time
    t1 = []
    for dim in DIMS:
        for r in cell_rates(con, 'true', dim):
            t1.append(dict(dimension=dim, **r))
    write_rows('01-table1-missingness', t1, keys)

    # Cross tabs that carry the known biases
    con.execute("""CREATE TEMP VIEW tb AS SELECT *, CASE WHEN cited_kind IN ('book','book_or_serial') THEN 'book'
                   ELSE cited_kind END AS kind2,
                   CASE WHEN cited_year IS NULL THEN 'no year' WHEN cited_year < 1990 THEN '<1990'
                        WHEN cited_year < 2000 THEN '1990-99' WHEN cited_year < 2010 THEN '2000-09'
                        ELSE CAST(cited_year AS VARCHAR) END AS cy FROM t""")
    for a, b, name in (('kind2', 'country', 'kind_x_country'), ('kind2', 'cy', 'kind_x_citedyear'),
                       ('kind2', 'citing_band', 'kind_x_band'), ('cited_as', 'country', 'citedas_x_country'),
                       ('route', 'country', 'route_x_country')):
        if a == 'route':
            write_rows('01-cross-route-x-country', [dict(zip(['route', 'country', 'citations'], r)) for r in
                       con.execute("SELECT route, country, count(*) FROM t GROUP BY ALL ORDER BY 2,1").fetchall()],
                       ['route', 'country', 'citations'])
            continue
        rows = con.execute(f"""SELECT {a}, {b}, count(*) n, sum(m::INT) k, count(DISTINCT did) th
                               FROM tb GROUP BY ALL ORDER BY 1,2""").fetchall()
        write_rows(f'01-cross-{name.replace("_", "-")}',
                   [dict(a=x[0], b=x[1], citations=x[2], matched=x[3], rate=round(x[3] / x[2], 4), theses=x[4],
                         small=x[4] < SMALL) for x in rows], ['a', 'b', 'citations', 'matched', 'rate', 'theses', 'small'])

    # Frames
    fr, frc, frk = [], [], []
    for name, pred in FRAMES.items():
        n, k, th = con.execute(f'SELECT count(*), sum(m::INT), count(DISTINCT did) FROM t WHERE {pred}').fetchone()
        rows = con.execute(f"SELECT did, count(*) n, sum(m::INT) k FROM t WHERE {pred} GROUP BY 1").fetchnumpy()
        lo, hi = boot_ratio(rows['k'], rows['n'])
        fr.append(dict(frame=name, citations=n, share_of_all=round(n / total[0], 4), matched=k, rate=round(k / n, 4),
                       lo=round(lo, 4), hi=round(hi, 4), theses=th))
        for r in cell_rates(con, pred, 'country'):
            frc.append(dict(frame=name, **r))
        for r in cell_rates(con, pred, "CASE WHEN cited_kind IN ('book','book_or_serial') THEN 'book' ELSE cited_kind END"):
            frk.append(dict(frame=name, **r))
    write_rows('01-frames', fr, ['frame', 'citations', 'share_of_all', 'matched', 'rate', 'lo', 'hi', 'theses'])
    write_rows('01-frames-by-country', frc, ['frame'] + keys[1:])
    write_rows('01-frames-by-kind', frk, ['frame'] + keys[1:])
    # spread of country match rates inside each frame: max/min ratio over the six countries
    spread = {}
    for name in FRAMES:
        r = {x['value']: x['rate'] for x in frc if x['frame'] == name and x['value'] != 'other'}
        spread[name] = dict(rates=r, max_over_min=round(max(r.values()) / min(r.values()), 2),
                            range_points=round(100 * (max(r.values()) - min(r.values())), 1))

    # Person route without a catalogue match: parsed author name -> diss-person anchor of a graph person
    con.execute(f"""CREATE TEMP TABLE dp AS SELECT DISTINCT substr(a, 13) pk FROM
        (SELECT unnest(anchors) a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    con.execute(f"""CREATE TEMP TABLE wa AS SELECT work_id, bool_or(person_key IN (SELECT pk FROM dp)) has_person
        FROM read_csv('{CORPUS}/authored.csv.gz', all_varchar=true) WHERE NOT {INITIAL_ONLY} GROUP BY 1""")
    pr = con.execute("""SELECT country, count(*) n, sum(coalesce(wa.has_person,false)::INT) person_route,
                               sum(m::INT) work_route,
                               sum((m OR coalesce(wa.has_person,false))::INT) either
                        FROM t LEFT JOIN wa USING (work_id) GROUP BY ROLLUP(country) ORDER BY 1""").fetchall()
    write_rows('01-person-route-coverage',
               [dict(country=r[0] or 'all', citations=r[1], person_route=round(r[2] / r[1], 4),
                     work_route=round(r[3] / r[1], 4), either=round(r[4] / r[1], 4)) for r in pr],
               ['country', 'citations', 'person_route', 'work_route', 'either'])

    summary = dict(total_citations=total[0], matched=total[1], rate=round(total[1] / total[0], 4), theses=total[2],
                   frames=fr, country_spread_by_frame=spread)
    out('01-summary.json').write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
