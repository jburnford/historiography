"""AHA supervisors -> their PID keys through career facts on Wikidata (2026-11-02). Writes a proposal.

Many supervisors in the AHA genealogy sit on keys built from the AHA alone (`aha:<token>`, and
`aha-phd:<record>` when their own dissertation is linked), while the same historian is keyed from the canon
map, the atlas or the LC books route with an LC authority and a QID. Their dissertations were often published
under another title (George Mosse, Jonathan Spence), so the works route (key_aha_lc_books) cannot join them.

A supervisor key with no LC, QID or ORCID joins the key of a Wikidata item (or of an ORCID record, for a key
with an ORCID and no QID; the record's education and employment count with the item's P69 and P108) when:
- the key holds a QID whose label is name-compatible with the supervisor (surname equal, given names
  compatible: key_registry.names_compatible, and the given names agree as names, not just initials:
  lc_canon_people.given_agrees; Jane and Jack Censer both taught at George Mason), and it is the only such key whose item passes the checks below
  (an initial makes 'Spence, Jonathan' compatible with Joseph Spence; the career facts tell them apart);
- the item states the supervisor's career twice over: an educated-at (P69) institution agrees with the
  school of the supervisor's own AHA dissertation, and an employer (P108) agrees with a school where the
  supervisor's students took their doctorates (aha_links.school_agrees);
- the item's birth year, if any, puts the doctorate between ages 18 and 70 (Richard L. McCormick, born 1947,
  is not the author of the Pennsylvania dissertation of 1948);
- the two keys do not hold different AHA dissertations or different PIDs.
A supervisor without a linked dissertation of their own needs an employer for two of their students' schools.
Everything else is listed in `candidates.json` with the facts found (for review or a Sol check): one fact
only, or none (the item states no education or employer), or several candidate keys passing.

    python3 scripts/key_aha_career.py --out data/identifiers/aha-career-2026-11-02
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from aha_links import first_and_family, school_agrees
from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_aha import AHA
from key_registry import names_compatible
from lc_canon_people import given_agrees
from merge_guard import guarded
from review_atlas_qids import sparql

PUBLIC = ('lcnaf', 'wd', 'orcid')


def given(label):
    family, comma, rest = label.partition(', ')
    if comma:
        return rest
    return ' '.join(label.split()[:-1])


def same_person_name(a, b):
    """Compatible names whose given names agree as names, not initials alone ('Censer, Jane' is not
    'Censer, Jack'; both taught at George Mason, so the career facts cannot tell them apart)."""
    return names_compatible(a, b) and given_agrees(given(a), given(b)) and given_agrees(given(b), given(a))


def surname(label):
    f = first_and_family(label)
    return f[1] if f else label.lower()


def wikidata_facts(qids, cache):
    """QID -> dict(edu, emp: English labels of P69 / P108 values; birth: years)."""
    facts = defaultdict(lambda: dict(edu=set(), emp=set(), birth=set()))
    qids = sorted(qids)
    for i in range(0, len(qids), 100):
        part = qids[i:i + 100]
        query = """SELECT ?p ?prop ?l ?b WHERE { VALUES ?p { %s }
          { ?p wdt:P69 ?o . ?o rdfs:label ?l FILTER(lang(?l)='en') BIND('edu' AS ?prop) }
          UNION { ?p wdt:P108 ?o . ?o rdfs:label ?l FILTER(lang(?l)='en') BIND('emp' AS ?prop) }
          UNION { ?p wdt:P569 ?b BIND('birth' AS ?prop) } }""" % ' '.join('wd:' + q for q in part)
        name = 'career-' + '-'.join([part[0], part[-1], str(len(part))])
        for r in sparql(query, cache, name):
            f = facts[r['p']['value'].rsplit('/', 1)[-1]]
            if r['prop']['value'] == 'birth':
                if r['b']['value'][:4].isdigit():
                    f['birth'].add(int(r['b']['value'][:4]))
            elif 'l' in r:
                f[r['prop']['value']].add(r['l']['value'])
    return facts


def orcid_facts(orcid):
    """Education and employment organisations in the person's cached ORCID record (data/orcid-2026-09-21)."""
    path = ROOT / 'data/orcid-2026-09-21/records' / f'{orcid}.json'
    out = dict(edu=set(), emp=set(), birth=set())
    if not path.exists():
        return out
    acts = json.loads(path.read_text()).get('activities-summary') or {}
    for section, field in (('educations', 'edu'), ('employments', 'emp')):
        for g in (acts.get(section) or {}).get('affiliation-group', []):
            for summary in g.get('summaries', []):
                for v in summary.values():
                    if (v.get('organization') or {}).get('name'):
                        out[field].add(v['organization']['name'])
    return out


def assess(own, students, f):
    """Facts agreeing between the AHA records and a Wikidata item's career statements."""
    phd = sorted({r['department'] for r in own if any(school_agrees(r['department'], e) for e in f['edu'])})
    emp = sorted({r['department'] for r in students if any(school_agrees(r['department'], e) for e in f['emp'])})
    years = [int(r['year']) for r in own if (r['year'] or '').isdigit()]
    age_ok = not (years and f['birth']) or any(18 <= y - b <= 70 for y in years for b in f['birth'])
    joins = bool(age_ok and ((own and phd and emp) or (not own and len(emp) >= 2)))
    return dict(phd_school=phd, employer_schools=emp, age_ok=age_ok, has_edu=bool(f['edu']), has_emp=bool(f['emp'])), joins


