# Open Frame Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use usask-foundation:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** End the atlas's 1920–2000 coverage cutoff. Post-2000 work becomes ordinary content; each field shows how far it has been reviewed; the exact-2000 view survives only as an archive; the title drops its dates.

**Architecture:** Revision 1.132 is a data transform (`scripts/apply_open_frame.py`, in the same build/apply/check pattern as the other appliers). It replaces prose coverage limits with a structured per-entry `coverage.reviewed_through`, makes spans open and moves the 2000-view pointers into `scope.archive`. The site then draws each mark solid to its reviewed year and faded beyond it, up to the research cutoff, instead of stopping at a wall. The archived 1.121 graph keeps rendering exactly as before, through the old code paths, because it still carries the legacy labels.

**Tech Stack:** Python 3 (data scripts, unittest, Playwright browser tests); dependency-free ES modules (site/); Node test runner (`node tests/test_site_core.mjs`).

## Global Constraints

- User decisions (2026-10-14):
  - "we need to end the 2000 break in this project";
  - "switch now, build field by field" with a visible per-field "reviewed through" marker;
  - keep the exact-2000 view (revision 1.121) "as an archive", reachable from Reading this map, with no main-view toggle;
  - the title is "drop the dates": **The Historiography Atlas**.
- Revision numbering:
  - the Chakrabarty person entry (high priority, draft ready) is **1.132**;
  - the open frame is revision **1.133** on baseline 1.132;
  - the science-studies critique batch is **1.134**.
  - Every "1.132" below that refers to the open-frame revision means **1.133**. The applier
    constants are already updated: REV '1.133', baseline v1.132, open-frame-1.133.
- Keep the data file name `historiography-1920-2000.json`. `build_site.load_baseline` recovers archives from git history under that literal, so do not rename it in this plan.
- The archive must still render exactly: `#range=2000` loads `data/graph-2000.json` (revision 1.121, sha256 `5fe82ffc101f1bef12e36a99f565eba40c0627eda5cde5397c86309d110935a9`), whose labels still say "coverage through 2000". Every site change must keep that path working.
- Historical appliers and acceptance scripts (`apply_*`, `accept_*`, `build_*_candidate`) reconstruct old revisions and stay unchanged. Only forward-facing tools change.
- No date_label may contain "coverage through 2000" or "baseline through 2000" after 1.132.
- Wording: say "reviewed through 2000", never "ends in 2000". A year of review is a limit of our reading, not an ending of the field.
- CI must stay green:
  - `python3 scripts/validate_graph.py`;
  - the data tests listed in `.github/workflows/pages.yml`;
  - `node tests/test_site_core.mjs`;
  - `python3 scripts/build_site.py`;
  - `python3 tests/run_site_checks.py`, with a server on port 4173 started by `python3 -m http.server 4173 --bind 127.0.0.1 --directory docs`;
  - `git diff --exit-code docs`, after building.

---

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `scripts/apply_open_frame.py` | Pure `transform(graph) -> graph` plus build/apply/check CLI | Create |
| `data/production-batches/open-frame-1.133/` | `acceptance.json`, `README.md` | Create (by `apply`) |
| `tests/test_open_frame.py` | Unit tests of the transform on the live graph | Create |
| `historiography-1920-2000.json` | Graph data | Modified by the applier only |
| `seminar-pathways.json` | One question reworded | Modify |
| `scripts/build_site.py` | Read the archive pointers from `scope.archive` (fallback `scope.extension`) | Modify `load_baseline` and `build` |
| `scripts/journal_venue_batches.py` | Year bound 2000 → research-cutoff year | Modify L38, L62 |
| `site/field.mjs` | `frameOf()`, open spans, reviewed-through segments | Modify |
| `site/app.js` | Archive banner and link; texts; remove the toggle; new field SVG legend | Modify |
| `site/landing.mjs` | Remove the hard-coded `AXIS.coverage` line | Modify |
| `site/index.html`, `site/styles.css` | Meta, eyebrow, new `.unreviewed` and `.archive-banner` styles | Modify |
| `tests/test_site_core.mjs`, `tests/test_site_browser.py`, `tests/test_indigenous_browser.py`, `tests/test_evidence_asset.py` | Assertions moved from the wall to reviewed-through | Modify |
| `GRAPH-FORMAT.md`, `README.md`, `site/README.md`, `DEVELOPMENT.md`, `REVISION-NOTES.md` | Policy and counts | Modify |
| `data/production-batches/extension-1.123/acceptance.json` | `amendments` for pinned files changed here | Modify |

---

### Task 1: The data transform (revision 1.132)

**Files:**
- Create: `scripts/apply_open_frame.py`
- Create: `tests/test_open_frame.py`
- Modify (by running the script): `historiography-1920-2000.json`, `seminar-pathways.json`

