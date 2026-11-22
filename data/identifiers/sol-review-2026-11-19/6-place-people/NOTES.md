# Task 6 review checkpoint

The queue is complete. All 115 Sri Lanka cases and all 600 Canada cases have verdicts. Use the bare person key for Sri Lanka and `Q16/p-N` for Canada. Use the latest line per case, including supersessions. `DONE` gives the current counts.

Use the read-only November 18 explorer snapshot with DuckDB memory limited to 1 GB and two threads. Filter `pw.place` to the requested country, for example `place:Q16`, and include self and descendant rows. Join distinct non-fiction `pw.work` to `e_authored_t."to"` for edges whose `"from"` is the person. Exclude roles `edition-editor`, `translator`, `introducer`, `series-editor` and `contributor`. Preserve the snapshot work key, title and year. Keep the OpenAlex investigation paused.

## Pilot

The first 20 Sri Lanka cases cover 218 distinct person–work pairs. Re-read all 20 against case order, credits, dates, geographic scope and evidence. Appended corrections for Michael Roberts, Kumari Jayawardena, Patrick Peebles and R. Raven-Hart. The pilot showed why an imported work ORCID needs independent checks and why a translation, deposit date, parent-book DOI or inherited review tag needs its own reading.

## Latest session

On 2026-11-21, appended 75 verdicts for Canada ranks 526–600, covering 610 person–work pairs, and 8 supersessions. The 75 new verdicts are 55 sound, 11 unclear, 8 some-works-not-theirs and 1 works-not-about-place. The ledger has 806 lines, including 91 supersessions. Its 715 current verdicts cover 9,873 person–work pairs.

Signed journal records distinguish the reviewers Shannon, Guillaume, Lexier and Winks from the authors and editors of the works they reviewed. Comeau and Tremblay edited the collective volume about Ryerson. Pearson’s preface confirms that Fyson joined the textbook team for the sixth edition, and the graph record pools it with the 1993 first edition. The Forest Service locates the “Canadian super-wolf” discourse in the US Northern Rockies. Edinburgh credits Rutherford as a contributor to the forum on her own book.

Repository catalogues establish Flatt’s 2008 thesis issue date alongside Redeemer’s 2009 degree date, and confirm the Gouglas and Jasen thesis titles. HathiTrust MARC records distinguish Beck’s 1982 Howe biography from the earlier edition of Howe’s writings. Preserve Champlain’s unresolved birth year and the editorial roles in the collected voyages. His writings document the place as primary sources.

Signed journal contents distinguish Campeau and Couturier from reviewers of their works. The Moran anthology entries reproduce nineteenth-century documents and carry modern editorial credits. The Wien review and Lacoursière translation each have two graph records. The Canadian elements of the Maloney and Gates works are substantive even where the events or publication took place outside Canada.

The Meisel cleavages item, Béatrice Craig’s Tenant League review, the two Wilson Agricultural History reviews, the Gerald Craig foreign-policy book, the Muirhead thesis and Mannion’s Annals review still need firmer credit or edition checks. The Caves lecture, MacKay memoir and Dobson merchant directory need firmer evidence of Canadian scope. Biggar’s two reviews and Kilbourn’s thesis and journal contribution need firmer credit checks.

All 715 case IDs and work counts match the queue. All appended work IDs, titles and years match the snapshot. The first 723 ledger lines retain their starting SHA-256. All three source-host tests passed, and the appended verdicts passed the source-host scan.

## Research methods

Start with institutional bibliographies, catalogues, publisher contents and dated bylines. Check signed issue contents for reviews because deposits can list the reviewer alongside the reviewed author. LC name-authority JSON and LC item JSON give different evidence. The first links names and careers, and the second gives book credits and geographic subjects. University CVs can resolve alternate dates, including Bryce’s 2016 Active History piece. Keep the snapshot title, year and ID while documenting the published form and edition. Use repository catalogue landing pages for thesis metadata. Distinguish a publication’s venue, setting and institutional affiliation from its geographic subject.
