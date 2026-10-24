# Are we still stuck in the 1980s? Change beyond the baseline

2026-10-23. Analysis of the History PhD citation graph (release 2026-10-23: 7,107 strict History PhDs; the
cohort comparisons below use the 6,794 with a year) to answer one question for the atlas's extension past
2000: the top of the citation table is Anderson, Foucault, Said, J. C. Scott, Thompson — has anything
changed since the 1980s, or do the raw counts only show that everyone cites the same ten books?

Script: `scripts/cohort_change_analysis.py --release <release dir>` (reads the release tables, no graph.json
load; about two minutes). Outputs in this folder. Thesis cohorts: pre-1990, 1990–99, 2000–09, 2010–14,
2015–19, 2020–25. The main contrast is **Canada + United States, 2015–25 (1,893 theses) against 2000–09
(630)**; Europe enters the record only after 2005, so it is compared separately (2015–25 against 2000–14).

## Short answer

1. **The theory canon holds, and the bibliographies are getting older.** Foucault is cited by more theses now
   than in the 2000s (10% of theses in 2000 → 17% from 2010 on). Anderson, Said, Bourdieu, J. Scott and
   Thompson are flat; only Hobsbawm has slipped (12.6% in 2010 → 8%). But that canon is not "the 1980s": it is
   a 1963–1998 layer (Thompson 1963, Foucault 1977, Said 1978, Anderson 1983/1991, Scott 1986, Butler 1990,
   White 1991, Pratt 1992, Trouillot 1995, J. C. Scott 1998). The 1980s share of bibliographies has fallen
   steadily; the 1990s share has not.
