#!/usr/bin/env python3
"""Match browser-saved German thesis PDFs back to DNB records and add them to the harvest manifest
(after stage 4 of the German thesis harvest, 2026-11-14).

For each PDF in the drop folder (recursively):
  1. file name contains a DNB id from theses.csv.gz (e.g. 1240316119.pdf) -> that record;
  2. a URN (urn:nbn:de:...) in the file name or in the text of the first 3 pages -> the record with
     that URN;
  3. otherwise title page match: the record whose author surname appears on pages 1-3 and whose
     title shares the most distinctive words (at least 60% of its first 8 title words of 4+ letters,
     and at least 3 words), one clear winner only.
Several drop folders (default: /mnt/e/german-theses-2026-11-14/browser-drop and, for files modified
since --since, the shared /mnt/e/historiography-dissertation-pdfs, which also holds other countries'
PDFs: matched only by DNB id, URN or title page). .crdownload/.part files are ignored. Archives
(.tgz/.tar/.zip, e.g. heiDOK multi-file theses or DNB-id-named zips) are listed and only their PDF
members are extracted into a new directory per archive under <fetch-dir>/browser-extracted/; an
archive named by a DNB id hints that id.
Matched files are COPIED (never moved or deleted) to <fetch-dir>/browser/<dnb-id>.pdf and a row
with status 'downloaded' and note 'browser:<rule>' is appended to manifest.csv. Files that are not
PDFs, already registered (same sha256), or unmatched are listed in register-report.csv.

Usage:
  python3 -I scripts/german_theses_register.py [--drop /mnt/e/german-theses-2026-11-14/browser-drop] \
      [--table data/field-research/dnb-germany-harvest-2026-11-14/theses.csv.gz] [--dry-run]
"""
import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import pathlib
import re
import shutil
import subprocess
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
FETCH = pathlib.Path('/mnt/e/german-theses-2026-11-14')
MAN_FIELDS = ['dnb_id', 'host', 'status', 'url', 'landing_url', 'sha256', 'bytes', 'path', 'date', 'note', 'screen']
SHARED = pathlib.Path('/mnt/e/historiography-dissertation-pdfs')


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def first_pages(path, n=3):
    try:
        return subprocess.run(['pdftotext', '-f', '1', '-l', str(n), '-q', str(path), '-'], capture_output=True,
                              timeout=120).stdout.decode('utf-8', 'replace')
    except Exception:
        return ''


