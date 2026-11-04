# Brief: second pass on cited works the first pass could not ground

You are matching works cited in history dissertations to a scholarly knowledge graph. Your group is the entry in
`../groups.json` whose `id` your instructions name. Each item is a work as dissertations cite it (`cited_title`,
`cited_year`, `cited_authors`, `cited_by_theses`), the graph's works by keyed people among its authors
(`candidates`), and `first_pass`: what a first reader answered and why that answer could not be used
(`failed_because`). Every identifier is checked by a script before anything is written: an LCCN or ISBN against
the Library of Congress catalogue, a DOI against Crossref, a URL by the page's citation metadata (citation_title,
citation_author); titles and authors must agree.

## What to do with each item

Read `failed_because`, then:
- **no identifier**: find one that can be checked. A book: its Library of Congress LCCN (search catalog.loc.gov),
  else an ISBN, with `source_url` the catalogue or publisher page showing it. An article or chapter: its DOI; if it
  has none, `url` = the publisher's or journal's own page for the article (OJS, SciELO, Persée, Érudit, Cairn,
  bepress Digital Commons pages carry citation metadata), not a PDF link or a repository copy of someone else's.
- **title differs**: the identifier found a different work. Often the cited work is a chapter or essay and the
  identifier is its book: give the chapter's own DOI or page if it has one; otherwise `relation: part` and say
  which book holds it (`container`). If the record is the right book under another title (a typo, a translated
  title), say so in `note` and give the identifier again.
- **author mismatch**: LC may catalogue the author under another form of the name (Hebe Mattos as "Castro, Hebe
  Maria Mattos de"; a medieval author under the Latin form; an edited volume under its editors). Give that form in
  `catalogued_as` ("Castro") and the identifier again.
- **unclear**: decide only if you are confident which work is meant; otherwise `relation: unresolvable`.
- Use `relation: unresolvable` (with the reason in `note`) for citations that cannot name one work: two books run
  together, an author's name with a generic title, an archive, a newspaper, a law, a census, an anonymous source.

Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads or course reading-list scans.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per item, in order:

```json
[{"id": "<item id>", "work": "w-... or null", "relation": "translation|edition|same|none|part|unresolvable|unclear",
  "original_title": "", "original_year": null, "kind": "book|article|chapter|book_selection|thesis",
  "lccn": "", "isbn": "", "doi": "", "url": "", "container": "", "catalogued_as": "", "source_url": "", "note": "<short>"}]
```
