"""Prepare the first five dedicated historian relationship dossiers; --check never rewrites a packet."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / 'data/field-research/dedicated-historians-five-2026-10-25-batch01'
SUBJECTS = ['angela_cavender_wilson', 'darcy_mcnickle', 'edward_ahenakew', 'georges_e_sioui', 'howard_adams']
sys.path.insert(0, str(ROOT))
from scripts.apply_person_entries import Batch, EDGE_KEYS, serial
from scripts.validate_graph import validate


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def verify(before, packet, after):
    assert before['revision_history'][-1]['version'] == '1.195'
    assert not packet['nodes'] and not packet['people_updates']
    assert not packet['edge_revisions'] and not packet['roster_edges']
    for key, value in before.items():
        if key not in ('edges', 'sources', 'revision_history'):
            assert after[key] == value, key
    assert after['edges'][:len(before['edges'])] == before['edges']
    assert after['revision_history'][:-1] == before['revision_history']
    sources = {s['id']: s for s in after['sources']}
    for old in before['sources']:
        current = deepcopy(sources[old['id']])
        if old['id'] in packet['source_addenda']:
            assert current['verification']['note'].startswith(old['verification']['note'])
            current['verification'] = old['verification']
        assert current == old, old['id']
    added = after['edges'][len(before['edges']):]
    assert all(set(SUBJECTS).intersection((e['source'], e['target'])) for e in added)
    keys = [(e['source'], e['target'], e['relationship_kind']) for e in added]
    assert len(keys) == len(set(keys)), 'Duplicate new directed claim category'
    old_keys = {(e['source'], e['target'], e.get('relationship_kind')) for e in before['edges']}
    assert not old_keys.intersection(keys), 'Existing direct relationship duplicated'
    errors, warnings = validate(after, read(ROOT / 'seminar-pathways.json'))
    assert not errors, errors
    people = {n['id'] for n in before['nodes'] if n.get('entry_kind') == 'person'}
    def measures(graph, subject):
        incident = [e for e in graph['edges'] if subject in (e['source'], e['target'])]
        neighbors = {e['target'] if e['source'] == subject else e['source'] for e in incident}
        return dict(relationships=len(incident), person_neighbors=sorted(neighbors & people))
    return dict(status='pass', counts={k: len(after[k]) for k in ('nodes', 'edges', 'sources', 'people')},
                new_edges=len(added), new_sources=len(packet['sources']),
                source_addenda=len(packet['source_addenda']),
                subjects={subject: dict(before=measures(before, subject), after=measures(after, subject)) for subject in SUBJECTS},
                old_edges_nodes_people_chronology_preserved=True,
                old_sources_preserved_with_append_only_reading_notes=True,
                structural_errors=errors, structural_warnings=warnings,
                expected_production_sha256=hashlib.sha256(serial(after).encode()).hexdigest())


def prepare():
    assert not (ROOT / 'data/production-batches/person-links-1.196/acceptance.json').exists()
    before = read(ROOT / 'historiography-1920-2000.json')
    assert before['revision_history'][-1]['version'] == '1.195'
    selection = read(AUDIT / 'batch-selection.json')
    assert selection['baseline_revision'] == '1.195'
    assert selection['baseline_graph_sha256'] == sha(ROOT / 'historiography-1920-2000.json')
    assert selection['person_ids'] == SUBJECTS
    old_sources = {s['id']: s for s in before['sources']}
    edges, sources, addenda = [], {}, {}
    inputs = {}
    paths = [AUDIT / 'batch-selection.json',
             ROOT / 'data/field-research/stedman-jones-relationships-2026-10-25/review-protocol.md',
             ROOT / 'data/field-research/stedman-jones-relationships-2026-10-25/review-queue-baseline-1.194.json']
    for subject in SUBJECTS:
        context = read(AUDIT / subject / 'context.json')
        assert context['person_id'] == subject
        assert context['baseline_graph_sha256'] == selection['baseline_graph_sha256']
        review = read(AUDIT / subject / 'independent-review.json')
        reviewed = review['reviewed_sha256']
        assert set(reviewed) >= {'proposals.json', 'sources.json', 'held-cases.json', 'case-review.json'}
        for name, digest in reviewed.items():
            assert sha(AUDIT / subject / name) == digest, (subject, name, 'stale independent review')
        assert review['verdict'].startswith('pass'), subject
        assert not review.get('blocking_findings'), subject
        assert review['proposal_count'] == len(read(AUDIT / subject / 'proposals.json')['proposals']), subject
        paths += [AUDIT / subject / name for name in ('context.json', 'proposals.json', 'sources.json', 'held-cases.json', 'case-review.json', 'independent-review.json', 'README.md')]
    for path in paths:
        inputs[str(path.relative_to(ROOT))] = sha(path)
    streams = [(AUDIT / subject / 'proposals.json', AUDIT / subject / 'sources.json') for subject in SUBJECTS]
    for proposal_path, source_path in streams:
        for path in (proposal_path, source_path):
            inputs[str(path.relative_to(ROOT))] = sha(path)
        for row in read(proposal_path)['proposals']:
            edges.append({k: row[k] for k in ['proposal_id', *EDGE_KEYS] if k in row})
        doc = read(source_path)
        for item in (doc if isinstance(doc, list) else doc['sources']):
            source = item.get('source_record', item)
            if source['id'] in sources:
                assert sources[source['id']] == source
            sources[source['id']] = source
        for sid, note in (doc.get('source_addenda', {}) if isinstance(doc, dict) else {}).items():
            note = deepcopy(note)
            if isinstance(note, str):
                note = dict(status='supporting_page_checked', checked_on='2026-10-25', note=note)
            prefix = old_sources[sid].get('verification', {}).get('note', '')
            if prefix and note['note'].startswith(prefix):
                note['note'] = note['note'][len(prefix):].strip()
            if sid in addenda:
                prior = addenda[sid]
                note = dict(status='supporting_page_checked', checked_on='2026-10-25',
                            note=prior['note'] + ' Separately scoped dedicated-person reading: ' + note['note'])
            addenda[sid] = note
    assert len({e['proposal_id'] for e in edges}) == len(edges)
    existing = {s['id'] for s in before['sources']}
    assert not existing.intersection(sources)
    assert set(addenda) <= existing
    cited = {sid for e in edges for sid in e['source_ids']}
    assert set(sources) <= cited, 'Unused new source'
    cfg = dict(revision='1.196', baseline_revision='1.195', date='2026-10-25',
               batch_dir='person-links-1.196', persons=[], extras=['responses'],
               summary=f'Add {len(edges)} source-reviewed relationships after five dedicated dossiers for Angela Cavender Wilson, D’Arcy McNickle, Edward Ahenakew, Georges E. Sioui and Howard Adams, with independent passage and coverage review.',
               authorization='The user explicitly requests continuing dedicated relationship reviews with agents five at a time; earlier authorization to research, review with Astra, correct and push persists.',
               rationale='Existing endpoints only. Preserve named debts, critical qualifications, coauthor and translator credit, and selected-reading limits. No relationship quota, new biography, life fact, chronology event or dissertation count.')
    write(HERE / 'batch.json', cfg)
    write(HERE / 'responses/entry-draft.json', dict(proposed_edges=edges,
          new_sources=list(sources.values()), source_addenda=addenda))
    batch = Batch(HERE)
    batch.build()
    report = verify(before, read(batch.packet), batch.transform(before, read(batch.packet)))
    write(HERE / 'verification.json', report)
    write(HERE / 'baseline.json', dict(revision='1.195',
          commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          graph_sha256=sha(ROOT / 'historiography-1920-2000.json'),
          counts={k: len(before[k]) for k in ('nodes', 'edges', 'sources', 'people')}))
    write(HERE / 'manifest.json', dict(input_sha256=inputs, new_edge_count=len(edges),
          new_source_count=len(sources), expected_production_sha256=report['expected_production_sha256']))
    files = ['batch.json', 'responses/entry-draft.json', 'release/editorial-additions.json',
             'verification.json', 'baseline.json', 'manifest.json', 'prepare.py']
    write(HERE / 'freeze.json', dict(revision='1.196', packet_sha256=sha(batch.packet),
          files_sha256={name: sha(HERE / name) for name in files}))
    print(json.dumps({k: v for k, v in report.items() if k != 'structural_warnings'}))


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
    print('PASS: frozen supplement, input hashes and preservation checks; no mutation.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    check() if args.check else prepare()
