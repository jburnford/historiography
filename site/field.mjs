/* The Field: every atlas entry on one time axis, with journals that carry an evidenced
   venue relation. Pure functions — layout and markup only; app.js owns events and routing.

   Two ideas do the work:
   1. Focus re-lays out. Holding an entry collapses everything unrelated to a thin ghost
      mark so the entry and its relations expand into the freed space.
   2. Current dates come from explicit graph chronology: selected events, supported
      intervals and editorial coverage remain distinct. The frozen archive alone
      follows legacy date labels and curated date_span values. Neither a selection
      extent nor a review year establishes historical duration or peak influence. */

import {chronologyOf, chronologySpan, chronologyGeometry, chronologyEvents} from './chronology.mjs';

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
/* The axis never starts before 1750 (user, 2026-10-17). Earlier dated events (Guaman Poma, ancient
   precursors) sit at the left edge as 'before 1750' marks with their real dates in titles and panels. */
export const AXIS_FLOOR = 1750;
const G_FULL = {padL: 18, padR: 26, barH: 18, rowGap: 8, bandGap: 30, ghostH: 4, ghostGap: 3,
           chipH: 22, chipGap: 6, minW: 600, bandHead: 26, axisGap: 40, clipAt: 46};
/* The person-profile map: the same layout at a compact density, one band, no ghosts. */
const G_COMPACT = {...G_FULL, padL: 10, padR: 14, barH: 13, rowGap: 9, bandGap: 4, chipH: 18, chipGap: 5,
                   minW: 520, bandHead: 0, axisGap: 30, clipAt: 48, stackGap: 15, stackMinW: 280};

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
  /* "1939–40", "1900–20": a two-digit end shares the start's century. */
  for (let m, re = /\b(1[6-9]\d{2}|20[0-2]\d)\s*[–—-]\s*(\d{2})\b(?!\d)/g; (m = re.exec(body));) {
    const a = +m[1], b = Math.floor(a / 100) * 100 + +m[2];
    if (b > a) found.push([a, b]);
  }
  if (!found.length) return null;
  const endsExplicitly = /\bended\b|\bends\b|\buntil\b|\bceased\b|\bclosed\b|\bdisbanded\b/i.test(body);
  /* "expanding postwar reception" and the like say the thing carried on. */
  const continues = coverage !== null || /onward|present|continu|ongoing|later\b|expanding|reception/i.test(body);
  /* "Earlier roots · Howard 1961 …" names undated roots before its first year: the first
     dated year is a contribution to an established field, not an origin. "1800s roots" is
     dated and is not open. */
  const openStart = /^\s*(earlier|ancient|older)\b/i.test(body);
  return {
    start: Math.min(...found.map(f => f[0])), end: Math.max(...found.map(f => f[1])),
    endKind: endsExplicitly ? 'terminus' : continues ? 'coverage_limit' : 'unstated',
    openStart, coverage, precision, curated: false,
  };
}

