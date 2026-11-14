# Co-authors printed on keyed works who are missing from the graph (2026-11-14)

ARCHITECTURE.md section 8, class 43. Script: `scripts/coauthor_gaps.py` (`crossref-index`, `measure`, `sample-fetch`,
`fetch`, `propose`). **A proposal: not applied.** The dry run against the key log (seq 5,837,623) passes with 18,909 events.

## Probes

- **w-549919** 'Thinking through forests' (Journal of Historical Geography 2026). Crossref prints Jim Clifford and Iva
  Lučić. The 11-11 co-author mints held her, with two works (this one and w-1480407 'The Coniferocene', JHG 2026, nine
  authors). Then `scripts/narrow_coauthor_mints.py` vetoed her w-549919 mention through `KNOWN_ERRORS`: "the author is
  Iva Peša, p-6823". That veto was a mistake. Peša is a different person and is not on the paper. With one work left
  and only an OpenAlex-inferred ORCID, she was dropped.
  - Changed 2026-11-14: `KNOWN_ERRORS` is now empty, and its docstring and comment record why.
  - The same veto is also written in the 2026-11-11 handoff memory note. That note is not edited here.
  - Her ORCID (0000-0003-0835-5896) is inferred by OpenAlex on both records. It is not printed: Crossref prints none for
    her. Her public ORCID record (Iva Lucic, Uppsala, *Law of the Forest*, Bosnia-Herzegovina) agrees in name and field.
  - In this proposal she rests on rule G: two works with her full name, joined by the same venue, the same OpenAlex
    author id and the same institution ROR. That makes the inferred ORCID her anchor.
- **w-703278** 'Logging and Settlement beyond the Rapids' (Canadian Historical Review 2025). Crossref and OpenAlex print
  Jim Clifford and Sam Huckerby (University of Saskatchewan, no ORCID). The author list *was* loaded: an OpenAlex
  position, linker state `none` (no key bears the name). The Crossref record is also held on E:
  (`crossref-meta-2026-11-11`, CHR file). It was not missed by a date cut-off.
  - The 11-11 mints proposed him (`new:p58777`, one work). The narrowing dropped every one-work, name-only person.
  - `work-people-2026-11-11/unkeyed-people.csv.gz` lists only names with 2+ works or a JSTOR-printed institution. It
    ignores the OpenAlex ROR list, so he appears in no file.
  - In this proposal he is minted under rule H, as a one-work key.

## Class counts (`report.json` -> `measure`; build of 2026-11-14 afternoon, link results of 2026-11-14 00:09)

**Population.** 1,122,753 key-log works carry a DOI:

- 740,061 have printed author positions;
- 302,315 are reviews whose reviewer is loaded instead (not a gap);
- 47,349 are review records that print no reviewer (not counted).

On 126,286 works, more names are printed than the graph credits plus candidates.

**(a) No author list loaded.**

- 6,739 works have a Crossref record on E: that was never loaded; on 937 of them it prints more people than the graph
  credits.
- 26,289 works have no record anywhere on disk (13,639 of them JSTOR `10.2307` DOIs; articles 22,559, books 3,164,
  theses 566).
- Sample fetch, 300 DOIs (seed 20261114; one client, generic User-Agent, 0.5 s apart, 222 s, no throttling):
  - 209 returned 404, including 146 JSTOR DOIs (these are not Crossref DOIs);
  - 91 were found: 38 with no authors, 27 with one, 26 with two or more;
  - 20 print more people than the graph holds.
- Estimate: about 1,750 works (95% CI about 1,080-2,660), many of them preprints and SSRN/OSF records outside history.

**(b) A printed co-author with no key, not minted** (125,762 works). The 11-11 mint record explains the positions in
`b_positions_by_reason`:

- 245,370 were never in the 11-11 mints (no historian on the work);
- 17,237 were minted, then dropped by the one-work rule;
- 11,047 were dropped as an inferred ORCID on a single work;
- held as more than 25 authors 3,633, unmatched key-log author 2,364, unparsed 1,156, organisation 737, initials 681,
  twin 537.

**(c) A key exists but the position was dropped:** 77 positions (76 with candidates and no candidate edge, 1 linked).
Negligible.

