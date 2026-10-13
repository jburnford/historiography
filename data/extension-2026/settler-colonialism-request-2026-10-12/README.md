# Request: a new atlas entry, *Settler colonialism*

Prepared 12 October 2026 for the user and for Astra. **A proposal for review only.**
Nothing here changes `historiography-1920-2000.json` (revision 1.127), `docs/`, `site/`,
`data/evidence-layer/` or `data/field-research/`. Every claim, person and relationship
carries `review_status: needs_review`.

On 2026-10-12 the user said that "Settler Colonialism is super important". At present the
atlas holds it as a single comparison row: Patrick Wolfe's 1999 book in the Indigenous
entry's strand `settler_colonial_interlocutor`. It has no entry of its own, no roster
beyond Wolfe and Harris, and no relationships.

## The case in brief

1. **Canadian History PhDs have taken it up fast, from almost nothing.** Over 2009–2011,
   1 of 149 strict History PhDs cited a core settler-colonial work. Over 2021–2023 the
   figure was 27 of 211 (12.8%). Over 2009–2026 as a whole it is 86 of 1,303 (6.6%, 95% CI
   5.4–8.1%).
2. **Its home is the Canadian historiography of Indigenous peoples and the West.**
   - 74 of the 86 core-citing PhDs also engage the "Indigenous peoples, fur trade & the
     West" co-citation field. That is 86%, against 20% of all PhDs (lift 4.3).
   - Wolfe, Veracini, Coulthard and A. Simpson are all clustered in that field.
3. **It is contested, and the critiques are cited too.** 23 PhDs cite a published critique
   or reassessment. Allan Greer's CHA presidential essay is the most cited (8 PhDs).
4. **The atlas cannot show any of this yet.** Settler colonialism mostly falls after 2000,
   so it belongs in the partial extension, like `digital_history`.

## 1. Dissertation evidence

Full tables are in [evidence.json](evidence.json) and the CSVs. Counts are of
**dissertations, not citations**. They use only `in_analysis: true` strict History PhDs. The
analysis period is 2009–2026; pre-2009 rows are context only.

### Work sets

| Series | Definition |
| --- | --- |
| theory | Wolfe (1999, 2001, 2006, 2016), Veracini (2008, 2010, 2011, 2013, 2015, 2017), Elkins & Pedersen (2005), Battell Lowman & Barker (2015), Cavanagh & Veracini (2016/17), Hixson (2013), Mamdani (2001, 2020) |
| **core** (headline) | theory + Coulthard (2014), A. Simpson (2014), Tuck & Yang (2012), Byrd (2011), L. B. Simpson (2011, 2017), Kauanui (2016) |
| core + vocabulary | core, or any cited work whose title says "settler colonial(ism)" |
| Canadian context | Harris (1997, 2002, 2004, 2020), Carter (1990, 1997, 1999, 2008, 2016), Perry (2001, 2015), Daschuk (2013), Regan (2010), Razack (2002) |
| critique | Greer (2019 ×2), Ostler & Shoemaker (2019), Shoemaker (2019), Macoun & Strakosch (2013), Snelgrove, Dhamoon & Corntassel (2014), King (2019) |

**Why the Canadian context series is kept separate.** Carter, Perry, Harris and Daschuk are
already cited at 8–14% of PhDs in the earlier context years. Counting them in the core
would measure the long-standing Indigenous–newcomer historiography, not uptake of the
paradigm.

**Work matching.** Each work's graph ids were matched by hand, with title variants merged.
The scripts list them.

### Uptake by window

Shares are of strict History PhDs in each window; the core 95% CI is Wilson.

