# Task 8 — place headings that did not ground to Wikidata
Read data/graph/places/README.md (if present), data/field-research/place-nodes-scoping-2026-11-18/SCOPING.md
(grounding section) and data/graph/places/overrides.csv (35 hand groundings: follow that format
and standard of "basis"). data/graph/places/ungrounded.csv.gz lists Library of Congress
geographic heading strings with use counts and the reason they failed. Queue (queue.csv): first
every ungrounded heading on works about Canada or Sri Lanka/South Asia, then all others by uses
descending (stop at headings with fewer than 5 uses). Places only: skip peoples, nations, ethnic
groups and "categories of countries" (verdict not-a-place). For each heading find the right
Wikidata item by following identifiers: id.loc.gov authority page → its Wikidata/VIAF/GeoNames
links, or the Wikidata item whose LC authority id (P244) or GeoNames id matches; read the item
(instance-of, country, coordinates, inception/dissolution) to confirm it is the same place and
period. Do NOT use Wikidata's string search (wbsearchentities) to pick an item; if only a name
search could find it, verdict is "unclear". Verdict: grounded (qid) / no-item-exists (say what
the heading denotes, e.g. "Northwest, Canadian" as a historical region, and the nearest broader
items) / several-candidates (list them) / not-a-place / unclear. Add fields: heading, uses,
lc_authority, qid, qid_label, instance_of, country_qid, period (years), basis.
