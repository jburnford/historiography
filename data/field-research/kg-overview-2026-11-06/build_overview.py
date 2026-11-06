"""Scope and depth of the historiography knowledge graph: counts for the overview infographic (2026-11-06).

Reads the local graph build (build/graph/*.parquet, from scripts/build_graph.py) and the dissertation corpus
tables (dissertations.csv, works.csv, strict-citations.csv.gz; counts only, no thesis text). Also reads data/person-facts/person-roles.csv.gz (scripts/person_roles.py) and dup-bound.json (dup_bound.py).
Writes stats.json
and kg-overview.html (template.html with the counts embedded) beside this script.

    python3 data/field-research/kg-overview-2026-11-06/build_overview.py
"""
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
G = ROOT / 'build/graph'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'


def main():
    db = duckdb.connect()
    one = lambda q: db.execute(q).fetchone()
    report = json.loads((G / 'report.json').read_text())
    s = {}
    # people
    total, orcid, wd, lc, gnd, viaf, isni, idref, any_pid = one(f"""SELECT count(*), count(orcid), count(wd), count(lcnaf),
        count(gnd), count(viaf), count(isni), count(idref),
        count(*) FILTER (WHERE coalesce(orcid, wd, lcnaf, gnd, viaf, isni, idref) IS NOT NULL) FROM '{G}/person.parquet'""")
    res = dict(db.execute(f"SELECT resolution, count(*) FROM '{G}/person.parquet' GROUP BY 1").fetchall())
    s['people'] = dict(total=total, with_public_id=any_pid, established=res.get('established', 0),
                       recorded=res.get('recorded', 0), unresolved=res.get('unresolved', 0),
                       ids={'Library of Congress': lc, 'GND (German National Library)': gnd, 'VIAF': viaf,
                            'ISNI': isni, 'Wikidata': wd, 'ORCID': orcid, 'IdRef (France)': idref})
    # works: reviews are review works whatever their catalogue kind (JSTOR and Crossref reviews are 'article')
    rows = db.execute(f"""SELECT CASE
            WHEN key IN (SELECT "from" FROM '{G}/reviews.parquet') OR len(reviewer_names) > 0 THEN 'Book reviews'
            WHEN kind = 'book' THEN 'Books (LC catalogue)'
            WHEN kind = 'article' THEN 'Journal articles'
            WHEN kind = 'thesis' THEN 'Doctoral theses'
            WHEN kind = 'other' AND list_bool_or([a LIKE 'orcid-work:%' FOR a IN anchors]) THEN 'Works listed on ORCID records (type not given)'
            WHEN kind = 'other' AND list_bool_or([a LIKE 'hnet-book:%' FOR a IN anchors]) THEN 'Books reviewed on H-Net'
            WHEN kind = 'atlas_source' THEN 'Atlas sources'
            ELSE 'Other' END k, count(*) FROM '{G}/work.parquet' GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    s['works'] = dict(total=sum(n for _, n in rows), by_kind=dict(rows))
    s['works']['articles_recorded'] = one(f"SELECT count(*) FROM '{G}/work.parquet' WHERE kind = 'article' AND resolution = 'recorded' AND len(reviewer_names) = 0 AND key NOT IN (SELECT \"from\" FROM '{G}/reviews.parquet')")[0]
    # roles (scripts/person_roles.py) and the duplicate bound (dup_bound.py)
    roles = db.execute(f"SELECT role, count(*) FROM read_csv_auto('{ROOT}/data/person-facts/person-roles.csv.gz') GROUP BY 1 ORDER BY 2 DESC").fetchall()
    signals = db.execute(f"""SELECT s, count(*) FROM (SELECT unnest(string_split(signals, ';')) s
        FROM read_csv_auto('{ROOT}/data/person-facts/person-roles.csv.gz', all_varchar=true) WHERE signals IS NOT NULL) GROUP BY 1""").fetchall()
    s['people']['roles'] = dict(roles)
    s['people']['signals'] = dict(signals)
    s['people']['duplicates'] = json.loads((HERE / 'dup-bound.json').read_text())
    s['institutions'] = report['Institution']
    # relations
    s['edges'] = {k: v for k, v in report.items() if k.isupper()}
    # reviews
    s['reviews'] = dict(total=s['works']['by_kind']['Book reviews'],
                        with_keyed_reviewer=one(f"SELECT count(DISTINCT review) FROM '{G}/reviewed.parquet'")[0],
                        printed_reviewer_names=one(f"SELECT sum(len(reviewer_names)) FROM '{G}/work.parquet'")[0])
    # dissertation corpus (counts only)
    d = f"read_csv_auto('{CORPUS}/dissertations.csv')"
    s['corpus'] = dict(
        records=one(f"SELECT count(*) FROM {d}")[0],
        parsed=one(f"SELECT count(*) FROM {d} WHERE bibliography_entries > 0")[0],
        in_analysis=one(f"SELECT count(*) FROM {d} WHERE in_analysis")[0],
        bibliography_entries=one(f"SELECT sum(bibliography_entries) FROM {d}")[0],
        by_country=dict(db.execute(f"SELECT coalesce(country, '?'), count(*) FROM {d} WHERE in_analysis GROUP BY 1 ORDER BY 2 DESC").fetchall()),
        distinct_cited_works=one(f"SELECT count(*) FROM read_csv_auto('{CORPUS}/works.csv')")[0],
        corpus_citations=one(f"SELECT count(*) FROM read_csv_auto('{CORPUS}/strict-citations.csv.gz')")[0],
        theses_citing_in_graph=one(f"SELECT count(DISTINCT \"from\") FROM '{G}/cites.parquet'")[0],
        keyed_cited_works=one(f"SELECT count(DISTINCT \"to\") FROM '{G}/cites.parquet'")[0])
    s['built'] = '2026-11-06'
    (HERE / 'stats.json').write_text(json.dumps(s, indent=1, ensure_ascii=False) + '\n')
    page = (HERE / 'template.html').read_text().replace('/*STATS*/null', json.dumps(s, ensure_ascii=False))
    (HERE / 'kg-overview.html').write_text(page)
    print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
