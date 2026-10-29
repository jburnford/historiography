/* The company they keep: people placed between the entries that name them, in two levels.
   The overview rings the twelve editorial families and draws only the people named in two or
   more of them; a family opens a ring of its own entries with everyone they name. Deterministic
   layout, no force simulation. A person named in one entry gathers at that entry; a person named
   in several is drawn near the mean of their positions. Roster membership is shared context,
   never an influence edge: no line is ever drawn between two people. */

/* Labels written surname first in this roster. A `sort_name` field on people records would
   replace this editorial list; until then it is kept here and documented in the site README. */
const SURNAME_FIRST = new Set(['Wang Feng', 'Fei Xiaotong', 'Sun Tzu (Sunzi)', 'Lu Gwei-djen',
  'Wang Ling', 'Ho Peng-Yoke', 'Tsien Tsuen-hsuin', 'Huang Hsing-Tsung']);
const WHOLE_NAME = new Set(['Te Rangi Hīroa (Peter H. Buck)', 'Plutarch']);
const COMPOUND = {'Paul Vidal de la Blache': 'Vidal de la Blache',
  'Numa Denis Fustel de Coulanges': 'Fustel de Coulanges', 'Luis González y González': 'González y González'};
const PARTICLES = new Set(['de', 'van', 'von', 'du', 'da', 'della', 'der', 'den', 'le', 'la', 'ter', 'dos', 'das', 'di', 'del', 'y']);
const fold = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '');

/* Returns {surname, given, key, initial}. `key` sorts; `initial` is the register letter. */
export function sortName(label) {
  let base = label.replace(/\s*\([^)]*\)\s*$/, '').replace(/,\s*Jr\.?$/, '').trim();
  if (base.includes(' / ')) base = base.split(' / ').pop().trim();
  if (WHOLE_NAME.has(label) || !base.includes(' ')) {
    const name = label.replace(/\s*\([^)]*\)\s*$/, '');
    return {surname: name, given: '', key: fold(name).toLocaleLowerCase(), initial: fold(name)[0].toUpperCase()};
  }
  if (SURNAME_FIRST.has(label)) {
    const [surname, ...rest] = base.split(' ');
    return {surname, given: rest.join(' '), key: fold(`${surname} ${rest.join(' ')}`).toLocaleLowerCase(), initial: fold(surname)[0].toUpperCase()};
  }
  let surname, given;
  if (COMPOUND[label]) { surname = COMPOUND[label]; given = base.slice(0, base.length - surname.length).trim(); }
  else {
    const parts = base.split(' ');
    surname = parts.pop();
    while (parts.length > 1 && PARTICLES.has(parts.at(-1))) surname = `${parts.pop()} ${surname}`;
    given = parts.join(' ');
  }
  const core = surname.split(' ').filter(w => !PARTICLES.has(w)).join(' ') || surname;
  return {surname, given, key: fold(`${core}, ${given}`).toLocaleLowerCase(), initial: fold(core)[0].toUpperCase()};
}
export function bySurname(a, b) { return sortName(a.label).key.localeCompare(sortName(b.label).key); }

/* Every entry that names a person, with the role it gives them. */
/* A collaborative work (Life Lived Like a Story, 1.201) keeps its entry, its credited people and its place in
   their panels, but it is not a field: drawing it as a segment of the circles is a category error (user,
   2026-10-28). Its people stay on the circles through their fields. */
const NOT_A_RING = new Set(['Collaborative work']);
const ringEntry = (graph, id) => !NOT_A_RING.has(graph.nodes.find(n => n.id === id)?.entry_type);
export function membership(graph) {
  const byPerson = new Map(), byEntry = new Map();
  for (const n of graph.nodes) {
    if (!n.representative_people?.length) continue;
    byEntry.set(n.id, n.representative_people.map(r => ({id: r.person_id, role: r.role})));
    for (const r of n.representative_people) {
      if (!byPerson.has(r.person_id)) byPerson.set(r.person_id, []);
      byPerson.get(r.person_id).push({id: n.id, role: r.role});
    }
  }
  return {byPerson, byEntry};
}
/* Greedy neighbours: start from the largest set and keep appending the one whose people overlap
   most with the previous one, so neighbours on a ring share people. */
