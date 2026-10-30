"""Download open Oxford DPhil PDFs from ORA for theses in History departments (2026-10-29).

Input: raw/ora-landing.jsonl (ora_landing.py) and raw/datacite-oxford.json (authors, supervisors).
A row is downloaded when ORA records an Oxford doctoral award, the department screen in
scripts/uk_dissertation_scope.py places it in History (or history and philosophy of science), and
the landing page offers an open PDF (citation_pdf_url). Other departments are listed in
outside-history.csv for title review; nothing is downloaded for them yet.

Robots.txt allows /objects/ and /files/. One request every 5 seconds. A file is kept only if it
starts with %PDF. Output: downloads.jsonl (resumable; one row per DOI), PDFs under STORAGE.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from uk_dissertation_scope import classify  # noqa: E402

STORAGE = Path('/mnt/e/historiography-dissertation-pdfs/oxford-ora-2026-10-29')
UA = 'historiography-research (+https://github.com/jburnford/historiography; jic823@usask.ca)'


def slug(doi):
    return re.sub(r'[^a-z0-9]+', '-', doi.split('/', 1)[1].lower()).strip('-')


def main():
    if not STORAGE.parent.is_dir():
        raise SystemExit('E: is not mounted')
    STORAGE.mkdir(exist_ok=True)
    meta = json.loads((HERE / 'raw/datacite-oxford.json').read_text())
    out = HERE / 'downloads.jsonl'
    done = {json.loads(l)['doi'] for l in out.open()} if out.exists() else set()
    outside = []
    rows = [json.loads(l) for l in (HERE / 'raw/ora-landing.jsonl').open() if l.strip()]
    with out.open('a') as f:
        for r in rows:
            if r.get('error') or r.get('award_level') != 'Doctoral' or 'Oxford' not in (r.get('awarding_institution') or ''):
                continue
            scope, basis = classify(r['title'], [r['department']] if r.get('department') else [], '', 'oxford-ora')
            if not scope.startswith('explicit_history'):
                outside.append(dict(doi=r['doi'], year=r['year'], department=r.get('department') or '', scope=scope,
                                    pdf=bool(r.get('pdf_url')), title=r['title']))
                continue
            if r['doi'] in done:
                continue
            m = meta.get(r['doi'], {})
            rec = dict(doi=r['doi'], id='ora-' + slug(r['doi']), url=r['url'], title=r['title'], year=r['year'],
                       authors=m.get('creators', []), supervisors=m.get('supervisors') or r.get('supervisors', []),
                       department=r.get('department'), college=r.get('college'), award_type=r.get('award_type'),
                       history_scope=scope, basis=basis, pdf_url=r.get('pdf_url'))
            if not r.get('pdf_url'):
                rec['status'] = 'no_open_pdf'
            else:
                path = STORAGE / f"{rec['id']}.pdf"
                try:
                    req = urllib.request.Request(r['pdf_url'], headers={'User-Agent': UA})
                    with urllib.request.urlopen(req, timeout=180) as resp:
                        body = resp.read()
                    if body[:4] != b'%PDF':
                        rec['status'] = 'not_pdf'
                    else:
                        path.write_bytes(body)
                        rec.update(status='downloaded', path=str(path), bytes=len(body),
                                   sha256=hashlib.sha256(body).hexdigest())
                except Exception as e:  # recorded, not retried automatically
                    rec['status'] = 'error'
                    rec['error'] = f'{type(e).__name__}: {e}'
                time.sleep(5)
            rec['checked_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            f.flush()
    with (HERE / 'outside-history.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['doi', 'year', 'department', 'scope', 'pdf', 'title'])
        w.writeheader()
        w.writerows(sorted(outside, key=lambda x: (x['department'], x['year'] or 0)))


if __name__ == '__main__':
    main()
