import gzip
import csv
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import duckdb

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_history_journals_crossref import build as build_baseline
from build_history_orcid_index import build,valid_orcid,normalize_orcid
from audit_history_orcid_index import audit
from harvest_ahr_crossref import FIELDS,sha,write_json

class OrcidIndexTest(unittest.TestCase):
    def test_identifier_syntax_and_checksum(self):
        self.assertEqual(normalize_orcid('HTTPS://ORCID.ORG/0000-0002-1825-0097 '),'0000-0002-1825-0097')
        self.assertTrue(valid_orcid('0000-0002-1825-0097'))
        self.assertFalse(valid_orcid('0000-0002-1825-0098'))
        self.assertFalse(valid_orcid('Jane Example'))

    def test_changed_identifier_and_duplicate_batches_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'baseline';base.mkdir();fan=root/'fanout';fan.mkdir()
            original={'DOI':'10.example/one','title':['Original title'],'ISSN':['1234-5678'],
                'type':'journal-article','published':{'date-parts':[[2021]]},'page':'10-21',
                'author':[{'given':'Jane','family':'Example','ORCID':'https://orcid.org/0000-0002-1825-0097','authenticated-orcid':False}]}
            changed={**original,'title':['Revised title'],'author':[{'given':'Jane','family':'Example','ORCID':'https://orcid.org/0000-0001-5109-3700','authenticated-orcid':True}]}
            def source(path,record,filter_spec):
                path.mkdir(parents=True)
                page=path/'page.json.gz'
                with gzip.open(page,'wt') as f:json.dump({'retrieved_at':'2026-09-22T00:00:00Z','items':[record]},f)
                write_json(path/'manifest.json',{'status':'complete','filter':filter_spec,'select':FIELDS,'records':1,'pages':[{'path':'page.json.gz','sha256':sha(page),'records':1}]})
            source(base/'raw',original,'issn:1234-5678,until-pub-date:2026-09-21')
            write_json(base/'selection.json',{'cutoff':'2026-09-21','journals':[{'key':'base_journal','label':'Example Journal','catalogue_ids':['journal_test'],'issns':['1234-5678'],'selection_basis':'test','reuse_work':str(base/'raw')}]})
            with redirect_stdout(StringIO()):build_baseline(base,base/'generated/v1')
            batches=[{'key':key,'issns':['1234-5678']} for key in ['batch1','batch2']]
            for b in batches:source(fan/'generated/harvests'/b['key'],changed,'issn:1234-5678,has-orcid:true,until-pub-date:2026-09-22')
            write_json(fan/'selection.json',{'cutoff':'2026-09-22','scope':'test','batches':batches,'journals':[
                {'journal_key':'journal_test','label':'Example Journal','issns':['1234-5678'],'identity_status':'checked','publication_role':'research_journal'},
                {'journal_key':'title_context','label':'Earlier title context','issns':['1234-5678'],'identity_status':'checked','publication_role':'research_journal'}]})
            with redirect_stdout(StringIO()):build(fan,base,fan/'generated/v1')
            r=json.loads((fan/'report.json').read_text())['metrics']
            self.assertEqual(r['distinct_orcid_ids'],2)
            self.assertEqual(r['baseline_orcid_ids'],1)
            self.assertEqual(r['additional_orcid_ids'],1)
            self.assertEqual(r['unique_contributor_credit_ids'],1)
            self.assertEqual(r['credit_evidence_versions'],2)
            self.assertEqual(r['records_with_differing_metadata_versions'],1)
            self.assertEqual(r['venue_contexts_with_orcids'],2)
            with duckdb.connect(str(fan/'generated/v1/orcid-index.duckdb'),read_only=True) as c:
                self.assertEqual(c.execute('SELECT title_text FROM records').fetchone()[0],'Original title')
                self.assertEqual(c.execute('SELECT count(*) FROM record_sources').fetchone()[0],3)
                self.assertEqual(c.execute('SELECT DISTINCT identity_status FROM orcid_evidence').fetchone()[0],'unreviewed')
            before=sha(fan/'generated/v1/orcid-index.duckdb')
            with redirect_stdout(StringIO()):audit(fan)
            with (fan/'orcid-identifiers-for-review.csv').open() as f:review=list(csv.DictReader(f))
            self.assertEqual([r['orcid_id'] for r in review],['0000-0001-5109-3700'])
            self.assertEqual(sha(fan/'generated/v1/orcid-index.duckdb'),before)

if __name__=='__main__':unittest.main()
