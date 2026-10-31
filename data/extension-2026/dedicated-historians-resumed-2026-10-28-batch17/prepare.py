"""Freeze the reviewed subset of the remaining-historians audit; --check never rewrites."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / 'data/field-research/dedicated-historians-resumed-2026-10-28'
SELECTION = AUDIT / 'publication-selection-1.222.json'
sys.path.insert(0, str(ROOT))
from scripts.apply_person_entries import Batch, EDGE_KEYS, serial
from scripts.validate_graph import validate
from scripts.source_hosts import findings


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def key(edge):
    ends = (edge['source'], edge['target'])
    if edge.get('relationship_kind') == 'comparison':
        ends = tuple(sorted(ends))
    return (*ends, edge.get('relationship_kind'))


def verify(before, packet, after):
    selection = read(SELECTION)
    subjects = selection['person_ids']
    assert before['revision_history'][-1]['version'] == '1.221'
    for field in ('nodes', 'people_updates', 'edge_revisions', 'roster_edges', 'wikidata'):
        assert not packet[field], field
    for field, value in before.items():
        if field not in ('edges', 'sources', 'revision_history'):
            assert after[field] == value, field
    assert after['edges'][:len(before['edges'])] == before['edges']
    assert after['revision_history'][:-1] == before['revision_history']
    after_sources = {s['id']: s for s in after['sources']}
    for old in before['sources']:
        current = deepcopy(after_sources[old['id']])
        if old['id'] in packet['source_addenda']:
            assert current['verification']['note'].startswith(old['verification']['note'])
            current['verification'] = old['verification']
        assert current == old, old['id']
    added = after['edges'][len(before['edges']):]
    assert all(set(subjects).intersection((e['source'], e['target'])) for e in added)
    # Exclude the owned dossier, while allowing other historians' explicit use
    # of the existing endpoint; all old nodes and edges remain exact above.
    assert 'alexis_de_tocqueville' not in subjects
    assert len({key(e) for e in added}) == len(added)
    assert not {key(e) for e in before['edges']}.intersection(key(e) for e in added)
    errors, warnings = validate(after, read(ROOT / 'seminar-pathways.json'))
    assert not errors, errors
    people = {n['id'] for n in before['nodes'] if n.get('entry_kind') == 'person'}
    def measures(graph, subject):
        incident = [e for e in graph['edges'] if subject in (e['source'], e['target'])]
        neighbors = {e['target'] if e['source'] == subject else e['source'] for e in incident}
        return dict(relationships=len(incident), person_neighbors=sorted(neighbors & people))
    return dict(status='pass', counts={k: len(after[k]) for k in ('nodes', 'edges', 'sources', 'people')},
                new_edges=len(added), new_sources=len(packet['sources']),
                source_addenda=len(packet['source_addenda']), reviewed_dossiers=len(subjects),
                remaining_priority_dossiers=len(selection['remaining_person_ids']),
                subjects={pid: dict(before=measures(before, pid), after=measures(after, pid)) for pid in subjects},
                old_edges_nodes_people_chronology_preserved=True,
                old_sources_preserved_with_append_only_reading_notes=True,
                structural_errors=errors, structural_warnings=warnings,
                expected_production_sha256=hashlib.sha256(serial(after).encode()).hexdigest())


def prepare():
    assert not (ROOT / 'data/production-batches/person-links-1.222/acceptance.json').exists()
    before = read(ROOT / 'historiography-1920-2000.json')
    baseline = read(AUDIT / 'request-baseline.json')
    selection = read(SELECTION)
    assert before['revision_history'][-1]['version'] == selection['baseline_revision'] == '1.221'
    assert sha(ROOT / 'historiography-1920-2000.json') == selection['baseline_graph_sha256']
    assert selection['baseline_counts'] == {k: len(before[k]) for k in selection['baseline_counts']}
    assert selection['research_baseline_graph_sha256'] == baseline['baseline_graph_sha256']
    first = read(AUDIT / 'implementation-1.221.json')
    assert first['production_sha256'] == selection['baseline_graph_sha256']
    assert read(ROOT / selection['baseline_acceptance_record'])['production_sha256'] == selection['baseline_graph_sha256']
    previous = [read(AUDIT / ('implementation-' + rev + '.json')) for rev in ['1.205', '1.206', '1.207', '1.208', '1.209', '1.210', '1.211', '1.212', '1.213', '1.214', '1.215', '1.217', '1.218', '1.219', '1.220', '1.221']]
    assert set().union(*(set(x['person_ids']) for x in previous)) == set(selection['previously_implemented_person_ids'])
    subjects = selection['person_ids']
    assert len(subjects) == len(set(subjects))
    previously = set(selection['previously_implemented_person_ids'])
    assert not previously.intersection(subjects)
    assert set(subjects) | set(selection['remaining_person_ids']) | previously == set(baseline['remaining_person_ids'])
    assert not set(subjects).intersection(selection['remaining_person_ids'])
    assert 'alexis_de_tocqueville' in baseline['excluded_person_ids']
    old_sources = {s['id']: s for s in before['sources']}
    edges, sources, addenda, source_owners, new_source_addenda = [], {}, {}, {}, {}
    spacing = read(HERE / 'text-spacing.json')
    spacing_used = set()
    def display(key, value):
        if key not in spacing:
            return value
        row = spacing[key]
        assert row['old'] == value, key
        assert value.replace(' ', '') == row['new'].replace(' ', ''), key
        spacing_used.add(key)
        return row['new']
    legacy_type_normalizations = {}
    paths = [HERE / 'text-spacing.json', ROOT / selection['baseline_acceptance_record'], SELECTION, AUDIT / 'request-baseline.json', AUDIT / 'available-person-endpoints.json',
             AUDIT / 'publication-selection-1.205.json', AUDIT / 'implementation-1.205.json',
             AUDIT / 'publication-selection-1.206.json', AUDIT / 'implementation-1.206.json',
             AUDIT / 'publication-selection-1.207.json', AUDIT / 'implementation-1.207.json',
             AUDIT / 'publication-selection-1.208.json', AUDIT / 'implementation-1.208.json',
             AUDIT / 'publication-selection-1.209.json', AUDIT / 'implementation-1.209.json',
             AUDIT / 'publication-selection-1.210.json', AUDIT / 'implementation-1.210.json',
             AUDIT / 'publication-selection-1.211.json', AUDIT / 'implementation-1.211.json',
             AUDIT / 'publication-selection-1.212.json', AUDIT / 'implementation-1.212.json',
             AUDIT / 'publication-selection-1.213.json', AUDIT / 'implementation-1.213.json',
             AUDIT / 'publication-selection-1.214.json', AUDIT / 'implementation-1.214.json',
             AUDIT / 'publication-selection-1.215.json', AUDIT / 'implementation-1.215.json',
             AUDIT / 'publication-selection-1.217.json', AUDIT / 'implementation-1.217.json',
             AUDIT / 'publication-selection-1.218.json', AUDIT / 'implementation-1.218.json',
             AUDIT / 'publication-selection-1.219.json', AUDIT / 'implementation-1.219.json',
             AUDIT / 'publication-selection-1.220.json', AUDIT / 'implementation-1.220.json',
             AUDIT / 'publication-selection-1.221.json', AUDIT / 'implementation-1.221.json',
             AUDIT / 'baseline-counts-amendment-1.218.json',
             AUDIT / 'integration-notes-1.222.md',
             ROOT / 'data/field-research/stedman-jones-relationships-2026-10-25/review-protocol.md']
    for subject in subjects:
        folder = AUDIT / subject
        context = read(folder / 'context.json')
        assert context['person_id'] == subject
        assert context['baseline_graph_sha256'] == selection['research_baseline_graph_sha256']
        review = read(folder / 'independent-review.json')
        assert review['verdict'].startswith('pass') and not review.get('blocking_findings'), subject
        assert set(review['reviewed_sha256']) >= {'context.json', 'proposals.json', 'sources.json', 'held-cases.json', 'case-review.json', 'README.md'}
        for name, digest in review['reviewed_sha256'].items():
            assert 'raw/' not in name, 'Public checks cannot require unpublished bodies'
            assert sha(folder / name) == digest, (subject, name, 'stale independent review')
            paths.append(folder / name)
        paths.append(folder / 'independent-review.json')
        access_path = folder / 'source-access-review-2026-10-30.json'
        access = read(access_path)
        assert access['verdict'] == 'pass' and not access['blocking_findings']
        assert access['reviewed_sha256'] == review['reviewed_sha256']
        paths.append(access_path)
        rows = read(folder / 'proposals.json')['proposals']
        assert review['proposal_count'] == len(rows), subject
        for row in rows:
            assert subject in (row['source'], row['target'])
            edge = {k: row[k] for k in ['proposal_id', *EDGE_KEYS] if k in row}
            if edge['relationship_kind'] == 'critique' and edge['type'] == 'connection':
                legacy_type_normalizations[row['proposal_id']] = dict(person_id=subject, **{'from': 'connection', 'to': 'critique'})
                edge['type'] = 'critique'
            for field in ('relationship', 'evidence_note'):
                edge[field] = display(f'edges|{row["proposal_id"]}|{field}', edge[field])
            assert not findings(json.dumps(edge, ensure_ascii=False)), row['proposal_id']
            edges.append(edge)
        doc = read(folder / 'sources.json')
        for source in doc['sources']:
            source = deepcopy(source)
            sid = source['id']
            for field in ('title', 'citation'):
                source[field] = display(f'sources|{sid}|{field}', source[field])
            source['verification']['note'] = display(f'sources|{sid}|verification.note', source['verification']['note'])
            assert not findings(json.dumps(source, ensure_ascii=False)), sid
            assert sid not in sources or sources[sid] == source, ('Conflicting source', sid)
            sources[sid] = source
            source_owners.setdefault(sid, []).append(subject)
        for sid, note in doc.get('source_addenda', {}).items():
            note = deepcopy(note)
            if isinstance(note, str):
                note = dict(status='supporting_page_checked', checked_on='2026-10-28', note=note)
            note['note'] = display(f'addenda|{sid}|{subject}', note['note'])
            assert not findings(note['note']), sid
            if sid not in old_sources:
                new_source_addenda.setdefault(sid, []).append(dict(person_id=subject, verification=note))
                continue
            prefix = old_sources[sid].get('verification', {}).get('note', '')
            if prefix and note['note'].startswith(prefix):
                note['note'] = note['note'][len(prefix):].strip()
            if sid in addenda:
                note = dict(status='supporting_page_checked', checked_on='2026-10-28',
                            note=addenda[sid]['note'] + ' Separately scoped dedicated-person reading: ' + note['note'])
            addenda[sid] = note
    assert spacing_used == set(spacing), sorted(set(spacing) - spacing_used)
    # Preserve separately scoped reading notes for any shared new source.
    for sid, readings in new_source_addenda.items():
        assert sid in sources, ('Unknown shared new source', sid)
        sources[sid] = deepcopy(sources[sid])
        verification = sources[sid]['verification']
        for reading in readings:
            note = reading['verification']
            verification['note'] += f" Addendum {note['checked_on']}: {note['note']}"
            if note['status'] == 'supporting_page_checked':
                verification['status'], verification['checked_on'] = note['status'], note['checked_on']
    assert len({e['proposal_id'] for e in edges}) == len(edges)
    assert len({key(e) for e in edges}) == len(edges)
    assert not set(old_sources).intersection(sources)
    assert set(addenda) <= set(old_sources)
    cited = {sid for e in edges for sid in e['source_ids']}
    assert cited <= set(old_sources) | set(sources), sorted(cited - set(old_sources) - set(sources))
    # Unused sources support held/negative-search cases. Keep them in the frozen
    # owner dossier, but publish only sources actually cited by accepted edges.
    excluded_sources = {sid: source_owners[sid] for sid in sorted(set(sources) - cited)}
    included_sources = [s for sid, s in sources.items() if sid in cited]
    cfg = dict(revision='1.222', baseline_revision='1.221', date='2026-10-30',
               batch_dir='person-links-1.222', persons=[], extras=['responses'],
               summary=f'Add {len(edges)} relationships from {len(subjects)} independently reviewed historian dossiers; continue research on the remaining priority list.',
               authorization='The user explicitly resumed researching and adding edges for leading timeline historians while UK dissertation collection continues. Prior researcher dossiers are reviewed by the explicitly named reviewers; current source restrictions apply. Apply only this independently reviewed subset; continue the remaining queue. No new publication/push is inferred from this resume.',
               rationale='Existing endpoints only; preserve named mediation, coauthorship, critical qualifications, edition and reading limits. All old graph records unchanged apart from append-only source reading notes. Tocqueville excluded as an owned dossier or newly read primary body, not as an existing resource endpoint in another historian’s own testimony. No new biographies, fields, life facts, chronology or dissertation analysis. OpenAlex remains paused.')
    write(HERE / 'batch.json', cfg)
    write(HERE / 'responses/entry-draft.json', dict(proposed_edges=edges, new_sources=included_sources, source_addenda=addenda))
    batch = Batch(HERE)
    batch.build()
    report = verify(before, read(batch.packet), batch.transform(before, read(batch.packet)))
    write(HERE / 'verification.json', report)
    write(HERE / 'baseline.json', dict(revision='1.221', commit=selection['baseline_commit'],
          graph_sha256=sha(ROOT / 'historiography-1920-2000.json'),
          counts={k: len(before[k]) for k in ('nodes', 'edges', 'sources', 'people')}))
    write(HERE / 'manifest.json', dict(input_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
          person_ids=subjects, new_edge_count=len(edges), new_source_count=len(included_sources),
          legacy_type_normalizations=legacy_type_normalizations,
          new_source_reading_addenda=new_source_addenda,
          excluded_uncited_new_sources=excluded_sources,
          expected_production_sha256=report['expected_production_sha256']))
    files = ['batch.json', 'responses/entry-draft.json', 'release/editorial-additions.json',
             'verification.json', 'baseline.json', 'manifest.json', 'prepare.py', 'text-spacing.json']
    write(HERE / 'freeze.json', dict(revision='1.222', packet_sha256=sha(batch.packet),
          files_sha256={name: sha(HERE / name) for name in files}))
    print(json.dumps({k: v for k, v in report.items() if k not in ('subjects', 'structural_warnings')}))


def check():
    for name, digest in read(HERE / 'freeze.json')['files_sha256'].items():
        assert sha(HERE / name) == digest, name
    for name, digest in read(HERE / 'manifest.json')['input_sha256'].items():
        assert sha(ROOT / name) == digest, name
    batch = Batch(HERE)
    accepted = (batch.out / 'acceptance.json').exists()
    before = batch.baseline() if accepted else read(ROOT / 'historiography-1920-2000.json')
    after = batch.check() if accepted else batch.transform(before, read(batch.packet))
    assert verify(before, read(batch.packet), after) == read(HERE / 'verification.json')
    print('PASS: frozen reviewed subset, hashes and exact preservation; no mutation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check() if args.check else prepare()
