import unittest
from copy import deepcopy

from scripts import build_extension_release_candidate as m


class ExtensionReleaseCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = m.read(m.GRAPH)
        cls.candidate = m.prepare(cls.before)
        cls.after = m.project(cls.before, cls.candidate)

    def test_references_and_production_preservation(self):
        self.assertEqual(m.verify_inputs(), [])
        errors, warnings = m.audit(self.before, self.after, self.candidate)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 4)
        self.assertEqual(self.before['edges'], self.after['edges'])
        self.assertEqual(self.before['journal_catalogue'], self.after['journal_catalogue'])

    def test_stale_baseline_rejected(self):
        before = deepcopy(self.before)
        before['people'][0]['label'] += ' stale edit'
        with self.assertRaisesRegex(ValueError, 'exact production baseline'):
            m.project(before, self.candidate)

    def test_source_scope_and_review_status_survive(self):
        original = {c['id']:c for c in m.read(m.PACKET/'batch.json')['claims']}
        for c in self.candidate['catalogue_additions']['claims']:
            self.assertEqual(c['evidence'], original[c['id']]['evidence'])
            self.assertEqual(c['review']['status'], 'needs_review')
            self.assertEqual((c['subject'], c['object']), (original[c['id']]['subject'], original[c['id']]['object']))

    def test_description_only_claim_cannot_enter_recommended_subset(self):
        decisions = m.read(m.OUT/'review-decisions.json')
        for d in decisions['claims']:
            if d['claim_id'].endswith(':owens_patients'):
                d['decision'] = 'recommend_bounded_acceptance'
        with self.assertRaisesRegex(ValueError, 'Description-only'):
            m.prepare(self.before, decisions=decisions)

    def test_coauthor_loss_is_rejected(self):
        after = deepcopy(self.after)
        after['claim_catalogue']['claims'] = [c for c in after['claim_catalogue']['claims']
            if not (c['predicate'] == 'authored' and c['subject'] == 'person:niyah_campbell')]
        errors, _ = m.audit(self.before, after, self.candidate)
        self.assertTrue(any('Incomplete authorship' in e for e in errors))

    def test_old_roster_and_wider_context_cannot_be_replaced(self):
        after = deepcopy(self.after)
        next(n for n in after['nodes'] if n['id'] == 'spatialhistory')['representative_people'].pop(0)
        errors, _ = m.audit(self.before, after, self.candidate)
        self.assertTrue(any('Prior node representative_people' in e for e in errors))

    def test_reprint_and_cutoff_do_not_become_intervention_dates(self):
        spatial = next(n for n in self.after['nodes'] if n['id'] == 'spatialhistory')
        mck = next(s for s in spatial['strands'] if s['id'] == 'extension05_mckittrick_demonic_2006')
        self.assertEqual(mck['intervention_year'], 2006)
        self.assertEqual(spatial['extension_coverage']['publication_years'], [2002, 2006, 2007, 2013, 2024, 2025])
        self.assertEqual(self.after['scope']['main_period'], [1920, 2000])
        self.assertEqual(self.after['scope']['extension']['proposed_view_period'], [1920, 2026])

    def test_existing_gregory_identity_and_context_reused(self):
        self.assertEqual(sum(p['id'] == 'ian_gregory' for p in self.after['people']), 1)
        before = next(n for n in self.before['nodes'] if n['id'] == 'spatialhistory')
        after = next(n for n in self.after['nodes'] if n['id'] == 'spatialhistory')
        self.assertEqual(next(p for p in before['representative_people'] if p['person_id'] == 'ian_gregory'),
                         next(p for p in after['representative_people'] if p['person_id'] == 'ian_gregory'))
        strand = next(s for s in after['strands'] if s['id'] == 'extension05_gregory_healey_hgis_2007')
        self.assertEqual(strand['person_ids'], ['ian_gregory', 'richard_g_healey'])


if __name__ == '__main__':
    unittest.main()
