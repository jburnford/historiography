"""End-to-end probe tables from LC subject headings + hand-checked titles (place-nodes scoping pilot).

Inputs: build/graph (work, authored, person, reviews, cites), SCRATCH/lcout/heads-grounded.parquet (lc_indirect.py),
SCRATCH/place-title-matches.parquet and title-matches.parquet (title scripts), the checked CSVs in the pilot folder.
Outputs (pilot folder): ceylon-works.csv, ceylon-people.csv, saskatchewan-works.csv, saskatchewan-people.csv,
prince-albert-people.csv, canada-by-province.csv, canada-top50-people.csv, ceylon-canada-links.csv, probes-summary.json.
A person's places are derived from their works here, never stored on the person.
"""
import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path('/home/jic823/historiography')
G = ROOT / 'build/graph'
D = Path(__file__).resolve().parent.parent
S = Path(os.environ['SCRATCH'])
EXCL = "('translator','introducer','edition-editor','series-editor','contributor')"

PROV = {  # LC qualifier abbreviations and heading names -> province / territory
    'Ont.': 'Ontario', 'Ontario': 'Ontario', 'Québec': 'Quebec', 'Quebec': 'Quebec', 'Québec (Province)': 'Quebec',
    'Quebec (Province)': 'Quebec', 'B.C.': 'British Columbia', 'British Columbia': 'British Columbia',
    'Alta.': 'Alberta', 'Alberta': 'Alberta', 'Man.': 'Manitoba', 'Manitoba': 'Manitoba', 'Sask.': 'Saskatchewan',
    'Saskatchewan': 'Saskatchewan', 'N.S.': 'Nova Scotia', 'Nova Scotia': 'Nova Scotia', 'N.B.': 'New Brunswick',
    'New Brunswick': 'New Brunswick', 'P.E.I.': 'Prince Edward Island', 'Prince Edward Island': 'Prince Edward Island',
    'N.L.': 'Newfoundland and Labrador', 'Nfld.': 'Newfoundland and Labrador', 'Newfoundland and Labrador': 'Newfoundland and Labrador',
    'Newfoundland': 'Newfoundland and Labrador', 'Labrador (N.L.)': 'Newfoundland and Labrador', 'Yukon': 'Yukon',
    'Yukon Territory': 'Yukon', 'N.W.T.': 'Northwest Territories', 'Northwest Territories': 'Northwest Territories',
    'Nunavut': 'Nunavut', 'Canada': 'Canada (country level)', 'Prairie Provinces': 'Prairie Provinces (region)',
    'Canada, Western': 'Western Canada (region)', 'Northwest, Canadian': 'Canadian Northwest (region)',
    'Maritime Provinces': 'Maritime Provinces (region)', 'Atlantic Provinces': 'Atlantic Provinces (region)',
    'Canada, Northern': 'Northern Canada (region)', 'Upper Canada': 'Ontario', 'Lower Canada': 'Quebec',
}


def con():
    c = duckdb.connect()
    c.execute("set memory_limit='4GB'; set threads=4")
    return c


def lc_province(heading, parent):
    if heading in PROV:
        return PROV[heading]
    q = re.findall(r'\(([^)]*)\)$', heading or '')
    if q:
        for part in re.split(r'\s*(?:,| and | et |:)\s*', q[0]):
            if part in PROV and PROV[part] != 'Canada (country level)':
                return PROV[part]
    if parent in PROV and PROV[parent] != 'Canada (country level)':
        return PROV[parent]
    if parent == 'Canada':
        return 'Canada (child, no province)'
    return None


