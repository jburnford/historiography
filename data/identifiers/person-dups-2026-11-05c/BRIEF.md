# Brief: does this reviewer's institution fit the historian's career? Judge by career facts.

A scholarly knowledge graph holds people as keys. Each pair below is two keys with the same full name: key `a` is a
well-identified historian (LC authority, Wikidata, atlas entry or ORCID, and several works); key `b` is a book-review
credit from H-Net's crossposts of H-Soz-Kult reviews. An earlier reader could only judge these by name and topic
(`earlier_verdict`, `earlier_evidence`), which this project never accepts as identity. Now each pair carries
`hsozkult_credits`: the line "Rezensiert für H-Soz-Kult von <name>, <institution>" from the Internet Archive's copy of
the original review page (`source_url`), i.e. the reviewer's institution at the review date.

Your batch is the list of group ids your instructions name, entries of `groups.json`; each group has up to fifteen
`pairs`, each with both keys' labels, anchors and works, plus the credits.

## The question

For each pair: does the credited institution (at the review's date: see the review's year among b's works) fit the
career of key `a`'s person?
- `same` with basis `career`: the institution is where a's person worked or studied around that date (their
  university, institute, chair; a doctoral or postdoc post). Use a's identifiers and works, your knowledge of German
  and European academic careers, and quick checks (the person's university page or CV, GND via lobid.org, Wikidata,
  ORCID records) when unsure.
- `different`: the institution or field shows another person (a literature scholar's institute for a historian, a
  different country or discipline with no link to a's career).
- `unclear`: you cannot place a's person at that institution. A wrong merge is worse than a missed one.
Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads or course reading-list scans (the
archived H-Soz-Kult pages are the publisher's own pages and fine).

## Output

Write the output file your instructions name and nothing anywhere else: a list, one object per pair, in order:

```json
[{"id": "<pair id>", "verdict": "same|different|unclear", "basis": "career|topic",
  "evidence": "<institution at date and how it fits a's career, short>",
  "source_url": "<the hsozkult_credits source_url you relied on, or a page you checked>"}]
```
Use basis `career` only when the institution fits; otherwise `topic` with verdict `unclear` or `different`.
