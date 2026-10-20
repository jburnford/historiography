#!/usr/bin/env python3
"""Render trends.json (dissertation_citation_trends.py) as one self-contained HTML page.

``--country CC`` renders a country sub-graph's page (``summary/countries/<CC>/``); without it,
the main graph's (``summary/``). See ``dissertation_scope.py``.

Small multiples of the share of History PhD dissertations citing each scholar per year
(centred three-year window, Wilson 95% band), grouped by the computed trend, plus the
context charts (dissertations per year, bibliography length, age of cited work).
Thin windows (fewer than ``min_window`` dissertations) are drawn in grey.
"""
import argparse
import json
from pathlib import Path

from dissertation_scope import add_scope_argument, in_scope, scope_label, summary_dir

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What __WHO__History PhDs cite, over time</title>
<style>
.viz-root {
  color-scheme: light;
  --surface-1: #fcfcfb; --page: #f9f9f7;
  --text-primary: #0b0b0b; --text-secondary: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --thin: #b9b8b1;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --surface-1: #1a1a19; --page: #0d0d0d;
    --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --thin: #5a5955;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --surface-1: #1a1a19; --page: #0d0d0d;
  --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --series-1: #3987e5; --thin: #5a5955;
}
body { margin: 0; }
.viz-root { background: var(--page); color: var(--text-primary);
  font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; padding: 24px 28px 48px; min-height: 100vh; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 6px; }
h2 { font-size: 16px; font-weight: 600; margin: 32px 0 4px; }
p.lede, p.note { color: var(--text-secondary); max-width: 920px; margin: 4px 0; }
p.note { font-size: 12.5px; }
.controls { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin: 18px 0 8px; }
.controls label { color: var(--text-secondary); font-size: 13px; }
select, button { font: inherit; color: var(--text-primary); background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 6px; padding: 5px 10px; }
button { cursor: pointer; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap: 12px; }
figure { margin: 0; background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 12px 12px 8px;
  position: relative; }
