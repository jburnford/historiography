#!/usr/bin/env python3
"""Q54: citation-graph counts for candidate pre-2000 Indigenous critiques of
fur-trade / native-newcomer historiography (plus non-Indigenous context works).

Counts strict History PhDs (Dissertation nodes with in_analysis, 2009-2026),
counted by dissertation, split francophone (montreal, uqam, laval, sherbrooke)
vs anglophone. Works are matched by graph work-id surname prefix plus a title
regex, so spelling variants of one title are pooled. Author totals pool the
listed person keys (AUTHORED edges); these are name keys, not reviewed
identities.

Writes counts JSON to the path given as the first argument (results are
copied into q54-indigenous-critique.json). Run from anywhere:
    python3 q54_counts.py /tmp/q54-counts.json
"""
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
GRAPH = ROOT / 'data/field-research/dissertation-citations-2026-10-11/graph.json'
FRANCO = {'montreal', 'uqam', 'laval', 'sherbrooke'}

# work label -> (work-id surname regex, title regex)
WORKS = {
    'adams_prison_of_grass_1975': (r'adams', r'prison of ?grass'),
    'adams_tortured_people_1999': (r'adams', r'tortured people|^ortured people'),
    'adams_challenging_eurocentric_history_2000': (r'adams', r'challenging eurocentric'),
    'sioui_autohistory_1989_1992': (r'sioui', r'autohist|pour une histoire am[eé]rindienne de l'),
    'sioui_huron_wendat_1994_1999': (r'sioui', r'^(?!.*toponymique).*(huron.?wendat|hurons.?wendats|civilisation m[eé]connue)'),
    'larocque_defeathering_1975': (r'laroc?que', r'defeathering'),
    'larocque_native_woman_scholar_1996': (r'laroc?que', r'colonization of a native woman scholar'),
    'larocque_dissertation_1999': (r'laroc?que', r'native writers resisting'),
    'larocque_when_the_other_is_me_2010': (r'laroc?que', r'when the other is me'),
    'wheeler_indigenous_voices_1999': (r'stevenson|wheeler', r'indigenous voices,? indigenous histories'),
    'wheeler_ethnic_assimilates_1998': (r'stevenson|wheeler', r'ethnic.{0,3} assimilates'),
    'wheeler_calling_badger_1999': (r'stevenson|wheeler', r'calling badger'),
    'wheeler_journals_and_voices_1996': (r'stevenson|wheeler', r'journals and voices'),
    'wheeler_reflections_oral_history_2005': (r'stevenson|wheeler', r'social relations of indigenous oral'),
    'wheeler_decolonizing_tribal_histories_2000': (r'stevenson|wheeler', r'decoloni[sz]ing tribal'),
    'dickason_myth_of_the_savage_1984': (r'dickason', r'myth of ?the savage'),
    'dickason_canadas_first_nations_1992': (r'dickason', r"^(?!.*concise)(canada.?s first nations|les premi[eè]res nations)"),
    'trigger_historians_indian_1986': (r'trigger', r"historians.? indian"),
    'trigger_early_native_responses_1991': (r'trigger', r'early native north american responses'),
    'trigger_ethnohistory_problems_1982': (r'trigger', r'^ethnohistory'),
    'trigger_natives_and_newcomers_1985': (r'trigger', r'natives and newcomers'),
    'trigger_problems_of_success_1996': (r'trigger', r'problems of success'),
    'washburn_trigger_euro_american_historiography_1996': (r'washburn|trigger', r'native peoples? in euro.?american historiography'),
    'wheeler_othering_part1_1998': (r'stevenson|wheeler', r'othering of indigenous'),
    'kelm_brownlie_absolution_1994': (r'brownl?[ie]e|kelm|jarvis brownlie', r'seeking absolution: native agency|notes and comments: desperately seeking absolution native'),
    'cole_et_al_absolution_responses_1995': (r'c ?ole|miller|greer|wien|trottier|kelm', r'absolution:? responses'),
}

# author label -> person-key regex (anchored after 'P:')
AUTHORS = {
    'Howard Adams': r'adams\|howard',
    'Georges E. Sioui': r'sioui\|georges',
    'Emma LaRocque': r'laroc?que\|emma',
    'Winona Wheeler (Stevenson)': r'(wheeler\|winona|stevenson\|winona)',
    'Olive P. Dickason': r'dickason\|olive',
    'Bruce G. Trigger': r'trigger\|bruce',
    'Mary-Ellen Kelm': r'kelm\|mary',
    'Robin Jarvis Brownlie': r'brownlie\|(robin|jarvis)',
}


def split(ds, diss):
    fr = sum(1 for d in ds if diss[d]['institution'] in FRANCO)
    return {'phds': len(ds), 'francophone': fr, 'anglophone': len(ds) - fr}


def main():
    g = json.loads(GRAPH.read_text())
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k: n for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis')
            and n.get('year') and 2009 <= n['year'] <= 2026}
    citing, works_of = defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            citing[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'])
    out = {'graph': str(GRAPH.relative_to(ROOT)), 'universe': {'strict_phds_2009_2026': len(diss),
           **split(set(diss), diss)}, 'works': {}, 'authors': {}}
    for label, (arx, trx) in WORKS.items():
        ra, rt = re.compile(r'^W:(' + arx + r')\|', re.I), re.compile(trx, re.I)
        ws = {w for w in citing if w.startswith('W:') and ra.search(w) and rt.search(nodes[w].get('title') or '')}
        ds = set().union(*(citing[w] for w in ws)) if ws else set()
        out['works'][label] = {**split(ds, diss),
                               'matched_work_ids': sorted(ws),
                               'titles': sorted({nodes[w].get('title') for w in ws}),
                               'citing_dissertations': sorted(
                                   f"{diss[d]['institution']} {diss[d]['year']} {d}" for d in ds)}
    for label, prx in AUTHORS.items():
        rp = re.compile(r'^P:' + prx, re.I)
        keys = sorted(k for k in works_of if rp.search(k))
        ws = set().union(*(works_of[k] for k in keys)) if keys else set()
        ds = set().union(*(citing.get(w, set()) for w in ws)) if ws else set()
        out['authors'][label] = {**split(ds, diss), 'person_keys': keys}
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for k, v in out['works'].items():
        print(f"{k:45s} {v['phds']:3d} fr={v['francophone']} en={v['anglophone']}")
    for k, v in out['authors'].items():
        print(f"{k:45s} {v['phds']:3d} fr={v['francophone']} en={v['anglophone']} keys={v['person_keys']}")


if __name__ == '__main__':
    main()
