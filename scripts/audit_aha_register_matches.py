#!/usr/bin/env python3
"""Audit AHA title-page registrations for the 2026-11-15 false-match class (2026-11-15).

register_aha_browser_downloads.py (until 2026-11-15) could tie a file to an AHA record whose surname was
any word on pages 1-5 and whose year was decades off. For every registered record of the AHA-matched
manual folders this re-reads pages 1-5 of the file on E: (no copies, no writes to E:) and records:
  surname_front   the AHA dissertator as a name (given name/initial + surname) on pages 1-5 outside
                  supervisor/committee lines (column name kept)
  surname_any     the AHA surname anywhere on pages 1-5
  year_fit        'no' when pages 1-2 date the thesis more than 3 years after the AHA year with no year
                  in [AHA-8, AHA+3] ('none' = no usable year printed)
  name_hint       the file name's AHA id / surname / year agrees ('none' = repository file name)
  rematch         the fixed matcher's pick (AHA id, 'held: reason')
A record is a suspect when any check fails. 'clear' = the surname is nowhere on pages 1-5 AND (the year
or the file name contradicts): those are the false-match class. Output: CSV of suspects (metadata only).

Usage: python3 scripts/audit_aha_register_matches.py [--workers 4] [--out CSV]
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import register_aha_browser_downloads as R  # noqa: E402

BASE = R.FIELD/'us-dissertations-expansion-2026-10-20'
FOLDERS = ['manual-aha-2026-11-04', 'manual-uchicago', 'manual-johnshopkins', 'manual-uc']
AHA_ROWS = None


def text(path, last):
    return subprocess.run(['pdftotext', '-f', '1', '-l', str(last), str(path), '-'], capture_output=True,
                          text=True, timeout=120).stdout


def init():
    global AHA_ROWS
    AHA_ROWS = [r for r in csv.DictReader(open(R.AHA, encoding='utf-8'))
                if r['status'] == 'completed' and r['year'].isdigit() and int(r['year']) >= 1900
                and not r['title'].startswith('[')]


def audit(job):
    folder, rec = job
    path = Path(rec.get('source_pdf') or '')
    aha = rec.get('aha_record') or {}
    out = dict(folder=folder, institution=rec['institution'], id=rec['id'], aha_id=rec.get('aha_id') or '',
               aha_dissertator=aha.get('dissertator') or '; '.join(rec.get('authors') or []),
               aha_year=aha.get('year') or rec.get('year') or '', file=path.name, eligibility_basis=(rec.get('eligibility_basis') or '')[:160])
    if not path.exists():
        return dict(out, problem='file missing')
    opening, front = text(path, 5), text(path, 2)
    row = dict(aha, id=rec.get('aha_id') or '', dissertator=out['aha_dissertator'], year=str(out['aha_year'] or 0),
               title=aha.get('title') or rec['title'])
    surname = [w for w in R.words(row['dissertator'].split(',')[0]) if len(w) > 1]
    flat = ' '.join(R.words(opening))
    squashed = ''.join(R.words(opening)) if sum(len(w) == 1 for w in flat.split()) > 0.5 * max(len(flat.split()), 1) else ''
    out['surname_front'] = 'yes' if R.name_on_pages(row, R.byline_text(opening)) else 'no'
    present = set(R.words(opening))
    out['surname_any'] = 'yes' if any(w in present for w in surname) or (squashed and ''.join(surname) in squashed) else 'no'
    years = R.front_years(front) - ({int(y) for y in re.findall(R.YEAR, row['title'])} | R.content_years(row['title']))
    y = int(row['year']) if str(row['year']).isdigit() else 0
    out['front_years'] = ' '.join(map(str, sorted(years)))
    late = any(v > y + R.YEAR_WINDOW for v in years) and not any(y - 8 <= v <= y + R.YEAR_WINDOW for v in years)
    out['year_fit'] = 'none' if not years else 'no' if late else 'yes'
    hid, hnames, hyear = R.file_hints(path.name)
    bad = []
    if hid and row['id'] and hid != row['id']:
        bad.append(f'aha{hid}')
    if hnames and not any(w in hnames for w in surname):
        bad.append('surname ' + ' '.join(sorted(hnames)))
    if hyear and y and abs(hyear - y) > R.YEAR_WINDOW:
        bad.append(f'year {hyear}')
    out['name_hint'] = 'none' if not (hid or hnames or hyear) else ('no: ' + ', '.join(bad) if bad else 'yes')
    if folder == 'manual-aha-2026-11-04':
        found, rejected = R.match_file(path, opening, front, squashed, AHA_ROWS)
        out['rematch'] = found[1]['id'] if found else 'held: ' + ('; '.join(rejected[:2]) or 'no candidate')
    else:
        out['rematch'] = 'n/a (registered by its own route)'
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--out', type=Path, default=BASE/'manual-aha-2026-11-04/audit-2026-11-15-suspects.csv')
    args = ap.parse_args()
    jobs = []
    for f in FOLDERS:
        paths = {(d['institution'], d['id']): d['files'][0]['path'] for d in R.rows(BASE/f/'downloads.jsonl')
                 if d.get('status') == 'downloaded' and d.get('files')}
        for r in R.rows(BASE/f/'records.jsonl'):
            p = paths.get((r['institution'], r['id']))
            jobs.append((f, dict(r, source_pdf=str(BASE/f/p) if p else r.get('source_pdf'))))
    with ProcessPoolExecutor(max_workers=args.workers, initializer=init) as pool:
        results = list(pool.map(audit, jobs, chunksize=8))
    suspects, counts = [], {}
    for r in results:
        if r.get('problem'):
            r['verdict'] = 'file missing'
        else:
            fails = [k for k in ('surname_front', 'year_fit') if r[k] == 'no'] + \
                    (['name_hint'] if r['name_hint'].startswith('no:') else []) + \
                    (['rematch'] if not r['rematch'].startswith('n/a') and r['rematch'] != r['aha_id'] else [])
            clear = r['surname_any'] == 'no' and (r['year_fit'] == 'no' or r['name_hint'].startswith('no:'))
            r['verdict'] = 'ok' if not fails else ('clear false match' if clear else 'suspect: ' + ', '.join(fails))
        counts.setdefault(r['folder'], {}).setdefault(r['verdict'].split(':')[0], 0)
        counts[r['folder']][r['verdict'].split(':')[0]] += 1
        if r['verdict'] != 'ok':
            suspects.append(r)
    fields = ['verdict', 'folder', 'institution', 'id', 'aha_id', 'aha_dissertator', 'aha_year', 'file', 'surname_front',
              'surname_any', 'front_years', 'year_fit', 'name_hint', 'rematch', 'eligibility_basis', 'problem']
    with args.out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(sorted(suspects, key=lambda r: (r['verdict'], r['folder'], r['file'])))
    print(json.dumps(counts, indent=1))
    print(len(suspects), 'suspects ->', args.out)


if __name__ == '__main__':
    main()