**Interfaces:**
- Produces, for later tasks:
  - `scope.frame = {"start": 1920, "end": null, "research_cutoff": "2026-10-14"}`.
  - `scope.archive = {"label": "The original 1920–2000 experiment", "baseline_period": [1920, 2000], "baseline_graph": "drafts/historiography-1920-2000.v1.121.json", "baseline_revision": "1.121", "baseline_sha256": "5fe82ffc…a9"}`. Task 2 adds `baseline_asset` at build time.
  - `scope.main_period = [1920, null]`.
  - `scope.extension` is removed. Its history stays in `revision_history` and the acceptance records.
  - Every group node gets `coverage = {"reviewed_through": 2000, "basis": "<text>"}`. The five nodes with `extension_coverage` keep it unchanged, as selected later interventions.
  - Any curated `date_span` with `end_kind: "coverage_limit"` becomes `end: null, end_kind: "open"`. Its basis gains a sentence.
  - Journal `principal_venue` edges whose `temporal_scope.end == 2000` and whose note names the coverage boundary become `end: null`.
  - `revision_history` gains `{"version": "1.132", ...}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_open_frame.py
import json, re, unittest
from pathlib import Path
from scripts import apply_open_frame as m

ROOT = Path(__file__).resolve().parents[1]

class OpenFrame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.after = json.loads((ROOT / 'historiography-1920-2000.json').read_text())

    def test_title_and_frame(self):
        self.assertEqual(self.after['title'], 'The Historiography Atlas')
        self.assertEqual(self.after['schema_version'], '1.5')
        self.assertEqual(self.after['scope']['main_period'], [1920, None])
        self.assertEqual(self.after['scope']['frame']['start'], 1920)
        self.assertIsNone(self.after['scope']['frame']['end'])
        self.assertNotIn('extension', self.after['scope'])

    def test_archive_pointer_is_the_exact_1121_view(self):
        a = self.after['scope']['archive']
        self.assertEqual(a['baseline_revision'], '1.121')
        self.assertEqual(a['baseline_sha256'], m.ARCHIVE_SHA)
        self.assertEqual(a['baseline_period'], [1920, 2000])

    def test_no_prose_coverage_limits(self):
        bad = [n['id'] for n in self.after['nodes'] if re.search(r'(coverage|baseline) through 2000', n['date_label'])]
        self.assertEqual(bad, [])

    def test_every_group_has_reviewed_through(self):
        for n in self.after['nodes']:
            if n['entry_kind'] == 'group':
                self.assertIsInstance(n.get('coverage', {}).get('reviewed_through'), int, n['id'])

    def test_spans_are_open(self):
        for n in self.after['nodes']:
            d = n.get('date_span')
            if d:
                self.assertNotEqual(d.get('end_kind'), 'coverage_limit', n['id'])

    def test_selected_interventions_kept(self):
        ids = sorted(n['id'] for n in self.after['nodes'] if n.get('extension_coverage'))
        self.assertEqual(ids, ['digital_history', 'indigenous', 'medicalhistory', 'spatialhistory', 'web_history'])

    def test_reconstructs_exactly(self):
        m.Batch().check()   # raises on mismatch

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3 -m unittest tests.test_open_frame -v`
Expected: ERROR, `ModuleNotFoundError: No module named 'scripts.apply_open_frame'`.

- [ ] **Step 3: Write the transform**

