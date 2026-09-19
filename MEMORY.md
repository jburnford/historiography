# Project memory and visualization handoff

## Production import complete; website assigned to Fable — revision 1.119

User said “add it to the production graph,” then “Fable will rebuilt the website.” Eight full entries now in `historiography-1920-2000.json`: Scott, Davis, Hunt, Hall, Davidoff, Higginbotham, Smith and Daston, preserving people IDs. Totals: **124 nodes (73 groups/51 people), 761 teaching edges, 840 sources, 829 shared people**. Nine added teaching edges edge_753–761; prior records, rosters/strands, journal catalogue and snapshots preserved. Only eight people gain node_id. No new external authority/gender accepted; OpenAlex paused.

`claim_catalogue` production schema 1.0 uses vocabulary 0.2: seven first-class works, eighteen historical claims (17 accepted, Davis comparative biography provisional), nine authorship credits and eight presentation claims. Citation checks stay on joins. Shared coauthors and no-node participants survive. Exact work/concept endpoints and compound strands remain in claim_projection/target_strand. Davis edge_755 is visibly provisional; description scope never upgraded. Other research packets remain staging.

Acceptance and renderer handoff: `data/production-batches/promotions-01/README.md` and `acceptance.json`. Import `scripts/apply_promotion_batch.py`; audit `scripts/audit_promotion_import.py`; structural extension `scripts/validate_claim_catalogue.py`, called by normal graph validator. Twenty promotion_import/graph_validation/people_validation tests pass; exact reconstruction and preservation audit passes. Original graph: `drafts/historiography-1920-2000.v1.118.json`; browser bytes: `drafts/extension-browser-v1.118/`. Frozen staging tools requiring unchanged live production are historical: do not reset hashes or run their builders against current production. New audit checks pinned inputs against archives.

**Fable owns the website rebuild.** Initial site/app/core changes and generated docs from this turn were reverted after that instruction. Current website source/public assets remain at their pre-import state, checked against baseline hashes. Production data remains. No push/deployment performed. Use `audit_promotion_import.py --check-public` only after Fable rebuilds; otherwise use the data audit. Expose all eighteen work-specific relationships, coauthor credits and evidence scopes without broadening precise targets or hiding participants without nodes.

User asked about seven more people: **Himmelfarb, Joan Thirsk, Letitia Woods Brown, Lily Ross Taylor absent**; **Gerda Lerner** (`gerda_lerner`) in women/identity rosters, no node; **Barbara W. Tuchman** (`barbara_tuchman`) and **C. V. Wedgwood** (`cv_wedgwood`) already full nodes. Answered during import; those four additions and Lerner promotion were not performed. Retain as research leads alongside the 65-name cohort and eleven-field omissions.

## Eight concrete pre-2000 promotion drafts — 2026-09-18

Continued the representation response with `data/extension-2026/promotions-01/README.md`: Scott, Davis, Hunt, Hall, Davidoff, Higginbotham, Smith and Daston. Eight actual legacy-format node drafts preserve stable people IDs and every existing roster/strand context; no accepted QIDs or gender values added. Seven first-class works, eighteen historical proposals, nine authorship credits and eight presentation links (35 total claims). All `needs_review`; zero production imports. `scripts/build_promotion_batch.py` rebuilds offline; `scripts/validate_promotion_batch.py` checks packet/manifest/baselines and an in-memory node-only overlay. Nine focused tests in `tests/test_promotion_batch.py`.

Fresh checks: Scott 1986 pp. 1067–1068, Hunt 1989 introduction pp. 1–5, Higginbotham 1992 pp. 251–253, Smith 1999 introduction pp. 1–5, Daston/Galison 1992 complete scope paragraph p. 81 and opening p. 82. Fourteen historical claims passage-checked; three Family Fortunes claims use an indexed publisher prologue abstract, one Davis comparative-biography claim a Fulcrum description. Neither limited-access source is a full body-text check. Family Fortunes original 1987 differs from later reissues/new introductions; Davis original 1995 differs from listed 1997 manifestation. Selected PDF pages/OCR and raw web captures are durable; full downloaded PDFs remain temporary. Download hashes and original-page mappings in raw/pdf-observations.json. Local date 18 September, assembly UTC timestamp 19 September; no research-cutoff expansion implied.

Shared work IDs preserve Hall/Davidoff and Daston/Galison coauthorship. Rosaldo, Hine and Smith-Rosenberg have scoped claims without teaching-node promotion. Collins is a local candidate named by Smith, no accepted external identity or reconciled cited work. Higginbotham’s critique of insufficient racial analysis is not automatically a critique of Scott/Butler merely because she cites them. Preserve legacy edge_313 and edge_314; no new Scott–Thompson personal edge without its own passage. Historical claims target works or precise concepts/compound strands, never unqualified umbrella entries. Node-only overlay intentionally does not generate legacy edges from these claims.

Next: `remaining-checks.json` identifies Davis body text, original/aligned Family Fortunes passages, Scott–Thompson attribution, Hunt’s political-culture work, Collins identity/work reconciliation, and broader balance. Continue other pre-2000 omissions (including non-European contributions) alongside the 2026 breadth extension; these eight accessible English-language interventions do not complete the 65-name cohort or fix eleven zero-woman fields. Barbara Fields is a fresh lead from Higginbotham p. 253. OpenAlex stays paused; production graph/browser baseline unchanged. Frozen contracts/prior packet manifests were not rewritten.

Verification: 54 tests pass (35 promotion/reproduction/breadth/gender plus 19 ontology tests run with discovery from the ontology directory); all four research validators pass. The first combined module invocation could not import ontology's local `validate` module; corrected discovery invocation passes without changing the frozen tests. Offline rebuild is byte-identical, selected PDFs parse cleanly, and production/browser hashes match their baseline.

## Fable representation packet reproduced; pre-2000 omissions prioritized — 2026-09-18

User supplied a detailed list of women missing full nodes or absent entirely, followed by Fable 5.1's audit and raw inputs, now preserved at `data/extension-2026/representation-audit-2026-09-18/README.md`. Read that original README **together with `REPRODUCTION.md`**, which records independently verified corrections. Source scratchpad was `/tmp/claude-1000/-home-jic823-historiography/ada2587b-0dfc-4ba3-881e-51021303ca19/scratchpad/`; needed raw files are now in the repository packet. Original supplied files remain unchanged. Prioritize existing pre-2000 visibility/relationship omissions alongside newer-field coverage; do not merely add women to gender history or use appearance counts as importance.

`scripts/reproduce_representation_audit.py` replays all 829 rows exactly from saved MCP/QLever gender observations and graph/ranking inputs. Reproduces provisional 162 women / 493 men / 174 unknown-or-multiple; 13/30 full nodes (only 12/30 in accepted-QID subset), 313/808/248 topic occurrences, 97 edges touching provisionally woman-classified nodes, eleven fields with no provisionally classified women, 10 women among 118 externally reviewed and 97 among the visibility thousand. **These are provisional name-match/provider tallies, not accepted demographics or rigorous lower bounds.** Forty-two accepted node-QIDs and the unreviewed roster-QID map are checked against original repository inputs.

Corrections: three women, not one, in the reviewed priority band—Hannah Arendt, Drew Gilpin Faust, Nina Garsoyan—confirmed in reviewed-all and reviewed-priority. Saved `top1000_nonmale.csv` contains 115 male records because gender URIs survived its filter; sixth-batch TSV has English labels on all 173 rows. Corrected 97-row export is in `reproduction/`. Butler's combined female/non-binary label result comes from four DIFFERENT QIDs; philosopher Q219368's returned row is non-binary, the female rows are namesakes. Do not repeat the original claim that these are multiple values on the philosopher's item. Do not infer full statement history from this query. Original README's career-period generalization was not reproduced.

`scripts/audit_representation_visibility.py` exports the user's 65-name cohort with exact current roster/strand contexts, works, inherited source records, direct edges and separately flagged source-overlap leads. Forty-four local name/explicit-alias matches: 43 lack full nodes, Frances A. Yates is the existing-node control. Twenty-one no-label-match leads are distinct from verified absences. Louise Tilly requires Louise A. Tilly alias. Scott has eight roster entries and seven strand-entry appearances; people already have shared identity/profile records, not text-only presence. `edge_314` already encodes gender → Thompson critique at an umbrella endpoint. Individual attribution remains missing; preserve productive inheritance and criticism separately, without automatically giving every feminist roster member the same critique. No new QID, node or edge accepted.

Earlier work this turn is saved in `data/extension-2026/recovery-02/`: selected Leon/Gallon/Rutherford/disability/youth passages, Putnam abstract, raw failures and a contract-0.2 packet with eleven work referents, eight scoped proposals and one deferred task. One work ID reuses breadth-01. AHR authors explicitly acknowledge Leon during their 2020 revision. Rutherford credits a 2019 Cleall talk while explicitly not having read the 2022 book—never encode that as the book influencing her earlier work. New claims remain needs_review; demographic counts were not inferred from these authors. See recovery README for scope and bibliography leads not yet parsed.

Next: contribution-based promotion review across cultural/gender, Black, Indigenous, postcolonial, science, economic and other histories; authority/alias disambiguation; use preserved roster evidence to form citation-specific claims independently of whether a person receives a teaching node. Continue newer-field recovery after balancing pre-2000 omissions. The visibility ranking is not a baseline or calibration population. OpenAlex stays paused. Production graph and browser baselines unchanged.

Verification: 45 relevant tests (eight new reproduction/recovery tests, twelve breadth, six gender and nineteen ontology), plus all three existing research validators pass. New manifests pin supplied raw inputs and derived outputs; no supplied audit input was overwritten. Existing accepted Yates authority state is preserved separately from unaccepted new alias/name leads.

## First balanced breadth batch and representation safeguard — 2026-09-18

User approved scaling beyond the seven-work gender pilot. Completed a first **partial** breadth packet: `data/extension-2026/breadth-01/REPORT.md`, twelve field dossiers, 24 selected survey/programme works (22 new local work proposals plus two reused knowledge-pilot IDs), 23 scoped claims, all `needs_review`. Nine sources have selected passages checked, five abstracts, seven publisher descriptions, two indexed excerpts, and one metadata-only source (Erll; no argument claim). Zero fully reviewed fields or production imports. Field selection: gender, disability, borderlands, digital, web, emotions, senses, knowledge, trans, childhood/youth, memory, transnational. Childhood and youth remain separate candidate identities; youth coverage is a gap. These sources do not establish complete coverage to 2026.

**New user constraint:** User reports Astra and Fable 5.1 top-fifty historians lists contained seven and six women. Treat this as a warning about selection/training bias, not a verified demographic benchmark or proof about training-corpus composition. `REPRESENTATION-REVIEW.md` requires source-grounded audits of discovery, selection and substantive connections across every field, including full nodes versus roster mentions. Women must not be confined to gender history. Model recall, Wikipedia visibility, citation/catalogue counts and degree cannot establish importance. Do not infer gender from names. Every new dossier has a specific representation question; `representation-audit.json` remains pending and blocks production readiness. The 37 harvested author/editor credits are unresolved observations, not distinct people or demographic counts. Digital bibliography recovery lead: Sharon Leon’s chapter on the Great Man narrative; read it before deriving claims.

Reusable offline builder `scripts/build_breadth_batch.py` produces 519 discovery occurrences: 276 raw Crossref references, 154 note bundles, 89 captured bibliography lines. These are not 519 distinct or reviewed works; notes include commentary, ibid and software. Four sources supply all Crossref references (180 from knowledge), and extracted reference leads exist for only five of the twelve fields. `review-queue.json` allocates up to twenty occurrences per field and records seven missing bibliographies, plus the representation-recovery lead. Captures are partial web-tool extracts; parsed bibliography coverage is partial. Fourteen selected DOI metadata requests succeeded; `scripts/harvest_breadth_metadata.py` caches responses, verifies DOI, throttles uncached requests. Preserve raw provider references and dates; no automatic authority merges. Rothberg’s Crossref platform date is 2020, not a replacement for the 2009 work; childhood/education is 2023 despite 2022 in its DOI.

`ontology/contract-v0.2.json` and `ontology/validate_research.py` add scoped historical-intervention predicates for staging; frozen 0.1 files and gender pilot are unchanged. `scripts/bridge_extension_research.py` losslessly adapts the two prior packets to 18 historical claims plus two discovery tasks, retaining all twenty original records and citation joins. Nineteen consulted witnesses become source records, not fictional issued publications. Person IDs and compound strand addresses survive. The earlier gender crosswalk remains a historical audit; the separate bridge now resolves its format gap without accepting its claims. See `ontology/RESEARCH-0.2.md`.

Validation: new preservation/semantic tests, original ontology tests and gender tests; all three research validators check staging/provenance/baselines. Main graph remains revision 1.118, 116 nodes, 752 edges; browser assets unchanged. Next: targeted representation recovery; independent regional/language surveys and missing bibliographies; reference parsing/relevance review, author/work/edition reconciliation, body-text and reception checks, and chronological coverage of 2001–2019 and 2020–2026. Original LOD precision/provenance issues remain unresolved. OpenAlex remains paused. No production migration or deployment authorized by this batch.

## Gender-history / LOD integration batch — 2026-09-18

User approved the proposed small gender-history integration batch after the status discussion. Completed a bounded staging packet and report at `data/extension-2026/gender-integration/REPORT.md`; broader bulk mining and production migration were not resumed. This supersedes the earlier blanket pause for this specific batch. OpenAlex remains paused.

`batch.json` uses the imported `ontology/contract.json` 0.1 directly and remains `fixture_only: true`, `staging_only`, with zero production imports. Five people (three reused legacy IDs; Ghosh/Najmabadi new local candidates), seven works, eight publications, two Stryker versions, 37 proposed claims including seven interpretive proposals. All claims and four external authority mappings remain `needs_review`. Seven Scott/Davis LOD records have role/type review notes: three publisher-corroborated, four saved-catalogue-only. Exact manifestation joins are pending. Davis is an identity/publication control, not an automatically added gender connection.

Research includes Scott 2010 abstract and selected Sex and Secularism introduction pp. 3–7; Ghosh's 2022 author retrospective on her 2006 book plus Cornell profile; Najmabadi publisher description; Stryker author/publisher edition metadata. Stryker's author page confirms February 2026 third-edition release, distinguishing it from the 2008 work and 2017 edition. Preserve Duke's December 2013 release for Professing Selves separately from JSTOR's 2014 copyright; Cambridge 2014 online frontmatter does not redate Ghosh's 2006 work. See report for source access limits and regional gaps. This is not a complete field review.

`schema-crosswalk.json` audits all 19 works, 19 consulted witnesses and 20 claims/citation joins from the two unchanged older packets. **Not a completed conversion:** consulted HTML/PDF witnesses need separation from issued publications; contract 0.1 lacks exact critique/revision/contribution/qualification/programme predicates. Preserve these claims and compound strand addresses rather than coercing them into research_connection. Scott's explicit Taylor disagreement and Foucault/Asad method references provide further predicate-design cases, not accepted edges.

Updated the gender ledger bins to `partial_pilot_review`, leaving overall `pending` and zero fully reviewed topics. Added `data/extension-2026/README.md` and revised `EXTENSION-2026-PLAN.md` to prioritize balanced breadth, common ontology and the missing 2001–2019 span. Corpus volume/degree must not make economic history appear more important than gender or other fields. Next: claim-vocabulary design against preserved examples, precision-aware authority reconciliation, fuller gender survey/reception and underdeveloped borderlands/disability/digital-web batches before further economic depth.

Validation: `scripts/validate_gender_integration.py` checks common contract, evidence hashes/scopes, legacy IDs, preserved catalogue records, full older-packet mapping coverage and baseline graph/browser hashes; six new semantic/preservation tests and 19 existing ontology tests pass. Original extension validator passes unchanged (19 works, 20 claims; excludes the separately typed new packet). Integration manifest pins artifacts, code, common contract and consulted LOD exports; source captures are web-tool responses, not raw HTML. Main graph still revision 1.118 / 116 nodes / 752 edges. Known original LOD provenance/date-precision findings remain unfixed; full raw-cache replay still unavailable from this checkout.

