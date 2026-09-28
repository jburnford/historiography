# Figure gaps — revision 1.124

On 2026-09-28 the user approved ("add the 15 in") the fifteen likely omissions of the [figure-gaps audit](../../evidence-layer/audits/figure-gaps-2026-09-27/README.md). The first of them prompted the audit. New cultural history named Geertz but not Foucault, although Hunt's *The New Cultural History* (1989) opens its "Models for Cultural History" with O'Brien, "Michel Foucault's History of Culture" (pp. 25–46).

| Entry | Added | Role | Sources |
|---|---|---|---|
| New cultural history | Michel Foucault | contributor, plus edge_766 and a strand | `obrien_foucault_1989` (JSTOR chapter opening) |
| Postcolonial history / critique | Gyan Prakash | historian | `prakash_post_orientalist_1990`, `prakash_subaltern_postcolonial_1994` |
| | Stuart Hall | contributor | `hall_diaspora`, `hall_postcolonial_1996` |
| | Paul Gilroy | contributor | `gilroy` |
| Linguistic turn / poststructuralism | Richard Rorty | contributor | `rorty_linguistic_turn_1967` |
| Frankfurt School / critical theory | Georg Lukács | precursor | `lukacs_orthodox_primary` |
| | Siegfried Kracauer | contributor | `jay_kracauer_extraterritorial` |
| Microhistory / everyday life | Natalie Zemon Davis | historian | `davis_martin_guerre_1983` |
| | Martin Broszat | historian | `broszat_bayern_1977` |
| Urban history | David Harvey | contributor | `harvey_social_justice_1973`, `harvey_place_tradition` |
| | Walter Benjamin | contributor | `benjamin_arcades_project` |
| | Michel de Certeau | contributor | `certeau` (now bibliographically checked) |
| Women's history | Leonore Davidoff; Catherine Hall (coauthor credit) | historian | `family_fortunes` |
| | Elizabeth Fox-Genovese | historian | `fox_genovese_plantation_1988` |
| Memory studies | Aby Warburg | precursor | `assmann_collective`, `warburg_institution_history` |

Other changes:
- **Strands:** two new ones, `culture.foucault_model` ("Discourse, power and the critique of social history") and `urbanhistory.space_capital_culture` ("Space, capital and the cultural city").
- **Figures lines:** New cultural history's now names all four of Hunt's models. Seven other entries have figures appended.
- **Geertz:** Biersack's chapter is added to his New cultural history record.

The prior figures line, Geertz's prior record and de Certeau's prior verification are saved in [acceptance.json](acceptance.json).

**Evidence limits:**
- The Crossref and OpenLibrary responses are saved under `raw/` and hashed in the acceptance record.
- They establish bibliographic identity only; no book or article body was reread.
- The contexts are bounded editorial readings. Each keeps the person's other contexts distinct, and none claims school membership: Kracauer was never a member of the Institute, and Rorty records the name's source, not a lineage.
- Hall's 1996 essay is identified through its 2021 reprint, and the original volume's pagination is not asserted.
- Jay's Kracauer essay is identified through its reprint and his collection *Permanent Exiles* (1985); the Salmagundi original was not checked.

**Validation:**
- Structural: zero errors, the same six warnings.
- `python3 scripts/apply_figure_gaps.py --check` reconstructs the graph exactly from `drafts/historiography-1920-2000.v1.123.json` (gitignored; its hash is pinned).
- The full local suite has the same failures before and after the revision, with one exception. `test_digital_acceptance_browser.test_production_build_matches_checked_preview` compared the published graph with the 1.123 preview byte for byte. It now does that comparison only until a later accepted revision supersedes 1.123, and still checks every other published file.

Not included: the audit's 47 critic, interlocutor and precursor candidates, which await the user's review.
