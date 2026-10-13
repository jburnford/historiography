import json
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_people_records_asset import effective_tier, public_url
from audit_landing_evidence import run_scenario
from apply_student_beta_editorial import transform, serial
from apply_indigenous_deep_dive import baseline as indigenous_baseline
import duckdb


class ProfileAssetTests(unittest.TestCase):
    def test_weaker_link_controls_the_displayed_identity(self):
        self.assertEqual(effective_tier('probable','anchored'), 'probable')
        self.assertEqual(effective_tier('accepted','probable'), 'probable')
        self.assertEqual(effective_tier('accepted','anchored'), 'anchored')
        for tier in ('unresolved','conflicted',None):
            with self.assertRaises(ValueError):
                effective_tier(tier,'anchored')

    def test_only_public_web_links_are_allowed(self):
        self.assertIsNone(public_url('file:///tmp/record'))
        self.assertIsNone(public_url('javascript:alert(1)'))
        self.assertIsNone(public_url('https://user:secret@example.org'))
        self.assertEqual(public_url('https://doi.org/10.1/a'), 'https://doi.org/10.1/a')

    def test_asset_retains_tiers_sources_and_only_allowed_metadata(self):
        a = json.loads((ROOT / 'data/evidence-layer/site-people.json').read_text())
        self.assertEqual(len(a['people']),8)
        for pid,p in a['people'].items():
            self.assertLessEqual(set(p), {'label','atlas_identity_tier','atlas_identity_bases','counts','records'})
            self.assertTrue(p['records'], pid)
            self.assertEqual(len({r['id'] for r in p['records']}),len(p['records']))
            for r in p['records']:
                self.assertLessEqual(set(r), {'id','source_id','item_id','kind','title','year','review_year','venue','role','url',
                                              'identity_tier','credit_tier','identity_bases'})
                self.assertEqual(r['identity_tier'],effective_tier(p['atlas_identity_tier'],r['credit_tier']))
                self.assertTrue(r['source_id'])
                self.assertTrue(public_url(r['url']))
        self.assertLess((ROOT / 'data/evidence-layer/site-people.json').stat().st_size,100_000)


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.db = duckdb.connect()
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE records(record_id VARCHAR,year INT,record_type VARCHAR,is_test_record BOOLEAN,page_count INT,book_citation_title_hint BOOLEAN)')
        self.db.execute("INSERT INTO records VALUES ('a',2001,'journal-article',false,11,false),('b',2001,'journal-article',false,9,false),('c',2001,'journal-article',false,NULL,false),('d',2001,'journal-article',false,20,true),('e',2001,'journal-article',true,30,false),('f',2001,'book',false,30,false)")
        self.db.execute('CREATE TABLE memberships(record_id VARCHAR,journal_key VARCHAR)')
        self.db.execute("INSERT INTO memberships VALUES ('a','one'),('a','two'),('b','one'),('c','journal_supplement_journal_of_digital_history'),('d','one'),('e','one'),('f','one')")
        self.db.execute('CREATE TABLE themes(journal_key VARCHAR,target VARCHAR)')
        self.db.execute("INSERT INTO themes VALUES ('one','social'),('two','culture'),('journal_supplement_journal_of_digital_history','digital')")
        self.membership = [('Social','social',True),('Culture','culture',True),('Theory','digital',True)]

    def test_doi_counting_keeps_overlapping_journal_memberships_without_double_denominator(self):
        r = run_scenario(self.db,self.membership)
        self.assertEqual(r['strip']['items'],3)
        self.assertEqual(r['strip']['families']['Social'],1.5)
        self.assertEqual(r['strip']['families']['Culture'],.5)
        self.assertEqual(r['strip']['families']['Theory'],1)

    def test_threshold_screen_and_article_number_exception_are_distinct(self):
        self.assertEqual(run_scenario(self.db,self.membership,minimum=8)['strip']['items'],4)
        self.assertEqual(run_scenario(self.db,self.membership,minimum=15)['strip']['items'],2)
        r=run_scenario(self.db,self.membership,screen_titles=True)
        self.assertEqual(r['strip']['items'],2)
        self.assertEqual(r['strip']['families']['Theory'],1)


class EditorialPreservationTests(unittest.TestCase):
    def test_only_documented_additions_change_the_exact_prior_graph(self):
        graph=indigenous_baseline()
        record=json.loads((ROOT/'data/production-batches/student-beta-1.125/acceptance.json').read_text())
        before=deepcopy(graph)
        self.assertEqual(before['revision_history'].pop()['version'],'1.125')
        self.assertEqual([s['id'] for s in before['sources'][-2:]],['said_subaltern_foreword_1988','cooper_stoler_tensions_1997'])
        del before['sources'][-2:]
        nodes={n['id']:n for n in before['nodes']}
        for nid,pid,sid in [('subaltern','edward_said','said_subaltern_foreword_1988'),('post','frederick_cooper','cooper_stoler_tensions_1997')]:
            added=nodes[nid]['representative_people'].pop()
            self.assertEqual((added['person_id'],added['role']),(pid,'contributor'))
            self.assertEqual(nodes[nid]['source_ids'].pop(),sid)
        self.assertEqual(nodes['post']['strands'].pop()['id'],'metropole_colony')
        self.assertEqual(hashlib.sha256(serial(before).encode()).hexdigest(),record['baseline_sha256'])
        self.assertEqual(transform(before),graph)
        self.assertEqual(hashlib.sha256(serial(graph).encode()).hexdigest(),record['production_sha256'])


if __name__ == '__main__':
    unittest.main()
