# Timeline candidates after the Oxford / UK rebuild (2026-10-30)

User, 2026-10-30: "identify historians we need to add to the main timeline after updating the graph; we had a 100 or 150 for Canadian limit; I'm not sure if that needs adjustment."

`cited-people-vs-entries.csv` lists every first-author key cited by at least 60 dated strict History PhDs in the 2026-10-30 build. Each row gives:
- the count of dated strict theses citing the key, and its share of the 9,908 dated strict theses;
- the counts by region;
- the atlas person entry it matches, if any.

**How the counts are made.** Counts are exact keys, never summed. The scope is the same as the 1.170–1.191 queue: dated strict theses citing the key as first author.

**How keys are matched to entries.** Three routes, in order:
- the reading links and the 2026-10-25 queue;
- Wikidata QID;
- name.

Name matches are candidates and need checking. For example, "Beard, Mary" matched `mary_ritter_beard`, but the cited Mary Beard may be the classicist.

## Why the 100 / 150 rule needs a decision

The rule was set on the 2026-10-23 release: 6,794 dated strict theses, of which Canada had 2,212, the US 2,168, Europe 2,025 (almost no UK) and elsewhere 389. The 2026-10-30 build has 9,908. That is 46% more, and almost all of the growth is in the US (2,835) and the UK (2,482, about 1,900 of them new).

- **Canada is unchanged** at 2,212 dated theses. Canadian historians are cited mostly by Canadian theses, so the Canadian bar of ≥150 keeps its meaning.
- **For everyone else, an absolute bar of more than 100 now admits about 240 keys without an entry.**
  - 44 of them owe at least 40% of their citations to British theses.
  - Only 98 would clear 100 without the UK.

  The bar would move with whatever we harvest next. France is to be raised to 2,000.

**Recommendation.** Keep the Canadian bar at ≥150 and express the other bar as a share of the corpus. At the time, more than 100 of 6,794 was 1.47%. Today that is **at least 146** of 9,908 (more than 145.8), and it scales as further countries are added.

**Decision (user, 2026-10-30):** "1.47 seems like a good cut off for now". The Canadian-history bar stays at ≥150. Other historians must exceed 1.47% of dated strict theses, which is 145.8 in the 2026-10-30 build, so **at least 146** theses (100 of 6,794 = 1.4719%).

**Revised bar (user, 2026-10-30): "I think Paul Thompson is the better cut off".**
- Other historians now need at least 136 dated strict theses (1.37%), the count of Paul Thompson the oral historian after his namesakes are removed.
- The Canadian-history bar stays at ≥150. The user confirmed this on 2026-10-30: "yes, keep Canada at 150". Bothwell 139, Stacey 138, Strong-Boag 136 and Trigger 141 are not added.
- Under the ≥146 rule the list below was 13. The 136–145 band adds the names in *Band 136–145* at the end of this file.

## Candidates under the adopted rule

**Namesakes resolved by cited works.** The user said "the citations have the books/articles, so it shouldn't be hard". `namesake-resolution.json` assigns each cited work to its author by title, across every key variant. Counts are distinct dated strict theses citing any of that author's works.

