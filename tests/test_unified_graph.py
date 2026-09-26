import gzip
import json
from pathlib import Path
import tempfile
import unittest

from scripts import build_hnet_graph as hnet
from scripts import build_unified_graph as unified
from scripts import query_unified_graph as query
from scripts import import_reviews_in_history as rih
from scripts import count_review_activity as activity


class UnifiedGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.atlas={
            'people':[{'id':'alex','label':'Alex Smith','node_id':'alex'}],
            'nodes':[{'id':'alex','label':'Alex Smith','entry_kind':'person','scope_note':'Qualified biography'},
                     {'id':'topic','label':'A field','entry_kind':'group','representative_people':[
                         {'person_id':'alex','role':'critic','context':'Critic, not adherent','works':'A Book',
                          'source_ids':['s'],'basis':'source_review'}],
                      'strands':[{'id':'one','title':'One approach','person_ids':['alex'],'source_ids':['s']}]},
                     {'id':'wide','label':'An umbrella','entry_kind':'group'}],
            'sources':[{'id':'s','title':'Evidence','url':'https://example.org','verification':{'status':'abstract_only'}}],
            'edges':[{'id':'comparison','source':'topic','target':'wide','relationship_kind':'comparison',
                      'directed':False,'source_ids':['s'],'evidence_note':'Comparison, not influence'}],
            'claim_catalogue':{'entities':[{'id':'person:alex','type':'person','label':'Alex Smith','legacy_person_id':'alex'},
                                          {'id':'work:book','type':'work','label':'A Book'}],
                               'source_records':[{'id':'w','provider':'Publisher','url':'https://example.org'}],
                               'claims':[{'id':'claim:one','subject':'person:alex','predicate':'authored','object':'work:book',
                                          'review':{'status':'provisional'},'qualification':'Metadata only',
                                          'evidence':[{'source_record_id':'w','scope':'abstract','limitation':'No body reading'}]}]},
            'journal_catalogue':{'sources':[],'nodes':[{'id':'j','label':'Journal','entry_kind':'periodical'}],
                                 'subject_classifications':[{'id':'classification','journal_id':'j','subject_id':'topic','source_ids':[]}]}}
        self.atlas_path=self.write('atlas.json',self.atlas)
        self.people=self.write('people.json',{'people':[{'person_id':'alex','status':'accepted',
            'wikidata':{'qid':'Q1','label':'Alex Smith'},'life':{'birth':'1970','birth_precision':'year'}}]})
        self.fields=self.write('fields.json',{'entries':[
            {'node_id':'topic','status':'accepted','match_kind':'same_concept','wikidata':{'qid':'Q10','label':'A field'}},
            {'node_id':'wide','status':'accepted','match_kind':'broader_concept','wikidata':{'qid':'Q11','label':'Broad field'}}]})
        self.decisions=self.write('decisions.json',{'people':[],'decisions':[]})
        self.wd=self.root/'wd.jsonl.gz'
        with gzip.open(self.wd,'wt') as f:
            for qid,label,rank in [('Q1','Alex Smith','normal'),('Q2','Alex Smith','normal'),('Q3','Other Person','deprecated')]:
                f.write(json.dumps({'qid':qid,'label':label,'label_en':label,'occupation_statements':[
                    {'uri':'http://www.wikidata.org/entity/statement/'+qid+'-statement','rank':rank}],
                    'date_statements':[{'property':'P569','date':'1971-01-01T00:00:00Z','precision':9,'rank':'normal'}],
                    'atlas_person_match_candidates':['alex'] if qid in ('Q1','Q2') else []})+'\n')
        self.source=self.root/'source';(self.source/'json/classic').mkdir(parents=True)
        record=dict(era='classic',review_id='1',source_url='https://www.h-net.org/reviews/showrev.php?id=1',
                    body_text='PRIVATE REVIEW BODY '+('body '*110),content_ok=True,
                    reviewer='Alex Smith',reviewer_affiliation='University A',network='H-Test',review_date='May, 2020',
                    book_title='A Book',book_author='Alex Smith',isbn='9780306406157',pub_year='2019',citation='A Book citation')
        self.record=self.write('source/json/classic/1.json',record)
        hg=hnet.Graph(self.root/'hnet.sqlite');hnet.load_source(hg,self.source,self.record)
        hnet.decisions(hg,{'resolved_people':[],'network_field_candidates':[]},self.atlas)
        hg.db.commit();hg.db.close();self.hnet=self.root/'hnet.sqlite'

    def tearDown(self):self.tmp.cleanup()

    def write(self,name,value):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False));return path

    def stage(self):
        s=unified.Stage(self.root/'stage.sqlite')
        unified.import_atlas(s,self.atlas);unified.import_hnet(s,self.hnet)
        unified.import_wikidata(s,self.wd)
        unified.import_authorities(s,json.loads(self.people.read_text()),json.loads(self.fields.read_text()))
        unified.candidates(s)
        return s

    def build(self,out='out'):
        return unified.build(self.atlas_path,self.hnet,self.wd,self.people,self.fields,self.decisions,self.root/out,64)

    def rih_fixture(self):
        root=self.root/'rih';(root/'html').mkdir(parents=True)
        html='''<div class="node-review">
        <div class="view-display-id-summary"><div class="book-details-content">
        <strong>A <em>Book</em></strong><br>edited by: Alex Smith<br>
        London, Publisher, <span class="date-display-single">2019</span>, ISBN: 9780306406157
        </div></div>
        <div class="view-display-id-reviewer"><div class="book-details-content">
        <strong>Dr Alex Smith</strong><br>Magdelen College, Oxford</div></div>
        <div class="group-footer"><p>PRIVATE RIH BODY '''+('review '*30)+'''</p>
        <div class="field-name-field-review-publication-date">May 2020</div>
        <section id="author-response"><div class="content"><div class="title">Alex Smith</div>
        <div class="timestamp">Posted: June 2020</div><p>Short thanks.</p></div></section></div></div>
        <div><h2>Related terms</h2><a href="/search?f[0]=taxonomy_vocabulary_4%3A28">Social History</a></div>'''
        (root/'html/1.html.gz').write_bytes(gzip.compress(html.encode()))
        self.write('rih/json/1.json',dict(source='reviews_in_history',review_id='1',content_ok=True,
                   body_text='PRIVATE RIH BODY '*40,source_url='https://reviews.history.ac.uk/review/1',
                   review_title='A Book',book_author=None,review_date=None,has_author_response=False))
        return root,html

    def test_rih_recovers_structured_credits_dates_and_short_response(self):
        root,html=self.rih_fixture();header=rih.parse_header(html)
        self.assertEqual(header['reviewer'],'Dr Alex Smith')
        self.assertEqual(header['affiliation'],'Magdelen College, Oxford')
        self.assertEqual(header['books'][0]['title'],'A Book')
        self.assertEqual(header['books'][0]['credit'],'edited by: Alex Smith')
        self.assertEqual(header['date_raw'],'May 2020')
        self.assertEqual(len(header['responses']),1)
        self.assertEqual(header['responses'][0]['text_length'],13)
        self.assertEqual(header['subjects'][0]['key'],'taxonomy_vocabulary_4:28')
        s=self.stage();counts=rih.import_corpus(s,root,self.root/'inventory.csv');rih.reconcile(s)
        self.assertEqual(counts['reviews'],1);unified.validate_stage(s)
        self.assertEqual(s.db.execute("SELECT count(*) FROM nodes WHERE kind='review_record'").fetchone()[0],2)
        self.assertEqual(s.db.execute("SELECT count(*) FROM links WHERE predicate='candidate_same_publication'").fetchone()[0],1)
        self.assertEqual(s.db.execute("SELECT count(*) FROM links WHERE origin='reviews_in_history' AND predicate='published_on'").fetchone()[0],0)
        roles=[json.loads(d[0])['metadata']['role'] for d in s.db.execute("SELECT data FROM nodes WHERE origin='reviews_in_history' AND kind='person_mention'")]
        self.assertCountEqual(roles,['editor','reviewer','respondent'])
        payload=' '.join(d[0] for d in s.db.execute("SELECT data FROM nodes WHERE origin='reviews_in_history'"))
        self.assertNotIn('PRIVATE RIH BODY',payload);self.assertNotIn('Short thanks.',payload)
        s.db.close();rih.verify_inventory(root,self.root/'inventory.csv')
        (root/'html/1.html.gz').write_bytes(gzip.compress((html+'changed').encode()))
        with self.assertRaisesRegex(ValueError,'source changed'):rih.verify_inventory(root,self.root/'inventory.csv')

    def test_rih_source_identity_and_empty_records_excluded(self):
        root,_=self.rih_fixture()
        row=json.loads((root/'json/1.json').read_text())
        self.write('rih/json/2.json',dict(row,review_id='2'))
        self.write('rih/json/3.json',dict(row,review_id='3',source_url='https://reviews.history.ac.uk/review/3',content_ok=False))
        s=self.stage();counts=rih.import_corpus(s,root,self.root/'inventory.csv')
        self.assertEqual(counts['reviews'],1);self.assertEqual(counts['excluded_identity'],1);self.assertEqual(counts['excluded_empty'],1)
        s.db.close()

    def test_rih_wordpress_avoids_mobile_duplicates_and_modified_dates(self):
        html='''<meta property="article:modified_time" content="2023-07-22">
        <div class="review-header"><h1>The Actual Review Title</h1></div>
        <div class="review-content"><table class="book-details desktop">
        <tr><th>Book:</th><td><strong>A Book</strong><br><span>Alex Smith</span><br>
        <span>London, Publisher, 2010, ISBN: 9780306406157</span></td></tr>
        <tr><th>Reviewer:</th><td><strong>Dr Jane Doe</strong><br>University A</td></tr>
        </table><section class="book-details mobile-table"><h4>Book:</h4><p><strong>A Book</strong></p></section>
        <ul class="related-terms-list"><li><a href="/search?taxonomies=history-type_social-history">Social History</a></li></ul>
        <section class="content"><p>Review text.</p><p>December 2010</p></section>
        <section class="responses"><section class="author-response-card"><h2 id="author-response">Author's response</h2>
        <p><strong>Alex Smith</strong><br><span>Posted: 2011</span></p><div class="card-content">Thank you.</div>
        </section></section></div>'''
        header=rih.parse_header(html)
        self.assertEqual(len(header['books']),1)
        self.assertEqual(header['books'][0]['credit'],'Alex Smith')
        self.assertEqual(header['books'][0]['publication_year'],2010)
        self.assertEqual(header['date_raw'],'December 2010')
        self.assertEqual(header['review_title'],'The Actual Review Title')
        self.assertEqual(header['responses'][0]['author'],'Alex Smith')
        self.assertEqual(header['body_length'],12)
        self.assertEqual(len(header['subjects']),1)

    def test_rih_native_profile_and_raw_fingerprint_guard(self):
        root,_=self.rih_fixture()
        report=unified.build(self.atlas_path,self.hnet,self.wd,self.people,self.fields,self.decisions,self.root/'out',64,root)
        self.assertEqual(report['reviews_in_history']['counts']['reviews'],1);unified.check(self.root/'out')
        db,conn=unified.connect_ladybug(self.root/'out/graph.lbdb',buffer_mib=64)
        try:
            profile=query.person(conn,'alex')
            self.assertEqual(len(profile['candidate_review_credits']),5)
            self.assertEqual(len(profile['candidate_hnet_credits']),2)
            self.assertIn('Reviews in History source',query.html_profile(profile))
            credit=next(c for c in profile['candidate_review_credits'] if c['source']=='rih')
            self.assertTrue(credit['source_raw_sha256'])
            tally=activity.count_activity(conn,term='Alex Smith')
            self.assertEqual(activity.count_activity(conn),tally)
            self.assertEqual(len(tally),1)
            self.assertEqual(tally[0]['books_reviewed'],2)
            self.assertEqual(tally[0]['reviews_written'],2)
            self.assertEqual(tally[0]['reviews_received'],2)
            self.assertEqual(tally[0]['books_editor'],1)
            self.assertEqual(tally[0]['books_role_unspecified'],1)
            self.assertEqual(activity.count_activity(conn,'accepted'),[])
        finally:conn.close();db.close()
        s=self.stage();rih.import_corpus(s,root,self.root/'inventory.csv')
        decision=dict(id='r',occurrence_id=credit['mention_id'],person_id='atlas:person:alex',
                      source_json_sha256=credit['source_json_sha256'],status='accepted',rationale='Checked',evidence=['fixture'])
        with self.assertRaisesRegex(ValueError,'raw source fingerprint'):unified.identity_decisions(s,{'decisions':[decision]})
        s.db.close()

    def test_sources_and_qualifications_preserved(self):
        s=self.stage();unified.validate_stage(s)
        row=s.db.execute("SELECT directed,data,evidence FROM links WHERE id='atlas:comparison'").fetchone()
        self.assertEqual(row[0],'false')
        self.assertEqual(json.loads(row[1]),self.atlas['edges'][0])
        claim=s.db.execute("SELECT data FROM links WHERE id='atlas:claim:one'").fetchone()[0]
        self.assertEqual(json.loads(claim),self.atlas['claim_catalogue']['claims'][0])
        row=s.db.execute("SELECT object FROM links WHERE id='atlas:classification'").fetchone()
        self.assertEqual(row[0],'atlas:entry:topic');s.db.close()

    def test_same_and_broader_concepts_do_not_become_person_identity(self):
        s=self.stage()
        rows=s.db.execute("SELECT predicate FROM links WHERE origin='authority' ORDER BY predicate").fetchall()
        self.assertEqual([r[0] for r in rows],['maps_to_broader_concept','maps_to_same_concept','same_person'])
        s.db.close()

    def test_homonymous_qids_remain_separate_candidates(self):
        s=self.stage()
        rows=s.db.execute("SELECT object,status FROM links WHERE predicate='candidate_wikidata_identity' ORDER BY object").fetchall()
        self.assertEqual(rows,[('wd:Q1','candidate_only'),('wd:Q2','candidate_only')])
        self.assertFalse(s.db.execute("SELECT 1 FROM links WHERE predicate='resolved_as'").fetchone())
        s.db.close()

    def test_deprecated_assertions_and_conflicting_dates_survive(self):
        s=self.stage()
        row=s.db.execute("SELECT status FROM links WHERE subject='wd:Q3' AND predicate='occupation'").fetchone()
        self.assertEqual(row[0],'deprecated')
        row=json.loads(s.db.execute("SELECT data FROM nodes WHERE id='wd:Q1'").fetchone()[0])
        self.assertEqual(row['date_statements'][0]['precision'],9)
        self.assertEqual(row['date_statements'][0]['date'],'1971-01-01T00:00:00Z')
        row=json.loads(s.db.execute("SELECT data FROM links WHERE predicate='same_person'").fetchone()[0])
        self.assertEqual(row['life']['birth'],'1970');s.db.close()

    def test_book_title_match_does_not_merge_publications(self):
        s=self.stage()
        row=s.db.execute("SELECT status,object FROM links WHERE predicate='candidate_publication_of'").fetchone()
        self.assertEqual(row,('candidate_only','atlas:catalogue:work:book'))
        self.assertEqual(s.db.execute("SELECT count(*) FROM nodes WHERE kind IN ('catalogue_work','bibliographic_item')").fetchone()[0],2)
        s.db.close()

    def test_resolution_rejects_stale_source(self):
        s=self.stage();mid=s.db.execute("SELECT id FROM nodes WHERE kind='person_mention' ORDER BY id").fetchone()[0]
        decision={'id':'d','occurrence_id':mid,'person_id':'atlas:person:alex','source_json_sha256':'wrong',
                  'status':'accepted','rationale':'Fixture review','evidence':[{'source':'fixture'}]}
        with self.assertRaisesRegex(ValueError,'Stale'):
            unified.identity_decisions(s,{'decisions':[decision]})
        s.db.close()

    def test_resolution_rejects_multiple_accepted_assignments(self):
        s=self.stage()
        mid,data=s.db.execute("SELECT id,data FROM nodes WHERE kind='person_mention' ORDER BY id").fetchone()
        decision={'id':'one','occurrence_id':mid,'person_id':'atlas:person:alex',
                  'source_json_sha256':json.loads(data)['source_json_sha256'],
                  'status':'accepted','rationale':'Fixture review','evidence':[{'source':'fixture'}]}
        with self.assertRaisesRegex(ValueError,'multiple people'):
            unified.identity_decisions(s,{'decisions':[decision,dict(decision,id='two')]})
        s.db.close()

    def test_reviewed_occurrences_leave_candidate_results(self):
        s=self.stage()
        mentions=s.db.execute("SELECT id,data FROM nodes WHERE kind='person_mention' ORDER BY id").fetchall()
        decisions=[]
        for i,(mid,data) in enumerate(mentions):
            decisions.append({'id':str(i),'occurrence_id':mid,'person_id':'atlas:person:alex',
                'source_json_sha256':json.loads(data)['source_json_sha256'],
                'status':'accepted' if i==0 else 'rejected','rationale':'Fixture evidence',
                'evidence':[{'source':'fixture'}]})
        s.db.close();self.write('decisions.json',{'people':[],'decisions':decisions})
        self.build()
        db,conn=unified.connect_ladybug(self.root/'out/graph.lbdb',buffer_mib=64)
        try:
            profile=query.person(conn,'alex')
            self.assertEqual(len(profile['accepted_hnet_credits']),1)
            self.assertEqual(profile['accepted_hnet_credits'][0]['mention_id'],mentions[0][0])
            self.assertEqual(profile['candidate_hnet_credits'],[])
        finally:conn.close();db.close()

    def test_missing_evidence_is_rejected(self):
        s=self.stage()
        s.edge('atlas:person:alex','test','wd:Q1','test',evidence=['missing'])
        with self.assertRaisesRegex(ValueError,'Missing evidence'):unified.validate_stage(s)
        s.db.close()

    def test_native_import_multiple_batches(self):
        s=self.stage();unified.validate_stage(s)
        dest=self.root/'chunks';dest.mkdir();unified.write_csv(s,dest)
        expected={name:s.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
                  for name,table in [('nodes','nodes'),('links','links')]}
        s.db.close()
        _,counts=unified.ladybug_import(dest,64,chunk_rows=10)
        self.assertEqual(counts,expected)
        self.assertFalse((dest/'import-chunk.csv').exists())

    def test_native_ladybug_roundtrip_and_person_profile(self):
        report=self.build();self.assertEqual(report['backend'],'ladybug')
        unified.check(self.root/'out')
        db,conn=unified.connect_ladybug(self.root/'out/graph.lbdb',buffer_mib=64)
        try:
            profile=query.person(conn,'alex')
            self.assertEqual(profile['wikidata_identities'][0]['id'],'wd:Q1')
            self.assertEqual(profile['atlas_contexts'][0]['selection']['role'],'critic')
            self.assertEqual(len(profile['candidate_hnet_credits']),2)
            self.assertEqual(profile['accepted_hnet_credits'],[])
            self.assertEqual(profile['catalogue_works'][0]['status'],'provisional')
            self.assertEqual(len(query.search(conn,'Alex Smith',20,'person')),1)
            self.assertTrue(query.neighbors(conn,'atlas:person:alex')['links'])
            self.assertFalse(any(r['status']=='candidate_only' for r in query.neighbors(conn,'wd:Q1')['links']))
            html=query.html_profile(profile)
            self.assertIn('not accepted credits',html)
            self.assertNotIn('PRIVATE REVIEW BODY',html)
            self.assertEqual(query.person(conn,'Missing Person')['status'],'choose_identity')
        finally:conn.close();db.close()

    def test_exports_reproduce_without_changing_inputs(self):
        report=self.build();again=self.build('out2')
        for filename in ['nodes.csv','links.csv','identity-review-seeds.csv']:
            self.assertEqual(report['files'][filename],again['files'][filename])
        for item in report['inputs'].values():self.assertEqual(unified.sha(Path(item['path'])),item['sha256'])
        self.assertNotIn(b'PRIVATE REVIEW BODY',(self.root/'out/nodes.csv').read_bytes())
        with (self.root/'out/links.csv').open('a') as f:f.write('corruption')
        with self.assertRaisesRegex(ValueError,'Generated output changed'):unified.check(self.root/'out')

    def test_html_escapes_source_supplied_strings(self):
        profile=dict(status='found',person={'id':'x','label':'<script>alert(1)</script>'},
                     atlas_entries=[],wikidata_identities=[],atlas_contexts=[],catalogue_works=[],
                     accepted_hnet_credits=[],candidate_hnet_credits=[],truncated={},sources=[])
        html=query.html_profile(profile)
        self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html)


if __name__=='__main__':unittest.main()
