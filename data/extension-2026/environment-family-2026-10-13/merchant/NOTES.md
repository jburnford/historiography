# Carolyn Merchant: person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). I applied it in
memory to the 1.130 graph: the node, `node_id`, ten new sources, one addendum, two edges
(`edge_901`, `edge_902`) and two roster `edge_id`s. It passes `validate_graph` with no new
errors or warnings (0 errors, 7 warnings before and after). The same holds with the optional
`edge_336` relabel applied.

## What is proposed

- **Node `carolyn_merchant`.** A person entry with the twelve standard person keys. The date
  label is *The Death of Nature 1980 · Ecological Revolutions 1989 · Radical Ecology 1992 ·
  coverage through 2000*.
- **`people_update`.** The existing `carolyn_merchant` record gets
  `node_id: carolyn_merchant`.
- **Edge 1 (main).** `carolyn_merchant → environment`, contribution, *Ecological revolutions
  and reproduction, 1987–90*. Target strand `environment/merchant_material_ideas`; roster row
  `environment`.
- **Edge 2 (main).** `carolyn_merchant → science`, contribution, *Mechanism and the death of
  nature, 1980*. Target strand `science/women_environment`; roster row `science`.
- **Optional edge revision.** Relabel `edge_336` (science → environment) so that it no longer
  carries her name. This follows the `edge_886` (1.129) and `edge_063` (1.130) precedents.
  `edge_113` is left unchanged (see below).
- **Sources.** Ten new (`pe131_merchant_*`), one addendum (`merchant_death_excerpt`), three
  reused on the node or the edges (`merchant_death_excerpt`, `pesic_proteus_1999`,
  `merchant_scientific_retrospective`).

## The framework, in her words

- **1980.** In *The Death of Nature*, a science that, "by reconceptualizing reality as a
  machine rather than a living organism, sanctioned the domination of both nature and women"
  (1993 reprint, p. 269). Also: "The removal of animistic, organic assumptions about the cosmos
  constituted the death of nature" (1991 reprint, p. 37).
- **1987 and 1989.** Ecological revolutions "arise from changes, tensions, and contradictions
  that develop between a society's mode of production and its ecology, and between its modes
  of production and reproduction". These tensions in turn support new forms of consciousness
  (*Environmental Review* 1987, pp. 265–266). Reproduction is "fourfold", with biological and
  social forms (p. 270).
- **1990.** Worster's framework "lacks a gender analysis", and environmental history "needs a
  fourth analytical level, that of reproduction" (*JAH* 76:4, p. 1117).

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `pe131_merchant_structure_1987` (new) | Full text, pp. 265–274, from the author-hosted JSTOR scan | The thesis; the four concepts; fourfold reproduction; her debts to Kuhn, Marx, Meillassoux, Peterson and Bridenthal |
| `pe131_merchant_jah_1990` (new) | Full text, pp. 1117–1121, author-hosted JSTOR scan | Gender analysis of Worster's three levels; reproduction as a fourth level; women conservationists; patriarchy. The canon-evidence file had marked this round-table response as inaccessible |
| `pe131_merchant_ecorev_1989` (new) | Book unread (Internet Archive copy is lending-only; search-inside returns 403). Read the chapter 1 and epilogue excerpts in Dolbeare 1996, pp. 577–590 (author-hosted) | Changes in gender relations as part of each revolution; nature as actor; socialist versus radical feminism. **Pages are the reprint's** |
| `pe131_merchant_death_1980_reprint` (new) | Introduction and Bacon chapter as excerpted in Zimmerman et al. 1993, pp. 268–281 (author-hosted, OCR) | The domination of nature and women; mechanism; the Bacon reading. **Pages are the reprint's** |
| `merchant_death_excerpt` (addendum) | Re-read, Zerzan and Carnes 1991, pp. 36–40; the contents page gives the 1980 source pages as 192–193, 290–292 and 294–295 | The "death of nature" sentence; power and commercial capitalism |
| `pe131_merchant_radical_1992` (new) | Conclusion, pp. 235–240, in facsimile (Redclift and Woodgate 1995) | The framework carried over to environmental movements (p. 239) |
| `pe131_merchant_retrospective_1998` (new) | pp. 198–202, and the start of the appendix | Her credits to Hessen, Zilsel, Leiss and Kubrin; early objections as she reports them (p. 201) |
| `pe131_merchant_steinberg_1991` (new) | Full review, Project MUSE (OCR) | In-period praise ("signal contribution") and criticism ("painfully few people making history"); book pp. 2–3 and 187 as he quotes them |
| `pe131_merchant_cronon_1993` (new) | pp. 2–3, 8–9 and notes (OCR) | "harmed nature and women in parallel ways" (p. 3); the gender lesson in n. 18 (p. 9) |
| `pe131_merchant_leach_green_1997` (new) | pp. 343–349 and references, open access | Places *Death of Nature* among the ecofeminist histories it criticises; its main target is Shiva |
| `pe131_merchant_soble_1995` (new) | Abstract only (OpenAlex) | A 1995 defence of Bacon that names Merchant |
| `pesic_proteus_1999` (reused) | Abstract re-read (OpenAlex) | Contests the torture reading. It does not name Merchant |

