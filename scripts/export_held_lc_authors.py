"""Held LC authors -> review items for outside adjudication (2026-11-07). An LC authority from the reviewed-books
routes is held when a live same-name key without an LC authority exists (key_review_books_lc twins()). One item per
authority still unkeyed, with what each side holds: the LC record (label, dates, 670 sources, its books in the
reviews) and every candidate key (label, anchors, AHA dissertation, works). The verdict asked: is the LC authority
one of the candidate keys, or none of them. Writes JSONL (one item per line).

    python3 scripts/export_held_lc_authors.py /mnt/e/kg-review/held-lc-authors.jsonl
"""
import gzip, json, sys
from pathlib import Path
import duckdb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State, DEFAULT_DIR
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
HELD = ['data/identifiers/review-books-lc-2026-11-07d/held-people.json',
        'data/identifiers/review-books-lc-qwen-2026-11-07/held-people.json',
        'data/identifiers/review-books-lc-qwen-2026-11-07b/held-people.json']
out = Path(sys.argv[1])
state = State.load(DEFAULT_DIR)
held = {}
for f in HELD:
    for x in json.load(open(ROOT / f)):
        held.setdefault(x['lcnaf'], x)
held = {k: v for k, v in held.items() if k not in state.anchor}
db = duckdb.connect(); db.execute('SET enable_progress_bar=false')
lc = {i: dict(label=l, birth=b, death=d, sources=list(s or [])[:8]) for i, l, b, d, s in db.execute(
    "SELECT lcid, label, birth, death, sources FROM '/mnt/e/lc-authorities/personal-names.parquet' WHERE lcid IN (SELECT unnest($1))",
    [[k[6:] for k in held]]).fetchall()}
db.execute('CREATE TABLE a(lcid VARCHAR, label VARCHAR, fam VARCHAR)')
db.executemany('INSERT INTO a VALUES (?,?,?)', [(k, v['label'], v['label'].split(',')[0]) for k, v in lc.items()])
books = {}
for lcid, t, y in db.execute("""SELECT a.lcid, r.title, r.date1 FROM read_parquet('/mnt/e/lc-bib-2016/index/headings-*.parquet') h
        JOIN a ON h.family = a.fam JOIN read_parquet('/mnt/e/lc-bib-2016/index/records-*.parquet') r ON trim(r.control) = trim(h.control)
        WHERE (h.uri <> '' AND split_part(rtrim(h.uri, '/'), '/', -1) = a.lcid) OR (h.uri = '' AND h.heading = a.label)""").fetchall():
    books.setdefault('lcnaf:' + lcid, []).append([t[:140], y])
aha = {}
for line in open(ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'):
    r = json.loads(line); aha['aha-phd:' + r['id']] = dict(title=r['title'], year=r['year'], department=r['department'])
G = ROOT / 'build/graph'
works = {}
for k, l, y, kind in db.execute(f"""SELECT a."from", w.label, w.year, w.kind FROM {keylog(G, 'authored')} a
        JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE NOT starts_with(w.label, 'Review')""").fetchall():
    works.setdefault(k, []).append([l[:140], y, kind])
n = 0
with open(out, 'w', encoding='utf-8') as fh:
    for lcnaf, x in sorted(held.items()):
        cands = []
        for t in x['twins']:
            for k in state.lookup(t):
                if any(c['key'] == k for c in cands) or state.keys[k]['status'] not in ('active', 'provisional'):
                    continue
                an = sorted(state.keys[k]['anchors'])
                cands.append(dict(key=k, label=state.keys[k]['label'], anchors=an[:12],
                                  aha_dissertations=[aha[a] for a in an if a in aha],
                                  works=sorted(works.get(k, []), key=lambda w: w[1] or 0)[:15]))
        if not cands:
            continue
        fh.write(json.dumps(dict(item=lcnaf, lc=dict(id=lcnaf, **lc.get(lcnaf[6:], dict(label=x['label']))),
                                 lc_books=sorted(books.get(lcnaf, []), key=lambda b: b[1] or '')[:12], candidates=cands), ensure_ascii=False) + '\n')
        n += 1
print('items', n)
