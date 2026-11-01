# Relationship backfill: the thin 1.232–1.234 person entries (revision 1.236 candidate)

User, 2026-10-31: "We need to work on those 18" (person entries added in revisions 1.232–1.234 that
still have fewer than five relationships in `historiography-1920-2000.json` revision 1.235), "1 historian
per agent". You are the researcher for **one** historian, named in your instructions. Claude verifies every
claim afterwards against the passages you cite, and holds anything it cannot confirm, so depth and honest
limits matter more than count.

The earlier packets for these people were accepted only after Claude's verification removed or held
weak claims (see `held_at_verification`). Common failures then: citing pages outside what was actually read,
unreadable or wrong URLs, dates taken from reprints, abstracts treated as arguments, and relationships
inferred from shared topic. Avoid all of them.

## Inputs (this folder; read-only for you)

- `entries.json`: your historian's record. Description, works, scope note, every current edge (with its
  relationship and evidence note), the sources those cite, nodes whose text mentions them, and edges held at
  verification with the reason. Start here.
- `endpoints.json`: every existing node. **Edges may only join existing endpoints.** A wanted endpoint
  that does not exist is recorded as held ("missing endpoint"), never created.
- Protocol: `../../field-research/stedman-jones-relationships-2026-10-25/review-protocol.md`.
- Format precedent: `../davis-backfill-2026-10-17/davis/entry-draft.json` and the 1.235 drafts in
  `../thin-person-edges-2026-10-31/*/entry-draft.json`.

## What to do

1. Inspect every current edge of your historian (both directions), its sources and its limits.
2. Find the relationships the entry is missing. Priority order:
   - **person ↔ person**, with both people existing endpoints: named intellectual debts, supervisors and
     students, co-authorship and co-editing, published exchanges, reviews and critiques, responses;
   - person → field / school / debate: a contribution or critique that a substantive source names, where
     the current edges do not already carry it;
   - incoming edges: other scholars' named critiques of or debts to your historian.
3. For each lead, read fresh primary passages. Record exact locators (page, paragraph or section), the
   original publication year (not a reprint's), and short quoted phrases. If you could read only an abstract,
   a publisher page or a review, bound the claim to that and say so.
4. Re-examine the held edges in `held_at_verification`. Propose one again only with **new** evidence that
   answers the stated reason; otherwise list it under `edges_considered_not_proposed` with the reason.
5. Record every lead you investigated and did not propose, with the reason: already represented, missing
   endpoint, unread or inaccessible evidence, or searched without a verified relationship.

Typical outcome: 2–6 new edges. Zero is acceptable with reasons. Degree is a triage signal, not a quota;
never pad.

## Output: `<person_id>/` (your folder; write nothing anywhere else)

1. `entry-draft.json`:
```
{"status": "proposal_for_review", "prepared": "2026-10-31", "researcher": "Sol 6.1 (Codex)",
 "applies_to": "historiography-1920-2000.json revision 1.235 -> candidate 1.236 (<person_id>: existing person entry, relationship backfill; no new node)",
 "review_status": "needs_review",
 "proposed_edges": [{"proposal_id": "<short>_bf_01", "source": "...", "target": "...", "type": "connection" | "critique",
     "relationship_kind": "contribution" | "influence" | "comparison" | "critique", "directed": true | false,
     "relationship": "<one sentence: the claim, with the work and its original year>", "map_label": "<short label>",
     "evidence_note": "<what was read, exact locators, short quoted phrases, what remains unread, limits of the claim>",
     "source_ids": ["existing or new source ids"], "classification_basis": "editorial_review"}],
 "edges_considered_not_proposed": [{"pair": "a ↔ b", "reason": "..."}],
 "new_sources": [{"id": "bf_<author>_<short>_<year>", "title": "<full citation>", "citation": "<same>",
     "url": "<DOI, publisher, JSTOR stable, institutional repository, open journal, or the author's own page>",
     "verification": {"status": "supporting_page_checked" | "bibliographic_metadata_checked", "checked_on": "2026-10-31", "note": "<exactly what was read>"}}],
 "reused_sources": [{"id": "<existing source id>", "use": "<which proposals>"}]}
```
2. `reading-log.json`: every document you opened, in order: `{"url", "title", "what_was_read"
   (pages, sections or "abstract only"), "used_for" (proposal ids or "lead not proposed")}`. Include
   failed fetches (403, paywall, robots.txt) as `"what_was_read": "not accessible: <reason>"`.

Edge rules:
- `relationship_kind: critique` needs `type: critique`. Comparison and co-authorship edges are
  `directed: false`. Otherwise `source` contributes to, influences or critiques `target`; a historian's
  contribution to a field is person → field.
- No duplicates of an existing edge (same endpoints and kind); check the other endpoint's edges too.
- The relationship sentence must state what the passage supports and no more.

## Evidence rules (binding)

- **Read what you cite.** Fine: publisher pages, DOIs, open-access articles, journal abstracts, reviews in
  open journals (H-Net, Reviews in History, BC Studies, etc.), institutional repositories, the author's own
  pages, interviews on institutional or journal sites, public-domain or lending-library scans.
- **Never** read or cite document-sharing or pirate-copy sites, shadow libraries, unauthorised uploads or
  transcriptions of in-copyright work, or course-hosted scans of whole books. If a text is only reachable
  that way, treat it as unread. **Never name such a route anywhere in your output.**
- Respect robots.txt, 403s and bot checks; do not work around them.
- No Wikipedia as evidence (use it only to find sources you then read). OpenAlex is paused: do not use it.
- **Topic is not evidence.** Two people writing on the same subject is never an edge; a named debt,
  citation in argument, co-authorship, supervision or exchange is.
- **Living people:** never write a living person's birth year anywhere in the draft.
- Network politeness: one request at a time per host.

## Scope

Write only inside your `<person_id>/` folder. Do not edit `historiography-1920-2000.json`, the input
files, other people's folders or anything else. Do not commit. End with a short summary of what you
proposed, what you held and what you could not read.
