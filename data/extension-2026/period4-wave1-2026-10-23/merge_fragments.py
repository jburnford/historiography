#!/usr/bin/env python3
"""Merge the three agents' batch fragments (A, B, C) into batch.json for revision 1.156.

List keys are concatenated; edge_revisions (a dict keyed by edge id) are merged with a conflict check;
persons and extras are unioned in order. Run from the repository root:
    python3 data/extension-2026/period4-wave1-2026-10-23/merge_fragments.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST_KEYS = ['text_revisions', 'field_sets', 'source_field_sets', 'node_list_additions', 'strand_list_additions',
             'new_strands', 'roster_list_additions', 'claim_reviews']


def main():
    frags = [json.loads((HERE / f'batch-fragment-{x}.json').read_text()) for x in 'ABC']
    persons, extras = [], []
    for f in frags:
        for p in f.get('persons', []):
            if p not in persons:
                persons.append(p)
        for e in (f.get('extras') or []):
            if e not in extras:
                extras.append(e)
    edge_revisions = {}
    for f in frags:
        for k, v in (f.get('edge_revisions') or {}).items():
            if k in edge_revisions:
                raise SystemExit(f'edge revision conflict: {k}')
            edge_revisions[k] = v
    batch = {
        'revision': '1.156', 'baseline_revision': '1.155', 'date': '2026-10-24', 'batch_dir': 'group-revision-1.156',
        'persons': persons, 'extras': extras,
        'summary': 'After 2000, wave 1. ' + ' '.join(f['summary'].strip() for f in frags),
        'authorization': 'User, 2026-10-23: "use this information to build out the atlas (that we don\'t call an atlas anymore)", '
                         'after the cohort analysis of the History PhD citation graph (data/field-research/dissertation-citations-2026-10-11/summary/cohorts/README.md) '
                         'and the user\'s readings: the narrative is still the 1980s debate; no new debate everyone cites; the change is new fields, '
                         'environmental history and settler colonial studies in particular, perhaps the history of emotions.',
        'rationale': ' '.join(f['rationale'].strip() for f in frags),
        'source_merges': {}, 'edge_revisions': edge_revisions,
    }
    for k in LIST_KEYS:
        merged = []
        for f in frags:
            merged.extend(f.get(k) or [])
        if merged:
            batch[k] = merged
    # one guarded field set per (node, field): a conflict means two agents touched the same field
    seen = set()
    for fs in batch.get('field_sets', []):
        key = (fs['node'], fs['field'])
        if key in seen:
            raise SystemExit(f'field_sets conflict: {key}')
        seen.add(key)
    (HERE / 'batch.json').write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n')
    print('batch.json:', {k: (len(v) if isinstance(v, (list, dict)) else '…') for k, v in batch.items()})


if __name__ == '__main__':
    main()
