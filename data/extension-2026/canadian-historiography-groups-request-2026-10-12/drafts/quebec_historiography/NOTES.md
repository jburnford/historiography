# Quebec historiography: drafting notes

Draft prepared 2026-10-12. Nothing is applied to the atlas.

**Entry.** Research field, `period_1`, with Groulx as an earlier root. Date label: "Earlier national history (Groulx) · RHAF first issue 1947 · Montreal and Laval schools 1950s–60s · Histoire du Québec contemporain 1979 · Rudin's critique 1992 · coverage through 2000". The description has 232 words. There are 21 roster people, 11 strands and 8 proposed relationships. (After the 2026-10-12 answers: 233 words, 26 roster people, 12 strands; see the end of this file.)

**Sources.** 33 new records: 8 with a supporting page read and 25 with metadata checked. One record is unverified and not cited: the founding of the IHAF by Groulx in 1946. About two-thirds of the sources are in French. The strongest pages read are the following:
- Bédard and Goyette's anthology *Parole d'historiens* (PUM 2006, on OpenEdition). I read its contents page and three reprinted texts: Savard 1974, Linteau 1983 and Rudin 1995.
- Rudin's 1992 opening in the CHR.
- Rouillard's 1997 abstract in the JCS.

**Evidence.** 161 of 1,303 PhDs (12.4%) cite two or more roster people. The share is steady to rising: 11.7% in 2009–14 and 13.1% in 2020–26. Francophone universities supply 40% of these PhDs, although they hold only 14% of the corpus. The older schools are cited almost only in French: Séguin by 7 of 7 PhDs, Wallot by 20 of 27, Groulx by 14 of 29.

**Judgement calls.**
- The Montreal school, Laval, the modernists and their critics are treated as distinct, overlapping positions. Savard warns against treating the "École de Québec" as one unit.
- "Revisionist" is presented as Rudin's polemical label.
- Annales influence is scoped narrowly. Savard documents Ouellet's debt to Labrousse, and Mandrou wrote the preface to Ouellet's 1966 book. Linteau says his generation owed more to sociology and to American historians.
- New France encounter history with Indigenous peoples is left to `native_newcomer`.

**Proposed relationships.**
- annales → quebec_historiography (contribution, Laval strand)
- social → quebec_historiography (contribution)
- nationaltradition – quebec_historiography (comparison)
- quebec_historiography – cdn_national_tradition (comparison, title-level)
- quebec_historiography – cdn_working_class (comparison)
- quebec_historiography – cdn_religion_reform (comparison)
- quebec_historiography – cdn_women_gender (comparison)
- quebec_historiography – cdn_sixties (comparison, for coordination with that drafter)

**Questions for the user.**
1. Groulx's founding of the IHAF and the RHAF is not verified. The draft says only that he contributed to the journal's first issue.
2. Should the period be `period_1` or `period_0`?
3. Should the label become "Quebec and French-Canadian historiography"?
4. Should the post-1970 generation be called "modernist", with "revisionist" kept only for the debate?
5. Should Trudel join the roster?
6. Several subtitles come from citation-graph records rather than catalogues. Each is flagged in its record.

**Overlaps with other drafts (checked 2026-10-12).** Three pairs are proposed twice.
- **National traditions.** `cdn_national_tradition` proposes its own comparison with this entry. Prefer that one and drop qcreq_rel_04, which is title-level only.
- **Religion.** `cdn_religion_reform` proposes a contribution edge to this entry (Catholic Action revisionism). Its kind differs from my comparison, qcreq_rel_06; keep one.
- **Women's history.** `cdn_women_gender` proposes a critique: women's history questions a male-centred Quebec history. Its kind differs from my comparison, qcreq_rel_07; keep one.

Two further proposals touch this entry: `liberal_order_framework` proposes quebec_historiography → liberal_order_framework (contribution), and `who_killed_debate` proposes a comparison.

## Answers applied (2026-10-12)
- **Q58 (applied).** Groulx founded the IHAF in 1946 and the RHAF in 1947. New record `qcreq_ihaf_1946` replaces the unverified one: the IHAF profile on fundit.fr was read, and the Canadian Encyclopedia and the 1976 RHAF note are cited from verification.json. Groulx's founding role is now stated in the description, date label, date span (1946), row and strand. The month of the first issue is not used, because the two sources disagree (March or June 1947).
- **Q59 (no change).** The entry stays in period_1, with Groulx as an earlier root. The rationale now says he is cited by 29 PhDs, mostly as a source for his memoirs.
- **Q60 (no change).** The label stays "Quebec historiography".
- **Q61 (applied).** The description, scope note and rows now call the post-1970 generation "modernist". "Revisionist" survives only in the normal-society debate strand and in cited titles.
- **Q62 (applied).** Dechêne is described as "trained in France in the Annales milieu of Mandrou and Goubert; Paris doctorate 1973". The source is the new record `qcreq_charron_dechene` (the Dictionnaire universel des créatrices entry, read); the Linteau and BnF evidence for 1973 comes via verification.json. The Annales edge `qcreq_rel_01` now also covers the New France strand. "Under Mandrou at Nanterre" was not added: theses.fr has no record. The Dictionnaire does say the thesis was "dirigée par R. Mandrou"; check the book's acknowledgements before relying on that.
- **Q63 (applied).** Trudel joins the roster. His sources are *L'esclavage au Canada français* (1960; record `cdnsrc_trudel_1960`, copied unchanged from cdn_immigration_ethnicity) and *Histoire de la Nouvelle-France* vol. 1 (Fides, 1963; new record `qcreq_trudel_1963`, checked against Open Library and a review heading in RHAF).
- **Q64 (no change).** Added to `pre_release_checks`: seven records whose subtitle or details come from the citation graph need checking against catalogues in the release check.
- **Q04 (cross-draft).** Brunet was already on the roster with a verified work (Montreal school). His row now gives his citation counts.
- **From Q12 (religion).** The new strand `catholic_action_origins` covers Meunier and Warren 2002, Bienvenue 2003 and Gauvreau 2005, with the Gauvreau 2004, Baum 2007 and Hébert 2009 reviews. Meunier, Warren and Bienvenue join the roster; Gauvreau gets strand credit only. Their records are copies under the same `crr_` ids. Gauvreau 2005 is cited here as `qcreq_gauvreau_2005`; merge it with `crr_gauvreau_2005` at release. Gauvreau has also moved out of `quiet_revolution_origins`.
- **From Q38 (women and gender).** The strand `women_in_quebec_history` (Clio, Lévesque, Baillargeon) is now primary here. Lévesque joins the roster, and Baillargeon's 2012 synthesis is added; these are copied `cdnsrc_` records. `cdn_women_gender` keeps the critique edge `cwg_rel_03`. The same works are recorded under two ids: Collectif Clio 1982 (`qcreq_clio_1982` and `cdnsrc_clio_1982`, whose contributor lists differ) and Baillargeon 1991 (`qcreq_baillargeon_1991` and `cdnsrc_baillargeon_1991`). Reconcile them at release.
- **Question for the user.** The roster is now 26, above the brief's 8–20. Candidates to make strand-only: Warren (primary placement cdn_sixties), Meunier, Durocher and Robert (coauthors with Linteau).
- **Fecteau 1999 (follow-up, from Q81).** `cdng_fecteau_1999`, his CHR review essay on Rudin, was missing from this draft. It is now added with the same id and citation, after Crossref was re-checked. It goes in the sources, the normal-society debate strand and Fecteau's row.
