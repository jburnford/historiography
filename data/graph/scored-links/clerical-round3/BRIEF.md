# Clerical linkage audit: who is the printed person? (round three, 2026-11-12)

Each item is one printed name at one position of one work (author, JSTOR author, reviewer, volume editor, or a
Library of Congress heading of a book), and the candidate person keys (p-NNN) of a scholarly knowledge graph whose
names are compatible with it. Each key is meant to be one real person. You see, per candidate: identifiers held
(lcnaf = Library of Congress authority, wd = Wikidata, orcid, aha-phd = a PhD in the AHA directory, diss-person = a PhD
thesis in the corpus, review-credit = a key built from printed review credits, ...), affiliations with source and
years, advisor/student links, key-log co-authors, and a sample of the key's works.

Decide, from the dossier alone (no web search), which candidate is the person printed on the work.

Verdict, one of:
- `A`, `B`, `C`, `D`, `E`: that candidate is the printed person;
- `not-keyed`: the printed person is none of the candidates (a namesake with no key);
- `cannot-tell`: the dossier does not decide (two candidates fit equally, or a candidate and an unkeyed namesake).

Standing rulings:
1. No false matches; but do not be conservative where only one candidate is plausible (a rare name with a
   compatible career is enough).
2. Every candidate shown already passed a date test (the work falls inside the key's possible career).
3. A printed second given name or initial that disagrees with the key excludes that key.
4. Topic may support a link; lack of topical overlap never excludes (a scholar may change field; the works shown
   are a sample). Positive evidence of another person (a printed affiliation the key never had, co-authors or a
   work from another profession under a common name) can.
5. A review's author is the reviewer, never the reviewed book's author.
6. An OpenAlex author profile shared with a key is not evidence.
7. Never infer identity, nation or community from a name.
8. Several candidates may be one person split across keys (a review-credit key and a thesis key). If so, give the
   letter of the fullest record and list the other keys in `duplicate_keys` (`|`-separated). Two people with one
   name are not duplicates.
9. In reasons, do not call people "historians"; say the candidate, the author, the reviewer, or use the name.

Confidence: `high`, `medium` or `low`.

Output: write a CSV with the Write tool at the path you are given, header exactly
`item,verdict,confidence,duplicate_keys,reason`, one row per item in the batch, reason one short sentence (quote it
if it contains a comma). Judge every item; do not skip.
