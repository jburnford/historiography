import {PAGE_SIZE, LAYER_TITLES, KINDS, PERSON_ROLES, edgeKind, hasArrow, filterNodes, filterPeople, personContexts, neighborhood, partitionNeighborhood, readRoute, routeHash, OVERVIEW_PATCH} from './core.mjs';
import {buildFieldLayout, fieldNodes, fieldEdges, fieldKinds, fieldLayers, relationIndex, milestoneYears, lifeIndex,
  focusSetFor, fieldMatches, journalNodes, spanOf, anchor, edgePath, kindLabel, kindChip, dirWord,
  pathwaySet, pathwayEdges, BASE_KINDS, JOURNAL_LAYER, extensionOf, interventionsOf} from './field.mjs';
import {sortName, bySurname, companyLayout, bridges} from './people.mjs';
import {VIEWS, stripSegments, familyBySlug, familyGraph, rowsSvg, cardsHtml, tableHtml} from './landing.mjs';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
let graph, pathways, state, nodeById, sourceById, personById, personNames;
/* `production` is the current graph; `baselineGraph` the archived 2000 graph, loaded on demand
   for the exact baseline view. `catalogue` indexes the claim catalogue of whichever is shown. */
let production, baselineGraph = null, catalogue = {entities: new Map(), claims: new Map(), records: new Map()};
/* The evidence layer (data/evidence.json): aggregates from reviews and journal metadata, shown
   beside an entry's interpretation and never merged into it. Loaded with the graph; the landing needs it. */
let evidence = null;
const revision = () => graph.revision_history.at(-1).version;
const activeExtension = () => state?.range === '2000' ? null : extensionOf(graph);
function adopt(g) {
  graph = g;
  nodeById = new Map(graph.nodes.map(n => [n.id, n]));
  sourceById = new Map(graph.sources.map(s => [s.id, s]));
  personById = new Map(graph.people.map(p => [p.id, p]));
  personNames = new Map(graph.people.map(p => [p.id, p.label]));
  fieldCatalogue = journalNodes(graph);
  journalSourceById = new Map((graph.journal_catalogue?.sources || []).map(s => [s.id, s]));
  atlasEdgeIds = new Set(graph.edges.map(e => e.id));
  fieldIndex = relationIndex(graph);
  fieldNodeById = new Map(fieldNodes(graph).map(n => [n.id, n]));
  graph.__fieldNodes = fieldNodes(graph);
  const cc = graph.claim_catalogue || {};
  catalogue = {entities: new Map((cc.entities || []).map(e => [e.id, e])),
    claims: new Map((cc.claims || []).map(c => [c.id, c])),
    records: new Map((cc.source_records || []).map(r => [r.id, r]))};
  $('total-entries').textContent = graph.nodes.length;
}
/* The 2000 view is the archived baseline graph itself, never a date filter over the current one. */
async function ensureRange(range) {
  const asset = production.scope?.extension?.baseline_asset;
  if (range === '2000' && asset) {
    if (!baselineGraph) {
      const response = await fetch(asset);
      if (!response.ok) throw new Error(`Could not load ${asset} (${response.status})`);
      baselineGraph = await response.json();
    }
    if (graph !== baselineGraph) adopt(baselineGraph);
  } else if (graph !== production) adopt(production);
}
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
const lifeSpan = p => {
  if (!p.life?.birth && !p.life?.death) return '';
  const y = (v, k) => v ? `${['year', 'decade', 'century'].includes(p.life[`${k}_precision`]) ? 'c. ' : ''}${String(v).slice(0, 5).replace(/-$/, '')}` : '';
  return ` <span class="lifespan">${esc(y(p.life.birth, 'birth'))}–${esc(y(p.life.death, 'death'))}</span>`;
};
/* ---------------- Claim catalogue: exact claims and their evidence ---------------- */
const CHECK_LABELS = {passage_checked: 'Passage checked', abstract_checked: 'Abstract only checked',
  metadata_checked: 'Bibliographic metadata checked', description_checked: 'Publisher description checked', not_checked: 'Not checked'};
const REVIEW_LABELS = {accepted: 'Accepted', needs_review: 'Needs review', provisional: 'Provisional', rejected: 'Rejected'};
const PREDICATES = {authored: 'authored', contributes_to: 'contributes to', assesses_scope: 'assesses the scope of', critiques: 'critiques',
  qualifies: 'qualifies', related_concept: 'is related to', proposes_programme: 'proposes a programme for', realizes: 'is realized in', entry_presents: 'is presented in'};
