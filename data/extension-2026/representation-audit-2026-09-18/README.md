# Representation audit: women in the graph (18 September 2026)

Answer to the question "which women have we missed in this graph?" against `historiography-1920-2000.json` (116 entries, 829 shared people, 752 edges). **Research staging only.** Nothing in the production graph, site or authority sheet was changed. Prepared by Fable 5.1; this is a discovery input for the [representation review](../../../REPRESENTATION-REVIEW.md), not an accepted demographic record.

## Method

Gender values are Wikidata `P21` (sex or gender) statements, retrieved 18 September 2026. No gender was inferred from names, photographs or subject specialisms. Three evidence tiers, recorded per person in the `basis` column of `roster_gender_audit.csv`:

| basis | people | meaning |
| --- | ---: | --- |
| `accepted_qid` | 42 | QIDs already accepted in `data/people-wikidata.json` (people with their own atlas entry). |
| `name_match_qid_unreviewed` | 356 | Candidate QIDs from `data/wikidata/historians-qlever-2026-09-17/atlas-name-match-candidates.csv`. **Unreviewed name matches, not authority reconciliations.** Where a person has several candidates, all their P21 values are joined with `/`. |
| `label_consensus_N` | 258 | For roster people with no candidate, an exact English-label match against Wikidata humans (`P31 = Q5`) with a P21 value. N is the number of homonyms; all N carry the same value. Identity is **not** established; a single homonym is weak evidence, 26 homonyms (Mary Douglas) is weaker. |
| `label_mixed_N` | 4 | Homonyms disagree. Unresolved: Harry Collins, Wang Feng, Chandler Davis; Judith Butler carries both female and non-binary values in Wikidata and must not be forced into a binary tally. |
| `no_wikidata_match` | 169 | No candidate and no exact label match. Includes e.g. Caroline Walker Bynum, Sherry B. Ortner, Sonya O. Rose, Francesca Bray. Absence of a match does not mean absence from Wikidata; many atlas labels carry initials or disambiguators. |

Endpoints: the first five P21 batches (`raw/values_0..4.txt`) were run through the WikidataMCP SPARQL tool before the user directed a switch to QLever; batch six and the label match ran against `https://qlever.dev/api/wikidata` (label query sent by POST, `raw/labelmatch.rq`). Two QLever rows lack an English label and carry the item URI; Q6581097 = male and Q6581072 = female per the labelled rows.

Footprints (`roster_footprint.csv`) count distinct entries in which a person appears in `representative_people` and in `strands[].person_ids`. Edge degree is counted only for the 43 person entries, because edges connect entries, not roster people.

## Headline counts

| Stage | Women | Men | Unknown / mixed |
| --- | ---: | ---: | ---: |
| Person entries (43) | 13 | 30 | 0 |
| Roster people (829) | 162 (161 female, 1 trans woman) | 493 | 174 |
| Person occurrences across the 73 topic entries (1,369) | 313 | 808 | 248 |
| Edges touching a woman's entry (of 752) | 97 | | |
| Reviewed external candidates (118, `ranking/editorial-review/reviewed-all.csv`) | 10 | 108 | 0 |
| Visibility top 1000 (`ranking/ranked-top-1000.csv`) | 97 (96 female, 1 trans woman) | 903 | 0 |

Median edge degree: women's entries 8, men's entries 9. The 13 women with entries are as connected as the men; the gap is in who has an entry at all. The 13 are Pinchbeck, Clark, Beard, Spruill, Salmon, Flexner, Tuchman, Power, Wedgwood, Yates, Cam, Dorothy Thompson, Torr: all roots figures or British Marxist history. No woman active mainly after 1960 has an entry.

## Findings

1. **High-footprint roster women with no entry and therefore no edges** (see `summary-lists.txt`, "roster women by footprint"): Joan Wallach Scott (8 representative + 7 strand entries, more than any woman with an entry), Dolores Hayden, Natalie Zemon Davis, Jackie Huggins, Amanda Vickery, Sally Alexander, Michelle Perrot, Janaki Nair, Anna Clark, Lynn Hunt, Ute Frevert, Ann Laura Stoler, Deborah Gray White, Dharma Kumar, Barbara Taylor, Louise Tilly, Silvia Rivera Cusicanqui, Elizabeth Fox-Genovese, Catherine Hall, Gerda Lerner, Joanna Bourke, Sheila Rowbotham, Darlene Clark Hine, Leonore Davidoff, Luisa Passerini, Susan Stryker. Label-consensus tier adds Rita Huggins, Julie Cruikshank, Belinda Bozzoli, Evelyn Brooks Higginbotham, Doreen Massey, Carroll Smith-Rosenberg, Carolyn Merchant, Gayatri Spivak, Kimberlé Crenshaw, Linda Tuhiwai Smith.
2. **Eleven topic entries have no woman among representative people or strands** (`summary-tallies.txt`): durkheim, anticolonial, ssk, epistemology, historicism, historicalecon, modern, wartradition, nationaltradition, economictheory, global. Annales has 1 of 20; philhistory 1 of 40; economic 8 of 54. Fields where women are a majority of named people: women, gender, identity, historyworkshop, indigenous, black.
3. **Women absent from the graph entirely** (`top1000_nonmale.csv`, `atlas_match` empty): among them Hannah Arendt (only woman in the reviewed priority band), Romila Thapar, Laurel Thatcher Ulrich, Gertrude Himmelfarb, Mona Ozouf, Sheila Fitzpatrick, Nell Irvin Painter, Ida Blom, Yvonne Hirdman, Anna Pankratova, Lucy Dawidowicz, Deborah Lipstadt, Élisabeth Roudinesco, Linda Nochlin, Lisa Jardine, Averil Cameron, Patricia Crone, Annette Gordon-Reed, Deirdre McCloskey. Frances Yates appears unmatched only because the atlas label is "Frances A. Yates". The visibility ranking is a discovery input, not an importance measure; many of its women are novelists, journalists or public figures whose occupation statement needs review.

## Limits

- 174 roster people have no usable gender value; 169 have no Wikidata match under the current label. Counts above are therefore lower bounds for both women and men.
- Roster-tier identities are unreviewed. Before any of this feeds a batch, accept or reject the QID per person (the `sibling`/`person-disambig` procedures apply) and record the source of the P21 value.
- Wikidata P21 is a public structured claim, not self-identification; retain the value and scope, and prefer nonbinary or trans values as recorded rather than collapsing them.
- This audit compares stages and fields, as the review requires. It does not propose a target ratio, and a name here is a lead, not authority to create an entry or an influence edge.

## Files

- `roster_gender_audit.csv`: one row per roster person: `person_id, label, gender_wikidata, basis, has_node, rep_entries, strand_entries, entries`.
- `roster_footprint.csv`: footprint counts without gender.
- `top1000_nonmale.csv`: non-male people in the visibility top 1000 with rank, dates, description, atlas match, relevance screen.
- `summary-lists.txt`, `summary-tallies.txt`: printed analysis outputs, including the per-entry tally and the 169 unmatched labels.
- `raw/`: exact VALUES batches, raw P21 results (`gender_mcp.txt`, `gender_q5.tsv`), the label-match query and response, QID maps (`node_qids.json`, `roster_qids.json`, `qid_batches.json`) and the unmatched roster list.
