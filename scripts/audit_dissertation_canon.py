"""Screen the frozen dissertation canon against current teaching content.

This produces discovery leads, never accepted identity matches or graph edits.
Release author counts include all credited authorship positions; public person
series count first-author works only. Those populations remain separate.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'
PUBLIC = ROOT / 'data/dissertation-layer/site'


def norm(value):
    # These Latin ligatures do not decompose under NFKD. Folding supplies a
    # display-name/title lead, never an authority decision or ID merge.
    folded = unicodedata.normalize('NFKD', value).casefold().replace('œ', 'oe').replace('æ', 'ae')
    return ''.join(c for c in folded if c.isalnum())


def ordered_name(value):
    if ',' in value:
        surname, given = value.split(',', 1)
        return given.strip() + ' ' + surname.strip()
    return value


def signature(value):
    if ',' in value:
        surname, given = value.split(',', 1)
        first = given.split()[0] if given.split() else ''
    else:
        parts = value.split()
        first, surname = (parts[0], parts[-1]) if len(parts) > 1 else ('', '')
    # Initial-only matches cannot establish even a unique first-name lead.
    return (norm(first), norm(surname)) if len(norm(first)) > 1 and norm(surname) else None


def title_pattern(title):
    main = title.split(':', 1)[0].strip('“”"\' ')
    # A bare generic word is particularly liable to match a different book or
    # ordinary prose. Use its subtitle if available; otherwise retain uncertainty.
    if len(main.split()) < 2 or len(norm(main)) < 8:
        main = title if ':' in title else ''
    return norm(main) if len(norm(main)) >= 8 else ''


class Coverage:
    def __init__(self, graph, links):
        self.people = {p['id']: p for p in graph['people']}
        self.nodes = {n['id']: n for n in graph['nodes']}
        self.sources = {s['id']: s for s in graph['sources']}
        self.exact, self.short, self.direct = defaultdict(list), defaultdict(list), defaultdict(list)
        self.contexts = defaultdict(list)
        self.node_text = {}
        for pid, p in self.people.items():
            self.exact[norm(p['label'])].append(pid)
            if signature(p['label']):
                self.short[signature(p['label'])].append(pid)
            if p.get('node_id') in self.nodes:
                n = self.nodes[p['node_id']]
                self.contexts[pid].append((n['id'], 'individual', self.text(n), n.get('source_ids', [])))
        for pid, row in links.get('people', {}).items():
            self.direct[row['source'][2:]].append(pid)
        for node in graph['nodes']:
            self.node_text[node['id']] = self.text(node)
            for row in node.get('representative_people', []):
                self.contexts[row['person_id']].append((node['id'], 'roster', self.text(row), row.get('source_ids', [])))
            for strand in node.get('strands', []):
                for pid in strand.get('person_ids', []):
                    self.contexts[pid].append((node['id'] + '/' + strand['id'], 'strand', self.text(strand), strand.get('source_ids', [])))
        self.source_text = {sid: norm(s.get('title', '') + ' ' + s.get('citation', '')) for sid, s in self.sources.items()}

    @staticmethod
    def text(row):
        fields = ('label', 'description', 'scope_note', 'representative_figures_and_works',
                  'context', 'works', 'title', 'focus')
        text = ' '.join(row.get(k, '') for k in fields)
        text += ' ' + ' '.join(e['label'] for e in row.get('chronology', {}).get('events', []))
        return norm(text)

    def person(self, key, name):
        if key in self.direct:
            ids, basis = self.direct[key], 'reviewed_teaching_link'
        elif norm(ordered_name(name)) in self.exact:
            ids, basis = self.exact[norm(ordered_name(name))], 'exact_display_name_candidate'
        else:
            ids, basis = self.short.get(signature(name), []), 'first_name_surname_candidate'
        ids = sorted(set(ids))
        if len(ids) != 1:
            status = 'ambiguous_name' if ids else 'no_automatic_match'
        elif self.people[ids[0]].get('node_id'):
            status = 'standalone_candidate'
        elif self.contexts[ids[0]]:
            status = 'roster_or_strand_candidate'
        else:
            status = 'indexed_person_only_candidate'
        risk = bool(re.search(r'\b(department|government|parliament|commission|university|press|canada)\b', name, re.I))
        risk |= not (' ' in ordered_name(name).strip())
        return {'person_key': key, 'name': name, 'match_basis': basis if ids else 'none',
                'coverage_lead': status, 'possible_person_ids': ';'.join(ids),
                'existing_entry_ids': ';'.join(sorted({c[0] for pid in ids for c in self.contexts[pid]})),
                'name_or_corporate_review_needed': bool(risk)}

    def work(self, row, match):
        key = title_pattern(row['title'])
        if not key:
            return {'content_lead': 'generic_title_needs_review', 'matched_contexts': '', 'source_mentions': ''}
        contexts, bibliography = [], []
        # Multiple possible identities cannot supply an author-credited title match.
        ids = match['possible_person_ids'].split(';') if match['possible_person_ids'] else []
        if len(ids) == 1:
            for address, kind, text, sources in self.contexts[ids[0]]:
                if key in text:
                    contexts.append((address, kind))
                bibliography.extend(sid for sid in sources if key in self.source_text.get(sid, ''))
        if contexts:
            status = 'individual_title_mention' if any(kind == 'individual' for _, kind in contexts) else 'roster_or_strand_title_mention'
        elif bibliography:
            status = 'attached_bibliography_only'
        else:
            contexts = [(nid, 'unattributed') for nid, text in self.node_text.items() if key in text]
            bibliography = [sid for sid, text in self.source_text.items() if key in text]
            status = 'unattributed_title_pattern' if contexts else 'source_catalogue_only' if bibliography else 'no_title_pattern_found'
        return {'content_lead': status, 'matched_contexts': ';'.join(sorted({a for a, _ in contexts})),
                'source_mentions': ';'.join(sorted(set(bibliography)))}


def stream(name, release=RELEASE):
    with gzip.open(release / (name + '.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
        yield from csv.DictReader(f)


def public_statistics(index, directory=PUBLIC):
    indexed = {str(s['id']): s['key'] for s in index['sources']}
    result = {}
    for filename in sorted({s['asset'] for s in index['sources']}):
        shard = json.loads((directory / filename).read_text())
        for sid, source in shard['sources'].items():
            result[indexed[sid]] = {'dated_count': source['n'], 'dated_regions': source['n_region'],
                'dated_2000_2009': sum(sum(r) for r in source['series'][3:5]),
                'dated_2015_2026': sum(sum(r) for r in source['series'][6:8])}
    return result


def verify_public_outputs(manifest, directory=PUBLIC):
    """Reject changed input shards before attributing a frozen public count."""
    for filename, expected in manifest['outputs'].items():
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Public count input hash mismatch: ' + filename)


def write_csv(path, rows):
    if path.is_symlink():
        raise ValueError('Refusing symlink output: ' + str(path))
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def validate_destination(path):
    destination = path.resolve()
    for protected in (ROOT / 'docs', ROOT / 'site', PUBLIC, RELEASE):
        if destination == protected or protected in destination.parents:
            raise ValueError('Audit output must stay outside browser assets and the frozen release')
    for filename in ('author-candidates.csv', 'work-candidates.csv', 'audit-summary.json'):
        if (destination / filename).is_symlink():
            raise ValueError('Refusing symlink output: ' + str(destination / filename))
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--min-person-cited', type=int, default=30)
    parser.add_argument('--min-work-cited', type=int, default=20)
    args = parser.parse_args()
    destination = validate_destination(args.out)
    graph_path, links_path, index_path = (ROOT / 'historiography-1920-2000.json',
        ROOT / 'data/dissertation-layer/links.json', PUBLIC / 'index.json')
    graph, links, index = (json.loads(p.read_text()) for p in (graph_path, links_path, index_path))
    manifest_path = ROOT / 'data/dissertation-layer/manifest.json'
    verify_public_outputs(json.loads(manifest_path.read_text()))
    coverage = Coverage(graph, links)
    stats = public_statistics(index)
    public_people = {s['key'][2:] for s in index['sources'] if s['key'].startswith('P:')}
    public_works = {s['key'] for s in index['sources'] if s['key'].startswith('W:')}
    people, matches = [], {}
    for row in stream('people'):
        if int(row['cited_by_dissertations']) < args.min_person_cited and row['person_key'] not in public_people:
            continue
        match = coverage.person(row['person_key'], row['name']); matches[row['person_key']] = match
        stat = stats.get('P:' + row['person_key'], {})
        people.append({**match, 'release_all_credit_dissertations': int(row['cited_by_dissertations']),
            'public_dated_first_author_dissertations': stat.get('dated_count'),
            'public_dated_regions': json.dumps(stat.get('dated_regions'), sort_keys=True),
            'public_first_author_2000_2009': stat.get('dated_2000_2009'),
            'public_first_author_2015_2026': stat.get('dated_2015_2026')})
    works = []
    for row in stream('works'):
        if int(row['cited_by_strict_phds']) < args.min_work_cited and row['work_id'] not in public_works:
            continue
        match = matches.get(row['first_author_key']) or coverage.person(row['first_author_key'], row['first_author'])
        stat = stats.get(row['work_id'], {})
        works.append({'work_id': row['work_id'], 'first_author_key': row['first_author_key'],
            'first_author': row['first_author'], 'title': row['title'], 'corpus_year_unverified': row['year'],
            'parsed_kind': row['kind'], 'release_citing_dissertations': int(row['cited_by_strict_phds']),
            'public_dated_citing_dissertations': stat.get('dated_count'),
            'public_dated_regions': json.dumps(stat.get('dated_regions'), sort_keys=True),
            'public_dated_2000_2009': stat.get('dated_2000_2009'),
            'public_dated_2015_2026': stat.get('dated_2015_2026'),
            'person_coverage_lead': match['coverage_lead'], 'possible_person_ids': match['possible_person_ids'],
            **coverage.work(row, match)})
    people.sort(key=lambda r: (-r['release_all_credit_dissertations'], r['person_key']))
    works.sort(key=lambda r: (-r['release_citing_dissertations'], r['work_id']))
    inputs = [graph_path, links_path, index_path, manifest_path,
              *(RELEASE / (n + '.csv.gz') for n in ('people', 'works', 'dissertations'))]
    summary = {'schema': 'dissertation_canon_coverage_audit/1', 'revision': graph['revision_history'][-1]['version'],
        'release': '2026-10-23', 'sample': index['coverage'],
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'selection': {'min_all_credit_person_dissertations': args.min_person_cited,
            'min_work_dissertations': args.min_work_cited, 'reviewed_public_exceptions_included': True},
        'screened_people': len(people), 'screened_works': len(works),
        'person_leads': dict(Counter(r['coverage_lead'] for r in people)),
        'work_leads': dict(Counter(r['content_lead'] for r in works)),
        'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'count_scopes': {'release_people': 'All credited authorship positions, distinct strict dissertations, including missing years.',
            'public_people': 'First-author work keys only, distinct dated dissertations. Not directly subtractable from all-credit release totals.',
            'works': 'Distinct citing dissertations per existing work ID; raw release includes missing years, public series excludes them.',
            'blank_public_counts': 'No exported public record; not zero citing dissertations.'},
        'limits': ['Identity matches are discovery candidates except separately reviewed teaching links; namesakes and inherited initials remain.',
            'Title-pattern matches establish mentions, not adequate explanation; generic titles are held for review.',
            'No automatic name/title/edition merges, graph edits, influence inference or field membership.',
            'Primary sources, reference tools, corpus parsing problems and content-specific studies can rank highly; human review is required.',
            'Regional/cohort samples differ; public series are context, not a controlled trend or universal canon.']}
    destination.mkdir(parents=True, exist_ok=True)
    validate_destination(destination)
    write_csv(destination / 'author-candidates.csv', people)
    write_csv(destination / 'work-candidates.csv', works)
    (destination / 'audit-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(f"Screened {len(people)} author keys and {len(works)} work IDs against revision {summary['revision']}; discovery leads only.")


if __name__ == '__main__':
    main()
