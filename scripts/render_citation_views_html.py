#!/usr/bin/env python3
"""Render views.json (dissertation_citation_views.py) as one self-contained HTML page:
fields (co-citation map + engagement over time), supervision, and universities.

``--country CC`` renders a country sub-graph's page (``summary/countries/<CC>/``, with the
atlas section when its crosswalk exists); without it, the main graph's (``summary/``).
See ``dissertation_scope.py``."""
import argparse
import json
from pathlib import Path
import re

from dissertation_scope import add_scope_argument, audit_dir, scope_label, summary_dir

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__WHO__History PhDs: fields, supervision, universities</title>
<style>
.viz-root { color-scheme: light;
  --surface-1:#fcfcfb; --page:#f9f9f7; --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10); --series-1:#2a78d6; --thin:#b9b8b1; --node:#a9a8a1; --edge:#d6d5ce;
  --seq-1:#cde2fb; --seq-2:#9ec5f4; --seq-3:#6da7ec; --seq-4:#3987e5; --seq-5:#256abf; --seq-6:#184f95; --seq-7:#0d366b; }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) .viz-root { color-scheme: dark;
  --surface-1:#1a1a19; --page:#0d0d0d; --text-primary:#ffffff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --series-1:#3987e5; --thin:#5a5955; --node:#5f5e59; --edge:#2e2e2b;
  --seq-1:#0d366b; --seq-2:#104281; --seq-3:#184f95; --seq-4:#1c5cab; --seq-5:#2a78d6; --seq-6:#5598e7; --seq-7:#9ec5f4; } }
:root[data-theme="dark"] .viz-root { color-scheme: dark;
  --surface-1:#1a1a19; --page:#0d0d0d; --text-primary:#ffffff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --series-1:#3987e5; --thin:#5a5955; --node:#5f5e59; --edge:#2e2e2b;
  --seq-1:#0d366b; --seq-2:#104281; --seq-3:#184f95; --seq-4:#1c5cab; --seq-5:#2a78d6; --seq-6:#5598e7; --seq-7:#9ec5f4; }
body { margin:0; }
.viz-root { background:var(--page); color:var(--text-primary); font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; padding:24px 28px 56px; min-height:100vh; }
h1 { font-size:22px; font-weight:600; margin:0 0 6px; } h2 { font-size:18px; font-weight:600; margin:36px 0 6px; } h3 { font-size:15px; font-weight:600; margin:22px 0 6px; }
p.lede, p.note { color:var(--text-secondary); max-width:960px; margin:4px 0; } p.note { font-size:12.5px; }
nav { display:flex; gap:8px; margin:14px 0 4px; flex-wrap:wrap; } nav a { color:var(--text-primary); text-decoration:none; border:1px solid var(--border); background:var(--surface-1); border-radius:999px; padding:4px 12px; font-size:13px; }
figure { margin:0; background:var(--surface-1); border:1px solid var(--border); border-radius:10px; padding:12px; position:relative; }
figcaption { font-size:13px; font-weight:600; margin:0 0 2px; } figcaption .sub { display:block; font-weight:400; color:var(--text-secondary); font-size:12px; }
svg { display:block; width:100%; height:auto; overflow:visible; }
.tick { fill:var(--muted); font-size:10px; font-variant-numeric:tabular-nums; } .lab { fill:var(--text-secondary); font-size:11px; } .end { fill:var(--text-secondary); font-size:11px; font-variant-numeric:tabular-nums; }
.flabel { fill:var(--text-secondary); font-size:11px; font-weight:600; paint-order:stroke; stroke:var(--surface-1); stroke-width:3px; cursor:pointer; }
.flabel.on { fill:var(--text-primary); }
.mapwrap { display:grid; grid-template-columns:minmax(0,2fr) minmax(280px,1fr); gap:14px; align-items:start; }
@media (max-width: 1000px) { .mapwrap { grid-template-columns:1fr; } }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; } .chips button { font:inherit; font-size:12px; color:var(--text-primary); background:var(--surface-1); border:1px solid var(--border); border-radius:999px; padding:3px 10px; cursor:pointer; }
.chips button[aria-pressed="true"] { border-color:var(--series-1); box-shadow:inset 0 0 0 1px var(--series-1); }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(232px,1fr)); gap:12px; } .grid figcaption { min-height:4.6em; }
.tiles { display:flex; gap:14px; flex-wrap:wrap; } .tile { background:var(--surface-1); border:1px solid var(--border); border-radius:10px; padding:14px 18px; min-width:220px; }
.tile .label { color:var(--text-secondary); font-size:13px; } .tile .value { font-size:40px; font-weight:600; line-height:1.1; } .tile .ctx { color:var(--text-secondary); font-size:12px; }
table { border-collapse:collapse; font-size:12.5px; background:var(--surface-1); } th, td { border-bottom:1px solid var(--grid); padding:4px 8px; text-align:left; vertical-align:top; }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
.detail ol { margin:4px 0 8px 18px; padding:0; } .detail li { margin:2px 0; font-size:12.5px; } .detail .muted { color:var(--text-secondary); }
.tip { position:fixed; pointer-events:none; background:var(--surface-1); border:1px solid var(--border); border-radius:8px; padding:8px 10px; font-size:12px; box-shadow:0 4px 16px rgba(0,0,0,.12); display:none; z-index:10; max-width:340px; }
.tip strong { font-size:14px; display:block; } .tip .k { color:var(--text-secondary); }
.uni { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; } .uni figure ol { margin:4px 0 4px 18px; padding:0; font-size:12.5px; } .uni .muted { color:var(--text-secondary); font-size:12px; }
.heat td.c { text-align:center; font-size:11px; font-variant-numeric:tabular-nums; min-width:34px; padding:4px 3px; } .heat th.r { white-space:nowrap; font-weight:500; } .heat th.c { font-size:11px; font-weight:500; text-align:center; }
.key { display:flex; gap:4px; align-items:center; color:var(--text-secondary); font-size:12px; margin:6px 0; } .key span.sw { width:22px; height:10px; display:inline-block; }
</style>
</head>
<body>
<div class="viz-root">
<h1>__WHO__History PhDs: fields, supervision and universities</h1>
<p class="lede">Built from the bibliographies of __N__ History doctoral dissertations (strict History PhDs with a parsed
bibliography). Every measure is a share of dissertations, so corpus growth and department size do not read as influence.</p>
<nav><a href="#fields">1 · Fields</a><a href="#supervision">2 · Supervision</a><a href="#universities">3 · Universities</a><a href="#practice">4 · Practice</a><!--atlas--><a href="#atlas">5 · The atlas</a><!--/atlas--></nav>

