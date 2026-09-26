"""Identity repair regression tests: evidence, homonyms, slots and full rebuilds."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import repair_groundings as repair


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.occ=[{'occurrence_id':'a','occurrence_fingerprint':'hash-a','legacy_qid':'Q10'},
                  {'occurrence_id':'b','occurrence_fingerprint':'hash-b','legacy_qid':None}]
        self.ledger={'people':[{'id':'person-a','preferred_qid':'Q20'}, {'id':'person-b','preferred_qid':'Q30'}],
                     'evidence':[{'id':'book-source'}], 'decisions':[]}

    def decision(self,oid='a',pid='person-a',status='accepted'):
        o=next(o for o in self.occ if o['occurrence_id']==oid)
        return dict(id='d-'+oid,occurrence_id=oid,occurrence_fingerprint=o['occurrence_fingerprint'],
                    legacy_qid=o['legacy_qid'],status=status,person_id=pid,
                    rationale='Book and affiliation identify this individual.',evidence=['book-source'])

    def test_wrong_id_replaced_and_old_assignment_retained(self):
        d=self.decision();d['rejected_qids']=['Q10'];self.ledger['decisions']=[d]
        r=repair.resolve(self.occ,self.ledger)
        self.assertEqual((r[0]['legacy_qid'],r[0]['effective_qid']),('Q10','Q20'))
        self.assertIsNone(r[1]['effective_qid'])

    def test_identical_names_can_resolve_to_distinct_people(self):
        for o in self.occ:o['name']='Mark Harrison'
        self.ledger['decisions']=[self.decision(),self.decision('b','person-b')]
        self.assertEqual([o['effective_qid'] for o in repair.resolve(self.occ,self.ledger)],['Q20','Q30'])

    def test_rejection_is_not_ignored_for_lack_of_replacement(self):
        self.ledger['decisions']=[self.decision(pid=None,status='rejected')]
        r=repair.resolve(self.occ,self.ledger)[0]
        self.assertIsNone(r['effective_qid']);self.assertEqual(r['identity_status'],'rejected')

    def test_unresolved_is_explicitly_unaccepted(self):
        self.ledger['decisions']=[self.decision(pid=None,status='unresolved')]
        r=repair.resolve(self.occ,self.ledger)[0]
        self.assertEqual(r['effective_qid'],'Q10');self.assertIsNone(r['person_id'])
        self.assertEqual(r['identity_status'],'unresolved')

    def test_conflicting_decisions_fail_regardless_of_order(self):
        first=self.decision();second=dict(self.decision(pid='person-b'),id='other')
        for ds in ([first,second],[second,first]):
            self.ledger['decisions']=ds
            with self.assertRaisesRegex(ValueError,'Conflicting'):repair.resolve(self.occ,self.ledger)

    def test_stale_source_or_old_id_fails(self):
        for field,value in [('occurrence_fingerprint','changed'),('legacy_qid','Q99')]:
            d=self.decision();d[field]=value;self.ledger['decisions']=[d]
            with self.assertRaisesRegex(ValueError,'Stale'):repair.resolve(self.occ,self.ledger)

    def test_missing_evidence_and_accepted_rejection_fail(self):
        for change in [{'evidence':[]},{'evidence':['absent']},{'rejected_qids':['Q20']}]:
            d=self.decision();d.update(change);self.ledger['decisions']=[d]
            with self.assertRaises(ValueError):repair.resolve(self.occ,self.ledger)

    def test_same_qid_cannot_hide_two_local_people(self):
        self.ledger['people'][1]['preferred_qid']='Q20'
        with self.assertRaisesRegex(ValueError,'multiple local'):repair.resolve(self.occ,self.ledger)

    def test_rejection_supersedes_old_acceptance_in_either_order(self):
        old=self.decision()
        rejection=dict(self.decision(pid=None,status='rejected'),id='rejection',supersedes=[old['id']])
        for ds in ([old,rejection],[rejection,old]):
            self.ledger['decisions']=ds
            self.assertIsNone(repair.resolve(self.occ,self.ledger)[0]['effective_qid'])
            self.assertEqual(len(self.ledger['decisions']),2)

    def test_cyclic_and_cross_occurrence_supersession_fail(self):
        old=self.decision();new=dict(self.decision(),id='new',supersedes=[old['id']])
        old['supersedes']=['new'];self.ledger['decisions']=[old,new]
        with self.assertRaisesRegex(ValueError,'Cyclic'):repair.resolve(self.occ,self.ledger)
        old.pop('supersedes');new['occurrence_id']='b'
        with self.assertRaisesRegex(ValueError,'crosses'):repair.resolve(self.occ,self.ledger)


class BuildTests(unittest.TestCase):
    def fixture(self,root):
        frozen=root/'generated/frozen';frozen.mkdir(parents=True)
        (frozen/'record.json').write_text('{"source":"fixture"}')
        (frozen/'record.html').write_text('fixture header')
        row={'source':'hnet','era':'classic','review_id':'1','reviewer':'Reviewer',
             'reviewer_qid':None,'reviewer_wd_status':'unmatched','book_author':'A One, B Two, C Three',
             'book_title':'A Book','author_qids':'Q1|Q3','n_authors':3,'n_authors_grounded':2,
             'body_text':'Source review text must remain unchanged.'}
        with duckdb.connect(str(frozen/'catalog.duckdb')) as c:
            c.execute('CREATE TABLE reviews(source VARCHAR,era VARCHAR,review_id VARCHAR,reviewer VARCHAR,reviewer_qid VARCHAR,reviewer_wd_status VARCHAR,book_author VARCHAR,book_title VARCHAR,author_qids VARCHAR,n_authors BIGINT,n_authors_grounded BIGINT,body_text VARCHAR)')
            c.execute('INSERT INTO reviews VALUES('+','.join('?' for _ in row)+')',list(row.values()))
        repair.write_json(frozen/'catalog-selection.json',[row])
        manifest={'catalog_rows':1,'catalog_sha256':repair.sha(frozen/'catalog.duckdb'),
                  'files':[{'path':p.name,'sha256':repair.sha(p)} for p in frozen.iterdir()]}
        repair.write_json(root/'baseline-manifest.json',manifest)
        occ=[]
        for i,(name,qid) in enumerate([('A One','Q1'),('B Two',None),('C Three','Q3')],1):
            o={'occurrence_id':str(i),'source':'hnet','era':'classic','review_id':'1','name':name,
               'role':'contributor_unspecified','item_id':'item','item_title':'A Book','position':i,
               'legacy_qid':qid,'pilot':i==2,'json_path':'record.json','raw_path':'record.html',
               'source_json_sha256':repair.sha(frozen/'record.json'),
               'source_raw_file_sha256':repair.sha(frozen/'record.html'),'source_raw_sha256':repair.sha(frozen/'record.html')}
            o['occurrence_fingerprint']=repair.digest(o);occ.append(o)
        repair.write_json(root/'occurrences.json',occ)
        ledger={'baseline_manifest_sha256':repair.sha(root/'baseline-manifest.json'),
                'people':[{'id':'b','label':'B Two','preferred_qid':'Q2'}],
                'evidence':[{'id':'fixture','note':'An exact book-credit match'}],
                'decisions':[{'id':'d2','occurrence_id':'2','occurrence_fingerprint':occ[1]['occurrence_fingerprint'],
                              'legacy_qid':None,'status':'accepted','person_id':'b','evidence':['fixture'],'rationale':'Exact book evidence.'}]}
        repair.write_json(root/'decisions.json',ledger)
        return frozen

    def test_middle_author_slot_and_two_full_builds(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);frozen=self.fixture(root)
            repair.build(root,root/'out1');repair.build(root,root/'out2')
            with duckdb.connect(str(root/'out1/catalog.duckdb'),read_only=True) as c:
                self.assertEqual(c.execute('SELECT author_qids,n_authors_grounded FROM reviews').fetchone(),('Q1|Q2|Q3',3))
                self.assertEqual(c.execute('SELECT effective_qid FROM person_occurrences ORDER BY position').fetchall(),[('Q1',),('Q2',),('Q3',)])
            a=json.loads((root/'out1/report.json').read_text());b=json.loads((root/'out2/report.json').read_text())
            self.assertEqual(a['assignment_digest'],b['assignment_digest'])
            self.assertEqual(repair.sha(frozen/'catalog.duckdb'),a['baseline_catalog_sha256'])

    def test_changed_source_rejected_before_output_created(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);frozen=self.fixture(root)
            (frozen/'record.html').write_text('Different author header')
            with self.assertRaisesRegex(ValueError,'Stale frozen'):repair.build(root,root/'out')
            self.assertFalse((root/'out').exists())


if __name__=='__main__':unittest.main()
