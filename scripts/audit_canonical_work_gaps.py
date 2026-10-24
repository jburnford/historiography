"""Find cited-work candidates missing from individual teaching entries.

Reads the frozen public release, not the large research graph. Name matches are
review leads only; reviewed teaching links take precedence. Counts are distinct
dissertations per existing work record, never summed across possible editions.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text).casefold() if c.isalnum())


def title_key(title):
    # Compare the main title, retaining subtitles in the output. Generic very
    # short strings cannot establish that a work is represented.
    main = title.split(':', 1)[0].strip('“”"\' ')
    key = norm(main)
    if len(key) < 8 and ':' in title:
        key = norm(title)  # e.g. Gender: A Useful Category…, Hunger: A Modern History
    return key if len(key) >= 8 else ''


def represented(title, text):
    key = title_key(title)
    return bool(key and key in norm(text))


def name_parts(label, inverted=False):
    if inverted:
        parts = label.split(',', 1)
        return (norm(parts[1].split()[0]), norm(parts[0])) if len(parts) == 2 and parts[1].split() else None
    parts = label.split()
    return (norm(parts[0]), norm(parts[-1])) if len(parts) >= 2 else None


def audit(graph, index, links, release, minimum=10):
    people = {p['id']: p for p in graph['people']}
    sources = {s['id']: s for s in graph['sources']}
    by_key = {s['key']: s for s in index['sources']}
    names = {}
    for s in index['sources']:
        if s['key'].startswith('P:'):
            names.setdefault(name_parts(s['short'], True), []).append(s['key'])
    matched = []
    targets = {}
    for node in graph['nodes']:
        if node.get('entry_kind') != 'person':
            continue
        pid = next((p['id'] for p in graph['people'] if p.get('node_id') == node['id']), node['id'])
        direct = links['people'].get(pid)
        candidates = [direct['source']] if direct else names.get(name_parts(people.get(pid, node)['label']), [])
        row = {'node_id': node['id'], 'person_id': pid, 'label': node['label'],
               'basis': 'reviewed_named_works' if direct else 'unique_first_surname_candidate' if len(candidates) == 1 else 'ambiguous_name' if candidates else 'no_match',
               'source_key': candidates[0] if len(candidates) == 1 else '', 'candidates': ';'.join(candidates)}
        matched.append(row)
        if len(candidates) == 1:
            targets[candidates[0][2:]] = (node, row)
    candidates = []
    with gzip.open(release / 'works.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        for work in csv.DictReader(f):
            if work['first_author_key'] not in targets or int(work['cited_by_strict_phds']) < minimum:
                continue
            node, match = targets[work['first_author_key']]
            reading = node.get('representative_figures_and_works', '')
            chronology = ' '.join(e['label'] for e in node.get('chronology', {}).get('events', []))
            bibliography = ' '.join(sources[s].get('title', '') + ' ' + sources[s].get('citation', '') for s in node.get('source_ids', []) if s in sources)
            in_reading = represented(work['title'], reading)
            in_chronology = represented(work['title'], chronology)
            in_sources = represented(work['title'], bibliography)
            if in_reading and in_chronology:
                continue
            candidates.append({'node_id': node['id'], 'person': node['label'], 'match_basis': match['basis'],
                'person_key': work['first_author_key'], 'work_id': work['work_id'], 'title': work['title'],
                'corpus_year_unverified': work['year'], 'citing_dissertations': int(work['cited_by_strict_phds']),
                'in_selected_readings': in_reading, 'on_timeline': in_chronology, 'in_entry_sources': in_sources,
                'review_status': 'candidate_requires_identity_title_edition_review'})
    candidates.sort(key=lambda r: (-r['citing_dissertations'], r['node_id'], r['work_id']))
    return matched, candidates


def validate_review(ledger, graph):
    """Check an explicit review against its frozen queue and current graph.

    Title heuristics cannot establish translations, edition dates or authorship.
    A decision must preserve its input row and name its canonical facts/sources.
    """
    queue = ROOT / ledger['queue']
    if hashlib.sha256(queue.read_bytes()).hexdigest() != ledger['queue_sha256']:
        raise ValueError('Reviewed candidate queue changed')
    with queue.open(newline='', encoding='utf-8') as f:
        original = list(csv.DictReader(f))
    reviews = ledger['reviews']
    if len(reviews) != len(original):
        raise ValueError('Every candidate needs one review')
    nodes = {n['id']: n for n in graph['nodes']}
    sources = {s['id'] for s in graph['sources']}
    decisions = {}
    outcomes = {'added_work', 'expanded_existing', 'already_represented', 'translation_or_edition', 'unresolved'}
    for i, (prior, decision) in enumerate(zip(original, reviews), 1):
        if decision['candidate'] != i or any(decision.get(k) != v for k, v in prior.items()):
            raise ValueError('Candidate row changed or reordered')
        key = (decision['node_id'], decision['work_id'])
        if key in decisions or decision['outcome'] not in outcomes or not decision['rationale'].strip():
            raise ValueError('Duplicate or incomplete review')
        node = nodes[decision['node_id']]
        event_ids = {e['id'] for e in node['chronology']['events']}
        if decision['outcome'] != 'unresolved' and (not decision['canonical_event_ids'] or not decision['source_ids']):
            raise ValueError('Resolved candidate needs a dated fact and evidence')
        if not set(decision['canonical_event_ids']) <= event_ids or not set(decision['source_ids']) <= sources:
            raise ValueError('Review points to missing facts or sources')
        decisions[key] = decision
    reviewed_nodes = {r['node_id'] for r in reviews}
    relationships = ledger['relationship_review']
    if len(relationships) != len(reviewed_nodes) or {r['node_id'] for r in relationships} != reviewed_nodes:
        raise ValueError('Every individual needs a relationship review')
    return decisions


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--graph', type=Path, default=ROOT / 'historiography-1920-2000.json')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min-cited', type=int, default=10)
    ap.add_argument('--review-ledger', type=Path, help='Apply explicit decisions to their frozen queue; retain unresolved and new leads')
    args = ap.parse_args()
    index_path = ROOT / 'data/dissertation-layer/site/index.json'
    link_path = ROOT / 'data/dissertation-layer/links.json'
    graph = json.loads(args.graph.read_text())
    matched, candidates = audit(graph, json.loads(index_path.read_text()),
                                json.loads(link_path.read_text()), RELEASE, args.min_cited)
    raw_count = len(candidates)
    ledger = None
    if args.review_ledger:
        ledger = json.loads(args.review_ledger.read_text())
        decisions = validate_review(ledger, graph)
        candidates = [r for r in candidates if (r['node_id'], r['work_id']) not in decisions
                      or decisions[(r['node_id'], r['work_id'])]['outcome'] == 'unresolved']
    args.out.mkdir(parents=True, exist_ok=True)
    fields = ['node_id','person','match_basis','person_key','work_id','title','corpus_year_unverified',
              'citing_dissertations','in_selected_readings','on_timeline','in_entry_sources','review_status']
    for name, rows_, keys in [('candidates.csv', candidates, fields), ('matches.csv', matched, list(matched[0]))]:
        with (args.out / name).open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader(); w.writerows(rows_)
    summary = {'minimum_citing_dissertations': args.min_cited, 'individual_entries': len(matched),
        'matched_for_review': sum(bool(r['source_key']) for r in matched), 'work_candidates': len(candidates),
        'revision': json.loads(args.graph.read_text())['revision_history'][-1]['version'],
        'input_sha256': {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (args.graph, index_path, link_path, RELEASE / 'works.csv.gz')},
        'limits': 'Discovery queue, not accepted identities or a universal canon. Title matching can miss translations and alternate titles; corpus dates need bibliographic checking. Counts are per work record, not sums over title variants.'}
    if ledger:
        summary.update(raw_title_flags=raw_count, reviewed_candidates=len(decisions),
                       unresolved_review_records=sum(d['outcome'] == 'unresolved' for d in decisions.values()),
                       review_ledger=str(args.review_ledger.relative_to(ROOT)) if args.review_ledger.is_relative_to(ROOT) else str(args.review_ledger),
                       review_sha256=hashlib.sha256(args.review_ledger.read_bytes()).hexdigest())
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f"{len(matched)} individual entries; {summary['matched_for_review']} matches for review; {len(candidates)} work/chronology candidates.")


if __name__ == '__main__':
    main()
