# Sherry Olson: person entry draft (Canadian persons, Tier 2, pe139)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- Date label now ends with 'Rebuilding a Neighbourhood of Montreal' (with Dufaux) 2014, the chapter that anchors the HGIS edge (finding 10).
- Rel_01 identifies the ten-surname micro-sample of 1997 as the Protestant sample only, distinct from the Catholic baptismal sample and from the twelve-surname sampling of the 2011 book with Thornton, known from publisher copy (finding 8).
- The `suburban_building` focus revision now reads as the review gives it: 'Olson’s Baltimore (1980) examines city growth through boom-and-bust ‘long swings,’ with roughly eighteen years between peaks.' (finding 9). The chapter-2 conflict-of-interest exclusion stands.

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json). The user (2026-10-14):
"she is the key HGIS person in Canada". The evidence base started from
[../../quebec-historiography-2026-10-14/evidence-quebec.md](../../quebec-historiography-2026-10-14/evidence-quebec.md) §3,
which judged an entry supportable as an HGIS method framework, not as a Quebec figure.

**Disclosure.** Jim Clifford co-wrote chapter 2 of Bonnell and Fortin, eds., *Historical GIS
Research in Canada* (2014): Beard, Macfarlane and Clifford, "Mapping the Welland Canals and the
St. Lawrence Seaway with Google Earth". It does not mention Olson and is not used. The editors'
introduction, chapter 1 (Lutz et al.) and chapter 8 (Dufaux and Olson) are used.

**Validation (historical, drafting stage).** The live graph is revision **1.138** (Ouellet). A throwaway script in the session
scratchpad applies the draft in memory: the node; new people `sherry_olson` (with `node_id`) and
`patricia_thornton`; 17 new sources; 2 edges (`edge_993`, `edge_994`); 3 roster rows, two of them
carrying those edge ids; the two proposed strand-list additions and two focus text revisions
(each `old` matches exactly once). Result: **0 errors and 7 warnings, the same 7 as the
unmodified graph** (180 nodes, 994 edges). All source ids resolve and both `target_strand`
addresses exist.

## What is proposed

- **Node `sherry_olson`.** The twelve standard person keys. The date label lists dated works,
  1979–2011, with MAP "from 2000". The description has five sentences:
  1. Baltimore (1980) as city building in "long swings", in her words;
  2. sampled, linked and mapped Montreal families (1997, her words);
  3. MAP as a collective HGIS from 2000, in her and Dufaux's words;
  4. reception and contest: the 2014 editors ("led by" Olson *and* Sweeny), the Victoria team's
     "a model of spatial history" (with Gilliland flagged as her collaborator), and Sweeny's 2009
     critique of GIS ontology;
  5. Peopling the North American City (2011) with Thornton.
- **People.** `sherry_olson` is new (`people_update.new: true`). `patricia_thornton` is new
  (`new_people`), roster only; her identity note distinguishes her from `john_thornton` and from a
  Wikidata painter namesake.

### Edges

| # | Target | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | spatialhistory | contribution | Households on the cadastral lot, 1997–2014 | historical_gis | new row, edge_id |
| 2 | urbanhistory | contribution | City building in long swings, 1979–80 | suburban_building | new row, edge_id |

- **Roster additions:**
  - `spatialhistory`: Olson, historian, linked to edge 1;
  - `urbanhistory`: Olson, historian, linked to edge 2;
  - `urbanhistory`: Thornton, historian, no edge.
  - The edges set `roster_row: null`, as in the Carson draft: a new person's row is carried by
    `roster_additions` with its `proposal_id`.
- **For the batch (not consumed from drafts):**
  - `strand_list_additions`: Olson into `historical_gis` and `suburban_building`.
  - `text_revisions`: one dated sentence appended to each of those two strand foci.
- **No critique edge.** In the texts read she criticises no atlas entry in her own words.

## Guarding against the 1.136 faults

- **"First"/"pioneer".** The entry makes no founding or priority claim.
  - "Pioneering" appears only inside the Lutz et al. quotation, attributed to them.
  - The editors say "Since the 1990s, only a small number" of Canadian HGIS projects, and give the
    US and British national repositories as "some of the most important work in the field" (p. xi).
  - The British strand (Gregory and Southall 1998) is named as a separate aggregate tradition.
- **Co-leadership kept.**
  - MAP is "led by" Olson *and* Sweeny (editors, p. xii).
  - Sweeny built the Cane-map framework (Olson 2004, p. 165).
  - The project was begun by "a dozen Montreal scholars and a dozen graduate students" in 2000
    (Dufaux and Olson, p. 176 n. 1).
  - Sweeny describes himself as co-director (2009).
- **Independence flagged.** Lutz et al.'s chapter includes Jason Gilliland, her MAP collaborator
  and co-author. The edge says so.
- **Snippet witnesses labelled.**
  - Sager (CHR 2012) and Horner (HS/SH 2013) are read only in their opening paragraphs (MUSE
    excerpts via OpenAlex).
  - Peopling itself is unread; "twelve surnames" is publisher copy and is attributed to it.
- **Abstracts labelled.** The 1979, 1998, 2010 and 2011 articles and the MAP repository record.
- **Dating.** The in-period evidence is Baltimore (1980) and the 1997 chapter. MAP (2000) and
  the 2004–14 texts are labelled as after 2000, and the node text dates each.
