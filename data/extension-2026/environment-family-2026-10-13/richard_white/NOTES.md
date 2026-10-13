# Richard White: person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). It was applied in
memory to the 1.130 graph: the node, `node_id`, 17 new sources, two edges (`edge_901`,
`edge_902`) and the roster `edge_id` on `indigenous`. It passes `validate_graph` with no new
errors or warnings (0 errors and 7 warnings before and after).

**Not Hayden White.** Hayden White is people id and node id `white`. This entry uses the
existing people record `richard_white`.

## Placement: context for the editor

- **The user has queried White's placement before.** The dissertation-citation audit
  (memory note *historiography-dissertation-citations*; `audit/field-robustness.json`) found
  that *The Middle Ground* sits stably in the co-citation field "New France, early modern empire
  & the Atlantic". Its main neighbour is "Indigenous peoples, fur trade & the West". The
  audit called it a bridge work.
- **Canadian environmental historians use him mainly for the 1985 survey.** See
  [canon-evidence-canada.md](../canon-evidence-canada.md).
  - The *PHR* essay is cited in Cook 1990, Forkey 1998, Wynn 2004, Castonguay 2006 and Wynn
    2009.
  - His environmental monographs appear only twice: *Organic Machine* in a reading list, and
    *Land Use* as a model.
  - No text read there mentions *Roots of Dependency*.
  - *The Middle Ground* enters Canadian environmental-history writing once (Furst 2020), and
    only as a lead.
- **What follows for the entry.** He is drawn as one person with two separate contributions:
  - environment, which rests on his own environmental books and the field survey;
  - Indigenous history, which rests on the middle ground.

  He is not presented as a founder of environmental history.

## What is proposed

- **Node `richard_white`.** A person entry with the twelve standard keys. The date label is
  *Land Use, Environment, and Social Change 1980 · The Roots of Dependency 1983 · field survey
  1985 · The Middle Ground 1991 · The Organic Machine 1995 · coverage through 2000*.
- **`people_update`.** The existing `richard_white` record gets `node_id: richard_white`.
- **Edge 1.** `richard_white → indigenous`, contribution, labelled "Middle ground, 1991".
  - Target strand: `indigenous/middle_ground`.
  - Roster row: `indigenous`.
- **Edge 2.** `richard_white → environment`, contribution, labelled "Land use, labour and the
  field, 1980–1995".
  - Target strand: none (no strand fits; a new one is suggested in the draft).
  - Roster row: none (he has no environment roster row).
- **Sources.**
  - 17 new.
  - One addendum: `ind127_white_1991`.
  - Two reused: `ind127_white_1991` and `cronon_environment_syllabus_1994`.
- **No edge revisions.** No existing edge mentions him.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| *The Middle Ground* (1991) | Cambridge Core first-page excerpts: introduction p. ix, ch. 2 p. 50, ch. 3 p. 94, epilogue p. 518. Google Books search-within of the 2011 edition, whose body pages match 1991 (checked at pp. 50, 53, 93 and 518): p. x (2011 p. xxvi), pp. 52–53, 93. Crossref chapter records | The middle ground in his words: "creates as well as destroys"; "the place in between"; "creative, and often expedient, misunderstandings"; "mutual invention"; "stark choices between assimilation and otherness" |
| 2011 preface | Google Books snippets, pp. xi–xxi | **Later reading.** He answers Merrell, Havard and Deloria (2006): "People did not come together to love one another"; the process does not always produce a pays d'en haut |
| Savard 1992 (*JSA* 78:1, 119–120) | Read in full (Persée page text) | In-period. Praise: "inattaquable" circularity. Doubt about the premise of Iroquois devastation |
| Edmunds 1993 (*IMH*, 147–149) | Read in full | In-period. "A valuable model". The post-1770 chapters are "less convincing" |
| D. R. Miller 1994 (*CJNS* 14:1, 157–170) | Read in full | In-period and Canadian (SIFC, Regina). "Extraordinary benchmark"; he neglects groups that are neither Iroquoian nor Algonquian; the north shore of the Great Lakes remains to be studied; dependency "can also be an environmental relationship" (p. 486) |
| *Land Use* (1980; 1992 paperback) | Google Books snippets: p. 7, the 1992 preface (pp. xvii–xix) and Cronon's foreword (pp. xi–xvi) | His departure from intellectual and political environmental history; his debt to Malin; his 1991 self-criticism of climax ecology; Cronon's "underappreciated classic" |
| *The Organic Machine* (1995) | Google Books snippets: preface (page ids PP13–14) and p. 112 | The organic machine, energy and labour; environmentalists "stress the eye over the hand" |
| Cronon 1993, Worster 1990 (Portuguese), Cook 1990, Cronon 1994 syllabus | Re-read at the White passages | In-period use of his books and of the 1985 survey |
| McNeill 2003, Isenberg 2013, Wynn 2004 | Re-read at the White passages | Later readings only. McNeill on the concept's travel; Isenberg quotes the 1990 round-table response |
| Borrows 1994 (*UBC Law Review* 28:1) | Read at p. 13 n. 40 | Canadian legal use of the book as a factual source; cited only in `edges_considered_not_proposed` |

