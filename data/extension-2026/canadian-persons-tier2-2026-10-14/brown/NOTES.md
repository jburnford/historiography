# Jennifer S. H. Brown: person entry draft (Tier 2 Canadian persons, pe139)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- The 1991 Ethnohistory address is an **indexed excerpt only** (OpenAlex's abstract field); p. 113 is its recorded first page, and the page itself was not inspected. Node scope note, rel_02 evidence and the source record now say so (finding 5). The methodological contribution rests independently on the 1983 essay.

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). It is validated
together with [../vankirk/](../vankirk/NOTES.md) against live revision 1.138, with 0 new errors
and 0 new warnings. That note gives the details.

## What is proposed

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | → native_newcomer | contribution | Company families and Métis emergence, 1980–85 | fur_trade_families_metis | yes |
| 2 | → ethnohistory | contribution | Ethnohistory of Rupert's Land, 1983–96 | documentary_method | no row |

The comparison with Van Kirk is drawn once, as `pe139_vankirk_rel_03` in the Van Kirk draft.
LaRocque's criticism, which names Brown and Van Kirk together, is drawn once, as
`pe139_vankirk_rel_04`, and is quoted on Brown's rel_01.

### Rel_01: company families and Métis emergence

- **Her own words** (*CJNS*, 1983, read in full):
  - "Biologically, métissage ... the meeting and mingling of Indian and white racial groups.
    Socially and culturally, it has had a complex history". Both halves are quoted, so the
    qualification is kept.
  - The two-to-one daughters-and-sons pattern in her St. Gabriel Street sample.
  - "the maternal element as formative in metis emergence".
- **The book through reviewers:**
  - Gresko (1981) gives the title's legal sense and the HBC/NWC contrast. She also criticises:
    "academic thesis", "bits of anthropological theory", and no mention of Jamieson.
  - Bowsfield (1981) adds "hinterland to metropolis".
- **Later readings, labelled:**
  - Gaudry (2013) uses Peterson and Brown (1985) for the small-m/big-M distinction. Quoting
    Andersen (2011), he rejects "ostensible mixedness" as a definition. The edge says he does
    *not* aim that criticism at Peterson and Brown.
  - Brown's own 2017 retitling of her 1985 essay explains that "Métis" in 1800s Rupert's Land
    meant Catholics of French-Canadian paternal origin.

### Rel_02: ethnohistory

- **Her own in-period words:**
  - the 1983 use of Bishop and Krech's "matriorganization" and Asch's "unilocality" on HBC
    district reports and the 1818 Red River testimonies;
  - an indexed excerpt only (OpenAlex's abstract field) of her 1991 presidential address to the
    American Society for Ethnohistory; p. 113 is the recorded first page, not an inspected page.
- **Title-level:** *The Orders of the Dreamed* (1988) and *Reading Beyond Words* (1996). Fiske
  (2000) cites the latter for "a rhetorical approach that subjects both oral and written
  narratives to textual analysis".
- **"The Blind Men and the Elephant" (1990).** It is read only in a revised 2017 reprint (the
  reprint cites a 2014 book), so it is used only as a labelled later text.

## Verification: what was read

### Read in full
- Brown, *CJNS* 3:1 (1983), pp. 39–46, from an Internet Archive capture of Brandon University's
  CJNS archive.
- Gresko, *Canadian Woman Studies* 3:2 (1981), pp. 112–13, from an Internet Archive capture.
  - The OJS record is titled for the next review on the page.
  - A separate Atlantis "Strangers in Blood" record (6:2, 1981) actually holds Gresko's review of
    *True Daughters of the North*.
- Gaudry, *aboriginal policy studies* 2:2 (2013).

### Read in part
- The 1991 *Ethnohistory* address: indexed excerpt only (OpenAlex's abstract field); the page
  itself was not inspected.
- *An Ethnohistorian in Rupert's Land* (2017, open access): acknowledgements, part
  introductions, chapter 3, the opening of chapter 9, chapter 11 and the publication credits.

### Shared with the Van Kirk draft
- Bowsfield (1981).
- Gagan and Turner (1982).
- LaRocque (1999).
- Fiske and McPherson (2000).
- Perry (2008).

### Not read
- *Strangers in Blood* (Internet Archive copy borrow-only).
- *The New Peoples* (1985), including the introduction and "Diverging Identities" in their
  original form.
- *The Orders of the Dreamed*.
- *Reading Beyond Words*.
- The full 1991 address.
- The 1990 original of "The Blind Men and the Elephant".
- "Partial Truths" (2001).
- Andersen (2011).
- Closed reviews: McCalla, *AHR* 1982; Kay, *WHQ* 1981; Nichols, *WHQ* 1986; Jaenen, *AHR* 1986;
  Slobodin, *Ethnohistory* 1987.
- The *Annals of Iowa* review (1982), behind an Anubis bot wall, which I respected.
- The 2012 essay in its original form. The De Gruyter PDF returned nothing, so the 2017 reprint
  was used.

## Wikidata

**Q63075209, correct.** The cross-checks:
- University of Winnipeg: her 1983 byline.
- Harvard and Chicago: her 2012 account.
- candidates.csv also gives this QID.

Wikidata gives only US citizenship, which is not used. The birth year (1940) comes from Wikidata
alone. It can be dropped if living people should carry no birth dates.

## Open questions for the editor

1. **Ethnohistory roster row.** Add a row for Brown (historian, strand `documentary_method`) so
   that rel_02 can carry a roster link?
2. **"The Blind Men and the Elephant" (1990).** If the Boreal Institute original can be read, a
   dated critique edge to Innis's fur-trade thesis
   (`native_newcomer/fur_trade_national_economy` or `harold_a_innis`) may be warranted.
3. **The `nnreq_peterson_brown_1985` note.** It still says the year is "to confirm". The 2017
   credits and Gaudry confirm 1985 (University of Manitoba Press). Add a source addendum at
   release?
4. **Andersen (2011).** It should be read before any person-level critique of the "mixed"
   framing of *The New Peoples* is drawn.
