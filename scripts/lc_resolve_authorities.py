"""Resolve reviewed-book credits to LC name authorities, with life dates (PID-PLAN.md section 6, step 2).

Inputs:
- the catalogue harvest (scripts/lc_catalogue_harvest.py): books.ndjson, one LC record per book;
- the personal-name index (scripts/lc_names_index.py): personal-names.parquet from the MADS/RDF dump;
- registry v12 (read-only): the H-Net and Reviews in History book credits, their individuals, and the
  LCNAF those individuals reach through Wikidata (QID -> P244), for the precision check.

Steps:
1. **Same book.** The LC record is used only if it is the same book: its LCCN or one of its ISBNs equals
   the book's. A record found by ISBN must carry that ISBN.
2. **Heading -> authority.** A heading's $0/$1 URI, else an exact match of the normalised heading to one
   authorised heading in the index (a heading with an open date, 'X, 1924-', also reaches the one
   authority whose heading has since been closed, 'X, 1924-2023'), else to exactly one variant (400) form. A $0 is used only if the
   index holds it as a live personal name; otherwise the heading is matched. A heading that matches only
   deprecated records stays unresolved: the dump records no successor for them. Headings created after
   the dump stay unresolved (the label service can pick them up
   later).
3. **Credit -> heading**, only inside the credit's own book and through the registry's name gate
   (identity_routes.compatible), as in the pilot. Two compatible headings leave the credit unresolved.
4. **Life dates** for each authority: the RWO's birth/death dates (MARC 046, EDTF) where present, else
   the dates in the heading ($d). The source and precision of each date are kept.

Outputs in OUT: credits.csv (one row per credit), authorities.csv (one row per authority reached),
summary.json.

    python3 scripts/lc_resolve_authorities.py --harvest /mnt/e/lc-authorities/books.ndjson \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/field-research/lc-authorities-2026-10-30
"""
import argparse
import csv
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_routes import compatible, isbn13  # noqa: E402
from lc_authority_pilot import BOOK_ROLES, HNET, REGISTRY, UPSTREAM  # noqa: E402

YEAR = r'(\d{3,4})'


def norm(h):
    h = unicodedata.normalize('NFC', h or '').replace('’', "'")
    h = re.sub(r'\s+', ' ', h).strip(' ,')
    h = re.sub(r'\s*,\s*', ', ', h)
    return h[:-1] if h.endswith('.') and not re.search(r'(\b\w|-)\.$', h) else h


def heading_dates(d):
    """(birth, death, precision) from a heading's $d: '1931-1999', '1967-', 'b. 1932', 'd. 1890',
    '1880 or 1881-1950', 'approximately 1940-'. Centuries, 'active' and 'flourished' dates are not
    life dates and are skipped."""
    d = (d or '').strip(' ,.')
    if not d or re.search(r'active|flourished|fl\.|century|cent\.', d, re.I):
        return '', '', ''
    approx = bool(re.search(r'approximately|ca\.|\?|or ', d, re.I))
    m = re.match(rf'^(?:b\.|born)\s*{YEAR}', d)
    if m:
        return m.group(1), '', 'approximate' if approx else 'year'
    m = re.match(rf'^(?:d\.|died)\s*{YEAR}', d)
    if m:
        return '', m.group(1), 'approximate' if approx else 'year'
    m = re.match(rf'^-\s*{YEAR}', d)
    if m:
        return '', m.group(1), 'approximate' if approx else 'year'
    m = re.match(rf'^(?:approximately\s*)?{YEAR}[^-]*?-\s*(?:approximately\s*)?(?:{YEAR})?', d)
    if m:
        return m.group(1), m.group(2) or '', 'approximate' if approx else 'year'
    return '', '', ''


def label_dates(label):
    """The $d part of an authorised heading: 'Veldkamp, Ferdinand D., 1931-1999' -> '1931-1999'."""
    m = re.search(r',\s*((?:b\.|d\.|born|died|approximately|active|flourished|fl\.)?\s*-?\d{3,4}[^,]*)$', label or '')
    return m.group(1) if m else ''


def edtf_year(v):
    m = re.match(r'^-?(\d{4})', v or '')
    return m.group(1) if m and 'X' not in v[:4] else ''


def load_names(path, lcids=None):
    """The LC personal-name index as dicts. The full index takes about 6 GB of memory; pass `lcids` to load
    only those records, and never run two full loads at once (two crashed WSL on 2026-10-30)."""
    db = duckdb.connect()
    where = ''
    if lcids is not None:
        db.execute('CREATE TABLE want(lcid VARCHAR)')
        db.executemany('INSERT INTO want VALUES (?)', [(x,) for x in lcids])
        where = 'WHERE lcid IN (SELECT lcid FROM want)'
    rows = db.execute(f"""SELECT lcid, label, variants, birth, death, undifferentiated, deprecated, use_instead,
                                 external, sources FROM read_parquet('{path}') {where}""").fetchall()
    by_id, by_label, by_variant, by_open = {}, defaultdict(set), defaultdict(set), defaultdict(set)
    for lcid, label, variants, birth, death, undiff, dep, use, ext, src in rows:
        by_id[lcid] = dict(label=label, birth=birth, death=death, undifferentiated=undiff, deprecated=dep,
                           external=ext, sources=src or [])
        by_label[norm(label)].add(lcid)
        open_form = re.sub(r'(\d{4})-\d{4}$', r'\1-', norm(label))
        if open_form != norm(label):                 # 'X, 1924-2023' is also reached from 'X, 1924-'
            by_open[open_form].add(lcid)
        for v in variants:
            by_variant[norm(v)].add(lcid)
    return by_id, by_label, by_variant, by_open


