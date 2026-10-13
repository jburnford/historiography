/* Public metadata only. A source-credit match is limited by the atlas identity match. */
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const TIER_LABELS = {accepted: 'Reviewed match', anchored: 'Identifier-supported match', probable: 'Probable match'};
const ROLE_LABELS = {author:'author', editor:'editor', reviewer:'reviewer', contributor_unspecified:'credited contributor', translator:'translator'};

export function recordPanel(asset, personId) {
  const p = asset?.people?.[personId];
  if (!p) return '';
  const groups = [['journal_item','Journal records'], ['reviewed_book','Books reviewed'], ['review_written','Reviews written']];
  const parts = groups.map(([kind,label]) => {
    const rows = p.records.filter(r => r.kind === kind).sort((a,b) => (b.year || 0)-(a.year || 0) || a.title.localeCompare(b.title));
    if (!rows.length) return '';
    return `<details class="publication-group"><summary>${label} · ${p.counts[kind]}</summary><ol>${rows.map(r => {
      const url = /^https?:\/\//i.test(r.url || '') ? r.url : null;
      const title = url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>` : esc(r.title);
      return `<li>${title}<p class="fine-print">${r.year ? esc(r.year) : 'Publication year not recorded'} · ${esc(r.venue || 'Venue not recorded')} · ${esc(ROLE_LABELS[r.role] || r.role)}${kind==='reviewed_book' ? ` · ${r.review_year ? `reviewed ${esc(r.review_year)}` : 'Review date unresolved'}` : ''}</p>
        <span class="identity-tier tier-${esc(r.identity_tier)}">${esc(TIER_LABELS[r.identity_tier] || 'Unresolved match')}</span>
        <details class="identity-evidence"><summary>Why this record is linked</summary><p class="fine-print">Atlas identity: ${esc(TIER_LABELS[p.atlas_identity_tier])}. Source credit: ${esc(TIER_LABELS[r.credit_tier])}. ${esc((r.identity_bases || []).map(x=>x.replaceAll('_',' ')).join('; '))}. Source record: ${esc(r.source_id)}.</p></details></li>`;
    }).join('')}</ol></details>`;
  }).join('');
  return `<section class="publication-records" aria-label="This person in the publication record"><h3>In the publication record</h3>
    <p class="fine-print">${esc(asset.coverage)}</p><p class="fine-print">${esc(asset.identity_note)}</p>${parts}
    <p class="fine-print">Book counts refer to distinct catalogued items; one book can have several review links. Journal records may include reviews and other material. Presence here does not establish agreement or influence.</p></section>`;
}
