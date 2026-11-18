// Graph explorer: one node in the centre, its relations around it; click any node to recentre.
// Data from scripts/graph_explorer.py (/api/node, /api/group, /api/search, /api/meta).

const CAT = {
  person: { label: 'Person', shape: 'circle' },
  book: { label: 'Book', shape: 'square' },
  article: { label: 'Article', shape: 'triangle' },
  chapter: { label: 'Chapter', shape: 'triangle' },
  thesis: { label: 'Thesis', shape: 'diamond' },
  review: { label: 'Review', shape: 'down' },
  other: { label: 'Other work', shape: 'round' },
  institution: { label: 'Institution', shape: 'hex' },
  prize: { label: 'Prize', shape: 'diamond' },
  place: { label: 'Place', shape: 'pin' },
};
const FETCH_LIMIT = 24;
const NS = 'http://www.w3.org/2000/svg';
const $ = (s) => document.querySelector(s);
const state = {
  key: null, data: null, sort: 'weight',
  per: +($('#per').value),
  hidden: new Set(JSON.parse(localStorage.getItem('gx-hidden') || '[]')),
  trail: [],
  // place pages (2026-11-18): include the places within it; kind, decade and source filters (reset on a new place)
  popts: { children: localStorage.getItem('gx-children') === '1' ? '1' : '0', kind: '', decade: '', source: '',
    fiction: localStorage.getItem('gx-fiction') === '0' ? '0' : '' },
};
const placeQuery = (key) => key && key.startsWith('place:')
  ? '&' + new URLSearchParams(Object.entries(state.popts).filter(([, v]) => v)).toString() : '';

// a work is shown and grouped by the kind its matched record names (kind_proposed) when that differs from the graph's
const shownKind = (it) => it.kind_proposed || it.kind;
const cat = (it) => it.type === 'work' ? (CAT[shownKind(it)] ? shownKind(it) : 'other') : (CAT[it.type] ? it.type : 'other');
const kindNote = (it) => it.type === 'work' && it.kind_proposed && it.kind_proposed !== it.kind
  ? `listed as ${it.kind}; source says ${it.kind_proposed}` : null;
const fmt = (n) => (n ?? 0).toLocaleString('en');
const trunc = (s, n) => (s && s.length > n ? s.slice(0, n - 1) + '…' : s || '');

async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null) el.append(k.nodeType ? k : document.createTextNode(k));
  return el;
}
function s(tag, attrs = {}, ...kids) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) el.setAttribute(k, v);
  for (const k of kids.flat()) if (k != null) el.append(k.nodeType ? k : document.createTextNode(k));
  return el;
}

function shapePath(shape, r) {
  const p = (pts) => 'M' + pts.map((q) => q.map((v) => v.toFixed(1)).join(',')).join('L') + 'Z';
  switch (shape) {
    case 'circle': return `M${-r},0a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0`;
    case 'square': return p([[-r * .85, -r * .85], [r * .85, -r * .85], [r * .85, r * .85], [-r * .85, r * .85]]);
    case 'round': { const a = r * .85, c = r * .35; return `M${-a + c},${-a}H${a - c}Q${a},${-a} ${a},${-a + c}V${a - c}Q${a},${a} ${a - c},${a}H${-a + c}Q${-a},${a} ${-a},${a - c}V${-a + c}Q${-a},${-a} ${-a + c},${-a}Z`; }
    case 'triangle': return p([[0, -r * 1.1], [r * 1.05, r * .75], [-r * 1.05, r * .75]]);
    case 'down': return p([[0, r * 1.1], [r * 1.05, -r * .75], [-r * 1.05, -r * .75]]);
    case 'diamond': return p([[0, -r * 1.15], [r * 1.15, 0], [0, r * 1.15], [-r * 1.15, 0]]);
    case 'hex': return p([0, 1, 2, 3, 4, 5].map((i) => [r * Math.cos(Math.PI / 3 * i), r * Math.sin(Math.PI / 3 * i)]));
    case 'pin': { const a = r * .85; return `M0,${r * 1.15}L${-a * .8},${-r * .05}A${a},${a} 0 1,1 ${a * .8},${-r * .05}Z`; }
  }
}
const mark = (c, r) => s('path', { class: 'mark', d: shapePath(CAT[c].shape, r), fill: `var(--${c})` });
const icon = (c) => s('svg', { width: 12, height: 12, viewBox: '-7 -7 14 14', 'aria-hidden': 'true' }, s('path', { d: shapePath(CAT[c].shape, 5), fill: `var(--${c})` }));

