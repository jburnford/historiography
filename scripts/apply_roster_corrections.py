#!/usr/bin/env python3
"""Apply/audit the user's four named-person corrections without site changes."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_graph import validate
OUT=ROOT/'data/production-batches/roster-corrections-1.121'
GRAPH=ROOT/'historiography-1920-2000.json'
BASE=ROOT/'drafts/historiography-1920-2000.v1.120.json'
DAY='2026-09-18'
def read(p):return json.loads(p.read_text())
def serial(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def transform(before):
    if before['revision_history'][-1]['version']!='1.120':raise ValueError('Expected incoming revision 1.120')
    g=deepcopy(before);nodes={n['id']:n for n in g['nodes']}
    for pid,label in [('paul_e_lovejoy','Paul E. Lovejoy'),('keith_nield','Keith Nield'),('helen_clifford','Helen Clifford')]:
        if any(p['id']==pid for p in g['people']):raise ValueError('Existing person needs reconciliation: '+pid)
        g['people'].append(dict(id=pid,label=label))
    sources=[
        dict(id='eley_nield_politics_1980',title='Geoff Eley and Keith Nield, “Why does social history ignore politics?” (1980).',citation='Social History 5(2), 249–271. DOI 10.1080/03071028008567479.',url='https://www.tandfonline.com/doi/abs/10.1080/03071028008567479',scope_note='Publisher byline/title/issue checked. Establishes a named intervention in social history; body unread. 1980 issue, not the online posting of 30 May 2008.'),
        dict(id='wrigley_economic_ehs',title='Economic History Society, obituary of E. A. (Tony) Wrigley (2022).',citation='Economic History Society, “Obituary: Professor Sir Tony Wrigley (August 1931 – 24 February 2022)”.',url='https://ehs.org.uk/obituary-professor-sir-tony-wrigley/',scope_note='Institutional account of economic and social history, People, Cities and Wealth (1987), and Continuity, Chance and Change (1988). Used for field association and bounded work scope, not acceptance of every biographical/bibliographic detail or a body-text check of the books.'),
        dict(id='lovejoy_diaspora_1997',title='Paul E. Lovejoy, “The African Diaspora: Revisionist Interpretations of Ethnicity, Culture and Religion under Slavery” (1997).',citation='Studies in the World History of Slavery, Abolition and Emancipation II(1), 1997.',url='https://ppgh.ufba.br/sites/ppgh.ufba.br/files/lovejoy_-_af_diaspora_revisionist_interpretations.pdf',scope_note='Indexed author abstract read from university-hosted article. Supports a specific African-centred diaspora research programme. Full PDF retrieval failed certificate verification; no body or reception claim.'),
        dict(id='lovejoy_york_identity',title='York University, Paul E. Lovejoy faculty profile.',citation='Department of History, York University, Paul E. Lovejoy, accessed 18 September 2026.',url='https://profiles.laps.yorku.ca/profiles/plovejoy/',scope_note='Institutional name, field and publication identity only. Distinct from Arthur O. Lovejoy. This profile includes later projects and internally varying dates; no institutional founding or demographic assertion imported.')]
    sources.append(dict(id='berg_clifford_consumers_1999',title='Maxine Berg and Helen Clifford, eds., Consumers and Luxury: Consumer Culture in Europe, 1650–1850 (1999).',citation='Manchester University Press, 1999; Warwick Research Archive Portal bibliographic record.',url='https://wrap.warwick.ac.uk/id/eprint/38873/',scope_note='Author-institution repository metadata checked for both editors, title and year; no full-volume reading. One Google Books edition returned an unrelated Conservative-women description and was not used as argument evidence.'))
    g['sources'].extend(sources)
    def append(field,pid,context,works,sids):
        node=nodes[field]
        if any(r['person_id']==pid for r in node['representative_people']):raise ValueError('Duplicate representative: '+pid)
        node['representative_people'].append(dict(person_id=pid,role='historian',context=context,works=works,source_ids=sids,basis='source_review'))
        node['source_ids']=list(dict.fromkeys(node['source_ids']+sids))
    social_context='Practitioner in social history and coauthor of its debate over politics. The 1980 article establishes participation; its full argument remains unchecked. His existing Sonderweg critique and public-sphere contexts remain distinct.'
    for pid in ['geoff_eley','keith_nield']:
        append('social',pid,social_context if pid=='geoff_eley' else 'Coauthors with Geoff Eley a named intervention about politics within social history; both author credits retained. Publisher metadata checked, article body unread.',
               'With '+('Keith Nield' if pid=='geoff_eley' else 'Geoff Eley')+', “Why does social history ignore politics?” (1980)',['eley_nield_politics_1980'])
    nodes['social']['strands'].append(dict(id='eley_nield_politics',title='Politics within social-history debate',person_ids=['geoff_eley','keith_nield'],focus='Eley and Nield participate in debate about politics within social history. The verified article metadata establishes this intervention; no detailed account of its unread argument is supplied.',works='“Why does social history ignore politics?” (1980), coauthored',source_ids=['eley_nield_politics_1980'],basis='editorial_distinction'))
    nodes['social']['representative_figures_and_works']+=' Geoff Eley and Keith Nield: “Why does social history ignore politics?” (1980).'
    append('economic','e_a_wrigley','Economic historian of industrialization, growth and population change. This complements his demographic, quantitative and social-history work; these are overlapping practices.',
        'People, Cities and Wealth (1987); Continuity, Chance and Change (1988)',['wrigley_economic_ehs'])
    nodes['economic']['strands'].append(dict(id='wrigley_growth',title='Population and the character of industrial growth',person_ids=['e_a_wrigley'],focus='Wrigley investigates population change and the contingent character of industrial growth. This bounded summary follows the Economic History Society account; the two books have not been reread here.',works='People, Cities and Wealth (1987); Continuity, Chance and Change (1988)',source_ids=['wrigley_economic_ehs'],basis='editorial_distinction'))
    nodes['economic']['representative_figures_and_works']+=' E. A. Wrigley: People, Cities and Wealth (1987); Continuity, Chance and Change (1988).'
    for field in ['africanhist','atlantic']:
        append(field,'paul_e_lovejoy','Historian of African slavery and diaspora. His 1997 programme proposes historically specific African origins, biographical and oral evidence, and the reconstruction of forced movements; checked at indexed-abstract scope.',
            '“The African Diaspora: Revisionist Interpretations of Ethnicity, Culture and Religion under Slavery” (1997)', ['lovejoy_diaspora_1997','lovejoy_york_identity'])
        nodes[field]['strands'].append(dict(id='lovejoy_african_diaspora',title='African histories within diaspora reconstruction',person_ids=['paul_e_lovejoy'],focus='Lovejoy proposes connecting diaspora research to historically specific African backgrounds and individual trajectories. This is a scoped programme, not timeless ethnic continuity or a claim that all diaspora scholarship adopts it.',works='“The African Diaspora” (1997), indexed author abstract',source_ids=['lovejoy_diaspora_1997'],basis='editorial_distinction'))
        nodes[field]['representative_figures_and_works']+=' Paul E. Lovejoy: “The African Diaspora” (1997).'
    for pid,other in [('maxine_berg','Helen Clifford'),('helen_clifford','Maxine Berg')]:
        append('consumption',pid,'Coedits with '+other+' an inquiry into European consumer culture and luxury. Editorial participation and subject are checked from the university repository; not every chapter is attributed to either editor.',
            'With '+other+', eds., Consumers and Luxury: Consumer Culture in Europe, 1650–1850 (1999)',['berg_clifford_consumers_1999'])
    nodes['consumption']['strands'].append(dict(id='berg_clifford_luxury',title='Luxury and European consumer culture',person_ids=['maxine_berg','helen_clifford'],focus='Berg and Clifford coedit a volume on luxury and consumer culture in Europe, 1650–1850. This records their editorial contribution; detailed chapter arguments remain unchecked.',works='Consumers and Luxury (1999), coedited volume',source_ids=['berg_clifford_consumers_1999'],basis='editorial_distinction'))
    nodes['consumption']['representative_figures_and_works']+=' Maxine Berg and Helen Clifford, eds.: Consumers and Luxury (1999).'
    wall=next(r for r in nodes['dependency']['representative_people'] if r['person_id']=='immanuel_wallerstein')
    wall['role']='historian'
    wall['context']='Practitioner and theorist of world-systems historical analysis. '+wall['context']+' The role describes his practice in this selection, not an exclusive disciplinary credential or affiliation with every dependency programme.'
    g['revision_history'].append(dict(version='1.121',date=DAY,summary='User-requested roster corrections: Eley and coauthor Nield in social history, Wrigley in economic history, Paul E. Lovejoy in African and Atlantic histories, Wallerstein as a world-systems practitioner, Berg and coeditor Clifford in consumption. Existing roles elsewhere retained; no post-2000 research packet imported.',added_person_ids=['paul_e_lovejoy','keith_nield','helen_clifford'],added_source_ids=[s['id'] for s in sources],acceptance_record='data/production-batches/roster-corrections-1.121/acceptance.json'))
    return g

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:
        record=read(OUT/'acceptance.json')
        if sha(BASE)!=record['baseline_sha256']:raise ValueError('Baseline hash mismatch')
        if read(GRAPH)!=transform(read(BASE)):raise ValueError('Exact reconstruction mismatch')
        for name,expected in record['evidence_hashes'].items():
            if sha(ROOT/name)!=expected:raise ValueError('Evidence changed: '+name)
        g=read(GRAPH)
    else:
        before=read(GRAPH);g=transform(before)
        errors,_=validate(g,read(ROOT/'seminar-pathways.json'))
        if errors:raise ValueError('\n'.join(errors))
        if BASE.exists() and BASE.read_bytes()!=GRAPH.read_bytes():raise ValueError('Refusing to replace snapshot')
        BASE.write_bytes(GRAPH.read_bytes());OUT.mkdir(parents=True,exist_ok=True)
        paths=[ROOT/'data/extension-2026/health-geography-05/raw'/name for name in ['classification.json','lovejoy-primary.json','berg.json']]
        record=dict(revision='1.121',date=DAY,authorization='User identifies missing Paul Lovejoy, requests Eley in New Social History, Wrigley as economic historian, Wallerstein as world-systems practitioner, and Berg linked to consumption.',baseline=str(BASE.relative_to(ROOT)),baseline_sha256=sha(BASE),
            evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},
            prior_wallerstein_record=next(r for n in before['nodes'] if n['id']=='dependency' for r in n['representative_people'] if r['person_id']=='immanuel_wallerstein'),
            changes='Seven roster additions, one contextual role correction, three shared people, five sources and five strands. No new influence edges, full person nodes or post-2000 imports.',
            website_handoff='Fable owns source/build; no website files touched.')
        GRAPH.write_text(serial(g));record['production_sha256']=sha(GRAPH);(OUT/'acceptance.json').write_text(serial(record))
    errors,warnings=validate(g,read(ROOT/'seminar-pathways.json'))
    print(serial(dict(errors=errors,warnings=warnings,nodes=len(g['nodes']),edges=len(g['edges']),sources=len(g['sources']),people=len(g['people']))),end='')
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())