figcaption { font-size: 13px; font-weight: 600; margin: 0 0 2px; }
figcaption .sub { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  font-weight: 400; color: var(--text-secondary); font-size: 12px; height: 2.9em; font-style: italic; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
.tick { fill: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }
.end { fill: var(--text-secondary); font-size: 11px; font-variant-numeric: tabular-nums; }
.tip { position: fixed; pointer-events: none; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; z-index: 10; }
.tip strong { font-size: 14px; display: block; }
.tip .k { color: var(--text-secondary); }
.tip .warn { color: var(--text-secondary); font-style: italic; }
.key { display: flex; gap: 18px; align-items: center; color: var(--text-secondary); font-size: 12px; margin: 6px 0 0; flex-wrap: wrap; }
.key i { display: inline-block; width: 18px; height: 2px; vertical-align: middle; margin-right: 6px; }
.key b { display: inline-block; width: 18px; height: 10px; vertical-align: middle; margin-right: 6px; opacity: .25; }
table { border-collapse: collapse; font-size: 12.5px; margin-top: 10px; background: var(--surface-1); }
th, td { border-bottom: 1px solid var(--grid); padding: 4px 10px; text-align: left; }
td.n { text-align: right; font-variant-numeric: tabular-nums; }
.hidden { display: none; }
</style>
</head>
<body>
<div class="viz-root">
<h1>What __WHO__History PhDs cite, over time</h1>
<p class="lede">The bibliographies of __N__ History doctoral dissertations from __U__ __UNIS__.
Each panel shows the share of a year's dissertations that cite a scholar (any of their works), over a
centred three-year window. Shares are normalised by dissertations per year, so corpus growth does not
read as rising influence.</p>
<p class="note">Grey line and band: thin windows of fewer than __MIN__ dissertations, mostly before 1990,
where one thesis moves the share by several points. The shaded band is a 95% Wilson interval. Years are
repository issued years, which can be deposit rather than convocation years. __COVERAGE__ Trend
groups compare 2000–09 with 2018–25 (rising: at least 1.25× and 2 points higher; declining: at most 0.75× and
2 points lower). The final year is a two-year window, and recent deposits may still be incomplete.</p>

<h2>The corpus and the bibliographies</h2>
<div class="cards" id="context"></div>
<div class="key"><span><i style="background:var(--series-1)"></i>Window of 30 or more dissertations</span>
<span><i style="background:var(--thin)"></i>Thin window (small sample)</span>
<span><b style="background:var(--series-1)"></b>95% interval</span></div>

<div class="controls">
  <label for="pick">Add a scholar</label>
  <select id="pick"><option value="">Choose a scholar…</option></select>
  <button id="tableBtn" type="button" aria-pressed="false">Show table</button>
</div>
<div id="picked" class="grid"></div>
<div id="tableView" class="hidden"></div>

<h2>Rising since the 2000s</h2><p class="note" id="n-rising"></p><div class="grid" id="rising"></div>
<h2>Steady</h2><p class="note" id="n-steady"></p><div class="grid" id="steady"></div>
<h2>Declining since the 2000s</h2><p class="note" id="n-declining"></p><div class="grid" id="declining"></div>
<div class="tip" id="tip" role="status"></div>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const NS = 'http://www.w3.org/2000/svg';
const tip = document.getElementById('tip');
const YEARS = DATA.years, Y0 = 1965, Y1 = YEARS[YEARS.length - 1];
const PER_GROUP = 15;

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function pct(v) { return v == null ? '–' : (+(100 * v).toFixed(v < 0.1 ? 1 : 0)) + '%'; }

// One small line chart: points [{year, value, lo, hi, thin}], yMax, formatter.
function lineChart(fig, pts, opts) {
  const W = 260, H = 120, L = 30, R = 34, T = 8, B = 20;
  const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': opts.label}, fig);
  const x = y => L + (y - Y0) / (Y1 - Y0) * (W - L - R);
  const y = v => T + (1 - v / opts.yMax) * (H - T - B);
  for (const t of opts.ticks) {
    el('line', {x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: 'var(--grid)', 'stroke-width': 1}, svg);
    const lab = el('text', {x: L - 4, y: y(t) + 3, 'text-anchor': 'end', class: 'tick'}, svg);
    lab.textContent = opts.fmtTick(t);
  }
  for (const yr of [1970, 1990, 2010, Y1]) {
    const lab = el('text', {x: x(yr), y: H - 5, 'text-anchor': 'middle', class: 'tick'}, svg);
    lab.textContent = yr;
  }
  el('line', {x1: L, x2: W - R, y1: y(0), y2: y(0), stroke: 'var(--axis)', 'stroke-width': 1}, svg);
  const shown = pts.filter(p => p.year >= Y0 && p.value != null);
  // band, split by thin/thick
  const segs = [];
  for (const p of shown) {
    const last = segs[segs.length - 1];
    if (!last || last.thin !== p.thin) segs.push({thin: p.thin, pts: last ? [last.pts[last.pts.length - 1], p] : [p]});
    else last.pts.push(p);
  }
  for (const s of segs) {
    if (opts.band && s.pts[0].lo != null) {
      const up = s.pts.map(p => `${x(p.year)},${y(Math.min(p.hi, opts.yMax))}`).join(' ');
      const dn = s.pts.slice().reverse().map(p => `${x(p.year)},${y(p.lo)}`).join(' ');
      el('polygon', {points: up + ' ' + dn, fill: s.thin ? 'var(--thin)' : 'var(--series-1)', opacity: s.thin ? 0.07 : 0.12}, svg);
    }
    el('polyline', {points: s.pts.map(p => `${x(p.year)},${y(Math.min(p.value, opts.yMax))}`).join(' '), fill: 'none',
      stroke: s.thin ? 'var(--thin)' : 'var(--series-1)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round'}, svg);
  }
  const end = shown[shown.length - 1];
  if (end) {
    el('circle', {cx: x(end.year), cy: y(Math.min(end.value, opts.yMax)), r: 4, fill: 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2}, svg);
    const t = el('text', {x: x(end.year) + 7, y: y(Math.min(end.value, opts.yMax)) + 4, class: 'end'}, svg);
    t.textContent = opts.fmtEnd(end.value);
  }
  // crosshair + tooltip
  const cross = el('line', {y1: T, y2: H - B, stroke: 'var(--axis)', 'stroke-width': 1, visibility: 'hidden'}, svg);
  const dot = el('circle', {r: 4, fill: 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2, visibility: 'hidden'}, svg);
  const hit = el('rect', {x: L, y: 0, width: W - L - R, height: H, fill: 'transparent', tabindex: 0}, svg);
  function show(clientX, clientY, yr) {
    const p = shown.reduce((a, b) => Math.abs(b.year - yr) < Math.abs(a.year - yr) ? b : a, shown[0]);
    if (!p) return;
    cross.setAttribute('x1', x(p.year)); cross.setAttribute('x2', x(p.year)); cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', x(p.year)); dot.setAttribute('cy', y(Math.min(p.value, opts.yMax))); dot.setAttribute('visibility', 'visible');
    tip.replaceChildren();
    const s = document.createElement('strong'); s.textContent = opts.fmtEnd(p.value); tip.appendChild(s);
    const k = document.createElement('div'); k.className = 'k'; k.textContent = opts.describe(p); tip.appendChild(k);
    if (p.thin) { const w = document.createElement('div'); w.className = 'warn'; w.textContent = 'Thin window: small sample'; tip.appendChild(w); }
    tip.style.display = 'block';
    tip.style.left = Math.min(clientX + 14, window.innerWidth - tip.offsetWidth - 8) + 'px';
    tip.style.top = (clientY + 14) + 'px';
  }
  hit.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect();
    const sx = (ev.clientX - r.left) / r.width * W;
    show(ev.clientX, ev.clientY, Y0 + (sx - L) / (W - L - R) * (Y1 - Y0));
  });
  hit.addEventListener('focus', () => { const r = svg.getBoundingClientRect(); show(r.right - 40, r.top, Y1); });
  for (const evn of ['pointerleave', 'blur']) hit.addEventListener(evn, () => {
    tip.style.display = 'none'; cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden');
  });
}

