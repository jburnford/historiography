#!/usr/bin/env python3
"""Audit the accepted 1.111 library pass against its preserved 1.110 snapshot."""
import hashlib
import json
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue, make_audit
    from .journal_metadata_batches import merge_metadata
    from .journal_subject_batches import merge_source_check
    from .validate_journal_catalogue import validate_catalogue
except ImportError:
    from build_journal_catalogue import make_catalogue, make_audit
    from journal_metadata_batches import merge_metadata
    from journal_subject_batches import merge_source_check
    from validate_journal_catalogue import validate_catalogue

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/journal-catalogue'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    before_path = ROOT/'drafts/historiography-1920-2000.v1.110.json'
    before = read(before_path)
    graph = read(ROOT/'historiography-1920-2000.json')
    catalogue = read(DATA/'catalogue.json')
    if graph['revision_history'][-1]['version'] != '1.111':
        raise ValueError('This audit targets revision 1.111; use its saved report for later revisions')
    for key in before:
        if key not in ('journal_catalogue', 'revision_history'):
            assert before[key] == graph[key], 'Historical graph changed: '+key
    assert set(before) == set(graph)
    assert graph['revision_history'][:-1] == before['revision_history']
    subject = read(DATA/'source-check-batches/root-web-005.json')
    metadata = read(DATA/'metadata-batches/root-library-001.json')
    review = read(ROOT/'feedback/journals/library-integration-v1.111-review.json')
    accepted = read(DATA/'accepted-metadata-batches.json')
    assert sha(ROOT/accepted['review_report']) == accepted['review_sha256']
    assert sha(DATA/'metadata-batches/library-subject-mapping-001.json') == accepted['subject_mapping_sha256']
    expected = merge_metadata(merge_source_check(before['journal_catalogue'], subject), metadata)
    assert catalogue == graph['journal_catalogue'] == expected == make_catalogue()
    assert not validate_catalogue(catalogue, graph['nodes'])
    old = before['journal_catalogue']
    for key in ('edges', 'title_relationships', 'discovery_resources'):
        assert old[key] == catalogue[key]
    old_nodes = {n['id']:n for n in old['nodes']}
    nodes = {n['id']:n for n in catalogue['nodes']}
    assert set(old_nodes) == set(nodes)
    for jid, n in old_nodes.items():
        if n['entry_kind'] == 'periodical':
            for key in ('label', 'aliases', 'occurrences', 'publication_role', 'urls', 'publication_end', 'publication_status', 'publisher_country'):
                assert n.get(key) == nodes[jid].get(key), (jid, key)
            if n.get('date_span') or n.get('publication_start') is not None or n.get('publication_end') is not None:
                for key in ('date_span', 'publication_start', 'publication_end', 'chronology_note'):
                    assert n.get(key) == nodes[jid].get(key), (jid, key)
    sources = {s['id']:s for s in catalogue['sources']}
    assert all(sources[s['id']] == s for s in old['sources'])
    active = {r['id']:r for r in catalogue['subject_classifications']}
    archived = {r['id']:r for r in catalogue.get('superseded_subject_classifications', [])}
    for row in old['subject_classifications']:
        if row['id'] in active:
            assert row == active[row['id']]
        else:
            assert row['status'] == 'provisional'
            assert row == {k:v for k,v in archived[row['id']].items() if k not in ('superseded_by_batch', 'superseded_on')}
    for path, digest in {**review['stage_sha256'], **review['used_raw_sha256']}.items():
        assert sha(ROOT/path) == digest, 'Saved research changed: '+path
    counts = make_audit(catalogue)
    journals = [n for n in catalogue['nodes'] if n['entry_kind'] == 'periodical']
    checked = {r['journal_id'] for r in catalogue['subject_classifications'] if r.get('status', 'checked') == 'checked'}
    profiles = {n['id'] for n in journals if n.get('bibliographic_evidence')}
    exceptions = []
    for outcome in review['reviews']:
        jid = outcome['journal_id']
        if outcome['outcome'] == 'deferred':
            exceptions.append(dict(journal_id=jid, title=outcome['title'], field='identity', reason=outcome['reason'],
                next_step='Check source-occurrence context, primary and translated titles, own ISSNs and competing library/OpenAlex identities; retain separate candidate IDs.'))
        elif nodes[jid].get('publication_start') is None:
            exceptions.append(dict(journal_id=jid, title=outcome['title'], field='publication_start', reason=outcome['date_reason'],
                next_step='Read first-issue and title-history evidence, distinguishing series, print/online editions and predecessor titles.'))
        if jid in profiles and jid not in checked:
            exceptions.append(dict(journal_id=jid, title=outcome['title'], field='subject_classification',
                reason='No accepted broad subject mapping yet; original library headings remain in bibliographic evidence.',
                next_step='Review unmapped headings or publisher remit; retain narrower provisional classifications until explicitly checked.'))
    exception_path = ROOT/'feedback/journals/library-integration-v1.111-exceptions.json'
    exception_path.write_text(json.dumps(exceptions, ensure_ascii=False, indent=2)+'\n')
    result = dict(version='1.111', status='passed', snapshot=str(before_path.relative_to(ROOT)),
        snapshot_sha256=sha(before_path), graph_sha256=sha(ROOT/'historiography-1920-2000.json'),
        catalogue_sha256=sha(DATA/'catalogue.json'), additions=review['counts'],
        coverage={k:v for k,v in counts.items() if k not in ('subjects','unclassified_journal_ids','ambiguous_title_ids','limitations','source_occurrences')},
        candidates_with_reviewed_subject_or_profile=len(checked | profiles),
        profiles_with_headings_and_publication_start=sum(n['id'] in profiles and n.get('publication_start') is not None
            and any(r.get('subjects') for r in n['bibliographic_evidence']) for n in journals),
        unclassified_candidates=len(counts['unclassified_journal_ids']),
        preserved_staged_records=len(review['stage_sha256']), verified_used_raw_responses=len(review['used_raw_sha256']),
        historical_graph_preserved=True, old_sources_preserved=True, old_chronology_preserved=True,
        candidate_ids_and_occurrences_preserved=True, exact_generator_rebuild=True,
        exception_count=len(exceptions), exception_candidates=len({e['journal_id'] for e in exceptions}),
        next_step='Resolve field-specific exceptions; avoid rerunning frozen initial retrieval plans against the enriched catalogue.',
        limitations='Reviewed bibliographic identity is not full publisher-remit verification. Catalogued title/edition starts are not independently verified founding dates. Library agreement may reflect shared cataloguing. No complete holdings feed.')
    (ROOT/'feedback/journals/library-integration-v1.111.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    audit()
