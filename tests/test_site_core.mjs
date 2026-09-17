import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {edgeKind, hasArrow, filterNodes, filterPeople, personContexts, neighborhood, partitionNeighborhood, readRoute, routeHash} from '../site/core.mjs';
import {parseSpan, spanOf, journalNodes, fieldNodes, fieldEdges, fieldKinds, fieldLayers,
  relationIndex, buildFieldLayout, focusSetFor, pathwaySet, pathwayEdges, milestoneYears,
  JOURNAL_LAYER} from '../site/field.mjs';

const graph = JSON.parse(readFileSync(new URL('../historiography-1920-2000.json', import.meta.url)));
const pathways = JSON.parse(readFileSync(new URL('../seminar-pathways.json', import.meta.url)));

test('arrows never turn legacy links or comparisons into influence', () => {
  const legacy = {source:'a',target:'b',type:'connection'};
  assert.equal(edgeKind(legacy), 'unclassified');
  assert.equal(hasArrow(legacy), false);
  assert.ok(graph.edges.some(e => edgeKind(e) === 'comparison'));
  for (const e of graph.edges) {
    if (!e.relationship_kind || e.relationship_kind === 'comparison') assert.equal(hasArrow(e), false, e.id);
    else assert.equal(hasArrow(e), true, e.id);
  }
});
test('a person can span groups while critic and resource roles remain distinct', () => {
  const hobsbawm = graph.people.find(p => p.label === 'Eric Hobsbawm');
  assert.ok(personContexts(graph, hobsbawm.id).length > 1);
  assert.ok(filterPeople(graph, {query:'Hobsbawm'}).some(p => p.id === hobsbawm.id));
  const eley = graph.people.find(p => p.label === 'Geoff Eley');
  assert.equal(personContexts(graph,eley.id).find(c=>c.node.id==='bielefeld').representative.role,'critic');
  assert.equal(personContexts(graph,'geertz').find(c=>c.node.id==='culture').representative.role,'contributor');
  assert.ok(filterNodes(graph.nodes,{query:'Geoff Eley'},graph.people).some(n=>n.id==='bielefeld'));
  assert.ok(filterNodes(graph.nodes,{query:'E. P. Thompson'},graph.people).some(n=>n.id==='culture'));
});
test('every edge is reachable once in its correct directional lane', () => {
  for (const n of graph.nodes) {
    const rows=neighborhood(graph,n.id);
    const lanes=partitionNeighborhood(rows,n.id);
    assert.equal(Object.values(lanes).flat().length, rows.length);
    for (const r of lanes.incoming) { assert.equal(r.edge.target,n.id); assert.ok(hasArrow(r.edge)); }
    for (const r of lanes.outgoing) { assert.equal(r.edge.source,n.id); assert.ok(hasArrow(r.edge)); }
    for (const r of lanes.associated) assert.equal(hasArrow(r.edge),false);
  }
});
test('search includes works and preserves distinct Marx IDs', () => {
  assert.ok(filterNodes(graph.nodes, {query: 'Metahistory'}).some(n => n.id === 'white'));
  assert.ok(filterNodes(graph.nodes, {query: 'Pinchbeck'}).some(n => n.id === 'ivy_pinchbeck'));
  assert.notEqual(graph.nodes.find(n => n.id === 'karl').label, graph.nodes.find(n => n.id === 'marx').label);
  assert.equal(filterNodes(graph.nodes, {hunt: true}).length, 4);
  assert.equal(filterNodes(graph.nodes, {query: 'no-such-entry-xyz'}).length, 0);
});
test('period browsing retains unassigned entries and filters compose', () => {
  const unknown = graph.nodes.filter(n => !n.period);
  for (const p of graph.periods) {
    const rows = filterNodes(graph.nodes, {period: p.id});
    for (const n of unknown) assert.ok(rows.includes(n));
    assert.ok(rows.every(n => !n.period || n.period === p.id));
  }
  assert.equal(filterNodes(graph.nodes, {period: 'unassigned'}).length, unknown.length);
  assert.ok(filterNodes(graph.nodes, {layer: 'intellectual_connections', query: 'women'}).every(n => n.layer === 'intellectual_connections'));
});
test('every relationship remains reachable from both endpoint neighborhoods', () => {
  for (const n of graph.nodes) {
    const rows = neighborhood(graph, n.id);
    assert.equal(rows.length, graph.edges.filter(e => e.source === n.id || e.target === n.id).length);
    for (const {edge, node} of rows) {
      assert.notEqual(node.id, n.id);
      assert.ok([edge.source, edge.target].includes(node.id));
    }
  }
});
test('direct URLs resolve edges, reject unknown IDs, and preserve pathway context', () => {
  const e = graph.edges.find(e => e.relationship_kind === 'comparison');
  const route = readRoute(`#edge=${e.id}`, graph, pathways);
  assert.equal(route.node, e.source);
  assert.equal(route.edge, e.id);
  const invalid = readRoute('#node=missing&layer=bad&period=bad&kind=bad&page=-3', graph, pathways);
  assert.equal(invalid.node, ''); assert.equal(invalid.page, 0); assert.equal(invalid.kind, '');
  const state = readRoute('#node=annales&pathway=paradigms_and_limits&view=list&query=a%26b', graph, pathways);
  assert.deepEqual(readRoute(routeHash(state), graph, pathways), state);
  assert.ok(routeHash({...state, view: 'map'}).includes('view=map'), 'mobile needs an explicit map override');
});

