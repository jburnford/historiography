/* The Field: every atlas entry on one time axis, with journals that carry an evidenced
   venue relation. Pure functions — layout and markup only; app.js owns events and routing.

   Two ideas do the work:
   1. Focus re-lays out. Holding an entry collapses everything unrelated to a thin ghost
      mark so the entry and its relations expand into the freed space.
   2. Dates stay honest. A mark runs across the years its date label names. A label that
      says "onward" or "coverage through 2000" is drawn solid to the atlas's coverage wall
      with an open, fading end: the wall is a limit of the map, never an ending. Nothing in
      the drawing claims a period of peak influence. A curated `date_span` always wins over
      the prose parse, and the panel says which was used. See scope.notes: "Dates describe
      approximate emergence or expansion, not termination." */

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
const G = {padL: 18, padR: 26, barH: 18, rowGap: 8, bandGap: 30, ghostH: 4, ghostGap: 3,
           chipH: 22, chipGap: 6, minW: 600};

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
/* A curated short label wins on the field; the full label stays everywhere else. */
export const displayLabel = n => n.short_label || n.label;

/* Years named in a date label. Parsed from prose, so they are drawn as unlabelled ticks
   and described as read by the site, never as curated milestones. */
export function milestoneYears(node) {
  const s = (node.date_label || '').replace(/coverage through\s+\d{4}/i, ' ');
  return [...new Set((s.match(/\b(1[6-9]\d{2}|20[0-2]\d)\b(?!s)/g) || []).map(Number))]
    .sort((a, b) => a - b);
}

/* `width` is the width of the box the SVG will actually sit in — measure it, do not guess
   from the page. `opts.numbering` (Map id → n) prefixes labels for the pathway overlay. */
export function buildFieldLayout(graph, width, focusSet, layerOrder, opts = {}) {
  const numbering = opts.numbering || null;
  const nodes = fieldNodes(graph);
  const rows = nodes.map(node => ({node, span: spanOf(node)}));
  const spans = rows.filter(r => r.span).map(r => r.span);
  const minYear = Math.min(1900, Math.floor(Math.min(...spans.map(s => s.start)) / 10) * 10);
  const maxYear = Math.max(2000, Math.ceil(Math.max(...spans.map(s => s.end)) / 10) * 10);
  const coverageYear = graph.scope?.main_period?.[1] ?? 2000;

  const undatedTotal = rows.filter(r => !r.span).length;
  const inner = Math.max(Math.floor(width) - 2, G.minW);
  const x0 = G.padL + 6, x1 = inner - G.padR;
  const W = x1 - x0;
  const early = BREAK_YEAR - minYear, late = maxYear - BREAK_YEAR;
  const scale = yr => yr <= BREAK_YEAR
    ? x0 + (early ? (yr - minYear) / early : 0) * W * EARLY_SHARE
    : x0 + W * EARLY_SHARE + (yr - BREAK_YEAR) / late * W * (1 - EARLY_SHARE);
  const labelOf = node => {
    const base = clip(displayLabel(node), 46);
    const n = numbering?.get(node.id);
    return n ? `${n}. ${base}` : base;
  };

  const axisTop = 14;
  let y = axisTop + 40;
  const bands = [], bars = [], chips = [], ghosts = [], captions = [];

  for (const layerId of layerOrder) {
    const mine = rows.filter(r => r.node.layer === layerId);
    if (!mine.length) continue;
    const isFull = r => !focusSet || focusSet.has(r.node.id);
    const full = mine.filter(isFull), faded = mine.filter(r => !isFull(r));
    const labelY = y + 11;
    y += 26;
    const top = y;

    /* Entries with no stated span sit in a wrapping strip at the top of their band, so the
       time axis keeps the whole width instead of giving a fifth of it to a rail. */
    const undated = full.filter(r => !r.span);
    let cx = x0, cy = y, chipRows = 0;
    if (undated.length) {
      const caption = `No span stated · ${undated.length}`;
      captions.push({x: x0, y: cy + G.chipH / 2 + 1, text: caption});
      cx = x0 + textW(caption, 10) + 14;
      chipRows = 1;
    }
    for (const item of undated) {
      const label = clip(displayLabel(item.node), 40);
      const w = Math.min(240, Math.round(textW(label, 11) + 22));
      if (cx + w > x1 && cx > x0) { cx = x0; cy += G.chipH + G.chipGap; chipRows++; }
      chips.push({...item, shape: 'chip', label, x: cx, y: cy, w, h: G.chipH});
      cx += w + G.chipGap;
    }
    const chipBlock = chipRows ? chipRows * (G.chipH + G.chipGap) + 4 : 0;
    const barTop = y + chipBlock;

    const rowEnds = [];
    for (const item of full.filter(r => r.span).sort((a, b) =>
        a.span.start - b.span.start || a.node.label.localeCompare(b.node.label))) {
      const bx = scale(item.span.start);
      /* An open-ended label is drawn solid to the coverage wall; the wall is the map's limit. */
      const open = item.span.endKind === 'coverage_limit';
      const drawEnd = open ? (item.span.coverage ?? coverageYear) : item.span.end;
      const point = drawEnd === item.span.start;
      const bw = Math.max(point ? 12 : 7, scale(drawEnd) - bx);
      const label = labelOf(item.node);
      const fitsRight = bx + bw + 7 + textW(label) <= x1;
      const fitsLeft = bx - textW(label) - 9 >= G.padL;
      const side = fitsRight ? 'right' : fitsLeft ? 'left' : 'inside';
      const need = side === 'left' ? bx - textW(label) - 9 : bx;
      const occupied = side === 'right' ? bx + bw + 7 + textW(label) : bx + bw;
      let r = rowEnds.findIndex(end => end + 16 <= need);
      if (r === -1) { r = rowEnds.length; rowEnds.push(0); }
      rowEnds[r] = occupied;
      const ticks = milestoneYears(item.node)
        .filter(yr => yr > item.span.start && yr <= drawEnd).map(yr => ({yr, x: scale(yr)}));
      bars.push({...item, shape: 'bar', label, side, contW: 0, open, drawEnd, point, ticks,
        x: bx, w: bw, h: G.barH, y: barTop + r * (G.barH + G.rowGap)});
    }

    const fullH = chipBlock + rowEnds.length * (G.barH + G.rowGap);
    let gy = y + fullH + (faded.length ? 6 : 0);
    const ghostEnds = [];
    for (const item of faded.sort((a, b) => (a.span?.start ?? 0) - (b.span?.start ?? 0))) {
      const bx = item.span ? scale(item.span.start) : x0;
      const ghostEnd = item.span?.endKind === 'coverage_limit'
        ? (item.span.coverage ?? coverageYear) : item.span?.end;
      const bw = item.span ? Math.max(5, scale(ghostEnd) - bx) : 40;
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

  return {inner, scale, chips, bars, ghosts, bands, captions, axisTop, x0, x1, G,
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

/* A seminar pathway as a set of field entries, and the relationships recorded among them.
   Order is a reading sequence, not a genealogy, so no edge is inferred from adjacency. */
export function pathwaySet(pathway) {
  return pathway ? new Set(pathway.node_ids) : null;
}
export function pathwayEdges(graph, pathway, index) {
  const set = pathwaySet(pathway);
  if (!set) return [];
  const seen = new Set(), out = [];
  for (const id of pathway.node_ids) for (const r of index.get(id) || [])
    if (set.has(r.other) && !seen.has(r.edge.id)) { seen.add(r.edge.id); out.push(r.edge); }
  return out;
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
