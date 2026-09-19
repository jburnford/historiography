import unittest

from scripts.rank_wikidata_historians import ranked, score_components
from scripts.build_historian_signal_catalog import classify


class DiscoveryRankingTests(unittest.TestCase):
    def test_missing_evidence_does_not_renormalize_weights(self):
        self.assertEqual(sum(score_components(0, 0, 0, 0).values()), 0)
        self.assertAlmostEqual(sum(score_components(50, 0, 0, 0).values()), 65)
        self.assertAlmostEqual(sum(score_components(0, 3, 2, 3).values()), 35)

    def test_caps_and_monotonicity(self):
        self.assertAlmostEqual(sum(score_components(500, 100, 100, 100).values()), 100)
        scores = [sum(score_components(n, 0, 0, 0).values()) for n in range(51)]
        self.assertEqual(scores, sorted(scores))
        self.assertGreater(scores[1] - scores[0], scores[20] - scores[19])
        with self.assertRaises(ValueError):
            score_components(-1, 0, 0, 0)

    def test_equal_scores_share_rank_with_stable_order(self):
        rows = [{'qid': 'Q2', 'label': 'B', 'score': 10, 'wikipedia_editions': 2},
                {'qid': 'Q1', 'label': 'A', 'score': 10, 'wikipedia_editions': 2},
                {'qid': 'Q3', 'label': 'C', 'score': 0, 'wikipedia_editions': 0}]
        result = list(ranked(rows))
        self.assertEqual([r['rank'] for r in result], [1, 1, 3])
        self.assertEqual([r['qid'] for r in result], ['Q1', 'Q2', 'Q3'])

    def test_generic_honours_and_ordinary_memberships_not_scored(self):
        for prop, obj in [('P166', {'label': 'Order of Merit', 'description': 'state decoration'}),
                          ('P463', {'label': 'Royal Historical Society', 'description': 'historical society'}),
                          ('P463', {'label': 'Saint Petersburg Academy of Sciences', 'description': 'historical academy (1724–1917)'}),
                          ('P39', {'label': 'member of the Second Chamber', 'description': 'member of a historic parliament'})]:
            self.assertFalse(classify(prop, 'Q1', obj, {})[0])

    def test_history_award_and_leadership_are_scored(self):
        self.assertTrue(classify('P166', 'Q724144', {'label': 'Bancroft Prize', 'description': 'award for books on American history'}, {})[0])
        self.assertTrue(classify('P39', 'Q2', {'label': 'President of the British Society for the History of Science'}, {})[0])

    def test_fellowship_and_academy_membership_deduplicate(self):
        award = classify('P166', 'Q1', {'label': 'Fellow of the British Academy'}, {})
        membership = classify('P463', 'Q2', {'label': 'British Academy'}, {})
        self.assertTrue(award[0] and membership[0])
        self.assertEqual(award[1], membership[1])

    def test_reference_editions_collapse(self):
        first = classify('P1343', 'Q1', {'label': 'Encyclopædia Britannica 11th edition'}, {})
        second = classify('P1343', 'Q2', {'label': 'Encyclopædia Britannica Ninth Edition'}, {})
        self.assertTrue(first[0] and second[0])
        self.assertEqual(first[1], second[1])

    def test_police_and_authority_records_not_reference_points(self):
        self.assertFalse(classify('P1343', 'Q1', {'description': 'biographical database of the secret police'}, {})[0])
        self.assertFalse(classify('P1343', 'Q2', {'description': 'regional authority collection'}, {})[0])

    def test_historical_fiction_and_alternate_history_award_excluded(self):
        self.assertFalse(classify('P800', 'Q1', {'label': 'A History of Somewhere', 'description': 'historical novel'}, {})[0])
        self.assertFalse(classify('P166', 'Q2', {'label': 'Sidewise Award for Alternate History'}, {})[0])

    def test_work_subject_supplies_provisional_relevance(self):
        work = {'label': 'An opaque title', 'subjects': 'http://www.wikidata.org/entity/Q2'}
        self.assertTrue(classify('P800', 'Q1', work, {'Q2': {'label': 'economic history'}})[0])
        self.assertFalse(classify('P800', 'Q1', work, {})[0])

    def test_unknown_value_never_scores(self):
        self.assertFalse(classify('P800', 'http://www.wikidata.org/.well-known/genid/x', {'label': 'History'}, {})[0])


if __name__ == '__main__':
    unittest.main()
