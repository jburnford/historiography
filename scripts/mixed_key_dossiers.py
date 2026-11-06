"""Person keys that may mix namesakes' works -> dossiers for agents to judge by works (2026-11-05).

For each key: its identifiers (anchors other than claim anchors) and every work credited to it (AUTHORED or EDITED in
build/graph) with the claim that credits it and that claim's source (its anchor scheme: lc-authored, cited-authored,
orcid-claim, crossref-orcid, aha-auth, ...) and subject (`via`: the anchor the claim names, e.g. a corpus id).
apply_mixed_key_verdicts.py reads the agents' verdicts. Keys come from a JSON list (--keys).

    python3 scripts/mixed_key_dossiers.py --keys keys.json --out data/identifiers/mixed-keys-2026-11-05b --batches 7
"""
import argparse
import glob
import gzip
import json
from collections import defaultdict
from pathlib import Path

import duckdb

from identifiers import ROOT

GRAPH = ROOT / 'build/graph'
HIDE = ('lc-', 'cited-', 'verdict-', 'orcid-claim', 'hand-', 'crossref-', 'reviewed-', 'jstor-')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--keys', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--batches', type=int, default=5)
    ap.add_argument('--max-works', type=int, default=120)
    args = ap.parse_args()
    keys = json.loads(args.keys.read_text())
    db = duckdb.connect()
    people = {k: (l, an) for k, l, an in db.execute(f"SELECT key, label, anchors FROM '{GRAPH}/person.parquet'").fetchall()}
    keys = [k for k in keys if k in people]
    db.execute('CREATE TABLE k(k VARCHAR)')
    db.executemany('INSERT INTO k VALUES (?)', [(k,) for k in keys])
    rows = db.execute(f"""
        SELECT a."from", a.claim, 'authored', w.key, w.label, w.year, w.kind FROM '{GRAPH}/authored.parquet' a
          JOIN '{GRAPH}/work.parquet' w ON w.key = a."to" WHERE a."from" IN (SELECT k FROM k)
        UNION ALL SELECT a."from", a.claim, 'edited', w.key, w.label, w.year, w.kind FROM '{GRAPH}/edited.parquet' a
          JOIN '{GRAPH}/work.parquet' w ON w.key = a."to" WHERE a."from" IN (SELECT k FROM k)""").fetchall()
    claims = {r[1] for r in rows}
    src = {}
    for f in sorted(glob.glob(str(ROOT / 'data/identifiers/events-*.jsonl*'))):
        op = gzip.open if f.endswith('.gz') else open
        with op(f, 'rt', encoding='utf-8') as fh:
            for line in fh:
                if '"type": "claim"' not in line:
                    continue
                i = line.find('"key": "c-')
                if i < 0:
                    continue
                c = line[i + 8:line.find('"', i + 8)]
                if c in claims:
                    e = json.loads(line)
                    src[c] = (e['anchors'][0].split(':')[0], e['relation']['subject'])
    works = defaultdict(list)
    for k, c, role, w, label, year, kind in rows:
        s = src.get(c, ('?', '?'))
        works[k].append(dict(claim=c, role=role, work=w, title=(label or '')[:200], year=year, kind=kind, source=s[0], via=s[1]))
    out = [dict(key=k, label=people[k][0], anchors=[a for a in people[k][1] if not a.startswith(HIDE)][:15],
                works=sorted(works[k], key=lambda w: w['year'] or 0)[:args.max_works]) for k in keys if works[k]]
    b, tot = [[] for _ in range(args.batches)], [0] * args.batches
    for d in sorted(out, key=lambda d: -len(d['works'])):
        i = tot.index(min(tot))
        b[i].append(d)
        tot[i] += len(d['works'])
    args.out.mkdir(parents=True, exist_ok=True)
    for i, x in enumerate(b, 1):
        (args.out / f'batch{i}.json').write_text(json.dumps(x, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(keys=len(out), works=sum(tot), batches=[len(x) for x in b])))


if __name__ == '__main__':
    main()
