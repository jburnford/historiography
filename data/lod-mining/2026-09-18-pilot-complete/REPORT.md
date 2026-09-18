# First LOD mining harvest

This is source-observation staging, not accepted scholarly classifications or a new atlas release.

Completed 2026-09-18T02:57:11.012442+00:00. Queries have individually recorded retrieval times; the endpoints are not one synchronized snapshot.

## What was harvested

- **777 distinct discovery candidates**, plus inherited atlas matches and controls: **819 people** in total.
- **90 sampled people**, through **91 IdRef authority identifiers**.
- **1,903 Sudoc bibliographic resources** across all returned years for those identifiers and the specified contribution roles.
- **87 records with a structured year in 2020–2026**, of which **87** have one unambiguous exact year.
- **82 recent records have subject links**, spanning **218 distinct subject identifiers**.
- **15,028 deduplicated source statements** with query-level provenance; **59 successful queries**.

Records are not deduplicated intellectual works. Translations, reissues, different formats and cataloguing duplicates can all increase these counts. Continuing series and editorial-board records can also appear: Davis’s 2020 Early Modern Cultural Studies record is one example. Resource types and contribution roles need review before counting books or original scholarship. Year 2026 is partial; a catalogue year does not prove an item has already been released.

## Discovery and sampling

| Discovery route | Distinct candidate people |
| --- | ---: |
| environmental_history | 255 |
| labour_history | 102 |
| gender_history | 129 |
| gender_adjacent | 301 |

Routes overlap. Narrow fields use P101 or P106→P425; broad gender/women’s studies additionally require the exact historian occupation. The broad route is explicitly adjacent-field discovery, not a gender-history membership assertion.

The 42 previously accepted atlas–Wikidata identities were carried forward as an identity baseline, not re-matched by name. The other atlas people have not yet been systematically reconciled. Scott, Davis and Clifford are explicit controls. No absence from a field query excludes a control.

For bibliographies, select available controls then fill each 30-person theme quota using a fixed SHA-256 ordering of QIDs. This is reproducible convenience sampling of linked records, not a representative sample of historians, languages, living scholars or contemporary field activity.

| Sample group | People sampled | People with recent records | Recent records | With sampled author role |
| --- | ---: | ---: | ---: | ---: |
| environmental_history | 30 | 12 | 19 | 13 |
| labour_history | 30 | 12 | 33 | 24 |
| gender_history_and_adjacent | 30 | 15 | 35 | 15 |

Sample groups and publications can overlap. These columns describe the selected identifiers, not the total output of a field. Control-group placement is not a new field assignment.

## What happened to the controls

### Joan Wallach Scott (Q291798)

Discovery cohorts: labour_history. Recent linked records: 3. These links remain identity candidates until reviewed.