**Later readings, labelled as such.**
- McNeill 2003, pp. 38–39 (read): her scheme "has not attracted wide imitation within
  environmental history". Edge 1 quotes it as a later reading. I did not add it as a source,
  because other 1.131 drafts will probably add McNeill 2003; see `later_readings_not_added`.
- Merchant's 2006 *Isis* response: not re-read. It is listed on the node only.

**Not read.**
- The full texts of the three books.
- The other JAH 1990 responses and Worster's reply.
- Worster's own review of *Ecological Revolutions* (PHR 60:1, 1991, 102–103; 403 at UC Press).
- The 1981 reviews of *Death of Nature* (Longino, Osler, Pagel, Errington, Jacob, Perkins).
- The bodies of Soble 1995 and Pesic 1999.

**Founder claims: none.** Steinberg's "played an important role in forging the field" is
reported in the source note only. The entry names her own credited sources instead.

## Edges: reasoning

- **Edge 1 → environment.** Her framework is a direct, named intervention in environmental
  history's theory debate (the 1987 special issue and the 1990 round table).
  `merchant_material_ideas` names the production and reproduction scheme. `gender_nature` is
  the *Death of Nature* strand.
- **Edge 2 → science.** The 1980 argument about mechanism and the domination of nature. The
  contestation is set out in the evidence note: Soble, Pesic, Leach and Green, and her own
  1998 list of early objections.
  - The target is `women_environment` rather than `bacon_metaphor_dispute`. The dispute strand
    is about the disagreement and leans on the 2006 response, as Pomeranz's edges avoided the
    2002 "dispute" strands. Swap the target if reviewers prefer the arrow to land on the
    dispute.
- **How the person edges relate to the group edges.**
  - **`edge_336` (science → environment).** It is labelled "Merchant connects the history of
    science with women and environmental questions". Her two person edges tell this story,
    split into two arrows. An optional relabel to a group-level claim is offered, with the
    sources unchanged.
    - **Caveat.** All of `edge_336`'s sources are about Merchant or Pesic, so even
      relabelled it still rests on her case. Leaving it unchanged is a real alternative.
    - **How to apply it.** The applier reads `edge_revisions` from `batch.json`. Copy the
      relabel there if it is accepted.
  - **`edge_113` (environment → women).** Unchanged. It is the only environment–women link,
    and no person edge covers that pair.
- **Not proposed.**
  - **→ women.** Her words do tie her to women's history: nature as mother "links women's
    history with the history of the environment", and she recovered women conservationists
    in 1990. But no in-period text was read in which women's history takes her up, she has no
    roster row there, and no strand fits.
  - **→ gender.** The checked evidence shows a contribution to environmental history, not to
    gender history as a field.

## Wikidata Q2940097: the right person

Checked with the MCP tools (`search_items` and `get_statements`).
- **Search.** Semantic search returns Q2940097 first, then *The Death of Nature*
  (Q97798654), whose author is Q2940097.
- **Birth date and employer.** Wikidata gives 12 July 1936. LoC n79096657 gives "b. 7/12/36"
  and the Berkeley department named in her JAH byline.
- **Open Library.** Author OL443506A holds all three books.
- **Existing record.** The bulk match in `people-wikidata.json` is now reviewed.
- **Caveat.** Her P800 book item (Q96607820) is dated 1989, which is the second edition.

## Citation evidence (metadata only)

- **Canadian corpus.** 27 of 1,303 strict History PhDs (2009–2026) cite her, at 14
  universities.
- **Which works.** *Ecological Revolutions* 11, *Death of Nature* 8.
- **Caveat.** This measures Canadian reading, not importance. It is kept out of all node and
  edge text.

## Open questions for the editor

1. Accept the `edge_336` relabel, or keep her name on the group edge?
2. Should Edge 2 target `science/women_environment` or `science/bacon_metaphor_dispute`?
3. Should there be a `→ women` edge? If yes, read the 1984 *Environmental Review* article
   "Women of the Progressive Conservation Movement" first (author-hosted, articles/17.pdf),
   and relabel `edge_113`.
4. Source merging at release: Cronon 1993 (`pe131_merchant_cronon_1993`) and McNeill 2003
   are likely to be cited by the parallel Cronon, Worster and Crosby drafts under other ids.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 9.** Edge 1 quotes McNeill (2003, pp. 38–39) as a later reading; it now carries
  `pe131_extras_mcneill_2003` (canonical after the batch merges) in `source_ids`. The wording
  was re-checked in the text-layer PDF. `later_readings_not_added.mcneill_2003` records this.
