"""AHA-only person keys -> LC authorities through LC's own notes (2026-11-02). Writes a proposal.

The split-key sweep. An AHA author or supervisor sits on a key built from the AHA alone (`aha-phd:<record>`,
`aha:<token>`), while the same historian is keyed elsewhere with an LC authority (canon map, atlas, LC books),
or has an LC authority no key holds yet. The works route (key_aha_lc_books) reads LC's bibliographic records;
this route reads the authority record's 670 notes, which often cite the dissertation itself ("His Fallen hero,
1992": Christopher Finan, Columbia 1992) or state the doctorate ("Ph. D., UCLA, 1990").

A key with no public PID joins one LC authority (keyed or not) on any of:
- **title**: a 670 cites the dissertation, or a book carrying its title: the cited title and the dissertation's
  main title share three or more content words making up 60% of the shorter, or are the same two words
  (key_aha's own_book rule), cited from two years before the PhD to fifteen after. Identity by works.
- **degree**: a 670 clause speaking of a doctorate names the AHA school and a year within one of the AHA year
  (user rule, 2026-11-01: "name year school should be unique").
- **school and employer**: a doctorate clause names the AHA school, and a clause speaking of teaching (or a 373
  affiliation) names the institution the AHA directory lists for them or a school where their students took
  doctorates.
And always:
- names that agree: same surname, given names agreeing as names both ways (nicknames allowed: 'Bill Waiser'
  is 'Waiser, William'); no single-initial pooled labels;
- an LC birth year, if any, putting the doctorate between ages 18 and 70;
- no doctorate clause naming another school (Casey: Princeton in the AHA, 'PhD at the University of Delaware'
  in LC). Such pairs are listed, not joined;
- exactly one candidate passing. Several, or one fact short, go to `candidates.json.gz`.
The merge (an AHA key into an LC-keyed key) goes through the merge guard and key_aha_career's merge rule (no
two different public PIDs or own dissertations of one kind on the joined keys).

    python3 scripts/key_aha_lc_notes.py --out data/identifiers/aha-lc-notes-2026-11-02
"""
import argparse
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from aha_links import school
from identifiers import DEFAULT_DIR, PUBLIC_SCHEMES, State, materialise, plan
from key_aha import AHA, DIRECTORY
from key_aha_career import given, merge_rule, same_person_name, surname
from key_lc_books import label_of
from lc_canon_people import NICKNAMES, content, given_agrees, initials_only, words
from merge_guard import guarded

DOCTORATE = re.compile(r'ph\.?\s?d\b|d\.?\s?phil|doctora|doctor of philosophy|thesis|dissertation', re.I)
JOB = re.compile(r'prof|lectur|faculty|taught|teach|instructor|\bchair|fellow', re.I)
INSTITUTION = re.compile(r'univ|college|coll\.|institut|école|ecole|school of|polytechn', re.I)
YEAR = re.compile(r'\b(1[89]\d\d|20[0-2]\d)\b')
SOURCE_YEAR = re.compile(r'(?:c|©|p)?\[?(1[5-9]\d\d|20[0-2]\d)\??\]?')
# Words in LC's notes that are not school names; and LC's abbreviations of state and school names.
NOISE = {'prof', 'profe', 'asst', 'assoc', 'assis', 'hist', 'histo', 'from', 'phd', 'lect', 'lectu', 'emer', 'emeri',
         'instr', 'dept', 'depar', 'thesi', 'disse', 'docto', 'degre', 'recei', 'usage', 'with', 'teach', 'taugh',
         'autho', 'earne', 'award', 'submi', 'publi', 'work', 'his', 'her', 'their', 'thes', 'diss', 'phil', 'not',
         'title', 'page', 'data', 'sheet', 'view', 'also', 'was', 'who', 'has', 'had', 'held', 'now', 'cand',
         'dphil', 'prese', 'forme', 'membe', 'curre', 'scien', 'socia', 'resea', 'senio', 'visit', 'adjun', 'endow',
         'chair', 'direc', 'acade', 'polit', 'humani', 'facul', 'janua', 'febru', 'march', 'april', 'may', 'june',
         'july', 'augus', 'septe', 'octob', 'novem', 'decem', 'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug',
         'sep', 'sept', 'oct', 'nov', 'dec', 'born', 'access', 'acces', 'point', 'digit', 'info', 'email', 'mail'}
