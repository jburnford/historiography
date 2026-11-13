"""Explorer sweep (2026-11-13; a standing step after every explorer restart). A page failed on a missing column that the
API probes did not catch; this loads a random sample of person, work (keyed and unkeyed) and prize nodes plus a fixed
probe list through /api/node, then every /api/group each node lists, and exits non-zero on any error.

    python3 scripts/explorer_sweep.py [--port 4180] [--n 300] [--seed 13] [--graph build/graph]
"""
import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
PROBES = ['p-24137', 'w-1025226', 'doi:10.1515/9781552387443-004', 'w-916866', 'p-1025', 'p-15018',
          'w-689154', 'w-1477380']


def sample(G, n, seed):
    db = duckdb.connect()
    db.execute("SET memory_limit='2GB'; SET threads=2")
    db.execute(f'SELECT setseed({(seed % 1000) / 1000})')
    keys = []
    q = [(f"SELECT key FROM '{G}/person.parquet'", n // 2),
         (f"SELECT key FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed'", n // 4),
         (f"SELECT key FROM '{G}/work.parquet' WHERE resolution = 'unkeyed'", n // 8),
         (f"SELECT \"from\" FROM '{G}/same_work.parquet'", n // 16)]
    if (G / 'prize.parquet').exists():
        q.append((f"SELECT key FROM '{G}/prize.parquet'", n // 16))
    for sql, k in q:
        keys += [r[0] for r in db.execute(f'SELECT * FROM ({sql}) USING SAMPLE {max(k, 1)} ROWS').fetchall()]
    return keys


def get(base, path, params):
    url = f'{base}{path}?{urllib.parse.urlencode(params)}'
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get('error')
        except Exception:
            msg = None
        return None, f'{e.code} {msg or e.reason}: {url}'
    except Exception as e:
        return None, f'{type(e).__name__} {e}: {url}'
    if isinstance(body, dict) and body.get('error'):
        return None, f"error {body['error']}: {url}"
    return body, None


def sweep(base, key):
    errors, calls = [], 1
    node, err = get(base, '/api/node', dict(key=key))
    if err:
        return [err], calls
    shown = node['node']['key']
    for g in node.get('groups', []):
        for sort in ('weight', 'year'):
            calls += 1
            _, err = get(base, '/api/group', dict(key=shown, rel=g['id'], offset=0, limit=50, sort=sort))
            if err:
                errors.append(err)
    return errors, calls


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--port', type=int, default=4180)
    ap.add_argument('--n', type=int, default=300)
    ap.add_argument('--seed', type=int, default=int(time.time()))
    ap.add_argument('--graph', type=Path, default=ROOT / 'build/graph')
    args = ap.parse_args()
    base = f'http://localhost:{args.port}'
    keys = PROBES + sample(args.graph, args.n, args.seed)
    t0 = time.time()
    errors, calls = [], 0
    with ThreadPoolExecutor(4) as ex:
        for key, (errs, n) in zip(keys, ex.map(lambda k: sweep(base, k), keys)):
            calls += n
            errors += [f'{key}: {e}' for e in errs]
    print(f'{len(keys)} nodes ({len(PROBES)} probes, seed {args.seed}), {calls} calls, {len(errors)} errors, '
          f'{time.time() - t0:.0f}s')
    for e in errors[:50]:
        print('  ', e)
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