## Borderlands history added to discovery queue — 2026-09-18

User added borderland/borderlands history as another field to investigate. Added **Borderlands history** to `FIELD-DISCOVERY-2026.md` and the structured field-candidate ledger (`borderlands_history`). Current graph has no dedicated entry or explicitly named borderlands strand. Research should examine earlier roots and post-2000 developments, regional differences, and relationships to frontier, transnational, spatial, imperial and Indigenous histories without treating these as equivalent. Queue now contains 37 candidates: 30 user-seeded/contextual rows and 7 research discoveries. This is a queue update only; broader research remains paused and the graph is unchanged.

## GitHub LOD sync and paused extension handoff — 2026-09-18

User paused research, then requested pulling additional LOD work from their other machine before continuing. Fetched and fast-forwarded `main` from `116a506` to `e390323` (Add ontology prototype and reviewed LOD pilot harvest); HEAD and origin/main now agree. Both additive MEMORY handoffs were preserved. All 1,363 other dirty/untracked local files were hash-checked unchanged. A safety copy of the prior local MEMORY remains in stash `codex-before-lod-sync-2026-09-18`; merged text is already restored, so do not blindly apply that stash again. Recovery files are in `/tmp/historiography-github-sync-e215o_5a/`.

New `ontology/` is a separate, more developed contract/fixture proposal, not a production migration. Read it before extending the local research prototype; reconcile the two designs rather than building competing production schemas. The incoming LOD harvest, scope, identity flags and independent-review findings are preserved below. On this machine, ontology validation passes (5 cases, 21 claims), all 19 ontology tests and 10 LOD tests pass, and the local extension validator still reports zero errors. Full LOD cache replay was not run; raw endpoint caches are excluded from Git.

**Latest editorial constraint:** The user's capitalism workspace is unusually deep because they are researching it exhaustively. Do not let its source/node/edge abundance make economic history appear more important than gender history or other fields. Keep detailed discovery in staging, give under-researched fields comparable attention in the first breadth pass, and keep corpus volume/graph degree separate from importance and overview prominence. This direction supersedes any plan that would keep deepening the economic-history pilots before balancing the broader map. It has been recorded here; presentation changes and the corresponding detailed plan update remain pending.

**Local work saved before pause:** `data/extension-2026/` holds the 73-topic ledger, 36 field candidates (29 initial seeds plus 7 discoveries), baseline hashes, web evidence captures, two research-prototype packets (19 work records, 20 proposed claims and scoped citation checks, including one metadata-only unresolved programme lead), and read-only capitalism mining outputs. `scripts/mine_capitalism_workspace.py` inventoried 305 catalogue entries, 89 registered sources, 188 reading-list entries and 759 topic-search hits from `/home/jic823/capitalism`; the source inputs were hash-checked unchanged. Its inherited 18,691 work and 20,849 citation records include parsing defects and are not accepted KG content. Local selected readings also identify the 2020 Broadberry preprint despite its catalogue's 2021 journal label. `scripts/validate_extension_research.py` passes. No topic is yet fully reviewed through 2026 and no production addition has been made. Readable pilot reports, a research README/manifest and balancing-policy updates were not completed before the pause. No further research resumed during this sync. OpenAlex remains paused.

## New-field discovery is a core extension track — 2026-09-18

User corrected the initial 2026 plan: updating existing entries is insufficient; actively identify additional fields and programmes. [FIELD-DISCOVERY-2026.md](FIELD-DISCOVERY-2026.md) records all supplied examples in 29 separately assessable rows, including contextual computational history/digital humanities, current graph representation, research decisions, checked source leads, an open-ended discovery procedure and dossier requirements. This is a planning queue, not accepted additions. [EXTENSION-2026-PLAN.md](EXTENSION-2026-PLAN.md) now gives discovery equal priority with existing-topic review, adds a fourth history-of-knowledge pilot, distinguishes digital/web/computational history, and requires an outcome for every seed plus discovery beyond the list. Earlier three-pilot/primarily-existing-fields wording below is superseded.

Important baseline distinctions: `global` and `memory` are full entries; `spatialhistory/historical_gis`, `queer/trans_intervention`, childhood strands in `demography`, and Great Divergence strands in `economic`/`global` already exist. Their presence does not settle whether standalone entries or richer strands are needed. Do not call these wholly absent. Verified source leads include Burke 2000, Agnotology 2008, History of Humanities 2016, KNOW 2017–2024 (publisher confirms cessation), Journal for the History of Knowledge 2020, Information: A Historical Companion 2021, and Memory Studies January 2008. Venue/work dates do not establish field origins. Main graph/schema/browser assets unchanged; OpenAlex remains paused.

## Extension through 2026: plan — 2026-09-18

User requested a plan to move the KG forward to 2026 and asked about Wikipedia. [EXTENSION-2026-PLAN.md](EXTENSION-2026-PLAN.md) proposes field-by-field review of all 73 existing topics, Wikipedia as a discovery/reference source, scholarly evidence for accepted interpretive claims, minimal work/claim/citation schema foundations, and three pilots (Great Divergence, Tackett/Chinese history, digital/computational history). Recommended first implementation slice: coverage ledger plus Great Divergence evidence packet, then schema support tested on that packet. Cutoff is actual research date (currently 18 September 2026), not a claim to cover the whole unfinished year. **Plan only; authoritative data/schema/browser assets unchanged.** OpenAlex remains paused. Huang's 2023 article was identified through its publisher record; the supplied Windows PDF was not read.

Current-code correction to older handoffs: `site/field.mjs` already draws ongoing fields to the coverage wall, handles undated earlier roots and supports death/posthumous reception. Do not repeat older assertions that those rendering changes are wholly unimplemented. A future extension still needs semantic chronology and hard-coded-2000/catalogue-dependency audits. Preserve existing uncommitted candidate-review and ontology work.

## Historian relevance review and 1940 filter — 2026-09-17

**Latest user correction:** The first ranking selected famous people more than key historians. User supports an LLM review layer for mixed cases such as Churchill and H. G. Wells and an exclusion filter for people who died before 1940. User explicitly identifies **Hannah Arendt as a likely node for her contribution to the totalitarianism debate**. Therefore assess **contribution to historiographical fields, methods and debates**, including philosophers and other conceptual contributors; do not substitute a professional-historian-only rule. Arendt is absent from current nodes and shared people. Recorded as priority node candidate; graph addition not implemented during candidate review.

**Completed:** Reviewed original first 100 individually using captured biographies/selected work passages, plus 18 targeted low-ranked candidates. [Current reviewed list](data/wikidata/historians-qlever-2026-09-17/ranking/editorial-review/REVIEWED-LIST.md), [documentation](data/wikidata/historians-qlever-2026-09-17/ranking/editorial-review/README.md), `decisions.tsv`, role/priority/field/contribution/reason/source CSVs, evidence captures, reusable `REVIEW-PROMPT.md` and manifest. Review is by this assistant (LLM editorial judgment), not an external model call or primary-passage edge verification. Original Wikipedia-weighted score now only orders within editorial bands. Old ranking/output hashes remain preserved and its README points to the replacement.

**Results:** 118 reviewed; after death filtering, **42 priority** candidates, **29 further substantive**, **13 contextual/deferred**, and **34 earlier-root** records. Arendt is priority conceptual contributor; Churchill/Wells are retained historical writers in the second band. Bernal, Bauman, Lotman and other nonhistorian contributors survive through named historical contributions. Targeted recoveries include Ogot, Sarkar, Sastri, Laroui, Djaït, Agoncillo, Ileto, Bean and Tackett. Tackett's main work and named Applebaum books need the planned post-2000 extension. No implication that remaining candidates have been reviewed.

**Death rule:** Starting from the 116,441 prior addition candidates, exclude usable non-deprecated deaths strictly before 1940; deaths in 1940 pass. **8,275 excluded**, **18 uncertain death cases**, **108,148 in default view** (41,400 usable deaths in/after 1940; 66,748 with no recorded death). Missing death is not proof of being alive after 1940. Conflicts across cutoff, coarse dates, unsupported calendars, uncertainty and Julian boundary dates stay review cases. All original candidates and all-period existing-graph match leads preserved; no existing graph person removed. **108,064** default-view candidates remain explicitly unreviewed.

Reproducer `scripts/build_reviewed_historian_list.py` has configurable `--death-cutoff` and `--output`; tests `tests/test_reviewed_historian_list.py` cover cutoff boundaries, missing/deprecated/conflicting dates, uncertainty and relevance-before-visibility ordering. Current graph, IDs, other inventories and browser assets untouched. OpenAlex still paused; Fable feedback and timeline-rendering issues still pending.

## Ranked historian discovery inventory — 2026-09-17

**Latest user direction:** Use all four proposed prominence signals to create a ranked list, with Wikipedia articles the most important because they can help research field edges. Built a separate, provisional discovery ranking under [data/wikidata/historians-qlever-2026-09-17/ranking/README.md](data/wikidata/historians-qlever-2026-09-17/ranking/README.md). Weights: Wikipedia 65, history/humanities recognition 15, reference-work coverage 10, notable historical-work metadata 10. Logarithmic diminishing returns; counts and each component visible. No accepted identities, graph additions or field edges; OpenAlex remains paused.

**Outputs:** `TOP-100.md`, `ranked-top-1000.csv`, `ranked-candidates.csv` (all **116,441** dated potential additions), compressed all-period/history-supported/date-review rankings, `ranked-existing-match-leads.csv`, all-language `candidate-wikipedia-articles.csv`, compressed per-person evidence, explicit scored/unscored signal catalogue and hash manifest. **63,880** addition candidates have Wikipedia sitelinks; **9,119** have at least five editions and **2,560** at least ten. Among 363 date-qualified Wikidata name-match leads, 333 have at least one edition, 252 at least five and 156 at least ten. These are unverified QID matches, not a verified historian calibration set. Exact latest component coverage/counts: `ranking/summary.json`.

**Limits and review:** Source/work/award relevance is primarily a provisional metadata screen, not primary-passage verification or demonstrated work influence. Ordinary memberships, generic honours, primary police records and explicit fiction are not credited. Broad science-academy memberships were removed after exposing celebrity inflation; historical-science roles can still legitimately score. The ranking can still favor people primarily famous outside history. Each row has a history-relevance review flag; all original candidates remain. Sparse/non-English metadata can reduce scores. Tackett has no Wikipedia sitelink in this capture but a work signal; Bean has seven editions. Low ranks do not establish absence of importance. Name-only atlas matching can leave false new candidates, and no identity match is accepted.

**Retrieval/reproduction:** QLever supplied 78,871 Wikipedia-linked items / 258,800 articles across the full queried occupation population, six direct-property inventories, and object/type/subject metadata. Ranking traits use truthy properties; occupation membership retains normal/preferred statements as before. The live index changed P1343 during offset paging, so its 37,177 rows were recaptured in one complete unpaginated response; old pages are diagnostic only. One incidental new live-index item outside the saved population is excluded. Successful raw JSON compressed with byte-preservation checks. Offline scripts: `scripts/build_historian_signal_catalog.py`, `scripts/rank_wikidata_historians.py`; focused tests: `tests/test_historian_ranking.py`. Raw/count/duplicate/membership validation runs inside export; output hashes and unchanged curated atlas checked. Prior inventory and browser assets preserved.

## Wikidata historian inventory — 2026-09-17

**Latest user direction:** Match against everyone already in the atlas regardless of dates, but focus potential **additions on historians living in or after 1900**. The user rejected Q17489339 (historian of Modern Age) because it concerns period studied. Added birth/death statement extraction and conservative lifespan screening: **116,804 date-qualified; 13,683 died before 1900; 22,118 date-review cases** among the 152,605 non-deprecated occupation items. The focused new-candidate file has **116,441** records after setting aside 363 Wikidata items with unreviewed existing-person name matches. Missing deaths are not treated as evidence of life; coarse, conflicting and boundary dates remain review cases. This does not establish scholarly activity after 1900 or authorize extending/adding to the atlas.

Date artifacts: `historians-with-dates.csv`, `historians-living-1900-onward.csv`, **`new-candidates-1900-onward.csv`**, `atlas-matches-all-periods.csv`, `date-review.csv`, `died-before-1900.csv`, compressed evidence JSONL and `date-filter-manifest.json` under the QLever directory linked below. `DATE-FILTER.md` explains the rules. `scripts/filter_wikidata_historians.py` reproduces the screen; eleven focused tests pass. **221,020 date statements** reproduce independent per-property counts; all output hashes and unchanged atlas fingerprint checked. Tackett and Bean pass the screen; Herodotus remains in the full inventory. All 829 atlas people were compared by selected labels; 379 have possible matches and 450 remain unmatched by that narrow method. No identity matches have been accepted.

The user requested mining everyone with occupation **P106=Q201788 (historian)**, then explicitly instructed switching to **QLever** when WDQS failed. Completed the exact-occupation extraction through `https://qlever.dev/api/wikidata`: **152,605 non-deprecated items**, **35 deprecated-only**, **152,640 total items / 152,650 statements**. Standard truthy query gives 152,522; 83 additional normal-rank occupation matches are hidden by preferred ranks. This is a separate discovery inventory across all periods, not an atlas expansion. No subclass expansion or human-instance restriction. OpenAlex remains paused.

Artifacts and reproduction: [data/wikidata/historians-qlever-2026-09-17/README.md](data/wikidata/historians-qlever-2026-09-17/README.md), CSV, compressed JSONL, exact queries, raw paginated responses, counts and manifest; offline exporter `scripts/export_wikidata_historians.py`. Eight 20,000-row pages (last partial) reconcile with independent aggregate and rank counts. Every item has a label after en/mul/other-language fallback; descriptions may be absent. Name comparison yields **394 unreviewed candidate pairs for 379 of 829 atlas people**; 450 have no narrow label match, which does not mean absence from Wikidata. Tackett Q107085771, Herodotus Q26825 and Charles Bean Q5075487 are present. No authority identities assigned or historical claims accepted.

QLever describes its August-dump-based index as **updated LIVE**; dump dates must not be reported as its latest represented edit. Saved extraction files are fixed, but the endpoint requests are not a transactional snapshot. Earlier WDQS results differ by two items and remain separate incomplete diagnostics under `data/wikidata/historians-2026-09-17/`. Successful HTTP status was insufficient: unpaged results could truncate during export. Only fully parsed, counted pages feed the final exporter. All authoritative graph/catalogue data, existing snapshots and browser assets remain unchanged.

**Earlier discussion still pending:** Fable's ontology feedback remains unimplemented. The user also identified misleading Annales and military-history timeline spans: `parseSpan` turns Annales's 1929 onward label into a short solid 1929 mark plus pale continuation, and military history's selected Howard 1961/Keegan 1976 milestones into an apparent 1961 beginning. Neither is a defensible field boundary. These were diagnosed, not repaired; official military historiography (including Bean/Edmonds) is an additional substantive coverage lead. User's current task is the Wikidata candidate inventory, not deployment or a silent chronology migration.

## Fable ontology review — 2026-09-17

The user supplied six structural concerns and explicitly attributed them to **Fable**, who had reviewed Astra’s explanation rather than the JSON. Checked the authoritative data, validators, build and renderer; findings are in [feedback/fable-ontology-review.md](feedback/fable-ontology-review.md). This was a review/documentation task, not authorization for a schema migration. Historical revision remains 1.118; OpenAlex remains paused.

Most concerns hold with corrections: Thompson’s Moral Economy already has a shared source ID across four rosters, but no normalized work/edition identity. Wehler’s critique already exists as `edge_705` (`bielefeld → micro`); the structural problem is substituting broad endpoints for named actors/strands, not absence of that critique. There are 89 critic selections without `edge_id`, not necessarily 89 missing claims. Source verification is explicitly scoped in prose but not attached to source–claim joins. Local strand IDs can support compound addresses without replacement. Node date fields are synchronized with `date_span`, but title events are not reconciled; three accepted successor titles render “Publication dates unverified.” Historical changes have snapshots/manifests, although no uniform claim lifecycle. Candidate state is mixed into `publication_role`, not `entry_kind`.

