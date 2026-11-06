#!/usr/bin/env python3
"""Mexican History doctorates: screen the harvested records, then download their PDFs (2026-11-04).

    python3 scripts/mexico_download.py screen            # -> candidates.jsonl (all sources harvested so far)
    python3 scripts/mexico_download.py download [src...] # PDFs to E:, resumable, logged in downloads.jsonl

The screen reads metadata only; the title page check (Doctor/Doctorado en Historia) comes at
registration, as for Chicago. Per source:
- unam: TesiUNAM records whose "Título otorgado" is exactly Doctorado en Historia (not Historia del Arte)
  and open access.
- colmex: doctoral theses (type_conacyt doctoralThesis) of the Centro de Estudios Históricos; academic_degree
  is filled in for only one record in ten.
- ibero: "Tesis - (Doctorado en Historia)" in dc.description.
- colmich: doctoral theses in the Centro de Estudios Históricos community (com_1016_25).
- colsan: doctoral theses in the Doctorado en Historia collection (col_1013_47).
- mora: every doctoral thesis (the Instituto's doctorate is in history; confirmed on the title page).

PDFs are found per platform: DSpace JSPUI item pages (Mora, Colegio de Michoacán, Colegio de San Luis),
DSpace 7 REST (Ibero), UNAM's ru.dgb.unam.mx item pages (reached by handle), and Hyrax file-set downloads
(El Colegio de México). robots.txt allows each path used; no bot check is ever circumvented; TLS stays
verified.
"""
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/mexico-theses-2026-11-04'
PDF = Path('/mnt/e/historiography-dissertation-pdfs/mexico-theses-2026-11-04/pdf')
UA = 'historiography-research/0.1 (jic823@usask.ca; dissertation citation study)'
CTX = ssl.create_default_context(cafile=certifi.where())
DELAY = {'ibero': 2.0}
DEFAULT_DELAY = 3.0
MIN_FREE = 20 * 1024 ** 3  # stop if E: falls under 20 GB


def oai(source):
    p = D / 'oai' / f'{source}.jsonl'
    return [json.loads(l) for l in p.open(encoding='utf-8')] if p.exists() else []


def first(r, k):
    v = r.get(k) or []
    return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else '')


def doctoral(r):
    return any('doctoralThesis' in t or 'doctorado' in t.lower() for t in r.get('type', []))


def base(source, rid, r, item_url):
    return {'source': source, 'id': f'mx_{source}_{rid}', 'item_url': item_url,
            'title': first(r, 'title'), 'author': first(r, 'creator'), 'year': (re.search(r'(1[89]|20)\d\d', first(r, 'date')) or [''])[0],
            'advisors': r.get('contributor', []), 'record': r}


def screen():
    out = []
    for r in oai('unam'):
        degree = [re.sub(r'.*Título otorgado:\s*', '', d).strip() for d in r.get('description', []) if 'Título otorgado' in d]
        open_access = any('Acceso abierto' in x for x in r.get('rights', []))
        if degree and degree[0] == 'Doctorado en Historia' and open_access:
            handle = next((m.group(0) for x in r.get('identifier', []) for m in [re.search(r'https?://hdl\.handle\.net/\S+?(?=[\s)]|$)', x)] if m), '')
            c = base('unam', r['oai_id'].rsplit(':', 1)[1], r, handle)
            c['advisors'] = [a.strip() for x in r.get('contributor', []) for a in re.sub(r'^Asesor:\s*', '', x).split(';') if a.strip()]
            out.append(c)
    colmex = D / 'colmex' / 'theses.jsonl'
    for r in (json.loads(l) for l in colmex.open(encoding='utf-8')) if colmex.exists() else []:
        if 'doctoralThesis' in (r.get('type_conacyt') or '') and 'Centro de Estudios Históricos' in (r.get('center') or []):
            out.append({'source': 'colmex', 'id': f"mx_colmex_{r['id']}", 'item_url': r['url'], 'title': first(r, 'title'),
                        'author': first(r, 'creator'), 'year': first(r, 'date_created')[:4], 'advisors': r.get('director') or [],
                        'record': r})
    for r in oai('ibero'):
        if any(re.search(r'Doctorado en Historia\)', d, re.I) for d in r.get('description', [])):
            out.append(base('ibero', r['oai_id'].rsplit(':', 1)[1].replace('/', '_'), r, first(r, 'identifier')))
    for src, tag in [('colmich', 'com_1016_25'), ('colsan', 'col_1013_47'), ('mora', None)]:
        for r in oai(src):
            if doctoral(r) and (tag is None or tag in r.get('sets', [])):
                url = next((u for u in r.get('identifier', []) if '/handle/' in u), '')
                out.append(base(src, r['oai_id'].rsplit(':', 1)[1].replace('/', '_'), r, url.replace('http://', 'https://')))
    out = list({c['id']: c for c in out}.values())  # a harvest stopped mid-page can save a page twice
    with (D / 'candidates.jsonl').open('w', encoding='utf-8') as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    from collections import Counter
    print(len(out), 'candidates', dict(Counter(c['source'] for c in out)))


