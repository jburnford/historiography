"""POSSIBLY_SAME person pairs -> an outside-review queue for Terra (Codex) agents (2026-11-09; user: "use Codex as fast as
you want"). scripts/key_possible_same.py recorded 14,672 same-name pairs whose timelines fit but that no identifier,
shared work or dissertation route could settle; this writes one folder per pair with item.json (both keys: label,
anchors, life years, dissertation, dated works, citing items) for an agent to judge by works and careers (BRIEF.md in the
review folder). Pairs are ordered by the citing items on the less-cited key (user, 2026-11-08: the more citations on
both sides of a split, the more it matters), and cut into batch-NNN.json files of 150 pairs.

    python3 scripts/export_possible_same_review.py --out data/identifiers/possible-same-review-2026-11-09
"""
import argparse, csv, gzip, json
from collections import defaultdict
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--batch', type=int, default=150)
    args = ap.parse_args()
    db = duckdb.connect(); db.execute("SET memory_limit = '6GB'")
    pairs = db.execute(f"""select distinct least("from", "to") AS a, greatest("from", "to") AS b
                           from '{G}/possibly_same.parquet'""").fetchall()
    keys = {k for p in pairs for k in p}
    db.execute("create temp table ks(k varchar)"); db.executemany("insert into ks values (?)", [(k,) for k in keys])
    person = {k: (l, a) for k, l, a in db.execute(f"select key, label, anchors from '{G}/person.parquet' where key in (select k from ks)").fetchall()}
    works = defaultdict(list)
    for p, key, label, kind, year, journal in db.execute(f"""
            select x."from", w.key, w.label, w.kind, w.year, w.journal
            from (select "from", "to" from '{G}/authored.parquet' union select "from", "to" from '{G}/edited.parquet') x
            join '{G}/work.parquet' w on w.key = x."to" where x."from" in (select k from ks)
            order by w.year nulls last""").fetchall():
        works[p].append(dict(title=(label or '')[:250], year=year, kind=kind, journal=journal))
    cited = dict(db.execute(f"""
            select x."from", count(distinct c."from") from '{G}/authored.parquet' x
            join '{G}/cites.parquet' c on c."to" = x."to" where x."from" in (select k from ks) group by 1""").fetchall())
    supervised = defaultdict(list)
    try:
        for p, label, year in db.execute(f"""select s."from", w.label, w.year from '{G}/supervised.parquet' s
                join '{G}/work.parquet' w on w.key = s."to" where s."from" in (select k from ks)""").fetchall():
            supervised[p].append(dict(thesis=(label or '')[:200], year=year))
    except duckdb.Error:
        pass
    affil = defaultdict(list)
    try:
        for p, inst in db.execute(f"""select a."from", i.label from '{G}/affiliated_with.parquet' a
                join '{G}/institution.parquet' i on i.key = a."to" where a."from" in (select k from ks)""").fetchall():
            affil[p].append(inst)
    except duckdb.Error:
        pass
    life = {}
    with gzip.open(ROOT / 'data/person-facts/life-years.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['key'] in keys:
                life[r['key']] = dict(birth=r['birth'] or None, death=r['death'] or None)

    def side(k):
        label, anchors = person.get(k, ('', []))
        return dict(key=k, label=label, anchors=[a for a in anchors or [] if not a.startswith('possible-same:')],
                    life_years=life.get(k), citing_items=cited.get(k, 0), works=works.get(k, [])[:40],
                    n_works=len(works.get(k, [])), supervised_theses=supervised.get(k, [])[:10],
                    affiliations=sorted(set(affil.get(k, [])))[:10])
    items = []
    for a, b in pairs:
        if a not in person or b not in person:
            continue
        items.append(dict(a=side(a), b=side(b)))
    items.sort(key=lambda it: (-min(it['a']['citing_items'], it['b']['citing_items']),
                               -(it['a']['citing_items'] + it['b']['citing_items'])))
    args.out.mkdir(parents=True, exist_ok=True)
    ids = []
    for n, it in enumerate(items, 1):
        pid = f'ps{n:05d}'
        it['id'] = pid
        d = args.out / pid
        d.mkdir(exist_ok=True)
        (d / 'item.json').write_text(json.dumps(it, ensure_ascii=False, indent=1) + '\n')
        ids.append(pid)
    for i in range(0, len(ids), args.batch):
        (args.out / f'batch-{i // args.batch + 1:03d}.json').write_text(json.dumps(dict(items=ids[i:i + args.batch])) + '\n')
    (args.out / 'index.json').write_text(json.dumps([dict(id=it['id'], a=it['a']['key'], b=it['b']['key'],
                                                          label=it['a']['label'], cites=[it['a']['citing_items'], it['b']['citing_items']])
                                                     for it in items], ensure_ascii=False) + '\n')
    print(len(items), 'pairs;', (len(ids) + args.batch - 1) // args.batch, 'batches; top:',
          [(it['a']['label'], it['a']['citing_items'], it['b']['citing_items']) for it in items[:5]])


if __name__ == '__main__':
    main()
