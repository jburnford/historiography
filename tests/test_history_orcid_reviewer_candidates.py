import unittest

from scripts.match_history_orcids_to_reviewers import affiliation_overlap, normalized, route


class ReviewerCandidateBoundaries(unittest.TestCase):
    def test_name_keys_preserve_disambiguating_information(self):
        self.assertNotEqual(normalized('J. Smith'), normalized('John Smith'))
        self.assertNotEqual(normalized('João Silva'), normalized('Joao Silva'))
        self.assertNotEqual(normalized('王伟'), normalized('李伟'))
        self.assertEqual(normalized('Adam R. Seipp'), normalized('ADAM R SEIPP'))

    def test_affiliation_clues_do_not_match_generic_departments_or_substrings(self):
        self.assertFalse(affiliation_overlap('Department of History', 'Department of History, University of Idaho'))
        self.assertFalse(affiliation_overlap('University of York', 'University of Yorkshire'))
        self.assertFalse(affiliation_overlap('', 'University of Minnesota'))
        self.assertTrue(affiliation_overlap('History, Texas A & M University', 'Texas A&M University'))
        self.assertFalse(affiliation_overlap('University of Oxford', 'University of Warwick'))

    def test_existing_identifier_does_not_turn_a_name_match_into_acceptance(self):
        self.assertEqual(route(True, False), 'name_only')
        self.assertEqual(route(False, True), 'existing_qid_only')
        self.assertEqual(route(True, True), 'name_and_existing_qid')


if __name__ == '__main__':
    unittest.main()
