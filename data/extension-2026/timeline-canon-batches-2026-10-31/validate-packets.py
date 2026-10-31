"""Simulate the three ordered proposals; never write graph, site or acceptance."""
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
from scripts.chronology import validate_chronologies


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def review_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def text_findings(folder):
    bad=[]
    for p in folder.rglob('*'):
        if not p.is_file() or any(x in p.relative_to(folder).parts for x in ['research','__pycache__']):
            continue
        if p.suffix not in {'.json','.md','.py'}:
            continue
        # A failed report records paths/counts, never repeats a prohibited route.
        n=len(findings(p.read_text()))
        if n:bad.append(dict(path=str(p.relative_to(ROOT)),count=n))
    return bad


def main():
    production=read(ROOT/'historiography-1920-2000.json')
    assert production['revision_history'][-1]['version']=='1.231', 'Rebase and renumber after production advances.'
    pathways=read(ROOT/'seminar-pathways.json')
    candidate=production
    dependencies=[]
    reports=[]
    audit=read(HERE/'quality-review/final-audit.json')
    audit_rows={r['person_id']:r for r in audit['people']}
    progress=read(HERE/'quality-review/progress.json')
    assert len(audit_rows)==len(audit['people'])==32
    assert set(audit_rows)=={r['person_id'] for r in progress['people']}
    shared_bad=text_findings(HERE)
    for number in [1,2,3]:
        folder=ROOT/f'data/extension-2026/timeline-canon-batch{number}-2026-10-31'
        cfg=read(folder/'batch.json');packet=read(folder/'release/editorial-additions.json')
        queue=read(ROOT/f'data/field-research/timeline-candidates-2026-10-30/work-queues/batch-{number}.json')['persons']
        before=candidate; original=deepcopy(before)
        candidate=Batch(folder).transform(before,packet)
        baseline_errors,baseline_warnings=validate(before,pathways)
        errors,warnings=validate(candidate,pathways)
        nodes_before={n['id']:n for n in before['nodes']}
        nodes_after={n['id']:n for n in candidate['nodes']}
        roster_counts=Counter(r['node'] for r in packet.get('roster_additions',[]))
        old_nodes_preserved=True
        for pid,n in nodes_before.items():
            restored=deepcopy(nodes_after[pid])
            if roster_counts[pid]:restored['representative_people']=restored['representative_people'][:-roster_counts[pid]]
            old_nodes_preserved &= restored==n
        people_before={p['id']:p for p in before['people']}
        updated={p['id'] for p in packet['people_updates']}
        old_people_preserved=True
        for person in candidate['people']:
            if person['id'] not in people_before:continue
            restored=deepcopy(person);previous=people_before[person['id']]
            if person['id'] in updated:
                if 'node_id' in previous:restored['node_id']=previous['node_id']
                else:restored.pop('node_id',None)
            old_people_preserved &= restored==previous
        bridge=read(folder/'reading-bridge.json')['rows']
        actual=Counter((r['person_id'],r['key']) for r in bridge)
        expected=Counter((p['person_id'],k) for p in queue for k in p['keys_with_counted_works'])
        manifest=read(folder/'protected-manifest.json')
        protected_changes=[p for p,h in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
        docs={str(p.relative_to(ROOT)) for p in (ROOT/'docs').rglob('*') if p.is_file()}
        bad=text_findings(folder)+shared_bad
        core_hits=findings(json.dumps({k:candidate[k] for k in ['nodes','edges','sources','people']},ensure_ascii=False))
        no_birth=[];missing_life=[];count_in_prose=[];contexts=True;releases_exact=True;quality_exact=True
        for person in queue:
            pid=person['person_id'];d=read(folder/pid/'entry-draft.json')
            notes=read(folder/pid/'research-notes.json');life=read(folder/pid/'life-status.json')
            prose=' '.join(d['node'][k] for k in ['description','scope_note','date_label','representative_figures_and_works'])
            if not life.get('death_year') and life.get('birth_year') and re.search(r'\b'+str(life['birth_year'])+r'\b',prose):no_birth.append(pid)
            if not life.get('sources') or (not life.get('birth_year') and pid!='kathleen_wilson'):missing_life.append(pid)
            if re.search(r'\b(?:PhDs?|citation count|most[- ]cited|cited by)\b',prose,re.I):count_in_prose.append(pid)
            contexts &= set(person['proposed_context_ids']) <= set(notes['context_decisions'])
            releases_exact &= d['node']==nodes_after[pid]
            reviewed=audit_rows[pid]
            quality_exact &= (reviewed['status']==d.get('quality_review',{}).get('status')=='researcher_review_complete'
                and reviewed['reviewed_content_sha256']==review_hash({k:d[k] for k in ['node','proposed_edges','new_sources','roster_additions']})
                and reviewed['context_decisions_sha256']==review_hash(notes['context_decisions'])
                and reviewed['life_evidence_sha256']==review_hash(life)
                and bool(reviewed['audit_note']) and bool(reviewed['passage_reads']) and bool(reviewed['remaining_limits']))
        source_ids={s['id'] for s in candidate['sources']}
        valid_new_sources=all(set(n['source_ids'])<=source_ids for n in packet['nodes'])
        edge_lookup={e['proposal_id']:e for e in packet['edges']}
        roster_support=all(r['proposal_id'] in edge_lookup and edge_lookup[r['proposal_id']]['source']==r['row']['person_id'] and edge_lookup[r['proposal_id']]['target']==r['node'] and edge_lookup[r['proposal_id']]['relationship_kind']=='contribution' and set(r['row']['source_ids'])<=source_ids for r in packet.get('roster_additions',[]))
        no_application=not (ROOT/'data/production-batches'/cfg['batch_dir']/'acceptance.json').exists() and not (ROOT/f'drafts/historiography-1920-2000.v{cfg["revision"]}.json').exists()
        checks=dict(baseline_has_no_errors=not baseline_errors,
            transform_does_not_mutate_input=before==original,
            old_edges_byte_equivalent=serial(before['edges'])==serial(candidate['edges'][:len(before['edges'])]),
            old_sources_byte_equivalent=serial(before['sources'])==serial(candidate['sources'][:len(before['sources'])]),
            old_nodes_exact_except_roster_appends=old_nodes_preserved,
            old_people_exact_except_entry_links=old_people_preserved,
            prior_revision_history_exact=candidate['revision_history'][:-1]==before['revision_history'],
            unrelated_top_level_tables_exact=all(candidate[k]==v for k,v in before.items() if k not in ['nodes','people','edges','sources','revision_history']),
            queue_entries_exact=set(cfg['persons'])=={p['person_id'] for p in queue}=={n['id'] for n in packet['nodes']},
            release_nodes_match_drafts=releases_exact,
            reading_bridge_exact=actual==expected,
            every_proposed_context_reviewed=contexts,
            researcher_substantive_audit_matches_final_content=quality_exact,
            separate_life_evidence_complete=not missing_life,
            no_living_birth_year_in_entry_prose=not no_birth,
            no_selection_count_in_entry_prose=not count_in_prose,
            new_entry_source_references_resolve=valid_new_sources,
            roster_appends_have_supported_contribution=roster_support,
            no_disallowed_route_in_owned_text=not bad,
            no_disallowed_route_in_candidate_core_tables=not core_hits,
            canonical_and_docs_bytes_unchanged=not protected_changes,
            docs_file_set_unchanged=docs=={p for p in manifest if p.startswith('docs/')},
            no_new_structural_warnings=Counter(warnings)==Counter(baseline_warnings),
            chronology_valid=not validate_chronologies(candidate),
            no_acceptance_or_new_snapshot=no_application)
        if number==3:
            checks['greenblatt_is_individual_theorist']=nodes_after['stephen_greenblatt']['entry_type']=='Individual theorist' and nodes_after['stephen_greenblatt']['layer']=='intellectual_connections'
            checks['davis_is_historian']=nodes_after['mike_davis']['entry_type']=='Individual historian'
            checks['wilson_has_no_invented_wikidata_item']=read(folder/'kathleen_wilson/research-notes.json')['identity']['qid'] is None
        report=dict(status='passed' if not errors and all(checks.values()) else 'failed',
            mode='Ordered in-memory simulation of unaccepted proposals; independent review pending. No graph/site application, acceptance, commit or push.',
            substantive_research_review='All assigned entries strengthened and self-audited; independent Claude review remains pending.',
            baseline_revision=cfg['baseline_revision'],revision=cfg['revision'],
            unaccepted_dependencies=deepcopy(dependencies),
            errors=errors,warnings=warnings,new_warnings=list((Counter(warnings)-Counter(baseline_warnings)).elements()),checks=checks,
            counts_before={k:len(before[k]) for k in ['nodes','people','edges','sources']},
            counts_candidate={k:len(candidate[k]) for k in ['nodes','people','edges','sources']},
            publication_events=sum(len(n['chronology']['events']) for n in packet['nodes']),reading_bridge_rows=len(bridge),
            roster_additions=len(packet.get('roster_additions',[])),new_people=len(packet.get('new_people',[])),new_edges=len(packet['edges']),new_sources=len(packet['sources']),
            packet_sha256=sha(folder/'release/editorial-additions.json'),canonical_sha256=sha(ROOT/'historiography-1920-2000.json'),
            simulated_baseline_sha256=hashlib.sha256(serial(before).encode()).hexdigest(),candidate_sha256=hashlib.sha256(serial(candidate).encode()).hexdigest(),
            protected_changes=protected_changes,source_policy_findings=bad,candidate_core_source_policy_finding_count=len(core_hits),
            source_policy_scope='All four owned packet/control directories, plus candidate nodes/edges/sources/people matching the existing test. Unchanged legacy journal/claim catalogues excluded.',
            living_birth_prose_findings=no_birth,missing_life_evidence=missing_life,selection_count_prose_findings=count_in_prose)
        (folder/'validation.json').write_text(serial(report))
        print(f"Batch {number}: {report['status']}; {len(errors)} errors, {len(report['new_warnings'])} new warnings; {report['counts_candidate']}")
        dependencies.append(dict(packet=str(folder.relative_to(ROOT)),revision=cfg['revision'],release_sha256=report['packet_sha256']))
        reports.append(dict(packet=str(folder.relative_to(ROOT)),revision=cfg['revision'],status=report['status'],release_sha256=report['packet_sha256']))
    summary=dict(status='passed' if all(r['status']=='passed' for r in reports) else 'failed',production_revision='1.231',candidate_revision='1.234',independent_review='pending Claude acceptance',packets=reports,
        substantive_research_review=audit['status'],researcher_reviewed_entries=len(audit_rows),
        total_entries=sum(len(read(ROOT/r['packet']/'batch.json')['persons']) for r in reports),
        counts_production={k:len(production[k]) for k in ['nodes','people','edges','sources']},counts_combined_candidate={k:len(candidate[k]) for k in ['nodes','people','edges','sources']},
        canonical_sha256=sha(ROOT/'historiography-1920-2000.json'),source_policy_scope='Owned packet/control text plus core atlas tables; no broader legacy catalogue audit claimed.')
    (HERE/'validation.json').write_text(serial(summary))
    if summary['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
