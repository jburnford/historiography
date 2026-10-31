"""Validate this proposal in memory and record preservation evidence; never apply."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.apply_person_entries import Batch, serial
from scripts.source_hosts import findings
from scripts.validate_graph import validate


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cfg = read(HERE/'batch.json')
    before = read(ROOT/'historiography-1920-2000.json')
    packet = read(HERE/'release/editorial-additions.json')
    original = deepcopy(before)
    after = Batch(HERE).transform(before, packet)
    pathways = read(ROOT/'seminar-pathways.json')
    errors, warnings = validate(after, pathways)
    baseline_errors, baseline_warnings = validate(before, pathways)
    bridge = read(HERE/'reading-bridge.json')['rows']
    queue = read(ROOT/'data/field-research/timeline-candidates-2026-10-30/work-queues/batch-1.json')['persons']
    actual_keys = Counter((r['person_id'],r['key']) for r in bridge)
    expected_keys = Counter((p['person_id'],k) for p in queue for k in p['keys_with_counted_works'])
    manifest = read(HERE/'protected-manifest.json')
    protected_changes = [p for p,h in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    doc_files = {str(p.relative_to(ROOT)) for p in (ROOT/'docs').rglob('*') if p.is_file()}
    protected_docs = {p for p in manifest if p.startswith('docs/')}
    old_nodes = {n['id']:n for n in before['nodes']}
    updated_nodes = {n['id']:n for n in after['nodes']}
    roster_counts = Counter(r['node'] for r in packet['roster_additions'])
    groups_exact_except_additions = True
    for pid,node in old_nodes.items():
        candidate = deepcopy(updated_nodes[pid])
        count = roster_counts[pid]
        if count:
            candidate['representative_people'] = candidate['representative_people'][:-count]
        groups_exact_except_additions &= candidate == node
    people_before = {p['id']:p for p in before['people']}
    promoted = {u['id'] for u in packet['people_updates']}
    old_people_preserved = True
    for p in after['people']:
        if p['id'] not in people_before: continue
        candidate=deepcopy(p)
        if p['id'] in promoted:
            candidate.pop('node_id',None)
        old_people_preserved &= candidate == people_before[p['id']]
    bad=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file() or 'research' in path.relative_to(HERE).parts or '__pycache__' in path.parts:
            continue
        if path.suffix not in {'.json','.md','.py'}: continue
        hits=findings(path.read_text())
        if hits: bad.append(dict(path=str(path.relative_to(HERE)),hits=hits))
    # Match tests/test_source_hosts.py's published atlas-table scope. Legacy
    # journal/claim catalogues are unchanged; their wider URL audit is separate.
    candidate_host_hits = findings(json.dumps({k:after[k] for k in ['nodes','edges','sources','people']},ensure_ascii=False))
    living_birth_prose=[]
    for p in cfg['persons']:
        d=read(HERE/p/'entry-draft.json'); ls=read(HERE/p/'life-status.json')
        if not ls.get('death_year'):
            prose=' '.join(d['node'][k] for k in ['description','scope_note','date_label','representative_figures_and_works'])
            if re.search(r'\b'+str(ls['birth_year'])+r'\b',prose): living_birth_prose.append(p)
    all_contexts_accounted=all(set(p['proposed_context_ids']) <= set(read(HERE/p['person_id']/'research-notes.json')['context_decisions']) for p in queue)
    checks=dict(baseline_has_no_errors=not baseline_errors, transform_does_not_mutate_input=before==original,
                old_edges_byte_equivalent=serial(before['edges'])==serial(after['edges'][:len(before['edges'])]),
                old_sources_byte_equivalent=serial(before['sources'])==serial(after['sources'][:len(before['sources'])]),
                old_nodes_exact_except_roster_appends=groups_exact_except_additions,
                old_people_exact_except_entry_links=old_people_preserved,
                prior_revision_history_exact=after['revision_history'][:-1]==before['revision_history'],
                unrelated_top_level_tables_exact=all(after[k]==v for k,v in before.items() if k not in ['nodes','people','edges','sources','revision_history']),
                reading_bridge_exact=actual_keys==expected_keys,
                ten_queue_entries_exact=set(cfg['persons'])=={p['person_id'] for p in queue}=={n['id'] for n in packet['nodes']},
                every_proposed_context_reviewed=all_contexts_accounted,
                separate_life_records=all((HERE/p/'life-status.json').is_file() for p in cfg['persons']),
                no_living_birth_year_in_entry_prose=not living_birth_prose,
                no_disallowed_route_in_drafts=not bad,
                no_disallowed_route_in_candidate_core_tables=not candidate_host_hits,
                canonical_and_docs_bytes_unchanged=not protected_changes,
                docs_file_set_unchanged=doc_files==protected_docs,
                no_new_structural_warnings=Counter(warnings)==Counter(baseline_warnings),
                no_acceptance_or_new_snapshot=(not (ROOT/'data/production-batches'/cfg['batch_dir']/'acceptance.json').exists()
                    and not (ROOT/f'drafts/historiography-1920-2000.v{cfg["revision"]}.json').exists()))
    report=dict(status='passed' if not errors and all(checks.values()) else 'failed',
                mode='Build plus in-memory transformation only. Independent review pending; no apply, site build, commit or push.',
                baseline_revision=cfg['baseline_revision'],revision=cfg['revision'],errors=errors,
                warnings=warnings,new_warnings=list((Counter(warnings)-Counter(baseline_warnings)).elements()),checks=checks,
                counts_before={k:len(before[k]) for k in ['nodes','people','edges','sources']},
                counts_candidate={k:len(after[k]) for k in ['nodes','people','edges','sources']},
                publication_events=sum(len(n['chronology']['events']) for n in packet['nodes']),
                reading_bridge_rows=len(bridge),roster_additions=len(packet['roster_additions']),
                packet_sha256=sha(HERE/'release/editorial-additions.json'),canonical_sha256=sha(ROOT/'historiography-1920-2000.json'),
                candidate_sha256=hashlib.sha256(serial(after).encode()).hexdigest(),protected_changes=protected_changes,
                source_policy_scope='All owned text drafts plus candidate nodes, edges, sources and people, matching tests/test_source_hosts.py. Unchanged legacy journal/claim catalogues are outside that test scope.',
                source_policy_findings=bad,candidate_core_source_policy_findings=candidate_host_hits,living_birth_prose_findings=living_birth_prose)
    (HERE/'validation.json').write_text(serial(report))
    print(report['status'],json.dumps(checks,indent=2))
    if report['status']!='passed': raise SystemExit(1)


if __name__=='__main__':
    main()
