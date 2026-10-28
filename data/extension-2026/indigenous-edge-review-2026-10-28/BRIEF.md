# Edge review: Indigenous person entries of 1.201 (brief, 2026-10-28)

**Request (user, 2026-10-28):** "we need to use research agents to review the edges more carefully". The trigger: Winona Wheeler appears to engage settler colonial studies, but the graph has no relationship between her and `settler_colonialism`. A C Magazine conversation between Joi T. Arcand and Wheeler (https://cmagazine.com/articles/im-a-little-too-rebellious-for-that-a-conversation-with-joi-t-ar) only served its title to automated reading.

## Task, per entry
1. **Check every existing edge** touching the entry against its cited source. Is the type right (critique / contribution / influence / connection / comparison)? Is the target field and strand right after the 1.201 split, and does the label say only what the text says? Verdict for each: keep, revise (give the exact new wording), or reroute (give the new target).
2. **Find missed relationships** in the scholar's own published writing, especially:
   - engagement with **settler colonial studies** (Wolfe, Veracini, the *Settler Colonial Studies* journal, "settler colonialism" as a frame), whether adoption, use or critique;
   - the other fields in the graph: `indigenous`, `ethnohistory`, `native_newcomer`, `community_engaged_indigenous`, `settler_colonialism`, `oral`, `environment`, `womens`, `canada_*`, and others.

   A missed relationship needs a passage you have read, with page or paragraph locators.
3. **Report reception.** Note where named readers attach the scholar to a field. Encode only what texts say. Don't synthesise a "critique of X" from topic overlap.

## Where things are
- **Graph:** `historiography-1920-2000.json` (revision 1.203).
  - Nodes carry `representative_people` rosters, strands and `scope_note`.
  - Edges carry `source`, `target`, `target_strand`, `type`, `label`, `evidence` and `source_ids`.
  - Sources live in `sources`.
- **1.201 materials:** `data/extension-2026/indigenous-histories-2026-10-27/`. Read `BRIEF.md` and `OCAP-REVIEW.md` first. Entry drafts are in `<id>/entry-draft.json`. Evidence notes are `evidence-*.md`; use them, but they are local only.
- **Do not open `PRIVATE-identity-review.md`.** Do not discuss anyone's identity beyond what an entry already records.

## Hard rules
- **Read-only.** Do not edit the graph, scripts, tests or any file outside your own output file.
- **OCAP** (see `OCAP-REVIEW.md`):
  - describe scholarship, not community knowledge;
  - no ceremonial or protocol content, no genealogies, no family detail;
  - short attributed quotations of a scholar's own argument only.
- **Source provenance:** never read from or link to dokumen.pub, Scribd, libcom, Internet Archive user uploads, or course-page scans. Use publishers, DOIs, journal sites, institutional repositories, open-access presses, and author or institutional pages. If a site blocks automated reading, record it as blocked; do not work around bot checks.
- **No personal data to APIs:** do not send any email address (no Unpaywall email, no OpenAlex mailto).
- **Mark what you read and what you didn't:** "read in full", "read pp. X–Y", "known through publisher description or abstract", "blocked".

## Output
Write exactly one file: `review-<LETTER>.md` in this folder. For each entry:
- a table of existing edges with verdicts and reasons;
- proposed new edges as JSON-like rows: `source`, `target`, `target_strand` (existing or "new: title"), `type`, `label`, `evidence` (short, with locator), `source` (URL + citation), and `read_status`;
- a "held" list of items that need a passage nobody could read.

Keep the file under about 400 lines. End with a 5-line summary.
