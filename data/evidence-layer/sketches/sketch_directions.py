# Sketch generator (design exploration, 2026-09-27): three landing directions from rough real data.
# Run from the repo root: python3 data/evidence-layer/sketches/sketch_directions.py <outdir>
import json, csv, re, collections, html, sys
S=sys.argv[1]
g=json.load(open('historiography-1920-2000.json')); nodes={n['id']:n for n in g['nodes'] if n.get('entry_kind')=='group'}
F={
 'Social history':(['social','marx','labourhistory','historyworkshop','demography','urbanhistory','micro','newleft','durkheim','women','black','identity','racial_formation','intersectionality'],['none:rural_agrarian','none:local_regional_history','none:childhood_youth','none:ethnic_history','none:jewish_studies']),
 'Cultural & intellectual history':(['culture','oldculture','intellectualhistory','context','conceptual','language','memory','culturalstudies','anthropology','practice','psychohistory','frankfurt','saussure','gender','queer','biography','lifetradition','consumption'],['none:religious_history','none:art_history','none:history_of_knowledge','none:history_of_emotions','none:book_library_history']),
 'Annales':(['annales'],[]),
 'Political, national & international':(['political','nationalismstudies','nationaltradition','progressive','holocaust'],['none:diplomatic_international','none:legal_history','none:socialism_left_politics','none:human_rights','none:peace_history']),
 'War & the military':(['military','wartradition'],['none:genocide_studies']),
 'Economy & social science history':(['economic','historicalecon','economictheory','quant','historicalsociology','bielefeld','modern','dependency','weber','spatialhistory','karl'],['none:social_science_history','none:business_history']),
 'Indigenous histories':(['indigenous','ethnohistory'],[]),
 'Empire, colonialism & the global':(['anticolonial','post','subaltern','africanhist','atlantic','global'],['none:imperial_colonial_history','none:migration_history','none:transnational_history','none:slavery_studies','none:maritime_ocean_history']),
 'Science, technology & medicine':(['science','ssk','sts','technology','medicalhistory','epistemology'],['none:disability_history']),
 'Environment':(['environment','geography'],['none:animal_history']),
 'Theory & method':(['philhistory','historicism','truthdebate','ranke','publichistory','oral','digital_history','web_history'],[]),
}
def year(n):
    m=re.search(r'(1[6-9]\d\d|20[0-2]\d)', n.get('date_label') or ''); return int(m.group(1)) if m else None