```python
# scripts/apply_open_frame.py
"""Revision 1.132: end the 1920–2000 coverage cutoff (user, 2026-10-14).

    python3 scripts/apply_open_frame.py          # apply to the 1.131 graph
    python3 scripts/apply_open_frame.py --check  # rebuild 1.132 exactly from its baseline
"""
import argparse, hashlib, json, re, sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

GRAPH = ROOT / 'historiography-1920-2000.json'
PATHWAYS = ROOT / 'seminar-pathways.json'
OUT = ROOT / 'data/production-batches/open-frame-1.133'
BASE = ROOT / 'drafts/historiography-1920-2000.v1.132.json'
REV, DAY, CUTOFF = '1.133', '2026-10-14', '2026-10-14'
ARCHIVE_SHA = '5fe82ffc101f1bef12e36a99f565eba40c0627eda5cde5397c86309d110935a9'
LIMIT = re.compile(r'\s*·?\s*(?:coverage|baseline) through 2000\b')
AUTH = ("User, 2026-10-14: 'we need to end the 2000 break in this project'; the 2000 frame "
        "'comes from the original experiment where I scoped it to 2000, but we're building it out now'; "
        "decisions: switch now and build field by field; keep the exact-2000 view as an archive; drop the dates.")
REVIEW_BASIS = ('Reviewed through 2000 in the original 1920–2000 experiment. Later work is not yet '
                'surveyed for this entry; selected later interventions, where present, are dated individually.')
OLD_Q = "Which parts of Hunt's argument would require extending this map beyond its current 2000 endpoint?"
NEW_Q = ("Which parts of Hunt's argument depend on work after 2000, and which entries on this "
         "pathway are still reviewed only through 2000?")


def read(p): return json.loads(Path(p).read_text())
def serial(v): return json.dumps(v, ensure_ascii=False, indent=2) + '\n'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clean_label(label):
    out = LIMIT.sub('', label).strip(' ·')
    return out or label


def transform(before):
    if before['revision_history'][-1]['version'] != '1.132':
        raise ValueError('Expected revision 1.132')
    g = deepcopy(before)
    g['title'] = 'The Historiography Atlas'
    g['schema_version'] = '1.5'
    ext = g['scope'].pop('extension')
    if ext['baseline_sha256'] != ARCHIVE_SHA:
        raise ValueError('Archive pointer is not the exact 1.121 view')
    g['scope']['main_period'] = [1920, None]
    g['scope']['frame'] = dict(start=1920, end=None, research_cutoff=CUTOFF,
        note='Open frame from revision 1.132. Each entry records how far it has been reviewed '
             '(coverage.reviewed_through); a review year is a limit of our reading, not an ending.')
    g['scope']['archive'] = dict(label='The original 1920–2000 experiment', baseline_period=[1920, 2000],
        baseline_graph=ext['baseline_graph'], baseline_revision=ext['baseline_revision'],
        baseline_sha256=ext['baseline_sha256'], acceptance_records=ext.get('acceptance_records', []))
    notes = g['scope']['notes']
    notes[:] = [n for n in notes if not n.startswith('Sources published after 2000 can retrospectively')]
    notes.append('From revision 1.132 the atlas has no closing date. Fields are extended one at a time; '
                 'each entry states the year through which it has been reviewed. The original 1920–2000 '
                 'experiment (revision 1.121) is kept as an archived view.')
    for n in g['nodes']:
        n['date_label'] = clean_label(n['date_label'])
        if n['entry_kind'] == 'group':
            n['coverage'] = dict(reviewed_through=2000, basis=REVIEW_BASIS)
        d = n.get('date_span')
        if d and d.get('end_kind') == 'coverage_limit':
            d['end'], d['end_kind'] = None, 'open'
            d.pop('coverage_through', None)
            d['basis'] = (d.get('basis', '') + ' Open from revision 1.132: the former 2000 end was the '
                          'atlas boundary, not an ending.').strip()
    for e in g.get('journal_catalogue', {}).get('edges', []):
        ts = e.get('temporal_scope') or {}
        if ts.get('end') == 2000 and 'coverage boundary' in json.dumps(e):
            ts['end'] = None
            ts['note'] = (ts.get('note', '') + ' Open from revision 1.132: 2000 was the atlas boundary.').strip()
    g['revision_history'].append(dict(version=REV, date=DAY,
        acceptance_record=str((OUT / 'acceptance.json').relative_to(ROOT)),
        summary='Open frame: the 1920–2000 cutoff ends. Prose coverage limits become coverage.reviewed_through '
                '(2000 for every group, pending field-by-field review); open spans; the exact-2000 view '
                '(1.121) moves to scope.archive; title "The Historiography Atlas".',
        added_node_ids=[], added_edge_ids=[], revised_edge_ids=[]))
    return g


def pathways_transform(p):
    p = deepcopy(p)
    for path in p['pathways']:
        path['questions'] = [NEW_Q if q == OLD_Q else q for q in path['questions']]
    return p


class Batch:
    def apply(self):
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before = read(GRAPH)
        graph, paths = transform(before), pathways_transform(read(PATHWAYS))
        errors, _ = validate(graph, paths)
        if errors:
            raise ValueError('\n'.join(errors))
        BASE.parent.mkdir(exist_ok=True)
        BASE.write_bytes(GRAPH.read_bytes())
        prior_paths = PATHWAYS.read_bytes()
        GRAPH.write_text(serial(graph))
        PATHWAYS.write_text(serial(paths))
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'acceptance.json').write_text(serial(dict(revision=REV, date=DAY, authorization=AUTH,
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE), production_sha256=sha(GRAPH),
            pathways_before_sha256=hashlib.sha256(prior_paths).hexdigest(), pathways_sha256=sha(PATHWAYS),
            prior_scope=before['scope'], prior_title=before['title'], prior_schema=before['schema_version'],
            prior_labels={n['id']: n['date_label'] for n in before['nodes'] if LIMIT.search(n['date_label'])},
            prior_spans={n['id']: n['date_span'] for n in before['nodes']
                         if n.get('date_span', {}).get('end_kind') == 'coverage_limit'})))
        return graph

    def baseline(self):
        record = read(OUT / 'acceptance.json')
        if BASE.exists():
            return read(BASE)
        from scripts.build_site import load_baseline   # clean checkout: recover 1.131 from git history
        graph, _ = load_baseline(dict(baseline_graph=str(BASE.relative_to(ROOT)),
                                      baseline_sha256=record['baseline_sha256']))
        if graph is None:
            raise ValueError('1.131 baseline unavailable')
        return graph

    def check(self):
        if transform(self.baseline()) != read(GRAPH):
            raise ValueError('Exact 1.132 reconstruction differs')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    b = Batch()
    graph = (b.check() or read(GRAPH)) if ap.parse_args().check else b.apply()
    errors, warnings = validate(graph, read(PATHWAYS))
    print(f'{REV}: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} nodes; {len(graph["edges"])} edges')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Apply, then run the tests and the validator**

Run:
```bash
python3 scripts/apply_open_frame.py
python3 -m unittest tests.test_open_frame -v
python3 scripts/validate_graph.py | tail -2
grep -c "coverage through 2000" historiography-1920-2000.json
```
Expected:
- the applier prints `1.132: 0 errors; 7 warnings; 166 nodes; 913 edges` (counts as of 1.131);
- 7 tests pass;
- the validator ends normally;
- grep prints `2`. Those are the two historical `revision_history` summaries (1.104 and 1.105), which stay as written.

If `validate_journal_catalogue` rejects `temporal_scope.end: null`, read its rule. If null ends are disallowed, extend the rule to accept `null` as "open" (one line, `end is None or isinstance(end, int)`). Add a test for it in `tests/test_open_frame.py`, then rerun.

- [ ] **Step 5: Check the other appliers still reconstruct, then commit**

Run:
```bash
python3 scripts/apply_person_entries.py data/extension-2026/environment-family-2026-10-13 --check
python3 scripts/apply_open_frame.py --check
python3 -m unittest tests.test_graph_validation tests.test_people_validation tests.test_evidence_asset tests.test_practice_families tests.test_student_beta tests.test_indigenous_deep_dive tests.test_indigenous_foundations tests.test_borderlands_release_candidate tests.test_evidence_coverage_audit tests.test_publication_repairs tests.test_open_frame
```
Expected: both checks print counts; all tests OK. Do not commit yet. Task 2 must build first, because CI checks `docs/` against the sources. Stash nothing; continue to Task 2.

### Task 2: Build pipeline reads `scope.archive`

**Files:**
- Modify: `scripts/build_site.py` (`load_baseline` callers in `build()`, about L180–207 and L224–229)
- Modify: `scripts/journal_venue_batches.py` L38, L62
- Test: `tests/test_open_frame.py` (add one test)

**Interfaces:**
- Consumes `scope.archive` from Task 1.
- Produces:
  - published `docs/data/graph.json` with `scope.archive.baseline_asset = "data/graph-2000.json"`;
  - `docs/data/graph-2000.json`, byte-identical to before;
  - `docs/data/overview.json` with `scope.archive.baseline_asset`.

- [ ] **Step 1: Write the failing test**

```python
    def test_build_publishes_archive_asset(self):
        import subprocess
        subprocess.run([sys.executable, 'scripts/build_site.py'], cwd=ROOT, check=True, capture_output=True)
        pub = json.loads((ROOT / 'docs/data/graph.json').read_text())
        self.assertEqual(pub['scope']['archive']['baseline_asset'], 'data/graph-2000.json')
        arch = ROOT / 'docs/data/graph-2000.json'
        self.assertEqual(hashlib.sha256(arch.read_bytes()).hexdigest() != '', True)
        self.assertEqual(json.loads(arch.read_text())['revision_history'][-1]['version'], '1.121')
