import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_ahr_crossref import pagination

class PaginationTests(unittest.TestCase):
    def test_single_locator_is_not_a_one_page_length(self):
        r=pagination('1669')
        self.assertEqual(r['first_page'],1669)
        self.assertIsNone(r['last_page'])
        self.assertIsNone(r['page_count'])

    def test_explicit_one_page_and_inclusive_range(self):
        self.assertEqual(pagination('1669-1669')['page_count'],1)
        self.assertEqual(pagination('522–523')['page_count'],2)
        self.assertEqual(pagination('19—52')['page_count'],34)

    def test_abbreviation_requires_documented_expansion(self):
        r=pagination('199-03')
        self.assertEqual((r['last_page'],r['page_count']),(203,5))
        self.assertEqual(r['pagination_status'],'expanded_abbreviated_range')

    def test_complex_front_matter_missing_and_bad_ranges_remain_unresolved(self):
        for raw in [None,'','xvi','xvi-xx','S1-S5','12-14,18-20','20-10','0-5','1-1000']:
            with self.subTest(raw=raw):self.assertIsNone(pagination(raw)['page_count'])

if __name__=='__main__':unittest.main()
