# Independent review of the first LOD harvest

Reviewed 18 September 2026. Scope: the completed pilot, miner, summarizer, plan, existing tests, current project instructions and ontology proposal. Read-only review of harvested data; no accepted data or code changes.

**Verdict: usable for discovery, inspection and building a review queue. It is not yet an accepted graph of historians’ specialisms, a count of new works, or a basis for comparing field size or productivity.** The conservative staging design makes it possible to improve the data without losing the original observations. No critical corruption or fabricated source statements were found in the checks completed.

## What the harvest teaches us

- Multiple discovery routes and explicit controls are necessary. Scott enters the target discovery results through labour history but her retained control retrieves three recent records. This repairs discovery coverage; those three records do not themselves establish her gender-history specialism.
- Source categories need substantive review. Andrew H. Knoll (Q505705) enters environmental history through Wikidata P101. His harvested bibliography includes geobiology and planetary history, and three recent records concern *A Brief History of Earth* and its French translation. They are real source links; whether they fit this project’s environmental-history concept is a separate decision. Michael Schmidt (Q125372009) links to an IdRef authority labelled “ingénieur” and environmental-management publications. This is an identity/disciplinary-fit review lead, not a demonstrated mistaken identity.
- Catalogue subjects are useful discovery vocabulary but do not consistently identify author specialisms. Their value lies in finding and comparing records, followed by concept mapping and interpretation.
- The contemporary window captures circulation as well as new research: translations, reissues, special issues, series and academic dossiers occur together. Recent catalogue dates cannot supply original-work dates.

## Severity-ranked findings

### P2 — Birth-year comparison discards source date precision (implementation limitation)

`scripts/mine_lod.py`, `identity_flags()` and the `people_*` queries retrieve direct P569 values and compare their first four digits. Wikidata time precision and calendar metadata are not retrieved. George Bryan Souza (Q106647718) has `1900-01-01T00:00:00Z`; Anne Balay (Q117767676) has `1901-01-01T00:00:00Z`. These values must not be interpreted as independently verified exact birth years. The current cache cannot establish their precision.

**Current impact:** no birth-conflict flag was generated, so no erroneous rejection was demonstrated. Only 55 of 91 identity links have parseable year values on both sides even before considering missing Wikidata precision. “Zero conflicts” is therefore weak evidence, not identity validation.

**Next step:** fetch statement-level birth precision/calendar metadata when reviewing identities; compare compatible intervals, and preserve “unknown precision” until then. Keep every identity link under review.

### P3 — Twenty-five subject-label observations omit additional provenance links (verified defect)

In the subject loop, `observe(subject, skos:prefLabel, ...)` is called only when the label has not previously been added to that subject’s list. When a later batch returns the same label, its request ID is omitted from the observation.

I independently reconstructed the exported triples from all 59 raw packages. All **15,028** distinct expected triples are present, and every listed source request supports its triple. **25 observations** nevertheless have incomplete supporting-request lists. This does not fabricate evidence or remove it from the raw cache, but the exported provenance is incomplete.

**Next step:** call `observe()` for every returned label row while separately deduplicating display labels; add a test where the same subject label appears in two request batches. Multiple batches from one endpoint must still not be counted as independent scholarly corroboration.

### P3 — Thesis exclusion wording is broader than the query implements (scope documentation)

The plan says “theses and other linked corpora are out of scope.” The query excludes other URI corpora, but it does not filter bibliographic types inside Sudoc. The all-period data include Dolléans’s explicitly titled doctoral thesis, Sudoc **117692433**. The recent data include Fontaine’s 2021 habilitation dossier, **27852589X**. Thus the statement is defensible as a restriction on external corpora, not as exclusion of thesis-like content.

**Next step:** clarify the distinction and classify Sudoc resource types before any publication-only export. Retaining these records as discovery evidence is useful.

## Documented limits that are material, not new defects

- **Identity:** Linda Gale Jones (Q134285134) has two IdRef identifiers, 174631510 and 261809237; both require reconciliation. David Brody (Q5231769; 085716553) has no returned authority label. The three flags affect two people. Missing labels do not establish invalid identifiers, and matching labels do not establish identity. All links appropriately remain `needs_review`.
- **Works, editions and roles:** Davis’s **252657071** is an ongoing series with editorial-board credit. Souza’s **27241638X** is another series. Scott’s **271458526** is a special issue with editorial credit. Soluri’s **280993439/283415975** have identical *Banana Cultures* citations; Klapper’s **243277059/248840800** are another likely edition/format reconciliation pair. Do not deduplicate on title alone or count these as distinct new works. Retaining raw role URIs is correct; credit lists cover only sampled authorities.
- **Dates and coverage:** 87 records have one structured year in 2020–2026; only three carry 2026. Another 387 of the 1,903 records lack structured dates. They cannot be classified as outside the window. Exact-year filtering is appropriately cautious but incomplete; catalogue dates do not prove publication or date a person’s field affiliation.
- **Selection:** the 90-person sample requires IdRef links, uses fixed quotas and hashed QIDs, and includes historical/deceased people. It is reproducible convenience sampling. The broad gender route additionally requires exact historian occupation, unlike the narrow routes. These unequal selection rules preclude category-size comparisons. Thirty people per group do not supply representative coverage.
- **Source assertions:** Wikidata direct properties omit statement references, ranks and qualifiers. The cache proves what the endpoint returned, not the underlying scholarly basis or historical validity of a classification. Further statement-level retrieval is needed before an accepted interpretation.
- **Reproduction:** raw caches and exact queries support replay. The run fingerprints inputs but does not pin miner/summarizer code or runtime in its manifest. Archive code hashes and the dirty working-tree state before relying on long-term reproducibility.

## Completed checks and strengths

Reviewed all 91 identity rows and all 87 recent citations, sampled other bibliographic records, and inspected candidate-selection/date/identity/provenance logic. Independently checked all exported triples against raw caches as described above. The largest cached query returns 718 rows, well below its 9,999-row limit; no observed batch approached a cap. This is evidence against configured-limit truncation, not proof that an endpoint returned its entire underlying corpus.

The harvest keeps source URIs, raw literals and role predicates; avoids title-derived publication years; distinguishes missing dates; keeps authorities separate from Wikidata people; marks observations unreviewed; and makes no subject-to-specialism, authorship-to-influence or roster-to-membership inference. These are sound safeguards aligned with the proposed ontology.

The existing audit/reproducibility files report hash verification and a byte-identical offline rebuild; I read those results but did not independently rerun the complete miner or test suite in this review. The parent reviewer separately verified protected inputs. No live endpoint verification, exhaustive identity adjudication, detailed resource-type retrieval or scholarly validation was completed. Those remain explicit limits.

## Prioritized next steps

1. Reconcile Jones and Brody, and review Schmidt’s identity/disciplinary fit. Add precision-aware birth checks before accepting matches.
2. Fix the 25 missing provenance links and clarify the corpus/type scope wording.
3. Classify the 87 recent resources; resolve a small set of work/version/publication pairs and contribution roles before expanding the harvest.
4. Review environmental, gender and labour concept mappings against multilingual subjects and the known control cases. Keep subject assignments and interpreted person–field connections as separate claims.
5. Pin code with each run and define comparable coverage measures before increasing sample size. Use this harvest as an evidence inventory, not a ranking.
