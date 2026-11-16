"""Dry-run key-log proposals in order against the SQLite cache (2026-11-16). Nothing is written: events are numbered and
validated in memory exactly as `identifiers.py apply` would (materialise, inplace on a read-only cache view), each file
on the state the earlier files leave. Prints events per file, by event and minted type, and claim mints skipped as
withdrawn on review.

    python3 scripts/keylog_dryrun.py data/identifiers/<round>/01-*.json data/identifiers/<round>/02-*.json ...
"""
import contextlib, gzip, io, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
import keylog_snapshot as KS  # noqa: E402

I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
state = KS.read_state()
seq0 = state.seq
out = []
for p in map(Path, sys.argv[1:]):
    with (gzip.open if p.suffix == '.gz' else open)(p, 'rt', encoding='utf-8') as fh:
        prop = json.load(fh)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            events, names = I.materialise(state, prop, 'dry-run', 'dry-run', inplace=True)
        out.append(dict(file=p.name, ops=len(prop['ops']), events=len(events), by_event=dict(Counter(e['event'] for e in events)),
                        minted=dict(Counter(e['type'] for e in events if e['event'] == 'mint')), stderr=err.getvalue().strip(),
                        rejected=None))
    except I.LogError as e:
        out.append(dict(file=p.name, ops=len(prop['ops']), events=0, rejected=str(e)))
        break
print(json.dumps(dict(cache_seq=seq0, final_seq=state.seq, files=out), indent=1))
