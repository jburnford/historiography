# Career merges: one person on several thin keys (2026-11-13; NOT applied)

Defect class 39 in ARCHITECTURE.md §8. Probe: Daniel Macfarlane, split over six keys (LC/Wikidata key, his Ottawa thesis
key, two review-credit keys minted per printed affiliation, two H-Net review keys). The owner ruled the six one person
(`../macfarlane-ruling-2026-11-13/`, applied, commit ef59374f) and asked for the general rule. The older merge rules
need a shared identifier, or the same name form plus the same institution; they never read the evidence a reader uses.
Review credits mint one key per printed affiliation, so anyone who reviewed from several institutions is split.

Built by `scripts/key_career_merges.py` on the post-apply build (key log seq 5,821,772).

## The rule (strict tier)
A thin key (review-credit or H-Net review only, harvested thesis only, AHA PhD only, repository-advisor token only, or
name only) merges into the anchored key of its name group, or, when the group has no anchored key, into its best thin
key (thesis, then AHA, then review), when all of these hold:
1. **Names**: same family name after folding (case, accents, punctuation, order, Mac/Mc spacing) and full given-name
   agreement (`propose_person_dup_merges.names_agree`): the first written-out given name identical, an extra middle name
   or initial allowed when compatible, conflicting initials and Jr/Sr block, a hyphenated given name is one name.
   No nicknames. Initials-only thin keys never qualify.
2. **Closed group**: every live key with a compatible name is in the group, except keys separated by hard evidence
   (different LC/Wikidata/ORCID/ISNI/IdRef, life years from life-years.csv.gz or the LC heading that rule out the thin
   key's activity, a `not-same:` mark, an outside 'different' verdict). Two anchored keys that could be the person, or
   an anchored initials-only key that fits, send the thin key to review. Name frequency: bearers = max(date-possible LC
   authorities not on the group + 1, OpenAlex History author ids), as in the works linker; **names with 26+ bearers are
   never strict**.
3. **One career**: a thesis year T bounds all dated reviews, articles, chapters and theses to T-9..T+50; nothing before
   birth + 20 or after death + 3; no span over 55 years; two keys each holding a thesis, or AHA PhD years more than two
   apart, never merge. The merge guard holds 9 merges (review tier).
4. **A tie beyond the name** between the thin key and the key it joins (or a key already strictly joined): a printed
   institution that appears on another key of the group (review-credit affiliation, thesis institution, AHA record,
   affiliations incl. LC 373 and ORCID); a network partner in common (REVIEWED, COAUTHORED, COEDITED, ADVISED, key-log
   evidence); topic: the pass-nine likelihood ratio of the thin key's titles under the other keys' titles, subject +
   subfield >= 6 (function words of German, French, Spanish and Italian removed); or a shared venue (journal or H-Net
   list) when the name has at most 5 bearers. Institutions differing never block; topic only ever supports.
   Ties grow only through strict ties (no chaining through a weakly tied key). Identity reads key-log rows only.

Review tier: the group is closed and the dates fit but the tie is below the bar (3,708), two or more anchored keys fit
(1,570), merge guard (9).

## Counts
- Thin keys whose full name block they share with another key: 26,788; judged 25,990.
- **Strict: 10,502 merges** (10,502 person keys removed if applied; dry-run validated: 10,502 events): 5,859 into an
  anchored key, 4,643 thin into thin (mostly H-Soz-u-Kult per-review keys); by band unique 3,016, 2-5 7,152, 6-25 334;
  by tie venue 6,048, topic 4,062, institution 217, network 175; by type review 10,033, AHA 347, thesis 93, name 18,
  advisor 11.
- Review tier: 5,287 (`review-tier.csv.gz`); no tie or career/clash failure: 7,058; group survivors 3,143.
- What it would change: 2,468 author-candidate positions (work, role) go from 2+ claimants to one; 4,222 lose at least
  one claimant (of 242,805). POSSIBLY_SAME pairs resolved: 2,586 of 6,426. Work-people duplicate groups
  (`work-people-2026-11-11/candidate-duplicates.csv.gz`, 4,903 with 2+ live keys): 1,915 fully and 183 partly resolved.

## Error measurement (`sample-checked.csv`, verdict and reason per row)
Judged from graph metadata (titles, years, venues, institutions, LC headings); no outside lookups were needed.
- First rule (any tie): 190 tied candidates, 10 per band x tie stratum: 18 wrong, 11 unclear. Wrong by band: unique
  0/60, 2-5 1/66, 6-25 5/58, 26+ 15/47; by tie: weak topic 12/40, venue 5/47, topic >= 6 2/70, institution 1/41,
  network 1/33. What misled it: weak topic words ('ireland', 'america', 'state'), dates printed only in the LC heading,
  a hyphenated given name, venue-only matches of common German names on H-Soz-u-Kult, chains through another thin key.
- Second draw, 41 rows of the tightened strict tier by stratum: 3 wrong, 1 unclear, all with 26+ bearers (a topic score
  from 'zum fur'; an undated H-Net review joined to a man who died in 1976; a Chicago thesis on 1905 joined to a
  biologist through an LC 373 string): 26+ left the strict tier, foreign function words left the topic score.
- **Final strict tier: 156 sampled rows, 0 wrong, 2 unclear** (an editorial-office signature 'TH Darmstadt Redaktion
  NPL'; a plausible Wittenberg/Restoration-England pair). 95% upper bound on the wrong share 1.9% (4.0% counting unclear
  as wrong). By band: unique 0/56 (upper 5.2%), 2-5 0/67 (4.4%), 6-25 0/33 (8.7%). Review-tier rows in the sample:
  16 wrong and 10 unclear of 91 (17.6%), which is why they are not proposed.
- Recall: on a copy of the graph taken before the owner's Macfarlane merge, all five Macfarlane thin keys are strict
  into p-143231 (thesis by the Ottawa institution and topic 17.2; Ottawa review by topic 9.0; Western Michigan key by a
  network partner and topic; the two H-Net keys by the H-Environment venue).

Caveats: the strict tier is dominated by H-Soz-u-Kult per-review keys of German names, so the sample is too; North
American and British review-credit merges are a smaller share. Editorial-office signatures are not people (count not
measured). Apply only after the owner's review:
`flock .keylog.lock python3 scripts/identifiers.py apply data/identifiers/career-merges-2026-11-13/proposal.json`.

Files: `proposal.json` (strict, not applied), `strict-tier.csv.gz` (the same rows with their ties), `review-tier.csv.gz`,
`sample-checked.csv`, `report.json` (counts, measurement, rule history, recall), `run-report.json` (raw run counts).
