#!/usr/bin/env python3
"""Register PDFs saved by hand from the Brazil browser handoff (2026-11-01).

The user saves thesis PDFs from ``browser-handoff.html`` into the drop folder on E: under any
filename. Each new PDF is validated (``checked_file`` from register_uk_browser_downloads.py: PDF
header, %%EOF, pdfinfo page count, SHA-256) and matched to a CAPES History doctorate from the text
of its first four pages:
- a file named ``<key>.pdf`` is that doctorate;
- otherwise the doctorate whose folded title (first 45 characters) appears in the text and whose
  author shares at least two name tokens with it. Exactly one such doctorate registers the file;
  none or several leave it for review in ``browser-handoff/unmatched.json``.
Files are not moved or copied. Registered files get a ``downloads.jsonl`` row (status
``downloaded``, source ``user_browser_download``) and their CAPES record in
``browser-candidates.json``, both read by the Brazil ingest. Rerunning skips files already
registered (by SHA-256).

    python3 scripts/register_brazil_browser_downloads.py
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from brazil_match_capes import capes_doctorates, doc_key, fold, name_tokens  # noqa: E402
from register_uk_browser_downloads import checked_file  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / 'data/field-research/brazil-theses-2026-10-31'
DROP = Path('/mnt/e/historiography-dissertation-pdfs/brazil-theses-2026-10-31/browser-drop')


def first_pages(path):
    r = subprocess.run(['pdftotext', '-l', '4', '-enc', 'UTF-8', str(path), '-'], capture_output=True,
                       text=True, timeout=120)
    return fold(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--drop', default=str(DROP))
    a = ap.parse_args()
    docs = {}
    for d in capes_doctorates(OUT):
        docs[doc_key(d)] = d
    log_path = OUT / 'downloads.jsonl'
    known_sha = set()
    if log_path.exists():
        for line in open(log_path, encoding='utf-8'):
            r = json.loads(line)
            if r.get('sha256'):
                known_sha.add(r['sha256'])
    bc_path = OUT / 'browser-candidates.json'
    browser = json.loads(bc_path.read_text()) if bc_path.exists() else {}
    unmatched, added = [], 0
    pdfs = sorted(p for p in Path(a.drop).rglob('*') if p.suffix.lower() == '.pdf')
    with open(log_path, 'a', encoding='utf-8') as log:
        for p in pdfs:
            try:
                info = checked_file(p)
            except Exception as e:
                unmatched.append(dict(path=str(p), reason=str(e)))
                continue
            if info['sha256'] in known_sha:
                continue
            if p.stem in docs:
                hits = [p.stem]
            else:
                text = first_pages(p)
                hits = []
                for k, d in docs.items():
                    t = fold(d['title'])[:45]
                    if len(t) >= 20 and t in text and len(name_tokens(d['author']) & set(text.split())) >= 2:
                        hits.append(k)
            if len(hits) != 1:
                unmatched.append(dict(path=str(p), reason='no match' if not hits else 'several matches',
                                      candidates=hits[:5]))
                continue
            k = hits[0]
            d = docs[k]
            row = dict(key=k, inst=d['inst'], checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                       status='downloaded', source='user_browser_download', path=info['path'],
                       bytes=info['bytes'], pages=info['pages'], sha256=info['sha256'])
            log.write(json.dumps(row, ensure_ascii=False) + '\n')
            browser[k] = dict(d, key=k, match='browser_text' if p.stem != k else 'browser_filename')
            known_sha.add(info['sha256'])
            added += 1
            print(f'registered {p.name} -> {k} ({d["inst"]} {d["year"]}, {d["author"].title()})')
    bc_path.write_text(json.dumps(browser, ensure_ascii=False, indent=0))
    (OUT / 'browser-handoff').mkdir(exist_ok=True)
    (OUT / 'browser-handoff/unmatched.json').write_text(json.dumps(unmatched, ensure_ascii=False, indent=1))
    print(f'{len(pdfs)} PDFs in drop folder; {added} newly registered; {len(browser)} registered in all; '
          f'{len(unmatched)} need review (browser-handoff/unmatched.json)')


if __name__ == '__main__':
    main()
