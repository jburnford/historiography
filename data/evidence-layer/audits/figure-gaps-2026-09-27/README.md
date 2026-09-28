# Figure gaps audit, 2026-09-27

This audit looks for people the review record ties to an atlas entry but the entry never names. It was prompted by one case. New cultural history named Geertz but not Foucault. Yet Hunt's *The New Cultural History* (1989) opens its "Models for Cultural History" with O'Brien, "Michel Foucault's History of Culture" (pp. 25–46), and the reviews invoke Foucault seven times as often as Geertz. The entry followed Wikipedia's Cultural history article, which names Geertz and never Foucault.

Built by `scripts/audit_figure_gaps.py --series v17 --mentions mentions-v2`. The outputs hold ids, counts and editorial judgements, and no review text.

## Method

The audit has two lenses for each atlas group entry:
- **Field:** reviews whose crosswalk theme is the entry.
- **Approach:** reviews that invoke the entry's approach by name.

For every roster person invoked in those reviews, it records:
- `k`, the number of reviews;
- `lift`, the rate in the lens divided by the rate across all 49,520 scanned reviews;
- whether the atlas already links the person to the entry: a representative person, an edge, or the full name in the entry's text;
- the entries the person *is* linked to (`linked_elsewhere`).

A candidate must pass four tests:
- the person is not linked to the entry;
- `k >= 10`;
- `lift >= 2`;
- the reviews spread over at least three years, with no single network-year holding more than half of them.

Pairs that fail only the spread test are set aside in `bursts.csv`. The largest of these, Pratibha Parmar, came from one run of H-Soz-u-Kult reviews.

## Checks

- **Known case:** in the approach lens, Foucault appears in 36 reviews at a lift of 3.9, spread over 18 years, and is unlinked. He is recovered.
- **Control:** Geertz appears in 6 reviews at a lift of 4.7 and is linked.
- **Namesakes:** 18 sampled mentions of David Harvey, Stuart Hall and Gyan Prakash all refer to the right person. The passages were read locally and not stored.

## Result (240 candidate pairs)

| Judgement | Pairs | Meaning |
|---|---|---|
| `likely_omission` | 15 | A defining figure of the field is missing: the same pattern as the Foucault case |
| `interlocutor_or_critic` | 47 | A critique, comparison or precursor edge may be warranted, not membership |
| `covered_by_entry_link` | 13 | Already reached through an entry-level edge (e.g. Historical materialism → Frankfurt School) |
| `canon_co_mention` | 82 | A widely invoked theorist co-occurring with the field's reviews |
| `not_an_error` | 83 | A subject of the reviewed books, an artefact of the lexicon's scope, or a German-corpus co-mention |

Likely omissions, all awaiting the user's editorial review:

| Entry | Figure | Basis |
|---|---|---|
| New cultural history | Michel Foucault | Hunt 1989, ch. 1 (O'Brien) |
| Postcolonial history / critique | Gyan Prakash | CSSH 1990; AHR 1994 |
| Postcolonial history / critique | Stuart Hall | Postcolonial cultural theory |
| Postcolonial history / critique | Paul Gilroy | *The Black Atlantic* (1993) |
| Linguistic turn / poststructuralism | Richard Rorty | *The Linguistic Turn* (1967) named it |
| Frankfurt School / critical theory | György Lukács | *History and Class Consciousness* (1923) |
| Frankfurt School / critical theory | Siegfried Kracauer | Frankfurt milieu; the atlas has him only in microhistory |
| Microhistory / everyday life | Natalie Zemon Davis | *The Return of Martin Guerre* (1983) |
| Microhistory / everyday life | Martin Broszat | Bavaria Project (1977–83), Alltagsgeschichte |
| Urban history | David Harvey | *Social Justice and the City* (1973) |
| Urban history | Walter Benjamin | The Arcades Project |
| Urban history | Michel de Certeau | "Walking in the City" (1980) |
| Women's history | Leonore Davidoff | *Family Fortunes* (1987, with Hall) |
| Women's history | Elizabeth Fox-Genovese | *Within the Plantation Household* (1988) |
| Memory studies | Aby Warburg | Social memory, *Mnemosyne* |

Urban history shows the same shape as New cultural history. Its people are all social-science urban historians, and the spatial and cultural turn (Harvey, Benjamin, de Certeau) is missing.

Judgements are the assistant's historiographical readings. Like the Foucault case, each should be checked against the field's own defining texts before a revision batch changes the curated graph.
