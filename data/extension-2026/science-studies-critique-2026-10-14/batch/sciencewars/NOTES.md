# The Science Wars, 1994–2000: Debate entry draft for 1.135

Prepared 2026-10-14. The decision is the user's, made on 2026-10-14: "yes" to a new Debate entry,
"The Science Wars, 1994–2000". Haraway and Latour are "broadly aligned", so Haraway is not drawn
as a critic of Latour.

The draft is [entry-draft.json](entry-draft.json): a group node with no `people_update`. Its
evidence is [../../evidence-science-wars.md](../../evidence-science-wars.md), with
[../../evidence-ssk-latour.md](../../evidence-ssk-latour.md) as background.

## Validation (in memory)

The packet was built with `Batch(...).build()`, which writes `../release/editorial-additions.json`.
It was then applied with `Batch.transform` to a copy of the live 1.133 graph, whose last
`revision_history` version was set to 1.134 in memory only.

- **Result.** 168 nodes, 934 edges, 1,212 people and 1,597 sources.
- **Validation.** 0 errors, and the same 7 warnings as the unmodified graph.
- **Sources.** No source id dangles, and every new source is used.

The live graph was not edited.

## What is proposed

### The node `sciencewars`

- **Kind.** `entry_kind` is "group" and `entry_type` is "Debate".
- **Layer and period.** `historiographical_developments` and `period_3` (c. 1985–2000), as for
  `who_killed_debate` and `truthdebate`. `revival` uses `period_2` because its debate dates from
  1979–80.
- **No `date_span`.** `truthdebate` and `revival` have none either. The `date_label` carries the
  dated milestones, from *Higher Superstition* (1994) to *Pandora's Hope* and Shapin (1999), and
  one later reading (Latour 2004).
- **`coverage`.** `reviewed_through: 2000`. The survey covered 1994–2000. Later work was not
  surveyed: Latour 2004 is the only later text read, and *The One Culture?* and *After the Science
  Wars* (both 2001) are named but unread.
- **Description.** Seven sentences, longer than the 3–5 in the brief; debate entries run long
  (`who_killed_debate` has eleven). It is written as a teaching entry about the reception of
  science studies, and it notes that most attackers were scientists or philosophers.
- **Strands.** Six phase strands:
  - `higher_superstition` (1994–97)
  - `social_text_hoax` (1996)
  - `golem_physics_today` (1996–97)
  - `impostures_latour` (1997–99)
  - `house_built_on_sand` (1998)
  - `historians_answer` (1996–99)
- **Roster.** 22 rows in the node, plus Latour through `roster_additions`, linked to his reply edge.

**Roles.** The role vocabulary has no "respondent". I used it like this:
- **`critic`** goes to anyone who argued against one side:
  - the attackers: Gross, Levitt, Sokal, Bricmont, Weinberg, Koertge and Mermin (qualified);
  - the answerers: Collins, Pinch, Edge, Ross, Robbins, Fish, Wise, Shapin, Krige, Beller and Latour;
  - Jacob, as a historian on the attackers' side.
- **`historian`** goes to the even-handed historians and historian-commentators: Jardine,
  Frasca-Spada and Schweber.
- **`contributor`** goes to Hacking, the clarifier.

In `who_killed_debate` the charge-makers are `historian` and the repliers `critic`. That fits a
quarrel among historians, not this one. Each row's `context` says which side the person was on.
This is an editorial call: see open question 1.

**New people (17).** All are absent from the people table:
- the attackers: `paul_r_gross`, `norman_levitt`, `alan_sokal`, `jean_bricmont`,
  `steven_weinberg`, `n_david_mermin` and `noretta_koertge`;
- the SSK and *Social Text* respondents: `david_edge`, `andrew_ross` and `bruce_robbins`;
- the historians: `m_norton_wise`, `john_krige`, `mara_beller`, `nick_jardine`,
  `marina_frasca_spada` and `silvan_s_schweber`;
- the clarifier: `ian_hacking`.

Existing people reused: `harry_collins`, `trevor_pinch`, `steven_shapin`, `stanley_fish`,
`margaret_c_jacob` and `latour`. No Wikidata matches are recorded for the new people, following
the 1.131 practice for roster participants.

### Edges (11)

| # | Edge | Kind | Map label | Support |
|---|---|---|---|---|
| 1 | sciencewars → ssk | critique | Strong programme and The Golem attacked, 1994–98 | strong: Sokal 1997/98, Sokal and Bricmont pp. 79, 84, Mermin 1996 p. 11; Gross and Levitt only via Edge |
| 2 | ssk → sciencewars | critique | SSK replies: "scientific fundamentalists", 1996–97 | strong: Collins and Pinch 1996 p. 11; Edge 1997 |
| 3 | sciencewars → latour | critique | Latour attacked: nature and relativity, 1996–98 | strong: Sokal and Bricmont pp. 85, 115, 121; Sokal 1997/98; Sokal, *Le Monde*; Weinberg 1996; with Mermin's 1997 dissent and Fuller's LSE report |
| 4 | latour → sciencewars | critique | Latour replies: "not at war", 1996–99 | strong: *Pandora's Hope* ch. 1; *Le Monde* only as quoted by others; 2004 as a labelled later reading |
| 5 | science → sciencewars | critique | Historians of science reply, 1996–99 | strong: Shapin 1999 pp. 3–4, 11; Krige 1998; Beller 1998; Wise only via Edge |
| 6 | sciencewars → sts | critique | Science studies charged with relativism, 1994–98 | supported: Jardine and Frasca-Spada quoting the target; Sokal 1997/98; Robbins and Ross; Koertge (abstract) |
| 7 | sciencewars → kuhn | critique | The "immoderate Kuhn" blamed, 1996–98 | supported: Sokal and Bricmont p. 70; Weinberg 1996 and 1998 |
| 8 | sciencewars → language | critique | Postmodern theory attacked, 1996–98 | supported: Sokal's confession; the parody; *Le Monde*; the book's chapters on French theorists are unread |
| 9 | truthdebate → ssk | critique | Telling the Truth against the strong programme, 1994 | moderate: *TTAH* chs. 5 and 7, without print pages |
| 10 | truthdebate → latour | critique | Latour as postmodernist, 1994–98 | moderate: *TTAH* ch. 6 n. 9; Jacob 1998 (abstract only) |
| 11 | sciencewars – truthdebate | comparison | Truth, relativism and two 1990s disputes | Jacob in both debates; Evans 1999 enlisting Sokal |

