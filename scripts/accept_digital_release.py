#!/usr/bin/env python3
"""Accept/reproduce digital release 10 without modifying its frozen research inputs."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_digital_release_candidate as candidate

read, serial, sha = candidate.read, candidate.serial, candidate.sha
GRAPH = ROOT/'historiography-1920-2000.json'
BASE = ROOT/'drafts/historiography-1920-2000.v1.122.json'
OUT = ROOT/'data/production-batches/extension-1.123'
PUBLIC_BASE = OUT/'baseline-public-1.122.json'
RECORD = 'data/production-batches/extension-1.123/acceptance.json'
DAY = '2026-09-19'


def baseline_path():
    return BASE if BASE.exists() else GRAPH


def frozen_path(name):
    if name == 'historiography-1920-2000.json':
        return baseline_path()
    if name == 'docs/data/graph.json' and PUBLIC_BASE.exists():
        return PUBLIC_BASE
    return ROOT/name


def frozen_errors():
    errors = []
    for manifest in (candidate.OUT/'baseline.json', candidate.OUT/'manifest.json'):
        for name, expected in read(manifest)['files'].items():
            path = frozen_path(name)
            if not path.is_file() or sha(path) != expected:
                errors.append('Pinned input changed: '+name)
    return errors


@contextmanager
def archived_candidate_inputs():
    """Historical builder/tests resolve their original graph and public-build pins."""
    old_graph,old_verify = candidate.GRAPH,candidate.verify_inputs
    candidate.GRAPH,candidate.verify_inputs = baseline_path(),frozen_errors
    try:
        yield
    finally:
        candidate.GRAPH,candidate.verify_inputs = old_graph,old_verify


def checked_candidate():
    errors = frozen_errors()
    if errors:
        raise ValueError('\n'.join(errors))
    with archived_candidate_inputs():
        generated,preview = candidate.outputs()
    for name,value in generated.items():
        if serial(value) != (candidate.OUT/name).read_text():
            raise ValueError('Frozen candidate reconstruction differs: '+name)
    if generated['summary.json']['errors']:
        raise ValueError(str(generated['summary.json']['errors']))
    return generated,preview


def transform(before, delta, batch):
    graph = candidate.project(before,delta)
    errors,_ = candidate.audit(before,graph,batch,delta)
    if errors:
        raise ValueError(str(errors))
    decisions = {d['claim_id']:d for d in read(candidate.OUT/'review-decisions.json')['claims']}
    new_ids = {c['id'] for c in delta['catalogue_additions']['claims']}
    for claim in graph['claim_catalogue']['claims']:
        if claim['id'] not in new_ids:
            continue
        if claim['predicate'] in ('authored','realizes'):
            reason = 'Accept the recorded author credit or version identity; no influence or whole-work reading inferred.'
        else:
            decision = decisions[claim['id']]
            if decision['decision'] != 'recommend_bounded_acceptance':
                raise ValueError('Historical claim lacks bounded recommendation: '+claim['id'])
            reason = decision['rationale']
        claim['review'] = dict(status='accepted', reviewed_on=DAY,
                              reviewer='Codex editorial integration review', rationale=reason)
        claim['history'].append(dict(date=DAY, action='accepted_into_production', revision='1.123', decision_record=RECORD))
    entity_ids = {e['id'] for e in delta['catalogue_additions']['entities']}
    for entity in graph['claim_catalogue']['entities']:
        if entity['id'] in entity_ids and entity['type'] == 'person':
            entity['identity_status'] = 'existing_local_person'
    for node in graph['nodes']:
        if node['id'] not in candidate.FIELDS:
            continue
        node['extension_coverage'].update(status='partial_accepted',acceptance_record=RECORD)
        for strand in node['strands']:
            strand['review_status'] = 'accepted'
    previous_scope = before['scope']['extension']
    records = list(dict.fromkeys(previous_scope.get('acceptance_records',[]) +
                                [previous_scope['acceptance_record'],RECORD]))
    graph['scope']['extension'].update(status='partial_accepted',acceptance_record=RECORD,acceptance_records=records,
        note='Selected medical, geographical, digital and web-history interventions only. '
             'Publication milestones are not field origins or endpoints; no field is completely reviewed through 2026.')
    # The delta's 1.122 baseline is NOT the exact-2000 view's 1.121 baseline.
    for key in ('baseline_graph','baseline_revision','baseline_sha256'):
        if graph['scope']['extension'][key] != previous_scope[key]:
            raise ValueError('Exact 2000 baseline changed: '+key)
    graph['revision_history'].append(dict(version='1.123',date=DAY,acceptance_record=RECORD,
        summary='Accept the revised digital/web selection: two research-field entries, seventeen selected works, '
                'twenty-seven historical claims, thirty-one author credits, two version links, twenty contextual strands '
                'and twenty-six shared people. Practitioner contributions and critical scholarship coexist; '
                'no new teaching arrows. Exact 2000 baseline remains 1.121; no field-completeness claim.'))
    errors,_ = candidate.validate_graph(graph,read(ROOT/'seminar-pathways.json'))
    if errors:
        raise ValueError(str(errors))
    return graph


def verify_accepted(actual,expected):
    if actual != expected:
        raise ValueError('Accepted graph differs from exact reviewed transformation')


def coverage(graph):
    """Keep the discovery ledger while adding the two now-existing topic rows."""
    result = deepcopy(read(candidate.OUT/'coverage-current.json'))
    result.update(graph_revision='1.123',derived_from=str((candidate.OUT/'coverage-current.json').relative_to(ROOT)),
                  acceptance_record=RECORD,accepted_field_ids=graph['scope']['extension']['field_ids'])
    for row in result['field_candidates']:
        if row['candidate_id'] not in candidate.FIELDS:
            continue
        node = next(n for n in graph['nodes'] if n['id']==row['candidate_id'])
        row.update(disposition='separate_entry_partial_accepted',production_ready=True,
                   production_entry_id=node['id'],acceptance_record=RECORD,field_review_complete=False)
        result['topics'].append(dict(entry_id=node['id'],label=node['label'],original_ledger_row=None,
            discovery_ledger_row=deepcopy(row['original_ledger_row']),entry_added_in_revision='1.123',
            current_scope_note=node['scope_note'],earlier_packet_links=[str((candidate.OUT/'README.md').relative_to(ROOT))],
            new_work_ids=deepcopy(node['work_ids']),review_outcome='pending',reviewed_through=None,
            research_bins=deepcopy(row['research_bins']),production_status='partial_accepted',acceptance_record=RECORD,
            next_action='Continue primary-project, earlier-root and regional/language review; selected accepted works do not complete a field survey.'))
    return result


def apply(generated,expected):
    delta = generated['candidate.json']
    if sha(GRAPH) != delta['baseline_sha256']:
        raise ValueError('Production is no longer the reviewed 1.122 baseline; refusing to apply')
    if (OUT/'acceptance.json').exists():
        raise ValueError('Acceptance record already exists; use --check')
    if BASE.exists() and sha(BASE) != delta['baseline_sha256']:
        raise ValueError('Existing 1.122 archive differs; refusing to overwrite')
    public = ROOT/'docs/data/graph.json'
    public_hash = read(candidate.OUT/'baseline.json')['files']['docs/data/graph.json']
    if sha(public) != public_hash or (PUBLIC_BASE.exists() and sha(PUBLIC_BASE) != public_hash):
        raise ValueError('Original published graph differs; refusing to archive or overwrite')
    if not BASE.exists():
        BASE.write_bytes(GRAPH.read_bytes())
    OUT.mkdir(parents=True,exist_ok=True)
    if not PUBLIC_BASE.exists():
        PUBLIC_BASE.write_bytes(public.read_bytes())
    record = dict(revision='1.123',date=DAY,baseline=str(BASE.relative_to(ROOT)),baseline_sha256=sha(BASE),
        prior_public_graph=str(PUBLIC_BASE.relative_to(ROOT)),prior_public_sha256=sha(PUBLIC_BASE),
        production_sha256=candidate.fingerprint(expected),
        authorization='User continued after review of the corrected digital/web candidate. '
                      'Local production integration and allowlisted build; no remote deployment.',
        editorial_direction=read(candidate.OUT/'research-reconciliation.json')['editorial_direction'],
        accepted_claim_ids=[c['id'] for c in delta['catalogue_additions']['claims']],
        prior_claim_records=deepcopy(delta['catalogue_additions']['claims']),
        historical_decisions=read(candidate.OUT/'review-decisions.json')['claims'],
        previous_extension_scope=deepcopy(delta['previous_extension_scope']),
        evidence_note='Exact evidence joins, qualifications, dates and full coauthor credits retained. '
                      'Twenty-three selected-passage and four abstract historical claims; no full-work certification.',
        frozen_inputs={str(p.relative_to(ROOT)):sha(p) for p in [candidate.OUT/'manifest.json',
            candidate.OUT/'candidate.json',candidate.OUT/'review-decisions.json',ROOT/'seminar-pathways.json']})
    (OUT/'acceptance.json').write_text(serial(record))
    GRAPH.write_text(serial(expected))
    (OUT/'coverage-current.json').write_text(serial(coverage(expected)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply',action='store_true')
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--candidate-preview',type=Path)
    mode.add_argument('--accepted-preview',type=Path)
    args = parser.parse_args()
    generated,preview = checked_candidate()
    before = read(baseline_path())
    expected = transform(before,generated['candidate.json'],generated['reconciled-research.json'])
    if args.candidate_preview or args.accepted_preview:
        dest = (args.candidate_preview or args.accepted_preview).resolve()
        if not dest.is_relative_to(Path('/tmp')):
            raise ValueError('Preview must stay under /tmp')
        dest.write_text(serial(preview if args.candidate_preview else expected))
        print('Reproduced '+('candidate' if args.candidate_preview else 'accepted')+' digital graph against exact 1.122.')
        return
    if args.apply:
        apply(generated,expected)
    record = read(OUT/'acceptance.json')
    for name,digest in record['frozen_inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Accepted input changed: '+name)
    for path,key in [(BASE,'baseline_sha256'),(PUBLIC_BASE,'prior_public_sha256'),(GRAPH,'production_sha256')]:
        if sha(path) != record[key]:
            raise ValueError('Accepted graph/archive hash differs: '+str(path))
    verify_accepted(read(GRAPH),expected)
    if read(OUT/'coverage-current.json') != coverage(expected):
        raise ValueError('Accepted coverage ledger differs from reviewed transformation')
    if (OUT/'manifest.json').is_file():
        for name,digest in read(OUT/'manifest.json')['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name) != digest:
                raise ValueError('Acceptance manifest mismatch: '+name)
    errors,warnings = candidate.validate_graph(expected,read(ROOT/'seminar-pathways.json'))
    print(serial(dict(revision='1.123',errors=errors,warnings=warnings,
                     totals={k:len(expected[k]) for k in ('nodes','edges','sources','people')})),end='')


if __name__ == '__main__':
    main()
