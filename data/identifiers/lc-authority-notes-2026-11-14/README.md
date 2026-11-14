# LC authorities attached through the titles in their source notes (2026-11-14)

ARCHITECTURE.md section 8, class 40. Script: `scripts/key_lc_authority_notes.py`. **Proposal only: nothing applied.**

## Probe

Valerie Deacon, p-37340 (anchor `aha-phd:17768`; thesis w-11219 "The 'Other' Resistance: The Extreme Right in France
during the Second World War", 2011). LC authority n2016049415 "Deacon, Valerie, 1981-" has one 670: "Her The extreme
Right in the French Resistance, 2016:". The 11-12 pass (`key_lc_authority_ties.py`, class 34) saw the pair and left it
`name-only`: its title tie needs the key's whole main title ("the other resistance") inside the 670, and a thesis
usually becomes a book under a new title; the medium tier needs an institution or a linked-credit title, and LC records
no 373 for her. This rule ties her (strict, `thesis-book`, shared rare words "extreme, resistance, right", 79% of the
note title's weight; born 1981, PhD at 30, book five years later; the only "Deacon, Valerie" in LC and in the graph).

## Rule

- Population: 82,584 live person keys with no `lcnaf:` anchor holding a titled work (the AHA PhD record's title, or a
  key-log AUTHORED / EDITED work other than a review); initials-only labels never.
- Names: the strict full-name rule (`propose_person_dup_merges.names_agree`: same family, the first written-out given
  name identical, no nicknames, initials alone never) against the authorised form (and LC's fuller form) or a 400
  variant: 442,809 pairs on 50,643 keys.
- Notes: each 670 source is read as a work (`His/Her/Their <title>, <year>:`, `Family, Given. <title>, <year>:`, a bare
  `<title>, <year>:`, NUC report prefixes stripped); database, web, mail and phone sources and denials are skipped.
- Title tie, on key-log titles only: `same` (main titles agree, or the key's 3+-word main title runs inside the note), or
  `thesis-book` (the key's thesis and a note dated T-1..T+20 sharing at least two rare words, idf >= 6 over every graph
  work title and the notes, shared weight >= 16, covering >= 50% of the note title's or the thesis title's weight).
- Dates refuse the pair: LC birth vs thesis outside ages 22-70; a note before birth + 18; works before birth + 15; the
  thesis after the LC death, works more than 3 years after it; key life years off by more than 2; a `same` note outside
  T-9..T+50.
- Strict: a title tie, dates fit, the name group closed (no other unseparated key bears the authority's name) or rare
  (at most 2 date-possible LC authorities bear the key's name), the label (not only an alias or variant) agreeing, one
  authority per key and one key per authority. Everything else title-tied goes to the review tier; an authority already
  on another key goes to `possible-duplicates.csv.gz`.

## Counts

| | |
| --- | --- |
| Title-tied pairs | 6,360 (same 3,774, thesis-book 1,061, weak overlap 1,525 not tied) |
| **Strict (proposal.json)** | **4,050** keys (same 3,153, thesis-book 897; bands: unique 2,949, 2-5 804, 6-25 253, 26+ 44); 1,299 status ops recorded → established; dry run: 5,349 events, clean |
| Review tier (`review-tier.csv.gz`) | 477 (name group open 125, variant or alias only 255, key with two authorities 85, authority fitting two keys 12) |
| Possible duplicates | 252 (the authority is anchored on another key; the two keys may be one person) |
| Refused on dates | 73 |

Of the strict pairs, 2,926 are on keys outside the 11-12 population (no thesis/AHA/directory/review evidence: ORCID,
canon and article keys), 993 were name-only in the 11-12 run, 126 were its held medium ties.

## Hand check (`sample-checked.csv`)

130 strict ties, stratified by tie (same / thesis-book) and name band (unique, 2-5, 6-25, 26+ LC bearers), 16-18 per
stratum, chosen by hash so reruns keep the sample. Read against the graph titles and years and LC's heading, dates and
670 text. **130 right, 0 wrong, 0 unclear**: 95% upper bound on the wrong rate 2.3% (0/130). Earlier samples on the
first runs (75 more rows, before the NUC-prefix and given-name parser fixes) were also all right. Two notes on weak but
correct ties: Cassin (the key's main title "Gregory of Nyssa" runs inside a different volume he edited) and Hartman
Davies (a main title shared by his article and the volume he co-edited); both names are unique. The bound is above 1%
because the sample is 130; the rule was not loosened.

Unverified: no web page was read; judgements rest on the graph and LC metadata.