atlas={f:sorted(y for y in (year(nodes[e]) for e in es if e in nodes) if y) for f,(es,_) in F.items()}
jour=collections.defaultdict(lambda: collections.defaultdict(int))
tmap={t:f for f,(es,ns) in F.items() for t in es+ns}
for r in csv.DictReader(open('data/evidence-layer/generated/v16/series.csv')):
    if r['axis']!='theme' or not r['year'] or r['target'] not in tmap: continue
    y=int(r['year']); f=tmap[r['target']]
    if r['source']=='journal' and r['kind']=='research_proxy' and 1900<=y<=2026: jour[f][y//5*5]+=int(r['items'])
tot_j={f:sum(jour[f].values()) for f in F}; tot_a={f:len(atlas[f]) for f in F}; fams=list(F)
X0,X1,W=1880,2026,500; x=lambda y:240+max(0,(y-X0))/(X1-X0)*W
gmax=max(v for d in jour.values() for v in d.values())
rows=[]
for i,f in enumerate(fams):
    y0=30+i*34
    bars=''.join(f'<rect x="{x(b):.1f}" y="{y0+26-18*v/gmax:.1f}" width="{W/((X1-X0)/5)-1:.1f}" height="{18*v/gmax:.1f}" class="rec"/>' for b,v in jour[f].items())
    dots=''.join(f'<circle cx="{x(y):.1f}" cy="{y0+5}" r="3.2" class="atl"/>' for y in atlas[f])
    rows.append(f'<text x="232" y="{y0+18}" text-anchor="end" class="lab">{html.escape(f)}</text><line x1="240" x2="{240+W}" y1="{y0+26.5}" y2="{y0+26.5}" class="base"/>{bars}{dots}')
H=30+len(fams)*34
axis=''.join(f'<text x="{x(y):.0f}" y="{H+14}" text-anchor="middle" class="tick">{y}</text><line x1="{x(y):.0f}" x2="{x(y):.0f}" y1="24" y2="{H}" class="grid"/>' for y in range(1900,2030,20))
A=f'<svg viewBox="0 0 750 {H+30}" class="chart">{axis}{"".join(rows)}<line x1="{x(2000)}" x2="{x(2000)}" y1="20" y2="{H}" class="wall"/></svg>'
cards=[]
for f in fams:
    bb=''.join(f'<rect x="{(b-1950)/5*9:.0f}" y="{40-36*jour[f].get(b,0)/gmax:.1f}" width="8" height="{36*jour[f].get(b,0)/gmax:.1f}" class="rec"/>' for b in range(1950,2030,5))
    ticks=''.join(f'<line x1="{(y-1880)/146*144:.1f}" x2="{(y-1880)/146*144:.1f}" y1="0" y2="10" class="atlt"/>' for y in atlas[f])
    cards.append(f'<div class="card"><h4>{html.escape(f)}</h4><p class="k"><b>{tot_a[f]}</b> atlas entries</p><svg viewBox="0 0 146 12" class="mini">{ticks}</svg><p class="k"><b>{tot_j[f]:,}</b> research articles 1950–2026</p><svg viewBox="0 0 146 42" class="mini">{bb}</svg></div>')
B='<div class="grid5">'+''.join(cards)+'</div>'
recent={f:sum(v for b,v in jour[f].items() if b>=2000) for f in fams}; ra=sum(recent.values()); aa=sum(tot_a.values())
order=sorted(fams,key=lambda f:-recent[f]/ra)
crow=''.join(f'<text x="200" y="{24+i*26}" text-anchor="end" class="lab">{html.escape(f)}</text><rect x="210" y="{12+i*26}" width="{tot_a[f]/aa*900:.0f}" height="8" class="atl"/><rect x="210" y="{21+i*26}" width="{recent[f]/ra*900:.0f}" height="8" class="rec"/><text x="{214+max(tot_a[f]/aa,recent[f]/ra)*900:.0f}" y="{24+i*26}" class="tick">{tot_a[f]/aa:.0%} of atlas · {recent[f]/ra:.0%} of record</text>' for i,f in enumerate(order))
C=f'<svg viewBox="0 0 750 {20+len(fams)*26}" class="chart">{crow}</svg>'
page=f'''<!doctype html><html><head><meta charset="utf-8"><title>Landing layouts: three directions</title><style>
body{{font:13px/1.5 system-ui,sans-serif;background:#f6f4ec;color:#1f2a24;margin:0;padding:22px 30px;max-width:1100px}}
h1{{font:26px Georgia,serif;margin:0 0 4px}} h2{{font:20px Georgia,serif;margin:30px 0 4px}} .note{{color:#5d6a61;max-width:860px}}
.chart{{width:100%;max-width:900px;background:#fbfaf4;border:1px solid #d9dccf;border-radius:6px}}
.lab{{font-size:11px;fill:#1f2a24}} .tick{{font-size:9px;fill:#6b756d}} .grid{{stroke:#e6e7dd}} .base{{stroke:#cfd4c6}} .wall{{stroke:#9aa39a;stroke-dasharray:3 3}}
.rec{{fill:#2e5e4e}} .atl{{fill:#c07a3e}} .atlt{{stroke:#c07a3e;stroke-width:1.6}}
.grid5{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;max-width:900px}} .card{{background:#fbfaf4;border:1px solid #d9dccf;border-radius:6px;padding:10px}}
.card h4{{font:14px Georgia,serif;margin:0 0 6px;min-height:36px}} .k{{margin:4px 0 2px;font-size:11px}} .mini{{width:100%;display:block}}
</style></head><body><h1>Three directions for the landing view</h1>
<p class="note">Sketches with rough real data: eleven draft families, Annales on its own. <b style="color:#c07a3e">Orange = the atlas</b> (each entry at the first year in its date label). <b style="color:#2e5e4e">Green = the record</b> (journal research articles per five years; journal-level tags, overlapping counts). For comparing layouts only; numbers are not final.</p>
<h2>A · Paired rows on one time axis</h2><p class="note">Each family is one row: atlas entries as dots where the atlas dates them, the record's volume as bars beneath, on one 1880–2026 axis. Keeps the site's single time axis. The gap shows as dots bunched before 2000 above green that keeps growing after it. Click a row to open its fields.</p>{A}
<h2>B · Small multiples, one card per family</h2><p class="note">Eleven cards on the same scales. Easier to scan and to read on a phone, but timing is harder to compare across families. Click a card to open the family.</p>{B}
<h2>C · Share of attention: atlas vs record</h2><p class="note">Each family's share of atlas entries (orange) against its share of research articles since 2000 (green). The quickest statement of the gap, but it drops time, so it would sit above A or B as a headline rather than replace them.</p>{C}
</body></html>'''
open(S+'/landing-directions.html','w').write(page)
print({f:(tot_a[f],tot_j[f]) for f in fams})
