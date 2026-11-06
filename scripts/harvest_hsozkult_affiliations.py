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
import urllib.parse
import urllib.request
from pathlib import Path

PAGES = Path('/home/jic823/hnet-reviews/data/html/classic')
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'
OLD = re.compile(r'hsozkult\.geschichte\.hu-berlin\.de/(rezensionen|tagungsberichte)/id=(\d+)')
NEW = re.compile(r'hsozkult\.de/(publicationreview|conferencereport)/id/((?:rezbuecher|tagungsberichte)-\d+)')
CREDIT = re.compile(r'(?:Rezensiert für|Rezensiert fuer|Reviewed for|Bericht von)\s*H-Soz-(?:u-)?Kult\s*(?:von|by)?\s*:?\s*(.{3,200}?)(?:\s{2,}|\n|$)', re.I)


def get(url):
    for wait in (0, 5, 30):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            pass
    return None


def hsk_url(hnet_id):
    p = PAGES / f'{hnet_id}.html.gz'
    if not p.exists():
        return None
    t = gzip.open(p, 'rt', errors='replace').read()
    m = NEW.search(t)
    if m:
        return f'hsozkult.de/{m.group(1)}/id/{m.group(2)}'
    m = OLD.search(t)
    if m:
        kind = 'publicationreview/id/rezbuecher' if m.group(1) == 'rezensionen' else 'conferencereport/id/tagungsberichte'
        return f'hsozkult.de/{kind}-{m.group(2)}'
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ids', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    ids = sorted(set(json.loads(args.ids.read_text())))
    done = json.loads(args.out.read_text()) if args.out.exists() else {}
    for n, i in enumerate(ids):
        if i in done:
            continue
        url = hsk_url(i)
        rec = dict(url=url)
        if url:
            avail = get('https://archive.org/wayback/available?url=' + urllib.parse.quote(url))
            snap = ((json.loads(avail).get('archived_snapshots') or {}).get('closest') or {}).get('url') if avail else None
            rec['snapshot'] = snap
            if snap:
                page = get(snap)
                if page:
                    text = html.unescape(re.sub(r'<[^>]+>', '\n', page))
                    text = re.sub(r'[ \t]+', ' ', text)
                    m = CREDIT.search(re.sub(r'\n\s*', '  ', text))
                    rec['credit'] = m.group(1).strip(' ,|') if m else None
            time.sleep(1)
        done[i] = rec
        if n % 50 == 0:
            args.out.write_text(json.dumps(done, ensure_ascii=False, indent=0))
            print(f'{n}/{len(ids)}', flush=True)
    args.out.write_text(json.dumps(done, ensure_ascii=False, indent=0))
    print(json.dumps(dict(ids=len(ids), with_url=sum(1 for r in done.values() if r.get('url')),
                          with_credit=sum(1 for r in done.values() if r.get('credit')))))


if __name__ == '__main__':
    main()
