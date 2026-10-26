"""Protect the all-entry relationship audit and its source-scoped additions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/field-research/response-edge-audit-2026-10-25'
PACKET = ROOT / 'data/extension-2026/response-edges-2026-10-25'


def read(path):
    return json.loads(path.read_text())


class ResponseEdgeAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        batch = Batch(PACKET)
        cls.before = batch.baseline()
        cls.after = batch.check()
        cls.packet = read(batch.packet)
        cls.edges = {e['id']: e for e in cls.after['edges']}

    def test_every_original_entry_has_one_reasoned_semantic_screen(self):
        report = read(AUDIT / 'all-node-audit.json')
        rows = report['nodes']
        expected = {n['id'] for n in self.before['nodes']}
        self.assertEqual(len(rows), 357)
        self.assertEqual(len({r['node_id'] for r in rows}), len(rows))
        self.assertEqual({r['node_id'] for r in rows}, expected)
        self.assertEqual(report['unreviewed_node_ids'], [])
        for row in rows:
            degree = sum(row['node_id'] in (e['source'], e['target'])
                         for e in self.before['edges'])
            self.assertEqual(row['existing_edge_count'], degree, row['node_id'])
            self.assertTrue(row['assessment'], row['node_id'])
            self.assertTrue(row['extent'], row['node_id'])

    def test_prior_claims_sources_people_and_chronology_survive_the_review(self):
        revisions = self.packet['edge_revisions']
        for old in self.before['edges']:
            expected = dict(old, **revisions.get(old['id'], {}))
            self.assertEqual(self.edges[old['id']], expected, old['id'])
        self.assertEqual(self.after['people'], self.before['people'])
        expected_nodes = deepcopy(self.before['nodes'])
        for revision in self.packet.get('text_revisions', []):
            self.assertEqual(revision['field'], 'edge_id')
            self.assertEqual(revision['new'], '')
            node = next(n for n in expected_nodes if n['id'] == revision['node'])
            row = next(r for r in node['representative_people']
                       if r['person_id'] == revision['person_id'])
            self.assertEqual(row['edge_id'], revision['old'])
            row['edge_id'] = ''
        self.assertEqual(self.after['nodes'], expected_nodes)
        sources = {s['id']: s for s in self.after['sources']}
        for old in self.before['sources']:
            current = sources[old['id']]
            for field in ('title', 'citation', 'url', 'scope_note', 'claim_source_record_id'):
                self.assertEqual(old.get(field), current.get(field), old['id'])
            self.assertIn(old.get('verification', {}).get('note', ''),
                          current.get('verification', {}).get('note', ''), old['id'])
        for field in ('scope', 'periods', 'layers', 'claim_catalogue', 'journal_catalogue'):
            self.assertEqual(self.before[field], self.after[field], field)

    def test_turner_bloch_and_archived_web_connections_reach_the_actual_entries(self):
        self.assertEqual(self.edges['edge_951']['target'], 'frederick_jackson_turner')
        self.assertEqual(self.edges['edge_957']['target'], 'frederick_jackson_turner')
        critiques = {e['source'] for e in self.after['edges']
                     if e['target'] == 'frederick_jackson_turner'
                     and e['relationship_kind'] == 'critique'}
        self.assertTrue({'j_m_s_careless', 'donald_creighton', 'william_cronon',
                         'richard_white', 'richard_hofstadter', 'philip_j_deloria',
                         'alan_taylor'} <= critiques)
        pairs = {(e['source'], e['target'], e['relationship_kind'])
                 for e in self.after['edges']}
        self.assertIn(('lucien_febvre', 'marc_bloch', 'influence'), pairs)
        self.assertIn(('marc_bloch', 'durkheim', 'critique'), pairs)
        self.assertIn(('durkheim', 'marc_bloch', 'influence'), pairs)
        self.assertNotIn(('emile_durkheim', 'marc_bloch', 'influence'), pairs)
        adjacency = {n['id']: set() for n in self.after['nodes']}
        for edge in self.after['edges']:
            adjacency[edge['source']].add(edge['target'])
            adjacency[edge['target']].add(edge['source'])
        pending, seen = ['web_history'], set()
        while pending:
            pid = pending.pop()
            if pid in seen:
                continue
            seen.add(pid)
            pending.extend(adjacency[pid] - seen)
        self.assertEqual(seen, set(adjacency))

    def test_names_joint_authorship_and_overlapping_criticisms_are_not_collapsed(self):
        before = {e['id']: e for e in self.before['edges']}
        for eid in ('edge_617', 'edge_618', 'edge_730'):
            self.assertEqual(self.edges[eid], before[eid], eid)
        for source in ('rogers_brubaker', 'frederick_cooper'):
            for target in ('stuart_hall', 'racial_formation'):
                matches = [e for e in self.after['edges']
                           if (e['source'], e['target'], e['relationship_kind'])
                           == (source, target, 'critique')]
                self.assertEqual(len(matches), 1, (source, target))
                self.assertIn('rt186_brubaker_identity', matches[0]['source_ids'])
        johnson = [e for e in self.after['edges']
                   if (e['source'], e['target'], e['relationship_kind'])
                   == ('walter_johnson', 'eugene_genovese', 'critique')]
        self.assertEqual(len(johnson), 1)
        self.assertGreaterEqual(len(johnson[0]['source_ids']), 2)
        self.assertIn('2001', johnson[0]['evidence_note'])
        self.assertIn('2003', johnson[0]['evidence_note'])


class LeGoffRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        batch = Batch(ROOT / 'data/extension-2026/le-goff-relationships-2026-10-25')
        cls.before = batch.baseline()
        cls.after = batch.check()
        cls.packet = read(batch.packet)

    def test_supplement_preserves_earlier_claims_biographies_and_source_limits(self):
        self.assertEqual(self.before['nodes'], self.after['nodes'])
        self.assertEqual(self.before['people'], self.after['people'])
        self.assertEqual(self.before['edges'], self.after['edges'][:len(self.before['edges'])])
        self.assertEqual(self.before['revision_history'], self.after['revision_history'][:-1])
        after_sources = {s['id']: s for s in self.after['sources']}
        for old in self.before['sources']:
            current = deepcopy(after_sources[old['id']])
            if old['id'] in self.packet['source_addenda']:
                self.assertTrue(current['verification']['note'].startswith(old['verification']['note']))
                current['verification'] = old['verification']
            self.assertEqual(old, current, old['id'])
        for field in ('scope', 'layers', 'periods', 'claim_catalogue', 'journal_catalogue'):
            self.assertEqual(self.before[field], self.after[field], field)

    def test_le_goff_has_named_resources_and_qualified_critical_exchange(self):
        added = self.after['edges'][len(self.before['edges']):]
        self.assertTrue(all('jacques_le_goff' in (e['source'], e['target']) for e in added))
        pairs = {(e['source'], e['target'], e['relationship_kind']) for e in added}
        for source in ('marc_bloch', 'fernand_braudel', 'jack_goody', 'frances_yates'):
            self.assertIn((source, 'jacques_le_goff', 'influence'), pairs)
        for source in ('lucien_febvre', 'pierre_nora'):
            self.assertIn((source, 'jacques_le_goff', 'contribution'), pairs)
        for source in ('natalie_zemon_davis', 'philippe_aries'):
            self.assertIn((source, 'jacques_le_goff', 'critique'), pairs)
        self.assertIn(('jacques_le_goff', 'georges_duby', 'critique'), pairs)
        self.assertIn(('jacques_le_goff', 'fernand_braudel', 'critique'), pairs)
        self.assertIn(('jacques_le_goff', 'memory', 'contribution'), pairs)
        # The Canadian agricultural controversy concerns T. J. A. Le Goff.
        self.assertFalse(any('pe137_ouellet_le_goff_1974' in e['source_ids'] for e in added))
        sources = {s['id']: s for s in self.after['sources']}
        memoria = sources['lg_memory_memoria_1990']
        self.assertIn('Irene Ferreira', memoria['citation'])
        self.assertIn('not an original essay date', memoria['verification']['note'])


if __name__ == '__main__':
    unittest.main()
