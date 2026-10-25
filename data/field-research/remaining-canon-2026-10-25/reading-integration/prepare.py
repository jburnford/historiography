"""Prepare all remaining reading bridges; never change live links or exports."""
from collections import defaultdict
from copy import deepcopy
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RELEASE = ROOT/'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'
REVIEW = ROOT/'data/dissertation-layer/reviews/remaining-canon-2026-10-25.json'
CHOICES = {
'pierre_bourdieu':['W:bourdieu|distinction'],
'jurgen_habermas':['W:habermas|structural transformation of the public sphere'],
'hannah_arendt':['W:arendt|origins of totalitarianism'],
'judith_butler':['W:butler|gender trouble'],
'david_harvey':['W:harvey|condition of postmodernity'],
'maurice_halbwachs':['W:halbwachs|on collective memory'],
'mary_louise_pratt':['W:pratt|imperial eyes'],
'homi_k_bhabha':['W:bhabha|location of culture'],
'rogers_brubaker':['W:brubaker|citizenship and nationhood in france and germany'],
'ernest_gellner':['W:gellner|nations and nationalism'],
'anne_mcclintock':['W:mcclintock|imperial leather'],
'marcel_mauss':['W:mauss|gift'],
'mary_douglas':['W:douglas|purity and danger'],
'anthony_giddens':['W:giddens|consequences of modernity'],
'gilles_deleuze':['W:deleuze|thousand plateaus'],
'anthony_d_smith':['W:smith|ethnic origins of nations'],
'max_weber':['W:weber|protestant ethic and the spirit of capitalism'],
'paul_ricoeur':['W:ricoeur|temps et recit'],
'karl_marx':['W:marx|capital'],
'stuart_hall':['W:hall|cultural identity and diaspora|a'],
'walter_benjamin':['W:benjamin|arcades project'],
'henri_lefebvre':['W:lefebvre|production of space','W:lefebvre|production de lespace'],
'raymond_williams':['W:williams|keywords'],
'erving_goffman':['W:goffman|presentation of self in everyday life'],
'arjun_appadurai':['W:appadurai|social life of things'],
'paul_gilroy':['W:gilroy|black atlantic'],
'emile_durkheim':['W:durkheim|division du travail social'],
'sigmund_freud':['W:freud|three essays on the theory of sexuality'],
'samuel_huntington':['W:huntington|soldier and the state'],
'giorgio_agamben':['W:agamben|homo sacer'],
'theodor_w_adorno':['W:adorno|dialectic of enlightenment'],
'michel_de_certeau':['W:de certeau|practice of everyday life'],
'charles_tilly':['W:tilly|coercion capital and european states ad 990 1992'],
'timothy_mitchell':['W:mitchell|rule of experts'],
'jack_goody':['W:goody|development of the family and marriage in europe'],
'tzvetan_todorov':['W:todorov|conquest of america'],
'steven_hahn':['W:hahn|nation under our feet','W:hahn|roots of southern populism'],
'partha_chatterjee':['W:chatterjee|nation and its fragments'],
'alessandro_portelli':['W:portelli|death of luigi trastulli and other stories'],
'alexis_de_tocqueville':['W:tocqueville|democracy in america'],
'charles_taylor':['W:taylor|sources of the self'],
'peter_brown':['W:brown|cult of the saints'],
}
EXCEPTIONS = {'anthony_giddens','sigmund_freud','theodor_w_adorno','jack_goody'}
NOTES = {
'pierre_bourdieu':'Richard Nice’s English translation and the French original remain separately credited and dated.',
'jurgen_habermas':'The English Structural Transformation translation is distinct from the 1962 German original and other language keys.',
'maurice_halbwachs':'On Collective Memory is edited and translated selections, credited to Lewis A. Coser; it is not silently equated with one complete French volume.',
'mary_louise_pratt':'Mary Louise Pratt is identified through Imperial Eyes; painter Mary Pratt and unrelated titles are not resolved or merged by this link.',
'marcel_mauss':'The frozen 1990 Gift manifestation is associated with W. D. Halls’s translation and Mary Douglas’s foreword; Jane I. Guyer’s expanded 2016 edition in the biography remains distinct. The 34-key count is not declared to be Guyer-only.',
'gilles_deleuze':'A Thousand Plateaus is joint work with Félix Guattari, translated with a foreword by Brian Massumi. The 1980 French original and 1987 English translation remain separate facts.',
'max_weber':'The original 1904–05 Protestant Ethic and 1920 revision remain distinct; this frozen work-key count does not isolate one version or translation.',
'paul_ricoeur':'Temps et récit is a normalized work key that may pool volumes or editions. Its count is not assigned solely to volume I; the 1983, 1984 and 1985 volumes remain separate dated facts.',
'karl_marx':'Capital is a normalized work key that may pool volumes or editions. Its count is not assigned solely to the biography’s 1867 volume I; later editorial and translation credits are not inferred from the key.',
'stuart_hall':'Cultural Identity and Diaspora is Hall’s chapter in the collection edited by Jonathan Rutherford, rather than sole authorship of the entire collection.',
'walter_benjamin':'The posthumous Arcades Project retains Rolf Tiedemann’s editorial role and Howard Eiland and Kevin McLaughlin’s English translation credit.',
'arjun_appadurai':'The Social Life of Things is an edited collection: Appadurai’s editorial role and his own introduction are distinct from the other contributors’ chapters.',
'sigmund_freud':'Three Essays is identified through its named title; the release’s 1962 manifestation does not replace the original 1905 publication or identify every cited translation.',
'theodor_w_adorno':'Dialectic of Enlightenment is joint work with Max Horkheimer. The 2002 manifestation credits editor Gunzelin Schmid Noerr and translator Edmund Jephcott; 1944 limited circulation and 1947 revised publication remain separate.',
'michel_de_certeau':'The exact P:certeau namespace and W:de certeau namespace are retained. The parallel W:certeau Practice key is not summed or merged. Steven Rendall’s English translation and the French original retain their dates and contributor qualifications.',
'charles_tilly':'The selected frozen key ends AD 990–1992; the biography’s original 1990 title ends AD 990–1990. The extended/revised title and later paperback are distinct manifestations, without changing the frozen release year or assigning all citations to one edition.',
'steven_hahn':'Eligibility rests on an independently sourced, deduplicated union of 103 dissertations citing four positively matched Steven Hahn books. The displayed 121 is the unchanged provisional P:hahn|steven c key, with known foreign-author contamination and unresolved records; it is not a clean 121 for the historian. Steven C. Hahn’s Creek/Mary Musgrove works remain distinct. Selected work counts overlap and are not added.',
'alexis_de_tocqueville':'Democracy in America is the English title concordance for the two-part French work of 1835 and 1840. The frozen key does not isolate one part or one translator’s edition; Mansfield and Winthrop’s roles belong to the separately identified 2000 witness.',
'charles_taylor':'The philosopher’s eligibility is supported by a conservative, deduplicated 102-dissertation union of 17 positively matched work records. The displayed 148 remains the provisional P:taylor|charles bibliography key and includes journalist Charles Taylor’s Radical Tories and unresolved records. The journalist is not merged with the philosopher, and the raw total is not presented as a clean authority count.',
'peter_brown':'The late-antique historian’s eligibility is supported by a conservative, deduplicated 101-dissertation union of positively matched translations and credited chapters. The displayed 114 remains the provisional P:brown|peter bibliography key and includes other-author and unresolved records. Peter Hume Brown’s Scottish-history works remain distinct. Title identity does not certify the completeness of every attributed citation.',
}

