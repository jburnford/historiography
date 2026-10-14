# Revision 1.133: the open frame

**Authorization.** User, 2026-10-14: "we need to end the 2000 break in this project"; the 2000
frame "comes from the original experiment where I scoped it to 2000, but we're building it out
now". The decisions, chosen in the session:
- switch now and build field by field, with a visible "reviewed through" marker;
- keep the exact-2000 view as an archive reachable from *Reading this map*;
- drop the dates from the title.

**Applier.** `scripts/apply_open_frame.py`. The baseline is 1.132 (`drafts/historiography-1920-2000.v1.132.json`,
or git history). `--check` rebuilds 1.133 exactly. The acceptance record keeps the prior scope,
title, schema, 102 prior date labels and the prior spans.

**Data.**
- schema 1.5;
- `scope.frame` and `scope.archive`, the latter pointing to the exact 1.121 view, sha256 `5fe82ffc…a9`;
- `coverage.reviewed_through: 2000` on all 95 groups;
- open spans and 27 open journal intervals;
- one reworded pathway question (global scale).

**Site.** Plan Tasks 3–4:
- reviewed-through tails, a research-cutoff line, the archive banner and link, and the toggle
  hidden;
- every behaviour gated on the data;
- `data/graph-2000.json` is published byte-identical.

**Plan deviations, accepted.**
- An entry with `reviewed_through` is open unless its span ends explicitly.
- The solid end is `max(reviewed_through, span.end)`.
- Person entries carry no `coverage`.
- `clean_label` was rewritten to avoid dangling separators.
- Three venue notes saying "atlas boundary" were opened too.
- The journal validator accepts a null end.
- `apply_open_frame` recovers its baseline in a clean checkout.
- A mobile legend fix; open venue intervals read "Dated from … onward".

**Pinned files.** The revision 1.123 acceptance pins site and data hashes. The files this revision
changes are logged in `data/production-batches/extension-1.123/acceptance.json['amendments']`.

**Checks.**
- validate_graph;
- the CI data tests plus `tests.test_open_frame`;
- view tests and browser tests;
- `git diff docs` clean after building.
