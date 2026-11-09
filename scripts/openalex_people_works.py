"""Graph people -> their publications in OpenAlex (2026-11-08; user on p-31280, Ben Bradley: "you are missing Ben's book"
and "other publications"). Identity by works (memory: identity-by-works): an OpenAlex author is tied to a graph person
only through a work the graph already credits to that person, never through name, topic or field alone.

link    One pass over the OpenAlex History/HPS harvest (scripts/openalex_history_harvest.py, works and dissertations).
        Each OpenAlex work is matched to a graph work by DOI, else by main title + an author's family name through the
        JSTOR session's matcher (strong / title+year only, one graph work). On a matched work, an authorship whose
        family name is the family name of a person the graph credits with that work (authored or edited) ties that
        OpenAlex author id to the person ('work'); an authorship ORCID equal to a person's ORCID anchor ties it too
        ('orcid'). Every authorship row is kept (OpenAlex author id, name, work id, DOI, type, year, title, the matched
        graph work) in parquet on E:, one file per slice; metadata only.
report  The ties per (OpenAlex author, person); an OpenAlex author tied to two persons is held (a namesake merge in
        OpenAlex, or two graph keys for one person: listed as dedup candidates); for each cleanly tied author, the works
        in the harvest the graph lacks, under an authorship with the person's family name, within the years of the
        works that tied them (40 years either side) -> candidate authored works. Writes report.json, ties.parquet,
        candidates.parquet, and the people asked about.

    python3 scripts/openalex_people_works.py link --workers 4
    python3 scripts/openalex_people_works.py report [--show p-145261,p-...]
    python3 scripts/openalex_people_works.py propose --out data/identifiers/openalex-person-works-2026-11-09 [--shard 90000]

propose  From the screened candidates with status 'add' (not reviews: a review needs the reviewed book, kept apart in
        reviews.parquet on E:), whose authorship name agrees with the person (same family name; given names agree, as
        scripts/namesake_check_groups.py given_names_agree): one work key per OpenAlex work (anchor doi:, else
        openalex:W...; year:, kind:, journal:) and an authored claim on the person's most stable anchor (orcid, lcnaf,
        wd, then any other except pooled diss-person ids). 'existing?' rows with a DOI attach the DOI to the graph work
        when no key holds it. Rows for a DOI the key log already holds become claims on that work.
"""
import argparse, collections, glob, gzip, importlib.util, json, multiprocessing as mp, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = '/mnt/e/openalex-history-2026-11-08'
OUT = Path('/mnt/e/openalex-people-2026-11-08')
GRAPH = ROOT / 'build/graph'

M = IDX = DOI_WORK = WORK_PEOPLE = PERSON_FAM = ORCID_PERSON = None


