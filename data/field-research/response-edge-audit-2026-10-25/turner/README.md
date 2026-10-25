# Turner and the wider US/economic/environmental response network

Research and semantic screen, checked **25 October 2026** against canonical
**1.191** (357 nodes, 1,595 edges, 2,951 sources, 1,426 people). **No canonical
change, biography, life record, reading export or publication is made here.**
OpenAlex remains paused.

[Node review](node-review.json) gives a reasoned row for **all 90 assigned nodes**:
existing degree and edge IDs, represented relations, individual gap/hold judgments,
selected inherited source-scope witnesses and explicit fresh-reading boundaries.
This is a semantic screen of compact entry descriptions/scopes, incident relationship
labels and selected inherited notes. It does not claim to reread every cited body,
all chronologies or all incident evidence notes, or to certify that the network is
complete. Degree is a measurement, never a completeness rule. Twenty assigned
nodes have separately itemized fresh selected witnesses.

## Reviewable proposals

[Proposals](proposals.json) recommend **17 new relationships and seven guarded
repairs of existing endpoints**, with exact claims, kinds, directions, IDs, duplicate
checks, grades and source scope. The [draft fragment](entry-draft-fragment.json)
contains the 17 candidate edge records and 12 used source records; it is a research
handoff, not an accepted extension packet. All new witness IDs begin `rea_turner_`.
The [source sheet](sources.json) records 17 research witnesses, exact URLs and
locators, selected reading extent and short excerpts. No full downloaded bodies
are committed. The prior graph records remain in [related-edge witnesses](existing-related-edges.json).

| New relationship | Kind | Evidence and boundary |
| --- | --- | --- |
| Cronon → Turner | Critique | Own 1987 selected argument; vague categories, periodization and regional alternatives |
| Turner → Cronon | Influence | Explicitly acknowledged critical organizing resource; does not endorse the thesis |
| Richard White → Turner | Critique | Selected uncollated chapter transcription plus Richard W. Steele’s substantive 1995 review |
| Hofstadter → Turner | Critique | Bogue’s 1994 quotation and precise book-page reference; Hofstadter chapter remains unread |
| Philip J. Deloria → Turner | Critique | Publisher’s 2002 primary chapter, especially printed 8–10 |
| Alan Taylor → Turner | Critique | Own 2008 review of Kluger’s recycled racial/national types |
| Wolfe ↔ Turner | Comparison | Explicit qualified agreement in 2013; containment and assimilation, not a blanket defense |
| Du Bois → Foner | Influence | Own 2015 acknowledgment of using Black Reconstruction and Du Bois’s interpretation |
| Bourdieu → Noiriel | Influence | Own 2012 acknowledgment, with school allegiance expressly disclaimed |
| Noiriel → Bourdieu | Critique | Own distinction between researched scholarship and later public interventions |
| Wittgenstein → Noiriel | Influence | Explicitly borrowed game metaphor, not wholesale philosophical agreement |
| Tilly → Vernon | Critique | Own 1994 review’s agency and democracy arguments; praises empirical work |
| Tilly → Joyce | Critique | Same primary review’s relational/causal objection; empirical praise preserved |
| Walter Johnson → Genovese | Critique | Complete 2001 rereading; hegemony and resistance, without the simplistic no-agency charge |
| Gramsci → Genovese | Influence | Johnson’s substantive explanation of the specific adaptation; mediated, not a fresh original-book reading |
| Cohen → McGirr | Influence | Explicit debt and extension in McGirr’s 2016 answer; distinct emphases are not incompatible |
| Gerstle ↔ McGirr | Comparison | McGirr’s explicit agreement on uneven state power; agreement alone does not prove transmission |

Three new relationships have explicit grade-B mediation: White’s selected
transcription plus Steele, Hofstadter through Bogue, and Gramsci’s use through
Johnson. The others use own selected statements. These distinctions remain visible
for independent review; none is promoted solely from metadata or a name match.

## Existing endpoints

The seven candidates preserve exact prior records and all substantive claims,
classifications, direction and citations:

| Edge | Proposed attribution | Reason |
| --- | --- | --- |
| 466 | David Cannadine → Dorothy Thompson | Specifically his Queen Victoria review; remove only the obsolete group-arrow introduction |
| 1137 | Tony Judt → Hobsbawm | Specifically his Age of Extremes review; remove only the obsolete no-node routing sentence |
| 629 | Wallerstein → Dobb | Specifically his criticism of the unit and definition of capitalism |
| 244 | Curtin → Atlantic history | Named Census contribution; numerical-review caveat stays |
| 204 | Demography → de Vries | Demographic resources point toward their named user; do not reverse that use |
| 347 | de Vries → Economic history | His specific demand/labour argument; distinct from the Dutch-history contribution |
| 068 | Winter → Military history | His named Great War mourning contribution; not all memory studies or operational history |

No group roster pointer requires clearing for these seven edges. Existing claims
sharing a corrected pair remain distinct records. In particular, the demographic
resource use differs from de Vries’s narrower existing household claim, and his
1994 contribution differs from the 1997 Dutch-history claim.

## Held cases and limits

The original Turner inquiry uncovered genuine coverage gaps that cannot be filled
with invented endpoints. Limerick, Bolton, George Wilson Pierson, Billington,
Glenda Riley and Margaret Washington have no standalone graph nodes; New Western
History has no group node. Their supported or bibliographic leads remain held.
Bolton’s selected 1932 address/1933 article proposes a qualified modification;
Cronon identifies Pierson’s conceptual critique and the women’s-history literature.
Those original bodies are not silently treated as read. Ruth Roach Pierson is a
different person. Neither women’s history nor Indigenous history stands in for one
unavailable named critic, and common subject matter does not prove a Turner response.

The Benson edge already concerns Turner and Beard jointly and stays mixed. Likewise,
edge 1161 combines Tilly, Lawrence, Oddy and Craig; it cannot be reassigned wholly
to Tilly. Separate freshly read Tilly claims preserve that summary. The mixed
Gramsci–Genovese/Gutman relationship stays intact. Other specific research leads
and their limits are recorded per node and in [screening holds](screening-holds.json).
This pass does not claim exhaustive coverage of Turner reception from the 1890s
to the present; unverified early and recent responses remain gaps.

## Reproduction

Run from the repository root:

```sh
python data/field-research/response-edge-audit-2026-10-25/turner/check.py
```

The check verifies all 90 assignment rows and exact degrees, source/endpoint IDs,
absence of existing new-edge pairs, all seven prior-record guards and pointer
constraints. Its hypothetical in-memory graph has **357 nodes, 1,612 edges,
2,963 sources and 1,426 people**, with **zero structural errors**; all nodes,
people, chronology and life data remain exact. [Validation](validation.json)
retains both warning lists and the unchanged canonical hash. This numerical
preview does not replace substantive approval and does not apply the proposals.
Raw PDFs, HTML, extracted text and images stay under ignored `raw/`.
