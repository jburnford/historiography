#!/usr/bin/env python3
"""Test the atlas's family trends against Canadian History PhD citations (read-only on both).

The atlas's landing trends are each editorial family's share of the journal record per
five-year bin (``data/evidence-layer/generated/<series>/family_series.csv``). The journal
items are assigned to families through their journal's themes. This script applies the
same journal -> theme -> family assignment to the journal articles that History PhDs cite,
so both series answer "what share of the literature belongs to this family?": one for what
journals published, one for what dissertations drew on.

The test uses only years in which both heavyweight programmes (Toronto from 2009, York
from 2012) are in the corpus, and the atlas bins that overlap them (2010-14, 2015-19,
2020-24). For each family it compares the direction and size of change from the first to
the last bin, with bootstrap intervals over dissertations, and the rank agreement across
families (Spearman, permutation p). Robustness variants drop Toronto, give each university
equal weight within a bin, and keep only literature published in the fifteen years before
the dissertation.

A second measure counts the dissertations citing anyone on the atlas rosters of each
family's entries. A scholar table ranks the people History PhDs cite, 2009 onward, with
their atlas status (full entry, roster only, absent), for editorial review.

The Toronto and York windows make this a test of the Canadian sub-graph: run it with
``--country CA`` (see ``dissertation_scope.py``). It reads and writes the sub-graph's summary
directory, ``<out>/summary/countries/CA/``: ``atlas-trend-test.json``, ``atlas-trend-test.csv``
and ``scholars-for-atlas-review.csv``. Nothing here edits the atlas or the evidence layer.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import random
import re
import unicodedata

from dissertation_scope import add_scope_argument, check_country, in_scope, summary_dir

ROOT = Path(__file__).resolve().parents[1]
BINS = (2010, 2015, 2020)
EARLY, LATE = (2009, 2014), (2020, 2026)


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower().replace('&', ' and ')
    text = re.sub(r'[^a-z0-9]+', ' ', text).strip()
    return re.sub(r'^the ', '', text)


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b, perms=10000, seed=1):
    """Rank correlation with a two-sided permutation p-value."""
    if len(a) < 4:
        return None, None
    ra, rb = ranks(a), ranks(b)

    def corr(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y)
        sx = math.sqrt(sum((v - mx) ** 2 for v in x))
        sy = math.sqrt(sum((v - my) ** 2 for v in y))
        return sum((u - mx) * (v - my) for u, v in zip(x, y)) / (sx * sy) if sx and sy else 0.0
    rho = corr(ra, rb)
    rng = random.Random(seed)
    hits = 0
    rb2 = rb[:]
    for _ in range(perms):
        rng.shuffle(rb2)
        hits += abs(corr(ra, rb2)) >= abs(rho) - 1e-12
    return round(rho, 3), round((hits + 1) / (perms + 1), 4)


def load_families(series_dir):
    """Journal key -> families, through the journal's themes and the families' members (bridges included)."""
    members = defaultdict(set)
    with (ROOT / 'data/evidence-layer/families-draft.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['status'] == 'rejected':
                continue
            members[r['member']].add(r['family'])
            if r['bridge_family']:
                members[r['member']].add(r['bridge_family'])
    journal_fams, labels = {}, {}
    with (series_dir / 'journal_coverage.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            themes = json.loads(r['themes'].replace("'", '"')) if r['themes'] else []
            journal_fams[r['journal_key']] = {fam for t in themes for fam in members.get(t, ())}
            labels[r['journal_key']] = r['label']
    families = sorted({fam for fams in members.values() for fam in fams})
    return families, journal_fams, labels, members


def journal_index(labels):
    """Folded title or alias -> journal key; titles shared by two journals are dropped."""
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import evidence_inputs
    names = defaultdict(set)
    for j in evidence_inputs.selected_journals():
        for t in [j['label']] + j.get('aliases', []):
            if fold(t):
                names[fold(t)].add(j['journal_key'])
    for key, label in labels.items():
        names[fold(label)].add(key)
    return {t: next(iter(k)) for t, k in names.items() if len(k) == 1 and len(t) >= 4}  # 'Isis'


def atlas_series(series_dir, view):
    out = defaultdict(dict)
    with (series_dir / 'family_series.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['view'] == view and int(r['bin']) in BINS:
                out[r['family']][int(r['bin'])] = int(r['items']) / int(r['total'])
    return out


def bin_of(year):
    return next((b for b in BINS if b <= year < b + 5), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--series', default='v18', help='evidence-layer series version')
    parser.add_argument('--first-year', type=int, default=2009)
    parser.add_argument('--last-year', type=int, default=2026)
    parser.add_argument('--min-articles', type=int, default=3, help='dissertations citing fewer catalogue-journal articles are left out of shares')
    parser.add_argument('--recent-window', type=int, default=15, help='years before the dissertation for the recent-literature variant')
    parser.add_argument('--boot', type=int, default=2000)
    parser.add_argument('--scholars', type=int, default=250)
    add_scope_argument(parser)
    args = parser.parse_args()
    series_dir = ROOT / 'data/evidence-layer/generated' / args.series
    summary = summary_dir(args.out, args.country)
    g = json.loads((args.out / 'graph.json').read_text())
    check_country(g, args.country)
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k: n for k, n in nodes.items() if in_scope(n, args.country)
            and n['year'] and args.first_year <= n['year'] <= args.last_year}
    families, journal_fams, labels, members = load_families(series_dir)
    index = journal_index(labels)

    work_journal = {}
    for k, n in nodes.items():
        if n['type'] == 'Work' and n.get('container'):
            j = index.get(fold(n['container']))
            if j:
                work_journal[k] = j
    cites, authored = defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            cites[e['source']].add(e['target'])
        elif e['type'] == 'AUTHORED':
            authored[e['source']].add(e['target'])

    # Per dissertation: catalogue-journal articles cited, and their families.
    profile = {}
    for d, n in diss.items():
        for variant in ('all', 'recent'):
            arts = [w for w in cites[d] if w in work_journal and (variant == 'all' or (
                nodes[w].get('year') and n['year'] - args.recent_window <= nodes[w]['year'] <= n['year']))]
            fam = Counter(f for w in arts for f in journal_fams.get(work_journal[w], ()))
            profile[(d, variant)] = (len(arts), fam)

    # Roster engagement: atlas entries' representative people -> graph persons (crosswalk candidates).
    atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    xw = {}
    with (summary / 'atlas-people-crosswalk.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['graph_person']:
                xw[r['atlas_person']] = (r['graph_person'], r['basis'])
    roster = defaultdict(set)
    person_entries = defaultdict(set)
    for node in atlas['nodes']:
        for p in node.get('representative_people') or []:
            person_entries[p['person_id']].add(node['id'])
            for fam in members.get(node['id'], ()):
                if p['person_id'] in xw:
                    roster[fam].add(xw[p['person_id']][0])
    person_works = {p: authored[p] for ps in roster.values() for p in ps}
    engages = {d: {fam for fam, ps in roster.items() if any(person_works[p] & cites[d] for p in ps)} for d in diss}

    def share(ds, fam, variant, weight):
        rows = [(profile[(d, variant)], weight(d)) for d in ds]
        rows = [((n_, c), w) for (n_, c), w in rows if n_ >= args.min_articles]
        tot = sum(w for _, w in rows)
        return sum(w * c[fam] / n_ for (n_, c), w in rows) / tot if tot else None

    def engage_share(ds, fam, weight):
        tot = sum(weight(d) for d in ds)
        return sum(weight(d) for d in ds if fam in engages[d]) / tot if tot else None

    by_bin = defaultdict(list)
    for d, n in diss.items():
        b = bin_of(n['year'])
        if b:
            by_bin[b].append(d)

    def variants():
        inst_count = {b: Counter(diss[d]['institution'] for d in ds) for b, ds in by_bin.items()}
        yield 'main', lambda ds: ds, lambda d: 1.0, 'all'
        yield 'without_toronto', lambda ds: [d for d in ds if diss[d]['institution'] != 'toronto'], lambda d: 1.0, 'all'
        yield 'universities_equal', lambda ds: ds, lambda d: 1.0 / inst_count[bin_of(diss[d]['year'])][diss[d]['institution']], 'all'
        yield 'recent_literature', lambda ds: ds, lambda d: 1.0, 'recent'

    rng = random.Random(20261012)
    atlas_views = {v: atlas_series(series_dir, v) for v in ('established', 'all')}
    results, rows_out = {}, []
    for name, select, weight, lit in variants():
        res = {'families': {}, 'dissertations_per_bin': {b: len(select(by_bin[b])) for b in BINS}}
        for fam in families:
            ser = {b: share(select(by_bin[b]), fam, lit, weight) for b in BINS}
            eng = {b: engage_share(select(by_bin[b]), fam, weight) for b in BINS} if fam in roster else None
            boots = []
            first, last = select(by_bin[BINS[0]]), select(by_bin[BINS[-1]])
            for _ in range(args.boot if name == 'main' else args.boot // 4):
                s0 = share([rng.choice(first) for _ in first], fam, lit, weight)
                s1 = share([rng.choice(last) for _ in last], fam, lit, weight)
                if s0 and s1:
                    boots.append(math.log(s1 / s0))
            boots.sort()
            change = math.log(ser[BINS[-1]] / ser[BINS[0]]) if ser[BINS[0]] and ser[BINS[-1]] else None
            ci = (boots[int(len(boots) * 0.025)], boots[int(len(boots) * 0.975) - 1]) if len(boots) > 40 else (None, None)
            fam_res = dict(dissertation_share=ser, dissertation_log_change=change, dissertation_log_change_ci95=ci,
                           roster_engagement=eng)
            for view, aser in atlas_views.items():
                a = aser.get(fam, {})
                a_change = math.log(a[BINS[-1]] / a[BINS[0]]) if a.get(BINS[0]) and a.get(BINS[-1]) else None
                if a_change is None or change is None or ci[0] is None:
                    verdict = 'no_data'
                elif abs(a_change) < 0.1:
                    verdict = 'atlas_flat:' + ('consistent' if ci[0] <= 0 <= ci[1] or abs(change) < 0.1 else 'dissertations_move')
                elif ci[0] > 0 or ci[1] < 0:
                    verdict = 'agree' if (ci[0] > 0) == (a_change > 0) else 'disagree'
                else:
                    verdict = 'indeterminate'
                fam_res[view] = dict(atlas_share=a, atlas_log_change=a_change, verdict=verdict)
            res['families'][fam] = fam_res
            for b in BINS:
                rows_out.append([name, fam, b, ser[b], (eng or {}).get(b), atlas_views['established'].get(fam, {}).get(b),
                                 atlas_views['all'].get(fam, {}).get(b)])
        for view in atlas_views:
            fams = [f for f in families if res['families'][f][view]['atlas_log_change'] is not None
                    and res['families'][f]['dissertation_log_change'] is not None]
            res[f'spearman_change_{view}'] = dict(zip(('rho', 'p'), spearman(
                [res['families'][f][view]['atlas_log_change'] for f in fams], [res['families'][f]['dissertation_log_change'] for f in fams])), families=len(fams))
            res[f'spearman_level_{view}'] = {b: dict(zip(('rho', 'p'), spearman(
                [atlas_views[view].get(f, {}).get(b, 0) for f in families], [res['families'][f]['dissertation_share'][b] or 0 for f in families])))
                for b in BINS}
            res[f'verdicts_{view}'] = dict(Counter(res['families'][f][view]['verdict'].split(':')[0] for f in families))
        results[name] = res

    # Coverage of the bridge itself.
    cited_articles = sum(1 for d in diss for w in cites[d] if nodes[w]['kind'] == 'article')
    matched = sum(1 for d in diss for w in cites[d] if w in work_journal)
    tagged = sum(1 for d in diss for w in cites[d] if w in work_journal and journal_fams.get(work_journal[w]))
    top_journals = Counter(labels.get(work_journal[w], work_journal[w]) for d in diss for w in cites[d] if w in work_journal)
    unmatched = Counter(nodes[w]['container'] for d in diss for w in cites[d] if nodes[w]['kind'] == 'article'
                        and w not in work_journal and nodes[w].get('container'))

    # Scholars: History PhDs citing each person, first-bin vs last-bin share, atlas status.
    graph_to_atlas = {v[0]: (k, v[1]) for k, v in xw.items()}
    full = {p['id'] for p in atlas['people'] if p.get('node_id')}
    in_people = {p['id'] for p in atlas['people']}
    views = json.loads((summary / 'views.json').read_text())
    field_label = {f['id']: f['label'] for f in views['fields']['fields']}
    work_field = {n['id']: field_label.get(n['field']) for n in views['fields']['nodes'] if n.get('field') is not None}
    early = [d for d in diss if EARLY[0] <= diss[d]['year'] <= EARLY[1]]
    late = [d for d in diss if LATE[0] <= diss[d]['year'] <= LATE[1]]
    scholars = []
    for p, works in authored.items():
        name = nodes[p].get('name') or ''
        if not p.startswith('P:') or not re.match(r"^[^,]{2,}, [A-ZÀ-Ý]", name) or re.match(r'(?i)(anonymous|canada|al)\b', name):
            continue  # inverted personal names only: no corporate authors or co-author fragments
        citing = {d for d in diss if cites[d] & works}
        if len(citing) < 15:
            continue
        a = graph_to_atlas.get(p)
        status = 'full_entry' if a and a[0] in full else 'roster_only' if a and a[0] in in_people else 'not_in_atlas'
        fields = Counter(work_field[w] for w in works if work_field.get(w))
        e_share = sum(1 for d in early if d in citing) / len(early)
        l_share = sum(1 for d in late if d in citing) / len(late)
        scholars.append(dict(person=p, name=nodes[p].get('name'), qid=nodes[p].get('qid') or '', history_phds_citing=len(citing),
                             share=round(len(citing) / len(diss), 4), universities=len({diss[d]['institution'] for d in citing}),
                             share_2009_14=round(e_share, 4), share_2020_26=round(l_share, 4),
                             trend='rising' if l_share > e_share * 1.25 else 'falling' if l_share < e_share * 0.8 else 'steady',
                             cocitation_field=fields.most_common(1)[0][0] if fields else '',
                             atlas_status=status, atlas_person=a[0] if a else '', atlas_match_basis=a[1] if a else '',
                             atlas_roster_entries='; '.join(sorted(person_entries.get(a[0], ()))) if a else ''))
    scholars.sort(key=lambda s: -s['history_phds_citing'])
    with (summary / 'scholars-for-atlas-review.csv').open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(scholars[0]))
        wr.writeheader()
        wr.writerows(scholars[:args.scholars])
    with (summary / 'atlas-trend-test.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['variant', 'family', 'bin', 'dissertation_share', 'roster_engagement', 'atlas_share_established', 'atlas_share_all'])
        wr.writerows([[a, b, c] + [round(x, 4) if isinstance(x, float) else x for x in rest] for a, b, c, *rest in rows_out])
    full_entry_people = sorted(({'atlas_person': k, 'history_phds_citing': len({d for d in diss if cites[d] & authored[v[0]]})}
                                for k, v in xw.items() if k in full), key=lambda r: -r['history_phds_citing'])
    report = dict(description=__doc__.split('\n\n')[0], period=[args.first_year, args.last_year], bins=list(BINS),
                  dissertations=len(diss), by_university=dict(Counter(n['institution'] for n in diss.values()).most_common()),
                  bridge=dict(cited_articles=cited_articles, matched_to_catalogue_journals=matched, in_family_journals=tagged,
                              top_matched_journals=top_journals.most_common(25), top_unmatched_containers=unmatched.most_common(40)),
                  roster_people_matched={f: len(ps) for f, ps in roster.items()},
                  variants=results, full_entry_people=full_entry_people,
                  caveats=['Dissertation years are repository issued dates.',
                           'Journal families come from journal-level themes; general and national journals (CHR, AHR) carry no family, as in the atlas series.',
                           'Dissertations cite literature published over decades; the recent-literature variant limits the lag.',
                           'Atlas-person matches by surname and first name are candidates, not identities.'])
    (summary / 'atlas-trend-test.json').write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    m = results['main']
    print(json.dumps(dict(dissertations=len(diss), per_bin=m['dissertations_per_bin'], bridge=report['bridge']['matched_to_catalogue_journals'],
                          verdicts=m['verdicts_established'], spearman=m['spearman_change_established']), default=str))


if __name__ == '__main__':
    main()