```
Also add `import hashlib, sys` at the top of the test file.

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m unittest tests.test_open_frame.OpenFrame.test_build_publishes_archive_asset -v`
Expected: FAIL, `KeyError: 'archive'`. The builder still looks for `scope.extension`.

- [ ] **Step 3: Implement**

In `scripts/build_site.py`, wherever `build()` reads `graph['scope'].get('extension')` to find the baseline (about L180), replace it with:

```python
    archive = graph['scope'].get('archive') or graph['scope'].get('extension')
```

Use `archive` for `load_baseline(archive, override)`. Where the builder injects `baseline_asset` (about L197–198), write it into the same object it read:

```python
    key = 'archive' if 'archive' in published['scope'] else 'extension'
    published['scope'][key]['baseline_asset'] = BASELINE_ASSET
```

Make the same `archive`/`extension` choice for `overview.json` (about L224–229). Leave the literal `historiography-1920-2000.json` in `load_baseline` (L132, L137) alone.

In `scripts/journal_venue_batches.py`, replace the two `2000` bounds:

```python
CUTOFF_YEAR = 2026   # open frame (revision 1.132): founding and venue years run to the research cutoff
...
if not 1 <= year <= CUTOFF_YEAR:          # was 2000 (L38)
...
if year > CUTOFF_YEAR:                    # was 2000 (L62)
```

- [ ] **Step 4: Run the tests and the build**

Run:
```bash
python3 -m unittest tests.test_open_frame -v
python3 scripts/build_site.py | tail -3
```
Expected: 8 tests pass. The build says `Built 15 allowlisted files in docs/`.

- [ ] **Step 5: Commit the data, builder and build together**

```bash
git add scripts/apply_open_frame.py tests/test_open_frame.py historiography-1920-2000.json seminar-pathways.json \
  data/production-batches/open-frame-1.133 scripts/build_site.py scripts/journal_venue_batches.py docs/data
git commit -m "Revision 1.132 (data): open frame — reviewed_through replaces the 2000 cutoff; exact-2000 view archived"
```
Note: the browser tests are expected to fail until Tasks 3–5. CI is pushed only after Task 6.

### Task 3: `field.mjs` draws reviewed-through instead of a wall

**Files:**
- Modify: `site/field.mjs` (header comment L7–11; `spanOf` L80–96; `journalNodes` L120; `extensionOf` L218–231; `buildFieldLayout` L245–340)
- Test: `tests/test_site_core.mjs`

