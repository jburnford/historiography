# Task 5 — thesis authors ("seeds") and their possible publications
Read data/identifiers/crossref-seed-links-2026-11-17/README.md first. Thesis authors from the
German national library register and Mexican theses get a person key only once linked to an
article, book or review. seed-candidates.csv.gz holds candidate Crossref works per seed with an
evidence class; seed-summary.csv the per-seed status. Queue (queue.csv), in order: every seed
whose best link is "weak" (about 101 German, 188 Mexican), then seeds with "name only"
candidates that have 5 or fewer same-name candidates. For each seed decide whether at least one
candidate work is by the thesis author: yes (which DOIs; the proof: publisher author note,
university page, ORCID record listing both thesis and work, the book being the published
thesis…) / no (namesake: say what shows it) / unclear. Common names need a real tie, not a
shared topic. Add fields: seed, thesis {title, year, university}, works_confirmed (DOIs),
works_rejected (DOIs with reason), identifiers found for the person (ORCID, GND, VIAF, Wikidata
with URLs).
