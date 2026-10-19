# robert_brenner: draft notes (revision 1.145, not applied)

- **Source of the draft:** `../../brenner-2026-10-18/evidence-brenner.md`, sections 11.1–11.3, 11.6 and 11.8–11.9, used as re-sourced under that file's ledger. Edges come from 11.3; ctpm_rel_08 comes from `evidence-transition-political-marxism.md` §6.3.
- **Wikidata:** Q329922, re-checked on 2026-10-18 with the WikidataMCP tools `search_items` and `get_statements`. Statements seen: "American economic historian"; born 28 Nov. 1943 in New York City; employer UCLA. It is not written to `data/people-wikidata.json` in this packet.

**The user's rule:** 14 edges and 15 dated events, all on read evidence or labelled readers.

**Edges**

| id | edge | kind | strength |
|---|---|---|---|
| rb_rel_01 | → economic | contribution, target `economic/marxist` | strong |
| rb_rel_02 | → economic | critique of Postan's demographic model | strong |
| rb_rel_03 | → annales | critique, target `annales/serial` | strong |
| rb_rel_04 | → dependency | critique, target `dependency/worldsystems` | strong |
| rb_rel_06 | → marx | contribution, target `marx/transition` | strong |
| rb_rel_05 | Dobb → Brenner | influence | strong |
| rb_rel_07 | Hilton → Brenner | contribution (evidence and framing) | moderate |
| rb_rel_08 | Tawney → Brenner | contribution (evidence) | moderate |
| rb_rel_11 | karl → Brenner | influence (optional in the research; kept because it is strong) | strong |
| ctpm_rel_08 | christopher_hill → Brenner | influence (two readers; book unread) | moderate |
| rb_rel_09 | Brenner → kenneth_pomeranz | critique (body read only in a truncated repost) | moderate |

- **rb_rel_09 is the split from edge_1050.** Brenner and Isett were removed from edge_1050, and edge_1050 was moved to the debate entry, so the 2002 critique is drawn once.
- **Edges joining the debate entry,** drawn in its draft: ctpm_rel_03 (Brenner → debate) and ctpm_rel_04 (debate → Brenner, critique by named respondents).
- **Roster additions:**
  - `economic`, historian, linked to rb_rel_01;
  - `marx`, contributor, linked to rb_rel_06;
  - `dependency`, critic, linked to rb_rel_04;
  - `annales`, critic, linked to rb_rel_03;
  - `historicalsociology`, contributor, no edge;
  - `global`, critic, no edge.
- **Strands joined** (batch `strand_list_additions`): `marx/transition`, `economic/marxist`, `dependency/worldsystems`, `historicalsociology/marxian_transitions`. Focus sentences are appended to `marx/transition` and `dependency/worldsystems` (batch `text_revisions`).
- **Changes to the research text:**
  - Edge notes that referred to the withdrawn `brennerdebate` edges now point to the `capitalismdebates → robert_brenner` critique.
  - The chronology drops the `basis` and `retain` keys.
  - One reception event is added: Parthasarathi 2011, pp. 3–5, a publisher excerpt read for component 4.
- **The 1976 reading copy (decided):** the article was read in a JSTOR scan and. Sol's review retained the reading as evidence; the source record links only the official DOI (now also in its citation), and its note records the actual procedure (whole article OCRed; pp. 30–34, 42–43, 47, 53, 56, 61–62, 71–75 read closely; the rest searched and skimmed; cross-checked against another copy). See `../release/fixes-1.145.md` finding 10.
- **Sol review fixes (2026-10-18):** rb_rel_07 no longer claims an ordered Dobb–Brenner–Bois genealogy; rb_rel_08 is narrowed to entry fines; Bois's phrases are attributed to Wikipedia and Callinicos (1990); the chronology label reaches 2004 and The Economics of Global Turbulence moves to the context track; `chronology.editorial_record` added.
