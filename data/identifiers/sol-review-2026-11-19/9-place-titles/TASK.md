# Task 9 — read titles for ambiguous Canadian and Sri Lankan place names
Title rules were adopted only for names that read ≥95% right; these names failed or were never
read, so their works carry no title tag: Ottawa, Calgary, Victoria (B.C.), Kingston (Ont.),
Hamilton (Ont.), London (Ont.), Windsor (Ont.), Sydney (N.S.), Saint John (N.B.), St. John's
(N.L.), Regina, Saskatoon, Prince Albert, Yukon, Great Lakes, British North America, Halifax
(beyond the adopted narrow rule), Toronto/Montreal/Vancouver/Edmonton/Quebec City (titles NOT
caught by the adopted pattern rule), and for Sri Lanka: Colombo, Galle, Trincomalee,
Batticaloa, Kandy district names, Nuwara Eliya, Uva, Taprobane, Serendib, Ceilão/Ceilan/Zeilan.
See data/graph/places/title-readings/ and scripts for the adopted rules and earlier readings
(read the README or the reading CSVs there first; do not redo works already read).
For each name: list work nodes whose title (nodes.label, type='work') contains the name as a
whole word and that have no ABOUT_PLACE tag to that place yet (build/graph/explorer.duckdb,
SET memory_limit='1GB'); queue.csv = name, work key, title, year, kind, journal. Order: Sri
Lankan names first, then Canadian names by fewest matches first. Read every title (use the
journal, year and, where the title alone cannot decide, the work's public record: publisher or
journal page, library catalogue) and give a verdict per work: about-place (this Canadian /
Sri Lankan place is a subject of the work) / other-place-same-name / person-or-thing-same-name /
incidental (publisher, venue, institution, conference, place of publication) / unclear.
Add fields: name, place_qid (from data/graph/places/places.csv.gz), work, title, year, kind,
why. Titles are the main evidence; say when you relied on a web record (with URL).
