# Brief: where did this advisor earn their doctorate?

You are checking one historian for a scholarly knowledge graph of historians and their dissertations. Your
record is the entry in `../entries.json` whose `id` your instructions name.

## The question

The entry is an **advisor**: the AHA Directory of History Dissertations lists them as the supervisor of the
students in `students` (with each student's university and year). An automatic step linked this advisor to
`linked_record`, an AHA dissertation by someone of the same name, as if it were the advisor's own doctorate.
Many of these advisors teach in Canada and earned their doctorate outside the United States, where the AHA
directory has no record, so the linked dissertation may belong to a namesake.

Find out, from sources, **where and when the advisor earned their doctorate**, and whether `linked_record` is
their dissertation.

## How to work

1. Identify the advisor: the historian of that name who supervised those students at those universities in
   those years. A faculty page, CV, departmental listing, publisher's author note, obituary, or the
   acknowledgements or front matter of a student's thesis usually names the supervisor's affiliation; the
   advisor's own CV, faculty page, book author note, or obituary usually states their PhD.
2. Look for the advisor's doctorate: institution, year, and title if available. A library catalogue record of
   the thesis (LC, WorldCat, a university repository, a national library, theses.fr, EThOS, ProQuest's abstract
   page) is the best evidence for the title.
3. Compare with `linked_record` (dissertator, department, year, title). The same person if the doctorate
   matches it; a namesake if the doctorate is elsewhere or the linked dissertation's author is shown to be a
   different person.

## Sources: rules

- Use public, open sources: university and department pages, CVs posted by the person or their institution,
  publisher pages, library and repository catalogues, scholarly society pages, obituaries in newspapers or
  society publications, Wikipedia and Wikidata (as leads; confirm from another source when you can).
- **Never** read from or cite dokumen, Scribd, libcom, Internet Archive user uploads, or scans of course
  materials. Do not mention them.
- Record what sources say, not your opinion of anyone. No personal or identity information beyond name,
  affiliation, degree, year and title (no ethnicity, nation, religion, family). No birth dates.
- If sources conflict or you cannot find the doctorate, say so: `unclear` is a good answer.

## Output

Write `verdict.json` in your working directory, and nothing anywhere else:

```json
{
  "id": "<the entry id>",
  "advisor": "<name as in the entry>",
  "advisor_identified": "<one line: who this is, e.g. 'historian of medicine, McMaster then McGill'>",
  "doctorate": {"institution": "...", "year": "...", "title": "...", "degree": "PhD|DPhil|..."},
  "linked_record_is_theirs": "yes|no|unclear",
  "evidence": [{"url": "...", "says": "<short quote or paraphrase of what it states>"}],
  "notes": "<anything a reviewer should know, short>"
}
```

Use `null` for fields you could not establish. Two independent sources for the doctorate are better than one.
