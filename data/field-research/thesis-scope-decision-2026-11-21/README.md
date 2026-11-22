# Thesis scope: what the outside reviewer found, and what needs a ruling (2026-11-21)

Sol (Codex) read the public record of every doctoral thesis held out of the History corpus: 3,232 theses
(data/identifiers/sol-review-2026-11-19/7-thesis-scope-holds/, latest verdict per thesis). This folder is the
audit, the releases made under existing rulings, and a one-read decision sheet for the classes the user has
not yet ruled on. Titles and departments only; no abstracts. Made by `scripts/thesis_scope_sol_review.py`.

## What you need to decide

Four classes are held, waiting for a ruling. The counts below are theses. A "History unit" is a doctorate whose
department is a History department or chair, such as Alte Geschichte, Histoire or Ancient History.

| Class | Theses | In a History unit | Theology or religious studies | Other unit | Not established |
| --- | ---: | ---: | ---: | ---: | ---: |
| Church history / history of religions | 474 | 231 | 132 | 72 | 39 |
| Philology / text edition | 374 | 80 | 9 | 243 | 42 |
| Art history | 112 | 10 | 1 | 96 | 5 |
| Philosophy / philosophy of science | 43 | 1 | 2 | 40 | 0 |
| Other-subject doctorate carrying a History code (Sweden) | 16 | 0 | 0 | 16 | 0 |

The breakdown by source is below. "Canada" means the Toronto IHPST and UVic holds.

| Class | DNB | theses.fr | SwePub | Canada | Edinburgh | Oxford |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Church history / history of religions | 347 | 119 | 4 | 1 | 3 | 0 |
| Philology / text edition | 234 | 115 | 6 | 5 | 13 | 1 |
| Art history | 93 | 7 | 5 | 7 | 0 | 0 |
| Philosophy / philosophy of science | 8 | 2 | 0 | 33 | 0 | 0 |
| Other subject with a History code | 0 | 0 | 16 | 0 | 0 | 0 |

The two splits most likely to settle these classes in one ruling each:

1. **Church history / history of religions: do theses in a History unit count?** There are 231. Examples are
   cults in Lycaonia (TU Chemnitz, History), the secularisation of the Duchy of Berg (Düsseldorf, History) and
   American churches and the Second World War (FU Berlin, North American History). Sol read 72 of them as History
   outright. The 132 theology or religious-studies doctorates are the clear "no" side. Examples are New Testament
   exegesis, patristics and the EPHE *Histoire des religions et anthropologie religieuse*.
2. **Philology / text edition: do historical commentaries in a History unit count?** There are 80. An example is
   the Claudius Lyon tablet commentary in Münster's Seminar für Alte Geschichte. The other 294 are classical,
   Sanskrit and Egyptological philology, editions and literary studies.

The other three classes are one-line rulings:

- **Art history** (112): 96 are in art-history or architecture units.
- **Philosophy of science** (43): 33 are Toronto IHPST theses that read as philosophy (realism, modelling,
  epistemology). Three IHPST theses use historical case studies. These are held here and not released.
- **Swedish other-subject doctorates with a History code** (16): sociology, library science, working-life
  studies and the like.

Fifteen representative titles per class, with their departments, are in `unruled-class-examples.csv`. The source
spread follows each source's share of the class.

### Sol's borderline notes, summarised

Sol marked 906 of the 1,019 theses in these classes as borderline. The recurring reasons:

- **Church and religion.** The doctorate is in Ancient or Medieval History and cult or church is the lens on
  politics or society. Or the work appears in a church-history or New Testament series. Or archaeological
  evidence is substantial.
- **Philology.** The supervisor or chair is Ancient History, or the commentary serves a historical argument
  (dating, kingship, identity).
- **Art history.** Patronage and social history are part of the work. Or religion or liturgy shapes the reading.
  Or the objects double as archaeological evidence.
- **Philosophy.** The argument follows a historical sequence. Examples are behaviourism to cybernetics and the
  Polanyi–Bernal dispute. Or an intellectual-history method is stated.

## Released under existing rulings

There were 244 candidates: Sol read the thesis as History and the hold as wrong. Of these, **80 are released**
by a narrower rule:

- Sol's confidence is high.
- The original hold ground is not an unruled class (church history, history of religions, philosophy of science).
- Sol's department names a History unit.
- The department is not History didactics, art history or philosophy.

The provenance on each override is "Sol read 2026-11-19/21, audited".

| Source | Released | Override file (form the pipeline reads) | PDF status |
| --- | ---: | --- | --- |
| DNB | 59 | `dnb-germany-harvest-2026-11-14/screen-overrides-2026-11-21.csv` (dnb_id, decision, note) | 32 have a free DNB link and 27 have none. Whether a PDF is on disk is unknown: the manifest is on E:, which is not mounted. |
| theses.fr | 19 | `france-theses-resurvey-2026-11-15/scope-overrides-2026-11-21.csv` (nnt, decision, note). New hook in `register_france_resurvey.py`. | None downloaded. They were outside the download lists. |
| SwePub | 2 | `diva-sweden-pilot-2026-11-14/scope-overrides-2026-11-21.csv` (record_id, decision, note). New hook in `register_sweden_theses.py`. | None downloaded. |

By ruling, the 80 releases are:

| Ruling | Theses |
| --- | ---: |
| Ancient history | 35 |
| History PhD in a History unit | 28 |
| Economic history | 8 |
| History of science | 7 |
| History of education | 2 |

Only DNB rows with a downloaded PDF can enter at the next ingest, and that count is at most 59. The French and
Swedish releases need a download first, then a register run. Nothing was ingested or rebuilt here.

The other 164 Sol read as History stay held (`held-history-reads.csv`):

| Reason held | Theses |
| --- | ---: |
| Original ground is church history, history of religions or philosophy of science | 74 |
| Sol's confidence is medium | 75 |
| Department is not a named History unit (mostly economics doctorates and Egyptology) | 13 |
| History didactics | 1 |
| Philosophy department | 1 |

The 13 economics and Egyptology theses could be released under the economic-history ruling and the
historical-Egyptology reading after a second look.

## Audit (`audit.csv`)

**A. Random 40 of the 244 candidates:**

- 25 are History and releasable now.
- 12 are History, but in an unruled class (church history or religion grounds, and philosophy of science at IHPST).
- 3 are wrong: a History-didactics thesis, a development-economics thesis and a philosophy-of-science thesis.

The whole candidate set fails the 95% bar, so it was not released as a block.

**B. The release rule:** 40 audited candidates pass it (16 from sample A plus 24 more drawn from the rule's
set). 39 of the 40 are right. The miss was a Heidelberg Philosophisches Seminar thesis. The rule now excludes
philosophy departments, and all 39 that pass the final rule are right.

**C. Random 40 confirmed holds, stratified by class:**

- 39 of the 40 holds are right.
- The one doubt is *La représentation des riches et des pauvres en Grèce* (Grenoble, Histoire ancienne). Sol read
  it as unclear, and it is likely History. It stays held.

## Notes

- Ten Canadian History-scope cases carry file-verification holds (fragments, incomplete PDFs). Those are not scope
  questions.
- *The Trilateral Commission* (SwePub, released) is a Copenhagen doctorate in contemporary history. Its country
  should be DK, not SE.
- The DNB manifest on E: could not be read: E: is not mounted. Sol could not read it either.