def main():
    c = con()
    c.execute(f"CREATE TABLE w AS SELECT key, label, kind, year, journal FROM '{G}/work.parquet'")
    c.execute(f"CREATE TABLE p AS SELECT key, label FROM '{G}/person.parquet'")
    c.execute(f"""CREATE TABLE au AS SELECT DISTINCT "from" AS person, "to" AS work FROM '{G}/authored.parquet'
                  WHERE coalesce(role,'author') NOT IN {EXCL}""")
    c.execute(f"CREATE TABLE lc AS SELECT * FROM '{S}/lcout/heads-grounded.parquet'")
    summary = {}

    # ---------- tags: (work, region, place, source)
    tags = []
    # Ceylon family from LC
    for key, heading, parent in c.execute("""SELECT DISTINCT key, heading, parent FROM lc WHERE heading IN ('Sri Lanka','Ceylon')
            OR heading LIKE '%(Sri Lanka%' OR heading LIKE '%Ceylon%' OR parent IN ('Sri Lanka','Ceylon')""").fetchall():
        place = 'Sri Lanka / Ceylon' if heading in ('Sri Lanka', 'Ceylon') else re.sub(r'\s*\(.*\)$', '', heading)
        tags.append((key, 'ceylon', place, 'lc'))
    # Saskatchewan family from LC (the LC qualifier 'Sask.' is itself the hierarchy)
    for key, heading, parent in c.execute(r"""SELECT DISTINCT key, heading, parent FROM lc WHERE heading = 'Saskatchewan'
            OR regexp_matches(heading, '\((.*\b)?Sask\.') OR parent = 'Saskatchewan' OR heading LIKE 'Saskatchewan %'""").fetchall():
        place = 'Saskatchewan' if heading == 'Saskatchewan' else re.sub(r'\s*\(.*\)$', '', heading)
        tags.append((key, 'saskatchewan', place, 'lc'))
    # titles: hand-checked right (and the Saskatchewan River class, part of the Saskatchewan family)
    for f, region in (('ceylon-works-checked.csv', 'ceylon'), ('saskatchewan-works-checked.csv', 'saskatchewan')):
        for r in csv.DictReader(open(D / f)):
            if r['verdict'] == 'right' or (r['verdict'] == 'river'):
                for pl in r['matched_places'].split('+'):
                    if r['verdict'] == 'river':
                        pl = 'Saskatchewan River / district'
                    elif pl in ('Sri Lanka', 'British Ceylon', 'Ceylon (other languages)', 'Taprobane/Serendib'):
                        pl = 'Sri Lanka / Ceylon'
                    tags.append((r['work'], region, pl, 'title'))
            elif r['verdict'] == 'other_place' and 'National Park' in r['note']:
                tags.append((r['work'], 'saskatchewan', 'Prince Albert National Park', 'title'))
    c.execute("CREATE TABLE t (work VARCHAR, region VARCHAR, place VARCHAR, source VARCHAR)")
    c.executemany("INSERT INTO t VALUES (?,?,?,?)", tags)
    c.execute("UPDATE t SET place = 'Prince Albert' WHERE place IN ('Prince Albert Region')")
    c.execute("""CREATE TABLE tw AS SELECT t.work, t.region, list_distinct(list(place ORDER BY place)) places,
                 list_distinct(list(source ORDER BY source)) sources, w.label, w.kind, w.year
                 FROM t JOIN w ON w.key = t.work GROUP BY ALL""")

    for region in ('ceylon', 'saskatchewan'):
        rows = c.execute(f"""SELECT tw.*, (SELECT list(a.person || ' ' || coalesce(p.label,'') ORDER BY a.person) FROM au a
                 LEFT JOIN p ON p.key = a.person WHERE a.work = tw.work) authors FROM tw WHERE region = '{region}'
                 ORDER BY year NULLS LAST, label""").fetchall()
        with open(D / f'{region}-works.csv', 'w', newline='') as fh:
            wr = csv.writer(fh)
            wr.writerow(['work', 'title', 'year', 'decade', 'kind', 'places', 'tag_sources', 'authors'])
            for work, _, places, sources, label, kind, year, authors in rows:
                wr.writerow([work, label, year, (year // 10 * 10) if year else '', kind, '; '.join(places), '+'.join(sources),
                             '; '.join(authors or [])])
        s = {}
        s['works'] = len(rows)
        s['by_source'] = dict(Counter('+'.join(r[3]) for r in rows))
        s['by_kind'] = dict(Counter(r[5] for r in rows).most_common())
        s['by_decade'] = dict(sorted(Counter((r[6] // 10 * 10) if r[6] else None for r in rows).items(), key=lambda x: (x[0] is None, x[0])))
        s['by_place'] = dict(Counter(pl for r in rows for pl in r[2]).most_common())
        # people
        ppl = c.execute(f"""SELECT a.person, p.label, count(DISTINCT tw.work) n,
                 count(DISTINCT tw.work) FILTER (WHERE tw.kind <> 'review') n_nonreview,
                 count(DISTINCT tw.work) FILTER (WHERE tw.kind = 'review' OR tw.label LIKE 'Review of%') n_review,
                 list(DISTINCT tw.kind), list(tw.label ORDER BY tw.year NULLS LAST)[1:3], list(DISTINCT tw.work),
                 list_distinct(flatten(list(tw.sources))), list_distinct(flatten(list(tw.places)))
                 FROM tw JOIN au a ON a.work = tw.work LEFT JOIN p ON p.key = a.person
                 WHERE tw.region = '{region}' GROUP BY ALL ORDER BY n_nonreview DESC, n DESC, p.label""").fetchall()
        s['people_ge1'] = len(ppl)
        s['people_ge2'] = sum(1 for x in ppl if x[2] >= 2)
        s['people_ge2_nonreview'] = sum(1 for x in ppl if x[3] >= 2)
        s['works_with_keyed_author'] = c.execute(f"SELECT count(DISTINCT work) FROM tw JOIN au USING (work) WHERE region = '{region}'").fetchone()[0]
        s['top15'] = [(x[0], x[1], x[2], x[6][0]) for x in ppl[:15]]
        with open(D / f'{region}-people.csv', 'w', newline='') as fh:
            wr = csv.writer(fh)
            wr.writerow(['rank', 'person', 'label', 'works', 'works_not_reviews', 'reviews', 'kinds', 'tag_sources', 'places', 'example_titles', 'work_keys'])
            for i, x in enumerate(ppl, 1):
                wr.writerow([i, x[0], x[1], x[2], x[3], x[4], '|'.join(sorted(k for k in x[5] if k)), '+'.join(sorted(x[8])),
                             '; '.join(sorted(x[9])), ' || '.join(t[:120] for t in x[6]), ' '.join(sorted(x[7]))])
        summary[region] = s

    # ---------- Prince Albert (inside the Saskatchewan family)
    pa = c.execute("""SELECT a.person, p.label, count(DISTINCT tw.work), list(tw.label ORDER BY tw.year), list(DISTINCT tw.work)
             FROM tw JOIN au a ON a.work = tw.work LEFT JOIN p ON p.key = a.person
             WHERE tw.region = 'saskatchewan' AND (list_contains(tw.places, 'Prince Albert') OR list_contains(tw.places, 'Prince Albert National Park'))
             GROUP BY ALL ORDER BY 3 DESC, 2""").fetchall()
    with open(D / 'prince-albert-people.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['person', 'label', 'works', 'titles', 'work_keys'])
        for x in pa:
            wr.writerow([x[0], x[1], x[2], ' || '.join(t[:120] for t in x[3]), ' '.join(x[4])])
    summary['prince_albert'] = dict(
        works=c.execute("SELECT count(*) FROM tw WHERE region='saskatchewan' AND list_contains(places,'Prince Albert')").fetchone()[0],
        works_incl_park=c.execute("SELECT count(*) FROM tw WHERE region='saskatchewan' AND (list_contains(places,'Prince Albert') OR list_contains(places,'Prince Albert National Park'))").fetchone()[0],
        by_source=dict(c.execute("SELECT array_to_string(sources,'+'), count(*) FROM tw WHERE region='saskatchewan' AND list_contains(places,'Prince Albert') GROUP BY 1").fetchall()),
        n_people=len(pa), people=[(x[0], x[1], x[2], x[3][0][:100]) for x in pa])

    # ---------- hierarchy: what a Saskatchewan search gains from child places
    child = c.execute("""SELECT count(*), count(*) FILTER (WHERE NOT list_contains(places, 'Saskatchewan')) FROM tw WHERE region = 'saskatchewan'""").fetchone()
    gained_people = c.execute("""WITH own AS (SELECT DISTINCT a.person FROM tw JOIN au a ON a.work = tw.work WHERE region='saskatchewan' AND list_contains(places,'Saskatchewan')),
          allp AS (SELECT DISTINCT a.person FROM tw JOIN au a ON a.work = tw.work WHERE region='saskatchewan')
          SELECT (SELECT count(*) FROM own), (SELECT count(*) FROM allp)""").fetchone()
    summary['saskatchewan_hierarchy'] = dict(works_family=child[0], works_only_via_child_place=child[1],
                                             people_saskatchewan_itself=gained_people[0], people_with_children=gained_people[1],
                                             child_places=dict(c.execute("""SELECT pl, count(*) FROM (SELECT unnest(places) pl FROM tw WHERE region='saskatchewan'
                                                              AND NOT list_contains(places,'Saskatchewan')) GROUP BY 1 ORDER BY 2 DESC""").fetchall()))
    cey = c.execute("""SELECT count(*), count(*) FILTER (WHERE NOT list_contains(places, 'Sri Lanka / Ceylon')) FROM tw WHERE region='ceylon'""").fetchone()
    summary['ceylon_hierarchy'] = dict(works_family=cey[0], works_only_via_child_place=cey[1])

    # ---------- Canada: LC by province (+ unchecked title counts)
    canada_lc = []
    for key, heading, parent in c.execute("""SELECT DISTINCT key, heading, parent FROM lc""").fetchall():
        prov = lc_province(heading, parent)
        if prov:
            canada_lc.append((key, prov))
    c.execute("CREATE TABLE ca (work VARCHAR, prov VARCHAR)")
    c.executemany("INSERT INTO ca VALUES (?,?)", canada_lc)
    c.execute(f"""CREATE TABLE cat AS SELECT key AS work, CASE WHEN place IN ('Toronto','Ottawa') THEN 'Ontario' WHEN place = 'Montreal' THEN 'Quebec'
                  WHEN place = 'Vancouver' THEN 'British Columbia' WHEN place = 'Winnipeg' THEN 'Manitoba' WHEN place IN ('Calgary','Edmonton') THEN 'Alberta'
                  WHEN place = 'Halifax' THEN 'Nova Scotia' WHEN place = 'Canada' THEN 'Canada (country level)' ELSE place END AS prov
                  FROM '{S}/place-title-matches.parquet' WHERE region = 'canada' AND place <> 'Halifax'""")
    prov_rows = c.execute("""SELECT prov, (SELECT count(DISTINCT work) FROM ca WHERE ca.prov = x.prov),
             (SELECT count(DISTINCT work) FROM cat WHERE cat.prov = x.prov),
             (SELECT count(DISTINCT work) FROM (SELECT work FROM ca WHERE ca.prov = x.prov UNION SELECT work FROM cat WHERE cat.prov = x.prov)),
             (SELECT count(DISTINCT a.person) FROM au a WHERE a.work IN (SELECT work FROM ca WHERE ca.prov = x.prov UNION SELECT work FROM cat WHERE cat.prov = x.prov))
             FROM (SELECT DISTINCT prov FROM ca UNION SELECT DISTINCT prov FROM cat) x ORDER BY 4 DESC""").fetchall()
    with open(D / 'canada-by-province.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['province_or_level', 'works_lc', 'works_title_unchecked', 'works_union', 'keyed_people'])
        wr.writerows(prov_rows)
    c.execute("CREATE TABLE canw AS SELECT work FROM ca UNION SELECT work FROM cat")
    summary['canada'] = dict(works_lc=c.execute("SELECT count(DISTINCT work) FROM ca").fetchone()[0],
                             works_title_unchecked=c.execute("SELECT count(DISTINCT work) FROM cat").fetchone()[0],
                             works_union=c.execute("SELECT count(*) FROM canw").fetchone()[0],
                             people_ge1=c.execute("SELECT count(DISTINCT person) FROM au WHERE work IN (SELECT work FROM canw)").fetchone()[0])
    top = c.execute("""SELECT a.person, p.label, count(DISTINCT a.work) n,
             count(DISTINCT a.work) FILTER (WHERE a.work IN (SELECT work FROM ca)) n_lc, any_value(w.label)
             FROM au a JOIN canw USING (work) LEFT JOIN p ON p.key = a.person JOIN w ON w.key = a.work
             GROUP BY ALL ORDER BY n DESC LIMIT 50""").fetchall()
    with open(D / 'canada-top50-people.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['rank', 'person', 'label', 'works', 'works_with_lc_tag', 'example_title'])
        for i, x in enumerate(top, 1):
            wr.writerow([i, *x])

    # ---------- links between Ceylon and Canada
    c.execute("CREATE TABLE cey AS SELECT work FROM tw WHERE region = 'ceylon'")
    both_people = c.execute("""SELECT a.person, p.label,
             (SELECT count(DISTINCT work) FROM au b WHERE b.person = a.person AND b.work IN (SELECT work FROM cey)) n_cey,
             (SELECT count(DISTINCT work) FROM au b WHERE b.person = a.person AND b.work IN (SELECT work FROM canw)) n_can
             FROM (SELECT DISTINCT person FROM au WHERE work IN (SELECT work FROM cey)) a LEFT JOIN p ON p.key = a.person
             WHERE a.person IN (SELECT person FROM au WHERE work IN (SELECT work FROM canw)) """).fetchall()
    both_people.sort(key=lambda x: -(x[2] + x[3]))
    both_works = c.execute("SELECT w.key, w.label, w.year FROM w WHERE key IN (SELECT work FROM cey) AND key IN (SELECT work FROM canw)").fetchall()
    c.execute(f"CREATE TABLE ci AS SELECT \"from\" AS f, \"to\" AS t, source FROM '{G}/cites.parquet'")
    cite_cey_can = c.execute("""SELECT f, wf.label, t, wt.label, source FROM ci JOIN w wf ON wf.key = f JOIN w wt ON wt.key = t
             WHERE (f IN (SELECT work FROM cey) AND t IN (SELECT work FROM canw)) OR (f IN (SELECT work FROM canw) AND t IN (SELECT work FROM cey))""").fetchall()
    cites_from_cey = c.execute("SELECT count(*) FROM ci WHERE f IN (SELECT work FROM cey)").fetchone()[0]
    cites_to_cey = c.execute("SELECT count(*) FROM ci WHERE t IN (SELECT work FROM cey)").fetchone()[0]
    with open(D / 'ceylon-canada-links.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['link', 'a', 'a_label', 'b', 'b_label', 'detail'])
        for x in both_people:
            wr.writerow(['person-with-both', x[0], x[1], '', '', f'ceylon works {x[2]}; canada works {x[3]}'])
        for x in both_works:
            wr.writerow(['work-names-both', x[0], x[1], '', '', x[2]])
        for x in cite_cey_can:
            wr.writerow(['cites', x[0], x[1], x[2], x[3], x[4]])
    frames = {
        'empire/colonial': r'\b(British Empire|[Ee]mpire|[Ii]mperial|[Cc]olon(y|ial|ies|ization|isation))',
        'plantation/tea/coffee': r'\b([Pp]lantation|[Tt]ea\b|[Cc]offee|[Ee]state labou?r)',
        'migration': r'\b([Mm]igra|[Ee]migra|[Ii]mmigra|[Ss]ettle(r|ment))',
        'missions': r'\b([Mm]ission)',
        'railways': r'\b([Rr]ailw)',
        'census': r'\b([Cc]ensus)',
    }
    fr = {}
    for name, rx in frames.items():
        fr[name] = dict(ceylon=c.execute(f"SELECT count(*) FROM w WHERE key IN (SELECT work FROM cey) AND regexp_matches(label, '{rx}')").fetchone()[0],
                        canada=c.execute(f"SELECT count(*) FROM w WHERE key IN (SELECT work FROM canw) AND regexp_matches(label, '{rx}')").fetchone()[0])
    summary['links'] = dict(people_with_both=len(both_people), people=[(x[0], x[1], x[2], x[3]) for x in both_people[:25]],
                            works_naming_both=len(both_works), works=[(x[0], x[1][:100]) for x in both_works],
                            cites_between=len(cite_cey_can), cites_from_ceylon_works=cites_from_cey, cites_to_ceylon_works=cites_to_cey,
                            cites=[(x[1][:70], x[3][:70], x[4]) for x in cite_cey_can[:20]], frames_in_titles=fr)
    # ---------- reviews that would inherit a book's place
    for region in ('ceylon', 'saskatchewan'):
        summary[region]['reviews_inheriting'] = c.execute(f"""SELECT count(DISTINCT r."from") FROM '{G}/reviews.parquet' r
             WHERE r."to" IN (SELECT work FROM tw WHERE region = '{region}') AND r."from" NOT IN (SELECT work FROM tw WHERE region = '{region}')""").fetchone()[0]
    (D / 'probes-summary.json').write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False))
    print(json.dumps({k: (v if k != 'links' else {kk: vv for kk, vv in v.items() if kk not in ('people', 'works', 'cites')})
                      for k, v in summary.items()}, indent=1, default=str, ensure_ascii=False)[:9000])


if __name__ == '__main__':
    main()
