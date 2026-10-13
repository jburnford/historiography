#!/usr/bin/env python3
"""Citation evidence for four drafted Canadian group entries.

Writes evidence.json into drafts/{cdn_national_tradition, cdn_political_national,
who_killed_debate, cdn_regional}/. Run from the repository root:

    python3 data/extension-2026/canadian-historiography-groups-request-2026-10-12/drafts/cdn_national_tradition/four_groups_evidence.py

Counts are dissertations, not citations. Two denominators are reported:
- `strict_2009_2026`: Dissertation nodes with in_analysis true and year 2009-2026 (the packet's
  standard denominator);
- `strict_all_years`: every in_analysis Dissertation, any year (the brief's debate counts use it).

A work is counted through every graph Work record whose title matches its pattern and whose id
matches its author pattern (variant records of the same work are merged and listed). Person
counts reuse the scholar packet's identity-cleaned person works (candidates.csv plus
identity-decisions.csv), exactly as groups_evidence.py does. Bibliographies record consultation,
not influence.
"""
from collections import Counter, defaultdict
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PACKET = ROOT / 'data/extension-2026/canadian-historiography-groups-request-2026-10-12'
GRAPH = ROOT / 'data/field-research/dissertation-citations-2026-10-11/graph.json'
SCHOLARS = ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12'
WINDOWS = {'2009_14': (2009, 2014), '2015_19': (2015, 2019), '2020_26': (2020, 2026)}

