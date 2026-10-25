import json,re
from pathlib import Path
p=Path('data/field-research/dissertation-canon-review-2026-10-24/recent-regional-review.json');r=json.load(open(p))
r['source_checks']=[s for s in r['source_checks'] if s['id']!='rosenwein_reddy_frameworks']
r['source_checks'] += [
 {'id':'rosenwein_cornell','url':'https://cornellpress.cornell.edu/book/9780801474163/','scope':'Publisher description checked; book unread','support':'Rosenwein reconstructs coexisting emotional communities, norms of valuation/expression and religious styles, and critiques a single civilizing-process account. The linked paperback lists June 2007; do not overwrite the corpus original 2006 work date.'},
 {'id':'seixas_project','url':'https://www.historicalthinking.ca/books','scope':'Author project bibliography checked','support':'The Big Six is jointly credited to Peter Seixas and Tom Morton. Project page lists 2012 while corpus gives 2013; verify the cited edition before assigning a chronology date.'},
 {'id':'ahmed_edinburgh','url':'https://edinburghuniversitypress.com/the-cultural-politics-of-emotion-772.html','scope':'Publisher description checked; book unread','support':'Sara Ahmed examines relations between emotions, language and bodies, including emotionality of texts, asylum/migration and reconciliation. This is an adjacent framework to investigate, not proof of a unified emotions school.'}
]
for x in r['proposals']:
 if x['id']=='emotions_frameworks':x['source_ids']=['reddy_cambridge','rosenwein_cornell','ahmed_edinburgh']
 if x['id']=='historical_consciousness_learning':
  x['source_ids'].append('seixas_project');x['limits'].append('Big Six project bibliography lists 2012 while the frozen work record gives 2013; edition identity needs checking before chronology work.')
 for c in x['existing_coverage']:
  if x['id']=='space_social_production' and c['node_id']=='urbanhistory':c['detail']='Harvey is an existing indexed resource for space, capital and the cultural city.'
for x in r['deferred_or_already_covered']:
 if x['topic']=='Archive/race/critical fabulation':
  x['existing_ids']=['archival_turn','saidiya_hartman','marisa_j_fuentes'];x['decision']='Already substantially covered';x['reason']='The new Hartman and Fuentes standalone entries and archival_turn already cover substantive methods. Further author names alone do not establish missing content.'
 elif x['topic']=='Material culture and object biographies':
  x['decision']='Already substantially covered';x['reason']='Appadurai, circulation/value, Kopytoff object biography and commodity histories already have strands. Jane Bennett, Vibrant Matter (15 dated), and Tsing, Friction (13 dated), remain lower-count leads; they do not establish absence of a material turn. Tony Bennett is a different indexed person.'
 else:
  x['decision']='Regional research lead only';x['country']='All 16 FR';x['reason']='Relevant to existing narrative, truth and life-writing content, but the small recent-publication sample and a 403 publisher access failure warrant lower priority than the ten proposals above. The institutional bibliography verifies the 2014 title; its detailed argument remains unread.';x['publisher_result']='403 Forbidden'
r['sample']['cohort_note']='Recomputed contrasts explicitly use Canada/US 2015–2026 versus 2000–2009. Historical reports label their contrasts 2015–25 and 2020–25; retain these labels when quoting them, distinct from the public 2020–2026 series. The recomputed Canada/US recent denominator 1,893 matches the older labelled denominator. The historical Europe contrast is 2015–25 versus 2000–14, with denominators 1,351 versus 674.'
r['sample']['composition_limits']=[
 'Sampled strict History-programme PhDs, not all History PhDs or adjacent disciplines.',
 'University, country, language and subfield mix changes over time; partly embargoed recent cohorts and US thinness before 2010 affect apparent growth.',
 'Country describes dissertation programme/repository geography, not the geography studied.',
 'Counts establish cited-work presence, not influence, agreement, field membership or rhetorical citation role.',
 'Post-2000 works could not be cited by earlier cohorts; publication age and exposure must be considered.',
 'A work-level count is a deduplicated dissertation union for that exact key. No edition, translation or author-key totals have been summed.'
]
# Restore readable word/number boundaries in our editorial prose only; preserve all corpus keys, raw rows and titles.
def prose(t):
 t=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', t);t=re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', t)
 for a,b in {'CAUS':'Canada/US','CAand':'CA and','USand':'US and','USsample':'US sample','recentCAUS':'recent Canada/US','recentpublication':'recent publication','allstrict':'all strict','publicworkcutoff':'public work cutoff','firstauthorcreditisnotsoleauthorship':'first-author credit is not sole authorship','jointlycreditedPeterSeixasandTomMorton':'jointly credited Peter Seixas and Tom Morton','Wineburgbook':'Wineburg book','same-titlearticle':'same-title article','Swedishcollection':'Swedish collection','Swedishciters':'Swedish citers','RüsenHistory':'Rüsen History','RüsenEnglish':'Rüsen English','SwedishHistoryprogramme':'Swedish History-programme','weakglobal':'weak global','vsunstratified':'versus unstratified','recent1893':'recent 1,893','strictHistoryprogrammePhDs':'strict History-programme PhDs','whole-bookreading':'whole-book reading','USliterature':'US literature','UnitedStates':'United States','Cowie cultural':'Cowie cultural','noHunt':'no Hunt','NoHartog':'No Hartog','ExistingKoselleckdoes':'Existing Koselleck does','publisheronly':'publisher only'}.items():t=t.replace(a,b)
 return t
