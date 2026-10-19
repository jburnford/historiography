# Revision 1.145 packet: Capitalism, divergence and industrialisation (draft, not applied)

**Reviewed.** Sol's cross-model review (`sol-review-1.145.md`: accept with fixes, 14 findings) was applied to the drafts and batch on 2026-10-18, and the packet was rebuilt. Each change is listed in `fixes-1.145.md`; the wording checks are in `quote-verification-1.145.md`.

- **Revision:** 1.145; baseline 1.144 (live graph, sha256 `45d28864…818a`).
- **Date:** 2026-10-18.
- **batch_dir:** `group-revision-1.145`.
- **Packet:** `release/editorial-additions.json` (sha256 `8981f0550d05085ca67a99fc59be86f609a2ea69ea6b1ab6bf14b4ede78b61d6`; the pre-review build was `a64b5696…af7d`), built by `scripts/apply_person_entries.py … --build` from `../batch.json` and the three drafts `../capitalismdebates/`, `../robert_brenner/` and `../ellen_meiksins_wood/`. Each draft has its own `entry-draft.json` and `NOTES.md`.
- **What has not been done:** no git commands, no edits to the graph, docs or site, and no email sent to any service.

## Contents

| item | count |
|---|---|
| New entries | 3: `capitalismdebates` (group, Debate), `robert_brenner`, `ellen_meiksins_wood` (persons) |
| New edges | 34: 20 contribution, 9 critique, 5 influence (cd_rel_gd2 became a contribution after review). New ids would be edge_1075–edge_1108 |
| Edges into or out of the debate | 21: 19 new, plus edge_1050 and edge_407 moved to it |
| Edge revisions | 4: edge_1050 and edge_407 (source moved to the debate, notes extended); edge_478 (Sweezy now read in full); edge_899 (one sentence) |
| Debate strands | 11, covering all five components |
| Debate roster | 60 rows; 6 linked to edges |
| Debate chronology | 45 events |
| Brenner | 14 edges, 15 dated events |
| Wood | 6 edges, 12 dated events |
| New sources | 83 (`cd_` 44, `rb_` 24, `ctpm_` 15); `cd_tpm_economist_2014` was added after review |
| Source addenda | 5 |
| New people records | 35 (33 plus Brenner and Wood) |
| Roster rows on existing entries | 8: Brenner on economic, marx, dependency, annales, historicalsociology, global; Wood on karl, marx |
| Strand list additions | 4 |
| Strand focus revisions | 2 |
| Source field corrections | 1: `williams_capitalism_primary` url, via the new batch key `source_field_sets` (personal-site PDF replaced by the UNC Press page) |

## Validation

Re-run on 2026-10-18 after the review fixes. The rebuilt packet was transformed in memory against the live 1.144 graph (sha256 unchanged, `45d28864…818a`). Nothing was written. The check used the same `transform` and `validate` the applier uses, through a scratch script that writes no files.

- **Result: 0 errors, 12 warnings**, the same as before the fixes. These are the same 12 as the 1.144 baseline: 10 repeated endpoint/type combinations that already exist, plus the unconnected `digital_history` and `web_history`. No new warning: every new source is used, no new edge repeats an endpoint pair and type, and every roster `edge_id` connects its person and entry.
- **Result graph:** 191 nodes, 1,108 edges, 1,970 sources (one more than before review: `cd_tpm_economist_2014`), 1,280 people. Brenner has 14 incident edges and 15 events, Wood 6 and 12, the debate 21 and 45.
- `williams_capitalism_primary` carries the UNC Press URL in the result graph. `tests/test_apply_person_entries_fields.py` passes (7 tests).

To apply after review (not done):

```
python3 scripts/apply_person_entries.py data/extension-2026/capitalism-debate-2026-10-18
python3 scripts/apply_person_entries.py data/extension-2026/capitalism-debate-2026-10-18 --check
```

## Judgement calls

1. **edge_1050 and the Brenner arrow.**
   - edge_1050 (critics of Pomeranz) moves from `economic` to `capitalismdebates`, keeping its id.
   - Brenner and Isett are removed from it and drawn once, as rb_rel_09 `robert_brenner → kenneth_pomeranz` (moderate).
   - Mokyr (2002) and Vries (2009) are added to edge_1050 as named critics.
   - Nothing is drawn twice. The Huang–Pomeranz edges 1043 and 1044 are untouched.
   - edge_407 (Drescher on Williams) moves from `economic` to the debate in the same way.
