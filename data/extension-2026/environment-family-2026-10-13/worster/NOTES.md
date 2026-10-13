# Donald Worster: person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). It was applied in
memory to the 1.130 graph: the node, `node_id`, eight new sources, one addendum, one edge and
one roster `edge_id`. With those changes it passes `validate_graph` with no new errors or
warnings (0 errors and 7 warnings before and after).

## What is proposed

- **Node `donald_worster`.** A person entry with the twelve standard person keys. The date
  label is *Nature's Economy 1977 · Dust Bowl 1979 · Rivers of Empire 1985 · 'Transformations of
  the Earth' 1990 · coverage through 2000*.
- **`people_update`.** The existing `donald_worster` record gets `node_id: donald_worster`.
- **Edge 1 (the only edge).** `donald_worster → environment`, contribution. Its target strand
  is `environment/agriculture_capitalism` and its roster row is `environment`.
  - **Claim.** The three levels of environmental history (nature, modes of production,
    ideas), with the capitalist transformation of agriculture as the middle level.
- **Sources.**
  - Eight new: `pe131_worster_ends_1988`, `_jah_1990`, `_wealth_1993`, `_rivers_1985`,
    `_natures_economy_1977`, `_merchant_1990`, `_cronon_1992` and `_hennessey_1987`.
  - One addendum: `worster_dust_bowl`.
  - Three reused: `worster_dust_bowl`, `worster_dirty_thirties` and
    `mcdean_dust_historiography`.
- **Merge at release.** Two sources duplicate records in sibling packets:
  - `pe131_worster_merchant_1990` is the same article as `pe131_merchant_jah_1990`;
  - `pe131_worster_cronon_1992` is the same article as `pe131_cronon_place_stories_1992`.

  The brief's ID rule made separate IDs necessary. Keep one record of each.

## The framework in his own words

The three levels, from "Doing Environmental History" (1988), checked against the 1988 edition:

- "There are three levels on which the new history proceeds, three clusters of issues it
  addresses".
- "The first deals with understanding nature itself, as organized and functioning in past times".
- "The second level in this history brings in the socioeconomic realm as it interacts with the
  environment. Here we are concerned with tools and work, with the social relations that grow
  out of that work, with the various modes people have devised of producing goods from natural
  resources".
- The third is "the purely mental or intellectual, in which perceptions, ethics, laws, myths, and
  other structures of meaning become part of an individual's or group's dialogue with nature".
- Together they "constitute a single dynamic inquiry".

**Page.** Running heads in the 1988 edition place the passage between pp. 292 and 294, and
Isenberg (2013) cites p. 293. The exact page break was not seen.

**Isenberg misquotes one phrase.** He gives "as it interacts with nature"; the 1988 text reads
"with the environment".

**The 1990 essay** (English wording from the 1993 reprint):
- He writes that "most environmental historians seem to have settled philosophically on a
  position that is at once materialist and idealist".
- He then turns to "that middle level, the analysis of modes of production as ecological
  phenomena". Isenberg gives JAH p. 1091 for both quotations.
- He proposes that "the single most important task" in modern agroecology is "to trace what
  Karl Polanyi has called 'the great transformation'".

## Verification: what was read

