# Anderson book and author identity audit

Checked **25 October 2026**, against the unchanged **23 October 2026 frozen release**.

Yes: **685 of the 716 dated dissertations under the frozen first-author key (95.67%) cite a positively identified title-family record for *Imagined Communities*.** The narrower main work key accounts for **641/716 (89.53%)**. Fifteen separately stored translations or complete-title variants add **44 distinct dissertations**, after deduplication. The main key already coalesces editions; its recorded year 1991 does not make all of its citations citations to that edition.

These figures describe bibliography presence. They do not establish a full reading, endorsement or intellectual influence. Positively identified book-family records include raw article-labelled variants; the corpus does not resolve whole-book use versus excerpt or component use. Incomplete fragments are excluded from the confirmed union.

| Region | Dated sample | Frozen Anderson P | Main book key | Confirmed book union | Main/P | Book union/P | Book union/sample |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Global | 6,794 | 716 | 641 | 685 | 89.53% | 95.67% | 10.08% |
| Canada | 2,212 | 292 | 266 | 280 | 91.10% | 95.89% | 12.66% |
| United States | 2,168 | 262 | 249 | 251 | 95.04% | 95.80% | 11.58% |
| Europe | 2,025 | 129 | 98 | 121 | 75.97% | 93.80% | 5.98% |
| Other | 389 | 33 | 28 | 33 | 84.85% | 100.00% | 8.48% |

Europe uses the site's exact country mapping, including the UK and Switzerland; this is not an EU membership classification. Each count is a union of dissertation IDs with `in_analysis == True` and a four-digit dissertation year. Source geography and sample composition limit regional comparison.

## All 57 work records reviewed

| Decision | Work keys | Rule |
| --- | ---: | --- |
| Confirmed *Imagined Communities* family | 16 | Complete distinctive main title, or explicit translation witness; matched author; minor OCR, punctuation and singular/plural variants allowed |
| Other confirmed Benedict Anderson work | 28 | Positive author/title match in institutional bibliography, original publication or publisher contents |
| Ambiguous, held | 11 | Subtitle fragments, imprints, generic titles, unmatched title or incompatible apparent date without an identified alternative author |
| Confirmed other author | 2 | Positive alternative-author metadata |

[decisions.json](decisions.json) preserves every original work row, its exact ID and count fields, and records the decision, rationale, witnesses, locators and limits. [sources.json](sources.json) records exact URLs, what was checked and access limits. Publication metadata is used only for title/author identity; this audit makes no substantive argument or influence claims.

The confirmed translations are French, Swedish, Italian, German, Dutch, Portuguese and Spanish. French BnF and Swedish/Italian/German library records explicitly identify the original or uniform title. Dutch mapping uses matched WorldCat metadata plus Louis Vos's original comparative discussion identifying Paul Syrier's translation with *Imagined Communities*. Portuguese mapping uses matched WorldCat metadata plus the original Ática copyright/title page, reproduced on a third-party host, explicitly naming the English original. Current publisher pages identify the title family; they do not independently establish the particular edition cited in each dissertation.

Two confirmed contaminations remain in the frozen denominator:

- *A crise da crise do marxismo*: CLAEH's library record credits **Perry Anderson**.
- *Report on the Trade of the Chiengmai District for the Year 1894* (published 1895): Heidelberg's institutional bibliography credits **W. J. Archer**.

*The New World Disorder* is **Benedict Anderson's** 1992 *New Left Review* article: it is not assigned to Perry. *Violence and the State in Suharto's Indonesia* retains Anderson's editor credit; the *Preliminary Analysis* retains Ruth McVey's coauthorship and Frederick Bunnell's assistance. A Thai-studies title with an incompatible frozen 1966 date has a positive Benedict title match in the Cornell bibliography and Chula library; the frozen date is preserved and qualified.

Held titles include *Reflections on the Origin and Spread of Nationalism* without its main title, *of Nationalism*, *Democracy*, imprint-only records, *L'Imaginaire Social*, and the lone word *Imagined*. The Ukrainian title dated 1872 is suspicious and incompatible with Benedict Anderson's 1936 birth year, but the alternative author has not been established; it remains held rather than being assigned. Plausible book fragments are not counted as confirmed translations.

The union of all positively identified Benedict works reaches **707** of the frozen 716. Of the remaining nine, the only available keys are held or confirmed foreign-author records. This is an identity-review observation, **not a corrected P denominator**. The 28 other-Benedict work keys reach 52 dissertations, overlapping the book union in 30; **22** cite a confirmed other Benedict work without a confirmed book-family record. The other **nine** account for the difference between 707 and the frozen 716.

## Reproduction and preservation

Run from any directory:

```sh
python data/field-research/historian-classification-amendment-2026-10-25/anderson-book-identity/audit.py
```

[audit.py](audit.py) verifies six frozen input hashes against the release `SHA256SUMS`, checks exact preservation and coverage of all 57 original rows, validates their strict/all-record citation counts, and joins citation IDs to the dated dissertation population. It verifies the input hashes again after counting. It writes only [counts.json](counts.json) and [citation-unions.json](citation-unions.json) in this audit directory. The latter includes all 57 per-work citation sets and the exact 44 additional book-family dissertation IDs.

Adding the 16 book-key counts would give 686; their dissertation union is **685**, because one dissertation cites multiple records. Neither work counts nor regional denominators are inferred from author-row totals.

The raw main-key strict count **647** includes six undated dissertations; its all-record count is **658**. The frozen author row is **726** strict and **737** all-record, while the dated first-author union is **716**. One additional second-author row (`W:soerjono|on mussos return|a`) is outside the requested first-author scope. These scopes remain distinct. No IDs, raw numbers, release CSVs, graph data, UI data or existing exports were changed. No OpenAlex request was made. Downloaded PDF/text bodies remain ignored under `raw/`.
