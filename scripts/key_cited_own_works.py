"""Cited works -> the cited person's own keyed works, by title (2026-11-03). Writes a crosswalk beside the log.

The book crosswalk (key_cited_works) matches cited books to LC works; the article crosswalk (key_cited_articles)
matches cited articles and chapters to JSTOR and Crossref records. Since the ORCID works (key_orcid_works) the log
also holds what people say they wrote, uncited until now: Ian Milligan's 'Illusionary Order' (CHR 2013) and
*History in the Age of Abundance?* (2019) are his works in the graph, but the theses citing them did not reach
them. Here a cited work not in either crosswalk, with a keyed author (the key holding `diss-person:<id>` for an
author the corpus lists), is that key's own work (authored or edited in the graph) when exactly one of those
works has an agreeing title of two words or more (key_cited_articles.titles_agree) and, where both are dated, a year within two.
Reads the graph build's Parquet tables (build/graph), not the log, so it stays small.

    python3 scripts/key_cited_own_works.py --crosswalk data/identifiers/cited-works-2026-11-03/crosswalk.csv.gz \\
        data/identifiers/cited-articles-2026-11-03b/crosswalk.csv.gz --out data/identifiers/cited-own-works-2026-11-03
"""
import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import ROOT
from key_cited_articles import titles_agree
from key_lc_works import title_key

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, nargs='+', required=True, help='crosswalks already made (their works are skipped)')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute("SET memory_limit = '4GB'")
    files = ', '.join(f"'{x}'" for x in args.crosswalk)
    db.execute(f"CREATE TABLE done AS SELECT DISTINCT work_id FROM read_csv([{files}], all_varchar=true, union_by_name=true)")
    db.execute(f"""CREATE TABLE pk AS SELECT substr(a, 13) AS p, key FROM
                   (SELECT key, unnest(anchors) AS a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    db.execute(f"""CREATE TABLE cw AS SELECT au.person_key AS p, w.work_id, w.title, try_cast(w."year" AS INT) AS y
                   FROM read_csv('{CORPUS}/authored.csv.gz') au JOIN read_csv('{CORPUS}/works.csv', all_varchar=true) w USING (work_id)
                   WHERE au.person_key IN (SELECT p FROM pk) AND w.work_id NOT IN (SELECT work_id FROM done)
                     AND coalesce(w.title, '') <> ''""")
    own = defaultdict(list)                          # person key -> (work key, label, year)
    for key, wk, label, year in db.execute(f"""
            SELECT r."from", w.key, w.label, w.year FROM (SELECT "from", "to" FROM '{GRAPH}/authored.parquet'
              UNION SELECT "from", "to" FROM '{GRAPH}/edited.parquet') r JOIN '{GRAPH}/work.parquet' w ON w.key = r."to"
            WHERE r."from" IN (SELECT key FROM pk) AND w.kind <> 'review'""").fetchall():
        own[key].append((wk, label, year))
    keys = defaultdict(set)
    for p, k in db.execute('SELECT p, key FROM pk').fetchall():
        keys[p].add(k)
    report, found = Counter(), {}
    for p, wid, title, y in db.execute('SELECT p, work_id, title, y FROM cw').fetchall():
        if len(title_key(title).split()) < 2:            # 'Introduction', 'Conclusion': never decided by title
            report['one_word_title'] += 1
            continue
        hits = {wk for k in keys[p] for wk, label, wy in own[k]
                if titles_agree(title, label) and not (y and wy and abs(y - wy) > 2)}
        if len(hits) == 1:
            found.setdefault(wid, set()).update(hits)
        elif hits:
            report['several_own_works'] += 1
    rows = sorted((w, next(iter(ks))) for w, ks in found.items() if len(ks) == 1)
    report['cited_works_matched'] = len(rows)
    report['ambiguous_between_authors'] = sum(1 for ks in found.values() if len(ks) > 1)
    args.out.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work_id', 'key'])
        w.writerows(rows)
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
