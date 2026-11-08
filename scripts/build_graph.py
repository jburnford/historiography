"""The key log as a queryable graph: Parquet tables and an embedded LadybugDB (Cypher) database (2026-11-02).

The key log (data/identifiers/events-*.jsonl, closed shards gzipped) is the source of truth in git; this builds a local, disposable
view of it that anyone can rebuild from a clean clone. It reads only files tracked in git (it stops if an input
is untracked) and writes to build/graph/ (git-ignored):
- nodes: `Person`, `Work`, `Institution` (active keys; identifiers by scheme as columns, all anchors as a list);
- relations from the log's claims: `AUTHORED`, `EDITED`, `SUPERVISED` (Person -> Work), `PUBLISHED_AS` and
  `REVIEWS` (Work -> Work: a review and the book it reviews), with the claim key and its resolution; claims
  whose endpoints do not resolve to one key each are left out and counted;
- `COEDITED` (Person -> Person, once per pair), derived as COAUTHORED from shared EDITED volumes;
- `PART_OF` (Work -> Work): a chapter and the volume it is in; `EDITOR_OF` (Person -> Person), derived: a
  volume's editor -> each author of a chapter in it (with the chapter and volume keys; user, 2026-11-05);
- `REVIEWED` (Person -> Person), derived: the author of a review -> each author of the book it reviews, with
  the review and book keys (user, 2026-11-02: edges between reviewers and the authors of the books);
- `ADVISED` (Person -> Person), derived: a thesis's supervisor -> its author (with the claim and thesis keys),
  and the log's person-to-person `advised` claims (Wikidata's doctoral advisors where the student's thesis is
  not in the log; thesis empty);
- `COAUTHORED` (Person -> Person, stored once per pair, lower key first), derived: people who authored the same
  works, with the number of works, of distinct titles (an editorial co-signed in many journals has one DOI per
  journal: 147 works, 1 title), the first and last year and the work keys (user, 2026-11-05: a count matters);
- `AWARDED_BY` (Work -> Institution) from the works' `awarded-by:` members;
- `AFFILIATED_WITH` (Person -> Institution): dated affiliations by source (AHA directory and advising, IHR staff
  lists, ORCID, Wikidata, review credits, JSTOR review signatures, LC 373) from data/graph/affiliations.csv.gz
  (scripts/export_affiliations.py; user, 2026-11-08: departments should show the faculty who taught there);
- `POSSIBLY_SAME` (Person -> Person, once per pair, lower key first) from `possible-same:` members: same name and
  fitting timelines, not confirmed (scripts/key_possible_same.py; user, 2026-11-08); dropped once the two merge;
- `CITES` (Work -> Work): a corpus dissertation citing a keyed work (data/graph/cites.csv.gz, exported from
  the corpus by scripts/export_citations.py), and a JSTOR article, review essay or review article citing one in
  its notes (data/graph/jstor-cites.csv.gz, scripts/export_jstor_citations.py; 2026-11-06). `edition` is true when
  the only evidence is a JSTOR note citing a later edition or translation of the work (2026-11-08); counts may
  include or leave these out. Crossref reference lists of journal articles add more (data/graph/crossref-cites.csv.gz,
  scripts/crossref_citations.py; 2026-11-08), above all after the JSTOR runs end (about 2020).
With --db, the Parquet tables are loaded into a LadybugDB database (build/graph/historiography.lbug), queried in
Cypher:

    MATCH (p:Person)-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) WHERE p.label = 'Benjamin Hoy' RETURN s.label, t.label

    python3 scripts/build_graph.py            # Parquet tables only
    python3 scripts/build_graph.py --db       # and the LadybugDB database
"""
import argparse
import csv
import gzip
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from identifiers import DEFAULT_DIR, PREDICATES, RETIRED, ROOT, State

