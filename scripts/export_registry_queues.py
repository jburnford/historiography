"""Export the person registry's human-review queues as CSVs with evidence side by side.

Reads a built registry (read-only) and writes `<registry dir>/queues/*.csv` plus
`queues/summary.json`. Rows are proposals for review; nothing here is an identity decision.
Record accepted or rejected decisions in a ledger, never by editing these exports.
"""
import argparse
import json
from pathlib import Path

import duckdb

QUEUES = {
    # Name-level upstream QID equals the QID of an ORCID-anchored individual; unresolved credit.
    "legacy-bridges": """
        SELECT b.corpus, b.role, b.name, b.affiliation AS credit_affiliation, b.record_date, b.qid,
               b.legacy_basis, b.individual_label,
               (SELECT string_agg(DISTINCT a.org || coalesce(' ' || CAST(a.start_year AS INT) || '-'
                                    || coalesce(CAST(CAST(a.end_year AS INT) AS VARCHAR), ''), ''), ' | ')
                FROM individuals i JOIN orcid_aff_all a ON 'orcid:' || a.orcid = i.node
                WHERE i.individual_id = b.individual_id) AS individual_affiliations,
               b.occurrence_id, b.individual_id
        FROM legacy_bridge_candidates b
        ORDER BY (b.affiliation IS NOT NULL AND b.affiliation <> '') DESC, b.name""",
    # Credits where several Open Library authors of the work were name-compatible.
    "openlibrary-ambiguous": """
        SELECT o.corpus, o.role, o.name, o.record_id, a.author_keys, a.occurrence_id
        FROM ol_ambiguous a JOIN occurrences o USING (occurrence_id) ORDER BY o.name""",
    # Credits whose strongest tier points to different individuals.
    "resolution-conflicts": """
        SELECT o.corpus, o.role, o.name, o.affiliation, c.tier, c.bases,
               (SELECT string_agg(s.label || ' [' || s.individual_id || ']', ' | ')
                FROM individual_summary s WHERE list_contains(c.individuals, s.individual_id)) AS individuals,
               c.occurrence_id
        FROM resolution_conflicts c JOIN occurrences o USING (occurrence_id) ORDER BY c.tier DESC, o.name""",
    # Wikidata assigns one ORCID to several items: probable duplicate items.
    "orcid-multi-qid": "SELECT orcid, qids FROM orcid_qid_conflicts ORDER BY orcid",
    # Open Library author and ORCID holder share a credit but carry different QIDs.
    "shared-credit-qid-clashes": "SELECT * FROM shared_credit_pairs WHERE qid_clash ORDER BY credits DESC",
    # Open Library records paired with more than one ORCID: possible conflated namesakes.
    "openlibrary-multi-orcid": "SELECT * FROM shared_credit_multi",
    # P648 links refused by the lifespan gate (possible wrong P648 statements on Wikidata).
    "lifespan-blocked": "SELECT * FROM lifespan_blocked ORDER BY qid",
    # Upstream names whose legacy QIDs disagree across roles or files.
    "legacy-name-conflicts": "SELECT * FROM legacy_name_conflicts ORDER BY credits DESC",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("registry", type=Path, help="e.g. data/person-registry/generated/v6")
    args = ap.parse_args()
    out = args.registry / "queues"
    out.mkdir(exist_ok=True)
    db = duckdb.connect(str(args.registry / "registry.duckdb"), read_only=True)
    # Affiliations for context: ORCID records plus Crossref deposits on anchored credits.
    summary = json.loads((args.registry / "summary.json").read_text())
    aff_path = summary["inputs"]["orcid_affiliations"]["path"]
    db.execute(f"""CREATE TEMP VIEW orcid_aff_all AS
        SELECT orcid, org, start_year, end_year FROM read_parquet('{aff_path}') WHERE org IS NOT NULL
        UNION ALL
        SELECT DISTINCT substr(l.person_id, 7), o.affiliation, TRY_CAST(o.record_date AS INT), NULL
        FROM identity_links l JOIN occurrences o USING (occurrence_id)
        WHERE l.basis LIKE 'crossref_deposit%' AND o.affiliation IS NOT NULL AND o.affiliation <> ''""")
    counts = {}
    for name, sql in QUEUES.items():
        path = out / f"{name}.csv"
        db.execute(f"COPY ({sql}) TO '{path}' (HEADER, DELIMITER ',')")
        counts[name] = db.execute(f"SELECT count(*) FROM ({sql})").fetchone()[0]
    (out / "summary.json").write_text(json.dumps(counts, indent=2) + "\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