Additional confirmed build issue: slimming retains all title relations while dropping some dependencies; seven relations lack endpoints and one source is missing in the projected catalogue. Resolve chronology before slimming or include its dependencies when implementing a repair. No application/data changes made. Baseline validator: zero errors/four unchanged warnings. In-memory semantic-role and projection probes documented in the report. The entry-kind proposal now links the review; work identities, explicit claim participants and citation evidence should be designed together before a broader migration.

## Ontology documentation handoff — 2026-09-17

**Latest user direction:** Record the explanatory ontology walkthrough for future use and **propose** a fix for `entry_kind: group`. Saved [ONTOLOGY.md](ONTOLOGY.md) with examples and Mermaid diagrams, and [ONTOLOGY-PROPOSAL.md](ONTOLOGY-PROPOSAL.md) with a concrete migration design. This was a documentation task; no schema or data migration was requested or performed. OpenAlex remains paused.

**Recommendation, not yet adopted:** Replace historical `group` with seven explicit machine-readable kinds derived from the existing `entry_type` categories; retain `person` and existing human-readable labels. Derive broad People/Topics browsing separately. Proposed historical schema 1.5 needs version-aware validators, journal target checks, consumer updates, and a preservation audit. Do not restrict debate-venue targets to debate entries: existing named exchanges also target SSK and Nationalism studies. Keep journal kinds, identities, claims, rosters, strands, sources, chronology, and immutable batches intact. Read the proposal before any implementation.

**Implementation-state correction:** Contrary to older handoffs and one sentence in the original walkthrough, current `site/field.mjs` already renders a projection of journals with accepted venue edges. `scripts/build_site.py` includes that module and publishes a reduced journal catalogue; its current allowlist has seven assets. The full repository catalogue remains authoritative. Do not use older “journal renderer absent,” “six assets,” or byte-identical-full-public-graph statements as descriptions of current frontend code. No frontend change or deployment was performed for this documentation task.

The data handoff below remains the revision 1.118 baseline; its frontend statements are historical where superseded above.

## First LOD mining harvest completed (2026-09-18 UTC)

User authorized starting LOD mining. `lod-mining-plan.json`, `scripts/mine_lod.py`, and `scripts/summarize_lod.py` now implement a bounded, reproducible Wikidata QLever → IdRef/Sudoc staging harvest. Completed snapshot: `data/lod-mining/2026-09-18-pilot-complete/`; the earlier `2026-09-18-pilot/` is incomplete after filesystem read timeouts. Successful retrieval used a temporary local cache, then copied the full snapshot. Raw caches are Git-ignored and included in the user-facing archive.

Results: 777 field/occupation discovery candidates, 819 people including inherited atlas matches and explicit controls; 90 sampled people, 91 IdRef identifiers; 1,903 bibliographic resources, 87 with structured years in 2020–2026, 82 with subject links, 218 subject identifiers; 15,028 deduplicated source observations from 59 successful queries. All are unreviewed staging. Three identity-link flags affect two people: Linda Gale Jones has two IdRef IDs; David Brody’s queried authority label was missing. No birth-year conflict was detected, which does not establish identity. Scott’s field discovery returned labour history only, but her explicit control recovered three recent records; Davis recovered four. Series/editorial-board records, translations and reissues are included, so these are not counts of new works or author output.

Ten targeted miner tests passed. An offline rebuild made zero network requests and reproduced nine data exports byte-for-byte. The audit verified all source hashes, row caps, observation provenance and protected input hashes. The authoritative atlas, accepted identities, site assets and OpenAlex remain unchanged. Next: review identity flags, distinguish bibliographic resource types and work/edition relationships, then map subjects with explicit evidence before accepting any person-to-field claim or expanding the sample. The requested 2020–2026 window concerns catalogue years; the 2001–2019 gap remains explicit. The ontology-first note below records the preceding design stage.

Independent review: `data/lod-mining/2026-09-18-pilot-complete/INDEPENDENT-REVIEW.md` independently confirmed all 15,028 statements against the cached sources. Outstanding findings: 25 subject-label observations omit additional supporting request IDs; birth comparison lacks Wikidata precision; thesis-corpus exclusion does not exclude thesis-like content within Sudoc. These remain documented and unfixed in this snapshot. Use for discovery/review, not accepted specialisms, new-work counts or field rankings.

## Current direction: ontology-first linked-data expansion (2026-09-17)

The user wants QLever/Wikidata and linked author/library data to expand the KG, with a contemporary discovery window of 2020–2026. They questioned the ontology before scaling and approved formalizing it against five stress cases. `ontology/README.md` now proposes the extension, with `contract.json`, `cases.json`, scoped evidence snapshots, a standard-library validator and negative-case tests. The cases cover Scott's missing gender classification, Davis's mixed field/period values, Clifford's environmental-history field versus book subjects, Ginzburg's translated 2026 reissue, and Hilton's Annales interlocutor status without inferred membership. This is a fixture-only design prototype, not an accepted import, a complete ontology or a migration. Preserve the authoritative atlas and all existing IDs/qualifications. In particular, the local `gender` entry is a teaching umbrella, not an exact match for gender history or gender studies. No bulk ingest, production export, site rebuild or OpenAlex restart occurred. Historical dataset counts and the through-2000 boundary below are unchanged. Next work is the mapping/identity/version/claim-history design described in the proposal, before any large import; the 2001–2019 gap remains explicit under the requested discovery window.

Run `python3 ontology/validate.py` and `python3 -m unittest discover -s ontology -p 'test_*.py' -v`. The prototype blocks production export of its fixtures; passed checks certify model constraints, not scholarly truth. Source-verification scopes are inherited unchanged, except the explicitly documented publisher metadata check.

## Earlier atlas handoff (unchanged data state)

Updated **2026-09-16**, after four user-requested field entries (**revision 1.118; historical schema 1.4; journal schema 1.3**).

**Latest user direction:** Add Spatial History/Historical Geography, Intellectual History, Labour History and Ethnohistory. All four now have dedicated sourced entries. Keep OpenAlex paused and coverage through 2000; continue substantive evidence and regional distinctions. No frontend design or deployment.

**Current historical data:** **116 nodes / 752 edges / 833 sources / 829 shared people**, including **73 groups / 43 individual entries / 731 internal approaches / 1,309 contextual person selections**. New IDs: `spatialhistory`, `intellectualhistory`, `labourhistory`, `ethnohistory`. Added 28 approaches, 56 selections, 18 shared identities, 29 map connections and 14 sources. All earlier historical records remain exactly preserved. Relationships: 62 influences, 471 contributions, 121 critiques, 98 comparisons. Source statuses: 719 supporting-page checks, 78 metadata checks, nine not checked, 27 unrecorded; these are scoped checks, not blanket historical verification.

**Key distinctions:** Historical geography predates GIS; the 1994–1999 GBHGIS phase supplies a pre-2000 digital example. Intellectual history extends beyond Cambridge contextualism and includes Lovejoy, publishing/circulation, and Maruyama with Hane’s translation credit. Labour history covers institutions, class/culture, gender/households, colonial categories, workers’ testimony and military labour. Ethnohistory includes commissioned claims research, documentary criticism, Nahua and Andean programmes and qualified Indigenous interlocutors; it is not synonymous with Indigenous authority. The Webbs, Harley, Lurie and Andean volume have bounded primary readings with exact limits. Existing source scopes are unchanged.

**Journals unchanged:** 1,638 candidate/title records, 140 subjects, 798 library profiles, 808 records with ISSNs and 566 starts. 2,006 active classifications (1,322 checked / 684 provisional); 864 checked-classified, 442 provisional-only and 332 unclassified candidates. **54 venue edges: 42 principal / nine founding / three debate**. Principal links reach 29 fields; all venue types reach **32 of 73 fields**. Eleven title relations. The new 73-field ledger carries the prior 69 rows unchanged and adds unaccepted leads for the four targets. Existing Ethnohistory→Indigenous history and Le Mouvement social→social history edges retain their qualifications; no automatic retargeting or duplication.

**Next:** These are substantive initial entries, not complete global coverage. Follow the four-field report’s primary-reading and regional gaps, alongside the public/medical/urban follow-ups from 1.117. Review dated journal roles against the new targets before accepting links. The original first pass covers 109 baseline entries; the older second pass still has 48 outcomes plus five pre-capture resolutions and 187 pending questions. These additions do not resolve unrelated frozen questions. No broad OpenAlex/library restart.

**Artifacts / validation:** `feedback/four-fields-v1.118.md`, exact `-additions.json`, `-validation.json`, `feedback/journals/principal-venues-v1.118-review.json`; snapshot `drafts/historiography-1920-2000.v1.117.json`. Research PDF/hash manifest under `data/field-research/v1.118/`, outside browser assets. Current summary and supplemental pass-log entries updated. Run `python3 scripts/build_site.py` and `python3 scripts/audit_four_fields.py`; older audits target older revisions. 62 Python and ten JavaScript tests pass; zero structural errors/four unchanged warnings. Exact earlier records, unchanged/reproducible catalogue, 73-field ledger, PDF hash and six asset bytes checked. Existing renderer loads all four fields; journal renderer still absent. No browser review or deployment.

## Historical handoff through revision 1.117 (superseded where noted above)

Updated **2026-09-16**, after dedicated public, medical/health and urban history entries (**revision 1.117; historical schema 1.4; journal schema 1.3**).

**Latest user direction:** Work on the three strongest atlas gaps: public, medical and urban history. This authorizes substantive historical entries and connections, extending the earlier journal-only work. Completed all three as qualified enduring fields. OpenAlex stays paused. Continue quality through sourced programmes, internal differences and specific connections; do not turn journal launch dates into field origins or venue counts into importance rankings.

**Current historical data:** **112 nodes / 723 edges / 819 sources / 811 shared people**, including **69 group entries / 43 individual entries / 703 approaches**. New IDs: `publichistory`, `medicalhistory`, `urbanhistory`. Added 18 approaches, 23 contextual people selections using 22 people (14 new shared identities), 15 map edges and 14 sources. Earlier historical records remain byte-equivalent as JSON objects. Reused existing people; medical historian `dorothy_porter_medical` is distinct from `dorothy_porter_wesley`.

**Journal data:** **1,638 periodical/title candidates**, 140 subjects, 798 library profiles, 808 with ISSNs, 566 starts (545 catalogued-title starts). Active classifications unchanged: 2,006 (1,322 checked / 684 provisional), 864 checked-classified, 442 provisional-only, 332 unclassified. **54 venue edges: 42 principal / nine founding / three debate**, reaching 32 of 69 fields; principal selections reach 29 fields through 36 title records. Eleven title relations. New principal intervals: The Public Historian→public1978–2000; Social History of Medicine→medical1988–2000; Urban History Yearbook→urban1974–1991; Urban History→urban1992–2000. New Yearbook title has an explicit1992 transition; original Urban History date metadata is untouched. Yearbook ISSN remains unfilled because the publisher past-title page repeats modern IDs.

**What this resolves / next:** These three missing-entry gaps now have substantive initial entries, not complete global coverage. Public history still needs fuller museum/Indigenous/non-Anglophone treatment; medical history needs wider regional, clinical and psychiatric historiographies; urban history needs wider regional and medieval/early-modern coverage. Medical History, Bulletin of the History of Medicine, Journal of the History of Medicine and Allied Sciences, and Journal of Urban History are unaccepted sustained-role leads. Canadian Urban History Review duplicates need identity reconciliation. Fuller primary reading is valuable where publisher descriptions/abstracts currently support selected works. Do not misreport scoped passages as full-book reading. Older1.116 journal leads remain relevant.

**Artifacts / validation:** Report `feedback/gap-fields-v1.117.md`; full additions manifest `feedback/gap-fields-v1.117-additions.json`; updated69-field ledger `feedback/journals/principal-venues-v1.117-review.json`; audit output `feedback/gap-fields-v1.117-validation.json`. Preserved snapshot1.116 and immutable hash-pinned `venue-batches/founding-006.json`; research PDFs/hash manifest under `data/journal-catalogue/venue-research/v1.117/`. Reproduce with `python3 scripts/build_journal_catalogue.py`, `python3 scripts/build_site.py`, `python3 scripts/audit_gap_fields.py`. Earlier audit scripts target earlier revisions. 62 Python tests and JS core suite passed; zero structural errors/four unchanged warnings. Prior records, catalogue reproduction, ledger and six allowlisted asset bytes verified. Historical renderer loads new entries through existing code; journal renderer still absent. No deployment or frontend design changes.

## Historical handoff through revision 1.116 (superseded where noted above)

Updated **2026-09-16**, after continued principal-journal review (**editorial revision 1.116; historical schema 1.4; journal schema 1.3**).

**Latest user direction:** Continue building evidence-based journal edges and use them to expose meaningful historiographical gaps. Principal venues require sustained historical/institutional roles, sourced intervals and target qualifications. Retain the stricter founding criterion; do not infer importance from titles, current remit or isolated articles. No rankings, quotas or frontend design. OpenAlex remains paused.

**Current accepted data (1.116):** Added **11 principal links**, bringing the total to **38 principal links across 32 title records and 26 fields**. With nine founding and three debate links, there are **50 venue edges reaching 29 of 66 group entries**. Added the previously absent Journal of the Historical Society of Nigeria and four Annales title phases: **1,637 candidates/title records**, 808 with ISSNs, 565 starts, 798 library profiles. Active subjects remain 2,006 (1,322 checked / 684 provisional); 864 checked-classified, 442 provisional-only, 331 unclassified records. Historical graph remains 109 nodes / 708 edges / 805 sources / 797 people.

**New selections:** Quaderni Storici→Italian microhistory (1976–1987); JHSN→African historiography and anti-colonial histories (1956–1980); Ethnohistory→Indigenous history as an interlocutor (1954–2000); Le Mouvement social→social history (1960–2000); Journal of Negro History→Black history (1916–2000); three Annales title intervals→Annales (1929–1938, 1946–1993, 1994–2000); Social Studies of Science→STS (1980–2000); Journal of the History of Sexuality→sexuality-history strand (1990–2000). Existing links unchanged. Ethnohistory is not equated with Indigenous research authority; sexuality history is not equated with uniform queer theory.

**Annales reconciliation:** Five publisher-confirmed title transitions now connect original1929 → AHS1939–1941 → Mélanges1942–1944 → AHS1945 → ESC1946–1993 → HSS1994 onward. Four missing title-phase nodes added. ESC/HSS share ISSN0395-2649; the preserved HSS library record describes the combined postwar run from1946. Generic Annales candidate remains unresolved. Original canonical dates/metadata are unchanged; the new relations carry the title boundaries. Do not import Persée’s erroneous1929–1937 summary label or platform grouping of all postwar volumes under HSS. Ten title-history relations now exist overall.

**Evidence and continuation:** New report and updated66-field ledger: `feedback/journals/principal-venues-v1.116.md` / `-review.json`. Untouched field notes are explicitly carried forward. Three new selections retain partial access: Ethnohistory scholarly abstract; SSS indexed retrospective opening; JHSexuality indexed abstract/opening. Full-text follow-up remains valuable. Located Lutz Raphael’s GG25-year study, actually GG26(1),2000,5–37,JSTOR40185967; body unread, so no principal edge added. Review(Fernand Braudel Center), RHR newsletter/title phases, History&Memory, JournalAfricanHistory and Francophone/Indigenous-led venues remain leads. The missing Nigerian title is a catalogue/venue-community gap, not an absent entire field. Strong atlas-entry candidates remain public, medical/health and urban history from sourced1.112 findings; no new major field omission established here.

**Preservation / verification:** Snapshot1.115 and hash-pinned `venue-batches/founding-005.json`; all prior historical content and journal identities, chronology, bibliography, sources, edges, classifications and title relations preserved. Existing journals change only research role/source references. Run `python3 scripts/build_journal_catalogue.py`, then `python3 scripts/audit_journal_venue_continuation.py` (older audit scripts target earlier revisions). 62Python tests and JS core passed; zero structural errors/four unchanged warnings; exact reconstruction, research-PDF hashes and six allowlisted asset bytes verified. Research copies under `data/journal-catalogue/venue-research/v1.116/` stay outside browser assets. No deployment or journal renderer.

