/* The company they keep: 830 people placed between the entries that name them.
   Deterministic layout, no force simulation. Entries sit on a ring, grouped by layer and
   ordered so neighbours share people. A person named in one entry gathers at that entry;
   a person named in several entries is drawn at the mean of their positions, pulled toward
   the ring so that pairs do not all collapse onto the centre. Roster membership is shared
   context, never an influence edge: no line is ever drawn between two people. */

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
/* Ring order: layers in dataset order; inside a layer, start from the largest roster and
   keep appending the entry whose people overlap most with the previous one. */
export function ringOrder(graph, byEntry) {
  const sets = new Map([...byEntry].map(([id, rows]) => [id, new Set(rows.map(r => r.id))]));
  const overlap = (a, b) => { let n = 0; for (const p of sets.get(a)) if (sets.get(b).has(p)) n++; return n / (1 + sets.get(a).size + sets.get(b).size - n); };
  const order = [];
  for (const layer of graph.layers) {
    const pool = graph.nodes.filter(n => n.layer === layer.id && byEntry.has(n.id)).map(n => n.id);
    if (!pool.length) continue;
    let cur = pool.reduce((a, b) => sets.get(b).size > sets.get(a).size ? b : a);
    pool.splice(pool.indexOf(cur), 1); order.push(cur);
    while (pool.length) {
      const next = pool.reduce((a, b) => overlap(b, cur) > overlap(a, cur) ? b : a);
      pool.splice(pool.indexOf(next), 1); order.push(next); cur = next;
    }
  }
  return order;
}
const hash = s => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return ((h >>> 0) % 1000) / 1000; };

export function companyLayout(graph, width) {
  const size = Math.max(560, Math.round(width));
  const {byPerson, byEntry} = membership(graph);
  const order = ringOrder(graph, byEntry);
  const labelSpace = Math.min(240, Math.max(96, size * 0.19));
  const R = size / 2 - labelSpace - 14;
  const cx = size / 2, cy = size / 2;
  const angle = new Map(order.map((id, i) => [id, 2 * Math.PI * i / order.length - Math.PI / 2]));
  const nodes = new Map(graph.nodes.map(n => [n.id, n]));
  const anchors = order.map(id => ({id, angle: angle.get(id), x: cx + R * Math.cos(angle.get(id)),
    y: cy + R * Math.sin(angle.get(id)), layer: nodes.get(id).layer, label: nodes.get(id).label, count: byEntry.get(id).length}));
  const pos = new Map(anchors.map(a => [a.id, a]));
  const singles = new Map();   /* entry -> ordered ids of its single-entry people */
  for (const [pid, rows] of byPerson) {
    const ids = [...new Set(rows.map(r => r.id))];
    if (ids.length === 1) { if (!singles.has(ids[0])) singles.set(ids[0], []); singles.get(ids[0]).push(pid); }
  }
  const people = [];
  /* Single-entry people pack into short rows just inside their entry, never overlapping:
     each row holds as many dots as fit in the gap between neighbouring anchors, and the
     rows step inward, so a large roster reads as a short tail pointing at the centre. */
  const dot = size * 0.0021 + 1, step = dot * 2.7;
  const innerR = R - size * 0.04;
  const slots = Math.max(2, Math.floor((2 * Math.PI * innerR / order.length) / step) - 1);
  for (const [pid, rows] of byPerson) {
    const entries = [...new Set(rows.map(r => r.id))];
    const roles = [...new Set(rows.map(r => r.role))];
    let x, y;
    if (entries.length === 1) {
      const list = singles.get(entries[0]); const k = list.indexOf(pid), n = list.length;
      const row = Math.floor(k / slots), inRow = Math.min(slots, n - row * slots), col = k % slots;
      const r = innerR - row * step;
      const a = angle.get(entries[0]) + (col - (inRow - 1) / 2) * (step / r);
      x = cx + r * Math.cos(a); y = cy + r * Math.sin(a);
    } else {
      const mx = entries.reduce((s, id) => s + pos.get(id).x, 0) / entries.length;
      const my = entries.reduce((s, id) => s + pos.get(id).y, 0) / entries.length;
      const pull = entries.length === 2 ? 0.6 : entries.length === 3 ? 0.72 : 0.85;
      const j = size * 0.012;
      x = cx + (mx - cx) * pull + (hash(pid) - 0.5) * 2 * j;
      y = cy + (my - cy) * pull + (hash(pid + '|y') - 0.5) * 2 * j;
    }
    people.push({id: pid, x, y, entries, roles, single: entries.length === 1,
      layer: entries.length === 1 ? nodes.get(entries[0]).layer : ''});
  }
  return {size, cx, cy, R, labelSpace, anchors, people, byPerson, byEntry, order};
}
/* People named in the most entries, for the panel's opening list. */
export function bridges(graph, byPerson, limit = 8) {
  const names = new Map(graph.people.map(p => [p.id, p.label]));
  return [...byPerson].map(([id, rows]) => ({id, label: names.get(id), count: new Set(rows.map(r => r.id)).size}))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label)).slice(0, limit);
}