# key: (short label, title regex, work-id author regex or None, title exclusion regex or None)
WORKS = {
    # national tradition
    'mackintosh_1923': ('Mackintosh, "Economic Factors in Canadian History" (1923)', r'economic factors in canadian history', r'mackintosh', None),
    'innis_1930': ('Innis, The Fur Trade in Canada (1930)', r'^the fur trade in canada', r'innis', None),
    'innis_1940': ('Innis, The Cod Fisheries (1940)', r'^the cod fisheries', r'innis', None),
    'creighton_1937': ('Creighton, The Commercial Empire of the St. Lawrence (1937) / The Empire of the St. Lawrence (1956)', r'empire of the st\.? lawrence', r'creighton', r'decline and fall'),
    'creighton_macdonald': ('Creighton, John A. Macdonald (1952, 1955)', r'^(sir )?john a\.? macdonald( ?: ?the (old chieftain|young politician))?$', r'creighton', None),
    'lower_1938': ('Lower, The North American Assault on the Canadian Forest (1938)', r'north american assault on the canadian forest', r'lower', None),
    'lower_1946': ('Lower, Colony to Nation (1946)', r'colony to nation', r'lower', None),
    'underhill_1960': ('Underhill, In Search of Canadian Liberalism (1960)', r'in search of ?canadian liberalism', r'underhill', None),
    'careless_1954': ('Careless, "Frontierism, Metropolitanism, and Canadian History" (1954)', r'frontierism,? metropolitanism', r'careless', None),
    'morton_1946': ('Morton, "Clio in Canada" (1946)', r'clio in canada', r'morton', None),
    'morton_1963': ('Morton, The Kingdom of Canada (1963)', r'kingdom of canada', r'morton', None),
    'morton_1964': ('Morton, The Critical Years (1964)', r'^the critical years', r'morton', None),
    'neatby_1966': ('Neatby, Quebec: The Revolutionary Age (1966)', r'^quebec(: the revolutionary age)?', r'neatby', r'little'),
    'trudel_1973': ('Trudel, The Beginnings of New France (1973)', r'beginnings of new france', r'trudel', None),
    'brown_cook_1974': ('Brown and Cook, Canada 1896-1921 (1974)', r'canada,? 1896', r'brown|cook', None),
    'thompson_seager_1985': ('Thompson and Seager, Canada 1922-1939 (1985)', r'canada,? 1922', r'thompson|seager', None),
    'ouellet_1966': ('Ouellet, Histoire économique et sociale du Québec (1966)', r'^histoire [ée]conomique et sociale du qu[ée]bec', r'ouellet', None),
    'ouellet_1980': ('Ouellet, Lower Canada 1791-1840 (1980)', r'^lower canada,? 1791', r'ouellet', None),
    'stanley_1936': ('Stanley, The Birth of Western Canada (1936)', r'birth of western canada', r'stanley', None),
    'stacey_1970': ('Stacey, Arms, Men and Governments (1970)', r'arms,? men,? and governments', r'stacey', None),
    'stacey_1977': ('Stacey, Canada and the Age of Conflict (1977, 1981)', r'canada and the age of conflict', r'stacey', None),
    'berger_1976': ('Berger, The Writing of Canadian History (1976; 2nd ed. 1986)', r'writing of canadian history', r'berger', None),
    'watkins_1963': ('Watkins, "A Staple Theory of Economic Growth" (1963)', r'staple theory of ?economic growth', r'watkins', None),
    # limited identities and the debate
    'cook_1967': ('Cook, "Canadian Centennial Cerebrations" (1967)', r'centennial (cere|cele)brations', r'cook', None),
    'careless_1969': ('Careless, "\'Limited Identities\' in Canada" (1969)', r'limited identities.{0,4} in canada', r'careless', None),
    'buckner_1988': ('Buckner, "\'Limited Identities\' and Canadian Historical Scholarship" (1988)', r'limited identities.{0,4} and canadian historical scholarship', r'buck', None),
    'buckner_2000': ('Buckner, "\'Limited Identities\' Revisited" (2000)', r'limited identities', r'buck', r'scholarship'),
    'bliss_1991': ('Bliss, "Privatizing the Mind" (1991-92)', r'privati[sz]ing the mind', r'bliss', None),
    'g_kealey_1992': ('G. Kealey, "Class in English-Canadian Historical Writing" (1992)', r'neither privati', None, None),
    'l_kealey_et_al_1992': ('L. Kealey, Pierson, Sangster and Strong-Boag, "Whose \'National\' History Are We Lamenting?" (1992)', r'teaching canadian history in the 1990s|whose .national. history', None, None),
    'strong_boag_1994': ('Strong-Boag, "Contested Space" (1994)', r'contested space', r'strong', None),
    'granatstein_1998': ('Granatstein, Who Killed Canadian History? (1998)', r'who killed canadian history', r'granat', r'trenches'),
    'mckillop_1999': ('McKillop, "Who Killed Canadian History? A View from the Trenches" (1999)', r'who killed canadian history', r'mckil', None),
    'palmer_1999': ('Palmer, "Of Silences and Trenches" (1999)', r'silences and trenches', None, None),
    'letourneau_2000_chr': ('Létourneau, "L\'avenir du Canada: par rapport à quelle histoire?" (2000)', r'avenir du canada', r'leto', None),
    'letourneau_2000_book': ('Létourneau, Passer à l\'avenir (2000)', r'passer [àa] l', r'leto', None),
    'cook_2000': ('Cook, "Identities Are Not Like Hats" (2000)', r'identities are not like hats', None, None),
    'osborne_2000': ('Osborne, "Our History Syllabus Has Us Gasping" (2000)', r'syllabus has us gasping', None, None),
    'mckay_2000_lof': ('McKay, "The Liberal Order Framework" (2000)', r'^the liberal order framework', r'mck', None),
    'dummitt_dawson_2009': ('Dummitt and Dawson, eds., Contesting Clio\'s Craft (2009)', r'contesting clio', None, None),
    'reid_1987': ('Reid, "Towards the Elusive Synthesis" (1987)', r'elusive synthesis', r'reid', None),
    # political, international and national
    'granatstein_1975': ('Granatstein, Canada\'s War (1975)', r'^canada.s war', r'granat', None),
    'granatstein_hitsman_1977': ('Granatstein and Hitsman, Broken Promises (1977)', r'^broken promises', r'granat', None),
    'granatstein_1982': ('Granatstein, The Ottawa Men (1982)', r'ottawa men', r'granat', None),
    'whitaker_1977': ('Whitaker, The Government Party (1977)', r'^the government party', r'whitaker', None),
    'bde_1981': ('Bothwell, Drummond and English, Canada since 1945 (1981)', r'^canada since 1945', r'bothwell|drummond|english', None),
    'bde_1987': ('Bothwell, Drummond and English, Canada 1900-1945 (1987)', r'^canada,? 1900', r'bothwell|drummond|english', None),
    'english_1977': ('English, The Decline of Politics (1977)', r'decline of politics', r'english', None),
    'english_1989': ('English, Shadow of Heaven (1989)', r'shadow of heaven', r'english', None),
    'brown_1975': ('Brown, Robert Laird Borden (1975, 1980)', r'robert laird borden', r'brown', None),
    'belanger_1986': ('Bélanger, Wilfrid Laurier (1986)', r'quand la politique devient passion', r'belanger', None),
    'bercuson_1993': ('Bercuson, True Patriot (1993)', r'^true patriot', r'bercuson', None),
    'bliss_1974': ('Bliss, A Living Profit (1974)', r'^a living profit', r'bliss', None),
    'bliss_1978': ('Bliss, A Canadian Millionaire (1978)', r'canadian millionaire', r'bliss', None),
    'bliss_1987': ('Bliss, Northern Enterprise (1987)', r'^northern enterprise', r'bliss', None),
    'bliss_1994': ('Bliss, Right Honourable Men (1994)', r'right honourable men', r'bliss', None),
    'drummond_1974': ('Drummond, Imperial Economic Policy (1974)', r'imperial economic policy', r'drummond', None),
    'drummond_1987': ('Drummond, Progress without Planning (1987)', r'progress without planning', r'drummond', None),
    'owram_1986': ('Owram, The Government Generation (1986)', r'government generation', r'owram', None),
    'hillmer_granatstein_1994': ('Hillmer and Granatstein, Empire to Umpire (1994)', r'empire to umpire', r'hillmer|granat', None),
    'whitaker_marcuse_1994': ('Whitaker and Marcuse, Cold War Canada (1994)', r'^cold war canada', r'whitaker|marcuse', None),
    'buckner_1993': ('Buckner, "Whatever Happened to the British Empire?" (1993)', r'whatever happened to the british empire', r'buck', None),
    'buckner_francis_2006': ('Buckner and Francis, eds., Canada and the British World (2006)', r'canada and the british world', r'buck|francis', None),
    'bothwell_2007': ('Bothwell, Alliance and Illusion (2007)', r'alliance and illusion', r'bothwell', None),
    'chapnick_2000': ('Chapnick, "The Canadian Middle Power Myth" (2000)', r'middle power myth', r'chapnick', None),
    'chapnick_2005': ('Chapnick, The Middle Power Project (2005)', r'middle power project', r'chapnick', None),
    # regional
    'morton_1957': ('Morton, Manitoba: A History (1957)', r'^manitoba(: a history)?$', r'morton', None),
    'ormsby_1958': ('Ormsby, British Columbia: A History (1958)', r'^british columbia(: a history)?$', r'ormsby', None),
    'acheson_1972': ('Acheson, "The National Policy and the Industrialization of the Maritimes" (1972)', r'national policy and the industriali[sz]ation of the maritimes', r'acheso', None),
    'forbes_1979': ('Forbes, The Maritime Rights Movement (1979)', r'maritime rights', r'forbes', r'origins'),
    'forbes_1989': ('Forbes, Challenging the Regional Stereotype (1989)', r'regional ?stereotype', r'forbes', None),
    'owram_1980': ('Owram, Promise of Eden (1980)', r'promise of eden', r'owram', None),
    'friesen_1984': ('Friesen, The Canadian Prairies: A History (1984)', r'^the canadian prairies', r'friesen', None),
    'francis_1989': ('Francis, Images of the West (1989)', r'^images of the west', r'francis', None),
    'careless_1989': ('Careless, Frontier and Metropolis (1989)', r'^frontier and metropolis', r'careless', None),
    'carter_1990': ('Carter, Lost Harvests (1990)', r'^lost harvests', r'carter', None),
    'barman_1991': ('Barman, The West Beyond the West (1991)', r'west beyond the west', r'barman', None),
    'harris_1997': ('Harris, The Resettlement of British Columbia (1997)', r'resettlement of british columbia', r'harris', None),
    'stonechild_waiser_1997': ('Stonechild and Waiser, Loyal till Death (1997)', r'loyal till death', r'stonechild|waiser', None),
    'painchaud_1987': ('Painchaud, Un rêve français dans le peuplement de la Prairie (1987)', r'r[êe]ve fran[çc]ais dans le peuplement', r'painchaud', None),
    'gaspesie_1981': ('Bélanger, Desjardins and Frenette, Histoire de la Gaspésie (1981; new edition 1999)', r'^histoire de la gasp[ée]sie', None, None),
    'mckay_2000_region': ('McKay, "A Note on \'Region\'" (2000)', r'note on .?region', r'mc ?kay', None),
    'friesen_2000_howe': ('Friesen, "Atlantic Canada\'s Historical Writing Today: No Howe?" (2000)', r'no howe', r'friesen', None),
    'friesen_2000_citizens': ('Friesen, Citizens and Nation (2000)', r'^citizens and nation', r'friesen', None),
    'conrad_hiller_2001': ('Conrad and Hiller, Atlantic Canada (2001; 2010)', r'^atlantic canada(: a (history|region in the making))?$', r'conrad|hiller', None),
    'reid_et_al_2004': ('Reid et al., The "Conquest" of Acadia, 1710 (2004)', r'^the .?conquest.? of acadia', r'reid', None),
    'waiser_2005': ('Waiser, Saskatchewan: A New History (2005)', r'^saskatchewan(: a new history)?$', r'waiser', None),
    'sandwell_2005': ('Sandwell, Contesting Rural Space (2005)', r'contesting rural space', r'sandwell', None),
    'harvey_2006': ('Harvey, "Identity and Scales of Regionalism in Canada and Quebec" (2006)', r'scales of regionalism', None, None),
}

