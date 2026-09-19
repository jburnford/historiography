# Production promotion batch — revision 1.119

The user explicitly requested production integration of the eight proposals. The graph now includes Joan Wallach Scott, Natalie Zemon Davis, Lynn Hunt, Catherine Hall, Leonore Davidoff, Evelyn Brooks Higginbotham, Linda Tuhiwai Smith and Lorraine Daston as full entries, using existing shared person IDs.

**124 entries (73 groups, 51 people), 761 teaching connections, 840 sources and 829 shared people.** No new authority match or gender classification was accepted. Earlier nodes, edges, sources, roster/strand contexts and the journal catalogue are preserved. Only the eight existing people gain `node_id`. [Acceptance record](acceptance.json) pins the original graph, research packet and resulting production graph.

Nine teaching edges (`edge_753`–`edge_761`) present selected claims. Eight are accepted within their evidence limits. Davis → comparative biography remains explicitly **provisional**, supported by a book description with body-text checking open. Its label, `review_status` and underlying claim retain that distinction.

The optional `claim_catalogue` is production schema 1.0 using vocabulary 0.2. It preserves seven shared works and eighteen historical claims: **seventeen accepted, one provisional**. Nine authorship credits and eight entry/person links bring the catalogue to 35 claims. These overlap teaching views and must not be added to the edge count as distinct relationships. Hall/Davidoff share one work, as do Daston/Galison. Rosaldo, Hine and Smith-Rosenberg participate without full nodes. Collins remains a local catalogue referent with unresolved external identity, not a new shared-person record.

## Website handoff to Fable

The user assigned the rebuild to Fable. Website source and generated `docs/` assets remain at their pre-import state; **the new data is not yet in the browser build**. No push or deployment performed.

Read the production JSON and `GRAPH-FORMAT.md`. New edge fields:

- `claim_ids`: underlying exact claim.
- `claim_projection.subject` and `.object`: original person/work/concept endpoints; the note explains their teaching view.
- `target_strand`: compound `entry_id/strand_id` where applicable. Display that qualification rather than implying a claim about the whole field.
- `review_status`: accepted or needs_review. Davis’s legacy label also says provisional.

New nodes carry `work_ids` and `claim_ids`. Catalogue entities distinguish people, works, concepts and entry presentations. Shared works retain every `author_id`. Claims retain predicate, statement, qualification, intervention year, review/history and citation-specific evidence. A work’s year is not a field origin or career boundary (`valid_time` remains null).

**Check status belongs to `claims[].evidence[]`, not sources.** Display passage/abstract/description distinctions, locator, access limits, check date and provisional state. New top-level sources point to catalogue witnesses with `claim_source_record_id`; their `scope_note` is not blanket verification.

Expose all eighteen historical claims from author entries and shared-person profiles, including contributors without nodes. Match people through `legacy_person_id`, then works through `author_ids`, and retrieve claims involving either. Fields can match the parent of exact `legacy_strand_address` values. Authorship/presentation links are metadata, not influence arrows. A concept-targeted critique must not become a critique of every scholar cited or the entire field.

Keep the build allowlist and accepted-only Wikidata enrichment. Raw captures/PDFs and local snapshot paths are repository provenance, not new browser assets. Separate gaps identified in the user's latest question: Himmelfarb, Thirsk, Letitia Woods Brown and Lily Ross Taylor are absent; Lerner is roster-only; Tuchman and Wedgwood already have full nodes. This batch did not add the four or promote Lerner.

## Checks and preserved baselines

```sh
python3 scripts/audit_promotion_import.py
python3 -m unittest tests.test_promotion_import tests.test_graph_validation tests.test_people_validation
```

Twenty tests and exact import/preservation audit pass; previous structural warnings are unchanged. After rebuilding, add `--check-public` to the audit to verify generated data and assets. That option is expected to fail before the rebuild.

The staging packet and manifest remain frozen. Their unchanged-production assertions describe the historical research baseline. Do not rerun their builders on newer production or rewrite old hashes. Original graph bytes are in `drafts/historiography-1920-2000.v1.118.json`, browser bytes in `drafts/extension-browser-v1.118/`. The production audit resolves pinned baseline inputs to those archives. Other research packets remain staged.
