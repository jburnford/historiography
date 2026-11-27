#!/usr/bin/env python3
"""Works grounded to each place, as one self-contained HTML map (no outside requests).

Areas are shaded (countries; states/provinces of nine large countries and the four UK nations), everything
else is a circle (settlements, physical features, structures, smaller administrative units) and places that have
neither a boundary here nor a sensible point (regions, former states) are a ranked list, drawn as circles only on
request. Counts are works tagged directly to the place (build/graph/place.parquet, `works`).

Inputs: build/graph/place.parquet, data/graph/places/place-coordinates.csv.gz (Wikidata P625 by exact QID) and,
in build/place-map/vendor/, Leaflet 1.9.4 and Natural Earth 1:50m outlines (public domain): ne50.geojson
(admin 0 countries), ne50_admin1.geojson (states/provinces), ne50_units.geojson (map units, for the UK nations).

  python3 scripts/place_works_map.py            # -> build/place-map/place-map.html
"""
import json
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / 'build/place-map/vendor'
OUT = ROOT / 'build/place-map/place-map.html'
UK = {'England', 'Scotland', 'Wales', 'Northern Ireland'}


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 2), round(c[1], 2)]
    out = [rnd(x) for x in c]
    if out and isinstance(out[0][0], (int, float)):
        d = [out[0]]
        for p in out[1:]:
            if p != d[-1]:
                d.append(p)
        out = d
    return out


def feat(f, qid, parent=None):
    p = {'q': qid}
    if parent:
        p['c'] = parent
    return {'type': 'Feature', 'properties': p,
            'geometry': {'type': f['geometry']['type'], 'coordinates': rnd(f['geometry']['coordinates'])}}


def main():
    c = duckdb.connect()
    P = {r[0]: r[1:] for r in c.execute(
        f"SELECT qid, label, kind, works, works_lc, works_title FROM '{ROOT}/build/graph/place.parquet' "
        "WHERE works > 0 AND qid IS NOT NULL").fetchall()}
    XY = {r[0]: (round(r[1], 3), round(r[2], 3)) for r in c.execute(
        f"SELECT qid, lat, lon FROM read_csv('{ROOT}/data/graph/places/place-coordinates.csv.gz')").fetchall()}
    by_name = {}
    for q, v in P.items():
        if v[1] == 'administrative unit':
            by_name.setdefault(v[0], []).append(q)

    countries, cq = [], {}
    for f in json.load(open(V / 'ne50.geojson'))['features']:
        q = f['properties'].get('WIKIDATAID')
        q = q if q in P else None
        countries.append(feat(f, q))
        cq[f['properties']['ADMIN']] = q
    subs, unmatched = [], 0

    def sub(f, name, q, admin):
        nonlocal unmatched
        if q not in P or P[q][1] not in ('administrative unit', 'country'):
            # Natural Earth carries some wrong ids (British Columbia): fall back to a unique exact name
            cand = by_name.get(name, [])
            q = cand[0] if len(cand) == 1 else None
        unmatched += q is None
        subs.append(feat(f, q, cq.get(admin)))

    for f in json.load(open(V / 'ne50_admin1.geojson'))['features']:
        p = f['properties']
        sub(f, p.get('name'), p.get('wikidataid'), p.get('admin'))
    for f in json.load(open(V / 'ne50_units.geojson'))['features']:
        p = f['properties']
        if p['ADMIN'] == 'United Kingdom' and p['GEOUNIT'] in UK:
            sub(f, p['GEOUNIT'], p.get('WIKIDATAID'), 'United Kingdom')

    area = {f['properties']['q'] for f in countries + subs if f['properties']['q']}
    info = {q: [P[q][0], P[q][1], P[q][2], P[q][3], P[q][4]] for q in area}
    pts, nolist, nocoord = [], [], [0, 0]
    for q, (label, kind, w, wl, wt) in sorted(P.items(), key=lambda kv: -kv[1][2]):
        if q in area:
            continue
        if kind in ('region', 'historical polity'):
            nolist.append([label, kind, w, q])
        if q in XY:
            pts.append([XY[q][0], XY[q][1], label, kind, w, wl, wt, q])
        else:
            nocoord[0] += 1
            nocoord[1] += w
    stats = dict(areas=len(area), sub_features=len(subs), sub_unmatched=unmatched, points=len(pts),
                 no_coordinates=nocoord, regions_listed=len(nolist))
    print(json.dumps(stats))

    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    html = (TEMPLATE.replace('__CSS__', (V / 'leaflet.css').read_text())
            .replace('__LEAFLET__', (V / 'leaflet.js').read_text().replace('</script>', '<\\/script>'))
            .replace('__COUNTRIES__', js({'type': 'FeatureCollection', 'features': countries}))
            .replace('__SUBS__', js({'type': 'FeatureCollection', 'features': subs}))
            .replace('__INFO__', js(info)).replace('__PTS__', js(pts)).replace('__LIST__', js(nolist[:400]))
            .replace('__MISS__', f'{nocoord[0]:,} places ({nocoord[1]:,} work tags) have no coordinates in Wikidata.')
            .replace('__DATE__', date.today().isoformat()))
    OUT.write_text(html)
    print(OUT, f'{OUT.stat().st_size:,} bytes')


