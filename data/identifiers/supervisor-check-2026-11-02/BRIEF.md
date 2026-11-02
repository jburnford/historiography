# Brief: is this PhD supervisor the person of the candidate record?

You are checking a group of historians for a scholarly knowledge graph of historians and their PhD students.
Your group is the entry in `../groups.json` whose `id` your instructions name; it lists up to eight
supervisors. Check each one.

## The situation

Each supervisor comes from the AHA Directory of History Dissertations: they are named as the advisor of the
`students` listed (student, university, year, title; `students_total` is the full count). `own_phd` is their
own doctorate where the AHA records it (an AHA dissertation, or the PhD school the AHA directory lists; may
be empty). `candidates` are records of a historian with a compatible name: a graph person holding a Wikidata
item, an ORCID, and/or a Library of Congress name authority (`lc`), or an LC authority not yet in the graph.
An automatic check compared career facts (education with `own_phd`, employers with the students'
universities) but could not confirm the match (`facts_agreeing` shows what did agree).

## The question

For each supervisor: **is one of the candidates the same person?** Look for:
- the supervisor at the students' university in those years (a faculty page, CV, obituary, department
  history, or a student's thesis acknowledgements naming the advisor);
- the candidate's identity (Wikidata item at https://www.wikidata.org/wiki/<QID>, LC authority at
  https://id.loc.gov/authorities/names/<lc>.html, ORCID at https://orcid.org/<orcid>);
- whether they agree: same institution and period, same field of doctorate, a PhD matching `own_phd`.
Two historians of the same name in different places or periods are common; say `no` when sources show the
candidate is someone else, and `unclear` when you cannot tell. Keep each supervisor brief: a few searches,
not a biography.

## Sources: rules

- Use public, open sources: university and department pages, CVs posted by the person or their institution,
  publisher pages, library catalogues and authority files, thesis repositories, scholarly society pages,
  obituaries in newspapers or society publications, Wikipedia and Wikidata (as leads).
- **Never** read from or cite dokumen, Scribd, libcom, Internet Archive user uploads, or scans of course
  materials. Do not mention them.
- Record what sources say, not your opinion of anyone. No personal or identity information beyond name,
  affiliation, degree, year, field and works (no ethnicity, nation, religion, family, birth dates).
- Do not edit Wikidata or any other site.

## Output

Write `verdicts.json` in your working directory, and nothing anywhere else: a list with one object per
supervisor in your group, in order:

```json
[
  {
    "id": "<the supervisor's id>",
    "supervisor": "<name>",
    "same_as": "<graph_key, or lc id for an LC-only candidate, or null>",
    "verdict": "yes|no|unclear",
    "who": "<one line: who the supervisor is, e.g. 'historian of Mexico, University of Arizona, PhD Texas 1975'>",
    "evidence": [{"url": "...", "says": "<short quote or paraphrase>"}],
    "notes": "<short>"
  }
]
```
