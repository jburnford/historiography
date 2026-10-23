# Revision 1.152 packet: The languages of class debate (draft, not applied)

**Reviewed.** Sol's cross-model review (`sol-review-1.152.md`: accept with fixes, 15 findings) was applied to the drafts and batch on 2026-10-22, and the packet was rebuilt. Each change is listed in `fixes-1.152.md`.

- **Revision:** 1.152; baseline 1.151 (live graph, sha256 `ea17d68d…`).
- **Date:** 2026-10-22.
- **batch_dir:** `group-revision-1.152`.
- **Packet:** `release/editorial-additions.json` (sha256 `a234bce7…`; the pre-review build was `97b4158f…`), built by `scripts/apply_person_entries.py … --build` from `../batch.json` and the five drafts `../languages_of_class/`, `../gareth_stedman_jones/`, `../patrick_joyce/`, `../james_vernon/` and `../jon_lawrence/`. Each draft has its own `entry-draft.json` and `NOTES.md`. The research files (`../evidence-*.md`, `../BRIEF.md`, `../pathway-proposal.json`) are untouched.
- **What has not been done:** no git commands, no site or evidence-layer build, no edits to the graph, docs or `seminar-pathways.json`, no email to any service, nothing written to `data/people-wikidata.json`. The pathway rework itself (`../pathway-proposal.json`) is a separate step after acceptance.

## Contents