function legend() {
  $('#legend').replaceChildren(...Object.entries(CAT).map(([c, v]) => h('span', {}, icon(c), v.label)));
}

// ---------- navigation ----------
function go(key) {
  if (!key || key === state.key) return;
  if (key.startsWith('place:') && key !== state.key) Object.assign(state.popts, { kind: '', decade: '', source: '' });
  location.hash = key;
}
window.addEventListener('hashchange', () => load(location.hash.slice(1)));

async function load(key, keepView = false) {
  if (!key) return;
  if (key.startsWith('cmp:')) return loadCompare(key);
  let data;
  try {
    data = await api(`/api/node?key=${encodeURIComponent(key)}&limit=${FETCH_LIMIT}&sort=${state.sort}${placeQuery(key)}`);
  } catch (e) {
    $('#panel').replaceChildren(h('p', { class: 'empty' }, `Could not load ${key}: ${e.message}`));
    return;
  }
  state.key = key; state.data = data;
  if (!keepView) {
    const i = state.trail.findIndex((t) => t.key === key);
    if (i >= 0) state.trail.splice(i, 1);
    state.trail.push({ key, label: data.node.label, c: cat(data.node) });
    if (state.trail.length > 14) state.trail.shift();
  }
  document.title = `${data.node.label} · Graph explorer`;
  renderTrail(); renderPanel(); renderGraph();
}

function renderTrail() {
  $('#trail').replaceChildren(...state.trail.map((t) =>
    h('a', { href: '#' + t.key, class: t.key === state.key ? 'cur' : null, title: t.label }, trunc(t.label, 40))));
}

