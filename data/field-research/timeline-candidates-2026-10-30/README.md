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

**Canadian history, ≥150 (unchanged bar):**
- Nancy Christie, 161.
- John Herd Thompson, 153.
- J. R. Miller, 170. This is the key "Miller, James", which mixes J. R. Miller with namesakes and must be resolved before counting. See `historiography-indigenous-priority-2026-10-27`.

**Other history, more than 146**, excluding primary-source authors (Smith, Locke, Burke, Rousseau) and corporate or anonymous keys. All need the usual identity and classification review:

| Key | Count | Note |
| --- | --- | --- |
| Keith Thomas | 197 | |
| Peter Marshall | 181 | Namesake check: the Reformation historian or P. J. Marshall of empire |
| J. H. Elliott | 168 | |
| Barbara Rosenwein | 167 | |
| John M. MacKenzie | 167 | |
| Callum Brown | 166 | 114 of the 166 are British theses |
| Joanna Bourke | 164 | |
| Jonathan Israel | 163 | |
| Arthur Schlesinger | 155 | Namesake check: Jr or Sr |
| Stephen Greenblatt | 153 | A literary scholar: mixed, separate review |
| Geoffrey Parker | 151 | |
| Paul Thompson | 147 | *The Voice of the Past*, oral history |

**Just below the Canadian bar (130–149):** Bothwell 139, Stacey 138, Strong-Boag 136, R. C. Brown 133, Bradbury 132, Heron 131, Nelles 130.

**Unchanged:** the Indigenous-scholar exception (user, 2026-10-27).

**Not done here:**
- Theory and mixed-scholarship classification.
- Namesake resolution.
- Life review.

These follow the established queue procedure once the user settles the bar.
