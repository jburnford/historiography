# TF-IDF families of sources (prototype, 2026-10-20)

**The user's idea (2026-10-20).** Weight each source by the sources it appears beside in a
dissertation's bibliography, "something like tf-idf", so that families emerge despite
the randomness of any one bibliography.

This prototype sits beside the co-citation fields of `scripts/dissertation_citation_views.py`
and changes nothing in that pipeline. Script: `scripts/dissertation_tfidf_families.py`. Logs:
`../../logs/tfidf-families-*.log`.

## Method

**Matrix.** Rows are dissertations, columns are works.

| Choice | Setting | Why |
| --- | --- | --- |
| Rows | strict History PhDs in scope (`in_analysis`) that cite at least 3 of the column works (`--min-works`) | fewer than 3 gives no usable mixture |
| Columns | scholarly works cited by at least 15 strict PhDs in scope (`--min-cited`) | same `scholarly` filter as the co-citation fields (no corporate or single-name first author; not cited mainly as a primary source). At 15 the vocabulary is exactly the co-citation fields' 884 works; the script checks this at run time. |
| Cells | binary (cited or not) | a bibliography lists a work once |
| IDF | smoothed, ln((1+N)/(1+df)) + 1 | a work cited by 15 PhDs weighs about three times one cited by 400; canonical works everyone cites say little about family |
| Length | each row L2-normalised after IDF | a 600-entry bibliography counts the same as a 60-entry one. Length is measured over the column works. |

**Families.**
- **Model.** NMF on the TF-IDF matrix: Frobenius loss, coordinate descent, `nndsvd` init
  (deterministic), seed 0. W is dissertations by families; H is families by works.
- **Soft membership.** Scale-free: a family's share of the reconstructed column (works) or
  row (dissertations). For works this is `colsum(W)_f · H[f,j]`, normalised. A work's
  normalised entropy (0 to 1) is its bridge score.
- **Stability.** Bootstrap with 50 refits per k. Dissertations are resampled with
  replacement and TF-IDF and NMF are refitted. Each refit's components are matched to the
  full-data fit by Hungarian assignment on the cosine of their work loadings. The score is
  the mean matched cosine. A family counts as reproduced at a matched cosine of 0.80 or
  more, and is flagged `unstable` below 0.60.
- **Init check.** Four random-init refits and one `nndsvda` refit, matched the same way.

**Choosing k (sweep 8–30, every k).**
- **First rule tried.** The largest k at or after the error elbow whose mean stability is at
  least 0.80. No k qualified, so the rule was replaced. The error curve is almost linear
  (relative error 0.90–0.96, usual for sparse binary data), so its elbow is weak, and mean
  stability never reaches 0.80.
- **Rule used.** The k that reproduces the most families at 0.80 or more, among ks with
  mean stability of at least 0.75. Ties go to the smaller k.

## The k sweep (main graph)

Columns:
- *mean*: mean matched cosine, over all families and refits.
- *p10* and *min*: the 10th-percentile family and the weakest family.
- *repro.*: the number of families reproduced at 0.80 or more.

| k | rel. error | mean | median family | p10 | min | repro. | |
|---|---|---|---|---|---|---|---|
| 8 | .957 | .768 | .749 | .635 | .617 | 3 | |
| 10 | .950 | .766 | .776 | .655 | .621 | 5 | |
| 12 | .943 | .783 | .795 | .695 | .569 | 6 | |
| 14 | .938 | .770 | .773 | .600 | .559 | 6 | |
| 16 | .933 | .733 | .758 | .493 | .280 | 6 | |
| 17 | .930 | .751 | .776 | .559 | .267 | 7 | |
| **18** | **.927** | **.784** | **.837** | .504 | .414 | **12** | **chosen** |
| 19 | .924 | .771 | .816 | .516 | .435 | 10 | elbow |
| 20 | .922 | .757 | .827 | .491 | .311 | 11 | |
| 22 | .917 | .740 | .795 | .382 | .348 | 11 | |
| 26 | .909 | .711 | .813 | .403 | .369 | 15 | |
| 30 | .901 | .692 | .731 | .452 | .355 | 12 | |

