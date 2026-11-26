"""Hand verdicts on audit-sample.csv (read 2026-11-25 from the Crossref metadata in the row) -> audit.csv, with each row's
state in the final matches (kept, or the hold that now applies), and per-cell rates.

    python3 write_audit.py
"""
import csv
import gzip
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRONG = {44: "a review of Pfeiffer's 'Treasures of Taliesin' taken for the 1984 LC node 'Frank Lloyd Wright' (the family "
             "name 'Wright' is the book's title; the node also joins seven LC records). Rule added: a family name counts "
             "only outside the book's title words; unkeyed nodes joining several catalogue records are held"}
UNCLEAR = {}
NOTES = {31: 'page range is the journal review section; the record is the review',
         41: 'collective review; second book matched', 42: 'collective review; third book matched',
         43: "Crossref title misprints 'Enlightenment' as 'Environment'; same book",
         53: 'collective review; second book matched', 73: 'collective review; first book matched',
         80: "link right, but Crossref lists the reviewed author (Hobsbawm) beside the reviewer, and the book node's "
             "family names (from an OpenAlex credit) lack him, so he would be a reviewer-name member",
         28: 'second edition (1963) of Knowles; node is the 1963 edition'}
rows = list(csv.DictReader(open(HERE / 'audit-sample.csv', encoding='utf-8')))
final = {(r['doi'], r['book']) for r in csv.DictReader(gzip.open(HERE / 'matches.csv.gz', 'rt', encoding='utf-8'))}
held = {(r['doi'], r['book']): r['reason'] for r in csv.DictReader(gzip.open(HERE / 'held.csv.gz', 'rt', encoding='utf-8'))}
out, rate = [], Counter()
for i, r in enumerate(rows):
    v = 'wrong' if i in WRONG else ('unclear' if i in UNCLEAR else 'right')
    k = (r['doi'], r['book'])
    now = 'kept' if k in final else ('held: ' + held[k] if k in held else 'gone')
    out.append(dict(n=i, verdict=v, note=WRONG.get(i) or UNCLEAR.get(i) or NOTES.get(i, ''), after_narrowing=now, **r))
    for cell in (r['cell'], 'stratum:' + r['cell'].split('/')[0], 'book:' + (r['cell'].split('/')[1] if '/' in r['cell'] else 'extra'),
                 'period:' + (r['cell'].split('/')[2] if '/' in r['cell'] else 'extra'), 'all'):
        rate[cell, v] += 1
with open(HERE / 'audit.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, list(out[0]))
    w.writeheader()
    w.writerows(out)
for c in sorted({c for c, _ in rate}):
    n = sum(rate[c, v] for v in ('right', 'wrong', 'unclear'))
    print(f'{c:45} {rate[c, "right"]}/{n} right, {rate[c, "wrong"]} wrong, {rate[c, "unclear"]} unclear')
print(Counter(o['after_narrowing'] for o in out))
