import {PAGE_SIZE, LAYER_TITLES, KINDS, PERSON_ROLES, edgeKind, hasArrow, filterNodes, filterPeople, personContexts, neighborhood, partitionNeighborhood, readRoute, routeHash} from './core.mjs';
import {buildFieldLayout, fieldNodes, fieldEdges, fieldKinds, fieldLayers, relationIndex, milestoneYears,
  focusSetFor, fieldMatches, journalNodes, spanOf, anchor, edgePath, kindLabel, kindChip, dirWord,
  pathwaySet, pathwayEdges, BASE_KINDS, JOURNAL_LAYER} from './field.mjs';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
let graph, pathways, state, nodeById, sourceById, personById, personNames;
const revision = () => graph.revision_history.at(-1).version;
const layerIndex = id => graph.layers.findIndex(l => l.id === id);
const layerLabel = id => LAYER_TITLES[id] || id;
const periodLabel = id => graph.periods.find(p => p.id === id)?.label || 'No assigned period';
const href = patch => routeHash({...state, ...patch});
const nodeHref = id => href({node: id, person: '', edge: '', section: '', page: 0, kind: '', neighborLayer: ''});
const connectedNodeHref = id => href({node: id, person: '', edge: '', section: 'connections', page: 0, kind: '', neighborLayer: ''});
const personHref = id => href({person: id, edge: '', section: '', page: 0, kind: '', neighborLayer: ''});
const linkNode = (id, className = '') => `<a class="${className}" href="${esc(nodeHref(id))}">${esc(nodeById.get(id).label)}</a>`;
const layerOptions = selected => graph.layers.map(l => `<option value="${l.id}" ${selected === l.id ? 'selected' : ''}>${esc(layerLabel(l.id))}</option>`).join('');
const crumbs = items => `<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="#">Atlas</a>${items.map(i => `<span aria-hidden="true">/</span>${i}`).join('')}</nav>`;
const layerTag = n => `<span class="layer-tag tone-${layerIndex(n.layer)}">${esc(layerLabel(n.layer))}</span>`;
const huntTag = n => n.hunt_core_paradigm ? '<span class="hunt-tag">Hunt’s teaching lens</span>' : '';
const rosterLabel = n => `${n.representative_people?.length || 0} historians & contributors`;
function personCard(p, rep = null) {
  const contexts = personContexts(graph, p.id);
  const readings = [...new Set(contexts.map(c => c.representative.works).filter(Boolean))];
  const own = nodeById.get(p.node_id);
  const work = rep ? (rep.works || own?.representative_figures_and_works || '') : (readings[0] || own?.representative_figures_and_works || '');
  return `<article class="person-card"><p class="eyebrow">${rep ? esc(PERSON_ROLES[rep.role]) : `${contexts.length} GROUP${contexts.length === 1 ? '' : 'S'}${own ? ' · FULL ENTRY' : ''}`}</p>
    <h3><a href="${esc(personHref(p.id))}">${esc(p.label)}</a></h3>
    ${rep ? `<p class="person-context">${esc(rep.context)}</p>` : `<p class="person-context">${esc(contexts.map(c => c.node.label).slice(0, 3).join(' · ') || layerLabel(own?.layer))}${contexts.length > 3 ? ' …' : ''}</p>`}
    ${work ? `<p class="person-work">${esc(work)}</p>` : '<p class="person-work fine-print">See the group’s representative works and references.</p>'}
    <a class="entry-open" href="${esc(personHref(p.id))}">Explore this person →</a></article>`;
}
function schoolTabs(n) {
  if (!n.representative_people?.length) return '';
  return `<nav class="school-tabs" aria-label="Explore this entry"><a href="${esc(href({section: '', edge: '', page: 0, kind: '', neighborLayer: '', person: ''}))}" ${state.section !== 'connections' ? 'aria-current="page"' : ''}>Historians & contributors <span>${n.representative_people.length}</span></a>
    <a href="${esc(href({section: 'connections', person: '', page: 0}))}" ${state.section === 'connections' ? 'aria-current="page"' : ''}>Connections <span>${neighborhood(graph, n.id).length}</span></a></nav>`;
}
function strandGuide(n) {
  if (!n.strands?.length) return '';
  return `<section class="strand-guide" aria-label="Approaches within this entry"><h3>Different approaches within this entry</h3><p class="fine-print">Overlapping approaches and debates, not a sequence of schools replacing one another.</p>${n.strands.map(branch => `<details class="strand"><summary>${esc(branch.title)}</summary><p>${esc(branch.focus)}</p><p class="strand-people">${branch.person_ids.map(id => `<a href="${esc(personHref(id))}">${esc(personById.get(id).label)}</a>`).join(' · ')}</p><p class="person-work">${esc(branch.works)}</p><details><summary>Reading references</summary><p class="fine-print">These readings have different scopes; see their source notes.</p>${sourceList(branch.source_ids)}</details></details>`).join('')}</section>`;
}
function corePeople(n) {
  if (!n.representative_people?.length) return '';
  return `<section class="core-people" aria-label="Historians and contributors for this entry"><div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THIS ENTRY</p><h3>Historians & contributors</h3></div><a class="text-link" href="${esc(href({section:'',edge:'',page:0,kind:'',neighborLayer:''}))}">Explore works & approaches →</a></div><ul>${n.representative_people.map(r => `<li data-person="${r.person_id}"><a href="${esc(personHref(r.person_id))}">${esc(personById.get(r.person_id).label)}</a><span>${esc(PERSON_ROLES[r.role])}</span></li>`).join('')}</ul><p class="fine-print">All ${n.representative_people.length} people in this entry’s selection. Roles distinguish historians, resources, and critics; this roster is not an influence diagram.</p></section>`;
}
function schoolPeople() {
  const n = nodeById.get(state.node);
  const reps = n.representative_people;
  return `${crumbs([`<a href="${esc(href({node: '', person: '', edge: '', page: 0, section: ''}))}">${state.pathway ? 'Back to pathway' : 'Back to entries'}</a>`, `<span aria-current="page">${esc(n.label)}</span>`])}
    <div class="section-heading"><div><p class="eyebrow">03 / MEET THE HISTORIANS & CONTRIBUTORS</p><h2>${esc(n.label)}</h2></div><span class="count">${reps.length} people in this selection</span></div>
    ${schoolTabs(n)}<div class="school-layout"><section aria-label="Representative people"><p class="context-note">A selective guide to the people behind this entry. The labels distinguish historians, intellectual resources, and critics; inclusion does not imply a shared doctrine or formal membership.</p>
      ${strandGuide(n)}<div class="people-grid">${pageSlice(reps, 12).map(rep => personCard(personById.get(rep.person_id), rep)).join('')}</div>${pagination(reps.length, 12)}</section>
      <aside class="reading-panel" aria-label="Entry details">${nodeDetail(n)}</aside></div>`;
}
function peopleDirectory() {
  const people = filterPeople(graph, state);
  return `${crumbs(['<span aria-current="page">Historians & contributors</span>'])}<div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THE MAP</p><h2>Find a historian. Follow their work.</h2></div><span class="count">${people.length} of ${graph.people.length} people</span></div>
    <p class="context-note">People can appear in several schools, fields, or debates, with a different role in each. Layer and period filters refer to the entries in which they appear, not to a person’s lifespan.</p>
    ${people.length ? `<div class="people-directory">${pageSlice(people, 12).map(p => personCard(p)).join('')}</div>${pagination(people.length, 12)}` : '<div class="empty"><h3>No people match these filters.</h3><a href="#tab=people">Clear filters →</a></div>'}`;
}
function personPage() {
  const p = personById.get(state.person);
  const contexts = personContexts(graph, p.id);
  const own = nodeById.get(p.node_id);
  const parent = nodeById.get(state.node);
  const origin = parent ? `<a href="${esc(href({person: '', page: 0, section: ''}))}">${esc(parent.label)}</a>` : '<a href="#tab=people">Historians & contributors</a>';
  const basisLabels = {curated_entry: 'Selection recorded in the curated entry', existing_relationship: 'Selection supported by an existing qualified connection', source_review: 'Selection with a scoped source check', editorial_comparison: 'Editorial comparison across constituent fields'};
  return `${crumbs([origin, `<span aria-current="page">${esc(p.label)}</span>`])}<article class="person-profile"><div class="section-heading"><div><p class="eyebrow">A PERSON ACROSS THE MAP</p><h2>${esc(p.label)}</h2></div>${own ? `<a class="button-link" href="${esc(nodeHref(own.id))}">Full entry & relationships →</a>` : ''}</div>
    ${own ? `<p class="profile-introduction">${esc(own.description)}</p>` : '<p class="context-note">Read this person through the works and contexts below. These are selected points of entry, not a complete biography.</p>'}
    <h3>Where to read them</h3><div class="person-contexts">${contexts.map(({node:n, representative:r}) => `<section class="person-affiliation tone-${layerIndex(n.layer)}">${layerTag(n)}<h3><a href="${esc(nodeHref(n.id))}">${esc(n.label)} →</a></h3><span class="role-tag">${esc(PERSON_ROLES[r.role])}</span><p>${esc(r.context)}</p>
      ${r.works ? `<p class="person-work">${esc(r.works)}</p>` : `<p class="fine-print">The current selection names this person without a separate work citation. <a href="${esc(nodeHref(n.id))}">Read the group’s works and references.</a></p>`}
      <details class="person-evidence"><summary>References & basis for inclusion</summary><p class="fine-print">${esc(basisLabels[r.basis])}. Group references provide context; they do not certify every affiliation or interpretation.</p>${r.edge_id ? `<a class="text-link" href="#edge=${r.edge_id}">Inspect the existing relationship →</a>` : ''}${sourceList(r.source_ids)}</details></section>`).join('')}</div>
    ${!contexts.length && own ? `<p>No group roster currently includes this person. Their individual entry provides the selected works and connections.</p><section class="reading-panel"><h3>Representative figures & works</h3><p>${esc(own.representative_figures_and_works)}</p><details class="bibliography" open><summary>References</summary>${sourceList(own.source_ids)}</details></section>` : ''}
    </article>`;
}

