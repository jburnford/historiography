import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import gzip

from scripts import build_hnet_graph as hnet
from scripts.query_hnet_graph import query


HTML = '''<html><head><meta name="DC.Creator" content="Alex Smith"></head><body>
<p class="revtext"><strong>Daniel J. Cohen, Roy Rosenzweig.</strong>
<em>Digital History.</em> Philadelphia: Press, 2006. ISBN 978-0-8122-1923-4.</p>
<p class="revtext"><strong>Jane Doe, John Roe, eds.</strong>
<em>Another Book.</em> London: Press, 2014. ISBN 978-1-137-39323-4.</p>
<p class="revtext"><strong>Reviewed by</strong> Alex Smith (University A)<br/>
<strong>Published on</strong> H-Test (January, 2020)</p>
<p class="revtext"><strong>Secret essay</strong>DO NOT EXPORT THIS REVIEW BODY.</p></body></html>'''


class HnetGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root/'source'
        (self.source/'json/classic').mkdir(parents=True)
        (self.source/'html/classic').mkdir(parents=True)
        self.atlas = self.root/'atlas.json'
        self.atlas.write_text(json.dumps({'people':[{'id':'alex','label':'Alex Smith'}],
                                         'nodes':[{'id':'test','label':'Test field','entry_kind':'group'}]}))
        self.policy = self.root/'decisions.json'
        self.policy.write_text(json.dumps({'resolved_people':[], 'network_field_candidates':[
            {'network':'H-Test','field_id':'test','rationale':'Test label mapping'}]}))

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, rid='10', html=HTML, **changes):
        rec = dict(review_id=rid,era='classic',source_url=f'https://www.h-net.org/reviews/showrev.php?id={rid}',
                   wayback_url='https://web.archive.org/example',wayback_timestamp='20200201000000',
                   reviewer='Alex Smith',reviewer_affiliation='University A',network='H-Test',
                   review_date='January, 2020',book_author='First book only',book_title='First book only',
                   body_text='DO NOT EXPORT THIS REVIEW BODY. '+('text '*120),content_ok=True)
        rec.update(changes)
        path=self.source/'json/classic'/f'{rid}.json'
        path.write_text(json.dumps(rec))
        if html is not None:
            with gzip.open(self.source/'html/classic'/f'{rid}.html.gz','wb') as handle:
                handle.write(html.encode())
        return path

    def graph(self):
        return hnet.Graph(self.root/'graph.sqlite')

    def test_all_citations_recovered_without_essay(self):
        books,meta=hnet.citations(HTML,{})
        self.assertEqual([b['title'] for b in books],['Digital History','Another Book'])
        self.assertEqual(books[1]['credit'],'Jane Doe, John Roe, eds')
        self.assertEqual(books[1]['publication_year'],2014)
        self.assertNotIn('Secret essay',hnet.serial(books))
        self.assertEqual(meta['DC.Creator'],'Alex Smith')

    def test_missing_byline_never_turns_essay_italics_into_books(self):
        books,_=hnet.citations('<p class="revtext"><em>Words in an essay</em></p>',
                               {'book_title':'JSON citation title'})
        self.assertEqual(len(books),1)
        self.assertEqual(books[0]['title'],'JSON citation title')
        self.assertEqual(books[0]['extraction'],'parsed_json_fallback')

    def test_publication_header_stops_extraction_when_reviewer_is_absent(self):
        html='''<p class="revtext"><em>Actual citation</em></p>
        <p class="revtext"><strong>Published on</strong> H-Test (May, 2000)</p>
        <p class="revtext"><em>Essay reference</em></p>
        <p class="revtext"><strong>Citation: URL:</strong><em>Footer reference</em></p>
        <p class="revtext">Reviewed by someone in a footer</p>'''
        books,_=hnet.citations(html,{})
        self.assertEqual([b['title'] for b in books],['Actual citation'])

    def test_email_source_identity_keeps_its_own_namespace(self):
        rec=dict(era='email',review_id='123',source_url='https://www.h-net.org/reviews/showrev.php?id=123')
        self.assertTrue(hnet.valid_source(rec,'email','123'))
        self.assertFalse(hnet.valid_source(rec,'classic','123'))

    def test_duplicate_fingerprint_ignores_source_url_footer(self):
        prefix='Actual review paragraph.'
        a=prefix+'\n\nCitation:\nReviewer. URL: id=10'
        b=prefix+'\n\nCitation:\nReviewer. URL: id=11'
        self.assertEqual(hnet.text_fingerprint(a),hnet.text_fingerprint(b))
        self.assertNotEqual(hnet.text_fingerprint(a),hnet.text_fingerprint('Different paragraph.'))

    def test_editor_and_joint_author_credits(self):
        names,_,_=hnet.split_credit('Jane Doe, John Roe, eds.')
        self.assertEqual(names,[('Jane Doe','editor'),('John Roe','editor')])
        names,_,_=hnet.split_credit('Daniel J. Cohen, Roy Rosenzweig')
        self.assertEqual(len(names),2)
        self.assertEqual(names[0][1],'contributor_unspecified')

    def test_ambiguous_names_are_not_split_into_fake_people(self):
        self.assertEqual(hnet.split_credit('Smith, John')[1],'unresolved')
        self.assertEqual(hnet.split_credit('Bill; Freund',reviewer=True)[1],'unresolved')
        self.assertEqual(hnet.split_credit('History Society')[1],'unresolved')
        self.assertEqual(hnet.split_credit('James H. Nichols, Jr',True)[0], [('James H. Nichols, Jr','reviewer')])

    def test_joint_reviewers_split_without_attaching_affiliation_as_name(self):
        names,_,_=hnet.split_credit('Ileana Apostol and Tridib Banerjee',True)
        self.assertEqual([n for n,r in names],['Ileana Apostol','Tridib Banerjee'])

    def test_initials_accents_and_name_order_remain_distinct(self):
        self.assertNotEqual(hnet.normalized('José Smith'),hnet.normalized('Jose Smith'))
        self.assertNotEqual(hnet.normalized('J. Smith'),hnet.normalized('John Smith'))
        self.assertNotEqual(hnet.normalized('Smith John'),hnet.normalized('John Smith'))

    def test_isbn_checksums_and_equivalent_formats(self):
        self.assertEqual(hnet.isbn13('0-306-40615-2'),'9780306406157')
        self.assertEqual(hnet.isbn13('978-0-306-40615-7'),'9780306406157')
        self.assertIsNone(hnet.isbn13('9780306406158'))
        self.assertIsNone(hnet.isbn13('123'))

    def test_bad_dates_are_preserved_but_not_used(self):
        self.assertEqual(hnet.review_date('January, 1970'),(None,'suspect_default_date'))
        self.assertEqual(hnet.review_date('September, 2026'),('2026-09','source_recorded'))
        self.assertEqual(hnet.review_date(None),(None,'missing_or_unparsed'))

    def test_empty_and_malformed_urls_excluded(self):
        graph=self.graph()
        for path in [self.record('1',body_text='  ',content_ok=False),
                     self.record('2',source_url='https://www.h-net.org/reviews/showrev.php?id=2broken')]:
            hnet.load_source(graph,self.source,path)
        self.assertEqual(graph.db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0],0)
        self.assertEqual(graph.db.execute('SELECT COUNT(*) FROM sources').fetchone()[0],2)
        graph.db.close()

    def test_homonyms_have_separate_mentions_and_no_automatic_person(self):
        graph=self.graph()
        for path in [self.record('10'),self.record('11',reviewer_affiliation='University B')]:
            hnet.load_source(graph,self.source,path)
        rows=graph.db.execute("SELECT id,candidate_id FROM mentions WHERE name='Alex Smith'").fetchall()
        self.assertEqual(len(rows),2)
        self.assertNotEqual(rows[0][0],rows[1][0])
        self.assertEqual(rows[0][1],rows[1][1])
        self.assertEqual(graph.db.execute("SELECT COUNT(*) FROM nodes WHERE kind='person'").fetchone()[0],0)
        self.assertEqual(graph.db.execute('SELECT COUNT(*) FROM items').fetchone()[0],2)
        hnet.decisions(graph,json.loads(self.policy.read_text()),json.loads(self.atlas.read_text()))
        self.assertEqual(graph.db.execute("SELECT status FROM edges WHERE predicate='candidate_atlas_identity'").fetchone()[0],'candidate_only')
        graph.db.close()

    def test_same_isbn_with_conflicting_title_does_not_merge(self):
        graph=self.graph()
        hnet.load_source(graph,self.source,self.record('10'))
        hnet.load_source(graph,self.source,self.record('11',html=HTML.replace('Digital History.','Different Book.')))
        self.assertEqual(graph.db.execute('SELECT COUNT(*) FROM items').fetchone()[0],3)
        graph.db.close()

    def test_repeated_name_inside_credit_preserves_both_positions(self):
        graph=self.graph()
        hnet.load_source(graph,self.source,self.record('10',html=HTML.replace('Daniel J. Cohen, Roy Rosenzweig','John Smith, John Smith')))
        rows=graph.db.execute("SELECT id FROM mentions WHERE name='John Smith'").fetchall()
        self.assertEqual(len(rows),2)
        self.assertNotEqual(rows[0],rows[1])
        graph.db.close()

    def test_reports_without_isbn_are_not_asserted_to_be_books(self):
        graph=self.graph()
        path=self.record('10',html=None,book_author=None,book_title='Annual Conference',isbn=None)
        hnet.load_source(graph,self.source,path)
        row=graph.db.execute("SELECT kind,properties FROM nodes WHERE label='Annual Conference'").fetchone()
        self.assertEqual(row[0],'reviewed_item')
        self.assertEqual(json.loads(row[1])['book_status'],'type_unresolved')
        graph.db.close()

    def test_identity_decisions_are_pinned_and_cannot_double_assign(self):
        graph=self.graph()
        hnet.load_source(graph,self.source,self.record())
        mid=graph.db.execute("SELECT id FROM mentions WHERE role='reviewer'").fetchone()[0]
        policy={'resolved_people':[{'id':'alex','label':'Alex Smith','rationale':'checked',
                 'evidence':[{'source':'fixture','locator':'byline'}],
                 'mentions':[{'id':mid,'source_json_sha256':'wrong'}]}]}
        with self.assertRaisesRegex(ValueError,'stale'):
            hnet.decisions(graph,policy,{'people':[],'nodes':[]})
        graph.db.close()

    def test_reviewed_resolution_preserves_occurrences_and_rejects_double_assignment(self):
        graph=self.graph()
        path=self.record()
        hnet.load_source(graph,self.source,path)
        mid=graph.db.execute("SELECT id FROM mentions WHERE role='reviewer'").fetchone()[0]
        person={'id':'alex','label':'Alex Smith','rationale':'Checked fixture affiliation',
                'evidence':[{'source':'fixture','locator':'byline'}],
                'mentions':[{'id':mid,'source_json_sha256':hnet.sha_file(path)}]}
        hnet.decisions(graph,{'resolved_people':[person]},{'people':[],'nodes':[]})
        self.assertEqual(graph.db.execute("SELECT object FROM edges WHERE predicate='identified_as'").fetchone()[0],'hnet:person:alex')
        self.assertEqual(graph.db.execute('SELECT COUNT(*) FROM mentions WHERE id=?',(mid,)).fetchone()[0],1)
        graph.db.close()
        other=hnet.Graph(self.root/'other.sqlite')
        hnet.load_source(other,self.source,path)
        with self.assertRaisesRegex(ValueError,'Duplicate, missing or stale'):
            hnet.decisions(other,{'resolved_people':[person,dict(person,id='different-alex')]},{'people':[],'nodes':[]})
        other.db.close()

    def test_read_only_queries_follow_book_and_reviewer_paths(self):
        self.record()
        hnet.build(self.source,self.root/'out',self.policy,self.atlas)
        db=self.root/'out/graph.sqlite'
        person=query(db,'person','alex smith')
        self.assertEqual(len(person['results']),1)
        self.assertEqual(person['results'][0]['affiliation'],'University A')
        network=query(db,'network','H-Test')
        self.assertEqual({x['title'] for x in network['results']},{'Digital History','Another Book'})
        self.assertEqual(query(db,'book','Digital History')['results'][0]['network'],'H-Test')
        self.assertEqual(len(query(db,'review','10')['results']),4)
        with self.assertRaises(ValueError):query(db,'person','x',limit=10000)

    def test_full_build_is_reproducible_metadata_only_and_checked(self):
        self.record('10');self.record('11')
        first=hnet.build(self.source,self.root/'out',self.policy,self.atlas)
        second=hnet.build(self.source,self.root/'out2',self.policy,self.atlas)
        self.assertEqual(first['source_fingerprint'],second['source_fingerprint'])
        for filename in ['nodes.jsonl','edges.jsonl','identity-candidates.csv']:
            self.assertEqual((self.root/'out'/filename).read_bytes(),(self.root/'out2'/filename).read_bytes())
        self.assertNotIn(b'DO NOT EXPORT THIS REVIEW BODY',(self.root/'out/nodes.jsonl').read_bytes())
        self.assertNotIn(b'DO NOT EXPORT THIS REVIEW BODY',(self.root/'out/edges.jsonl').read_bytes())
        self.assertEqual(first['counts']['duplicate_review_groups'],1)
        hnet.check(self.root/'out')
        with (self.root/'out/nodes.jsonl').open('a') as handle:handle.write('{}\n')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):hnet.check(self.root/'out')


if __name__=='__main__':
    unittest.main()
