# Task 1 — catalogued authors on Sri Lanka and Canada place pages
Books tagged to a place often have no linked person; the Library of Congress main entry is shown
as "author as catalogued". Inputs: data/graph/places/lc-printed-authors.csv.gz (work, printed
author, LC authority id), data/graph/places/work-places.csv.gz (work → place QID),
data/graph/places/places.csv.gz and place-hierarchy.csv.gz, data/graph/places/README.md if present,
data/identifiers/place-demo-fixes-2026-11-18/README.md. Build your queue yourself (queue.csv in
your folder): one row per catalogued author (group by LC authority id; by exact printed heading
when none) with their works, for (a) works tagged to Sri Lanka Q854 or places within it —
all of them first (~146 authors); then (b) Canada Q16 and places within it (~3,200), ordered by
number of works descending. Skip fiction settings (source lc-fiction).
For each author decide: scholar (academic or serious independent scholar of history or a
neighbouring field) / official-or-participant (colonial official, missionary, traveller, soldier,
politician writing as a participant: a primary-source author) / literary (novelist, poet) /
corporate-or-not-a-person / journalist-or-popular / unclear. Add fields: lc_authority, name,
life_years, role_evidence, identifiers {lcnaf, viaf, isni, wikidata, orcid, gnd…} each with the
URL you read, field_or_discipline, institution_with_years if found, and existing_key: check
whether the graph already has a person key that is plainly this person (search nodes by name in
explorer.duckdb; compare identifiers/works) and give the key and the proof, or null.
