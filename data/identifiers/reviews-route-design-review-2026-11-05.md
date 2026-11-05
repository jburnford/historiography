# JSTOR book-review route: design review (Fable, 2026-11-05)

Scope: the draft route that matches JSTOR `book-review` items (/mnt/e/jstor-book-reviews.parquet, 3.33M rows) to keyed
LC books, mints the review as a work with a `reviews` claim, and keys the reviewer. The open question is reviewer
identity (options a–d in the brief). Figures below come from probes run today against build/graph (468,072 keyed
books with an author) and the parquet; the probe code is not kept.

## Recommendation (option d: c plus evidence-gated attach; never a name-only key)

1. **Mint every matched review as a work and a `reviews` claim regardless of whether the reviewer is keyed.** Put the
   reviewer name(s) on the review work as members (`reviewer-name:<as printed>`), with the journal and date. This alone
   answers "which reviews did my book get, in which journals, by whom (as printed)" for every keyed book, which is
   the gap the lead described; it needs no identity decision.
2. **Do not mint `jstor-reviewer:<name>` keys (option a).** Name is the only thing JSTOR gives, and the pool is all
   disciplines, 1660–2024. A name-only key pools namesakes by construction: "Jim Clifford" has six JSTOR reviews, and
   two of them (On Point, 2001 and 2004, US Civil War cavalry) are another Jim Clifford; "David Smith" has 488 across
   157 journals. The project rule is names never merge; a `jstor-reviewer:` key is a merge of every bearer of the name.
   It also buys little: of the 96,698 full reviewer names on reviews that match a keyed book, 65,637 occur once; only
   184 names carry 20+ reviews, and those are exactly the common names (and the Foreign Affairs capsule reviewers).
   It would add ~97k person keys, most outside history.
3. **Do not use option b.** "Exactly one established key with that name" is a fact about our coverage, not about the
   world: the On Point reviewer is not in the graph, so (b) would hand his reviews to the lead. Field agreement is
   name-plus-topic, which the lead has ruled out as sole evidence, and a historian reviewing a history book is the
   normal case, so it discriminates nothing.
4. **Attach reviewer -> existing key only on a positive, non-name fact tying that person to that review**, in order:
   - **ORCID on the review record** (Crossref for the same DOI, or for the publisher's DOI of the same review: 10.2307
     DOIs are also registered in Crossref, and the Environmental History / Labour reviews exist under OUP and Érudit
     DOIs too). ORCID decides; the name is not consulted. Claim anchor `crossref-orcid:<doi>:<orcid>`, as key_crossref_orcid does.
   - **Same review already keyed from H-Net / Reviews in History** (same book, same reviewer name, review-credit key
     with an affiliation): add the JSTOR DOI as a second occurrence of the same review work only when journal and year
     agree; do not key a new person.
   - **Works-in-this-journal route** (a works criterion, not a field one): the name agrees with exactly one key by
     `key_aha_lc_notes.name_agrees` (full given name, no initials), that key already `authored` an article or review
     in the same journal within +/-10 years of the review date, and no other key of an agreeing name has any work in that
     journal. Record the claim `recorded` with anchor `jstor-reviewer:<doi>:<key-basis-anchor>`. In the probe 11,626
     reviews (4,704 names) have exactly one established namesake key; 3,137 of those keys carry an ORCID, so the
     ORCID step will settle most of them without the journal rule.
   - Everything else stays an unkeyed name on the review work. Keep a table `unattached-reviewers.csv` (name, doi,
     journal, year, book key) as the queue for Sol/agents, worked **per historian of interest**, not across 3.3M rows:
     the lead's network questions are asked about keyed historians, so resolve the reviewers of their books and the
     reviews by them, and leave the rest as names.
5. **Tiers.** Review works: `recorded` on the JSTOR record (`established` when a second DOI or an H-Net record of the
   same review joins). Reviewer `authored` claims: `recorded` for the journal route, as for every single-source claim;
   the person key's own tier is unchanged by a review (a review is not a public identifier and not a second source for
   identity). No new person key is minted by this route at all.

How the network questions are answered under this design: REVIEWS (Work->Work) is complete for matched reviews;
REVIEWED (Person->Person) appears where the reviewer was attached by ORCID, H-Net, or the journal route; for the
rest the graph build should expose the printed reviewer names on the Work node (and a `reviewer_names` list on the
book, derived) so "who reviewed X" is answerable by name while "what did Y review" is answered only for keyed Y.
That asymmetry is the price of "a wrong merge is worse than a missed one", and it is the right price here.

## Flaws in steps 1-3 and concrete rules

