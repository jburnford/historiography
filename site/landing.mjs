/* The landing: eleven editorial families, the atlas's dating beside the record's share of
   what historians published. Pure builders; app.js renders and wires them.
   specs/2026-09-27-landing-redesign-design.md */
import {spanOf} from './field.mjs';

export const AXIS = {start: 1880, end: 2024, coverage: 2000};
export const VIEWS = {all: 'All journals', established: 'Established journals only', reviews: 'Reviews'};

const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const pct = x => `${(x * 100).toFixed(1)}%`;
const short = f => f.label.split(/[\s,&]/)[0];

/* Where the atlas dates each member: its first year (curated span, else the date label). */
export function atlasTrack(graph, family) {
  const byId = new Map(graph.nodes.map(n => [n.id, n]));
  const dots = [], early = [], undated = [];
  for (const m of family.members) {
    const node = byId.get(m.id);
    if (!node) continue;
    const s = spanOf(node);
    if (!s) undated.push(node);
    else (s.start < AXIS.start ? early : dots).push({node, year: s.start});
  }
  dots.sort((a, b) => a.year - b.year || a.node.label.localeCompare(b.node.label));
  return {dots, early, undated};
}

export function recordShares(family, view) {
  return (family.series[view] || []).filter(([bin]) => bin + 4 <= AXIS.end)
    .map(([bin, items, total]) => ({bin, items, total, share: total ? items / total : 0}));
}

/* The gap in one line: primary members only, so each bar sums to 100%. */
export function stripSegments(block, graph) {
  const groups = new Set(graph.nodes.filter(n => n.entry_kind === 'group').map(n => n.id));
  const count = f => f.members.filter(m => m.primary && groups.has(m.id)).length;
  const total = block.families.reduce((a, f) => a + count(f), 0) || 1;
  return {
    atlas: block.families.map(f => ({id: f.id, label: f.label, short: short(f), share: count(f) / total, count: count(f)})),
    record: block.families.map(f => ({id: f.id, label: f.label, short: short(f), share: block.strip.shares[f.id] || 0})),
    unclaimed: block.strip.unclaimed, period: block.strip.period,
  };
}

export function familyBySlug(block, slug) {
  return block?.families?.find(f => f.id === slug) || null;
}

/* The field view for one family: its fields (bridges included), the person entries linked to
   them, and only the relationships among those. Journals follow via journalNodes.
   `__fieldNodes` is reset so a subgraph never inherits a cache built from the full graph. */
export function familyGraph(graph, family) {
  const keep = new Set(family.members.map(m => m.id));
  const kind = new Map(graph.nodes.map(n => [n.id, n.entry_kind]));
  const ids = new Set(keep);
  for (const e of graph.edges) {
    if (keep.has(e.source) && kind.get(e.target) === 'person') ids.add(e.target);
    if (keep.has(e.target) && kind.get(e.source) === 'person') ids.add(e.source);
  }
  return {...graph, nodes: graph.nodes.filter(n => ids.has(n.id)),
    edges: graph.edges.filter(e => ids.has(e.source) && ids.has(e.target)),
    __fieldNodes: undefined};
}

const peakOf = (block, view) => Math.max(0.01, ...block.families.flatMap(f => recordShares(f, view).map(s => s.share)));

/* Long family labels wrap at the space nearest the middle rather than overflow the left
   edge; ' ›' always stays on the last line. ~7px/character at the label's 14px serif. */
function labelLines(label, labelW) {
  if (label.length * 7 + 12 <= labelW) return [`${label} ›`];
  const mid = label.length / 2;
  const spaces = [...label].map((c, i) => c === ' ' ? i : -1).filter(i => i >= 0);
  if (!spaces.length) return [`${label} ›`];
  const at = spaces.reduce((best, i) => Math.abs(i - mid) < Math.abs(best - mid) ? i : best);
  return [label.slice(0, at), `${label.slice(at + 1)} ›`];
}

