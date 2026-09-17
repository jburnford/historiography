/* The Field: every entry in the curated graph, in one time-spined picture.

   Two ideas do the work here:
   1. Focus re-lays out. Holding an entry collapses everything unrelated to a thin
      ghost mark and lets the entry and its relations expand into the freed space, so
      the connections are short and legible instead of fanning across empty rows.
   2. Dates stay honest. A curated `date_span` always wins; the prose parser below is
      a prototype stand-in for entries that do not yet carry one, and the panel says
      which was used. */

/* Known kinds render in this order; anything else the data carries is picked up at load
   and given a neutral treatment, so a new relationship_kind is never silently dropped. */
const BASE_KINDS = ['critique', 'contribution', 'influence', 'comparison'];
let KINDS = [...BASE_KINDS];

/* Preferred band order and display names. Neither is authoritative: the real order is
   derived from graph.layers at load, with any unlisted layer appended rather than skipped. */
const LAYER_PREFERRED = ['intellectual_traditions', 'historiographical_developments',
                         'intellectual_connections', 'enduring_fields_and_genres'];
const LAYER_RENAME = {
  intellectual_traditions: 'Intellectual traditions · earlier roots',
  historiographical_developments: 'Schools, approaches & expanding fields',
  intellectual_connections: 'Thinkers & intellectual connections',
  enduring_fields_and_genres: 'Enduring fields & genres',
};
let LAYER_ORDER = [...LAYER_PREFERRED];
const LAYER_TITLE = {...LAYER_RENAME};

function indexTaxonomy() {
  /* Every layer id that actually occurs on a node, in preferred order first. */
  const declared = (graph.layers || []).map(l => l.id);
  const onNodes = [...new Set(graph.nodes.map(n => n.layer))];
  const ordered = [...LAYER_PREFERRED.filter(id => onNodes.includes(id))];
  for (const id of [...declared, ...onNodes]) if (!ordered.includes(id)) ordered.push(id);
  LAYER_ORDER = ordered;
  for (const id of ordered) {
    if (LAYER_TITLE[id]) continue;
    LAYER_TITLE[id] = (graph.layers || []).find(l => l.id === id)?.label
      || id.replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
  }
  const onEdges = [...new Set(graph.edges.map(e => e.relationship_kind).filter(Boolean))];
  KINDS = [...BASE_KINDS.filter(k => onEdges.includes(k)),
           ...onEdges.filter(k => !BASE_KINDS.includes(k))];
}
/* The nineteenth-century roots are real but sparse. Compressing them keeps the
   twentieth century, where most of the map lives, readable. The break is drawn. */
const BREAK_YEAR = 1900, EARLY_SHARE = 0.2;
const G = {padL: 18, padR: 26, barH: 19, rowGap: 9, bandGap: 30, ghostH: 4, ghostGap: 3,
           chipH: 23, chipGap: 6, railW: 310, railCols: 2, railGap: 22};

let graph, nodeById, personById, relsByNode, placed;
let view = null, selected = null, hovered = null, emphEdge = null;
let query = '', showAll = false;
const kindOn = new Set(KINDS);

const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c =>
  ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const textW = (s, px = 11.5) => s.length * px * 0.545;
const clip = (s, n) => s.length > n ? s.slice(0, n - 1) + '…' : s;

/* ---------- dates ---------- */
function spanOf(node) {
  const d = node.date_span;
  if (d && Number.isFinite(d.start)) {
    return {start: d.start, end: Number.isFinite(d.end) ? d.end : d.start,
            endKind: d.end_kind || (d.open_end ? 'coverage_limit' : 'unstated'),
            coverage: Number.isFinite(d.coverage_through) ? d.coverage_through : null,
            precision: d.precision || 'year', curated: true, basis: d.basis || ''};
  }
  const parsed = parseSpan(node.date_label);
  return parsed && {...parsed, curated: false};
}

