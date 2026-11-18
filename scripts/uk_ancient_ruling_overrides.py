#!/usr/bin/env python3
"""Apply the ancient-history ruling (user, 2026-11-17) to UK doctorates already in the manifest.

The UK screen (uk_dissertation_scope.classify) files Edinburgh School of History, Classics and Archaeology theses
with a classical-antiquity title as 'classical_school_title', which the graph builder counts as needs_review.
Manifest entries are never rewritten, so the ruling reaches them through record-level rows in
eligibility-overrides.csv: an entry with that scope and no override yet gets 'history_phd' (ancient_topic yes)
when ancient_ruling.verdict(title) is 'history'. Archaeology, philology and history-of-religions titles get no
row and stay needs_review. Prints the counts; --dry-run writes nothing.
"""
import argparse
import csv
import json
from pathlib import Path

from ancient_ruling import verdict

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
FIELDS = ['institution', 'id', 'eligibility', 'ancient_topic', 'basis', 'reviewed_on', 'reviewer', 'note', 'title']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    path = D / 'eligibility-overrides.csv'
    with open(path, newline='', encoding='utf-8') as fh:
        have = {(r['institution'], r['id']) for r in csv.DictReader(fh)}
    counts, rows = {}, []
    for e in json.loads((D / 'doctorates.json').read_text()):
        if e.get('history_scope') != 'classical_school_title' or (e['institution'], e['id']) in have:
            continue
        v = verdict(e.get('title'))
        counts[v] = counts.get(v, 0) + 1
        print(v, '|', (e.get('title') or '')[:100])
        if v == 'history':
            rows.append(dict(institution=e['institution'], id=e['id'], eligibility='history_phd', ancient_topic='yes',
                             basis='ancient-history ruling: Edinburgh classical-antiquity title read as history',
                             reviewed_on='2026-11-17',
                             reviewer='rule ancient_ruling.verdict (user ruling 2026-11-17: "ancient history is history '
                                      'unless it is archeology"); record-level',
                             note='History by title (not archaeology, philology or history of religions)',
                             title=e.get('title') or ''))
    print(json.dumps(counts))
    if not args.dry_run and rows:
        text = path.read_text(encoding='utf-8')
        with open(path, 'a', newline='', encoding='utf-8') as fh:
            if not text.endswith('\n'):
                fh.write('\n')
            csv.DictWriter(fh, fieldnames=FIELDS).writerows(rows)


if __name__ == '__main__':
    main()