## Historical handoff through revision 1.115 (superseded where noted above)

Updated **2026-09-16**, after the principal-venue review (**editorial revision 1.115; historical schema 1.4; journal schema 1.3**).

**Latest user direction — principal journals, not a founding-journal census:** User approved identifying important journals through sustained historical roles and using the results to expose atlas gaps. This supersedes the earlier instruction below to prioritize JSTOR before venue review. Use `principal_venue` with a sourced interval and explicit editorial selection rationale; keep `founded_for` for constitutive cases and `site_of_debate` for named published exchanges. No quotas or citation/impact rankings. A current remit, launch statement or isolated famous article does not establish sustained importance.

**Current accepted data (1.115):** Added **27 principal-venue edges across 22 journal/title records and 19 fields**, plus two debate edges (Smith–Gellner in Nations and Nationalism, 1996; Bloor–Latour in Studies in History and Philosophy of Science Part A, 1999). With thirteen founding withdrawals, there are **39 venue edges: 27 principal, nine founding, three debate**, reaching 24 of 66 group entries. Inventory stays **1,632** candidates, 798 library profiles, 803 with ISSNs, 560 starts; historical graph remains109 nodes/708 edges/805 sources/797 people. Every prior journal identity, date, bibliographic record, subject and title relation is unchanged.

**Founding reappraisal resolved:** Of the thirteen pending1.113 claims, retain Isis with its 1912 foundation/1913 first-volume distinction and withdraw twelve unsupported founding inferences. Most receive separately sourced principal relations; History and Anthropology and Holocaust and Genocide Studies remain research leads. Also withdraw the earlier Journal of World History founding inference in favour of its consolidating venue role. Environment and History’s rejected founding claim remains withdrawn. Environmental Review1976–1989, Environmental History Review1990–1995 and Environmental History1996–2000 have separate principal intervals, preserving the accepted merger history. Other retained founding claims keep their original qualifications; this is not a new complete founding census.

**Coverage and next work:** `feedback/journals/principal-venues-v1.115-review.json` screens target fit for all66 entries and supplies explicitly unaccepted discovery leads. Only19 have initial principal selections; absence of an edge is not absence of a journal or field. Annales needs generic/ESC/HSS title reconciliation before a long principal interval. Prioritize remaining dedicated venues, non-Anglophone journals and African-based communities; the initial evidence favours English-language retrospective material. JSH selection uses a scholarly abstract; JWH uses an explicitly limited search-indexed WHA retrospective (direct PDF unavailable). Do not claim either full article read. Strong dedicated-entry candidates remain public history, medical/health history and urban history, carrying forward the sourced1.112 findings; broader intellectual history and comparative genocide remain target-fit questions. No new field nodes or journal renderer added.

**Reproduction / checks:** Snapshot1.114; hash-pinned `venue-batches/founding-004.json` records exact withdrawals, additions and prior-node fingerprints. `research_venue_checks` may promote only eligible researched periodicals and append sources; they cannot alter chronology/identity/bibliography. Withdrawn IDs cannot be reused. Run `python3 scripts/build_journal_catalogue.py` and `python3 scripts/audit_journal_principal_venues.py`. Report: `feedback/journals/principal-venues-v1.115.md`; reappraisal: `founding-reappraisal-v1.115.json`. 62 Python tests and JavaScript core passed; zero structural errors/four unchanged warnings; exact preservation/offline reconstruction passed. Six allowlisted assets rebuilt. OpenAlex remains paused; no deployment.

## Historical handoff through revision 1.114 (superseded where noted above)

Updated **2026-09-16**, after the environmental founding correction and full JSTOR title-history harvest (**editorial revision 1.114; historical schema 1.4; journal extension schema 1.3**).


**Latest user correction and JSTOR direction — 2026-09-16 (1.114):** User rejected Environment and History as a founding journal, correctly identified the environmental journal lineage, and asked whether JSTOR title histories could be harvested. Corrected the founding edge to **Environmental Review (1976)**, supported by ASEH’s field-organizing history. Recorded separate Environmental Review→Environmental History Review and Journal of Forest History→Forest & Conservation History branches, both merging into Environmental History in 1996. Added four missing title records; retained all existing journal IDs/metadata. JSTOR’s modern-title 2020 endpoint is coverage, not cessation. Its earlier Forest History Newsletter grouping needs title-name reconciliation; preserve it in staging. Grove’s editorial names Ranajit Guha, not Ramachandra: corrected the mistaken source note with an exact prior-record audit trail.

**Founding criterion:** A journal must help constitute the named field or school. A launch mission, later consolidation or broad topical remit is insufficient. The previous 1.113 expansion overreached. `feedback/journals/founding-criterion-reappraisal-v1.114.json` records specific concerns for its other thirteen additions; those still need historical reappraisal and have NOT been recertified by this correction. Do not present the 22 stored founding edges as a newly verified founding-journal census. User’s latest direction is bibliographic title-history harvesting, so finish that pipeline before resuming speculative founding additions.

**JSTOR full-file harvest COMPLETE:** Official Complete Title History List downloaded: **5,021 rows / 4,631 distinct title IDs**. All 390 repeated-ID rows retained. Compared all **1,628 pre-correction candidates**: **370** with strict candidates (**242 title-and-ISSN, 117 title-only, 11 ISSN-only**), 1,258 unmatched by this method. Matched families contain 537 title IDs, including 175 additional related-title leads. **233** reported predecessor observations have overlap/reverse-order flags; one reference is missing. Critical: JSTOR reference fields can serialize overlapping family members, not true succession. Preserve raw pointers; no automatic genealogy, dates or founding edges. Download is saved/hash-recorded under `data/journal-catalogue/jstor-title-history/`; `python3 -m scripts.stage_jstor_title_history` reproduces staging against snapshot1.113. Next: review title/ISSN matches and their families, resolve branches with publisher/library sources, then accept scoped title histories. No bulk imports yet.

**Current accepted data / validation:** Revision1.114: **1,632** periodical/title candidates, 803 with ISSNs, 560 publication starts, 798 library profiles; 864 checked subject candidates, 442 provisional-only, **326 unclassified**. Historical graph remains109nodes/708edges/805sources/797people. Venue count remains23 because one edge was replaced; title-history relations now5. Snapshot1.113; hash-pinned founding-003 records the exact withdrawn edge, replacement, four new titles, four title relations and Guha correction. All prior journal nodes, dates, bibliography and classifications unchanged. Report `feedback/journals/environmental-correction-v1.114.md`; validation JSON alongside. 61Python tests, JS core, zero structural errors/four unchanged warnings, exact preservation/rebuild and six public-asset byte checks passed. No deployment or OpenAlex. Earlier revision-specific audits remain historical; do not run them against1.114 as current checks.

**Latest direction / expanded founding review — 2026-09-16 (1.113):** User challenged the five-link pass as too small (“Only 5?”). Expanded historical research and integrated **14 more founding-programme links**, bringing the journal graph to **22 founded_for + 1 site_of_debate**. Added Feminist Studies, Signs, Social Science History, Economic History Review, Oral History Review, History in Africa, Gender & History, Journal of Interdisciplinary History, Isis, Comparative Studies in Society and History, Environment and History, Nations and Nationalism, Holocaust and Genocide Studies, and History and Anthropology. Each carries a programme claim, source-access scope and target qualification. Some are institutional histories, contemporary reviews or an explicitly limited scholarly abstract, not full founding-editorial readings. Journal creation/consolidation never dates the origin of a whole field. Preserve Isis’s 1912 foundation / 1913 first-volume distinction.

**Current data:** 1,628 periodical candidates, 798 reviewed bibliographic profiles, 799 with ISSNs; **557 publication starts** after filling only Oral History Review 1973 and History in Africa 1974. All 545 catalogued title starts and all previously known dates remain unchanged. Checked subject coverage remains 864, provisional-only 442, unclassified 322; 2,006 active classification rows. Historical graph unchanged: 109 nodes, 708 edges, 805 sources, 797 people. Journal edges are data only; the current historical renderer does not display them.

**Continuation:** This is a targeted expansion, not a completed founding review of all 1,628 titles. The report and 28-record accepted/continuation ledger are `feedback/journals/founding-expansion-v1.113.md` and `-review.json`. Public, medical and urban history remain the strongest dedicated-entry candidates from the previous full subject gap matrix. Further target questions: broader history of ideas/intellectual history (no Lovejoy mention found; Cambridge School is narrower), and comparative genocide studies beyond the Holocaust entry. These are research leads, not confirmed blanket omissions. Pending founding readings include Representations, Journal of the History of Sexuality, History and Theory, JEH and JAH; Environmental History needs a 1996 merger-programme review, RHR needs newsletter/title reconciliation, and British New Left Review cannot be assigned to the specifically US New Left entry. History & Memory is still a lead without a programme reading. Do not restart broad library/OpenAlex retrieval.

**Reproduction / validation (1.113):** Snapshot `drafts/historiography-1920-2000.v1.112.json`; hash-pinned `venue-batches/founding-002.json` applies after founding-001 and immutable bibliography. Venue importer can fill wholly unknown chronology only through explicit `publication_start_checks`, protected by exact prior-node fingerprints; it cannot replace existing dates or infer continuity. Run `python3 scripts/build_journal_catalogue.py` then `python3 scripts/audit_journal_founding_expansion.py`; old revision-specific audits deliberately target their historical revisions. 57 Python tests and JavaScript core suite passed, zero structural errors/four unchanged warnings, exact preservation and offline reconstruction passed. Six allowlisted public assets rebuilt and byte-checked; no deployment. This update supersedes the narrower status and queue below.

**Latest direction and completed journal founding pass — 2026-09-15 (1.112):** User wants edges for journals established with fields/programmes (especially Past & Present and Annales), and to use journal coverage to detect major atlas gaps. Added five founding edges: P&P→marx (1952, explicitly a broad coalition), Technology and Culture→technology (1959), Journal of World History→global (1990), Geschichte und Gesellschaft→bielefeld (1975, reused the existing primary foreword review), Journal of Negro History→black (1916, earlier roots; original title retained). Annales already had its 1929 primary founding edge; preserved it and all three other existing venue claims. Current total **9 venue edges: 8 founded_for, 1 site_of_debate**. All 109 historical nodes, 708 historical edges, 805 historical sources, 797 people, journal dates, bibliographic profiles, classifications and candidate IDs unchanged. Five journals gained source references, with necessary role promotion. No new historical field nodes yet.

**Gap findings / next data work:** Strong candidates for dedicated entries are **public history, history of medicine/health, urban history**; each has substantial existing partial coverage, documented in `feedback/journals/founding-and-gaps-v1.112.md` and `.json`. Start with public history, connecting existing oral/memory/History Workshop approaches without conflating them. Medical history already includes Roy Porter and African healing; medical historian Dorothy Porter is distinct from the existing librarian Dorothy Porter Wesley. Urban titles need Newsletter/Yearbook/current-title reconciliation before a founding link. Archaeology, legal/education history and regional historiographies are further leads, not yet fully researched gap findings. Do not create schools from region labels or journal counts. Gender & History's 1989 editorial is identified but its programme text still needs reading. Other founding venues remain a targeted queue; broad collection and OpenAlex work are paused.

**Reproduction / validation (1.112):** Snapshot `drafts/historiography-1920-2000.v1.111.json`. New immutable `venue-batches/founding-001.json` accepted in `accepted-venue-batches.json`; importer runs after metadata so the earlier exact-record fingerprints stay valid. Run `python3 scripts/build_journal_catalogue.py` then `python3 scripts/audit_journal_foundings.py`. The older library audit explicitly targets 1.111 and must not be run against 1.112 as if counts were unchanged. 54 relevant Python tests and JavaScript core suite passed; zero structural errors/four unchanged warnings. Exact prior data preservation and offline rebuild checked. Six allowlisted public assets rebuilt; no frontend design or deployment. Journal edges remain a separate dataset graph, not displayed by the current historical renderer.

**Library reconciliation/import COMPLETE — 2026-09-15 (1.111):** User approved the proposed continuous review-and-import pass. Screened the entire 1,628-candidate inventory and accepted 798 primary-title/own-ISSN-concordant bibliographic profiles, with saved OpenAlex source IDs/hashes where used as identifier evidence. Added ISSNs to 786 candidates, language codes to 797, 545 catalogued title starts and 611 LCSH-supported subject rows for 476 candidates; archived 223 directly superseded provisional rows. Source-supported subject coverage increased from 507 to 864. Original headings, title/format relations, dates and source qualifications are retained. Deferrals include ambiguous identities, translations, current-title/newsletter confusion and date conflicts. Explicitly rejected Accounting History newsletter, Japanese Legal History Review, Dialogos and Contradictions homonym risks; preserved Isis 1912 and History Workshop Journal 1976. Fixed review-layer MARC interpretation so genre/form field 655 cannot establish region studied. No original parser/staged evidence was rewritten. Individually reviewed 362 statements support JEH 1941 and JAH current-title 1964. No OpenAlex indexed dates were imported. Scripts: `review_journal_library_metadata.py` stages only, `journal_metadata_batches.py` applies hash-pinned additions, `audit_journal_library_import.py` verifies this revision. Report: `feedback/journals/library-integration-v1.111.md`. This completed initial pass supersedes earlier no-import and review-not-started notes below; field-specific exceptions remain future research.

**OpenAlex source-metadata pass COMPLETE — 2026-09-15:** User said “we can finish the open alex work.” Completed all remaining 608 searches using 608 requests, bringing the initial pass to **1,628/1,628 with zero pending queries**. Outcomes: **12 unique ISSN candidates, 947 title candidates needing review, 333 other identity-review searches, 336 no-result searches**; 55 query result sets are truncated. Final quota check: $0.608 of the free $1 daily allowance used, $0.392 remaining, no prepaid use. All 1,020 prior result hashes were preserved; authoritative graph and catalogue hashes unchanged and their catalogues equal. Nine OpenAlex source IDs map to multiple catalogue candidates and require reconciliation; three existing-start conflicts remain protected. Across the two retrieval efforts, **1,161 candidates** have a potentially relevant library record or a single OpenAlex identity candidate, including **131** with an OpenAlex candidate but no library candidate. These remain candidate evidence, not verified complete profiles. Proof: `feedback/journals/openalex-completion-audit-2026-09-15.json`; full per-candidate report: `feedback/journals/openalex-metadata-full-audit.json`; baseline: `feedback/journals/openalex-resume-baseline-2026-09-15.json`. No worker remains running. The frozen library plan and its earlier OpenAlex hints remain unchanged; new identifiers may support a later targeted library pass in separate staging. Next work: identity/collision review, title/format/date reconciliation, subject mapping and reviewed metadata acceptance. The older works/citation investigation remains paused. This completion supersedes all earlier source-retrieval budget-stop and resume instructions below.

**Library evidence quality audit — 2026-09-15:** In response to “Do we have good data for 1000+ journals?”, audited all 1,628 candidates: 1,030 have potentially relevant library records, 1,011 have library subjects and 1,002 have publication-start observations. Best identity tiers are 12 curated-catalogue ISSN matches, 549 OpenAlex-derived ISSN-hint matches, 469 title-only candidates and 598 unresolved. There are 557 candidates with an identifier-linked record containing both subjects and an exact start-year observation, still requiring identity/title/format review. Existing source-supported subject coverage remains 507; combining it with identifier-linked library subjects covers 849, or 1,163 if title-only library suggestions are included. Thus 1,000+ have useful candidate evidence, not 1,000 verified complete profiles. Report and per-candidate audit: `feedback/journals/library-coverage-audit-2026-09-15.md` / `.json`.

