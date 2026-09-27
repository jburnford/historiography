"""Editorial families over the practice mapping: the landing's paired atlas/record rows.

specs/2026-09-27-landing-redesign-design.md. `load_families` validates
data/evidence-layer/families-draft.csv against the atlas and the crosswalk; `family_series`
runs inside build_practice_series.py's DuckDB session, over its `items` and `mapped` tables.

Counting rules: a family's series counts distinct items tagged at theme level (hierarchy
rollups excluded) with any of its members, bridges included, so family series overlap and must
not be summed. The denominator is every item in the view and bin, tagged or not. The headline
strip splits each item equally across its primary families, so strip shares plus the unclaimed
share sum to one.
"""
import csv
import re
from collections import Counter

KINDS = {"atlas_entry", "record_only"}
VIEWS = ("all", "established", "reviews")
FIRST_YEAR, LAST_YEAR, BIN = 1900, 2024, 5
STRIP_FROM = 2000
ESTABLISHED = ((1970, 1974), (2015, 2019))


def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower().replace("&", "and")).strip("-")


def load_families(path, group_ids, crosswalk_targets):
    """Families in file order; each member once as primary, optionally again as a bridge."""
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["status"] != "rejected"]
    order = list(dict.fromkeys(r["family"] for r in rows))
    errors = []
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
