#!/usr/bin/env python3
"""Job B, step 1 (local, read-only): the inputs scripts/crossref_identity_evidence.py needs on spark (2026-11-17).

  b_authored.parquet  person key, work key, DOI, work year, kind, evidence, source, role (AUTHORED + EDITED rows of
                      works with a DOI: a doi: anchor or a doi: key)
  b_persons.parquet   person keys: label, ORCID anchors, all anchors, cited, works
  b_graph_dois.parquet every DOI the graph holds (anchors and doi: keys), for the outside-venue sweep

  python3 scripts/crossref_identity_inputs.py OUTDIR
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def main(out):
    out = Path(out)
    db = duckdb.connect()
    db.execute("set threads=2; set memory_limit='5GB'")
    db.execute(f"attach '{ROOT}/build/graph/explorer.duckdb' as g (read_only)")
    db.execute("""create temp table wd as
        select key, lower(substr(a, 5)) doi, year, kind from g.nodes, unnest(anchors) u(a)
        where type='work' and starts_with(a, 'doi:')
        union select key, lower(substr(key, 5)), year, kind from g.nodes where type='work' and starts_with(key, 'doi:')""")
    db.execute(f"copy (select distinct doi from wd) to '{out}/b_graph_dois.parquet' (format parquet)")
    db.execute(f"""copy (
        select e."from" person, e."to" "work", wd.doi, wd.year, wd.kind, 'authored' rel, e.evidence, e.source, e.role
        from g.e_authored_f e join wd on wd.key = e."to" where starts_with(e."from", 'p-')
        union all
        select e."from", e."to", wd.doi, wd.year, wd.kind, 'edited', e.evidence, e.source, e.role
        from g.e_edited_f e join wd on wd.key = e."to" where starts_with(e."from", 'p-')
        ) to '{out}/b_authored.parquet' (format parquet)""")
    db.execute(f"""copy (select key, label, anchors, list_transform(list_filter(anchors, a->starts_with(a,'orcid:')),
                   a->substr(a,7)) orcids, cited, works, weight
        from g.nodes where type='person') to '{out}/b_persons.parquet' (format parquet)""")
    for f in ('b_graph_dois', 'b_authored', 'b_persons'):
        print(f, db.execute(f"select count(*) from '{out}/{f}.parquet'").fetchone())


if __name__ == '__main__':
    main(sys.argv[1])
