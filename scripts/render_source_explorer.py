#!/usr/bin/env python3
"""Render the source explorer page from ``summary/explorer/explorer.json`` (build_source_explorer.py).

Writes ``summary/comparisons/explorer.html``: a self-contained page (inline SVG and JavaScript, no
external assets). Pick a cited work or person to see its citations over time by region, the works or
people cited with it, how that company changes period by period, and its company in each region.
"""
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'


def main():
    data = json.load((D / 'summary' / 'explorer' / 'explorer.json').open())
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    n_people = sum(1 for s in data['sources'] if data['labels'][s['id']]['key'].startswith('P:'))
    page = (TEMPLATE.replace('__DATA__', payload).replace('__BUILT__', date.today().isoformat())
            .replace('__NW__', f"{len(data['sources']) - n_people:,}").replace('__NP__', f'{n_people:,}')
            .replace('__MINW__', str(data['params']['min_work'])).replace('__MINP__', str(data['params']['min_person']))
            .replace('__MINS__', f"{data['params']['min_strength']:g}"))
    dest = D / 'summary' / 'comparisons' / 'explorer.html'
    dest.write_text(page, encoding='utf-8')
    print(f'wrote {dest.relative_to(ROOT)} ({dest.stat().st_size / 1e6:.1f} MB)')


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Source explorer: who History PhDs cite, with whom, and when</title>
<style>
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--other:#a3a29b;--edge:#c9c8c2;
 --f0:#008300;--f1:#e34948;--f2:#6250d6;--f3:#e87ba4;--f4:#eda100;--f5:#c9c8c2;
 --seq-0:#f2f1ed;--seq-1:#cde2fb;--seq-2:#9ec5f4;--seq-3:#6da7ec;--seq-4:#3987e5;--seq-5:#256abf;--seq-6:#184f95;--seq-7:#0d366b}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--other:#6f6e68;--edge:#4a4944;
 --f0:#008300;--f1:#e66767;--f2:#9085e9;--f3:#d55181;--f4:#c98500;--f5:#4a4944;
 --seq-0:#242422;--seq-1:#0d366b;--seq-2:#104281;--seq-3:#184f95;--seq-4:#1c5cab;--seq-5:#2a78d6;--seq-6:#5598e7;--seq-7:#9ec5f4}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;
 --other:#6f6e68;--edge:#4a4944;--f0:#008300;--f1:#e66767;--f2:#9085e9;--f3:#d55181;--f4:#c98500;--f5:#4a4944;
 --seq-0:#242422;--seq-1:#0d366b;--seq-2:#104281;--seq-3:#184f95;--seq-4:#1c5cab;--seq-5:#2a78d6;
 --seq-6:#5598e7;--seq-7:#9ec5f4}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:24px max(16px,calc(50vw - 620px))}