def matcher():
    p = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py'
    spec = importlib.util.spec_from_file_location('jstor_match_candidates', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def setup():
    global M, IDX, DOI_WORK, WORK_PEOPLE, PERSON_FAM, ORCID_PERSON
    import duckdb
    M = matcher()
    IDX, DOI_WORK = M.work_index()
    db = duckdb.connect(); db.execute("SET memory_limit = '4GB'")
    WORK_PEOPLE = collections.defaultdict(list)
    for w, p in db.execute(f"""select "to", "from" from '{GRAPH}/authored.parquet'
                               union select "to", "from" from '{GRAPH}/edited.parquet'""").fetchall():
        WORK_PEOPLE[w].append(p)
    PERSON_FAM = {k: M.family(l) for k, l in db.execute(f"select key, label from '{GRAPH}/person.parquet'").fetchall()}
    ORCID_PERSON = dict(db.execute(f"""select orcid, min(key) from '{GRAPH}/person.parquet' where orcid is not null
                                      group by orcid having count(*) = 1""").fetchall())


def oa_family(name):
    words = M.fold(re.sub(r',?\s+(?:Jr|Sr|II|III|IV)\.?$', '', name or '')).split()
    return words[-1] if words else ''


def graph_work(w, fams):
    d = (w.get('doi') or '').lower().replace('https://doi.org/', '')
    if d and d in DOI_WORK:
        return DOI_WORK[d], 'doi'
    tk = M.cited_key(w.get('title') or '')
    if not M.usable(tk):
        return None, None
    found = {}
    for fam in dict.fromkeys(f for f in fams if len(f) >= 2):
        pick, b = M.lookup(IDX, tk, fam, w.get('publication_year'))
        if pick and len(pick) == 1 and b in ('strong', 'title+year'):
            found[pick[0][0]] = b
    if len(found) == 1:
        (k, b), = found.items()
        return k, b
    return None, None


def do_file(path):
    import pyarrow as pa, pyarrow.parquet as pq
    name = Path(path).parent.name + '-' + Path(path).name.replace('.jsonl.gz', '')
    dest = OUT / 'rows' / f'{name}.parquet'
    if dest.exists():
        return 0
    cols = collections.defaultdict(list)
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            w = json.loads(line)
            auths = w.get('authorships') or []
            names = [(a.get('author') or {}).get('display_name') or a.get('raw_author_name') or '' for a in auths]
            fams = [oa_family(n) for n in names]
            g, basis = graph_work(w, fams)
            people = WORK_PEOPLE.get(g, []) if g else []
            for a, n, fam in zip(auths, names, fams):
                au = a.get('author') or {}
                orcid = (au.get('orcid') or '').rsplit('/', 1)[-1]
                tie = ''
                person = ''
                hits = [p for p in people if PERSON_FAM.get(p) == fam and fam]
                if len(hits) == 1:
                    person, tie = hits[0], 'work'
                if orcid and orcid in ORCID_PERSON:
                    if not person or person == ORCID_PERSON[orcid]:
                        person, tie = ORCID_PERSON[orcid], (tie + '+orcid' if tie else 'orcid')
                for k, v in (('author', (au.get('id') or '').rsplit('/', 1)[-1]), ('name', n), ('family', fam),
                             ('orcid', orcid), ('work', w['id'].rsplit('/', 1)[-1]),
                             ('doi', (w.get('doi') or '').lower().replace('https://doi.org/', '')),
                             ('type', w.get('type') or ''), ('year', w.get('publication_year')),
                             ('title', (w.get('title') or '')[:400]),
                             ('venue', (((w.get('primary_location') or {}).get('source') or {}).get('display_name') or '')[:200]),
                             ('graph_work', g or ''), ('match', basis or ''), ('person', person), ('tie', tie)):
                    cols[k].append(v)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.part')
    pq.write_table(pa.table(dict(cols)) if cols else pa.table({'author': pa.array([], pa.string())}), tmp)
    os.replace(tmp, dest)
    return len(cols['author'])


def link(args):
    t0 = time.time()
    setup()
    files = sorted(glob.glob(f'{SRC}/history/*.jsonl.gz') + glob.glob(f'{SRC}/dissertations/*.jsonl.gz'),
                   key=lambda p: -os.path.getsize(p))
    print(f'index ready in {time.time() - t0:.0f}s; {len(files)} files', flush=True)
    n = done = 0
    with mp.get_context('fork').Pool(args.workers) as pool:
        for r in pool.imap_unordered(do_file, files):
            n += r; done += 1
            if done % 20 == 0:
                print(f'{done}/{len(files)} files, {n:,} authorship rows, {time.time() - t0:.0f}s', flush=True)
    print(f'done: {n:,} rows, {time.time() - t0:.0f}s', flush=True)


KEEP_TYPES = {'article': 'article', 'book-chapter': 'chapter', 'book': 'book', 'dissertation': 'thesis',
              'reference-entry': 'chapter', 'review': 'review', 'book-review': 'review', 'other': 'other'}


def words(t):
    import unicodedata
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z0-9]+', t) if len(w) > 2}


