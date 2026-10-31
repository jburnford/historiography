"""Download open French History doctorates through theses.fr (2026-10-30).

User, 2026-10-30: "we can then target more French dissertations to get them to 2000".

Input: candidates.json, the ABES open-data export "Thèses soutenues en France depuis 1985" (data.gouv.fr,
January 2024 snapshot) screened for History disciplines (art, law, literary, philosophy, music,
archaeology and architecture histories excluded), accessible == "oui", defended, and not already in
the dissertation manifest by title.

For each thesis, theses.fr/api/v1/document/<nnt> lists the deposited files on the awarding
university's server, or redirects to the thesis's HAL record (theses.hal.science/tel-...), whose file
is at <record>/document (not disallowed by HAL's robots.txt). The first file that is a PDF is saved to
STORAGE. Theses whose document endpoint answers 403 are restricted to French higher-education members
("Accès réservé aux membres de l'enseignement supérieur français") or to libraries; they are recorded
and not pursued. theses.fr asks for a crawl
delay of 5 seconds. University hosts are checked against their robots.txt and paced 3 seconds per host.
The script stops when E: has less than 4 GB free. Output: downloads.jsonl (resumable).
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
import urllib.request
import urllib.robotparser
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
STORAGE = Path('/mnt/e/historiography-dissertation-pdfs/france-theses-2026-10-30/pdf')
UA = 'historiography-research (+https://github.com/jburnford/historiography; jic823@usask.ca)'
ROBOTS, LAST = {}, {}


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.geturl()


def allowed(url):
    host = urlsplit(url).scheme + '://' + urlsplit(url).netloc
    if host not in ROBOTS:
        rp = urllib.robotparser.RobotFileParser()
        try:
            body, _ = get(host + '/robots.txt', timeout=30)
            rp.parse(body.decode('utf-8', 'replace').splitlines())
        except Exception:
            rp.parse([])          # no robots file: allowed
        ROBOTS[host] = rp
    return ROBOTS[host].can_fetch(UA, url)


HAL_RECORD = re.compile(r'^https?://(theses\.hal\.science|tel\.archives-ouvertes\.fr|hal\.science)/(tel|hal)-\d+(v\d+)?/?$')
SKIP_HOSTS = ('purl.org', 'inbox.hal.science', 'cdn.mathjax.org')
ASSET = re.compile(r'\.(css|js|png|ico|svg|webmanifest|jpg|gif|woff2?)(\?|$)', re.I)


def file_urls(links):
    """Absolute candidate file URLs: HAL records become <record>/document; page assets are dropped."""
    out = []
    for url in links:
        if url.startswith('//') or not url.startswith('http') or ASSET.search(url):
            continue
        if any(h in urlsplit(url).netloc for h in SKIP_HOSTS):
            continue
        url = url.rstrip('/') + '/document' if HAL_RECORD.match(url) else url
        if url not in out:
            out.append(url)
    # a HAL page links the whole portal; when a record or PDF link is present, try only those
    files = [u for u in out if u.endswith('/document') or u.lower().endswith('.pdf')]
    return files or out


def retry(row):
    """Rows worth another try: HAL records or relative links the first run missed, network failures
    and server errors (not 403s, which are access restrictions)."""
    return row['status'] in ('not_pdf', 'error') and '403' not in row.get('error', '') and \
        any(HAL_RECORD.match(u) for u in row.get('links') or []) or 'unknown url type' in row.get('error', '') or \
        row.get('error', '').startswith('URLError') or 'HTTP Error 500' in row.get('error', '')


def pace(host, seconds):
    wait = LAST.get(host, 0) + seconds - time.time()
    if wait > 0:
        time.sleep(wait)
    LAST[host] = time.time()


def main():
    STORAGE.mkdir(parents=True, exist_ok=True)
    cands = json.loads((HERE / 'candidates.json').read_text())
    cands.sort(key=lambda d: d.get('date_soutenance') or '', reverse=True)
    out = HERE / 'downloads.jsonl'
    rows = [json.loads(l) for l in out.open()] if out.exists() else []
    latest = {r['nnt']: r for r in rows}
    done = {n for n, r in latest.items() if not retry(r)}
    with out.open('a') as f:
        for d in cands:
            if d['nnt'] in done:
                continue
            if shutil.disk_usage(STORAGE).free < 4e9:
                print('stopping: less than 4 GB free on E:', file=sys.stderr)
                break
            rec = dict(nnt=d['nnt'], checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
            try:
                pace('theses.fr', 5)
                body, _ = get(f"https://theses.fr/api/v1/document/{d['nnt']}")
                links = re.findall(r'href="([^"]+)"', body.decode('utf-8', 'replace'))
                rec['links'] = links
                rec['status'] = 'no_file_listed'
                for url in file_urls(links)[:3]:
                    if not allowed(url):
                        rec['status'] = 'robots_disallowed'
                        continue
                    pace(urlsplit(url).netloc, 3)
                    data, final = get(url, timeout=300)
                    if data[:4] != b'%PDF':
                        rec['status'] = 'not_pdf'
                        continue
                    path = STORAGE / f"{d['nnt']}.pdf"
                    path.write_bytes(data)
                    rec.update(status='downloaded', url=final, path=str(path), bytes=len(data),
                               sha256=hashlib.sha256(data).hexdigest())
                    break
            except Exception as e:   # recorded, not retried automatically
                rec['status'] = 'error'
                rec['error'] = f'{type(e).__name__}: {e}'[:300]
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            f.flush()


if __name__ == '__main__':
    main()
