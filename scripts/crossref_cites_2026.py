#!/usr/bin/env python3
"""Job 3 (run on spark): Crossref reference lists of history journals as citing works for the graph.

Inputs (spark, /mnt/data/jic823/tools/crossref-extract/cites/):
  journals-resolved.csv, issn-containers.csv   scripts/crossref_cites_journals.py (journal scope: the user's 405 screened
                                               journals + economic-history-titled journals of journal-coverage.csv)
  graph-doi-key.parquet                        doi -> key from build/graph/explorer.duckdb anchors (read-only export)
  graph-work-nodes.parquet                     work nodes of that build (key, kind, type, year)
  graph-cites.parquet                          its CITES edges (from, to, source)
  /mnt/data/jic823/crossref-history-slice/     works, refs (journals outside journal-coverage.csv appended by
                                               scripts/crossref_history_slice_add.py)
  /mnt/data/jic823/crossref-2026-parquet/works metadata of cited DOIs

Citing works: journal-article records with a deposited reference list (n_refs > 0) whose normalised first/second ISSN
is one a resolved journal uses AND whose container title agrees with that journal (issn-containers.csv `agrees`; for
title-only resolutions the one container). Kind by the repo's title rules (scripts/canadian_journals.py classify:
front matter, editorial, review by scripts/review_books.review_like + review_extra), then: listings (BIBLIO: Isis Current
Bibliography, lists of publications, books received) are kind `bibliography` and their rows go to edges-excluded/ with
front matter; HZ-style "Name, Title. Place year" headings (NAME_CIT) are reviews; then a page-length rule: a record
the title rules call an article that spans 1-2 printed pages ('123-124') is `short` (most are untitled-as-review book
reviews, notes and notices; kept as citing works, flagged).

Graph status: 'keyed' = a key-log work (key w-...); 'unkeyed-node' = a node of the build that is not a key (doi:, openalex:,
lccn: ... ids from the two-layer tables); 'new' = no node holds the DOI.

Citing scope (user rule 2026-11-10): these works cite because the venue is history; their cited works are dead-end
nodes (no reference list of a cited work is read; nothing snowballs).

Outputs (--out): citing-works.csv.gz, edges/part-NN.csv.gz (citing_work, cited_work, citations, basis, source,
asserted_by, citing_doi, cited_doi, cited_node), cited-works.csv.gz (cited DOI not a graph node: Crossref metadata if the
DOI is in Crossref), nodoi-refs.parquet (references without DOI; spark only), report.json, samples for the hand check.
"""
import argparse, collections, csv, gzip, json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duckdb  # noqa: E402

P = "/mnt/data/jic823/crossref-2026-parquet"
SL = "/mnt/data/jic823/crossref-history-slice"
T = "/mnt/data/jic823/tools/crossref-extract/cites"
SOURCE = "crossref-2026-03"
EDGES_PER_PART = 1_500_000


# 2026-11-17 hand check: listings are not citations (Isis Current Bibliography, EHR 'List of publications on the
# economic and social history of Great Britain', 'Recent Articles on French History', 'Books Received'): kind bibliography,
# their reference rows go to edges-excluded/, not to the CITES parts
BIBLIO = re.compile(r"(?i)^\W*(?:isis\s+)?(?:\d{4}\s+)?(?:isis\s+)?current bibliography|^\W*list of publications|"
                    r"^\W*(?:other\s+)?(?:books|publications) received|^\W*recent (?:articles|books|publications|dissertations)|"
                    r"bibliography(?:\s+\d{4})?\W*$|history bibliography|bibliographical supplement|annual bibliograph|^\W*bibliographie\W*$|^\W*livres re[çc]us")
# Historische Zeitschrift-style review headings the title rules miss: 'Given Family, Title. (Series.) Place, Publisher
# year' (hand check: 2 of 20 'article' records were HZ reviews; 1,410 records match, 1,279 in HZ, 25 of 25 read reviews)
NAME_CIT = re.compile(r"^(?:[A-ZÀ-Þ][\w'’\-]*\.?\s+){1,3}[A-ZÀ-Þ][\w'’\-]+(?:\s*\((?:Hrsg|Hg|Ed|Eds|ed|eds|dir|coord)\.?\))?\s*,\s+(\S.{8,})")
CIT_MARK = re.compile(r"\b(1[5-9]\d\d|20[0-2]\d)\b|\(|/")


