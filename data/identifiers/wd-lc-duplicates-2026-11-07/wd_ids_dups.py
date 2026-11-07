"""Keys holding an identifier (LC, GND, ORCID) that Wikidata gives for the item another key holds: one person on
two keys. Merged when the names are compatible and the two keys hold no conflicting identifiers beyond those
Wikidata itself lists for the item (LC's duplicate authorities); otherwise held for review."""
import json, sys
sys.path.insert(0, 'scripts')
from collections import Counter
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys
from key_registry import names_compatible
found = json.load(open(sys.argv[1]))
out = sys.argv[2]
s = State.load(DEFAULT_DIR); b = blocked_keys(s)
PIDS = ('lcnaf:', 'wd:', 'orcid:', 'gnd:', 'viaf:', 'isni:', 'idref:')
ops, held, done, res = [], [], set(), Counter()
for q, ids in found.items():
    A = s.lookup('wd:' + q)
    if len(A) != 1: continue
    a = A[0]
    wdids = set(ids) | {'wd:' + q}
    for i in sorted(set(ids)):
        B = s.lookup(i) if i in s.anchor else []
        if len(B) != 1 or B[0] == a: continue
        o = B[0]
        pair = tuple(sorted((a, o)))
        if pair in done: continue
        done.add(pair)
        la, lo = s.keys[a]['label'], s.keys[o]['label']
        conf = sorted({f'{x} / {y}' for x in s.keys[a]['anchors'] for y in s.keys[o]['anchors']
                       if x.startswith(PIDS) and y.startswith(PIDS) and x.split(':')[0] == y.split(':')[0] and x != y
                       and not (x in wdids and y in wdids)})
        why = None
        if s.keys[a]['type'] != 'person' or s.keys[o]['type'] != 'person': why = 'not two people'
        elif pair[0] in b or pair[1] in b: why = 'merge guard'
        elif conf: why = 'conflicting identifiers: ' + '; '.join(conf[:3])
        elif not names_compatible(la, lo): why = 'names not compatible by rule'
        res[why.split(':')[0] if why else 'merge'] += 1
        rec = dict(qid=q, id=i, key=a, label=la, other=o, other_label=lo)
        if why: held.append(dict(rec, why=why)); continue
        keep, drop = sorted(pair, key=lambda k: int(k[2:]))
        ops.append(dict(event='merge', key=drop, into=keep,
                        basis=f"identity by identifier: Wikidata {q} (on {a}, {la}) gives {i}, held by {o} ({lo}); names agree; the older key survives"))
print(dict(res))
json.dump(dict(basis='keys holding an identifier (LC, GND, ORCID) that Wikidata gives for the item another same-name key holds',
               decided_by='rule', ops=ops), open(out + '/proposal-all.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open(out + '/held-all.json', 'w'), ensure_ascii=False, indent=1)
import random; random.seed(3)
for o in random.sample(ops, min(20, len(ops))): print(o['basis'][:170])
print('--- held sample')
for h in random.sample(held, min(15, len(held))): print(h['label'][:28], '|', h['other_label'][:30], '|', h['id'], '|', h['why'][:70])