/* Returns {start, end, endKind, precision, coverage} or null when no span is stated.

   scope.notes[0]: "Dates describe approximate emergence or expansion, not termination."
   So a right edge is never a terminus unless the label says so. Three end states:
     terminus       — the label states an ending; draw a hard cap.
     coverage_limit — "coverage through YYYY" or "onward"; draw a continuation rail.
     unstated       — the record simply stops; draw a soft edge, claiming nothing. */
function parseSpan(label) {
  const s = label || '';
  /* Pull the coverage statement out first so it is never read as an end date. */
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
    start: Math.min(...found.map(f => f[0])),
    end: Math.max(...found.map(f => f[1])),
    endKind: endsExplicitly ? 'terminus' : continues ? 'coverage_limit' : 'unstated',
    coverage, precision,
  };
}

/* ---------- layout ---------- */
function buildLayout(width, focusSet) {
  const rows = graph.nodes.map(node => ({node, span: spanOf(node)}));
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

  for (const layerId of LAYER_ORDER) {
    const mine = rows.filter(r => r.node.layer === layerId);
    if (!mine.length) continue;
    const isFull = r => !focusSet || focusSet.has(r.node.id);
    const full = mine.filter(isFull), faded = mine.filter(r => !isFull(r));

    const labelY = y + 11;
    y += 26;
    const top = y;

    /* Rail: entries with no stated span, kept inside their own band. */
    full.filter(r => !r.span).forEach((item, i) => {
      const col = i % G.railCols, row = Math.floor(i / G.railCols);
      chips.push({...item, shape: 'chip',
        label: clip(item.node.label, Math.max(6, Math.floor((colW - 18) / 6.05))),
        x: G.padL + col * (colW + G.chipGap), y: y + row * (G.chipH + G.chipGap),
        w: colW, h: G.chipH});
    });

    /* Timeline: greedy packing that reserves room for each label. */
    const rowEnds = [];
    for (const item of full.filter(r => r.span)
        .sort((a, b) => a.span.start - b.span.start || a.node.label.localeCompare(b.node.label))) {
      const bx = scale(item.span.start);
      const bw = Math.max(7, scale(item.span.end) - bx);
      const label = clip(item.node.label, 46);
      const contW = item.span.endKind === 'coverage_limit'
        ? Math.max(0, scale(item.span.coverage ?? coverageYear) - (bx + bw)) : 0;
      const fitsRight = bx + bw + contW + 7 + textW(label) <= x1;
      const fitsLeft = bx - textW(label) - 9 >= G.padL;
      const side = fitsRight ? 'right' : fitsLeft ? 'left' : 'inside';
      const need = side === 'left' ? bx - textW(label) - 9 : bx;
      const occupied = side === 'right'
        ? bx + bw + contW + 7 + textW(label) : bx + bw + contW;
      let r = rowEnds.findIndex(end => end + 16 <= need);
      if (r === -1) { r = rowEnds.length; rowEnds.push(0); }
      rowEnds[r] = occupied;
      bars.push({...item, shape: 'bar', label, side, x: bx, w: bw, h: G.barH,
        contW,
        y: y + r * (G.barH + G.rowGap)});
    }

    const fullH = Math.max(rowEnds.length * (G.barH + G.rowGap),
      Math.ceil(full.filter(r => !r.span).length / G.railCols) * (G.chipH + G.chipGap));
    let gy = y + fullH + (faded.length ? 6 : 0);

    /* Ghosts: unrelated entries keep their place in time but surrender their space. */
    const ghostEnds = [];
    for (const item of faded.sort((a, b) =>
        (a.span?.start ?? 0) - (b.span?.start ?? 0))) {
      const bx = item.span ? scale(item.span.start) : G.padL;
      const bw = item.span ? Math.max(5, scale(item.span.end) - bx) : colW;
      let r = ghostEnds.findIndex(end => end + 2 <= bx);
      if (r === -1) { r = ghostEnds.length; ghostEnds.push(0); }
      ghostEnds[r] = bx + bw;
      ghosts.push({...item, shape: 'ghost', x: bx, w: bw, h: G.ghostH,
        y: gy + r * (G.ghostH + G.ghostGap)});
    }
    const ghostH = ghostEnds.length * (G.ghostH + G.ghostGap);

    bands.push({layerId, labelY, top: top - 26, height: fullH + ghostH + 26,
                full: full.length, faded: faded.length,
                undated: full.filter(r => !r.span).length});
    y += fullH + ghostH + (focusSet ? 18 : G.bandGap);
  }

  placed = new Map([...chips, ...bars, ...ghosts].map(p => [p.node.id, p]));
  return {inner, scale, chips, bars, ghosts, bands, axisTop, x0, x1, railW,
          minYear, maxYear, coverageYear, height: y + 14,
          datedCount: rows.filter(r => r.span).length, undatedCount: undatedTotal};
}

