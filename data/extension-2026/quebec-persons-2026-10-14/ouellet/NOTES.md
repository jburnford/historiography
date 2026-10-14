# Fernand Ouellet: person entry draft (Quebec persons, 2026-10-14)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json). The evidence base is
[../../quebec-historiography-2026-10-14/evidence-quebec.md](../../quebec-historiography-2026-10-14/evidence-quebec.md)
(committed as 497783b). The user (2026-10-14) asked for it: "we also probably need Ouellet and
then some of his critics".

**Revision.** The brief said to validate against 1.136. The working graph is now **1.137**
(Said, Guha, Spivak), so the draft was validated in memory against live 1.137 and is proposed for
the next revision. Ids keep the requested `pe137_ouellet_` prefix. They do not collide with
1.137's `pe137_said_` / `pe137_guha_` / `pe137_spivak_` sources.

**Validation** (throwaway script in the session scratchpad). It does the following in memory:
- appends the node and sets `node_id`;
- adds 4 new people, 13 new sources and 3 source addenda;
- adds 6 included edges (`edge_988`–`edge_993`) and links edge 1 to Ouellet's `quebec_historiography` roster row;
- applies the 3 `text_revisions`, each with an `old` that matches exactly once;
- adds 6 roster rows.

Result: **0 errors and 8 warnings**, against 0 and 7 for the unmodified graph (179 nodes, 993
edges). The one new warning is the expected repeated pair "Repeated endpoint/type combination in
edge_991": edges 3 and 4 are both `fernand_ouellet → quebec_historiography` critiques. They
target different strands. See the open questions.

## What is proposed

- **Node `fernand_ouellet`.** The twelve standard person keys. The date label lists dated works
  only. The description has four sentences:
  1. his framework, in his words from 1962, with the qualification "pas le seul moteur";
  2. the mentalities claim (1962, 1976);
  3. three in-period critics in their own words, Tousignant's qualification ("une notable
     amélioration") kept;
  4. his 1985 critique of the Montreal school and the modernists.
- **`people_update`.** The existing record (`fernand_ouellet`) gets `node_id`. His only roster
  row is on `quebec_historiography` (role historian). He appears in the `laval_school`,
  `agricultural_crisis_debate` and `normal_society_debate` strands. Edge 1 sets
  `roster_row: quebec_historiography`.
- **Edges.**
  1. `fernand_ouellet → quebec_historiography`: contribution, `agricultural_crisis_debate`.
     The crisis from 1802 and peasant routine behind nationalism and, "en grande partie", 1837–38
     (1962–76).
  2. `quebec_historiography → fernand_ouellet`: **critique**. Paquet and Wallot (1972),
     Tousignant (1980) and Greer (1981) in their own words. Greer 1993 is given only through the
     reviewers' words (Dessureault, Cardinal), labelled as theirs. Ouellet's 1976 reply is
     included.
  3. `fernand_ouellet → quebec_historiography`: **critique**, `montreal_school`. Séguin's
     "décapitation" thesis, taken up by Brunet, read as a neo-nationalist schema. The trauma is
     placed "pas au moment de la conquête" (1976). Séguin has no node, so the strand is the target.
  4. `fernand_ouellet → quebec_historiography`: **critique**, `modernist_synthesis`. In 1985,
     economic history "par trop centrée sur la situation précaire des Canadiens français" and
     "pas étranger à la montée du mouvement indépendantiste". The revisers of Séguin's model are
     followed by Robert, Linteau and Normand Séguin.
  5. `donald_creighton → fernand_ouellet`: influence. The 1962 article borrows Creighton's
     "société féodale décadente". Paquet and Wallot pair the two (1972, p. 186 n. 5). This is a
     borrowed characterisation, not a lineage.
  6. *(optional, included)* `ernest_labrousse → fernand_ouellet`: influence. The debt is known
     only through Savard ("Ouellet a dit sa dette…") and the critics' "position Labrousse".
     `edge_874` already carries this at group level.
- **Roster additions on `quebec_historiography`:**
  - `gilles_paquet` (critic; existing person, already in the strand, no roster row);
  - `allan_greer` (critic; existing person);
  - new people `pierre_tousignant` (critic), `jean_paul_bernard`, `normand_seguin` and
    `t_j_a_le_goff` (historians).
  - The Le Goff identity note distinguishes him from `jacques_le_goff`; the Normand Séguin note
    distinguishes him from Maurice Séguin.
- **`text_revisions`** (batch format):
  - the `agricultural_crisis_debate` focus, which said "titles only", and its works;
  - the `montreal_school` focus, which adds Ouellet's "théoricien" and Tousignant's "maître à penser".