**Not read.**
- **Paywalled or blocked:**
  - PHR 1985 (UC Press 403; JSTOR challenge);
  - JAH 1990 (OUP 403);
  - Trigger's review (PHR 1992) and Dickason's (JHG 1995);
  - Carlson's JEH review (1984);
  - D. R. Miller's GPQ review of *Roots* (1985; UNL Cloudflare);
  - Webber, *Osgoode Hall LJ* 1995 (Cloudflare).
- **Not previewed:**
  - *The Roots of Dependency*;
  - "Are You an Environmentalist or Do You Work for a Living?" (*Uncommon Ground*, 1995).
- **Copies avoided:** the Internet Archive copies are lending-restricted. An unrestricted
  copy of the 2010 edition PDF on archive.org was deliberately not used.

**Small corrections found.**
- Edmunds prints "congruencies"; White wrote "congruences" (p. 93).
- Miller drops "both" from the p. 53 sentence.
- Fohlen's review (*RFHOM* 1992) calls him "Robert" White. It was read but not used.

## Edges: reasoning

**Edge 1 → `indigenous`.**
- **Evidence.** The strand `middle_ground` already holds him alone and states the checked
  argument. Its caution ("Great Lakes circumstances do not supply a universal account")
  matches his own 2011 p. xiii.
- **Wording.** The evidence note says that this is a scholar's interpretation, which the
  entry lists as "related scholarship". It is not an Indigenous historical practice.
- **Open question.** The editor may prefer `ethnohistory` as the target. Edmunds calls the book
  a landmark "in the ethnohistory of the Great Lakes tribes", and Miller titles his essay
  "Social History Meets Ethnohistory". That would mean no roster row.

**Edge 2 → `environment`.**
- **His own words.** The edge rests chiefly on *Land Use* p. 7 and the 1992 preface, and on
  the *Organic Machine* preface.
- **In-period readers.** Cronon (1993, 1994), Miller (1994), Worster (1990) and Cook (1990).
- **The 1990 round table** is evidenced only through Isenberg 2013, labelled as a later
  reading.
- **No target strand.** A new strand ("Land use, labour and Native subsistence") could be
  added at release.

**`native_newcomer`: considered, not proposed.**
- **Node text.** The node's text and strands never mention White or the middle ground.
- **Pre-2000 Canadian readings found.**
  - Savard and Miller review the book. Miller calls a north-shore study "a challenge".
  - Borrows uses it for facts on gift diplomacy, not as a framework.
- **No checked application.** No checked pre-2000 Canadian historical work applies the concept.
- **Citation data.** The heavy Canadian use shows only in post-2009 PhD citations, which are
  metadata.
