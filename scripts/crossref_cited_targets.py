#!/usr/bin/env python3
"""Job A, step 1 (local, read-only): the held cited works without a DOI, with their authors, as one Parquet table
to copy to spark for scripts/crossref_cited_match.py (2026-11-17).

Reads build/graph/explorer.duckdb and work.parquet (read-only), data/graph/cited-works/authors.csv.gz,
data/graph/jstor-cited-works/works.csv.gz and the LC personal-name labels on E: (lcid, label only).
Target = a work node with cited > 0, no doi: anchor and a key that is not doi:.

  python3 scripts/crossref_cited_targets.py OUT.parquet
"""
import sys
from collections import defaultdict
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crossref_names import families, german  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'


def main(out):
    db = duckdb.connect()
    db.execute("set threads=2; set memory_limit='4GB'")
    db.execute(f"attach '{ROOT}/build/graph/explorer.duckdb' as g (read_only)")
    db.execute(f"""create temp table t as
        select n.key, n.kind, n.year, n.first_year, n.journal, n.issn, n.isbn, n.editors_printed, n.cited,
               w.label as title, w.variant_titles
        from g.nodes n join '{ROOT}/build/graph/work.parquet' w using (key)
        where n.type='work' and n.cited>0 and not starts_with(n.key,'doi:')
          and len(list_filter(n.anchors, a->starts_with(a,'doi:')))=0""")
    # works whose node is not in work.parquet (unkeyed cited works are only in the explorer): add them
    db.execute("""insert into t select n.key, n.kind, n.year, n.first_year, n.journal, n.issn, n.isbn,
               n.editors_printed, n.cited, n.label, null
        from g.nodes n where n.type='work' and n.cited>0 and not starts_with(n.key,'doi:')
          and len(list_filter(n.anchors, a->starts_with(a,'doi:')))=0 and n.key not in (select key from t)""")
    print('targets', db.execute('select count(*) from t').fetchone(), flush=True)
    names = defaultdict(set)   # key -> {(printed name, source)}
    for rel in ('authored', 'edited'):
        for k, lab in db.execute(f"""select e."to", p.label from g.e_{rel}_t e join g.nodes p on p.key=e."from"
                                    where e."to" in (select key from t)""").fetchall():
            names[k].add((lab, rel))
    for k, raw in db.execute(f"""select work, raw_name from read_csv('{ROOT}/data/graph/cited-works/authors.csv.gz',
                                 all_varchar=true) where raw_name is not null""").fetchall():
        names[k].add((raw, 'cited-works'))
    lcs = db.execute(f"""select id, lc_author from read_csv('{ROOT}/data/graph/jstor-cited-works/works.csv.gz',
                         all_varchar=true) where lc_author is not null""").fetchall()
    want = {l for _, l in lcs}
    lab = {}
    if Path(LC_NAMES).exists():
        db.execute('create temp table want(l varchar)')
        db.executemany('insert into want values (?)', [(x,) for x in want])
        lab = dict(db.execute(f"select lcid, label from read_parquet('{LC_NAMES}') where lcid in (select l from want)").fetchall())
    for k, l in lcs:
        if l in lab:
            names[k].add((lab[l], 'lc-author'))
    for k, ed in db.execute('select key, editors_printed from t where editors_printed is not null').fetchall():
        for e in str(ed).split(';'):
            if e.strip():
                names[k].add((e.strip(), 'editors-printed'))
    rows = db.execute('select key, kind, year, first_year, journal, issn, isbn, cited, title, variant_titles from t').fetchall()
    cols = defaultdict(list)
    for key, kind, year, fy, journal, issn, isbn, cited, title, vt in rows:
        nm = sorted(names.get(key, ()))
        fams = sorted({f for n, _ in nm for f in families(n)})
        for c, v in (('key', key), ('kind', kind), ('year', year), ('first_year', fy), ('journal', journal),
                     ('issn', issn), ('isbn', isbn), ('cited', int(cited or 0)), ('title', title),
                     ('variant_titles', list(vt) if vt is not None else None),
                     ('names', [n for n, _ in nm]), ('name_sources', [s for _, s in nm]), ('families', fams),
                     ('german', german(title or ''))):
            cols[c].append(v)
    pq.write_table(pa.table(cols), out, compression='zstd')
    print('written', len(rows), 'with names', sum(1 for f in cols['families'] if f),
          'german', sum(cols['german']), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