export function spanOf(node) {
  if (chronologyOf(node)) return chronologySpan(node);
  const d = node.date_span;
  if (d && Number.isFinite(d.start)) {
    const end = Number.isFinite(d.end) ? d.end : null;
    return {
      start: d.start, end: end ?? d.start,
      /* An unverified end is not an ending: continue rather than stop. */
      endKind: end === null || d.end_kind === 'open' ? 'coverage_limit' : (d.end_kind || 'unstated'),
      coverage: Number.isFinite(d.coverage_through) ? d.coverage_through : null,
      precision: d.precision || 'year', curated: true,
      basis: d.basis || '', startKind: d.start_kind || '',
      openStart: ['earlier_roots', 'undated_roots', 'open'].includes(d.start_kind),
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
    const dated = d && Number.isFinite(d.start);
    /* No publication dates in the catalogue: fall back to the earliest evidenced venue role,
       say so, and let the mark run to the coverage limit (an unverified end is not an ending). */
    const roleStart = dated ? null : Math.min(...edges.filter(e => e.source === id)
      .map(e => e.temporal_scope?.start).filter(Number.isFinite));
    const viaRole = !dated && Number.isFinite(roleStart);
    return {
      id, label: j.label, layer: JOURNAL_LAYER, entry_kind: 'periodical',
      ...(j.chronology ? {chronology: j.chronology} : {}),
      entry_type: 'Journal or periodical', period: null, hunt_core_paradigm: false,
      date_label: viaRole ? `Publication dates unverified · venue role evidenced from ${roleStart}`
        : journalDateLabel(j),
      date_span: dated ? {
        start: d.start, end: Number.isFinite(d.end) ? d.end : null,
        precision: d.precision || 'year',
        end_kind: Number.isFinite(d.end) ? d.end_kind : 'coverage_limit',
        start_kind: d.start_kind || '', basis: journalDateBasis(j),
      } : viaRole ? {
        start: roleStart, end: null, precision: 'year', end_kind: 'coverage_limit',
        start_kind: 'venue_role_start',
        basis: `The catalogue records no publication dates for this title. The mark begins at ${roleStart}, `
          + 'the earliest evidenced venue role, not the first issue, and runs to the coverage limit '
          + 'because no cessation is recorded.',
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
  if (chronologyOf(node)) return [...new Set(chronologyEvents(node).flatMap(e => e.bounds))].sort((a, b) => a - b);
  const s = (node.date_label || '').replace(/coverage through\s+\d{4}/i, ' ');
  return [...new Set((s.match(/\b(1[6-9]\d{2}|20[0-2]\d)\b(?!s)/g) || []).map(Number))]
    .sort((a, b) => a - b);
}

/* `width` is the width of the box the SVG will actually sit in — measure it, do not guess
   from the page. `opts.numbering` (Map id → n) prefixes labels for the pathway overlay. */
/* The frame the field is drawn in. Open graphs (revision 1.133 on) have no wall: the axis runs
   to the end of the year holding the research cutoff. Legacy graphs, such as the archived 1.121
   view, carry a numeric main_period end and keep it as their wall. */
export function frameOf(graph) {
  const s = graph.scope || {};
  const legacyWall = Number.isFinite(s.main_period?.[1]) ? s.main_period[1] : null;
  if (!s.frame && legacyWall !== null) return {open: false, start: s.main_period[0], end: legacyWall, cutoff: null, wall: legacyWall};
  const d = s.frame?.research_cutoff ? new Date(s.frame.research_cutoff) : new Date();
  const cutoff = d.getUTCFullYear() + (d.getUTCMonth() + 0.5) / 12;
  return {open: true, start: s.frame?.start ?? 1920, end: Math.ceil(cutoff), cutoff, wall: null};
}
export const reviewedThrough = node => node.coverage?.reviewed_through ?? null;

/* Selected interventions after the coverage limit. The atlas's curated marks stop at their own
   recorded coverage; an extension adds dated points for the works a later release selected,
   on the entry's own row, and stretches only the axis. Nothing else is extended. */
export function extensionOf(graph) {
  if (frameOf(graph).open) return null;
  const ext = graph.scope?.extension;
  if (!ext?.proposed_view_period) return null;
  const cutoff = ext.research_cutoff ? (() => { const d = new Date(ext.research_cutoff);
    return d.getUTCFullYear() + (d.getUTCMonth() + 0.5) / 12; })() : null;
  const covered = graph.nodes.filter(n => n.extension_coverage?.publication_years?.length);
  /* The axis runs to the end of the year that holds the research cutoff, so the cutoff is drawn
     where it falls rather than clipped to the view period. */
  const end = Math.max(ext.proposed_view_period[1], cutoff ? Math.ceil(cutoff) : 0);
  return {end, start: graph.scope.main_period[1], cutoff,
    latest: ext.latest_selected_publication ?? null, status: ext.status || 'release_candidate',
    fieldIds: ext.field_ids || covered.map(n => n.id), covered: covered.length,
    complete: ext.fully_reviewed_fields || 0};
}
export function interventionsOf(node) {
  const c = node.extension_coverage;
  if (!c?.publication_years?.length) return [];
  return [...new Set(c.publication_years)].sort((a, b) => a - b);
}

/* Options: `numbering` (above); `extension` (archive-era extension zone); `only` (a Set of ids:
   lay out just these entries); `compact` (the profile map's density: one band, no band heading,
   no ghosts, and an axis that starts at 1900 unless an entry is earlier); `badges` (Map id → a
   short word drawn after the label, counted in its width so labels still never collide);
   `stacked` (with compact, for phone widths: one mark per row, its label on its own line above). */
export function buildFieldLayout(graph, width, focusSet, layerOrder, opts = {}) {
  const numbering = opts.numbering || null;
  const extension = opts.extension || null;
  const compact = Boolean(opts.compact);
  const G = compact ? G_COMPACT : G_FULL;
  const badges = opts.badges || null;
  const nodes = opts.only ? fieldNodes(graph).filter(n => opts.only.has(n.id)) : fieldNodes(graph);
  const rows = nodes.map(node => ({node, span: spanOf(node)}));
  const spans = rows.filter(r => r.span).map(r => r.span);
  const earliest = spans.length ? Math.min(...spans.map(s => s.start)) : BREAK_YEAR;
  const minYear = Math.max(AXIS_FLOOR, Math.min(1900, Math.floor(earliest / 10) * 10));
  const frame = frameOf(graph);
  const maxYear = Math.max(frame.open ? frame.end : (extension ? extension.end : 2000),
    spans.length ? Math.ceil(Math.max(...spans.map(s => s.end)) / 10) * 10 : 0);
  const coverageYear = frame.open ? null : frame.wall;
  /* Open frame: the prose "coverage through 2000" suffix is gone, so an entry that records a
     review year continues unless its span ends explicitly. The archive reads its labels. */
  const isOpen = item => !item.span?.chronological && (item.span?.endKind === 'coverage_limit'
    || (frame.open && reviewedThrough(item.node) !== null && item.span?.endKind !== 'terminus'));

  const undatedTotal = rows.filter(r => !r.span).length;
  const stacked = compact && Boolean(opts.stacked);
  const inner = Math.max(Math.floor(width) - 2, stacked ? G.stackMinW : G.minW);
  const x0 = G.padL + 6, x1 = inner - G.padR;
  const W = x1 - x0;
  const early = BREAK_YEAR - minYear, late = maxYear - BREAK_YEAR;
  /* A compact map with nothing before 1900 gives the compressed segment's width back. */
  const earlyShare = compact && !early ? 0 : EARLY_SHARE;
  const scale = yr => yr <= BREAK_YEAR
    ? x0 + (early ? (Math.max(yr, minYear) - minYear) / early : 0) * W * earlyShare
    : x0 + W * earlyShare + (yr - BREAK_YEAR) / late * W * (1 - earlyShare);
  const labelOf = node => {
    const base = clip(displayLabel(node), G.clipAt);
    const n = numbering?.get(node.id);
    return n ? `${n}. ${base}` : base;
  };
  /* Badges are small capitals with letter-spacing; compact labels get a little slack for bold. */
  const badgeW = b => b ? textW(b.toUpperCase(), 8.6) * 1.5 + 8 : 0;
  const slack = compact ? 1.06 : 1;

  const lives = lifeIndex(graph);
  const axisTop = 14;
  let y = axisTop + G.axisGap;
  const bands = [], bars = [], chips = [], ghosts = [], captions = [];

  for (const layerId of compact ? [null] : layerOrder) {
    const mine = rows.filter(r => layerId === null || r.node.layer === layerId);
    if (!mine.length) continue;
    const isFull = r => compact || !focusSet || focusSet.has(r.node.id);
    const full = mine.filter(isFull), faded = mine.filter(r => !isFull(r));
    const labelY = y + 11;
    y += G.bandHead;
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
      const badge = badges?.get(item.node.id) || '';
      const w = Math.min(240 + badgeW(badge), Math.round(textW(label, 11) + 22 + badgeW(badge)));
      if (cx + w > x1 && cx > x0) { cx = x0; cy += G.chipH + G.chipGap; chipRows++; }
      chips.push({...item, shape: 'chip', label, badge, x: cx, y: cy, w, h: G.chipH});
      cx += w + G.chipGap;
    }
    const chipBlock = chipRows ? chipRows * (G.chipH + G.chipGap) + 4 : 0;
    const barTop = y + chipBlock;

    const rowEnds = [];
    for (const item of full.filter(r => r.span).sort((a, b) =>
        a.span.start - b.span.start || a.node.label.localeCompare(b.node.label))) {
      const bx = scale(item.span.start);
      /* Open frame: an open-ended mark is solid to its reviewed year, then faded to the frame
         end. Archive: solid to the coverage wall; the wall is the map's limit. Dated work past
         the reviewed year stays solid, so a mark never ends before its own last named year. */
      const open = isOpen(item);
      const reviewed = frame.open ? reviewedThrough(item.node) : null;
      const drawEnd = open
        ? (frame.open ? Math.max(reviewed ?? frame.end, item.span.end) : (item.span.coverage ?? coverageYear))
        : item.span.end;
      const fadeTo = open && frame.open ? frame.end : drawEnd;
      const point = drawEnd === item.span.start;
      const bw = Math.max(point ? 12 : 7, scale(drawEnd) - bx);
      let label = labelOf(item.node);
      const badge = badges?.get(item.node.id) || '';
      const extra = badgeW(badge);
      /* Undated roots: a thin lead-in from the axis's left edge to the first dated year. */
      const lead = item.span.openStart && bx - x0 > 4 ? {x: x0, w: bx - x0} : null;
      const fitsRight = bx + bw + 7 + textW(label) * slack + extra <= x1;
      const fitsLeft = bx - textW(label) * slack - extra - 9 >= G.padL;   /* a left label may sit over a lead-in */
      let side = stacked ? 'above' : fitsRight ? 'right' : fitsLeft ? 'left' : 'inside';
      if (stacked) label = clip(label, Math.max(6, Math.floor((x1 - x0 - extra) / (11.5 * 0.545 * slack))));
      else if (compact && side === 'inside') {
        /* A narrow map: put the label where there is most room and shorten it to fit there. */
        const rooms = {right: x1 - (bx + bw + 7), left: bx - 9 - G.padL, inside: bw - 12};
        side = Object.entries(rooms).sort((a, b) => b[1] - a[1])[0][0];
        const chars = Math.max(6, Math.floor((rooms[side] - extra) / (11.5 * 0.545 * slack)));
        label = clip(label, chars);
      }
      const labelW = textW(label) * slack + extra;
      const reviewX = item.span.chronological && reviewed !== null ? scale(reviewed) : null;
      const need = Math.min(lead ? x0 : side === 'left' ? bx - labelW - 9 : bx, reviewX === null ? Infinity : reviewX - 4);
      const occupied = Math.max(reviewX === null ? -Infinity : reviewX + 4, side === 'right' ? bx + bw + 7 + labelW
        : side === 'inside' && compact ? Math.max(bx + bw, bx + 9 + labelW) : bx + bw);
      let r = stacked ? -1 : rowEnds.findIndex(end => end + 16 <= need);
      if (r === -1) { r = rowEnds.length; rowEnds.push(0); }
      rowEnds[r] = occupied;
      /* Stacked: the label sits above its mark, starting where the mark starts unless that
         would run off the right edge. */
      const labelX = stacked ? Math.max(x0, Math.min(bx, x1 - labelW)) : null;
      const ticks = (item.span.chronological ? [] : milestoneYears(item.node))
        .filter(yr => yr > item.span.start && yr <= drawEnd).map(yr => ({yr, x: scale(yr)}));
      /* Death within the axis: a marker, and the part of the mark after it is posthumous. */
      const life = lives.get(item.node.id) || null;
      /* Drawn only inside the coverage limit; a later death is stated in the panel instead. */
      const death = !item.span.chronological && life?.death && life.death >= minYear && life.death <= (coverageYear ?? frame.end)
        ? {yr: life.death, x: scale(life.death)} : null;
      const posthumous = death && death.x < bx + bw
        ? {x: Math.max(bx, death.x), w: bx + bw - Math.max(bx, death.x)} : null;
      /* Dated interventions after the wall (archive) or the reviewed year (open frame), on this
         entry's row, separate from the mark. */
      const interventions = !item.span.chronological && (frame.open || extension) ? interventionsOf(item.node)
        .filter(yr => yr > (frame.open ? (reviewed ?? 0) : coverageYear)
          && yr <= (frame.open ? frame.end : extension?.end ?? 0))
        .map(yr => ({yr, x: scale(yr)})) : [];
      if (interventions.length) rowEnds[r] = Math.max(rowEnds[r], scale(interventions.at(-1).yr) + 8);
      bars.push({...item, shape: 'bar', label, badge, labelW, side, contW: 0, open, lead, drawEnd, reviewed, fadeTo, point, ticks,
        chronology: item.span.chronological ? chronologyGeometry(item.node, scale, minYear,
          life?.death && life.death >= minYear && life.death <= frame.end ? life.death : null) : null,
        reviewMarker: reviewX !== null ? {year: reviewed, x: reviewX} : null,
        life, death, posthumous, interventions, labelX, x: bx, w: bw, h: G.barH,
        y: barTop + r * (G.barH + G.rowGap + (stacked ? G.stackGap : 0)) + (stacked ? G.stackGap : 0)});
    }

    const fullH = chipBlock + rowEnds.length * (G.barH + G.rowGap + (stacked ? G.stackGap : 0));
    let gy = y + fullH + (faded.length ? 6 : 0);
    const ghostEnds = [];
    for (const item of faded.sort((a, b) => (a.span?.start ?? 0) - (b.span?.start ?? 0))) {
      const bx = item.span ? scale(item.span.start) : x0;
      const ghostEnd = isOpen(item)
        ? (frame.open ? frame.end : (item.span.coverage ?? coverageYear)) : item.span?.end;
      const bw = item.span ? Math.max(5, scale(ghostEnd) - bx) : 40;
      let r = ghostEnds.findIndex(end => end + 2 <= bx);
      if (r === -1) { r = ghostEnds.length; ghostEnds.push(0); }
      ghostEnds[r] = bx + bw;
      ghosts.push({...item, shape: 'ghost', ghostEnd, x: bx, w: bw, h: G.ghostH,
        y: gy + r * (G.ghostH + G.ghostGap)});
    }
    const ghostH = ghostEnds.length * (G.ghostH + G.ghostGap);
    bands.push({layerId, labelY, top: top - G.bandHead, height: fullH + ghostH + G.bandHead,
      full: full.length, faded: faded.length});
    y += fullH + ghostH + (focusSet ? 18 : G.bandGap);
  }

  return {inner, scale, chips, bars, ghosts, bands, captions, axisTop, x0, x1, G, extension, frame,
    minYear, maxYear, coverageYear, breakYear: BREAK_YEAR, earlyShare, height: y + (compact ? 6 : 14),
    placed: new Map([...chips, ...bars, ...ghosts].map(p => [p.node.id, p])),
    datedCount: rows.filter(r => r.span).length, undatedCount: undatedTotal};
}

/* ---------- a person on the field ---------- */
/* The words drawn after each entry's label on a person's profile map. `contributor` reads as
   "resource", as in the people register: an intellectual resource, not a member. */
export const ROLE_BADGE = {historian: 'historian', contributor: 'resource', precursor: 'earlier resource',
  critic: 'critic', comparison: 'comparison', own: 'own entry', approach: 'in an approach'};

/* The entries a person's profile map draws: those whose rosters name the person (with the
   role), the person's own entry, and every entry an own-entry relationship reaches, so each
   relationship is drawn to a real place on the time axis rather than to an off-map stub.
   A person named only inside approaches (strands) falls back to those entries. */
export function personMapSubset(graph, personId) {
  const person = (graph.people || []).find(p => p.id === personId) || null;
  const atlas = new Set(graph.nodes.map(n => n.id));
  const own = person?.node_id && atlas.has(person.node_id) ? person.node_id : null;
  const roster = new Map();
  for (const n of graph.nodes) for (const r of n.representative_people || [])
    if (r.person_id === personId && !roster.has(n.id)) roster.set(n.id, r.role);
  let basis = roster.size ? 'roster' : own ? 'own' : 'none';
  if (!roster.size && !own) for (const n of graph.nodes)
    if ((n.strands || []).some(s => s.person_ids?.includes(personId))) { roster.set(n.id, 'approach'); basis = 'approach'; }
  const edges = own ? graph.edges.filter(e => (e.source === own || e.target === own)
    && atlas.has(e.source) && atlas.has(e.target) && e.source !== e.target) : [];
  const linked = new Map();
  for (const edge of edges) {
    const other = edge.source === own ? edge.target : edge.source;
    if (!linked.has(other)) linked.set(other, []);
    linked.get(other).push({edge, dir: edge.source === own ? 'out' : 'in'});
  }
  const ids = new Set([...roster.keys(), ...(own ? [own] : []), ...linked.keys()]);
  return {person, own, roster, linked, edges, ids, basis};
}
/* Below STACK_BELOW px the map stacks (one mark per row, label above) instead of scrolling. */
export const STACK_BELOW = 560;
export function personMapLayout(graph, personId, width) {
  const subset = personMapSubset(graph, personId);
  const badges = new Map([...subset.roster].map(([id, role]) => [id, ROLE_BADGE[role] || role]));
  if (subset.own) badges.set(subset.own, ROLE_BADGE.own);
  return {...buildFieldLayout(graph, width, null, [], {only: subset.ids, compact: true, badges,
    stacked: width < STACK_BELOW}), subset};
}

export const anchor = p => ({x: p.chronology?.selection
  ? p.chronology.selection.x + p.chronology.selection.w / 2 : p.x + p.w / 2, y: p.y + p.h / 2});
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

/* Life dates for people who have their own entry, keyed by entry id. Only present when the
   published people records carry `life` (see scripts/build_site.py). A death year lets the
   field separate an author's lifetime from the posthumous reception of their work. */
export function lifeIndex(graph) {
  const index = new Map();
  for (const p of graph.people || []) {
    if (!p.node_id || !p.life) continue;
    const year = v => { const m = String(v ?? '').match(/^-?\d+/); return m ? +m[0] : null; };  // BCE-safe
    index.set(p.node_id, {birth: year(p.life.birth), death: year(p.life.death),
      birthPrecision: p.life.birth_precision || null, deathPrecision: p.life.death_precision || null,
      retrieved: p.life.retrieved || null, qid: p.wikidata?.qid || null,
      status: p.life_review?.status || null, checkedOn: p.life_review?.checked_on || null,
      sources: p.life_review?.sources || [], reviewNote: p.life_review?.note || ''});
  }
  return index;
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