- **To revisit:** read the Trigger and Dickason reviews, or a Canadian fur-trade work that
  applies the concept. Note that Podruchny 2006, already in the node, is a later reading under
  the 2000 frame.

## Founder claims and criticism

**Founder claims.** The draft makes none.
- *Land Use* credits "The trail James Malin blazed".
- Isenberg (2013) names White as one of a group who "synthesized the material and cultural
  approaches".
- Worster (1990) praises the 1985 essay as the best effort to trace the field's emergence,
  "pelo menos em uma parte influente do mundo". The draft does not call it the field's
  "first" historiography: no text read says so.

**Criticism, kept in period order.**
- **In-period.**
  - Savard: the premise of Iroquois devastation.
  - Edmunds: the post-1770 chapters.
  - Miller: peoples outside the Algonquian/Iroquoian frame.
  - White's 1992 self-critique of climax ecology.
- **Later, labelled.**
  - Merrell 1999, Havard 2003 and Deloria 2006, all known here only through White's 2011
    preface.
  - McNeill 2003 on the concept's spread.

## Wikidata Q7329939: the right person

Checked with the MCP tools: `search_items` and `get_statements`.
- **Search result.** Q7329939 ("American historian") comes first, then *The middle ground*
  (Q131716889), whose author is Q7329939.
- **Birth date.** Wikidata gives 28 May 1947. LoC n79093584 also gives b. 5/28/47 and a
  Stanford note.
- **Education.** Wikidata lists the University of Washington. This agrees with the user's
  identity decision (UW PhD 1975).
- **Existing record.** `people-wikidata.json` has no row for him yet.

## Citation evidence (metadata only)

It is kept out of the node and edge text. Source: candidates.csv; it was not recounted from
`graph.json`.
- **Overall.** 132 of the strict History PhDs from 2009–2026 cite him (10.1%), at 23
  universities.
- **Top works.**
  - *The Middle Ground*: 66;
  - *Organic Machine*: 28;
  - *Roots*: 9.
- **Placement hints.** The strongest lift is in Environmental history (4.2), then Ethnohistory
  (3.7).

## Notes for the batch build

- **Likely duplicate sources.** Sibling packets will probably cite Cronon 1993, Worster 1990,
  McNeill 2003 and Isenberg 2013 under their own `pe131_*` ids. The build should merge them so
  that each work is one source.
- **Duplicate addenda.** `ind127_white_1991` carries an addendum. Make sure no sibling also
  adds one, because `apply_person_entries.py` raises on duplicate addenda.
- **No personal identifiers sent.** No email address or other personal identifier was sent to
  any service. Unpaywall was not used.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 5.** Every quotation now names its witness at the point of quotation. Cambridge Core
  first-page excerpts (pp. ix, 50, 94, 518) are full pages with observed folios and stay
  quoted. Wording witnessed only by Google Books search-within snippets is paraphrased where it
  carries the claim: the middle-ground definition on 1991 p. x (= 2011 p. xxvi), Land Use p. 7
  (including the Malin credit), and the Organic Machine preface and conclusion (preface folios
  unseen; p. 112 taken from the page id). Non-essential snippet quotations (the 1992 preface,
  Cronon's foreword, the 2011 preface, p. 52) stay quoted with a "snippet" label. The p. 53
  phrase "existed on two distinct levels" had no recorded snippet witness in the source note,
  so it was replaced by a paraphrase of the recorded p. 53 snippet. The node description
  paraphrases the snippet-only passages and marks the remaining quotations as Cambridge Core
  excerpts. A re-try to reach Google Books page images returned 403 on 2026-10-13.
- **Finding 6.** Scope note pagination corrected: 1991 p. x = 2011 p. xxvi (inferred from the
  introduction's openings, 1991 p. ix and 2011 p. xxv). Merrell (1999) is now an in-period
  critique known through White's later 2011 response; Havard (2003) and Deloria (2006) are
  later critiques. Edge 1's later-reading section and the 2011 preface source note say the
  same.
- The table above still quotes snippet wording for the editor; it is not atlas text.
