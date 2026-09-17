"""Protect uncertain identities, publication chronology and venue semantics."""
import copy
import json
import unittest
from pathlib import Path
from scripts.build_journal_catalogue import make_catalogue, normalized_title
from scripts.validate_journal_catalogue import validate_catalogue, valid_issn

ROOT = Path(__file__).resolve().parents[1]


class JournalCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = make_catalogue()
        cls.atlas = json.loads((ROOT/'historiography-1920-2000.json').read_text())['nodes']

    def test_generated_catalogue_has_valid_references(self):
        self.assertEqual(validate_catalogue(self.catalogue, self.atlas), [])

    def test_every_input_occurrence_survives(self):
        expected = {'journal_source_sheet_271':271,'journal_source_sheet_1389':1389,'journal_source_ooir':204,'journal_source_wikipedia':337,'journal_source_toronto':10}
        for sid, count in expected.items():
            self.assertEqual(sum(o['source_id']==sid for n in self.catalogue['nodes'] for o in n.get('occurrences',[])), count)

    def test_no_loss_of_original_script_or_labor_labour_distinction(self):
        self.assertNotEqual(normalized_title('文史哲學報'), normalized_title('史學月刊'))
        self.assertNotEqual(normalized_title('Labor History'), normalized_title('Labour History'))
        self.assertTrue(any(n['label']=='文史哲學報' for n in self.catalogue['nodes']))

    def test_title_change_does_not_end_successor_or_field(self):
        nodes = {n['label']:n for n in self.catalogue['nodes']}
        old, new = nodes['Journal of Negro History'], nodes['Journal of African American History']
        self.assertEqual(old['date_span']['end_kind'], 'title_change')
        self.assertEqual(new['date_span']['start'], 2002)
        self.assertIsNone(new['publication_end'])
        self.assertTrue(any(e['predecessor']==old['id'] and e['successor']==new['id'] for e in self.catalogue['title_relationships']))

    def test_directory_membership_cannot_become_influence(self):
        data = copy.deepcopy(self.catalogue)
        data['edges'][0]['relationship_kind']='influence'
        self.assertTrue(validate_catalogue(data,self.atlas))
        self.assertTrue(all(e['relationship_kind'] in ('founded_for','site_of_debate','principal_venue') for e in self.catalogue['edges']))
        data=copy.deepcopy(self.catalogue)
        data['edges'][0]['relationship_kind']='publishes'
        self.assertTrue(validate_catalogue(data,self.atlas))

    def test_primary_source_magazine_cannot_be_research_venue(self):
        data=copy.deepcopy(self.catalogue)
        magazine=next(n for n in data['nodes'] if n.get('publication_role')=='primary_source_periodical')
        edge=data['edges'][0]
        edge['source']=magazine['id']
        self.assertTrue(validate_catalogue(data,self.atlas))

    def test_issn_checksum_and_no_impact_metrics_in_graph(self):
        self.assertTrue(valid_issn('0022-0507'))
        self.assertFalse(valid_issn('0022-0508'))
        data=copy.deepcopy(self.catalogue)
        data['nodes'][0]['metrics']=[{'value':2.3}]
        self.assertTrue(validate_catalogue(data,self.atlas))

    def test_debate_requires_a_named_exchange_and_readable_sources(self):
        data=copy.deepcopy(self.catalogue)
        edge=next(e for e in data['edges'] if e['relationship_kind']=='site_of_debate')
        del edge['debate_name']
        self.assertTrue(validate_catalogue(data,self.atlas))

    def test_principal_venue_requires_sustained_evidence(self):
        data=copy.deepcopy(self.catalogue)
        data['edges'][0].update(relationship_kind='principal_venue',basis='editorial_longitudinal_review')
        self.assertTrue(validate_catalogue(data,self.atlas))

    def test_no_dates_inferred_from_catalogue_year_or_archive_end(self):
        nodes={n['label']:n for n in self.catalogue['nodes']}
        self.assertIsNone(nodes['Cross-Currents: East Asian History and Culture Review']['publication_end'])
        self.assertEqual(nodes['Cross-Currents: East Asian History and Culture Review']['archive_coverage']['end'],2020)
        self.assertTrue(all(n.get('publication_start')!=2026 for n in self.catalogue['nodes']))

    def test_rebuild_is_deterministic(self):
        self.assertEqual(self.catalogue,make_catalogue())


if __name__=='__main__': unittest.main()