def extract_pdfs(archive, root, report):
    """List an archive (tar/tgz/zip) and extract only its PDF members, by base name, into a NEW
    directory <root>/<archive name>/ (reused on later runs). Nothing in it is ever executed."""
    import tarfile
    import zipfile
    dest = root / archive.name.replace('.', '_')
    out = []
    if dest.exists():
        return sorted(dest.glob('*.pdf'))
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as z:
                members = [(i.filename, i) for i in z.infolist() if i.filename.lower().endswith('.pdf') and not i.is_dir()]
                dest.mkdir(parents=True)
                for name, info in members:
                    target = dest / pathlib.PurePosixPath(name).name
                    with z.open(info) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    out.append(target)
        else:
            with tarfile.open(archive) as t:
                members = [m for m in t.getmembers() if m.isfile() and m.name.lower().endswith('.pdf')]
                dest.mkdir(parents=True)
                for m in members:
                    target = dest / pathlib.PurePosixPath(m.name).name
                    with t.extractfile(m) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    out.append(target)
    except Exception as e:
        report.append({'file': str(archive), 'result': f'archive unreadable ({type(e).__name__})'})
        return []
    report.append({'file': str(archive), 'result': f'archive: {len(out)} PDF(s) extracted to {dest}'})
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--drop', type=pathlib.Path, nargs='+', default=[FETCH / 'browser-drop', SHARED],
                    help='drop folders (default: browser-drop and the shared thesis PDF folder)')
    ap.add_argument('--since', default='2026-11-14',
                    help='in the shared thesis folder only consider files modified on or after this date '
                         '(it also holds other countries\' PDFs)')
    ap.add_argument('--fetch-dir', type=pathlib.Path, default=FETCH)
    ap.add_argument('--table', type=pathlib.Path,
                    default=ROOT / 'data/field-research/dnb-germany-harvest-2026-11-14/theses.csv.gz')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    with gzip.open(a.table, 'rt', newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    by_id = {r['dnb_id']: r for r in rows}
    for r in rows:
        for o in r['other_edition_ids'].split('|'):
            if o:
                by_id.setdefault(o, r)
    by_urn = {r['urn'].lower(): r for r in rows if r['urn']}
    words = {}
    by_sur = collections.defaultdict(list)
    for r in rows:
        w = [x for x in fold(r['title']).split() if len(x) >= 4][:8]
        words[r['dnb_id']] = w
        sur = fold(r['author'].split(',')[0]).split()
        if sur:
            by_sur[sur[-1]].append(r)
    mp = a.fetch_dir / 'manifest.csv'
    have, have_sha = set(), set()
    if mp.exists():
        with mp.open(newline='') as f:
            for m in csv.DictReader(f):
                if m['status'] == 'downloaded':
                    have.add(m['dnb_id'])
                    have_sha.add(m['sha256'])
    report, new = [], []
    since = dt.datetime.fromisoformat(a.since).replace(tzinfo=dt.timezone.utc).timestamp()
    cands = []  # (path, dnb id hinted by an archive name)
    for drop in a.drop:
        shared = drop.resolve() == SHARED.resolve()
        for p in sorted(drop.rglob('*') if not shared else drop.glob('*')):
            if not p.is_file() or p.name.endswith(('.crdownload', '.part', '.tmp')):
                continue
            if shared and p.stat().st_mtime < since:
                continue
            low = p.name.lower()
            if low.endswith(('.tgz', '.tar.gz', '.tar', '.zip')):
                for x in extract_pdfs(p, a.fetch_dir / 'browser-extracted', report):
                    cands.append((x, p.stem.split('.')[0]))
            elif low.endswith('.pdf'):
                cands.append((p, ''))
    for p, hint in cands:
        with open(p, 'rb') as f:
            if not f.read(1024).startswith(b'%PDF'):
                report.append({'file': str(p), 'result': 'not a PDF'})
                continue
        sha = sha256(p)
        if sha in have_sha:
            report.append({'file': str(p), 'result': 'already registered'})
            continue
        rec, rule = None, ''
        for m in re.finditer(r'\d{8,9}[\dX]', hint + ' ' + p.name):
            if m.group(0) in by_id:
                rec, rule = by_id[m.group(0)], 'dnb id in file name'
                break
        text = ''
        if not rec:
            text = first_pages(p)
            for src, s in (('file name', p.name), ('title page', text)):
                for m in re.finditer(r'urn:nbn:de:[a-z0-9:\-.]+', s.replace('\n', ''), re.I):
                    u = m.group(0).lower().rstrip('.-')
                    if u in by_urn:
                        rec, rule = by_urn[u], f'URN in {src}'
                        break
                if rec:
                    break
        if not rec:
            ft = set(fold(text).split())
            scored = []
            for sur, recs in by_sur.items():
                if sur not in ft:
                    continue
                for r in recs:
                    w = words[r['dnb_id']]
                    hit = sum(1 for x in w if x in ft)
                    if w and hit >= 3 and hit / len(w) >= 0.6:
                        scored.append((hit / len(w), hit, r))
            scored.sort(key=lambda x: (-x[0], -x[1]))
            if scored and (len(scored) == 1 or scored[0][:2] > scored[1][:2]):
                rec, rule = scored[0][2], f'title page (surname + {scored[0][1]} title words)'
            elif scored:
                report.append({'file': str(p), 'result': 'ambiguous: ' + ' | '.join(s[2]['dnb_id'] for s in scored[:4])})
                continue
        if not rec:
            report.append({'file': str(p), 'result': 'no match'})
            continue
        if rec['dnb_id'] in have:
            report.append({'file': str(p), 'result': f'record already downloaded ({rec["dnb_id"]})', 'dnb_id': rec['dnb_id'],
                           'screen': rec.get('screen', ''), 'title': rec['title'][:120]})
            continue
        dest = a.fetch_dir / 'browser' / f'{rec["dnb_id"]}.pdf'
        scr = rec.get('screen') or f'not screened ({rec["confidence"]})'
        new.append({'dnb_id': rec['dnb_id'], 'host': 'browser', 'status': 'downloaded', 'url': '', 'landing_url': '',
                    'sha256': sha, 'bytes': p.stat().st_size, 'path': str(dest),
                    'date': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'note': f'browser:{rule}; from {p.name}', 'screen': scr})
        report.append({'file': str(p), 'result': 'matched: ' + rule, 'dnb_id': rec['dnb_id'], 'screen': scr,
                       'title': rec['title'][:120]})
        have.add(rec['dnb_id'])
        have_sha.add(sha)
        if not a.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)  # copy, never move (copy2 fails on the NTFS mount's utime)
    if not a.dry_run and new:
        exists = mp.exists()
        with mp.open('a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=MAN_FIELDS)
            if not exists:
                w.writeheader()
            w.writerows(new)
    rp = a.fetch_dir / 'register-report.csv'
    if not a.dry_run:
        with rp.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'result', 'dnb_id', 'screen', 'title'], extrasaction='ignore')
            w.writeheader()
            w.writerows(report)
    for r in report:
        if r.get('screen') in ('adjacent', 'not-history', 'unclear', 'church-history'):
            print(f"  {r['screen']}: {r['dnb_id']} {r.get('title', '')[:80]} <- {r['file']}")
    c = collections.Counter(r['result'].split(':')[0].split(' (')[0] for r in report)
    print(f'{len(new)} newly registered{" (dry run)" if a.dry_run else ""}; ' + ', '.join(f'{k} {v}' for k, v in c.items()))


if __name__ == '__main__':
    main()
