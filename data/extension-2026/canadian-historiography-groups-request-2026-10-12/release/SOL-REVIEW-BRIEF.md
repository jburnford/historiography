# Adversarial review brief: revision 1.128 (historiography in Canada)

You are reviewing a revision batch for a historiography atlas used to teach historiography in
Canada. Claude (Anthropic) drafted it with research agents. The user asked for a critical review
from a different model family before Claude accepts it. Be adversarial: find what is wrong,
overstated, unsupported or inconsistent. Do not rewrite the entries.

## What to read
- `release/editorial-additions.json`: the frozen packet. It holds 18 new group entries (nodes),
  new people, sources and edges, in atlas format. This is what will be applied.
- `drafts/<id>/`: per-entry working drafts. Each has `entry-draft.json` (with
  `question_resolutions`), `literature.json` (fuller verification records), `evidence.json` and
  `NOTES.md`.
- `answers/ANSWERS.md` and `answers/research/`: the reasoning behind editorial decisions.
- `GRAPH-FORMAT.md` (repository root): the atlas's editorial rules. Read the sections on rosters,
  strands, relationships, bibliographic verification and chronology.
- The atlas itself, `historiography-1920-2000.json` (read-only), for existing entries the new ones
  link to.

## What to check (in priority order)
1. **Claims the sources do not support.**
   - Compare each description, strand focus, roster context and edge evidence note with its
     `source_ids`, and with the verification notes in the sources (and the drafts'
     literature.json).
   - Flag any statement about what a work argues where the source record says only metadata was
     checked, or where the note says the text was not read.
   - Flag quotations that the notes do not show were seen.
2. **Overstatement.** Founding claims, "first", "defining", influence where only a comparison is
   evidenced, and generalisations from one reviewer to "reviewers".
3. **Relationships.**
   - Kind and direction (comparison, contribution, critique, influence).
   - Evidence notes that do not support the kind.
   - Duplicate or contradictory pairs.
   - Edges to existing atlas entries whose own descriptions make the link doubtful.
4. **Identity.**
   - People conflated with namesakes; wrong ids reused for different people.
   - Labels that misname people. One person published as Robin Brownlie and now goes by Jarvis
     Brownlie.
   - QIDs in `people_wikidata` that look wrong.
5. **Coverage and balance for teaching in Canada.**
   - Obvious missing figures, francophone scholarship, women, or Indigenous and Black scholars,
     where the drafts' own evidence shows them.
   - Entries whose scope overlaps so much that students would be confused.
6. **Schema and rules.**
   - Date labels must give milestones and say what each date means.
   - Rosters are not edges.
   - Every verification needs a scope note and date.
   - Spans run to the 2000 coverage limit, and later works are readings, not registered extension
     interventions. Is that policy applied consistently, and is any text inconsistent with it?

Spot-check sources on the web where you can (Crossref, publisher pages, Érudit). Say which ones
you checked.

## Output
Write a report with:
- a short overall verdict;
- a numbered list of findings, most severe first. Each finding gives:
  - severity: blocker, major or minor;
  - the entry id or record id;
  - the exact text at issue;
  - why it is a problem;
  - what evidence you checked;
  - a concrete fix.

Keep it to findings; no praise. If something is fine, don't list it.
