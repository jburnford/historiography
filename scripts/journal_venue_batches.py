"""Apply reviewed venue claims after immutable bibliographic imports."""
import copy
import hashlib
import json
from pathlib import Path
import re

try:
    from .journal_metadata_batches import fingerprint
except ImportError:
    from journal_metadata_batches import fingerprint


def merge_venues(catalogue, batch):
    result = copy.deepcopy(catalogue)
    nodes = {n['id']: n for n in result['nodes']}
    sources = {s['id']: s for s in result['sources']}
    for source in batch['sources']:
        if source['id'] in sources:
            raise ValueError('Venue source already exists: ' + source['id'])
        sources[source['id']] = copy.deepcopy(source)
    expected = batch['expected_node_fingerprints']
    if set(expected) != {e['source'] for e in batch['edges']}:
        raise ValueError('Every founding journal needs a reviewed fingerprint')
    for jid, value in expected.items():
        node = nodes.get(jid, {})
        if (node.get('entry_kind') != 'periodical'
                or node.get('publication_role') == 'primary_source_periodical'
                or fingerprint(node) != value):
            raise ValueError('Founding journal changed or is not a research venue: ' + jid)
    for jid, check in batch.get('publication_start_checks', {}).items():
        node = nodes.get(jid, {})
        year, refs = check.get('year'), check.get('source_ids', [])
        if (jid not in expected or node.get('publication_start') is not None
                or node.get('publication_end') is not None or node.get('date_span')
                or node.get('publication_status') != 'unknown'):
            raise ValueError('Founding date check may only fill wholly unknown chronology')
        if (type(year) is not int or not 1 <= year <= 2000
                or not check.get('note') or not refs
                or any(s not in sources for s in refs)):
            raise ValueError('Founding date check needs a sourced, in-scope publication year')
        node['publication_start'] = year
        node['date_span'] = dict(start=year, end=None, precision='year',
                                start_kind='publication_start', end_kind='unknown',
                                open_end=None, basis='source_check', source_ids=list(refs))
        node['chronology_note'] = check['note']
        node['source_ids'] = list(dict.fromkeys([*node['source_ids'], *refs]))
    ids = {e['id'] for e in result['edges']}
    triples = {(e['source'], e['target'], e['relationship_kind']) for e in result['edges']}
    for edge in batch['edges']:
        key = (edge['source'], edge['target'], edge['relationship_kind'])
        if edge['id'] in ids or key in triples:
            raise ValueError('Duplicate venue claim')
        ids.add(edge['id'])
        triples.add(key)
        span = edge.get('temporal_scope', {})
        year = span.get('start')
        if (edge['relationship_kind'] != 'founded_for'
                or edge.get('basis') not in ('sourced_founding_programme', 'primary_founding_editorial')
                or edge.get('directed') is not True
                or not edge.get('relationship') or not edge.get('evidence_note')
                or type(year) is not int or year > 2000
                or span.get('end') != year or span.get('precision') != 'year'
                or year != nodes[edge['source']].get('publication_start')):
            raise ValueError('Founding claim needs a programme and a matching in-scope year')
        refs = edge.get('source_ids', [])
        if not refs or any(s not in sources for s in refs):
            raise ValueError('Unknown founding source')
        node = nodes[edge['source']]
        # Existing dates, identity, subjects and bibliographic evidence are protected.
        node['publication_role'] = 'research_journal'
        node['source_ids'] = list(dict.fromkeys([*node['source_ids'], *refs]))
        result['edges'].append(copy.deepcopy(edge))
    result['sources'] = list(sources.values())
    return result


def apply_accepted_venues(catalogue, directory):
    directory = Path(directory)
    manifest = directory / 'accepted-venue-batches.json'
    if not manifest.exists():
        return catalogue
    result, seen = catalogue, set()
    for entry in json.loads(manifest.read_text())['batches']:
        name = entry['filename']
        if not re.fullmatch(r'founding-\d{3}\.json', name) or name in seen:
            raise ValueError('Invalid or repeated venue batch filename')
        seen.add(name)
        raw = (directory / 'venue-batches' / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Accepted venue batch changed: ' + name)
        batch = json.loads(raw)
        if batch.get('operation') == 'venue_correction':
            result = correct_venues(result, batch)
        else:
            result = merge_venues(result, batch)
    return result


def correct_venues(catalogue, batch):
    """Apply an explicit, hash-pinned editorial correction without erasing its evidence."""
    if fingerprint(catalogue) != batch['expected_catalogue_fingerprint']:
        raise ValueError('Venue correction baseline changed')
    result = copy.deepcopy(catalogue)
    previous = {e['id']: e for e in result['edges']}
    removed = set()
    for withdrawal in batch['withdrawals']:
        edge = withdrawal['edge']
        if (edge['id'] in removed or previous.get(edge['id']) != edge
                or edge.get('relationship_kind') != 'founded_for'
                or not withdrawal.get('reason')
                or withdrawal.get('decision') not in ('rejected', 'withheld_pending_evidence')):
            raise ValueError('Withdrawal needs an exact founding claim and editorial decision')
        removed.add(edge['id'])
    result['edges'] = [e for e in result['edges'] if e['id'] not in removed]
    for correction in batch.get('source_corrections', []):
        old, new = correction['before'], correction['after']
        if old['id'] != new['id'] or old not in result['sources'] or not correction.get('reason'):
            raise ValueError('Source correction requires the exact prior record and stable ID')
        result['sources'][result['sources'].index(old)] = copy.deepcopy(new)
    for key in ('sources', 'nodes', 'edges', 'title_relationships', 'subject_classifications'):
        existing = {r['id'] for r in result[key]}
        if key == 'edges':
            existing.update(previous)  # Withdrawn IDs must never acquire a different meaning.
        for record in batch.get('added_' + key, []):
            if record['id'] in existing:
                raise ValueError('Correction cannot replace an existing record: ' + record['id'])
            existing.add(record['id'])
            result[key].append(copy.deepcopy(record))
    nodes = {n['id']: n for n in result['nodes']}
    sources = {s['id'] for s in result['sources']}
    reviewed = set()
    for check in batch.get('research_venue_checks', []):
        jid = check['journal_id']
        node = nodes.get(jid, {})
        refs = check.get('source_ids', [])
        if (jid in reviewed or node.get('entry_kind') != 'periodical'
                or node.get('publication_role') not in ('periodical_candidate', 'research_journal')
                or fingerprint(node) != check.get('expected_node_fingerprint')
                or not check.get('reason') or not refs or any(s not in sources for s in refs)
                or not any(e['source'] == jid for e in batch.get('added_edges', []))):
            raise ValueError('Research venue check needs an unchanged eligible journal, evidence and an added edge')
        reviewed.add(jid)
        # A venue review cannot alter identity, chronology, bibliography or subjects.
        node['publication_role'] = 'research_journal'
        node['source_ids'] = list(dict.fromkeys([*node['source_ids'], *refs]))
    return result
