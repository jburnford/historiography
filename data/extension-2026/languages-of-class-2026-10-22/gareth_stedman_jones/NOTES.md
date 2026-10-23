# gareth_stedman_jones: draft notes (revision 1.152, not applied)

- **Source of the draft:** `../evidence-stedman-jones.md` §§0–2 (Foster 1985, Epstein 1986) and `../evidence-stedman-jones-part2.md` §§3–12 and P.1–P.8, used as written. Posts and dates are carried at the standing the research gave them (institution pages as cited by Wikipedia, not seen; the Berkeley Townsend page and the Columbia author note read).
- **Wikidata:** Q5522975, checked by QLever SPARQL on 2026-10-22 (exact label match; P569 1942-12-17; historian; QMUL employer; VIAF 29679542). The people record `gareth_stedman_jones` already exists (label only), so `people_update.new` is false and the applier only sets `node_id`; the identity note in the draft is for the reviewer and must be entered by hand (see the README's "Left out").
- **Layer:** `historians`, as for `joan_wallach_scott`, `bryan_d_palmer` and `ep_thompson` on the same pathway; the research proposed `intellectual_connections`, which the live graph uses for theorists (Foucault, Derrida, Latour, Wood).

**Edges (11 incident: 10 new, plus edge_200 revised)**

| id | edge | kind | standing |
|---|---|---|---|
| edge_200 (revised) | → language | contribution, target `language/class_political_idioms` | the Introduction pp. 19–22 as quoted by Foster and Epstein (both read in full); was historyworkshop ↔ language (comparison) |
| locA_rel_02 | → labourhistory | contribution, target `labourhistory/class_experience` | NLR 1975 read in full; 1974 essay via Epstein |
| locA_rel_03 | → historyworkshop | contribution, target `historyworkshop/language` | Epstein p. 207 read; collective membership unconfirmed |
| locA_rel_04 | → political | contribution, target `political/popular_radicalism` | LoC pages as quoted by Epstein and Foster; Kirk pp. 3–4 read |
| locA_rel_05 | → marx | critique, target `marx/language_class` | NLR 1975 read; Epstein p. 208; the Marx book through two readers |
| locA_rel_06 | → intellectualhistory | contribution | publisher and Cambridge Core pages; Samalin read; Kirk n. 6 read |
| locA_rel_07 | → ep_thompson | critique | LoC p. 101 as quoted by Foster; Kirk nn. 5, 8 read |
| locA_rel_08 | ep_thompson → | influence | Foster and Kirk read |
| locA_rel_09 | joan_wallach_scott → | critique | ILWCH 31 editors' remarks read in full; Scott's text unread beyond p. 1; Eley–Nield n. 20 |
| locA_rel_10 | debate → | critique (Foster, Gray, Epstein, Kirk) | on the debate draft |
| locA_rel_11 | → debate | contribution | on the debate draft; linked to his roster row |

- **locA_rel_01 is not a new edge.** Agent A's P.8 option (a) is followed: edge_200 keeps its id and takes locA_rel_01's source, kind, text and sources; a second gareth_stedman_jones → language arrow would have repeated the endpoint pair.
- **Not drawn:** bryan_d_palmer → gareth_stedman_jones (deferred by A: the book unread); jon_lawrence → gareth_stedman_jones (held: the 1993 reply unread by A or B).
- **Roster additions:** `political` (historian, linked to locA_rel_04) and `labourhistory` (historian, linked to locA_rel_02). The existing rows on `language`, `historyworkshop` and `marx` are amended by the batch (text_revisions and roster_list_additions): the `language` works string loses its read-status remark and its context takes the p. 22 programme; the `historyworkshop` role becomes `contributor` (not `historian`, since founding-collective membership is unconfirmed); the `marx` row gains the 1975 review.
- **Strands joined** (batch): `marx/language_class` gains Foster and Epstein and a sentence saying the essays do not address Dorothy Thompson directly; `historyworkshop/language` and `chartist_language_class` gain the reviewers' sources; `language/class_political_idioms` is rewritten.
- **Chronology:** 26 events, 1971–2025 (A's 24 less the birth, the 1974 King's fellowship and the 2013 FBA events — no source record lawfully carries the first and last, and the fellowship date rests on institution pages not seen (Sol review finding 12); the FBA stays in the identity note from Wikidata P166 — plus the 1997 Lüdtke chapter as its own event, the 2005 directorship attested by the Columbia author note, Samalin 2017 and Roberts 2019 as separate reception events (finding 13), and Gurney 2025). The 1991 Centre foundation is a context event from the Harvard Gazette, which does not name him; the Queen Mary appointment is undated.
- **Sol review fixes (2026-10-22):** local "as quoted by" attributions on locA_rel_04, 07 and 09 and on edge_200 (finding 5); the three institutional events above (12); the split reviews (13). `loc_townsend_bio` is no longer created (its only use was the withheld 1974 event); the scope note records the Berkeley page's reading. See `../release/fixes-1.152.md`.
- **Changes to the research text:** none of substance. Kirk's n. 5 wording ("treats Thompson's 'experience' as subjectivist") is paraphrased, not quoted, since the note was read in an OCR of a scan.
