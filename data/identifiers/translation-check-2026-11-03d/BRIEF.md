# Brief: what work is this much-cited book, and is it already in the graph?

You are matching works cited in history dissertations to works in a scholarly knowledge graph. Your group is the
entry in `../groups.json` whose `id` your instructions name: up to twenty `items`. Each item is a work as
dissertations cite it (`cited_title`, `cited_year`, `cited_authors`; every one is cited by ten to nineteen theses,
often a Portuguese, Spanish, French or English translation, a later edition, a reprint or an essay) and, for each
graph person whose corpus id is a cited author (`candidates`), that person's works in the graph (`work` id, kind,
year, title; mostly Library of Congress records). Many of these are Brazilian citations of translated classics
(*História e memória*, *O poder simbólico*, *Costumes em comum*).

## The question

1. Is the cited work the same work as one of the candidates' works, i.e. the same book in another language,
   edition, printing or with a variant title? Answer with that `work` id.
   - Same work: a translation (*Futuro Passado* is Koselleck's *Vergangene Zukunft*), another edition, a reprint,
     the same book under a shortened or variant title.
   - Not the same work: a different book by the same author, a part or chapter of a larger work, a collection
     that contains it, a book about the work. A translation that is a selection made for that language
     (*O poder simbólico* collects Bourdieu essays; *História e memória* gathers Le Goff's encyclopaedia entries)
     matches only a graph work with the same contents (*Histoire et mémoire*, 1988, is the French edition of the
     Le Goff selection); otherwise answer null and describe it below.
   - If two graph works are the same book (an original and a translation), give the original.
2. If no candidate work is the same work, identify the work itself so it can be added: the original's title,
   year and language, and its kind (`book`, `article`, `chapter`, `book_selection` for a translation-only
   collection). Give one identifier you have confirmed in a library catalogue or publisher record, best first:
   the Library of Congress LCCN of the original (catalog.loc.gov), an ISBN of the original or of the cited
   edition, an OCLC number, or for an article or chapter its DOI (or the journal, volume, year and pages when
   there is no DOI). Put the page you confirmed it on in `source_url`. Do not guess identifiers.
3. If the citation is garbled (two works run together, an author misread, a journal title taken as the book), say
   what the cited work most likely is and set `relation` to `unclear` unless you are sure.

Use your knowledge of the authors' bibliographies, and search the web to confirm (library catalogues, publisher
pages, Wikipedia). Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads or course
reading-list scans.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per item, in order:

```json
[{"id": "<item id>", "work": "w-... or null", "relation": "translation|edition|same|none|unclear",
  "original_title": "", "original_year": null, "original_language": "", "kind": "book|article|chapter|book_selection",
  "lccn": "", "isbn": "", "oclc": "", "doi": "", "container": "", "source_url": "", "note": "<short>"}]
```
