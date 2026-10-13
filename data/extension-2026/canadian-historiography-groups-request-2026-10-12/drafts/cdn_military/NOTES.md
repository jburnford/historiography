# Canadian military history: drafting notes

Draft prepared 2026-10-12. Nothing is applied to the atlas.

**Entry.** Research field, `period_1`. The label is the one in `groups.json`. Date label: "Earlier official history (Duguid 1938) · Stacey's official histories 1955–70 · Broken Promises 1977 · war-and-society studies 1986–93 · Valour and the Horror controversy 1992 · Vance 1997 · coverage through 2000, selected later works". The description has 224 words. There are 19 roster people, 7 strands and 6 proposed relationships.

**Sources.** 27 new records: 4 with a supporting page read and 23 with metadata checked. The pages read are these:
- Cook's 2002 abstract in the CHR, which says the historical officers made the records and the narrative, and that those records were "neither neutral nor unbiased".
- Carr's review of Cook's *Clio's Warriors* (2006), which calls Stacey the long-time head of the Army's historical section.
- The UBC Press description of Vance's *Death So Noble*.
- The contents of *The Valour and the Horror Revisited* (1994), which include Wise's report to the CBC ombudsman.

Francophone sources:
- Gagnon's history of the 22nd Battalion (1986).
- Gagnon's 1995 essay in a Bulletin d'histoire politique dossier on "mythes et réalités".
- Pariseau's book on bilingualism in the forces (1987).

**Evidence.** 218 of 1,303 PhDs (16.7%) cite two or more roster people. The share falls from 19.0% in 2009–14 to 11.4% in 2020–26. *Death So Noble* is the most-cited work, in 67 PhDs. The francophone military historians are rarely cited: Gagnon in 5 PhDs, Pariseau in 3. The overlap with working-class history is high (86 PhDs, lift 2.69, even with Copp, Bercuson and Desmond Morton removed from both rosters). No checked source links the two fields.

**Judgement calls.**
- Official history, war and society, and memory are treated as overlapping modes, not stages.
- Berton is a popular-history "contributor".
- The 1992 Valour and the Horror controversy is a strand. It could become a debate entry in its own right.
- People whose primary placement is elsewhere appear for specific works: Stanley, Granatstein, Copp, Bercuson, Pierson and Vance.
- Unverified details were removed from the citations: Stacey's series title, Bernier's coauthorship and Duguid's volume count.

**Proposed relationships.**
- cdn_military – military (comparison)
- cdn_military → memory (contribution, Vance, to the war_mourning strand)
- cdn_military – quebec_historiography (comparison: conscription)
- cdn_military – cdn_women_gender (comparison: Pierson)
- cdn_military – publichistory (comparison: Valour and the Horror, Berton)
- cdn_military – cdn_political_national (comparison: war policy)

**Questions for the user.**
1. Should the label be shortened?
2. Is Bernier a coauthor of the 1987 Pariseau volume?
3. Did Duguid publish only one volume?
4. Should Berton stay on the roster?
5. Should the Valour and the Horror controversy become its own debate entry?
6. Should a checked pre-2000 history of Black or Japanese-Canadian soldiers be added?

**Overlaps with other drafts (checked 2026-10-12).**
- **War policy.** `cdn_political_national` proposes a comparison with this entry (war policy, conscription and the state). It duplicates my milreq_rel_06. Keep one.
- **War memory.** `cdn_intellectual_cultural` proposes a comparison on war memory. It complements milreq_rel_02 (cdn_military → memory).

## Answers applied (2026-10-12)

Applied from `answers/ANSWERS.md` and `answers/verification.json`; each answer is recorded in `question_resolutions`. The `open_questions` list is unchanged.

- **Q65 (applied).** The label is now **"Canadian military history"**. The description (248 words) opens with the three overlapping modes: official and operational history, war and society, and memory and public history.
- **Q66 (applied).** Serge Bernier is now coauthor of the 1987 volume, with the subtitle, series and tome: *tome 1, 1763–1969: le spectre d'une armée bicéphale*.
  - Checked against the DND official-histories page and a Bulletin d'histoire politique review header.
  - Bernier is credited in the strand only.
  - Merging the French and English records of the work gives 5 PhDs, not 2.
- **Q67 (applied).** The Stacey 1955 and 1960 citations now name the series: *Official History of the Canadian Army in the Second World War*, vol. I and vol. III. Checked against the DND page and the official-histories list.
- **Q68 (applied).** Duguid's 1938 volume is now "the only volume published", and Nicholson 1962 is named as its replacement.
  - New source: Gustavson, *Canadian Military History* 10:2 (2001), abstract read (`milreq_gustavson_2001`).
  - The Nicholson record now also cites the CHR 1963 review.
- **Q69 (no change).** Berton stays on the roster.
- **Q70 (applied).** The controversy stays a strand, with checked dates: broadcast January 1992, Senate hearings from June 1992, and the Ombudsman's report on 10 November 1992.
  - It is called a **major public-history controversy**, on the witness of Dick, *Archivaria* 35 (1993): 253–269 (new source `milreq_dick_1993`; read for verification.json). Dick is also added to milreq_rel_05.
  - It is **not** called "defining", because Carr's 2005 CHR article is unread.
- **Q71 (applied).** Walker, CHR 70:1 (1989), is the scholarly anchor, verified in Crossref.
  - Walker has a roster row, reusing `james_w_st_g_walker` from cdn_immigration_ethnicity.
  - Ruck (Nimbus 1987) and Ito (Canada's Wings 1984) are listed as community and veteran histories, checked against Open Library.
  - All three join Dempsey in a new strand, "Visible minorities and Indigenous soldiers".
  - PhD uptake, 2009–2026: Walker 14, Ito 4, Ruck 3.

**New sources:** Gustavson 2001 and Dick 1993 (supporting page checked); Walker 1989, Ruck 1987 and Ito 1984 (metadata checked). That makes 32 records in all. `proposed_source_records` in `entry-draft.json` was regenerated from `literature.json`, so the two now match.

**Corrections to the notes above:**
- The judgement call "Unverified details were removed" no longer applies: the series title, Bernier's coauthorship and Duguid's volume count are now verified and cited.
