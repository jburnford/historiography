# Allan Greer: person entry draft (Canadian persons, Tier 2, 2026-10-14)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- Rel_04 (the staples critique) is released.
- The shared Palmer review record's scope note now reads 'Used in the Curtis and Greer entries.'

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json).

The user (2026-10-14) called the Tier 2 candidates "obvious". The candidate line in
`canadian-person-candidates-2026-10-14.md` covers:
- *Colonial Leviathan*;
- *The Patriots and the People*;
- *Property and Dispossession*;
- "a critic of liberal order and of settler-colonial framing".

The second half of that last phrase is confirmed (rel_03). The first half is not (see below).

**Revision.** Validated in memory against live **1.138**. Ids use the `pe139_greer_` prefix. The
Palmer review carries `pe139_curtis_palmer_1993` because it reviews both books. It appears with
identical content in both drafts, and the applier keeps one copy.

**Validation** (historical, drafting stage; `ct2scripts/validate.py`, session scratchpad). Result: **0 errors and the 7
baseline warnings**, with no new warnings. This holds alone (180 nodes, 996 edges) and with the
Curtis draft (181 nodes, 998 edges). Three edges link to Greer's existing roster rows. A new
`cdn_national_tradition` row is linked to rel_04. Both text revisions match exactly once.

## Relation to the Ouellet entry (1.138)

- **Greer's 1981 critique of Ouellet** stays in `edge_989` (`quebec_historiography →
  fernand_ouellet`). It is not repeated here.
- **No `fernand_ouellet` edge is proposed.** The distinct later intervention is Ouellet's 1995
  review essay on *The Patriots and the People* (*Histoire sociale / Social History* 28:56). It
  is still unread: the journal's OJS returned a browser check. Greer's 1993 book is also unread,
  so neither side of the Patriots exchange can be quoted in its author's own words.
- **rel_01** cites the 1981 article only for representative works and for its mechanism (wage
  labour fitted to the household economy). It cites the 1993 book only through reviewers'
  wording, labelled as theirs.

## What is proposed

- **Node `allan_greer`.** The twelve person keys, with four sentences:
  1. the household-centred feudal habitant society, in his 1985 words, with his own "No doubt the
     debates will continue";
  2. the staples critique;
  3. *Colonial Leviathan*, with Palmer's criticism and Greer's 2019 self-criticism, and the
     rebellion book through reviewers;
  4. settler colonialism historicised, with "I am not here to trash or dismiss settler-colonial
     theory".
- **Edges.**
  1. `allan_greer → quebec_historiography`: contribution, no strand (see note), roster_row
     `quebec_historiography`. "Peasant, lord and merchant, 1981–93".
  2. `allan_greer → liberal_order_framework`: **comparison**, undirected, strand
     `state_formation_roots`, roster_row `liberal_order_framework`. "Colonial Leviathan, 1992". It
     is a comparison, as in Valverde's `edge_966`, because no checked text joins the volume to
     McKay. It includes Greer's own 2019 judgment that the volume "neglected everything to do with
     Indigenous peoples and processes of elimination".
  3. `allan_greer → settler_colonialism`: critique, strand `critiques_and_limits`, roster_row
     `settler_colonialism`. "Settler colonialism and beyond, 2018–19". It is post-2000 and dated.
     It keeps his explicit sympathy ("qualified support"; Wolfe "still the most important
     theorist").
  4. `allan_greer → cdn_national_tradition`: critique, *optional*, strand `staples`.
     "Staples and the subsistence household, 1985". It comes from his critique of Pentland, and
     the note says the essay is aimed chiefly at Pentland. A new roster row (critic) is linked to
     it.
- **Text revisions:**
  - `state_formation_roots` focus, shared with Curtis: apply once.
  - `transition_to_capitalism` focus: removes the PhD counts ("Greer: 5 of 16, lift 4.2";
    Bradbury's 13 of 44) from entry text. Sol's 1.136 finding 1 bars them. They move to
    `citation_evidence`.

## Verification: what was read

| Source | Status | Read |
|---|---|---|
| `pe139_greer_pentland_1985` | read in full | pp. 7–22 (L/LT PDF, text layer and OCR) |
| `screq_greer_2019_jcha` (addendum) | read in full | pp. 61–79 and notes 80–86 (Érudit PDF served to an ordinary WebFetch request; text layer) |
| `lof_greer_2018` (addendum) | introduction read | Cambridge Core HTML, pp. 1–24, no page markers, so no locators |
| `pe139_curtis_palmer_1993` | read in full | pp. 365–367 |
| `pe137_ouellet_greer_1993` (addendum) | publisher summary only | OpenAlex; book unread |
| `pe137_ouellet_greer_1981`, `pe137_ouellet_dessureault_1998`, `pe137_ouellet_cardinal_1999`, `qcreq_rudin_1995` | not re-read | quotations as recorded for the Ouellet entry and in evidence-quebec.md |
| `lof_greer_1985`, `lof_greer_radforth_1992`, `screq_greer_2019_wmq` | not read | publisher description, metadata, opening only |

**Faults avoided:**
- **Reviewers' wording is marked as theirs.** This applies to Dessureault and Cardinal on 1993,
  and to Palmer on 1992.
- **The "critic of liberal order" label is not adopted.** No text by Greer criticising McKay was
  found. The 2018 introduction argues against property as "a single thing, the hallmark of
  civilization and modernity", but does not name McKay. This is recorded in
  `edges_considered_not_proposed`.
- **Proxies are named.** rel_04 says it stands for one passage of a Pentland review.
- **No PhD counts in text.**

## Access record

- **Érudit** served the 2019 PDF once, through WebFetch. Its Anubis check then appeared (for the
  Curtis draft's 1985 article), and no further Érudit request was made.
- **Bot or browser checks** also blocked:
  - *Histoire sociale / Social History* (Ouellet 1995; an unidentified review page, article 16492);
  - *Left History* (Errington's review).
- **Other blocks:**
  - the Internet Archive copies of the 1985, 1992 and 1993 books are lending-only, and
    search-inside returned 403;
  - the UTP page for "1837–38: Rebellion Reconsidered" (CHR 1995) returned 403.

## Open questions for the editor

1. **rel_02, kind.** Comparison or contribution? Should the `liberal_order_framework` roster row,
   which also covers his 1985 book and property work, carry this edge's id?
2. **rel_04.** Keep the optional staples critique? It fills a gap, since there is no critique of
   the staples strand. But Greer's main target, Pentland, is not in the atlas.
3. **rel_01, strand.** Should it target `rebellions_1837_interpretations` if the 1985 half is
   dropped?
4. **Next reads.** Ouellet's 1995 review essay and Greer's "1837–38: Rebellion Reconsidered"
   (1995) are the next reads for the Patriots debate. They would allow a Greer–Ouellet edge in
   both authors' own words.
5. **Not covered.** Greer's New France and Jesuit work (*The People of New France*, 1997;
   *Mohawk Saint*, 2005) may deserve a later native_newcomer or religion edge.
