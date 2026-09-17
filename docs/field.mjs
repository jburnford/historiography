/* The Field: every atlas entry on one time axis, with journals that carry an evidenced
   venue relation. Pure functions — layout and markup only; app.js owns events and routing.

   Two ideas do the work:
   1. Focus re-lays out. Holding an entry collapses everything unrelated to a thin ghost
      mark so the entry and its relations expand into the freed space.
   2. Dates stay honest. Spans say when something arrived and was influential, not how long
      it lasted. A curated `date_span` always wins over the prose parse, and the panel says
      which was used. See scope.notes: "Dates describe approximate emergence or expansion,
      not termination." */

export const BASE_KINDS = ['critique', 'contribution', 'influence', 'comparison'];
export const KIND_SECTION = {
  critique: 'Disagreements', contribution: 'Contributions',
  influence: 'Influence', comparison: 'Comparisons',
  founded_for: 'Founded for', site_of_debate: 'Site of debate',
  principal_venue: 'Principal venue',
};
const DIR = {
  critique: {out: 'criticises', in: 'is criticised by'},
  contribution: {out: 'contributes to', in: 'draws a contribution from'},
  influence: {out: 'influences', in: 'is influenced by'},
  comparison: {out: 'compared with', in: 'compared with'},
  founded_for: {out: 'was founded for', in: 'has a founding venue'},
  site_of_debate: {out: 'hosted a debate in', in: 'debated in'},
  principal_venue: {out: 'is a principal venue for', in: 'has a principal venue'},
};
export const JOURNAL_LAYER = 'journals_and_venues';
const BREAK_YEAR = 1900, EARLY_SHARE = 0.2;
const G = {padL: 18, padR: 26, barH: 19, rowGap: 9, bandGap: 30, ghostH: 4, ghostGap: 3,
           chipH: 23, chipGap: 6, railW: 300, railCols: 2, railGap: 22};

const titleCase = k => String(k).replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
/* Section headings read as questions; legend chips read as the relationship's own name. */
export const kindLabel = k => KIND_SECTION[k] || titleCase(k);
export const kindChip = k => ({critique: 'Critique', contribution: 'Contribution',
  influence: 'Influence', comparison: 'Comparison'})[k] || titleCase(k);
export const dirWord = (kind, dir) => DIR[kind]?.[dir]
  || `${kindLabel(kind).toLowerCase()} ${dir === 'out' ? '→' : '←'}`;

/* ---------- dates ---------- */
export function parseSpan(label) {
  const s = label || '';
  const cov = s.match(/coverage through\s+(1[6-9]\d{2}|20[0-2]\d)/i);
  const coverage = cov ? +cov[1] : null;
  const body = cov ? s.replace(cov[0], ' ') : s;
  const found = [];
  let precision = 'year';
  const decade = /(1[6-9]\d0|20[0-2]0)s(?:\s*[–—-]\s*(?:(1[6-9]\d0|20[0-2]0)s|(\d{2})s))?/g;
  for (let m; (m = decade.exec(body));) {
    const a = +m[1];
    let b = a + 9;
    if (m[2]) b = +m[2] + 9;
    else if (m[3]) b = Math.floor(a / 100) * 100 + +m[3] + 9;
    found.push([a, b]);
    precision = 'decade';
  }
  for (const y of body.match(/\b(1[6-9]\d{2}|20[0-2]\d)\b(?!s)/g) || []) found.push([+y, +y]);
  if (!found.length) return null;
  const endsExplicitly = /\bended\b|\bends\b|\buntil\b|\bceased\b|\bclosed\b|\bdisbanded\b/i.test(body);
  const continues = coverage !== null || /onward|present|continu|ongoing|later\b/i.test(body);
  return {
    start: Math.min(...found.map(f => f[0])), end: Math.max(...found.map(f => f[1])),
    endKind: endsExplicitly ? 'terminus' : continues ? 'coverage_limit' : 'unstated',
    coverage, precision, curated: false,
  };
}

