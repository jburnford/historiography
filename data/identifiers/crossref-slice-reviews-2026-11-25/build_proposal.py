"""Matched Crossref-slice reviews -> tables, held list and key-log proposals (2026-11-25). Nothing is applied.

Reads, in WORK (the spark outputs and the graph exports): candidates.parquet (one row per record segment and book,
with the spark rule's reason when refused or held), records.parquet (the records' metadata and authors),
books.parquet, graph-dois.parquet, graph-reviews.parquet. Writes to the folder of this script:

- candidates.csv.gz    every pair the title rule found that a date or author rule did not refuse as not-a-review
- matches.csv.gz       the links proposed (one row per review record and book), with stratum and book category
- held.csv.gz          pairs held, with the reason
- 01-reviews-of-keyed-books.proposal.json.gz   review works + `reviews` claims (+ ORCID `authored` claims) for keyed books
- 02-reviews-of-unkeyed-books.proposal.json.gz the unkeyed book nodes minted as works (their own DOI / LCCN /
  OpenAlex anchors), then the same ops for their reviews. Separate because minting the book is a decision of its own.
- report.json

Design as scripts/key_crossref_reviews.py: no reviewer person keys by name; a reviewer is tied to a key only by an
ORCID on the Crossref record that the key log holds. Review works carry `reviewer-name:` members as printed.

    python3 build_proposal.py WORK
"""
import gzip
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
import keylog_snapshot as KS  # noqa: E402

WORK = Path(sys.argv[1])
SKIP_REASONS = {'record author shares a family name with the book', 'dated more than eight years after the book',
                'dated before the book', 'book has no known author'}      # refused (not counted as held)
BOOK_ANCHOR = ('doi', 'lccn', 'openalex', 'hnet-book', 'isbn')


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def journal_fold(s):
    return ' '.join(w for w in re.sub(r'[^a-z0-9]+', ' ', fold(s)).split() if w not in ('the', 'of', 'and'))


def words(s):
    return set(re.sub(r'[^a-z0-9]+', ' ', fold(s)).split())


