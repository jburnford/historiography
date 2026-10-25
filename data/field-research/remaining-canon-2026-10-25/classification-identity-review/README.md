# Remaining canon: classification and identity review

Checked 25 October 2026 against published 1.183 and the unchanged 23 October 2026 frozen citation release. **All 21 cases have decisions: nine eligible historian candidates, nine below the applicable threshold, three retained holds.** No biographies, graph records, release files or reading exports were changed.

The criterion is substantial research reconstructing historical change, events, institutions or experience. Department and nationality do not decide classification. Historical anthropology, sociology, literary scholarship and political theory can coexist with historical research. The applicable screen remains **Canadian-history focus ≥150; other historical research >100**.

## Concrete biography queue

| Candidate | Eligibility count | Person ID | Basis |
|---|---:|---|---|
| Michel de Certeau |266|michel_de_certeau|Early-modern religious/mystical history|
| Charles Tilly |178|charles_tilly|Archival/comparative histories of contention, revolutions and states|
| Timothy Mitchell |135|timothy_mitchell, new|Colonial/modern Egyptian historical research|
| Jack Goody |125|jack_goody|Historical kinship, property, literacy and Eurasian comparison|
| Tzvetan Todorov |125|tzvetan_todorov, new|Sixteenth-century conquest histories using contemporary sources|
| Partha Chatterjee |119|partha_chatterjee|Colonial/postcolonial historical projects|
| Alessandro Portelli |104|alessandro_portelli|Original oral histories of workers and wartime memory|
| Alexis de Tocqueville |104|alexis_de_tocqueville, new|Old Regime/French Revolution historical research|
| Steven Hahn |**103 clean lower bound**|steven_hahn, new|Four positively identified US slavery/populism books; distinct from Steven C.Hahn|

The eight classification cases retain the existing exact frozen first-author key screen and its qualification. They are **not represented as complete work-by-work identity audits**. Named institutional/publisher projects establish historical-research function and author identity. The frozen raw Hahn key is 121; it is **not accepted as a clean person total**. His four-book union 103 independently passes the threshold. New IDs are proposed after checking existing graph people: Mitchell Dean/Juliet Mitchell are distinct; no existing exact Todorov, Tocqueville or Steven Hahn identity was found. Preserve existing identity notes and interdisciplinary roles when writing biographies.

## Below-threshold decisions

| Case | Count evidence | Decision |
|---|---|---|
| Bruce G.Trigger |122raw; Canadian-title union64; global major-book union21|Historical researcher; Canadian focus retained; below 150|
| Reg Whitaker |115raw maximum|Canadian historical projects; below 150|
| John Herd Thompson |146raw maximum|Canadian historian; below 150 even before contamination cleanup|
| Robert Craig Brown |118raw maximum|Canadian political historian; below 150|
| Richard Harris |107raw maximum|Canadian urban historical geographer; below 150|
| Peter Ward |101raw maximum;72confirmed named-book subset|Canadian social historian; below 150|
| James Miller |146mixed key;97J.R.Miller selected books;23James E.Miller selected books;≤51all records outside the two positively identified J.R.books|J.R.Miller below Canadian 150; NewSchool identity below the other-history minimum of 101|
| Alice Kessler-Harris |103raw;79confirmed named-book subset;**≤100**after four confirmed foreign works excluded|Belowother101 even if every remaining held record were hers|
| Paul Thompson |101raw;54confirmed English-book subset;**≤98**after one confirmed foreign work excluded|Belowother101 even if every remaining held record were his|

Trigger's global historical work is substantial: *A History of Archaeological Thought* and *Understanding Early Civilizations* are positively identified comparative/worldwide projects. Their full-title frozen-key union is21. A conservative named Canadian/Wendat/StLawrence/Canadian-historiography set reaches64/122, and the two major Canadian book families alone reach54. This supports retaining Canadian focus on actual cited work rather than nationality or existing roster membership. The focus comparison classifies clearly named topics, not the exact use made in each dissertation; it is not a full identity audit of every variant. Its exact indices and deduplicated IDs are recorded.

Alice's four excluded titles are *Alaska and Klondike Goldfields* (1897A.C.Harris), *Sex Offender Recidivism: A Simple Question* (Andrew J.R.Harris and R.Karl Hanson), *Settlers and Convicts* (Alexander Harris), and *Historical Syntax in Cross-Linguistic Perspective* (Alice C.Harris and Lyle Campbell). Paul Thompson's *The Nature of Work* is positively linked to the Stirling labor-process scholar, distinct from the Essex oral historian. Exclusion is at work-key level: a dissertation also citing a confirmed work remains counted. These maxima are unions of remaining dissertation IDs, not subtraction of raw work counts.

For below 150Canadian cases, the entire frozen-key count is already an upper bound below the floor. Additional generic-key cleanup was deliberately limited to positive named-work witnesses and explicit identity patterns; no fabricated clean total is supplied. Empty selected subsets in the machine record mean no lower-bound audit was required, not zero authentic works.

## Three retained holds

- **Peter Brown:** Princeton late-antique historian is clearly identified; Peter Hume Brown and other namesakes remain separate. Thirteen positively identified English books yield a clean lower bound 69. Excluding the positively identified Scottish-travel record leaves an optimistic 112. Translation/article matching has not established >100; retain the identity/threshold hold rather than assign 114 to one person.
- **Charles Taylor:** retain theory/identity review. The1931philosopher has a positively matched selected subset 62; Formac's journalist author of *Radical Tories* is distinct. Raw 148 is not a clean philosopher total. Historical and intellectual-history dimensions remain visible; this review does not automatically promote him to historian or establish a clean theory-queue threshold.
- **Adam Smith:** retain split theory/identity review. The eighteenth-century moral philosopher/economist has selected major-book union 77; modern Oxford US historian Adam I.P.Smith has selected CivilWar-book union 9. Raw 110 is assigned to neither person. Other Chinese-history and generic records remain held. Existing adam_smith is reserved for the eighteenth-century author.

## Evidence and reproduction

[review.json](review.json) records all 21 original queue rows, explicit identity patterns, existing/proposed person IDs, classification reasons, source IDs, selected and foreign-work decisions, raw original work rows and count limits. [eligible-historian-queue.json](eligible-historian-queue.json) is the concrete nine-person queue. [sources.json](sources.json) records exact primary-source URLs, locators, checked date, scope and access limitations. Search-indexed primary records are identified where direct access failed; no inaccessible body is claimed as read.

[count-witnesses.json](count-witnesses.json) contains exact selected/possible/frozen dissertation-ID unions and five frozen-release hashes. [raw-work-concordance.json](raw-work-concordance.json) preserves all work rows under the 21 exact first-author keys. [dated-citation-sets.json](dated-citation-sets.json) records their dated dissertation IDs. No aliases or IDs are merged; no count is inferred from summed variants.

Reproduce the source-row preservation, SHA256, population and union assertions:

```sh
python data/field-research/remaining-canon-2026-10-25/classification-identity-review/reproduce.py
```

The population is the 6794 dated `in_analysis=True` dissertations. Each dissertation ID is counted once per selected union. Counts describe bibliography presence, not approval, reading completeness or intellectual influence. Source metadata supports identity/classification only; it creates no graph arrow. No OpenAlex request was made. Raw-download bodies, if later acquired, belong only in ignored `raw/`.
