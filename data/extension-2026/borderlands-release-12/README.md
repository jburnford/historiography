# Borderlands and disability preview after the Indigenous revision

This unapplied candidate rebases the unchanged borderlands/disability research packet onto revision **1.126**. Candidate 11 remains preserved at its original revision 1.125 baseline. The new adapter accepts no historical claim and changes no production field.

[Candidate](candidate.json), [review decisions](review-decisions.json) and [summary](summary.json) retain every source-reading limit and the pending field-boundary, earlier-root, identity, family-placement and publication-crosswalk checks.

```sh
python3 scripts/build_borderlands_release_candidate.py --check
python3 -m unittest tests.test_borderlands_release_candidate
```