| Window | PhDs | theory | **core** | core 95% CI | core + vocab | Canadian context | critique |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 1990–99 (context, thin) | 183 | 0 | 0 | 0–2.1% | 0 | 2 (1.1%) | 0 |
| 2000–04 (context, thin) | 132 | 0 | 0 | 0–2.8% | 0 | 11 (8.3%) | 0 |
| 2005–08 (context, thin) | 123 | 0 | 0 | 0–3.0% | 0 | 17 (13.8%) | 0 |
| 2009–11 | 149 | 1 | **1 (0.7%)** | 0.1–3.7% | 3 (2.0%) | 18 (12.1%) | 0 |
| 2012–14 | 261 | 2 | **3 (1.1%)** | 0.4–3.3% | 6 (2.3%) | 37 (14.2%) | 0 |
| 2015–17 | 314 | 11 | **17 (5.4%)** | 3.4–8.5% | 25 (8.0%) | 45 (14.3%) | 3 |
| 2018–20 | 245 | 17 | **24 (9.8%)** | 6.7–14.2% | 32 (13.1%) | 29 (11.8%) | 3 |
| 2021–23 | 211 | 22 | **27 (12.8%)** | 9.0–18.0% | 40 (19.0%) | 32 (15.2%) | 11 |
| 2024–26 (incomplete) | 123 | 12 | **14 (11.4%)** | 6.9–18.2% | 30 (24.4%) | 18 (14.6%) | 6 |

- **Pre-2009.** Lacking Toronto and York, the corpus has 621 dated PhDs from before 2009.
  None cites a core work, and 30 cite the Canadian context works.
- **Takeoff.** Uptake rises around 2015. The Canadian context series stays flat at about
  12–15%: the new vocabulary joins an existing literature rather than replacing it.
- **Other views.** Year-by-year figures are in [uptake-by-year.csv](uptake-by-year.csv).

### By university, 2009–2026

Core share, with counts. Full table: [uptake-by-university.csv](uptake-by-university.csv).

| University | PhDs | core | Note |
| --- | ---: | ---: | --- |
| Manitoba | 17 | 6 (35%) | thin |
| Saskatchewan | 59 | 9 (15%) | |
| Alberta | 40 | 6 (15%) | |
| SFU | 30 | 4 (13%) | |
| UVic | 33 | 4 (12%) | |
| UBC | 58 | 7 (12%) | |
| York | 94 | 9 (10%) | |
| McGill | 86 | 7 (8%) | |
| Western | 68 | 5 (7%) | |
| Toronto | 207 | 12 (6%) | |
| Queen's | 70 | 2 (3%) | |
| Carleton | 44 | 1 (2%) | |
| McMaster | 53 | 1 (2%) | |
| Montréal | 91 | 1 (1%) | |
| UQAM | 65 | 1 (2%) | |
| Ottawa | 54 | 0 | |
| Guelph | 35 | 0 | |

- **West and east.** Uptake is concentrated in the West and British Columbia.
- **Francophone universities are near zero.** That holds even counting French vocabulary.
  The one French title with "colonialisme de peuplement" cited by two PhDs (Côté 2019)
  is an education article. Laval has only 14 PhDs in the graph while downloads are
  pending, so francophone coverage needs a re-check.

### Core works by citing PhDs, 2009–2026

Of 1,303 strict History PhDs.

| Work | PhDs | Universities | First cited |
| --- | ---: | ---: | ---: |
| Wolfe, "Elimination of the Native" (2006) | 31 | 13 | 2013 |
| Veracini, *Settler Colonialism* (2010) | 25 | 14 | 2012 |
| Coulthard, *Red Skin, White Masks* (2014) | 23 | 11 | 2015 |
| A. Simpson, *Mohawk Interruptus* (2014) | 23 | 11 | 2015 |
| Wolfe, *Settler Colonialism and the Transformation of Anthropology* (1999) | 17 | 11 | 2012 |
| Tuck & Yang, "Decolonization Is Not a Metaphor" (2012) | 13 | 9 | 2015 |
| Byrd, *Transit of Empire* (2011) | 10 | 8 | 2015 |
| Wolfe, "Land, Labor, and Difference" (2001) | 9 | 6 | 2009 |
| L. B. Simpson, *As We Have Always Done* (2017) | 8 | 6 | 2019 |
| Kauanui, "A Structure, Not an Event" (2016) | 7 | 4 | 2020 |
| Veracini 2011; Veracini 2013; Battell Lowman & Barker 2015 | 6 each | | |
| Elkins & Pedersen (2005) | 2 | 2 | 2012 |