def get(url, tries=3, binary=False):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
                body = r.read()
                return (body, r.headers.get('content-type', '')) if binary else body.decode('utf-8', 'replace')
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            code = getattr(e, 'code', None)
            if code and code < 500 and code != 429:
                raise
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f'failed: {url}')


def pdf_urls(c):
    """The PDF links for one candidate, in order (a few theses come in parts)."""
    src = c['source']
    if src in ('mora', 'colmich', 'colsan'):
        page = get(c['item_url'])
        host = urllib.parse.urlsplit(c['item_url'])
        links = re.findall(r'href="(/jspui/bitstream/[^"]+?\.pdf)"', page, re.I)
        return list(dict.fromkeys(f'{host.scheme}://{host.netloc}{l}' for l in links))
    if src == 'ibero':
        handle = c['item_url'].split('/handle/', 1)[1]
        item = json.loads(get(f'https://ri.ibero.mx/server/api/pid/find?id={handle}'))
        bundles = json.loads(get(item['_links']['bundles']['href']))['_embedded']['bundles']
        orig = next((b for b in bundles if b['name'] == 'ORIGINAL'), None)
        if not orig:
            return []
        bits = json.loads(get(orig['_links']['bitstreams']['href']))['_embedded']['bitstreams']
        return [b['_links']['content']['href'] for b in bits if b['name'].lower().endswith('.pdf')]
    if src == 'unam':
        page = get(c['item_url'])  # handle -> ru.dgb.unam.mx/items/<uuid>
        links = re.findall(r'href="(?:https://ru\.dgb\.unam\.mx)?(/bitstreams/[0-9a-f-]{36}/download)"', page)
        return list(dict.fromkeys(f'https://ru.dgb.unam.mx{l}' for l in links))
    if src == 'colmex':
        rid = (c['record'].get('representative_id') or {}).get('id')
        return [f'https://repositorio.colmex.mx/downloads/{rid}'] if rid else []
    return []


def download(sources):
    import shutil
    log = D / 'downloads.jsonl'
    done = {json.loads(l)['id'] for l in log.open()} if log.exists() else set()
    cands = [json.loads(l) for l in (D / 'candidates.jsonl').open(encoding='utf-8')]
    todo = [c for c in cands if c['id'] not in done and (not sources or c['source'] in sources)]
    print(f'{len(todo)} to download', flush=True)
    with log.open('a', encoding='utf-8') as out:
        for n, c in enumerate(todo, 1):
            if shutil.disk_usage(PDF.parent.parent).free < MIN_FREE:
                raise SystemExit('E: under 20 GB free; stopping')
            delay = DELAY.get(c['source'], DEFAULT_DELAY)
            rec = {'id': c['id'], 'source': c['source'], 'item_url': c['item_url']}
            try:
                urls = pdf_urls(c)
                files = []
                for i, u in enumerate(urls):
                    time.sleep(delay)
                    body, ctype = get(u, binary=True)
                    if not body.startswith(b'%PDF'):
                        raise RuntimeError(f'not a PDF ({ctype}, {len(body)} bytes) at {u}')
                    path = PDF / c['source'] / (c['id'] + (f'_p{i + 1}' if len(urls) > 1 else '') + '.pdf')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(body)
                    files.append({'url': u, 'path': str(path), 'bytes': len(body)})
                rec.update(status='ok' if files else 'no_pdf', files=files)
            except Exception as e:  # noqa: BLE001 - logged per thesis, the run goes on
                rec.update(status='error', error=repr(e)[:300])
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            out.flush()
            if n % 25 == 0:
                print(f"{time.strftime('%H:%M:%S')} {n}/{len(todo)}", flush=True)
            time.sleep(delay)
    print('done', flush=True)


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:] or ['']
    if cmd == 'screen':
        screen()
    elif cmd == 'download':
        download(rest)
    else:
        raise SystemExit(__doc__)