<h2 id="fields">1 · Fields: what is cited together</h2>
<p class="note">Each dot is a work cited by at least __MINC__ History PhDs (__WORKS__ works; corporate authors and works cited mainly
as primary sources excluded). Works close together are cited by the same dissertations. Fields are the consensus of 40
clustering runs: works stay in a field only if they fall together in at least 80% of runs (__CLUSTERED__ of __WORKS__ works).
Field names are provisional editorial labels. Select a field to see its works and people; click a dot to see a work's
co-citation neighbours and whether it bridges fields. Robustness grades come from re-clustering at other resolutions and
consensus thresholds (__ROBUSTNESS__).</p>
<div class="chips" id="fieldChips"></div>
<div class="mapwrap">
  <figure><figcaption>Co-citation map<span class="sub">Dot size: History PhDs citing the work. Thick lines: co-citation between fields (wider = stronger); thin lines: strongest links within a field.</span></figcaption><div id="map"></div></figure>
  <figure class="detail" id="detail"><figcaption>Select a field</figcaption><p class="note">Click a field name on the map or a chip above.</p></figure>
</div>
<h3>How fields change: share of each year's dissertations engaging the field</h3>
<p class="note">A dissertation engages a field when it cites at least three of its works. Centred three-year window, 95% band; grey = fewer than __MIN__ dissertations in the window.</p>
<div class="grid" id="fieldTrends"></div>

<h2 id="supervision">2 · Supervision: do students cite their supervisors?</h2>
<p class="note">__WITHSUP__ of the __N__ dissertations record a supervisor. Baseline: for supervisors with three or more students,
the share of other History PhDs at the same university, within five years of the supervisor's students, that cite the same person.</p>
<div class="tiles" id="tiles"></div>
<h3>By period</h3><p class="note">Bibliographies roughly tripled in length over the period, which raises every citation rate.</p>
<figure style="max-width:560px"><div id="period"></div></figure>
<h3>Supervisors with the most students: share of their students citing them, against same-university peers</h3>
<div class="key"><svg width="120" height="12"><circle cx="8" cy="6" r="4" fill="var(--node)"/><text x="16" y="10" class="lab">Peers</text><circle cx="66" cy="6" r="4" fill="var(--series-1)"/><text x="74" y="10" class="lab">Students</text></svg></div>
<figure><div id="dumbbell"></div></figure>
<h3>Supervision chains in the corpus</h3><p class="note">A supervisor whose own PhD is also in the corpus, with its supervisor.</p>
<div id="chains"></div>