export function spanOf(node) {
  const d = node.date_span;
  if (d && Number.isFinite(d.start)) {
    const end = Number.isFinite(d.end) ? d.end : null;
    return {
      start: d.start, end: end ?? d.start,
      /* An unverified end is not an ending: continue rather than stop. */
      endKind: end === null ? 'coverage_limit' : (d.end_kind || 'unstated'),
      coverage: Number.isFinite(d.coverage_through) ? d.coverage_through : null,
      precision: d.precision || 'year', curated: true,
      basis: d.basis || '', startKind: d.start_kind || '',
    };
  }
  const parsed = parseSpan(node.date_label);
  return parsed || null;
}

/* ---------- journals ---------- */
/* The catalogue is a discovery inventory (1,600+ periodicals). Only journals carrying at
   least one evidenced venue edge become field entries; the rest stay counted, not drawn. */
export function journalNodes(graph) {
  const jc = graph.journal_catalogue;
  if (!jc?.nodes?.length) return {nodes: [], edges: [], unlinked: 0};
  const byId = new Map(jc.nodes.map(n => [n.id, n]));
  const atlas = new Set(graph.nodes.map(n => n.id));
  const edges = (jc.edges || []).filter(e => byId.has(e.source) && atlas.has(e.target));
  const linked = new Set(edges.map(e => e.source));
  const nodes = [...linked].map(id => {
    const j = byId.get(id), d = j.date_span;
    return {
      id, label: j.label, layer: JOURNAL_LAYER, entry_kind: 'periodical',
      entry_type: 'Journal or periodical', period: null, hunt_core_paradigm: false,
      date_label: journalDateLabel(j),
      date_span: d && Number.isFinite(d.start) ? {
        start: d.start, end: Number.isFinite(d.end) ? d.end : null,
        precision: d.precision || 'year',
        end_kind: Number.isFinite(d.end) ? d.end_kind : 'coverage_limit',
        start_kind: d.start_kind || '', basis: journalDateBasis(j),
      } : undefined,
      description: j.mapping_note
        || 'A periodical linked to the atlas by an evidenced founding, debate or principal-venue claim.',
      representative_figures_and_works: '', scope_note: j.chronology_note || '',
      source_ids: j.source_ids || [], issns: j.issns || [],
    };
  }).sort((a, b) => a.label.localeCompare(b.label));
  return {
    nodes,
    edges: edges.map(e => ({
      id: e.id, source: e.source, target: e.target, relationship: e.relationship,
      relationship_kind: e.relationship_kind, type: 'connection', directed: true,
      source_ids: e.source_ids || [], evidence_note: e.evidence_note || '',
    })),
    unlinked: Number.isFinite(jc.unlinked_periodical_count)
      ? jc.unlinked_periodical_count
      : jc.nodes.filter(n => n.entry_kind === 'periodical' && !linked.has(n.id)).length,
  };
}

function journalDateLabel(j) {
  const d = j.date_span;
  if (!d || !Number.isFinite(d.start)) return 'Publication dates unverified';
  if (Number.isFinite(d.end))
    return `${d.start}–${d.end}${d.end_kind === 'title_change' ? ' · continued under a new title' : ''}`;
  return `${d.start} onward · end not verified`;
}

function journalDateBasis(j) {
  const d = j.date_span || {};
  const startWord = {publication_start: 'first issue',
    current_title_start: 'start of the current title'}[d.start_kind] || 'recorded start';
  return Number.isFinite(d.end)
    ? `Start read as ${startWord}; end recorded as ${(d.end_kind || 'unknown').replace(/_/g, ' ')}.`
    : `Start read as ${startWord}. No end is recorded, so the mark continues rather than `
      + 'stopping — an unverified end is not an ending.';
}

