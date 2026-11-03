# Brief: compare a historian's CV with what the knowledge graph holds

You are checking one historian for a scholarly knowledge graph of historians, their works, their PhD students
and the dissertations that cite them. Your folder (your working directory) holds:
- `cv.txt`: the person's CV as text (from a PDF; the user notes CVs can be out of date);
- `graph.json`: every graph person whose name agrees with the CV's (`keys`), each with its identifiers, thesis
  advisor, students (advisor -> student edges) and works (kind, year, title, how many corpus dissertations cite it).

Work only from these two files. Do not browse the web.

## Questions

1. **Which keys are this person?** For each key: `same` (its works or identifiers are the CV's), `other` (a
   namesake: its works are not on the CV and do not fit the CV's field and dates), or `unclear`. Several `same`
   keys are one person split in two: say so.
2. **Works.** List every publication on the CV (books, edited books, journal articles, book chapters, reviews,
   other scholarly items such as reports, encyclopedia entries, digital projects with a publication), each with
   kind, year, title, and the graph `work` id it matches on a `same` key (or null). Count presentations, grants,
   teaching and service separately or not at all; they are not works.
3. **Graph works not on the CV**, on `same` keys: list them, and say for each whether it looks like the
   person's (the CV omits it or is out of date), a namesake's, or a duplicate of another graph work.
4. **Doctorate and advisor.** The CV's PhD (school, year, title if given, supervisor if named) against the graph's
   thesis work and `thesis_advisor`: agree, disagree or missing.
5. **Students.** Doctoral students the CV names as supervised (completed or current), against the graph's
   `students`: in both, CV only, graph only.

## Output

Write `verdicts.json` in your working directory and nothing anywhere else:

```json
{
  "person": "<name>",
  "keys": [{"key": "p-...", "verdict": "same|other|unclear", "why": "<short>"}],
  "split": ["p-...", "p-..."],
  "cv_works": [{"kind": "...", "year": 0, "title": "...", "graph_work": "w-... or null"}],
  "graph_not_on_cv": [{"work": "w-...", "title": "...", "assessment": "person's|namesake|duplicate", "why": "<short>"}],
  "doctorate": {"cv": "<school, year, title, supervisor>", "graph": "<thesis and advisor>", "verdict": "agree|disagree|missing", "note": "<short>"},
  "students": {"both": ["..."], "cv_only": ["..."], "graph_only": ["..."]},
  "notes": "<short: anything else the graph gets wrong or misses>"
}
```