<h2 id="universities">3 · Universities, 2010–2025</h2>
<p class="note">Same years for every university (__UNIS__ universities with at least 25 History PhDs in 2010–2025), so the comparison is not a period effect.</p>
<h3>Field engagement by university</h3><p class="note">Share of each university's dissertations engaging each field. Darker = higher share.</p>
<div id="heat" style="overflow-x:auto"></div>
<h3>What each department draws on more than others</h3>
<p class="note">Scholars cited by at least five of the university's dissertations, ranked by excess share (share here minus share at all other universities). Own faculty: people who supervise History PhDs there; students cite their supervisors, so they are listed separately.</p>
<div class="uni" id="uni"></div>
<h2 id="practice">4 · Practice: what bibliographies are built from</h2>
<p class="note">Share of each year's dissertations whose bibliography has a section of each kind, read from the dissertation's own
subheadings (__SECTIONED__ History PhDs with a subheaded bibliography). Headings follow local conventions, so read levels
cautiously and changes with more confidence. Centred three-year window, 95% band; grey = thin window.</p>
<div class="grid" id="methods"></div>

<!--atlas--><h2 id="atlas">5 · The atlas: what __WHO__History PhDs do with its canon</h2>
<p class="note">Atlas roster people matched to the citation graph by Wikidata QID or, where exactly one roster person shares a
surname and first name, by name (a candidate match). Evidence beside the atlas, not edits to it.</p>
<div class="tiles" id="atlasTiles"></div>
<h3>Most-cited scholars outside the atlas roster</h3>
<p class="note">For editorial review. Many belong to Canadian national historiography, outside the atlas's stated scope; others
are international (James C. Scott, Mariana Valverde) and bear on existing entries.</p>
<div id="gaps" style="overflow-x:auto"></div>
<h3>Fields and the atlas entries that name their people</h3>
<div id="fieldAtlas" style="overflow-x:auto"></div>
<!--/atlas-->
<div class="tip" id="tip" role="status"></div>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const V = JSON.parse(document.getElementById('data').textContent);
const NS = 'http://www.w3.org/2000/svg', tip = document.getElementById('tip');
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const [k, v] of Object.entries(a || {})) e.setAttribute(k, v); if (p) p.appendChild(e); return e; };
const h = (t, txt, p, cls) => { const e = document.createElement(t); if (txt != null) e.textContent = txt; if (cls) e.className = cls; if (p) p.appendChild(e); return e; };
const pct = v => v == null ? '–' : (+(100 * v).toFixed(v < 0.1 ? 1 : 0)) + '%';
const uniName = {alberta:'Alberta',calgary:'Calgary',carleton:'Carleton',concordia:'Concordia',dalhousie:'Dalhousie',guelph:'Guelph',laurier:'Laurier',laval:'Laval',manitoba:'Manitoba',mcgill:'McGill',mcmaster:'McMaster',memorial:'Memorial',montreal:'Montréal',ottawa:'Ottawa',queens:"Queen's",sfu:'SFU',sherbrooke:'Sherbrooke',toronto:'Toronto',unb:'UNB',uqam:'UQAM',usask:'Saskatchewan',uvic:'UVic',waterloo:'Waterloo',western:'Western',york:'York'};
function showTip(ev, lines) {
  tip.replaceChildren(); h('strong', lines[0], tip); for (const l of lines.slice(1)) h('div', l, tip, 'k');
  tip.style.display = 'block';
  tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8) + 'px'; tip.style.top = (ev.clientY + 14) + 'px';
}
const hideTip = () => { tip.style.display = 'none'; };
function hover(node, lines) {
  node.addEventListener('pointermove', ev => showTip(ev, lines()));
  node.addEventListener('focus', () => { const r = node.getBoundingClientRect(); showTip({clientX: r.right, clientY: r.top}, lines()); });
  node.addEventListener('pointerleave', hideTip); node.addEventListener('blur', hideTip);
}

