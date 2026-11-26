"""Scope and depth of the historiography knowledge graph: counts for the overview infographic.

First built 2026-11-06; reworked 2026-11-26 for the graph of 2026-11-25 (two layers of works, several citing sources,
places, prizes, institutions and affiliations, reviews by year, known limits as tracked numbers, growth since
2026-11-07).

Reads the local graph build (build/graph/*.parquet and report.json, from scripts/build_graph.py; never rebuilt here)
and the dissertation corpus tables (dissertations.csv, works.csv, strict-citations.csv.gz; counts only, no thesis
text). Also reads data/person-facts/person-roles.csv.gz (scripts/person_roles.py), data/person-facts/life-years.csv.gz
(scripts/build_life_years.py) and dup-bound.json (dup_bound.py beside this script); rerun those two first so they
cover the same build. Every query is an aggregate in DuckDB (memory capped at 4 GB); no table is loaded into Python.

Writes stats.json and kg-overview.html (template.html with the counts embedded; self-contained, no outside scripts,
fonts or tiles) beside this script.

Works come in two layers (build_graph.py, 2026-11-10): works with a key in the key log (resolution established or
recorded) and unkeyed works, held as references only (cited works matched to LC, OpenAlex or Crossref; works on the
ORCID/OpenAlex profiles of keyed people; Crossref citing articles; volumes named by chapter records). Kinds on the page
are exclusive: a review is any work recorded as a review, proposed as one by a matched record, carrying printed
reviewer names, or reviewing a book (REVIEWS); a work recorded as 'other' (type not given) takes the kind a matched
record proposes (kind_proposed); everything else keeps its recorded kind.

    python3 scripts/person_roles.py
    python3 data/field-research/kg-overview-2026-11-06/dup_bound.py
    python3 data/field-research/kg-overview-2026-11-06/build_overview.py
"""
import datetime
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
G = ROOT / 'build/graph'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LIFE_YEARS = ROOT / 'data/person-facts/life-years.csv.gz'   # scripts/build_life_years.py
ROLES = ROOT / 'data/person-facts/person-roles.csv.gz'      # scripts/person_roles.py

# The page of 2026-11-07 (git: this folder's stats.json at 55fcab5e), for the growth comparison. Its relation total
# summed 13 relation kinds; the same kinds are summed now for a like-for-like figure.
BASELINE = dict(built='2026-11-07', people=231229, works=1819820, institutions=1235, reviews=420813,
                cites=1465722, dissertations=13996, relations=3750745,
                relation_kinds=['ADVISED', 'AUTHORED', 'AWARDED_BY', 'CITES', 'COAUTHORED', 'COEDITED', 'EDITED',
                                'EDITOR_OF', 'PART_OF', 'PUBLISHED_AS', 'REVIEWED', 'REVIEWS', 'SUPERVISED'])

# relation tables (build/graph/<name>.parquet) by edge label; candidate and printed-name tables are not relations
RELATIONS = ['AUTHORED', 'EDITED', 'CONTRIBUTED', 'CITES', 'REVIEWS', 'REVIEWED', 'AWARDED_BY', 'SUPERVISED',
             'ADVISED', 'COAUTHORED', 'COEDITED', 'EDITOR_OF', 'PART_OF', 'PUBLISHED_AS', 'EDITION_OF', 'SAME_WORK',
             'ABOUT_PLACE', 'PLACE_IN', 'AWARDED', 'AFFILIATED_WITH', 'POSSIBLY_SAME']

CATEGORY = f"""CASE
    WHEN kind IN ('article', 'other', 'review') AND (kind = 'review' OR kind_proposed = 'review'
         OR len(reviewer_names) > 0 OR key IN (SELECT "from" FROM '{G}/reviews.parquet')) THEN 'review'
    WHEN kind = 'other' AND kind_proposed IN ('article', 'chapter') THEN kind_proposed
    WHEN kind IN ('article', 'book', 'chapter', 'thesis', 'preprint', 'dataset', 'atlas_source') THEN kind
    ELSE 'other' END"""

