# Immigration, ethnicity & race in Canada (`cdn_immigration_ethnicity`): drafting notes

Prepared 2026-10-12. Proposal only; the atlas is not modified.

- **Entry:** Research field, `period_2`. Date label: Earlier work (Trudel 1960; Winks 1971) · Walker 1976 · Ward 1978 · Avery 1979 · Abella and Troper 1982 · Perin 1983 · Anderson 1991 · Walker 1997 · Backhouse 1999 · selected publication milestones, not boundaries; coverage through 2000.
- **Description:** 206 words. **Roster:** 18 people. **Strands:** 7.
- **Sources:** 26 verified (7 with a supporting page read, 19 metadata only); 1 unverified and excluded (harney_1988).
- **PhD engagement:** 172 of 1303 PhDs (13%); 14.6% (2009–14) → 8.9% (2020–26); 9 at francophone universities.

## Proposed relationships

- `racial_formation` — `cdn_immigration_ethnicity` (comparison): Race as a historically made category. Evidence: abstract_checked.
- `cdn_immigration_ethnicity` → `black` (contribution): African-Canadian historiography. Evidence: full_text_checked.
- `identity` — `cdn_immigration_ethnicity` (comparison): Ethnicity, recognition and the politics of its discovery. Evidence: opening_text_checked.
- `cdn_immigration_ethnicity` — `cdn_working_class` (comparison): Immigrant workers and labour radicalism. Evidence: bibliographic_metadata_only.
- `cdn_immigration_ethnicity` — `cdn_women_gender` (comparison): Immigrant, ethnic and racialized women. Evidence: bibliographic_metadata_only.
- `cdn_immigration_ethnicity` — `native_newcomer` (comparison): Citizenship programmes for newcomers and Indigenous peoples. Evidence: abstract_checked.

Proposed in my other drafts (one edge per pair): `moral_regulation`–`cdn_immigration_ethnicity` (comparison, in moral_regulation).

## Judgement calls

- Black Canadian history is a strand here, not a sub-field; the contribution edge goes to the atlas's black entry. A separate Canadian Black history entry is an open question.
- Walker's 'Allegories and Orientations' is cited as Dalhousie Review 77:2 (1997), checked in full text; the request's CHR 1999 citation was wrong.
- Anderson is a contributor, not a critic of Ward: no checked text states a critique.
- Harney's Daedalus essay is excluded as unverified; Gathering Place stands in.
- Racial formation is a comparison edge: Omi and Winant are almost never cited by these PhDs, so derivation is not asserted.

## Questions for the user

- Black Canadian history: keep it as a strand here (proposed), or create a separate Canadian Black history entry? groups.json lists 'Black Canadian history' among possible missing groups. Walker's 1997 essay treats it as its own historiography.
- Correction to the request: Walker's 'Allegories and Orientations in African-Canadian Historiography' is Dalhousie Review 77:2 (1997), not CHR 1999.
- Harney's 'So Great a Heritage as Ours' (Daedalus 1988) and his role in the Multicultural History Society of Ontario could not be verified; Gathering Place (1985) stands in for him.
- Ward and Anderson: the draft notes that their approaches differ (attitudes and policy vs racial category) but does not make Anderson a critic of Ward, because no checked text says so. Should someone read Anderson 1991's introduction?
- Knowles is a popular historian whose 2007 edition is what PhDs cite; keep her as a contributor row?
- Francophone uptake is low (9 of 172 engaged PhDs at Montréal, UQAM, Laval and Sherbrooke). Ramirez and Helly are included; are there other francophone works the user wants (e.g. on immigration to Quebec)?

## Answers applied (2026-10-12)

Per-question records are in `entry-draft.json` → `question_resolutions`. The counts at the top of this file predate these changes: Harney 1988 is now cited, so nothing is excluded as unverified, and three sources were added.

- **Q46 (held for the user):** the answer recommends a separate 'Black Canadian history' group. Nothing was created; the Black Canadian strand and the contribution edge to `black` are unchanged.
- **Q47 (no change):** Walker 1997 was already cited as Dalhousie Review 77:2.
- **Q48 (applied, partly verified):** Harney, "So Great a Heritage as Ours", Daedalus 117, no. 4 (1988): 51–97. The volume, year and pages come from a citing article (Wilson, CJPS 1993). **The issue number is still unconfirmed.** Harney's row now says he co-founded the Multicultural History Society of Ontario in 1976 with Milton Israel and others, and was its president and academic director from 1977 until his death in 1989. New sources: `cdnsrc_mhso_1976` (society page) and `cdnsrc_vecoli_1990` (AHA obituary), both read.
- **Q49 (applied):** Stanley's review in BC Studies 97 (1993) was read in full and added as `cdnsrc_stanley_1993`. Reviewers saw Anderson moving beyond earlier studies of white attitudes and prejudice. Stanley's caveat is also noted: like those studies, she says little about Chinese Canadians' own challenges to the discourse. Anderson is still not called a critic of Ward.
- **Q50 (no change):** Knowles stays as a contributor row.
- **Q51 (pending research):** further francophone works on immigration to Quebec are still being researched.
- **Q51 (applied after research, 2026-10-12):** added a short **Immigration to Quebec** strand with five new sources:
  - Ramirez 1984, and the French edition *Par monts et par vaux* 1991 (new);
  - Helly 1987;
  - Anctil 1988 (optional, included; new);
  - Taschereau, RHAF 1988, title level only (new);
  - Pâquet 1997 in period (new), and *Tracer les marges de la Cité* 2005 as extension (new).

  Martin Pâquet (Q55717189) is a new contributor row. Research-checked QIDs were added for Ramirez and Helly. The text says these works are thinly cited (3–8 PhDs each) and does not call them widely taken up.