// ---------- 1. Fields ----------
const F = V.fields, fields = F.fields;
const map = el('svg', {viewBox: '0 0 900 640', role: 'img', 'aria-label': 'Co-citation map of frequently cited works'}, document.getElementById('map'));
const X = x => 70 + x * 760, Y = y => 40 + y * 560;
const nodeById = Object.fromEntries(F.nodes.map(n => [n.id, n]));
const gEdges = el('g', {}, map), gNodes = el('g', {}, map), gLabels = el('g', {}, map);
for (const [a, b, w] of V.field_links) { const p = fields[a], q = fields[b]; el('line', {x1: X(p.cx), y1: Y(p.cy), x2: X(q.cx), y2: Y(q.cy), stroke: 'var(--edge)', 'stroke-width': 1 + 9 * w, 'stroke-linecap': 'round', opacity: 0.7}, gEdges); }
for (const [a, b] of F.edges) { const p = nodeById[a], q = nodeById[b]; el('line', {x1: X(p.x), y1: Y(p.y), x2: X(q.x), y2: Y(q.y), stroke: 'var(--edge)', 'stroke-width': 0.6}, gEdges); }
const circles = F.nodes.sort((a, b) => b.cited_by - a.cited_by).map(n => {
  const c = el('circle', {cx: X(n.x), cy: Y(n.y), r: 1.6 + Math.sqrt(n.cited_by) / 2.2, fill: 'var(--node)', stroke: 'var(--surface-1)', 'stroke-width': 1, tabindex: -1}, gNodes);
  hover(c, () => [n.title, `${n.author}${n.year ? ', ' + n.year : ''}`, `Cited by ${n.cited_by} History PhDs`, n.field == null ? 'Unclustered' : fields[n.field].label]);
  c.addEventListener('click', () => showWork(n));
  return [c, n];
});
const labelEls = fields.map(f => {
  const members = F.nodes.filter(n => n.field === f.id), top = Math.min(...members.map(n => Y(n.y)));
  const cx = X(f.cx), anchor = cx < 230 ? 'start' : cx > 670 ? 'end' : 'middle';
  const t = el('text', {x: anchor === 'start' ? Math.max(8, cx - 40) : anchor === 'end' ? Math.min(892, cx + 40) : cx, y: top - 8, 'text-anchor': anchor, class: 'flabel', tabindex: 0}, gLabels);
  t.textContent = f.label; t.addEventListener('click', () => select(f.id)); t.addEventListener('keydown', e => { if (e.key === 'Enter') select(f.id); });
  return t;
});
const chips = document.getElementById('fieldChips');
const ROB = V.robustness || {};
const grade = f => { const r = ROB[f.label]; if (!r) return ''; return r.mean >= 0.75 ? 'robust' : r.mean >= 0.5 ? 'moderate' : 'fragile'; };
const chipEls = fields.map(f => { const b = h('button', `${f.label} (${f.works})${grade(f) ? ' · ' + grade(f) : ''}`, chips); b.type = 'button'; b.setAttribute('aria-pressed', 'false'); b.addEventListener('click', () => select(f.id)); return b; });
let current = null;
function select(i) {
  current = current === i ? null : i;
  for (const [c, n] of circles) {
    const on = current == null || n.field === current;
    c.setAttribute('fill', current != null && n.field === current ? 'var(--series-1)' : 'var(--node)');
    c.setAttribute('opacity', on ? 1 : 0.25);
  }
  labelEls.forEach((t, j) => { t.classList.toggle('on', j === current); t.setAttribute('opacity', current == null || j === current ? 1 : 0.35); });
  chipEls.forEach((b, j) => b.setAttribute('aria-pressed', j === current));
  const d = document.getElementById('detail'); d.replaceChildren();
  if (current == null) { h('figcaption', 'Select a field', d); h('p', 'Click a field name on the map or a chip above.', d, 'note'); return; }
  const f = fields[current];
  const cap = h('figcaption', f.label, d); h('span', `${f.works} works · engaged by ${f.engaged} History PhDs${f.label_is_provisional ? ' · label auto-generated' : ' · provisional label'}`, cap, 'sub');
  const rob = ROB[f.label];
  if (rob) h('p', `Robustness: ${grade(f)} (mean Jaccard ${rob.mean} with the matching field when clustering resolution and consensus change; lowest ${rob.min}).`, d, 'note');
  h('div', 'Most cited works in the field', d, 'muted');
  const ol = h('ol', null, d); for (const w of f.top_works.slice(0, 8)) h('li', `${w.author.split(',')[0]}, ${w.title}${w.year ? ' (' + w.year + ')' : ''} · ${w.cited_by}`, ol);
  h('div', 'People cited by the dissertations that engage it (share within the field · times the corpus rate)', d, 'muted');
  const ol2 = h('ol', null, d); for (const p of f.people.slice(0, 12)) h('li', `${p.name} · ${pct(p.within)} · ×${p.lift}`, ol2);
}

