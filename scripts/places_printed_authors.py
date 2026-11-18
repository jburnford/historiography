"""Authors as catalogued on books with no linked author (2026-11-18, place-demo increment 3).

A display fact from the LC record, never a credit: for every graph work with an LCCN and no AUTHORED or EDITED row of
any evidence, the LC 2016 record's 100 main entry (the heading as catalogued, its dates and relators), the statement
of responsibility as printed (245 $c), and the LC name authority the heading resolves to: its $0, else the one live
authority whose label is the heading, else the one whose name agrees and whose dates start with the heading's dates
('Archer, John Hall, 1914-' -> 'Archer, John Hall, 1914-2004'). The person key holding that authority, if any, is
named (state `on-key`: a credit the LC catalogue route, scripts/lc_catalogue_credits.py, should make), else
`no-key`, or `unresolved`. The explorer shows these as "author as catalogued", visibly not a link, and lists the
authorities on place pages as "catalogued authors not yet in the people index".

Second output: a mint proposal (NOT applied) under the standing rule of 2026-11-10 (a person is minted only with an
LC authority and 2+ citing theses), limited to authorities that are the main entry of a book with an LC place
heading: theses citing any of the authority's graph books (CITES source with a thesis bit), counted per authority.

    python3 scripts/places_printed_authors.py
Writes data/graph/places/lc-printed-authors.csv.gz, data/identifiers/place-demo-fixes-2026-11-18/
mint-place-authors.proposal.json(.gz) and printed-authors-report.json.
"""
import gzip
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
LC = Path('/mnt/e/lc-bib-2016/index')
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
OUT = ROOT / 'data/graph/places/lc-printed-authors.csv.gz'
PROP = ROOT / 'data/identifiers/place-demo-fixes-2026-11-18'


