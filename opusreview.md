# Coverage review of the curated graph — 13 September 2026

Read against editorial revision **1.105 / schema 1.4**: 109 entries, 708 relationships,
805 sources, 797 people.

This is a **coverage** review: what is not on the map. It does not assess whether what *is*
on the map is historiographically sound, and it is not a verification audit. It complements
[EDITORIAL-REVIEW.md](EDITORIAL-REVIEW.md), which reviewed the entries that exist.

Written to inform the journals-as-nodes work in progress. The last section is addressed to
that task specifically: several journals will look poorly connected, and the reason will
usually be a gap in this map rather than anything about the journal.

---

## What is not a gap

Worth stating first, so effort does not go here.

- **Structure is sound.** Zero isolated nodes. Minimum degree is 3. No orphan records.
- **Every edge is evidenced.** All 708 relationships carry both `source_ids` and an
  `evidence_note`. No exceptions.
- **Rosters are complete.** All 1,230 roster slots cite a contextual work; none are bare names.
- **Verification has moved a long way.** 691 of 805 sources have a scoped supporting-page
  check; 78 have bibliographic-metadata checks; 9 are not checked; 27 have no recorded status.

> **`EDITORIAL-REVIEW.md` is stale on this point.** Written at revision 1.9, its "Limits and
> remaining source work" section reports 51/165 supporting-page checks and "70 roster
> selections that still lack a work string." Both were closed somewhere between 1.9 and 1.105.
> That section should be updated or dated, because it currently understates the dataset.

The only routine metadata gap: **186 of 708 edges have no `classification_basis`** (522 are
`editorial_review`). Low priority, but it means "how was this classified" is unanswerable for
a quarter of the graph.

---

## The gaps

### 1. Non-Western traditions appear as subject matter, not as historiography

The deepest gap, because it is structural rather than additive.

Among **797 people there is not one Chinese, Japanese, or Korean historian.** China (85
mentions) and Japan (26) occur only *inside* Western entries — Derrida, strategic and military
scholarship, anthropology, history of science, historical demography, history of technology,
Dobb. They are objects of Western historiographical attention, never traditions with their own
institutions, debates, and practitioners.

Absent entirely: Ibn Khaldun; any Islamic or Ottoman historiographical tradition (Islam: 0
mentions, Ottoman: 3); Korean historiography (0); the Kyoto School (0). Indian historiography
is present through Subaltern Studies (Guha, Chakrabarty, Spivak, Chaudhuri) but not through
Aligarh Marxist economic history (Habib: absent) or Thapar (absent).

`scope.geographic_emphasis` declares "primarily Western academic historiography," so this is
disclosed rather than concealed. But it pulls against the teaching purpose: Hunt's argument in
*Writing History in the Global Era* is precisely about globalization forcing the discipline to
rethink, and the map's shape is the thing that argument is about. That tension is teachable,
but it should be visible in the interface rather than resting in a scope field.

**Where the map already does this well** — and the template for extending it: African history
is anchored *institutionally*, with Ibadan (7 mentions) and Dar es Salaam (10) present, not
merely through reception of European theory. Subaltern Studies likewise. Regions arrive as
traditions when they arrive with institutions.

### 2. The post-1985 cliff

Arrival decade, taken from the earliest year in each entry's date label:

| 1920s | 1930s | 1940s | 1950s | 1960s | 1970s | 1980s | 1990s |
|---|---|---|---|---|---|---|---|
| 7 | 12 | 9 | 12 | **23** | 14 | 6 | 2 |

Only eight entries arrive after 1985 — precisely the period Hunt writes about. Not represented:
history of emotions; history of the body; animal and more-than-human history; digital history;
transnational history as distinct from world history; the history of capitalism.

### 3. A third of the map carries no recorded objection

**23 of 109 entries have zero critique edges.**

The most consequential cluster: **Kuhn, Latour, SSK, and STS have no critiques at all**, and
"Science Wars" returns 0 mentions across the whole file. That is the signature epistemological
controversy of the late period, the one where historians' claims about the construction of
knowledge were contested in public, and it is missing. Also uncritiqued: oral history,
environmental history, memory studies, history of science.

For a map whose stated purpose is to let students "inspect and contest a connection, not merely
follow it," this is the gap that most undercuts the pedagogy. It is also the most tractable:
additive, well-sourced territory, no structural change required.

### 4. The discipline's own institutions are missing as objects

