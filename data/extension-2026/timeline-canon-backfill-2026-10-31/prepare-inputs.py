#!/usr/bin/env python3
"""Inputs for the relationship backfill of the thin 1.232–1.234 person entries (2026-10-31).

User, 2026-10-31: "We need to work on those 18" (the person entries added in 1.232–1.234 that still
have fewer than five relationships after 1.235). Writes, beside this script:
- entries.json: each person's current description, works, scope note, every current edge (with its
  relationship and evidence note), the sources those cite, the nodes whose text mentions them, and the
  edges held at Claude's verification of 1.232–1.234 (with reasons);
- endpoints.json: every existing node (id, label, kind, entry type), the only allowed edge endpoints;
- batch.json: the person list and the baseline revision.
"""
from collections import Counter
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
baseline = graph['revision_history'][-1].get('revision') or graph['revision_history'][-1].get('version')
nodes = {n['id']: n for n in graph['nodes']}
sources = {s['id']: s for s in graph['sources']}
degree = Counter()
for e in graph['edges']:
    degree[e['source']] += 1
    degree[e['target']] += 1

packets = sorted(glob.glob(str(ROOT / 'data/extension-2026/timeline-canon-batch[0-9]-2026-10-31')))
added = {pid: Path(p) for p in packets for pid in json.loads((Path(p) / 'batch.json').read_text())['persons']}
persons = sorted((pid for pid in added if degree[pid] < 5), key=lambda p: (degree[p], p))

TEXT = ('description', 'scope_note', 'representative_figures_and_works', 'representative_people')
entries = []
for pid in persons:
    n = nodes[pid]
    edges = [e for e in graph['edges'] if pid in (e['source'], e['target'])]
    used = {sid for e in edges for sid in e.get('source_ids', [])} | set(n.get('source_ids', []))
    surname = n['label'].split()[-1]
    mentioned = [m['id'] for m in graph['nodes'] if m['id'] != pid and any(
        n['label'] in str(m.get(k) or '') or (surname in str(m.get(k) or '') and len(surname) > 4) for k in TEXT)]
    draft = json.loads((added[pid] / pid / 'entry-draft.json').read_text())
    entries.append({
        'id': pid, 'label': n['label'], 'entry_type': n.get('entry_type'), 'current_degree': degree[pid],
        'accepted_in': json.loads((added[pid] / 'batch.json').read_text())['revision'],
        **{k: n.get(k) for k in ('description', 'date_label', 'representative_figures_and_works', 'scope_note')},
        'edges': [{k: e.get(k) for k in ('id', 'source', 'target', 'type', 'relationship_kind', 'directed',
                                          'relationship', 'evidence_note', 'source_ids')} for e in edges],
        'sources': [{k: sources[s].get(k) for k in ('id', 'title', 'url', 'verification')} for s in sorted(used) if s in sources],
        'mentioned_in': mentioned,
        'held_at_verification': draft.get('edges_considered_not_proposed', []),
    })

endpoints = [{'id': n['id'], 'label': n['label'], 'kind': n.get('entry_kind'), 'entry_type': n.get('entry_type')}
             for n in graph['nodes']]
(HERE / 'entries.json').write_text(json.dumps(entries, indent=1, ensure_ascii=False) + '\n')
(HERE / 'endpoints.json').write_text(json.dumps(endpoints, indent=1, ensure_ascii=False) + '\n')
(HERE / 'batch.json').write_text(json.dumps({
    'revision': 'candidate', 'baseline_revision': baseline, 'date': '2026-10-31', 'persons': persons,
    'purpose': 'relationship backfill for the 1.232–1.234 person entries with fewer than five relationships',
}, indent=1, ensure_ascii=False) + '\n')
print(f'baseline {baseline}: {len(persons)} people', [(p, degree[p]) for p in persons])