const anchor = p => ({x: p.x + p.w / 2, y: p.y + p.h / 2});

/* ---------- rendering ---------- */
function periodMarks() {
  /* Bounds are read from the period labels themselves ("c. 1945–70"), not invented. */
  return graph.periods.map(p => {
    const nums = (p.label.match(/\b(1[89]\d{2}|20\d{2})\b/g) || []).map(Number);
    if (nums.length === 2) return {...p, from: nums[0], to: nums[1]};
    if (nums.length === 1) return {...p, from: nums[0], to: nums[0] + 15};
    return {...p, from: view ? view.minYear : 1800, to: 1945, openLeft: true};
  });
}

function svgField() {
  const v = view, bottom = v.height;
  const washes = periodMarks().map((p, i) => {
    const a = v.scale(Math.max(p.from, v.minYear)), b = v.scale(Math.min(p.to, v.maxYear));
    const room = Math.max(3, Math.floor((b - a - 16) / 6.1));
    return `<rect class="period-wash ${i % 2 ? 'alt' : ''}" x="${a}" y="${v.axisTop}"
      width="${Math.max(0, b - a)}" height="${bottom - v.axisTop}"/>
      <text class="period-label" x="${a + 7}" y="${v.axisTop + 13}">${esc(
        clip(p.label.replace(/^[^·]*·\s*/, ''), room))}${p.openLeft ? ' ←' : ''}</text>`;
  }).join('');

  let grid = '';
  const tick = (yr, major) => {
    grid += `<line class="tick ${major ? 'major' : ''}" x1="${v.scale(yr)}"
      y1="${v.axisTop + 22}" x2="${v.scale(yr)}" y2="${bottom}"/>`;
    if (major) grid += `<text class="tick-label" x="${v.scale(yr)}" y="${v.axisTop + 34}"
      text-anchor="middle">${yr}</text>`;
  };
  for (let yr = Math.ceil(v.minYear / 25) * 25; yr < BREAK_YEAR; yr += 25) tick(yr, true);
  for (let yr = BREAK_YEAR; yr <= v.maxYear; yr += 10) tick(yr, yr % 20 === 0);
  /* Mark the change of scale rather than letting it pass unannounced. */
  const wx = v.scale(v.coverageYear);
  grid += `<line class="coverage-wall" x1="${wx}" y1="${v.axisTop + 16}" x2="${wx}" y2="${bottom}"/>
    <text class="coverage-label" x="${wx - 6}" y="${bottom - 6}" text-anchor="end"
      >curated coverage ends ${v.coverageYear}</text>`;
  const bx = v.scale(BREAK_YEAR);
  grid += `<line class="scale-break" x1="${bx}" y1="${v.axisTop + 16}" x2="${bx}" y2="${bottom}"/>`;

  const railHead = v.railW ? `<text class="rail-head" x="${G.padL}" y="${v.axisTop + 13}">
    No span stated · ${v.undatedCount}</text>
    <line class="rail-rule" x1="${v.x0 - G.railGap / 2}" y1="${v.axisTop + 14}"
      x2="${v.x0 - G.railGap / 2}" y2="${bottom}"/>` : '';

  const bandLabels = v.bands.map(b => `<line class="band-rule" x1="${G.padL}"
      y1="${b.labelY - 13}" x2="${v.x1}" y2="${b.labelY - 13}"/>
    <text class="band-label" x="${v.x0}" y="${b.labelY}">${esc(LAYER_TITLE[b.layerId])}</text>
    <text class="band-count" x="${v.x1}" y="${b.labelY}" text-anchor="end">${
      b.faded ? `${b.full} shown · ${b.faded} set aside` : `${b.full} entries`}</text>`).join('');

  const chips = v.chips.map(p => `<g class="chip" data-id="${esc(p.node.id)}" tabindex="0"
      role="button" aria-label="${esc(p.node.label)}, no date span stated">
      <rect class="chip-shape" x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"/>
      <text class="chip-label" x="${p.x + 10}" y="${p.y + p.h / 2 + 1}">${esc(p.label)}</text>
    </g>`).join('');

  const ghosts = v.ghosts.map(p => `<rect class="ghost" data-id="${esc(p.node.id)}"
      x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="2"
      ><title>${esc(p.node.label)} · ${esc(p.node.date_label)}</title></rect>`).join('');

  const bars = v.bars.map(p => {
    const fuzzy = p.span.precision === 'decade';
    const y0 = p.y, h = p.h, xEnd = p.x + p.w;
    /* A tapering tail says "still present, less salient" — it cannot be misread as
       an ending the way a second hard edge can. */
    const tail = p.contW > 2 ? `<path class="bar-tail" d="M${xEnd},${y0}
      L${xEnd + p.contW},${y0 + (h - 2.5) / 2} L${xEnd + p.contW},${y0 + (h + 2.5) / 2}
      L${xEnd},${y0 + h} Z"/>` : '';
    const endCap = p.span.endKind === 'terminus'
      ? `<line class="bar-cap end" x1="${xEnd}" y1="${y0}" x2="${xEnd}" y2="${y0 + h}"/>` : '';
    return `<g class="entry end-${esc(p.span.endKind)}" data-id="${esc(p.node.id)}"
      tabindex="0" role="button"
      aria-label="${esc(p.node.label)}, ${esc(p.node.date_label)}">
      ${tail}
      <rect class="bar-shape ${p.node.entry_kind === 'person' ? 'person' : ''}"
        x="${p.x}" y="${y0}" width="${p.w}" height="${h}"
        ${fuzzy ? 'fill-opacity="0.62"' : ''} rx="3"/>
      <line class="bar-cap start" x1="${p.x}" y1="${y0}" x2="${p.x}" y2="${y0 + h}"/>
      ${endCap}
      <text class="bar-label ${p.side}" y="${y0 + h / 2 + 1}"
        x="${p.side === 'right' ? xEnd + Math.max(p.contW, 0) + 7
            : p.side === 'left' ? p.x - 7 : p.x + 9}"
        ${p.side === 'left' ? 'text-anchor="end"' : ''}>${esc(p.label)}</text>
    </g>`;
  }).join('');

  return `<svg class="field" width="${v.inner}" height="${v.height}"
      viewBox="0 0 ${v.inner} ${v.height}">
    <defs><linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#9fae9e" stop-opacity=".7"/>
      <stop offset="1" stop-color="#9fae9e" stop-opacity="0"/>
    </linearGradient></defs>
    <g class="chrome">${washes}${grid}
      <line class="axis-line" x1="${v.x0}" y1="${v.axisTop + 22}" x2="${v.x1}"
        y2="${v.axisTop + 22}"/>${railHead}${bandLabels}</g>
    <g class="ghosts">${ghosts}</g>
    <g id="edges"></g>
    ${chips}${bars}
  </svg>`;
}