**Interfaces:**
- Consumes: `scope.frame`, `scope.archive`, node `coverage.reviewed_through`, `date_span.end_kind 'open'`.
- Produces:
  - `export function frameOf(graph) -> {open: boolean, start: number, end: number, cutoff: number|null, wall: number|null}`.
    - Open graphs: `wall: null`, and `end = ceil(year of research_cutoff)`.
    - Legacy graphs (main_period[1] is a number, e.g. the 1.121 archive): `open: false`, `wall: main_period[1]`.
  - Each layout bar gains `reviewed: number|null` (x-ready via `view.scale`) and `fadeTo: number`, the year the faded tail ends.
  - `buildFieldLayout(...)` returns `view.frame = frameOf(graph)`. `view.coverageYear` stays for legacy graphs and is `null` for open ones.
  - `extensionOf(graph)` returns `null` for open graphs. Interventions still come from `interventionsOf(node)`, now drawn whenever `yr > reviewed`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_site_core.mjs`, following the file's existing `test(...)` style)

```js
test('open frame: frameOf reads scope.frame; legacy graphs keep their wall', () => {
  const open = {scope: {main_period: [1920, null], frame: {start: 1920, end: null, research_cutoff: '2026-10-14'}}, nodes: []};
  assert.deepEqual(frameOf(open), {open: true, start: 1920, end: 2027, cutoff: 2026 + 9.5 / 12, wall: null});
  const legacy = {scope: {main_period: [1920, 2000]}, nodes: []};
  assert.equal(frameOf(legacy).open, false);
  assert.equal(frameOf(legacy).wall, 2000);
});

test('open frame: a group is solid to reviewed_through and fades to the frame end', () => {
  const g = {scope: {main_period: [1920, null], frame: {start: 1920, end: null, research_cutoff: '2026-10-14'}},
    layers: [{id: 'L'}], edges: [], people: [], nodes: [
      {id: 'a', label: 'A', layer: 'L', entry_kind: 'group', date_label: '1970s consolidation',
       coverage: {reviewed_through: 2000}}]};
  const view = buildFieldLayout(g, 1000, null, ['L']);
  const bar = view.bars[0];
  assert.equal(bar.reviewed, 2000);
  assert.equal(bar.fadeTo, 2027);
  assert.ok(view.scale(bar.fadeTo) > view.scale(2000));
  assert.equal(view.coverageYear, null);
});

test('archive graphs still draw to the 2000 wall', () => {
  const g = {scope: {main_period: [1920, 2000]}, layers: [{id: 'L'}], edges: [], people: [], nodes: [
    {id: 'a', label: 'A', layer: 'L', entry_kind: 'group', date_label: '1970s consolidation · coverage through 2000'}]};
  const view = buildFieldLayout(g, 1000, null, ['L']);
  assert.equal(view.coverageYear, 2000);
  assert.equal(view.bars[0].drawEnd, 2000);
});
```
Import `frameOf` alongside the existing imports from `../site/field.mjs`.

- [ ] **Step 2: Run them to see them fail**

Run: `node tests/test_site_core.mjs 2>&1 | grep -E "^not ok|frameOf"`
Expected: failures, "frameOf is not a function".

- [ ] **Step 3: Implement**

Add `frameOf`, and make `extensionOf` return `null` on open graphs:

```js
export function frameOf(graph) {
  const s = graph.scope || {};
  const legacyWall = Number.isFinite(s.main_period?.[1]) ? s.main_period[1] : null;
  if (!s.frame && legacyWall !== null) return {open: false, start: s.main_period[0], end: legacyWall, cutoff: null, wall: legacyWall};
  const d = s.frame?.research_cutoff ? new Date(s.frame.research_cutoff) : new Date();
  const cutoff = d.getUTCFullYear() + (d.getUTCMonth() + 0.5) / 12;
  return {open: true, start: s.frame?.start ?? 1920, end: Math.ceil(cutoff), cutoff, wall: null};
}
export const reviewedThrough = node => node.coverage?.reviewed_through ?? null;
```

At the top of `extensionOf`, add `if (frameOf(graph).open) return null;`.

In `spanOf`, treat `end_kind === 'open'` like a null end:

```js
      endKind: end === null || d.end_kind === 'open' ? 'coverage_limit' : (d.end_kind || 'unstated'),
```

In `journalNodes` L120, change the label to `` `Publication dates unverified · venue role evidenced from ${roleStart}` `` and drop the "coverage through 2000" suffix. Open frames have no wall, and the archive does not draw journals from this code path's labels.

In `buildFieldLayout`:

```js
  const frame = frameOf(graph);
  const maxYear = Math.max(frame.open ? frame.end : (extension ? extension.end : 2000),
    Math.ceil(Math.max(...spans.map(s => s.end)) / 10) * 10);
  const coverageYear = frame.open ? null : frame.wall;
```

In the bar loop, replace the `drawEnd` line with:

```js
      const reviewed = frame.open ? reviewedThrough(item.node) : null;
      const drawEnd = open ? (frame.open ? (reviewed ?? frame.end) : (item.span.coverage ?? coverageYear)) : item.span.end;
      const fadeTo = open && frame.open ? frame.end : drawEnd;
```

Then:
- the posthumous-death limit becomes `life.death <= (coverageYear ?? frame.end)`;
- the interventions filter becomes `.filter(yr => yr > (frame.open ? (reviewed ?? 0) : coverageYear) && yr <= (frame.open ? frame.end : extension?.end ?? 0))`, guarded so it runs when `frame.open || extension`;
- `fadeTo` and `reviewed` are pushed into the bar object, and so is a ghost `ghostEnd` (use `frame.end` for open ghosts);
- the returned view object gains `frame`.

Update the header comment (L7–11) to describe the reviewed-through drawing: "solid to the year through which the entry has been reviewed, then faded to the research cutoff; the archived 2000 view keeps its wall".

- [ ] **Step 4: Run the tests**

Run: `node tests/test_site_core.mjs 2>&1 | grep -E "^# (pass|fail)"`
Expected: `# fail 0`. Existing "coverage through 2000" parse tests still pass, because `parseSpan` is unchanged and those labels exist in the archive.