| Source | Check | Supports |
| --- | --- | --- |
| `pe131_worster_ends_1988` | Abridged reprint in the Merchant reader (reader pp. 2–9). Wording and running heads checked by full-text search of the 1988 edition (archive.org `endsofearthpersp0000unse`, lending-restricted, snippets only) | Three levels; Leopold; "born out of a moral purpose" |
| `pe131_worster_jah_1990` | Crossref metadata only. The English JAH text was unreachable (OUP 403; JSTOR bot challenge). Whole essay read in Portuguese translation | Identity and the round-table structure |
| `pe131_worster_wealth_1993` | Full-text search snippets of Worster's 1993 reprint (`wealthofnatureen00wors`). Contents, index and running heads seen in snippets; page images not seen | The 1990 English wording; note 5 on p. 226 |
| `pe131_worster_merchant_1990` | Author-hosted JSTOR scan, OCR'd. p. 1117 read closely, pp. 1120–1121 read | The levels as "a significant framework"; "lacks a gender analysis"; the fourth level, reproduction |
| `pe131_worster_cronon_1992` | Author-hosted PDF. pp. 1347–1349 and 1363–1364 read | Dust Bowl pp. 4–5 quoted; capitalism as "chief agent"; "apocalyptic prophecy"; Indians peripheral |
| `pe131_worster_hennessey_1987` | Review read in full (online, no print pagination) | Rivers of Empire quoted at pp. 4, 7, 130 and 206; the Wittfogel revision |
| `pe131_worster_rivers_1985`, `pe131_worster_natures_economy_1977` | Full-text search snippets and contents only | "modern hydraulic society"; "arcadian" and "imperial" traditions |
| `worster_dust_bowl` (addendum) | Full-text search of the 1979 edition (`dustbowl00dona`) | Wording of the p. 4 and p. 5 passages that Cronon quotes |

**Not read.**
- The English JAH pages of 1990.
- Worster's reply, "Seeing Beyond Culture" (JAH 76:4, 1142–1147).
- The White, Cronon, Crosby and Pyne responses. White's and Cronon's objections are known only
  through Isenberg (2013), a later reading.
- White 1985.
- The full books.

**Later readings.** These are labelled as later readings in the edge text and do not carry it:
- Isenberg (2013), read;
- McNeill (2003, p. 37), read: "The most cogent was probably the one elaborated in slightly
  different versions by both Donald Worster and Arthur McEvoy", but such theories "have sparked
  no groundswells of enthusiasm".

**Founder claims.** The draft makes none.
- Worster grounds the idea in Leopold's "ecological interpretation of history".
- McEvoy's ecology, production and cognition triad appeared in the same 1988 volume.
- The only "founder" wording seen is the translator's note to the Portuguese translation (2002):
  "um dos fundadores". That is not Worster's text, and it is not used.

## Edges: reasoning

- **→ environment, `agriculture_capitalism`.**
  - **Why this strand.** It holds Worster alone and states the Dust Bowl thesis. The 1990
    essay's middle level is the same argument generalised.
  - **No strand for the framework.** No strand states the three-level model itself. At release
    the editor could add one ("three levels: nature, production, cognition") holding Worster,
    Merchant's fourth level and McEvoy.
- **Not proposed.**
  - **→ economic.** No evidence that economic historians took the argument up. `edge_267`
    already compares.
  - **→ technology.** Rivers of Empire is a power-and-state argument (Wittfogel revised), and
    no checked text places it in the history of technology.
  - **→ science.** This is the strongest of the alternatives. Merchant (1990) credits "his
    account of the changing history of ecological ideas", and Cronon (1993) says Merchant
    "joined Worster in bringing an environmentalist perspective to the history of science".
    It is not proposed for three reasons:
    - Nature's Economy was checked only by snippets;
    - there is no science roster row;
    - there is no strand for the history of ecology.
  - **→ geography.** He uses Hewes; that is not a contribution to geography.
  - **→ annales.** See below. That passage is evidence for `edge_111`, not for a person edge.

## Annales passage (for edge_111)

**Found in English, in Worster's own reprint. The JAH 1990 page was not reached.**

The text is note 5 to "Transformations of the Earth" as reprinted in *The Wealth of Nature*
(Oxford University Press, 1993), Notes, **p. 226** (chapter 4, n. 5). The JAH note is also n. 5.
The Portuguese translation numbers it n. 5 as well, and its wording matches.

Assembled from overlapping full-text-search snippets of the archive.org copy
(`wealthofnatureen00wors`). Each joint was confirmed by an overlapping snippet; the citation
fields between "American" and "Pacific Historical Review" were not all seen:

> 5. The best effort to trace the emergence of the field, at least in one influential part of
> the world, is Richard White, "American Environmental History: The Development of a New
> Historical Field," Pacific Historical Review, 54 (Aug. 1985), 297–335. White argues that the
> study of frontier and western history has been the formative influence on this field. Another
> important source of ideas, quite removed from the influence of Frederick Jackson Turner, has
> been French historians and geographers, particularly Fernand Braudel, Lucien Febvre, and
> Emmanuel Le Roy Ladurie, all associated with the journal Annales.

