"""Journals each ORCID-keyed person has published in, from OpenAlex's works under that ORCID (2026-11-06).

For key_review_reviewers.py, beside Crossref's works under the ORCID and the ORCID record itself: OpenAlex also lists
the works its author profile for that ORCID holds that carry no ORCID in their Crossref deposit (older articles,
reviews). CAUTION: OpenAlex builds author profiles by algorithmic clustering, so a profile can hold a namesake's
work; links made on this source say so in their basis and can be withdrawn by it.

Works are fetched 50 ORCIDs to a request (`filter=author.orcid:A|B|...`, journal venues only, 100 to a page), and
each work's venue and year go to the batch's ORCIDs that its authorships name. The API key is read from
~/.config/openalex/key (never written out). A list call costs $0.0001 (free $1 a day, then prepaid usage): the
harvest stops when less than --reserve-usd is left and resumes where it stopped. Four batches run at a time. Output: JSON {orcid: [[venue, year], ...]}.

    python3 scripts/harvest_openalex_venues.py --orcids orcids.json --out /mnt/e/openalex-venues-2026-11-06.json
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEY = Path.home() / '.config/openalex/key'
API = 'https://api.openalex.org/works'


def fetch(params):
    """One API call: the JSON and the budget left in USD (the free daily allowance plus prepaid usage)."""
    url = API + '?' + urllib.parse.urlencode(params)
    for wait in (0, 10, 60, 300):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'historiography-research/1.0'}),
                                        timeout=120) as r:
                h = r.headers
                usd = float(h.get('x-ratelimit-remaining-usd') or 0) + float(h.get('x-ratelimit-prepaid-remaining-usd') or 0)
                return json.load(r), usd
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f'HTTP {e.code}') from None
        except (urllib.error.URLError, TimeoutError):
            pass
    raise RuntimeError('OpenAlex unavailable')


def fetch_batch(batch, key):
    """Venues and years of every journal work under a batch of ORCIDs: ({orcid: [[venue, year]]}, calls, usd left)."""
    got, calls, usd, cursor = {o: [] for o in batch}, 0, None, '*'
    while cursor:
        d, usd = fetch({'filter': f"author.orcid:{'|'.join(batch)},primary_location.source.type:journal",
                        'per_page': 100, 'cursor': cursor, 'api_key': key,
                        'select': 'publication_year,primary_location,authorships'})
        calls += 1
        for w in d['results']:
            venue = (((w.get('primary_location') or {}).get('source')) or {}).get('display_name')
            if not venue or not w.get('publication_year'):
                continue
            for a in w.get('authorships') or []:
                o = ((a.get('author') or {}).get('orcid') or '').rsplit('/', 1)[-1]
                if o in got:
                    got[o].append([venue, w['publication_year']])
        cursor = d['meta'].get('next_cursor') if d['results'] else None
    return {o: sorted({tuple(x) for x in v}) for o, v in got.items()}, calls, usd


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--orcids', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--batch', type=int, default=50)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--reserve-usd', type=float, default=0.5, help='stop when less than this is left')
    args = ap.parse_args()
    key = KEY.read_text().strip()
    orcids = list(dict.fromkeys(json.loads(args.orcids.read_text())))   # in the given order
    done = json.loads(args.out.read_text()) if args.out.exists() else {}
    todo = [o for o in orcids if o not in done]
    batches = [todo[i:i + args.batch] for i in range(0, len(todo), args.batch)]
    print(f'{len(orcids)} ORCIDs, {len(todo)} to fetch in {len(batches)} batches', flush=True)
    calls, n = 0, 0
    with ThreadPoolExecutor(args.threads) as pool:
        for start in range(0, len(batches), args.threads * 4):
            for got, c, usd in pool.map(lambda b: fetch_batch(b, key), batches[start:start + args.threads * 4]):
                done.update(got)
                calls += c
                n += 1
            args.out.write_text(json.dumps(done, ensure_ascii=False))
            print(f'{n}/{len(batches)} batches, calls {calls}, ${usd:.2f} left', flush=True)
            if usd < args.reserve_usd:
                print('budget low: stopping', flush=True)
                break
    print(json.dumps(dict(orcids=len(done), with_venues=sum(1 for v in done.values() if v), calls=calls)))


if __name__ == '__main__':
    main()
