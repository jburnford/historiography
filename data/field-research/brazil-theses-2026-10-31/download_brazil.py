"""Download open PDFs of Brazilian History doctorates matched to CAPES (2026-11-01).

User, 2026-10-31/11-01: add Brazil ("start the catalog; I'll figure out space"; then "162 gb
free on E now").

Input: candidates.json from scripts/brazil_match_capes.py (CAPES doctorate + repository record).
The PDF is found by the repository's kind:
- a direct link in the record (UFF programme site ``/stricto/td/<n>.pdf``; USP item pages' ``publico/`` files);
- DSpace 7 (UFMG, UFPA, UFES, UFU): ``/server/api/pid/find?id=<handle>`` -> item ->
  ``bundles?embed=bitstreams``, the largest PDF in the ORIGINAL bundle;
- DSpace 6 (UERJ, UFPE, UFRJ): the item page ``/handle/<handle>``, its linked ``/bitstream/...pdf``.
FGV is skipped: its repository answers with a bot challenge page ("Making sure you're not a
bot!", 2026-11-01), which is not circumvented.
Every URL is checked against its host's robots.txt (longest-match rule, as in
scripts/brazil_oai_harvest.py) before it is fetched; hosts are paced 3 seconds apart. Never the
CAPES ``DS_URL_TEXTO_COMPLETO`` links (sucupira.capes.gov.br disallows everything). 401/403 are
recorded as restricted and not pursued. Stops when E: has less than 4 GB free.

Output: downloads.jsonl (resumable; one row per candidate key) and PDFs in STORAGE.
"""
import hashlib
import json
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from brazil_oai_harvest import robots_rules  # noqa: E402

STORAGE = Path('/mnt/e/historiography-dissertation-pdfs/brazil-theses-2026-10-31/pdf')
UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'
HANDLE_HOSTS = {'1843': 'repositorio.ufmg.br', '2011': 'repositorio.ufpa.br', '10': 'repositorio.ufes.br',
                '11422': 'pantheon.ufrj.br', '1': 'www.bdtd.uerj.br:8443', '10438': 'repositorio.fgv.br'}
DSPACE7 = {'repositorio.ufmg.br', 'repositorio.ufpa.br', 'repositorio.ufes.br', 'repositorio.ufu.br'}
BLOCKED = {'repositorio.fgv.br': 'bot_challenge'}
# certifi's CA bundle: the system store lacks GlobalSign Root R46, which anchors the RNP ICPEdu
# certificates of Brazilian universities (www.bdtd.uerj.br:8443 failed verification without it).
TLS = ssl.create_default_context(cafile=certifi.where())
LAST, ROBOTS = {}, {}


def pace(url):
    host = urllib.parse.urlsplit(url).netloc
    wait = 3 - (time.time() - LAST.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    LAST[host] = time.time()


def allowed(url):
    p = urllib.parse.urlsplit(url)
    root = f'{p.scheme}://{p.netloc}'
    if root not in ROBOTS:
        try:
            body = fetch(root + '/robots.txt', check=False)[0].decode('utf-8', 'replace')
            ROBOTS[root] = [] if '<html' in body.lower() else robots_rules(body)
        except Exception:
            ROBOTS[root] = []
    best = (-1, True)
    for allow, pat in ROBOTS[root]:
        rx = '^' + re.escape(pat).replace(r'\*', '.*').replace(r'\$', '$')
        if re.match(rx, p.path or '/') and (len(pat) > best[0] or (len(pat) == best[0] and allow)):
            best = (len(pat), allow)
    return best[1]


def fetch(url, check=True, timeout=180):
    if check and not allowed(url):
        raise PermissionError(f'robots.txt disallows {url}')
    pace(url)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout, context=TLS) as r:
        return r.read(), r.geturl(), r.headers.get('Content-Type', '')


def handle_of(url):
    m = re.search(r'(?:/handle/|hdl\.handle\.net/)(\d+/[^/?#\s]+)', url or '')
    return m.group(1) if m else None


def item_host(url, handle):
    host = urllib.parse.urlsplit(url).netloc
    if host == 'www.bdtd.uerj.br':  # port 443 sends only the leaf certificate; 8443 sends the full chain
        return 'www.bdtd.uerj.br:8443'
    return HANDLE_HOSTS.get(handle.split('/')[0]) if host == 'hdl.handle.net' else host