GROUP_WORKS = {
    'cdn_national_tradition': ['mackintosh_1923', 'innis_1930', 'innis_1940', 'watkins_1963', 'creighton_1937', 'creighton_macdonald',
                               'lower_1938', 'lower_1946', 'underhill_1960', 'careless_1954', 'morton_1946', 'morton_1963', 'morton_1964',
                               'neatby_1966', 'trudel_1973', 'brown_cook_1974', 'thompson_seager_1985', 'ouellet_1966', 'ouellet_1980',
                               'stanley_1936', 'stacey_1970', 'stacey_1977', 'berger_1976', 'cook_1967', 'careless_1969'],
    'cdn_political_national': ['granatstein_1975', 'granatstein_hitsman_1977', 'granatstein_1982', 'whitaker_1977', 'english_1977',
                               'bde_1981', 'bde_1987', 'english_1989', 'brown_1975', 'belanger_1986', 'bercuson_1993', 'bliss_1974',
                               'bliss_1978', 'bliss_1987', 'bliss_1994', 'drummond_1974', 'drummond_1987', 'owram_1986', 'stacey_1977',
                               'hillmer_granatstein_1994', 'whitaker_marcuse_1994', 'buckner_1993', 'buckner_francis_2006',
                               'bothwell_2007', 'chapnick_2000', 'chapnick_2005', 'thompson_seager_1985'],
    'who_killed_debate': ['cook_1967', 'careless_1969', 'reid_1987', 'buckner_1988', 'bliss_1991', 'g_kealey_1992', 'l_kealey_et_al_1992',
                          'strong_boag_1994', 'granatstein_1998', 'mckillop_1999', 'palmer_1999', 'letourneau_2000_chr',
                          'letourneau_2000_book', 'cook_2000', 'buckner_2000', 'osborne_2000', 'mckay_2000_lof', 'dummitt_dawson_2009'],
    'cdn_regional': ['morton_1946', 'morton_1957', 'ormsby_1958', 'cook_1967', 'careless_1969', 'acheson_1972', 'forbes_1979', 'owram_1980',
                     'friesen_1984', 'painchaud_1987', 'gaspesie_1981', 'buckner_1988', 'careless_1989', 'forbes_1989', 'francis_1989',
                     'carter_1990', 'barman_1991', 'harris_1997', 'stonechild_waiser_1997', 'mckay_2000_region', 'buckner_2000',
                     'friesen_2000_howe', 'friesen_2000_citizens', 'conrad_hiller_2001', 'reid_et_al_2004', 'waiser_2005',
                     'sandwell_2005', 'harvey_2006'],
}

