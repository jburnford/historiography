"""JSTOR article citations of keyed works -> a compact committed table (2026-11-06).

The JSTOR full-text session parses the notes of JSTOR research articles, review essays and review articles and
matches the cited works to the graph read-only (/mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet; see
data/field-research/jstor-fulltext-2026-11-06/HANDOVER-match-candidates.md). JSTOR's legal team cleared releasing the
citation graph (2026-11-06); the notes themselves are never committed. This keeps one row per citing work and cited
work:
- basis 'strong' (title key and first-author family name agree, year within one) or 'title+year' (a unique title
  of three or more words with no person on the work, year within one);
- one graph work only (n_works = 1; more than one = duplicate or namesake keys, left for dedupe);
- 'edition?' rows (reprints and translations of the cited work) are left out: same work, another edition; they
  are kept for a later edition relation, not merged.
The citing work is the JSTOR item's own work key (key_jstor_articles.py); keys resolve through merges at build
time (scripts/build_graph.py). `citations` counts the notes citing the work, Ibid. and short forms included.

    python3 scripts/export_jstor_citations.py --out data/graph/jstor-cites.csv.gz
"""
import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

import duckdb

MATCHES = Path('/mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--matches', type=Path, default=MATCHES)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    report = Counter(dict(db.execute(f"SELECT basis, count(*) FROM '{args.matches}' GROUP BY 1").fetchall()))
    rows = db.execute(f"""SELECT citing_work, work, sum(coalesce(weight, 1))::INT FROM '{args.matches}'
        WHERE basis IN ('strong', 'title+year') AND n_works = 1 AND citing_work IS NOT NULL AND citing_work <> work
        GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    report['skipped_no_citing_work'] = db.execute(f"SELECT count(*) FROM '{args.matches}' WHERE citing_work IS NULL").fetchone()[0]
    report['skipped_several_works'] = db.execute(f"SELECT count(*) FROM '{args.matches}' WHERE n_works > 1 AND basis <> 'edition?'").fetchone()[0]
    with gzip.open(args.out, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['citing_work', 'cited_work', 'citations'])
        w.writerows(rows)
    report['edges'] = len(rows)
    report['citing_works'] = len({r[0] for r in rows})
    report['cited_works'] = len({r[1] for r in rows})
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
