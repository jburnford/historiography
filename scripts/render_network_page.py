#!/usr/bin/env python3
"""Render the network page: History PhDs and the works they cite, as one force-directed graph.

Reads ``summary/network/subgraph.json`` and ``layout.json`` (``network_layout.py extract`` then
``layout``) and writes a self-contained page (canvas, no external assets) to
``summary/comparisons/network-full.html`` (the page ``network.html`` is the co-citation map of
``render_cocitation_map.py``):

    python3 scripts/network_layout.py extract --out <D> --min-cited 8 --min-regional 4
    python3 scripts/network_layout.py layout --out <D>
    python3 scripts/render_network_page.py

Theses are coloured by region as on the comparison pages (Canada blue, United States orange,
France aqua, rest of Europe an aqua ring, elsewhere grey); works are neutral and sized by the
number of drawn theses citing them. Wheel to zoom, drag to pan, hover for details, click a node
to highlight its links; region toggles and a work search sit above the canvas.
"""
from datetime import date
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
NET = D / 'summary' / 'network'
REGIONS = ['CA', 'US', 'FR', 'EU', 'OTHER']
REGION_NAMES = {'CA': 'Canada', 'US': 'United States', 'FR': 'France', 'EU': 'Rest of Europe', 'OTHER': 'Elsewhere'}
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731


def main():
    sub = json.load((NET / 'subgraph.json').open())
    lay = json.load((NET / 'layout.json').open())
    # Frame on the bulk of the graph: centre on the median and scale by the 99th-percentile radius,
    # so a few far-flung outlier clusters do not shrink the map.
    import statistics
    xs, ys = [p[0] for p in lay['xy']], [p[1] for p in lay['xy']]
    mx, my = statistics.median(xs), statistics.median(ys)
    radii = sorted(((x - mx) ** 2 + (y - my) ** 2) ** 0.5 for x, y in lay['xy'])
    r99 = radii[int(len(radii) * 0.99)] or 1
    xy = {k: [(x - mx) / r99, (y - my) / r99] for k, (x, y) in zip(lay['ids'], lay['xy'])}
    nodes, labels, extra, index = [], [], [], {}
    for t in sub['theses']:
        index[t['id']] = len(nodes) // 5  # node number (five values per node)
        x, y = xy[t['id']]
        nodes += [x, y, 0, REGIONS.index(t['region']), 0]
        labels.append(t['title'])
        extra.append(f"{t['author']} · {t['institution']}, {t['year'] or 'n.d.'}" + (' · bibliography rebuilt from notes' if t['notes'] else ''))
    for w in sub['works']:
        index[w['id']] = len(nodes) // 5
        x, y = xy[w['id']]
        nodes += [x, y, 1, -1, w['cited']]
        name = w['author'].split(',')[0] if w['author'] else ''
        labels.append(f"{name}, {w['title']}" + (f" ({w['year']})" if w['year'] else ''))
        extra.append(' · '.join(f"{REGION_NAMES[r]} {w['by_region'].get(r, 0)}" for r in REGIONS if w['by_region'].get(r)))
    edges = []
    for d, w in sub['edges']:
        edges += [index[d], index[w]]
    top = sorted(sub['works'], key=lambda w: -w['cited'])[:40]
    rows = ''.join(f"<tr><td>{esc((w['author'].split(',')[0] + ', ') if w['author'] else '')}{esc(w['title'])}</td><td>{w['cited']}</td>"
                   + ''.join(f"<td>{w['by_region'].get(r, 0)}</td>" for r in REGIONS) + '</tr>' for w in top)
    n_theses, n_works = len(sub['theses']), len(sub['works'])
    payload = json.dumps(dict(nodes=[round(v, 4) if isinstance(v, float) else v for v in nodes], labels=labels, extra=extra,
                              edges=edges, regions=REGIONS, names=REGION_NAMES), ensure_ascii=False, separators=(',', ':'))
    page = TEMPLATE.replace('__DATA__', payload.replace('</', '<\\/')).replace('__ROWS__', rows).replace(
        '__N_THESES__', f'{n_theses:,}').replace('__N_WORKS__', f'{n_works:,}').replace('__N_EDGES__', f'{len(sub["edges"]):,}').replace(
        '__STRICT__', f"{sub['strict_total']:,}").replace('__MISSING__', f"{sub['strict_total'] - n_theses:,}").replace(
        '__MIN_CITED__', str(sub['params']['min_cited'])).replace('__MIN_REGIONAL__', str(sub['params']['min_regional'])).replace(
        '__BUILT__', date.today().isoformat()).replace('__REGION_HEAD__', ''.join(f'<th>{REGION_NAMES[r]}</th>' for r in REGIONS))
    dest = D / 'summary' / 'comparisons' / 'network-full.html'
    dest.write_text(page, encoding='utf-8')
    print(f'wrote {dest.relative_to(ROOT)} ({dest.stat().st_size / 1e6:.1f} MB; {n_theses} theses, {n_works} works, {len(sub["edges"])} edges)')


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The citation network of History PhDs</title>
<style>
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--node-work:#8f8e88;--edge:#7a7974;--other:#a3a29b}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--node-work:#8a897f;--edge:#9c9b92;--other:#6f6e68}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;
 --node-work:#8a897f;--edge:#9c9b92;--other:#6f6e68}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:24px max(16px,calc(50vw - 640px))}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 6px}
