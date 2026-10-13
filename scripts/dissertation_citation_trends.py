#!/usr/bin/env python3
"""Change over time in what Canadian History PhD dissertations cite.

Uses strict History PhDs (eligibility ``history_phd``) with a parsed bibliography and a
year. Every measure is normalised by the number of dissertations in the year: a
person's value is the share of that year's dissertations citing any of their works.
Shares use a centred three-year window with Wilson 95% intervals; windows with fewer
than ``--min-window`` dissertations are flagged as thin (early years are small samples).

Years are repository issued years, which can be deposit rather than convocation years.

Writes ``summary/trends.json`` (for the HTML view) and ``summary/trends-people.csv``.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import statistics

CITABLE = {'book', 'article', 'chapter', 'thesis', 'book_or_serial', 'unstyled'}


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--first-year', type=int, default=1960)
    parser.add_argument('--last-year', type=int, default=2025)
    parser.add_argument('--min-window', type=int, default=30)
    parser.add_argument('--min-citing', type=int, default=20, help='include people cited by at least this many dissertations')
    args = parser.parse_args()
    graph = json.loads((args.out / 'graph.json').read_text())
    nodes = {n['id']: n for n in graph['nodes']}
    diss = {k: n for k, n in nodes.items() if n['type'] == 'Dissertation' and n['in_analysis']
            and n['year'] and args.first_year <= n['year'] <= args.last_year}
    cites, authored = defaultdict(set), defaultdict(set)
    for e in graph['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            cites[e['source']].add(e['target'])
        elif e['type'] == 'AUTHORED':
            authored[e['target']].add(e['source'])
    years = list(range(args.first_year, args.last_year + 1))
    n_year = Counter(d['year'] for d in diss.values())
    window = {y: sum(n_year[x] for x in (y - 1, y, y + 1)) for y in years}

    # Per-year context: bibliography length and age of cited scholarship.
    context = []
    for y in years:
        ds = [k for k, d in diss.items() if abs(d['year'] - y) <= 1]
        sizes = [len(cites[k]) for k in ds]
        ages = [diss[k]['year'] - nodes[w]['year'] for k in ds for w in cites[k]
                if nodes[w].get('year') and 1800 <= nodes[w]['year'] <= diss[k]['year'] and nodes[w]['kind'] in CITABLE]
        context.append(dict(year=y, dissertations=n_year[y], window=window[y], thin=window[y] < args.min_window,
                            median_works_cited=statistics.median(sizes) if sizes else None,
                            median_age_cited=statistics.median(ages) if ages else None))

    # Per-person yearly counts of citing dissertations.
    by_person = defaultdict(Counter)
    for k, ws in cites.items():
        for p in set().union(*(authored[w] for w in ws)) if ws else ():
            by_person[p][diss[k]['year']] += 1
    ranked = sorted((p for p in by_person if nodes[p]['name_key_kind'] != 'corporate_or_single_name'
                     and sum(by_person[p].values()) >= args.min_citing), key=lambda p: -sum(by_person[p].values()))

    def share(c, y0, y1):
        k = sum(c[y] for y in range(y0, y1 + 1))
        n = sum(n_year[y] for y in range(y0, y1 + 1))
        return k / n if n else 0

    works_of = defaultdict(set)
    for w, ps in authored.items():
        for p in ps:
            works_of[p].add(w)
    people = []
    for p in ranked:
        c = by_person[p]
        series = []
        for y in years:
            k = sum(c[x] for x in (y - 1, y, y + 1))
            lo, hi = wilson(k, window[y])
            r4 = lambda v: round(v, 4) if v is not None else None
            series.append(dict(year=y, k=k, n=window[y], share=r4(k / window[y]) if window[y] else None, lo=r4(lo), hi=r4(hi),
                               thin=window[y] < args.min_window))
        early, late = share(c, 2000, 2009), share(c, 2018, 2025)
        trend = ('rising' if late >= 1.25 * early and late - early >= 0.02 else
                 'declining' if late <= 0.75 * early and early - late >= 0.02 else 'steady')
        top_works = sorted(((nodes[w]['cited_by'], nodes[w]['title']) for w in works_of[p]), reverse=True)[:3]
        people.append(dict(id=p, name=nodes[p]['name'], qid=nodes[p].get('qid'), total=sum(c.values()),
                           share_2000s=round(early, 4), share_2018_25=round(late, 4), trend=trend,
                           top_works=[t for _, t in top_works], series=series))
    out = args.out / 'summary'
    (out / 'trends.json').write_text(json.dumps(dict(
        generated_from='graph.json', unit='share of strict History PhD dissertations citing the person (centred 3-year window)',
        min_window=args.min_window, min_citing=args.min_citing, years=years, context=context, people=people), ensure_ascii=False) + '\n')
    with (out / 'trends-people.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['person', 'qid', 'dissertations_citing', 'share_2000_09', 'share_2018_25', 'trend'] + [str(y) for y in years])
        for p in people:
            w.writerow([p['name'], p['qid'] or '', p['total'], p['share_2000s'], p['share_2018_25'], p['trend']] +
                       [round(s['share'], 4) if s['share'] is not None else '' for s in p['series']])
    print(Counter(p['trend'] for p in people))


if __name__ == '__main__':
    main()
