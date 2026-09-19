# Medical history, historical geography and named omissions — batch 05

The user redirected the 2000–2026 continuation toward thin medical/health and historical-geography coverage, then identified Paul Lovejoy and the Eley, Wrigley, Wallerstein and Berg field connections. This packet develops **16 works, 18 historical proposals, 27 author credits and two version links**. Eight proposals use selected passages, five author abstracts and five publisher descriptions. All 47 claims remain `needs_review`; none of this post-2000 packet is imported automatically.

The separate [production correction 1.121](../../production-batches/roster-corrections-1.121/README.md) handles the named roster fixes using pre-2001 works and a retrospective institutional source. It does not accept these newer claims. Paul E. Lovejoy and Keith Nield were new candidates against this packet's pinned 1.120 baseline; the separate production correction now supplies their shared identities. [Crosswalk](production-crosswalk.json) prevents duplicate creation.

## Concrete entry drafts

[entry-proposals.json](entry-proposals.json) contains complete additive drafts for `medicalhistory`, `spatialhistory`, `social` and a possible full Paul E. Lovejoy entry. Existing node IDs, original roster rows, strand IDs and qualifications survive unchanged. Proposed local source IDs require an acceptance adapter; these drafts are not drop-in production data. Lovejoy's production representation is currently in two field rosters, not the proposed full node.

| Field | Selected additions | Evidence and limits |
| --- | --- | --- |
| Medical and health history | Rogaski (2004): changing meanings of *weisheng*, body and city | Introduction pp. 1–3 checked; Tianjin case, not a universal Chinese account. |
| Medical and health history | Cueto and Palmer (2014/2015): Latin American and Caribbean historiography | Publisher introduction summary; PDF timeout remains unresolved. Cambridge gives December 2014, reviews often 2015. |
| Medical and health history | Cooper Owens (2017): enslaved Black and Irish immigrant women in gynecology | Publisher description only; neither patient consent nor homogeneous experience inferred. |
| Medical and health history | McCallum (2017): Indigenous health under Canadian colonialism | Reproduced author abstract only; primary publisher body inaccessible. |
| Medical and health history | Wynter, Campbell, Chaney and Marks (2025): psychiatric categories and antiracist practitioners | Version-of-record pp. 2–3; all four author credits. Studied period c.1800–2020 is not publication date. |
| Historical geography | Harris (2002): colonial land policies and spatial arrangements | Publisher chapter pp. 8–10; not Indigenous testimony. Current 2003/2007 formats do not date the original work. |
| Historical geography | McKittrick (2006): Black women’s geographies; explicit engagement with Wynter | Chapter 5 pp. 121–123, consulted in authorized 2020 reprint; no new 2020 intervention or checked 2026 paratext. |
| Historical geography | Gregory and Healey (2007): historical GIS across quantitative/qualitative inquiry | Author-deposited abstract; distinct from Gregory and Ell's book. GIS does not define the entire field. |
| Historical geography | Machado and Gomes (2013): Brazilian urban and territorial inquiries | Portuguese journal abstract, English research paraphrase; Abreu/Moraes are two cases, not the whole field. |
| Historical geography | Gomes da Silveira (2024): southern knowledge production | Indexed publisher abstract; English-language regional survey, body still pending. |
| Historical geography | Legg, Ding, Ferretti, Morin and Novaes (2025): multilingual disciplinary review | Editorial pp. 5–6 checked; five coauthors, no claim that its aims are already accomplished. |
| African/Atlantic histories | Lovejoy: *Transformations in Slavery* (1983), diaspora programme (1997), *Jihād* (2016) | First work is a metadata referent, with third edition separate; 1997 indexed abstract; 2016 publisher description. Distinct from Arthur O. Lovejoy. |
| Social/cultural history | Eley (2005); Eley and Nield (2007) | Publisher descriptions; supports specific proposed connections, not exclusive school membership or rejection of cultural history. |

The [coverage view](coverage-current.json) retains all 75 topics, 37 discovery candidates and original ledger rows. It adds research-bin evidence and a separate pre-2001 recovery list; reprints and later digital editions do not fill newer bins. This is an index of partial research, not a merged count of all staging records. No field is fully reviewed through the September 2026 cutoff.

## Next source work

Medical history still needs patient and care histories beyond doctor/patient dyads, nursing and midwifery, hospitals, pharmaceuticals, disability without medical reduction, South Asian/African/Pacific and relevant-language surveys. Earlier omissions such as Charles Rosenberg, Mary Fissell and Nancy Tomes are research leads, not additions already established here. Monica Green's 2020 plague article and recent pandemic historiography remain leads; no substantive claim was generated from a title or podcast listing.

Historical geography needs older traditions beyond the current British selection and further Indigenous spatial authority. Meinig, Baker, regional landscape traditions, Chinese-language scholarship and the surveys identified in the 2025 editorial remain a queue. The Portuguese abstract narrows one language gap but does not complete an original-language survey. The two fields now have actual work-based drafts; neither a larger roster nor an English-accessible sample certifies balanced coverage. No demographic attributes were inferred.

Digital/web history was interrupted by these priorities. `raw/digital-leads.json` preserves the Gallini/Noiret 2011 Spanish introduction, Rosenzweig 2003, Winters 2018, Ogden/Maemura 2021 and Hegarty 2024-online/2025-issue leads. Gallini PDF was retrieved only to `/tmp`; no claims were assembled. Putnam's university download returned 403, so the old abstract-only claim **has not** been upgraded. Resume alongside the earlier Leon/Gallon/Putnam packet; retain Hegarty's publication-date distinction.

## Reproduction

`python3 scripts/build_priority_research.py --check` verifies the research contract, source hashes, exact rebuild and pinned production/prior-packet preservation. `python3 -m unittest tests.test_priority_research tests.test_roster_corrections tests.test_graph_validation tests.test_people_validation` passes 25 checks. The baseline graph is archived as `drafts/historiography-1920-2000.v1.120.json`; the original hash is preserved, not reset after correction 1.121. Earlier packets and manifests are unchanged. Captures distinguish web extraction, indexed abstracts, metadata and downloaded PDF text; binary third-party PDFs remain outside the repository.

Fable owns the website. No site/build edits, deployment, OpenAlex work or external messages were performed.