def screen(db):
    """Status of each candidate work:
    add            a strong tie (the person's ORCID, or two or more shared works), a kept type, inside the life years;
    weak_tie       as add, but the OpenAlex author shares only one work with the person (OpenAlex author ids can join
                   namesakes; Classen-size lists from one shared work need a look);
    existing?      the title shares most of its words with a work the graph already credits to the person (a typo or
                   subtitle variant: Clifford's 'Urban Peropherpy' = w-1025223): a DOI for that work, not a new one;
    out_part       the DOI extends the DOI of a graph work (a chapter of the person's own book: 10.59962/9780774834209-005);
    out_type       datasets, paratext, editorials, errata, preprints, abstracts ...;
    out_life       after death + 3 (posthumous editions: Pope, Dickens, Davy) or before birth + 18."""
    import csv as _csv
    life = {}
    with gzip.open(ROOT / 'data/person-facts/life-years.csv.gz', 'rt', encoding='utf-8') as f:
        for r in _csv.DictReader(f):
            life[r['key']] = (int(r['birth']) if r['birth'] else None, int(r['death']) if r['death'] else None)
    gdoi = {r[0] for r in db.execute(f"""select lower(substr(a, 5)) from (select unnest(anchors) a from '{GRAPH}/work.parquet')
                                         where a like 'doi:%'""").fetchall()}
    own = collections.defaultdict(list)
    for person, key, label in db.execute(f"""select x.person, w.key, w.label from
            (select "from" AS person, "to" AS wk from '{GRAPH}/authored.parquet' union select "from", "to" from '{GRAPH}/edited.parquet') x
            join '{GRAPH}/work.parquet' w on w.key = x.wk
            where x.person in (select distinct person from cand)""").fetchall():
        own[person].append((key, words(label)))
    strong = {(a, p) for a, p, w, k in db.execute("select author, person, works, tie_kinds from oa_ties").fetchall()
              if w >= 2 or any('orcid' in t for t in k)}
    rows = db.execute("select person, author, work, doi, wtype, year, title from cand").fetchall()
    out, rep = [], collections.Counter()
    for person, author, work, doi, wtype, year, title in rows:
        status, existing = None, ''
        b, d = life.get(person, (None, None))
        if wtype not in KEEP_TYPES:
            status = 'out_type'
        elif year and ((d and year > d + 3) or (b and year < b + 18)):
            status = 'out_life'
        elif doi and re.sub(r'[-.][^-./]+$', '', doi) in gdoi:
            status = 'out_part'
        else:
            tw = words(title)
            if len(tw) >= 3:
                for key, ow in own[person]:
                    if ow and len(tw & ow) / len(tw | ow) >= 0.6:
                        status, existing = 'existing?', key
                        break
            if not status:
                status = 'add' if (author, person) in strong else 'weak_tie'
        rep[status] += 1
        out.append((person, work, status, existing))
    db.execute("create temp table st(person varchar, work varchar, status varchar, existing varchar)")
    db.executemany("insert into st values (?, ?, ?, ?)", out)
    db.execute("""create or replace temp table cand as select c.*, st.status, st.existing from cand c
                  join st on st.person = c.person and st.work = c.work""")
    rep['add_persons'] = db.execute("select count(distinct person) from cand where status = 'add'").fetchone()[0]
    rep['add_by_type'] = dict(db.execute("select wtype, count(*) from cand where status = 'add' group by 1 order by 2 desc").fetchall())
    return dict(rep)


