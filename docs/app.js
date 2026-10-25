import {PAGE_SIZE, LAYER_TITLES, KINDS, PERSON_ROLES, edgeKind, hasArrow, filterNodes, filterPeople, personContexts, neighborhood, partitionNeighborhood, readRoute, routeHash, OVERVIEW_PATCH, isOverviewHash} from './core.mjs';
import {buildFieldLayout, fieldNodes, fieldEdges, fieldKinds, fieldLayers, relationIndex, milestoneYears, lifeIndex,
  focusSetFor, fieldMatches, journalNodes, spanOf, anchor, edgePath, kindLabel, kindChip, dirWord,
  pathwaySet, pathwayEdges, BASE_KINDS, JOURNAL_LAYER, extensionOf, interventionsOf, frameOf, reviewedThrough,
  personMapSubset, personMapLayout, ROLE_BADGE} from './field.mjs';
import {sortName, bySurname, companyLayout, bridges, familyIndex, familyOverviewLayout, familyCompanyLayout, ENTRY_LINE, FAMILY_LINE} from './people.mjs';
import {AXIS, MIN_BIN_TOTAL, VIEWS, stripSegments, familyBySlug, familyGraph, familyContent, rowsSvg, cardsHtml, tableHtml} from './landing.mjs';
import {recordPanel as publicationPanel} from './records.mjs';
import {chronologyOf, chronologyLabel, chronologyEvents, contributionSpan, dateText} from './chronology.mjs';
import {isReadingHash, mountReading, mountReadingContext, resizeReading} from './dissertations.mjs';

const $ = id => document.getElementById(id);
const phone = () => matchMedia('(max-width: 700px)').matches;
const phoneCircles = () => matchMedia('(max-width: 760px)').matches;
const canHover = () => matchMedia('(hover: hover)').matches;
const disclosureOpen = () => phone() ? '' : 'open';
function closeNavigation() {
  $('nav-more').setAttribute('aria-expanded', 'false');
  document.querySelector('.main-nav').classList.remove('expanded');
}
const chartReturn = (id, label) => `<button type="button" class="touch-only chart-return" data-scroll-target="${id}">${label} ↑</button>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
let graph, pathways, state, nodeById, sourceById, personById, personNames;
/* `pathwayAsset` is data/pathways.json as loaded; `pathways` is the same object restricted to the
   entries the shown graph has (the 2000 archive predates some pathway entries). It is rebuilt on
   every adopt and never written back, so switching views keeps the full lists. A pathway with no
   entry in the shown graph is omitted. */
let pathwayAsset;
function pathwaysFor(g) {
  const ids = new Set(g.nodes.map(n => n.id));
  return {...pathwayAsset, pathways: pathwayAsset.pathways
    .map(p => ({...p, node_ids: p.node_ids.filter(id => ids.has(id))})).filter(p => p.node_ids.length)};
}
/* `production` is the current graph; `baselineGraph` the archived 2000 graph, loaded on demand
   for the exact baseline view. `catalogue` indexes the claim catalogue of whichever is shown. */
let production, productionRequest, baselineGraph = null, catalogue = {entities: new Map(), claims: new Map(), records: new Map()};
async function loadProduction() {
  if (!production.overview_only) return;
  if (!productionRequest) productionRequest = fetch('data/graph.json', {signal: AbortSignal.timeout(30000)})
    .then(r => { if (!r.ok) throw new Error('Could not load the detailed entries'); return r.json(); })
    .catch(error => { productionRequest = null; throw error; });
  production = await productionRequest;
  if (graph.overview_only) adopt(production);
}
/* The evidence layer (data/evidence.json): aggregates from reviews and journal metadata, shown
   beside an entry's interpretation and never merged into it. Loaded with the graph; the landing needs it. */
let evidence = null;
let peopleRecords, peopleRecordsRequest;
const RECORD_PILOT = new Set(['paul_e_lovejoy', 'geoff_eley', 'serge_noiret', 'lorraine_daston', 'jay_winter', 'peter_galison', 'ida_altman', 'joel_mokyr']);
async function loadPeopleRecords() {
  if (!state?.person || !RECORD_PILOT.has(state.person)) return;
  if (!peopleRecordsRequest) peopleRecordsRequest = fetch('data/people-records.json', {signal: AbortSignal.timeout(8000)})
    .then(r => { if (!r.ok) throw new Error('Profile records unavailable'); return r.json(); })
    .then(asset => { peopleRecords = asset; })
    .catch(() => { peopleRecordsRequest = null; });
  await peopleRecordsRequest;
  const box = document.querySelector('[data-person-records]');
  if (!box || box.dataset.personRecords !== state.person) return;
  box.innerHTML = peopleRecords ? publicationPanel(peopleRecords, state.person)
    : '<p class="fine-print">Publication records could not be loaded. <button type="button" data-retry-records>Try again</button></p>';
}
const revision = () => graph.revision_history.at(-1).version;
const activeExtension = () => state?.range === '2000' ? null : extensionOf(graph);
/* The open frame (revision 1.133 on): no closing wall; each entry is reviewed through its own
   year. The archived 2000 graph, and any graph without scope.frame, keeps the legacy wall. */
const openFrame = (g = graph) => frameOf(g).open;
const explicitChronology = () => graph.chronology_policy?.version === '1';
/* The year an open-ended entry is drawn solid to, as buildFieldLayout draws it. */
function solidEnd(n, span) {
  const fr = frameOf(graph);
  if (!fr.open) return span.coverage ?? graph.scope.main_period[1];
  const reviewed = reviewedThrough(n);
  return reviewed === null ? fr.end : Math.max(reviewed, span.end);
}
const isOpenSpan = (n, span) => !span.chronological && (span.endKind === 'coverage_limit'
  || (openFrame() && reviewedThrough(n) !== null && span.endKind !== 'terminus'));
function adopt(g) {
  graph = g;
  pathways = pathwaysFor(g);
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
  const asset = production.scope?.archive?.baseline_asset ?? production.scope?.extension?.baseline_asset;
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
const connectedNodeHref = (id, view = state.view) => href({node: id, person: '', edge: '', section: 'connections', view, page: 0, kind: '', neighborLayer: ''});
const personHref = id => href({person: id, edge: '', section: '', page: 0, kind: '', neighborLayer: ''});
const linkNode = (id, className = '') => `<a class="${className}" href="${esc(nodeHref(id))}">${esc(nodeById.get(id).label)}</a>`;
const layerOptions = selected => graph.layers.map(l => `<option value="${l.id}" ${selected === l.id ? 'selected' : ''}>${esc(layerLabel(l.id))}</option>`).join('');
const crumbs = items => `<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="#">History in Conversation</a>${items.map(i => `<span aria-hidden="true">/</span>${i}`).join('')}</nav>`;
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
  if (openFrame()) {
    const through = reviewedThrough(n) ?? c.baseline_through ?? 2000;
    return `<section class="extension" aria-label="Selected later interventions"><div class="ext-head"><p class="eyebrow">AFTER ${esc(through)} · SELECTED LATER INTERVENTIONS</p><span class="badge status-${esc(c.status || 'release_candidate')}">${esc(statusText)}</span></div>
    <p class="context-note">${years.length} publication${years.length === 1 ? '' : 's'} selected (${esc(years.join(', '))}). Research cutoff ${esc(c.research_cutoff || 'unrecorded')}. ${c.field_review_complete ? 'This field has been reviewed through the cutoff.' : `This field is <strong>reviewed through ${esc(through)}</strong>: these are selected interventions after the review year, not a survey.`} ${chronologyOf(n) ? 'Each selected contribution is dated individually; the review year remains separate.' : `The entry’s mark, reviewed through ${esc(through)}, is unchanged.`}</p>
    ${(c.work_ids || []).map(workCard).join('')}</section>`;
  }
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
function strandCredits(branch) {
  const credits = branch.participant_credits || [];
  return `${credits.length ? `<p class="fine-print"><strong>Community knowledge contributors.</strong> ${credits.map(c => `${esc(c.name)} (${esc(c.role)}; ${esc(c.locator)})`).join(' · ')}</p>` : ''}${branch.citation_note ? `<p class="fine-print">${esc(branch.citation_note)}</p>` : ''}`;
}

function strandGuide(n) {
  if (!n.strands?.length) return '';
  return `<section class="strand-guide" aria-label="Approaches within this entry"><h3>Different approaches within this entry</h3><p class="fine-print">Overlapping approaches and debates, not a sequence of schools replacing one another.</p>${n.strands.map(branch => `<details class="strand${branch.intervention_year ? ' strand-extension' : ''}"><summary>${esc(branch.title)}${branch.intervention_year ? `<span class="strand-year">${esc(branch.intervention_year)}</span>` : ''}</summary>${branch.intervention_year ? `<p class="strand-meta">Selected intervention · ${esc(branch.intervention_year)} ${reviewBadge(branch.review_status)}<span class="fine-print"> A work's year is not the field's origin or a career boundary.</span></p>` : ''}<p>${esc(branch.focus)}</p><p class="strand-people">${branch.person_ids.map(id => `<a href="${esc(personHref(id))}">${esc(personById.get(id)?.label || id)}</a>`).join(' · ')}</p><p class="person-work">${esc(branch.works)}</p>${strandCredits(branch)}${branch.claim_ids?.length ? `<details class="strand-claims"><summary>Exact claims · ${branch.claim_ids.length}</summary>${claimCards(branch.claim_ids)}</details>` : ''}<details><summary>Reading references</summary><p class="fine-print">These readings have different scopes; see their source notes.</p>${sourceList(branch.source_ids)}</details></details>`).join('')}</section>`;
}
function corePeople(n) {
  if (!n.representative_people?.length) return '';
  return `<details class="core-people" ${disclosureOpen()} aria-label="Historians and contributors for this entry"><summary>Historians & contributors · ${n.representative_people.length}</summary><div class="section-heading"><a class="text-link" href="${esc(href({section:'',edge:'',page:0,kind:'',neighborLayer:''}))}">Explore works & approaches →</a></div><ul>${n.representative_people.map(r => `<li data-person="${r.person_id}"><a href="${esc(personHref(r.person_id))}">${esc(personById.get(r.person_id).label)}</a><span>${esc(PERSON_ROLES[r.role])}</span></li>`).join('')}</ul><p class="fine-print">All ${n.representative_people.length} people in this entry’s selection. Roles distinguish historians, resources, and critics; this roster is not an influence diagram.</p></details>`;
}
function schoolPeople() {
  const n = nodeById.get(state.node);
  const reps = n.representative_people;
  return `${crumbs([`<a href="${esc(href({node: '', person: '', edge: '', page: 0, section: ''}))}">${state.pathway ? 'Back to pathway' : 'Back to entries'}</a>`, `<span aria-current="page">${esc(n.label)}</span>`])}
    <div class="section-heading"><div><p class="eyebrow">03 / MEET THE HISTORIANS & CONTRIBUTORS</p><h2>${esc(n.label)}</h2></div><span class="count">${reps.length} people in this selection</span></div>
    ${schoolTabs(n)}<div class="school-layout"><section aria-label="Representative people"><p class="context-note">A selective guide to the people behind this entry. The labels distinguish historians, intellectual resources, and critics; inclusion does not imply a shared doctrine or formal membership.</p>
      <div data-reading-entry="${esc(n.id)}"></div>${extensionSection(n)}${strandGuide(n)}<div class="people-grid">${pageSlice(reps, 12).map(rep => personCard(personById.get(rep.person_id), rep)).join('')}</div>${pagination(reps.length, 12)}</section>
      <aside class="reading-panel" aria-label="Entry details">${nodeDetail(n,false)}</aside></div>`;
}
/* ---------------- Historians & contributors: the company they keep ----------------
   Two levels (people.mjs): the families overview (#tab=people) and one family's ring
   (#tab=people&family=<slug>). With family=all, or without the evidence asset, every entry sits
   on one ring as before. `companyL` is the layout last built; a hold link opens the level that
   draws what it holds. */
let companyHover = null, companyWidth = 0, companyBound = false, companyL = null;
const ROLE_SHORT = {historian: 'historian', contributor: 'resource', precursor: 'earlier resource', critic: 'critic', comparison: 'comparison'};
const filtersOn = () => Boolean(state.query || state.layer || state.period || state.hunt);
const nameMark = label => { const {surname} = sortName(label); const i = label.indexOf(surname);
  return i < 0 ? esc(label) : `${esc(label.slice(0, i))}<strong>${esc(surname)}</strong>${esc(label.slice(i + surname.length))}`; };
/* The level to draw: 'all', a family id, or '' for the overview. An old link holding an entry
   (#tab=people&hold=women) opens that entry's family. */
function companyLevel() {
  const block = evidence?.families;
  if (!block?.families?.length || state.family === 'all') return 'all';
  const index = familyIndex(graph, block);
  if (!index.families.length) return 'all';
  return index.families.some(f => f.id === state.family) ? state.family : index.primaryOf.get(state.hold) || '';
}
function companyModel(width) {
  const level = companyLevel();
  companyL = level === 'all' ? companyLayout(graph, width) : level ? familyCompanyLayout(graph, evidence.families, level, width)
    : familyOverviewLayout(graph, evidence.families, width);
  companyL.drawn = new Set([...companyL.people.map(p => p.id), ...(companyL.kind === 'overview' ? [] : companyL.anchors.map(a => a.id))]);
  return companyL;
}
const familyName = (L, id) => L.index?.families.find(f => f.id === id)?.label || id;
/* Where holding `id` is drawn: this level if it draws them; else an entry's family or a person's
   only family; else the overview, which lights the families of anyone not drawn. */
function holdFamily(id) {
  const L = companyL;
  if (!L || L.kind === 'all') return state.family;
  if (L.drawn.has(id)) return L.kind === 'family' ? L.family.id : '';
  const fs = L.index.primaryOf.has(id) ? [L.index.primaryOf.get(id)] : L.index.familiesOf.get(id) || [];
  return fs.length === 1 ? fs[0] : '';
}
const holdHref = id => href({hold: id, letter: '', page: 0, family: holdFamily(id)});
/* Opening a family keeps a held person who belongs to it. */
const familyPeopleHref = (L, id) => href({family: id, letter: '', page: 0,
  hold: state.hold && (L.index.familiesOf.get(state.hold) || []).includes(id) ? state.hold : ''});
const overviewHref = () => href({family: '', hold: '', letter: '', page: 0});
const dotClass = (p, matched, extra = '') => ['dot', extra, p.own ? 'own' : '', p.roles.includes('critic') ? 'critic' : '',
  p.roles.includes('historian') || p.own ? '' : 'resource', matched && !matched.has(p.id) ? 'mute' : '', state.hold === p.id ? 'selected' : ''].filter(Boolean).join(' ');
const dotMarks = p => `${p.roles.includes('critic') ? `<circle class="ring" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${(p.r + 1.6).toFixed(1)}"/>` : ''}
      <circle class="core" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.r.toFixed(1)}"/>`;
