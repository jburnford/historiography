# Donald Creighton: person entry draft (Tier 1, 2026-10-14)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json). Applied in memory
to the live graph (revision 1.133), it adds the node, sets `node_id` on the people record,
adds eleven new sources and three included edges (as `edge_919`–`edge_921`), and puts the
edge 1 id on Creighton's `cdn_national_tradition` roster row. `validate_graph` reports
**0 errors and the same 7 warnings** as the unmodified graph (168 nodes, 921 edges). No edge
or node cites a missing source id.

## What is proposed

- **Node `donald_creighton`.** The twelve standard person keys. The date label lists dated
  works only: *The Commercial Empire of the St. Lawrence 1937 · Dominion of the North 1944 ·
  John A. Macdonald 1952, 1955 · CHA presidential address 1957 · "The Decline and Fall of the
  Empire of the St. Lawrence" 1969 · Canada's First Century 1970*. There is no
  `reviewed_through` key, because person nodes do not carry one.
- **`people_update`.** The existing record gets `node_id: donald_creighton`. Its people id is
  `donald_creighton` (checked). His only roster row is on `cdn_national_tradition` (role
  historian). He appears in three strands there: `laurentian`,
  `liberal_conservative_nationalists` and `analysing_tradition`.
- **Edge 1: → `cdn_national_tradition` (contribution).** "Laurentian narrative, 1937–55".
  Strand `cdn_national_tradition/laurentian`; roster row `cdn_national_tradition`.
- **Edge 2: `harold_a_innis` → `donald_creighton` (influence).** "Staples behind the Laurentian
  narrative, contested". No strand and no roster row, because the target is a person entry.
- **Edge 3: → `progressive` (critique, type `critique`).** "Against the frontier thesis,
  1957". Strand `progressive/progressive`, which lists Turner and "Turner's frontier essay".
  No roster row.
- **Edge 4: → `karl` (critique). Optional; `include: false`.** It covers the 1957 attack on
  the "Marxian doctrine of the class struggle". I excluded it because his object is the
  League for Social Reconstruction's use of Marxism in Canada, not a position held by any
  `karl` strand or roster member. The editor may restore it.
- **Sources.**
  - Eleven new: the 1969 lecture, the 1957 address, *Dominion of the North* (1944), the Innis
    portrait (1957, metadata only), *Canada's First Century* (1970, metadata only), and the
    reviews or readings by Heaton (1938), Brunet (1953), Frégault (1955), Brouillette (1957),
    Woodcock (1979) and Ouellet (1984).
  - Two addenda: `cdng_davis_1985` (now read in full) and `cdng_creighton_macdonald` (volume
    subtitles, from the review headers).
  - Reused without re-reading: `cdng_creighton_1937`, `cdng_salmon_1997`, `cdng_buckner_2000`,
    `cdng_miville_2016`, `cdng_careless_1954`, `cdng_innis_1930` and `cdng_innis_1940`.

## A historical big idea that declined

The entry says so, but only in dated, attributed terms:

- **His own view.** Creighton's 1969 lecture describes the "decline and fall" of the Empire of
  the St. Lawrence. That is a decline of the country he described, not of his thesis.
- **The field.** The node draws on Buckner (2000), which says the national frame gave way from
  the late 1960s to "limited identities". It also draws on Davis (1985), which shows
  metropolitan theses, Creighton's among them, attacked by hinterland critics and recommends
  that urban historians drop them.
- **Citation data.** The Canadian-PhD citation share falls from 7.3% (2009–14) to 2.7%
  (2020–26). This is recorded in `citation_evidence` only, never in entry text.

## Verification: what was read

| Source | Check | Supports |
| --- | --- | --- |
| `pe135_creighton_decline_1969` (new) | Read in full, pp. 14–25, OCR of page images (Internet Archive capture of the Érudit PDF; live Érudit has a bot wall) | His own retrospect on the Laurentian theme (pp. 14–17), the Innis qualification (pp. 14–15), the "trilogy on one theme" (p. 16), and his later nationalism (pp. 18, 21–25) |
| `pe135_creighton_address_1957` (new) | Read in full, pp. 1–12, OCR of page images (Internet Archive capture) | Innis "at its height" (p. 3); the Liberal "Authorized Version" (pp. 4–5); the Marxian and frontier theories (pp. 6–12) |
| `pe135_creighton_dominion_1944` (new) | Open Internet Archive copy: contents and pp. 3–6, 21, 24–25, 166, 185, 270, 272, 298, 419, 505–507. Pages are taken from the printed running heads, because the OCR leaf map is offset | The in-period Laurentian statement (pp. 21, 24–25, 298, 419); Innis's books in the reading list (p. 506) |
| `pe135_creighton_heaton_1938` (new) | First page only (p. 565), from the Cambridge Core first-page image | In-period reception; the book's own words as Heaton quotes them |
| `pe135_creighton_brunet_1953` (new) | Read in full (RHAF; Internet Archive capture) | Quebec in-period critique of *The Young Politician* |
| `pe135_creighton_fregault_1955` (new) | Read in full (RHAF; Internet Archive capture) | Quebec in-period review of *The Old Chieftain*: praise, and the missing French Canadians |
| `pe135_creighton_brouillette_1957` (new) | Read in full | The Innis portrait's account of the east–west, St. Lawrence axis, as the reviewer reports it |
| `pe135_creighton_woodcock_1979` (new) | Read in full (UBC OJS PDF) | Reading of the Innis lineage (p. 134); critique of his account of Confederation (p. 140) |
| `pe135_creighton_ouellet_1984` (new) | pp. 225–229 read | "partant de la théorie des staples"; "le chef de l'Ecole laurentienne"; the Conquest scheme before Séguin, Frégault and Brunet |
| `cdng_davis_1985` (addendum) | Read in full (Internet Archive capture) | Harrison on Creighton and Innis; Morton's two remarks as Davis quotes them; Careless's sources; the "Laurentian School, then regnant" |

