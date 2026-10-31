# Sol brief: 32 new timeline entries from the dissertation canon (2026-10-31)

**Task.** Write individual entries for 31 historians and one theorist. They are the historians whom History PhDs cite most and who have no entry on the timeline. Work in three batches of research packets, each in the format of the lane rounds 1.171–1.191, built by `scripts/apply_person_entries.py`:
- `data/extension-2026/historian-canon-lane1-round1-2026-10-25/` is the worked example;
- `data/production-batches/person-entries-1.171/` is its acceptance.

The baseline is **revision 1.231**, the completed relationship queue. Claude reviews and accepts each batch; do not commit or push.

## The queue

| Batch | Expected revision | File | People |
| --- | --- | --- | --- |
| 1 | 1.232 | `work-queues/batch-1.json` | Christie, J. R. Miller, Trigger, Bynum, Rosenwein, Bourke, Keith Thomas, Elliott, MacKenzie, Callum Brown |
| 2 | 1.233 | `work-queues/batch-2.json` | Israel, Parker, Devine, R. J. Evans, Laqueur, Maier, E. H. Carr, Walkowitz, Paul Kennedy, Smout |
| 3 | 1.234 | `work-queues/batch-3.json` | David Arnold, J. R. McNeill, Fitzpatrick, Geary, Mike Davis, Trevor-Roper, Peter Gay, Paul Thompson, Kathleen Wilson, Charles Rosenberg, Robert Bartlett, Stephen Greenblatt |

If another revision lands first, renumber; never overwrite.

Each person record in a batch file gives:
- `person_id` and `qid`;
- `existing_profile` and `existing_context_ids`. For these people the atlas already has a people record and roster rows, so keep the id and make the proposed contexts *additive*;
- `proposed_context_ids`, the fields where the entry should be rostered or linked. These are proposals: argue against any that the evidence does not support;
- `bibliography_leads`, the most-cited works;
- `keys_with_counted_works`, the citation keys whose works were counted. The reading bridge must list all of them;
- `note`, with identity checks and namesake resolutions.

## How they were chosen (for the entries' framing, not as claims of influence)

- **Count.** The count is distinct dated strict History PhDs (build of 2026-10-30) that cite any of the person's works as first author, with key variants combined and namesakes removed by reading the cited works.
- **Bars.**
  - Canadian historians need at least 150.
  - Other historians need at least 136, the count of Paul Thompson the oral historian (user, 2026-10-30: "I think Paul Thompson is the better cut off").
- **Editorial additions below the bars, by the user:**
  - Kathleen Wilson, 135, and Charles E. Rosenberg, 127 (2026-10-30: "they give us two more women and a key sub field");
  - Robert Bartlett, 135, and Bruce Trigger, 141 (2026-10-31).
- Counts select the queue. They are not evidence of influence and must not appear in entry text as such.

## Decisions already made (do not reopen)

- **Stephen Greenblatt** is an **Individual theorist** entry (New Historicism), not a historian entry.
- **Mike Davis** is a **historian** (urban and environmental history), not a mixed-scholarship writer.
- **Bruce Trigger** is a Canadian archaeologist and ethnohistorian; Q991855 was checked. The atlas already records Indigenous criticism of his work:
  - Emma LaRocque (1999) on his foreword to Sioui's *Autohistory*;
  - LaRocque on the "neo cross-cultural approach".

  His entry must carry that criticism alongside *Natives and Newcomers* and *The Children of Aataentsic*. OCAP rules below.
- **J. R. Miller** is a settler scholar of residential schools and treaties. Four citation keys were combined by cited works (see `namesake-resolution.json`). Do not attribute *Democracy is in the Streets* (James Miller) or Joseph C. Miller's works to him. OCAP rules apply to all residential-school and treaty material.
- **Callum G. Brown.** His works are filed under the garbled key "brown|katherine e". Every work under that key is his.
- **Kathleen Wilson** has no Wikidata item. She is grounded to her [Stony Brook department page](https://www.stonybrook.edu/commcms/history/people/_faculty/wilson.php).
- **Nancy Christie.** Q112466726 is one person. The item's Oxford Brookes employer claim is unverified; do not use it.
- **Mary P. Ryan** already has an entry (`mary_ryan`, 1.178) and is not in the queue.

## Source rules (binding)

- Read only from authorised routes:
  - publishers, DOI landing pages, JSTOR stable links, Persée/OpenEdition, institutional repositories;
  - authors' own postings;
  - Internet Archive *lending-library* or public-domain scans.

  Do not read from document-sharing sites, shadow libraries, uploads of in-copyright books, or reposts on unrelated sites. If a text can only be reached that way, treat it as **unread** and use abstracts, authorised excerpts or named readers instead.
- Never name a disallowed route anywhere: notes, drafts, README text or commit messages. Say "not read".
- Link only DOI, publisher, JSTOR, repository or the author's page. Everand is acceptable, and so are single chapters shared for teaching.
- Respect robots.txt. Do not get around 403s, paywalls or bot checks. OpenAlex remains paused.
- For Wikidata, use `Special:EntityData/<QID>.json` or a SPARQL endpoint for item checks. Never use `wbsearchentities` to identify people.
- Your own email may appear in a User-Agent string for legitimate research requests. Never use it for sign-ups or unrelated services.

## OCAP (binding for Trigger, Miller and any Indigenous material)

These rules follow `data/extension-2026/indigenous-histories-2026-10-27/OCAP-REVIEW.md`:
- Write about scholarship: what scholars argued and how collaborations worked. Never give the content of oral narratives, teachings, ceremonies, songs or traditional knowledge.
- No genealogies or family details of community members. Do not quote narrators or interviewees, even through reviewers.
- Identity notes for Indigenous scholars are minimal, self-stated and professional (the nation only), and written as prose, never as a structured field.

## Life dates

- The research packet records all life evidence (`life-status.json`), including birth years of living people, with source and precision.
- The site export withholds birth years for people with no recorded death unless they were born more than 120 years ago. Do not put living people's birth years in entry prose.

## Each entry should have

- A biography in the lane style. It distinguishes primary reading, interviews or named substantive readers from bibliographic metadata, and keeps original, edition and translation dates separate.
- Scoped relationships to existing entries, each grounded in read passages (with locators), including critics and criticisms. There is no quota and no claim to an exhaustive network.
- Additive roster contexts with sources.
- A reading bridge that lists every key in `keys_with_counted_works`.

## Checks before handing back

- Run `apply_person_entries.py --build` and the in-memory apply with no new structural warnings.
- Confirm earlier edges and sources are byte-equivalent.
- Run a grep of all drafts for disallowed hosts; it should find none.
- Write a per-batch README with the review boundaries, as in lane 1 round 1.

Leave the graph and `docs/` unapplied for Claude's acceptance.
