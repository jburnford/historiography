# Black Canadian history (`cdn_black_history`): drafting notes

Prepared 2026-10-12. This is a proposal only; the atlas is not modified. The entry was created on the user's decision of 2026-10-12 (Q46), and it is not yet in `groups.json`.

## The entry

- **Type and period:** Research field, `period_2`.
- **Date label:** Earlier work: Trudel on slavery in French Canada 1960 · Winks's survey 1971 · Walker's Black Loyalists 1976 · Calliste on sleeping car porters 1987 · Brand's oral history of Black working women 1991 · We're Rooted Here 1994 · Walker's five orientations 1997 · Cahill–Walker exchange 1999 · selected publication milestones, not boundaries; coverage through 2000, selected later works.
- **Description:** 228 words.
- **Roster:** 18 people, 7 of them women. Four people work at or are read mostly at francophone and Quebec institutions: Trudel, Gay, Mackey and Williams.
- **Strands:** 7. **Relationships:** 7.
- **Literature:** 38 records. 22 have a supporting page checked and 16 are metadata-only. Four more are excluded as unverified.
  - Read in full: Walker 1997, Walker 1999 and Cahill 1999.
  - Reused by the same ids: 4 records moved from `cdn_immigration_ethnicity`, 2 from `cdn_military` and 2 from `cdn_sixties`.

## Uptake

- **The curated set.** 177 of 1303 PhDs (2009–26) cite at least one Black Canadian history work: 9.5% (2009–14) rising to 15.3% (2020–26). 79 cite two or more (3.7% → 7.2%). 16 are at francophone universities.
- **The Q46 figure.** The Q46 regex reproduces exactly: 104 PhDs, 5.6% → 8.9%. But 25 of those 104 enter only through non-Canadian matches ('esclavage' in French, medieval and Antillean slavery; the Indian Army). The regex also misses Mathieu, Barrington Walker, Williams, Calliste, Brand and Africville.
- **Dissertations on Black Canadian subjects.** There are 11, plus one in part. The "23" in the answer came from a title regex that also caught Natal, Chicago, the Black Sea and black bears; only 6 of those 23 are Black Canadian subjects.
- **Overlap with immigration and ethnicity.** 45% of the 177 engage `cdn_immigration_ethnicity` (lift 3.4; 43% without Walker as an anchor). Women and gender is the largest overlap (61%, lift 2.4).
- **Readership trends.** Readers are moving from the survey literature to post-2000 monographs:
  - falling: James Walker (2.4% → 0.5%) and Winks;
  - rising: Austin, Cooper, Mathieu, Whitfield and Trudel's slavery books (0.2% → 2.2%).

## Judgement calls

- **Period.** I chose `period_2` because the academic field formed in 1971–85: Winks, Walker 1976, the 1980 guide, Hill 1981 and the 1985 CHA booklet. Walker himself ties the "Community" orientation to that turn. `period_3` is a defensible alternative. Of the 20 most-cited works, 7 date from 1986–2000 against 4 before 1986, and the median first-publication year is 1998.
- **Critic and debate.** Cahill (1999) is the field's named critic. Both he and Walker were read in full. Walker's critical 1971 review of Winks is known only from their footnotes, so it is cited through Walker 1999 and not as its own source.
- **Community and non-academic authors.** Hill, Brand, Mackey, Ruck and Forsythe are included because Walker's reading list or PhD bibliographies use them. Forsythe (1971) is labelled a participants' collection, and Ruck a community history.
- **Excluded from the counts.** Rushforth's *Bonds of Alliance* is left out because its Black-history content was not checked. Backhouse's *Colour-Coded* is left out because it is a general history of racism.
- **Moves out of `cdn_immigration_ethnicity`.** That entry keeps a short cross-reference strand with Calliste (1993–94) and Shepard (1997), shared by id. Walker keeps a row there for *"Race," Rights and the Law* (1997).
- **Weak verification.** Calliste 1987 (*Canadian Ethnic Studies*) is checked only against Walker's bibliography; no catalogue or DOI record was found. Daniel Gay's and Barry Cahill's Wikidata matches are probable, not confirmed from their books.

## Proposed spec for `groups.json`

This is for the user to add; this draft does not edit `groups.json`. Only Walker and Mills appear in `candidates.csv`; the other names use the same format.

```json
{"id": "cdn_black_history", "label": "Black Canadian history",
 "scope": "People of African descent in Canada: slavery in New France and British North America (Trudel, Cooper, Whitfield, Mackey), Black Loyalists and refugees (Winks, Walker), community, women and oral history (Brand, Bristow et al., Williams, Flynn), work, migration and law (Calliste, Mathieu, B. Walker), Black Montreal (Austin, Mills), and the field's self-reflection (Walker 1997; Cahill–Walker 1999).",
 "period": "1970s onward (Trudel 1960 earlier)", "atlas_period_fit": "main period (period_2/period_3); most uptake from post-2000 extension work",
 "related_atlas_entries": ["black", "cdn_immigration_ethnicity (proposed)", "cdn_sixties (proposed)", "quebec_historiography (proposed)", "cdn_women_gender (proposed)"],
 "primary": ["Walker, James W. St. G", "Winks, Robin W", "Calliste, Agnes", "Williams, Dorothy W", "Cooper, Afua", "Whitfield, Harvey Amani", "Mathieu, Sarah-Jane", "Walker, Barrington", "Austin, David", "Brand, Dionne", "Bristow, Peggy", "Cahill, Barry", "Hill, Daniel G", "Mackey, Frank", "Gay, Daniel", "Flynn, Karen"],
 "also": ["Trudel, Marcel", "Mills, Sean"]}
```

## Questions for the user

There are no open questions. Two judgement calls could still be reviewed:

- the period (`period_2` or `period_3`);
- moving Walker's primary placement here.