p.lede,.note{color:var(--text-secondary);max-width:860px}a{color:var(--series-1)}code{font-size:13px}
.controls{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;margin:12px 0 8px;font-size:13px;color:var(--text-secondary)}
.controls label{display:inline-flex;align-items:center;gap:6px;cursor:pointer}
.sw{display:inline-block;width:11px;height:11px;border-radius:50%;box-sizing:border-box}
.sw.CA{background:var(--series-1)}.sw.US{background:var(--series-2)}.sw.FR{background:var(--series-3)}
.sw.EU{border:2px solid var(--series-3)}.sw.OTHER{background:var(--other)}.sw.W{background:var(--node-work);border-radius:2px}
input[type=search]{font:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--grid);border-radius:6px;background:var(--surface-1);color:var(--text-primary);min-width:240px}
button{font:inherit;font-size:13px;padding:4px 10px;border:1px solid var(--grid);border-radius:6px;background:var(--surface-2);color:var(--text-primary);cursor:pointer}
.stage{position:relative;height:78vh;min-height:520px;border:1px solid var(--grid);border-radius:8px;overflow:hidden;background:var(--surface-1);touch-action:none}
.stage canvas{position:absolute;inset:0;width:100%;height:100%}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:6px 9px;font-size:12.5px;max-width:380px;box-shadow:0 2px 8px rgba(0,0,0,.14);display:none;z-index:5}
#tip b{display:block;margin-bottom:2px}#tip span{color:var(--text-secondary)}
details{margin:8px 0}summary{color:var(--text-secondary);font-size:13px;cursor:pointer}
table{border-collapse:collapse;font-size:13px;margin:8px 0}th,td{padding:3px 10px;text-align:right;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left;max-width:460px}
.status{font-size:12.5px;color:var(--text-muted)}
</style></head><body><main class="viz-root">
<h1>The citation network of History PhDs</h1>
<p class="lede">__N_THESES__ History PhDs and the __N_WORKS__ works they most often cite, joined by __N_EDGES__ citations and laid out
so that theses citing the same literature sit together (a force-directed layout of the ForceAtlas2 kind). Theses are coloured by where the degree
was awarded; works are dark and sized by how many of the drawn theses cite them.</p>
<div class="controls" id="toggles">
 <label><input type="checkbox" data-r="CA" checked><span class="sw CA"></span>Canada</label>
 <label><input type="checkbox" data-r="US" checked><span class="sw US"></span>United States</label>
 <label><input type="checkbox" data-r="FR" checked><span class="sw FR"></span>France</label>
 <label><input type="checkbox" data-r="EU" checked><span class="sw EU"></span>Rest of Europe</label>
 <label><input type="checkbox" data-r="OTHER" checked><span class="sw OTHER"></span>Elsewhere</label>
 <span><span class="sw W"></span> Cited work</span>