/* ---------------- The field: every entry on one time axis ---------------- */
let fieldIndex, fieldNodeById, fieldCatalogue, journalSourceById, atlasEdgeIds;
let hoverId = null, fieldWidth = 0, scrolledFocus = '';

const FIELD_TITLES = {...LAYER_TITLES, [JOURNAL_LAYER]: 'Journals & venues'};
const fieldTitle = id => FIELD_TITLES[id]
  || String(id).replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
const hiddenKinds = () => new Set(state.hide ? state.hide.split(',') : []);
const focusHref = id => href({focus: id, node: '', person: '', edge: '', page: 0, section: ''});
/* Releasing a held entry keeps any pathway overlay and search; it only lets go of the hold. */
const releaseHref = () => href({focus: '', node: '', person: '', edge: '', page: 0, section: ''});
const releaseLink = () => `<a class="release" href="${esc(releaseHref())}">← Show everything</a>`;
const activePathway = () => state.path ? pathways.pathways.find(p => p.id === state.path) : null;
const pathNumbering = () => {
  const p = activePathway();
  return p ? new Map(p.node_ids.map((id, i) => [id, i + 1])) : null;
};
/* Focus wins over a pathway overlay; the pathway stays in the URL as context. */
function fieldFocusSet() {
  if (state.focus) return focusSetFor(graph, state.focus, fieldIndex);
  return pathwaySet(activePathway());
}
function fieldView(width) {
  return buildFieldLayout(graph, width, fieldFocusSet(), fieldLayers(graph, FIELD_TITLES),
    {numbering: state.focus ? null : pathNumbering()});
}

function fieldLegend() {
  const kinds = fieldKinds(graph);
  const hidden = hiddenKinds();
  const counts = new Map();
  for (const e of fieldEdges(graph))
    counts.set(e.relationship_kind, (counts.get(e.relationship_kind) || 0) + 1);
  const toggle = k => {
    const next = new Set(hidden);
    next.has(k) ? next.delete(k) : next.add(k);
    return href({hide: [...next].join(',')});
  };
  return `<div class="field-legend">
    <div class="lg"><strong>Relationships</strong>${kinds.map(k =>
      `<a class="kind k-${esc(k)}${BASE_KINDS.includes(k) ? '' : ' k-extra'}" role="button"
        href="${esc(toggle(k))}" aria-pressed="${!hidden.has(k)}"
        title="${hidden.has(k) ? 'Show' : 'Hide'} ${esc(kindChip(k).toLowerCase())}"
        ><i></i>${esc(kindChip(k))} <em>${counts.get(k) || 0}</em></a>`).join('')}</div>
    <div class="lg"><strong>The mark</strong>
      <span class="swatch precise">years the label names</span>
      <span class="swatch point">a single dated year</span>
      <span class="swatch fuzzy">decade precision</span>
      <span class="swatch open">continues past the coverage limit</span>
      <span class="swatch axis-note">pre-1900 compressed</span></div>
    <div class="lg right"><strong>View</strong>
      <a class="view-link" role="button" href="${esc(href({view: 'map'}))}"
        aria-pressed="${state.view !== 'list'}">Field</a>
      <a class="view-link" role="button" href="${esc(href({view: 'list'}))}"
        aria-pressed="${state.view === 'list'}">List</a></div>
  </div>`;
}

/* The relationships the field is currently showing: a held entry's, or a pathway's own. */
function activeFieldEdges() {
  const hidden = hiddenKinds();
  const edges = state.focus ? (fieldIndex.get(state.focus) || []).map(r => r.edge)
    : pathwayEdges(graph, activePathway(), fieldIndex);
  return edges.filter(e => !hidden.has(e.relationship_kind));
}