/* ---------- edges ---------- */
const edgePath = (a, b) => {
  const m = (a.y + b.y) / 2;
  return `M${a.x},${a.y} C${a.x},${m} ${b.x},${m} ${b.x},${b.y}`;
};

function drawEdges() {
  const box = $('edges');
  if (!box) return;
  const focus = hovered || selected;
  const solo = showAll && kindOn.size === 1 ? ' solo' : '';
  const rows = showAll ? graph.edges.map(e => ({e, faint: true}))
    : focus ? (relsByNode.get(focus) || []).map(r => ({e: r.edge, faint: false})) : [];

  box.innerHTML = rows.filter(({e}) => kindOn.has(e.relationship_kind)).map(({e, faint}) => {
    const s = placed.get(e.source), t = placed.get(e.target);
    if (!s || !t) return '';
    const emph = emphEdge === e.id ? 'emph' : emphEdge ? 'mute' : '';
    const kindClass = BASE_KINDS.includes(e.relationship_kind)
      ? e.relationship_kind : 'unknown-kind';
    return `<path class="edge ${kindClass} ${faint ? 'faint' + solo : ''} ${emph}"
      d="${edgePath(anchor(s), anchor(t))}"/>`;
  }).join('');

  const related = new Set();
  if (focus) for (const r of relsByNode.get(focus) || [])
    if (kindOn.has(r.edge.relationship_kind)) related.add(r.other);

  document.querySelector('svg.field')?.classList.toggle('focused', Boolean(focus || showAll));
  for (const el of document.querySelectorAll('.entry, .chip')) {
    const id = el.dataset.id;
    el.classList.toggle('selected', id === selected);
    el.classList.toggle('related', related.has(id) && id !== selected);
    el.classList.toggle('dimmed', Boolean(focus) && !related.has(id) && id !== focus);
  }
  applyQuery();
}

