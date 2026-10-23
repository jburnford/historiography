#!/usr/bin/env python3
"""Network view of the dissertation citation graph: extraction and force-directed layout.

User (2026-10-23): "a classic network visualization on a third page showing the full graph".
The full graph (some 2 million nodes) cannot be drawn, so the drawn graph is its backbone:

- every strict History PhD (``in_analysis``) that cites at least one drawn work;
- every work cited by ``--min-cited`` (15) or more strict PhDs, plus works cited by
  ``--min-regional`` (8) or more PhDs within France, the rest of Europe or the rest of the world,
  so the smaller regions' own canons are drawn too;
- every CITES edge between them.

``extract`` reads ``graph.json`` once (about 11 GB of memory: run it alone) and writes
``summary/network/subgraph.json``. ``layout`` runs a ForceAtlas2-style layout (linear
attraction, degree-scaled repulsion, weak strong-gravity; exact repulsion compiled with Numba, no
graph library). Tuned 2026-10-23 by eye: gravity 0.03 separates the regional clusters, gravity 1
squeezes the graph into a uniform disc, and LinLog mixes the regions more and writes ``summary/network/layout.json`` for
``render_network_page.py``.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dissertation_scope import summary_dir  # noqa: E402
from region_top_citations import EUROPE  # noqa: E402


def region(country):
    if country in ('CA', 'US', 'FR'):
        return country
    return 'EU' if country in EUROPE else 'OTHER'


def extract(out, min_cited, min_regional):
    g = json.load((out / 'graph.json').open())
    theses = {}
    for n in g['nodes']:
        if n['type'] == 'Dissertation' and n.get('in_analysis'):
            theses[n['id']] = dict(id=n['id'], title=(n.get('title') or '')[:160], author=(n.get('authors') or [''])[0],
                                   institution=n.get('institution'), year=n.get('year'), country=n.get('country'),
                                   region=region(n.get('country')), notes=n.get('extraction_status') == 'parsed_notes')
    cites = defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in theses:
            cites[e['target']].add(e['source'])
    first_author = {}
    for e in g['edges']:
        if e['type'] == 'AUTHORED' and e['target'] in cites and e['target'] not in first_author:
            first_author[e['target']] = e['source']
    names = {n['id']: n.get('name') for n in g['nodes'] if n['type'] == 'Person'}
    works_meta = {n['id']: n for n in g['nodes'] if n['type'] == 'Work' and n['id'] in cites}
    del g
    keep = {}
    for w, ds in cites.items():
        by = Counter(theses[d]['region'] for d in ds)
        if len(ds) >= min_cited or any(by[r] >= min_regional for r in ('FR', 'EU', 'OTHER')):
            n = works_meta[w]
            keep[w] = dict(id=w, title=(n.get('title') or '')[:160], year=n.get('year'),
                           author=names.get(first_author.get(w)) or '', cited=len(ds), by_region=dict(by))
    edges = [(d, w) for w in keep for d in cites[w]]
    used = {d for d, _ in edges}
    data = dict(theses=[theses[d] for d in theses if d in used], works=list(keep.values()), edges=edges,
                params=dict(min_cited=min_cited, min_regional=min_regional),
                strict_total=len(theses), strict_drawn=len(used))
    dest = summary_dir(out) / 'network'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'subgraph.json').write_text(json.dumps(data, ensure_ascii=False))
    print(f'theses {len(used)} of {len(theses)} strict; works {len(keep)}; edges {len(edges)}')


def _kernel():
    """Numba-compiled force pass (exact all-pairs repulsion, parallel over nodes)."""
    from numba import njit, prange

    @njit(parallel=True, fastmath=True, cache=True)
    def repulse(pos, deg, scaling, out):
        n = pos.shape[0]
        for i in prange(n):
            fx = 0.0
            fy = 0.0
            xi, yi, di = pos[i, 0], pos[i, 1], deg[i]
            for j in range(n):
                dx = xi - pos[j, 0]
                dy = yi - pos[j, 1]
                d2 = dx * dx + dy * dy + 1e-2
                f = scaling * di * deg[j] / d2
                fx += dx * f
                fy += dy * f
            out[i, 0] = fx
            out[i, 1] = fy
    return repulse


def forceatlas2(n, src, dst, iters=500, scaling=1.0, gravity=1.0, linlog=False, seed=7):
    """ForceAtlas2-style layout: attraction along edges (linear, or log(1+d) in LinLog mode),
    repulsion k (deg_i+1)(deg_j+1)/d between all pairs (exact; Numba, parallel) and strong
    gravity k_g (deg+1) d towards the centre. Each step moves a node at most a fraction of the
    current spread, cooling from 10% to 0.2%."""
    repulse = _kernel()
    rng = np.random.default_rng(seed)
    pos = rng.normal(size=(n, 2))
    deg = np.bincount(np.concatenate([src, dst]), minlength=n).astype(float) + 1.0
    t0 = time.time()
    force = np.zeros((n, 2))
    for it in range(iters):
        repulse(pos, deg, scaling, force)
        d = pos[dst] - pos[src]
        if linlog:
            dist = np.sqrt((d ** 2).sum(-1)) + 1e-9
            d = (np.log1p(dist) / dist)[:, None] * d
        np.add.at(force, src, d)
        np.add.at(force, dst, -d)
        force -= gravity * deg[:, None] * pos
        spread = np.sqrt((pos ** 2).sum(-1)).mean()
        frac = 0.1 * (0.02 ** (it / max(1, iters - 1)))
        mag = np.sqrt((force ** 2).sum(-1)) + 1e-12
        pos += force / mag[:, None] * np.minimum(mag, frac * spread)[:, None]
        if it % 100 == 0:
            print(f'  iteration {it}/{iters} ({time.time() - t0:.0f} s)', flush=True)
    return pos


def layout(out, iters, scaling=1.0, gravity=1.0, linlog=False):
    dest = summary_dir(out) / 'network'
    data = json.load((dest / 'subgraph.json').open())
    ids = [t['id'] for t in data['theses']] + [w['id'] for w in data['works']]
    index = {k: i for i, k in enumerate(ids)}
    src = np.array([index[d] for d, _ in data['edges']])
    dst = np.array([index[w] for _, w in data['edges']])
    pos = forceatlas2(len(ids), src, dst, iters=iters, scaling=scaling, gravity=gravity, linlog=linlog)
    pos -= pos.mean(0)
    pos /= np.abs(pos).max()
    (dest / 'layout.json').write_text(json.dumps(dict(ids=ids, xy=[[round(float(x), 4), round(float(y), 4)] for x, y in pos])))
    print(f'layout of {len(ids)} nodes, {len(src)} edges written')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('step', choices=['extract', 'layout'])
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--min-cited', type=int, default=15)
    p.add_argument('--min-regional', type=int, default=8)
    p.add_argument('--iters', type=int, default=700)
    p.add_argument('--scaling', type=float, default=1.0, help='repulsion strength (with linear attraction it only rescales)')
    p.add_argument('--gravity', type=float, default=0.03,
                   help='strong-gravity strength relative to attraction; at 1 the graph is squeezed into a disc')
    p.add_argument('--linlog', action='store_true', help='log(1+d) attraction (tighter clusters)')
    args = p.parse_args()
    if args.step == 'extract':
        extract(args.out, args.min_cited, args.min_regional)
    else:
        layout(args.out, args.iters, args.scaling, args.gravity, args.linlog)


if __name__ == '__main__':
    main()
