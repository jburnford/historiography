"""Crossref reviews of keyed historians' books -> review works, `reviews` claims, ORCID reviewers (2026-11-05).

Reads the cache harvest_crossref_reviews.py wrote (/mnt/e/crossref-reviews/<book key>.json: Crossref journal records
found by the book's title and author). Design as key_jstor_reviews.py (Fable's review,
data/identifiers/reviews-route-design-review-2026-11-05.md): no reviewer keys by name. A record is a review of the
book when
- its title, with HTML tags, a leading 'Book review:' and a leading '<author name>, ' removed, contains the book's
  main title (key_lc_works.title_key, two words or more) at its start, or equals it;
- none of its authors has the family name of one of the book's keyed authors (the author does not review himself);
- it is dated from the book's year to eight years after, and has one or two authors (more: a review essay or a
  symposium, left out).
The review becomes a work (`doi:`, members `year:`, `journal:`, `reviewer-name:`) unless a key holds the DOI, or a
review of the same book in the same journal and year is already keyed (JSTOR's 10.2307 DOI): then the Crossref DOI
is attached to that work. A `reviews` claim (`crossref-reviews:<doi>`) ties it to the book. A reviewer whose ORCID
(on the Crossref record) a key holds gets an `authored` claim (`crossref-orcid:<doi>:<orcid>`): REVIEWED follows.

    python3 scripts/key_crossref_reviews.py --out data/identifiers/crossref-reviews-2026-11-05
"""
import argparse
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import title_key

GRAPH = ROOT / 'build/graph'
CACHE = Path('/mnt/e/crossref-reviews')


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def family(label):
    return fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1])


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', html.unescape(t or ''))
    t = re.sub(r'^\s*(book reviews?|review|compte rendu)\s*[:.-]\s*', '', ' '.join(t.split()), flags=re.I)
    t = re.sub(r'^[A-Z][^,:]{2,60},\s+(?=[A-Z0-9"\'«])', '', t)          # 'Jim Clifford, West Ham and ...'
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    db = duckdb.connect()
    # reviews already keyed: book -> {(journal, year): review work}
    known = defaultdict(dict)
    for review, book, journal, year in db.execute(f"""SELECT r."from", r."to", w.journal, w.year FROM '{GRAPH}/reviews.parquet' r
            JOIN '{GRAPH}/work.parquet' w ON w.key = r."from" WHERE w.journal IS NOT NULL""").fetchall():
        known[book][fold(journal), year] = review
    state = State.load(args.state)
    keyed_orcid = {a.split(':', 1)[1] for a in state.anchor if a.startswith('orcid:')}
    report, ops, seen = Counter(), [], set()
    for f in sorted(CACHE.glob('*.json')):
        d = json.loads(f.read_text())
        book, byear = d['book'], d['year']
        bt = title_key(re.split(r'\s*[:;/]\s*', d['title'] or '')[0])
        if len(bt.split()) < 2:
            continue
        afams = {family(a) for a in d['authors']}
        for it in d.get('items') or []:
            doi = (it.get('DOI') or '').lower()
            t = clean((it.get('title') or [''])[0])
            tk = title_key(t)
            if not doi or not (tk == bt or tk.startswith(bt + ' ')):
                continue
            authors = it.get('author') or []
            y = ((it.get('issued') or {}).get('date-parts') or [[None]])[0][0]
            if not authors or len(authors) > 2 or any(fold(a.get('family')) in afams for a in authors) \
                    or not y or not byear or not byear <= y <= byear + 8:
                report['not_a_review'] += 1
                continue
            if doi in seen:
                continue
            seen.add(doi)
            journal = ((it.get('container-title') or ['']) or [''])[0]
            names = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors]
            report['reviews'] += 1
            anchor = f'doi:{doi}'
            existing = state.lookup(anchor)
            same = known[book].get((fold(journal), y))
            if existing:
                report['doi_keyed'] += 1
            elif same:
                ops.append(dict(event='attach', key=same, anchors=[anchor], aliases=[], members=[],
                                basis='the same review (book, journal, year) under its publisher DOI in Crossref'))
                report['attached_to_jstor_review'] += 1
            else:
                ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work', label=f"Review of {d['title'][:300]}"[:400],
                                resolution='recorded', anchors=[anchor], aliases=[],
                                members=[f'year:{y}'] + ([f'journal:{journal}'] if journal else [])
                                        + [f'reviewer-name:{n}' for n in names],
                                basis=f'Crossref record of a review ({journal}, {y}) of the keyed book {book}'))
                report['review_works'] += 1
            claim = f'crossref-reviews:{doi}'
            if claim not in state.anchor and not same:
                ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[claim], relation=dict(subject=anchor, predicate='reviews', object=book),
                                basis='Crossref files this review under the book\'s title; the book\'s author is not among its authors'))
            for a in authors:
                o = (a.get('ORCID') or '').rstrip('/').split('/')[-1]
                c = f'crossref-orcid:{doi}:{o}'
                if o in keyed_orcid and c not in state.anchor:
                    ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                                    anchors=[c], relation=dict(subject=f'orcid:{o}', predicate='authored', object=anchor),
                                    basis='Crossref lists this ORCID as the review\'s author'))
                    report['reviewer_by_orcid'] += 1
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / 'proposal.json', 'w', encoding='utf-8') as fh:
        json.dump(dict(basis="Crossref reviews of keyed historians' books; reviewers by ORCID only", decided_by='rule', ops=ops),
                  fh, ensure_ascii=False)
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
