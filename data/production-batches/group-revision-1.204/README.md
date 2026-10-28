# Revision 1.204: edge review of the Indigenous person entries

The user asked for research agents "to review the edges more carefully" (28 October 2026). The trigger was evidence that Winona Wheeler engages settler colonial studies, which the graph didn't show. Three agents re-read the sources behind every relationship of the twelve entries added or backfilled in 1.201. Their [brief](data/extension-2026/indigenous-edge-review-2026-10-28/BRIEF.md) applies the OCAP and source-provenance rules. Their reviews (`review-{A,B,C}.md`) became the guarded fragments merged here. Only stage-1 items are encoded, meaning those resting on passages read with locators; 30 items are held for stage 2.

The graph contains **368 entries, 2,195 relationships, 3,250 sources and 1,438 indexed people**.

**Settler colonialism.**
- Wheeler adopts Wolfe's definition in Henning & Wheeler 2021 (DOI 10.1002/ss.20365). This gives a new Wolfe → Wheeler influence and a Wheeler row on `settler_colonialism`. Her earlier frames (internal colonialism, "intellectual colonialism", anti-colonial research) are named in her description.
- McCallum's settler-colonialism row now cites Williams's reading of her work "Following Wolfe".
- Innes frames the 1880s deaths as "colonial genocide", so his critique of Daschuk (edge_2153) moves to `native_newcomer/reserves_schools_state`.
- Simpson's and Coulthard's settler-colonialism relationships now point at `recognition_refusal_resurgence`, and Trask's at `indigenous_scholars_critique` (Kauanui's reading).
- No read text shows any of these scholars criticising Wolfe or the field. That claim is not made.

**Corrections.**
- Coulthard's dissertation page references were one page high in five relationships, his scope note and the source note.
- Andersen's "hybrid off-shoot of two races" quotation is aimed at John Ralston Saul (p. 6), not at fur-trade historians. The relationship is reworded from pp. 5 and 10–11.
- Wheeler's entry called her a co-founder of Shekon Neechie. She sits on its managing board; the relationship now rests on her own statements of 2000, 2001 and 2010.
- *When the Other Is Me* is dated 2010 (first printing), not 2011.
- McCallum's 2017 *CHR* source links its DOI instead of a ResearchGate copy.
- The Smith *Decolonizing Methodologies* citation names the publisher record, not the excluded copy it named before.

**New relationships (20).**
- **LaRocque (6):** her critiques of postcolonial theory, Sioui's autohistory, Mandelbaum's ethnography and fur-trade national-economy history; plus Fanon's and Dickason's influence on her.
- **Wheeler (6):** Wolfe, postcolonial theory, L. T. Smith and Deloria to Wheeler; and Wheeler to institutional criticism and to oral-tradition transmission models.
- **Andersen:** a critique of Great Lakes ethnohistory, worded as resting on the 2011 abstract and p. 13; a critique of Charles Taylor; Bourdieu's influence on him.
- **Coulthard:** influences from Deloria, Howard Adams and Cole Harris.
- **Macdougall:** to `indigenous/peoplehood`.
- **McCallum:** a critique of how Indigenous–newcomer history frames Indigenous work, resting on two reviewers.

**Reroutes and timelines.**
- LaRocque's critique of Trigger moves to `native_newcomer/historians_indian`.
- edge_1003 now leaves from LaRocque, not from the field.
- edge_750 now leaves from *Life Lived Like a Story* into `ethnohistory/collaboration_authority`.
- *Life Lived Like a Story* records the 1992 CHA best scholarly book prize as the CHA lists it ("Julia A. Cruikshank"), with a note that the entry credits Sidney, Smith, Ned and Cruikshank together.
- McNickle's timeline gains his 1966 Regina appointment; McNickle's relationship to the field (edge_775) is reworded to his own argument.

**Provenance.** Removing the excluded scan host from the Smith citation required a guarded edit, so the old citation stays in the batch input and the acceptance record as the prior value. It appears in no published field.

**Test fix.** `tests/test_site_core.mjs` still pinned the Indigenous family at its pre-split size, which failed the view tests on GitHub for 1.201–1.203. The pins are updated to 79 approaches, 133 people and 23 approaches in `indigenous`, and the Carlson search finds two Stó:lō strands.

**1.204 status: publication authorised by the user ("you should also push the indigenous update").**
- Locally: the 61 view tests pass. The 73 browser cases pass; one person-map case timed out while a dissertation extraction loaded the machine, and passes when run alone.
- `--check` rebuilds 1.204 exactly.
- The 180-test data suite was still running locally at push time, so GitHub's run confirms it.

- **Inputs:** `data/extension-2026/indigenous-edge-review-2026-10-28/` (reviews A–C, fragments A–C, `er-{A,B,C}/entry-draft.json`), merged by `merge_fragments.py` into `batch.json`; packet `release/editorial-additions.json`; baseline 1.203 (`drafts/historiography-1920-2000.v1.203.json`).
- **Check:** `python3 scripts/apply_person_entries.py data/extension-2026/indigenous-edge-review-2026-10-28 --check`.
