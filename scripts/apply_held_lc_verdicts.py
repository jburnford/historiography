"""Outside verdicts on held LC authors (Sol via the JSTOR session; scripts/export_held_lc_authors.py items) -> a review
proposal (2026-11-07). Only `same` verdicts at high confidence attach the LC authority to the named key, and only
when the key is still live, holds no LC authority and is not behind the merge guard. `none` at high confidence records
`rejected:lcnaf:<id>` on every candidate key, so the LC routes stop holding that author against them. Everything else
is listed in held.json for hand review.

Medium confidence (user, 2026-11-09, after reading 281 medium 'same' and a sample of the medium 'none': Terra's
'medium' mostly means no single page states the link):
- `same`, the key has a dissertation (AHA record or thesis work), and the basis does not hedge ('may conflate', 'if
  ... an error for'): attach as for high, plus the member `very-likely:lcnaf:<id>` marking the link as inferred (a
  source ties the LC book's author to the candidate's doctorate: the same university, mostly the same year);
- `same` on a key without a dissertation (a review byline or adviser listing only): no attach; the member
  `very-likely-lcnaf:<id>` records the probable identity without moving the LC books onto a thin key;
- `same` with hedged wording: held;
- `none`: `rejected:lcnaf:<id>` as for high (different middle names, doctorates or fields).
--medium-only processes only the medium verdicts (batches applied before this rule).

    python3 scripts/apply_held_lc_verdicts.py <verdicts.jsonl> [more.jsonl ...] --items <items.jsonl> --out <dir> [--reviewer auto|Sol|Terra]
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys

ap = argparse.ArgumentParser()
ap.add_argument('verdicts', type=Path, nargs='+'); ap.add_argument('--items', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--medium-only', action='store_true')
ap.add_argument('--reviewer', default='auto', help="the model that wrote the verdicts (Sol, Terra); 'auto' reads it from each item's <id>/codex.log beside the verdicts file (2026-11-09 the queue moved to Terra)")
args = ap.parse_args()
items = {json.loads(l)['item']: json.loads(l) for l in open(args.items)}
state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
ops, held, res = [], [], Counter()
MODELS = {'gpt-6.1-sol': 'Sol', 'gpt-6.1-terra': 'Terra'}
HEDGE = re.compile(r'conflat|namesake|\bmay\b|\bif\b.{0,40}\b(error|mistake|typo)|uncertain|cannot confirm', re.I)


def reviewer(path, item):
    if args.reviewer != 'auto':
        return args.reviewer
    log = path.parent / item.replace(':', '_') / 'codex.log'
    m = re.search(r'^model: (\S+)', log.read_text(errors='ignore'), re.M) if log.exists() else None
    return MODELS.get(m.group(1), m.group(1)) if m else 'Sol'


lines = [(vf, l) for vf in args.verdicts for l in open(vf)]
for vf, line in lines:
    v = json.loads(line); it = items.get(v['item']); who = reviewer(vf, v['item']); res['by_' + who] += 1
    src = '; '.join(f"{e['url']} ({e['says'][:120]})" for e in v.get('evidence', [])[:3])
    if not it:
        res['item_unknown'] += 1; held.append(dict(v, why='item not in the export')); continue
    conf = v.get('confidence')
    if args.medium_only and conf != 'medium':
        continue
    if v['item'] in state.anchor:
        res['already_keyed'] += 1; continue
    if v['verdict'] == 'same' and conf == 'medium':
        cand = next((c for c in it['candidates'] if c['key'] == v.get('key')), None)
        k = (state.lookup(v.get('key') or '') or [None])[0]
        if not cand or not k:
            res['medium_same_key_not_a_candidate'] += 1; held.append(dict(v, why='key not among the candidates')); continue
        if HEDGE.search(v['basis'] + ' ' + ' '.join(e.get('says', '') for e in v.get('evidence', []))):
            res['held_medium_same_hedged'] += 1; held.append(dict(v, why='medium same, hedged wording')); continue
        has_diss = bool(cand.get('aha_dissertations')) or any(w[2] == 'thesis' for w in cand.get('works') or [] if len(w) > 2)
        if not has_diss:
            ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f"very-likely-lcnaf:{v['item'][6:]}"],
                            basis=f"outside review ({who}, web sources), medium confidence, key without a dissertation: very likely LC {v['item']}: {v['basis'][:300]} Evidence: {src}"[:900]))
            res['medium_same_very_likely_member'] += 1; continue
        if k in blocked or any(a.startswith('lcnaf:') for a in state.keys[k]['anchors']):
            res['medium_same_guard_or_has_lc'] += 1; held.append(dict(v, why='merge guard, or the key holds an LC authority')); continue
        ops.append(dict(event='attach', key=k, anchors=[v['item']], aliases=[], members=[f"very-likely:{v['item']}"],
                        basis=f"outside review ({who}, web sources), medium confidence (inferred: same doctorate): {v['basis'][:300]} Evidence: {src}"[:900]))
        state.anchor[v['item']] = k
        res['medium_same_attached'] += 1; continue
    if v['verdict'] == 'none' and conf == 'medium':
        for c in it['candidates']:
            for k in state.lookup(c['key']):
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f"rejected:lcnaf:{v['item'][6:]}"],
                                basis=f"outside review ({who}, web sources), medium confidence: LC authority {v['item']} is a namesake: {v['basis'][:300]} Evidence: {src}"[:900]))
        res['medium_none_recorded'] += 1; continue
    if v['verdict'] == 'same' and conf == 'high':
        k = (state.lookup(v['key']) or [None])[0]
        if not k or k not in {c['key'] for c in it['candidates']} and v['key'] not in {c['key'] for c in it['candidates']}:
            res['same_key_not_a_candidate'] += 1; held.append(dict(v, why='key not among the candidates')); continue
        if k in blocked or any(a.startswith('lcnaf:') for a in state.keys[k]['anchors']):
            res['same_guard_or_has_lc'] += 1; held.append(dict(v, why='merge guard, or the key holds an LC authority')); continue
        ops.append(dict(event='attach', key=k, anchors=[v['item']], aliases=[], members=[],
                        basis=f"outside review ({who}, web sources): {v['basis'][:300]} Evidence: {src}"[:900]))
        res['same_attached'] += 1
    elif v['verdict'] == 'none' and v.get('confidence') == 'high':
        for c in it['candidates']:
            for k in state.lookup(c['key']):
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f"rejected:lcnaf:{v['item'][6:]}"],
                                basis=f"outside review ({who}, web sources): LC authority {v['item']} is a namesake: {v['basis'][:300]} Evidence: {src}"[:900]))
        res['none_recorded'] += 1
    else:
        res[f"held_{v['verdict']}_{v.get('confidence')}"] += 1; held.append(dict(v, why='not high-confidence same/none'))
args.out.mkdir(parents=True, exist_ok=True)
json.dump(dict(basis=f'held LC authors: outside review verdicts ({', '.join(sorted(k[3:] for k in res if k.startswith('by_')))}), high and medium confidence by the 2026-11-09 rules', decided_by='review', ops=ops),
          open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open(args.out / 'held.json', 'w'), ensure_ascii=False, indent=1)
print(dict(res))
