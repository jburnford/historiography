"""JSTOR book reviews of keyed books -> review works and `reviews` claims, reviewer names as printed (2026-11-05).

User, 2026-11-05: his book had six reviews; the graph linked one ("you'd need to find them in crossref or jstor").
The JSTOR metadata export marks book reviews (content_subtype `book-review`; /mnt/e/jstor-book-reviews.parquet,
3.33M rows, all disciplines; creators mix the reviewer and the book's authors). Design reviewed by Fable
(data/identifiers/reviews-route-design-review-2026-11-05.md): mint every matched review as a work and a `reviews`
claim; keep reviewer names as printed (members `reviewer-name:`); mint NO reviewer keys (a name-only key pools every
bearer of the name: two of JSTOR's six "Jim Clifford" reviews are another Jim Clifford's); attach reviewers to
people later only on a non-name fact (ORCID on the review's Crossref record, the same review keyed from H-Net).

A review matches a keyed book (an LC book with a keyed author) when
- its main title (a leading 'Book Review :' and trailing creator family names removed; key_lc_works.title_key before
  the first colon) equals the book's, two words or more, not a section heading ('Book Reviews', 'New Books', ...);
- a family name of the book's keyed author is among the review's creators;
- the review is dated from the book's year minus one to eight years after (twenty for titles over three words);
- exactly one keyed book fits (otherwise none: 184 at the probe).
Reviewer names are the creators whose family name is not on the book (its keyed authors and every 100/700 heading
of its LC records), without empty or initials-only names; when more than two remain, or the title joins several
titles, the review is `collective` and no reviewer is recorded.

    python3 scripts/key_jstor_reviews.py --out data/identifiers/jstor-reviews-2026-11-05
"""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import title_key
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

GRAPH = ROOT / 'build/graph'
REVIEWS = Path('/mnt/e/jstor-book-reviews.parquet')
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
GENERIC = {'review', 'reviews', 'book reviews', 'book review', 'new books', 'book notes', 'bulletin', 'notes bibliographiques',
           'books received', 'short notices', 'brief notices', 'other books', 'recent books'}


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def family(label):
    return fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1])


def main_title(t):
    return title_key(re.split(r'\s*[:;/]\s*', t or '')[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute("SET memory_limit = '5GB'")
    db.execute("SET temp_directory = '/mnt/e/duckdb-tmp'")
    books = defaultdict(list)                          # main title key -> [(work key, year, author families, label, lccns)]
    for k, label, year, authors, anchors in db.execute(f"""
            SELECT w.key, w.label, w.year, list(DISTINCT p.label), any_value(w.anchors)
            FROM '{GRAPH}/work.parquet' w JOIN {keylog(GRAPH, 'authored')} a ON a."to" = w.key
            JOIN '{GRAPH}/person.parquet' p ON p.key = a."from" WHERE w.kind = 'book' GROUP BY 1, 2, 3""").fetchall():
        t = main_title(label)
        if len(t.split()) >= 2 and t not in GENERIC:
            books[t].append((k, year, {family(a) for a in authors}, label, [a[5:] for a in anchors if a.startswith('lccn:')]))
    report, matched = Counter(), []
    for doi, title, date, first, last, container in db.execute(
            f"SELECT doi, title, date, first, last, container FROM '{REVIEWS}' WHERE title <> '' AND doi <> ''").fetchall():
        t = re.sub(r'^\s*book reviews?\s*:\s*', '', ' '.join(title.split()), flags=re.I)
        fams = {fold(x) for x in last if x}
        tk = main_title(t)
        cands = books.get(tk)
        if not cands:
            words = tk.split()
            while words and words[-1] in fams:
                words.pop()
            tk = ' '.join(words)
            cands = books.get(tk) if len(words) >= 2 else None
        if not cands:
            continue
        y = int(date[:4]) if date[:4].isdigit() else None
        span = 8 if len(tk.split()) <= 3 else 20
        fit = [c for c in cands if c[2] & fams and (not y or not c[1] or c[1] - 1 <= y <= c[1] + span)]
        if len(fit) != 1:
            report['several_books' if fit else 'no_fit'] += 1
            continue
        matched.append((doi, t, y, list(zip(first, last)), container, fit[0]))
    report['matched'] = len(matched)
    # every heading on the matched books' LC records: co-authors, editors and translators are not reviewers
    db.execute('CREATE TABLE lc(c VARCHAR)')
    db.executemany('INSERT INTO lc VALUES (?)', [(c,) for m in matched for c in m[5][4]])
    heads = defaultdict(set)
    for c, fam in db.execute(f"SELECT trim(control), family FROM read_parquet('{LC_INDEX}/headings-*.parquet') "
                             "WHERE trim(control) IN (SELECT DISTINCT c FROM lc)").fetchall():
        heads[c].add(fold(fam).split()[0] if fold(fam).split() else '')
    state = State.load(args.state)
    ops, seen = [], set()
    for doi, t, y, creators, container, (book, byear, afams, blabel, lccns) in matched:
        if doi in seen:
            report['duplicate_doi'] += 1
            continue
        seen.add(doi)
        exclude = afams | {f for c in lccns for f in heads.get(c, ())}
        names = [f'{a} {b}'.strip() for a, b in creators
                 if b and fold(b).split()[:1] and fold(b).split()[0] not in exclude and fold(b) not in exclude
                 and not all(len(x.strip('.')) <= 1 for x in (a or '').split())]
        collective = len(names) > 2 or ';' in t
        if collective:
            names = []
            report['collective'] += 1
        members = [m for m in (f'year:{y}' if y else '', f'journal:{container}' if container else '',
                               'collective-review' if collective else '') if m] + [f'reviewer-name:{n}' for n in names]
        anchor = f'doi:{doi}'
        if anchor not in state.anchor:
            ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work', label=f'Review of {blabel[:300]}'[:400],
                            resolution='recorded', anchors=[anchor], aliases=[], members=members,
                            basis=f'JSTOR book review ({container}, {y}) of the keyed book {book}'))
            report['review_works'] += 1
        else:
            report['review_work_exists'] += 1
        claim = f'jstor-reviews:{doi}'
        if claim in state.anchor:
            report['claim_exists'] += 1
            continue
        ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded', anchors=[claim],
                        relation=dict(subject=anchor, predicate='reviews', object=book),
                        basis='JSTOR files this book review under the book\'s title and author'))
        report['reviews_claims'] += 1
        report['with_reviewer_name'] += bool(names)
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / 'proposal.json', 'w', encoding='utf-8') as f:
        json.dump(dict(basis='JSTOR book reviews of keyed books, reviewer names as printed', decided_by='rule', ops=ops),
                  f, ensure_ascii=False)
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
