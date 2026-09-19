# Transnational history, migration, mobility and diaspora — batch 09

Research cutoff **19 September 2026**. Six new works and twelve new historical proposals; two inherited breadth-01 works/claims preserved exactly. One **Transnational history** entry draft and four explicit boundary decisions. Everything remains research staging; production remains **1.122**.

Eight works total; fourteen historical claims: eleven selected-passage, two abstract and one inherited publisher-description claim. Twenty-two authorship credits and one version assertion bring the total to **37 claims, all `needs_review`**. The twenty-two people comprise nine authors of new selections and thirteen metadata-only credits from the older Saunier book and AHR forum. No person is promoted to production here.

| New reading | Checked scope | Important limit |
| --- | --- | --- |
| [Wimmer and Glick Schiller, 2002](https://www.columbia.edu/~aw2951/B52.pdf) | Published pp. 301–303, 324–325 | Both authors retained; critique of national categories also qualifies transnational community research. |
| [Brubaker, 2005](https://www.tandfonline.com/doi/abs/10.1080/0141987042000289997) | Indexed author abstract | Body not recovered. The 2006 online posting does not replace the 2005 issue year. |
| [McKeown, 2007](https://escholarship.org/uc/item/4t49t5zq) | Conference paper, PDF pp. 1–7 | Separate from his 2004 article and 2011 chapter. Opening argument and counting caveats, not statistical replication. |
| [Greefs and Winter, 2024](https://doi.org/10.1017/ssh.2024.9) | Published pp. 383–387 | Antwerp-bound migration, 1850–1910. “Democratization” is their term for changing selectivity, not universal equality. |
| [Reinecke and Löhr, 2024](https://academic.oup.com/migration/article/12/3/mnae023/7725796) | Introduction, opening of section 2, selected section 3 | Their proposed uses of history; referenced scholarship is not independently read by association. |
| [Liebisch-Gümüş, 2024 version](https://docupedia.de/zg/liebisch_guemues_mobilities_v2_en_2024) | English sections 1–2; German/English version metadata | Earlier version uncollated. German v2: 15 July; English v2: 18 October. No argument-origin or translator inference. |

`entry-proposals.json` proposes a distinct teaching entry for a plural historical approach. Its strands preserve exact claim joins, qualifications and dates. Saunier's description and the AHR opening remain labelled leads; neither supplies individual practitioners to the draft argument roster. All twelve AHR byline credits survive separately in the research catalogue. Metadata authorship does not imply assent to every forum argument.

`boundary-review.json` keeps migration, mobility and diaspora distinct. Migration merits consideration beyond the existing Atlantic context; mobility is provisionally a cross-field approach; diaspora requires further historical and conceptual review while preserving existing African/Atlantic strands. These are editorial recommendations, not influence arrows. The three exploratory concepts **do not silently enlarge the 37-candidate ledger**.

`coverage-current.json` advances batch 08 without changing its 75 topic rows or 36 unrelated candidate rows. Current candidate dispositions: **five separate-entry drafts, fourteen partial research/no field decision, eighteen pending**. No field is fully reviewed. Partial chronological bins are navigation aids; the 2013 description does not establish body-supported coverage of that decade. Latest selected publication here is 2024, separate from the 2026 research cutoff.

See `representation-review.json` for every selection, access failure and named follow-up. English readings dominate. Asian migration in one comparative paper does not constitute regional or language balance. Priorities include Saunier and individual forum bodies, Gabaccia/Donato and Hoerder/Kaur, Mavhunga, Huber, Lüthi, Falk, Schewel, and diaspora work beyond Brubaker. These leads remain unaccepted; no demographic or authority inference was made.

`research.json` is the reproducible recipe. `batch.json` follows ontology contract 0.2. `review-actions.json` retains full older work records before additive metadata; `source-proposals.json` maps bibliography IDs. Raw web files are tool extractions, not original HTML or claims to have read entire works. The Wimmer file is a selected text extract; the downloaded PDF remains under `/tmp`. Retrieval failures never upgrade evidence.

Rebuild and check:

```sh
python3 scripts/build_transnational_mobility_batch.py
python3 scripts/build_transnational_mobility_batch.py --check
python3 -m unittest tests.test_transnational_mobility_batch
```

Eight focused tests cover exact inherited evidence, coauthors, forum attribution, abstract limits, chronology, coverage and staging status. Baseline pins protect the production graph, site/build assets, acceptance packet and prior research packets. Existing snapshots and manifests remain unchanged; no website edit or deployment. OpenAlex remains paused.

Next consolidate a reviewed subset for production, beginning with the digital/web drafts and their four older breadth works. For this new draft, recover Saunier and specific AHR essays and review earlier/regional roots before admission. Broader field review remains distinct from acceptance of a bounded subset.