**Library full pass completed; restart recovery — 2026-09-15:** The saved worker state shows completion on **2026-09-14 at 21:03 UTC**, with `finished_with_exceptions`. All **1,628 candidates / 3,256 provider lookups** were attempted; **1,626 candidates** completed bounded lookups at both providers. LOC: 1,620 retrieved, seven retrieved with query errors, one failed. Harvard: 1,627 retrieved, one failed. The exception queue contains **346 lookups across 312 candidates**: 337 truncated searches, seven partial query-error lookups and two failures. Failed titles: Harvard `Reception: Texts,  Readers, Audiences, History` (HTTP 400), LOC `History and Philosophy of the Life Sciences"` (invalid catalogue response). Recovery independently verified **4,723 raw-response hashes**, all **3,256 staging snapshot fingerprints**, and the unchanged authoritative catalogue hash, with zero integrity errors. Audit: `feedback/journals/library-restart-audit-2026-09-15.json`; comparisons: `data/journal-catalogue/library-metadata/triangulation.json` / `.md`. Do not restart the finished full pass merely because the host restarted. Next work is identity/date/subject review and targeted exception repair in preserved staging; no metadata has been automatically imported. These are bibliographic catalogue records, not an established complete volume/issue holdings feed. Existing better dates remain protected; OpenAlex stays paused. This completion supersedes the launch-time status below.

**Full library run authorized and launched — 2026-09-14:** User explicitly rejects stopping after 25-journal batches and wants the full catalogue processed automatically without batch reports/permission gates. Implemented `scripts/library_journal_worker.py`; launched detached PID **1966293** with `--execute --background --max-requests 30000`. Scope: remaining 1,600 candidates / 3,200 LOC+Harvard lookups, continuing the frozen plan. Check `data/journal-catalogue/library-metadata/worker-state.json` and process liveness for current status; do not assume the launch-time count is current. Worker saves each provider lookup, checkpoints on disk, refreshes comparisons every 50 lookups, isolates query failures, retries temporary errors with cooldowns, and writes a final exception queue and hash audit. Duplicate launch protection is a process lock. Do not launch the old batch runner concurrently. It continues after the chat turn while the host runs; repeat the same command after an unexpected host/process stop, subject to the recorded stop reason. Integrity/budget/unexpected errors or five consecutive temporary provider failures cause an explicit operational stop. Thirty-five relevant tests pass. Existing better dates and graph remain protected; no automatic metadata acceptance. No OpenAlex requests authorized by this library continuation. Earlier no-live-worker and bounded-batch stopping instructions below are superseded.

**Library batch 001 completed — 2026-09-14:** User said “run it” for the next 25 LOC/Harvard candidates. All 25 bounded lookups completed for both providers; **28/1,628 candidates queried, 1,600 remain**. Of the new 25, 20 have potentially relevant subject records, 19 have date observations, 10 match existing catalogue ISSNs, and eight have some cross-library date agreement (not independent verification). Fixed LOC title relation and Harvard colon escaping; LOC missing-MARC diagnostics now retain query errors while trying other queries. JEH has one failed query but a later 1941 record; two LOC lookups are truncated. Review catches HWJ 1976/1995 title succession, Isis 1913 versus curated 1912 and an unrelated Harvard 1817–1848 homonym, and Cross-Currents print 2012 versus repository coverage 2011. Preserve better dates. Report and audit: `data/journal-catalogue/library-metadata/batch-001-review.md`, `batch-001-validation.json`. All 99 raw hashes, 56 stage fingerprints and six unchanged pilot files verified; 15 library + 17 existing OpenAlex tests pass. Graph/catalogue unchanged at 1.110; no imports, frontend edits, deployment or OpenAlex calls. No live worker. Earlier statements below that bulk library retrieval had not started are superseded by this checkpoint.

**Library triangulation script — 2026-09-14:** User asked for LOC/Harvard retrieval to triangulate existing data and supplied bibliographic-versus-holdings requirements. Implemented `scripts/library_journal_metadata.py` and `scripts/library_journal_records.py`; runbook `data/journal-catalogue/library-metadata/README.md`. Offline by default, 1,628-candidate frozen plan, optional saved OpenAlex ISSN hints, bounded/paginated/rate-limited/resumable retrieval, raw response hashes, conservative identity assessment and field comparisons. LOC uses MARCXML and preserves 362, 310/321, title relations, all original subfields, and separate holdings fields when returned. Harvard uses MODS. Holdings/volume coverage never becomes publication chronology; no complete holdings feed has been established. Shared LCCN/OCLC evidence is flagged, without numerical confidence or presumed independence. Existing better dates remain protected; no automatic graph edits. Live three-journal pilot completed both providers in 12 requests, then reparsed offline: LOC dates P&P 1952, HGS 1986, JAAH current title 2002; Harvard matches HGS 1986 and leaves the other pilot titles unresolved. Report: `data/journal-catalogue/library-metadata/triangulation.md`; proof: `pilot-validation.json`. Twelve new library tests and 17 existing OpenAlex tests pass. No live worker; bulk library run has not started.

**OpenAlex full run checkpoint — 2026-09-14:** User authorized “run the rest.” Completed **1,020 of 1,628** initial source queries (996 beyond the pilot); **608 remain**, starting with Lias. OpenAlex returned HTTP 429; authenticated usage endpoint confirms daily budget $1, used $0.9993, remaining $0.0007, zero prepaid balance, versus $0.001 per title search. Await the daily midnight-UTC reset (18:00 Regina); no worker is running and no automatic resume is scheduled. Authorization persists: after reset, resume `python3 scripts/openalex_journal_metadata.py --execute --limit 608 --max-requests 709` with network access. Do not change keys or buy credit to bypass this budget. Results: 12 unique ISSN candidates, 624 title candidates requiring review, 198 other identity-review results, 186 zero-result queries; 42 search result sets truncated. Full audit: `feedback/journals/openalex-metadata-full-audit.json`; usage: `feedback/journals/openalex-usage.json`; attempt logs retained. Eight runner tests plus nine existing OpenAlex tests pass. Catalogue hash and graph unchanged at 1.110; no metadata auto-imported. User's date rule: only use OpenAlex dates where better dates are absent, preserving sourced chronology and labeling fallbacks as indexed ranges. The older works/citation investigation remains paused.

**Library API follow-up:** User asked about Library of Congress and Harvard during this run. Both have accessible catalogue APIs. A live LC ISSN lookup for Past & Present returned publication start 1952, subject headings and related editions. Harvard LibraryCloud responds, but tokenized identifier searches are noisy and the exact hyphenated test missed; no Harvard match accepted. Raw small samples and provenance: `data/journal-catalogue/library-api-samples/manifest.json`. Library records should be checked before falling back to OpenAlex dates; no bulk library retrieval has started.

**Latest OpenAlex work — 2026-09-14:** User said “run it”; the journal source-metadata pilot is now authorized and completed. Retrieved all 24 prepared research-journal queries with 24 successful-run API requests after a sandboxed attempt failed (four attempts). Results: 12 unique ISSN candidates, five exact-title candidates, three other searches needing identity review, four zero-result queries. No matches automatically accepted; graph/catalogue remain 1.110. Pilot report: `feedback/journals/openalex-metadata-pilot-2026-09-14.json`. Staging: `data/journal-catalogue/openalex-metadata-staging/`. The earliest indexed years are unreliable as founding dates: Past & Present 1921 versus publisher first issue 1952; Holocaust and Genocide Studies 1971 versus first issue 1986; additional conflicts with existing curated dates are in the report. IDs, publishers and topics are useful attributed metadata. 1,604 initial queries remain; next work is alias/identity review and wider source-only retrieval. No active process or new goal. Authorization to run source metadata persists; the older works/citation investigation stays paused.

**Latest completed web pass (1.110):** Reached **507 candidates with source-supported subjects**, exceeding the explicit goal of 500. Added 143 supported candidates and 225 checked rows using 88 DOAJ records, 46 JSTOR directory matches and nine targeted Sol scope checks. Superseded 69 provisional rows with their history preserved. One attempted check (Aegyptus) remains unresolved because its publisher URL served another journal’s description. The reviewed Sol queue has 20 candidates deliberately deferred; no agent is researching them. Proof: `feedback/journals/goal-500-audit.json`; report: `feedback/journals/web-scope-v1.110.json`. Directory support is explicitly distinguished from publisher remit. No further research is needed for this bounded goal; broader catalogue work remains available for later sessions.

**Completed initial Sol delegation (revision 1.107):** User explicitly requested Sol. Agent `/root/journal_subject_classification` (gpt-5.6-sol) completed all **1,297** previously unclassified candidates in 52 batches. Root reviewed the sources and audited high-risk title assignments with Sol. The quality audit removed 216 unsupported rows and added/retyped 53 literal-title rows. Final new outcomes: **3 checked candidates / 7 classifications; 817 provisional candidates / 988 classifications; 477 unresolved candidates**. No active delegated work or new goal remains. OpenAlex and the original 187-item second-pass queue remain paused.

**Current journal catalogue:** **1,628 candidate periodicals, 140 publication subjects, 2,006 active classification rows, four visual venue edges and 28 discovery resources**. There are **798 reviewed bibliographic profiles**, **799 candidates with ISSNs**, **555 with publication starts** (545 catalogued title/edition starts), **794 with original library subject headings** and **797 with language codes**. **864 candidates have source-supported classifications**, **442 have provisional classifications only**, and **322 have no classification**. The 1,322 checked and 684 provisional rows remain separate; 304 superseded provisional rows retain their original IDs/content. There are still 53 publisher-scope-checked candidates. **1,010 candidates have a reviewed profile or source-supported subjects; 552 have a profile with library headings and a publication start.** These are field-specific counts, not 1,010 complete profiles. Four venue edges remain unchanged.

**Evidence policy:** `title_indicated` classifications are explicitly provisional, have `checked_on: null` and a review date. Opaque titles remain unresolved with reasons. Never present title suggestions as checked publisher remit. `classification_reviews` retains every outcome. CSV and coverage counts separate checked and provisional classifications. Newly introduced subject vocabulary has no inferred atlas-field correspondence. Institutional location, title language and publishing format do not establish region studied or scholarly method.

**Active user direction:** Continue journal data research using broad lists to reveal geographic and historiographical gaps. Include titles beyond 2000 for eventual 2026 coverage. No frontend design. Read only the journal-relevant sections of `opusreview.md`; other review issues are deferred. Use only `founded_for`, `site_of_debate` and `principal_venue` as journal visualization edges, with specific sourced claims and dates. Subject scope remains metadata; no generic `publishes` edges, impact ranking or removal of sparse/non-Western candidates.

**Work remaining:** Use `feedback/journals/library-integration-v1.111-exceptions.json`: 830 deferred library identities, 245 date reviews among accepted profiles and 146 profiles without an accepted broad subject mapping (1,221 field-specific items across 1,179 candidates). Resolve translated titles, homonyms, duplicate OpenAlex candidates, title/series/edition starts and unmapped library headings. Check publisher/library/index scope for the 322 unclassified and 442 provisional-only candidates, prioritizing regional/language gaps. Most bibliographic profiles are not full publisher-remit reviews; founding programmes, debates and sustained venue roles need separate evidence. Initial source retrieval is complete. Do not resume the broader historiography goal or OpenAlex works/citation investigation implicitly.

**Opus review follow-up (2026-09-14, review only):** Read the new `feedback/journals/opus-catalogue-review.md` against 1.110; detailed response: `feedback/journals/opus-catalogue-review-response-v1.110.md`. Recommend subject-to-atlas metadata mappings and the 14 missing date spans among 24 explicitly typed research journals as the next bounded data work. Dates alone do not admit unlinked journals to the prototype. Its footer currently counts subjects as unlinked periodicals (1,764 shown versus 1,624 actual). The 67 stronger-source candidates include library/index evidence; 53 have publisher-scope evidence. All 412 unresolved reviews already retain reasons and next steps. No new goal, frontend change or further source-research batch started.

**Files/workflow:** The authoritative graph contains the exact generated `data/journal-catalogue/catalogue.json`. Generator `scripts/build_journal_catalogue.py` imports hash-pinned subject, source-check and metadata batches, with no network calls. Accepted files are immutable. `accepted-metadata-batches.json` pins `metadata-batches/root-library-001.json`; `accepted-source-checks.json` adds `source-check-batches/root-web-005.json`. Subject checks supersede only explicitly named provisional IDs and retain history. Metadata additions verify the original periodical fingerprint and preserve better data. Current coverage: `feedback/journals/coverage-review.md`; audit: `feedback/journals/library-integration-v1.111.json`; full screening outcomes: `library-integration-v1.111-review.json`. Snapshot `drafts/historiography-1920-2000.v1.110.json` preserves the atlas and catalogue before integration. The original LOC/Harvard and OpenAlex plans remain frozen at 1.110; do not rerun them against the enriched catalogue. Offline review preparation always reads the preserved 1.110 snapshot.

**Preservation and validation:** Revision 1.111 passes 84 Python tests, the JavaScript core suite, zero structural errors and the original four reviewed warnings. Exact generator reconstruction and six allowlisted build files verified. All original historical graph data, journal IDs/occurrences, existing sourced dates and source objects preserved. All 4,884 provider/OpenAlex staged files and 1,079 used raw responses verified by hash. Accepted extracted bibliography is public data; raw XML/MARC, holdings, API credentials and research staging stay outside browser assets. No frontend design or deployment. No live worker remains.

## User direction and latest corrections

- **Map-wide date correction (2026-09-13):** User notes that quantitative history did not end in the 1970s and explicitly approves treating this as a wider problem. All 66 group labels now distinguish emergence/expansion or landmarks from “coverage through 2000.” Never use an expansion range as a field’s lifespan. The 2000 boundary is atlas coverage, not historical termination.

- **Coverage clarification (2026-09-13):** User rejected Black history appearing to end at 1935. Retain the broad field name and explicitly show coverage through 2000; early milestone dates must not visually truncate an enduring field. Revision 1.104 implements this clarification.

- **Date correction (2026-09-13):** Entry date labels must contain actual chronological information. Use sourced publication/institutional milestones or explicit approximate periods; names and generic editorial placeholders are insufficient. All 36 flagged entries and Structural linguistics corrected in 1.103. Do not infer a field’s origin or a person’s lifespan from these dates.

- Build a nested, interactive teaching atlas for **MA history students who have read Lynn Hunt’s _Writing History in the Global Era_ (2014)**. The map is a selective, contestable interpretation, not an exhaustive genealogy or a succession of superseded schools.
- Current historical coverage is **1920–2000 with earlier roots**. Extension through 2026 is intended but unwritten. Later retrospective bibliography does not extend mapped coverage.
- The user rejected a field’s incidental cross-links standing in for its key historians: Marxist social history showed Dorothy Thompson without E. P. Thompson; history of science appeared to offer Yates and Foucault without Kuhn. **This is a whole-map requirement, not an instruction to patch isolated famous names.** Every group now has a shared core-person roster, visible in Connections too.
- Annales appearing to have one connection and the Marxist neighborhood showing only a few links were unacceptable. **Show all recorded incoming and outgoing connections around the selected entry.** No focused-lane or relationship-list pagination. Comparisons remain visible separately without invented direction.
- The confirmed direction is **upstream on the left → selected entry → downstream on the right**. The repeated “left” in the user’s original prompt was clarified as directional shorthand.
- Generic “economic history” arrows are insufficient. Explain which historians, works, methods, and mechanisms travel. Broad entries now contain explicit internal approaches, with cross-group links retained.
- **E. P. Thompson belongs to an early cultural reorientation within British Marxist social history.** Feminist/gender historians built on him while criticizing his limits; he resisted some later extensions. Do not describe class history as noncultural or gender history as only a critique of it. Neither gender historians nor the cultural turn are one uniform position.
- Work autonomously on reversible implementation and review. No hosting provider is selected and no deployment has occurred.

## Authoritative files and current state