function fieldSvg(view) {
  const bottom = view.height;
  const washes = graph.periods.map((per, i) => {
    const nums = (per.label.match(/\b(1[89]\d{2}|20\d{2})\b/g) || []).map(Number);
    const from = nums.length ? nums[0] : view.minYear;
    const to = nums.length === 2 ? nums[1] : nums.length ? nums[0] + 15 : 1945;
    const a = view.scale(Math.max(from, view.minYear)), b = view.scale(Math.min(to, view.maxYear));
    const room = Math.max(3, Math.floor((b - a - 16) / 6.1));
    const text = per.label.replace(/^[^·]*·\s*/, '');
    return `<rect class="period-wash ${i % 2 ? 'alt' : ''}" x="${a}" y="${view.axisTop}"
      width="${Math.max(0, b - a)}" height="${bottom - view.axisTop}"/>
      <text class="period-label" x="${a + 7}" y="${view.axisTop + 13}">${esc(
        text.length > room ? text.slice(0, room - 1) + '…' : text)}</text>`;
  }).join('');
  let grid = '';
  const tick = (yr, major) => {
    grid += `<line class="tick ${major ? 'major' : ''}" x1="${view.scale(yr)}"
      y1="${view.axisTop + 22}" x2="${view.scale(yr)}" y2="${bottom}"/>`;
    if (major) grid += `<text class="tick-label" x="${view.scale(yr)}"
      y="${view.axisTop + 34}" text-anchor="middle">${yr}</text>`;
  };
  for (let yr = Math.ceil(view.minYear / 25) * 25; yr < view.breakYear; yr += 25) tick(yr, true);
  for (let yr = view.breakYear; yr <= view.maxYear; yr += 10) tick(yr, yr % 20 === 0);
  const wx = view.scale(view.coverageYear), bx = view.scale(view.breakYear);
  grid += `<line class="coverage-wall" x1="${wx}" y1="${view.axisTop + 16}" x2="${wx}" y2="${bottom}"/>
    <text class="coverage-label" x="${wx - 6}" y="${bottom - 6}" text-anchor="end"
      >curated coverage ends ${view.coverageYear}</text>
    <line class="scale-break" x1="${bx}" y1="${view.axisTop + 16}" x2="${bx}" y2="${bottom}"/>`;

  const bands = view.bands.map(b => `<line class="band-rule" x1="${view.G.padL}"
      y1="${b.labelY - 13}" x2="${view.x1}" y2="${b.labelY - 13}"/>
    <text class="band-label" x="${view.x0}" y="${b.labelY}">${esc(fieldTitle(b.layerId))}</text>
    ${b.faded ? `<a class="band-release" href="${esc(state.focus ? releaseHref() : href({path: ''}))}"
        aria-label="Show all ${b.full + b.faded} entries in this band"><text class="band-count" x="${view.x1}" y="${b.labelY}" text-anchor="end">${
        b.full} shown · ${b.faded} set aside · show all</text></a>`
      : `<text class="band-count" x="${view.x1}" y="${b.labelY}" text-anchor="end">${b.full} entries</text>`}`).join('');
  const captions = view.captions.map(c => `<text class="chip-caption" x="${c.x}" y="${c.y}"
      >${esc(c.text)}</text>`).join('');

  const shown = activeFieldEdges();
  const edges = shown.map(e => {
    const a = view.placed.get(e.source), b = view.placed.get(e.target);
    if (!a || !b) return '';
    const kind = BASE_KINDS.includes(e.relationship_kind) ? e.relationship_kind : 'extra-kind';
    return `<path class="edge ${kind}" data-edge="${esc(e.id)}"
      d="${esc(edgePath(anchor(a), anchor(b)))}"/>`;
  }).join('');

  const related = new Set();
  if (state.focus) for (const e of shown) related.add(e.source === state.focus ? e.target : e.source);
  else for (const id of pathwaySet(activePathway()) || []) related.add(id);
  const emphasised = Boolean(state.focus || state.path);
  const cls = p => {
    const on = [];
    if (p.node.id === state.focus) on.push('selected');
    else if (related.has(p.node.id)) on.push('related');
    else if (emphasised) on.push('dimmed');
    if (state.query && !fieldMatches(graph, fieldIndex, personNames, p.node.id, state.query))
      on.push('dimmed');
    else if (state.query) on.push('hit');
    return on.join(' ');
  };

  const markHref = p => p.node.id === state.focus ? releaseHref() : focusHref(p.node.id);
  const heldNote = p => p.node.id === state.focus ? ' Held; activate again to release.' : '';
  const chips = view.chips.map(p => `<a class="chip ${cls(p)}" data-id="${esc(p.node.id)}"
      href="${esc(markHref(p))}"
      aria-label="${esc(p.node.label)}, no date span stated.${heldNote(p)}">
      <rect class="chip-shape" x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"/>
      <text class="chip-label" x="${p.x + 10}" y="${p.y + p.h / 2 + 1}">${esc(p.label)}</text>
    </a>`).join('');
  const ghosts = view.ghosts.map(p => `<a class="ghost-link" data-id="${esc(p.node.id)}"
      href="${esc(focusHref(p.node.id))}"><rect class="ghost" x="${p.x}" y="${p.y}"
      width="${p.w}" height="${p.h}" rx="2"/><title>${esc(p.node.label)} · ${esc(
      p.node.date_label)}</title></a>`).join('');
  const bars = view.bars.map(p => {
    const fuzzy = p.span.precision === 'decade';
    const xEnd = p.x + p.w;
    return `<a class="entry end-${esc(p.span.endKind)} ${cls(p)}" data-id="${esc(p.node.id)}"
      href="${esc(markHref(p))}"
      aria-label="${esc(p.node.label)}, ${esc(p.node.date_label)}.${heldNote(p)}">
      <rect class="bar-shape${p.point ? ' point' : ''}${p.node.entry_kind === 'person' ? ' person' : ''}${
        p.node.entry_kind === 'periodical' ? ' periodical' : ''}"
        x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"
        ${fuzzy && !p.point ? 'fill-opacity="0.62"' : ''} rx="3"/>
      <line class="bar-cap start" x1="${p.x}" y1="${p.y}" x2="${p.x}" y2="${p.y + p.h}"/>
      ${p.span.endKind === 'terminus'
        ? `<line class="bar-cap end" x1="${xEnd}" y1="${p.y}" x2="${xEnd}" y2="${p.y + p.h}"/>` : ''}
      ${p.open && p.w > 30 ? `<rect class="bar-fade" x="${xEnd - 22}" y="${p.y - 1}" width="23" height="${p.h + 2}"/>` : ''}
      ${p.ticks.map(t => `<line class="ms" x1="${t.x}" y1="${p.y + 3}" x2="${t.x}" y2="${p.y + p.h - 3}"
        ><title>${t.yr} · a year named in this entry’s date label</title></line>`).join('')}
      <text class="bar-label ${p.side}" y="${p.y + p.h / 2 + 1}"
        x="${p.side === 'right' ? xEnd + 7 : p.side === 'left' ? p.x - 7 : p.x + 9}"
        ${p.side === 'left' ? 'text-anchor="end"' : ''}>${esc(p.label)}</text>
    </a>`;
  }).join('');

  /* role=group, not img: the marks inside are links and must stay reachable. */
  return `<svg class="field ${emphasised ? 'focused' : ''}"
      width="${view.inner}" height="${view.height}" viewBox="0 0 ${view.inner} ${view.height}"
      role="group" aria-label="Historiography on a time axis. Each mark is a link; a text list of the same entries is available under View · List.">
    <defs><linearGradient id="fade-right" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#fbfaf4" stop-opacity="0"/>
      <stop offset="1" stop-color="#fbfaf4" stop-opacity=".92"/></linearGradient></defs>
    <g class="chrome">${washes}${grid}
      <line class="axis-line" x1="${view.x0}" y1="${view.axisTop + 22}" x2="${view.x1}"
        y2="${view.axisTop + 22}"/>${bands}${captions}</g>
    <g class="ghosts">${ghosts}</g><g class="edges">${edges}</g>${chips}${bars}
  </svg>`;
}

function fieldDateNote(n, span) {
  if (!span) return `<strong>No span stated.</strong> <code>${esc(n.date_label)}</code> names
    people or methods rather than years, so it sits in the band’s strip rather than being given a
    date it does not claim.`;
  const wall = span.coverage ?? graph.scope.main_period[1];
  const periodical = n.entry_kind === 'periodical';
  const precision = span.precision === 'decade' ? ' (decade precision)' : '';
  let opening, ending;
  if (span.endKind === 'coverage_limit') {
    opening = periodical
      ? `<strong>First issue ${span.start}</strong>, drawn to ${wall}.`
      : `<strong>From ${span.start}</strong>${precision}, drawn to ${wall}.`;
    ending = `${wall} is the limit of this atlas’s coverage, not an ending: the mark fades into
      the wall because the ${periodical ? 'periodical' : 'field'} continues beyond what is mapped here.`;
  } else if (span.end > span.start) {
    opening = periodical
      ? `<strong>Published ${span.start}–${span.end}</strong>.`
      : `<strong>Dated ${span.start}–${span.end}</strong> by its label${precision}.`;
    ending = span.endKind === 'terminus'
      ? 'An ending is recorded, so the mark is capped.'
      : span.endKind === 'title_change'
        ? 'The title changed here. The periodical did not cease; it continued under a new name.'
        : 'The label stops here without recording an ending, so the mark has no closing cap.';
  } else {
    opening = `<strong>Dated ${span.start}</strong> by its label${precision}.`;
    ending = span.endKind === 'terminus'
      ? 'An ending is recorded in the same year.'
      : 'A single year is all the label names, so the mark is a single mark, not a span.';
  }
  const ticks = milestoneYears(n).filter(y => y > span.start).length;
  const tickNote = ticks ? ` The ${ticks === 1 ? 'other year' : `${ticks} other years`} the label
    names ${ticks === 1 ? 'is' : 'are'} ticked on the bar.` : '';
  const prov = span.curated
    ? `From the curated <code>date_span</code>. ${esc(span.basis || '')}`
    : `Read from <code>${esc(n.date_label)}</code> by the site, not curated as numbers. The mark
       says nothing about when the ${periodical ? 'periodical' : 'field'} was most influential.`;
  return `${opening} ${ending}${tickNote}<br><span class="prov">${prov}</span>`;
}

/* One relationship, with its evidence and references one click away. */
function relRow(r) {
  const e = r.edge, kind = e.relationship_kind;
  const other = fieldNodeById.get(r.other);
  const tone = BASE_KINDS.includes(kind) ? kind : 'extra-kind';
  const atlasEdge = atlasEdgeIds.has(e.id);
  const sources = atlasEdge ? sourceList(e.source_ids) : sourceList(e.source_ids, journalSourceById);
  const scope = e.temporal_scope?.start ? `<p class="fine-print">Dated ${e.temporal_scope.start}${
    e.temporal_scope.end && e.temporal_scope.end !== e.temporal_scope.start ? `–${e.temporal_scope.end}` : ''}${
    e.temporal_scope.meaning ? ` · ${esc(String(e.temporal_scope.meaning).replace(/_/g, ' '))}` : ''}.</p>` : '';
  return `<details class="rel ${tone}" data-edge="${esc(e.id)}"><summary>
      <span class="dir">${esc(dirWord(kind, r.dir))}</span>
      <span class="who">${esc(other.label)}</span>
      <span class="what">${esc(e.relationship)}</span></summary>
    <div class="rel-body">
      ${e.evidence_note ? `<p class="evidence"><strong>Evidence.</strong> ${esc(e.evidence_note)}</p>`
        : '<p class="evidence fine-print">No evidence note is recorded for this relationship.</p>'}${scope}
      <details class="rel-sources"><summary>References · ${e.source_ids?.length || 0}</summary>${sources}</details>
      <p class="rel-links"><a href="${esc(focusHref(r.other))}">Hold ${esc(other.label)} →</a>${
        atlasEdge ? `<a href="#edge=${esc(e.id)}">Inspect this relationship →</a>` : ''}</p>
    </div></details>`;
}

