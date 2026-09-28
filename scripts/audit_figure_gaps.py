"""Figure gaps: people the review record ties to an atlas entry that the entry never names.

Editorial audit (2026-09-27), prompted by the user's finding that New cultural history named
Geertz but not Foucault, although Hunt's The New Cultural History (1989) opens its models with
O'Brien on Foucault and reviews invoke Foucault seven times as often as Geertz. The atlas had
followed Wikipedia's narrative; this audit looks for the same pattern across all entries.

Inputs (read-only): the review mention tags (generated/<mentions>/review_tags.parquet), the
per-review crosswalk themes (generated/<series>/review_themes.csv) and the curated graph.

Two lenses per atlas group entry E:
  field     reviews whose crosswalk theme is E (networks and subject headings);
  approach  reviews that invoke E's approach by name (the mentions lexicon, 31 targets).
For each person P invoked in those reviews: k = reviews in the lens invoking P, lift = the rate of
P in the lens divided by P's rate across all scanned reviews.

"Linked" means the atlas already ties P to E: P is one of E's representative people, an edge joins
P's person entry and E, or P's label appears in E's description, figures line or strands.

A candidate is unlinked with k >= MIN_K and lift >= MIN_LIFT, spread over at least MIN_YEARS years
with no single (network, year) holding more than MAX_CELL_SHARE of its reviews. `linked_elsewhere`
lists the entries the atlas does tie P to: the Foucault error was exactly a figure placed in a
sibling entry (Linguistic turn) but not in the one the record ties him to. Candidates are prompts for editorial
review, not corrections: a figure can be invoked because a field argues with them, and a lift can
reflect a single network's habits. Output holds ids and counts only; no review text.

    python3 scripts/audit_figure_gaps.py --series v17 --mentions mentions-v2 --out data/evidence-layer/audits/figure-gaps-2026-09-27
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data/evidence-layer/generated"
GRAPH = ROOT / "historiography-1920-2000.json"
HNET = ROOT / "data/hnet-graph/generated/graph.sqlite"
MIN_K, MIN_LIFT = 10, 2.0
# Burst guard: a run of reviews from one network in one year (a themed issue, a signature or
# boilerplate) is not a field's habit. Such pairs are reported separately, not as candidates.
MAX_CELL_SHARE, MIN_YEARS = 0.5, 3


def links(graph):
    """(entry, person) pairs the atlas already records."""
    people = {p["id"]: p["label"] for p in graph["people"]}
    kind = {n["id"]: n.get("entry_kind") for n in graph["nodes"]}
    out, texts = set(), {}
    for n in graph["nodes"]:
        if n.get("entry_kind") != "group":
            continue
        out |= {(n["id"], r["person_id"]) for r in n.get("representative_people") or []}
        text = json.dumps([n.get("description"), n.get("representative_figures_and_works"), n.get("strands")],
                          ensure_ascii=False)
        out |= {(n["id"], pid) for pid, label in people.items() if label in text}
        texts[n["id"]] = text
    for e in graph["edges"]:
        for a, b in ((e["source"], e["target"]), (e["target"], e["source"])):
            if kind.get(a) == "group" and kind.get(b) == "person":
                out.add((a, b))
    return out, texts


def surname_mentioned(text, label):
    """Passing mention by surname only (e.g. "Chartier appropriates Foucault"): context, not a link."""
    surname = label.split()[-1]
    return len(surname) >= 4 and surname in text


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--series", required=True)
    ap.add_argument("--mentions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    graph = json.loads(GRAPH.read_text())
    groups = {n["id"]: n["label"] for n in graph["nodes"] if n.get("entry_kind") == "group"}
    people = {p["id"]: p["label"] for p in graph["people"]}
    linked, texts = links(graph)

    db = duckdb.connect()
    tags = GEN / args.mentions / "review_tags.parquet"
    themes = GEN / args.series / "review_themes.csv"
    db.execute(f"CREATE VIEW tags AS SELECT * FROM '{tags}'")
    db.execute(f"CREATE VIEW themes AS SELECT * FROM read_csv('{themes}', all_varchar=true)")
    scanned = json.loads((GEN / args.mentions / "summary.json").read_text())["reviews_scanned"]
    base = dict(db.execute("SELECT target, count(DISTINCT item) FROM tags WHERE kind = 'person' GROUP BY 1").fetchall())

    # Lens sizes: every review carrying the theme, and every review invoking the approach.
    sizes = {("field", e): n for e, n in db.execute(
        "SELECT target, count(DISTINCT item) FROM themes GROUP BY 1").fetchall()}
    sizes |= {("approach", e): n for e, n in db.execute(
        "SELECT target, count(DISTINCT item) FROM tags WHERE kind = 'approach' GROUP BY 1").fetchall()}
    rows = db.execute("""
        SELECT 'field' AS lens, t.target AS entry, p.target AS person, list(DISTINCT p.item) AS items
        FROM themes t JOIN tags p ON p.item = t.item AND p.kind = 'person' GROUP BY ALL
        UNION ALL
        SELECT 'approach', a.target, p.target, list(DISTINCT p.item)
        FROM tags a JOIN tags p ON p.item = a.item AND a.kind = 'approach' AND p.kind = 'person' GROUP BY ALL
    """).fetchall()
    year = dict(db.execute("SELECT item, any_value(year) FROM tags GROUP BY 1").fetchall())
    db.execute(f"ATTACH '{HNET}' AS hn (TYPE sqlite, READ_ONLY)")
    network = dict(db.execute("SELECT r.id, coalesce(n.label, r.network_id) FROM hn.reviews r "
                              "LEFT JOIN hn.nodes n ON n.id = r.network_id").fetchall())
    elsewhere = defaultdict(set)
    for e, p in linked:
        elsewhere[p].add(e)

    out = []
    for lens, entry, person, items in rows:
        if entry not in groups or person not in people:
            continue
        k, n = len(items), sizes[(lens, entry)]
        cells = Counter((network.get(i, "Reviews in History" if i.startswith("rih") else "?"), year.get(i))
                        for i in items)
        lift = (k / n) / (base[person] / scanned)
        out.append({"lens": lens, "entry": entry, "entry_label": groups[entry], "person": person,
                    "person_label": people[person], "k": k, "lens_reviews": n,
                    "person_reviews_all": base[person], "lift": round(lift, 2),
                    "linked": (entry, person) in linked,
                    "surname_in_text": surname_mentioned(texts[entry], people[person]),
                    "networks": len({c[0] for c in cells}), "years": len({c[1] for c in cells}),
                    "top_cell_share": round(max(cells.values()) / k, 2),
                    "linked_elsewhere": ";".join(sorted(elsewhere[person]))})
    rank = lambda r: (-r["k"] * min(r["lift"], 20), r["entry"], r["person"])
    gap = [r for r in out if not r["linked"] and r["k"] >= MIN_K and r["lift"] >= MIN_LIFT]
    spread = lambda r: r["top_cell_share"] <= MAX_CELL_SHARE and r["years"] >= MIN_YEARS
    cand = sorted((r for r in gap if spread(r)), key=rank)
    bursts = sorted((r for r in gap if not spread(r)), key=rank)
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fields = ["lens", "entry", "entry_label", "person", "person_label", "k", "lens_reviews",
              "person_reviews_all", "lift", "linked", "surname_in_text", "networks", "years",
              "top_cell_share", "linked_elsewhere"]
    for name, rs in (("candidates.csv", cand), ("bursts.csv", bursts)):
        with open(outdir / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields + ["judgement", "note"])
            w.writeheader()
            for r in rs:
                w.writerow({**r, "judgement": "", "note": ""})
    # Known case and control, reported whatever the thresholds say.
    probe = {(r["lens"], r["entry"], r["person"]): r for r in out}
    checks = {f"{l}:{e}:{p}": probe.get((l, e, p)) for l in ("field", "approach")
              for e, p in (("culture", "foucault"), ("culture", "geertz"))}
    summary = {"series": args.series, "mentions": args.mentions, "reviews_scanned": scanned,
               "thresholds": {"min_k": MIN_K, "min_lift": MIN_LIFT, "max_cell_share": MAX_CELL_SHARE,
                              "min_years": MIN_YEARS}, "pairs_scored": len(out),
               "linked_pairs_in_atlas": len(linked), "candidates": len(cand), "bursts": len(bursts),
               "candidates_by_lens": dict(Counter(r["lens"] for r in cand)),
               "entries_with_candidates": len({r["entry"] for r in cand}),
               "checks": checks}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "checks"}, indent=1))
    for k, v in checks.items():
        print(k, v and {x: v[x] for x in ("k", "lift", "linked", "years", "top_cell_share", "linked_elsewhere")})


if __name__ == "__main__":
    main()