ABBREV = {'ga': 'georgia', 'uconn': 'connecticut', 'conn': 'connecticut', 'calif': 'california', 'ariz': 'arizona',
          'wis': 'wisconsin', 'wisc': 'wisconsin', 'va': 'virginia', 'mass': 'massachusetts', 'penn': 'pennsylvania',
          'pa': 'pennsylvania', 'ill': 'illinois', 'ind': 'indiana', 'tenn': 'tennessee', 'okla': 'oklahoma',
          'tex': 'texas', 'fla': 'florida', 'md': 'maryland', 'mo': 'missouri', 'nc': 'north carolina',
          'oxf': 'oxford', 'camb': 'cambridge', 'tor': 'toronto', 'sask': 'saskatchewan', 'ubc': 'british columbia',
          'mcgill': 'mcgill', 'uw': 'washington', 'upenn': 'pennsylvania', 'umich': 'michigan', 'ucl': 'london',
          'kcl': 'kings london'}
DEPT = re.compile(r'dept|department|program|committee|graduate|grad\.|school of|faculty|division|centre|center',
                  re.I)


def expand(s):
    """LC's abbreviations spelled out: 'Ga. State Univ.', 'PhD, Tor.', 'UConn'. Two- and three-letter forms only
    with their period ('Ill.', 'Va.')."""
    return re.sub(r"\b([A-Za-z]+)(\.?)", lambda m: ABBREV[m[1].lower()] + m[2]
                  if m[1].lower() in ABBREV and (m[2] or len(m[1]) >= 4) else m[0], s or '')


def school_words(s, drop=()):
    return {w[:5] for w in school(expand(s))} - NOISE - set(drop)


STATE = re.compile(r'\bstate\b(?! of)', re.I)


def aha_school(department):
    """The university of an AHA department string, its department and programme segments set aside
    ('Univ. of Virginia, Corcoran Dept. of History' -> 'Univ. of Virginia')."""
    segs = [s for s in department.split(',') if not DEPT.search(s)]
    return ', '.join(segs) or department


def _pm(x, y):
    return x == y or (min(len(x), len(y)) >= 3 and (x.startswith(y) or y.startswith(x)))


def lc_school_agrees(department, clause, drop=()):
    """An AHA department and a clause of LC's notes name one school: every word of one side's school name
    meets a word of the other (prefixes count, for LC's abbreviations: 'U of Minn.', 'PhD, Tor.')."""
    a = school_words(aha_school(department))
    c = school_words(clause) - (set(drop) - a)          # a name that is also the school's ('Brown') stays
    if bool(STATE.search(aha_school(department))) != bool(STATE.search(expand(clause))):
        return False                                     # Michigan is not Michigan State
    return bool(a and c) and (all(any(_pm(x, y) for y in c) for x in a) or all(any(_pm(y, x) for x in a) for y in c))


def clauses(note):
    note = re.sub(r'\((ph\.? ?d\.?|d\.? ?phil\.?)\)', r'\1', note, flags=re.I)     # 'Thesis (Ph. D.)--Yale'
    return [c.strip() for c in re.split(r'[;()]| :: ', note) if c.strip()]


def cited(note, label):
    """(title, year) of the source a 670 cites ('His Fallen hero, 1992:'; 'Finan, Christopher M. Alfred E.
    Smith, the happy warrior, 2002:'; 'American policy toward Germany [MI] 1974:'), or None."""
    src = note.split(' :: ')[0].strip().rstrip(':').strip()
    years = list(SOURCE_YEAR.finditer(src))
    if not years:
        return None
    m = years[-1]
    t = re.sub(r'\[[^\]]*\]', '', src[:m.start()]).strip()
    t = re.sub(r"^(his|her|their|author'?s)\s+", '', t, flags=re.I)
    family, _, giv = label.partition(', ')
    if family and t.startswith(family + ', '):
        rest = t[len(family) + 2:]
        t = rest[len(giv):].lstrip('. ') if giv and rest.startswith(giv) else rest.split('. ', 1)[-1]
    return t.strip(' ,.'), int(m.group(1))