- **For comparison, the Canadian context works are cited far more.** Perry 2001 has 73
  PhDs, Harris 2002 48, Carter 1990 47, Daschuk 2013 45 and Carter 2008 44.
- **By scholar** (any work, 2009–2026): Carter 125, Perry 122, Greer 119, Harris 88,
  Wolfe 54, Daschuk 43, Veracini 39, Mamdani 35 (mostly *Citizen and Subject*, which is not
  settler-colonial), A. Simpson 33, Coulthard 26, L. B. Simpson 26, Tuck 21, Elkins 13,
  Byrd 12.

### Works co-cited with Wolfe and Veracini

58 PhDs (2009–2026) cite a Wolfe or Veracini settler-colonial work. The works they most
often also cite are:
- Daschuk 2013 (19 PhDs, lift 10.2)
- Perry 2001 (19)
- L. T. Smith, *Decolonizing Methodologies* (17, lift 9.6)
- Van Kirk, *Many Tender Ties* (17)
- Anderson, *Imagined Communities* (16, lift 1.7)
- Kelm, *Colonizing Bodies* (15)
- Said, *Orientalism* (15, lift 3.1)
- Harris 2002 (14)
- Hogue, *Metis and the Medicine Line* (13)
- McKay, "Liberal Order Framework" (13)
- A. Simpson (12)
- Coulthard (12)
- Tuck & Yang (11, lift 19)

Higher-lift neighbours include:
- the 2019 *William and Mary Quarterly* forum introduction (lift 22);
- Greer 2019 (lift 17);
- Harris 2004;
- Jacobs 2009;
- Métis histories: *One of the Family*, *Metis and the Medicine Line*, *"Métis": Race,
  Recognition*, and *The North-West Is Our Mother*.

The full list is in [cocitation-wolfe-veracini.csv](cocitation-wolfe-veracini.csv).

### Neighbourhood among the `views.json` co-citation fields

**Placement of the works.** Every clustered core work sits in **"Indigenous peoples, fur
trade & the West"**:
- Wolfe 2006: 0.91 of link weight;
- Coulthard: 0.91;
- Veracini 2010: 0.73;
- Wolfe 1999: 0.71.

Wolfe 1999 and Veracini also link to "Environment, development & the state". *Orientalism*
and Mamdani 1996 sit in "Empire, colonialism & postcolonial theory".

**Fields that core-citing PhDs also engage.** Lift is the share among core-citing PhDs
against the share among all PhDs:

| Field | Core-citing PhDs | All PhDs | Lift |
| --- | ---: | ---: | ---: |
| Indigenous peoples, fur trade & the West | 74 of 86 (86%) | 20% | **4.26** |
| New France, early modern empire & the Atlantic | 25 (29%) | 10% | 2.83 |
| Environment, development & the state | 21 (24%) | 10% | 2.45 |
| Immigration, race & ethnicity | 22 (26%) | 14% | 1.78 |
| Liberal order, religion & the state | 24 (28%) | 17% | 1.61 |
| Empire, colonialism & postcolonial theory | 32 (37%) | 24% | 1.58 |
| Labour & the working class | 5 (6%) | 9% | 0.66 |

**Reading.** In Canadian History PhDs, settler colonialism lives inside Indigenous and
western historiography, with secondary ties to the environment, early modern empire and
postcolonial theory. It is not a branch of postcolonial studies in this corpus.

### Dissertations that name it

Seven strict History PhDs have "settler colonial(ism)" in their own titles, all from
2011 onwards. Five of the seven cite the core.

| Year | University | Title |
| --- | --- | --- |
| 2011 | Toronto | "Toronto Has No History!" Indigeneity, Settler Colonialism, and Historical Memory |
| 2018 | UVic | Settler colonialism and the failed-settlement narrative in the Ottawa-Huron Tract |
| 2018 | York | The Science of Settler Colonialism: … the Thrifty Gene Hypothesis |
| 2020 | McGill | Universal nation: Settler colonialism and the Canadian public debt over Miꞌkmaꞌki |
| 2020 | Western | Russian Settler Colonialism in the Post-Soviet Crimea |
| 2021 | Saskatchewan | … Coast Salish and Mi'kmaw Work and Family Life under Canadian Settler Colonialism |
| 2023 | SFU | Enabling settler citizens: … settler colonialism in northern Ontario |