const fieldName = i => i == null || i < 0 ? 'Unclustered' : fields[i].label;
function showWork(n) {
  const d = document.getElementById('detail'); d.replaceChildren();
  const cap = h('figcaption', n.title, d); h('span', `${n.author}${n.year ? ', ' + n.year : ''} · cited by ${n.cited_by} History PhDs · field: ${fieldName(n.field)}`, cap, 'sub');
  h('div', 'Where its co-citation links go (share of link strength)', d, 'muted');
  const ul = h('ol', null, d); for (const [f, v] of n.link_split) h('li', `${fieldName(f)} · ${pct(v)}`, ul);
  const own = (n.link_split.find(([f]) => f === n.field) || [null, 0])[1];
  if (n.field != null && own < 0.5) h('p', 'A bridge work: most of its co-citation links run outside its own field.', d, 'note');
  h('div', 'Most co-cited works', d, 'muted');
  const ol = h('ol', null, d);
  for (const [id, w] of n.neighbours) { const m = nodeById[id]; if (m) h('li', `${m.author.split(',')[0]}, ${m.title}${m.year ? ' (' + m.year + ')' : ''} · ${fieldName(m.field)} · cosine ${w}`, ol); }
}
function lineChart(fig, pts, o) {
  const W = 260, H = 116, L = 30, R = 34, T = 8, B = 20, Y0 = 1965, Y1 = 2025;
  const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': o.label}, fig);
  const x = y => L + (y - Y0) / (Y1 - Y0) * (W - L - R), y = v => T + (1 - Math.min(v, o.yMax) / o.yMax) * (H - T - B);
  for (const t of o.ticks) { el('line', {x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: 'var(--grid)'}, svg); el('text', {x: L - 4, y: y(t) + 3, 'text-anchor': 'end', class: 'tick'}, svg).textContent = (100 * t) + '%'; }
  for (const yr of [1970, 1990, 2010, Y1]) el('text', {x: x(yr), y: H - 5, 'text-anchor': 'middle', class: 'tick'}, svg).textContent = yr;
  const shown = pts.filter(p => p.share != null && p.year >= Y0);
  const segs = []; for (const p of shown) { const l = segs[segs.length - 1]; if (!l || l.thin !== p.thin) segs.push({thin: p.thin, pts: l ? [l.pts[l.pts.length - 1], p] : [p]}); else l.pts.push(p); }
  for (const s of segs) {
    const up = s.pts.map(p => `${x(p.year)},${y(p.hi)}`).join(' '), dn = s.pts.slice().reverse().map(p => `${x(p.year)},${y(p.lo)}`).join(' ');
    el('polygon', {points: up + ' ' + dn, fill: s.thin ? 'var(--thin)' : 'var(--series-1)', opacity: s.thin ? 0.07 : 0.12}, svg);
    el('polyline', {points: s.pts.map(p => `${x(p.year)},${y(p.share)}`).join(' '), fill: 'none', stroke: s.thin ? 'var(--thin)' : 'var(--series-1)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round'}, svg);
  }
  const e = shown[shown.length - 1];
  el('circle', {cx: x(e.year), cy: y(e.share), r: 4, fill: 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2}, svg);
  el('text', {x: x(e.year) + 7, y: y(e.share) + 4, class: 'end'}, svg).textContent = pct(e.share);
  const cross = el('line', {y1: T, y2: H - B, stroke: 'var(--axis)', visibility: 'hidden'}, svg);
  const hit = el('rect', {x: L, y: 0, width: W - L - R, height: H, fill: 'transparent', tabindex: 0}, svg);
  hit.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect(), yr = Y0 + ((ev.clientX - r.left) / r.width * W - L) / (W - L - R) * (Y1 - Y0);
    const p = shown.reduce((a, b) => Math.abs(b.year - yr) < Math.abs(a.year - yr) ? b : a);
    cross.setAttribute('x1', x(p.year)); cross.setAttribute('x2', x(p.year)); cross.setAttribute('visibility', 'visible');
    showTip(ev, [pct(p.share), `${p.year} · ${p.k} of ${p.n} dissertations`, `95% ${pct(p.lo)}–${pct(p.hi)}`].concat(p.thin ? ['Thin window: small sample'] : []));
  });
  hit.addEventListener('pointerleave', () => { hideTip(); cross.setAttribute('visibility', 'hidden'); });
}
const trends = document.getElementById('fieldTrends');
for (const f of fields) {
  const fig = h('figure', null, trends); const cap = h('figcaption', f.label, fig);
  h('span', f.people.slice(0, 3).map(p => p.name.split(',')[0]).join(' · '), cap, 'sub');
  fig.addEventListener('click', () => { select(f.id); document.getElementById('fields').scrollIntoView({behavior: 'smooth'}); });
  lineChart(fig, f.series, {yMax: 0.3, ticks: [0, 0.1, 0.2, 0.3], label: 'Engagement with ' + f.label});
}

