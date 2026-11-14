# Independent spot check of the 2026-11-14 LC-note links

A read-only check of three rule-made link sets from 2026-11-14 (ARCHITECTURE.md section 8, classes 40-41). Nothing in
the key log, scripts or graph was changed. Verdicts were reached first. The builder's samples
(`lc-authority-notes-2026-11-14/sample-checked.csv`, `note-review-books-2026-11-14/*-sample-checked.csv`) were read
only afterwards, to compare.

Files: `checked-authorities.csv` (set 1), `checked-note-books.csv` (set 2), `checked-review-ties.csv` (set 3). Each row
holds the key, the link, a verdict, a one-line reason, the source used and a URL where a web page or ORCID record was
read.

## Method

- **Seed 20261114** (`pandas.DataFrame.sample(random_state=20261114)` on each stratum or file).
- **Set 1** (4,050 strict ties in `ties.csv.gz`, decision `strict`): 110 rows, 55 `same` and 55 `thesis-book`. Each
  tie type was split by name band: unique 13, 2-5 15, 6-25 14, 26+ 13. That over-weights the common-name bands: 26+
  has only 44 strict rows in all, and 26 of them are sampled. 49 of the 110 rows carry a common surname (1,500 or more
  LC personal authorities with that family name, such as Smith, Davis, Wilson, Taylor, Chen, Zhang or Li).
  - Each row was judged from LC's heading, dates, every 670 and the affiliations
    (`/mnt/e/lc-authorities/personal-*.parquet`), set against the key's label, anchors, credited works, thesis
    (including the AHA record's department and year) and affiliations in a read-only copy of
    `build/graph/explorer.duckdb` (built 09:11).
  - **Outside sources:** for the 51 sampled keys with an ORCID anchor, the public ORCID record (pub.orcid.org) was
    read: name, employment, education and works. 48 of them carry enough data to confirm the LC note's affiliation or
    book. For 11 AHA/thesis rows, publisher, faculty or library pages were found by web search. In all, 59 of the 110
    rows were confirmed outside LC and the graph.
- **Set 2** (1,353 `lcnote:` books in `data/graph/lc-note-books.csv.gz`): 60 rows. For each row:
  - the person's credited, edited and contributed works within 3 years were listed;
  - the graph was searched for other nodes with the same title prefix;
  - 26 rows were searched on the web (publisher, catalogue and faculty pages), and 22 of those found a confirming
    page.
- **Set 3** (1,788 ties in `data/graph/review-titled-books.csv.gz`): 60 rows. Each review node's label, journal and
  year was read against the tied book node, its credited authors and editors, and the person's other works. Two
  rows were confirmed on the web.
- 95% upper bounds are one-sided Clopper-Pearson. No shadow-library or user-upload site was used. No service refused
  a request. No contact details were sent: ORCID was queried with a generic client name.

## Results

| Set | n | right | wrong | duplicate | unclear | 95% upper bound on wrong |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 LC authority attachments | 110 | 110 | 0 | n/a | 0 | 2.7% (0/110) |
| 2 note books | 60 | 25 | 3 | 28 (25 certain, 3 probable) | 4 | wrong only 12.4% (3/60); wrong or duplicate 62.9% (31/60, point 52%) |
| 3 review title ties | 60 | 58 | 2 | n/a | 0 | 10.1% (2/60) |

### Set 1 by stratum

| tie / band | unique | 2-5 | 6-25 | 26+ | all |
| --- | ---: | ---: | ---: | ---: | ---: |
| same | 13/13 | 15/15 | 14/14 | 13/13 | 55/55 right (upper 5.3%) |
| thesis-book | 13/13 | 15/15 | 14/14 | 13/13 | 55/55 right (upper 5.3%) |

- All 49 common-surname rows are right. 28 of the 55 `thesis-book` rows are NUC or UMI reports of the key's own
  dissertation, so the "book" is the thesis itself, which makes them the easiest rows to judge. The 27 true
  thesis-to-book rows are all right; their topics, dates and printed bios agree (Deacon-type cases such as Shiner,
  Manko, Harper, Pavlides, Kazanjian, Black and Mason).
- None of the failure kinds asked about turned up: no namesake in the same field, no father and son or Jr and Sr, no
  coincidental rare words, no impossible birth year, and no note citing the person only as a subject.

**Related problems (not caused by this rule).** About 12 of the 110 keys are conflated. Their ORCID-route works
include namesakes:

- Martin Davis: 1950s logic reviews and a golf book;
- Ulrike Müller, David Baker, David Holland, James Davis and Ju Li;
- Thomas Morel and Ivan Simic: engineering theses;
- Luis Carlos dos Passos Martins: a medical thesis;
- Benjamin J. Richardson: genetics.

In every one, the ORCID owner is the LC person, so the attachment is right. The key's work list is not.

Two LC records also look internally mixed:

- Steinbach n2003003134 adds a 2001 Germanistik title;
- Ross n86802425 adds a supply-chain book (possibly the same man's later career).

### Set 2: wrong and doubtful rows

**Wrong (3):**

- **Tyson p-215405**, *One princess, two castles* (2021): a children's book by an elementary-school teacher who
  shares her name. The key's own `lcnaf:no2022030202` anchor is the root error; the builder's README already flags it.
- **Yamanaka p-79949**, *A college town in black and white* (2023): an article in the North Carolina Historical
  Review (100.1). The 670 reads `caption (...) page 28`, which marks an article, not a book.
- **Ott p-62768**, *Victorian illness revisited ... IN PACSCLnews* (1992): a newsletter article. The `IN <serial>`
  marker was not caught.

**Duplicates (28).** The book is already in the graph, almost always credited to the same key, under its full or
final title. What let them through:

- a CIP or working title that differs from the published one: Peace River Valley/Frontier, Politics of school
  reform/Power and the promise, Vanderbilt Medical Center/Making medical doctors, ERA and the politics of
  gender/Sex, gender, and the politics of ERA;
- probable working titles (counted as duplicates): Benin's *And the Lord came down*, Ballard's *From a mighty long
  way* and Walkowitz's *Sex and class in Victorian England*;
- the main title only, or the subtitle only: David Joris, The Stanleys, The United States Naval Institute, The
  movement for family allowances, Matilda of Scotland, Tropical surge, The virgin vote, Lady Rachel Russell;
- LC abbreviations and typos: "encyc", "N.Y.C", "Ren.", "Ubootbunker u.", "undergrouth", "Parlour", "Missionaires",
  "Economic change in rural resistance";
- the same title already held: Renaissance Florence, Tefillin;
- a translation or another romanisation of a held book: Malia in Russian, Jensen's Chinese edition.

The README says notes are skipped when their main title agrees with a credited work or a graph book within two years.
In this sample that test missed every variant except exact equality.

**Unclear (4):**

- Selinger, *Renaissance/Reformation bibliography* (c1979);
- Meschievitz, *Panchayat justice* (1987, cover only; probably a working paper);
- Schmidt, *The Sullivan principles* (c1979; may be an early form of the credited 1980 *Decoding corporate
  camouflage*);
- Kyte, *The blockade of Gloucester in 1781* (1956; probably an offprint).

**Role.** One right row is an edited volume, not an authored one: Stoker, *Military advising and assistance*,
Routledge 2008. Co-authorships (Allison with Wadman, Kellar with Patel, Gandy with Stanlis) are right as AUTHORED.

**Size of the duplicate problem across all 1,353 rows** (rough measures, not checks):

- A crude scan (the note's first three title words equal a credited book or "other" work within 3 years) flags
  419 rows.
- A wider flag, "the key already has a credited book dated from 2 years before to 1 year after the note year", flags
  788 rows. In this sample that flag catches 24 of the 28 duplicates. It also flags 5 rows that are not duplicates: 4 right
  and 1 unclear.
- The duplicate share across all rows is likely 40-55%.

### Set 3: wrong rows

- **doi:10.53458/zwlg.v77i.1744 to w-932680 (Cottier).** The review is of the 2017 UVK book *Fatale Gewalt. Ehre,
  Subjekt und Kriminalität am Übergang zur Moderne*. That book is already a node: w-762827, mistyped as an article.
  The tie went to a different 2015 Cottier item with the same short title. This is the "different book with the same
  short title" kind: the short-title match picked the wrong item among the person's works.
- **w-907178 to w-28428 (Le Zotte).** The AHR review is of the 2017 UNC Press book. The tie went to her 2013
  dissertation of the same main title, because the graph has no node for the book. The rule allows thesis targets;
  it should not when the review names a publisher or year after the thesis, or a different subtitle.

Drossbach (w-1896491, typed thesis) is right: the node is the published Habilitation the review names.

One right pair (doi:10.15581/001.15.1753 to lccn:2012455152) has no REVIEWS edge in the 09:11 explorer build. This is
worth a look at build time.

## Comparison with the builder's samples

- **Set 1:** 22 of my 110 rows are in the builder's 130, mostly in the 26+ band. We agree on all 22: right.
- **Set 2:** 5 rows overlap. We agree on 2 (Jaehn, Samper). We disagree on 3, which the builder marked right and I
  mark duplicate: ERA and the politics of gender, The politics of school reform, The intelligent traveler's guide.
  - The builder's note says "no graph book of the title for the person": the check compared the exact title only.
  - Applying my wider flag to the builder's 60 rows flags 30 of their 57 "right" rows, including many abbreviated
    LC titles ("Oil diplomacy in the 20th cent", "Native sources of Japanese industrial., 1750-1920", "Ideal gov't
    and the mixed constitution"). So their 57/60 overstates set 2.
- **Set 3:** 2 rows overlap. We agree on both: right. My two wrong cases are outside their sample.

## Recommendation

1. **Set 1: keep as is.** 0/110 wrong, with the sample weighted toward the hard tie and common names; the 95% upper
   bound is 2.7%. The key conflations seen alongside are an older ORCID-route problem worth its own pass.
2. **Set 2: withdraw or hold the 788 rows the wider flag catches.** Then rerun the absence test on fuller title
   evidence:
   - normalise LC abbreviations and spellings;
   - compare the note title as a prefix of, or contained in, every work credited to the person within -2 to +2
     years;
   - treat any credited book in the same year as a probable CIP variant unless the titles share no words;
   - drop translations of a held work.

   Also drop notes carrying `IN <serial>`, `caption` or `page N` article markers. Correct Stoker's credit to EDITED.
   Remove Tyson's `lcnaf:no2022030202` anchor and its book. The 565 unflagged rows still need the fuller test. In this
   sample, the 31 unflagged rows were:
   - 21 right;
   - 3 wrong (all article or namesake cases, which the markers and the Tyson fix address);
   - 3 unclear;
   - 4 duplicates the flag missed:
     - a graph node not credited to the key (Lincoln encyc.);
     - a translation (Malia);
     - a working title published 2 years later (Benin);
     - a CIP title published 2 years later (Crowl).

   Widen the year window to +2 and also match uncredited graph books.
3. **Set 3: keep, with two fixes.**
   - Withdraw the two wrong ties: Cottier w-932680 and Le Zotte w-28428.
   - Tighten the rule: when the person has several works sharing the review's short title, prefer the one whose
     subtitle or year agrees with the label, or hold the tie.
   - Do not tie to a thesis node when the review is more than about 2 years after the thesis, or the label prints a
     subtitle the thesis lacks.

## Not verified

- Set 1 rows that rely only on LC and the graph: 51 of 110, mostly NUC thesis reports, which are self-evident.
  Rydberg and Prada have ORCID records with no data.
- The web did not confirm the PhD institution for Howell or Reidy; dates and topics agree.
- Set 2: Pitsula's 1982 book was not found online. The 4 unclear rows remain unresolved. "Probable" duplicates
  (Benin, Ballard, Walkowitz) rest on CIP and timing evidence, not on a catalogue statement.
- Set 3: 58 rows were judged from the review labels and graph nodes; only the two wrong ones were checked on the web.
