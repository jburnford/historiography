# Is Canadian environmental history rooted in the American canon? (test, 2026-10-13)

The user's hypothesis (2026-10-13): "I bet the Canadian environmental history is very rooted in
the American canon, but you can test it."

Script: [env_canon_test.py](env_canon_test.py), run as
`python3 -I env_canon_test.py data/field-research/dissertation-citations-2026-10-11 results.json`.
Output: [results.json](results.json).

## Which dissertations count

There are 1,959 History PhDs in the analysis set of the Canadian dissertation citation graph.
"Environmental" means both of the following:

- the title has an environmental keyword (166 dissertations); and
- the bibliography cites at least 3 works from the co-citation field "Environment, development
  & the state" (92 dissertations).

52 dissertations meet both tests. One is from 2004 or earlier, 16 are from 2005–2014 and 35
are from 2015 onwards. The corpus says almost nothing about Canadian environmental history
before 2005.

## Results for the 52 environmental PhDs

**Who they cite.** 96% cite at least one of 22 American canon figures, and 87% cite at least one
of 21 Canadian figures.

| American | PhDs (of 52) | Canadian | PhDs (of 52) |
| --- | ---: | --- | ---: |
| Cronon | 39 (75%) | Loo | 34 (65%) |
| White, Richard | 28 | Piper | 22 |
| Hays | 24 | MacEachern | 20 |
| Worster | 22 | Sandlos | 17 |
| McNeill | 19 | Innis | 15 (29%) |
| Jacoby | 17 | Evenden, Cole Harris | 15 each |
| Nash | 15 | Keeling, Binnema | 13 each |
| Merchant | 14 | Wynn | 11 |
| Crosby | 13 | Lower | 7 |
| Carson | 9 | Forkey | 7 |
| Pyne | 8 | Cook | 4 |
| Marsh | 4 | | |
| Leopold | 2 | | |

**Top 50 people cited.** The most cited person is Cronon. Three of the top five are American:
Cronon, Richard White and James C. Scott. Further down, the list is mostly Canadian: Loo,
Parr, Nelles, Piper, MacEachern, McKay, Sandlos, Colpitts, Owram, Cole Harris, Evenden, Innis
and others. About 31 of the 50 are Canadian scholars and about 17 are American.

**Change over time.** The share of these PhDs citing Cronon rises from 56% (2005–14) to 83%
(2015 onwards), and Crosby from 6% to 34%. Hays and Nash fall. Innis rises from 19% to 34%.

## Reading

The hypothesis holds for frameworks. The shared conceptual canon of Canadian
environmental-history PhDs is American: Cronon above all, then White, Worster, Hays, McNeill
and Crosby. The Canadian names are mostly content historians of Canadian places and resources,
with Innis a minority reference. This is the pattern of the person-entry principle: American
frameworks, Canadian content.

The Canadian self-accounts (see [canon-evidence-canada.md](../canon-evidence-canada.md)) tell
their origin story around Innis, while dissertation reading runs through Cronon. Both are true
at different levels.

## Limits

- **A narrow slice (user).** These are Canadian PhDs only. A US comparison waits on the US
  dissertation harvest.
- **Name matching.** People are matched on name keys. "Cook" may include other Cooks; Cole
  Harris includes his historical-geography work; White counts all of his works, including *The
  Middle Ground*.
- **What "cites" means.** A bibliography lists works consulted, not influence.
- **Sample size.** n = 52 is small. The keyword-only set (n = 166) gives the same ordering at
  lower rates.
