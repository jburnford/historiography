"""Thesis notes from LC's Books All 2016 records (2026-11-07): which catalogued books are dissertations as published.

A book revised from its author's dissertation usually says so: MARC 502 ('Thesis (Ph. D.)--University of
Wisconsin--Madison, 1999.', or $b degree, $c institution, $d year) or a 500 note ('Revision of the author's
thesis (Ph. D.)--Boston University, 1989.'). With the book's author heading, institution and degree year, the
book joins the author's dissertation record (AHA, repository) on name, institution and year, whatever the
title became. This reads the raw files with lc_bib_index's MARC reader and writes one table beside the index:

- theses-notes.parquet: control (001), tag (502 or 500), note (the note as printed), degree, institution,
  year (from $b $c $d when given, else parsed from the note text; empty when not found).

    python3 scripts/lc_thesis_notes.py --raw /mnt/e/lc-bib-2016/raw --out /mnt/e/lc-bib-2016/index/theses-notes.parquet
"""
import argparse
import gzip
import re
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lc_bib_index import parse, records  # noqa: E402

KEYS = (b'hesis', b'HESIS', b'issertation', b'Diss.', b'Inaug')
NOTE = re.compile(r'(thesis|dissertation|diss\.|inaugural)', re.I)
DEGREE = re.compile(r'\(([^()]*?(?:Ph\.?\s*D|D\.?\s*Phil|Doctoral|Dr\.|Doktor|M\.?\s*A|M\.?\s*Phil|Litt|Th\.?\s*D|Ed\.?\s*D|D\.?\s*A)[^()]*)\)', re.I)
YEAR = re.compile(r'(1[89]\d\d|20[01]\d)')


def split_note(note):
    """(degree, institution, year) from 'Thesis (Ph. D.)--University of X, 1999.' style text."""
    degree = (m.group(1).strip() if (m := DEGREE.search(note)) else '')
    inst, year = '', ''
    if '--' in note:
        tail = note.split('--', 1)[1]
        ys = YEAR.findall(tail)
        year = ys[-1] if ys else ''
        inst = re.sub(r',?\s*(1[89]\d\d|20[01]\d)\b.*$', '', tail).strip(' .,;')
    elif (ys := YEAR.findall(note)):
        year = ys[-1]
    return degree, inst[:200], year


def notes(fields):
    control, out = '', []
    for f in fields:
        if len(f) == 2:
            if f[0] == '001':
                control = f[1].strip()
            continue
        tag, _, _, subs = f
        if tag == '502':
            text = ' '.join(v for _, v in subs).strip()
            sub = {c: v.strip(' .,;') for c, v in subs}
            degree, inst, year = split_note(text)
            out.append(dict(tag='502', note=text[:600], degree=sub.get('b') or degree,
                            institution=sub.get('c') or inst, year=(YEAR.findall(sub.get('d', '')) or [year])[0]))
        elif tag == '500':
            text = ' '.join(v for c, v in subs if c == 'a').strip()
            if NOTE.search(text):
                degree, inst, year = split_note(text)
                out.append(dict(tag='500', note=text[:600], degree=degree, institution=inst, year=year))
    return [dict(control=control, **n) for n in out]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    rows, bad = [], 0
    for path in sorted(args.raw.glob('*.utf8.gz')):
        n0 = len(rows)
        with gzip.open(path, 'rb') as fh:
            for raw in records(fh):
                if not any(k in raw for k in KEYS):
                    continue
                try:
                    rows += notes(parse(raw)[1])
                except (ValueError, IndexError):
                    bad += 1
        print(path.name, len(rows) - n0, flush=True)
    pq.write_table(pa.Table.from_pylist(rows), args.out, compression='zstd')
    print('notes', len(rows), 'unreadable', bad)


if __name__ == '__main__':
    main()
