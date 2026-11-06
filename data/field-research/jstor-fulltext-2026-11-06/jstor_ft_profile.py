"""Profile the JSTOR full-text delivery (2026-11-06) and pull out the reference lists. Local only: nothing here is committed."""
import gzip, json, sqlite3, sys, time
from collections import Counter, defaultdict
SRC = '/mnt/e/7d08e73a-0591-4390-a0d3-dc940b06cdb6.jsonl.gz'
OUT = '/mnt/e/jstor-fulltext-2026-11-06'
meta = {}
c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
for iid, j, y, g, sub in c.execute('select item_id, journal_title, year, genre, subtype from records where included'):
    meta[iid.split(':')[-1]] = (j, y, g, sub)
print('metadata', len(meta), flush=True)
keys = Counter(); n = 0; t0 = time.time()
by_genre = defaultdict(lambda: [0, 0, 0, 0])    # items, with refs, refs, chars
by_journal = defaultdict(lambda: [0, 0, 0])
by_decade = defaultdict(lambda: [0, 0, 0])
empty_text = 0; unknown = 0; seen = set()
slim = gzip.open(f'{OUT}/references.jsonl.gz', 'wt', encoding='utf-8')
items = open(f'{OUT}/items.tsv', 'w', encoding='utf-8')
items.write('iid\tpages\tchars\trefs\n')
with gzip.open(SRC, 'rt', encoding='utf-8') as f:
    for line in f:
        r = json.loads(line); n += 1
        keys.update(r.keys())
        iid = r['iid']; seen.add(iid)
        ft = r.get('full_text') or []; refs = r.get('references') or []
        chars = sum(len(p) for p in ft)
        if not chars: empty_text += 1
        j, y, g, sub = meta.get(iid, ('?', None, '?', '?'))
        if iid not in meta: unknown += 1
        G = by_genre[g]; G[0] += 1; G[1] += bool(refs); G[2] += len(refs); G[3] += chars
        J = by_journal[j]; J[0] += 1; J[1] += bool(refs); J[2] += len(refs)
        D = by_decade[(y // 10 * 10) if y else None]; D[0] += 1; D[1] += bool(refs); D[2] += len(refs)
        if refs: slim.write(json.dumps({'iid': iid, 'references': refs}, ensure_ascii=False) + '\n')
        items.write(f'{iid}\t{len(ft)}\t{chars}\t{len(refs)}\n')
        if n % 50000 == 0: print(n, round(time.time() - t0), flush=True)
slim.close(); items.close()
rep = dict(records=n, distinct=len(seen), keys=keys, empty_text=empty_text, not_in_request_metadata=unknown,
           requested_not_delivered=len(set(meta) - seen),
           by_genre={k: dict(items=v[0], with_refs=v[1], refs=v[2], chars=v[3]) for k, v in by_genre.items()},
           by_decade={str(k): dict(items=v[0], with_refs=v[1], refs=v[2]) for k, v in sorted(by_decade.items(), key=lambda x: x[0] or 0)},
           by_journal={k: dict(items=v[0], with_refs=v[1], refs=v[2]) for k, v in sorted(by_journal.items(), key=lambda x: -x[1][0])})
open(f'{OUT}/profile.json', 'w').write(json.dumps(rep, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in rep.items() if k not in ('by_journal',)}, indent=1, ensure_ascii=False))
