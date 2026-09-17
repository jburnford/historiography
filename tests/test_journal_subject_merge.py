import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.journal_subject_batches import merge_batches, apply_accepted_batches, merge_source_check


class SubjectMergeTests(unittest.TestCase):
    def setUp(self):
        self.catalogue={'schema_version':'1.0','nodes':[
            {'id':'j1','label':'Korean History','entry_kind':'periodical'},
            {'id':'j2','label':'Opaque','entry_kind':'periodical'}],
            'sources':[{'id':'sheet'}],'subject_classifications':[],
            'edges':[{'id':'preserved-edge'}]}
        self.batch={'batch_id':'sol-test','checked_on':'2026-09-13','sources':[],
            'classifications':[{'journal_id':'j1','subject_path':['By region','Korea'],
                'basis':'title_indicated','status':'provisional','source_ids':['sheet'],
                'evidence_note':'Title evidence only; publisher remit not checked.'}],
            'unresolved':[{'journal_id':'j2','reason':'Opaque title','next_step':'Find publisher scope.'}]}

    def test_preserves_identity_and_edges_without_promoting_title_evidence(self):
        original=copy.deepcopy(self.catalogue)
        merged=merge_batches(self.catalogue,[self.batch],['j1','j2'])
        self.assertEqual(self.catalogue,original)
        self.assertEqual(merged['edges'],original['edges'])
        self.assertEqual([n for n in merged['nodes'] if n['entry_kind']=='periodical'],original['nodes'])
        row=merged['subject_classifications'][0]
        self.assertEqual(row['status'],'provisional')
        self.assertIsNone(row['checked_on'])
        self.assertEqual(row['reviewed_on'],'2026-09-13')
        self.assertEqual({r['outcome'] for r in merged['classification_reviews']},{'provisional','unresolved'})

    def test_rejects_incomplete_or_repeated_queue(self):
        with self.assertRaises(ValueError): merge_batches(self.catalogue,[self.batch],['j1','j2','j3'])
        duplicate=copy.deepcopy(self.batch);duplicate['batch_id']='another'
        with self.assertRaises(ValueError): merge_batches(self.catalogue,[self.batch,duplicate],['j1','j2'])

    def test_rejects_classified_and_unresolved_same_identity(self):
        self.batch['unresolved'].append({'journal_id':'j1','reason':'conflict','next_step':'review'})
        with self.assertRaises(ValueError): merge_batches(self.catalogue,[self.batch],['j1','j2'])

    def test_unaccepted_and_changed_batches_cannot_enter_generated_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);batches=directory/'subject-classification-batches';batches.mkdir()
            path=batches/'sol-001.json';raw=json.dumps(self.batch).encode();path.write_bytes(raw)
            self.assertEqual(apply_accepted_batches(self.catalogue,directory),self.catalogue)
            manifest={'reviewed_journal_ids':['j1','j2'],'batches':[{'filename':'sol-001.json','sha256':hashlib.sha256(raw).hexdigest()}]}
            (directory/'accepted-subject-batches.json').write_text(json.dumps(manifest))
            self.assertEqual(len(apply_accepted_batches(self.catalogue,directory)['classification_reviews']),2)
            path.write_bytes(raw+b' ')
            with self.assertRaises(ValueError): apply_accepted_batches(self.catalogue,directory)

    def source_fixture(self):
        current=merge_batches(self.catalogue,[self.batch],['j1','j2'])
        source=copy.deepcopy(self.batch)
        source.update(batch_id='web-test',reviewed_journal_ids=['j1','j2'],
                      replaces_provisional_ids=[current['subject_classifications'][0]['id']])
        source['classifications'][0].update(status='checked',basis='publisher_scope')
        return current,source

    def test_source_check_archives_guess_and_preserves_other_outcomes(self):
        current,source=self.source_fixture()
        result=merge_source_check(current,source)
        self.assertEqual(result['edges'],current['edges'])
        self.assertEqual(len(result['superseded_subject_classifications']),1)
        self.assertEqual(result['superseded_subject_classifications'][0]['id'],current['subject_classifications'][0]['id'])
        self.assertEqual(result['subject_classifications'][0]['status'],'checked')
        self.assertEqual({r['journal_id']:r['outcome'] for r in result['classification_reviews']},{'j1':'checked','j2':'unresolved'})
        self.assertEqual(len(result['classification_review_history']),1)
        self.assertEqual(len(result['source_check_attempts']),1)
        self.assertEqual(current['subject_classifications'][0]['status'],'provisional')

    def test_source_check_cannot_replace_checked_or_unknown_rows(self):
        current,source=self.source_fixture()
        current['subject_classifications'][0]['status']='checked'
        with self.assertRaises(ValueError): merge_source_check(current,source)
        source['replaces_provisional_ids']=['unknown']
        with self.assertRaises(ValueError): merge_source_check(current,source)

    def test_partial_source_check_does_not_promote_unreviewed_suggestions(self):
        current,source=self.source_fixture();source['replaces_provisional_ids']=[]
        result=merge_source_check(current,source)
        self.assertEqual(next(r for r in result['classification_reviews'] if r['journal_id']=='j1')['outcome'],'mixed')
        self.assertEqual(len(result['subject_classifications']),2)
