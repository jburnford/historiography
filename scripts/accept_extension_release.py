#!/usr/bin/env python3
"""Accept/reproduce the bounded medical/geography release; preserve frozen research."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_extension_release_candidate as candidate

read, serial, sha = candidate.read, candidate.serial, candidate.sha
GRAPH = ROOT / 'historiography-1920-2000.json'
BASE = ROOT / 'drafts/historiography-1920-2000.v1.121.json'
OUT = ROOT / 'data/production-batches/extension-1.122'
RECORD = 'data/production-batches/extension-1.122/acceptance.json'
DAY = '2026-09-18'


def baseline_path():
    return BASE if BASE.exists() else GRAPH


def accepted_path():
    """A later release preserves 1.122 as an archive; check that exact accepted state."""
    archive = ROOT / 'drafts/historiography-1920-2000.v1.122.json'
    return archive if archive.exists() else GRAPH


def verify_frozen():
    """Resolve the old live-graph pin to its exact archive after acceptance."""
    for manifest in (candidate.OUT / 'baseline.json', candidate.OUT / 'manifest.json',
                     candidate.PACKET / 'manifest.json'):
        for name, expected in read(manifest)['files'].items():
            path = baseline_path() if name == 'historiography-1920-2000.json' else ROOT / name
            if not path.is_file() or sha(path) != expected:
                raise ValueError('Pinned input changed: ' + name)


@contextmanager
def archived_candidate_inputs():
    """Run the unchanged historical builder against its original graph."""
    old = candidate.GRAPH
    candidate.GRAPH = baseline_path()
    try:
        yield
    finally:
        candidate.GRAPH = old


def checked_candidate():
    verify_frozen()
    with archived_candidate_inputs():
        generated, preview = candidate.outputs()
    for name, value in generated.items():
        if serial(value) != (candidate.OUT / name).read_text():
            raise ValueError('Frozen candidate reconstruction differs: ' + name)
    if generated['summary.json']['errors']:
        raise ValueError(str(generated['summary.json']['errors']))
    return generated['candidate.json'], preview


def transform(before, delta):
    graph = candidate.project(before, delta)
    errors, _ = candidate.audit(before, graph, delta)
    if errors:
        raise ValueError(str(errors))
    decisions = {d['claim_id']: d for d in read(candidate.OUT / 'review-decisions.json')['claims']}
    new_ids = {c['id'] for c in delta['catalogue_additions']['claims']}
    for claim in graph['claim_catalogue']['claims']:
        if claim['id'] not in new_ids:
            continue
        if claim['predicate'] in ('authored', 'realizes'):
            reason = 'Accept the recorded bibliographic credit/version identity; no intellectual influence inferred.'
        else:
            decision = decisions[claim['id']]
            if decision['decision'] != 'recommend_bounded_acceptance':
                raise ValueError('Claim lacks bounded acceptance recommendation: ' + claim['id'])
            reason = decision['rationale']
        claim['review'] = dict(status='accepted', reviewed_on=DAY,
                               reviewer='Codex editorial integration review', rationale=reason)
        claim['history'].append(dict(date=DAY, action='accepted_into_production',
                                     revision='1.122', decision_record=RECORD))
    new_entities = {e['id'] for e in delta['catalogue_additions']['entities']}
    for entity in graph['claim_catalogue']['entities']:
        if entity['id'] in new_entities and entity['type'] == 'person':
            entity['identity_status'] = 'existing_local_person'
    for node in graph['nodes']:
        if node['id'] in candidate.FIELDS:
            node['extension_coverage'].update(status='partial_accepted', acceptance_record=RECORD)
    graph['scope']['extension'].update(status='partial_accepted', baseline_graph=str(BASE.relative_to(ROOT)),
                                       baseline_revision='1.121', baseline_sha256=delta['baseline_sha256'],
                                       acceptance_record=RECORD)
    graph['revision_history'].append(dict(
        version='1.122', date=DAY, acceptance_record=RECORD,
        summary='First partial post-2000 release: nine medical-history and historical-geography works, '
                'twelve scoped historical claims, eighteen author credits and one reprint assertion. '
                'Nine strands and seventeen shared people; no new teaching edges. '
                'Exact revision 1.121 retained as the 2000 view; neither field is completely reviewed through 2026.'))
    errors, _ = candidate.validate(graph, read(ROOT / 'seminar-pathways.json'))
    if errors:
        raise ValueError(str(errors))
    return graph


def verify_accepted(actual, expected):
    if actual != expected:
        raise ValueError('Accepted graph differs from exact reviewed transformation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--candidate-preview', type=Path)
    args = parser.parse_args()
    delta, preview = checked_candidate()
    if args.candidate_preview:
        path = args.candidate_preview.resolve()
        if not path.is_relative_to(Path('/tmp')):
            raise ValueError('Candidate previews must stay under /tmp')
        path.write_text(serial(preview))
        print('Frozen candidate reproduced against exact revision 1.121.')
        return
    before = read(baseline_path())
    expected = transform(before, delta)
    if args.apply:
        if sha(GRAPH) != delta['baseline_sha256']:
            raise ValueError('Production is no longer the reviewed 1.121 baseline; refusing to apply')
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Acceptance record already exists; use --check')
        if not BASE.exists():
            BASE.write_bytes(GRAPH.read_bytes())
        OUT.mkdir(parents=True, exist_ok=True)
        decisions = read(candidate.OUT / 'review-decisions.json')
        record = dict(revision='1.122', date=DAY, baseline=str(BASE.relative_to(ROOT)),
                      baseline_sha256=sha(BASE), production_sha256=candidate.fingerprint(expected),
                      authorization='Continuation of the authorized extension; user reports the website ready. '
                                    'Local production integration and build, not remote deployment.',
                      accepted_claim_ids=[c['id'] for c in delta['catalogue_additions']['claims']],
                      prior_claim_records=deepcopy(delta['catalogue_additions']['claims']),
                      historical_decisions=decisions['claims'],
                      evidence_note='All evidence joins, qualifications and dates retained exactly. '
                                    'Eight selected-passage and four abstract historical claims; no full-work certification.',
                      frozen_inputs={str(p.relative_to(ROOT)): sha(p) for p in
                                     [candidate.OUT / 'manifest.json', candidate.OUT / 'candidate.json',
                                      candidate.OUT / 'review-decisions.json', ROOT / 'seminar-pathways.json']})
        (OUT / 'acceptance.json').write_text(serial(record))
        GRAPH.write_text(serial(expected))
    record = read(OUT / 'acceptance.json')
    for name, digest in record['frozen_inputs'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('Accepted input changed: ' + name)
    if sha(BASE) != record['baseline_sha256'] or sha(accepted_path()) != record['production_sha256']:
        raise ValueError('Accepted graph or archive hash differs')
    verify_accepted(read(accepted_path()), expected)
    errors, warnings = candidate.validate(expected, read(ROOT / 'seminar-pathways.json'))
    print(serial(dict(revision='1.122', errors=errors, warnings=warnings,
                     totals={k: len(expected[k]) for k in ('nodes', 'edges', 'sources', 'people')})), end='')


if __name__ == '__main__':
    main()
