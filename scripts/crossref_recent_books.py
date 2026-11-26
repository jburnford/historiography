"""Loader for the recent-books layer (2026-11-26): Crossref books of 2016-2026 the graph lacked, and the Crossref reviews of
them, both in the linked layer (never the key log). Kept out of scripts/build_graph.py so that file need not change
beyond two calls; build_graph passes in its own structures and its `crossref_slice_reviews` function.

Tables (written by scripts/crossref_recent_books_table.py; round folder data/identifiers/crossref-recent-books-2026-11-26):
- data/graph/crossref-recent-books.csv.gz         one row per book: `doi:` node key, title, subtitle, year, publisher,
  type, ISBNs, printed authors / editors (with ORCIDs where given), the person keys an ORCID sits on, routes, alternates
- data/graph/crossref-recent-book-reviews.csv.gz  review -> book rows, same columns as crossref-slice-reviews.csv.gz

What the loader does
1. Each book: if its DOI or an alternate DOI already resolves to a work node (keyed since, or made by another layer),
   nothing is added and no credit is given (report `<tag>_book_on_existing_node`); else an unkeyed `doi:` work node,
   kind book, with title (+ subtitle), year, ISBNs, the alternates as anchors, editors_printed for edited books.
2. Credits: only on the nodes this layer adds, and only through an ORCID that is the anchor of exactly one person key
   (checked again against the key log here): AUTHORED (role author) or EDITED (role editor), evidence linked, source
   crossref-recent-books:orcid. Names stay as printed; no name-only credit.
3. Reviews: build_graph.crossref_slice_reviews on the reviews table (tag crossref_recent_book_reviews), after the book
   nodes exist; its REVIEWS rows are appended to rb_rows (pairs already there skipped), its reviewer credits (by ORCID
   on a key) to csr_credits, which build_graph already merges into the linked AUTHORED rows.

In scripts/build_graph.py (two lines):
    from crossref_recent_books import recent_books   # with the other imports
    rbk_edited = recent_books(state, types, works, wi, unkeyed, resolve, report, rb_rows, csr_credits, crossref_slice_reviews)
        # right after the `if CROSSREF_SLICE_REVIEWS in p5_files:` block
and after `linked['EDITED'] = list(linked.get('EDITED', []))`:
    linked['EDITED'] += rbk_edited
(the AUTHORED credits travel in csr_credits, which build_graph merges already).
"""
import csv
import gzip
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / 'data/graph/crossref-recent-books.csv.gz'
REVIEWS = ROOT / 'data/graph/crossref-recent-book-reviews.csv.gz'
SOURCE = 'crossref-recent-books:orcid'


def _rows(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as fh:
        yield from csv.DictReader(fh)


def _tracked(paths):
    for p in paths:
        try:
            rel = str(p.relative_to(ROOT))
        except ValueError:          # a test table outside the repository
            continue
        if subprocess.run(['git', 'ls-files', '--error-unmatch', rel], cwd=ROOT, capture_output=True).returncode:
            raise SystemExit(f'inputs not tracked in git: {rel}')


def contributors(cell):
    """'role|name|orcid' joined by '; ' -> [(role, name, orcid)]"""
    out = []
    for part in (cell or '').split('; '):
        if part:
            role, name, orcid = (part.split('|') + ['', ''])[:3]
            out.append((role, name, orcid))
    return out


def recent_books(state, types, works, wi, unkeyed, resolve, report, rb_rows, csr_credits, slice_reviews,
                 books=BOOKS, reviews=REVIEWS, tag='crossref_recent_books'):
    """Add the book nodes and their ORCID credits; load their reviews. Mutates works / wi / unkeyed / types, rb_rows and
    csr_credits in place; returns the EDITED rows (evidence linked) for build_graph to merge."""
    if os.environ.get('BUILD_PASS5_OFF') or not books.exists():
        return []
    _tracked([books] + ([reviews] if reviews.exists() else []))
    added, edited, seen_c = set(), [], set()
    for r in _rows(books):
        report[f'{tag}_rows'] += 1
        key = r['doi']
        alts = [a for a in (r['alternates'] or '').split(';') if a]
        hit = next((n for x in [key] + alts if (n := resolve(x)) and n in wi), None)
        if hit:
            report[f'{tag}_book_on_existing_node'] += 1
            continue
        if key in wi:               # an unkeyed node of that DOI (resolve returns it already; kept for safety)
            report[f'{tag}_book_on_existing_node'] += 1
            continue
        title = r['title'] + (f": {r['subtitle']}" if r['subtitle'] else '')
        people = contributors(r['contributors'])
        eds = [n for role, n, _ in people if role == 'editor']
        w = dict(key=key, label=title or None, resolution='unkeyed', anchors=sorted([key] + alts), kind='book', lccn=None,
                 year=int(r['year']) if (r['year'] or '').isdigit() else None, reviewer_names=[], journal=None,
                 isbn=r['isbns'] or None, editors_printed='; '.join(eds) if eds and r['type'] == 'edited-book' else None)
        works.append(w)
        wi[key] = w
        unkeyed.add(key)
        types[key] = 'work'
        added.add(key)
        report[f'{tag}_nodes_added'] += 1
        for role, _, orcid in people:
            if not orcid:
                continue
            ks = [k for k in state.lookup(f'orcid:{orcid}') if types.get(k) == 'person']
            if len(ks) != 1:
                report[f'{tag}_orcid_not_on_one_person_key'] += 1
                continue
            if (ks[0], key, role) in seen_c:
                continue
            seen_c.add((ks[0], key, role))
            row = {'from': ks[0], 'to': key, 'claim': f'{SOURCE}:{key[4:]}:{orcid}', 'resolution': 'linked',
                   'source': SOURCE, 'state': 'exact', 'role': 'editor' if role == 'editor' else 'author'}
            if role == 'editor':
                edited.append(row)
            else:
                csr_credits.append(row)
            report[f'{tag}_{"EDITED" if role == "editor" else "AUTHORED"}_by_orcid'] += 1
    if reviews.exists():
        have = {(x['from'], x['to']) for x in rb_rows}
        rows, credits = slice_reviews(state, types, works, wi, unkeyed, resolve, report, path=reviews,
                                      tag='crossref_recent_book_reviews')
        report['crossref_recent_book_reviews_pair_already_linked'] = sum(1 for x in rows if (x['from'], x['to']) in have)
        rb_rows += [x for x in rows if (x['from'], x['to']) not in have]
        csr_credits += credits
    return edited
