"""Build the person registry: one identity authority across the atlas, H-Net, RiH and Crossref.

IDENTITY-PLAN.md steps 1, 2.1, 2.2 and 2.5. Read-only over every input; writes a new
versioned DuckDB under data/person-registry/generated/<version>/ and refuses to overwrite.

Layers, weakest to strongest:
  occurrence       one credit in one source record (never merged by name)
  claim            an identifier asserted about an occurrence: a deposited ORCID, or a
                   legacy upstream QID proposal (name-dictionary; never an identity)
  identity_link    occurrence -> person, status accepted (human-reviewed ledger),
                   anchored (deterministic identifier join), rejected or unresolved
  person_link      person <-> person or person <-> wd:Q node, by shared accepted QID or
                   Wikidata P496; union-find over these gives the established individual
An ORCID that Wikidata assigns to more than one QID is never linked; it is reported.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path

import duckdb

import identity_routes as ir

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = Path("/home/jic823/hnet-reviews")
GENERATED = ROOT / "data/person-registry/generated"
ORCID_RE =re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def lit(path):
    """SQL string literal for a trusted local path (DuckDB cannot bind ATTACH/table-function args)."""
    return "'" + str(path).replace("'", "''") + "'"


def orcid_id(value):
    m = ORCID_RE.search(value or "")
    return m.group(1).upper() if m else None


def orcid_checksum_ok(oid):
    digits = oid.replace("-", "")
    total = 0
    for ch in digits[:-1]:
        total = (total + int(ch)) * 2
    check = (12 - total % 11) % 11
    return digits[-1] == ("X" if check == 10 else str(check))


def cluster(nodes, links):
    """Union-find. links: iterable of (a, b). Returns {node: cluster_root}; root = min member."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in links:
        parent.setdefault(a, a)
        parent.setdefault(b, b)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {n: find(n) for n in parent}


def inputs(args):
    paths = {
        "atlas_graph": ROOT / "historiography-1920-2000.json",
        "atlas_wikidata": ROOT / "data/people-wikidata.json",
        "pilot_decisions": ROOT / "data/grounding-repair/decisions.json",
        "hnet_graph": ROOT / "data/hnet-graph/generated/graph.sqlite",
        "unified_nodes": ROOT / "data/unified-graph/generated/nodes.csv",
        "crossref_catalog": ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb",
        "orcid_flags": ROOT / "data/history-orcid-fanout-2026-09-22/orcid-quality-flags.csv",
        "upstream_catalog": UPSTREAM / "data/export/catalog.duckdb",
        "upstream_reviewer_grounding": UPSTREAM / "data/grounding/reviewer_grounding.csv",
        "upstream_author_grounding": UPSTREAM / "data/grounding/author_grounding.csv",
        "orcid_claimed_works": GENERATED / "orcid-claims/claimed-works.parquet",
        "orcid_names": GENERATED / "orcid-claims/orcid-names.parquet",
        "openlibrary_work_authors": GENERATED / "openlibrary/work-authors.tsv.gz",
    }
    for f in sorted((UPSTREAM / "data/grounding/mcp_results").glob("*.csv")):
        paths["upstream_mcp:" + f.name] = f
    auth = args.authorities
    manifest = json.loads((auth / "manifest.json").read_text())
    for pid in manifest:
        paths["wikidata_authority:" + pid] = auth / f"{pid}.tsv.gz"
    paths["wikidata_lifespans"] = auth / "lifespans.tsv.gz"
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise SystemExit("Missing inputs: " + ", ".join(missing))
    return paths, manifest


BOOK_ROLES = "('contributor_unspecified', 'editor', 'translator', 'author')"


