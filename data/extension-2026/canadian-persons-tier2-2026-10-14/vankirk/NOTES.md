# Sylvia Van Kirk: person entry draft (Tier 2 Canadian persons, pe139)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- Rel_04 (LaRocque, `indigenous → sylvia_van_kirk`) is released as a named-proxy critique.
- The `cdn_women_gender` row stays a comparison row. Its PhD counts are removed and its source_ids and works gain the 1986 and 1997–98 articles and McPherson (2000) (findings 1–2, `roster_list_additions` in batch.json).
- The `comparison_fur_trade_empire` focus is rewritten from McPherson (2000) and Perry (1995), without the PhD-citation ranking (finding 1).
- Perry's critique (`pe139_perry_rel_03`) now targets this entry.

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json); its pair is
[../brown/](../brown/).

I applied both drafts in memory to the live graph, which had moved to **1.138** (Ouellet)
while I worked. The application added:
- two nodes;
- `node_id` on both people records;
- 16 new sources and one addendum (`ind126_larocque_thesis`);
- six edges, `edge_993`–`edge_998`;
- three roster `edge_id`s.

It passes `validate_graph` with **0 errors and the same 7 existing warnings** (181 nodes, 998
edges), with or without the proposed text revision. Every source id resolves and every
`target_strand` exists. A sibling Kealey draft may claim the same edge numbers; ids are
assigned at release.

## What is proposed

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | → native_newcomer | contribution | Women in fur-trade society, 1980–86 | fur_trade_families_metis | yes |
| 2 | → cdn_women_gender | contribution | Fur-trade women in women's history, 1980–98 | comparison_fur_trade_empire | yes (row role is `comparison`) |
| 3 | ↔ jennifer_s_h_brown | comparison | Paired fur-trade family studies, 1980 | none (person to person) | no |
| 4 | indigenous → Van Kirk | critique | LaRocque: description as othering, 1999 | none (person target) | no |

### The pair, without duplication

Each woman's own work goes on her own edges:
- Van Kirk: women and marriage → native_newcomer; women's history → cdn_women_gender.
- Brown: company families and Métis emergence → native_newcomer; method → ethnohistory.

The pair is drawn **once**, as the undirected comparison (rel_03). Its in-period basis is three
texts:
- Bowsfield's 1981 joint review, "using basically the same sources and employing the same
  macrobiographical approach";
- Gagan and Turner (1982), who cite both books in one note;
- Brown (1983), who takes Van Kirk's book as "another starting point".

The distinction rests on their own in-period words: women's history and race among women
(Van Kirk 1986) against matriorganization, descent and Métis emergence (Brown 1983). Brown's
2012 essay ("the Bobbsey Twins of fur trade social history ... cited in the same breath or
footnote by writers who might or might not have read our books") is a labelled later reading.

### Critique edge

Rel_04 is the atlas's first critique edge aimed at either woman. LaRocque (1999, PDF p. 249
and n. 18) criticises *Many Tender Ties* by page. She keeps her qualification that the approach
was "much improved" on "earlier racist material", and the edge quotes it. Rel_04 follows the
`edge_989` model: a group-to-person critique that names its critic.

The source is `indigenous` (strand `metis_representation_criticism`), as in `edge_868`. One
arrow is drawn, to Van Kirk, because the note's example is her book. Brown, named in the same
list, has the criticism quoted on her rel_01. LaRocque has no person entry, and a roster
`edge_id` must join the person's own entry to the group, so no roster row is linked.

### Roster rows and text revision

- **native_newcomer** (historian): "Puts women, marriage and kinship at the centre of fur-trade
  society". This matches rel_01.
- **cdn_women_gender** (comparison): the row describes the same work, and 1.136 linked Valverde's
  comparison row to a contribution edge in the same way.
  - The row's context displays PhD counts ("61% of the 61 PhDs ... lift 2.5").
  - `proposed_text_revisions` replaces them with read evidence (McPherson 2000), as 1.136 did for
    Berger.
  - The role (comparison or historian) is left to the editor.

## Verification: what was read

### Read in full
- Bowsfield, "Studies in Fur", *Archivaria* 12 (1981).
- Gagan and Turner, *Archivaria* 14 (1982).
- Van Kirk, "The Reputation of a Lady", *Manitoba History* 11 (1986). This is the society's web
  edition, which has no page numbers.
- Brown, *CJNS* 3:1 (1983), via an Internet Archive capture.
- McPherson and Fiske, *Atlantis* 25:1 (2000).
- Perry, *Left History* 13:2 (2008), a later reading, via an Internet Archive capture; the York
  site is behind a bot check.
- Brown 2012, in its 2017 open-access reprint, pp. 183–92.

### Read in part
- Van Kirk, *BC Studies* 115/116 (1997–98), pp. 149–51 only; the journal PDF breaks after
  page 7.
- LaRocque's dissertation (1999), PDF pp. 54, 249 and 250.

### Not read
- **"Many Tender Ties".** The Internet Archive copies are borrow-only and search-inside
  returned "Item not available"; the Google Books quota was exhausted. The book is quoted only
  through Bowsfield (who gives no pages) and LaRocque (pp. 101–103).
- **"Women in Between" (CHA *Historical Papers*, 1977).** It is on Érudit and was not fetched.
- **Frontiers (1984, 2002).** Closed.
- **The early-1990s critiques Perry names.** Pierson, *JWH* 1992, returned a Project MUSE
  verification page; Emberley, *Cultural Critique* 1990–91, was not found open.
- **Closed US reviews.** *PHR*, *Ethnohistory*, *Utah HQ* (1984) and *AHR* (1985).
- ***Annals of Iowa* (1984).** Behind an Anubis bot wall, which I respected.

## Wikidata

No item was found, by semantic search or by exact-label SPARQL. candidates.csv also says
`none_found`. No birth date is given.

## Open questions for the editor

1. **Rel_04.** Accept a group-to-person critique from `indigenous`, or keep the Indigenous
   critiques only at entry level (`edge_868`)?
2. **The cdn_women_gender row.** Apply the text revision? Should the role change from
   `comparison` to `historian`?
3. **The comparison_fur_trade_empire focus.** It ranks works by PhD citation ("among the works
   most cited by this field's PhDs"). It could be rewritten with McPherson (2000).
4. **International reception.** A gender or women edge would need the Frontiers 1984 article or
   the *Unequal Sisters* reprint to be read.
5. **No personal identifier was sent to any service.** The services used were the Wikidata MCP,
   Crossref and OpenAlex (repo key, no mailto), Internet Archive (metadata and Wayback), journal
   OJS sites, mhs.mb.ca, aupress.ca, the University of Manitoba MSpace and web search.