| File | Purpose |
| --- | --- |
| `historiography-1920-2000.json` | **109 graph entries, 708 relationships, 805 sources, 797 shared people**; **66 group rosters / 1230 selections**, **43 individual graph entries**; historical schema **1.4**; revision **1.111** also includes the separate journal extension described above. |
| `seminar-pathways.json` | **13** pathways with questions and exercises. Reading order is not influence. |
| `GRAPH-FORMAT.md` | Required reading before loading/rendering relationships; scope, people, internal approaches, directions, bibliography semantics. |
| `EDITORIAL-REVIEW.md` | Revision 1.9 baseline review and coverage matrix; newer research is in the enrichment pass records. |
| `feedback/editorial-review-2026-09-10.json` | Preserved revision 1.9 baseline: all 109 entries and 331 edges. |
| `feedback/enrichment-current-summary.json` | Current counts, source statuses and missing contextual works. |
| `feedback/enrichment-pass-log.json` | Persistent substantive review inventory: 109 reviewed, 0 pending; follow-up queue. |
| `feedback/enrichment-science-v1.10.json` | Exact before/after records and six-dimension findings for the science batch. |
| `feedback/enrichment-economic-roots-v1.11.json` | Exact economic-roots changes, two six-dimension reviews, and ten filled work selections. |
| `feedback/enrichment-geography-environment-v1.12.json` | Exact geography/environment changes, two six-dimension reviews, and five filled work selections. |
| `feedback/enrichment-economic-consumption-v1.13.json` | Exact economic/consumption changes and two six-dimension reviews. |
| `feedback/enrichment-quant-demography-v1.14.json` | Exact quantitative/demography changes, two six-dimension reviews and three filled work selections. |
| `feedback/enrichment-political-social-v1.15.json` | Exact political/social changes, two six-dimension reviews and eight filled work selections. |
| `feedback/enrichment-comparative-german-v1.16.json` | Exact comparative/German changes and two reviews. |
| `feedback/enrichment-micro-oral-v1.17.json` | Exact micro/oral changes, two reviews and Levi’s filled work selection. |
| `feedback/enrichment-memory-workshop-v1.18.json` | Exact memory/Workshop changes and two reviews. |
| `feedback/enrichment-nations-holocaust-v1.19.json` | Nationalism/Holocaust exact changes, two reviews and four filled work selections. |
| `feedback/enrichment-post-subaltern-v1.20.json` | Postcolonial/subaltern changes, two reviews, Amin’s filled work and eight exchanges. |
| `feedback/enrichment-africa-anticolonial-v1.21.json` | Anti-colonial/African changes, two reviews, seventeen approaches and five exchanges. |
| `feedback/enrichment-fanon-rodney-v1.22.json` | Fanon/Rodney individual reviews, five relationships and three selections. |
| `feedback/enrichment-james-williams-v1.23.json` | James/Williams reviews, primary passages, five links and five selections. |
| `feedback/enrichment-black-atlantic-v1.24.json` | Black/Atlantic reviews, three works filled, nine approaches and three links. |
| `feedback/enrichment-women-gender-v1.25.json` | Women/gender reviews, five works filled, fourteen approaches and four links. |
| `feedback/enrichment-identity-queer-v1.26.json` | Identity/queer reviews, three works filled, fifteen approaches and four links. |
| `feedback/enrichment-indigenous-cultural-v1.27.json` | Research authority, collective practice, cultural debates and nine connections. |
| `feedback/enrichment-anthropology-v1.28.json` | Three reviews, four works filled, thirteen approaches and five links. |
| `feedback/enrichment-linguistics-durkheim-v1.29.json` | Two reviews, fifteen approaches, two new and seven clarified connections. |
| `feedback/enrichment-annales-founders-v1.30.json` | Three reviews, two works filled, seven approaches and eight new connections. |
| `feedback/enrichment-annales-successors-v1.31.json` | Three reviews, sixteen exchanges, eleven sources and a resolved Braudel reception gap. |
| `feedback/enrichment-marx-thompsons-v1.32.json` | Three reviews, sixteen exchanges, seven approaches and ten additional Marxist-roster selections. |
| `feedback/enrichment-dobb-hilton-torr-v1.33.json` | Three reviews, nineteen exchanges, four approaches and eighteen additional roster selections. |
| `feedback/enrichment-hobsbawm-hill-tawney-v1.34.json` | Three reviews, twenty-one exchanges, four approaches and eleven additional roster selections. |
| `feedback/enrichment-power-pinchbeck-clark-v1.35.json` | Three reviews, ten exchanges, three approaches and eleven additional roster selections. |
| `feedback/enrichment-cam-yates-wedgwood-v1.36.json` | Three reviews, eleven exchanges, five approaches and twenty-four additional roster selections. |
| `feedback/enrichment-beard-spruill-salmon-v1.37.json` | Three reviews, twelve exchanges, five approaches and twenty-two additional roster selections. |
| `feedback/enrichment-flexner-tuchman-v1.38.json` | Two reviews, nine exchanges, four approaches and sixteen additional roster selections. |
| `feedback/enrichment-war-military-v1.39.json` | Two group reviews, four work gaps filled, eight exchanges, fifteen approaches and twenty-seven additional selections. |
| `feedback/enrichment-biography-v1.40.json` | two group reviews, one work gap filled, eight exchanges, fifteen approaches and twenty-seven additional selections. |
| `feedback/enrichment-psychoanalysis-v1.41.json` | two reviews, Freud work filled, fourteen approaches and five specific exchanges. |
| `feedback/enrichment-lacan-althusser-v1.42.json` | two individual reviews, eight approaches and six specific connections. |
| `feedback/enrichment-foucault-derrida-v1.43.json` | two individual reviews, nine approaches and seven specific connections. |
| `feedback/enrichment-nietzsche-barthes-v1.44.json` | two individual reviews, one work filled, nine approaches and nine specific connections. |
| `feedback/enrichment-cultural-national-v1.45.json` | two group reviews, two works filled, thirteen approaches and seven connections. |
| `feedback/enrichment-ranke-historicism-v1.46.json` | two group reviews, Dilthey work filled, sixteen approaches and seven connections. |
| `feedback/enrichment-wittgenstein-ryle-v1.47.json` | two individual reviews, primary philosophical distinctions, eight selections and three connections. |
| `feedback/enrichment-context-conceptual-v1.48.json` | two group reviews, Pocock work filled, twelve approaches and six connections. |
| `feedback/enrichment-materialism-sociology-modernization-v1.49.json` | three group reviews, seventeen approaches and six specific connections. |
| `feedback/enrichment-dependency-newleft-v1.50.json` | two group reviews, twelve approaches, six connections and the final two work blanks filled. |
| `feedback/enrichment-culture-language-v1.51.json` | two group reviews, twelve approaches, feminist and social-history contributions, and named textual methods. |
| `feedback/enrichment-global-v1.52.json` | global-history review, seven approaches, five specific exchanges and precisely scoped primary sources. |
| `feedback/enrichment-white-gramsci-v1.53.json` | two individual reviews, narrative/evidence distinctions, intellectual functions and critical receptions. |
| `feedback/enrichment-philhistory-v1.54.json` | explanation/objectivity review, six distinctions and specific narrative/memory resources. |
| `feedback/enrichment-frankfurt-v1.55.json` | differentiated critical theory, feminist historians and exile assistance. |
| `feedback/enrichment-practice-elias-v1.56.json` | collaborative practice research, relational inquiry and specific reception. |
| `feedback/enrichment-progressive-v1.57.json` | Latest: sectional mapping, literary conflict and contested consensus arguments. |
| `feedback/enrichment-revival-v1.58.json` | Narrative plurality, selected primary evidence and specific reception. |
| `feedback/enrichment-truth-v1.59.json` | Final first-pass entry: plural historical-truth debates. |
| `feedback/enrichment-second-pass-baseline.json` | Immutable captured follow-up inventory. |
| `feedback/enrichment-second-pass-log.json` | Second-pass researched outcomes. |
| `feedback/enrichment-second-science-v1.60.json` | Objectivity, instruments and Chinese-series credits; first second-pass outcome. |
| `feedback/enrichment-second-science-regions-v1.61.json` | Regional science projects and exact limits. |
| `feedback/enrichment-second-kuhn-v1.62.json` | Kuhn, Popper, Lakatos and existing reception evidence. |
| `feedback/enrichment-second-epistemology-v1.63.json` | Primary epistemology and named statistical/geographical resources. |
| `feedback/enrichment-second-ssk-v1.64.json` | Durkheim resource and paired Bloor–Latour primary excerpts. |
| `feedback/enrichment-second-sts-technology-v1.65.json` | Feminist alternatives, institutions, collaboration and technology editions. |
| `feedback/enrichment-second-historical-economics-v1.66.json` | Primary programmes, internal disagreements and selected reception. |
| `feedback/enrichment-second-economic-theory-v1.67.json` | Specific theory uses, colonial property debate and Naoroji’s appropriation. |
| `feedback/enrichment-second-critical-geography-v1.68.json` | Critical/feminist geography, historical uses and imperial knowledge practices. |
| `feedback/enrichment-second-sauer-febvre-v1.69.json` | Sauer scan, landscape criticism, Febvre/Vidal and specific teaching reception. |
| `feedback/enrichment-second-environment-justice-v1.70.json` | Bullard, Huggins collaboration, situated comparison and evidence limits. |
| `feedback/enrichment-second-dust-bowl-v1.71.json` | Causal disagreements, regional scale, household survival and Hewes resource. |
| `feedback/enrichment-second-wilderness-v1.72.json` | Guha/Cronon contexts, named reception and Inden resource. |
| `feedback/enrichment-second-conservation-v1.73.json` | Merchant/Pesic disagreement and Carruthers/Grove conservation comparison. |
| `feedback/enrichment-second-business-v1.74.json` | Chandler/Mokyr/Roy comparison and Berg’s specific resource. |
| `feedback/enrichment-second-fogel-v1.75.json` | Counterfactual assumptions, efficiency criticism and explicit reply access limit. |
| `feedback/enrichment-second-pomeranz-v1.76.json` | Regional units, named resources and Huang’s specific challenge. |
| `feedback/enrichment-second-household-consumption-v1.77.json` | Weatherill/Vickery, Shammas comparison and specific theory reception. |
| `feedback/enrichment-second-clunas-v1.78.json` | Ming consumers, source distinctions and Pagani’s reception. |
| `feedback/enrichment-second-consumption-theory-v1.79.json` | Primary theory, Geary’s application and specific historical uses. |
| `feedback/enrichment-second-quantitative-v1.80.json` | Mobility samples, Indian agrarian categories and reply access limit. |
| `feedback/enrichment-second-demography-v1.81.json` | Marriage comparisons and collaborative French sampling. |
| `feedback/enrichment-second-chinese-population-v1.82.json` | Fertility measures, intentional-control debate and research collaboration. |
| `feedback/enrichment-second-family-history-v1.83.json` | Family-history concepts, source selection and Italian marriage patterns. |
| `feedback/enrichment-second-political-biography-v1.84.json` | Political motives, Wood’s critique and biographical inference. |
| `feedback/enrichment-second-political-regions-v1.85.json` | Rio de la Plata politics, research collaboration and public-sphere reception. |
| `feedback/enrichment-second-bengal-labor-v1.86.json` | Bengal labor, cultural continuity and gender criticism. |
| `feedback/enrichment-second-family-colonial-labor-v1.87.json` | Family-history debate and Mombasa labor case. |
| `feedback/enrichment-second-experience-military-v1.88.json` | Experience response, recruitment comparison and Tilly resource. |
| `feedback/enrichment-second-comparative-causation-v1.89.json` | Primary comparative cases and contemporary criticism. |
| `feedback/enrichment-second-structural-criticism-v1.90.json` | Reciprocal reply and explicit full-text limits. |
| `feedback/enrichment-second-comparative-traditions-v1.91.json` | Earlier comparisons, named reception and regional criticism. |
| `feedback/enrichment-second-german-institutions-v1.92.json` | Journal programme, antecedents and political continuities. |
| `feedback/enrichment-second-everyday-exchange-v1.93.json` | Reciprocal Lüdtke–Wehler exchange; Frevert subpart pending. |
| `feedback/enrichment-second-german-gender-v1.94.json` | Frevert’s primary case and Studer’s gender/class reception. |
| `feedback/enrichment-second-levi-v1.95.json` | Levi’s methodology and qualified interpretation critique. |
| `feedback/enrichment-second-scale-v1.96.json` | Primary scale argument and Mexican local-history collaboration. |
| `feedback/enrichment-second-oral-method-v1.97.json` | Primary participation and editing passages, named collaborators. |
| `feedback/enrichment-second-oral-tradition-v1.98.json` | Transmission, performance and institutional interpretation. |
| `feedback/enrichment-second-memory-primary-v1.99.json` | Changing traditions and contested memorial production. |
| `feedback/enrichment-second-memory-regions-v1.100.json` | Argentina research, Vichy representations and Jewish historiography. |
| `feedback/enrichment-second-workshop-primary-v1.101.json` | Primary evidence selection and imperial motherhood. |
| `feedback/enrichment-second-workshop-practice-v1.102.json` | Worker history and paired Chartism interpretations. |
| `feedback/date-label-corrections-v1.103.json` | Exact 37-entry date-label corrections and source mapping. |
| `feedback/black-history-date-scope-v1.104.json` | Black history date explicitly covers through 2000. |
| `feedback/group-date-coverage-v1.105.json` | All group labels separate expansion/landmarks from atlas coverage. |
| `feedback/enrichment-next-research.md` | Current bounded-second-pass next action and completed research handoffs. |
| `feedback/representative-people-audit.json` | Preserved revision 1.9 roster audit and limitations. |
| `REVISION-NOTES.md` | Historical editorial decisions. Older sections retain their historical counts. |
| `DEVELOPMENT.md` | Current design status followed by historical ideas; earlier sequencing suggestions are not current instructions. |
| `drafts/historiography-1920-2000.v1.0.json` through `.v1.105.json` | Preserved snapshots. v1.3 is the completed Fable merge before twelve women historians were added. |
| `drafts/seminar-pathways.v1.4.json` | Earlier pathway text before Thompson-related refinement. |
| `feedback/fable-5.1-review.json` | Decisions on all 116 proposed Fable links: 113 curated, 3 deferred; preserves proposed-to-actual ID mappings. |
| `site/` | Native JavaScript/HTML/CSS/SVG frontend; no package dependencies. |
| `scripts/build_site.py` | Validates and copies exactly six allowlisted public files. |

The workspace is `/home/jic823/historiography`. No working Git repository was found; do not assume commits or a branch exist. Leave unrelated `Clifford/` material alone.

## Current visualization

Nesting is **four overview layers → school/field → internal approaches and representative people → person profiles and contextual works**. All sixty-six groups have **685** explicit internal approaches. These are collapsible teaching distinctions, not inferred communities, additional graph nodes, or exclusive affiliations. Search includes their titles, focus, people, and works.

Opening a group defaults to historians and contributors. Its Connections tab shows the **entire selected core roster above the map** and all matching recorded connections together. Left and right lanes expand vertically; the centre remains the selected entry. Incoming influences precede contributions and critiques, alphabetically within roles; outgoing links are alphabetical. Comparisons and any future unclassified links appear below, without arrows. Full relationship explanations and evidence are inspectable. Some broad links have short `map_label` explanations on neighbor cards.

Current focused counts:

| Entry | Incoming | Outgoing | Comparisons | Total |
| --- | ---: | ---: | ---: | ---: |
| Marxist social history | 14 | 15 | 2 | 31 |
| Biographical & literary traditions | 1 | 3 | 1 | 5 |
| Biography / life writing | 15 | 6 | 3 | 24 |
| Strategic & military scholarship | 5 | 2 | 0 | 7 |
| Military history | 10 | 6 | 1 | 17 |
| Eleanor Flexner | 4 | 2 | 0 | 6 |
| Barbara W. Tuchman | 4 | 3 | 1 | 8 |
| Mary Ritter Beard | 3 | 2 | 1 | 6 |
| Julia Cherry Spruill | 2 | 2 | 1 | 5 |
| Lucy Maynard Salmon | 3 | 3 | 3 | 9 |
| Helen Maud Cam | 2 | 2 | 1 | 5 |
| Frances A. Yates | 3 | 2 | 3 | 8 |
| C. V. Wedgwood | 4 | 4 | 1 | 9 |
| Eileen Power | 3 | 5 | 1 | 9 |
| Ivy Pinchbeck | 3 | 2 | 1 | 6 |
| Alice Clark | 4 | 3 | 1 | 8 |
| Eric Hobsbawm | 7 | 6 | 0 | 13 |
| Christopher Hill | 8 | 5 | 0 | 13 |
| R. H. Tawney | 3 | 6 | 0 | 9 |
| Maurice Dobb | 5 | 3 | 0 | 8 |
| Rodney Hilton | 5 | 5 | 0 | 10 |
| Dona Torr | 3 | 6 | 0 | 9 |
| E. P. Thompson | 8 | 14 | 0 | 22 |
| Dorothy Thompson | 4 | 7 | 1 | 12 |
| Annales | 12 | 9 | 5 | 26 |
| Marc Bloch | 1 | 3 | 0 | 4 |
| Lucien Febvre | 2 | 6 | 0 | 8 |
| Fernand Braudel | 5 | 5 | 0 | 10 |
| Ernest Labrousse | 2 | 3 | 0 | 5 |
| Roger Chartier | 5 | 5 | 0 | 10 |
| Economic history | 19 | 15 | 4 | 38 |
| History of science | 9 | 5 | 1 | 15 |
| Anti-colonial histories | 6 | 7 | 1 | 14 |
| African history | 6 | 6 | 2 | 14 |
| Frantz Fanon | 1 | 4 | 0 | 5 |
| Walter Rodney | 4 | 5 | 0 | 9 |
| C. L. R. James | 2 | 7 | 0 | 9 |
| Eric Williams | 1 | 4 | 0 | 5 |
| Black history | 1 | 8 | 3 | 12 |
| Atlantic & diaspora histories | 8 | 2 | 1 | 11 |
| Women’s history | 14 | 22 | 4 | 40 |
| Gender & racial formation | 12 | 18 | 3 | 33 |
| Identity histories | 7 | 0 | 5 | 12 |
| Sexuality & queer history | 5 | 1 | 1 | 7 |
| Indigenous history | 1 | 3 | 3 | 7 |
| British cultural studies | 8 | 4 | 2 | 14 |
| Anthropology & ethnography | 4 | 16 | 4 | 24 |
| Claude Lévi-Strauss | 4 | 4 | 1 | 9 |
| Clifford Geertz | 5 | 5 | 2 | 12 |
| Structural linguistics | 2 | 5 | 1 | 8 |
| Social facts & collective life | 1 | 14 | 0 | 15 |

“All connections” means every recorded edge matching the explicit filters, not a claim that every historical connection has been researched. The science view prominently includes Kuhn, Sarton, Koyré, Merton, Shapin, and Schaffer; Yates and Foucault are additional qualified links. Kuhn’s existing `edge_131` is now classified as a contribution and visible in the flow.

Directory/person-card pagination remains; focused relationship pagination has been removed. Old `inPage`, `outPage`, and `otherPage` URL parameters are ignored. Hash URLs support entry, person, edge, pathway, filters, views, and directory pages. Browser history, reset, keyboard activation, and pathway context work. Below 700 px, the complete relationship list is the default; the map scrolls inside its own container when explicitly selected. No force simulation or fabricated timeline is used.

## Data semantics to preserve

- Four layers: `intellectual_traditions`, `enduring_fields_and_genres`, `intellectual_connections`, `historiographical_developments`. Thinker layer label: “Thinkers and intellectual connections.” Layers are not person professions or node types.
- Four period groups: earlier roots/interwar; approximately 1945–70; 1970–85; 1985–2000. Null-period entries remain discoverable under period filters. `date_label` is prose, not reviewed start/end dates. Never infer a tradition’s termination from a period boundary.
- `entry_kind: group | person` controls browsing. Schema 1.4’s `entry_type` supplies a human-readable category; `scope_note` explains distinctions. Combined entries deliberately preserve differences: Progressive/consensus, dependency/world-systems, microhistory/everyday life, gender/racial formation, etc.
- `people` supplies shared identities and optional full `node_id`. Roster roles are historian, contributor, precursor, critic, or comparison, with contextual works and sources. **Rosters and internal approaches are not influence edges or verified membership registers.** Keep original `representative_figures_and_works` prose too.
- `strands` have local IDs, titles, focus, shared person IDs, contextual works, source IDs, and `basis: editorial_distinction`. A strand may use a person whose roster context is elsewhere. Do not infer additional affiliations or edges.
- Stable IDs matter: `karl` = historical materialism; `marx` = Marxist social history. Hunt’s four core paradigms (`annales`, `marx`, `modern`, `identity`) are a teaching lens, not a universal importance ranking.
- All **708** current edges are classified: **62 influences, 439 contributions, 121 critiques, 86 comparisons**. All have explicit source references. Influence/contribution/critique are directed; critique points from critic to criticized position; comparisons are undirected.
- Missing direction metadata in an older/future record must still render as **unclassified**, not influence. Source references and `classification_basis: editorial_review` do not certify a claim. Preserve `relationship`, `evidence_note`, and optional short `map_label`.
- Source URLs may be null. Missing citations/verification remain unrecorded. Scoped statuses are `not_checked`, `bibliographic_metadata_checked`, `supporting_page_checked`; completed checks carry notes and dates. Do not use a green “verified history” badge.

## Editorial review: completed work and limits

Revisions 1.8–1.9 classified all 155 inherited unclassified edges individually, qualified broad claims, expanded thin rosters, and exposed full focused neighborhoods. All prior node, person, edge, and source IDs survive. Two inherited endpoint directions were corrected explicitly, with stable IDs: `edge_120` linguistic turn → queer history, and `edge_122` dependency/world-systems → global history (world-systems-specific). See review for scope.

Eleven shared people gained full nodes: Bloch, Febvre, Braudel, Labrousse, Dobb, Hilton, Torr, Hobsbawm, Hill, Tawney, Chartier. Seventeen new links are `edge_315`–`edge_331`. Tawney remains an external interlocutor of the British Marxists; Annales’ links distinguish founders, generations, methods, and reception. Economic history’s seven approaches distinguish historical economics, British economic/social history, French serial history, capitalist development, cliometrics, institutional change, and slavery/empire. Modernization, Indigenous history, Black history, oral history, and new social history also received explicit roster expansions.

**Completed editorial/display review is not complete historical verification.** Of 805 sources, 691 have scoped supporting-page checks, 78 metadata checks, 9 are marked not checked, and 27 have unrecorded verification. No current roster selection lacks a contextual work string. Some inherited influence claims explicitly need stronger passage/reception evidence. The preserved baseline audit and current enrichment records distinguish source limits from substantive review progress. Tests prove display and structural consistency, not completeness of a canon or historical truth.

The user now explicitly prioritizes repeated substantive passes through the knowledge graph. Content depth takes priority over optional interface refinements such as side-by-side comparison. Preserve source limits rather than quietly upgrading verification statuses.

## Next work: iterative enrichment of the whole graph

Work through every school, tradition, field, method, and individual entry in manageable, documented batches. Use the existing audit as the starting inventory. Keep a persistent pass log with reviewed IDs, actual changes, unresolved questions, and the next batch so a context reset does not restart the review or repeatedly revisit only the most prominent hubs.

For each entry, examine:

1. **People:** Which central historians or intellectual contributors are missing? Distinguish founders, later generations, interlocutors, critics, and internal disagreements. Check substantive and regional breadth; a nonempty roster is not evidence of adequate coverage.
2. **Works and arguments:** Supply contextual works, dates, historical questions, evidence, and explanatory methods. All 70 baseline empty selections are filled; continue checking whether contextual works explain why a person matters here. Adding names alone is insufficient.
3. **Internal distinctions:** Identify different programmes, generations, and approaches hidden by umbrella labels. Use explicit nested approaches where helpful, preserving overlap and links across groups.
4. **Incoming connections:** Identify specific intellectual resources, methods, institutions, collaborations, and debates that shaped the entry. Name the people and mechanisms involved rather than relying on generic field-to-field arrows.
5. **Outgoing connections:** Trace later adaptations, productive inheritances, criticisms, and exchanges. Revisit neighboring entries when a new connection exposes an omission. A sparse or empty lane is a research prompt, not proof of no influence and not a reason to invent edges.
6. **Evidence and interpretation:** Check relationship direction and whether the claim is influence, contribution, critique, or comparison. Research substantive additions with appropriate scholarly sources; record exactly what was checked and retain uncertainty where reception evidence is incomplete.

After each coherent batch, preserve a snapshot, retain IDs and qualifications, update revision notes and the pass log, validate data and references, and rebuild only the allowlisted public files. No further frontend design or visual checks are required under the current user direction.

Repeat the pass: new historians and connections can reveal gaps in entries already visited. Judge progress by explanatory depth and defensible relationships, not node/edge counts or a claim that every field has received one check. The pass log is established in `ENRICHMENT-PASSES.md` and `feedback/enrichment-pass-log.json`. **All 109 baseline entries are reviewed; the bounded second pass remains.** Neighboring edits alone do not mark an entry reviewed.

Revision 1.105 applies the user-approved wider correction: Quantitative history now reads “1950s–70s expansion · coverage through 2000.” All 66 group entries explicitly distinguish the map’s coverage through 2000 from dates of emergence, expansion, reception, works or institutions. Sixty-five date labels updated; Black history already corrected in 1.104. All 43 individual entries retain their dates and other content. The 2000 boundary describes this atlas, not termination of an ongoing field, and does not assert exhaustive coverage.

Current totals remain 109 entries, 708 relationships, 805 sources, 797 people, 1230 selections and 685 approaches across 66 groups. First pass complete; 48 second-pass outcomes, five completed before capture and 187 pending. Date corrections do not resolve unrelated queue questions. Next: followup 049 Ranger colonial traditions and reconsideration, then remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests and eight JavaScript checks passed. Exact 65-field preservation audit, 66/66 group coverage labels, all 109 dated entries, unchanged individual nodes and frozen baseline checked. Six public files rebuilt and byte-identical to inputs. No frontend design/code changes, browser review, deployment or OpenAlex. Manifest: `feedback/group-date-coverage-v1.105.json`. Both 1.105 scripts complete; do not rerun. No active process. No 1.106 mutation/snapshot.

## Historical decisions that must survive

- Fanon, Rodney, C. L. R. James, and Eric Williams retain distinct individual entries and arguments. James includes _Beyond a Boundary_ as well as _The Black Jacobins_. Do not equate all four positions or treat Black/anti-colonial histories as merely applications of European theories.
- All twelve requested women have individual entries: `ivy_pinchbeck`, `alice_clark`, `mary_ritter_beard`, `julia_cherry_spruill`, `lucy_maynard_salmon`, `eleanor_flexner`, `barbara_tuchman`, `eileen_power`, `cv_wedgwood`, `frances_yates`, `helen_maud_cam`, `dorothy_thompson`.
- Women’s history predates its 1960s expansion. Women also contribute across substantive fields, not exclusively to women’s history. Dorothy Thompson links class, women’s popular politics, and feminist debate without a simple abandonment of class.
- Power’s direction of Pinchbeck’s research has support in Pinchbeck’s original preface. Tuchman/Wedgwood illustrate narrative continuity before Stone’s 1979 essay. Yates’s mnemonic arts differ from collective-memory studies and Cambridge contextualism.
- Eley/Blackbourn are critics of Sonderweg, not adherents. Bielefeld, Sonderweg, and Historikerstreit remain distinct. A 1984 book cannot document the 1986–87 controversy. Stone 1979 cannot anticipate White 1973. African historical scholarship does not begin with postwar university recognition.
- Thompson/gender edges `edge_311`–`edge_314` separate Marxist social history → gender contribution, E. P. Thompson → culture contribution, Thompson → gender contribution, and gender → Thompson critique. `edge_050` and `edge_117` retain their historical-materialism and feminist-critique qualifications. The combined gender/racial-formation node’s notes restrict the Thompson claims to gender history.
- Barbara Taylor’s 2024 participant account, Scott 1986 pp. 1059–60, and Thompson’s later postscript support bounded parts of that relationship. The postscript mentions 1979 publications despite its archive’s 1978 heading; do not date it to 1978. Publisher metadata is not full-book verification.

## Build, preview, and validation

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory site/dist
```

A preview at **http://127.0.0.1:4173/** ran during an earlier implementation stage; current availability is unconfirmed. No public deployment has occurred. Useful links: `#node=science&section=connections`, `#node=marx&section=connections`, `#node=annales&section=connections`, `#node=economic`, `#person=eric_hobsbawm`.

Revision 1.9 baseline checks passed on 2026-09-10 (current revision checks are recorded below):

- `python3 scripts/validate_graph.py`: **0 errors, 0 warnings**.
- `python3 -m unittest tests.test_graph_validation tests.test_people_validation -q`: **14 passed**.
- `node tests/test_site_core.mjs`: **8 passed**.
- `python3 -m unittest tests.test_site_browser -v`: **9 passed**, including all 109 entries, 228 person profiles, 13 pathways, every focused edge set and all 66 core rosters; sources, branches, direction, filters, history, keyboard activation, mobile overflow, and public-file checks.
- Prior-ID preservation checks passed, with only the two documented endpoint reversals. All earlier snapshots are preserved.

Browser tests use installed Python Playwright and Chromium; bind/Chromium required sandbox escalation. This is not a cross-browser or full screen-reader audit. Screenshots are in ignored `site/test-results/`, outside the public build. See `site/README.md` for details.

## Historical revision 1.10 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 237 profiles, every focused edge set and core roster, and 13 pathways. The six-file build was rebuilt and science’s expanded connection view inspected. Preview was restarted on port 4173. Exact before/after records and validation are in `feedback/enrichment-science-v1.10.json`. These checks establish display and reference consistency, not historical completeness.

## Historical revision 1.11 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 239 profiles, every focused edge set and core roster, and 13 pathways. A focused browser inspection additionally checked both expanded four-approach views, all three new exchanges, and the six-row historical-economics mobile view without document overflow. The desktop connection screenshot was visually inspected. The allowlisted six-file site is rebuilt and the port-4173 preview responded. Exact evidence and limitations are in `feedback/enrichment-economic-roots-v1.11.json`.

## Historical revision 1.12 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 246 profiles, every focused edge set and core roster, and 13 pathways. Focused browser inspection checked geography’s four approaches, environment’s eight, all four new connections and both complete mobile relationship lists without document overflow. The environmental connection screenshot was visually inspected. The allowlisted six-file site is rebuilt and the port-4173 preview responded. Exact evidence and limitations are in `feedback/enrichment-geography-environment-v1.12.json`.

## Historical revision 1.13 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 254 profiles, every focused edge set and core roster, and 13 pathways. Focused inspection checked economic history’s eleven approaches, consumption’s eight, all four new connections, Polanyi’s critic role and all three affected mobile relationship lists without document overflow. Consumption’s connection screenshot was visually inspected. The allowlisted six-file build is current and port 4173 responded. Exact evidence and limitations are in `feedback/enrichment-economic-consumption-v1.13.json`.

## Historical revision 1.14 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 264 profiles, every focused edge set and core roster, and 13 pathways. Focused inspection checked seven quantitative approaches, six demographic/family approaches, all five new connections, Benson/Gutman critic roles and five affected mobile relationship lists without document overflow. The quantitative connection screenshot was visually inspected. Exactly six public files are rebuilt and port 4173 responded. Exact records and limits: `feedback/enrichment-quant-demography-v1.14.json`.

## Historical revision 1.15 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python and 8 JavaScript checks passed; all 9 Chromium scenarios passed across 109 entries, 266 profiles, every focused edge set and core roster, and 13 pathways. Focused inspection checked eight political approaches, seven social approaches, all eight new connections, Scott’s critic profile and seven affected mobile relationship lists without document overflow. The political connection screenshot was visually inspected. Exactly six public files are rebuilt. Exact records and limits: `feedback/enrichment-political-social-v1.15.json`.

## Historical revision 1.16 validation

