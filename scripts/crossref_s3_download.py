"""Download the Crossref public data file from its requester-pays S3 bucket in 2 GiB byte ranges (2026-11-08).

The torrent stalled on E: (aria2 holds thousands of the 35,909 files open), so the tar comes from S3 instead: one
object, fetched as numbered range pieces written start to finish under /mnt/e/crossref-dl/parts/. A piece that
exists is skipped, so a dropped connection repeats one piece, not the whole ~208 GB (requester pays: ~$0.09/GB).
scripts/crossref_dump_pass.py reads the tar across the pieces without unpacking it.

    python3 scripts/crossref_s3_download.py --key <object key> [--workers 3]
"""
import argparse, concurrent.futures as cf, json, os, subprocess, sys, time
from pathlib import Path

BUCKET = 'api-snapshots-reqpays-crossref'
OUT = Path('/mnt/e/crossref-dl/parts')
PIECE = 2 * 1024 ** 3
AWS = [os.path.expanduser('~/.local/bin/aws'), '--region', 'us-east-1']


def head(key):
    r = subprocess.run(AWS + ['s3api', 'head-object', '--bucket', BUCKET, '--key', key, '--request-payer', 'requester'],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'head-object failed: {r.stderr.strip()}')
    return json.loads(r.stdout)['ContentLength']


def fetch(key, i, size):
    dest = OUT / f'part-{i:04d}'
    lo, hi = i * PIECE, min(size, (i + 1) * PIECE) - 1
    if dest.exists() and dest.stat().st_size == hi - lo + 1:
        return i, 'have'
    tmp = OUT / f'part-{i:04d}.tmp'
    for attempt in range(6):
        r = subprocess.run(AWS + ['s3api', 'get-object', '--bucket', BUCKET, '--key', key, '--request-payer', 'requester',
                                  '--range', f'bytes={lo}-{hi}', str(tmp)], capture_output=True, text=True)
        if r.returncode == 0 and tmp.stat().st_size == hi - lo + 1:
            os.replace(tmp, dest)
            return i, 'got'
        time.sleep(10 * (attempt + 1))
    return i, 'failed: ' + r.stderr.strip()[:200]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--key', required=True)
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    size = head(args.key)
    n = (size + PIECE - 1) // PIECE
    (OUT / 'manifest.json').write_text(json.dumps(dict(bucket=BUCKET, key=args.key, size=size, piece=PIECE, pieces=n)))
    print(f'{args.key}: {size:,} bytes, {n} pieces', flush=True)
    t0, got = time.time(), 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for i, status in ex.map(lambda i: fetch(args.key, i, size), range(n)):
            got += status == 'got'
            el = time.time() - t0
            print(f'piece {i + 1}/{n} {status}; {got * PIECE / max(el, 1) / 1024 ** 2:.1f} MiB/s, {el / 60:.0f} min', flush=True)
    bad = [p for p in range(n) if not (OUT / f'part-{p:04d}').exists()]
    print('complete' if not bad else f'missing pieces: {bad} (rerun to retry)', flush=True)


if __name__ == '__main__':
    main()