// ---------- graph ----------
function renderGraph() {
  const svg = $('#viz');
  const { width: W, height: H } = svg.getBoundingClientRect();
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const { node, groups } = state.data;
  const cx = W / 2, cy = H / 2;
  const Rx = Math.max(140, W / 2 - 230), Ry = Math.max(110, H / 2 - 40);
  const shown = groups.filter((g) => !state.hidden.has(node.type + ':' + g.id)).map((g) => {
    const items = g.items.slice(0, state.per);
    return { ...g, shown: items, more: g.total - items.length };
  });
  const slots = shown.map((g) => g.shown.length + (g.more > 0 ? 1 : 0));
  const S = slots.reduce((a, b) => a + b, 0);
  const gap = shown.length > 1 ? 0.10 : 0;
  const avail = 2 * Math.PI - gap * shown.length;
  const gEdges = s('g'), gNodes = s('g'), gLabels = s('g');
  let a0 = -Math.PI / 2 + gap / 2;
  const rad = (w) => Math.min(13, 4 + 2.2 * Math.log10(1 + (w || 0)));
  const pos = (a, f) => [cx + Rx * f * Math.cos(a), cy + Ry * f * Math.sin(a)];

  shown.forEach((g, gi) => {
    const span = S ? avail * slots[gi] / S : 0;
    const step = span / slots[gi];
    const mid = a0 + span / 2;
    const [lx, ly] = pos(mid, 0.42);
    const entries = [...g.shown.map((it) => ({ it })), ...(g.more > 0 ? [{ more: g.more }] : [])];
    const tight = step < 0.13;
    entries.forEach((e, i) => {
      const a = a0 + step * (i + 0.5);
      const f = tight && i % 2 ? 0.8 : 1;
      const [x, y] = pos(a, f);
      const path = s('path', { class: g.id === 'possibly_same' ? 'edge maybe' : 'edge', d: `M${cx},${cy}Q${lx},${ly} ${x},${y}`,
        'stroke-width': e.it ? Math.min(4, 0.8 + Math.log2(e.it.n || 1)) : 0.8, 'stroke-opacity': 0.7 });
      gEdges.append(path);
      const right = Math.cos(a) >= 0;
      if (e.more) {
        const el = s('g', { class: 'node more', transform: `translate(${x},${y})`, tabindex: 0, role: 'button',
          'aria-label': `${fmt(e.more)} more: ${g.label}` },
          s('circle', { r: 9 }), s('text', { x: right ? 13 : -13, dy: '0.35em', 'text-anchor': right ? 'start' : 'end' }, `+${fmt(e.more)} more`));
        el.addEventListener('click', () => openGroup(g.id, true));
        gNodes.append(el);
        return;
      }
      const it = e.it, c = cat(it), r = rad(it.weight);
      const el = s('g', { class: 'node', 'data-w': (it.weight || 0) + (it.n || 0) * 1000, transform: `translate(${x},${y})`, tabindex: 0, role: 'link',
        'aria-label': `${CAT[c].label}: ${it.label}` },
        mark(c, r),
        s('text', { x: right ? r + 4 : -r - 4, dy: '0.35em', 'text-anchor': right ? 'start' : 'end' },
          trunc(it.label, 30) + (it.year ? ` (${it.year})` : '')));
      el.addEventListener('click', () => go(it.key));
      el.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') go(it.key); });
      el.addEventListener('mouseenter', (ev) => { path.classList.add('hi'); tip(ev, it, g); });
      el.addEventListener('mousemove', (ev) => tip(ev, it, g));
      el.addEventListener('mouseleave', () => { path.classList.remove('hi'); $('#tip').hidden = true; });
      gNodes.append(el);
    });
    const lab = s('text', { class: 'glabel', x: lx, y: ly, 'text-anchor': 'middle', dy: '0.35em',
      'paint-order': 'stroke', stroke: 'var(--surface)', 'stroke-width': 4, 'stroke-linejoin': 'round' },
      g.label, s('tspan', { class: 'n' }, ` ${fmt(g.total)}`));
    lab.style.cursor = 'pointer';
    lab.addEventListener('click', () => openGroup(g.id, false));
    gLabels.append(lab);
    a0 += span + gap;
  });

  const c = cat(node);
  const lines = wrap(node.label, 38, 3);
  const focus = s('g', { class: 'node focus', transform: `translate(${cx},${cy})` },
    mark(c, 18),
    s('text', { 'text-anchor': 'middle', y: 34, 'paint-order': 'stroke', stroke: 'var(--surface)', 'stroke-width': 5, 'stroke-linejoin': 'round' },
      lines.map((l, i) => s('tspan', { x: 0, dy: i ? '1.2em' : 0 }, l))));
  const root = s('g', { class: 'fade' }, gEdges, gLabels, gNodes, focus);
  svg.replaceChildren(root);
  $('#tip').hidden = true;
  declutter(root);
  if (!groups.length) svg.append(s('text', { x: cx, y: cy + 90, 'text-anchor': 'middle', class: 'glabel' }, 'No edges in the graph for this node.'));
  requestAnimationFrame(() => root.classList.add('shown'));
}

// Hide node labels that would overlap a label already placed (heavier nodes first); hover shows them.
function declutter(root) {
  const gl = [];
  for (const t of root.querySelectorAll('.glabel')) {          // nudge relation labels apart
    for (let i = 0; i < 4 && gl.some((p) => { const r = t.getBoundingClientRect(); return r.left < p.right && p.left < r.right && r.top < p.bottom && p.top < r.bottom; }); i++)
      t.setAttribute('y', +t.getAttribute('y') + 15);
    gl.push(t.getBoundingClientRect());
  }
  const placed = [...root.querySelectorAll('.glabel, .focus text, .more text, .mark, .more circle')].map((t) => t.getBoundingClientRect());
  const nodes = [...root.querySelectorAll('.node:not(.focus):not(.more)')].sort((a, b) => b.dataset.w - a.dataset.w);
  const hit = (a, b) => a.left < b.right + 2 && b.left < a.right + 2 && a.top < b.bottom && b.top < a.bottom;
  for (const n of nodes) {
    const t = n.querySelector('text'), r = t.getBoundingClientRect();
    if (placed.some((p) => hit(r, p))) t.classList.add('hid'); else placed.push(r);
  }
}