# Debate texts (the debate's own interventions) and its roots, counted as sets.
DEBATE_CORE = ['bliss_1991', 'g_kealey_1992', 'l_kealey_et_al_1992', 'strong_boag_1994', 'granatstein_1998', 'mckillop_1999',
               'palmer_1999', 'letourneau_2000_chr', 'cook_2000', 'buckner_2000', 'osborne_2000', 'dummitt_dawson_2009']
DEBATE_ROOTS = ['cook_1967', 'careless_1969', 'buckner_1988']

# Roster people with a candidates.csv record (identity-cleaned person counts).
ROSTER_CANDIDATES = {
    'cdn_national_tradition': ['Innis, Harold A', 'Creighton, Donald', 'Careless, J.M.S', 'Morton, W.L', 'Stacey, C.P', 'Stanley, George F.G',
                               'Brown, Robert Craig', 'Cook, Ramsay', 'Berger, Carl'],
    'cdn_political_national': ['Granatstein, J.L', 'Bothwell, Robert', 'English, John', 'Hillmer, Norman', 'Whitaker, Reg',
                               'Thompson, John Herd', 'Buckner, Phillip', 'Francis, R. Douglas', 'Drummond, Ian M', 'Bercuson, David',
                               'Bliss, Michael', 'Owram, Doug', 'Brown, Robert Craig', 'Stacey, C.P'],
    'who_killed_debate': ['Bliss, Michael', 'Granatstein, J.L', 'Kealey, Gregory S', 'Strong-Boag, Veronica', 'Pierson, Ruth Roach',
                          'Sangster, Joan', 'Palmer, Bryan D', 'Cook, Ramsay', 'Careless, J.M.S', 'Buckner, Phillip', 'McKay, Ian',
                          'Owram, Doug'],
    'cdn_regional': ['Morton, W.L', 'Careless, J.M.S', 'Cook, Ramsay', 'Buckner, Phillip', 'Friesen, Gerald', 'Owram, Doug', 'Waiser, Bill',
                     'Barman, Jean', 'Harris, Cole', 'Carter, Sarah', 'Conrad, Margaret', 'Reid, John G', 'Sandwell, Ruth', 'McKay, Ian'],
}


