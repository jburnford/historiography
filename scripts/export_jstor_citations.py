"""JSTOR article citations of keyed works -> a compact committed table (2026-11-06).

The JSTOR full-text session parses the notes of JSTOR research articles, review essays and review articles and
matches the cited works to the graph read-only (/mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet; see
data/field-research/jstor-fulltext-2026-11-06/HANDOVER-match-candidates.md). JSTOR's legal team cleared releasing the
citation graph (2026-11-06); the notes themselves are never committed. This keeps one row per citing work and cited
work:
- basis 'strong' (title key and a cited author's family name agree, year within one; journal pieces cited one or two
  years after the graph year count, the online-first date), 'title+year' (a unique title of three or more words with
  no person on the work, year within one), 'doi' (the note gives the work's DOI) or 'no_year' (title and family agree,
  the note gives no year; 2026-11-08, one graph work only);
- one graph work only (n_works = 1; more than one = duplicate or namesake keys, left for dedupe);
- 'edition?' rows (title and family agree, the years more than one apart) are kept as basis 'edition' when the
  cited year is after the graph work's year (a reprint, later edition or translation: Marx, Tocqueville, Foucault in
  English; JSTOR session and KG session, 2026-11-08), one graph work only; never when the cited year is earlier
  (the graph key may be a later, different work of the same title). A pair with a clean row is basis 'match'.
The citing work is the JSTOR item's own work key (key_jstor_articles.py); keys resolve through merges at build
time (scripts/build_graph.py). `citations` counts the notes citing the work, Ibid. and short forms included.

Qwen re-read (2026-11-07, --qwen): the session's Qwen pass over the notes of the 49,782 articles the rules parse badly
(match-candidates-qwen.parquet, HANDOVER-note-citations-qwen.md; 24/24 Qwen-only pairs right in its hand check).
Its clean pairs are added and the rules' pairs kept (rules-only pairs stay); a pair both give counts the larger
of the two citation counts, not their sum.

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
QWEN = Path('/mnt/e/jstor-fulltext-2026-11-06/match-candidates-qwen.parquet')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--matches', type=Path, default=MATCHES)
    ap.add_argument('--qwen', type=Path, default=QWEN, help="Qwen candidate table; '' to leave it out")
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    report = Counter(dict(db.execute(f"SELECT basis, count(*) FROM '{args.matches}' GROUP BY 1").fetchall()))
    clean = """SELECT citing_work, work, sum(coalesce(weight, 1))::INT AS n FROM {}
        WHERE basis IN ('strong', 'title+year', 'doi', 'no_year') AND n_works = 1 AND citing_work IS NOT NULL AND citing_work <> work
        GROUP BY 1, 2"""
    # an online-first match through a later cited author can be another author's same-title reply ('The Economic
    # Depression of the Renaissance' 1962/1964): online_first only through the first cited author (JSTOR session, 2026-11-08)
    def source(path, name):
        cols = {d[0] for d in db.execute(f"SELECT * FROM '{path}' LIMIT 0").description}
        if not {'route', 'author_rank'} <= cols:
            return f"'{path}'"
        report[f'{name}_skipped_online_first_later_author'] = db.execute(
            f"SELECT count(*) FROM '{path}' WHERE route = 'online_first' AND author_rank > 0").fetchone()[0]
        return f"(SELECT * FROM '{path}' WHERE NOT (route = 'online_first' AND coalesce(author_rank, 0) > 0))"
    rules = source(args.matches, 'rules')
    parts = [clean.format(rules)]
    qwen = None
    if args.qwen and str(args.qwen) and args.qwen.exists():
        qwen = source(args.qwen, 'qwen')
        parts.append(clean.format(qwen))
        report['qwen_clean_pairs'] = db.execute(f"SELECT count(*) FROM ({parts[1]})").fetchone()[0]
        report['rules_clean_pairs'] = db.execute(f"SELECT count(*) FROM ({parts[0]})").fetchone()[0]
    edition = """SELECT citing_work, work, sum(coalesce(weight, 1))::INT AS n FROM {}
        WHERE basis = 'edition?' AND n_works = 1 AND citing_work IS NOT NULL AND citing_work <> work
          AND cited_year > work_year GROUP BY 1, 2"""
    eparts = [edition.format(p) for p in [rules] + ([qwen] if qwen else [])]
    rows = db.execute(f"""WITH m AS (SELECT citing_work, work, max(n) n FROM ({' UNION ALL '.join(parts)}) GROUP BY 1, 2),
        e AS (SELECT citing_work, work, max(n) n FROM ({' UNION ALL '.join(eparts)}) GROUP BY 1, 2)
        SELECT citing_work, work, n, 'match' FROM m
        UNION ALL SELECT citing_work, work, n, 'edition' FROM e ANTI JOIN m USING (citing_work, work)
        ORDER BY 1, 2""").fetchall()
    report['edition_edges'] = sum(r[3] == 'edition' for r in rows)
    report['skipped_no_citing_work'] = db.execute(f"SELECT count(*) FROM '{args.matches}' WHERE citing_work IS NULL").fetchone()[0]
    report['skipped_several_works'] = db.execute(f"SELECT count(*) FROM '{args.matches}' WHERE n_works > 1 AND basis <> 'edition?'").fetchone()[0]
    with gzip.open(args.out, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['citing_work', 'cited_work', 'citations', 'basis'])
        w.writerows(rows)
    report['edges'] = len(rows)
    report['citing_works'] = len({r[0] for r in rows})
    report['cited_works'] = len({r[1] for r in rows})
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
