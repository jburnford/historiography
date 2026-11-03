"""Withdraw the book links key_reviews.unlinked_reviews no longer makes (applied 2026-11-02 before the rule existed):
`reviews` claims of collective-review records repeating another record's citation, and of Reviews in History
landing pages; and book works reached only through those records. Writes proposal-2.json beside this file."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
import duckdb  # noqa: E402
from identifiers import DEFAULT_DIR, State, materialise  # noqa: E402
from key_reviews import SOURCE, UP, lc_book_lccn, norm, unlinked_reviews  # noqa: E402

state = State.load(DEFAULT_DIR)
reviews = duckdb.connect().execute(f"""SELECT r.source, r.review_id, r.reviewer, r.reviewer_affiliation, r.review_date,
        r.network, r.source_url, b.book_id, r.book_title, r.book_author
    FROM read_parquet('{UP}/export/reviews.parquet') r
    LEFT JOIN read_parquet('{UP}/books/review_book.parquet') b USING (source, review_id)
    WHERE r.is_real ORDER BY r.source, r.review_id""").fetchall()
identified = {r[0] for r in duckdb.connect().execute(
    f"SELECT book_id FROM read_parquet('{UP}/books/books.parquet') WHERE isbn13 IS NOT NULL OR lccn IS NOT NULL").fetchall()}
unlinked = unlinked_reviews(reviews, identified)
ops, books_kept = [], {r[7] for r in reviews if (r[0], r[1]) not in unlinked and r[7]}
for (source, rid), why in sorted(unlinked.items()):
    for k in state.lookup(f'reviews:{SOURCE[source]}:{rid}'):
        ops.append(dict(event='withdraw', key=k, basis=f'book link not kept: {why}'))
dropped = {r[7] for r in reviews if (r[0], r[1]) in unlinked and r[7]} - books_kept
for bk in sorted(dropped):
    for k in state.lookup(f'hnet-book:{bk}'):
        if not any(state.lookup(a) == [k] for a in state.keys[k]['anchors'] if a.startswith('lccn:')):
            ops.append(dict(event='withdraw', key=k, basis='reviewed book reached only through records without a book'))
_, lc_title = lc_book_lccn([Path('/mnt/e/lc-authorities/books-2016.ndjson'), Path('/mnt/e/lc-authorities/books.ndjson')])
isbn = dict(duckdb.connect().execute(f"SELECT book_id, isbn13 FROM read_parquet('{UP}/books/books.parquet')").fetchall())
gone = {o['key'] for o in ops}
for bk, title in sorted(isbn.items()):
    for k in state.lookup(f'hnet-book:{bk}'):
        if k not in gone and norm(state.keys[k]['label']).startswith('reviews in history') and (lc_title.get(bk) or title):
            ops.append(dict(event='relabel', key=k, label=lc_title.get(bk) or f'ISBN {title}',
                            basis="the catalogue's title was a parsing failure ('Reviews in History'); LC's title or the ISBN"))
            gone.add(k)
materialise(state, dict(basis='reviews repair', ops=ops), 'dry-run', 'dry-run')
(HERE / 'proposal-2.json').write_text(json.dumps(dict(
    basis='Collective reviews and landing pages: book links withdrawn (key_reviews.unlinked_reviews)',
    decided_by='rule', ops=ops), ensure_ascii=False, indent=1) + '\n')
print(len(unlinked), 'records;', len(ops), 'withdrawals')
