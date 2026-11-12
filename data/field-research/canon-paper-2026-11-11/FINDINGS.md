# Canon paper: first analyses (2026-11-11; figures updated 2026-11-12)

Scripts `00_base.py`–`09_translations.py` and their tables in `out/` were first run on the check build of the graph
(`build/graph-check/`, 37.0% of thesis citations matched; tables in `out-2026-11-11-morning/`), then on the live build
of 11-11 20:08 (41.96%; `out-2026-11-11-evening/`, `CHANGES-2026-11-11.txt`), and on 2026-11-12 on the live build with
credit roles, first publication years and the canonical translation fixes (42.14%; `out/`, `CHANGES-2026-11-12.txt`).
Figures marked [11-12] are from that run, with the 11-11 morning figure in brackets where it differs. Intervals are
bootstraps over citing documents (500 resamples). Counts and shares only; no thesis or article text. "People" are
person keys: other-field scholars and primary-source authors as well as historians.

## Table 1: what is matched [11-12] (1,285,599 of 3,050,449 thesis citations, 42.14%; morning 37.0%)

| Cut | Matched |
| --- | --- |
| Thesis country | US 56.7%, CA 47.5%, GB 42.7%, BR 35.5%, MX 31.2%, FR 28.1% (morning US 52.6, CA 42.2, GB 38.4, MX 27.4, BR 25.1, FR 24.5) |
| Cited kind | book 65.1%, article 36.9%, book or serial 29.8%, chapter 14.4%, unstyled 8.6%, thesis 2.6% (morning 60.2, 24.6, 28.5, 10.7, 7.7, 1.7) |
| Theses citing the work | 1: 21.4%; 2–4: 62.6%; 5–9: 82.7%; 10–49: 97.4%; 50+: 99.8% (morning 18.9, 54.7, 76.0, 84.4, 78.7: the dip at 50+ was Portuguese translations, gone since the translation links) |
| Section label | secondary 57.3%, primary 27.2%, unspecified 30.6% (morning 52.3, 24.7, 24.4; 83% of Brazilian citations are unlabelled) |
| Book year | 2010–13 about 55–59%; 2016 about 30%; 2017–20 about 18–23%; 2021+ 9–16% (11-11 evening; the post-2016 hole is unchanged in kind) |

- Scholarship frame (not mostly primary, cited by 2+ theses, dated 2015 or earlier): 32.7% of citations,
  79.8% matched (79.5–80.1) [11-12] (morning 69.8%); books only 85.8% (77.6%).
- No frame equalises countries: in the scholarship frame the US is at 89.4% and Brazil at 69.9% [11-12] (morning
  84.9% and 45.4%); the gap narrowed but did not close.
- A name route needs no catalogue match: the parsed author name is an anchor (`diss-person:`) of a person key
  for 37.6% of citations, 52.6% together with matched works [11-12] (Brazil 40.3% by name against 35.5% by match;
  morning 37.8%, 50.7%, Brazil 40% against 25%).

## Claims the data supports now

1. **The canon reaches far but takes little (robust).** The 100 most-cited works take 0.7% (corpus level) to
   2.1% (graph, 2.01–2.11) [11-12] (morning 1.6%) of thesis citations, yet 46–57% of theses cite at least one of
   them and 72–73% cite one of the 100 most-cited people. Unchanged under random loss of matches; the graph value
   is an upper bound.
2. **Supervisor effect (robust as an effect; about 4x within a stated frame).** 48.0% (46.7–49.4) [11-12] of
   theses cite their own supervisor through matched works (morning 46.8%), 56.7% with parsed names. Topical peers
   (same institution and decade, 3+ shared cited works) cite the same person 10.8% of the time: ratio 4.4
   (4.2–4.6) [11-12] (morning 3.6–3.7). The rise is a definition effect: with more works matched more peers pass
   the 3-shared-works bar, so state the ratio with its threshold. 8,950 thesis–supervisor pairs from 7,741
   theses. Against all institution-decade peers the ratio is 21–24, which is topic, not influence.
3. **Anglophone canons overlap about a fifth (robust).** Canada, the UK and the US share 12–14% of their
   top-100 people (21–25 names) [11-12]; profile similarity (cosine) 0.42–0.57, the same by matches and by names.