test('central contributors have directional links and field branches are searchable', () => {
  for (const [person, field] of [['kuhn','science'],['marc_bloch','annales'],['maurice_dobb','marx']]) {
    assert.ok(neighborhood(graph,field).some(r=>r.node.id===person && hasArrow(r.edge)));
  }
  assert.ok(filterNodes(graph.nodes,{query:'cliometrics'},graph.people).some(n=>n.id==='economic'));
  assert.ok(filterNodes(graph.nodes,{query:'Labrousse'},graph.people).some(n=>n.id==='annales'));
});

test('new public, medical and urban fields resolve in search, routes and shared person contexts', () => {
  for (const [query, id] of [['Public history','publichistory'], ['Curing Their Ills','medicalhistory'], ['Streetcar Suburbs','urbanhistory']]) {
    assert.ok(filterNodes(graph.nodes, {query}, graph.people).some(n => n.id === id));
    assert.equal(readRoute(`#node=${id}`, graph, pathways).node, id);
    assert.ok(neighborhood(graph,id).length > 0);
  }
  const hayden = personContexts(graph,'dolores_hayden').map(c => c.node.id);
  assert.ok(hayden.includes('publichistory') && hayden.includes('urbanhistory'));
  assert.ok(personContexts(graph,'roy_porter').some(c => c.node.id === 'medicalhistory'));
  assert.equal(personContexts(graph,'dorothy_porter_wesley').some(c => c.node.id === 'medicalhistory'), false);
  const comparison = neighborhood(graph,'medicalhistory').find(r => r.node.id === 'science');
  assert.equal(hasArrow(comparison.edge), false);
});

test('spatial, intellectual, labour and ethnohistory remain distinct and navigable', () => {
  for (const [query, id] of [['HGIS','spatialhistory'], ['history of ideas','intellectualhistory'], ['labor','labourhistory'], ['Ethnohistory','ethnohistory']]) {
    assert.ok(filterNodes(graph.nodes, {query}, graph.people).some(n => n.id === id), query);
    assert.equal(readRoute(`#node=${id}`, graph, pathways).node, id);
  }
  const thompson = personContexts(graph, 'ep_thompson').map(c => c.node.id);
  assert.ok(thompson.includes('marx') && thompson.includes('labourhistory'));
  const skinner = personContexts(graph, 'quentin_skinner').map(c => c.node.id);
  assert.ok(skinner.includes('context') && skinner.includes('intellectualhistory'));
  const ethno = neighborhood(graph, 'ethnohistory');
  assert.equal(hasArrow(ethno.find(r => r.node.id === 'indigenous').edge), false);
  assert.equal(personContexts(graph, 'angela_cavender_wilson').find(c => c.node.id === 'ethnohistory').representative.role, 'critic');
});


