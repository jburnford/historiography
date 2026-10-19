# Revision 1.145: wording check of the WebFetch-extracted quotations

- **Date:** 2026-10-18.
- **Method:** each page was fetched with curl and its HTML reduced to plain text. Every quotation the evidence notes attribute to it was then matched, after normalising curly quotes, dashes and whitespace.
  - reviews.history.ac.uk returned 403 to curl, so the Griffin review was read from the Internet Archive capture (`web.archive.org/web/2024/https://reviews.history.ac.uk/review/943`).
  - No pages are kept in the repository.

| source id | page | result |
|---|---|---|
| `cd_mendels_stone_nyrb_1984` | nybooks.com, 25 Oct. 1984 letters | All 7 Mendels and Stone quotations match word for word (evidence-industrialisation.md §1e). |
| `cd_griffin_allen_2010` | Reviews in History no. 943 (Internet Archive copy) | All 6 quotations match word for word. |
| `cd_nyt_capitalism_2013` | cupblog.org, 8 Apr. 2013, quoting the *NYT* | All quotations match. The Levy sentence is split on the page: “And to understand capitalism,” said Jonathan Levy, [an assistant professor of history at Princeton University and the author of …,] “you’ve got to understand capitalists.” Any display must mark the omission. The *NYT* article itself remains unread. |
| `cd_economist_baptist_2014` | mprnews.org, 5 Sept. 2014 | The review sentence and both apology sentences match word for word. |
| `cd_mokyr_nobel_2025` (for 1.146) | northwestern.edu, “Nobel laureate” | “in recognition of his groundbreaking theory on sustained economic growth” matches. The official nobelprize.org wording is still unchecked. |

**Brenner 1976.** The source record `rb_brenner_1976` already cites the official DOI, https://doi.org/10.1093/past/70.1.30. Crossref confirms *Past and Present* 70, pp. 30–75, 1976. The record does not link the course or Internet Archive copy. Only its verification note names that copy.