function wrap(text, n, max) {
  const words = (text || '').split(/\s+/), out = [];
  let cur = '';
  for (const w of words) {
    if ((cur + ' ' + w).trim().length > n && cur) { out.push(cur); cur = w; } else cur = (cur + ' ' + w).trim();
  }
  if (cur) out.push(cur);
  if (out.length > max) { out.length = max; out[max - 1] = trunc(out[max - 1], n - 1) + '…'; }
  return out;
}

function tip(ev, it, g) {
  const t = $('#tip'), box = $('.stage').getBoundingClientRect();
  const bits = [CAT[cat(it)].label, it.year, it.weight ? `${fmt(it.weight)} links in` : null,
    it.resolution === 'recorded' ? 'single source' : null].filter(Boolean).join(' · ');
  t.replaceChildren(...[h('b', {}, it.label), h('span', {}, bits), it.detail ? h('span', {}, h('br'), `${g.label}: ${it.detail}`) : null].filter(Boolean));
  t.hidden = false;
  const x = Math.min(ev.clientX - box.left + 14, box.width - 370);
  t.style.left = x + 'px'; t.style.top = (ev.clientY - box.top + 14) + 'px';
}

// ---------- side panel ----------
function renderPanel() {
  const { node, groups } = state.data;
  const c = cat(node);
  const meta = [CAT[c].label, node.type === 'place' ? node.kind : null, node.year, node.journal].filter(Boolean).join(' · ');
  // first publication year where it differs from the key's year (a reprint or a translation; data/graph/work-years)
  const first = node.type === 'work' && node.first_year && node.first_year !== node.year
    ? `first published ${node.first_year}` + (node.first_year_basis ? ` (${node.first_year_basis.replaceAll(';', ', ')})` : '') : null;
  const facts = node.type === 'work' ? [kindNote(node), first, node.in_volume,
    node.editors_printed ? `editors as printed: ${node.editors_printed}` : null,
    node.variant_titles ? `also titled: ${node.variant_titles}` : null,
    node.isbn ? `ISBN ${node.isbn}` : null, node.issn ? `ISSN ${node.issn}` : null,
    node.journal && node.journal_source && node.journal_source !== 'keylog' && node.journal_source !== 'node-source'
      ? `journal from the ${node.journal_source} record` : null].filter(Boolean) : [];
  const stats = [];
  if (node.type === 'person') stats.push(['works', node.works], ['citations to them', node.cited], ['reviews of their books', node.reviewed]);
  if (node.type === 'work') stats.push(['cited by', node.cited], ['reviews', node.reviewed]);
  if (node.type === 'work' && node.cited_edition) stats.push(['of the citations, in translation or another edition', node.cited_edition]);
  if (node.type === 'institution') stats.push(['theses', node.weight]);
  if (node.type === 'prize') stats.push(['awards listed', node.weight]);
  const card = h('div', {},
    h('div', {}, h('span', { class: 'chip' }, icon(c), ' ', meta),
      node.resolution === 'recorded' ? h('span', { class: 'chip', title: 'Known from one source only' }, 'recorded (one source)') : null),
    h('h2', {}, node.label),
    facts.length ? h('div', { class: 'muted' }, facts.map((f) => h('div', {}, f))) : null,
    h('div', { class: 'stats' }, stats.map(([l, v]) => h('span', {}, h('b', {}, fmt(v)), l))),
    h('div', { class: 'ids' }, h('span', { class: 'chip', title: 'Graph key' }, node.key),
      node.ids.filter((i) => !['review-credit', 'diss-person'].includes(i.scheme)).slice(0, 18).map((i) =>
        h('span', { class: 'chip', title: `${i.scheme}:${i.value}` },
          i.url ? h('a', { href: i.url, target: '_blank', rel: 'noopener' }, `${i.scheme} ${trunc(i.value, 24)}`) : `${i.scheme} ${trunc(i.value, 24)}`))));
  if (node.type === 'place') card.append(placeHeader(node));
  const sections = groups.map((g) => {
    const hid = node.type + ':' + g.id;
    const cb = h('input', { type: 'checkbox', checked: !state.hidden.has(hid), onclick: (ev) => ev.stopPropagation(),
      onchange: (ev) => { ev.target.checked ? state.hidden.delete(hid) : state.hidden.add(hid);
        localStorage.setItem('gx-hidden', JSON.stringify([...state.hidden])); renderGraph(); } });
    const list = h('ul', { class: 'items' }, g.items.map((it) => row(it, g.id)));
    const d = h('details', { 'data-rel': g.id, open: g.id !== 'candidates' && (g.items.length <= 8 || groups.length <= 3) ? true : null },
      h('summary', {}, g.label, h('span', { class: 'n' }, fmt(g.total)), h('label', { title: 'Show in the graph' }, cb, 'in view')),
      list);
    if (g.total > g.items.length) d.append(moreButton(g, list));
    return d;
  });
  $('#panel').replaceChildren(card, ...sections);
  $('#panel').scrollTop = 0;
}

