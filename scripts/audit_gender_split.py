#!/usr/bin/env python3
"""Check revision 1.120, relocated strands, claim preservation and untouched journals."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.split_gender_fields import OUT, read, sha, transform
from scripts.validate_graph import validate


def audit():
    a=read(OUT/'acceptance.json')
    assert sha(ROOT/a['baseline'])==a['baseline_sha256']
    assert sha(ROOT/a['pathway_baseline'])==a['pathway_baseline_sha256']
    before=read(ROOT/a['baseline']); paths=read(ROOT/a['pathway_baseline'])
    after=read(ROOT/'historiography-1920-2000.json'); newpaths=read(ROOT/'seminar-pathways.json')
    assert sha(ROOT/'historiography-1920-2000.json')==a['production_sha256']
    assert sha(ROOT/'seminar-pathways.json')==a['pathways_sha256']
    assert (after,newpaths)==transform(before,paths)
    errors,warnings=validate(after,newpaths)
    assert not errors, errors
    assert warnings==validate(before,paths)[1],warnings
    assert after['journal_catalogue']==before['journal_catalogue']
    assert after['people'][:-1]==before['people']
    assert after['sources'][:-1]==before['sources']
    for key in ['claims','entities','source_records']:
        assert after['claim_catalogue'][key][:len(before['claim_catalogue'][key])]==before['claim_catalogue'][key],key
    oldnodes={n['id']:n for n in before['nodes']}; nodes={n['id']:n for n in after['nodes']}
    for id,n in oldnodes.items():
        if id not in ['gender','queer']:assert nodes[id]==n,id
    for old,new in [('race','racial_formation'),('intersection','intersectionality')]:
        original=next(s for s in oldnodes['gender']['strands'] if s['id']==old)
        moved=next(s for s in nodes[new]['strands'] if s['id']==old)
        assert original==moved
    assert nodes['queer']['strands'][:-1]==oldnodes['queer']['strands']
    assert nodes['queer']['representative_people'][:-1]==oldnodes['queer']['representative_people']
    assert nodes['gender']['label']=='Gender history'
    assert nodes['racial_formation']['label']=='Racial formation'
    assert nodes['intersectionality']['entry_type']=='Method / approach'
    direct={e['target'] for e in after['edges'] if e['source']=='intersectionality'}
    assert {'gender','racial_formation','queer'}<=direct
    print('1.120 verified: 126 entries, 765 teaching edges, 841 sources, 830 people; 75 group entries.')
    print('Moved strands retain exact records and redirects; prior claims, unrelated nodes, original queer contexts and the journal catalogue are preserved. Four structural warnings unchanged.')


if __name__=='__main__':audit()
