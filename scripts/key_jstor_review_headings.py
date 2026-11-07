"""Books named in JSTOR review headings -> review works and `reviews` claims (2026-11-06). Writes a proposal.

The JSTOR full-text session read the heading at the start of each JSTOR book review (author or editors, title, place,
publisher, year, pages) and matched the book to graph works as it matches note citations (handover
data/field-research/jstor-fulltext-2026-11-06/HANDOVER-review-books.md; candidates on E:,
/mnt/e/jstor-fulltext-2026-11-06/review-book-candidates.parquet). This reaches the 117,047 reviews JSTOR leaves
untitled, which the metadata route (key_jstor_reviews.py, by JSTOR's title) cannot. Taken here:
- basis 'strong' (main title and an author's or editor's family name agree, imprint year within one) or 'title+year'
  (a unique title of three or more words on a work with no person);
- one graph work only (n_works = 1), and not already linked;
- 'edition?' and 'no_year' rows are left for a separate relation;
- held: a book that is a thesis record (the review is of the published book, another work), a JSTOR journal piece
  (doi:10.2307 or jstor-item anchor on an article), and a review DOI already anchored on a book key (a stray review
  DOI on the book: the claim would say the book reviews itself).
A review not yet keyed gets a work on its DOI (lower case) with `year:` and `journal:` members from the request
metadata (/mnt/e/JSTOR_history_citation_graph/records.sqlite) and the reviewer as printed (`reviewer-name:`, the
signature's metadata name, conf >= 0.75; review-signatures-rules.jsonl.gz). No reviewer keys are minted (reviewers
join people only on a non-name fact: key_review_signatures.py). One claim per review and book:
`jstor-heading-reviews:<doi>:<work>`. Parsed fields only; no review text is read or committed.

    python3 scripts/key_jstor_review_headings.py --out data/identifiers/jstor-review-headings-2026-11-06
"""
import argparse
import gzip
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise

FT = Path('/mnt/e/jstor-fulltext-2026-11-06')
CANDIDATES = FT / 'review-book-candidates.parquet'
SIGNATURES = FT / 'review-signatures-rules.jsonl.gz'
GRAPH = ROOT / 'build/graph'
RECORDS = Path('/mnt/e/JSTOR_history_citation_graph/records.sqlite')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    rows = db.execute(f"""SELECT iid, lower(trim(doi)), work, basis, book_year, untitled FROM '{CANDIDATES}'
        WHERE basis IN ('strong', 'title+year') AND n_works = 1 AND NOT known AND doi IS NOT NULL AND work IS NOT NULL
        ORDER BY iid, book, work""").fetchall()
    kind, jstor_piece = {}, set()
    for k, kd, anchors in db.execute(f"SELECT key, kind, anchors FROM '{GRAPH}/work.parquet'").fetchall():
        for cur in state.lookup(k):
            kind[cur] = kd
            if kd == 'article' and any(a.startswith(('doi:10.2307/', 'jstor-item:')) for a in anchors):
                jstor_piece.add(cur)
    by_review = defaultdict(list)
    for iid, doi, work, basis, byear, untitled in rows:
        by_review[(iid, doi)].append((work, basis, byear, untitled))
    signers = {}
    with gzip.open(SIGNATURES, 'rt', encoding='utf-8') as f:
        for line in f:
            s = json.loads(line)
            if s.get('creator') and (s.get('conf') or 0) >= 0.75:
                signers[s['iid']] = ' '.join(s['creator'].split())
    meta = {}
    c = sqlite3.connect(f'file:{RECORDS}?mode=ro', uri=True)
    for iid, year, journal in c.execute('SELECT item_id, year, journal_title FROM records'):
        meta[iid] = (year, journal)
    report, ops, seen_claims = Counter(), [], set()
    for (iid, doi), books in by_review.items():
        report['reviews'] += 1
        anchor = f'doi:{doi}'
        live_books = []
        for work, basis, byear, untitled in books:
            w = state.lookup(work)
            if len(w) != 1:
                report['book_key_retired_or_split'] += 1
                continue
            if kind.get(w[0]) == 'thesis':
                report['held_thesis_target'] += 1
                continue
            if w[0] in jstor_piece:
                report['held_jstor_piece_target'] += 1
                continue
            have = state.lookup(anchor)
            if have and (w[0] in have or any(kind.get(h) == 'book' for h in have)):
                report['held_review_doi_on_book'] += 1
                continue
            live_books.append((w[0], basis, byear, untitled))
        if not live_books:
            continue
        if anchor not in state.anchor:
            year, journal = meta.get(iid, (None, None))
            name = signers.get(iid)
            label = 'Review of ' + '; '.join(state.keys[b[0]]['label'][:200] for b in live_books[:3])
            members = [m for m in (f'year:{year}' if year else '', f'journal:{journal}' if journal else '',
                                   f'reviewer-name:{name}' if name else '') if m]
            ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work', label=label[:400], resolution='recorded',
                            anchors=[anchor], aliases=[], members=members,
                            basis=f'JSTOR book review ({journal}, {year}); the book named in its printed heading is keyed '
                                  f'(JSTOR full-text request 7d08e73a)'))
            report['review_works_minted'] += 1
            report['review_works_with_reviewer_name'] += bool(name)
        else:
            report['review_work_exists'] += 1
        for book, basis, byear, untitled in live_books:
            claim = f'jstor-heading-reviews:{doi}:{book}'
            if claim in state.anchor or claim in seen_claims:
                report['claim_exists'] += 1
                continue
            seen_claims.add(claim)
            ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=[claim], relation=dict(subject=anchor, predicate='reviews', object=book),
                            basis=f"the review's printed heading names this book ({'title and author or editor, imprint year ' + str(byear) if basis == 'strong' else 'unique title and imprint year ' + str(byear)})"
                                  + ('; JSTOR gives the review no title' if untitled else '')))
            report['reviews_claims'] += 1
            report['claims_' + basis] += 1
            report['claims_untitled_review'] += bool(untitled)
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(basis='JSTOR review headings: reviewed books, review works on DOI, reviewer names as printed',
                           decided_by='rule', ops=ops), ensure_ascii=False) + '\n'
    if len(body) > 50_000_000:
        with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
    else:
        (args.out / 'proposal.json').write_text(body)
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