2. **Measured against the corpus baseline, there is a clear second layer, published c. 1995–2014**, that
   the 2015–25 cohort cites and the 2000–09 cohort did not: the archive as object (Stoler, Trouillot,
   Hartman, Fuentes, Farge), settler colonial studies (Wolfe, Veracini, Daschuk, Simpson, Coulthard), empire,
   law and sovereignty (Benton, Burbank and Cooper, Armitage, Stern), slavery and capitalism (W. Johnson,
   Beckert, Camp, Morgan), Indigenous borderlands (Hämäläinen, Witgen, DuVal, Blackhawk, O'Brien), the long
   1970s and neoliberalism (Harvey, Cowie, Self, Lassiter), the international turn (Westad, Manela, Moyn), and
   in France Hartog's *régimes d'historicité*.
3. **The second layer is added to the first, not substituted for it.** Theses citing at least one canon figure:
   39.5% (2000–09) → 44.8% (2020–25). Theses citing at least one of twelve post-2000 framework authors: 12.5%
   → 42.3%. Citing both: 9.7% → 25.7%. The right word is *layered*, not *stuck*.
4. **The genuinely post-2000 canon is thin and regional.** Only four works published after 2000 are cited by
   2% or more of 2018–25 theses across the whole record (Stoler 2009, Chakrabarty 2000, Wolfe 2006, Stoler
   2002); 56 reach 2% within Canada and 90 within the US, but one in Europe (Hartog). Nothing published after
   2015 reaches 1.3% yet (Fuentes 2016); works take eight to ten years to peak (Stoler 2009 peaks c. 2015).

## 1. The canon holds, and ages

Share of theses citing each person, centred 3-year window, whole record (`summary/trends.json`):

| | 1995 | 2000 | 2005 | 2010 | 2015 | 2020 | 2024 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Foucault | 7.8 | 9.8 | 11.6 | 17.2 | 17.7 | 17.5 | 16.1 |
| Anderson | 2.6 | 5.6 | 9.2 | 16.0 | 12.9 | 10.6 | 12.0 |
| Hobsbawm | 6.0 | 6.3 | 12.4 | 12.6 | 11.1 | 8.1 | 8.2 |
| Bourdieu | 3.5 | 6.3 | 6.8 | 10.5 | 12.0 | 10.8 | 9.7 |
| Said | 1.7 | 5.6 | 5.2 | 7.8 | 7.6 | 7.4 | 6.2 |
| E. P. Thompson | 10.3 | 4.9 | 4.4 | 7.2 | 5.9 | 6.4 | 4.8 |
| Joan Scott | 5.2 | 10.5 | 5.6 | 5.5 | 6.0 | 5.3 | 5.9 |
| James C. Scott | 3.5 | 2.1 | 3.6 | 8.1 | 9.4 | 7.4 | 7.2 |
| Stoler | 0.9 | 1.4 | 1.6 | 6.4 | 7.8 | 7.1 | 5.9 |
| Cooper | 0.9 | 0.0 | 2.4 | 7.6 | 7.4 | 5.2 | 5.2 |
| Butler | 0.9 | 1.4 | 2.4 | 3.6 | 4.5 | 3.6 | 5.6 |
| Trouillot | 0 | 0 | 0 | 3.3 | 2.0 | 2.9 | 3.9 |
| Wolfe | 0 | 0 | 0 | 0.5 | 1.5 | 2.6 | 3.9 |
| Benton | 0 | 0 | 0 | 1.6 | 2.8 | 2.7 | 3.2 |
| W. Johnson | 0 | 0 | 0 | 2.8 | 2.2 | 3.7 | 3.2 |
| Beckert | 0 | 0 | 0 | 0.9 | 2.5 | 3.1 | 2.8 |
| Hartman | 0 | 0 | 0 | 0.7 | 0.8 | 1.5 | 2.5 |

(Post-2005 shares are diluted by the European theses, which cite the Anglophone canon less.)

**Age profile** (`age-profile.csv`): for the secondary works each thesis cites (books, articles, chapters not
under a primary-sources heading, with a year), each thesis weighted equally.

| Cohort | Canada: median age · under 10 y · over 30 y | US: median · under 10 · over 30 | Europe: median · under 10 · over 30 |
| --- | --- | --- | --- |
| 1990–99 | 14.5 · 38% · 16% | 17 · 30% · 24% | |
| 2000–09 | 16 · 30% · 20% | 17 · 30% · 24% | 16 · 41% · 24% |
| 2010–14 | 18 · 26% · 25% | 17 · 29% · 23% | 20 · 24% · 32% |
| 2015–19 | 19 · 23% · 26% | 18 · 25% · 25% | 22 · 18% · 36% |
| 2020–25 | 23 · 14% · 35% | 22 · 15% · 34% | 27 · 10% · 44% |

Bibliographies have also grown (median 98 works for a 1985 thesis, 227 for a 2015 one), so
`age-profile-controlled.csv` repeats the measure for Canada + US theses citing 100–250 works: median age 15 →
16.75 → 18.5 → 22, share under ten years 33% → 16%. The ageing is not a bibliography-length artefact.

**Which decade lasts.** Share of a cohort's secondary citations by the cited work's decade (Canada; US is the same
within two points):

| Cohort | 1970s | 1980s | 1990s | 2000s | 2010s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1990–99 | 26 | 35 | 17 | | |
| 2000–09 | 14 | 26 | 33 | 13 | |
| 2010–14 | 10 | 17 | 29 | 30 | 4 |
| 2015–19 | 7 | 14 | 25 | 32 | 13 |
| 2020–25 | 8 | 13 | 22 | 29 | 20 |

Each new decade's output takes a smaller slice of the following cohort's reading: 1990s work was 33% of the
2000s cohort's citing, 2000s work 30% of the 2010–14 cohort's, 2010s work 20% of the 2020–25 cohort's. The
1980s layer has decayed (35% → 13%); the 1990s layer has not (33% → 22%). If the field is "stuck", it is stuck
in the 1990s.

**Canon persistence** (`canon-persistence.csv`, Canada + US): the 50 works most cited by the 2000–09 cohort
(median publication year 1989) are cited by 52% of that cohort, 59% of 2010–14, 59% of 2015–19 and 50% of
2020–25. Each later cohort's own top 50 shares 22, 23 and then 15 titles with it, and the median publication
year of the top 50 moves 1989 → 1992 → 1993 → 1996: the canon ages about a year for every three that pass.

## 2. Beyond the baseline: what distinguishes 2015–25 from 2000–09

`distinctive-works-ca-us.csv`, `distinctive-people-ca-us.csv`. For each work (or first author) the shrunk
log-odds ratio of the share of theses citing it in 2015–25 against 2000–09, with a prior drawn from the
corpus-wide share (after Monroe, Colaresi and Quinn 2008), and a z-score. Works everyone cites in both
cohorts (Anderson, Foucault, Thompson) fall out of the ranking by construction; what remains is change.

Of the 40 most distinctive rising works, 19 were published in the 2000s, 9 in the 2010s and 9 in the 1990s
(median 2005). Of the 40 most distinctive fading works, 30 are from the 1980s and 1990s (median 1987). The
rising works, by cluster (share of Canada + US theses 2015–25 against 2000–09):

- **The archive as object.** Stoler, *Along the Archival Grain* 2009 (4.4% vs 0); Trouillot, *Silencing the
  Past* 1995 (4.3 vs 0.8); Stoler, *Carnal Knowledge* 2002 (3.8 vs 1.1); Fuentes, *Dispossessed Lives* 2016;
  Hartman (2.7 vs 0); in France Farge, *Le goût de l'archive*. Stoler is the single strongest riser among
  people (10.6% vs 3.2%, z = 5.3).
- **Settler colonial studies.** Wolfe 2006 (3.1 vs 0); Veracini 2010 (2.4 vs 0); Daschuk 2013; Simpson,
  *Mohawk Interruptus* 2014; Coulthard 2014; J. R. Miller, *Compact, Contract, Covenant* 2009; Carlson 2010;
  Raibmon 2005. Inside the Indigenous TF-IDF family Wolfe goes from 0 to 28% of theses, Daschuk 0 → 24%,
  Tuhiwai Smith 10 → 29%.
- **Empire, law and sovereignty.** Benton, *A Search for Sovereignty* 2010 (2.9 vs 0); Burbank and Cooper
  2010; Armitage 2000; Stern, *The Company-State* 2011; Kramer 2006; Cooper, *Colonialism in Question* 2005;
  Bayly 2004; Ballantyne.
- **Slavery and capitalism.** W. Johnson, *River of Dark Dreams* 2013 (3.1 vs 0); Beckert, *Empire of Cotton*
  2014 (3.1 vs 0); Camp 2004; J. Morgan 2004; Smallwood 2007; Glymph 2008. US-weighted (Johnson 5.7% of US
  theses, 1.0% of Canadian). Covered by the atlas's `capitalismdebates` (1.145).
- **Indigenous borderlands.** Hämäläinen, *The Comanche Empire* 2008 (2.5 vs 0); Witgen 2012; DuVal 2006;
  Blackhawk 2006; Barr 2007; O'Brien, *Firsting and Lasting* 2010; Rushforth 2012; Basso, *Wisdom Sits in
  Places* 1996; Richter 2001.
- **The long 1970s and neoliberalism.** Harvey, *A Brief History of Neoliberalism* 2005; Cowie, *Stayin'
  Alive* 2010; Self; Lassiter 2006; McGirr 2001; Sugrue 1996; Cohen, *A Consumer's Republic* 2003. In Canada
  the sixties and Quebec: Palmer, *Canada's 1960s* 2009; Mills, *The Empire Within* 2010; Igartua 2006;
  Iacovetta, *Gatekeepers* 2006 (24% of the Canadian postwar family, from 7%).
- **The international turn.** Westad, *The Global Cold War* 2005; Manela 2007; Moyn, *The Last Utopia* 2010;
  Mazower; Pedersen 2015; Getachew 2019.
- **The state seen from above.** J. C. Scott, *Seeing Like a State* 1998 (7.8 vs 3.3); *The Art of Not Being
  Governed* 2009. Scott is the second strongest rising person (12.7% vs 5.9%).
- **Emotions** (small): Reddy 2001, Rosenwein 2002, each about 1% of recent theses.
- **Europe** (`distinctive-works-europe.csv`; mostly France, Sweden, Germany, Italy): Hartog, *Régimes
  d'historicité* 2003 (2.6% vs 1.0%, the only post-2000 work above 2% of European theses); Jablonka's 2014
  manifesto; Farge; Boucheron; Charle; Ariès; and a history-education population (Seixas, Wineburg, Rüsen,
  Karlsson) that comes from the Swedish *historiedidaktik* theses.

**Fading** (Canada + US): Canadian national and political history (Granatstein 9.0% → 4.5%, Bliss 5.9 → 1.9,
Owram 6.7 → 2.2, Cook, Berger's *Writing of Canadian History*, Bothwell), Gaddis's *We Now Know*, the social
gospel and labour classics (Allen, Copp, Kealey, Palmer's *Working-Class Experience*), the 1980s women's
history (Bacchi, Vicinus, Kerber, Ross), Hartz and Huntington.

**Robustness.** `robustness-stratified.csv` re-estimates the top 180 contrasts within the 15 universities that
have at least 15 theses in both cohorts (686 vs 456 theses), pooling per-university log-odds. The sign agrees
for 178 of 180. The stratified z-scores are smaller (the stratification discards most of the US record, which
is thin before 2010), and 14 pass |z| ≥ 2 on their own: rising Said's *Orientalism*, Stoler (person and *Along
the Archival Grain*), J. C. Scott (person and *Seeing Like a State*), W. Johnson, Wolfe, Veracini, Hämäläinen
(person and *Comanche Empire*); fading Granatstein, Bliss, Peter Gay, Gaddis.

**Within the baseline.** `distinctive-works-ca-us-baseline-citers.csv` repeats the contrast only among theses
that cite Anderson's *Imagined Communities*, Foucault's *Discipline and Punish* or Thompson's *Making* (380 vs
107). The same risers come top (Trouillot, Stoler, Fanon, Butler, Foucault's *History of Sexuality* and
*Power/Knowledge*, Palmer, Raibmon, Kelm, Milloy, Mills): the change is not a different population displacing
the social historians, it is the same readers adding an archival and colonial layer.

**Within families.** `distinctive-by-family.csv` gives the top risers inside each TF-IDF family (theses with a
dominant family share ≥ 0.4). Gender family: Beattie, Gowing, Walker (crime and gender in early modern
England). Canadian postwar family: Iacovetta, Palmer, Mills, Igartua, Baillargeon, Myers. Indigenous family:
Wolfe, Miller, Tuhiwai Smith, Daschuk, Carlson, Basso, Macdougall. US Civil War family: Howe, Hahn, Camp,
Glymph, Faust, McCurry. Canadian military family: Tim Cook, Vance, Morton, Rutherdale.

## 3. Two layers, not a replacement

`canon-vs-newer.csv` (Canada + US). Canon = Foucault, Anderson, Thompson, Said, Bourdieu, Hobsbawm, Geertz,
Joan Scott. Newer = twelve authors from the rising list (Stoler, Wolfe, Trouillot, Benton, Beckert, W. Johnson,
Cooper, Chakrabarty, Veracini, Hartman, Butler, J. C. Scott; chosen after the fact, so illustrative).

| Cohort | theses | cites any canon | cites any newer | both | newer without canon |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1990–99 | 365 | 18.1% | 1.9% | 1.1% | 0.8% |
| 2000–09 | 630 | 39.5% | 12.5% | 9.7% | 2.9% |
| 2010–14 | 875 | 44.3% | 32.1% | 21.3% | 10.9% |
| 2015–19 | 1,018 | 46.3% | 36.2% | 22.1% | 14.1% |
| 2020–25 | 875 | 44.8% | 42.3% | 25.7% | 16.6% |

## 4. What this says for the atlas after 2000

All 78 school and field entries carry `coverage.reviewed_through: 2000`; the periods end at "Further turns,
c. 1985–2000". `atlas-entries-momentum.csv` scores each entry by the 2000s → 2018–25 citing share of its
representative people (where the roster has a Wikidata QID that the citation graph also has; 32 entry people,
including Richard White, Wolfe, McKay and Valverde, have no row in `data/people-wikidata.json` yet and are
missed).

- **Rising:** `post` (1.38×: Said, Stoler, Cooper), `queer` (1.36×: Foucault, Stoler), `subaltern` (1.47×),
  `conceptual` (Koselleck 2.6 → 4.4%), `africanhist` (Cooper), `anticolonial` (Fanon 1.4 → 3.4%), `memory`
  (Nora, Halbwachs, Derrida), `oral` (Portelli), `identity`/`intersectionality` (Crenshaw).
- **Flat:** `culture`, `language`, `gender`, `social`, `global`, `environment`, `science`, `ssk`.
- **Falling:** every Canadian national entry (`cdn_political_national` 0.38×, `cdn_intellectual_cultural` 0.50×,
  `who_killed_debate` 0.50×, `cdn_regional` 0.54×, `quebec_historiography` 0.67×), `marx` (0.75×),
  `cdn_working_class` (0.71×), `cdn_military` (0.37×), `quant` (0.62×), `modern`, `newleft`, `progressive`.

A data-backed shape for a **period 4, c. 2000–**:

1. **New field or debate entries the citing supports** (strongest evidence first):
   - *The archive as object* (archival turn): Stoler 2002/2009, Trouillot 1995, Farge 1989, Hartman 2008,
     Fuentes 2016, Derrida's *Archive Fever*; no atlas entry covers it.
   - *Settler colonial studies after Wolfe*: the entry exists; extend its chronology past 2000 (Wolfe 2006,
     Veracini 2010, the journal 2011, Daschuk 2013, Simpson and Coulthard 2014) and give Wolfe's person entry
     the data.
   - *Empire, law and sovereignty / the new imperial history*: Cooper and Stoler 1997, Hall 2002, Burton,
     Benton 2002/2010, Burbank and Cooper 2010, Armitage, Stern; partly inside `post`, no entry of its own.
   - *Indigenous borderlands and the "Native New World"*: Richter 2001, DuVal, Blackhawk, Hämäläinen 2008,
     O'Brien 2010, Witgen 2012; extends `native_newcomer` and `indigenous`.
   - *The long 1970s, neoliberalism and the "age of fracture"* (US; Canada's sixties already has `cdn_sixties`).
   - *The international and global turn*: Westad 2005, Manela 2007, Moyn 2010, Bayly 2004, Osterhammel,
     Conrad; extends `global`.
   - *History of emotions* (Reddy, Rosenwein; small but new) and *régimes d'historicité / presentism*
     (Hartog, Jablonka; the one post-2000 framework that travels in Europe).
2. **Person entries the data argues for** (share of Canada + US theses 2015–25): James C. Scott (12.7%, the
   largest figure with no entry; already in the 2026-10-11 proposal), Ann Laura Stoler (10.6%; roster only),
   Frederick Cooper (7.0%; roster only), Trouillot (4.5%), Judith Butler (5.1%; theorist layer), Walter Johnson
   and Beckert (capitalismdebates roster), Lauren Benton (4.6%), Hämäläinen (3.5%), and for Europe Hartog.
3. **Chronology forward for existing entries** in rising order: `post`, `queer`, `subaltern`, `memory`,
   `global`, `indigenous`, `environment` (Cronon flat at 4%, Chakrabarty's climate essay 2009), and the
   `capitalismdebates` and `languages_of_class` groups already past 2000.
4. **Show the decline** rather than extend it: the Canadian national entries and `quant` are read far less by
   recent PhDs; a coverage note with the figures is more honest than a forward chronology.

## Caveats

- Citation is presence, one edge per work per thesis; a frame, a foil and a ritual reference count the same.
- The university mix changes between cohorts (the US record is thin before 2010); the stratified check keeps
  the direction of every contrast but weakens the z-scores.
- The 2020–25 cohort is partly embargoed and skews to the repositories that release quickly.
- Person keys are name keys; namesakes merged after the 2026-10-23 ledger (Richard White is the Stanford one).
- The "newer" set in §3 was chosen from the rising list, so the table illustrates the layering; it does not
  test it.
- European non-English bibliographies parse less cleanly (audit precision 58–63%), so European shares are low.

## Files

| File | Content |
| --- | --- |
| `age-profile.csv`, `age-profile-controlled.csv` | age of cited secondary works by cohort and region; length-controlled |
| `distinctive-works-ca-us.csv`, `distinctive-people-ca-us.csv` | log-odds 2015–25 vs 2000–09, Canada + US |
| `distinctive-*-ca-us-baseline-citers.csv` | the same among theses citing Anderson / Foucault / Thompson |
| `distinctive-*-europe.csv` | Europe 2015–25 vs 2000–14 |
| `distinctive-*-family-N.csv`, `distinctive-by-family.csv` | within each TF-IDF family |
| `robustness-stratified.csv` | institution-stratified re-estimate of the top contrasts |
| `post2000-works.csv` | works published 2000+ by share of 2018–25 theses, with regional shares |
| `canon-persistence.csv`, `canon-vs-newer.csv` | the 2000s top 50 later; canon and newer layers by cohort |
| `atlas-entries-momentum.csv` | atlas field entries scored by their representative people's citing trend |
| `rising-people-atlas.csv` | top 150 rising first authors against the atlas roster (QID match) |

## 5. Is there a new big debate? Positioning, breadth and candidates

Added 2026-10-23 after the user reframed the question: the *narrative* is stuck in the 1980s, Thompson
challenged by Joan Scott with Foucault and Derrida behind her, and PhD students still position themselves in
that debate; no later debate is cited by everyone; Latour and Haraway are nowhere near that dominance;
James C. Scott entered History c. 2000 with *Seeing Like a State* and is a different thing from the linguistic
turn. Script: `scripts/debate_positioning_analysis.py` → `debate-dyads.csv`, `breadth.csv`,
`breadth-rising.csv`, `theorists-by-cohort.csv`. Three measures: co-citation of both sides of a debate by
cohort; breadth, the number of the 18 TF-IDF families (theses 2010–25 with a dominant family ≥ 0.4, 2,791
theses) in which a figure is cited by at least 3% of the family's theses; and the share of theses citing
each theorist by cohort.

### The 1980s debate is cited as canon, not as a debate

Share of Canada + US theses citing both sides:

| Pair | 2000–09 | 2010–14 | 2015–19 | 2020–25 |
| --- | ---: | ---: | ---: | ---: |
| Thompson and Joan Scott (either work) | 1.3 | 1.0 | 0.7 | 1.5 |
| Thompson's *Making* and Scott's "Gender" / *Gender and the Politics* | 0.3 | 0.7 | 0.2 | 0.8 |
| Thompson, Scott and Foucault, all three | 0.6 | 0.6 | 0.1 | 0.7 |
| Joan Scott and Derrida | 0.0 | 0.1 | 0.1 | 0.3 |
| Any text of the exchange (Stedman Jones 1983, Palmer 1990, Joyce 1991/94, Toews 1987, Canning 1994, Spiegel 1990, Eley 2005) | 2.9 | 2.3 | 1.1 | 1.8 |
| …and Thompson or Scott | 1.4 | 1.1 | 0.4 | 1.3 |

Thompson alone is cited by 6–7% of Canada + US theses in every cohort since 2000, Joan Scott by 6.5–8.9%
(8.9% in 2020–25, her highest), Foucault by 13.5–18%. The two sides are cited together by about 1% of theses,
and the texts in which they argued (*Languages of Class* 5 theses in 2010–25, *Descent into Discourse* 5,
*Visions of the People* 7, Toews 3, Canning 8) are almost absent. Derrida is cited by 1–1.5% and never
together with Scott. So the debate survives as a settled canon, Scott's "Gender" and Foucault as framework and
Thompson as origin, each cited across most fields (Thompson reaches 3% in 13 of 18 families, Scott 12,
Foucault 18) at a modest depth (mean family share 5.8%, 5.6% and 19.3%). Students cite the result of the
debate; they do not re-fight it.

### No later pair reaches the same breadth and two-sidedness

| Candidate | 2000–09 | 2010–14 | 2015–19 | 2020–25 | families ≥ 3% (2010–25) |
| --- | ---: | ---: | ---: | ---: | --- |
| J. C. Scott and Foucault | 2.1 | 4.6 | 4.7 | 4.0 | J. C. Scott 14 |
| J. C. Scott and (Thompson or J. Scott) | 1.4 | 3.1 | 2.6 | 3.1 | |
| Stoler and (Thompson or J. Scott) | 1.8 | 2.5 | 1.9 | 2.5 | Stoler 11 |
| Wolfe and Veracini | 0.0 | 0.2 | 2.1 | 3.0 | Wolfe 3, Veracini 2 |
| Wolfe and his Indigenous critics (Tuck and Yang, Simpson, Coulthard) | 0.0 | 0.0 | 0.9 | 2.3 | |
| Stoler and Trouillot | 0.2 | 0.7 | 1.0 | 1.7 | Trouillot 5 |
| (Beckert or W. Johnson) and Baptist | 0.0 | 0.0 | 1.5 | 1.1 | Beckert 6, Johnson 4 |
| Chakrabarty and Cooper | 0.6 | 1.4 | 1.0 | 1.1 | Chakrabarty 3, Cooper 6 |
| Chakrabarty and Foucault | 0.6 | 2.4 | 1.2 | 1.9 | |
| Chakrabarty and (Thompson or J. Scott) | 0.3 | 1.0 | 0.5 | 0.9 | |
| Wolfe and (Thompson or J. Scott) | 0.2 | 0.2 | 0.3 | 1.1 | |
| Latour and Shapin | 0.2 | 0.7 | 0.9 | 0.7 | Latour 10, Shapin 3 |
| Latour and Haraway | 0.3 | 0.7 | 0.5 | 0.1 | Haraway 2 |
| Moyn and Hunt's *Inventing Human Rights* | 0.0 | 0.2 | 0.5 | 0.3 | Moyn 4 |
| Pomeranz and Brenner | 0.0 | 0.0 | 0.1 | 0.2 | Pomeranz 2 |
| Guldi and Armitage, *History Manifesto* (cited at all) | 0.0 | 0.0 | 0.2 | 0.3 | 0 |
| For scale: Anderson and Foucault | 3.2 | 6.7 | 3.4 | 3.5 | |
| Bourdieu and Foucault | 2.9 | 3.8 | 2.4 | 3.1 | |

Reading, figure by figure:

- **James C. Scott** is the one entrant since 1998 with canon-level breadth: cited by 12–13% of Canada + US
  theses in every cohort since 2010, in 14 of 18 families at 3% or more (mean family share 9.9%, behind only
  Foucault, Anderson, Bourdieu and Hobsbawm). But it is *Seeing Like a State* (182 theses 2010–25, nine
  families) that History took up, not *Weapons of the Weak* or *Domination and the Arts of Resistance* (60 and
  57, four families each), and there is no opposing side co-cited with him: he is a framework, not a debate,
  and his nearest companion is Foucault (4–4.7% co-cited). The user's reading holds: a different thing from
  the linguistic turn, fifteen years later.
- **Latour and Haraway** are confirmed nowhere near: Latour 3.5% of Canada + US theses in 2020–25 (peak 4.5%
  in 2015–19), broad but shallow (10 families, mean 4.1%, *Reassembling the Social* 39 theses, *We Have Never
  Been Modern* 20); Haraway 1.5%, two families, never above 7% even in the environment family; the two are
  co-cited by 0.1% of theses.
- **Chakrabarty** (user: "maybe emerging as a challenger to the older debate") is rising again in Canada + US
  (2.8% in 2015–19 → 4.5% in 2020–25; 4.7% in 2010–14) but narrow: 3 families at 3%, 18% of the postcolonial
  family and 1–2% elsewhere. He is co-cited with Foucault (1.9%) more than with Thompson or Scott (0.9%), and
  with Cooper, his nearest critic, at a flat 1%. *Provincializing Europe* reaches two families. He reads as a
  framework inside the postcolonial field, not yet a cross-field challenger.
- **Wolfe** is the fastest riser in the record (0.5% of Canada + US theses in 2000–09 → 3.5% → 6.6% in
  2020–25; 31% of the Indigenous family) and the only post-2000 figure around whom a *two-sided* citing is
  forming: Wolfe with Veracini (0 → 3.0%) and Wolfe with his Indigenous critics, Tuck and Yang, Audra Simpson,
  Coulthard (0 → 0.9 → 2.3%), both still rising in the 2020s. It is confined to three families (Indigenous,
  Canadian postwar, postcolonial) and co-cited with Thompson or Scott by 1.1% of theses. If a new debate is
  emerging, this is its shape: settler colonialism and its Indigenous critique, regional (Canada 4.2% of
  theses, US 3.6%, Europe 0.1% for the 2006 essay), not yet general.
- **Stoler** has the breadth (11 families, mean 7%) and the momentum (3.2% → 10.7%), and is the one newer
  figure regularly co-cited with the old debate (with Thompson or Scott 2.5%, with Foucault more); the
  archive-as-object cluster (Stoler and Trouillot 1.7% and rising) has no opposing side.
- The other candidates (slavery and capitalism with Baptist's critics, Moyn against Hunt, Pomeranz against
  Brenner, the *History Manifesto*) are cited by 0.2–1.5% of theses together and do not travel across fields.

**Europe differs.** European theses cite Thompson and Scott little; their shared frame is time, memory and
historicity: Ricoeur 4.2% of all theses (mostly European), Nora 4.0%, Koselleck 3.3%, Hartog 2.3%, Certeau
3.4%. Hartog's *régimes d'historicité* is the nearest thing to a post-2000 debate text there.

### Verdict

The user's hypothesis survives with one amendment. There is no new debate everyone feels the need to cite:
every post-1995 pair is co-cited by under 3% of theses, and the only figures with canon breadth since then,
James C. Scott and Stoler, are frameworks without an opposing side. But the 1980s debate is not being
re-fought either: its texts are almost uncited, and what persists is the settled result, Scott and Foucault as
the shared theoretical floor with Thompson as the origin story, at a stable 6–9% each and in most fields.
"Stuck" is the right word for the *floor*; the *debate* ended, and nothing has replaced it as a debate. The
one two-sided, rising candidate is settler colonialism (Wolfe against Veracini and against Tuck, Simpson and
Coulthard), regional and young.

For the atlas, this argues for the period-4 narrative being framed as *layering without a new debate*: a
stable theoretical floor from the 1980s, a set of regional frameworks (settler colonialism, the archive, empire
and sovereignty, the long 1970s) added under it, and one emerging two-sided debate to watch.

Caveats: co-citation within a thesis is a weak proxy for positioning (a thesis can cite both sides in
different chapters, or position itself against a figure it cites once). Family breadth depends on the TF-IDF
families (k = 18, main graph; the French and Swedish families dilute the Anglophone measures). Person keys are
first-author keys, so edited volumes and co-authored works count to the first name only.

## 6. New fields: engagement, family shares and a snowball around the founders

Added 2026-10-23 (user: "we also see new fields: environmental history in particular alongside settler colonial
studies; maybe the history of emotions?" and "some kind of snowball measure to see how the network of scholarship
around Cronon, Worster and White grew across the years … the same for the history of sexuality, queer history").
Scripts: `scripts/field_emergence_analysis.py` (→ `field-engagement.csv`, `field-seeds-resolved.csv`,
`family-shares-by-cohort.csv`) and `scripts/field_snowball_analysis.py --region CA|US` (→
`snowball-summary-<region>.csv`, `snowball-members-<region>.csv`).

### 6.1 Field engagement: share of theses citing two or more of a field's core authors

Seed lists of 13–50 authors per field (`field-seeds-resolved.csv`; one seed can be a passing citation of Cronon
or Wolfe, two is a field being read). Canada + US:

| Field | 1990–99 | 2000–09 | 2010–14 | 2015–19 | 2020–25 | CA 2020–25 | US 2020–25 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Environmental history | 1.6 | 5.7 | 9.5 | 11.3 | 9.9 | 10.2 | 9.7 |
| Settler colonial studies | 0 | 3.2 | 4.2 | 9.0 | 11.0 | 15.2 | 6.8 |
| The archive as object | 0 | 3.3 | 7.1 | 7.6 | 10.4 | 9.0 | 11.8 |
| Global / transnational | 0.3 | 1.3 | 7.1 | 7.3 | 7.8 | 7.2 | 8.4 |
| Borderlands | 0 | 1.1 | 3.7 | 6.3 | 6.7 | 5.5 | 7.9 |
| History of capitalism | 0.3 | 0.8 | 2.9 | 5.6 | 5.9 | 3.5 | 8.4 |
| Medical and health | 1.1 | 3.0 | 4.8 | 5.8 | 6.1 | 8.5 | 3.6 |
| Spatial turn | 0.3 | 4.1 | 6.3 | 6.8 | 5.1 | 5.5 | 4.8 |
| Human rights | 0 | 0.5 | 2.3 | 3.3 | 3.0 | 1.8 | 4.1 |
| History of emotions | 0 | 0.8 | 0.9 | 2.5 | 3.0 | 3.5 | 2.5 |
| Animal history | 0 | 0 | 0.6 | 0.9 | 1.3 | 1.6 | 0.9 |
| Disability history | 0 | 0.3 | 1.0 | 1.0 | 0.9 | 1.4 | 0.5 |
| Sensory history | 0 | 0.6 | 1.4 | 1.6 | 0.7 | 0.7 | 0.7 |
| Digital history | 0.3 | 0.2 | 0.8 | 0.5 | 0.8 | 1.2 | 0.5 |
| Affect theory | 0 | 0 | 0.5 | 0.5 | 0.6 | 0.5 | 0.7 |
| *Gender (scale)* | 5.8 | 14.4 | 23.1 | 22.8 | 20.1 | 27.3 | 13.1 |
| *Labour (scale)* | 5.8 | 11.4 | 12.5 | 13.4 | 9.4 | 13.2 | 5.7 |

Reading: **environmental history is a 2000s arrival that plateaued at about 10% from 2010**; **settler colonial
studies is the 2010s arrival still rising**, and in Canada (15%) it has overtaken environmental history (10%);
the archive, global, borderlands and capitalism are the other 2010s arrivals (US-weighted for capitalism and
borderlands, Canada-weighted for medical and settler colonial). **The history of emotions is real but small**:
3% of theses, tripled since 2010, with affect theory flat at 0.6%. Animal, disability, sensory and digital history
stay near or under 1%. Labour is declining (13% → 9%; 6% in the US); gender is the largest field at 20–27% and
flat since 2010. In Europe only global history (3.4%) and gender (4.2%) pass 3%.

The seed-free check (`family-shares-by-cohort.csv`, share of placed theses whose dominant TF-IDF family is each
family) agrees on direction: in Canada the postcolonial/empire family rises 2.6% → 12.3%, the environment/state
family 2.6% → 5.7%, the Atlantic/slavery family 2.2% → 5.7%, while the Canadian postwar social family falls 38.5%
→ 20.5% and military 13% → 3.3%; in the US the Atlantic/slavery family rises 4.4% → 12.9% and postcolonial 4.9%
→ 11.4%, Civil War/South falls 24.6% → 8.5%, and the environment/state family *falls* 7.7% → 4.7% even though
10–11% of US theses cite two or more environmental historians: environmental history is read in the US more than
it is the subject of theses, which is the diffusion the snowball shows below.

### 6.2 Snowball: the network of scholarship around a field's founders

Founding works fixed across cohorts (environment: Cronon's *Changes in the Land*, *Nature's Metropolis* and
"The Trouble with Wilderness", Worster's *Dust Bowl*, *Rivers of Empire* and *Nature's Economy*, White's
*Organic Machine*, Crosby's *Ecological Imperialism*, Merchant's *Death of Nature*; sexuality/queer: Chauncey,
D'Emilio ×2, Weeks, Sedgwick, Kinsman, Halperin, Canaday, Duggan, Meyerowitz, Rupp, Boyd; settler colonial:
Wolfe 1999 and 2006, Veracini 2010, Tuck and Yang 2012; emotions: Reddy, Rosenwein ×2, Stearns ×2, Plamper;
Indigenous: *Middle Ground*, Richter, Deloria, Tuhiwai Smith, J. R. Miller; capitalism, global, memory, and
gender and labour for scale). Per region and cohort: *seed citers* = theses citing a founding work; the
*neighbourhood* = works cited by at least 3 of a random sample of 15 seed citers and at least three times as
often by them as by the cohort (300 draws; averaged, so cohorts of different size are comparable); *recent* =
neighbourhood works published within ten years of the cohort's midpoint; *entrants* = works joining the
full-set neighbourhood for the first time. Two rounds of snowballing were tried and dropped: the second round
amplifies itself (a large network pulls in general theses, which enlarge it again), so the measure is the
one-step neighbourhood of the founders.

**Canada**

| Field | cohort | seed citers | neighbourhood (eq.) | recent | median year | entrants named |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Environment | 2000–09 | 3.9% | 14 | 3 | 1986 | *Middle Ground* |
| | 2010–14 | 7.4% | 37 | 9 | 1996 | Pratt, J. C. Scott, Jasen, MacEachern, Loo, Nash |
| | 2015–19 | 8.6% | 27 | 7 | 2000 | Innis, Parr *Sensing Changes*, Lutz, Piper, Loo |
| | 2020–25 | 7.2% | 17 | 3 | 2003 | Wolfe 2006, Wolfe 1999, Tuck and Yang |
| Settler colonial | 2015–19 | 3.1% | 51 | 13 | 1999 | Perry, Van Kirk, Tuhiwai Smith, Miller, Lutz, Harris |
| | 2020–25 | 8.5% | 51 | 17 | 2006 | Coulthard, Simpson, Carter, Miller *Compact*, McKay, Daschuk |
| Indigenous | 2000–09 | 7.3% | 35 | 9 | 1990 | Owram, Richter, Carter, Trigger, Tobias |
| | 2010–14 | 8.9% | 42 | 12 | 1996 | Pratt, Perry, Van Kirk, Trigger, Tough, Ray |
| | 2015–19 | 10.4% | 55 | 14 | 1999 | Lutz, Carlson, Macdougall, Kelm, Milloy, Cruikshank |
| | 2020–25 | 11.5% | 50 | 15 | 2006 | McCallum, Coulthard, Rushforth, Hill, Nickel |
| Sexuality/queer | 2015–19 | 4.5% | 24 | 3 | 1997 | Jackson, Valverde, Foucault D&P, Smith, Kinsman 2010 |
| | 2020–25 | 3.7% | 17 | 3 | 1998 | Foucault HoS, Owram |
| Emotions | 2020–25 | 3.5% | 12 | 0 | 1999 | none |
| Memory | 2015–19 | 6.7% | 14 | 1 | 1991 | Vance, Eksteins, Nora 1989, Moss, Fussell |
| *Gender* | 2000–09 | 7.0% | 38 | 12 | 1991 | Marks, Copp, Scott 1988, Cook, Walkowitz |
| | 2020–25 | 11.3% | 8 | 0.5 | 1993 | Srigley, Sangster, Nicholas, Lears |
| *Labour* | 2000–09 → 2020–25 | 4.4% → 5.3% | 33 → 6 | 7 → 0 | 1987 → 1983 | — |

**United States**

| Field | cohort | seed citers | neighbourhood (eq.) | recent | median year | entrants named |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Environment | 2000–09 | 10.2% | 10 | 3 | 1990 | J. C. Scott, Limerick |
| | 2010–14 | 10.8% | 19 | 5 | 1996 | Rodgers, Nash, Wiebe, Jacoby, White *Misfortune* |
| | 2015–19 | 11.4% | 17 | 3 | 2000 | Cohen, *Middle Ground*, Hämäläinen, Self, DuVal, Deloria |
| | 2020–25 | 10.0% | 19 | 4 | 2005 | W. Johnson, Perdue, O'Brien, Jacobs, Basso, McNeill |
| Sexuality/queer | 2010–14 | 8.5% | 42 | 12 | 1997 | Peiss, Cohen, Sugrue, May, Bederman |
| | 2015–19 | 7.1% | 41 | 9 | 2001 | Sánchez, Shah, Self, Pascoe, Omi and Winant |
| | 2020–25 | 4.8% | 30 | 8 | 2007 | Muhammad, Cowie |
| Settler colonial | 2015–19 | 3.9% | 34 | 15 | 2005 | *Middle Ground*, Blackhawk, Witgen, Hämäläinen, O'Brien, Hixson |
| | 2020–25 | 5.0% | 41 | 13 | 2008 | Jacobs, W. Johnson, Ostler, Miles, Chang, Saunt |
| Indigenous | 2010–14 → 2020–25 | 8.3% → 8.8% | 27 → 32 | 10 → 6 | 1998 → 2005 | Deloria 2004, DuVal, Gallay … Fuentes, Camp |
| Capitalism | 2015–19 | 12.0% | 23 | 6 | 2000 | Rothman, Foner, Camp, White *Railroaded*, Hahn, Glymph |
| | 2020–25 | 10.2% | 29 | 6 | 2003 | *Middle Ground*, Howe, Fuentes, Wood, Williams 1944, Sinha |
| *Gender* | 2000–09 → 2020–25 | 9.8% → 6.3% | 35 → 10 | 14 → 1 | 1992 → 2000 | — |
| *Labour* | 2010–14 → 2020–25 | 6.1% → 4.3% | 43 → 8 | 10 → 0 | 1996 → 1995 | — |

What the snowball separates:

- **Growing and renewing networks:** Indigenous history in Canada (neighbourhood 35 → 50 works, recent works 9
  → 15, median year 1990 → 2006) and settler colonial studies in both countries (the largest neighbourhood of any
  field, 51 works in Canada, with the most recent membership: 17 works within ten years, median 2006). These are
  the fields whose scholarship is still being added to and still read as a body.
- **Stable but ageing networks:** environmental history in the US (10–11% of theses cite a founder in every
  cohort; neighbourhood flat at 17–19 works; recent works 3–5; median year moving 1990 → 2005 with the cohorts) and
  Canadian memory studies (14 works, one recent, Great War memory: Vance, Fussell, Mosse).
- **A network being absorbed:** environmental history in Canada peaked in 2010–14 (37 works, 9 recent: Jasen,
  MacEachern, Loo, Nash) and has since halved (17, 3 recent); its only new entrants in 2020–25 are Wolfe and Tuck
  and Yang, and in the US the entrants are *Middle Ground*, Hämäläinen, DuVal, O'Brien, W. Johnson. The scholarship
  around Cronon, Worster and White is now cited *with* Indigenous, settler colonial and capitalism works rather than
  with new environmental ones: the field has diffused into its neighbours, which is also why its dominant-family
  share falls in the US while its readership holds.
- **Networks that dissolved as their concepts generalised:** gender (founders cited by 7–11% of Canadian theses
  throughout, neighbourhood 38 → 8 works, recent 12 → 0.5) and labour (33 → 6). By construction a work that
  everyone cites drops out of a neighbourhood (lift < 3), so this is what success looks like in the measure:
  Scott, Butler, Davidoff and Hall are cited across all fields with no distinct company any more. Sexuality and
  queer history is on the same path in the US: a large neighbourhood (42 → 30) but founders cited by fewer theses
  (8.5% → 4.8%), with the entrants (Shah, Pascoe, Self, Muhammad, Cowie) from histories of race, the state and the
  family rather than from sexuality.
- **Readerships without a network:** the history of emotions (3% of theses cite Reddy, Rosenwein or Stearns; no
  co-cited neighbourhood, zero recent works) and the global turn (seed citers 3–4%; neighbourhood under 10 works):
  cited singly, as a gesture, not read as a body. Emotions is new, rising and not yet a field in these theses.

### 6.3 For the atlas

- Environmental history is the 2000s field and should be dated as such in period 4 (its readership reached
  10% around 2010 and stopped growing); its chronology forward should show the absorption into Indigenous and
  settler colonial history (Loo, Piper, Parr, Binnema and Sandlos in Canada; the "Native New World" works in the US)
  rather than a second environmental wave.
- Settler colonial studies is the 2010s field, still rising, Canada-led, with the largest and youngest network;
  the Indigenous critique (Coulthard, Simpson, Tuck and Yang) belongs inside the entry, as §5 found.
- The history of emotions warrants a short entry or a strand (Reddy, Rosenwein, Stearns, Plamper, Frevert,
  Boddice), dated 2001–, with the honest note that in these theses it is 3% and not yet a network.
- Gender's dissolution into the general vocabulary is itself an event for the gender entry's chronology.

Caveats: the seed lists are mine; the snowball depends on the founders chosen and on `lift ≥ 3`, so concepts
that spread to everyone fall out by construction; 15 seed citers is coarse (the equalised size has a standard
deviation of roughly 5–8 works across draws); Europe was not run (too few seed citers per field); sexuality and
queer history in Canada has 16–23 seed citers per cohort, at the edge of the measure.
