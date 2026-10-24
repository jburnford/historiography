#!/usr/bin/env python3
"""Which fields are new? Field engagement by cohort from seed authors, and TF-IDF family shares.

For each candidate field a seed list of its core authors (first-author keys, resolved from surname and
given-name initial, most-cited key wins) and the share of theses in each cohort and region citing at least
one and at least two of them. Two seeds is the engagement proxy: one seed can be a passing citation of
Cronon or Wolfe; two is a field being read. Also the TF-IDF family shares by cohort and region (dominant
family >= 0.4) as a seed-free check. Writes ``summary/cohorts/field-engagement.csv``,
``field-seeds-resolved.csv``, ``family-shares-by-cohort.csv`` and prints the tables.

Run: python3 scripts/field_emergence_analysis.py --release data/.../release/2026-10-23
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cohort_change_analysis import COHORTS, cohort, region

# surname, given initial(s) as printed in bibliographies; the resolver matches key prefix 'surname|g'
FIELDS = {
    'environment': ['Cronon W', 'Worster D', 'Merchant C', 'Crosby A', 'McNeill J', 'Steinberg T', 'Sutter P',
                    'Loo T', 'Piper L', 'MacEachern A', 'Nash R', 'Hays S', 'Warde P', 'Castonguay S', 'Evenden M',
                    'Radkau J', 'Sörlin S', 'Fiege M', 'Isenberg A', 'Rome A', 'Judd R', 'Uekötter F', 'Pyne S',
                    'Guha R', 'Grove R', 'Beinart W', 'Mitman G', 'Nash L', 'Hurley A', 'Melosi M', 'Tarr J',
                    'Colten C', 'Stewart M', 'Mosley S', 'Hughes J D', 'Jørgensen D', 'Coates P', 'Sandlos J',
                    'Binnema T', 'Kheraj S', 'Wynn G', 'Bavington D', 'Zeller S', 'Stroud E', 'Andrews T',
                    'Langston N', 'Jacoby K', 'Spence M', 'Warren L', 'Brooks K'],
    'settler_colonial': ['Wolfe P', 'Veracini L', 'Tuck E', 'Simpson A', 'Coulthard G', 'Jacobs M', 'Edmonds P',
                         'Banivanua Mar T', 'Mar T', 'Banner S', 'Denoon D', 'Stasiulis D', 'Moreton-Robinson A',
                         'Byrd J', 'Morgensen S', 'Kauanui J', 'Lowe L', 'Elkins C', 'Cavanagh E', 'Hixson W',
                         'Belich J', 'Weaver J', 'Bateman F', 'Rifkin M', 'Goldstein A', 'Pasternak S',
                         'Mawani R', 'Stanger-Ross J', 'Harris C', 'Perry A', 'Carter S', 'Daschuk J',
                         'Simpson L', 'Barker J', 'Arvin M', 'Estes N', 'Dunbar-Ortiz R', 'Hokowhitu B'],
    'emotions': ['Reddy W', 'Rosenwein B', 'Stearns P', 'Plamper J', 'Frevert U', 'Boddice R', 'Matt S', 'Dixon T',
                 'Scheer M', 'Eustace N', 'Bourke J', 'Bound Alberti F', 'Broomhall S', 'Nagy P', 'Olsen S',
                 'Lemmings D', 'Barclay K', 'Bailey J', 'Stearns C', 'Gammerl B', 'Lutz C', 'Hochschild A'],
    'affect_theory': ['Ahmed S', 'Massumi B', 'Berlant L', 'Sedgwick E', 'Cvetkovich A', 'Ngai S', 'Stewart K',
                      'Gregg M', 'Clough P', 'Thrift N', 'Brennan T', 'Tomkins S', 'Probyn E'],
    'history_of_capitalism': ['Beckert S', 'Johnson W', 'Baptist E', 'Hyman L', 'Levy J', 'Ott J', 'Zakim M',
                              'Rockman S', 'Lipartito K', 'Sklansky J', 'Kocka J', 'Piketty T', 'Schermerhorn C',
                              'Olmstead A', 'Rhode P', 'Williams E', 'Inikori J', 'Mihm S', 'Rosenthal C',
                              'Levine B', 'Trentmann F', 'Appleby J'],
    'global_transnational': ['Bayly C', 'Osterhammel J', 'Conrad S', 'Subrahmanyam S', 'Iriye A', 'Tyrrell I',
                             'Saunier P', 'Manning P', 'Bentley J', 'Pomeranz K', 'Hopkins A', 'Clavin P',
                             'Sachsenmaier D', 'Mazlish B', 'Geyer M', 'Bright C', 'Wong R', 'Frank A',
                             'Wallerstein I', 'Hunt L', 'Armitage D', 'Sluga G', 'Rodgers D', 'Thelen D',
                             'Seigel M', 'Werner M', 'Zimmermann B'],
    'borderlands': ['Adelman J', 'Aron S', 'Truett S', 'Hämäläinen P', 'DuVal K', 'Barr J', 'Weber D', 'Johnson B',
                    'Graybill A', 'Blackhawk N', 'St. John R', 'Hogue M', 'McManus S', 'Evans S', 'Ramirez B',
                    'Rodríguez M', 'Baud M', 'Van Schendel W', 'Sahlins P', 'Hoy B', 'Witgen M', 'Brooks J'],
    'human_rights': ['Moyn S', 'Hunt L', 'Hoffmann S', 'Eckel J', 'Iriye A', 'Burke R', 'Cmiel K', 'Keys B',
                     'Mazower M', 'Jensen S', 'Simpson A W B', 'Lauren P', 'Ishay M', 'Snyder S', 'Bradley M',
                     'Normand R', 'Zaidi S', 'Glendon M', 'Borgwardt E', 'Dudziak M'],
    'digital_history': ['Cohen Daniel', 'Rosenzweig R', 'Graham S', 'Milligan I', 'Weingart S', 'Guldi J', 'Moretti F',
                        'Ayers E', 'Thomas W', 'Gibbs F', 'Owens T', 'Hitchcock T', 'Underwood T', 'Jockers M',
                        'Blevins C', 'Robertson S', 'Nicholson B', 'Putnam L', 'Manovich L', 'Drucker J',
                        'Gregory I', 'Knowles A', 'Bodenhamer D'],
    'animal_history': ['Ritvo H', 'Fudge E', 'Kean H', 'Pearson S', 'Anderson V', 'Nance S', 'Brantz D',
                       'Swart S', 'Haraway D', 'Baratay E', 'Pearson C', 'Greene A', 'McShane C',
                       'Tarr J', 'Rothfels N', 'Kalof L', 'Montgomery G', 'Mizelle B', 'Few M', 'Tortorici Z',
                       'Shaw D', 'Benson E', 'Wolch J', 'Philo C', 'Wilcox S', 'Rutherford S', 'Colpitts G'],
    'disability_history': ['Longmore P', 'Kudlick C', 'Baynton D', 'Rembis M', 'Nielsen K', 'Burch S', 'Stiker H',
                           'Garland-Thomson R', 'Davis L', 'Linker B', 'Carey A', 'Rose Sarah', 'Williamson B',
                           'Schweik S', 'Rose M', 'Metzler I', 'Turner D', 'Borsay A', 'Kudlick C', 'Reaume G',
                           'Burch S', 'Jarrett S'],
    'sensory_history': ['Smith M M', 'Corbin A', 'Classen C', 'Howes D', 'Jütte R', 'Hoffer P', 'Jenner M',
                        'Rath R', 'Schafer R', 'Thompson Emily', 'Sterne J', 'Picker J', 'Jay M', 'Crary J',
                        'Kiechle M', 'Tullett W', 'Bijsterveld K', 'Boutin A', 'Woolgar C', 'Cockayne E'],
    'spatial_turn': ['Lefebvre H', 'Massey D', 'Soja E', 'Harvey D', 'Tuan Y', 'Cresswell T', 'de Certeau M',
                     'CERTEAU M', 'Casey E', 'Basso K', 'Warf B', 'Ethington P', 'Kingston R', 'Guldi J',
                     'Gregory I', 'Knowles A', 'Withers C', 'Gieryn T', 'Agnew J', 'Harris C', 'Wynn G',
                     'Blomley N', 'Mitchell D', 'Bachelard G', 'Augé M'],
    'medical_health': ['Rosenberg C', 'Porter R', 'Kelm M', 'Lux M', 'Mosby I', 'Daschuk J', 'Arnold D', 'Vaughan M',
                       'Packard R', 'Tomes N', 'Warner J', 'Duffin J', 'Bynum W', 'Rosen G',
                       'Leavitt J', 'Brandt A', 'Starr P', 'Jones D', 'Burnham J', 'McCallum M', 'Anderson W',
                       'Comaroff J', 'Hogarth R', 'Greene Jeremy', 'Rogers N', 'Wailoo K'],
    'archive_as_object': ['Stoler A', 'Trouillot M', 'Farge A', 'Hartman S', 'Fuentes M', 'Derrida J', 'Steedman C',
                          'Burton A', 'Blouin F', 'Rosenberg W', 'Manoff M', 'Schwartz J', 'Cook T', 'Zeitlyn D',
                          'Burns K', 'Arondekar A', 'Ghosh D', 'Lowry J', 'Caswell M', 'Cvetkovich A', 'Dirks N',
                          'Richards T', 'Bastian J', 'Mbembe A', 'Echevarría R', 'Taylor D', 'Hamilton C'],
}
PAIRED_FOR_SCALE = {
    'gender_core': ['Scott Joan', 'Butler J', 'Davidoff L', 'Hall C', 'Kessler-Harris A', 'Bederman G', 'Canning K',
                    'Downs L', 'Riley D', 'Kerber L', 'Parr J', 'Sangster J', 'Iacovetta F', 'Valverde M',
                    'Walkowitz J', 'Rose S O', 'Clark A', 'Gowing L', 'Laqueur T', 'Connell R', 'Tosh J',
                    'Roper M', 'Kimmel M', 'Rotundo E', 'Hoganson K', 'Levine P', 'Burton A', 'Stoler A',
                    'McClintock A', 'Sinha M', 'Perry A', 'Higginbotham E', 'Hine D', 'Morgan J', 'Camp S'],
    'labour_core': ['Thompson Edward', 'Hobsbawm E', 'Montgomery D', 'Gutman H', 'Kealey G', 'Palmer B', 'Heron C',
                    'Joyce P', 'Stedman Jones G', 'Sewell W', 'Katznelson I', 'Roediger D', 'Cowie J',
                    'Lichtenstein N', 'Brody D', 'Dubofsky M', 'Rouillard J', 'Frank D', 'Eley G', 'Nield K',
                    'Steedman C', 'Savage M', 'Kirk N', 'McKay I', 'Sangster J', 'Bradbury B', 'Hinton J'],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, required=True)
    args = ap.parse_args()
    base = args.release.parent.parent
    out = base / 'summary' / 'cohorts'

    d = pd.read_csv(args.release / 'dissertations.csv.gz')
    d = d[(d.in_analysis == True) & d.year.notna()].copy()  # noqa: E712
    d['year'] = d.year.astype(int)
    d['cohort'] = d.year.map(cohort)
    d['region'] = d.country.map(region)
    d = d.set_index('dissertation_id')
    c = pd.read_csv(args.release / 'citations.csv.gz', usecols=['dissertation_id', 'work_id'])
    c = c[c.dissertation_id.isin(d.index)].drop_duplicates()
    w = pd.read_csv(args.release / 'works.csv.gz', usecols=['work_id', 'first_author_key', 'cited_by_strict_phds'])
    w = w[w.cited_by_strict_phds >= 2].set_index('work_id')
    c = c[c.work_id.isin(w.index)]
    c['person'] = c.work_id.map(w.first_author_key)
    ppl = pd.read_csv(args.release / 'people.csv.gz', usecols=['person_key', 'name', 'cited_by_dissertations'])
    ppl = ppl[ppl.person_key.str.contains(r'\|', na=False)]
    ppl['surname'] = ppl.person_key.str.split('|').str[0]
    ppl['given'] = ppl.person_key.str.split('|').str[1].fillna('')
    by_surname = {k: g.sort_values('cited_by_dissertations', ascending=False) for k, g in ppl.groupby('surname')}

    def fold(s):
        import unicodedata
        return ''.join(ch for ch in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(ch))

    def resolve(seed):
        parts = seed.split(' ')
        # surname may be multiword ('Stedman Jones G', 'Banivanua Mar T', 'St. John R', 'Bound Alberti F', 'de Certeau M')
        for cut in range(len(parts) - 1, 0, -1):
            sur = fold(' '.join(parts[:cut]).replace('.', '').replace("'", ''))
            giv = fold(''.join(parts[cut:]))
            g = by_surname.get(sur)
            if g is None:
                continue
            # a one-letter given name matches the initial; a longer one must match as a prefix (no fallback)
            m = g[g.given.str.replace(' ', '').str.startswith(giv if len(giv) > 1 else giv[:1])]
            if len(m):
                r = m.iloc[0]
                return r.person_key, r['name'], int(r.cited_by_dissertations)
        return None, None, 0

    thesis_people = c.groupby('dissertation_id').person.apply(set).to_dict()
    groups = {'ALL': d.index, 'CA+US': d[d.region.isin(['CA', 'US'])].index, 'CA': d[d.region == 'CA'].index,
              'US': d[d.region == 'US'].index, 'EUROPE': d[d.region == 'EUROPE'].index}
    seed_rows, rows = [], []
    for field, seeds in {**FIELDS, **PAIRED_FOR_SCALE}.items():
        keys = {}
        for sd in seeds:
            k, nm, n = resolve(sd)
            seed_rows.append({'field': field, 'seed': sd, 'person_key': k, 'name': nm, 'cited_by': n})
            if k:
                keys[k] = nm
        counts = {t: len(s & keys.keys()) for t, s in thesis_people.items()}
        for gname, ids in groups.items():
            for coh in COHORTS:
                cids = [t for t in ids if d.at[t, 'cohort'] == coh]
                if len(cids) < 50:
                    continue
                n1 = sum(1 for t in cids if counts.get(t, 0) >= 1)
                n2 = sum(1 for t in cids if counts.get(t, 0) >= 2)
                n3 = sum(1 for t in cids if counts.get(t, 0) >= 3)
                rows.append({'field': field, 'group': gname, 'cohort': coh, 'theses': len(cids),
                             'ge1_pct': round(n1 / len(cids) * 100, 1), 'ge2_pct': round(n2 / len(cids) * 100, 1),
                             'ge3_pct': round(n3 / len(cids) * 100, 1)})
        # which seeds carry the field in 2015-25 (ALL)
        rec = [t for t in d[d.cohort.isin(['2015-19', '2020-25'])].index]
        top = sorted(((sum(1 for t in rec if k in thesis_people.get(t, ())), nm) for k, nm in keys.items()), reverse=True)[:6]
        print(f"{field}: {len(keys)}/{len(seeds)} seeds resolved; top 2015-25: " + ', '.join(f'{nm} {n}' for n, nm in top))
    sr = pd.DataFrame(seed_rows)
    sr.to_csv(out / 'field-seeds-resolved.csv', index=False)
    unresolved = sr[sr.person_key.isna()]
    print('\nunresolved seeds:', ', '.join(f"{r.field}:{r.seed}" for _, r in unresolved.iterrows()))
    fe = pd.DataFrame(rows)
    fe.to_csv(out / 'field-engagement.csv', index=False)
    for gname in ('CA+US', 'CA', 'US', 'EUROPE'):
        for meas in ('ge2_pct', 'ge1_pct'):
            piv = fe[fe.group == gname].pivot(index='field', columns='cohort', values=meas).reindex(columns=COHORTS)
            piv = piv.reindex(list(FIELDS) + list(PAIRED_FOR_SCALE))
            print(f'\n== FIELD ENGAGEMENT {gname}: % of theses citing {"2+" if meas == "ge2_pct" else "1+"} seed authors')
            print(piv.to_string())

    # ---- TF-IDF family shares by cohort and region (seed-free check)
    m = pd.read_csv(base / 'summary' / 'tfidf-families' / 'dissertation-mixtures.csv',
                    usecols=['dissertation_id', 'dominant_family', 'dominant_share'])
    m['dissertation_id'] = m.dissertation_id.str.replace('^D:', '', regex=True)
    m = m[m.dissertation_id.isin(d.index)].set_index('dissertation_id').join(d[['cohort', 'region']])
    m = m[m.dominant_share >= 0.4]
    names = {int(f['id']): f['name'] for f in json.load((base / 'summary' / 'explorer' / 'explorer.json').open())['families']}
    rows = []
    for (reg, coh), g in m.groupby(['region', 'cohort']):
        if len(g) < 40:
            continue
        vc = g.dominant_family.value_counts(normalize=True) * 100
        for fid, pct in vc.items():
            rows.append({'region': reg, 'cohort': coh, 'theses_placed': len(g), 'family': fid,
                         'family_name': names.get(fid, ''), 'pct': round(pct, 1)})
    fs = pd.DataFrame(rows)
    fs.to_csv(out / 'family-shares-by-cohort.csv', index=False)
    for reg in ('CA', 'US', 'EUROPE'):
        piv = fs[fs.region == reg].pivot(index='family_name', columns='cohort', values='pct').reindex(columns=COHORTS)
        print(f'\n== TF-IDF FAMILY SHARE OF PLACED THESES, {reg} (dominant >= 0.4)')
        print(piv.fillna(0).to_string())
    print('done ->', out)


if __name__ == '__main__':
    main()
