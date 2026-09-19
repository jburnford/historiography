#!/usr/bin/env python3
"""Revision 1.120: separate gender, racial formation and intersectional analysis."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_graph import validate

OUT=ROOT/'data/production-batches/gender-split-1.120'
BASE='drafts/historiography-1920-2000.v1.119.json'
PATH_BASE='drafts/seminar-pathways.before-1.120.json'
DAY='2026-09-18'
STAMP='2026-09-19T00:43:34+00:00'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def transform(before,paths):
    if before['revision_history'][-1]['version']!='1.119':
        raise ValueError('Split requires the reviewed 1.119 state')
    graph=copy.deepcopy(before); pathways=copy.deepcopy(paths)
    nodes={n['id']:n for n in graph['nodes']}
    gender=nodes['gender']; queer=nodes['queer']
    reps={r['person_id']:copy.deepcopy(r) for r in gender['representative_people']}
    strands={s['id']:copy.deepcopy(s) for s in gender['strands']}
    gender.update(label='Gender history',entry_type='Research field',
        description='Examines gender as a historically changing organization of social relations, identities and power. Research on work, family, masculinity, bodies and colonial settings connects gender to class, race and other relations without reducing these to one framework. Some feminist historians develop and criticize British Marxist social history; this is one route among several.',
        representative_figures_and_works='Joan Wallach Scott, “Gender” (1986); Leonore Davidoff and Catherine Hall, Family Fortunes (1987); Evelyn Brooks Higginbotham, “The Metalanguage of Race” (1992); Anna Clark, The Struggle for the Breeches (1995).',
        scope_note='Gender history is a distinct research field with competing explanations and methods. Women’s history remains independent and is not superseded. Racial formation and intersectional analysis have their own entries; connections express specific arguments rather than membership in a combined school. Historical differences of class, race, caste, place and sexuality remain integral questions within gender history.')
    gender['representative_people']=[r for r in gender['representative_people'] if r['person_id'] not in {'michael_omi','howard_winant','kimberle_crenshaw'}]
    gender['strands']=[s for s in gender['strands'] if s['id'] not in {'race','intersection'}]
    gender['source_ids']=[sid for sid in gender['source_ids'] if sid not in {'omi_winant','crenshaw_1989'}]
    for r in gender['representative_people']:
        r['context']=r['context'].replace('; distinct from the racial-formation programmes in this combined entry','')
    cohen_rep={'person_id':'cathy_j_cohen','role':'critic',
        'context':'Critiques single-oppression queer politics and argues for analysis of intersecting systems of power; a situated political-theoretical intervention, not a verdict on every sexuality historian.',
        'works':'“Punks, Bulldaggers, and Welfare Queens: The Radical Potential of Queer Politics?” (1997)',
        'source_ids':['cohen_queer_1997'],'basis':'source_review'}
    cohen_strand={'id':'intersectional_critique','title':'Intersectional criticism of queer politics',
        'person_ids':['cathy_j_cohen'],'focus':'Cohen challenges a simple heterosexual/queer division of power and calls for attention to race, gender, class and sexuality together. Political critique is not equivalent to a rejection of all queer history.',
        'works':cohen_rep['works'],'source_ids':['cohen_queer_1997'],'basis':'editorial_distinction'}
    queer['representative_people'].append(copy.deepcopy(cohen_rep))
    queer['strands'].append(copy.deepcopy(cohen_strand))
    queer['source_ids'].append('cohen_queer_1997')
    graph['people'].append({'id':'cathy_j_cohen','label':'Cathy J. Cohen'})
    graph['sources'].append({'id':'cohen_queer_1997',
        'title':'Cathy J. Cohen, “Punks, Bulldaggers, and Welfare Queens: The Radical Potential of Queer Politics?” (1997).',
        'citation':'Cathy J. Cohen, GLQ 3(4) (1997), 437–465. DOI: 10.1215/10642684-3-4-437.',
        'url':'https://doi.org/10.1215/10642684-3-4-437',
        'scope_note':'Primary university-hosted scan, selected pp. 437–442 read with OCR; p. 441 visually checked. Citation-level checks in claim_catalogue; not a full-article reading.',
        'claim_source_record_id':'witness:split120:cohen'})
    common={'layer':'historiographical_developments','period':'period_3','hunt_core_paradigm':False,'entry_kind':'group'}
    race={**common,'id':'racial_formation','label':'Racial formation','entry_type':'Approach / theoretical programme',
        'date_label':'Earlier roots · Omi–Winant 1986 / revised 1994 · coverage through 2000',
        'description':'Investigates how racial categories and meanings are produced and contested through social, political and economic relations. Omi and Winant’s programme treats race as historically specific and consequential, not as a biological essence or a simple expression of another social category.',
        'scope_note':'A distinct theoretical programme relevant to histories of racialization, not a synonym for Black history or all scholarship about race. Original 1986 and revised 1994 editions remain distinct. The checked course extract is labelled second edition; its retyped pagination and edition attribution have not been independently authenticated. Intersectional analysis connects racial inquiry with gender, class and sexuality without being identical to racial-formation theory.',
        'representative_figures_and_works':'Michael Omi and Howard Winant, Racial Formation in the United States (1986; second edition 1994).',
        'representative_people':[reps['michael_omi'],reps['howard_winant']],
        'strands':[strands['race']],'source_ids':['omi_winant']}
    intersection={**common,'id':'intersectionality','label':'Intersectional analysis','entry_type':'Method / approach',
        'date_label':'Earlier Black feminist roots · Crenshaw 1989 · Cohen 1997 · coverage through 2000',
        'description':'Examines how relations of race, gender, class and sexuality interact in specific structures of power. Crenshaw challenges single-axis frameworks that obscure Black women; Cohen brings an explicit intersectional critique to queer politics. The approach connects distinct fields without merging their objects or methods.',
        'scope_note':'An analytical approach with Black feminist and other intellectual and political roots, not a single school founded from nothing in 1989. Crenshaw’s legal critique and Cohen’s political intervention are distinct. Connections to gender, racial formation and queer history do not establish that every practitioner adopts this approach, or a direct Crenshaw–Omi/Winant borrowing.',
        'representative_figures_and_works':'Kimberlé Crenshaw, “Demarginalizing the Intersection of Race and Sex” (1989); Cathy J. Cohen, “Punks, Bulldaggers, and Welfare Queens” (1997). Earlier Black feminist resources are explicitly acknowledged by these authors.',
        'representative_people':[reps['kimberle_crenshaw'],copy.deepcopy(cohen_rep)],
        'strands':[strands['intersection'],copy.deepcopy(cohen_strand)],'source_ids':['crenshaw_1989','cohen_queer_1997']}
    graph['nodes'].extend([race,intersection])
    graph.setdefault('strand_redirects',[]).extend([
        {'from':'gender/race','to':'racial_formation/race','revision':'1.120','reason':'Separate racial-formation programme from gender history; strand record retained.'},
        {'from':'gender/intersection','to':'intersectionality/intersection','revision':'1.120','reason':'Separate connecting approach; strand record retained.'}])
    cleanup={
        'The target combines gender and racial formation. This comparison concerns gender and class;':'This comparison concerns gender and class;',
        'not every theory in the paired target':'not every theory discussed in gender history',
        'within this combined gender/racial-formation entry':'within the gender-history entry',
        'The source denotes the gender-history side of the combined gender/racial-formation entry. ':'',
        'This applies to the gender dimension of the combined source entry. ':'',
        'A gender-specific contribution within the combined source entry;':'A gender-history contribution;',
        'not the combined gender/racial-formation field’s verdict':'not a verdict shared by all gender historians',
        'not a sole origin of gender history or all racial-formation theory':'not a sole origin of gender history',
        'all gender/racial-formation research with Marxism':'all gender history with Marxism',
    }
    reviewed_edges=[]
    for e in graph['edges']:
        if 'gender' not in (e['source'],e['target']):continue
        reviewed_edges.append(e['id'])
        for old,new in cleanup.items():
            e['evidence_note']=e.get('evidence_note','').replace(old,new)
        if e['id']=='edge_116':
            e.update(relationship='Scott questions transparent experience and homogeneous identity categories',
                map_label='Scott: experience requires historical explanation',
                source_ids=['scott_gender_1986','scott_experience'],
                evidence_note='The retained gender-history link concerns Scott’s gender and experience arguments. Crenshaw’s separate single-axis critique is recorded from intersectional analysis. Omi and Winant’s account of racial classification belongs to the distinct racial-formation programme; it is no longer bundled into a joint critique. Questioning transparent experience does not eliminate political claims.')
    # Append first-class works, exact endpoints and scoped joins to the existing store.
    cat=graph['claim_catalogue']; entities={e['id']:e for e in cat['entities']}
    people={p['id']:p for p in graph['people']}
    def ent(id,label,type,**more):
        if id not in entities:
            row={'id':id,'label':label,'type':type,**more};entities[id]=row;cat['entities'].append(row)
        return id
    def person(pid):return ent('person:'+pid,people[pid]['label'],'person',legacy_person_id=pid,identity_status='Local identity; no new external authority accepted')
    for pid in ['michael_omi','howard_winant','kimberle_crenshaw','cathy_j_cohen']:person(pid)
    concepts={
        'intersection':ent('concept:intersectionality','Intersectional analysis','concept',concept_kind=['approach'],legacy_entry_id='intersectionality'),
        'race':ent('concept:racial_formation','Racial formation','concept',concept_kind=['approach'],legacy_entry_id='racial_formation'),
        'gender':ent('concept:gender_history','Gender history','concept',concept_kind=['research_field'],legacy_entry_id='gender'),
        'queer':ent('concept:queer/intersectional_critique','Single-oppression frameworks in the queer politics addressed by Cohen','concept',concept_kind=['topic'],legacy_strand_address='queer/intersectional_critique'),
        'identity':ent('concept:identity_single_axis','Single-axis identity frameworks addressed by Crenshaw','concept',concept_kind=['topic'],legacy_entry_id='identity')}
    works={
        'omi':('work:omi_winant_racial_formation_1986','Racial Formation in the United States',1986,['michael_omi','howard_winant'],'omi_winant'),
        'crenshaw':('work:crenshaw_demarginalizing_1989','Demarginalizing the Intersection of Race and Sex',1989,['kimberle_crenshaw'],'crenshaw_1989'),
        'cohen':('work:cohen_queer_1997','Punks, Bulldaggers, and Welfare Queens: The Radical Potential of Queer Politics?',1997,['cathy_j_cohen'],'cohen_queer_1997')}
    for key,(wid,title,year,authors,sid) in works.items():
        ent(wid,title,'work',first_publication_year=year,author_ids=[person(p) for p in authors],legacy_source_ids=[sid],identity_status='Local work identity; editions and external authorities not conflated')
    witnesses={
        'omi':('https://scalar.usc.edu/works/bodies/media/Omi%20and%20Winant,%20Racial%20Formations.pdf','USC-hosted course extract','PDF pp. 1–3, especially “Race as a Social Concept” and definition of racial formation','Second-edition label and pagination unauthenticated; original 1986 and revised 1994 are distinct. Regional claims are attributed to the authors.'),
        'crenshaw':('https://ideas.wharton.upenn.edu/wp-content/uploads/2018/07/Crenshaw-1989.pdf','Penn-hosted primary article','Printed pp. 139–140','Selected opening only; no full case-law review or claim to invent earlier Black feminist analysis.'),
        'cohen':('https://blackwomenintheblackfreedomstruggle.voices.wooster.edu/wp-content/uploads/sites/210/2019/02/Cathy-J-Cohen_Punks-bulldaggers.pdf','Wooster-hosted primary article scan','Printed pp. 437–442, especially 440–441','Selected pages read via OCR; p. 441 visually checked. Critique addresses named tendencies in queer politics, not every sexuality historian.')}
    for key,(url,provider,locator,limit) in witnesses.items():
        s={'id':'witness:split120:'+key,'provider':provider,'url':url,'observed_at':STAMP,
           'describes_work':works[key][0],'access_note':limit,
           'reading_notes_path':'data/production-batches/gender-split-1.120/EVIDENCE.md'}
        if key=='cohen':s['download_sha256']='fa261ca536c85d3baf9b55a062fa100547819d0ded1f889fdc4ce5be4e358bc5'
        cat['source_records'].append(s)
    added_claims=[]
    def claim(key,subject,predicate,obj,keys,statement,qualification):
        ev=[]
        for k in keys:
            url,provider,locator,limit=witnesses[k]
            ev.append({'source_record_id':'witness:split120:'+k,'locator':locator,'scope':'metadata' if predicate=='authored' else 'passage',
                       'support':statement,'check_status':'metadata_checked' if predicate=='authored' else 'passage_checked',
                       'checked_on':DAY,'support_assessment':'supports_scoped_statement','limitation':limit+' '+qualification})
        c={'id':'claim:split120:'+key,'subject':subject,'predicate':predicate,'object':obj,
           'statement':statement,'qualification':qualification,'basis':'source_assertion' if predicate=='authored' else 'editorial_interpretation',
           'attributed_to':'Named author(s); comparison links are explicitly editorial, not transmission claims',
           'intervention_year':1994 if keys==['omi'] else works[keys[0]][2], 'valid_time':None,
           'review':{'status':'accepted','reviewer':'Codex editorial review','reviewed_on':DAY,'rationale':'User-authorized separation; accepted only within the recorded reading scope.'},
           'history':[{'on':DAY,'status':'accepted','revision':'1.120','action':'Scoped relationship after separating the combined entry.'}], 'evidence':ev}
        if predicate=='related_concept':
            c['intervention_year']=None
            c['comparison_recorded_on']=DAY
        cat['claims'].append(c);added_claims.append(c['id']);return c
    for key,(wid,title,year,authors,sid) in works.items():
        for pid in authors:claim('authored_'+pid,person(pid),'authored',wid,[key],people[pid]['label']+' is credited as an author of this work.','Joint authorship retained; credit does not establish reception or sole authorship of a passage.')
    claim('omi_programme',works['omi'][0],'contributes_to',concepts['race'],['omi'],
          'Omi and Winant treat racial categories as historically constituted through social and political relations.',
          'Formulation checked in the course extract labelled second edition; not retroactively verified in the 1986 text.')
    claim('crenshaw_programme',works['crenshaw'][0],'contributes_to',concepts['intersection'],['crenshaw'],
          'Crenshaw centres Black women to challenge separate-axis accounts of race and sex.',
          'Specific legal and feminist intervention, not the origin of all Black feminist thinking.')
    claim('cohen_programme',works['cohen'][0],'contributes_to',concepts['intersection'],['cohen'],
          'Cohen explicitly calls for intersectional analysis of interacting systems of oppression in queer politics.',
          'Political analysis, not demonstrated adoption throughout queer historiography.')
    claim('crenshaw_cohen',person('kimberle_crenshaw'),'contributes_to',works['cohen'][0],['cohen'],
          'Cohen names Crenshaw among Black feminist authors informing her intersectional argument.',
          'Explicit acknowledgement on p. 441; the exact Crenshaw work is not assigned from this passage.')
    linked=[]
    linked.append((claim('gender_link',concepts['intersection'],'related_concept',concepts['gender'],['crenshaw'],
        'Intersectional analysis connects gender inquiry with race and class through criticism of single-axis explanations.',
        'Editorial connection grounded in Crenshaw’s opening; not all gender history adopts one approach.'),'gender','comparison',None))
    linked.append((claim('race_link',concepts['intersection'],'related_concept',concepts['race'],['crenshaw','omi'],
        'Intersectional analysis and racial formation pose related but distinct questions about racial categories and power.',
        'Editorial comparison of independently read arguments; no direct Crenshaw–Omi/Winant borrowing or critique is established.'),'racial_formation','comparison',None))
    linked.append((claim('queer_link',works['cohen'][0],'critiques',concepts['queer'],['cohen'],
        'Cohen critiques single-oppression queer politics that obscures race, class and gender hierarchies.',
        'The teaching source presents Cohen’s intervention within intersectional analysis; the target is this specific debate, not all queer or sexuality history.'),'queer','critique','queer/intersectional_critique'))
    linked.append((claim('identity_link',works['crenshaw'][0],'critiques',concepts['identity'],['crenshaw'],
        'Crenshaw challenges identity frameworks built around otherwise privileged members of racial or gender groups.',
        'Her specific single-axis critique is separate from Scott’s experience argument; it does not reject all collective identification.'),'identity','critique',None))
    for num,(c,target,kind,strand) in enumerate(linked,762):
        e={'id':f'edge_{num}','source':'intersectionality','target':target,'type':'critique' if kind=='critique' else 'connection',
           'relationship_kind':kind,'directed':kind!='comparison','relationship':c['statement'],'map_label':c['statement'],
           'evidence_note':c['qualification'],'source_ids':[works[k][4] for k in ('cohen',) if any(v['source_record_id'].endswith(':'+k) for v in c['evidence'])] or ['crenshaw_1989'],
           'classification_basis':'editorial_review','review_status':'accepted','claim_ids':[c['id']],
           'claim_projection':{'subject':c['subject'],'object':c['object'],'note':'Qualified teaching view; read the exact claim endpoints and evidence.'}}
        if c['id'].endswith('race_link'):e['source_ids'].append('omi_winant')
        if strand:e['target_strand']=strand
        graph['edges'].append(e)
    race['work_ids']=[works['omi'][0]]
    intersection['work_ids']=[works['crenshaw'][0],works['cohen'][0]]
    race['claim_ids']=[cid for cid in added_claims if 'omi' in cid or 'winant' in cid or cid.endswith('race_link')]
    intersection['claim_ids']=[cid for cid in added_claims if cid not in race['claim_ids'] or cid.endswith('race_link')]
    for p in pathways['pathways']:
        if p['id']=='difference_and_categories':
            pos=p['node_ids'].index('gender')+1
            p['node_ids'][pos:pos]=['racial_formation','intersectionality']
            p['questions'][1]='How does intersectional analysis connect gender history, racial formation and queer history while retaining their distinct objects and methods?'
            p['exercise']='Compare a named argument from gender history, racial formation or queer history with an intersectional intervention. Distinguish conceptual comparison, documented use and criticism, and state the evidence for each link.'
    graph['revision_history'].append({'version':'1.120','date':DAY,
        'summary':'Separate Gender history and Racial formation; add Intersectional analysis as a connecting approach while preserving independent Sexuality & queer history. Move two strands with redirects, distinguish the mixed identity critique, and add Cohen’s sourced queer-political intervention.',
        'added_node_ids':['racial_formation','intersectionality'],'updated_node_ids':['gender','queer'],
        'added_person_ids':['cathy_j_cohen'],'added_source_ids':['cohen_queer_1997'],
        'added_edge_ids':[f'edge_{n}' for n in range(762,766)],'reviewed_gender_edge_ids':reviewed_edges,
        'acceptance_record':'data/production-batches/gender-split-1.120/acceptance.json'})
    return graph,pathways


def main():
    path=ROOT/'historiography-1920-2000.json';pp=ROOT/'seminar-pathways.json'
    original=path.read_bytes();original_paths=pp.read_bytes()
    before=json.loads(original);paths=json.loads(original_paths)
    after,newpaths=transform(before,paths)
    errors,_=validate(after,newpaths)
    if errors:raise ValueError('\n'.join(errors))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,data in [(BASE,original),(PATH_BASE,original_paths)]:
        p=ROOT/name
        if p.exists() and p.read_bytes()!=data:raise ValueError('Different snapshot already exists: '+name)
        p.write_bytes(data)
    if path.read_bytes()!=original or pp.read_bytes()!=original_paths:raise ValueError('Concurrent edit detected; re-review')
    write(path,after);write(pp,newpaths)
    changed={}
    for coll in ['nodes','edges']:
        old={r['id']:r for r in before[coll]}
        changed[coll]=[{'id':r['id'],'before':old[r['id']],'after':r} for r in after[coll] if r['id'] in old and r!=old[r['id']]]
    acceptance={'revision':'1.120','date':DAY,'authorization':'User approved independent gender/racial/queer entries connected by intersectional analysis.',
        'baseline':BASE,'baseline_sha256':sha(ROOT/BASE),'pathway_baseline':PATH_BASE,'pathway_baseline_sha256':sha(ROOT/PATH_BASE),
        'production_sha256':sha(path),'pathways_sha256':sha(pp),'changes':changed,
        'strand_redirects':after['strand_redirects'],
        'note':'Captures the actual incoming 1.119 state, including pre-existing witness hashes and validator changes by another session. Those changes are preserved. Website files are untouched.'}
    write(OUT/'acceptance.json',acceptance)
    print('Applied 1.120: 126 entries, 765 teaching edges; independent gender, racial formation and queer entries, linked through intersectional analysis.')


if __name__=='__main__':main()
