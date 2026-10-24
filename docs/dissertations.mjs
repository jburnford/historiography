/* Dissertation reading: frozen, derived metadata, loaded only when requested. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const NAMES = {CA:'Canada', US:'United States', EUROPE:'Europe', OTHER:'Elsewhere'};
const COLORS = ['#356c91', '#b45331', '#52764b', '#796486'];
const fmt = n => Number(n).toLocaleString('en');
const cache = new Map();
const charts = new WeakMap();
const ROOT = 'data/dissertations/';
export const readingHref = key => `#tab=dissertations${key ? `&source=${encodeURIComponent(key)}` : ''}`;
export const isReadingHash = hash => new URLSearchParams(hash.replace(/^#/, '')).get('tab') === 'dissertations'
  && !['node','person','edge','focus','path','pathway','hold','letter','range'].some(k => new URLSearchParams(hash.replace(/^#/, '')).get(k));
async function get(name) {
  if (!cache.has(name)) cache.set(name, fetch(ROOT + name, {signal: AbortSignal.timeout(15000)})
    .then(r => { if (!r.ok) throw new Error('The dissertation data could not be loaded.'); return r.json(); })
    .catch(e => { cache.delete(name); throw e; }));
  return cache.get(name);
}
const publicUrl = url => /^https?:\/\//i.test(url || '') ? url : null;
const sourceLink = (label, text = label.short) => `<a href="${esc(readingHref(label.key))}">${esc(text)}</a>`;
export function share(count, denominator) { return denominator >= 15 ? `${(100 * count / denominator).toFixed(1)}%` : 'Small sample'; }
const table = (caption, heads, body) => `<div class="reading-table-scroll" tabindex="0" role="region" aria-label="${esc(caption)}"><table><caption>${esc(caption)}</caption><thead><tr>${heads.map(h => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`;

export function trendTable(data, source) {
  return table('Dissertations citing, by degree period and region', ['Degree period', ...data.regions.map(r => NAMES[r])],
    data.periods.map((p, i) => `<tr><th scope="row">${esc(p)}</th>${data.regions.map((r,j) => `<td>${share(source.series[i][j], data.denominators[i][j])}<small>${fmt(source.series[i][j])} of ${fmt(data.denominators[i][j])}</small></td>`).join('')}</tr>`).join(''));
}
export function trendChart(data, source, width=880) {
  const W = Math.max(280, Math.min(880, width)), H = 280, left = 42, right = W-20, top = 16, bottom = 230;
  const value = (p, r) => data.denominators[p][r] >= 15 ? 100 * source.series[p][r] / data.denominators[p][r] : null;
  const max = Math.max(1, ...data.periods.flatMap((_,p) => data.regions.map((_,r) => value(p,r) || 0)));
  const ceiling = Math.ceil(max / 4) * 4;
  const x = p => left + p * (right - left) / (data.periods.length - 1), y = v => bottom - (bottom - top) * v / ceiling;
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Citation shares over time. Exact counts and percentages are in the table below.">`;
  for (let k=0;k<=4;k++) svg += `<line class="reading-grid" x1="${left}" x2="${right}" y1="${y(k*ceiling/4)}" y2="${y(k*ceiling/4)}"/><text x="${left-8}" y="${y(k*ceiling/4)+4}" text-anchor="end">${k*ceiling/4}%</text>`;
  data.periods.forEach((p,i) => {
    if(W<600 && ![0,2,4,7].includes(i))return;
    svg += `<text x="${x(i)}" y="${bottom+26}" text-anchor="${i===data.periods.length-1?'end':'middle'}">${esc(p.replace('before ', '<'))}</text>`;
  });
  data.regions.forEach((r,j) => {
    let path = '', pen = false;
    data.periods.forEach((_,i) => { const v=value(i,j); if(v===null) {pen=false;return;} path += `${pen?'L':'M'}${x(i)},${y(v)} `; pen=true; });
    svg += `<path d="${path}" fill="none" stroke="${COLORS[j]}" stroke-width="2.5"${j===3?' stroke-dasharray="5 3"':''}/>`;
    data.periods.forEach((p,i) => { const v=value(i,j); if(v===null)return; svg += `<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${COLORS[j]}"><title>${esc(`${NAMES[r]}, ${p}: ${v.toFixed(1)}% (${source.series[i][j]} of ${data.denominators[i][j]})`)}</title></circle>`; });
  });
  return `<div class="reading-legend">${data.regions.map((r,j) => `<span><i style="background:${COLORS[j]}"></i>${NAMES[r]}</span>`).join('')}</div><div class="reading-chart">${svg}</svg></div>`;
}
function coverage(data) {
  const c=data.coverage;
  return `<details class="reading-coverage"><summary>Coverage, sources and method · snapshot ${esc(data.snapshot)}</summary>
    <p>${fmt(c.in_analysis)} dissertations are included in the research analysis. These comparisons use the ${fmt(c.with_year)} with a recorded year (${c.years[0]}–${c.years[1]}); ${fmt(c.missing_year)} without years are excluded. The latest period includes partial ${c.years[1]} coverage. Years follow repository metadata and can be deposit or copyright years.</p>
    <p>These are available repository holdings, with uneven coverage by institution, language and year. They are not a census of History PhDs. Europe pools different national collections; changes can reflect which repositories are represented.</p>
    ${table('Dissertations available for time comparisons', ['Degree period', ...data.regions.map(r=>NAMES[r])], data.periods.map((p,i)=>`<tr><th scope="row">${esc(p)}</th>${data.denominators[i].map(n=>`<td>${fmt(n)}</td>`).join('')}</tr>`).join(''))}
    <details><summary>Institutions and countries represented</summary>${table('Dated dissertations by repository institution', ['Region','Country','Institution as recorded','Dissertations'],c.institutions.map(i=>`<tr><td>${NAMES[i.region]}</td><td>${esc(i.country)}</td><th scope="row">${esc(i.institution)}</th><td>${fmt(i.n)}</td></tr>`).join(''))}</details>
    <h3>What is counted</h3><p>A dissertation counts once for a source, however often it cites it. Person counts cover works attributed to that person as first author. ${fmt(c.from_notes_with_year)} dated dissertations use works reconstructed from notes; the others use closing bibliographies. A bibliography can include works consulted without a footnote citation. Notes record cited works. Neither establishes agreement or intellectual influence.</p>
    <h3>Parsing and identities</h3><p>Bibliographic fields are extracted by rules and OCR, then merged by name and title evidence. Person records remain bibliography name keys; namesakes and editions can be joined incorrectly. Reviewed teaching links identify selected keys and retain that limit. The earlier Canadian audit measured 77% fully usable entries; a separate non-English BASE sample measured 32% before subsequent fixes. These samples do not establish current accuracy across all languages. Notes have especially uncertain publication years.</p>
    <p>Search includes works cited by at least ${data.params.min_work} dated dissertations and people cited by at least ${data.params.min_person}. Lower counts are omitted from search, so an absent result is not evidence of absence from the corpus. Companions meet the research explorer's association-strength threshold of ${data.params.min_strength} and at least ${data.params.min_shared} shared dissertations.</p>
    <p><a href="https://github.com/jburnford/historiography/tree/main/data/field-research/dissertation-citations-2026-10-11/release/2026-10-23" target="_blank" rel="noopener noreferrer">Dated data release, methods and measured quality →</a></p>
  </details>`;
}
function teachings(links, key) {
  const matches = Object.entries(links.people).filter(([,p]) => p.source===key || p.works.includes(key));
  if (!matches.length) return '';
  const entries = Object.entries(links.entries).filter(([,e]) => e.people.some(pid=>matches.some(([id])=>id===pid)));
  return `<nav class="reading-teaching" aria-label="Related teaching entries"><strong>Follow the historical arguments</strong>${matches.map(([id,p])=>`<a href="#person=${esc(id)}">${esc(p.label)}’s profile →</a>`).join('')}${entries.map(([id,e])=>`<a href="#node=${esc(id)}">${esc(e.label)} →</a>`).join('')}</nav>`;
}
function companions(data, shard, source) {
  const label = id => shard.labels[id];
  if (!source.rows.length) return '<p>No companions meet the shared-dissertation thresholds for this source.</p>';
  const link=id=>data.sources.some(s=>s.id===id)?sourceLink(label(id)):esc(label(id).short);
  const summary=`<ul class="reading-companions">${source.rows.slice(0,8).map(([id,n])=>`<li>${link(id)}<span>${fmt(n)} of ${fmt(source.n)} dissertations</span></li>`).join('')}</ul>`;
  return summary+`<details class="reading-over-time"><summary>Compare companions over time</summary><p>Rounded percentages of this source’s citing dissertations in each degree period. The column headings give the number of citing dissertations; fewer than ten is a small sample.</p>`+
    table('Share of this source’s citing dissertations also citing each companion', ['Companion', ...data.periods.map((p,i)=>`${p} (n=${source.n_period[i]})`)], source.rows.map(([id,,values])=>`<tr><th scope="row">${link(id)}</th>${values.map(v=>`<td>${v==null?'—':`${v}%`}</td>`).join('')}</tr>`).join(''))+'</details>';
}
function families(data, source) {
  const f=source.fields;
  const placed=f.placed.reduce((a,b)=>a+b,0);
  return `<details class="reading-families"><summary>Explore provisional citation families · ${fmt(placed)} of ${fmt(source.n)} citing dissertations placed</summary>
    <p>These are modelled groups of shared literature, labelled by signature authors and title terms. They are a second lens on the bibliography record. They do not assign dissertations to the teaching project’s families or establish school membership. Percentages describe the placed dissertations’ mixtures; the model leaves other dissertations unplaced.</p>
    ${table('Modelled family mixtures among citing dissertations', ['Provisional family', ...data.periods],f.fams.map((id,j)=>`<tr><th scope="row">${esc(data.families[id].name)}<small>${esc(data.families[id].terms)}</small></th>${data.periods.map((_,p)=>`<td>${f.placed[p]>=5 ? `${f.shares[p][j]??0}%` : '—'}<small>${f.placed[p]} placed</small></td>`).join('')}</tr>`).join(''))}
    <p>Shares for fewer than five placed citing dissertations are omitted. The shared-work vocabulary favours frequently cited literature and varies with the corpus; changes in family mixtures are exploratory.</p></details>`;
}
export function sourceDetail(data, shard, source, links) {
  const label=shard.labels[source.id];
  const person=label.key.startsWith('P:');
  const totals=data.regions.map((_,j)=>data.denominators.reduce((a,row)=>a+row[j],0));
  const examples=source.examples || [];
  return `<article class="reading-detail"><p class="eyebrow">${person?'CITED PERSON · FIRST-AUTHOR NAME KEY':'CITED WORK'}</p><h3 tabindex="-1">${esc(label.short)}</h3>
    ${person?'<p class="fine-print">This bibliography name key can include unresolved namesakes. Use the listed works and example dissertations to inspect the attribution.</p>':`<p>${esc(label.full)}${label.year?` (${esc(label.year)})`:''}${label.author?` · ${esc(label.author)}`:''}</p>`}
    <div class="reading-counts"><div><strong>${fmt(source.n)}</strong><span>of ${fmt(data.coverage.with_year)} dated dissertations cite this source</span></div>${data.regions.map((r,j)=>`<div><strong>${fmt(source.n_region[r]||0)}</strong><span>of ${fmt(totals[j])} in ${NAMES[r]}</span></div>`).join('')}</div>
    ${teachings(links,label.key)}
    <section><h4>Citations over time</h4><p>Share of the sampled dissertations in each region and degree period. Exact counts remain visible below; shares with fewer than 15 dissertations in the region-period are suppressed.</p><div class="reading-trend">${trendChart(data,source)}</div><p class="reading-scroll-hint">Scroll the table sideways to compare all regions.</p>${trendTable(data,source)}</section>
    ${source.works?.length?`<section><h4>Explore selected works</h4><ul class="reading-work-list">${source.works.map(id=>`<li>${sourceLink(shard.labels[id])}</li>`).join('')}</ul><p class="fine-print">Frequently cited works attributed to this first-author key; an exploratory list, not an authority-reviewed bibliography.</p></section>`:''}
    <section><h4>Cited alongside</h4><p>Among dissertations citing this source, how often does each companion also appear? Companion selection uses shared citations above the corpus baseline. Co-citation does not establish an exchange between authors.</p>${companions(data,shard,source)}</section>
    <section><h4>Companions across regions</h4><div class="reading-regions">${data.regions.map(r=>`<div><h5>${NAMES[r]} · ${source.n_region[r]||0} citing dissertations</h5>${source.regional[r]?`<ul>${source.regional[r].map(([id,v])=>`<li>${data.sources.some(s=>s.id===id)?sourceLink(shard.labels[id]):esc(shard.labels[id].short)} <strong>${v}%</strong></li>`).join('')}</ul>`:'<p>Fewer than 10 citing dissertations; regional companions are not shown.</p>'}</div>`).join('')}</div></section>
    ${families(data,source)}
    <section><h4>Inspect example dissertations</h4><p class="fine-print">Up to two examples per region, selected in source-file order. These illustrate the records behind the counts and are not representative samples. Repository links open the original records.</p><ul class="reading-examples">${examples.map(e=>`<li>${publicUrl(e.item_url)?`<a href="${esc(e.item_url)}" target="_blank" rel="noopener noreferrer">${esc(e.title)}</a>`:esc(e.title)}<p>${esc(e.authors)} · ${esc(e.institution)} · ${esc(e.country)} · ${e.year} · ${e.via==='notes'?'citation reconstructed from notes':'bibliography record'}</p></li>`).join('')}</ul></section></article>`;
}
function errorHtml() { return '<p role="status">The dissertation data could not be loaded. <button type="button" data-reading-retry>Try again</button></p>'; }

export async function mountReading(root, key='') {
  if (!root) return;
  root.innerHTML='<p class="loading" role="status">Loading dissertation reading…</p>';
  try {
    const [data,links]=await Promise.all([get('index.json'),get('links.json')]);
    if(!root.isConnected)return;
    root.innerHTML=`<div class="section-heading"><div><p class="eyebrow">THE READING RECORD · RESEARCH PREVIEW</p><h2>Dissertation reading</h2></div></div>
      <p class="reading-intro">What scholarship do doctoral historians draw on? Explore a cited historian or work, compare its use across time and regions, and follow the literature cited alongside it.</p>
      <p class="reading-scope">${fmt(data.coverage.with_year)} dated dissertations · ${fmt(data.sources.filter(s=>s.key.startsWith('W:')).length)} searchable works · ${fmt(data.sources.filter(s=>s.key.startsWith('P:')).length)} searchable people · snapshot ${esc(data.snapshot)}</p>
      <form class="reading-search" role="search"><label for="reading-search">Find a historian or work</label><div><input id="reading-search" type="search" placeholder="Try Cronon, Stoler, Thompson, or a book title" autocomplete="off"><button type="submit">Search</button></div></form>
      <div class="reading-results" aria-live="polite"></div>
      <nav class="reading-starters" aria-label="Starting points">${Object.values(links.people).map(p=>`<a href="${esc(readingHref(p.source))}">${esc(p.label)}</a>`).join('')}</nav>
      <div class="reading-source" aria-live="polite"></div>${coverage(data)}`;
    const input=root.querySelector('input'),results=root.querySelector('.reading-results');
    let hits=[];
    const norm=s=>s.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase();
    const search=()=>{
      const terms=norm(input.value).trim().split(/\s+/).filter(Boolean);
      hits=terms.length ? data.sources.filter(s=>terms.every(t=>norm(`${s.short} ${s.full} ${s.author}`).includes(t))).sort((a,b)=>Number(b.key.startsWith('P:'))-Number(a.key.startsWith('P:'))||b.n-a.n):[];
      results.innerHTML=!terms.length?'':`<p>${fmt(hits.length)} matching sources${hits.length>12?'; showing the first 12':''}.</p><ul>${hits.slice(0,12).map(s=>`<li>${sourceLink(s)} <span>${s.key.startsWith('P:')?'Person':'Work'} · ${fmt(s.n)} citing dissertations</span></li>`).join('')}</ul>`;
    };
    input.addEventListener('input',search);
    input.addEventListener('keydown',e=>{if(e.key==='ArrowDown') {results.querySelector('a')?.focus();e.preventDefault();} if(e.key==='Escape'){results.innerHTML='';}});
    root.querySelector('form').addEventListener('submit',e=>{e.preventDefault();search();results.querySelector('a')?.focus();});
    const box=root.querySelector('.reading-source');
    if(!key) {box.innerHTML='<p class="context-note">Choose a starting point or search above. Follow a historian’s works, compare regions, and return to the teaching entries to examine the historical arguments.</p>';return;}
    const chosen=data.sources.find(s=>s.key===key);
    if(!chosen){box.innerHTML='<p role="status">This source is not in the current explorer snapshot. Search for a historian or work above.</p>';return;}
    input.value=chosen.short;
    box.innerHTML='<p role="status">Loading the selected source…</p>';
    try {
      const shard=await get(chosen.asset);
      if(root.isConnected) {
        const source=shard.sources[chosen.id];
        box.innerHTML=sourceDetail(data,shard,source,links);
        charts.set(root,{data,source});
        resizeReading(root);
      }
    } catch {if(root.isConnected){box.innerHTML=errorHtml();box.querySelector('button').onclick=()=>mountReading(root,key);}}
  } catch {if(root.isConnected){root.innerHTML=errorHtml();root.querySelector('button').onclick=()=>mountReading(root,key);}}
}

export function resizeReading(root) {
  const state=charts.get(root), box=root?.querySelector('.reading-trend');
  if(state && box)box.innerHTML=trendChart(state.data,state.source,box.clientWidth);
}

export async function mountReadingContext(root, type, id) {
  if(!root)return;
  try {
    const links=await get('links.json');
    if(!root.isConnected)return;
    const pids=type==='person'?(links.people[id]?[id]:[]):links.entries[id]?.people||[];
    if(!pids.length)return;
    root.innerHTML=`<section class="reading-context"><p class="eyebrow">IN DISSERTATION READING</p><h3>${type==='person'?'Where this scholarship is cited':'What dissertations draw on'}</h3>
      <p>${type==='person'?'Follow selected works and their use across time and regions.':'Explore two selected authors on this entry’s roster. Their counts describe these authors’ first-author bibliography keys; they do not measure the readership of the whole field.'}</p>
      ${pids.map(pid=>{const p=links.people[pid];return `<div class="reading-context-person"><h4><a href="${esc(readingHref(p.source))}">${esc(p.label)} →</a></h4><p><strong>${fmt(p.n)}</strong> dated dissertations cite this first-author key.</p><ul>${p.works.map(key=>`<li><a href="${esc(readingHref(key))}">${esc(p.work_labels[key])}</a></li>`).join('')}</ul></div>`;}).join('')}
      <p class="fine-print">Snapshot ${esc(links.snapshot)}. Bibliography presence and notes citations are distinct from influence. These teaching links were reviewed through named works; the underlying name keys can still contain attribution errors.</p><a class="text-link" href="${readingHref()}">Explore dissertation reading →</a></section>`;
  } catch {if(root.isConnected)root.innerHTML='<p class="fine-print">Dissertation links are temporarily unavailable. <a href="#tab=dissertations">Open dissertation reading →</a></p>';}
}
