# Fixes to the 1.140 packet after Sol's review

Date: 2026-10-14. Review: [sol-review-1.140.md](sol-review-1.140.md) (accept with fixes).

The fixes were made in the drafts and `batch.json`. The frozen
[editorial-additions.json](editorial-additions.json) was then rebuilt with
`python3 scripts/apply_person_entries.py data/extension-2026/canadian-persons-tier2-2026-10-14 --build`.
Neither the release file nor the atlas JSON was edited by hand. The packet has not been applied.

## Validation (release 1.139 → 1.140, in memory)

The check ran `Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`:

| | Errors | Warnings | Nodes | Edges |
| --- | --- | --- | --- | --- |
| Live 1.139, unmodified | 0 | 7 | 179 | 992 |
| 1.140 packet before fixes | 0 | 7 (same) | 187 | 1,023 |
| 1.140 packet after fixes | 0 | 7 (same; no new warnings) | 187 | 1,023 |

The packet contents:

- 8 person entries;
- 31 edges (`edge_993`–`edge_1023`);
- 65 new sources and 11 addenda;
- 3 new people and 11 roster additions;
- 11 text revisions, 5 strand-list additions and 3 roster-list additions.

The validations in each draft's NOTES.md are historical, drafting-stage checks. Each NOTES.md now says so, and each records the release decisions.

## Applier change: `roster_list_additions`

`text_revisions` changes only one string field. Finding 2 also needs `source_ids` and `works` changes on existing roster rows. `scripts/apply_person_entries.py` therefore gains an optional batch-level key:

```json
"roster_list_additions": [{"node": "...", "person_id": "...", "source_ids": ["..."], "works_append": "..."}]
```

How the key works:

- **Build.** It is copied into the packet only when present.
- **Transform.** It runs after `roster_additions`. It appends the source ids that are missing and joins `works_append` to `works` with "; ".
- **Failures.** It raises an error if the row is missing or if the works string is already listed.
- **Apply.** Its nodes are added to the `touched` set, so their prior records go into the acceptance record.

The earlier packets are unaffected:

- **Byte-identical rebuilds.** `--build` reproduces these five packets exactly: person-entries-2026-10-14b, science-studies-critique-2026-10-14/batch, canadian-persons-2026-10-14, postcolonial-persons-2026-10-14 and quebec-persons-2026-10-14. Each original was compared after the rebuild.
- **`--check` passes for all five.** The validator still reports 2, 2 and 1 errors for the reconstructed 1.134, 1.135 and 1.136 graphs. The unmodified script reports the same numbers, so these come from the current validator, not from this change.
- **Latent issue, not fixed here.** The `touched` set does not include nodes changed only by `text_revisions`, `strand_list_additions` or `new_strands`. Baseline recovery without the drafts snapshot would therefore fail for such a packet.

## Findings

### 1. Displayed PhD counts (within this batch's scope)

Two new `text_revisions` in batch.json:

- **`cdn_women_gender.scope_note`.** The clause "where 91% of its citing PhDs sit" is removed.
- **`cdn_women_gender/comparison_fur_trade_empire.focus`.** The citation ranking ("among the works most cited by this field’s PhDs") is replaced with the comparison the read texts support:
  - McPherson (2000) credits Van Kirk's research "and the critical debates it has aroused" with "bringing cultural difference and conflict into Canadian women’s history".
  - Perry (1995) traced the "scarcity model" to colonial discourse.
  - Perry also faulted fur-trade historians, Van Kirk's "brilliant account" included, for explaining mixed-race relationships by white women's absence.
  - A strand-list addition adds `pe139_vankirk_mcpherson_2000` and `pe139_perry_sick_1995` to the strand's sources.

The batch's earlier removals stand: the Van Kirk and Perry roster contexts and `transition_to_capitalism`.

Every other displayed numerical corpus claim in live 1.139 is listed, not fixed, in [phd-count-sweep-candidates.md](phd-count-sweep-candidates.md). That file has 89 snippets in 83 fields:

- 30 in node, strand and roster text;
- 59 in edge evidence notes;
- plus 4 non-numerical corpus references.

The list includes McKay's "53% of the 182" context and the political-history strands' counts ("47 PhDs", "7–12 PhDs each"). A sweep of the transformed 1.140 graph finds no new counts in the eight entries.

### 2. Roster contexts without their sources

`roster_list_additions` in batch.json:

- **`cdn_women_gender/sylvia_van_kirk`.** Adds `pe139_vankirk_reputation_1986`, `pe139_vankirk_five_families_1997` and `pe139_vankirk_mcpherson_2000`. The works gain "The Reputation of a Lady" (1986) and "Tracing the Fortunes of Five Founding Families of Victoria" (1997–98).
- **`cdn_women_gender/adele_perry`.** Adds `pe139_perry_sick_1995` and appends the 1995 essay to the works. The Perry context revision now replaces the whole context, because "(title and chapter level; after 2000)" also no longer described the evidence.

### 3. Perry's obsolete access wording

These are new `text_revisions`:

