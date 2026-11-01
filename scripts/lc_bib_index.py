"""Index LC's Books All 2016 retrospective (MDSConnect, UTF-8 MARC) for local lookup (PID-PLAN.md section 6).

LC distributes its bibliographic records free as 43 gzipped MARC files
(https://www.loc.gov/cds/products/MDSConnect-books_all.html; records to 2016). This reads them without a
MARC library and writes two Parquet tables per part, so books can be matched by LCCN, ISBN or title
without querying LC's SRU server; SRU (scripts/lc_catalogue_harvest.py) is left for books the 2016 set
does not hold, mostly those published after it.

Text is normalised to NFC (LC's files keep diacritics decomposed; SRU returns them composed). The 001
control number in these files is the LCCN form, not the internal number SRU's records carry, so compare
records across the two by LCCN.

- records: control (001), lccn (010 $a, normalised as the harvest does), isbns (020 $a as ISBN-13),
  title (245 $a $b, as the harvest), title_a (245 $a), date1 (008/07-10), lang (008/35-37),
  publisher (260/264 $b);
- headings: control, pos, and the personal-name headings from 100/700 without $t, with the same fields
  and rules as `bib_headings` + `record_facts` (heading, family, given, fuller, uri, dates, relators).

    python3 scripts/lc_bib_index.py --raw /mnt/e/lc-bib-2016/raw --out /mnt/e/lc-bib-2016/index
"""
import argparse
import gzip
import sys
import unicodedata
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_routes import isbn13  # noqa: E402
from lc_authority_pilot import HEADING_CODES, norm_lccn  # noqa: E402

FT, SF, RT = b'\x1e', b'\x1f', b'\x1d'


def records(stream, chunk=1 << 22):
    """Raw MARC records from a byte stream, split on the record terminator (lengths in the leader can
    be wrong for records over 99,999 bytes)."""
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


def parse(raw):
    """(leader, [(tag, ind1, ind2, [(code, value)]) or (tag, value) for control fields])."""
    leader = raw[:24].decode('ascii', 'replace')
    base = int(leader[12:17])
    directory = raw[24:base - 1]
    fields = []
    for i in range(0, len(directory) - 11, 12):
        tag = directory[i:i + 3].decode('ascii', 'replace')
        length, start = int(directory[i + 3:i + 7]), int(directory[i + 7:i + 12])
        body = raw[base + start:base + start + length].rstrip(FT)
        if tag < '010':
            fields.append((tag, body.decode('utf-8', 'replace')))
            continue
        ind = body[:2].decode('utf-8', 'replace').ljust(2)
        # LC's files keep diacritics decomposed ('u' + combining umlaut); SRU returns them composed (NFC)
        subs = [(s[:1].decode('ascii', 'replace'), unicodedata.normalize('NFC', s[1:].decode('utf-8', 'replace')))
                for s in body[2:].split(SF)[1:] if s]
        fields.append((tag, ind[0], ind[1], subs))
    return leader, fields


def facts(fields):
    """One records row and its headings, following lc_catalogue_harvest.record_facts and
    lc_authority_pilot.bib_headings."""
    rec = dict(control='', lccn='', isbns=[], title='', title_a='', date1='', lang='', publisher='')
    heads = []
    for f in fields:
        tag = f[0]
        if len(f) == 2:
            if tag == '001':
                rec['control'] = f[1].strip()
            elif tag == '008' and len(f[1]) >= 38:
                rec['date1'], rec['lang'] = f[1][7:11].strip(), f[1][35:38].strip()
            continue
        _, ind1, _, subs = f
        if tag == '245':
            rec['title'] = ' '.join(v for c, v in subs if c in 'ab').strip(' /:;,.')
            rec['title_a'] = ' '.join(v for c, v in subs if c == 'a').strip(' /:;,.')
        elif tag == '020':
            rec['isbns'] += [i for c, v in subs if c == 'a' and (i := isbn13(v.split(' ')[0]))]
        elif tag == '010':
            rec['lccn'] = norm_lccn(next((v for c, v in subs if c == 'a'), '')) or ''
        elif tag in ('260', '264') and not rec['publisher']:
            rec['publisher'] = ' '.join(v for c, v in subs if c == 'b').strip(' /:;,.')
        elif tag in ('100', '700') and ind1 != '3' and not any(c == 't' for c, _ in subs):
            parts = [v.strip() for c, v in subs if c in HEADING_CODES]
            if not parts:
                continue
            a = next((v for c, v in subs if c == 'a'), '')
            family, _, given = a.rstrip(' ,.').partition(',')
            q = next((v for c, v in subs if c == 'q'), '')
            uris = [v for c, v in subs if c in '01' and 'id.loc.gov/authorities/names/' in v]
            heads.append(dict(tag=tag, heading=' '.join(parts).rstrip(' ,'), family=family.strip(), given=given.strip(),
                              fuller=q.strip('() ,'), uri=uris[0] if uris else '',
                              dates=' '.join(v for c, v in subs if c == 'd').strip(' ,.'),
                              relators=[v.strip(' ,.') for c, v in subs if c in 'e4']))
    rec['isbns'] = list(dict.fromkeys(rec['isbns']))
    return rec, heads


def index_part(path, out):
    recs, heads, bad = [], [], 0
    with gzip.open(path, 'rb') as fh:
        for raw in records(fh):
            try:
                rec, hs = facts(parse(raw)[1])
            except (ValueError, IndexError):
                bad += 1
                continue
            recs.append(rec)
            heads += [dict(control=rec['control'], pos=i, **h) for i, h in enumerate(hs)]
    stem = path.name.split('.utf8')[0]
    pq.write_table(pa.Table.from_pylist(recs), out / f'records-{stem}.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(heads), out / f'headings-{stem}.parquet', compression='zstd')
    return len(recs), len(heads), bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--force', action='store_true', help='rebuild parts already indexed')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for path in sorted(args.raw.glob('BooksAll.2016.part*.utf8.gz')):
        stem = path.name.split('.utf8')[0]
        if (args.out / f'headings-{stem}.parquet').exists() and not args.force:
            continue
        print(path.name, *index_part(path, args.out), flush=True)


if __name__ == '__main__':
    main()