function barChart(fig, rows) {
  const W = 300, H = 130, L = 30, R = 8, T = 8, B = 20;
  const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Dissertations per year'}, fig);
  const shown = rows.filter(r => r.year >= Y0);
  const max = Math.max(...shown.map(r => r.dissertations));
  const yMax = Math.ceil(max / 20) * 20;
  const x = yr => L + (yr - Y0) / (Y1 - Y0 + 1) * (W - L - R);
  const bw = Math.max(1, (W - L - R) / (Y1 - Y0 + 1) - 1);
  const y = v => T + (1 - v / yMax) * (H - T - B);
  for (const t of [0, yMax / 2, yMax]) {
    el('line', {x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: 'var(--grid)', 'stroke-width': 1}, svg);
    el('text', {x: L - 4, y: y(t) + 3, 'text-anchor': 'end', class: 'tick'}, svg).textContent = t;
  }
  for (const yr of [1970, 1990, 2010, Y1]) el('text', {x: x(yr) + bw / 2, y: H - 5, 'text-anchor': 'middle', class: 'tick'}, svg).textContent = yr;
  for (const r of shown) {
    if (!r.dissertations) continue;
    const b = el('rect', {x: x(r.year), y: y(r.dissertations), width: bw, height: y(0) - y(r.dissertations),
      fill: r.thin ? 'var(--thin)' : 'var(--series-1)', rx: 1, tabindex: 0}, svg);
    const show = (cx, cy) => {
      tip.replaceChildren();
      const s = document.createElement('strong'); s.textContent = r.dissertations + ' dissertations'; tip.appendChild(s);
      const k = document.createElement('div'); k.className = 'k'; k.textContent = r.year + ' · 3-year window ' + r.window; tip.appendChild(k);
      if (r.thin) { const w = document.createElement('div'); w.className = 'warn'; w.textContent = 'Thin window'; tip.appendChild(w); }
      tip.style.display = 'block'; tip.style.left = (cx + 14) + 'px'; tip.style.top = (cy + 14) + 'px';
    };
    b.addEventListener('pointermove', ev => show(ev.clientX, ev.clientY));
    b.addEventListener('focus', () => { const bb = b.getBoundingClientRect(); show(bb.right, bb.top); });
    for (const evn of ['pointerleave', 'blur']) b.addEventListener(evn, () => { tip.style.display = 'none'; });
  }
  el('line', {x1: L, x2: W - R, y1: y(0), y2: y(0), stroke: 'var(--axis)', 'stroke-width': 1}, svg);
}

function card(parent, title, sub) {
  const fig = document.createElement('figure');
  const cap = document.createElement('figcaption');
  cap.textContent = title;
  const s = document.createElement('span'); s.className = 'sub'; s.textContent = sub; cap.appendChild(s);
  fig.appendChild(cap); parent.appendChild(fig);
  return fig;
}

// Context charts
const ctx = document.getElementById('context');
barChart(card(ctx, 'Dissertations per year', 'Strict History PhDs with a parsed bibliography; grey = thin 3-year window'), DATA.context);
const ctxLine = (title, sub, field, yMax, ticks, unit) => lineChart(card(ctx, title, sub),
  DATA.context.map(c => ({year: c.year, value: c[field], thin: c.thin})),
  {yMax, ticks, band: false, label: title, fmtTick: t => t, fmtEnd: v => Math.round(v) + unit,
   describe: p => p.year + ' · median, 3-year window'});
ctxLine('Works cited per dissertation', 'Median bibliography length (distinct works)', 'median_works_cited', 300, [0, 100, 200, 300], '');
ctxLine('Age of cited scholarship', 'Median years between a dissertation and the works it cites', 'median_age_cited', 40, [0, 20, 40], ' yrs');

