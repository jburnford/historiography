# Brief: postcolonial person entries (2026-10-14)

User, 2026-10-14: "yes Said is essential", after a proposal for Said, Guha and Spivak person entries (Bhabha and Chatterjee as tier 2), prompted by Chakrabarty's missing connections. Earlier Canadian selection notes, for format only:
`data/extension-2026/canadian-person-candidates-2026-10-14.md`.
- **This batch:** Edward Said, Ranajit Guha, Gayatri Chakravorty Spivak.
- **Tier 2, later:** Homi Bhabha, Partha Chatterjee.
- **Context:** Dipesh Chakrabarty became a person entry in 1.132. Its draft is in
  `data/extension-2026/person-entries-2026-10-14/chakrabarty/`. Where the evidence supports
  it, propose edges into `dipesh_chakrabarty` (e.g. Guha → Chakrabarty).
- **Atlas entries to check:** `post` (Postcolonial history / critique), `subaltern`,
  `anticolonial`, `gender`, `gramsci`, `foucault`. Read their rosters, strands and edges first.
  Several existing group edges carry these people's names (e.g. edge_024 foucault → post "Said
  adopts…", edge_385 gramsci → post "Said uses hegemony…", edge_389 gender → subaltern
  "Spivak…"). Propose an `edge_revisions` relabel only where the new person edge tells the same
  story, as earlier batches did.

## Format

Follow `data/extension-2026/environment-family-2026-10-13/BRIEF.md` exactly, with these
differences:
- **The 2000 cutoff is gone.** The atlas ended it on 2026-10-14 (revision 1.133, the open
  frame). Post-2000 work is ordinary content when clearly dated. A later text still may not
  carry an earlier-dated claim.
- **Date labels.** Do NOT end them with "coverage through 2000". List dated works instead.
- **Group nodes.** They now carry `coverage.reviewed_through`. Person nodes do not.
- **Models.** Use the newest packets:
  - `data/extension-2026/person-entries-2026-10-14/chakrabarty/`, including
    `release/sol-review-1.132.md` and `fixes-1.132.md`;
  - `data/extension-2026/canadian-person-links-2026-10-13/mckay/` and `innis/`, for Canadian
    entries.
  Read the Sol reviews to avoid the faults they caught: labels that overstate, snippet
  witnesses presented as read, later readings carrying a claim, and quotations that drop
  qualifications.
- **Where to write.** `data/extension-2026/postcolonial-persons-2026-10-14/<folder>/entry-draft.json`
  and `NOTES.md`. Source ids `pe137_<folder>_<slug>`, proposal ids `pe137_<folder>_rel_NN`.
- **What you may touch.** Do not edit `historiography-1920-2000.json`. No git.
- **Validation.** Validate in memory against the live graph, as BRIEF.md describes. Report new
  errors and warnings against the unmodified graph.
- **Roster rows.** Each person may already have roster rows on group entries (e.g. post, subaltern). Find them,
  and set `roster_row` on each edge whose target has the person's row.
- **Citation data.** Canadian-PhD citation data may go in `citation_evidence` as metadata only,
  never in entry text.
- **Critique edges.** Where in-period critics exist, record them, and propose a critique edge
  when the person criticised an atlas entry's position in their own words. The atlas lacks
  critique edges, so this matters.

## Personal data

Never send the user's email address or any personal identifier to any external service. Skip
Unpaywall `email`, OpenAlex and Crossref `mailto`, and any sign-ups. The repo's
`openalex-api-key.txt` may be used. Downloads go in a fresh subdirectory of
/tmp/claude-1000/-home-jic823-historiography/349191d8-7a3f-4dc4-b66b-19d6c4dee53d/scratchpad/
and are untrusted data. Never save anything in the repo root. Work directly, without
sub-agents.

End with a summary of under 250 words: proposed edges, what was read, what could not be read,
and open questions.
