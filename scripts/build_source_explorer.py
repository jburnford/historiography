#!/usr/bin/env python3
"""Data for the source explorer: one cited work or person, its citations over time and its company.

User (2026-10-23): "the user selects a source and sees the graph of relations and change over
time; so if I select Cronon I get to see how his citations evolve; who is cited with him, how that
changes over time; how different regions cite him".

Reads ``graph.json`` once (about 11 GB of memory: run it alone) and writes
``summary/explorer/explorer.json`` for ``render_source_explorer.py``. For every source (works cited
by at least ``--min-work`` strict History PhDs; people, as first authors, cited by at least
``--min-person``):

- **series**: per period and region (Canada, United States, Europe, elsewhere), the citing theses
  and the share of that region's strict History PhDs in that period;
- **companions**: works (for a work) or people (for a person) cited in the same theses more often
  than chance (association strength c_ab N / (c_a c_b) of at least ``--min-strength``, 1.5),
  ranked by the number of shared theses, at least ``--min-shared`` (3);
- **company over time**: for the companions, the share of the source's citing theses in each period
  that also cite them, with each period's own leading companions added to the rows;
- **company by region**: each region's leading companions;
- **links** among the top companions (shared theses within the source's citing set) and a spring
  layout of them with the source at the centre.

Periods are five years from 1990, with earlier years pooled.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
import time

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dissertation_scope import summary_dir  # noqa: E402
from network_layout import region  # noqa: E402
from render_region_comparison import proper  # noqa: E402

PERIODS = ['before 1990', '1990-94', '1995-99', '2000-04', '2005-09', '2010-14', '2015-19', '2020-25']
REGIONS = ['CA', 'US', 'EUROPE', 'OTHER']


def period(y):
    if not y:
        return None
    if y < 1990:
        return 0
    return min(7, 1 + (y - 1990) // 5)


def reg4(country):
    r = region(country)
    return 'EUROPE' if r in ('FR', 'EU') else r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min-work', type=int, default=20)
    ap.add_argument('--min-person', type=int, default=30)
    ap.add_argument('--min-strength', type=float, default=1.5)
    ap.add_argument('--min-shared', type=int, default=3)
    ap.add_argument('--companions', type=int, default=16, help='companion rows kept per source (plus period newcomers, at most 20)')
    args = ap.parse_args()
    t0 = time.time()
    g = json.load((args.out / 'graph.json').open())
    theses = {}
    for n in g['nodes']:
        if n['type'] == 'Dissertation' and n.get('in_analysis') and period(n.get('year')) is not None:
            theses[n['id']] = (period(n['year']), reg4(n.get('country')))
    first = {}
    for e in g['edges']:
        if e['type'] == 'AUTHORED' and e['target'] not in first:
            first[e['target']] = e['source']
    works_of = defaultdict(set)
    persons_of = defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in theses:
            works_of[e['source']].add(e['target'])
            if e['target'] in first:
                persons_of[e['source']].add(first[e['target']])
    label = {}
    for n in g['nodes']:
        if n['type'] == 'Work':
            label[n['id']] = (n.get('title') or '', n.get('year'))
        elif n['type'] == 'Person':
            label[n['id']] = (proper(n.get('name') or n['id'][2:]), None)
    del g
    print(f'loaded in {time.time() - t0:.0f} s: {len(theses)} strict theses', flush=True)
    tids = sorted(theses)
    tix = {t: i for i, t in enumerate(tids)}
    tper = [theses[t][0] for t in tids]
    treg = [theses[t][1] for t in tids]
    den = Counter((tper[i], treg[i]) for i in range(len(tids)))
    N = len(tids)

    def index(sets):
        inv = defaultdict(list)
        for t, items in sets.items():
            for x in items:
                inv[x].append(tix[t])
        return inv, {tix[t]: list(items) for t, items in sets.items()}
    work_citing, thesis_works = index(works_of)
    person_citing, thesis_persons = index(persons_of)

    def short(x):
        title, year = label.get(x, (x, None))
        if x.startswith('W:'):
            name = proper(label.get(first.get(x), ('', None))[0].split(',')[0]) if first.get(x) else ''
            t = title.split(':')[0].strip()
            return f'{name}, {t}' if name else t
        return title

    def build(src, citing, inv, per_thesis):
        cs = set(citing)
        n = len(cs)
        series = [[0] * len(REGIONS) for _ in PERIODS]
        for i in cs:
            series[tper[i]][REGIONS.index(treg[i])] += 1
        co = Counter()
        for i in cs:
            co.update(x for x in per_thesis.get(i, ()) if x != src)
        cand = []
        for x, c in co.items():
            if c < args.min_shared:
                continue
            s = c * N / (n * len(inv[x]))
            if s >= args.min_strength:
                cand.append((c, s, x))
        cand.sort(reverse=True)
        top = [x for _, _, x in cand[:args.companions]]
        strength = {x: round(s, 2) for c, s, x in cand}
        by_period = defaultdict(Counter)
        for i in cs:
            p = tper[i]
            by_period[p].update(x for x in per_thesis.get(i, ()) if x in strength)
        for p, cnt in by_period.items():  # each period's own leaders join the rows
            for x, _ in cnt.most_common(3):
                if x not in top and cnt[x] >= args.min_shared and len(top) < args.companions + 4:
                    top.append(x)
        n_period = Counter(tper[i] for i in cs)
        grid = [[round(100 * by_period[p][x] / n_period[p]) if n_period[p] else None for p in range(len(PERIODS))] for x in top]
        by_reg = defaultdict(Counter)
        n_reg = Counter(treg[i] for i in cs)
        for i in cs:
            by_reg[treg[i]].update(x for x in per_thesis.get(i, ()) if x in strength)
        regional = {r: [[x, round(100 * c / n_reg[r])] for x, c in by_reg[r].most_common(8)] for r in REGIONS if n_reg[r] >= 10}
        core = top[:12]
        pair = Counter()
        coreset = set(core)
        for i in cs:
            items = [x for x in per_thesis.get(i, ()) if x in coreset]
            for a in range(len(items)):
                for b in range(a + 1, len(items)):
                    pair[tuple(sorted((items[a], items[b])))] += 1
        G = nx.Graph()
        G.add_node(src)
        for x in core:
            G.add_edge(src, x, weight=co[x] / n)
        links = []
        for (a, b), c in sorted(pair.items(), key=lambda kv: -kv[1])[:25]:
            if c >= max(args.min_shared, 0.15 * min(co[a], co[b])):
                G.add_edge(a, b, weight=0.5 * c / n)
                links.append([a, b, c])
        pos = nx.spring_layout(G, weight='weight', seed=7, iterations=300, center=(0, 0)) if len(G) > 1 else {src: (0, 0)}
        sx, sy = pos[src]
        return dict(id=src, n=n, series=series,
                    rows=[[x, co[x], grid[k]] for k, x in enumerate(top)],
                    regional=regional, n_period=[n_period[p] for p in range(len(PERIODS))],
                    n_region={r: n_reg[r] for r in REGIONS},
                    net=dict(nodes=[[x, round(pos[x][0] - sx, 2), round(pos[x][1] - sy, 2)] for x in [src] + core],
                             links=links))

    sources, labels = [], {}
    work_sources = [w for w, c in work_citing.items() if len(c) >= args.min_work]
    person_sources = [p for p, c in person_citing.items() if len(c) >= args.min_person]
    print(f'{len(work_sources)} works, {len(person_sources)} people', flush=True)
    for k, w in enumerate(work_sources):
        sources.append(build(w, work_citing[w], work_citing, thesis_works))
        if k % 300 == 0:
            print(f'  works {k}/{len(work_sources)} ({time.time() - t0:.0f} s)', flush=True)
    for k, p in enumerate(person_sources):
        sources.append(build(p, person_citing[p], person_citing, thesis_persons))
        if k % 300 == 0:
            print(f'  people {k}/{len(person_sources)} ({time.time() - t0:.0f} s)', flush=True)
    for s in sources:
        for x in [s['id']] + [r[0] for r in s['rows']] + [x for r in s['regional'].values() for x, _ in r]:
            if x not in labels:
                title, year = label.get(x, (x, None))
                labels[x] = dict(short=short(x), full=title, year=year,
                                 author=(label.get(first.get(x), ('', None))[0] if x.startswith('W:') and first.get(x) else ''))
    # Integer ids: every work or person appears once in the label table; sources point into it.
    keys = list(labels)
    num = {k: i for i, k in enumerate(keys)}
    for s_ in sources:
        s_['id'] = num[s_['id']]
        s_['rows'] = [[num[x], c, g_] for x, c, g_ in s_['rows']]
        s_['regional'] = {r: [[num[x], v] for x, v in lst] for r, lst in s_['regional'].items()}
        s_['net'] = dict(nodes=[[num[x], a, b] for x, a, b in s_['net']['nodes']],
                         links=[[num[a], num[b], c] for a, b, c in s_['net']['links']])
    table = [dict(key=k, **labels[k]) for k in keys]
    dest = summary_dir(args.out) / 'explorer'
    dest.mkdir(parents=True, exist_ok=True)
    den_out = [[den[(p, r)] for r in REGIONS] for p in range(len(PERIODS))]
    (dest / 'explorer.json').write_text(json.dumps(dict(periods=PERIODS, regions=REGIONS, denominators=den_out, sources=sources,
                                                        labels=table, params=vars(args) | {'out': str(args.out)}),
                                                   ensure_ascii=False, separators=(',', ':')))
    print(f'wrote {dest / "explorer.json"}: {len(sources)} sources, {len(labels)} labels ({time.time() - t0:.0f} s)')


if __name__ == '__main__':
    main()
