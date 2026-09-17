# Four requested fields: revision 1.118

Added dedicated **Spatial history / Historical geography**, **Intellectual history**, **Labour history**, and **Ethnohistory** entries. Benjamin Hoy’s supplied chart prompted the coverage comparison; its small annotations were not used as verified bibliographic evidence. The user explicitly requested these four fields. The additions preserve the atlas’s substantive coverage through 2000, with earlier roots.

| Entry ID | Contextual person selections | Internal approaches | Main distinctions |
| --- | ---: | ---: | --- |
| `spatialhistory` | 11 | 7 | Landscape reconstruction; documentary geography; critical cartography; contested places; colonial naming; public landscapes; historical GIS |
| `intellectualhistory` | 10 | 6 | History of ideas; contextual arguments; conceptual history; texts and experience; publishing; Japanese thought and translation |
| `labourhistory` | 21 | 8 | Unions; class and culture; workplaces; strikes; gender and households; colonial labour; workers’ oral histories; military labour |
| `ethnohistory` | 14 | 7 | Commissioned claims research; documentary method; archaeology; Nahua texts; Andean inquiry; collaboration and authority; oral-tradition comparison |

These are 56 selections using existing identities and 18 new shared people. No person gains a duplicate identity or an invented individual graph node. Twenty-nine new edges name particular resources, projects and comparisons. Earlier nodes, sources, people, relationships, pathways, editorial qualifications and the entire journal catalogue are unchanged.

## Editorial decisions and evidence

Spatial history includes both earlier geographical reconstruction and digital methods. [Gregory and Southall’s 1998 abstract](https://researchportal.port.ac.uk/en/publications/putting-the-past-in-its-place-the-great-britain-historical-gis/) anchors the HGIS approach within the coverage period. The later redevelopment of that project is not backdated. Harley’s opening three pages explicitly identify different uses of Foucault and Derrida; the two new connections name that reception. Existing checked sources supply Sauer, Massey, Driver/Samuel and Hayden. Hoskins, Darby and Carter retain publisher/catalogue-level reading limits.

Intellectual history is broader than the existing Cambridge School entry. [Lovejoy’s institutional account](https://philosophy.jhu.edu/about/early-hopkins-philosophers/lovejoy/) supports his particular history-of-ideas programme. Existing scoped primary readings support Skinner, Pocock and Koselleck. Darnton supplies publishing and circulation; Maruyama and his translator Mikiso Hane supply a distinct Japanese inquiry. [Maruyama’s displayed primary openings](https://www.jstor.org/stable/j.ctt7zv34k) identify essays from 1940–1944 and reveal a situated modernization interpretation. The comparison with modernization theory asserts neither affiliation nor a documented transmission. Toews remains a metadata-supported intervention whose detailed argument needs reading.

Labour history joins scattered existing coverage without relocating or deleting it. The [Webbs’ original preface, reproduced in the 1920 edition](https://en.wikisource.org/wiki/The_History_of_Trade_Unionism/Preface), supplies union archives, observation and named research assistance. E. P. Thompson’s cultural analysis, Dorothy Thompson’s political history, feminist contributions and colonial critiques retain their differences. Nair’s criticism of Chakrabarty remains explicit. French, South Asian and African inquiries complement British and US work. The military connection uses the previously read Lucassen–Zürcher article, not an inferred association based on a title.

Ethnohistory is neither a synonym for Indigenous history nor a guarantee of Indigenous research authority. [Indiana’s public finding aid](https://archives.iu.edu/catalog/InU-Ar-VAA2723) identifies the Justice Department’s commission and Wheeler-Voegelin’s research role. Lurie’s primary opening disputes restricting ethnohistory to particular peoples. The Andean volume’s preface/introduction and 1978/1986 publication history support a specific interdisciplinary and editorial connection. Yukon elders remain named collaborators. Wilson and Rivera appear as qualified critical interlocutors; their inclusion does not assign them membership in an externally defined school. Vansina is a methodological comparison, not an assertion that African history derives from US ethnohistory.

## Access limits and remaining work

Fourteen new source records state exactly what was consulted. Primary readings include Harley 1–3, Lurie 78–84, the Webbs’ complete transcribed preface, and the Andean volume’s preface ix–x and introduction 1–3. These are bounded readings, with uncollated OCR/transcription where noted. Several books remain supported by publisher descriptions or short displayed extracts. Lockhart’s book metadata is supplemented by a clearly dated 2010 retrospective; later discoveries are not imported into the mapped period.

- **Spatial:** deeper regional historical geographies, Indigenous spatial knowledge, and fuller evaluation of early HGIS methods and uncertainty.
- **Intellectual:** women’s intellectual histories and African, Islamic, South Asian and Latin American programmes; fuller primary readings of Lovejoy, LaCapra, Toews and Maruyama.
- **Labour:** broader Latin American, Caribbean, East Asian and Indigenous histories, plus more specific histories of racialized, enslaved and unpaid labour. The present selection is not a global census.
- **Ethnohistory:** fuller Mesoamerican and Andean readings, additional regional traditions, Indigenous critiques and source mediation. Neither legal research nor non-Indigenous reconstruction automatically represents community priorities.

The 73-field journal ledger carries forward the previous 69 rows unchanged and adds unaccepted leads for the four new targets. **No journal edge is automatically transferred or duplicated.** Existing Ethnohistory→Indigenous history and Le Mouvement social→social history links retain their qualifications. The catalogue still has 1,638 candidate/title records and 54 venue edges: 42 principal, nine founding, three debate. Principal links reach 29 fields; all venue types reach 32.

## Preservation and validation

Current totals are **116 nodes, 752 edges, 833 sources, 829 people, 1,309 contextual selections and 731 approaches across 73 groups**. The original 109-entry first-pass inventory and the 187 pending second-pass questions retain their historical accounting; these additions do not resolve unrelated questions.

The snapshot is `drafts/historiography-1920-2000.v1.117.json`; exact additions and its hash are in `feedback/four-fields-v1.118-additions.json`. The current ledger is `feedback/journals/principal-venues-v1.118-review.json`. The research PDF and hash manifest live under `data/field-research/v1.118/`, outside public assets.

Validation: **62 Python tests and 10 JavaScript tests passed**. An initial Python run identified a stale 69-group assertion; it was updated to 73 and the suite rerun. The revision audit verifies zero structural errors, four unchanged documented comparison/contribution warnings, exact prior-record preservation, unchanged and reproducible journal catalogue, all 73 ledger rows, the research PDF hash and six byte-identical public assets. These checks do not certify historical truth or comprehensive coverage.

```bash
python3 scripts/build_site.py
python3 scripts/audit_four_fields.py
```

Older revision-specific audits still target their preserved revisions. No frontend design, browser review, deployment or OpenAlex work. The existing historical renderer loads all four entries; journal rendering remains absent.