**How p. 226 was established.**
- The running head "226 Notes" falls inside the end of chapter 3's notes (before n. 32).
- "Notes 227" falls immediately before chapter 4's n. 9.
- So chapter 4's notes 1–8, including n. 5, are on p. 226.
- Page images were not seen.

**Corrections to the earlier gloss.**
- In canon-evidence-international.md (item C), "realmente retirada da influência" was glossed
  as "well removed from". The English is "**quite removed from** the influence of Frederick
  Jackson Turner".
- The subject of the sentence is "French historians and geographers". The translation's "a dos
  historiadores" adds "that of".

**For quotation in the atlas.**
- **Recommended citation.** Worster, *The Wealth of Nature* (1993), 226 n. 5, reprinting JAH 76
  (1990), n. 5.
- **The JAH page is not checked.** Since the essay opens at p. 1087 with Leopold and notes 1–5
  come early, the note probably falls on pp. 1088–1089. This is an inference only; do not
  print it.
- **Revisions not checked.** Whether the 1993 reprint revised the note was not checked. Its
  wording matches the 2002 Portuguese translation of the JAH text point for point. That is
  good but not conclusive evidence of identity.

**What the passage says, for `edge_111`.**
- Worster reports White's view that frontier and western history was "the formative
  influence".
- He adds the Annales historians and geographers as "another important source of ideas".
- That supports "an influence on the field's ideas", in Worster's 1990 words. It does not
  support a founding lineage, and it should sit beside McNeill's and Massard-Guilbaud's
  objections as already summarised in canon-evidence-international.md.

**A related lead, not followed.** The 1993 notes to the same chapter (p. 228) cite Georges
Bertrand, "Pour une histoire écologique de la France rurale". This was seen in a search snippet
only.

## Wikidata Q1240502: the right person

Checked with the MCP tools `search_items` and `get_statements`.
- **Search result.** Semantic search returns Q1240502 first.
- **Library of Congress.** LoC n84043788 gives "Worster, Donald, 1941-" and cites *Nature's
  economy*. It records Kansas, Brandeis, Yale and Hawaii.
- **Open Library.** Author OL718022A holds all five books used here.
- **Existing record.** `people-wikidata.json` already has Q1240502 from the unreviewed bulk
  match; this check reviews it.
- **Statement not used.** Wikidata's field of work "history of China" is not used.

## Citation evidence (metadata only)

These figures are kept out of node and edge text.
- **cited-people.csv.** 52 strict-corpus dissertations (53 overall).
- **Top work.** RECOMMENDATION.md gives Rivers of Empire as the most-cited work (15). It was not
  recounted here.

## Open questions for the editor

1. **Strand.** Should a three-level framework strand be added to `environment` at release? If
   so, the edge could target it instead of `agriculture_capitalism`.
2. **Roster context.** Should the `environment` roster row's context be widened beyond the Dust
   Bowl to mention the three levels?
3. **Merges.** Merge the duplicate Merchant 1990 and Cronon 1992 source records with the
   sibling packets.
4. **Science edge.** Is a `→ science` edge for Nature's Economy wanted? If so, the book needs a
   proper reading (archive.org borrow), not snippets.
5. **JAH page for n. 5.** Needs library access to the JAH PDF (JSTOR 2936586).

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 9.** Edge 1 quotes Isenberg (2013) and McNeill (2003) as later readings; both are
  now in its `source_ids` under the canonical merged ids `pe131_crosby_isenberg_2013` and
  `pe131_extras_mcneill_2003`. McNeill's qualifier "probably" is restored (p. 37, re-checked in
  the text-layer PDF).
- **Finding 5 (`edge_111`).** The English wording of note 5 above was assembled from joined
  archive.org search snippets. `edge_111` now paraphrases it in English and quotes the
  Portuguese translation (read in full) verbatim; p. 226 is marked as inferred from running
  heads. A re-try of the archive.org full-text search on 2026-10-13 returned 403, so the
  English wording could not be re-checked.
