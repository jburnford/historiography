#!/usr/bin/env python3
"""Stage the official JSTOR title-history export; never import dates or genealogy."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.build_journal_catalogue import normalized_title
from scripts.validate_journal_catalogue import valid_issn

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/journal-catalogue/jstor-title-history'


def stage(rows, catalogue):
    records, by_title, by_issn = defaultdict(list), defaultdict(set), defaultdict(set)
    for number, row in enumerate(rows, 2):
        if not row.get('title_id') or not row.get('publication_title'):
            raise ValueError('Incomplete JSTOR row: ' + str(number))
        records[row['title_id']].append(dict(row_number=number, raw=row))
        by_title[normalized_title(row['publication_title'])].add(row['title_id'])
        for key in ('print_identifier', 'online_identifier'):
            if valid_issn(row[key]):
                by_issn[row[key]].add(row['title_id'])
    # Retain pointers as reported observations, not assertions of succession.
    observations, neighbours = [], defaultdict(set)
    for tid, variants in sorted(records.items()):
        for record in variants:
            row = record['raw']
            for field in ('preceding_publication_title_id', 'parent_publication_title_id'):
                other = row[field]
                if not other:
                    continue
                flags = []
                if other == tid:
                    flags.append('self_reference')
                if other not in records:
                    flags.append('referenced_title_missing')
                else:
                    neighbours[tid].add(other)
                    neighbours[other].add(tid)
                    if field == 'preceding_publication_title_id':
                        first = row['date_first_issue_online']
                        if any(first and r['raw']['date_last_issue_online'] >= first
                               for r in records[other]):
                            flags.append('coverage_overlap_or_reverse_order')
                observations.append(dict(title_id=tid, field=field, reported_value=other,
                                         row_number=record['row_number'], flags=flags,
                                         status='unverified_relationship'))
    components, family_for, visited = [], {}, set()
    for tid in sorted(records):
        if tid in visited:
            continue
        todo, members = [tid], set()
        while todo:
            current = todo.pop()
            if current in members:
                continue
            members.add(current)
            todo.extend(neighbours[current] - members)
        visited.update(members)
        family = 'jstor_family_' + hashlib.sha256('|'.join(sorted(members)).encode()).hexdigest()[:16]
        components.append(dict(id=family, title_ids=sorted(members),
                               interpretation='Connected reported references; no directed genealogy inferred.'))
        family_for.update({t: family for t in members})
    matches = []
    for node in catalogue['nodes']:
        if node['entry_kind'] != 'periodical':
            continue
        titles, identifiers = set(), set()
        for title in [node['label'], *node.get('aliases', [])]:
            titles.update(by_title.get(normalized_title(title), set()))
        for issn in node.get('issns', []):
            identifiers.update(by_issn.get(issn, set()))
        concordant = titles & identifiers
        status = ('unique_title_and_issn_candidate' if len(concordant) == 1
                  and titles == identifiers else 'identity_conflict_or_multiple_candidates'
                  if (titles and identifiers and titles != identifiers) or len(titles | identifiers) > 1
                  else 'issn_only_candidate' if identifiers else 'title_only_candidate'
                  if titles else 'no_match')
        matches.append(dict(journal_id=node['id'], label=node['label'], status=status,
                            title_match_ids=sorted(titles), issn_match_ids=sorted(identifiers),
                            candidate_family_ids=sorted({family_for[t] for t in titles | identifiers})))
    return dict(raw_rows=len(rows), distinct_title_ids=len(records),
                duplicate_or_multiple_coverage_rows=len(rows)-len(records),
                records=dict(sorted(records.items())), relationship_observations=observations,
                reported_reference_families=components, catalogue_matches=matches,
                match_counts=dict(Counter(m['status'] for m in matches)),
                relationship_flags=dict(Counter(f for o in observations for f in o['flags'])),
                policy='Staging only. Coverage dates are not publication lifespans. Identifier/title matches are candidates. Reported pointers may serialize a family rather than encode true predecessor relations. No founding or other atlas edges inferred.')


def main():
    raw_path = DATA / 'complete-title-history-2026-09-16.tsv'
    baseline = ROOT / 'drafts/historiography-1920-2000.v1.113.json'
    raw = raw_path.read_bytes()
    with raw_path.open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source, delimiter='\t'))
    graph = json.loads(baseline.read_text())
    result = stage(rows, graph['journal_catalogue'])
    result['provenance'] = dict(
        retrieved_on='2026-09-16',
        source_url='https://www.jstor.org/kbart/collections/all-archive-titles?contentType=journals',
        discovery_url='https://support.jstor.org/hc/en-us/articles/115007466248-JSTOR-Title-Lists',
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
        catalogue_revision='1.113', baseline=str(baseline.relative_to(ROOT)),
        baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest())
    (DATA / 'staged.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    summary = {k: v for k, v in result.items() if k not in (
        'records', 'relationship_observations', 'reported_reference_families', 'catalogue_matches')}
    (DATA / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