**Freeman's 2011 thesis.** It cites the earlier settler-society literature (Stasiulis &
Yuval-Davis 1995, Coombes 2006, Pateman 2007) rather than Wolfe or Veracini. This is a
reminder that the vocabulary predates the paradigm's canon.

**Wider "settler" titles.** Eleven more titles use "settler" more broadly ("settler
science", "settler wasting", "Indigenous–settler relations"). See
[settler-titled-dissertations.csv](settler-titled-dissertations.csv).

## 2. The field's literature

[literature.json](literature.json) holds 52 records. Each was checked on 2026-10-12 against
the DOI or URL recorded with it: Crossref, OpenAlex, Cambridge Core, UBC Press, journal
pages, library catalogues or Open Library.

**Verification status.**
- 17 are `supporting_page_checked`: an abstract, contents page or opening was read for the
  stated point.
- 34 are `bibliographic_metadata_checked`.
- **1 is `unverified`**: Wolfe's 1994 *Social Analysis* essay. JSTOR blocked access, so it
  is excluded from the proposed sources.
- **No book was read in full.**

**Sections:**
- **Origins and precursors:** Denoon 1983; Stasiulis & Yuval-Davis 1995; Wolfe 1999;
  Elkins & Pedersen 2005.
- **Theory:** Wolfe 2001, 2006, 2016; Veracini 2008, 2010, 2011, 2013, 2015; Cavanagh &
  Veracini; Hixson; Hoxie 2008.
- **Indigenous critique and resurgence:** Byrd; L. B. Simpson 2011, 2017; Tuck & Yang;
  Coulthard; A. Simpson; Kauanui.
- **Canadian historiography:** Carter 1990, 2008; Harris 1997, 2002, 2004, 2020; Perry 2001;
  Razack; Regan; Daschuk; Battell Lowman & Barker; Burrill.
- **Comparative and adjacent:** Mamdani 2001, 2020; Belich; Jacobs; Ford; Côté.
- **Critiques.** Each was checked from its abstract or opening unless noted.
  - Macoun & Strakosch 2013: the theory "posits a structural inevitability".
  - Rowse 2014: a "teleology of elimination".
  - Snelgrove, Dhamoon & Corntassel 2014: argument from a search summary; a lead only.
  - Sexton 2016: Black radicalism and decolonial sovereignty.
  - Greer 2019 (*JCHA*): settler colonialism dominates some periods and regions, and
    "imperial/commercial penetration" and "extractivism" are other modes.
  - Greer 2019 (*WMQ*).
  - Ostler & Shoemaker 2019.
  - Shoemaker 2019: universal theory or English heritage?
  - Konishi 2019: Indigenous scholars on settler colonial studies.
  - King 2019: metadata only.
  - Garba & Sorentino 2020: a critique of Tuck & Yang's triad.

**Date discrepancies are recorded, not resolved:**
- Elkins & Pedersen: 2005 in the catalogue, 2006 on the publisher page.
- Cavanagh & Veracini: online 2016, print 2017.
- Wolfe 2016: editions dated 2015 and 2016.
- Regan: EPUB 2010, print 2011.
- Greer *JCHA*: volume 30 (2019), online 2020.

## 3. Proposed entry

The full draft is in [entry-draft.json](entry-draft.json).

- **id / label:** `settler_colonialism` / **Settler colonialism**
- **Classification:** `entry_kind` group, `entry_type` Research field, layer
  `historiographical_developments`, `period` null.
- **date_label:** *Earlier settler-society studies 1983–95 · Wolfe 1999, 2006 · Veracini 2010 · journal 2011 · selected critiques 2013–20; field chronology unresolved*
- **date_span:** 1983 (`earlier_roots`) to 2020 (`unstated`), described as selected
  milestones only.
- **Relation to 1920–2000.** Only the precursors (1983, 1995) and Wolfe 1999 fall inside the
  main period. The name, the journal, Canadian uptake and the critiques all come after
  2000. Recommended handling:
  - make it an extension entry with `extension_coverage.status: proposed` and
    `field_review_complete: false`;
  - keep it out of the exact-2000 baseline (1.121);
  - keep the Indigenous strand `settler_colonial_interlocutor` as the in-period
    cross-reference.
- **Description** (188 words). It is drafted from the abstracts and contents read, and
  names its critics.
- **Roster** (33 people; 30 new ids, plus existing `patrick_wolfe`, `cole_harris` and
  `nira_yuval_davis`):
  - contributors: Wolfe, Veracini, Elkins, Pedersen, Coulthard, A. Simpson, L. B. Simpson,
    Tuck, Yang, Byrd, Battell Lowman, Barker, Regan, Razack;
  - historians: Harris, Carter, Perry, Burrill;
  - comparisons: Daschuk, Mamdani;
  - precursors: Denoon, Stasiulis, Yuval-Davis;
  - critics: Kauanui, Greer, Shoemaker, Rowse, Konishi, Macoun, Strakosch, Garba,
    Sorentino, Sexton.
  - **QIDs.** Each person's citation-graph QID is carried with a note that it was not
    reviewed for the atlas. No new Wikidata grounding was done.
- **Thirteen strands:**
  - structure, not event;
  - theory and field formation;
  - settler societies before the name;
  - comparative twentieth-century colonies;
  - Indigenous critiques of recognition, sovereignty and resurgence;
  - dispossession, reserves and geography;
  - gender, family and nation;
  - settler identity and reconciliation;
  - health and starvation (comparison);
  - labour and the settler order;
  - critiques of structure, region and period;
  - Indigenous scholars on the field;
  - slavery and Black studies critiques.
- **Sources.** 51 proposed records with the prefix `screq_`, plus a reuse map for the
  existing atlas sources (`ind127_wolfe_1999`, `ind127_harris_1997`,
  `healthgeo05_harris_native_space_2002`).

### Proposed relationships

All use exact existing ids and the atlas vocabulary.

| # | Source → target | Kind | Basis |
| --- | --- | --- | --- |
| 1 | indigenous — settler_colonialism | comparison | Konishi 2019, Kauanui 2016 (abstracts); PhD lift 4.26 |
| 2 | indigenous → settler_colonialism | critique | Konishi, Kauanui, Snelgrove et al.; no identity classification |
| 3 | post — settler_colonialism | comparison | Veracini 2011 and Hoxie 2008 abstracts. Alternative: a directed contribution post → settler_colonialism |
| 4 | settler_colonialism → nationaltradition | critique | Veracini 2013 (disavowal, "empty" settings); Regan contents ("peacemaker myth") |
| 5 | anticolonial — settler_colonialism | comparison | Veracini 2013 (decolonization-era usage); Mamdani 2001 opening |
| 6 | spatialhistory → settler_colonialism | contribution | Harris 2004 abstract; Harris 2020 postscript title |
| 7 | settler_colonialism → cdn_working_class | contribution | Burrill 2019 abstract; PhD lift only 0.66, so a new link. Retargeted from labourhistory on 2026-10-12 (groups packet Q33): Burrill's book is Canadian, and the Canadian working-class group carries Canadian labour history |
| 8 | africanhist — settler_colonialism | comparison | Mamdani 2001; Elkins & Pedersen (contents unread) |
| 9 | black → settler_colonialism | critique | Garba & Sorentino, Sexton; **the source node is uncertain**: this is Black studies theory, not the atlas's Black history |
| 10 | settler_colonialism — racial_formation | comparison | Wolfe 2001, 2016, title level only: **weakest, optional** |

**Considered but not proposed, for lack of a checked source:**
- environment (lift 2.45);
- medical history (Daschuk and Mosby);
- memory and nationalism studies.

Existing edges `edge_776` and `edge_777` are untouched.

## 4. Open questions for the user

1. **Field, paradigm or approach?** The draft says Research field, but much of its use is as
   an analytic lens, as Burrill's "framework" shows. "Approach / theoretical programme"
   (as for `racial_formation`) is the alternative.
2. **Where does it sit relative to Indigenous history and postcolonial critique?**
   - The PhD data put it inside Indigenous/western historiography, not under postcolonial
     studies.
   - The atlas's Indigenous scope note already resists making Indigenous methods a subset
     of European theory. The draft keeps both as comparisons and adds the critique edge.
   - Should the Indigenous theory strand (Coulthard, the Simpsons, Byrd, Tuck & Yang) live
     here or in `indigenous`?
3. **Should decolonization be part of it?** Tuck & Yang argue that decolonization is not a
   metaphor, and resurgence is part of the same reading lists. The draft does not make
   decolonization an approach of this entry. Decolonizing methods already belong to
   `indigenous`, and anti-colonial decolonization to `anticolonial`.
4. **Canadian historians who predate or resist the label.** Carter, Perry, Harris and
   Daschuk are the most cited figures in this neighbourhood, but they are not
   settler-colonial theorists. Should they appear as "historian" or "comparison"? Should
   the strands say so more strongly?
5. **Is there an imperial history home?** The atlas has no entry for imperial or colonial
   history. That would be the natural home for Elkins & Pedersen, Belich, Lester and
   Ballantyne. This request does not create one.
6. **The Black studies critique edge (row 9).** Keep it with `black` as the source,
   downgrade it to a comparison, or keep it inside the entry's strand only?
7. **Francophone scope.** Uptake at Montréal and UQAM is near zero, and Laval is
   unmeasured. Should the entry say so, and should a francophone check follow once the
   Laval downloads finish?

## Method and reproduction

```bash
python3 data/extension-2026/settler-colonialism-request-2026-10-12/settler_colonial_evidence.py
python3 data/extension-2026/settler-colonialism-request-2026-10-12/build_request.py
```

- **Inputs.** `settler_colonial_evidence.py` reads `graph.json` once (about 8 s) and
  `views.json`. It records both SHA-256 hashes in `evidence.json`.
- **Field engagement.** A dissertation engages a co-citation field when it cites at least
  two of that field's clustered works.
- **Literature and draft.** `build_request.py` holds the curated literature and the entry
  draft, and takes PhD counts from `evidence.json`. Its verification notes say exactly
  what was read.
- **Caveats:**
  - Bibliographies record works consulted, not influence.
  - Years are mostly repository dates.
  - 2024–26 is incomplete.
  - Parsing gaps can only undercount.
  - Two settler-colonial-titled theses (Toronto 2011, UVic 2018) cite older or local
    literatures rather than the core, so the core series is a conservative measure of
    vocabulary use.

## Files

| File | Contents |
| --- | --- |
| `README.md` | This request |
| `evidence.json` | All dissertation evidence: series, windows, universities, works, scholars, co-citation, neighbourhood, titled dissertations |
| `uptake-by-window.csv`, `uptake-by-year.csv`, `uptake-by-university.csv` | Uptake tables with denominators |
| `core-works.csv` | Per-work PhD counts with graph ids |
| `cocitation-wolfe-veracini.csv` | Works co-cited with Wolfe or Veracini (k ≥ 4) |
| `settler-titled-dissertations.csv` | Dissertations whose titles use "settler" |
| `literature.json` | 52 verified (or flagged) literature records |
| `entry-draft.json` | Node draft, roster, strands, new people, source records, relationships |
| `settler_colonial_evidence.py`, `build_request.py` | Scripts that produce the above |

## Reviewed decisions (user, 2026-10-12)
- **Type:** settler colonialism is a **field** ("I think settler colonialism is a field
  now"), so the entry is a research-field group, not an approach.
- **Indigenous theory:** works such as Coulthard, Audra Simpson, Leanne Betasamosake
  Simpson, Tuck & Yang and Byrd "can exist in more than one field". They stay in this
  entry's roster and may also appear in `indigenous`. Rosters are not edges, so dual
  placement is allowed.
- **Order:** this entry is drafted alongside the Canadian historiography group entries
  (`../canadian-historiography-groups-request-2026-10-12/`). Its Canadian relationships
  should be settled together with them.
