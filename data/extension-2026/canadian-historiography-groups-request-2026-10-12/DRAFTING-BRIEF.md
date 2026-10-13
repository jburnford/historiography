# Drafting brief: Canadian historiography group entries

This brief is shared by everyone drafting the entries proposed in `groups.json`. The user
approved the structure and its decisions on 2026-10-12; see README.md.

## Rules
- **Write only inside `drafts/<group_id>/`.** Do not edit the atlas
  (`historiography-1920-2000.json`), `groups.json`, the other packets, `docs/`, `site/`,
  `data/evidence-layer/` or `data/field-research/`. Do not commit.
- **The atlas's editorial rules apply** (`GRAPH-FORMAT.md`):
  - date labels give dated milestones, not boundaries, and say what each date means;
  - rosters are not edges;
  - edges need evidence notes and a relationship kind from the atlas's vocabulary;
  - the main period is 1920–2000, with a partial post-2000 extension.

  Read the existing national-school entries as models for register and length: `annales`,
  `progressive`, `newleft`, `historyworkshop`, `bielefeld`, `nationaltradition`.
- **Every source must be verified against a real record**: Crossref
  (`https://api.crossref.org/works/{doi}` or `?query.bibliographic=`, with
  `mailto=jic823@usask.ca`), publisher pages, Érudit, JSTOR landing pages, library catalogues
  (Open Library, WorldCat, LAC), or OpenAlex. Record the URL or DOI checked and what was checked:
  - `bibliographic_metadata_checked`: details only;
  - `supporting_page_checked`: an abstract, contents page or opening text was read.

  Never cite from memory. If a work can't be verified, mark it `unverified` and keep it out of
  the proposed sources. Check claims about a work's argument against an abstract, review or
  contents page where possible, and say when you couldn't.
- **Use the evidence.** `groups.json` gives each group's scope and anchor people; `evidence.json`
  gives anchor citation counts and most-cited works for 2009–2026 PhDs. For deeper evidence, use
  the citation graph `data/field-research/dissertation-citations-2026-10-11/graph.json`:
  - load it once;
  - use Dissertation nodes with `in_analysis: true`;
  - CITES goes Dissertation → Work, AUTHORED goes Person → Work;
  - count dissertations, not citations.

  `../canadian-historiography-scholars-request-2026-10-12/candidates.csv` gives each person's
  works and counts. Its `identity-decisions.csv` lists works that belong to namesakes; never
  attribute those to the person.
- **Canadian historiography is bilingual.** Include francophone scholarship wherever it belongs,
  not only in Quebec historiography.
- **Model your output on `../settler-colonialism-request-2026-10-12/`**, especially its
  `entry-draft.json` and `literature.json`.

## Output for each group (`drafts/<group_id>/`)
1. **`entry-draft.json`:**
   - `id`, `label`, `entry_kind: "group"`, `entry_type` (for example research field, school,
     debate or topic field), `period` and its rationale;
   - `date_label` following the milestone rules;
   - a `description` of 150–250 words in the atlas's register: what the field or school is,
     its key works and turns, its debates and its critics;
   - `representative_figures_and_works` prose;
   - `roster`: `person_id` (snake_case; reuse existing atlas `people` ids where the person is
     already there), name, role, a context sentence, works, and `source_ids`;
   - `strands`: dated interventions with work and source ids;
   - `proposed_relationships`: to existing atlas entry ids and to other proposed group ids, with
     kind, direction, evidence note and source ids;
   - `open_questions`.
2. **`literature.json`:** each verified source as `id`, citation, year, url or doi, a
   `verification` object (status, checked_on, checked_against, what was read), and the claim it
   supports.
3. **`evidence.json`:** whatever counts you computed, with denominators.
4. **`NOTES.md`:** a half-page summary, with the judgement calls and questions for the user.

Keep each roster to the people who matter for teaching the field: typically 8–20, including
the scholars from `groups.json` and any important earlier or francophone figures. Include
critics where they exist.
