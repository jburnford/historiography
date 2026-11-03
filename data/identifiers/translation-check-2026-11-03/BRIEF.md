# Brief: which keyed work is this cited book an edition or translation of?

You are matching books cited in history dissertations to works already in a scholarly knowledge graph. Your group
is the entry in `../groups.json` whose `id` your instructions name: up to twenty `items`. Each item is a book as
dissertations cite it (`cited_title`, `cited_year`, `cited_authors`; often a Portuguese, Spanish, French or English
translation, a later edition or a reprint) and, for each graph person whose corpus id is a cited author
(`candidates`), that person's works in the graph (`work` id, kind, year, title; mostly Library of Congress records).

## The question

For each item: is the cited book the same work as one of the candidates' works, i.e. the same book in another
language, edition, printing or with a variant title? Answer with that `work` id, or null.
- Same work: a translation of it (*Futuro Passado* is Koselleck's *Vergangene Zukunft*), another edition, a reprint,
  the same book under a shortened or variant title.
- Not the same work: a different book by the same author, a part or chapter of a larger work, a collection
  that contains it, a book about the work. If the cited title is a multi-volume work and the graph holds only
  some volumes, answer null unless one graph work is the whole.
- If two graph works are the same book (an original and a translation both in the graph), give the original.
Use your knowledge of the authors' bibliographies; you may search the web to confirm a translation's original
title (publisher pages, library catalogues, Wikipedia). Never read from or cite dokumen, Scribd, libcom or
Internet Archive user uploads.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per item, in order:

```json
[{"id": "<item id>", "work": "w-... or null", "relation": "translation|edition|same|none|unclear",
  "original_title": "<the original's title, if you know it>", "note": "<short>"}]
```