The full table is in `sweep.csv`.

**Why k = 18.**
- It is the most stable k overall (0.784, level with k = 12 at 0.783).
- It reproduces twice as many families as k = 12 (12 against 6).
- It sits next to the elbow (19).
- Above k = 20, extra families are mostly splinters: mean stability falls below 0.75.
- Random-init refits recover the k = 18 solution at a mean cosine of 0.90, so it is not an
  artefact of the `nndsvd` start.

**Coverage.** The fit covers 1,370 of 2,267 strict PhDs, using 884 works. The other 897 do
not cite 3 of the 884 works (see Limitations).

## Families, main graph (k = 18)

These are provisional labels: first authors of the top works, plus title terms. Stability
is the bootstrap matched cosine, and `!` marks an unstable family. *n* is the number of
dissertations dominated by the family.

| F | n | stab. | top works |
|---|---|---|---|
| 0 | 143 | .84 | Cook *Regenerators*, Westfall *Two Worlds*, Errington *Lion, the Eagle*, Berger *Sense of Power*, Allen *Social Passion*: 19th-c. English Canada, Protestantism, ideas |
| 1 | 139 | .94 | Van Kirk *Many Tender Ties*, Carter *Lost Harvests*, Smith *Decolonizing Methodologies*, Brown *Strangers in Blood*, Miller *Skyscrapers*: Indigenous history and the fur trade |
| 2 | 121 | .85 | Gleason *Normalizing the Ideal*, Adams *Trouble with Normal*, Owram *Born at the Right Time*, Korinek, Valverde: postwar youth, family, gender, moral regulation |
| 3 | 110 | .85 | Kelley & Trebilcock *Making of the Mosaic*, Knowles *Strangers at Our Gates*, Avery *Reluctant Host* and *Dangerous Foreigners*, Ward *White Canada Forever*: immigration, race and labour |
| 4 | 92 | .80 | Scott *Seeing Like a State*, Cronon *Nature's Metropolis* and *Changes in the Land*, Loo *States of Nature*, White *Organic Machine*: environment and the state |
| 5 | 83 | .41 ! | Davidoff & Hall *Family Fortunes*, Walkowitz *City of Dreadful Delight*, Foucault *Discipline and Punish*, Clark, Stone: British social and gender history (unstable) |
| 6 | 82 | .91 | Linteau *Histoire du Québec contemporain*, Lamonde, Dumont *Genèse*, Dion, Bock: Quebec historiography |
| 7 | 80 | .52 ! | Chakrabarty, Chatterjee, Stoler *Along the Archival Grain* and *Carnal Knowledge*, Cooper: postcolonial and colonial studies (unstable) |
| 8 | 71 | .90 | Pearson *Mike*, Granatstein *Ottawa Men*, Eayrs, Bothwell *Canada since 1945*, Stacey: political, diplomatic and defence history of Canada |
| 9 | 70 | .91 | Anderson *Imagined Communities*, Hobsbawm & Ranger *Invention of Tradition*, Gellner, Hobsbawm, Halbwachs: nationalism and memory theory |
| 10 | 65 | .90 | Vance *Death So Noble*, Morton *When Your Number's Up*, Fussell, Harris *Canadian Brass*, Cook *Shock Troops*: First World War and military history |
| 11 | 56 | .84 | Sugrue, McGirr, Cohen *Consumer's Republic*, May *Homeward Bound*, Rodgers *Atlantic Crossings*: postwar United States |
| 12 | 54 | .76 | Brewer *Sinews of Power*, Bailyn, Colley *Britons*, Linebaugh & Rediker, Hancock: British Atlantic and 18th-c. empire |
| 13 | 50 | .81 | White *Middle Ground*, Havard *Empire et métissages*, Dechêne *Habitants et marchands*, Richter, Trudel: New France and the Great Lakes |
| 14 | 45 | .73 | Butler *Gender Trouble* and *Bodies That Matter*, Scott "Gender", Foucault *History of Sexuality* and *Discipline and Punish*: gender and sexuality theory |
| 15 | 42 | .74 | Westad *Global Cold War*, Judt *Postwar*, Naimark, Herf, Zubok: Cold War and postwar Europe |
| 16 | 34 | .93 | Kotkin *Magnetic Mountain*, Martin *Affirmative Action Empire*, Hirsch, Fitzpatrick, Zubkova: Soviet history |
| 17 | 33 | .47 ! | Said *Orientalism* and *Culture and Imperialism*, Weber *Peasants into Frenchmen*, Fanon, Burbank & Cooper: a component carried by two Said titles (unstable) |