/* Paired rows on one axis. `width` is the measured width of the box the SVG sits in. Each
   row is a native SVG `<a>` (not a `<g>` with a synthetic role): middle-click, Enter and
   no-JS all work without app.js wiring a click handler. */
export function rowsSvg({block, graph, view = 'all', width = 1000, href}) {
  const labelW = Math.min(280, Math.max(160, width * 0.26));
  const x0 = labelW + 16, x1 = width - 16, rowH = 58, top = 26, foot = 26, barMax = 26;
  const x = y => x0 + (Math.max(y, AXIS.start) - AXIS.start) / (AXIS.end + 1 - AXIS.start) * (x1 - x0);
  const peak = peakOf(block, view);
  const H = top + block.families.length * rowH + foot, bw = Math.max(1, x(2005) - x(2000) - 1.5);
  const grid = [1900, 1920, 1940, 1960, 1980, 2000, 2020].map(y =>
    `<line class="grid" x1="${x(y).toFixed(1)}" x2="${x(y).toFixed(1)}" y1="${top}" y2="${H - foot}"/>` +
    `<text class="tick" x="${x(y).toFixed(1)}" y="${H - 9}" text-anchor="middle">${y}</text>`).join('');
  const rows = block.families.map((f, i) => {
    const t = atlasTrack(graph, f), shares = recordShares(f, view);
    const y0 = top + i * rowH, base = y0 + rowH - 6, cy = y0 + rowH / 2;
    const dots = t.dots.map(d => `<circle class="atlas-dot" cx="${x(d.year).toFixed(1)}" cy="${y0 + 13}" r="4"><title>${esc(d.node.label)} · ${d.year}</title></circle>`).join('');
    const early = t.early.length ? `<text class="early-mark" x="${x0 - 3}" y="${y0 + 17}" text-anchor="end">◂<title>${esc(`Dated before ${AXIS.start}: ${t.early.map(e => `${e.node.label} (${e.year})`).join('; ')}`)}</title></text>` : '';
    const bars = shares.filter(s => s.items).map(s => {
      const h = s.share / peak * barMax;
      return `<rect class="record-bar" x="${x(s.bin).toFixed(1)}" y="${(base - h).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}"><title>${s.bin}–${s.bin + 4}: ${pct(s.share)} (${s.items.toLocaleString('en')} of ${s.total.toLocaleString('en')})</title></rect>`;
    }).join('');
    const dated = t.dots.length + t.early.length;
    const label = `${f.label}: ${dated} dated atlas entr${dated === 1 ? 'y' : 'ies'}${t.undated.length ? `, ${t.undated.length} undated` : ''}; share of the record in ${shares.at(-1)?.bin ?? '—'}–${AXIS.end}: ${pct(shares.at(-1)?.share || 0)}. Open its fields.`;
    /* Undated members are not dropped from the row; they surface in its tooltip. */
    const undatedTitle = t.undated.length
      ? `<title>${esc(`Undated: ${t.undated.map(n => n.label).join('; ')}`)}</title>` : '';
    const lines = labelLines(f.label, labelW);
    const labelEl = lines.length > 1
      ? `<text class="family-label" x="${labelW}" y="${(cy - 3).toFixed(1)}" text-anchor="end">` +
        lines.map((l, li) => `<tspan x="${labelW}" dy="${li === 0 ? 0 : 15}">${esc(l)}</tspan>`).join('') +
        `${undatedTitle}</text>`
      : `<text class="family-label" x="${labelW}" y="${(cy + 5).toFixed(1)}" text-anchor="end">${esc(lines[0])}${undatedTitle}</text>`;
    return `<a class="family-row" href="${esc(href(f.id))}" data-family="${esc(f.id)}" aria-label="${esc(label)}">` +
      `<rect class="row-hit" x="0" y="${y0}" width="${width}" height="${rowH}"/>` +
      labelEl +
      `<line class="row-base" x1="${x0}" x2="${x1}" y1="${base + 0.5}" y2="${base + 0.5}"/>${bars}${dots}${early}` +
      (bars ? '' : `<text class="row-empty" x="${x1}" y="${base - 4}" text-anchor="end">no items in this view</text>`) + `</a>`;
  }).join('');
  const cx = x(AXIS.coverage).toFixed(1);
  const wall = `<line class="coverage-line" x1="${cx}" x2="${cx}" y1="${top - 6}" y2="${H - foot}"/>` +
    `<text class="coverage-label" x="${(+cx - 5).toFixed(1)}" y="${top - 10}" text-anchor="end">atlas coverage ends ${AXIS.coverage}</text>`;
  return `<svg class="landing-svg" viewBox="0 0 ${width} ${H}" width="${width}" height="${H}" role="group" aria-label="Families of historical writing: atlas dating and share of the record, ${AXIS.start}–${AXIS.end}">${grid}${wall}${rows}</svg>`;
}

