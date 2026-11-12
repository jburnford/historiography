# Translations and editions of dissertation-cited works (2026-11-11)

Not applied: nothing here is a key-log event, and build_graph.py / export_cited_works.py are unchanged.

## Files
- `lc-clusters.csv.gz`: LC 2016 records clustered into works from MARC 240 (uniform title with $l language), 041 $h,
  500 "Translation of" notes, and records by the same main entry whose 245 $a equals the uniform title. One row per
  record: cluster_id, lccn, role (original / translation / later edition / compilation), lang, original_lang, basis,
  original_lccn, cluster_canonical, graph_node. 378,961 records in 195,928 clusters (186,645 translations, 63,508
  originals, 36,477 later editions, 92,331 records with collective uniform titles: Works, Selections, Poems ...).
  A few records appear twice where one LCCN is held by two graph nodes.
- `lc-edition-groups.csv.gz`: LC records with the same main-entry heading (dates removed) and the same full 245 $a
  (3+ words), held by more than one graph node (edition splits).
- `crosswalk.csv.gz`: corpus work_id -> canonical_id, relation (translation / edition / compilation), cited_language,
  route, basis, confidence, cited_by_dissertations, cited and canonical titles, cluster_id, previous_target (the node
  the work is matched to now, for consolidations), recovers_citations (true = the work was unmatched before),
  canonical_key_authors (>1 = the canonical key pools LC records by different main entries).
- `compilations.csv.gz`: works judged compilations with no single original (Microfísica do poder, O poder simbólico,
  A história cultural, Magia e técnica arte e política, Obras escolhidas, Ditos e escritos ...). No canonical work.
- `held.csv.gz`: failed verification, article/chapter translations, classical texts, unsure, ambiguous clusters,
  and the dropped catalogue route.
- `judgments.csv.gz`, `judgments/`: every verdict with the verifier's evidence; batch files, the frozen row index and
  copies of the scratch scripts (marc_extract.py, clusters.sql, cands.py, packets.py, verify.py, assemble.py, report.py).
- `audit-sample.csv`: 200 rows judged against the catalogue records.
- `report.json`.

## Routes
1. `author-constrained` (unmatched works): the cited title is in another language than the author's LC records;
   the original was proposed from knowledge and counts only when verified mechanically (see report.json audit).
   Canonical = the key holding a verified LC record (earliest), else the LC cluster canonical, else the keyed work,
   else `lccn:` of the earliest verified record.
2. `lc-cluster` (matched works): the matched node holds an LCCN that LC marks as a translation or later edition of a
   cluster whose canonical is another node. No new matched citations; the citations move to the canonical work.
3. `lc-edition-split` (matched works): same LC main entry and same full title held by several graph nodes;
   canonical = keyed node, then the earliest record.
4. `catalogue` (dropped after the audit, 21/23): the cited title equals a record inside a translation cluster.

Cluster canonical order: key holding the original LCCN; key holding an original-language edition; unkeyed graph node
of an original-language edition; `lccn:<original>`; a keyed translation only when LC holds no original.

## Known cases
- Foucault: Surveiller et punir 75505881 (original, key w-205024) with German 77565170 and English 77005301 /
  78011257 / 95203580 (key w-204964): Discipline and Punish (703 theses) now consolidates into w-205024.
- Bloch: Apologie pour l'histoire a51010626 (1949) + 75502294 (1974 edition), both in key w-1182922; The historian's
  craft 52012182 (w-1182930) and Russian 87123985 are translations.
- Anderson, Imagined Communities: 84152806 (1983), 91010900 (1991 rev.), 2006281800 (2006) are pooled in w-315433:
  right (one work, three editions). LC holds no translation of it with a 240, so it has no LC translation cluster; the
  Swedish and Portuguese editions come in through the author-constrained route.
- Lyell, w-289585: all 11 LCCNs are Principles of Geology (eds 1-11, 1830-1872, the 1969 and 1990 facsimiles and
  Secord's 1997 Penguin abridgement). Pooling is right at the work level; the problem is only that edition-level
  facts (Secord as editor of the 1997 abridgement) attach to the work. Edition editors should hang on the edition
  (its LCCN), not the work key.
- Key-log over-pooling found on the way: w-165950 "Machiavelli" holds LCCNs of books by Skinner, Price, Cust,
  Barincou and Machiavelli himself (same title, different works). 9 canonical keys pool records by several LC main
  entries (`canonical_key_authors` > 1); worth a review queue.

## How the graph should represent this
The JSTOR convention fits: `export_jstor_citations.py` writes a CITES edge to the work with `edition = true` when
the citation is to a later edition or translation (basis 'edition'), and build_graph keeps `edition` on cites.
Proposed change (not made):
- `export_cited_works.py`: after choosing a corpus work's cited id, look the corpus work up in this crosswalk; when
  relation is translation or edition, write the CITES row to `canonical_id` with `basis = translation|edition` and a
  new column `cited_as` = the previous cited id (key, `lccn:` or the corpus work id when it was unmatched).
- `build_graph.py`: carry `edition = true` (as for JSTOR) plus `cited_as` and `relation` on CITES; add Work nodes
  (resolution `unkeyed`) for the 1,756 `lccn:` canonical ids not yet in data/graph/cited-works/works.csv.gz; add a
  `translation_of` / `edition_of` edge table from each previous node to its canonical (from the lc-cluster and
  edition-split rows), so the explorer can show editions without merging keys.
- Compilations get no canonical: keep them as unmatched (or as unkeyed `corpus:` works later) and list them; a
  compilation-contains-work relation needs per-volume tables of contents, which we do not have.
- Keys are not merged here: a translation key (Discipline and Punish) keeps its identity; the merge-or-not decision
  for key pairs in one LC cluster belongs to a key-log proposal.

## Round 2 (2026-11-11, later)
- Judged the X rows cited 5–8 times and the unknown-language rows that have LC titles by the author, down to
  judgment-index row 4013 (cited 6+). Not judged: 1,115 rows cited 5–6 (5,584 citations) after that row, and 1,207
  rows whose author has no LC title at all (6,726 citations; only the key-log-work route could verify them).
- Fresh audit of 100 newly judged rows: 96/100. Low-confidence author-route proposals are now held
  (`low_confidence_after_round2_audit`); 96/99 on the rest. `audit-sample-round2.csv`.
- Round-1 numbers are kept under `round1` in report.json.
- Brazil denominator: 2,615 Brazilian theses with citations (not 12,000+). Hobsbawm: 21 → 719 theses (0.8% → 27.5%);
  the parsed-name route gives 835 (31.9%); the gap is imprint strings parsed as titles, the Francis Newton pseudonym
  (The jazz scene), the "Hobsbawn" misspelling, chapters and edited volumes.
- Compilations keep their author at person level only if the graph carries them: `compilations.csv.gz` now has
  `corpus_person_key` and `kg_person_key`; proposed representation is an unkeyed `corpus:` Work node with CITES and a
  linked_authored edge (not identity evidence), never a canonical/edition link.
