"""H-Soz-Kult reviewers' affiliations from the Internet Archive's copies of the reviews (2026-11-05).

H-Net crossposts H-Soz-Kult reviews without the reviewer's affiliation, and hsozkult.de sits behind a bot check
(not to be circumvented). The Wayback Machine's archived copies of the original review pages (web archive
snapshots of the publisher's pages, not user uploads) print "Rezensiert für H-Soz-Kult von <name>, <institution>".
A Claude agent found the route (person-dups-2026-11-05b, batch 12); this makes it a harvest. For each H-Net review
id given: the saved H-Net page (/home/jic823/hnet-reviews/data/html/classic/<id>.html.gz) gives the old H-Soz-Kult
address (hsozkult.geschichte.hu-berlin.de/rezensionen/id=N, /tagungsberichte/id=N), mapped to today's
(hsozkult.de/publicationreview/id/rezbuecher-N, conferencereport/id/tagungsberichte-N); the Wayback availability API
gives a snapshot, read for the credit line. About one request a second. Output: JSON {hnet id: {url, snapshot,
credit}}; resumable.

    python3 scripts/harvest_hsozkult_affiliations.py --ids ids.json --out /mnt/e/hsozkult-affiliations.json
"""
import argparse
import gzip
import html
import json
import re
import time
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import urllib.request
from pathlib import Path

PAGES = Path('/home/jic823/hnet-reviews/data/html/classic')
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'
OLD = re.compile(r'hsozkult\.geschichte\.hu-berlin\.de/(rezensionen|tagungsberichte)/id=(\d+)')
NEW = re.compile(r'hsozkult\.de/(publicationreview|conferencereport)/id/((?:rezbuecher|tagungsberichte)-\d+)')
CREDIT = re.compile(r'(?:Rezensiert für|Rezensiert fuer|Reviewed for|Bericht von)\s*H-Soz-(?:u-)?Kult\s*(?:von|by)?\s*:?\s*(.{3,200}?)(?:\s{2,}|\n|$)', re.I)


def get(url):
    """(text, final url); (None, None) when the archive has no copy (404) or keeps failing."""
    for wait in (0, 30, 120, 600):           # Wayback refuses connections for minutes when pushed
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return r.read().decode('utf-8', 'replace'), r.geturl()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, None
        except Exception:
            pass
    return None, None


def hsk_urls(hnet_id):
    """The review's hsozkult.de address and, when the H-Net page gives it, the older hu-berlin.de address
    (reviews from before about 2012 were archived only there)."""
    p = PAGES / f'{hnet_id}.html.gz'
    if not p.exists():
        return []
    t = gzip.open(p, 'rt', errors='replace').read()
    urls = []
    m = NEW.search(t)
    if m:
        urls.append(f'hsozkult.de/{m.group(1)}/id/{m.group(2)}')
    m = OLD.search(t)
    if m:
        kind = 'publicationreview/id/rezbuecher' if m.group(1) == 'rezensionen' else 'conferencereport/id/tagungsberichte'
        if not urls:
            urls.append(f'hsozkult.de/{kind}-{m.group(2)}')
        urls.append(m.group(0))
    return urls


def one(i):
    urls = hsk_urls(i)
    rec = dict(url=urls[0] if urls else None, snapshot=None)
    for url in urls:
        # one request per address: the Wayback raw-content form redirects to the nearest snapshot
        page, final = get('https://web.archive.org/web/2026id_/http://' + url)
        time.sleep(2)
        if page:
            rec['snapshot'] = final
            text = html.unescape(re.sub(r'<[^>]+>', '\n', page))
            text = re.sub(r'[ \t]+', ' ', text)
            m = CREDIT.search(re.sub(r'\n\s*', '  ', text))
            rec['credit'] = m.group(1).strip(' ,|') if m else None
            if rec['credit']:
                break
    return i, rec


def save(path, done):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(done, ensure_ascii=False, indent=0))
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ids', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--workers', type=int, default=1)
    args = ap.parse_args()
    ids = sorted(set(json.loads(args.ids.read_text())))
    done = json.loads(args.out.read_text()) if args.out.exists() else {}
    # misses from the faster 2026-11-06 run (new address only, connections refused) are tried once more
    todo = [i for i in ids if i not in done or (done[i].get('url') and not done[i].get('snapshot') and not done[i].get('retried'))]
    with ThreadPoolExecutor(args.workers) as pool:
        for n, (i, rec) in enumerate(pool.map(one, todo), 1):
            done[i] = dict(rec, retried=True) if i in done else rec
            if n % 50 == 0:
                save(args.out, done)
                print(f'{len(done)}/{len(ids)}', flush=True)
    save(args.out, done)
    print(json.dumps(dict(ids=len(ids), with_url=sum(1 for r in done.values() if r.get('url')),
                          with_credit=sum(1 for r in done.values() if r.get('credit')))))


if __name__ == '__main__':
    main()
