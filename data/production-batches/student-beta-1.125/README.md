# Revision 1.125: student beta and bounded roster additions

Production has **128 entries, 766 teaching relationships, 899 sources and 876
shared people**. Two documented contributions are added without changing older
claims: Said's 1988 foreword appears in the Subaltern Studies roster; Cooper's
1997 collaboration with Stoler appears in the postcolonial roster and one
internal approach. These are contextual contributions, not founding, membership
or influence claims. The source records state precisely what was read:
bibliographic description for the foreword, publisher description and contents
for the edited collection. The bodies remain unread.

[acceptance.json](acceptance.json) pins both versions and records preservation.
`python3 scripts/apply_student_beta_editorial.py --check` reconstructs the exact
transformation using the 1.124 snapshot or its hash-matched git history. The
exact-2000 baseline remains revision 1.121. The remaining figure-audit pairs
are still research candidates.

The associated local website beta adds a small initial overview download,
recoverable full-graph/profile downloads, an eight-person source-linked records
pilot and a visible landing sensitivity note. It keeps practice v17,
methods-v3 and mentions-v2. The browser suite and public-file allowlist have
been expanded. [STUDENT-TESTING.md](../../../STUDENT-TESTING.md) provides tasks
and a feedback sheet. Source/build changes to historical pins are recorded
as append-only amendments to the 1.123 acceptance manifest.

The [borderlands/disability candidate](../../extension-2026/borderlands-release-11/README.md)
is compatible with this graph but **unapplied**. No public deployment or
OpenAlex investigation occurred.