// a place tag arrives as 'badge|line' (LC subject heading, title read or ruled, review of a book about the place)
const BADGED = new Set(['about', 'wider', 'places']);
function row(it, gid) {
  const c = cat(it);
  let badge = null, detail = it.detail;
  if (BADGED.has(gid) && detail && /^(LC|title \(read\)|title \(rule\)|review)\|/.test(detail)) {
    const i = detail.indexOf('|');
    badge = h('span', { class: 'badge src-' + detail.slice(0, i).split(' ')[0].toLowerCase() }, detail.slice(0, i));
    detail = detail.slice(i + 1);
  }
  const sub = [kindNote(it), detail, it.type === 'work' && it.weight ? `cited/reviewed ${fmt(it.weight)}` : null,
    it.type === 'person' && it.weight ? `${fmt(it.weight)} links to their works` : null,
    it.type === 'place' && it.weight ? `${fmt(it.weight)} works about it` : null].filter(Boolean).join(' · ');
  const li = h('li', { tabindex: 0, onclick: () => go(it.key), onkeydown: (ev) => { if (ev.key === 'Enter') go(it.key); }, title: it.label },
    icon(c), h('span', { class: 'lab' }, badge, it.label, sub ? h('span', { class: 'sub' }, sub) : null),
    h('span', { class: 'yr' }, it.year ?? ''));
  if (gid === 'people' && it.works && it.works.length) {      // the person's works about the place: the evidence
    const d = h('details', { class: 'pworks', onclick: (ev) => ev.stopPropagation() },
      h('summary', {}, `${it.works.length < it.n ? 'first ' + it.works.length + ' of ' : ''}${it.n} work${it.n === 1 ? '' : 's'} about the place`),
      h('ul', {}, it.works.map((w) => h('li', { onclick: (ev) => { ev.stopPropagation(); go(w.key); } },
        h('span', { class: 'badge src-' + w.source.split(' ')[0].toLowerCase() }, w.source), icon(CAT[w.kind] ? w.kind : 'other'), ' ',
        w.label, w.year ? ` (${w.year})` : ''))));
    li.querySelector('.lab').append(d);
  }
  return li;
}

