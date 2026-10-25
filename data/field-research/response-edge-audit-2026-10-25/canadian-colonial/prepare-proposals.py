"""Write reviewable response proposals; no canonical mutation or source-body copies."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
G=json.loads((ROOT/'historiography-1920-2000.json').read_text());N={n['id']:n for n in G['nodes']};S={s['id']:s for s in G['sources']}
P=[]
def proposal(number,source,target,kind,claim,evidence,sids,locator,extent,related=(),status='include',gap='missing_named_response',date=None):
 pair=[e['id'] for e in G['edges'] if {e['source'],e['target']}=={source,target}]
 assert source in N and target in N and not pair,(source,target,pair)
 P.append(dict(proposal_id=f'rea_canadian_{number:02}',disposition=status,source=source,target=target,relationship_kind=kind,type='critique' if kind=='critique' else 'connection',directed=kind!='comparison',relationship=claim,evidence_note=evidence,source_ids=sids,primary_locators=locator,read_extent=extent,date_scope=date,missing_relation_assessment=gap,existing_edge_check=dict(any_edge_between_endpoints=pair,related_existing_edges=list(related),action='Add only the scoped named relation; preserve all existing field and multi-voice records.')))
proposal(1,'sarah_carter','adele_perry','critique',
 'Carter’s appreciative review of On the Edge of Empire asks for fuller North American comparison and more evidence of Indigenous social centrality, political agency and initiatives (2002/03).',
 'The signed review praises the gender/race analysis and conclusion while making these two requests on p119. It does not say Perry denied Indigenous resistance. The reviewed book is not newly read.',
 ['pe139_perry_carter_2002'],['BC Studies136 (Winter2002/03), pp117–119, especially p119 final three paragraphs'],
 'Fresh read of the complete signed three-page review (PDF pages1–3 of a34-page book-review section); not the rest of the section or Perry’s monograph.',date='Winter2002/03')
proposal(2,'franca_iacovetta','joan_sangster','critique',
 'With Linda Kealey, Iacovetta answers Sangster’s Beyond Dichotomies, objecting that its polemic risks oversimplification and misrepresentation while welcoming debate (1996).',
 'The opening expressly names Sangster’s essay and frames the response as disagreement among friends and colleagues. Linda Kealey is coauthor; she is not Gregory S.Kealey. Do not treat this as a single-author reply.',
 ['rea_canadian_iacovetta_kealey_1996'],['Left History combined3.2/4.1 (1996), p221 opening'],
 'Fresh reading of the journal PDF’s indexed opening page221 and journal landing-page author/DOI metadata. Direct PDF retrieval now returns browser verification; pp222–237 were not read.',date='1996')
proposal(3,'joan_sangster','franca_iacovetta','critique',
 'Replying to Iacovetta and Linda Kealey, Sangster welcomes their review but contests the simplification charge and treats gender as both standpoint and field (1996).',
 'This is a qualified rejoinder: p247 stresses shared questions and theoretical overlap. It must not turn Iacovetta/Kealey into simple poststructuralist adversaries or erase the coauthor.',
 ['cdnsrc_sangster_1996'],['Reconsidering Dichotomies, pp240 and247, including n15'],
 'Fresh selected primary PDF text read through the journal/search extraction: pp239–242 and247. No whole-article reading claim; direct PDF requests now show browser verification.',date='1996')
proposal(4,'joan_sangster','mariana_valverde','critique',
 'Sangster questions Valverde’s suggestion that women’s history is not self-sufficient, reading it as implying gender history’s superiority (1996).',
 'The attribution is explicit in p240 n3; this records Sangster’s reading, not an agreed hierarchy.',
 ['cdnsrc_sangster_1996'],['Reconsidering Dichotomies, p240 and n3'],
 'Fresh selected primary PDF text, p240 and footnote3; Valverde’s entire1993 article was not newly read.',date='1996')
proposal(5,'joan_sangster','joy_parr','critique',
 'Sangster objects that Parr groups feminist and antifeminist critics of gender history together (1996).',
 'The criticism is confined to p240 n2 and its quoted passage; it does not reject Parr’s entire gender-history project.',
 ['cdnsrc_sangster_1996'],['Reconsidering Dichotomies, p240 n2'],
 'Fresh selected primary PDF text, p240 and footnote2; Parr’s complete essay was not newly read.',date='1996')
proposal(6,'joan_sangster','joan_wallach_scott','critique',
 'Sangster contrasts Canadian feminist materialist work with what she calls Scott’s more radical antimaterialist deconstruction (2000).',
 'The wording is Sangster’s characterization. Her neighbouring objection about constructed materiality targets Sewell, not Scott.',
 ['wcreq_sangster_2000'],['Labour/Le Travail46 (2000), pp157–158; Scott characterization on p157'],
 'Inherited primary full-article reading and exact passage retained on edge1169; this audit checked primary journal metadata/search text but did not freshly reread the whole body.',
 related=['edge_1169','edge_1318','edge_1319'],gap='named_critic_hidden_inside_existing_multi_voice_field_record',date='2000')
proposal(7,'bryan_d_palmer','ian_mckay','critique',
 'Reviewing Reasoning Otherwise, Palmer challenges McKay’s elastic liberal-order category for obscuring capitalism’s changing structures while praising the book’s achievement (2009).',
 'The review names McKay and the2008 book. This adds personal visibility to the existing field critique; it is not new evidence of a different dispute. No direct McKay rejoinder is established.',
 ['lof_palmer_2009'],['Radical Reasoning, Underhill Review Fall2009; print pp3–5 and31'],
 'Fresh primary indexed HTML sectionsI–III andVI read; inherited full read supplies print-page locators. Reasoning Otherwise itself was not newly read.',
 related=['edge_922','edge_894'],gap='same_documented_response_already_field_routed_person_route_missing',date='2009')
proposal(8,'allan_greer','fernand_ouellet','critique',
 'Greer’s Sorel case challenges the demographic-and-cultural explanation of agrarian crisis associated with Ouellet, especially the routine-bound habitant premise (1981).',
 'The named work is identified in n41. This isolates Greer’s intervention without replacing the multi-author controversy or treating his unread1993 book as direct evidence.',
 ['pe137_ouellet_greer_1981'],['Fur-Trade Labour and Lower Canadian Agrarian Structures (1981), pp213–214 and n41'],
 'Inherited full primary reading and exact final-page passages retained on edge989; fresh DOI/title concordance only. Direct new body retrieval was unsuccessful.',
 related=['edge_989','edge_1010'],gap='one_named_intervention_inside_preserved_multi_voice_field_record',date='1981')
proposal(9,'james_c_scott','evelyn_brooks_higginbotham','influence',
 'Higginbotham explicitly uses Scott’s infrapolitics for her discussion of micropolitical resistance (1992).',
 'Her note67 identifies Domination and the Arts of Resistance, pp183–192; James C.Scott is distinct from Joan W.Scott.',
 ['higginbotham_race'],['Signs17.2 (1992), p274 and n67'],
 'Fresh primary printed pp251–252 and274 read from the institutional PDF; the remaining article was not reread.',date='1992')
proposal(10,'darlene_clark_hine','evelyn_brooks_higginbotham','contribution',
 'Higginbotham credits Hine’s reading, suggestions and questions on an earlier version of her1992 article.',
 'This is a named draft-feedback contribution, not evidence that Hine originated the article’s theory.',
 ['higginbotham_race'],['Signs17.2 (1992), p251 acknowledgment'],
 'Fresh primary acknowledgment on printed p251; no date of the feedback meeting is inferred.',date='Documented1992; feedback date unspecified')
proposal(11,'foucault','evelyn_brooks_higginbotham','influence',
 'Higginbotham adapts Foucault’s technologies terminology to race, gender and sexuality (1992).',
 'Her p252 n4 names History of Sexuality1 and explains the term alongside Teresa de Lauretis; neither resource is exclusive.',
 ['higginbotham_race'],['Signs17.2 (1992), p252 and n4'],
 'Fresh primary p252 and n4; not a fresh full reading of Foucault or de Lauretis.',related=['edge_408'],date='1992')
proposal(12,'w_e_b_du_bois','david_roediger','influence',
 'Roediger identifies Black Reconstruction as an intellectual entry point for connecting emancipation with broader labour freedom (acknowledged2012).',
 'The written union interview directly records Roediger’s acknowledgment, not merely its interviewer’s introduction. It does not explain his whole research programme.',
 ['hc172_david_roediger_1'],['UE,1February2012, opening Du Bois exchange before the first marked question'],
 'Fresh complete written interview read; no monograph body read newly claimed.',date='Acknowledged2012; Du Bois work1935')
proposal(13,'walter_johnson','eugene_genovese','critique',
 'Johnson rejects three premises of Genovese’s resistance/hegemony account while rejecting the claim that Roll, Jordan, Roll simply ignores enslaved agency (2003).',
 'The named p117 criticism concerns revolutionary aspiration, culture versus coercive force, and the individual/collective distinction. It is not a denial that Genovese discussed resistance.',
 ['hc172_walter_johnson_1'],['On Agency, Journal of Social History37.1 (2003), p117; notes9–11 on p123'],
 'Fresh primary pp113–114,117 and122–123 read; Genovese’s books were not newly read.',date='2003')
proposal(14,'karl_marx','walter_johnson','influence',
 'Johnson explicitly uses Marx’s Eighteenth Brumaire formulation as an alternative starting point for rethinking agency (2003).',
 'The opening counterposes Marx’s constrained history-making formulation to Gutman’s Sartre-derived injunction; no universal Marxist lineage is inferred.',
 ['hc172_walter_johnson_1'],['On Agency, p113 and p122 n2'],
 'Fresh primary opening and cited note; Gutman has no individual graph node.',date='2003')
proposal(15,'homi_k_bhabha','dipesh_chakrabarty','influence',
 'Chakrabarty explicitly uses Bhabha’s pedagogic/performative distinction to formulate a tension within nationalism and peasant citizenship (2000).',
 'The acknowledgment is on p10. It concerns this conceptual distinction, not derivation of the whole provincializing-Europe project.',
 ['post'],['Provincializing Europe, introduction p10'],
 'Fresh publisher-hosted primary introduction pp3–10 read; whole book and Bhabha’s original essay not newly read.',date='2000')
proposal(16,'foucault','dipesh_chakrabarty','influence',
 'Chakrabarty credits Foucault with encouraging critiques of historicism while explicitly denying that postcolonial criticism simply derives from Western poststructuralism (2000).',
 'Both the acknowledgment and the qualification occur together on p6. This must not become a one-way European-origin account.',
 ['post'],['Provincializing Europe, introduction p6'],
 'Fresh publisher-hosted primary introduction pp3–10 read; not the whole book or a new reading of Foucault.',date='2000')
# Preserve prior source statements. Addenda are proposed rather than applied.
used={sid for p in P for sid in p['source_ids']};sources=[]
new=dict(id='rea_canadian_iacovetta_kealey_1996',title='Franca Iacovetta and Linda Kealey, “Women’s History, Gender History and Debating Dichotomies,” Left History combined3.2/4.1 (1996):221–237.',url='https://doi.org/10.25071/1913-9632.6968',citation='Franca Iacovetta and Linda Kealey, “Women’s History, Gender History and Debating Dichotomies,” Left History4.1 (1996):221–237 (combined issue3.2/4.1).',verification=dict(status='supporting_page_checked',checked_on='2026-10-25',note='Both authors and DOI checked on the journal page; primary indexed opening p221 read. Direct PDF presently returns browser verification; later pages not claimed read.'))
for sid in sorted(used):
 ps=[p for p in P if sid in p['source_ids']]
 sources.append(dict(source_id=sid,existing=sid in S,source_record=new if sid==new['id'] else S[sid],proposed_verification_addendum=dict(checked_on='2026-10-25',locators=sorted({loc for p in ps for loc in p['primary_locators']}),read_extent=sorted({p['read_extent'] for p in ps}),limitations='Prior verification retained. These addenda are proposed, not applied; bibliographic concordance is not whole-book reading.')))
H=[
 ('hold_greer_wolfe',['allan_greer','patrick_wolfe'],'Do not add a blanket personal critique. Greer2019 pp62–64 affirms Wolfe’s structure insight and addresses overgeneralized application; edge1012 already explains this distinction.','Fresh primary pp62–64 read.','https://www.erudit.org/en/journals/jcha/2019-v30-n1-jcha05408/1070631ar.pdf'),
 ('hold_johnson_berlin',['walter_johnson','ira_berlin'],'Do not assign an anonymous agency quotation to Berlin: Johnson explicitly withholds names (p122 n4).','Fresh primary pp114,122 and n4 read.','https://glc.yale.edu/sites/default/files/pdf/on_agency_johnson.pdf'),
 ('hold_davis_williams',['david_brion_davis','eric_williams'],'Different emphases in moral and economic explanations are not themselves a verified direct criticism. Read the particular Davis passage and distinguish the two Williams theses.','Entry and inherited source-note screen only; no fresh direct-response passage.',''),
 ('hold_palmer_granatstein',['bryan_d_palmer','j_l_granatstein'],'The1999 essay Of Silences and Trenches is a specific lead, but secondary descriptions disagree about its principal target; the primary body was not retrieved.','Bibliographic lead only; not a new primary reading.',''),
 ('hold_morton_granatstein',['desmond_morton','j_l_granatstein'],'Reported approval has not been checked in Morton’s own signed text. No agreement arrow from coauthorship or common military-history field.','Secondary search lead only; no primary confirmation.',''),
 ('hold_davidoff_hall',['leonore_davidoff','catherine_hall'],'Joint authorship is bibliographically certain; a substantive collaboration edge awaits the exact joint framing or signed retrospective. Do not turn metadata into an argument arrow.','Fresh catalog/publisher-preview metadata only; prior limited prologue reading remains inherited.','https://www.routledge.com/Family-Fortunes-Men-and-Women-of-the-English-Middle-Class-1780-1850/Davidoff-Hall/p/book/9781138068810'),
 ('hold_stoler_cooper',['ann_laura_stoler','frederick_cooper'],'The coedited colonial agenda is a valuable joint-work lead, but the introduction or jointly signed retrospective must establish the intended relationship and scope.','Current Stoler description and inherited notes only.',''),
 ('hold_cooper_thompson',['frederick_cooper','ep_thompson'],'A named retrospective is embedded in the African-labour debate; inspect its actual praise, reservations and mediation before defining an influence or critique edge.','Existing collective-edge context only; original retrospective not freshly read.',''),
 ('hold_walker_winks',[],'A signed criticism of Winks by James Walker occurs in Black Canadian history, but neither person has a current standalone node. No substitute endpoints.','Entry/inherited source context only; absent endpoints.',''),
 ('hold_metropolitan_reserved',[],'Turner/Innis/Creighton/Careless metropolitan routes are assigned to the parent/other lane and are deliberately not duplicated here.','Scope exclusion, not an evidence judgment.','')]
holds=[dict(case_id=i,node_ids=nodes,disposition='hold',reason=reason,read_extent=extent,url=url) for i,nodes,reason,extent,url in H]
report=dict(schema='response_edge_proposals/1',checked_on='2026-10-25',baseline_revision=G['revision_history'][-1]['version'],baseline_graph_sha256=hashlib.sha256((ROOT/'historiography-1920-2000.json').read_bytes()).hexdigest(),status='prepared_for_parent_deduplication_and_substantive_review',scope='Existing endpoints only; proposals do not edit canonical data, life metadata or reading exports.',proposals=P,sources=sources,holds=holds)
(HERE/'proposals.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
r=json.loads((HERE/'node-review.json').read_text());r['status']='all_90_reasoned_screens_complete_proposals_prepared_for_review'
for row in r['rows']:
 row['read_extent']['fresh_primary_source_ids']=sorted({sid for p in P if row['node_id'] in (p['source'],p['target']) and not p['read_extent'].startswith('Inherited') for sid in p['source_ids']})
 # Incident proposals supplement, rather than replace, the primary node screen.
 row['proposal_ids']=sorted(set(row['proposal_ids'])|{p['proposal_id'] for p in P if row['node_id'] in (p['source'],p['target'])})
(HERE/'node-review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(P),'scoped proposals,',len(sources),'sources,',len(holds),'holds; all90 node rows retained')
if __name__=='__main__':pass
