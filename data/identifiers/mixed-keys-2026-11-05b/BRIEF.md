# Brief: which works credited to this person key are someone else's?

A knowledge graph of historians (the historiography project) holds people as keys and credits works to them through
claims from several sources (`source`): `lc-authored`/`lc-edited` (Library of Congress records), `orcid-claim` (the
person's own ORCID record), `cited-authored`/`verdict-authored` (a dissertation bibliography's citation, matched to a
JSTOR/Crossref/LC record; `via` is the corpus id used, e.g. `diss-person:allen|robert`), `hnet-*` (H-Net reviews),
`hand-authored`, `crossref-orcid` (Crossref lists the ORCID among the authors), `orcid-claim` (the person's own ORCID record: treat as reliable unless the ORCID itself is clearly another person's). Each key below was found to mix several people's works (namesakes: two Robert
C. Allens, P. J. Marshall and Peter Marshall). Your batch file lists keys with their identifiers (`anchors`: lcnaf,
wd, orcid, gnd, viaf, aha-phd, atlas, diss-person...) and every credited work (claim key, title, year, kind,
source, via).

## Task

For each key:
1. Decide who the key IS: the person its public identifiers name (LC authority, Wikidata, ORCID, atlas entry), or,
   failing those, the person most of its works belong to. Say it in one line (name, dates or field, institution).
2. List every credited work that is NOT that person's, by claim key, with who wrote it instead and a short reason
   (subject, dates, a different person named on the publisher's/journal's page). Judge by the works themselves:
   titles, fields, dates (a work before the person was born or after they died), co-authors. A shared field is not
   proof of identity; a different field or impossible dates is strong evidence against.
3. List corpus ids (`diss-person:...` anchors on the key) that name someone else (their cited works are mostly
   another person's), if you can tell, in `corpus_ids_not_theirs`; list any other anchor on the key that names
   someone else (an `aha-phd:` thesis record, a `review-credit:`, an `lcnaf:`/`wd:` record of a namesake: check
   id.loc.gov or Wikidata before saying so) in `other_anchors_not_theirs`.
4. If you cannot tell for a work, leave it out (a wrong removal is worse than a missed one). If the key has no
   dominant person at all, say so (`no_dominant_person: true`).

Use your own knowledge first; search the web only to settle real doubts (publisher pages, university pages, library
catalogues, Google Scholar, JSTOR). Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads
or course reading-list scans.

## Output

Write a JSON list to the output path your instructions give, one object per key, in the batch's order:

```json
[{"key": "p-1472", "person": "Robert Clyde Allen (b. 1950), film historian, UNC",
  "not_theirs": [{"claim": "c-637176", "belongs_to": "Robert C. Allen, economic historian (Oxford/NYU Abu Dhabi)", "reason": "Economic History Review article on early modern wages"}],
  "corpus_ids_not_theirs": ["diss-person:allen|robert"], "other_anchors_not_theirs": [], "no_dominant_person": false}]
```
Write the file even if some keys are left empty (`"not_theirs": []`). Do not edit any other file.
