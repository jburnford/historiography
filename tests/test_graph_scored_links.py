"""Scorer-only links loader (scripts/graph_scored_links.py, 2026-11-12)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from graph_scored_links import scored_layer  # noqa: E402


def row(work, pos, key, decision, score='7.0', role='author', rule_state='', rule_key='', source='openalex'):
    return dict(work=work, role=role, position=str(pos), printed_name='X', person_key=key, score=score, runner_up_score='',
                decision=decision, n_candidates='1', top_fields='topic=high', rule_state=rule_state, rule_key=rule_key,
                source=source)


def run(rows, wi=None, review_works=(), keylog=(), linked=None, cands=None):
    rels = {'AUTHORED': [{'from': a, 'to': b} for a, b in keylog], 'EDITED': []}
    linked = linked or {'AUTHORED': [], 'EDITED': []}
    cands = cands if cands is not None else []
    rep = {}
    scored_layer(lambda p: rows, Path('x'), lambda k: k or None, lambda w: w, wi or {}, set(review_works), rels, linked,
                 cands, rep)
    return linked, cands, rep['scored_links']


class Scored(unittest.TestCase):
    def test_scorer_only_link_loads(self):
        linked, _, rep = run([row('w1', 0, 'p-1', 'link')], wi={'w1': {'kind': 'article', 'label': 'An article'}})
        [r] = linked['AUTHORED']
        self.assertEqual((r['source'], r['state'], r['score']), ('scored-links', 'scored', 7.0))

    def test_review_work_excluded_for_author_role(self):
        for wi, rv in (({'w1': {'kind': 'review', 'label': 'x'}}, ()), ({'w1': {'kind': 'article', 'label': 'Review of Y'}}, ()),
                       ({'w1': {'kind': 'article', 'label': 'x'}}, ('w1',))):
            linked, _, _ = run([row('w1', 0, 'p-1', 'link')], wi=wi, review_works=rv)
            self.assertEqual(linked['AUTHORED'], [])
        linked, _, _ = run([row('w1', 0, 'p-1', 'link', role='reviewer', source='review')], wi={'w1': {'kind': 'review', 'label': 'x'}})
        self.assertEqual(len(linked['AUTHORED']), 1)                 # the reviewer of a review is its author

    def test_same_as_rule_annotates(self):
        ex = {'from': 'p-1', 'to': 'w1', 'source': 'name-only:openalex'}
        linked, _, rep = run([row('w1', 0, 'p-1', 'link', rule_state='linked', rule_key='p-1')],
                             linked={'AUTHORED': [ex], 'EDITED': []})
        self.assertEqual(len(linked['AUTHORED']), 1)
        self.assertEqual(ex['score'], 7.0)

    def test_rule_names_another_key(self):
        linked, _, rep = run([row('w1', 0, 'p-1', 'link', rule_state='linked', rule_key='p-2')])
        self.assertEqual(linked['AUTHORED'], [])
        self.assertEqual(rep['link|rule_names_another_key'], 1)

    def test_exact_and_keylog_not_loaded(self):
        linked, _, _ = run([row('w1', 0, 'p-1', 'exact', score=''), row('w2', 0, 'p-1', 'link')], keylog=[('p-1', 'w2')])
        self.assertEqual(linked['AUTHORED'], [])

    def test_review_rows_become_candidates(self):
        rows = [row('w1', 0, f'p-{i}', 'review', score=str(i)) for i in range(1, 6)]
        _, cands, _ = run(rows, cands=[{'from': 'p-5', 'to': 'w1'}])
        self.assertEqual([c['from'] for c in cands[1:]], ['p-4', 'p-3', 'p-2'])
        self.assertTrue(all(c['reason'] == 'scored-review' for c in cands[1:]))


if __name__ == '__main__':
    unittest.main()
