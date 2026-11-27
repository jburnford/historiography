#!/usr/bin/env python3
"""Top cited works and people by region: Europe beside Canada and the United States.

User question (2026-10-22): "show me the top citations in Europe to compare with the USA and
Canada". Counts are the build's strict citations (``strict-citations.csv.gz``: one row per strict
History PhD and cited work): a work's share in a region is the percentage of that region's PhDs citing
it (presence, one count per thesis). A person's share is the percentage citing any work of theirs as
first author (the first ``authored.csv.gz`` row of each work; the builder writes the first author first),
distinct theses.

Regions (user, 2026-10-30: "make France its own and then Europe (other) for the rest"): CA, US,
GB (a sub-graph since the Oxford expansion), FR, and EUO, the other European countries. Until
then Europe was pooled, with a Europe-without-France series.

Since 2026-11-21 the tables are streamed from the build's CSV outputs (``dissertations.csv``,
``strict-citations.csv.gz``, ``authored.csv.gz``, ``works.csv``, ``cited-people.csv``) instead of loading the
3 GB ``graph.json`` whole, which no longer fits in memory. Person keys the graph pooled are split back
with ``person-unpool.csv.gz`` and named from ``person-unpool-people.csv.gz`` when present
(dissertation_person_unpool.py), as on the canon maps.

Output: ``summary/regions/top-works.csv``, ``top-people.csv`` and ``distinctive.csv`` (for each
work, its share in each region and how far its highest region leads the next), and a printed
summary.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
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


def rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8', newline='') as f:
        yield from csv.DictReader(f)


def tables(out):
    """(theses per region, work -> Counter of citing theses by region, first author -> region -> thesis numbers,
    person key -> display name)."""
    from dissertation_person_unpool import load_overrides
    moved, people = load_overrides(out)
    region, n = {}, Counter()
    for r in rows(out / 'dissertations.csv'):
        if r['in_analysis'] == 'True' and (rs := regions_of(r['country'])):
            region[r['id']] = (len(region), rs)
            n.update(rs)
    first_author = {}
    for r in rows(out / 'authored.csv.gz'):
        if r['work_id'] not in first_author:
            first_author[r['work_id']] = moved.get((r['work_id'], r['person_key']), r['person_key'])
    wcite = defaultdict(Counter)
    pcite = defaultdict(lambda: defaultdict(set))
    for r in rows(out / 'strict-citations.csv.gz'):
        if (hit := region.get(r['dissertation_id'])):
            i, rs = hit
            p = first_author.get(r['work_id'])
            for reg in rs:
                wcite[r['work_id']][reg] += 1
                if p:
                    pcite[p][reg].add(i)
    pcite = {p: Counter({reg: len(s) for reg, s in d.items()}) for p, d in pcite.items()}
    names = {r['person_key']: r['name'] for r in rows(out / 'cited-people.csv')}
    names.update((k, v['name']) for k, v in people.items())
    return n, wcite, pcite, names


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--top', type=int, default=40)
    args = p.parse_args()
    n, wcite, pcite, names = tables(args.out)
    regs = REGIONS
    share = lambda d, r: round(100 * d.get(r, 0) / n[r], 1) if n[r] else 0  # noqa: E731
    dest = summary_dir(args.out) / 'regions'
    dest.mkdir(parents=True, exist_ok=True)
    # work labels for the works the tables print: title and year from works.csv
    wanted = {k for r in regs for k in sorted(wcite, key=lambda k: -wcite[k].get(r, 0))[:max(args.top, 10)]}
    wanted |= {k for k, d in wcite.items() if max(share(d, r) for r in regs) >= 2}
    titles = {r['work_id']: (r['title'], r['year']) for r in rows(args.out / 'works.csv') if r['work_id'] in wanted}

    def write(name, table, label):
        out = []
        for r in regs:
            top = sorted(table, key=lambda k: (-table[k].get(r, 0), k))[:args.top]
            for rank, k in enumerate(top, 1):
                out.append(dict(region=r, rank=rank, id=k, label=label(k), **{f'share_{x}': share(table[k], x) for x in regs}))
        with (dest / name).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
        return out

    wl = lambda k: f"{titles.get(k, ('', ''))[0][:70]} ({titles.get(k, ('', ''))[1] or ''})"  # noqa: E731
    pl = lambda k: names.get(k[2:] if k.startswith('P:') else k) or k  # noqa: E731
    write('top-works.csv', wcite, wl)
    pcite = {f'P:{k}': v for k, v in pcite.items()}
    write('top-people.csv', pcite, pl)
    dist = []
    for k, d in wcite.items():
        s = {r: share(d, r) for r in regs}
        if max(s.values()) >= 2:
            lead, second = sorted(regs, key=lambda r: -s[r])[:2]
            dist.append(dict(id=k, label=wl(k), **{f'share_{r}': s[r] for r in regs}, lead=lead,
                             lead_margin=round(s[lead] - s[second], 1)))
    dist.sort(key=lambda r: (-r['lead_margin'], r['id']))
    with (dest / 'distinctive.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(dist[0]))
        w.writeheader()
        w.writerows(dist)
    print('strict PhDs:', dict(n))
    head = ' | '.join(regs)
    for title, table, label in (('PEOPLE', pcite, pl), ('WORKS', wcite, wl)):
        for reg in regs:
            print(f'\n== {title}: top 10 in {REGION_NAMES[reg]} (share of PhDs citing, %: {head})')
            for k in sorted(table, key=lambda k: (-table[k].get(reg, 0), k))[:10]:
                print(f"  {label(k)[:60]:60} " + ' '.join(f'{share(table[k], r):5}' for r in regs))


if __name__ == '__main__':
    main()
