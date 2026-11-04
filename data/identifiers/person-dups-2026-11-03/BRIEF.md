# Brief: are these two keys the same person? Judge by their works.

A scholarly knowledge graph holds people as keys. Key `a` in each pair was just created for the author of a
much-cited book, identified through the Library of Congress record of that book (`lcnaf:` anchor). Key `b` is an
older key for someone with the same family name and first given name but no LC authority: a PhD from the AHA
dissertation directory (`aha-phd:`), a Brazilian or other thesis author (`diss-author:`, `capes-person:`), a
university repository's thesis supervisor (`repo-advisor:<university>|<name>`), a book reviewer (`review-credit:`),
an ORCID holder (`orcid:`), an atlas entry (`atlas:`), a GND, IdRef or ISNI record. Your group is the entry in
`../groups.json` whose `id` your instructions name: up to fifteen `pairs`, each with both keys' labels, anchors and
works (titles, years, kinds; `thesis` for a dissertation).

## The question

For each pair: are `a` and `b` the same person?
- Decide from the works. Same person when the works belong to one career: a thesis and the book made from it (*O
  corpo, a doença e a saúde: o saber médico luso-brasileiro no século XVIII*, UFMG 2006, and *Nos domínios do
  corpo: o saber médico luso-brasileiro no século XVIII*, 2011), the same subject pursued across the titles at
  plausible dates, a thesis at the right time before the books, an ORCID or repository profile that lists the book.
- A shared name is not evidence. A shared broad field is not evidence either (two US historians named James Adams
  are two people unless the works connect). Different subjects, impossible dates (a thesis decades after the
  person's first book, a career ending before the other begins), or a different discipline mean different people.
- When one key has no works, use its anchors: a repository supervisor at a university where the LC author is
  known to teach, an AHA PhD whose year fits; search the web (faculty pages, publisher author notes, library
  catalogues) to confirm. Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads or course
  reading-list scans.
- If you cannot tell, answer `unclear`; a wrong merge is worse than a missed one.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per pair, in order:

```json
[{"id": "<pair id>", "verdict": "same|different|unclear", "evidence": "<the works or facts that decide it, short>",
  "source_url": "<a page you confirmed it on, if you searched>"}]
```
