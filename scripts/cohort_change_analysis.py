#!/usr/bin/env python3
"""Change beyond the baseline: what newer History PhD cohorts cite that older ones did not.

Raw counts reproduce the universal canon (Anderson, Foucault, Thompson). This script reads the
public release tables (no graph.json load) and writes measures that separate the baseline from
the change, into ``summary/cohorts/``:

- ``age-profile.csv``: for each thesis cohort and region, how old the secondary works cited are
  (publication-decade shares, median age, share under 10 years, share over 30), each thesis
  weighted equally;
- ``distinctive-works-<slice>.csv`` / ``distinctive-people-<slice>.csv``: works and first authors
  that distinguish the 2015-25 cohort from the 2000-09 cohort, by a shrunk log-odds ratio with a
  corpus-share prior (after Monroe, Colaresi and Quinn 2008), with a z-score; slices: Canada+US,
  Canada+US theses that cite one of the three baseline works, Europe (2005-14 vs 2015-25), and each
  TF-IDF family on its own (Canada+US);
- ``post2000-works.csv``: works published from 2000 ranked by the share of 2018-25 theses citing them;
- ``canon-persistence.csv``: how much of each later cohort's citing goes to the 2000-09 top 50, and
  how far each cohort's own top 50 overlaps it;
- ``rising-people-atlas.csv``: the rising first authors against the atlas roster (QID match).

Run: python3 scripts/cohort_change_analysis.py --release data/.../release/2026-10-23
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

EUROPE = {'FR', 'SE', 'DE', 'IT', 'ES', 'BE', 'GB', 'PT', 'GR', 'FI', 'LV', 'PL', 'HU', 'IE', 'MT', 'NL',
          'AT', 'CH', 'DK', 'NO', 'CZ', 'LT', 'EE', 'RO', 'HR', 'SI', 'SK', 'BG', 'IS', 'LU'}
BASELINE_WORKS = ['W:anderson|imagined communities', 'W:foucault|discipline and punish',
                  'W:thompson|the making of the english working class']
SECONDARY_KINDS = {'book', 'article', 'chapter'}


def cohort(y):
    if y < 1990:
        return 'pre1990'
    if y < 2000:
        return '1990-99'
    if y < 2010:
        return '2000-09'
    if y < 2015:
        return '2010-14'
    if y < 2020:
        return '2015-19'
    return '2020-25'


COHORTS = ['pre1990', '1990-99', '2000-09', '2010-14', '2015-19', '2020-25']


def region(c):
    if c in ('CA', 'US'):
        return c
    return 'EUROPE' if c in EUROPE else 'OTHER'


def log_odds(a_counts, n_a, b_counts, n_b, prior_share, alpha0=20.0, min_total=15):
    """Shrunk log-odds ratio of citing share in A against B, prior drawn from the corpus share."""
    rows = []
    keys = set(a_counts) | set(b_counts)
    for k in keys:
        ya, yb = a_counts.get(k, 0), b_counts.get(k, 0)
        if ya + yb < min_total:
            continue
        p = prior_share.get(k, 0.0)
        al = alpha0 * p + 0.5
        be = alpha0 * (1 - p) + 0.5
        la = math.log((ya + al) / (n_a - ya + be))
        lb = math.log((yb + al) / (n_b - yb + be))
        var = 1 / (ya + al) + 1 / (n_a - ya + be) + 1 / (yb + al) + 1 / (n_b - yb + be)
        delta = la - lb
        rows.append((k, ya, yb, ya / n_a, yb / n_b, delta, delta / math.sqrt(var)))
    return pd.DataFrame(rows, columns=['key', 'n_A', 'n_B', 'share_A', 'share_B', 'log_odds', 'z'])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=None, help='default: <release>/../../summary/cohorts')
    ap.add_argument('--mixtures', type=Path, default=None, help='tfidf-families/dissertation-mixtures.csv')
    ap.add_argument('--explorer', type=Path, default=None, help='explorer.json (family names)')
    ap.add_argument('--atlas-people', type=Path, default=Path('data/people-wikidata.json'))
    args = ap.parse_args()
    base = args.release.parent.parent
    out = args.out or base / 'summary' / 'cohorts'
    out.mkdir(parents=True, exist_ok=True)
    fam_dir = base / 'summary' / 'tfidf-families'
    mixtures = args.mixtures or fam_dir / 'dissertation-mixtures.csv'
    explorer = args.explorer or base / 'summary' / 'explorer' / 'explorer.json'

    d = pd.read_csv(args.release / 'dissertations.csv.gz')
    d = d[(d.in_analysis == True) & d.year.notna()].copy()  # noqa: E712
    d['year'] = d.year.astype(int)
    d['cohort'] = d.year.map(cohort)
    d['region'] = d.country.map(region)
    d = d.set_index('dissertation_id')
    print(f'{len(d)} strict theses; by region {d.region.value_counts().to_dict()}')

    c = pd.read_csv(args.release / 'citations.csv.gz', usecols=['dissertation_id', 'work_id', 'via', 'section_side', 'kind'])
    c = c[c.dissertation_id.isin(d.index)]
    w = pd.read_csv(args.release / 'works.csv.gz',
                    usecols=['work_id', 'title', 'year', 'kind', 'first_author_key', 'first_author', 'cited_by_strict_phds'])
    w = w[w.cited_by_strict_phds >= 3].set_index('work_id')
    c = c.join(d[['year', 'cohort', 'region']], on='dissertation_id')

    # ---- 1. Age profile of secondary citing, each thesis weighted equally
    s = c[(c.section_side != 'primary') & c.kind.isin(SECONDARY_KINDS)]
    s = s.join(w[['year']].rename(columns={'year': 'wyear'}), on='work_id')
    s = s[s.wyear.notna()]
    s = s[(s.wyear >= 1800) & (s.wyear <= s.year)]
    s['age'] = s.year - s.wyear
    s['decade'] = np.where(s.wyear < 1960, 'before 1960', (s.wyear // 10 * 10).astype(int).astype(str) + 's')
    rows = []
    for (coh, reg), grp in s.groupby(['cohort', 'region']):
        n_theses = grp.dissertation_id.nunique()
        if n_theses < 20:
            continue
        per = grp.groupby('dissertation_id')
        # thesis-level shares, then averaged
        dec = grp.groupby(['dissertation_id', 'decade']).size().unstack(fill_value=0)
        dec = dec.div(dec.sum(axis=1), axis=0).mean()
        u10 = per.age.apply(lambda a: (a <= 10).mean()).mean()
        o30 = per.age.apply(lambda a: (a >= 30).mean()).mean()
        med = per.age.median().median()
        row = {'cohort': coh, 'region': reg, 'theses': n_theses, 'median_age': med,
               'share_under_10y': round(u10, 3), 'share_over_30y': round(o30, 3)}
        for k in ['before 1960', '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s']:
            row[k] = round(float(dec.get(k, 0.0)), 3)
        rows.append(row)
    age = pd.DataFrame(rows)
    age['cohort'] = pd.Categorical(age.cohort, COHORTS)
    age = age.sort_values(['region', 'cohort'])
    age.to_csv(out / 'age-profile.csv', index=False)
    print('\nAGE PROFILE (secondary works, each thesis weighted equally)')
    print(age.to_string(index=False))

    # ---- presence tables: thesis -> works (any side), thesis -> first authors
    pres = c[['dissertation_id', 'work_id']].drop_duplicates()
    pres = pres[pres.work_id.isin(w.index)]
    first = w.first_author_key
    pres['person'] = pres.work_id.map(first)
    pp = pres[['dissertation_id', 'person']].dropna().drop_duplicates()
    N = len(d)
    prior_w = (pres.groupby('work_id').size() / N).to_dict()
    prior_p = (pp.groupby('person').size() / N).to_dict()
    label = {}
    for wid, r in w.iterrows():
        au = (r.first_author or '').split(',')[0] if isinstance(r.first_author, str) else ''
        t = str(r.title).split(':')[0].strip()
        label[wid] = f'{au}, {t} ({int(r.year)})' if pd.notna(r.year) else f'{au}, {t}'
    pname = w.drop_duplicates('first_author_key').set_index('first_author_key').first_author.to_dict()

    def slice_counts(ids):
        ids = set(ids)
        cw = pres[pres.dissertation_id.isin(ids)].groupby('work_id').size().to_dict()
        cp = pp[pp.dissertation_id.isin(ids)].groupby('person').size().to_dict()
        return cw, cp, len(ids)

    def distinct(name, ids_a, ids_b, label_a, label_b, top=80, min_total=15):
        cwa, cpa, na = slice_counts(ids_a)
        cwb, cpb, nb = slice_counts(ids_b)
        if na < 30 or nb < 30:
            return None, None
        dw = log_odds(cwa, na, cwb, nb, prior_w, min_total=min_total)
        dw['label'] = dw.key.map(label)
        dw['work_year'] = dw.key.map(w.year)
        dp = log_odds(cpa, na, cpb, nb, prior_p, min_total=min_total)
        dp['label'] = dp.key.map(pname)
        for df, kind in ((dw, 'works'), (dp, 'people')):
            df.attrs['A'] = f'{label_a} (n={na})'
            df.attrs['B'] = f'{label_b} (n={nb})'
            rising = df.sort_values('z', ascending=False).head(top)
            fading = df.sort_values('z').head(top // 2)
            res = pd.concat([rising.assign(direction='rising'), fading.assign(direction='fading')])
            res.insert(0, 'A', label_a)
            res.insert(1, 'B', label_b)
            res.to_csv(out / f'distinctive-{kind}-{name}.csv', index=False)
        return dw, dp

    def show(df, n=30, cols=('label', 'n_A', 'n_B', 'share_A', 'share_B', 'z')):
        x = df.sort_values('z', ascending=False).head(n)[list(cols)].copy()
        x['share_A'] = (x.share_A * 100).round(1)
        x['share_B'] = (x.share_B * 100).round(1)
        x['z'] = x.z.round(1)
        print(x.to_string(index=False))

    na_us = d[d.region.isin(['CA', 'US'])]
    A = na_us[na_us.cohort.isin(['2015-19', '2020-25'])].index
    B = na_us[na_us.cohort == '2000-09'].index
    print(f'\n== CANADA+US: 2015-25 (n={len(A)}) vs 2000-09 (n={len(B)})')
    dw, dp = distinct('ca-us', A, B, '2015-25', '2000-09')
    print('-- works rising'); show(dw)
    print('-- works fading'); show(dw.assign(z=-dw.z), 15)
    print('-- people rising'); show(dp, 40)
    print('-- people fading'); show(dp.assign(z=-dp.z), 15)

    # baseline citers: theses citing at least one of the three baseline works
    citers = set(pres[pres.work_id.isin(BASELINE_WORKS)].dissertation_id)
    A2 = [i for i in A if i in citers]
    B2 = [i for i in B if i in citers]
    print(f'\n== CANADA+US theses citing Anderson/Foucault D&P/Thompson Making: 2015-25 (n={len(A2)}) vs 2000-09 (n={len(B2)})')
    dw2, dp2 = distinct('ca-us-baseline-citers', A2, B2, '2015-25', '2000-09')
    print('-- works rising'); show(dw2)
    print('-- people rising'); show(dp2, 30)

    eu = d[d.region == 'EUROPE']
    AE = eu[eu.cohort.isin(['2015-19', '2020-25'])].index
    BE_ = eu[eu.cohort.isin(['2000-09', '2010-14'])].index
    print(f'\n== EUROPE: 2015-25 (n={len(AE)}) vs 2000-14 (n={len(BE_)})')
    dwe, dpe = distinct('europe', AE, BE_, '2015-25', '2000-14')
    if dwe is not None:
        print('-- works rising'); show(dwe, 25)
        print('-- people rising'); show(dpe, 25)

    # per family (Canada+US), dominant family share >= 0.4
    fam_names = {}
    if explorer.exists():
        for f in json.load(explorer.open())['families']:
            fam_names[int(f['id'])] = f['name']
    if mixtures.exists():
        m = pd.read_csv(mixtures, usecols=['dissertation_id', 'dominant_family', 'dominant_share'])
        m['dissertation_id'] = m.dissertation_id.str.replace('^D:', '', regex=True)
        m = m[m.dominant_share >= 0.4].set_index('dissertation_id')
        fam_rows = []
        for fid, grp in m.groupby('dominant_family'):
            ids = set(grp.index)
            fa = [i for i in A if i in ids]
            fb = [i for i in B if i in ids]
            if len(fa) < 30 or len(fb) < 30:
                continue
            r = distinct(f'family-{fid}', fa, fb, '2015-25', '2000-09', top=40, min_total=10)
            if r[0] is None:
                continue
            for df, kind in zip(r, ('work', 'person')):
                top = df.sort_values('z', ascending=False).head(12)
                for _, x in top.iterrows():
                    fam_rows.append({'family': fid, 'family_name': fam_names.get(fid, ''), 'n_2015_25': len(fa), 'n_2000_09': len(fb),
                                     'kind': kind, 'label': x.label, 'share_2015_25': round(x.share_A, 3),
                                     'share_2000_09': round(x.share_B, 3), 'z': round(x.z, 2)})
        fr = pd.DataFrame(fam_rows)
        fr.to_csv(out / 'distinctive-by-family.csv', index=False)
        print('\n== PER FAMILY (Canada+US, dominant share >= 0.4): top rising works')
        for fid, grp in fr[fr.kind == 'work'].groupby('family'):
            g = grp.head(8)
            print(f"family {fid} {fam_names.get(fid, '')}: n {g.n_2015_25.iloc[0]} vs {g.n_2000_09.iloc[0]}")
            for _, x in g.iterrows():
                print(f"   {x.label[:70]:<70} {x.share_2015_25*100:5.1f}% vs {x.share_2000_09*100:5.1f}%  z={x.z}")

    # ---- post-2000 works by share of 2018-25 theses
    recent = d[d.year >= 2018]
    rec_ids = set(recent.index)
    cw_recent = pres[pres.dissertation_id.isin(rec_ids)].groupby('work_id').size()
    reg_counts = {}
    for reg in ('CA', 'US', 'EUROPE'):
        ids = set(recent[recent.region == reg].index)
        reg_counts[reg] = (pres[pres.dissertation_id.isin(ids)].groupby('work_id').size(), len(ids))
    p2 = w[(w.year >= 2000)].copy()
    p2['cited_2018_25'] = p2.index.map(cw_recent).fillna(0).astype(int)
    p2['share_2018_25'] = (p2.cited_2018_25 / len(rec_ids)).round(4)
    for reg, (cnt, n) in reg_counts.items():
        p2[f'share_{reg}'] = (p2.index.map(cnt).fillna(0) / max(n, 1)).round(4)
    p2 = p2[p2.cited_2018_25 >= 10].sort_values('cited_2018_25', ascending=False)
    p2 = p2.reset_index()[['work_id', 'first_author', 'title', 'year', 'cited_by_strict_phds', 'cited_2018_25', 'share_2018_25',
                           'share_CA', 'share_US', 'share_EUROPE']]
    p2.to_csv(out / 'post2000-works.csv', index=False)
    print(f'\n== WORKS PUBLISHED 2000+ by share of 2018-25 theses (n={len(rec_ids)})')
    for _, x in p2.head(60).iterrows():
        print(f"{x.share_2018_25*100:5.1f}%  CA {x.share_CA*100:4.1f} US {x.share_US*100:4.1f} EU {x.share_EUROPE*100:4.1f}  {str(x.first_author).split(',')[0]}, {str(x.title)[:60]} ({int(x.year)})")
    print('\n-- by publication half-decade, top 6 each')
    for lo in (2000, 2005, 2010, 2015, 2020):
        g = p2[(p2.year >= lo) & (p2.year < lo + 5)].head(6)
        print(f'{lo}-{lo+4}:')
        for _, x in g.iterrows():
            print(f"   {x.share_2018_25*100:5.1f}%  {str(x.first_author).split(',')[0]}, {str(x.title)[:60]} ({int(x.year)})")

    # ---- canon persistence (Canada+US): the 2000-09 top 50, later
    ids_b = set(B)
    top_b = pres[pres.dissertation_id.isin(ids_b)].groupby('work_id').size().sort_values(ascending=False).head(50)
    rows = []
    for coh in COHORTS:
        ids = set(na_us[na_us.cohort == coh].index)
        if len(ids) < 30:
            continue
        cnt = pres[pres.dissertation_id.isin(ids)].groupby('work_id').size()
        top_c = set(cnt.sort_values(ascending=False).head(50).index)
        mean_share = float(cnt.reindex(top_b.index).fillna(0).mean() / len(ids))
        any_share = pres[pres.dissertation_id.isin(ids) & pres.work_id.isin(top_b.index)].dissertation_id.nunique() / len(ids)
        rows.append({'cohort': coh, 'theses': len(ids), 'mean_share_of_2000s_top50': round(mean_share, 4),
                     'theses_citing_any_2000s_top50': round(any_share, 3),
                     'overlap_own_top50_with_2000s_top50': len(top_c & set(top_b.index)),
                     'top50_pub_year_median': float(w.year.reindex(list(top_c)).median())})
    cp = pd.DataFrame(rows)
    cp.to_csv(out / 'canon-persistence.csv', index=False)
    print('\n== CANON PERSISTENCE (Canada+US; 2000-09 top 50 works)')
    print(cp.to_string(index=False))


    # ---- robustness 1: institution-stratified log-odds (Canada+US), pooled over universities
    #      with at least 15 theses in each cohort (Mantel-Haenszel-style weighting of per-institution deltas)
    inst_a = d.loc[A].institution
    inst_b = d.loc[B].institution
    common = [i for i in set(inst_a) & set(inst_b) if (inst_a == i).sum() >= 15 and (inst_b == i).sum() >= 15]
    strata = []
    for i in common:
        ia = set(inst_a[inst_a == i].index)
        ib = set(inst_b[inst_b == i].index)
        strata.append((i, slice_counts(ia), slice_counts(ib)))
    print(f'\n== STRATIFIED BY INSTITUTION ({len(common)} universities with >=15 theses in both cohorts): '
          f'{sum(len(set(inst_a[inst_a == i].index)) for i in common)} vs {sum(len(set(inst_b[inst_b == i].index)) for i in common)} theses')

    def stratified(df, which, prior, top_keys):
        rows = []
        for k in top_keys:
            num = den = 0.0
            for inst, (cwa, cpa, na), (cwb, cpb, nb) in strata:
                ca = (cwa if which == 'work' else cpa).get(k, 0)
                cb = (cwb if which == 'work' else cpb).get(k, 0)
                p = prior.get(k, 0.0)
                al = 20.0 * p + 0.5
                be = 20.0 * (1 - p) + 0.5
                delta = math.log((ca + al) / (na - ca + be)) - math.log((cb + al) / (nb - cb + be))
                var = 1 / (ca + al) + 1 / (na - ca + be) + 1 / (cb + al) + 1 / (nb - cb + be)
                num += delta / var
                den += 1 / var
            rows.append((k, num / den if den else 0.0, (num / den) * math.sqrt(den) if den else 0.0))
        return pd.DataFrame(rows, columns=['key', 'strat_log_odds', 'strat_z'])

    checks = []
    for df, which, prior in ((dw, 'work', prior_w), (dp, 'person', prior_p)):
        top = pd.concat([df.sort_values('z', ascending=False).head(60), df.sort_values('z').head(30)])
        st = stratified(df, which, prior, list(top.key)).set_index('key')
        top = top.set_index('key').join(st).reset_index()
        top['kind'] = which
        checks.append(top)
    st = pd.concat(checks)
    st['agrees'] = np.sign(st.z) == np.sign(st.strat_z)
    st[['kind', 'label', 'n_A', 'n_B', 'share_A', 'share_B', 'z', 'strat_z', 'agrees']].to_csv(out / 'robustness-stratified.csv', index=False)
    print(f"sign agreement pooled vs stratified: {int(st.agrees.sum())}/{len(st)}; "
          f"|strat_z|>=2 for {int((st.strat_z.abs() >= 2).sum())} of {len(st)}")
    weak = st[(st.z.abs() >= 2.5) & (st.strat_z.abs() < 1.5)]
    print('pooled-significant but weak once stratified:')
    for _, x in weak.iterrows():
        print(f"   {x.kind:<6} {x.label[:60]:<60} z={x.z:.1f} strat_z={x.strat_z:.1f}")

    # ---- robustness 2: age profile with bibliography length held roughly constant (100-250 works), bibliography-only
    bl = c[c.via == 'bibliography'].groupby('dissertation_id').size() if 'via' in c.columns else None
    nw = pres.groupby('dissertation_id').size()
    mid = set(nw[(nw >= 100) & (nw <= 250)].index)
    s2 = s[s.dissertation_id.isin(mid) & s.region.isin(['CA', 'US'])]
    rows = []
    for coh, grp in s2.groupby('cohort'):
        n_theses = grp.dissertation_id.nunique()
        if n_theses < 30:
            continue
        per = grp.groupby('dissertation_id')
        rows.append({'cohort': coh, 'theses_100_250_works': n_theses, 'median_age': per.age.median().median(),
                     'share_under_10y': round(per.age.apply(lambda a: (a <= 10).mean()).mean(), 3),
                     'share_over_30y': round(per.age.apply(lambda a: (a >= 30).mean()).mean(), 3)})
    ac = pd.DataFrame(rows)
    ac['cohort'] = pd.Categorical(ac.cohort, COHORTS)
    ac = ac.sort_values('cohort')
    ac.to_csv(out / 'age-profile-controlled.csv', index=False)
    print('\n== AGE PROFILE, Canada+US theses citing 100-250 works only')
    print(ac.to_string(index=False))

    # ---- canon vs newer frameworks: share of theses citing any of each set, by cohort (Canada+US)
    ppl_tab = pd.read_csv(args.release / 'people.csv.gz', usecols=['person_key', 'name', 'cited_by_dissertations'])
    ppl_tab = ppl_tab.sort_values('cited_by_dissertations', ascending=False).drop_duplicates('name')
    name_key = ppl_tab.set_index('name').person_key.to_dict()
    CANON_N = ['Foucault, Michel', 'Anderson, Benedict', 'Thompson, Edward P', 'Said, Edward', 'Bourdieu, Pierre',
               'Hobsbawm, Eric', 'Geertz, Clifford', 'Scott, Joan W']
    NEWER_N = ['Stoler, Ann Laura', 'Wolfe, Patrick', 'Trouillot, Michel-Rolph', 'Benton, Lauren', 'Beckert, Sven',
               'Johnson, Walter', 'Cooper, Frederick', 'Chakrabarty, Dipesh', 'Veracini, Lorenzo', 'Hartman, Saidiya',
               'Butler, Judith', 'Scott, James C']
    CANON = [name_key[n] for n in CANON_N if n in name_key]
    NEWER = [name_key[n] for n in NEWER_N if n in name_key]
    print('\nkeys:', dict(zip(CANON_N + NEWER_N, CANON + NEWER)), 'missing:', [n for n in CANON_N + NEWER_N if n not in name_key])
    rows = []
    for coh in COHORTS:
        ids = set(na_us[na_us.cohort == coh].index)
        if len(ids) < 30:
            continue
        sub = pp[pp.dissertation_id.isin(ids)]
        any_c = sub[sub.person.isin(CANON)].dissertation_id.nunique() / len(ids)
        any_n = sub[sub.person.isin(NEWER)].dissertation_id.nunique() / len(ids)
        both = len(set(sub[sub.person.isin(CANON)].dissertation_id) & set(sub[sub.person.isin(NEWER)].dissertation_id)) / len(ids)
        rows.append({'cohort': coh, 'theses': len(ids), 'cites_any_canon_1963_91': round(any_c, 3),
                     'cites_any_newer_2000s': round(any_n, 3), 'cites_both': round(both, 3),
                     'newer_without_canon': round(any_n - both, 3)})
    cn = pd.DataFrame(rows)
    cn.to_csv(out / 'canon-vs-newer.csv', index=False)
    print('\n== CANON (Foucault, Anderson, Thompson, Said, Bourdieu, Hobsbawm, Geertz, J. Scott) vs NEWER '
          '(Stoler, Wolfe, Trouillot, Benton, Beckert, W. Johnson, Cooper, Chakrabarty, Veracini, Hartman, Butler, J.C. Scott), Canada+US')
    print(cn.to_string(index=False))

    # ---- rising people against the atlas roster
    atlas = {}
    if args.atlas_people.exists():
        for p in json.load(args.atlas_people.open())['people']:
            q = (p.get('wikidata') or {}).get('qid')
            if q and p.get('status') == 'accepted':
                atlas[q] = p.get('label')
    people = pd.read_csv(args.release / 'people.csv.gz', usecols=['person_key', 'qid']).set_index('person_key').qid.to_dict()
    r = dp.sort_values('z', ascending=False).head(150).copy()
    r['qid'] = r.key.map(people)
    r['atlas_label'] = r.qid.map(atlas)
    r['in_atlas'] = r.atlas_label.notna()
    r[['label', 'qid', 'in_atlas', 'atlas_label', 'n_A', 'n_B', 'share_A', 'share_B', 'z']].to_csv(out / 'rising-people-atlas.csv', index=False)
    print(f"\nRising people (top 150 by z, Canada+US): {int(r.in_atlas.sum())} in the atlas, {int((~r.in_atlas).sum())} not")
    print('not in atlas, top 40:')
    for _, x in r[~r.in_atlas].head(40).iterrows():
        print(f"   {x.label:<30} {x.share_A*100:5.1f}% vs {x.share_B*100:5.1f}%  z={x.z:.1f}  {x.qid if isinstance(x.qid, str) else ''}")
    print('done ->', out)


if __name__ == '__main__':
    main()
