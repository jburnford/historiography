"""Qwen link labels in git as parts (2026-11-21): data/graph/scored-links/qwen-labels/part-NNN.csv.gz + manifest.json.

The single qwen-labels.csv.gz passed 60 MB (GitHub warns above 50 MB, rejects above 100 MB), so the table lives as
complete CSV parts (header in each), split by row count in the writer's order (sorted by position, so a re-merge
changes the early parts little), each well under 30 MB compressed. The logical content is the header once followed by
every part's rows in part order: byte for byte the CSV the writer produced. manifest.json records the columns, rows per
part, total rows and the sha256 of that logical content, so readers can check they have every part.

Every reader goes through here; each function takes either the parts directory or a single .csv.gz (the form copied to
Plato for training, made with `assemble`):
    iter_rows(path)            csv.DictReader rows (strings), as from the single file
    read_frame(path, **kw)     pandas.read_csv over the logical content (same type inference as the single file)
    duckdb_source(path)        a read_csv(...) expression for DuckDB SQL
    content_sha256(path)       sha256 of the logical content (manifest value for parts, computed for a single file)
    write_parts(src, path)     DataFrame or CSV(.gz) path -> parts + manifest (atomic per file; stale parts removed)

    python3 scripts/qwen_labels_io.py verify   [--labels DIR_OR_FILE]
    python3 scripts/qwen_labels_io.py assemble --out build/.../qwen-labels.csv.gz [--labels DIR]
    python3 scripts/qwen_labels_io.py split    --src qwen-labels.csv.gz [--labels DIR]
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / 'data/graph/scored-links/qwen-labels'      # the tracked parts directory
ROWS_PER_PART = 100_000          # ~19.5 MB gzip each at 2026-11-21 row sizes
MAX_PART_BYTES = 40_000_000      # the writer refuses parts above this (GitHub warns at 50 MB)
CHUNK = 1 << 20


def _is_parts(path):
    return Path(path).is_dir()


def manifest(path=LABELS):
    return json.loads((Path(path) / 'manifest.json').read_text())


def part_paths(path=LABELS):
    """the part files the manifest lists, after checking they are exactly the part files present"""
    p = Path(path)
    m = manifest(p)
    names = [x['name'] for x in m['parts']]
    present = sorted(x.name for x in p.glob('part-*.csv.gz'))
    if present != sorted(names):
        raise RuntimeError(f'{p}: parts present {present} != manifest {names}')
    return [p / n for n in names]


class _Chain(io.RawIOBase):
    """the logical uncompressed bytes: first part whole, later parts without their header line"""

    def __init__(self, files):
        self._files = list(files)
        self._cur = None
        self._first = True

    def readable(self):
        return True

    def _next(self):
        if self._cur:
            self._cur.close()
        if not self._files:
            self._cur = None
            return False
        self._cur = gzip.open(self._files.pop(0), 'rb')
        if not self._first:
            self._cur.readline()            # the header (column names: no quotes or newlines)
        self._first = False
        return True

    def readinto(self, b):
        while True:
            if self._cur is None and not self._next():
                return 0
            data = self._cur.read(len(b))
            if data:
                b[:len(data)] = data
                return len(data)
            if not self._next():
                return 0

    def close(self):
        if self._cur:
            self._cur.close()
            self._cur = None
        super().close()


def open_binary(path=LABELS):
    """a binary file object over the logical uncompressed CSV"""
    if _is_parts(path):
        return io.BufferedReader(_Chain(part_paths(path)), CHUNK)
    return gzip.open(path, 'rb')


def open_text(path=LABELS):
    return io.TextIOWrapper(open_binary(path), encoding='utf-8', newline='')


def iter_rows(path=LABELS):
    """csv.DictReader rows; for parts, raises at the end if the row count differs from the manifest"""
    n = 0
    with open_text(path) as f:
        for r in csv.DictReader(f):
            n += 1
            yield r
    if _is_parts(path) and n != manifest(path)['rows']:
        raise RuntimeError(f'{path}: read {n} rows, manifest says {manifest(path)["rows"]}')


def read_frame(path=LABELS, **kw):
    """pandas.read_csv over the logical content (kw passed through: usecols, dtype, keep_default_na, ...)"""
    import pandas as pd
    with open_binary(path) as f:
        D = pd.read_csv(f, **kw)
    if _is_parts(path) and len(D) != manifest(path)['rows']:
        raise RuntimeError(f'{path}: read {len(D)} rows, manifest says {manifest(path)["rows"]}')
    return D


def duckdb_source(path=LABELS):
    """read_csv(...) for DuckDB SQL: the part files as one table (each has its header); types sniffed over every row
    (sample_size=-1) so the parts read with the types the single file gives"""
    files = [str(p) for p in part_paths(path)] if _is_parts(path) else [str(path)]
    lst = ', '.join("'" + f.replace("'", "''") + "'" for f in files)
    return f'read_csv([{lst}], header=true, sample_size=-1)'


def content_sha256(path=LABELS):
    """sha256 of the logical uncompressed CSV (the manifest value for parts; computed for a single file)"""
    if _is_parts(path):
        return manifest(path)['sha256']
    return _hash(path)[0]


def _hash(path):
    h, n = hashlib.sha256(), 0
    with open_binary(path) as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def _records(f):
    """raw CSV records (bytes, line ending included) from a binary file: a record ends at a newline once its quote
    count is even (quoted fields may hold newlines; quotes inside are doubled)"""
    buf, q = [], 0
    for line in f:
        buf.append(line)
        q += line.count(b'"')
        if q % 2 == 0:
            yield b''.join(buf)
            buf, q = [], 0
    if buf:
        yield b''.join(buf)


def write_parts(src, path=LABELS, rows_per_part=ROWS_PER_PART):
    """DataFrame (written as DataFrame.to_csv(index=False) would) or a CSV / CSV.gz path -> part-NNN.csv.gz +
    manifest.json under `path`. The parts hold the source's records verbatim, in its order. Each file is written to a
    temp name and moved into place; parts beyond the new count are removed; the manifest is written last."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix='.qwen-labels-', dir=path.parent))
    try:
        if not isinstance(src, (str, Path)):
            csv_path = tmpdir / 'all.csv'
            src.to_csv(csv_path, index=False)
            src = csv_path
        src = Path(src)
        op = gzip.open if src.name.endswith('.gz') else open
        h, total, parts = hashlib.sha256(), 0, []
        with op(src, 'rb') as f:
            header = f.readline()
            h.update(header)
            cols = next(csv.reader([header.decode('utf-8')]))
            out, n = None, 0

            def close():
                out.close()
                name = f'part-{len(parts):03d}.csv.gz'
                size = (tmpdir / name).stat().st_size
                if size > MAX_PART_BYTES:
                    raise RuntimeError(f'{name} is {size} bytes; lower ROWS_PER_PART')
                parts.append(dict(name=name, rows=n, bytes=size))

            for rec in _records(f):
                if out is None:
                    out = gzip.open(tmpdir / f'part-{len(parts):03d}.csv.gz', 'wb', compresslevel=9)
                    out.write(header)
                    n = 0
                out.write(rec)
                h.update(rec)
                n += 1
                total += 1
                if n == rows_per_part:
                    close()
                    out = None
            if out is not None or not parts:
                if out is None:                     # no rows: one part with the header only
                    out = gzip.open(tmpdir / 'part-000.csv.gz', 'wb', compresslevel=9)
                    out.write(header)
                    n = 0
                close()
        for x in parts:
            os.replace(tmpdir / x['name'], path / x['name'])
        keep = {x['name'] for x in parts}
        for old in path.glob('part-*.csv.gz'):
            if old.name not in keep:
                old.unlink()
        m = dict(table='qwen-labels', note='logical content = header once + every part\'s rows in part order; '
                 'read with scripts/qwen_labels_io.py', columns=cols, rows=total, sha256=h.hexdigest(),
                 rows_per_part=rows_per_part, parts=parts)
        (tmpdir / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n')
        os.replace(tmpdir / 'manifest.json', path / 'manifest.json')
        return m
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def verify(path=LABELS):
    """recompute the logical hash and row counts of the parts against the manifest"""
    m = manifest(path)
    sha, nbytes = _hash(path)
    rows = []
    for p in part_paths(path):
        with gzip.open(p, 'rb') as f:
            f.readline()
            rows.append(sum(1 for _ in _records(f)))
    ok = sha == m['sha256'] and rows == [x['rows'] for x in m['parts']] and sum(rows) == m['rows']
    return dict(ok=ok, sha256=sha, manifest_sha256=m['sha256'], rows=sum(rows), manifest_rows=m['rows'],
                bytes_uncompressed=nbytes)


def assemble(path, out):
    """the parts as one .csv.gz (for Plato training, which takes one file); out should be under build/ (untracked)"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + '.tmp')
    with open_binary(path) as f, gzip.open(tmp, 'wb') as g:
        shutil.copyfileobj(f, g, CHUNK)
    os.replace(tmp, out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['verify', 'assemble', 'split'])
    ap.add_argument('--labels', default=str(LABELS), help='parts directory (or a single .csv.gz for verify)')
    ap.add_argument('--out', help='assemble: the single .csv.gz to write')
    ap.add_argument('--src', help='split: a single .csv.gz to write as parts')
    a = ap.parse_args()
    if a.cmd == 'verify':
        if not _is_parts(a.labels):
            sha, n = _hash(a.labels)
            print(json.dumps(dict(sha256=sha, bytes_uncompressed=n)))
            return
        r = verify(a.labels)
        print(json.dumps(r, indent=1))
        if not r['ok']:
            raise SystemExit(1)
    elif a.cmd == 'assemble':
        if not a.out:
            raise SystemExit('--out required')
        print(assemble(a.labels, a.out))
    else:
        if not a.src:
            raise SystemExit('--src required')
        m = write_parts(a.src, a.labels)
        print(json.dumps({k: m[k] for k in ('rows', 'sha256', 'parts')}, indent=1))


if __name__ == '__main__':
    main()
