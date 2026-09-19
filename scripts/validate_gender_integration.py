#!/usr/bin/env python3
"""Check the bounded LOD/editorial integration batch, never export it."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate import validate as validate_contract

BASE = ROOT / 'data/extension-2026/gender-integration'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data=None):
    data = read(BASE / 'batch.json') if data is None else data
    errors = validate_contract(data, read(ROOT / 'ontology/contract.json'), ROOT)
    if data.get('fixture_only') is not True or data.get('status') != 'staging_only' or data.get('production_graph_imports') != 0:
        errors.append('Batch must remain explicitly staging-only and blocked from production.')
    for row in data['claims']:
        if row['review']['status'] != 'needs_review':
            errors.append(f'{row["id"]}: this batch has no production acceptance decisions')
        for ev in row['evidence']:
            if not all(ev.get(k) for k in ['check_status', 'checked_on', 'limitation']):
                errors.append(f'{row["id"]}: missing citation check scope')
            if ev.get('check_status') == 'passage_checked' and ev.get('scope') != 'passage':
                errors.append(f'{row["id"]}: passage check cannot stand for a metadata or abstract check')
    for mapping in data['identity_mappings']:
        if mapping['review']['status'] != 'needs_review':
            errors.append('External authority links have not been accepted in this batch.')
    for source in data['source_records']:
        path = (ROOT / source['snapshot_path']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or sha(path) != source.get('snapshot_sha256'):
            errors.append(f'{source["id"]}: missing or changed source snapshot')

    baseline = read(ROOT / 'data/extension-2026/baseline.json')
    if sha(ROOT / baseline['graph_path']) != baseline['graph_sha256']:
        errors.append('Authoritative graph changed from the extension baseline.')
    for path, expected in baseline['browser_asset_hashes'].items():
        if sha(ROOT / path) != expected:
            errors.append(f'Browser asset changed: {path}')
    graph = read(ROOT / baseline['graph_path'])
    entities = {e['id']: e for e in data['entities']}
    for e in entities.values():
        if e.get('legacy_id'):
            collection = graph['people'] if e['type'] == 'person' else graph['nodes']
            original = next((r for r in collection if r['id'] == e['legacy_id']), None)
            if not original or original['label'] != e['label']:
                errors.append(f'{e["id"]}: legacy identity/label not preserved')
    candidates = {r['candidate_id'] for r in read(ROOT / 'data/extension-2026/field-candidates.json')}
    for e in entities.values():
        if e.get('candidate_ledger_id') and e['candidate_ledger_id'] not in candidates:
            errors.append(f'{e["id"]}: unknown discovery candidate')

    lod = ROOT / 'data/lod-mining/2026-09-18-pilot-complete'
    records = {r['uri']: r for r in read(lod / 'bibliographic-resources.json')}
    reviewed = data['record_reviews']
    if len({r['record_uri'] for r in reviewed}) != len(reviewed):
        errors.append('Duplicate catalogue review.')
    sources = {r['id'] for r in data['source_records']}
    for row in reviewed:
        if row['raw_record'] != records.get(row['record_uri']):
            errors.append(f'{row["record_uri"]}: original catalogue evidence changed')
        if row.get('work_candidate_id') and entities.get(row['work_candidate_id'], {}).get('type') != 'work':
            errors.append('Record review points to an unknown work.')
        if not row.get('evidence') or any(e.get('source_record_id') not in sources for e in row['evidence']):
            errors.append('Record review requires known evidence.')

    crosswalk = read(BASE / 'schema-crosswalk.json')
    for packet in crosswalk['input_packets']:
        path = ROOT / packet['path']
        if sha(path) != packet['sha256']:
            errors.append(f'Prior research packet changed: {packet["path"]}')
        original = read(path)
        for collection, mapping in [('works', 'work_mappings'), ('publications', 'publication_mappings'), ('claims', 'claim_mappings')]:
            rows = [r for r in crosswalk[mapping] if r['input_packet'] == path.name]
            if Counter(r['legacy_id'] for r in rows) != Counter(r['id'] for r in original[collection]):
                errors.append(f'{path.name}: incomplete or duplicate {collection} mapping audit')
        for row in (r for r in crosswalk['claim_mappings'] if r['input_packet'] == path.name):
            c = next(c for c in original['claims'] if c['id'] == row['legacy_id'])
            expected_citations = [e['id'] for e in original['citations'] if e['claim_id'] == c['id']]
            if row['actor'] != c['actor'] or row['target'] != c['target'] or row['predicate'] != c['kind'] or row['input_citation_ids'] != expected_citations:
                errors.append(f'{c["id"]}: mapping audit lost claim participants or evidence joins')
    manifest_path = BASE / 'manifest.json'
    if manifest_path.exists():
        for path, expected in read(manifest_path)['file_hashes'].items():
            actual = ROOT / path
            if not actual.is_file() or sha(actual) != expected:
                errors.append(f'Integration manifest mismatch: {path}')
    return {'errors': errors, 'entities_by_type': dict(Counter(e['type'] for e in entities.values())),
            'claim_proposals': len(data['claims']),
            'interpretive_proposals': sum(c['basis'] == 'editorial_interpretation' for c in data['claims']),
            'reviewed_catalogue_records': len(reviewed),
            'authority_mappings_pending': len(data['identity_mappings']),
            'older_claims_preserved_pending_predicate_design': len(crosswalk['claim_mappings']),
            'production_graph_imports': 0}


if __name__ == '__main__':
    report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report['errors']))