2. **No strands moved.** The related field strands are listed in the debate's scope note and in its strands' `works`. This includes economic's divergence, coal and slavery-productivity strands. edge_1042's target strand is unchanged.
3. **Roster rows.** A person who appears in several components has one merged row (Frank, Brenner, Mokyr, Allen, Pomeranz, Engerman). Toynbee's role is `precursor`.
4. **Debate edge pattern.** Fields and persons contribute to the debate, and named critics are drawn from it to the person they answer, as in `sciencewars`. Pomeranz → debate (cd_rel_gd2) was first drawn as a critique built on his replies to Huang. After review it is a contribution: his 2011 reassessment of divergence timing, as reported by Vries (moderate). The replies to Huang stay on edges 1043–1044.
5. **The component-3 split.** The three strands (`ir_concept_revision`, `protoindustry_industrious`, `why_britain`) are used instead of one long strand.
6. **Optional items.** They are included only where strong. karl → Brenner (rb_rel_11) is in. These are out: Pomeranz → Brenner (rb_rel_10), debate → global, labourhistory → debate, the high-wage critique arrow, and the English Revolution strand.
7. **Deferred person entries.** Mokyr, Wrigley, de Vries, Wong, Allen and Beckert have roster rows only, per instruction. Their component edges run from the fields: demography, consumption and technology hold the Wrigley, de Vries and Mokyr arrows for now. When those entries are made in the next packet, cd_rel_ci3, ci4 and ci5 should be revisited.

## Flags for the reviewer

- **Brenner's 1976 article (decided).** Sol retained the reading as evidence.
  - The source record links only the official DOI, which is now also in its citation.
  - Its note records the actual procedure: whole article OCRed; pp. 30–34, 42–43, 47, 53, 56, 61–62 and 71–75 read closely; the rest searched and skimmed; cross-checked against another copy.
  - The course and Internet Archive copy is named as provenance only, with no link.
- **Bois's "political Marxism" and "a voluntarist vision of history" (1985 reprint pp. 115–116).** These are known only through Wikipedia and Callinicos (1990), and are now attributed to both by name wherever used.
- **WebFetch extractions (checked).** NYRB 1984, Griffin 2010 (Internet Archive capture), the CUP blog quoting the 2013 *NYT* article, and MPR on *The Economist* were matched word for word by direct page fetch on 2026-10-18.
  - Talking Points Memo (5 September 2014) was read and added as a second witness for the Economist episode.
  - The Griffin URL stays the review page: the IHR PDF returned 403 and has no archive capture.
  - The CUP page splits the Levy quotation; mark the omission if it is ever displayed.
- **`williams_capitalism_primary` (corrected).** The personal-site PDF link is replaced by the UNC Press page through `source_field_sets`; the reading note is unchanged.
  - uncpress.org returns 403 to scripted requests; an Internet Archive capture of the page exists (2025).
- **`chronology.editorial_record`.** All three entries point to `data/production-batches/group-revision-1.145/acceptance.json`, following every live entry and the 1.144 drafts, because the applier does not set it. See `fixes-1.145.md` finding 14.
- **People records:** QIDs for Bois (probable), Wunder, Klíma and Aston are noted from the Brenner research but were not re-checked. Brenner (Q329922) and Wood (Q434183) were re-checked with the WikidataMCP tools. None is written to `data/people-wikidata.json`.
- **Reviewed:** Sol's cross-model review is in `sol-review-1.145.md`; all 14 findings are applied or explained in `fixes-1.145.md`.

## Left out

- Person entries for Mokyr, Wrigley, de Vries, Wong, Allen and Beckert (next packet).
- The optional strand `english_revolution_social_interpretation`.
- Roster rows proposed in the research as optional: Merrington, Debin Ma, Seth Rockman, David Eltis, Morgan Kelly, Cormac Ó Gráda, Gregory Clark. They are named in strand text or edge notes only.
- Brenner packet roster tweaks to existing rows: Postan on `economic`, Le Roy Ladurie on `annales`, and the J. P. Cooper identity note. The applier cannot edit people identity notes, and the row tweaks were optional.
- The 1.144 component of the Pomeranz scope note was not revised; it remains accurate.