test('field dates: spans read arrival, never a coverage limit as an ending', () => {
  // "coverage through 2000" is a statement about the atlas, not about the field.
  const q = parseSpan('1950s–70s expansion · coverage through 2000');
  assert.equal(q.start, 1950);
  assert.equal(q.end, 1979, 'the coverage year must not become the span end');
  assert.equal(q.coverage, 2000);
  assert.equal(q.endKind, 'coverage_limit');
  assert.equal(parseSpan('Ranke · archives · philology'), null, 'no years means no span');
  assert.equal(parseSpan('Journal ran 1916 until 1929').endKind, 'terminus');
  // A curated date_span wins, and a null end continues rather than stopping.
  const curated = spanOf({date_span: {start: 1967, end: null, precision: 'year'}, date_label: 'x'});
  assert.ok(curated.curated);
  assert.equal(curated.endKind, 'coverage_limit', 'an unverified end is not an ending');
});

test('field taxonomy is derived from the data, so new layers and kinds cannot vanish', () => {
  const nodes = fieldNodes(graph);
  const ids = new Set(nodes.map(n => n.id));
  for (const n of graph.nodes) assert.ok(ids.has(n.id), `${n.id} missing from the field`);
  const {nodes: journals, edges: jEdges, unlinked} = journalNodes(graph);
  assert.equal(nodes.length, graph.nodes.length + journals.length);
  // Every promoted journal carries at least one evidenced edge; the rest stay counted.
  const linked = new Set(jEdges.flatMap(e => [e.source, e.target]));
  for (const j of journals) assert.ok(linked.has(j.id), `${j.id} promoted without an edge`);
  assert.ok(unlinked >= 0);
  if (journals.length) assert.ok(fieldLayers(graph, {}).includes(JOURNAL_LAYER));
  // Kinds beyond the curated four are surfaced rather than dropped.
  const kinds = fieldKinds(graph);
  for (const e of fieldEdges(graph)) assert.ok(kinds.includes(e.relationship_kind), e.relationship_kind);
});

test('field layout places every entry it counts', () => {
  const order = fieldLayers(graph, {});
  const view = buildFieldLayout(graph, 1400, null, order);
  const total = fieldNodes(graph).length;
  assert.equal(view.placed.size, total, 'a counted entry must also be drawn');
  assert.equal(view.datedCount + view.undatedCount, total);
  // Focus keeps the focused entry and its neighbours full size, ghosting the rest.
  const index = relationIndex(graph);
  const busiest = fieldNodes(graph)
    .map(n => [n.id, (index.get(n.id) || []).length]).sort((a, b) => b[1] - a[1])[0][0];
  const focused = buildFieldLayout(graph, 1400, focusSetFor(graph, busiest, index), order);
  assert.equal(focused.placed.size, total, 'ghosted entries stay addressable');
  assert.ok(focused.ghosts.length > 0, 'unrelated entries should be set aside');
  assert.ok(focused.height < view.height, 'focus must reclaim vertical space');
});

