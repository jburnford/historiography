"""Every OpenAlex work whose primary topic is in History (subfield 1202) or History and Philosophy of Science (1207),
plus every dissertation with such a topic anywhere (2026-11-08; user paid for OpenAlex access: "we need to figure
something out to use up the $10"). About 8.4M works + 0.36M dissertations; list calls at 200 records cost about
$0.0001 each, so the whole pull is about 44k calls (~$4.5).

What it feeds:
- missing dissertations (type dissertation, with repository links) for the user to download;
- publications of the people in the graph (books, chapters, articles with authorships: names, ORCIDs, institutions):
  Ben Bradley's book and chapters had no route in (no ORCID; LC bib file ends 2016);
- citations: referenced_works between works (OpenAlex resolves only part of a reference list, but adds what
  Crossref lacks for some publishers), mapped to graph works through DOIs.

Year slices are harvested with cursors in parallel; each slice is written to E: as one jsonl.gz by rename, so a run
resumes. Metadata only (no abstracts). The API key is read from ~/.config/openalex/key and never printed or logged.

    python3 scripts/openalex_history_harvest.py count
    python3 scripts/openalex_history_harvest.py harvest --workers 6
"""
import argparse, concurrent.futures as cf, gzip, json, os, sys, threading, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path('/mnt/e/openalex-history-2026-11-08')
KEY = Path(os.path.expanduser('~/.config/openalex/key'))
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography)'
SELECT = ('id,doi,title,display_name,publication_year,publication_date,type,language,authorships,primary_location,'
          'locations,ids,biblio,primary_topic,referenced_works,referenced_works_count,cited_by_count,open_access,'
          'best_oa_location,is_retracted')
SETS = {'history': 'primary_topic.subfield.id:1202|1207',
        'dissertations': 'topics.subfield.id:1202|1207,type:dissertation'}
calls = 0
lock = threading.Lock()


def get(params, key):
    global calls
    q = dict(params, api_key=key)
    url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(q)
    for i in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
                with lock:
                    calls += 1
                return json.load(r)
        except Exception as e:
            code = getattr(e, 'code', None)
            if code in (400, 401, 403):
                raise RuntimeError(f'OpenAlex refused the request (HTTP {code}); check the key or the credit balance')
            time.sleep(min(120, 2 * 2 ** i))
    raise RuntimeError('OpenAlex: gave up after retries')


def slices():
    out = []
    for name, f in SETS.items():
        out.append((name, 'pre1900', f + ',publication_year:<1900'))
        for y in range(1900, 2027):
            out.append((name, str(y), f + f',publication_year:{y}'))
        out.append((name, 'later', f + ',publication_year:>2026'))
    return out


def harvest_slice(s, key):
    name, label, f = s
    dest = OUT / name / f'{label}.jsonl.gz'
    if dest.exists():
        return name, label, -1
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.part')
    n, cursor = 0, '*'
    with gzip.open(tmp, 'wt', encoding='utf-8') as out:
        while cursor:
            d = get(dict(filter=f, per_page=200, cursor=cursor, select=SELECT), key)
            for w in d['results']:
                out.write(json.dumps(w, ensure_ascii=False) + '\n')
            n += len(d['results'])
            cursor = d['meta'].get('next_cursor') if d['results'] else None
    os.replace(tmp, dest)
    return name, label, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('count', 'harvest'))
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()
    key = KEY.read_text().strip()
    if args.phase == 'count':
        tot = 0
        for name, f in SETS.items():
            n = get(dict(filter=f, per_page=1), key)['meta']['count']
            tot += n
            print(f'{name}: {n:,} works, ~{n // 200 + 1:,} list calls')
        print(f'total ~{tot // 200:,} list calls (~${tot / 200 * 0.0001:.2f} at $0.0001 per list call)')
        return
    t0 = time.time(); total = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(harvest_slice, s, key) for s in slices()]
        for fu in cf.as_completed(futs):
            name, label, n = fu.result()
            if n >= 0:
                total += n
                print(f'{name} {label}: {n:,} works; {total:,} so far, {calls:,} calls, {time.time() - t0:.0f}s', flush=True)
    print(f'done: {total:,} works, {calls:,} calls this run', flush=True)


if __name__ == '__main__':
    main()
