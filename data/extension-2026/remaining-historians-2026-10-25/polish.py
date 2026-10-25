"""Readable final annotations for the unaccepted packet; run after prepare.py."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
cfg=json.loads((P/'batch.json').read_text())
scopes={
'michel_de_certeau':'Read the English preface ix–x and General Introduction xi–xv via OCR of the later paperback scan. French original and body chapters were not collated. The colonial generalization in the introduction is not adopted as an established fact.',
'charles_tilly':'Read the1985chapter at169–172. Complete books and comparative datasets remain unread. The1990original title and later1992revision remain distinct; the memorial’s inconsistent ContentiousFrench date is not adopted.',
'timothy_mitchell':'Read the1991paperback preface ix–xiii. The original1988book and later manifestation remain distinct. Metadata supplies the dates of RuleofExperts and CarbonDemocracy; their unread bodies support no additional substantive relation.',
'jack_goody':'Read FamilyandMarriage8–9 including note1, and the selected opening1–3 of TheTheftofHistory. Empirical studies cited in these passages were not independently checked. Joint authorship with IanWatt is retained.',
'tzvetan_todorov':'The colonial connection uses only three authored opening paragraphs of the1984essay, printed89. The memory connection uses Todorov’s short UNESCOessay. The full1984article and historical monographs remain unread. Howard’s1984Englishtranslation and the1982Frenchoriginal are distinct; the2018webpost is posthumous.',
'partha_chatterjee':'Read the2012Çubukçu interview at2–3. Remaining interview and complete books remain unread. Existing qualifications for the1993chapter and the Andersonexchange are preserved. The2025digital migration does not redate the2012interview.',
'alessandro_portelli':'Read all four pages of the adapted1991excerpt, WhatMakesOralHistoryDifferent? The handout modernizes terms in brackets. Original1979Italian and1981English versions were not collated, and complete books remain unread.',
'alexis_de_tocqueville':'Read only the1856Avant-propos at5–12; DemocracyinAmerica and the remaining OldRegime text remain unread. Connections describe an earlier historical programme, not membership in twentieth-century schools. The joint penitentiary report with Gustave de Beaumont is not treated as a sole-authored work; the Académie’s unverified1832date is not adopted.',
'steven_hahn':'Read the complete2009Pennfeature with direct author comments and PeterNichols’s account. Other book records establish dates and identity only. No full monograph reading. Four positively matched book keys yield the clean103-dissertation lower bound; all other key rows remain unassigned.'}
notes={
'alessandro_portelli':[
'The adapted1991excerpt,sectionIV, describes questions, changing relationships and the distortion caused by removing the interviewer’s voice. The handout modernizes bracketed terms and is not an exact1981transcription.',
'The adapted excerpt,sectionIII, uses workers’ memories of Trastulli in Terni to distinguish event chronology from narrated meaning. Factual verification remains necessary; false memories do not replace established dates.'],
'partha_chatterjee':[
'The2012interview at2–3 explains how FortWilliam and the BlackHole story connect with selectively traced political economy, law and techniques of imperial power. Chatterjee explicitly notes that selection was necessary; no exhaustive global history is inferred.',
'At2, Chatterjee says he learned through SubalternStudies to interrogate popular culture theoretically. Theatre and football enter alongside policy and elite discourse. His sweeping claim about what other intellectual historians omit is not adopted.'],
'alexis_de_tocqueville':[
'The1856Avant-propos at5–12 asks how habits and institutions from the monarchy persisted after1789. This is an earlier historical inquiry into political change, not membership in a modern school.',
'At7–10, Tocqueville describes moving beyond celebrated writers and public figures toward institutional practices, relations among classes and provincial administrative archives. This is his research programme; it does not make every archival voice representative.'],
'steven_hahn':[
'Nichols’s2009feature quotes Hahn challenging a narrative centred on integration and citizenship, and describes aspirations outside that framework. This connection concerns that documented intervention, not all AfricanAmerican historical experience.',
'The2009feature and direct book quotation describe Hahn’s interpretation of enslaved people’s wartime flight and armed participation as rebellion. The interpretation remains attributed to him; no uncontested ranking of the largest rebellion is asserted.']}
# Split obvious typography, then restore named compound titles with readable words.
replacements={
'FamilyandMarriage':'Family and Marriage','TheTheftofHistory':'The Theft of History','RuleofExperts':'Rule of Experts','CarbonDemocracy':'Carbon Democracy','ContentiousFrench':'Contentious French','IanWatt':'Ian Watt','UNESCOessay':'UNESCO essay','Englishtranslation':'English translation','Frenchoriginal':'French original','Andersonexchange':'Anderson exchange','WhatMakesOralHistoryDifferent':'What Makes Oral History Different','DemocracyinAmerica':'Democracy in America','OldRegime':'Old Regime','Pennfeature':'Penn feature','PeterNichols':'Peter Nichols','SubalternStudies':'Subaltern Studies','FortWilliam':'Fort William','BlackHole':'Black Hole','AfricanAmerican':'African American','authorcomments':'author comments','completebooksunread':'complete books unread','fullbookunread':'full book unread','fullbook':'full book','wholebook':'whole book','bookbodyunread':'book body unread','monographunread':'monograph unread','originalpublication':'original publication','bodyunread':'body unread','chapterbody':'chapter body','firstpublished':'first published','notredated':'not redated','datedevent':'dated event','participantbio':'participant bio','exactdates':'exact dates','newpreface':'new preface','bookquotation':'book quotation','bookkeys':'book keys','intellectualdiscourse':'intellectual discourse','localnarrative':'local narrative','conceptualhistory':'conceptual history','historicalscholar':'historical scholar','empirehistory':'empire history','globalempire':'global empire','politicaleconomy':'political economy','printed169':'printed 169','originaldate':'original date','lifemetadata':'life metadata','currentpublisher':'current publisher','author-participationwitness':'author participation witness','positivewitnessdated':'positive witness dated','posthumousUNESCOwebreproduction':'posthumous UNESCO web reproduction','adaptedexcerpt':'adapted excerpt','bracketedmodernizations':'bracketed modernizations','historicalmonographs':'historical monographs','primarytitlepage':'primary title page','institutionalfeature':'institutional feature','primaryinterview':'primary interview','biographypreface':'biography preface','sourcequalifications':'source qualifications','dateddissertations':'dated dissertations','first-authorworkkeyincludedinclean':'first-author work key included in clean ','neverindependently':'never independently','notindependently':'not independently','verifiedattendance':'verified attendance','missingdeathdata':'missing death data','life-year':'life year','new-workevent':'new work event'}
def readable(v):
 for old,new in sorted(replacements.items(),key=lambda kv:len(kv[0]),reverse=True):v=v.replace(old,new)
 v=re.sub(r'([a-z])([A-Z])',r'\1 \2',v)
 v=re.sub(r'([A-Za-zÀ-ž])([0-9])',r'\1 \2',v)
 v=re.sub(r'([0-9])([A-Za-zÀ-ž])',r'\1 \2',v)
 v=re.sub(r'([,;:])(?=[A-Za-zÀ-ž])',r'\1 ',v)
 v=v.replace('P: ','P:').replace('W: ','W:')
 return v
fields={'label','description','date_label','representative_figures_and_works','scope_note','selection_note','support','interpretation','basis','relationship','evidence_note','context','works','title','citation','note','limits','locator','check_scope','identity_rationale'}
def clean(o):
 if isinstance(o,dict):
  for k,v in o.items():
   if k in fields and isinstance(v,str):o[k]=readable(v)
   elif isinstance(v,(dict,list)):clean(v)
 elif isinstance(o,list):
  for v in o:clean(v)
for pid in cfg['persons']:
 f=P/pid/'entry-draft.json';d=json.loads(f.read_text());oldscope=d['node']['scope_note'];tail=oldscope[oldscope.index('The exact frozen'):] if 'The exact frozen' in oldscope else oldscope[oldscope.index('Four positively'):]
 d['node']['scope_note']=scopes[pid]+' '+tail
 for e,txt in zip(d['proposed_edges'],notes.get(pid,[])):e['evidence_note']=txt
 clean(d)
 # A direct, narrow primary extract is never described as an abstract or full-book reading.
 if pid=='tzvetan_todorov':assert 'three authored opening' in d['node']['scope_note']
 f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 lf=P/pid/'life-status.json';l=json.loads(lf.read_text());clean(l);lf.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n')
 nf=P/pid/'research-notes.json';n=json.loads(nf.read_text());n['unread_limits']=d['node']['scope_note'];n['primary_reading_extent']=[{'source_id':s['id'],'url':s['url'],'extent_and_limits':s['verification']['note']} for s in d['new_sources']];n['relationship_scope']=[{'target':e['target'],'claim':e['relationship'],'evidence':e['evidence_note']} for e in d['proposed_edges']];nf.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n')

# Final explicit copy corrections keep authority tokens intact.
from copy_fixes import main as apply_copy_fixes
apply_copy_fixes()
