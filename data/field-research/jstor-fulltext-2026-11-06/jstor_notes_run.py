"""Run the rule note parser (jstor_notes.citations) over every JSTOR note list; rows to E: (2026-11-06).

Streams references.jsonl.gz (made by jstor_ft_profile.py), all genres that carry notes. Output: one gzip JSON-lines
part per 10,000 items in /mnt/e/jstor-fulltext-2026-11-06/rules/, each written to a temporary name and renamed,
so a rerun skips finished parts (E: has dropped off once). A row is one citation:
  iid, note, cit, rule, kind, conf, ref, authors, surnames, title, container, place, publisher, year, volume, pages
No note text is written. An article that takes over 20 s is recorded as a timeout and skipped.

    python3 jstor_notes_run.py            # ~30 min, one CPU, < 1 GB RAM
"""
import gzip, json, os, signal, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jstor_notes as J  # noqa: E402

SRC = '/mnt/e/jstor-fulltext-2026-11-06/references.jsonl.gz'
OUT = Path('/mnt/e/jstor-fulltext-2026-11-06/rules')
PART = 10000
KEYS = ('note', 'cit', 'rule', 'kind', 'conf', 'ref', 'authors', 'surnames', 'title', 'container', 'place', 'publisher',
        'year', 'volume', 'pages', 'editors')


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def main():
    OUT.mkdir(exist_ok=True)
    signal.signal(signal.SIGALRM, _alarm)
    t0 = time.time(); n = 0; part = 0; fh = None; skip = False; stats = dict(items=0, rows=0, timeouts=0)
    with gzip.open(SRC, 'rt', encoding='utf-8') as f:
        for line in f:
            if n % PART == 0:
                if fh:
                    fh.close(); os.replace(tmp, final)
                    print(part, n, round(time.time() - t0), flush=True)
                part = n // PART
                final = OUT / f'part-{part:03d}.jsonl.gz'; tmp = OUT / f'part-{part:03d}.jsonl.gz.tmp'
                skip = final.exists()
                fh = None if skip else gzip.open(tmp, 'wt', encoding='utf-8', compresslevel=5)
            n += 1
            if skip:
                continue
            r = json.loads(line)
            signal.alarm(20)
            try:
                rows = J.citations(r['references'])
            except Timeout:
                fh.write(json.dumps({'iid': r['iid'], 'rule': 'timeout'}) + '\n'); stats['timeouts'] += 1
                continue
            except Exception as e:   # one bad article must not stop a 30-minute pass
                fh.write(json.dumps({'iid': r['iid'], 'rule': 'error', 'error': repr(e)[:200]}) + '\n'); stats['errors'] = stats.get('errors', 0) + 1
                continue
            finally:
                signal.alarm(0)
            stats['items'] += 1
            for row in rows:
                out = {'iid': r['iid']}
                out.update({k: row[k] for k in KEYS if row.get(k) not in (None, [], '')})
                fh.write(json.dumps(out, ensure_ascii=False) + '\n'); stats['rows'] += 1
    if fh:
        fh.close(); os.replace(tmp, final)
    print('done', n, stats, round(time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