h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 4px}h3{font-size:15px;margin:10px 0 4px}
p.lede,.note{color:var(--text-secondary);max-width:860px}a{color:var(--series-1)}code{font-size:13px}ul.note li{margin:4px 0}
.search{position:relative;max-width:560px;margin:14px 0}
.search input{width:100%;box-sizing:border-box;font:inherit;padding:8px 12px;border:1px solid var(--grid);border-radius:8px;background:var(--surface-1);color:var(--text-primary)}
.sugg{position:absolute;left:0;right:0;top:100%;background:var(--surface-1);border:1px solid var(--grid);border-radius:8px;margin-top:4px;z-index:6;display:none;max-height:360px;overflow:auto}
.sugg div{padding:6px 12px;cursor:pointer;display:flex;justify-content:space-between;gap:12px}.sugg div:hover,.sugg div.on{background:var(--surface-2)}
.sugg small{color:var(--text-muted);white-space:nowrap}
.head{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline}.head .kind{color:var(--text-muted);font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}
.tile{background:var(--surface-2);border-radius:8px;padding:10px 12px}.tile .v{font-size:22px;font-weight:600}.tile .k{color:var(--text-secondary);font-size:12.5px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--text-secondary);margin:4px 0}
.legend span::before{content:"";display:inline-block;width:14px;height:3px;margin-right:6px;vertical-align:3px;border-radius:2px}
.legend .CA::before{background:var(--series-1)}.legend .US::before{background:var(--series-2)}.legend .EUROPE::before{background:var(--series-3)}
.legend .OTHER::before{background:var(--other)}
svg{display:block;width:100%;height:auto}
.grid line{stroke:var(--grid)}.tick{fill:var(--text-muted);font-size:11px}
.line{fill:none;stroke-width:2;stroke-linejoin:round}.pt{stroke:var(--surface-1);stroke-width:2}
.s-CA{stroke:var(--series-1);fill:var(--series-1)}.s-US{stroke:var(--series-2);fill:var(--series-2)}
.s-EUROPE{stroke:var(--series-3);fill:var(--series-3)}.s-OTHER{stroke:var(--other);fill:var(--other)}
.line.s-CA,.line.s-US,.line.s-EUROPE,.line.s-OTHER{fill:none}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:22px}@media(max-width:900px){.two{grid-template-columns:1fr}}
.fleg{display:grid;gap:3px;font-size:12.5px;margin:6px 0 4px}.fleg span{display:flex;gap:7px;align-items:baseline}
.fleg i{flex:none;width:11px;height:11px;border-radius:2px;display:inline-block;transform:translateY(1px)}.fleg small{color:var(--text-muted)}
.seg{stroke:var(--surface-1);stroke-width:2}.segt{font-size:10.5px;fill:var(--surface-1);pointer-events:none}
.periods{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}
.periods button{font:inherit;font-size:12px;padding:2px 8px;border:1px solid var(--grid);border-radius:6px;background:var(--surface-1);color:var(--text-secondary);cursor:pointer}
.periods button.on{background:var(--text-primary);color:var(--surface-1);border-color:var(--text-primary)}
.net .lk{stroke:var(--edge)}.net .cn{fill:var(--text-secondary)}.net .src{fill:var(--text-primary)}
.net text{fill:var(--text-primary);font-size:11px;paint-order:stroke;stroke:var(--surface-1);stroke-width:3px;stroke-linejoin:round}
.net .off{opacity:.18}
table.heat{border-collapse:separate;border-spacing:2px;font-size:12px;width:100%}
table.heat th{font-weight:500;color:var(--text-muted);font-size:11px;text-align:center;padding:2px}
table.heat td.l{text-align:left;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px;padding-right:6px}
table.heat td.c{height:20px;min-width:34px;border-radius:3px;text-align:center;font-size:10.5px}
table.heat td.thin{opacity:.35}
.regions{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
.bar{display:grid;grid-template-columns:1fr 46px;gap:8px;align-items:center;font-size:12.5px;margin:3px 0}
.bar .t{position:relative;padding:2px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .t i{position:absolute;inset:0 auto 0 0;border-radius:3px;opacity:.22}
.bar .v{text-align:right;color:var(--text-secondary)}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:6px 9px;font-size:12.5px;max-width:360px;box-shadow:0 2px 8px rgba(0,0,0,.14);display:none;z-index:9}
#tip b{display:block}#tip span{color:var(--text-secondary)}
</style></head><body><main class="viz-root">
<h1>Source explorer</h1>
<p class="lede">Pick a work or a person cited in History PhD dissertations to see how often it is cited over time in Canada, the
United States and Europe, what is cited with it, and how that company changes. __NW__ works (cited by __MINW__ or more History
PhDs) and __NP__ people (__MINP__ or more) can be explored.</p>
<div class="search"><input id="q" type="search" placeholder="Search a work or person, e.g. Cronon, Foucault, Thompson" aria-label="Search a source" autocomplete="off"><div class="sugg" id="sugg"></div></div>
<div id="view"></div>
<h2>How to read this</h2><ul class="note">
<li><b>Share citing</b>: the percentage of a region's strict History PhDs in that period whose bibliography (or notes) cites the source.
Shares are shown only where a region has at least 15 PhDs in the period; counts are in the tooltips.</li>
<li><b>Who cites it, by field</b>: each placed dissertation is a mixture of citation families found by TF-IDF and NMF over all History PhD
bibliographies, labelled by their signature works and title terms (labels are provisional). The column shows how the citing dissertations' mixtures
divide among the source's five largest families. About 40% of dissertations are not placed by the model.</li>
<li><b>Companions</b>: works (for a work) or people (for a person) that appear in the same dissertations at least __MINS__ times as often as
chance would give (association strength), ranked by the number of shared dissertations. A citation is not engagement.</li>
<li><b>Company over time</b>: of the dissertations citing the source in each period, the share that also cite each companion. Rows include
each period's own leading companions; pale columns have fewer than 10 citing dissertations.</li>
<li>Works are first-author surname and main title, with translations merged through Wikidata; people are first authors.</li></ul>
<p class="note">Built __BUILT__ (<code>scripts/build_source_explorer.py</code>, <code>scripts/render_source_explorer.py</code>). See also the
<a href="network.html">map of the most cited works</a> and <a href="europe-ca-us.html">Europe, Canada and the United States</a>.</p>
<div id="tip"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
(()=>{
const DATA=JSON.parse(document.getElementById('data').textContent);
const P=DATA.periods, R=DATA.regions, NAMES={CA:'Canada',US:'United States',EUROPE:'Europe',OTHER:'Elsewhere'}, L=DATA.labels;
const byId=new Map(DATA.sources.map(s=>[s.id,s])), byKey=new Map(DATA.sources.map(s=>[L[s.id].key,s]));
const isPerson=x=>L[x].key.startsWith('P:');
const FAM=DATA.families, BASE=DATA.baseline;
const view=document.getElementById('view'), tip=document.getElementById('tip'), q=document.getElementById('q'), sugg=document.getElementById('sugg');
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const lab=x=>L[x]?L[x].short:x, full=x=>{const l=L[x];if(!l)return x;if(isPerson(x))return l.short;return (l.author?l.author+', ':'')+l.full+(l.year?` (${l.year})`:'');};
function showTip(e,h){tip.innerHTML=h;tip.style.display='block';tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(e.clientY+14)+'px';}
const hide=()=>{tip.style.display='none';};
// search
const index=DATA.sources.map(s=>({id:s.id,n:s.n,text:(lab(s.id)+' '+(L[s.id]?.full||'')+' '+(L[s.id]?.author||'')).toLowerCase()}));
let hits=[],sel=0;
function suggest(){const t=q.value.trim().toLowerCase();if(t.length<2){sugg.style.display='none';return;}
 hits=index.filter(x=>x.text.includes(t)).sort((a,b)=>(isPerson(b.id)-isPerson(a.id))||b.n-a.n).slice(0,14);sel=0;
 sugg.innerHTML=hits.map((h,i)=>`<div data-i="${i}" class="${i?'':'on'}"><span>${esc(lab(h.id))}</span><small>${isPerson(h.id)?'person':'work'} · ${h.n} PhDs</small></div>`).join('')||'<div><span>No source matches</span></div>';
 sugg.style.display='block';}
q.addEventListener('input',suggest);
q.addEventListener('keydown',e=>{if(!hits.length)return;if(e.key==='ArrowDown'||e.key==='ArrowUp'){sel=(sel+(e.key==='ArrowDown'?1:hits.length-1))%hits.length;
 [...sugg.children].forEach((d,i)=>d.classList.toggle('on',i===sel));e.preventDefault();}
 if(e.key==='Enter'){pick(hits[sel].id);}});
sugg.addEventListener('click',e=>{const d=e.target.closest('[data-i]');if(d)pick(hits[+d.dataset.i].id);});
document.addEventListener('click',e=>{if(!e.target.closest('.search'))sugg.style.display='none';});
function pick(id){sugg.style.display='none';q.value=lab(id);render(byId.get(id));history.replaceState(null,'','#'+encodeURIComponent(L[id].key));}
// charts
function lineChart(s){const W=900,H=280,x0=52,x1=858,y0=20,y1=240;
 const share=(p,r)=>{const d=DATA.denominators[p][R.indexOf(r)];return d>=15?100*s.series[p][R.indexOf(r)]/d:null;};
 let vmax=0;for(let p=0;p<P.length;p++)for(const r of R){const v=share(p,r);if(v!=null)vmax=Math.max(vmax,v);}
 const step=[0.5,1,2,2.5,5,10,20,25].find(t=>t*4>=vmax*1.05)||25, nice=step*4, X=p=>x0+(x1-x0)*p/(P.length-1), Y=v=>y1-(y1-y0)*v/nice;
 let o=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Share of History PhDs citing, by period and region"><g class="grid">`;
 for(let k=0;k<=4;k++){const v=nice*k/4;o+=`<line x1="${x0}" x2="${x1}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tick" x="${x0-8}" y="${Y(v)+4}" text-anchor="end">${+v.toFixed(1)}%</text>`;}
 o+='</g>';P.forEach((p,i)=>{o+=`<text class="tick" x="${X(i)}" y="${H-16}" text-anchor="middle">${p}</text>`;});
 for(const r of R){let path='',pen=false;for(let p=0;p<P.length;p++){const v=share(p,r);if(v==null){pen=false;continue;}path+=(pen?'L':'M')+X(p)+' '+Y(v)+' ';pen=true;}
  if(path)o+=`<path class="line s-${r}" d="${path}"/>`;
  for(let p=0;p<P.length;p++){const v=share(p,r);if(v==null)continue;const c=s.series[p][R.indexOf(r)],d=DATA.denominators[p][R.indexOf(r)];
   o+=`<circle class="pt s-${r}" cx="${X(p)}" cy="${Y(v)}" r="4.5" data-tip="${esc(NAMES[r])}, ${P[p]}: ${v.toFixed(1)}% (${c} of ${d} History PhDs)"/>`;}}
 return o+'</svg>';}
function fields(s){const F=s.fields,W=520,H=330,x0=36,x1=510,y0=12,y1=290,cols=P.map((p,i)=>i).filter(i=>F.placed[i]>=5);
 const totPlaced=F.placed.reduce((a,b)=>a+b,0);
 let o=`<div class="fleg">${F.fams.map((f,k)=>`<span><i style="background:var(--f${k})"></i><b>${esc(FAM[f].name)}</b> <small>${esc(FAM[f].terms)}</small></span>`).join('')}<span><i style="background:var(--f5)"></i>Other families</span></div>`;
 if(!cols.length)return o+'<p class="note">Too few placed citing PhDs to show fields.</p>';
 const bw=Math.min(52,(x1-x0)/cols.length-10),X=k=>x0+(x1-x0)*(k+0.5)/cols.length-bw/2,Y=v=>y1-(y1-y0)*v/100;
 o+=`<svg viewBox="0 0 ${W} ${H+24}" role="img" aria-label="Fields of the PhDs citing the source, by period">`;
 for(const v of [0,25,50,75,100])o+=`<line x1="${x0}" x2="${x1}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text class="tick" x="${x0-6}" y="${Y(v)+4}" text-anchor="end">${v}%</text>`;
 cols.forEach((p,k)=>{let acc=0;const sh=F.shares[p],other=Math.max(0,100-sh.reduce((a,b)=>a+(b||0),0));
  [...sh,other].forEach((v,j)=>{if(!v)return;const fam=j<F.fams.length?FAM[F.fams[j]]:null,base=fam?BASE[p][F.fams[j]]:null;
   const tipT=fam?`${fam.name} (${fam.terms}), ${P[p]}: ${v}% of the citing PhDs' field mix; ${base}% of all History PhDs`:`Other families, ${P[p]}: ${v}%`;
   o+=`<rect class="seg" x="${X(k)}" y="${Y(acc+v)}" width="${bw}" height="${(Y(acc)-Y(acc+v)).toFixed(1)}" fill="var(--f${j})" data-tip="${esc(tipT)}"/>`;
   if(v>=12)o+=`<text class="segt" x="${X(k)+bw/2}" y="${(Y(acc+v/2)+4).toFixed(1)}" text-anchor="middle">${v}</text>`;acc+=v;});
  o+=`<text class="tick" x="${X(k)+bw/2}" y="${H+4}" text-anchor="middle">${P[p].replace('before ','<')}</text><text class="tick" x="${X(k)+bw/2}" y="${H+18}" text-anchor="middle">n=${F.placed[p]}</text>`;});
 return o+`</svg><p class="note" style="font-size:12.5px">${totPlaced} of ${s.n} citing PhDs are placed by the family model; periods with fewer than 5 are left out.</p>`;}
function heat(s){const ramp=v=>v==null?'var(--seq-0)':`var(--seq-${Math.min(7,Math.max(1,Math.ceil(v/7)))})`;
 let o='<table class="heat"><thead><tr><th></th>'+P.map(p=>`<th>${p.replace('before ','<')}</th>`).join('')+'</tr></thead><tbody>';
 for(const r of s.rows){o+=`<tr><td class="l" title="${esc(full(r[0]))}">${esc(lab(r[0]))}</td>`;
  r[2].forEach((v,p)=>{const thin=s.n_period[p]<10;o+=`<td class="c${thin?' thin':''}" style="background:${ramp(v)};color:${v!=null&&v>=21?'var(--surface-1)':'var(--text-primary)'}" data-tip="${esc(lab(r[0]))}, ${P[p]}: ${v==null?'no citing PhDs':v+'% of '+s.n_period[p]+' PhDs citing the source'}">${v?Math.round(v):''}</td>`;});
  o+='</tr>';}
 return o+'</tbody></table>';}
function regions(s){let o='<div class="regions">';
 for(const r of ['CA','US','EUROPE']){const list=s.regional[r];o+=`<div><h3>${NAMES[r]} <span class="kind">(${s.n_region[r]||0} citing PhDs)</span></h3>`;
  if(!list){o+='<p class="note">Fewer than 10 citing PhDs.</p></div>';continue;}
  const mx=Math.max(...list.map(x=>x[1]));
  for(const [x,v] of list)o+=`<div class="bar"><div class="t" title="${esc(full(x))}"><i class="s-${r}" style="width:${(100*v/mx).toFixed(0)}%;background:var(--series-${r==='CA'?1:r==='US'?2:3})"></i>${esc(lab(x))}</div><div class="v">${v}%</div></div>`;
  o+='</div>';}
 return o+'</div>';}
let current=null,per=-1;
function render(s){current=s;per=-1;const tot=DATA.denominators.reduce((a,row)=>a+row.reduce((x,y)=>x+y,0),0);
 const person=isPerson(s.id);
 view.innerHTML=`<div class="head"><h2 style="margin:8px 0 0">${esc(lab(s.id))}</h2><span class="kind">${person?'Person (as first author)':esc(full(s.id))}</span></div>
 <div class="tiles"><div class="tile"><div class="v">${s.n.toLocaleString()}</div><div class="k">History PhDs citing (${(100*s.n/tot).toFixed(1)}%)</div></div>
 ${['CA','US','EUROPE'].map(r=>`<div class="tile"><div class="v">${s.n_region[r]||0}</div><div class="k">in ${NAMES[r]}</div></div>`).join('')}</div>
 <h2>Citations over time</h2><p class="note">Share of each region's History PhDs citing ${esc(lab(s.id))}, by period of the degree.</p>
 <div class="legend">${R.map(r=>`<span class="${r}">${NAMES[r]}</span>`).join('')}</div>${lineChart(s)}
 <div class="two"><div><h2>Who cites ${person?'them':'it'}, by field</h2><p class="note">The citation families (TF-IDF) of the PhDs citing ${esc(lab(s.id))}, period by period: how the communities citing it shift. Hover for each family's share of all History PhDs.</p>
 ${fields(s)}</div>
 <div><h2>Company over time</h2><p class="note">Of the PhDs citing ${esc(lab(s.id))} in each period, the % also citing each companion.</p>${heat(s)}</div></div>
 <h2>Company by region</h2><p class="note">Of the PhDs citing ${esc(lab(s.id))} in each region, the % also citing each companion.</p>${regions(s)}`;
}
view.addEventListener('mousemove',e=>{const t=e.target.closest('[data-tip]');if(t)showTip(e,esc(t.dataset.tip));else hide();});
view.addEventListener('mouseleave',hide);
const start=decodeURIComponent(location.hash.slice(1));
const first=byKey.get(start)||DATA.sources.filter(s=>isPerson(s.id)&&/cronon/i.test(lab(s.id))).sort((a,b)=>b.n-a.n)[0]||DATA.sources[0];
pick(first.id);
})();
</script></main></body></html>
"""

if __name__ == '__main__':
    main()
