#!/usr/bin/env python3
"""Verify the accepted import, immutable staging evidence and generated public data."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.apply_promotion_batch import transform, sha, read, PACKET, OUT
from scripts.validate_graph import validate


def audit():
    acceptance=read(OUT/'acceptance.json')
    before=read(ROOT/acceptance['baseline'])
    after=read(ROOT/'historiography-1920-2000.json')
    assert sha(ROOT/acceptance['baseline'])==acceptance['baseline_sha256']
    assert sha(ROOT/'historiography-1920-2000.json')==acceptance['production_graph_sha256']
    assert sha(PACKET/'batch.json')==acceptance['research_packet_sha256']
    assert sha(PACKET/'manifest.json')==acceptance['research_manifest_sha256']
    proposed=read(PACKET/'node-proposals.json')['proposals']
    assert after==transform(before,read(PACKET/'batch.json'),proposed), 'Import does not match reviewed transformation'
    for key in ['nodes','edges','sources']:
        assert after[key][:len(before[key])]==before[key], 'Earlier records changed: '+key
    protected=set(before)-{'nodes','edges','sources','people','revision_history'}
    assert all(before[k]==after[k] for k in protected)
    assert after['revision_history'][:-1]==before['revision_history']
    original={p['id']:p for p in before['people']}
    promoted=set(acceptance['node_ids'])
    for p in after['people']:
        expected=dict(original[p['id']])
        if p['id'] in promoted: expected['node_id']=p['id']
        assert p==expected
    assert len(after['people'])==len(before['people'])
    errors,warnings=validate(after,read(ROOT/'seminar-pathways.json'))
    assert not errors, errors
    assert warnings==validate(before,read(ROOT/'seminar-pathways.json'))[1], warnings
    # Research manifests remain historical. Resolve their graph/browser inputs
    # against preserved baseline bytes, never rewrite their hashes to this release.
    for name,expected in read(PACKET/'manifest.json')['files'].items():
        actual=ROOT/acceptance['baseline'] if name=='historiography-1920-2000.json' else ROOT/name
        assert sha(actual)==expected, name
    baseline=read(ROOT/'data/extension-2026/baseline.json')
    for name,expected in baseline['browser_asset_hashes'].items():
        actual=ROOT/acceptance['browser_baseline_archive']/Path(name).relative_to('docs')
        assert sha(actual)==expected, name
    if '--check-public' in sys.argv:
        public=read(ROOT/'docs/data/graph.json')
        for key in ['nodes','edges','sources','claim_catalogue','revision_history']:
            assert public[key]==after[key], 'Public mismatch: '+key
        for name in ['app.js','core.mjs','field.mjs','styles.css','index.html']:
            assert (ROOT/'site'/name).read_bytes()==(ROOT/'docs'/name).read_bytes()
    print('Revision 1.119: 124 nodes, 761 teaching edges, 840 sources, 829 shared people; 7 works and 18 historical claims (17 accepted, 1 provisional).')
    print('Prior records, roster/strand contexts, journal catalogue, research packet, and archived graph/browser baselines preserved.')
    print('Public data verified.' if '--check-public' in sys.argv else 'Website rebuild is assigned to Fable; public build not required by this data audit.')


if __name__=='__main__':
    audit()
