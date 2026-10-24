#!/usr/bin/env python3
"""Snowball: how the network of scholarship around a field's founding works grew, cohort by cohort.

For each field a few founding works (Cronon, Worster and White for environmental history; Foucault's
*History of Sexuality* I, Chauncey, D'Emilio, Weeks, Sedgwick and Kinsman for sexuality and queer history;
and so on). In each thesis cohort:

1. field theses = theses citing at least one founding work;
2. the neighbourhood = works cited by enough field theses (support) and far more often by them than by the
   cohort as a whole (lift); founding works plus neighbourhood = round-1 network;
3. snowball once: field theses = theses citing at least two network works; recompute the neighbourhood.

The network's size (works, first authors), the theses it reaches, its density (network works cited per
field thesis), the new entrants (works not in any earlier cohort's network) and the age of its members are
written to ``summary/cohorts/snowball-summary.csv`` and ``snowball-members.csv``. The founding works are
the same in every cohort, so the growth is the field's, not the seeds'.

Run: python3 scripts/field_snowball_analysis.py --release data/.../release/2026-10-23 [--region CA+US|ALL]
"""
from __future__ import annotations

import argparse
import random
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from cohort_change_analysis import COHORTS, cohort, log_odds, region

# (first-author key prefix, title substring) resolved to the most cited matching work
FIELDS = {
    'environment': [('cronon', 'changes in the land'), ('cronon', 'nature'), ('cronon', 'trouble with wilderness'),
                    ('worster', 'dust bowl'), ('worster', 'rivers of empire'), ('worster', 'nature'),
                    ('white|r', 'organic machine'), ('crosby', 'ecological imperialism'), ('merchant', 'death of nature')],
    'sexuality_queer': [('chauncey', 'gay new york'), ('demilio', 'sexual politics'), ('demilio', 'intimate matters'),
                        ('weeks', 'politics and society'), ('sedgwick', 'epistemology'), ('kinsman', 'regulation of desire'),
                        ('halperin|d', 'how to do the history'), ('canaday', 'straight state'), ('duggan', 'sapphic slashers'),
                        ('meyerowitz', 'how sex changed'), ('rupp', 'desired past'), ('boyd', 'wide open town')],
    'settler_colonial': [('wolfe', 'settler colonialism and the elimination'), ('wolfe', 'settler colonialism and the transformation'),
                         ('veracini', 'settler colonialism'), ('tuck', 'decolonization is not')],
    'emotions': [('reddy', 'navigation of feeling'), ('rosenwein', 'worrying about emotions'), ('rosenwein', 'emotional communities'),
                 ('stearns', 'emotionology'), ('stearns', 'american cool'), ('plamper', 'history of emotions')],
    'indigenous': [('white|r', 'middle ground'), ('richter', 'facing east'), ('deloria|p', 'playing indian'),
                   ('smith|l', 'decolonizing methodologies'), ('miller|j', 'skyscrapers hide the heavens')],
    'history_of_capitalism': [('beckert', 'empire of cotton'), ('johnson|w', 'river of dark dreams'), ('baptist', 'half has never'),
                              ('levy|j', 'freaks of fortune'), ('hyman', 'debtor nation'), ('rockman', 'scraping by')],
    'global_transnational': [('bayly', 'birth of the modern world'), ('osterhammel', 'transformation of the world'),
                             ('pomeranz', 'great divergence'), ('subrahmanyam', 'connected histories'),
                             ('conrad', 'what is global history'), ('iriye', 'global and transnational')],
    'memory': [('nora', 'lieux de m'), ('nora', 'realms of memory'), ('halbwachs', 'collective memory'),
               ('halbwachs', 'mémoire collective'), ('winter', 'sites of memory'), ('assmann', 'cultural memory')],
    'gender_scale': [('scott|joan', 'gender'), ('butler', 'gender trouble'), ('davidoff', 'family fortunes'),
                     ('bederman', 'manliness and civilization')],
    'labour_scale': [('thompson|e', 'making of the english working class'), ('gutman', 'culture and society'),
                     ('montgomery', 'fall of the house of labor'), ('kealey', 'toronto workers'),
                     ('palmer', 'working class experience')],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--region', default='CA+US', help='CA+US (default), ALL, CA, US or EUROPE')
    ap.add_argument('--min-support', type=int, default=5)
    ap.add_argument('--min-z', type=float, default=2.0)
    ap.add_argument('--support-share', type=float, default=0.10, help='support must also reach this share of field theses')
    ap.add_argument('--min-lift', type=float, default=3.0)
    ap.add_argument('--snowball', action='store_true', help='add one anchored snowball round (off by default)')
    ap.add_argument('--sample', type=int, default=15)
    ap.add_argument('--draws', type=int, default=300)
    ap.add_argument('--min-field', type=int, default=15, help='skip cohorts with fewer field theses than this')
    args = ap.parse_args()
    base = args.release.parent.parent
    out = base / 'summary' / 'cohorts'

    d = pd.read_csv(args.release / 'dissertations.csv.gz')
    d = d[(d.in_analysis == True) & d.year.notna()].copy()  # noqa: E712
    d['year'] = d.year.astype(int)
    d['cohort'] = d.year.map(cohort)
    d['region'] = d.country.map(region)
    if args.region == 'CA+US':
        d = d[d.region.isin(['CA', 'US'])]
    elif args.region != 'ALL':
        d = d[d.region == args.region]
    d = d.set_index('dissertation_id')
    c = pd.read_csv(args.release / 'citations.csv.gz', usecols=['dissertation_id', 'work_id'])
    c = c[c.dissertation_id.isin(d.index)].drop_duplicates()
    w = pd.read_csv(args.release / 'works.csv.gz',
                    usecols=['work_id', 'title', 'year', 'first_author_key', 'first_author', 'cited_by_strict_phds'])
    w = w[w.cited_by_strict_phds >= 4].set_index('work_id')
    c = c[c.work_id.isin(w.index)]
    thesis_works = c.groupby('dissertation_id').work_id.apply(set).to_dict()
    work_theses = c.groupby('work_id').dissertation_id.apply(set).to_dict()
    cohort_ids = {coh: set(d[d.cohort == coh].index) for coh in COHORTS}

    def label(wid):
        r = w.loc[wid]
        au = str(r.first_author).split(',')[0] if isinstance(r.first_author, str) else ''
        y = f' ({int(r.year)})' if pd.notna(r.year) else ''
        return f"{au}, {str(r.title).split(':')[0][:48]}{y}"

    def find_work(author_prefix, title_sub):
        m = w[w.first_author_key.str.startswith(author_prefix, na=False) & w.title.str.lower().str.contains(title_sub, regex=False, na=False)]
        return m.cited_by_strict_phds.idxmax() if len(m) else None

    summary, members = [], []
    for field, seeds in FIELDS.items():
        seed_ids = []
        for a, t in seeds:
            wid = find_work(a, t)
            if wid:
                seed_ids.append(wid)
            else:
                print(f'  {field}: seed not found {a} / {t}')
        seed_set = set(seed_ids)
        print(f'\n== {field}: {len(seed_set)} seeds: ' + '; '.join(label(s) for s in seed_ids))
        seen = set()
        for coh in COHORTS:
            ids = cohort_ids[coh]
            if len(ids) < 50:
                continue
            n_coh = len(ids)
            cohort_count = Counter()
            for t in ids:
                cohort_count.update(thesis_works.get(t, ()))

            def neighbourhood(field_theses, network):
                sup = Counter()
                for t in field_theses:
                    sup.update(thesis_works.get(t, ()))
                nf = len(field_theses)
                cand = {wid: s for wid, s in sup.items()
                        if wid not in network and s >= args.min_support and s >= args.support_share * nf}
                if not cand:
                    return {}
                rest = {wid: cohort_count[wid] - cand[wid] for wid in cand}
                prior = {wid: cohort_count[wid] / n_coh for wid in cand}
                lo = log_odds(cand, nf, rest, n_coh - nf, prior, alpha0=10.0, min_total=args.min_support)
                found = {}
                for _, r in lo.iterrows():
                    lift = (cand[r.key] / nf) / (cohort_count[r.key] / n_coh)
                    if lift >= args.min_lift:
                        found[r.key] = (int(cand[r.key]), round(lift, 1))
                return found

            t0 = {t for t in ids if thesis_works.get(t, set()) & seed_set}
            if len(t0) < args.min_field:
                summary.append({'field': field, 'cohort': coh, 'cohort_theses': n_coh, 'seed_citers': len(t0)})
                continue
            n1 = neighbourhood(t0, seed_set)
            if args.snowball:
                # one anchored round: a field thesis cites a founding work, or at least three network works
                net1 = seed_set | set(n1)
                t1 = {t for t in ids if (thesis_works.get(t, set()) & seed_set) or len(thesis_works.get(t, set()) & net1) >= 3}
                n2 = neighbourhood(t1, seed_set)
                field_theses = t1
            else:
                n2, field_theses = n1, t0
            net2 = seed_set | set(n2)
            # power-equalised neighbourhood: resample a fixed number of seed citers; a work is in the
            # neighbourhood of a draw when >= 3 of them cite it and it is cited >= 3x as often as in the cohort
            rng = random.Random(0)
            pool = sorted(t0)
            mid = {'pre1990': 1985, '1990-99': 1995, '2000-09': 2005, '2010-14': 2012, '2015-19': 2017, '2020-25': 2022}[coh]
            eq, eq_recent, eq_med = [], [], []
            for _ in range(args.draws):
                samp = rng.sample(pool, args.sample)
                sup = Counter()
                for t in samp:
                    sup.update(thesis_works.get(t, ()))
                hood = [wid for wid, k in sup.items() if wid not in seed_set and k >= 3
                        and (k / args.sample) / (cohort_count[wid] / n_coh) >= 3]
                ys = [int(w.at[x, 'year']) for x in hood if pd.notna(w.at[x, 'year'])]
                eq.append(len(hood))
                eq_recent.append(sum(1 for y in ys if mid - y <= 10))
                if ys:
                    eq_med.append(float(pd.Series(ys).median()))
            eq_size = sum(eq) / len(eq)
            eq_rec = sum(eq_recent) / len(eq_recent)
            eq_year = sum(eq_med) / len(eq_med) if eq_med else None
            new = set(n2) - seen
            seen |= set(n2)
            years = [int(w.at[x, 'year']) for x in n2 if pd.notna(w.at[x, 'year'])]
            dens = sum(len(thesis_works.get(t, set()) & net2) for t in field_theses) / max(len(field_theses), 1)
            authors = {w.at[x, 'first_author_key'] for x in net2}
            summary.append({'field': field, 'cohort': coh, 'cohort_theses': n_coh, 'seed_citers': len(t0),
                            'seed_citers_pct': round(len(t0) / n_coh * 100, 1),
                            'network_works': len(net2), 'network_authors': len(authors), 'eq_network_works': round(eq_size, 1), 'eq_recent_works': round(eq_rec, 1), 'eq_median_pub_year': round(eq_year) if eq_year else None,
                            'field_theses': len(field_theses), 'field_theses_pct': round(len(field_theses) / n_coh * 100, 1),
                            'density': round(dens, 1), 'new_entrants': len(new),
                            'median_pub_year': int(pd.Series(years).median()) if years else None,
                            'pct_published_within_10y': round(sum(1 for y in years if mid - y <= 10) / len(years) * 100) if years else None})
            top_new = sorted(((n2[x][0], x) for x in new), reverse=True)[:8]
            print(f"{coh:<8} cohort {n_coh:>4}  seed citers {len(t0):>3} ({len(t0)/n_coh*100:4.1f}%)  network {len(net2)-len(seed_set):>3} works / {len(authors):>3} authors  "
                  f"eq15 size {eq_size:5.1f} recent {eq_rec:4.1f} median-year {round(eq_year) if eq_year else '-'}  new entrants {len(new):>3}")
            if top_new:
                print('         new: ' + ' | '.join(f'{label(x)} [{s}]' for s, x in top_new))
            for x, (s, lift) in n2.items():
                members.append({'field': field, 'cohort': coh, 'work_id': x, 'label': label(x), 'year': w.at[x, 'year'],
                                'support': s, 'lift': lift, 'new_entrant': x in new})
    pd.DataFrame(summary).to_csv(out / f'snowball-summary-{args.region.replace("+", "")}.csv', index=False)
    pd.DataFrame(members).to_csv(out / f'snowball-members-{args.region.replace("+", "")}.csv', index=False)
    print('done ->', out)


if __name__ == '__main__':
    main()