def report(args):
    import duckdb
    db = duckdb.connect(); db.execute("SET memory_limit = '8GB'")
    R = f"read_parquet('{OUT}/rows/*.parquet', union_by_name=true)"
    db.execute(f"""create temp table oa_ties as
        select author, person, count(distinct work) works, list(distinct tie) tie_kinds, min(year) y0, max(year) y1
        from {R} where person <> '' and author <> '' group by author, person""")
    db.execute("""create temp table clean as select * from oa_ties where author in
                  (select author from oa_ties group by author having count(distinct person) = 1)""")
    db.execute(f"""create temp table cand as
        select c.person, r.author, r.work, any_value(r.doi) AS doi, any_value(r.type) AS wtype, any_value(r.year) AS year,
               any_value(r.title) AS title, any_value(r.venue) AS venue, any_value(r.name) AS name
        from {R} r join clean c on c.author = r.author
        join (select key, label from '{GRAPH}/person.parquet') p on p.key = c.person
        where r.graph_work = '' and r.year between c.y0 - 40 and c.y1 + 40
        group by c.person, r.author, r.work""")
    rep = dict(
        authorship_rows=db.execute(f"select count(*) from {R}").fetchone()[0],
        oa_works_matched_to_graph=db.execute(f"select count(distinct work) from {R} where graph_work <> ''").fetchone()[0],
        match_bases=dict(db.execute(f"select match, count(distinct work) from {R} where graph_work <> '' group by 1").fetchall()),
        ties=db.execute("select count(*) from oa_ties").fetchone()[0],
        persons_tied=db.execute("select count(distinct person) from clean").fetchone()[0],
        oa_authors_tied_cleanly=db.execute("select count(distinct author) from clean").fetchone()[0],
        oa_authors_held_two_persons=db.execute("select count(distinct author) from oa_ties where author not in (select author from clean)").fetchone()[0],
        candidate_works=db.execute("select count(*) from cand").fetchone()[0],
        candidate_persons=db.execute("select count(distinct person) from cand").fetchone()[0],
        candidate_types=dict(db.execute("select wtype, count(*) from cand group by 1 order by 2 desc").fetchall()),
    )
    rep['screen'] = screen(db)
    db.execute(f"copy oa_ties to '{OUT}/ties.parquet'")
    db.execute(f"copy cand to '{OUT}/candidates.parquet'")
    db.execute(f"""copy (select t.author, list(t.person) persons, list(p.label) labels from oa_ties t
                   join '{GRAPH}/person.parquet' p on p.key = t.person
                   where t.author not in (select author from clean) group by t.author) to '{OUT}/held-two-persons.parquet'""")
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    for p in (args.show or '').split(','):
        if not p:
            continue
        print(f'\n== {p}')
        for r in db.execute(f"select * from oa_ties where person = '{p}'").fetchall():
            print('  tie', r)
        for r in db.execute(f"select status, year, wtype, title, venue, doi, existing from cand where person = '{p}' order by status, year").fetchall():
            print('  +', r)


PERSON_ANCHOR_ORDER = ('orcid:', 'lcnaf:', 'wd:', 'gnd:', 'viaf:', 'isni:', 'idref:', 'aha-phd:')
KIND = {'article': 'article', 'book-chapter': 'chapter', 'book': 'book', 'dissertation': 'thesis',
        'reference-entry': 'chapter', 'other': 'other'}


