# Adele Perry: person entry draft (Tier 2 Canadian persons, pe139)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- **Edge 3 now targets `sylvia_van_kirk`**, released in the same revision; its evidence no longer describes a strand target or a possible re-pointing (finding 11). Open question 1 is resolved this way, and the table and bullet below are superseded.
- The `cdn_women_gender` row stays a comparison row (open question 2): its context is rewritten without counts or 'title and chapter level', and the 1995 essay is added to its sources and works (finding 2).
- The `settler_colonialism` row context and the `gender_family_nation` focus no longer say 'metadata' only; they name the read essays and reviews and keep the book unread (finding 3). Sources are added to the row and strand.
- Edge 1 now says that no derivation from Wolfe is established by the texts checked (finding 4).

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and nothing
was committed. The draft is in [entry-draft.json](entry-draft.json).

## Validation (historical, drafting stage)

The brief named live revision 1.138 or later. During drafting the live file moved to **1.139**,
which changed only the seminar pathways; the graph content is the same as 1.138.

I applied the draft in memory to live 1.139. It adds the node, `node_id` on `adele_perry`,
6 new sources, four edges (`edge_993`–`edge_996`), one roster `edge_id`, one roster addition and
one text revision. Results:

- **Alone:** 0 errors and the same 7 warnings as the unmodified graph (180 nodes, 996 edges). No
  new warnings.
- **Together with the Harris packet:** 0 errors and 8 warnings. The extra warning comes from the
  Harris packet's optional Atlas edge.

The source `pe139_perry_forum_2016` is shared, identically, with the Harris packet.

## What is proposed

- **Node `adele_perry`.** The twelve standard person keys. The date label lists works from 1995 to
  2015; post-2000 work is dated.
- **`people_update`.** Sets `node_id: adele_perry`.
- **Wikidata.** Q64626780, already in `data/people-wikidata.json`, is "probably correct; thin
  item". It is cross-checked through its Semantic Scholar author ID, whose work list matches
  hers.
- **`text_revisions`.** The `cdn_women_gender` comparison row loses its PhD counts ("67% of the
  122 PhDs … lift 2.9"), per finding 1 of the 1.136 review. The counts move to
  `citation_evidence`.

### Edges

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | → settler_colonialism | contribution | Gender, race and a settler colony, 1995–2001 | gender_family_nation | yes (historian) |
| 2 | → cdn_women_gender | contribution | Gender imbalance, race and whiteness, 1995–2001 | comparison_fur_trade_empire | no (comparison row, see below) |
| 3 | → sylvia_van_kirk (retargeted at release) | critique | Perry: mixed-race unions beyond white women's absence, 1995–2001 | person target | new `native_newcomer` row (critic), unlinked |
| 4 | post → | influence | Gender and colonialism literature, 1995–2001 | person target | no |

- **Edge 2 and the comparison row.** Her `cdn_women_gender` row has role `comparison` and basis
  `editorial_comparison`. Linking a contribution edge to it would change its meaning, so it is
  left unlinked. If the editor wants the edge on the roster, the row's role should be revised
  deliberately.
- **Edge 3 and the Van Kirk packet** (drafting-stage reasoning, superseded at release: the edge targets
  `sylvia_van_kirk`). It criticises Van Kirk's explanation of intermarriage. It
  targets the strand, not `sylvia_van_kirk`, so as not to cross the sibling Van Kirk packet, which
  cites Perry only through her 2008 Left History essay as a later reading. Her 1995 notes 8 and 11
  are the in-period evidence the Van Kirk drafter may want.

## What was read

**Her own words**
- "Oh I'm Just Sick of the Faces of Men" (BC Studies 105/106, 1995, pp. 27–44). Read closely at
  pp. 27–33 and 42–43; the middle skimmed.
- "Presence, Absence, and the Writing of BC History" (BC Studies 132, 2001/02, pp. 57–64), read in
  full.
- Her reply in the 2016 BC Studies forum on Colonial Relations (pp. 106–108 and 112–113). A later
  reading.

**Reviews of On the Edge of Empire, read in full**
- **Carter, BC Studies 136 (2002/03).** p. 118 is missing from the single-review PDF and was read
  in the issue's review PDF.
- **Orlowski, Left History 8:1 (2002).** Read in an Internet Archive capture, because York's site
  serves a browser check.
  - A search-engine summary attributed this review to Greg Dening. The PDF shows it is
    Orlowski's; Dening reviewed the preceding book.
  - Nothing in the draft relies on the summary.
- **Rutherdale, Labour/Le Travail 50 (2002).**

**Later reading.** Ballantyne in the 2016 forum (pp. 104–105).

## What could not be read

- **On the Edge of Empire itself.** Book quotations come only through Carter, Orlowski and
  Rutherdale, with their page references. The Google Books API quota was exhausted, and the UTP
  chapters are on De Gruyter, which has a bot wall.
- **"The Historian and the Theorist Revisited" (Histoire sociale/Social History, 2000).**
  - It sits in a round table with Valverde and Palmer, which makes it a strong lead for a
    critique or comparison edge.
  - The York site has a Cloudflare check, and there is no Wayback capture.
- **"Fair Ones of a Purer Caste" (1997).** Not read.
- **The 2009 liberal-order chapter.** Still title level, so no `liberal_order_framework` edge is
  proposed.
- **Colonial Relations (2015).** Not read.
- **Caroline Andrew's review (Recherches féministes, 2002).** On Érudit, which has a bot wall;
  not attempted.

## Faults avoided (from the 1.136 and 1.138 reviews)

- **No PhD counts in text.** The count in the existing roster text is removed.
- **Reviewer characterisations are marked as theirs.** Stoler's influence rests on Rutherdale's
  and Orlowski's statements, and edge 4 says so.
- **Qualifications kept:**
  - Van Kirk's account is a "brilliant account" and "pioneering work";
  - her own admission that her analysis "minimizes the subjectivity of First Nations people";
  - her caution about analysing "white discourse and white discourse alone".
- **The printed sentence ending "erasure of dispossession settler consciousness" is not silently
  repaired.** The quotation stops at "dispossession" and a note explains why.
- **The 2016 self-reading and Ballantyne's reading are labelled as later readings.** They do not
  carry the dated claims.

## Open questions for the editor

1. Should edge 3 point at `sylvia_van_kirk` if the Van Kirk entry is released in the same batch?
2. Should the `cdn_women_gender` comparison row become a `historian` row linked to edge 2?
3. The source of edge 4: `post` (chosen) or `gender/colonial_categories`? Both hold Stoler.
4. Leads:
   - read the 2009 liberal-order chapter (contributor row exists) and the 2000 Histoire sociale
     round table;
   - her 2008 Left History essay on Van Kirk, already read by the Van Kirk drafter, may also bear
     on edge 3.