</div>
<div class="controls"><input type="search" id="q" placeholder="Find a work or author (e.g. Foucault, Imagined)" aria-label="Find a work">
 <button id="reset">Reset view</button><span class="status" id="status">Wheel or pinch to zoom, drag to pan, click a node to highlight its links.</span></div>
<div class="stage" id="stage"><canvas id="base"></canvas><canvas id="over"></canvas></div>
<div id="tip"></div>
<details><summary>Table: the 40 most cited works in the network, by region of the citing theses</summary>
<table><thead><tr><th>Work</th><th>Theses</th>__REGION_HEAD__</tr></thead><tbody>__ROWS__</tbody></table></details>
<h2>How to read this</h2><ul class="note">
<li><b>What is drawn.</b> Strict History PhDs (__STRICT__ in the graph) and every work cited by at least __MIN_CITED__ of them, or
by at least __MIN_REGIONAL__ within France, the rest of Europe or elsewhere, so the smaller regions' own canons are drawn too.
__MISSING__ theses cite none of these works and are not drawn; most are European, where citation is more dispersed.</li>
<li><b>Position.</b> Linked nodes attract and all nodes repel, so a thesis sits among the works it cites and a work among the
theses citing it. Distance across the map is only meaningful as clustering; the axes have no meaning.</li>
<li><b>Works</b> are first-author surname and main title; translations mapped through Wikidata count as one work. A citation
is not engagement.</li></ul>
<p class="note">Built __BUILT__ (<code>scripts/network_layout.py</code>, <code>scripts/render_network_page.py</code>). See also the
<a href="network.html">map of the most cited works</a>, <a href="europe-ca-us.html">Europe, Canada and the United States</a> and <a href="ca-us.html">Canada and the United States</a>.</p>
<script id="data" type="application/json">__DATA__</script>
<script>
(()=>{
const DATA=JSON.parse(document.getElementById('data').textContent);
const N=DATA.nodes.length/5, nx=new Float32Array(N), ny=new Float32Array(N), kind=new Uint8Array(N), reg=new Int8Array(N), cited=new Uint16Array(N);
for(let i=0;i<N;i++){nx[i]=DATA.nodes[5*i];ny[i]=DATA.nodes[5*i+1];kind[i]=DATA.nodes[5*i+2];reg[i]=DATA.nodes[5*i+3];cited[i]=DATA.nodes[5*i+4];}
const E=DATA.edges, nE=E.length/2, adj=Array.from({length:N},()=>[]);
for(let k=0;k<nE;k++){adj[E[2*k]].push(E[2*k+1]);adj[E[2*k+1]].push(E[2*k]);}
const radius=i=>kind[i]?1.1+Math.sqrt(cited[i])*0.22:1.7;
const stage=document.getElementById('stage'), base=document.getElementById('base'), over=document.getElementById('over'), tip=document.getElementById('tip');
const bctx=base.getContext('2d'), octx=over.getContext('2d');
const on={CA:true,US:true,FR:true,EU:true,OTHER:true};
let W=0,H=0,dpr=1,scale=1,tx=0,ty=0,selected=-1,matches=[],frame=0;
const css=n=>getComputedStyle(stage).getPropertyValue(n).trim();
let C={};
function colours(){C={CA:css('--series-1'),US:css('--series-2'),FR:css('--series-3'),EU:css('--series-3'),OTHER:css('--other'),
 work:css('--node-work'),edge:css('--edge'),text:css('--text-primary'),surface:css('--surface-1'),muted:css('--text-muted')};}
function fit(){scale=Math.min(W,H)*0.46;tx=W/2;ty=H/2;}
function resize(){const r=stage.getBoundingClientRect();dpr=window.devicePixelRatio||1;W=r.width;H=r.height;
 for(const c of [base,over]){c.width=W*dpr;c.height=H*dpr;c.getContext('2d').setTransform(dpr,0,0,dpr,0,0);}
 if(!scale||scale===1)fit();draw();}
const sx=i=>nx[i]*scale+tx, sy=i=>ny[i]*scale+ty;
const visible=i=>kind[i]===1||on[DATA.regions[reg[i]]];
function dot(ctx,i,r){const x=sx(i),y=sy(i);
 if(kind[i]){ctx.fillStyle=C.work;ctx.beginPath();ctx.arc(x,y,r,0,6.2832);ctx.fill();return;}
 const g=DATA.regions[reg[i]];
 if(g==='EU'){ctx.strokeStyle=C.EU;ctx.lineWidth=1.3;ctx.beginPath();ctx.arc(x,y,r+0.6,0,6.2832);ctx.stroke();return;}
 ctx.fillStyle=C[g];ctx.beginPath();ctx.arc(x,y,r,0,6.2832);ctx.fill();}
function draw(){cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
 bctx.clearRect(0,0,W,H);
 bctx.globalAlpha=Math.min(0.10,0.035*Math.sqrt(scale/(Math.min(W,H)*0.46)));bctx.strokeStyle=C.edge;bctx.lineWidth=0.6;bctx.beginPath();
 for(let k=0;k<nE;k++){const a=E[2*k],b=E[2*k+1];if(!visible(a))continue;bctx.moveTo(sx(a),sy(a));bctx.lineTo(sx(b),sy(b));}
 bctx.stroke();bctx.globalAlpha=1;
 const z=Math.sqrt(scale/(Math.min(W,H)*0.46));
 bctx.globalAlpha=0.55;for(let i=0;i<N;i++)if(kind[i])dot(bctx,i,radius(i)*Math.min(z,2.2));bctx.globalAlpha=1;
 for(let i=0;i<N;i++)if(!kind[i]&&visible(i))dot(bctx,i,1.8*Math.min(z,2.2));  // theses on top: region colour is the story
 labels(z);overlay();});}
