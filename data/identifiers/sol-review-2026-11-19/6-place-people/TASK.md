# Task 6 — the people lists a live demo will show (Sri Lanka and Canada)
The explorer's place pages rank "people with works about this place" from work → place tags
(data/graph/places/work-places.csv.gz; build/graph/explorer.duckdb tables pw / e_about_place_f,
e_authored_f, nodes; SET memory_limit='1GB'). Queue (queue.csv): person keys with 2+ works tagged
to Sri Lanka Q854 or places within it (all, about 115), then the top 600 person keys by number
of works tagged to Canada Q16 or places within it; fiction settings excluded.
For each key: who is this person (identifiers on the key's anchors; LC authority, ORCID,
university page), and for each of their place-tagged works: is it really theirs (namesake
credits are common) and is it really about that place? Verdict per key: sound / some-works-not-theirs /
two-people-one-key / works-not-about-place / label-defect (misspelt or mangled name: give the
correct published form with source) / unclear. Add fields: person {name, life_years, field,
institution_with_years, identifiers with URLs}, works (list of {work, title, year, theirs:
yes/no/unclear, about_place: yes/no/unclear, why}), and scholar_of_place: yes / incidental / no
(e.g. a health-survey author whose works merely have "Canadian" in the title is "incidental").
Never label anyone a historian; report what the evidence shows.