**Step 1, title matching.**
- 893,591 rows (27%) have a blank title; they cannot match by title at all. Try the Crossref record of the 10.2307 DOI
  for a title before giving up; otherwise skip.
- JSTOR titles very often append the book's author (and series notes) after the title: "The Great Cat Massacre and
  Other Episodes in French Cultural History. Robert Darnton", "…Working Class, Coll. Pélican n o 1000 E. P. Thompson".
  Strip trailing creator-name tokens before normalising, and compare `key_lc_works.title_key` of the main title (before
  ":") rather than whole-title equality; 86,446 titled rows end in a creator's family name.
- Generic headings masquerade as titles: "Review" (4,105), "Book Reviews", "New Books", "Book Notes", "BULLETIN",
  "NOTES BIBLIOGRAPHIQUES", "Books Received". Blacklist a title key with fewer than two words and any key that is a
  section heading.
- Short and shared titles: 9,951 keyed title keys are shared by two or more keyed books; 99,586 main titles are under 12
  characters. Rules: (i) require the review date >= book year - 1 (the probe found 2,454 matches dated before the book,
  i.e. earlier books or editions of the same title); (ii) require the date <= book year + 8 for titles of three words
  or fewer; (iii) when several keyed books fit (581 cases) attach to none and queue; (iv) a family-name match must be
  on the matched book's own author, not any keyed book of that title.
- Multi-volume works: ~101k titles carry vol./volume/Band/tome. Matching at work level is right, but keep the volume
  string as a member of the review (`volume:` ) so a review of vol. 2 is not conflated with one of vol. 1 later.
- Review essays: 22,582 titles contain ";" and many rows have 4+ creators. These list the authors of every book under
  review. Rule 2 would strip only the matched book's authors and read the other books' authors as reviewers, giving
  false REVIEWED edges between authors. Rule: if after removing the matched book's headings more than two creators
  remain, or the title contains ";" or " and " joining two titles, classify as `collective` and record no reviewer
  (as key_reviews already does for H-Net collective reviews); match each title segment separately if wanted.
- Parse noise in creators: split names ("Harold M.", "Mayer"), a publisher as a creator ("John Wiley"), empty names
  (42,136 rows with a blank first creator), and 500,888 of 3.05M creator rows are initials-only. Drop empty and
  initials-only creators from reviewer inference (they can stay as printed members).

**Step 2, reviewer = creators not among LC 100/700.**
- LC headings are incomplete: older records trace only the first author (rule of three), and co-authors, editors of a
  festschrift, or a translator are sometimes missing from 700. A co-author absent from LC would be read as the reviewer
  and get a REVIEWED edge to their own co-author. Rules: also exclude any creator whose family name appears in the
  review's own title string, in the LC 245$c statement of responsibility, or among the work's keyed authors from any
  source (ORCID, H-Net); and cap inferred reviewers at two per review (JSTOR reviews rarely have more), holding the rest.
- Translators: exclude 700 with relator trl as now; note that a review of a translation names the translator in the
  title, so the title-string exclusion above catches translators LC did not trace.
- A reviewer sharing the author's family name (a different Smith reviewing Smith) is lost; accept the loss.
- Order is not reliable (reviewer-first is common but "Robert Darnton, Deborah D. Rogers" and "E. P. Thompson,
  H. McQueen" occur); never use position.

**Step 3, minting.**
- Anchor the review `doi:10.2307/<id>` with member `jstor:<id>`, kind `review`, label "Review of <book> (<journal>,
  <year>)". When Crossref gives the publisher DOI of the same review (same journal, year, book, reviewer surname),
  attach it to the same work rather than minting twice; otherwise the lead's book shows eight reviews instead of six.
- Mint only reviews of keyed books (163,125 matched in the probe, with 50,503 title-only matches rejected for lacking
  the author's name among creators). A JSTOR review of an unkeyed book is not useful yet and would add ~2M works.
- The `reviews` claim should carry the matching basis in its anchor (`jstor-review:<doi>:<book key basis>`) so the title
  rule can be tightened later and bad matches detached without touching the review work.

## Smaller points
- JSTOR coverage is partial (the lead's book: 2 of 6 reviews here). Run the per-book Crossref query for the books of
  keyed historians of interest first (established keys with an ORCID or LC anchor), not for all 578k books.
- The review-credit keys from H-Net (41k) are a precedent, but they carry an affiliation and a dated source page;
  a JSTOR name has neither, which is why this route should mint no person keys at all.
- Keep a count in the proposal summary: matched reviews, collective reviews held, reviewers attached by ORCID / H-Net
  / journal route, reviewers left as names; the ratios will say whether the journal route is pulling its weight.
