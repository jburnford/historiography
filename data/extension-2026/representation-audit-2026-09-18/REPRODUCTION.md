# Independent reproduction and corrections

The supplied Fable 5.1 packet and README are retained unchanged. Run `python3 scripts/reproduce_representation_audit.py` to reproduce from the saved MCP/QLever observations and current local graph/ranking inputs. No network call or demographic inference is needed. The separate `reproduction/manifest.json` pins all inputs and outputs. The 42 accepted node-QID mappings and the unreviewed roster candidate map are checked against their original repository files.

All 829 audit CSV rows reproduce exactly: gender-value strings, evidence basis, node status, distinct representative/strand entry counts and entry lists. These are **provisional classifications**, not accepted roster identities or a verified demographic census.

| Measure | Reproduced result |
| --- | --- |
| Shared people | 162 provisionally classified women, 493 men, 174 unknown/multiple |
| Full person entries | 13 women, 30 men under the packet's classification method |
| Accepted node identities only | 12 women, 30 men; the thirteenth woman's identity is outside that accepted-QID set |
| Topic-entry occurrences | 313 women, 808 men, 248 unknown/multiple |
| Edges touching the provisionally classified women's full nodes | 97 |
| Reviewed candidate cohort | 10 women, 108 men |
| Visibility top thousand | 97 women, 903 men; woman-labelled records include 96 female and one trans woman |

The eleven flagged fields and the Annales, explanation/objectivity and economic-history ratios also reproduce. The replay retains all raw values, candidate QIDs and source locations. Buckets are only a reproduction of the supplied method; mixed or nonbinary values are not forced into a binary count.

Three substantive corrections:

1. **The reviewed priority band contains three women:** Hannah Arendt (Q60025), Drew Gilpin Faust (Q49128) and Nina Garsoyan (Q23120599). All three are in both `reviewed-all.csv` and `reviewed-priority.csv` and pass the recorded death screen. The claim that Arendt is the only one is incorrect.
2. **The saved `top1000_nonmale.csv` contains 115 male records.** Raw item URIs survived a label-based filter. The raw sixth-batch TSV actually has English male/female labels on all 173 returned rows; the problem is not two missing labels in that saved response. The corrected provisional women-only export is `reproduction/top1000-women-provisional.csv` (97 rows). The original file remains intact for audit.
3. **The Butler row combines different people.** In `raw/labelmatch.tsv`, philosopher Q219368 has the returned value non-binary (Q48270). Three other Judith Butlers have female values (a nurse scientist and two historical namesakes). Thus this response does not show female and non-binary on the philosopher's item. Preserve QID-level observations; adjudicate the identity before making a personal demographic assertion. This does not claim to inspect every Wikidata statement or its history.

Additional limits matter. Counts from unreviewed name matches are not mathematically secure lower bounds: wrong matches can produce false positives as well as omissions. Agreement among 26 Mary Douglas namesakes does not establish which one is the anthropologist. “No provisionally classified women” in a topic is not proof no women occur there. The generic query export does not preserve statement rank, qualifiers or full reference provenance. The README's claim about every woman's career being mainly before 1960 has not been independently established by this replay.

The structural review also confirms that roster figures have shared person records and discoverable profiles, rather than text-only presence. Scott has eight representative-entry appearances and seven distinct strand-entry appearances but no full node. The gender-to-Thompson critique already exists at an umbrella endpoint (`edge_314`); finer individual attribution remains absent. Promoting a node should preserve this qualified exchange rather than inventing a new disagreement or copying it to every feminist historian.

The local cohort audit checks 65 supplied names, including an alias control and three anti-colonial leads. Louise A. Tilly and Frances A. Yates require explicit aliases. These corrections do not authorize a Wikidata merge. Use `people-review.json` for preserved contexts, work strings and inherited evidence; use contribution and reception review, not the number of appearances, to decide promotions.
