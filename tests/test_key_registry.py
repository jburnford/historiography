"""Registry keying (scripts/key_registry.py, PID-PLAN.md rollout step 4)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from identifiers import State, apply_proposal, plan  # noqa: E402
from key_registry import clusters_for  # noqa: E402


class RegistryKeying(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        apply_proposal(self.dir, dict(ops=[
            dict(event='mint', key='new:a', type='person', label='Ian Milligan', resolution='established',
                 anchors=['atlas:person:ian_milligan']),
            dict(event='mint', key='new:b', type='person', label='Hall, Stuart', resolution='unresolved',
                 anchors=['diss-person:hall|stuart'], members=['dissertation-qid:Q1:title_verified']),
            dict(event='mint', key='new:c', type='person', label='Smith, J.', resolution='unresolved',
                 anchors=['diss-person:smith|j'], members=['dissertation-qid:Q2:probable_historian'])]),
            commit='t', date='d')
        self.state = State.load(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, rows):
        return clusters_for(rows, {}, self.state, 'vT')

    def test_atlas_person_gains_orcid(self):
        clusters, _, _ = self.build([('atlas:ian_milligan', ['atlas:ian_milligan', 'orcid:0000-0002'], [], 'Ian Milligan', ['anchored'])])
        ops, assign, held = plan(self.state, clusters)
        self.assertEqual(assign[0], 'p-1')
        self.assertIn('orcid:0000-0002', ops[0]['anchors'])

    def test_title_verified_qid_joins_the_canon_key_and_probable_only_queues(self):
        clusters, queue, _ = self.build([('orcid:1', ['orcid:1'], ['Q1'], 'Stuart Hall', ['anchored']),
                                         ('orcid:2', ['orcid:2'], ['Q2'], 'John Smith', ['anchored'])])
        _, assign, _ = plan(self.state, clusters)
        self.assertEqual(sorted(assign.values()), ['new:1', 'p-2'])
        self.assertEqual([q['kind'] for q in queue], ['probable_dissertation_qid_agrees'])

    def test_open_library_anchors_only_when_nothing_else_does(self):
        clusters, _, report = self.build([('ol:OL1A', ['ol:OL1A'], [], 'William J. Turkel', ['anchored']),
                                          ('orcid:3', ['orcid:3', 'ol:OL2A'], [], 'A Person', ['anchored'])])
        self.assertEqual(clusters[0]['anchors'], {'ol:OL1A'})
        self.assertEqual(clusters[1]['anchors'], {'orcid:3'})
        self.assertIn('ol:OL2A', clusters[1]['members'])
        self.assertEqual(report['anchored_on_open_library_only'], 1)

    def test_probable_individuals_get_no_key(self):
        clusters, _, report = self.build([('orcid:4', ['orcid:4'], [], 'Maybe', ['probable'])])
        self.assertEqual(clusters, [])
        self.assertEqual(report['probable_only_not_keyed'], 1)

    def test_an_anchor_on_two_individuals_is_dropped_and_queued(self):
        clusters, queue, _ = self.build([('orcid:5', ['orcid:5'], ['Q9'], 'A', ['anchored']),
                                         ('orcid:6', ['orcid:6'], ['Q9'], 'B', ['anchored'])])
        self.assertTrue(all('wd:Q9' not in c['anchors'] for c in clusters))
        self.assertIn('anchor_on_several_individuals', [q['kind'] for q in queue])

    def test_same_inputs_same_proposal(self):
        rows = [('orcid:7', ['orcid:7'], ['Q7'], 'X', ['anchored']), ('ol:OL3A', ['ol:OL3A'], [], 'Y', ['accepted'])]
        def ops(r):     # placeholders name the cluster's input position; the mint order is what keys follow
            return [{k: v for k, v in o.items() if k != 'key'} for o in plan(self.state, self.build(r)[0])[0]]
        self.assertEqual(ops(rows), ops(list(reversed(rows))))


if __name__ == '__main__':
    unittest.main()
