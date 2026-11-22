"""Run scripts/merge_guard.py on the merges of 04a-orcid-merges.proposal.json (read-only; prints and writes merge-guard.json).

    flock build/.heavy.lock flock .keylog.lock python3 data/identifiers/sol-proposals-2026-11-21/check_merge_guard.py
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
import keylog_snapshot  # noqa: E402
from merge_guard import blocked_keys, pooled_keys, SINGLE_KEY_CHECKS  # noqa: E402

state = keylog_snapshot.read_state()
blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
pooled = pooled_keys(state)
out = []
for op in json.loads((HERE / '04a-orcid-merges.proposal.json').read_text())['ops']:
    ks = [op['key'], op['into']]
    live = {k: state.lookup(k) for k in ks}
    out.append(dict(key=op['key'], into=op['into'], live=live, blocked=[k for k in ks if k in blocked], pooled=[k for k in ks if k in pooled],
                    passes=not any(k in blocked for k in ks) and all(live[k] == [k] for k in ks)))
res = dict(cache_seq=state.seq, merges=out, passed=sum(o['passes'] for o in out), held=sum(not o['passes'] for o in out))
(HERE / 'merge-guard.json').write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
