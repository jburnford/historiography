# Atlas Wikidata QID review (2026-10-30)

The user asked for this on 2026-10-30, after keying the canon map revealed that `immanuel_kant`
carried Q78129 (Gustav Teichmüller): "fix Kant and probably do a systematic review of all of the
QIDs".

The review covers all 713 accepted QIDs in [data/people-wikidata.json](../../people-wikidata.json).
542 of them were applied in bulk on 2026-09-22 *without individual review*.

**How it was run**
- Script: `scripts/review_atlas_qids.py` (re-runnable). Its output is `review.csv`, one row per
  person, and `summary.json`.
- Facts about each item came from the Wikidata Query Service. The public QLever endpoint was
  returning 502s.
- Candidate searches used the WikidataMCP (`search_items`), and every candidate was checked against
  its statements (`get_statements`). The MCP returns real QIDs, but its ranking cannot be trusted on
  its own: for "Immanuel Kant German philosopher" it ranks Teichmüller first.

## Checks

1. **Mechanical.**
   - The item exists, is not a redirect, and is a human (P31 = Q5).
   - A label or alias carries the atlas surname, and the first given names agree.
   - The occupations include something scholarly.
2. **Independent routes.**
   - The dissertation graph's own QID for the same person, through the canon-map key joins or an
     exact name-key candidate.
   - The person registry v12 (ORCID → QID).
3. **Works.** A Wikidata work credited to the QID (P50), of three or more words, appears in the
   atlas text that credits this person. Confirmed 42.
4. **Library of Congress.** The item's LCNAF (P244) leads to an authority record whose 670 source
   titles appear in the atlas text. Confirmed 20.
5. **By hand.**
   - Every flagged item was checked.
   - The descriptions and birth years of all remaining unconfirmed items were scanned: the 198 whose
     name belongs to a single Wikidata human, and the 50 whose name is shared or absent.

## Results

**Corrections to the sheet:**

| Person | Was | Now |
| --- | --- | --- |
| Immanuel Kant | Q78129, Gustav Teichmüller | **Q9312** |
| Sándor Ferenczi | Q12355577, a Hungarian archaeologist | **Q335466**, the psychoanalyst. The atlas cites him in the Freud entry. |
| Alexander Savine | Q103846282, an American composer | **Q16514980**, Aleksandr Savin (1873–1923), Vinogradoff's student |
| Peter Pesic | Q136036202, a Serbian basketball referee | **rejected**; no item exists |
| Peter D. McClelland | Q47356633, a Canadian rower | **rejected**; no item exists |
| Kitty Smith | Q119117255, an entomologist | **rejected**; no item for the Southern Tutchone and Tlingit elder |
| Patricia O'Brien | Q7145777, a Canadian accounting economist | **rejected**; no item for the historian (Foucault chapter, *New Cultural History*) |
| Deborah A. Gordon | Q2310251, a myrmecologist | **rejected**; no item for the anthropologist (*Women Writing Culture*) |
| Quintin Hoare | Q16938681, right person | Placeholder dates 1900/2025 **removed** from the sheet's life field |

**Bulk error rate.** All eight wrong QIDs came from the bulk match: 8 of 542, or 1.5%. Three of them
(Kant, Ferenczi, Savine) were cases where the match chose among namesakes it had itself listed.

**Checked and confirmed by hand.** These were flagged by the mechanical checks but are correct:
- Angela Sidney, Rita Huggins, Jane M. Jacobs (the geographer), D. F. McKenzie, George Sessions,
  Milton Rogovin, Dave Foreman, Armida de la Vara.
- James Vernon, Jon Lawrence, Antoinette Burton and Norbert Elias. For these four the atlas is
  right; see "Dissertation-side errors" below.

**Final verdicts** on the 708 accepted QIDs:

| Verdict | People | Meaning |
| --- | ---: | --- |
| confirmed | 466 | Individually reviewed, or an independent route, works or LC sources agree |
| plausible | 242 | Name, human and occupation fit; description and birth year scanned by hand; no independent confirmation found |

The atlas text for most roster people describes their role in someone else's entry. It does not list
their own books, so the works and LC title checks cannot confirm them. The remaining risk is a
namesake whose description happens to fit.

## Dissertation-side errors found on the way

These are errors in the dissertation graph's automatic QIDs. They are not fixed here. They are
recorded so the next grounding run can override them in `person-wikidata-decisions.csv`.

| Dissertation person key | Its QID | Actually |
| --- | --- | --- |
| `vernon\|james` | Q6144651 | an English politician (1646–1727) |
| `elias\|norbert` | Q124644194 | Ann Elias, an art historian |
| Burton key joined to Antoinette Burton | Q133344893 | Eric Burton, a historian born 1987 |
| `lawrence\|jon` | Q64594177 | Jon M. Lawrence, a researcher |
| `obrien\|patrick` | Q7145777 | Patricia O'Brien (accounting); the cited person is the economic historian Patrick O'Brien |

## Follow-ups

- **Commit, then re-key.** Once `data/people-wikidata.json` is committed:
  - `key_atlas.py` will attach the corrected QIDs (Kant, Ferenczi, Savin) as anchors;
  - `key_canon_map.py` will join Kant, now that both sides agree on Q9312.
- **Reviewed QIDs as anchors.** The 466 confirmed QIDs can be promoted to exact anchors in the key
  log. At present only individually reviewed methods are anchors.
- **The 242 plausible.** The Library of Congress route through the person's own books (see
  `../lc-authority-pilot-2026-10-30`) can confirm many more. Persons with no LC record stay
  plausible.
- **No QID at all.** Four people are unmatched, 282 roster people were never grounded, and five are
  now rejected. The LC route and the MCP search are the next step for them.