/* Atlas entries plus linked journals, in one addressable list. */
export function fieldNodes(graph) {
  return [...graph.nodes, ...journalNodes(graph).nodes];
}
export function fieldEdges(graph) {
  return [...graph.edges, ...journalNodes(graph).edges];
}
export function fieldKinds(graph) {
  const on = [...new Set(fieldEdges(graph).map(e => e.relationship_kind).filter(Boolean))];
  return [...BASE_KINDS.filter(k => on.includes(k)), ...on.filter(k => !BASE_KINDS.includes(k))];
}
export function fieldLayers(graph, titles) {
  const nodes = fieldNodes(graph);
  const used = new Set(nodes.map(n => n.layer));
  const preferred = Object.keys(titles).filter(id => used.has(id));
  const rest = [...(graph.layers || []).map(l => l.id), ...used]
    .filter(id => used.has(id) && !preferred.includes(id));
  return [...preferred, ...new Set(rest)];
}
export function relationIndex(graph) {
  const index = new Map(fieldNodes(graph).map(n => [n.id, []]));
  for (const edge of fieldEdges(graph)) {
    index.get(edge.source)?.push({edge, other: edge.target, dir: 'out'});
    index.get(edge.target)?.push({edge, other: edge.source, dir: 'in'});
  }
  return index;
}

/* ---------- layout ---------- */
const textW = (s, px = 11.5) => s.length * px * 0.545;
const clip = (s, n) => s.length > n ? s.slice(0, n - 1) + '…' : s;

