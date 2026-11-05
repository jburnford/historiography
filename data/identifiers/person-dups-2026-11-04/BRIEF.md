# Brief: are these two keys the same person? Judge by their works.

A scholarly knowledge graph holds people as keys. Each pair below came from the dissertation citation corpus: theses
cite a person, and some of that person's cited works are credited in the graph to a second key with the same family
name and compatible given names (`Hunt, Lynn` and `Lynn Hunt`; `Hornblower, S.` and `Hornblower, Simon`). Either key
may hold a Library of Congress authority (`lcnaf:`), a Wikidata item (`wd:`), an ORCID, an AHA dissertation record
(`aha-phd:`), a thesis (`diss-author:`), a university supervisor record (`repo-advisor:<university>|<name>`), a book
reviewer (`review-credit:`), an atlas entry (`atlas:`), or only a corpus id (`diss-person:<family>|<given>`: the name
as bibliographies cite it). Your group is the entry in `../groups.json` whose `id` your instructions name: up to fifteen
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

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per pair, in order:

```json
[{"id": "<pair id>", "verdict": "same|different|mixed|unclear", "evidence": "<the works or facts that decide it, short>",
  "source_url": "<a page you confirmed it on, if you searched>"}]
```
