"""Title matches for the place probes over all graph work nodes; random samples for hand checking.

    python3 title_probes.py match    # build/graph -> SCRATCH/title-matches.parquet + counts
    python3 title_probes.py sample   # 40 random matches per probe -> hand-check CSV (seed 20261118)
"""
import csv
import json
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path('/home/jic823/historiography')
G = ROOT / 'build/graph'
OUT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get('SCRATCH', '/tmp'))

# probe -> case-sensitive regex on the title (word-bounded); the class each probe stands for
PROBES = {
    'London': (r'\bLondon\b', 'huge city; namesakes (Jack London), London Ontario, venues'),
    'Ceylon/Sri Lanka': (r'\b(Ceylon|Sri Lanka|Lanka)\b', 'renamed colony/polity'),
    'Saskatchewan': (r'\bSaskatchewan\b', 'province with child places; river of same name'),
    'Prince Albert': (r'\bPrince Albert\b', 'small town colliding with a person name'),
    'Bengal': (r'\bBengal', 'region without fixed borders (presidency, province, partition)'),
    'Danzig/Gdańsk': (r'\b(Danzig|Gdańsk|Gdansk|Dantzig)\b', 'city renamed across languages'),
    'Mediterranean': (r'\b(Mediterranean|Méditerranée|Mediterráneo|Mittelmeer)', 'sea / maritime region'),
    'Jamaica': (r'\bJamaica', 'colony to state; namesakes (Jamaica, Queens)'),
    'Prairies': (r'\b[Pp]rairies?\b', 'vague region; common noun'),
    'Normandy': (r'\b(Normandy|Normandie|normand|Normand)', 'non-English titles; adjective forms'),
}
EXCLUDED_ROLES = "('translator','introducer','edition-editor','series-editor','contributor')"


def con():
    c = duckdb.connect()
    c.execute("set memory_limit='4GB'; set threads=4")
    return c


def match():
    c = con()
    cases = ' UNION ALL '.join(
        f"SELECT '{p}' AS probe, key, label, kind, year, journal FROM w WHERE regexp_matches(label, '{rx}')"
        for p, (rx, _) in PROBES.items())
    c.execute(f"""CREATE TEMP TABLE w AS SELECT key, label, kind, year, journal FROM '{G}/work.parquet'
                  WHERE label IS NOT NULL""")
    c.execute(f"CREATE TEMP TABLE m AS {cases}")
    c.execute(f"""CREATE TEMP TABLE a AS SELECT DISTINCT "from" AS person, "to" AS work FROM '{G}/authored.parquet'
                  WHERE coalesce(role,'author') NOT IN {EXCLUDED_ROLES} AND "to" IN (SELECT key FROM m)""")
    c.execute(f"""COPY (SELECT m.*, (SELECT list(person ORDER BY person) FROM a WHERE a.work = m.key) AS people
                  FROM m) TO '{SCRATCH}/title-matches.parquet'""")
    total = c.execute("SELECT count(*), count_if(key LIKE 'w-%') FROM w").fetchone()
    rows = c.execute(f"""SELECT probe, count(*), count(DISTINCT key) FILTER (WHERE key IN (SELECT work FROM a)),
                         (SELECT count(DISTINCT person) FROM a JOIN m m2 ON a.work = m2.key WHERE m2.probe = m.probe)
                         FROM m GROUP BY probe ORDER BY 2 DESC""").fetchall()
    by_kind = c.execute("SELECT probe, kind, count(*) FROM m GROUP BY ALL ORDER BY 1, 3 DESC").fetchall()
    res = dict(work_nodes_with_label=total[0], keyed_w=total[1],
               probes={p: dict(titles=n, titles_with_keyed_author=k, keyed_people=pp) for p, n, k, pp in rows},
               by_kind={})
    for p, k, n in by_kind:
        res['by_kind'].setdefault(p, {})[k] = n
    print(json.dumps(res, indent=1))
    (SCRATCH / 'title-counts.json').write_text(json.dumps(res, indent=1))


def sample():
    c = con()
    rows = c.execute(f"""SELECT probe, key, kind, year, journal, label, len(people) FROM (
          SELECT *, row_number() OVER (PARTITION BY probe ORDER BY hash(key || '20261118')) AS r
          FROM '{SCRATCH}/title-matches.parquet') WHERE r <= 40 ORDER BY probe, r""").fetchall()
    with open(OUT / 'title-handcheck.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['probe', 'key', 'kind', 'year', 'journal', 'title', 'keyed_people', 'class', 'note'])
        for r in rows:
            w.writerow(list(r) + ['', ''])
    print(len(rows))


if __name__ == '__main__':
    {'match': match, 'sample': sample}[sys.argv[1]]()