| Key | Resolves to | Theses |
| --- | --- | --- |
| "Miller, James", "J.", "James R." and "Jim" | **J. R. Miller** (*Skyscrapers*, *Shingwauk's Vision*, *Compact, Contract, Covenant*, the anti-Catholicism and Equal Rights work) | **163** |
| | Other keys inside: James Miller (*Democracy is in the Streets*), Joseph C. Miller (*Way of Death*, his own key), John Miller (*Popery and Politics*) and others | |
| "Marshall, Peter" | **P. J. Marshall** (empire, India, Hastings) | 86 |
| | **Peter Marshall** (English Reformation) | 48 |
| | Peter Marshall (*Demanding the Impossible*, anarchism) | 13 |
| "Schlesinger, Arthur M" | **Jr.** | 106 |
| | **Sr.** (*Colonial Merchants*, *Rise of the City*) | 21 |
| "Thompson, John" | **John Herd Thompson** (*Decades of Discord*, *Harvests of War*, *Ambivalent Allies*) | 113 |
| "Thompson, Paul" | **Paul Thompson**, oral history (*The Voice of the Past* and its translations, *The Edwardians*) | 136 |
| | Other Paul Thompsons (labour process, Natal, Zulu rebellion) | 13 |

Callum Brown's works are filed under the garbled key "brown|katherine e". Every work under it is his, and the count is 166.

**Qualify. Canadian history, ≥150:**
- Nancy Christie, 161.
- J. R. Miller, 163. A settler scholar; the ≥150 rule applies to him and he clears it.

**Qualify. Other history, at least 146:**

| Historian | Theses | Note |
| --- | --- | --- |
| Keith Thomas | 197 | |
| J. H. Elliott | 168 | |
| Barbara Rosenwein | 167 | |
| John M. MacKenzie | 167 | |
| Callum Brown | 166 | |
| Joanna Bourke | 164 | |
| Jonathan Israel | 163 | |
| Stephen Greenblatt | 153 | Literary scholar; mixed-scholarship review |
| Geoffrey Parker | 151 | |

**Do not qualify after resolution:**
- P. J. Marshall, 86.
- Peter Marshall (Reformation), 48.
- Arthur Schlesinger Jr., 106.
- John Herd Thompson, 113.
- Paul Thompson, 136.

**Variant review (user, 2026-10-30: "yes, we need to do the review looking for name variations").**

1. **Grouping.** Keys cited by at least 3 dated theses were grouped by folded surname and first initial. Given names had to agree (Jim = James; full first names must match). An initial-only key joins every group with that initial.
2. **Screen.** 42 groups had an upper bound, the distinct theses citing any key in the group, at or above the bar, while no single key reached 150. They are in `variant-review-packet.json`, with the top works per key.
3. **Reading.** Each group's works were read. Most hold different people with the same name: the David, Robert and John Smiths; Christopher Clark of *Iron Kingdom* and Christopher Clark of *Roots of Rural Capitalism*; the three David Potters.
4. **Recount.** Where one person was split, the count is the person's main key plus the matching works under the variant keys.

| Person | Keys | Theses | Outcome |
| --- | --- | --- | --- |
| **T. M. Devine** | "Devine, Thomas M" + "Devine, Tom" | **147** | Qualifies |
| **Richard J. Evans** | "Evans, Richard J" + "Evans, Richard" (*Epidemics and Revolutions*, *The German Underworld*, the German *In Defence of History*) | **146** | Qualifies |
| W. E. B. Du Bois | "Du Bois" + "DuBois" | 211 | Already has an entry |
| Todorov | | 153 | Already has an entry |
| Agamben | | 147 | Already has an entry |
| F. J. Turner | | | Already has an entry |
| David Brion Davis | | 146 | Already has an entry |
| Gordon Wood | | 144 | Already has an entry |
| J. R. McNeill | | 144 | Below the bar; one work under the key is another John McNeill's |
| Daniel Richter | | 140 | Below the bar |
| David Arnold | | 141 | Below the bar |
| Christopher Hill | | 136 | Below the bar |
| R. C. Brown | | ≤133 | Below the bar |
| Robert Self | | 133 | Below the bar |

**Not covered.**
- Variants that differ in surname spelling ("Hobsbawn" for "Hobsbawm").
- Garbled given names. Callum Brown's works sit under "Brown, Katherine E" and were caught only by reading.

**Final list: 13 to add.**
- Canadian history: Christie 161, J. R. Miller 163.
- Other history:
  - Keith Thomas 197
  - Elliott 168
  - Rosenwein 167
  - MacKenzie 167
  - Callum Brown 166
  - Bourke 164
  - Israel 163
  - Greenblatt 153 (mixed scholarship)
  - Parker 151
  - Devine 147
  - Richard J. Evans 146

**Caveat.** Only these keys were resolved. A person whose citations are split across several key variants, as J. R. Miller's were, can sit below the bar on every single key. A systematic merge of variants by cited works would catch such cases.

**Just below the Canadian bar (130–149):** Bothwell 139, Stacey 138, Strong-Boag 136, R. C. Brown 133, Bradbury 132, Heron 131, Nelles 130.

**Unchanged:** the Indigenous-scholar exception (user, 2026-10-27).

**Not done here:**
- Theory and mixed-scholarship classification.
- Namesake resolution.
- Life review.

These follow the established queue procedure once the user settles the bar.

## Band 136–145 (bar revised to Paul Thompson's 136)

Every person in the band was checked for namesakes by their cited works. Name variants were merged after a second variant screen at 136, which included compound surnames split at the hyphen or space ("Walker Bynum", "Kessler-Harris").

**New candidates without an entry (other history, at least 136):**

| Historian | Theses | Note |
| --- | --- | --- |
| Caroline Walker Bynum | about 166 | With "Bynum, C" and "Walker Bynum, Caroline"; she would also have cleared 146 |
| Thomas Laqueur | 145 | |
| Charles S. Maier | 145 | |
| E. H. Carr | 143 | |
| Judith Walkowitz | 143 | |
| Paul Kennedy | 142 | |
| T. C. Smout | 141 | |
| David Arnold | 141 | |
| J. R. McNeill | 140 | Without the works of a namesake John McNeill (Presbyterian Church) |
| Sheila Fitzpatrick | 140 | |
| Patrick Geary | 140 | "Geary, Patrick J" + "Geary, Patrick" |
| Mike Davis | 138 | Writer and urban historian; mixed-scholarship review |
| Robert Bartlett | 137 | |
| Hugh Trevor-Roper | 136 | |
| Peter Gay | 136 | |
| Paul Thompson | 136 | |

**Bruce Trigger, 141.** *The Children of Aataentsic* and *Natives and Newcomers* are Canadian history, so the ≥150 bar applies unless he is classed as anthropology or archaeology. Flagged for the user.

**Already have entries:** François Furet 136, Michael B. Katz 140, Adele Perry 136, Christopher Hill 136 (135 + 1 variant), Daniel K. Richter 140.

**Below 136 after resolution:**
- A. H. M. Jones, 130. The key "Jones, Arnold H" also holds UAW, Baptist mission and Greenland-trade works.
- Kathleen Wilson, 135.
- Mary P. Ryan, 135.
- Charles Rosenberg, 127.
- Alice Kessler-Harris, 119.

**Excluded as primary-source authors:** Lenin, Hume, Hobbes.

**Canadian history between 136 and 149 (bar ≥150):** Bothwell 139, Stacey 138, Strong-Boag 136, Trigger 141 (see above).

**Editorial additions below the bar (user, 2026-10-30):** "Kathleen Wilson, Mary Ryan and Charles Rosenberg should be added; they give us two more women and a key sub field".

| Historian | Theses | Reason |
| --- | --- | --- |
| Kathleen Wilson | 135 | New imperial history and the British empire |
| Mary P. Ryan | 135 | Women's and gender history of the US middle class and public life |
| Charles E. Rosenberg | 127 | History of medicine; the key sub-field |

Each count is after namesakes are removed, including Ryan's "Ryan, Mary" variant and Rosenberg's "Rosenberg, Charles" variant.

**Final queue (2026-10-30):** 32 historians. That is 2 Canadian (Christie, J. R. Miller), 27 other by the bar, and 3 editorial additions (Kathleen Wilson, Mary P. Ryan, Charles E. Rosenberg).