const reviewBadge = status => status ? `<span class="badge status-${esc(status)}">${esc(REVIEW_LABELS[status] || status.replace(/_/g, ' '))}</span>` : '';
const entityOf = id => catalogue.entities.get(id);
function entityLink(id) {
  const e = entityOf(id);
  const label = e?.label || String(id).replace(/^[a-z_]+:/, '').replace(/_/g, ' ');
  if (e?.type === 'person') { const pid = e.legacy_person_id || id.split(':').pop(); if (personById.has(pid)) return `<a href="${esc(personHref(pid))}">${esc(label)}</a>`; }
  if (e?.type === 'atlas_entry' && nodeById.has(e.legacy_id)) return `<a href="${esc(nodeHref(e.legacy_id))}">${esc(label)}</a>`;
  if (e?.type === 'concept' && e.field_navigation_ids?.[0] && nodeById.has(e.field_navigation_ids[0])) return `<span class="concept">${esc(label)}</span> <span class="fine-print">(within ${linkNode(e.field_navigation_ids[0])})</span>`;
  return `<span class="${e?.type === 'work' ? 'work-title' : ''}">${esc(label)}</span>`;
}
function evidenceList(evidence) {
  if (!evidence?.length) return '<p class="fine-print">No evidence join recorded for this claim.</p>';
  return `<ul class="evidence-list">${evidence.map(ev => { const rec = catalogue.records.get(ev.source_record_id);
    const url = /^https?:\/\//.test(rec?.url || '') ? rec.url : null;
    return `<li><p class="ev-head"><span class="badge check-${esc(ev.check_status || 'not_checked')}">${esc(CHECK_LABELS[ev.check_status] || 'Check unrecorded')}</span>${ev.scope ? `<span class="ev-scope">scope: ${esc(ev.scope)}</span>` : ''}${ev.checked_on ? `<span class="ev-scope">checked ${esc(ev.checked_on)}</span>` : ''}</p>
      ${ev.locator ? `<p class="ev-locator"><strong>Where.</strong> ${esc(ev.locator)}</p>` : ''}
      ${ev.support ? `<p><strong>Supports.</strong> ${esc(ev.support)}</p>` : ''}
      ${ev.limitation ? `<p class="ev-limit"><strong>Limit.</strong> ${esc(ev.limitation)}</p>` : ''}
      ${rec ? `<p class="fine-print">Witness: ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(rec.provider || 'source')}<span class="sr-only"> (opens in a new tab)</span> ↗</a>` : esc(rec.provider || rec.id)}${rec.access_note ? ` · ${esc(rec.access_note)}` : ''}. Capture kept as repository provenance, not fetched by the browser.</p>` : ''}</li>`; }).join('')}</ul>`;
}
function claimCard(id) {
  const c = catalogue.claims.get(id);
  if (!c) return `<li class="claim-card"><p class="fine-print">Claim ${esc(id)} is not in the published catalogue.</p></li>`;
  return `<li class="claim-card"><p class="claim-head">${reviewBadge(c.review?.status)}${c.intervention_year ? `<span class="claim-year">Intervention · ${esc(c.intervention_year)}</span>` : ''}</p>
    <p class="claim-endpoints">${entityLink(c.subject)} <em>${esc(PREDICATES[c.predicate] || c.predicate.replace(/_/g, ' '))}</em> ${typeof c.object === 'string' ? entityLink(c.object) : esc(JSON.stringify(c.object))}</p>
    <p class="claim-statement">${esc(c.statement)}</p>
    ${c.qualification ? `<p class="claim-qual"><strong>Qualification.</strong> ${esc(c.qualification)}</p>` : ''}
    <details class="claim-evidence"><summary>Evidence · ${c.evidence?.length || 0}</summary>${evidenceList(c.evidence)}</details></li>`;
}
const claimCards = ids => ids?.length ? `<ol class="claim-list">${ids.map(claimCard).join('')}</ol>` : '';
/* A work with every credited author, its consulted versions and the historical claims made from it. */
function workCard(workId) {
  const w = entityOf(workId);
  if (!w) return '';
  const authors = (w.author_ids || []).map(entityLink);
  const versions = [...catalogue.entities.values()].filter(e => e.type === 'version' && e.work_id === workId);
  const claims = [...catalogue.claims.values()].filter(c => (c.subject === workId || c.attributed_to === workId) && !['authored', 'entry_presents'].includes(c.predicate)).map(c => c.id);
  return `<article class="work-card"><h4>${esc(w.label)}</h4>
    <p class="work-meta">${w.publication_year_observation ? `Intervention · <strong>${esc(w.publication_year_observation)}</strong>` : 'Year unrecorded'}${w.language && w.language !== 'en' ? ` · language: ${esc(w.language)}` : ''}${w.date_note ? ` · <span class="fine-print">${esc(w.date_note)}</span>` : ''}</p>
    <p class="work-authors"><strong>${authors.length === 1 ? 'Author' : `Authors · ${authors.length}`}.</strong> ${authors.join(', ') || 'Not recorded'}</p>
    ${versions.map(v => `<p class="work-version"><strong>Consulted as.</strong> ${esc(v.label)}${v.version_year ? ` (${esc(v.version_year)})` : ''}${v.scope_note ? ` — ${esc(v.scope_note)}` : ''} The intervention keeps its original date.</p>`).join('')}
    ${claims.length ? `<p class="fine-print">${claims.length} historical claim${claims.length === 1 ? '' : 's'} made from this work; each carries its own evidence scope.</p>${claimCards(claims)}` : '<p class="fine-print">No historical claim beyond authorship is recorded for this work.</p>'}</article>`;
}
/* Selected interventions after the coverage limit, shown apart from the entry's original mark. */
function extensionSection(n) {
  const c = n.extension_coverage;
  if (!c || state.range === '2000') return '';
  const years = [...new Set(c.publication_years || [])].sort((a, b) => a - b);
  const statusText = c.status === 'release_candidate' ? 'Release candidate · not yet accepted into production'
    : /accepted/.test(c.status || '') ? 'Partial release · accepted' : (c.status || '').replace(/_/g, ' ');
  return `<section class="extension" aria-label="Selected interventions after 2000"><div class="ext-head"><p class="eyebrow">AFTER ${esc(c.baseline_through || 2000)} · SELECTED INTERVENTIONS</p><span class="badge status-${esc(c.status || 'release_candidate')}">${esc(statusText)}</span></div>
    <p class="context-note">${years.length} publication${years.length === 1 ? '' : 's'} selected (${esc(years.join(', '))}). Research cutoff ${esc(c.research_cutoff || 'unrecorded')}. ${c.field_review_complete ? 'This field has been reviewed through the cutoff.' : 'This field is <strong>not</strong> reviewed through the cutoff: these are selected interventions, not a survey of the field after 2000.'} The original mark and its coverage through ${esc(c.baseline_through || 2000)} are unchanged.</p>
    ${(c.work_ids || []).map(workCard).join('')}</section>`;
}
function personCard(p, rep = null) {
  const contexts = personContexts(graph, p.id);
  const readings = [...new Set(contexts.map(c => c.representative.works).filter(Boolean))];
  const own = nodeById.get(p.node_id);
  const work = rep ? (rep.works || own?.representative_figures_and_works || '') : (readings[0] || own?.representative_figures_and_works || '');
  return `<article class="person-card"><p class="eyebrow">${rep ? esc(PERSON_ROLES[rep.role]) : `${contexts.length} GROUP${contexts.length === 1 ? '' : 'S'}${own ? ' · FULL ENTRY' : ''}`}</p>
    <h3><a href="${esc(personHref(p.id))}">${esc(p.label)}</a>${lifeSpan(p)}</h3>
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
  return `<section class="strand-guide" aria-label="Approaches within this entry"><h3>Different approaches within this entry</h3><p class="fine-print">Overlapping approaches and debates, not a sequence of schools replacing one another.</p>${n.strands.map(branch => `<details class="strand${branch.intervention_year ? ' strand-extension' : ''}"><summary>${esc(branch.title)}${branch.intervention_year ? `<span class="strand-year">${esc(branch.intervention_year)}</span>` : ''}</summary>${branch.intervention_year ? `<p class="strand-meta">Selected intervention · ${esc(branch.intervention_year)} ${reviewBadge(branch.review_status)}<span class="fine-print"> A work's year is not the field's origin or a career boundary.</span></p>` : ''}<p>${esc(branch.focus)}</p><p class="strand-people">${branch.person_ids.map(id => `<a href="${esc(personHref(id))}">${esc(personById.get(id)?.label || id)}</a>`).join(' · ')}</p><p class="person-work">${esc(branch.works)}</p>${branch.claim_ids?.length ? `<details class="strand-claims"><summary>Exact claims · ${branch.claim_ids.length}</summary>${claimCards(branch.claim_ids)}</details>` : ''}<details><summary>Reading references</summary><p class="fine-print">These readings have different scopes; see their source notes.</p>${sourceList(branch.source_ids)}</details></details>`).join('')}</section>`;
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
      ${extensionSection(n)}${strandGuide(n)}<div class="people-grid">${pageSlice(reps, 12).map(rep => personCard(personById.get(rep.person_id), rep)).join('')}</div>${pagination(reps.length, 12)}</section>
      <aside class="reading-panel" aria-label="Entry details">${nodeDetail(n)}</aside></div>`;
}
/* ---------------- Historians & contributors: the company they keep ---------------- */
let companyHover = null, companyWidth = 0, companyBound = false;
const holdHref = id => href({hold: id, letter: '', page: 0});
const ROLE_SHORT = {historian: 'historian', contributor: 'resource', precursor: 'earlier resource', critic: 'critic', comparison: 'comparison'};
const filtersOn = () => Boolean(state.query || state.layer || state.period || state.hunt);
const nameMark = label => { const {surname} = sortName(label); const i = label.indexOf(surname);
  return i < 0 ? esc(label) : `${esc(label.slice(0, i))}<strong>${esc(surname)}</strong>${esc(label.slice(i + surname.length))}`; };
function companySvg(L, matched, allowed) {
  const t = id => layerIndex(nodeById.get(id).layer);
  const own = id => Boolean(personById.get(id)?.node_id);
  const spokes = L.people.filter(p => !p.single).flatMap(p => p.entries.map(g => { const a = L.anchors.find(x => x.id === g);
    return `<line class="spoke" data-p="${p.id}" data-g="${g}" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${a.x.toFixed(1)}" y2="${a.y.toFixed(1)}"/>`; })).join('');
  const dots = L.people.map(p => {
    const label = personById.get(p.id).label;
    const cls = ['dot', p.single ? `tone-${layerIndex(p.layer)}` : 'bridge', own(p.id) ? 'own' : '', p.roles.includes('critic') ? 'critic' : '',
      p.roles.includes('historian') || own(p.id) ? '' : 'resource', matched && !matched.has(p.id) ? 'mute' : '', state.hold === p.id ? 'selected' : ''].filter(Boolean).join(' ');
    const r = own(p.id) ? L.size * 0.0033 + 1.6 : L.size * 0.0021 + 1;
    const body = `<title>${esc(label)} · ${p.entries.length} entr${p.entries.length === 1 ? 'y' : 'ies'}</title>
      ${p.roles.includes('critic') ? `<circle class="ring" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${(r + 1.6).toFixed(1)}"/>` : ''}
      <circle class="core" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r.toFixed(1)}"/>
      ${own(p.id) && p.entries.length >= 4 ? `<text class="dot-label" x="${(p.x + r + 3).toFixed(1)}" y="${(p.y + 3.5).toFixed(1)}">${esc(label)}</text>` : ''}`;
    return own(p.id) ? `<a class="${cls}" data-id="${p.id}" href="${esc(holdHref(p.id))}" aria-label="${esc(label)}: light up their entries">${body}</a>` : `<g class="${cls}" data-id="${p.id}">${body}</g>`;
  }).join('');
  const anchors = L.anchors.map(a => {
    const deg = a.angle * 180 / Math.PI, flip = ((deg % 360) + 360) % 360 > 90 && ((deg % 360) + 360) % 360 < 270;
    const lx = L.cx + (L.R + 16) * Math.cos(a.angle), ly = L.cy + (L.R + 16) * Math.sin(a.angle);
    /* Fit the label to the space outside the ring: first drop a subtitle after a slash or
       colon, then cut on a word boundary. The full label stays in the accessible name. */
    const max = Math.floor(L.labelSpace / 6); let label = a.label;
    if (label.length > max) label = label.split(/\s[/:]\s|:\s/)[0];
    if (label.length > max) label = `${label.slice(0, max - 1).replace(/\s+\S*$/, '')}…`;
    const cls = ['anchor', `tone-${t(a.id)}`, allowed && !allowed.has(a.id) ? 'mute' : '', state.hold === a.id ? 'selected' : ''].filter(Boolean).join(' ');
    return `<a class="${cls}" data-id="${a.id}" href="${esc(holdHref(a.id))}" aria-label="${esc(a.label)}, ${a.count} people"><circle cx="${a.x.toFixed(1)}" cy="${a.y.toFixed(1)}" r="${(L.size * 0.0045 + 2).toFixed(1)}"/>
      <text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" transform="rotate(${(flip ? deg + 180 : deg).toFixed(1)} ${lx.toFixed(1)} ${ly.toFixed(1)})" text-anchor="${flip ? 'end' : 'start'}" dominant-baseline="middle">${esc(label)} <tspan>${a.count}</tspan></text></a>`;
  }).join('');
  return `<svg class="company${state.hold ? ' held' : ''}" viewBox="0 0 ${L.size} ${L.size}" width="${L.size}" height="${L.size}" role="group" aria-label="People placed between the entries that name them">
    <g class="spokes">${spokes}</g><g class="dots">${dots}</g><g class="anchors">${anchors}</g></svg>`;
}
function companyPanel(L) {
  const id = companyHover || state.hold;
  const release = state.hold && !companyHover ? `<p class="panel-release"><a class="release" href="${esc(href({hold: ''}))}">← Show everyone</a></p>` : '';
  if (!id) {
    const top = bridges(graph, L.byPerson, 8);
    return `<div class="panel-empty"><p class="eyebrow">Nothing selected</p>
      <h2>Hover a dot to see whose company they keep. Click to hold.</h2>
      <p>Each of the ${L.anchors.length} entries sits on the ring with the number of people it names. A person named in one entry gathers at that entry, in its colour. A person named in several entries moves inward, between them, in ink. The bigger dots are the ${graph.people.filter(p => p.node_id).length} people who also have an entry of their own.</p>
      <ul class="company-legend"><li><span class="lg lg-hist"></span>named as historian</li><li><span class="lg lg-res"></span>named as resource or comparison</li><li><span class="lg lg-crit"></span>critical intervention</li><li><span class="lg lg-own"></span>has own entry</li></ul>
      <div class="sec"><p class="eyebrow">Named in the most entries</p><ol class="bridge-list">${top.map(b => `<li><a href="${esc(holdHref(b.id))}" aria-label="${esc(b.label)}: light up their entries">${esc(b.label)}</a><span>${b.count}</span></li>`).join('')}</ol></div>
      <p class="fine-print">Sharing an entry is shared context, not influence: no line is drawn between two people, and a roster place is not an edge. Placement is the plain mean of an entry’s positions, not a force layout.</p></div>`;
  }
  if (personById.has(id)) {
    const p = personById.get(id); const rows = L.byPerson.get(id) || []; const own = nodeById.get(p.node_id);
    return `${release}<p class="eyebrow">${rows.length ? `Named in ${new Set(rows.map(r => r.id)).size} entr${new Set(rows.map(r => r.id)).size === 1 ? 'y' : 'ies'}` : 'Own entry only'}${own ? ' · has own entry' : ''}</p>
      <h2>${esc(p.label)}${lifeSpan(p)}</h2>${own ? `<p class="claim">${esc(own.description)}</p>` : ''}
      <ul class="panel-entries">${rows.map(r => `<li><a href="${esc(holdHref(r.id))}">${esc(nodeById.get(r.id).label)}</a><span class="role-tag">${esc(PERSON_ROLES[r.role])}</span></li>`).join('')}</ul>
      <p class="panel-more"><a class="button-link" href="${esc(personHref(id))}">Profile: where to read them →</a>${own ? ` <a class="button-link" href="${esc(nodeHref(own.id))}">Full entry →</a>` : ''}</p>`;
  }
  const n = nodeById.get(id); const rows = L.byEntry.get(id) || [];
  const reps = new Map((n.representative_people || []).map(r => [r.person_id, r]));
  const groups = ['historian', 'contributor', 'critic', 'precursor', 'comparison'].map(role => [role, rows.filter(r => r.role === role)]).filter(([, r]) => r.length);
  /* One person per line with the work the entry cites, so a long roster can be scanned. */
  const line = x => { const rep = reps.get(x.id); const work = (rep?.works || '').split(';')[0].trim();
    return `<li><a href="${esc(holdHref(x.id))}">${esc(personById.get(x.id).label)}</a>${lifeSpan(personById.get(x.id))}${work ? `<span class="panel-work">${esc(work.length > 70 ? `${work.slice(0, 69)}…` : work)}</span>` : ''}</li>`; };
  return `${release}<p class="eyebrow">${esc(layerLabel(n.layer))} · ${rows.length} people</p><h2>${esc(n.label)}</h2><p class="meta">${esc(n.date_label || '')}</p>
    ${groups.map(([role, r]) => `<div class="sec"><p class="eyebrow">${esc(PERSON_ROLES[role])}${r.length > 1 ? `s · ${r.length}` : ''}</p><ul class="panel-roster">${[...r].sort((a, b) => bySurname(personById.get(a.id), personById.get(b.id))).map(line).join('')}</ul></div>`).join('')}
    <p class="panel-more"><a class="button-link" href="${esc(nodeHref(id))}">Open the entry →</a></p>`;
}
function register(L) {
  const matched = filterPeople(graph, state);
  const letters = new Set(matched.map(p => sortName(p.label).initial));
  let rows, title, note = '';
  if (state.hold && personById.has(state.hold)) { rows = [personById.get(state.hold)]; title = 'Held'; }
  else if (state.hold && nodeById.has(state.hold)) { const ids = new Set((L.byEntry.get(state.hold) || []).map(r => r.id)); rows = matched.filter(p => ids.has(p.id)); title = `Named in ${nodeById.get(state.hold).label}`; }
  else if (filtersOn()) { rows = matched; title = `${matched.length} people match`; }
  else if (state.letter) { rows = matched.filter(p => sortName(p.label).initial === state.letter); title = `Surnames beginning with ${state.letter}`; }
  else { rows = matched.filter(p => p.node_id); title = 'People with an entry of their own'; note = 'Everyone else is one letter away. Sorted by surname; particles such as “de” and “von” follow the given name in the sort.'; }
  rows = [...rows].sort(bySurname);
  const rail = `<nav class="letter-rail" aria-label="Register by surname"><a href="${esc(href({letter: '', hold: '', page: 0}))}" ${!state.letter && !state.hold && !filtersOn() ? 'aria-current="page"' : ''}>Own entries</a>${'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(l => letters.has(l)
    ? `<a href="${esc(href({letter: l, hold: '', page: 0}))}" ${state.letter === l && !state.hold && !filtersOn() ? 'aria-current="page"' : ''}>${l}</a>` : `<span class="off" aria-hidden="true">${l}</span>`).join('')}</nav>`;
  const row = p => { const rs = L.byPerson.get(p.id) || []; const own = nodeById.get(p.node_id);
    return `<li class="reg-row"><a class="reg-name" href="${esc(personHref(p.id))}">${nameMark(p.label)}</a><span class="reg-life">${lifeSpan(p) || ''}</span>
      <span class="reg-entries">${rs.map(r => `<a href="${esc(nodeHref(r.id))}">${esc(nodeById.get(r.id).label)}</a><small>${esc(ROLE_SHORT[r.role])}</small>`).join(' · ') || (own ? esc(layerLabel(own.layer)) : '')}</span>
      <span class="reg-more">${own ? `<a href="${esc(nodeHref(own.id))}">Full entry →</a>` : `<a href="${esc(holdHref(p.id))}">Light up →</a>`}</span></li>`; };
  return `${rail}<div class="register-head"><h3>${esc(title)}</h3><span class="count">${rows.length} of ${graph.people.length} people${note ? '' : ''}</span></div>${note ? `<p class="context-note">${esc(note)}</p>` : ''}
    ${rows.length ? `<ol class="register">${rows.map(row).join('')}</ol>` : '<div class="empty"><h3>No people match.</h3><a href="#tab=people">Clear filters →</a></div>'}`;
}
function peopleDirectory() {
  const L = companyLayout(graph, 1000);
  return `${crumbs(['<span aria-current="page">Historians & contributors</span>'])}<div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THE MAP</p><h2>The company they keep</h2></div><span class="count">${graph.people.length} people · ${L.anchors.length} entries that name them</span></div>
    <p class="context-note">Every person in this atlas is placed between the schools, fields and debates that name them. Hover to see whose company someone keeps; click to hold; search or filter above to light up a subset. Roles distinguish historians from intellectual resources and critics; being named together is shared context, not influence.</p>
    <div class="company-split"><div class="company-chart" aria-busy="true"></div><aside class="field-panel company-panel" aria-label="Selection details">${companyPanel(L)}</aside></div>
    <section class="register-section" aria-label="Register of people">${register(L)}</section>`;
}
function drawCompany() {
  const box = document.querySelector('.company-chart');
  if (!box) return;
  companyWidth = box.clientWidth || 0;
  if (!companyWidth) return;   /* hidden on narrow screens; the register carries the content */
  const L = companyLayout(graph, companyWidth);
  const matched = filtersOn() ? new Set(filterPeople(graph, state).map(p => p.id)) : null;
  const allowed = filtersOn() ? new Set(filterNodes(graph.nodes, {...state, query: ''}).map(n => n.id)) : null;
  box.innerHTML = companySvg(L, matched, allowed);
  box.removeAttribute('aria-busy');
  const svg = box.querySelector('svg.company');
  const panel = document.querySelector('.company-panel');
  const paint = () => { panel.innerHTML = companyPanel(L); };
  const light = id => {
    const related = new Set();
    if (id && L.byPerson.has(id)) for (const r of L.byPerson.get(id)) related.add(r.id);
    if (id && L.byEntry.has(id)) for (const r of L.byEntry.get(id)) related.add(r.id);
    svg.classList.toggle('previewing', Boolean(id));
    for (const el of svg.querySelectorAll('[data-id]')) el.classList.toggle('hi', el.dataset.id === id || related.has(el.dataset.id));
    for (const sp of svg.querySelectorAll('.spoke')) sp.classList.toggle('hi', sp.dataset.p === id || sp.dataset.g === id);
  };
  const preview = target => {
    const id = target.closest?.('[data-id]')?.dataset.id || null;
    if (id === companyHover) return;
    companyHover = id; light(id || state.hold || null); paint();
  };
  const clear = () => { if (companyHover === null) return; companyHover = null; light(state.hold || null); paint(); };
  svg.addEventListener('mouseover', e => preview(e.target));
  svg.addEventListener('mouseleave', clear);
  svg.addEventListener('focusin', e => preview(e.target));
  svg.addEventListener('focusout', e => { if (!svg.contains(e.relatedTarget)) clear(); });
  svg.addEventListener('click', e => {
    const dot = e.target.closest?.('g.dot');
    if (dot) { change({hold: state.hold === dot.dataset.id ? '' : dot.dataset.id, letter: ''}); return; }
    if (!e.target.closest('a') && state.hold) change({hold: ''});
  });
  if (state.hold) light(state.hold);
  if (!companyBound) {
    companyBound = true;
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && state.hold && state.tab === 'people' && !state.person) change({hold: ''}); });
  }
}

