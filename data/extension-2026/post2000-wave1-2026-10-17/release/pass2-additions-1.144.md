# Revision 1.144: additions taken from the second research pass

A second, independent research agent re-researched the same five people. Its notes are kept as `../evidence-<person>.pass2.md`; the `*.pass1.md` files duplicate pass 1 and can be ignored.

This file lists **only the delta** that the packet took from pass 2, so a reviewer can check that alone. Each item rests on a text that pass 2 says it read; its read status, quotations and pages are copied into the source records and evidence notes and labelled "read by the second research pass". The edge ids are those of the current build on live 1.143.

## New edges (12)

| Edge | Proposal | Claim | Pass-2 strength | Evidence (as pass 2 read it) |
|---|---|---|---|---|
| edge_1047 | w1_huang_rel_07 | `practice` → `philip_huang`, influence | strong | Huang 2005, n. 3 (Bourdieu's "practice" acknowledged and modified); 1995, pp. 109–110 |
| edge_1048 | w1_huang_rel_08 | `philip_huang` → `karl`, critique ("incipient capitalism") | strong | 1985, p. 11 and 1991, p. 302 (read by pass 1 too); 1991, p. 313 and 1998, p. 188 (pass 2) |
| edge_1049 | w1_huang_rel_09 | `philip_huang` → `edward_said`, critique | strong | "Four Traps and a Question" (1998), pp. 193–195 |
| edge_1052 | w1_pomeranz_rel_03 | `kenneth_pomeranz` → `consumption`, contribution | moderate | his introduction (2000), pp. 17–18; pass 1 also saw p. 17. Flagged as a candidate by the coordinator |
| edge_1053 | w1_pomeranz_rel_04 | `kenneth_pomeranz` → `dependency`, critique | moderate | introduction (2000), pp. 14–16; p. 14 also read by pass 1. Flagged by the coordinator |
| edge_1063 | w1_daston_rel_05 | `elias` → `lorraine_daston`, influence | strong | "The Moral Economy of Science" (1995), n. 7 and p. 22 (IAS scan) |
| edge_1069 | w1_hall_rel_06 | `clr_james` → `catherine_hall`, influence | strong | Hall, *JBS* 2003, p. 533 ("as C. L. R. James's The Black Jacobins (1938) taught us") |
| edge_1070 | w1_hall_rel_07 | `fanon` → `catherine_hall`, influence | moderate–strong | *JBS* 2003, p. 530. Distinct from edge_418, which is **Stuart** Hall |
| edge_1071 | w1_hall_rel_08 | `catherine_hall` → `atlantic`, contribution | strong | UCL REF 2014 case study (WebFetch excerpts); 2014 introduction (excerpts, no pages) |
| edge_1072 | w1_hall_rel_09 | `catherine_hall` → `publichistory`, contribution | strong | REF 2014 case study; 2014 introduction |
| edge_1073 | w1_hall_rel_10 | `catherine_hall` → `gender`, contribution | moderate–strong | *JBS* 2003, pp. 531, 536–537 |
| edge_1074 | w1_hall_rel_11 | `catherine_hall` → `nationaltradition`, critique | strong (own text) | *JBS* 2003, pp. 530, 537; Tao Wei (2014) only as a reader of *Macaulay and Son*. This replaces the held C6: the edge now rests on her own 2003 statement, not the publisher's description |

Duplicate checks:
- edge_418 (`fanon` → `identity`) concerns Stuart Hall.
- No `clr_james`, `fanon`, `practice`, `karl`, `consumption`, `dependency`, `elias`, `atlantic`, `publichistory`, `gender` or `nationaltradition` edge already touches these persons.
- `catherine_hall` → `atlantic` (LBS reinscribing slave-ownership) and → `economic` (capital formation, pass 1) are kept as separate claims.

## Evidence added to existing proposals and edges

- **economic → Pomeranz (edge_1050).** Broadberry and Gupta, *EHR* 59:1 (2006), are added as a named critic (summary and pp. 2–3).
- **edge_898 (revision, appended).**
  - Pomeranz was co-founding editor of the *Journal of Global History* (2006), per the AHA biography as pass 2 read it.
  - The *JGH* editors' note of 2021 (read in full) says the debate "was a major inspiration for the foundation of the Journal in 2006"; it does not name Pomeranz.
- **Huang → Pomeranz (edge_1043).** Huang's 2016 restatement, "Our Sense of Problem" (p. 136).
- **Williams → Hall (edge_1064).**
  - The 2014 *Legacies* introduction's verdicts on Williams's four arguments (excerpts, no pages).
  - Donington (2020), "The project foregrounded Williams's work".
  - The REF case study, for Hall as the principal investigator.
- **Hall → post (edge_1066).** Her own 2003 statement of the book's "central argument" (p. 530) and the split narrative (p. 534).
- **foucault — Daston (edge_1061, now a comparison).** Henning (2008, read in full), pp. 154 and 157.
- **Hunt → global (edge_1056) and the `hunt` source addendum.** McClure was read in full by pass 2, which records Hunt's words with the book's pages as McClure gives them (pp. 43, 52, 55, 59).
- **Hunt → political (edge_1054).** The 2003 address's "politicization of everyday life" is located at n. 42.

## New source records from pass 2 (16)

- **Pomeranz:**
  - `kp_broadberry_gupta_2006`
  - `kp_jgh_editorial_2021`
  - `kp_huang_sense_problem_2016` (also used by Huang)
- **Huang:**
  - `ph_four_traps_1998`
  - `ph_rural_class_1995`
  - `ph_divorce_practice_2005`
  - `ph_modern_china_first_issue` (metadata)
- **Hunt:**
  - `lh_presentism_2002`
- **Daston:**
  - `ld_henning_2008`
  - `ld_cdf_bio_2009`
  - `ld_rules_2022`
- **Hall:**
  - `ch_jbs_response_2003`
  - `ch_ref_case_2014`
  - `ch_donington_2020`
  - `ch_taowei_2014`
  - `ch_lucky_valley_2024` (abstract)

Pass-2 ids are kept where pass 1 had no record. Where both passes read the same work, the pass-1 id is kept and pass 2's reading is appended to its note, so that each work has one source record. These are:
- Huang's 2003 rejoinder;
- Pomeranz's "Facts are Stubborn Things";
- Brenner and Isett;
- the AHA biography and address;
- Daston 1995 (`w1_daston_moral_economy_1995`);
- Hall's *Legacies* (`w1_hall_legacies_2014`), which is upgraded to `supporting_page_checked` for the introduction.

DOIs and URLs that pass 2 did not give were taken from OpenAlex or Crossref (no mailto) or found by search; each source note says which:
- Broadberry–Gupta;
- the *JGH* note;
- Huang 1995, 1998 and 2005;
- the Henning eprint;
- Donington's forum page;
- *Rules* (by the ISBN pattern).

## Chronology points added from pass 2

- **Huang:**
  - *Modern China* first issue, dated to January 1975 (Crossref), with Huang's own 2016, p. 154 n. 3, "which I founded in 1975";
  - 1995, "Rural Class Struggle";
  - 1998, "Four Traps", on the context track;
  - 2005, divorce-law practice;
  - 2016, "Our Sense of Problem", on the context track.
- **Pomeranz:**
  - 2006, *Journal of Global History* begins, on the context track (no journal edge);
  - 2006, Broadberry and Gupta (reception);
  - 2016, Huang's restatement (reception);
  - 2021, the *JGH* editors (reception).
- **Hunt:** 1 May 2002, "Against Presentism".
- **Daston:**
  - 1995, director at the MPIWG, on the context track, from the Collège de France biography ("Since 1995 she has been Director");
  - 2008, Henning's review (reception).
- **Hall:**
  - October 2003, "A Response to the Commentators";
  - 28 February 2013, the online Encyclopaedia launched;
  - 2014, Tao Wei's review (reception);
  - 11 January 2024, *Lucky Valley*;
  - the LBS project start dated 1 June 2009 and *Legacies* 28 August 2014 (REF case study; Crossref).

## Roster and strands from pass 2

- **New roster rows:**
  - `practice` (Huang, edge_1047);
  - `consumption` (Pomeranz, edge_1052);
  - `publichistory` (Hall, edge_1072);
  - `nationaltradition` (Hall, critic, edge_1074).
- **Existing rows:**
  - the `atlantic` row for Hall now carries edge_1071;
  - Hall's `gender` row gains *Civilising Subjects* (2002) and the 2003 response.
- **Strand fix:** `economic/coal_constraints_dispute` works go from "Huang (2002),533–534" to "Huang (2002),532–533". Checked against the pass-1 OCR: the coal discussion begins on p. 532, and p. 534 is the conclusion.

## People and identity

- **Huang's Wikidata QID Q64788725** was verified by pass 2 (WikidataMCP search and statements) and is recorded as the Huang draft's `wikidata_check`. `data/people-wikidata.json` is not edited.
- **Leadership of LBS.** Pass 1 had written that Hall's leadership was "not established". The REF case study, which pass 2 read, names the project as run by "Professor Hall and her research associates", so her description now says she "led" it with Draper and McClelland.

## Declined (pass-2 items not taken)

- **`lorraine_daston` → `epistemology`** (pass 2 rated it strong). It conflicts with the entry's French-tradition scope. Pass 2 also proposed widening that scope, citing Daston 1995, pp. 23–24 and Sturm 2008. This is left as a question for Sol and recorded in `edges_considered_not_proposed`.
- **`freud` → `lynn_hunt`**: weak; publisher description only.
- **`elias` → `lynn_hunt`**: moderate; Bell's claim about an unread book.
- **`kuhn` → `philip_huang`** and **`lorraine_daston` → `kuhn`**: optional or weak.
- **`post` → `catherine_hall`** (Gikandi): optional; known only through Hall's reply.
- **`catherine_hall` → `racial_formation`**: not recommended by pass 2 either.
- **Not used:**
  - Allen 2009 (abstract only);
  - Peer Vries via Mokyr;
  - Monnet 2010 (excerpts);
  - the Toynbee Prize announcement;
  - the Dan David page;
  - the 2011 *Historically Speaking* forum (metadata);
  - the NPR *neijuan* piece;
  - the Myers exchange (metadata);
  - the A. V. Chayanov people record.
- **Optional strands not taken:** pass 2's `economic/involution_growth_development`, `post/imperial_englishness` and `science/moral_economies_virtues`. A narrower `science/moral_economies` (Daston only) was added under Sol's finding 10.

## Disagreements between the passes, and their resolution

| Point | Pass 1 | Pass 2 | Resolution |
|---|---|---|---|
| Huang 1985 text | "1985 first printing" | "1988 paperback" | The archive.org metadata says 1988; the copyright page in the same OCR reads © 1985 with no reprint line. Pages agree. Cited as the 1985 text, noted in the source |
| Huang 2002, read extent | pp. 501–503, 511–512, 515, 530–535 closely | pp. 501–503, 514–515, 520–521, 532–534 | Both OCRed the whole article. Sol's wording is used; the page lists are kept in the source notes |
| Coal passage in Huang 2002 | p. 533 | pp. 532–533 | It begins on p. 532 (checked). The strand is corrected |
| Huang's rejoinder, pages read | 157–158, 164–165 | 157–158, 165–167 | Both partial; each pass's quotations keep its own pages |
| Daston 1995 page range | 3–24 | 2–24 | The article's first page prints "OSIRIS 1995, 10: 3-24"; p. 2 is the frontispiece. 3–24 kept |
| Daston directorship start | inferred from "24 years" | "Since 1995" (Collège de France biography, read) | 1995 is now a dated context event. Still no interval (Sol, finding 11) |
| *Rules* date | 2022 | 12 July 2022 (Princeton page) | A UK retailer gives 18 October 2022, so the year alone is used |
| Tao Wei volume | (search snippet: *Essays in History* 48:1) | 47 (read) | Pass 2's read citation is kept; the snippet is unverified (site now behind Anubis) |
| McClure review | WebFetch extraction | read in full (4-page PDF) | Pass 2's read status and page quotations are added to the `hunt` addendum |
| Hall and LBS leadership | "not established" | REF: run by "Professor Hall and her research associates" | Pass 2's read case study resolves it: "led" |