def merge_rule(state):
    def ok(cluster, keys):
        anchors = set(cluster['anchors']) | {a for k in keys for a in state.keys[k]['anchors']}
        if any(len({a for a in anchors if a.startswith(p + ':')}) > 1 for p in PUBLIC + ('aha-phd',)):
            return False
        labels = [state.keys[k]['label'] for k in keys]
        return all(names_compatible(a, b) for a in labels for b in labels)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/field-research/aha-career-2026-11-02/raw')
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    state = State.load(args.state)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    by_token = defaultdict(list)
    for r in records.values():
        for t in (r['advisor_ids'] or '').split(';'):
            if t.strip():
                by_token[t.strip()].append(r)
    live = {k for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    with_pid = defaultdict(list)                      # surname -> (key, QID, ORCID)
    for k in live:
        qs = [a[3:] for a in state.keys[k]['anchors'] if a.startswith('wd:')]
        os_ = [a[6:] for a in state.keys[k]['anchors'] if a.startswith('orcid:')]
        if len(qs) == 1 or (not qs and len(os_) == 1):
            with_pid[surname(state.keys[k]['label'])].append((k, qs[0] if qs else None, os_[0] if len(os_) == 1 else None))
    report, cands = Counter(), {}
    supervisors = {}
    for k in sorted(live, key=lambda k: int(k[2:])):
        anchors = state.keys[k]['anchors']
        tokens = [a[4:] for a in anchors if a.startswith('aha:')]
        if not tokens or any(a.split(':', 1)[0] in PUBLIC for a in anchors):
            continue
        students = [r for t in tokens for r in by_token.get(t, [])]
        if not students:
            continue
        report['supervisors_without_pid'] += 1
        own = [records[a[8:]] for a in anchors if a.startswith('aha-phd:') and a[8:] in records]
        cs = [(c, q, o) for c, q, o in with_pid.get(surname(state.keys[k]['label']), [])
              if c != k and same_person_name(state.keys[k]['label'], state.keys[c]['label'])]
        if cs:
            supervisors[k] = (own, students)
            cands[k] = cs
    facts = wikidata_facts({q for cs in cands.values() for _, q, _ in cs if q}, args.cache)
    orcid = {o: orcid_facts(o) for cs in cands.values() for _, _, o in cs if o}
    clusters, listed = [], []
    for k, cs in cands.items():
        own, students = supervisors[k]
        rows = []
        for c, q, o in cs:
            f = dict(edu=set(), emp=set(), birth=set())
            for part in (facts.get(q), orcid.get(o)):
                for field, vals in (part or {}).items():
                    f[field] |= vals
            found, joins = assess(own, students, f)
            rows.append(dict(key=c, label=state.keys[c]['label'], qid=q, orcid=o, joins=joins, **found))
        joining = [r for r in rows if r['joins']]
        entry = dict(key=k, label=state.keys[k]['label'], students=len(students),
                     own_dissertations=[dict(record=r['id'], school=r['department'], year=r['year']) for r in own], candidates=rows)
        if len(joining) > 1:
            report['several_candidate_keys_join'] += 1
            listed.append(dict(entry, outcome='several_candidate_keys_join'))
            continue
        if not joining:
            r = max(rows, key=lambda r: (bool(r['phd_school']) + bool(r['employer_schools']), r['age_ok']))
            kind = 'one_fact' if (r['phd_school'] or r['employer_schools']) and r['age_ok'] else \
                'age_disagrees' if not r['age_ok'] else 'no_fact_agrees' if r['has_edu'] or r['has_emp'] else 'item_states_no_career'
            report[kind] += 1
            listed.append(dict(entry, outcome=kind))
            continue
        r = joining[0]
        report['joins'] += 1
        why = [f'educated at {", ".join(r["phd_school"])}'] if r['phd_school'] else []
        why.append(f'employed where students took doctorates ({"; ".join(r["employer_schools"][:3])})')
        clusters.append(dict(type='person', label=state.keys[r['key']]['label'], anchors={f'wd:{r["qid"]}' if r['qid'] else f'orcid:{r["orcid"]}'} | state.keys[k]['anchors'],
                             members=set(), aliases=set(), resolution='established',
                             basis=f'AHA supervisor {state.keys[k]["label"]} is {"Wikidata " + r["qid"] if r["qid"] else "ORCID " + r["orcid"]}: {"; ".join(why)} '
                                   f'(Wikidata P69/P108 and the ORCID record\'s education and employment, against AHA records)'))
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    for o in [o for o in ops if o['event'] == 'merge']:     # an AHA-only survivor takes the PID key's fuller name
        into, gone = state.keys[o['into']], state.keys[o['key']]
        if not any(a.split(':', 1)[0] in PUBLIC for a in into['anchors']) and len(gone['label']) > len(into['label']):
            ops.append(dict(event='relabel', key=o['into'], label=gone['label'], basis='the name on the LC or Wikidata key it joined'))
    materialise(state, dict(basis='aha career', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="AHA supervisors joined to Wikidata-keyed historians by education and employer (P69, P108)", decided_by='build',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'candidates.json').write_text(json.dumps(listed, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