def read(path):
    return json.loads(path.read_text())

def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(text):
    text=' '.join(re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()).split())
    return re.sub(r'^(the |a |les |le |la |l )','',text)

def matches(title, label):
    a,b=norm(title.split(':')[0]),norm(label.split(':')[0])
    return min(len(a),len(b))>=3 and (a==b or a.startswith(b+' ') or b.startswith(a+' '))

def main():
    baseline=read(HERE/'baseline.json')
    targets=[]
    for path in sorted(HERE.parent.glob('theory-lane-*.json')):
        for p in read(path)['persons']:
            targets.append({**p,'kind':'theory','queue':str(path.relative_to(ROOT))})
    hpath=HERE.parent/'classification-identity-review/eligible-historian-queue.json'
    for p in read(hpath)['records']:
        targets.append({**p,'person_id':p['resolved_person_id'],'kind':'historian','queue':str(hpath.relative_to(ROOT))})
    extra_path=HERE.parent/'final-identity-pass/additive-queue.json'
    for p in read(extra_path)['records']:
        targets.append({**p,'person_id':p['resolved_person_id'],
            'kind':'theory' if p['layer']=='intellectual_connections' else 'historian',
            'queue':str(extra_path.relative_to(ROOT)),
            'eligibility_count':p['confirmed_selected_person_lower_bound'],
            'eligibility_count_scope':'Conservative deduplicated union of positively matched work records; frozen raw author-key count remains provisional.'})
    assert len(targets)==42 and len({p['person_id'] for p in targets})==42
    assert {p['person_id'] for p in targets}==set(CHOICES)
    missing_packets=[p['person_id'] for p in targets if not list((ROOT/'data/extension-2026').glob('remaining-*/'+p['person_id']+'/entry-draft.json'))]
    if missing_packets:
        print(json.dumps(dict(status='awaiting_biography_packets',target_people=42,expected_profiles=157,missing=missing_packets),indent=2))
        return
    keys={p['source_key'][2:] for p in targets}
    metadata,author_work={},{}
    with gzip.open(RELEASE/'works.csv.gz','rt',encoding='utf8') as f:
        for w in csv.DictReader(f):
            if w['first_author_key'] in keys:
                metadata[w['work_id']]=w
                author_work[w['work_id']]=w['first_author_key']
    selected={k for choices in CHOICES.values() for k in choices}
    extra_hahn=['W:hahn|nation under our feet','W:hahn|roots of southern populism','W:hahn|political worlds of slavery and freedom','W:hahn|nation without borders']
    wanted=selected|set(extra_hahn)
    final_review=read(HERE.parent/'final-identity-pass/review.json')
    identity_positive={r['source_key']:[w['raw_record']['work_id'] for w in r['work_decisions']
        if w['identity_count_decision']=='confirmed_selected_person']
        for r in final_review['records'] if r['source_key'] in ('P:taylor|charles','P:brown|peter')}
    for ids in identity_positive.values():wanted.update(ids)
    eu=set('AT BE BG CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LI LT LU LV MC ME MK MT NL NO PL PT RO RS SE SI SK UA'.split())
    regions=['CA','US','EUROPE','OTHER'];theses={}
    with gzip.open(RELEASE/'dissertations.csv.gz','rt',encoding='utf8') as f:
        for d in csv.DictReader(f):
            if d['in_analysis']=='True':
                y=int(d['year']) if d['year'] else None;c=d['country'];reg=c if c in ('CA','US') else 'EUROPE' if c in eu else 'OTHER'
                period=0 if y is not None and y<1990 else min(7,1+(y-1990)//5) if y else None
                theses[d['dissertation_id']]=(y,period,regions.index(reg))
    raw,dated=defaultdict(set),defaultdict(set)
    with gzip.open(RELEASE/'citations.csv.gz','rt',encoding='utf8') as f:
        for c in csv.DictReader(f):
            tid,wid=c['dissertation_id'],c['work_id']
            if wid not in author_work or tid not in theses:continue
            for key in ['P:'+author_work[wid]]+([wid] if wid in wanted else []):
                raw[key].add(tid)
                if theses[tid][0]:dated[key].add(tid)
    numbers={}
    for key in {'P:'+k for k in keys}|wanted:
        series=[[0]*4 for _ in range(8)]
        for tid in dated[key]:_,p,r=theses[tid];series[p][r]+=1
        numbers[key]=dict(n=len(dated[key]),series=series,n_region={r:sum(row[j] for row in series) for j,r in enumerate(regions)},strict_with_or_without_year=len(raw[key]))
        if key.startswith('W:'):
            numbers[key]['release_metadata']=metadata[key]
            assert len(raw[key])==int(metadata[key]['cited_by_strict_phds']),key
    old_index={s['index']['key']:s['index'] for s in baseline['sources']}
    for key,row in numbers.items():
        if key in old_index:assert row['n']==old_index[key]['n'],key
    hahn_union=set().union(*(dated[k] for k in extra_hahn))
    classified=read(HERE.parent/'classification-identity-review/count-witnesses.json')
    hahn=next(r for r in classified['records'] if r['source_key']=='P:hahn|steven c')
    assert len(hahn_union)==103 and hahn_union==set(hahn['confirmed_selected_dissertation_ids'])
    final_sets=read(HERE.parent/'final-identity-pass/dated-citation-sets.json')['per_person']
    final_identity_counts=[]
    for source,ids in identity_positive.items():
        name='Charles Taylor' if source=='P:taylor|charles' else 'Peter Brown'
        expected=102 if source=='P:taylor|charles' else 101
        union=set().union(*(dated[k] for k in ids))
        assert len(union)==expected and union==set(final_sets[name]['confirmed_selected_dissertation_ids'])
        final_identity_counts.append(dict(name=name,source=source,provisional_key_count=numbers[source]['n'],
            eligibility_subset=expected,positive_work_ids=ids,dated_dissertation_ids=sorted(union)))
    count_witness=dict(schema='frozen_named_work_presence_counts/1',checked_on='2026-10-25',snapshot='2026-10-23',
        method='Distinct in_analysis dissertation IDs, requiring a year for dated presence; one exact first_author_key per person, without name unions or count sums.',
        sources=numbers,source_file_sha256={name:sha_file(RELEASE/(name+'.csv.gz')) for name in ('works','dissertations','citations')},
        final_identity_eligibility=final_identity_counts,
        final_identity_witness_sha256={name:sha_file(HERE.parent/'final-identity-pass'/name) for name in
            ('review.json','count-witnesses.json','dated-citation-sets.json','sources.json','additive-queue.json')},
        hahn_eligibility=dict(source='P:hahn|steven c',frozen_provisional_key_count=121,verified_subset_count=103,
            selected_work_ids=extra_hahn,dated_dissertation_ids=sorted(hahn_union),
            witness=str((HERE.parent/'classification-identity-review/count-witnesses.json').relative_to(ROOT)),witness_sha256=sha_file(HERE.parent/'classification-identity-review/count-witnesses.json')))
    (HERE/'count-witnesses.json').write_text(json.dumps(count_witness,ensure_ascii=False,indent=2)+'\n')
    graph=read(ROOT/'historiography-1920-2000.json');nodes={n['id']:n for n in graph['nodes']};graph_sources={s['id']:s for s in graph['sources']}
    accepted={}
    accepted_packets=[]
    for revision in range(184,190):
        record_path=ROOT/f'data/production-batches/person-entries-1.{revision}/acceptance.json'
        record=read(record_path);packet_path=ROOT/record['packet']
        assert sha_file(packet_path)==record['packet_sha256'],str(packet_path)
        packet=read(packet_path);updates={p['id']:p for p in packet['people_updates']}
        provenance=dict(revision=f'1.{revision}',acceptance_record=str(record_path.relative_to(ROOT)),
            acceptance_record_sha256=sha_file(record_path),packet=record['packet'],packet_sha256=record['packet_sha256'])
        accepted_packets.append(provenance)
        for accepted_node in packet['nodes']:
            assert accepted_node['id'] not in accepted
            accepted[accepted_node['id']]=dict(node=accepted_node,people_update=updates[accepted_node['id']],provenance=provenance)
    assert {p['person_id'] for p in targets}==set(accepted)
    decisions=deepcopy(baseline['links']);registry=deepcopy(baseline['registry']);supplements=read(HERE/'supplemental-metadata.json')
    frozen_labels=read(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')['labels'];label_map={r['key']:(i,r) for i,r in enumerate(frozen_labels)}
    next_id=max([len(frozen_labels)-1]+[r['id'] for r in registry['sources']])+1
    reviews,unresolved,new_theory,new_hist=[],[],[],[]
    for p in targets:
        pid=p['person_id'];paths=list((ROOT/'data/extension-2026').glob('remaining-*/'+pid+'/entry-draft.json'))
        if len(paths)!=1:
            unresolved.append(dict(person_id=pid,reason='Expected exactly one remaining-canon biography packet',paths=[str(x.relative_to(ROOT)) for x in paths]));continue
        path=paths[0];draft=read(path);assert draft['people_update']['id']==pid and draft['node']['id']==pid
        accepted_entry=accepted[pid]
        node=nodes.get(pid,accepted_entry['node']);available={**{s['id']:s for s in draft.get('new_sources',[])},**graph_sources}
        assert accepted_entry['node']['label']==node['label'],pid
        if draft['people_update'].get('new'):
            (new_theory if p['kind']=='theory' else new_hist).append(pid)
            assert draft['people_update']['label']==draft['node']['label'],pid
        if pid in baseline['links']['people']:
            decision=deepcopy(baseline['links']['people'][pid]);assert decision['works']==CHOICES[pid]
            status='retain_existing_unchanged'
        else:
            note='Identified through '+('; '.join(metadata[k]['title'] for k in CHOICES[pid]))+'. '
            note+='The displayed total is one exact provisional first-author bibliography key. Named works verify this bridge, not every attribution in that key; no authority identities, separate name keys or title variants are merged. Citation presence does not establish adoption or influence.'
            if pid in NOTES:note+=' '+NOTES[pid]
            decision=dict(source=p['source_key'],works=CHOICES[pid],review_note=note)
            decisions['people'][pid]=decision;status='accept_named_work_bridge'
        assert decision['source']==p['source_key']
        credits=[]
        for key in decision['works']:
            work=metadata[key];assert work['first_author_key']==p['source_key'][2:],key
            if key not in old_index:
                assert pid in EXCEPTIONS,(pid,key)
                if key in label_map:sid,label=label_map[key]
                else:
                    sid=next_id;next_id+=1
                    label=dict(key=key,short=work['first_author'].split(',')[0]+', '+work['title'].split(':')[0],full=work['title'],year=int(work['year']) if work['year'].isdigit() else None,author=work['first_author'])
                registry['sources'].append({**label,'id':sid,'source_index':baseline['source_count']+len(registry['sources'])-len(baseline['registry']['sources'])})
            events=[e for e in node['chronology']['events'] if matches(work['title'],e['label'])]
            if pid=='charles_tilly':events=[e for e in node['chronology']['events'] if 'Coercion, Capital' in e['label']]
            if pid=='alexis_de_tocqueville':events=[e for e in node['chronology']['events'] if 'démocratie en Amérique' in e['label']]
            accepted_events={e['id']:e for e in accepted_entry['node']['chronology']['events']}
            assert all(accepted_events[e['id']]==e for e in events),(pid,key)
            witnesses=[]
            for sid in dict.fromkeys(s.removeprefix('graph:') for e in events for s in e['source_ids']):
                s=available[sid];witnesses.append(dict(source_id=sid,url=s.get('url'),verification=s.get('verification',{})))
            witnesses+=supplements.get(pid,[])
            if not events or not witnesses:unresolved.append(dict(person_id=pid,work_id=key,reason='Named biography event and source witness required'))
            credits.append(dict(work_id=key,release_metadata=work,**{k:numbers[key][k] for k in ('n','series','n_region','strict_with_or_without_year')},
                source_scope='existing_exported_source' if key in old_index else 'reviewed_counts_only_exception',biography_events=events,primary_evidence=witnesses,
                identity_scope='Title/author concordance only; frozen kind/year retained. Edition, translation and volume-specific counts are not inferred.'))
        reviews.append(dict(person_id=pid,label=node['label'],kind=p['kind'],source=p['source_key'],decision=status,
            frozen_provisional_dated_first_author_count=numbers[p['source_key']]['n'],eligibility_count=p.get('eligibility_count'),eligibility_scope=p.get('eligibility_count_scope'),
            biography_packet=str(path.relative_to(ROOT)),biography_packet_sha256=sha_file(path),biography_reading_scope=node.get('scope_note'),
            accepted_credit_witness=accepted_entry['provenance'],
            packet_identity_note=accepted_entry['people_update'].get('identity_note'),verified_work_credits=credits,review_note=decision.get('review_note')))
    assert len(decisions['people'])==157
    assert len(registry['sources'])==22 and registry['sources'][:18]==baseline['registry']['sources']
    assert set(new_theory)=={'hannah_arendt','mary_louise_pratt','rogers_brubaker','anne_mcclintock','gilles_deleuze','giorgio_agamben','charles_taylor'}
    assert set(new_hist)=={'timothy_mitchell','tzvetan_todorov','steven_hahn','alexis_de_tocqueville'}
    review=dict(schema='teaching_reading_bridge_review/1',date='2026-10-25',snapshot='2026-10-23',status='prepared_not_applied',graph_revision=graph['revision_history'][-1]['version'],graph_sha256=sha_file(ROOT/'historiography-1920-2000.json'),
        target_people=42,new_people_links=41,retained_target_people=['henri_lefebvre'],expected_profiles=157,expected_sources=4059,expected_reviewed_exceptions=22,
        people=reviews,unresolved=unresolved,new_identity_ids=dict(theory=new_theory,historians=new_hist),
        accepted_packets=accepted_packets,
        baseline=str((HERE/'baseline.json').relative_to(ROOT)),count_witness=str((HERE/'count-witnesses.json').relative_to(ROOT)),
        limits=['All 42 targets are reviewed; Lefebvre already has a frozen reading profile, so there are 41 additions and 157 distinct profiles.',
            'All 116 prior people links, five field panels and Anderson’s personal comparison remain exact.',
            'All 4055 prior IDs, source positions, index metadata, numeric series and non-works source fields remain exact. Four author works lists must gain the new reviewed books.',
            'The 18 prior registry rows remain exact. Four counts-only work exceptions append source rows and reuse frozen label IDs where available.',
            'Hahn eligibility is the separately verified 103-dissertation subset; the displayed raw 121 remains provisional and is not a clean historian authority total.',
            'Taylor and Brown eligibility subsets are 102 and 101 respectively; displayed raw totals 148 and 114 remain qualified. Namesakes and held works are not silently assigned to the intended people.',
            'All theory keys remain provisional bibliography keys. Metadata title identity does not imply complete body reading or citation-by-citation verification.',
            'No automatic namesake merges, variant-key count sums, new field panels, aggregate source keys or inferred influence.'])
    REVIEW.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    (HERE/'candidate-links.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n')
    (HERE/'candidate-reviewed-source-ids.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(targets=len(reviews),new_links=41,profiles=len(decisions['people']),sources=4059,new_registry=registry['sources'][18:],unresolved=unresolved),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
