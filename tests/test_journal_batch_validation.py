import unittest
from scripts.check_journal_classification_batches import check_batch


class JournalBatchTests(unittest.TestCase):
    def setUp(self):
        self.catalogue={'nodes':[{'id':'j','entry_kind':'periodical'}], 'sources':[{'id':'sheet'}]}
        self.batch={'batch_id':'sol-001','checked_on':'2026-09-13','classifications':[
            {'journal_id':'j','subject_path':['By region','Korea'],'basis':'title_indicated',
             'status':'provisional','source_ids':['sheet'],'evidence_note':'Title evidence only; publisher remit not checked.'}]}

    def test_provisional_title_classification_is_valid(self):
        self.assertEqual(check_batch(self.batch,self.catalogue),[])

    def test_title_evidence_cannot_be_promoted_to_checked(self):
        self.batch['classifications'][0]['status']='checked'
        self.assertTrue(check_batch(self.batch,self.catalogue))

    def test_unknown_journal_or_source_is_rejected(self):
        self.batch['classifications'][0].update(journal_id='missing',source_ids=['unknown'])
        self.assertEqual(len(check_batch(self.batch,self.catalogue)),2)

    def test_metadata_cannot_smuggle_visual_edge(self):
        self.batch['classifications'][0]['relationship_kind']='publishes'
        self.assertTrue(check_batch(self.batch,self.catalogue))

    def test_opaque_title_can_remain_unresolved(self):
        self.batch['classifications']=[]
        self.batch['unresolved']=[{'journal_id':'j','reason':'Ambiguous title','next_step':'Find an ISSN or publisher.'}]
        self.assertEqual(check_batch(self.batch,self.catalogue),[])
