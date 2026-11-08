# Brief: is this Library of Congress author one of the people already in our graph?

You are checking one item for a scholarly knowledge graph of historians, their dissertations, books and reviews.
Your record is the entry in `../entries.json` whose `id` your instructions name.

## The question

The entry is a Library of Congress name authority (`lc`: LC id, heading, dates, and `sources`, which are LC's own
source citations). `lc_books` lists books that LC's catalogue gives under this heading. `candidates` are people
already in our graph with the same or a similar name. Each has:
- `key`;
- `label`;
- `anchors` (identifiers such as `aha-phd:`, `orcid:`, `wd:`, `lcnaf:`);
- `aha_dissertations` (their doctoral dissertation as listed by the AHA Directory: title, year, department);
- `works` (title, year, kind).

An automatic step held this item back because the name alone cannot tell us whether the LC author is one of the
candidates or a namesake. **Is this LC authority the same person as one of the candidate keys, or none of them?**

## Identity is decided by works, not by names or topics

`same` needs a fact, other than the name, that ties the LC author to the candidate. Any one of these counts:
1. **The LC book is the candidate's dissertation as published.** A preface, catalogue record, publisher page or review says the book grew out of the dissertation at that university, or the titles and years make this plain and a source confirms it.
2. **The same institution in the right years.** A faculty page, CV, author note or obituary names both the LC book and the candidate's PhD (university, year), or their post.
3. **Authority or profile records.** LC, VIAF, WorldCat Identities, ORCID or Wikidata records list the candidate's dissertation or works under this person.

Rules:
- **Topic or field is not evidence.** The same name and the same subject is `unclear`, not `same`.
- **`none`:** the evidence shows a different person, such as other dates, another field, another country, or another doctorate.
- **`unclear`:** you cannot tell from the sources. That is a good answer; do not stretch.
- **`confidence`:** `high` when a source states the link directly. `medium` when the link is strong but inferred, such as the dissertation and book titles and years lining up and a publisher page placing the author at the right university.

## How to work

1. Read the LC heading, its `sources` and the `lc_books`. Search for the book: publisher page, catalogue records (LC, WorldCat, a national library), reviews, the author's faculty page or CV.
2. For each candidate, compare its dissertation (title, year, department) and works with what you find about the LC author.
3. Stop when you have one decisive source, or when a reasonable search, about ten queries, finds nothing decisive.

## Sources: rules

- **Use public sources:**
  - publisher pages;
  - university and department pages;
  - CVs posted by the person or their institution;
  - library catalogues and authority files (LC, VIAF, WorldCat);
  - repositories;
  - obituaries;
  - scholarly society pages;
  - ORCID;
  - Wikidata and Wikipedia (as leads; confirm elsewhere when you can).
- **Never** read from or cite dokumen, Scribd, libcom, Internet Archive user uploads, or scans of course materials. Do not mention them.
- **Record only:** name, affiliation, degree, year and titles. Nothing else about the person: no birth dates beyond what LC's heading already shows, and no ethnicity, nation, religion or family. Never paste full text; `says` is at most 200 characters stating what the page says.

## Output

Write `verdict.json` in your working directory, and nothing anywhere else. It holds one JSON object:

```json
{"item": "lcnaf:…", "verdict": "same" | "none" | "unclear", "key": "p-…", "evidence": [{"url": "…", "says": "≤200 chars, what the page states"}], "basis": "one or two sentences", "confidence": "high" | "medium"}
```

- `key` is the candidate's key, and only when `verdict` is `same`. Otherwise use null.
- `item` is the entry's `item` field (`lcnaf:…`), not its `id`.
- Give at least one evidence URL for `same` and for `none`.
