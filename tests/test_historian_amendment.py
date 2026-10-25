"""Historian corrections preserve prior evidence; personal comparisons keep author identity."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.build_dissertation_site import validate_links
from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/field-research/historian-classification-amendment-2026-10-25'


def read(path):
    return json.loads(path.read_text())


class PersonalComparisonTests(unittest.TestCase):
    def test_person_comparison_rejects_foreign_identity_and_unreviewed_work(self):
        graph = read(ROOT / 'historiography-1920-2000.json')
        decisions = read(ROOT / 'data/dissertation-layer/links.json')
        keys = {r['key'] for r in read(ROOT / 'data/dissertation-layer/site/index.json')['sources']}
        pid = 'william_cronon'
        comparison = {'intro': 'Selected works by this author.', 'question': 'Which works appear?',
                      'works': [{'person_id': pid, 'work': decisions['people'][pid]['works'][0]}]}
        decisions.setdefault('person_comparisons', {})[pid] = comparison
        validate_links(decisions, graph, keys)
        wrong = deepcopy(decisions)
        wrong['person_comparisons'][pid]['works'][0]['person_id'] = 'richard_white'
        with self.assertRaisesRegex(ValueError, 'outside this author selection'):
            validate_links(wrong, graph, keys)
        wrong = deepcopy(decisions)
        wrong['person_comparisons'][pid]['works'][0]['work'] = decisions['people']['richard_white']['works'][0]
        with self.assertRaisesRegex(ValueError, 'outside this author selection'):
            validate_links(wrong, graph, keys)


class HistorianAmendmentTests(unittest.TestCase):
    def test_user_classifications_are_additive_and_counts_are_unchanged(self):
        report = read(REVIEW / 'decisions.json')
        original = ROOT / 'data/field-research/dissertation-content-2026-10-25/classification-review.json'
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                         report['original_classification_sha256'])
        self.assertEqual({r['person_id']: r['dated_dissertations'] for r in report['decisions']},
                         {'benedict_anderson': 716, 'immanuel_wallerstein': 119, 'sidney_mintz': 127})
        self.assertTrue(all(r['classification'] == 'historian' and r['dated_dissertations'] > 100
                            for r in report['decisions']))

    def test_three_historians_retain_old_edges_dated_facts_and_identity_qualifications(self):
        before = Batch(ROOT / 'data/extension-2026/historian-anderson-2026-10-25').baseline()
        # This assertion covers the frozen three-person acceptance. Later reviewed
        # endpoint repairs are checked separately by the remaining-canon tests.
        after = Batch(ROOT / 'data/extension-2026/historian-mintz-2026-10-25').check()
        nodes = {n['id']: n for n in after['nodes']}
        people = {p['id']: p for p in after['people']}
        for pid in ('benedict_anderson', 'immanuel_wallerstein', 'sidney_mintz'):
            self.assertEqual(nodes[pid]['layer'], 'historians')
            self.assertEqual(people[pid]['node_id'], pid)
            self.assertNotIn('coverage', nodes[pid])
        self.assertEqual(before['edges'], after['edges'][:len(before['edges'])])
        for old in before['people']:
            if old.get('identity_note'):
                self.assertIn(old['identity_note'], people[old['id']]['identity_note'], old['id'])
        for old in before['nodes']:
            current = nodes[old['id']]
            self.assertEqual(old.get('coverage'), current.get('coverage'), old['id'])
            events = {e['id']: e for e in current['chronology']['events']}
            for event in old['chronology']['events']:
                self.assertEqual(event, events[event['id']], event['id'])
            self.assertEqual(old['chronology']['intervals'], current['chronology']['intervals'])


if __name__ == '__main__':
    unittest.main()
