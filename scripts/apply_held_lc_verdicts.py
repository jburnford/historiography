"""Outside verdicts on held LC authors (Sol via the JSTOR session; scripts/export_held_lc_authors.py items) -> a review
proposal (2026-11-07). Only `same` verdicts at high confidence attach the LC authority to the named key, and only
when the key is still live, holds no LC authority and is not behind the merge guard. `none` at high confidence records
`rejected:lcnaf:<id>` on every candidate key, so the LC routes stop holding that author against them. Everything else
is listed in held.json for hand review.

    python3 scripts/apply_held_lc_verdicts.py <verdicts.jsonl> <items.jsonl> --out <dir>
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys

ap = argparse.ArgumentParser()
ap.add_argument('verdicts', type=Path); ap.add_argument('items', type=Path); ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
items = {json.loads(l)['item']: json.loads(l) for l in open(args.items)}
state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
ops, held, res = [], [], Counter()
for line in open(args.verdicts):
    v = json.loads(line); it = items.get(v['item'])
    src = '; '.join(f"{e['url']} ({e['says'][:120]})" for e in v.get('evidence', [])[:3])
    if not it:
        res['item_unknown'] += 1; held.append(dict(v, why='item not in the export')); continue
    if v['item'] in state.anchor:
        res['already_keyed'] += 1; continue
    if v['verdict'] == 'same' and v.get('confidence') == 'high':
        k = (state.lookup(v['key']) or [None])[0]
        if not k or k not in {c['key'] for c in it['candidates']} and v['key'] not in {c['key'] for c in it['candidates']}:
            res['same_key_not_a_candidate'] += 1; held.append(dict(v, why='key not among the candidates')); continue
        if k in blocked or any(a.startswith('lcnaf:') for a in state.keys[k]['anchors']):
            res['same_guard_or_has_lc'] += 1; held.append(dict(v, why='merge guard, or the key holds an LC authority')); continue
        ops.append(dict(event='attach', key=k, anchors=[v['item']], aliases=[], members=[],
                        basis=f"outside review (Sol, web sources): {v['basis'][:300]} Evidence: {src}"[:900]))
        res['same_attached'] += 1
    elif v['verdict'] == 'none' and v.get('confidence') == 'high':
        for c in it['candidates']:
            for k in state.lookup(c['key']):
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f"rejected:lcnaf:{v['item'][6:]}"],
                                basis=f"outside review (Sol, web sources): LC authority {v['item']} is a namesake: {v['basis'][:300]} Evidence: {src}"[:900]))
        res['none_recorded'] += 1
    else:
        res[f"held_{v['verdict']}_{v.get('confidence')}"] += 1; held.append(dict(v, why='not high-confidence same/none'))
args.out.mkdir(parents=True, exist_ok=True)
json.dump(dict(basis='held LC authors: outside review verdicts (Sol), high confidence only', decided_by='review', ops=ops),
          open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open(args.out / 'held.json', 'w'), ensure_ascii=False, indent=1)
print(dict(res))
