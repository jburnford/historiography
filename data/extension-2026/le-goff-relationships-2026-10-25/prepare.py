"""Prepare the focused Le Goff supplement; --check never rewrites a packet."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / 'data/field-research/le-goff-relationships-2026-10-25'
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
    assert before['revision_history'][-1]['version'] == '1.192'
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
    assert all('jacques_le_goff' in (e['source'], e['target']) for e in added)
    keys = [(e['source'], e['target'], e['relationship_kind']) for e in added]
    assert len(keys) == len(set(keys)), 'Duplicate new directed claim category'
    errors, warnings = validate(after, read(ROOT / 'seminar-pathways.json'))
    assert not errors, errors
    degree = lambda graph: sum('jacques_le_goff' in (e['source'], e['target'])
                              for e in graph['edges'])
    return dict(status='pass', counts={k: len(after[k]) for k in ('nodes', 'edges', 'sources', 'people')},
                new_edges=len(added), new_sources=len(packet['sources']),
                source_addenda=len(packet['source_addenda']),
                le_goff_before=degree(before), le_goff_after=degree(after),
                old_edges_nodes_people_chronology_preserved=True,
                old_sources_preserved_with_append_only_reading_notes=True,
                structural_errors=errors, structural_warnings=warnings,
                expected_production_sha256=hashlib.sha256(serial(after).encode()).hexdigest())


def prepare():
    assert not (ROOT / 'data/production-batches/person-links-1.193/acceptance.json').exists()
    before = read(ROOT / 'historiography-1920-2000.json')
    assert before['revision_history'][-1]['version'] == '1.192'
    old_sources = {s['id']: s for s in before['sources']}
    edges, sources, addenda, inputs = [], {}, {}, {}
    for lane in ('annales', 'reception', 'methods', 'memory'):
        for name in ('proposals.json', 'sources.json'):
            path = AUDIT / lane / name
            inputs[str(path.relative_to(ROOT))] = sha(path)
        for row in read(AUDIT / lane / 'proposals.json')['proposals']:
            edges.append({k: row[k] for k in ['proposal_id', *EDGE_KEYS] if k in row})
        doc = read(AUDIT / lane / 'sources.json')
        for item in doc['sources']:
            source = item.get('source_record', item)
            if source['id'] in sources:
                assert sources[source['id']] == source
            sources[source['id']] = source
        for sid, note in doc.get('source_addenda', {}).items():
            assert sid not in addenda, 'Merge source reading notes explicitly'
            note = deepcopy(note)
            prefix = old_sources[sid].get('verification', {}).get('note', '')
            if prefix and note['note'].startswith(prefix):
                note['note'] = note['note'][len(prefix):].strip()
            addenda[sid] = note
    assert len({e['proposal_id'] for e in edges}) == len(edges)
    existing = {s['id'] for s in before['sources']}
    assert not existing.intersection(sources)
    assert set(addenda) <= existing
    cited = {sid for e in edges for sid in e['source_ids']}
    assert set(sources) <= cited, 'Unused new source'
    cfg = dict(revision='1.193', baseline_revision='1.192', date='2026-10-25',
               batch_dir='person-links-1.193', persons=[], extras=['responses'],
               summary=f'Add {len(edges)} source-reviewed relationships for Jacques Le Goff after a focused review of his intellectual debts, collaborations and critical reception.',
               authorization='The user requests correction of Le Goff’s sparse relationships; earlier authorization to research with agents, review with Astra, correct and push persists.',
               rationale='Existing endpoints only. Preserve named debts, critical qualifications, coauthor and translator credit, and selected-reading limits. No relationship quota, new biography, life fact, chronology event or dissertation count.')
    write(HERE / 'batch.json', cfg)
    write(HERE / 'responses/entry-draft.json', dict(proposed_edges=edges,
          new_sources=list(sources.values()), source_addenda=addenda))
    batch = Batch(HERE)
    batch.build()
    report = verify(before, read(batch.packet), batch.transform(before, read(batch.packet)))
    write(HERE / 'verification.json', report)
    write(HERE / 'baseline.json', dict(revision='1.192',
          commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          graph_sha256=sha(ROOT / 'historiography-1920-2000.json'),
          counts={k: len(before[k]) for k in ('nodes', 'edges', 'sources', 'people')}))
    write(HERE / 'manifest.json', dict(input_sha256=inputs, new_edge_count=len(edges),
          new_source_count=len(sources), expected_production_sha256=report['expected_production_sha256']))
    files = ['batch.json', 'responses/entry-draft.json', 'release/editorial-additions.json',
             'verification.json', 'baseline.json', 'manifest.json', 'prepare.py']
    write(HERE / 'freeze.json', dict(revision='1.193', packet_sha256=sha(batch.packet),
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
