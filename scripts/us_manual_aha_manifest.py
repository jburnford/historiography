#!/usr/bin/env python3
"""Write a collection-manifest CSV for AHA title-page registrations that no manifest lists yet.

The ``us_expansion`` ingest source reads every ``collection-manifest*.csv`` in
data/field-research/us-dissertations-expansion-2026-10-20/. scripts/audit_us_dissertation_collection.py
writes those rows, but it rebuilds the whole 3,088-row collection-manifest.csv from logs whose paths have moved
(2026-11-16: its output would have dropped most rows), so it must not be run. This script does the same row
check for one register only (default manual-aha-2026-11-04: records.jsonl + downloads.jsonl from
register_aha_browser_downloads.py) and writes the rows that no existing manifest holds to a new dated file:

- the record is a doctoral History PhD (eligibility 'history_phd', degree_classification 'doctoral');
- its downloaded file is a .pdf that exists with the logged size, a PDF header and %%EOF;
- the same columns as the audit's manifest.

usage: python3 scripts/us_manual_aha_manifest.py --out collection-manifest-manual-aha-2026-11-17.csv [--dry-run]
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
US = ROOT / 'data/field-research/us-dissertations-expansion-2026-10-20'
FIELDS = ['institution', 'id', 'title', 'authors', 'year', 'aha_id', 'item_url', 'eligibility_basis', 'files', 'bytes', 'paths']


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--register', type=Path, default=US / 'manual-aha-2026-11-04')
    ap.add_argument('--out', required=True, help='file name inside us-dissertations-expansion-2026-10-20/')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    out = US / args.out
    assert out.name.startswith('collection-manifest-') and out.name != 'collection-manifest.csv'
    listed = set()
    for m in sorted(US.glob('collection-manifest*.csv')):
        if m == out:
            continue
        with open(m, newline='', encoding='utf-8') as fh:
            listed |= {(r['institution'], r['id']) for r in csv.DictReader(fh)}
    meta = {(r['institution'], r['id']): r for r in rows(args.register / 'records.jsonl')
            if r.get('eligibility') == 'history_phd' and r.get('degree_classification') == 'doctoral'}
    entries, problems = [], []
    for log in rows(args.register / 'downloads.jsonl'):
        k = (log.get('institution'), log.get('id'))
        if log.get('status') != 'downloaded' or k not in meta or k in listed:
            continue
        r, ok, paths = meta[k], True, []
        for f in log.get('files', []):
            p = Path(f['path'])
            if p.suffix.lower() != '.pdf' or not p.exists() or p.stat().st_size != f.get('bytes'):
                ok = False
                break
            with p.open('rb') as h:
                if not h.read(1024).lstrip().startswith(b'%PDF'):
                    ok = False
                    break
                h.seek(max(0, p.stat().st_size - 65536))
                if b'%%EOF' not in h.read():
                    ok = False
                    break
            paths.append(str(p))
        if not ok or not paths:
            problems.append(k)
            continue
        listed.add(k)
        entries.append(dict(institution=r['institution'], id=r['id'], title=r['title'], authors='; '.join(r.get('authors', [])),
                            year=r.get('year'), aha_id=r.get('aha_id'), item_url=r.get('item_url'),
                            eligibility_basis=r.get('eligibility_basis'), files=len(paths),
                            bytes=sum(f['bytes'] for f in log['files']), paths=json.dumps(paths)))
    print(f'{len(entries)} new manifest rows; {len(problems)} registered files failed the check: {problems[:10]}')
    if not args.dry_run and entries:
        with open(out, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(entries)


if __name__ == '__main__':
    main()