test('focus routes to the field and is distinct from an entry page', () => {
  graph.__fieldNodes = fieldNodes(graph);
  const journal = journalNodes(graph).nodes[0];
  if (journal) {
    const r = readRoute(`#focus=${journal.id}`, graph, pathways);
    assert.equal(r.focus, journal.id, 'a linked journal must be addressable in the field');
    assert.equal(r.node, '', 'a journal is not an atlas entry page');
  }
  assert.equal(readRoute('#focus=not-a-real-id', graph, pathways).focus, '');
  const both = readRoute('#focus=annales&node=marx', graph, pathways);
  assert.equal(both.node, 'marx');
  assert.equal(both.focus, '', 'an entry page clears the field focus');
  assert.equal(readRoute('#hide=comparison,critique', graph, pathways).hide, 'comparison,critique');
  assert.equal(readRoute('#hide=<script>', graph, pathways).hide, '', 'hide must be validated');
});

test('field layout fits the box it is given and never reserves a rail', () => {
  const order = fieldLayers(graph, {});
  for (const width of [1400, 940, 780, 640]) {
    const view = buildFieldLayout(graph, width, null, order);
    assert.ok(view.inner <= Math.max(width - 2, 600), `layout wider than its box at ${width}`);
    // Every label placed to the right must end inside the drawable area.
    for (const b of view.bars) {
      assert.ok(b.x >= view.x0 - 1 && b.x + b.w <= view.x1 + 1, `${b.node.id} bar outside axis`);
    }
    for (const c of view.chips) assert.ok(c.x + c.w <= view.x1 + 1, `${c.node.id} chip outside axis`);
  }
  const view = buildFieldLayout(graph, 1400, null, order);
  if (view.undatedCount) assert.ok(view.captions.length > 0, 'undated strip must be captioned');
  // "onward · coverage through 2000" is drawn solid to the wall and marked open, never as a stub.
  const annales = view.bars.find(b => b.node.id === 'annales');
  assert.ok(annales.open && !annales.point);
  assert.ok(Math.abs(annales.x + annales.w - view.scale(view.coverageYear)) < 0.5, 'open ends reach the coverage wall');
  for (const b of view.bars.filter(b => b.span.endKind === 'coverage_limit'))
    assert.ok(Math.abs(b.x + b.w - view.scale(b.span.coverage ?? view.coverageYear)) < 0.5, b.node.id);
  // A label naming one year, with no "onward", is a single mark of readable width.
  const point = view.bars.find(b => b.point);
  if (point) assert.ok(point.w >= 12 && point.span.endKind !== 'coverage_limit', 'a single dated year is drawn as a mark, not a sliver');
});

test('milestone ticks come only from years the label actually names, inside the span', () => {
  assert.deepEqual(milestoneYears({date_label: 'The Order of Things 1966 · Discipline and Punish 1975 · coverage through 2000'}), [1966, 1975]);
  assert.deepEqual(milestoneYears({date_label: '1950s–70s expansion'}), []);
  const view = buildFieldLayout(graph, 1400, null, fieldLayers(graph, {}));
  for (const b of view.bars) for (const t of b.ticks) {
    assert.ok(t.yr > b.span.start, `${b.node.id} tick at its own start`);
    assert.ok(t.x > b.x && t.x <= b.x + b.w + b.contW + 0.5, `${b.node.id} tick outside its mark`);
  }
});

test('a pathway overlay is a set of entries and only their recorded relationships', () => {
  const p = pathways.pathways.find(p => p.id === 'paradigms_and_limits');
  const set = pathwaySet(p);
  assert.equal(set.size, p.node_ids.length);
  const index = relationIndex(graph);
  const edges = pathwayEdges(graph, p, index);
  assert.ok(edges.length > 0);
  for (const e of edges) assert.ok(set.has(e.source) && set.has(e.target), `${e.id} leaves the pathway`);
  assert.equal(new Set(edges.map(e => e.id)).size, edges.length, 'no edge is drawn twice');
  assert.equal(pathwaySet(null), null);
  assert.deepEqual(pathwayEdges(graph, null, index), []);
  // Numbered labels follow reading order, and the overlay ghosts everything else.
  const numbering = new Map(p.node_ids.map((id, i) => [id, i + 1]));
  const view = buildFieldLayout(graph, 1400, set, fieldLayers(graph, {}), {numbering});
  const annales = view.bars.find(b => b.node.id === 'annales');
  assert.ok(annales.label.startsWith(`${numbering.get('annales')}. `));
  assert.equal(view.ghosts.length, fieldNodes(graph).length - set.size);
});

