import gzip
import json
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import duckdb

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_history_journals_crossref import build
from harvest_ahr_crossref import FIELDS, sha, write_json


class CollectionTest(unittest.TestCase):
    def test_parallel_harvest_reports_failure_without_overwriting_other_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)
            journals=[{'key':key,'label':key,'issns':['1234-5678']} for key in ('complete','different_config')]
            write_json(work/'selection.json',{'cutoff':'2026-09-22','journals':journals})
            for journal in journals:
                source=work/'generated/harvests'/journal['key'];source.mkdir(parents=True)
                spec='issn:1234-5678,until-pub-date:2026-09-22'
                if journal['key']=='different_config':spec+='wrong'
                write_json(source/'manifest.json',{'status':'complete','filter':spec,'select':FIELDS,'records':0,'pages':[]})
            before=(work/'generated/harvests/complete/manifest.json').read_bytes()
            script=Path(__file__).resolve().parents[1]/'scripts/harvest_history_journals_crossref.py'
            result=subprocess.run([sys.executable,str(script),'--work',str(work),'--workers','2'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            report=json.loads((work/'harvest-run-status.json').read_text())
            self.assertEqual(report['attempted_groups'],2)
            self.assertEqual([r['journal_key'] for r in report['failed_groups']],['different_config'])
            self.assertEqual((work/'generated/harvests/complete/manifest.json').read_bytes(),before)

    def test_overlap_variants_empty_journal_and_pagination(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);journals=[]
            first={'DOI':'10.example/ONE','title':['A title'],'type':'journal-article','page':'12-23',
                   'published':{'date-parts':[[2000]]},'author':[{'given':'Jane','family':'Example','ORCID':'https://orcid.org/0000-0002-1825-0097','affiliation':[{'name':'Example University'}]}]}
            second={**first,'title':['A revised deposit']}
            unknown={'DOI':'10.example/two','title':['A single page locator'],'type':'journal-article','page':'522'}
            for key,items in [('first',[first,unknown]),('second',[second]),('empty',[])]:
                source=work/key;source.mkdir()
                page=source/'page.json.gz'
                with gzip.open(page,'wt') as f:json.dump({'retrieved_at':'2026-09-21T00:00:00Z','items':items},f)
                write_json(source/'manifest.json',{'status':'complete','filter':'issn:1234-5678,until-pub-date:2026-09-21','select':FIELDS,'records':len(items),'pages':[{'path':'page.json.gz','sha256':sha(page),'records':len(items)}]})
                journals.append({'key':key,'label':key,'issns':['1234-5678'],'catalogue_ids':[],'selection_basis':'test','reuse_work':str(source)})
            write_json(work/'selection.json',{'cutoff':'2026-09-21','journals':journals})
            with redirect_stdout(StringIO()):build(work,work/'result')
            with duckdb.connect(str(work/'result/catalog.duckdb'),read_only=True) as c:
                self.assertEqual(c.execute('SELECT count(*) FROM records').fetchone()[0],2)
                self.assertEqual(c.execute('SELECT count(*) FROM memberships').fetchone()[0],3)
                self.assertEqual(c.execute('SELECT variants FROM metadata_variants').fetchone()[0],2)
                self.assertEqual(c.execute("SELECT title_text FROM records WHERE doi='10.example/one'").fetchone()[0],'A title')
                self.assertEqual(c.execute('SELECT page_count FROM research_candidates_by_length').fetchone()[0],12)
                self.assertIsNone(c.execute("SELECT page_count FROM records WHERE doi='10.example/two'").fetchone()[0])
                self.assertEqual(c.execute('SELECT count(*) FROM journals').fetchone()[0],3)
                self.assertEqual(c.execute('SELECT count(*) FROM contributors').fetchone()[0],1)
            report=json.loads((work/'report.json').read_text())
            self.assertEqual(next(j for j in report['journals'] if j['journal_key']=='empty')['records'],0)
            self.assertEqual(report['metrics']['distinct_orcids'],1)


if __name__=='__main__':unittest.main()