function applyQuery() {
  const q = query.trim().toLowerCase();
  for (const el of document.querySelectorAll('.entry, .chip')) {
    const hit = Boolean(q) && matches(el.dataset.id, q);
    el.classList.toggle('hit', hit);
    if (q) el.classList.toggle('dimmed', !hit);
  }
}

function matches(id, q) {
  const n = nodeById.get(id);
  if (!n) return false;
  if ((n.label + ' ' + n.description + ' ' + (n.representative_figures_and_works || ''))
      .toLowerCase().includes(q)) return true;
  if ((n.representative_people || []).some(r =>
      (personById.get(r.person_id)?.label || '').toLowerCase().includes(q))) return true;
  return (relsByNode.get(id) || []).some(r => r.edge.relationship.toLowerCase().includes(q));
}



/* ---------- journal catalogue ---------- */
/* Journals live in a parallel sub-graph (`journal_catalogue`) with its own nodes and a
   small set of evidenced venue edges. The catalogue is a discovery inventory — 1,676
   periodicals as of 1.106 — so it is NOT map content. Only journals carrying at least
   one visual edge are promoted onto the field; the rest stay searchable but unplaced.
   Astra's policy: "Only specific founding, debate and sustained principal-venue claims
   are visual edges." */
const JOURNAL_LAYER = 'journals_and_venues';
let journalById = new Map(), unlinkedJournals = [];

