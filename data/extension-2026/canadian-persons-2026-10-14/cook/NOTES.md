# Ramsay Cook: person entry draft (Canadian persons, Tier 1)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json).

## Validation

The draft was applied in memory to the live graph (revision 1.133). The test added the node,
the `node_id`, 7 new sources, 7 edges as `edge_919`–`edge_925` and 5 roster `edge_id`s.
- **Result:** `validate_graph` gives 0 errors and 7 warnings, the same 7 as the unmodified graph.
- **Size:** 168 nodes and 925 edges.
- **Source ids:** every edge and node source id resolves.
- **Caveat:** other Tier 1 drafts will take edge numbers too, so the final ids will differ.

## What is proposed

- **Node `ramsay_cook`.** It has the twelve standard person keys. Its date label lists dated
  works: "Canadian Centennial Cerebrations" 1967 · The Maple Leaf Forever 1971 ·
  "Regionalism Unmasked" 1983 · The Regenerators 1985 · "Cabbages Not Kings" 1990 ·
  "Identities Are Not Like Hats" 2000. The label has no coverage suffix.
- **`people_update`.** The existing `ramsay_cook` record gets `node_id: ramsay_cook`.

### Edges

| # | Target / strand | Type | Map label | roster_row |
| --- | --- | --- | --- | --- |
| 1 | `cdn_regional/limited_identities` | influence | 'Limited identities', 1967–69 | `cdn_regional` (precursor) |
| 2 | `cdn_regional/questioning_region` | **critique** | Regionalism questioned, 1977–83 | null (see below) |
| 3 | `cdn_national_tradition/laurentian` | **critique** | The Laurentian view as regional, 1977–83 | `cdn_national_tradition` (role mismatch) |
| 4 | `cdn_religion_reform/secularization_thesis` | contribution | The Regenerators, 1985 | `cdn_religion_reform` |
| 5 | `environment/ecological_exchange` | contribution | 'Cabbages Not Kings', 1990 | null |
| 6 | `who_killed_debate/reassessments_2000` | contribution | Identities contingent and multiple, 1993–2000 | `who_killed_debate` |
| 7 | `cdn_intellectual_cultural/empire_and_nation` | contribution | Nationalism criticised, 1967–71 | `cdn_intellectual_cultural` |

- **The two critique edges** rest on Cook's own words in two Acadiensis review essays, both
  read in full:
  - **1977.** "Those who live in the Valley of the Fraser, the Red or the Restigouche can hardly
    accept the Laurentian view of Canadian history as 'national' … And the other nationalist
    themes fare little better" (p. 110).
  - **1983.** "as a tool of analysis, 'regionalism' is a concept whose time has gone" (p. 141).
    In the same essay he asks "why not call a region what it really is — a province" (p. 140).
- **Why edge 2 has no roster row.** A roster row holds a single `edge_id`, so `cdn_regional`
  gets edge 1, whose influence kind matches its precursor role.
- **Edge 3 and its roster row.** The `cdn_national_tradition` row has the role contributor.
  Its context already says limited identities "reoriented the national frame". Reviewers may
  attach this critique edge or leave the row empty.

## Roster rows (5) and edge_id at apply time

| Roster row (role) | edge_id |
| --- | --- |
| `cdn_regional` (precursor) | `pe135_cook_rel_01` |
| `cdn_national_tradition` (contributor) | `pe135_cook_rel_03` (role/kind mismatch, see above) |
| `cdn_intellectual_cultural` (historian) | `pe135_cook_rel_07` |
| `cdn_religion_reform` (historian) | `pe135_cook_rel_04` |
| `who_killed_debate` (contributor) | `pe135_cook_rel_06` |

## What was read

| Source | Read | Supports |
| --- | --- | --- |
| `pe135_cook_burden_1977` (new) | UNB PDF, in full, pp. 110–115 | Edges 2 and 3 |
| `pe135_cook_unmasked_1983` (new) | UNB PDF, in full, pp. 137–142 | Edges 2 and 3 |
| `pe135_cook_atlantic_1993` (new) | UNB PDF, in full, pp. 146–152 | Edge 6 |
| `pe135_gauvreau_halfway_1991` (new) | UNB PDF, pp. 158–166 and 173–174 | Edges 1, 4 and 5 (in-period critic; quotes *Regenerators* pp. 4, 6, 12, 229) |
| `pe135_gaffield_regenerators_1986` (new) | uOttawa scan, OCR checked against the page images | Edges 4 and 7 |
| `cdng_buckner_2000` (addendum) | UNB PDF, pp. 4–5, 8–10 and 12 | Edges 1, 2, 3, 6 and 7 |
| `cic_karr_1989` (addendum) | UNB PDF, pp. 161–163 | Edges 4 and 7 |
| `crr_marshall_1993` (addendum) | cchahistory.ca web text, Cook passages and notes 2, 4 and 6 | Edge 4 |
| `cdng_cook_1967` (addendum) | OpenAlex opening text only | Edges 1 and 7 |
| `cdng_cook_2000` (addendum) | Abstract only | Edge 6 |
| `cdng_bliss_1991` | Abstract re-read; it does not name Cook | Context, edge 6 |

