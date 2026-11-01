"""Rule merges never settle a held question (scripts/merge_guard.py; Fable review 2026-11-01)."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State, apply_proposal, plan  # noqa: E402
from merge_guard import conflict_keys, guarded  # noqa: E402


def person(label, *anchors):
    return dict(type='person', label=label, anchors=set(anchors), members=set(), aliases=set(), resolution='established')


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        apply_proposal(self.dir, dict(ops=[
            dict(event='mint', key='new:a', type='person', label='Young, Robert', resolution='established',
                 anchors=['diss-person:young|robert']),
            dict(event='mint', key='new:b', type='person', label='Young, Robert J. C.', resolution='unresolved',
                 anchors=['diss-person:young|robert j']),
            dict(event='mint', key='new:c', type='person', label='Robert J. C. Young', resolution='established',
                 anchors=['orcid:0000-0003-1754-2642'])]), commit='t', date='d')
        self.state = State.load(self.dir)
        self.queues = self.dir / 'queues'
        (self.queues / 'lc-canon').mkdir(parents=True)
        (self.queues / 'lc-canon' / 'merge-review-queue.json').write_text(json.dumps(
            [dict(kind='shared_lcnaf', lcnaf='n85198162', keys=['p-1', 'p-2'])]))
        # the rule's cluster reaches the bare-name key and the ORCID key
        self.cluster = person('Robert J. C. Young', 'diss-person:young|robert', 'orcid:0000-0003-1754-2642', 'wd:Q7345847')

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_key_in_an_open_conflict_is_not_merged_by_a_rule(self):
        blocked = conflict_keys(self.state, self.queues, self.dir / 'none.json')
        self.assertEqual(blocked, {'p-1', 'p-2'})
        ops, _, held = plan(self.state, [self.cluster], guarded(self.state, lambda c, ks: True, blocked))
        self.assertNotIn('merge', [o['event'] for o in ops])
        self.assertTrue(held)

    def test_a_decided_conflict_releases_its_keys(self):
        decisions = self.dir / 'decisions.json'
        decisions.write_text(json.dumps([dict(kind='shared_lcnaf', keys=['p-2', 'p-1'], decision='p-1 holds n85198162',
                                              basis='works', date='2026-11-01')]))
        blocked = conflict_keys(self.state, self.queues, decisions)
        self.assertEqual(blocked, set())
        ops, _, _ = plan(self.state, [self.cluster], guarded(self.state, lambda c, ks: True, blocked))
        self.assertIn('merge', [o['event'] for o in ops])

    def test_a_conflict_whose_keys_have_merged_is_settled(self):
        apply_proposal(self.dir, dict(ops=[dict(event='merge', key='p-2', into='p-1')]), commit='t', date='d')
        self.assertEqual(conflict_keys(State.load(self.dir), self.queues, self.dir / 'none.json'), set())

    def test_probable_links_do_not_block(self):
        (self.queues / 'lc-canon' / 'merge-review-queue.json').write_text(json.dumps(
            [dict(kind='probable_dissertation_qid_agrees', key='p-1', qid='Q1')]))
        self.assertEqual(conflict_keys(self.state, self.queues, self.dir / 'none.json'), set())


class EveryRuleMergeIsGuarded(unittest.TestCase):
    def test_scripts_pass_merge_ok_to_plan_only_through_guarded(self):
        for path in sorted((ROOT / 'scripts').glob('*.py')):
            for call in re.findall(r'= plan\(state, clusters, ([^\n]+)\)', path.read_text()):
                self.assertTrue(call.startswith('guarded('), f'{path.name}: plan(..., {call})')


if __name__ == '__main__':
    unittest.main()
