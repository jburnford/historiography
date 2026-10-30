"""Harvest Library of Congress catalogue records for every reviewed book (PID-PLAN.md section 6, step 1).

For each book in the upstream book table (/home/jic823/hnet-reviews/data/books/books.parquet) the LC
catalogue is queried through SRU (MARCXML): by LCCN when the book has one, otherwise (or when the LCCN finds nothing) by ISBN-13. One
line per book goes to OUT/books.ndjson:
- the query and the number of LC records it matched;
- the record's control number, title (245 $a $b), ISBNs (020) and LCCN (010), so a later step can
  check that the record is the same book (an LCCN taken from OpenLibrary can be wrong);
- the personal-name headings (100/700 without $t), each with its $d dates, relator ($e/$4) and any
  authority URI ($0/$1).

Network only; the resolution of headings to LC name authorities and of credits to headings is a later
step (scripts/lc_resolve_authorities.py). Responses are cached on disk, so the run resumes where it
stopped; books already in books.ndjson are skipped.

    python3 scripts/lc_catalogue_harvest.py --cache /mnt/e/lc-authorities/sru --out /mnt/e/lc-authorities
"""
import argparse
import json
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_routes import isbn13  # noqa: E402
from lc_authority_pilot import HEADING_CODES, MARC, SRU, UPSTREAM, Fetcher, bib_headings, norm_lccn, text  # noqa: E402


def record_facts(xml):
    """Control number, title, ISBNs and LCCN of the first record; relators and $d for each heading."""
    root = ET.fromstring(xml)
    rec = root.find(f'.//{MARC}record')
    if rec is None:
        return {}
    out = dict(control='', title='', isbns=[], lccn='', heading_extra=[])
    for cf in rec.findall(f'{MARC}controlfield'):
        if cf.get('tag') == '001':
            out['control'] = text(cf).strip()
    for df in rec.findall(f'{MARC}datafield'):
        tag = df.get('tag')
        subs = [(sf.get('code'), text(sf)) for sf in df.findall(f'{MARC}subfield')]
        if tag == '245':
            out['title'] = ' '.join(v for c, v in subs if c in 'ab').strip(' /:;,.')
        elif tag == '020':
            out['isbns'] += [i for c, v in subs if c == 'a' and (i := isbn13(v.split(' ')[0]))]
        elif tag == '010':
            out['lccn'] = norm_lccn(next((v for c, v in subs if c == 'a'), '')) or ''
        # Must keep exactly the fields bib_headings keeps: main() pairs the two lists by position.
        elif (tag in ('100', '700') and df.get('ind1') != '3' and not any(c == 't' for c, _ in subs)
              and any(c in HEADING_CODES for c, _ in subs)):
            out['heading_extra'].append(dict(
                dates=' '.join(v for c, v in subs if c == 'd').strip(' ,.'),
                relators=[v.strip(' ,.') for c, v in subs if c in 'e4']))
    out['isbns'] = list(dict.fromkeys(out['isbns']))
    return out


class Unanswered(Exception):
    """LC did not answer usably (connection refused or closed after all retries, or an unparseable
    response): the book is not recorded."""


def search(fetch, row, query):
    r = fetch.get(SRU + urllib.parse.quote(query))
    if r['status'] == 0:
        raise Unanswered(query)
    row['http'] = r['status']
    try:
        heads, row['lc_records'] = bib_headings(r['body'])
        return heads, (record_facts(r['body']) if row['lc_records'] > 0 else {})
    except ET.ParseError:           # not recorded, so a re-run retries it
        raise Unanswered(query) from None


def books():
    db = duckdb.connect()
    return db.execute(f"""SELECT book_id, lccn, isbn13, book_title FROM read_parquet('{UPSTREAM / 'books.parquet'}')
                          ORDER BY (coalesce(lccn, '') = ''), book_id""").fetchall()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--delay', type=float, default=1.0, help='seconds between requests')
    ap.add_argument('--pause', type=float, default=300, help='seconds to stand back after repeated refusals')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--lccns', type=Path, help='only books with these LCCNs (whitespace-separated file)')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    fetch = Fetcher(args.cache, args.delay)
    path = args.out / 'books.ndjson'
    done = set()
    if path.exists():
        with path.open(encoding='utf-8') as f:
            for line in f:
                try:
                    done.add(json.loads(line)['book_id'])
                except json.JSONDecodeError:    # a line cut off when a run was stopped
                    continue
    todo = [b for b in books() if b[0] not in done]
    if args.lccns:
        wanted = set(args.lccns.read_text().split())
        todo = [b for b in todo if norm_lccn(b[1]) in wanted]
    if args.limit:
        todo = todo[:args.limit]
    print(f'{len(done)} books done, {len(todo)} to go', flush=True)
    unanswered = streak = 0
    with path.open('a', encoding='utf-8') as f:
        for k, (book_id, lccn, isbn, title) in enumerate(todo, 1):
            l, i = norm_lccn(lccn), isbn13(isbn)
            query = f'bath.lccn={l}' if l else f'bath.isbn={i}' if i else ''
            row = dict(book_id=book_id, title=title, lccn=l or '', isbn13=i or '', query=query)
            try:
                if query:
                    heads, facts = search(fetch, row, query)
                    if row['lc_records'] == 0 and l and i:     # the LCCN may be wrong; try the ISBN
                        row['query'] = f'bath.isbn={i}'
                        heads, facts = search(fetch, row, row['query'])
                    for h, extra in zip(heads, facts.pop('heading_extra', [])):
                        h.update(extra)
                    row.update(record=facts, headings=heads)
            except Unanswered:
                unanswered += 1
                streak += 1
                if streak >= 3:            # LC is blocking us: stand back before going on
                    print(f'{streak} unanswered in a row; pausing {args.pause:.0f}s', flush=True)
                    time.sleep(args.pause)
                continue
            streak = 0
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
            f.flush()
            if k % 250 == 0:
                print(f'{k}/{len(todo)} books, {fetch.requests} requests, {unanswered} unanswered', flush=True)
    print(f'done: {len(done) + len(todo) - unanswered} books recorded, {unanswered} unanswered (re-run to retry), '
          f'{fetch.requests} requests', flush=True)


if __name__ == '__main__':
    main()