// ---------- place header (2026-11-18) ----------
function placeHeader(node) {
  const p = node.place, o = state.popts;
  const reload = () => { localStorage.setItem('gx-children', o.children); localStorage.setItem('gx-fiction', o.fiction || '1'); load(state.key, true); };
  const sel = (name, label, options) => h('label', {}, label + ' ',
    h('select', { onchange: (ev) => { o[name] = ev.target.value; reload(); } },
      h('option', { value: '' }, 'all'), options.map(([v, n, t]) => h('option', { value: v, selected: o[name] === String(v) ? true : null }, `${t ?? v} (${fmt(n)})`))));
  const srcName = { lc: 'LC subject heading', title: 'title', review: 'review of a book' };
  const facts = [
    p.lc_heading ? `LC heading: ${p.lc_heading}` : 'no LC heading',
    p.period_of ? h('span', {}, 'a period polity of ', h('a', { href: '#place:' + p.period_of }, p.period_of_label || p.period_of),
      ' (its works are searched with it)') : null,
    p.variants && p.variants.length > 1 ? `also found as: ${p.variants.slice(1, 12).join(', ')}${p.variants.length > 12 ? ' …' : ''}` : null,
  ].filter(Boolean);
  const counts = h('div', { class: 'stats' },
    h('span', {}, h('b', {}, fmt(p.works)), 'works about it'),
    h('span', {}, h('b', {}, fmt(p.works_no_author)), 'of them with no linked author'),
    p.children_places ? h('span', {}, h('b', {}, fmt(p.works_with_children)), `with the ${fmt(p.children_places)} places within it (${fmt(p.works_with_children_no_author)} with no linked author)`) : null);
  const wider = p.wider && p.wider.length ? h('div', { class: 'muted' }, 'Wider regions (shown apart, not counted here): ',
    p.wider.map(([k, l, n], i) => h('span', {}, i ? ', ' : '', h('a', { href: '#' + k }, l), ` (${fmt(n)} works)`))) : null;
  const ctl = h('div', { class: 'pctl' },
    p.children_places ? h('label', {}, h('input', { type: 'checkbox', checked: o.children === '1' ? true : null,
      onchange: (ev) => { o.children = ev.target.checked ? '1' : '0'; reload(); } }), ` include the ${fmt(p.children_places)} places within it`) : null,
    h('label', { title: 'LC subject headings with the subdivision Fiction give the setting of a novel, not its subject' },
      h('input', { type: 'checkbox', checked: o.fiction === '0' ? true : null,
        onchange: (ev) => { o.fiction = ev.target.checked ? '0' : ''; reload(); } }), ' leave out fiction settings'),
    sel('kind', 'kind', p.by_kind.map(([k, n]) => [k, n])),
    sel('decade', 'decade', p.by_decade.map(([d, n]) => [d, n, d === 'none' ? 'no year' : d + 's'])),
    sel('source', 'evidence', p.by_source.map(([s, n]) => [s, n, srcName[s] || s])));
  const cmpIn = h('input', { type: 'search', placeholder: 'a place name', 'aria-label': 'Compare with another place' });
  const cmp = h('form', { class: 'pctl', onsubmit: async (ev) => {
      ev.preventDefault();
      const hit = (await api(`/api/search?q=${encodeURIComponent(cmpIn.value)}`)).find((x) => x.type === 'place');
      if (hit) location.hash = `cmp:${p.qid}+${hit.key.slice(6)}`; else cmpIn.value = 'no place found';
    } }, 'Compare with ', cmpIn, h('button', { type: 'submit' }, 'compare'),
    ...[['Q16', 'Canada'], ['Q854', 'Sri Lanka']].filter(([q]) => q !== p.qid).map(([q, l]) => h('a', { href: `#cmp:${p.qid}+${q}` }, l)));
  return h('div', { class: 'place' }, h('div', { class: 'muted' }, facts.map((f) => h('div', {}, f))), counts, ctl, cmp, wider,
    h('div', { class: 'muted' }, 'People are listed for the works they wrote; a place is never asserted of a person.'));
}

function moreButton(g, list) {
  const b = h('button', { class: 'moreb' }, `Show more (${fmt(g.total - g.items.length)} left)`);
  b.addEventListener('click', async () => {
    b.disabled = true;
    const r = await api(`/api/group?key=${encodeURIComponent(state.key)}&rel=${g.id}&offset=${g.items.length}&limit=50&sort=${state.sort}${placeQuery(state.key)}`);
    g.items.push(...r.items);
    list.append(...r.items.map((it) => row(it, g.id)));
    if (g.total > g.items.length) { b.textContent = `Show more (${fmt(g.total - g.items.length)} left)`; b.disabled = false; } else b.remove();
  });
  return b;
}

