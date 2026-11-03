# Brief: is the linked dissertation this supervisor's own doctorate?

You are checking a group of historians for a scholarly knowledge graph of historians and their PhD students.
Your group is the entry in `../groups.json` whose `id` your instructions name; it lists up to eight
supervisors. Check each one.

## The situation

Each supervisor comes from the AHA Directory of History Dissertations: they are named as the advisor of the
`students` listed (student, university, year, title; `students_total` is the full count). The graph already
identifies the supervisor with the public records listed (`wikidata` QID, `lc` Library of Congress name
authority, `orcid`). An automatic step also linked one AHA dissertation to them as **their own doctorate**
(`linked_dissertation`), on name and date alone. A check of the public records found education facts that do
not name that dissertation's university (`facts_found`: Wikidata/ORCID education, LC notes on a doctorate), so
the dissertation may be a namesake's (a different person with the same name).

## The question

For each supervisor: **is `linked_dissertation` the supervisor's own doctorate?** Look for where and when the
supervisor (the person of the QID / LC authority / ORCID, who taught the listed students) took their
doctorate: a faculty page, CV, obituary, department history, Wikipedia, a library catalogue record of the
thesis, or the published book of the thesis.
- `own`: sources give the supervisor's doctorate at the linked university around the linked year (or the
  linked title is theirs);
- `namesake`: sources give the supervisor's doctorate elsewhere or at a clearly different time, so the
  linked dissertation is someone else's;
- `unclear`: you cannot tell.
Facts listing only a first degree, a post, or a postdoctoral fellowship do not contradict the link. Keep each
supervisor brief: a few searches, not a biography.

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
    "verdict": "own|namesake|unclear",
    "doctorate": "<the supervisor's doctorate as sources give it, e.g. 'PhD, Yale, 1975', or null>",
    "evidence": [{"url": "...", "says": "<short quote or paraphrase>"}],
    "notes": "<short>"
  }
]
```
