"""Request items for the Qwen review run (jstor_llm_reviews.py), all book reviews, in shards (2026-11-07).

Same item as the pilot (job 26351198): {id, journal, year, meta_title, creators, head, tail, title_found}.
- `head`: 1,800 characters from 400 before the first four words of JSTOR's title, when they are found in the text;
  otherwise the first 3,000 characters.
- `tail`: the last 1,800 characters, when the text runs past `head`.

Items quote review text: they go to E: and to Nibi project storage only, never to git.

Output: /mnt/e/jstor-fulltext-2026-11-06/llm-review-items/part-NN.jsonl (N_SHARDS shards, round-robin).

    python3 jstor_llm_review_items.py [N_SHARDS]
"""
import gzip, json, os, re, sqlite3, sys, unicodedata

E = '/mnt/e/jstor-fulltext-2026-11-06'
OUT = f'{E}/llm-review-items'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def item(r, meta):
    j, y, t, cr = meta
    mt = re.sub(r'\s+', ' ', re.sub(r'^Book Review\s*:\s*', '', t or '')).strip()
    txt = re.sub(r'\s+', ' ', ' '.join(r['full_text'])).strip()
    if len(txt) < 200:
        return None
    words = re.findall(r'[a-z0-9]{3,}', fold(mt))[:4]
    pos = -1
    if len(words) >= 2:
        m = re.search(r'[^a-z0-9]+(?:[a-z0-9]{1,2}[^a-z0-9]+)*'.join(map(re.escape, words)), fold(txt))
        pos = m.start() if m else -1
    if pos >= 0:
        start = max(0, pos - 400); head = txt[start:start + 1800]
    else:
        start = 0; head = txt[:3000]
    tail = txt[-1800:] if len(txt) > start + len(head) else ''
    return dict(id=r['iid'], journal=j, year=y, meta_title=mt[:300], creators=cr or '', head=head, tail=tail,
                title_found=pos >= 0)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
    meta = {i.split(':')[-1]: (j, y, t, cr) for i, j, y, t, cr in c.execute(
        "select item_id, journal_title, year, title, creators_string from records where genre='book_review_as_deposited'")}
    os.makedirs(OUT, exist_ok=True)
    fhs = [open(f'{OUT}/part-{k:02d}.jsonl.tmp', 'w', encoding='utf-8') for k in range(n)]
    k = short = 0
    with gzip.open(f'{E}/reviews.jsonl.gz', 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            it = item(r, meta.get(r['iid'], (None, None, None, None)))
            if it is None:
                short += 1
                continue
            fhs[k % n].write(json.dumps(it, ensure_ascii=False) + '\n')
            k += 1
    for i, fh in enumerate(fhs):
        fh.close()
        os.replace(f'{OUT}/part-{i:02d}.jsonl.tmp', f'{OUT}/part-{i:02d}.jsonl')
    print(f'{k} items in {n} shards; {short} reviews under 200 characters skipped')


if __name__ == '__main__':
    main()
