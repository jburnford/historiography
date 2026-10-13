# Patrick Wolfe: person entry draft for 1.129

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json).

## What is proposed

- **Node `patrick_wolfe`.** A person entry with the twelve standard person keys. The
  date label is *Settler Colonialism and the Transformation of Anthropology 1999 · later
  essays 2001, 2006 · coverage through 2000*.
- **`people_update`.** The existing `patrick_wolfe` record gets `node_id: patrick_wolfe`.
  Both roster rows stay unchanged: contributor in `settler_colonialism` and comparison in
  `indigenous`.
- **Edge 1 (main).** `patrick_wolfe → settler_colonialism`, contribution, evidenced by the
  1999 book. It has no strand target (see below).
- **Edge 2 (optional).** `patrick_wolfe → anthropology/colonial_knowledge`, contribution.
- **Not proposed.**
  - `→ indigenous`;
  - `→ racial_formation`, because the evidence is post-2000 and `edge_885` already covers it.
- **Two new sources.** The 1999 contents page and the CiNii catalogue record. Five existing
  `screq_` sources are reused.

## Verification

| Source | Check | What it supports |
| --- | --- | --- |
| `cpl129_wolfe_1999_contents` (new) | Contents scan, digitized by IDS Basel Bern and hosted by BVB, read 2026-10-13; found via OpenAlex W3044173471 | Chapter titles only: introduction "Anthropology and Settler Colonialism"; virgin birth "in Anthropology and in Australian Settler Discourse"; "Science, Colonialism and Anthropology"; mother-right; totemism; Tylor; "Repressive Authenticity" |
| `cpl129_wolfe_1999_catalogue` (new) | CiNii BA39470163 | Cassell 1999, 246 p., LCCN 98022519, both ISBNs. LCSH includes *Racism in anthropology -- Australia* and *Australian aborigines -- Public opinion* |
| `screq_wolfe_1999` | Open Library OL1895662W rechecked | Author OL226928A; ISBNs and LCCN agree with CiNii |
| `screq_wolfe_2001`, `screq_wolfe_2006`, `screq_kauanui_2016`, `screq_veracini_2013` | Crossref (mailto) rechecked | Metadata agrees with the atlas records |

**The book itself is unread.** No claim rests on its argument or stance. The description says
only what the title, the contents and the subject headings show.

**"Structure, not an event."** The formulation appears only in the scope note, attributed to
Kauanui's 2016 abstract, and the note says Wolfe's own pages are unchecked. The edge does not
use it as evidence.

**Founder claim.** The draft makes none. The scope note and edge 1 both cite earlier usage of
the term (Veracini 2013) and earlier settler-society studies (1983, 1995).

## Wikidata Q109284663: the right person

Checked with the MCP tools (`search_items`, `get_statements`, `get_statement_values`).
- **The item.** "Australian historian", born 12 June 1949 (LoC-referenced), died 18 February
  2016 in Melbourne.
- **LoC authority n98039450.** It was established from the 1999 book's CIP record, with a
  birth date of 06-12-49, and it also cites *Traces of History* (2016).
- **Open Library OL226928A.** This is the author on the 1999 work record.
- **No duplicate item found.**
- **Limitation.** Wikidata has no notable-work link to the book.

## Edges: reasoning

- **Settler colonialism, contribution.** The 1999 book is the only in-period evidence. Its
  title and contents frame anthropology's history through settler colonialism.
  - **Wording.** This is a contribution, not a founding. Canadian uptake is post-2000: 17
    PhDs cite the book (first in 2012), and 54 cite any of his works. The evidence note says
    so.
  - **No strand target.** `structure_and_elimination` would imply that the formulation is
    checked in the 1999 book. Reviewers may still choose it.
- **Anthropology (optional), contribution.** This edge has direct in-period evidence. The
  chapters are on Victorian anthropology, Tylor, totemism and mother-right, and the
  catalogue gives *Racism in anthropology* as a subject.
  - **Kind.** The stance is unread, so the draft uses contribution to `colonial_knowledge`.
    If the introduction shows a critical argument, critique toward `anthropology/evolution`
    may fit better.
- **Indigenous: not warranted.** The 1999 book studies anthropological and settler
  representations of Aboriginal people. It does not contribute to Indigenous historical
  practice or method, and the Indigenous scope rejects anthropology or European theory as a
  common origin. The roster comparison row, its strand and `edge_881` already carry the
  relation. Indigenous engagement with Wolfe is post-2000 and partly critical (Kauanui,
  Konishi).

## Citation evidence

Source: `canadian-historiography-scholars-request-2026-10-12/candidates.csv`.
- **Reach.** 54 strict History PhDs (2009–2026) at 18 universities, 13 of them at Toronto or
  York.
- **Trend.** The share rose from 0.98% (2009–14) to 8.64% (2020–26). That +7.7 points is the
  largest rise among the 162 candidates; next is Stoler at +6.3.
- **Most-cited work.** "Elimination of the Native" (31 PhDs).

## Open leads (not used)

- **Two reviews, both unread:**
  - Deborah Bird Rose, review essay, *Postcolonial Studies* 4:2 (2001): 251–261,
    doi:10.1080/13688790120077542. Crossref metadata only, no abstract.
  - Chris Healy, review, *Meanjin* 58:2 (1999): 196, via OpenAlex W2258757203 and Informit.
    This one is in-period reception.
- **Reading the introduction (pp. 1–8).** This would settle the kind of the anthropology edge,
  and whether the 1999 book states "structure, not an event".
- **Duplicate records.** `ind127_wolfe_1999` and `screq_wolfe_1999` describe the same book;
  consider merging them at release.