- **`settler_colonialism/adele_perry` context.** "metadata and chapter titles only" becomes a statement that her 1995 and 2001/02 essays and three in-period reviews (Carter, Orlowski, Rutherdale, 2002) are read and that the book itself is unread. Through `roster_list_additions`, the row gains those five sources and the two essays in its works.
- **`gender_family_nation.focus`.** "Metadata level only." becomes: Perry is read in her essays and in in-period reviews, the book itself unread; Carter (2008) and Jacobs (2009) remain at metadata level. A strand-list addition adds the two Perry essays to the strand's sources.

### 4. Independence from Wolfe

- **Harris rel_01.** The relationship now reads "with no derivation from Wolfe's theory established by the texts checked". The evidence opens "No derivation from Wolfe is established by the texts checked", then keeps the citation evidence (Merivale, Kymlicka, Macklem) and the roster's "earlier or beside", and notes that the books are unread.
- **Perry rel_01.** The evidence uses the same sentence and notes that the book is unread. The relationship now says the book was, in her words, inspired by an international literature on gender and colonialism, "no derivation from Wolfe's settler-colonial theory is established by the texts checked".
- **Harris NOTES.** Updated to match.

### 5. Brown's indexed excerpt

The node `scope_note`, the rel_02 evidence, and the `pe139_brown_ase_1991` verification note and scope note now say "indexed excerpt only" (OpenAlex's abstract field). Each identifies p. 113 as the recorded first page and states that the page itself was not inspected. The NOTES are updated too. The status stays `supporting_page_checked`, which GRAPH-FORMAT defines as "a relevant page or extract was consulted".

### 6. Kealey's policing edge

The `pe138_kealey_rel_04` relationship and evidence now separate three things:

1. **The checked 1992 intervention.** The documentary article's introduction (pp. 169–171) and its n. 4 on the Bulletins.
2. **The earlier notice.** The 1988 author note "is currently working on…", described as an announcement and not a checked argument. The 1984 use of the RCMP memorandum is kept.
3. **The later works.** The 1992 CHR and INS articles, Secret Service (2012) and Spying on Canadians (2017), described as "catalogue level only and not assessed here".

The edge now states that it claims the 1992 argument and the edition, not the later syntheses. The map label changes from "Political policing from 1914, 1988–2017" to "Political policing: the Cold War from 1919, 1992". The `cdn_political_national` roster-addition context is narrowed the same way.

### 7. The "provides" quotation

The saved 1992 text (session scratchpad, `kealey1992rcmp.txt`, p. 169) was checked. Its subject is the archival visit: "A RECENT ARCHIVAL VISIT to the Public Record Office … when combined with a number of Access to Information requests to the Canadian Security Intelligence Service (CSIS), provides considerable insight…". The evidence now quotes it from "when combined" with "provides" restored, and the paraphrase names the 1991 visit. The other 1992 quotations were also checked against the saved text.

### 8. Olson's Protestant sample

The rel_01 evidence separates the samples:

- the Catholic baptismal cohort of 1859 (n. 4);
- the ten-surname micro-sample, "for the Protestant population only", with the full quotation "Pour la population protestante, notre microéchantillon s’appuie sur dix patronymes" (p. 85; checked in the saved 1997 text);
- the twelve-surname sampling of the 2011 book with Thornton, as the publisher's description gives it (book unread).

`pe139_olson_peopling_2011` is added to the edge's sources.

### 9. Olson's long swings

The `suburban_building` new text is the review's wording, with plain text in place of markdown italics, since strand text carries no markdown: "Olson’s Baltimore (1980) examines city growth through boom-and-bust ‘long swings,’ with roughly eighteen years between peaks." The Olson draft's copy is synchronised; batch.json is authoritative.

### 10. Olson's date label

The label now ends "· 'Rebuilding a Neighbourhood of Montreal' (with Dufaux) 2014".

### 11. Staging language and release decisions

- **Perry rel_03.** It targets `sylvia_van_kirk`. The evidence's "Coordination … the editor may re-point it" sentence is replaced by a statement of the target and its reason. The NOTES table and bullet are marked superseded.
- **Harris rel_03.** It is excluded (`include: false`), and the NOTES record this. Rel_07 is released: "Optional:" is removed from its displayed evidence and its `include_note` records the release.
- **Kealey.** "Optional with edge 7." is removed from the `cdn_immigration_ethnicity` roster context. The NOTES record that edge 7 is released.
- **Curtis rel_02.** The displayed line "the editor may prefer comparison" is replaced by the qualification that the critique is not a rejection of quantitative work.
- **Shared Palmer review.** The source scope note now reads "Used in the Curtis and Greer entries." It no longer refers to drafts.
- **All eight NOTES.md.** Each opens with a "Release 1.140" note. The note marks the existing validation as a historical drafting-stage check, distinct from the 1.139 → 1.140 release validation above. It lists that entry's release decisions, including the resolved open questions. "This is a proposal for review only" now reads as past tense.

## Not changed

- **The chapter-2 conflict-of-interest exclusion** for Olson is unchanged.
- **PhD counts elsewhere in the graph.** The live graph's other displayed counts are listed for a separate batch, as the brief asked.