4. **The periphery leans on the shared canon; France and Brazil form an axis (within frame).** By name, on
   equal draws, 15–20% of French, Brazilian and Mexican person citations go to people cited in all six
   countries, against 8–9% for Canada, the UK and the US; through matched works 12.5–18.9% against 5.6–6.6%
   [11-12] (in the morning only the name route showed it). France–Brazil cosine 0.45 (0.43–0.47) by name and
   0.43 (0.41–0.46) by matched works [11-12], as close as Canada–US (0.47). Brazil and Mexico are more
   concentrated (top-100 people 7.2% and 5.9% of parsed-name person citations, against 2.0–2.9% elsewhere;
   morning 6.9%, 5.8%, 1.7–2.8%).
5. **Bibliographies age slowly (robust for theses).** Median age of cited scholarship, as printed: 17 years
   (theses of 2005–09), 18 (2010–14), 19 (2015–18), 20 (2019–26). Share under ten years old falls from 27.7%
   to 22.3%. Graph-matched by first publication year [11-12]: 21 / 21 / 22 for 2005–09 / 2010–14 / 2015–18.
   JSTOR articles, reweighted: 17 years in the 1970s–80s to 20 in the 2010s [11-12] (morning 12 to 19; 11-11
   evening 15 to 19). This part has weakened twice, with the larger JSTOR article set and with first publication
   years; it is a modest rise, not a firm trend.

## Claims the data does not support

- **"Brazil ignores the international canon."** A matching artefact: in the morning through matched works
  Hobsbawm reached 0.8% of Brazilian theses, by parsed name 31.9%; with the translation crosswalks and links
  [11-12] he reaches 28.4% through matched works (Thompson 16.6% / 18.2%, Le Goff 21.6% / 27.0%, Bourdieu
  17.5% / 29.1%). A cross-national claim on matched works is only as good as the translation links behind it.
- **"Sharp ageing in the 2020s."** Matched-only medians go 21 to 24 [11-12] (morning 19 to 23) because recent
  books are unmatched; the corpus as printed gives 19 to 20. The October Canada figure (16 to 23) is not reproduced.
- **Gini and top-1% levels.** They move with sample size (0.48 to 0.39 under a random 50% loss).
- **A decline in article canon concentration.** Reweighted by the thesis match rate the JSTOR top-100 share is
  flat at 4.3–4.5% by decade [11-12]; the observed fall (3.6% to 2.3%) is the match rate.
- **"Articles are more canonical than theses."** No JSTOR denominator (18 matched citations per article
  against 82 per thesis [11-12]); 2008–2020 the top-100 works take 2.2% of thesis pairs and 1.7% of article
  pairs. What holds: the two canons agree (person cosine 0.75 [11-12], morning 0.77; top-100 overlap about 0.27).
- **Any "historians only" result.** The role labels are unreliable (register class 16; 15 of the top 200 people
  are labelled 'primary source' [11-12]).

## Robustness

Headlines rerun with edition links off, linked credits added, the translation roll-up off, primary-source people
dropped, comma-title LC matches dropped, and authored credits only: all conclusions hold [11-12]. Exception in
size: dropping primary-source people raises Brazil's universal share from 18.8% to 24.5% (morning 5.5% to 7.4%),
because the classifier mislabels Brazilian scholars. Since 11-12 edition editors, translators, introducers, series
editors and contributors (associate, consulting, picture editors ...) never count as citations of the person's
own work; the edition editors of classics (Schluchter, Ewald, Lerner) have left the ranking, and Engels (26 -> 95)
and Foner (29 -> 64) fall because their edition-editor and consulting-editor credits no longer count.

## Data problems found (see ARCHITECTURE.md §8, classes 15–18)

Edition editors credited with classics (fixed 11-12 by credit roles); role labels wrong for Brazil and Mexico;
reprint years on work keys (11-12: first publication years cut anachronistic pairs from 2,229 to 779); 13,575
graph thesis edges (older `cites.csv.gz` routes) not rebuilt from the crosswalks (morning about 108k); a duplicate
original (Veyne, two keys, class 25).

## What would strengthen it most

1. Translation and edition links (Brazil's Portuguese canon first, about 59k citations).
2. Post-2016 book matching.
3. A field variable for theses outside Canada.
4. A JSTOR denominator, and AHR, Past & Present, EHR and CHR as citing journals.
5. An edition-editor flag, a reviewed role classifier, and the duplicate fixes.
6. Better French, Mexican and US samples.