def writecsv(path, rows, cols):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def main():
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=4")
    cand = db.execute(f"SELECT * FROM '{WORK}/candidates.parquet'").fetchdf().to_dict('records')
    recs = {r['doi']: r for r in db.execute(f"SELECT * FROM '{WORK}/records.parquet'").fetchdf().to_dict('records')}
    books = {r['key']: r for r in db.execute(f"""SELECT key, label, year, resolution, anchors, families FROM '{WORK}/books.parquet'
                     WHERE key IN (SELECT DISTINCT book FROM '{WORK}/candidates.parquet')""").fetchdf().to_dict('records')}
    gdoi = {r['anchor'][4:].lower(): r for r in db.execute(f"""SELECT * FROM '{WORK}/graph-dois.parquet'
                     WHERE lower(substr(anchor, 5)) IN (SELECT lower(doi) FROM '{WORK}/records.parquet')""").fetchdf().to_dict('records')}
    # existing reviews of the candidate books: book -> {(journal, year): [(review key, resolution, anchors)]}
    known = defaultdict(lambda: defaultdict(list))
    for r in db.execute(f"""SELECT * FROM '{WORK}/graph-reviews.parquet'
                     WHERE book IN (SELECT DISTINCT book FROM '{WORK}/candidates.parquet')""").fetchdf().to_dict('records'):
        if r['journal'] and r['year']:
            known[r['book']][journal_fold(r['journal']), int(r['year'])].append(r)
    nseg = Counter()
    for c in cand:
        nseg[c['doi']] = max(nseg[c['doi']], c['seg'] + 1)
    report = Counter()

    def cat(b):
        bk = books[b]
        schemes = {a.split(':', 1)[0] for a in bk['anchors']}
        k = 'keyed' if bk['resolution'] != 'unkeyed' else 'unkeyed'
        s = 'doi' if 'doi' in schemes and 'lccn' not in schemes else ('lccn' if 'lccn' in schemes and 'doi' not in schemes
                                                                       else ('doi+lccn' if 'doi' in schemes else 'other'))
        return f'{k}-{s}'

    rows_all, held, ok = [], [], []
    for c in cand:
        r = recs.get(c['doi'])
        if r is None:
            continue
        people = [p for p in (r['people'] if r['people'] is not None else []) if p['family'] or p['name']]
        row = dict(c, book_category=cat(c['book']), book_label=books[c['book']]['label'], review_title=r['title'],
                   review_subtitle=r['subtitle'], journal=r['container'], issn=r['issn'], review_year=r['year'],
                   page=r['page'], publisher=r['publisher'],
                   reviewers='; '.join(f"{p['given'] or ''} {p['family'] or p['name'] or ''}".strip() for p in people),
                   orcids='; '.join((p['orcid'] or '').rstrip('/').split('/')[-1] for p in people if p['orcid']))
        if c['reason'] in SKIP_REASONS:
            report[f"refused: {c['reason']}"] += 1
            continue
        rows_all.append(row)
        if not c['reason'] and c['fam_in_title']:
            # audit 2026-11-25 ('Frank Lloyd Wright' 1984 taken for a review of Pfeiffer's Treasures of Taliesin): a family
            # name counts only outside the book's own title words
            bk = books[c['book']]
            fams = [f for f in (bk['families'] if bk['families'] is not None else []) if f]
            tw = words(re.sub(r'<[^>]+>', ' ', r['title'] or '') + ' ' + (r['subtitle'] or ''))
            btw = words(re.split(r'\s*[:;/]\s*', bk['label'])[0])
            hit = [f for f in fams if all(x in tw for x in f.split())]
            if hit and all(all(x in btw for x in f.split()) for f in hit):
                c['fam_in_title'] = row['fam_in_title'] = False
                if c['title_words'] <= 2 or c['shared'] > 1:
                    c['reason'] = row['reason'] = 'short or shared title; the author name is only the title itself'
        if not c['reason'] and not c['fam_in_title']:
            # audit narrowing (2026-11-25): without the author's name in the title, a record of over eight pages is
            # often an article of the book's title; a bare main title of three words or fewer may be another book
            span = re.fullmatch(r'\s*(\d+)\s*[-–]\s*(\d+)\s*', r['page'] or '')
            if c['stratum'] == 'bare' and span and int(span.group(2)) - int(span.group(1)) > 8:
                c['reason'] = row['reason'] = 'bare title without the author name on a record of over eight pages'
            elif c['eq'] == 'main' and c['title_words'] <= 3:
                c['reason'] = row['reason'] = 'title of three words or fewer without the author name'
        if c['reason']:
            held.append(row)
        else:
            ok.append(row)
    # one book per record segment: several books left -> prefer one whose people are printed in the title; then a
    # keyed node over unkeyed duplicates of the same title; else hold
    byseg = defaultdict(list)
    for row in ok:
        byseg[row['doi'], row['seg']].append(row)
    chosen = []
    for (doi, seg), rs in byseg.items():
        if len(rs) > 1:
            fam = [x for x in rs if x['fam_in_title']]
            rs = fam if fam else rs
        if len(rs) > 1:
            keyed = [x for x in rs if not x['book_category'].startswith('unkeyed')]
            if len(keyed) == 1:
                for x in rs:
                    if x is not keyed[0]:
                        report['unkeyed twin of the chosen keyed book (not linked)'] += 1
                rs = keyed
        if len(rs) > 1:
            for x in rs:
                held.append(dict(x, reason='two or more graph books fit'))
            continue
        chosen.append(rs[0])
    # graph checks and Crossref duplicates
    final, seen_rev = [], {}
    for row in chosen:
        doi, b = row['doi'].lower(), row['book']
        g = gdoi.get(doi)
        row['review_in_graph'] = (g['key'] if g else '')
        row['review_graph_kind'] = (g['kind'] if g else '')
        if g is not None and g['reviews'] is not None and b in list(g['reviews']):
            report['already linked in the graph'] += 1
            continue
        if g is not None and g['reviews'] is not None and len(g['reviews']) and nseg[row['doi']] == 1:
            held.append(dict(row, reason='review already linked to another book'))
            continue
        jy = (journal_fold(row['journal']), int(row['review_year']))
        same = known[b].get(jy, [])
        row['same_journal_year'] = '; '.join(x['review'] for x in same)
        if same:
            jstor = [x for x in same if x['resolution'] != 'unkeyed'
                     and all(a.startswith('doi:10.2307/') for a in x['anchors'] if a.startswith('doi:'))
                     and g is None]
            if len(same) == 1 and jstor:
                row['action'] = 'attach-to-jstor-review'
                row['attach_to'] = jstor[0]['review']
            else:
                held.append(dict(row, reason='a review of the book in the same journal and year is in the graph'))
                continue
        dk = (b, jy, tuple(sorted(fold(n.split()[-1]) for n in row['reviewers'].split('; ') if n)))
        if dk in seen_rev:
            held.append(dict(row, reason='second Crossref record of the same review', attach_to=seen_rev[dk]))
            continue
        seen_rev[dk] = row['doi']
        row.setdefault('action', 'claim-only' if g is not None and g['resolution'] != 'unkeyed' else 'mint-review')
        final.append(row)

    # --- proposals ---
    state = KS.read_state()
    gone = set()
    ops1, ops2, minted_books, minted_reviews = [], [], {}, set()
    for row in final:
        b, doi = row['book'], row['doi'].lower()
        unkeyed = row['book_category'].startswith('unkeyed')
        ops = ops2 if unkeyed else ops1
        obj = b
        if unkeyed:
            bk = books[b]
            anchors = [a for a in bk['anchors'] if a.split(':', 1)[0] in BOOK_ANCHOR]
            if sum(a.startswith('lccn:') for a in anchors) > 1:     # several LC records on one node (two DOIs of one book are common)
                row['held_reason'] = 'unkeyed book node joins several catalogue records'
                held.append(dict(row, reason=row['held_reason']))
                continue
            if not anchors or any(state.lookup(a) for a in anchors):
                row['held_reason'] = 'unkeyed book node has no usable anchor, or one is keyed'
                held.append(dict(row, reason=row['held_reason']))
                continue
            obj = anchors[0]
            if b not in minted_books:
                minted_books[b] = obj
                ops.append(dict(event='mint', key=f'new:b{len(ops)}', type='work', label=bk['label'][:400],
                                resolution='recorded', anchors=anchors, aliases=[],
                                members=['kind:book'] + ([f"year:{int(bk['year'])}"] if bk['year'] else []),
                                basis=f'graph book node {b} (unkeyed) keyed because a Crossref review of it was found '
                                      '(crossref-slice-reviews-2026-11-25)'))
                report['unkeyed books minted'] += 1
        anchor = f'doi:{doi}'
        existing = state.lookup(anchor) or (anchor in minted_reviews)     # a collective review: one work, a claim per book
        names = [n for n in row['reviewers'].split('; ') if n]
        if existing:
            row['action'] = 'claim-only'
        elif row['action'] == 'attach-to-jstor-review':
            minted_reviews.add(anchor)
            ops.append(dict(event='attach', key=row['attach_to'], anchors=[anchor], aliases=[], members=[],
                            basis='the same review (book, journal, year) under its publisher DOI in Crossref'))
        else:
            minted_reviews.add(anchor)
            ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work',
                            label=f"Review of {books[b]['label']}"[:400], resolution='recorded', anchors=[anchor], aliases=[],
                            members=['kind:review', f"year:{int(row['review_year'])}"]
                                    + ([f"journal:{row['journal']}"] if row['journal'] else [])
                                    + [f'reviewer-name:{n}' for n in names],
                            basis=f"Crossref record of a review ({row['journal']}, {int(row['review_year'])}) of the graph book "
                                  f"{b}; crossref-slice-reviews-2026-11-25, rule {row['stratum']}/{row['eq']}"))
        report[f"action {row['action']}"] += 1
        claim = f'crossref-reviews:{doi}' if nseg[row['doi']] == 1 else f'crossref-reviews:{doi}:{row["seg"]}'
        if row['action'] != 'attach-to-jstor-review' and claim not in state.anchor:
            ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=[claim], relation=dict(subject=anchor, predicate='reviews', object=obj),
                            basis="Crossref files this review under the book's title; the book's people are not among its "
                                  f"authors (crossref-slice-reviews-2026-11-25, {row['stratum']}/{row['eq']})"))
        for o in [x for x in row['orcids'].split('; ') if x]:
            c = f'crossref-orcid:{doi}:{o}'
            if f'orcid:{o}' in state.anchor and c not in state.anchor:
                ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[c], relation=dict(subject=f'orcid:{o}', predicate='authored', object=anchor),
                                basis="Crossref lists this ORCID as the review's author"))
                report['reviewer authored claims by ORCID'] += 1
    final = [r for r in final if 'held_reason' not in r]
    for name, ops, basis in (
            ('01-reviews-of-keyed-books', ops1, 'Crossref history slice (March 2026 data file): reviews of keyed graph books by '
             'the rules of key_crossref_reviews.py run over every record; reviewers by ORCID only. NOT APPLIED.'),
            ('02-reviews-of-unkeyed-books', ops2, 'Crossref history slice: reviews of unkeyed graph book nodes; each book is '
             'minted as a work under its own identifiers first (a key-log relation needs a keyed endpoint). NOT APPLIED.')):
        with gzip.open(HERE / f'{name}.proposal.json.gz', 'wt', encoding='utf-8') as fh:
            json.dump(dict(basis=basis, decided_by='rule', ops=ops), fh, ensure_ascii=False)
        report[f'{name} ops'] = len(ops)
    cols = ['doi', 'seg', 'book', 'book_category', 'book_label', 'book_year', 'review_title', 'review_subtitle', 'journal',
            'issn', 'review_year', 'page', 'reviewers', 'orcids', 'stratum', 'eq', 'how', 'printed_names', 'title_words',
            'shared', 'fam_in_title', 'fam_in_names', 'review_in_graph', 'review_graph_kind', 'same_journal_year',
            'action', 'attach_to', 'reason']
    slim = ['doi', 'seg', 'book', 'book_category', 'review_year', 'stratum', 'eq', 'how', 'title_words', 'shared',
            'fam_in_title', 'fam_in_names', 'reason']
    short = [dict(x, review_title=' '.join((x['review_title'] or '').split())[:150], book_label=(x['book_label'] or '')[:120])
             for x in held]
    writecsv(HERE / 'candidates.csv.gz', rows_all, slim)            # every pair past the refusals; titles in the two below
    writecsv(HERE / 'matches.csv.gz', final, cols)
    writecsv(HERE / 'held.csv.gz', short, ['doi', 'seg', 'book', 'book_category', 'book_label', 'book_year', 'review_title',
                                           'journal', 'review_year', 'reviewers', 'stratum', 'eq', 'reason', 'attach_to'])
    report['matches'] = len(final)
    report['held'] = len(held)
    for x in held:
        report[f"held: {x['reason']}"] += 1
    for x in final:
        report[f"stratum {x['stratum']}"] += 1
        report[f"book {x['book_category']}"] += 1
    (HERE / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items())), indent=1))


if __name__ == '__main__':
    main()
