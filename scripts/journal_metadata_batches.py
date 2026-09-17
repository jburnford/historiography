"""Apply hash-pinned, reviewed bibliographic additions without replacing better data."""
import copy
import hashlib
import json
from pathlib import Path
import re


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def merge_metadata(catalogue, batch):
    result = copy.deepcopy(catalogue)
    nodes = {n['id']: n for n in result['nodes']}
    sources = {s['id']: s for s in result['sources']}
    for source in batch['sources']:
        if source['id'] in sources and sources[source['id']] != source:
            raise ValueError('Conflicting bibliographic source')
        sources[source['id']] = copy.deepcopy(source)
    seen = set()
    for update in batch['updates']:
        jid = update['journal_id']
        if jid in seen or jid not in nodes or nodes[jid]['entry_kind'] != 'periodical':
            raise ValueError('Invalid or repeated metadata journal')
        seen.add(jid)
        node = nodes[jid]
        if fingerprint(node) != update['expected_node_fingerprint']:
            raise ValueError('Journal changed since metadata review: ' + jid)
        if node.get('identity_status') == 'ambiguous_title':
            raise ValueError('Ambiguous catalogue identities require separate resolution')
        fields = update['fields']
        if set(fields) - {'issns', 'languages', 'identity_status', 'publication_start', 'date_span',
                          'chronology_note', 'bibliographic_evidence'}:
            raise ValueError('Unapproved metadata field')
        for key in ('issns', 'languages'):
            if key in fields and node.get(key):
                raise ValueError('Existing metadata must be preserved: ' + key)
        if 'date_span' in fields:
            if node.get('date_span') or node.get('publication_start') is not None or node.get('publication_end') is not None:
                raise ValueError('Existing chronology must be preserved')
            span = fields['date_span']
            if (span.get('start_kind') != 'catalogued_title_start' or span.get('end') is not None
                    or span.get('end_kind') != 'unknown' or span.get('open_end') is not None
                    or fields.get('publication_start') != span.get('start')):
                raise ValueError('Library dates must retain title-level and unknown-end semantics')
        elif 'publication_start' in fields or 'chronology_note' in fields:
            raise ValueError('Publication chronology requires an evidenced span')
        if 'identity_status' in fields and (node.get('identity_status') != 'title_matched_candidate'
                or fields['identity_status'] != 'bibliographic_metadata_checked'):
            raise ValueError('Existing identity qualifications must be preserved')
        if node.get('bibliographic_evidence'):
            raise ValueError('Existing bibliographic evidence must be preserved')
        if not update['source_ids'] or any(s not in sources for s in update['source_ids']):
            raise ValueError('Metadata needs known source references')
        node.update(copy.deepcopy(fields))
        node['source_ids'] = list(dict.fromkeys([*node['source_ids'], *update['source_ids']]))
    result['sources'] = list(sources.values())
    result['schema_version'] = '1.3'
    result['metadata_reviewed_on'] = batch.get('checked_on')
    return result


def apply_accepted_metadata(catalogue, directory):
    directory = Path(directory)
    path = directory / 'accepted-metadata-batches.json'
    if not path.exists():
        return catalogue
    result = catalogue
    seen = set()
    for entry in json.loads(path.read_text())['batches']:
        name = entry['filename']
        if not re.fullmatch(r'root-library-\d{3}\.json', name) or name in seen:
            raise ValueError('Invalid or repeated metadata batch filename')
        seen.add(name)
        raw = (directory / 'metadata-batches' / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Accepted metadata batch changed: ' + name)
        result = merge_metadata(result, json.loads(raw))
    return result
