# Borderlands/disability: current-graph release candidate

Prepared 10 October 2026 against the exact **revision 1.125** graph. This is an
unapplied adapter for the frozen [borderlands-disability-08 packet](../borderlands-disability-08/README.md):
two entry proposals, ten works, 31 claims, 14 source records, 13 proposed local
people and ten work-based approaches. Seventeen historical attributions have
12 passage checks and five abstract checks; the remaining claims record author
credits and versions. Existing field entries and teaching relationships are preserved.

[candidate.json](candidate.json) is pinned to the current production hash.
[review-decisions.json](review-decisions.json) keeps every claim at `needs_review`
and states the outstanding field review. [summary.json](summary.json) records
input hashes and validation: no errors, four existing duplicate-edge warnings
and four unconnected entries in the preview. No new arrows are inferred.

The adapter retains original publication dates separately from witnessed
translation, reception and manuscript dates, and keeps contributor roles and
all source captures unchanged. The historical view remains the exact 1.121
baseline. Research cutoff is the packet's September cutoff, not its October
assembly date. None of the six fields in the preview is fully reviewed.

Before production integration, review earlier roots, regional coverage, field
boundaries, each bounded attribution and the new people. Choose the two entries'
landing-family placements and evidence crosswalks. The existing landing evidence
contains production fields only, so this candidate is intended for direct-entry
review rather than as a finished landing comparison. It is absent from `docs/`.

```bash
python3 scripts/build_borderlands_release_candidate.py --check --preview /tmp/borderlands-preview.json
python3 scripts/build_site.py --graph /tmp/borderlands-preview.json --dest /tmp/borderlands-preview-site
python3 -m http.server 4174 --bind 127.0.0.1 --directory /tmp/borderlands-preview-site
```

Open `http://127.0.0.1:4174/#node=disability` or
`http://127.0.0.1:4174/#node=borderlands_history`. Preview output stays in `/tmp`.
The adapter refuses stale production hashes, conflicting identities and ID
collisions; its audit requires exact preservation of previous records and dates.