- **No PhD or citation counts in text.** `citation_evidence` holds the cited-people.csv row as
  metadata.
- **Personal data.**
  - The birth year and the family statement on Wikidata are not used.
  - "American-born" rests only on the Wikidata description and citizenship statement, so the node
    says "at Johns Hopkins and then McGill" (LoC) instead.

## Verification: what was read

### Read in full or in the pages cited

- **"Le peuplement de Montréal"** (*Atlas historique du Québec: Population et territoire*, 1997),
  pp. 81–94 and endnotes.
  - Source: the CIEQ PDF deposited on depot.erudit.org. This is not the Érudit journal platform; it
    served the file with no challenge. The atlas.cieq.ca URL is a PDF.js viewer.
  - Note 1 records GIS mapping "sur ATLAS GIS" in the McGill SIG laboratory, and Thornton's
    demographic analysis.
- ***Baltimore* (1980)**: copyright page, contents, acknowledgments (p. vii), introduction
  (pp. ix–x). Source: the Maryland State Archives electronic edition (olson00.html). The chapters
  were not read.
- **"Ethnic Partition of the Work Force in 1840s Montréal"** (*Labour/Le Travail* 53, 2004),
  pp. 159–165, 173–174, 192. Source: the journal PDF.
- **Bonnell and Fortin, Introduction** (2014), pp. xi–xiii, xvii, xix n. 12. Source: the publisher's
  open-access front-matter PDF.
- **Lutz, Dunae, Gilliland, Lafreniere and Harvey**, ch. 1 (2014), p. 11 and n. 31 (pp. 23–24).
- **Dufaux and Olson**, ch. 8 (2014), pp. 153, 155, 175–176 and nn. 1–2.
- **Sweeny, "Rethinking Boundaries"** (*Digital Studies*, 2009), opening and section 1. Source: the
  Internet Archive capture; the live site was not requested.

The 2014 PDFs were downloaded fresh from the University of Calgary repository. The earlier Quebec
session's text extracts (qc-olson2) were used only to locate passages.

### Abstracts, title level, snippets

- **Abstracts** (OpenAlex):
  - "Baltimore Imitates the Spider" (1979);
  - "Claims on Housing Space" (1998);
  - Gilliland and Olson (2010);
  - Gilliland, Olson and Gauvreau (2011);
  - the MAP repository record (undated; the Memorial URL now redirects);
  - the 1989 and 1991 infant-mortality papers (used only in "considered").
- **Title level:** "Occupations and Residential Spaces" (*Historical Methods*, 1989); Olson and
  Hanna, *Historical Atlas of Canada*, vol. 3, plate 30 (1990).
- **Snippets:** Sager (2012) and Horner (2013), opening paragraphs.

### Could not be read

- **In-period reviews of *Baltimore*:**
  - Browne (AHR 1981);
  - Cox (JAH 1981);
  - Fries (*Technology and Culture* 1981);
  - Vill (JEH 1981; the Cambridge first-page preview image is illegible at preview resolution);
  - Muller (JIH 1982);
  - Kirby (*Journal of Historical Geography* 1982).
  - They sit behind JSTOR, OUP and Elsevier walls, and JSTOR and OUP returned challenges. No
    in-period judgement of the book is reported.
- **Reviews of *Peopling*:**
  - Jolivet (RHAF), Gossage (*Globe*), Dillon (CQD) and Turmel (RS) are all on Érudit; not tried.
  - Lafreniere (JHG 2012) is in Elsevier. He was Gilliland's student, so not independent anyway.
  - The full texts of Sager and Horner: MUSE, and the HS/SH site challenge.
- ***Peopling the North American City*** itself.
- **Sweeny's 2020 introduction** to *Sharing Spaces*, the festschrift. Closed.
- **Other articles:**
  - "Claims on Housing Space" full text (UTP Journals Cloudflare challenge).
  - The 1989 *Annales de démographie historique* article (Persée captcha).
  - The 1989 *Historical Methods* article (closed).
- **GEOinfo 2003 (Gilliland and Olson).** The Western repository has moved and no capture exists.

No bot challenge was solved; each was left at the first refusal. No email or other personal
identifier was sent to any service. OpenAlex was queried with the repo's API key and no `mailto`.

## Lutz et al.'s n. 31: citation slips

It gives:
- Historical Methods 22 as 81–99. Crossref has 81–96.
- *Labour/Le Travail* 53 as 1–66. The journal has 159–202.
- *Urban Geography* as "33 (January 2010)". The DOI record has 31(1).

The draft uses the publishers' data.

## Open questions for the editor

1. **`quebec_historiography` roster row?** Her 1997 chapter is in the CIEQ's *Atlas historique du
   Québec*, and her 2004 note engages Ouellet, Greer and Lamonde. But the Quebec self-accounts read
   do not name her. A contributor row is defensible; not proposed.
2. **`digital_history`.** No digital-history text read names her, so no edge. Sweeny 2009 appeared
   in *Digital Studies*.
3. **Critics.** In-period critics of *Baltimore* and of the method are unread. Reading the 1981–82
   reviews (library access) and Sweeny's 2020 festschrift introduction would let the entry
   record criticism of her own work, not only Sweeny's critique of GIS.
4. **Strand fit.** For edge 2, `suburban_building` was chosen over `mobility_records`.
5. **Thornton's roster row.** It is on `urbanhistory` only. A `demography` row could follow if the
   1859 cohort studies are read.