OUT = ROOT / 'build/graph'
CITES = ROOT / 'data/graph/cites.csv.gz'
JSTOR_CITES = ROOT / 'data/graph/jstor-cites.csv.gz'   # scripts/export_jstor_citations.py (JSTOR article notes)
CROSSREF_CITES = ROOT / 'data/graph/crossref-cites.csv.gz'   # scripts/crossref_citations.py (Crossref reference lists)
AFFILIATIONS = ROOT / 'data/graph/affiliations.csv.gz'  # scripts/export_affiliations.py (dated person -> institution)
SCHEMES = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'ror')
PERSON_RELATIONS = ('authored', 'edited', 'supervised')


def require_tracked(paths):
    """Stop unless every input is tracked in git: the build must work from a clean clone."""
    missing = []
    for p in paths:
        r = subprocess.run(['git', 'ls-files', '--error-unmatch', str(p.relative_to(ROOT))], cwd=ROOT,
                           capture_output=True)
        if r.returncode:
            missing.append(str(p.relative_to(ROOT)))
    if missing:
        sys.exit(f'inputs not tracked in git: {missing}')


def first(anchors, scheme):
    vals = sorted(a.split(':', 1)[1] for a in anchors if a.split(':', 1)[0] == scheme)
    return vals[0] if vals else None


def year_of(members, prefix):
    vals = sorted(m.split(':', 1)[1] for m in members if m.startswith(prefix) and m.split(':', 1)[1][:4].isdigit())
    return int(vals[0][:4]) if vals else None


def work_kind(anchors, members=()):
    stated = [m.split(':', 1)[1] for m in members if m.startswith('kind:')]   # a kind stated on review (DOI-only books)
    if len(stated) == 1:
        return stated[0]
    schemes = {a.split(':', 1)[0] for a in anchors}
    if schemes & {'aha-diss', 'diss-thesis', 'wrap'}:
        return 'thesis'
    if schemes & {'hnet-review', 'rih-review'}:
        return 'review'
    if 'lccn' in schemes:
        return 'book'
    if 'doi' in schemes:
        return 'article'          # articles and chapters cited in the corpus (key_cited_articles), and ORCID works
    if 'atlas' in schemes:
        return 'atlas_source'
    return 'other'


