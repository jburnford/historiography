# Task 0: dissertation-guided work and chronology gaps

The user identified Richard White’s missing *Railroaded* and a selected chronology
ending in 1995. The first repair is revision 1.157, local and not published.

`scripts/audit_canonical_work_gaps.py` compares individual teaching entries with the
frozen 2026-10-23 dissertation release. It checks whether a work’s main title appears
in selected readings, dated events and the entry’s attached bibliography. The
minimum is ten citing dissertations per existing work record. Counts include the
release’s complete analysis set, including dissertations without years; the public
time explorer excludes those without years, so its totals can differ.

The script inventories **104 individual entries**. **72** have either an explicit
reviewed teaching link or a unique first-name/surname search candidate in the
explorer. Names remain discovery leads until checked through works. The other
entries stay in `matches.csv` as unmatched or ambiguous, not as zero-readership cases.
This narrow matching and the explorer’s frequency threshold can miss real matches.

The before pass produced **153 work/chronology candidates**. Five belong to White:

| Work | Citing dissertations | Before |
| --- | ---: | --- |
| Railroaded (2011) | 51 | Missing from readings, timeline and entry bibliography |
| It’s Your Misfortune and None of My Own (1991) | 50 | Missing from all three |
| Are You an Environmentalist or Do You Work for a Living? (1995) | 20 | Reading and reference present; timeline point missing |
| The Nationalization of Nature (1999) | 15 | Missing from all three |
| The Republic for Which It Stands (2017) | 10 | Missing from all three |

All five are now represented in his readings and chronology. The after pass has
**148 remaining candidates**. These are not 148 confirmed canonical omissions:
translations, alternate titles, source-only references and name attribution require
review. A reading can be present while its individual timeline point is absent.
No count establishes canonical importance, agreement or influence, and counts for
possible editions/title variants must not be added together.

White’s broader bibliographic check also adds *Remembering Ahanagran* (1998), its
2003 Washington paperback with William Cronon’s foreword, the 2010 spatial-history
working paper, the 2011 *Middle Ground* anniversary edition, the documented 2020
*California Exposures* discussion with photographer Jesse Amble White, and *Who
Killed Jane Stanford?* (2022). The original four facts and all earlier source limits
remain intact. Book metadata and supplied descriptions are distinguished from
full-book reading; the spatial-history paper was read in selected paragraphs.

Evidence and exact prior records are in the
[acceptance record](../../production-batches/person-works-1.157/acceptance.json).
Bibliography keys for the Toronto and Australian Richard Whites remain separate.
The inherited `white|richard d` key is not an accepted middle initial for the
Stanford historian. The one-citation, 2021-dated *Railroaded* variant stays unmerged
and is not used to date the 2011 publication.

Reproduce the current queue:

```bash
python3 scripts/audit_canonical_work_gaps.py --out /tmp/canonical-work-gaps
python3 scripts/apply_person_entries.py data/extension-2026/canonical-work-gaps-2026-10-24 --check
```

`before/` and `after/` retain graph/input hashes and separate readings, timeline and
bibliography flags. The before pass used revision 1.156; after uses 1.157 and the
explicit White teaching link. No other person’s entry has been edited by this audit.

## Review completed locally: revisions 1.158–1.159

The preceding before/after counts are the frozen discovery snapshots, not the
current unresolved count. Every one of the 148 rows has now been reviewed:
100 receive bibliography/chronology additions, 47 are already represented or
translation/edition reconciliations, and one truncated Foucault volume remains
unresolved. **36 individual entries change; 45 relationship reviews are recorded.**
White gains economic-history and capitalism contributions in 1.158. Four further
contributions in 1.159 connect O’Brien to settler colonialism, McKay to public
history, Cook to Canadian women’s/gender history and Davis to memory history.

[All 148 decisions](reviewed/decisions.csv) retain the corpus title/year/count,
canonical event IDs, source IDs and rationale. The full
[review ledger](../../extension-2026/remaining-work-review-2026-10-24/review-decisions.json)
includes the relationship reviews. The original CSV is hash-pinned and unchanged;
new candidates cannot silently inherit a decision. The short-main-title bug for
“Gender: …” and “Hunger: …” is repaired; translation equivalence remains editorial.

The new pass still has 57 raw title flags, of which 56 are explicitly reconciled
by the ledger. One remains pending: “História da sexualidade, Vol”, whose mixed
language/volume label cannot identify the cited volume. This record stays in
`reviewed/candidates.csv`; it is not imported or merged into volume I.

```bash
python3 scripts/audit_canonical_work_gaps.py \
  --out /tmp/canonical-work-reviewed \
  --review-ledger "$PWD/data/extension-2026/remaining-work-review-2026-10-24/review-decisions.json"
python3 scripts/apply_person_entries.py data/extension-2026/white-capitalism-2026-10-24 --check
python3 scripts/apply_person_entries.py data/extension-2026/remaining-work-review-2026-10-24 --check
```

The current batch adds 94 dated facts and preserves coauthor/editor credits,
original/translation/reprint dates, all old facts and source-reading limits. It is
a selected bibliographic repair, not a complete reading of the authors’ later
works. See the [1.159 acceptance summary](../../production-batches/person-works-1.159/README.md).