function personPage() {
  const p = personById.get(state.person);
  const contexts = personContexts(graph, p.id);
  const own = nodeById.get(p.node_id);
  const parent = nodeById.get(state.node);
  const origin = parent ? `<a href="${esc(href({person: '', page: 0, section: ''}))}">${esc(parent.label)}</a>` : '<a href="#tab=people">Historians & contributors</a>';
  const basisLabels = {curated_entry: 'Selection recorded in the curated entry', existing_relationship: 'Selection supported by an existing qualified connection', source_review: 'Selection with a scoped source check', editorial_comparison: 'Editorial comparison across constituent fields'};
  return `${crumbs([origin, `<span aria-current="page">${esc(p.label)}</span>`])}<article class="person-profile"><div class="section-heading"><div><p class="eyebrow">A PERSON ACROSS THE MAP</p><h2>${esc(p.label)}${lifeSpan(p)}</h2>${p.wikidata?.qid ? `<p class="fine-print">Identity: <a href="https://www.wikidata.org/wiki/${esc(p.wikidata.qid)}" target="_blank" rel="noopener noreferrer">Wikidata ${esc(p.wikidata.qid)}</a>${p.life?.retrieved ? `, dates retrieved ${esc(p.life.retrieved)}` : ''}.</p>` : ''}</div>${own ? `<a class="button-link" href="${esc(nodeHref(own.id))}">Full entry & relationships →</a>` : ''}</div>
    ${own ? `<p class="profile-introduction">${esc(own.description)}</p>` : '<p class="context-note">Read this person through the works and contexts below. These are selected points of entry, not a complete biography.</p>'}
    <h3>Where to read them</h3><div class="person-contexts">${contexts.map(({node:n, representative:r}) => `<section class="person-affiliation tone-${layerIndex(n.layer)}">${layerTag(n)}<h3><a href="${esc(nodeHref(n.id))}">${esc(n.label)} →</a></h3><span class="role-tag">${esc(PERSON_ROLES[r.role])}</span><p>${esc(r.context)}</p>
      ${r.works ? `<p class="person-work">${esc(r.works)}</p>` : `<p class="fine-print">The current selection names this person without a separate work citation. <a href="${esc(nodeHref(n.id))}">Read the group’s works and references.</a></p>`}
      <details class="person-evidence"><summary>References & basis for inclusion</summary><p class="fine-print">${esc(basisLabels[r.basis])}. Group references provide context; they do not certify every affiliation or interpretation.</p>${r.edge_id ? `<a class="text-link" href="#edge=${r.edge_id}">Inspect the existing relationship →</a>` : ''}${sourceList(r.source_ids)}</details></section>`).join('')}</div>
    ${!contexts.length && own ? `<p>No group roster currently includes this person. Their individual entry provides the selected works and connections.</p><section class="reading-panel"><h3>Representative figures & works</h3><p>${esc(own.representative_figures_and_works)}</p><details class="bibliography" open><summary>References</summary>${sourceList(own.source_ids)}</details></section>` : ''}
    ${strandContexts(p)}
    </article>`;
}
/* Approaches (strands) that name a person, including works added after the roster record. */
function strandContexts(p) {
  const hits = graph.nodes.flatMap(n => (n.strands || []).filter(s => s.person_ids?.includes(p.id)).map(strand => ({n, strand})));
  if (!hits.length) return '';
  return `<h3>Approaches that name them</h3><p class="fine-print">Named within an approach or work-based strand of an entry. A later work here does not re-date the roster record above.</p><div class="person-contexts">${hits.map(({n, strand}) => `<section class="person-affiliation tone-${layerIndex(n.layer)}">${layerTag(n)}<h3><a href="${esc(nodeHref(n.id))}">${esc(n.label)} →</a></h3><p class="strand-title">${esc(strand.title)}${strand.intervention_year ? ` <span class="strand-year">${esc(strand.intervention_year)}</span>` : ''}${reviewBadge(strand.review_status)}</p>
    ${strand.works ? `<p class="person-work">${esc(strand.works)}</p>` : ''}${strand.claim_ids?.length ? `<details class="strand-claims"><summary>Exact claims · ${strand.claim_ids.length}</summary>${claimCards(strand.claim_ids)}</details>` : ''}</section>`).join('')}</div>`;
}

