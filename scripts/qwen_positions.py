"""Where each position Qwen read sits in the printed lists (2026-11-13): data/graph/scored-links/qwen-positions.csv.gz
(position, tbl, list_source, pos) for the positions of data/graph/scored-links/qwen-labels.csv.gz, from the classifier
inputs' meta.parquet (build/linkclf-2026-11-13/clf-inputs). The build (graph_scored_links.model_layer) reads it to find
the rule linker's row for the same position: claims work-people:<role>:<pos> (tbl wp) and name-only:<source>:<pos>
(tbl no). Ids and list positions only.

    python3 scripts/qwen_positions.py [--meta build/linkclf-2026-11-13/clf-inputs/meta.parquet]
"""
import argparse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--meta', default=str(ROOT / 'build/linkclf-2026-11-13/clf-inputs/meta.parquet'))
    ap.add_argument('--labels', default=str(ROOT / 'data/graph/scored-links/qwen-labels.csv.gz'))
    ap.add_argument('--out', default=str(ROOT / 'data/graph/scored-links/qwen-positions.csv.gz'))
    a = ap.parse_args()
    db = duckdb.connect()
    tmp = a.out + '.tmp.csv.gz'
    db.execute(f"""COPY (SELECT q.position, m.tbl, m.source AS list_source, m.pos
        FROM read_csv('{a.labels}') q LEFT JOIN '{a.meta}' m ON m.pid = q.position ORDER BY q.position)
        TO '{tmp}' (HEADER, COMPRESSION gzip)""")
    n, miss = db.execute(f"SELECT count(*), count(*) FILTER (WHERE pos IS NULL) FROM read_csv('{tmp}')").fetchone()
    Path(tmp).replace(a.out)
    print(f'{n} positions, {miss} without a list position -> {a.out}')


if __name__ == '__main__':
    main()
