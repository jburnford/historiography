"""Materialize the explicitly reviewed September 21 pilot, not a general matcher.

Author IDs below are review-record IDs inspected in this pilot. Reviewer decisions
require the institution present in the inspected source. All other pilot credits
receive explicit unresolved outcomes. Re-running replaces this draft ledger.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from repair_groundings import key,sha,write_json

WORK=Path(__file__).resolve().parent
raw=WORK/'generated/evidence';raw.mkdir(parents=True,exist_ok=True)
evidence=[]


def ev(eid,url,note,locator='Bibliographic entry / biography',snapshot=None):
    e={'id':eid,'url':url,'checked_on':'2026-09-21','locator':locator,'note':note,
       'scope':'Identity/bibliography only; not review-argument analysis.'}
    if snapshot:
        dst=raw/Path(snapshot).name
        if Path(snapshot).exists() and Path(snapshot).resolve()!=dst.resolve():shutil.copy2(snapshot,dst)
        if not dst.exists():raise ValueError('Missing saved evidence: '+str(snapshot))
        e.update(snapshot_path=str(dst.relative_to(WORK)),snapshot_sha256=sha(dst))
    evidence.append(e)


ev('source-credit',None,'Each decision is tied to its individual saved source header and catalog occurrence by JSON, raw HTML, and extraction fingerprints.','Occurrence-specific locator in occurrences.json')
ev('wd-pilot','https://www.wikidata.org/','Saved entity claims distinguish birth dates and GND identifiers; QID descriptions alone do not establish a credit.',snapshot=ROOT/'data/grounding-audit-2026-09-21/wikidata-entities.json')
ev('wd-controls','https://www.wikidata.org/','Saved entity records distinguish the two Manns, Schneiders and Harrisons and identify Bernstein and Ganguly.',snapshot=ROOT/'data/grounding-audit-2026-09-21/wikidata-controls.json')
for name,gnd in [('arnold','1026192242'),('walke','118784215X'),('angster','1022103326'),('mueller','115598553')]:
    ev(name+'-gnd','https://lobid.org/gnd/'+gnd,'GND identity fields and authority links checked against the source institution/book and saved Wikidata GND statement.',snapshot='/tmp/grounding-'+name+'-gnd.json')
ev('schaefer-judeophobia','https://www.suhrkamp.de/buch/peter-schaefer-judenhass-und-judenfurcht-t-9783458710288','Publisher links Judeophobia to Judaic scholar born 1943; excludes the historian born 1931.')
ev('schaefer-mysticism','https://www.mohrsiebeck.com/buch/the-origins-of-jewish-mysticism-9783161499319/','Publisher connects exact title with Judaic scholar born 1943 at Berlin/Princeton.')
ev('schaefer-bar','https://www.mohrsiebeck.com/buch/the-bar-kokhba-war-reconsidered-9783161587948/','Publisher identifies editor Peter Schäfer and supplies biography, born 1943. Source occurrence retains its less specific recorded role.')
ev('arnold-bio','https://uni-freiburg.de/frias/dr-jorg-arnold/','University biography links Freiburg and Nottingham appointments and lists Luftkrieg with Süß and Thießen.')
ev('walke-bio','https://history.wustl.edu/people/anika-walke','Washington University profile lists Pioneers and Partisans; GND independently records the same institution.')
ev('angster-bio','https://www.phil.uni-mannheim.de/neuere-und-neueste-geschichte/team/julia-angster/','Mannheim profile, born 1968, lists Konsenskapitalismus and Erdbeeren und Piraten. Catalog subtitle end-year differs; bibliographic discrepancy retained.')
ev('mueller-book','https://www.kulturkaufhaus.de/de/detail/ISBN-9783486577365/M%C3%BCller-Guido/Europ%C3%A4ische-Gesellschaftsbeziehungen-nach-dem-Ersten-Weltkrieg','Book biography identifies historian born 1957, Aachen/Stuttgart; incompatible with geographer born 1937.')
ev('mueller-preface','https://api.pageplace.de/preview/DT0400.9783486713763_A23143836/preview-9783486713763_A23143836.pdf','Author preface cites his edited international-relations volume with Conze/Lappenküper and his 2001 review of Loth/Osterhammel.','Introduction, footnote 1')
ev('bernstein-jefferson','https://digitalcommons.nyls.edu/fac_books/61/','NYLS repository identifies Richard B. Bernstein as author of Thomas Jefferson and records institutional affiliation.')
ev('bernstein-founders','https://digitalcommons.nyls.edu/fac_books/47/','NYLS repository identifies Richard B. Bernstein as author of The Founding Fathers Reconsidered.')
ev('ganguly-bio','https://polisci.indiana.edu/about/emeriti-faculty/ganguly-sumit.html','Indiana profile identifies Tagore Chair and lists Deadly Impasse and Ascending India with Thompson.')
ev('ganguly-future','https://manchesteruniversitypress.co.uk/9781526155139/','Publisher identifies Future of U.S.-India Security Cooperation editor as Indiana/Tagore Chair; confirms Šumit spelling variant.')
ev('ganguly-hallowed','https://academic.oup.com/book/2336','OUP lists editors Fair and Ganguly, identifying the latter with Indiana and the Tagore Chair. Confirms comma-and credit extraction.')
ev('mann-history','https://www.projekt-mida.de/staff/michael-mann/','Historian born 1959, Humboldt/Fernuniversität career; bibliography lists Geschichte Indiens, Sinnvolle Geschichte, Geschichte Südasiens, Bauernwiderstand, Beyond the Line and Civilizing Mission. Catalog wording differences are retained.')
ev('mann-sociology','https://soc.ucla.edu/person/michael-mann/','UCLA profile identifies sociologist born 1942 and lists Fascists and The Dark Side of Democracy.')
ev('schneider-mainz','https://zeithistorische-forschungen.de/autoren/ute-schneider-0','Journal author profile identifies Mainz book historian and lists Der unsichtbare Zweite.')
ev('schneider-ullstein','https://www.degruyterbrill.com/document/doi/10.1515/9783110337211/html?lang=de','Publisher lists Oels and Schneider, both Mainz, as editors of the Ullstein volume.')
ev('schneider-essen','https://www.uni-due.de/geschichte/ute_schneider.php','Institutional bibliography explicitly lists Die Macht der Karten, Kartenwelten, Dimensionen der Moderne and Handbuch Moderneforschung for the Essen historian.')
ev('harrison-warwick','https://warwick.ac.uk/fac/soc/economics/staff/mharrison/public/','Warwick economist bibliography lists The Economics of World War II and The Economics of World War I; separate from Oxford medical historian.')
ev('harrison-oxford','https://www.history.ox.ac.uk/people/professor-mark-harrison','Institutional biography identifies Oxford professor of history of medicine, matching RiH reviewer affiliations.')
ev('harrison-annual','https://wuhmo.web.ox.ac.uk/sites/default/files/wuhmo/documents/media/complete_annual_report_2002-2003.pdf','Oxford unit report lists Medicine and Victory and Disease and the Modern World under Mark Harrison.','Page numbered 27, Mark Harrison publications')
ev('harrison-commerce','https://academic.oup.com/book/7242','OUP attaches the exact book to Oxford professor of history of medicine.')
ev('harrison-social','https://global.history.ox.ac.uk/symplectic/publications/list/2364241/74413216/119941/?filter_types-2364241%5B%5D=&page-2364241=3&widget_limit_to_favourites-2364241=0&widget_max_publications_to_display-2364241=5&widget_page_title-2364241=Professor+Mark+Harrison&widget_show_author_and_editor_names-2364241=0','Oxford publication list associates the Pati/Harrison edited volume with the medical historian.')

specs=[
 ('peter-schaefer-judaist','Peter Schäfer','Q97091',['schaefer-judeophobia','wd-pilot'],[]),
 ('joerg-arnold-historian','Jörg Arnold','Q95266163',['arnold-gnd','arnold-bio','wd-pilot'],['Q112434101']),
 ('anika-walke','Anika Walke','Q130815595',['walke-gnd','walke-bio','wd-pilot'],['Q130598476']),
 ('julia-angster','Julia Angster','Q95193358',['angster-gnd','angster-bio','wd-pilot'],['Q112475577']),
 ('guido-mueller-historian','Guido Müller','Q95242932',['mueller-gnd','mueller-book','wd-pilot'],[]),
 ('richard-b-bernstein','Richard B. Bernstein','Q7323841',['bernstein-jefferson','wd-controls'],[]),
 ('sumit-ganguly','Sumit Ganguly','Q17090449',['ganguly-bio','wd-controls'],[]),
 ('michael-mann-historian','Michael Mann (South Asia historian)','Q1928511',['mann-history','wd-controls'],[]),
 ('michael-mann-sociologist','Michael Mann (sociologist)','Q1425193',['mann-sociology','wd-controls'],[]),
 ('ute-schneider-book-historian','Ute Schneider (book historian)','Q93972366',['schneider-mainz','wd-controls'],[]),
 ('ute-schneider-cultural-historian','Ute Schneider (cultural historian)','Q16295137',['schneider-essen','wd-controls'],[]),
 ('mark-harrison-economist','Mark Harrison (economist)','Q110009814',['harrison-warwick','wd-controls'],[]),
 ('mark-harrison-medical-historian','Mark Harrison (medical historian)','Q56434388',['harrison-oxford','wd-controls'],[]),
]
people=[{'id':pid,'label':label,'preferred_qid':qid,'evidence':evs,
         'alternate_qids':[{'qid':q,'status':'suspected_duplicate_not_accepted_equivalence'} for q in alts]} for pid,label,qid,evs,alts in specs]
by_person={p['id']:p for p in people}

# Explicit title-level decisions; exact source and extraction hashes are attached
# below. Mapping applies only to the identified pilot contributor in each record.
author={}
def books(name,pid,eids,ids):
    for rid in ids.split():author[rid,name]=(pid,eids)
books('peter schafer','peter-schaefer-judaist',['schaefer-judeophobia'],'1482')
books('peter schafer','peter-schaefer-judaist',['schaefer-mysticism'],'32796')
books('peter schafer','peter-schaefer-judaist',['schaefer-bar'],'18385')
books('jorg arnold','joerg-arnold-historian',['arnold-bio'],'29699')
books('anika walke','anika-walke',['walke-bio'],'48117')
books('julia angster','julia-angster',['angster-bio'],'17221 37895')
books('guido muller','guido-mueller-historian',['mueller-book'],'21164')
books('guido muller','guido-mueller-historian',['mueller-preface'],'19030 19368')
books('r b bernstein','richard-b-bernstein',['bernstein-jefferson'],'9650')
books('r b bernstein','richard-b-bernstein',['bernstein-founders'],'26238')
books('sumit ganguly','sumit-ganguly',['ganguly-hallowed'],'25255')
books('sumit ganguly','sumit-ganguly',['ganguly-future'],'60527')
books('sumit ganguly','sumit-ganguly',['ganguly-bio'],'47704 49918')
books('michael mann','michael-mann-historian',['mann-history'],'20731 29531 30560 34881 41233 42498 37390')
books('michael mann','michael-mann-sociologist',['mann-sociology'],'10938 12486 21721')
books('ute schneider','ute-schneider-book-historian',['schneider-mainz'],'19148')
books('ute schneider','ute-schneider-book-historian',['schneider-ullstein'],'45564')
books('ute schneider','ute-schneider-cultural-historian',['schneider-essen'],'19549 20867 23299 46355')
books('mark harrison','mark-harrison-economist',['harrison-warwick'],'3250 11971')
books('mark harrison','mark-harrison-medical-historian',['harrison-annual'],'13722 24073')
books('mark harrison','mark-harrison-medical-historian',['harrison-commerce'],'35383')
books('mark harrison','mark-harrison-medical-historian',['harrison-social'],'24926')

occurrences=json.loads((WORK/'occurrences.json').read_text())
decisions=[]
for o in occurrences:
    if not o['pilot']:continue
    n=key(o['display_name']);pid=None;evs=[]
    rationale='Credit reviewed, but no institution or independent exact-review attribution established in this pilot. Name and topic alone do not justify acceptance. Retain the old QID only as an unverified suggestion.'
    if o['role']!='reviewer':
        if (o['review_id'],n) not in author:raise ValueError('Unreviewed pilot book '+str(o))
        pid,evs=author[o['review_id'],n]
        rationale='The source names this contributor on this particular book. Checked bibliography/biography connects the book to this person; authority identity checked separately. Decision is scoped to this occurrence.'
    elif n=='r b bernstein' and 'New York Law School' in (o['affiliation'] or ''):
        pid='richard-b-bernstein';evs=['bernstein-jefferson'];rationale='Recorded reviewer name and New York Law School affiliation match the institutional author identity; this exact occurrence is accepted.'
    elif n=='jorg arnold' and any(x in (o['affiliation'] or '') for x in ['Freiburg','Nottingham']):
        pid='joerg-arnold-historian';evs=['arnold-bio','arnold-gnd'];rationale='Recorded historical institution matches the university career and GND biography. Use GND-linked Q95266163; alternate QID remains a suspected duplicate, not an asserted Wikidata merge.'
    elif n=='anika walke' and o['affiliation']=='Washington University':
        pid='anika-walke';evs=['walke-bio','walke-gnd'];rationale='Source reviewer institution agrees with university and GND records. Use the authority-linked Q130815595; preserve alternate QID as a suspected duplicate.'
    elif n=='sumit ganguly' and 'Indiana University' in (o['affiliation'] or ''):
        pid='sumit-ganguly';evs=['ganguly-bio'];rationale='Recorded name and Indiana affiliation/Tagore Chair match the institutional identity.'
    elif n=='mark harrison' and 'Warwick' in (o['affiliation'] or ''):
        pid='mark-harrison-economist';evs=['harrison-warwick'];rationale='Source explicitly names Warwick Economics. Preserve distinction from the Oxford medical historian.'
    elif n=='mark harrison' and 'Oxford' in (o['affiliation'] or ''):
        pid='mark-harrison-medical-historian';evs=['harrison-oxford'];rationale='Source explicitly names Oxford; matches medical historian and is distinct from the Warwick economist.'
    elif n=='guido muller' and o['review_id']=='34213':
        pid='guido-mueller-historian';evs=['mueller-preface'];rationale='The historian cites this exact Loth/Osterhammel review in his own book introduction; stronger than topic/name agreement.'
    rejected=[]
    if pid and o['legacy_qid'] and o['legacy_qid']!=by_person[pid]['preferred_qid']:
        if o['legacy_qid'] not in [x['qid'] for x in by_person[pid]['alternate_qids']]:rejected=[o['legacy_qid']]
    decisions.append({'id':'pilot-20260921-'+o['occurrence_id'].rsplit(':',1)[1],
      'occurrence_id':o['occurrence_id'],'occurrence_fingerprint':o['occurrence_fingerprint'],
      'source_json_sha256':o['source_json_sha256'],'source_raw_sha256':o['source_raw_sha256'],
      'status':'accepted' if pid else 'unresolved','person_id':pid,'legacy_qid':o['legacy_qid'],
      'rejected_qids':rejected,'rationale':rationale,'evidence':list(dict.fromkeys(['source-credit',*evs,*(by_person[pid]['evidence'] if pid else [])])),
      'reviewed_on':'2026-09-21','reviewer':'Codex; source-checked pilot','supersedes':[]})

ledger={'schema_version':'grounding-repair-1.0','baseline_manifest_sha256':sha(WORK/'baseline-manifest.json'),
        'scope':'Ten-name pilot; accepted decisions are individual credits; unresolved assignments remain provisional.',
        'people':people,'evidence':evidence,'decisions':decisions}
write_json(WORK/'decisions.json',ledger)
print('Pilot decisions:',len(decisions),'accepted:',sum(d['status']=='accepted' for d in decisions))
