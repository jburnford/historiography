"""Verify frozen reading data and prospective bridges; writes reports only."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent

def read(path):return json.loads(path.read_text())
def sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--public-only',action='store_true');args=parser.parse_args()
    baseline=read(HERE/'baseline.json');candidate=read(HERE/'candidate-links.json');registry=read(HERE/'candidate-reviewed-source-ids.json')
    review=read(ROOT/'data/dissertation-layer/reviews/remaining-canon-2026-10-25.json');counts=read(HERE/'count-witnesses.json')
    site=ROOT/'data/dissertation-layer/site';index=read(site/'index.json');public=read(site/'links.json');actual=read(ROOT/'data/dissertation-layer/links.json')
    indexed={r['key']:r for r in index['sources']};exported='karl_marx' in public['people']
    assert len(candidate['people'])==review['expected_profiles']
    assert registry['sources'][:18]==baseline['registry']['sources']
    assert len(registry['sources'])==22
    for field in ('entries','entry_comparisons','person_comparisons'):
        assert candidate[field]==baseline['links'][field],field
        assert actual[field]==baseline['links'][field],field
    assert public['entries']==baseline['public_links']['entries']
    assert public['people']['benedict_anderson']==baseline['public_links']['people']['benedict_anderson']
    for pid,row in baseline['links']['people'].items():
        assert candidate['people'][pid]==row,pid
        assert actual['people'][pid]==row,pid
        assert public['people'][pid]==baseline['public_links']['people'][pid],pid
    assert candidate['people']['henri_lefebvre']==baseline['links']['people']['henri_lefebvre']
    assert sha({k:v for k,v in index.items() if k not in ('sources','reviewed_selection_count')})==baseline['index_context_sha256']
    exception_sources={p['source']:p['verified_work_credits'][0]['work_id'] for p in review['people']
                       if p['verified_work_credits'][0]['source_scope']=='reviewed_counts_only_exception'}
    expected_exceptions={'P:giddens|anthony','P:freud|sigmund','P:adorno|theodor w','P:goody|jack'}
    assert set(exception_sources)==expected_exceptions
    shards={};works_changed=[]
    for old in baseline['sources']:
        row=old['index'];key=row['key'];assert indexed[key]==row,key
        assert index['sources'][old['index_position']]==row,key
        if row['asset'] not in shards:shards[row['asset']]=read(site/row['asset'])
        source=shards[row['asset']]['sources'][str(row['id'])]
        assert sha({k:source[k] for k in ('n','series','n_region')})==old['numeric_sha256'],key
        assert sha({k:v for k,v in source.items() if k!='works'})==old['source_without_works_sha256'],key
        expected=[indexed[exception_sources[key]]['id']] if exported and key in exception_sources else old['work_ids']
        assert source['works']==expected,key
        if source['works']!=old['work_ids']:works_changed.append(key)
    assert set(works_changed)==(expected_exceptions if exported else set())
    graph=read(ROOT/'historiography-1920-2000.json');people={p['id']:p for p in graph['people']};nodes={n['id']:n for n in graph['nodes']}
    reviewed_ids={p['person_id'] for p in review['people']};assert len(reviewed_ids)==review['target_people']
    new_keys=set(candidate['people'])-set(baseline['links']['people'])
    assert new_keys==reviewed_ids-{'henri_lefebvre'}
    assert len(new_keys)==review['new_people_links']
    for row in review['people']:
        pid=row['person_id'];path=ROOT/row['biography_packet'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['biography_packet_sha256']
        packet=read(path);assert packet['node']['id']==pid==packet['people_update']['id']
        accepted=row['accepted_credit_witness'];accepted_path=ROOT/accepted['packet']
        assert hashlib.sha256(accepted_path.read_bytes()).hexdigest()==accepted['packet_sha256']
        acceptance_path=ROOT/accepted['acceptance_record']
        assert hashlib.sha256(acceptance_path.read_bytes()).hexdigest()==accepted['acceptance_record_sha256']
        acceptance=read(acceptance_path);assert acceptance['packet_sha256']==accepted['packet_sha256']
        accepted_node=next(n for n in read(accepted_path)['nodes'] if n['id']==pid)
        accepted_events={e['id']:e for e in accepted_node['chronology']['events']}
        people.setdefault(pid,dict(id=pid,label=packet['node']['label']));nodes.setdefault(pid,packet['node'])
        if packet['people_update'].get('new'):assert people[pid]['label']==packet['node']['label'],pid
        assert row['frozen_provisional_dated_first_author_count']==counts['sources'][row['source']]['n']
        assert candidate['people'][pid]['source']==row['source']
        for work in row['verified_work_credits']:
            assert work['release_metadata']['first_author_key']==row['source'][2:]
            assert work['biography_events'] and work['primary_evidence'],(pid,work['work_id'])
            assert all(accepted_events[e['id']]==e for e in work['biography_events'])
            assert all(w['url'].startswith(('https://','http://')) for w in work['primary_evidence'])
    hahn=next(p for p in review['people'] if p['person_id']=='steven_hahn')
    assert hahn['eligibility_count']==103 and hahn['frozen_provisional_dated_first_author_count']==121
    assert '103' in candidate['people']['steven_hahn']['review_note'] and '121' in candidate['people']['steven_hahn']['review_note']
    witness=counts['hahn_eligibility'];prior=read(ROOT/witness['witness']);hahn_record=next(r for r in prior['records'] if r['source_key']=='P:hahn|steven c')
    assert witness['dated_dissertation_ids']==hahn_record['confirmed_selected_dissertation_ids']
    citation_sets=read(HERE.parent/'classification-identity-review/dated-citation-sets.json')['per_work']
    assert len(set().union(*(set(citation_sets[k]) for k in witness['selected_work_ids'])))==103
    if review['target_people']==42:
        final_sets=read(HERE.parent/'final-identity-pass/dated-citation-sets.json')
        for identity in counts['final_identity_eligibility']:
            expected=102 if identity['name']=='Charles Taylor' else 101
            raw=148 if identity['name']=='Charles Taylor' else 114
            ids=set().union(*(set(final_sets['per_work'][k]) for k in identity['positive_work_ids']))
            assert len(ids)==expected and ids==set(identity['dated_dissertation_ids'])
            assert ids==set(final_sets['per_person'][identity['name']]['confirmed_selected_dissertation_ids'])
            assert identity['provisional_key_count']==raw
            pid='charles_taylor' if identity['name']=='Charles Taylor' else 'peter_brown'
            assert str(expected) in candidate['people'][pid]['review_note'] and str(raw) in candidate['people'][pid]['review_note']
        for filename,expected in counts['final_identity_witness_sha256'].items():
            assert hashlib.sha256((HERE.parent/'final-identity-pass'/filename).read_bytes()).hexdigest()==expected
    exact_work_credits=0
    if not args.public_only:
        spec=importlib.util.spec_from_file_location('exporter',ROOT/'scripts/build_dissertation_site.py');exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
        chosen={k for row in candidate['people'].values() for k in row['works']}
        metadata={w['work_id']:w for w in exporter.rows('works') if w['work_id'] in chosen};authors={k:w['first_author_key'] for k,w in metadata.items()}
        data=read(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')
        exporter.add_reviewed_sources(data,candidate,{**graph,'people':list(people.values()),'nodes':list(nodes.values())},metadata,registry)
        by_key={data['labels'][s['id']]['key']:s for s in data['sources']}
        exporter.validate_links(candidate,{**graph,'people':list(people.values()),'nodes':list(nodes.values())},set(by_key),authors)
        for old in baseline['sources']:assert by_key[old['index']['key']]['id']==old['index']['id']
        assert len(data['sources'])==4059
        for filename,expected in counts['source_file_sha256'].items():assert hashlib.sha256((exporter.RELEASE/(filename+'.csv.gz')).read_bytes()).hexdigest()==expected
        exact_work_credits=len(metadata)
    if exported:
        assert len(public['people'])==review['expected_profiles'] and len(index['sources'])==4059 and index['reviewed_selection_count']==22
        for record in registry['sources'][18:]:
            assert index['sources'][record['source_index']]['id']==record['id']
            entry=indexed[record['key']];source=read(site/entry['asset'])['sources'][str(entry['id'])]
            for field in ('n','series','n_region'):assert source[field]==counts['sources'][record['key']][field]
            assert source['analysis_scope']=='counts_only' and source['rows']==[] and source['regional']=={}
    report=dict(status='pass' if not review['unresolved'] else 'pending_witnesses',target_people=review['target_people'],new_profile_links=len(new_keys),
        expected_profiles=review['expected_profiles'],expected_sources=4059,expected_reviewed_exceptions=22,
        old_sources_checked=4055,old_profile_links_preserved=116,old_field_panels_preserved=5,Anderson_personal_comparison_preserved=True,
        old_registry_rows_preserved=18,new_exceptions=[dict(key=r['key'],id=r['id'],source_index=r['source_index'],n=counts['sources'][r['key']]['n']) for r in registry['sources'][18:]],
        accepted_biography_packets_verified=[r['revision'] for r in review['accepted_packets']],
        old_source_work_list_changes=works_changed,exact_release_work_credits_checked=exact_work_credits,hahn_eligibility_subset=103,hahn_provisional_source_count=121,
        additional_identity_eligibility=[dict(name=r['name'],eligibility_subset=r['eligibility_subset'],
            provisional_key_count=r['provisional_key_count'],positive_work_records=len(r['positive_work_ids']))
            for r in counts.get('final_identity_eligibility',[])],
        exported=exported,public_only=args.public_only,unresolved=review['unresolved'])
    (HERE/('public-verification.json' if args.public_only else 'verification.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
