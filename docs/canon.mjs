/* Canon map: the people History PhDs cite, linked by co-citation. Loaded only when opened.
   Data: data/dissertations/canon-map.json, exported by scripts/export_canon_map.py from the
   research page that scripts/historian_cocitation_network.py builds. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = n => Number(n).toLocaleString('en');
const NS = 'http://www.w3.org/2000/svg', S = 1000;
const X = v => v * S * 0.46 + S / 2, Y = X;
const REGION_LABELS = {CA: 'Canada', US: 'United States', GB: 'Britain', BR: 'Brazil', EU: 'Rest of Europe'};
// Sub-graph maps (2026-11-03): one data file per scope; `scope` in the hash picks one (#tab=canon&scope=BR).
const SCOPE_LABELS = {main: 'All countries', BR: 'Brazil', CA: 'Canada', GB: 'Britain', US: 'United States'};
const scopeOf = hash => { const s = new URLSearchParams(hash.replace(/^#/, '')).get('scope'); return s in SCOPE_LABELS ? s : 'main'; };
const loads = {};
// no-cache: revalidate with the server, so a cached older data file never meets newer code
const getData = scope => loads[scope] ||= fetch(scope === 'main' ? 'data/dissertations/canon-map.json' : `data/dissertations/canon-map-${scope}.json`, {cache: 'no-cache', signal: AbortSignal.timeout(20000)})
  .then(r => { if (!r.ok) throw new Error('The canon map could not be loaded.'); return r.json(); })
  .catch(e => { delete loads[scope]; throw e; });

const minCoSteps = data => [...new Set([data.min_co, 10, 20, 30, 50, 100, 200])].filter(v => v >= data.min_co).sort((a, b) => a - b);

export const isCanonHash = hash => new URLSearchParams(hash.replace(/^#/, '')).get('tab') === 'canon';

function shell(data) {
  const local = data.scope && data.scope !== 'main';
  const leans = Object.entries(data.leans).map(([k, v]) => `<span class="canon-key ${k}">${esc(v)}</span>`).join('');
  return `<div class="section-heading"><div><p class="eyebrow">THE READING RECORD · RESEARCH PREVIEW</p><h2>Canon map</h2></div></div>
    <p class="reading-intro">Who do doctoral historians cite together? Each circle is a person cited in History PhD bibliographies; two people are linked when the same theses cite them both. Raise the threshold to keep only the most cited, or switch the links to find the fields hidden behind the famous names.</p>
    <p class="reading-scope">${fmt(data.theses)} History PhDs ${local ? `from ${esc(SCOPE_LABELS[data.scope])} only` : 'from Canada, the United States, Britain, Brazil and elsewhere'} · ${fmt(data.nodes.length)} people cited by at least ${fmt(data.steps[0])} of them · build of ${esc(data.snapshot)}</p>
    <div class="canon-controls">
      ${(data.scopes || []).length > 1 ? `<label>Theses from <select class="canon-scope">${data.scopes.map(s => `<option value="${esc(s)}"${s === (data.scope || 'main') ? ' selected' : ''}>${esc(SCOPE_LABELS[s] || s)}</option>`).join('')}</select></label>` : ''}
      <label>Cited by at least <input type="range" class="canon-threshold" min="0" max="${data.steps.length - 1}" step="1" aria-valuetext=""> <output class="canon-threshold-value"></output></label>
      <label>Links <select class="canon-measure"><option value="raw">Co-citation count: the core and its hubs</option><option value="assoc">Association strength: fields and neighbours</option></select></label>
      <label>Links per person <select class="canon-top">${[5, 10, 25].map(k => `<option value="${k}"${k === data.keep ? ' selected' : ''}>Top ${k}</option>`).join('')}</select></label>
      <label>Cited together by at least <input type="range" class="canon-minco" min="0" max="${minCoSteps(data).length - 1}" step="1" value="0" aria-valuetext=""> <output class="canon-minco-value"></output></label>
      <label class="canon-find-label">Find a person <input type="search" class="canon-find" list="canon-names" autocomplete="off" placeholder="Try Thompson, Innis, Foucault"></label><datalist id="canon-names"></datalist>
      <span class="canon-buttons"><button type="button" data-zoom="in" aria-label="Zoom in">+</button><button type="button" data-zoom="out" aria-label="Zoom out">−</button><button type="button" class="canon-fit">Fit</button><button type="button" class="canon-relayout">Reset positions</button></span>
    </div>
    <div class="canon-legend" aria-label="Colours">${leans}<span class="canon-key NOQ">No reviewed Wikidata identity</span><span>Circle size: theses citing the person</span></div>
    <div class="canon-stage"><svg class="canon-svg" role="img" aria-label="Co-citation map of cited people. The strongest pairs are listed in the table below the map."><g class="canon-vp"></g></svg><div class="canon-tip" hidden></div></div>
    <p class="fine-print canon-help">Drag to pan, Ctrl or ⌘ + scroll (or pinch) to zoom, drag a person to move them. Hover or select a person to see who they are most often cited with.</p>
    <section class="canon-detail" aria-live="polite"><p class="context-note">Select a person on the map, or find one above, to see their citation profile.</p></section>
    <details class="reading-coverage canon-pairs"><summary>The strongest co-citations among the people shown</summary><div class="reading-table-scroll" tabindex="0" role="region" aria-label="Strongest co-citations"><table><caption>Pairs of people cited by the same theses</caption><thead><tr><th scope="col">Pair</th><th scope="col">Theses citing both</th><th scope="col">Theses citing the first</th><th scope="col">Theses citing the second</th></tr></thead><tbody></tbody></table></div></details>
    <details class="reading-coverage"><summary>How to read this map</summary>
      <p><strong>Co-citation count</strong> is the number of theses whose bibliographies cite both people (any of their works). It grows with fame, so the most cited theorists become hubs and the map shows the canon's core and its reach. <strong>Association strength</strong> divides that count by what the two people's citation counts would give by chance, so people sit with those who share their readers. That brings out fields rather than fame.</p>
      <p>Almost every pair of well-cited people is cited together somewhere, so the lines are a selection. Each person draws their strongest links among the people shown (<strong>Links per person</strong>: top 5, 10 or 25), counting only pairs that at least the chosen number of theses cite together (<strong>Cited together by at least</strong>). A line appears when either person picks it, so much-cited people collect more than their share. A missing line means the two are not among each other's strongest partners, not that no thesis cites both. Top 25 is offered from ${fmt(Object.entries(data.link_top).filter(([, k]) => k >= 25).map(([t]) => +t).sort((a, b) => a - b)[0] ?? 0)} theses up; at lower thresholds a full set would run to tens of thousands of lines. With association strength and a high minimum, a person's picks come from their ${fmt(Math.max(...Object.values(data.link_top)))} strongest partners, so a few weaker qualifying pairs can be missed.</p>
      <p>The positions come from a spring layout of each person's ${fmt(data.keep)} strongest links, computed once for each threshold and kept when you change the link controls, so the axes mean nothing. People with no link to the main map at a threshold are not drawn.</p>
      ${local ? `<p><strong>This map</strong> counts and links people within the ${fmt(data.theses)} History PhDs from ${esc(SCOPE_LABELS[data.scope])} only, so its thresholds start lower than the all-countries map's. Colours and the regional shares still compare every country's theses.</p>` : ''}
      <p><strong>Colour</strong> marks where a person is read. A person leans to a region when the share of its History PhDs citing them is at least 1.5 times the next region's; otherwise they are shared. The regions hold different numbers of theses (${Object.entries(data.region_theses || {}).map(([k, n]) => `${esc(REGION_LABELS[k] || k)} ${fmt(n)}`).join(', ')}). Coverage depends on which repositories release full texts, so these are samples, not censuses.</p>
      <p><strong>People</strong> are the first authors of cited works as the citation graph resolves them. Namesakes are split through their cited titles where reviewed. Hollow circles have no reviewed Wikidata identity: most are real historians, but a common name can merge namesakes. Stray tokens, government bodies and initial-only names are left out. A citation records use, not agreement or influence. Life years come from Library of Congress name authorities, Wikidata and the atlas's sourced reviews; birth years are shown only for people who have died.</p>
      <p>This map uses a newer build of the dissertation graph than the dated release behind <a href="#tab=dissertations">Dissertation reading</a>, so counts can differ between the two. <a href="https://github.com/jburnford/historiography/blob/main/scripts/historian_cocitation_network.py" target="_blank" rel="noopener noreferrer">Method and code →</a></p>
    </details>`;
}

export async function mountCanon(root, scope = scopeOf(location.hash)) {
  if (!root) return;
  root.innerHTML = '<p class="loading" role="status">Loading the canon map…</p>';
  let data;
  try { data = await getData(scope); } catch {
    if (root.isConnected) { root.innerHTML = '<p role="status">The canon map could not be loaded. <button type="button" data-canon-retry>Try again</button></p>'; root.querySelector('button').onclick = () => mountCanon(root, scope); }
    return;
  }
  if (!root.isConnected) return;
  try { build(root, upgrade(data)); } catch (e) {
    // a failure while drawing must not leave the page on "Loading"
    console.error(e);
    root.innerHTML = '<p role="status">The canon map could not be drawn. <button type="button" data-canon-retry>Try again</button></p>';
    root.querySelector('button').onclick = () => { delete loads[scope]; mountCanon(root, scope); };
  }
}

// Data files before the link controls (2026-10-31) carry fixed top-5 lines (`views[].edges`) and their pair
// counts (`co`) instead of candidate links; read them as candidate links with top 5 as the only choice.
function upgrade(data) {
  if (data.links) return data;
  const links = Object.entries(data.co || {}).flatMap(([k, v]) => [...k.split(',').map(Number), v]);
  return {...data, links, keep: 5, min_co: 5, link_top: Object.fromEntries(data.steps.map(t => [t, 5]))};
}

function build(root, data) {
  root.innerHTML = shell(data);
  const $ = s => root.querySelector(s);
  const scopeSel = $('.canon-scope');
  if (scopeSel) scopeSel.onchange = () => {
    const p = new URLSearchParams(location.hash.replace(/^#/, ''));
    if (scopeSel.value === 'main') p.delete('scope'); else p.set('scope', scopeSel.value);
    history.replaceState(history.state, '', `#${p}`);
    mountCanon(root, scopeSel.value);
  };
  const N = data.nodes, svg = $('.canon-svg'), vp = $('.canon-vp'), tip = $('.canon-tip'), thr = $('.canon-threshold'), measure = $('.canon-measure'), find = $('.canon-find');
  const topSel = $('.canon-top'), minco = $('.canon-minco'), MINCO = minCoSteps(data);
  // candidate links: (a, b, theses citing both) triples; each person's list of [partner, count]
  const coMap = new Map(), partners = N.map(() => []);
  for (let i = 0; i < data.links.length; i += 3) {
    const a = data.links[i], b = data.links[i + 1], c = data.links[i + 2];
    coMap.set(a * 100000 + b, c); partners[a].push([b, c]); partners[b].push([a, c]);
  }
  thr.value = Math.max(0, data.steps.indexOf(data.default));
  const nameOf = n => n.label || n.name;
  const byName = new Map(N.map((n, i) => [nameOf(n), i]));
  $('#canon-names').innerHTML = [...byName.keys()].sort().map(s => `<option value="${esc(s)}">`).join('');
  const radius = n => 2 + Math.sqrt(n.cited) * 0.36;
  const co = (a, b) => coMap.get(Math.min(a, b) * 100000 + Math.max(a, b)) || 0;
  const strength = (a, b) => measure.value === 'raw' ? co(a, b) : co(a, b) / (N[a].cited * N[b].cited);
  const moved = {};
  let cur = null, curKey = '', pos = {}, nbr = {}, nodeEls = {}, labelEls = {}, labelLayer = null, linkLayer = null, view = {x: 0, y: 0, w: S, h: S}, selected = null;

  function linksFor(ids, k, m) {
    // each shown person's k strongest partners among the shown, pairs cited together by at least m theses
    const shown = new Set(ids), out = new Map();
    for (const a of ids) {
      const best = partners[a].filter(([b, c]) => c >= m && shown.has(b)).map(([b]) => [strength(a, b), b]).sort((x, y) => y[0] - x[0]).slice(0, k);
      for (const [, b] of best) out.set(Math.min(a, b) * 100000 + Math.max(a, b), [Math.min(a, b), Math.max(a, b)]);
    }
    return [...out.values()];
  }
  function draw(refit = true) {
    const t = data.steps[+thr.value], key = `${t}-${measure.value}`, mv = moved[key] ||= {};
    cur = data.views[key]; curKey = key;
    const most = data.link_top[t];
    for (const o of topSel.options) o.disabled = +o.value > most;
    if (+topSel.value > most) topSel.value = String([...topSel.options].filter(o => !o.disabled).pop().value);
    $('.canon-threshold-value').textContent = `${t} theses (${fmt(cur.ids.length)} people)`;
    thr.setAttribute('aria-valuetext', `${t} theses, ${cur.ids.length} people`);
    vp.textContent = ''; pos = {}; nodeEls = {};
    cur.ids.forEach((i, j) => { pos[i] = mv[i] || cur.xy[j]; });
    linkLayer = document.createElementNS(NS, 'g'); linkLayer.setAttribute('class', 'canon-links'); vp.appendChild(linkLayer);
    const nodes = document.createDocumentFragment();
    for (const i of [...cur.ids].sort((a, b) => N[a].cited - N[b].cited)) {
      const n = N[i], g = document.createElementNS(NS, 'g'), c = document.createElementNS(NS, 'circle');
      g.setAttribute('class', `canon-node ${n.lean}${n.qid ? '' : ' noq'}`); g.dataset.i = i;
      c.setAttribute('cx', X(pos[i][0])); c.setAttribute('cy', Y(pos[i][1])); c.setAttribute('r', radius(n).toFixed(1));
      g.appendChild(c); nodes.appendChild(g); nodeEls[i] = g;
    }
    vp.appendChild(nodes);
    labelLayer = document.createElementNS(NS, 'g'); labelLayer.setAttribute('class', 'canon-labels'); vp.appendChild(labelLayer);
    drawLinks();
    if (refit) fit(); else setView();
  }
  // The link controls change only the lines: rebuild the link layer, not the circles and labels.
  function drawLinks() {
    const m = MINCO[+minco.value];
    cur.edges = linksFor(cur.ids, +topSel.value, m);
    $('.canon-minco-value').textContent = `${fmt(m)} theses (${fmt(cur.edges.length)} lines)`;
    minco.setAttribute('aria-valuetext', `${m} theses, ${cur.edges.length} lines`);
    nbr = {};
    cur.ids.forEach(i => { nbr[i] = []; });
    const wmax = Math.max(1e-12, ...cur.edges.map(([a, b]) => strength(a, b)));
    const lines = document.createDocumentFragment();
    for (const [a, b] of cur.edges) {
      const l = document.createElementNS(NS, 'line');
      l.setAttribute('class', 'canon-link'); l._a = a;
      l.setAttribute('x1', X(pos[a][0])); l.setAttribute('y1', Y(pos[a][1])); l.setAttribute('x2', X(pos[b][0])); l.setAttribute('y2', Y(pos[b][1]));
      l.setAttribute('stroke-width', (0.3 + 2.2 * Math.sqrt(strength(a, b) / wmax)).toFixed(2));
      nbr[a].push([b, l]); nbr[b].push([a, l]); lines.appendChild(l);
    }
    linkLayer.replaceChildren(lines);
    const rows = [...cur.edges].sort((e, f) => co(f[0], f[1]) - co(e[0], e[1])).slice(0, 150);
    $('.canon-pairs tbody').innerHTML = rows.map(([a, b]) => `<tr><th scope="row">${esc(nameOf(N[a]))} — ${esc(nameOf(N[b]))}</th><td>${fmt(co(a, b))}</td><td>${fmt(N[a].cited)}</td><td>${fmt(N[b].cited)}</td></tr>`).join('');
    if (selected != null && pos[selected]) highlight(selected);
  }
  let relinkFrame = 0;   // a dragged slider fires many input events: redraw the lines at most once a frame
  const relink = () => { if (!relinkFrame) relinkFrame = requestAnimationFrame(() => { relinkFrame = 0; drawLinks(); }); };
  function setView() { svg.setAttribute('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`); labels(); }
  function labels() {
    if (!labelLayer) return;
    labelLayer.textContent = ''; labelEls = {};
    const k = S / view.w, boxes = [], fs = 11 / k;
    for (const i of [...cur.ids].sort((a, b) => N[b].cited - N[a].cited)) {
      const n = N[i], x = X(pos[i][0]) + radius(n) + 2 / k, y = Y(pos[i][1]) + fs * 0.35;
      if (x < view.x || x > view.x + view.w || y < view.y || y > view.y + view.h) continue;
      const t = nameOf(n).length > 30 ? nameOf(n).slice(0, 28) + '…' : nameOf(n), w = t.length * fs * 0.55, b = [x, y - fs, w, fs * 1.2];
      if (boxes.some(o => b[0] < o[0] + o[2] && o[0] < b[0] + b[2] && b[1] < o[1] + o[3] && o[1] < b[1] + b[3])) continue;
      boxes.push(b);
      const e = document.createElementNS(NS, 'text');
      e.setAttribute('x', x); e.setAttribute('y', y); e.style.fontSize = fs.toFixed(2) + 'px'; e.style.strokeWidth = (3 / k).toFixed(2) + 'px';
      e.textContent = t; labelLayer.appendChild(e); labelEls[i] = e;
    }
    if (selected != null) highlight(selected);
  }
  function highlight(i) {
    svg.classList.toggle('focus', i != null);
    Object.values(nodeEls).forEach(g => g.classList.remove('on'));
    Object.values(labelEls).forEach(t => t.classList.remove('on'));
    vp.querySelectorAll('.canon-link.on').forEach(l => l.classList.remove('on'));
    if (i == null || !nodeEls[i]) return;
    nodeEls[i].classList.add('on'); labelEls[i]?.classList.add('on');
    for (const [j, l] of nbr[i]) { nodeEls[j].classList.add('on'); labelEls[j]?.classList.add('on'); l.classList.add('on'); }
  }
  const profile = n => `Cited by ${fmt(n.cited)} theses · ${Object.entries(REGION_LABELS).map(([k, v]) => `${v} ${n.shares[k]}%`).join(' · ')} of each region's theses · ${data.leans[n.lean]}`;
  function showTip(i, e) {
    const n = N[i];
    tip.innerHTML = `<strong>${esc(nameOf(n))}${n.life ? ` <span class="canon-life">${esc(n.life)}</span>` : ''}</strong><span>${esc(profile(n))}</span><ol>${n.top.slice(0, 6).map(([j, v]) => `<li>${esc(nameOf(N[j]))} <b>${fmt(v)}</b></li>`).join('')}</ol>`;
    tip.hidden = false;
    const box = root.querySelector('.canon-stage').getBoundingClientRect();
    tip.style.left = Math.min(e.clientX - box.left + 14, box.width - tip.offsetWidth - 8) + 'px';
    tip.style.top = Math.min(e.clientY - box.top + 14, box.height - tip.offsetHeight - 8) + 'px';
  }
  function select(i) {
    selected = i; highlight(i);
    const box = $('.canon-detail');
    if (i == null) { box.innerHTML = '<p class="context-note">Select a person on the map, or find one above, to see their citation profile.</p>'; return; }
    const n = N[i];
    box.innerHTML = `<p class="eyebrow">CITED PERSON${n.qid ? ` · <a href="https://www.wikidata.org/wiki/${esc(n.qid)}" target="_blank" rel="noopener noreferrer">${esc(n.qid)}</a>` : ''}${n.lc ? ` · <a href="https://id.loc.gov/authorities/names/${esc(n.lc)}.html" target="_blank" rel="noopener noreferrer">LC ${esc(n.lc)}</a>` : ''}</p><h3>${esc(nameOf(n))}${n.life ? ` <span class="canon-life">${esc(n.life)}</span>` : ''}</h3><p>${esc(profile(n))}.</p>
      ${n.reading ? `<p><a href="#tab=dissertations&amp;source=${encodeURIComponent(n.reading)}">Follow this person in Dissertation reading →</a></p>` : ''}
      <h4>Most often cited with</h4><ol class="canon-partners">${n.top.map(([j, v]) => `<li><button type="button" data-canon-person="${j}">${esc(nameOf(N[j]))}</button> <span>${fmt(v)} theses${pos[j] ? '' : ' · not shown at this threshold'}</span></li>`).join('')}</ol>`;
  }
  function goTo(i) {
    // lower the threshold until the person is drawn; someone without links at any step keeps their profile
    for (let k = data.steps.filter(t => t <= N[i].cited).length - 1; !pos[i] && k >= 0; k--) {
      if (+thr.value !== k) { thr.value = k; draw(); }
    }
    if (!pos[i]) { select(i); return; }
    const cx = X(pos[i][0]), cy = Y(pos[i][1]);
    view = {x: cx - view.w / 4, y: cy - view.h / 4, w: view.w / 2, h: view.h / 2}; setView(); select(i);
  }
  function fit() {
    const p = svg.getBoundingClientRect(), a = (p.height || 600) / (p.width || 900);
    const xs = cur.xy.map(q => X(q[0])), ys = cur.xy.map(q => Y(q[1]));
    let x0 = Math.min(...xs) - 30, x1 = Math.max(...xs) + 150, y0 = Math.min(...ys) - 30, y1 = Math.max(...ys) + 30, w = x1 - x0, h = y1 - y0;
    if (h / w > a) { const nw = h / a; x0 -= (nw - w) / 2; w = nw; } else { const nh = w * a; y0 -= (nh - h) / 2; h = nh; }
    view = {x: x0, y: y0, w, h}; setView();
  }
  function zoom(f, mx = view.x + view.w / 2, my = view.y + view.h / 2) {
    view.x = mx - (mx - view.x) * f; view.y = my - (my - view.y) * f; view.w *= f; view.h *= f; setView();
  }
  const toMap = e => { const p = svg.getBoundingClientRect(); return [view.x + (e.clientX - p.left) * view.w / p.width, view.y + (e.clientY - p.top) * view.h / p.height]; };
  let drag = null, nodeDrag = null, travelled = 0;
  vp.addEventListener('pointermove', e => { const g = e.target.closest('.canon-node'); if (g && !drag && nodeDrag == null) { highlight(+g.dataset.i); showTip(+g.dataset.i, e); } });
  vp.addEventListener('pointerout', e => { if (nodeDrag != null || e.relatedTarget?.closest?.('.canon-node')) return; tip.hidden = true; highlight(selected); });
  vp.addEventListener('pointerdown', e => { const g = e.target.closest('.canon-node'); if (!g) return; e.stopPropagation(); nodeDrag = +g.dataset.i; travelled = 0; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener('pointerdown', e => { drag = {x: e.clientX, y: e.clientY, vx: view.x, vy: view.y}; travelled = 0; svg.setPointerCapture(e.pointerId); svg.classList.add('dragging'); });
  svg.addEventListener('pointermove', e => {
    if (nodeDrag != null) {
      travelled++;
      const [px, py] = toMap(e), i = nodeDrag, v = [(px - S / 2) / (S * 0.46), (py - S / 2) / (S * 0.46)];
      pos[i] = v; moved[curKey][i] = v;
      const c = nodeEls[i].firstChild; c.setAttribute('cx', px); c.setAttribute('cy', py);
      for (const [, l] of nbr[i]) { if (l._a === i) { l.setAttribute('x1', px); l.setAttribute('y1', py); } else { l.setAttribute('x2', px); l.setAttribute('y2', py); } }
      const t = labelEls[i]; if (t) { const k = S / view.w; t.setAttribute('x', px + radius(N[i]) + 2 / k); t.setAttribute('y', py + 11 / k * 0.35); }
      tip.hidden = true; return;
    }
    if (!drag) return;
    travelled++;
    const k = view.w / svg.clientWidth; view.x = drag.vx - (e.clientX - drag.x) * k; view.y = drag.vy - (e.clientY - drag.y) * k; setView();
  });
  svg.addEventListener('pointerup', () => {
    if (nodeDrag != null) { const i = nodeDrag; nodeDrag = null; if (travelled < 3) select(i); else labels(); }
    else if (drag && travelled < 3) select(null);
    drag = null; svg.classList.remove('dragging');
  });
  svg.addEventListener('wheel', e => { if (!e.ctrlKey && !e.metaKey) return; e.preventDefault(); zoom(Math.exp(e.deltaY * 0.0015), ...toMap(e)); }, {passive: false});
  root.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => zoom(b.dataset.zoom === 'in' ? 0.7 : 1 / 0.7)));
  let found = '';   // a blur after a picked name fires change again; act once per name
  find.addEventListener('change', () => { const i = byName.get(find.value); if (i != null && find.value !== found) { found = find.value; goTo(i); } });
  root.addEventListener('click', e => { const b = e.target.closest('[data-canon-person]'); if (b) goTo(+b.dataset.canonPerson); });
  thr.addEventListener('input', () => draw()); measure.addEventListener('change', () => draw());
  // the link controls change only the lines: keep the reader's zoom and pan
  topSel.addEventListener('change', relink); minco.addEventListener('input', relink);
  $('.canon-fit').addEventListener('click', fit);
  $('.canon-relayout').addEventListener('click', () => { moved[curKey] = {}; draw(); });
  const observer = new ResizeObserver(() => { if (!root.isConnected) { observer.disconnect(); return; } fit(); });
  observer.observe(svg);
  draw();
}
