"""Atlas source works -> the LC book works they cite (2026-11-02). Writes a proposal.

The atlas keys each cited source as a work (`atlas:source:<id>`). Where the source is a whole book that LC
catalogued under a keyed person (scripts/key_lc_works.py), the two keys are one work and merge:
- the source's title or citation contains the book's normalised main title and the family name of one of the book's authors or editors (an `authored` or
  `edited` relation from the LC catalogue); or the source's URL or citation carries an ISBN of one of the
  book's LC records;
- the citation does not quote a part title ("“Thick Description,” The Interpretation of Cultures" cites an
  essay in the book, not the book) or name a part (pages, a chapter, the introduction, a section; 'with an introduction by' describes an
  edition, not a part). Such
  sources are listed in `part-of.json` for a later part-of relation, not merged. Reviews of the book are
  skipped, as are interviews, commentaries, symposia, forums, obituaries and responses (each is its own work);
- the matching family name is not part of the book's own title (*Cheikh Anta Diop: An African Scientist*, by
  another Diop, matched every source naming Diop);
- a title of one or two words (*Orientalism*) counts only as the source's whole title after its author's
  family name ('Edward Said: Orientalism (1978)'): an LC memoir titled *Stanford* had gathered every
  Stanford Encyclopedia page;
- exactly one LC work matches. Several atlas sources citing the same whole book merge with it as one work.

    python3 scripts/key_atlas_lc_works.py --out data/identifiers/atlas-lc-works-2026-11-02
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import title_key

ATLAS = ROOT / 'historiography-1920-2000.json'
QUOTED = re.compile(r'[“"‘][^”"’]{4,}[”"’]')
REVIEW = re.compile(r'\breview(ed|s)?\b|\binterview|\bcommentary\b|\bsymposium\b|\broundtable\b|\bforum\b|\bobituary\b|\bresponse\b', re.I)
PART = re.compile(r'\bpp?\.\s*[0-9ivxlc]|\bchapters?\b|\bintroduction\b(?! by)|\bpreface\b(?! by)|\bforeword\b(?! by)|\bbook [ivx0-9]+\b|\bsection\b|\bpart [ivx0-9]+\b', re.I)
ISBN = re.compile(r'97[89][0-9]{10}|\b[0-9]{9}[0-9Xx]\b')


def family(label):
    fam, comma, _ = label.partition(', ')
    return title_key(fam if comma else label.split()[-1] if label.split() else label)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--index', default='/mnt/e/lc-bib-2016/index')
    args = ap.parse_args()
    state = State.load(args.state)
    sources = {s['id']: s for s in json.loads(ATLAS.read_text())['sources']}
    people = defaultdict(set)                         # LC work key -> family names of its authors and editors
    for _, subj, pred, obj in state.relations():
        if pred in ('authored', 'edited') and len(obj) == 1 and any(a.startswith('lccn:') for a in state.keys[obj[0]]['anchors']):
            for p in subj:
                people[obj[0]].add(family(state.keys[p]['label']))
    by_start = defaultdict(list)                      # first three title words -> (LC work key, title key)
    short = defaultdict(list)                         # one- and two-word titles -> LC work keys
    for w in people:
        tk = title_key(state.keys[w]['label'].split(' : ')[0])
        if len(tk.split()) >= 3:
            by_start[' '.join(tk.split()[:3])].append((w, tk))
        elif tk:
            short[tk].append(w)
    lccn_work = {a[5:]: k for a, k in state.anchor.items() if a.startswith('lccn:')}
    report, ops, part_of, queue, joins = Counter(), [], [], [], defaultdict(list)
    atlas_works = defaultdict(list)
    for a, k in state.anchor.items():
        if a.startswith('atlas:source:') and state.keys[k]['type'] == 'work':
            atlas_works[k].append(a[len('atlas:source:'):])
    isbn_texts = {}
    for k, ids in atlas_works.items():
        isbn_texts[k] = {m.upper() for i in ids for m in ISBN.findall(' '.join(str(sources.get(i, {}).get(f, '')) for f in ('url', 'citation')))}
    want = {i for v in isbn_texts.values() for i in v}
    isbn_lccn = {}
    if want:
        db = duckdb.connect()
        db.execute('CREATE TABLE want(i VARCHAR)')
        db.executemany('INSERT INTO want VALUES (?)', [(i,) for i in want])
        for isbn, control in db.execute(f"""WITH r AS (SELECT trim(control) AS control, unnest(isbns) AS isbn
                FROM read_parquet('{args.index}/records-*.parquet')) SELECT isbn, control FROM r JOIN want ON r.isbn = want.i""").fetchall():
            isbn_lccn[isbn] = control
    for k, ids in sorted(atlas_works.items()):
        if any(a.startswith('lccn:') for a in state.keys[k]['anchors']):
            report['already_joined'] += 1
            continue
        recs = [sources[i] for i in ids if i in sources]
        text = ' '.join(f'{r.get("title", "")} {r.get("citation", "")}' for r in recs)
        norm = ' ' + title_key(text.replace(':', ' ')) + ' '
        words = norm.split()
        found = {}
        for i in range(len(words) - 2):
            for w, tk in by_start.get(' '.join(words[i:i + 3]), ()):
                if f' {tk} ' in norm and any(f and f' {f} ' in norm and f not in tk.split() for f in people[w]):
                    found[w] = 'title and author'
        for r in recs:          # a short title only as the source's whole title after its author: 'Edward Said: Orientalism (1978)'
            own = [t for t in title_key((r.get('title') or '').replace(':', ' ')).split()]
            for n in (1, 2):
                for i in range(1, min(len(own), 6)):
                    rest = [t for t in own[i + n:] if not t.isdigit()]
                    for w in short.get(' '.join(own[i:i + n]), ()) if not rest else ():
                        if own[i - 1] in people[w]:
                            found[w] = 'title and author'
        for isbn in isbn_texts[k]:
            if isbn in isbn_lccn and isbn_lccn[isbn] in lccn_work:
                found[lccn_work[isbn_lccn[isbn]]] = 'ISBN'
        if not found:
            report['no_lc_work'] += 1
            continue
        cited = ' '.join(f'{r.get("title", "")} {r.get("citation", "")}' for r in recs)
        if REVIEW.search(cited):
            report['a_review_of_the_book'] += 1
            continue
        quoted = [q for r in recs for q in QUOTED.findall(r.get('citation', '') or '')] + PART.findall(cited)
        if quoted:
            part_of.append(dict(work=k, label=state.keys[k]['label'], parts=quoted, books={w: state.keys[w]['label'] for w in found}))
            report['part_of_a_book'] += 1
            continue
        if len(found) > 1:
            queue.append(dict(kind='atlas_source_several_lc_works', work=k, label=state.keys[k]['label'],
                              lc_works={w: state.keys[w]['label'] for w in found}))
            report['several_lc_works'] += 1
            continue
        (w, how), = found.items()
        joins[w].append((k, how))
    for w, ks in sorted(joins.items()):                 # several atlas sources citing one whole book are one work
        into = min((k for k, _ in ks), key=lambda k: int(k[2:]))
        for k, how in ks:
            if k != into:
                ops.append(dict(event='merge', key=k, into=into, basis=f'both atlas sources cite LC\'s book {state.keys[w]["label"][:120]}'))
                report['atlas_sources_merged'] += 1
        ops.append(dict(event='merge', key=w, into=into, basis=f'the atlas source is LC\'s book {state.keys[w]["label"][:120]} ({ks[0][1]})'))
        report['merged_' + ks[0][1].replace(' ', '_')] += 1
    materialise(state, dict(basis='atlas lc works', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis='atlas sources that are LC-catalogued books', decided_by='build',
                                                            ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'part-of.json').write_text(json.dumps(part_of, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    summary = dict(atlas_works=len(atlas_works), **dict(sorted(report.items())), ops=len(ops))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
