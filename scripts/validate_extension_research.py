"""Validate staging references and evidence scopes without changing the graph."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/extension-2026'


def validate():
    errors = []
    graph_path = ROOT / 'historiography-1920-2000.json'
    graph = json.loads(graph_path.read_text())
    baseline = json.loads((DATA / 'baseline.json').read_text())
    nodes = {n['id']: n for n in graph['nodes']}
    people = {p['id'] for p in graph['people']}
    sources = {s['id'] for s in graph['sources']}
    fields = json.loads((DATA / 'field-candidates.json').read_text())
    candidates = {f['candidate_id'] for f in fields}
    topics = json.loads((DATA / 'existing-topics.json').read_text())
    expected = {n['id'] for n in graph['nodes'] if n['entry_kind'] == 'group'}
    if len(topics) != len(expected) or {r['entry_id'] for r in topics} != expected:
        errors.append('Existing-topic ledger does not match the complete baseline topic set.')
    if len(candidates) != len(fields):
        errors.append('Duplicate candidate IDs.')
    seed_table = (ROOT / 'FIELD-DISCOVERY-2026.md').read_text().split(
        '## Initial candidate queue')[1].split('## Checked starting sources')[0]
    seed_rows = [line for line in seed_table.splitlines() if line.startswith('|')][2:]
    expected_seed_labels = {line.split('|')[1].strip() for line in seed_rows}
    actual_seed_labels = [f['label'] for f in fields if f['discovery_route'] == 'user_seed']
    if set(actual_seed_labels) != expected_seed_labels or len(actual_seed_labels) != len(seed_rows):
        errors.append('User seed queue differs from the documented discovery list.')
    if any(f['production_status'] != 'not_added' for f in fields):
        errors.append('Research candidate presented as a production addition.')
    if hashlib.sha256(graph_path.read_bytes()).hexdigest() != baseline['graph_sha256']:
        errors.append('Authoritative graph differs from research baseline.')
    for path, digest in baseline['browser_asset_hashes'].items():
        p = ROOT / path
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            errors.append(f'Browser asset changed: {path}')

    packets = [json.loads((DATA / name).read_text())
               for name in ['pilot-evidence.json', 'capitalism-evidence.json']]
    works, publications, claims, citations = {}, {}, {}, {}
    for packet in packets:
        if packet['production_graph_imports'] != 0 or packet['status'] != 'staging_only':
            errors.append('Packet is not explicitly staging-only.')
        for name, index in [('works', works), ('publications', publications),
                            ('claims', claims), ('citations', citations)]:
            for record in packet[name]:
                if record['id'] in index:
                    errors.append(f'Duplicate {name} ID: {record["id"]}')
                index[record['id']] = record
    for w in works.values():
        for source in w.get('legacy_source_ids', []):
            if source not in sources:
                errors.append(f'Unknown legacy source: {source}')
    for p in publications.values():
        if p['work_id'] not in works:
            errors.append(f'Unknown publication work: {p["id"]}')
        for capture in p.get('captures', []):
            if not (DATA / capture).is_file():
                errors.append(f'Missing capture: {capture}')
        for path_key, hash_key in [('path', 'sha256'), ('original_pdf', 'original_pdf_sha256')]:
            if path_key in p:
                path = Path(p[path_key])
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != p[hash_key]:
                    errors.append(f'Changed source witness: {p[path_key]}')
    for c in claims.values():
        if c['editorial_state'] != 'proposed' or not c.get('history'):
            errors.append(f'Claim missing proposal history: {c["id"]}')
        if c['intervention_year'] > 2026:
            errors.append(f'Future intervention: {c["id"]}')
        for key in ['actor', 'target']:
            ref = c[key]
            kind = ref['kind']
            if kind == 'strand':
                node = nodes.get(ref['entry_id'], {})
                valid = ref['strand_id'] in {s['id'] for s in node.get('strands', [])}
            else:
                valid = ref.get('id') in {'work': works, 'candidate': candidates,
                                         'person': people, 'entry': nodes}.get(kind, {})
            if not valid:
                errors.append(f'Unresolved {key}: {c["id"]}: {ref}')
        if not any(e['claim_id'] == c['id'] for e in citations.values()):
            errors.append(f'No scoped evidence record: {c["id"]}')
    for e in citations.values():
        if e['claim_id'] not in claims or e['publication_id'] not in publications:
            errors.append(f'Broken citation join: {e["id"]}')
        if not e.get('locator') or not e.get('limitation') or not e.get('checked_on'):
            errors.append(f'Incomplete check scope: {e["id"]}')
        if e['check_status'] not in {'passage_checked', 'abstract_checked', 'metadata_checked'}:
            errors.append(f'Unknown check status: {e["id"]}')
        if e['check_status'] == 'metadata_checked' and e['support_assessment'] != 'not_established':
            errors.append(f'Metadata promoted to substantive support: {e["id"]}')
        locator = e['locator']
        pub = publications.get(e['publication_id'], {})
        if isinstance(locator, dict) and pub.get('path'):
            total = len(Path(pub['path']).read_text().split('\n'))
            if not 1 <= locator['line_start'] <= locator['line_end'] <= total:
                errors.append(f'Invalid local line locator: {e["id"]}')
    for field in fields:
        if set(field.get('evidence_claim_ids', [])) - claims.keys():
            errors.append(f'Unknown candidate evidence: {field["candidate_id"]}')
    return {'errors': errors, 'existing_topics': len(topics), 'field_candidates': len(fields),
            'user_seed_candidates': sum(f['discovery_route'] == 'user_seed' for f in fields),
            'works': len(works), 'publications': len(publications), 'claim_proposals': len(claims),
            'citation_checks': len(citations),
            'substantive_support_checks': sum(e['check_status'] != 'metadata_checked' for e in citations.values()),
            'production_graph_imports': 0, 'fully_reviewed_topics': sum(r['review_outcome'] != 'pending' for r in topics)}


if __name__ == '__main__':
    report = validate()
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['errors']))