function labels(z){const order=[...Array(N).keys()].filter(i=>kind[i]).sort((a,b)=>cited[b]-cited[a]);
 const taken=[];bctx.font='12px system-ui,sans-serif';bctx.textBaseline='middle';let shown=0;const limit=Math.round(16*z*z);
 for(const i of order){if(shown>=limit)break;const x=sx(i),y=sy(i);if(x<0||y<0||x>W||y>H)continue;
  const t=DATA.labels[i].length>42?DATA.labels[i].slice(0,40)+'…':DATA.labels[i];const w=bctx.measureText(t).width;
  const box=[x+radius(i)*Math.min(z,2.2)+4,y-8,w,16];
  if(taken.some(b=>box[0]<b[0]+b[2]&&b[0]<box[0]+box[2]&&box[1]<b[1]+b[3]&&b[1]<box[1]+box[3]))continue;
  taken.push(box);shown++;bctx.lineWidth=3;bctx.strokeStyle=C.surface;bctx.strokeText(t,box[0],y);bctx.fillStyle=C.text;bctx.fillText(t,box[0],y);}}
function overlay(){octx.clearRect(0,0,W,H);const z=Math.sqrt(scale/(Math.min(W,H)*0.46));
 const hl=selected>=0?[selected]:matches;if(!hl.length)return;
 octx.fillStyle=C.surface;octx.globalAlpha=0.55;octx.fillRect(0,0,W,H);octx.globalAlpha=1;
 for(const s of hl){octx.strokeStyle=C.edge;octx.lineWidth=0.8;octx.globalAlpha=0.5;octx.beginPath();
  for(const j of adj[s]){if(!visible(j))continue;octx.moveTo(sx(s),sy(s));octx.lineTo(sx(j),sy(j));}octx.stroke();octx.globalAlpha=1;
  for(const j of adj[s])if(visible(j))dot(octx,j,(kind[j]?radius(j):1.9)*Math.min(z,2.2));
  dot(octx,s,(kind[s]?radius(s):2.5)*Math.min(z,2.2)+1.5);
  octx.font='600 12.5px system-ui,sans-serif';octx.textBaseline='middle';const t=DATA.labels[s].slice(0,70);
  octx.lineWidth=3;octx.strokeStyle=C.surface;octx.strokeText(t,sx(s)+10,sy(s));octx.fillStyle=C.text;octx.fillText(t,sx(s)+10,sy(s));}}