function chain(pool, sets) {
  const overlap = (a, b) => { let n = 0; for (const p of sets.get(a)) if (sets.get(b).has(p)) n++; return n / (1 + sets.get(a).size + sets.get(b).size - n); };
  const order = [];
  pool = [...pool];
  if (!pool.length) return order;
  let cur = pool.reduce((a, b) => sets.get(b).size > sets.get(a).size ? b : a);
  pool.splice(pool.indexOf(cur), 1); order.push(cur);
  while (pool.length) {
    const next = pool.reduce((a, b) => overlap(b, cur) > overlap(a, cur) ? b : a);
    pool.splice(pool.indexOf(next), 1); order.push(next); cur = next;
  }
  return order;
}
/* Ring order: layers in dataset order; inside a layer, neighbours share people. */
export function ringOrder(graph, byEntry) {
  const sets = new Map([...byEntry].map(([id, rows]) => [id, new Set(rows.map(r => r.id))]));
  return graph.layers.flatMap(layer => chain(graph.nodes.filter(n => n.layer === layer.id && byEntry.has(n.id) && !NOT_A_RING.has(n.entry_type)).map(n => n.id), sets));
}
const hash = s => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return ((h >>> 0) % 1000) / 1000; };

/* Label metrics, shared with the tests: the renderer draws at these sizes (styles.css). */
export const ENTRY_CHAR = 6, ENTRY_LINE = 12.5;      /* rotated entry labels, 11px sans */
export const FAMILY_CHAR = 8, FAMILY_LINE = 15;      /* family labels, 12.5px semibold sans */
export const NAME_CHAR = 6.2, NAME_H = 12;           /* person names, 10.5px serif */

/* Fit a label into at most `maxLines` lines of `maxChars`: wrap on spaces; if it still does not
   fit, drop a subtitle after a slash or colon; then cut on a word boundary. The full label stays
   in the accessible name. */
export function fitLabel(label, maxChars, maxLines = 1) {
  const wrap = text => { const lines = []; let cur = '';
    for (const w of text.split(' ')) { if (!cur) cur = w; else if (cur.length + 1 + w.length <= maxChars) cur += ` ${w}`; else { lines.push(cur); cur = w; } }
    return cur ? [...lines, cur] : lines; };
  const fits = lines => lines.length <= maxLines && lines.every(l => l.length <= maxChars);
  let lines = wrap(label);
  if (!fits(lines)) { const short = label.split(/\s[/:]\s|:\s/)[0]; if (short !== label) lines = wrap(short); }
  if (fits(lines)) return lines;
  const cut = l => `${l.slice(0, maxChars - 1).replace(/\s+\S*$/, '') || l.slice(0, maxChars - 1)}…`;
  lines = lines.slice(0, maxLines).map(l => l.length > maxChars ? cut(l) : l);
  const last = lines.at(-1);
  if (!last.endsWith('…')) lines[lines.length - 1] = last.length + 1 <= maxChars ? `${last}…` : cut(last);
  return lines;
}

/* Dots go down one at a time on a sunflower spiral around their target, each at the first spot
   that clears every dot already placed and stays within `limit` of the centre. Deterministic and
   overlap-free; a target that is already free keeps its exact position. */
function packer(cx, cy, limit, gap = 1.2) {
  const cell = 12, grid = new Map(); let maxR = 0;
  const free = (x, y, r) => {
    const reach = Math.ceil((r + maxR + gap) / cell), ci = Math.floor(x / cell), cj = Math.floor(y / cell);
    for (let i = ci - reach; i <= ci + reach; i++) for (let j = cj - reach; j <= cj + reach; j++)
      for (const d of grid.get(`${i},${j}`) || []) if (Math.hypot(d.x - x, d.y - y) < d.r + r + gap) return false;
    return true;
  };
  const add = (x, y, r) => { const k = `${Math.floor(x / cell)},${Math.floor(y / cell)}`;
    if (!grid.has(k)) grid.set(k, []); grid.get(k).push({x, y, r}); maxR = Math.max(maxR, r); };
  const place = (tx, ty, r) => {
    const c = (2 * r + gap) * 0.56;
    for (let k = 0; k < 6000; k++) {
      const x = tx + c * Math.sqrt(k) * Math.cos(k * 2.39996), y = ty + c * Math.sqrt(k) * Math.sin(k * 2.39996);
      if (Math.hypot(x - cx, y - cy) + r <= limit && free(x, y, r)) { add(x, y, r); return {x, y}; }
    }
    // A dense roster can leave gaps that the coarse target spiral skips. Search the
    // whole disc at finer spacing before giving up the preferred neighbourhood.
    const step = Math.max(1, r / 2);
    for (let y = cy - limit + r; y <= cy + limit - r; y += step)
      for (let x = cx - limit + r; x <= cx + limit - r; x += step)
        if (Math.hypot(x - cx, y - cy) + r <= limit && free(x, y, r)) { add(x, y, r); return {x, y}; }
    add(tx, ty, r); return {x: tx, y: ty};
  };
  return {add, place};
}

