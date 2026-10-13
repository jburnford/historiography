"""Check that source supplements restore missing lengths without rewriting deposits."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import duckdb

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evidence_inputs as inputs

class PublicationRepairTests(unittest.TestCase):
    def test_aliases_use_catalogue_ids_and_preserve_distinct_contexts(self):
        got=inputs.venue_keys([dict(journal_key='initial:a',catalogue_ids=['catalogue:a','catalogue:a']),
            dict(journal_key='other:a',catalogue_ids=['catalogue:a'])])
        self.assertEqual(got['catalogue:a'],{'initial:a','other:a'})
        self.assertNotIn('a',got)

    def catalogues(self,root):
        paths=[]
        for i in range(3):
            path=root/str(i);(path/'generated/v1').mkdir(parents=True)
            db=duckdb.connect(str(path/'generated/v1/catalog.duckdb'))
            db.execute('CREATE TABLE records(record_id VARCHAR,doi VARCHAR,first_page INT,page_count INT,record_type VARCHAR,is_test_record BOOLEAN)')
            db.execute("INSERT INTO records VALUES ('r','10.1/r',1,NULL,'journal-article',false),('short','10.1/s',1,4,'journal-article',false)")
            db.execute('CREATE TABLE memberships(record_id VARCHAR,journal_key VARCHAR)')
            db.execute("INSERT INTO memberships VALUES ('r','j')")
            db.execute('CREATE TABLE journals(journal_key VARCHAR,label VARCHAR)')
            db.execute("INSERT INTO journals VALUES ('j','Journal')")
            db.close();paths.append(path)
        return paths

    def attach(self,record='r',first=1,last=15,extra=None):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);paths=self.catalogues(root)
            row=dict(record_id=record,first_page=first,last_page=last,source_url='https://publisher.example/issue',source_sha256='a'*64,status='metadata_checked')
            for name,rows in [('pages.csv',[row]),('extra.csv',extra or [])]:
                with (root/name).open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerows(rows)
            db=duckdb.connect()
            try:
                with patch.object(inputs,'COLLECTIONS',paths),patch.object(inputs,'PAGES',root/'pages.csv'),patch.object(inputs,'EXTRA_PAGES',root/'extra.csv'):
                    inputs.attach_catalogues(db)
                return db.execute('SELECT record_id,page_count,effective_page_count FROM x_effective_records ORDER BY record_id').fetchall(),db.execute('SELECT record_id FROM x_research').fetchall()
            finally: db.close()

    def test_fill_deduplicates_records_and_preserves_deposited_values(self):
        rows,research=self.attach()
        self.assertEqual(rows,[('r',None,15),('short',4,4)])
        self.assertEqual(research,[('r',)])

    def test_deposited_range_conflicts_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'conflicts with deposits'): self.attach(record='short')
        with self.assertRaisesRegex(ValueError,'conflicts with deposits'): self.attach(first=2)

    def test_unknown_dois_and_invalid_ranges_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown DOIs'): self.attach(record='unknown')
        with self.assertRaisesRegex(ValueError,'Invalid sourced'): self.attach(last=300)

    def test_conflicting_assertions_are_rejected(self):
        extra=[dict(record_id='r',first_page=1,last_page=30,source_url='https://publisher.example/issue',source_sha256='b'*64,status='metadata_checked')]
        with self.assertRaisesRegex(ValueError,'Conflicting sourced'): self.attach(extra=extra)

    def test_old_review_decisions_are_unchanged(self):
        repair=ROOT/'data/evidence-layer/repairs/2026-10-10'
        with (repair/'before/data/evidence-layer/practice-crosswalk.csv').open() as f: before=list(csv.DictReader(f))
        with (ROOT/'data/evidence-layer/practice-crosswalk.csv').open() as f: current=list(csv.DictReader(f))
        self.assertEqual(current[:len(before)],before)
        repair_rows=current[len(before):len(before)+13]
        self.assertTrue(all(r['status']=='reviewed' and r['note'].startswith('2026-10-10') for r in repair_rows))
        # Rows added after the repair (later journal supplements) stay proposals, never silent reviews.
        self.assertTrue(all(r['status']=='proposed' for r in current[len(before)+13:]))

if __name__=='__main__': unittest.main()
