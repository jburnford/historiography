# Evidence layer: using the review and article record to push past the standard narrative

2026-09-26. A companion to [IDENTITY-PLAN.md](IDENTITY-PLAN.md). The identity work makes
people traceable across corpora; this plan uses that record to put *practice* beside the
atlas's *interpretation*.

## Why: what the data shows

- **The canon and the record barely overlap.** Of 593 atlas people with a Wikidata identity,
  only **82** appear anywhere in the review or article data, mostly as authors of a few
  reviewed books (Eley 12, Wehler 8, Winter and Assmann 7). Meanwhile **544 people outside
  the atlas** each have five or more reviewed books; the registry holds about 52,000
  individuals. None of the 885 atlas bibliography records (reading labels) matches a
  reviewed book by title.
- **The record covers the atlas's weakest period.** H-Net (1993–), Reviews in History
  (1996–) and the 405-journal Crossref collection are densest after 1990. The atlas
  thins after 1985 and its post-2000 extension is partial.
- **Two different maps of the discipline.** The profession's own infrastructure classifies
  history by **region, period and theme**: H-Net networks (H-German, H-LatAm, H-CivWar,
  H-Environment), journal directory subjects (Eastern Europe, Middle Ages, Religion), RiH
  headings. The atlas classifies by **approach and school**. Only the theme axis maps onto
  atlas entries. The mismatch is itself a finding worth showing.
- **One network is almost half the H-Net corpus.** H-Soz-u-Kult (general German-language
  history) holds 21,448 of 46,798 H-Net reviews. Any per-field measure must show this
  unassignable share, not silently drop it.

## Principles

1. **Two layers.** The curated teaching graph stays interpretive and editorially owned. A
   derived evidence layer is generated from the registry and corpora, rebuilt as data
   grows, and shown *beside* the interpretation ("the atlas says X; the record shows Y"),
   never merged into it.
2. **Participation, not influence.** Reviews and articles measure where work happened and
   who took part. A review is not agreement, and a count is not importance.
3. **Coverage is always visible.** Corpus, date span and unassigned share are shown next to
   every series. These corpora are not the profession: H-Net is US-centred and starts in
   1993, RiH is British, Crossref coverage is uneven, and ORCID skews recent.
4. **Identity tiers are carried through.** Strict and probable identities are labelled on the
   site; nothing is presented as verified that is not.
5. **Metadata and links only.** No review or article text is republished. Derived metadata
   links to the source (H-Net page or Wayback capture, RiH page, DOI).
6. **Crosswalks are editorial.** Mapping networks, subjects and journals to atlas entries is
   an interpretive act. It lives in a reviewed, versioned file with a basis and rationale
   per row, as the journal catalogue's classifications already do.

## Components, in order

### 1. Field as practice (first)
- **Crosswalk.** Map each H-Net network, RiH subject heading and journal directory subject
  onto three axes: *theme/approach* (→ atlas entry ids, possibly several), *region*, and
  *period*. General sources (H-Soz-u-Kult, "General history") stay `general`. Start from
  the 18 existing network→field candidates and the journal catalogue's subject
  classifications. Every row is `proposed` until reviewed.
- **Series.** Reviews per year per network and subject; journal research items per year,
  using at-least-ten-page items as a provisional research-article proxy. Include journal
  first-record years, flagged where Crossref backfiles distort them.
- **Outputs.**
  - per atlas entry: a practice timeline beside the atlas's own dated span
  - "fields the atlas lacks": large theme networks and subjects with no entry
  - the region × period map of the record, set against the atlas's approach map
- **Checks.** Totals reconcile with corpus counts; unassigned shares are reported;
  multi-mapped sources are not double-counted in any total.

### 2. People across the record
A page for anyone in the registry, not only atlas people: books reviewed (with reviews
received, networks and dates), reviews written, journal articles, dated affiliations, and
tier-labelled identity links. Atlas profiles gain the same panel. Built from the registry,
loaded lazily.

### 3. The missing middle (editorial queue)
Per field and per region: people with large footprints who are absent from the atlas. Rank
by books reviewed, spread of reviews across networks and journals, and career span. The
queue is discovery input for promotions, in the same spirit as the 2026-09-18
representation audit. Gender comes only from Wikidata P21 and is shown only where recorded.

### 4. Reception and the operational canon (decisions needed)
- **Reception.** For each book: lag from publication to review, and how many distinct
  networks, subjects and journals reviewed it. Cross-field books are candidate evidence
  for atlas relationships drawn by hand.
- **Operational canon.** Which works and people reviewers *invoke* in their reviews, year by
  year. This needs a mention extractor over review text (italics, bibliographic patterns,
  known titles), research-only, publishing derived metadata alone.
  **Decision:** proceed with review-text mentions?
- **Citations.** The article data deliberately has no reference lists. **Decision:** resume
  OpenAlex, or fetch Crossref references, for a citation layer?

### 5. Site integration
Build-time, allowlisted evidence files loaded on demand, following the pattern of the
Wikidata overlay; `graph.json` stays small. Each view carries corpus coverage and
provenance.

## Status (2026-09-27)

Components 1-4 have first passes: field-as-practice crosswalk and series, candidate clusters,
approach folds, method signals (titles, abstracts, practitioners) and review-text mentions.
Component 5 is started: entry pages show a "What the record shows" panel from
`docs/data/evidence.json`. Not yet published: the commits are local and unpushed.

## Earlier status

Step 1 first pass done (2026-09-26): crosswalk, yearly series and an overview chart in
[data/evidence-layer](data/evidence-layer/README.md). Next: review the crosswalk, then per-entry
practice timelines, then component 2.