"Journal" appears 170 times — always as a citation, never as an entity. Peer review: 0.
Funding: 5. Professionalization: 5. PhD: 3.

There is no entry for the professionalization of history, the seminar and doctoral system,
state archives as infrastructure, or the postwar expansion of universities — which is what
actually explains the 1960s bulge in the table above. The map explains ideas by other ideas.

This gap bears directly on the journals work, which is the first move toward closing it.

### 5. "Enduring fields & genres" is lopsided

Six entries against forty schools. Missing peers with comparably long traditions: **religious
and church history** (conspicuous when Weber and Tawney are both present), legal and
constitutional history, diplomatic and international history, urban history, agrarian and rural
history, medical history, art history.

### 6. Individual entries skew early — with a visualization cost

Only **43 of 797 people have an individual entry**; the other 756 exist solely inside rosters.
That ratio is defensible — most rostered names are contextual. But the selection of which 43
get entries has drifted, and some of the omissions are load-bearing.

Most-rostered people with **no individual entry**:

| Rosters | Person | Why it is odd |
|---|---|---|
| 7 | Joan Wallach Scott | The most widely rostered person in the graph |
| 5 | Natalie Zemon Davis | |
| 5 | Charles Tilly | |
| 4 | Leopold von Ranke | "Critical historical scholarship · Ranke's preface 1824" is largely *about* him |
| 4 | Johann Gottfried Herder | Anchors historicism, which has its own entry |
| 4 | Raphael Samuel | Founder of the History Workshop movement, which has its own entry |
| 4 | Partha Chatterjee | |
| 3 | R. G. Collingwood | |
| 3 | Wilhelm Dilthey | Anchors historicism and interpretive sociology |
| 3 | W. E. B. Du Bois | |

Also roster-only: Ginzburg, Koselleck, Nora, Bourdieu, Certeau, Said, Spivak, Guha, Chakrabarty,
Gerda Lerner.

The pattern: **entries exist for people who were the object of the women-historians expansion,
and for the Annales and British Marxist circles, but not for the figures who anchor the
traditions the map already names.** Ranke, Herder, Dilthey and Collingwood are the intellectual
content of three existing entries while having no presence of their own.

This is not only a coverage question. Roster-only people have no edges, so they cannot be
selected or explored in any relationship view — they are unreachable in the field view by
construction. The later generation, and nearly every theory-side figure an MA student will
actually be assigned, is invisible as a node.

---

## Implications for the journals work

Journal nodes will inherit the gaps above. **A journal's edge count will be a function of this
map's coverage, not of the journal's standing in the discipline.** That inference is easy to
make accidentally and hard to unmake once it is in a student-facing view.

Three distinct patterns will produce thin journals, and they call for different responses.

### Pattern A — thin because the corresponding field is absent

These have **no textual anchor anywhere in the corpus** *and* no corresponding entry. Thinness
here is a true signal, pointing at gaps 1 and 5.

`Church History` · `Law and History Review` · `Bulletin of the History of Medicine` ·
`Agricultural History` · `Journal of Urban History` · `Hispanic American Historical Review` ·
`Indian Economic and Social History Review` · `Osiris`

**Response:** do not force edges. A journal with few connections *because the map lacks its
field* is evidence for adding the field. Record it as such.

### Pattern B — thin despite a strong corresponding field

These are **not named anywhere in the corpus** even though the map has substantial entries for
what they publish. This is an anchoring gap, not a coverage gap — and the easiest win available.

| Journal | Corresponding entry that already exists |
|---|---|
| `Journal of Social History` | New social history |
| `Journal of American History` | Progressive & consensus historiography; New Left & radical history |
| `Journal of Interdisciplinary History` | Quantitative history; historical demography |
| `Journal of Negro History` | Black history |
| `Oral History Review` | Oral history |
| `Gender & History` | Gender & racial formation; Women's history |
| `Journal of the History of Sexuality` | Sexuality & queer history |

**Response:** these should connect well once added. If they come out thin, suspect the linking
method rather than the map.

### Pattern C — connected, but only in one direction

The science-studies cluster is present and well populated (`Isis` alone has 59 mentions,
`Social Studies of Science` 2) but **carries zero critique edges**. Journals here will attach
through contribution and influence only, producing a picture in which the field looks
uncontested. Given that this is the Science Wars cluster, that is the most misleading possible
outcome.

**Response:** close gap 3 before or alongside adding these journals.

### Journals with strong existing anchors

