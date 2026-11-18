"""Extract subject and geographic fields (043, 600-662, 752) from LC Books All 2016 MARC parts.

Place-nodes scoping pilot (2026-11-18). Streams each gzipped MARC part (never loads a whole file) and writes
one Parquet per part: control (001), lccn (010 $a, normalised as scripts/lc_authority_pilot.norm_lccn),
tag, ind1, ind2, occ (field order), subs (list of 'code=value'), uri ($0 values).

    python3 -I lc_subject_extract.py RAW_DIR OUT_DIR [--procs 8]
"""
import gzip
import re
import sys
import unicodedata
from multiprocessing import Pool
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

FT, SF, RT = b'\x1e', b'\x1f', b'\x1d'
KEEP = {'043', '600', '610', '611', '630', '647', '648', '650', '651', '653', '655', '662', '752'}


def norm_lccn(v):
    v = re.sub(r'\s+', '', (v or '').split('|')[0]).lower()
    return v if re.fullmatch(r'[a-z]{0,3}\d{8,10}', v) else None


def records(stream, chunk=1 << 22):
    buf = b''
    while True:
        data = stream.read(chunk)
        if not data:
            break
        buf += data
        *done, buf = buf.split(RT)
        yield from (r for r in done if r.strip())
    if buf.strip():
        yield buf


def fields(raw):
    leader = raw[:24].decode('ascii', 'replace')
    base = int(leader[12:17])
    directory = raw[24:base - 1]
    for i in range(0, len(directory) - 11, 12):
        tag = directory[i:i + 3].decode('ascii', 'replace')
        length, start = int(directory[i + 3:i + 7]), int(directory[i + 7:i + 12])
        if tag not in KEEP and tag not in ('001', '010'):
            continue
        body = raw[base + start:base + start + length].rstrip(FT)
        if tag == '001':
            yield tag, '', '', [('', body.decode('utf-8', 'replace').strip())]
            continue
        ind = body[:2].decode('utf-8', 'replace').ljust(2)
        subs = [(s[:1].decode('ascii', 'replace'), unicodedata.normalize('NFC', s[1:].decode('utf-8', 'replace')).strip())
                for s in body[2:].split(SF)[1:] if s]
        yield tag, ind[0], ind[1], subs


def do_part(args):
    path, out = args
    rows, bad, n = [], 0, 0
    with gzip.open(path, 'rb') as fh:
        for raw in records(fh):
            try:
                fs = list(fields(raw))
            except (ValueError, IndexError):
                bad += 1
                continue
            n += 1
            control = next((s[0][1] for t, _, _, s in fs if t == '001'), '')
            lccn = next((norm_lccn(v) for t, _, _, s in fs if t == '010' for c, v in s if c == 'a'), None) or ''
            occ = 0
            for tag, i1, i2, subs in fs:
                if tag in ('001', '010'):
                    continue
                rows.append(dict(control=control, lccn=lccn, tag=tag, ind1=i1, ind2=i2, occ=occ,
                                 subs=[f'{c}={v}' for c, v in subs if c not in '01'],
                                 uri=[v for c, v in subs if c in '01']))
                occ += 1
    stem = path.name.split('.utf8')[0]
    pq.write_table(pa.Table.from_pylist(rows), out / f'subjects-{stem}.parquet', compression='zstd')
    return stem, n, len(rows), bad


def main():
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    procs = int(sys.argv[sys.argv.index('--procs') + 1]) if '--procs' in sys.argv else 8
    out.mkdir(parents=True, exist_ok=True)
    parts = [(p, out) for p in sorted(raw.glob('BooksAll.2016.part*.utf8.gz'))
             if not (out / f"subjects-{p.name.split('.utf8')[0]}.parquet").exists()]
    with Pool(procs) as pool:
        for stem, n, r, bad in pool.imap_unordered(do_part, parts):
            print(stem, 'records', n, 'fields', r, 'bad', bad, flush=True)


if __name__ == '__main__':
    main()
