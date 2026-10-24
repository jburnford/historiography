# Revision 1.159: review the remaining 148 work candidates

The user asked to repeat White’s work-completeness check on the remaining 148
records, then clarified that the review also needs relationships. Every record
from the frozen revision-1.157 queue now has an explicit decision:

| Decision | Records |
| --- | ---: |
| Add a missing selected work, chapter, collection or edition | 62 |
| Expand an existing selection or supply its missing dated point | 38 |
| Already represented; title comparison missed it | 13 |
| Translation, retitling, edition or reprint reconciliation | 34 |
| Unresolved truncated volume | 1 |
| Total | 148 |

These are corpus work records, not 148 distinct books or an objective canon.
Citation counts are retained per record and are never summed across possible
editions. Of the 45 individuals reviewed, 36 receive entry changes and 33 gain
chronology facts. The batch adds 94 dated facts (90 individual and four field
facts), 45 scoped sources and four contribution edges. Counts become **203 entries,
1,261 edges, 2,445 sources and 1,355 people**. Every old event, edge and source
record is retained, and field-review years and career intervals stay unchanged.

Examples include O’Brien’s *Firsting and Lasting* (2010), Higginbotham’s *Righteous
Discontent* (1993), McKay and Swift’s *Warrior Nation* (2012), McKay and Bates’s
*In the Province of History* (2010), Harris’s *The Reluctant Land* (2008), and
Greer’s *Mohawk Saint* (2005). Foucault’s original publications and lecture courses
are separated from posthumous French and English editions. Greer’s *Colonial
Saints* flag is the 2000 article, not the distinct 2003 coedited book. Davis’s
“Introduction” is identified through the release’s **Representations** container
and publisher metadata: coauthored with Randolph Starn in the 1989 *Memory and
Counter-Memory* issue, not Hunt’s introduction to *The New Cultural History*.

Four scoped contributions are added, with linked field rosters and dated facts:

- O’Brien → settler colonialism, from the publisher’s description of local histories, erasure and continuing land/right claims.
- McKay → public history, crediting Bates and the institutional abstract on tourism, heritage and the production of a public past.
- Cook → Canadian women’s/gender history, the explicit coediting of *The Proper Sphere* with Wendy Mitchinson.
- Davis → memory history, the documented joint introduction with Starn; no unreviewed claim about its argument or critique of Nora.

All 45 individuals have a separate relationship decision naming the existing
edges and the reason for retaining or adding connections. Bibliographic checks
do not establish influence. New full books and articles remain unread unless
a source record explicitly identifies the description or passage checked.

The remaining unresolved record is **candidate 93**, `W:foucault|sexualitetens historia`,
labelled “História da sexualidade, Vol”. Neither the volume nor language can safely
be resolved from this mixed/truncated record. It remains visible; no volume-I
merge, new date or edge is accepted.

Research packet: `data/extension-2026/remaining-work-review-2026-10-24/`.
`review-decisions.json` preserves every original queue field and pins the CSV hash;
`reviewed/decisions.csv` in the work-gap audit is the human-readable table.
`acceptance.json` pins the production graph and prior records. The applier can
recover earlier accepted local revisions through hash-checked acceptance records,
without ignored snapshots or intermediate commits. The exact-2000 archive,
publication evidence, profile pilot and pathways are unchanged. Local only.

Validation: 96 Python cases and 57 JavaScript cases pass. Browser acceptance covers
all 51 cases; White’s test follows both field contexts to their relationship evidence.
The site builder produces 52 allowlisted files; research packets and raw citation
strings are excluded from deployment.
