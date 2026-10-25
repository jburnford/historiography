"""Index the separate human reviews without merging people or work counts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALIASES = {
    'space_social_production': 'framework_lefebvre',
    'imperial_jurisdiction': 'hist_benton',
    'us_conservatism_suburbia': 'hist_mcgirr',
}
PACKETS = [
    ('State legibility and resistance', ['framework_scott']),
    ('Social production of space', ['framework_lefebvre']),
    ('Emotions and sensory methods', ['emotions_frameworks', 'corbin_sensory_history']),
    ('Imperial legal pluralism', ['hist_benton']),
    ('Emancipation and Black political life', ['hist_foner', 'hist_berlin', 'hist_kelley']),
    ('Labour, consumer citizenship and reform', ['hist_cohen', 'hist_rodgers']),
    ('Race, gender and immigration law', ['hist_bederman', 'hist_ngai', 'hist_jacobson']),
    ('US suburban conservatism', ['hist_mcgirr']),
    ('Indigenous representation and modernity', ['philip_deloria_modernity']),
    ('Colonial representation and techno-politics', ['pratt_contact_zone', 'timothy_mitchell_expertise']),
    ('Nation-making and commemoration', ['colley_britishness', 'mosse_symbols_bodies_mourning']),
    ('Global Cold War and international order', ['global_cold_war', 'international_order_self_determination']),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    graph_path = ROOT / 'historiography-1920-2000.json'
    graph = json.loads(graph_path.read_text())
    candidates, hashes, seen = {}, {}, set()
    for filename, array in [('frameworks-review.json', 'candidates'),
                            ('historical-review.json', 'candidates'),
                            ('recent-regional-review.json', 'proposals'),
                            ('additional-content-review.json', 'candidates')]:
        path = HERE / filename
        report = json.loads(path.read_text())
        hashes[filename] = digest(path)
        for row in report[array]:
            original = row.get('candidate_id', row.get('id'))
            assert original not in seen, original
            seen.add(original)
            key = ALIASES.get(original, original)
            item = candidates.setdefault(key, {'id': key,
                'label': row.get('label', row.get('title', row.get('candidate'))),
                'status': 'research_candidate_only', 'review_references': [], 'work_ids': []})
            item['review_references'].append({'file': filename, 'candidate_id': original,
                'reviewer_priority': row['priority']})
            works = row.get('work_keys', [w['work_id'] for w in
                row.get('work_leads', row.get('named_work_evidence', []))])
            item['work_ids'] = sorted(set(item['work_ids']) | set(works))
    assert set(ALIASES) <= seen
    assert len(seen) == 41 and len(candidates) == 38
    assert all(key in candidates for _, keys in PACKETS for key in keys)
    packet_ids = {key for _, keys in PACKETS for key in keys}
    individual_path = HERE / 'individual-work-review.json'
    individual = json.loads(individual_path.read_text())
    hashes[individual_path.name] = digest(individual_path)
    assert individual['baseline_graph_sha256'] == digest(graph_path)
    ledger = ROOT / individual['prior_148_decisions_path']
    assert digest(ledger) == individual['prior_148_decisions_sha256_preserved']
    result = {'schema': 'dissertation_canon_review_index/1', 'review_date': '2026-10-24',
        'graph_revision': graph['revision_history'][-1]['version'],
        'graph_sha256': digest(graph_path), 'input_report_sha256': hashes,
        'producer_sha256': digest(Path(__file__)),
        'review_status': 'Local review only; no accepted graph edits or publication.',
        'scope': 'Selective human review of 41 proposals, deduplicated to 38 thematic research candidates. Not exhaustive.',
        'candidate_count': len(candidates),
        'first_research_packets': [{'topic': label, 'candidate_ids': keys} for label, keys in PACKETS],
        'further_research_candidate_ids': sorted(set(candidates) - packet_ids),
        'candidates': list(candidates.values()),
        'individual_work_review': {'file': individual_path.name,
            'decision_counts': individual['decision_counts'],
            'distinct_work_gap_ids': [r['work_id'] for r in individual['results']
                if r['decision'] == 'actual_new_work_gap'],
            'limits': 'Eight missing bibliographic objects are not eight wholly new concepts; collections and component dates need separate research.'},
        'limits': ['No person identity, work edition or citation-count unions are accepted here.',
            'First research packets express editorial sequencing, not a citation-based ranking.',
            'Detailed current coverage, count scopes, primary links and qualifications remain in the referenced reports.']}
    output = HERE / 'reviewed-content-queue.json'
    if output.is_symlink():
        raise ValueError('Refusing symlink output')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f"Indexed {len(seen)} proposals as {len(candidates)} thematic candidates; prior ledger unchanged.")


if __name__ == '__main__':
    main()
