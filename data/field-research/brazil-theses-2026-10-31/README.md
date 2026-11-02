# Brazilian History doctorates (2026-10-31 to 2026-11-02)

The user asked for Brazil on 2026-10-31 ("start the catalog; I'll figure out space"). The goal is a Brazilian
sub-graph of the dissertation citation graph (2,000+ theses).

`python3 scripts/brazil_pipeline.py status|run|handoff|register|cleanup` drives every step.

## Sources and the History screen
- **CAPES Catálogo de Teses e Dissertações** (dadosabertos.capes.gov.br, open data, 1987–2024) is the
  national record of every defended thesis. A thesis counts as History when CAPES gives level DOUTORADO
  and knowledge area HISTÓRIA: **8,898 doctorates**.
  - The CAPES rows carry the advisor (with a CAPES person id from 2013) and the student id.
  - `capes-raw/` (not in git; 169 MB with abstracts) holds the full rows. `capes/` is the committed
    copy: doctorates only, with the columns the scripts read.
- **PDFs**, all matched to CAPES by institution, title and author (`scripts/brazil_match_capes.py` →
  `candidates.json`):
  - university repositories over OAI-PMH: UFMG, UERJ, UFU, UFES, UFPE, UFPA, UFRJ and FGV (metadata only);
  - the UFF History programme's thesis list, which includes examination committees;
  - USP item pages, reached through its sitemap;
  - author-authorized files on **legacy Sucupira** (`download_sucupira_legado.py`, run by the user's
    decision of 2026-11-01). It also records the committee and funders in `sucupira-records.jsonl`.
  - browser downloads by the user (`scripts/register_brazil_browser_downloads.py`).
- **Result:** 2,718 doctorates with PDFs, logged in `downloads.jsonl`. The PDFs are on E: under
  `historiography-dissertation-pdfs/brazil-theses-2026-10-31/pdf/`.

## Rules followed
- robots.txt is checked with longest-match semantics; `urllib.robotparser` gets teses.usp.br wrong.
  - USP disallows `/oai`, so USP was read through its sitemap and item pages instead. A few minutes
    of USP OAI harvesting by mistake on 2026-11-01 were stopped, and those records are unused.
- sucupira.capes.gov.br disallows every crawler, so its links are never fetched by scripts.
- Bot challenges are never circumvented. FGV, UFSC, UNISINOS, UNICAMP, PUC-SP and PUC-RS appear
  only through Sucupira or the browser handoff.
- TLS verification stays on; certifi supplies the GlobalSign R46 root. UERJ is fetched on port 8443.

## Ingest
`adapter_brazil_capes` in `scripts/dissertation_ingest.py` handles this source. It is registered as
`brazil_capes`, with `"ingest": false` until the user approves the run.
- Dry run, 2026-11-02: 2,710 new entries. 7 are dropped as the same file (theses listed in both the
  2012 and 2013 CAPES files) and 1 as the same title.
- Entries carry the CAPES ids, advisors, committee, funders, and the PDF parts in order (40 multi-part
  USP theses).

`advisor-graph-match-2026-11-02/` holds a name-only match of the 499 advisors against the citation
graph and the key log. These are leads, not identities.