for x in r['proposals']:
 for k in ['title','missing_or_underdeveloped_content','proposed_action']:x[k]=prose(x[k])
 x['limits']=[prose(t) for t in x['limits']]
 for c in x['existing_coverage']:c['detail']=prose(c['detail'])
for s in r['source_checks']:s['support']=prose(s['support'])
# A few clear formulations replace compact provisional drafting.
for x in r['proposals']:
 if x['id']=='historicity_presentism':x['limits']=['42 of 59 dated citers are FR and 17 CA: a French-language and regional signal.','The historical Europe contrast is 35/1,351 recent versus 7/674 baseline, labelled 2015–25 versus 2000–14; these are not Canada/US denominators.','French 2003, revised French editions and English 2015 must not be conflated.','Existing Koselleck coverage does not prove an influence edge; the publisher names him as an inspiration.']
 if x['id']=='historical_consciousness_learning':x['limits']=['Swedish citers: Wineburg 12/20, Rüsen History 14/18, Swedish collection 22/22, Big Six 7/11. This reflects Swedish History-programme composition, not universal History PhD reading.','Rüsen English 2005 and Swedish 2004 are distinct works; do not sum as editions without checking contents.','Wineburg book 2001 is distinct from the same-title article 1998 and reprint 2010.','Big Six is jointly credited to Peter Seixas and Tom Morton. The project bibliography lists 2012 while the frozen corpus gives 2013; check the cited edition before chronology work.']
# Validate all existing graph and source references, public series n, and strict count concordance.
g=json.load(open('historiography-1920-2000.json'));N={n['id']:n for n in g['nodes']};S={s['id'] for s in r['source_checks']}
for x in r['proposals']:
 assert set(x['source_ids'])<=S
 for c in x['existing_coverage']:
  n=N[c['node_id']]; strands={s['id'] for s in n.get('strands',[])}
  assert not c.get('strand_id') or c['strand_id'] in strands
  assert not c.get('strand_ids') or set(c['strand_ids'])<=strands
for w in r['works'].values():
 assert w['computed_strict_n']==int(w['cited_by_strict_phds'])
 if w.get('public_shard_record'):assert w['dated_n']==w['public_shard_record']['n']
for x in r['deferred_or_already_covered']:assert set(x.get('existing_ids',[]))<=N.keys()
r['validation']={'proposals':len(r['proposals']),'exact_work_records':len(r['works']),'work_strict_count_concordance':True,'public_series_total_concordance':True,'existing_node_strand_and_source_ids_resolve':True,'note':'Review statistics and reference consistency checked; this does not validate substantive historical interpretation or establish citation use.'}
json.dump(r,open(p,'w'),ensure_ascii=False,indent=2);print(p,'validated')
extra=[{'id':'stern_oup','url':'https://academic.oup.com/book/11841','scope':'Publisher abstract and bibliographic metadata checked; book unread','support':'The work is by Philip J. Stern (2011), not another Stern. It treats the East India Company as a corporate sovereign and challenges a simple commercial-to-political transformation narrative.'},{'id':'burbank_cooper_frontmatter','url':'https://www.degruyterbrill.com/document/doi/10.1515/9781400834709-fm/pdf','scope':'Publisher-hosted frontmatter extract checked','support':'Princeton 2010 work is jointly authored by Jane Burbank and Frederick Cooper. Preserve both credits despite the frozen first-author work key.'}]
r=json.load(open(p));r['source_checks']+=extra
for x in r['proposals']:
 if x['id']=='imperial_jurisdiction':x['source_ids']+=['stern_oup','burbank_cooper_frontmatter']
json.dump(r,open(p,'w'),ensure_ascii=False,indent=2)
r['source_checks']=list({s['id']:s for s in r['source_checks']}.values())
for x in r['proposals']:x['source_ids']=list(dict.fromkeys(x['source_ids']))
json.dump(r,open(p,'w'),ensure_ascii=False,indent=2)
print('Final sources:',len(r['source_checks']))
