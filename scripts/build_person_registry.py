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

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = Path("/home/jic823/hnet-reviews")
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
    }
    for f in sorted((UPSTREAM / "data/grounding/mcp_results").glob("*.csv")):
        paths["upstream_mcp:" + f.name] = f
    auth = args.authorities
    manifest = json.loads((auth / "manifest.json").read_text())
    for pid in manifest:
        paths["wikidata_authority:" + pid] = auth / f"{pid}.tsv.gz"
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise SystemExit("Missing inputs: " + ", ".join(missing))
    return paths, manifest


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
    db.create_function("orcid_id", orcid_id, [str], str)
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

    # ---- person links and established individuals --------------------------------------
    q("""CREATE TABLE person_links (a VARCHAR, b VARCHAR, basis VARCHAR, status VARCHAR)""")
    q("""INSERT INTO person_links SELECT person_id, 'wd:' || preferred_qid, 'accepted_qid', 'accepted'
         FROM people WHERE preferred_qid IS NOT NULL""")
    q("""CREATE TABLE orcid_qid_conflicts AS SELECT a.value AS orcid, list(DISTINCT a.qid ORDER BY a.qid) AS qids
         FROM authority_ids a JOIN people p ON p.person_id = 'orcid:' || a.value
         WHERE a.scheme = 'orcid' GROUP BY 1 HAVING count(DISTINCT a.qid) > 1""")
    q("""INSERT INTO person_links SELECT DISTINCT 'orcid:' || a.value, 'wd:' || a.qid, 'wikidata_P496', 'anchored'
         FROM authority_ids a JOIN people p ON p.person_id = 'orcid:' || a.value
         WHERE a.scheme = 'orcid' AND a.value NOT IN (SELECT orcid FROM orcid_qid_conflicts)""")
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
    # Effective resolution of each occurrence: at most one active positive link is allowed.
    q("""CREATE VIEW occurrence_resolution AS
         SELECT o.occurrence_id, o.corpus, o.role, o.name, l.person_id, l.status, l.basis, i.individual_id
         FROM occurrences o
         LEFT JOIN identity_links l ON l.occurrence_id = o.occurrence_id AND l.status IN ('accepted', 'anchored')
         LEFT JOIN individuals i ON i.node = l.person_id""")
    dup = q("""SELECT occurrence_id, count(DISTINCT individual_id) FROM occurrence_resolution
               WHERE individual_id IS NOT NULL GROUP BY 1 HAVING count(DISTINCT individual_id) > 1""").fetchall()
    if dup:
        raise SystemExit(f"{len(dup)} occurrences resolve to more than one individual, e.g. {dup[:3]}")
    orphan = q("""SELECT count(*) FROM identity_links l LEFT JOIN occurrences o USING (occurrence_id)
                  WHERE o.occurrence_id IS NULL""").fetchone()[0]
    if orphan:
        raise SystemExit(f"{orphan} identity links point to unknown occurrences")
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
               count(*) FILTER (WHERE r.status IS NULL AND p.occurrence_id IS NOT NULL) AS legacy_proposal_only,
               count(*) FILTER (WHERE r.status IS NULL AND p.occurrence_id IS NULL) AS no_identity_evidence,
               count(DISTINCT r.individual_id) AS individuals
        FROM occurrences o JOIN occurrence_resolution r USING (occurrence_id)
        LEFT JOIN (SELECT DISTINCT occurrence_id FROM claims WHERE scheme = 'wikidata') p USING (occurrence_id)
        GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    cols = ["occurrences", "accepted", "anchored", "legacy_proposal_only", "no_identity_evidence", "individuals"]
    return {
        "by_corpus": {r[0]: dict(zip(cols, r[1:])) for r in by_corpus},
        "people": dict(db.execute("SELECT origin, count(*) FROM people GROUP BY 1 ORDER BY 1").fetchall()),
        "established_individuals": one("SELECT count(DISTINCT individual_id) FROM occurrence_resolution WHERE individual_id IS NOT NULL"),
        "individuals_with_qid": one("""SELECT count(*) FROM individual_summary s WHERE len(s.qids) > 0 AND
             s.individual_id IN (SELECT individual_id FROM occurrence_resolution)"""),
        "individuals_with_multiple_qids": one("SELECT count(*) FROM individual_summary WHERE len(qids) > 1"),
        "individuals_with_multiple_orcids": one("""SELECT count(*) FROM individual_summary
             WHERE len(list_filter(people, x -> x LIKE 'orcid:%')) > 1"""),
        "orcid_qid_conflicts": one("SELECT count(*) FROM orcid_qid_conflicts"),
        "excluded_or_invalid_orcids": one("SELECT count(*) FROM orcid_quality WHERE excluded OR NOT checksum_ok"),
        "cross_corpus_individuals": one("""SELECT count(*) FROM (SELECT individual_id FROM occurrence_resolution
             WHERE individual_id IS NOT NULL GROUP BY 1 HAVING count(DISTINCT corpus) > 1)"""),
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
