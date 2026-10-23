#!/usr/bin/env python3
"""Co-citation map of the most cited works: the network page.

User (2026-10-23), on the full thesis-and-work network: "that is still too much"; chose a map of
the top works. Reads ``summary/network/subgraph.json`` (``network_layout.py extract``) and the
strict thesis counts in ``dissertations.csv``; writes ``summary/comparisons/network.html``.

- **Nodes**: the ``--per-region`` (90) works cited by the largest share of strict History PhDs in
  each of Canada, the United States and Europe, together (a ranking by raw count let the denser
  North American canon crowd out Europe's); sized by the number of citing theses.
- **Links**: two works are linked by co-citation, the number of theses citing both. Strength is
  the association strength used by VOSviewer, c_ab / (c_a c_b) scaled by the number of theses,
  so that heavily cited works are not linked to everything. Each work keeps its ``--keep`` (5)
  strongest links among pairs co-cited by at least ``--min-co`` (5) theses.
- **Colour**: the region that cites the work most relative to its size (share of the region's
  strict History PhDs citing it): Canada, United States or Europe when that share is at least
  ``--lean`` (1.5) times the next region's; otherwise 'shared'.
- **Layout**: a weighted spring layout (networkx), precomputed; the page is SVG with zoom, pan
  and hover.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import html
from itertools import combinations
import json
import math
from pathlib import Path
import sys

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_layout import region  # noqa: E402
from render_region_comparison import proper  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731
LEANS = {'CA': 'Canada', 'US': 'United States', 'EUROPE': 'Europe', 'SHARED': 'Shared'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--per-region', type=int, default=90, help='works taken from each region by share of its PhDs citing')
    ap.add_argument('--keep', type=int, default=5)
    ap.add_argument('--min-co', type=int, default=5)
    ap.add_argument('--lean', type=float, default=1.5)
    args = ap.parse_args()
    sub = json.load((D / 'summary' / 'network' / 'subgraph.json').open())
    totals = Counter()
    for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8')):
        if r['in_analysis'] == 'True':
            reg = region(r['country'])
            totals['EUROPE' if reg in ('FR', 'EU') else reg] += 1
    # Selection by region, so the denser North American canon does not crowd out Europe's: the
    # --per-region works with the highest share in each of Canada, the US and Europe, together.
    def share(w, reg):
        by = w['by_region']
        n = by.get('FR', 0) + by.get('EU', 0) if reg == 'EUROPE' else by.get(reg, 0)
        return n / totals[reg]
    chosen = {}
    for reg in ('CA', 'US', 'EUROPE'):
        for w in sorted(sub['works'], key=lambda w: -share(w, reg))[:args.per_region]:
            chosen[w['id']] = w
    works = sorted(chosen.values(), key=lambda w: -w['cited'])
    wid = {w['id']: i for i, w in enumerate(works)}
    citing = defaultdict(set)
    for d, w in sub['edges']:
        if w in wid:
            citing[wid[w]].add(d)
    n_theses = len({d for s in citing.values() for d in s})
    by_thesis = defaultdict(list)
    for i, ds in citing.items():
        for d in ds:
            by_thesis[d].append(i)
    co = Counter()
    for ws in by_thesis.values():
        for a, b in combinations(sorted(ws), 2):
            co[(a, b)] += 1
    cnt = {i: len(citing[i]) for i in range(len(works))}
    strength = {k: v * n_theses / (cnt[k[0]] * cnt[k[1]]) for k, v in co.items() if v >= args.min_co}
    best = defaultdict(list)
    for (a, b), s in strength.items():
        best[a].append((s, b))
        best[b].append((s, a))
    edges = set()
    for a, lst in best.items():
        for s, b in sorted(lst, reverse=True)[:args.keep]:
            edges.add((min(a, b), max(a, b)))
    # a work below the co-citation floor keeps its single strongest link (co-cited at least twice),
    # so it is placed among its neighbours instead of flying off; works with none are dropped
    for i in range(len(works)):
        if i not in best:
            cand = [(v * n_theses / (cnt[a] * cnt[b]), (a, b)) for (a, b), v in co.items() if i in (a, b) and v >= 2]
            if cand:
                s_, e = max(cand)
                strength[e] = s_
                edges.add(e)
    linked = {x for e in edges for x in e}
    keep_idx = [i for i in range(len(works)) if i in linked]
    remap = {old: new for new, old in enumerate(keep_idx)}
    works = [works[i] for i in keep_idx]
    edges = {(remap[a], remap[b]) for a, b in edges}
    strength = {(remap[a], remap[b]): v for (a, b), v in strength.items() if a in remap and b in remap}
    co = Counter({(remap[a], remap[b]): v for (a, b), v in co.items() if a in remap and b in remap})
    G = nx.Graph()
    G.add_nodes_from(range(len(works)))
    smax = max(strength[e] for e in edges)
    for a, b in edges:
        G.add_edge(a, b, weight=math.sqrt(strength[(a, b)] / smax))
    # Only the main connected map is drawn: small detached pairs would fly to the corners.
    main_part = max(nx.connected_components(G), key=len)
    detached = [works[i] for i in G.nodes if i not in main_part]
    G = G.subgraph(main_part).copy()
    pos = nx.spring_layout(G, weight='weight', k=1.6 / math.sqrt(len(main_part)), iterations=1500, seed=7)
    # frame on the bulk: centre on the median, scale by the 97th-percentile radius
    xs, ys = sorted(p[0] for p in pos.values()), sorted(p[1] for p in pos.values())
    cx, cy = xs[len(xs) // 2], ys[len(ys) // 2]
    rad = sorted(math.hypot(p[0] - cx, p[1] - cy) for p in pos.values())
    r97 = rad[int(len(rad) * 0.97)] or 1
    pos = {i: ((p[0] - cx) / r97, (p[1] - cy) / r97) for i, p in pos.items()}
    # nodes without links (rare at these settings) are placed by the layout's repulsion alone
    nodes, new_index = [], {}
    for i, w in enumerate(works):
        if i not in main_part:
            continue
        new_index[i] = len(nodes)
        by = w['by_region']
        shares = {'CA': 100 * by.get('CA', 0) / totals['CA'], 'US': 100 * by.get('US', 0) / totals['US'],
                  'EUROPE': 100 * (by.get('FR', 0) + by.get('EU', 0)) / totals['EUROPE']}
        top2 = sorted(shares.items(), key=lambda kv: -kv[1])
        lean = top2[0][0] if top2[0][1] >= args.lean * max(top2[1][1], 1e-9) else 'SHARED'
        name = proper((w['author'].split(',')[0] if w['author'] else '').strip())
        title = w['title'].split(':')[0].strip()
        nodes.append(dict(x=round(float(pos[i][0]), 4), y=round(float(pos[i][1]), 4), cited=w['cited'], lean=lean,
                          label=f"{name}, {title}" if name else title, full=w['title'], year=w['year'], author=proper(w['author']),
                          shares={k: round(v, 1) for k, v in shares.items()}))
    links = [[new_index[a], new_index[b], round(G[a][b]['weight'], 3), co[(min(a, b), max(a, b))]] for a, b in G.edges()]
    lean_counts = Counter(n['lean'] for n in nodes)
    rows = ''.join(f"<tr><td>{esc(n['label'])}</td><td>{n['cited']}</td><td>{LEANS[n['lean']]}</td>"
                   f"<td>{n['shares']['CA']}%</td><td>{n['shares']['US']}%</td><td>{n['shares']['EUROPE']}%</td></tr>"
                   for n in sorted(nodes, key=lambda n: -n['cited']))
    payload = json.dumps(dict(nodes=nodes, links=links, leans=LEANS), ensure_ascii=False, separators=(',', ':'))
    page = (TEMPLATE.replace('__DATA__', payload.replace('</', '<\\/')).replace('__ROWS__', rows)
            .replace('__TOP__', str(len(nodes))).replace('__DETACHED__', ', '.join(esc(w['title'][:40]) for w in detached) or 'none').replace('__LINKS__', f'{len(links):,}').replace('__KEEP__', str(args.keep))
            .replace('__MINCO__', str(args.min_co)).replace('__LEAN__', f'{args.lean:g}').replace('__BUILT__', date.today().isoformat())
            .replace('__NCA__', str(lean_counts['CA'])).replace('__NUS__', str(lean_counts['US']))
            .replace('__NEU__', str(lean_counts['EUROPE'])).replace('__NSH__', str(lean_counts['SHARED'])))
    dest = D / 'summary' / 'comparisons' / 'network.html'
    dest.write_text(page, encoding='utf-8')
    print(f'detached, not drawn: {[w["title"][:40] for w in detached]}')
    print(f'wrote {dest.relative_to(ROOT)}: {len(nodes)} works, {len(links)} links; leans {dict(lean_counts)}')


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A map of the works History PhDs cite</title>
<style>
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--shared:#8f8e88;--edge:#b8b7b0}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--shared:#8a897f;--edge:#4a4944}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;
 --shared:#8a897f;--edge:#4a4944}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:24px max(16px,calc(50vw - 640px))}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 6px}
p.lede,.note{color:var(--text-secondary);max-width:860px}a{color:var(--series-1)}code{font-size:13px}ul.note li{margin:4px 0}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;font-size:13px;color:var(--text-secondary);margin:10px 0 8px}
.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.legend .CA::before{background:var(--series-1)}.legend .US::before{background:var(--series-2)}
.legend .EUROPE::before{background:var(--series-3)}.legend .SHARED::before{background:var(--shared)}
button{font:inherit;font-size:13px;padding:3px 10px;border:1px solid var(--grid);border-radius:6px;background:var(--surface-2);color:var(--text-primary);cursor:pointer}
.stage{border:1px solid var(--grid);border-radius:8px;overflow:hidden;background:var(--surface-1);touch-action:none}
svg.map{width:100%;height:78vh;min-height:520px;display:block;cursor:grab}
svg .link{stroke:var(--edge);stroke-linecap:round}
svg .node circle{stroke:var(--surface-1);stroke-width:1.5}
svg .CA{fill:var(--series-1)}svg .US{fill:var(--series-2)}svg .EUROPE{fill:var(--series-3)}svg .SHARED{fill:var(--shared)}
svg text{fill:var(--text-primary);font-size:11px;paint-order:stroke;stroke:var(--surface-1);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
svg.focus .node{opacity:.15}svg.focus .link{opacity:.06}svg.focus .node.on{opacity:1}svg.focus .link.on{opacity:1;stroke:var(--text-muted)}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:6px 9px;font-size:12.5px;max-width:360px;box-shadow:0 2px 8px rgba(0,0,0,.14);display:none;z-index:5}
#tip b{display:block;margin-bottom:2px}#tip span{color:var(--text-secondary)}
details{margin:8px 0}summary{color:var(--text-secondary);font-size:13px;cursor:pointer}
table{border-collapse:collapse;font-size:13px;margin:8px 0}th,td{padding:3px 10px;text-align:right;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left;max-width:460px}
</style></head><body><main class="viz-root">
<h1>A map of the works History PhDs cite</h1>
<p class="lede">__TOP__ works: the 90 most cited in each of Canada, the United States and Europe (by share of the region's
History PhDs), together. Two works are linked when many theses cite them together, so works
that share readers sit together; each work keeps its __KEEP__ strongest links. Colour shows which region cites the work most
for its size; grey works are cited evenly across Canada, the United States and Europe.</p>
<div class="legend"><span class="CA">Canada (__NCA__)</span><span class="US">United States (__NUS__)</span>
<span class="EUROPE">Europe (__NEU__)</span><span class="SHARED">Shared (__NSH__)</span>
<button id="reset">Reset view</button><span>Size: number of citing theses. Wheel to zoom, drag to pan, hover a work to see its links.</span></div>
<div class="stage"><svg class="map" id="map" role="img" aria-label="Co-citation map of the most cited works"><g id="vp"></g></svg></div>
<div id="tip"></div>
<details><summary>Table: the __TOP__ works, with the share of each region's History PhDs citing them</summary>
<table><thead><tr><th>Work</th><th>Theses</th><th>Leans to</th><th>Canada</th><th>United States</th><th>Europe</th></tr></thead><tbody>__ROWS__</tbody></table></details>
<h2>How to read this</h2><ul class="note">
<li><b>Links</b> join works co-cited by at least __MINCO__ theses, weighted by association strength (co-citations relative to
what the two works' citation counts would give by chance, as in VOSviewer); each work keeps its __KEEP__ strongest, __LINKS__ in
all. Position comes from a spring layout of these links; the axes mean nothing. Works linked only to each other, apart from
the main map, are left out: __DETACHED__.</li>
<li><b>Colour</b>: a work leans to a region when that region's share of History PhDs citing it is at least __LEAN__ times the next
region's. Europe here is all European countries together, France included.</li>
<li><b>Works</b> are first-author surname and main title, with translations mapped through Wikidata counted as one work. A
citation is not engagement.</li></ul>
<p class="note">Built __BUILT__ (<code>scripts/render_cocitation_map.py</code>). See also the <a href="explorer.html">source explorer</a>, <a href="europe-ca-us.html">Europe, Canada and
the United States</a>, <a href="ca-us.html">Canada and the United States</a>, and the <a href="network-full.html">full network of
theses and works</a> (5,600 theses, 11,000 works).</p>
<script id="data" type="application/json">__DATA__</script>
<script>
(()=>{
const DATA=JSON.parse(document.getElementById('data').textContent), svg=document.getElementById('map'), vp=document.getElementById('vp'), tip=document.getElementById('tip');
const NS='http://www.w3.org/2000/svg', S=1000, X=v=>v*S*0.46+S/2, Y=v=>v*S*0.46+S/2;
const r=n=>2.5+Math.sqrt(n.cited)*0.42, nbr=DATA.nodes.map(()=>[]);
const linkEls=DATA.links.map(([a,b,w])=>{const l=document.createElementNS(NS,'line');
 l.setAttribute('class','link');l.setAttribute('x1',X(DATA.nodes[a].x));l.setAttribute('y1',Y(DATA.nodes[a].y));
 l.setAttribute('x2',X(DATA.nodes[b].x));l.setAttribute('y2',Y(DATA.nodes[b].y));l.setAttribute('stroke-width',(0.4+1.6*w).toFixed(2));
 nbr[a].push([b,l]);nbr[b].push([a,l]);vp.appendChild(l);return l;});
const order=DATA.nodes.map((n,i)=>i).sort((a,b)=>DATA.nodes[a].cited-DATA.nodes[b].cited);
const nodeEls=[];
for(const i of order){const n=DATA.nodes[i],g=document.createElementNS(NS,'g');g.setAttribute('class','node');
 const c=document.createElementNS(NS,'circle');c.setAttribute('cx',X(n.x));c.setAttribute('cy',Y(n.y));c.setAttribute('r',r(n).toFixed(1));c.setAttribute('class',n.lean);
 g.appendChild(c);g.dataset.i=i;vp.appendChild(g);nodeEls[i]=g;}
// labels: largest first, skipping collisions; more appear as the view zooms in
const labelLayer=document.createElementNS(NS,'g');vp.appendChild(labelLayer);
let view={x:0,y:0,w:S,h:S};
function setView(){svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`);labels();}
function labels(){labelLayer.textContent='';const k=S/view.w,boxes=[],fs=11/k;
 const byCited=DATA.nodes.map((n,i)=>i).sort((a,b)=>DATA.nodes[b].cited-DATA.nodes[a].cited);
 for(const i of byCited){const n=DATA.nodes[i],x=X(n.x)+r(n)+2/k,y=Y(n.y)+fs*0.35;
  if(x<view.x||x>view.x+view.w||y<view.y||y>view.y+view.h)continue;
  const t=n.label.length>34?n.label.slice(0,32)+'…':n.label,w=t.length*fs*0.55,b=[x,y-fs,w,fs*1.2];
  if(boxes.some(o=>b[0]<o[0]+o[2]&&o[0]<b[0]+b[2]&&b[1]<o[1]+o[3]&&o[1]<b[1]+b[3]))continue;boxes.push(b);
  const e=document.createElementNS(NS,'text');e.setAttribute('x',x);e.setAttribute('y',y);e.setAttribute('font-size',fs.toFixed(2));
  e.setAttribute('stroke-width',(3/k).toFixed(2));e.textContent=t;labelLayer.appendChild(e);}}
function focus(i,e){if(i==null){svg.classList.remove('focus');nodeEls.forEach(g=>g.classList.remove('on'));linkEls.forEach(l=>l.classList.remove('on'));tip.style.display='none';return;}
 svg.classList.add('focus');nodeEls.forEach(g=>g.classList.remove('on'));linkEls.forEach(l=>l.classList.remove('on'));
 nodeEls[i].classList.add('on');for(const [j,l] of nbr[i]){nodeEls[j].classList.add('on');l.classList.add('on');}
 const n=DATA.nodes[i];tip.innerHTML='<b></b><span></span>';tip.querySelector('b').textContent=(n.author?n.author+', ':'')+n.full+(n.year?` (${n.year})`:'');
 tip.querySelector('span').textContent=`Cited by ${n.cited} theses · Canada ${n.shares.CA}% · United States ${n.shares.US}% · Europe ${n.shares.EUROPE}% · ${DATA.leans[n.lean]}`;
 tip.style.display='block';tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(e.clientY+14)+'px';}
vp.addEventListener('pointermove',e=>{const g=e.target.closest('.node');if(g&&!drag)focus(+g.dataset.i,e);});
vp.addEventListener('pointerout',e=>{if(!e.relatedTarget||!e.relatedTarget.closest||!e.relatedTarget.closest('.node'))focus(null);});
let drag=null;
svg.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};svg.setPointerCapture(e.pointerId);svg.style.cursor='grabbing';});
svg.addEventListener('pointermove',e=>{if(!drag)return;const k=view.w/svg.clientWidth;view.x=drag.vx-(e.clientX-drag.x)*k;view.y=drag.vy-(e.clientY-drag.y)*k;setView();});
svg.addEventListener('pointerup',()=>{drag=null;svg.style.cursor='grab';});
svg.addEventListener('wheel',e=>{e.preventDefault();const p=svg.getBoundingClientRect(),mx=view.x+(e.clientX-p.left)*view.w/p.width,my=view.y+(e.clientY-p.top)*view.h/p.height;
 const f=Math.exp(e.deltaY*0.0015);view.x=mx-(mx-view.x)*f;view.y=my-(my-view.y)*f;view.w*=f;view.h*=f;setView();},{passive:false});
function fit(){const p=svg.getBoundingClientRect(),a=p.height/p.width;  // fit the map's extent, with room for labels
 const xs=DATA.nodes.map(n=>X(n.x)),ys=DATA.nodes.map(n=>Y(n.y));let x0=Math.min(...xs)-30,x1=Math.max(...xs)+170,y0=Math.min(...ys)-30,y1=Math.max(...ys)+30;
 let w=x1-x0,h=y1-y0;if(h/w>a){const nw=h/a;x0-=(nw-w)/2;w=nw;}else{const nh=w*a;y0-=(nh-h)/2;h=nh;}view={x:x0,y:y0,w,h};setView();}
document.getElementById('reset').addEventListener('click',fit);new ResizeObserver(fit).observe(svg);
})();
</script></main></body></html>
"""

if __name__ == '__main__':
    main()