def write(name, rows, schema):
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, OUT / f'{name}.parquet')
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--db', action='store_true', help='also load the tables into LadybugDB')
    args = ap.parse_args()
    shards = sorted(args.state.glob('events-*.jsonl*'))
    require_tracked(shards + [CITES] + [p for p in (JSTOR_CITES, CROSSREF_CITES, AFFILIATIONS) if p.exists()])
    state = State.load(args.state)
    OUT.mkdir(parents=True, exist_ok=True)
    report = Counter()

    live = {k: v for k, v in state.keys.items() if v['status'] not in RETIRED}
    people, works, insts = [], [], []
    for k, v in live.items():
        anchors = sorted(v['anchors'])
        members = state.members.get(k, set())
        base = dict(key=k, label=v['label'], resolution=v['resolution'], anchors=anchors)
        if v['type'] == 'person':
            people.append(dict(base, **{s: first(anchors, s) for s in SCHEMES if s != 'ror'}))
        elif v['type'] == 'work':
            works.append(dict(base, kind=work_kind(anchors, members), lccn=first(anchors, 'lccn'),
                              year=year_of(members, 'year:') or year_of(members, 'lc-first-year:'),
                              # a review's reviewers as printed (key_jstor_reviews: no name-only person keys)
                              reviewer_names=sorted(m.split(':', 1)[1] for m in members if m.startswith('reviewer-name:')),
                              journal=next((m.split(':', 1)[1] for m in members if m.startswith('journal:')), None)))
        elif v['type'] == 'institution':
            insts.append(dict(base, ror=first(anchors, 'ror')))
    s, L = pa.string(), pa.list_(pa.string())
    report['Person'] = write('person', people, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L)] +
                                                        [(x, s) for x in SCHEMES if x != 'ror']))
    report['Work'] = write('work', works, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L),
                                                    ('kind', s), ('lccn', s), ('year', pa.int32()),
                                                    ('reviewer_names', L), ('journal', s)]))
    report['Institution'] = write('institution', insts, pa.schema([('key', s), ('label', s), ('resolution', s),
                                                                  ('anchors', L), ('ror', s)]))
    types = {k: v['type'] for k, v in live.items()}

    rels = defaultdict(list)
    for claim, subj, pred, obj in state.relations():
        if len(subj) != 1 or len(obj) != 1:
            report[f'{pred}_unresolved'] += 1
            continue
        a, b = subj[0], obj[0]
        want = PREDICATES.get(pred, ('person', 'work'))
        if (types.get(a), types.get(b)) != want:
            report[f'{pred}_wrong_types'] += 1
            continue
        rels[pred.upper()].append({'from': a, 'to': b, 'claim': claim, 'resolution': state.keys[claim]['resolution']})
    rel_schema = pa.schema([('from', s), ('to', s), ('claim', s), ('resolution', s)])
    for name in ('AUTHORED', 'EDITED', 'SUPERVISED', 'PUBLISHED_AS', 'REVIEWS', 'PART_OF'):
        report[name] = write(name.lower(), rels[name], rel_schema)
    authors = defaultdict(set)
    for r in rels['AUTHORED']:
        authors[r['to']].add(r['from'])
    reviewed = sorted({(a, b, r['from'], r['to']) for r in rels['REVIEWS'] for a in authors[r['from']]
                       for b in authors[r['to']] if a != b})
    report['REVIEWED'] = write('reviewed', [{'from': a, 'to': b, 'review': rv, 'book': bk} for a, b, rv, bk in reviewed],
                               pa.schema([('from', s), ('to', s), ('review', s), ('book', s)]))
    # editor -> contributor: a volume's editors -> the authors of a chapter in it (user, 2026-11-05: editors of
    # books I've published in)
    editors = defaultdict(set)
    for r in rels['EDITED']:
        editors[r['to']].add(r['from'])
    editor_of = sorted({(e, a, r['from'], r['to']) for r in rels['PART_OF'] for e in editors[r['to']]
                        for a in authors[r['from']] if e != a})
    report['EDITOR_OF'] = write('editor_of', [{'from': e, 'to': a, 'chapter': c, 'volume': v} for e, a, c, v in editor_of],
                                pa.schema([('from', s), ('to', s), ('chapter', s), ('volume', s)]))
    # advisor -> student: a supervised thesis's authors, and Wikidata's person-to-person advised claims
    advised = {(r['from'], b): (r['claim'], r['to']) for r in rels['SUPERVISED'] for b in authors[r['to']] if b != r['from']}
    for r in rels['ADVISED']:
        advised.setdefault((r['from'], r['to']), (r['claim'], ''))
    report['ADVISED'] = write('advised', [{'from': a, 'to': b, 'claim': c, 'thesis': t} for (a, b), (c, t) in sorted(advised.items())],
                              pa.schema([('from', s), ('to', s), ('claim', s), ('thesis', s)]))

    # co-authors: people who authored the same works, once per pair, with how many works, the years and the
    # works (user, 2026-11-05: a count matters; several joint articles are an ongoing collaboration, not a one-off)
    year = {w['key']: w['year'] for w in works}
    from key_lc_works import title_key
    title = {w['key']: title_key(re.sub(r'\s+—\s+.*$', '', w['label'] or '')) or w['key'] for w in works}
    shared = defaultdict(set)
    for w, people_of in authors.items():
        for a in people_of:
            for b in people_of:
                if a < b:
                    shared[a, b].add(w)
    rows = []
    for (a, b), ws in sorted(shared.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        rows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                     'first_year': ys[0] if ys else None,
                     'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws)})
    # co-editors: people who edited the same volume, built as COAUTHORED is (user, 2026-11-05: editors in the network)
    eds_of = defaultdict(set)
    for r in rels['EDITED']:
        eds_of[r['to']].add(r['from'])
    co_ed = defaultdict(set)
    for w, people_of in eds_of.items():
        for a in people_of:
            for b in people_of:
                if a < b:
                    co_ed[a, b].add(w)
    erows = []
    for (a, b), ws in sorted(co_ed.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        erows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                      'first_year': ys[0] if ys else None, 'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws)})
    report['COEDITED'] = write('coedited', erows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                           ('first_year', pa.int32()), ('last_year', pa.int32()), ('work_keys', L)]))
    report['COAUTHORED'] = write('coauthored', rows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                                ('first_year', pa.int32()), ('last_year', pa.int32()),
                                                                ('work_keys', L)]))

    awarded = []
    for w in works:
        for m in state.members.get(w['key'], ()):
            if m.startswith('awarded-by:'):
                i = state.lookup(m.split(':', 1)[1])
                if len(i) == 1 and types.get(i[0]) == 'institution':
                    awarded.append({'from': w['key'], 'to': i[0]})
    report['AWARDED_BY'] = write('awarded_by', awarded, pa.schema([('from', s), ('to', s)]))

    possible = set()
    for person in people:
        for m in state.members.get(person["key"], ()):
            if m.startswith('possible-same:'):
                o = state.lookup(m.split(':', 1)[1])
                if len(o) == 1 and o[0] != person["key"] and types.get(o[0]) == 'person':
                    possible.add(tuple(sorted((person["key"], o[0]))))
    aff = {}
    if AFFILIATIONS.exists():
        with gzip.open(AFFILIATIONS, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                pk, ik = state.lookup(r['person']), state.lookup(r['institution'])
                if len(pk) != 1 or len(ik) != 1 or types.get(pk[0]) != 'person' or types.get(ik[0]) != 'institution':
                    report['affiliations_unresolved'] += 1
                    continue
                yv = lambda v: int(v) if v else None
                akey = (pk[0], ik[0], r['source'])
                old = aff.get(akey)
                y0 = min([v for v in (yv(r['first_year']), old and old['first_year']) if v] or [None])
                y1 = max([v for v in (yv(r['last_year']), old and old['last_year']) if v] or [None])
                aff[akey] = {'from': pk[0], 'to': ik[0], 'source': r['source'], 'first_year': y0, 'last_year': y1,
                            'n': int(r['n']) + (old['n'] if old else 0), 'rank': r['rank'] or (old and old['rank']) or None,
                            'department': r['department'] or (old and old['department']) or None}
    report['AFFILIATED_WITH'] = write('affiliated_with', list(aff.values()), pa.schema([
        ('from', s), ('to', s), ('source', s), ('first_year', pa.int32()), ('last_year', pa.int32()), ('n', pa.int32()),
        ('rank', s), ('department', s)]))
    report['POSSIBLY_SAME'] = write('possibly_same', [{'from': a, 'to': b} for a, b in sorted(possible)],
                                    pa.schema([('from', s), ('to', s)]))

    cites = {}                      # (citing, cited) -> edition only (True) or a direct match (False)
    with gzip.open(CITES, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            a, b = state.lookup(f'diss-thesis:{r["dissertation_id"]}'), state.lookup(r['work_key'])
            if len(a) == 1 and len(b) == 1 and types.get(a[0]) == types.get(b[0]) == 'work' and a[0] != b[0]:
                cites[(a[0], b[0])] = False
            else:
                report['cites_unresolved'] += 1
    for name, path in (('jstor', JSTOR_CITES), ('crossref', CROSSREF_CITES)):   # journal articles citing keyed works
        if not path.exists():
            continue
        with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                a, b = state.lookup(r['citing_work']), state.lookup(r['cited_work'])
                if len(a) == 1 and len(b) == 1 and types.get(a[0]) == types.get(b[0]) == 'work' and a[0] != b[0]:
                    report[f'cites_from_{name}'] += (a[0], b[0]) not in cites
                    ed = r.get('basis') == 'edition'      # cites a later edition or translation of the work
                    cites[(a[0], b[0])] = cites.get((a[0], b[0]), True) and ed
                    report[f'{name}_cites_edition'] += ed
                else:
                    report[f'{name}_cites_unresolved'] += 1
    report['CITES'] = write('cites', [{'from': a, 'to': b, 'edition': e} for (a, b), e in sorted(cites.items())],
                            pa.schema([('from', s), ('to', s), ('edition', pa.bool_())]))
    report['CITES_edition_only'] = sum(cites.values())

    if args.db:
        load_db(report)
    (OUT / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items())), indent=1))


