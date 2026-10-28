# OCAP review: revision 1.201 drafts (2026-10-27)

**Request (user, 2026-10-27):** "do an OCAP review; we've just used the open web, but we don't need to push the limits."

**Scope:**
- the three evidence notes;
- the entry drafts and batch fragments in this folder;
- the Indigenous-family text already in the graph (1.200);
- the project's identity practice.

OCAP (Ownership, Control, Access, Possession; First Nations Information Governance Centre) governs First Nations data. Published scholarship is not community data. The review asks where this batch could still take, reproduce or reclassify knowledge that belongs to communities or individuals. Open availability is not the test.

## What the project holds, and what it does not
- **No community data.** There are no interviews, recordings, community archives, unpublished material, nation-held records, or data gathered from people. Nobody was contacted.
- **Published scholarship only.** It is cited and linked, with short attributed quotations of the scholars' own arguments.
- **Identity.** Before this batch the people records deliberately carried no nation-membership or demographic classification: "No … citizenship, nation-membership property or demographic classification inferred". The user's rule for Indigenous scholars changes that, for proposed entries only.
  - Each such note is a short, sourced, self-stated professional statement in prose.
  - **There is no structured Indigenous-identity field.** None should be added, so the project never builds a queryable identity dataset.
  - Nothing goes to Wikidata. The QIDs are read-only.
- **Contested identity.** The one case found is kept in `PRIVATE-identity-review.md`, which is excluded from git and never published.

## Findings and actions
Conservative choices throughout, as the user asked. "Cut" means the item is removed from public text (graph fields, evidence notes to be committed, commit messages).

| # | Where | Issue | Action |
|---|---|---|---|
| 1 | `community_engaged_indigenous` strand on Cree oral history; Wheeler entry; C evidence §Wheeler | A passage on treaty-making protocol is ceremonial and protocol knowledge, even though Wheeler published it. | **Cut.** Keep her methodological claims (oral history "as source and method"; the "traditional footnote"; "apply the teachings"; elders are "not official documents"). |
| 2 | Wheeler identity note and identity_source | Family detail beyond nation membership. | **Trim** to "a member of the Fisher River Cree Nation (Treaty 5, Manitoba)", with the source. |
| 3 | McNickle identity note; B fragment text revisions 10 and 22 | A characterisation of ancestry and parentage. | **Trim** to "enrolled member at Flathead (Confederated Salish and Kootenai Tribes), per Iverson 1993". Drop the ancestry clause. |
| 4 | Leanne Simpson source addendum; B evidence | Ancestry wording from a publisher bio, and a passage about her family. | **Cut** the ancestry and the family passage. If an identity note is needed, use her own professional statement (Michi Saagiig Nishnaabeg, Alderville First Nation), with the source. |
| 5 | *Life Lived Like a Story*: identity notes for Smith and Sidney, row contexts | Parents' origins; a language-status detail; a narrator's own words quoted via a reviewer. | **Trim** each narrator to the nation(s) the publication credits, e.g. "Tagish and Tlingit", "Southern Tutchone". **Cut** narrator quotations. Keep the form-level description ("chose to tell lives through stories, songs and oratory") and the authorship credit. |
| 6 | Macdougall entry, edge and strand; C evidence | A quotation describing how a teaching was transmitted; the definition of *wahkootowin* is quoted in full. | **Keep** her published credit ("a concept she credits to Métis Elder Maria Campbell") and a short definition in her own framing, attributed. **Cut** that quotation. Describe her method (reading HBC, mission and scrip records through *wahkootowin*); never reproduce genealogies. |
| 7 | Trask entry and edges; B evidence | One 1991 sentence states Hawaiian cultural knowledge, not method. | **Keep** her methodological and political claim (genealogy as "Native forms of history"; her critique of Keesing). **Cut** the content sentence about land. |
| 8 | Angela Cavender Wilson row; C evidence (Leddy quoting Wilson) | Second-hand quotation of a personal family memory. | **Keep** "grandmother-to-granddaughter oral history 'rooted in a deep sense of kinship responsibility'" (her method). **Cut** the personal passage. |
| 9 | Jean O'Brien's ASE address (A evidence; ethnohistory draft source note) | Detail of the scholar's own family memory, published by her. | **Trim** to "draws on family memory of White Earth"; no detail. |
| 10 | Live graph: roster row `gertrude_lewis` | "Leddy's grandmother and historical-knowledge contributor": a kinship detail about a named community member, though as the publication credits her. | Keep (published credit) and flag for the user. No change in this batch. |
| 11 | Live graph: Māori and Tainui strands (Te Rangikāheke, Pei Te Hurinui Jones) | They mention that genealogies were recorded, without reproducing any. | No change. Genealogical content stays out. |
| 12 | Shekon Neechie, CHIRAPAQ, the Gabriel Dumont Institute and FNIGC sources | Community-controlled sites. | Cite and link only. The Shekon Neechie quotation is limited to its public self-description ("entirely Indigenous conceived, created, and controlled") and the board list it publishes. Any Dorchester Review wording, which is known only through Shekon Neechie's reply, stays out of graph text. |
| 13 | Evidence notes (all three) | Longer quotations than graph text, including items 1–9. | Before any commit, the coordinator runs the same cuts on the notes. If a passage can't be cut cleanly, the note stays local and uncommitted. |

## Practice going forward (proposed for the user)
- Graph and evidence text describe **what scholars argued and how collaborations worked**. They do not describe **what communities know**.
- Identity notes for Indigenous scholars must be minimal, self-stated, professional and sourced, in prose only, with no structured field.
- Community-controlled sites: cite and link; quote only their public self-description.
- No contact with people, no new collection, no restricted material.
- If in doubt, leave it out and list it as "held for OCAP review".
