# Brief: are these two keys the same person? Judge by their works.

A scholarly knowledge graph holds people as keys. Each pair below is two keys with the same full name: key `a` is a well-identified historian
(an LC authority, Wikidata item, atlas entry or ORCID, and several works); key `b` is a single-source record of
someone with that name (a book-review credit with the reviewer's affiliation, an AHA dissertation record, a thesis,
a university's supervisor record, an ORCID, a CAPES record) that no route has yet compared with `a`. Either key
may hold a Library of Congress authority (`lcnaf:`), a Wikidata item (`wd:`), an ORCID, an AHA dissertation record
(`aha-phd:`), a thesis (`diss-author:`), a university supervisor record (`repo-advisor:<university>|<name>`), a book
reviewer (`review-credit:`), an atlas entry (`atlas:`), or only a corpus id (`diss-person:<family>|<given>`: the name
as bibliographies cite it). Your batch is the list of group ids your instructions name, entries of `groups.json`; each group has up to fifteen
`pairs`, each with both keys' labels, anchors and works (titles, years, kinds; `thesis` for a dissertation).

## The question

For each pair: are `a` and `b` the same person?
- Decide from the works: one career (the same books, a thesis and the book from it, one subject pursued at plausible
  dates, a faculty page or CV that lists both keys' works).
- A shared name is not evidence; nor is a shared broad field. Different subjects, impossible dates or a different
  discipline mean different people.
- Initials-only keys (`Clark, J.`, `Taylor, A.`) and corpus ids with only a first initial may gather several people
  under one name: answer `same` only when the key's works are (nearly) all the other key's person's; if they mix
  people, answer `mixed`.
- If both keys hold different `lcnaf:` or `wd:` identifiers, check whether those records describe one person (LC
  and Wikidata sometimes have duplicates) or two; say which in the evidence.
- When a key has no works, use its anchors (a supervisor at the right university, an AHA PhD whose year fits) and
  search the web (faculty pages, publisher author notes, library catalogues). Never read from or cite dokumen,
  Scribd, libcom, Internet Archive user uploads or course reading-list scans.
- If you cannot tell, answer `unclear`; a wrong merge is worse than a missed one.

## Output

Write the output file your instructions name and nothing anywhere else: a list, one object per pair, in order:

```json
[{"id": "<pair id>", "verdict": "same|different|mixed|unclear", "evidence": "<the works or facts that decide it, short>",
  "source_url": "<a page you confirmed it on, if you searched>"}]
```