- **Not consumed by the applier, for the editor:**
  - `strand_list_additions`: new person_ids and source_ids for those two strands. Lists cannot be
    changed by `text_revisions`.
  - `proposed_new_strands`: `rebellions_1837_interpretations`. It needs an applier extension or a
    manual edit.

## Verification: what was read

The scratch copies were wiped by a machine restart. They were re-fetched on 2026-10-14 through
the WebFetch tool's ordinary requests, which Érudit served for six PDFs; then Érudit returned its
bot-check page and attempts stopped. No challenge was solved. The scanned PDFs were OCR'd locally
(French or English Tesseract). Every page number below was re-checked against the printed folios.

| Source | Status | Read |
|---|---|---|
| `qcreq_ouellet_hamelin_1962` (addendum) | read in full | pp. 17–33 |
| `qcreq_paquet_wallot_1972` (addendum) | read in full (1972 only) | pp. 185–237 |
| `pe137_ouellet_mythe_1976` | read in full | pp. 115–132 |
| `pe137_ouellet_modernisation_1985` | read in part | pp. 11–29, 38, 47, 51–52, 64–68; the rest by name search |
| `pe137_ouellet_tousignant_1980` | read in full | pp. 415–436 |
| `pe137_ouellet_greer_1981` | read in full | pp. 197–214 |
| `pe137_ouellet_bouchard_1990` | read (OpenEdition, ¶) | ¶6, ¶13 |
| `qcreq_savard_1974` (addendum) | read (OpenEdition, ¶) | ¶8, ¶11 |
| `pe137_ouellet_dessureault_1998`, `pe137_ouellet_cardinal_1999`, `pe137_ouellet_rudin_1995b` | read in full earlier on 2026-10-14 for the evidence file | not re-fetched (bot check); the quotations are those recorded then, and the notes say so |
| `qcreq_rudin_1995` | read on OpenEdition earlier the same day | no addendum |
| `pe137_ouellet_le_goff_1974`, `pe137_ouellet_greer_1993`, `pe137_ouellet_bernard_1983`, `pe137_ouellet_bas_canada_1976`, `pe137_ouellet_elements_1972` | metadata only | unread |
| `qcreq_ouellet_1966`, `cdng_ouellet_1980`, `pe135_creighton_ouellet_1984`, `cdng_creighton_1937` | reused | not re-read; cited as recorded or as quoted by others |

**Faults avoided** (Sol's 1.136 list):
- **No PhD counts in text.** They are in `citation_evidence` only.
- **Qualifications kept:**
  - "pas le seul moteur" (1962);
  - Tousignant's "notable amélioration" and closing credit;
  - Paquet and Wallot's "Quant à savoir si le débat est résolu…, nous ne saurions le dire";
  - "comme la plupart de ses prédécesseurs".
- **Reviewers' wording labelled.** On Greer 1993 the words are the reviewers' (Dessureault,
  Cardinal), marked as such.
- **Ouellet's book quotations attributed.** Quotations from his books come only as Paquet and
  Wallot quote them, with their page references.
- **Le Goff not counted as a critic.** His article is unread, and Ouellet reports he supported a
  crisis.
- **"Founder" avoided.** Bouchard's "avec quelques autres" is quoted instead.

## Open questions for the editor

1. **Edges 3 and 4** repeat the pair `fernand_ouellet → quebec_historiography` (critique), which
   adds one validator warning. Keep both (they are different claims on different strands), or
   merge them into one edge without a target strand?
2. **Maurice Séguin entry.** If he gets an entry (recommended in the evidence file), retarget
   edge 3 to `maurice_seguin`.
3. **Labrousse influence.** Keep edge 6, or rely on `edge_874` alone?
4. **Applier support.** The strand list additions and the new rebellions strand need an applier
   extension (or manual edit).
5. **Ouellet's reply to Greer.** His 1995 review essay on Greer (*Histoire sociale* 28:56)
   remains unread because of the browser check. It is the obvious next read before the edge 2 note
   is finalised.
6. **Wikidata.** Q3069288 is correct (MCP checked). Carleton as employer is unverified; his
   archive is at York.


## Release (1.138)

Revision 1.138, baseline 1.137. Five edges (rel_04 merged into rel_03, same endpoints and type), 992 relationships, 0 errors and the 7 baseline warnings. The applier now supports `strand_list_additions` and `new_strands`, so both are applied from `batch.json`. Earlier references above to 'proposed revision 1.137', eight warnings or an applier extension being needed are historical. Sol's review and the fixes are in `release/`.