**Bulk fetch for (a): not run.** Command (resumable, stops on 429):

    flock build/.heavy.lock python3 scripts/coauthor_gaps.py fetch

It covers 26,289 DOIs, takes about 8 hours, and about 70% will 404. The fetched records must then be loaded as positions
(like `positions-crossref.parquet`) before any mint can see them.

## Mint rule

**Current rule** (`narrow_coauthor_mints.py`, 11-11): co-authors of a historian key (person-roles historian,
strong/supported) only, with either a printed ORCID or two or more works joined by the same OpenAlex author id, historian
co-author or institution ROR.

**This proposal** (owner framing 2026-11-14). A mint needs:

- a printed full name: a written-out given name, never initials only, not an organisation;
- linker state `none`;
- a work with a keyed author;
- and one of these rules:
  - **O**: an ORCID printed on the record (OpenAlex `raw_orcid` or the Crossref author ORCID);
  - **G**: two or more works with the same full name, joined by a shared keyed co-author, the same venue, the same
    OpenAlex author id, the same ROR or the same inferred ORCID;
  - **H**: one work in a history venue (journal catalogue) with a keyed co-author.

**One-work mints stay one-work keys.** Their anchor is `coauthor-mention:<work>:<pos>`. An inferred ORCID becomes an
anchor only under G, with the name in full on every mention, and only if no other mint prints that ORCID. Otherwise it
is a member `orcid-inferred:`.

**Never minted from** (works skipped):

| Skipped records | Works |
| --- | ---: |
| Review records | 43,015 |
| Journal records titled with a graph book's title (reviews whose book authors OpenAlex prints as authors) | 17,397 |
| Records of three pages or fewer | 56,670 |
| Review or notes section records ('Reviews', 'Short notices', 'Books: ...', 'Title / Author') | 3,905 |
| Pre-1990 records with 5+ names | 1,956 |

**Held** (`held.csv.gz`, with reasons):

| Held mentions or people | Count |
| --- | ---: |
| A compatible key exists (a link question) | 23,869 |
| Key-log author matches no printed name | 6,379 |
| Over 25 authors, no ORCID | 3,660 |
| Unparsed | 2,551 |
| Initials only | 2,424 |
| Organisation | 1,210 |
| The printed name is in the title (the subject) | 1,148 |
| A live key with the same full name (possible name-form link) | 965 |
| ORCID already on a key | 159 |
| Two printed ORCIDs in one group | 4 |

Not covered: 30,695 one-work people outside history venues with no ORCID (co-authors of historian keys).

**Proposal size: 8,685 people, 10,224 authorship claims.**

- By rule: H 6,601, OH 930, GH 609, OGH 232, G 200, O 83, OG 30.
- By works: 1 work 7,614; 2 works 843; 3 works 144; 4 works 44; 5+ works 40.
- The 11-11 rule would keep 2,049 of them. The loosening adds 6,636 (H 6,601, GH 22, G 13).
- 44 have a key whose given name agrees only at variant level (Sam/Samuel). These are listed, never merged.

## Hand check (`sample-checked.csv`)

The 60 lowest hashes of label and works, plus the two probes: **56 right, 2 wrong, 2 unclear** (95% upper bound on
wrong: 10.2%).

- Wrong:
  - Chris Lıghtfoot: a dotless ı defeats the name fold. This should be a link to p-97899 Chris S. Lightfoot.
  - 'Hutton Da': a garbled printed name.
- Unclear:
  - Felipe Pereda: contributors of a volume, listed as authors.
  - 'Angela Zimmerman' on an AHR forum: possibly Andrew Zimmerman, p-4063.
- Both probes are right and distinct from every key.

The first pass, before the section, subject and pre-1990 guards, found 6 wrong of 60: five review or notes section
records (Italian Studies 1970, Social Forces 1926, Acta Poloniae Historica 1982, 'Reviews', 'Short notices') and one
subject printed as an author ('John Seldon'). Those guards were added then.

Open:

- fold `ı` (and other non-decomposing letters) in the name forms;
- a page-count source for records outside the Crossref harvest;
- Vancouver-style names ('Hutton DA').
