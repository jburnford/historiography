#!/usr/bin/env python3
"""Is there a new big debate? Positioning, breadth and candidate debates in History PhD citing.

The user's hypothesis (2026-10-23): the historiographical narrative is still the 1980s one, Thompson
challenged by Joan Scott with Foucault and Derrida behind her; PhD students position themselves in that
debate decades later, and no later debate is cited by everyone. This script tests that with the release
tables, writing to ``summary/cohorts/``:

- ``debate-dyads.csv``: share of theses citing both sides of a debate, by cohort (the 1980s debate and
  candidate later ones), plus the debate's own texts;
- ``breadth.csv``: how widely each figure or work is cited across the TF-IDF families (families where it
  reaches 3% of theses; max and mean family share), which is what "everyone cites" has to mean;
- ``breadth-rising.csv``: every first author cited by 40+ theses in 2010-25, ranked by breadth, with the year
  of their most-cited work, so post-1995 entrants can be compared with the canon;
- ``theorists-by-cohort.csv``: shares by cohort for the post-1990 theorist layer.

Run: python3 scripts/debate_positioning_analysis.py --release data/.../release/2026-10-23
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from cohort_change_analysis import COHORTS, cohort, region

PEOPLE = {  # display name -> release people.csv name
    'Thompson': 'Thompson, Edward P', 'J. Scott': 'Scott, Joan W', 'Foucault': 'Foucault, Michel',
    'Derrida': 'Derrida, Jacques', 'Anderson': 'Anderson, Benedict', 'Said': 'Said, Edward',
    'Bourdieu': 'Bourdieu, Pierre', 'Hobsbawm': 'Hobsbawm, Eric', 'Geertz': 'Geertz, Clifford',
    'H. White': 'White, Hayden', 'Butler': 'Butler, Judith', 'J. C. Scott': 'Scott, James C',
    'Latour': 'Latour, Bruno', 'Haraway': 'Haraway, Donna', 'Stoler': 'Stoler, Ann Laura',
    'Cooper': 'Cooper, Frederick', 'Trouillot': 'Trouillot, Michel-Rolph', 'Wolfe': 'Wolfe, Patrick',
    'Veracini': 'Veracini, Lorenzo', 'Chakrabarty': 'Chakrabarty, Dipesh', 'Benton': 'Benton, Lauren',
    'Beckert': 'Beckert, Sven', 'W. Johnson': 'Johnson, Walter', 'Koselleck': 'Koselleck, Reinhart',
    'Hartog': 'HARTOG, François', 'Agamben': 'AGAMBEN, Giorgio', 'Mbembe': 'Mbembe, Achille',
    'Deleuze': 'Deleuze, G', 'Lefebvre': 'Lefebvre, Henri', 'Appadurai': 'Appadurai, Arjun',
    'Bhabha': 'Bhabha, Homi K', 'Spivak': 'Spivak, Gayatri Chakravorty', 'Gilroy': 'Gilroy, Paul',
    'Massey': 'Massey, Doreen', 'Harvey': 'Harvey, David', 'Ahmed': 'Ahmed, Sara', 'Asad': 'Asad, Talal',
    'Mignolo': 'Mignolo, Walter D', 'Pomeranz': 'Pomeranz, Kenneth', 'Brenner': 'Brenner, Robert',
    'Moyn': 'Moyn, Samuel', 'L. Hunt': 'Hunt, Lynn', 'Cronon': 'Cronon, William', 'Worster': 'Worster, Donald',
    'R. White': 'White, Richard', 'Hartman': 'Hartman, Saidiya', 'Simpson': 'Simpson, Audra',
    'Coulthard': 'Coulthard, Glen Sean', 'Tuck': 'Tuck, Eve', 'Shapin': 'Shapin, Steven',
    'Daston': 'Daston, Lorraine', 'Guldi': 'Guldi, Jo', 'Armitage': 'Armitage, David',
    'Rancière': 'Rancière, Jacques', 'Žižek': 'Žižek, Slavoj', 'Bennett': 'Bennett, Jane',
    'Tsing': 'Tsing, Anna Lowenhaupt', 'Wynter': 'Wynter, Sylvia', 'Quijano': 'Quijano, Aníbal',
    'Berlant': 'Berlant, Lauren', 'Sedgwick': 'Sedgwick, Eve Kosofsky', 'Williams': 'Williams, Raymond',
    'Gramsci': 'Gramsci, Antonio', 'Habermas': 'Habermas, Jürgen', 'Arendt': 'Arendt, Hannah',
    'Benjamin': 'Benjamin, Walter', 'Certeau': 'CERTEAU, Michel de', 'Ricoeur': 'RICOEUR, Paul',
    'Nora': 'NORA, Pierre', 'Ginzburg': 'Ginzburg, Carlo', 'Davis': 'Davis, Natalie Zemon',
    'Joyce': 'Joyce, Patrick', 'Stedman Jones': 'Stedman Jones, Gareth', 'Palmer': 'Palmer, Bryan D',
    'Sewell': 'Sewell, William H', 'Eley': 'Eley, Geoff', 'Canning': 'Canning, Kathleen',
}
WORKS = {  # display -> work_id
    'Scott, Gender (1986)': 'W:scott|gender|a',
    'Scott, Gender and the Politics of History (1988)': 'W:scott|gender and the politics of history',
    'Thompson, Making (1963)': 'W:thompson|making of the english working class',
    'Foucault, Discipline and Punish': 'W:foucault|discipline and punish',
    'Stedman Jones, Languages of Class (1983)': 'W:stedman jones|languages of class',
    'Palmer, Descent into Discourse (1990)': 'W:palmer|descent into discourse',
    'Joyce, Visions of the People (1991)': 'W:joyce|visions of the people',
    'Joyce, Democratic Subjects (1994)': 'W:joyce|democratic subjects',
    'Toews, Intellectual history after the linguistic turn (1987)': 'W:toews|intellectual history after the linguistic turn|a',
    'Canning, Feminist history after the linguistic turn (1994)': 'W:canning|feminist history after the linguistic turn|a',
    'Spiegel, History, historicism (1990)': 'W:spiegel|history historicism and the social logic of the text|a',
    'Sewell, Work and Revolution (1980)': 'W:sewell|work and revolution in france',
    'Eley, A Crooked Line (2005)': 'W:eley|crooked line',
    'White, Metahistory (1973)': 'W:white|metahistory',
    'Derrida, Of Grammatology': 'W:derrida|of grammatology',
    'J. C. Scott, Seeing Like a State (1998)': 'W:scott|seeing like a state',
    'J. C. Scott, Weapons of the Weak (1985)': 'W:scott|weapons of the weak',
    'J. C. Scott, Domination and the Arts (1990)': 'W:scott|domination and the arts of resistance',
    'Latour, We Have Never Been Modern (1993)': 'W:latour|we have never been modern',
    'Latour, Reassembling the Social (2005)': 'W:latour|reassembling the social',
    'Haraway, Simians, Cyborgs and Women (1991)': 'W:haraway|simians cyborgs and women',
    'Haraway, Situated Knowledges (1988)': 'W:haraway|situated knowledges|a',
    'Pomeranz, Great Divergence (2000)': 'W:pomeranz|great divergence',
    'Wolfe 2006': 'W:wolfe|settler colonialism and the elimination of the native|a',
    'Tuck and Yang 2012': 'W:tuck|decolonization is not a metaphor|a',
    'Baptist 2014': 'W:baptist|half has never been told',
    'Hunt, Inventing Human Rights (2007)': 'W:hunt|inventing human rights',
    'Moyn, Last Utopia (2010)': 'W:moyn|last utopia',
    'Guldi and Armitage, History Manifesto (2014)': 'W:guldi|history manifesto',
    'Cronon, Trouble with Wilderness (1996)': 'W:cronon|trouble with wilderness|a',
    'Chakrabarty, Provincializing Europe (2000)': 'W:chakrabarty|provincializing europe',
    'Cooper, Colonialism in Question (2005)': 'W:cooper|colonialism in question',
    'Stoler, Along the Archival Grain (2009)': 'W:stoler|along the archival grain',
    'Trouillot, Silencing the Past (1995)': 'W:trouillot|silencing the past',
    'Agamben, Homo Sacer (1998)': 'W:agamben|homo sacer',
    'Bhabha, Location of Culture (1994)': 'W:bhabha|location of culture',
    'Lefebvre, Production of Space (1991)': 'W:lefebvre|production of space',
    'Gilroy, Black Atlantic (1993)': 'W:gilroy|black atlantic',
    'Butler, Gender Trouble (1990)': 'W:butler|gender trouble',
}
DEBATE_TEXTS = ['Stedman Jones, Languages of Class (1983)', 'Palmer, Descent into Discourse (1990)',
                'Joyce, Visions of the People (1991)', 'Joyce, Democratic Subjects (1994)',
                'Toews, Intellectual history after the linguistic turn (1987)',
                'Canning, Feminist history after the linguistic turn (1994)', 'Spiegel, History, historicism (1990)',
                'Eley, A Crooked Line (2005)']
DYADS = [  # (label, side A spec, side B spec); spec = ('p', display) person or ('w', display) work or ('set', [specs])
    ('1980s: Thompson & J. Scott (people)', ('p', 'Thompson'), ('p', 'J. Scott')),
    ('1980s: Thompson & Foucault', ('p', 'Thompson'), ('p', 'Foucault')),
    ('1980s: J. Scott & Foucault', ('p', 'J. Scott'), ('p', 'Foucault')),
    ('1980s: J. Scott & Derrida', ('p', 'J. Scott'), ('p', 'Derrida')),
    ('1980s: Thompson Making & Scott Gender (works)', ('w', 'Thompson, Making (1963)'),
     ('set', [('w', 'Scott, Gender (1986)'), ('w', 'Scott, Gender and the Politics of History (1988)')])),
    ('1980s: Thompson, J. Scott and Foucault (all three)', ('set', [('p', 'Thompson')]),
     ('setand', [('p', 'J. Scott'), ('p', 'Foucault')])),
    ('1980s: any debate text (Stedman Jones, Palmer, Joyce, Toews, Canning, Spiegel, Eley)',
     ('set', [('w', t) for t in DEBATE_TEXTS]), None),
    ('1980s: any debate text & (Thompson or J. Scott)', ('set', [('w', t) for t in DEBATE_TEXTS]),
     ('set', [('p', 'Thompson'), ('p', 'J. Scott')])),
    ('Great Divergence: Pomeranz & Brenner', ('p', 'Pomeranz'), ('p', 'Brenner')),
    ('Settler colonialism: Wolfe & (Tuck, Simpson or Coulthard)', ('p', 'Wolfe'),
     ('set', [('p', 'Tuck'), ('p', 'Simpson'), ('p', 'Coulthard')])),
    ('Settler colonialism: Wolfe & Veracini', ('p', 'Wolfe'), ('p', 'Veracini')),
    ('Capitalism and slavery: (Beckert or W. Johnson) & Baptist', ('set', [('p', 'Beckert'), ('p', 'W. Johnson')]),
     ('w', 'Baptist 2014')),
    ('Human rights: Moyn & L. Hunt (Inventing)', ('p', 'Moyn'), ('w', 'Hunt, Inventing Human Rights (2007)')),
    ('Science studies: Latour & Haraway', ('p', 'Latour'), ('p', 'Haraway')),
    ('Science studies: Latour & Shapin', ('p', 'Latour'), ('p', 'Shapin')),
    ('Postcolonial: Chakrabarty & Cooper', ('p', 'Chakrabarty'), ('p', 'Cooper')),
    ('Archive: Stoler & Trouillot', ('p', 'Stoler'), ('p', 'Trouillot')),
    ('Wilderness: Cronon (Trouble) & Worster', ('w', 'Cronon, Trouble with Wilderness (1996)'), ('p', 'Worster')),
    ('Longue durée: Guldi & Armitage (Manifesto) cited at all', ('w', 'Guldi and Armitage, History Manifesto (2014)'), None),
    ('Challenger: Chakrabarty & Thompson', ('p', 'Chakrabarty'), ('p', 'Thompson')),
    ('Challenger: Chakrabarty & J. Scott', ('p', 'Chakrabarty'), ('p', 'J. Scott')),
    ('Challenger: Chakrabarty & Foucault', ('p', 'Chakrabarty'), ('p', 'Foucault')),
    ('Challenger: Chakrabarty & (Thompson or J. Scott)', ('p', 'Chakrabarty'), ('set', [('p', 'Thompson'), ('p', 'J. Scott')])),
    ('Challenger: Wolfe & Thompson', ('p', 'Wolfe'), ('p', 'Thompson')),
    ('Challenger: Wolfe & J. Scott', ('p', 'Wolfe'), ('p', 'J. Scott')),
    ('Challenger: Wolfe & Foucault', ('p', 'Wolfe'), ('p', 'Foucault')),
    ('Challenger: Wolfe & (Thompson or J. Scott)', ('p', 'Wolfe'), ('set', [('p', 'Thompson'), ('p', 'J. Scott')])),
    ('Challenger: Chakrabarty & Wolfe', ('p', 'Chakrabarty'), ('p', 'Wolfe')),
    ('Challenger: Stoler & (Thompson or J. Scott)', ('p', 'Stoler'), ('set', [('p', 'Thompson'), ('p', 'J. Scott')])),
    ('Challenger: J. C. Scott & (Thompson or J. Scott)', ('p', 'J. C. Scott'), ('set', [('p', 'Thompson'), ('p', 'J. Scott')])),
    ('J. C. Scott & Foucault', ('p', 'J. C. Scott'), ('p', 'Foucault')),
    ('J. C. Scott & Thompson', ('p', 'J. C. Scott'), ('p', 'Thompson')),
    ('Theory pair: Butler & Foucault', ('p', 'Butler'), ('p', 'Foucault')),
    ('Theory pair: Bourdieu & Foucault', ('p', 'Bourdieu'), ('p', 'Foucault')),
    ('Theory pair: Said & Foucault', ('p', 'Said'), ('p', 'Foucault')),
    ('Theory pair: Anderson & Foucault', ('p', 'Anderson'), ('p', 'Foucault')),
]
THEORISTS = ['Foucault', 'Derrida', 'Bourdieu', 'Butler', 'Said', 'Anderson', 'Geertz', 'H. White', 'J. C. Scott',
             'Latour', 'Haraway', 'Agamben', 'Mbembe', 'Deleuze', 'Lefebvre', 'Appadurai', 'Bhabha', 'Spivak',
             'Gilroy', 'Massey', 'Harvey', 'Ahmed', 'Asad', 'Mignolo', 'Rancière', 'Žižek', 'Bennett', 'Tsing',
             'Wynter', 'Quijano', 'Berlant', 'Sedgwick', 'Williams', 'Gramsci', 'Habermas', 'Arendt', 'Benjamin',
             'Certeau', 'Ricoeur', 'Koselleck', 'Hartog', 'Nora', 'Chakrabarty', 'Stoler', 'Cooper', 'Trouillot',
             'Wolfe', 'Hartman', 'Benton', 'Beckert', 'Pomeranz', 'Cronon', 'R. White', 'Davis', 'Ginzburg',
             'Thompson', 'J. Scott', 'Hobsbawm']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, required=True)
    args = ap.parse_args()
    base = args.release.parent.parent
    out = base / 'summary' / 'cohorts'
    out.mkdir(parents=True, exist_ok=True)

    d = pd.read_csv(args.release / 'dissertations.csv.gz')
    d = d[(d.in_analysis == True) & d.year.notna()].copy()  # noqa: E712
    d['year'] = d.year.astype(int)
    d['cohort'] = d.year.map(cohort)
    d['region'] = d.country.map(region)
    d = d.set_index('dissertation_id')
    c = pd.read_csv(args.release / 'citations.csv.gz', usecols=['dissertation_id', 'work_id'])
    c = c[c.dissertation_id.isin(d.index)].drop_duplicates()
    w = pd.read_csv(args.release / 'works.csv.gz', usecols=['work_id', 'year', 'first_author_key', 'cited_by_strict_phds'])
    w = w[w.cited_by_strict_phds >= 3].set_index('work_id')
    c = c[c.work_id.isin(w.index)]
    c['person'] = c.work_id.map(w.first_author_key)
    ppl = pd.read_csv(args.release / 'people.csv.gz', usecols=['person_key', 'name', 'cited_by_dissertations'])
    ppl = ppl.sort_values('cited_by_dissertations', ascending=False).drop_duplicates('name')
    name_key = ppl.set_index('name').person_key.to_dict()
    key_name = ppl.set_index('person_key').name.to_dict()
    pkey = {}
    for disp, nm in PEOPLE.items():
        if nm in name_key:
            pkey[disp] = name_key[nm]
        else:
            print('person not found:', disp, nm)
    missing_w = [k for k, v in WORKS.items() if v not in w.index]
    if missing_w:
        print('works not found:', missing_w)

    thesis_people = c.groupby('dissertation_id').person.apply(set).to_dict()
    thesis_works = c.groupby('dissertation_id').work_id.apply(set).to_dict()

    def citing(spec):
        kind, val = spec
        if kind == 'p':
            k = pkey.get(val)
            return {t for t, s in thesis_people.items() if k in s} if k else set()
        if kind == 'w':
            wid = WORKS[val]
            return {t for t, s in thesis_works.items() if wid in s}
        if kind == 'set':
            r = set()
            for sp in val:
                r |= citing(sp)
            return r
        if kind == 'setand':
            r = None
            for sp in val:
                r = citing(sp) if r is None else r & citing(sp)
            return r or set()
        raise ValueError(kind)

    # ---- dyads by cohort
    groups = {'ALL': d.index, 'CA+US': d[d.region.isin(['CA', 'US'])].index}
    rows = []
    for label, a, b in DYADS:
        sa = citing(a)
        both = sa & citing(b) if b else sa
        for gname, ids in groups.items():
            for coh in COHORTS:
                cids = set(d.loc[ids][d.loc[ids].cohort == coh].index)
                if len(cids) < 50:
                    continue
                rows.append({'dyad': label, 'group': gname, 'cohort': coh, 'theses': len(cids),
                             'share_A': round(len(sa & cids) / len(cids) * 100, 2),
                             'share_both': round(len(both & cids) / len(cids) * 100, 2),
                             'both_given_A': round(len(both & cids) / max(len(sa & cids), 1) * 100, 1)})
    dy = pd.DataFrame(rows)
    dy.to_csv(out / 'debate-dyads.csv', index=False)
    piv = dy[dy.group == 'CA+US'].pivot(index='dyad', columns='cohort', values='share_both').reindex(columns=COHORTS)
    piv = piv.reindex([x[0] for x in DYADS])
    print('\n== DYADS: % of Canada+US theses citing both sides, by cohort')
    print(piv.to_string())
    piv2 = dy[dy.group == 'ALL'].pivot(index='dyad', columns='cohort', values='share_both').reindex(columns=COHORTS)
    print('\n== DYADS: % of ALL theses citing both sides, by cohort')
    print(piv2.reindex([x[0] for x in DYADS]).to_string())

    # ---- breadth across TF-IDF families (theses 2010-25 with dominant family >= 0.4)
    m = pd.read_csv(base / 'summary' / 'tfidf-families' / 'dissertation-mixtures.csv',
                    usecols=['dissertation_id', 'dominant_family', 'dominant_share'])
    m['dissertation_id'] = m.dissertation_id.str.replace('^D:', '', regex=True)
    m = m[(m.dominant_share >= 0.4) & m.dissertation_id.isin(d.index)].set_index('dissertation_id')
    m = m.join(d[['cohort']])
    m = m[m.cohort.isin(['2010-14', '2015-19', '2020-25'])]
    fam_of = m.dominant_family.to_dict()
    fam_size = m.dominant_family.value_counts()
    fam_size = fam_size[fam_size >= 30]
    fams = list(fam_size.index)
    import json
    fam_names = {int(f['id']): f['name'] for f in json.load((base / 'summary' / 'explorer' / 'explorer.json').open())['families']}
    print(f'\nfamilies used: {len(fams)} (>=30 theses 2010-25, dominant >= 0.4), {int(fam_size.sum())} theses')

    def breadth(ids):
        ids = {t for t in ids if t in fam_of}
        shares = {}
        for f in fams:
            n = sum(1 for t in ids if fam_of[t] == f)
            shares[f] = n / fam_size[f]
        v = np.array(list(shares.values()))
        return {'families_ge3pct': int((v >= 0.03).sum()), 'families_ge1pct': int((v >= 0.01).sum()),
                'max_family_pct': round(float(v.max()) * 100, 1), 'mean_family_pct': round(float(v.mean()) * 100, 1),
                'top_family': fam_names.get(max(shares, key=shares.get), ''), 'n_2010_25': len(ids)}

    rows = []
    for disp in PEOPLE:
        if disp in pkey:
            rows.append({'figure': disp, 'kind': 'person', **breadth(citing(('p', disp)))})
    for disp in WORKS:
        if WORKS[disp] in w.index:
            rows.append({'figure': disp, 'kind': 'work', **breadth(citing(('w', disp)))})
    br = pd.DataFrame(rows).sort_values(['kind', 'families_ge3pct', 'mean_family_pct'], ascending=[True, False, False])
    br.to_csv(out / 'breadth.csv', index=False)
    print('\n== BREADTH across families, theses 2010-25 (people)')
    print(br[br.kind == 'person'].drop(columns='kind').to_string(index=False))
    print('\n== BREADTH across families, theses 2010-25 (works)')
    print(br[br.kind == 'work'].drop(columns='kind').to_string(index=False))

    # ---- all first authors with 40+ citing theses 2010-25, ranked by breadth; year of their most cited work
    recent = set(d[d.cohort.isin(['2010-14', '2015-19', '2020-25'])].index)
    cr = c[c.dissertation_id.isin(recent)]
    pc = cr.groupby('person').dissertation_id.nunique()
    cand = pc[pc >= 40].index
    topwork = cr[cr.person.isin(cand)].groupby(['person', 'work_id']).size().reset_index(name='n')
    topwork = topwork.sort_values('n', ascending=False).drop_duplicates('person').set_index('person')
    rows = []
    person_theses = cr[cr.person.isin(cand)].groupby('person').dissertation_id.apply(set)
    for k in cand:
        b = breadth(person_theses[k])
        rows.append({'person': key_name.get(k, k), 'theses_2010_25': int(pc[k]), **b,
                     'top_work': topwork.loc[k, 'work_id'][2:60], 'top_work_year': w.year.get(topwork.loc[k, 'work_id'])})
    bb = pd.DataFrame(rows).sort_values(['families_ge3pct', 'mean_family_pct'], ascending=False)
    bb.to_csv(out / 'breadth-rising.csv', index=False)
    print('\n== BREADTH, all first authors with 40+ citing theses 2010-25: the widest 45')
    print(bb.head(45).to_string(index=False))
    late = bb[bb.top_work_year >= 1995]
    print('\n-- of those, widest 30 whose most-cited work is 1995 or later')
    print(late.head(30).to_string(index=False))

    # ---- theorists by cohort
    rows = []
    for disp in THEORISTS:
        if disp not in pkey:
            continue
        s = citing(('p', disp))
        r = {'figure': disp}
        for gname, ids in groups.items():
            for coh in COHORTS[1:]:
                cids = set(d.loc[ids][d.loc[ids].cohort == coh].index)
                r[f'{gname} {coh}'] = round(len(s & cids) / len(cids) * 100, 1) if len(cids) >= 50 else None
        rows.append(r)
    th = pd.DataFrame(rows)
    th.to_csv(out / 'theorists-by-cohort.csv', index=False)
    cols = ['figure'] + [f'CA+US {c_}' for c_ in COHORTS[1:]] + [f'ALL {c_}' for c_ in COHORTS[3:]]
    print('\n== THEORISTS AND FRAMEWORK FIGURES, % of theses citing, by cohort')
    print(th[cols].to_string(index=False))
    print('done ->', out)


if __name__ == '__main__':
    main()
