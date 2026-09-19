# Gender-history / LOD integration pilot

Research cutoff: 18 September 2026. **Staging only; no production graph, authority merge or browser change.** This is a bounded integration exercise, not a completed survey of gender history through 2026.

## Result

The packet uses the existing `ontology/contract.json` directly: **five people, seven works, eight publications, two versions, 37 proposed claims**. Seven claims propose interpretive connections; the rest concern authorship, bibliography and a catalogue subject. All remain `needs_review`. Three people reuse existing shared identities (Scott, Davis and Stryker); Ghosh and Najmabadi are local research candidates. Four external identity mappings remain unresolved.

Seven recent Scott/Davis catalogue records now have explicit role/type review notes. Three have publisher metadata corroboration; four have only the saved catalogue inspection. None is an accepted Sudoc manifestation merge. Raw records and original role URIs are preserved.

## Substantive findings and limits

| Contribution | Proposed significance | Evidence actually inspected |
| --- | --- | --- |
| Joan Wallach Scott, *Gender: Still a Useful Category of Analysis?* (2010) | Keeps gender analysis focused on how categories acquire historical meaning; does not declare a new school. | [Author abstract on SAGE](https://journals.sagepub.com/doi/10.1177/0392192110369316), not full article. |
| Scott, *Sex and Secularism* (2017) | Explicitly adopts genealogy to investigate secularism and questions a necessary connection between secularization and gender equality. | [Publisher’s introduction](https://assets.press.princeton.edu/chapters/i11126.pdf), selected printed pp. 3–7. This establishes Scott’s programme, not the correctness or reception of all its claims. |
| Durba Ghosh, *Sex and the Family in Colonial India* (2006) | Connects family, racial distinctions and gendered archival silences in colonial South Asia. | [Author’s 2022 retrospective](https://cambridgeblog.org/2022/05/sex-and-the-family-in-colonial-india-the-making-of-empire/) and [Cornell profile](https://history.cornell.edu/durba-ghosh). The retrospective date must not redate the original contribution. Book passages and reception remain to read. |
| Afsaneh Najmabadi, *Professing Selves* (publisher release December 2013) | A historically situated Iranian case combining history and ethnography; a useful check against assuming a single US-centered trans chronology. | [Duke description and metadata](https://dukeupress.edu/professing-selves), not book passages. This is a proposed reading direction, not a verified cross-author critique. |
| Susan Stryker, *Transgender History* (2008; revised 2017 and 2026) | A separately addressable trans-history contribution with an edition history, rather than three unrelated new works. | [Author bibliography](https://www.susanstryker.net/writing), [2017 publisher listing](https://www.littlebrown.co.uk/titles/susan-stryker/transgender-history-second-edition/9781580056892/) and [2026 listing](https://www.hachettebookgroup.com/titles/susan-stryker/transgender-history-third-edition/9781541605886/?lens=seal-press). Author reports February 2026 release; revised content not collated. |

Scott’s institutional biography supplies a direct gender-history connection that the LOD discovery route missed. This is stronger than deriving specialism from subjects assigned to her books. The current `gender` atlas entry combines gender and racial formation; it is not identical to a single gender-history concept. Trans history remains a distinct research candidate, already linked to the user’s discovery queue.

Two other works test the limits of extending a person’s classification to all their writing: Scott’s [*On the Judgment of History* (2020)](https://cup.columbia.edu/book/on-the-judgment-of-history/9780231551908/) and Davis’s [*Listening to the Languages of the People* (2022)](https://www.aup.nl/en/book/9789633865934/listening-to-the-languages-of-the-people). The packet adds bibliographic proposals, not automatic gender-history assignments. Davis is an identity/publication control, not an assertion that this particular work represents a new gender-history development.

## What the seven recent LOD records become

| Sudoc record | Review outcome |
| --- | --- |
| 271458526 — Scott, *Psychoanalysis and History* (2022) | Publisher confirms a co-edited issue of *History of the Present*, not a sole-authored Scott monograph. Component contributions need their own identities. |
| 256830967 — Scott, *On the Judgment of History* (2020) | Publisher corroborates work-level identification; exact catalogue manifestation remains pending. |
| 263655423 — Scott, *In the Name of History* (2020) | Retain as a separate catalogue lead. Do not merge with *On the Judgment of History* on subject or lecture overlap. |
| 261615114 — Davis, *Le retour de Martin Guerre* (2022) | Reissue/composite-edition lead; catalogue also names Dumas and Ginzburg. Component identities and credits unresolved. |
| 26222738X — Louise Labé, *Œuvres* (2022) | Davis foreword credit; not authorship of the whole work. |
| 277050014 — Davis, *Listening to the Languages of the People* (2022) | Publisher corroborates work identification and year; exact manifestation merge remains pending. |
| 252657071 — *Early Modern Cultural Studies* (2020–) | Continuing series with Davis on its editorial board; not a new Davis book. |

## Chronology checks

- Duke’s December 2013 release for *Professing Selves* and JSTOR’s 2014 copyright remain separate source observations. The packet proposes a 2013 publication year following Duke; it does not infer two distinct works or pretend all manifestation dates are reconciled.
- Cambridge’s 2014 online frontmatter date is separate from Ghosh’s 2006 print publication.
- Stryker’s third-edition publisher page retains preorder wording alongside its 3 February 2026 date. The author’s explicit report of February release provides an additional witness. It does not establish the extent or reception of the revisions.

## Combining the schemas without losing meaning

`schema-crosswalk.json` inventories every record in the two older research packets: **19 works, 19 consulted witnesses labelled publications, 20 claims and all their citation joins**. It is a mapping audit, not a conversion falsely described as complete.

The new batch demonstrates a shared model for supported predicates. The older packets still require two deliberate design decisions:

1. A consulted publisher page or extracted PDF is a **source witness**, not automatically an issued publication. Preserve its hash and locator while identifying the publication it describes.
2. Contract 0.1 lacks exact relations for several critique, revision, contribution, qualification and programme claims. Do not flatten these to `research_connection`. Their original text, participants, compound strand addresses, histories and citation joins remain in the unchanged source packets.

Scott’s introduction also supplies a concrete next predicate-design case: her stated disagreement with Charles Taylor (pp. 5–6), distinguished from her use of genealogy and stated agreement with Asad. These remain reading/design leads rather than silently invented influence or critique edges.

## Coverage and next action

The gender entry’s three time bins now say `partial_pilot_review`; its overall outcome remains pending. This packet covers selected English-accessible Euro-Atlantic, Indian and Iranian cases. It does not cover the whole racial-formation umbrella, establish representative global coverage, or finish any field through 2026. African, Latin American, East Asian, Indigenous and original-language surveys, masculinity histories, broader feminist debates and independent reception remain outstanding.

Next: extend the common claim vocabulary against the preserved critique/contribution examples; perform precision-aware authority reconciliation; read the proposed works beyond metadata; and undertake a broader field survey. Then apply the same workflow to less-developed fields such as borderlands and disability history. Economic-history holdings remain valuable detailed research, but their volume must not control overview prominence or the order of coverage reviews.

## Files and checks

- `batch.json`: ontology-compatible research packet, blocked from production export.
- `schema-crosswalk.json`: complete inventory of older packet mappings and unresolved semantics.
- `raw/`: saved web-tool search/extraction outputs, not original HTML or full-book readings.
- `manifest.json`: hashes of the packet, evidence captures, common contract, validator and consulted LOD exports.
- Run `python3 scripts/validate_gender_integration.py` and `python3 -m unittest discover -s tests -p 'test_gender_integration.py'`.

Checks cover the common contract, source hashes, catalogue preservation, legacy identities, mapping coverage, scoped evidence and unchanged graph/browser hashes. Tests reject subject-to-specialism conversion, changed contribution credits, silent authority acceptance and umbrella-to-field equivalence. These checks certify structure and preservation, not scholarly truth. The known original LOD provenance/date-precision defects remain pending; no full raw-cache replay was possible from this Git checkout.
