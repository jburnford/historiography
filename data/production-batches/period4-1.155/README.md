# Revision 1.155: a fifth teaching period, c. 2000–

The user (2026-10-23), after the cohort analysis of the History PhD citation graph
(`data/field-research/dissertation-citations-2026-10-11/summary/cohorts/README.md`): "use this information to
build out the atlas (that we don't call an atlas anymore)". Their reading of the analysis: the
historiographical narrative is still the 1980s debate (Thompson against Joan Scott, Foucault and Derrida);
"there is no new big debate that everyone feels the need to cite"; the change is new fields, environmental
history and settler colonial studies in particular, perhaps the history of emotions.

- **Batch:** `data/extension-2026/period4-frame-2026-10-23/batch.json`.
- **Change:** one guarded replacement of the top-level `periods` list, adding
  `period_4` "Layering: new fields under a settled canon, c. 2000–", and six guarded `period` field sets:
  `settler_colonialism`, `liberal_order_framework`, `cdn_sixties`, `digital_history`, `web_history` →
  `period_4`; `languages_of_class` → `period_3`. No entry, edge or source text changes.
- **Why the name.** In the citation graph the theory canon of 1963–98 holds in every cohort since 2010
  (Foucault 17% of theses, Anderson 11%, Thompson and Joan Scott 6% each); no pair of later works is
  co-cited by more than 3% of theses; what grew after 2000 is a layer of regional frameworks and fields
  (the archive as object, settler colonial studies, environmental history, empire and sovereignty, the
  history of capitalism) added under the floor. The period is named for that finding.
- **Why these entries.** Each by its own chronology: settler colonialism (Wolfe 1999 and 2006, Veracini
  2010, the journal 2011, critiques 2012–20); the liberal order framework (McKay 2000, the 2009 debate);
  Canada's 1960s (Owram 1996 as the early account, Palmer 2009, Mills 2010, the 2013 collection); digital
  history (2003–22); web history (2003–26). The languages of class debate (1983–96) belongs with the further
  turns of c. 1985–2000. `capitalismdebates` (1944–2023) and the enduring fields stay unassigned by design.
- **Applier:** `periods_set` ({expect, value}) replaces the period list, guarded like `layers_set`; the
  prior list is kept in the acceptance record (`prior_periods`) for exact baseline recovery; `period` joins
  the `field_sets` allow-list. Test: `tests/test_apply_person_entries_fields.py::PeriodTests`.
- **Next:** the period's content. Wave 1 research (`data/extension-2026/period4-wave1-2026-10-23/`): the
  archive as object (new entry; Stoler and Trouillot person entries), settler colonial studies to 2024
  with the Wolfe entry backfilled, environmental history to 2024 with Cronon and Worster backfilled.

**Checks.** `--check` is exact; `validate_graph.py` 0 errors, 12 warnings (baseline).
