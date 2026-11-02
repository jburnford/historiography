"""Scan legacy Sucupira records and download authorized thesis PDFs (2026-11-01).

User decision, 2026-11-01 ("Scan + download"), after the trade-off was set out: the legacy host
sucupira-legado.capes.gov.br has no robots.txt (404), while sucupira.capes.gov.br disallows all
crawlers; the files are ones their authors authorized for publication ("O trabalho possui
divulgação autorizada"). Gentle by design: one request at a time, 7 seconds apart, identifying
user agent, and only the 2013+ doctorates of the browser handoff (universities whose own
repositories block scripts), unless --all is given.

For each record (CAPES ``id_trabalho``, from the catalogue's full-text link):
1. GET the legacy record page (cookie session). Parse the authorization line, the attachment name,
   advisor, examination committee (name + category) and funders.
2. When an attachment is listed, submit the page's ``download`` form exactly as the link's onclick
   does (fields ``download``, ``javax.faces.ViewState`` and ``download:link_download_arquivo``)
   and save the response if it is a PDF.

Output: ``sucupira-records.jsonl`` (one row per record: authorization, committee, funders, file
status) and, for saved files, a ``downloads.jsonl`` row (source ``sucupira_legado``) with the PDF
in the Brazil PDF store. Resumable: records already in sucupira-records.jsonl are skipped.

    python3 data/field-research/brazil-theses-2026-10-31/download_sucupira_legado.py
"""
import argparse
import hashlib
import html
import http.cookiejar
import json
import re
import shutil
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from brazil_match_capes import capes_doctorates, doc_key  # noqa: E402

HOST = 'https://sucupira-legado.capes.gov.br'
UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'
STORAGE = Path('/mnt/e/historiography-dissertation-pdfs/brazil-theses-2026-10-31/pdf')
DELAY = 7.0
TLS = ssl.create_default_context(cafile=certifi.where())
_last = [0.0]


def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), urllib.request.HTTPSHandler(context=TLS))


def request(op, url, data=None, timeout=300):
    wait = DELAY - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Referer': url})
    with op.open(req, timeout=timeout) as r:
        return r.read(), r.headers.get('Content-Type', '')


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def parse(page):
    auth = re.search(r'id="sigiloso">([^<]*)<', page)
    anexo = re.search(r'id="download:link_download_arquivo"[^>]*>([^<]*)</a>', page)
    form = re.search(r'<form id="download"[^>]*action="([^"]+)"', page)
    state = re.search(r'<form id="download".*?name="javax.faces.ViewState"[^>]*value="([^"]+)"', page, re.S)
    advisor = re.search(r'id="orientador">([^<]*)<', page)
    committee = []
    banca = page.split('Banca Examinadora', 1)[-1].split('Financiadores', 1)[0]
    for name, cat in re.findall(r'<tr>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*</tr>', banca):
        if name.strip() != 'Nome':
            committee.append(dict(name=text(name), category=text(cat)))
    funders = [text(f) for f in re.findall(r'id="j_idt\d+:\d+:descricao">([^<]*)<', page)]
    return dict(authorization=text(auth.group(1)) if auth else None,
                attachment=text(anexo.group(1)) if anexo else None,
                advisor=text(advisor.group(1)) if advisor else None, committee=committee, funders=funders,
                form_action=html.unescape(form.group(1)) if form else None,
                view_state=state.group(1) if state else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='every 2013+ doctorate with a CAPES link, not only the handoff')
    ap.add_argument('--limit', type=int)
    a = ap.parse_args()
    downloaded, keys = set(), None
    log_path = HERE / 'downloads.jsonl'
    if log_path.exists():
        for line in open(log_path, encoding='utf-8'):
            r = json.loads(line)
            if r['status'] == 'downloaded':
                downloaded.add(r['key'])
    if not a.all:
        keys = {q['key'] for q in json.loads((HERE / 'browser-handoff/queue.json').read_text())}
    rec_path = HERE / 'sucupira-records.jsonl'
    seen = set()
    if rec_path.exists():
        seen = {json.loads(l)['key'] for l in open(rec_path, encoding='utf-8')}
    todo = []
    for d in capes_doctorates(HERE):
        k = doc_key(d)
        m = re.search(r'id_trabalho=(\d+)', d.get('fulltext_url') or '')
        if m and k not in downloaded and k not in seen and (keys is None or k in keys):
            todo.append((k, d, m.group(1)))
    todo.sort(key=lambda t: -t[1]['year'])
    if a.limit:
        todo = todo[:a.limit]
    print(f'{len(todo)} records to scan', flush=True)
    STORAGE.mkdir(parents=True, exist_ok=True)
    counts = {}
    with open(rec_path, 'a', encoding='utf-8') as rec_log, open(log_path, 'a', encoding='utf-8') as dl_log:
        for i, (k, d, tid) in enumerate(todo, 1):
            if shutil.disk_usage(STORAGE).free < 4 * 1024 ** 3:
                print('STOP: under 4 GB free on E:', flush=True)
                break
            op = opener()
            url = f'{HOST}/sucupira/public/consultas/coleta/trabalhoConclusao/viewTrabalhoConclusao.jsf?popup=true&id_trabalho={tid}'
            row = dict(key=k, inst=d['inst'], id_trabalho=tid, checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
            try:
                page = request(op, url)[0].decode('utf-8', 'replace')
                info = parse(page)
                row.update({x: info[x] for x in ('authorization', 'attachment', 'advisor', 'committee', 'funders')})
                if not info['attachment'] or not info['form_action'] or not info['view_state']:
                    row['file_status'] = 'no_attachment'
                else:
                    form = urllib.parse.urlencode({'download': 'download', 'javax.faces.ViewState': info['view_state'],
                                                   'download:link_download_arquivo': 'download:link_download_arquivo'}).encode()
                    body, ctype = request(op, urllib.parse.urljoin(url, info['form_action']), data=form, timeout=600)
                    if body.startswith(b'%PDF'):
                        path = STORAGE / f'{k}.pdf'
                        path.write_bytes(body)
                        row['file_status'] = 'downloaded'
                        dl_log.write(json.dumps(dict(key=k, inst=d['inst'], checked_at=row['checked_at'], status='downloaded',
                                                     source='sucupira_legado', url=url, path=str(path), bytes=len(body),
                                                     sha256=hashlib.sha256(body).hexdigest()), ensure_ascii=False) + '\n')
                        dl_log.flush()
                    else:
                        row['file_status'] = f'not_pdf ({ctype})'
            except Exception as e:
                row['file_status'] = 'error'
                row['error'] = repr(e)[:300]
            rec_log.write(json.dumps(row, ensure_ascii=False) + '\n')
            rec_log.flush()
            counts[row['file_status'].split(' ')[0]] = counts.get(row['file_status'].split(' ')[0], 0) + 1
            if i % 20 == 0 or i == len(todo):
                print(f'{i}/{len(todo)} {counts}', flush=True)
    print('SUCUPIRA-DONE', counts, flush=True)


if __name__ == '__main__':
    main()
