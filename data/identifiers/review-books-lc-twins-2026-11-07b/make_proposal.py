import json, sys
sys.path.insert(0, 'scripts')
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys
S = '/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
j = json.load(open(S + 'twin_book_joins.json'))
state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
ops, held, seen = [], [], set()
WHY = {'A_diss': 'is its dissertation as published (titles agree)',
       'B_diss': 'is its dissertation as published (two or more distinctive title words shared, the book within fifteen years of the PhD)',
       'A_work': 'is a work this key holds by another route (titles agree)'}
for x in j:
    if x['key'] in blocked: held.append(dict(x, why='merge guard')); continue
    if x['lcnaf'] in seen or x['key'] in {o['key'] for o in ops}: held.append(dict(x, why='several in one run')); continue
    seen.add(x['lcnaf'])
    ops.append(dict(event='attach', key=x['key'], anchors=[x['lcnaf']], aliases=[], members=[],
                    basis=f"LC authority {x['lcnaf']} ({x['label']}): its book '{x['book'][:80]}' ({x['book_year']}) "
                          f"{WHY[x['rule']]}: '{x['own'][:80]}' ({x['own_year']}); identity by works; the only same-name key"))
json.dump(dict(basis="held LC authors of reviewed books joined to their one same-name key through their LC books: the key's dissertation as published, or a work it holds",
               decided_by='rule', ops=ops), open('data/identifiers/review-books-lc-twins-2026-11-07b/proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(j, open('data/identifiers/review-books-lc-twins-2026-11-07b/joins.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open('data/identifiers/review-books-lc-twins-2026-11-07b/held.json', 'w'), ensure_ascii=False, indent=1)
print(len(ops), 'attach;', len(held), 'held', [h['label'] for h in held])
