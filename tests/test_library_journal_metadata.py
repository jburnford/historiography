import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from scripts import library_journal_metadata as runner
from scripts.library_journal_records import assess, compare, issn, parse_page, parse_marc, MODS

SAMPLE = Path(__file__).resolve().parents[1]/'data/journal-catalogue/library-api-samples/loc-past-present.xml'


class LibraryMetadataTests(unittest.TestCase):
    def node(self):
        return {'id': 'journal_test', 'label': 'Past & Present', 'aliases': [],
                'issns': ['0031-2746'], 'identity_status': 'title_matched_candidate',
                'date_span': {'start': 1952, 'end': None, 'end_kind': 'unknown'}}

    def record(self):
        return parse_page(SAMPLE.read_bytes(), 'loc')['records'][0]

    def test_issn_checksum_and_punctuation(self):
        self.assertEqual(issn('00312746'), '0031-2746')
        self.assertEqual(issn('1477-464x'), '1477-464X')
        self.assertIsNone(issn('0031-2747'))

    def test_mods_dates_do_not_promote_holdings_notes_or_marc_sentinels(self):
        r = self.record()
        self.assertIn(1952, [d['year'] for d in r['date_candidates']])
        self.assertNotIn(9999, [d['year'] for d in r['date_candidates']])
        self.assertNotIn(2008, [d['year'] for d in r['date_candidates']])
        self.assertTrue(any('2008' in n['value'] for n in r['notes']))

    def test_related_issn_is_not_record_identity(self):
        r = self.record()
        self.assertEqual(r['issns'], ['0031-2746'])
        self.assertTrue(any(i['value'] == '1477-464X' for e in r['related_items'] for i in e['identifiers']))

    def test_other_title_with_matching_words_is_not_accepted(self):
        r = self.record(); r['issns'] = ['1477-464X']
        self.assertEqual(assess(self.node(), r)['status'], 'identifier_conflict')
        n = self.node(); n['issns'] = []
        result = assess(n, r)
        self.assertEqual(result['status'], 'title_candidate')
        self.assertFalse(result['accepted'])

    def test_openalex_hints_remain_distinct_from_curated_identifiers(self):
        n = self.node(); n['issns'] = []
        self.assertEqual(assess(n, self.record(), ['0031-2746'])['status'], 'openalex_identifier_hint_match')
        n['identity_status'] = 'ambiguous_title'
        self.assertEqual(assess(n, self.record(), ['0031-2746'])['status'], 'ambiguous_catalogue_identity')

    def test_shared_cataloguing_is_flagged_and_curated_dates_preserved(self):
        a = self.record(); a.update(record_key='loc:a', identity=assess(self.node(), a))
        b = copy.deepcopy(a); b.update(provider='harvard', record_key='harvard:b')
        b['date_candidates'][0]['year'] = 1875
        node = self.node(); before = copy.deepcopy(node)
        result = compare(node, [a, b], [{'id': 'S1', 'first_publication_year': 1921, 'last_publication_year': 2025}])
        self.assertEqual(node, before)
        self.assertTrue(result['shared_cataloguing_provenance'])
        self.assertTrue(any(o['comparison_with_curated'] == 'differs' for o in result['date_observations']))
        self.assertEqual(result['cross_library_date_comparisons'][0]['result'], 'differs')
        self.assertFalse(result['date_observations'][0]['openalex_comparisons'][0]['same_number'])

    def test_diagnostics_and_html_are_not_zero_results(self):
        for raw in [b'<html>Unavailable</html>', b'<r><diagnostic>Unsupported index</diagnostic></r>']:
            with self.assertRaises(ValueError):
                parse_page(raw, 'loc')

    def test_loc_title_fallback_uses_supported_equality_relation(self):
        entry = {'node': self.node(), 'hint_issns': []}
        query = list(runner.queries(entry, 'loc'))[-1]
        self.assertEqual(query['params']['query'], 'dc.title = "Past & Present"')

    def test_harvard_title_colon_is_literal(self):
        node = self.node()
        node['label'] = 'Cross-Currents: East Asian History and Culture Review'
        query = list(runner.queries({'node': node, 'hint_issns': []}, 'harvard'))[-1]
        self.assertEqual(query['params']['title'],
                         '"Cross-Currents\\: East Asian History and Culture Review"')

    def test_marc_bibliographic_and_holdings_layers_stay_separate(self):
        xml = '''<record xmlns="http://www.loc.gov/MARC21/slim">
          <leader>00000cas a2200000 a 4500</leader><controlfield tag="001">bib1</controlfield>
          <controlfield tag="008">000000c19529999xxx</controlfield>
          <datafield tag="022" ind1=" " ind2=" "><subfield code="a">0031-2746</subfield></datafield>
          <datafield tag="245" ind1="0" ind2="0"><subfield code="a">Past &amp; Present</subfield></datafield>
          <datafield tag="362" ind1="0" ind2=" "><subfield code="a">No. 1 (Feb. 1952)-</subfield></datafield>
          <datafield tag="310" ind1=" " ind2=" "><subfield code="a">Quarterly</subfield></datafield>
          <datafield tag="853" ind1="2" ind2="0"><subfield code="8">1</subfield><subfield code="a">v.</subfield></datafield>
          <datafield tag="863" ind1="4" ind2="1"><subfield code="8">1.1</subfield><subfield code="a">70</subfield><subfield code="i">2023</subfield></datafield>
          <datafield tag="866" ind1="4" ind2="1"><subfield code="a">v.1(1952)-v.70(2023)</subfield></datafield>
          <datafield tag="785" ind1="0" ind2="0"><subfield code="x">1477-464X</subfield></datafield>
        </record>'''
        element = ET.fromstring(xml); r = parse_marc(element, 'loc')
        self.assertEqual(r['record_level'], 'bibliographic')
        self.assertTrue(r['serial'])
        self.assertEqual(r['issns'], ['0031-2746'])
        self.assertEqual(r['date_candidates'][0]['year'], 1952)
        self.assertNotIn(2023, [d['year'] for d in r['date_candidates']])
        self.assertEqual(r['holdings']['fields'][1]['subfields'][0]['value'], '1.1')
        element.find('{http://www.loc.gov/MARC21/slim}leader').text = '00000ny  a2200000 a 4500'
        r = parse_marc(element, 'loc')
        self.assertEqual(r['record_level'], 'holdings')
        self.assertEqual(r['date_candidates'], [])
        self.assertFalse(r['serial'])

    def test_request_budget_prevents_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.urlopen') as network:
            with self.assertRaisesRegex(runner.FetchError, 'request_budget'):
                runner.Client(Path(tmp), 0).get('loc', {'query': 'test'})
            network.assert_not_called()

    def test_loc_missing_record_is_preserved_and_title_fallback_continues(self):
        diagnostic = b'''<r xmlns:d="http://www.loc.gov/zing/srw/diagnostic/">
          <d:diagnostic><d:uri>info:srw/diagnostic/1/1</d:uri>
          <d:details>missing MARC record (Bib-1 1 Permanent system error)</d:details>
          </d:diagnostic></r>'''
        class FakeClient:
            def get(self, provider, params):
                return (diagnostic if 'bath.issn' in params['query'] else SAMPLE.read_bytes()), {'sha256': 'sample'}
        result = runner.fetch_provider({'node': self.node(), 'hint_issns': []}, 'loc', FakeClient())
        self.assertEqual(result['status'], 'retrieved_with_query_errors')
        self.assertEqual(len(result['query_errors']), 1)
        self.assertEqual(len(result['records']), 1)
        self.assertEqual(result['attempts'][0]['kind'], 'title')

    def test_offline_prepare_uses_no_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.urlopen') as network:
            runner.main(['--output', tmp])
            self.assertEqual(json.loads((Path(tmp)/'plan.json').read_text())['candidate_count'], 1628)
            network.assert_not_called()

    def test_pagination_reports_truncation_and_deduplicates_records(self):
        class FakeClient:
            def get(self, provider, params):
                raw = SAMPLE.read_bytes().replace(b'<zs:numberOfRecords>1', b'<zs:numberOfRecords>100')
                return raw, {'sha256': 'sample', 'params': params}
        entry = {'node': self.node(), 'hint_issns': []}
        result = runner.fetch_provider(entry, 'loc', FakeClient(), max_pages=2)
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['attempts']), 2)
        self.assertEqual(len(result['records']), 1)

    def test_resume_skips_successful_provider(self):
        class FakeClient:
            requests = 0
            cache_hits = 0
            def get(self, provider, params):
                self.requests += 1
                return SAMPLE.read_bytes(), {'sha256': 'sample'}
        with tempfile.TemporaryDirectory() as tmp:
            entry = {'node': self.node(), 'hint_issns': [], 'openalex_candidates': []}
            plan = {'catalogue_sha256': 'fixed', 'queue': [entry]}
            client = FakeClient()
            runner.run(plan, client, Path(tmp), providers=('loc',))
            runner.run(plan, client, Path(tmp), providers=('loc',))
            self.assertEqual(client.requests, 1)


if __name__ == '__main__':
    unittest.main()