// Small multiples
const share = s => s.share;
const yMaxShare = 0.33;
function personPanel(parent, p) {
  const short = t => { const m = t.split(/[:.]\s/)[0]; return m.length > 38 ? m.slice(0, 36).trimEnd() + '…' : m; };
  const sub = p.top_works.slice(0, 2).map(short).join(' · ');
  const fig = card(parent, p.name, sub);
  lineChart(fig, p.series.map(s => ({year: s.year, value: s.share, lo: s.lo, hi: s.hi, thin: s.thin, k: s.k, n: s.n})),
    {yMax: yMaxShare, ticks: [0, 0.1, 0.2, 0.3], band: true, label: 'Share of dissertations citing ' + p.name,
     fmtTick: t => (100 * t) + '%', fmtEnd: v => pct(v),
     describe: q => `${q.year} · ${q.k} of ${q.n} dissertations · 95% ${pct(q.lo)}–${pct(q.hi)}`});
}
const ORDER = {rising: p => -(p.share_2018_25 - p.share_2000s), declining: p => (p.share_2018_25 - p.share_2000s), steady: p => -p.total};
const HOW = {rising: 'largest increases', declining: 'largest decreases', steady: 'most cited'};
for (const g of ['rising', 'steady', 'declining']) {
  const ps = DATA.people.filter(p => p.trend === g).sort((a, b) => ORDER[g](a) - ORDER[g](b));
  document.getElementById('n-' + g).textContent =
    `${ps.length} of the ${DATA.people.length} scholars cited by at least ${DATA.min_citing} History PhDs; the ${Math.min(PER_GROUP, ps.length)} with the ${HOW[g]} (2000–09 to 2018–25) are shown. Add others with the selector above.`;
  for (const p of ps.slice(0, PER_GROUP)) personPanel(document.getElementById(g), p);
}

// Selector
const pick = document.getElementById('pick');
DATA.people.slice().sort((a, b) => a.name.localeCompare(b.name)).forEach(p => {
  const o = document.createElement('option'); o.value = p.id; o.textContent = `${p.name} (${p.total})`; pick.appendChild(o);
});
pick.addEventListener('change', () => {
  const p = DATA.people.find(q => q.id === pick.value);
  if (p) personPanel(document.getElementById('picked'), p);
  pick.value = '';
});

// Table view
const tableBtn = document.getElementById('tableBtn'), tv = document.getElementById('tableView');
tableBtn.addEventListener('click', () => {
  const open = tv.classList.toggle('hidden') === false;
  tableBtn.setAttribute('aria-pressed', open); tableBtn.textContent = open ? 'Hide table' : 'Show table';
  if (open && !tv.firstChild) {
    const t = document.createElement('table');
    const head = t.createTHead().insertRow();
    for (const h of ['Scholar', 'Dissertations citing', 'Share 2000–09', 'Share 2018–25', 'Trend']) {
      const th = document.createElement('th'); th.textContent = h; head.appendChild(th);
    }
    const body = t.createTBody();
    for (const p of DATA.people) {
      const r = body.insertRow();
      [[p.name], [p.total, 'n'], [pct(p.share_2000s), 'n'], [pct(p.share_2018_25), 'n'], [p.trend]].forEach(([v, c]) => {
        const td = r.insertCell(); td.textContent = v; if (c) td.className = c;
      });
    }
    tv.appendChild(t);
  }
});
</script>
</body>
</html>
"""


CA_COVERAGE = """Coverage is by repository
holdings: UBC is absent, most of Laval is pending, and most dissertations date from after 2010."""
MAIN_COVERAGE = """Coverage is by repository
holdings and differs by country (coverage-by-university.csv); most dissertations date from after 2010."""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    add_scope_argument(parser)
    args = parser.parse_args()
    summary = summary_dir(args.out, args.country)
    data = json.loads((summary / 'trends.json').read_text())
    graph = json.loads((args.out / 'graph.json').read_text())
    n = sum(c['dissertations'] for c in data['context'])
    diss = [d for d in graph['nodes'] if in_scope(d, args.country)]
    universities = len({d['institution'] for d in diss})
    countries = len({d['country'] for d in diss})
    label = scope_label(args.country)
    unis = f'{label} universities' if args.country else f'universities in {countries} {"country" if countries == 1 else "countries"}'
    html = (TEMPLATE.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__WHO__', f'{label} ' if label else '').replace('__UNIS__', unis)
            .replace('__COVERAGE__', CA_COVERAGE if args.country == 'CA' else MAIN_COVERAGE)
            .replace('__N__', f'{n:,}').replace('__U__', str(universities)).replace('__MIN__', str(data['min_window'])))
    (summary / 'citation-trends.html').write_text(html)
    print('wrote', summary / 'citation-trends.html', graph['meta'].get('dissertations'))

if __name__ == '__main__':
    main()