**Not read.**

- ***The Commercial Empire of the St. Lawrence* (1937).** The Internet Archive copies are
  borrow-only, and their search-inside service returned "Item not available". Its argument is
  carried by three labelled substitutes: the 1944 book, Heaton's first page and the 1969
  retrospect. The 1969 retrospect is the author's later statement, so the edge does not rest
  on it for what the 1937 text says.
- **The Macdonald volumes (1952, 1955), *Canada's First Century* (1970) and the Innis portrait
  (1957).** None of these was read. The node's account of his later nationalism rests on the
  1969 lecture.
- **Careless, "Frontierism, Metropolitanism, and Canadian History" (CHR 1954).** UTP returned
  403. *One West, Two Myths II* is not open access.
- **Morton, "Clio in Canada" (UTQ 1946) and "Canada's History and Historians".** UTP and Project
  MUSE were blocked. Both are known only through Davis's quotations.
- **Berger, *The Writing of Canadian History* (1976), chapter on Creighton.** The Internet
  Archive copies are borrow-only.
- **Other reviews.** Lower's CHR review (1938) returned 403, and Tucker's AHR review (1939)
  returned 403. Paquin (1999) on the compact theory could not be reached: the Érudit bot wall
  blocked it and no capture was found.
- **Google Books.** The API quota was exhausted. HathiTrust returned 403.

**Founder claims.** The draft makes none. In 1969 Creighton reports that others regarded the
phrase as "the inspiration, at least in part, of a new school" and the "genesis" of "the
Laurentian interpretation". He says only that he had "no wish to disavow the parentage of an
idea". "Laurentian School" or "École laurentienne" appears only in attributed later readings
(Ouellet 1984, Davis 1985).

**Contested claims recorded as contested.**

- **Brunet (1953).** He finds "nombreux préjugés", says no French-Canadian newspaper was read,
  and sees a hero "centre-moteur".
- **Frégault (1955).** He asks "où sont les Canadiens français", while praising the book.
- **Morton, through Davis.** He says the metropolitan thesis minimizes the hinterland.
- **Woodcock (1979).** He calls Creighton's centralist reading of Confederation "a major
  distortion".
- **The Innis lineage.** Creighton disputed it himself (1969); see edge 2.
- **Polemics recorded, not adopted.** The 1957 and 1969 judgements of King, Quebec,
  bilingualism and American power are recorded as his claims.

## Edges: reasoning

- **Edge 1.**
  - **Evidence.** In-period evidence comes first: his own 1944 text, then Heaton (1938),
    Brunet (1953) and Frégault (1955). The 1969 retrospect is labelled as the author's later
    statement.
  - **The biography.** It is folded in because Creighton himself calls the 1937 book and the
    two Macdonald volumes "a trilogy on one theme".
- **Edge 2.**
  - **The case for it.** His own staple vocabulary (1944, p. 21), the reading list (p. 506), his
    1957 recollection of Innis's influence, and readers from 1979 to 1997 support it.
  - **The qualification.** His 1969 denial concerns where the subject came from (Kennedy, not
    Innis). The wording keeps that qualification, so the edge says "resource", not
    "derivation".
  - **Alternative.** If reviewers think the strand `cdn_national_tradition/laurentian` (which
    names both men) is enough, set `include: false`.
- **Edge 3.**
  - **Why propose it.** The brief asks for critique edges where the person criticised an atlas
    entry's position in his own words. The 1957 address attacks Turner's frontier thesis
    (pp. 6–9 and 12).
  - **Limits stated.** It is a polemic that names no Canadian frontierist. The atlas's own
    reading of Turner (`multiple_hypotheses`) shows a less doctrinal Turner.
  - **Context.** Davis records that Careless's 1954 article was also an "obituary" for the
    frontier thesis.
- **Edges considered and not proposed** (details in the draft):
  - `quebec_historiography`: his 1969 target is public opinion, not named historians, and
    edge_799 carries the comparison;
  - `biography`: folded into edge 1;
  - `cdn_political_national`: later field, with no roster row;
  - `urbanhistory` and metropolitanism: Careless's ground, and edge_800 exists;
  - a Morton or regional critique arrow: edge_805 exists;
  - a critique of the Liberal "Authorized Version": it would point at his own group entry.

## Wikidata

Q3036031 (Donald Creighton, 1902–1979) is **correct**. It was checked with the MCP tools
`search_items` and `get_statements`. Cross-checks:

- Open Library OL141501A, which is the target of OL5686088A, carries remote id Q3036031 and is
  the author of `cdng_creighton_1937` (OL1380120W).
- The citation graph's person node already carries Q3036031.

## Open questions for the editor

1. **Edge 2.** Keep the Innis → Creighton influence edge, given Creighton's own 1969
   qualification, or leave the lineage to the shared `laurentian` strand?
2. **Edge 4.** Restore the excluded Marxism critique (to `karl`), or leave the 1957 attack on
   the class-struggle reading in the node text only?
3. **Second roster row.** Should Creighton get a roster row on `progressive` as a critic? The
   edge sets `roster_row` null because he has none.
4. **Unread texts.** A borrow of the 1937 book (its preface, for its own statement and any
   acknowledgement of Innis) and of Berger 1976 (the Creighton chapter) would close the main
   gaps.

No email address or other personal identifier was sent to any service. The services used were
OpenAlex (with the repo key), Crossref, Open Library, Internet Archive metadata and Wayback,
the Cambridge Core public page and first-page image, UBC OJS, web search and the Wikidata MCP.
