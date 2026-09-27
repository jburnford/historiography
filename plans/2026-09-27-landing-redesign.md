# Landing Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use usask-foundation:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the landing field view with eleven editorial families. Each family row pairs the atlas's dating (orange dots) with the family's share of the record (green bars), under a one-line headline strip. Selecting a family opens today's field view, filtered to that family.

**Architecture:**
- **Builder.** A new module, `scripts/practice_families.py`, validates `data/evidence-layer/families-draft.csv`. It computes share-of-period family series inside `build_practice_series.py`'s DuckDB session.
- **Asset.** `build_evidence_asset.py` copies those aggregates into a `families` block in the existing tracked `data/evidence-layer/site-evidence.json`, published as `docs/data/evidence.json`. No new public file.
- **Site.** A new pure module, `site/landing.mjs`, builds the strip, the rows SVG, the mobile cards and the table. `site/core.mjs` gains the `family`, `record` and derived `overview` route keys. `site/app.js` renders the landing and filters the field view to a family.

**Tech Stack:**
- Python 3.12: DuckDB, `unittest`
- Vanilla ES modules: `node:test` via `node tests/test_site_core.mjs`
- Playwright browser tests, which need a server on 4173
- Static build: `scripts/build_site.py` writes `docs/`

Spec: [specs/2026-09-27-landing-redesign-design.md](../specs/2026-09-27-landing-redesign-design.md).

## Global Constraints

**Design rules:**
- Evidence layer beside the interpretation, never merged into it. Label the tracks "where this atlas dates its schools and fields" and "share of what historians published".
- Participation, not influence. Coverage notes and caveats go with every view.
- The axis ends at 2024. The last bin is 2020–24, and 2025–26 is excluded.
- Record default: share of all research articles in the five-year bin. The denominator includes untagged and general items.
- Record views: `all` (default), `established` (research items in both 1970–74 and 2015–19), `reviews` (H-Net plus Reviews in History).
- Bridges count in each family. Family shares overlap and must not be summed, and the page says so.
- Headline strip: each item is split equally across its primary families, with an unclaimed remainder, so each bar sums to 100%.
- Person entries stay off the overview and appear on drill-down.

**Data and publishing:**
- No new public file. Families go in `data/evidence.json`, and the allowlists stay unchanged.
- Aggregates and metadata only. No review, abstract or article text, and no personal data.
- Existing deep links (`focus=`, `path=`, `node=`, `view=list`, `range=2000`, `query=`, `layer=`, `period=`, `hunt=`, `hide=`) keep opening the detailed views.

**Visual and accessibility:**
- Colours: atlas `#a8572f` (4.9:1 on `#fbfaf4`, 5.2:1 under white text), record `var(--green)` `#284f41` (9.2:1), unclaimed `#c9cdc2` with ink text (7.7:1).
- Light theme only: the site has no dark mode.
- Colour is never the only cue: dots versus bars, text labels, and a table.

**Process:**
- Commit only your own files. Other agents (Astra) may have uncommitted work in the tree. Never commit `data/wikidata/` or `data/orcid-2026-09-21/*.log`.
- Do not push. The user must say yes explicitly.
- Browser tests need `python3 -m http.server 4173 --bind 127.0.0.1 --directory docs` running in the background. Rebuild `docs/` with `python3 scripts/build_site.py` before running them.
- Changed pinned files (`site/*`, `docs/*`, and the browser tests) are logged as revision 1.123 amendments in `data/production-batches/extension-1.123/acceptance.json` (Task 8).

## File Structure

| File | Responsibility |
|---|---|
| `data/evidence-layer/families-draft.csv` (modify) | Editorial family membership. Adds `freud` and `revival`, which are currently unplaced. |
| `data/evidence-layer/approach-folds.csv` (modify) | Identity histories folds into social and cultural history. |
| `scripts/practice_families.py` (create) | `slug`, `load_families`, `family_series` |
| `tests/test_practice_families.py` (create) | Validation and counting on a DuckDB fixture |
| `scripts/build_practice_series.py` (modify) | Calls the family stage, writes `family_series.csv` and `summary.json["families"]` |
| `scripts/build_evidence_asset.py` (modify) | `families_block`, which adds `asset["families"]` |
| `tests/test_evidence_asset.py` (modify) | Family block invariants |
| `site/landing.mjs` (create) | Pure landing builders |
| `site/core.mjs` (modify) | Route keys `family`, `record`, `overview` |
| `tests/test_site_core.mjs` (modify) | Landing and route tests |
| `site/app.js`, `site/styles.css`, `site/index.html` (modify) | Landing render, family drill-down, styles, deck copy |
| `scripts/build_site.py` (modify) | Publishes `site/landing.mjs` |
| `tests/test_site_browser.py`, `tests/test_site_extension.py`, `tests/test_digital_release_browser.py` (modify) | Landing browser tests; old front-door tests move to `#family=all` |
| `site/README.md`, `data/evidence-layer/README.md`, `EVIDENCE-LAYER-PLAN.md` (modify) | Docs |

---

### Task 1: Family definitions and validation

**Files:**
- Modify: `data/evidence-layer/families-draft.csv`, `data/evidence-layer/approach-folds.csv`
- Create: `scripts/practice_families.py`
- Test: `tests/test_practice_families.py`

**Interfaces:**
- Produces:
  - `slug(label: str) -> str`
  - `load_families(path, group_ids: set[str], crosswalk_targets: set[str]) -> dict`, with keys:
    - `families`: a list of `{id, label, members: [{id, kind, primary: bool, status}]}` in file order
    - `membership`: a list of `(family_label, member_id, is_primary)`
    - `record_only_without_rows`: a sorted list of `none:` members with no crosswalk rows

  It raises `SystemExit` on invalid input.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_practice_families.py
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import practice_families as pf  # noqa: E402

HEAD = "family,member,member_kind,bridge_family,status,note\n"