export function buildFieldLayout(graph, width, focusSet, layerOrder) {
  const nodes = fieldNodes(graph);
  const rows = nodes.map(node => ({node, span: spanOf(node)}));
  const spans = rows.filter(r => r.span).map(r => r.span);
  const minYear = Math.min(1900, Math.floor(Math.min(...spans.map(s => s.start)) / 10) * 10);
  const maxYear = Math.max(2000, Math.ceil(Math.max(...spans.map(s => s.end)) / 10) * 10);
  const coverageYear = graph.scope?.main_period?.[1] ?? 2000;

  const undatedTotal = rows.filter(r => !r.span).length;
  const railW = undatedTotal ? G.railW : 0;
  const railGap = undatedTotal ? G.railGap : 0;
  const inner = Math.max(width - 2, 1060);
  const x0 = G.padL + railW + railGap, x1 = inner - G.padR;
  const W = x1 - x0;
  const early = BREAK_YEAR - minYear, late = maxYear - BREAK_YEAR;
  const scale = yr => yr <= BREAK_YEAR
    ? x0 + (early ? (yr - minYear) / early : 0) * W * EARLY_SHARE
    : x0 + W * EARLY_SHARE + (yr - BREAK_YEAR) / late * W * (1 - EARLY_SHARE);
  const colW = railW ? (railW - (G.railCols - 1) * G.chipGap) / G.railCols : 0;

  const axisTop = 14;
  let y = axisTop + 36;
  const bands = [], bars = [], chips = [], ghosts = [];

  for (const layerId of layerOrder) {
    const mine = rows.filter(r => r.node.layer === layerId);
    if (!mine.length) continue;
    const isFull = r => !focusSet || focusSet.has(r.node.id);
    const full = mine.filter(isFull), faded = mine.filter(r => !isFull(r));
    const labelY = y + 11;
    y += 26;
    const top = y;

    full.filter(r => !r.span).forEach((item, i) => {
      const col = i % G.railCols, row = Math.floor(i / G.railCols);
      chips.push({...item, shape: 'chip',
        label: clip(item.node.label, Math.max(6, Math.floor((colW - 18) / 6.05))),
        x: G.padL + col * (colW + G.chipGap), y: y + row * (G.chipH + G.chipGap),
        w: colW, h: G.chipH});
    });

    const rowEnds = [];
    for (const item of full.filter(r => r.span).sort((a, b) =>
        a.span.start - b.span.start || a.node.label.localeCompare(b.node.label))) {
      const bx = scale(item.span.start);
      const bw = Math.max(7, scale(item.span.end) - bx);
      const label = clip(item.node.label, 46);
      const contW = item.span.endKind === 'coverage_limit'
        ? Math.max(0, scale(item.span.coverage ?? coverageYear) - (bx + bw)) : 0;
      const fitsRight = bx + bw + contW + 7 + textW(label) <= x1;
      const fitsLeft = bx - textW(label) - 9 >= G.padL;
      const side = fitsRight ? 'right' : fitsLeft ? 'left' : 'inside';
      const need = side === 'left' ? bx - textW(label) - 9 : bx;
      const occupied = side === 'right' ? bx + bw + contW + 7 + textW(label) : bx + bw + contW;
      let r = rowEnds.findIndex(end => end + 16 <= need);
      if (r === -1) { r = rowEnds.length; rowEnds.push(0); }
      rowEnds[r] = occupied;
      bars.push({...item, shape: 'bar', label, side, contW, x: bx, w: bw, h: G.barH,
        y: y + r * (G.barH + G.rowGap)});
    }

    const fullH = Math.max(rowEnds.length * (G.barH + G.rowGap),
      Math.ceil(full.filter(r => !r.span).length / G.railCols) * (G.chipH + G.chipGap));
    let gy = y + fullH + (faded.length ? 6 : 0);
    const ghostEnds = [];
    for (const item of faded.sort((a, b) => (a.span?.start ?? 0) - (b.span?.start ?? 0))) {
      const bx = item.span ? scale(item.span.start) : G.padL;
      const bw = item.span ? Math.max(5, scale(item.span.end) - bx) : Math.max(40, colW);
      let r = ghostEnds.findIndex(end => end + 2 <= bx);
      if (r === -1) { r = ghostEnds.length; ghostEnds.push(0); }
      ghostEnds[r] = bx + bw;
      ghosts.push({...item, shape: 'ghost', x: bx, w: bw, h: G.ghostH,
        y: gy + r * (G.ghostH + G.ghostGap)});
    }
    const ghostH = ghostEnds.length * (G.ghostH + G.ghostGap);
    bands.push({layerId, labelY, top: top - 26, height: fullH + ghostH + 26,
      full: full.length, faded: faded.length});
    y += fullH + ghostH + (focusSet ? 18 : G.bandGap);
  }

  return {inner, scale, chips, bars, ghosts, bands, axisTop, x0, x1, railW, G,
    minYear, maxYear, coverageYear, breakYear: BREAK_YEAR, height: y + 14,
    placed: new Map([...chips, ...bars, ...ghosts].map(p => [p.node.id, p])),
    datedCount: rows.filter(r => r.span).length, undatedCount: undatedTotal};
}

export const anchor = p => ({x: p.x + p.w / 2, y: p.y + p.h / 2});
export const edgePath = (a, b) => {
  const m = (a.y + b.y) / 2;
  return `M${a.x},${a.y} C${a.x},${m} ${b.x},${m} ${b.x},${b.y}`;
};

export function focusSetFor(graph, id, index) {
  if (!id) return null;
  const keep = new Set([id]);
  for (const r of index.get(id) || []) keep.add(r.other);
  return keep;
}

/* Matching used by the field's search box: labels, prose, rosters and relationship text. */
export function fieldMatches(graph, index, personNames, id, query) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const n = fieldNodes(graph).find(x => x.id === id);
  if (!n) return false;
  const base = [n.label, n.description, n.representative_figures_and_works, n.date_label,
    n.entry_type].filter(Boolean).join(' ').toLowerCase();
  if (base.includes(q)) return true;
  if ((n.representative_people || []).some(r =>
    (personNames.get(r.person_id) || '').toLowerCase().includes(q))) return true;
  return (index.get(id) || []).some(r => r.edge.relationship.toLowerCase().includes(q));
}
