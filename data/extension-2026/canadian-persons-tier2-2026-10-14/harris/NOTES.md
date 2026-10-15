# Cole Harris: person entry draft (Tier 2 Canadian persons, pe139)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- **Edge 3 (the Historical Atlas of Canada) is excluded** from the release (`include: false`): same endpoints and type as edge 2; the Atlas stays in the representative works. Open question 1 is resolved this way.
- Edge 7 (Napoleon, `indigenous → cole_harris`) is released as a named-proxy critique; its evidence no longer says 'Optional'. Open question 2 is resolved this way.
- Edge 1 now says that no derivation from Wolfe is established by the texts checked (finding 4), keeping the citation evidence and the roster's 'earlier or beside'.

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and nothing
was committed. The draft is in [entry-draft.json](entry-draft.json).

## Validation (historical, drafting stage)

The brief named live revision 1.138 or later. During drafting the live file moved to **1.139**,
which changed only the seminar pathways; the graph content is the same as 1.138.

I applied the draft in memory to live 1.139 with a throwaway script that mirrors
`apply_person_entries.transform`. It adds the node, `node_id` on `cole_harris`, one new person
(`val_napoleon`), 8 new sources, 1 addendum, seven edges (`edge_993`–`edge_999`), two roster
`edge_id`s, one linked roster addition and one unlinked roster addition. Results:

- **Errors:** 0.
- **Warnings:** 8, against 7 in the unmodified graph. The one new warning is "Repeated
  endpoint/type combination" on edge 3: edges 2 and 3 both run `cole_harris → spatialhistory`.
  Edge 3 was optional; it is excluded from the 1.140 release.
- **Size:** 180 nodes, 999 edges.
- **Together with the Perry packet:** still 0 errors and the same single new warning (181 nodes,
  1,003 edges).

The two packets share one source record, `pe139_perry_forum_2016`, which is identical in both.
The applier keeps one copy, so either packet can be applied alone.

## What is proposed

- **Node `cole_harris`.** The twelve standard person keys. The date label lists dated works, from
  The Seigneurial System (1966) to A Bounded Land (2020).
- **`people_update`.** The existing record (identity note "Local author identity") gets
  `node_id: cole_harris`.
- **Wikidata.** Q5142660 is checked and found correct. `data/people-wikidata.json` already holds
  it from the bulk roster match of 2026-09-22.
- **New person `val_napoleon`.** Her row on `indigenous` is a critic row with no `edge_id`. The
  validator requires a roster row's edge to join that person's own entry and the group, so the
  row cannot be linked to edge 7. This is the same pattern as Ouellet's critics.

### Edges

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | → settler_colonialism | contribution | Geographical dispossession in British Columbia, 1997–2004 | dispossession_reserves_geography | yes (historian) |
| 2 | → spatialhistory | contribution | Colonialism's geographies, 1997–2003 | extension05_harris_native_space_2002 | yes (historian) |
| 3 | → spatialhistory (excluded at release) | contribution | Historical Atlas of Canada, vol. 1, 1987 | none (note) | no |
| 4 | → native_newcomer | critique | Harris: cultural enrichment questioned, 1997–98 | none (note) | new row (historian) |
| 5 | → post | critique | Harris: culture overweighted in colonial-discourse studies, 2003–04 | none (note) | no |
| 6 | foucault → | influence | Sovereign and disciplinary power, 1997–2004 | person target | no |
| 7 | indigenous → (released) | critique | Napoleon: a settler perspective, 2004 | person target | Napoleon row, unlinked |

Notes on individual edges:

- **Edge 4** targets the entry, not the `indigenous_actors_in_trade` strand. That strand also
  holds Ray, whom the critique does not name, and the 1.136 review warned against strand
  addresses broader than a critique.
- **Edge 5** targets `post` as a whole, because the 2004 abstract criticises "the colonial
  discourse literature" without naming Said. Harris also cites Said approvingly (1997–98,
  p. 59 n. 39).
- **Edge 7** begins by naming its proxy. It is one review, not a verdict of the field.

