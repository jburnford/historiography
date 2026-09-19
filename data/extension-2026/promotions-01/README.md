# First pre-2000 promotion proposals

Prepared 18 September 2026 (America/Regina). **Eight concrete node drafts, seven distinct works, and eighteen historical relationship proposals.** All remain `needs_review`; zero production imports. This is a bounded response to the representation audit, not a complete remedy or a ranking of the eight most important women.

The selection follows contributions already represented in the atlas, across biography, social explanation, cultural history, Black history, Indigenous research authority and history of science as well as gender history. Existing roster frequency helps locate evidence; it does not establish importance. No gender classifications or new QIDs are accepted here.

| Proposed node | Selected intervention | Concrete relationship and evidence scope |
| --- | --- | --- |
| Joan Wallach Scott | “Gender” (1986) | Gender as historical analysis; separately attributed uses of Foucault and Rosaldo. Selected pp. 1067–1068. |
| Natalie Zemon Davis | *Women on the Margins* (1995) | Comparative biography across religious and colonial settings. New check is the book description; body-text check remains open. |
| Lynn Hunt | Introduction to *The New Cultural History* (1989) | Cultural interpretation within social history; qualified criticism of the priority given to social experience. Introduction pp. 1–5. |
| Catherine Hall | *Family Fortunes*, with Davidoff (1987) | Gender, family and middle-class formation. Indexed publisher prologue abstract; later-edition witness. |
| Leonore Davidoff | *Family Fortunes*, with Hall (1987) | Equal credit for the same argument and work, also addressable from the gender/class strand. Same abstract, not independent corroboration. |
| Evelyn Brooks Higginbotham | “The Metalanguage of Race” (1992) | Race in historical explanation; criticism of insufficient racial analysis in feminist theory; acknowledged feedback from Hine and Smith-Rosenberg. Selected pp. 251–253. |
| Linda Tuhiwai Smith | *Decolonizing Methodologies* (1999) | Indigenous research authority; explicit use of Collins’s outsider-within formulation. Introduction pp. 1–5. |
| Lorraine Daston | “The Image of Objectivity,” with Galison (1992) | Historical forms of scientific objectivity; both authors retain contribution credit. Complete scope paragraph on p. 81 and opening paragraph on p. 82. |

Fourteen historical claims have selected-passage checks, three have an abstract check, and one has a description check. These are checks on particular claims, not whole books or independent confirmations. The total of **35 claims** also includes nine authorship credits and eight proposed entry/person presentation links; it must not be reported as 35 historical relationships.

## Reviewable files

- [Node drafts](node-proposals.json): actual legacy-format node fields, stable person/node IDs, work and claim references, and every existing roster/strand context preserved verbatim.
- [Historical relationships](relationship-proposals.json): all eighteen proposals, with direction, attribution, exact evidence locator, check scope, qualification and review history inherited from the canonical claims.
- [Research packet](batch.json): contract 0.2 entities, first-class works, source witnesses and citation-bearing claims. Work metadata records the original intervention year; it does not equate it with a later edition or a field’s origin.
- [Outstanding checks](remaining-checks.json): concrete unresolved readings, identities and next selection priorities.
- [Evidence](raw/): web captures and selected primary PDF pages with companion OCR. [PDF observations](raw/pdf-observations.json) record original download hashes and page mappings. Full downloaded PDFs are temporary; the selected witnesses needed for review are retained.
- [Manifest](manifest.json): hashes of inputs, code, evidence and outputs. Existing packets and frozen ontology 0.1 files remain unchanged.

`node-proposals.json` is a review artifact, not a file for direct browser import. The validator checks an in-memory node-only overlay for legal fields and references, but does not manufacture legacy edges from the richer research relationships. The eight drafts therefore do not yet appear in the public graph.

## What this exercises

Work identity is shared across authors and contexts: Hall and Davidoff resolve to one *Family Fortunes*, and Daston and Galison to one joint article. Claims attach to people, works and compound strand addresses independently of teaching-node promotion. Rosaldo, Hine and Smith-Rosenberg can contribute to the research graph without receiving full nodes in this batch. Collins is a newly named local person candidate, with authority reconciliation still open.

The claim vocabulary preserves different acts. Hunt qualifies an explanatory priority; Higginbotham critiques insufficient racial analysis; Smith proposes a research programme. Acknowledged manuscript feedback is distinct from coauthorship or endorsement. Dates identify interventions, with `valid_time: null`; the drafts do not invent career endpoints or move field origins to a publication year.

Preserve existing `edge_313` and `edge_314`. They already distinguish productive inheritance from feminist criticism of Thompson. Scott’s full node is not permission to copy every group-level criticism onto her, and Higginbotham’s citation of Scott or Butler does not automatically make either a personal target of criticism.

## Reading limits and next work

The *Family Fortunes* abstract was exposed by a search-indexed publisher result; direct opening returned only page furniture. It supports a bounded proposal but does not establish that every word matches the original edition. Routledge identifies the original 1987 publication separately from the 2019 third edition and Hall’s new introduction. Davis’s Fulcrum record lists a 1997 manifestation; the separately captured copyright/printing information distinguishes the 1995 work. No imaginary prologue conversation is treated as a historical meeting.

Hunt’s fresh check covers her own introduction, not the entire edited volume or her 1984 book. Some Daston/Galison extracted lines were truncated; only the complete named paragraphs support these proposals. Higginbotham’s initial extraction also clipped words, so it was replaced for claim checking by raster OCR of complete pages. OCR remains fallible; the selected PDFs allow inspection. Scott p. 1067, Higginbotham p. 252 and Smith pp. 2–5 were also checked visually.

This batch is still concentrated in accessible English-language work. It does not resolve the eleven fields with no provisionally woman-classified roster figures, the full 65-name user cohort, geographic gaps, or post-2000 coverage. Continue with the remaining Black, Indigenous, postcolonial, economic, labour and other contributions rather than deepening these eight careers indefinitely. Barbara Fields, explicitly discussed by Higginbotham on p. 253, is a further identity/work discovery lead; no accepted match or edge was fabricated here.

## Reproduction and checks

Run from the repository root:

```sh
python3 scripts/build_promotion_batch.py
python3 scripts/validate_promotion_batch.py
python3 -m unittest tests.test_promotion_batch
```

The builder is offline and refuses a changed production baseline. It writes only this staging packet. Validation checks the research contract, shared authorship, compound targets, citation-level checks, preservation of original contexts, concrete node fields, and unchanged production/browser hashes. Nine tests cover loss of contexts/coauthors, invalid targets, overstated check scope, mistaken validity intervals, node-independent claims and rejection of production export. Structural checks cannot establish the historical truth of a proposal.