### Not read

- **Not accessible:**
  - ***The Regenerators*.** UTP returned 403, De Gruyter a captcha, and the Internet Archive
    copy is borrow-only. Its words are used only as Gauvreau, Karr and Gaffield quote them,
    and each quotation is labelled.
  - **"Cabbages Not Kings".** Project MUSE showed a captcha. The draft reuses the reading of
    2026-10-13 (`pe131_extras_cook_1990`; `canon-evidence-canada.md`, C1).
    - The conclusion, "Cabbages, at least as much as kings…" (p. 15), is recorded in the canon
      file but not in the source's verification note.
  - **The 1967 "limited identities" sentence.** It is not on the opening page available here,
    so it is quoted through Buckner.
  - **The 1970 nationalism essay and *The Maple Leaf Forever*.** These are quoted through
    Buckner and Karr. `pe135_cook_portnoy_1970` is metadata only.
  - **Careless 1969.** It is quoted through Buckner, as before.
  - ***Canada and the French-Canadian Question* (1966).** The Internet Archive copy is
    borrow-only.
- **Respected and not bypassed:**
  - **Érudit.** Its anti-scraping challenge blocked Cook's 1966 CHA paper on French-Canadian
    interpretations of the Conquest. I did not bypass it.
  - **The Internet Archive.** Its search-inside service returned 403.
- **Not attempted:** the body of Cook's 2000 CHR essay; "The Golden Age of Canadian
  Historical Writing" (1977); *Canada, Quebec and the Uses of Nationalism* (1995 edition).

## Corrections found

1. **The brief's title is wrong.** The 1967 article is "Canadian Centennial **Cerebrations**",
   not "Celebrations". The atlas sources already have the right title.
2. **Buckner 2000 misdates and misquotes Cook.**
   - **Date.** His n. 15 dates "The Burden of Regionalism" Autumn 1974. It reviews 1977 books
     and its OJS record is 1977.
   - **Quotation.** He quotes "whose time **is** gone"; the 1983 page reads "has gone".
   - **Paraphrase as quotation.** His p. 10 phrase "a construct which served only to mask …"
     reads as a quotation from "Regionalism Unmasked", but it is not on its pages. There, Cook
     quotes Gibbins on cloaking "provincial self-interest in the garb of regionalism".

   The draft quotes Cook's own pages and notes the slips in the source addendum.
3. **Bliss.** The brief suggested Bliss 1991 as a critic of limited identities. Only its
   abstract is readable, and it names neither Cook nor the phrase. The draft cites it only as
   context. The grouping of Bliss with the "gone too far" view is Buckner's (p. 9).

## Edges considered and not proposed

- **`quebec_historiography`:** his Quebec books are unread and he has no roster row there.
- **`cdn_political_national`:** content history.
- **`social`:** `edge_811` already carries his 2000 abstract.
- **`cdn_women_gender`:** *The Proper Sphere* is an edited collection.
- **`nationalismstudies`:** no engagement with its theorists in the texts read.
- **A second arrow to `cdn_religion_reform`:** the social-gospel and Allen material is folded
  into edge 4.
- **A Cook–Careless link:** see open question 3.

## Wikidata Q3101851: the right person

- **Identity.** "George Ramsay Cook", Canadian historian (1931–2016), born in Alameda,
  Saskatchewan.
- **LoC cross-check.** LoC n50027290 (id.loc.gov) gives "Cook, Ramsay", born 1931-11-28, with
  source citations to *The Regenerators* and *The Proper Sphere*.
- **No duplicate found.** No second person item came up.
- **Already recorded.** `data/people-wikidata.json` has this QID from an unreviewed bulk match;
  this check confirms it.

## Citation evidence (metadata only)

- **Reach.** 114 of 1,303 strict History PhDs (2009–2026) cite him, at 22 universities.
- **Trend.** The share is 9.0%, then 11.7%, then 4.9% (2020–26).
- **Most-cited works.** *The Regenerators* (41) and *Canada 1896–1921* (30).
- **Spread.** Dispersion is 0.835 across 5 fields.
- **Use.** None of this appears in the entry text.

## Open questions for the editor

1. **Two arrows to `cdn_regional`.** Should Cook have both an influence edge and a critique
   edge to `cdn_regional`? This draft says yes: the coiner of limited identities later judged
   region "a concept whose time has gone", and that turn is the point of the entry.
2. **Edge 3's roster row.** Accept edge 3 with the contributor row, or leave the row's
   `edge_id` empty?
3. **Careless.** He is being drafted in parallel. Decide whether the 1969 take-up is drawn
   once between the two entries. Here it sits in edge 1's evidence only.
4. **Strand membership.** Add Cook to `cdn_regional/questioning_region`, and decide whether
   the environment entry needs a Canadian strand (raised in the environment-family notes).
5. **Mid-task message.** The coordinator's mid-task note about Joy Parr and "The question of
   class" pathway reached this drafter. It concerns the Parr entry (folder `parr`), not Cook,
   and nothing for Parr was drafted here.