def write(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    f.write(HEAD + text)
    f.close()
    return f.name


class LoadFamiliesTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(pf.slug("Political, national & international"), "political-national-and-international")
        self.assertEqual(pf.slug("Annales"), "annales")

    def test_members_bridges_and_unmapped_record_only(self):
        path = write("Social history,social,atlas_entry,,proposed,\n"
                     "Social history,women,atlas_entry,Cultural & intellectual history,reviewed,\n"
                     "Social history,none:rural_agrarian,record_only,,proposed,\n"
                     "Cultural & intellectual history,culture,atlas_entry,,proposed,\n"
                     "Cultural & intellectual history,none:history_of_knowledge,record_only,,proposed,\n")
        got = pf.load_families(path, {"social", "women", "culture"}, {"social", "women", "culture", "none:rural_agrarian"})
        self.assertEqual([f["id"] for f in got["families"]], ["social-history", "cultural-and-intellectual-history"])
        cultural = got["families"][1]
        self.assertEqual([(m["id"], m["primary"]) for m in cultural["members"]],
                         [("culture", True), ("none:history_of_knowledge", True), ("women", False)])
        self.assertIn(("Cultural & intellectual history", "women", False), got["membership"])
        self.assertIn(("Social history", "women", True), got["membership"])
        self.assertEqual(got["record_only_without_rows"], ["none:history_of_knowledge"])

    def test_rejected_rows_are_ignored(self):
        path = write("Social history,social,atlas_entry,,proposed,\nSocial history,ghost,atlas_entry,,rejected,\n")
        got = pf.load_families(path, {"social"}, set())
        self.assertEqual([m["id"] for m in got["families"][0]["members"]], ["social"])

    def test_invalid_files_fail_loudly(self):
        cases = {
            "unknown entry": ("Social history,nosuch,atlas_entry,,proposed,\n", {"social"}),
            "unplaced entry": ("Social history,social,atlas_entry,,proposed,\n", {"social", "culture"}),
            "duplicate": ("Social history,social,atlas_entry,,proposed,\nAnnales,social,atlas_entry,,proposed,\n", {"social"}),
            "unknown bridge": ("Social history,social,atlas_entry,Nowhere,proposed,\n", {"social"}),
            "bad kind": ("Social history,social,school,,proposed,\n", {"social"}),
            "record_only not none:": ("Social history,social,atlas_entry,,proposed,\nSocial history,rural,record_only,,proposed,\n", {"social"}),
        }
        for name, (text, groups) in cases.items():
            with self.subTest(name), self.assertRaises(SystemExit):
                pf.load_families(write(text), groups, set())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_practice_families -v`
Expected: `ModuleNotFoundError: No module named 'practice_families'`

- [ ] **Step 3: Write `scripts/practice_families.py` (loader part)**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tests.test_practice_families -v`
Expected: 4 tests, OK.

- [ ] **Step 5: Place the two unplaced atlas entries and fold Identity histories**

The real file currently leaves `freud` and `revival` unplaced, so the loader would reject it. Append two rows as `proposed`, with the assistant's recommendation. The user may move them: this is a data edit only.

```bash
cat >> data/evidence-layer/families-draft.csv <<'EOF'
Cultural & intellectual history,freud,atlas_entry,,proposed,"Assistant recommendation 2026-09-27: Freudian psychoanalysis is used by psychohistory (approach-folds.csv), which sits in cultural & intellectual history. Awaiting user confirmation."
Theory & method,revival,atlas_entry,Economy & social science history,proposed,"Assistant recommendation 2026-09-27: the revival of narrative is a debate about how history is written (Stone 1979, Hobsbawm 1980); it bridges social science history because it was a debate over quantification. Awaiting user confirmation."
EOF
```

Then regroup the rows so that each family's rows stay contiguous:

```bash
python3 - <<'EOF'
import csv
p = 'data/evidence-layer/families-draft.csv'
rows = list(csv.DictReader(open(p, newline='')))
order = list(dict.fromkeys(r['family'] for r in rows))
rows.sort(key=lambda r: order.index(r['family']))
w = csv.DictWriter(open(p, 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
EOF
```

Append the Identity histories folds. Relation `subfield` already exists in the file, so the builder handles it without changes.

```bash
cat >> data/evidence-layer/approach-folds.csv <<'EOF'
identity,Identity histories,social,subfield,reviewed,"User 2026-09-27: Hunt's Identity histories is not a family or umbrella; its fields sit under social and cultural history, several bridging both (families-draft.csv). The practice-hierarchy rollup rows are rejected."
identity,Identity histories,culture,subfield,reviewed,"User 2026-09-27: Hunt's Identity histories is not a family or umbrella; its fields sit under social and cultural history, several bridging both (families-draft.csv). The practice-hierarchy rollup rows are rejected."
EOF
```

- [ ] **Step 6: Validate the real file**

Run:
```bash
python3 - <<'EOF'
import csv, json, sys
sys.path.insert(0, 'scripts'); import practice_families as pf
g = json.load(open('historiography-1920-2000.json'))
groups = {n['id'] for n in g['nodes'] if n.get('entry_kind') == 'group'}
cw = {r['target'] for r in csv.DictReader(open('data/evidence-layer/practice-crosswalk.csv'))}
got = pf.load_families('data/evidence-layer/families-draft.csv', groups, cw)
print(len(got['families']), [f['id'] for f in got['families']], got['record_only_without_rows'])
EOF
```
Expected: `11 ['social-history', 'cultural-and-intellectual-history', 'annales', ...] ['none:history_of_knowledge', 'none:transnational_history']`. The two `none:` members have no crosswalk rows yet. They stay listed and are reported, not counted.

- [ ] **Step 7: Commit**

```bash
git add scripts/practice_families.py tests/test_practice_families.py data/evidence-layer/families-draft.csv data/evidence-layer/approach-folds.csv
git commit -m "Families: validated loader; place freud and revival (proposed); fold Identity histories into social and cultural history"
```

---

### Task 2: Family series (share of period, established journals, reviews, strip)

**Files:**
- Modify: `scripts/practice_families.py`
- Test: `tests/test_practice_families.py`

**Interfaces:**
- Consumes: `membership` from `load_families`.
- Consumes: a DuckDB connection holding these tables:
  - `items(source, item, source_label, year INT, kind, journal_key)`
  - `mapped(source, item, source_label, year, kind, axis, target, target_label, status)`

  These are the tables `build_practice_series.py` creates.
- Produces: `family_series(db, membership) -> dict`, with keys:
  - `bins`: `[1900, 1905, ..., 2020]`
  - `views`: `{view: {"totals": {bin: n}, "families": {family_label: {bin: n}}}}`
  - `strip`: `{period: [2000, 2024], items: int, families: {family_label: float}, unclaimed: float}`
  - `established_journals`: an int

- [ ] **Step 1: Write the failing test**

Append to `tests/test_practice_families.py`, before `if __name__`:

```python
import duckdb  # noqa: E402


class FamilySeriesTests(unittest.TestCase):
    """A small corpus whose right answers can be counted by hand."""

    def setUp(self):
        db = duckdb.connect()
        db.execute("CREATE TABLE items (source VARCHAR, item VARCHAR, source_label VARCHAR, year INT, kind VARCHAR, journal_key VARCHAR)")
        db.execute("CREATE TABLE mapped (source VARCHAR, item VARCHAR, source_label VARCHAR, year INT, kind VARCHAR, axis VARCHAR, target VARCHAR, target_label VARCHAR, status VARCHAR)")
        items = [  # j1 publishes research in 1970-74 and 2015-19 (established); j2 only later
            ("journal", "a", "s", 2016, "research_proxy", "j1"), ("journal", "a", "s2", 2016, "research_proxy", "j1"),
            ("journal", "b", "s", 2017, "research_proxy", "j2"), ("journal", "c", "s", 2018, "research_proxy", "j2"),
            ("journal", "d", "s", 1972, "research_proxy", "j1"), ("journal", "e", "s", 2016, "other", "j2"),
            ("journal", "x", "s", 2016, "research_proxy", "j1"), ("journal", "z", "s", 2026, "research_proxy", "j2"),
            ("hnet", "r1", "net", 2001, "review", None),
        ]
        db.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", items)
        mapped = [
            ("journal", "a", "s", 2016, "research_proxy", "theme", "social", "", "proposed"),
            ("journal", "b", "s", 2017, "research_proxy", "theme", "social", "", "proposed"),
            ("journal", "b", "s", 2017, "research_proxy", "theme", "culture", "", "proposed"),
            ("journal", "d", "s", 1972, "research_proxy", "theme", "economic", "", "proposed"),
            ("journal", "e", "s", 2016, "other", "theme", "social", "", "proposed"),
            ("journal", "x", "s", 2016, "research_proxy", "theme", "social", "", "rollup"),
            ("journal", "z", "s", 2026, "research_proxy", "theme", "social", "", "proposed"),
            ("hnet", "r1", "net", 2001, "review", "theme", "culture", "", "proposed"),
            ("hnet", "r1", "net", 2001, "review", "region", "europe", "", "proposed"),
        ]
        db.executemany("INSERT INTO mapped VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", mapped)
        membership = [("Social", "social", True), ("Cultural", "culture", True), ("Social", "culture", False),
                      ("Economy", "economic", True)]
        self.got = pf.family_series(db, membership)

    def test_share_of_period_counts_distinct_items_over_all_items(self):
        allv = self.got["views"]["all"]
        self.assertEqual(allv["totals"][2015], 4)          # a, b, c, x; e is not research; z is past 2024
        self.assertEqual(allv["families"]["Social"][2015], 2)   # a, b once (bridge not double counted); x is a rollup
        self.assertEqual(allv["families"]["Cultural"][2015], 1)
        self.assertEqual(allv["families"]["Economy"][1970], 1)
        self.assertNotIn(2025, allv["totals"])
        self.assertEqual(self.got["bins"][-1], 2020)

    def test_established_view_keeps_only_journals_in_both_windows(self):
        est = self.got["views"]["established"]
        self.assertEqual(self.got["established_journals"], 1)
        self.assertEqual(est["totals"][2015], 2)           # a, x from j1
        self.assertEqual(est["families"]["Social"][2015], 1)

    def test_reviews_view_and_bridges(self):
        rev = self.got["views"]["reviews"]
        self.assertEqual(rev["totals"][2000], 1)
        self.assertEqual(rev["families"]["Cultural"][2000], 1)
        self.assertEqual(rev["families"]["Social"][2000], 1)   # culture bridges into Social

    def test_strip_splits_items_across_primary_families_and_sums_to_total(self):
        s = self.got["strip"]
        self.assertEqual(s["items"], 4)
        self.assertEqual(s["families"], {"Cultural": 0.5, "Social": 1.5})
        self.assertAlmostEqual(s["unclaimed"], 2.0)
        self.assertAlmostEqual(sum(s["families"].values()) + s["unclaimed"], s["items"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_practice_families -v`
Expected: 4 errors, `AttributeError: module 'practice_families' has no attribute 'family_series'`.

- [ ] **Step 3: Implement `family_series`**

Append to `scripts/practice_families.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tests.test_practice_families -v`
Expected: 8 tests, OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/practice_families.py tests/test_practice_families.py
git commit -m "Families: share-of-period series, established-journal and review views, headline strip"
```

---

### Task 3: Wire the family stage into the practice series build

**Files:**
- Modify: `scripts/build_practice_series.py`

**Interfaces:**
- Consumes: `load_families` and `family_series` from Tasks 1 and 2.
- Produces:
  - `data/evidence-layer/generated/v17/family_series.csv`, with columns `view,family,bin,items,total`
  - `summary.json["families"]`: `family_series` output plus `definitions` (the `load_families()["families"]` list), `record_only_without_rows` and `counting`

- [ ] **Step 1: Add the input and the import**

In `scripts/build_practice_series.py`, add this under `FOLDS = ...`:

```python
FAMILIES = ROOT / "data/evidence-layer/families-draft.csv"
```

Add this after `import duckdb`:

```python
import practice_families
```

In `inputs = {...}`, add `"families": FAMILIES,` after `"folds": FOLDS,`.

- [ ] **Step 2: Compute families after the fold stage**

Insert this immediately before `summary = {`. The `entries` and `q` names already exist at that point.

```python
    # Editorial families (landing redesign): definitions validated against the atlas and crosswalk.
    fam_defs = practice_families.load_families(
        FAMILIES, set(entries), {t for (t,) in q("SELECT DISTINCT target FROM cw WHERE target IS NOT NULL").fetchall()})
    families = practice_families.family_series(db, fam_defs["membership"])
    families.update(definitions=fam_defs["families"], record_only_without_rows=fam_defs["record_only_without_rows"],
                    counting=practice_families.__doc__.split("Counting rules:")[1].strip())
```

In the `summary = {...}` literal, add this after `"journal_level_themes": {...},`:

```python
        "families": families,
```

After `q(f"COPY series TO {lit(tmp / 'series.csv')} (HEADER)")`, add:

```python
    with open(tmp / "family_series.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["view", "family", "bin", "items", "total"])
        for view, d in families["views"].items():
            for fam, bins in sorted(d["families"].items()):
                for b in sorted(bins):
                    w.writerow([view, fam, b, bins[b], d["totals"][b]])
```

At the end of `main()`, add:

```python
    print("families:", {v: sum(len(b) for b in d["families"].values()) for v, d in families["views"].items()},
          "| established journals:", families["established_journals"],
          "| strip unclaimed share:", round(families["strip"]["unclaimed"] / max(families["strip"]["items"], 1), 3))
```

- [ ] **Step 3: Run the build**

Run: `python3 scripts/build_practice_series.py --version v17`

This takes a few minutes. It reads the gitignored corpora, which exist locally.

Expected output:
- the usual summary
- `atlas entries without direct evidence: ... unaccounted: [...]`, where `identity` must now be folded rather than unaccounted
- a final `families:` line, with established journals between 60 and 100 (the sketch found 80) and an unclaimed share of roughly 0.2–0.3

If the established count falls outside 60–100, stop and report it. The sketch's rule may have differed.

- [ ] **Step 4: Check the output**

Run:
```bash
python3 - <<'EOF'
import json
s = json.load(open('data/evidence-layer/generated/v17/summary.json'))
f = s['families']
print(len(f['definitions']), f['established_journals'], f['strip'])
print('identity' in s['atlas_entries_folded'], s['atlas_entries_unaccounted'])
EOF
head -3 data/evidence-layer/generated/v17/family_series.csv
```
Expected:
- `11`, the established count, and a strip whose family values plus `unclaimed` sum to `items`
- `True` for identity being folded

- [ ] **Step 5: Commit** (only the script: generated builds are gitignored)

```bash
git add scripts/build_practice_series.py
git commit -m "Practice series v17: editorial family series (share of period, established journals, reviews)"
```

---

### Task 4: Families in the site evidence asset

**Files:**
- Modify: `scripts/build_evidence_asset.py`
- Test: `tests/test_evidence_asset.py`
- Regenerate: `data/evidence-layer/site-evidence.json`, `docs/data/evidence.json`

**Interfaces:**
- Consumes: `summary.json["families"]` from Task 3.
- Produces: `asset["families"]`, which Tasks 5 to 7 read in the browser:

```json
{"note": "...", "established_journals": 80, "bins": [1900, ..., 2020],
 "strip": {"period": [2000, 2024], "items": 123456, "shares": {"social-history": 0.2}, "unclaimed": 0.23},
 "families": [{"id": "social-history", "label": "Social history",
               "members": [{"id": "social", "primary": true}],
               "record_only": [{"id": "none:rural_agrarian", "label": "Rural & agrarian history", "primary": true}],
               "series": {"all": [[1920, 12, 900]], "established": [[1970, 30, 800]], "reviews": [[1995, 40, 2000]]}}]}
```

Each series row is `[bin, family_items, bin_total]`. Rows exist only for bins where the view has items.

- [ ] **Step 1: Write the failing tests**

Add these methods to `EvidenceAssetTests` in `tests/test_evidence_asset.py`:

```python
    def test_families_place_every_field_once_and_in_order(self):
        fams = self.asset["families"]["families"]
        self.assertEqual(len(fams), 11)
        self.assertEqual(fams[0]["label"], "Social history")
        self.assertEqual(len({f["id"] for f in fams}), 11)
        primary = [m["id"] for f in fams for m in f["members"] if m["primary"]]
        self.assertEqual(sorted(primary), sorted(self.groups), "every atlas field has exactly one primary family")

    def test_family_series_are_shares_of_a_real_total_ending_2024(self):
        block = self.asset["families"]
        for f in block["families"]:
            self.assertEqual(set(f["series"]), {"all", "established", "reviews"})
            for view, rows in f["series"].items():
                for b, items, total in rows:
                    self.assertLessEqual(items, total, (f["id"], view, b))
                    self.assertTrue(1900 <= b <= 2020 and b % 5 == 0, (f["id"], view, b))

    def test_strip_sums_to_one_and_names_its_unclaimed_share(self):
        s = self.asset["families"]["strip"]
        self.assertAlmostEqual(sum(s["shares"].values()) + s["unclaimed"], 1.0, places=2)
        self.assertEqual(s["period"], [2000, 2024])
        self.assertIn("not be summed", self.asset["families"]["note"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_evidence_asset -v`
Expected: the 3 new tests fail with `KeyError: 'families'`.

- [ ] **Step 3: Implement `families_block`**

In `scripts/build_evidence_asset.py`, add this above `def main():`:

```python
def families_block(fam, entries, cw_labels):
    """Landing data: editorial families and their share-of-period record series (aggregates only)."""
    ids = {d["label"]: d["id"] for d in fam["definitions"]}
    out = []
    for d in fam["definitions"]:
        series = {}
        for view in ("all", "established", "reviews"):
            v = fam["views"][view]
            got = v["families"].get(d["label"], {})
            series[view] = [[int(b), got.get(b, 0), v["totals"][b]] for b in sorted(v["totals"], key=int)]
        out.append({"id": d["id"], "label": d["label"],
                    "members": [{"id": m["id"], "primary": m["primary"]} for m in d["members"]
                                if m["kind"] == "atlas_entry"],
                    "record_only": [{"id": m["id"], "label": label_of(m["id"], entries, cw_labels),
                                     "primary": m["primary"]} for m in d["members"] if m["kind"] == "record_only"],
                    "series": series})
    s = fam["strip"]
    n = max(s["items"], 1)
    return {"note": "Families are editorial groupings. A field that bridges two families counts in both, so family "
                    "shares overlap and must not be summed. The headline strip is the exception: it splits each "
                    "item across its primary families.",
            "established_journals": fam["established_journals"], "bins": fam["bins"],
            "strip": {"period": s["period"], "items": s["items"],
                      "shares": {ids[k]: round(v / n, 4) for k, v in s["families"].items()},
                      "unclaimed": round(s["unclaimed"] / n, 4)},
            "families": out}
```

In `main()`, add `"families": families_block(series["families"], entries, cw_labels),` to the `asset = {...}` literal after `"fields_the_atlas_lacks": lacks,`. Update the module docstring's example command to `--series v17`.

- [ ] **Step 4: Rebuild the asset and run the tests**

Run:
```bash
python3 scripts/build_evidence_asset.py --series v17 --methods methods-v3 --mentions mentions-v2
python3 -m unittest tests.test_evidence_asset -v
```
Expected:
- `site-evidence.json: 77 entries, NN KB`, with NN under 60
- all 8 tests OK

- [ ] **Step 5: Rebuild the site and confirm nothing else moved**

Run:
```bash
python3 scripts/build_site.py && git status --short docs
```
Expected: only `docs/data/evidence.json` changed.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_evidence_asset.py tests/test_evidence_asset.py data/evidence-layer/site-evidence.json docs/data/evidence.json
git commit -m "Evidence asset: editorial families with share-of-period series and headline strip (series v17)"
```

---

### Task 5: Pure landing builders and route keys

**Files:**
- Create: `site/landing.mjs`
- Modify: `site/core.mjs`, `scripts/build_site.py`
- Test: `tests/test_site_core.mjs`

**Interfaces:**
- Consumes: `spanOf(node)` from `site/field.mjs`, and `asset.families` from Task 4.
- Produces (`site/landing.mjs`):
  - `AXIS = {start: 1880, end: 2024, coverage: 2000}`
  - `VIEWS = {all, established, reviews}`, mapping each key to its button label
  - `atlasTrack(graph, family) -> {dots: [{node, year}], early: [{node, year}], undated: [node]}`
  - `recordShares(family, view) -> [{bin, items, total, share}]`
  - `stripSegments(block, graph) -> {atlas: [{id, label, short, share, count}], record: [{id, label, short, share}], unclaimed, period}`
  - `familyBySlug(block, slug) -> family | null`
  - `familyGraph(graph, family) -> graph`: members plus adjacent person entries and internal edges only
  - `rowsSvg({block, graph, view, width}) -> string`
  - `cardsHtml({block, graph, view, href}) -> string`, where `href` maps a family id to a hash
  - `tableHtml({block, graph, view}) -> string`
- Produces (`site/core.mjs`): `readRoute` returns `family` (a slug or `'all'`), `record` (`''`, `'established'` or `'reviews'`) and `overview` (a boolean). `routeHash` never writes `overview`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_site_core.mjs`, add this after the existing imports:

```js
import {AXIS, atlasTrack, recordShares, stripSegments, familyBySlug, familyGraph, rowsSvg, cardsHtml, tableHtml} from '../site/landing.mjs';
const families = JSON.parse(readFileSync(new URL('../data/evidence-layer/site-evidence.json', import.meta.url))).families;
```

Append these tests at the end of the file:

```js
test('landing: every family member is dated, early or undated, never dropped', () => {
  const ids = new Set(graph.nodes.map(n => n.id));
  for (const f of families.families) {
    const t = atlasTrack(graph, f);
    assert.equal(t.dots.length + t.early.length + t.undated.length, f.members.filter(m => ids.has(m.id)).length, f.id);
    for (const d of t.dots) assert.ok(d.year >= AXIS.start, f.id);
    for (const d of t.early) assert.ok(d.year < AXIS.start, f.id);
  }
});
test('landing: record shares are items over the bin total and stop at 2024', () => {
  for (const f of families.families) for (const view of ['all', 'established', 'reviews']) {
    for (const s of recordShares(f, view)) {
      assert.ok(s.share >= 0 && s.share <= 1, `${f.id} ${view} ${s.bin}`);
      assert.equal(s.share, s.total ? s.items / s.total : 0);
      assert.ok(s.bin + 4 <= AXIS.end);
    }
  }
});
test('landing: both strip bars sum to one', () => {
  const s = stripSegments(families, graph);
  assert.ok(Math.abs(s.atlas.reduce((a, x) => a + x.share, 0) - 1) < 1e-9);
  assert.ok(Math.abs(s.record.reduce((a, x) => a + x.share, 0) + s.unclaimed - 1) < 0.01);
  assert.equal(s.atlas.length, 11);
});
test('landing: a family subgraph holds its fields, their person entries, and internal edges only', () => {
  const annales = familyBySlug(families, 'annales');
  assert.ok(annales);
  assert.equal(familyBySlug(families, 'nosuch'), null);
  const sub = familyGraph(graph, annales);
  const ids = new Set(sub.nodes.map(n => n.id));
  assert.ok(ids.has('annales'));
  for (const n of sub.nodes) assert.ok(n.id === 'annales' || n.entry_kind === 'person', n.id);
  for (const e of sub.edges) assert.ok(ids.has(e.source) && ids.has(e.target), e.id);
});
test('landing: rows, cards and table render one item per family', () => {
  const svg = rowsSvg({block: families, graph, view: 'all', width: 1100});
  assert.equal((svg.match(/class="family-row"/g) || []).length, 11);
  assert.match(svg, /data-family="annales"/);
  assert.match(svg, /class="coverage-line"/);
  const cards = cardsHtml({block: families, graph, view: 'reviews', href: id => `#family=${id}`});
  assert.equal((cards.match(/class="family-card"/g) || []).length, 11);
  const table = tableHtml({block: families, graph, view: 'established'});
  assert.equal((table.match(/<tr>/g) || []).length, 12);
});
test('routes: the bare front door is the overview; deep links still open the detail views', () => {
  assert.equal(readRoute('', graph, pathways).overview, true);
  assert.equal(readRoute('#record=reviews', graph, pathways).overview, true);
  assert.equal(readRoute('#view=map', graph, pathways).overview, true);   // routeHash always writes view=map
  assert.equal(readRoute('#record=reviews', graph, pathways).record, 'reviews');
  assert.equal(readRoute('#record=bogus', graph, pathways).record, '');
  const detail = ['#family=annales', '#family=all', '#focus=marx', '#path=paradigms_and_limits', '#view=list',
                  '#range=2000', '#query=thompson', '#node=marx', '#tab=people'];
  for (const h of detail) assert.equal(readRoute(h, graph, pathways).overview, false, h);
  assert.equal(readRoute('#family=annales', graph, pathways).family, 'annales');
  assert.equal(readRoute('#family=Not%20A%20Slug!', graph, pathways).family, '');
  /* Links the site writes must land where they were written from. */
  for (const h of ['', '#record=established', ...detail]) {
    const r = readRoute(h, graph, pathways), hash = routeHash(r);
    assert.doesNotMatch(hash, /overview/, h);
    assert.equal(readRoute(hash, graph, pathways).overview, r.overview, h);
  }
  assert.match(routeHash(readRoute('#family=annales&record=reviews', graph, pathways)), /family=annales&record=reviews/);
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `node tests/test_site_core.mjs`
Expected: `ERR_MODULE_NOT_FOUND` for `../site/landing.mjs`.

- [ ] **Step 3: Write `site/landing.mjs`**

```js
/* The landing: eleven editorial families, the atlas's dating beside the record's share of
   what historians published. Pure builders; app.js renders and wires them.
   specs/2026-09-27-landing-redesign-design.md */
import {spanOf} from './field.mjs';

export const AXIS = {start: 1880, end: 2024, coverage: 2000};
export const VIEWS = {all: 'All journals', established: 'Established journals only', reviews: 'Reviews'};

const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const pct = x => `${(x * 100).toFixed(1)}%`;
const short = f => f.label.split(/[\s,&]/)[0];

/* Where the atlas dates each member: its first year (curated span, else the date label). */
export function atlasTrack(graph, family) {
  const byId = new Map(graph.nodes.map(n => [n.id, n]));
  const dots = [], early = [], undated = [];
  for (const m of family.members) {
    const node = byId.get(m.id);
    if (!node) continue;
    const s = spanOf(node);
    if (!s) undated.push(node);
    else (s.start < AXIS.start ? early : dots).push({node, year: s.start});
  }
  dots.sort((a, b) => a.year - b.year || a.node.label.localeCompare(b.node.label));
  return {dots, early, undated};
}

export function recordShares(family, view) {
  return (family.series[view] || []).filter(([bin]) => bin + 4 <= AXIS.end)
    .map(([bin, items, total]) => ({bin, items, total, share: total ? items / total : 0}));
}

/* The gap in one line: primary members only, so each bar sums to 100%. */
export function stripSegments(block, graph) {
  const groups = new Set(graph.nodes.filter(n => n.entry_kind === 'group').map(n => n.id));
  const count = f => f.members.filter(m => m.primary && groups.has(m.id)).length;
  const total = block.families.reduce((a, f) => a + count(f), 0) || 1;
  return {
    atlas: block.families.map(f => ({id: f.id, label: f.label, short: short(f), share: count(f) / total, count: count(f)})),
    record: block.families.map(f => ({id: f.id, label: f.label, short: short(f), share: block.strip.shares[f.id] || 0})),
    unclaimed: block.strip.unclaimed, period: block.strip.period,
  };
}

export function familyBySlug(block, slug) {
  return block?.families?.find(f => f.id === slug) || null;
}

/* The field view for one family: its fields (bridges included), the person entries linked to
   them, and only the relationships among those. Journals follow via journalNodes. */
export function familyGraph(graph, family) {
  const keep = new Set(family.members.map(m => m.id));
  const kind = new Map(graph.nodes.map(n => [n.id, n.entry_kind]));
  const ids = new Set(keep);
  for (const e of graph.edges) {
    if (keep.has(e.source) && kind.get(e.target) === 'person') ids.add(e.target);
    if (keep.has(e.target) && kind.get(e.source) === 'person') ids.add(e.source);
  }
  return {...graph, nodes: graph.nodes.filter(n => ids.has(n.id)),
    edges: graph.edges.filter(e => ids.has(e.source) && ids.has(e.target))};
}

const peakOf = (block, view) => Math.max(0.01, ...block.families.flatMap(f => recordShares(f, view).map(s => s.share)));

/* Paired rows on one axis. `width` is the measured width of the box the SVG sits in. */
export function rowsSvg({block, graph, view = 'all', width = 1000}) {
  const labelW = Math.min(250, Math.max(150, width * 0.24));
  const x0 = labelW + 16, x1 = width - 16, rowH = 58, top = 26, foot = 26, barMax = 26;
  const x = y => x0 + (Math.max(y, AXIS.start) - AXIS.start) / (AXIS.end + 1 - AXIS.start) * (x1 - x0);
  const peak = peakOf(block, view);
  const H = top + block.families.length * rowH + foot, bw = Math.max(1, x(2005) - x(2000) - 1.5);
  const grid = [1900, 1920, 1940, 1960, 1980, 2000, 2020].map(y =>
    `<line class="grid" x1="${x(y).toFixed(1)}" x2="${x(y).toFixed(1)}" y1="${top}" y2="${H - foot}"/>` +
    `<text class="tick" x="${x(y).toFixed(1)}" y="${H - 9}" text-anchor="middle">${y}</text>`).join('');
  const rows = block.families.map((f, i) => {
    const t = atlasTrack(graph, f), shares = recordShares(f, view);
    const y0 = top + i * rowH, base = y0 + rowH - 6;
    const dots = t.dots.map(d => `<circle class="atlas-dot" cx="${x(d.year).toFixed(1)}" cy="${y0 + 13}" r="4"><title>${esc(d.node.label)} · ${d.year}</title></circle>`).join('');
    const early = t.early.length ? `<text class="early-mark" x="${x0 - 3}" y="${y0 + 17}">◂<title>${esc(`Dated before ${AXIS.start}: ${t.early.map(e => `${e.node.label} (${e.year})`).join('; ')}`)}</title></text>` : '';
    const bars = shares.filter(s => s.items).map(s => {
      const h = s.share / peak * barMax;
      return `<rect class="record-bar" x="${x(s.bin).toFixed(1)}" y="${(base - h).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}"><title>${s.bin}–${s.bin + 4}: ${pct(s.share)} (${s.items.toLocaleString('en')} of ${s.total.toLocaleString('en')})</title></rect>`;
    }).join('');
    const dated = t.dots.length + t.early.length;
    const label = `${f.label}: ${dated} dated atlas entr${dated === 1 ? 'y' : 'ies'}${t.undated.length ? `, ${t.undated.length} undated` : ''}; share of the record in ${shares.at(-1)?.bin ?? '—'}–${AXIS.end}: ${pct(shares.at(-1)?.share || 0)}. Open its fields.`;
    return `<g class="family-row" data-family="${esc(f.id)}" tabindex="0" role="link" aria-label="${esc(label)}">` +
      `<rect class="row-hit" x="0" y="${y0}" width="${width}" height="${rowH}"/>` +
      `<text class="family-label" x="${labelW}" y="${y0 + rowH / 2 + 5}" text-anchor="end">${esc(f.label)} ›</text>` +
      `<line class="row-base" x1="${x0}" x2="${x1}" y1="${base + 0.5}" y2="${base + 0.5}"/>${bars}${dots}${early}</g>`;
  }).join('');
  const cx = x(AXIS.coverage).toFixed(1);
  const wall = `<line class="coverage-line" x1="${cx}" x2="${cx}" y1="${top - 6}" y2="${H - foot}"/>` +
    `<text class="coverage-label" x="${(+cx + 5).toFixed(1)}" y="${top - 10}">atlas coverage ends ${AXIS.coverage}</text>`;
  return `<svg class="landing-svg" viewBox="0 0 ${width} ${H}" width="${width}" height="${H}" role="group" aria-label="Families of historical writing: atlas dating and share of the record, ${AXIS.start}–${AXIS.end}">${grid}${wall}${rows}</svg>`;
}

/* Narrow screens: one card per family, on the same shared scale from 1950. */
export function cardsHtml({block, graph, view = 'all', href}) {
  const peak = peakOf(block, view);
  return `<ol class="family-cards">${block.families.map(f => {
    const t = atlasTrack(graph, f), s = recordShares(f, view).filter(b => b.bin >= 1950);
    const bars = s.map((b, i) => { const h = b.share / peak * 28; return `<rect x="${i * 9}" y="${(30 - h).toFixed(1)}" width="8" height="${h.toFixed(1)}"/>`; }).join('');
    const first = [...t.early, ...t.dots].map(d => d.year).sort((a, b) => a - b)[0];
    const n = t.dots.length + t.early.length + t.undated.length;
    return `<li><a class="family-card" href="${esc(href(f.id))}"><h3>${esc(f.label)}</h3>` +
      `<p><strong>${n}</strong> atlas entr${n === 1 ? 'y' : 'ies'}${first ? `, earliest ${first}` : ''}</p>` +
      `<svg class="card-bars" viewBox="0 0 ${Math.max(9, s.length * 9)} 31" preserveAspectRatio="none" role="img" aria-label="${esc(`Share of the record from 1950: ${s.map(b => `${b.bin} ${pct(b.share)}`).join(', ')}`)}">${bars}</svg>` +
      `<p class="fine-print">${s.length ? `${s.at(-1).bin}–${AXIS.end}: ${pct(s.at(-1).share)} of the record` : 'No record in this view'}</p></a></li>`;
  }).join('')}</ol>`;
}

/* The same numbers as text. */
export function tableHtml({block, graph, view = 'all'}) {
  const bins = [...new Set(block.families.flatMap(f => recordShares(f, view).map(s => s.bin)))]
    .filter(b => b >= 1920).sort((a, b) => a - b);
  const head = `<tr><th scope="col">Family</th><th scope="col">Atlas entries</th><th scope="col">Undated</th>${bins.map(b => `<th scope="col">${b}–${String(b + 4).slice(2)}</th>`).join('')}</tr>`;
  const rows = block.families.map(f => {
    const t = atlasTrack(graph, f), by = new Map(recordShares(f, view).map(s => [s.bin, s]));
    return `<tr><th scope="row">${esc(f.label)}</th><td>${t.dots.length + t.early.length + t.undated.length}</td><td>${t.undated.length}</td>${bins.map(b => {
      const s = by.get(b);
      return `<td${s ? ` title="${s.items.toLocaleString('en')} of ${s.total.toLocaleString('en')}"` : ''}>${s ? pct(s.share) : '—'}</td>`;
    }).join('')}</tr>`;
  }).join('');
  return `<div class="table-scroll"><table><caption class="sr-only">Atlas entries and share of the record (${esc(VIEWS[view])}) per family and five-year period</caption><thead>${head}</thead><tbody>${rows}</tbody></table></div>`;
}
```

- [ ] **Step 4: Add the route keys in `site/core.mjs`**

In `readRoute`, add these properties inside the `route = {...}` literal, after `hide: ...`:

```js
    /* `family` opens one editorial family's fields ('all' = every entry on one axis);
       `record` picks the landing's record view. */
    family: /^[a-z0-9-]{2,60}$/.test(p.get('family') || '') ? p.get('family') : '',
    record: ['established', 'reviews'].includes(p.get('record')) ? p.get('record') : '',
```

Immediately before `return route;`, add:

```js
  /* The bare front door is the families overview. Any value that names a detailed field state
     (and the exact 2000 view) opens the detailed field instead, so old links keep working.
     Values, not key presence: routeHash always writes view=map, so only view=list is a detail. */
  const detail = route.family || route.focus || route.path || p.get('view') === 'list' || route.query
    || route.layer || route.period || route.hunt || route.hide || route.range;
  route.overview = route.tab === 'map' && !route.node && !route.person && !detail;
```

In `routeHash`, change the condition inside the loop to:

```js
    if (v && k !== 'overview' && !(k === 'tab' && v === 'map')) p.set(k, v === true ? '1' : String(v));
```

- [ ] **Step 5: Publish the module**

In `scripts/build_site.py`, add `'site/landing.mjs': 'landing.mjs',` to `PAGE_ASSETS` after `'site/people.mjs'`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `node tests/test_site_core.mjs`
Expected: all tests pass (`# fail 0`).

- [ ] **Step 7: Commit** (`docs/` is rebuilt in Task 6, once the app uses the module)

```bash
git add site/landing.mjs site/core.mjs scripts/build_site.py tests/test_site_core.mjs
git commit -m "Landing builders (strip, paired rows, cards, table) and family/record/overview routes"
```

---

### Task 6: Render the landing

**Files:**
- Modify: `site/app.js`, `site/styles.css`, `site/index.html`
- Test: `tests/test_site_browser.py`
- Rebuild: `docs/`

**Interfaces:**
- Consumes: everything `site/landing.mjs` produces, plus `state.overview`, `state.record` and `state.family`.
- Produces:
  - DOM: `.landing-page`, `.strip-bar.atlas .seg` (11), `.strip-bar.record .seg` (12, including `.unclaimed`), `.landing-rows svg.landing-svg .family-row` (11), `.family-cards li` (11), `details.landing-table`
  - Toggle links named exactly as in `VIEWS`, with `aria-pressed`

- [ ] **Step 1: Write the failing browser test**

In `tests/test_site_browser.py`, update the `open()` locator so the landing counts as a loaded page. Change `'.field-page, .layer-card, ...'` to begin with `'.landing-page, .field-page, .layer-card, ...'`.

Then add this test:

```python
    def test_landing_families_strip_and_record_views(self):
        """The front door: eleven families, the atlas's dating beside the record's share."""
        self.open()
        expect(self.page.locator('.landing-page')).to_be_visible()
        expect(self.page.locator('svg.landing-svg .family-row')).to_have_count(11)
        expect(self.page.locator('.strip-bar.atlas .seg')).to_have_count(11)
        expect(self.page.locator('.strip-bar.record .seg')).to_have_count(12)
        expect(self.page.locator('.strip-bar.record .seg.unclaimed')).to_contain_text('%')
        expect(self.page.locator('.landing-page')).to_contain_text('must not be summed')
        self.assertTrue(self.page.locator('#toolbar').is_hidden())
        box = self.page.locator('.landing-rows')
        self.assertLessEqual(box.evaluate('el => el.scrollWidth'), box.evaluate('el => el.clientWidth'))
        self.page.get_by_role('link', name='Established journals only', exact=True).click()
        expect(self.page.get_by_role('link', name='Established journals only', exact=True)).to_have_attribute('aria-pressed', 'true')
        self.assertIn('record=established', self.page.url)
        self.page.locator('details.landing-table > summary').click()
        expect(self.page.locator('details.landing-table tbody tr')).to_have_count(11)
        self.page.screenshot(path=str(self.artifacts / 'landing-desktop.png'), full_page=True)
```

- [ ] **Step 2: Rebuild, start the server, and run the test to verify it fails**

Run:
```bash
python3 scripts/build_site.py
(python3 -m http.server 4173 --bind 127.0.0.1 --directory docs >/dev/null 2>&1 &)
python3 -m unittest tests.test_site_browser.AtlasBrowserTests.test_landing_families_strip_and_record_views -v
```
Expected: FAIL. `.landing-page` is not visible.

- [ ] **Step 3: Load the evidence eagerly**

In `site/app.js`, add this import after the `./people.mjs` import:

```js
import {VIEWS, stripSegments, familyBySlug, familyGraph, rowsSvg, cardsHtml, tableHtml} from './landing.mjs';
```

Update the comment above `let evidence = null;` to say "Loaded with the graph; the landing needs it." In `start()`, add this as the first line inside `try {`:

```js
    const evidenceLoad = fetch('data/evidence.json').then(r => r.ok ? r.json() : null).catch(() => null);
```

Replace:

```js
    state = await routeFor();
    render();
    fetch('data/evidence.json').then(r => r.ok ? r.json() : null).then(d => {
      evidence = d;
      if (d && state?.node) render();
    }).catch(() => {});
```

with:

```js
    evidence = await evidenceLoad;
    state = await routeFor();
    render();
```

- [ ] **Step 4: Add the landing page functions**

In `site/app.js`, add this block immediately above `function fieldPage() {`:

```js
/* ---------------- Landing: families, the atlas beside the record ---------------- */
let landingWidth = 0;
const AXIS_LABEL = '1880–2024';
const recordView = () => state.record || 'all';
function stripBar(segments, cls, unclaimed = null) {
  const seg = (s, extra = '') => `<span class="seg${extra}" style="flex-basis:${(s.share * 100).toFixed(2)}%" title="${esc(`${s.label}: ${Math.round(s.share * 100)}%`)}">${s.share >= 0.07 ? esc(`${s.short} ${Math.round(s.share * 100)}%`) : ''}</span>`;
  const rest = unclaimed === null ? '' : seg({label: 'General journals no family claims', short: 'general / unclaimed', share: unclaimed}, ' unclaimed');
  return `<div class="strip-bar ${cls}" role="img" aria-label="${esc(segments.map(s => `${s.label} ${Math.round(s.share * 100)}%`).join(', ') + (unclaimed === null ? '' : `, unclaimed ${Math.round(unclaimed * 100)}%`))}">${segments.map(s => seg(s)).join('')}${rest}</div>`;
}
function landingPage() {
  const block = evidence.families, view = recordView(), strip = stripSegments(block, graph);
  const toggles = Object.entries(VIEWS).map(([k, label]) =>
    `<a class="view-link" href="${esc(href({record: k === 'all' ? '' : k}))}" aria-pressed="${k === view}">${esc(label)}</a>`).join('');
  const viewNote = view === 'established'
    ? `Only the ${block.established_journals} journals publishing research in both 1970–74 and 2015–19. Old journals are slow to take up new fields.`
    : view === 'reviews' ? 'Share of all book reviews in H-Net and Reviews in History in each five-year period.'
    : 'Share of all research articles in each five-year period, across every journal in the collection.';
  return `<div class="landing-page">
    <div class="section-heading"><div><p class="eyebrow">01 / THE ATLAS AND THE RECORD · ${AXIS_LABEL}</p>
      <h2>Eleven families of historical writing</h2></div></div>
    <p class="lede"><b class="atlas">Orange</b>: where this atlas dates its schools and fields. <b class="record">Green</b>: each family’s share of what historians published. ◂ marks entries dated before 1880. Choose a family to see its fields.</p>
    <p class="eyebrow">THE GAP IN ONE LINE</p>
    <div class="strip"><span>Share of atlas entries</span>${stripBar(strip.atlas, 'atlas')}
      <span>Share of research, ${strip.period[0]}–${strip.period[1]}</span>${stripBar(strip.record, 'record', strip.unclaimed)}</div>
    <div class="landing-controls"><p class="eyebrow">OVER TIME</p><div class="view-links" role="group" aria-label="Record view">${toggles}</div></div>
    <p class="fine-print">${esc(viewNote)} ${esc(block.note)}</p>
    <div class="landing-rows" aria-busy="true"></div>
    ${cardsHtml({block, graph, view, href: id => href({family: id})})}
    <details class="landing-table"><summary>Table of these numbers</summary>${tableHtml({block, graph, view})}</details>
    <p class="fine-print">Atlas entries are placed at the first year in their date label, an editorial reading rather than verified chronology. Record counts use journal-level tags, and research articles are records of at least ten pages. ${esc(evidence.caveats.join(' '))}
      <a href="${esc(href({family: 'all'}))}">All entries on one axis →</a></p>
  </div>`;
}
function drawLanding() {
  const box = document.querySelector('.landing-rows');
  if (!box) return;
  landingWidth = box.clientWidth || 1000;
  box.innerHTML = rowsSvg({block: evidence.families, graph, view: recordView(), width: landingWidth});
  box.removeAttribute('aria-busy');
  const open = row => { if (row) location.hash = href({family: row.dataset.family}); };
  const svg = box.querySelector('svg');
  svg.addEventListener('click', e => open(e.target.closest('.family-row')));
  svg.addEventListener('keydown', e => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    open(e.target.closest('.family-row'));
  });
}
```

In `onResize`, add this inside the `setTimeout` callback, after the field redraw:

```js
    const rows = document.querySelector('.landing-rows');
    if (rows && Math.abs(rows.clientWidth - landingWidth) > 4) drawLanding();
```

- [ ] **Step 5: Dispatch the landing in `render()`**

In `render()`, replace:

```js
  const onField = state.tab === 'map' && !state.node && !state.person;
```

with the following, and move it to the top of `render()` (after `rangeControls();`):

```js
  const onField = state.tab === 'map' && !state.node && !state.person;
  /* Without the evidence asset the front door falls back to the full field view. */
  const onLanding = onField && state.overview && Boolean(evidence?.families);
```

Change the toolbar line to:

```js
  $('toolbar').hidden = !['map','people','browse'].includes(state.tab) || Boolean(state.node || state.person) || onLanding;
```

In the workspace chain, change `: onField ? fieldPage()` to `: onLanding ? landingPage() : onField ? fieldPage()`. Change `if (onField) wireField();` to `if (onLanding) drawLanding(); else if (onField) wireField();`.

In the announcement expression, change its first branch to:

```js
  $('announcement').textContent = onLanding ? 'Eleven families of historical writing: the atlas beside the record.'
    : state.tab === 'map' && !state.node && !state.person
```

The rest of the expression stays unchanged.

- [ ] **Step 6: Styles**

Append to `site/styles.css`:

```css
/* ---------------- Landing: families, the atlas beside the record ---------------- */
:root{--atlas:#a8572f;--record:var(--green);--unclaimed:#c9cdc2}
.landing-page .lede{max-width:860px;color:#536259;font-size:15px;line-height:1.7}
.landing-page .lede b.atlas{color:var(--atlas)}.landing-page .lede b.record{color:var(--record)}
.strip{border:1px solid var(--line);border-radius:7px;background:#fbfaf4;padding:14px 16px;display:grid;grid-template-columns:minmax(140px,230px) minmax(0,1fr);gap:8px 14px;align-items:center;font-size:12px;margin-bottom:8px}
.strip>span{text-align:right}
.strip-bar{display:flex;height:24px;border-radius:3px;overflow:hidden;min-width:0}
.strip-bar .seg{display:flex;align-items:center;padding:0 6px;color:#fff;font-size:11px;white-space:nowrap;overflow:hidden;border-right:1px solid #fbfaf4;min-width:0}
.strip-bar.atlas .seg{background:var(--atlas)}.strip-bar.record .seg{background:var(--record)}
.strip-bar .seg.unclaimed{background:var(--unclaimed);color:var(--ink)}
.landing-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:26px 0 4px}
.landing-controls .eyebrow{margin:0}.view-links{display:flex;gap:6px;flex-wrap:wrap}
.landing-rows{border:1px solid var(--line);border-radius:7px;background:#fbfaf4;overflow-x:auto;margin-top:8px}
.landing-svg{display:block}
.landing-svg .grid{stroke:#e6e7dd}.landing-svg .tick{font-size:10px;fill:var(--muted)}.landing-svg .row-base{stroke:#cfd4c6}
.landing-svg .coverage-line{stroke:#8a938b;stroke-dasharray:3 3}.landing-svg .coverage-label{font-size:10px;fill:var(--muted)}
.landing-svg .atlas-dot{fill:var(--atlas)}.landing-svg .record-bar{fill:var(--record)}
.landing-svg .early-mark{fill:var(--atlas);font-size:13px;text-anchor:end}
.landing-svg .family-label{font:14px var(--serif);fill:var(--ink)}
.landing-svg .row-hit{fill:transparent}.family-row{cursor:pointer;outline:none}
.family-row:hover .row-hit,.family-row:focus-visible .row-hit{fill:#eef0e5}
.family-row:focus-visible .row-hit{stroke:#a8572f;stroke-width:2}
.family-row:focus-visible .family-label{text-decoration:underline}
.family-cards{display:none;list-style:none;padding:0;margin:8px 0 0;gap:10px}
.family-card{display:block;text-decoration:none;border:1px solid var(--line);border-radius:6px;background:#fbfaf4;padding:14px}
.family-card h3{font-size:19px;margin:0 0 6px}.family-card p{font-size:12px;margin:4px 0}
.card-bars{width:100%;height:36px;display:block}.card-bars rect{fill:var(--record)}
.landing-table{margin-top:14px;font-size:12px}.table-scroll{overflow-x:auto}
.landing-table table{border-collapse:collapse;font-size:11px;margin-top:8px}
.landing-table th,.landing-table td{padding:4px 7px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.landing-table th:first-child{text-align:left}
@media(max-width:700px){.landing-rows{display:none}.family-cards{display:grid}.strip{grid-template-columns:1fr}.strip>span{text-align:left}.landing-controls{flex-direction:column;align-items:flex-start}}
```

- [ ] **Step 7: Deck copy**

In `site/index.html`, replace the `.deck` paragraph's first sentence, "See the whole field on one time axis, hold an entry to read its arguments, then follow the disagreements.", with "Start with eleven families of historical writing, set beside what historians actually published; open one to see its fields on a time axis, then follow the disagreements."

- [ ] **Step 8: Rebuild and run the landing test**

Run:
```bash
python3 scripts/build_site.py
python3 -m unittest tests.test_site_browser.AtlasBrowserTests.test_landing_families_strip_and_record_views -v
```
Expected: PASS. Open `site/test-results/landing-desktop.png` and check it against `data/evidence-layer/sketches/recommended-landing.png`:
- labels not clipped
- the coverage label clear of the first row
- the strip readable

- [ ] **Step 9: Commit** (Task 7 updates the old front-door tests, so the whole browser suite runs there)

```bash
git add site/app.js site/styles.css site/index.html tests/test_site_browser.py docs/
git commit -m "Landing: eleven families with headline strip, paired atlas/record rows, record views and table"
```

---

### Task 7: Family drill-down and front-door test updates

**Files:**
- Modify: `site/app.js`
- Modify tests: `tests/test_site_browser.py`, `tests/test_site_extension.py`, `tests/test_digital_release_browser.py`
- Rebuild: `docs/`

**Interfaces:**
- Consumes: `familyBySlug` and `familyGraph`, plus `state.family`.
- Produces:
  - The field page under `#family=<slug>`, headed by the family label, with `.family-crumbs` holding the links "← All families" and "All entries on one axis"
  - `#family=all`, which is today's full field view

- [ ] **Step 1: Write the failing tests and move the old front-door tests**

In `tests/test_site_browser.py`:
- In `test_overview_search_filters_keyboard_and_reset`, the reset now lands on the families overview. Change `expect(self.page.locator('.field-page')).to_be_visible()` to `expect(self.page.locator('.landing-page')).to_be_visible()`.
- In `test_pathways_and_direct_links`, change the last line, `expect(self.page.locator('.field-page')).to_be_visible()`, to `expect(self.page.locator('.landing-page')).to_be_visible()`.
- In `test_field_view_focus_list_and_filters`, change the first `self.open()` to `self.open('#family=all')`.
- `test_hero_compacts_off_the_field` keeps `self.open()`: the landing is still the uncompacted front door.

Add these tests:

```python
    def test_family_drilldown_filters_the_field(self):
        self.open()
        self.page.locator('.family-row[data-family="annales"]').focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.field-page .section-heading h2')).to_have_text('Annales')
        self.assertIn('family=annales', self.page.url)
        expect(self.page.locator('svg.field .entry[data-id="annales"]')).to_have_count(1)
        expect(self.page.locator('svg.field .entry[data-id="military"]')).to_have_count(0)
        self.open('#family=social-history')
        expect(self.page.locator('.family-note')).to_contain_text('Cultural & intellectual history')   # bridges named
        expect(self.page.locator('svg.field .entry[data-id="women"]')).to_have_count(1)
        self.page.get_by_role('link', name='← All families').click()
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.open('#family=all')
        expect(self.page.locator('svg.field .entry[data-id="military"]')).to_have_count(1)
        self.open('#family=nosuch')
        expect(self.page.locator('.field-page')).to_be_visible()   # unknown family: the full field, not an error

    def test_landing_cards_on_mobile(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open()
        expect(self.page.locator('.family-cards li')).to_have_count(11)
        self.assertTrue(self.page.locator('.landing-rows').is_hidden())
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.locator('.family-card').filter(has_text='Environment').click()
        self.assertIn('family=environment', self.page.url)
        self.page.screenshot(path=str(self.artifacts / 'landing-mobile.png'), full_page=True)
```

In `tests/test_site_extension.py`, the extension marks live on the full field. Change `self.open('')` (line 81) to `self.open('#family=all')`. Make the same change to the `open()` locator list there if it lacks `.landing-page`.

In `tests/test_digital_release_browser.py`, change `self.open()` in `test_new_entries_and_exact_baseline` to `self.open('#family=all')`. If its `open()` locator waits only for field markup, add `.landing-page` to it.

- [ ] **Step 2: Rebuild and run to verify the new tests fail**

Run:
```bash
python3 scripts/build_site.py
python3 -m unittest tests.test_site_browser.AtlasBrowserTests.test_family_drilldown_filters_the_field -v
```
Expected: FAIL. The heading reads "Historiography on one time axis", not "Annales".

- [ ] **Step 3: Filter the field to the family**

In `site/app.js`, add this after `const activePathway = ...`:

```js
/* One editorial family's fields ('all' or an unknown slug shows everything). */
const activeFamily = () => state.family && state.family !== 'all' ? familyBySlug(evidence?.families, state.family) : null;
let shownMemo = {};
function shownGraph() {
  const f = activeFamily();
  if (!f) return graph;
  if (shownMemo.id !== f.id || shownMemo.base !== graph) shownMemo = {id: f.id, base: graph, g: familyGraph(graph, f)};
  return shownMemo.g;
}
```

Change `fieldView` to lay out the shown graph:

```js
function fieldView(width) {
  return buildFieldLayout(shownGraph(), width, fieldFocusSet(), fieldLayers(shownGraph(), FIELD_TITLES),
    {numbering: state.focus ? null : pathNumbering(), extension: activeExtension()});
}
```

In `activeFieldEdges`, change the return so it draws only relationships among the shown entries:

```js
  const shown = new Set(fieldNodes(shownGraph()).map(n => n.id));
  return edges.filter(e => !hidden.has(e.relationship_kind) && shown.has(e.source) && shown.has(e.target));
```

In `fieldList`, change `fieldNodes(graph)` to `fieldNodes(shownGraph())`.

- [ ] **Step 4: The family heading**

Add this above `function fieldPage()`:

```js
function familyHeading(f) {
  const bridged = f.members.filter(m => !m.primary).map(m => nodeById.get(m.id)?.label).filter(Boolean);
  const primaryOf = id => evidence.families.families.find(x => x.members.some(m => m.id === id && m.primary))?.label;
  const shared = f.members.filter(m => m.primary && evidence.families.families.some(x => x.id !== f.id && x.members.some(y => y.id === m.id)))
    .map(m => nodeById.get(m.id)?.label).filter(Boolean);
  const bridgeFamilies = [...new Set(f.members.filter(m => !m.primary).map(m => primaryOf(m.id)).filter(Boolean))];
  const lacks = f.record_only.map(x => x.label);
  return `<nav class="family-crumbs" aria-label="Families"><a href="${esc(href({family: '', focus: '', path: ''}))}">← All families</a>
      <a href="${esc(href({family: 'all', focus: '', path: ''}))}">All entries on one axis</a></nav>
    <p class="family-note">${shared.length ? `Shared with other families: ${esc(shared.join(', '))}. ` : ''}${bridged.length ? `Also drawn here from ${esc(bridgeFamilies.join(', '))}: ${esc(bridged.join(', '))}. ` : ''}${lacks.length ? `In the record but not in the atlas: ${esc(lacks.join(', '))}.` : ''}</p>`;
}
```

In `fieldPage()`:
- Add `const fam = activeFamily();` as the first line.
- Replace the opening of the returned template up to `</p></div>` with the version below. It keeps the counts, reads the shown graph, and adds the family heading.

```js
  return `<div class="field-page">
    ${fam ? familyHeading(fam) : ''}
    <div class="section-heading"><div><p class="eyebrow">${fam ? '01 / ONE FAMILY OF HISTORICAL WRITING' : '01 / THE WHOLE FIELD'}</p>
      <h2>${fam ? esc(fam.label) : 'Historiography on one time axis'}</h2></div>
      <p class="field-summary">${counts.datedCount} placed in time${counts.undatedCount
        ? ` · ${counts.undatedCount} without a stated span` : ''} ·
        ${fieldEdges(shownGraph()).length} relationships${activeExtension() ? ` · ${activeExtension().covered} entries with selected interventions after ${graph.scope.main_period[1]}` : ''}</p></div>
```

The rest of `fieldPage()` stays unchanged. Then add this style to `site/styles.css`:

```css
.family-crumbs{display:flex;gap:18px;font-size:12px;margin-top:22px}.family-note{font-size:12px;color:var(--muted);max-width:900px;margin:8px 0 0}
```

- [ ] **Step 5: Rebuild and run the whole browser and view suites**

Run:
```bash
python3 scripts/build_site.py
node tests/test_site_core.mjs
python3 -m unittest tests.test_site_browser tests.test_site_extension tests.test_digital_release_browser tests.test_evidence_asset tests.test_practice_families -v
```
Expected: all pass, with no page errors (each browser test's `tearDown` asserts that). Check `site/test-results/landing-mobile.png`.

- [ ] **Step 6: Commit**

```bash
git add site/app.js site/styles.css tests/test_site_browser.py tests/test_site_extension.py tests/test_digital_release_browser.py docs/
git commit -m "Landing: family drill-down filters the field; full field at #family=all; front-door tests follow"
```

---

### Task 8: Amendments, docs, full verification, handoff

**Files:**
- Modify:
  - `data/production-batches/extension-1.123/acceptance.json`
  - `site/README.md`
  - `data/evidence-layer/README.md`
  - `EVIDENCE-LAYER-PLAN.md`
  - `specs/2026-09-27-landing-redesign-design.md` (status line)

- [ ] **Step 1: Log revision 1.123 amendments**

Log every pinned file this redesign changed, as the evidence-panel commit 3cf2bde did. The accepted hash is the file as of `a1cc112` (the commit before this work). It is null for new files.

Run:
```bash
python3 - <<'EOF'
import hashlib, json, subprocess, datetime
p = 'data/production-batches/extension-1.123/acceptance.json'
rec = json.load(open(p))
base = 'a1cc112'
why = {
 'site/app.js': 'Landing page of eleven editorial families (headline strip, paired atlas/record rows, record views, table, mobile cards); field view filtered by family; evidence asset loaded with the graph.',
 'site/core.mjs': 'Route keys family, record and the derived overview flag; routeHash never writes overview.',
 'site/landing.mjs': 'New pure module: landing strip, rows, cards and table builders; family subgraph.',
 'site/styles.css': 'Landing and family-heading styles.',
 'site/index.html': 'Deck copy introduces the families landing.',
 'scripts/build_site.py': 'Publishes site/landing.mjs.',
 'docs/app.js': 'Rebuilt from site/app.js.', 'docs/core.mjs': 'Rebuilt from site/core.mjs.',
 'docs/landing.mjs': 'Rebuilt from site/landing.mjs.', 'docs/styles.css': 'Rebuilt from site/styles.css.',
 'docs/index.html': 'Rebuilt from site/index.html.',
 'docs/data/evidence.json': 'Rebuilt: evidence asset adds the families block (series v17).',
 'tests/test_site_extension.py': 'Extension marks are checked on the full field (#family=all); the bare URL is now the families landing.',
 'tests/test_digital_release_browser.py': 'Digital-release entries are checked on the full field (#family=all).',
}
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
for f, reason in why.items():
    try: old = sha_bytes(subprocess.check_output(['git', 'show', f'{base}:{f}'], stderr=subprocess.DEVNULL))
    except subprocess.CalledProcessError: old = None
    new = sha_bytes(open(f, 'rb').read())
    if old == new: continue
    rec['amendments'].append({'file': f, 'accepted_sha256': old, 'amended_sha256': new,
        'date': datetime.date.today().isoformat(), 'reason': reason,
        'scope': 'Landing redesign (specs/2026-09-27-landing-redesign-design.md); curated graph and claims unchanged.'})
json.dump(rec, open(p, 'w'), indent=1, ensure_ascii=False); open(p, 'a').write('\n')
print(len(rec['amendments']))
EOF
git diff --stat data/production-batches/extension-1.123/acceptance.json
```
Expected: the amendment count rises by roughly 12–14. Check that the file's existing formatting (indent 1, trailing newline) matches `git show a1cc112:data/production-batches/extension-1.123/acceptance.json | head -3`. If the file used a different indent, rerun with that indent so the diff shows only appended entries.

- [ ] **Step 2: Docs**

- **`site/README.md`**: add a "Landing" section covering:
  - Routes: the bare URL gives the families overview; `#family=<slug>` gives one family's field; `#family=all` gives the full field; `#record=established|reviews` switches the record view.
  - Data: the view reads `docs/data/evidence.json` → `families`.
  - Fallback: without the asset, the page falls back to the full field.
- **`data/evidence-layer/README.md`**: add the families stage:
  - `families-draft.csv` columns
  - `scripts/practice_families.py` counting rules (quote its docstring)
  - `generated/v17/family_series.csv`
  - rebuilding with `build_practice_series.py --version vNN` followed by `build_evidence_asset.py --series vNN ...` and `build_site.py`
- **`EVIDENCE-LAYER-PLAN.md`**: add a dated line under component 1: "2026-09-27: landing redesign pairs the atlas with family-level record shares (spec and plan in specs/ and plans/)".
- **Spec**: change the status line to "approved and implemented 2026-09-27 (unpushed)".

- [ ] **Step 3: Full verification**

Run:
```bash
python3 scripts/validate_graph.py
python3 -m unittest tests.test_graph_validation tests.test_people_validation tests.test_evidence_asset tests.test_practice_families
node tests/test_site_core.mjs
python3 scripts/build_site.py && git status --short docs
python3 -m unittest tests.test_site_browser tests.test_site_extension tests.test_digital_release_browser -v
```
Expected:
- everything passes
- `docs/` is clean after the rebuild, so CI's stale check would pass

Report failures verbatim. Do not claim success without this output.

- [ ] **Step 4: Commit**

```bash
git add data/production-batches/extension-1.123/acceptance.json site/README.md data/evidence-layer/README.md EVIDENCE-LAYER-PLAN.md specs/2026-09-27-landing-redesign-design.md
git commit -m "Landing redesign: revision 1.123 amendments and docs"
```

- [ ] **Step 5: Hand off. Do not push.**

Send the user `site/test-results/landing-desktop.png` and `landing-mobile.png`. Report:
- the unpushed commit count
- the two proposed placements (`freud`, `revival`) awaiting their call
- the two record-only members with no crosswalk rows (`none:history_of_knowledge`, `none:transnational_history`)
- the actual established-journal count and unclaimed share