// ---------- 2. Supervision ----------
const S = V.supervision;
const tiles = document.getElementById('tiles');
const tile = (label, value, ctx) => { const t = h('div', null, tiles, 'tile'); h('div', label, t, 'label'); h('div', value, t, 'value'); h('div', ctx, t, 'ctx'); };
tile('Students citing their supervisor', pct(S.cite_supervisor / S.with_supervisor), `${S.cite_supervisor} of ${S.with_supervisor} dissertations with a recorded supervisor`);
tile('Same-university peers citing that supervisor', pct(S.mean_peer_share), `mean over ${S.supervisors_3plus} supervisors with 3+ students`);
tile('Supervisors never cited by their students', String(S.never_cited), `of ${S.supervisors_3plus} with 3+ students`);
(function periodChart() {
  const W = 520, H = 150, L = 110, R = 50, rowH = 30;
  const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Share citing supervisor by period'}, document.getElementById('period'));
  const x = v => L + v * (W - L - R);
  S.by_period.forEach(([p, n, s], i) => {
    const y = 10 + i * rowH;
    el('text', {x: L - 8, y: y + 14, 'text-anchor': 'end', class: 'lab'}, svg).textContent = p;
    const bar = el('rect', {x: L, y: y + 4, width: x(s) - L, height: 16, rx: 4, fill: 'var(--series-1)', tabindex: 0}, svg);
    el('text', {x: x(s) + 6, y: y + 16, class: 'end'}, svg).textContent = pct(s);
    hover(bar, () => [pct(s), `${p} · ${n} dissertations with a supervisor`]);
  });
  el('line', {x1: L, x2: L, y1: 6, y2: H - 10, stroke: 'var(--axis)'}, svg);
})();
(function dumbbell() {
  const rows = S.supervisors_list.slice(0, 40), W = 900, rowH = 19, L = 260, R = 60, T = 22;
  const H = T + rows.length * rowH + 10;
  const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Supervisors: students citing vs peers'}, document.getElementById('dumbbell'));
  const x = v => L + v * (W - L - R);
  for (const t of [0, 0.25, 0.5, 0.75, 1]) { el('line', {x1: x(t), x2: x(t), y1: T - 6, y2: H - 6, stroke: 'var(--grid)'}, svg); el('text', {x: x(t), y: 12, 'text-anchor': 'middle', class: 'tick'}, svg).textContent = (100 * t) + '%'; }
  rows.forEach((r, i) => {
    const y = T + i * rowH + 6;
    el('text', {x: L - 10, y: y + 4, 'text-anchor': 'end', class: 'lab'}, svg).textContent = `${r.name} · ${uniName[r.institution] || r.institution} · ${r.students}`;
    el('line', {x1: x(r.peer_share), x2: x(r.share), y1: y, y2: y, stroke: 'var(--axis)', 'stroke-width': 2}, svg);
    el('circle', {cx: x(r.peer_share), cy: y, r: 4, fill: 'var(--node)', stroke: 'var(--surface-1)', 'stroke-width': 2}, svg);
    el('circle', {cx: x(r.share), cy: y, r: 4.5, fill: 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2}, svg);
    const hit = el('rect', {x: 0, y: y - rowH / 2, width: W, height: rowH, fill: 'transparent', tabindex: 0}, svg);
    hover(hit, () => [r.name, `${r.students_citing} of ${r.students} students cite them (${pct(r.share)})`, `Peers at ${uniName[r.institution] || r.institution}: ${pct(r.peer_share)} of ${r.peers}`, `Students' PhDs ${r.first_year}–${r.last_year}`]);
  });
})();
(function chains() {
  const t = h('table', null, document.getElementById('chains')); const hr = t.createTHead().insertRow();
  for (const c of ['Supervisor', 'Student (PhD)', 'Student cites supervisor', 'Student has since supervised']) h('th', c, hr);
  const b = t.createTBody();
  for (const c of S.chains.slice(0, 25)) {
    const r = b.insertRow(); r.insertCell().textContent = c.teacher;
    r.insertCell().textContent = `${c.student} (${uniName[c.student_phd.institution] || c.student_phd.institution}${c.student_phd.year ? ', ' + c.student_phd.year : ''})`;
    r.insertCell().textContent = c.student_cites_teacher ? 'yes' : 'no';
    const n = r.insertCell(); n.textContent = c.student_supervised; n.className = 'n';
  }
})();

