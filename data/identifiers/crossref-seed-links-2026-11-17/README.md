# Crossref seed test 2026-11-17: do thesis-author seeds have works in Crossref? (EVIDENCE ONLY)

The user's seed rule (2026-11-14): authors of theses taken from national registers are seeds; a seed gets a person key
only once it is linked to an article, book or book review. This folder tests how many seeds the Crossref public data
file (March 2026) can link. **No key-log proposal is written and nothing is applied; the user decides.**

Seed sets (`seeds-input.csv.gz`: seed id = thesis id, printed name, thesis title, year, university, GND):
- **DNB**: the 1,000 DNB thesis authors of `data/identifiers/thesis-round-2026-11-16/seeds.csv.gz`;
- **MX**: the 690 authors proposed as mints in `thesis-round-2026-11-16/03-author-mints-mexico.json` (684 Mexican + 6
  French-scope theses of the Mexico ingest); whether the seed rule applies to them is the user's open decision.

## Numbers first

| seed set | seeds | linked strong | linked weak | name only | nothing |
| --- | --- | --- | --- | --- | --- |
| DNB | 1,000 | **56** (5.6%) | 101 | 411 | 432 |
| MX | 690 | **34** (4.9%) | 188 | 271 | 197 |

Status is the best class among a seed's candidate works. Candidate rows (`seed-candidates.csv.gz`, 34,222 rows):

| evidence class (rows) | DNB | MX |
| --- | --- | --- |
| title_strong (thesis title ~ work title) | 49 | 31 |
| affil_thesis_univ (+topic) | 30 | 6 |
| orcid_of_linked (alone or with topic) | 2 | 24 |
| weak: topic only | 206 | 391 |
| weak: affil_weak (+topic) | 35 | 26 |
| name_only | 27,055 | 6,367 |

Seeds linked strong, by evidence (a seed can have several): DNB title 39, affiliation 18, ORCID of a linked work 2;
MX title 28, affiliation 6, ORCID 3. Strong works by type: DNB 34 journal articles, 34 books (monograph / edited-book /
book), 10 chapters; MX 35 articles, 18 books, 8 chapters. Most strong DNB links are the thesis published as a book.

## Hand check (`sample-checked.csv`, 60 rows, random draw seed 20261117)

- **Strong: 40 of 40 right** (25 by title: thesis-as-book or article on the thesis subject; 9 by affiliation; 6 by the
  ORCID of a linked work). One right link rests on topic, not the thesis: Sanchiz Ruiz's 2013 review of a book on the same subject.
- **Weak: 18 of 20 right, 2 wrong (90%)**: Susana Rodríguez (a bibliography of Spanish linguistic historiography;
  thesis on Mexican photojournalism; common name, nothing ties them) and Christian Richter (media-studies chapters at
  Potsdam; the seed is Enrico Christian Richter, thesis on German Zionism). Weak links are good leads, not links.

A first run had a looser rule; reading its strong rows found 8+ namesakes, so the rule was tightened before the check:
- *Cross-language stems*: Tao Zhang's 'Universitäten' matched 'universities' by a 7-letter prefix. A prefix match now
  counts with the idf of the commoner word.
- *Affiliation alone*: Thomas Schmidt (astrophysics, Potsdam), Joachim Graf (health sciences, Tübingen), Christian
  Richter (media studies, Potsdam), Marco A. Pérez (mathematics, UNAM), Manuel Suárez (urban studies, UNAM) matched the
  thesis university. The affiliation now counts as strong only with all of: full name led by the seed's first given
  name, full family name (not the first surname alone), a work in the history slice, at most one ORCID among the
  same-name Crossref authors, year thesis −3 to +6. Otherwise it is `affil_weak`.

## Rules

Candidate (scripts/crossref_seed_links.py, run on spark):
- family name equal after folding (umlaut → ae/oe/ue then ae/oe/ue → a/o/u, ß → ss, accents dropped, hyphens as
  spaces, particles von/van/de/de la/del… stripped); MX seeds with a double surname also match a Crossref family that is
  the first surname alone, and then the given name must match in full;
- given name compatible: every full Crossref given token is one of the seed's given names, initials agree, the first
  Crossref token is the first given initial or one of the seed's full given names; no nicknames ('Uli' ≠ Ulrich);
- work year in thesis year −3 … +30; contributor role author or editor;
- scope: the Crossref history slice (`/mnt/data/jic823/crossref-history-slice`, see
  `data/field-research/crossref-history-slice-2026-11-17/README.md`) plus every Crossref book, monograph,
  edited-book, reference-book and book-chapter.

Evidence: `title_strong` = thesis title and work title + subtitle share ≥2 rare words (fewer than ~2,000 of the 33.6M
slice + book titles carry them), ≥60% of the smaller side's idf mass, idf sum ≥14; `affil_thesis_univ` as above
(`inst-regex.csv`: university code → affiliation pattern); `orcid_of_linked` = the ORCID on a title- or
affiliation-linked work; `topic` (weak) = ≥1 rare shared title word, idf sum ≥8. An initial-only given name is linked
only by title or ORCID. Name only = none of these: not a link.

## What could not be used
- **ORCID of the seed**: no seed has one (DNB records carry GND, the Mexican records nothing), so ORCID is only usable
  once another fact links a work.
- **Later institutions**: none known for seeds; only the thesis university is tested.
- **Review of / reviewed with the thesis book**: Crossref review records name the reviewer as author; reviews of a
  seed's book are not looked for here (the seed is not the author). A review the seed wrote counts like any work.
- Life years: not known for seeds; the career window comes from the thesis year only.
- Works outside the slice that are not books (articles in non-history journals) are not searched, so seeds publishing
  in other fields stay unlinked.

## Base rate (`seed-summary.csv`: same_name_* columns)

Counts are Crossref author rows compatible with the seed's name (any compatible form, so 'Ana García' counts for
'García García, Ana María del Socorro': an upper bound on namesakes).
- DNB: 125 seeds have 2+ distinct ORCIDs among same-name authors, 99 have 100+ same-name rows, 208 have 5+ same-name
  works in the career window within scope. Worst: Li Jie (28,957 rows, 775 ORCIDs), Zhang Tao (25,727 / 650), Zhang
  Yang (23,858 / 729), Wu I-Wei, Li Zhi, Yang Xiao. Of the 136 seeds with a common name (2+ same-name ORCIDs or 100+ same-name rows), 9 are linked strong (all by
  title), 24 weak, 98 name only.
- MX: 280 seeds have 2+ ORCIDs among same-name authors, 179 have 100+ rows (Spanish given names and first surnames
  are common). Of 285 common-name seeds, 17 strong (16 by title, 1 by affiliation), 98 weak, 150 name only. Weak links for these seeds rest on topic
  words alone and carry the most risk (the Susana Rodríguez error above).

## Files
`seed-candidates.csv.gz` (every candidate: seed id, name, thesis title/year/university, DOI, Crossref name, work title,
subtitle, container, year, type, in_slice, link_class, evidence_class, evidence_detail), `seed-summary.csv` (per seed:
status, counts by class, strong evidence, base-rate columns), `stats.json`, `sample-checked.csv`, `inst-regex.csv`,
`seeds-input.csv.gz`. Scripts: `scripts/crossref_seed_links.py` (spark: `/mnt/data/jic823/tools/crossref-extract/seedtest/`).