| item | count |
|---|---|
| New entries | 5: `languages_of_class` (group, Debate); `gareth_stedman_jones`, `patrick_joyce`, `james_vernon`, `jon_lawrence` (persons, layer `historians`) |
| New edges | 51: 26 contribution, 18 critique, 4 influence, 3 comparison (agent A 10, B 28, C 13). New ids would be edge_1158–edge_1208 |
| Edges into or out of the debate | 21: 9 in (persons), 5 critiques out to persons, 7 to fields |
| Edge revisions | 5: edge_200 (re-sourced to Stedman Jones, kept id, comparison → contribution), edge_920 and edge_921 (Temple page; no excluded route named), edge_1127 (body of Scott 2000 and the Eley–Nield reply), edge_314 (Scott's texts added) |
| Debate strands | 12 (from 15 proposed; see the debate NOTES for the merges) |
| Debate roster | 47 rows (17 historian, 17 critic, 12 contributor, 1 precursor); 9 linked to edges |
| Debate chronology | 50 events, 1963–2022 |
| Stedman Jones | 11 incident edges (10 new + edge_200), 26 events |
| Joyce | 13 edges, 25 events |
| Vernon | 10 edges, 18 events |
| Lawrence | 9 edges, 21 events |
| New sources | 136 (81 supporting_page_checked, 49 bibliographic_metadata_checked, 6 not_checked); 14 without a URL (no lawful page found) |
| Source addenda | 3: `w2_scott_class_lost_2000` (body read), `languages_class`, `kirk_defence_class` |
| Source field corrections | 9 (`source_field_sets`): `joyce_visions`, `stedman_chartism_primary`, `pe132_chandavarkar_1997` notes; `cdnsrc_palmer_1990` url and note; `thompson_making_preface` url, title, citation and note (course-site transcription replaced by the Penguin Modern Classics page) |
| New people records | 24 (22 in the debate draft; Vernon and Lawrence through their drafts) |
| Roster rows on existing entries | 15: Stedman Jones on political, labourhistory; Joyce on social, political, culture, urbanhistory, labourhistory; Vernon on political, language, social, global; Lawrence on political, language, social, labourhistory |
| Roster row amendments | 11 `text_revisions` (language rows for Stedman Jones, Joyce, Palmer; historyworkshop row role and context; strand focus/works for `social/eley_nield_politics`, `marx/language_class`, `language/class_political_idioms`) and 7 `roster_list_additions` |
| Strand list additions | 5; new strand 1: `political/new_political_history` |

## Validation

Re-run on 2026-10-22 after the review fixes, with a scratch script that imports `scripts.apply_person_entries` (`Batch(...).transform(before, packet)`) and `scripts.validate_graph.validate(graph, pathways_within(graph, pathways))`; nothing was written.

- **Baseline 1.151:** 0 errors, 12 warnings (10 repeated endpoint/type combinations, plus the unconnected `digital_history` and `web_history`); 195 nodes, 1,157 edges, 2,121 sources, 1,285 people.
- **Result 1.152: 0 errors, 12 warnings — the same 12**, before and after the fixes. No new warning: every new source is used; no new edge repeats an endpoint pair and type (checked against the whole result graph); every `target_strand` resolves; every roster `edge_id` connects its person and entry; no revised or new edge or source names an Internet Archive borrow copy or any other excluded route.
- **Result graph:** 200 nodes, 1,208 edges, 2,257 sources, 1,309 people. Incident edges and events: the debate 21 and 50; Stedman Jones 11 and 26; Joyce 13 and 25; Vernon 10 and 18; Lawrence 9 and 21.
- After the revisions: edge_200 is `gareth_stedman_jones → language`, connection/contribution, directed; `w2_scott_class_lost_2000`, `languages_class` and `kirk_defence_class` are `supporting_page_checked`; `cdnsrc_palmer_1990` carries the Temple University Press URL; `thompson_making_preface` carries the Penguin page (fetched 2026-10-22: ISBN 9780141976952, paperback 2013).
- `python3 -m unittest tests.test_apply_person_entries_fields tests.test_graph_validation tests.test_people_validation tests.test_chronology`: 30 tests, OK (4.9 s).

To apply after review (not done):

```
python3 scripts/apply_person_entries.py data/extension-2026/languages-of-class-2026-10-22
python3 scripts/apply_person_entries.py data/extension-2026/languages-of-class-2026-10-22 --check
```

## Judgement calls

1. **edge_200 is locA_rel_01.** Agent A's option (a) is followed: the arrow keeps its id, its source becomes the person entry, and it changes from a movement–umbrella comparison to the author's contribution, with Foster's and Epstein's readings of the Introduction. A second `gareth_stedman_jones → language` arrow would have repeated the pair; none is drawn. The History Workshop relation is now `gareth_stedman_jones → historyworkshop` (locA_rel_03) and the roster role there becomes `contributor`.
2. **Layer `historians`** for the four persons, as for Scott, Palmer and Thompson on the same pathway; the research proposed `intellectual_connections`, which the live graph uses for theorists.
3. **Strands: 15 → 12.** The baseline (Johnson, Ruskin, Anderson) is merged into the 1982–83 strand; the British first critics and the 1987 ILWCH forum are one round; South Asia is merged with Africa and Latin America on Eley and Nield's own grouping (2000, n. 2). The other regional strands stay distinct from the British rounds. No existing strand is moved.
4. **Debate edge pattern.** Persons contribute to the debate; its named critics are drawn from it to the person they answer; the spread runs from the debate to fields. Palmer → debate is a contribution, not C's critique, because edge_920 and edge_921 already carry his critiques. The debate → Scott arrow names only critics without arrows of their own (Stansell, Sangster, Eley and Nield), so that Palmer → Scott (edge_920) and Valverde → Scott (edge_967) are not drawn twice; after review, debate → Lawrence likewise carries only Purdue and Goldthorpe, Vernon's 1999 review staying on `james_vernon → jon_lawrence`. No new edge repeats a live pair.
5. **Nine of agent C's arrows could not be drawn** because their sources (Sangster, Rancière, Sewell, Canning, Cooper, James, Eley, Nield, Bergquist) are people records, not entries; their words sit on roster rows and in strands, and the field arrows carry the spread.
6. **Three drafting additions** (locB_rel_30–32: Joyce, Vernon, Lawrence → debate) were built from agent B's read evidence so that each person on the pathway has a roster row linked to an arrow; their notes say so.
7. **Held or dropped edges (11)** are listed in the debate draft's `edges_considered_not_proposed`: B's four HELD edges, C's weak bielefeld comparison, Chandavarkar → Chakrabarty (not an entry; reading route flagged), Scott → Thompson (ch. 4 unread; edge_314 strengthened instead), A's deferred Palmer → Stedman Jones, Joyce → Hobsbawm.
8. **Lawrence–Taylor 1993** is one of the user's named rounds; neither agent could read it (Taylor & Francis 403), so it is dated and named but no arrow to Stedman Jones is drawn.
9. **Sources dropped on provenance grounds:** Harman's 1980 review (a Marxists Internet Archive transcription), Renaud's self-reposted H-Net review, the QMUL 2013 page (404), and — after review — the inherited course-site transcription of Thompson's preface is replaced by the publisher's page (the earlier reading record is preserved in the note; new text quotes the preface only through named readers). The Anderson row rests on the Verso page and Bergquist's quotation; the 2013 FBA stays in the identity note (Wikidata P166) rather than as an event.
10. **Birth events and undated posts are not drawn** (no source record carries them; no live person entry has a birth event); after review the 1974 King's fellowship is withheld, the Centre's 1991 foundation is separated from the directorship attested in 2005, and the Queen Mary appointment is undated.
11. **`chronology.editorial_record`** on all five entries points to `data/production-batches/group-revision-1.152/acceptance.json`, as every live entry does, because the applier does not set it.
12. **`coverage.reviewed_through: 2000`**, with the selected later reception retained in the text dated individually through 2022 (Sol review finding 14), following the 1.145 precedent.

## Flags for the reviewer

- **Quotations to re-verify word for word.** Chapter openings read through Cambridge's chapter summaries as indexed by OpenAlex (Visions of the People introduction and chs 3, 4, 14; Democratic Subjects; Speaking for the People chs 1–5, 9; Sewell 1980 ch. 1); the Küster 2005 review (fetch summary with German quotations); OCRed scans (ILWCH editors' remarks 1983, 1984, 1987; Rancière's 1984 reply; Salvatore's deposit; Kirk pp. 2–5 and 44–47); the Cannadine–Joyce letters, the Reviews in History pages, Tilly, Sangster, Cooper, Scott 2000, Eley and Nield 2000 and the 2007 preface (text layers or page fetches). Every quotation from Languages of Class, Politics and the People, Resistance and Integration and Anderson 1980 is "as quoted by" a named reader and marked so in every field where it appears (Sol review finding 5).
- **Unread books whose theses are carried from publisher pages or readers:** Languages of Class (pp. 7–22, 93–174 as quoted by Foster, Epstein, Kirk); Descent into Discourse (Temple page; Callinicos); Visions of the People, Democratic Subjects, Politics and the People, Speaking for the People, The Rule of Freedom, The State of Freedom, Hunger, Distant Strangers (bodies); Work and Revolution in France; Working-Class Formation; Languages of Labor and Gender; The Origins of Industrial Capitalism in India and Imperial Power and Popular Politics; Resistance and Integration; The Future of Class in History (body); Dorothy Thompson's The Chartists; Cannadine's December 1992 review (known through Joyce's letter).
- **The Social History paywall.** Every Taylor & Francis page returned 403: the whole 1992–96 exchange (Mayfield–Thorne ×2, Lawrence–Taylor, Joyce's note and 'The End of Social History?', Vernon 1994, Kirk 1994, Eley–Nield 1995, Steinberg 1996), Gray 1986 and Cooper 1995 are dated and placed by title, abstract or later readers only. A library copy of Social History 17–21 would settle the second British round.
- **The Chandavarkar provenance flag.** `pe132_chandavarkar_1997` was read (2026-10-14) on a non-publisher host; its note is corrected (host name removed, re-verification on OUP pending, the earlier record preserved inside it), the essay is named in the debate strand and Chandavarkar's row with no quotation (Sol review finding 1), and the person-to-person critique is held. edge_916 and the Chakrabarty entry still carry the earlier quotations.
- **Thompson's preface.** The inherited `thompson_making_preface` record linked a course-site transcription; the batch replaces the link with the Penguin Modern Classics page (which does not reproduce the preface) and records that the reading was made earlier. The preface has not been re-read through an eligible route; edge_924's quotations stand on the earlier record.
- **Ungrounded or probable people:** ungrounded — Foster, Gray, Mayfield, Thorne, Steinberg, Bergquist (and, existing, Nield, Epstein, Kirk); probable — Miles Taylor (Q29034157), Andrew Miles (Q50229713), Daniel James (Q5217668). Vernon (Q30122046), Lawrence (Q107232879), Stedman Jones (Q5522975) and Joyce (Q7146880) were checked with QLever SPARQL; the WikidataMCP endpoint was down all session. Nothing is written to `data/people-wikidata.json`.
- **Attributions by inference:** the 1984 ILWCH editors' remarks are attributed to David Montgomery from the initials "D.M." and his editorship; the 1987 remarks to Helmut Gruber from "H. G."; the Thatcher chapter's co-authorship with Sutcliffe-Braithwaite rests on the chapter opening.
- **Scott 2000** was read in a Cambridge PDF that was accessible this session though not labelled open access; the addendum says so.
- **Strand targets with a loose fit:** `social/collective` for Lawrence's community work and `culture/foucault_model` for Joyce's cultural history remain; the Vernon targets `global/nation_narratives` and `culture/foucault_model` were removed after review (finding 15).
- **Stedman Jones's posts** (Cambridge lecturer, reader, professor; Queen Mary) rest on institution pages as cited by Wikipedia and not seen; only the Columbia author note (directorship, 2005) and the Berkeley Townsend page (NLR board, undated) were read. The 1974 King's fellowship is withheld; his NLR board years and HWJ founding-collective membership are not asserted.
- **Hostile characterisations** (Eley and Nield's "most viciously" of Palmer; Tilly's "softcore solipsism"; Scott's "Assent to Discourse"; Cannadine's caricature of Joyce) are recorded as the readers' words wherever used.

## Left out

- **Identity notes the applier cannot write.** `gareth_stedman_jones` (Q5522975) and `patrick_joyce` (Q7146880) are existing label-only records: the batch sets their `node_id` only; the notes drafted in `people_update.identity_note` must be entered by hand. Likewise agent B's and C's QIDs for existing records: `david_cannadine` Q4382556, `geoff_eley` Q1036755, `neville_kirk` Q56996996 (probable), `james_epstein` Q83422387 (probable), `joy_parr` Q28064772, `gregory_s_kealey` Q5607005, `sonya_rose` Q20675662, `anna_clark` Q112479129 (probable), `laura_lee_downs` Q64627027 (its record now says "not grounded"), and a note for `keith_nield` (no Wikidata item).
- **Scope-note updates to `dorothy_thompson` and `ep_thompson`** (agent A, P.8 7–8: The Chartist Experience printed the first version of the essay; the 1983 critique of "experience") — possible through `field_sets` but not done here; the facts are on the debate strand and locA_rel_07/08.
- **The Stone–Joyce exchange** ('History and Post-Modernism', Past & Present 131–135, 1991–92): no `lawrence_stone` node or source exists; dated as an event on Joyce's entry only.
- **Rows on `labourhistory` for Chandavarkar and Viotti da Costa** and the 1992 collection on the `catherine_hall` entry (agent C, optional).
- **edge_920's 2021 sources** stay in its list, labelled as later readings, rather than being removed.
- **Richard Biernacki, Barbara Weinstein, Belinda Bozzoli, Aristide Zolberg, Christopher H. Johnson, Michael Hanagan, Lenard Berlanstein, Donald Reid, Thomas Welskopp, Richard Johnson:** no rows or records; named in strand text or source records only.
- **Brief corrections noted by the agents** (the wrong DOI for Joyce 1995; the HWJ 2014 title; no "making of the working class" chapter in Chandavarkar 1998) are applied in the source records; the brief itself is unchanged.
- **A re-reading of Thompson's preface through an eligible route** (Sol review finding 2): the link is corrected, but the preface was not re-read; edge_924 is untouched.
- **The pathway rework** (`../pathway-proposal.json`): not part of this packet.
