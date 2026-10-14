# Backlog from the Gemini review of 1.130 (2026-10-13)

The user pasted an outside review of the public site at 1.130 and asked to "note this for
future work". This is the review triaged against the data and code. Nothing here is
scheduled.

## Wrong or already done

- **Deep links already exist:** `#node=<id>`, `#edge=<id>`, `#path=<id>`, person and family
  hashes. Possible small task: a visible "copy link" control.
- **No unclassified relationships remain.** All 913 edges carry a `relationship_kind`; the 182
  undirected edges are deliberate comparisons.
- **Digital history exists**, with a post-2000 extension. The five extended entries are
  indigenous, medicalhistory, spatialhistory, digital_history and web_history.
- **Environment timeline:** fixed by 1.131. The family still has only two fields.

## Worth doing, in suggested order

1. **Critique backfill.** 70 of 166 entries have no critique edge in or out, which is worse
   than the review's "~25%". Start with science studies: kuhn, latour, ssk, sts and science
   have none. Use the in-period Science Wars: Gross and Levitt 1994, the Sokal affair 1996,
   Hacking 1999. Then audit the rest.
2. **Canadian lens toggle** on the landing atlas-versus-record chart. The Canada family's 17
   entries compress the other families' atlas share, while Canadian journals are about 2% of
   the record. Show the chart with and without it.
3. **History of emotions and senses entry, with pre-2000 roots:** Febvre's sensibilité (1941),
   Stearns and Stearns' emotionology (1985), Corbin (1982), Reddy (1997). Possibly material
   culture too.
4. **Break up the unclaimed 35%** of 2000–2024 articles into flagship generalist, period and
   national/regional journals, using journal-level data we already hold.
5. **People graph controls:** a minimum-appearances filter and a one-hop ego-network
   highlight.
6. **Lower priority:** a side-by-side entry comparison; `.bib`/RIS and printable exports for
   entries and pathways; a browse-by-journal view.

## Defer

- **Post-2000 expansions:** climate and the Anthropocene (Chakrabarty), the new history of
  capitalism and racial capitalism, emotions after 2000 (Rosenwein), Trentmann. These belong
  to the planned whole-atlas rebuild that drops the 2000 cutoff, not piecemeal additions.
- **Non-Western traditions:** Latin American dependencia and social history, East Asian
  historical materialism, Korean Minjung, Ibn Khaldun's reception. A real gap, but it needs
  the same careful front-and-centre evaluation as the Environment family (field
  self-accounts first), not a quick 4–6 entries.