// ---------- 3. Universities ----------
const U = V.universities;
(function heat() {
  const steps = ['--seq-1', '--seq-2', '--seq-3', '--seq-4', '--seq-5', '--seq-6', '--seq-7'];
  const max = Math.max(...U.field_matrix.flatMap(r => r.shares));
  const t = h('table', null, document.getElementById('heat'), 'heat'); const hr = t.createTHead().insertRow();
  h('th', 'Field', hr); for (const r of U.field_matrix) { const th = h('th', uniName[r.institution] || r.institution, hr, 'c'); th.title = `${r.n} dissertations`; }
  h('th', 'All', hr, 'c');
  const b = t.createTBody();
  fields.forEach((f, j) => {
    const row = b.insertRow(); h('th', f.label, row, 'r');
    for (const r of U.field_matrix.concat([{institution: 'all', n: null, shares: U.overall}])) {
      const v = r.shares[j], i = Math.min(steps.length - 1, Math.floor(v / max * steps.length));
      const c = row.insertCell(); c.className = 'c'; c.textContent = Math.round(100 * v);
      c.style.background = `var(${steps[i]})`; c.style.color = i >= 3 ? '#ffffff' : 'var(--text-primary)'; c.tabIndex = 0;
      hover(c, () => [pct(v), `${uniName[r.institution] || 'All universities'} · ${f.label}`].concat(r.n ? [`${r.n} dissertations, 2010–2025`] : []));
    }
  });
  const key = h('div', null, document.getElementById('heat'), 'key'); h('span', 'Share engaging the field: 0%', key);
  for (const s of steps) { const sw = h('span', null, key, 'sw'); sw.style.background = `var(${s})`; } h('span', pct(max), key);
})();
(function uni() {
  const box = document.getElementById('uni');
  for (const d of U.distinctive) {
    const fig = h('figure', null, box); const cap = h('figcaption', uniName[d.institution] || d.institution, fig); h('span', `${d.n} History PhDs, 2010–2025`, cap, 'sub');
    h('div', 'Drawn on more than elsewhere (share here / elsewhere)', fig, 'muted');
    const ol = h('ol', null, fig); for (const r of d.external.slice(0, 7)) h('li', `${r.name} · ${pct(r.share)} / ${pct(r.elsewhere)}`, ol);
    if (d.own_faculty.length) { h('div', 'Own faculty most cited by its dissertations', fig, 'muted'); h('div', d.own_faculty.slice(0, 5).map(r => `${r.name.split(',')[0]} ${pct(r.share)}`).join(' · '), fig); }
  }
})();
// ---------- 4. Practice ----------
if (V.methods) {
  const box = document.getElementById('methods');
  for (const [name, series] of Object.entries(V.methods.series)) {
    const fig = h('figure', null, box); const cap = h('figcaption', name, fig);
    const last = series.filter(p => p.share != null).slice(-6);
    h('span', `${pct(last.reduce((a, p) => a + p.k, 0) / Math.max(1, last.reduce((a, p) => a + p.n, 0)))} of recent dissertations`, cap, 'sub');
    lineChart(fig, series, {yMax: 1, ticks: [0, 0.5, 1], label: name});
  }
}
// ---------- 5. Atlas ----------
if (V.atlas) {
  const A = V.atlas, t = document.getElementById('atlasTiles');
  const tl = (label, value, ctx) => { const d = h('div', null, t, 'tile'); h('div', label, d, 'label'); h('div', value, d, 'value'); h('div', ctx, d, 'ctx'); };
  tl('Atlas people found in bibliographies', `${A.found} / ${A.roster}`, `${A.by_qid} by Wikidata QID, ${A.by_name} by name (candidate)`);
  tl('Atlas people cited by 10+ History PhDs', String(A.cited10), `${A.cited50} by 50 or more`);
  tl('Atlas people among the 100 most cited', String(A.top100), 'the rest are mostly Canadian national historiography');
  const gt = h('table', null, document.getElementById('gaps')); const gh = gt.createTHead().insertRow();
  for (const c of ['#', 'Scholar', 'History PhDs', 'Trend (2000s → 2018–25)', 'Main field', 'Most cited works']) h('th', c, gh);
  const gb = gt.createTBody();
  for (const r of A.gaps.slice(0, 40)) {
    const row = gb.insertRow();
    [[r.rank, 'n'], [r.name], [r.history_phds_citing, 'n'], [r.trend ? `${r.trend} (${pct(+r.share_2000_09)} → ${pct(+r.share_2018_25)})` : ''], [r.main_field], [r.top_works]].forEach(([v, c]) => { const td = row.insertCell(); td.textContent = v; if (c) td.className = c; });
  }
  const ft = h('table', null, document.getElementById('fieldAtlas')); const fh = ft.createTHead().insertRow();
  for (const c of ['Field', 'Atlas entries naming its people', 'Its people named in the atlas', 'Its people not in the atlas roster']) h('th', c, fh);
  const fb = ft.createTBody();
  for (const r of A.fields) { const row = fb.insertRow(); for (const k of ['field', 'atlas_entries_naming_its_people', 'field_people_named_in_atlas_entries', 'field_people_not_in_atlas_roster']) row.insertCell().textContent = r[k]; }
}
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    add_scope_argument(parser)
    args = parser.parse_args()
    summary = summary_dir(args.out, args.country)
    v = json.loads((summary / 'views.json').read_text())
    rob_path = audit_dir(args.out, args.country) / 'field-robustness.json'
    if rob_path.exists():
        rob = json.loads(rob_path.read_text())
        same = [c for c in rob['perturbations'] if not c.startswith('min cited')]
        v['robustness'] = {}
        for i, f in enumerate(rob['fields']):
            js = [rob['perturbations'][c][i]['jaccard'] for c in same]
            v['robustness'][f['field']] = dict(mean=round(sum(js) / len(js), 2), min=min(js))
    if (summary / 'methods.json').exists():
        v['methods'] = json.loads((summary / 'methods.json').read_text())
    if (summary / 'atlas-people-crosswalk.csv').exists():
        import csv
        rows = list(csv.DictReader((summary / 'atlas-people-crosswalk.csv').open()))
        found = [r for r in rows if r['basis'] != 'not_found']
        trends = {p['name']: p for p in json.loads((summary / 'trends.json').read_text())['people']}
        top100 = sorted(trends.values(), key=lambda p: -p['total'])[:100]
        atlas_names = {r['graph_name'] for r in found}
        v['atlas'] = dict(roster=len(rows), found=len(found), by_qid=sum(r['basis'] == 'wikidata_qid' for r in found),
                          by_name=sum(r['basis'] != 'wikidata_qid' for r in found),
                          cited10=sum(int(r['history_phds_citing']) >= 10 for r in found),
                          cited50=sum(int(r['history_phds_citing']) >= 50 for r in found),
                          top100=sum(p['name'] in atlas_names for p in top100),
                          gaps=list(csv.DictReader((summary / 'atlas-gaps.csv').open())),
                          fields=list(csv.DictReader((summary / 'field-atlas-crosswalk.csv').open())))
    template = TEMPLATE if 'atlas' in v else re.sub(r'<!--atlas-->.*?<!--/atlas-->\n?', '', TEMPLATE, flags=re.S)
    label = scope_label(args.country)
    html = (template.replace('<!--atlas-->', '').replace('<!--/atlas-->\n', '').replace('<!--/atlas-->', '')
            .replace('__WHO__', f'{label} ' if label else '')
            .replace('__ROBUSTNESS__', rob_path.relative_to(args.out).as_posix())
            .replace('__DATA__', json.dumps(v, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__N__', f"{v['supervision']['dissertations']:,}").replace('__WITHSUP__', f"{v['supervision']['with_supervisor']:,}")
            .replace('__MINC__', str(v['fields']['min_cited'])).replace('__WORKS__', str(v['fields']['works']))
            .replace('__CLUSTERED__', str(v['fields']['clustered'])).replace('__MIN__', str(v['min_window']))
            .replace('__UNIS__', str(len(v['universities']['institutions'])))
            .replace('__SECTIONED__', f"{v.get('methods', {}).get('dissertations', 0):,}"))
    (summary / 'citation-views.html').write_text(html)
    print('wrote', summary / 'citation-views.html')


if __name__ == '__main__':
    main()
