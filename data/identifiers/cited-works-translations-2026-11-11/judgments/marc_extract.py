"""Stream LC Books All 2016 raw MARC and keep the fields the index lacks: 240/130 uniform title, 041,
765/767, 250, 500 'Translation of' notes, 246, plus 100 heading. One parquet per part in OUT.
Only records with at least one of 240/130/041/765/767/250/translation-note are written (all records keep
title/author in the existing index)."""
import gzip
import re
import sys
import unicodedata
from multiprocessing import Pool
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAW = Path('/mnt/e/lc-bib-2016/raw')
OUT = Path(sys.argv[1])
FT, SF, RT = b'\x1e', b'\x1f', b'\x1d'
WANT = {'001', '008', '010', '041', '100', '110', '111', '130', '240', '243', '245', '246', '250', '500', '765', '767', '775'}
TRNOTE = re.compile(r'^\s*(translation of|translated from|tradu[cç][aã]o de|traduction de|übersetzung von|original title|titre original|título original|t[ií]tulo do original|title of original)', re.I)


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


def nfc(b):
    return unicodedata.normalize('NFC', b.decode('utf-8', 'replace'))


def sub_join(subs, codes):
    return ' '.join(v for c, v in subs if c in codes).strip(' /:;,.=')


def norm_lccn(v):
    v = re.sub(r'\s+', '', (v or '').split('|')[0]).lower()
    return v if re.fullmatch(r'[a-z]{0,3}\d{8,10}', v) else ''


def one(raw):
    leader = raw[:24].decode('ascii', 'replace')
    base = int(leader[12:17])
    d = raw[24:base - 1]
    rec = dict(control='', lccn='', date1='', lang='', l041a='', l041h='', ind041='', main_tag='', main='', main_uri='',
               u_tag='', u_a='', u_l='', u_k='', u_np='', u_f='', title_a='', title='', edition='', notes='', vt='',
               e765='', e767='')
    keep = False
    notes, vts = [], []
    for i in range(0, len(d) - 11, 12):
        tag = d[i:i + 3].decode('ascii', 'replace')
        if tag not in WANT:
            continue
        length, start = int(d[i + 3:i + 7]), int(d[i + 7:i + 12])
        body = raw[base + start:base + start + length].rstrip(FT)
        if tag < '010':
            s = body.decode('utf-8', 'replace')
            if tag == '001':
                rec['control'] = s.strip()
            elif tag == '008' and len(s) >= 38:
                rec['date1'], rec['lang'] = s[7:11].strip(), s[35:38].strip()
            continue
        ind = body[:2].decode('utf-8', 'replace').ljust(2)
        subs = [(s[:1].decode('ascii', 'replace'), nfc(s[1:])) for s in body[2:].split(SF)[1:] if s]
        if tag == '010':
            rec['lccn'] = norm_lccn(next((v for c, v in subs if c == 'a'), ''))
        elif tag == '041':
            keep = True
            rec['ind041'] = ind[0]
            rec['l041a'] = ';'.join(v for c, v in subs if c == 'a')
            rec['l041h'] = ';'.join(v for c, v in subs if c == 'h')
        elif tag in ('100', '110', '111') and not rec['main_tag']:
            rec['main_tag'] = tag
            rec['main'] = sub_join(subs, 'abcqd')
            rec['main_uri'] = next((v for c, v in subs if c in '01' and 'authorities/names/' in v), '')
        elif tag in ('130', '240', '243') and not rec['u_tag']:
            keep = True
            rec['u_tag'] = tag
            rec['u_a'] = sub_join(subs, 'a')
            rec['u_l'] = sub_join(subs, 'l')
            rec['u_k'] = sub_join(subs, 'k')
            rec['u_np'] = sub_join(subs, 'np')
            rec['u_f'] = sub_join(subs, 'f')
        elif tag == '245':
            rec['title'] = sub_join(subs, 'ab')
            rec['title_a'] = sub_join(subs, 'a')
        elif tag == '250':
            keep = True
            rec['edition'] = sub_join(subs, 'ab')[:200]
        elif tag == '500':
            t = sub_join(subs, 'a')
            if TRNOTE.match(t):
                keep = True
                notes.append(t[:300])
        elif tag == '246':
            vts.append((ind[1] + ':' + sub_join(subs, 'ab'))[:200])
        elif tag in ('765', '767', '775'):
            keep = True
            v = (sub_join(subs, 'a') + ' | ' + sub_join(subs, 't') + ' | ' + sub_join(subs, 'w'))[:300]
            k = 'e765' if tag == '765' else 'e767'
            rec[k] = (rec[k] + ' ;; ' + v) if rec[k] else (tag + ':' + v)
    if not keep:
        return None
    rec['notes'] = ' ;; '.join(notes)
    rec['vt'] = ' ;; '.join(vts)[:600]
    return rec


def part(path):
    stem = path.name.split('.utf8')[0]
    out = OUT / f'marcx-{stem}.parquet'
    if out.exists():
        return stem, -1, 0
    rows, bad, n = [], 0, 0
    with gzip.open(path, 'rb') as fh:
        for raw in records(fh):
            n += 1
            try:
                r = one(raw)
            except (ValueError, IndexError):
                bad += 1
                continue
            if r:
                rows.append(r)
    pq.write_table(pa.Table.from_pylist(rows), str(out) + '.tmp', compression='zstd')
    Path(str(out) + '.tmp').rename(out)
    return stem, n, len(rows), bad


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    parts = sorted(RAW.glob('BooksAll.2016.part*.utf8.gz'))
    if len(sys.argv) > 2:
        parts = parts[:int(sys.argv[2])]
    with Pool(3) as p:
        for res in p.imap_unordered(part, parts):
            print(*res, flush=True)
