# Brief: whose works are cited under this name? Judge by the works.

A knowledge graph of history dissertations reads each thesis bibliography into cited works, and groups the cited
authors under corpus ids built from family name and given names (`silva|maria`, `mello|joao m`). A corpus id can
pool several people: `silva|maria` gathers every Maria ... da Silva the bibliographies cite. Each id also carries a
display name (`cited_name`), taken from one of its citations; it may be wrong for most of them.

Each id below is held by a person key (`key_label`, `key_anchors`; `lc_label` is that person's LC heading when
the key has one). Several articles cited under the id were just found, by their own catalogue records, to be
another person's, so the id may name someone else, or pool several people. Your group is the entry in
`../groups.json` whose `id` your instructions name: up to ten `items`, each with the corpus id (`person`), its
`cited_name`, `cited_by_theses`, the key, and its most-cited `works` (title, year, kind, the author as the
bibliography gave it in `cited_authors`, number of citing theses); `works_count` is the total.

## The question

For each item: are the id's cited works, by citing theses, the works of the key's person (`lc_label` / `key_label`)?
- `same`: (nearly) all of the listed works are that person's; the names are variants or spellings (Raphael /
  Rafael Bluteau, Fritz / Friedrich Fischer, Luiz / Luís), or the `cited_name` is simply wrong for them.
- `mostly`: the id pools several people, but the LC person's works carry most of the id's citing theses (more than
  about two thirds of those listed).
- `minority`: the id pools several people and the LC person's works are a minority of its citations.
- `different`: the listed works are another person's (or other people's); the LC person is a namesake.
- `unclear`: you cannot tell. A wrong tie is worse than a missed one.

Decide from the works: know or check who wrote each of the top titles (library catalogues, publisher pages,
Google Books, the author's CV or Lattes page, review articles). A shared name or a shared field is not evidence.
Never read from or cite dokumen, Scribd, libcom, Internet Archive user uploads or course reading-list scans.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else: a list, one object per item, in order:

```json
[{"person": "<corpus id>", "verdict": "same|mostly|minority|different|unclear", "lc_share": <0-1, your estimate of
the share of the listed works' citing theses that are the LC person's>, "other_people": ["<name of another person
whose works are pooled here, if any>"], "evidence": "<the titles or facts that decide it, short>",
"source_url": "<a page you confirmed it on, if you searched>"}]
```