def resolve(h, names):
    by_id, by_label, by_variant, by_open = names
    uri_id = h['uri'].rstrip('/').split('/')[-1] if h.get('uri') else ''
    if uri_id in by_id and not by_id[uri_id]['deprecated']:
        lcid, via = uri_id, 'bib_$0'
    else:                           # no $0, or one the dump does not hold as a live personal name
        key = norm(h['heading'])
        live = {i for i in by_label.get(key, ()) if not by_id[i]['deprecated']}
        dep = by_label.get(key, set()) - live
        if len(live) == 1:
            lcid, via = next(iter(live)), 'heading'
        elif not live and len(open_live := {i for i in by_open.get(key, ()) if not by_id[i]['deprecated']}) == 1:
            lcid, via = next(iter(open_live)), 'heading_since_closed'   # the person has died since cataloguing
        elif not live and dep:      # the dump gives no successor for deprecated records; never anchor on one
            return '', 'deprecated_heading'
        elif not live and len(by_variant.get(key, ())) == 1:
            lcid, via = next(iter(by_variant[key])), 'variant'
        else:
            return '', 'ambiguous_heading' if len(live) > 1 else 'not_in_dump'
    return lcid, via


def credits_by_book():
    """Registry book credits (H-Net, RiH) with the upstream book_ids they review."""
    db = duckdb.connect()
    db.execute(f"ATTACH '{REGISTRY}' AS r (READ_ONLY)")
    isbn_books = defaultdict(set)
    for book_id, isbn in db.execute(f"SELECT book_id, isbn13 FROM read_parquet('{UPSTREAM / 'books.parquet'}')").fetchall():
        if (i := isbn13(isbn)):
            isbn_books[i].add(book_id)
    con = sqlite3.connect(f'file:{HNET}?mode=ro', uri=True)
    item_books = {iid: {b for x in json.loads(js or '[]') if (i := isbn13(x)) for b in isbn_books.get(i, ())}
                  for iid, js in con.execute('SELECT id, isbns FROM items')}
    rih = defaultdict(set)
    for rid, bid in db.execute(f"""SELECT review_id, book_id FROM read_parquet('{UPSTREAM / 'review_book.parquet'}')
                                   WHERE source = 'reviews_in_history'""").fetchall():
        rih[str(rid)].add(bid)
    lcnaf, qids = defaultdict(set), defaultdict(set)
    for ind, v in db.execute("""SELECT DISTINCT i.individual_id, a.value FROM r.individuals i
                                JOIN r.authority_ids a ON a.qid = substr(i.node, 4)
                                WHERE i.node LIKE 'wd:%' AND a.scheme = 'lcnaf'""").fetchall():
        lcnaf[ind].add(v)
    for ind, node in db.execute("SELECT individual_id, node FROM r.individuals WHERE node LIKE 'wd:%'").fetchall():
        qids[ind].add(node[3:])
    out = []
    for oid, corpus, rec, item, name, ind in db.execute(f"""
            SELECT o.occurrence_id, o.corpus, o.record_id, o.item_id, o.name, x.individual_id
            FROM r.occurrences o LEFT JOIN r.occurrence_resolution x USING (occurrence_id)
            WHERE o.corpus IN ('hnet', 'rih') AND o.role IN {BOOK_ROLES}""").fetchall():
        books = item_books.get(item, set()) if corpus == 'hnet' else rih.get(rec.split(':')[2], set())
        for b in sorted(books):
            out.append(dict(occurrence_id=oid, book_id=b, name=name, individual_id=ind or '',
                            registry_lcnaf=sorted(lcnaf.get(ind, ())), registry_qids=sorted(qids.get(ind, ()))))
    return out


def same_book(row):
    rec = row.get('record') or {}
    if not rec:
        return False
    if row['query'].startswith('bath.lccn='):
        return rec.get('lccn') == row['lccn'] or (row['isbn13'] and row['isbn13'] in rec.get('isbns', []))
    return row['isbn13'] in rec.get('isbns', [])