test('the pathway overlay route is distinct from the pathway reading page', () => {
  graph.__fieldNodes = fieldNodes(graph);
  const r = readRoute('#path=paradigms_and_limits', graph, pathways);
  assert.equal(r.path, 'paradigms_and_limits');
  assert.equal(r.tab, 'map', 'an overlay is a field view');
  assert.equal(r.pathway, '', 'the reading page is a separate route');
  assert.equal(readRoute('#path=not-real', graph, pathways).path, '');
  const held = readRoute('#path=paradigms_and_limits&focus=annales', graph, pathways);
  assert.equal(held.focus, 'annales');
  assert.equal(held.path, 'paradigms_and_limits', 'holding an entry keeps the pathway as context');
  assert.equal(readRoute('#path=paradigms_and_limits&node=marx', graph, pathways).path, '', 'an entry page clears the overlay');
  assert.ok(routeHash({path: 'paradigms_and_limits', tab: 'map'}).includes('path=paradigms_and_limits'));
});

test('undated earlier roots open the start of a mark instead of inventing an origin', () => {
  const military = parseSpan('Earlier roots · Howard 1961 · Keegan 1976 · multiple paradigms · coverage through 2000');
  assert.equal(military.start, 1961, 'the first dated year is kept as data');
  assert.ok(military.openStart, 'but the label states earlier roots');
  assert.equal(parseSpan('1800s roots · Namier 1929 · coverage through 2000').openStart, false, 'dated roots are a dated start');
  assert.equal(parseSpan('Ancient roots · Strachey 1918 · coverage through 2000').openStart, true);
  assert.equal(parseSpan('Comparative programmes · 1960s–90s · earlier resources').openStart, false, 'earlier resources drawn on are not the field’s own roots');
  const curated = spanOf({date_span: {start: 1961, end: null, start_kind: 'earlier_roots'}, date_label: 'x'});
  assert.ok(curated.openStart);
  const view = buildFieldLayout(graph, 1400, null, fieldLayers(graph, {}));
  const bar = view.bars.find(b => b.node.id === 'military');
  assert.ok(bar.lead, 'military history enters the timeline as already established');
  assert.equal(bar.lead.x, view.x0);
  assert.ok(Math.abs(bar.lead.x + bar.lead.w - bar.x) < 0.5, 'the lead-in meets the first dated year');
  for (const b of view.bars) if (b.span.openStart) assert.ok(b.lead || b.x - view.x0 <= 4, b.node.id);
});

test('journals without publication dates fall back to their evidenced venue role, and say so', () => {
  const jc = graph.journal_catalogue;
  const undated = jc.nodes.filter(n => n.entry_kind === 'periodical' && !Number.isFinite(n.date_span?.start));
  const {nodes: journals} = journalNodes(graph);
  for (const j of journals) {
    const raw = jc.nodes.find(n => n.id === j.id);
    if (Number.isFinite(raw.date_span?.start)) {
      assert.equal(j.date_span.start, raw.date_span.start, 'recorded dates are never replaced');
      continue;
    }
    const roles = jc.edges.filter(e => e.source === j.id).map(e => e.temporal_scope?.start).filter(Number.isFinite);
    if (!roles.length) { assert.equal(j.date_span, undefined); continue; }
    assert.equal(j.date_span.start, Math.min(...roles));
    assert.equal(j.date_span.start_kind, 'venue_role_start');
    assert.equal(j.date_span.end, null, 'an unverified end is not an ending');
    assert.match(j.date_label, /unverified/);
    assert.match(j.date_span.basis, /not the first issue/);
  }
  assert.ok(undated.length >= 0);
});