/* A few names, greedily: `rank` orders the candidates; each name goes right of its dot, or else
   left, and only where it clears every dot, every name already placed and every `blocked` box,
   with all four corners within `limit` of the centre. Anyone unnamed is still named on hover,
   in the panel and in the register. */
function nameLabels(people, names, rank, blocked, size, limit) {
  const hit = (b, c) => b[0] < c[2] && c[0] < b[2] && b[1] < c[3] && c[1] < b[3];
  const boxes = [...blocked], dots = people.map(p => [p.x - p.r, p.y - p.r, p.x + p.r, p.y + p.r]), out = [];
  const inside = b => [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]].every(([x, y]) => Math.hypot(x - size / 2, y - size / 2) <= limit);
  for (const p of people.filter(p => rank(p) > 0).sort((a, b) => rank(b) - rank(a) || names.get(a.id).localeCompare(names.get(b.id)))) {
    const text = names.get(p.id), w = text.length * NAME_CHAR;
    for (const side of ['start', 'end']) {
      const x0 = side === 'start' ? p.x + p.r + 3 : p.x - p.r - 3 - w;
      const box = [x0, p.y - NAME_H / 2, x0 + w, p.y + NAME_H / 2], pad = [x0 - 2, box[1] - 1, box[2] + 2, box[3] + 1];
      if (!inside(box) || boxes.some(b => hit(b, pad)) || dots.some((d, i) => people[i] !== p && hit(d, pad))) continue;
      boxes.push(box); out.push({id: p.id, text, x: side === 'start' ? x0 : x0 + w, y: p.y, anchor: side, box});
      break;
    }
  }
  return out;
}

/* The drawing's own extent, so a ring of one or two entries is not set in an empty square. */
function frame(boxes, pad = 8) {
  const x0 = Math.min(...boxes.map(b => b[0])) - pad, y0 = Math.min(...boxes.map(b => b[1])) - pad;
  return {x: x0, y: y0, w: Math.max(...boxes.map(b => b[2])) + pad - x0, h: Math.max(...boxes.map(b => b[3])) + pad - y0};
}

/* One ring of entries (`order`) and the people they name. A person named in one of them gathers
   at that entry; a person named in several is drawn near the plain mean of their positions,
   pulled toward the ring so that pairs do not all collapse onto the centre, at the first spot
   free of other dots. `byPerson` and `byEntry` stay the whole atlas's, for the panel and register. */