function openGroup(id, more) {
  const d = $(`#panel details[data-rel="${id}"]`);
  if (!d) return;
  d.open = true;
  d.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (more) d.querySelector('.moreb')?.click();
}

// ---------- two places compared (2026-11-18): #cmp:<QID>+<QID> ----------
async function loadCompare(key) {
  const [qa, qb] = key.slice(4).split('+');
  let d;
  try {
    d = await api(`/api/compare?a=place:${qa}&b=place:${qb}${placeQuery('place:x')}`);
  } catch (e) {
    $('#panel').replaceChildren(h('p', { class: 'empty' }, `Could not compare: ${e.message}`));
    return;
  }
  state.key = key; state.data = null;
  document.title = `${d.a_label} and ${d.b_label} · Graph explorer`;
  const A = d.a_label, B = d.b_label, o = state.popts;
  const wlink = (w) => h('a', { href: '#' + w.key }, w.label, w.year ? ` (${w.year})` : '');
  const sec = (label, n, kids, open) => h('details', { open: open ? true : null }, h('summary', {}, label, h('span', { class: 'n' }, fmt(n))), kids);
  const people = h('ul', { class: 'items' }, d.people_both.map((p) => h('li', {},
    icon('person'), h('span', { class: 'lab' }, h('a', { href: '#' + p.key }, p.label), h('span', { class: 'sub' }, `${p.na} on ${A} · ${p.nb} on ${B}`),
      h('details', { class: 'pworks' }, h('summary', {}, 'the works'),
        h('ul', {}, p.works.a.map((w) => h('li', {}, `${A}: `, wlink(w))), p.works.b.map((w) => h('li', {}, `${B}: `, wlink(w)))))))));
  const frames = h('table', { class: 'frames' }, h('tr', {}, h('th', {}, 'frame (LC headings and titles)'), h('th', {}, A), h('th', {}, B)),
    d.frames.map((f) => h('tr', {}, h('td', {}, f.frame), h('td', {}, `${fmt(f.a)} (${f.a_share}%)`), h('td', {}, `${fmt(f.b)} (${f.b_share}%)`))));
  const card = h('div', {}, h('span', { class: 'chip' }, icon('place'), ' Two places compared'),
    h('h2', {}, h('a', { href: '#place:' + qa }, A), ' and ', h('a', { href: '#place:' + qb }, B)),
    h('div', { class: 'stats' },
      h('span', {}, h('b', {}, fmt(d.works_a)), `works about ${A}`), h('span', {}, h('b', {}, fmt(d.works_b)), `works about ${B}`),
      h('span', {}, h('b', {}, fmt(d.people_both_total)), 'people with works about both'),
      h('span', {}, h('b', {}, fmt(d.works_both)), 'works about both'),
      h('span', {}, h('b', {}, fmt(d.cites_a_to_b)), `citations ${A} → ${B}`), h('span', {}, h('b', {}, fmt(d.cites_b_to_a)), `citations ${B} → ${A}`)),
    h('div', { class: 'pctl' }, h('label', {}, h('input', { type: 'checkbox', checked: o.children === '1' ? true : null,
      onchange: (ev) => { o.children = ev.target.checked ? '1' : '0'; localStorage.setItem('gx-children', o.children); loadCompare(key); } }),
      ' include the places within each')),
    h('div', { class: 'muted' }, `People are listed for the works they wrote (${fmt(d.people_a)} people for ${A}, ${fmt(d.people_b)} for ${B}).`));
  $('#panel').replaceChildren(card,
    sec('People with works about both', d.people_both_total, people, true),
    sec('Works about both', d.works_both, h('ul', { class: 'items' }, d.works_both_list.map((w) => h('li', {}, h('span', { class: 'lab' }, wlink(w))))), d.works_both > 0),
    sec('Citations between the two sets', d.cites_a_to_b + d.cites_b_to_a, h('ul', { class: 'items' }, d.cites.map((c) =>
      h('li', {}, h('span', { class: 'lab' }, wlink(c.citing), h('span', { class: 'sub' }, '→ cites ', wlink(c.cited)))))), true),
    sec('Shared frames', d.frames.length, frames, true));
  const svg = $('#viz');
  const { width: W, height: H } = svg.getBoundingClientRect();
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const r = Math.min(W, H) / 4, cx = W / 2, cy = H / 2;
  svg.replaceChildren(
    s('circle', { cx: cx - r * .6, cy, r, fill: 'var(--place)', 'fill-opacity': .15, stroke: 'var(--place)' }),
    s('circle', { cx: cx + r * .6, cy, r, fill: 'var(--person)', 'fill-opacity': .15, stroke: 'var(--person)' }),
    s('text', { x: cx - r * 1.1, y: cy - r - 10, 'text-anchor': 'middle', class: 'glabel' }, `${A}: ${fmt(d.people_a)} people`),
    s('text', { x: cx + r * 1.1, y: cy - r - 10, 'text-anchor': 'middle', class: 'glabel' }, `${B}: ${fmt(d.people_b)} people`),
    s('text', { x: cx, y: cy, 'text-anchor': 'middle', class: 'glabel' }, `${fmt(d.people_both_total)} both`),
    s('text', { x: cx, y: cy + 18, 'text-anchor': 'middle', class: 'glabel' }, `${fmt(d.cites_a_to_b + d.cites_b_to_a)} citations between`));
}