/* ---------------- The field: every entry on one time axis ---------------- */
let fieldIndex, fieldNodeById, fieldCatalogue, journalSourceById, atlasEdgeIds;
let hoverId = null, fieldWidth = 0, scrolledFocus = '';

const FIELD_TITLES = {...LAYER_TITLES, [JOURNAL_LAYER]: 'Journals & venues'};
const fieldTitle = id => FIELD_TITLES[id]
  || String(id).replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
const hiddenKinds = () => new Set(state.hide ? state.hide.split(',') : []);
/* Holding an entry the family view does not draw leaves the family for the full field. */
const outsideFamily = id => { const ids = shownIds(); return Boolean(ids) && !ids.has(id); };
const focusHref = id => href({focus: id, node: '', person: '', edge: '', page: 0, section: '',
  ...(state.family && state.family !== 'all' && (!activeFamily() || outsideFamily(id)) ? {family: ''} : {})});
/* Releasing a held entry keeps any pathway overlay and search; it only lets go of the hold. */
const releaseHref = () => href({focus: '', node: '', person: '', edge: '', page: 0, section: ''});
const releaseLink = () => `<a class="release" href="${esc(releaseHref())}">← Show everything</a>`;
const activePathway = () => state.path ? pathways.pathways.find(p => p.id === state.path) : null;
/* One editorial family's fields ('all' or an unknown slug shows everything). */
let shownMemo = {};
function familyShown(f) {
  if (shownMemo.id !== f.id || shownMemo.base !== graph) {
    const g = familyGraph(graph, f), nodes = fieldNodes(g);
    shownMemo = {id: f.id, base: graph, g, nodes, ids: new Set(nodes.map(n => n.id))};
  }
  return shownMemo;
}
/* A pathway overlay, or a held entry the family does not draw, falls back to the full field. */
function activeFamily() {
  if (!state.family || state.family === 'all' || state.path) return null;
  const f = familyBySlug(evidence?.families, state.family);
  if (!f || (state.focus && !familyShown(f).ids.has(state.focus))) return null;
  return f;
}
function shownGraph() { const f = activeFamily(); return f ? familyShown(f).g : graph; }
/* The ids the family view draws, or null when the full field is shown. */
function shownIds() { const f = activeFamily(); return f ? familyShown(f).ids : null; }
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
  return buildFieldLayout(shownGraph(), width, fieldFocusSet(), fieldLayers(shownGraph(), FIELD_TITLES),
    {numbering: state.focus ? null : pathNumbering(), extension: activeExtension()});
}

