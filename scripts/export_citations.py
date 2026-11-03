"""Corpus citations of keyed works -> a compact committed table (2026-11-02).

The dissertation corpus's citation table (strict-citations.csv.gz, 2.5M rows) and its works table are build
artefacts of the corpus pipeline and are not in git. The graph build (scripts/build_graph.py) must run from a
clean clone, so the citations it needs are kept here: one row per citing dissertation and cited work that the
key log holds, through the citation crosswalks (scripts/key_cited_works.py for books; scripts/key_cited_articles.py
for articles and chapters, whose keys are `doi:` anchors, resolved at build time like work keys). Rows carry the corpus dissertation
id (anchored in the log as `diss-thesis:<id>`) and the cited work's key, resolved through merges at build time.
Regenerate after each corpus build and crosswalk run.

    python3 scripts/export_citations.py --crosswalk data/identifiers/cited-works-2026-11-02b/crosswalk.csv.gz \
        --out data/graph/cites.csv.gz
"""
import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

from identifiers import ROOT

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, required=True, nargs='+',
                    help='book crosswalk (key_cited_works), then the article crosswalk (key_cited_articles)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--corpus', type=Path, default=CORPUS)
    args = ap.parse_args()
    key_of = {}
    for path in args.crosswalk:                       # a work id the first crosswalk names keeps that key
        with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                key_of.setdefault(r['work_id'], r['key'])
    rows, report = set(), Counter()
    with gzip.open(args.corpus / 'strict-citations.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            report['citations'] += 1
            k = key_of.get(r['work_id'])
            if k:
                rows.add((r['dissertation_id'], k))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['dissertation_id', 'work_key'])
        w.writerows(sorted(rows))
    report['rows'] = len(rows)
    report['dissertations'] = len({d for d, _ in rows})
    report['works'] = len({k for _, k in rows})
    print(json.dumps(report))


if __name__ == '__main__':
    main()
