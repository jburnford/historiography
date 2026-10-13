"""Adapt the frozen borderlands/disability packet to the current graph, without accepting it."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_digital_release_candidate import audit, project, serial

PACKET = ROOT / 'data/extension-2026/borderlands-disability-08'
OUT = ROOT / 'data/extension-2026/borderlands-release-14'
GRAPH = ROOT / 'historiography-1920-2000.json'
# Candidate 14 was prepared against revision 1.127. Later accepted revisions must not change it,
# so it reads that exact graph: the current file while it still matches, else the 1.127 snapshot
# (drafts/, or git history), verified by hash.
PINNED_SHA = '29d9d4e0a2c201434e21e1d6ec27695e75b892c0f5f8a12df1ec835e5f7441ac'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_graph():
    if sha(GRAPH) == PINNED_SHA:
        return read(GRAPH)
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from build_site import load_baseline
    graph, _ = load_baseline(dict(baseline_graph='drafts/historiography-1920-2000.v1.127.json', baseline_sha256=PINNED_SHA))
    if graph is None:
        raise ValueError('Revision 1.127 graph unavailable')
    return graph


def outputs():
    before, batch = baseline_graph(), read(PACKET / 'batch.json')
    entities, claims, sources = (deepcopy(batch[k]) for k in ('entities', 'claims', 'source_records'))
    previous = {p['id']: p for p in before['people']}
    additions = []
    for e in entities:
        if e['type'] != 'person':
            continue
        pid = e['id'].split(':', 1)[1]
        names = [p['id'] for p in before['people'] if p['label'].casefold() == e['label'].casefold()]
        if (names and names != [pid]) or (pid in previous and previous[pid]['label'] != e['label']):
            raise ValueError('Identity requires reconciliation: ' + e['id'])
        e.update(legacy_person_id=pid, identity_status='existing_local_person' if pid in previous else 'proposed_local_person')
        if pid not in previous:
            additions.append(dict(id=pid, label=e['label'], identity_note='Proposed local credited contributor; no external identity or demographic inference.'))
    proposals = read(PACKET / 'source-proposals.json')
    smap = {s['claim_source_record_id']: s['id'] for s in proposals}
    graph_sources = deepcopy(proposals)
    for s in graph_sources:
        limits = list(dict.fromkeys(ev['limitation'] for c in claims for ev in c['evidence'] if ev['source_record_id'] == s['claim_source_record_id']))
        s['scope_note'] = ' '.join(limits)
    nodes = []
    for draft in read(PACKET / 'entry-proposals.json'):
        node = deepcopy(draft['node'])
        dated = []
        for strand in node['strands']:
            for year in strand.pop('intervention_years'):
                selected = [c for c in claims if c['id'] in strand['claim_ids'] and c['intervention_year'] == year]
                row = deepcopy(strand)
                row.update(id=strand['id'] + '_' + str(year), intervention_year=year,
                           claim_ids=[c['id'] for c in selected],
                           focus=' '.join(c['statement'] + ' ' + c['qualification'] for c in selected),
                           source_ids=list(dict.fromkeys(smap[ev['source_record_id']] for c in selected for ev in c['evidence'])))
                dated.append(row)
        years = sorted({s['work_publication_year'] for s in dated})
        node.update(strands=dated,
                    date_span=dict(start=min(years), end=max(years), start_kind='earlier_roots', end_kind='unstated', precision='year',
                                   basis='Selected work publications only; neither endpoint defines the field’s existence.'),
                    extension_coverage=dict(status='release_candidate', baseline_through=2000, research_cutoff=batch['research_cutoff'],
                                            field_review_complete=False, publication_years=years, work_ids=node['work_ids'], claim_ids=node['claim_ids']))
        node['source_ids'] = list(dict.fromkeys(node['source_ids'] + [smap[s['id']] for s in sources if s.get('describes_work') in node['work_ids']]))
        nodes.append(node)
    scope = deepcopy(before['scope']['extension'])
    scope.update(status='release_candidate', field_ids=scope['field_ids'] + [n['id'] for n in nodes],
                 candidate_record=str((OUT / 'candidate.json').relative_to(ROOT)),
                 note='Unapplied borderlands/disability preview alongside four accepted partial extensions. Field boundaries, roots and coverage remain under review.')
    candidate = dict(schema_version='extension_release_candidate/1', status='prepared_not_applied',
                     baseline_revision=before['revision_history'][-1]['version'], baseline_sha256=PINNED_SHA,
                     people_additions=additions, source_additions=graph_sources, node_additions=nodes,
                     catalogue_additions=dict(entities=entities, claims=claims, source_records=sources),
                     source_id_map=smap, extension_scope=scope, previous_extension_scope=before['scope']['extension'])
    after = project(before, candidate)
    errors, warnings = audit(before, after, batch, candidate)
    if errors:
        raise ValueError('\n'.join(errors))
    decisions = dict(status='needs_review', production_imports=0,
        fields=[dict(entry_id=n['id'], status='needs_review', requirements=[
            'Review earlier roots, regional coverage and field boundaries.',
            'Review each bounded attribution and its witness, including abstract-only evidence.',
            'Review new people and translation credits.',
            'Choose landing-family placements and evidence crosswalks before production integration.']) for n in nodes],
        claims=[dict(claim_id=c['id'], decision='needs_review', evidence_scopes=[ev['check_status'] for ev in c['evidence']],
                     qualification=c.get('qualification'), rationale=c['review']['rationale']) for c in claims])
    inputs = [GRAPH, PACKET / 'batch.json', PACKET / 'entry-proposals.json', PACKET / 'source-proposals.json',
              ROOT / 'ontology/contract-v0.2.json', Path(__file__).resolve()]
    summary = dict(status='prepared_not_applied', production_imports=0, date='2026-10-10', errors=errors, warnings=warnings,
                   baseline_revision=candidate['baseline_revision'], baseline_sha256=candidate['baseline_sha256'],
                   inputs={str(p.relative_to(ROOT)): PINNED_SHA if p == GRAPH else sha(p) for p in inputs},
                   entries=len(nodes), works=sum(e['type']=='work' for e in entities), claims=len(claims),
                   source_records=len(sources), new_people=len(additions), new_strands=sum(len(n['strands']) for n in nodes),
                   historical_evidence=dict(Counter(ev['check_status'] for c in claims if c['predicate'] not in ('authored','realizes') for ev in c['evidence'])),
                   family_crosswalk='pending; the preview uses existing production evidence only',
                   preservation='Exact old nodes, relationships, people, sources, catalogue and 2000-baseline pointers. Frozen packet and all citation scopes unchanged.')
    return {'candidate.json': candidate, 'review-decisions.json': decisions, 'summary.json': summary}, after


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--preview', type=Path, help='Write an unpublished graph JSON for the existing site builder')
    args = ap.parse_args()
    generated, after = outputs()
    if args.check:
        for name, value in generated.items():
            if (OUT / name).read_text() != serial(value):
                raise ValueError('Candidate reconstruction differs: ' + name)
    else:
        if (OUT / 'summary.json').exists():
            raise ValueError('Candidate already exists; use --check')
        OUT.mkdir(parents=True, exist_ok=True)
        for name, value in generated.items():
            (OUT / name).write_text(serial(value))
    if args.preview:
        args.preview.write_text(serial(after))
    print('Borderlands/disability: exact candidate reconstructed; 0 errors; no production import')


if __name__ == '__main__':
    main()