def life(a, heading_d):
    """Birth/death years with source and precision: 046 (EDTF) first, then the heading's $d."""
    out = {}
    hb, hd, hp = heading_dates(heading_d)
    for part, edtf, hy in (('birth', a['birth'], hb), ('death', a['death'], hd)):
        y = edtf_year(edtf)
        if y:
            if re.search(r'[?~%/]', edtf):          # uncertain, approximate or an interval
                prec = 'approximate'
            else:
                prec = {10: 'day', 7: 'month'}.get(len(edtf.lstrip('-')), 'year')
            out[part] = (y, edtf, '046', prec)
        elif hy:
            out[part] = (hy, hy, 'heading', hp)
        else:
            out[part] = ('', '', '', '')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--harvest', type=Path, required=True)
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    names = load_names(args.names)
    by_id = names[0]
    print(f'{len(by_id):,} personal-name authorities indexed', flush=True)
    harvest = {}
    with args.harvest.open(encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            harvest[r['book_id']] = r
    credits = credits_by_book()
    print(f'{len(harvest):,} books harvested; {len(credits):,} credit-book pairs', flush=True)

    heads_by_book, book_stats = {}, Counter()
    for b, r in harvest.items():
        if r.get('lc_records', 0) <= 0:
            book_stats['no_lc_record'] += 1
            continue
        if not same_book(r):
            book_stats['lc_record_not_same_book'] += 1
            continue
        book_stats['same_book'] += 1
        for h in r['headings']:
            h['lcid'], h['via'] = resolve(h, names)
        heads_by_book[b] = r['headings']

    rows, reached = [], defaultdict(lambda: dict(credits=0))
    for c in credits:
        r = harvest.get(c['book_id'])
        heads = heads_by_book.get(c['book_id'])
        reg = c['registry_lcnaf']
        match = [h for h in heads or [] if compatible(c['name'], h['given'], h['family'])
                 or (h['fuller'] and compatible(c['name'], h['fuller'], h['family']))]
        h = match[0] if len(match) == 1 else None
        lcid = h['lcid'] if h else ''
        a = by_id.get(lcid, {})
        if r is None:
            outcome = 'book_not_harvested'
        elif heads is None:
            outcome = 'no_lc_record' if r.get('lc_records', 0) <= 0 else 'lc_record_not_same_book'
        elif not heads:
            outcome = 'no_personal_heading'
        elif len(match) > 1:
            outcome = 'ambiguous_heading'
        elif not h:
            outcome = 'credit_not_in_record'
        elif not lcid:
            outcome = 'heading_' + h['via']
        elif a.get('undifferentiated'):
            outcome = 'undifferentiated'
        elif reg and lcid in reg:
            outcome = 'agrees_with_registry'
        elif reg:
            outcome = 'conflicts_with_registry'
        elif c['registry_qids']:
            outcome = 'qid_lacks_lcnaf'
        elif c['individual_id']:
            outcome = 'new_for_known_individual'
        else:
            outcome = 'new_for_unresolved_credit'
        if lcid and a and not a.get('undifferentiated'):
            reached[lcid]['credits'] += 1
        rows.append(dict(occurrence_id=c['occurrence_id'], book_id=c['book_id'], credit_name=c['name'],
                         individual_id=c['individual_id'], registry_qids=' '.join(c['registry_qids']),
                         registry_lcnaf=' '.join(reg), heading=h['heading'] if h else '', lcnaf=lcid,
                         via=h['via'] if h else '', outcome=outcome))

    auth_rows, date_stats = [], Counter()
    for lcid, v in sorted(reached.items()):
        a = by_id.get(lcid)
        if not a:
            continue
        lf = life(a, label_dates(a['label']))
        date_stats['birth_' + (lf['birth'][2] or 'none')] += 1
        date_stats['death_' + (lf['death'][2] or 'none')] += 1
        ext = [e for e in a['external'] if 'viaf.org/en/viaf/LC' not in e]
        auth_rows.append(dict(lcnaf=lcid, label=a['label'], credits=v['credits'],
                              birth_year=lf['birth'][0], birth_value=lf['birth'][1], birth_source=lf['birth'][2],
                              birth_precision=lf['birth'][3], death_year=lf['death'][0], death_value=lf['death'][1],
                              death_source=lf['death'][2], death_precision=lf['death'][3],
                              external=' '.join(ext), first_source=(a['sources'] or [''])[0]))

    for name, data in (('credits.csv', rows), ('authorities.csv', auth_rows)):
        with open(args.out / name, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]) if data else [])
            w.writeheader()
            w.writerows(data)
    distinct = {}
    for r in rows:
        distinct[r['occurrence_id'], r['book_id']] = r['outcome']
    summary = dict(authorities_indexed=len(by_id), books_harvested=len(harvest), books=dict(book_stats),
                   credit_book_pairs=len(rows), outcomes=dict(Counter(distinct.values()).most_common()),
                   individuals_reached=len({r['individual_id'] for r in rows if r['lcnaf'] and r['individual_id']}),
                   authorities_reached=len(auth_rows), dates=dict(sorted(date_stats.items())),
                   heading_resolution=dict(Counter(h['via'] for hs in heads_by_book.values() for h in hs).most_common()))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
