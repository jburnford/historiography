import csv
import gzip
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import qwen_labels_io as Q  # noqa: E402

import pandas as pd  # noqa: E402


def frame(n):
    return pd.DataFrame({'item': [f'Q{i}' for i in range(n)], 'position': range(n),
                         'reason': ['plain' if i % 3 else 'two\nlines, "quoted"' for i in range(n)],
                         'facts': ['' if i % 2 else 'x | y' for i in range(n)], 'weight': [1.0] * n})


class TestQwenLabelsIO(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip_and_readers(self):
        D = frame(23)
        single = self.d / 'one.csv.gz'
        D.to_csv(single, index=False, compression='gzip')
        parts = self.d / 'parts'
        m = Q.write_parts(D, parts, rows_per_part=5)
        self.assertEqual([x['rows'] for x in m['parts']], [5, 5, 5, 5, 3])
        self.assertEqual(m['rows'], 23)
        self.assertEqual(m['sha256'], Q.content_sha256(single))
        self.assertTrue(Q.verify(parts)['ok'])
        with gzip.open(single, 'rb') as f, Q.open_binary(parts) as g:
            self.assertEqual(f.read(), g.read())
        for p in Q.part_paths(parts):           # every part is a complete CSV
            self.assertEqual(list(pd.read_csv(p).columns), list(D.columns))
        self.assertTrue(Q.read_frame(parts).equals(pd.read_csv(single)))
        with gzip.open(single, 'rt', newline='', encoding='utf-8') as f:
            self.assertEqual(list(Q.iter_rows(parts)), list(csv.DictReader(f)))
        import duckdb
        n, s = duckdb.connect().execute(f'SELECT count(*), sum(position) FROM {Q.duckdb_source(parts)}').fetchone()
        self.assertEqual((n, s), (23, sum(range(23))))
        out = Q.assemble(parts, self.d / 'build' / 'all.csv.gz')
        self.assertEqual(Q.content_sha256(out), m['sha256'])

    def test_rewrite_removes_stale_parts_and_checks_manifest(self):
        parts = self.d / 'parts'
        Q.write_parts(frame(23), parts, rows_per_part=5)
        m = Q.write_parts(frame(7), parts, rows_per_part=5)
        self.assertEqual(sorted(p.name for p in parts.glob('part-*')), ['part-000.csv.gz', 'part-001.csv.gz'])
        self.assertEqual(len(Q.read_frame(parts)), 7)
        self.assertEqual(m['rows'], 7)
        (parts / 'part-001.csv.gz').unlink()
        with self.assertRaises(RuntimeError):
            Q.read_frame(parts)

    def test_csv_path_source(self):
        src = self.d / 'src.csv'
        frame(4).to_csv(src, index=False)
        m = Q.write_parts(src, self.d / 'p', rows_per_part=100)
        self.assertEqual(len(m['parts']), 1)
        self.assertEqual(Q.content_sha256(self.d / 'p'), m['sha256'])
        with open(src, 'rb') as f, Q.open_binary(self.d / 'p') as g:
            self.assertEqual(f.read(), g.read())


if __name__ == '__main__':
    unittest.main()
