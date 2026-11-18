"""Place-demo probe class (2026-11-18): LC books with a place heading and no linked author although the LC record names
the author with a name authority.

Probes: Gunawardana, Robe and plough (lccn:78026090); Abeyasinghe, Portuguese rule in Ceylon (lccn:sa 67004090);
Archer, Saskatchewan: a history (lccn:81157483). Counts, over every graph book that carries an LC place heading
(build/graph/about_place.parquet, source lc-*) and no AUTHORED or EDITED row of any evidence, the books whose LC 2016
record has a 100 main entry, and splits them by the main entry's authority: on exactly one person key (a credit the
LC catalogue route should make: scripts/lc_catalogue_credits.py), on no key (a person to mint: a key-log proposal), or
not resolvable to one authority. Writes data/identifiers/place-demo-fixes-2026-11-18/unlinked-lc-authors.json and
unlinked-lc-authors.csv.gz (the books, main entry heading, authority, person key if any, place QIDs).

    python3 scripts/places_unlinked_authors.py
"""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
LC = Path('/mnt/e/lc-bib-2016/index')
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
OUT = ROOT / 'data/identifiers/place-demo-fixes-2026-11-18'
PROBES = ['lccn:78026090', 'lccn:sa 67004090', 'lccn:81157483']


def main():
    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'; SET threads=3; SET preserve_insertion_order=false")
    c.execute(f"""CREATE TABLE credited AS SELECT DISTINCT "to" w FROM '{G}/authored.parquet'
                  UNION SELECT DISTINCT "to" FROM '{G}/edited.parquet'""")
    c.execute(f"""CREATE TABLE pw AS SELECT "from" AS w, list(DISTINCT substr("to", 7)) AS qids FROM '{G}/about_place.parquet'
                  WHERE starts_with(source, 'lc-') GROUP BY 1""")
    c.execute(f"""CREATE TABLE b AS SELECT w.key, w.label, w.year, w.lccn, w.resolution, pw.qids FROM '{G}/work.parquet' w
                  JOIN pw ON pw.w = w.key WHERE w.key NOT IN (SELECT w FROM credited) AND w.lccn IS NOT NULL""")
    c.execute(f"""CREATE TABLE rec AS SELECT trim(control) control, lccn FROM read_parquet('{LC}/records-*.parquet')
                  WHERE trim(control) IN (SELECT lccn FROM b) OR lccn IN (SELECT lccn FROM b)""")
    c.execute("""CREATE TABLE br AS SELECT b.key, r.control FROM b JOIN rec r ON r.control = b.lccn OR r.lccn = b.lccn""")
    c.execute(f"""CREATE TABLE hd AS SELECT trim(control) control, tag, heading, uri FROM read_parquet('{LC}/headings-*.parquet')
                  WHERE tag = '100' AND trim(control) IN (SELECT control FROM br)""")
    # the main entry's authority: its $0, else the one live authority whose label is the heading (trailing dots off)
    c.execute(f"""CREATE TABLE nm AS SELECT lcid, rtrim(label, '.') n FROM '{NAMES}' WHERE NOT coalesce(deprecated, false)""")
    c.execute("""CREATE TABLE ha AS SELECT h.control, h.heading,
                   coalesce(nullif(regexp_extract(h.uri, '([a-z]+[0-9]+)/?$', 1), ''),
                            (SELECT CASE WHEN count(*) = 1 THEN min(lcid) END FROM nm WHERE nm.n = rtrim(h.heading, ' .,'))) lcid
                 FROM hd h""")
    c.execute(f"""CREATE TABLE pk AS SELECT substr(a, 7) lcid, list(DISTINCT key) keys FROM (SELECT key, unnest(anchors) a
                  FROM '{G}/person.parquet') WHERE a LIKE 'lcnaf:%' GROUP BY 1""")
    c.execute("""CREATE TABLE res AS SELECT b.key, b.label, b.year, b.lccn, b.resolution, b.qids, any_value(ha.heading) heading,
                   any_value(ha.lcid) lcid, any_value(pk.keys) keys
                 FROM b LEFT JOIN br USING (key) LEFT JOIN ha ON ha.control = br.control LEFT JOIN pk ON pk.lcid = ha.lcid
                 GROUP BY ALL""")
    r = {}
    r['lc_place_books'] = c.execute('SELECT count(*) FROM pw').fetchone()[0]
    r['lc_place_books_no_author_or_editor'] = c.execute('SELECT count(*) FROM b').fetchone()[0]
    r['of_them_with_an_lc_2016_record'] = c.execute('SELECT count(DISTINCT key) FROM br').fetchone()[0]
    r['with_a_100_main_entry'] = c.execute('SELECT count(*) FROM res WHERE heading IS NOT NULL').fetchone()[0]
    r['main_entry_authority_on_one_person_key'] = c.execute('SELECT count(*) FROM res WHERE len(keys) = 1').fetchone()[0]
    r['main_entry_authority_on_several_keys'] = c.execute('SELECT count(*) FROM res WHERE len(keys) > 1').fetchone()[0]
    r['main_entry_authority_on_no_key'] = c.execute('SELECT count(*) FROM res WHERE lcid IS NOT NULL AND keys IS NULL').fetchone()[0]
    r['main_entry_authority_not_resolved'] = c.execute('SELECT count(*) FROM res WHERE heading IS NOT NULL AND lcid IS NULL').fetchone()[0]
    r['distinct_authorities_on_no_key'] = c.execute('SELECT count(DISTINCT lcid) FROM res WHERE lcid IS NOT NULL AND keys IS NULL').fetchone()[0]
    r['probes'] = [dict(zip(['key', 'label', 'heading', 'lcid', 'keys'], x)) for x in c.execute(
        'SELECT key, label, heading, lcid, keys FROM res WHERE key IN (SELECT unnest(?))', [PROBES]).fetchall()]
    c.execute(f"COPY (SELECT * FROM res WHERE heading IS NOT NULL ORDER BY key) TO '{OUT}/unlinked-lc-authors.csv.gz' (HEADER, COMPRESSION gzip)")
    (OUT / 'unlinked-lc-authors.json').write_text(json.dumps(r, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(r, indent=1, ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