function ringLayout(graph, width, order, {byPerson, byEntry}, {dotScale = 0.0021, ownScale = 0.0033, labelShare = 0.19, maxSlots = Infinity, rank} = {}) {
  const size = Math.max(560, Math.round(width));
  const labelSpace = Math.min(250, Math.max(96, size * labelShare));
  const R = size / 2 - labelSpace - 14;
  const cx = size / 2, cy = size / 2;
  /* The first entry at the top; one or two entries sit at the sides so their labels read flat,
     and a few are turned half a step so none stands upright. */
  const start = order.length <= 2 ? 0 : -Math.PI / 2 + (order.length <= 4 ? Math.PI / order.length : 0);
  const angle = new Map(order.map((id, i) => [id, start + 2 * Math.PI * i / order.length]));
  const nodes = new Map(graph.nodes.map(n => [n.id, n]));
  const owners = new Set((graph.people || []).filter(p => p.node_id).map(p => p.id));
  /* Up to three label lines, only as many as the gap between neighbouring anchors holds. */
  const maxLines = Math.max(1, Math.min(3, Math.floor((2 * Math.PI * (R + 16) / Math.max(order.length, 1) - 2) / ENTRY_LINE)));
  const anchors = order.map(id => { const count = byEntry.get(id).length;
    const room = Math.floor((labelSpace - 6 - (String(count).length + 1) * 5.5) / ENTRY_CHAR);
    return {id, angle: angle.get(id), x: cx + R * Math.cos(angle.get(id)), y: cy + R * Math.sin(angle.get(id)),
      layer: nodes.get(id).layer, label: nodes.get(id).label, count, lines: fitLabel(nodes.get(id).label, room, maxLines)}; });
  const pos = new Map(anchors.map(a => [a.id, a]));
  const on = new Set(order);
  const entriesOf = new Map([...byPerson].map(([pid, rows]) => [pid, [...new Set(rows.map(r => r.id))].filter(id => on.has(id))]).filter(([, ids]) => ids.length));
  const singles = new Map();   /* entry -> ordered ids of its single-entry people */
  for (const [pid, ids] of entriesOf) if (ids.length === 1) { if (!singles.has(ids[0])) singles.set(ids[0], []); singles.get(ids[0]).push(pid); }
  /* Single-entry people pack into short rows just inside their entry, never overlapping:
     each row holds as many dots as fit in the gap between neighbouring anchors at its own
     radius, and the rows step inward, so a large roster reads as a short tail pointing at
     the centre. */
  const dot = size * dotScale + 1, ownDot = size * ownScale + 1.6, step = Math.max(dot * 2.7, ownDot * 2 + 1.2);
  const innerR = R - size * 0.04;
  const slotsAt = r => Math.min(maxSlots, Math.max(1, Math.floor((2 * Math.PI * r / order.length) / step) - 1));
  const pk = packer(cx, cy, R - 6);
  const people = [];
  const person = (pid, ids, x, y, r) => ({id: pid, x, y, r, entries: ids, roles: [...new Set(byPerson.get(pid).filter(row => on.has(row.id)).map(row => row.role))],
    single: ids.length === 1, own: owners.has(pid), layer: ids.length === 1 ? nodes.get(ids[0]).layer : ''});
  for (const [id, list] of singles) {
    for (let k = 0, row = 0; k < list.length; row++) {
      const r = Math.max(innerR - row * step, 2 * step), inRow = Math.min(slotsAt(r), list.length - k);
      for (let col = 0; col < inRow; col++, k++) {
        /* A tail long enough to reach another near the centre steps aside to the nearest free spot. */
        const pid = list[k], a = angle.get(id) + (col - (inRow - 1) / 2) * (step / r), rad = owners.has(pid) ? ownDot : dot;
        const {x, y} = pk.place(cx + r * Math.cos(a), cy + r * Math.sin(a), rad);
        people.push(person(pid, [id], x, y, rad));
      }
    }
  }
  const multi = [...entriesOf].filter(([, ids]) => ids.length > 1).sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
  for (const [pid, ids] of multi) {
    const mx = ids.reduce((s, id) => s + pos.get(id).x, 0) / ids.length;
    const my = ids.reduce((s, id) => s + pos.get(id).y, 0) / ids.length;
    const pull = ids.length === 2 ? 0.6 : ids.length === 3 ? 0.72 : 0.85;
    const j = size * 0.006, rad = owners.has(pid) ? ownDot : dot;
    const {x, y} = pk.place(cx + (mx - cx) * pull + (hash(pid) - 0.5) * 2 * j, cy + (my - cy) * pull + (hash(pid + '|y') - 0.5) * 2 * j, rad);
    people.push(person(pid, ids, x, y, rad));
  }
  const names = new Map((graph.people || []).map(p => [p.id, p.label]));
  const labels = nameLabels(people, names, rank || (p => p.own && p.entries.length >= 4 ? p.entries.length : 0), [], size, R - 8);
  /* Each rotated label as a box: it runs out along its radius, as thick as its lines. */
  for (const a of anchors) {
    const w = Math.max(...a.lines.map(l => l.length)) * ENTRY_CHAR + (String(a.count).length + 1) * 5.5, t = a.lines.length * ENTRY_LINE / 2;
    const c = Math.cos(a.angle), s = Math.sin(a.angle);
    const corners = [R + 16, R + 16 + w].flatMap(d => [-t, t].map(o => [cx + d * c - o * s, cy + d * s + o * c]));
    a.box = [Math.min(...corners.map(k => k[0])), Math.min(...corners.map(k => k[1])), Math.max(...corners.map(k => k[0])), Math.max(...corners.map(k => k[1]))];
  }
  const view = frame([...anchors.map(a => a.box), ...people.map(p => [p.x - p.r - 2, p.y - p.r - 2, p.x + p.r + 2, p.y + p.r + 2]), ...labels.map(l => l.box)]);
  return {size, cx, cy, R, labelSpace, anchors, people, labels, byPerson, byEntry, order, view};
}