- [ ] **Step 5: Commit**

```bash
git add site/field.mjs tests/test_site_core.mjs
git commit -m "Field: reviewed-through marks for the open frame; archive keeps its 2000 wall"
```

### Task 4: Site text, the field SVG, the archive banner and the landing

**Files:**
- Modify: `site/app.js`:
  - `activeExtension` L41; `extensionSection` L139–148;
  - `fieldSvg` L464–486 (the wall, plus a new tail and cutoff rendering in the bar markup);
  - legend L422–423; `interventionNote` L584–589; `fieldDateNote` L590–610;
  - `fieldPanel` L691–703; `fieldList` L737–751; landing fine print L809; field header L901;
  - `about()` L1182–1185; `rangeControls()` L1203–1217.
- Modify: `site/landing.mjs` L6, L152–154
- Modify: `site/index.html` L6, L19; `site/styles.css` (add rules)

**Interfaces:**
- Consumes: `frameOf`, `reviewedThrough`, and the bar fields `reviewed`/`fadeTo` from Task 3; `scope.archive.baseline_asset` from Task 2.
- Produces:
  - DOM `.unreviewed` rect per open bar, from `scale(reviewed)` to `scale(fadeTo)`;
  - `line.frame-cutoff` at the research cutoff;
  - `.archive-banner` element when `state.range === '2000'`;
  - `a.archive-link` in `about()`;
  - `#range-toggle` always hidden.

- [ ] **Step 1: Write the failing browser tests** (in `tests/test_site_browser.py`, replacing the "Annales must run solid to the 2000 wall" assertion at L342–351 and the `.coverage-label` click at L374–375)

```python
    def test_open_frame_marks(self):
        self.page.goto(f'{BASE}/#focus=annales')
        self.page.wait_for_selector('svg.field')
        self.assertEqual(self.page.locator('.coverage-wall').count(), 0)
        self.assertGreater(self.page.locator('rect.unreviewed').count(), 0)
        self.assertEqual(self.page.locator('line.frame-cutoff').count(), 1)
        note = self.page.locator('.field-panel').inner_text()
        self.assertIn('reviewed through 2000', note)

    def test_archive_reachable_from_reading_this_map(self):
        self.page.goto(f'{BASE}/#tab=about')
        link = self.page.locator('a.archive-link')
        self.assertEqual(link.count(), 1)
        link.click()
        self.page.wait_for_selector('.archive-banner')
        self.assertIn('1.121', self.page.locator('#edition-label').inner_text())
        self.assertTrue(self.page.locator('#range-toggle').is_hidden())
        self.assertEqual(self.page.locator('.coverage-wall').count() >= 0, True)
```

In `tests/test_indigenous_browser.py`, L57–63 and L141–147 click `#range-toggle a[aria-pressed="false"]` to leave the archive. Replace those clicks with `self.page.locator('.archive-banner a').click()`. Keep the `1.121` and strand-count assertions.

- [ ] **Step 2: Build, serve and run them to see them fail**

Run:
```bash
python3 scripts/build_site.py >/dev/null
(python3 -m http.server 4173 --bind 127.0.0.1 --directory docs >/dev/null 2>&1 &)
python3 -m unittest tests.test_site_browser -k open_frame -k archive -v
```
Expected: FAIL. `.coverage-wall` count is 1 and `a.archive-link` count is 0.

- [ ] **Step 3: Implement**

`fieldSvg` replaces the wall block with:

```js
  const fr = view.frame;
  if (fr.open) {
    const cx = view.scale(fr.cutoff);
    grid += `<line class="frame-cutoff" x1="${cx}" y1="${view.axisTop + 16}" x2="${cx}" y2="${bottom}"/>
      <text class="cutoff-label" x="${cx - 4}" y="${view.axisTop + 13}" text-anchor="end">research cutoff ${esc(graph.scope.frame.research_cutoff)}</text>
      <line class="scale-break" x1="${bx}" y1="${view.axisTop + 16}" x2="${bx}" y2="${bottom}"/>`;
  } else {
    /* the archived 2000 view: unchanged wall and extension zone code below */
    grid += `<line class="coverage-wall" .../>` // keep the existing markup verbatim
  }
```

The existing `if (ext) {…}` block runs only when `!fr.open`. In the bar markup, after the solid rect of each bar with `b.open && fr.open && b.fadeTo > b.drawEnd`, add:

```js
`<rect class="unreviewed" x="${view.scale(b.drawEnd)}" y="${b.y}" width="${Math.max(0, view.scale(b.fadeTo) - view.scale(b.drawEnd))}" height="${b.h}"><title>Reviewed through ${b.drawEnd}; later work not yet surveyed</title></rect>`
```

Text changes (exact wording):

