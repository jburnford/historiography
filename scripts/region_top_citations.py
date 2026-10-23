#!/usr/bin/env python3
"""Top cited works and people by region: Europe beside Canada and the United States.

User question (2026-10-22): "show me the top citations in Europe to compare with the USA and
Canada". Counts come from the graph's CITES edges for strict History PhDs (``in_analysis``):
a work's share in a region is the percentage of that region's PhDs citing it (presence, one
count per thesis). A person's share is the percentage citing any work of theirs (first author).

Regions: CA, US, EUROPE (European countries in the graph), and EUROPE_EX_FR, because France
is about half of the European PhDs and would otherwise set the European list.

Output: ``summary/regions/top-works.csv``, ``top-people.csv`` and ``distinctive.csv`` (works
much more cited in Europe than in North America and the reverse), and a printed summary.
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


def regions_of(country):
    out = []
    if country in ('CA', 'US'):
        out.append(country)
    if country in EUROPE:
        out.append('EUROPE')
        if country != 'FR':
            out.append('EUROPE_EX_FR')
    return out


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
    regs = ['EUROPE', 'EUROPE_EX_FR', 'CA', 'US']
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
        eu, na = share(d, 'EUROPE'), max(share(d, 'CA'), share(d, 'US'))
        if eu >= 2 or na >= 2:
            dist.append(dict(id=k, label=wl(k), share_EUROPE=eu, share_EUROPE_EX_FR=share(d, 'EUROPE_EX_FR'),
                             share_CA=share(d, 'CA'), share_US=share(d, 'US'), europe_minus_na=round(eu - na, 1)))
    dist.sort(key=lambda r: -r['europe_minus_na'])
    with (dest / 'distinctive.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(dist[0]))
        w.writeheader()
        w.writerows(dist)
    print('strict PhDs:', dict(n))
    for title, table, label in (('PEOPLE', pcite, pl), ('WORKS', wcite, wl)):
        print(f'\n== {title}: top 25 in Europe (share of PhDs citing, %: Europe | Europe ex-France | Canada | US)')
        for k in sorted(table, key=lambda k: -len(table[k].get('EUROPE', ())))[:25]:
            print(f"  {label(k)[:60]:60} {share(table[k], 'EUROPE'):5} {share(table[k], 'EUROPE_EX_FR'):5} {share(table[k], 'CA'):5} {share(table[k], 'US'):5}")
    print('\n== WORKS much more cited in Europe than in Canada or the US')
    for r in dist[:15]:
        print(f"  {r['label'][:60]:60} EU {r['share_EUROPE']:5} exFR {r['share_EUROPE_EX_FR']:5} CA {r['share_CA']:5} US {r['share_US']:5}")
    print('\n== WORKS much more cited in North America than in Europe')
    for r in dist[-15:][::-1]:
        print(f"  {r['label'][:60]:60} EU {r['share_EUROPE']:5} exFR {r['share_EUROPE_EX_FR']:5} CA {r['share_CA']:5} US {r['share_US']:5}")


if __name__ == '__main__':
    main()