def propose(args):
    import duckdb
    sys.path.insert(0, str(ROOT / 'scripts'))
    from identifiers import State, DEFAULT_DIR, materialise
    from namesake_check_groups import given_names_agree
    global M
    m = M = matcher()
    db = duckdb.connect(); db.execute("SET memory_limit = '6GB'")
    C = f"'{OUT}/candidates.parquet'"
    db.execute(f"copy (select * from {C} where wtype in ('book-review', 'review')) to '{OUT}/reviews.parquet'")
    label = dict(db.execute(f"select key, label from '{GRAPH}/person.parquet'").fetchall())
    anchors = dict(db.execute(f"select key, anchors from '{GRAPH}/person.parquet'").fetchall())
    rows = db.execute(f"""select person, author, work, doi, wtype, year, title, venue, name, status, existing from {C}
                          where status in ('add', 'existing?') and wtype not in ('book-review', 'review')""").fetchall()
    state = State.load(DEFAULT_DIR)
    rep, ops, work_new, seen_claim = collections.Counter(), [], {}, set()

    def subject(p):
        an = [a for a in anchors.get(p) or [] if not a.startswith('diss-person:')]
        for pre in PERSON_ANCHOR_ORDER:
            for a in an:
                if a.startswith(pre) and state.anchor.get(a) == p:
                    return a
        for a in an:
            if state.anchor.get(a) == p:
                return a
        return None
    for person, author, work, doi, wtype, year, title, venue, name, status, existing in rows:
        lab = label.get(person) or ''
        if m.family(lab) != oa_family(name) or not given_names_agree(lab, name):
            rep['name_disagrees'] += 1; continue
        if status == 'existing?':
            if doi and f'doi:{doi}' not in state.anchor and existing in state.keys:
                ops.append(dict(event='attach', key=existing, anchors=[f'doi:{doi}'], aliases=[], members=[],
                                basis=f'OpenAlex {work}: the same work as {existing} (title variant) under {person}\'s '
                                      f'OpenAlex author {author}; scripts/openalex_people_works.py'))
                state.anchor[f'doi:{doi}'] = existing
                rep['doi_attached_to_existing'] += 1
            else:
                rep['existing_skipped'] += 1
            continue
        subj = subject(person)
        if not subj:
            rep['person_without_stable_anchor'] += 1; continue
        anc = f'doi:{doi}' if doi else f'openalex:{work}'
        if anc not in state.anchor and anc not in work_new:
            clean = re.sub(r'\s+', ' ', title or '').strip()
            if not clean:
                rep['untitled'] += 1; continue
            work_new[anc] = f'new:w{len(work_new)}'
            mem = [f'kind:{KIND[wtype]}'] + ([f'year:{year}'] if year else [])
            if wtype == 'article' and venue:
                mem.append(f'journal:{venue}')
            ops.append(dict(event='mint', key=work_new[anc], type='work', label=clean[:400], resolution='recorded',
                            anchors=[anc] + ([f'openalex:{work}'] if doi and f'openalex:{work}' not in state.anchor else []),
                            aliases=[], members=mem,
                            basis=f'OpenAlex {work} ({wtype}, {year}); scripts/openalex_people_works.py'))
            rep['works_minted'] += 1
        ca = f"{'doi' if doi else 'openalex'}-authored:{doi or work}:{subj}"
        if ca in state.anchor or ca in seen_claim:
            rep['claim_exists'] += 1; continue
        seen_claim.add(ca)
        ops.append(dict(event='mint', key=f'new:c{len(seen_claim)}', type='claim', label='', resolution='recorded',
                        anchors=[ca], relation=dict(subject=subj, predicate='authored', object=anc),
                        basis=f'OpenAlex author {author} ({name}) wrote {work}; the same OpenAlex author wrote works the '
                              f'graph credits to {person} (identity by works); scripts/openalex_people_works.py'))
        rep['claims'] += 1
        rep['persons'] = rep.get('persons', 0)
    rep['persons'] = len({o['relation']['subject'] for o in ops if o.get('type') == 'claim'})
    print(json.dumps(dict(rep)), flush=True)
    # Shards of contiguous ops, applied in order: a work is minted before its first claim, so each claim's work exists
    # by the time its shard is applied. One proposal for all ~870k ops needed ~18 GB to validate (2026-11-09: WSL at
    # 0 GB free); identifiers.py apply validates each shard as it applies it.
    del state
    args.out.mkdir(parents=True, exist_ok=True)
    size = args.shard
    for n, i in enumerate(range(0, len(ops), size), 1):
        body = json.dumps(dict(basis=f'OpenAlex works of graph people, tied through works the graph already credits to them '
                                     f'(scripts/openalex_people_works.py), shard {n}', decided_by='rule',
                               ops=ops[i:i + size]), ensure_ascii=False) + '\n'
        with gzip.open(args.out / f'proposal-{n:02d}.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
        if n == 1:          # validate the first shard (the rest follow the same code path)
            materialise(State.load(DEFAULT_DIR), dict(basis='dry run', ops=ops[i:i + size]), 'dry-run', 'dry-run')
    rep['shards'] = n
    (args.out / 'report.json').write_text(json.dumps(dict(rep), indent=1) + '\n')
    print('written', len(ops), 'ops in', n, 'shards')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('link', 'report', 'propose'))
    ap.add_argument('--out', type=Path)
    ap.add_argument('--shard', type=int, default=90000, help='ops per proposal shard (propose)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--show')
    args = ap.parse_args()
    dict(link=link, report=report, propose=propose)[args.phase](args)


if __name__ == '__main__':
    main()