def main():
    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'; SET threads=3; SET preserve_insertion_order=false")
    c.execute(f"""CREATE TABLE credited AS SELECT DISTINCT "to" w FROM '{G}/authored.parquet'
                  UNION SELECT DISTINCT "to" FROM '{G}/edited.parquet'""")
    c.execute(f"""CREATE TABLE b AS SELECT key, lccn FROM '{G}/work.parquet'
                  WHERE lccn IS NOT NULL AND key NOT IN (SELECT w FROM credited)""")
    c.execute(f"""CREATE TABLE rec AS SELECT trim(control) control, lccn, responsibility FROM read_parquet('{LC}/records-*.parquet')
                  WHERE trim(control) IN (SELECT lccn FROM b) OR lccn IN (SELECT lccn FROM b)""")
    c.execute("""CREATE TABLE br AS SELECT DISTINCT b.key, r.control, r.responsibility FROM b JOIN rec r
                 ON r.control = b.lccn OR r.lccn = b.lccn""")
    c.execute(f"""CREATE TABLE hd AS SELECT trim(control) control, heading, family, given, dates, uri, relators
                  FROM read_parquet('{LC}/headings-*.parquet') WHERE tag = '100' AND trim(control) IN (SELECT control FROM br)""")
    c.execute(f"""CREATE TABLE nm AS SELECT lcid, rtrim(label, '.') n,
                    rtrim(regexp_replace(label, ',\\s*(approximately |active |b\\. |d\\. )?[0-9?].*$', ''), '.') nd,
                    regexp_extract(label, '([0-9]{{3,4}})', 1) y
                  FROM '{NAMES}' WHERE NOT coalesce(deprecated, false)""")
    c.execute("""CREATE TABLE ha AS SELECT h.*,
                   rtrim(h.heading, ' .,') AS hn,
                   rtrim(regexp_replace(h.heading, ',\\s*(approximately |active |b\\. |d\\. )?[0-9?].*$', ''), ' .,') AS hnd,
                   regexp_extract(h.dates, '([0-9]{3,4})', 1) AS hy FROM hd h""")
    c.execute("""CREATE TABLE res AS SELECT a.control, a.heading, a.dates, a.relators,
                   coalesce(nullif(regexp_extract(a.uri, '([a-z]+[0-9]+)/?$', 1), ''),
                            (SELECT CASE WHEN count(*) = 1 THEN min(lcid) END FROM nm WHERE nm.n = a.hn),
                            (SELECT CASE WHEN count(*) = 1 THEN min(lcid) END FROM nm WHERE nm.nd = a.hnd AND a.hy <> '' AND nm.y = a.hy)) lcid
                 FROM ha a""")
    c.execute(f"""CREATE TABLE pk AS SELECT substr(a, 7) lcid, list(DISTINCT key) keys FROM (SELECT key, unnest(anchors) a
                  FROM '{G}/person.parquet') WHERE a LIKE 'lcnaf:%' GROUP BY 1""")
    c.execute("""CREATE TABLE out AS SELECT br.key AS work, any_value(r.heading) heading, any_value(r.dates) dates,
                   any_value(array_to_string(r.relators, ';')) relators, any_value(br.responsibility) printed,
                   any_value(r.lcid) lcnaf, any_value(CASE WHEN len(pk.keys) = 1 THEN pk.keys[1] END) person,
                   CASE WHEN any_value(r.lcid) IS NULL THEN 'unresolved' WHEN any_value(pk.keys) IS NULL THEN 'no-key'
                        WHEN len(any_value(pk.keys)) = 1 THEN 'on-key' ELSE 'several-keys' END state
                 FROM br JOIN res r ON r.control = br.control LEFT JOIN pk ON pk.lcid = r.lcid GROUP BY br.key""")
    c.execute(f"COPY (SELECT * FROM out ORDER BY work) TO '{OUT}' (HEADER, COMPRESSION gzip)")
    rep = dict(works_lccn_no_author=c.execute('SELECT count(*) FROM b').fetchone()[0],
               works_with_lc_record=c.execute('SELECT count(DISTINCT key) FROM br').fetchone()[0],
               works_with_100=c.execute('SELECT count(*) FROM out').fetchone()[0],
               by_state=dict(c.execute('SELECT state, count(*) FROM out GROUP BY 1 ORDER BY 2 DESC').fetchall()),
               authorities_no_key=c.execute("SELECT count(DISTINCT lcnaf) FROM out WHERE state = 'no-key'").fetchone()[0])
    # the mint rule: authorities on no key, main entry of a book with an LC place heading, 2+ citing theses over all
    # their graph books
    c.execute(f"""CREATE TABLE pb AS SELECT DISTINCT "from" w FROM '{G}/about_place.parquet' WHERE starts_with(source, 'lc-')""")
    c.execute(f"""CREATE TABLE th AS SELECT "to" w, "from" t FROM '{G}/cites.parquet' WHERE source LIKE '%thesis%'""")
    c.execute("""CREATE TABLE cand AS SELECT o.lcnaf, any_value(o.heading) heading, count(DISTINCT o.work) books,
                   count(DISTINCT o.work) FILTER (WHERE o.work IN (SELECT w FROM pb)) place_books,
                   count(DISTINCT th.t) theses, list(DISTINCT o.work) works
                 FROM out o LEFT JOIN th ON th.w = o.work WHERE o.state = 'no-key' GROUP BY 1""")
    rep['no_key_authorities_with_a_place_book'] = c.execute('SELECT count(*) FROM cand WHERE place_books > 0').fetchone()[0]
    rep['of_them_with_2plus_citing_theses'] = c.execute('SELECT count(*) FROM cand WHERE place_books > 0 AND theses >= 2').fetchone()[0]
    rep['their_books'] = c.execute('SELECT sum(books) FROM cand WHERE place_books > 0 AND theses >= 2').fetchone()[0]
    rows = c.execute("""SELECT c.lcnaf, c.heading, n.plabel, c.works, c.theses FROM cand c JOIN (SELECT lcid, any_value(n) AS plabel FROM nm GROUP BY 1) n
                        ON n.lcid = c.lcnaf WHERE c.place_books > 0 AND c.theses >= 2 ORDER BY c.theses DESC""").fetchall()
    wl = dict(c.execute(f"SELECT key, label FROM '{G}/work.parquet' WHERE key IN (SELECT unnest(works) FROM cand WHERE place_books > 0 AND theses >= 2)").fetchall())
    ops = []
    for i, (lcid, heading, label, works, theses) in enumerate(rows):
        ops.append(dict(event='mint', key=f'new:p{i}', type='person', label=label, resolution='established', anchors=[f'lcnaf:{lcid}'],
                        aliases=[], members=[], basis=f'LC name authority of the main entry of {len(works)} graph book(s), one with an LC '
                        f'place heading; {theses} citing theses (rule of 2026-11-10: LC authority and 2+ citing theses)'))
        for j, w in enumerate(sorted(works)):
            ops.append(dict(event='mint', key=f'new:c{i}x{j}', type='claim', label='', resolution='recorded',
                            anchors=[f'lc-authored:{w[5:] if w.startswith("lccn:") else w}:{lcid}'],
                            relation=dict(subject=f'lcnaf:{lcid}', predicate='authored', object=w),
                            basis=f'LC 100 main entry {heading!r} on {wl.get(w, w)[:120]!r}'))
    rep['proposal_ops'] = len(ops)
    prop = dict(basis=('People minted from the LC main entries of books on place pages, under the standing rule (user, 2026-11-10): '
                       'a person is minted only with an LC authority and 2+ citing theses. Authorities on no person key; their books '
                       'are graph works (keyed, or unkeyed lccn: nodes the claim names by LCCN). NOT APPLIED: for the user.'),
                decided_by='rule', ops=ops)
    with gzip.open(PROP / 'mint-place-authors.proposal.json.gz', 'wt', encoding='utf-8') as fh:
        json.dump(prop, fh, ensure_ascii=False)
    rep['top_candidates'] = [dict(lcnaf=r[0], label=r[2], books=len(r[3]), theses=r[4]) for r in rows[:25]]
    (PROP / 'printed-authors-report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