def routes(db, paths):
    """Identity routes (plan 2.3-2.4). Each ties a credit to a person through a shared book,
    review or catalogued work, then gates on name compatibility within that context."""
    q = db.execute
    for fname, fn in (("isbn13", ir.isbn13), ("title_key", ir.title_key), ("folded_text", ir.folded_text)):
        db.create_function(fname, fn, [str], str, null_handling="special")
    db.create_function("end_tokens", ir.end_tokens, [str], str, null_handling="special")
    names = q(f"SELECT orcid, given, family, credit, other_names FROM read_parquet({lit(paths['orcid_names'])})").fetchall()
    var = {o: ir.variants(g, f, c, list(others or [])) for o, g, f, c, others in names}
    db.create_function("orcid_compat", lambda credit, orcid: ir.compatible_any(credit, var.get(orcid, [])),
                       [str, str], bool)
    db.create_function("full_compat", lambda credit, full: ir.compatible_any(credit, [ir.split_full(full)]),
                       [str, str], bool)
    q("CREATE TEMP TABLE orcid_family (orcid VARCHAR, fam VARCHAR)")
    db.executemany("INSERT INTO orcid_family VALUES (?, ?)",
                   sorted({(o, t[-1]) for o, vs in var.items() for g, f in vs for t in [ir.tokens(f)] if t}))
    q(f"""CREATE TEMP TABLE cw AS SELECT * FROM read_parquet({lit(paths['orcid_claimed_works'])})
          WHERE orcid_ok(orcid) AND orcid NOT IN
            (SELECT upper(orcid_id) FROM orcid_flags WHERE exclude_from_person_grounding = 'True')""")

    # Books credited in the review corpora: H-Net per item (its own citation ISBNs), RiH via the
    # upstream single-book bridge. The RiH placeholder title is excluded.
    q(f"""CREATE TEMP TABLE credit_book AS
          SELECT o.occurrence_id, o.name, it.title, TRY_CAST(it.publication_year AS INT) AS year,
                 title_key(it.title) AS tk, it.isbns AS isbn_json, NULL AS isbn
          FROM occurrences o JOIN hn.items it ON it.id = o.item_id
          WHERE o.corpus = 'hnet' AND o.role IN {BOOK_ROLES}
          UNION ALL
          SELECT o.occurrence_id, o.name, b.book_title, TRY_CAST(b.pub_year4 AS INT), title_key(b.book_title), NULL, b.isbn13
          FROM occurrences o JOIN up.review_book rb ON rb.source = 'reviews_in_history'
               AND rb.review_id = split_part(o.record_id, ':', 3)
          JOIN up.books b USING (book_id)
          WHERE o.corpus = 'rih' AND o.role IN {BOOK_ROLES} AND b.book_title <> 'Reviews in History'""")
    q("""CREATE TEMP TABLE credit_isbn AS
         SELECT DISTINCT occurrence_id, name, isbn FROM (
           SELECT occurrence_id, name, isbn13(unnest(from_json(isbn_json, '["VARCHAR"]'))) AS isbn
           FROM credit_book WHERE isbn_json IS NOT NULL
           UNION ALL SELECT occurrence_id, name, isbn13(isbn) FROM credit_book WHERE isbn IS NOT NULL)
         WHERE isbn IS NOT NULL""")
    q("""CREATE TEMP TABLE claim_isbn AS SELECT DISTINCT orcid, put_code, type, title, isbn13(i) AS isbn
         FROM (SELECT orcid, put_code, type, title, unnest(isbns) AS i FROM cw) WHERE isbn13(i) IS NOT NULL""")
    # Reviewed items for reviewer credits.
    q("""CREATE TEMP TABLE reviewer_items AS
         SELECT o.occurrence_id, o.name, it.title FROM occurrences o
         JOIN hn.edges e ON e.subject = o.record_id AND e.predicate = 'reviews_item'
         JOIN hn.items it ON it.id = e.object
         WHERE o.corpus = 'hnet' AND o.role = 'reviewer'
         UNION ALL
         SELECT o.occurrence_id, o.name, b.book_title FROM occurrences o
         JOIN up.review_book rb ON rb.source = 'reviews_in_history' AND rb.review_id = split_part(o.record_id, ':', 3)
         JOIN up.books b USING (book_id)
         WHERE o.corpus = 'rih' AND o.role = 'reviewer' AND b.book_title <> 'Reviews in History'""")

    q("""CREATE TABLE route_links (occurrence_id VARCHAR, person_id VARCHAR, status VARCHAR, basis VARCHAR,
         evidence VARCHAR)""")
    # R1: the claimed work's URL names this exact review; reviewer name compatible.
    q("""INSERT INTO route_links SELECT DISTINCT o.occurrence_id, 'orcid:' || c.orcid, 'anchored',
         'orcid_claim_review_url', 'put-code ' || c.put_code || ': ' || coalesce(c.title, '')
         FROM (SELECT orcid, put_code, title, unnest(hnet_review_ids) AS rid, 'hnet' AS corpus, 4 AS part FROM cw
               UNION ALL SELECT orcid, put_code, title, unnest(rih_review_ids), 'rih', 3 FROM cw) c
         JOIN occurrences o ON o.corpus = c.corpus AND o.role = 'reviewer'
              AND split_part(o.record_id, ':', c.part) = CAST(c.rid AS VARCHAR)
         WHERE orcid_compat(o.name, c.orcid)""")
    # R2: the ORCID holder claims a work carrying this book's ISBN; credit name compatible.
    q("""INSERT INTO route_links SELECT DISTINCT ci.occurrence_id, 'orcid:' || cl.orcid, 'anchored',
         'orcid_claim_isbn', cl.type || ' put-code ' || cl.put_code || ' ISBN ' || cl.isbn || ': ' || coalesce(cl.title, '')
         FROM credit_isbn ci JOIN claim_isbn cl USING (isbn) WHERE orcid_compat(ci.name, cl.orcid)""")
    # R3: claimed book with the same main title, year within three; credit name compatible.
    q("""INSERT INTO route_links SELECT DISTINCT cb.occurrence_id, 'orcid:' || c.orcid, 'probable',
         'orcid_claim_book_title', c.type || ' put-code ' || c.put_code || ': ' || coalesce(c.title, '')
         FROM credit_book cb JOIN (SELECT *, title_key(title) AS tk, TRY_CAST(year AS INT) AS y FROM cw
                                   WHERE type IN ('book', 'edited-book')) c ON c.tk = cb.tk
         WHERE cb.tk IS NOT NULL AND (c.y IS NULL OR cb.year IS NULL OR abs(c.y - cb.year) <= 3)
           AND orcid_compat(cb.name, c.orcid)""")
    # R4: the ORCID holder claims a review whose title contains this reviewed book's main title;
    # reviewer name compatible. Blocked on surname tokens before the containment test.
    q("""INSERT INTO route_links SELECT DISTINCT ri.occurrence_id, 'orcid:' || c.orcid, 'probable',
         'orcid_claim_review_title', 'put-code ' || c.put_code || ': ' || coalesce(c.title, '')
         FROM (SELECT *, title_key(title) AS tk, string_split(end_tokens(name), ' ') AS ends
               FROM reviewer_items) ri
         JOIN orcid_family f ON list_contains(ri.ends, f.fam)
         JOIN (SELECT orcid, put_code, title, folded_text(coalesce(title, '') || ' ' || coalesce(subtitle, '')) AS ft
               FROM cw WHERE type = 'book-review' OR folded_text(title) LIKE 'review%') c ON c.orcid = f.orcid
         WHERE ri.tk IS NOT NULL AND contains(c.ft, ri.tk) AND orcid_compat(ri.name, c.orcid)""")
    # R5: Open Library work for this review's book (title re-checked, since the upstream ISBN
    # lookup took the first hit); exactly one of its authors has a compatible name.
    q(f"""CREATE TEMP TABLE olwa AS SELECT * FROM read_csv({lit(paths['openlibrary_work_authors'])}, delim='\t',
          header=true, quote='', all_varchar=true)""")
    q(f"""CREATE TEMP TABLE ol_hits AS
          SELECT o.occurrence_id, w.author_key, any_value(w.author_name) AS author_name,
                 any_value(b.book_title) AS book_title, any_value(w.title) AS ol_title, any_value(w.work) AS work,
                 coalesce(any_value(TRY_CAST(b.pub_year4 AS INT)), any_value(TRY_CAST(left(o.record_date, 4) AS INT))) AS year
          FROM occurrences o
          JOIN up.review_book rb ON rb.source = CASE o.corpus WHEN 'hnet' THEN 'hnet' ELSE 'reviews_in_history' END
               AND rb.review_id = split_part(o.record_id, ':', CASE o.corpus WHEN 'hnet' THEN 4 ELSE 3 END)
          JOIN up.books b USING (book_id)
          JOIN olwa w ON w.work = b.ol_work_olid
          WHERE o.corpus IN ('hnet', 'rih') AND o.role IN {BOOK_ROLES} AND b.book_title <> 'Reviews in History'
            AND (title_key(b.book_title) = title_key(w.title)
                 OR contains(folded_text(b.book_title), folded_text(w.title))
                 OR contains(folded_text(w.title), folded_text(b.book_title)))
            AND full_compat(o.name, w.author_name)
          GROUP BY 1, 2""")
    q("""INSERT INTO people SELECT 'ol:' || author_key, any_value(author_name), NULL, 'openlibrary', NULL
         FROM ol_hits WHERE occurrence_id IN (SELECT occurrence_id FROM ol_hits GROUP BY 1 HAVING count(*) = 1)
         GROUP BY author_key""")
    q("""INSERT INTO route_links SELECT h.occurrence_id, 'ol:' || h.author_key, 'probable', 'openlibrary_author',
         'work ' || h.work || ' "' || coalesce(h.ol_title, '') || '" author ' || h.author_name
         FROM ol_hits h WHERE h.occurrence_id IN (SELECT occurrence_id FROM ol_hits GROUP BY 1 HAVING count(*) = 1)""")
    q("""CREATE TABLE ol_ambiguous AS SELECT occurrence_id, list(author_key) AS author_keys FROM ol_hits
         GROUP BY 1 HAVING count(*) > 1""")

    # ORCID holders reached only through their records become people too.
    q("""INSERT INTO people SELECT DISTINCT r.person_id, NULL, NULL, 'orcid_record', NULL FROM route_links r
         WHERE r.person_id LIKE 'orcid:%' AND r.person_id NOT IN (SELECT person_id FROM people)""")
    q(f"""UPDATE people SET label = trim(coalesce(n.given, '') || ' ' || coalesce(n.family, ''))
          FROM read_parquet({lit(paths["orcid_names"])}) n
          WHERE people.person_id = 'orcid:' || n.orcid AND people.label IS NULL""")
    q("""INSERT INTO identity_links SELECT occurrence_id, person_id, status, basis,
         'Route: credit tied to person through a shared work, then name-compatible', evidence, NULL, NULL
         FROM route_links""")