Full details are in `families.json`. Each family has its top 25 works and top 15 people,
year distribution and share of each five-year bin, top institutions, sample dissertations,
bootstrap and init stability, and a Louvain hint.

**Canadian sub-graph (`../countries/CA/tfidf-families/`).**
- **Fit.** k = 17; 1,259 rows; 838 works; mean stability 0.755; init 0.92.
- **Same families as the main graph:** Indigenous and fur trade (.94), Quebec (.93), and the
  political and diplomatic family (.93).
- **Differences:** postcolonial studies is stable here (.90, with Said at its head), and
  British Atlantic (.47), postwar Europe (.50) and British social history (.58) are
  unstable. With US theses removed there
  is no postwar-US family.
- **A new, unstable family** (F14, .23) mixes French Foucault translations, Chartier and
  Scott's *Weapons of the Weak*: a French-language theory component.

## Comparison with the Louvain co-citation fields

`comparison.json` matches NMF families with the Louvain fields of `views.json`, run at
their own settings.

**Overall agreement.** NMF top family against Louvain field, over the 818 works Louvain
clusters:
- Main graph: adjusted Rand 0.58, NMI 0.67.
- Canadian sub-graph: 0.53 and 0.64.

The two methods broadly agree.

**Where they coincide.**
- Strong matches (Jaccard over member works):
  - Indigenous and fur trade, 0.85
  - Quebec historiography, 0.77
  - War and the military, 0.75
  - Environment and the state, 0.66
  - Liberal order and religion, 0.61
- Matching on dissertations is weaker (0.3–0.5), as expected: Louvain's "engages" (cites
  3 or more of a field's works) is not the same as NMF's "dominated by".

**What NMF separates that Louvain merges.**
- **Postwar Canada, the Sixties and the Cold War** (84 works) splits into:
  - political and diplomatic history (F8, 41 works; Pearson, Granatstein, Bothwell);
  - postwar social and gender history (F2, 21 works; Gleason, Adams, Owram).
- **Colley · Brewer · Gilroy** (63 works) splits into:
  - the British Atlantic (F12, 32 works);
  - New France and the Great Lakes (F13, 24 works; Dechêne, Havard, Trudel, Richter).
- **Indigenous history and the Middle Ground.** Louvain puts *The Middle Ground* itself in
  its Indigenous field, which the main graph's label calls "New France, early modern empire
  & the Atlantic" (an inherited anchor label). NMF keeps Indigenous history (F1) apart from
  New France and the Great Lakes (F13). The main graph's label for that field should be
  revisited; the CA label "Indigenous peoples, fur trade & the West" fits it.
- **Soviet, Eastern European & Holocaust** (19 works) splits into Soviet history (F16) and
  Cold War and postwar Europe (F15).
- **Empire, colonialism & postcolonial theory** (60 works) splits three ways:
  - postcolonial studies (F7, 30 works);
  - British social and gender history (F5, 18 works);
  - the Said component (F17, 9 works).

  F5 and F17 are unstable, so this split is not firm.

**What Louvain finds that NMF does not.**
- **Labour & the working class** (42 works) has no NMF family at k = 18. 27 of its works
  join immigration (F3), 7 join F0, and Thompson's *Making* is split between F5 and F3.
  Labour history is cited by the same dissertations as immigration and ethnicity, so NMF
  does not separate the two; Louvain's cosine graph can.
