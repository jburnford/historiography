# Brief: is this Wikidata item the person of this LC authority?

You are checking pairs for a scholarly knowledge graph of historians. You get either one entry of
`../entries.json` (by `id`) or a group of up to eight entries in `../groups.json` (by group `id`); check each
entry. Keep each check brief: a few lookups, not a biography.

## The situation

The graph holds a person (`key_label`, with `key_evidence`: their AHA dissertation records, Open Library
author id, ORCID, or the name under which dissertations cite them). That person carries an LC name
authority (`lc`), reached through their own books in the Library of Congress catalogue. A Wikidata item
(`wikidata`) cites that LC authority (property P244), so normally the item is the same person. An automatic
check refused it (`automatic_check_problems`):

- `name_disagrees`: the item's labels do not match the name (it may be a transliteration, a married or
  changed name, a pen name, or simply a wrong P244 on Wikidata);
- `birth_disagrees`: LC's and Wikidata's birth years differ by more than two years (a typo on one side, or
  two people);
- `lc_links_other_item`: the LC authority itself links to a different Wikidata item.

## The questions

1. **Is the Wikidata item the same person as the LC authority?** Open the LC authority page (`lc.url`; its
   sources and notes say who it is and which books) and the Wikidata item (`wikidata.url`; description,
   occupation, works, other identifiers such as VIAF, ORCID, ISNI). Compare.
2. **Does the LC authority fit the graph's person?** Check `key_evidence` against the LC authority (for
   example, the dissertation's subject and year against the books LC lists, or the Open Library author's
   books). Usually yes; say `no` only if sources show a different person.
3. If birth years disagree and the item is the same person: which year do the best sources support (an
   obituary, a CV, a national library record)?
4. If the item is a different person and `lc_links_other_item` names another item, or you find the right
   item for the LC person, give its QID.

## Sources: rules

- Use public, open sources: id.loc.gov, Wikidata, VIAF, national library catalogues, university and
  department pages, CVs posted by the person or their institution, publisher pages, obituaries in newspapers
  or society publications, Wikipedia (as a lead).
- **Never** read from or cite dokumen, Scribd, libcom, Internet Archive user uploads, or scans of course
  materials. Do not mention them.
- Record what sources say, not your opinion of anyone. No personal or identity information beyond name,
  name forms, affiliation, field, works, and birth or death years as LC or Wikidata state them (no ethnicity,
  nation, religion, family).
- Do not edit Wikidata or any other site.
- If sources conflict or you cannot tell, say so: `unclear` is a good answer.

## Output

Write `verdict.json` in your working directory, and nothing anywhere else (for a group: `verdicts.json`, a
list with one such object per entry, in order):

```json
{
  "id": "<the entry id>",
  "item_is_lc_person": "yes|no|unclear",
  "lc_fits_key": "yes|no|unclear",
  "lc_person": "<one line: who the LC authority is, e.g. 'historian of the French navy, Queen's University; books 1987-2004'>",
  "item_person": "<one line: who the Wikidata item is>",
  "birth_year_supported": "<year or null, with the source in evidence>",
  "right_qid_for_lc_person": "<QID or null>",
  "evidence": [{"url": "...", "says": "<short quote or paraphrase>"}],
  "notes": "<anything a reviewer should know, short>"
}
```