def wilson(k, n, z=1.96):
    if n == 0:
        return [0, 0]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def main():
    g = json.loads(GRAPH.read_text())
    nodes = {n['id']: n for n in g['nodes'] if n['type'] in ('Dissertation', 'Work')}
    strict = {k: n for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis')}
    recent = {k for k, n in strict.items() if n.get('year') and 2009 <= n['year'] <= 2026}
    win = {w: {d for d in recent if a <= strict[d]['year'] <= b} for w, (a, b) in WINDOWS.items()}
    cites, works_of = defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in strict:
            cites[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'])
    del g
    work_nodes = {k: n for k, n in nodes.items() if n['type'] == 'Work'}

    def match(spec):
        _, pat, akey, excl = spec
        rx, ax, ex = re.compile(pat, re.I), re.compile(akey, re.I) if akey else None, re.compile(excl, re.I) if excl else None
        out = []
        for wid, n in work_nodes.items():
            t = n.get('title') or ''
            if rx.search(t) and (ax is None or ax.search(wid)) and not (ex and ex.search(t)) and cites.get(wid):
                out.append(wid)
        return out

    def series(ds):
        r = {'strict_all_years': len(ds), 'strict_2009_2026': len(ds & recent)}
        for w, s in win.items():
            r[f'phds_{w}'] = len(ds & s)
            r[f'share_{w}'] = round(len(ds & s) / len(s), 4)
        return r

    work_sets, work_rows = {}, {}
    for key, spec in WORKS.items():
        ids = match(spec)
        ds = {d for w in ids for d in cites[w]}
        work_sets[key] = ds
        per = sorted(((len(cites[w]), len(cites[w] & recent), w) for w in ids), reverse=True)
        work_rows[key] = dict(label=spec[0], **series(ds),
                              graph_records=[dict(work_id=w, title=work_nodes[w].get('title'), year=work_nodes[w].get('year'),
                                                  strict_all_years=a, strict_2009_2026=b) for a, b, w in per])

    # identity-cleaned person counts (as groups_evidence.py)
    cands = {r['name']: r for r in csv.DictReader((SCHOLARS / 'candidates.csv').open())}
    decisions = {r['person_key']: r for r in csv.DictReader((SCHOLARS / 'identity-decisions.csv').open())}

    def person_works(name):
        keys = cands[name]['person_keys'].split('; ')
        ws = set()
        for k in keys:
            foreign = {x.strip() for x in (decisions.get(k, {}).get('foreign_work_ids') or '').split(';') if x.strip()}
            ws |= works_of[k] - foreign
        for r in decisions.values():
            if r.get('move_to') and r['move_to'] in keys:
                ws |= {x.strip() for x in r['move_work_ids'].split(';') if x.strip()}
        return ws

    # group engagement sets from groups.json (cites works by >= 2 anchor people), 2009-2026
    spec = json.loads((PACKET / 'groups.json').read_text())
    engaged = {}
    for gr in spec['groups']:
        anchors = [n for n in gr['primary'] + gr['also'] if n in cands]
        hits = Counter(d for n in anchors for d in {d for w in person_works(n) for d in cites.get(w, ())} & recent)
        engaged[gr['id']] = {d for d, k in hits.items() if k >= 2}

    def overlaps(mine_set, label):
        rows = []
        base = len(mine_set)
        for gid, s in engaged.items():
            if not base or s is mine_set:
                continue
            both = len(mine_set & s)
            p_other = len(s) / len(recent)
            rows.append(dict(other=gid, both=both, share_of_mine=round(both / base, 4), share_of_all_phds=round(p_other, 4),
                             lift=round((both / base) / p_other, 2) if p_other else None))
        return dict(basis=label, n=base, rows=sorted(rows, key=lambda r: -r['lift'] if r['lift'] else 0))

    total = dict(strict_all_years=len(strict), strict_2009_2026=len(recent), **{f'phds_{w}': len(s) for w, s in win.items()})
    common = dict(prepared='2026-10-12', script=str(Path(__file__).relative_to(ROOT)), graph=str(GRAPH.relative_to(ROOT)),
                  denominators=total,
                  method='Dissertations, not citations. Variant Work records of one work are merged (listed under graph_records). '
                         'Person counts reuse the scholar packet\'s identity-cleaned works. Engagement sets follow groups_evidence.py '
                         '(a 2009-2026 PhD citing works by at least two of a group\'s anchors in groups.json). Lift = share of this '
                         'set that is also engaged with the other group, divided by that group\'s share of all 2009-2026 PhDs. '
                         'Bibliographies record consultation, not influence or agreement.')
    for gid in GROUP_WORKS:
        keys = GROUP_WORKS[gid]
        people = {}
        for name in ROSTER_CANDIDATES[gid]:
            ds = {d for w in person_works(name) for d in cites.get(w, ())}
            people[name] = dict(qid=cands[name]['qid'], **series(ds))
        out = dict(common, group=gid, works={k: work_rows[k] for k in keys}, roster_people_candidates_csv=people,
                   group_engagement=dict(engaged_2009_2026=len(engaged[gid]), share=round(len(engaged[gid]) / len(recent), 4),
                                         share_ci95=wilson(len(engaged[gid]), len(recent)),
                                         by_window={w: round(len(engaged[gid] & s) / len(s), 4) for w, s in win.items()}),
                  overlap_with_other_groups=overlaps(engaged[gid], f'{gid} engagement set (groups.json anchors), 2009-2026'))
        if gid == 'who_killed_debate':
            core = set().union(*(work_sets[k] for k in DEBATE_CORE))
            roots = set().union(*(work_sets[k] for k in DEBATE_ROOTS))
            out['debate_text_uptake'] = dict(
                note='Measured through the debate texts themselves, not the people. Core = the interventions 1991-2009; roots = '
                     'Cook 1967, Careless 1969, Buckner 1988.',
                core_texts=DEBATE_CORE, root_texts=DEBATE_ROOTS,
                core_any=series(core), roots_any=series(roots), core_or_roots=series(core | roots),
                core_and_roots=series(core & roots),
                universities_core_2009_2026=sorted(Counter(strict[d]['institution'] for d in core & recent).items(), key=lambda x: -x[1]),
                core_citing_phds_2009_2026=sorted([dict(id=d, year=strict[d]['year'], institution=strict[d]['institution'],
                                                        title=strict[d].get('title')) for d in core & recent], key=lambda x: x['year']))
            out['overlap_of_debate_texts_with_groups'] = overlaps(core & recent, 'PhDs 2009-2026 citing any core debate text')
        (PACKET / 'drafts' / gid / 'evidence.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(gid, 'written')


if __name__ == '__main__':
    main()