## What was read

**His own words**
- "Social Power and Cultural Change in Pre-Colonial British Columbia" (BC Studies 115/116,
  1997/98). Read closely at pp. 45–47, 56–60, 68–70 and 80–82; the rest skimmed. This is the
  in-period critique of Fisher and the "cultural enrichment hypothesis".
- "Revisiting the Native Land Question" (BC Studies 138/139, 2003, pp. 137–163), read in full:
  - his précis of Making Native Space;
  - Jo-Anne Fiske's commentary;
  - Gordon Gibson's commentary (Fraser Institute; a policy commentator, not used as a scholarly
    critic);
  - Harris's reply.
- The 2004 Annals abstract, read verbatim via OpenAlex. The article body is closed. CiteSeerX
  redirected to an empty Wayback page.

**Reception, read in full**
- MacDonald on the Atlas (Manitoba History 20, 1990). Web text with no page numbers; it is the
  only witness to the Atlas preface.
- Loo on The Resettlement of British Columbia (BC Studies 117, 1998).
- Clayton's guest editorial on Making Native Space (BC Studies 138/139, 2003).
- Val Napoleon on Making Native Space (BC Studies 141, 2004). Page heads were checked in the
  issue's review PDF.

**Later reading.** Perry's 2016 reply in the BC Studies forum on Colonial Relations (p. 112).

## What could not be read

- **His books.** The Seigneurial System, the Atlas, The Resettlement of British Columbia, Making
  Native Space and A Bounded Land. Quotations from them come through Loo, Clayton, Napoleon and
  MacDonald, with their page references.
- **Native Studies Review 16:2 (2005), "Appraising Cole Harris' Making Native Space".** The
  contributors are Carlson, Carter, McPherson and Murton, with a response by Harris.
  - The University of Saskatchewan PDF returns 404, and there is no Wayback capture.
  - A search-engine snippet says the CHA panel behind it was organised by Robin Brownlie and
    Adele Perry. That is not used as evidence.
- **Canadian Geographer 47:1 (2003) review symposium.** Wiley, closed. Known only through
  Napoleon's summary, which is attributed to her.
- **His 1994 Ethnohistory article on smallpox and the 1977 and 1991 Annals essays.** Known through
  Clayton's notes.
- **"Regionalism and the Canadian Archipelago" (1982).** Not located.
- **Schreiber, "Glaciers Listen" (BC Studies 159, 2008).** Downloaded but not used.

## Faults avoided (from the 1.136 and 1.138 reviews)

- **No PhD counts in text.** They are in `citation_evidence` only.
- **Qualifications kept:**
  - "needs to be approached very cautiously";
  - "There is good evidence for all of these developments";
  - "anything but passive victims";
  - "several theoretical perspectives yield crucial insights";
  - Napoleon's praise alongside her criticism.
- **Clayton's characterisation is marked as his.** Harris is "neither a close student … nor a
  slavish follower" (Clayton's paraphrase), and the "suspicion of an international postcolonial
  literature" is likewise Clayton's wording.
- **No founding claims.** The Atlas is credited as collaborative. The texts read do not cite Wolfe,
  so edge 1 says that no derivation from Wolfe is established by the texts checked.
- **Roster rows.** Only two existing rows are linked, settler_colonialism and spatialhistory,
  each matching its described intervention. The indigenous and cdn_regional rows are not linked.
- **Group-to-person critique (edge 7).** It names its proxy in the first sentence of the
  evidence.

## Open questions for the editor

1. Keep edge 3 (the Atlas) as a separate arrow, or merge it into edge 2? Keeping it adds one
   validator warning.
2. Keep edge 7 (indigenous → cole_harris, Napoleon)? The alternative is to keep her as a critic
   row only.
3. Should the Native Studies Review forum (2005) be pursued? Carter and Carlson have atlas people
   records. It would give a stronger critic set than one review.
4. Edge 4 could also be answered by Fisher. His 1992 second edition of Contact and Conflict is
   cited by Perry (1995). Was there a reply to Harris after 1997? Not checked.
