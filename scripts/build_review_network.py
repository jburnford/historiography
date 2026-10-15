#!/usr/bin/env python3
"""Reviewer -> author network: who reviewed whose books, across H-Net, Reviews in History and
the Crossref journal collection, resolved to registry individuals.

Every review record names its reviewer and the people credited on the reviewed item, so each
yields edges reviewer -> author (relation `reviewed`). The sources differ:

  hnet      mentions with role `reviewer`; the item's `contributor_unspecified` (author), `editor`
            and `translator` credits. Item titles from the H-Net graph.
  rih       the same roles; `respondent` is the author answering the review, an edge
            respondent -> reviewer (relation `responded`). Item titles from the unified graph.
  crossref  JSTOR-era review deposits: a record with two or more author credits and only a first
            page credits the reviewer first and the reviewed books' authors after (checked on
            samples: Van Tine on Schneirov, Fellman on Mark M. Smith; 92% of dissertation-topic
            matches in the AHA pilot sit at position 2+). Records with more than 5 credits are
            flagged `many_credits` (film reviews credit their crews). Single-author reviews name the
            book's author only inside the title and give no edge here.

Endpoints resolve through the registry's occurrence_resolution (accepted / anchored / probable).
With --minted, credits the AHA-minted pilot (scripts/aha_minted_identities.py) attached to an
unlinked dissertation record resolve to `aha:<id>` (minted_anchored / minted_probable), only
where the registry left the credit unresolved. Names alone never join endpoints: an unresolved
endpoint stays an occurrence. An edge is strict when both ends are accepted, anchored or
minted_anchored; probable when both are resolved and one is probable; self-edges (one individual
on both ends) are dropped.

    python3 scripts/build_review_network.py --registry data/person-registry/generated/v12 \
        --minted data/person-registry/generated/aha-minted-pilot \
        --out data/person-registry/generated/review-network-v12
"""
import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CROSSREF = [ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb",
            ROOT / "data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb"]
HNET = ROOT / "data/hnet-graph/generated/graph.sqlite"
UNIFIED = ROOT / "data/unified-graph/generated/nodes.csv"
AUTHOR_ROLES = {"contributor_unspecified": "author", "author": "author", "editor": "editor",
                "translator": "translator"}
STRICT = {"accepted", "anchored", "minted_anchored"}
MANY = 5


def lit(path):
    return "'" + str(path).replace("'", "''") + "'"


def edge_tier(a, b):
    if a is None or b is None:
        return "unresolved_" + ("both" if a is None and b is None else "one")
    return "strict" if a in STRICT and b in STRICT else "probable"


