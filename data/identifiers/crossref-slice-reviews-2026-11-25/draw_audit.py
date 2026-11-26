"""Draw the stratified audit sample of proposed links (2026-11-25): stratum (relation / marked / bare) x book (DOI-keyed:
a doi anchor and no LCCN, keyed or not; catalogue: an LCCN) x review date (before 2015 / 2020 on), up to N per cell,
seed 20261125, plus 20 bare matches without the author's name in the title (the riskiest part). Writes audit-sample.csv (verdicts are filled in by hand in audit.csv).

    python3 draw_audit.py [N]
"""
import csv
import gzip
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
rows = list(csv.DictReader(gzip.open(HERE / 'matches.csv.gz', 'rt', encoding='utf-8')))
cells = defaultdict(list)
for r in rows:
    y = int(r['review_year'])
    period = 'pre2015' if y < 2015 else ('2020plus' if y >= 2020 else None)
    book = 'doi-book' if r['book_category'].endswith('-doi') else ('catalogue' if 'lccn' in r['book_category'] else 'other')
    if period and book != 'other':
        cells[r['stratum'], book, period].append(r)
extra = [r for r in rows if r['stratum'] == 'bare' and r['fam_in_title'] == 'False']   # the riskiest bare part
rng = random.Random(20261125)
out = []
for cell in sorted(cells):
    pool = cells[cell]
    for r in rng.sample(pool, min(N, len(pool))):
        out.append(dict(cell='/'.join(cell), cell_size=len(pool), **r))
for r in rng.sample(extra, min(20, len(extra))):
    out.append(dict(cell='extra:bare-no-author-in-title', cell_size=len(extra), **r))
cols = ['cell', 'cell_size', 'doi', 'book', 'book_category', 'book_label', 'book_year', 'review_title', 'review_subtitle',
        'journal', 'review_year', 'page', 'reviewers', 'stratum', 'eq', 'fam_in_title']
with open(HERE / 'audit-sample.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, cols, extrasaction='ignore')
    w.writeheader()
    w.writerows(out)
print(len(out), {'/'.join(k): len(v) for k, v in sorted(cells.items())})
