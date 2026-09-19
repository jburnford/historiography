# Fable handoff: bounded post-2000 release candidate

The source data is prepared in `candidate.json`, rebased on production revision 1.121. Reproduce a complete simulated graph under `/tmp` using the command in the README. Production has not been changed and all new claim review states remain `needs_review`. The candidate is suitable for implementing and testing the extension view before recorded acceptance; do not publish the preview as an accepted release.

## Separate the baseline from selected later contributions

`scope.main_period` remains `[1920, 2000]`. `scope.extension` carries `proposed_view_period: [1920, 2026]`, the research cutoff, two field IDs and `latest_selected_publication: 2025`. Each changed node has `extension_coverage` with its exact selected years, works and historical claims. New strands carry `intervention_year` and `work_ids`. Those dates describe scholarly interventions, not field origins, lifespans or the period studied.

Implement a baseline/extension view choice. The baseline view must omit the candidate additions, not merely hide their dates. Use the pinned production graph for the baseline or an exact reverse delta; do not infer which roster people existed in 2000 from their life dates. Existing source records published after 2000 can still support older claims, so publication-year filtering alone is not a valid baseline reconstruction.

Keep unchanged entries at their own recorded coverage. An extension canvas reaching 2026 must not automatically extend every open field or person mark to that boundary. Derive its domain from the selected view metadata and show new intervention dates separately from the original field mark. The field is not founded anew in 2002/2004. No new layer or generic post-2000 generation is required.

Current read-only inspection found `site/field.mjs` computes its maximum from parsed baseline spans and reads coverage from `scope.main_period`; `site/app.js` also uses that limit and contains fixed 2000 explanations; `site/index.html` retains a 1920–2000 subtitle. Existing code does not consume the new `extension_coverage` fields. Re-check these observations against Fable's current working state before editing.

## Expose the exact claims and evidence

Each changed node and new strand references `claim_catalogue` through `work_ids` and `claim_ids`. Resolve the exact subject/object and show the statement, qualification, intervention year and each evidence join's locator, check status, support and limitation. New graph source records use `claim_source_record_id` to reach the source witness; a source URL alone is not the claim's verification status. Keep source-capture paths as audit provenance, never browser fetch targets.

Preserve all coauthors. The 2025 medical article has four authors; the 2025 geography editorial has five. Frederick Hickling, Aggrey Burke and Suman Fernando are subjects of the psychiatric history, not authors of its 2025 article. Rebecca Wynter and Sylvia Wynter are different people. A method or argument belongs to its work; do not turn roster membership into an influence arrow. This candidate creates no teaching edges.

Ian Gregory's old roster record is deliberately unchanged. His additional 2007 work appears through the new Gregory/Healey strand; a profile must collect new work contexts from strands as well as the legacy roster. McKittrick's 2006 intervention is consulted through a separately identified 2020 reprint; neither that reprint nor a 2026 anniversary edition changes the intervention date.

Read-only search found no `claim_catalogue`/`claim_ids` consumption in the current `site/app.js`, `site/core.mjs` or `site/people.mjs`. This is a functional dependency, not simply a title or axis edit. The public build already carries the graph but must be checked for the exact claims, statuses and participants actually displayed. No website changes were made by this research task.

## Acceptance and release

`renderer-cases.json` provides concrete semantic cases, including abstract labels, coauthors, original/reprint dates and the unchanged baseline. Implement meaningful UI checks for these rather than tests that only reproduce a field lookup.

After the rendering checks pass, accept the agreed delta against its exact baseline, archive 1.121, record claim decisions and append a production revision. That future acceptance may set the twelve recommended historical claims and their bibliographic assertions to accepted without changing the evidence check scopes. Update candidate-status coverage metadata to a partial accepted release; do not mark either field complete. If another production edit has landed, rebase and repeat preservation checks first.

Rebuild using the existing public allowlist. Keep all research packets, captures, preview files and unrelated workspace files outside deployed assets. A passed data preview is not a browser test or an authorization to deploy. OpenAlex remains paused.
