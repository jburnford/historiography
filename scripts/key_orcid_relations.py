"""ORCID-claimed chapters -> the volume they are part of; ORCID-claimed reviews -> the book reviewed (2026-11-05).

User, 2026-11-05, asking for his network ("co-authors, people I've reviewed, students, supervisors, ... editors of
books I've published in"): key_orcid_works.py keyed his chapters and reviews as works, but nothing tied a chapter
to its edited volume or a review to its book, so neither editors nor reviewed authors could be reached. ORCID gives
a chapter's volume title (`journal-title`) and titles a review with the book's title. For every work claimed in a
cached ORCID record (key_orcid_works' `orcid-work:<orcid>:<put-code>` anchor, or its DOI):
- a book chapter whose volume title names exactly one book in the graph (key_lc_works.title_key of the main title,
  an H-Net 'Editor et al. (eds.), ' prefix removed) is `part_of` that book (claim `orcid-part-of:<orcid>:<code>`);
- a book review whose title names exactly one book in the graph `reviews` it (claim `orcid-reviews:<orcid>:<code>`).
A title naming no book or several is counted and left. build_graph derives EDITOR_OF (a volume's editor -> each
author of a chapter in it) and REVIEWED (the review's author -> the book's authors) from these.

    python3 scripts/key_orcid_relations.py --out data/identifiers/orcid-relations-2026-11-05
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import title_key
from key_orcid_works import RECORDS

GRAPH = ROOT / 'build/graph'
EDS = re.compile(r'^.{0,200}?\((?:eds?|editors?|hrsg|dir|orgs?)\.?\)\s*,\s*', re.I)


def main_title(t):
    t = EDS.sub('', t or '')
    return title_key(re.split(r'\s*[:;/]\s*|\s+—\s+', t)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    db = duckdb.connect()
    books = defaultdict(set)                           # main title key -> book work keys
    for key, label in db.execute(f"SELECT key, label FROM '{GRAPH}/work.parquet' WHERE kind IN ('book', 'edited_book', 'lc_book') "
                                 "OR list_has_any(list_transform(anchors, a -> split_part(a, ':', 1)), ['lccn', 'isbn', 'hnet-book'])").fetchall():
        k = main_title(label)
        if len(k.split()) >= 2:
            books[k].add(key)
    orcids = [o for (o,) in db.execute(f"SELECT orcid FROM '{GRAPH}/person.parquet' WHERE orcid IS NOT NULL").fetchall()]
    state = State.load(args.state)
    report, ops = Counter(), []
    for o in orcids:
        path = RECORDS / f'{o}.json'
        if not path.exists():
            continue
        groups = ((json.loads(path.read_text()).get('activities-summary') or {}).get('works') or {}).get('group') or []
        for g in groups:
            s = g['work-summary'][0]
            kind = s.get('type')
            if kind not in ('book-chapter', 'book-review'):
                continue
            code = s.get('put-code')
            ids = [e for e in ((s.get('external-ids') or {}).get('external-id') or []) if e.get('external-id-type') == 'doi']
            work = state.lookup(f'orcid-work:{o}:{code}') or (state.lookup(f"doi:{ids[0]['external-id-value'].lower()}") if ids else [])
            if len(work) != 1:
                report[f'{kind}:work_not_keyed'] += 1
                continue
            if kind == 'book-chapter':
                target = main_title((s.get('journal-title') or {}).get('value') or '')
                pred, anchor = 'part_of', f'orcid-part-of:{o}:{code}'
            else:
                t = ((s.get('title') or {}).get('title') or {}).get('value') or ''
                target = main_title(re.sub(r'^(review of|rev\.|compte rendu( de)?)\s*:?\s*', '', t, flags=re.I))
                pred, anchor = 'reviews', f'orcid-reviews:{o}:{code}'
            hits = books.get(target, set()) - set(work) if target else set()
            if len(hits) != 1:
                report[f'{kind}:{"no_book" if not hits else "several_books"}'] += 1
                continue
            if anchor in state.anchor:
                report[f'{kind}:claim_exists'] += 1
                continue
            report[f'{kind}:linked'] += 1
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded', anchors=[anchor],
                            relation=dict(subject=work[0], predicate=pred, object=next(iter(hits))),
                            basis=f"the person's ORCID record names the {'volume' if pred == 'part_of' else 'book reviewed'}"))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='chapters and reviews claimed in ORCID records tied to the volume or book they name', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