`target_strand` points into the new node's own strands for the replies (edges 2, 4 and 5), and to
`ssk/strong_programme` for edges 1 and 9. It is null for person targets (`latour`, `kuhn`) and for
`sts` and `language`, with a note. Every `roster_row` is null. The Latour roster link comes through
`roster_additions` with `proposal_id: ss136_sw_rel_04`.

### Not drawn (see `edges_considered_not_proposed`)

- **Thin edges.** `sciencewars → science` and `sciencewars → gender` were not re-read and stay
  thin.
- **`sts → sciencewars`.** No STS essay was read, and Robbins and Ross write as cultural-studies
  editors.
- **A `truthdebate → sciencewars` critique.** The truthdebate book predates the Science Wars, and
  Evans endorses Sokal rather than criticising him.
- **Mediators.** Hacking and Kitcher are not drawn as critics.
- **Even-handed or defending pieces.** Jardine and Frasca-Spada, and Mermin's 1997 column, are not
  drawn as one-way critiques.
- **Cultural studies.** No edge to `culturalstudies`: that entry is British cultural studies.
- **Haraway.** She is not drawn against Latour (user decision).

## Verification

**Spot-checked quotations.** I did not re-read whole texts. The research phase read them today. I
checked every quotation used in the node, roster and edges against the research phase's saved
copies, with a normalising string match. Mismatches were OCR spacing only. The texts checked were:
- the Sokal texts;
- the *Lingua Franca* reply;
- the *Physics Today* scans;
- Edge;
- Jardine and Frasca-Spada;
- Weinberg (1996 and 1998);
- Krige;
- Shapin 1999 (OCR);
- *Pandora's Hope* ch. 1;
- Fuller;
- Croissant;
- *Telling the Truth about History*;
- Evans's response.

**URLs.** Source URLs were confirmed by HTTP status or by Crossref:
- The ELTE mirror pages return 200.
- Crossref supplied the DOIs for the *Physics Today* items, Shapin 1999, Jardine and
  Frasca-Spada, Sokal's *Social Text* article, Wise 1996 and Koertge 1998.
- The `physics.nyu.edu/sokal/` pages redirect to HTTPS, which failed from this machine. The copies
  had been saved in the research phase.
- Croissant's review URL returned 403 and was read from a saved copy.

**Re-reading the second-hand texts.** I tried to reach several texts known only at second hand,
without success:
- **Wise, *Isis* 1996.** The University of Chicago Press returned 403.
- **Laudan 1981.** SAGE returned 403.
- **Others.** scholar.archive.org returned a bot wall. A web search found no open copy of Latour's
  *Le Monde* article of 18 January 1997.

Their second-hand status is stated wherever they are cited.

**Not read** (as recorded in the source notes):
- *Higher Superstition*;
- Wise 1996;
- the *Social Text* essays;
- Latour, *Le Monde* 1997;
- *A House Built on Sand*, except Sokal's chapter and the publisher abstracts;
- *The Golem*;
- Hacking 1999 and Kitcher 1998;
- Gregory 1997;
- Levitt and Gross in *Technoscience* 1996;
- the *TTAH* print pages.

**New finding.** Crossref lists "Science wars: Apology" by Jardine and Frasca-Spada in *SHPS*
28:4 (1997), p. iii. Its subject is unknown. The editorial is our only witness for Latour's
*Le Monde* wording ("A small number of theoretical physicists deprived of the fat budgets of the
cold war"). The scope note, the `ss136_jfs_1997` note and edge 4 say so. The apology should be read
before release.

No email address, mailto or other personal identifier was sent to any service. Crossref and Open
Library were queried without one.

## Citation evidence (metadata only)

The figures are in `citation_evidence` in the draft, from `evidence-science-wars.md` §10. They
appear in no node or edge text.

## Open questions for the editor

1. **Roles.** Should both sides be `critic`, with the context giving the side, as drafted? The
   alternative is the `who_killed_debate` pattern, with the charge-makers as `contributor` (shown
   as "resource") and the respondents as `critic`.
2. **Label.** Keep the dates in the label ("The Science Wars, 1994–2000"), as the user approved? The
   other debate labels carry no dates.
3. **The Jardine and Frasca-Spada "Apology".** Read it before release. If it concerns the Latour
   quotation, edge 4 should rest on *Pandora's Hope* alone.
4. **Edge 8 (→ language).** Should it wait until a chapter of *Intellectual Impostures* on Lacan or
   Kristeva is read? Today it rests on Sokal's own statements of his targets.
5. **`sciencewars → gender`.** Draw it after *Higher Superstition* ch. 5 is read? Then
   `bacon_metaphor_dispute` on `science` could link Newman and Soble to Merchant.
