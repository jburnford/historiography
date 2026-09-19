export const PAGE_SIZE = 6;
export const LAYER_TITLES = {
  intellectual_traditions: 'Intellectual traditions',
  enduring_fields_and_genres: 'Enduring fields & genres',
  intellectual_connections: 'Thinkers & intellectual connections',
  historiographical_developments: 'Schools, approaches & expanding fields',
};
export const KINDS = {
  influence: 'Influence', contribution: 'Contribution', comparison: 'Comparison',
  critique: 'Critique', unclassified: 'Unclassified connection',
};
export const PERSON_ROLES = {
  historian: 'Representative historian', contributor: 'Intellectual contributor',
  precursor: 'Earlier resource', critic: 'Critical intervention', comparison: 'Teaching comparison',
};
export function edgeKind(edge) {
  return edge.relationship_kind && typeof edge.directed === 'boolean'
    ? edge.relationship_kind : 'unclassified';
}
export function hasArrow(edge) {
  return edgeKind(edge) !== 'unclassified' && edge.directed === true;
}
export function filterNodes(nodes, {query = '', layer = '', period = '', hunt = false} = {}, people = []) {
  const names = new Map(people.map(p => [p.id, p.label]));
  const words = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  return nodes.filter(n => (!layer || n.layer === layer)
    // Unassigned entries stay discoverable alongside a selected teaching period.
    && (!period || (period === 'unassigned' ? !n.period : (!n.period || n.period === period)))
    && (!hunt || n.hunt_core_paradigm)
    && words.every(w => [n.label, n.description, n.scope_note, n.entry_type, n.representative_figures_and_works, n.date_label,
      ...(n.strands || []).map(s => `${s.title} ${s.focus} ${s.works} ${s.person_ids.map(id => names.get(id) || '').join(' ')}`),
      ...(n.representative_people || []).map(r => `${names.get(r.person_id) || ''} ${r.works} ${r.context}`)]
      .filter(Boolean).join(' ').toLocaleLowerCase().includes(w)));
}
export function personContexts(graph, personId) {
  return graph.nodes.flatMap(node => (node.representative_people || [])
    .filter(r => r.person_id === personId).map(representative => ({node, representative})));
}
export function filterPeople(graph, state = {}) {
  const words = (state.query || '').toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  const allowed = new Set(filterNodes(graph.nodes, {...state, query: ''}).map(n => n.id));
  return (graph.people || []).filter(p => {
    const contexts = personContexts(graph, p.id).filter(c => allowed.has(c.node.id));
    const own = p.node_id && allowed.has(p.node_id) ? graph.nodes.find(n => n.id === p.node_id) : null;
    if (!contexts.length && !own) return false;
    const text = [p.label, own?.representative_figures_and_works,
      ...contexts.map(c => `${c.representative.works} ${c.representative.context}`)].join(' ').toLocaleLowerCase();
    return words.every(w => text.includes(w));
  }).sort((a, b) => a.label.localeCompare(b.label));
}
export function neighborhood(graph, id, kind = '', layer = '') {
  const nodes = new Map(graph.nodes.map(n => [n.id, n]));
  return graph.edges.filter(e => (e.source === id || e.target === id)
    && (!kind || edgeKind(e) === kind))
    .map(edge => ({edge, node: nodes.get(edge.source === id ? edge.target : edge.source)}))
    .filter(row => !layer || row.node.layer === layer)
    .sort((a, b) => a.node.label.localeCompare(b.node.label) || a.edge.id.localeCompare(b.edge.id));
}
export function partitionNeighborhood(rows, id) {
  const priority = {influence: 0, contribution: 1, critique: 2};
  return {
    incoming: rows.filter(r => hasArrow(r.edge) && r.edge.target === id)
      .sort((a,b) => priority[edgeKind(a.edge)] - priority[edgeKind(b.edge)] || a.node.label.localeCompare(b.node.label)),
    outgoing: rows.filter(r => hasArrow(r.edge) && r.edge.source === id),
    associated: rows.filter(r => !hasArrow(r.edge)),
  };
}
export function readRoute(hash, graph, pathways) {
  const p = new URLSearchParams(hash.replace(/^#/, ''));
  const valid = (key, rows) => rows.some(n => n.id === p.get(key)) ? p.get(key) : '';
  /* `focus` holds an entry inside the field view; `node` opens the full entry page.
     Journals are addressable in the field but are not atlas entries. */
  const fieldIds = graph.__fieldNodes || graph.nodes;
  const route = {
    tab: ['people', 'pathways', 'about', 'browse'].includes(p.get('tab')) ? p.get('tab') : 'map',
    focus: fieldIds.some(n => n.id === p.get('focus')) ? p.get('focus') : '',
    /* `path` lays a seminar pathway over the field; `pathway` opens its reading page. */
    path: valid('path', pathways.pathways),
    node: valid('node', graph.nodes), edge: valid('edge', graph.edges),
    person: valid('person', graph.people || []),
    /* `hold` keeps a person or an entry lit in the people constellation; `letter` opens a
       register letter. Neither leaves the people tab. */
    hold: (graph.people || []).some(x => x.id === p.get('hold')) || graph.nodes.some(n => n.id === p.get('hold')) ? p.get('hold') : '',
    letter: /^[A-Z]$/.test(p.get('letter') || '') ? p.get('letter') : '',
    section: p.get('section') === 'connections' ? 'connections' : '',
    pathway: valid('pathway', pathways.pathways), layer: valid('layer', graph.layers),
    period: p.get('period') === 'unassigned' ? 'unassigned' : valid('period', graph.periods),
    query: p.get('query') || '', hunt: p.get('hunt') === '1',
    view: p.get('view') === 'list' ? 'list' : 'map',
    kind: Object.hasOwn(KINDS, p.get('kind')) ? p.get('kind') : '',
    neighborLayer: graph.layers.some(l => l.id === p.get('neighborLayer')) ? p.get('neighborLayer') : '',
    page: Math.max(0, Math.min(1000, Number.parseInt(p.get('page'), 10) || 0)),
    hide: (p.get('hide') || '').split(',').filter(Boolean)
      .filter(k => /^[a-z_]{3,30}$/.test(k)).join(','),
  };
  if (route.edge) {
    const e = graph.edges.find(e => e.id === route.edge);
    if (![e.source, e.target].includes(route.node)) route.node = e.source;
    route.section = 'connections';
    route.person = '';
  }
  if (route.kind || route.neighborLayer) route.section = 'connections';
  if (route.path) { route.pathway = ''; route.person = ''; route.tab = 'map'; }
  if (route.pathway) route.tab = 'pathways';
  if (route.node) { route.tab = 'map'; route.focus = ''; route.path = ''; }
  if (route.focus) { route.tab = 'map'; route.person = ''; }
  if (route.person && !route.node) route.tab = 'people';
  if ((route.hold || route.letter) && !route.node && !route.person && !route.pathway) route.tab = 'people';
  return route;
}
export function routeHash(state) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(state)) {
    if (v && !(k === 'tab' && v === 'map')) p.set(k, v === true ? '1' : String(v));
  }
  return p.size ? `#${p}` : '#';
}
