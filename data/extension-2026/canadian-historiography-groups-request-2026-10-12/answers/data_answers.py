#!/usr/bin/env python3
"""Answer the drafts' open questions that the citation evidence can settle.

All counts are strict History PhDs completed 2009-2026 (both large programmes present), counted
by dissertation. Methods used throughout:
- **Engagement** with a group: citing works by at least two of its anchor people (groups.json),
  excluding the person under test.
- **Placement test:** for a contested person, the share of PhDs citing them that engage each
  candidate group, against that group's base rate (lift).
- **Overlap test** for splitting an entry: the lift of citing both halves together, compared
  with pairs of entries that are already separate.
- **Coverage-artefact test** for declines: the same trend within a fixed panel of universities
  present in both periods, and against the decline common to all groups.

Writes data-answers.json. Run from the repository root.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
SCHOLARS = ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12'
EARLY, LATE = (2009, 2014), (2020, 2026)
FRANCO = {'montreal', 'uqam', 'laval', 'sherbrooke'}

g = json.loads((OUT / 'graph.json').read_text())
nodes = {n['id']: n for n in g['nodes']}
diss = {k: n for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis') and n['year'] and 2009 <= n['year'] <= 2026}
N = len(diss)
cites, works_of, citing_of = defaultdict(set), defaultdict(set), defaultdict(set)
for e in g['edges']:
    if e['type'] == 'CITES' and e['source'] in diss:
        cites[e['source']].add(e['target'])
        citing_of[e['target']].add(e['source'])
    elif e['type'] == 'AUTHORED':
        works_of[e['source']].add(e['target'])
spec = json.loads((PACKET / 'groups.json').read_text())
G = {x['id']: x for x in spec['groups']}
cands = {r['name']: r for r in csv.DictReader((SCHOLARS / 'candidates.csv').open())}
dec = {r['person_key']: r for r in csv.DictReader((SCHOLARS / 'identity-decisions.csv').open())}
early = {d for d in diss if EARLY[0] <= diss[d]['year'] <= EARLY[1]}
late = {d for d in diss if LATE[0] <= diss[d]['year'] <= LATE[1]}


def pworks(name):
    """Works of a scholar-packet person (identity-cleaned), or of a surname|given key prefix."""
    if name in cands:
        ws = set()
        for k in cands[name]['person_keys'].split('; '):
            bad = {x.strip() for x in (dec.get(k, {}).get('foreign_work_ids') or '').split(';') if x.strip()}
            ws |= works_of[k] - bad
        return ws
    return set().union(*(w for k, w in works_of.items() if k.startswith('P:' + name))) if any(k.startswith('P:' + name) for k in works_of) else set()


def wsearch(title_rx, author_rx=None):
    rt = re.compile(title_rx, re.I)
    ra = re.compile(author_rx, re.I) if author_rx else None
    return {w for w, n in nodes.items() if n['type'] == 'Work' and citing_of.get(w) and rt.search(n.get('title') or '')
            and (not ra or ra.search(w))}


def citers(ws):
    return set().union(*(citing_of[w] for w in ws)) if ws else set()


def engaged(gid, exclude=()):
    anchors = [n for n in G[gid]['primary'] + G[gid]['also'] if n in cands and n not in exclude]
    hits = Counter(d for n in anchors for d in citers(pworks(n)))
    return {d for d, k in hits.items() if k >= 2}


ENG = {gid: engaged(gid) for gid in G}


def placement(name, groups, ws=None):
    c = citers(ws if ws is not None else pworks(name))
    out = {}
    for gid in groups:
        e = engaged(gid, exclude=(name,))
        share = len(c & e) / len(c) if c else 0
        out[gid] = dict(share=round(share, 3), lift=round(share / (len(e) / N), 2) if e else None)
    return dict(citing_phds=len(c), groups=out)


def lift(a, b):
    return round((len(a & b) / N) / ((len(a) / N) * (len(b) / N)), 2) if a and b else None


def trend(s):
    return dict(early=round(len(s & early) / len(early), 4), late=round(len(s & late) / len(late), 4))


def count(ws, label=None):
    c = citers(ws)
    return dict(phds=len(c), franco=len([d for d in c if diss[d]['institution'] in FRANCO]), **trend(c),
                works=sorted(((nodes[w]['title'][:70], nodes[w].get('year'), len(citing_of[w])) for w in ws), key=lambda x: -x[2])[:6])


A = {}
# --- Q02, Q04, Q58-59, Q63: older Quebec and national figures ---
for name, key in [('Trudel', 'trudel|marcel'), ('Ouellet', 'ouellet|fernand'), ('Brunet', 'brunet|michel'), ('Groulx', 'groulx|lionel'),
                  ('Séguin', 'seguin|maurice'), ('Frégault', 'fregault|guy'), ('Ormsby', 'ormsby|margaret'), ('Daniel N. Paul', 'paul|daniel'),
                  ('Lears', 'lears|'), ('Allen, Richard', 'allen|richard'), ('Corrigan', 'corrigan|philip'), ('Sutherland, Neil', 'sutherland|neil')]:
    A[f'figure:{name}'] = count(pworks(key))
# --- Q03, Q25, Q28, Q31, Q34, Q39, Q45, Q56, Q73/80, Q74, Q84, Q91: placement tests ---
tests = {
    'Stanley, George F.G': ['cdn_national_tradition', 'native_newcomer', 'cdn_military', 'cdn_regional'],
    'Stacey, C.P': ['cdn_national_tradition', 'cdn_military', 'cdn_political_national'],
    'Innis, Harold A': ['cdn_national_tradition', 'native_newcomer', 'cdn_regional'],
    'Owram, Doug': ['cdn_intellectual_cultural', 'cdn_childhood_youth', 'cdn_sixties', 'cdn_political_national'],
    'Curtis, Bruce': ['liberal_order_framework', 'moral_regulation'],
    'Backhouse, Constance': ['moral_regulation', 'cdn_immigration_ethnicity', 'cdn_women_gender'],
    'McKay, Ian': ['liberal_order_framework', 'cdn_working_class', 'cdn_intellectual_cultural', 'cdn_regional'],
    'Van Kirk, Sylvia': ['native_newcomer', 'cdn_women_gender', 'settler_colonialism'],
    'Perry, Adele': ['native_newcomer', 'cdn_women_gender', 'settler_colonialism'],
    'Harris, Cole': ['cdn_regional', 'native_newcomer', 'settler_colonialism'],
    'Carter, Sarah': ['cdn_regional', 'native_newcomer', 'settler_colonialism', 'cdn_women_gender'],
    'Granatstein, J.L': ['cdn_political_national', 'cdn_military', 'who_killed_debate'],
    'Bercuson, David': ['cdn_working_class', 'cdn_military', 'cdn_political_national'],
    'Bliss, Michael': ['cdn_political_national', 'who_killed_debate', 'liberal_order_framework'],
    'Morton, Desmond': ['cdn_military', 'cdn_working_class', 'cdn_political_national'],
    'Gauvreau, Michael': ['cdn_religion_reform', 'quebec_historiography', 'cdn_sixties'],
    'Martel, Marcel': ['quebec_historiography', 'cdn_sixties'],
}
A['placement'] = {n: placement(n, gs) for n, gs in tests.items()}
A['placement']['Backhouse: Colour-Coded'] = placement('Backhouse, Constance', ['moral_regulation', 'cdn_immigration_ethnicity', 'cdn_women_gender'],
                                                      wsearch(r'colour.coded'))
A['placement']['Backhouse: Petticoats and Prejudice'] = placement('Backhouse, Constance', ['moral_regulation', 'cdn_immigration_ethnicity', 'cdn_women_gender'],
                                                                  wsearch(r'petticoats and prejudice'))
A['placement']['Bliss: business history'] = placement('Bliss, Michael', ['cdn_political_national', 'who_killed_debate'],
                                                      wsearch(r'northern enterprise|living profit|canadian millionaire|the discovery of insulin|banting'))
A['placement']['Bliss: Privatizing the Mind'] = placement('Bliss, Michael', ['cdn_political_national', 'who_killed_debate'], wsearch(r'privati[sz]ing the mind'))
A['placement']['Palmer: Descent into Discourse'] = placement('Palmer, Bryan D', ['cdn_working_class', 'cdn_women_gender', 'cdn_intellectual_cultural'],
                                                             wsearch(r'descent into discourse'))
A['placement']['Milloy: A National Crime'] = placement('Milloy, John S', ['native_newcomer', 'cdn_childhood_youth', 'settler_colonialism'], wsearch(r'national crime'))
# --- Q07, Q35: split tests, against already-separate pairs ---
intel = citers(wsearch(r'sense of power|writing of canadian history|contours of canadian thought|matter of mind|government generation|promise of eden|science of society'))
cult = citers(wsearch(r'quest of the folk|art of nation.building|death so noble|imaginary indian|national dreams|inglorious arts|royal spectacle'))
women = citers(wsearch(r'canadian women: a history|new day recalled|they.re still women|nature of their bodies|no easy road|rethinking canada'))
gender = citers(wsearch(r'gender of breadwinners|useful category of historical analysis|gender trouble|working families|public men and virtuous|gendered pasts'))
A['split'] = dict(intellectual_vs_cultural=dict(a=len(intel), b=len(cult), both=len(intel & cult), lift=lift(intel, cult)),
                  women_vs_gender=dict(a=len(women), b=len(gender), both=len(women & gender), lift=lift(women, gender)),
                  reference_separate_pairs={f'{a}|{b}': lift(ENG[a], ENG[b]) for a, b in [
                      ('cdn_military', 'cdn_women_gender'), ('quebec_historiography', 'cdn_working_class'),
                      ('liberal_order_framework', 'moral_regulation'), ('cdn_women_gender', 'cdn_childhood_youth'),
                      ('native_newcomer', 'settler_colonialism'), ('cdn_political_national', 'cdn_military')]})
# --- Q09, Q16, Q94: declines, coverage artefact ---
inst_e = Counter(diss[d]['institution'] for d in early)
inst_l = Counter(diss[d]['institution'] for d in late)
panel = {i for i in inst_e if inst_e[i] >= 10 and inst_l[i] >= 10}
pe, pl = {d for d in early if diss[d]['institution'] in panel}, {d for d in late if diss[d]['institution'] in panel}
bib = {p: statistics.median(len(cites[d]) for d in s) for p, s in (('early', early), ('late', late))}
dec_rows = {}
for gid, e in ENG.items():
    a, b = len(e & early) / len(early), len(e & late) / len(late)
    pa, pb = len(e & pe) / len(pe), len(e & pl) / len(pl)
    dec_rows[gid] = dict(all=[round(a, 4), round(b, 4)], panel=[round(pa, 4), round(pb, 4)],
                         ratio=round(b / a, 2) if a else None, panel_ratio=round(pb / pa, 2) if pa else None)
med_ratio = statistics.median(r['ratio'] for r in dec_rows.values() if r['ratio'])
A['declines'] = dict(panel_universities=sorted(panel), panel_sizes=[len(pe), len(pl)], median_bibliography_entries=bib,
                     median_ratio_all_groups=med_ratio, groups=dec_rows)
# --- Q10, Q14, Q22: particular co-citations and trends ---
quest = citers(wsearch(r'quest of the folk'))
lears = citers(wsearch(r'no place of grace'))
A['Q10_lears'] = dict(quest_phds=len(quest), lears_phds=len(lears), both=len(quest & lears), lift=lift(quest, lears))
A['Q14_allen_vs_cook'] = dict(allen=count(wsearch(r'social passion')), cook_regenerators=count(wsearch(r'the regenerators')),
                              christie_gauvreau=count(wsearch(r'full.orbed christianity')), marshall=count(wsearch(r'secularizing the faith')))
lof = citers(wsearch(r'liberal order framework'))
A['Q22_transition'] = {t: dict(phds=len(c), with_lof=len(c & lof), lift=lift(c, lof)) for t, c in
                       [('Bradbury Working Families', citers(wsearch(r'^working families'))), ('Greer Peasant Lord Merchant', citers(wsearch(r'peasant, lord')))]}
# --- Q12, Q15, Q38, Q86-87: readerships of specific literatures ---
lits = {
    'Q12_catholic_action_quiet_revolution': r'catholic origins of quebec|prelude to quebec.s quiet|sortir de la .grande noirceur|une douce anarchie|r[ée]volution tranquille',
    'Q15_irish_catholic': r'piety and nationalism|waning of the green|irish catholic|irish in ontario',
    'Q38_quebec_womens_history': r'histoire des femmes au qu[ée]bec|qu[ée]b[ée]coises du 20e|m[ée]nag[eè]res au temps|femmes et histoire|une histoire des femmes',
    'Q86_87_acadia': r'acadi|from migrant to acadian|great and noble scheme',
    'Q70_valour_horror': r'valour and the horror',
    'Q76_british_world': r'british world',
    'Q72_business_history': r'northern enterprise|living profit|history of canadian business|concise history of business|canadian millionaire|business history',
    'Q46_black_canadian': r'black loyalist|blacks in canada|hanging of ang[ée]lique|black battalion|fear of a black nation|african.canadian|race and recruitment|slavery in canada|esclavage|african nova scotia',
}
A['literatures'] = {}
for q, rx in lits.items():
    ws = wsearch(rx)
    c = citers(ws)
    A['literatures'][q] = dict(count(ws), engagement={gid: dict(share=round(len(c & e) / len(c), 3), lift=lift(c, e)) for gid, e in ENG.items()} if c else {})
# --- Q46, Q52, Q60, Q85, Q42, Q23: the dissertations' own titles ---
def titles(rx):
    r = re.compile(rx, re.I)
    s = {d for d in diss if r.search(diss[d].get('title') or '')}
    return dict(phds=len(s), **trend(s))
A['titles'] = {k: titles(rx) for k, rx in {
    'native_newcomer_term': r'native.newcomer|natives? and newcomers', 'indian': r'\bindians?\b', 'native': r'\bnatives?\b',
    'aboriginal': r'aboriginal|autochtone', 'indigenous': r'indigenous', 'first_nations': r'first nations|premi[eè]res nations',
    'settler': r'settler', 'metis': r'm[ée]tis',
    'black_canadian': r'\bblack\b|african.canadian|afro|\bnoirs?\b|slaver|esclav',
    'french_canada_outside_quebec': r'franco.ontari|acadi|franco.manitob|francophones? (?:hors|minorit|outside)|french.canad|canadiens.fran[cç]ais|canada fran[cç]ais',
    'quebec': r'qu[ée]bec|montr[ée]al',
    'ontario': r'ontario|toronto', 'newfoundland_labrador': r'newfoundland|labrador|terre.neuve', 'north_arctic': r'arctic|yukon|northwest territories|nunavut|inuit|\bnorth(?:ern)?\b',
    'prairies_west': r'prairie|saskatchewan|manitoba|alberta|winnipeg', 'british_columbia': r'british columbia|vancouver|colombie',
    'atlantic_maritimes': r'nova scotia|new brunswick|maritime|atlantic canada|prince edward|halifax',
    'family': r'\bfamil', 'childhood_youth': r'child|youth|adolescen|enfan|jeunesse|boys?\b|girls?\b',
    'moral_regulation': r'moral regulation|r[ée]gulation morale', 'regulat': r'regulat|r[ée]glement',
    'sixties': r'1960s|sixties|ann[ée]es 1960|ann[ée]es soixante', 'capitalism': r'capitalis'}.items()}
# --- Q06, Q41, Q59, Q90: publication years of each group's most-cited works ---
A['period_evidence'] = {}
for gid in ['cdn_national_tradition', 'cdn_childhood_youth', 'quebec_historiography', 'cdn_sixties', 'cdn_women_gender', 'native_newcomer']:
    anchors = [n for n in G[gid]['primary'] + G[gid]['also'] if n in cands]
    ws = Counter()
    for n in anchors:
        for w in pworks(n):
            ws[w] = len(citing_of[w])
    top = [w for w, _ in ws.most_common(20) if nodes[w].get('year')]
    ys = sorted(nodes[w]['year'] for w in top)
    A['period_evidence'][gid] = dict(top20_years=ys, median=statistics.median(ys) if ys else None,
                                     earliest_top5=sorted((nodes[w]['year'], nodes[w]['title'][:50], ws[w]) for w in top[:5]))
# --- Q75, Q77: who else the political-history readers cite ---
pol = ENG['cdn_political_national']
person_c = Counter()
for p, ws in works_of.items():
    c = citers(ws)
    if len(c) >= 10:
        person_c[p] = (len(c & pol), len(c))
rows = []
for p, (inside, total) in person_c.items():
    l = (inside / len(pol)) / (total / N)
    if inside >= 8 and l >= 2.5:
        rows.append((round(l, 1), inside, total, nodes[p].get('name')))
A['Q75_77_political_cocited'] = sorted(rows, reverse=True)[:40]
fr_pol = {d for d in pol if diss[d]['institution'] in FRANCO}
A['Q75_franco_political'] = dict(franco_engaged=len(fr_pol))
# --- Q27, Q32: atlas rosters ---
atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
roster = {n['id']: [p['person_id'] for p in n.get('representative_people') or []] for n in atlas['nodes']}
A['Q27_great_arch'] = count(wsearch(r'great arch'))
A['Q32_labourhistory_roster'] = roster.get('labourhistory')
A['Q26_foucault_edges'] = Counter(e.get('relationship_kind') for e in atlas['edges'] if e['source'] == 'foucault')
(Path(__file__).parent / 'data-answers.json').write_text(json.dumps(A, indent=1, ensure_ascii=False, default=list))
print(json.dumps({k: v for k, v in A.items() if k in ('split', 'declines', 'titles', 'Q10_lears')}, indent=0, ensure_ascii=False, default=list)[:6000])