def load_db(report):
    import ladybug as lb
    path = OUT / 'historiography.lbug'
    if path.exists():
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    for side in (path.with_suffix('.lbug.wal'),):
        if side.exists():
            side.unlink()
    conn = lb.Connection(lb.Database(str(path)))
    ids = 'anchors STRING[], lcnaf STRING, wd STRING, orcid STRING, gnd STRING, viaf STRING, isni STRING, idref STRING'
    conn.execute(f'CREATE NODE TABLE Person(key STRING, label STRING, resolution STRING, {ids}, PRIMARY KEY (key))')
    conn.execute('CREATE NODE TABLE Work(key STRING, label STRING, resolution STRING, anchors STRING[], kind STRING, '
                 'lccn STRING, year INT32, reviewer_names STRING[], journal STRING, PRIMARY KEY (key))')
    conn.execute('CREATE NODE TABLE Institution(key STRING, label STRING, resolution STRING, anchors STRING[], '
                 'ror STRING, PRIMARY KEY (key))')
    for name in ('AUTHORED', 'EDITED', 'SUPERVISED'):
        conn.execute(f'CREATE REL TABLE {name}(FROM Person TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PUBLISHED_AS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE REVIEWS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PART_OF(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE EDITOR_OF(FROM Person TO Person, chapter STRING, volume STRING)')
    conn.execute('CREATE REL TABLE REVIEWED(FROM Person TO Person, review STRING, book STRING)')
    conn.execute('CREATE REL TABLE ADVISED(FROM Person TO Person, claim STRING, thesis STRING)')
    conn.execute('CREATE REL TABLE COEDITED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[])')
    conn.execute('CREATE REL TABLE COAUTHORED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[])')
    conn.execute('CREATE REL TABLE AWARDED_BY(FROM Work TO Institution)')
    conn.execute('CREATE REL TABLE POSSIBLY_SAME(FROM Person TO Person)')
    conn.execute('CREATE REL TABLE AFFILIATED_WITH(FROM Person TO Institution, source STRING, first_year INT32, '
                 'last_year INT32, n INT32, rank STRING, department STRING)')
    conn.execute('CREATE REL TABLE CITES(FROM Work TO Work, edition BOOL)')
    for table, file in (('Person', 'person'), ('Work', 'work'), ('Institution', 'institution'),
                        ('AUTHORED', 'authored'), ('EDITED', 'edited'), ('SUPERVISED', 'supervised'),
                        ('PUBLISHED_AS', 'published_as'), ('REVIEWS', 'reviews'), ('PART_OF', 'part_of'), ('EDITOR_OF', 'editor_of'), ('REVIEWED', 'reviewed'), ('ADVISED', 'advised'),
                        ('COAUTHORED', 'coauthored'), ('COEDITED', 'coedited'),
                        ('AWARDED_BY', 'awarded_by'), ('POSSIBLY_SAME', 'possibly_same'), ('AFFILIATED_WITH', 'affiliated_with'),
                        ('CITES', 'cites')):
        conn.execute(f"COPY {table} FROM '{OUT / (file + '.parquet')}'")
    report['db'] = str(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
