#!/usr/bin/env python3
"""Top cited works and people by region: Europe beside Canada and the United States.

User question (2026-10-22): "show me the top citations in Europe to compare with the USA and
Canada". Counts come from the graph's CITES edges for strict History PhDs (``in_analysis``):
a work's share in a region is the percentage of that region's PhDs citing it (presence, one
count per thesis). A person's share is the percentage citing any work of theirs (first author).

Regions (user, 2026-10-30: "make France its own and then Europe (other) for the rest"): CA, US,
GB (a sub-graph since the Oxford expansion), FR, and EUO, the other European countries. Until
then Europe was pooled, with a Europe-without-France series.

Output: ``summary/regions/top-works.csv``, ``top-people.csv`` and ``distinctive.csv`` (for each
work, its share in each region and how far its highest region leads the next), and a printed
summary.
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dissertation_scope import summary_dir  # noqa: E402

EUROPE = {'FR', 'DE', 'IT', 'ES', 'PT', 'BE', 'NL', 'LU', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IS', 'GB', 'IE', 'GR', 'CY', 'MT',
          'PL', 'CZ', 'SK', 'HU', 'SI', 'HR', 'RS', 'BA', 'ME', 'MK', 'AL', 'RO', 'BG', 'EE', 'LV', 'LT', 'UA', 'BY', 'MD'}


REGIONS = ['CA', 'US', 'GB', 'FR', 'EUO']
REGION_NAMES = {'CA': 'Canada', 'US': 'United States', 'GB': 'Britain', 'FR': 'France', 'EUO': 'Rest of Europe'}


def regions_of(country):
    if country in ('CA', 'US', 'GB', 'FR'):
        return [country]
    return ['EUO'] if country in EUROPE else []


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--top', type=int, default=40)
    args = p.parse_args()
    g = json.load((args.out / 'graph.json').open())
    region = {}
    n = defaultdict(int)
    for node in g['nodes']:
        if node['type'] == 'Dissertation' and node.get('in_analysis'):
            rs = regions_of(node.get('country'))
            if rs:
                region[node['id']] = rs
                for r in rs:
                    n[r] += 1
    works = {node['id']: node for node in g['nodes'] if node['type'] == 'Work'}
    persons = {node['id']: node for node in g['nodes'] if node['type'] == 'Person'}
    first_author = {}
    for e in g['edges']:
        if e['type'] == 'AUTHORED' and e['target'] not in first_author:
            first_author[e['target']] = e['source']  # the builder writes the first author first
    wcite = defaultdict(lambda: defaultdict(set))
    pcite = defaultdict(lambda: defaultdict(set))
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in region:
            for r in region[e['source']]:
                wcite[e['target']][r].add(e['source'])
                if e['target'] in first_author:
                    pcite[first_author[e['target']]][r].add(e['source'])
    del g
    regs = REGIONS
    share = lambda d, r: round(100 * len(d.get(r, ())) / n[r], 1) if n[r] else 0  # noqa: E731
    dest = summary_dir(args.out) / 'regions'
    dest.mkdir(parents=True, exist_ok=True)

    def write(name, table, label):
        rows = []
        for r in regs:
            top = sorted(table, key=lambda k: -len(table[k].get(r, ())))[:args.top]
            for rank, k in enumerate(top, 1):
                rows.append(dict(region=r, rank=rank, id=k, label=label(k), **{f'share_{x}': share(table[k], x) for x in regs}))
        with (dest / name).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        return rows

    wl = lambda k: f"{works[k].get('title', '')[:70]} ({works[k].get('year') or ''})"  # noqa: E731
    pl = lambda k: (persons.get(k) or {}).get('name') or k  # noqa: E731
    write('top-works.csv', wcite, wl)
    write('top-people.csv', pcite, pl)
    dist = []
    for k, d in wcite.items():
        s = {r: share(d, r) for r in regs}
        if max(s.values()) >= 2:
            lead, second = sorted(regs, key=lambda r: -s[r])[:2]
            dist.append(dict(id=k, label=wl(k), **{f'share_{r}': s[r] for r in regs}, lead=lead,
                             lead_margin=round(s[lead] - s[second], 1)))
    dist.sort(key=lambda r: -r['lead_margin'])
    with (dest / 'distinctive.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(dist[0]))
        w.writeheader()
        w.writerows(dist)
    print('strict PhDs:', dict(n))
    head = ' | '.join(regs)
    for title, table, label in (('PEOPLE', pcite, pl), ('WORKS', wcite, wl)):
        for reg in regs:
            print(f'\n== {title}: top 10 in {REGION_NAMES[reg]} (share of PhDs citing, %: {head})')
            for k in sorted(table, key=lambda k: -len(table[k].get(reg, ())))[:10]:
                print(f"  {label(k)[:60]:60} " + ' '.join(f'{share(table[k], r):5}' for r in regs))

if __name__ == '__main__':
    main()