function pathwayPanel(p) {
  const among = pathwayEdges(graph, p, fieldIndex).length;
  return `<div class="path-panel"><p class="eyebrow">Seminar pathway · ${p.node_ids.length} entries</p>
    <h2 id="field-title" tabindex="-1">${esc(p.title)}</h2>
    <p class="meta">Numbered in reading order. The order is a suggested sequence, not a claim of
      influence; only the ${among} relationship${among === 1 ? '' : 's'} recorded among these
      entries ${among === 1 ? 'is' : 'are'} drawn.</p>
    <ol>${p.node_ids.map(id => `<li><a href="${esc(focusHref(id))}">${esc(nodeById.get(id).label)}</a></li>`).join('')}</ol>
    <section class="sec"><h3>Questions to work with</h3><ol class="questions">${
      p.questions.map(q => `<li>${esc(q)}</li>`).join('')}</ol>
      <div class="exercise"><p class="eyebrow">Try this</p><p>${esc(p.exercise)}</p></div></section>
    <p class="panel-more"><a class="button-link" href="#pathway=${esc(p.id)}">Reading page for this pathway →</a>
      <a class="text-link" href="${esc(href({path: ''}))}">Clear the overlay</a></p>
    <p class="fine-print">Editorial teaching prompts, not quotations from Hunt.</p></div>`;
}

function fieldPanel() {
  const id = hoverId || state.focus;
  const p = activePathway();
  if (!id) {
    if (p) return pathwayPanel(p);
    return `<div class="panel-empty"><p class="eyebrow">Nothing selected</p>
    <h2>Hover to light up an argument. Click to hold it.</h2>
    <p>A mark runs across <strong>the years an entry’s date label names</strong>. The left cap
    is the earliest dated year. A bar that fades into the dashed wall at 2000 continues beyond
    what this atlas covers: the wall is a limit of the map, not an ending. Ticks mark other
    years the label names. Open a relationship to read its evidence.</p>
    <p class="fine-print">To let go of a held entry, click it again, click empty space in the chart,
    press Escape, or use “Show everything” at the top of this panel.</p>
    <p class="fine-print">${fieldCatalogue.unlinked.toLocaleString()} catalogued periodicals
    are not shown: they have no evidenced founding, debate or principal-venue claim yet.</p></div>`;
  }
  const n = fieldNodeById.get(id);
  const span = spanOf(n);
  const hidden = hiddenKinds();
  const rels = (fieldIndex.get(id) || []).filter(r => !hidden.has(r.edge.relationship_kind));
  const atlas = graph.nodes.some(x => x.id === id);
  const groups = [...new Set(rels.map(r => r.edge.relationship_kind))];
  const seq = p ? p.node_ids.indexOf(id) : -1;
  return `${state.focus && !hoverId ? `<p class="panel-release">${releaseLink()}</p>` : ''}
    ${p ? `<p class="path-strip">${seq >= 0 ? `Entry ${seq + 1} of ${p.node_ids.length} in` : 'Outside'}
      the pathway <a href="${esc(href({focus: ''}))}">${esc(p.title)}</a>.</p>` : ''}
    <p class="eyebrow">${esc(n.entry_type || 'Entry')}</p>
    <h2 id="field-title" tabindex="-1">${esc(n.label)}</h2>
    <p class="meta">${esc(n.date_label || 'No date label')} · ${esc(fieldTitle(n.layer))}</p>
    <div class="datewhy">${fieldDateNote(n, span)}</div>
    <p class="claim">${esc(n.description)}</p>
    ${n.scope_note ? `<div class="scope"><strong>Scope &amp; distinctions.</strong>
      ${esc(n.scope_note)}</div>` : ''}
    ${groups.map(kind => {
      const items = rels.filter(r => r.edge.relationship_kind === kind);
      return `<section class="sec"><h3>${esc(kindLabel(kind))} · ${items.length}</h3>${
        items.map(relRow).join('')}</section>`;
    }).join('')}
    ${atlas ? `<p class="panel-more"><a class="button-link" href="${esc(nodeHref(id))}"
      >Full entry, people &amp; references →</a></p>` : `<p class="panel-more fine-print">
      A catalogued periodical. Its atlas links are listed above; it has no entry page.</p>`}`;
}

/* The accessible equivalent of the field: the same entries, in time order, grouped by band. */
function fieldList() {
  const rows = fieldNodes(graph).map(n => ({n, span: spanOf(n)}))
    .filter(r => !state.query || fieldMatches(graph, fieldIndex, personNames, r.n.id, state.query))
    .sort((a, b) => (a.span?.start ?? 9999) - (b.span?.start ?? 9999)
      || a.n.label.localeCompare(b.n.label));
  if (!rows.length) return `<div class="empty"><h3>No entries match “${esc(state.query)}”.</h3>
    <a href="${esc(href({query: ''}))}">Clear the search →</a></div>`;
  const starts = rows.filter(r => r.span).map(r => r.span.start);
  const lo = Math.floor(Math.min(1900, ...starts) / 10) * 10;
  const hi = Math.max(graph.scope?.main_period?.[1] ?? 2000, ...rows.filter(r => r.span).map(r => r.span.end));
  const pct = yr => Math.max(0, Math.min(100, (yr - lo) / (hi - lo) * 100));
  const mini = span => {
    if (!span) return '';
    const open = span.endKind === 'coverage_limit';
    const a = pct(span.start), b = Math.max(a + 1.5, pct(open ? (span.coverage ?? hi) : span.end));
    return `<span class="mini" aria-hidden="true"><i class="${open ? 'open' : ''}" style="left:${a}%;width:${b - a}%"></i></span>`;
  };
  return `<p class="fine-print">All ${rows.length} entries, in time order within each band.
      Dates describe arrival and influence, not a lifespan.</p>` +
    fieldLayers(graph, FIELD_TITLES).map(layerId => {
      const mine = rows.filter(r => r.n.layer === layerId);
      if (!mine.length) return '';
      /* Narrow screens open one band at a time; the summary carries the count. */
      return `<details class="band-list" ${matchMedia('(max-width: 700px)').matches ? '' : 'open'}><summary>${esc(fieldTitle(layerId))}<span>${mine.length}</span></summary>
      <table class="field-table"><caption>${esc(fieldTitle(layerId))}</caption>
      <thead><tr><th scope="col">Dates</th><th scope="col">Entry</th><th scope="col">Kind</th>
        <th scope="col">Relationships</th></tr></thead><tbody>${mine.map(({n, span}) => {
        const rels = (fieldIndex.get(n.id) || []).length;
        return `<tr><td class="td-date">${esc(span ? `${span.start}${span.end > span.start
            ? `–${span.end}` : ''}` : 'not stated')}${mini(span)}</td>
          <td><a href="${esc(focusHref(n.id))}">${esc(n.label)}</a>
            <span class="td-note">${esc(n.date_label)}</span></td>
          <td>${esc(n.entry_type || fieldTitle(n.layer))}</td>
          <td class="td-num">${rels}</td></tr>`;
      }).join('')}</tbody></table></details>`;
    }).join('');
}

function fieldPage() {
  const counts = fieldView(1200);   /* counts do not depend on width; the SVG is drawn after measuring */
  const body = state.view === 'list' ? `<div class="field-listing">${fieldList()}</div>`
    : '<div class="field-scroll" aria-busy="true"></div>';
  return `<div class="field-page">
    <div class="section-heading"><div><p class="eyebrow">01 / THE WHOLE FIELD</p>
      <h2>Historiography on one time axis</h2></div>
      <p class="field-summary">${counts.datedCount} placed in time${counts.undatedCount
        ? ` · ${counts.undatedCount} without a stated span` : ''} ·
        ${fieldEdges(graph).length} relationships</p></div>
    ${fieldLegend()}
    <div class="field-split">${body}
      <aside class="field-panel">${fieldPanel()}</aside></div>
    <p class="fine-print">${state.view === 'list'
      ? 'Text view. Switch to Field for the visual arrangement.'
      : 'A text list of the same entries is available under View · List.'}
      Bars follow the years each date label names; they are editorial readings, not verified chronology or measures of influence.</p>
  </div>`;
}

