# Publication-evidence coverage audit — 10 October 2026

The empty early bars cannot be read as the absence of historical scholarship.
The audit confirms failures at several different stages: journal selection,
catalogue-to-harvest joins, title-phase mappings, deposited backfiles, page-length
filtering and chart display. Annales is one example of a wider problem.

This is a coverage audit of **revision 1.125 / practice v17**, covering all eleven
families, 77 group entries, 407 selected title contexts, the 819-context community
screen and 1,638 catalogue periodicals. It also checks the method and review-mention
derivations and the scope of the profile pilot. It does not reverify every historical
relationship, roster attribution or citation in the teaching graph.

## Confirmed omissions and false starting points

- **Two selected journals lose accepted venue mappings through their catalogue
  aliases.** Three curated edges are affected: two for the original Annales title
  and one for History and Theory. The builder tests whether the edge's source is
  a selected `journal_key`; it ignores the selection's explicit `catalogue_ids`.
  The selected keys are `initial:annales_1929` and `initial:history_theory`.
  This is a join defect, rather than an editorial disagreement.
- **Annales's early title phases are collected but untagged.** The original title
  has 207 records and 65 ten-page candidates, all in 1929–1932. Its three wartime
  title contexts add 129 records and 34 candidates. The modern mapping therefore
  starts in 1946 despite those earlier records. The publisher records the original
  phase as 1929–1938; local deposits for 1933–1938 are absent. Fixing the join alone
  cannot recover those years or map the three later phases. The English edition
  is also untagged and needs a translation/edition decision before combination.
  [Publisher title history](https://www.cambridge.org/core/societies/annales-histoire-sciences-sociales).
- **History and Theory has two independent problems.** Its 932 candidates across
  the full snapshot lose their curated mapping. Its records begin in 1960, but
  every one of the 390 records in 1960–1974 lacks a calculable page length, so even
  a repaired join leaves that period empty. For a concrete check, the deposited
  page for DOI `10.2307/2504255` is `1`; the journal's own bibliography gives
  pages 1–31 under Articles. This establishes a real excluded long article, without
  classifying every other record. [Volume 1 bibliography](https://historyandtheory.org/volumes15/volume1).
- **Environmental history loses two collected predecessors.** Journal of Forest
  History has 125 candidates and Forest & Conservation History has 38; neither
  has a theme mapping. The current family begins in 1976, while the first of those
  titles contains candidates from 1974. The publisher confirms the 1974–1989 and
  1990–1995 title runs. One deposited record under the later context is dated 1981;
  retain and flag that anomaly rather than treating it as the title's founding.
  Merger relationships support review of these mappings, not automatic propagation
  of every successor classification. [Publisher title note](https://www.journals.uchicago.edu/toc/jforehist/1989/33/3),
  [archive description](https://academic.oup.com/foreconshist/pages/About).
- **Labour/Le Travail is collected but untagged.** It has 3,520 records from 1976
  onward and 181 candidates across the snapshot. Its deposited metadata produces
  no ten-page candidates before 2016: all 2,383 records from 1976–1999 lack a
  calculable length, although all have a page field. Its publisher identifies
  working-class history as a defining focus. A source-backed journal mapping and
  pagination repair are separate jobs. [Journal description](https://lltjournal.ca/index.php/llt).
- **The Journal of African History is collected but untagged.** Its 6,294 records
  include 1,965 candidates from 1960 through 2024. The empire/global family currently
  begins in 1974. Mapping this title to African history is a high-priority editorial
  proposal; its presence in the catalogue alone is not an accepted family assignment.
  Cambridge's archive independently confirms the 1960–1996 backfile.
  [Publisher archive](https://www.cambridge.org/core/journals/journal-of-african-history/information/digital-archive-1960-1996).
- **Indigenous histories has a strong pagination discontinuity.** Ethnohistory is
  mapped and has records from 1954, but all 2,707 pre-2000 records lack calculable
  lengths; only one lacks a page field. Its first qualifying candidate is dated
  2000. The family's earlier candidates come from Western Historical Quarterly
  from 1970, so the family chart's apparent beginning says little about earlier
  Ethnohistory scholarship. A checked 1954 example has deposited page `155` but
  archive pages 155–165. [Publisher's issue table](https://www.jstor.org/stable/i220831).
  Western Historical Quarterly's whole-venue Indigenous tag also needs a remit
  review: an overlap does not make every article Indigenous history.
- **War and military coverage omits a longstanding journal lineage.** Journal of
  Military History is a catalogue candidate with no resolved ISSN in this snapshot
  and was not selected. Its predecessors were not collected either. The Society
  dates the journal's scholarship to 1937; the mapped family record begins in 1967.
  This needs bibliographic identification, a selection decision and a backfile
  source, rather than a chart-level patch. Selected Civil War History has zero
  deposits and no theme mapping; its empty result is another source limitation.
  [Society description](https://www.smh-hq.org/jmh.html),
  [archive title history](https://www.jstor.org/journal/jamermilihistfou).

Candidate counts above refer to the full frozen snapshot unless a date window is
specified. Landing counts use 1900–2024; field panels also include later years.
Ten pages is a screening proxy, not a checked article genre. Do not add the counts
across overlapping families or interpret DOI rows as necessarily distinct publications.

## All eleven families

The two date columns are the first mapped deposited record and the first qualifying
candidate **within 1900–2024**, using the current mapping. They are coverage dates,
not origins of fields. Bridges count in both families.

| Family | First record | First candidate | Main coverage finding |
| --- | ---: | ---: | --- |
| Social history | 1916 | 1916 | Labour/Le Travail is untagged and its older lengths are unavailable; early Black-history counts already exist. |
| Cultural & intellectual history | 1916 | 1916 | Culture & History Digital Journal is tagged but all 305 journal-article records lack calculated lengths; current proxy counts none. |
| Annales | 1946 | 1946 | Alias defect, three untagged wartime phases and an incomplete original-title backfile. |
| Political, national & international | 1918 | 1918 | Nations and Nationalism is deliberately excluded by the political-science screen; do not silently reverse that decision. |
| War & the military | 1967 | 1967 | Journal of Military History lineage unselected; Civil War History has no deposits. |
| Economy & social science history | 1927 | 1927 | Interwar economic records exist. Several related venues have incomplete backfiles; Agricultural History deposits begin in 2000 despite publication from 1927. |
| Indigenous histories | 1954 | 1970 | Ethnohistory's pre-2000 page data cannot pass the length filter; two of four mapped contexts have no deposits. |
| Empire, colonialism & the global | 1974 | 1974 | Journal of African History is untagged; older African-history records are outside the family's current series. |
| Science, technology & medicine | 1913 | 1913 | Early records exist. Two curated science-studies venues are outside the identified selection; journal/remit decisions are unresolved. |
| Environment | 1976 | 1976 | Two forest-history predecessor contexts have collected candidates but no theme mapping. |
| Theory & method | 1912 | 1952 | History and Theory alias/length failures; Oral History Review is outside the identified collection. Method use requires separate evidence. |

Agricultural History's society confirms publication from 1927, so its local 2000
start is a genuine coverage warning. [Society history](https://www.aghistorysociety.org/the-society).
Isis has a publisher founding date of 1912 and a library start observation of 1913;
the audit preserves that conflict. Its first local record is 1913.
[Publisher description](https://www.journals.uchicago.edu/isis).

## Systematic findings and their limits

Of 407 selected contexts, **63 have no deposited records**, **144 nonempty contexts
have no theme mapping** (134 still have qualifying candidates), **six mapped
nonempty contexts have no qualifying candidates**, and **194 have mapped candidates**.
General, regional and period classifications can intentionally lack a field theme;
the 144 are a review inventory, not 144 confirmed mistakes. Twenty-eight of the
zero-result contexts have theme mappings. The anti-colonial panel's zero-journal
statement is specifically misleading: a selected venue is tagged but has no deposits.

The six mapped nonempty contexts with zero candidates are Afriques, New York History,
Culture & History Digital Journal, Entreprises et Histoire, Mundo Agrario and
Archivium Hibernicum. Each lacks calculated lengths for every journal-article
record. Only Afriques lacks the page field for all those records. The other five
demonstrate why “missing pagination” must distinguish a missing field from a single
starting page or article number. The Journal of Digital History already has an
article-number exception; other exceptions need source-specific genre review.
CSIC explicitly describes Culture & History Digital Journal as an electronic
publication founded in 2012. [Publisher description](https://cultureandhistory.revistas.csic.es/index.php/cultureandhistory/index).

**85 contexts start depositing after all their recorded publication-start
observations; 82 have internal years without deposits.** These sets overlap and
are screening flags. Publication interruptions, title phases, date errors and
incomplete Crossref deposits can all cause a flag. Neither result proves a failed
harvest: the selected harvest was completed, including empty coverage checks.

**Nine curated venue edges point to eight titles outside the selection.** Signs
and Feminist Studies were screened as mixed communities; Nations and Nationalism
and New Left Review were explicitly excluded under the user's political-science
rule. Oral History Review, Studies in History and Philosophy of Science Part A,
Social Studies of Science and Urban History Yearbook have no resolved ISSNs in
these catalogue nodes. Oral History Review's publisher supplies identifiers and
a 1973 issue with a long article, making it a concrete recovery lead.
[First issue](https://academic.oup.com/ohr/issue/1/1).

Urban History Yearbook is an important counterexample: it is unselected as a
separate title, but the selected Urban History context already contains 1974
records and candidates. The publisher lists both title phases under its archive.
Do not add another backfile without comparing DOI memberships.
[Publisher title history](https://www.cambridge.org/core/journals/urban-history/information/about-this-journal/past-titles).

**Chart display hides existing early evidence.** All narrow-screen family cards
start at 1950, and the field-panel journal charts also start at 1950. Eight entries
have earlier counts hidden there: Annales, Black history, economic history,
medical/health history, history of science, new social history, historical geography
and history of technology. The desktop landing has a wider window. Its five-year
bins can also appear before the first actual record: the War family's 1965 bar
contains records starting in 1967. Show the bin interval and coverage state.

The “80 established journals” are **80 title contexts**. Two Annales contexts share
all 18,010 DOI records. The family series deduplicates those records correctly,
but the context count is not a measured count of distinct continuing journals.
Title changes with different keys also affect established-view eligibility.

## Adjacent evidence checks

The review-mention build references practice v14 rather than v17. Comparing the
actual `(source, item, target)` mappings finds **20,984 pairs in both, with zero
additions or removals**. This is a provenance label to improve, not a demonstrated
stale-result error. H-Net and Reviews in History remain recent, geographically
selective review collections; their absence in interwar years is expected.

The methods-v3 summary has no input hash manifest. Its displayed “practitioners”
combine venue credits, ORCID claims and atlas rosters, without exporting confidence
tiers. Among the practitioner IDs, the registry contains 51 probable and two accepted
atlas occurrences, plus 6,889 anchored Crossref occurrences. Those are occurrence
counts, not counts of probable people or publications. A zero method-venue credit
total does not establish that no method journal was collected. Title and abstract
matches are also incomplete signals and do not establish use of a method in an article.

The eight-profile, 84-credit pilot is explicitly bounded and already displays the
weaker identity tier. Absence outside that pilot does not show absence of a person's
publications. No identity links or historical claims were promoted by this audit.

## Correction order

1. Repair selected catalogue-ID joins and add regression coverage. Rebuild into a
   **new** practice version; retain v17. Correct zero/absence wording and label
   title-context counts and chart windows before historical interpretation exercises.
2. Review explicit mappings for the Annales wartime phases, forest-history
   predecessors, Labour/Le Travail and Journal of African History. Keep mapping
   acceptance separate from source pagination and edition decisions.
3. Recover page ranges through DOI-linked publisher/archive metadata, beginning
   with Ethnohistory, History and Theory and Labour/Le Travail. Preserve original
   deposited metadata and attach provenance to a supplemental correction table.
   Do not infer endpoints from the next starting page or admit every journal article.
4. Resolve and review Journal of Military History and Oral History Review as bounded
   acquisition candidates. Respect the approved collection screen. Check missing
   Annales years and high-impact backfiles before expanding general journal scope.
5. Add input pins and confidence breakdowns to the next method build, and retain
   the present distinction between candidate persons, credited works and demonstrated
   method use. Complete the existing genre and mapping reviews after these repairs.

The [correction queue](correction-queue.csv) records causes, evidence and remaining
decisions. It is an audit queue, not accepted classifications or a harvest instruction.

## Reproduction and evidence

Run `python3 scripts/audit_evidence_coverage.py --out /tmp/coverage-audit-fresh`.
The script refuses an existing output directory, opens databases read-only,
pins 30 inputs, checks that their hashes remain unchanged and exactly reproduces
every published all-journal family bin and the weighted headline.

- [Summary and input/output hashes](summary.json).
- [407 journal contexts](journal-coverage.csv), [1,638 catalogue periodicals](catalogue-selection.csv).
- [54 curated venue links](venue-coverage.csv), [11 title relationships](title-history.csv).
- [All families](family-coverage.csv), [all group entries](entry-coverage.csv).
- [Targeted period comparisons](targeted-periods.csv), [bounded primary-source checks](source-checks.json).

The initial run is retained in `runs/initial/`. The final run distinguishes missing
page fields from missing calculated lengths and records graph revision 1.125;
the shared aggregate and mapping results agree. Six regression cases cover alias
resolution, equal-title separation, distinct coverage states, policy exclusions
and conflicting date observations, plus export hashes and scope reconciliation.
All 23 focused coverage, evidence-asset and family tests passed; `git diff --check`
is clean. Public evidence and profile JSON still match their unchanged inputs.
Publication snapshots, public assets, existing
IDs and editorial decisions are unchanged. No harvesting, deployment or OpenAlex work.