function fieldLegend() {
  const kinds = fieldKinds(shownGraph());
  const hidden = hiddenKinds();
  const counts = new Map();
  for (const e of fieldEdges(shownGraph()))
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
      <span class="swatch lead">earlier roots, undated</span>
      <span class="swatch posthumous">† death · hatched = posthumous reception</span>
      <span class="swatch point">a single dated year</span>
      <span class="swatch fuzzy">decade precision</span>
      <span class="swatch open">continues past the coverage limit</span>
      <span class="swatch axis-note">pre-1900 compressed</span>${activeExtension() ? '<span class="swatch intervention">◆ selected intervention after the limit</span>' : ''}</div>
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
  const ids = shownIds();
  return edges.filter(e => !hidden.has(e.relationship_kind) && (!ids || (ids.has(e.source) && ids.has(e.target))));
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
  /* The extension zone: only the axis is stretched; marks keep their own coverage, and the
     selected later interventions are drawn as points. The cutoff is a research date, not an end. */
  const ext = view.extension;
  if (ext) {
    const ex = view.scale(ext.end);
    /* The zone is narrow: footnotes are clipped to it and the axis notes hang from the right edge. */
    const fitTo = px => s => { const room = Math.max(4, Math.floor((ex - wx - 10) / px));
      return s.length > room ? s.slice(0, room - 1) + '…' : s; };
    const fit = fitTo(6), fitSmall = fitTo(5);   /* bold 9.5px footnote vs 9px axis note */
    grid += `<rect class="ext-zone" x="${wx}" y="${view.axisTop + 16}" width="${Math.max(0, ex - wx)}" height="${bottom - view.axisTop - 16}"/>
      <text class="ext-label" x="${wx + 6}" y="${bottom - (ext.latest ? 42 : 30)}">${
        [`after ${view.coverageYear}`, ext.status.replace(/_/g, ' '),
         `${ext.covered} of ${graph.nodes.filter(n => n.entry_kind === 'group').length} entries`]
          .map((s, i) => `<tspan x="${wx + 6}" dy="${i ? 12 : 0}">${esc(fit(s))}</tspan>`).join('')}${
        ext.latest ? `<tspan class="latest-label" x="${wx + 6}" dy="12">${esc(fit(`latest selected ${ext.latest}`))}</tspan>` : ''}</text>`;
    if (ext.cutoff && ext.cutoff <= ext.end) grid += `<line class="cutoff" x1="${view.scale(ext.cutoff)}" y1="${view.axisTop + 16}" x2="${view.scale(ext.cutoff)}" y2="${bottom}"/>
      <text class="cutoff-label" x="${view.scale(ext.cutoff) - 4}" y="${view.axisTop + 13}" text-anchor="end">${esc(fitSmall(`research cutoff ${graph.scope.extension.research_cutoff}`))}</text>`;
  }

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
      ${p.lead ? `<rect class="bar-lead" x="${p.lead.x}" y="${p.y + 5}" width="${p.lead.w}" height="${p.h - 10}" rx="2"/>
        <rect class="bar-lead-fade" x="${p.lead.x}" y="${p.y + 4}" width="${p.lead.w}" height="${p.h - 8}"/>` : ''}
      <rect class="bar-shape${p.point ? ' point' : ''}${p.node.entry_kind === 'person' ? ' person' : ''}${
        p.node.entry_kind === 'periodical' ? ' periodical' : ''}"
        x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"
        ${fuzzy && !p.point ? 'fill-opacity="0.62"' : ''} rx="3"/>
      ${p.lead ? '' : `<line class="bar-cap start" x1="${p.x}" y1="${p.y}" x2="${p.x}" y2="${p.y + p.h}"/>`}
      ${p.span.endKind === 'terminus'
        ? `<line class="bar-cap end" x1="${xEnd}" y1="${p.y}" x2="${xEnd}" y2="${p.y + p.h}"/>` : ''}
      ${p.open && p.w > 30 ? `<rect class="bar-fade" x="${xEnd - 22}" y="${p.y - 1}" width="23" height="${p.h + 2}"/>` : ''}
      ${p.ticks.map(t => `<line class="ms" x1="${t.x}" y1="${p.y + 3}" x2="${t.x}" y2="${p.y + p.h - 3}"
        ><title>${t.yr} · a year named in this entry’s date label</title></line>`).join('')}
      ${p.posthumous ? `<rect class="posthumous" x="${p.posthumous.x}" y="${p.y}" width="${p.posthumous.w}" height="${p.h}" rx="3"
        ><title>After ${p.death.yr}: posthumous reception</title></rect>` : ''}
      ${p.death ? `<g class="death-mark"><line x1="${p.death.x}" y1="${p.y - 4}" x2="${p.death.x}" y2="${p.y + p.h + 4}"/>
        <text x="${p.death.x}" y="${p.y - 5}" text-anchor="middle">†</text>
        <title>Died ${p.death.yr} (Wikidata)</title></g>` : ''}
      <text class="bar-label ${p.side}" y="${p.y + p.h / 2 + 1}"
        x="${p.side === 'right' ? xEnd + 7 : p.side === 'left' ? p.x - 7 : p.x + 9}"
        ${p.side === 'left' ? 'text-anchor="end"' : ''}>${esc(p.label)}</text>
    ${(p.interventions || []).map(iv => `<path class="intervention" d="M${iv.x} ${p.y + 2} l6 ${p.h / 2 - 2} l-6 ${p.h / 2 - 2} l-6 ${-(p.h / 2 - 2)} z"><title>${esc(p.node.label)} · selected intervention ${iv.yr}</title></path>`).join('')}
    </a>`;
  }).join('');

  /* role=group, not img: the marks inside are links and must stay reachable. */
  return `<svg class="field ${emphasised ? 'focused' : ''}"
      width="${view.inner}" height="${view.height}" viewBox="0 0 ${view.inner} ${view.height}"
      role="group" aria-label="Historiography on a time axis. Each mark is a link; a text list of the same entries is available under View · List.">
    <defs><linearGradient id="fade-right" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#fbfaf4" stop-opacity="0"/>
      <stop offset="1" stop-color="#fbfaf4" stop-opacity=".92"/></linearGradient>
    <pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#fbfaf4" stroke-width="2.2"/></pattern>
    <linearGradient id="fade-left" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#fbfaf4" stop-opacity=".95"/>
      <stop offset=".55" stop-color="#fbfaf4" stop-opacity=".35"/>
      <stop offset="1" stop-color="#fbfaf4" stop-opacity="0"/></linearGradient></defs>
    <g class="chrome">${washes}${grid}
      <line class="axis-line" x1="${view.x0}" y1="${view.axisTop + 22}" x2="${view.x1}"
        y2="${view.axisTop + 22}"/>${bands}${captions}</g>
    <g class="ghosts">${ghosts}</g><g class="edges">${edges}</g>${chips}${bars}
  </svg>`;
}

function interventionNote(n) {
  const years = activeExtension() ? interventionsOf(n) : [];
  if (!years.length) return '';
  const c = n.extension_coverage;
  return `<p class="ext-note"><strong>After ${esc(c.baseline_through || 2000)}.</strong> ${years.length} selected intervention${years.length === 1 ? '' : 's'} (${esc(years.join(', '))}), drawn as ◆ on this row. ${c.status === 'release_candidate' ? 'Release candidate, not yet accepted. ' : ''}${c.field_review_complete ? '' : 'The field is not reviewed through the cutoff.'} Open the entry to read the exact claims and their evidence.</p>`;
}
function fieldDateNote(n, span) {
  if (!span) return `<strong>No span stated.</strong> <code>${esc(n.date_label)}</code> names
    people or methods rather than years, so it sits in the band’s strip rather than being given a
    date it does not claim.`;
  const wall = span.coverage ?? graph.scope.main_period[1];
  const periodical = n.entry_kind === 'periodical';
  const precision = span.precision === 'decade' ? ' (decade precision)' : '';
  let opening, ending;
  const roots = span.openStart ? `<strong>Earlier roots, undated.</strong> The label’s first dated
    year is ${span.start}; that dates a contribution to an already established
    ${periodical ? 'periodical' : 'field'}, not its origin, so the mark runs in from the left edge
    without a starting cap. ` : '';
  if (span.endKind === 'coverage_limit') {
    opening = periodical
      ? `<strong>First issue ${span.start}</strong>, drawn to ${wall}.`
      : span.openStart ? `Drawn solid from ${span.start} to ${wall}.`
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
  return `${roots}${opening} ${ending}${tickNote}<br><span class="prov">${prov}</span>`;
}

/* Life dates from Wikidata, when the published people record carries them. */
function lifeLine(n, span) {
  const life = lifeIndex(graph).get(n.id);
  if (!life || (!life.birth && !life.death)) return '';
  const approx = k => ['year', 'decade', 'century'].includes(life[`${k}Precision`]) ? 'c. ' : '';
  const parts = [];
  if (life.birth) parts.push(`Born ${approx('birth')}${life.birth}`);
  parts.push(life.death ? `died ${approx('death')}${life.death}` : 'living at retrieval');
  const posthumous = life.death && span && life.death < (span.endKind === 'coverage_limit'
    ? (span.coverage ?? graph.scope.main_period[1]) : span.end);
  return `<p class="life">${esc(parts.join(' · '))}${life.qid ? ` · <a href="https://www.wikidata.org/wiki/${esc(life.qid)}"
      target="_blank" rel="noopener noreferrer">Wikidata ${esc(life.qid)}</a>` : ''}${
      life.retrieved ? ` <span class="prov">retrieved ${esc(life.retrieved)}</span>` : ''}${
      posthumous ? `<br><span class="posthumous-note">The hatched part of the mark, after ${life.death},
      is reception of the work after the author’s death.</span>` : ''}</p>`;
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
  const outside = outsideFamily(r.other);
  return `<details class="rel ${tone}" data-edge="${esc(e.id)}"><summary>
      <span class="dir">${esc(dirWord(kind, r.dir))}</span>
      <span class="who">${esc(other.label)}${outside ? ' <span class="outside-tag">outside this family</span>' : ''}</span>
      <span class="what">${esc(e.relationship)}</span></summary>
    <div class="rel-body">
      ${e.evidence_note ? `<p class="evidence"><strong>Evidence.</strong> ${esc(e.evidence_note)}</p>`
        : '<p class="evidence fine-print">No evidence note is recorded for this relationship.</p>'}${scope}
      <details class="rel-sources"><summary>References · ${e.source_ids?.length || 0}</summary>${sources}</details>
      <p class="rel-links"><a href="${esc(focusHref(r.other))}">Hold ${esc(other.label)}${outside ? ' in the full field' : ''} →</a>${
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
    <p>A mark runs across <strong>the years an entry’s date label names</strong>. A left cap is
    the earliest dated year; a thin lead-in from the left edge means the label states earlier,
    undated roots. A bar that fades into the dashed wall at ${graph.scope.main_period[1]} continues beyond what this atlas
    covers: the wall is a limit of the map, not an ending. Ticks mark other years the label names.
    Open a relationship to read its evidence.</p>${activeExtension() ? `<p>Beyond the wall, ◆ marks <strong>selected interventions after ${graph.scope.main_period[1]}</strong> for the ${activeExtension().covered} entries a partial release covers. Nothing else is extended; the research cutoff is a date of reading, not an ending.</p>` : ''}
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
    ${lifeLine(n, span)}
    <div class="datewhy">${fieldDateNote(n, span)}${interventionNote(n)}</div>
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
  const rows = fieldNodes(shownGraph()).map(n => ({n, span: spanOf(n)}))
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
    return `<span class="mini" aria-hidden="true">${span.openStart ? `<i class="lead" style="left:0;width:${a}%"></i>` : ''}<i class="${open ? 'open' : ''}" style="left:${a}%;width:${b - a}%"></i></span>`;
  };
  const fam = activeFamily();
  return `<p class="fine-print">All ${rows.length} entries, in time order within each band.
      Dates describe arrival and influence, not a lifespan.${fam
        ? ' Relationship counts include relationships with entries outside this family.' : ''}</p>` +
    fieldLayers(shownGraph(), FIELD_TITLES).map(layerId => {
      const mine = rows.filter(r => r.n.layer === layerId);
      if (!mine.length) return '';
      /* Narrow screens open one band at a time; the summary carries the count. */
      return `<details class="band-list" ${matchMedia('(max-width: 700px)').matches ? '' : 'open'}><summary>${esc(fieldTitle(layerId))}<span>${mine.length}</span></summary>
      <table class="field-table"><caption>${esc(fieldTitle(layerId))}</caption>
      <thead><tr><th scope="col">Dates</th><th scope="col">Entry</th><th scope="col">Kind</th>
        <th scope="col">${fam ? 'All relationships' : 'Relationships'}</th></tr></thead><tbody>${mine.map(({n, span}) => {
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

/* ---------------- Landing: families, the atlas beside the record ---------------- */
let landingWidth = 0;
const AXIS_LABEL = '1880–2024';
const recordView = () => state.record || 'all';
/* Landing links clear the mobile list default (view) so the family page applies its own default. */
const familyHref = id => href({family: id, view: ''});
function stripBar(segments, cls, unclaimed = null) {
  const seg = (s, extra = '') => `<span class="seg${extra}" style="flex-basis:${(s.share * 100).toFixed(2)}%" title="${esc(`${s.label}: ${Math.round(s.share * 100)}%`)}">${s.share >= 0.07 ? esc(`${s.short} ${Math.round(s.share * 100)}%`) : ''}</span>`;
  const rest = unclaimed === null ? '' : seg({label: 'Items no family claims, mostly in general, regional and period journals', short: 'general, regional & period', share: unclaimed}, ' unclaimed');
  return `<div class="strip-bar ${cls}" role="img" aria-label="${esc(segments.map(s => `${s.label} ${Math.round(s.share * 100)}%`).join(', ') + (unclaimed === null ? '' : `, unclaimed ${Math.round(unclaimed * 100)}%`))}">${segments.map(s => seg(s)).join('')}${rest}</div>`;
}
function landingPage() {
  const block = evidence.families, view = recordView(), strip = stripSegments(block, graph);
  const toggles = Object.entries(VIEWS).map(([k, label]) =>
    `<a class="view-link" role="button" href="${esc(href({...OVERVIEW_PATCH, record: k === 'all' ? '' : k}))}" aria-pressed="${k === view}">${esc(label)}</a>`).join('');
  const viewNote = view === 'established'
    ? `Only the ${block.established_journals} journals publishing research in both 1970–74 and 2015–19. Old journals are slow to take up new fields.`
    : view === 'reviews' ? 'Share of all book reviews in H-Net and Reviews in History in each five-year period.'
    : 'Share of all research articles in each five-year period, across every journal in the collection.';
  return `<div class="landing-page">
    <div class="section-heading"><div><p class="eyebrow">01 / THE ATLAS AND THE RECORD · ${AXIS_LABEL}</p>
      <h2>Eleven families of historical writing</h2></div></div>
    <p class="lede"><b class="atlas">Orange</b>: where this atlas dates its schools and fields. <b class="record">Green</b>: each family’s share of what historians published. ◂ marks entries dated before 1880. Choose a family to see its fields.</p>
    <p class="eyebrow">THE GAP IN ONE LINE</p>
    <div class="strip"><span>Share of atlas entries</span>${stripBar(strip.atlas, 'atlas')}
      <span>Share of research, ${strip.period[0]}–${strip.period[1]}</span>${stripBar(strip.record, 'record', strip.unclaimed)}</div>
    <div class="landing-controls"><p class="eyebrow">OVER TIME</p><div class="view-links" role="group" aria-label="Record view">${toggles}</div></div>
    <p class="fine-print">${esc(viewNote)} ${esc(block.note)}</p>
    <div class="landing-rows" aria-busy="true"></div>
    ${cardsHtml({block, graph, view, href: familyHref})}
    <details class="landing-table"><summary>Table of these numbers</summary>${tableHtml({block, graph, view})}</details>
    <p class="fine-print">Atlas entries are placed at the first year in their date label, an editorial reading rather than verified chronology. Record counts use journal-level tags, and research articles are records of at least ten pages. The atlas’s own coverage ends in 2000; record bars after it have no matching atlas entries. ${esc(evidence.caveats.join(' '))}
      <a href="${esc(href({family: 'all', view: ''}))}">All entries on one axis →</a></p>
  </div>`;
}
function drawLanding() {
  const box = document.querySelector('.landing-rows');
  if (!box) return;
  landingWidth = box.clientWidth || 1000;
  /* Rows are native SVG links (Enter, middle-click and no-JS all work), so no handlers here. */
  box.innerHTML = rowsSvg({block: evidence.families, graph, view: recordView(), width: landingWidth, href: familyHref});
  box.removeAttribute('aria-busy');
}

/* Crumbs, then a note pairing each shared or bridged entry with its other families. */
function familyHeading(f) {
  const all = evidence.families.families;
  const label = id => nodeById.get(id)?.label;
  const primaryOf = id => all.find(x => x.members.some(m => m.id === id && m.primary))?.label;
  /* Bridges, grouped by the family that claims them: "A, B (from F); C (from G)". */
  const byHome = new Map();
  for (const m of f.members.filter(m => !m.primary && label(m.id))) {
    const home = primaryOf(m.id) || 'no primary family';
    byHome.set(home, [...(byHome.get(home) || []), label(m.id)]);
  }
  const bridged = [...byHome].map(([home, names]) => `${names.join(', ')} (from ${home})`);
  const shared = f.members.filter(m => m.primary && label(m.id)).map(m => {
    const others = all.filter(x => x.id !== f.id && x.members.some(y => y.id === m.id)).map(x => x.label);
    return others.length ? `${label(m.id)} (also in ${others.join(', ')})` : '';
  }).filter(Boolean);
  const lacks = f.record_only.map(x => x.label);
  const note = [shared.length ? `Shared with other families: ${shared.join('; ')}.` : '',
    bridged.length ? `Also drawn here: ${bridged.join('; ')}.` : '',
    lacks.length ? `In the record but not in the atlas: ${lacks.join(', ')}.` : ''].filter(Boolean).join(' ');
  return `<nav class="family-crumbs" aria-label="Families"><a href="${esc(href(OVERVIEW_PATCH))}">← All families</a>
      <a href="${esc(href({family: 'all', focus: '', path: ''}))}">All entries on one axis</a></nav>
    ${note ? `<p class="family-note">${esc(note)}</p>` : ''}`;
}

function fieldPage() {
  const fam = activeFamily();
  const counts = fieldView(1200);   /* counts do not depend on width; the SVG is drawn after measuring */
  const body = state.view === 'list' ? `<div class="field-listing">${fieldList()}</div>`
    : '<div class="field-scroll" aria-busy="true"></div>';
  return `<div class="field-page">
    ${fam ? familyHeading(fam) : ''}
    <div class="section-heading"><div><p class="eyebrow">${fam ? '01 / ONE FAMILY OF HISTORICAL WRITING' : '01 / THE WHOLE FIELD'}</p>
      <h2>${fam ? esc(fam.label) : 'Historiography on one time axis'}</h2></div>
      <p class="field-summary">${counts.datedCount} placed in time${counts.undatedCount
        ? ` · ${counts.undatedCount} without a stated span` : ''} ·
        ${fieldEdges(shownGraph()).length} relationships${activeExtension() ? ` · ${activeExtension().covered} entries with selected interventions after ${graph.scope.main_period[1]}` : ''}</p></div>
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
    const company = document.querySelector('.company-chart');
    if (company && Math.abs(company.clientWidth - companyWidth) > 4) drawCompany();
    const rows = document.querySelector('.landing-rows');
    if (rows && Math.abs(rows.clientWidth - landingWidth) > 4) drawLanding();
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
    ${n.entry_type ? `<p class="entry-type">${esc(n.entry_type)}</p>` : ''}<p class="description">${esc(n.description)}</p>${n.scope_note ? `<h3>Scope & distinctions</h3><p>${esc(n.scope_note)}</p>` : ''}${recordPanel(n)}<h3>Representative figures & works</h3><p>${esc(n.representative_figures_and_works || 'Not recorded.')}</p>
    ${n.representative_people?.length ? '' : extensionSection(n)}${n.entry_kind === 'person' && n.claim_ids?.length ? `<details class="entry-claims"><summary>Exact claims behind this entry · ${n.claim_ids.length}</summary><p class="fine-print">Catalogue claims with their own review status and evidence scope; authorship credits are metadata, not influence.</p>${claimCards(n.claim_ids)}</details>` : ''}
    <details class="bibliography" open><summary>References <span>${n.source_ids?.length || 0}</span></summary><p class="fine-print">References offer context; a metadata check does not certify every interpretation.</p>${sourceList(n.source_ids)}</details>
    ${memberPaths.length ? `<h3>Read in a pathway</h3><ul class="related-pathways">${memberPaths.map(p => `<li><a href="#pathway=${p.id}">${esc(p.title)} →</a></li>`).join('')}</ul>` : ''}`;
}
/* A small bar chart of counts per five-year bin: one series, so the heading names it and no
   legend is needed; values are in the accessible label and each bar's tooltip. */
const RECORD_END = 2026;  // collections run to September 2026, so the last bin is partial
function recordBars(bins, first, last, noun) {
  const years = [];
  for (let y = first; y <= last; y += 5) years.push(y);
  const span = y => y + 4 > RECORD_END ? `${y}–${RECORD_END} (partial)` : `${y}–${y + 4}`;
  const values = years.map(y => bins[y] || 0);
  const max = Math.max(1, ...values);
  const w = 300, h = 54, gap = 2, bw = (w - gap * (years.length - 1)) / years.length;
  const bars = years.map((y, i) => {
    const bh = values[i] ? Math.max(2, Math.round(values[i] / max * (h - 6))) : 0;
    return `<rect x="${(i * (bw + gap)).toFixed(1)}" y="${h - bh}" width="${bw.toFixed(1)}" height="${bh}" rx="1.5"><title>${span(y)}: ${values[i].toLocaleString()} ${noun}</title></rect>`;
  }).join('');
  const label = years.filter((y, i) => values[i]).map(y => `${span(y)}: ${bins[y]}`).join('; ');
  return `<svg class="record-bars" viewBox="0 0 ${w} ${h + 14}" role="img" aria-label="${esc(noun)} per five years. ${esc(label || 'none')}">${bars}<line x1="0" x2="${w}" y1="${h + .5}" y2="${h + .5}"/><text x="0" y="${h + 12}">${first}</text><text x="${w}" y="${h + 12}" text-anchor="end">${Math.min(last + 4, RECORD_END)}</text></svg>`;
}
function recordPanel(n) {
  const e = evidence?.entries?.[n.id];
  if (!e) return '';
  const fmt = v => Number(v || 0).toLocaleString();
  const entryLink = x => nodeById.has(x.id) ? linkNode(x.id) : esc(x.label);
  const parts = [];
  if (e.status === 'direct') {
    parts.push(e.reviews_total ? `<p><strong>${fmt(e.reviews_total)}</strong> reviews in networks and headings mapped to this field</p>${recordBars(e.reviews_by_5yr, 1990, 2025, 'reviews')}` : '<p>No reviews in networks or headings mapped to this field.</p>');
    parts.push(e.journal_items_total ? `<p><strong>${fmt(e.journal_items_total)}</strong> research articles in journals tagged with this field</p>${recordBars(e.journal_items_by_5yr, 1950, 2025, 'research articles')}` : '<p>No journals in the collection are tagged with this field.</p>');
  } else if (e.status === 'cross_field_method_with_roots') {
    parts.push(`<p>A method used across fields, with roots in ${e.roots_in.map(entryLink).join(' and ')}.</p>`);
  } else {
    parts.push(`<p>No direct signal: networks, subject headings and journals do not name this ${n.entry_type ? 'entry' : 'approach'}. In the record it is practised within ${e.practised_within.map(entryLink).join(', ')}.</p>`);
  }
  if (e.method) {
    const m = e.method;
    const where = m.practitioner_items_in_method_venues
      ? `, ${Math.round(m.share_elsewhere * 100)}% of whose research appears outside method journals`
      : '; no journals devoted to the method are in the collection';
    parts.push(`<p>Articles naming the method in their title: <strong>${fmt(m.title_hits)}</strong>${m.abstract_hits_not_in_title ? `; abstracts name it in ${fmt(m.abstract_hits_not_in_title)} more` : ''} (lower bounds). ${fmt(m.practitioners)} practitioners${where}.</p>`);
  }
  if (e.invoked_in_reviews) {
    const most = (e.invoked_most_in || []).map(x => `${entryLink(x)} (×${x.lift})`).join(', ');
    parts.push(`<p>Invoked by name in <strong>${fmt(e.invoked_in_reviews)}</strong> reviews${most ? `; most over-represented in ${most}` : ''}.</p>`);
  }
  return `<details class="record-panel" open><summary>What the record shows <span>evidence layer</span></summary>${parts.join('')}
    <details class="record-about"><summary>About these counts</summary><p class="fine-print">${esc(evidence.coverage.reviews)}; ${esc(evidence.coverage.journals)}. ${evidence.caveats.map(esc).join(' ')}</p></details></details>`;
}
function edgeDetail(e) {
  const kind = edgeKind(e);
  return `<div class="reading-header"><p class="eyebrow">THE RELATIONSHIP · ${esc(e.id)}</p><h2 id="detail-title" tabindex="-1">${esc(KINDS[kind])}</h2><a class="text-link" href="${esc(href({edge: ''}))}">← Back to entry</a></div>
    <div class="edge-endpoints">${linkNode(e.source)}<span>${hasArrow(e) ? '↓ toward' : kind === 'comparison' ? '↕ compared with · no direction' : '↕ direction unclassified'} </span>${linkNode(e.target)}</div>
    <h3>Interpretation</h3><p class="description">${esc(e.relationship)}</p>
    ${kind === 'unclassified' ? `<p class="context-note">Direction metadata is not recorded. This is not classified as influence. Legacy category: ${esc(e.type)}.</p>` : kind === 'contribution' ? '<p class="context-note">A contribution does not imply founding a field.</p>' : kind === 'critique' ? '<p class="context-note">The arrow runs from the critic toward the position criticized.</p>' : ''}
    <h3>Evidence & qualifications</h3>${e.review_status ? `<p>${reviewBadge(e.review_status)}${/provisional/i.test(e.relationship) ? ' <span class="fine-print">Labelled provisional by the editors.</span>' : ''}</p>` : ''}<p>${esc(e.evidence_note || 'No relationship-specific evidence note recorded.')}</p>
    ${e.claim_ids?.length ? `<h3>Underlying claim${e.claim_ids.length === 1 ? '' : 's'}</h3>${e.claim_projection ? `<p class="fine-print"><strong>Exact endpoints.</strong> ${entityLink(e.claim_projection.subject)} → ${entityLink(e.claim_projection.object)}.${e.claim_projection.note ? ` ${esc(e.claim_projection.note)}` : ''}</p>` : ''}${e.target_strand ? (() => { const [nid, sid] = e.target_strand.split('/'); const strand = nodeById.get(nid)?.strands?.find(x => x.id === sid); return `<p class="fine-print"><strong>Target is a strand.</strong> “${esc(strand?.title || sid)}” within ${linkNode(nid)}, not the whole entry.</p>`; })() : ''}${claimCards(e.claim_ids)}` : ''}
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
    <h3>Periods are approximate groupings</h3><p>Coverage is 1920–2000 with earlier roots. ${production.scope?.extension ? `A partial extension after 2000 exists as a ${esc((production.scope.extension.status || '').replace(/_/g, ' '))}: selected interventions in ${production.scope.extension.field_ids?.length || 0} entries, research cutoff ${esc(production.scope.extension.research_cutoff || '')}, latest selected publication ${esc(production.scope.extension.latest_selected_publication || '')}. It is not a survey of any field after 2000; the exact 2000 view remains available.` : 'An extension beyond 2000 has not yet been written.'} Periods describe emergence or expansion, not termination, and prose date labels can refer to publication or reception. Entries without assigned periods remain available when you filter by a period. There is no continuous timeline.</p>
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
function rangeControls() {
  const ext = production.scope?.extension;
  const toggle = $('range-toggle');
  const eyebrow = $('scope-eyebrow');
  if (!ext) { toggle.hidden = true; eyebrow.textContent = `${production.scope.main_period[0]}–${production.scope.main_period[1]} · WITH EARLIER ROOTS`; return; }
  const [a, b] = production.scope.main_period, end = ext.proposed_view_period?.[1];
  const status = /accepted/.test(ext.status || '') ? 'partial release' : (ext.status || '').replace(/_/g, ' ');
  const partial = `${a}–${b} · earlier roots · selected interventions to ${ext.latest_selected_publication || end} · ${status}`;
  eyebrow.textContent = (state.range === '2000' ? `${a}–${b} · WITH EARLIER ROOTS · EXACT ${b} VIEW` : partial).toUpperCase();
  $('edition-label').textContent = state.range === '2000' && ext.baseline_revision
    ? `Draft ${ext.baseline_revision} · ${b} view` : `Draft ${production.revision_history.at(-1).version}`;
  if (!ext.baseline_asset) { toggle.hidden = true; return; }
  toggle.hidden = false;
  toggle.innerHTML = `<span>Coverage</span><a href="${esc(href({range: '2000'}))}" aria-pressed="${state.range === '2000'}">Through ${b}</a><a href="${esc(href({range: ''}))}" aria-pressed="${state.range !== '2000'}">Through ${end} · partial</a>`;
}
function render() {
  rangeControls();
  const onField = state.tab === 'map' && !state.node && !state.person;
  /* Without the evidence asset the front door falls back to the full field view. */
  const onLanding = onField && state.overview && Boolean(evidence?.families);
  $('toolbar').hidden = !['map','people','browse'].includes(state.tab) || Boolean(state.node || state.person) || onLanding;
  $('search').value = state.query;
  $('layer-filter').value = state.layer;
  $('period-filter').value = state.period;
  $('hunt-filter').checked = state.hunt;
  document.querySelectorAll('[data-tab]').forEach(a => {
    const tab = state.person ? 'people' : state.pathway ? 'pathways' : state.node ? 'browse'
      : state.tab === 'map' ? 'field' : state.tab;
    if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.body.dataset.view = onField ? 'field' : '';
  document.body.dataset.compact = onField ? '' : '1';
  $('workspace').innerHTML = state.person ? personPage()
    : state.node ? (nodeById.get(state.node).representative_people?.length && state.section !== 'connections' ? schoolPeople() : focused())
    : onLanding ? landingPage() : onField ? fieldPage()
    : state.tab === 'people' ? peopleDirectory()
    : state.tab === 'about' ? about()
    : state.tab === 'pathways' ? pathwayPage()
    : state.layer || state.query || state.period || state.hunt ? directory() : overview();
  if (onLanding) drawLanding(); else if (onField) wireField();
  if (state.tab === 'people' && !state.person && !state.node) { companyHover = null; drawCompany(); }
  document.title = `${state.person ? personById.get(state.person).label : state.node ? nodeById.get(state.node).label : state.pathway ? pathways.pathways.find(p => p.id === state.pathway).title : 'Historiography'} · A seminar atlas`;
  $('announcement').textContent = onLanding ? `Eleven families of historical writing: the atlas beside the record. Record view: ${VIEWS[recordView()]}.`
    : state.tab === 'map' && !state.node && !state.person
    ? (state.focus ? `${fieldNodeById.get(state.focus).label} held in the field view.`
       : state.path ? `Pathway ${pathways.pathways.find(p => p.id === state.path).title} shown on the field.`
       : activeFamily() ? `${activeFamily().label}. ${shownIds().size} entries on a time axis.`
       : `Field view. ${fieldNodes(graph).length} entries on a time axis.`)
    : state.person ? personById.get(state.person).label : state.node ? `${nodeById.get(state.node).label}. ${state.section === 'connections' ? 'Connections view.' : rosterLabel(nodeById.get(state.node))}` : state.tab === 'people' ? `${filterPeople(graph,state).length} matching people.` : state.tab === 'map' ? `${filterNodes(graph.nodes,state,graph.people).length} matching entries.` : state.pathway ? pathways.pathways.find(p=>p.id===state.pathway).title : state.tab === 'pathways' ? 'Seminar pathways.' : 'Reading this map.';
  const resetLanes = {page:0};
  $('kind-filter')?.addEventListener('change', e => change({kind: e.target.value, ...resetLanes}));
  $('neighbor-layer')?.addEventListener('change', e => change({neighborLayer: e.target.value, ...resetLanes}));
}
async function start() {
  try {
    const evidenceLoad = fetch('data/evidence.json', {signal: AbortSignal.timeout(8000)}).then(r => r.ok ? r.json() : null).catch(() => null);
    [production, pathways] = await Promise.all(['data/graph.json', 'data/pathways.json'].map(async url => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${url} (${response.status})`);
      return response.json();
    }));
    adopt(production);
    window.addEventListener('resize', onResize);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && state.focus && document.querySelector('svg.field')
          && !e.target.closest('input, select, textarea')) change({focus: ''});
    });
    $('edition-label').textContent = `Draft ${revision()}`;
    $('layer-filter').insertAdjacentHTML('beforeend', layerOptions(''));
    $('period-filter').insertAdjacentHTML('beforeend', graph.periods.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('') + '<option value="unassigned">No assigned period</option>');
    /* Parse once to learn which graph the route wants, adopt it, then parse against that graph. */
    const routeFor = async () => {
      const wanted = readRoute(location.hash, production, pathways).range;
      await ensureRange(wanted);
      const next = readRoute(location.hash, graph, pathways);
      if (matchMedia('(max-width: 700px)').matches && !new URLSearchParams(location.hash.slice(1)).has('view')) next.view = 'list';
      return next;
    };
    evidence = await evidenceLoad;
    state = await routeFor();
    render();
    window.addEventListener('hashchange', async () => {
      const focusedId = document.activeElement?.id;
      const old = state;
      state = await routeFor();
      render();
      if (state.edge && state.edge !== old.edge) $('detail-title')?.focus({preventScroll: !matchMedia('(max-width: 1000px)').matches});
      else if (focusedId && $(focusedId) && !$(focusedId).closest('[hidden]')) $(focusedId).focus({preventScroll: true});
      else {
        $('workspace').focus({preventScroll: true});
        if (state.node !== old.node || state.person !== old.person || state.section !== old.section || state.tab !== old.tab || state.pathway !== old.pathway || state.family !== old.family || state.overview !== old.overview) $('workspace').scrollIntoView({block: 'start'});
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
