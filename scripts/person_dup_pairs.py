"""Possible duplicate people after the cited-book-author route -> pair groups for Sol to judge by works (2026-11-03).

key_cited_book_authors.py minted a key for each author of a much-cited book that no key held (identity by works:
LC catalogues the book under that authority). Some of those authors were already keys without an LC authority: a
PhD from the AHA directory, a Brazilian thesis author, an ORCID holder, an atlas person (Abreu, Jean Luiz Neves is
both the author of the cited book and of the UFMG thesis behind it). Names alone decide nothing (identity by works),
so this only gathers pairs for a reader: a key minted by those runs and an older key without an LC authority whose
family name and first given name agree, each with its anchors and its works in the graph (build/graph).

    python3 scripts/person_dup_pairs.py --proposals data/identifiers/cited-book-authors-2026-11-03/proposal.json \\
        data/identifiers/cited-book-authors-2026-11-03b/proposal.json --out data/identifiers/person-dups-2026-11-03
"""
import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb

from identifiers import ROOT

GRAPH = ROOT / 'build/graph'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def name_key(label):
    """('family', 'first given name') from 'Family, Given' or 'Given Family'; dates and fuller forms dropped."""
    l = fold(re.sub(r'\([^)]*\)', '', label or ''))
    if ',' in l:
        fam, giv = l.split(',', 1)
        giv = re.sub(r'[\d\-?]+.*', '', giv)
    else:
        t = l.split()
        fam, giv = (t[-1] if t else ''), ' '.join(t[:-1])
    g = [x for x in re.split(r'[\s.]+', giv) if x]
    return re.sub(r'[^a-z ]', '', fam).strip(), (g[0] if g else '')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--proposals', type=Path, nargs='+', required=True, help='book-author proposals whose mints are checked')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--size', type=int, default=15)
    args = ap.parse_args()
    minted = {a for p in args.proposals for o in json.loads(p.read_text())['ops'] if o['event'] == 'mint'
              for a in o['anchors'] if a.startswith('lcnaf:')}
    db = duckdb.connect()
    people = db.execute(f"SELECT key, label, lcnaf, anchors FROM '{GRAPH}/person.parquet'").fetchall()
    works = defaultdict(list)
    for p, title, year, kind in db.execute(f"""
            SELECT a."from", w.label, w.year, w.kind FROM (SELECT "from", "to" FROM '{GRAPH}/authored.parquet'
                   UNION SELECT "from", "to" FROM '{GRAPH}/edited.parquet') a JOIN '{GRAPH}/work.parquet' w ON w.key = a."to"
            ORDER BY w.year NULLS LAST""").fetchall():
        works[p].append(dict(title=(title or '')[:160], year=year, kind=kind))
    # a thesis author's key often has no AUTHORED edge to the thesis: show it from the thesis work's anchor
    thesis = {}
    for title, year, anchors in db.execute(f"""SELECT label, year, anchors FROM '{GRAPH}/work.parquet'
                                             WHERE len(list_filter(anchors, a -> a LIKE 'diss-thesis:%' OR a LIKE 'aha-diss:%')) > 0""").fetchall():
        for a in anchors:
            if a.startswith('diss-thesis:'):
                thesis['diss-author:' + a[12:]] = dict(title=(title or '')[:160], year=year, kind='thesis')
            elif a.startswith('aha-diss:'):
                thesis['aha-phd:' + a[9:]] = dict(title=(title or '')[:160], year=year, kind='thesis')
    for k, _, _, anchors in people:
        have = {w['title'] for w in works[k]}
        works[k] += [thesis[a] for a in anchors if a in thesis and thesis[a]['title'] not in have]
    new = [p for p in people if p[2] and f'lcnaf:{p[2]}' in minted]
    old = defaultdict(list)
    for p in people:
        if not p[2]:
            old[name_key(p[1])].append(p)
    pairs = []
    for k, label, lc, anchors in new:
        nk = name_key(label)
        if len(nk[1]) < 2:
            continue
        for k2, label2, _, anchors2 in old.get(nk, ()):
            if not works[k2] and not any(not a.startswith('diss-person:') for a in anchors2):
                continue
            show = lambda a: [x for x in a if not x.startswith(('lc-', 'cited-', 'verdict-'))][:12]
            pairs.append(dict(id=f'{k}~{k2}', a=dict(key=k, label=label, anchors=show(anchors), works=works[k][:30]),
                              b=dict(key=k2, label=label2, anchors=show(anchors2), works=works[k2][:30])))
    groups = [dict(id=f'g{i // args.size + 1:03d}', pairs=pairs[i:i + args.size]) for i in range(0, len(pairs), args.size)]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(new_keys=len(new), pairs=len(pairs), groups=len(groups))))


if __name__ == '__main__':
    main()