/* Draw the SVG into the box it will occupy, at the box's real width. Redrawn on resize. */
function drawField() {
  const box = document.querySelector('.field-scroll');
  if (!box) return;
  fieldWidth = box.clientWidth || 1000;
  box.innerHTML = fieldSvg(fieldView(fieldWidth));
  box.removeAttribute('aria-busy');
  const svg = box.querySelector('svg.field');
  const panel = document.querySelector('.field-panel');
  const paint = () => { panel.innerHTML = fieldPanel(); };
  const preview = target => {
    const g = target.closest?.('.entry, .chip');
    const id = g ? g.dataset.id : null;
    if (id === hoverId) return;
    hoverId = id;
    svg.classList.toggle('previewing', Boolean(id));
    paint();
  };
  const clear = () => { if (hoverId === null) return; hoverId = null; svg.classList.remove('previewing'); paint(); };
  svg.addEventListener('mouseover', e => preview(e.target));
  svg.addEventListener('mouseleave', clear);
  /* Keyboard users get the same preview as hover. */
  svg.addEventListener('focusin', e => preview(e.target));
  svg.addEventListener('focusout', e => { if (!svg.contains(e.relatedTarget)) clear(); });
  svg.addEventListener('mouseover', e => emphasise(svg, e.target));
  /* Clicking empty chart space lets go of the held entry. */
  svg.addEventListener('click', e => {
    if (state.focus && !e.target.closest('a')) change({focus: ''});
  });
  if (state.focus && state.focus !== scrolledFocus) {
    scrolledFocus = state.focus;
    const held = svg.querySelector('.entry.selected, .chip.selected');
    held?.scrollIntoView({block: 'center',
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  }
  if (!state.focus) scrolledFocus = '';
}
function emphasise(svg, target) {
  const row = target.closest?.('[data-edge]');
  for (const path of svg.querySelectorAll('.edge')) {
    path.classList.toggle('emph', Boolean(row) && path.dataset.edge === row.dataset.edge);
    path.classList.toggle('mute', Boolean(row) && path.dataset.edge !== row.dataset.edge);
  }
}
function wireField() {
  drawField();
  const panel = document.querySelector('.field-panel');
  panel?.addEventListener('mouseover', e => {
    const svg = document.querySelector('svg.field');
    if (svg) emphasise(svg, e.target);
  });
}
let resizeTimer;
function onResize() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    const box = document.querySelector('.field-scroll');
    if (box && Math.abs(box.clientWidth - fieldWidth) > 4) drawField();
  }, 150);
}

