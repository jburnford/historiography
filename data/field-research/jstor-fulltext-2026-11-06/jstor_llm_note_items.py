"""Request items for the Qwen notes run (jstor_llm_notes.py): the articles the rules parse badly (2026-11-07).

Selection is read from notes-article-quality.parquet, which has one row per article with the rule outcome counts.
- **Outcomes:** each rule citation is one of full, resolved back-reference, unresolved back-reference, partial, primary or other (as in jstor_llm_eval.py).
- **Bad share:** (unresolved + partial + other) / all.
- **Kept:** articles with a bad share of at least --min-bad (default 0.4), except book reviews. The brief takes citations from article, review-essay and review-article notes only.
- **Pieces:** taken from the JSTOR note list (references.jsonl.gz), or, for articles without one, from the notes cut out of the page text (textnotes-pieces.jsonl.gz). Each is cut to 1,500 characters.
- **Requests:** 8 consecutive pieces each, as in the pilot (job 26350911): {id, iid, era, journal, year, first, pieces}.

Items quote note text: they go to E: and to Nibi project storage only, never to git.

Output: /mnt/e/jstor-fulltext-2026-11-06/llm-note-items/part-NNN.jsonl. Each shard holds whole articles and about --shard-pieces pieces.

    python3 jstor_llm_note_items.py [--min-bad 0.4] [--shard-pieces 80000]
"""
import argparse, gzip, json, os

import duckdb

E = '/mnt/e/jstor-fulltext-2026-11-06'
OUT = f'{E}/llm-note-items'


def era(y):
    return 'pre1940' if (y or 0) < 1940 else '1940-79' if y < 1980 else '1980+'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-bad', type=float, default=0.4)
    ap.add_argument('--shard-pieces', type=int, default=80000)
    a = ap.parse_args()
    db = duckdb.connect()
    sel = {i: (s, j, y) for i, s, j, y in db.execute(f"""
        select iid, src, journal, year from '{E}/notes-article-quality.parquet'
        where genre <> 'book_review_as_deposited'
          and (unres + partial + other) >= {a.min_bad} * (full_ + res + unres + partial + prim + other)
          and (full_ + res + unres + partial + prim + other) > 0""").fetchall()}
    print(len(sel), 'articles selected', flush=True)
    os.makedirs(OUT, exist_ok=True)
    shard, n_shard, fh, tmp = 0, 0, None, None
    stats = dict(articles=0, requests=0, pieces=0)

    def open_shard():
        nonlocal fh, tmp
        tmp = f'{OUT}/part-{shard:03d}.jsonl.tmp'
        fh = open(tmp, 'w', encoding='utf-8')

    def close_shard():
        fh.close(); os.replace(tmp, tmp[:-4])

    open_shard()
    for src, fn, key in (('list', f'{E}/references.jsonl.gz', 'references'), ('text', f'{E}/textnotes-pieces.jsonl.gz', 'pieces')):
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            for line in f:
                iid = line[9:45]
                s = sel.get(iid)
                if not s or s[0] != src:
                    continue
                r = json.loads(line)
                pieces = [(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))[:1500] for p in r[key]]
                if not pieces:
                    continue
                _, j, y = s
                for k in range(0, len(pieces), 8):
                    fh.write(json.dumps(dict(id=f'{iid}:{k}', iid=iid, era=era(y), journal=j, year=y, first=k,
                                             pieces=pieces[k:k + 8]), ensure_ascii=False) + '\n')
                    stats['requests'] += 1
                stats['articles'] += 1; stats['pieces'] += len(pieces); n_shard += len(pieces)
                if n_shard >= a.shard_pieces:
                    close_shard(); shard += 1; n_shard = 0; open_shard()
    close_shard()
    print(stats, shard + 1, 'shards')


if __name__ == '__main__':
    main()
