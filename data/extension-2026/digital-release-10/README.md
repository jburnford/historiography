# Revised digital/web release candidate — 19 September 2026

**Prepared, not applied.** The current entry drafts are in [entry-proposals.json](entry-proposals.json); the additive production proposal is [candidate.json](candidate.json). These supersede digital-web-07's entry selection without changing that frozen research packet. Production remains **1.122**.

The user identified an overcorrection in the digital selection following Sharon Leon's criticism. The earlier draft gave too little space to practitioners' projects and methods: Thomas appeared as a target of criticism without his own substantive contribution, while Cohen and Ayers were missing. The revised entry opens with historical practice, projects and methods and retains the supported critical scholarship. There is no gender quota or inferred demographic classification.

- Cohen and Rosenzweig: searchable evidence, publication, public participation and authority, from the online introduction to *Digital History* (2005).
- Thomas and Ayers: the joint *Differences Slavery Made* comparison (2003, repository author abstract only), alongside Thomas's own discussion of digital form, evidence and argument in *Computing and the Historical Imagination* (2004).
- Graham, Milligan and Weingart: computational exploration, public research notebooks and collaboration, from their 2014 AHA essay. This is a distinct work from the 2015 *Macroscope* book and its 2022 second edition.
- Blevins: achieved public/archival work and the case for more explicit academic argument, from selected passages of his 2016 chapter.
- Romein and all eight coauthors, plus Milligan's 2019 and 2022 books: reconciled from the older breadth packet, with selected passages checked. The publisher credits **nine** Romein authors, including Stefania Scagliola.

Leon, Gallon, Putnam, Gallini/Noiret, Winters and the archived-web contributors remain in the selection. Thomas's own work and Leon's specific critique coexist. Brügger's 2018 book remains a research lead with reconciled authorship/date metadata; its description-only historical claim is deferred from the candidate.

The candidate contains **17 selected works, 27 historical claims (23 selected-passage, 4 abstract), 31 authorship credits, 2 version links and 26 new shared people**. Roy Rosenzweig reuses his production identity. Nineteen work entities include two additional target/response referents, not nineteen newly read works. Two proposed group entries contain twenty contextual strands; shared works appear in both relevant fields. The consolidated research packet includes the deferred Brügger work/claim/credit and person.

## Evidence and chronology

Selected readings and limits are on every claim citation. Cohen/Rosenzweig: introduction sections on manipulability, interactivity and authority. Thomas: concluding digital-scholarship discussion, captured lines 82–111, especially the joint-project account at 92–103. Thomas/Ayers: repository abstract, not the inaccessible electronic article or companion print overview. Graham/Milligan/Weingart: “What Does a Macroscope See?” and “Why Write It Online?” Blevins: opening argument and the later qualification that public history contains interpretation. Milligan 2022: pp. 7–9, sections 1.3–1.4; Milligan 2019: introduction pp. 3–5. Romein: selected opening and quantitative-text-analysis passages, not the entire field literature.

Older claims, qualifications and citations survive. Three breadth claims gain additive evidence; their complete prior records are in review-actions.json. Duplicated concept records and annotated older works retain their previous records there. Candidate source URLs added from the earlier bibliography are explicitly recorded in candidate.json; IDs, captures and citation joins survive.

Publication, reception, edition and research-cutoff dates remain distinct. Leon's 2018 work and its documented 2020 reception have separate strands. Hegarty's 2024 online publication retains its 2025 issue version. The 2014 Macroscope essay concerns a 2013 public draft; it is not dated to either book edition. The discovered 2022 edition has a fourth coauthor, Kim/Kimberley Martin, and remains a follow-up rather than a three-author import. Thomas's online Companion byline says “II”; the self-identified joint Ayers project and UNL/AHR metadata support the local “William G. Thomas III” identity, with the variation recorded.

The entry date labels and curated spans identify selected publication milestones with earlier roots open; they do not assign field founding or termination dates. No field is fully reviewed. See [representation-review.json](representation-review.json) for selection reasons and remaining project, regional, language and earlier-root gaps.

## Validation and next step

`python3 scripts/build_digital_release_candidate.py --check --preview /tmp/historiography-digital10.json` checks pinned inputs, source hashes and exact reproduction. It has no production-write mode. Six focused candidate tests and four browser cases cover prior-record preservation, coauthors, substantive and critical contributions, description-only exclusion, dates, evidence links, the exact 2000 view and mobile layout. Production graph/people checks also pass.

Preview totals: **128 nodes, 765 edges, 885 sources, 876 shared people**. The graph has zero structural errors, four existing duplicate endpoint/type warnings and two expected unconnected-entry warnings. No arrows are invented from field overlap. The exact 2000 view still uses frozen **1.121**; the additive candidate baseline is current **1.122**. These baselines serve different purposes and must not be conflated.

The unchanged site builder produces ten allowlisted files under /tmp. No site source, docs output, authority sheets, prior packets or production graph were changed. Browser checks passed for both new entries, all nine Romein coauthors, Thomas's argument, retained Leon, Hegarty's separate dates, explicit abstract scope, evidence links, mobile width and absence of the new entries from the exact 2000 view.

Next: record acceptance of this bounded candidate against the then-current production graph, archive that baseline and integrate locally using the established acceptance approach. Preserve the 1.121 exact-2000 pointer and previous accepted claims. This candidate is ready for that separate integration step; it is not evidence that the entire extension through 2026 is complete. OpenAlex remains paused. No commit, push or remote deployment.