function mergeJournalCatalogue() {
  const jc = graph.journal_catalogue;
  if (!jc?.nodes?.length) return;
  journalById = new Map(jc.nodes.map(n => [n.id, n]));
  const linked = new Set();
  for (const e of jc.edges || []) {
    if (!journalById.has(e.source) || !graph.nodes.some(n => n.id === e.target)) continue;
    linked.add(e.source);
  }
  if (linked.size) {
    graph.layers = [...(graph.layers || []),
      {id: JOURNAL_LAYER, label: 'Journals & venues'}];
  }
  for (const id of linked) {
    const j = journalById.get(id);
    const d = j.date_span;
    graph.nodes.push({
      id, label: j.label, layer: JOURNAL_LAYER, entry_kind: 'periodical',
      entry_type: 'Journal or periodical', period: null, hunt_core_paradigm: false,
      date_label: journalDateLabel(j),
      /* Publication start is a fact; an unverified end is not an ending. */
      date_span: d && Number.isFinite(d.start) ? {
        start: d.start, end: Number.isFinite(d.end) ? d.end : null,
        precision: d.precision || 'year',
        end_kind: d.end === null || d.end === undefined ? 'coverage_limit' : d.end_kind,
        basis: journalDateBasis(j), source_ids: d.source_ids || [],
      } : undefined,
      description: j.mapping_note
        || 'A periodical linked to this map by an evidenced founding or debate claim.',
      representative_figures_and_works: '',
      scope_note: j.chronology_note || '',
      source_ids: j.source_ids || [],
    });
  }
  for (const e of jc.edges || []) {
    if (!linked.has(e.source)) continue;
    graph.edges.push({
      id: e.id, source: e.source, target: e.target,
      relationship: e.relationship, relationship_kind: e.relationship_kind,
      type: 'connection', directed: true,
      source_ids: e.source_ids || [], evidence_note: e.evidence_note || '',
    });
  }
  unlinkedJournals = jc.nodes.filter(n => !linked.has(n.id));
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
                     current_title_start: 'start of the current title'}[d.start_kind]
                     || 'recorded start';
  return Number.isFinite(d.end)
    ? `Start read as ${startWord}; end recorded as ${(d.end_kind || 'unknown').replace(/_/g, ' ')}.`
    : `Start read as ${startWord}. No end is recorded, so the mark continues rather than `
      + `stopping — an unverified end is not an ending.`;
}

/* ---------- taxonomy-driven legend ---------- */
const KIND_LABEL = k => k.replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());

function buildKindLegend() {
  const box = document.getElementById('kind-legend');
  if (!box) return;
  const counts = new Map();
  for (const e of graph.edges)
    counts.set(e.relationship_kind, (counts.get(e.relationship_kind) || 0) + 1);
  kindOn.clear();
  box.innerHTML = '<strong>Relationships</strong>' + KINDS.map(k => {
    kindOn.add(k);
    const known = BASE_KINDS.includes(k);
    return `<button class="kind k-${k}${known ? '' : ' k-unknown'}" data-kind="${k}"
      aria-pressed="true"${known ? '' : ' title="Not one of the four curated kinds — '
        + 'shown in a neutral style until it is given one."'}><i></i>${KIND_LABEL(k)}
      <em>${counts.get(k) || 0}</em></button>`;
  }).join('');
}

/* Nothing may be counted that is not drawn. If layout loses a record, say so. */
function reconcile() {
  const missing = graph.nodes.filter(n => !placed.has(n.id));
  const banner = document.getElementById('notice');
  if (!banner) return;
  if (!missing.length) { banner.hidden = true; banner.textContent = ''; return; }
  banner.hidden = false;
  banner.textContent = `${missing.length} entr${missing.length === 1 ? 'y is' : 'ies are'} `
    + `in the data but not drawn: ${missing.slice(0, 5).map(n => n.label).join(', ')}`
    + `${missing.length > 5 ? '…' : ''}. This is a rendering fault, not a data fault.`;
}

/* ---------- detail panel ---------- */
const DIR = {
  critique: {out: 'criticises', in: 'is criticised by'},
  contribution: {out: 'contributes to', in: 'draws a contribution from'},
  influence: {out: 'influences', in: 'is influenced by'},
  comparison: {out: 'compared with', in: 'compared with'},
};
/* An unfamiliar kind still gets readable direction wording. */
const dirWord = (kind, dir) => DIR[kind]?.[dir]
  || `${KIND_LABEL(kind).toLowerCase()} ${dir === 'out' ? '→' : '←'}`;