def review_edges(rows):
    """rows: (corpus, record_id, item_id, role, occurrence_id, position, n_authors, last_page) for one
    record. Yields (reviewer_occ, author_occ, author_role, relation, item_id, flags)."""
    corpus = rows[0][0]
    if corpus == "crossref":
        authors = sorted((r for r in rows if r[3] == "author"), key=lambda r: r[5] or 0)
        if len(authors) < 2 or authors[0][7] is not None:
            return
        flags = "many_credits" if len(authors) > MANY else ""
        for a in authors[1:]:
            yield authors[0][4], a[4], "author", "reviewed", None, flags
        return
    reviewers = [r for r in rows if r[3] == "reviewer"]
    credited = [r for r in rows if r[3] in AUTHOR_ROLES]
    respondents = [r for r in rows if r[3] == "respondent"]
    for rv in reviewers:
        for a in credited:
            yield rv[4], a[4], AUTHOR_ROLES[a[3]], "reviewed", a[2], ""
        for rs in respondents:
            yield rs[4], rv[4], "respondent", "responded", None, ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--minted", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(args.registry / "registry.duckdb"), read_only=True)
    for i, path in enumerate(CROSSREF):
        db.execute(f"ATTACH {lit(path)} AS x{i} (READ_ONLY)")
    q = lambda s, *p: db.execute(s, *p).fetchall()

    # ---- review records and their credits ----
    rows = q("""
        WITH xr AS (SELECT record_id, last_page FROM x0.records UNION ALL SELECT record_id, last_page FROM x1.records),
        hn AS (SELECT DISTINCT record_id FROM occurrences WHERE corpus IN ('hnet', 'rih') AND role IN ('reviewer', 'respondent')),
        xa AS (SELECT record_id, count(*) AS n FROM occurrences WHERE corpus = 'crossref' AND role LIKE '%author%'
               GROUP BY 1 HAVING count(*) > 1)
        SELECT o.corpus, o.record_id, o.item_id,
               CASE WHEN o.corpus = 'crossref' THEN 'author' ELSE o.role END,
               o.occurrence_id, TRY_CAST(split_part(o.occurrence_id, ':', 4) AS INT), xa.n, xr.last_page
        FROM occurrences o LEFT JOIN xa USING (record_id) LEFT JOIN xr USING (record_id)
        WHERE (o.corpus IN ('hnet', 'rih') AND o.record_id IN (SELECT record_id FROM hn))
           OR (o.corpus = 'crossref' AND o.role LIKE '%author%' AND xa.n IS NOT NULL AND xr.last_page IS NULL)
        ORDER BY o.record_id""")
    by_record = defaultdict(list)
    for r in rows:
        by_record[r[1]].append(r)

    # ---- endpoint resolution ----
    occ_ids = {r[4] for r in rows}
    q("CREATE TEMP TABLE ep (occurrence_id VARCHAR)")
    db.executemany("INSERT INTO ep VALUES (?)", [(o,) for o in occ_ids])
    occ = {}
    for oid, name, date, venue, ind, status in q("""
            SELECT o.occurrence_id, o.name, o.record_date, o.venue, res.individual_id, res.status
            FROM ep JOIN occurrences o USING (occurrence_id) JOIN occurrence_resolution res USING (occurrence_id)"""):
        occ[oid] = dict(name=name, year=(date or "")[:4], venue=venue, ind=ind if status else None, status=status)
    minted_used = Counter()
    if args.minted:
        with open(args.minted / "credit-links.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                o = occ.get(row["occurrence_id"])
                if o and o["ind"] is None and row["tier"] in ("anchored", "probable"):
                    o["ind"], o["status"] = "aha:" + row["aha_id"], "minted_" + row["tier"]
                    minted_used[row["tier"]] += 1
    labels = dict(q("SELECT s.individual_id, s.label FROM individual_summary s JOIN "
                    "(SELECT DISTINCT individual_id FROM occurrence_resolution res JOIN ep USING (occurrence_id)) USING (individual_id)"))
    if args.minted:
        with open(args.minted / "minted-individuals.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                family, _, given = row["dissertator"].partition(",")
                labels["aha:" + row["aha_id"]] = f"{given.strip()} {family.strip()} (PhD {row['school']} {row['year']})"

    # ---- item titles ----
    titles = {}
    hn = sqlite3.connect(f"file:{HNET}?mode=ro", uri=True)
    for iid, title, year in hn.execute("SELECT id, title, publication_year FROM items"):
        titles[iid] = (title, year)
    for iid, label in db.execute(f"""SELECT id, label FROM read_csv({lit(UNIFIED)}, header=true, all_varchar=true,
            max_line_size=20000000) WHERE origin = 'reviews_in_history' AND kind IN ('bibliographic_item', 'reviewed_item')""").fetchall():
        titles[iid] = (label, None)
    xtitles = dict(q("""SELECT r.record_id, trim(coalesce(r.title_text, '') || ' ' || coalesce(r.subtitle_text, ''))
                        FROM (SELECT * FROM x0.records UNION ALL SELECT * FROM x1.records) r
                        JOIN (SELECT DISTINCT record_id FROM occurrences JOIN ep USING (occurrence_id)
                              WHERE corpus = 'crossref') USING (record_id)"""))

    # ---- edges ----
    edges, dropped = [], Counter()
    for rid, recs in by_record.items():
        for rv, au, role, relation, item, flags in review_edges(recs):
            a, b = occ.get(rv), occ.get(au)
            if not a or not b:
                dropped["endpoint_missing"] += 1
                continue
            if a["ind"] and a["ind"] == b["ind"]:
                dropped["self_edge"] += 1
                continue
            title, item_year = titles.get(item, (xtitles.get(rid), None)) if item else (xtitles.get(rid), None)
            edges.append(dict(
                corpus=recs[0][0], record_id=rid, venue=a["venue"], year=a["year"], relation=relation,
                item_id=item or "", item_title=(title or "")[:300], item_year=item_year or "",
                source_occurrence=rv, source_name=a["name"], source_individual=a["ind"] or "",
                source_status=a["status"] or "", target_occurrence=au, target_name=b["name"], target_role=role,
                target_individual=b["ind"] or "", target_status=b["status"] or "",
                tier=edge_tier(a["status"], b["status"]), flags=flags))
    fields = list(edges[0])
    with open(args.out / "review-edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(edges)

    # ---- individual-level network (both ends resolved) ----
    pairs = defaultdict(lambda: dict(n=0, years=[], venues=Counter(), corpora=set(), tiers=Counter(), items=[]))
    for e in edges:
        if e["source_individual"] and e["target_individual"] and not e["flags"]:
            p = pairs[(e["source_individual"], e["target_individual"], e["relation"])]
            p["n"] += 1
            p["corpora"].add(e["corpus"])
            p["tiers"][e["tier"]] += 1
            p["venues"][e["venue"]] += 1
            if e["year"].isdigit():
                p["years"].append(int(e["year"]))
            if e["item_title"]:
                p["items"].append(e["item_title"][:80])
    reviewed = {(s, t) for s, t, rel in pairs if rel == "reviewed"}
    out_pairs = []
    for (s, t, rel), p in pairs.items():
        out_pairs.append(dict(
            source=s, source_label=labels.get(s, ""), target=t, target_label=labels.get(t, ""), relation=rel,
            reviews=p["n"], first_year=min(p["years"], default=""), last_year=max(p["years"], default=""),
            corpora="+".join(sorted(p["corpora"])), strict=p["tiers"]["strict"] == p["n"],
            mutual=rel == "reviewed" and (t, s) in reviewed,
            venues="; ".join(v for v, _ in p["venues"].most_common(3) if v), items=" | ".join(p["items"][:3])))
    out_pairs.sort(key=lambda x: (-x["reviews"], x["source_label"]))
    with open(args.out / "individual-edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out_pairs[0]))
        w.writeheader()
        w.writerows(out_pairs)

    # ---- summary ----
    rev = [p for p in out_pairs if p["relation"] == "reviewed"]
    deg_out, deg_in = Counter(), Counter()
    for p in rev:
        deg_out[p["source"]] += 1
        deg_in[p["target"]] += 1
    nodes = set(deg_out) | set(deg_in)
    minted_edges = [e for e in edges if e["source_status"].startswith("minted") or e["target_status"].startswith("minted")]
    summary = dict(
        registry=str(args.registry), minted=str(args.minted or ""),
        review_records=len(by_record), edges=len(edges), dropped=dict(dropped),
        edges_by_corpus=dict(Counter(e["corpus"] for e in edges)),
        edges_by_relation=dict(Counter(e["relation"] for e in edges)),
        edges_by_tier=dict(Counter(e["tier"] for e in edges)),
        edges_by_corpus_tier={c: dict(Counter(e["tier"] for e in edges if e["corpus"] == c))
                              for c in sorted({e["corpus"] for e in edges})},
        flagged_many_credits=sum(e["flags"] == "many_credits" for e in edges),
        minted_endpoint_credits=dict(minted_used),
        edges_touching_minted=len(minted_edges),
        resolved_edges_touching_minted=sum(e["tier"] in ("strict", "probable") for e in minted_edges),
        individual_pairs=len(out_pairs),
        individual_reviewed_pairs=len(rev), strict_reviewed_pairs=sum(p["strict"] for p in rev),
        mutual_reviewed_pairs=sum(p["mutual"] for p in rev) // 2,
        cross_corpus_pairs=sum("+" in p["corpora"] for p in rev),
        repeat_pairs=sum(p["reviews"] > 1 for p in rev),
        responded_pairs=sum(p["relation"] == "responded" for p in out_pairs),
        network_individuals=len(nodes),
        top_reviewers=[(labels.get(i, i), n) for i, n in deg_out.most_common(10)],
        most_reviewed=[(labels.get(i, i), n) for i, n in deg_in.most_common(10)],
    )
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