- **Legend (L422–423):** for open graphs, "solid to the year reviewed · faded where later work is not yet surveyed" and "◆ selected later intervention". Keep the old strings for the archive.
- **`fieldDateNote`, coverage_limit branch, open frame:** `opening` is unchanged except "drawn to ${reviewed}". `ending` becomes:

  ```js
  `This entry is <strong>reviewed through ${reviewed}</strong>. The faded part runs to the research
    cutoff (${esc(graph.scope.frame.research_cutoff)}): later work is not yet surveyed here, not absent.`
  ```

  Here `reviewed = reviewedThrough(n) ?? frameOf(graph).end`. Persons and journals without `coverage` use "drawn to the research cutoff; later work is cited where checked".
- **`fieldPanel` empty-state paragraph, open frame:** "A mark is solid through the year its entry has been reviewed and faded after it, to the research cutoff. Fields are being extended one at a time; a faded tail means later work is not yet surveyed, not that the field stopped." Keep the old paragraph when `!frameOf(graph).open`.
- **`interventionNote` and `extensionSection`:** replace `c.baseline_through || 2000` with `reviewedThrough(n) ?? c.baseline_through ?? 2000`. Change the eyebrow to `AFTER ${…} · SELECTED LATER INTERVENTIONS` and drop "not a survey of the field after 2000" in favour of "selected interventions after the review year, not a survey".
- **`fieldList`:** `hi = frameOf(graph).open ? frameOf(graph).end : Math.max(graph.scope?.main_period?.[1] ?? 2000, …)`.
- **Field header (L901):** for open graphs, `` ` · ${n} entries reviewed through 2000` `` (count group nodes with `reviewed_through === 2000`). Otherwise the old text.
- **Landing fine print (L809):** "The atlas has no closing date; its entries are reviewed through 2000 unless marked otherwise, so record bars after 2000 can run ahead of the atlas's reading."
- **`landing.mjs`:**
  - L6: `export const AXIS = {start: 1880, end: 2024};`;
  - delete the `.coverage-line` markup at L152–154;
  - in `tests/test_site_core.mjs` L410, replace the `coverage-line present` assertion with `assert.ok(!svg.includes('coverage-line'))`.
- **`rangeControls()`:** the whole body becomes:

  ```js
  function rangeControls() {
    const toggle = $('range-toggle'), eyebrow = $('scope-eyebrow');
    toggle.hidden = true;
    const arch = production.scope?.archive;
    if (state.range === '2000' && arch) {
      eyebrow.textContent = `${arch.baseline_period[0]}–${arch.baseline_period[1]} · ARCHIVED VIEW · REVISION ${arch.baseline_revision}`;
      $('edition-label').textContent = `Archive ${arch.baseline_revision} · the original 1920–2000 experiment`;
    } else {
      eyebrow.textContent = 'EARLIER ROOTS TO THE PRESENT · ENTRIES REVIEWED FIELD BY FIELD';
      $('edition-label').textContent = `Draft ${production.revision_history.at(-1).version}`;
    }
  }
  ```

  `ensureRange` reads `production.scope?.archive?.baseline_asset ?? production.scope?.extension?.baseline_asset`.
- **Archive banner:** in `render()`, when `state.range === '2000'`, insert this at the top of the main content:

  ```js
  `<div class="archive-banner" role="note"><strong>Archived view.</strong> The original 1920–2000 experiment (revision ${esc(production.scope.archive.baseline_revision)}). <a href="${esc(href({range: ''}))}">Return to the current atlas →</a></div>`
  ```

- **`about()` "Periods are approximate groupings":** replace the coverage sentences with:

  ```js
  `The atlas began as a 1920–2000 experiment and is now being extended field by field, with no closing date. Each entry says how far it has been reviewed; most are reviewed through 2000 so far, and some carry selected later interventions. <a class="archive-link" href="${esc(href({range: '2000', tab: 'map'}))}">Open the original 1920–2000 experiment (archived revision ${esc(production.scope.archive?.baseline_revision || '1.121')}) →</a>`
  ```

  In "What this beta does not yet cover", change "Coverage thins sharply after 1985" to "Most entries are reviewed only through 2000; work since then is being added field by field". Change "About a quarter of entries record no objection at all" to "Many entries record no objection at all".
- **`index.html`:**
  - L6 meta: "A teaching map of historiography with earlier roots, extended field by field, for reading alongside Lynn Hunt’s Writing History in the Global Era."
  - L19 default eyebrow: "EARLIER ROOTS TO THE PRESENT".
- **`styles.css`** (append):

  ```css
  rect.unreviewed { fill: var(--bar, #c9bba5); opacity: .28; }
  line.frame-cutoff { stroke: var(--ink-soft, #7a6f60); stroke-dasharray: 2 3; }
  .archive-banner { margin: 0 0 1rem; padding: .6rem .9rem; border-left: 3px solid #b5651d; background: #fbf4ea; font-size: .92rem; }
  ```

- [ ] **Step 4: Run all the site tests**

Run:
```bash
node tests/test_site_core.mjs 2>&1 | grep -E "^# (pass|fail)"
python3 scripts/build_site.py >/dev/null && python3 tests/run_site_checks.py 2>&1 | tail -3
```
Expected: `# fail 0`; browser `OK`. If `test_site_browser` still asserts the old eyebrow or `range-toggle` visibility elsewhere, update those assertions to the new strings above. Do not weaken the archive assertions.

- [ ] **Step 5: Commit**

