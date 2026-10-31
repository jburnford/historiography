"""Check the timeline-canon person entries accepted as 1.232–1.234.

The packets were drafted by a researcher model and independently verified and
corrected by Claude (quality-review/claude-review.json). These tests bind the
accepted revisions to that verification: each revision reconstructs exactly,
held edges stay out, corrected endpoints and dates hold, and no living person's
birth year enters public prose.
"""
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch
from scripts.source_hosts import findings

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'data/extension-2026'
PACKETS = [EXT / f'timeline-canon-batch{b}-2026-10-31' for b in (1, 2, 3)]
REVIEW = EXT / 'timeline-canon-batches-2026-10-31/quality-review'
HELD = {
    ('nancy_christie', 'jurgen_habermas'), ('barbara_h_rosenwein', 'peter_n_stearns'),
    ('jeremy_black', 'geoffrey_parker'), ('charles_s_maier', 'memory'),
    ('t_c_smout', 'nationaltradition'), ('david_arnold', 'post'), ('david_arnold', 'foucault'),
    ('patrick_geary', 'memory'), ('mike_davis', 'newleft'), ('peter_gay', 'intellectualhistory'),
}
ADDED = {
    ('bruce_trigger', 'georges_e_sioui'), ('eric_hobsbawm', 'hugh_trevor_roper'),
    ('hugh_trevor_roper', 'nationalismstudies'), ('foucault', 'stephen_greenblatt'),
    ('geertz', 'stephen_greenblatt'), ('mike_davis', 'karl_marx'),
}


def read(path):
    return json.loads(path.read_text())


class TimelineCanon1232To1234Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batches = [Batch(p) for p in PACKETS]
        cls.graphs = [b.check() for b in cls.batches]
        cls.before = cls.batches[0].baseline()
        cls.after = cls.graphs[-1]
        cls.persons = [pid for p in PACKETS for pid in read(p / 'batch.json')['persons']]
        cls.nodes = {n['id']: n for n in cls.after['nodes']}
        cls.added = cls.after['edges'][len(cls.before['edges']):]
        cls.new_sources = cls.after['sources'][len(cls.before['sources']):]

    def test_revisions_chain_and_counts(self):
        self.assertEqual([b.cfg['revision'] for b in self.batches], ['1.232', '1.233', '1.234'])
        self.assertEqual([b.cfg['baseline_revision'] for b in self.batches], ['1.231', '1.232', '1.233'])
        self.assertEqual(len(self.persons), 32)
        self.assertEqual(len(self.after['nodes']) - len(self.before['nodes']), 32)
        self.assertEqual(len(self.added), 131)
        self.assertEqual(len(self.new_sources), 114)

    def test_earlier_records_unchanged(self):
        self.assertEqual(self.after['edges'][:len(self.before['edges'])], self.before['edges'])
        self.assertEqual(self.after['sources'][:len(self.before['sources'])], self.before['sources'])

    def test_entry_types(self):
        for pid in self.persons:
            node = self.nodes[pid]
            want = 'Individual theorist' if pid == 'stephen_greenblatt' else 'Individual historian'
            self.assertEqual(node['entry_type'], want, pid)
        self.assertEqual(self.nodes['stephen_greenblatt']['layer'], 'intellectual_connections')

    def test_held_edges_absent_and_added_edges_present(self):
        pairs = {(e['source'], e['target']) for e in self.added}
        self.assertFalse(HELD & pairs)
        self.assertLessEqual(ADDED, pairs)
        self.assertNotIn(('mike_davis', 'karl'), {(e['source'], e['target']) for e in self.added
                                                   if e['relationship_kind'] == 'critique'})

    def test_core_arguments_stated(self):
        expect = {'thomas_laqueur': 'one-sex', 'paul_kennedy': 'imperial overstretch',
                  'hugh_trevor_roper': 'General Crisis', 'stephen_greenblatt': 'Self-Fashioning',
                  'charles_e_rosenberg': 'The Cholera Years', 'charles_s_maier': 'Recasting Bourgeois Europe',
                  'e_h_carr': 'Elton', 'peter_gay': 'Freud: A Life for Our Time'}
        for pid, phrase in expect.items():
            self.assertIn(phrase, self.nodes[pid]['description'], pid)

    def test_corrected_facts(self):
        wilson = self.nodes['kathleen_wilson']
        self.assertIn('Strolling Players of Empire (2022)', wilson['representative_figures_and_works'])
        sources = {s['id']: s for s in self.after['sources']}
        self.assertEqual(sources['tc233_maier_2000']['url'], 'https://doi.org/10.2307/2651811')

    def test_no_excluded_routes(self):
        # The project's blocked-host list (scripts/source_hosts.py), applied to the accepted records
        # and to the researcher and verification files kept beside them.
        text = json.dumps([self.new_sources, self.added, [self.nodes[p] for p in self.persons]], ensure_ascii=False)
        self.assertEqual(findings(text), [])
        for name in ('claude-review.json', 'claude-verification.json', 'upgrades.json'):
            self.assertEqual(findings((REVIEW / name).read_text()), [], name)

    def test_no_living_birth_year_in_prose(self):
        for packet in PACKETS:
            for pid in read(packet / 'batch.json')['persons']:
                life = read(packet / pid / 'life-status.json')
                if life.get('death_year') or not life.get('birth_year'):
                    continue
                node = self.nodes[pid]
                prose = ' '.join(node.get(k) or '' for k in ('description', 'scope_note', 'date_label',
                                                             'representative_figures_and_works'))
                self.assertNotRegex(prose, rf"\b{life['birth_year']}\b", pid)

    def test_every_person_verified_by_claude(self):
        audit = {r['person_id']: r for r in read(REVIEW / 'final-audit.json')['people']}
        review = read(REVIEW / 'claude-review.json')
        for pid in self.persons:
            self.assertIn('claude_verification', audit[pid], pid)
            self.assertTrue(review[pid]['verification'], pid)


if __name__ == '__main__':
    unittest.main()