const nameTexts = (L, matched) => L.labels.map(l => `<text class="dot-label${matched && !matched.has(l.id) ? ' mute' : ''}" data-for="${l.id}" x="${l.x.toFixed(1)}" y="${(l.y + 3.5).toFixed(1)}" text-anchor="${l.anchor}">${esc(l.text)}</text>`).join('');
/* The drawing's own extent (people.mjs `view`), never stretched past its drawn size. */
const viewBox = L => `viewBox="${L.view.x.toFixed(1)} ${L.view.y.toFixed(1)} ${L.view.w.toFixed(1)} ${L.view.h.toFixed(1)}" width="${Math.round(L.view.w)}" height="${Math.round(L.view.h)}" style="max-width:${Math.round(L.view.w)}px"`;
/* One ring of entries: every entry (family=all, or the fallback) or one family's. */
function companySvg(L, matched, allowed) {
  const t = id => layerIndex(nodeById.get(id).layer);
  const pos = new Map(L.anchors.map(a => [a.id, a]));
  const spokes = L.people.filter(p => !p.single).flatMap(p => p.entries.map(g => { const a = pos.get(g);
    return `<line class="spoke" data-p="${p.id}" data-g="${g}" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${a.x.toFixed(1)}" y2="${a.y.toFixed(1)}"/>`; })).join('');
  const dots = L.people.map(p => {
    const label = personById.get(p.id).label, away = p.elsewhere || [];
    const cls = dotClass(p, matched, `${p.single ? `tone-${layerIndex(p.layer)}` : 'bridge'}${away.length ? ' elsewhere' : ''}`);
    const also = away.length ? `; also in ${away.map(f => familyName(L, f)).join(', ')}` : '';
    const body = `<title>${esc(label)} · ${p.entries.length} entr${p.entries.length === 1 ? 'y' : 'ies'}${esc(also)}</title>${dotMarks(p)}
      ${away.length ? `<circle class="away" cx="${(p.x + p.r * 0.8 + 1.6).toFixed(1)}" cy="${(p.y - p.r * 0.8 - 1.6).toFixed(1)}" r="1.7"/>` : ''}`;
    return p.own ? `<a class="${cls}" data-id="${p.id}" href="${esc(holdHref(p.id))}" aria-label="${esc(label)}: light up their entries${esc(also)}">${body}</a>` : `<g class="${cls}" data-id="${p.id}">${body}</g>`;
  }).join('');
  const anchors = L.anchors.map(a => {
    const deg = a.angle * 180 / Math.PI, flip = ((deg % 360) + 360) % 360 > 90 && ((deg % 360) + 360) % 360 < 270;
    const lx = (L.cx + (L.R + 16) * Math.cos(a.angle)).toFixed(1), ly = (L.cy + (L.R + 16) * Math.sin(a.angle)).toFixed(1);
    /* people.mjs fits each label to the space outside the ring (fitLabel); the full label stays
       in the accessible name. Lines stack about the radius, so a flipped label reads the same. */
    const k = a.lines.length;
    const lines = a.lines.map((l, i) => `<tspan x="${lx}" dy="${i ? ENTRY_LINE : (-(k - 1) / 2 * ENTRY_LINE).toFixed(2)}">${esc(l)}${i === k - 1 ? ` <tspan class="n">${a.count}</tspan>` : ''}</tspan>`).join('');
    const home = a.bridged ? `; shared from ${familyName(L, a.home)}` : '';
    const cls = ['anchor', `tone-${t(a.id)}`, a.bridged ? 'bridged' : '', allowed && !allowed.has(a.id) ? 'mute' : '', state.hold === a.id ? 'selected' : ''].filter(Boolean).join(' ');
    return `<a class="${cls}" data-id="${a.id}" href="${esc(holdHref(a.id))}" aria-label="${esc(a.label)}, ${a.count} people${esc(home)}"><circle cx="${a.x.toFixed(1)}" cy="${a.y.toFixed(1)}" r="${(L.size * 0.0045 + 2).toFixed(1)}"/>
      <text x="${lx}" y="${ly}" transform="rotate(${(flip ? deg + 180 : deg).toFixed(1)} ${lx} ${ly})" text-anchor="${flip ? 'end' : 'start'}" dominant-baseline="middle">${lines}</text></a>`;
  }).join('');
  const what = L.kind === 'family' ? `The entries of ${L.family.label}, with the people they name` : 'People placed between the entries that name them';
  return `<svg class="company${state.hold ? ' held' : ''}" ${viewBox(L)} role="group" aria-label="${esc(what)}">
    <g class="spokes">${spokes}</g><g class="dots">${dots}</g><g class="names">${nameTexts(L, matched)}</g><g class="anchors">${anchors}</g></svg>`;
}
/* The overview: the families on a ring, and only the people named in two or more of them. */
function overviewSvg(L, matched) {
  const pos = new Map(L.anchors.map(a => [a.id, a]));
  const spokes = L.people.flatMap(p => p.families.map(f => { const a = pos.get(f);
    return `<line class="spoke" data-p="${p.id}" data-g="family:${f}" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${a.x.toFixed(1)}" y2="${a.y.toFixed(1)}"/>`; })).join('');
  const dots = L.people.map(p => {
    const label = personById.get(p.id).label, fams = p.families.map(f => pos.get(f).label).join(', ');
    return `<a class="${dotClass(p, matched, 'bridge')}" data-id="${p.id}" href="${esc(holdHref(p.id))}" aria-label="${esc(`${label}: named in ${p.families.length} families, ${fams}. Light them up`)}"><title>${esc(label)} · ${esc(fams)}</title>${dotMarks(p)}</a>`;
  }).join('');
  const families = L.anchors.map(a => {
    const hits = matched ? L.index.families.find(f => f.id === a.id).people.filter(id => matched.has(id)).length : null;
    const lines = matched ? [...a.lines.slice(0, -1), `${hits} of ${a.count} match`] : a.lines;
    const text = lines.map((l, i) => `<tspan class="${i === lines.length - 1 ? 'n' : ''}" x="${a.lx.toFixed(1)}" y="${(a.top + FAMILY_LINE * (i + 0.78)).toFixed(1)}">${esc(l)}</tspan>`).join('');
    const said = `${a.label}: ${a.count} people named in ${a.entries} entr${a.entries === 1 ? 'y' : 'ies'}; ${a.shared} also named in other families. Open the family.`;
    /* One target for the disc and its label together. */
    const hit = [Math.min(a.box[0], a.x - a.r), Math.min(a.box[1], a.y - a.r), Math.max(a.box[2], a.x + a.r), Math.max(a.box[3], a.y + a.r)];
    return `<a class="family-anchor${hits === 0 ? ' mute' : ''}" data-id="family:${a.id}" href="${esc(familyPeopleHref(L, a.id))}" aria-label="${esc(said)}"><rect class="hit" x="${hit[0].toFixed(1)}" y="${hit[1].toFixed(1)}" width="${(hit[2] - hit[0]).toFixed(1)}" height="${(hit[3] - hit[1]).toFixed(1)}"/><circle class="disc" cx="${a.x.toFixed(1)}" cy="${a.y.toFixed(1)}" r="${a.r.toFixed(1)}"/><text text-anchor="${a.anchor}">${text}</text></a>`;
  }).join('');
  return `<svg class="company overview${state.hold ? ' held' : ''}" ${viewBox(L)} role="group" aria-label="${L.anchors.length} families of historical writing, with the ${L.people.length} people named in two or more of them placed between those families">
    <g class="spokes">${spokes}</g><g class="families">${families}</g><g class="dots">${dots}</g><g class="names">${nameTexts(L, matched)}</g></svg>`;
}
const LEGEND = `<ul class="company-legend"><li><span class="lg lg-hist"></span>named as historian</li><li><span class="lg lg-res"></span>named as resource or comparison</li><li><span class="lg lg-crit"></span>critical intervention</li><li><span class="lg lg-own"></span>has own entry</li>`;
const topList = (rows, link) => `<ol class="bridge-list">${rows.map(b => `<li><a href="${esc(link(b.id))}" aria-label="${esc(b.label)}: light up their entries">${esc(b.label)}</a><span>${b.count}</span></li>`).join('')}</ol>`;
function companyIntro(L) {
  if (L.kind === 'overview') {
    const top = L.people.map(p => ({id: p.id, label: personById.get(p.id).label, count: p.families.length, entries: p.entries.length}))
      .sort((a, b) => b.count - a.count || b.entries - a.entries || a.label.localeCompare(b.label)).slice(0, 8);
    const counted = L.index.families.reduce((s, f) => s + f.people.length, 0);
    return `<div class="panel-empty"><p class="eyebrow">Nothing selected</p>
      <h2>${canHover() ? 'Hover a family or a dot. Click a family to open it.' : 'Tap a family circle to explore. Tap a person to hold them.'}</h2>
      <p>The ${L.anchors.length} families of the landing page sit on the ring; a disc’s area is the number of people its entries name. Only the ${L.people.length} people named in entries of two or more families are drawn, between those families, in ink. Everyone else is counted at their family and drawn when you open it.</p>
      ${LEGEND}</ul>
      <div class="sec"><p class="eyebrow">Families</p><ul class="panel-entries family-list">${L.index.families.map(f => `<li><a href="${esc(familyPeopleHref(L, f.id))}">${esc(f.label)}</a><span class="role-tag">${f.people.length} people</span></li>`).join('')}</ul></div>
      <div class="sec"><p class="eyebrow">Named across the most families</p>${topList(top, holdHref)}</div>
      <p class="fine-print">A person counts once in each family whose entries name them, so the families’ counts sum to ${counted}, more than the people drawn and counted. Sharing a family is shared context, not influence. <a href="${esc(href({family: 'all', hold: '', letter: ''}))}">All entries on one ring →</a></p></div>`;
  }
  const ring = new Set(L.order);
  const top = bridges(graph, L.kind === 'family' ? new Map([...L.byPerson].map(([id, rows]) => [id, rows.filter(r => ring.has(r.id))]).filter(([, rows]) => rows.length)) : L.byPerson, 8);
  if (L.kind === 'family') {
    const own = L.anchors.filter(a => !a.bridged), shared = L.anchors.filter(a => a.bridged);
    const entry = a => `<li><a href="${esc(holdHref(a.id))}">${esc(a.label)}</a><span class="role-tag">${a.count}</span></li>`;
    return `<div class="panel-empty"><p class="eyebrow">${esc(L.family.label)} · nothing selected</p>
      <h2>${canHover() ? 'Hover a dot to see whose company they keep. Click to hold.' : 'Tap a person to see whose company they keep.'}</h2>
      <p>The family’s ${own.length} entr${own.length === 1 ? 'y sits' : 'ies sit'} on the ring${shared.length ? `, then the ${shared.length} it shares with other families, in outline` : ''}, each with the number of people it names. A person named in one of them gathers at that entry, in its colour; a person named in several moves inward, between them, in ink. A small dot at a person’s shoulder marks someone also named in another family.</p>
      ${LEGEND}<li><span class="lg lg-away"></span>also in another family</li></ul>
      <div class="sec"><p class="eyebrow">Entries</p><ul class="panel-entries">${own.map(entry).join('')}</ul>${shared.length ? `<p class="eyebrow">Shared with other families</p><ul class="panel-entries">${shared.map(entry).join('')}</ul>` : ''}</div>
      ${top.length && top[0].count > 1 ? `<div class="sec"><p class="eyebrow">Named in the most entries here</p>${topList(top.filter(b => b.count > 1), holdHref)}</div>` : ''}
      <p class="fine-print">Sharing an entry is shared context, not influence: no line is drawn between two people. Placement is the plain mean of an entry’s positions, not a force layout.</p></div>`;
  }
  return `<div class="panel-empty"><p class="eyebrow">Nothing selected</p>
      <h2>${canHover() ? 'Hover a dot to see whose company they keep. Click to hold.' : 'Tap a person to see whose company they keep.'}</h2>
      <p>Each of the ${L.anchors.length} entries sits on the ring with the number of people it names. A person named in one entry gathers at that entry, in its colour. A person named in several entries moves inward, between them, in ink. The bigger dots are the ${graph.people.filter(p => p.node_id).length} people who also have an entry of their own.</p>
      ${LEGEND}</ul>
      <div class="sec"><p class="eyebrow">Named in the most entries</p>${topList(top, holdHref)}</div>
      <p class="fine-print">Sharing an entry is shared context, not influence: no line is drawn between two people, and a roster place is not an edge. Placement is the plain mean of an entry’s positions, not a force layout.</p></div>`;
}
function companyPanel(L) {
  const id = companyHover || state.hold;
  const release = state.hold && !companyHover ? `<p class="panel-release"><a class="release" href="${esc(href({hold: ''}))}">← Show everyone</a></p>` : '';
  if (!id) return companyIntro(L);
  if (id.startsWith('family:')) {
    const f = L.index.families.find(x => x.id === id.slice(7)), a = L.anchors.find(x => x.id === f.id);
    const shared = L.people.filter(p => p.families.includes(f.id)).sort((x, y) => y.families.length - x.families.length || y.entries.length - x.entries.length).slice(0, 6);
    return `<p class="eyebrow">Family · ${f.entries.length} entr${f.entries.length === 1 ? 'y' : 'ies'} · ${f.people.length} people</p><h2>${esc(f.label)}</h2>
      <p>${a.shared} of them ${a.shared === 1 ? 'is' : 'are'} also named in other families${f.bridged.length ? `; ${f.bridged.length} more entr${f.bridged.length === 1 ? 'y is' : 'ies are'} shared from other families` : ''}.</p>
      <div class="sec"><p class="eyebrow">Entries</p><ul class="panel-roster">${f.entries.map(e => `<li><a href="${esc(holdHref(e))}">${esc(nodeById.get(e).label)}</a></li>`).join('')}</ul></div>
      ${shared.length ? `<div class="sec"><p class="eyebrow">Shared most widely</p><ul class="panel-roster">${shared.map(p => `<li><a href="${esc(holdHref(p.id))}">${esc(personById.get(p.id).label)}</a><span class="panel-work">${p.families.length} families</span></li>`).join('')}</ul></div>` : ''}
      <p class="panel-more"><a class="button-link" href="${esc(familyPeopleHref(L, f.id))}">Open this family →</a></p>`;
  }
  if (personById.has(id)) {
    const p = personById.get(id); const rows = L.byPerson.get(id) || []; const own = nodeById.get(p.node_id);
    const fams = L.index?.familiesOf.get(id) || [];
    const away = L.kind === 'family' ? fams.filter(f => f !== L.family.id) : fams;
    const famLinks = away.map(f => `<a href="${esc(href({family: f, hold: id, letter: '', page: 0}))}">${esc(familyName(L, f))}</a>`).join(' · ');
    return `${release}<p class="eyebrow">${rows.length ? `Named in ${new Set(rows.map(r => r.id)).size} entr${new Set(rows.map(r => r.id)).size === 1 ? 'y' : 'ies'}` : 'Own entry only'}${L.index && fams.length ? ` · ${fams.length} famil${fams.length === 1 ? 'y' : 'ies'}` : ''}${own ? ' · has own entry' : ''}</p>
      <h2>${esc(p.label)}${lifeSpan(p)}</h2>${own ? `<p class="claim">${esc(own.description)}</p>` : ''}
      ${away.length ? `<p class="panel-families"><span class="eyebrow">${L.kind === 'family' ? 'Also in' : 'Families'}</span> ${famLinks}</p>` : ''}
      <ul class="panel-entries">${rows.map(r => `<li><a href="${esc(holdHref(r.id))}">${esc(nodeById.get(r.id).label)}</a><span class="role-tag">${esc(PERSON_ROLES[r.role])}</span></li>`).join('')}</ul>
      <p class="panel-more"><a class="button-link" href="${esc(personHref(id))}">Profile: where to read them →</a>${own ? ` <a class="button-link" href="${esc(nodeHref(own.id))}">Full entry →</a>` : ''}</p>`;
  }
  const n = nodeById.get(id); const rows = L.byEntry.get(id) || [];
  const reps = new Map((n.representative_people || []).map(r => [r.person_id, r]));
  const groups = ['historian', 'contributor', 'critic', 'precursor', 'comparison'].map(role => [role, rows.filter(r => r.role === role)]).filter(([, r]) => r.length);
  const home = L.index?.primaryOf.get(id);
  /* One person per line with the work the entry cites, so a long roster can be scanned. */
  const line = x => { const rep = reps.get(x.id); const work = (rep?.works || '').split(';')[0].trim();
    return `<li><a href="${esc(holdHref(x.id))}">${esc(personById.get(x.id).label)}</a>${lifeSpan(personById.get(x.id))}${work ? `<span class="panel-work">${esc(work.length > 70 ? `${work.slice(0, 69)}…` : work)}</span>` : ''}</li>`; };
  return `${release}<p class="eyebrow">${esc(layerLabel(n.layer))} · ${rows.length} people</p><h2>${esc(n.label)}</h2><p class="meta">${esc(chronologyLabel(n))}</p>
    ${L.kind === 'family' && home && home !== L.family.id ? `<p class="panel-families">Shared with this family from <a href="${esc(href({family: home, hold: id, letter: '', page: 0}))}">${esc(familyName(L, home))}</a>.</p>` : ''}
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
  companyHover = null;   /* a hover belongs to the chart it was made on */
  const L = companyModel(1000);
  const note = 'Roles distinguish historians from intellectual resources and critics; being named together is shared context, not influence.';
  let head;
  if (L.kind === 'family') {
    const shared = L.anchors.filter(a => a.bridged).length;
    head = `${crumbs([`<a href="${esc(overviewHref())}">Historians & contributors</a>`, `<span aria-current="page">${esc(L.family.label)}</span>`])}
    <nav class="family-crumbs" aria-label="Families"><a href="${esc(overviewHref())}">← All families</a><a href="${esc(href({tab: 'map', family: L.family.id, view: 'map', hold: '', letter: '', page: 0}))}">This family’s timeline →</a><a href="${esc(href({tab: 'map', family: L.family.id, view: 'approaches', hold: '', letter: '', page: 0}))}">This family’s approaches & works →</a></nav>
    <div class="section-heading"><div><p class="eyebrow">THE COMPANY THEY KEEP · ONE FAMILY</p><h2>${esc(L.family.label)}</h2></div><span class="count">${L.people.length} people · ${L.anchors.length - shared} entries${shared ? ` · ${shared} shared with other families` : ''}</span></div>
    <details class="company-guide" ${disclosureOpen()}><summary>How to read the circles</summary><p class="context-note">Everyone this family’s entries name, placed between the entries that name them. A small dot at a person’s shoulder marks someone also named in another family; the panel links to it. ${canHover() ? 'Hover to see whose company someone keeps; click to hold.' : 'Tap a person to hold them and read their context.'} Search or filter above to light up a subset. ${note}</p></details>`;
  } else if (L.kind === 'overview') {
    head = `${crumbs(['<span aria-current="page">Historians & contributors</span>'])}<div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THE CONVERSATIONS</p><h2>The company they keep</h2></div><span class="count">${graph.people.length} people · ${L.anchors.length} families · ${L.people.length} named in more than one</span></div>
    <details class="company-guide" ${disclosureOpen()}><summary>How to read the circles</summary><p class="context-note">The families of historical writing, as on the landing page. The people drawn are those named in the entries of two or more families, placed between them; open a family to see everyone its entries name. ${canHover() ? 'Hover to see whose company someone keeps; click to hold.' : 'Tap a person to hold them and read their context.'} Search or filter above to light up a subset. ${note}</p></details>`;
  } else {
    head = `${crumbs(['<span aria-current="page">Historians & contributors</span>'])}${state.family === 'all' && evidence?.families ? `<nav class="family-crumbs" aria-label="Families"><a href="${esc(overviewHref())}">← All families</a></nav>` : ''}<div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THE CONVERSATIONS</p><h2>The company they keep</h2></div><span class="count">${graph.people.length} people · ${L.anchors.length} entries that name them</span></div>
    <details class="company-guide" ${disclosureOpen()}><summary>How to read the circles</summary><p class="context-note">Every person in these circles is placed between the schools, fields and debates that name them. ${canHover() ? 'Hover to see whose company someone keeps; click to hold.' : 'Tap a person to hold them and read their context.'} Search or filter above to light up a subset. ${note}</p></details>`;
  }
  return `${head}
    <p class="touch-only chart-hint">Drag inside the circles to explore. Tap a family to open it or a person to hold them. <button type="button" data-scroll-target="people-register">People list ↓</button></p>
    <div class="company-split" data-held="${Boolean(state.hold)}"><div class="company-chart" id="company-map" tabindex="0" role="region" aria-label="Interactive people circles" aria-busy="true"></div><aside class="field-panel company-panel" aria-label="Selection details">${state.hold ? chartReturn('company-map', 'Back to circles') : ''}${companyPanel(L)}</aside></div>
    <section class="register-section" id="people-register" tabindex="-1" aria-label="Register of people">${register(L)}</section>`;
}
function drawCompany() {
  const box = document.querySelector('.company-chart');
  if (!box) return;
  companyWidth = box.clientWidth || 0;
  if (!companyWidth) return;
  const layoutWidth = phoneCircles() ? Math.max(620, companyWidth) : companyWidth;
  box.style.setProperty('--circle-width', `${layoutWidth}px`);
  const L = companyModel(layoutWidth);
  const matched = filtersOn() ? new Set(filterPeople(graph, state).map(p => p.id)) : null;
  const allowed = filtersOn() ? new Set(filterNodes(graph.nodes, {...state, query: ''}).map(n => n.id)) : null;
  box.innerHTML = L.kind === 'overview' ? overviewSvg(L, matched) : companySvg(L, matched, allowed);
  box.removeAttribute('aria-busy');
  const svg = box.querySelector('svg.company');
  const panel = document.querySelector('.company-panel');
  const paint = () => { panel.innerHTML = `${state.hold ? chartReturn('company-map', 'Back to circles') : ''}${companyPanel(L)}`; };
  const light = id => {
    const related = new Set();
    if (id?.startsWith('family:')) { for (const p of L.people) if (p.families.includes(id.slice(7))) related.add(p.id); }
    else if (id && L.kind === 'overview') for (const f of L.index.familiesOf.get(id) || []) related.add(`family:${f}`);
    else {
      if (id && L.byPerson.has(id)) for (const r of L.byPerson.get(id)) related.add(r.id);
      if (id && L.byEntry.has(id)) for (const r of L.byEntry.get(id)) related.add(r.id);
    }
    svg.classList.toggle('previewing', Boolean(id));
    for (const el of svg.querySelectorAll('[data-id]')) el.classList.toggle('hi', el.dataset.id === id || related.has(el.dataset.id));
    for (const el of svg.querySelectorAll('.dot-label')) el.classList.toggle('hi', el.dataset.for === id || related.has(el.dataset.for));
    for (const sp of svg.querySelectorAll('.spoke')) sp.classList.toggle('hi', sp.dataset.p === id || sp.dataset.g === id);
  };
  const preview = target => {
    const id = target.closest?.('[data-id]')?.dataset.id || null;
    if (id === companyHover) return;
    companyHover = id; light(id || state.hold || null); paint();
  };
  const clear = () => { if (companyHover === null) return; companyHover = null; light(state.hold || null); paint(); };
  svg.addEventListener('mouseover', e => { if (canHover()) preview(e.target); });
  svg.addEventListener('mouseleave', clear);
  svg.addEventListener('focusin', e => preview(e.target));
  svg.addEventListener('focusout', e => { if (!svg.contains(e.relatedTarget)) clear(); });
  svg.addEventListener('click', e => {
    /* A dot toggles its hold, whether or not it is a link; modified clicks keep the link. */
    const dot = e.target.closest?.('.dot');
    if (dot && !(e.ctrlKey || e.metaKey || e.shiftKey)) { e.preventDefault(); change({hold: state.hold === dot.dataset.id ? '' : dot.dataset.id, letter: ''}); return; }
    if (!e.target.closest('a') && state.hold) change({hold: ''});
  });
  if (state.hold) light(state.hold);
  if (phoneCircles()) {
    box.scrollLeft = (svg.getBoundingClientRect().width - box.clientWidth) / 2;
    const selected = svg.querySelector('.dot.selected, .anchor.selected');
    if (selected) {
      const mark = selected.getBoundingClientRect(), frame = box.getBoundingClientRect();
      box.scrollLeft += mark.x + mark.width / 2 - frame.x - frame.width / 2;
      box.scrollTop = mark.y + mark.height / 2 - frame.y - frame.height / 2;
    }
  }
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
  const family = familyBySlug(evidence?.families, state.family);
  /* A profile opened from the people view (its link says tab=people) leads back to the same
     level and hold; one opened from a family's approaches leads back there. */
  const fromPeople = new URLSearchParams(location.hash.slice(1)).get('tab') === 'people';
  const back = `<a href="${esc(href({person: '', page: 0, section: ''}))}">${esc(parent ? parent.label : fromPeople && family ? family.label : 'Historians & contributors')}</a>`;
  const origin = parent ? back : fromPeople && family ? `<a href="${esc(href({person: '', family: '', hold: '', letter: '', page: 0, section: ''}))}">Historians & contributors</a>${'<span aria-hidden="true">/</span>'}${back}`
    : family ? `<a href="${esc(href({tab: 'map', person: '', node: '', edge: '', focus: '', query: '', view: 'approaches'}))}">${esc(family.label)}</a>` : fromPeople ? back : '<a href="#tab=people">Historians & contributors</a>';
  const basisLabels = {curated_entry: 'Selection recorded in the curated entry', existing_relationship: 'Selection supported by an existing qualified connection', source_review: 'Selection with a scoped source check', editorial_comparison: 'Editorial comparison across constituent fields'};
  return `${crumbs([origin, `<span aria-current="page">${esc(p.label)}</span>`])}<article class="person-profile"><div class="section-heading"><div><p class="eyebrow">A PERSON ACROSS THE PROJECT</p><h2>${esc(p.label)}${lifeSpan(p)}</h2>${p.wikidata?.qid ? `<p class="fine-print">Identity: <a href="https://www.wikidata.org/wiki/${esc(p.wikidata.qid)}" target="_blank" rel="noopener noreferrer">Wikidata ${esc(p.wikidata.qid)}</a>${p.life?.retrieved ? `, dates retrieved ${esc(p.life.retrieved)}` : ''}.</p>` : ''}</div>${own ? `<a class="button-link primary" href="${esc(nodeHref(own.id))}">Full entry & relationships →</a>` : ''}</div>
    ${personMapSection(p)}
    ${own ? `<p class="profile-introduction">${esc(own.description)}</p>` : '<p class="context-note">Read this person through the works and contexts below. These are selected points of entry, not a complete biography.</p>'}
    <h3>Where to read them</h3><div class="person-contexts">${contexts.map(({node:n, representative:r}) => `<section class="person-affiliation tone-${layerIndex(n.layer)}">${layerTag(n)}<h3><a href="${esc(nodeHref(n.id))}">${esc(n.label)} →</a></h3><span class="role-tag">${esc(PERSON_ROLES[r.role])}</span><p>${esc(r.context)}</p>
      ${r.works ? `<p class="person-work">${esc(r.works)}</p>` : `<p class="fine-print">The current selection names this person without a separate work citation. <a href="${esc(nodeHref(n.id))}">Read the group’s works and references.</a></p>`}
      <details class="person-evidence"><summary>References & basis for inclusion</summary><p class="fine-print">${esc(basisLabels[r.basis])}. Group references provide context; they do not certify every affiliation or interpretation.</p>${r.edge_id ? `<a class="text-link" href="#edge=${r.edge_id}">Inspect the existing relationship →</a>` : ''}${sourceList(r.source_ids)}</details></section>`).join('')}</div>
    ${!contexts.length && own ? `<p>No group roster currently includes this person. Their individual entry provides the selected works and connections.</p><section class="reading-panel"><h3>Representative figures & works</h3><p>${esc(own.representative_figures_and_works)}</p><details class="bibliography" open><summary>References</summary>${sourceList(own.source_ids)}</details></section>` : ''}
    <div data-reading-person="${esc(p.id)}"></div>${strandContexts(p)}
    ${RECORD_PILOT.has(p.id) ? `<div data-person-records="${esc(p.id)}" aria-live="polite">${peopleRecords ? publicationPanel(peopleRecords,p.id) : '<p class="fine-print">Loading publication records…</p>'}</div>` : ''}
    </article>`;
}
/* ---------------- Where they sit: the profile's compact field ----------------
   The same layout as the field (buildFieldLayout, compact), restricted to the entries that name
   this person, their own entry, and the entries its relationships reach. Drawn after measuring
   the column, like the field, and redrawn on resize. */
let personMapWidth = 0, personMapSubsetMemo = null;
const PM_ROLE_ORDER = ['historian', 'contributor', 'precursor', 'critic', 'comparison', 'approach'];
const PM_ROLE_LABEL = {...PERSON_ROLES, approach: 'Named within an approach'};
function pmSubset(id) {
  if (personMapSubsetMemo?.id !== id || personMapSubsetMemo.g !== graph)
    personMapSubsetMemo = {id, g: graph, s: personMapSubset(graph, id)};
  return personMapSubsetMemo.s;
}
/* What a mark says on hover, on focus and to a screen reader: the entry, its dates, the role. */
function pmDescribe(p, s, id) {
  const n = nodeById.get(id);
  const parts = [`${n.label}${chronologyLabel(n) ? `, ${chronologyLabel(n)}` : ''}.`];
  if (id === s.own) parts.push(`${p.label}’s own entry${s.edges.length ? `, with ${s.edges.length} recorded relationship${s.edges.length === 1 ? '' : 's'}` : ''}.`);
  if (s.roster.has(id)) parts.push(`${s.roster.get(id) === 'approach' ? 'Names them within an approach' : `Names them as ${PM_ROLE_LABEL[s.roster.get(id)].toLowerCase()}`}.`);
  for (const r of s.linked.get(id) || [])
    parts.push(`${r.dir === 'out' ? `${p.label} ${dirWord(r.edge.relationship_kind, 'out')} this entry` : `This entry ${dirWord(r.edge.relationship_kind, 'out')} ${p.label}`} (${kindChip(r.edge.relationship_kind).toLowerCase()}).`);
  return parts.join(' ');
}
const pmHasLead = s => [...s.ids].some(id => { const n = nodeById.get(id), sp = n && spanOf(n);
  return Boolean(sp?.openStart); });
function personMapSection(p) {
  const s = pmSubset(p.id);
  if (!s.ids.size) return '';
  const own = s.own ? nodeById.get(s.own) : null;
  const named = [...s.roster.values()].filter(r => r !== 'approach').length;
  const reach = s.linked.size;
  const leave = {person: '', node: '', edge: '', page: 0, section: '', hold: '', letter: '', tab: 'map', view: 'map', family: '', path: ''};
  const fieldLink = own ? href({...leave, focus: own.id, query: ''})
    : href({...leave, focus: '', query: p.label});
  const summary = [named ? `Named on ${named} entr${named === 1 ? 'y’s roster' : 'ies’ rosters'}` : s.basis === 'approach' ? `Named within approaches of ${s.roster.size} entr${s.roster.size === 1 ? 'y' : 'ies'}` : '',
    own ? `own entry${s.edges.length ? ` with ${s.edges.length} relationship${s.edges.length === 1 ? '' : 's'} to ${reach} entr${reach === 1 ? 'y' : 'ies'}` : ''}` : ''].filter(Boolean).join(' · ');
  const roles = PM_ROLE_ORDER.filter(r => [...s.roster.values()].includes(r));
  const kinds = [...new Set(s.edges.map(e => e.relationship_kind))];
  const fr = frameOf(graph);
  return `<section class="person-map" aria-labelledby="pm-title"><div class="pm-head"><div><p class="eyebrow">WHERE THEY SIT</p>
      <h3 id="pm-title">${esc(p.label)} on the time axis</h3><p class="pm-summary">${esc(summary)}.</p></div>
      <a class="text-link pm-open" href="${esc(fieldLink)}">${own ? 'Open in the field' : 'Find them in the field'} →</a></div>
    <div class="pm-scroll" data-person="${esc(p.id)}" aria-busy="true"></div>
    <p class="pm-readout" aria-live="polite">${own || s.ids.size > 1 ? 'Hover or focus a mark for the entry and their role in it; select it to open the entry.' : 'Select the mark to open the entry.'}</p>
    <ul class="pm-legend" aria-label="Key">
      ${roles.map(r => `<li><span class="pm-badge-key${r === 'critic' ? ' critic' : ''}">${esc(ROLE_BADGE[r])}</span>${esc(PM_ROLE_LABEL[r].toLowerCase())}</li>`).join('')}
      ${own ? '<li><span class="pm-sw own"></span>their own entry</li>' : ''}
      ${reach ? '<li><span class="pm-sw linked"></span>related to their entry; does not name them</li>' : ''}
      ${pmHasLead(s) ? '<li><span class="pm-sw lead"></span>earlier roots, undated</li>' : ''}
      ${kinds.map(k => `<li class="pm-kind k-${esc(BASE_KINDS.includes(k) ? k : 'extra')}"><i></i>${esc(kindChip(k).toLowerCase())}</li>`).join('')}
      ${explicitChronology() ? '<li>● selected contribution · ○ context · ◇ edition or reception · † death (later points hollow: posthumous) · ▫ editorial review year · ◁ before 1750</li>' : fr.open ? '<li><span class="pm-sw tail"></span>solid to the year reviewed; faded where later work is not yet surveyed</li>'
        : `<li><span class="pm-sw wall"></span>${esc(fr.wall)}: the archive’s coverage limit, not an ending</li>`}
    </ul>
    <p class="fine-print pm-note">${explicitChronology() ? 'Points date works and events; dotted lines connect the selected contributions, not a lifespan, and stop at a person’s death. Editorial review years remain separate.' : 'Colour follows each entry’s layer, as in the cards below. Bars follow the years each entry’s date label names;'} A roster place is shared context, not influence${own ? ', and only relationships recorded for their own entry are drawn' : ''}.</p></section>`;
}
/* Shared marks for full, family and compact maps. Geometry comes only from graph facts. */
function chronologyShapes(p) {
  const c = p.chronology, mid = p.y + p.h / 2;
  const r = p.h < 16 ? 3 : 4;
  const selection = c.selection?.w > 0 ? `<line class="chron-selection" x1="${c.selection.x}" x2="${c.selection.x + c.selection.w}"
    y1="${mid}" y2="${mid}"><title>Extent of selected contributions; not historical duration</title></line>` : '';
  const intervals = c.intervals.map(i => i.unknownEnd
    ? `<circle class="chron-unknown" cx="${i.x}" cy="${mid}" r="${r + 2}"><title>${esc(i.subject)}: from ${esc(dateText(i.start))}; ending unestablished</title></circle>`
    : `<rect class="chron-interval${i.track === 'context' ? ' interval-context' : ''}" x="${i.x}" y="${mid - 3}" width="${Math.max(1, i.w)}" height="6"><title>${esc(i.subject)}: ${esc(dateText(i.start))}–${esc(dateText(i.end))}; ${esc(i.end_meaning.replace(/_/g, ' '))}${i.track === 'context' ? '; lineage context' : ''}</title></rect>`).join('');
  const events = c.events.map(e => {
    const y = e.track === 'context' ? mid - 4 : e.track === 'reception' || e.track === 'editions' ? mid + 4 : mid;
    const title = `${e.before ? 'Before 1750 (drawn at the axis edge): ' : ''}${dateText(e.date)} · ${e.label} · ${e.kind.replace(/_/g, ' ')} · ${e.track}${e.posthumous ? ' · posthumous' : ''}`;
    const range = !e.before && e.x1 > e.x0 ? `<line class="chron-range" x1="${e.x0}" x2="${e.x1}" y1="${y}" y2="${y}"/>` : '';
    /* Events before the axis floor point off the left edge; their real date is in the title and panels. */
    if (e.before) return `<g class="chron-event chron-before track-${e.track}" data-event="${esc(e.id)}" data-year="${e.bounds[0]}">
      <title>${esc(title)}</title><path d="M${e.x - r} ${y} l${r + 1} ${-r} v${2 * r} z"/></g>`;
    return `<g class="chron-event track-${e.track}${e.uncertain ? ' uncertain' : ''}${e.posthumous ? ' posthumous-event' : ''}" data-event="${esc(e.id)}" data-year="${e.bounds[0]}">
      <title>${esc(title)}</title>${range}${e.track === 'reception' || e.track === 'editions'
        ? `<path d="M${e.x} ${y-r} l${r} ${r} l${-r} ${r} l${-r} ${-r} z"/>`
        : `<circle cx="${e.x}" cy="${y}" r="${r}"/>`}</g>`;
  }).join('');
  const death = c.death ? `<g class="death-mark"><line x1="${c.death.x}" y1="${mid - r - 4}" x2="${c.death.x}" y2="${mid + r + 4}"/>
    <text x="${c.death.x}" y="${mid - r - 5}" text-anchor="middle">†</text><title>Died ${c.death.yr} (Wikidata); later points are posthumous</title></g>` : '';
  const review = p.reviewMarker ? `<rect class="chron-review" x="${p.reviewMarker.x - 2.5}" y="${p.y + p.h + 1}" width="5" height="4"><title>Editorial coverage: reviewed through ${p.reviewMarker.year}; not a historical endpoint</title></rect>` : '';
  return `<rect class="chron-hit" x="${p.x - 5}" y="${p.y - 3}" width="${p.w + 10}" height="${p.h + 6}" rx="3"/>${selection}${intervals}${events}${death}${review}`;
}

function personMapSvg(L, p) {
  const s = L.subset, fr = L.frame, top = L.axisTop + 16, bottom = L.height - 2;
  let grid = '';
  const step = L.inner < 640 ? 40 : 20;
  for (let yr = Math.ceil(L.minYear / 10) * 10; yr <= L.maxYear; yr += 10) {
    if (yr < L.breakYear && yr % 50) continue;
    const x = L.scale(yr).toFixed(1), major = yr >= L.breakYear ? yr % step === 0 : yr % 100 === 0;
    grid += `<line class="pm-tick${major ? ' major' : ''}" x1="${x}" y1="${top}" x2="${x}" y2="${bottom}"/>${major
      ? `<text class="pm-tick-label" x="${x}" y="${L.axisTop + 8}" text-anchor="middle">${yr}</text>` : ''}`;
  }
  if (L.earlyShare) { const bx = L.scale(L.breakYear).toFixed(1);
    grid += `<line class="pm-break" x1="${bx}" y1="${top}" x2="${bx}" y2="${bottom}"><title>Before 1900 the axis is compressed</title></line>`; }
  if (fr.open) { const cx = L.scale(fr.cutoff).toFixed(1);
    grid += `<line class="pm-cutoff" x1="${cx}" y1="${top - 4}" x2="${cx}" y2="${bottom}"><title>Research cutoff ${esc(graph.scope.frame?.research_cutoff || '')}</title></line>`; }
  else { const wx = L.scale(L.coverageYear).toFixed(1);
    grid += `<line class="pm-wall" x1="${wx}" y1="${top - 4}" x2="${wx}" y2="${bottom}"><title>Coverage ends ${L.coverageYear}</title></line>`; }
  const tone = id => `tone-${Math.max(0, layerIndex(nodeById.get(id).layer))}`;
  const kindOf = e => BASE_KINDS.includes(e.relationship_kind) ? e.relationship_kind : 'extra-kind';
  /* Every drawn relationship touches the own entry. Its ends are spread along the own mark, in
     the order of the other ends, and each other end meets its mark at the nearest point in time,
     on the side facing the own mark: lines run mostly upright, as a comb rather than a knot. */
  const ownP = s.own ? L.placed.get(s.own) : null;
  const ends = s.edges.map(e => ({e, o: L.placed.get(e.source === s.own ? e.target : e.source)})).filter(r => ownP && r.o)
    .sort((a, b) => (a.o.x + a.o.w / 2) - (b.o.x + b.o.w / 2) || a.o.y - b.o.y);
  const edges = ends.map(({e, o}, i) => {
    const ax = ownP.x + (ownP.w * (i + 1)) / (ends.length + 1);
    const above = o.y < ownP.y;
    const bx = Math.min(Math.max(ax, o.x + 3), o.x + Math.max(o.w - 3, 3));
    const a = {x: ax, y: above ? ownP.y : ownP.y + ownP.h}, b = {x: bx, y: above ? o.y + o.h : o.y};
    const data = `data-a="${esc(e.source)}" data-b="${esc(e.target)}"`;
    return {line: `<path class="edge pm-edge ${kindOf(e)}" ${data} d="${esc(edgePath(a, b))}"><title>${esc(e.relationship)}</title></path>`,
      dot: `<circle class="pm-end k-${kindOf(e) === 'extra-kind' ? 'extra' : kindOf(e)}" ${data} cx="${b.x.toFixed(1)}" cy="${b.y.toFixed(1)}" r="2.6"/>`}; });
  const lines = edges.map(x => x.line).join(''), endDots = edges.map(x => x.dot).join('');
  const cls = id => ['pm-entry', tone(id), id === s.own ? 'own' : s.roster.has(id) ? `role-${s.roster.get(id)}` : 'linked'].join(' ');
  /* The faded tail stops short of the next mark (or its left-hand label) on the same row. */
  const tailEnd = b => { let end = L.scale(b.fadeTo);
    for (const o of L.bars) { if (o === b || o.y !== b.y || o.x < b.x + b.w - 0.5) continue;
      end = Math.min(end, (o.side === 'left' ? o.x - o.labelW - 9 : o.x) - 6); }
    return end; };
  const label = b => { const badge = b.badge ? `<tspan class="pm-badge${b.badge === ROLE_BADGE.critic ? ' critic' : ''}" dx="6">${esc(b.badge.toUpperCase())}</tspan>` : '';
    const x = b.side === 'above' ? b.labelX : b.side === 'right' ? b.x + b.w + 7 : b.side === 'left' ? b.x - 7 : b.x + 9;
    const y = b.side === 'above' ? b.y - 7 : b.y + b.h / 2 + 1;
    return `<text class="pm-label ${b.side}" x="${x.toFixed(1)}" y="${y.toFixed(1)}"${b.side === 'left' ? ' text-anchor="end"' : ''}>${esc(b.label)}${badge}</text>`; };
  const bars = L.bars.map(b => {
    if (b.chronology) return `<a class="${cls(b.node.id)} explicit" data-id="${esc(b.node.id)}" href="${esc(nodeHref(b.node.id))}" aria-label="${esc(pmDescribe(p, s, b.node.id))}">${chronologyShapes(b)}${label(b)}</a>`;
    const tailW = fr.open && b.open && b.fadeTo > b.drawEnd ? tailEnd(b) - L.scale(b.drawEnd) : 0;
    return `<a class="${cls(b.node.id)}" data-id="${esc(b.node.id)}" href="${esc(nodeHref(b.node.id))}" aria-label="${esc(pmDescribe(p, s, b.node.id))}">
      ${b.lead ? `<line class="pm-lead" x1="${b.lead.x.toFixed(1)}" y1="${(b.y + b.h / 2).toFixed(1)}" x2="${(b.lead.x + b.lead.w).toFixed(1)}" y2="${(b.y + b.h / 2).toFixed(1)}"><title>Earlier roots, undated</title></line>` : ''}
      ${tailW > 1 ? `<rect class="pm-tail" x="${L.scale(b.drawEnd).toFixed(1)}" y="${b.y}" width="${tailW.toFixed(1)}" height="${b.h}"/>` : ''}
      <rect class="pm-bar${b.point ? ' point' : ''}" x="${b.x.toFixed(1)}" y="${b.y}" width="${b.w.toFixed(1)}" height="${b.h}" rx="2.5"${b.span.precision === 'decade' && !b.point ? ' fill-opacity="0.72"' : ''}/>
      ${!fr.open && b.open && b.w > 30 ? `<rect class="pm-fade" x="${(b.x + b.w - 20).toFixed(1)}" y="${b.y - 1}" width="21" height="${b.h + 2}"/>` : ''}
      ${label(b)}</a>`; }).join('');
  const chips = L.chips.map(c => `<a class="${cls(c.node.id)} pm-chip" data-id="${esc(c.node.id)}" href="${esc(nodeHref(c.node.id))}" aria-label="${esc(pmDescribe(p, s, c.node.id))} No date span stated.">
      <rect class="pm-bar" x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="9"/><text class="pm-label inside" x="${c.x + 9}" y="${c.y + c.h / 2 + 1}">${esc(c.label)}${c.badge ? `<tspan class="pm-badge" dx="6">${esc(c.badge.toUpperCase())}</tspan>` : ''}</text></a>`).join('');
  const captions = L.captions.map(c => `<text class="pm-caption" x="${c.x}" y="${c.y}">${esc(c.text)}</text>`).join('');
  return `<svg class="pm-svg" width="${L.inner}" height="${L.height}" viewBox="0 0 ${L.inner} ${L.height}" role="group"
      aria-label="Where ${esc(p.label)} sits: ${s.ids.size} entr${s.ids.size === 1 ? 'y' : 'ies'} on a time axis from ${L.minYear} to ${fr.open ? 'the research cutoff' : L.coverageYear}. Each mark is a link to the entry; the same entries are listed below.">
    <defs><linearGradient id="pm-fade" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fbfaf4" stop-opacity="0"/><stop offset="1" stop-color="#fbfaf4" stop-opacity=".92"/></linearGradient></defs>
    <g class="pm-chrome">${grid}<line class="pm-axis" x1="${L.x0}" y1="${top}" x2="${L.x1}" y2="${top}"/>${captions}</g>
    <g class="pm-edges">${lines}</g>${chips}${bars}<g class="pm-ends">${endDots}</g></svg>`;
}
function drawPersonMap() {
  const box = document.querySelector('.pm-scroll');
  if (!box || !state.person) return;
  const p = personById.get(box.dataset.person);
  personMapWidth = box.clientWidth || 900;
  const L = {...personMapLayout(graph, p.id, personMapWidth), subset: pmSubset(p.id)};
  box.innerHTML = personMapSvg(L, p);
  box.removeAttribute('aria-busy');
  const svg = box.querySelector('svg');
  const readout = document.querySelector('.pm-readout');
  const idle = readout.textContent;
  const light = id => {
    svg.classList.toggle('previewing', Boolean(id));
    for (const a of svg.querySelectorAll('.pm-entry')) a.classList.toggle('hi', a.dataset.id === id);
    for (const e of svg.querySelectorAll('.pm-edge, .pm-end')) {
      const on = Boolean(id) && (id === L.subset.own || e.dataset.a === id || e.dataset.b === id);
      e.classList.toggle('emph', on); e.classList.toggle('mute', Boolean(id) && !on);
    }
    readout.textContent = id ? pmDescribe(p, L.subset, id) : idle;
  };
  let current = null;
  const preview = target => { const id = target.closest?.('.pm-entry')?.dataset.id || null;
    if (id !== current) { current = id; light(id); } };
  svg.addEventListener('mouseover', e => preview(e.target));
  svg.addEventListener('mouseleave', () => { current = null; light(null); });
  svg.addEventListener('focusin', e => preview(e.target));
  svg.addEventListener('focusout', e => { if (!svg.contains(e.relatedTarget)) { current = null; light(null); } });
}

/* Approaches (strands) that name a person, including works added after the roster record. */
function strandContexts(p) {
  const hits = graph.nodes.flatMap(n => (n.strands || []).filter(s => s.person_ids?.includes(p.id)).map(strand => ({n, strand})));
  if (!hits.length) return '';
  return `<h3>Approaches that name them</h3><p class="fine-print">Named within an approach or work-based strand of an entry. A later work here does not re-date the roster record above.</p><div class="person-contexts">${hits.map(({n, strand}) => `<section class="person-affiliation tone-${layerIndex(n.layer)}">${layerTag(n)}<h3><a href="${esc(nodeHref(n.id))}">${esc(n.label)} →</a></h3><p class="strand-title">${esc(strand.title)}${strand.intervention_year ? ` <span class="strand-year">${esc(strand.intervention_year)}</span>` : ''}${reviewBadge(strand.review_status)}</p>
    ${strand.works ? `<p class="person-work">${esc(strand.works)}</p>` : ''}${strandCredits(strand)}${strand.claim_ids?.length ? `<details class="strand-claims"><summary>Exact claims · ${strand.claim_ids.length}</summary>${claimCards(strand.claim_ids)}</details>` : ''}</section>`).join('')}</div>`;
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
const focusHref = id => href({focus: id, node: '', person: '', edge: '', page: 0, section: '', view: 'map',
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
    <details class="mark-guide" ${disclosureOpen()}><summary>Reading the timeline</summary><div class="lg"><strong>The mark</strong>
      ${explicitChronology() ? `<span class="swatch chron-point">selected contribution</span>
      <span class="swatch chron-context">context or earlier work</span>
      <span class="swatch chron-reception">edition or reception</span>
      <span class="swatch chron-connector">extent of the selection</span>
      <span class="swatch chron-interval-key">sourced historical interval</span>
      <span class="swatch chron-review-key">editorial review year</span>
      <span class="swatch death-key">† death; later points hollow (posthumous)</span>
      <span class="swatch axis-note">pre-1900 compressed</span>
      <span class="swatch chron-before-key">◁ before 1750, at the axis edge</span>` : `<span class="swatch precise">years the label names</span>
      <span class="swatch lead">earlier roots, undated</span>
      <span class="swatch posthumous">† death · hatched = posthumous reception</span>
      <span class="swatch point">a single dated year</span>
      <span class="swatch fuzzy">decade precision</span>
      ${openFrame() ? `<span class="swatch open unreviewed">solid to the year reviewed · faded where later work is not yet surveyed</span>
      <span class="swatch axis-note">pre-1900 compressed</span>${shownGraph().nodes.some(n => interventionsOf(n).length) ? '<span class="swatch intervention">◆ selected later intervention</span>' : ''}`
      : `<span class="swatch open">continues past the coverage limit</span>
      <span class="swatch axis-note">pre-1900 compressed</span>${activeExtension() ? '<span class="swatch intervention">◆ selected intervention after the limit</span>' : ''}`}`}</div></details>
    <div class="lg right"><strong>View</strong>
      <a class="view-link" role="button" href="${esc(href({view: 'map'}))}"
        aria-pressed="${state.view !== 'list'}">Timeline</a>
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
  const earlyRoom = view.scale(view.breakYear) - view.scale(view.minYear);
  const earlyStep = explicitChronology() ? ([25, 50, 100, 200, 500, 1000].find(step =>
    step >= (view.breakYear - view.minYear) / Math.max(1, Math.floor(earlyRoom / 42))) || 1000) : 25;
  for (let yr = Math.ceil(view.minYear / earlyStep) * earlyStep; yr < view.breakYear; yr += earlyStep) tick(yr, true);
  for (let yr = view.breakYear; yr <= view.maxYear; yr += 10) tick(yr, yr % 20 === 0);
  const fr = view.frame, bx = view.scale(view.breakYear);
  const wx = fr.open ? null : view.scale(view.coverageYear);
  if (fr.open) {
    /* Open frame: no wall. The research cutoff is a date of reading, not an ending. */
    const cx = view.scale(fr.cutoff);
    grid += `<line class="frame-cutoff" x1="${cx}" y1="${view.axisTop + 16}" x2="${cx}" y2="${bottom}"/>
      <text class="cutoff-label" x="${cx - 4}" y="${view.axisTop + 13}" text-anchor="end">research cutoff ${esc(graph.scope.frame?.research_cutoff || '')}</text>
      <line class="scale-break" x1="${bx}" y1="${view.axisTop + 16}" x2="${bx}" y2="${bottom}"/>`;
  } else {
    grid += `<line class="coverage-wall" x1="${wx}" y1="${view.axisTop + 16}" x2="${wx}" y2="${bottom}"/>
    <text class="coverage-label" x="${wx - 6}" y="${bottom - 6}" text-anchor="end"
      >curated coverage ends ${view.coverageYear}</text>
    <line class="scale-break" x1="${bx}" y1="${view.axisTop + 16}" x2="${bx}" y2="${bottom}"/>`;
  }
  /* The extension zone: only the axis is stretched; marks keep their own coverage, and the
     selected later interventions are drawn as points. The cutoff is a research date, not an end. */
  const ext = fr.open ? null : view.extension;
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
      href="${esc(focusHref(p.node.id))}"><rect class="ghost${p.span?.chronological ? ' chron-ghost' : ''}" x="${p.x}" y="${p.y}"
      width="${p.w}" height="${p.h}" rx="2"/><title>${esc(p.node.label)} · ${esc(
      p.node.date_label)}</title></a>`).join('');
  /* Open frame: the faded tail runs from the reviewed year to the frame end, but stops short of
     the next mark (or its left-hand label) sharing the row, so tails never run under other entries. */
  const tailEnd = p => {
    let end = view.scale(p.fadeTo);
    for (const o of view.bars) {
      if (o === p || o.y !== p.y || o.x < p.x + p.w - 0.5) continue;
      const start = o.side === 'left' ? o.x - o.label.length * 6.27 - 9 : o.x;
      end = Math.min(end, start - 6);
    }
    return end;
  };
  const tail = p => {
    if (!fr.open || !p.open || !(p.fadeTo > p.drawEnd)) return '';
    const x = view.scale(p.drawEnd), w = tailEnd(p) - x;
    return w > 1 ? `<rect class="unreviewed" x="${x}" y="${p.y}" width="${w}" height="${p.h}"><title>${
      p.reviewed !== null ? `Reviewed through ${p.drawEnd}; later work not yet surveyed` : 'Drawn to the research cutoff; later work is cited where checked'}</title></rect>` : '';
  };
  const bars = view.bars.map(p => {
    if (p.chronology) return `<a class="entry explicit ${cls(p)}" data-id="${esc(p.node.id)}" href="${esc(markHref(p))}"
      aria-label="${esc(p.node.label)}, ${esc(chronologyLabel(p.node))}.${heldNote(p)}">${chronologyShapes(p)}
      <text class="bar-label ${p.side}" y="${p.y + p.h / 2 + 1}"
        x="${p.side === 'right' ? p.x + p.w + 7 : p.side === 'left' ? p.x - 7 : p.x + 9}"
        ${p.side === 'left' ? 'text-anchor="end"' : ''}>${esc(p.label)}</text></a>`;
    const fuzzy = p.span.precision === 'decade';
    const xEnd = p.x + p.w;
    const tailHtml = tail(p);
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
      ${tailHtml}${p.open && p.w > 30 && !tailHtml ? `<rect class="bar-fade" x="${xEnd - 22}" y="${p.y - 1}" width="23" height="${p.h + 2}"/>` : ''}
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
  if (chronologyOf(n)) return '';
  const open = openFrame() && state.range !== '2000';
  const years = open ? interventionsOf(n).filter(y => y > (reviewedThrough(n) ?? 0)) : activeExtension() ? interventionsOf(n) : [];
  if (!years.length) return '';
  const c = n.extension_coverage;
  if (open) return `<p class="ext-note"><strong>After ${esc(reviewedThrough(n) ?? c.baseline_through ?? 2000)}.</strong> ${years.length} selected later intervention${years.length === 1 ? '' : 's'} (${esc(years.join(', '))}), drawn as ◆ on this row. ${c.status === 'release_candidate' ? 'Release candidate, not yet accepted. ' : ''}${c.field_review_complete ? '' : 'Selected interventions after the review year, not a survey.'} Open the entry to read the exact claims and their evidence.</p>`;
  return `<p class="ext-note"><strong>After ${esc(c.baseline_through || 2000)}.</strong> ${years.length} selected intervention${years.length === 1 ? '' : 's'} (${esc(years.join(', '))}), drawn as ◆ on this row. ${c.status === 'release_candidate' ? 'Release candidate, not yet accepted. ' : ''}${c.field_review_complete ? '' : 'The field is not reviewed through the cutoff.'} Open the entry to read the exact claims and their evidence.</p>`;
}
function fieldDateNote(n, span) {
  const chronology = chronologyOf(n);
  if (chronology) {
    const selected = contributionSpan(n), review = reviewedThrough(n);
    return `<strong>${esc(chronology.label)}</strong><p>${esc(chronology.selection_note)}</p>
      <p>${selected ? `The selected contribution dates ${selected.start === selected.end ? `include ${selected.start}` : `run from ${selected.start} to ${selected.end}`}. ` : ''}
      Points date works or events. The thin dotted connector shows the extent of the selection; it does not assert continuous activity or influence. Earlier context, editions and reception have separate markers; work dated before 1750 points off the axis’s left edge.</p>
      ${review !== null ? `<p class="chronology-coverage"><strong>Editorial coverage: reviewed through ${review}.</strong> ${esc(n.coverage?.basis || '')} The small outlined square records this survey limit separately from the dated contributions.</p>` : ''}
      ${(chronology.intervals || []).map(i => `<p><strong>${esc(i.subject)}:</strong> ${esc(dateText(i.start))}${i.end ? `–${esc(dateText(i.end))}; ${esc(i.end_meaning.replace(/_/g, ' '))}` : '; ending unestablished'}. ${esc(i.support)}</p>`).join('')}
      ${chronologyDetails(n)}`;
  }
  if (!span) return `<strong>No span stated.</strong> <code>${esc(chronologyLabel(n))}</code> names
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
  if (openFrame() && isOpenSpan(n, span)) {
    const reviewed = reviewedThrough(n);
    if (reviewed !== null) {
      const drawn = solidEnd(n, span);
      opening = periodical
        ? `<strong>First issue ${span.start}</strong>, drawn to ${drawn}.`
        : span.openStart ? `Drawn solid from ${span.start} to ${drawn}.`
        : `<strong>From ${span.start}</strong>${precision}, drawn to ${drawn}.`;
      ending = `This entry is <strong>reviewed through ${reviewed}</strong>. The faded part runs to the research
        cutoff (${esc(graph.scope.frame?.research_cutoff || '')}): later work is not yet surveyed here, not absent.`;
    } else {
      opening = periodical
        ? `<strong>First issue ${span.start}</strong>, drawn to the research cutoff; later work is cited where checked.`
        : span.openStart ? `Drawn solid from ${span.start} to the research cutoff; later work is cited where checked.`
        : `<strong>From ${span.start}</strong>${precision}, drawn to the research cutoff; later work is cited where checked.`;
      ending = '';
    }
  } else if (span.endKind === 'coverage_limit') {
    opening = periodical
      ? `<strong>First issue ${span.start}</strong>, drawn to ${wall}.`
      : span.openStart ? `Drawn solid from ${span.start} to ${wall}.`
      : `<strong>From ${span.start}</strong>${precision}, drawn to ${wall}.`;
    ending = `${wall} is the limit of this map’s coverage, not an ending: the mark fades into
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
    : `Read from <code>${esc(chronologyLabel(n))}</code> by the site, not curated as numbers. The mark
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
  const posthumous = !chronologyOf(n) && life.death && span && life.death < (openFrame()
    ? (isOpenSpan(n, span) ? solidEnd(n, span) : span.end)
    : span.endKind === 'coverage_limit' ? (span.coverage ?? graph.scope.main_period[1]) : span.end);
  return `<p class="life">${esc(parts.join(' · '))}${life.qid ? ` · <a href="https://www.wikidata.org/wiki/${esc(life.qid)}"
      target="_blank" rel="noopener noreferrer">Wikidata ${esc(life.qid)}</a>` : ''}${
      life.retrieved ? ` <span class="prov">retrieved ${esc(life.retrieved)}</span>` : ''}${
      posthumous ? `<br><span class="posthumous-note">The hatched part of the mark, after ${life.death},
      is reception of the work after the author’s death.</span>` : ''}</p>`;
}

function chronologyDetails(n) {
  const c = chronologyOf(n);
  if (!c) return '';
  const source = ref => {
    const journal = ref.startsWith('journal:');
    const s = (journal ? journalSourceById : sourceById).get(ref.slice(journal ? 8 : 6));
    if (!s) return '';
    const title = s.citation || s.title;
    return `<li>${/^https?:\/\//.test(s.url || '') ? `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(title)} ↗</a>` : esc(title)}${s.verification?.note || s.note || s.scope_note ? `<p>${esc(s.verification?.note || s.note || s.scope_note)}</p>` : ''}</li>`;
  };
  const groups = {contributions: 'Selected contributions', context: 'Earlier works & context', editions: 'Editions & translations', reception: 'Reception & retrospective discussion'};
  const events = chronologyEvents(n);
  return `<details class="chronology-details"><summary>Dated contributions & evidence · ${events.length}</summary>
    <p>Dates distinguish publication, delivery, writing, editions and reception. Open an event for its source and date meaning.</p>${Object.entries(groups).map(([track, title]) => {
      const rows = events.filter(e => e.track === track);
      return rows.length ? `<section class="chronology-track"><h4>${title}</h4><ol>${rows.map(e => `<li data-chronology-event="${esc(e.id)}"><strong>${esc(dateText(e.date))}</strong> · ${esc(e.label)}
        <span class="chronology-kind">${esc(e.kind.replace(/_/g, ' '))}</span><details><summary>Evidence & date meaning</summary><p>${esc(e.support)}</p><ul class="chronology-sources">${e.source_ids.map(source).join('')}</ul></details></li>`).join('')}</ol></section>` : '';
    }).join('')}<p class="chronology-limits">${esc(c.continuation.basis)}</p></details>`;
}

/* One relationship, with its evidence and references one click away. */
function relRow(r) {
  const e = r.edge, kind = e.relationship_kind;
  const other = fieldNodeById.get(r.other);
  const tone = BASE_KINDS.includes(kind) ? kind : 'extra-kind';
  const atlasEdge = atlasEdgeIds.has(e.id);
  const sources = atlasEdge ? sourceList(e.source_ids) : sourceList(e.source_ids, journalSourceById);
  /* An open interval (end null, open frame) reads "from 1972 onward", not as a single year. */
  const scope = e.temporal_scope?.start ? `<p class="fine-print">${e.temporal_scope.end === null
    ? `Dated from ${e.temporal_scope.start} onward` : `Dated ${e.temporal_scope.start}`}${
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
    ${explicitChronology() ? `<p><strong>Points date selected works and events.</strong> Dotted connectors show the extent of a selection, not continuous activity or influence. Hollow markers distinguish earlier context; diamonds distinguish editions and reception. Bars are reserved for sourced historical intervals, with title changes distinguished from cessation.</p>
    <p>The small outlined square marks the entry's editorial review year. Later selected works can appear beyond it without implying that the intervening period has been surveyed. The research cutoff is a date of reading, not a historical ending. Select an entry to inspect its dates, sources and recorded connections.</p>` : openFrame() ? `<p>A mark runs across <strong>the years an entry’s date label names</strong>. A left cap is
    the earliest dated year; a thin lead-in from the left edge means the label states earlier,
    undated roots. A mark is solid through the year its entry has been reviewed and faded after it, to the research cutoff.
    Fields are being extended one at a time; a faded tail means later work is not yet surveyed, not that the field stopped.
    Ticks mark other years the label names; ◆ marks a selected later intervention. Open a relationship to read its evidence.</p>`
    : `<p>A mark runs across <strong>the years an entry’s date label names</strong>. A left cap is
    the earliest dated year; a thin lead-in from the left edge means the label states earlier,
    undated roots. A bar that fades into the dashed wall at ${graph.scope.main_period[1]} continues beyond what this project
    covers: the wall is a coverage limit, not an ending. Ticks mark other years the label names.
    Open a relationship to read its evidence.</p>`}${activeExtension() ? `<p>Beyond the wall, ◆ marks <strong>selected interventions after ${graph.scope.main_period[1]}</strong> for the ${activeExtension().covered} entries a partial release covers. Nothing else is extended; the research cutoff is a date of reading, not an ending.</p>` : ''}
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
  return `<div class="selection-actions">${chartReturn('timeline-map', 'Back to timeline')}${state.focus && !hoverId ? `<p class="panel-release">${releaseLink()}</p>` : ''}</div>
    ${p ? `<p class="path-strip">${seq >= 0 ? `Entry ${seq + 1} of ${p.node_ids.length} in` : 'Outside'}
      the pathway <a href="${esc(href({focus: ''}))}">${esc(p.title)}</a>.</p>` : ''}
    <p class="eyebrow">${esc(n.entry_type || 'Entry')}</p>
    <h2 id="field-title" tabindex="-1">${esc(n.label)}</h2>
    <p class="meta">${esc(chronologyLabel(n) || 'No date label')} · ${esc(fieldTitle(n.layer))}</p>
    ${atlas ? `<p class="panel-more"><a class="button-link" href="${esc(connectedNodeHref(id, ''))}">Follow all connections →</a></p>` : ''}
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
    ${atlas ? `<p class="panel-more"><a class="text-link" href="${esc(nodeHref(id))}">Full entry, people &amp; references →</a></p>` : `<p class="panel-more fine-print">
      A catalogued periodical. Its timeline links are listed above; it has no entry page.</p>`}`;
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
  const fr = frameOf(graph);
  const hi = fr.open ? fr.end
    : Math.max(graph.scope?.main_period?.[1] ?? 2000, ...rows.filter(r => r.span).map(r => r.span.end));
  const pct = yr => Math.max(0, Math.min(100, (yr - lo) / (hi - lo) * 100));
  const mini = (span, n) => {
    if (!span) return '';
    if (chronologyOf(n)) {
      const selected = contributionSpan(n);
      return `<span class="mini chronology-mini" aria-hidden="true">${selected && selected.end > selected.start ? `<i class="selection" style="left:${pct(selected.start)}%;width:${pct(selected.end) - pct(selected.start)}%"></i>` : ''}${chronologyEvents(n).map(e => `<b class="track-${e.track}" style="left:${pct((e.bounds[0] + e.bounds[1]) / 2)}%"></b>`).join('')}</span>`;
    }
    const open = fr.open ? isOpenSpan(n, span) : span.endKind === 'coverage_limit';
    const a = pct(span.start), b = Math.max(a + 1.5, pct(open ? (fr.open ? solidEnd(n, span) : (span.coverage ?? hi)) : span.end));
    return `<span class="mini" aria-hidden="true">${span.openStart ? `<i class="lead" style="left:0;width:${a}%"></i>` : ''}<i class="${open ? 'open' : ''}" style="left:${a}%;width:${b - a}%"></i></span>`;
  };
  const fam = activeFamily();
  return `<p class="fine-print">All ${rows.length} entries, in time order within each band.
      ${explicitChronology() ? 'Dates below give the selected contribution range; context and reception remain separately dated in each entry. These are not career or field boundaries.' : 'Dates describe selected works and developments, not a lifespan.'}${fam
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
        const selected = chronologyOf(n) ? contributionSpan(n) : span;
        return `<tr><td class="td-date">${esc(selected ? `${selected.start}${selected.end > selected.start
            ? `–${selected.end}` : ''}` : 'not stated')}${chronologyOf(n) ? '<small>selected</small>' : ''}${mini(span, n)}</td>
          <td><a href="${esc(focusHref(n.id))}">${esc(n.label)}</a>
            <span class="td-note">${esc(chronologyLabel(n))}</span></td>
          <td>${esc(n.entry_type || fieldTitle(n.layer))}</td>
          <td class="td-num">${rels}</td></tr>`;
      }).join('')}</tbody></table></details>`;
    }).join('');
}

/* ---------------- Landing: families, selected contributions beside the publication record ---------------- */
let landingWidth = 0;
const AXIS_LABEL = `${AXIS.start}–${AXIS.end}`;
const recordView = () => state.record || 'all';
/* Family links from the landing open the timeline explicitly, including on phones.
   Existing bare family URLs retain their approaches-and-people default. */
const familyHref = id => href({family: id, view: 'map'});
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
    ? `Only the ${block.established_journals} selected title contexts with qualifying research candidates in both 1970–74 and 2015–19. This holds the selected venues constant.`
    : view === 'deposited' ? 'All deposited journal-article records, including reviews and short items. This view exposes older metadata that lack page ranges; it does not establish research-article genre.'
    : view === 'reviews' ? 'Share of all book reviews in H-Net and Reviews in History in each five-year period.'
    : 'Share of research candidates in each five-year period, across the selected journals.';
  return `<div class="landing-page">
    <div class="timeline-entry"><div class="exploration-actions"><a class="button-link" href="#family=all&amp;view=map">Explore the timeline →</a>
      <a class="button-link" href="#tab=people">Explore the people circles →</a>
      <a class="button-link" href="#tab=dissertations">Explore dissertation reading →</a></div>
      <p>Trace arguments through time, meet historians across shared fields, or explore the scholarship doctoral historians draw on. Select an entry to examine its works, disagreements and evidence.</p></div>
    <div class="section-heading"><div><p class="eyebrow">FIND YOUR WAY IN</p>
      <h2>Twelve families of historical writing</h2></div></div>
    <p class="lede">Choose a family to explore its historians, fields and debates. Families overlap: a historian or an argument can belong in several conversations.</p>
    <nav class="landing-families" aria-label="Explore the twelve families">${block.families.map(f=>`<a href="${esc(familyHref(f.id))}">${esc(f.label)} <span aria-hidden="true">→</span></a>`).join('')}</nav>
    <section class="landing-reading"><div><p class="eyebrow">WHAT DO HISTORIANS READ?</p><h3>Follow the dissertation record</h3><p>Explore how Cronon, Worster, Stoler, Trouillot and Thompson are cited, which works appear alongside them, and how the sampled reading differs across periods and regions.</p></div><a class="button-link" href="#tab=dissertations">Start exploring →</a></section>
    <div class="section-heading"><div><p class="eyebrow">COMPARE WITH THE PUBLICATION RECORD · ${AXIS_LABEL}</p><h3>Selected contributions and published scholarship</h3></div></div>
    <p class="lede"><b class="atlas">Orange</b>: selected contribution dates for the curated schools and fields. <b class="record">Green</b>: each family’s share of this publication record. ◂ marks entries dated before 1880.</p>
    <p class="eyebrow">THE GAP IN ONE LINE</p>
    <div class="strip"><span>Share of curated entries</span>${stripBar(strip.atlas, 'atlas')}
      <span>Share of research candidates, ${strip.period[0]}–${strip.period[1]}</span>${stripBar(strip.record, 'record', strip.unclaimed)}</div>
    <div class="landing-controls"><p class="eyebrow">OVER TIME</p><div class="view-links" role="group" aria-label="Record view">${toggles}</div></div>
    <p class="fine-print">${esc(viewNote)} ${esc(block.note)} Blank bars can reflect selection limits, missing deposits, incomplete pagination or mapping gaps; they do not date a field’s beginning.</p>
    <div class="landing-rows" aria-busy="true"></div>
    ${cardsHtml({block, graph, view, href: familyHref})}
    <details class="landing-table"><summary>Table of these numbers</summary>${tableHtml({block, graph, view})}</details>
    <p class="fine-print">Curated entries are placed at their earliest selected contribution date. This is an editorial selection, not a field origin or a measure of influence. Record counts use journal-level tags. Research candidates are journal-article records of at least ten pages; the Journal of Digital History uses article numbers and its journal-article records are included without a page threshold. These filters do not establish article genre. ${openFrame() ? 'The project has no closing date; its entries are reviewed through 2000 unless marked otherwise, so later publication bars can run ahead of the editorial reading.' : 'This archived selection ends in 2000; later publication bars have no matching entries.'} Periods with fewer than ${MIN_BIN_TOTAL} items are omitted. ${esc(evidence.caveats.join(' ').replaceAll('atlas entries', 'curated entries'))}
      <a href="${esc(href({family: 'all', view: 'map'}))}">All entries on one axis →</a></p>
    ${evidence.sensitivity ? `<details class="landing-audit"><summary>How sensitive is this comparison?</summary><p class="fine-print">${esc(evidence.sensitivity.note)}</p><p class="fine-print">${esc(evidence.sensitivity.pagination_note)}</p></details>` : ''}
  </div>`;
}
function drawLanding() {
  const box = document.querySelector('.landing-rows');
  if (!box) return;
  landingWidth = box.clientWidth || 1000;
  /* Rows are native SVG links (Enter, middle-click and no-JS all work), so no handlers here. */
  box.innerHTML = rowsSvg({block: evidence.families, graph, view: recordView(), width: landingWidth, href: familyHref,
    closed: !openFrame()});
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
    lacks.length ? `In the record but not in the curated entries: ${lacks.join(', ')}.` : ''].filter(Boolean).join(' ');
  return `<nav class="family-crumbs" aria-label="Families"><a href="${esc(href(OVERVIEW_PATCH))}">← All families</a>
      <a href="${esc(href({family: 'all', focus: '', path: '', view: 'map'}))}">All entries on one axis</a></nav>
    ${note ? `<p class="family-note">${esc(note)}</p>` : ''}
    <p class="fine-print family-caveat">Record fields come from journal-level tags and subject headings; counts measure participation, not influence.</p>`;
}

function familyNavigation(exploring) {
  return `<nav class="family-views" aria-label="Family view">${[
    ['map', 'Timeline'], ['approaches', 'Approaches & people'], ['list', 'List']
  ].map(([view, label]) => `<a href="${esc(href({view, focus: '', page: 0}))}" ${
    (exploring ? view === 'approaches' : state.view === view) ? 'aria-current="page"' : ''}>${label}</a>`).join('')}
    <a href="${esc(href({tab: 'people', view: '', focus: '', path: '', hold: '', letter: '', page: 0}))}">People circles</a></nav>`;
}

function familyExplorer(fam) {
  const allowed = new Set(filterNodes(graph.nodes, {...state, query: ''}, graph.people).map(n => n.id));
  const content = familyContent(graph, fam, state.query, allowed);
  const {fields, approaches, people, connections, approachCount, peopleCount} = content;
  const grouped = fields.map(field => {
    const rows = approaches.filter(r => r.field.id === field.id);
    if (!rows.length) return '';
    return `<section class="family-approach-group" aria-label="${esc(field.label)} approaches">
      <div class="family-group-heading"><h3>${esc(field.label)}</h3><a href="${esc(nodeHref(field.id))}">Full field entry →</a></div>
      <div class="family-approach-grid">${rows.map(({strand:s}) => `<article class="family-approach" data-approach="${esc(field.id + '/' + s.id)}">
        <h4>${esc(s.title)}${s.intervention_year ? ` <span class="strand-year">${esc(s.intervention_year)}</span>` : ''}</h4>
        <p>${esc(s.focus)}</p><p class="person-work">${esc(s.works)}</p>
        <ul class="family-participants">${(s.person_ids || []).map(id => `<li><a href="${esc(personHref(id))}">${esc(personById.get(id)?.label || id)}</a></li>`).join('')}</ul>
        ${strandCredits(s)}${s.claim_ids?.length ? `<details class="strand-claims"><summary>Exact claims · ${s.claim_ids.length}</summary>${claimCards(s.claim_ids)}</details>` : ''}
        <details class="family-approach-sources"><summary>Sources & reading limits</summary>${sourceList(s.source_ids)}</details>
      </article>`).join('')}</div></section>`;
  }).join('');
  return `<div class="field-page family-explorer">${familyHeading(fam)}
    <div class="section-heading"><div><p class="eyebrow">ONE FAMILY OF HISTORICAL WRITING</p><h2>${esc(fam.label)}</h2></div>
      <p class="family-content-summary">${approachCount} approaches · ${peopleCount} historians & contributors · ${fields.length} fields</p></div>
    ${familyNavigation(true)}<p class="family-introduction">Explore the practices, works and collaborations within these fields. People appear through their recorded contributions; open a source to see what supports the selection.</p>
    ${state.query ? `<p class="family-results">${approaches.length} matching approaches · ${people.length} matching people <a href="${esc(href({query: ''}))}">Clear search</a></p>` : ''}
    <div class="family-explorer-split"><div>${grouped || '<p class="empty">No approaches match these filters.</p>'}</div>
      <aside class="family-people" aria-label="People in this family"><h3>Historians & contributors <span>${people.length}</span></h3>
        <p class="fine-print">Shared people appear once, with their roles in each field.</p><ul>${people.map(({person, contexts}) => `<li data-person="${esc(person.id)}"><a href="${esc(personHref(person.id))}">${esc(person.label)}</a>
          ${contexts.map(({field, row}) => `<p class="fine-print">${esc(PERSON_ROLES[row.role] || row.role)} · ${esc(field.label)}</p>`).join('')}</li>`).join('')}</ul></aside></div>
    <section class="family-boundaries" aria-label="Connections with related fields"><h3>Connections with related fields</h3>
      <div class="family-connection-grid">${connections.map(({edge:e, source, target}) => `<article class="family-boundary-card" data-edge="${esc(e.id)}">
        <p class="eyebrow">${esc(kindChip(e.relationship_kind))}</p><h4>${esc(source.label)} ${hasArrow(e) ? '→' : '·'} ${esc(target.label)}</h4>
        <p>${esc(e.relationship)}</p><a href="${esc(href({edge: e.id, node: e.source, person: '', focus: '', query: '', section: 'connections', page: 0}))}">Read the relationship & evidence →</a>
      </article>`).join('') || '<p>No related-field relationships recorded for this selection.</p>'}</div></section></div>`;
}

function fieldPage() {
  const fam = activeFamily();
  if (fam && !state.focus && state.view === 'approaches') return familyExplorer(fam);
  const counts = fieldView(1200);   /* counts do not depend on width; the SVG is drawn after measuring */
  const body = state.view === 'list' ? `<div class="field-listing">${fieldList()}</div>`
    : '<div class="field-scroll" id="timeline-map" tabindex="0" role="region" aria-label="Interactive timeline" aria-busy="true"></div>';
  return `<div class="field-page" data-selected="${Boolean(state.focus || state.path)}">
    ${fam ? familyHeading(fam) : ''}
    <div class="section-heading"><div><p class="eyebrow">${fam ? '01 / ONE FAMILY OF HISTORICAL WRITING' : '01 / THE WHOLE FIELD'}</p>
      <h2>${fam ? esc(fam.label) : 'Historiography on one time axis'}</h2></div>
      <p class="field-summary">${counts.datedCount} placed in time${counts.undatedCount
        ? ` · ${counts.undatedCount} without a stated span` : ''} ·
        ${fieldEdges(shownGraph()).length} relationships${openFrame()
          ? ` · ${shownGraph().nodes.filter(n => n.entry_kind === 'group' && reviewedThrough(n) === 2000).length} entries reviewed through 2000`
          : activeExtension() ? ` · ${activeExtension().covered} entries with selected interventions after ${graph.scope.main_period[1]}` : ''}</p></div>
    ${fam ? familyNavigation(false) : ''}${fieldLegend()}
    ${state.view !== 'list' ? '<p class="touch-only chart-hint">Scroll inside the timeline and tap an entry for its connections. Use List for a text view.</p>' : ''}
    <div class="field-split">${body}
      <aside class="field-panel">${fieldPanel()}</aside></div>
    <p class="fine-print">${state.view === 'list'
      ? 'Text view. Switch to Timeline for the visual arrangement.'
      : 'A text list of the same entries is available under View · List.'}
      ${explicitChronology() ? 'Points date selected works and events. Dotted lines connect the selection; they are not careers or field lifespans. Editorial coverage is shown separately.' : 'Bars follow the years each date label names; they are editorial readings, not verified chronology or measures of influence.'}</p>
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
  svg.addEventListener('mouseover', e => { if (canHover()) preview(e.target); });
  svg.addEventListener('mouseleave', clear);
  /* Keyboard users get the same preview as hover. */
  svg.addEventListener('focusin', e => preview(e.target));
  svg.addEventListener('focusout', e => { if (!svg.contains(e.relatedTarget)) clear(); });
  svg.addEventListener('mouseover', e => { if (canHover()) emphasise(svg, e.target); });
  /* Clicking empty chart space lets go of the held entry. */
  svg.addEventListener('click', e => {
    if (state.focus && !e.target.closest('a')) change({focus: ''});
  });
  if (state.focus && state.focus !== scrolledFocus) {
    scrolledFocus = state.focus;
    const held = svg.querySelector('.entry.selected, .chip.selected');
    if (phone() && held) {
      const mark = held.getBoundingClientRect(), frame = box.getBoundingClientRect();
      box.scrollTop += mark.y - frame.y - box.clientHeight / 2;
      box.scrollLeft += mark.x + mark.width / 2 - frame.x - box.clientWidth / 2;
    } else held?.scrollIntoView({block: 'center',
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
let resizeTimer, wasPhone = phone();
function onResize() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (wasPhone !== phone()) {
      wasPhone = phone();
      $('filter-options').open = !wasPhone || Boolean(state.layer || state.period || state.hunt);
      render();
      return;
    }
    const box = document.querySelector('.field-scroll');
    if (box && Math.abs(box.clientWidth - fieldWidth) > 4) drawField();
    const company = document.querySelector('.company-chart');
    if (company && Math.abs(company.clientWidth - companyWidth) > 4) drawCompany();
    const pm = document.querySelector('.pm-scroll');
    if (pm && Math.abs(pm.clientWidth - personMapWidth) > 4) drawPersonMap();
    const rows = document.querySelector('.landing-rows');
    if (rows && Math.abs(rows.clientWidth - landingWidth) > 4) drawLanding();
    if (state.tab === 'dissertations') resizeReading($('dissertation-reading'));
    document.querySelectorAll('[data-reading-entry]').forEach(resizeReading);
    fitConnections();
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
  return `<div class="section-heading"><div><p class="eyebrow">01 / FIND YOUR WAY IN</p><h2>Four ways of approaching history.</h2></div><p>Open a layer, meet its historians,<br> then follow their connections.</p></div>
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
      ${[...new Set(['paradigms_and_limits', 'agency_and_structure', pathways.pathways.at(-2)?.id])].map(id => pathways.pathways.find(p => p.id === id)).filter(Boolean).map(p => {
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
    ${rows.length ? `<div class="entry-grid">${pageSlice(rows, 12).map(n => `<article class="entry-card tone-${layerIndex(n.layer)}">${layerTag(n)}<h3>${linkNode(n.id)}</h3><p class="date">${esc(chronologyLabel(n) || 'Date not recorded')}</p><p class="entry-excerpt">${esc(n.description)}</p>${huntTag(n)}<a class="entry-open" href="${esc(nodeHref(n.id))}" aria-label="Explore ${esc(n.label)}">${n.representative_people?.length ? rosterLabel(n) + ' →' : 'Explore connections →'}</a></article>`).join('')}</div>${pagination(rows.length, 12)}` : '<div class="empty"><h3>No entries match these filters.</h3><p>Try a shorter search or choose a broader layer or period.</p><a href="#">Clear all filters →</a></div>'}`;
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
function nodeDetail(n, readingContext=true) {
  const memberPaths = pathways.pathways.filter(p => p.node_ids.includes(n.id));
  return `<div class="reading-header"><p class="eyebrow">THE ENTRY</p><h2 id="detail-title" tabindex="-1">${esc(n.label)}</h2>${layerTag(n)}${huntTag(n)}<a class="hold-link" href="#focus=${esc(n.id)}">Hold in the field →</a></div>
    <p class="date">${esc(chronologyLabel(n) || 'Date not recorded')}</p><p class="period-note">${esc(periodLabel(n.period))}</p>
    ${n.entry_type ? `<p class="entry-type">${esc(n.entry_type)}</p>` : ''}<p class="description">${esc(n.description)}</p>${n.scope_note ? `<h3>Scope & distinctions</h3><p>${esc(n.scope_note)}</p>` : ''}${recordPanel(n)}${readingContext?`<div data-reading-entry="${esc(n.id)}"></div>`:''}<h3>Representative figures & works</h3><p>${esc(n.representative_figures_and_works || 'Not recorded.')}</p>
    ${chronologyOf(n) ? `<section class="entry-chronology"><h3>Dates & historical meaning</h3><p>${esc(n.chronology.selection_note)}</p>${reviewedThrough(n) !== null ? `<p class="chronology-coverage">Editorial coverage: <strong>reviewed through ${reviewedThrough(n)}</strong>. Later selected contributions do not establish a survey of the intervening period.</p>` : ''}${chronologyDetails(n)}</section>` : ''}
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
    parts.push(e.reviews_total ? `<p><strong>${fmt(e.reviews_total)}</strong> reviews in networks and headings mapped to this field</p>${recordBars(e.reviews_by_5yr, 1990, 2025, 'reviews')}` : '<p>No mapped reviews in the selected collections for this field.</p>');
    parts.push(e.journal_items_total ? `<p><strong>${fmt(e.journal_items_total)}</strong> research candidates in journals tagged with this field</p>${recordBars(e.journal_items_by_5yr, 1900, 2025, 'research candidates')}` : '<p>No qualifying journal records in this collection for this field.</p>');
  } else if (e.status === 'cross_field_method_with_roots') {
    parts.push(`<p>Editorial method grouping, with proposed roots in ${e.roots_in.map(entryLink).join(' and ')}.</p>`);
  } else {
    parts.push(`<p>This entry has no direct theme mapping in the selected evidence. Editorial context: ${e.practised_within.map(entryLink).join(', ')}.</p>`);
  }
  if (e.coverage) parts.push(`<p class="fine-print">${esc(e.coverage.note)}${e.coverage.first_deposit ? ` Earliest collected record: ${e.coverage.first_deposit}; earliest qualifying candidate: ${e.coverage.first_candidate || 'none'}.` : ''}</p>`);
  if (e.method) {
    const m = e.method;
    const where = m.practitioner_items_in_method_venues
      ? `, ${Math.round(m.share_elsewhere * 100)}% of whose research appears outside method journals`
      : '; no matching method-venue credits were found';
    parts.push(`<p>Candidate title matches for the method: <strong>${fmt(m.title_hits)}</strong>${m.abstract_hits_not_in_title ? `; abstracts name it in ${fmt(m.abstract_hits_not_in_title)} more` : ''} (incomplete search proxies). ${fmt(m.practitioners)} candidate practitioners${where}. Venue credits, ORCID claims and curated rosters identify candidates; their other articles do not demonstrate use of the method.</p>`);
  }
  if (e.method?.identity_tiers_by_basis) {
    const tiers = Object.entries(e.method.identity_tiers_by_basis).map(([basis, counts]) => `${basis.replaceAll('_', ' ')}: ${fmt(counts.probable)} probable identity candidates`).join('; ');
    parts.push(`<p class="fine-print">${esc(tiers)}. Routes overlap; these counts must not be added together.</p>`);
  }
  if (e.invoked_in_reviews) {
    const most = (e.invoked_most_in || []).map(x => `${entryLink(x)} (×${x.lift})`).join(', ');
    parts.push(`<p>Invoked by name in <strong>${fmt(e.invoked_in_reviews)}</strong> reviews${most ? `; most over-represented in ${most}` : ''}.</p>`);
  }
  return `<details class="record-panel" open><summary>What the record shows <span>evidence layer</span></summary>${parts.join('')}
    <details class="record-about"><summary>About these counts</summary><p class="fine-print">${esc(evidence.coverage.reviews)}; ${esc(evidence.coverage.journals)}. ${evidence.caveats.map(x => esc(x.replaceAll('atlas entries', 'curated entries'))).join(' ')}</p></details></details>`;
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
      <a class="flow-label edge-label ${lane} kind-${edgeKind(e)} ${e.id === state.edge ? 'selected' : ''}" data-edge="${e.id}" style="top:${(y + cy) / 2}px" href="${esc(href({edge:e.id}))}" aria-label="Inspect ${esc(KINDS[edgeKind(e)])} from ${esc(nodeById.get(e.source).label)} to ${esc(nodeById.get(e.target).label)}">${esc(KINDS[edgeKind(e)])} →</a>`;
  };
  return `<div class="graph-scroll"><div class="flow-graph focus-graph" style="height:${height}px" aria-label="Upstream entries on the left, selected entry in the centre, downstream entries on the right">
    <div class="flow-head incoming">INTO THIS ENTRY · ${incoming.length}</div><div class="flow-head middle">YOUR FOCUS</div><div class="flow-head outgoing">FROM THIS ENTRY · ${outgoing.length}</div>
    <svg class="connections" viewBox="0 0 1000 ${height}" preserveAspectRatio="none" aria-hidden="true"><defs>${['influence','contribution','critique'].map(k => `<marker id="arrow-${k}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" class="arrow-${k}"/></marker>`).join('')}</defs>
      ${incoming.map(({edge:e},i) => `<path class="connection incoming kind-${edgeKind(e)} ${state.edge === e.id ? 'active' : ''}" data-edge="${e.id}" d="M260 ${rowY(i,incoming.length)} C325 ${rowY(i,incoming.length)}, 325 ${cy}, 390 ${cy}" marker-end="url(#arrow-${edgeKind(e)})"/>`).join('')}
      ${outgoing.map(({edge:e},i) => `<path class="connection outgoing kind-${edgeKind(e)} ${state.edge === e.id ? 'active' : ''}" data-edge="${e.id}" d="M610 ${cy} C675 ${cy}, 675 ${rowY(i,outgoing.length)}, 740 ${rowY(i,outgoing.length)}" marker-end="url(#arrow-${edgeKind(e)})"/>`).join('')}
    </svg><div class="flow-focus focus-node tone-${layerIndex(n.layer)}" style="top:${cy}px"><h3>${esc(n.label)}</h3><span>${esc(layerLabel(n.layer))}</span></div>
    ${incoming.map((r,i)=>renderNeighbor(r,i,'incoming')).join('')}${outgoing.map((r,i)=>renderNeighbor(r,i,'outgoing')).join('')}
    ${!incoming.length ? '<p class="lane-empty incoming">No incoming directed relationships in this selection.</p>' : ''}${!outgoing.length ? '<p class="lane-empty outgoing">No outgoing directed relationships in this selection.</p>' : ''}
    </div></div><p class="flow-caption">All ${incoming.length + outgoing.length} directed relationships · arrows read left → right</p>
    ${lanes.associated.length ? `<section class="associated-links" aria-label="Comparisons and unclassified connections"><div class="section-heading"><div><p class="eyebrow">ALONGSIDE THIS ENTRY</p><h3>Comparisons & unclassified connections</h3></div><span>${others.length} relationships · all shown</span></div><p class="fine-print">These links have no established upstream or downstream direction. Their labels distinguish explicit comparisons from unclassified older connections.</p><div class="associated-grid">${others.map(({edge:e,node})=>`<article class="associated-card" data-edge="${e.id}"><a href="${esc(connectedNodeHref(node.id))}">${esc(node.label)}</a><a class="edge-label kind-${edgeKind(e)} ${state.edge === e.id ? 'selected' : ''}" href="${esc(href({edge:e.id}))}">${esc(KINDS[edgeKind(e)])} · inspect</a><p class="associated-claim">${esc(e.relationship)}</p></article>`).join('')}</div></section>` : ''}`;
}

function fitConnections() {
  const box = document.querySelector('.flow-graph');
  if (!box) return;
  const cards = [...box.querySelectorAll('.flow-neighbor')];
  const spacing = Math.max(155, ...cards.map(card => card.getBoundingClientRect().height + 20));
  const lanes = ['incoming', 'outgoing'].map(side => cards.filter(card => card.classList.contains(side)));
  const height = Math.max(320, Math.max(...lanes.map(lane => lane.length)) * spacing + 100), cy = height / 2;
  box.style.height = `${height}px`;
  box.querySelector('svg.connections').setAttribute('viewBox', `0 0 1000 ${height}`);
  box.querySelector('.flow-focus').style.top = `${cy}px`;
  const positions = new Map();
  for (const lane of lanes) lane.forEach((card, i) => {
    const y = cy + (i - (lane.length - 1) / 2) * spacing;
    card.style.top = `${y}px`; positions.set(card.dataset.edge, y);
  });
  for (const path of box.querySelectorAll('.connection[data-edge]')) {
    const y = positions.get(path.dataset.edge);
    path.setAttribute('d', path.classList.contains('incoming')
      ? `M260 ${y} C325 ${y}, 325 ${cy}, 390 ${cy}`
      : `M610 ${cy} C675 ${cy}, 675 ${y}, 740 ${y}`);
  }
  for (const label of box.querySelectorAll('.flow-label[data-edge]'))
    label.style.top = `${(positions.get(label.dataset.edge) + cy) / 2}px`;
}

function focused() {
  const n = nodeById.get(state.node);
  const allRows = neighborhood(graph, n.id);
  const rows = neighborhood(graph, n.id, state.kind, state.neighborLayer);
  const e = graph.edges.find(e => e.id === state.edge);
  const returnPatch = {node: '', person: '', edge: '', section: '', page: 0, kind: '', neighborLayer: ''};
  const returnLabel = state.pathway ? 'Back to pathway' : state.query || state.layer || state.period || state.hunt ? 'Back to entries' : 'Back to entries';
  return `${crumbs([`<a href="${esc(href(returnPatch))}">${returnLabel}</a>`, `<span aria-current="page">${esc(n.label)}</span>`])}
    ${schoolTabs(n)}${corePeople(n)}<div class="focus-layout"><section class="neighborhood" aria-labelledby="neighborhood-title"><div class="section-heading"><div><p class="eyebrow">03 / EXAMINE THE CONNECTIONS</p><h2 id="neighborhood-title">${phone() ? esc(n.label) : 'One entry, in conversation.'}</h2></div></div>
      <p class="context-note">All connections matching the selected filters are shown together. ${state.view === 'list' ? 'Open a relationship to read its explanation and evidence.' : 'Read incoming relationships on the left and outgoing relationships on the right; comparisons and unclassified links appear below. Select a relationship to read its evidence.'}</p>
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
  if (!p) return `${crumbs(['<span aria-current="page">Seminar pathways</span>'])}<div class="section-heading"><div><p class="eyebrow">FOLLOW A QUESTION</p><h2>Read across the conversations.</h2></div><p>${pathways.pathways.length} routes into historical explanation.</p></div><p class="context-note">${esc(pathways.interpretation_note)}</p><div class="pathway-grid">${pathways.pathways.map((p, i) => `<a class="pathway-card" href="#pathway=${p.id}"><span class="eyebrow">PATHWAY ${String(i + 1).padStart(2, '0')} · ${p.node_ids.length} ENTRIES</span><h3>${esc(p.title)}</h3><p>${esc(p.questions[0])}</p><span class="text-link">Begin reading →</span></a>`).join('')}</div>`;
  return `${crumbs(['<a href="#tab=pathways">Seminar pathways</a>', `<span aria-current="page">${esc(p.title)}</span>`])}
    <div class="section-heading"><div><p class="eyebrow">SEMINAR PATHWAY · ${p.node_ids.length} ENTRIES</p><h2>${esc(p.title)}</h2></div></div>
    <div class="pathway-layout"><section><p class="context-note">A suggested reading sequence, not a claim of influence. Open an entry to examine its connections, or <a href="#path=${esc(p.id)}">see these entries together on the field →</a></p><ol class="reading-sequence">${p.node_ids.map((id, i) => {
      const n = nodeById.get(id);
      return `<li><span class="sequence-number">${String(i + 1).padStart(2, '0')}</span><div>${layerTag(n)}<h3>${linkNode(id)}</h3><p>${esc(n.description)}</p></div></li>`;
    }).join('')}</ol></section><aside class="seminar-panel"><p class="eyebrow">BRING TO THE SEMINAR</p><h3>Questions to work with</h3><ol class="questions">${p.questions.map(q => `<li>${esc(q)}</li>`).join('')}</ol><div class="exercise"><p class="eyebrow">TRY THIS</p><p>${esc(p.exercise)}</p></div><details><summary>Compare explanations</summary><ul>${pathways.comparison_axes.map(a => `<li>${esc(a)}</li>`).join('')}</ul></details><p class="fine-print">Editorial teaching prompts, not quotations from Hunt.</p></aside></div>`;
}
function about() {
  const arch = production.scope?.archive, open = openFrame(production);
  const individualEntries = graph.nodes.filter(n => n.entry_kind === 'person').length;
  const withoutCritique = graph.nodes.filter(n => !graph.edges.some(e =>
    e.target === n.id && edgeKind(e) === 'critique' && hasArrow(e))).length;
  const profileExamples = ['carlo_ginzburg', 'quentin_skinner', 'w_e_b_du_bois', 'saidiya_hartman',
    'peter_burke', 'gerda_lerner', 'nancy_f_cott', 'john_hope_franklin']
    .filter(id => personById.has(id) && !personById.get(id).node_id).slice(0, 4)
    .map(id => `<a href="#person=${esc(id)}">${esc(personById.get(id).label)}</a>`);
  const traditionExamples = ['romila_thapar', 'cheikh_anta_diop', 'liang_qichao', 'gu_jiegang', 'ibn_khaldun', 'masao_maruyama']
    .filter(id => nodeById.has(id)).map(id => `<a href="#node=${esc(id)}">${esc(nodeById.get(id).label)}</a>`);
  return `${crumbs(['<span aria-current="page">About this project</span>'])}<article class="about"><p class="eyebrow">SCOPE & INTERPRETATION</p><h2>History as an ongoing conversation.</h2><p class="deck">This is a selective, contestable teaching interpretation of historiography, for MA students reading Lynn Hunt’s <cite>Writing History in the Global Era</cite> (2014).</p>
    <h3>Explore circles, time and connections</h3><p>Open Historians & contributors to explore the people circles: families of historical writing arranged around the historians they share. Open a family to see everyone its entries name. The circles show shared context; proximity and shared membership do not establish influence. Open the Timeline to trace entries through time, across the whole field or within a family. Select an entry and follow its connections, each with an explanation and evidence. The connections view shows all recorded incoming relationships on the left and outgoing relationships on the right; comparisons and unclassified connections appear separately below the flow. A full-text list offers the same relationships. Approaches & people opens each family’s works and contributors; a shared person can appear in several fields with different roles.</p>
    <h3>Nesting is navigation</h3><p>The four layers organize a mixture of people, fields, traditions, methods, and debates. They do not define a historical family tree. Entries can connect across layers; seminar pathways overlap them. Hunt’s four paradigms are an explicit teaching lens, not a universal hierarchy.</p>
    <p class="person-coverage"><strong>${individualEntries} standalone person entries among ${graph.people.length.toLocaleString()} indexed people.</strong> A standalone entry has its own dated contributions and recorded relationships on the timeline. Other people can still be opened through their profiles, with selected works, roster contexts and references${profileExamples.length ? ` — for example, ${profileExamples.join(', ')}` : ''}. Browse <a href="#tab=people">Historians & contributors</a> and use search or the surname letters to find them. A profile’s presence does not mean its scholarship has the same depth of coverage as a standalone entry; absence from the timeline does not mean absence from the project.</p>
    ${production.chronology_policy ? '<h3>Dates name different kinds of evidence</h3><p>Points identify selected works and events. Dotted connectors show the extent of the contribution selection, not continuous activity or influence. Context, editions and reception have separate markers. Bars represent named, sourced historical intervals; a journal title change is different from cessation. The small outlined square records editorial review coverage separately. Unknown bounds remain unknown, and a first selected work is not a field origin. Open Dated contributions & evidence for date meanings, sources and unresolved questions. The archive retains its original dating conventions.</p>' : ''}
    <h3>Periods are approximate groupings</h3><p>${arch || open ? `The project began as a 1920–2000 experiment and is now being extended field by field, with no closing date. Each entry says how far it has been reviewed; most are reviewed through 2000 so far, and some carry selected later interventions.${arch?.baseline_asset ? ` <a class="archive-link" href="${esc(href({range: '2000', tab: 'map'}))}">Open the original 1920–2000 experiment (archived revision ${esc(arch.baseline_revision || '1.121')}) →</a>` : ''}` : `Coverage is 1920–2000 with earlier roots. ${production.scope?.extension ? `A partial extension after 2000 exists as a ${esc((production.scope.extension.status || '').replace(/_/g, ' '))}: selected interventions in ${production.scope.extension.field_ids?.length || 0} entries, research cutoff ${esc(production.scope.extension.research_cutoff || '')}, latest selected publication ${esc(production.scope.extension.latest_selected_publication || '')}. It is not a survey of any field after 2000; the exact 2000 view remains available.` : 'An extension beyond 2000 has not yet been written.'}`} Periods describe emergence or expansion, not termination, while dated events distinguish publication, delivery, editions and reception. Entries without assigned periods remain available when you filter by a period. The timeline shows selected dated works and developments, rather than a complete chronology.</p>
    <h3>Explore what doctoral historians read</h3><p><a href="#tab=dissertations">Dissertation reading</a> follows cited people and works through sampled History PhD bibliographies and notes. Compare degree periods and regions, inspect companion literature and open example repository records. Environmental history, the archival turn, economic history and the capitalism debates have selected links into this record. Corpus coverage, extraction limits and bibliography name keys remain visible beside the comparisons.</p>
    <h3>Read the relationship before drawing a conclusion</h3><p>Influence, contribution, and classified critique have arrows. Critique runs from critic toward the position criticized; contribution does not imply founding a field. Comparisons have no direction. Older connections without direction metadata are visibly unclassified and have no arrow, including older records with a legacy critique category.</p>
    <h3>References have limits</h3><p>Bibliographic metadata checks establish the scope stated in their notes. A supporting page check is narrower than a full reading or a passage-level audit of every claim. Missing verification information means unrecorded. Some citations have no web link; relationship references are distinct from entry bibliographies.</p>
    <h3>What this beta does not yet cover</h3><p><strong>Critical exchanges remain unevenly mapped.</strong> ${withoutCritique} of ${graph.nodes.length} entries have no incoming relationship classified as critique. That counts recorded relationships, not the absence of scholarly objections.${nodeById.has('sciencewars') ? ' The <a href="#node=sciencewars&section=connections">Science Wars entry</a> includes the 1990s objections to Kuhn, Latour, SSK and STS, alongside replies and disagreements within science studies; those exchanges are already represented.' : ''}</p>
    <p><strong>Later scholarship is covered selectively.</strong> ${open ? 'Most fields retain a review baseline of 2000; later work is being added field by field.' : 'The original experiment covers 1920–2000, with earlier roots.'}${nodeById.has('archival_turn') ? ' The <a href="#node=archival_turn">archive as object</a>, <a href="#node=settler_colonialism">settler colonialism</a> and <a href="#node=environment">environmental history</a> entries have reviews through 2024; selected individual entries also include later works and reception. This is not comprehensive coverage of twenty-first-century historiography.' : ''}</p>
    <p><strong>Historiographical traditions beyond Europe and North America need fuller treatment.</strong> African history and Subaltern Studies include their own intellectual and institutional contexts.${nodeById.has('philip_huang') && nodeById.has('r_bin_wong') ? ' <a href="#node=philip_huang">Philip C. C. Huang</a> and <a href="#node=r_bin_wong">R. Bin Wong</a> have individual entries on Chinese history and its historiographical debates.' : ''}${traditionExamples.length ? ` Selected individual entries also examine the work of ${traditionExamples.join(', ')}.` : ''} These distinct projects across different centuries do not amount to systematic accounts of Chinese, Japanese, Korean or Islamic historiographical traditions. Fuller research into their methods, institutions and critical exchanges remains a priority.</p>
    <h3>The journals are a first pass</h3><p>Journals appear only where a specific founding,
    debate or sustained principal-venue claim has a source. A journal that publishes work in a
    field is not, on its own, a link. Over 1,700 further periodicals are catalogued but not
    drawn, and a journal's small number of connections reflects what this project covers, not the
    journal's importance.</p>
    <h3>A selective scope</h3><p>${esc(graph.scope.geographic_emphasis)} Paired entries can contain contrasting approaches; read their qualifications. The selection is not exhaustive and does not depict a sequence of superseded schools.</p>
    <p class="data-links"><a href="data/graph.json" download>Download curated graph</a><a href="data/pathways.json" download>Download seminar pathways</a></p><p class="fine-print">${graph.nodes.length} entries · ${graph.edges.length} relationships · ${graph.sources.length} bibliography records · ${pathways.pathways.length} pathways. Draft editorial revision ${esc(revision())}.</p></article>`;
}
function rangeControls() {
  const ext = production.scope?.extension;
  const toggle = $('range-toggle');
  const eyebrow = $('scope-eyebrow');
  /* Open frame: the exact-2000 view is an archive reached from About this project, not a toggle. */
  const arch = production.scope?.archive;
  if (arch || openFrame(production)) {
    toggle.hidden = true;
    if (state.range === '2000' && arch) {
      eyebrow.textContent = `${arch.baseline_period[0]}–${arch.baseline_period[1]} · ARCHIVED VIEW · REVISION ${arch.baseline_revision}`;
      $('edition-label').textContent = `Archive ${arch.baseline_revision} · the original 1920–2000 experiment`;
    } else {
      eyebrow.textContent = 'EARLIER ROOTS TO THE PRESENT · ENTRIES REVIEWED FIELD BY FIELD';
      $('edition-label').textContent = `Draft ${production.revision_history.at(-1).version}`;
    }
    return;
  }
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
  closeNavigation();
  rangeControls();
  const onField = state.tab === 'map' && !state.node && !state.person;
  /* Without the evidence asset the front door falls back to the full field view. */
  const onLanding = onField && state.overview && Boolean(evidence?.families);
  $('toolbar').hidden = !['map','people','browse'].includes(state.tab) || Boolean(state.node || state.person) || onLanding;
  $('search').value = state.query;
  $('layer-filter').value = state.layer;
  $('period-filter').value = state.period;
  $('hunt-filter').checked = state.hunt;
  const filters = Number(Boolean(state.layer)) + Number(Boolean(state.period)) + Number(state.hunt);
  $('filter-count').textContent = filters ? `· ${filters} active` : '';
  if (!$('filter-options').dataset.initialized) {
    $('filter-options').open = !phone() || filters > 0;
    $('filter-options').dataset.initialized = 'true';
  }
  const pathCount = document.querySelector('[data-tab="pathways"] span');
  if (pathCount) pathCount.textContent = pathways.pathways.length;
  document.querySelectorAll('[data-tab]').forEach(a => {
    const tab = state.person ? 'people' : state.pathway ? 'pathways' : state.node ? 'browse'
      : state.tab === 'map' ? (onLanding || state.view === 'approaches' ? 'field' : 'timeline') : state.tab;
    if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.body.dataset.view = onField ? 'field' : '';
  document.body.dataset.compact = onField ? '' : '1';
  document.body.dataset.landing = String(onLanding);
  $('workspace').innerHTML = state.person ? personPage()
    : state.node ? (nodeById.get(state.node).representative_people?.length && state.section !== 'connections' ? schoolPeople() : focused())
    : onLanding ? landingPage() : onField ? fieldPage()
    : state.tab === 'people' ? peopleDirectory()
    : state.tab === 'dissertations' ? '<div class="dissertation-reading" id="dissertation-reading"></div>'
    : state.tab === 'about' ? about()
    : state.tab === 'pathways' ? pathwayPage()
    : state.layer || state.query || state.period || state.hunt ? directory() : overview();
  const arch = production.scope?.archive;
  if (state.range === '2000' && arch && graph !== production) $('workspace').insertAdjacentHTML('afterbegin',
    `<div class="archive-banner" role="note"><strong>Archived view.</strong> The original 1920–2000 experiment (revision ${esc(arch.baseline_revision)}). <a href="${esc(href({range: ''}))}">Return to the current project →</a></div>`);
  if (onLanding) drawLanding(); else if (onField) wireField();
  if (state.tab === 'people' && !state.person && !state.node) { companyHover = null; drawCompany(); }
  if (state.person) drawPersonMap();
  fitConnections();
  if (state.tab === 'dissertations' && !state.node && !state.person) mountReading($('dissertation-reading'), state.source);
  if (state.range !== '2000') {
    document.querySelectorAll('[data-reading-person]').forEach(el => mountReadingContext(el, 'person', el.dataset.readingPerson));
    document.querySelectorAll('[data-reading-entry]').forEach(el => mountReadingContext(el, 'entry', el.dataset.readingEntry));
  }
  const pageLabel = state.person ? personById.get(state.person).label : state.node ? nodeById.get(state.node).label
    : state.pathway ? pathways.pathways.find(p => p.id === state.pathway).title
    : onLanding ? '' : onField ? activeFamily()?.label || 'Timeline'
    : state.tab === 'people' ? 'Historians & contributors' : state.tab === 'browse' ? 'Browse entries'
    : state.tab === 'pathways' ? 'Seminar pathways' : state.tab === 'dissertations' ? 'Dissertation reading' : 'About this project';
  document.title = [pageLabel, production.title].filter(Boolean).join(' · ');
  $('announcement').textContent = onLanding ? `Twelve families of historical writing: selected contributions beside the publication record. Record view: ${VIEWS[recordView()]}.`
    : state.tab === 'map' && !state.node && !state.person
    ? (state.focus ? `${fieldNodeById.get(state.focus).label} held in the field view.`
       : state.path ? `Pathway ${pathways.pathways.find(p => p.id === state.path).title} shown on the field.`
       : activeFamily() ? state.view === 'approaches'
         ? `${activeFamily().label}. Approaches, works and contributors.`
         : `${activeFamily().label}. ${shownIds().size} entries on a time axis.`
       : `Field view. ${fieldNodes(graph).length} entries on a time axis.`)
    : state.person ? personById.get(state.person).label : state.node ? `${nodeById.get(state.node).label}. ${state.section === 'connections' ? 'Connections view.' : rosterLabel(nodeById.get(state.node))}` : state.tab === 'people' ? `${filterPeople(graph,state).length} matching people.` : state.tab === 'map' ? `${filterNodes(graph.nodes,state,graph.people).length} matching entries.` : state.pathway ? pathways.pathways.find(p=>p.id===state.pathway).title : state.tab === 'pathways' ? 'Seminar pathways.' : state.tab === 'dissertations' ? 'Dissertation reading.' : 'About this project.';
  const resetLanes = {page:0};
  $('kind-filter')?.addEventListener('change', e => change({kind: e.target.value, ...resetLanes}));
  $('neighbor-layer')?.addEventListener('change', e => change({neighborLayer: e.target.value, ...resetLanes}));
  if (state.person) loadPeopleRecords();
  $('workspace').dataset.route = location.hash;
  $('workspace').setAttribute('aria-busy', 'false');
}
async function start() {
  try {
    const evidenceLoad = fetch('data/evidence.json', {signal: AbortSignal.timeout(8000)}).then(r => r.ok ? r.json() : null).catch(() => null);
    [production, pathwayAsset] = await Promise.all([isOverviewHash(location.hash) || isReadingHash(location.hash) ? 'data/overview.json' : 'data/graph.json', 'data/pathways.json'].map(async url => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${url} (${response.status})`);
      return response.json();
    }));
    adopt(production);
    window.addEventListener('resize', onResize);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && $('nav-more').getAttribute('aria-expanded') === 'true') {
        closeNavigation(); $('nav-more').focus(); e.stopImmediatePropagation(); return;
      }
      if (e.key === 'Escape' && state.focus && document.querySelector('svg.field')
          && !e.target.closest('input, select, textarea')) change({focus: ''});
    });
    $('nav-more').addEventListener('click', () => {
      const expanded = $('nav-more').getAttribute('aria-expanded') !== 'true';
      $('nav-more').setAttribute('aria-expanded', String(expanded));
      document.querySelector('.main-nav').classList.toggle('expanded', expanded);
    });
    document.addEventListener('pointerdown', e => {
      if (!e.target.closest('.main-nav')) closeNavigation();
    });
    $('edition-label').textContent = `Draft ${revision()}`;
    $('layer-filter').insertAdjacentHTML('beforeend', layerOptions(''));
    $('period-filter').insertAdjacentHTML('beforeend', graph.periods.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('') + '<option value="unassigned">No assigned period</option>');
    /* Parse once to learn which graph the route wants, adopt it, then parse against that graph. */
    const routeFor = async () => {
      const routeHash = location.hash;
      try {
        if (!isReadingHash(location.hash) && (!isOverviewHash(location.hash) || !evidence?.families)) await loadProduction();
      } catch (error) {
        if (routeHash !== location.hash) return routeFor();
        throw error;
      }
      const wanted = readRoute(location.hash, production, pathways).range;
      await ensureRange(wanted);
      if (routeHash !== location.hash) return routeFor();
      const next = readRoute(location.hash, graph, pathways);
      if (next.view !== 'approaches' && matchMedia('(max-width: 700px)').matches && !new URLSearchParams(location.hash.slice(1)).has('view')) next.view = 'list';
      return next;
    };
    evidence = await evidenceLoad;
    state = await routeFor();
    render();
    window.addEventListener('hashchange', async () => {
      const focusedId = document.activeElement?.id;
      const old = state;
      $('workspace').setAttribute('aria-busy', 'true');
      if (production.overview_only && !isOverviewHash(location.hash)) $('notice').textContent = 'Loading the detailed entries…';
      try { state = await routeFor(); }
      catch (error) {
        $('workspace').setAttribute('aria-busy', 'false');
        $('notice').innerHTML = `${esc(error.message)}. <button type="button" data-retry-navigation>Try again</button>`;
        return;
      }
      $('notice').textContent = '';
      render();
      const selectedPanel = phoneCircles() && state.hold && state.hold !== old.hold && state.tab === 'people' && !state.person
        ? document.querySelector('.company-panel') : phone() && state.focus && state.focus !== old.focus
          ? document.querySelector('.field-page .field-panel') : null;
      if (selectedPanel) {
        selectedPanel.setAttribute('tabindex', '-1');
        selectedPanel.focus({preventScroll: true});
        selectedPanel.scrollIntoView({block: 'start'});
        return;
      }
      if (state.edge && state.edge !== old.edge) $('detail-title')?.focus({preventScroll: !matchMedia('(max-width: 1000px)').matches});
      else if (focusedId && $(focusedId) && !$(focusedId).closest('[hidden]')) $(focusedId).focus({preventScroll: true});
      else {
        $('workspace').focus({preventScroll: true});
        if (state.node !== old.node || state.person !== old.person || state.section !== old.section || state.tab !== old.tab || state.pathway !== old.pathway || state.family !== old.family || state.overview !== old.overview) {
          (phone() && !$('toolbar').hidden ? $('toolbar') : $('workspace')).scrollIntoView({block: 'start'});
        }
      }
    });
    $('notice').addEventListener('click', e => { if (e.target.closest('[data-retry-navigation]')) window.dispatchEvent(new HashChangeEvent('hashchange')); });
    $('search').addEventListener('input', e => change({query: e.target.value, node: '', person: '', edge: '', page: 0}, true));
    $('layer-filter').addEventListener('change', e => change({layer: e.target.value, page: 0}));
    $('period-filter').addEventListener('change', e => change({period: e.target.value, page: 0}));
    $('hunt-filter').addEventListener('change', e => change({hunt: e.target.checked, page: 0}));
    $('workspace').addEventListener('click', e => {
      const button = e.target.closest('button');
      if (!button) return;
      if (button.hasAttribute('data-retry-records')) loadPeopleRecords();
      if (button.dataset.scrollTarget) {
        const target = $(button.dataset.scrollTarget);
        target?.focus({preventScroll: true});
        target?.scrollIntoView({block: 'start'});
      }
      if (button.dataset.page !== undefined) change({page: Number(button.dataset.page)});
      if (button.dataset.view) change({view: button.dataset.view});
      if (button.id === 'clear-neighbor-filters') change({kind: '', neighborLayer: '', page: 0});
    });
  } catch (error) {
    $('workspace').innerHTML = `<div class="empty"><h2>History in Conversation could not be opened.</h2><p>${esc(error.message)}</p><p>Build the site and serve its dedicated output directory, then reload.</p><button onclick="location.reload()">Try again</button></div>`;
  }
}
start();