def title_agrees(cited_title, year, record):
    a, b = set(content(cited_title)), set(content(record['title'] or ''))
    if not (record['year'] or '').isdigit() or len(a) < 2 or len(b) < 2:
        return False
    if not int(record['year']) - 2 <= year <= int(record['year']) + 15:
        return False
    if min(len(a), len(b)) == 2:
        return a == b
    shared = len(a & b)
    return shared >= 3 and shared >= 0.6 * min(len(a), len(b))


def name_agrees(a, b):
    """Same person's name: key_aha_career's test, or the same surname with given names agreeing both ways as
    names or nicknames ('Waiser, William' / 'Bill Waiser')."""
    if initials_only(a if ', ' in a else f'{surname(a)}, {given(a)}') or \
            initials_only(b if ', ' in b else f'{surname(b)}, {given(b)}'):
        return False
    if same_person_name(a, b):
        return True
    return surname(a) == surname(b) and given_agrees(given(a), given(b)) and given_agrees(given(b), given(a))


def letters(label, first_only=False):
    """Initials a given name can agree on, nicknames spelled out ('Bill' -> b, w): an index for name_agrees."""
    toks = [t for t in words(given(label)) if t]
    toks = toks[:1] if first_only else toks
    return {c for t in toks for c in (t[0], NICKNAMES.get(t, t)[0])} | \
        {k[0] for t in toks for k, v in NICKNAMES.items() if v == t}


def by_letter(entries):
    """(surname, initial) -> entries; each entry (label, ...) is filed under every initial of its given names."""
    out = defaultdict(list)
    for e in entries:
        for c in letters(e[0]):
            out[surname(e[0]), c].append(e)
    return out


def assess(own, employers, notes, affiliations, birth, label):
    """Facts in one LC authority's notes about one AHA key. own: the key's AHA dissertation records;
    employers: directory institution and students' schools."""
    drop = school_words(label)          # the person's own name is not a school ('Bruce Brasington, Ph. D.')
    found = dict(title=[], degree=[], school=[], employer=[], other_school=[])
    for n in notes:
        c = cited(n, label)
        if c:
            found['title'] += [f'{c[0]}, {c[1]}' for r in own if title_agrees(c[0], c[1], r)]
        for cl in clauses(n):
            if DOCTORATE.search(cl):
                hits = [r for r in own if lc_school_agrees(r['department'], cl, drop)]
                for r in hits:
                    years = [int(y) for y in YEAR.findall(cl)]
                    ok = (r['year'] or '').isdigit() and any(abs(y - int(r['year'])) <= 1 for y in years)
                    found['degree' if ok else 'school'].append(cl[:160])
                if own and not hits and INSTITUTION.search(cl):
                    found['other_school'].append(cl[:160])
            elif JOB.search(cl):
                found['employer'] += [cl[:160] for e in employers if lc_school_agrees(e, cl, drop)]
    found['employer'] += [a for a in affiliations for e in employers if lc_school_agrees(e, a)]
    years = [int(r['year']) for r in own if (r['year'] or '').isdigit()]
    age_ok = not (years and birth) or any(18 <= y - birth <= 70 for y in years)
    found = {k: sorted(set(v)) for k, v in found.items()}
    fact = 'title' if found['title'] else 'degree' if found['degree'] else \
        'school_employer' if found['school'] and found['employer'] else None
    joins = bool(fact and age_ok and not found['other_school'])
    return dict(found, age_ok=age_ok, fact=fact, birth=birth), joins


