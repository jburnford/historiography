"""Works cited in the dissertation corpus -> the LC book works in the key log (2026-11-02). Writes a crosswalk.

The citation corpus (data/field-research/dissertation-citations-2026-10-11) names each cited work with a build
key (`W:childs|labours apprentices`), and its citation table links citing theses to those keys
(strict-citations.csv.gz). The key log holds the books LC catalogued under keyed people (key_lc_works.py),
with their authors and editors as `authored` / `edited` relations. A cited book is an LC work when:
- one of its listed authors' family name is the family name of one of the LC work's authors or editors;
- its main title (before the first colon), normalised by key_lc_works.title_key, equals the LC work's main
  title;
- exactly one LC work matches, or, when several do (an original and its translation share a main title),
  exactly one has the citation's whole title, or was first published within two years of the cited year.

The corpus keys are build artefacts that change when the corpus is rebuilt, so the result is a crosswalk file
beside the log, not log events: `crosswalk.csv.gz` (work_id, key, lccn, title), regenerated after each corpus
build. Joined with strict-citations.csv.gz it gives, for every keyed book, the theses that cite it.

    python3 scripts/key_cited_works.py --out data/identifiers/cited-works-2026-11-02
"""
import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State
from key_lc_works import title_key

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
BOOKISH = {'book', 'book_or_serial', 'edited_book', 'thesis_or_book', 'unstyled', ''}


def family_of(name):
    fam, comma, _ = name.strip().partition(',')
    return title_key(fam if comma else (name.split() or [''])[-1])


def main_title(t):
    return title_key((t or '').split(':')[0])


def whole_key(t):
    return title_key((t or '').split(' / ')[0].replace(' : ', ': '))


def tie_break(found, row, titles, state):
    """Several LC works under one main title (Agamben's *Homo sacer* in Italian and in English): the one whose
    whole title agrees with the citation's, else the one first published within two years of the cited year,
    when exactly one does (2026-11-03)."""
    whole = whole_key(row['title'])
    same = {w for w in found if any(whole_key(t) == whole for t in titles[w])}
    if len(same) == 1:
        return same
    y = int(row['year']) if (row.get('year') or '').isdigit() else None
    if y:
        near = set()
        for w in same or found:
            years = [int(m.rsplit(':', 1)[1]) for m in state.members.get(w, ()) if m.startswith(('lc-first-year:', 'year:'))
                     and m.rsplit(':', 1)[1].isdigit()]
            if years and abs(min(years) - y) <= 2:
                near.add(w)
        if len(near) == 1:
            return near
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--corpus', type=Path, default=CORPUS)
    args = ap.parse_args()
    state = State.load(args.state)
    titles = defaultdict(set)                         # live work -> its label and the labels of keys merged into it
    for k, v in state.keys.items():
        if v['type'] == 'work':
            for live in state.lookup(k):
                titles[live].add(v['label'])
    index = defaultdict(set)                          # (family, main title) -> LC work keys
    for _, subj, pred, obj in state.relations():
        if pred not in ('authored', 'edited') or len(obj) != 1:
            continue
        w = obj[0]
        lccns = sorted(a[5:] for a in state.keys[w]['anchors'] if a.startswith('lccn:'))
        if not lccns:
            continue
        for label in titles[w]:
            mt = main_title(label.replace(' : ', ':'))
            for p in subj:
                fam = family_of(state.keys[p]['label'])
                if fam and mt:
                    index[fam, mt].add(w)
    report, rows = Counter(), []
    with (args.corpus / 'works.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['kind'] not in BOOKISH:
                continue
            report['cited_books'] += 1
            mt = main_title(r['title'])
            if not mt:
                continue
            found = set()
            for name in r['authors'].split(';'):
                found |= index.get((family_of(name), mt), set())
            if len(found) > 1:                        # an original and its translation share a main title (Homo sacer)
                found = tie_break(found, r, titles, state) or found
            if len(found) == 1:
                w = found.pop()
                rows.append((r['work_id'], w, min(a[5:] for a in state.keys[w]['anchors'] if a.startswith('lccn:')),
                             state.keys[w]['label'][:200], r['cited_by_dissertations']))
                report['matched'] += 1
                report['citations_matched'] += int(r['cited_by_all'] or 0)
            elif found:
                report['several_lc_works'] += 1
    args.out.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work_id', 'key', 'lccn', 'title', 'cited_by_dissertations'])
        w.writerows(rows)
    summary = dict(**dict(sorted(report.items())), keyed_works=len({r[1] for r in rows}))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
