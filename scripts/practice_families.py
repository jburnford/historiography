"""Editorial families over the practice mapping: the landing's paired atlas/record rows.

specs/2026-09-27-landing-redesign-design.md. `load_families` validates
data/evidence-layer/families-draft.csv against the atlas and the crosswalk; `family_series`
runs inside build_practice_series.py's DuckDB session, over its `items` and `mapped` tables.

Counting rules: a family's series counts distinct items tagged at theme level (hierarchy
rollups excluded) with any of its members, bridges included, so family series overlap and must
not be summed. The denominator is every item in the view and bin, tagged or not. The headline
strip splits each item equally across its primary families, so the strip's family counts plus
the unclaimed count sum to the item count. A record listed under two selected journals joins
the established view if either journal is established, and carries both journals' themes.
"""
import csv
import re
from collections import Counter

KINDS = {"atlas_entry", "record_only"}
STATUSES = {"proposed", "reviewed", "needs_decision", "rejected"}
VIEWS = ("all", "established", "reviews")
FIRST_YEAR, LAST_YEAR, BIN = 1900, 2024, 5
STRIP_FROM = 2000
ESTABLISHED = ((1970, 1974), (2015, 2019))


def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower().replace("&", "and")).strip("-")


def load_families(path, group_ids, crosswalk_targets):
    """Families in file order; each member once as primary, optionally again as a bridge."""
    with open(path, newline="") as f:
        all_rows = list(csv.DictReader(f))
    errors = [f"{r['member']}: unknown status {r['status']!r}" for r in all_rows if r["status"] not in STATUSES]
    rows = [r for r in all_rows if r["status"] != "rejected"]
    order = list(dict.fromkeys(r["family"] for r in rows))
    for r in rows:
        m = r["member"]
        if r["member_kind"] not in KINDS:
            errors.append(f"{m}: unknown member_kind {r['member_kind']!r}")
        elif r["member_kind"] == "atlas_entry" and m not in group_ids:
            errors.append(f"{m}: not an atlas field entry")
        elif r["member_kind"] == "record_only" and not m.startswith("none:"):
            errors.append(f"{m}: record_only members must be none: targets")
        if r["bridge_family"] and r["bridge_family"] not in order:
            errors.append(f"{m}: unknown bridge family {r['bridge_family']!r}")
        if r["bridge_family"] and r["bridge_family"] == r["family"]:
            errors.append(f"{m}: bridges to its own family")
    errors += [f"{m}: listed more than once (use bridge_family)"
               for m, n in Counter(r["member"] for r in rows).items() if n > 1]
    placed = {r["member"] for r in rows if r["member_kind"] == "atlas_entry"}
    errors += [f"{g}: atlas field entry has no family" for g in sorted(set(group_ids) - placed)]
    if len({slug(f) for f in order}) != len(order):
        errors.append("two families share a slug")
    if errors:
        raise SystemExit("families-draft.csv: " + "; ".join(errors))

    def member(r, primary):
        return {"id": r["member"], "kind": r["member_kind"], "primary": primary, "status": r["status"]}

    families = [{"id": slug(fam), "label": fam,
                 "members": [member(r, True) for r in rows if r["family"] == fam]
                          + [member(r, False) for r in rows if r["bridge_family"] == fam]}
                for fam in order]
    return {"families": families,
            "membership": [(f["label"], m["id"], m["primary"]) for f in families for m in f["members"]],
            "record_only_without_rows": sorted(r["member"] for r in rows if r["member_kind"] == "record_only"
                                               and r["member"] not in crosswalk_targets)}


def family_series(db, membership):
    """Share-of-period series per family and record view, plus the headline strip."""
    q = db.execute
    q("CREATE OR REPLACE TEMP TABLE fam_members (family VARCHAR, target VARCHAR, is_primary BOOLEAN)")
    db.executemany("INSERT INTO fam_members VALUES (?, ?, ?)", membership)
    (a0, a1), (b0, b1) = ESTABLISHED
    q(f"""CREATE OR REPLACE TEMP TABLE fam_established AS
          SELECT journal_key FROM items WHERE source = 'journal' AND kind = 'research_proxy'
          GROUP BY 1 HAVING count(*) FILTER (WHERE year BETWEEN {a0} AND {a1}) > 0
                        AND count(*) FILTER (WHERE year BETWEEN {b0} AND {b1}) > 0""")
    q(f"""CREATE OR REPLACE TEMP TABLE fam_universe AS
          SELECT DISTINCT v.rv, i.source || ':' || i.item AS uid, i.year // {BIN} * {BIN} AS bin
          FROM items i CROSS JOIN (VALUES ('all'), ('established'), ('reviews')) v(rv)
          WHERE i.year BETWEEN {FIRST_YEAR} AND {LAST_YEAR} AND CASE v.rv
            WHEN 'all' THEN i.source = 'journal' AND i.kind = 'research_proxy'
            WHEN 'established' THEN i.source = 'journal' AND i.kind = 'research_proxy'
                                    AND i.journal_key IN (SELECT journal_key FROM fam_established)
            ELSE i.source IN ('hnet', 'rih') AND i.kind = 'review' END""")
    q("""CREATE OR REPLACE TEMP TABLE fam_tagged AS
         SELECT DISTINCT m.source || ':' || m.item AS uid, f.family, f.is_primary
         FROM mapped m JOIN fam_members f ON f.target = m.target
         WHERE m.axis = 'theme' AND coalesce(m.status, '') <> 'rollup'""")
    views = {v: {"totals": {}, "families": {}} for v in VIEWS}
    for v, b, n in q("SELECT rv, bin, count(DISTINCT uid) FROM fam_universe GROUP BY ALL").fetchall():
        views[v]["totals"][b] = n
    for v, fam, b, n in q("""SELECT u.rv, t.family, u.bin, count(DISTINCT u.uid) FROM fam_universe u
                             JOIN (SELECT DISTINCT uid, family FROM fam_tagged) t USING (uid)
                             GROUP BY ALL""").fetchall():
        views[v]["families"].setdefault(fam, {})[b] = n
    strip_items = q(f"SELECT count(DISTINCT uid) FROM fam_universe WHERE rv = 'all' AND bin >= {STRIP_FROM}").fetchone()[0]
    strip = dict(q(f"""WITH u AS (SELECT DISTINCT uid FROM fam_universe WHERE rv = 'all' AND bin >= {STRIP_FROM}),
                            p AS (SELECT DISTINCT uid, family FROM fam_tagged WHERE is_primary),
                            k AS (SELECT uid, count(*) AS n FROM p GROUP BY 1)
                       SELECT p.family, sum(1.0 / k.n) FROM u JOIN p USING (uid) JOIN k USING (uid)
                       GROUP BY 1""").fetchall())
    return {"bins": list(range(FIRST_YEAR, LAST_YEAR - BIN + 2, BIN)), "views": views,
            "strip": {"period": [STRIP_FROM, LAST_YEAR], "items": strip_items,
                      "families": {f: round(float(x), 4) for f, x in sorted(strip.items())},
                      "unclaimed": round(strip_items - float(sum(strip.values())), 4)},
            "established_journals": q("SELECT count(*) FROM fam_established").fetchone()[0]}