// ---------- search ----------
let timer, sel = -1, hits = [];
$('#q').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(search, 200); });
$('#q').addEventListener('keydown', (ev) => {
  const items = [...$('#results').children];
  if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
    ev.preventDefault();
    sel = Math.max(0, Math.min(items.length - 1, sel + (ev.key === 'ArrowDown' ? 1 : -1)));
    items.forEach((li, i) => li.setAttribute('aria-selected', i === sel));
  } else if (ev.key === 'Enter') {
    const it = hits[sel >= 0 ? sel : 0];
    if (it) pick(it);
  } else if (ev.key === 'Escape') $('#results').hidden = true;
});
document.addEventListener('click', (ev) => { if (!ev.target.closest('.search')) $('#results').hidden = true; });

async function search() {
  const q = $('#q').value.trim();
  if (q.length < 2) { $('#results').hidden = true; return; }
  hits = await api(`/api/search?q=${encodeURIComponent(q)}`);
  sel = -1;
  $('#results').replaceChildren(...(hits.length ? hits.map((it) => h('li', { role: 'option', onclick: () => pick(it) },
    icon(cat(it)), h('span', { class: 'lab' }, it.label), h('span', { class: 'muted' }, [it.year, it.weight ? `${fmt(it.weight)} links in` : null].filter(Boolean).join(' · '))))
    : [h('li', { class: 'muted' }, 'Nothing found')]));
  $('#results').hidden = false;
}
function pick(it) { $('#results').hidden = true; $('#q').value = ''; go(it.key); }

// ---------- controls ----------
$('#per').addEventListener('input', (ev) => { state.per = +ev.target.value; $('#perv').value = state.per; if (state.data) renderGraph(); });
document.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => {
  document.querySelectorAll('.seg button').forEach((x) => x.classList.toggle('on', x === b));
  state.sort = b.dataset.sort; load(state.key, true);
}));
let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => state.data && renderGraph(), 150); });

api('/api/meta').then((m) => {
  $('#meta').textContent = `${fmt(m.report.Person)} people · ${fmt(m.report.Work)} works · built ${String(m.built).slice(0, 10)}`;
}).catch(() => {});
legend();
if (!location.hash) history.replaceState(null, '', '#p-1025');   // start: Natalie Zemon Davis
load(location.hash.slice(1));
