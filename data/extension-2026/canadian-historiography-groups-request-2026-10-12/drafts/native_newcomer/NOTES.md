# Native–newcomer relations & fur-trade history: drafting notes

Draft prepared 2026-10-12. Nothing is applied to the atlas.

**Entry.** Research field, `period_2`. Date label: "Earlier resources: Innis 1930, Stanley 1936 · Ray 1974 · Van Kirk and Brown 1980 · Trigger's Natives and Newcomers 1985 · Miller 1989 · Milloy 1999 · coverage through 2000, selected later works". The description has 215 words. There are 22 roster people, 12 strands and 8 proposed relationships.

**Sources.** 25 new records: 5 with a supporting page read and 20 with metadata checked. One record is marked unverified and is not cited: Winona Wheeler's work. The draft also reuses 8 atlas sources (Trigger, Dickason, Miller, Lutz, Sioui, LaRocque) and 3 records from the settler-colonialism packet (Carter 1990, Greer 2019, Konishi 2019).

**Evidence.** 219 of 1,303 PhDs from 2009 to 2026 (16.8%) cite two or more roster people. The share is steady: 16.1% in 2009–14 and 16.0% in 2020–26. Only 13 of those PhDs come from francophone universities. Within this group, the share that also cites Wolfe's or Veracini's settler-colonial works rises from 1 of 66 (2009–14) to 26 of 65 (2020–26).

**How it differs from neighbouring entries.**
- **`indigenous`** centres Indigenous historical authority. This field centres relations, policy and encounter, often written from colonial archives.
- **`settler_colonialism`** reads the same subjects as a continuing structure of dispossession. Most works here predate that framework, and Greer's critique runs the other way.
- **Indigenous critiques** of the framing are shown as critiques: Sioui's autohistory, LaRocque's 1999 dissertation, and Fixico and S. A. Miller (US, 2009). Their authors are critics, not members of the field.

**Judgement calls.**
- I kept all 16 primary people named in `groups.json`. I added Delâge (francophone), Fisher, Sioui and LaRocque.
- Dickason, Miller, Lutz and Trigger reuse their atlas ids and keep their existing contexts.
- Stanley's argument is not characterised.
- Kelm and Brownlie (1994) is supported by its title only, because Project MUSE blocked automated reading. Some of the matched graph records for this article are keyed to "Cole", which may be a reply. This is unchecked.

**Proposed relationships.**
- ethnohistory → native_newcomer (contribution)
- indigenous – native_newcomer (comparison)
- indigenous → native_newcomer (critique)
- native_newcomer – settler_colonialism (comparison)
- cdn_national_tradition → native_newcomer (contribution, via Innis)
- native_newcomer → cdn_working_class (contribution, via Lutz)
- native_newcomer – cdn_women_gender (comparison)
- native_newcomer – medicalhistory (comparison, optional)

**Questions for the user.**
1. Should the label keep the historical term "Native–newcomer" or change to "Indigenous–settler relations"?
2. The roster has 22 people, above the brief's 8–20. Should Fisher go, or should Sioui and LaRocque move to strands?
3. Is there a checked Canadian Indigenous critique from before 2000, such as Wheeler's?
4. Should Daniel N. Paul (1993) stay? He is cited at title level only.
5. Is the Innis edge wanted, given that his primary placement is `cdn_national_tradition`?

**Overlaps with other drafts (checked 2026-10-12).** `cdn_regional` and `cdn_immigration_ethnicity` each propose a comparison with this entry. Neither duplicates the edges here.

## Answers applied (2026-10-12)

Per-question records are in `entry-draft.json` → `question_resolutions`.

- **Q52 (applied):** the label is now **Indigenous–newcomer relations & fur-trade history**. The description explains that the field long called itself 'native–newcomer' history, after Trigger's *Natives and Newcomers* (1985). The scope note explains why 'Indigenous–settler' was avoided.
- **Q53 (no change):** the roster stays at 22.
- **Q54 (pending research):** a Canadian Indigenous critique before 2000 (e.g. Wheeler) is still being researched.
- **Q55 (applied, partly verified):** the citation now reads Robin Brownlie and Mary-Ellen Kelm, "Desperately Seeking Absolution: Native Agency as Colonialist Alibi?", CHR 75:4 (December 1994): 543–56, confirmed on the author's University of Manitoba profile.
  - The author's display name is now **Jarvis Brownlie** (he), matching `liberal_order_framework`; the id `robin_jarvis_brownlie` is kept.
  - The essay is described as a critique of the agency turn in Indian-policy and potlatch scholarship (Cole and Chaikin, Miller, Loo), not of the fur-trade literature.
  - Those targets come from a search snippet of Miller's *Reflections*. The essay itself is still unread.
- **Q56 (no change):** Innis stays a precursor, and edge `nnreq_rel_05` is kept.
- **Q57 (applied):** Paul is kept. The source is renamed `nnreq_paul_2000` and cites the Fernwood 2000 edition, which PhDs cite (first published by Nimbus, 1993). Both editions were checked in Open Library edition records. It is cited by 12 PhDs (2009–2026).
- **Q54 (applied after research, 2026-10-12):** added Winona Stevenson [Wheeler], "Indigenous Voices, Indigenous Histories, Part I: The Othering of Indigenous History", *Saskatchewan History* 50:2 (Fall 1998): 24–27, as `nnreq_stevenson_1998`.
  - The essay was read in full via OCR (answers/research/q54). It replaces the unverified placeholder `nnreq_wheeler_unverified`, which has been removed.
  - The atlas person `winona_wheeler` is now a critic, named "Winona Wheeler (published as Winona Stevenson)", beside Sioui and LaRocque.
  - LaRocque's claim now cites PDF pp. 249, 102, 109 and the note on p. 30.
  - The description adapts the research file's suggested sentence. It is now exactly 250 words; a few phrasings elsewhere were tightened to fit.
  - Adams and Dickason are explicitly not critics of this field. Trigger, and Brownlie and Kelm, stay non-Indigenous context. Brownlie and Kelm are now phrased as a question ("asked whether"), as the research caution asks.
  - No source here claims the essay was "the first" Indigenous critique.