- 2022: [Psychoanalysis and history  / Brian Connolly and Joan Wallach Scott,special issue editors / [Durham (North Carolina)] : Duke University Press , 2022](http://www.sudoc.fr/271458526). Subjects: Complexe d'Oedipe; Psychanalyse; Psychanalyse et politique; Historiographie; Traumatisme psychique.
- 2020: [On the judgment of history  / Joan Wallach Scott / New York : Columbia University Press , 2020](http://www.sudoc.fr/256830967). Subjects: Philosophie de l'histoire; Historiographie; Nationalisme; Racisme; Nuremberg, Procès de (1945-1946).
- 2020: [In the name of history  / Joan Wallach Scott / Budapest : Central European university press , 2020](http://www.sudoc.fr/263655423). Subjects: Philosophie de l'histoire.

### Natalie Zemon Davis (Q266185)

Discovery cohorts: none; retained as a control. Recent linked records: 4. These links remain identity candidates until reviewed.

- 2022: [Le retour de Martin Guerre  / Natalie Zemon Davis  / Alexandre Dumas  ; préface de Carlo Ginzburg / Paris : Tallandier , DL 2022](http://www.sudoc.fr/261615114). Subjects: Ariège (France); Conditions morales; Conditions sociales; Imposteurs et impostures; Guerre, Martin (15..-1599).
- 2022: [Œuvres  / [Louise] Labé  ; présentation, notes, dossier, index et bibliographie de Michèle Clément et Michel Jourde  ; [avant-propos de Natalie Zemon Davis]/ [Nouvelle édition] / Paris : Flammarion , DL 2022](http://www.sudoc.fr/26222738X). Subjects: Poésie française -- 16e siècle.
- 2022: [Listening to the languages of the people  : Lazare Sainéan on Romanian, Yiddish, and French  / Natalie Zemon Davis / Budapest : Central European University Press , 2022](http://www.sudoc.fr/277050014). Subjects: Biographie; Philologues; Sainéan, Lazare (1859-1934 ; linguiste); Philologie.
- 2020: [Early Modern Cultural Studies  / editorial board; Stephen J. Campbell, Brian Cummings, Natalie Zemon Davis, ... [et 12 al.] / Turnhout : Brepols , 2020-](http://www.sudoc.fr/252657071). Subjects: Culture.

### Jim Clifford (Q112545811)

Discovery cohorts: environmental_history. Recent linked records: 0. These links remain identity candidates until reviewed.

No recent Sudoc record returned under these identifiers and roles; this is not evidence of no recent scholarship.

## Identity and date review

**3 sampled identity links carry review flags**, including **0 birth-year conflicts**. All sampled links remain `needs_review`, including those without flags.

The staging graph retains Wikidata people and IdRef authority URIs separately. The CSV’s candidate-person column is a join through the recorded identifier, not an accepted identity merge. Review identity flags before attributing bibliographic records to people.

Date status counts across all returned bibliographic resources:

- catalogued_year_in_window: 87
- missing_date: 387
- outside_window: 1,429

Recent extraction uses structured dc:date values. It never extracts a year from a title, subject-period string or citation. Multiple or non-exact dates remain ambiguous. The identity audit checks available birth-year conflicts and shared/multiple identifiers; it does not prove identity from matching names.

## Files and reproduction

- `people.csv` / `people.json`: discovery provenance, external identifiers and inherited atlas mappings.
- `selection.json`: exact theme samples and candidate authority joins.
- `recent-resources.csv`: inspectable recent records, raw role URIs, dates and original subject labels.
- `bibliographic-resources.json`: all-period records for the sampled authorities; no inferred first-publication dates.
- `identity-review.json`: authority labels, birth values and identity review flags.
- `observations.json`: unreviewed RDF-like source statements with provenance; no inferred field, membership or influence edges.
- `subjects.json`: subject IDs and original labels; no automatic subject-to-field mapping.
- `manifest.json`, `queries/`, `raw/`: exact queries, cached results, retrieval timestamps and SHA-256 hashes.
- `summary.json`, `audit.json`, `inputs.json`: scope counts, integrity checks and protected input fingerprints.

From the repository root, run:

```sh
python3 scripts/mine_lod.py --run PATH_TO_SNAPSHOT --offline
python3 scripts/summarize_lod.py PATH_TO_SNAPSHOT
python3 -m unittest discover -s tests -p 'test_lod_mining.py' -v
```

Omit `--offline` to fetch missing queries. Existing cache entries must match the exact query and endpoint; changed plans/inputs require a new run directory. A query hitting its row cap fails rather than masquerading as a complete harvest. IdRef queries respect its sorted-result ceiling. The raw cache should remain outside published site assets.

## Next batch

Review flagged identities first, then classify a small sample of recent records as original work, translation, reissue or unresolved publication. Use the observed subjects as discovery leads and record any person-to-field interpretation separately with evidence. Expand the bibliographic sample only after evaluating these outcomes; no field-size or productivity ranking is justified by this harvest.

The authoritative atlas, ontology fixtures, site assets and OpenAlex data were not modified by the miner. The requested 2020–2026 window applies to catalogued publication years, not the validity dates of Wikidata classifications.
