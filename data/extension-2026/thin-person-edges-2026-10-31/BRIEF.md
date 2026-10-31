# Low-edge person entries: relationship backfill (revision 1.235 candidate)

User, 2026-10-31: "review all the low edge historians" (after "Mary Jane Logan McCallum edges are very
small; she coauthored a book with Perry" and "Rosenberg is missing all together"). Twenty-one person entries
in `historiography-1920-2000.json` (revision 1.234) have three relationships or fewer.

Inputs, in this folder:
- `thin-entries.json`: each entry's description, works, current edges, sources (with what was read) and the
  nodes that already mention it.
- `endpoints.json`: every existing node (fields, groups, person entries). **Edges may only join existing
  endpoints.** A missing endpoint is recorded as held, never created.
- `mccallum-draft.json`: a coordinator draft for McCallum (five edges). Treat it as leads to verify, not as
  accepted.

Protocol: `data/field-research/stedman-jones-relationships-2026-10-25/review-protocol.md` (one researcher per
historian, fresh reading for each claim, record what is unread, independent review follows). Degree is a
triage
signal, not a quota: propose only relationships the evidence supports. Typical outcome 2–6 new edges per
person; zero is acceptable with reasons.

## Output: one folder per person, `<person_id>/entry-draft.json`

Format of `data/extension-2026/davis-backfill-2026-10-17/davis/entry-draft.json` (a backfill of an existing
entry, no `node`):
```
{"status": "proposal_for_review", "prepared": "2026-10-31",
 "applies_to": "historiography-1920-2000.json revision 1.234 -> candidate 1.235 (<person_id>: existing person entry, relationship backfill; no new node)",
 "review_status": "needs_review",
 "proposed_edges": [{"proposal_id": "<short>_rel_01", "source": "...", "target": "...", "type": "connection" | "critique",
     "relationship_kind": "contribution" | "influence" | "comparison" | "critique", "directed": true|false,
     "relationship": "<one sentence, the claim, with the work and year>", "map_label": "<short label>",
     "evidence_note": "<what was read, exact locators (page, paragraph, section), quoted short phrases, what remains unread, and the limits of the claim>",
     "source_ids": ["existing or new source ids"], "classification_basis": "editorial_review"}],
 "edges_considered_not_proposed": [{"pair": "a ↔ b", "reason": "..."}],
 "new_sources": [{"id": "<prefix>_<author>_<short>_<year>", "title": "<full citation>", "citation": "<same>", "url": "<DOI, publisher, JSTOR stable, institutional repository, or the author's own page>",
     "verification": {"status": "supporting_page_checked" | "bibliographic_metadata_checked", "checked_on": "2026-10-31", "note": "<what was read>"}}],
 "reused_sources": [{"id": "<existing source id>", "use": "<which proposals>"}],
 "source_addenda": {}}
```
Rules for edges:
- `relationship_kind: critique` needs `type: critique`; comparison edges are `directed: false` (co-authors:
  precedent Kealey ↔ Palmer).
- Direction: `source` contributes to / influences / critiques `target`. A historian's contribution to a field
  is person → field.
- Do not duplicate an existing edge (same endpoints and kind). Check the person's current edges and the
  other endpoint's.
- Person ↔ person edges are worth most: named debts, co-authorship, published exchanges and critiques, with
  both persons as existing endpoints.
- Use new source id prefix `thin_` (e.g. `thin_bourke_fear_2005`).

## Evidence rules (binding)

- **Read what you cite.** Publisher pages, open-access articles, journal abstracts, reviews in open journals
  (H-Net, Reviews in History, BC Studies, Manitoba History, etc.), institutional repositories, the author's
  own pages, and lending-library or public-domain scans are fine. Say exactly what was read; if only an
  abstract or blurb was read, the claim must be bounded to it.
- **Never** read or cite document-sharing or pirate-copy sites, shadow libraries, unauthorised transcriptions or uploads of in-copyright work, or course-hosted scans of whole books. If a text is only reachable that way,
  treat it as unread. Never name such a route anywhere in your output.
- **Topic is not evidence** of a relationship between two people. Shared subject matter alone never makes an
  edge; a named debt, citation-in-argument, co-authorship or exchange does.
- No Wikipedia as evidence (it may point you to sources, which you then read).

## OCAP (binding for McNickle, Trask, Innes, McCallum and any Indigenous material)

Describe scholarship, not community knowledge: what scholars argued and how collaborations worked. Never
give the content of oral narratives, teachings, ceremonies, protocol, songs or traditional knowledge. No
genealogies or family details; do not quote narrators or interviewees. Do not add or change identity notes.
Community-controlled sites (e.g. Shekon Neechie): cite and link, quote only their public self-description.

## Scope

Write only inside your assigned `<person_id>/` folders. Do not edit `historiography-1920-2000.json`, other
folders, or anything else in the repository. Do not commit. Network politeness: one request at a time per
host, a descriptive user agent is fine.