def pdf_urls(c):
    rec = c['repository']
    if rec.get('pdfs'):
        return rec['pdfs']
    if rec.get('pdf'):
        return [rec['pdf']]
    h = handle_of(rec.get('url'))
    if not h:
        return []
    host = item_host(rec['url'], h)
    if host in BLOCKED:
        raise LookupError(BLOCKED[host])
    if host in DSPACE7:
        body, final, _ = fetch(f'https://{host}/server/api/pid/find?id={h}')
        item = json.loads(body)
        b, _, _ = fetch(item['_links']['self']['href'] + '/bundles?embed=bitstreams')
        bits = []
        for bundle in json.loads(b)['_embedded']['bundles']:
            if bundle['name'] != 'ORIGINAL':
                continue
            for s in bundle['_embedded']['bitstreams']['_embedded']['bitstreams']:
                if s['name'].lower().endswith('.pdf'):
                    bits.append((s.get('sizeBytes') or 0, s['_links']['content']['href']))
        return [u for _, u in sorted(bits, reverse=True)]
    body, final, _ = fetch(f'https://{host}/handle/{h}')
    text = body.decode('utf-8', 'replace')
    links = re.findall(r'href="([^"]*/bitstream/[^"]+?\.pdf[^"]*)"', text, re.I)
    out = []
    for l in links:
        u = urllib.parse.urljoin(final, l.split('?')[0] if 'sequence' not in l else l)
        if u not in out:
            out.append(u)
    return out


def multipart(c):
    """USP item pages list every file of a thesis: volumes (V1, V2), parts, or chapters with separate
    Bibliografia/Fontes files. All are needed, since the bibliography is usually in the last one."""
    return len(c['repository'].get('pdfs') or []) > 1


def download_parts(c, row, urls):
    files = []
    for n, u in enumerate(urls, 1):
        try:
            body, final, ctype = fetch(u, timeout=600)
        except Exception as e:
            return dict(row, status='error', error=f'part {n}: {e!r}'[:300])
        if not body.startswith(b'%PDF'):
            return dict(row, status='not_pdf', error=f'part {n}: {ctype}')
        path = STORAGE / f"{c['key']}.part{n:02d}.pdf"
        path.write_bytes(body)
        files.append(dict(url=final, path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
    return dict(row, status='downloaded', url=files[0]['url'], path=files[0]['path'], files=files,
                bytes=sum(f['bytes'] for f in files), sha256=files[0]['sha256'])


def download(c, log):
    row = dict(key=c['key'], inst=c['inst'], checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        urls = pdf_urls(c)
    except PermissionError as e:
        return dict(row, status='robots_disallowed', error=str(e))
    except LookupError as e:
        return dict(row, status=str(e))
    except urllib.error.HTTPError as e:
        return dict(row, status='restricted' if e.code in (401, 403) else 'error', error=f'HTTP {e.code} (lookup)')
    except Exception as e:
        return dict(row, status='error', error=repr(e)[:300])
    if not urls:
        return dict(row, status='no_pdf')
    row['links'] = urls
    if multipart(c):
        return download_parts(c, row, urls)
    for u in urls[:3]:
        try:
            body, final, ctype = fetch(u, timeout=600)
        except PermissionError as e:
            row.update(status='robots_disallowed', error=str(e))
            continue
        except urllib.error.HTTPError as e:
            row.update(status='restricted' if e.code in (401, 403) else 'error', error=f'HTTP {e.code}')
            continue
        except Exception as e:
            row.update(status='error', error=repr(e)[:300])
            continue
        if not body.startswith(b'%PDF'):
            row.update(status='not_pdf', error=ctype)
            continue
        path = STORAGE / f"{c['key']}.pdf"
        path.write_bytes(body)
        return dict(row, status='downloaded', url=final, path=str(path), bytes=len(body),
                    sha256=hashlib.sha256(body).hexdigest())
    return row


def main():
    STORAGE.mkdir(parents=True, exist_ok=True)
    cands = json.loads((HERE / 'candidates.json').read_text())
    parts_needed = {c['key'] for c in cands if multipart(c)}
    log_path = HERE / 'downloads.jsonl'
    done = set()
    if log_path.exists():
        for line in open(log_path, encoding='utf-8'):
            r = json.loads(line)
            if r['status'] == 'downloaded' and r['key'] in parts_needed and not r.get('files'):
                continue  # saved before multi-part support (first volume only): fetch all parts
            if r['status'] in ('downloaded', 'restricted', 'no_pdf', 'robots_disallowed', 'not_pdf', 'bot_challenge'):
                done.add(r['key'])
    todo = [c for c in cands if c['key'] not in done]
    print(f'{len(cands)} candidates, {len(todo)} to do', flush=True)
    counts = {}
    with open(log_path, 'a', encoding='utf-8') as log:
        for i, c in enumerate(todo, 1):
            if shutil.disk_usage(STORAGE).free < 4 * 1024 ** 3:
                print('STOP: under 4 GB free on E:', flush=True)
                break
            row = download(c, log)
            log.write(json.dumps(row, ensure_ascii=False) + '\n')
            log.flush()
            counts[row['status']] = counts.get(row['status'], 0) + 1
            if i % 25 == 0:
                print(f'{i}/{len(todo)} {counts}', flush=True)
    print('BRAZIL-DOWNLOAD-DONE', counts, flush=True)


if __name__ == '__main__':
    main()