export function companyLayout(graph, width) {
  const {byPerson, byEntry} = membership(graph);
  return {kind: 'all', ...ringLayout(graph, width, ringOrder(graph, byEntry), {byPerson, byEntry})};
}

/* ---------------- Families: the two-level company view ----------------
   The twelve editorial families of the landing (evidence.families) organise the people view.
   Families are read by primary membership: each roster entry belongs to exactly one, and a
   person belongs to every family whose entries name them. A bridged entry is drawn inside its
   second family too, marked, but never counted there. */
export function familyIndex(graph, block) {
  const {byPerson, byEntry} = membership(graph);
  const families = (block?.families || []).map(f => ({id: f.id, label: f.label,
    entries: f.members.filter(m => m.primary && byEntry.has(m.id) && ringEntry(graph, m.id)).map(m => m.id),
    bridged: f.members.filter(m => !m.primary && byEntry.has(m.id) && ringEntry(graph, m.id)).map(m => m.id)})).filter(f => f.entries.length);
  const primaryOf = new Map(families.flatMap(f => f.entries.map(id => [id, f.id])));
  const familiesOf = new Map([...byPerson].map(([pid, rows]) => { const mine = new Set(rows.map(r => primaryOf.get(r.id)));
    return [pid, families.filter(f => mine.has(f.id)).map(f => f.id)]; }));
  for (const f of families) f.people = [...familiesOf].filter(([, fs]) => fs.includes(f.id)).map(([pid]) => pid);
  return {families, primaryOf, familiesOf, byPerson, byEntry};
}

/* Level one: the families on a ring, each a disc whose area is the number of people its entries
   name. Only people named in two or more families are drawn, packed around the mean of those
   families' positions (pulled slightly toward the centre); single-family people are counted at
   their family, not drawn. Labels sit horizontally outside the disc: beside it on the sides,
   above or below it at the top and bottom. */