For calibration — these already appear in the corpus and should connect readily:
`Annales` (198) · `Representations` (63) · `Isis` (59) · `History Workshop` (55) · `Signs` (23) ·
`Environmental History` (12) · `New Left Review` (11) · `American Historical Review` (10) ·
`Past & Present` (10) · `Comparative Studies in Society and History` (10) · `Critical Inquiry` (10).

Note that the six-journal panel in `journal-panel.json` is weighted toward the well-anchored
end. It is a reasonable pilot set but not a test of the sparse cases.

### Type the journal relation, or it will teach nothing

The instinct to threshold journals by edge count — or by impact factor — is answering the
wrong problem. The real issue is that **"publishes social history" is true of thirty journals**,
so it carries almost no information. Thresholding would simply show a student the thirty
best-connected uninformative edges.

Model the specific relations instead, and drop the weak one:

| Relation | Signal | Example |
|---|---|---|
| `founded_for` | **High.** Rare, datable, sourceable. | *Journal of Social History* (1967); *History Workshop Journal* (1976); *Annales* (1929) |
| `site_of_debate` | **High.** A named controversy a student can go and read. | Stone's "Revival of Narrative," *Past & Present* 1979 |
| `principal_venue` | Medium. Sustained and defining; editorially curated. | |
| ~~`publishes`~~ | **None.** True of nearly everything. Do not model it. | |

The admission test should be the one the rest of the graph already passes: **every edge carries
an `evidence_note`.** If a journal-to-field link cannot be stated as a specific claim with a
source, it should not be an edge. "Publishes social history" fails that test; "founded in 1967
to establish social history as a distinct field" passes it.

This also dissolves the threshold question. If journals connect only where there is a
defensible claim, degree becomes meaningful again and a sparse journal is sparse for a real
reason rather than as an artefact of weak modelling.

**On impact factor specifically:** it is a two-year citation window built for disciplines with
short citation half-lives; history's runs to decades. The OpenAlex audit already showed the
problem — 591 records with indexed references out of 127,272 indexed AHR records — so any IF
here would rest on a tiny, biased slice. It is also anachronistic for a 1920–2000 map: it
measures present standing, and would rank *Journal of Negro History* low today when in 1930 it
was the institutional home of Black history. It imports exactly the "artificial numerical
score" `DEVELOPMENT.md` rules out, and JCR values are licensed and not redistributable. If
emphasis is wanted later, a curated editorial flag is more honest than a borrowed metric.

**Display, not inclusion.** Keep every curated journal in the data. Where visual prominence
needs managing, demote rather than hide: the field view already renders set-aside entries as
thin ghost strips that stay present and clickable. A journal that is sparse because the map
lacks its field is evidence for gaps 1 and 5, and deleting it from view deletes the evidence.

### Two modelling cautions

**Relationship kind.** A journal's link to a field is not influence, contribution, critique, or
comparison. It is a venue or institutional relation — "published the debate," "institutionalized
the field," "was founded to advance it." Forcing it into the existing four kinds will corrupt
the semantics those kinds currently carry, including the colour encoding in the prototype field
view. This likely needs a fifth `relationship_kind`, with the consequences that follow for
`GRAPH-FORMAT.md`, the validator, and any renderer.

**Dates behave differently.** Unlike fields, journals have genuine durations: a real founding
year, and sometimes a real ending. They are the first records for which
`date_span.end_kind: "terminus"` is actually correct — a ceased journal *did* stop. The
crest-and-tail mark now used in the prototype assumes arrival-and-influence semantics; journals
should be capped at both ends where they have ended, and that distinction now has a drawing.
See `prototype/README.md`.

---

## Method

Findings are derived from `historiography-1920-2000.json` at revision 1.105 by direct
inspection: degree and relationship-kind distributions per node; presence tests over the
`people` array and the serialized file; arrival years parsed from `date_label` with
"coverage through YYYY" excluded. Keyword counts are raw mention counts over the serialized
JSON and indicate anchoring, not importance.

Absence claims were checked against the `people` array by name rather than inferred from the
entry list, after an initial substring pass produced false positives (E. H. Carr matched
"Carroll D. Wright"; Douglass North matched "Northrop Frye"). Both are in fact present. A
search for "Joan Scott" likewise returned nothing because the record reads "Joan Wallach
Scott" — check full name forms before recording an absence.

Gaps 1 and 5 are partly scope decisions rather than defects, and are the editors' call.