function panelFor(id) {
  const n = nodeById.get(id);
  const span = spanOf(n);
  const rels = relsByNode.get(id) || [];

  const block = (kind, title) => {
    const items = rels.filter(r => r.edge.relationship_kind === kind);
    if (!items.length) return '';
    return `<section class="sec"><h3>${title} · ${items.length}</h3>${items.map(r => `
      <button class="rel ${kind}" data-goto="${esc(r.other)}" data-edge="${esc(r.edge.id)}">
        <span class="dir">${esc(dirWord(kind, r.dir))}</span>
        <span class="who">${esc(nodeById.get(r.other).label)}</span>
        <span class="what">${esc(r.edge.relationship)}</span>
      </button>`).join('')}</section>`;
  };

  const people = n.representative_people || [];
  return `<p class="eyebrow">${esc(n.entry_type || 'Entry')}</p>
    <h2>${esc(n.label)}</h2>
    <p class="meta">${esc(n.date_label || 'No date label')} · ${esc(LAYER_TITLE[n.layer])}</p>
    <div class="datewhy">${span ? `
      ${n.entry_kind === 'periodical'
        ? `<strong>First issue ${span.start}</strong>${Number.isFinite(span.end)
             && span.end > span.start ? `, running to ${span.end}` : ''}.`
        : `<strong>Arrived ${span.start}</strong>${span.end > span.start
             ? `, most influential through ${span.end}` : ''}${span.precision === 'decade'
             ? ' (decade precision)' : ''}.`}
      ${span.endKind === 'terminus'
        ? 'An ending is recorded, so the mark is capped.'
        : span.endKind === 'title_change'
          ? 'The title changed here. The periodical did not cease; it continued under a new name.'
          : span.endKind === 'coverage_limit'
            ? `The tail runs to ${span.coverage ?? view.coverageYear}, where this atlas stops —
               not to an ending. ${n.entry_kind === 'periodical'
                 ? 'No cessation is recorded for this periodical.'
                 : 'The field continues beyond what is mapped here.'}`
            : 'The record simply stops here. The soft edge claims no ending.'}
      <br><span class="prov">${span.curated
        ? `From the curated <code>date_span</code>. ${esc(span.basis)}`
        : `Read by the prototype from <code>${esc(n.date_label)}</code>.`}</span></div>`
      : `<strong>No span stated.</strong> <code>${esc(n.date_label)}</code> names people or
         methods rather than years, so it waits in the rail rather than being given a
         date it does not claim.</div>`}
    <p class="claim">${esc(n.description)}</p>
    ${n.scope_note ? `<div class="scope"><strong>Scope &amp; distinctions.</strong>
      ${esc(n.scope_note)}</div>` : ''}
    ${KINDS.map(k => block(k, ({critique: 'Disagreements', contribution: 'Contributions',
      influence: 'Influence', comparison: 'Comparisons'})[k] || KIND_LABEL(k))).join('')}
    ${people.length ? `<section class="sec"><h3>Historians &amp; contributors · ${people.length}</h3>
      <div class="people">${people.slice(0, 24).map(r =>
        `<span>${esc(personById.get(r.person_id)?.label || r.person_id)}</span>`).join('')}</div>
      ${people.length > 24 ? `<p class="note">+ ${people.length - 24} more</p>` : ''}
      </section>` : ''}
    <section class="sec"><h3>References</h3><p class="note">${n.source_ids.length} records in
      the entry bibliography. A full view would summarise verification here rather than
      repeating a disclosure control for every item.</p></section>`;
}

let emptyPanel = '';

function renderPanel() {
  const id = hovered || selected;
  const panel = $('panel');
  if (!id) { panel.classList.remove('previewing'); panel.innerHTML = emptyPanel; return; }
  const preview = Boolean(hovered && selected && hovered !== selected);
  panel.classList.toggle('previewing', preview);
  panel.innerHTML = (preview
    ? `<p class="preview-flag">Previewing · <strong>${esc(nodeById.get(selected).label)}</strong>
       stays held. Click to switch.</p>` : '') + panelFor(id);
}

/* ---------- interaction ---------- */
/* Only a selection re-lays out. Hover merely lights edges, so the ground does not
   move under the pointer. */
function focusSetFor(id) {
  if (!id) return null;
  const keep = new Set([id]);
  for (const r of relsByNode.get(id) || []) keep.add(r.other);
  return keep;
}

