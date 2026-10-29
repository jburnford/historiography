#!/usr/bin/env python3
"""Post-stratification weights for a country's History PhDs against the AHA directory.

The US corpus over-represents open-repository universities. Each strict US History PhD from
SINCE onward gets a weight so that, within each decade, institutions count in proportion to
their completed History PhDs in the AHA directory, and the decades in proportion to AHA's
national totals. Weights are trimmed at TRIM times the median and scaled to a mean of 1.

Only SINCE onward is weighted. Before 2010 the US holdings cover 5-12% of each decade's AHA
output and one or two universities supply most of it (Michigan 40-80% of the 1950s-70s), so
weighting would only magnify them; ``decade_coverage()`` reports this per decade.

Weighting cannot restore programmes with no holdings (Columbia, Chicago, Princeton…):
``coverage()`` reports them. Run directly for a summary:

    python3 scripts/dissertation_weights.py
"""
import csv
import gzip
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.csv'
TRIM = 10
SINCE = 2010
CANADIAN = re.compile(r"Toronto|Queen's Univ|York Univ|McGill|British Columbia|Laval|Montreal|Ottawa|McMaster|"
                      r"Western Ontario|Alberta|Manitoba|Saskatchewan|Calgary|Dalhousie|Carleton|Concordia|"
                      r"Waterloo|Guelph|Simon Fraser|Victoria|Memorial Univ|New Brunswick|Laurier|Sherbrooke|"
                      r"Quebec|Royal Military|Trent")
# Collection slug -> exact AHA department name. History-of-science programmes are separate AHA
# departments and are not mapped. Unmapped slugs (BASE records) get their period's mean weight.
DEPARTMENT = {
    'alabama': 'Univ. of Alabama, Tuscaloosa, Dept. of History',
    'arkansas': 'Univ. of Arkansas, Fayetteville, Dept. of History',
    'duke': 'Duke Univ., Dept. of History',
    'florida': 'Univ. of Florida, Dept. of History',
    'harvard': 'Harvard Univ., Dept. of History',
    'johnshopkins': 'Johns Hopkins Univ., Dept. of History',
    'kentucky': 'Univ. of Kentucky, Dept. of History',
    'lsu': 'Louisiana State Univ., Baton Rouge, Dept. of History',
    'maryland': 'Univ. of Maryland, Coll. Park, Dept. of History',
    'michigan': 'Univ. of Michigan, Ann Arbor, Dept. of History',
    'minnesota': 'Univ. of Minnesota, Twin Cities, Dept. of History',
    'nebraska': 'Univ. of Nebraska, Lincoln, Dept. of History',
    'newmexico': 'Univ. of New Mexico, Dept. of History',
    'oklahoma': 'Univ. of Oklahoma, Dept. of History',
    'penn': 'Univ. of Pennsylvania, Dept. of History',
    'rice': 'Rice Univ., Dept. of History',
    'smu': 'Southern Methodist Univ., William P. Clements Dept. of History',
    'southcarolina': 'Univ. of South Carolina, Columbia, Dept. of History',
    'stanford': 'Stanford Univ., Dept. of History',
    'tennessee': 'Univ. of Tennessee, Knoxville, Dept. of History',
    'unc': 'Univ. of North Carolina, Chapel Hill, Dept. of History',
    'vanderbilt': 'Vanderbilt Univ., Dept. of History',
    'virginia': 'Univ. of Virginia, Corcoran Dept. of History',
    'washington': 'Univ. of Washington, Seattle, Dept. of History',
    'wisconsinmadison': 'Univ. of Wisconsin, Madison, Dept. of History',
    'yale': 'Yale Univ., Dept. of History',
    'ucberkeley': 'Univ. of California, Berkeley, Dept. of History',
    'ucdavis': 'Univ. of California, Davis, Dept. of History',
    'ucirvine': 'Univ. of California, Irvine, Dept. of History',
    'ucla': 'Univ. of California, Los Angeles, Meyer and Renee Luskin Dept. of History',
    'ucriverside': 'Univ. of California, Riverside, Dept. of History',
    'ucsd': 'Univ. of California, San Diego, Dept. of History',
    'ucsb': 'Univ. of California, Santa Barbara, Dept. of History',
    'ucsantacruz': 'Univ. of California, Santa Cruz, Dept. of History',
}


def period(year):
    return 1950 if year < 1960 else year // 10 * 10


def load_aha(path=AHA):
    """Completed US History PhDs in the AHA directory: list of (orgcd, department, year)."""
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8')):
        if r['status'] == 'completed' and r['year'].isdigit() and not CANADIAN.search(r['department']):
            out.append((r['orgcd'], r['department'], int(r['year'])))
    return out


def resolve(aha):
    """slug -> orgcd, and orgcd -> department name."""
    names = {}
    for org, dept, _ in aha:
        names.setdefault(org, dept)
    by_name = {d: o for o, d in names.items()}
    missing = sorted(d for d in DEPARTMENT.values() if d not in by_name)
    if missing:
        raise KeyError(f'AHA departments not found: {missing}')
    return {slug: by_name[d] for slug, d in DEPARTMENT.items()}, names


