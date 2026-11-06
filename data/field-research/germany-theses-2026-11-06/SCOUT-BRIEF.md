# Brief: scout German History doctorates that can be downloaded openly (2026-11-06)

Context: a research project builds a citation graph from the bibliographies of History PhD dissertations
(repo /home/jic823/historiography; see data/field-research/mexico-theses-2026-11-04/README.md for how a country
was added: harvest repository records, screen to History doctorates, download open PDFs, register, ingest).
Germany has only 224 theses in the graph. The user wants Germany targeted. This is a SCOUTING pass only:
do not download any dissertation PDFs.

## Questions
1. Which routes list German History doctorates (Dissertationen, Fach Geschichte / DDC 900–909, 930–990) with
   open full texts? Check at least: the DNB (Deutsche Nationalbibliothek) catalogue APIs (SRU, OAI; online
   Hochschulschriften, urn:nbn), DART-Europe, BASE, OATD, and the institutional repositories of the main
   History departments (HU Berlin edoc-Server, FU Berlin Refubium, LMU München Elektronische Dissertationen,
   Heidelberg heiDOK, Göttingen, Tübingen TOBIAS-lib, Münster, Bielefeld PUB, Freiburg FreiDok, Hamburg,
   Leipzig Qucosa, Köln KUPS, Frankfurt, Bonn, Konstanz KOPS, Mainz, Erlangen OPUS, Bochum, Halle, Jena,
   Kiel, Trier, Mannheim, Gießen, Marburg, Kassel, Dresden Qucosa...). For each: OAI-PMH endpoint and the
   sets or filters that isolate doctoral theses in History (dc:type doctoralThesis, ddc:9xx, faculty or
   institute), whether PDFs are openly downloadable, robots.txt rules, any rate limits or terms.
2. Estimate counts: History doctorates per route, 2000–2025, and how many have an open PDF. Note overlaps
   (DNB vs repositories).
3. Recommend a pipeline order (the route that gives the most open History doctorates with the least
   screening), and what a History screen would need (German titles: "Dissertation zur Erlangung des
   Doktorgrades ... Philosophische Fakultät ... Fach Geschichte / Neuere Geschichte ...").

## Rules
Respect robots.txt and published limits; identify with a contact address in requests (mailto:jic823@usask.ca
is allowed for this research); never work around bot checks, logins, or embargoes; never read from or cite
dokumen, Scribd, libcom, Internet Archive user uploads or course scans. Sample record counts with small
OAI/API requests (a few pages), not full harvests.

## Output
Write `SCOUT-REPORT.md` (findings, counts with how they were estimated, recommended order) and
`routes.json` (one object per route: name, url, oai_endpoint, history_filter, open_pdf, robots, est_history_phds,
est_open, notes) in this folder, and nothing anywhere else.