BOOK_SOURCE = """CASE
    WHEN list_bool_or([a LIKE 'lccn:%' OR a LIKE 'lcnote:%' FOR a IN list_append(anchors, key)]) THEN 'lc'
    WHEN list_bool_or([a LIKE 'hnet-book:%' FOR a IN anchors]) THEN 'hnet'
    WHEN list_bool_or([a LIKE 'doi:%' OR a LIKE 'openalex:%' FOR a IN list_append(anchors, key)]) THEN 'doi'
    WHEN key LIKE 'volume:%' THEN 'volume'
    WHEN key LIKE 'prizework:%' THEN 'prize'
    ELSE 'other' END"""

CITE_SOURCE = """CASE WHEN source LIKE '%thesis%' THEN 'thesis' WHEN source LIKE '%jstor%' THEN 'jstor'
    WHEN source LIKE '%crossref%' THEN 'crossref' ELSE 'other' END"""


def histogram(db, where, expr='year', start=1800, end=2029, width=5, table='wk', split=True):
    """Counts in `width`-year bins from `start` to `end`, before and after, and how many have no year; with
    `split`, also the bins of works with a project identifier (keyed) so the page can show the two layers."""
    rows = db.execute(f"""SELECT CASE WHEN y < {start} THEN -1 WHEN y > {end} THEN -2 ELSE (y - {start}) // {width} END b,
            count(*), count(*) FILTER (WHERE keyed) FROM (SELECT {expr} y, resolution <> 'unkeyed' keyed FROM {table}
            WHERE {where}) WHERE y IS NOT NULL GROUP BY 1""").fetchall()
    n, nk = db.execute(f"SELECT count(*), count(*) FILTER (WHERE resolution <> 'unkeyed') FROM {table} WHERE {where}").fetchone()
    bins, kb = [0] * ((end - start + 1) // width), [0] * ((end - start + 1) // width)
    before = after = 0
    for b, c, k in rows:
        if b == -1:
            before += c
        elif b == -2:
            after += c
        else:
            bins[b], kb[b] = c, k
    out = dict(start=start, width=width, bins=bins, before=before, after=after,
               total=sum(c for _, c, _ in rows), of=n, partial_last=True)
    if split:
        out.update(keyed=kb, of_keyed=nk)
    return out


def main():
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=4")
    one = lambda q: db.execute(q).fetchone()
    pairs = lambda q: dict(db.execute(q).fetchall())
    report = json.loads((G / 'report.json').read_text())
    s = dict(built=datetime.date.today().isoformat(),
             graph_built=datetime.date.fromtimestamp((G / 'report.json').stat().st_mtime).isoformat())
    checks = []

    # ---- people
    total, orcid, wd, lc, gnd, viaf, isni, idref, any_pid = one(f"""SELECT count(*), count(orcid), count(wd), count(lcnaf),
        count(gnd), count(viaf), count(isni), count(idref),
        count(*) FILTER (WHERE coalesce(orcid, wd, lcnaf, gnd, viaf, isni, idref) IS NOT NULL) FROM '{G}/person.parquet'""")
    res = pairs(f"SELECT resolution, count(*) FROM '{G}/person.parquet' GROUP BY 1")
    s['people'] = dict(total=total, with_public_id=any_pid, established=res.get('established', 0),
                       recorded=res.get('recorded', 0), unresolved=res.get('unresolved', 0),
                       ids={'Library of Congress': lc, 'GND (German National Library)': gnd, 'VIAF': viaf,
                            'ISNI': isni, 'Wikidata': wd, 'ORCID': orcid, 'IdRef (France)': idref})
    roles_csv = f"read_csv_auto('{ROLES}', all_varchar=true)"
    s['people']['roles'] = pairs(f"SELECT role, count(*) FROM {roles_csv} GROUP BY 1 ORDER BY 2 DESC")
    s['people']['roles_cover'] = one(f"SELECT count(*) FROM {roles_csv} r JOIN '{G}/person.parquet' p USING (key)")[0]
    s['people']['signals'] = pairs(f"""SELECT s, count(*) FROM (SELECT unnest(string_split(signals, ';')) s
        FROM {roles_csv} WHERE signals IS NOT NULL) GROUP BY 1""")
    s['people']['confidence'] = {f'{r}|{c}': n for r, c, n in db.execute(
        f"SELECT role, confidence, count(*) FROM {roles_csv} GROUP BY 1, 2").fetchall()}
    s['people']['duplicates'] = json.loads((HERE / 'dup-bound.json').read_text())
    s['people']['possibly_same'] = pairs(f"SELECT likelihood, count(*) FROM '{G}/possibly_same.parquet' GROUP BY 1")
    checks.append(('roles cover every person key', s['people']['roles_cover'] == total == sum(s['people']['roles'].values())))

    # ---- works: one exclusive category per work, two layers
    db.execute(f"""CREATE TEMP TABLE wk AS SELECT key, resolution, kind, year, first_year, {CATEGORY} AS cat,
        CASE WHEN kind = 'book' THEN {BOOK_SOURCE} END AS book_source FROM '{G}/work.parquet'""")
    s['works'] = dict(total=one("SELECT count(*) FROM wk")[0],
                      resolution=pairs("SELECT resolution, count(*) FROM wk GROUP BY 1"),
                      by_kind={c: dict(keyed=k, unkeyed=u) for c, k, u in db.execute("""SELECT cat,
                          count(*) FILTER (WHERE resolution <> 'unkeyed'), count(*) FILTER (WHERE resolution = 'unkeyed')
                          FROM wk GROUP BY 1 ORDER BY count(*) DESC""").fetchall()},
                      books_by_source={c: dict(keyed=k, unkeyed=u) for c, k, u in db.execute("""SELECT book_source,
                          count(*) FILTER (WHERE resolution <> 'unkeyed'), count(*) FILTER (WHERE resolution = 'unkeyed')
                          FROM wk WHERE kind = 'book' GROUP BY 1 ORDER BY count(*) DESC""").fetchall()})
    W = s['works']
    W['books_with_hnet_record'] = one("SELECT count(*) FROM wk w JOIN '" + str(G) + "/work.parquet' x USING (key) WHERE w.kind = 'book' AND list_bool_or([a LIKE 'hnet-book:%' FOR a IN x.anchors])")[0]
    W['keyed'] = W['resolution'].get('established', 0) + W['resolution'].get('recorded', 0)
    W['unkeyed'] = W['resolution'].get('unkeyed', 0)
    W['notes'] = dict(
        articles_proposed_chapter=one(f"SELECT count(*) FROM '{G}/work.parquet' WHERE kind = 'article' AND kind_proposed = 'chapter'")[0],
        other_typed_by_proposal=one(f"SELECT count(*) FROM '{G}/work.parquet' WHERE kind = 'other' AND kind_proposed IS NOT NULL")[0],
        books_or_theses_reviewing=one(f"""SELECT count(*) FROM '{G}/work.parquet' WHERE kind IN ('book', 'thesis')
            AND (len(reviewer_names) > 0 OR key IN (SELECT "from" FROM '{G}/reviews.parquet'))""")[0])
    # where the works held as references only come from (build_graph.py report counters)
    routes = {
        'profiles': report.get('Work_unkeyed_author_works', 0),
        'thesis_cited': report.get('Work_unkeyed_cited_works', 0),
        'jstor_cited': report.get('Work_unkeyed_jstor_cited_works', 0),
        'crossref_cited': report.get('crossref26_cited_nodes', 0),
        'crossref_citing': report.get('crossref26_citing_nodes', 0) + report.get('Work_unkeyed_articles', 0),
        'volumes': report.get('Work_unkeyed_volumes', 0) + report.get('name_only_chapters_added', 0),
        'reviews': report.get('crossref_slice_reviews_review_nodes_added', 0),
        'lc_books': (report.get('review_books_lc_book_nodes_added', 0) + report.get('lc_authority_books_nodes_added', 0)
                     + report.get('lc_note_books_nodes_added', 0)),
        'prize_works': sum(v for k, v in report.get('prizes', {}).items() if k.startswith('prize_work_nodes_added')),
    }
    rest = W['unkeyed'] - sum(routes.values())
    if rest:
        routes['other'] = rest
    W['unkeyed_routes'] = routes
    checks.append(('work kinds sum to the total', sum(v['keyed'] + v['unkeyed'] for v in W['by_kind'].values()) == W['total']))
    checks.append(('unkeyed routes sum to the unkeyed works without remainder', rest == 0))
    checks.append(('work total matches report', W['total'] == report['Work']))

    # ---- author credits: the key log's claims and credits linked by rules or identifiers
    s['credits'] = dict(
        authored=pairs(f"SELECT evidence, count(*) FROM '{G}/authored.parquet' GROUP BY 1"),
        edited=pairs(f"SELECT evidence, count(*) FROM '{G}/edited.parquet' GROUP BY 1"),
        linked_by_route=pairs(f"""SELECT CASE
                WHEN source LIKE 'author-works:%' OR source = 'openalex' THEN 'profiles'
                WHEN source = 'qwen-links' THEN 'model'
                WHEN source LIKE 'work-people:%' OR source LIKE 'name-only%' OR source IN ('scored-links', 'classified-links', 'same-work') THEN 'printed'
                WHEN source = 'lc' OR source LIKE 'lc-%' OR source LIKE 'jstor-matched%' OR source LIKE 'edition-roles%' THEN 'lc'
                ELSE 'other' END r, count(*) FROM '{G}/authored.parquet' WHERE evidence = 'linked' GROUP BY 1 ORDER BY 2 DESC"""),
        works_credited={r: n for r, n in db.execute(f"""SELECT w.resolution <> 'unkeyed', count(*) FROM wk w
            WHERE w.key IN (SELECT "to" FROM '{G}/authored.parquet' UNION SELECT "to" FROM '{G}/edited.parquet') GROUP BY 1""").fetchall()},
        people_credited=one(f"""SELECT count(DISTINCT "from") FROM '{G}/authored.parquet'""")[0])
    s['credits']['works_credited'] = {'keyed': s['credits']['works_credited'].get(True, 0),
                                      'unkeyed': s['credits']['works_credited'].get(False, 0)}
    checks.append(('authored rows match report', sum(s['credits']['authored'].values()) == report['AUTHORED']))

    # ---- relations, counted from the tables
    s['edges'] = {r: one(f"SELECT count(*) FROM '{G}/{r.lower()}.parquet'")[0] for r in RELATIONS}
    for r in RELATIONS:
        want = report.get(r, report.get('places', {}).get(r))
        if want is not None:
            checks.append((f'{r} matches report', want == s['edges'][r]))

    # ---- citations by citing source
    db.execute(f"""CREATE TEMP TABLE ct AS SELECT c."from" f, c."to" t, c.edition, {CITE_SOURCE} AS src,
        c.source LIKE '%crossref%' AND c.source LIKE '%jstor%' AS both_jc, w.resolution <> 'unkeyed' AS to_keyed
        FROM '{G}/cites.parquet' c JOIN wk w ON w.key = c."to\"""")
    s['citations'] = dict(
        by_source={src: dict(edges=e, citing=c, cited=d, to_keyed=k, edition_only=ed) for src, e, c, d, k, ed in db.execute(
            """SELECT src, count(*), count(DISTINCT f), count(DISTINCT t), count(*) FILTER (WHERE to_keyed),
               count(*) FILTER (WHERE edition) FROM ct GROUP BY 1 ORDER BY 2 DESC""").fetchall()},
        total=one("SELECT count(*) FROM ct")[0], citing=one("SELECT count(DISTINCT f) FROM ct")[0],
        cited=one("SELECT count(DISTINCT t) FROM ct")[0],
        cited_keyed=one("SELECT count(DISTINCT t) FILTER (WHERE to_keyed) FROM ct")[0],
        to_keyed=one("SELECT count(*) FILTER (WHERE to_keyed) FROM ct")[0],
        edition_only=one("SELECT count(*) FILTER (WHERE edition) FROM ct")[0],
        jstor_also_crossref=one("SELECT count(*) FILTER (WHERE both_jc) FROM ct")[0],
        citing_keyed=pairs("""SELECT w.resolution <> 'unkeyed', count(DISTINCT f) FROM ct JOIN wk w ON w.key = ct.f GROUP BY 1"""))
    s['citations']['citing_keyed'] = {'keyed': s['citations']['citing_keyed'].get(True, 0),
                                      'unkeyed': s['citations']['citing_keyed'].get(False, 0)}
    checks.append(('citations by source sum to CITES', sum(v['edges'] for v in s['citations']['by_source'].values()) == s['edges']['CITES']))

    # ---- reviews
    db.execute("CREATE TEMP TABLE rv AS SELECT * FROM wk WHERE cat = 'review'")
    s['reviews'] = dict(
        total=one("SELECT count(*) FROM rv")[0],
        keyed=one("SELECT count(*) FROM rv WHERE resolution <> 'unkeyed'")[0],
        linked_to_book=one(f"""SELECT count(*) FROM rv WHERE key IN (SELECT "from" FROM '{G}/reviews.parquet')""")[0],
        books_reviewed=one(f"""SELECT count(DISTINCT "to") FROM '{G}/reviews.parquet'""")[0],
        with_credited_reviewer=one(f"""SELECT count(*) FROM rv WHERE key IN (SELECT "to" FROM '{G}/authored.parquet')""")[0],
        with_keylog_reviewer=one(f"""SELECT count(*) FROM rv WHERE key IN (SELECT "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog')""")[0],
        reviewer_to_author=one(f"""SELECT count(DISTINCT review) FROM '{G}/reviewed.parquet'""")[0],
        printed_name_only=one(f"""SELECT count(*) FROM rv JOIN '{G}/work.parquet' w USING (key) WHERE len(w.reviewer_names) > 0
            AND rv.key NOT IN (SELECT "to" FROM '{G}/authored.parquet')""")[0],
        by_year=histogram(db, "true", start=1900, table='rv'))

    # ---- places
    db.execute(f"""CREATE TEMP TABLE pc AS SELECT key, label, kind, CASE WHEN kind = 'country' THEN qid ELSE country END c
        FROM '{G}/place.parquet'""")
    db.execute(f"""CREATE TEMP TABLE ap AS SELECT DISTINCT a."from" w, pc.c FROM '{G}/about_place.parquet' a JOIN pc ON pc.key = a."to\"""")
    countries = db.execute("""SELECT x.c, (SELECT label FROM pc WHERE pc.key = 'place:' || x.c) l, x.n
        FROM (SELECT c, count(DISTINCT w) n FROM ap WHERE c IS NOT NULL GROUP BY 1) x ORDER BY n DESC""").fetchall()
    tagged = f"""(SELECT DISTINCT "from" FROM '{G}/about_place.parquet')"""
    s['places'] = dict(
        total=one("SELECT count(*) FROM pc")[0],
        by_kind=pairs("SELECT kind, count(*) FROM pc GROUP BY 1 ORDER BY 2 DESC"),
        with_works=one(f"""SELECT count(DISTINCT "to") FROM '{G}/about_place.parquet'""")[0],
        works_tagged=one(f"SELECT count(*) FROM {tagged}")[0],
        works_tagged_by_kind={c: dict(tagged=t, of=n) for c, t, n in db.execute(f"""SELECT cat,
            count(*) FILTER (WHERE key IN {tagged}), count(*) FROM wk GROUP BY 1 ORDER BY 3 DESC""").fetchall()},
        by_source=pairs(f"""SELECT source, count(DISTINCT "from") FROM '{G}/about_place.parquet' GROUP BY 1 ORDER BY 2 DESC"""),
        countries_with_works=len(countries),
        top_countries=[dict(qid=c, label=l or c, works=n) for c, l, n in countries[:15]],
        works_without_country=one("SELECT count(*) FROM (SELECT w FROM ap GROUP BY 1 HAVING count(c) = 0)")[0])
    checks.append(('place total matches report', s['places']['total'] == report['places']['Place']))

    # ---- prizes and honours
    s['prizes'] = dict(
        total=one(f"SELECT count(*) FROM '{G}/prize.parquet'")[0],
        lists=one(f"SELECT count(*) FROM '{G}/prize.parquet' WHERE shown")[0],
        list_rows=one(f"SELECT sum(rows) FROM '{G}/prize.parquet' WHERE shown")[0],
        honours=one(f"SELECT count(*) FROM '{G}/prize.parquet' WHERE NOT shown")[0],
        awarded={f'{"list" if sh else "honour"}|{t}': dict(edges=e, recipients=r) for sh, t, e, r in db.execute(f"""SELECT shown, target,
            count(*), count(DISTINCT "to") FROM '{G}/awarded.parquet' GROUP BY 1, 2""").fetchall()},
        people_awarded=one(f"""SELECT count(DISTINCT "to") FROM '{G}/awarded.parquet' WHERE target = 'person'""")[0],
        people_list_prize=one(f"""SELECT count(DISTINCT "to") FROM '{G}/awarded.parquet' WHERE target = 'person' AND shown""")[0],
        works_awarded=one(f"""SELECT count(DISTINCT "to") FROM '{G}/awarded.parquet' WHERE target = 'work'""")[0],
        winners_unlinked=sum(v for k, v in report['prizes'].items() if k.startswith('winners_unlinked|')),
        by_country=pairs(f"""SELECT coalesce(body_country, '?'), count(*) FROM '{G}/prize.parquet' WHERE shown GROUP BY 1 ORDER BY 2 DESC"""),
        top_lists=[dict(label=l, body=b, rows=n, linked=k) for l, b, n, k in db.execute(f"""SELECT p.label, p.body, p.rows,
            (SELECT count(DISTINCT a.row) FROM '{G}/awarded.parquet' a WHERE a."from" = p.key) FROM '{G}/prize.parquet' p WHERE p.shown
            ORDER BY p.rows DESC LIMIT 10""").fetchall()])

    # ---- institutions and affiliations
    s['institutions'] = dict(
        total=one(f"SELECT count(*) FROM '{G}/institution.parquet'")[0],
        with_ror=one(f"SELECT count(ror) FROM '{G}/institution.parquet'")[0],
        affiliations=s['edges']['AFFILIATED_WITH'],
        by_kind={k: dict(edges=e, people=p, institutions=i) for k, e, p, i in db.execute(f"""SELECT kind, count(*),
            count(DISTINCT "from"), count(DISTINCT "to") FROM '{G}/affiliated_with.parquet' GROUP BY 1 ORDER BY 2 DESC""").fetchall()},
        by_source=pairs(f"""SELECT split_part(source, ':', 1), count(*) FROM '{G}/affiliated_with.parquet' GROUP BY 1 ORDER BY 2 DESC"""),
        people=one(f"""SELECT count(DISTINCT "from") FROM '{G}/affiliated_with.parquet'""")[0],
        people_employment=one(f"""SELECT count(DISTINCT "from") FROM '{G}/affiliated_with.parquet' WHERE kind IN ('employment', 'position')""")[0],
        with_people=one(f"""SELECT count(DISTINCT "to") FROM '{G}/affiliated_with.parquet'""")[0],
        awarding=one(f"""SELECT count(DISTINCT "to") FROM '{G}/awarded_by.parquet'""")[0])

    # ---- dissertation corpus (counts only)
    d = f"read_csv_auto('{CORPUS}/dissertations.csv')"
    thesis = s['citations']['by_source'].get('thesis', dict(edges=0, citing=0, cited=0, to_keyed=0))
    s['corpus'] = dict(
        records=one(f"SELECT count(*) FROM {d}")[0],
        parsed=one(f"SELECT count(*) FROM {d} WHERE bibliography_entries > 0")[0],
        in_analysis=one(f"SELECT count(*) FROM {d} WHERE in_analysis")[0],
        bibliography_entries=one(f"SELECT sum(bibliography_entries) FROM {d}")[0],
        by_country=pairs(f"SELECT coalesce(country, '?'), count(*) FROM {d} WHERE in_analysis GROUP BY 1 ORDER BY 2 DESC"),
        distinct_cited_works=one(f"SELECT count(*) FROM read_csv_auto('{CORPUS}/works.csv')")[0],
        corpus_citations=one(f"SELECT count(*) FROM read_csv_auto('{CORPUS}/strict-citations.csv.gz')")[0],
        thesis_cites=thesis['edges'], thesis_cites_keyed=thesis['to_keyed'], theses_citing=thesis['citing'],
        thesis_cited_works=thesis['cited'],
        thesis_cited_keyed=one("SELECT count(DISTINCT t) FROM ct WHERE src = 'thesis' AND to_keyed")[0])

    # ---- years (binned only; no individual's birth year)
    hist = f"""(SELECT r.key, try_cast(l.birth AS INT) birth, 'x' resolution FROM {roles_csv} r
        LEFT JOIN read_csv_auto('{LIFE_YEARS}', all_varchar=true) l USING (key) WHERE r.role = 'historian')"""
    s['years'] = dict(
        births=dict(histogram(db, 'true', expr='birth', end=2004, table=hist, split=False), partial_last=False),
        theses=histogram(db, "cat = 'thesis'"),
        books=histogram(db, "cat = 'book'", expr='coalesce(first_year, year)'),
        articles=histogram(db, "cat = 'article'"))
    b = s['years']['books']
    s['years']['books_2010_2016'] = one("SELECT count(*) FROM wk WHERE cat = 'book' AND coalesce(first_year, year) BETWEEN 2010 AND 2016")[0]
    s['years']['books_2017_2023'] = one("SELECT count(*) FROM wk WHERE cat = 'book' AND coalesce(first_year, year) BETWEEN 2017 AND 2023")[0]
    s['years']['books_keyed_2010_2016'] = one("SELECT count(*) FROM wk WHERE cat = 'book' AND resolution <> 'unkeyed' AND coalesce(first_year, year) BETWEEN 2010 AND 2016")[0]
    s['years']['books_keyed_2017_2023'] = one("SELECT count(*) FROM wk WHERE cat = 'book' AND resolution <> 'unkeyed' AND coalesce(first_year, year) BETWEEN 2017 AND 2023")[0]

    # ---- known limits, as tracked numbers
    s['limits'] = dict(
        name_only_unlinked=report.get('name_only_works_with_a_keyed_name_candidate_and_no_link'),
        works_without_place=W['total'] - s['places']['works_tagged'],
        books_without_place=s['places']['works_tagged_by_kind']['book']['of'] - s['places']['works_tagged_by_kind']['book']['tagged'],
        unkeyed_without_author=W['unkeyed'] - s['credits']['works_credited']['unkeyed'],
        possibly_same=sum(s['people']['possibly_same'].values()),
        dup_upper_bound=s['people']['duplicates']['surplus_upper_bound'],
        reviews_without_reviewer=s['reviews']['total'] - s['reviews']['with_credited_reviewer'],
        prize_winners_unlinked=s['prizes']['winners_unlinked'])

    # ---- growth since the page of 2026-11-07
    s['growth'] = dict(then=BASELINE, now=dict(
        people=total, works=W['total'], works_keyed=W['keyed'], institutions=s['institutions']['total'],
        reviews=s['reviews']['total'], cites=s['edges']['CITES'], dissertations=s['corpus']['in_analysis'],
        relations_same_kinds=sum(s['edges'][k] for k in BASELINE['relation_kinds']),
        relations=sum(s['edges'].values())))
    s['checks'] = {name: ok for name, ok in checks}

    (HERE / 'stats.json').write_text(json.dumps(s, indent=1, ensure_ascii=False) + '\n')
    page = (HERE / 'template.html').read_text().replace('/*STATS*/null', json.dumps(s, ensure_ascii=False))
    (HERE / 'kg-overview.html').write_text(page)
    for name, ok in checks:
        print('ok  ' if ok else 'FAIL', name)
    print(json.dumps({k: s[k] for k in ('people', 'works', 'edges', 'citations', 'limits', 'growth')}, indent=1)[:6000])


if __name__ == '__main__':
    main()
