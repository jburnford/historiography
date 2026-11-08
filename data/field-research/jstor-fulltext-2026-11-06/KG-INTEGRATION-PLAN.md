# Merging the JSTOR full-text data into the knowledge graph: plan for review (2026-11-07)

Owner: the KG session (identity, key log, graph build). The JSTOR full-text session parses and matches read-only
and hands tables over (BRIEF.md, HANDOVER-*.md in this folder). The goal is to use the JSTOR history corpus for
research on historians and historiography: who cites whom, who reviews whom, and how works move through the field.
This document says what is merged, what is planned, and the rules, and asks for review.

## Standing rules

**Legal and text:**
- JSTOR legal cleared releasing the citation graph (2026-11-06).
- We never commit or publish JSTOR text: no OCR, notes, review text, or any quoted span.
- We commit parsed bibliographic fields, counts, keys and edges only.
- The data lives on E: (/mnt/e/jstor-fulltext-2026-11-06/); the link expires 2026-12-23.

**Citations:**
- Citations come only from the notes of research articles, review essays and review articles.
- Book reviews never give citations. They are used only for the reviewed book (the heading) and the reviewer
  (name and institution in the signature).

**Identity:**
- Identity is by works and identifiers, never by name alone.
- Topic or field never merges or splits people.
- A same-name match needs a non-name fact: a shared work, a dissertation, a public identifier, or an
  institution in the right years.

**Key log:**
- The key log (data/identifiers/events-*.jsonl) is append-only.
- Rule merges go behind a merge guard (pooled names, open conflicts).
- A claim withdrawn on review is never re-minted by a rule rerun (scripts/identifiers.py materialise, since
  2026-11-07).

## Merged so far (all in the key log; graph built by scripts/build_graph.py)

| Step | Script | Result |
|---|---|---|
| JSTOR articles as works | key_jstor_articles.py | 100,219 article works on DOI |
| Citations from notes (rules) | export_jstor_citations.py → data/graph/jstor-cites.csv.gz | 572,904 edges (strong, or title+year; one graph work only) |
| Citations, Qwen re-read of 49,782 badly parsed articles | same, `--qwen` | +108,306 → 681,210 edges from 72,078 articles to 192,969 works (24/24 Qwen-only pairs right in a hand check) |
| Reviews by JSTOR title (metadata) | key_jstor_reviews.py | review works, `reviews` claims |
| Reviewed books from review headings (rules) | key_jstor_review_headings.py | 60,631 `reviews` claims |
| Same, Qwen re-read | same, `--candidates …-qwen.parquet`, new/changed rows | +36,425 and +4,886 claims (20/20 sample) |
| Reviewed books not in the graph, looked up in LC 2016 | key_review_books_lc.py (match/propose) | 31,395 + 20,715 + 2,092 books minted on LCCN; ~17k + 10,948 + 1,031 LC authors keyed |
| Rule links Qwen disputed, adjudicated (Qwen + two Sonnet passes) | review-rules-adjudicated.parquet | 107 wrong `reviews` claims withdrawn |
| Reviewers from signatures (name + institution, placed by the key's own records) | key_review_signatures.py | six passes; 76,300 reviews with a keyed reviewer of 420,813 |
| Review-credit duplicates (name + institution) | key_review_credit_merges.py | about 950 merges |
| Held same-name LC authors (Sol, web evidence, high confidence only) | apply_held_lc_verdicts.py | pilot + 2 batches: 177 attached, 86 namesakes recorded; about 4,800 to go |

Graph now: 231,229 person keys; 1.82M works; CITES 1,465,722 (681,210 from JSTOR); REVIEWS 439,223;
REVIEWED (reviewer → author) 86,404.

## Planned, in proposed order

1. **Authors of JSTOR research articles → person keys** (the largest gap).
   - Only 29,573 JSTOR article works have a keyed author.
   - Only 8,813 of the 72,078 citing articles do, so most citation edges can't yet become historian → historian
     edges.
   - Sources: the JSTOR creators in records.sqlite, Crossref/ORCID for the same DOI, author affiliations printed
     on the first page (the full-text session can parse these), and the review-signature institutions already
     held.
   - Route: an ORCID claim of the DOI (identifier). Then name plus a non-name fact: an AHA dissertation, the same
     institution in the window, a co-author, or an LC authority whose 670 cites the article or the journal.
   - Unresolved authors stay as printed names on the work (`author-name:` members), never minted as name-only keys.
2. **Edition relation.**
   - 95,265 'edition?' citation candidates (reprints, translations) and 1,365 'no_year' rows.
   - They become an edition/`published_as` relation between work keys, not merges, and citations follow it at
     analysis time.
3. **Unmatched cited works** (unmatched-works.parquet).
   - 935,538 books, 442,000 articles and 173,151 chapters that the notes cite but the graph lacks.
   - Plan: only rows cited by two or more items, or with mean_conf ≥ 0.7. Group title variants (author family plus
     title start). Look the works up in LC 2016 / Crossref / OpenAlex on title, author and year. Mint works with
     identifiers only; their authors are keyed as in step 1.
   - Known head: Williams, *Capitalism and Slavery*; Mintz, *Sweetness and Power*; Foucault cited as *The Birth of
     the Prison*.
4. **Remaining held LC authors** (Sol run in progress).
   - About 4,800 items, then the medium/unclear verdicts by hand.
   - `none` verdicts let the LC author be minted as their own person with their book claims (a propose rerun that
     honours `rejected:lcnaf`).
5. **Reviewer names still unkeyed.**
   - About 344k reviews carry a printed reviewer name only.
   - Next routes: Wikidata/OpenAlex journal records (done once, 7,155), and "several keys placed there" (675) to
     outside review.
   - Name-only remains unlinked.
6. **Publication and research use:**
   - The citation graph (JSTOR, theses), the review network (REVIEWED) and authorship are released as edge tables
     with keys and public identifiers (LINCS-compatible PIDs). No text.
   - Analyses (canon maps, cohort studies) count distinct citing works and drop initial-only name keys
     (a rule from 2026-11-03).

## Open questions for review

- Is the order right? Should article authors (1) come before unmatched works (3) and editions (2)?
- Step 1's identity rules: is name + same institution in the year window enough when the institution comes only
  from the article's first page? Is a co-author enough?
- Citation edges point at work keys. Should analyses aggregate to person keys only through `authored` claims of
  established people, or also through recorded (one-source) people?
- Qwen-only citation pairs are accepted on a 24-item hand check. Is that enough sampling for 108k edges? What
  sample would be enough?
- Book reviews as research data: is REVIEWED (reviewer → author) sound when the reviewer is linked on name plus
  institution only?
- Risks we may be missing: duplicate work keys splitting citation counts; namesake LC authorities; the JSTOR
  coverage gaps (no AHR, P&P, EHR, CHR); temporal bias (ORCID/Crossref favour recent work).
