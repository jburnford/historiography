# Brief: are these two keys the same scholar?

You are checking one pair for a scholarly knowledge graph of historians, their dissertations, books, articles and
reviews. Your record is `item.json` in your working directory.

## The question

`a` and `b` are two person keys in the graph with the same name: the same family name and first given name. Each
side has:
- `label`;
- `anchors`: identifiers such as `aha-phd:` (AHA dissertation directory), `orcid:`, `lcnaf:`, `wd:`, and `diss-person:`
  (a name in our dissertation corpus);
- `life_years`;
- `works`: title, year, kind, journal;
- `supervised_theses`;
- `affiliations`;
- `citing_items`: how many theses and articles cite their works.

An automatic step found that their dated works fit one career. It could not tell whether they are **one person**,
whose works the graph has split over two keys, or **two people with the same name**.

## Identity is decided by works and careers, not by names or topics

`same` needs a fact, beyond the shared name, that ties the two keys' works to one person. Any one of these counts:
1. **One source names works from both sides.** A CV, faculty page, publisher's author note, obituary, ORCID, LC/VIAF
   authority, Wikidata or Google Books author page lists a work of `a` and a work of `b` under the same person.
2. **The dissertation and the later works.** One side's dissertation (an `aha-phd:` or thesis work) is the origin of
   the other side's book: a preface, review or catalogue record says the book grew out of that dissertation at that
   university.
3. **One institution, the right years.** A source places the author of a work on one side at the institution and in
   the years the other side's thesis or affiliation shows, and nothing points to a second person.

Rules:
- **Topic or field is not evidence.** The same name and the same subject is `unclear`, not `same`.
- **`different`:** the evidence shows two people. Examples are different birth or death years, two different
  doctorates, two different careers or countries, or one of them writing in an unrelated discipline in the same years.
- **`unclear`:** you cannot tell from the sources. That is a good answer. A wrong merge is worse than a missed one.
- **`confidence`:** `high` when a source states the link (or the difference) directly; `medium` when it is strong but
  inferred.

## How to work

1. Read `item.json`. Pick the most distinctive work on each side, and the dissertation if one is there.
2. Search for the author: a faculty page or CV, the publisher page, catalogue and authority records (LC, VIAF,
   WorldCat), ORCID, Wikidata, and reviews of the books.
3. Stop when you have one decisive source, or when about ten queries find nothing decisive.

## Sources: rules

- **Use public sources:** publisher pages, university and department pages, CVs posted by the person or their
  institution, library catalogues and authority files, repositories, obituaries, scholarly society pages, ORCID, and
  Wikidata or Wikipedia (as leads; confirm elsewhere when you can).
- **Never** read from or cite dokumen, Scribd, libcom, Internet Archive user uploads, or scans of course materials. Do
  not mention them.
- **Record only:** name, affiliation, degree, year and titles. Nothing else about the person: no ethnicity, nation,
  religion or family. Never paste full text. `says` is at most 200 characters stating what the page says.

## Output

Write `verdict.json` in your working directory, and nothing anywhere else. It holds one JSON object:

```json
{"item": "ps…", "a": "p-…", "b": "p-…", "verdict": "same" | "different" | "unclear", "evidence": [{"url": "…", "says": "≤200 chars, what the page states"}], "basis": "one or two sentences", "confidence": "high" | "medium"}
```
