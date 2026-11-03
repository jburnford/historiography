"""Sol's verdicts on cited translations and editions -> a crosswalk beside the log (2026-11-03).

groups.json: the 500 most-cited books by keyed authors that no crosswalk matched (ungrounded_works.py,
`book_not_matched`), each with the authors' works in the graph. Sol (BRIEF.md) named the graph work each cited book
is a translation, edition or variant title of (*Futuro Passado* -> *Vergangene Zukunft*), or none. A verdict is
kept when its relation is translation, edition or same and its work is one of the item's candidate works.
Writes crosswalk.csv.gz (work_id, key) for export_citations, and report.json.

    python3 data/identifiers/translation-check-2026-11-03/apply-verdicts.py
"""
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
items = {i['id']: i for g in json.loads((HERE / 'groups.json').read_text()) for i in g['items']}
report, rows = Counter(), []
for f in sorted(HERE.glob('g*/verdicts.json')):
    for v in json.loads(f.read_text()):
        it = items.get(v.get('id'))
        if not it:
            report['unknown_item'] += 1
            continue
        report[f'relation:{v.get("relation")}'] += 1
        ok = {w['work'] for c in it['candidates'] for w in c['works']}
        if v.get('relation') in ('translation', 'edition', 'same') and v.get('work') in ok:
            rows.append((it['id'], v['work']))
            report['kept'] += 1
            report['kept_theses'] += it['cited_by_theses']
        elif v.get('work'):
            report['work_not_a_candidate'] += 1
with gzip.open(HERE / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['work_id', 'key'])
    w.writerows(sorted(rows))
(HERE / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
print(json.dumps(dict(sorted(report.items()))))
