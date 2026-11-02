"""AHA supervisors -> their PID keys through career facts on Wikidata (2026-11-02). Writes a proposal.

Many supervisors in the AHA genealogy sit on keys built from the AHA alone (`aha:<token>`, and
`aha-phd:<record>` when their own dissertation is linked), while the same historian is keyed from the canon
map, the atlas or the LC books route with an LC authority and a QID. Their dissertations were often published
under another title (George Mosse, Jonathan Spence), so the works route (key_aha_lc_books) cannot join them.

A supervisor key with no LC, QID or ORCID joins a key holding a QID, an ORCID or an LC authority. The career
statements of all three count together: Wikidata's P69/P108, the ORCID record's education and employment, and
LC's own notes (scripts/lc_notes_index.py: 670 data found speaking of a doctorate or of teaching, 373
affiliations). A supervisor with no such key may take an LC authority of that name that no key holds yet, on
LC's notes alone. The join needs:
- names that agree (surname equal, given names compatible: key_registry.names_compatible), with the given names
  agreeing as names, not initials alone (lc_canon_people.given_agrees; Jane and Jack Censer both taught at
  George Mason); and only one candidate passing the checks below (an initial makes 'Spence, Jonathan'
  compatible with Joseph Spence; the career facts tell them apart);
- the career stated twice over: an education agrees with the school of the supervisor's own AHA dissertation,
  (or the PhD school the AHA directory lists for them), and an employer agrees with a school where the
  supervisor's students took their doctorates (aha_links.school_agrees);
- a birth year, if any, that puts the doctorate between ages 18 and 70 (Richard L. McCormick, born 1947, is not
  the author of the Pennsylvania dissertation of 1948);
- no two different AHA dissertations or PIDs of one kind on the joined keys. When several candidate keys
  pass, each on its own facts, they are one person and all join (Michael Gauvreau's ORCID key and his
  LC/Wikidata key).
A supervisor without a linked dissertation of their own needs an employer for two of their students' schools.
Everything else is listed in `candidates.json` with the facts found (for review or a Sol check): one fact
only, or none (the item states no education or employer), or several candidate keys passing.

    python3 scripts/key_aha_career.py --out data/identifiers/aha-career-2026-11-02
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from aha_links import first_and_family, school_agrees
from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_aha import AHA, DIRECTORY
from key_lc_books import label_of
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


DOCTORATE = re.compile(r'ph\.?\s?d\b|d\.?\s?phil|doctora|thesis|\bdiss\b|dissertation', re.I)
JOB = re.compile(r'prof|lectur|faculty|taught|teach|instructor|\bchair', re.I)


def lc_facts(lcids, lc_dir):
    """LC id -> dict(edu, emp, birth) from LC's own records: the clauses of the 670 data found (and of the
    cited source) that speak of a doctorate are education ('Thesis (Ph. D.)--Yale University'); 373
    affiliations and clauses that speak of teaching are employment ('was Sterling Professor of History at Yale
    University from 1993 to 2008'); the 046 birth year."""
    out = {l: dict(edu=set(), emp=set(), birth=set()) for l in lcids}
    if not lcids:
        return out
    db = duckdb.connect()
    db.execute('CREATE TABLE want(lcid VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(l,) for l in lcids])
    orgs = {}
    rows = db.execute(f"SELECT lcid, notes, affiliations FROM read_parquet('{lc_dir}/personal-notes.parquet') JOIN want USING (lcid)").fetchall()
    want_orgs = {a['org'] for _, _, affs in rows for a in affs or []}
    if want_orgs:
        db.execute('CREATE TABLE o(id VARCHAR)')
        db.executemany('INSERT INTO o VALUES (?)', [(x,) for x in want_orgs])
        orgs = dict(db.execute(f"SELECT id, label FROM read_parquet('{lc_dir}/organisations.parquet') JOIN o USING (id)").fetchall())
    for lcid, notes, affs in rows:
        f = out[lcid]
        for n in notes or []:
            for clause in re.split(r'[;()]', n.replace(' :: ', ';')):
                if DOCTORATE.search(clause):
                    f['edu'].add(clause.strip())
                elif JOB.search(clause):
                    f['emp'].add(clause.strip())
        f['emp'] |= {orgs[a['org']] for a in affs or [] if a['org'] in orgs}
    for lcid, birth in db.execute(f"SELECT lcid, birth FROM read_parquet('{lc_dir}/personal-names.parquet') JOIN want USING (lcid)").fetchall():
        if (birth or '')[:4].isdigit():
            out[lcid]['birth'].add(int(birth[:4]))
    return out


def lc_by_name(families, lc_dir, keyed):
    """Surname -> [(LC id, label)] for live, differentiated LC personal names not yet on any key."""
    db = duckdb.connect()
    db.execute('CREATE TABLE fam(f VARCHAR)')
    db.executemany('INSERT INTO fam VALUES (?)', [(f,) for f in families])
    out = defaultdict(list)
    for lcid, label in db.execute(f"""SELECT lcid, label FROM read_parquet('{lc_dir}/personal-names.parquet')
            WHERE NOT undifferentiated AND NOT deprecated
              AND regexp_replace(lower(strip_accents(split_part(label, ',', 1))), '[^a-z]+', ' ', 'g') IN (SELECT f FROM fam)""").fetchall():
        if lcid not in keyed:
            out[surname(label_of(label))].append((lcid, label_of(label)))
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
    ap.add_argument('--lc', type=Path, default=Path('/mnt/e/lc-authorities'), help='personal-names, personal-notes and organisations parquet')
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
    degree_school = defaultdict(set)                   # AHA token -> PhD schools the directory lists
    with DIRECTORY.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['degree_school'] and r['degree'].upper().replace('.', '') in ('PHD', 'DPHIL'):
                degree_school[r['token']].add(r['degree_school'])
    live = {k for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    with_pid = defaultdict(list)                      # surname -> (key, QID, ORCID, LC id)
    for k in live:
        qs = [a[3:] for a in state.keys[k]['anchors'] if a.startswith('wd:')]
        os_ = [a[6:] for a in state.keys[k]['anchors'] if a.startswith('orcid:')]
        ls = [a[6:] for a in state.keys[k]['anchors'] if a.startswith('lcnaf:')]
        if len(qs) <= 1 and len(os_) <= 1 and len(ls) <= 1 and (qs or os_ or ls):
            with_pid[surname(state.keys[k]['label'])].append((k, (qs or [None])[0], (os_ or [None])[0], (ls or [None])[0]))
    keyed_lc = {a[6:] for a in state.anchor if a.startswith('lcnaf:')}
    unmatched = {}
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
        own += [dict(id=f'directory:{t}', department=d, year='') for t in tokens for d in sorted(degree_school.get(t, ()))]
        cs = [(c, q, o, l) for c, q, o, l in with_pid.get(surname(state.keys[k]['label']), [])
              if c != k and same_person_name(state.keys[k]['label'], state.keys[c]['label'])]
        supervisors[k] = (own, students)
        if cs:
            cands[k] = cs
        else:
            unmatched[k] = surname(state.keys[k]['label'])
    # supervisors with no candidate key: LC authorities of that name not yet keyed, judged on LC's own notes
    lc_names = lc_by_name(set(unmatched.values()), args.lc, keyed_lc)
    for k, fam in unmatched.items():
        cs = [(None, None, None, l) for l, label in lc_names.get(fam, []) if same_person_name(state.keys[k]['label'], label)]
        if cs:
            cands[k] = cs
    lc_label = {l: label for v in lc_names.values() for l, label in v}
    facts = wikidata_facts({q for cs in cands.values() for _, q, _, _ in cs if q}, args.cache)
    orcid = {o: orcid_facts(o) for cs in cands.values() for _, _, o, _ in cs if o}
    lcf = lc_facts({l for cs in cands.values() for _, _, _, l in cs if l}, args.lc)
    clusters, listed = [], []
    for k, cs in cands.items():
        own, students = supervisors[k]
        rows = []
        for c, q, o, l in cs:
            f = dict(edu=set(), emp=set(), birth=set())
            for part in (facts.get(q), orcid.get(o), lcf.get(l)):
                for field, vals in (part or {}).items():
                    f[field] |= vals
            found, joins = assess(own, students, f)
            rows.append(dict(key=c, label=state.keys[c]['label'] if c else lc_label[l], qid=q, orcid=o, lcnaf=l, joins=joins, **found))
        joining = [r for r in rows if r['joins']]
        entry = dict(key=k, label=state.keys[k]['label'], students=len(students),
                     own_dissertations=[dict(record=r['id'], school=r['department'], year=r['year']) for r in own], candidates=rows)
        if len(joining) > 1 and not all(r['key'] for r in joining):
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
        if len(joining) > 1:        # each key passes on its own: they are one person, as the merge rule allows
            report['joins_several_keys'] += 1
        why = [f'educated at {", ".join(r["phd_school"])}'] if r['phd_school'] else []
        why.append(f'employed where students took doctorates ({"; ".join(r["employer_schools"][:3])})')
        pids = {f'wd:{x["qid"]}' if x['qid'] else f'orcid:{x["orcid"]}' if x['orcid'] else f'lcnaf:{x["lcnaf"]}' for x in joining}
        pid = ', '.join(sorted(pids))
        report['joins_' + sorted(pids)[0].split(':')[0] + ('_new' if not r['key'] else '')] += 1
        clusters.append(dict(type='person', label=state.keys[r['key']]['label'] if r['key'] else state.keys[k]['label'],
                             anchors=pids | state.keys[k]['anchors'], members=set(), aliases=set(), resolution='established',
                             basis=f'AHA supervisor {state.keys[k]["label"]} is {pid}: {"; ".join(why)} (career statements of '
                                   f'Wikidata P69/P108, the ORCID record and LC\'s 670/373 notes, against AHA records)'))
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
