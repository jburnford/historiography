"""UK staff lists -> person keys: the IHR's 'Teachers of History in the Universities of the UK' (2026-11-06).

The IHR listed the people teaching history in UK universities in its annual 'Teachers of History' (Wayback copies
of the 2002-2004 editions; data/field-research/historian-positions-2026-10-29, source 'ihr'). Each listing
names a person and an institution. A listing joins a person key when:
- the names agree (same family name, compatible given names, first given names agreeing beyond an initial:
  namesake_check_groups.names_agree_strict; 'Ben Shepherd' is not 'Gillian B. Shepherd');
- the key's own record places the person at the same institution: an affiliation printed on one of its review
  credits (`review-credit:<name>|<affiliation>`), or an employment on its ORCID record that is not over before
  1998 or begun after 2006 (cached records, data/orcid-2026-09-21/records and the 2026-10-29 ORCID employment
  harvest). The name alone never joins (user, 2026-10-31: identity by works and facts, not names);
- institutions agree on their distinctive words after dropping generic ones ('University', 'Department of
  History'); a word that names another institution (Liverpool Hope, Oxford Brookes, Manchester Metropolitan,
  Sheffield Hallam, Canterbury Christ Church) blocks the join, and 'London' or 'Wales' alone never agrees.
The listing becomes an anchor `ihr:<surname|given|institution>` on the key: a historian signal (taught history
at a UK university, 2002-04) and a dated career fact for later merges. When several keys of that name each
place the person at the listed institution, they are one person and merge (Helen Meller's two Nottingham
review-credit keys), unless two different PIDs of one kind would meet or merge_guard holds a key.
Listings with no agreeing key are left for other career sources (JSTOR review signatures, H-Soz-Kult credits).

    python3 scripts/key_ihr_staff.py --out data/identifiers/ihr-staff-2026-11-06
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'data/field-research/historian-affiliations-2026-10-29'))
from identifiers import DEFAULT_DIR, State, materialise, plan  # noqa: E402
from key_review_reviewers import family  # noqa: E402
from merge_guard import guarded  # noqa: E402
from namesake_check_groups import given_words, names_agree_strict as given_names_agree  # noqa: E402
from orcid_ground import inst_tokens  # noqa: E402

POSITIONS = ROOT / 'data/field-research/historian-positions-2026-10-29/positions.csv'
ORCID_RECORDS = ROOT / 'data/orcid-2026-09-21/records'
ORCID_EMPLOYMENT = ROOT / 'data/field-research/historian-affiliations-2026-10-29/raw/orcid-affiliations.jsonl'
PUBLIC = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'aha-phd', 'diss-author')
GENERIC = {'dept', 'department', 'school', 'history', 'historical', 'division', 'faculty', 'centre', 'center',
           'studies', 'modern', 'humanities', 'arts', 'social', 'sciences', 'institute', 'unit', 'programme',
           'program', 'professor', 'lecturer', 'reader', 'senior', 'emeritus', 'research', 'fellow', 'and', 'of',
           'england', 'uk', 'united', 'kingdom', 'great', 'britain', 'gb', 'scotland', 'wales', 'northern', 'ireland'}
OTHER_PLACE = {'hope', 'brookes', 'metropolitan', 'hallam', 'moores', 'john', 'christ', 'church', 'spa', 'polytechnic',
               'ruskin', 'anglia', 'central', 'northumbria', 'west', 'east', 'north', 'south', 'city', 'new', 'trent',
               'saint', 'st', 'mary', 'marys', 'martin', 'martins', 'royal', 'holloway', 'queen', 'queens', 'kings',
               'birkbeck', 'goldsmiths', 'economics', 'oriental', 'african', 'slavonic', 'courtauld', 'guildhall',
               'education', 'open', 'beckett', 'napier', 'caledonian', 'heriot', 'watt', 'margaret', 'robert', 'gordon'}
WEAK = {'london', 'wales'}
NOT_PEOPLE = {'christ church', 'all souls', 'corpus christi'}     # IHR Oxford/Cambridge page headings read as names


def inst(s):
    return frozenset(inst_tokens(s) - GENERIC) or frozenset(t for t in inst_tokens(s) if t in WEAK)


def agree(a, b):
    ta, tb = inst(a), inst(b)
    if not ta or not tb or ta <= WEAK or tb <= WEAK:
        return bool(ta) and ta == tb and not ta <= WEAK
    if ta == tb:
        return True
    small, big = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    return small < big and not ((big - small) & OTHER_PLACE)


def orcid_employment():
    emp = defaultdict(list)
    for p in ORCID_RECORDS.glob('*.json'):
        d = json.loads(p.read_text())
        for g in ((d.get('activities-summary') or {}).get('employments') or {}).get('affiliation-group') or []:
            for s in g.get('summaries', []):
                e = s.get('employment-summary') or {}
                name = (e.get('organization') or {}).get('name')
                year = lambda f: (((e.get(f) or {}).get('year') or {}).get('value'))
                if name:
                    emp[p.stem].append((name, year('start-date'), year('end-date')))
    with ORCID_EMPLOYMENT.open() as f:
        for line in f:
            r = json.loads(line)
            if r['orcid'] not in emp:
                emp[r['orcid']] = [(e['organization'], e['start'], e['end']) for e in r['employment']]
    return emp


def in_window(start, end):
    num = lambda v: int(v) if v and str(v).isdigit() else None
    return not ((num(end) or 9999) < 1998 or (num(start) or 0) > 2006)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    emp = orcid_employment()
    by_family = defaultdict(list)
    for k, rec in state.keys.items():
        if rec['type'] == 'person' and rec['status'] in ('active', 'provisional') and given_words(rec['label'] or ''):
            by_family[family(rec['label'])].append(k)
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    listings = db.execute(f"""SELECT person_ref, any_value(name), list(DISTINCT institution), min(observed_year), max(observed_year)
        FROM read_csv_auto('{POSITIONS}', all_varchar=true) WHERE source = 'ihr' GROUP BY 1 ORDER BY 1""").fetchall()
    report, clusters, sample, open_items, found = Counter(), [], [], [], []
    for ref, name, insts, y0, y1 in listings:
        anchor = ref if ref.startswith('ihr:') else 'ihr:' + ref
        if anchor in state.anchor:
            report['already_keyed'] += 1
            continue
        if name.lower().strip() in NOT_PEOPLE:
            report['not_a_person'] += 1
            continue
        cands = [k for k in by_family.get(family(name), []) if given_names_agree(name, state.keys[k]['label'])]
        if not cands:
            report['no_key_of_that_name'] += 1
            continue
        joining = {}
        for k in cands:
            facts = []
            for a in sorted(state.keys[k]['anchors']):
                if a.startswith('review-credit:') and '|' in a:
                    aff = a.split('|', 1)[1]
                    if any(agree(i, aff) for i in insts):
                        facts.append(f'review credit printed at {aff}')
                elif a.startswith('orcid:'):
                    for org, s, e in emp.get(a[6:], []):
                        if in_window(s, e) and any(agree(i, org) for i in insts):
                            facts.append(f'ORCID employment at {org} ({s or "?"}-{e or ""})')
            if facts:
                joining[k] = sorted(set(facts))
        if not joining:
            report['name_only_no_institution_fact'] += 1
            if len(open_items) < 5000:
                open_items.append(dict(listing=anchor, name=name, institutions=insts, candidates=cands[:10]))
            continue
        report['joins'] += 1
        if len(joining) > 1:
            report['joins_several_keys'] += 1
        found.append((anchor, name, insts, y0, y1, joining))
    # a key reached by listings whose names disagree ('H. S. Jones' by H. Stuart Jones and Sian Jones) is ambiguous
    reach = defaultdict(set)
    for _, name, _, _, _, joining in found:
        for k in joining:
            reach[k].add(name)
    ambiguous = {k for k, names in reach.items() if any(not given_names_agree(a, b) for a in names for b in names)}
    report['ambiguous_keys_dropped'] = len(ambiguous)
    kept = []
    for f in found:
        j = {k: v for k, v in f[5].items() if k not in ambiguous}
        if j:
            kept.append(f[:5] + (j,))
        else:
            report['listings_left_ambiguous'] += 1
            open_items.append(dict(listing=f[0], name=f[1], institutions=f[2], candidates=sorted(f[5]), outcome='ambiguous'))
    found = kept
    # listings that reach the same key are one person (IHR's 2004 edition rewords departments: 'Glasgow' and
    # 'Dept. of Economic & Social History University of Glasgow'; a move between institutions also lists twice)
    parent = list(range(len(found)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first = {}
    for i, (*_, joining) in enumerate(found):
        for k in joining:
            parent[root(i)] = root(first.setdefault(k, i))
    groups = defaultdict(list)
    for i in range(len(found)):
        groups[root(i)].append(found[i])
    for group in groups.values():
        joining = defaultdict(set)
        for *_, j in group:
            for k, facts in j.items():
                joining[k].update(facts)
        ks = sorted(joining, key=lambda k: int(k.split('-')[1]))
        report['people'] += 1
        report['people_several_keys'] += len(ks) > 1
        listed = '; '.join(f'{name} at {" / ".join(insts[:2])} ({y0}{"-" + y1 if y1 != y0 else ""})'
                           for _, name, insts, y0, y1, _ in group)
        why = '; '.join(f'{k}: {", ".join(sorted(joining[k])[:2])}' for k in ks)
        clusters.append(dict(type='person', label=state.keys[ks[0]]['label'],
                             anchors={g[0] for g in group} | {min(state.keys[k]['anchors']) for k in ks},
                             members=set(), aliases=set(), resolution='recorded',
                             basis=f'IHR Teachers of History lists {listed}; the key places them there too ({why})'))
        if len(sample) < 80:
            sample.append(dict(listings=[g[0] for g in group], name=group[0][1], institutions=group[0][2],
                               keys={k: state.keys[k]['label'] for k in ks}, facts={k: sorted(v) for k, v in joining.items()}))

    def merge_ok(cluster, keys):
        anchors = {a for k in keys for a in state.keys[k]['anchors']}
        return not any(len({a for a in anchors if a.startswith(p + ':')}) > 1 for p in PUBLIC)
    ops, assign, held = plan(state, clusters, guarded(state, merge_ok, exclude=args.out))
    materialise(state, dict(basis='ihr staff', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="IHR Teachers of History listings (2002-04) joined to keys placed at the same institution", decided_by='rule',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'open.json').write_text(json.dumps(open_items, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(listings=len(listings), **dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