function change(patch, replace = false) {
  const hash = href(patch);
  if (replace) { history.replaceState(null, '', hash); state = readRoute(hash, graph, pathways); render(); }
  else if (location.hash === hash || (!location.hash && hash === '#')) render();
  else location.hash = hash;
}
function pagination(total, size) {
  if (total <= size) return '';
  const pages = Math.ceil(total / size);
  const page = Math.min(state.page, pages - 1);
  return `<nav class="pagination" aria-label="Pages"><button data-page="${page - 1}" ${page === 0 ? 'disabled' : ''}>← Previous</button><span>Page ${page + 1} of ${pages}</span><button data-page="${page + 1}" ${page + 1 === pages ? 'disabled' : ''}>Next →</button></nav>`;
}
function pageSlice(rows, size) {
  const page = Math.min(state.page, Math.max(0, Math.ceil(rows.length / size) - 1));
  return rows.slice(page * size, (page + 1) * size);
}
function overview() {
  const notes = [
    'Earlier resources for thinking about knowledge, society, and historical explanation.',
    'Subjects and forms of historical writing that persist across methodological turns.',
    'Individual arguments and conceptual resources, within and beyond the discipline.',
    'Collective projects, methodological debates, and fields as they expand and change.',
  ];
  const samples = [['karl', 'historicist'], ['science', 'political'], ['fanon', 'eileen_power'], ['annales', 'women']];
  return `<div class="section-heading"><div><p class="eyebrow">01 / FIND YOUR WAY IN</p><h2>One atlas. Four layers.</h2></div><p>Open a layer, meet its historians,<br> then follow their connections.</p></div>
    <div class="overview-layout"><section class="layer-grid" aria-label="Four layers">${graph.layers.map((layer, i) => {
      const members = graph.nodes.filter(n => n.layer === layer.id);
      const exampleIds = samples[i].filter(id => nodeById.has(id) && nodeById.get(id).layer === layer.id);
      const examples = [...exampleIds, ...members.map(n => n.id).filter(id => !exampleIds.includes(id))].slice(0, 3);
      const groups = [...graph.periods, {id: 'unassigned', label: 'No assigned period'}]
        .map(p => ({...p, count: members.filter(n => p.id === 'unassigned' ? !n.period : n.period === p.id).length})).filter(p => p.count);
      return `<article class="layer-card tone-${i}"><div class="card-top"><span class="layer-number">0${i + 1}</span><span>${members.length} entries</span></div>
        <h3><a href="#layer=${layer.id}">${esc(layerLabel(layer.id))}<span aria-hidden="true">↗</span></a></h3><p>${notes[i]}</p>
        ${groups.some(p => p.id !== 'unassigned') ? `<div class="nested-groups">${groups.map(p => `<a href="#layer=${layer.id}&period=${p.id}" class="period-row"><span>${esc(p.label)}</span><strong>${p.count}</strong></a>`).join('')}</div>` : ''}
        <div class="sample-entries"><span>Starting points</span>${examples.map(id => linkNode(id)).join('')}</div>
      </article>`;
    }).join('')}</section>
    <aside class="guide"><p class="eyebrow">FOLLOW A QUESTION</p><h2>Take a seminar pathway.</h2><p>Read a small constellation of entries together, then test what connects them.</p>
      ${['paradigms_and_limits', 'agency_and_structure', pathways.pathways.at(-2).id].map(id => {
        const p = pathways.pathways.find(p => p.id === id);
        return `<a class="pathway-teaser" href="#pathway=${p.id}"><span>${p.node_ids.length} ENTRIES</span><strong>${esc(p.title)}</strong><span aria-hidden="true">→</span></a>`;
      }).join('')}<a class="text-link" href="#tab=pathways">All ${pathways.pathways.length} pathways →</a>
      <div class="guide-note"><span class="small-orbit" aria-hidden="true">◎</span><p>The layers are browsing groups. They are not ranks, and they do not imply that one school replaced another.</p></div>
    </aside></div>`;
}
function directory() {
  const rows = filterNodes(graph.nodes, state, graph.people).sort((a, b) => a.label.localeCompare(b.label));
  const title = state.layer ? layerLabel(state.layer) : 'Find an entry';
  const matchingPeople = state.query ? filterPeople(graph, state) : [];
  return `${crumbs([`<span aria-current="page">${esc(title)}</span>`])}
    <div class="section-heading"><div><p class="eyebrow">02 / BROWSE ENTRIES</p><h2>${esc(title)}</h2></div><span class="count">${rows.length} of ${graph.nodes.length} entries</span></div>
    ${matchingPeople.length ? `<div class="people-search-hint"><a href="${esc(href({tab:'people', node:'', person:'', page:0}))}">${matchingPeople.length} matching people →</a><span>${esc(matchingPeople.slice(0,4).map(p=>p.label).join(' · '))}</span></div>` : ''}
    ${state.period ? `<p class="context-note">${esc(periodLabel(state.period))}. ${state.period !== 'unassigned' ? 'Entries with no assigned period are also included. Periods describe emergence or expansion, not termination.' : 'No period assignment does not mean the entry is undated; read its date label.'}</p>` : ''}
    ${state.hunt ? '<p class="context-note">These four entries form Hunt’s teaching lens, not a universal ranking of significance.</p>' : ''}
    ${rows.length ? `<div class="entry-grid">${pageSlice(rows, 12).map(n => `<article class="entry-card tone-${layerIndex(n.layer)}">${layerTag(n)}<h3>${linkNode(n.id)}</h3><p class="date">${esc(n.date_label || 'Date not recorded')}</p><p class="entry-excerpt">${esc(n.description)}</p>${huntTag(n)}<a class="entry-open" href="${esc(nodeHref(n.id))}" aria-label="Explore ${esc(n.label)}">${n.representative_people?.length ? rosterLabel(n) + ' →' : 'Explore connections →'}</a></article>`).join('')}</div>${pagination(rows.length, 12)}` : '<div class="empty"><h3>No entries match these filters.</h3><p>Try a shorter search or choose a broader layer or period.</p><a href="#">Clear all filters →</a></div>'}`;
}
function sourceList(ids, byId = sourceById) {
  if (!ids?.length) return '<p class="context-note">No relationship-specific references recorded. An entry’s bibliography does not establish this connection.</p>';
  const statuses = {not_checked: 'Not checked', bibliographic_metadata_checked: 'Bibliographic metadata checked', supporting_page_checked: 'Supporting page checked'};
  return `<ul class="sources">${ids.map(id => {
    const s = byId.get(id);
    if (!s) return '';
    const citation = esc(s.citation || s.title);
    const url = /^https?:\/\//.test(s.url || '') ? s.url : null;
    return `<li>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${citation}<span class="sr-only"> (opens in a new tab)</span> ↗</a>` : citation}
      ${s.notes ? `<p>${esc(s.notes)}</p>` : ''}
      <details><summary>${esc(statuses[s.verification?.status] || 'Verification unrecorded')}</summary><p>${esc(s.verification?.note || 'No verification scope has been recorded for this reference.')}</p>${s.verification?.checked_on ? `<p>Checked on ${esc(s.verification.checked_on)}.</p>` : ''}</details></li>`;
  }).join('')}</ul>`;
}
function nodeDetail(n) {
  const memberPaths = pathways.pathways.filter(p => p.node_ids.includes(n.id));
  return `<div class="reading-header"><p class="eyebrow">THE ENTRY</p><h2 id="detail-title" tabindex="-1">${esc(n.label)}</h2>${layerTag(n)}${huntTag(n)}<a class="hold-link" href="#focus=${esc(n.id)}">Hold in the field →</a></div>
    <p class="date">${esc(n.date_label || 'Date not recorded')}</p><p class="period-note">${esc(periodLabel(n.period))}</p>
    ${n.entry_type ? `<p class="entry-type">${esc(n.entry_type)}</p>` : ''}<p class="description">${esc(n.description)}</p>${n.scope_note ? `<h3>Scope & distinctions</h3><p>${esc(n.scope_note)}</p>` : ''}<h3>Representative figures & works</h3><p>${esc(n.representative_figures_and_works || 'Not recorded.')}</p>
    <details class="bibliography" open><summary>References <span>${n.source_ids?.length || 0}</span></summary><p class="fine-print">References offer context; a metadata check does not certify every interpretation.</p>${sourceList(n.source_ids)}</details>
    ${memberPaths.length ? `<h3>Read in a pathway</h3><ul class="related-pathways">${memberPaths.map(p => `<li><a href="#pathway=${p.id}">${esc(p.title)} →</a></li>`).join('')}</ul>` : ''}`;
}
function edgeDetail(e) {
  const kind = edgeKind(e);
  return `<div class="reading-header"><p class="eyebrow">THE RELATIONSHIP · ${esc(e.id)}</p><h2 id="detail-title" tabindex="-1">${esc(KINDS[kind])}</h2><a class="text-link" href="${esc(href({edge: ''}))}">← Back to entry</a></div>
    <div class="edge-endpoints">${linkNode(e.source)}<span>${hasArrow(e) ? '↓ toward' : kind === 'comparison' ? '↕ compared with · no direction' : '↕ direction unclassified'} </span>${linkNode(e.target)}</div>
    <h3>Interpretation</h3><p class="description">${esc(e.relationship)}</p>
    ${kind === 'unclassified' ? `<p class="context-note">Direction metadata is not recorded. This is not classified as influence. Legacy category: ${esc(e.type)}.</p>` : kind === 'contribution' ? '<p class="context-note">A contribution does not imply founding a field.</p>' : kind === 'critique' ? '<p class="context-note">The arrow runs from the critic toward the position criticized.</p>' : ''}
    <h3>Evidence & qualifications</h3><p>${esc(e.evidence_note || 'No relationship-specific evidence note recorded.')}</p>
    <h3>Relationship references</h3><p class="fine-print">These references are relevant to the connection; their presence is not proof of every claim.</p>${sourceList(e.source_ids)}`;
}
function relationshipList(rows, n) {
  return `<ol class="relationship-list">${rows.map(({edge: e, node}) => `<li class="relationship-row ${e.id === state.edge ? 'selected' : ''}"><div>${layerTag(node)}<h3>${linkNode(node.id)}</h3></div><a class="inspect-link kind-${edgeKind(e)}" href="${esc(href({edge: e.id}))}"><span>${esc(KINDS[edgeKind(e)])}${hasArrow(e) ? e.source === n.id ? ' → from this entry' : ' ← toward this entry' : ' · no arrow'}</span><strong>${esc(e.relationship)}</strong><span>Inspect evidence →</span></a></li>`).join('')}</ol>`;
}
function relationshipSummary(rows, n) {
  const lanes = partitionNeighborhood(rows, n.id);
  const comparisons = lanes.associated.filter(r => edgeKind(r.edge) === 'comparison').length;
  return `<div class="relationship-summary" aria-label="Connection coverage"><strong>${rows.length} relationships in this view</strong><span>${lanes.incoming.length} incoming</span><span>${lanes.outgoing.length} outgoing</span><span>${comparisons} comparisons</span><span>${lanes.associated.length - comparisons} direction unclassified</span></div>`;
}
function neighborhoodMap(rows, n) {
  const lanes = partitionNeighborhood(rows, n.id);
  const incoming = lanes.incoming;
  const outgoing = lanes.outgoing;
  const others = lanes.associated;
  const spacing = 155;
  const height = Math.max(320, Math.max(incoming.length, outgoing.length) * spacing + 100);
  const cy = height / 2;
  const rowY = (i, count) => cy + (i - (count - 1) / 2) * spacing;
  const renderNeighbor = ({edge:e, node}, i, lane) => {
    const y = rowY(i, lane === 'incoming' ? incoming.length : outgoing.length);
    return `<a class="flow-neighbor neighbor-node ${lane} tone-${layerIndex(node.layer)}" data-edge="${e.id}" style="top:${y}px" href="${esc(connectedNodeHref(node.id))}"><span>${esc(layerLabel(node.layer))}</span><strong>${esc(node.label)}</strong>${e.map_label ? `<span class="neighbor-exchange">${esc(e.map_label)}</span>` : ''}<span class="neighbor-open">Follow connections →</span></a>
      <a class="flow-label edge-label ${lane} kind-${edgeKind(e)} ${e.id === state.edge ? 'selected' : ''}" style="top:${(y + cy) / 2}px" href="${esc(href({edge:e.id}))}" aria-label="Inspect ${esc(KINDS[edgeKind(e)])} from ${esc(nodeById.get(e.source).label)} to ${esc(nodeById.get(e.target).label)}">${esc(KINDS[edgeKind(e)])} →</a>`;
  };
  return `<div class="graph-scroll"><div class="flow-graph focus-graph" style="height:${height}px" aria-label="Upstream entries on the left, selected entry in the centre, downstream entries on the right">
    <div class="flow-head incoming">INTO THIS ENTRY · ${incoming.length}</div><div class="flow-head middle">YOUR FOCUS</div><div class="flow-head outgoing">FROM THIS ENTRY · ${outgoing.length}</div>
    <svg class="connections" viewBox="0 0 1000 ${height}" preserveAspectRatio="none" aria-hidden="true"><defs>${['influence','contribution','critique'].map(k => `<marker id="arrow-${k}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" class="arrow-${k}"/></marker>`).join('')}</defs>
      ${incoming.map(({edge:e},i) => `<path class="connection incoming kind-${edgeKind(e)} ${state.edge === e.id ? 'active' : ''}" d="M260 ${rowY(i,incoming.length)} C325 ${rowY(i,incoming.length)}, 325 ${cy}, 390 ${cy}" marker-end="url(#arrow-${edgeKind(e)})"/>`).join('')}
      ${outgoing.map(({edge:e},i) => `<path class="connection outgoing kind-${edgeKind(e)} ${state.edge === e.id ? 'active' : ''}" d="M610 ${cy} C675 ${cy}, 675 ${rowY(i,outgoing.length)}, 740 ${rowY(i,outgoing.length)}" marker-end="url(#arrow-${edgeKind(e)})"/>`).join('')}
    </svg><div class="flow-focus focus-node tone-${layerIndex(n.layer)}" style="top:${cy}px"><h3>${esc(n.label)}</h3><span>${esc(layerLabel(n.layer))}</span></div>
    ${incoming.map((r,i)=>renderNeighbor(r,i,'incoming')).join('')}${outgoing.map((r,i)=>renderNeighbor(r,i,'outgoing')).join('')}
    ${!incoming.length ? '<p class="lane-empty incoming">No incoming directed relationships in this selection.</p>' : ''}${!outgoing.length ? '<p class="lane-empty outgoing">No outgoing directed relationships in this selection.</p>' : ''}
    </div></div><p class="flow-caption">All ${incoming.length + outgoing.length} directed relationships · arrows read left → right</p>
    ${lanes.associated.length ? `<section class="associated-links" aria-label="Comparisons and unclassified connections"><div class="section-heading"><div><p class="eyebrow">ALONGSIDE THIS ENTRY</p><h3>Comparisons & unclassified connections</h3></div><span>${others.length} relationships · all shown</span></div><p class="fine-print">These links have no established upstream or downstream direction. Their labels distinguish explicit comparisons from unclassified older connections.</p><div class="associated-grid">${others.map(({edge:e,node})=>`<article class="associated-card" data-edge="${e.id}"><a href="${esc(connectedNodeHref(node.id))}">${esc(node.label)}</a><a class="edge-label kind-${edgeKind(e)} ${state.edge === e.id ? 'selected' : ''}" href="${esc(href({edge:e.id}))}">${esc(KINDS[edgeKind(e)])} · inspect</a><p class="associated-claim">${esc(e.relationship)}</p></article>`).join('')}</div></section>` : ''}`;
}

function focused() {
  const n = nodeById.get(state.node);
  const allRows = neighborhood(graph, n.id);
  const rows = neighborhood(graph, n.id, state.kind, state.neighborLayer);
  const e = graph.edges.find(e => e.id === state.edge);
  const returnPatch = {node: '', person: '', edge: '', section: '', page: 0, kind: '', neighborLayer: ''};
  const returnLabel = state.pathway ? 'Back to pathway' : state.query || state.layer || state.period || state.hunt ? 'Back to entries' : 'Back to atlas';
  return `${crumbs([`<a href="${esc(href(returnPatch))}">${returnLabel}</a>`, `<span aria-current="page">${esc(n.label)}</span>`])}
    ${schoolTabs(n)}${corePeople(n)}<div class="focus-layout"><section class="neighborhood" aria-labelledby="neighborhood-title"><div class="section-heading"><div><p class="eyebrow">03 / EXAMINE THE CONNECTIONS</p><h2 id="neighborhood-title">One entry, in conversation.</h2></div></div>
      <p class="context-note">All connections matching the selected filters are shown together. Read incoming relationships on the left and outgoing relationships on the right; comparisons and unclassified links appear below. Select a relationship to read its evidence.</p>
      <div class="neighborhood-controls"><label><span>Relationship</span><select id="kind-filter"><option value="">All relationships (${allRows.length})</option>${Object.entries(KINDS).map(([k, label]) => `<option value="${k}" ${state.kind === k ? 'selected' : ''}>${label} (${allRows.filter(r => edgeKind(r.edge) === k).length})</option>`).join('')}</select></label>
      <label><span>Connected layer</span><select id="neighbor-layer"><option value="">All layers</option>${layerOptions(state.neighborLayer)}</select></label>
      <div class="view-toggle" aria-label="Relationship view"><button data-view="map" aria-pressed="${state.view === 'map'}">Map</button><button data-view="list" aria-pressed="${state.view === 'list'}">List</button></div></div>
      <div class="graph-meta"><span>${rows.length} matching relationships · ${allRows.length} total</span><span>Upstream → focus → downstream</span></div>
      ${relationshipSummary(rows, n)}
      ${rows.length ? state.view === 'list' ? relationshipList(rows, n) : neighborhoodMap(rows, n) : '<div class="empty"><h3>No relationships match.</h3><button id="clear-neighbor-filters">Show all relationships</button></div>'}
      <div class="legend"><span class="legend-directed">→ Influence / contribution</span><span class="legend-critique">⇢ Critique</span><span class="legend-comparison">– – Comparison</span><span class="legend-unclassified">··· Unclassified</span></div><p class="fine-print">Only classified, directed relationships have arrows. Comparisons and unclassified connections are distinct; open a link to read the claim.</p>
    </section><aside class="reading-panel" aria-label="Entry and relationship details">${e ? edgeDetail(e) : nodeDetail(n)}</aside></div>`;
}
function pathwayPage() {
  const p = pathways.pathways.find(p => p.id === state.pathway);
  if (!p) return `${crumbs(['<span aria-current="page">Seminar pathways</span>'])}<div class="section-heading"><div><p class="eyebrow">FOLLOW A QUESTION</p><h2>Read across the map.</h2></div><p>Thirteen routes into historical explanation.</p></div><p class="context-note">${esc(pathways.interpretation_note)}</p><div class="pathway-grid">${pathways.pathways.map((p, i) => `<a class="pathway-card" href="#pathway=${p.id}"><span class="eyebrow">PATHWAY ${String(i + 1).padStart(2, '0')} · ${p.node_ids.length} ENTRIES</span><h3>${esc(p.title)}</h3><p>${esc(p.questions[0])}</p><span class="text-link">Begin reading →</span></a>`).join('')}</div>`;
  return `${crumbs(['<a href="#tab=pathways">Seminar pathways</a>', `<span aria-current="page">${esc(p.title)}</span>`])}
    <div class="section-heading"><div><p class="eyebrow">SEMINAR PATHWAY · ${p.node_ids.length} ENTRIES</p><h2>${esc(p.title)}</h2></div></div>
    <div class="pathway-layout"><section><p class="context-note">A suggested reading sequence, not a claim of influence. Open an entry to examine its connections, or <a href="#path=${esc(p.id)}">see these entries together on the field →</a></p><ol class="reading-sequence">${p.node_ids.map((id, i) => {
      const n = nodeById.get(id);
      return `<li><span class="sequence-number">${String(i + 1).padStart(2, '0')}</span><div>${layerTag(n)}<h3>${linkNode(id)}</h3><p>${esc(n.description)}</p></div></li>`;
    }).join('')}</ol></section><aside class="seminar-panel"><p class="eyebrow">BRING TO THE SEMINAR</p><h3>Questions to work with</h3><ol class="questions">${p.questions.map(q => `<li>${esc(q)}</li>`).join('')}</ol><div class="exercise"><p class="eyebrow">TRY THIS</p><p>${esc(p.exercise)}</p></div><details><summary>Compare explanations</summary><ul>${pathways.comparison_axes.map(a => `<li>${esc(a)}</li>`).join('')}</ul></details><p class="fine-print">Editorial teaching prompts, not quotations from Hunt.</p></aside></div>`;
}
function about() {
  return `${crumbs(['<span aria-current="page">Reading this map</span>'])}<article class="about"><p class="eyebrow">SCOPE & INTERPRETATION</p><h2>A map to think with.</h2><p class="deck">This is a selective, contestable teaching interpretation of historiography, for MA students reading Lynn Hunt’s <cite>Writing History in the Global Era</cite> (2014).</p>
    <h3>Move from traditions to people</h3><p>Start with four layers, open a school or field, and meet its representative historians and intellectual contributors. A shared person can appear in several groups with different roles. Open a profile for works and contexts, or switch to Connections to inspect the group’s relationships. Each map shows all recorded incoming relationships on the left and outgoing relationships on the right. Comparisons and unclassified connections appear separately below the flow. The full-text list also shows every connection.</p>
    <h3>Nesting is navigation</h3><p>The four layers organize a mixture of people, fields, traditions, methods, and debates. They do not define a historical family tree. Entries can connect across layers; seminar pathways overlap them. Hunt’s four paradigms are an explicit teaching lens, not a universal hierarchy.</p>
    <h3>Periods are approximate groupings</h3><p>Coverage is 1920–2000 with earlier roots. An extension beyond 2000 has not yet been written. Periods describe emergence or expansion, not termination, and prose date labels can refer to publication or reception. Entries without assigned periods remain available when you filter by a period. There is no continuous timeline.</p>
    <h3>Read the relationship before drawing a conclusion</h3><p>Influence, contribution, and classified critique have arrows. Critique runs from critic toward the position criticized; contribution does not imply founding a field. Comparisons have no direction. Older connections without direction metadata are visibly unclassified and have no arrow, including older records with a legacy critique category.</p>
    <h3>References have limits</h3><p>Bibliographic metadata checks establish the scope stated in their notes. A supporting page check is narrower than a full reading or a passage-level audit of every claim. Missing verification information means unrecorded. Some citations have no web link; relationship references are distinct from entry bibliographies.</p>
    <h3>What this beta does not yet cover</h3><p>Known gaps, so you can argue with the map
    rather than around it. <strong>About a quarter of entries record no objection at all</strong> —
    including Kuhn, Latour, SSK and science studies, where the disagreements of the 1990s
    “science wars” are missing. <strong>Coverage thins sharply after 1985</strong>, which is the
    period Hunt writes about most. <strong>Non-Western traditions appear mostly as subject
    matter rather than as historiography</strong>: African history and Subaltern Studies are here
    as traditions with their own institutions, but there is no Chinese, Japanese, Korean or
    Islamic historiography among the people in this graph. <strong>Most people have no entry
    of their own</strong> — they appear inside a school's roster, so they cannot be opened in the
    field view. Treat all of these as questions to raise, not as settled scope.</p>
    <h3>The journals are a first pass</h3><p>Journals appear only where a specific founding,
    debate or sustained principal-venue claim has a source. A journal that publishes work in a
    field is not, on its own, a link. Over 1,700 further periodicals are catalogued but not
    drawn, and a journal's small number of connections reflects what this map covers, not the
    journal's importance.</p>
    <h3>A selective scope</h3><p>${esc(graph.scope.geographic_emphasis)} Paired entries can contain contrasting approaches; read their qualifications. The map is not exhaustive and does not depict a sequence of superseded schools.</p>
    <p class="data-links"><a href="data/graph.json" download>Download curated graph</a><a href="data/pathways.json" download>Download seminar pathways</a></p><p class="fine-print">${graph.nodes.length} entries · ${graph.edges.length} relationships · ${graph.sources.length} bibliography records · ${pathways.pathways.length} pathways. Draft editorial revision ${esc(revision())}.</p></article>`;
}
function render() {
  $('toolbar').hidden = !['map','people','browse'].includes(state.tab) || Boolean(state.node || state.person);
  $('search').value = state.query;
  $('layer-filter').value = state.layer;
  $('period-filter').value = state.period;
  $('hunt-filter').checked = state.hunt;
  document.querySelectorAll('[data-tab]').forEach(a => {
    const tab = state.person ? 'people' : state.pathway ? 'pathways' : state.node ? 'browse'
      : state.tab === 'map' ? 'field' : state.tab;
    if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  const onField = state.tab === 'map' && !state.node && !state.person;
  document.body.dataset.view = onField ? 'field' : '';
  document.body.dataset.compact = onField ? '' : '1';
  $('workspace').innerHTML = state.person ? personPage()
    : state.node ? (nodeById.get(state.node).representative_people?.length && state.section !== 'connections' ? schoolPeople() : focused())
    : onField ? fieldPage()
    : state.tab === 'people' ? peopleDirectory()
    : state.tab === 'about' ? about()
    : state.tab === 'pathways' ? pathwayPage()
    : state.layer || state.query || state.period || state.hunt ? directory() : overview();
  if (onField) wireField();
  document.title = `${state.person ? personById.get(state.person).label : state.node ? nodeById.get(state.node).label : state.pathway ? pathways.pathways.find(p => p.id === state.pathway).title : 'Historiography'} · A seminar atlas`;
  $('announcement').textContent = state.tab === 'map' && !state.node && !state.person
    ? (state.focus ? `${fieldNodeById.get(state.focus).label} held in the field view.`
       : state.path ? `Pathway ${pathways.pathways.find(p => p.id === state.path).title} shown on the field.`
       : `Field view. ${fieldNodes(graph).length} entries on a time axis.`)
    : state.person ? personById.get(state.person).label : state.node ? `${nodeById.get(state.node).label}. ${state.section === 'connections' ? 'Connections view.' : rosterLabel(nodeById.get(state.node))}` : state.tab === 'people' ? `${filterPeople(graph,state).length} matching people.` : state.tab === 'map' ? `${filterNodes(graph.nodes,state,graph.people).length} matching entries.` : state.pathway ? pathways.pathways.find(p=>p.id===state.pathway).title : state.tab === 'pathways' ? 'Seminar pathways.' : 'Reading this map.';
  const resetLanes = {page:0};
  $('kind-filter')?.addEventListener('change', e => change({kind: e.target.value, ...resetLanes}));
  $('neighbor-layer')?.addEventListener('change', e => change({neighborLayer: e.target.value, ...resetLanes}));
}
async function start() {
  try {
    [graph, pathways] = await Promise.all(['data/graph.json', 'data/pathways.json'].map(async url => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${url} (${response.status})`);
      return response.json();
    }));
    nodeById = new Map(graph.nodes.map(n => [n.id, n]));
    sourceById = new Map(graph.sources.map(s => [s.id, s]));
    personById = new Map(graph.people.map(p => [p.id, p]));
    personNames = new Map(graph.people.map(p => [p.id, p.label]));
    fieldCatalogue = journalNodes(graph);
    journalSourceById = new Map((graph.journal_catalogue?.sources || []).map(s => [s.id, s]));
    atlasEdgeIds = new Set(graph.edges.map(e => e.id));
    window.addEventListener('resize', onResize);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && state.focus && document.querySelector('svg.field')
          && !e.target.closest('input, select, textarea')) change({focus: ''});
    });
    fieldIndex = relationIndex(graph);
    fieldNodeById = new Map(fieldNodes(graph).map(n => [n.id, n]));
    graph.__fieldNodes = fieldNodes(graph);
    $('total-entries').textContent = graph.nodes.length;
    $('edition-label').textContent = `Draft ${revision()}`;
    $('layer-filter').insertAdjacentHTML('beforeend', layerOptions(''));
    $('period-filter').insertAdjacentHTML('beforeend', graph.periods.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('') + '<option value="unassigned">No assigned period</option>');
    state = readRoute(location.hash, graph, pathways);
    // Prefer the full-text list on narrow screens unless the URL chooses a view.
    if (matchMedia('(max-width: 700px)').matches && !new URLSearchParams(location.hash.slice(1)).has('view')) state.view = 'list';
    render();
    window.addEventListener('hashchange', () => {
      const focusedId = document.activeElement?.id;
      const old = state;
      state = readRoute(location.hash, graph, pathways);
      if (matchMedia('(max-width: 700px)').matches && !new URLSearchParams(location.hash.slice(1)).has('view')) state.view = 'list';
      render();
      if (state.edge && state.edge !== old.edge) $('detail-title')?.focus({preventScroll: !matchMedia('(max-width: 1000px)').matches});
      else if (focusedId && $(focusedId) && !$(focusedId).closest('[hidden]')) $(focusedId).focus({preventScroll: true});
      else {
        $('workspace').focus({preventScroll: true});
        if (state.node !== old.node || state.person !== old.person || state.section !== old.section || state.tab !== old.tab || state.pathway !== old.pathway) $('workspace').scrollIntoView({block: 'start'});
      }
    });
    $('search').addEventListener('input', e => change({query: e.target.value, node: '', person: '', edge: '', page: 0}, true));
    $('layer-filter').addEventListener('change', e => change({layer: e.target.value, page: 0}));
    $('period-filter').addEventListener('change', e => change({period: e.target.value, page: 0}));
    $('hunt-filter').addEventListener('change', e => change({hunt: e.target.checked, page: 0}));
    $('workspace').addEventListener('click', e => {
      const button = e.target.closest('button');
      if (!button) return;
      if (button.dataset.page !== undefined) change({page: Number(button.dataset.page)});
      if (button.dataset.view) change({view: button.dataset.view});
      if (button.id === 'clear-neighbor-filters') change({kind: '', neighborLayer: '', page: 0});
    });
  } catch (error) {
    $('workspace').innerHTML = `<div class="empty"><h2>The atlas could not be opened.</h2><p>${esc(error.message)}</p><p>Build the site and serve its dedicated output directory, then reload.</p><button onclick="location.reload()">Try again</button></div>`;
  }
}
start();