function select(id) {
  selected = id === selected ? null : id;
  hovered = emphEdge = null;
  draw();
  renderPanel();
  const p = selected && placed.get(selected);
  if (p) $('field').scrollTo(
    {top: Math.max(0, p.y - $('field').clientHeight / 2), behavior: 'smooth'});
}

function wire() {
  const wrap = $('field');
  const enter = e => {
    const g = e.target.closest('.entry, .chip');
    if (!g || g.dataset.id === hovered) return;
    hovered = g.dataset.id; drawEdges(); renderPanel();
  };
  wrap.addEventListener('mouseover', enter);
  wrap.addEventListener('focusin', enter);
  wrap.addEventListener('mouseleave', () => { hovered = null; drawEdges(); renderPanel(); });
  wrap.addEventListener('click', e => {
    const g = e.target.closest('.entry, .chip, .ghost');
    select(g ? g.dataset.id : null);
  });
  wrap.addEventListener('keydown', e => {
    const g = e.target.closest('.entry, .chip');
    if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); select(g.dataset.id); }
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    selected = hovered = emphEdge = null; draw(); renderPanel();
  });
  const panel = $('panel');
  panel.addEventListener('mouseover', e => {
    const r = e.target.closest('[data-edge]');
    const id = r ? r.dataset.edge : null;
    if (id !== emphEdge) { emphEdge = id; drawEdges(); }
  });
  panel.addEventListener('mouseleave', () => { emphEdge = null; drawEdges(); });
  panel.addEventListener('click', e => {
    const b = e.target.closest('[data-goto]');
    if (b) select(b.dataset.goto);
  });
  $('q').addEventListener('input', e => { query = e.target.value; drawEdges(); });
  $('reset').addEventListener('click', () => {
    query = ''; $('q').value = '';
    selected = hovered = emphEdge = null;
    showAll = false; $('show-all').checked = false;
    draw(); renderPanel();
  });
  $('show-all').addEventListener('change', e => { showAll = e.target.checked; drawEdges(); });
  for (const b of document.querySelectorAll('.kind')) {
    b.addEventListener('click', () => {
      const k = b.dataset.kind;
      kindOn.has(k) ? kindOn.delete(k) : kindOn.add(k);
      b.setAttribute('aria-pressed', String(kindOn.has(k)));
      drawEdges();
    });
  }
  let t;
  addEventListener('resize', () => { clearTimeout(t); t = setTimeout(draw, 180); });
}

function draw() {
  view = buildLayout($('field').clientWidth, focusSetFor(selected));
  $('field').innerHTML = svgField();
  drawEdges();
  reconcile();
}

/* ---------- start ---------- */
(async function start() {
  try {
    graph = await (await fetch('data/graph.json')).json();
    mergeJournalCatalogue();
    nodeById = new Map(graph.nodes.map(n => [n.id, n]));
    personById = new Map(graph.people.map(p => [p.id, p]));
    relsByNode = new Map(graph.nodes.map(n => [n.id, []]));
    for (const edge of graph.edges) {
      relsByNode.get(edge.source)?.push({edge, other: edge.target, dir: 'out'});
      relsByNode.get(edge.target)?.push({edge, other: edge.source, dir: 'in'});
    }
    indexTaxonomy();
    buildKindLegend();
    emptyPanel = $('panel').innerHTML;
    $('rev').textContent = `revision ${graph.revision_history.at(-1).version}`;
    draw();
    $('counts').textContent = `${view.datedCount} placed in time · ` +
      `${view.undatedCount} without a stated span · ${graph.edges.length} relationships`
      + (unlinkedJournals.length
        ? ` · ${unlinkedJournals.length.toLocaleString()} catalogued periodicals not yet linked`
        : '');
    wire();
  } catch (err) {
    $('field').innerHTML = `<p class="loading">Could not open the graph: ${esc(err.message)}.
      Run <code>python3 prototype/build.py</code> and serve <code>prototype/dist</code>.</p>`;
  }
})();
