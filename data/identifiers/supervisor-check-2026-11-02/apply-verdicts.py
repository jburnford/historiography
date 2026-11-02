"""Turn Sol's supervisor verdicts into a key-log proposal (2026-11-02).

For each group folder with verdicts.json, a `yes` naming one of the entry's candidates joins the supervisor's
key to it: a candidate graph key merges with it (through the merge guard and key_aha_career's merge rule: no
two PIDs of one kind, no two AHA dissertations, names agree), an LC-only candidate's authority is attached.
`no` and `unclear` change nothing and are listed in summary.json. Writes proposal.json, review-queue.json and
summary.json here.

    python3 data/identifiers/supervisor-check-2026-11-02/apply-verdicts.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State, materialise, plan  # noqa: E402
from key_aha_career import PUBLIC, merge_rule  # noqa: E402
from merge_guard import guarded  # noqa: E402

state = State.load(ROOT / 'data/identifiers')
entries = {e['id']: e for g in json.loads((HERE / 'groups.json').read_text()) for e in g['entries']}
clusters, queue, rows, summary = [], [], [], Counter()
for path in sorted(HERE.glob('g*/verdicts.json')):
    for v in json.loads(path.read_text()):
        e = entries.get(v.get('id'))
        if not e:
            summary['unknown_id'] += 1
            continue
        summary[v.get('verdict')] += 1
        rows.append(dict(id=e['id'], supervisor=e['supervisor'], verdict=v.get('verdict'), same_as=v.get('same_as'), who=v.get('who')))
        if v.get('verdict') != 'yes':
            continue
        k = e['id']
        cand = next((c for c in e['candidates'] if v.get('same_as') in (c['graph_key'], c['lc'])), None)
        if not cand or state.keys[k]['status'] not in ('active', 'provisional'):
            queue.append(dict(kind='sol_yes_not_applicable', id=k, same_as=v.get('same_as')))
            summary['yes_not_applicable'] += 1
            continue
        if cand['graph_key']:
            c = cand['graph_key']
            if state.keys[c]['status'] not in ('active', 'provisional'):
                queue.append(dict(kind='sol_candidate_key_retired', id=k, same_as=c))
                continue
            pid = next((a for a in sorted(state.keys[c]['anchors']) if a.split(':', 1)[0] in PUBLIC), None)
        else:
            pid = f'lcnaf:{cand["lc"]}'
        src = f'supervisor-check-2026-11-02/{path.parent.name}/verdicts.json'
        clusters.append(dict(type='person', label=state.keys[cand['graph_key']]['label'] if cand['graph_key'] else e['supervisor'],
                             anchors={pid} | state.keys[k]['anchors'], members=set(), aliases=set(), resolution='established',
                             basis=f'AHA supervisor {e["supervisor"]} is {pid}: {v.get("who")} (Sol check, {src})'))
ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state)))
for o in [o for o in ops if o['event'] == 'merge']:
    into, gone = state.keys[o['into']], state.keys[o['key']]
    if not any(a.split(':', 1)[0] in PUBLIC for a in into['anchors']) and len(gone['label']) > len(into['label']):
        ops.append(dict(event='relabel', key=o['into'], label=gone['label'], basis='the name on the LC or Wikidata key it joined'))
materialise(state, dict(basis='supervisor check', ops=ops), 'dry-run', 'dry-run')
(HERE / 'proposal.json').write_text(json.dumps(dict(basis='AHA supervisors matched to their PID keys by Sol agents', decided_by='review',
                                                    ops=ops), ensure_ascii=False, indent=1) + '\n')
(HERE / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
(HERE / 'summary.json').write_text(json.dumps(dict(counts=dict(summary), ops=dict(Counter(o['event'] for o in ops)),
                                                   held=len(held), rows=rows), ensure_ascii=False, indent=1) + '\n')
print(dict(summary), dict(Counter(o['event'] for o in ops)), 'held', len(held))