def page_len(p):
    m = re.match(r"^\s*(\d{1,5})\s*[-–]\s*(\d{1,5})\s*$", p or "")
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if b < a:   # '123-45' style
        if len(m.group(2)) < len(m.group(1)):
            b = int(m.group(1)[:len(m.group(1)) - len(m.group(2))] + m.group(2))
        if b < a:
            return None
    return b - a + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{T}/out")
    a = ap.parse_args()
    os.makedirs(f"{a.out}/edges", exist_ok=True)
    from canadian_journals import classify
    t0 = time.time()
    c = duckdb.connect(f"{T}/job3.duckdb")
    c.sql("set threads=12; set memory_limit='48GB'; set preserve_insertion_order=false")
    c.sql(f"set temp_directory='{T}/_tmp'")
    rep = {}
    # ---- journal scope: allowed (issn pair, container) groups
    J = list(csv.DictReader(open(f"{T}/journals-resolved.csv")))
    used = {j["jid"]: j for j in J if j["issns_used"]}
    allowed = []
    for r in csv.DictReader(open(f"{T}/issn-containers.csv")):
        if r["jid"] in used and r["agrees"]:
            i1, _, i2 = r["issn_pair"].partition(" ")
            allowed.append((i1, i2, r["container"], r["jid"], used[r["jid"]]["label"]))
    for j in used.values():
        if j["status"] in ("title_only", "main_title_only"):
            iss = j["issns_used"].split()
            allowed.append((iss[0], iss[1] if len(iss) > 1 else "", j["containers_used"], j["jid"], j["label"]))
    c.sql("create or replace table allowed (i1 varchar, i2 varchar, container varchar, jid varchar, jlabel varchar)")
    c.executemany("insert into allowed values (?,?,?,?,?)", allowed)
    c.sql(f"""create or replace table citing as
      with w as (select *, replace(upper(split_part(issn,' ',1)),'-','') wi1, replace(upper(split_part(issn,' ',2)),'-','') wi2
                 from '{SL}/works/*.parquet' where type='journal-article' and n_refs>0 and issn is not null)
      select w.doi, w.title, w.subtitle, w.container, w.issn, w.year, w.page, w.n_refs, w.publisher,
             min(al.jid) jid, min(al.jlabel) jlabel
      from w join allowed al on al.i1=w.wi1 and al.i2=w.wi2 and al.container=w.container
      group by all""")
    rep["citing_works"] = c.execute("select count(*) from citing").fetchall()[0][0]
    print("citing", rep["citing_works"], round(time.time() - t0), flush=True)
    # ---- graph status
    c.sql(f"create or replace table dk as select doi, min(key) key, count(distinct key) nkeys from '{T}/graph-doi-key.parquet' group by doi")
    c.sql(f"create or replace table wn as select key, kind from '{T}/graph-work-nodes.parquet'")
    # ---- kinds
    rows = c.sql("select doi, title, page, n_refs from citing").fetchall()
    kinds = []
    for doi, title, page, nrefs in rows:
        k = classify(title)
        pl = page_len(page)
        basis = "title"
        m = NAME_CIT.match(title or "")
        if BIBLIO.search(re.sub(r"<[^>]+>", "", title or "")):
            k, basis = "bibliography", "listing-title"
        elif k == "article" and m and CIT_MARK.search(m.group(1)) and (nrefs or 0) <= 5 and (pl is None or pl <= 4):
            k, basis = "review", "name-comma-citation"
        elif k == "article" and pl is not None and pl <= 2:
            k, basis = "short", "pages<=2"
        kinds.append((doi, k, basis, pl))
    c.sql("create or replace table kinds (doi varchar, kind varchar, kind_basis varchar, page_len integer)")
    c.executemany("insert into kinds values (?,?,?,?)", kinds)
    del rows, kinds
    print("kinds", round(time.time() - t0), flush=True)
    # ---- references of citing works
    c.sql(f"""create or replace table r as select r.doi citing_doi, r.idx, lower(trim(r.ref_doi)) ref_doi, r.doi_asserted_by,
              r.unstructured, r.author, r.year, r.article_title, r.journal_title, r.volume_title, r.series_title, r.volume,
              r.issue, r.first_page, r.isbn, r.issn, r.edition
              from '{SL}/refs/*.parquet' r semi join citing c on c.doi=r.doi""")
    rep["references"] = c.execute("select count(*) from r").fetchall()[0][0]
    rep["references_with_doi"] = c.execute("select count(*) from r where ref_doi is not null and ref_doi<>''").fetchall()[0][0]
    rep["references_with_doi_by_asserted_by"] = dict(c.sql(
        "select coalesce(doi_asserted_by,'(none)'), count(*) from r where ref_doi is not null and ref_doi<>'' group by 1").fetchall())
    print("refs", rep["references"], round(time.time() - t0), flush=True)
    # no-DOI references: spark only
    c.sql(f"""copy (select citing_doi, idx, unstructured, author, year, article_title, journal_title, volume_title, series_title,
                     volume, issue, first_page, isbn, issn, edition from r where ref_doi is null or ref_doi='')
              to '{a.out}/nodoi-refs.parquet' (format parquet, compression zstd)""")
    rep["references_without_doi"] = rep["references"] - rep["references_with_doi"]
    rep["references_without_doi_structured"] = c.sql("""select count(*) from r where (ref_doi is null or ref_doi='')
         and (article_title is not null or volume_title is not null or journal_title is not null)""").fetchall()[0][0]
    rep["references_without_doi_unstructured_only"] = c.sql("""select count(*) from r where (ref_doi is null or ref_doi='')
         and article_title is null and volume_title is null and journal_title is null and unstructured is not null""").fetchall()[0][0]
    # ---- edges
    c.sql("""create or replace table e as
      select citing_doi, ref_doi cited_doi, count(*) citations,
             string_agg(distinct coalesce(doi_asserted_by,'unknown'), ';' order by coalesce(doi_asserted_by,'unknown')) asserted_by
      from r where ref_doi is not null and ref_doi<>'' and ref_doi<>citing_doi group by 1, 2""")
    c.sql("""create or replace table e2 as
      select e.*,
        coalesce(d1.key, 'doi:'||e.citing_doi) citing_work,
        coalesce(d2.key, 'doi:'||e.cited_doi) cited_work,
        case when d2.key like 'w-%' then 'keyed' when d2.key is not null or w2.key is not null then 'unkeyed-node' else 'new' end cited_node
      from e left join dk d1 on d1.doi=e.citing_doi left join dk d2 on d2.doi=e.cited_doi
      left join wn w2 on w2.key='doi:'||e.cited_doi""")
    rep["edges"] = c.execute("select count(*) from e2").fetchall()[0][0]
    rep["edges_by_cited_node"] = dict(c.sql("select cited_node, count(*) from e2 group by 1").fetchall())
    rep["edges_by_asserted_by"] = dict(c.sql("select asserted_by, count(*) from e2 group by 1").fetchall())
    rep["cited_dois"] = c.execute("select count(distinct cited_doi) from e2").fetchall()[0][0]
    rep["cited_dois_by_node"] = dict(c.sql("select cited_node, count(distinct cited_doi) from e2 group by 1").fetchall())
    print("edges", rep["edges"], round(time.time() - t0), flush=True)
    # ---- citing works table
    c.sql("""create or replace table cw as
      select c.doi, coalesce(d.key, 'doi:'||c.doi) citing_work,
        case when d.key like 'w-%' then 'keyed' when d.key is not null or w.key is not null then 'unkeyed-node' else 'new' end in_graph,
        c.title, c.subtitle, c.year, c.container journal, c.issn, c.jid, c.jlabel journal_label, c.publisher, c.page,
        k.page_len, k.kind, k.kind_basis, c.n_refs,
        (select count(*) from e where e.citing_doi=c.doi) edges_with_doi
      from citing c join kinds k using (doi) left join dk d on d.doi=c.doi left join wn w on w.key='doi:'||c.doi""")
    rep["citing_by_in_graph"] = dict(c.sql("select in_graph, count(*) from cw group by 1").fetchall())
    rep["citing_by_kind"] = dict(c.sql("select kind, count(*) from cw group by 1").fetchall())
    rep["citing_by_decade"] = dict(c.sql("select coalesce((year//10*10)::varchar,'none') d, count(*) from cw group by 1 order by 1").fetchall())
    rep["citing_with_edges"] = c.execute("select count(*) from cw where edges_with_doi>0").fetchall()[0][0]
    rep["citing_doi_on_several_keys"] = c.execute("select count(*) from citing c join dk d using (doi) where d.nkeys>1").fetchall()[0][0]
    rep["edges_citing_on_several_keys"] = c.execute("select count(*) from e2 join dk d on d.doi=e2.citing_doi where d.nkeys>1").fetchall()[0][0]
    rep["edges_cited_on_several_keys"] = c.execute("select count(*) from e2 join dk d on d.doi=e2.cited_doi where d.nkeys>1").fetchall()[0][0]
    byj = c.sql("""select jid, journal_label, count(*) n, count(*) filter (where kind='article') articles,
                   count(*) filter (where kind='review') reviews, count(*) filter (where kind='short') short,
                   min(year) y0, max(year) y1, sum(edges_with_doi) edges,
                   count(*) filter (where in_graph<>'new') in_graph,
                   count(*) filter (where year<1950) pre1950, count(*) filter (where year between 1950 and 1999) y1950_99,
                   count(*) filter (where year between 2000 and 2009) y2000s, count(*) filter (where year between 2010 and 2019) y2010s,
                   count(*) filter (where year>=2020) y2020s
                   from cw group by 1, 2 order by n desc""")
    byj.write_csv(f"{a.out}/citing-by-journal.csv")
    c.sql(f"""copy (select doi, citing_work, in_graph, title, subtitle, year, journal, issn, jid, journal_label, publisher, page,
                     page_len, kind, kind_basis, n_refs, edges_with_doi from cw order by doi)
              to '{a.out}/citing-works.csv.gz' (header, compression gzip)""")
    EXCL = "('bibliography','front-matter')"
    # ---- cited works not a node: Crossref metadata (cited by loaded edges only)
    c.sql(f"""create or replace table cn as
      select x.cited_doi doi, x.citing, w.type, w.title, w.container, w.year, w.isbn, w.issn
      from (select cited_doi, count(distinct citing_doi) citing from e2 where cited_node='new'
                    and citing_doi not in (select doi from kinds where kind in {EXCL}) group by 1) x
      left join (select doi, type, title, container, year, isbn, issn from '{P}/works/*.parquet') w on w.doi=x.cited_doi""")
    rep["cited_new_dois"] = c.execute("select count(*) from cn").fetchall()[0][0]
    rep["cited_new_in_crossref"] = c.execute("select count(*) from cn where type is not null").fetchall()[0][0]
    rep["cited_new_by_type"] = dict(c.sql("select coalesce(type,'(not in Crossref)'), count(*) from cn group by 1 order by 2 desc").fetchall())
    c.sql(f"copy (select * from cn order by doi) to '{a.out}/cited-works.csv.gz' (header, compression gzip)")
    print("cited", round(time.time() - t0), flush=True)
    # ---- edge parts
    rep["edges_excluded_listing_or_front_matter"] = c.execute(
        f"select count(*) from e2 join kinds k on k.doi=e2.citing_doi where k.kind in {EXCL}").fetchall()[0][0]
    os.makedirs(f"{a.out}/edges-excluded", exist_ok=True)
    c.sql(f"""copy (select e2.citing_work, e2.cited_work, e2.citations, 'doi' basis, '{SOURCE}' source, e2.asserted_by,
                     e2.citing_doi, e2.cited_doi, e2.cited_node, k.kind citing_kind
              from e2 join kinds k on k.doi=e2.citing_doi where k.kind in {EXCL} order by 7, 8)
              to '{a.out}/edges-excluded/part-00.csv.gz' (header, compression gzip)""")
    c.sql(f"""create or replace table eo as select citing_work, cited_work, citations, 'doi' basis, '{SOURCE}' source, asserted_by,
              citing_doi, cited_doi, cited_node, row_number() over (order by citing_doi, cited_doi) rn
              from e2 where citing_doi not in (select doi from kinds where kind in {EXCL})""")
    n = c.execute("select count(*) from eo").fetchall()[0][0]
    rep["edges_loaded"] = n
    parts = (n + EDGES_PER_PART - 1) // EDGES_PER_PART
    for p in range(parts):
        c.sql(f"""copy (select citing_work, cited_work, citations, basis, source, asserted_by, citing_doi, cited_doi, cited_node
                  from eo where rn > {p * EDGES_PER_PART} and rn <= {(p + 1) * EDGES_PER_PART} order by rn)
                  to '{a.out}/edges/part-{p:02d}.csv.gz' (header, compression gzip)""")
    # ---- overlap with the graph's citations (same citing work)
    c.sql(f"create or replace table gc as select a, b, source from '{T}/graph-cites.parquet'")
    c.sql(f"create or replace table cx as select distinct citing_work a, cited_work b, cited_node from e2 where (citing_work not like 'doi:%' or citing_work in (select key from wn)) and citing_doi not in (select doi from kinds where kind in {EXCL})")
    c.sql("create or replace table ov_citing as select distinct a from cx where a in (select a from gc)")
    rep["overlap"] = dict(
        citing_works_with_existing_cites=c.execute("select count(*) from ov_citing").fetchall()[0][0],
        existing_sources_of_those=dict(c.sql("select source, count(*) from gc where a in (select a from ov_citing) group by 1 order by 2 desc").fetchall()),
        crossref_edges_on_those=c.execute("select count(*) from cx where a in (select a from ov_citing)").fetchall()[0][0],
        crossref_edges_on_those_to_graph_nodes=c.execute("select count(*) from cx where a in (select a from ov_citing) and cited_node<>'new'").fetchall()[0][0],
        crossref_edges_already_in_graph=c.execute("select count(*) from cx join gc using (a, b)").fetchall()[0][0],
        existing_edges_on_those=c.execute("select count(*) from gc where a in (select a from ov_citing)").fetchall()[0][0],
        existing_edges_on_those_to_doi_bearing_works=c.sql(
            "select count(*) from gc where a in (select a from ov_citing) and b in (select key from dk)").fetchall()[0][0],
        existing_doi_edges_found_by_crossref=c.sql(
            "select count(*) from gc join cx using (a, b) where gc.a in (select a from ov_citing) and gc.b in (select key from dk)").fetchall()[0][0],
    )
    o = rep["overlap"]
    o["agreement_crossref_side"] = round(o["crossref_edges_already_in_graph"] / max(1, o["crossref_edges_on_those_to_graph_nodes"]), 4)
    o["agreement_graph_side"] = round(o["existing_doi_edges_found_by_crossref"] / max(1, o["existing_edges_on_those_to_doi_bearing_works"]), 4)
    o["note"] = ("crossref side: of Crossref DOI edges from citing works the graph already cites from, whose cited DOI is a graph "
                 "node, the share the graph already has; graph side: of the graph's edges from those works to works holding a DOI, "
                 "the share Crossref also gives")
    rep["new_edges_not_in_graph"] = rep["edges"] - o["crossref_edges_already_in_graph"]
    # ---- samples for the hand check
    c.sql(f"copy (select * from (select * from e2 where citing_doi not in (select doi from kinds where kind in {EXCL})) using sample reservoir(30 rows) repeatable (17)) to '{a.out}/sample-edges.csv' (header)")
    c.sql(f"""copy (select doi, title, journal, year, page, page_len, n_refs, kind, kind_basis from (select * from cw where kind='review')
              using sample reservoir(20 rows) repeatable (17)) to '{a.out}/sample-review.csv' (header)""")
    c.sql(f"""copy (select doi, title, journal, year, page, page_len, n_refs, kind, kind_basis from (select * from cw where kind='article')
              using sample reservoir(20 rows) repeatable (17)) to '{a.out}/sample-article.csv' (header)""")
    rep["seconds"] = round(time.time() - t0)
    json.dump(rep, open(f"{a.out}/report-extract.json", "w"), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str), flush=True)


if __name__ == "__main__":
    main()