def weights(dissertations, aha=None, since=SINCE):
    """dissertations: iterable of (id, institution slug, year or None).

    Returns (weights, report). Only PhDs from ``since`` onward get a weight; earlier and
    undated ones are left out (see ``decade_coverage`` for why).
    """
    aha = aha or load_aha()
    mapping, names = resolve(aha)
    rows = [r for r in dissertations if r[2] and r[2] >= since]
    sample = Counter((mapping.get(s), period(y)) for _, s, y in rows if s in mapping)
    pop = Counter((o, period(y)) for o, _, y in aha if y >= since)
    national = Counter(period(y) for _, _, y in aha if y >= since)
    w = {}
    for d, s, y in rows:
        cell = (mapping.get(s), period(y))
        w[d] = pop[cell] / sample[cell] if cell in sample and pop.get(cell) else None
    # Unmatched rows (unmapped slugs, cells AHA lacks) take their period's mean weight; each
    # period is then scaled to its share of the AHA national total in the window.
    by_period = defaultdict(list)
    for d, s, y in rows:
        by_period[period(y)].append(d)
    for p, ids in by_period.items():
        known = [w[d] for d in ids if w[d] is not None]
        fill = (sum(known) / len(known)) if known else 1.0
        for d in ids:
            if w[d] is None:
                w[d] = fill
        scale = national[p] / sum(w[d] for d in ids)
        for d in ids:
            w[d] *= scale
    cap = TRIM * median(w.values())
    trimmed = sum(v > cap for v in w.values())
    w = {d: min(v, cap) for d, v in w.items()}
    mean = sum(w.values()) / len(w)
    w = {d: v / mean for d, v in w.items()}
    n_eff = sum(w.values()) ** 2 / sum(v * v for v in w.values())
    by_inst = Counter()
    for d, s, _ in rows:
        by_inst[s] += w[d]
    report = dict(since=since, n=len(rows), n_eff=n_eff, trimmed=trimmed,
                  institutions=len({s for _, s, _ in rows}),
                  unmapped=sorted({s for _, s, _ in rows if s not in mapping}),
                  raw_institutions={s: n / len(rows) for s, n in Counter(s for _, s, _ in rows).most_common()},
                  weighted_institutions={s: v / len(rows) for s, v in by_inst.most_common()})
    return w, report


def decade_coverage(dissertations, aha=None):
    """Per period: our PhDs, institutions, share of AHA output at those institutions, largest one's share."""
    aha = aha or load_aha()
    mapping, _ = resolve(aha)
    national = Counter(period(y) for _, _, y in aha)
    out = []
    for p in sorted(national):
        ours = Counter(s for _, s, y in dissertations if y and period(y) == p)
        orgs = {mapping[s] for s in ours if s in mapping}
        covered = sum(1 for o, _, y in aha if period(y) == p and o in orgs)
        top = ours.most_common(1)[0] if ours else ('', 0)
        out.append(dict(period=p, n=sum(ours.values()), institutions=len(ours), aha=national[p],
                        aha_covered=covered / national[p], top=top[0],
                        top_share=top[1] / sum(ours.values()) if ours else 0))
    return out


def coverage(held_slugs, since=2000, top=20, aha=None):
    """Share of AHA US PhDs since ``since`` at held institutions, and the largest programmes with none."""
    aha = aha or load_aha()
    mapping, names = resolve(aha)
    held = {mapping[s] for s in held_slugs if s in mapping}
    recent = Counter(o for o, _, y in aha if y >= since)
    total = sum(recent.values())
    missing = [(names[o], n) for o, n in recent.most_common(top) if o not in held]
    return dict(since=since, share_held=sum(n for o, n in recent.items() if o in held) / total,
                held=len(held), institutions=len(recent), missing_top=missing, top=top)


def strict_rows(country, path=D / 'dissertations.csv'):
    out = []
    for r in csv.DictReader(open(path, newline='', encoding='utf-8')):
        if r.get('in_analysis') in ('True', 'true', '1') and (r.get('country') or 'CA') == country:
            y = int(r['year']) if (r.get('year') or '').isdigit() else None
            out.append((r['id'], r['institution'], y))
    return out


def citation_files():
    """Per-dissertation links: the builder's strict files, else the newest public release."""
    if (D / 'strict-citations.csv.gz').exists():
        return D / 'strict-citations.csv.gz', D / 'authored.csv.gz'
    releases = sorted((D / 'release').glob('*/citations.csv.gz'))
    if releases:
        return releases[-1], releases[-1].with_name('authorship.csv.gz')
    return None, None


def citing_sets(ids, citations, authorship):
    """work_id -> set of citing ids and person_key -> set of citing ids, limited to ``ids``."""
    by_work = defaultdict(set)
    with gzip.open(citations, 'rt', newline='') as f:
        for r in csv.DictReader(f):
            if r['dissertation_id'] in ids:
                by_work[r['work_id']].add(r['dissertation_id'])
    by_person = defaultdict(set)
    with gzip.open(authorship, 'rt', newline='') as f:
        for r in csv.DictReader(f):
            if r['work_id'] in by_work:
                by_person[r['person_key']] |= by_work[r['work_id']]
    return by_work, by_person


if __name__ == '__main__':
    rows = strict_rows('US')
    for c in decade_coverage(rows):
        print(f"  {c['period']}s: {c['n']:5} PhDs, {c['institutions']:2} institutions, "
              f"{c['aha_covered']:5.1%} of AHA output covered; largest {c['top']} {c['top_share']:.0%}")
    w, rep = weights(rows)
    print(f"weighted window {rep['since']}-: {rep['n']} PhDs, effective n {rep['n_eff']:.0f}, "
          f"trimmed {rep['trimmed']}, unmapped {rep['unmapped']}")
    for s, v in list(rep['raw_institutions'].items())[:12]:
        print(f"  {s:18} raw {v:5.1%}  weighted {rep['weighted_institutions'][s]:5.1%}")
    cov = coverage({s for _, s, _ in rows})
    print(f"held institutions award {cov['share_held']:.0%} of AHA US PhDs since {cov['since']}; "
          f"top-{cov['top']} with none: {'; '.join(n for n, _ in cov['missing_top'])}")
