# Digital and web history: source recovery and entry drafts — batch 07

Continued research while Fable works on the website. **Six new works and thirteen new historical proposals**, combined with four unchanged claims and six work referents from recovery-02. The packet has twelve work referents, seventeen historical claims (fourteen selected-passage checks, three abstract checks), eleven author credits and two version links: thirty claims in total, all `needs_review`. Counts overlap earlier research and must not be summed as distinct additions. No production imports.

Two concrete [entry drafts](entry-proposals.json) propose separate Digital history and Web history / Archived-web research entries. They are partial selections with resolvable proposed sources and works, not drop-in production nodes. They do not equate digital history with computational history or all digital humanities. Histories of the web and histories using archived web evidence also remain distinguishable. Earlier roots and founding chronologies are unresolved.

## New source readings

| Work | Intervention | Reading and qualification |
| --- | --- | --- |
| Roy Rosenzweig, *Scarcity or Abundance?* | 2003 | Authorized RRCHNM transcription, opening discussion: abundance/loss and historians’ preservation responsibility. No present-day legal or preservation claims. |
| Stefania Gallini and Serge Noiret, *La historia digital en la era del Web 2.0* | 2011 | Spanish original, pp. 16–18: research/communication and historical/technical collaboration. English paraphrases; a Colombian dossier is not all Latin American practice. Both authors credited. |
| Jane Winters, *Web archives and (digital) history* | 2018 | Repository manuscript pp. 4–9: field boundaries and curatorial access. Manuscript pagination is separate from final chapter pp. 593–606. |
| Jessica Ogden and Emily Maemura, *‘Go fish’* | 2021 | Publisher HTML, introduction and §§3–3.2: overlapping research practices and the constraints of UK/Danish archive infrastructures. Fieldwork dates to 2018; these are not current access instructions. |
| Kieran Hegarty, *Web archives after platformization* | 2024 online; 2025 issue | Indexed author abstract: Australian library collection strategies and explicit use of Ann Stoler’s archival-grain approach. Direct body access failed; no body-check upgrade. |
| Leisa Gibbons, *Mediated recordkeeping and epistemic accountability* | 16 June 2026 | Publisher introduction, limitations and conclusion: evidence-making processes and limits of technical accountability. The paper explicitly attributes the model to earlier doctoral research; 2026 is not its origin. |

The new thirteenth proposal uses Sharon M. Leon’s 2018 chapter, paragraphs on institutional status and collaborative labour, to explain exclusion from digital-history narratives. Her already-staged critique of Thomas and the documented 2020 AHR revision response remain exact. This packet does not independently reproduce Leon’s grant counts or use them as a demographic benchmark.

Kim Gallon’s programme and Lara Putnam’s source-searching claim retain their original IDs, statements, review states and evidence. Three earlier works gain explicit author/date/navigation metadata with complete old records saved in [review-actions.json](review-actions.json). Putnam’s full article again returned an access error; its earlier abstract-only citation is unchanged. The other three reused work referents are Thomas’s chapter, the AHR review-stage draft and its authors’ response, not newly read or newly authored works.

Primary witnesses: [Gallini/Noiret](https://biblat.unam.mx/hevila/HistoriaCriticaBogota/2011/no43/1.pdf), [Rosenzweig](https://rrchnm.org/publications/scarcity-or-abundance-preserving-the-past-in-a-digital-era/), [Winters repository](https://sas-space.sas.ac.uk/9202/), [Ogden/Maemura](https://link.springer.com/article/10.1007/s42803-021-00032-5), [Hegarty publisher abstract](https://www.tandfonline.com/doi/abs/10.1080/1369118X.2024.2420033), [Gibbons](https://link.springer.com/article/10.1007/s10502-026-09550-z) and [Leon](https://dhdebates.gc.cuny.edu/read/untitled-4e08b137-aec5-49a4-83c0-38258425f145/section/53838061-eb08-4f46-ace0-e6b15e4bf5bf). Evidence joins carry the precise locators and limits; a linked work is never implicitly a whole-work reading.

## Entry and chronology decisions

The two candidate-field rows now record **separate entry drafts pending review**, with period-specific selected works. Other candidate rows and all 75 existing-topic rows are preserved. The digital-humanities row receives Gallon’s work as partial research; it does not inherit an approved field decision. Computational history is unchanged. No field is complete through the September 2026 cutoff.

The drafts keep `work_publication_year` separate from `intervention_years` on each strand. Leon’s 2018 work has a documented 2020 reception claim; collapsing both to the publication year would misdate the exchange. Hegarty’s online/issue distinction and Winters’s manuscript version have separate `realizes` assertions. Rosenzweig’s page footer dated 2026 is not the date of his 2003 intervention.

Eleven credited people appear: Rosenzweig reuses a production identity; Gallini reuses her batch-04 identity; nine are new local research identities. No QIDs, life dates or demographic attributes are accepted. Archival/information researchers appear as contextual contributors, not automatically as professionally credentialed historians. [Representation review and follow-ups](representation-review.json) records selection reasons, concrete omissions and remaining geographic/language gaps.

## What remains before accepting these entries

1. Reconcile the earlier breadth works by Romein and coauthors, Milligan and Brügger with these drafts, including complete author credits and their currently narrower evidence. These are retained research, not rejected contributors.
2. Resolve earlier roots and the relationship to quantitative/computational and public history without inventing a single founding event or influence arrow. Review the proposed separate-entry boundaries.
3. Continue named contributors recovered through Leon and broader regional/original-language surveys. One Spanish dossier and English-language Australian/European archive studies do not constitute global coverage.
4. Map the reviewed claims, shared people and [proposed bibliography records](source-proposals.json) through a production adapter after acceptance. The medical/geographical candidate 06 is unchanged and can proceed independently.

Keep the broader rotation moving: next review borderlands and disability/newer-field gaps while retaining this packet’s source-recovery queue. OpenAlex remains paused.

## Verification

```bash
python3 scripts/build_digital_web_batch.py
python3 scripts/build_digital_web_batch.py --check
python3 -m unittest tests.test_digital_web_batch
```

Eight tests pass: contract and pinned-input validation, exact prior-claim preservation, all coauthor credits, manuscript/issue chronology, distinct field drafts, unaffected coverage and the separate 2018 publication/2020 reception dates. Raw captures are tool extractions, not original HTML or proof that every returned passage was read. Source hashes verify both new captures and the older `sha256` form. Earlier packets remain unchanged.

The production baseline is pinned; if Fable accepts another batch concurrently, validation may resolve the exact old hash against its preserved revision snapshot. It never resets the baseline to changed live data. Website assets and mutable authority enrichment are outside this research baseline; no website edits, public build or deployment were performed here.
