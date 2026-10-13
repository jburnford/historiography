#!/usr/bin/env python3
"""PhD-citation evidence for four Canadian group drafts: cdn_intellectual_cultural, cdn_religion_reform,
liberal_order_framework, cdn_sixties. Reads the dissertation citation graph once and prints JSON with, per group,
the citing-PhD count for each listed work, engagement (PhDs citing two or more listed works), early/late shares,
overlaps between the four groups, selected co-citations and francophone-institution shares.

Run from the repository root:
    python3 data/extension-2026/canadian-historiography-groups-request-2026-10-12/drafts/liberal_order_framework/four_drafts_evidence.py

Counts are dissertations (in_analysis, 2009-2026), not citations. Works match by title pattern AND an AUTHORED
person-key pattern; variant work nodes are merged by union. Bibliographies record consultation, not influence.
"""
import json, re
from collections import Counter, defaultdict
from pathlib import Path

GRAPH = Path('data/field-research/dissertation-citations-2026-10-11/graph.json')
g = json.loads(GRAPH.read_text())
diss, works, cites, authors = {}, {}, defaultdict(set), defaultdict(set)
for n in g['nodes']:
    if n['type'] == 'Dissertation' and n.get('in_analysis'):
        diss[n['id']] = dict(year=n.get('year'), institution=n.get('institution'))
    elif n['type'] == 'Work':
        works[n['id']] = dict(title=n.get('title'), year=n.get('year'))
for e in g['edges']:
    if e['type'] == 'CITES' and e['source'] in diss:
        cites[e['target']].add(e['source'])
    elif e['type'] == 'AUTHORED':
        authors[e['target']].add(e['source'])
IN = lambda d: diss[d]['year'] and 2009 <= diss[d]['year'] <= 2026
N = sum(1 for d in diss if IN(d))
early = {d for d in diss if IN(d) and diss[d]['year'] <= 2014}
late = {d for d in diss if IN(d) and diss[d]['year'] >= 2020}
FR = {'laval', 'montreal', 'sherbrooke', 'uqam'}


def citers(pat, auth):
    r = re.compile(pat, re.I)
    s = set()
    for w, m in works.items():
        if m['title'] and r.search(m['title']) and any(re.search(auth, a, re.I) for a in authors.get(w, ())):
            s |= {d for d in cites.get(w, ()) if IN(d)}
    return s


GROUPS = {
 'cdn_intellectual_cultural': [
  ('berger_1970','sense of ?power','berger'),('berger_1976','writing ?of ?canadian history','berger'),('berger_1983','science,? god','berger'),
  ('mckillop_1979','disciplined ?intelligence','mckillop'),('mckillop_1994','matters ?of ?mind','mckillop'),
  ('owram_1980','promise ?of ?eden','owram'),('owram_1986','gover?n?ment generation','owram'),('shore_1987','science ?of ?social redemption','shore'),
  ('mckay_1994','quest ?of ?the folk|quest of the folk','m.?c.?k.?ay|mackay'),('nelles_1999','art of n?ation.building','nelles'),
  ('francis_1992','imaginary indian','francis\\|daniel'),('francis_1997','national dreams','francis'),('vance_1997','death ?so ?noble','vance'),
  ('coates_morgan_2002','heroines and history','coates|morgan'),('heaman_1999','inglorious arts','heaman'),('radforth_2004','royal spectacle','radforth'),
  ('walden_1997','becoming modern in toronto','walden'),('litt_1992','muses,? the masses','litt'),('vipond_1992','^listening in','vipond'),
  ('lamonde_2000','histoire sociale des id','lamonde')],
 'cdn_religion_reform': [
  ('allen_1971','social passion','allen'),('cook_1985','regenerators','cook'),('fraser_1988','social uplifters','fraser'),('westfall_1989','^two worlds','westfall'),
  ('vandie_1989','evangelical mind','van die'),('gauvreau_1991','evangelical century','gauvreau'),('marshall_1992','secularizing the faith','marshall'),
  ('airhart_1992','serving the present age','airhart'),('christie_gauvreau_1996','full.orbed','christie|gauvreau'),('semple_1996','lord.?s dominion','semple'),
  ('hamelin_gagnon_1984','histoire d[eu] catholicisme qu','hamelin|gagnon'),('perin_1990','rome in canada','perin'),('clarke_1993','piety and nationalism','clarke'),
  ('mcgowan_1999','waning of ?the green','mcgowan'),('ferretti_1999','br.ve histoire de l.?.glise','ferretti'),('meunier_warren_2002','sortir de la grande noirceur','meunier|warren'),
  ('bienvenue_2003','quand la jeunesse entre','bienvenue'),('gauvreau_2005','catholic origins of quebec|origines catholiques','gauvreau'),
  ('christie_gauvreau_2010','christian churches and their peoples','christie|gauvreau'),('marks_1996','revival?i?s? ?and ?roller rinks','marks'),('marks_2017','infidels and the damn','marks'),('hubert_2000','sur la terre comme au ciel','hubert')],
 'liberal_order_framework': [
  ('mckay_2000','liberal order framework','m.?c.?k.?a.?y'),('constant_ducharme_2009','liberal(ism)? and hegemony','constant|ducharme|perry|and jean'),
  ('greer_radforth_1992','colonial leviathan','greer|radforth|reer'),('curtis_1988','building the educational? state','curtis'),('curtis_1992','true gove?r?n?ment by choice','curtis'),
  ('curtis_2001','politics of ?population','curtis'),('curtis_2012','ruling by schooling','curtis'),('ducharme_2010','concept de libert|idea of liberty','ducharme'),
  ('roy_1988','progr.s,? harmonie','roy'),('mcnairn_2000','capacit?l?y to judge','mcn|m cn'),('bannister_2009','counter.revolution|loyalist order','ban+ister'),
  ('mckay_2005','rebels,? reds','mckay'),('mckay_2008','reasoning otherwise','mckay'),('heaman_2017','tax, order','heaman'),('greer_2018','property and dispossession','greer'),
  ('weaver_2003','great land rush','weaver'),('greer_1985','peasant,? lord','greer'),('sandwell_2003','limits of liberalism','sandwell')],
 'cdn_sixties': [
  ('kostash_1980','long ?way ?from home','kostash'),('levitt_1984','children of privilege','levitt'),('owram_1996','b[o0]r?n at the right time','owram|orwam'),
  ('igartua_2006','other quiet revolution','ig'),('clement_2008','canada.?s rights revolution','clement'),('palmer_2009','canada.?s 1960s','palmer'),
  ('dubinsky_2009','new world coming','dubinsky'),('mills_2010','empire within','mills|mins'),('henderson_2011','making the scene','henderson'),
  ('campbell_clement_kealey_2012','debating dissent','campbell|clement|kealey'),('austin_2013','fear of a black nation','austin'),
  ('milligan_2014','rebel youth','milligan'),('warren_2008','douce anarchie','warren'),('behiels_1985','prelude to quebec','behiels'),
  ('meunier_warren_2002','sortir de la grande noirceur','meunier|warren'),('bienvenue_2003','quand la jeunesse entre','bienvenue'),
  ('gauvreau_2005','catholic origins of quebec|origines catholiques','gauvreau'),('martel_1997','deuil d.un pays','martel'),('gelinas_2007','droite intellectuelle qu','gelinas'),
  ('champion_2010','strange demise of british canada','champion'),('kinsman_gentile_2010','canadian war on queers','kinsman|gentile'),('rutherford_2020','canada.?s other red scare','rutherford')]}

