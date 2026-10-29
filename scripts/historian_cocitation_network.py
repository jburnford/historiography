#!/usr/bin/env python3
"""Canon map: the historians History PhDs cite, linked by co-citation, with no theses drawn.

User (2026-10-29): "a canon visualization based on the full dissertation graph; a network without
the dissertations and edges weighted based on co-citation counts at the historian level:
EPThompson 555 Foucault; Foucault 23 ColeHarris etc", "with a filter for low count historians".

- **Theses**: every strict History PhD (``in_analysis``) in ``dissertations.csv``, all countries.
- **People**: cited authors from ``authored.csv.gz`` (work -> person keys, namesake splits already
  applied by the graph build), counted once per thesis however many of their works it cites. Kept
  when cited by ``--floor`` (40) or more theses and the key looks like a person: 'surname|given',
  not a stray token ('in', 'vol', 'Anonymous'), not a government body, and not an initial-only key
  ('smith|r', several people merged) unless it carries a reviewed Wikidata QID.
- **Edges**: co-citation count, the number of theses citing both people. The page draws either the
  raw counts (as asked; the most cited theorists become hubs) or association strength
  (c_ab * N / (c_a * c_b), as on the works map; neighbours by shared readership, not by size).
  Each person keeps their ``--keep`` (5) strongest links among people visible at the threshold,
  pairs co-cited by at least ``--min-co`` (5) theses.
- **Filter**: the page's threshold for the minimum number of citing theses snaps to the values in
  ``--thresholds``; each (threshold, measure) has its own precomputed spring layout, so dropping
  low-count historians re-forms the map instead of leaving holes.
- **Colour**: the region whose share of History PhDs citing the person is at least ``--lean`` (1.5)
  times the next region's (Canada, United States, Britain, rest of Europe); otherwise shared.

Writes ``summary/comparisons/historian-network.html`` and the pair table
``summary/network/historian-cocitation-pairs.csv`` (all pairs with co-citation >= ``--min-co``).
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import gzip
import html
import json
import math
from pathlib import Path
import sys

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_layout import EUROPE  # noqa: E402
from render_region_comparison import proper  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731
REGIONS = {'CA': 'Canada', 'US': 'United States', 'GB': 'Britain', 'EU': 'Rest of Europe'}
LEANS = {**REGIONS, 'SHARED': 'Shared'}
# surnames or given-name parts that mark a corporate or place 'author', not a person
NOT_PEOPLE = {'canada', 'great britain', 'britain', 'england', 'ontario', 'quebec', 'france', 'united states', 'new',
              'york', 'the', 'of', 'house', 'parliament', 'commons', 'lords', 'senate', 'congress', 'department',
              'ministry', 'office', 'committee', 'commission', 'council', 'society', 'association', 'university',
              'library', 'archives', 'bureau', 'government', 'province', 'state', 'city', 'company', 'church',
              'census', 'statistics', 'national', 'royal', 'colonial', 'board', 'unesco', 'united nations', 'anon',
              'anonymous', 'anonyme', 'collectif', 'others', 'ed', 'eds', 'et', 'al', 'vol', 'vols'}


def region(country):
    if country in ('CA', 'US', 'GB'):
        return country
    return 'EU' if country in EUROPE or country == 'FR' else 'OTHER'


def is_person(key, qid):
    if '|' not in key:
        return False
    surname, given = key.split('|', 1)
    words = set(surname.split()) | set(given.split()) | {surname, given}
    if words & NOT_PEOPLE or len(surname) < 2 or any(ch.isdigit() for ch in surname):
        return False
    return bool(qid) or len(given.replace(' ', '')) > 1


def layout(n, edges, weight):
    """Spring layout of nodes 0..n-1; only the main connected part, others returned as None."""
    G = nx.Graph()
    G.add_nodes_from(range(n))
    wmax = max(weight.values())
    for a, b in edges:
        G.add_edge(a, b, weight=math.sqrt(weight[(a, b)] / wmax))
    main = max(nx.connected_components(G), key=len)
    H = G.subgraph(main).copy()
    pos = nx.spring_layout(H, weight='weight', k=1.6 / math.sqrt(len(main)), iterations=800, seed=7)
    xs, ys = sorted(p[0] for p in pos.values()), sorted(p[1] for p in pos.values())
    cx, cy = xs[len(xs) // 2], ys[len(ys) // 2]
    rad = sorted(math.hypot(p[0] - cx, p[1] - cy) for p in pos.values())
    r97 = rad[int(len(rad) * 0.97)] or 1
    return {i: (round((p[0] - cx) / r97, 4), round((p[1] - cy) / r97, 4)) for i, p in pos.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--floor', type=int, default=40, help='lowest threshold: people cited by at least this many theses')
    ap.add_argument('--thresholds', default='40,60,80,100,150,200,300', help='filter steps on the page')
    ap.add_argument('--default', type=int, default=150, help='threshold shown when the page opens')
    ap.add_argument('--keep', type=int, default=5)
    ap.add_argument('--min-co', type=int, default=5)
    ap.add_argument('--lean', type=float, default=1.5)
    ap.add_argument('--partners', type=int, default=12, help='top co-cited partners listed per person on hover')
    args = ap.parse_args()
    steps = sorted(int(t) for t in args.thresholds.split(','))
    assert steps[0] >= args.floor and args.default in steps

    country = {}
    for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8')):
        if r['in_analysis'] == 'True':
            country[r['id']] = r['country']
    totals = Counter(region(c) for c in country.values())
    people = {}
    for r in csv.DictReader((D / 'cited-people.csv').open(newline='', encoding='utf-8')):
        if int(r['cited_by_dissertations']) >= args.floor * 0.8 and is_person(r['person_key'], r['qid']):
            people[r['person_key']] = r
    work_theses = defaultdict(set)
    with gzip.open(D / 'strict-citations.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r['dissertation_id'] in country:
                work_theses[r['work_id']].add(r['dissertation_id'])
    by_thesis = defaultdict(set)
    with gzip.open(D / 'authored.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r['person_key'] in people and r['work_id'] in work_theses:
                for d in work_theses[r['work_id']]:
                    by_thesis[d].add(r['person_key'])
    citing = Counter(p for ps in by_thesis.values() for p in ps)
    keys = sorted((p for p, c in citing.items() if c >= args.floor), key=lambda p: (-citing[p], p))
    idx = {p: i for i, p in enumerate(keys)}
    n_theses = len(country)
    cnt = np.array([citing[p] for p in keys], dtype=np.int64)
    reg_cnt = {reg: Counter() for reg in REGIONS}
    # co-citation counts as a sparse thesis x person product
    from scipy.sparse import csr_matrix
    rows, cols = [], []
    for t, (d, ps) in enumerate(by_thesis.items()):
        reg = region(country[d])
        for p in ps:
            if p in idx:
                rows.append(t)
                cols.append(idx[p])
                if reg in reg_cnt:
                    reg_cnt[reg][idx[p]] += 1
    M = csr_matrix((np.ones(len(rows), dtype=np.int32), (rows, cols)), shape=(len(by_thesis), len(keys)))
    C = (M.T @ M).tocoo()
    co = {(int(a), int(b)): int(v) for a, b, v in zip(C.row, C.col, C.data) if a < b and v >= args.min_co}
    print(f'{n_theses} theses, {len(keys)} people >= {args.floor}, {len(co):,} pairs >= {args.min_co}', file=sys.stderr)
    strength = {k: v * n_theses / (cnt[k[0]] * cnt[k[1]]) for k, v in co.items()}

    nbr = defaultdict(list)
    for (a, b), v in co.items():
        nbr[a].append(b)
        nbr[b].append(a)
    views, nodes_seen = {}, set()
    for t in steps:
        vis = {i for i in range(len(keys)) if cnt[i] >= t}
        for measure, w in (('raw', co), ('assoc', strength)):
            edges = set()
            for a in vis:
                best = sorted(((w[(min(a, b), max(a, b))], b) for b in nbr[a] if b in vis), reverse=True)[:args.keep]
                edges.update((min(a, b), max(a, b)) for _, b in best)
            local = sorted(vis)
            li = {g: j for j, g in enumerate(local)}
            pos = layout(len(local), {(li[a], li[b]) for a, b in edges}, {(li[a], li[b]): w[(a, b)] for a, b in edges})
            placed = {local[j]: xy for j, xy in pos.items()}
            nodes_seen.update(placed)
            views[f'{t}-{measure}'] = dict(xy={i: placed[i] for i in placed},
                                           edges=[[a, b] for a, b in sorted(edges) if a in placed and b in placed])
            print(f'  threshold {t} {measure}: {len(vis)} people, {len(placed)} placed, {len(edges)} links', file=sys.stderr)

    nodes = []
    for i, p in enumerate(keys):
        r = people[p]
        shares = {reg: round(100 * reg_cnt[reg][i] / totals[reg], 1) for reg in REGIONS}
        top2 = sorted(shares.items(), key=lambda kv: -kv[1])
        lean = top2[0][0] if top2[0][1] >= args.lean * max(top2[1][1], 1e-9) else 'SHARED'
        partners = sorted(((co[(min(i, b), max(i, b))], b) for b in nbr[i]), reverse=True)[:args.partners]
        nodes.append(dict(name=proper(r['name']), qid=r['qid'], cited=int(cnt[i]), lean=lean, shares=shares,
                          top=[[b, v] for v, b in partners]))
    # node positions are per view; send them as compact arrays aligned with the view's node list
    payload_views = {}
    for k, v in views.items():
        ids = sorted(v['xy'])
        payload_views[k] = dict(ids=ids, xy=[list(v['xy'][i]) for i in ids], edges=v['edges'])
    drawn = {tuple(e) for v in views.values() for e in v['edges']}
    co_out = {f'{a},{b}': co[(a, b)] for a, b in drawn}
    payload = json.dumps(dict(nodes=nodes, views=payload_views, co=co_out, steps=steps, default=args.default,
                              leans=LEANS, theses=n_theses), ensure_ascii=False, separators=(',', ':'))

    pairs_path = D / 'summary' / 'network' / 'historian-cocitation-pairs.csv'
    with pairs_path.open('w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['person_a', 'person_b', 'cocited_by_theses', 'cited_a', 'cited_b', 'association_strength', 'key_a', 'key_b', 'qid_a', 'qid_b'])
        for (a, b), v in sorted(co.items(), key=lambda kv: -kv[1]):
            wr.writerow([nodes[a]['name'], nodes[b]['name'], v, cnt[a], cnt[b], round(strength[(a, b)], 3),
                         keys[a], keys[b], nodes[a]['qid'], nodes[b]['qid']])
    lean_counts = Counter(n['lean'] for n in nodes)
    page = (TEMPLATE.replace('__DATA__', payload.replace('</', '<\\/'))
            .replace('__N__', f'{len(nodes):,}').replace('__THESES__', f'{n_theses:,}').replace('__FLOOR__', str(args.floor))
            .replace('__KEEP__', str(args.keep)).replace('__MINCO__', str(args.min_co)).replace('__LEAN__', f'{args.lean:g}')
            .replace('__BUILT__', date.today().isoformat())
            .replace('__TOTALS__', ', '.join(f"{REGIONS[r]} {totals[r]:,}" for r in REGIONS) + f", elsewhere {totals['OTHER']:,}"))
    dest = D / 'summary' / 'comparisons' / 'historian-network.html'
    dest.write_text(page, encoding='utf-8')
    print(f'wrote {dest.relative_to(ROOT)} ({len(page) / 1e6:.1f} MB): {len(nodes)} people; leans {dict(lean_counts)}', file=sys.stderr)
    print(f'wrote {pairs_path.relative_to(ROOT)}: {len(co):,} pairs', file=sys.stderr)


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The canon by co-citation: historians History PhDs cite together</title>
<style>
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--series-4:#8a5cc9;--shared:#8f8e88;--edge:#b8b7b0}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--series-4:#9a70d6;--shared:#8a897f;--edge:#4a4944}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;
 --series-4:#9a70d6;--shared:#8a897f;--edge:#4a4944}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:24px max(16px,calc(50vw - 640px))}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 6px}
p.lede,.note{color:var(--text-secondary);max-width:860px}a{color:var(--series-1)}code{font-size:13px}ul.note li{margin:4px 0}
.controls{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;font-size:13px;color:var(--text-secondary);margin:12px 0 6px}
.controls label{display:flex;gap:6px;align-items:center}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;font-size:13px;color:var(--text-secondary);margin:4px 0 8px}
.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.legend .CA::before{background:var(--series-1)}.legend .US::before{background:var(--series-2)}.legend .GB::before{background:var(--series-4)}
.legend .EU::before{background:var(--series-3)}.legend .SHARED::before{background:var(--shared)}
.legend .NOQ::before{background:none;border:2px solid var(--shared);width:8px;height:8px}
button,select,input[type=search]{font:inherit;font-size:13px;padding:3px 10px;border:1px solid var(--grid);border-radius:6px;background:var(--surface-2);color:var(--text-primary)}
button{cursor:pointer}
.stage{border:1px solid var(--grid);border-radius:8px;overflow:hidden;background:var(--surface-1);touch-action:none}
svg.map{width:100%;height:78vh;min-height:520px;display:block;cursor:grab}
svg .link{stroke:var(--edge);stroke-linecap:round}
svg .node{cursor:move}svg .node circle{stroke:var(--surface-1);stroke-width:1.5}
svg .CA{fill:var(--series-1)}svg .US{fill:var(--series-2)}svg .GB{fill:var(--series-4)}svg .EU{fill:var(--series-3)}svg .SHARED{fill:var(--shared)}
svg .node.noq circle{fill-opacity:.25;stroke-width:1.5}
svg .node.noq .CA{stroke:var(--series-1)}svg .node.noq .US{stroke:var(--series-2)}svg .node.noq .GB{stroke:var(--series-4)}
svg .node.noq .EU{stroke:var(--series-3)}svg .node.noq .SHARED{stroke:var(--shared)}
svg text{fill:var(--text-primary);font-size:11px;paint-order:stroke;stroke:var(--surface-1);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
svg.focus .node{opacity:.15}svg.focus .link{opacity:.05}svg.focus .node.on{opacity:1}svg.focus .link.on{opacity:1;stroke:var(--text-muted)}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:7px 10px;font-size:12.5px;max-width:380px;box-shadow:0 2px 8px rgba(0,0,0,.14);display:none;z-index:5}
#tip b{display:block;margin-bottom:2px}#tip .m{color:var(--text-secondary);display:block;margin-bottom:4px}
#tip table{font-size:12px;margin:0}#tip td{padding:1px 6px;border:0}
details{margin:8px 0}summary{color:var(--text-secondary);font-size:13px;cursor:pointer}
table{border-collapse:collapse;font-size:13px;margin:8px 0}th,td{padding:3px 10px;text-align:right;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left;max-width:460px}
</style></head><body><main class="viz-root">
<h1>The canon by co-citation</h1>
<p class="lede">The people History PhDs cite, with the theses taken out: two people are linked when theses cite them both, and
the link's weight is that number of theses. __N__ people cited by at least __FLOOR__ of __THESES__ strict History PhDs
(all countries); the filter hides people cited by fewer theses and redraws the map for those left.</p>
<div class="controls">
<label>Cited by at least <input type="range" id="thr" min="0" step="1"> <span><b id="thrv"></b> theses (<span id="shown"></span> people)</span></label>
<label>Links <select id="measure"><option value="raw">co-citation count</option><option value="assoc">association strength</option></select></label>
<label><input type="search" id="find" placeholder="Find a person" list="names"></label><datalist id="names"></datalist>
<button id="reset">Reset view</button><button id="relayout">Reset positions</button></div>
<div class="legend"><span class="CA">Canada</span><span class="US">United States</span><span class="GB">Britain</span>
<span class="EU">Rest of Europe</span><span class="SHARED">Shared</span><span class="NOQ">no reviewed Wikidata QID</span>
<span>Size: number of citing theses. Wheel to zoom, drag the background to pan, drag a person to move them, hover a person for their most co-cited partners.</span></div>
<div class="stage"><svg class="map" id="map" role="img" aria-label="Co-citation network of cited historians"><g id="vp"></g></svg></div>
<div id="tip"></div>
<details><summary>Table: the strongest co-citations among the people shown</summary>
<table><thead><tr><th>Pair</th><th>Theses citing both</th><th>Cited (a)</th><th>Cited (b)</th></tr></thead><tbody id="pairs"></tbody></table></details>
<h2>How to read this</h2><ul class="note">
<li><b>Co-citation count</b> is the raw number of theses whose bibliographies cite both people (any of their works). It
grows with size, so the most cited theorists (Foucault, Anderson, Hobsbawm, Bourdieu) become hubs and the map shows the
canon's core and its reach. <b>Association strength</b> divides by what the two citation counts would give by chance (as in
VOSviewer), so people sit with those who share their readers, which brings out fields rather than fame.</li>
<li>Each person keeps their __KEEP__ strongest links among the people shown, pairs cited together by at least __MINCO__ theses.
Positions come from a spring layout of those links, computed for each filter step; the axes mean nothing. People with no
link to the main map at a step are not drawn.</li>
<li><b>Colour</b>: a person leans to a region when its share of History PhDs citing them is at least __LEAN__ times the next
region's (__TOTALS__ theses). Hollow circles have no reviewed Wikidata QID; most are real historians, but a few common
names may merge namesakes.</li>
<li><b>People</b> are the authors of cited works as the graph resolves them (namesakes split through the cited titles). Stray
tokens, government bodies and initial-only names without a QID are left out. A citation is not engagement.</li></ul>
<p class="note">Built __BUILT__ (<code>scripts/historian_cocitation_network.py</code>); every pair co-cited by at least __MINCO__ theses is in
<code>summary/network/historian-cocitation-pairs.csv</code>. See also the <a href="network.html">map of the most cited works</a>.</p>
<script id="data" type="application/json">__DATA__</script>
<script>
(()=>{
const DATA=JSON.parse(document.getElementById('data').textContent), svg=document.getElementById('map'), vp=document.getElementById('vp'), tip=document.getElementById('tip');
const NS='http://www.w3.org/2000/svg', S=1000, X=v=>v*S*0.46+S/2, Y=v=>v*S*0.46+S/2, N=DATA.nodes;
const thr=document.getElementById('thr'), measure=document.getElementById('measure'), find=document.getElementById('find');
thr.max=DATA.steps.length-1; thr.value=DATA.steps.indexOf(DATA.default);
const dl=document.getElementById('names');N.map(n=>n.name).sort().forEach(s=>{const o=document.createElement('option');o.value=s;dl.appendChild(o);});
const r=n=>2+Math.sqrt(n.cited)*0.36;
let cur=null, curKey='', pos={}, nbr={}, nodeEls={}, linkEls=[], labelEls={}, labelLayer, view={x:0,y:0,w:S,h:S};
const moved={};  // dragged positions, per filter step and link measure
const co=(a,b)=>DATA.co[Math.min(a,b)+','+Math.max(a,b)];
function draw(){
 const t=DATA.steps[+thr.value], key=t+'-'+measure.value; cur=DATA.views[key]; curKey=key; const mv=moved[key]||(moved[key]={});
 document.getElementById('thrv').textContent=t; document.getElementById('shown').textContent=cur.ids.length.toLocaleString();
 vp.textContent=''; pos={}; nbr={}; nodeEls={}; linkEls=[];
 cur.ids.forEach((i,j)=>{pos[i]=mv[i]||cur.xy[j];nbr[i]=[];});
 const wmax=Math.max(...cur.edges.map(([a,b])=>measure.value==='raw'?co(a,b):co(a,b)/(N[a].cited*N[b].cited)));
 for(const [a,b] of cur.edges){const l=document.createElementNS(NS,'line');l.setAttribute('class','link');l._a=a;
  l.setAttribute('x1',X(pos[a][0]));l.setAttribute('y1',Y(pos[a][1]));l.setAttribute('x2',X(pos[b][0]));l.setAttribute('y2',Y(pos[b][1]));
  const w=(measure.value==='raw'?co(a,b):co(a,b)/(N[a].cited*N[b].cited))/wmax;l.setAttribute('stroke-width',(0.3+2.2*Math.sqrt(w)).toFixed(2));
  nbr[a].push([b,l]);nbr[b].push([a,l]);vp.appendChild(l);linkEls.push(l);}
 for(const i of [...cur.ids].sort((a,b)=>N[a].cited-N[b].cited)){const n=N[i],g=document.createElementNS(NS,'g');g.setAttribute('class','node'+(n.qid?'':' noq'));
  const c=document.createElementNS(NS,'circle');c.setAttribute('cx',X(pos[i][0]));c.setAttribute('cy',Y(pos[i][1]));c.setAttribute('r',r(n).toFixed(1));c.setAttribute('class',n.lean);
  g.appendChild(c);g.dataset.i=i;vp.appendChild(g);nodeEls[i]=g;}
 labelLayer=document.createElementNS(NS,'g');vp.appendChild(labelLayer);
 const rows=[...cur.edges].sort((e,f)=>co(f[0],f[1])-co(e[0],e[1])).slice(0,150);
 document.getElementById('pairs').innerHTML=rows.map(([a,b])=>`<tr><td></td><td>${co(a,b)}</td><td>${N[a].cited}</td><td>${N[b].cited}</td></tr>`).join('');
 [...document.querySelectorAll('#pairs td:first-child')].forEach((td,k)=>{td.textContent=N[rows[k][0]].name+' — '+N[rows[k][1]].name;});
 fit();}
function setView(){svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`);labels();}
function labels(){if(!labelLayer)return;labelLayer.textContent='';labelEls={};const k=S/view.w,boxes=[],fs=11/k;
 for(const i of [...cur.ids].sort((a,b)=>N[b].cited-N[a].cited)){const n=N[i],x=X(pos[i][0])+r(n)+2/k,y=Y(pos[i][1])+fs*0.35;
  if(x<view.x||x>view.x+view.w||y<view.y||y>view.y+view.h)continue;
  const t=n.name.length>30?n.name.slice(0,28)+'…':n.name,w=t.length*fs*0.55,b=[x,y-fs,w,fs*1.2];
  if(boxes.some(o=>b[0]<o[0]+o[2]&&o[0]<b[0]+b[2]&&b[1]<o[1]+o[3]&&o[1]<b[1]+b[3]))continue;boxes.push(b);
  const e=document.createElementNS(NS,'text');e.setAttribute('x',x);e.setAttribute('y',y);e.style.fontSize=fs.toFixed(2)+'px';
  e.style.strokeWidth=(3/k).toFixed(2)+'px';e.textContent=t;labelLayer.appendChild(e);labelEls[i]=e;}}
function focus(i,e){svg.classList.toggle('focus',i!=null);Object.values(nodeEls).forEach(g=>g.classList.remove('on'));linkEls.forEach(l=>l.classList.remove('on'));
 if(i==null){tip.style.display='none';return;}
 nodeEls[i].classList.add('on');for(const [j,l] of nbr[i]){nodeEls[j].classList.add('on');l.classList.add('on');}
 const n=N[i];tip.innerHTML='<b></b><span class="m"></span><table></table>';tip.querySelector('b').textContent=n.name+(n.qid?' ('+n.qid+')':'');
 tip.querySelector('.m').textContent=`Cited by ${n.cited} theses · Canada ${n.shares.CA}% · US ${n.shares.US}% · Britain ${n.shares.GB}% · rest of Europe ${n.shares.EU}% · ${DATA.leans[n.lean]}. Most often cited with:`;
 const tb=tip.querySelector('table');for(const [j,v] of n.top){const tr=tb.insertRow();tr.insertCell().textContent=v;tr.insertCell().textContent=N[j].name+(pos[j]?'':' (hidden)');}
 if(e){tip.style.display='block';tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=Math.min(e.clientY+14,innerHeight-tip.offsetHeight-8)+'px';}}
vp.addEventListener('pointermove',e=>{const g=e.target.closest('.node');if(g&&!drag&&ndrag==null)focus(+g.dataset.i,e);});
vp.addEventListener('pointerout',e=>{if(ndrag!=null)return;if(!e.relatedTarget||!e.relatedTarget.closest||!e.relatedTarget.closest('.node'))focus(null);});
let drag=null, ndrag=null;
// drag a person: the background pan below is skipped, and the node, its links and its label follow the pointer
vp.addEventListener('pointerdown',e=>{const g=e.target.closest('.node');if(!g)return;e.stopPropagation();ndrag=+g.dataset.i;
 svg.setPointerCapture(e.pointerId);svg.style.cursor='grabbing';});
function moveNode(i,e){const p=svg.getBoundingClientRect(),px=view.x+(e.clientX-p.left)*view.w/p.width,py=view.y+(e.clientY-p.top)*view.h/p.height;
 const v=[(px-S/2)/(S*0.46),(py-S/2)/(S*0.46)];pos[i]=v;moved[curKey][i]=v;
 const c=nodeEls[i].firstChild;c.setAttribute('cx',px);c.setAttribute('cy',py);
 for(const [,l] of nbr[i]){if(l._a===i){l.setAttribute('x1',px);l.setAttribute('y1',py);}else{l.setAttribute('x2',px);l.setAttribute('y2',py);}}
 const t=labelEls[i];if(t){const k=S/view.w;t.setAttribute('x',px+r(N[i])+2/k);t.setAttribute('y',py+11/k*0.35);}
 focus(i,e);}
svg.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};svg.setPointerCapture(e.pointerId);svg.style.cursor='grabbing';});
svg.addEventListener('pointermove',e=>{if(ndrag!=null){moveNode(ndrag,e);return;}if(!drag)return;const k=view.w/svg.clientWidth;view.x=drag.vx-(e.clientX-drag.x)*k;view.y=drag.vy-(e.clientY-drag.y)*k;setView();});
svg.addEventListener('pointerup',()=>{if(ndrag!=null){ndrag=null;labels();}drag=null;svg.style.cursor='grab';});
svg.addEventListener('wheel',e=>{e.preventDefault();const p=svg.getBoundingClientRect(),mx=view.x+(e.clientX-p.left)*view.w/p.width,my=view.y+(e.clientY-p.top)*view.h/p.height;
 const f=Math.exp(e.deltaY*0.0015);view.x=mx-(mx-view.x)*f;view.y=my-(my-view.y)*f;view.w*=f;view.h*=f;setView();},{passive:false});
function fit(){const p=svg.getBoundingClientRect(),a=p.height/p.width;
 const xs=cur.xy.map(q=>X(q[0])),ys=cur.xy.map(q=>Y(q[1]));let x0=Math.min(...xs)-30,x1=Math.max(...xs)+150,y0=Math.min(...ys)-30,y1=Math.max(...ys)+30;
 let w=x1-x0,h=y1-y0;if(h/w>a){const nw=h/a;x0-=(nw-w)/2;w=nw;}else{const nh=w*a;y0-=(nh-h)/2;h=nh;}view={x:x0,y:y0,w,h};setView();}
find.addEventListener('change',()=>{const i=N.findIndex(n=>n.name===find.value);if(i<0)return;
 if(!pos[i]){const s=DATA.steps.filter(t=>t<=N[i].cited);thr.value=DATA.steps.indexOf(s[s.length-1]??DATA.steps[0]);draw();}
 if(!pos[i])return;const cx=X(pos[i][0]),cy=Y(pos[i][1]);view={x:cx-view.w/6,y:cy-view.h/6,w:view.w/3,h:view.h/3};setView();focus(i,null);});
thr.addEventListener('input',draw);measure.addEventListener('change',draw);
document.getElementById('reset').addEventListener('click',fit);
document.getElementById('relayout').addEventListener('click',()=>{moved[curKey]={};draw();});new ResizeObserver(fit).observe(svg);
draw();
})();
</script></main></body></html>
"""

if __name__ == '__main__':
    main()
