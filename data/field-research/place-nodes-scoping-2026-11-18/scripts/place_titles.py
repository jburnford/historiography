"""Title matches for the gazetteer places (Ceylon, Saskatchewan, Canada) over all graph work nodes.

    SCRATCH=... python3 place_titles.py   # -> SCRATCH/place-title-matches.parquet
"""
import os
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gazetteer import CANADA, CEYLON, SASKATCHEWAN  # noqa: E402

G = Path('/home/jic823/historiography/build/graph')
SCRATCH = Path(os.environ['SCRATCH'])
EXCL = "('translator','introducer','edition-editor','series-editor','contributor')"


def main():
    c = duckdb.connect()
    c.execute("set memory_limit='4GB'; set threads=4")
    c.execute(f"CREATE TEMP TABLE w AS SELECT key, label, kind, year, journal FROM '{G}/work.parquet' WHERE label IS NOT NULL")
    parts = []
    for region, gaz in (('ceylon', CEYLON), ('saskatchewan', SASKATCHEWAN), ('canada', CANADA)):
        for place, (qid, parent, rx) in gaz.items():
            p = place.replace("'", "''")
            parts.append(f"SELECT '{region}' region, '{p}' place, {repr(qid) if qid else 'NULL'} qid, key, label, kind, year, journal "
                         f"FROM w WHERE regexp_matches(label, '{rx.replace(chr(39), chr(39)*2)}')")
    c.execute('CREATE TEMP TABLE m AS ' + ' UNION ALL '.join(parts))
    c.execute(f"""CREATE TEMP TABLE a AS SELECT DISTINCT a."from" AS person, a."to" AS work, p.label AS plabel
                  FROM '{G}/authored.parquet' a LEFT JOIN '{G}/person.parquet' p ON p.key = a."from"
                  WHERE coalesce(a.role,'author') NOT IN {EXCL} AND a."to" IN (SELECT key FROM m)""")
    c.execute(f"""COPY (SELECT m.*, (SELECT list(person ORDER BY person) FROM a WHERE a.work=m.key) people,
                  (SELECT list(person || ' ' || coalesce(plabel,'') ORDER BY person) FROM a WHERE a.work=m.key) people_labels
                  FROM m) TO '{SCRATCH}/place-title-matches.parquet'""")
    print(c.sql("SELECT region, place, count(*) n, count(DISTINCT key) works FROM m GROUP BY ALL ORDER BY 1, 3 DESC"))


if __name__ == '__main__':
    main()
