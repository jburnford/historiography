"""LC + title numbers for the six general-class probes and London (place-nodes scoping pilot).

Titles are the raw word matches of title_probes.py (precision from the 40-title hand check in title-handcheck.csv);
LC is the subject heading on the graph book. Writes generic-probes.csv (counts) and generic-probes-top-people.csv
(top 15 people per probe by LC-tagged works, then title matches; title matches unchecked).
"""
import csv
import os
from pathlib import Path

import duckdb

G = Path('/home/jic823/historiography/build/graph')
D = Path(__file__).resolve().parent.parent
S = Path(os.environ['SCRATCH'])
EXCL = "('translator','introducer','edition-editor','series-editor','contributor')"
LC = {
    'London': r"heading = 'London (England)' OR (heading = 'London' AND parent = 'England') OR regexp_matches(heading, '\(London, England\)$')",
    'Bengal': r"regexp_matches(heading, '^(West |East )?Bengal( \(India\))?$') OR (regexp_matches(heading, '^(West )?Bengal$') AND parent = 'India')",
    'Danzig/Gdańsk': r"heading IN ('Gdańsk (Poland)', 'Gdańsk', 'Danzig') OR regexp_matches(heading, '\(Gdańsk, Poland\)$') OR (heading = 'Gdańsk' AND parent = 'Poland')",
    'Mediterranean': r"heading IN ('Mediterranean Region', 'Mediterranean Sea', 'Mediterranean Sea Region') OR heading LIKE 'Mediterranean Region%'",
    'Jamaica': r"heading = 'Jamaica' OR regexp_matches(heading, '\(Jamaica\)$') OR parent = 'Jamaica'",
    'Prairies': r"heading IN ('Prairie Provinces', 'Canada, Western')",
    'Normandy': r"heading = 'Normandy (France)' OR (heading = 'Normandy' AND parent = 'France') OR regexp_matches(heading, '\(France : Normandy\)')",
}


def main():
    c = duckdb.connect()
    c.execute("set memory_limit='4GB'; set threads=4")
    c.execute(f"CREATE TABLE lc AS SELECT * FROM '{S}/lcout/heads-grounded.parquet'")
    c.execute(f"""CREATE TABLE au AS SELECT DISTINCT "from" AS person, "to" AS work FROM '{G}/authored.parquet'
                  WHERE coalesce(role,'author') NOT IN {EXCL}""")
    c.execute(f"CREATE TABLE p AS SELECT key, label FROM '{G}/person.parquet'")
    c.execute(f"CREATE TABLE w AS SELECT key, label, kind FROM '{G}/work.parquet'")
    out, top = [], []
    for probe, cond in LC.items():
        c.execute(f"CREATE OR REPLACE TABLE lw AS SELECT DISTINCT key AS work FROM lc WHERE {cond}")
        c.execute(f"CREATE OR REPLACE TABLE tw AS SELECT DISTINCT key AS work FROM '{S}/title-matches.parquet' WHERE probe = '{probe}'")
        n = c.execute("""SELECT (SELECT count(*) FROM lw), (SELECT count(*) FROM tw),
                 (SELECT count(*) FROM lw WHERE work IN (SELECT work FROM tw)),
                 (SELECT count(*) FROM (SELECT work FROM lw UNION SELECT work FROM tw)),
                 (SELECT count(DISTINCT person) FROM au WHERE work IN (SELECT work FROM lw)),
                 (SELECT count(*) FROM (SELECT person FROM au WHERE work IN (SELECT work FROM lw) GROUP BY 1 HAVING count(*) >= 2)),
                 (SELECT count(DISTINCT person) FROM au WHERE work IN (SELECT work FROM tw)),
                 (SELECT count(*) FROM (SELECT person FROM au WHERE work IN (SELECT work FROM tw) GROUP BY 1 HAVING count(*) >= 2))""").fetchone()
        out.append([probe, *n])
        for i, r in enumerate(c.execute("""SELECT a.person, p.label, count(*) FILTER (WHERE a.work IN (SELECT work FROM lw)) n_lc,
                 count(*) FILTER (WHERE a.work IN (SELECT work FROM tw)) n_title, any_value(w.label)
                 FROM au a JOIN p ON p.key = a.person JOIN w ON w.key = a.work
                 WHERE a.work IN (SELECT work FROM lw UNION SELECT work FROM tw) GROUP BY ALL
                 ORDER BY n_lc DESC, n_title DESC LIMIT 15""").fetchall(), 1):
            top.append([probe, i, *r])
    with open(D / 'generic-probes.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['probe', 'works_lc', 'works_title_raw', 'works_both', 'works_union', 'people_lc_ge1', 'people_lc_ge2', 'people_title_ge1', 'people_title_ge2'])
        wr.writerows(out)
    with open(D / 'generic-probes-top-people.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['probe', 'rank', 'person', 'label', 'works_lc', 'works_title_unchecked', 'example_title'])
        wr.writerows(top)
    for r in out:
        print(r)


if __name__ == '__main__':
    main()
