# Laurentian & national tradition (`cdn_national_tradition`): drafting notes

**Draft status:** proposal for review, 2026-10-12. Nothing in the atlas is changed.

**What it is.** A teaching umbrella for English-Canadian national historical writing, c. 1920s–1970s: the staple approach
(Mackintosh, Innis, later Watkins), Creighton's Laurentian narrative, the liberal and conservative nationalists (Lower and
Underhill; Creighton and Stacey), Careless's metropolitanism, Morton's questions about premises, the Canadian Centenary Series,
and Berger's analysis of the tradition. Date label: *Staple studies 1923–40 · Creighton 1937 · Lower 1946 · Careless 1954 ·
Centenary Series volumes 1964–85 · Berger's analysis 1976 · coverage through 2000*. Period: period_0.

**Roster:** 18 people, including the francophone historians Trudel and Ouellet (as translated Centenary Series authors), Brunet as a
comparison, Neatby, and the critics Davis and (through limited identities) Cook and Careless.

**Evidence.** 173 of 1,303 strict 2009–2026 History PhDs (13.3%) engage the anchors; falling from 16.6% (2009–14) to 8.9% (2020–26).
The most-cited works are Innis's Fur Trade (49 PhDs) and Berger's Writing of Canadian History (48). See `evidence.json`
(produced by `four_groups_evidence.py` in this folder, which writes evidence for all four of my drafts).

**Judgement calls.**
- The strongest witness for characterizing the tradition is Buckner 2000 (pp. 4–5, read): the liberal and conservative
  nationalists, the nation-state as frame, the comparison with US consensus history. Innis and Creighton are characterized
  through Watkins 1963 and Salmon 1997 (opening texts), not through reading their books.
- Careless 1954, Careless 1969, Berger 1976 and the Centenary Series are metadata-level only. I do not claim who edited the
  Centenary Series.
- Morton 1946 is used only for what its abstract says (it asks about premises); I do not claim it was a western critique of the
  Laurentian thesis, though that may well be the argument.
- Five relationships: comparison with `nationaltradition`, contribution to `economic`, comparison with `progressive`
  (consensus), comparison with `quebec_historiography` (via Miville's Creighton–Brunet study), and a critique from `urbanhistory`
  (Davis 1985). The comparison with Quebec duplicates qcreq_rel_04 in the quebec draft (title-level, Brunet 1958); I mark it
  `merge_with` so one edge carries both source sets. The Innis → native_newcomer contribution is in that draft (nnreq_rel_05).
  The regional critique, the political-history comparison and the debate comparison sit in my other drafts.

**Questions for the user:** see `open_questions` in `entry-draft.json` (entry type, Trudel/Ouellet placement, secondary anchors,
Brunet, period).

## Answers applied (2026-10-12)

Applied from `answers/ANSWERS.md`; each answer is recorded in `question_resolutions` in `entry-draft.json`. The `open_questions` list is unchanged.

- **Q1 (applied).** The entry type stays "Teaching umbrella". The label is now **"Laurentian & national tradition"**, and the scope note says that no checked source uses "Laurentian school".
- **Q2 (applied).** Trudel and Ouellet are off the roster and out of `new_people`.
  - Their translated volumes (1973, 1980) stay in the Centenary Series strand and the description.
  - `cdng_ouellet_1966`, which was cited only for Ouellet's row, was removed.
- **Q3 (applied).** Stacey is off the roster, along with the "Official history and external policy" strand and three sources: `cdng_stacey_1955`, `_1970` and `_1977`.
  - `_1970` and `_1977` remain defined in cdn_political_national.
  - Buckner's naming of Stacey as a conservative nationalist stays in the strand and description prose.
  - Stanley stays as a **secondary row** for *The Birth of Western Canada*, to represent the Riel interpretation (editorial decision).
- **Q4 (applied).** Brunet is off the roster and out of the strand person_ids. The Creighton–Brunet comparison stays in cdng_nt_rel_04 and in the prose.
- **Q5 (no change).** Ormsby stays in cdn_regional, and Neatby remains on this roster. Whether the tradition should include more women remains open.
- **Q6 (applied).** period_0 is confirmed. The rationale now cites the interwar founding works and the cited core, which runs from Innis 1930 to Berger 1986 (median 1969).

The roster now has 14 people, and the description has 199 words. The uptake figures still use the groups.json anchor set, which includes Stacey; the uptake note says so.