def build(db, paths, auth_manifest):
    q = db.execute
    q(f"ATTACH {lit(paths['crossref_catalog'])} AS xr (READ_ONLY)")
    q(f"ATTACH {lit(paths['upstream_catalog'])} AS up (READ_ONLY)")
    q("INSTALL sqlite; LOAD sqlite")
    q(f"ATTACH {lit(paths['hnet_graph'])} AS hn (TYPE sqlite, READ_ONLY)")

    # ---- occurrences -------------------------------------------------------------------
    q("""CREATE TABLE occurrences (occurrence_id VARCHAR PRIMARY KEY, corpus VARCHAR, record_id VARCHAR,
         item_id VARCHAR, role VARCHAR, name VARCHAR, given_name VARCHAR, family_name VARCHAR,
         affiliation VARCHAR, record_date VARCHAR, venue VARCHAR, source_sha256 VARCHAR)""")
    atlas = json.loads(paths["atlas_graph"].read_text())["people"]
    q("CREATE TEMP TABLE atlas_people (id VARCHAR, label VARCHAR)")
    db.executemany("INSERT INTO atlas_people VALUES (?, ?)", [(p["id"], p["label"]) for p in atlas])
    q("""INSERT INTO occurrences SELECT 'atlas:person:' || id, 'atlas', NULL, NULL, 'atlas_person', label,
         NULL, NULL, NULL, NULL, 'historiography atlas', NULL FROM atlas_people""")
    q("""INSERT INTO occurrences
         SELECT m.id, 'hnet', m.review_id, m.item_id, m.role, m.name, NULL, NULL, m.affiliation,
                r.date_month, n.label, s.json_sha256
         FROM hn.mentions m JOIN hn.reviews r ON r.id = m.review_id
         LEFT JOIN hn.sources s ON s.id = r.source_id
         LEFT JOIN hn.nodes n ON n.id = r.network_id""")
    q(f"""CREATE TEMP TABLE rih_nodes AS SELECT * FROM read_csv({lit(paths["unified_nodes"])}, header=true,
          all_varchar=true, max_line_size=20000000) WHERE origin = 'reviews_in_history'
          AND kind IN ('person_mention', 'review_record')""")
    q("""INSERT INTO occurrences
         SELECT m.id, 'rih', json_extract_string(m.data, '$.metadata.review_id'),
                json_extract_string(m.data, '$.metadata.item_id'), json_extract_string(m.data, '$.metadata.role'),
                m.label, NULL, NULL, json_extract_string(m.data, '$.metadata.affiliation'),
                json_extract_string(r.data, '$.metadata.date_month'), 'Reviews in History',
                json_extract_string(m.data, '$.source_json_sha256')
         FROM rih_nodes m LEFT JOIN rih_nodes r ON r.kind = 'review_record'
              AND r.id = json_extract_string(m.data, '$.metadata.review_id')
         WHERE m.kind = 'person_mention'""")
    q("""INSERT INTO occurrences
         SELECT c.credit_id, 'crossref', c.record_id, c.doi, c.role_array, c.name, c.given_name,
                c.family_name, json_extract_string(c.affiliation_json, '$[0].name'),
                CAST(r.publication_year AS VARCHAR), r.container_title, r.metadata_sha256
         FROM xr.contributors c JOIN xr.records r USING (record_id) WHERE NOT coalesce(r.is_test_record, false)""")

    # ---- Wikidata authority crosswalk --------------------------------------------------
    q("CREATE TABLE authority_ids (qid VARCHAR, scheme VARCHAR, value VARCHAR)")
    for pid, meta in auth_manifest.items():
        q(f"""INSERT INTO authority_ids SELECT qid, '{meta['scheme']}', value FROM
              read_csv({lit(paths['wikidata_authority:' + pid])}, delim='\t', header=true, quote='',
              columns={{'qid': 'VARCHAR', 'value': 'VARCHAR'}})""")
    q("UPDATE authority_ids SET value = upper(value) WHERE scheme IN ('orcid', 'isni')")
    q("CREATE INDEX authority_value ON authority_ids (scheme, value)")

    # ---- claims ------------------------------------------------------------------------
    q("""CREATE TABLE claims (occurrence_id VARCHAR, scheme VARCHAR, value VARCHAR, basis VARCHAR,
         confidence VARCHAR, authenticated BOOLEAN, provenance VARCHAR)""")
    db.create_function("orcid_id", orcid_id, [str], str, null_handling="special")
    q("""INSERT INTO claims SELECT credit_id, 'orcid', orcid_id(orcid), 'crossref_deposit', NULL,
         coalesce(TRY_CAST(json_extract(raw_credit_json, '$."authenticated-orcid"') AS BOOLEAN), false),
         record_id FROM xr.contributors WHERE orcid IS NOT NULL""")
    # Legacy upstream QIDs. Reviewer QIDs are stored per review row: exact attachment.
    q("""INSERT INTO claims SELECT o.occurrence_id, 'wikidata', u.reviewer_qid, 'upstream_reviewer_row',
         u.reviewer_wd_status, NULL, 'up.reviews:' || u.source || ':' || u.era || ':' || u.review_id
         FROM up.reviews u JOIN occurrences o ON o.role = 'reviewer' AND o.name = u.reviewer AND o.record_id =
           CASE WHEN u.source = 'hnet' THEN 'hnet:review:' || u.era || ':' || u.review_id
                ELSE 'rih:review:' || u.review_id END
         WHERE u.reviewer_qid IS NOT NULL""")
    # Author QIDs exist only per name string upstream: attach every distinct proposal with its file.
    q(f"""CREATE TEMP TABLE author_props AS
         SELECT name, qid, 'upstream_author_dictionary' AS basis, method AS confidence,
                'author_grounding.csv' AS file
         FROM read_csv({lit(paths["upstream_author_grounding"])}, header=true, all_varchar=true)
         WHERE status = 'matched' AND qid <> ''""")
    # Read MCP files as upstream does (csv.DictReader): some rows carry unquoted commas in the
    # trailing free-text reason, which leaves the leading fields intact.
    rows = []
    for key, p in paths.items():
        if key.startswith("upstream_mcp:"):
            with open(p, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    qid = (r.get("decided_qid") or "").strip()
                    if r["role"] != "reviewer" and qid not in ("", "none") and r["confidence"] != "low":
                        rows.append((r["name"], qid, "upstream_mcp", r["confidence"], p.name))
    db.executemany("INSERT INTO author_props VALUES (?, ?, ?, ?, ?)", rows)
    q("""INSERT INTO claims SELECT DISTINCT o.occurrence_id, 'wikidata', a.qid, a.basis, a.confidence, NULL, a.file
         FROM occurrences o JOIN author_props a ON a.name = o.name
         WHERE o.corpus IN ('hnet', 'rih') AND o.role <> 'reviewer'""")

    # ---- people and identity links -----------------------------------------------------
    q("""CREATE TABLE people (person_id VARCHAR PRIMARY KEY, label VARCHAR, preferred_qid VARCHAR,
         origin VARCHAR, note VARCHAR)""")
    q("""CREATE TABLE identity_links (occurrence_id VARCHAR, person_id VARCHAR, status VARCHAR, basis VARCHAR,
         rationale VARCHAR, evidence VARCHAR, decided_on VARCHAR, decision_id VARCHAR)""")
    atlas_wd = json.loads(paths["atlas_wikidata"].read_text())
    for row in atlas_wd["people"]:
        pid = "atlas:" + row["person_id"]
        wd = row.get("wikidata") or {}
        q("INSERT INTO people VALUES (?, ?, ?, 'atlas', ?)",
          [pid, row["label"], wd.get("qid") if row["status"] == "accepted" else None, row["status"]])
        q("INSERT INTO identity_links VALUES (?, ?, ?, 'atlas_wikidata_sheet', ?, ?, ?, NULL)",
          ["atlas:person:" + row["person_id"], pid,
           "accepted" if row["status"] == "accepted" else "unresolved",
           wd.get("basis"), "data/people-wikidata.json", atlas_wd.get("generated_on")])
    pilot = json.loads(paths["pilot_decisions"].read_text())
    for p in pilot["people"]:
        q("INSERT INTO people VALUES (?, ?, ?, 'grounding_repair_pilot', ?)",
          ["pilot:" + p["id"], p["label"], p["preferred_qid"], json.dumps(p.get("alternate_qids") or [])])
    for d in pilot["decisions"]:
        q("INSERT INTO identity_links VALUES (?, ?, ?, 'grounding_repair_pilot', ?, ?, ?, ?)",
          [d["occurrence_id"], "pilot:" + d["person_id"] if d.get("person_id") else None, d["status"],
           d.get("rationale"), json.dumps(d.get("evidence") or []), str(d.get("reviewed_on")), d["id"]])
    q("CREATE TABLE rejected_qids (occurrence_id VARCHAR, qid VARCHAR, decision_id VARCHAR)")
    db.executemany("INSERT INTO rejected_qids VALUES (?, ?, ?)",
                   [(d["occurrence_id"], qid, d["id"]) for d in pilot["decisions"]
                    for qid in d.get("rejected_qids") or []])

    # Deposited ORCIDs: one anchored person per valid, non-excluded identifier.
    q(f"CREATE TEMP TABLE orcid_flags AS SELECT * FROM read_csv({lit(paths['orcid_flags'])}, "
      "header=true, all_varchar=true)")
    db.create_function("orcid_ok", orcid_checksum_ok, [str], bool)
    q("""CREATE TABLE orcid_quality AS SELECT DISTINCT c.value AS orcid, f.flag,
         coalesce(f.exclude_from_person_grounding = 'True', false) AS excluded, orcid_ok(c.value) AS checksum_ok
         FROM claims c LEFT JOIN orcid_flags f ON upper(f.orcid_id) = c.value WHERE c.scheme = 'orcid'""")
    q("""INSERT INTO people SELECT 'orcid:' || orcid, NULL, NULL, 'crossref_deposit', flag
         FROM orcid_quality WHERE checksum_ok AND NOT excluded""")
    q("""UPDATE people SET label = s.name FROM (SELECT c.value, arg_max(o.name, o.record_date) AS name
         FROM claims c JOIN occurrences o USING (occurrence_id) WHERE c.scheme = 'orcid' GROUP BY 1) s
         WHERE people.person_id = 'orcid:' || s.value""")
    q("""INSERT INTO identity_links SELECT c.occurrence_id, 'orcid:' || c.value, 'anchored',
         CASE WHEN c.authenticated THEN 'crossref_deposit_authenticated' ELSE 'crossref_deposit' END,
         'Identifier deposited on this credit by the publisher', c.provenance, NULL, NULL
         FROM claims c JOIN orcid_quality q ON q.orcid = c.value
         WHERE c.scheme = 'orcid' AND q.checksum_ok AND NOT q.excluded""")

    routes(db, paths)

    # ---- person links and established individuals --------------------------------------
    q("""CREATE TABLE person_links (a VARCHAR, b VARCHAR, basis VARCHAR, status VARCHAR)""")
    q("""INSERT INTO person_links SELECT person_id, 'wd:' || preferred_qid, 'accepted_qid', 'accepted'
         FROM people WHERE preferred_qid IS NOT NULL""")
    for scheme, prefix, prop in (("orcid", "orcid:", "wikidata_P496"), ("openlibrary", "ol:", "wikidata_P648")):
        q(f"""CREATE TABLE {scheme}_qid_conflicts AS SELECT a.value AS {scheme}, list(DISTINCT a.qid ORDER BY a.qid) AS qids
              FROM authority_ids a JOIN people p ON p.person_id = '{prefix}' || a.value
              WHERE a.scheme = '{scheme}' GROUP BY 1 HAVING count(DISTINCT a.qid) > 1""")
        q(f"""INSERT INTO person_links SELECT DISTINCT '{prefix}' || a.value, 'wd:' || a.qid, '{prop}', 'anchored'
              FROM authority_ids a JOIN people p ON p.person_id = '{prefix}' || a.value
              WHERE a.scheme = '{scheme}' AND a.value NOT IN (SELECT {scheme} FROM {scheme}_qid_conflicts)""")
    # Lifespan gate on Open Library -> QID (P648): refuse the link when any credited book falls
    # before the person's 18th year or more than ten years after death. Catches namesake QIDs.
    q(f"""CREATE TABLE lifespans AS SELECT * FROM read_csv({lit(paths['wikidata_lifespans'])}, delim='\t',
          header=true, quote='', columns={{'qid': 'VARCHAR', 'birth_year': 'INT', 'death_year': 'INT'}})""")
    q("""CREATE TABLE lifespan_blocked AS
         SELECT l.a AS ol, l.b AS qid, any_value(ls.birth_year) AS birth_year, any_value(ls.death_year) AS death_year,
                list(DISTINCT h.year ORDER BY h.year) AS credit_years
         FROM person_links l JOIN lifespans ls ON 'wd:' || ls.qid = l.b
         JOIN ol_hits h ON 'ol:' || h.author_key = l.a
         WHERE l.basis = 'wikidata_P648' AND h.year IS NOT NULL
           AND ((ls.birth_year IS NOT NULL AND h.year < ls.birth_year + 18)
                OR (ls.death_year IS NOT NULL AND h.year > ls.death_year + 10))
         GROUP BY 1, 2""")
    q("""DELETE FROM person_links l USING lifespan_blocked b
         WHERE l.basis = 'wikidata_P648' AND l.a = b.ol AND l.b = b.qid""")
    # An Open Library author and an ORCID holder independently attributed the same credit are the
    # same person unless their QIDs disagree; clashes are recorded, not linked.
    q("""CREATE TABLE shared_credit_pairs AS
         WITH pairs AS (SELECT DISTINCT a.person_id AS ol, b.person_id AS orcid, count(*) AS credits
                        FROM route_links a JOIN route_links b USING (occurrence_id)
                        WHERE a.person_id LIKE 'ol:%' AND b.person_id LIKE 'orcid:%' GROUP BY 1, 2),
         qo AS (SELECT a, list(DISTINCT b) AS q FROM person_links WHERE b LIKE 'wd:%' GROUP BY 1)
         SELECT p.*, x.q AS ol_qids, y.q AS orcid_qids,
                x.q IS NOT NULL AND y.q IS NOT NULL AND NOT list_has_any(x.q, y.q) AS qid_clash
         FROM pairs p LEFT JOIN qo x ON x.a = p.ol LEFT JOIN qo y ON y.a = p.orcid""")
    # Open Library author records can conflate namesakes (e.g. two historians named Hannah Barker):
    # an OL node paired with more than one ORCID is not merged with any of them.
    q("""CREATE TABLE shared_credit_multi AS SELECT ol, list(orcid ORDER BY orcid) AS orcids
         FROM shared_credit_pairs GROUP BY 1 HAVING count(DISTINCT orcid) > 1""")
    q("""INSERT INTO person_links SELECT ol, orcid, 'shared_credit', 'probable'
         FROM shared_credit_pairs WHERE NOT qid_clash AND ol NOT IN (SELECT ol FROM shared_credit_multi)""")
    nodes = [r[0] for r in q("SELECT person_id FROM people").fetchall()]
    links = q("SELECT a, b FROM person_links").fetchall()
    roots = cluster(nodes, links)
    q("CREATE TABLE individuals (node VARCHAR, individual_id VARCHAR)")
    db.executemany("INSERT INTO individuals VALUES (?, ?)", sorted(roots.items()))
    q("""CREATE VIEW individual_summary AS
         SELECT i.individual_id, list(DISTINCT i.node ORDER BY i.node) FILTER (WHERE i.node NOT LIKE 'wd:%') AS people,
                list(DISTINCT substr(i.node, 4) ORDER BY substr(i.node, 4)) FILTER (WHERE i.node LIKE 'wd:%') AS qids,
                any_value(p.label) AS label
         FROM individuals i LEFT JOIN people p ON p.person_id = i.node GROUP BY 1""")
    orphan = q("""SELECT count(*) FROM identity_links l LEFT JOIN occurrences o USING (occurrence_id)
                  WHERE o.occurrence_id IS NULL""").fetchone()[0]
    if orphan:
        raise SystemExit(f"{orphan} identity links point to unknown occurrences")

    # Effective resolution: strongest tier wins (accepted > anchored > probable). Links to an
    # individual carrying a QID the pilot explicitly rejected for that credit are dropped.
    # Disagreement inside the winning tier leaves the credit unresolved and is recorded.
    q("""CREATE TABLE positive_links AS
         SELECT l.occurrence_id, l.person_id, l.status, l.basis, i.individual_id,
                CASE l.status WHEN 'accepted' THEN 3 WHEN 'anchored' THEN 2 ELSE 1 END AS tier
         FROM identity_links l JOIN individuals i ON i.node = l.person_id
         WHERE l.status IN ('accepted', 'anchored', 'probable')""")
    q("""CREATE TABLE blocked_links AS SELECT p.* FROM positive_links p
         JOIN rejected_qids r ON r.occurrence_id = p.occurrence_id
         JOIN individuals i ON i.individual_id = p.individual_id AND i.node = 'wd:' || r.qid""")
    q("""DELETE FROM positive_links p USING blocked_links b
         WHERE p.occurrence_id = b.occurrence_id AND p.person_id = b.person_id AND p.basis = b.basis""")
    q("""CREATE TABLE resolution_conflicts AS
         WITH top AS (SELECT occurrence_id, max(tier) AS tier FROM positive_links GROUP BY 1)
         SELECT p.occurrence_id, p.tier, list(DISTINCT p.individual_id ORDER BY p.individual_id) AS individuals,
                list(DISTINCT p.basis ORDER BY p.basis) AS bases
         FROM positive_links p JOIN top USING (occurrence_id, tier)
         GROUP BY 1, 2 HAVING count(DISTINCT p.individual_id) > 1""")
    fatal = q("SELECT count(*) FROM resolution_conflicts WHERE tier = 3").fetchone()[0]
    if fatal:
        raise SystemExit(f"{fatal} credits carry conflicting accepted decisions")
    q("""CREATE TABLE resolution AS
         WITH top AS (SELECT occurrence_id, max(tier) AS tier FROM positive_links GROUP BY 1)
         SELECT p.occurrence_id, any_value(p.individual_id) AS individual_id,
                any_value(p.status) AS status, list(DISTINCT p.basis ORDER BY p.basis) AS bases,
                list(DISTINCT p.person_id ORDER BY p.person_id) AS persons
         FROM positive_links p JOIN top USING (occurrence_id, tier)
         WHERE p.occurrence_id NOT IN (SELECT occurrence_id FROM resolution_conflicts)
         GROUP BY 1""")
    q("""CREATE VIEW occurrence_resolution AS
         SELECT o.occurrence_id, o.corpus, o.role, o.name, r.persons, r.status, r.bases, r.individual_id
         FROM occurrences o LEFT JOIN resolution r USING (occurrence_id)""")
    q("""CREATE VIEW legacy_name_conflicts AS SELECT o.name, list(DISTINCT c.value ORDER BY c.value) AS qids,
         count(DISTINCT o.occurrence_id) AS credits FROM claims c JOIN occurrences o USING (occurrence_id)
         WHERE c.scheme = 'wikidata' GROUP BY 1 HAVING count(DISTINCT c.value) > 1""")
    # Review queue, not identity: a name-level legacy QID that equals the QID of an individual
    # already anchored by a deposited ORCID. Two signals, one of them name-based.
    q("""CREATE VIEW legacy_bridge_candidates AS
         SELECT o.occurrence_id, o.corpus, o.role, o.name, o.affiliation, o.record_date, c.value AS qid,
                c.basis AS legacy_basis, i.individual_id, s.label AS individual_label
         FROM claims c JOIN occurrences o USING (occurrence_id)
         JOIN individuals i ON i.node = 'wd:' || c.value
         JOIN individual_summary s ON s.individual_id = i.individual_id
         WHERE c.scheme = 'wikidata' AND o.corpus IN ('hnet', 'rih')
           AND len(list_filter(s.people, x -> x LIKE 'orcid:%')) > 0
           AND o.occurrence_id NOT IN (SELECT occurrence_id FROM occurrence_resolution WHERE individual_id IS NOT NULL)""")


def summarize(db):
    one = lambda sql: db.execute(sql).fetchone()[0]
    by_corpus = db.execute("""
        SELECT o.corpus, count(*) AS occurrences,
               count(*) FILTER (WHERE r.status = 'accepted') AS accepted,
               count(*) FILTER (WHERE r.status = 'anchored') AS anchored,
               count(*) FILTER (WHERE r.status = 'probable') AS probable,
               count(*) FILTER (WHERE c.occurrence_id IS NOT NULL) AS conflicted,
               count(*) FILTER (WHERE r.status IS NULL AND c.occurrence_id IS NULL AND p.occurrence_id IS NOT NULL)
                 AS legacy_proposal_only,
               count(*) FILTER (WHERE r.status IS NULL AND c.occurrence_id IS NULL AND p.occurrence_id IS NULL)
                 AS no_identity_evidence,
               count(DISTINCT r.individual_id) FILTER (WHERE r.status IN ('accepted', 'anchored')) AS individuals_strict,
               count(DISTINCT r.individual_id) AS individuals_with_probable
        FROM occurrences o JOIN occurrence_resolution r USING (occurrence_id)
        LEFT JOIN resolution_conflicts c USING (occurrence_id)
        LEFT JOIN (SELECT DISTINCT occurrence_id FROM claims WHERE scheme = 'wikidata') p USING (occurrence_id)
        GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    cols = ["occurrences", "accepted", "anchored", "probable", "conflicted", "legacy_proposal_only",
            "no_identity_evidence", "individuals_strict", "individuals_with_probable"]
    routes = db.execute("""
        SELECT basis, count(*) AS links, count(DISTINCT occurrence_id) AS credits,
               count(DISTINCT person_id) AS people FROM route_links GROUP BY 1 ORDER BY 1""").fetchall()
    return {
        "by_corpus": {r[0]: dict(zip(cols, r[1:])) for r in by_corpus},
        "routes": {r[0]: {"links": r[1], "credits": r[2], "people": r[3]} for r in routes},
        "people": dict(db.execute("SELECT origin, count(*) FROM people GROUP BY 1 ORDER BY 1").fetchall()),
        "established_individuals_strict": one("""SELECT count(DISTINCT individual_id) FROM occurrence_resolution
             WHERE status IN ('accepted', 'anchored')"""),
        "established_individuals_with_probable": one(
            "SELECT count(DISTINCT individual_id) FROM occurrence_resolution WHERE individual_id IS NOT NULL"),
        "individuals_with_qid": one("""SELECT count(*) FROM individual_summary s WHERE len(s.qids) > 0 AND
             s.individual_id IN (SELECT individual_id FROM occurrence_resolution)"""),
        "individuals_with_multiple_qids": one("SELECT count(*) FROM individual_summary WHERE len(qids) > 1"),
        "individuals_with_multiple_orcids": one("""SELECT count(*) FROM individual_summary
             WHERE len(list_filter(people, x -> x LIKE 'orcid:%')) > 1"""),
        "cross_corpus_individuals": one("""SELECT count(*) FROM (SELECT individual_id FROM occurrence_resolution
             WHERE individual_id IS NOT NULL GROUP BY 1 HAVING count(DISTINCT corpus) > 1)"""),
        "resolution_conflicts": dict(db.execute(
            "SELECT tier, count(*) FROM resolution_conflicts GROUP BY 1 ORDER BY 1").fetchall()),
        "links_blocked_by_rejected_qid": one("SELECT count(*) FROM blocked_links"),
        "openlibrary_ambiguous_credits": one("SELECT count(*) FROM ol_ambiguous"),
        "orcid_qid_conflicts": one("SELECT count(*) FROM orcid_qid_conflicts"),
        "openlibrary_qid_conflicts": one("SELECT count(*) FROM openlibrary_qid_conflicts"),
        "shared_credit_links": one("SELECT count(*) FROM person_links WHERE basis = 'shared_credit'"),
        "shared_credit_ol_with_multiple_orcids": one("SELECT count(*) FROM shared_credit_multi"),
        "p648_links_blocked_by_lifespan": one("SELECT count(*) FROM lifespan_blocked"),
        "shared_credit_qid_clashes": one("SELECT count(*) FROM shared_credit_pairs WHERE qid_clash"),
        "excluded_or_invalid_orcids": one("SELECT count(*) FROM orcid_quality WHERE excluded OR NOT checksum_ok"),
        "legacy_name_conflicts": one("SELECT count(*) FROM legacy_name_conflicts"),
        "legacy_bridge_candidates": dict(db.execute("""SELECT corpus, count(DISTINCT occurrence_id)
             FROM legacy_bridge_candidates GROUP BY 1 ORDER BY 1""").fetchall()),
        "authority_ids": dict(db.execute("SELECT scheme, count(*) FROM authority_ids GROUP BY 1 ORDER BY 1").fetchall()),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="v1")
    ap.add_argument("--authorities", type=Path,
                    default=ROOT / "data/person-registry/generated/wikidata-authorities")
    args = ap.parse_args()
    out = ROOT / "data/person-registry/generated" / args.version
    if out.exists():
        raise SystemExit(f"{out} exists; choose a new --version")
    paths, auth_manifest = inputs(args)
    before = {k: sha(p) for k, p in paths.items()}
    tmp = out.with_name(out.name + ".building")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    db = duckdb.connect(str(tmp / "registry.duckdb"))
    db.execute("SET memory_limit = '6GB'; SET threads = 4")
    build(db, paths, auth_manifest)
    summary = summarize(db)
    db.close()
    after = {k: sha(p) for k, p in paths.items()}
    changed = [k for k in before if before[k] != after[k]]
    if changed:
        raise SystemExit("Inputs changed during build: " + ", ".join(changed))
    summary = {"built": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "inputs": {k: {"path": str(paths[k]), "sha256": v} for k, v in before.items()},
               "wikidata_authorities": auth_manifest, **summary,
               "database_sha256": sha(tmp / "registry.duckdb")}
    (tmp / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    tmp.rename(out)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("inputs", "wikidata_authorities")},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
