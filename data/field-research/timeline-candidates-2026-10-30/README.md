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

**Recommendation.** Keep the Canadian bar at ≥150 and express the other bar as a share of the corpus. At the time, more than 100 of 6,794 was 1.47%. Today that is **more than 146** of 9,908, and it scales as further countries are added.

**Decision (user, 2026-10-30):** "1.47 seems like a good cut off for now". The Canadian-history bar stays at ≥150. Other historians must exceed 1.47% of dated strict theses, which is more than 146 in the 2026-10-30 build.

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

**Qualify. Other history, more than 146:**

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

**Caveat.** Only these keys were resolved. A person whose citations are split across several key variants, as J. R. Miller's were, can sit below the bar on every single key. A systematic merge of variants by cited works would catch such cases.

**Just below the Canadian bar (130–149):** Bothwell 139, Stacey 138, Strong-Boag 136, R. C. Brown 133, Bradbury 132, Heron 131, Nelles 130.

**Unchanged:** the Indigenous-scholar exception (user, 2026-10-27).

**Not done here:**
- Theory and mixed-scholarship classification.
- Namesake resolution.
- Life review.

These follow the established queue procedure once the user settles the bar.
