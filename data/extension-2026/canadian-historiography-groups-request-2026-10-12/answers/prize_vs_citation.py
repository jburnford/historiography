#!/usr/bin/env python3
"""Prizes against citations: where prize-winning books rank among books of the same age by History PhD
uptake (2009-2026), the most-cited Canadian historians' books that won no CHA prize, the prize
timeline, and the political-history winners. Reads cha-prize-works.csv (cha_prizes.py) and the graph.
Writes prize-vs-citation.json. Run from the repository root."""
import csv, json, re
from collections import defaultdict
from pathlib import Path
import statistics
ROOT = Path(__file__).resolve().parents[4]; HERE = Path(__file__).resolve().parent
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
g = json.loads((OUT / 'graph.json').read_text()); nodes = {n['id']: n for n in g['nodes']}
diss = {k for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis') and n['year'] and 2009 <= n['year'] <= 2026}
citing = defaultdict(set)
for e in g['edges']:
    if e['type'] == 'CITES' and e['source'] in diss: citing[e['target']].add(e['source'])
rows = list(csv.DictReader((HERE / 'cha-prize-works.csv').open()))
books = [r for r in rows if re.search(r'Best Scholarly Book|Garneau|Book Prize|meilleur livre|Clio', r['prize']) and int(r['matched_works'] or 0)]
# Percentile of each winning book among cited books published within two years of it.
by_year = defaultdict(list)
for w, n in nodes.items():
    if n['type'] == 'Work' and n.get('kind') in ('book', 'book_or_serial', 'unstyled') and n.get('year') and citing.get(w):
        by_year[n['year']].append(len(citing[w]))
out_books = []
for r in books:
    up = int(r['phds_2009_2026']); m = re.search(r'(1[89]\d\d|20[0-2]\d)', r['title'] or '')
    pub = int(r['year']) - 1  # prizes go to the previous year's books
    pool = [x for y in range(pub - 2, pub + 3) for x in by_year.get(y, [])]
    pct = round(sum(1 for x in pool if x < up) / len(pool), 3) if pool else None
    out_books.append(dict(prize=r['prize'], prize_year=int(r['year']), winner=r['winner'], title=r['title'], phds=up, percentile_among_same_age_books=pct, pool=len(pool)))
mature = [b for b in out_books if b['prize_year'] <= 2014 and b['percentile_among_same_age_books'] is not None]
# Most-cited books by the packet's Canadian historians that never won a CHA prize (any prize).
prize_titles = {re.sub(r'[^a-z]', '', (r['title'] or '').lower())[:30] for r in rows if r['title']}
cands = [r for r in csv.DictReader((ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12/candidates.csv').open()) if r['person_type'] == 'canadian_historian']
unawarded = []
for c in cands:
    for part in c['top_works'].split(' | ')[:2]:
        m = re.match(r'(.+) \((\d{4}|n\.d\.); (\d+)\)$', part)
        if m and re.sub(r'[^a-z]', '', m.group(1).lower())[:30] not in prize_titles:
            unawarded.append(dict(author=c['name'], title=m.group(1), year=m.group(2), phds=int(m.group(3))))
unawarded.sort(key=lambda x: -x['phds'])
timeline = json.loads((HERE / 'cha-prizes.json').read_text())['timeline']
political = [dict(prize=r['prize'], year=r['year'], winner=r['winner'], title=r['title'][:120], phds=r['phds_2009_2026']) for r in rows if 'Political History' in r['prize']]
res = dict(books_matched=len(out_books), mature_books=len(mature),
           mature_median_percentile=statistics.median(b['percentile_among_same_age_books'] for b in mature) if mature else None,
           mature_share_top_decile=round(sum(b['percentile_among_same_age_books'] >= 0.9 for b in mature) / len(mature), 3) if mature else None,
           books=sorted(out_books, key=lambda b: b['prize_year']), unawarded_most_cited=unawarded[:40], timeline=timeline, political_history_winners=political,
           caveats=['Prizes go to the previous year\'s books; percentiles compare books published within two years.',
                    'Clio Prizes are listed only in part on the CHA site; first-listed years may postdate a prize\'s first award.',
                    'Unawarded means no CHA prize on the site; other prizes (Governor General, provincial, US) are not checked.'])
(HERE / 'prize-vs-citation.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in res.items() if k in ('books_matched', 'mature_books', 'mature_median_percentile', 'mature_share_top_decile')}))
