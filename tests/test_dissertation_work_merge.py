import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_dissertation_citation_graph import merge_titles  # noqa: E402

BY = {'anderson': {'imagined communities', 'imagine communities', 'imagined communites'}, 'said': {'orientalism'}}


def test_cluster_is_named_after_its_most_cited_spelling():
    counts = Counter({('anderson', 'imagined communities'): 500, ('anderson', 'imagine communities'): 3,
                      ('anderson', 'imagined communites'): 2})
    alias = merge_titles(BY, counts)
    assert alias == {('anderson', 'imagine communities'): ('anderson', 'imagined communities'),
                     ('anderson', 'imagined communites'): ('anderson', 'imagined communities')}


def test_membership_is_unchanged_by_naming():
    plain, named = merge_titles(BY), merge_titles(BY, Counter({('anderson', 'imagined communities'): 9}))
    groups = lambda a: sorted(sorted({k} | {x for x, r in a.items() if r == k} | {r for x, r in a.items() if x == k}) for k in {r for r in a.values()})  # noqa: E731
    assert {frozenset(g) for g in groups(plain)} == {frozenset(g) for g in groups(named)}