COCITE = {
 'mckay_1994 & lears_1981': (('quest ?of ?the folk', 'm.?c.?k.?ay|mackay'), ('no place ?of ?grace', 'lears')),
 'mckay_2000 & polanyi_1944': (('liberal order framework', 'm.?c.?k.?a.?y'), ('great transform', 'polanyi')),
 'mckay_2000 & macpherson_1962': (('liberal order framework', 'm.?c.?k.?a.?y'), ('possessive', 'macpherson')),
 'mckay_2000 & gramsci': (('liberal order framework', 'm.?c.?k.?a.?y'), ('prison notebooks|quaderni', 'gramsci')),
 'mckay_2000 & corrigan_sayer_1985': (('liberal order framework', 'm.?c.?k.?a.?y'), ('great arch', 'corrigan|sayer')),
 'mckay_2000 & beckert_2014': (('liberal order framework', 'm.?c.?k.?a.?y'), ('empire of cotton', 'beckert')),
 'mckay_2000 & valverde_1991': (('liberal order framework', 'm.?c.?k.?a.?y'), ('light,? soap', 'valverde')),
 'mckay_2000 & foucault_governmentality': (('liberal order framework', 'm.?c.?k.?a.?y'), ('governmentality|security, territory|birth of biopolitics', 'foucault')),
 'mills_2010 & fanon': (('empire within', 'mills|mins'), ('wretched of the earth|black skin|damn.s de la terre|peau noire', 'fanon')),
 'owram_1996 & marwick_1998': (('b[o0]r?n at the right time', 'owram'), ('^the sixties', 'marwick')),
 'christie_gauvreau_1996 & brown_2001': (('full.orbed', 'christie|gauvreau'), ('death of ?christian britain', 'brown')),
 'cook_1985 & valverde_1991': (('regenerators', 'cook'), ('light,? soap', 'valverde')),
}

out = dict(denominator=dict(strict_history_phds_2009_2026=N, phds_2009_2014=len(early), phds_2020_2026=len(late)), groups={}, overlaps={}, cocitation={}, francophone={})
engaged = {}
for grp, lst in GROUPS.items():
    hits, per = Counter(), {}
    for key, pat, auth in lst:
        s = citers(pat, auth)
        per[key] = dict(phds_2009_2026=len(s), universities=len({diss[d]['institution'] for d in s}), at_francophone=sum(diss[d]['institution'] in FR for d in s))
        hits.update(s)
    eng = {d for d, k in hits.items() if k >= 2}
    engaged[grp] = eng
    out['groups'][grp] = dict(works=per, phds_citing_two_or_more=len(eng), share=round(len(eng) / N, 4),
                              share_2009_14=round(len(eng & early) / len(early), 4), share_2020_26=round(len(eng & late) / len(late), 4),
                              at_francophone=sum(diss[d]['institution'] in FR for d in eng))
names = list(GROUPS)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        A, B = engaged[a], engaged[b]
        out['overlaps'][f'{a}|{b}'] = dict(both=len(A & B), lift=round(len(A & B) * N / (len(A) * len(B)), 2))
for k, (a, b) in COCITE.items():
    A, B = citers(*a), citers(*b)
    out['cocitation'][k] = dict(a=len(A), b=len(B), both=len(A & B))
print(json.dumps(out, indent=1))
