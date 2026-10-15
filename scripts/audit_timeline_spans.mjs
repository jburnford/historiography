/* Inventory the existing timeline without proposing or changing historical dates.
   node scripts/audit_timeline_spans.mjs [--check]
   Uses the production span reader and layout so the report describes what is drawn. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {LAYER_TITLES} from '../site/core.mjs';
import {spanOf, parseSpan, frameOf, reviewedThrough, fieldNodes, fieldLayers,
  buildFieldLayout, interventionsOf} from '../data/field-research/timeline-spans-2026-10-15/baseline/field.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = 'historiography-1920-2000.json';
const dest = path.join(root, 'data/field-research/timeline-spans-2026-10-15');
const baseline = JSON.parse(fs.readFileSync(path.join(dest, 'baseline/manifest.json')));
const snapshot = path.join(root, baseline.snapshot);
const raw = fs.existsSync(snapshot) ? fs.readFileSync(snapshot)
  : execFileSync('git', ['show', `${baseline.commit}:${baseline.graph_path}`], {cwd: root, maxBuffer: 64 * 1024 * 1024});
const graph = JSON.parse(raw);
const frame = frameOf(graph);
const layout = buildFieldLayout(graph, 1400, null, fieldLayers(graph, LAYER_TITLES));
const drawn = new Map(layout.bars.map(b => [b.node.id, b]));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const count = (rows, key) => Object.fromEntries([...new Set(rows.map(key))].sort()
  .map(k => [k, rows.filter(r => key(r) === k).length]));
const continuationCue = label => {
  const match = label.match(/onward|present|continu|ongoing|later\b|expanding|reception/i);
  return match ? {text: match[0], context: label.slice(Math.max(0, match.index - 24), match.index + match[0].length + 24)} : null;
};

function row(node) {
  const span = spanOf(node), prose = parseSpan(node.date_label), bar = drawn.get(node.id);
  const review = reviewedThrough(node), flags = [];
  if (!node.date_span) flags.push('prose_derived_span');
  if (node.entry_kind === 'person' && bar?.open) flags.push('person_continues_to_frame');
  if (node.entry_type === 'Debate' && bar?.open) flags.push('debate_continues_to_frame');
  if (review !== null && span && span.end > review) flags.push('normalized_end_after_review');
  if (review !== null && span && span.start > review) flags.push('review_precedes_normalized_start');
  if (node.date_span && prose && span.start !== prose.start) flags.push('structured_start_differs_from_prose');
  if (bar?.open && /present/i.test(node.date_label) && !/\bpresent\b/i.test(node.date_label))
    flags.push('present_matched_inside_word');
  return {
    id: node.id, label: node.label, entry_kind: node.entry_kind, entry_type: node.entry_type,
    origin: node.entry_kind === 'periodical' ? 'linked_journal' : 'curated_graph',
    date_label: node.date_label, date_span: node.date_span || null,
    date_source: node.date_span ? 'structured' : span ? 'prose' : 'undated',
    normalized_span: span, prose_span: prose, reviewed_through: review,
    selected_interventions: interventionsOf(node),
    continuation_cue: !node.date_span && span?.endKind === 'coverage_limit'
      ? continuationCue(node.date_label) : null,
    rendered: bar ? {start: span.start, solid_end: bar.drawEnd,
      continuation_until: bar.open ? bar.fadeTo : null, open: bar.open,
      point: bar.point, earlier_lead_in: Boolean(bar.lead)} : null,
    review_flags: flags,
  };
}

const entries = graph.nodes.map(row);
const journals = fieldNodes(graph).filter(n => n.entry_kind === 'periodical').map(row);
const flagNames = [...new Set(entries.flatMap(r => r.review_flags))].sort();
const audit = {
  purpose: 'Inventory of existing date semantics and rendering; flags are review prompts, not historical corrections.',
  input: {path: input, sha256: sha(raw), revision: graph.revision_history.at(-1).version,
    renderer_sha256: sha(fs.readFileSync(path.join(dest, 'baseline/field.mjs'))), layout_width: 1400},
  frame,
  summary: {
    entries: entries.length, by_kind: count(entries, r => r.entry_kind),
    by_date_source: count(entries, r => r.date_source),
    date_source_by_kind: count(entries, r => `${r.entry_kind}:${r.date_source}`),
    by_entry_type: count(entries, r => r.entry_type),
    by_precision: count(entries, r => r.normalized_span?.precision || 'none'),
    by_review_year: count(entries, r => String(r.reviewed_through)),
    rendered_open_by_kind: count(entries.filter(r => r.rendered?.open), r => r.entry_kind),
    flags: Object.fromEntries(flagNames.map(flag => [flag, entries.filter(r => r.review_flags.includes(flag)).length])),
    linked_journals: journals.length,
    journal_start_basis: count(journals, r => r.date_span?.start_kind || 'unspecified'),
  },
  flag_definitions: {
    prose_derived_span: 'The display infers numeric dates and continuation from prose. This does not by itself establish an incorrect historical date.',
    person_continues_to_frame: 'A person entry is drawn solid to the frame end, without a recorded per-person review year. Review the distinction between contributions and reception.',
    debate_continues_to_frame: 'A Debate entry is drawn beyond its last selected year toward the frame end. Review whether the exchange is bounded or continuing.',
    normalized_end_after_review: 'The normalized span end exceeds the review year. This may represent selected later evidence or a parsed decade bound, not a survey of the later period.',
    review_precedes_normalized_start: 'The review year predates the normalized start; inspect the inherited review metadata and its meaning.',
    structured_start_differs_from_prose: 'The explicit span starts at a different year from the first parsed year. This can correctly distinguish antecedents from the main episode.',
    present_matched_inside_word: 'The continuation parser matches present within a larger word, rather than an explicit temporal statement.',
  },
  entries, journals,
};
const columns = ['id','label','entry_kind','entry_type','date_source','date_label',
  'normalized_start','normalized_end','precision','reviewed_through','drawn_solid_to',
  'drawn_continuation_to','continuation_cue','review_flags'];
const csvValue = value => {
  const text = value === null || value === undefined ? '' : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};
const csvRows = [...entries, ...journals].map(r => [r.id,r.label,r.entry_kind,r.entry_type,
  r.date_source,r.date_label,r.normalized_span?.start,r.normalized_span?.end,
  r.normalized_span?.precision,r.reviewed_through,r.rendered?.solid_end,
  r.rendered?.continuation_until,r.continuation_cue?.text,r.review_flags.join(';')]);
const outputs = new Map([
  ['audit.json', JSON.stringify(audit, null, 2) + '\n'],
  ['entries.csv', [columns,...csvRows].map(r => r.map(csvValue).join(',')).join('\n') + '\n'],
]);
const check = process.argv.includes('--check');
if (!check) fs.mkdirSync(dest, {recursive: true});
for (const [name, content] of outputs) {
  const target = path.join(dest, name);
  if (check) {
    if (!fs.existsSync(target) || fs.readFileSync(target, 'utf8') !== content)
      throw new Error(`${name} does not match the current graph and renderer; regenerate the audit.`);
  } else fs.writeFileSync(target, content);
}
console.log(`${check ? 'Verified' : 'Wrote'} timeline audit: ${entries.length} curated entries and ${journals.length} linked journals.`);
console.log(JSON.stringify(audit.summary, null, 2));
