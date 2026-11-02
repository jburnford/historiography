"""Dissertations -> the books they were published as (2026-11-02). Writes a proposal.

A person key may author a dissertation work (an AHA record, `aha-diss:`, or a harvested thesis,
`diss-thesis:`) and LC book works (key_lc_works.py). The thesis was published as one of those books when,
by key_aha's own_book rule on the same person's works:
- the thesis's main title and the book's whole title (subtitle included: Michael Childs, *Labour's
  Apprentices: Working-Class Lads in Late Victorian and Edwardian England*) share at least three content words,
  at least 60% of the shorter; or the thesis's main title has two content words and is the book's main title,
  word for word, published within fifteen years (Erika Dyck, *Psychedelic Psychiatry*);
- the book appeared no earlier than the year before the doctorate;
- one book only (several matching books are listed in review-queue.json; a revised edition is one work).
One `published_as` claim per pair (work -> work), anchored `pub-as:<thesis anchor>:<lccn>`, `recorded`.

    python3 scripts/key_published_as.py --out data/identifiers/published-as-2026-11-02
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_aha import AHA
from lc_canon_people import STOP, content, main_title, words

THESES = ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'


def matches(thesis_title, thesis_year, book_title, book_year):
    d = set(content(thesis_title or ''))
    if book_year is not None and thesis_year is not None and book_year < thesis_year - 1:
        return False
    if len(d) >= 3:
        c = {w for w in words(book_title) if w not in STOP}
        shared = len(c & d)
        return shared >= 3 and shared >= 0.6 * min(len(c), len(d))
    if len(d) == 2:
        within = book_year is None or thesis_year is None or book_year <= thesis_year + 15
        return within and content(thesis_title) == content(main_title(book_title.replace(' : ', ': ')))
    return False


def year_of(v):
    return int(v[:4]) if (v or '')[:4].isdigit() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        aha = {r['id']: (r['title'], year_of(r['year'])) for r in csv.DictReader(f)}
    with THESES.open(newline='', encoding='utf-8') as f:
        theses = {r['id']: (r['title'], year_of(r['year'])) for r in csv.DictReader(f)}
    theses_of, books_of = defaultdict(set), defaultdict(set)
    for _, subj, pred, obj in state.relations('authored'):
        if len(obj) != 1:
            continue
        anchors = state.keys[obj[0]]['anchors']
        kind = 'book' if any(a.startswith('lccn:') for a in anchors) else \
            'thesis' if any(a.startswith(('aha-diss:', 'diss-thesis:')) for a in anchors) else None
        for p in subj:
            if kind == 'book':
                books_of[p].add(obj[0])
            elif kind == 'thesis':
                theses_of[p].add(obj[0])
    report, ops, queue = Counter(), [], []
    for p in sorted(set(theses_of) & set(books_of), key=lambda k: int(k[2:])):
        for t in sorted(theses_of[p]):
            anchors = sorted(state.keys[t]['anchors'])
            src = next((a for a in anchors if a.startswith('aha-diss:')), None) or next(a for a in anchors if a.startswith('diss-thesis:'))
            title, year = aha.get(src[9:]) if src.startswith('aha-diss:') else theses.get(src[12:], (state.keys[t]['label'], None))
            title = title or state.keys[t]['label']
            hits = []
            for b in books_of[p]:
                first = next((m.split(':', 1)[1] for m in state.members.get(b, ()) if m.startswith('lc-first-year:')), '')
                if matches(title, year, state.keys[b]['label'], year_of(first)):
                    hits.append(b)
            if not hits:
                continue
            if len(hits) > 1:
                queue.append(dict(kind='thesis_matches_several_books', person=p, thesis=t, title=title,
                                  books={b: state.keys[b]['label'] for b in hits}))
                report['several_books'] += 1
                continue
            b = hits[0]
            lccn = min(a for a in state.keys[b]['anchors'] if a.startswith('lccn:'))
            anchor = f'pub-as:{src}:{lccn[5:]}'
            if anchor in state.anchor:
                report['already_keyed'] += 1
                continue
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded', anchors=[anchor],
                            relation=dict(subject=src, predicate='published_as', object=lccn)))
            report['minted'] += 1
    materialise(state, dict(basis='published as', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="dissertations published as books: the same person's thesis and LC book by key_aha's own_book rule",
        decided_by='build', ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    summary = dict(people_with_both=len(set(theses_of) & set(books_of)), **dict(sorted(report.items())))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
