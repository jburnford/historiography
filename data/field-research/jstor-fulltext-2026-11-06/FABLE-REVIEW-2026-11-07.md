# Fable 5.1 review of KG-INTEGRATION-PLAN.md (2026-11-07)

This is an outside review of the plan beside it, requested by the user and run as one Fable 5.1 agent with read-only access to the scripts, the key log, the build and the E: tables. Its findings are summarised below; the full report is in the KG session transcript.

**User response (2026-11-07):** "an institution in the article is a very strong piece of evidence". So name plus the institution printed in the article or review counts as a strong fact, and P7's proposed downgrade of Sol's institution-based matches is declined. The fixes for P1 are kept, because the problem there lies elsewhere:
- the institution facts on the person key were undated;
- the institution named was only a university system;
- the institution came from an earlier automated link, not from the article.

## Findings, ranked

### P1. The signature route has no year window and feeds itself

This was verified on p-8481.
- `key_review_credit_merges.key_institutions()` discards dates: it keeps the ORCID employment organisation but drops its start and end years.
- `key_review_signatures.py` adds each review it links back into the key's institution facts, so every pass places the person more widely. The script was run six times.
- Example: p-8481, James Lockhart, a 2016 PhD whose ORCID record covers Cold War Chile, was credited with the senior Latin Americanist's reviews in HAHR and JIH from 1969 to 2003. The link went through a bare "University of California".
- Of the 33,614 signature claims:
  - 3,685 rest on an earlier signature (the cascade);
  - 2,804 rest on a bare system name;
  - 8,604 rest on undated H-Net affiliations.
- 29,815 of the 86,404 REVIEWED edges rest on this route.

**Fix:**
- Require a dated fact on the key, within about ±8 years of the review.
- Refuse bare system names.
- Never let a signature link become a placing fact for further links.
- Rerun from the state before the signature passes and withdraw the claims that no longer hold.

### P2. Citation counts are cut

The export keeps only citations that match exactly one work, and it leaves out reprints and translations.
- Rows matching two or more works are dropped: 10,297 strong rows. For example, *Nature's Metropolis* is held under two keys and loses 177 citing articles.
- 'edition?' rows are dropped: *Imagined Communities* has 277 citing items of this kind on top of its 487 strong ones.

**Fix:** build the edition relation and merge duplicate works before any count is published.

### P3. Edges carry no provenance

CITES does not say where each citation came from (rules or Qwen) or on what basis it was matched (strong or title+year). REVIEWED does not record the claim key or the route that linked the reviewer.

### P4. JSTOR book reviews are typed as articles

`build_graph.work_kind` gives JSTOR reviews the kind 'article'. About 302,000 review works are counted among the articles.

### P5. `key_review_books_lc.py` twins() ignores `rejected:lcnaf`

As a result, the rejections recorded from the Sol "none" verdicts have no effect yet.

### P6. Duplicate person keys

9,094 normalised labels sit on two or more live keys. 610 labels carry two different LC authorities.

### P7. Sol same/high verdicts that rest on an institution

A dozen or so 'same'/'high' verdicts rest on name plus one institution. The review proposed treating them as medium; the user declined (above).

## Open questions answered

- **Order:** repair P1 before step 1, the article authors. Do step 2 and the work dedupe before publishing counts. Leave unmatched works until last.
- **Co-author as evidence:** a co-author alone is not enough. It counts only with an established co-author and a work the two share by DOI or by an ORCID claim.
- **Aggregating citations to people:** use both tiers, carry the person's `resolution` on each edge, and make established people the headline figures.
- **Qwen sampling:** a 24/24 hand check only bounds the error below 11.7%. Check 300 pairs, stratified by basis, era, language and rules-had.
- **Coverage bias:**
  - The share of citing JSTOR articles with a keyed author peaks at about 29% in 1993–2004 and falls below 7% after 2017.
  - The corpus is heavy in French and Italian journals, while the identity routes are Anglo-American.
  - The "EHR" in the corpus is the *Economic History Review*; the *English Historical Review* is not included.

## Checks proposed before going further

1. Check every signature claim's review year against the dated facts on its key, and hand-check 100.
2. Hand-check 300 Qwen-only citation pairs, stratified.
3. Merge or relate the top 200 duplicate work pairs.
4. Hand-check 100 of the label pairs that carry two LC authorities.
5. Re-read 50 Sol same/high verdicts.
6. Recount articles once reviews are typed as reviews.
7. Do a dry run of the reviewed-books propose step with the rejections honoured.
