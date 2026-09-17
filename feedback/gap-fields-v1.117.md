# Public, medical/health and urban history: revision 1.117

All three missing-entry candidates now have dedicated, sourced atlas entries. They are enduring research fields with internal approaches, not newly declared schools or fields dated from a journal launch. Earlier nodes, people, sources, relationships and editorial qualifications are preserved exactly.

## What was added

| Entry | People selections | Approaches | Main distinctions |
| --- | ---: | ---: | --- |
| Public history (`publichistory`) | 8 | 5 | Professional commissioning; oral/public authority; place and preservation; everyday uses of the past; worker/community history |
| Medical & health history (`medicalhistory`) | 7 | 6 | Social medicine; patients and lay knowledge; public health and the state; gender and embodiment; colonial medicine; African healing |
| Urban history (`urbanhistory`) | 8 | 7 | Field organization and disagreement; suburban building; quantitative mobility; racial exclusion and industrial change; colonial space; hinterlands; public landscapes |

These are 23 contextual selections using 22 distinct people, including 14 new shared identities. Hayden appears in two new entries. Existing Frisch, Samuel, Roy Porter, Thernstrom, Cronon, Hayden, Feierman and Janzen identities are reused. Dorothy Porter, the medical historian, has a separate identity from Dorothy Porter Wesley, the librarian.

Fifteen new map connections identify particular contributions or explicit comparisons. Examples include Frisch’s editing work between oral and public history, Callinicos’s South African educational practice, Duden’s historical treatment of embodied experience, Feierman/Janzen’s African healing project, Thernstrom’s quantitative urban inquiry, Cronon’s city–hinterland relations and Hayden’s bridge between urban and public history. Comparisons with memory, postcolonial inquiry, Black history and history of science remain undirected. The entries do not manufacture a common founder or an undocumented chain of intellectual influence.

## Journal links

| Journal/title phase | Target | Reviewed interval |
| --- | --- | --- |
| The Public Historian | Public history | 1978–2000 |
| Social History of Medicine | Medical & health history | 1988–2000 |
| Urban History Yearbook | Urban history | 1974–1991 |
| Urban History | Urban history | 1992–2000 |

All four are `principal_venue` selections. No founding claims were added. Intervals describe a reviewed role; 2000 is the atlas boundary. The Yearbook is a new title-phase record with an explicit 1992 succession relation. The original Urban History record’s unknown canonical start remains unchanged. Cambridge repeats modern identifiers on its past-title page; the new Yearbook record leaves ISSNs empty pending title-specific identifier review.

The Public Historian selection combines [Kelley’s 1978 programme](https://eclass.uowm.gr/modules/document/file.php/ELED278/Kelley%20public%20history%201978%20PH.pdf) with [NCPH’s institutional retrospective](https://ncph.org/history-at-work/update-on-the-journal/). This supports a continuing US professional forum, not global representativeness or a complete article census.

The medical selection uses the editors’ [anniversary introduction and dated pre-2001 selections](https://academic.oup.com/shm/pages/chairs-choices-anniversary-vi). Urban selections use the [anniversary collection’s contemporary extracts and abstracts](https://www.cambridge.org/core/journals/urban-history/50th-anniversary-collection) and [explicit publisher title history](https://www.cambridge.org/core/journals/urban-history/information/about-this-journal/past-titles). These establish continuing institutions and changing questions; they do not make the journals sole representatives of their fields.

## Evidence and limits

Fourteen new historical sources supplement existing scoped readings. The downloaded Kelley opening documents applied professional work; [Callinicos’s 1986 opening](https://www.sahistory.org.za/sites/default/files/archive-files/Transforming%20Peoples%20Past%20by%20Luli%20Callinicos.pdf) supplies a distinct South African account of popular history and worker education. Their later sections were not read in this pass. Two research PDFs are hash-recorded outside public assets.

Several book entries rely on publisher descriptions, contents and edition metadata. The Sigerist retrospective and Roy Porter article use indexed body/opening text; Urban History items use extracts or abstracts. Source notes specify access and reading scope. Neither full-book verification nor an independent assessment of all historical findings is claimed.

The dedicated-entry gaps are closed at an initial substantive level. Coverage remains selective:

- **Public:** museum practice, Indigenous public authority and non-Anglophone formations need deeper treatment. US professional training, British local/oral practice and South African worker education remain distinct.
- **Medical:** Asia, Latin America, Indigenous medical historiographies, clinical scholarship and psychiatry need fuller treatment. Sigerist shows that social approaches did not begin with the later society/journal.
- **Urban:** wider African, Asian and Latin American urban historiographies and medieval/early-modern programmes need expansion. British organization, US linked-record research and Delhi’s colonial spaces are selected projects, not universal models.

Medical History, Bulletin of the History of Medicine and Journal of the History of Medicine and Allied Sciences remain unaccepted venue leads. Journal of Urban History needs a sustained-role review; the two Canadian Urban History Review candidate records need identity reconciliation. Existing venue leads elsewhere are carried forward without being presented as newly reviewed.

## Current totals and verification

- Historical graph: **112 nodes / 723 edges / 819 sources / 811 people**; **69 groups and 703 approaches**.
- Journal inventory: **1,638 candidate/title records**, 798 library profiles, 808 records with ISSNs and 566 recorded starts. The count includes title phases and unresolved candidates.
- Venue graph: **54 edges**, comprising **42 principal / nine founding / three debate**. Principal selections cover 36 title records and 29 fields; all venue types reach 32 fields. Eleven title relations.
- Subject classifications remain **2,006**: 1,322 checked and 684 provisional. 864 records have checked classifications, 442 only provisional classifications, and 332 are unclassified.
- **62 Python tests and the JavaScript core suite passed**, including a new check for field search, direct routes, shared people and Dorothy Porter identity separation.
- Zero structural errors; four unchanged, documented relationship warnings.
- Exact prior-record preservation, offline catalogue reproduction, 69-field ledger reconciliation and research-PDF hashes verified.
- Six allowlisted public assets rebuilt and checked byte-for-byte. Existing historical views can load the new entries; journal-edge rendering is still a separate future task.

## Reproduction and handoff

```bash
python3 scripts/build_journal_catalogue.py
python3 scripts/build_site.py
python3 scripts/audit_gap_fields.py
```

- Baseline: `drafts/historiography-1920-2000.v1.116.json`.
- Exact historical additions: `feedback/gap-fields-v1.117-additions.json`.
- Journal batch: `data/journal-catalogue/venue-batches/founding-006.json`, accepted by hash.
- Current field ledger: `feedback/journals/principal-venues-v1.117-review.json`; earlier 66 rows retained exactly and three original gap diagnoses marked implemented with limits.
- Audit output: `feedback/gap-fields-v1.117-validation.json`.

No deployment or OpenAlex work. No frontend design changes.