def lc_records(lcids, lc_dir):
    """LC id -> (notes, affiliation labels, birth year)."""
    db = duckdb.connect()
    db.execute('CREATE TABLE want(lcid VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(x,) for x in lcids])
    rows = db.execute(f"SELECT lcid, notes, affiliations FROM read_parquet('{lc_dir}/personal-notes.parquet') "
                      'JOIN want USING (lcid)').fetchall()
    orgs = {a['org'] for _, _, affs in rows for a in affs or []}
    db.execute('CREATE TABLE o(id VARCHAR)')
    db.executemany('INSERT INTO o VALUES (?)', [(x,) for x in orgs])
    org = dict(db.execute(f"SELECT id, label FROM read_parquet('{lc_dir}/organisations.parquet') JOIN o USING (id)").fetchall())
    out = {x: ([], [], None) for x in lcids}
    for lcid, notes, affs in rows:
        out[lcid] = (list(notes or []), [org[a['org']] for a in affs or [] if a['org'] in org], None)
    for lcid, birth in db.execute(f"SELECT lcid, birth FROM read_parquet('{lc_dir}/personal-names.parquet') "
                                  'JOIN want USING (lcid)').fetchall():
        if (birth or '')[:4].isdigit():
            out[lcid] = (out[lcid][0], out[lcid][1], int(birth[:4]))
    return out


def lc_unkeyed(families, lc_dir, keyed):
    """Surname -> [(LC id, label)] for live, differentiated LC personal names no key holds."""
    db = duckdb.connect()
    db.execute('CREATE TABLE fam(f VARCHAR)')
    db.executemany('INSERT INTO fam VALUES (?)', [(f,) for f in families])
    out = defaultdict(list)
    for lcid, label in db.execute(f"""SELECT lcid, label FROM read_parquet('{lc_dir}/personal-names.parquet')
            WHERE NOT undifferentiated AND NOT deprecated
              AND regexp_replace(lower(strip_accents(split_part(label, ',', 1))), '[^a-z]+', ' ', 'g')
                  IN (SELECT f FROM fam)""").fetchall():
        if lcid not in keyed:
            out[surname(label_of(label))].append((lcid, label_of(label)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--lc', type=Path, default=Path('/mnt/e/lc-authorities'),
                    help='personal-names, personal-notes and organisations parquet')
    args = ap.parse_args()
    state = State.load(args.state)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    student_schools = defaultdict(set)
    for r in records.values():
        for t in (r['advisor_ids'] or '').split(';'):
            if t.strip():
                student_schools[t.strip()].add(r['department'])
    institution = defaultdict(set)
    with DIRECTORY.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['institution']:
                institution[r['token']].add(r['institution'])
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    with_lc = []                                     # (label, key, LC id) for keys holding one LC authority
    targets = []
    for k, v in live.items():
        schemes = {a.split(':', 1)[0] for a in v['anchors']}
        lcs = [a[6:] for a in v['anchors'] if a.startswith('lcnaf:')]
        if len(lcs) == 1:
            with_lc.append((v['label'], k, lcs[0]))
        if not schemes & PUBLIC_SCHEMES and schemes & {'aha', 'aha-phd'}:
            targets.append(k)
    keyed_lc = {a[6:] for a in state.anchor if a.startswith('lcnaf:')}
    unkeyed = lc_unkeyed({surname(live[k]['label']) for k in targets}, args.lc, keyed_lc)
    index = by_letter(with_lc + [(lab, None, lc) for v in unkeyed.values() for lc, lab in v])
    report = Counter()
    pairs = {}
    for k in targets:
        label = live[k]['label']
        seen, cs = set(), []
        for c in letters(label, first_only=True):
            for lab, key, lc in index.get((surname(label), c), ()):
                if lc not in seen and name_agrees(label, lab):
                    seen.add(lc)
                    cs.append((key, lc, lab))
        if cs:
            pairs[k] = cs
    report['targets'] = len(targets)
    report['targets_with_candidates'] = len(pairs)
    lc = lc_records({lc for cs in pairs.values() for _, lc, _ in cs}, args.lc)
    clusters, listed, joins_csv = [], [], []
    for k, cs in sorted(pairs.items(), key=lambda kv: int(kv[0][2:])):
        anchors = live[k]['anchors']
        tokens = [a[4:] for a in anchors if a.startswith('aha:')]
        own = [records[a[8:]] for a in anchors if a.startswith('aha-phd:') and a[8:] in records]
        employers = sorted({e for t in tokens for e in institution.get(t, set()) | student_schools.get(t, set())})
        rows = []
        for c, lcid, lab in cs:
            notes, affs, birth = lc[lcid]
            found, joins = assess(own, employers, notes, affs, birth, lab)
            rows.append(dict(key=c, lcnaf=lcid, label=lab, joins=joins, **found))
        joining = [r for r in rows if r['joins']]
        entry = dict(key=k, label=live[k]['label'], own=[dict(record=r['id'], school=r['department'], year=r['year'],
                                                              title=r['title']) for r in own], employers=employers)
        if len(joining) > 1:
            report['several_join'] += 1
            listed.append(dict(entry, outcome='several_join', candidates=joining))
            continue
        if not joining:
            best = [r for r in rows if r['fact'] or r['school'] or r['employer'] or r['other_school']]
            if best:
                kind = 'contradicted' if any(r['fact'] and r['other_school'] for r in best) else \
                    'age_disagrees' if any(r['fact'] and not r['age_ok'] for r in best) else 'one_fact'
                report[kind] += 1
                listed.append(dict(entry, outcome=kind, candidates=best))
            else:
                report['no_fact'] += 1
            continue
        r = joining[0]
        report['joins'] += 1
        report[f'joins_{r["fact"]}_{"keyed" if r["key"] else "new_lc"}'] += 1
        evidence = r['title'] or r['degree'] or (r['school'][:1] + r['employer'][:1])
        joins_csv.append(dict(aha_key=k, aha_label=live[k]['label'], lc_key=r['key'] or '', lcnaf=r['lcnaf'],
                              lc_label=r['label'], fact=r['fact'], evidence=' | '.join(evidence)[:300],
                              aha=' | '.join(f'{o["department"]} {o["year"]}: {o["title"]}' for o in own)[:300]))
        clusters.append(dict(type='person', label=live[r['key']]['label'] if r['key'] else live[k]['label'],
                             anchors={f'lcnaf:{r["lcnaf"]}'} | anchors, members=set(), aliases=set(),
                             resolution='established',
                             basis=f'AHA {live[k]["label"]} is LC {r["lcnaf"]} by LC\'s notes ({r["fact"]}): '
                                   + '; '.join(evidence)[:400]))
    reach = Counter(next(a for a in c['anchors'] if a.startswith('lcnaf:')) for c in clusters)
    several = {a for a, n in reach.items() if n > 1}    # one authority, several AHA keys: none joins (listed)
    for c in [c for c in clusters if c['anchors'] & several]:
        report['joins'] -= 1
        report['lc_reached_by_several'] += 1
        listed.append(dict(key=sorted(a for a in c['anchors'] if a.startswith(('aha:', 'aha-phd:'))), label=c['label'],
                           outcome='lc_reached_by_several', basis=c['basis']))
    joins_csv = [r for r in joins_csv if f'lcnaf:{r["lcnaf"]}' not in several]
    clusters = [c for c in clusters if not c['anchors'] & several]
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    for o in [o for o in ops if o['event'] == 'merge']:     # an AHA-only survivor takes the LC key's fuller name
        into, gone = state.keys[o['into']], state.keys[o['key']]
        if not any(a.split(':', 1)[0] in PUBLIC_SCHEMES for a in into['anchors']) and len(gone['label']) > len(into['label']):
            ops.append(dict(event='relabel', key=o['into'], label=gone['label'], basis='the name on the LC key it joined'))
    materialise(state, dict(basis='aha lc notes', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="AHA-only keys joined to LC authorities by LC's 670 notes: the dissertation cited, or the doctorate "
              "stated (school and year, or school and employer)", decided_by='build', ops=ops),
        ensure_ascii=False, indent=1) + '\n')
    with gzip.open(args.out / 'candidates.json.gz', 'wt', encoding='utf-8') as f:      # about 16 MB unzipped
        f.write(json.dumps(listed, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    with (args.out / 'joins.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(joins_csv[0]) if joins_csv else ['aha_key'])
        w.writeheader()
        w.writerows(joins_csv)
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
