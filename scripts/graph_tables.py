"""Key-log-only reads of the merged graph tables (2026-11-11).

build_graph writes one edge table per relation: authored, edited, coauthored and reviewed carry an `evidence` column,
'keylog' for the key log's claims and 'linked' for rule or identifier credits outside it. Identity work (linkers,
career windows, person roles, merge and split builders) must read the key log's rows only, so that a credit made by a
rule never becomes evidence for another identity decision.

    from graph_tables import keylog
    db.execute(f"SELECT a.\"from\" FROM {keylog(G, 'authored')} a JOIN ...")

keylog(G, name) is a SQL table expression: the evidence = 'keylog' rows of G/name.parquet, or the whole file when it has
no evidence column (a build made before the merge, when these tables held key-log rows only).
"""
from pathlib import Path

import pyarrow.parquet as pq

_HAS = {}


def keylog(graph, name):
    path = Path(graph) / f'{name}.parquet'
    key = str(path)
    if key not in _HAS:
        try:
            _HAS[key] = 'evidence' in pq.read_schema(path).names
        except Exception:
            _HAS[key] = False
    return f"(SELECT * FROM '{path}' WHERE evidence = 'keylog')" if _HAS[key] else f"'{path}'"
