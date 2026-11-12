"""Corpus-id authorship claims whose record names another given name -> groups for Sol to judge by works (2026-11-05).

recheck_corpus_claims.py lists `cited-authored` / `verdict-authored` claims whose JSTOR or Crossref record names an
author of that family whose given names disagree with the person holding the corpus id (Eleanor Cowan's article on
Edward J. Cowan's key). Names alone are not the test (identity by works; a JSTOR record can carry a typo or a
nickname: 'Roberto' for Roberta Mazza, 'Toby' Higbie), so each claim goes to a reader with the article and the
key's other works. apply_corpus_claim_verdicts.py withdraws the claims judged `other`.

    python3 scripts/corpus_claim_groups.py --dir data/identifiers/corpus-claims-recheck-2026-11-05
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import duckdb

from identifiers import ROOT
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

GRAPH = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--size', type=int, default=20)
    args = ap.parse_args()
    items = json.loads((args.dir / 'candidates.json').read_text())
    db = duckdb.connect()
    db.execute('CREATE TABLE d(a VARCHAR)')
    db.executemany('INSERT INTO d VALUES (?)', [(i['doi'],) for i in items])
    art = {a: (label, year, kind) for a, label, year, kind in db.execute(
        f"""SELECT a, label, year, kind FROM (SELECT label, year, kind, unnest(anchors) AS a FROM '{GRAPH}/work.parquet')
            WHERE a IN (SELECT a FROM d)""").fetchall()}
    keys = sorted({i['key'] for i in items})
    db.execute('CREATE TABLE k(k VARCHAR)')
    db.executemany('INSERT INTO k VALUES (?)', [(k,) for k in keys])
    works = defaultdict(list)
    for k, title, year in db.execute(f"""SELECT a."from", w.label, w.year FROM {keylog(GRAPH, 'authored')} a
            JOIN '{GRAPH}/work.parquet' w ON w.key = a."to" WHERE a."from" IN (SELECT k FROM k)
            ORDER BY w.kind = 'book' DESC, w.year""").fetchall():
        works[k].append(f"{(title or '')[:120]} ({year or '?'})")
    anchors = {k: [a for a in an if not a.startswith(('diss-person:', 'lc-', 'cited-', 'verdict-'))][:8]
               for k, an in db.execute(f"SELECT key, anchors FROM '{GRAPH}/person.parquet' WHERE key IN (SELECT k FROM k)").fetchall()}
    out = []
    for i in items:
        t = art.get(i['doi'], ('', '', ''))
        out.append(dict(claim=i['claim'], doi=i['doi'], article=t[0], year=t[1], record_author=i['record'],
                        corpus_id=i['id'], key=i['key'], person=i['person'], person_anchors=anchors.get(i['key'], []),
                        person_works=[w for w in works[i['key']] if not w.startswith((t[0] or '\0')[:60])][:25]))
    groups = [dict(id=f'g{n // args.size + 1:03d}', items=out[n:n + args.size]) for n in range(0, len(out), args.size)]
    (args.dir / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(items=len(out), groups=len(groups))))


if __name__ == '__main__':
    main()