```bash
git add site tests docs
git commit -m "Site: open frame — reviewed-through tails, research cutoff, archive banner and link; title without dates"
```

### Task 5: Visual check

**Files:** none (verification only)

- [ ] **Step 1: Screenshot four routes** with the Playwright snippet below, then look at each image:
  - `#family=environment&view=map`
  - `#focus=annales`
  - `#tab=about`
  - `#range=2000&tab=map`

```python
from playwright.sync_api import sync_playwright
for route, name in [('#family=environment&view=map', 'env'), ('#focus=annales', 'annales'), ('#tab=about', 'about'), ('#range=2000&tab=map', 'archive')]:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1500, 'height': 1200})
        pg.goto('http://127.0.0.1:4173/' + route); pg.wait_for_timeout(3000)
        pg.screenshot(path=f'/tmp/claude-1000/-home-jic823-historiography/349191d8-7a3f-4dc4-b66b-19d6c4dee53d/scratchpad/open-{name}.png'); b.close()
```

Expected:
- **Environment:** bars are solid to 2000, then faint to 2026, with no "CURATED COVERAGE ENDS" label.
- **Archive:** looks as it did before, with the wall, a banner and the 1.121 edition label.

Fix any overlap of labels with the faded tails before continuing.

### Task 6: Docs, pinned-file amendments, revision notes

**Files:**
- Modify: `GRAPH-FORMAT.md`:
  - new top section "Current revision 1.132: open frame";
  - mark the policies at L54–70, L147–161, L231 and L307 as historical, with one line each: "Superseded by 1.132".
- Modify: `README.md` L1–4, L43–55, L85; `site/README.md` L4–8, L74–83; `DEVELOPMENT.md` L3–12, L39, L59, L80.
- Modify: `REVISION-NOTES.md`: append "Revision 1.132: open frame".
- Create: `data/production-batches/open-frame-1.133/README.md`.
- Modify: `data/production-batches/extension-1.123/acceptance.json`: add an `amendments` entry `{file, amended_sha256, reason}` for each file this plan changes that the 1.123 manifests pin. To find them:

  ```bash
  python3 -c "import scripts.accept_digital_release as m; print('\n'.join(m.frozen_errors()))"
  ```

  It lists `Pinned input changed: <file>` for each.

- [ ] **Step 1: Write the amendments and check them**

```bash
python3 - <<'EOF'
import json, hashlib
from pathlib import Path
import scripts.accept_digital_release as m
rec = Path('data/production-batches/extension-1.123/acceptance.json'); r = json.loads(rec.read_text())
for line in m.frozen_errors():
    name = line.split(': ', 1)[1]
    path = m.frozen_path(name)
    r.setdefault('amendments', []).append(dict(file=name, amended_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        reason='Revision 1.132 open frame (user, 2026-10-14): 2000 cutoff ended; archive view kept.'))
rec.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n')
print(m.frozen_errors())
EOF
```
Expected: the last line prints `[]`.

- [ ] **Step 2: Write the docs**

The GRAPH-FORMAT section must state:
- the new fields: `scope.frame`, `scope.archive`, node `coverage.reviewed_through` and `coverage.basis`, `date_span.end_kind: "open"`;
- schema 1.5;
- that `extension_coverage` and strand `intervention_year` remain as selected later interventions;
- that the archive is revision 1.121;
- that `historiography-1920-2000.json` keeps its name because archives are recovered from git history under it;
- how to extend a field: raise `coverage.reviewed_through` only after a survey of the field's later work, recorded in a revision batch.

README and site README: replace "1920–2000 with earlier roots and a partial post-2000 extension" with "earlier roots to the present, extended field by field". Replace the dashed-wall paragraph with the reviewed-through paragraph from Task 4. Counts: 166 entries, 913 relationships (unless 1.133 has landed).

- [ ] **Step 3: Run the full CI sequence**

Run:
```bash
python3 scripts/validate_graph.py | tail -1
python3 -m unittest tests.test_graph_validation tests.test_people_validation tests.test_evidence_asset tests.test_practice_families tests.test_student_beta tests.test_indigenous_deep_dive tests.test_indigenous_foundations tests.test_borderlands_release_candidate tests.test_evidence_coverage_audit tests.test_publication_repairs tests.test_open_frame
node tests/test_site_core.mjs 2>&1 | grep -E "^# (pass|fail)"
python3 scripts/build_site.py >/dev/null && python3 tests/run_site_checks.py 2>&1 | tail -2
git diff --exit-code --stat docs
```
Expected: OK, `# fail 0`, OK; no docs diff after committing in Step 4.

- [ ] **Step 4: Commit**

```bash
git add GRAPH-FORMAT.md README.md site/README.md DEVELOPMENT.md REVISION-NOTES.md data/production-batches docs
git commit -m "Revision 1.132: open frame — docs, acceptance record, 1.123 amendments"
```

Push only with the user's yes.

---

## After this plan (not tasks here)

- **1.133, Chakrabarty:** rebase the draft's `batch.json` to baseline 1.132. His group-free person node needs no `coverage`. The 2009 environment edge is ordinary content.
- **1.134, science-studies critiques.**
- **Field-by-field extension:** each batch raises a field's `coverage.reviewed_through` only after its later work has been surveyed.