- **Smaller fields.** Louvain's small theory field "Foucault · Scott" (16 works) maps only
  loosely to F14. Louvain leaves 66 works unclustered; NMF gives them soft memberships, and
  several (Geertz, Gramsci, Lefebvre, Scott's *Domination and the Arts of Resistance*) come
  out as high-entropy bridges rather than noise.

**Bridges.** Louvain has no bridge measure beyond each work's link split in `views.json`.
NMF entropy correlates with that link-split entropy (Spearman 0.49 main, 0.52 CA), but it
also gives each bridge's two families.

Most bridging works, cited by 30 or more PhDs (main graph):
- Bourdieu *Distinction* (0.82)
- Berman *All That Is Solid* (0.76)
- Gramsci *Prison Notebooks* (0.74)
- Geertz *Interpretation of Cultures* (0.71)
- McKay *Liberal Order Framework* (0.68; F0 0.32, environment and the state 0.16, then spread)
- Foucault *Power/Knowledge* (0.67)
- Francis *National Dreams* (0.67)
- Bederman *Manliness and Civilization* (0.66)
- Lefebvre *Production of Space* (0.66)
- Scott *Domination and the Arts of Resistance* (0.66)
- Igartua *Other Quiet Revolution* (0.66)
- Mills *Empire Within* (0.65)
- Pratt *Imperial Eyes* (0.65)
- McClintock *Imperial Leather* (0.65)

Theory classics and Canadian syntheses bridge. Topical monographs do not.

Named works:

| Work | NMF families (share) | Entropy | Note |
| --- | --- | --- | --- |
| *The Middle Ground* | F13 New France 0.67, F1 Indigenous 0.25 | 0.32 | a bridge between two families, not across the field map; the same pattern in CA (0.61 / 0.26) |
| Richter, *Facing East from Indian Country* | F13 0.52, F1 0.27 | 0.40 | |
| *Discipline and Punish* | F5 British social 0.40, F14 gender theory 0.31 | 0.56 | |
| Thompson, *Making of the English Working Class* | F5 0.37, F3 0.27 | 0.57 | |
| Colley, *Britons* | F5 0.42, F12 0.38 | 0.45 | |
| *Imagined Communities* | F9 0.79 | 0.32 | |
| *Seeing Like a State* | F4 0.73 | 0.32 | |
| *Orientalism* | F17 1.00 | 0 | it defines its own unstable component |

## Bibliographic coupling (dissertations)

`coupling.json` clusters dissertations by the cosine of their TF-IDF rows (a 15-nearest-
neighbour graph, Louvain), and also by Ward clustering into k clusters.

| Comparison | Main | CA |
| --- | --- | --- |
| kNN Louvain, resolution 1.0: ARI / NMI | 0.42 / 0.59 | 0.42 / 0.57 |
| kNN Louvain, resolution 1.5: ARI / NMI / weighted purity | 0.47 / 0.60 / 0.66 | 0.49 / 0.58 / 0.65 |
| Ward into k clusters: ARI / NMI | 0.33 / 0.54 | 0.24 / 0.51 |
| Nearest coupled neighbour shares the dominant family | 67% (chance 7%) | 67% (chance 7%) |

Dissertation clusters line up with NMF dominant families moderately well. Ward produces one
or two catch-all clusters, which lowers its ARI. The families are therefore visible from
both sides of the matrix: from works (H) and from dissertations (W and coupling).

## Variant: min-cited 8 (`variants/min-cited-8/`)

- **Fit.** 2,912 works and 1,673 rows (303 more dissertations covered); k = 14; mean
  stability 0.75; init 0.92; ARI with Louvain 0.56.
- **New family.** It finds early-modern English crime, gender and society (F4: Beattie,
  Fletcher, Walker, Stone; 126 dissertations), which is invisible at 15.
- **Cost.** Overall stability is lower at every k (no k reaches 0.75 above k = 17).
  Postwar Europe (0.56) and nationalism (0.59) become unstable, and postwar US weakens
  (0.63).
- **Trade-off.** Rarer works bring more dissertations in but add noise. Keep 15 as the
  default for now and revisit when the corpus grows.

## Limitations

- **Co-occurrence only.** Bibliographies are alphabetical lists. They give no in-text
  proximity, no citation counts and no section structure. "Appears alongside" means "in the
  same bibliography", nothing finer.
- **Coverage is about 60%.**
  - **Who drops out.** 897 strict PhDs (40%) cite fewer than 3 of the 884 shared works.
    They are mostly at Laval (68% of its PhDs), McGill (60%), Montréal (63%), UQAM (45%),
    McMaster (46%) and Alberta (49%).
  - **What they are.** Mostly ancient, medieval, European, Asian and African topics,
    French-language theses, and older theses. Their bibliographies are not short (median
    238 entries); they share little literature with the Canadian-history core.
  - **Consequence.** The families describe the Canadianist and modern core of the corpus,
    not the whole discipline.
- **Language and national literatures.** French-language literature forms its own families
  (Quebec, New France) partly because the works are in French. A French-language theory
  component appears in CA.
- **The corpus is CA-heavy.** Canada has 2,151 of 2,267 strict PhDs, so the main graph is
  almost the Canadian sub-graph. Once BASE extraction adds other countries, expect new
  families (European, Latin American and others) and a larger vocabulary.
- **Time bias in the vocabulary.** A work needs time to reach 15 citing PhDs. Recent
  dissertations therefore cite fewer column works, and family shares in late bins (for
  example the fall of Indigenous history after 2010) partly reflect the vocabulary. They
  are not trends. Do not read `share_of_bin` as a trend without a time-windowed vocabulary.
- **Instability is real.** Mean bootstrap stability is about 0.78 and three main-graph
  families are below 0.6. Treat F5, F7 and F17 as tentative.
- **Single-work components.** NMF can give one very widely cited work (here *Orientalism*)
  its own component.
- **Labels are provisional.** They are surnames plus title terms, with a Louvain hint, not
  editorial labels.

## Recommendations

1. **Use NMF as a second lens beside Louvain, not as a replacement.**
   - For bridges: soft membership and entropy, which Louvain lacks.
   - For dissertation mixtures: which families a thesis combines.
   - To flag Louvain fields that merge distinct literatures: postwar Canada, the Colley
     field, and the Soviet field.
2. **Review the main graph's Louvain label for field 0.** "New France, early modern empire &
   the Atlantic" is anchored on *The Middle Ground*, but its works are the Indigenous and
   fur-trade literature. NMF puts *The Middle Ground* with New France and the Great Lakes.
3. **Rerun the k sweep after BASE ingestion.** Consider a time-windowed vocabulary, for
   example works cited by at least 15 PhDs within ±10 years, before using family shares as
   trends.
4. **Report coverage beside every family statistic.** Consider per-area vocabularies (or
   min-cited 8) so that non-Canadianist dissertations get families.

## Rerun after new dissertations are added

```bash
# after build_dissertation_citation_graph.py has refreshed graph.json
python3 scripts/dissertation_tfidf_families.py --k-step 1 --bootstrap 50          # main graph
python3 scripts/dissertation_tfidf_families.py --country CA --k-step 1 --bootstrap 50
python3 scripts/dissertation_tfidf_families.py --min-cited 8 --variant min-cited-8 --k-step 1 --bootstrap 50
# a fixed k (still bootstrapped): --k 18 ; other options: --min-works, --seed, --knn, --bridges
```

- **Run time.** Each run takes 2–5 minutes (graph load about 8 s). The sweep re-chooses k
  by the rule above. A new sub-graph country runs with `--country CC` once it is in
  `meta.subgraphs`.
- **Family ids** are ordered by the number of dominated dissertations, so they change
  between runs. Match families across runs by their top works.