function nearest(mx,my){let best=-1,bd=144;const z=Math.sqrt(scale/(Math.min(W,H)*0.46));
 for(let i=0;i<N;i++){if(!visible(i))continue;const dx=sx(i)-mx,dy=sy(i)-my,d=dx*dx+dy*dy,r=(kind[i]?radius(i):2)*Math.min(z,2.2)+5;
  if(d<Math.max(bd,0)&&d<=r*r+60){bd=d;best=i;}}return best;}
function showTip(i,e){if(i<0){tip.style.display='none';return;}
 const deg=adj[i].length;tip.innerHTML='<b></b><span></span>';tip.querySelector('b').textContent=DATA.labels[i];
 tip.querySelector('span').textContent=kind[i]?`Cited by ${deg} drawn theses: ${DATA.extra[i]}`:`${DATA.names[DATA.regions[reg[i]]]} · ${DATA.extra[i]} · cites ${deg} drawn works`;
 tip.style.display='block';tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(e.clientY+14)+'px';}
let drag=null,moved=false;
stage.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,tx,ty};moved=false;stage.setPointerCapture(e.pointerId);});
stage.addEventListener('pointermove',e=>{const r=stage.getBoundingClientRect();
 if(drag){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>3)moved=true;
  if(moved){tx=drag.tx+dx;ty=drag.ty+dy;tip.style.display='none';draw();return;}}
 showTip(nearest(e.clientX-r.left,e.clientY-r.top),e);});
stage.addEventListener('pointerup',e=>{const r=stage.getBoundingClientRect();
 if(drag&&!moved){const i=nearest(e.clientX-r.left,e.clientY-r.top);selected=i===selected?-1:i;matches=[];overlay();}drag=null;});
stage.addEventListener('pointerleave',()=>{tip.style.display='none';});
stage.addEventListener('wheel',e=>{e.preventDefault();const r=stage.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
 const f=Math.exp(-e.deltaY*0.0015);tx=mx-(mx-tx)*f;ty=my-(my-ty)*f;scale*=f;draw();},{passive:false});
document.querySelectorAll('#toggles input').forEach(c=>c.addEventListener('change',()=>{on[c.dataset.r]=c.checked;draw();}));
document.getElementById('reset').addEventListener('click',()=>{fit();selected=-1;matches=[];document.getElementById('q').value='';draw();});
document.getElementById('q').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();selected=-1;
 matches=q.length<3?[]:[...Array(N).keys()].filter(i=>kind[i]&&DATA.labels[i].toLowerCase().includes(q)).sort((a,b)=>cited[b]-cited[a]).slice(0,8);
 document.getElementById('status').textContent=q.length<3?'Wheel or pinch to zoom, drag to pan, click a node to highlight its links.':
  matches.length?`${matches.length} work${matches.length>1?'s':''} highlighted (most cited first)`:'No drawn work matches';overlay();});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{colours();draw();});
colours();new ResizeObserver(resize).observe(stage);
})();
</script></main></body></html>
"""

if __name__ == '__main__':
    main()