export function familyOverviewLayout(graph, block, width) {
  const size = Math.max(560, Math.round(width));
  const index = familyIndex(graph, block);
  const {families, familiesOf, byPerson, byEntry} = index;
  const byId = new Map(families.map(f => [f.id, f]));
  const order = chain(families.map(f => f.id), new Map(families.map(f => [f.id, new Set(f.people)])));
  /* Room beside a side disc for the longest single word of a family label ("Historiography"). */
  const labelSpace = Math.min(210, Math.max(134, size * 0.21));
  const R = size / 2 - labelSpace - 10, cx = size / 2, cy = size / 2;
  const most = Math.max(1, ...families.map(f => f.people.length));
  const rMax = Math.min(size * 0.034, R * Math.sin(Math.PI / Math.max(order.length, 3)) * 0.5);
  const anchors = order.map((id, i) => {
    const f = byId.get(id), angle = 2 * Math.PI * i / order.length - Math.PI / 2;
    const x = cx + R * Math.cos(angle), y = cy + R * Math.sin(angle);
    const r = 5 + (rMax - 5) * Math.sqrt(f.people.length / most);
    const c = Math.cos(angle), side = c > 0.3 ? 'start' : c < -0.3 ? 'end' : 'middle';
    const lx = side === 'start' ? x + r + 8 : side === 'end' ? x - r - 8 : x;
    /* Wrap within the room to the chart's edge, and never wider than 22 characters a line. */
    const room = side === 'start' ? size - 4 - lx : side === 'end' ? lx - 4 : 2 * Math.min(lx, size - lx) - 8;
    const lines = [...fitLabel(f.label, Math.min(22, Math.floor(room / FAMILY_CHAR)), 3), `${f.people.length} people`];
    const w = Math.max(...lines.map(l => l.length)) * FAMILY_CHAR, h = lines.length * FAMILY_LINE;
    const top = side !== 'middle' ? y - h / 2 : Math.sin(angle) < 0 ? y - r - 6 - h : y + r + 6;
    const left = side === 'start' ? lx : side === 'end' ? lx - w : lx - w / 2;
    return {id, label: f.label, angle, x, y, r, count: f.people.length, entries: f.entries.length, bridged: f.bridged.length,
      shared: f.people.filter(p => familiesOf.get(p).length > 1).length, lines, lx, top, anchor: side, box: [left, top, left + w, top + h]};
  });
  const pos = new Map(anchors.map(a => [a.id, a]));
  const owners = new Set((graph.people || []).filter(p => p.node_id).map(p => p.id));
  const limit = R - rMax - 4;
  let dot = size * 0.0032 + 1.6, ownDot = size * 0.0046 + 2.2;
  // More standalone biographies enlarge their dots. Keep room between all people
  // on small screens as the roster grows, while retaining the two relative sizes.
  const area = [...familiesOf].filter(([, fs]) => fs.length > 1)
    .reduce((sum, [pid]) => sum + (owners.has(pid) ? ownDot : dot) ** 2, 0);
  const densityScale = Math.min(1, Math.sqrt(0.25 * limit ** 2 / Math.max(1, area)));
  dot *= densityScale; ownDot *= densityScale;
  const pk = packer(cx, cy, limit);
  const groups = new Map();
  for (const [pid, fs] of familiesOf) if (fs.length > 1) { const key = fs.join('|'); if (!groups.has(key)) groups.set(key, []); groups.get(key).push(pid); }
  const entryCount = pid => new Set(byPerson.get(pid).map(r => r.id)).size;
  const people = [];
  for (const [key, ids] of [...groups].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))) {
    const fs = key.split('|');
    const mx = fs.reduce((s, id) => s + pos.get(id).x, 0) / fs.length, my = fs.reduce((s, id) => s + pos.get(id).y, 0) / fs.length;
    const tx = cx + (mx - cx) * 0.8, ty = cy + (my - cy) * 0.8;
    for (const pid of ids.sort((a, b) => entryCount(b) - entryCount(a) || a.localeCompare(b))) {
      const r = owners.has(pid) ? ownDot : dot, {x, y} = pk.place(tx, ty, r);
      people.push({id: pid, x, y, r, families: fs, entries: [...new Set(byPerson.get(pid).map(row => row.id))],
        roles: [...new Set(byPerson.get(pid).map(row => row.role))], own: owners.has(pid), single: false});
    }
  }
  const names = new Map((graph.people || []).map(p => [p.id, p.label]));
  const discs = anchors.map(a => [a.x - a.r, a.y - a.r, a.x + a.r, a.y + a.r]);
  const labels = nameLabels(people, names, p => p.families.length >= 3 || p.own ? p.families.length * 10 + p.entries.length : 0,
    [...anchors.map(a => a.box), ...discs], size, R - rMax);
  const view = frame([...anchors.map(a => a.box), ...discs, ...people.map(p => [p.x - p.r - 2, p.y - p.r - 2, p.x + p.r + 2, p.y + p.r + 2]), ...labels.map(l => l.box)]);
  return {kind: 'overview', size, cx, cy, R, labelSpace, anchors, people, labels, byPerson, byEntry, index, order, view};
}

/* Level two: one family's ring. Its own entries first, then the entries it shares with another
   family (bridged, marked); the people they name, laid out as the full ring lays out everyone.
   `elsewhere` lists each person's other families. */
export function familyCompanyLayout(graph, block, familyId, width) {
  const index = familyIndex(graph, block);
  const family = index.families.find(f => f.id === familyId);
  if (!family) return null;
  const pick = ids => new Map(ids.map(id => [id, index.byEntry.get(id)]));
  const order = [...ringOrder(graph, pick(family.entries)), ...ringOrder(graph, pick(family.bridged))];
  const L = ringLayout(graph, width, order, index, {dotScale: 0.0032, ownScale: 0.0045, labelShare: 0.23, maxSlots: 9,
    rank: p => p.own && p.entries.length >= 2 ? p.entries.length + 1 : p.entries.length >= 3 ? p.entries.length : 0});
  const bridged = new Set(family.bridged);
  for (const a of L.anchors) { a.bridged = bridged.has(a.id); a.home = a.bridged ? index.primaryOf.get(a.id) : family.id; }
  for (const p of L.people) p.elsewhere = index.familiesOf.get(p.id).filter(f => f !== family.id);
  return {kind: 'family', ...L, family, index};
}
/* People named in the most entries, for the panel's opening list. */
export function bridges(graph, byPerson, limit = 8) {
  const names = new Map(graph.people.map(p => [p.id, p.label]));
  return [...byPerson].map(([id, rows]) => ({id, label: names.get(id), count: new Set(rows.map(r => r.id)).size}))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label)).slice(0, limit);
}
