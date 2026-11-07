import json, sys
sys.path.insert(0, 'scripts')
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys
S = '/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
j = json.load(open(S + 'atlas_roster_joins.json'))
DROP = {'p-1297': 'the atlas cites a different Wilkinson lecture from the one this key authored'}
state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
ops, held = [], []
for a, p, pl, h in j:
    al = state.keys[a]['label']
    if a in DROP: held.append(dict(atlas=a, partner=p, label=al, why=DROP[a])); continue
    if {a, p} & blocked: held.append(dict(atlas=a, partner=p, label=al, why='merge guard (pooled key or open conflict)')); continue
    how = (f"the atlas attributes to {al} the source '{h[1]}', keyed to a work this key ({pl}) authored or edited"
           if h[0] == 'shared' else
           f"the atlas attributes to {al} the source '{h[1]}' ({h[3][:70]}...), whose title and year agree with '{h[2][:70]}', which this key ({pl}) authored or edited")
    ops.append(dict(event='merge', key=p, into=a, basis=f'identity by works: {how}; same name; the atlas key survives'))
json.dump(dict(basis="atlas people and their same-name twins joined through the works the atlas's own rosters and strands attribute to them",
               decided_by='rule', ops=ops), open('data/identifiers/atlas-twins-by-works-2026-11-07b/proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open('data/identifiers/atlas-twins-by-works-2026-11-07b/held.json', 'w'), ensure_ascii=False, indent=1)
print(len(ops), 'merges;', len(held), 'held:', [(x['label'], x['why'][:30]) for x in held])