/* Narrow screens: one card per family, on the same shared scale from 1950. */
export function cardsHtml({block, graph, view = 'all', href}) {
  const peak = peakOf(block, view);
  return `<ol class="family-cards">${block.families.map(f => {
    const t = atlasTrack(graph, f), s = recordShares(f, view).filter(b => b.bin >= 1950);
    const bars = s.map((b, i) => { const h = b.share / peak * 28; return `<rect x="${i * 9}" y="${(30 - h).toFixed(1)}" width="8" height="${h.toFixed(1)}"/>`; }).join('');
    const first = [...t.early, ...t.dots].map(d => d.year).sort((a, b) => a - b)[0];
    const n = t.dots.length + t.early.length + t.undated.length;
    /* A decade-derived early year would misstate precision the atlas doesn't claim. */
    const firstText = first == null ? '' : first < AXIS.start ? `, earliest before ${AXIS.start}` : `, earliest ${first}`;
    return `<li><a class="family-card" href="${esc(href(f.id))}"><h3>${esc(f.label)}</h3>` +
      `<p><strong>${n}</strong> atlas entr${n === 1 ? 'y' : 'ies'}${firstText}</p>` +
      `<svg class="card-bars" viewBox="0 0 ${Math.max(9, s.length * 9)} 31" preserveAspectRatio="none" aria-hidden="true">${bars}</svg>` +
      `<p class="fine-print">${s.length ? `${s.at(-1).bin}–${AXIS.end}: ${pct(s.at(-1).share)} of the record` : 'No record in this view'}</p></a></li>`;
  }).join('')}</ol>`;
}

/* The same numbers as text: every bin the chart draws, not a truncated recent slice. */
export function tableHtml({block, graph, view = 'all'}) {
  const bins = [...new Set(block.families.flatMap(f => recordShares(f, view).map(s => s.bin)))]
    .sort((a, b) => a - b);
  const head = `<tr><th scope="col">Family</th><th scope="col">Atlas entries</th><th scope="col">Undated</th>${bins.map(b => `<th scope="col">${b}–${String(b + 4).slice(2)}</th>`).join('')}</tr>`;
  const rows = block.families.map(f => {
    const t = atlasTrack(graph, f), by = new Map(recordShares(f, view).map(s => [s.bin, s]));
    return `<tr><th scope="row">${esc(f.label)}</th><td>${t.dots.length + t.early.length + t.undated.length}</td><td>${t.undated.length}</td>${bins.map(b => {
      const s = by.get(b);
      return `<td${s ? ` title="${s.items.toLocaleString('en')} of ${s.total.toLocaleString('en')}"` : ''}>${s ? pct(s.share) : '—'}</td>`;
    }).join('')}</tr>`;
  }).join('');
  return `<div class="table-scroll"><table><caption class="sr-only">Atlas entries and share of the record (${esc(VIEWS[view])}) per family and five-year period</caption><thead>${head}</thead><tbody>${rows}</tbody></table></div>`;
}
