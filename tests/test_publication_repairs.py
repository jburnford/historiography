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

    def test_issue_sequence_lengths_fill_only_unknown_lengths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'0';(path/'generated/v1').mkdir(parents=True)
            db=duckdb.connect(str(path/'generated/v1/catalog.duckdb'))
            db.execute('CREATE TABLE records(record_id VARCHAR,doi VARCHAR,first_page INT,page_count INT,volume VARCHAR,issue VARCHAR,record_type VARCHAR,is_test_record BOOLEAN)')
            # Issue 1: a (p.1, start only) -> b (p.15) -> c (p.18, deposited 3 pp) -> d (p.40, last: no successor).
            # Issue 2: two items sharing a first page cannot be told apart; e has a deposited length.
            db.execute("""INSERT INTO records VALUES ('a','10.1/a',1,NULL,'7','1','journal-article',false),
                ('b','10.1/b',15,NULL,'7','1','journal-article',false),('c','10.1/c',18,3,'7','1','journal-article',false),
                ('d','10.1/d',40,NULL,'7','1','journal-article',false),('x','10.1/x',5,NULL,'7','2','journal-article',false),
                ('y','10.1/y',5,NULL,'7','2','journal-article',false),('e','10.1/e',30,12,'7','2','journal-article',false)""")
            db.execute('CREATE TABLE memberships(record_id VARCHAR,journal_key VARCHAR)')
            db.execute("INSERT INTO memberships SELECT record_id,'j' FROM records")
            db.execute('CREATE TABLE journals(journal_key VARCHAR,label VARCHAR)')
            db.execute("INSERT INTO journals VALUES ('j','Journal')");db.close()
            for name in ('pages.csv','extra.csv'):
                (root/name).write_text('record_id,first_page,last_page,source_url,source_sha256,status\n')
            db=duckdb.connect()
            with patch.object(inputs,'COLLECTIONS',[path]),patch.object(inputs,'PAGES',root/'pages.csv'),patch.object(inputs,'EXTRA_PAGES',root/'extra.csv'):
                inputs.attach_catalogues(db)
            got={r[0]:(r[1],r[2]) for r in db.execute('SELECT record_id,effective_page_count,length_basis FROM x_effective_records').fetchall()}
            research={r[0] for r in db.execute('SELECT record_id FROM x_research').fetchall()}
            db.close()
        self.assertEqual(got['a'],(14,'issue_sequence_inferred'))
        self.assertEqual(got['b'],(3,'issue_sequence_inferred'))
        self.assertEqual(got['c'],(3,'deposited'))
        self.assertEqual(got['d'],(None,None))
        self.assertEqual(got['x'],(None,None))
        self.assertEqual(got['e'],(12,'deposited'))
        self.assertEqual(research,{'a','e'})

    def test_old_review_decisions_are_unchanged(self):
        repair=ROOT/'data/evidence-layer/repairs/2026-10-10'
        with (repair/'before/data/evidence-layer/practice-crosswalk.csv').open() as f: before=list(csv.DictReader(f))
        with (ROOT/'data/evidence-layer/practice-crosswalk.csv').open() as f: current=list(csv.DictReader(f))
        # The proposed H-Emotions topic gained its own teaching field in1.166.
        # Its exact former row is retained in a declared promotion record; no
        # source population, review status or historical snapshot was changed.
        promotion=json.loads((ROOT/'data/evidence-layer/repairs/2026-10-25/emotions-target-promotion.json').read_text())
        restored=[dict(r) for r in current[:len(before)]]
        matching=[i for i,r in enumerate(restored) if r==promotion['after_row']]
        self.assertEqual(len(matching),1)
        self.assertEqual(promotion['before_row']['status'],promotion['after_row']['status'])
        self.assertEqual(set(promotion['changed_fields']),{'target','target_label','note'})
        restored[matching[0]]=promotion['before_row']
        self.assertEqual(restored,before)
        repair_rows=current[len(before):len(before)+13]
        self.assertTrue(all(r['status']=='reviewed' and r['note'].startswith('2026-10-10') for r in repair_rows))
        # Rows added after the repair (later journal supplements) stay proposals, never silent reviews.
        self.assertTrue(all(r['status']=='proposed' for r in current[len(before)+13:]))

if __name__=='__main__': unittest.main()