TEMPLATE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Works grounded to each place</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>__CSS__</style>
<style>
html,body{margin:0;height:100%;font:14px/1.4 system-ui,sans-serif;color:#222}
#map{position:absolute;inset:0;background:#dbe7ee}
#panel{position:absolute;z-index:1000;top:10px;right:10px;bottom:10px;overflow:auto;background:#fff;padding:10px 12px;border-radius:6px;box-shadow:0 1px 5px rgba(0,0,0,.35);width:270px;box-sizing:border-box}
#panel h1{font-size:15px;margin:0 0 6px}#panel h2{font-size:13px;margin:10px 0 3px}
#panel label{display:block;margin:2px 0;cursor:pointer}
.sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
.note{color:#555;font-size:12px;margin-top:8px}
input[type=range]{width:100%}
#legend span{display:inline-block;height:10px;width:28px}#legend div{font-size:11px;color:#555;display:flex;justify-content:space-between;width:196px}
#list{font-size:12px;margin:0;padding:0;list-style:none}#list li{display:flex;justify-content:space-between;gap:6px;border-bottom:1px solid #eee;padding:1px 0}
#list li span:last-child{font-variant-numeric:tabular-nums;color:#444}
</style></head><body><div id="map"></div>
<div id="panel"><h1>Works grounded to each place</h1>
<h2>Shaded areas</h2>
<label><input type="radio" name="mode" value="c" checked> Countries</label>
<label><input type="radio" name="mode" value="s"> States, provinces and UK nations<br><span class="note" style="margin-left:20px">(AU, BR, CA, CN, IN, ID, RU, ZA, US, UK; other countries stay whole)</span></label>
<div id="legend" style="margin-top:6px"></div>
<h2>Circles</h2><div id="kinds"></div>
<div style="margin-top:8px">At least <b id="minv">1</b> works<input id="min" type="range" min="0" max="11" value="0" step="1"></div>
<div id="count" style="margin-top:4px"></div>
<h2>Regions and former states (no boundary drawn)</h2><ul id="list"></ul>
<div class="note">Counts are works tagged directly to the place (LC subject headings and title readings); a country's count does not include works tagged to places inside it. Circle area is proportional to the count. __MISS__ Outlines: Natural Earth (public domain). Snapshot __DATE__.</div></div>
<script>__LEAFLET__</script>
<script>
const COUNTRIES=__COUNTRIES__;
const SUBS=__SUBS__;
const INFO=__INFO__;
const D=__PTS__;
const LIST=__LIST__;
const COL={'administrative unit':'#c98a1b','settlement':'#1f77b4','physical feature':'#1a8f8f','structure':'#444','other':'#888','historical polity':'#2e8b57','region':'#7a5ba8','country':'#b0452f'};
const OFF={'historical polity':1,'region':1};
const RAMP=['#fff7ec','#fee8c8','#fdd49e','#fdbb84','#fc8d59','#ef6548','#d7301f','#990000'], BRK=[1,10,30,100,300,1000,3000,10000];
function shade(w){if(!w)return '#f4f4f1';let i=0;while(i<BRK.length-1&&w>=BRK[i+1])i++;return RAMP[i]}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function wd(q){return '<a target="_blank" rel="noopener" href="https://www.wikidata.org/wiki/'+q+'">'+q+'</a>'}
function pop(q,parent){const i=INFO[q];if(!i)return 'No works tagged directly to this area';
 let h='<b>'+esc(i[0])+'</b><br>'+i[1]+'<br>'+i[2].toLocaleString()+' works ('+i[3].toLocaleString()+' by LC heading, '+i[4].toLocaleString()+' by title)<br>'+wd(q);
 if(parent&&INFO[parent])h+='<br><span style="color:#555">'+esc(INFO[parent][0])+' as a whole: '+INFO[parent][2].toLocaleString()+' works</span>';return h}
document.getElementById('legend').innerHTML=RAMP.map(c=>'<span style="background:'+c+'"></span>').join('')+'<div>'+['1','10','30','100','300','1k','3k','10k+'].map(x=>'<i style="font-style:normal;width:28px">'+x+'</i>').join('')+'</div>';
const map=L.map('map',{preferCanvas:true,worldCopyJump:true,maxZoom:9}).setView([35,-20],2);
map.createPane('land').style.zIndex=200;map.createPane('subs').style.zIndex=210;
const svg=L.svg({pane:'land'}), svg2=L.svg({pane:'subs'});
const sty=q=>({color:'#8a9399',weight:.6,fillColor:shade(INFO[q]&&INFO[q][2]),fillOpacity:1});
const cLayer=L.geoJSON(COUNTRIES,{pane:'land',renderer:svg,style:f=>sty(f.properties.q),onEachFeature:(f,l)=>l.bindPopup(()=>pop(f.properties.q))}).addTo(map);
const sLayer=L.geoJSON(SUBS,{pane:'subs',renderer:svg2,style:f=>sty(f.properties.q),onEachFeature:(f,l)=>l.bindPopup(()=>pop(f.properties.q,f.properties.c))});
document.querySelectorAll('input[name=mode]').forEach(r=>r.onchange=()=>{if(r.checked){r.value=='s'?sLayer.addTo(map):map.removeLayer(sLayer)}});
const layer=L.layerGroup().addTo(map), on={}, cnt={};
const STEPS=[1,2,5,10,20,50,100,200,500,1000,2000,5000];
D.forEach(r=>cnt[r[3]]=(cnt[r[3]]||0)+1);
const kd=document.getElementById('kinds');
Object.keys(COL).filter(k=>cnt[k]).forEach(k=>{on[k]=!OFF[k];const l=document.createElement('label');
 l.innerHTML='<input type="checkbox"'+(on[k]?' checked':'')+'> <span class="sw" style="background:'+COL[k]+'"></span>'+k+' ('+cnt[k].toLocaleString()+')';
 l.firstChild.onchange=e=>{on[k]=e.target.checked;draw()};kd.appendChild(l)});
const canvas=L.canvas({pane:'markerPane'});
function draw(){layer.clearLayers();const m=STEPS[+document.getElementById('min').value];document.getElementById('minv').textContent=m.toLocaleString();
 let n=0,w=0;for(const r of D){if(r[4]<m)break;if(!on[r[3]])continue;n++;w+=r[4];
  L.circleMarker([r[0],r[1]],{renderer:canvas,radius:Math.max(2.5,Math.sqrt(r[4])*0.35),color:COL[r[3]]||'#999',weight:1,fillOpacity:.45})
   .bindPopup('<b>'+esc(r[2])+'</b><br>'+r[3]+'<br>'+r[4].toLocaleString()+' works ('+r[5].toLocaleString()+' by LC heading, '+r[6].toLocaleString()+' by title)<br>'+wd(r[7])).addTo(layer)}
 document.getElementById('count').textContent=n.toLocaleString()+' circles, '+w.toLocaleString()+' work tags';}
document.getElementById('min').oninput=draw;draw();
document.getElementById('list').innerHTML=LIST.slice(0,60).map(r=>'<li><span>'+esc(r[0])+'</span><span>'+r[2].toLocaleString()+'</span></li>').join('');
</script></body></html>'''

if __name__ == '__main__':
    main()
