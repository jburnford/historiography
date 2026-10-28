#!/usr/bin/env python3
"""Merge the three agents' batch fragments (A, B, C) into batch.json for revision 1.201 (the Indigenous histories split).

List keys are concatenated; edge_revisions (a dict keyed by edge id) are merged with a conflict check;
persons and extras are unioned in order. Run from the repository root:
    python3 data/extension-2026/indigenous-histories-2026-10-27/merge_fragments.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST_KEYS = ['text_revisions', 'field_sets', 'source_field_sets', 'node_list_additions', 'strand_list_additions',
             'new_strands', 'roster_list_additions', 'claim_reviews',
             'edge_endpoint_sets', 'strand_moves', 'roster_moves', 'roster_removals', 'stage2',
             'strand_redirects_add', 'claim_entity_sets', 'strand_list_removals']


def main():
    frags = [json.loads((HERE / f'batch-fragment-{x}.json').read_text()) for x in 'ABCZ']
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
        'revision': '1.201', 'baseline_revision': '1.200', 'date': '2026-10-27', 'batch_dir': 'group-revision-1.201',
        'persons': persons, 'extras': extras,
        'summary': 'Indigenous histories: the family split in three and extended. ' + ' '.join(f['summary'].strip() for f in frags),
        'authorization': 'User, 2026-10-27: the Indigenous histories family is "a priority"; the citation-count promotion rule holds for settler '
                         'scholars but not for Indigenous scholars; J. R. Miller not front and centre; "split off the older scholarship from the newer '
                         'community engaged scholarship"; three-part list approved ("That list looks right to me, but do some careful research"); '
                         'co-authored work "could be packaged together"; "Brenda is Metis".',
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
    # Derived by the coordinator from the moves: each moved strand's old address redirects to its new
    # home (site deep links), and claim-catalogue entities addressed to it follow (validate_claim_catalogue).
    graph = json.loads((HERE.parents[2] / 'historiography-1920-2000.json').read_text())
    if graph['revision_history'][-1]['version'] != batch['baseline_revision']:
        raise SystemExit('graph on disk is not the baseline revision')
    for mv in batch.get('strand_moves', []):
        old_addr, new_addr = f"{mv['from_node']}/{mv['strand']}", f"{mv['to_node']}/{mv['strand']}"
        batch.setdefault('strand_redirects_add', []).append(
            {'from': old_addr, 'to': new_addr, 'reason': 'Indigenous histories split into three fields (1.201); strand record retained.'})
        for ent in graph['claim_catalogue']['entities']:
            if ent.get('legacy_strand_address') == old_addr:
                batch.setdefault('claim_entity_sets', []).append(
                    dict(entity_id=ent['id'], field='legacy_strand_address', expect=old_addr, value=new_addr))
    for key, ident in (('edge_endpoint_sets', lambda x: (x['edge_id'], x['field'])),
                       ('strand_moves', lambda x: x['strand']),
                       ('roster_moves', lambda x: (x['from_node'], x['person_id'])),
                       ('roster_removals', lambda x: (x['node'], x['person_id']))):
        ids = [ident(x) for x in batch.get(key, [])]
        if len(ids) != len(set(ids)):
            raise SystemExit(f'{key} conflict: {sorted(i for i in ids if ids.count(i) > 1)}')
    (HERE / 'batch.json').write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n')
    print('batch.json:', {k: (len(v) if isinstance(v, (list, dict)) else '…') for k, v in batch.items()})


if __name__ == '__main__':
    main()