Completed 2026-09-11: zero structural errors/warnings; 14 Python, 8 JavaScript and all 9 Chromium scenarios passed across 109 entries, 271 profiles, complete focused connections/rosters and 13 pathways. Focused checks covered nine comparative-sociology and five German-history approaches, seven new links, Sewell/Lüdtke critic roles and seven affected mobile relationship lists without document overflow. Comparative connections and German approaches screenshots were visually inspected. Exactly six allowlisted public files rebuilt; no deployment. Exact records: `feedback/enrichment-comparative-german-v1.16.json`.

## Historical revision 1.17 validation

Completed 2026-09-11: zero structural errors; one expected legacy endpoint/type warning for the deliberate anthropology comparison/contribution pair (`edge_041`, `edge_369`). All 14 Python, 8 JavaScript and 9 Chromium checks passed, covering 109 entries, 281 profiles, all focused connections/rosters and 13 pathways. Focused inspection checked six microhistory and eight oral-history approaches, six new links, comparison/contributor profiles and seven affected mobile lists without overflow. Both desktop connection screenshots were visually inspected. Exact manifest and preservation checks passed; precisely six public files rebuilt. No deployment. Exact record: `feedback/enrichment-micro-oral-v1.17.json`.

## Historical revision 1.18 validation

Completed 2026-09-11: zero structural errors and the one existing anthropology/microhistory comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium checks passed across 109 entries, 288 profiles, complete connections/rosters and 13 pathways. Focused inspection checked sixteen approaches, four new connections, two clarified links, critical-intervention/contributor profiles and eight affected mobile lists without overflow. Both desktop connection screenshots were visually inspected. Exact manifest and preservation checks passed; six public files rebuilt. No deployment. Exact record: `feedback/enrichment-memory-workshop-v1.18.json`.

## Historical revision 1.19 validation

Completed 2026-09-11: zero structural errors and the one existing anthropology/microhistory comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium checks passed across 109 entries, 297 profiles, complete connections/rosters and 13 pathways. Focused inspection checked seventeen approaches, six new links, contextual profile qualifications and eight affected mobile lists without overflow. Both desktop connection screenshots were inspected. Visual review prompted a chronology clarification: `edge_224` retains the representation debate as its main contribution; Broszat 1977 is explicitly an earlier methodological comparison, not a response to postmodernism. The focused check passed again after that text change. Exact manifest/preservation checks passed; six public files rebuilt. No deployment. Record: `feedback/enrichment-nations-holocaust-v1.19.json`.

## Public assets and paused work

**Serve only `site/dist`, never the repository root.** The exact six public files are `index.html`, `styles.css`, `app.js`, `core.mjs`, `data/graph.json`, and `data/pathways.json`. No documentation, audit files, tests, screenshots, credentials, or unrelated files are copied. The frontend needs no database, network API, or secret.

The local OpenAlex credential is in `openalex-api-key.txt`, ignored and owner-only. Never read it into conversation, copy it to memory, or place it in browser/deployment assets. No credential was needed or accessed for this review.

OpenAlex remains explicitly paused. Retain `scripts/openalex_ingest.py`, `scripts/journal_citations.py`, `openalex-plan.json`, `journal-panel.json`, `.cache/openalex/`, and `data/journals/`. Coverage limits are documented in `data/journals/REPORT.md`; do not restart the investigation as a prerequisite for visualization work.

Resume prompt: **“Read MEMORY.md, then continue systematic passes through the knowledge graph, fleshing out key historians, works, internal approaches, and incoming/outgoing connections. Track progress across every entry and keep the nested visualization current.”**

## Historical revision 1.20 validation

Completed 2026-09-11: zero structural errors and the existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium checks passed across 109 entries, 303 profiles, complete focused connections/rosters and 13 pathways. Focused inspection checked fifteen approaches, eight new links, critic/contributor profiles and nine affected mobile lists without overflow. Both desktop connection screenshots were visually inspected. The exact manifest and ID/prose preservation checks passed; exactly six public files rebuilt. No deployment. Exact record: `feedback/enrichment-post-subaltern-v1.20.json`.

## Historical revision 1.21 validation

Completed 2026-09-11: zero structural errors and the existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium checks passed across 109 entries, 312 profiles, complete focused connections/rosters and 13 pathways. Focused inspection checked seventeen approaches, five new links, contributor profiles and nine affected mobile lists without overflow. Both desktop connection screenshots were visually inspected. The exact manifest and ID/prose preservation checks passed; exactly six public files rebuilt. No deployment. Exact record: `feedback/enrichment-africa-anticolonial-v1.21.json`.

## Historical revision 1.22 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered both individual scopes, five new links, three neighboring selections and seven mobile lists without overflow. Both desktop screenshots visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph identical to authoritative JSON. No deployment. Exact record: `feedback/enrichment-fanon-rodney-v1.22.json`.

## Historical revision 1.23 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered both individual scopes, five new links, five selections and eight mobile lists without overflow. Both desktop screenshots visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph identical to authoritative JSON. No deployment. Exact record: `feedback/enrichment-james-williams-v1.23.json`.

## Historical revision 1.24 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered revised connections, three filled-work profiles, four neighboring selections, both approach lists, corrected help text and seven mobile lists without overflow. Both desktop screenshots visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-black-atlantic-v1.24.json`.

## Historical revision 1.25 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered complete 23/20 core rosters, new/revised links, four filled-work profiles, 9/8 approaches, three neighboring selections and seven mobile lists without overflow. Both desktop screenshots visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-women-gender-v1.25.json`.

## Historical revision 1.26 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered complete 9/14 core rosters, new/revised links, five contextual-work profiles, 6/9 approaches, four neighboring selections and nine mobile lists without overflow. Both desktop screenshots visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-identity-queer-v1.26.json`.

## Historical revision 1.27 validation

Completed 2026-09-11: zero structural errors, one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. Focused checks covered complete 12/15 core rosters, new/revised links, five contextual-work profiles, 9/10 approaches, four neighboring selections and ten mobile lists without overflow. Both desktop screenshots visually inspected; focused and broad browser checks passed after correcting the provisional New Left endpoint. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-indigenous-cultural-v1.27.json`.

## Historical revision 1.28 validation

Completed 2026-09-11: zero structural errors and the one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. A focused scenario checked the complete 28-person anthropology core roster, new/revised links across three reviewed views, five contextual-work profiles, seventeen approaches, three neighboring selections and eight complete mobile lists without overflow. Three desktop connection screenshots and the anthropology approaches screenshot were visually inspected. The initial focused-test invocation used an invalid module path; rerunning from /tmp passed. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-anthropology-v1.28.json`.

## Historical revision 1.29 validation

Completed 2026-09-11: zero structural errors and the one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. A focused scenario checked the complete 9/7-person core rosters, 8/7 approaches, five contextual-work profiles, new/revised links and nine complete mobile lists without overflow. Both desktop connection screenshots were visually inspected. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-linguistics-durkheim-v1.29.json`.

## Historical revision 1.30 validation

Completed 2026-09-11: zero structural errors and the one existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. A focused scenario checked Annales/Bloch/Febvre, the complete eighteen-person Annales roster, eleven approaches, six contextual-work profiles, eight new links and ten complete mobile lists without overflow. Three desktop connection screenshots visually inspected. The initial focused failure was a comparison-card selector error, corrected without application changes. Exact manifest and preservation checks passed; six allowlisted public files, graph/app identical to authoritative inputs. No deployment. Exact record: `feedback/enrichment-annales-founders-v1.30.json`.

## Current revision 1.31 validation

Completed 2026-09-11: zero structural errors and the existing comparison/contribution warning. All 14 Python, 8 JavaScript and 9 Chromium scenarios passed. One focused scenario checked all sixteen new links in Braudel/Labrousse/Chartier’s complete neighborhoods, economic/technology/Annales approach counts, seven contextual-work profiles and thirteen complete mobile lists without overflow. Three desktop connection screenshots visually inspected. An initial absolute-path unittest invocation failed import before running; corrected module invocation passed. Exact manifest and preservation checks passed; six allowlisted public files, graph/app byte-identical to authoritative inputs. No deployment. Record: `feedback/enrichment-annales-successors-v1.31.json`.


## Historical revision 1.32 validation

Completed 2026-09-11: zero structural errors and the one documented comparison/contribution warning; 14 Python, 8 JavaScript, 9 broad Chromium and one focused scenario passed. Focused checks cover all sixteen new exchanges, Marx/economic/technology approaches, seven new work profiles and thirteen complete mobile lists. Three desktop connection screenshots inspected. Sandbox initially blocked the focused browser; escalation allowed it to start. Its initial selector wrongly expected comparison cards in directed lanes; corrected selector passed. Exact manifest, prior IDs/prose/strand IDs, all prior endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; public graph/app byte-identical to inputs. No deployment.


## Historical revision 1.33 validation

Completed 2026-09-12: zero structural errors and the documented comparison/contribution warning; 14 Python and 8 JavaScript checks passed during implementation, followed by 9 broad Chromium and one focused scenario. Focused checks cover all nineteen new exchanges, six approach counts, nine new work profiles and thirteen complete mobile lists. Three desktop connection screenshots inspected. Both browser suites passed their first run for this batch. Exact manifest, prior IDs/prose/strand IDs, all prior endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; public graph/app byte-identical to inputs. No deployment.


## Historical revision 1.34 validation

Completed 2026-09-12: Zero structural errors and one documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium checks passed. One focused scenario checked all twenty-one new links, five approach counts, eleven new work profiles and eighteen complete mobile neighborhoods without overflow. Three desktop screenshots visually inspected. Initial focused invocation failed module resolution; corrected discovery passed. Exact manifest, prior IDs, original prose, existing strand IDs, endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; public graph/app byte-identical to inputs. No deployment.


## Historical revision 1.35 validation

Completed 2026-09-12: Zero structural errors and one documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium checks passed. One focused scenario checked all ten new links, three approach counts, eight new profiles and nine complete mobile neighborhoods without overflow. Three desktop screenshots visually inspected. Its initial biography count was corrected from three to two; the corrected scenario passed. Exact manifest, prior IDs, prose, strand IDs, endpoints/classifications and protected edges preserved. Exactly six public files rebuilt, byte-identical graph/app inputs. No deployment.


## Historical revision 1.36 validation

Completed 2026-09-12: Zero structural errors and the existing comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium scenarios passed. One focused scenario checked eleven new links, four approach counts, seventeen new profiles and eleven complete mobile neighborhoods without overflow. Three desktop screenshots visually inspected. Its initial Aylmer wording expectation was corrected from documents to documentary access; the corrected scenario passed. Exact manifest, prior IDs, original prose, strand IDs, endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; graph/app byte-identical to inputs. No deployment.


## Historical revision 1.37 validation

Completed 2026-09-12: Zero structural errors and the documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium scenarios passed. One focused scenario checked all twelve new links, four approach counts, thirteen new profiles and twelve complete mobile neighborhoods without overflow. Three desktop views visually inspected. Both browser suites passed their first run; focused checks passed again after a minor scope wording edit. Exact manifest, prior IDs, original prose, strand IDs, endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; graph/app byte-identical to inputs. No deployment.


## Historical revision 1.38 validation

Completed 2026-09-12: Zero structural errors and the documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium scenarios passed. One focused scenario checked all nine new links, four approach counts, eleven new profiles and ten complete mobile neighborhoods without overflow. Two desktop views visually inspected. Broad and focused browser suites passed their first run (24.229 seconds and 1.962 seconds). Exact manifest, prior IDs, original prose, strand IDs, endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; graph/app byte-identical to inputs. No deployment.


## Historical revision 1.39 validation

Completed 2026-09-12: Zero structural errors and the documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium scenarios passed. One focused scenario checked all eight new links, six/nine approach counts, twenty new profiles, three filled-work profiles and nine complete mobile neighborhoods without overflow. Two desktop views visually inspected. Exact manifest, prior IDs, original prose, strand IDs, endpoints/classifications and protected edges preserved. Exactly six allowlisted files rebuilt; graph/app byte-identical to inputs. No deployment.


## Historical revision 1.40 validation

Completed 2026-09-12: Zero structural errors and one documented comparison/contribution warning; 14 Python, 8 JavaScript and 9 broad Chromium scenarios passed. A focused scenario checked eight new links, seven/twelve approaches, twenty new profiles, the filled Davis work and eight complete mobile neighborhoods. Two desktop views inspected. Exact manifest, stable IDs, original representative prose, prior endpoints/classifications and approach IDs preserved. Six allowlisted files rebuilt; graph byte-identical. These visual checks preceded the user’s instruction to focus exclusively on getting the data ready; no further frontend work is required. No deployment.


## Historical revision 1.41 validation

Completed 2026-09-12: Zero structural errors and the one documented edge_369/edge_041 warning; 14 Python validator tests and 8 JavaScript data/relationship checks passed. Exact manifest, prior IDs, original representative prose, existing approach IDs and prior edge endpoints/classifications preserved; protected edges unchanged. Exactly six allowlisted files rebuilt, public graph byte-identical. No frontend design or browser review performed under the user’s data-only direction; no deployment.


## Historical revision 1.42 validation

zero errors, one existing edge_369/041 warning; fourteen Python validator tests and eight JavaScript data/relationship checks passed. Exact preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. An overly broad test discovery accidentally started browser/unrelated tests, showed two failures and was interrupted; it is not claimed to pass and was not pursued. The explicit data-only suite passed. OpenAlex remains paused; no deployment.



## Historical revision 1.43 validation

zero errors, one existing edge_369/041 warning; fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.44 validation

zero errors, one existing edge_369/041 warning; fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.45 validation

zero errors, one existing edge_369/041 warning; fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.46 validation

zero errors, two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 each distinguish a comparison from a directed contribution); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.47 validation

zero errors, two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.48 validation

zero errors, two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.49 validation

zero errors, two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Preservation and six-file allowlist/build checks passed; public graph byte-identical. No frontend design or visual review. OpenAlex remains paused; no deployment.



## Historical revision 1.50 validation

Zero structural errors and two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Exact manifest/preservation checks passed, including all old IDs, prose, selections, approach IDs and edge endpoints/classifications. Exactly six allowlisted public files were rebuilt and each is byte-identical to its input. No frontend design, browser review, deployment or OpenAlex.


## Historical revision 1.51 validation

Zero structural errors and two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Exact manifest/preservation checks passed, including all old IDs, prose, selections, approach IDs and edge endpoints/classifications. Exactly six allowlisted public files were rebuilt and each is byte-identical to its input. No frontend design, browser review, deployment or OpenAlex.


## Historical revision 1.52 validation

Zero structural errors and two reviewed endpoint/type warnings (edge_369/041 and edge_610/163 distinguish comparisons from contributions); fourteen Python validator tests and eight JavaScript data/relationship checks passed. Exact manifest/preservation checks passed, including all old IDs, prose, selections, approach IDs and edge endpoints/classifications. Exactly six allowlisted public files were rebuilt and each is byte-identical to its input. No frontend design, browser review, deployment or OpenAlex.


## Historical revision 1.53 validation

zero structural errors and two previously reviewed comparison/contribution warnings;14 Python validator tests and8 JavaScript data checks passed. Exact preservation manifest and six-file allowlist/build byte checks passed. No frontend design, browser review, deployment or OpenAlex.


## Historical revision1.54 validation

zero structural errors and two reviewed endpoint/type warnings;14 Python validator tests and8 JavaScript data checks passed. Exact before/after manifest, preservation and six-file allowlist/build byte checks passed. No frontend design, browser review, deployment or OpenAlex. No active process.


## Historical revision 1.56 validation

zero structural errors, three reviewed warnings, 14 Python tests, eight JavaScript checks and exact preservation/manifest/six-file build checks. The additional edge_662/180 warning distinguishes Freud’s documented reading contribution from the preserved broad comparison. No frontend design, visual review, deployment or OpenAlex. Next: the final three first-pass entries. No active process. No 1.57 mutation or snapshot.


## Historical revision 1.57 validation

zero structural errors, three reviewed comparison/contribution warnings, 14 Python tests, eight JavaScript checks and exact preservation/manifest/six-file build checks. No frontend design, visual review, deployment or OpenAlex. No active process. No 1.58 mutation/snapshot.
