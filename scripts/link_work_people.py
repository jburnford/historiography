"""Printed people on keyed works -> person keys: reviewers, JSTOR article authors, co-authors (2026-11-11).

The graph holds hundreds of thousands of keyed works whose printed reviewers, authors and co-authors are not credited
to the person keys that exist for them (owner, 2026-11-11, from his own page; "the fixes must be general"):
- reviews: 302k works carry `reviewer_names` (JSTOR/Crossref metadata), 96k have a keyed reviewer;
- JSTOR articles: 12% of the 76k JSTOR citing articles have a keyed author (no person was credited when they were keyed);
- co-authors: works that entered through one person's ORCID record or a DOI route credit only that person although the
  OpenAlex record lists more authors.

Roles (one position = one printed name on one keyed work)
  reviewer       work.reviewer_names of a review work; the JSTOR signature (data/field-research/jstor-fulltext-2026-11-06,
                 review-signatures-rules.jsonl.gz on E:) adds the institution printed under the review, grounded to ROR
                 by signature-institutions.csv (accepted strings only, system names refused);
  jstor-author   creators of a JSTOR research article / review essay / review article the graph keys (JSTOR metadata on
                 E:, structured first/last names in order);
  author         authorships of the OpenAlex record (History harvest, or the DOI lookup of graph DOIs outside it) of a
                 keyed work that is neither: full author list in order, ORCID, OpenAlex author id, institutions (ROR).
  Any position also takes ORCID / OpenAlex author id / ROR from the OpenAlex record of the same work when the names agree.

A position is already credited when one of the work's AUTHORED keys (key log) bears a name that agrees with it; those
are the gold rows. The others get a state, with the rule of scripts/link_cited_work_authors.py (imported, not edited):
  exact     ORCID on the record is on a key (name and dates guarded: OpenAlex profiles mix people)
  linked    the rule holds: one dated name-compatible key and a rare name, or a second independent fact (printed
            institution ROR = a DATED affiliation of the key; a key credited on the same work is its known co-author;
            OpenAlex author id tied to the key; the work cites the key's works)
  possible  name-compatible keys, rule not satisfied
  none      no keyed person bears a compatible name
Added here (measured on gold and namesake tests like everything else):
  'duplicate-group': the live candidates are provably one person on several keys (same family and given names word
  for word, no conflicting LC authority / ORCID / not-same mark, no PhD years apart, career windows compatible): they
  are judged as one candidate (facts and spans pooled); if the rule holds, the credit goes to the group's
  representative (an identifier-bearing key, else the key with most works) and the group is written to
  candidate-duplicates.csv.gz for merging. State `linked`, branch prefixed 'dupgroup:'.
Evidence hygiene (Fable review 2026-11-07, owner 2026-11-07): affiliations used as placing facts must be dated and
come from independent sources (AHA directory/advisor, IHR, ORCID, Wikidata; NOT review_credit or jstor_signature,
which earlier automated reviewer links produced); no link made in this run is evidence for another in the same run.

Subcommands
  extract     stream E: (OpenAlex harvest + DOI lookup records, JSTOR metadata) for the graph's works -> SCRATCH
  positions   build the positions table (SCRATCH/positions.parquet) with credited keys
  link        features, rule, gold / namesake evaluation, outputs in OUT (links, report, sizing, duplicates)

Reads build/graph, the key-log cache read-only, E: read-only. Writes no proposal and touches no key log.
"""
import argparse
import csv
import glob
import gzip
import json
import multiprocessing as mp
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

GRAPH = Path(os.environ.get('WP_GRAPH', ROOT / 'build/graph'))
OUT = ROOT / 'data/identifiers/work-people-2026-11-11'
LC_TIES = ROOT / 'data/graph/lc-authority-ties.csv.gz'   # key_lc_authority_ties.py (class 34): authorities tied by evidence
SCRATCH = Path(os.environ.get('WP_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/workpeople'))
HARVEST = Path('/mnt/e/openalex-history-2026-11-08/history')
DOILOOK = Path('/mnt/e/openalex-people-2026-11-09/doi-lookup')
OA_ROWS = '/mnt/e/openalex-people-2026-11-09/rows/*.parquet'
JSTOR_META = '/mnt/e/jstor_metadata_2026-10-23.jsonl.gz'
JSTOR_RECORDS = '/mnt/e/JSTOR_history_citation_graph/records.sqlite'
SIGNATURES = '/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz'
SIG_INST = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/signature-institutions/signature-institutions.csv'
JSTOR_GENRES = ('research_article_as_deposited', 'review_essay_as_deposited', 'review_article_as_deposited')
ID_RE = re.compile(r'"id":\s*"https://openalex\.org/W(\d+)"')


def duck():
    import duckdb
    tmp = SCRATCH / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB'; SET temp_directory='{tmp}';"
               " SET enable_progress_bar=false")
    return db


# ---------------------------------------------------------------- extract

def _oa_one(args):
    path, want_file, out = args
    want = set(open(want_file).read().split())
    n = 0
    with gzip.open(path, 'rt', encoding='utf-8') as f, open(out, 'w', encoding='utf-8') as o:
        for line in f:
            m = ID_RE.search(line, 0, 200)
            if not m or m.group(1) not in want:
                continue
            d = json.loads(line)
            auths = []
            for i, a in enumerate(d.get('authorships') or []):
                au = a.get('author') or {}
                auths.append(dict(
                    pos=i, author=(au.get('id') or '').rsplit('/', 1)[-1], name=au.get('display_name'),
                    raw=a.get('raw_author_name'), orcid=(au.get('orcid') or a.get('raw_orcid') or '').rsplit('/', 1)[-1],
                    rors=[(x.get('ror') or '').rsplit('/', 1)[-1] for x in a.get('institutions') or [] if x.get('ror')],
                    insts=[x.get('display_name') for x in a.get('institutions') or [] if x.get('display_name')],
                    raw_aff=(a.get('raw_affiliation_strings') or [])[:3]))
            src = ((d.get('primary_location') or {}).get('source') or {})
            o.write(json.dumps(dict(work='W' + m.group(1), doi=(d.get('doi') or '').replace('https://doi.org/', '').lower(),
                                    year=d.get('publication_year'), type=d.get('type'), title=(d.get('title') or '')[:300],
                                    venue=src.get('display_name'), authorships=auths,
                                    refs=[r.rsplit('/', 1)[-1] for r in d.get('referenced_works') or []]),
                               ensure_ascii=False) + '\n')
            n += 1
    return path.name, n


def extract(args):
    """OpenAlex records of graph works (by DOI or openalex anchor) -> SCRATCH/oa/*.jsonl; JSTOR metadata creators of
    graph works -> SCRATCH/jstor-creators.jsonl."""
    db = duck()
    G = GRAPH
    # graph DOIs and OpenAlex ids
    db.execute(f"""CREATE TABLE ga AS SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet')
                   WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%' OR a LIKE 'jstor-item:%'""")
    db.execute(f"""CREATE TABLE want AS SELECT DISTINCT r.work FROM read_parquet('{OA_ROWS}', union_by_name=true) r
                   WHERE ('doi:' || lower(r.doi)) IN (SELECT a FROM ga) OR ('openalex:' || r.work) IN (SELECT a FROM ga)""")
    ids = [w[1:] for (w,) in db.execute('SELECT work FROM want').fetchall()]
    print(len(ids), 'OpenAlex records wanted', flush=True)
    out = SCRATCH / 'oa'
    out.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'want.txt').write_text('\n'.join(ids))
    if not args.skip_oa:
        files = sorted(HARVEST.glob('*.jsonl.gz')) + sorted(DOILOOK.glob('part-*.jsonl.gz'))
        jobs = [(p, str(SCRATCH / 'want.txt'), str(out / (p.parent.name + '-' + p.name.replace('.jsonl.gz', '.jsonl'))))
                for p in files]
        tot = 0
        with mp.get_context('fork').Pool(args.workers) as pool:
            for name, n in pool.imap_unordered(_oa_one, jobs):
                tot += n
        print('OpenAlex records extracted', tot, flush=True)
    # JSTOR: graph works anchored on a JSTOR record's DOI or item id
    c = sqlite3.connect(f'file:{JSTOR_RECORDS}?mode=ro', uri=True)
    rec = {}
    for iid, doi, genre, year, journal in c.execute("SELECT item_id, doi, genre, year, journal_title FROM records WHERE included"):
        rec[iid] = (doi.strip().lower() if doi else '', genre, year, journal)
    anchors = {a: k for k, a in db.execute('SELECT key, a FROM ga').fetchall()}
    keep = {}
    for iid, (doi, genre, year, journal) in rec.items():
        k = anchors.get('doi:' + doi) if doi else None
        k = k or anchors.get('jstor-item:' + iid)
        if k:
            keep[iid] = (k, doi, genre, year, journal)
    print(len(keep), 'JSTOR records keyed in the graph', flush=True)
    import subprocess
    import orjson
    p = subprocess.Popen(['zcat', JSTOR_META], stdout=subprocess.PIPE, bufsize=1 << 20)
    n = 0
    with open(SCRATCH / 'jstor-creators.jsonl', 'w', encoding='utf-8') as o:
        for line in p.stdout:
            d = orjson.loads(line)
            iid = d.get('item_id')
            if iid not in keep:
                continue
            k, doi, genre, year, journal = keep[iid]
            cr = sorted(d.get('creators') or [], key=lambda x: x.get('order') or 0)
            names = []
            for x in cr:
                fn = re.sub(r'<[^>]+>[^<]*</[^>]+>', ' ', x.get('first_name') or '').strip()
                ln = re.sub(r'<[^>]+>[^<]*</[^>]+>', ' ', x.get('last_name') or '').strip()
                if ln or fn:
                    names.append((fn + ' ' + ln).strip())
            o.write(json.dumps(dict(iid=iid, work=k, doi=doi, genre=genre, year=year, journal=journal, names=names),
                               ensure_ascii=False) + '\n')
            n += 1
    print('JSTOR creators written', n, flush=True)



# ---------------------------------------------------------------- positions

from link_cited_work_authors import forms, name_level, initial_only, nfold   # noqa: E402


def agree_level(name_a, name_b):
    """best name agreement between two printed names ('full' > 'variant' > 'initial' > 'surname-variant'), or None"""
    best = None
    order = ('full', 'variant', 'initial')
    for f, _, g in forms(name_a):
        for f2, _, g2 in forms(name_b):
            if f == f2:
                lev = name_level(g, g2)
                if lev and (best is None or order.index(lev) < order.index(best)):
                    best = lev
    return best


def positions(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = duck()
    G = GRAPH
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    orcid_of = defaultdict(set)
    for k, o in db.execute(f"SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'orcid:%'").fetchall():
        orcid_of[k].add(o[6:])
    authors = defaultdict(list)
    for k, w in db.execute(f"""SELECT DISTINCT "from", "to" FROM {keylog(G, 'authored')}""").fetchall():
        authors[w].append(k)
    work = {}
    for k, kind, year, journal, rn, title in db.execute(f"""SELECT key, kind, year, journal, reviewer_names, label
            FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed'""").fetchall():
        work[k] = (kind, year, journal, rn, title)
    anchors = {a: k for k, a in db.execute(f"""SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet'
            WHERE resolution <> 'unkeyed') WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%'""").fetchall()}
    # OpenAlex records of graph works
    oa_by_work = defaultdict(list)
    refs = {}
    for fn in sorted((SCRATCH / 'oa').glob('*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            k = anchors.get('doi:' + r['doi']) if r['doi'] else None
            k = k or anchors.get('openalex:' + r['work'])
            if k:
                if not any(x['work'] == r['work'] for x in oa_by_work[k]):
                    oa_by_work[k].append(dict(work=r['work'], year=r['year'], type=r['type'], venue=r['venue'],
                                              authorships=r['authorships'], n=len(r['authorships'])))
                    refs[r['work']] = r['refs']
    print(len(oa_by_work), 'graph works with an OpenAlex record', flush=True)
    # JSTOR creators and signatures
    jst, iid_of = {}, {}
    for line in open(SCRATCH / 'jstor-creators.jsonl', encoding='utf-8'):
        r = json.loads(line)
        iid_of[r['work']] = r['iid']
        if r['genre'] in JSTOR_GENRES:
            jst[r['work']] = r
    from key_review_credit_merges import is_system
    sig_ror = {}
    with open(SIG_INST, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['decision'] == 'accepted' and r['ror'] and not is_system(r['ror_name'] or '') and not is_system(r['string']):
                sig_ror[r['string']] = (r['ror'].rsplit('/', 1)[-1], r['ror_name'])
    want_iid = {iid_of[w] for w, v in work.items() if v[3] and w in iid_of}
    sig = defaultdict(list)
    with gzip.open(SIGNATURES, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r['iid'] in want_iid:
                sig[r['iid']].append(r)
    print(len(jst), 'JSTOR articles keyed;', len(sig), 'signed reviews', flush=True)

    rows = []

    def enrich(row, w):
        """ORCID / OpenAlex author / ROR from the OpenAlex record of the same work, matched by name."""
        for rec in oa_by_work.get(w, ()):
            best = None
            for a in rec['authorships']:
                lev = agree_level(row['name'], a['raw'] or a['name'] or '') or agree_level(row['name'], a['name'] or '')
                if lev in ('full', 'variant') or lev == 'initial' and len(rec['authorships']) == 1:
                    best = a
                    break
            if best:
                row.update(orcid=best['orcid'] or '', oa_author=best['author'] or '', rors=best['rors'],
                           insts=best['insts'], raw_aff=best['raw_aff'], oa_work=rec['work'])
                return

    def credit(row, w):
        ks = authors.get(w, ())
        hit = [k for k in ks if row['orcid'] and row['orcid'] in orcid_of.get(k, ())]
        if hit:
            row.update(credited=hit[0], credited_how='orcid')
            return
        order = ('full', 'variant', 'initial')
        best = None
        for k in ks:
            lev = agree_level(row['name'], label.get(k, ''))
            if lev and (best is None or order.index(lev) < order.index(best[1])):
                best = (k, lev)
        if best:
            row.update(credited=best[0], credited_how='name:' + best[1])

    def base(role, source, w, pos, n, name):
        kind, year, journal, rn, title = work[w]
        return dict(role=role, source=source, work=w, pos=pos, n_auth=n, name=name, year=year, journal=journal or '',
                    kind=kind or '', title=(title or '')[:200], orcid='', oa_author='', rors=[], insts=[], raw_aff=[],
                    oa_work='', inst_printed='', inst_ror='', inst_ror_name='', sig_conf=0.0, credited='', credited_how='')
    done = set()
    for w, (kind, year, journal, rn, title) in work.items():
        if rn:
            done.add(w)
            sigs = sig.get(iid_of.get(w), [])
            for i, nm in enumerate(rn):
                row = base('reviewer', 'jstor-review' if w in iid_of else 'review', w, i, len(rn), nm)
                for s in sigs:
                    if s.get('institution') and (s['creator'] == nm or agree_level(nm, s['creator']) == 'full'):
                        row['inst_printed'] = s['institution'][:200]
                        row['sig_conf'] = s.get('conf') or 0.0
                        if s['institution'] in sig_ror:
                            row['inst_ror'], row['inst_ror_name'] = sig_ror[s['institution']]
                enrich(row, w)
                credit(row, w)
                rows.append(row)
        elif w in jst:
            done.add(w)
            ns = jst[w]['names']
            for i, nm in enumerate(ns):
                row = base('jstor-author', 'jstor', w, i, len(ns), nm)
                enrich(row, w)
                credit(row, w)
                rows.append(row)
    for w, recs in oa_by_work.items():
        if w in done or w not in work:
            continue
        rec = max(recs, key=lambda r: r['n'])
        for a in rec['authorships']:
            nm = a['name'] or a['raw'] or ''
            if a['raw'] and forms(nm) and initial_only(forms(nm)[0][2]) and forms(a['raw']) and not initial_only(forms(a['raw'])[0][2]):
                nm = a['raw']
            if not nm:
                continue
            row = base('author', 'openalex', w, a['pos'], rec['n'], nm)
            row.update(orcid=a['orcid'] or '', oa_author=a['author'] or '', rors=a['rors'], insts=a['insts'],
                       raw_aff=a['raw_aff'], oa_work=rec['work'])
            credit(row, w)
            rows.append(row)
    # one credited key per position: when two positions agree with one key, the better agreement keeps it
    by = defaultdict(list)
    for i, r in enumerate(rows):
        if r['credited']:
            by[r['work'], r['credited']].append(i)
    rank = lambda r: (0 if r['credited_how'] == 'orcid' else 1 + ('full', 'variant', 'initial').index(r['credited_how'][5:]), r['pos'])
    for ids in by.values():
        if len(ids) > 1:
            for i in sorted(ids, key=lambda i: rank(rows[i]))[1:]:
                rows[i]['credited'], rows[i]['credited_how'] = '', ''
    for i, r in enumerate(rows):
        r['pid'] = i
    t = pa.Table.from_pylist(rows)
    pq.write_table(t, SCRATCH / 'positions.parquet')
    with open(SCRATCH / 'oa-refs.jsonl', 'w') as f:
        for k, v in refs.items():
            if v:
                f.write(json.dumps([k, v]) + '\n')
    print(Counter((r['role'], bool(r['credited'])) for r in rows))


# ---------------------------------------------------------------- Crossref author lists (DOIs no OpenAlex record covers)

CROSSREF = Path('/mnt/e/crossref-refs-2026-11-08')
DOI_RE = re.compile(r'^\{"DOI": "([^"]+)"')


def _cr_one(args):
    path, want_file = args
    want = set(open(want_file).read().split())
    out = []
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            m = DOI_RE.match(line)
            if not m or m.group(1).lower() not in want:
                continue
            d = json.loads(line)
            au = []
            for a in d.get('author') or []:
                nm = ' '.join(x for x in (a.get('given'), a.get('family')) if x) or a.get('name') or ''
                au.append(dict(name=nm, orcid=(a.get('ORCID') or '').rsplit('/', 1)[-1],
                               aff=[x.get('name') for x in a.get('affiliation') or [] if x.get('name')][:2]))
            out.append(dict(doi=m.group(1).lower(), authors=au))
    return out


def crossref(args):
    """Author lists from the Crossref harvest (E:, 4.43M journal articles) for the graph's DOI works that no
    OpenAlex record we hold covers (not JSTOR's 10.2307 DOIs: the JSTOR metadata names their authors). Appends
    positions (role author, source crossref) to SCRATCH/positions-crossref.parquet, credited like the others."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = duck()
    G = GRAPH
    S = SCRATCH
    db.execute(f"""CREATE TABLE d AS SELECT DISTINCT key, substr(a, 5) doi FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet'
                   WHERE resolution <> 'unkeyed') WHERE a LIKE 'doi:%' AND a NOT LIKE 'doi:10.2307/%'""")
    db.execute(f"CREATE TABLE p AS SELECT DISTINCT work FROM '{S}/positions.parquet'")
    want = db.execute("SELECT key, doi FROM d WHERE key NOT IN (SELECT work FROM p)").fetchall()
    key_of = defaultdict(list)
    for k, doi in want:
        key_of[doi].append(k)
    (S / 'cr-want.txt').write_text('\n'.join(key_of))
    print(len(key_of), 'DOIs wanted', flush=True)
    files = sorted(CROSSREF.glob('journal_*.jsonl.gz'))
    recs = {}
    with mp.get_context('fork').Pool(args.workers) as pool:
        for n, out in enumerate(pool.imap_unordered(_cr_one, [(f, str(S / 'cr-want.txt')) for f in files], chunksize=20)):
            for r in out:
                recs[r['doi']] = r['authors']
            if n % 2000 == 0:
                print(n, len(recs), flush=True)
    print(len(recs), 'Crossref records found', flush=True)
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    orcid_of = defaultdict(set)
    for k, o in db.execute(f"SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'orcid:%'").fetchall():
        orcid_of[k].add(o[6:])
    keys = sorted({k for doi in recs for k in key_of[doi]})
    db.register('kk', db.execute('SELECT unnest(?) AS key', [keys]).df())
    work = {k: v for k, *v in db.execute(f"SELECT w.key, w.kind, w.year, w.journal, w.label FROM '{G}/work.parquet' w JOIN kk USING (key)").fetchall()}
    authors = defaultdict(list)
    for k, w in db.execute(f"SELECT DISTINCT a.\"from\", a.\"to\" FROM {keylog(G, 'authored')} a JOIN kk ON kk.key = a.\"to\"").fetchall():
        authors[w].append(k)
    base_pid = db.execute(f"SELECT max(pid) + 1 FROM '{S}/positions.parquet'").fetchone()[0]
    rows = []
    for doi, au in recs.items():
        for w in key_of[doi]:
            if w not in work:
                continue
            kind, year, journal, title = work[w]
            got = set()
            for i, a in enumerate(au):
                if not a['name']:
                    continue
                row = dict(role='author', source='crossref', work=w, pos=i, n_auth=len(au), name=a['name'], year=year,
                           journal=journal or '', kind=kind or '', title=(title or '')[:200], orcid=a['orcid'], oa_author='',
                           rors=[], insts=[], raw_aff=a['aff'], oa_work='', inst_printed=(a['aff'][0] if a['aff'] else '')[:200],
                           inst_ror='', inst_ror_name='', sig_conf=0.0, credited='', credited_how='')
                hit = [k for k in authors.get(w, ()) if a['orcid'] and a['orcid'] in orcid_of.get(k, ())]
                if hit:
                    row.update(credited=hit[0], credited_how='orcid')
                else:
                    best = None
                    for k in authors.get(w, ()):
                        lev = agree_level(a['name'], label.get(k, ''))
                        if lev and (best is None or ('full', 'variant', 'initial').index(lev) < ('full', 'variant', 'initial').index(best[1])):
                            best = (k, lev)
                    if best:
                        row.update(credited=best[0], credited_how='name:' + best[1])
                if row['credited'] in got:
                    row.update(credited='', credited_how='')
                got.add(row['credited'])
                row['pid'] = base_pid + len(rows)
                rows.append(row)
    schema = pq.read_schema(S / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), S / 'positions-crossref.parquet')
    print(len(rows), 'Crossref positions;', Counter(bool(r['credited']) for r in rows))


# ---------------------------------------------------------------- OpenAlex records matched by title (works with no DOI)

def titlematch(args):
    """Works that entered from one person's ORCID record with no DOI (kind 'other', no journal) have no identifier an
    OpenAlex record shares; openalex_people_works matched OpenAlex records to them by title, year and an author's
    family name ('strong', 'title+year'). Their authorships give the co-authors (Maitland's Moment, W2940871095).
    Extracts those records from E: and appends positions (role author, source openalex-title) to
    SCRATCH/positions-title.parquet, credited like the others."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = duck()
    G = GRAPH
    S = SCRATCH
    db.execute(f"CREATE TABLE pw AS SELECT DISTINCT work FROM '{S}/positions*.parquet'")
    m = db.execute(f"""SELECT DISTINCT r.work, r.graph_work FROM read_parquet('{OA_ROWS}', union_by_name=true, filename=true) r
            JOIN '{G}/work.parquet' w ON w.key = r.graph_work
            WHERE r.graph_work <> '' AND r.match IN ('strong', 'title+year') AND r.filename NOT LIKE '%dissertations%'
              AND w.kind <> 'thesis' AND r.graph_work NOT IN (SELECT work FROM pw)""").fetchall()
    g_of = defaultdict(set)
    for oa, g in m:
        g_of[oa].add(g)
    g_of = {oa: gs for oa, gs in g_of.items() if len(gs) == 1}           # one graph work per record
    n_of = Counter(next(iter(gs)) for gs in g_of.values())
    print(len(g_of), 'records for', len(n_of), 'works', flush=True)
    out = S / 'oa-title'
    out.mkdir(parents=True, exist_ok=True)
    (S / 'want-title.txt').write_text('\n'.join(w[1:] for w in g_of))
    files = sorted(HARVEST.glob('*.jsonl.gz')) + sorted(DOILOOK.glob('part-*.jsonl.gz'))
    jobs = [(p, str(S / 'want-title.txt'), str(out / (p.parent.name + '-' + p.name.replace('.jsonl.gz', '.jsonl')))) for p in files]
    with mp.get_context('fork').Pool(args.workers) as pool:
        tot = sum(n for _, n in pool.imap_unordered(_oa_one, jobs))
    print('extracted', tot, flush=True)
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    orcid_of = defaultdict(set)
    for k, o in db.execute(f"SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'orcid:%'").fetchall():
        orcid_of[k].add(o[6:])
    keys = sorted({next(iter(gs)) for gs in g_of.values()})
    db.register('kk', db.execute('SELECT unnest(?) AS key', [keys]).df())
    work = {k: v for k, *v in db.execute(f"SELECT w.key, w.kind, w.year, w.journal, w.label FROM '{G}/work.parquet' w JOIN kk USING (key)").fetchall()}
    authors = defaultdict(list)
    for k, w in db.execute(f"SELECT DISTINCT a.\"from\", a.\"to\" FROM {keylog(G, 'authored')} a JOIN kk ON kk.key = a.\"to\"").fetchall():
        authors[w].append(k)
    base_pid = db.execute(f"SELECT max(pid) + 1 FROM '{S}/positions*.parquet'").fetchone()[0]
    best = {}
    for fn in sorted(out.glob('*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            w = next(iter(g_of.get(r['work'], {None})))
            if w in work and (w not in best or len(r['authorships']) > len(best[w]['authorships'])):
                best[w] = r
    rows = []
    for w, r in best.items():
        kind, year, journal, title = work[w]
        got = set()
        for a in r['authorships']:
            nm = a['name'] or a['raw'] or ''
            if a['raw'] and forms(nm) and initial_only(forms(nm)[0][2]) and forms(a['raw']) and not initial_only(forms(a['raw'])[0][2]):
                nm = a['raw']
            if not nm:
                continue
            row = dict(role='author', source='openalex-title', work=w, pos=a['pos'], n_auth=len(r['authorships']), name=nm, year=year,
                       journal=journal or '', kind=kind or '', title=(title or '')[:200], orcid=a['orcid'] or '', oa_author=a['author'] or '',
                       rors=a['rors'], insts=a['insts'], raw_aff=a['raw_aff'], oa_work=r['work'], inst_printed='', inst_ror='', inst_ror_name='',
                       sig_conf=0.0, credited='', credited_how='')
            hit = [k for k in authors.get(w, ()) if row['orcid'] and row['orcid'] in orcid_of.get(k, ())]
            if hit:
                row.update(credited=hit[0], credited_how='orcid')
            else:
                b = None
                for k in authors.get(w, ()):
                    lev = agree_level(nm, label.get(k, ''))
                    if lev and (b is None or ('full', 'variant', 'initial').index(lev) < ('full', 'variant', 'initial').index(b[1])):
                        b = (k, lev)
                if b:
                    row.update(credited=b[0], credited_how='name:' + b[1])
            if row['credited'] and row['credited'] in got:
                row.update(credited='', credited_how='')
            got.add(row['credited'])
            row['pid'] = base_pid + len(rows)
            rows.append(row)
    schema = pq.read_schema(S / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), S / 'positions-title.parquet')
    print(len(rows), 'positions on', len(best), 'works;', Counter(bool(r['credited']) for r in rows))


# ---------------------------------------------------------------- link

import link_cited_work_authors as L   # noqa: E402
L.GRAPH = GRAPH      # WP_GRAPH (a check build) for the linker's People too (2026-11-12)
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)
keylog_sql = keylog

_name_level_base = L.name_level


def name_level_wp(gs, gk):
    """link_cited_work_authors.name_level, plus one refusal (2026-11-11, owner's page): a name printed as initial(s) and
    then a written given name ('J. Garry Clifford', 'J. Candace Clifford') is a person who goes by that written name; it
    agrees with a key whose first given name is written only when the key also carries that name (or its initial)
    after it. 'J. Garry' is not 'Jim'; it may be 'John Garry' or 'J. G.'."""
    lev = _name_level_base(gs, gk)
    if lev != 'initial' or not gs or not gk:
        return lev
    for x, y in ((list(gs), list(gk)), (list(gk), list(gs))):
        if len(x[0]) == 1 and len(y[0]) > 1:
            i = next((j for j, w in enumerate(x) if len(w) > 1), None)
            if i is not None and not any(w == x[i] or (len(w) == 1 and x[i].startswith(w)) or L._close(w, x[i]) for w in y[1:]):
                return None
    return lev


L.name_level = name_level_wp        # the linker's candidates() reads it from its module at call time
name_level = name_level_wp


def date_filter(p, fe, P):
    """Candidates the dates rule out (the work outside the key's career window by the rule's own date test: life
    years, PhD, dated works) are not candidates at all (owner 2026-11-11: possible rows listed a 2000- key for 1973
    reviews). -> (features without them, keys excluded)."""
    out = []
    for k, c in fe.get('cands', {}).items():
        ok, how = L.date_test(c, p['year'], p['book'], P)
        if not ok and str(how).startswith('out-of-window'):
            out.append(k)
    if not out:
        return fe, out
    return dict(fe, cands={k: c for k, c in fe['cands'].items() if k not in out}), out

INDEPENDENT_AFF = ('aha_directory', 'aha_advisor', 'ihr', 'orcid', 'wikidata', 'lc_373')
HIDE = [None]          # (work, key) whose credit is hidden in a gold test; facts from that work are hidden with it


class HideSpan:
    """People.span / span_short with the hidden work left out of the hidden key's works."""
    def __init__(self, orig, kw, short):
        self.orig, self.kw, self.short = orig, kw, short

    def get(self, k, default=None):
        h = HIDE[0]
        if h and h[1] == k:
            ys = [(y, kind) for y, kind, w in self.kw.get(k, ()) if w != h[0]]
            if self.short:
                ys = [y for y, kind in ys if kind in ('article', 'review', 'thesis', 'chapter')]
                return (min(ys), max(ys)) if ys else default
            ys = [y for y, _ in ys]
            return (min(ys), max(ys), len(ys)) if ys else default
        return self.orig.get(k, default)


class HideCoauth:
    def __init__(self, pairs):
        self.pairs = pairs

    def __contains__(self, ab):
        ws = self.pairs.get(ab)
        if not ws:
            return False
        h = HIDE[0]
        if h and h[1] in ab and h[0] in ws:
            return len(ws) > 1
        return True


class HideTies:
    """OpenAlex author id -> {key: (works, first year, last year)} through works the key log credits to the key
    (the authorship's name agreeing with the key's: openalex_people_works ties); ids tied to two keys dropped."""
    def __init__(self, ties):
        self.ties = ties

    def get(self, a, default=None):
        d = self.ties.get(a)
        if d is None:
            return default if default is not None else {}
        h = HIDE[0]
        out = {}
        for k, ws in d.items():
            ys = [y for w, y in ws if not (h and h[1] == k and h[0] == w)]
            if ys:
                out[k] = (len(ys), min(y for y in ys if y) if any(ys) else None, max(y for y in ys if y) if any(ys) else None)
        return out


APOS = str.maketrans({'\u2019': "'", '\u2018': "'", '\u02bc': "'", '`': "'", '\u00b4': "'"})


def apos(s):
    """one apostrophe: the linker's folding drops a curly one ('O\u2019Neill' -> oneill) but splits on a straight one
    ('O'Neill' -> neill), so the same name printed two ways lands in two families (2026-11-11, gold test)"""
    return (s or '').translate(APOS)


class WPPeople(L.People):
    def __init__(self, db):
        super().__init__(db)
        # 2026-11-12 (class 34): an LC authority tied to the key by evidence but not yet anchored
        # (data/graph/lc-authority-ties.csv.gz, scripts/key_lc_authority_ties.py) is the key's own: it no longer counts
        # as a namesake in the rarity tests (own_lc) and a different authority on a source is refused (lcnaf-differs).
        # Linked evidence, not key-log: it is not added to lc_key, so it never makes an 'exact' identifier credit.
        self.lc_tied = defaultdict(set)
        if LC_TIES.exists() and not os.environ.get('WP_NO_LC_TIES'):
            with gzip.open(LC_TIES, 'rt', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    if r['person'] in self.lcnaf and not self.lc_key.get(r['lcnaf']):
                        self.lc_tied[r['person']].add(r['lcnaf'])
                        self.lcnaf[r['person']] = self.lcnaf[r['person']] | {r['lcnaf']}
        self.index = defaultdict(list)
        for k, lab in self.label.items():
            for f, form, g in forms(apos(lab)):
                self.index[f].append((k, form, g))
        # 2026-11-12 (class 37): stated alternate family-name forms (data/graph/name-form-ties.csv.gz) make candidates only
        L.add_name_form_ties(self, apos)
        self.tied_form = {(k, f): src for (k, form), src in self.tied_kform.items() for f in [form.split(',')[0]]}
        G = GRAPH
        from key_review_credit_merges import is_system
        # placing facts: dated affiliations from independent sources only (no review-credit / signature routes)
        self.aff = defaultdict(list)
        src = ','.join(f"'{s}'" for s in INDEPENDENT_AFF)
        for k, ror, label, fy, ly in db.execute(f"""SELECT a."from", i.ror, i.label, a.first_year, a.last_year
                FROM '{G}/affiliated_with.parquet' a JOIN '{G}/institution.parquet' i ON i.key = a."to"
                WHERE i.ror IS NOT NULL AND a.source IN ({src}) AND (a.first_year IS NOT NULL OR a.last_year IS NOT NULL)""").fetchall():
            if not is_system(label or ''):
                self.aff[k].append((ror.rsplit('/', 1)[-1], label, fy, ly))
        kw = defaultdict(list)
        for k, y, kind, w in db.execute(f"""SELECT a."from", w.year, w.kind, w.key FROM (SELECT "from", "to" FROM {keylog(G, 'authored')}
                UNION SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to"
                WHERE w.year BETWEEN 1000 AND 2027""").fetchall():
            kw[k].append((y, kind, w))
        self.kw = kw
        self.span = HideSpan(self.span, kw, False)
        self.span_short = HideSpan(self.span_short, kw, True)
        pairs = {}
        for a, b, ws in db.execute(f"SELECT \"from\", \"to\", work_keys FROM {keylog(G, 'coauthored')}").fetchall():
            pairs[a, b] = pairs[b, a] = frozenset(ws)
        self.coauth = HideCoauth(pairs)
        ties = defaultdict(lambda: defaultdict(list))
        for a, p, w, y in db.execute(f"""SELECT DISTINCT r.author, r.person, g.key, r.year FROM read_parquet('{OA_ROWS}', union_by_name=true) r
                JOIN '{G}/work.parquet' g ON g.key = r.graph_work
                JOIN {keylog(G, 'authored')} au ON au."from" = r.person AND au."to" = r.graph_work
                WHERE r.tie LIKE '%work%' AND r.person <> ''""").fetchall():
            ties[a][p].append((w, y))
        self.ties = HideTies({a: dict(v) for a, v in ties.items() if len(v) == 1})
        # pass eight (2026-11-12): keys with scholarly evidence: a PhD year (AHA record, key-log thesis), a dissertation
        # corpus author or AHA directory anchor, a supervision, a dated directory affiliation (AHA directory, IHR staff list)
        self.scholar = set(self.phd)
        for k, an in db.execute(f"SELECT key, anchors FROM '{G}/person.parquet'").fetchall():
            if any(a.startswith(('aha-phd:', 'aha:', 'diss-author:')) for a in an or ()):
                self.scholar.add(k)
        for (k,) in db.execute(f"""SELECT DISTINCT "from" FROM '{G}/supervised.parquet' UNION
                SELECT DISTINCT "from" FROM '{G}/affiliated_with.parquet' WHERE source IN ('aha_directory', 'ihr')""").fetchall():
            self.scholar.add(k)


# ---------------------------------------------------------------- pass eight: the single-candidate, no-fact class
# (2026-11-12, ARCHITECTURE.md section 8 class 38). A position whose only surviving candidate fits the dates but has no
# confirming fact and a name that is not rare stays `possible`. Three candidate rules were measured on masked gold, the
# masked-author namesake test and the clerical labels (data/graph/scored-links/clerical-labels.csv); single_extras()
# computes their inputs for every such position and writes them to the signals ('x:...'), and a rule links only when
# it is named in P['ADOPT'] (link --adopt).
LCD = {}       # (family, first given) -> [(lcid, birth, death)] of LC authorities with a birth or death year


def _y4(s):
    m = re.search(r'(\d{4})', str(s or ''))
    return int(m.group(1)) if m else None


def lc_dated(db, needed):
    """LC personal-name authorities with a birth or death year, by the rarity key of population_counts (same parse)"""
    out = defaultdict(list)
    cur = db.execute(f"""SELECT lcid, label, birth, death FROM '{L.LC_NAMES}' WHERE NOT deprecated
            AND (coalesce(birth, '') <> '' OR coalesce(death, '') <> '')""")
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for lcid, label, b, d in rows:
            if not label or ',' not in label:
                continue
            fam = label.partition(',')[0]
            f = L.fam_norm(fam)
            g = L.gwords(label)
            if g and (f, g[0]) in needed:
                out[f, g[0]].append((lcid, _y4(b), _y4(d)))
    return out


def lc_impossible(b, d, year, book):
    """an LC namesake who cannot have written a work of this year: under 20 (career_window.ADULT), or, for anything but
    a book (posthumous editions), dead more than two years (AFTER_DEATH) or over 100 with no death year recorded"""
    if b is not None and year < b + L.ADULT:
        return True
    if not book and d is not None and year > d + L.AFTER_DEATH:
        return True
    if not book and d is None and b is not None and year > b + 100:
        return True
    return False


def single_extras(people, p, fe, pop, P, k):
    """inputs of the pass-eight rules for a position whose only live candidate k is dated and carries no contradiction"""
    c = fe['cands'][k]
    if c.get('tied') or c['why'] or not p.get('year'):
        return None
    good, how = L.date_test(c, p['year'], p['book'], P)
    if not good:
        return None
    n_lc, n_oa = pop[0].get(fe['name_key'], 0), pop[1].get(fe['name_key'], 0)
    own = L.own_lc(fe, [k])
    own_ids = set(c.get('klc', ())) | set(p.get('lc') or ())
    book = (p.get('kind') or '') == 'book'
    imp = sum(1 for lcid, b, d in LCD.get(fe['name_key'], ()) if lcid not in own_ids and lc_impossible(b, d, p['year'], book))
    others = max(0, n_lc - own)
    others_dp = max(0, others - imp)
    lev = c['lev']
    name = 'init' if all(len(w) == 1 for w in c['g']) else ('full' if lev == 'full' else lev)
    review_like = p.get('kind') == 'review' or bool(REVIEWISH.search(p['title'] or '')) or p.get('role') == 'reviewer'
    x = dict(others=others, others_dp=others_dp, n_oa=n_oa, name=name, scholar=k in people.scholar,
             venue=fe.get('venue') or 'none', topicv=c.get('topicv', 0.0), win=how,
             author_review=p.get('role') == 'author' and review_like)
    x['bearers'] = max(others + 1, n_oa)
    x['bearers_dp'] = max(others_dp + 1, n_oa)
    x['sig'] = [f"x:lco={others}", f"x:lcdp={others_dp}", f"x:oa={n_oa}", f"x:name={name}",
                'x:scholar' if x['scholar'] else 'x:noscholar', f"x:venue={x['venue']}", f"x:topicv={x['topicv']:.1f}",
                f"x:win={how}"] + (['x:author-review'] if x['author_review'] else [])
    x['fires'] = {
        # (i) namesakes the dates rule out no longer count against rarity
        'unique-rare-dated-namesakes': name == 'full' and others > P['RARE_LC'] and others_dp <= P['RARE_LC'] and n_oa <= P['RARE_OA'],
        # (ii) topic against the volume's title and its sibling chapters' titles as well as the work's own
        'unique-topic-volume': name in ('full', 'variant') and x['topicv'] >= P.get('TOPICV_MIN', 1e9),
        # (iii) a printed full given name, a scholar, a history venue, the career window: no positive fact
        'single-scholar-history-venue': (name == 'full' and x['scholar'] and x['venue'] != 'none' and how in ('life', 'phd')
                                         and not x['author_review'] and x['bearers_dp'] <= P.get('SCHOLAR_MAX_BEARERS', 0)),
    }
    return x


def make_pos(r):
    """a positions row -> the dict link_cited_work_authors.features / rule read"""
    p = dict(src=r['source'], swork=r['oa_work'] or r['work'], work_id=r['work'], oa_id=r['oa_work'], pos=r['pos'],
             role=r['role'], name=apos(r['name']), title=r['title'], year=r['year'], book=False, lc=[], lc_how='',
             orcid=r['orcid'] or '', oa_author=r['oa_author'] or '', rors=list(r['rors'] or []), insts=list(r['insts'] or []),
             raw_aff=list(r['raw_aff'] or []), citing=0, sb=None, sd=None, initial_check='', venue='', oa_type='',
             kind=r.get('kind') or '', journal=r.get('journal') or '')
    if r['inst_ror'] and r['inst_ror'] not in p['rors']:
        p['rors'].append(r['inst_ror'])
    p['forms'] = forms(p['name'])
    return p


def fullform_rare(fe, c, pop, P, live):
    """The printed form 'initial + written given name' ('J. Garry Clifford') agrees in full with the key's, and no
    other LC authority (and few OpenAlex History ids) bears that family + first initial + written name: a person who
    goes by a middle name is as identifiable as one with a rare first name. The linker's full-name rarity only reads
    written first names."""
    if len(pop) < 6 or c.get('lev') not in ('full', 'initial'):     # 'J. Garry' / 'Clifford, J. Garry' agree as 'initial'
        return False
    g, kg, f = c['g'], c['kg'], c['fam']
    if len(g) < 2 or len(g[0]) != 1 or len(kg) < 2 or kg[0][:1] != g[0]:
        return False
    w = next((x for x in g[1:] if len(x) > 1), None)
    if not w or w not in kg:
        return False
    n_lc = pop[2].get((f, g[0], w), 0) + pop[2].get((f, kg[0], w), 0) if len(kg[0]) > 1 else pop[2].get((f, g[0], w), 0)
    n_oa = pop[3].get((f, g[0], w), 0)
    return max(0, n_lc - L.own_lc(fe, live)) <= 0 and n_oa <= P.get('RARE_OA_FULL', 10)


def dup_group(people, cands, fe, pop, P, loose=False):
    """The candidate keys are one person on several keys: their names agree word for word (or one adds only middle
    initials), no two hold different LC authorities / ORCIDs, no not-same mark, PhD years and career starts agree; and
    the name is rare outside the graph or carries two written given names (so namesakes in the wider world are few)."""
    if len(cands) < 2:
        return None
    cs = fe['cands']
    for a in cands:
        for b in cands:
            if a >= b:
                continue
            ga, gb = cs[a]['kg'], cs[b]['kg']
            # a first initial is enough when a written given name follows it on both ('J. Garry')
            if cs[a]['fam'] != cs[b]['fam'] or not ga or not gb or ga[0] != gb[0] or (
                    len(ga[0]) == 1 and not (set(w for w in ga if len(w) > 1) & set(w for w in gb if len(w) > 1))):
                return None
            sh, lo = (ga, gb) if len(ga) <= len(gb) else (gb, ga)
            if tuple(lo[:len(sh)]) != tuple(sh) or any(len(w) > 1 for w in lo[len(sh):]):
                return None
            if b in people.not_same.get(a, ()):
                return None
            for d in (people.lcnaf, people.orcid):
                if d.get(a) and d.get(b) and not d[a] & d[b]:
                    return None
            pa_, pb = people.phd.get(a), people.phd.get(b)
            if pa_ and pb and abs(pa_ - pb) > 1:
                return None
            wa, wb = people.window(a), people.window(b)
            if wa == 'inconsistent' or wb == 'inconsistent':
                return None
            if isinstance(wa, tuple) and isinstance(wb, tuple) and wa[0] and wb[0] and abs(wa[0] - wb[0]) > 5:
                return None
    n_lc, n_oa, rare = L.rarity(fe, pop, P, cands)
    two_given = all(sum(len(w) > 1 for w in cs[k]['kg']) >= 2 for k in cands)
    if not (rare or two_given or loose or fullform_rare(fe, cs[cands[0]], pop, P, cands)):
        return None
    rep = sorted(cands, key=lambda k: (-(bool(people.lcnaf.get(k)) + bool(people.orcid.get(k))),
                                       -((people.span.get(k) or (0, 0, 0))[2]), k))[0]
    return rep


# PhD year minus k as the start of a career window, by role, where under ~0.5% of the key log's dated credits of
# people with a known PhD year fall earlier (measured 2026-11-11 on build/graph, 72,091 keys with a PhD year):
# reviews 0.53% at k=8, 0.45% at k=9; articles 2.2% and books 2.9% even at k=10, so no PhD start for them.
PHD_START = {'reviewer': 9}


def phd_window(people, p, fe):
    """the earliest PhD year on the key (AHA records, thesis works) bounds a reviewer's window from below: PhD - k,
    when later than birth + 20; it never loosens a window"""
    k = PHD_START.get(p['role'])
    if not k:
        return fe
    cands = {}
    for key, c in fe.get('cands', {}).items():
        ph = people.phd.get(key)
        w = c.get('win')
        if ph and not (isinstance(w, tuple) and w[0] is not None and w[0] >= ph - k):
            c = dict(c, win=(ph - k, w[1] if isinstance(w, tuple) else None, 'phd-start'))
        cands[key] = c
    return dict(fe, cands=cands)


TIE_FACTS_EXCLUDED = ('topic', 'oa-author-tie')   # a tied candidate needs a fact about people, not a topic or a profile


def rule_wp(people, p, fe, pop, P, use_dup=True):
    """rule_wp_core, then (class 37) a candidate that came in only through a stated alternate family-name form is marked
    (signal name-form-tie:<source>) and is linked only with a positive fact for this position; a rarity or full-name
    link through a tie is held as possible (branch name-form-tie-no-fact)."""
    st, k, br, cands, sig = rule_wp_core(people, p, fe, pop, P, use_dup)
    tied = {x: c['tied'] for x, c in fe.get('cands', {}).items() if c.get('tied')}
    if not tied:
        return st, k, br, cands, sig
    sig = sig + sorted({'name-form-tie:' + t.split(':')[0] for t in tied.values()})
    if st == 'linked' and k and any(x in tied for x in k.split(';')):
        allowed = (set(P['FACTS']) | set(L.NEW_FACTS) | set(NETWORK_FACTS)) - set(TIE_FACTS_EXCLUDED)
        if not any(f.split(':')[0] in allowed for x in k.split(';') for f in fe['cands'].get(x, {}).get('facts', ())):
            return 'possible', None, 'name-form-tie-no-fact', cands, sig
    return st, k, br, cands, sig


def rule_wp_core(people, p, fe, pop, P, use_dup=True):
    if fe.get('exact'):
        return L.rule(p, fe, pop, P)
    fe = phd_window(people, p, fe)
    fe, gone = date_filter(p, fe, P)
    if gone and not fe['cands']:
        return 'none', None, 'only-date-excluded', [], [f'date-excluded={len(gone)}']
    st, k, br, cands, sig = rule_wp_inner(people, p, fe, pop, P, use_dup)
    sig = sig + ([f'date-excluded={len(gone)}'] if gone else [])
    if st == 'possible' and len(cands) == 1 and not br.startswith('orcid-differs'):
        c = fe['cands'][cands[0]]
        good, how = L.date_test(c, p['year'], p['book'], P)
        if good and not (set(c['why']) - {'orcid-differs'}) and 'orcid-differs' not in c['why'] and fullform_rare(fe, c, pop, P, cands):
            return 'linked', cands[0], 'unique-rare-fullform', cands, sig + [f'date:{how}', 'fullform-rare']
        # pass eight: the single-candidate, no-fact class (single_extras); a rule links only when adopted (link --adopt)
        x = single_extras(people, p, fe, pop, P, cands[0]) if not br.startswith('name-form-tie') else None
        if x:
            sig = sig + x['sig']
            for name in P.get('ADOPT', ()):
                if x['fires'].get(name):
                    return 'linked', cands[0], name, cands, sig + [f"date:{x['win']}"]
    if st == 'possible' and len(cands) > 1 and br == 'several-several-dated' and P.get('ONE_NETWORK_FACT'):
        # 2026-11-12 (Andrew Watson probe): several candidates fit the dates and exactly one of them has a network fact
        # for this position (a co-author, co-editor, advisor / student or dated colleague of someone credited on the work
        # by the key log or an identifier; the volume's editors or other chapters' authors; the candidate edits the
        # volume; a dated printed institution), and no other candidate has any positive fact (an OpenAlex tie included):
        # linked, branch several-dated-one-fact. No contradiction on the one (orcid-differs only with a fact, as rule()).
        def fx(x):
            return {f.split(':')[0] for f in fe['cands'][x]['facts']}
        any_fact = [x for x in cands if fx(x) & (set(P['FACTS']) | set(L.NEW_FACTS))]
        net = [x for x in cands if fx(x) & set(NETWORK_FACTS)]
        if len(net) == 1 and any_fact == net:
            x = net[0]
            c = fe['cands'][x]
            good, how = L.date_test(c, p['year'], p['book'], P)
            if good and not (set(c['why']) - {'orcid-differs'}):
                facts = sorted(f for f in c['facts'] if f.split(':')[0] in NETWORK_FACTS)
                return 'linked', x, 'several-dated-one-fact', cands, sig + [f'date:{how}'] + facts + [f'others={len(cands) - 1}']
    if st == 'possible' and len(cands) > 1:
        # owner 2026-11-11: a candidate is listed only when it is the only one left or has a positive fact for this
        # position; otherwise the position is an ambiguous name, with no rows on anybody's page
        shown = [x for x in cands if [f for f in fe['cands'][x]['facts'] if f.split(':')[0] in P['FACTS'] or f.split(':')[0] in L.NEW_FACTS]]
        if not shown:
            return 'ambiguous', None, br, cands, sig + ['ambiguous-name']
        if len(shown) < len(cands):
            return st, k, br, shown, sig + [f'shown={len(shown)}/{len(cands)}']
    return st, k, br, cands, sig


def rule_wp_inner(people, p, fe, pop, P, use_dup=True):
    st, k, br, cands, sig = L.rule(p, fe, pop, P)
    if st == 'linked' and 'orcid-differs' in fe['cands'][k]['why'] and \
            not [x for x in fe['cands'][k]['facts'] if x.split(':')[0] in P['FACTS'] and x != 'oa-author-tie']:
        # the record prints an ORCID other than the key's, and the only tie is an OpenAlex author id, which carries
        # that other ORCID: two people (orcid-namesake test, 2026-11-11: Fei Chen, Liverpool planner / historian)
        return 'possible', None, 'orcid-differs-tie-only', cands, sig + ['orcid-differs']
    if st != 'possible' or not use_dup or len(cands) < 2:
        return st, k, br, cands, sig
    rep = dup_group(people, cands, fe, pop, P)
    if not rep:
        # the same tests without the rarity condition: listed for merging (candidate-duplicates), nothing credited
        if dup_group(people, cands, fe, pop, P, loose=True):
            return st, k, br, cands, sig + [f'duplicate-candidates={"|".join(sorted(cands))}']
        return st, k, br, cands, sig
    cs = fe['cands']
    c = dict(cs[rep])
    c['facts'] = sorted({f for x in cands for f in cs[x]['facts']})
    c['why'] = sorted({w for x in cands for w in cs[x]['why']})
    spans = [cs[x]['span'] for x in cands if cs[x]['span']]
    c['span'] = (min(s[0] for s in spans), max(s[1] for s in spans), sum(s[2] for s in spans)) if spans else None
    c['win'] = next((cs[x]['win'] for x in [rep] + list(cands) if cs[x]['win']), None)
    c['klc'] = set().union(*[cs[x]['klc'] for x in cands])
    fe2 = dict(fe, cands={rep: c})
    st2, k2, br2, _, sig2 = L.rule(p, fe2, pop, P)
    if st2 != 'linked' and not c['why'] and L.date_test(c, p['year'], p['book'], P)[0] and fullform_rare(fe2, c, pop, P, [rep]):
        st2, k2, br2, sig2 = 'linked', rep, 'unique-rare-fullform', sig2 + ['fullform-rare']
    if st2 == 'linked':
        return 'linked', k2, 'dupgroup:' + br2, cands, sig2 + [f'duplicate-keys={"|".join(sorted(cands))}']
    return st, k, br, cands, sig + [f'duplicate-keys={"|".join(sorted(cands))}']


def stable_half(s):
    return L.stable_half(s)


def tnorm(t):
    t = re.sub(r'^\s*(review of|rev\.? of|reseña|compte rendu|besprechung)[:\s]+', '', (t or '').strip(), flags=re.I)
    t = re.split(r'\s+/\s+|:|\s+—\s+', t)[0]
    w = re.sub(r'[^a-z0-9 ]+', ' ', nfold(t)).split()
    return ' '.join(w[:5]) if len(w) >= 2 else ''      # five words: subtitles are cut at different places


def is_review_title(t):
    return bool(re.match(r'^\s*(review of|rev\.? of|reseña|compte rendu|besprechung)\b', t or '', flags=re.I))


def own_book_check(r, k, book_titles, reviewed_authors):
    """A review record whose printed 'author' is the reviewed book's author (Crossref and OpenAlex review records
    often carry the book's author: Kindleberger 'reviewing' Manias, panics and crashes). -> 'none' when the key
    authored the book this review reviews (REVIEWS edge, or a 'Review of <title>' whose title is the key's own book);
    'possible' when a journal item bears the exact title of the key's own book (a review of it, most often)."""
    ks = set(k.split(';'))
    if ks & reviewed_authors.get(r['work'], set()):
        return 'none', 'author-of-reviewed-book'
    title = r['title'] or ''
    # AHR-style review headings print the book's author first: 'Jacques Nobécourt. Le Colonel de La Rocque ...'
    lead = re.match(r'^\s*([^.:]{3,60})\.\s+(.+)$', title)
    if lead and agree_level(apos(lead.group(1)), apos(r['name'])) in ('full', 'variant'):
        title = 'Review of ' + lead.group(2)
    tn = tnorm(title)
    if tn and ks & book_titles.get(tn, set()):
        if is_review_title(title) or r['role'] == 'reviewer':
            return 'none', 'author-of-reviewed-book'
        if r['kind'] in ('article', 'review', 'other'):
            return 'possible', 'same-title-as-own-book'
    return None


REVIEWISH = re.compile(r'(?i)^\s*review of|\breviews?\b|besprechung|rezension|reseñas?\b|recensioni?\b|comptes? rendus?|léirmheas')


def guard(r, st, k, br, sig, fe, P, book_titles, reviewed_authors, outside):
    """Checks after the rule (hand audit, 2026-11-11): the book's author on a review record; rarity measured in the
    History population does not speak for a work outside it (Amna Khalid, Sharjah), except a review (reviews of
    history books fetched by DOI are history's own population)."""
    if st in ('exact', 'linked') and k:
        x = own_book_check(r, k, book_titles, reviewed_authors)
        if x:
            return x[0], None if x[0] == 'none' else None, x[1], sig + [f'own-book:{k}']
    if st == 'linked' and r['role'] == 'author' and REVIEWISH.search(r['title'] or '') and 'rare' in br:
        # a review record outside the JSTOR reviewer route: its printed 'author' is often the reviewed book's author
        # (hand audit: about half of such rows before the book check, a fifth after it), so rarity alone does not link
        return 'possible', None, 'review-record-rarity-only', sig + ['review-record']
    if st == 'linked' and r['oa_work'] in outside and r['role'] == 'author' and not REVIEWISH.search(r['title'] or ''):
        c = fe['cands'].get(k) or {}
        facts = [f for f in c.get('facts', ()) if f.split(':')[0] in P['FACTS']]
        if not facts and 'rare' in br:
            return 'possible', None, 'outside-history-rarity-only', sig + ['outside-history']
    return st, k, br, sig


def load_positions(limit=None):
    """the positions table (pyarrow), or a sample of about one work in 2*limit"""
    import pyarrow as pa
    import pyarrow.parquet as pq
    t = pq.read_table(SCRATCH / 'positions.parquet')
    for extra in ('positions-crossref.parquet', 'positions-title.parquet', 'positions-extra.parquet'):
        if (SCRATCH / extra).exists():
            t = pa.concat_tables([t, pq.read_table(SCRATCH / extra)])
    if limit:
        keep = [stable_half(w + 'x') == 0 and int(L.hashlib.md5(w.encode()).hexdigest()[:6], 16) % limit == 0
                for w in t.column('work').to_pylist()]
        t = t.filter(pa.array(keep))
    return t


def iter_rows(t, mask=None):
    if mask is not None:
        t = t.filter(mask)
    for b in t.to_batches(50000):
        yield from b.to_pylist()


TOPIC_STOP = set("""history histories historical historiography study studies introduction review reviews essay essays
toward towards through between within without among against during after before since under over into from with their
there these those that this which what when where whose about other others more most some such than then them they very
also only same each both into upon onto vers dans pour avec entre leurs dont sous sans plus mais pero para como entre
sobre desde hasta dans eine einer eines einem einen nach durch unter zwischen gegen ohne uber über""".split())
TOPIC_RE = re.compile(r'[a-z]{4,}')


def topic_terms(title):
    """distinctive words of a title: letters only, accents folded, four letters or more, not a function word"""
    return {t for t in TOPIC_RE.findall(nfold(title or '')) if t not in TOPIC_STOP}


class Topics:
    """2026-11-12 (owner, Labelle probe): topic may SUPPORT a works link, never exclude one. Each person key's profile is
    the words of the titles of its key-log works (thesis included); a position's work title shares words with a
    candidate's profile; the score is the sum of their inverse document frequencies over all graph work titles (Wendat,
    Muskoka weigh; history, Canada do not). The gold test's hidden work is left out of the profile."""
    def __init__(self, db, people):
        import math
        G = GRAPH
        df = Counter()
        n = 0
        cur = db.execute(f"SELECT label FROM '{G}/work.parquet' WHERE label IS NOT NULL")
        while True:
            rows = cur.fetchmany(200000)
            if not rows:
                break
            for (lab,) in rows:
                df.update(topic_terms(lab))
                n += 1
        self.idf = {t: math.log(n / c) for t, c in df.items() if c <= n * 0.002}    # common words carry no weight
        del df
        self.prof = defaultdict(dict)      # key -> {term: number of the key's works with it}
        self.wterms = {}
        for k, w, lab in db.execute(f"""SELECT a."from", a."to", w.label FROM {keylog(G, 'authored')} a
                JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.label IS NOT NULL""").fetchall():
            ts = [t for t in topic_terms(lab) if t in self.idf]
            d = self.prof[k]
            for t in ts:
                d[t] = d.get(t, 0) + 1
        print('topics:', len(self.idf), 'weighted words,', len(self.prof), 'profiles', flush=True)

    def score_terms(self, k, terms, hidden=()):
        d = self.prof.get(k)
        if not d:
            return 0.0
        return sum(self.idf[t] for t in terms if t in d and t in self.idf and not (t in hidden and d[t] <= 1))

    def score(self, k, title, hide_work_title=None):
        d = self.prof.get(k)
        if not d:
            return 0.0, []
        hidden = topic_terms(hide_work_title) if hide_work_title else set()
        shared = [t for t in topic_terms(title) if t in d and t in self.idf and not (t in hidden and d[t] <= 1)]
        return sum(self.idf[t] for t in shared), shared


def nameonly_features(db, people, topic_min=0.0):
    """L.features plus the facts of the name-only class (FACTS_NAMEONLY): pairs from the key log only (COEDITED key-log
    rows, ADVISED from the key log's supervision claims and Wikidata), the volume's people from S/volume-people.parquet.
    The gold test's hidden credit is never among them: volume people are the volume's editors and the other chapters'
    authors."""
    G = GRAPH
    coed = set()
    for a, b in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'coedited')}").fetchall():
        coed.add((a, b))
        coed.add((b, a))
    adv = set()
    for a, b in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'advised')}").fetchall():
        adv.add((a, b))
        adv.add((b, a))
    vp = defaultdict(set)
    ved = defaultdict(set)
    if (SCRATCH / 'volume-people.parquet').exists():
        for w, k, how in db.execute(f"SELECT work, key, how FROM '{SCRATCH}/volume-people.parquet' WHERE work <> ''").fetchall():
            vp[w].add(k)
            if how == 'volume-editor':
                ved[w].add(k)
    print('name-only facts:', len(coed) // 2, 'co-editor pairs,', len(adv) // 2, 'advisor pairs,', len(vp), 'chapters with volume people', flush=True)
    topics = Topics(db, people) if topic_min > 0 else None
    # pass eight: history venues (journal catalogue titles and aliases) and each chapter's volume context (the volume's
    # title and the titles of its other chapters: graph PART_OF of any evidence, and the fetched sibling chapters)
    from key_review_reviewers import journal_key
    hist_j = set()
    with open(ROOT / 'data/journal-catalogue/catalogue.csv', newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            for t in [r['title']] + (r['aliases'] or '').split(' | '):
                jk = journal_key(t) if t else ''
                if jk:
                    hist_j.add(jk)
    vol_of, vol_titles = {}, defaultdict(list)
    for ch, vol, lab, vlab in db.execute(f"""SELECT p."from", p."to", w.label, v.label FROM '{G}/part_of.parquet' p
            LEFT JOIN '{G}/work.parquet' w ON w.key = p."from" LEFT JOIN '{G}/work.parquet' v ON v.key = p."to\"""").fetchall():
        vol_of.setdefault(ch, vol)
        if not vol_titles[vol] and vlab:
            vol_titles[vol].append(vlab)
        if lab:
            vol_titles[vol].append(lab)
    if (SCRATCH / 'sibling-chapters.parquet').exists():
        vlabel = {}
        for ch, vol, lab in db.execute(f"SELECT id, volume_work, title FROM '{SCRATCH}/sibling-chapters.parquet' WHERE id <> '' AND volume_work <> ''").fetchall():
            vol_of.setdefault(ch, vol)
            if lab:
                vol_titles[vol].append(lab)
            if vol not in vlabel:
                vlabel[vol] = None
        if vlabel:
            db.register('vl', db.execute('SELECT unnest(?) AS key', [sorted(vlabel)]).df())
            for k, lab in db.execute(f"SELECT w.key, w.label FROM '{G}/work.parquet' w JOIN vl USING (key)").fetchall():
                if lab and lab not in vol_titles[k][:1]:
                    vol_titles[k].insert(0, lab)
    vol_terms = {}
    for vol, ts in vol_titles.items():
        tt = set()
        for t in ts:
            tt |= topic_terms(t)
        vol_terms[vol] = tt
    del vol_titles
    print('pass eight:', len(hist_j), 'history journal keys,', len(vol_of), 'chapters with a volume', flush=True)

    def features(people_, p, mask=None, exacts=None, refkeys=None, citers_of=None):
        fe = L.features(people_, p, mask=mask, exacts=exacts, refkeys=refkeys, citers_of=citers_of)
        if fe.get('exact'):
            return fe
        w = p['work_id']
        h = HIDE[0]
        review_like = p.get('kind') == 'review' or bool(REVIEWISH.search(p['title'] or '')) or bool(
            re.match(r'^\s*[^.:]{3,60}\.\s+\S', p['title'] or '')) or p.get('role') == 'reviewer'
        for k, c in fe['cands'].items():
            # not on a review record: its title is the reviewed book's, so the book's author shares it (hand audit
            # 2026-11-12: 3 of 40 topic rows were the reviewed book's author printed on the review record)
            if topics is not None and c.get('lev') in ('full', 'variant') and not review_like:
                # the gold test hides the credited work: its own title is not part of the hidden key's profile
                sc, shared = topics.score(k, p['title'], p['title'] if (h and h[1] == k and h[0] == w) else None)
                if sc >= topic_min:
                    c['facts'].append(f'topic:{sc:.1f}')
            for k2 in exacts or ():
                if k2 != k and ((k, k2) in coed or (k, k2) in adv):
                    c['facts'].append(f'coauthor-network:{k2}')
                    break
            # a co-author credited on the work (key log / identifier) shares a dated affiliation (independent sources,
            # WPPeople.aff) with the candidate, both windows covering the work's year (L.SLACK either side)
            y = p['year']
            if y and exacts:
                mine = [(ror, fy, ly) for ror, _, fy, ly in people_.aff.get(k, ())
                        if (fy or ly) - L.SLACK <= y <= (ly or fy) + L.SLACK]
                if mine:
                    rs = {ror for ror, _, _ in mine}
                    for k2 in exacts:
                        if k2 != k and any(ror in rs and (fy or ly) - L.SLACK <= y <= (ly or fy) + L.SLACK
                                           for ror, _, fy, ly in people_.aff.get(k2, ())):
                            c['facts'].append(f'coauthor-colleague:{k2}')
                            break
            for k2 in vp.get(w, ()):
                if k2 != k and not (h and h[0] == w and h[1] == k2) and (
                        (k, k2) in people_.coauth or (k, k2) in coed or (k, k2) in adv):
                    c['facts'].append(f'volume-network:{k2}')
                    break
            if k in ved.get(w, ()):
                c['facts'].append('volume-editor')
            # pass eight (rule ii): topic against the volume's title and sibling chapters as well as the work's own title
            if topics is not None and c.get('lev') in ('full', 'variant') and not review_like:
                ctx = topic_terms(p['title']) | vol_terms.get(vol_of.get(w), set())
                hid = topic_terms(p['title']) if (h and h[1] == k and h[0] == w) else set()
                c['topicv'] = topics.score_terms(k, ctx, hid)
        jk = journal_key(p.get('journal') or '') if p.get('journal') else ''
        fe['venue'] = 'journal' if jk and jk in hist_j else ('volume' if vp.get(w) else 'none')
        return fe
    return features


def link(args):
    import random
    import time
    t0 = time.time()
    db = duck()
    G = GRAPH
    people = WPPeople(db)
    print('people', round(time.time() - t0), flush=True)
    import pyarrow.compute as pc
    T = load_positions(limit=args.limit)
    print(T.num_rows, 'positions', round(time.time() - t0), flush=True)
    works = set(T.column('work').to_pylist())
    authors = defaultdict(set)
    for k, w in db.execute(f"SELECT DISTINCT \"from\", \"to\" FROM {keylog(G, 'authored')}").fetchall():
        if w in works:
            authors[w].add(k)
    features = L.features
    if getattr(args, 'nameonly', False) and (SCRATCH / 'credited-extra.parquet').exists():
        # name-only class (2026-11-12): identifier credits are the work's known authors
        for w, k in db.execute(f"SELECT work, key FROM '{SCRATCH}/credited-extra.parquet' WHERE work <> ''").fetchall():
            if w in works:
                authors[w].add(k)
    if getattr(args, 'nameonly', False) or getattr(args, 'new_facts', False):
        features = nameonly_features(db, people, topic_min=args.topic_min)       # facts FACTS_NAMEONLY added (2026-11-12)
    # theses citing each work (for the 'a thesis the key supervised cites the work' fact)
    citers_of = defaultdict(set)
    for w, d in db.execute(f"""SELECT c."to", replace(a, 'diss-thesis:', '') FROM '{G}/cites.parquet' c
            JOIN (SELECT key, unnest(anchors) a FROM '{G}/work.parquet' WHERE kind = 'thesis') t ON t.key = c."from"
            WHERE a LIKE 'diss-thesis:%'""").fetchall():
        if w in works:
            citers_of[w].add(d)
    # keys credited (key log) with a work the position's work cites: JSTOR notes, OpenAlex references
    refkeys = defaultdict(set)
    for w, k in db.execute(f"""SELECT DISTINCT c."from", a."from" FROM '{G}/cites.parquet' c JOIN {keylog(G, 'authored')} a
            ON a."to" = c."to" WHERE c.source LIKE '%jstor%' OR c.source LIKE '%crossref%'""").fetchall():
        if w in works:
            refkeys[w].add(k)
    oa_graph = dict(db.execute(f"""SELECT DISTINCT work, graph_work FROM read_parquet('{OA_ROWS}', union_by_name=true)
            WHERE graph_work <> ''""").fetchall())
    oa_of = {o: w for o, w in zip(T.column('oa_work').to_pylist(), T.column('work').to_pylist()) if o}
    gauth = defaultdict(set)
    for k, w in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'authored')}").fetchall():
        gauth[w].add(k)
    for line in open(SCRATCH / 'oa-refs.jsonl'):
        ow, rs = json.loads(line)
        w = oa_of.get(ow)
        if w:
            for r in rs:
                g = oa_graph.get(r)
                if g:
                    refkeys[w] |= gauth.get(g, set())
    del gauth, oa_graph
    # the reviewed books' authors of each review work, and each key's own books by title (book-author check)
    reviewed_authors = defaultdict(set)
    for w, k in db.execute(f"""SELECT r."from", a."from" FROM '{G}/reviews.parquet' r JOIN {keylog(G, 'authored')} a ON a."to" = r."to"
            UNION SELECT r."from", e."from" FROM '{G}/reviews.parquet' r JOIN {keylog(G, 'edited')} e ON e."to" = r."to\"""").fetchall():
        if w in works:
            reviewed_authors[w].add(k)
    book_titles = defaultdict(set)
    for k, t in db.execute(f"""SELECT a."from", w.label FROM (SELECT "from", "to" FROM {keylog(G, 'authored')} UNION
            SELECT "from", "to" FROM {keylog(G, 'edited')}) a JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'book'""").fetchall():
        tn = tnorm(t)
        if tn:
            book_titles[tn].add(k)
    # OpenAlex records fetched by DOI outside the History harvest (their names' rarity is not measured there)
    import glob as _g
    outside = set()
    for fn in _g.glob(str(SCRATCH / 'oa' / 'doi-lookup-*.jsonl')) + _g.glob(str(SCRATCH / 'oa-title' / 'doi-lookup-*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            outside.add(line[10:40].split('"')[0])
    print('aux', len(outside), 'records outside History', round(time.time() - t0), flush=True)
    # population rarity: every name the positions print and every key's name
    needed = set()
    for nm in set(T.column('name').to_pylist()):
        for f, _, g in forms(nm)[:1]:
            needed.add((f, g[0]))
    for lab in people.label.values():
        for f, _, g in forms(lab):
            needed.add((f, g[0]))
    pop = L.population_counts(db, needed)
    LCD.clear()
    LCD.update(lc_dated(db, needed))
    print('population', len(needed), round(time.time() - t0), flush=True)
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'] = tuple(P['FACTS'])
    P['XDATE'] = tuple(P['XDATE'])
    L.PARAMS.update({k: v for k, v in P.items() if k in L.PARAMS})
    if getattr(args, 'nameonly', False) or getattr(args, 'new_facts', False):
        P['FACTS'] = P['FACTS'] + tuple(f for f in (args.facts.split(',') if args.facts else FACTS_NAMEONLY) if f and f != 'none')
        P['ONE_NETWORK_FACT'] = not args.no_one_fact and args.facts != 'none'
        if args.topic_min > 0 and args.facts != 'none':
            P['FACTS'] = P['FACTS'] + ('topic',)
        print('facts', P['FACTS'], flush=True)
    # pass eight: the single-candidate rules adopted (state linked, own branch names); thresholds chosen on the dev half
    P['ADOPT'] = tuple(x for x in (getattr(args, 'adopt', '') or '').split(',') if x)
    P['TOPICV_MIN'] = getattr(args, 'topicv_min', 1e9)
    P['SCHOLAR_MAX_BEARERS'] = getattr(args, 'scholar_max_bearers', 0)
    print('adopt', P['ADOPT'], 'topicv_min', P['TOPICV_MIN'], 'scholar_max_bearers', P['SCHOLAR_MAX_BEARERS'], flush=True)

    # pass 1: ORCID exacts per work (co-author fact)
    exact_of = defaultdict(set)
    for r in iter_rows(T, pc.and_(pc.equal(T.column('credited'), ''), pc.not_equal(T.column('orcid'), ''))):
        if True:
            fe = features(people, make_pos(r))
            if fe.get('exact'):
                exact_of[r['work']].update(fe['exact'])
    # pass 2: every uncredited position
    out = []
    for n, r in enumerate(iter_rows(T, pc.equal(T.column('credited'), ''))):
        p = make_pos(r)
        fe = features(people, p, exacts=authors.get(r['work'], set()) | exact_of.get(r['work'], set()),
                        refkeys=refkeys.get(r['work']), citers_of=citers_of)
        st, k, br, cands, sig = rule_wp(people, p, fe, pop, P, use_dup=not args.no_dup)
        st, k, br, sig = guard(r, st, k, br, sig, fe, P, book_titles, reviewed_authors, outside)
        already = bool(k) and any(x in authors.get(r['work'], ()) for x in k.split(';'))
        live = cands if st != 'exact' else []
        out.append(dict(pid=r['pid'], state=st, key=k or '', branch=br, candidates='|'.join(live), n_candidates=len(live),
                        signals=' '.join(sig), already_credited=already))
        if n % 100000 == 0:
            print(n, round(time.time() - t0), flush=True)
    print('linked all', round(time.time() - t0), flush=True)
    # gold and namesake tests
    def judge(k, g):
        fk, fg = forms(people.label.get(k, '')), forms(people.label.get(g, ''))
        if not any(a[0] == b[0] and name_level(a[2], b[2]) for a in fk for b in fg):
            return 'wrong'
        for d in (people.lcnaf, people.orcid):
            if d.get(k) and d.get(g) and not d[k] & d[g]:
                return 'wrong'
        if g in people.not_same.get(k, ()):
            return 'wrong'
        return 'dup'
    rnd = random.Random(11)
    by_role = defaultdict(list)
    G_T = T.filter(pc.not_equal(T.column('credited'), ''))
    idx = defaultdict(list)
    for i, role in enumerate(G_T.column('role').to_pylist()):
        idx[role].append(i)
    for role, ii in idx.items():
        rnd.shuffle(ii)
        by_role[role] = G_T.take(sorted(ii[:args.gold])).to_pylist()
    gold_out, ns_out = [], []
    for role, rs in by_role.items():
        for r in rs:
            g = r['credited']
            p = make_pos(r)
            if getattr(args, 'gold_no_oa', False):
                # the name-only case: the record carries no OpenAlex author id (a Crossref chapter, a JSTOR record)
                p['oa_author'] = ''
            HIDE[0] = (r['work'], g)
            by_orcid = r['credited_how'] == 'orcid'
            m = dict(key=g, orcid={r['orcid']} if by_orcid else set(), src_orcid=not by_orcid)
            ex = (authors.get(r['work'], set()) | exact_of.get(r['work'], set())) - {g}
            fe = features(people, p, mask=m, exacts=ex, refkeys=refkeys.get(r['work']), citers_of=citers_of)
            for use_dup in (False, True):
                st, k, br, cands, sig = rule_wp(people, p, fe, pop, P, use_dup=use_dup)
                st, k, br, sig = guard(r, st, k, br, sig, fe, P, book_titles, reviewed_authors, outside)
                cls = None if st != 'linked' else 'right' if k == g else judge(k, g)
                gold_out.append(dict(pid=r['pid'], role=role, half=stable_half(g), dup=use_dup, true=g, state=st, key=k or '',
                                     true_listed=g in (cands or []), cands='|'.join(cands or []),
                                     branch=br, cls=cls or '', sig=' '.join(sig), in_cands=g in fe['cands'],
                                     n_live=len(cands), name=r['name'], year=r['year'], how=r['credited_how']))
            # masked author: another name-compatible key proven a different person from g; drop g, hide its ids
            b1 = people.life.get(g, (None,))[0]
            for k2 in fe['cands']:
                if k2 == g:
                    continue
                b2 = people.life.get(k2, (None,))[0]
                p1, p2 = people.phd.get(g), people.phd.get(k2)
                if not ((people.lcnaf.get(g) and people.lcnaf.get(k2) and not people.lcnaf[g] & people.lcnaf[k2])
                        or (people.orcid.get(g) and people.orcid.get(k2) and not people.orcid[g] & people.orcid[k2])
                        or (b1 and b2 and abs(b1 - b2) > 1) or (p1 and p2 and abs(p1 - p2) > 1) or k2 in people.not_same.get(g, ())):
                    continue
                m2 = dict(drop={g}, key=k2, lc=set(people.lcnaf.get(k2, ())), orcid=set(people.orcid.get(k2, ())), src_orcid=False)
                fe2 = features(people, p, mask=m2, exacts=ex, refkeys=refkeys.get(r['work']), citers_of=citers_of)
                st, k, br, cands, sig = rule_wp(people, p, fe2, pop, P, use_dup=not args.no_dup)
                st, k, br, sig = guard(r, st, k, br, sig, fe2, P, book_titles, reviewed_authors, outside)
                ns_out.append(dict(test='masked-author', pid=r['pid'], role=role, proven=k2, true=g, state=st, key=k or '', cands='|'.join(cands or []),
                                   branch=br, false_link=st == 'linked' and k == k2, sig=' '.join(sig), name=r['name'], year=r['year']))
            HIDE[0] = None
    # ORCID namesake: the printed ORCID is on no key; the one name-compatible key holds a different ORCID
    for r in iter_rows(T, pc.and_(pc.equal(T.column('credited'), ''), pc.not_equal(T.column('orcid'), ''))):
        if people.orcid_key.get(r['orcid']):
            continue
        p = make_pos(r)
        cs = L.candidates(people, p)
        if len(cs) != 1:
            continue
        k = next(iter(cs))
        if not people.orcid.get(k):
            continue
        m = dict(key=k, orcid=set(people.orcid[k]), src_orcid=False)
        fe = features(people, p, mask=m, exacts=authors.get(r['work'], set()), refkeys=refkeys.get(r['work']), citers_of=citers_of)
        st, kk, br, cands, sig = rule_wp(people, p, fe, pop, P, use_dup=not args.no_dup)
        st, kk, br, sig = guard(r, st, kk, br, sig, fe, P, book_titles, reviewed_authors, outside)
        ns_out.append(dict(test='orcid-namesake', pid=r['pid'], role=r['role'], proven=k, true='', state=st, key=kk or '', cands='|'.join(cands or []),
                           branch=br, false_link=st == 'linked', sig=' '.join(sig), name=r['name'], year=r['year']))
    print('tests', len(gold_out), len(ns_out), round(time.time() - t0), flush=True)
    import pyarrow as pa
    import pyarrow.parquet as pq
    tag = (f'-{args.limit}' if args.limit else '') + (getattr(args, 'out_tag', '') or '')
    pq.write_table(pa.Table.from_pylist(out), SCRATCH / f'results{tag}.parquet')
    pq.write_table(pa.Table.from_pylist(gold_out), SCRATCH / f'gold{tag}.parquet')
    if ns_out:
        pq.write_table(pa.Table.from_pylist(ns_out), SCRATCH / f'namesake{tag}.parquet')
    # rarity of each position's name (for the bands in the report)
    rar = []
    for pid, nm in zip(T.column('pid').to_pylist(), T.column('name').to_pylist()):
        fs = forms(nm)
        if fs:
            f, _, g = fs[0]
            rar.append(dict(pid=pid, lc_n=pop[0].get((f, g[0]), 0), oa_n=pop[1].get((f, g[0]), 0)))
    pq.write_table(pa.Table.from_pylist(rar), SCRATCH / f'rarity{tag}.parquet')
    print('done', round(time.time() - t0), flush=True)


# ---------------------------------------------------------------- report and outputs

def band(n):
    return L.band(n)


def norm_name(nm):
    fs = forms(nm)
    if not fs:
        return nfold(nm).strip()
    f, _, g = fs[0]
    return f + ', ' + ' '.join(g)


def write_parts(path, rows, cols, max_bytes=45_000_000):
    """rows -> path/part-NN.csv.gz, each under max_bytes compressed (estimated as it writes)"""
    import io
    path.mkdir(parents=True, exist_ok=True)
    for old in path.glob('part-*.csv.gz'):
        old.unlink()
    n, f, w, raw = 0, None, None, None
    parts = []
    for r in rows:
        if f is None or raw.tell() > max_bytes:
            if f:
                f.close()
            fn = path / f'part-{n:02d}.csv.gz'
            parts.append(fn)
            raw = open(fn, 'wb')
            f = gzip.open(raw, 'wt', newline='', encoding='utf-8')
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            n += 1
        w.writerow(r)
    if f:
        f.close()
        raw.close()
    return parts


def report(args):
    import duckdb
    db = duck()
    G = GRAPH
    S = SCRATCH
    tag = f'-{args.limit}' if args.limit else ''
    OUT.mkdir(parents=True, exist_ok=True)
    db.execute(f"CREATE VIEW pos AS SELECT * FROM '{S}/positions*.parquet'")
    db.execute(f"CREATE VIEW res AS SELECT * FROM '{S}/results{tag}.parquet'")
    db.execute(f"CREATE VIEW gold AS SELECT * FROM '{S}/gold{tag}.parquet'")
    db.execute(f"CREATE VIEW ns AS SELECT * FROM '{S}/namesake{tag}.parquet'")
    db.execute(f"CREATE VIEW rar AS SELECT * FROM '{S}/rarity{tag}.parquet'")
    db.execute(f"""CREATE TABLE allp AS SELECT p.pid, p.role, p.source, p.work, p.pos, p.n_auth, p.name, p.year, p.journal, p.kind,
            p.orcid, p.oa_author, p.inst_printed, p.inst_ror, p.inst_ror_name, p.rors, p.credited, p.credited_how,
            coalesce(r.state, CASE WHEN p.credited <> '' THEN 'credited' END) state, r.key, r.branch, r.candidates,
            r.n_candidates, r.signals, r.already_credited
            FROM pos p {'JOIN' if args.limit else 'LEFT JOIN'} res r USING (pid)
            {"WHERE p.credited <> '' OR r.pid IS NOT NULL" if not args.limit else ''}""")
    rep = dict(date='2026-11-11', graph=str(G), rule=dict(base='link_cited_work_authors.py chosen parameters (report.json tuning.chosen of '
               'cited-work-authors-2026-11-10)', added=['duplicate-group (see docstring)', 'placing facts: dated, independent affiliation sources only',
               'gold rows hide the credited work from the key\'s span, co-author pairs and OpenAlex ties']))
    q = lambda sql: db.execute(sql).fetchall()
    # ---- states per role
    roles = {}
    for role, in q("SELECT DISTINCT role FROM allp ORDER BY 1"):
        d = dict(positions=q(f"SELECT count(*) FROM allp WHERE role='{role}'")[0][0])
        d['positions_by_state'] = dict(q(f"SELECT state, count(*) FROM allp WHERE role='{role}' GROUP BY 1 ORDER BY 2 DESC"))
        d['positions_already_credited_under_another_name'] = q(f"SELECT count(*) FROM allp WHERE role='{role}' AND already_credited")[0][0]
        d['branches'] = dict(q(f"SELECT branch, count(*) FROM allp WHERE role='{role}' AND state IN ('linked','possible','none') GROUP BY 1 ORDER BY 2 DESC"))
        d['possible_one_candidate'] = q(f"SELECT count(*) FROM allp WHERE role='{role}' AND state='possible' AND n_candidates=1")[0][0]
        w = q(f"""SELECT count(*), count(*) FILTER (WHERE b), count(*) FILTER (WHERE a), count(*) FILTER (WHERE allc), count(*) FILTER (WHERE allc_after)
                  FROM (SELECT work, bool_or(state='credited') b, bool_or(state='credited' OR (state IN ('exact','linked') AND NOT already_credited)) a,
                        bool_and(state='credited') allc, bool_and(state IN ('credited','exact','linked')) allc_after
                        FROM allp WHERE role='{role}' GROUP BY work)""")[0]
        d['works'] = dict(works=w[0], with_a_credited_person_before=w[1], after=w[2], every_name_credited_before=w[3], every_name_credited_after=w[4])
        d['people_linked'] = q(f"SELECT count(DISTINCT key) FROM allp WHERE role='{role}' AND state IN ('exact','linked') AND NOT already_credited")[0][0]
        roles[role] = d
    rep['roles'] = roles
    # candidates the dates rule out are removed before counting (2026-11-11); kept visible here
    rep['excluded_by_date'] = {role: dict(positions=n, candidates_excluded=int(c or 0), now_none=nn) for role, n, c, nn in q(
        f"""SELECT p.role, count(*), sum(TRY_CAST(regexp_extract(r.signals, 'date-excluded=(\\d+)', 1) AS INTEGER)),
              count(*) FILTER (WHERE r.branch = 'only-date-excluded')
           FROM '{S}/results{tag}.parquet' r JOIN pos p USING (pid) WHERE r.signals LIKE '%date-excluded=%' GROUP BY 1""")}
    if (S / 'results-prev.parquet').exists():
        rep['date_elimination_changes'] = {f'{role}|{a}->{b}': n for role, a, b, n in q(
            f"""SELECT p.role, o.state || CASE WHEN o.state = 'possible' THEN '(' || o.n_candidates || ')' ELSE '' END,
                  r.state || CASE WHEN r.state = 'possible' AND r.n_candidates < o.n_candidates AND o.state = 'possible' THEN '(fewer)'
                                  WHEN r.state = 'possible' THEN '(' || r.n_candidates || ')' ELSE '' END, count(*)
               FROM '{S}/results-prev.parquet' o JOIN '{S}/results{tag}.parquet' r USING (pid) JOIN pos p USING (pid)
               WHERE o.state <> r.state OR o.n_candidates <> r.n_candidates GROUP BY ALL HAVING count(*) >= 1 ORDER BY 4 DESC LIMIT 60""")}
        rep['date_elimination_summary'] = {f'{role}|{a}->{b}': n for role, a, b, n in q(
            f"""SELECT p.role, o.state, CASE WHEN o.state = 'possible' AND r.state = 'possible' AND r.n_candidates < o.n_candidates
                  THEN 'possible-fewer' ELSE r.state END, count(*)
               FROM '{S}/results-prev.parquet' o JOIN '{S}/results{tag}.parquet' r USING (pid) JOIN pos p USING (pid)
               WHERE o.state <> r.state OR o.n_candidates <> r.n_candidates GROUP BY ALL ORDER BY 4 DESC""")}
    # ---- the three headline measures
    jc = q(f"""WITH c AS (SELECT DISTINCT "from" w FROM '{G}/cites.parquet' WHERE source LIKE '%jstor%'),
            a AS (SELECT DISTINCT "to" w FROM {keylog(G, 'authored')}),
            n AS (SELECT DISTINCT work w FROM allp WHERE state IN ('exact','linked') AND NOT already_credited)
            SELECT count(*), count(*) FILTER (WHERE c.w IN (SELECT w FROM a)),
                   count(*) FILTER (WHERE c.w IN (SELECT w FROM a) OR c.w IN (SELECT w FROM n)) FROM c""")[0]
    rep['jstor_citing_articles'] = dict(articles=jc[0], with_credited_author_before=jc[1], after=jc[2],
                                        share_before=round(jc[1] / jc[0], 4) if jc[0] else None, share_after=round(jc[2] / jc[0], 4) if jc[0] else None)
    rv = q(f"""WITH r AS (SELECT DISTINCT "from" w FROM '{G}/reviews.parquet'),
            a AS (SELECT DISTINCT "to" w FROM {keylog(G, 'authored')}),
            n AS (SELECT DISTINCT work w FROM allp WHERE role='reviewer' AND state IN ('exact','linked') AND NOT already_credited)
            SELECT count(*), count(*) FILTER (WHERE r.w IN (SELECT w FROM a)), count(*) FILTER (WHERE r.w IN (SELECT w FROM a) OR r.w IN (SELECT w FROM n)) FROM r""")[0]
    rn = q(f"""SELECT count(*) FILTER (WHERE b), count(*) FILTER (WHERE a), count(*) FROM (SELECT work, bool_or(state='credited') b,
            bool_or(state='credited' OR (state IN ('exact','linked') AND NOT already_credited)) a FROM allp WHERE role='reviewer' GROUP BY work)""")[0]
    rep['reviews'] = dict(review_works=rv[0], with_credited_reviewer_before=rv[1], after=rv[2],
                          with_printed_reviewer=rn[2], printed_reviewer_credited_before=rn[0], printed_reviewer_credited_after=rn[1])
    ca = q(f"""SELECT count(*), count(DISTINCT work), count(DISTINCT key) FROM allp a WHERE role IN ('author','jstor-author') AND state IN ('exact','linked')
            AND NOT already_credited AND EXISTS (SELECT 1 FROM allp b WHERE b.work = a.work AND b.pid <> a.pid AND (b.state='credited'))""")[0]
    rep['coauthor_credits_added'] = dict(credits=ca[0], works=ca[1], people=ca[2],
                                         note='exact/linked authors on works where another author is already credited in the key log')
    # ---- gold
    def pr(rows):
        out = {}
        for k, n, l, ok, wr in rows:
            out[str(k)] = dict(gold=n, linked=l, right_or_duplicate_key=ok, wrong=wr, precision=round(ok / l, 4) if l else None,
                               recall=round(ok / n, 4) if n else None)
        return out
    gq = lambda by, where='': pr(q(f"""SELECT {by} k, count(*), count(*) FILTER (WHERE state='linked'), count(*) FILTER (WHERE cls IN ('right','dup')),
            count(*) FILTER (WHERE cls='wrong') FROM gold g LEFT JOIN rar USING (pid) WHERE half=1 AND dup {where} GROUP BY 1 ORDER BY 1"""))
    rep['gold'] = dict(
        note='held-out half (stable hash of the credited key = 1); the other half was used only to decide whether the duplicate-group branch is admitted',
        rows=dict(q("SELECT role, count(*) FROM gold WHERE dup GROUP BY 1")),
        by_role=gq('role'), by_role_without_dupgroup=pr(q("""SELECT role, count(*), count(*) FILTER (WHERE state='linked'), count(*) FILTER (WHERE cls IN ('right','dup')),
            count(*) FILTER (WHERE cls='wrong') FROM gold WHERE half=1 AND NOT dup GROUP BY 1""")),
        tuning_half_dupgroup=pr(q("""SELECT role || '|' || dup, count(*), count(*) FILTER (WHERE state='linked'), count(*) FILTER (WHERE cls IN ('right','dup')),
            count(*) FILTER (WHERE cls='wrong') FROM gold WHERE half=0 GROUP BY 1""")),
        by_branch=gq("role || '|' || branch", "AND state='linked'"),
        by_how_credited=gq("role || '|' || how"),
        by_lc_rarity=gq("role || '|lc ' || CASE WHEN lc_n=0 THEN '0' WHEN lc_n=1 THEN '1' WHEN lc_n<=5 THEN '2-5' ELSE '6+' END"),
        by_oa_rarity=gq("role || '|oa ' || CASE WHEN oa_n<=1 THEN '0-1' WHEN oa_n<=5 THEN '2-5' WHEN oa_n<=20 THEN '6-20' ELSE '21+' END"),
        by_decade=gq("role || '|' || coalesce(CAST(year // 10 * 10 AS VARCHAR), 'no year')"),
        not_linked_reasons=dict(q("SELECT role || '|' || state || '|' || branch, count(*) FROM gold WHERE half=1 AND dup AND state<>'linked' GROUP BY 1 ORDER BY 2 DESC LIMIT 40")))
    rep['namesake'] = dict(rows=dict(q("SELECT test || '|' || role, count(*) FROM ns GROUP BY 1")),
                           false_links=dict(q("SELECT test || '|' || role, count(*) FROM ns WHERE false_link GROUP BY 1")),
                           false_links_by_branch=dict(q("SELECT test || '|' || branch, count(*) FROM ns WHERE false_link GROUP BY 1")))
    db.execute(f"COPY (SELECT g.*, p.label true_label, p2.label linked_label FROM gold g LEFT JOIN '{G}/person.parquet' p ON p.key=g.true "
               f"LEFT JOIN '{G}/person.parquet' p2 ON p2.key=g.key WHERE dup AND cls IN ('wrong','dup')) TO '{OUT}/gold-wrong{tag}.csv' (HEADER)")
    db.execute(f"COPY (SELECT n.*, a.title, p.label proven_label, p2.label linked_label FROM ns n JOIN pos a USING (pid) LEFT JOIN '{G}/person.parquet' p ON p.key=n.proven "
               f"LEFT JOIN '{G}/person.parquet' p2 ON p2.key=n.key WHERE false_link) TO '{OUT}/namesake-links{tag}.csv' (HEADER)")
    # ---- C: unkeyed people (state none)
    rep['unkeyed'] = {}
    for role, in q("SELECT DISTINCT role FROM allp WHERE state='none'"):
        r = q(f"""SELECT count(*), count(DISTINCT work), count(*) FILTER (WHERE inst_printed <> '' OR len(rors) > 0),
                  count(*) FILTER (WHERE orcid <> '') FROM allp WHERE role='{role}' AND state='none'""")[0]
        rep['unkeyed'][role] = dict(positions=r[0], works=r[1], with_printed_institution=r[2], with_orcid=r[3])
    names = defaultdict(lambda: [0, set(), Counter(), Counter(), set()])
    for role, nm, inst, ror, w, orc in q("""SELECT role, name, CASE WHEN inst_ror_name <> '' THEN inst_ror_name ELSE inst_printed END,
            inst_ror, work, orcid FROM allp WHERE state='none'"""):
        k = (role, norm_name(nm))
        d = names[k]
        d[0] += 1
        d[1].add(w)
        d[2][nm] += 1
        if inst:
            d[3][inst] += 1
        if orc:
            d[4].add(orc)
    for role in rep['unkeyed']:
        ks = [k for k in names if k[0] == role]
        rep['unkeyed'][role]['distinct_names'] = len(ks)
        rep['unkeyed'][role]['distinct_name_institution'] = sum(max(1, len(names[k][3])) for k in ks)
        rep['unkeyed'][role]['names_with_2plus_works'] = sum(1 for k in ks if len(names[k][1]) >= 2)
        rep['unkeyed'][role]['names_with_5plus_works'] = sum(1 for k in ks if len(names[k][1]) >= 5)
    with gzip.open(OUT / f'unkeyed-people{tag}.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['role', 'name_key', 'printed_as', 'works', 'positions', 'institutions_printed', 'orcids'])
        for (role, k), d in sorted(names.items(), key=lambda x: -len(x[1][1])):
            if len(d[1]) >= 2 or d[3]:
                w.writerow([role, k, d[2].most_common(1)[0][0], len(d[1]), d[0], '; '.join(f'{i} ({n})' for i, n in d[3].most_common(4)), ';'.join(sorted(d[4]))])
    rep['unkeyed_top'] = {role: [dict(name=names[k][2].most_common(1)[0][0], works=len(names[k][1]),
                                      institutions=[i for i, _ in names[k][3].most_common(3)])
                                 for k in sorted([k for k in names if k[0] == role], key=lambda k: -len(names[k][1]))[:25]] for role in rep['unkeyed']}
    (OUT / f'report{tag}.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps({k: rep.get(k) for k in ('roles', 'jstor_citing_articles', 'reviews', 'coauthor_credits_added', 'namesake',
                                               'excluded_by_date', 'date_elimination_summary')}, indent=1, default=str))
    print(json.dumps(rep['gold']['by_role'], indent=1))
    print(json.dumps(rep['gold']['tuning_half_dupgroup'], indent=1))


# ---------------------------------------------------------------- co-author mints (proposal, not applied)

ORG = re.compile(r'(?i)\b(team|group|consortium|collaborat\w*|network|committee|investigators|project|society|association|'
                 r'council|institut\w*|universit\w*|department|centre|center|museum|library|foundation|press|muse|periodical|'
                 r'veranstaltung|commission|working party)\b|[().:]\s*$|\d{4}')
CAP = 25    # author lists longer than this: only ORCID-bearing co-authors are minted; the work is listed


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


def mints(args):
    """Owner, 2026-11-11 (co-author role only): a co-author of a work written by a person key with historian evidence
    (person-roles: historian, confidence strong or supported) gets a person key when none exists, even outside
    history. One key per person, not per paper: mentions join on a printed ORCID, else on strict full-name agreement
    AND a shared fact (the same OpenAlex author id, the same keyed historian co-author, the same printed institution
    ROR). Same full name, different historians, no shared fact: separate keys with possible-same marks. Initial-only
    names without ORCID, and names with a compatible key (state possible), are held. Dead end: the person and the
    authorship claim on the co-authored work only."""
    import duckdb
    db = duck()
    G = GRAPH
    S = SCRATCH
    out = OUT / 'coauthor-mints'
    out.mkdir(parents=True, exist_ok=True)
    roles = {}
    with gzip.open(ROOT / 'data/person-facts/person-roles.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            roles[r['key']] = (r['role'], r['confidence'])
    hist = {k for k, (r, c) in roles.items() if r == 'historian' and c in ('strong', 'supported')}
    db.execute(f"""CREATE TABLE a AS SELECT p.pid, p.role, p.work, p.pos, p.n_auth, p.name, p.year, p.journal, p.orcid, p.oa_author,
            p.rors, p.raw_aff, p.oa_work, p.credited, coalesce(r.state, 'credited') state, r.key, r.branch, r.candidates
            FROM '{S}/positions*.parquet' p LEFT JOIN '{S}/results.parquet' r USING (pid) WHERE p.role IN ('author', 'jstor-author')""")
    authored = defaultdict(set)
    for k, w in db.execute(f"SELECT \"from\", \"to\" FROM {keylog(G, 'authored')}").fetchall():
        authored[w].add(k)
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    work_label = {}
    contrib = set()
    if (S / 'contributors.parquet').exists():
        contrib = {p_ for (p_,) in db.execute(f"SELECT pid FROM '{S}/contributors.parquet' WHERE role = 'contributor'").fetchall()}
    rows = db.execute("SELECT * FROM a").fetchall()
    cols = [d[0] for d in db.description]
    rows = [dict(zip(cols, r)) for r in rows]
    by_work = defaultdict(list)
    for r in rows:
        by_work[r['work']].append(r)
    # historians on each work: key-log credits and ORCID exacts (no link made in this run is evidence here)
    hw = {}
    for w, rs in by_work.items():
        ks = {k for k in authored.get(w, ()) if k in hist} | {r['key'] for r in rs if r['state'] == 'exact' and r['key'] in hist}
        if ks:
            hw[w] = ks
    keyed_on = {w: authored.get(w, set()) | {r['key'] for r in by_work[w] if r['state'] == 'exact'} for w in hw}
    # a key-log author of the work that no printed name matched: the unmatched printed names may be that author
    # under another form (a married name, a transliteration): nothing on such a work is minted
    unmatched = {w: authored.get(w, set()) - {r['credited'] for r in by_work[w] if r['credited']}
                 - {x for r in by_work[w] if r['state'] in ('exact', 'linked') and r['key'] for x in r['key'].split(';')} for w in hw}
    rep = Counter()
    ncount = Counter()
    for w in hw:
        ncount[min(by_work[w][0]['n_auth'], 1000)] += 1
    rep_dist = {'1': 0, '2': 0, '3': 0, '4-5': 0, '6-10': 0, '11-25': 0, '26-50': 0, '51-100': 0, '101+': 0}
    for n, c in ncount.items():
        b = '1' if n <= 1 else '2' if n == 2 else '3' if n == 3 else '4-5' if n <= 5 else '6-10' if n <= 10 else '11-25' if n <= 25 else '26-50' if n <= 50 else '51-100' if n <= 100 else '101+'
        rep_dist[b] += c
    mentions, held, capped = [], [], []
    for w, ks in hw.items():
        for r in by_work[w]:
            if r['state'] in ('credited', 'exact', 'linked'):
                continue
            if r['pid'] in contrib:                     # a foreword writer or series editor, not a co-author
                rep['skipped_contributor'] += 1
                continue
            rep['mentions'] += 1
            m = dict(r, hist=sorted(ks), keyed=sorted(keyed_on[w]))
            fs = forms(r['name'])
            if not fs:
                rep['held_unparsed'] += 1
                held.append(dict(reason='name not parsed', **{k: m[k] for k in ('work', 'pos', 'name', 'year')}))
                continue
            f, _, g = fs[0]
            m['fam'], m['g'] = f, g
            if ORG.search(r['name']):
                rep['held_organisation_name'] += 1
                held.append(dict(reason='an organisation or project printed as an author', **{k: m[k] for k in ('work', 'pos', 'name', 'year')}))
                continue
            if r['n_auth'] > CAP and not r['orcid']:
                rep['capped_no_orcid'] += 1
                capped.append(m)
                continue
            if unmatched.get(w):
                rep['held_unmatched_credited_author'] += 1
                held.append(dict(reason='a key-log author of this work matches no printed name: the mention may be that author',
                                 unmatched=sorted(unmatched[w]), **{k: m[k] for k in ('work', 'pos', 'name', 'year')}))
                continue
            if r['state'] in ('possible', 'ambiguous'):
                rep['held_twin'] += 1
                held.append(dict(reason='a person key bears a compatible name: possible-same, not minted', candidates=r['candidates'],
                                 candidate_labels='|'.join(label.get(k, '') for k in (r['candidates'] or '').split('|') if k),
                                 **{k: m[k] for k in ('work', 'pos', 'name', 'year', 'orcid', 'hist')}))
                continue
            if initial_only(g) and not r['orcid']:
                rep['held_initial_only'] += 1
                held.append(dict(reason='initial-only name without ORCID', **{k: m[k] for k in ('work', 'pos', 'name', 'year', 'hist')}))
                continue
            mentions.append(m)
    # group mentions into people
    uf = UF()
    by_orcid = defaultdict(list)
    bucket = defaultdict(list)
    for i, m in enumerate(mentions):
        uf.find(i)
        if m['orcid']:
            by_orcid[m['orcid']].append(i)
        bucket[m['fam'], m['g'][0]].append(i)
    for ii in by_orcid.values():
        for j in ii[1:]:
            uf.union(ii[0], j)
    basis = defaultdict(set)

    def facts(a, b, extra=()):
        x, y = mentions[a], mentions[b]
        out = []
        if x['orcid'] and y['orcid'] and x['orcid'] != y['orcid']:
            return None                       # two ORCIDs: two people
        if x['oa_author'] and x['oa_author'] == y['oa_author']:
            out.append('openalex-author')
        if set(x['hist']) & set(y['hist']):
            out.append('historian-coauthor')
        if set(x['rors'] or []) & set(y['rors'] or []):
            out.append('institution')
        if 'keyed-coauthor' in extra and (set(x['keyed']) & set(y['keyed'])) - (set(x['hist']) & set(y['hist'])):
            out.append('keyed-coauthor')
        if 'inst-name' in extra and x['raw_aff'] and y['raw_aff']:
            from key_review_credit_merges import agree, is_system
            if any(agree(p, q) for p in x['raw_aff'] for q in y['raw_aff'] if p and q and not is_system(p) and not is_system(q)):
                out.append('inst-name')
        if 'journal-years' in extra and x['journal'] and x['journal'] == y['journal'] and x['year'] and y['year'] and abs(x['year'] - y['year']) <= 5:
            out.append('journal-years')
        return out
    pairs_nofact = []
    for (f, g0), ii in bucket.items():
        if len(ii) < 2:
            continue
        for a_ in range(len(ii)):
            for b_ in range(a_ + 1, len(ii)):
                a, b = ii[a_], ii[b_]
                if name_level(mentions[a]['g'], mentions[b]['g']) != 'full':
                    continue
                fx = facts(a, b)
                if fx is None:
                    continue
                if fx:
                    uf.union(a, b)
                    basis[a, b].update(fx)
                elif mentions[a]['work'] != mentions[b]['work']:
                    pairs_nofact.append((a, b))
    groups = defaultdict(list)
    for i in range(len(mentions)):
        groups[uf.find(i)].append(i)
    comp_basis = {}
    for root, ii in groups.items():
        orc = {mentions[i]['orcid'] for i in ii if mentions[i]['orcid']}
        if len(orc) > 1:
            rep['conflict_two_orcids_in_group'] += 1
        bs = set()
        for a in ii:
            for b in ii:
                bs |= basis.get((a, b), set())
        comp_basis[root] = ('orcid' if orc else '') , bs
    # possible-same between components joined only by name (the guard's cost)
    ps = set()
    for a, b in pairs_nofact:
        ra, rb = uf.find(a), uf.find(b)
        if ra != rb:
            ps.add((min(ra, rb), max(ra, rb)))
    # ---- the guard's cost: would extra facts join them? tested on ORCID mentions (hide the ORCID; same ORCID = same)
    def orcid_test(extra):
        ii = [i for i, m in enumerate(mentions) if m['orcid']]
        b2 = defaultdict(list)
        for i in ii:
            b2[mentions[i]['fam'], mentions[i]['g'][0]].append(i)
        joined = right = 0
        for jj in b2.values():
            for x in range(len(jj)):
                for y in range(x + 1, len(jj)):
                    a, b = jj[x], jj[y]
                    if mentions[a]['work'] == mentions[b]['work'] or name_level(mentions[a]['g'], mentions[b]['g']) != 'full':
                        continue
                    sa, sb = dict(mentions[a]), dict(mentions[b])
                    oa, ob = sa['orcid'], sb['orcid']
                    mentions[a]['orcid'] = mentions[b]['orcid'] = ''
                    fx = facts(a, b, extra)
                    mentions[a]['orcid'], mentions[b]['orcid'] = oa, ob
                    if fx and (set(fx) & set(extra) if extra else True):
                        joined += 1
                        right += oa == ob
        return dict(pairs_joined=joined, same_orcid=right, different_orcid=joined - right)
    tests = {'base (openalex-author, historian, institution ROR)': orcid_test(())}
    for ex in ('keyed-coauthor', 'inst-name', 'journal-years'):
        tests['+' + ex + ' (pairs joined by it alone)'] = orcid_test((ex,))
    hidden = Counter()
    for a, b in pairs_nofact:
        fx = facts(a, b, ('keyed-coauthor', 'inst-name', 'journal-years'))
        for x in fx or ():
            hidden[x] += 1
    # ---- people to mint
    ops, people_out = [], []
    anchor_of = {}
    for n_, (root, ii) in enumerate(sorted(groups.items())):
        ms = [mentions[i] for i in ii]
        orc = sorted({m['orcid'] for m in ms if m['orcid']})
        if len(orc) > 1:
            held.append(dict(reason='one name-and-fact group holds two ORCIDs', names=[m['name'] for m in ms], orcids=orc))
            continue
        names = Counter(m['name'] for m in ms)
        lab = max(names, key=lambda x: (len(x), names[x]))
        anchors = ([f'orcid:{orc[0]}'] if orc else []) + sorted({f"coauthor-mention:{m['work']}:{m['pos']}" for m in ms})
        anchor_of[root] = anchors[0]
        members = sorted({f"openalex-author:{m['oa_author']}" for m in ms if m['oa_author']})
        b = comp_basis[root]
        bas = ('ORCID printed on the record' if orc else 'printed name') + (
            '; mentions joined on ' + ', '.join(sorted(b[1])) if b[1] else '') +             f"; co-author of a historian key ({', '.join(sorted({h for m in ms for h in m['hist']}))}) on {len({m['work'] for m in ms})} work(s); "             'no person key bears a compatible name (work-people-2026-11-11 state none); not a historian on this evidence'
        ops.append(dict(event='mint', key=f'new:p{n_}', type='person', label=lab, resolution='established' if orc else 'recorded',
                        anchors=anchors, aliases=[], members=members, basis=bas))
        for m in ms:
            ops.append(dict(event='mint', key=f"new:c{n_}-{m['pos']}-{m['work']}", type='claim', label='', resolution='recorded',
                            anchors=[f"coauthor-claim:{m['work']}:{m['pos']}"],
                            relation=dict(subject=anchors[0], predicate='authored', object=m['work']),
                            basis=f"author {m['pos'] + 1} of {m['n_auth']} in the {'OpenAlex' if m['role'] == 'author' else 'JSTOR'} record of the work"))
        people_out.append(dict(root=root, label=lab, orcid=orc[0] if orc else '', basis='orcid' if orc else
                               ('+'.join(sorted(b[1])) if b[1] else 'single-work-or-name-only'), works=sorted({m['work'] for m in ms}),
                               hist=sorted({h for m in ms for h in m['hist']}), n_auth=max(m['n_auth'] for m in ms)))
    for a, b in sorted(ps):
        if a in anchor_of and b in anchor_of:
            ops.append(dict(event='attach', key=anchor_of[a], anchors=[], aliases=[], members=[f'possible-same:{anchor_of[b]}'],
                            basis='same full name, co-authors of different historians, no shared fact (owner rule 2026-11-11)'))
    # attach targets must be keys: resolved at apply by the placeholder of the minted person
    root_ph = {root: f'new:p{n_}' for n_, (root, _) in enumerate(sorted(groups.items()))}
    for op in ops:
        if op['event'] == 'attach':
            root = next(r for r, a in anchor_of.items() if a == op['key'])
            op['key'] = root_ph[root]
    proposal = dict(basis='co-authors of historian keys on keyed works (OpenAlex/JSTOR author lists), minted where no person key '
                    'fits (owner 2026-11-11: co-authors outside history should show in the historian\'s graph); dead end: only the '
                    'co-authored work', decided_by='rule', ops=ops)
    with gzip.open(out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:      # 68 MB raw: gzipped for git
        f.write(json.dumps(proposal, ensure_ascii=False) + '\n')
    with gzip.open(out / 'held.json.gz', 'wt', encoding='utf-8') as f:
        f.write(json.dumps(dict(held=held, capped=[{k: m[k] for k in ('work', 'pos', 'name', 'n_auth', 'hist')} for m in capped]),
                           ensure_ascii=False, default=str) + '\n')
    # ---- measures
    hp = defaultdict(set)            # (historian, minted person) -> works
    for p_ in people_out:
        for w in p_['works']:
            for h in hw[w]:
                hp[h, p_['root']].add(w)
    bridges = Counter(len(p_['hist']) for p_ in people_out)
    people_basis = Counter(p_['basis'] for p_ in people_out)
    import random
    rnd = random.Random(7)
    sample = rnd.sample(people_out, min(60, len(people_out)))
    with open(out / 'sample-60.csv', 'w', newline='', encoding='utf-8') as f:
        w_ = csv.writer(f)
        w_.writerow(['label', 'orcid', 'basis', 'works', 'historian_coauthors', 'historian_labels', 'max_authors_on_work'])
        for p_ in sample:
            w_.writerow([p_['label'], p_['orcid'], p_['basis'], ' '.join(p_['works']), ' '.join(p_['hist']),
                         '; '.join(label.get(h, '') for h in p_['hist']), p_['n_auth']])
    # guard cost list
    gc = defaultdict(set)
    for a, b in pairs_nofact:
        ra, rb = uf.find(a), uf.find(b)
        if ra != rb:
            nm = norm_name(mentions[a]['name'])
            gc[nm] |= set(mentions[a]['hist']) | set(mentions[b]['hist'])
    with open(out / 'guard-cost.csv', 'w', newline='', encoding='utf-8') as f:
        w_ = csv.writer(f)
        w_.writerow(['name', 'historians', 'historian_keys'])
        for nm, hs in sorted(gc.items(), key=lambda x: -len(x[1])):
            w_.writerow([nm, len(hs), ' '.join(sorted(hs))])
    capped_works = sorted({m['work'] for m in capped})
    report_ = dict(
        historian_keys=len(hist), works_with_a_historian=len(hw), author_count_distribution_on_historians_works=rep_dist,
        cap=CAP, capped=dict(works=len(capped_works), mentions_without_orcid=len(capped), work_keys_first_50=capped_works[:50]),
        counts=dict(rep), people_to_mint=len(people_out), people_by_basis=dict(people_basis),
        claims=sum(1 for o in ops if o['event'] == 'mint' and o['type'] == 'claim'),
        possible_same_marks=len(ps), historians_gaining_a_coauthor=len({h for h, _ in hp}),
        historian_coauthor_pairs=dict(total=len(hp), with_2plus_works=sum(1 for v in hp.values() if len(v) >= 2),
                                      with_3plus_works=sum(1 for v in hp.values() if len(v) >= 3)),
        bridges=dict(minted_people_by_number_of_historians={str(k): v for k, v in sorted(bridges.items())},
                     connecting_2plus=sum(v for k, v in bridges.items() if k >= 2)),
        guard_cost=dict(name_groups_kept_apart=len(gc), pairs=len(pairs_nofact),
                        names_with_3plus_historians=sum(1 for v in gc.values() if len(v) >= 3),
                        extra_facts_present_on_kept_apart_pairs=dict(hidden), orcid_tests=tests),
        resolution='recorded unless an ORCID is printed (then established); person-roles will read them as other scholar '
                   '(an article on record, no historian signal) unless other evidence exists')
    (out / 'report.json').write_text(json.dumps(report_, indent=1, ensure_ascii=False, default=str) + '\n')
    import pickle
    with open(S / 'mints.pkl', 'wb') as f:
        pickle.dump(dict(people=people_out, hp={f'{a}|{b}': sorted(v) for (a, b), v in hp.items()}), f)
    print(json.dumps(report_, indent=1, default=str))


# ---------------------------------------------------------------- benchmark panel

NAMED = ['p-24137', 'p-12778', 'p-6823', 'p-143231', 'p-145261', 'p-14064', 'p-36505', 'p-4256']   # owner's probes


def panel(args):
    """The standing regression panel: the owner's named probes and 12 historians drawn at random within strata
    (career start before 1980 / 1980-2009 / 2010+, x common / rare name), before and after this run's credits."""
    import pickle
    import random
    db = duck()
    G = GRAPH
    S = SCRATCH
    db.execute(f"""CREATE TABLE newlink AS SELECT DISTINCT unnest(string_split(r.key, ';')) k, p.work w, p.role FROM '{S}/results.parquet' r
                   JOIN '{S}/positions*.parquet' p USING (pid) WHERE r.state IN ('exact', 'linked') AND NOT r.already_credited""")
    db.execute(f"""CREATE TABLE ab AS SELECT DISTINCT "from" k, "to" w FROM {keylog(G, 'authored')}""")
    db.execute("CREATE TABLE aa AS SELECT k, w FROM ab UNION SELECT k, w FROM newlink")
    # works whose author list is longer than the cap (a review section filed as one record): not co-authorship
    db.execute(f"CREATE TABLE big AS SELECT work w FROM '{S}/positions*.parquet' GROUP BY 1 HAVING max(n_auth) > {CAP}")
    minted = pickle.load(open(S / 'mints.pkl', 'rb')) if (S / 'mints.pkl').exists() else dict(people=[], hp={})
    mint_pairs = defaultdict(set)
    for kv, ws in minted['hp'].items():
        h, root = kv.split('|')
        mint_pairs[h].add(root)
    roles = {}
    with gzip.open(ROOT / 'data/person-facts/person-roles.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            roles[r['key']] = (r['role'], r['confidence'])
    # strata for the random draw
    first = dict(db.execute(f"SELECT k, min(w.year) FROM ab JOIN '{G}/work.parquet' w ON w.key = ab.w WHERE w.year BETWEEN 1900 AND 2026 GROUP BY 1").fetchall())
    nworks = dict(db.execute("SELECT k, count(*) FROM ab GROUP BY 1").fetchall())
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    rar = {}
    import pyarrow.parquet as pq
    lcn = Counter()
    for lab in label.values():
        for f, _, g in forms(lab)[:1]:
            lcn[f, g[0]] += 1
    strata = defaultdict(list)
    for k, (role, conf) in roles.items():
        if role != 'historian' or conf not in ('strong', 'supported') or k not in first or nworks.get(k, 0) < 3 or k in NAMED:
            continue
        y = first[k]
        era = 'pre-1980' if y < 1980 else '1980-2009' if y < 2010 else '2010+'
        fs = forms(label.get(k, ''))
        if not fs:
            continue
        common = 'common name' if lcn[fs[0][0], fs[0][2][0]] >= 3 else 'rare name'
        strata[era, common].append(k)
    rnd = random.Random(20261111)
    drawn = []
    for st in sorted(strata):
        for k in rnd.sample(sorted(strata[st]), 2):
            drawn.append((k, ' / '.join(st)))
    people = [(k, 'named') for k in NAMED] + drawn
    rows = []
    for k, grp in people:
        q = lambda sql: db.execute(sql, dict(k=k)).fetchone()[0]
        d = dict(key=k, label=label.get(k), group=grp, role='/'.join(roles.get(k, ('?', '?'))), first_year=first.get(k))
        d['works_before'] = q("SELECT count(DISTINCT w) FROM ab WHERE k = $k")
        d['works_after'] = q("SELECT count(DISTINCT w) FROM aa WHERE k = $k")
        co_b = {r[0] for r in db.execute(f"""SELECT CASE WHEN "from" = $k THEN "to" ELSE "from" END FROM {keylog(G, 'coauthored')}
                WHERE "from" = $k OR "to" = $k""", dict(k=k)).fetchall()}
        co_a = {r[0] for r in db.execute("SELECT DISTINCT b.k FROM aa a JOIN aa b ON a.w = b.w WHERE a.k = $k AND b.k <> $k AND a.w NOT IN (SELECT w FROM big)", dict(k=k)).fetchall()}
        d['coauthors_before'] = len(co_b)
        d['coauthors_after_keyed'] = len(co_b | co_a)
        d['coauthors_after_with_mints'] = len(co_b | co_a) + len(mint_pairs.get(k, ()))
        d['reviews_of_books_keyed_reviewer_before'] = q(f"""SELECT count(DISTINCT r."from") FROM '{G}/reviews.parquet' r JOIN ab b ON b.w = r."to"
                AND b.k = $k WHERE r."from" IN (SELECT w FROM ab)""")
        d['reviews_of_books_keyed_reviewer_after'] = q(f"""SELECT count(DISTINCT r."from") FROM '{G}/reviews.parquet' r JOIN ab b ON b.w = r."to"
                AND b.k = $k WHERE r."from" IN (SELECT w FROM aa)""")
        d['reviews_of_books'] = q(f"""SELECT count(DISTINCT r."from") FROM '{G}/reviews.parquet' r JOIN ab b ON b.w = r."to" AND b.k = $k""")
        d['citing_works'] = q(f"""SELECT count(DISTINCT c."from") FROM '{G}/cites.parquet' c JOIN ab b ON b.w = c."to" AND b.k = $k""")
        d['citing_works_keyed_author_before'] = q(f"""SELECT count(DISTINCT c."from") FROM '{G}/cites.parquet' c JOIN ab b ON b.w = c."to" AND b.k = $k
                WHERE c."from" IN (SELECT w FROM ab WHERE k <> $k)""")
        d['citing_works_keyed_author_after'] = q(f"""SELECT count(DISTINCT c."from") FROM '{G}/cites.parquet' c JOIN ab b ON b.w = c."to" AND b.k = $k
                WHERE c."from" IN (SELECT w FROM aa WHERE k <> $k)""")
        d['citing_people_before'] = q(f"""SELECT count(DISTINCT a2.k) FROM '{G}/cites.parquet' c JOIN ab b ON b.w = c."to" AND b.k = $k
                JOIN ab a2 ON a2.w = c."from" WHERE a2.k <> $k""")
        d['citing_people_after'] = q(f"""SELECT count(DISTINCT a2.k) FROM '{G}/cites.parquet' c JOIN ab b ON b.w = c."to" AND b.k = $k
                JOIN aa a2 ON a2.w = c."from" WHERE a2.k <> $k""")
        rows.append(d)
    with open(OUT / 'panel.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


# ---------------------------------------------------------------- hand-audit samples

def audit(args):
    """Random rows for reading: 60 `linked` per role and 40 single-candidate `possible` per role, with what a reader
    needs (the candidate's identifiers, a few dated works, dated affiliations). Verdicts are written by hand into
    audit-verdicts.csv (sample, pid, verdict, reason)."""
    db = duck()
    G = GRAPH
    S = SCRATCH
    db.execute("SELECT setseed(0.1111)")
    rows = db.execute(f"""WITH x AS (SELECT p.pid, p.role, p.name, p.year, p.journal, p.title, p.inst_printed, p.insts, r.state, r.branch,
                r.key, r.candidates, r.signals, row_number() OVER (PARTITION BY p.role, r.state ORDER BY random()) rn
            FROM '{S}/results.parquet' r JOIN '{S}/positions*.parquet' p USING (pid)
            WHERE (r.state = 'linked' AND NOT r.already_credited) OR (r.state = 'possible' AND r.n_candidates = 1))
            SELECT * FROM x WHERE (state = 'linked' AND rn <= 60) OR (state = 'possible' AND rn <= 40) ORDER BY role, state, rn""").fetchall()
    cols = [d[0] for d in db.description]
    out = []
    for r in rows:
        r = dict(zip(cols, r))
        k = r['key'] or r['candidates']
        lab, an = db.execute(f"SELECT label, anchors FROM '{G}/person.parquet' WHERE key = ?", [k]).fetchone()
        ws = db.execute(f"""SELECT w.year, w.kind, coalesce(w.journal, ''), left(w.label, 60) FROM {keylog(G, 'authored')} a
                JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE a."from" = ? ORDER BY w.year NULLS LAST LIMIT 6""", [k]).fetchall()
        af = db.execute(f"""SELECT i.label, a.source, a.first_year, a.last_year FROM '{G}/affiliated_with.parquet' a
                JOIN '{G}/institution.parquet' i ON i.key = a."to" WHERE a."from" = ? LIMIT 5""", [k]).fetchall()
        out.append(dict(sample=f"{r['role']}|{r['state']}", pid=r['pid'], printed=r['name'], year=r['year'], journal=r['journal'],
                        title=(r['title'] or '')[:90], printed_institution=r['inst_printed'] or '; '.join(r['insts'] or [])[:80],
                        branch=r['branch'], signals=r['signals'], key=k, key_label=lab,
                        key_ids=' '.join(a for a in an if a.split(':')[0] in ('lcnaf', 'orcid', 'wd', 'aha-phd')),
                        key_works=' | '.join(f'{y} {kd} {j[:25]} {t}' for y, kd, j, t in ws),
                        key_affiliations=' | '.join(f'{l} ({s} {a}-{b})' for l, s, a, b in af)))
    with open(OUT / 'audit-sample.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), 'rows')


# ---------------------------------------------------------------- export

GRAPH_TABLE = ROOT / 'data/graph/work-people'


def export(args):
    """data/graph/work-people/part-NN.csv.gz (exact, linked, possible: what build_graph loads) and OUT/links/
    (every uncredited position with its state, `none` included, for the record); ids, printed names and printed
    institutions only. Also OUT/candidate-duplicates.csv.gz: groups of keys the duplicate-group test found to be one
    person, with the works at stake (not merged)."""
    db = duck()
    G = GRAPH
    S = SCRATCH
    # foreword writers and series editors (contributors step): role 'contributor', or held as a contributor-candidate
    if not (S / 'contributors.parquet').exists():
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist([dict(pid=-1, role='', state='', basis='')]), S / 'contributors.parquet')
    q = f"""SELECT p.work, coalesce(c.role, p.role) AS role, p.pos AS position, p.n_auth AS n_authors, p.name AS printed_name,
               p.inst_printed AS printed_institution,
               p.inst_ror AS institution_ror, p.source, concat_ws(';', CASE WHEN p.orcid <> '' THEN 'orcid:' || p.orcid END,
               CASE WHEN p.oa_author <> '' THEN 'openalex:' || p.oa_author END) AS source_person_id, p.year,
               coalesce(c.state, r.state) AS state, CASE WHEN c.state = 'possible' THEN '' ELSE r.key END AS person_key,
               CASE WHEN c.state = 'possible' AND r.candidates = '' THEN r.key ELSE r.candidates END AS candidates,
               CASE WHEN c.state = 'possible' THEN greatest(r.n_candidates, 1) ELSE r.n_candidates END AS n_candidates,
               coalesce(c.basis, r.branch) AS branch, r.signals
            FROM '{S}/results.parquet' r JOIN '{S}/positions*.parquet' p USING (pid)
            LEFT JOIN '{S}/contributors.parquet' c USING (pid) WHERE NOT r.already_credited"""
    cols = ['work', 'role', 'position', 'n_authors', 'printed_name', 'printed_institution', 'institution_ror', 'source',
            'source_person_id', 'year', 'state', 'person_key', 'candidates', 'n_candidates', 'branch', 'signals']

    def rows(where):
        cur = db.execute(q + where + ' ORDER BY p.work, p.role, p.pos')
        while True:
            b = cur.fetchmany(20000)
            if not b:
                break
            for r in b:
                yield dict(zip(cols, r))
    parts = write_parts(GRAPH_TABLE, rows(" AND r.state IN ('exact', 'linked', 'possible')"), cols)
    print('graph table', [(p.name, p.stat().st_size) for p in parts])
    parts = write_parts(OUT / 'links', rows(''), cols)
    print('links', [(p.name, p.stat().st_size) for p in parts])
    # candidate duplicates
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    ids = {k: ' '.join(a for a in an if a.split(':')[0] in ('lcnaf', 'orcid', 'wd', 'aha-phd', 'diss-author'))
           for k, an in db.execute(f"SELECT key, anchors FROM '{G}/person.parquet'").fetchall()}
    nworks = dict(db.execute(f"SELECT \"from\", count(DISTINCT \"to\") FROM {keylog(G, 'authored')} GROUP BY 1").fetchall())
    ps = {tuple(sorted(x)) for x in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/possibly_same.parquet'").fetchall()}
    groups = defaultdict(lambda: dict(works=set(), linked=0, credited_to=Counter(), roles=Counter(), test=''))
    for st, key, sig, work, role in db.execute(f"""SELECT r.state, r.key, r.signals, p.work, p.role FROM '{S}/results.parquet' r
            JOIN '{S}/positions*.parquet' p USING (pid) WHERE r.signals LIKE '%duplicate-keys=%' OR r.signals LIKE '%duplicate-candidates=%'""").fetchall():
        g = re.search(r'duplicate-(?:keys|candidates)=(\S+)', sig).group(1)
        groups[g]['test'] = 'strict (credited meanwhile)' if 'duplicate-keys=' in sig else 'loose (name rare test failed; nothing credited)'
        d = groups[g]
        d['works'].add(work)
        d['roles'][role] += 1
        if st == 'linked':
            d['linked'] += 1
            d['credited_to'][key] += 1
    with gzip.open(OUT / 'candidate-duplicates.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['keys', 'labels', 'identifiers', 'key_works', 'works_at_stake', 'positions_linked_meanwhile', 'credited_meanwhile_to',
                    'pairs_already_possibly_same', 'roles', 'test'])
        for g, d in sorted(groups.items(), key=lambda x: -len(x[1]['works'])):
            ks = g.split('|')
            w.writerow([g, ' | '.join(label.get(k, '') for k in ks), ' | '.join(f'{k}: {ids.get(k, "")}' for k in ks),
                        ' '.join(str(nworks.get(k, 0)) for k in ks), len(d['works']), d['linked'],
                        ' '.join(f'{k}:{n}' for k, n in d['credited_to'].most_common()),
                        sum(1 for a in ks for b in ks if a < b and (a, b) in ps), ' '.join(f'{r}:{n}' for r, n in d['roles'].items()), d['test']])
    rep = json.loads((OUT / 'report.json').read_text())
    rep['candidate_duplicates'] = dict(groups=len(groups), keys=len({k for g in groups for k in g.split('|')}),
                                       works_at_stake=len(set().union(*[d['works'] for d in groups.values()])) if groups else 0,
                                       groups_of_3plus=sum(1 for g in groups if g.count('|') >= 2),
                                       by_test=dict(Counter(d['test'] for d in groups.values())),
                                       note='duplicate-group test (link_work_people.dup_group); not merged; credits meanwhile go to the '
                                            'group representative (identifier-bearing key, else most works)')
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(rep['candidate_duplicates'])


# ---------------------------------------------------------------- defect classes

def defects(args):
    """OUT/defect-classes.json: each symptom on the panel pages as a class with a graph-wide count (owner,
    2026-11-11: fix the graph, not one network). 'today' is build/graph; 'after' is this run's credits (and the
    co-author proposal where it applies). Classes the build can recompute are also in build_graph's linkage.defects."""
    db = duck()
    G = GRAPH
    S = SCRATCH
    rep = json.loads((OUT / 'report.json').read_text())
    mrep = json.loads((OUT / 'coauthor-mints' / 'report.json').read_text()) if (OUT / 'coauthor-mints' / 'report.json').exists() else {}
    q = lambda sql: db.execute(sql).fetchone()
    db.execute(f"CREATE TABLE au AS SELECT DISTINCT \"from\" k, \"to\" w FROM {keylog(G, 'authored')}")
    db.execute(f"""CREATE TABLE nl AS SELECT DISTINCT p.work w, unnest(string_split(r.key, ';')) k, p.role FROM '{S}/results.parquet' r
                   JOIN '{S}/positions*.parquet' p USING (pid) WHERE r.state IN ('exact', 'linked') AND NOT r.already_credited""")
    art_b, art_a = q(f"""SELECT count(*) FILTER (WHERE key NOT IN (SELECT w FROM au)),
            count(*) FILTER (WHERE key NOT IN (SELECT w FROM au) AND key NOT IN (SELECT w FROM nl))
            FROM '{G}/work.parquet' WHERE kind = 'article' AND resolution <> 'unkeyed'""")
    roles = rep['roles']
    multi = q(f"""SELECT count(*) FILTER (WHERE n_unc > 0 AND n_cred > 0), count(*) FILTER (WHERE n_unc_after > 0 AND n_cred > 0) FROM (
            SELECT p.work, count(*) FILTER (WHERE p.credited <> '') n_cred,
                   count(*) FILTER (WHERE p.credited = '') n_unc,
                   count(*) FILTER (WHERE p.credited = '' AND coalesce(r.state, '') NOT IN ('exact', 'linked')) n_unc_after
            FROM '{S}/positions*.parquet' p LEFT JOIN '{S}/results.parquet' r USING (pid) WHERE p.role IN ('author', 'jstor-author') GROUP BY 1)""")
    orcid_only_b = q(f"""SELECT count(*) FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed' AND len(anchors) > 0
            AND len(list_filter(anchors, x -> NOT x LIKE 'orcid-work:%')) = 0""")[0]
    orcid_only_now = q(f"""SELECT count(DISTINCT w.key) FROM '{G}/work.parquet' w JOIN '{S}/positions-title.parquet' t ON t.work = w.key
            WHERE len(list_filter(w.anchors, x -> NOT x LIKE 'orcid-work:%')) = 0""")[0]
    twice = q(f"SELECT count(*) FROM (SELECT \"from\", \"to\" FROM {keylog(G, 'authored')} GROUP BY 1, 2 HAVING count(*) > 1)")[0]
    nojournal = q(f"""SELECT count(*) FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed' AND kind IN ('article', 'other') AND journal IS NULL""")[0]
    db.execute(f"CREATE TABLE oav AS SELECT DISTINCT oa_work FROM '{S}/positions*.parquet' WHERE oa_work <> ''")
    supply = q(f"""SELECT count(DISTINCT w.key) FROM '{G}/work.parquet' w JOIN (SELECT DISTINCT work FROM '{S}/positions*.parquet'
            WHERE oa_work <> '' OR source IN ('jstor', 'jstor-review')) p ON p.work = w.key
            WHERE w.resolution <> 'unkeyed' AND w.kind IN ('article', 'other') AND w.journal IS NULL""")[0]
    self_review = q(f"""SELECT count(*) FROM (SELECT DISTINCT a.k, a.w FROM au a JOIN '{G}/reviews.parquet' r ON r."from" = a.w
            JOIN au b ON b.w = r."to" AND b.k = a.k)""")[0]
    same_title = q(f"""WITH t AS (SELECT a.k, w.key, lower(regexp_replace(left(w.label, 80), '[^A-Za-z0-9]+', ' ', 'g')) tk, w.year
                FROM au a JOIN '{G}/work.parquet' w ON w.key = a.w WHERE w.kind IN ('article', 'other', 'chapter') AND length(w.label) > 25)
            SELECT count(*) FROM (SELECT k, tk FROM t GROUP BY 1, 2 HAVING count(DISTINCT key) > 1)""")[0]
    apos_labels = q(f"SELECT count(*) FROM '{G}/person.parquet' WHERE label LIKE '%’%'")[0]
    dpos = q(f"SELECT count(*) FROM '{S}/results.parquet' WHERE state = 'possible' AND signals LIKE '%duplicate-keys=%'")[0]
    dlink = q(f"SELECT count(*) FROM '{S}/results.parquet' WHERE state = 'linked' AND branch LIKE 'dupgroup:%'")[0]
    br = Counter()
    for role, d in roles.items():
        br.update(d['branches'])
    tied_missing = q(f"""SELECT count(DISTINCT work) FROM read_parquet('{OA_ROWS}', union_by_name=true) WHERE person <> '' AND graph_work = ''""")[0]
    cls = [
        dict(id=1, name='citing or keyed article with no credited author',
             query="JSTOR citing articles (cites.source jstor) with no AUTHORED row; keyed article works with no AUTHORED row",
             cause='key_jstor_articles minted JSTOR items without crediting anyone; DOI routes credit only a claiming author',
             fix='work-people jstor-author and author roles (LINKED_AUTHORED)',
             today=dict(jstor_citing_articles=rep['jstor_citing_articles']['articles'] - rep['jstor_citing_articles']['with_credited_author_before'],
                        keyed_articles=art_b),
             after=dict(jstor_citing_articles=rep['jstor_citing_articles']['articles'] - rep['jstor_citing_articles']['after'], keyed_articles=art_a)),
        dict(id=2, name='review with a printed reviewer and no person key', query='works with reviewer_names and no AUTHORED row',
             cause='key_jstor_reviews stored the printed name as a reviewer-name member and minted no name-only keys',
             fix='work-people reviewer role (printed institution as the strong fact)',
             today=rep['reviews']['with_printed_reviewer'] - rep['reviews']['printed_reviewer_credited_before'],
             after=rep['reviews']['with_printed_reviewer'] - rep['reviews']['printed_reviewer_credited_after']),
        dict(id=3, name='work credited to fewer people than its author list (the record owner only)',
             query='works with an OpenAlex/Crossref/JSTOR author list where some names are credited and some are not',
             cause='ORCID-claim and DOI routes credit the claiming author only',
             fix='author role links; co-author mints (proposal) for historians\' works',
             today=multi[0], after_links=multi[1],
             after_links_and_proposal=None),
        dict(id=4, name='co-authored work absent from the graph',
             query='OpenAlex works of tied authors with no graph work; graph DOIs no OpenAlex/Crossref record covers',
             cause='harvests are History-scoped; the DOI lookup ran 2026-11-09; Crossref harvest holds History-citing journals only',
             fix='not fixed here: needs an ingest decision (works of keyed historians outside History; DOI lookup refresh)',
             today=dict(tied_author_works_not_in_graph=tied_missing, graph_dois_without_any_author_list=None), after='unchanged'),
        dict(id=5, name='one person on several keys blocking links',
             query='possible positions whose live candidates pass the duplicate-group test',
             cause='minting from names (review-credit, H-Net review credits, dissertation authors) before identifiers',
             fix='duplicate-group branch credits the representative meanwhile; candidate-duplicates.csv.gz for merging',
             today=dict(groups=rep.get('candidate_duplicates', {}).get('groups'), keys=rep.get('candidate_duplicates', {}).get('keys')),
             after=dict(positions_linked_through_group=dlink, positions_still_possible=dpos)),
        dict(id=6, name='one work on two keys (preprint and version, same title)',
             query='(person, normalised title) with two or more article/other/chapter work keys',
             cause='DOI routes mint per DOI (10.2196/preprints.46643 and 10.2196/46643); ORCID records list both',
             fix='not fixed: needs a work-dedupe rule (same title, same authors, preprint/version DOIs)', today=same_title, after='unchanged'),
        dict(id=7, name='two authored claims for one person and work', query='AUTHORED (from, to) pairs with count > 1',
             cause='two routes (ORCID and DOI/LC) each minted a claim', fix='explorer lists the work once and counts distinct works; key log unchanged',
             today=twice, after=dict(key_log=twice, explorer='shown once')),
        dict(id=8, name='article/other work without a journal although a record would supply it',
             query="kind article/other, journal null, and an OpenAlex/JSTOR record held for the work",
             cause='works minted from ORCID records carry no journal member', fix='not fixed: a journal backfill from the records',
             today=dict(without_journal=nojournal, record_could_supply=supply), after='unchanged'),
        dict(id=9, name="non-historian co-author with no node",
             query="co-author mentions in state none on works of historian keys", cause='only persons met in history sources were keyed',
             fix='co-author mint proposal (not applied)', today=mrep.get('counts', {}).get('mentions'),
             after=dict(people_to_mint=mrep.get('people_to_mint'), held=mrep.get('counts'))),
        dict(id=10, name='bridge lost because one unkeyed co-author is split across papers',
             query='same full name, co-authors of different historians, no shared fact', cause='the grouping guard',
             fix='possible-same marks; extra facts tested on ORCID mentions', today=mrep.get('guard_cost', {}).get('name_groups_kept_apart'), after='kept apart, marked'),
        dict(id=11, name='work known only from one ORCID record (no DOI): no author list to read',
             query='works whose anchors are all orcid-work:', cause='ORCID works without DOI', fix='OpenAlex records matched by title+year+author family (openalex_people_works) read as author lists',
             today=orcid_only_b, after=dict(now_with_an_author_list=orcid_only_now)),
        dict(id=12, name="the reviewed book's author printed as the author of a review record",
             query='key-log AUTHORED on a review work by the author of the book it reviews; linker rows refused by the book-author check',
             cause='Crossref/OpenAlex review records carry the book author (source metadata)',
             fix='own_book_check refuses such links (state none / possible); the key-log claims are listed, not withdrawn',
             today=dict(key_log_claims=self_review), after=dict(refused_links=br.get('author-of-reviewed-book', 0) + br.get('same-title-as-own-book', 0))),
        dict(id=13, name='the same name printed with curly and straight apostrophes lands in two families',
             query="person labels with ’", cause="link_cited_work_authors.nfold drops ’ but splits on '", fix='apostrophes unified before matching (this script)',
             today=apos_labels, after='matched'),
        dict(id=14, name='an OpenAlex author id that joins two people',
             query="links whose only tie is an OpenAlex author id carrying another ORCID than the key's", cause='OpenAlex profile merges',
             fix='such links held as possible (orcid-differs-tie-only)', today=None, after=dict(held=br.get('orcid-differs-tie-only', 0))),
        dict(id=15, name='rarity measured in History used for a work outside History',
             query='rarity-only links on OpenAlex records fetched by DOI outside the History harvest', cause='population counts are History-scoped',
             fix='a second fact is required there', today=None, after=dict(held=br.get('outside-history-rarity-only', 0))),
    ]
    (OUT / 'defect-classes.json').write_text(json.dumps(cls, indent=1, ensure_ascii=False, default=str) + '\n')
    for c in cls:
        print(c['id'], c['name'], '|', c['today'], '->', c.get('after', c.get('after_links')))


# ---------------------------------------------------------------- the 11-10 linker's candidate lists, rechecked

CITED_AUTHORS = ROOT / 'data/graph/cited-works/authors.csv.gz'


def recheck_cited(args):
    """data/graph/cited-works/authors.csv.gz (link_cited_work_authors, 2026-11-10, exported by export_cited_works):
    its `possible` rows list candidates whose dates rule them out and candidates the name rule above refuses
    ('J. Garry' for 'Jim'). Each listed candidate is checked with the same features and date test; those ruled out are
    removed (a row left with none becomes `none`, branch only-date-excluded / only-name-excluded). Nothing is promoted
    to linked here. The file is rewritten in place (a copy of the original in SCRATCH)."""
    import shutil
    import time
    t0 = time.time()
    db = duck()
    people = WPPeople(db)
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'], P['XDATE'] = tuple(P['FACTS']), tuple(P['XDATE'])
    year = {i: (int(y) if y and y.lstrip('-').isdigit() else None, k) for i, y, k in db.execute(
        f"SELECT id, year, kind FROM read_csv('{ROOT / 'data/graph/cited-works/works.csv.gz'}', all_varchar=true)").fetchall()}
    shutil.copy(CITED_AUTHORS, SCRATCH / 'cited-authors-before-recheck.csv.gz')
    with gzip.open(CITED_AUTHORS, 'rt', newline='', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = list(rd)
    stats = Counter()
    for r in rows:
        if r['state'] != 'possible' or not r['candidates']:
            continue
        y, kind = year.get(r['work'], (None, None))
        sid = r['source_person_id'] or ''
        lcs = [x.split(':', 1)[-1] for x in sid.split(';') if x and not x.startswith(('orcid:', 'openalex:'))] if r['source'] == 'lc' else []
        orc = next((x[6:] for x in sid.split(';') if x.startswith('orcid:')), '')
        hb, hd = L.heading_dates(r['raw_name'])
        p = dict(src=r['source'], swork=r['work'], work_id=r['work'], oa_id='', pos=int(r['position'] or 0), role=r['role'],
                 name=apos(r['raw_name']), title='', year=y, book=r['source'] == 'lc' or kind == 'book', lc=lcs, lc_how='',
                 orcid=orc, oa_author='', rors=[], insts=[], raw_aff=[], citing=0, sb=hb, sd=hd, initial_check='', venue='', oa_type='')
        p['forms'] = forms(p['name'])
        fe = L.features(people, p, mask={'key': None})        # a mask skips the identifier route: only the candidates
        listed = [k for k in r['candidates'].split('|') if k]
        keep, gone_d, gone_n = [], 0, 0
        for k in listed:
            c = fe['cands'].get(k)
            if c is None:
                gone_n += 1
                continue
            ok, how = L.date_test(c, y, p['book'], P)
            if (not ok and str(how).startswith('out-of-window')) or set(c['why']) & L.HARD:
                gone_d += 1
                continue
            keep.append(k)
        stats[f"{r['source']}|{r['role']}|rows"] += 1
        if gone_d or gone_n:
            stats[f"{r['source']}|{r['role']}|changed"] += 1
            stats[f"{r['source']}|{r['role']}|candidates_date_excluded"] += gone_d
            stats[f"{r['source']}|{r['role']}|candidates_name_excluded"] += gone_n
            r['signals'] = (r['signals'] + f' date-excluded={gone_d} name-excluded={gone_n}').strip()
            if not keep:
                r['state'], r['branch'] = 'none', 'only-date-excluded' if gone_d >= gone_n else 'only-name-excluded'
                stats[f"{r['source']}|{r['role']}|now_none"] += 1
            r['candidates'], r['n_candidates'] = '|'.join(keep), str(len(keep))
    with gzip.open(CITED_AUTHORS, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    rep = json.loads((OUT / 'report.json').read_text())
    rep['cited_works_recheck'] = dict(sorted(stats.items()))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(dict(sorted(stats.items())), indent=1), round(time.time() - t0))


# ---------------------------------------------------------------- forewords and series editors (contributors)

LC_REC = '/mnt/e/lc-bib-2016/index/records-*.parquet'
LC_HEAD = '/mnt/e/lc-bib-2016/index/headings-*.parquet'
CONTRIB_PHRASE = re.compile(r'(?i)\b(?:with\s+(?:a|an)\s+)?(?:new\s+)?(?:foreword|forward|preface|introduction|afterword|epilogue|'
                            r'prologue|introductory essay|series (?:general )?editor|general editor)s?\s*(?:and [a-z ]+)?\s*(?:by|written by)\s+([^;\[\]]+)')
CONTRIB_RELATOR = re.compile(r'(?i)foreword|preface|introduction|afterword|epilogue|prologue|writer of|aui|wpr|wac|series editor|general editor')
SERIAL_N = (4, 5, 6)


def contributors(args):
    """Foreword writers and series editors credited as authors of books (owner, 2026-11-11; Graeme Wynn's
    Nature|History|Society forewords were the probe). For every credit of a person on a book (key-log AUTHORED, or a
    work-people link), a role from the LC record when the book has one (100 main entry = author; a name only in 700
    with a foreword/preface/introduction relator, or named in 245 $c after 'foreword by', 'introduction by', 'series
    editor' ... = contributor), and the serial-contributor pattern where LC says nothing: the person credited on N or
    more books of one publisher (DOI prefix, else LC publisher) whose primary author (LC 100, else the first name of the
    author list) is each time somebody else. Outputs: SCRATCH/contributors.parquet (pid -> role override for
    work-people rows), OUT/contributor-claims/ (key-log claims: proposal of withdrawals + CSV), report.json
    'contributors'."""
    db = duck()
    G, S = GRAPH, SCRATCH
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    db.execute(f"""CREATE TABLE bw AS SELECT key, kind, year, anchors FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed'
                   AND (kind = 'book' OR (kind = 'other' AND len(list_filter(anchors, x -> x LIKE 'lccn:%' OR x LIKE 'hnet-book:%')) > 0))""")
    db.execute("CREATE TABLE bl AS SELECT key, replace(a, 'lccn:', '') lccn FROM (SELECT key, unnest(anchors) a FROM bw) WHERE a LIKE 'lccn:%'")
    db.execute(f"CREATE TABLE rec AS SELECT r.control, r.lccn, r.publisher, r.responsibility FROM '{LC_REC}' r JOIN (SELECT DISTINCT lccn FROM bl) USING (lccn)")
    db.execute(f"CREATE TABLE hd AS SELECT h.control, h.pos, h.tag, h.heading, h.relators FROM '{LC_HEAD}' h WHERE h.control IN (SELECT control FROM rec)")
    lc = defaultdict(lambda: dict(main=[], added=[], resp='', pub=''))
    for w, ctl, pub, resp in db.execute("SELECT bl.key, rec.control, rec.publisher, rec.responsibility FROM bl JOIN rec USING (lccn)").fetchall():
        d = lc[w]
        d['resp'] = (d['resp'] + ' ; ' + (resp or '')).strip(' ;')
        d['pub'] = d['pub'] or (pub or '')
        d.setdefault('ctl', set()).add(ctl)
    heads = defaultdict(list)
    for ctl, pos, tag, h, rel in db.execute("SELECT control, pos, tag, heading, relators FROM hd").fetchall():
        heads[ctl].append((tag, h, rel or []))
    for w, d in lc.items():
        for ctl in d.get('ctl', ()):
            for tag, h, rel in heads.get(ctl, ()):
                (d['main'] if tag == '100' else d['added']).append((h, rel))
    print(len(lc), 'books with an LC record', flush=True)

    def lc_role(w, name):
        d = lc.get(w)
        if not d:
            return None
        if any(agree_level(apos(name), apos(h)) in ('full', 'variant', 'initial') for h, _ in d['main']):
            return 'author'
        for clause in re.split(r';', d['resp'] or ''):
            # a name in a plain clause ('John Fiske and John Hartley') is an author even if a later clause adds his foreword
            plain = re.sub(r'(?i)^\s*\[?by\]?\s+', '', clause)
            if not CONTRIB_PHRASE.search(clause) and not re.search(r'(?i)\b(by|edit|compil|translat|select|direct)', plain):
                if any(agree_level(apos(name), apos(x.strip())) in ('full', 'variant') for x in re.split(r',|\band\b|&', plain) if x.strip()):
                    return 'added'
        for clause in re.split(r';', d['resp'] or ''):
            # 'edited and with an introduction by X', 'translated, edited, and with an introduction by X': an editor or
            # translator who also introduces is not a foreword writer
            if re.search(r'(?i)\b(edit|compil|select|translat|transcri|annotat|arrang|collect)', clause.split(' by ')[0]):
                continue
            for seg in CONTRIB_PHRASE.findall(clause):
                for part in re.split(r',|\band\b|&', seg):
                    if part.strip() and agree_level(apos(name), apos(part.strip())) in ('full', 'variant'):
                        return 'contributor'
        for h, rel in d['added']:
            if agree_level(apos(name), apos(h)) in ('full', 'variant', 'initial'):
                # a writer of the introduction who is also an editor, compiler, translator or author is not a
                # foreword writer (Sörlin, Northscapes: 'writer of introduction', 'editor of compilation')
                if any(CONTRIB_RELATOR.search(r) for r in rel) and not any(
                        re.search(r'(?i)editor|compil|translat|author|^ed|^aut|^trl|^edt|^com', r) and not CONTRIB_RELATOR.search(r) for r in rel):
                    return 'contributor'
                return 'added'
        return 'absent'

    def lc_primary(w):
        d = lc.get(w)
        return d['main'][0][0] if d and d['main'] else None
    # credits on books: key-log AUTHORED (with claim keys) and work-people exact/linked positions
    keylog = defaultdict(set)
    claims = defaultdict(list)
    for k, w, c in db.execute(f"""SELECT a."from", a."to", a.claim FROM {keylog_sql(G, 'authored')} a JOIN bw ON bw.key = a."to" """).fetchall():
        keylog[w].add(k)
        claims[k, w].append(c)
    pos = defaultdict(list)          # work -> [(pos, name, key or '', pid, state, branch, credited)]
    for pid, w, ps, nm, n, st, key, br, cred in db.execute(f"""SELECT p.pid, p.work, p.pos, p.name, p.n_auth, r.state, r.key, r.branch, p.credited
            FROM '{S}/positions*.parquet' p JOIN bw ON bw.key = p.work LEFT JOIN '{S}/results.parquet' r USING (pid)
            WHERE p.role = 'author'""").fetchall():
        pos[w].append((ps, nm, cred or (key if st in ('exact', 'linked') else '') or '', pid, st or 'credited', br or '', bool(cred), n))
    group = {}
    for w, an in db.execute("SELECT key, anchors FROM bw").fetchall():
        doi = next((a[4:].split('/')[0] for a in an if a.startswith('doi:')), None)
        pub = lc.get(w, {}).get('pub') if w in lc else None
        group[w] = doi or (re.sub(r'[^a-z]+', ' ', nfold(pub)).strip()[:40] if pub else None) or 'unknown'
    # primary author of each book: LC 100, else the first printed name
    primary = {}
    for w in set(keylog) | set(pos):
        p0 = lc_primary(w)
        if not p0 and pos.get(w):
            p0 = min(pos[w])[1]
        primary[w] = p0
    credits = defaultdict(set)       # k -> books credited (any evidence)
    for w, ks in keylog.items():
        for k in ks:
            credits[k].add(w)
    for w, ps in pos.items():
        for (_, nm, k, pid, st, br, cred, n) in ps:
            if k:
                for x in k.split(';'):
                    credits[x].add(w)
    def same_name(lab, printed):
        """the key's name is the printed one: name agreement, or every family word and the first given name of the
        key inside the printed form (compound family names: 'Rostworowski de Diez Canseco, María')"""
        if not lab or not printed:
            return False
        if agree_level(apos(lab), apos(printed)):
            return True
        toks = set(re.split(r'[^a-z]+', nfold(printed)))
        for f, _, g in forms(apos(lab))[:1]:
            return all(x in toks for x in f.split()) and bool(g) and any(t.startswith(g[0][:1]) for t in toks if t)
        return False
    # books with at most two names (primary + one): an edited volume's co-editors are not foreword writers
    n_names, last_name = {}, {}
    for w, ps in pos.items():
        n_names[w] = max(x[7] or 0 for x in ps)
        last_name[w] = max(ps)[1]
    for w, d in lc.items():
        n_names.setdefault(w, len(d['main']) + len(d['added']))
    for w, ks in keylog.items():
        n_names.setdefault(w, len(ks))
    edit_clause = {}
    for w, d in lc.items():
        edit_clause[w] = ' '.join(c for c in re.split(r';', d['resp'] or '') if re.search(r'(?i)\b(edit|compil|select|direct|dir\.|hrsg|coord)', c))
    serial = {N: set() for N in SERIAL_N}
    serial_books = defaultdict(set)
    for k, ws in credits.items():
        lab = label.get(k, '')
        by_group = defaultdict(set)
        for w in ws:
            p0 = primary.get(w)
            # two names (primary + this one), or three with this one last (the foreword comes after a translator or co-author)
            fam0 = forms(apos(lab))[0][0] if forms(apos(lab)) else ''
            same_family = bool(fam0) and all(x in set(re.split(r'[^a-z]+', nfold(p0 or ''))) for x in fam0.split())
            # a primary of the same family name is a relative writing with them (Gisèle and Serge Berstein), not a series
            if (p0 and not same_name(lab, p0) and not same_family and (n_names.get(w, 0) <= 2 or (n_names.get(w, 0) == 3 and same_name(lab, last_name.get(w))))
                    and not (edit_clause.get(w) and same_name(lab, edit_clause[w]))):
                by_group[group.get(w, 'unknown')].add((w, norm_name(p0)))
        for g, wp in by_group.items():
            prim = {p for _, p in wp}
            for N in SERIAL_N:
                if len(prim) >= N:
                    serial[N].add((k, g))
            if len(prim) >= min(SERIAL_N):
                serial_books[k] |= {w for w, _ in wp}
    # gold: LC-labelled credits
    gold = []
    for k, ws in credits.items():
        for w in ws:
            r = lc_role(w, label.get(k, ''))
            if r in ('author', 'contributor'):
                gold.append((k, w, r))
    test = {}
    for N in SERIAL_N:
        flag = lambda k, w: (k, group.get(w, 'unknown')) in serial[N] and w in serial_books[k]
        tp = sum(1 for k, w, r in gold if r == 'contributor' and flag(k, w))
        fp = sum(1 for k, w, r in gold if r == 'author' and flag(k, w))
        fn = sum(1 for k, w, r in gold if r == 'contributor' and not flag(k, w))
        test[N] = dict(flagged_labelled=tp + fp, contributor=tp, author=fp, precision=round(tp / (tp + fp), 4) if tp + fp else None,
                       recall=round(tp / (tp + fn), 4) if tp + fn else None,
                       people=len({k for k, _ in serial[N]}))
    print(json.dumps(test, indent=1), flush=True)
    N = args.n
    flag = lambda k, w: (k, group.get(w, 'unknown')) in serial[N] and w in serial_books[k]
    # 1) work-people rows: overrides
    over = []
    for w, ps in pos.items():
        first_keylog = any(cred and p == min(x[0] for x in ps) for p, _, _, _, _, _, cred, _ in ps)
        last = max(x[0] for x in ps)
        for (p, nm, k, pid, st, br, cred, n) in ps:
            if cred:
                continue
            r = lc_role(w, nm)
            if st in ('exact', 'linked') and k:
                kk = k.split(';')[0]
                if r == 'contributor':
                    over.append(dict(pid=pid, role='contributor', state='linked', basis='lc-foreword'))
                elif r in ('author', 'added'):
                    continue
                elif flag(kk, w):
                    over.append(dict(pid=pid, role='contributor', state='linked', basis='series-foreword-pattern'))
                elif r is None and first_keylog and p == last and n >= 2 and 'rare' in br and 'fact' not in br:
                    over.append(dict(pid=pid, role='author', state='possible', basis='contributor-candidate'))
            elif r == 'contributor':
                over.append(dict(pid=pid, role='contributor', state=st, basis='lc-foreword'))
    # chapters of a flagged book: a chapter record (DOI = the book's DOI + '-NNN' / '.NNN') copies the book's name list,
    # so the foreword writer of the book is not the author of its chapters ('5 Pioneers', 'Figures')
    flagged_book = set()
    pid_work = {x[3]: (w, x[2]) for w, ps in pos.items() for x in ps}
    for o in over:
        w, k = pid_work.get(o['pid'], (None, ''))
        if o['role'] == 'contributor' and k:
            flagged_book.add((k.split(';')[0], w))
    for (k, w), cs in claims.items():
        r = lc_role(w, label.get(k, ''))
        if r == 'contributor' or (r not in ('author', 'added') and flag(k, w)):
            flagged_book.add((k, w))
    book_doi = {}
    for w, an in db.execute("SELECT key, anchors FROM bw").fetchall():
        for a in an:
            if a.startswith('doi:'):
                book_doi[a[4:]] = w
    db.execute(f"""CREATE TABLE ch AS SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet'
                   WHERE kind IN ('chapter', 'other', 'article') AND resolution <> 'unkeyed') WHERE a LIKE 'doi:%'""")
    parent = {}
    for w, a in db.execute("SELECT key, a FROM ch").fetchall():
        d = a[4:]
        m = re.match(r'^(.+?)[-.](?:ch)?\d{1,4}$', d)
        if m and m.group(1) in book_doi:
            parent[w] = book_doi[m.group(1)]
    for pid, w, k, st in db.execute(f"""SELECT p.pid, p.work, r.key, r.state FROM '{S}/positions*.parquet' p JOIN '{S}/results.parquet' r USING (pid)
            WHERE r.state IN ('exact', 'linked') AND p.work IN (SELECT key FROM ch)""").fetchall():
        if w in parent and (k.split(';')[0], parent[w]) in flagged_book:
            over.append(dict(pid=pid, role='contributor', state='linked', basis='parent-book-contributor'))
    chapter_claims = []
    for k, w, c in db.execute(f"""SELECT a."from", a."to", a.claim FROM {keylog_sql(G, 'authored')} a WHERE a."to" IN (SELECT key FROM ch)""").fetchall():
        if w in parent and (k, parent[w]) in flagged_book:
            chapter_claims.append((k, w, c))
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.Table.from_pylist(over or [dict(pid=-1, role='', state='', basis='')]), S / 'contributors.parquet')
    # 2) key-log claims on books that LC or the pattern make a contribution
    out = OUT / 'contributor-claims'
    out.mkdir(parents=True, exist_ok=True)
    rows, ops = [], []
    for (k, w), cs in claims.items():
        r = lc_role(w, label.get(k, ''))
        basis = 'lc-foreword' if r == 'contributor' else 'series-foreword-pattern' if (r not in ('author', 'added') and flag(k, w)) else None
        if not basis:
            continue
        for c in cs:
            rows.append(dict(claim=c, person=k, label=label.get(k, ''), work=w, primary=primary.get(w) or '', basis=basis,
                             lc_responsibility=(lc.get(w, {}).get('resp') or '')[:200], group=group.get(w, '')))
            ops.append(dict(event='withdraw', key=c, basis=f"{label.get(k, '')} is a {('foreword writer' if basis == 'lc-foreword' else 'series editor or foreword writer')} "
                            f"of this book, not its author ({basis}; link_work_people.py contributors, 2026-11-11). The key log has no "
                            "'contributed' predicate: withdraw the authored claim; re-credit as a contributor once one exists"))
    for k, w, c in chapter_claims:
        rows.append(dict(claim=c, person=k, label=label.get(k, ''), work=w, primary='', basis='parent-book-contributor',
                         lc_responsibility='', group=group.get(parent[w], '')))
        ops.append(dict(event='withdraw', key=c, basis=f"{label.get(k, '')} is a foreword writer or series editor of the book this "
                        "chapter record belongs to, not the chapter's author (parent-book-contributor; link_work_people.py contributors)"))
    with open(out / 'claims.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['claim', 'person', 'label', 'work', 'primary', 'basis', 'lc_responsibility', 'group'])
        wr.writeheader()
        wr.writerows(rows)
    (out / 'proposal.json').write_text(json.dumps(dict(basis='authored claims on books whose LC record or the serial-contributor '
                                                       'pattern shows a foreword writer or series editor, not an author (owner 2026-11-11)',
                                                       decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    top = Counter(r['person'] for r in rows)
    # 3) effects on the derived edges, read from the current build (display tables)
    retyped = {(r['person'], r['work']) for r in rows}
    wp_re = set()
    pmap = dict(db.execute(f"SELECT pid, work FROM '{S}/positions*.parquet'").fetchall()) if over else {}
    kmap = dict(db.execute(f"SELECT pid, key FROM '{S}/results.parquet'").fetchall())
    for o in over:
        if o['role'] == 'contributor' and kmap.get(o['pid']):
            wp_re.add((kmap[o['pid']].split(';')[0], pmap[o['pid']]))
    import pyarrow.parquet as pqq
    has_ev = 'evidence' in pqq.read_schema(G / 'coauthored.parquet').names
    co_lost = rv_lost = co_lost_kl = rv_lost_kl = 0
    if has_ev:
        for a, b, ev, wk, lwk in db.execute(f"SELECT \"from\", \"to\", evidence, work_keys, linked_work_keys FROM '{G}/coauthored.parquet'").fetchall():
            ws = set(lwk or []) if ev == 'linked' else set(wk or []) | set(lwk or [])
            left = {w for w in ws if not ((a, w) in wp_re or (b, w) in wp_re)}
            left_kl = {w for w in left if not ((a, w) in retyped or (b, w) in retyped)}
            co_lost += not left
            co_lost_kl += not left_kl
        for a, b, book in db.execute(f"SELECT \"from\", \"to\", book FROM '{G}/reviewed.parquet'").fetchall():
            rv_lost += (b, book) in wp_re
            rv_lost_kl += (b, book) in wp_re or (b, book) in retyped
    rep = json.loads((OUT / 'report.json').read_text())
    rep['contributors'] = dict(
        books=db.execute('SELECT count(*) FROM bw').fetchone()[0], books_with_lc_record=len(lc),
        detector_test_on_lc_labels=test, chosen_n=N,
        work_people_overrides=dict(Counter(f"{o['role']}|{o['state']}|{o['basis']}" for o in over)),
        keylog_claims_flagged=dict(Counter(r['basis'] for r in rows)), keylog_claims_people=len(top),
        top_people=[dict(key=k, label=label.get(k, ''), claims=n) for k, n in top.most_common(30)],
        coauthored_pairs_lost=dict(work_people_retype=co_lost, plus_keylog_proposal=co_lost_kl),
        reviewed_rows_lost=dict(work_people_retype=rv_lost, plus_keylog_proposal=rv_lost_kl),
        note='contributor rows stay in data/graph/work-people with role contributor (state linked); the loader must write them as '
             'CONTRIBUTED, not AUTHORED, and leave them out of COAUTHORED and REVIEWED')
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(rep['contributors'], indent=1, default=str))


# ---------------------------------------------------------------- title-matched records of the wrong kind

def title_filter(args):
    """A graph book whose OpenAlex record (matched by title, or by a DOI the key log put on the book) is not a book
    (a review of it typed 'book-review', or a journal 'article': key-log book keys carry review DOIs, e.g. w-154887
    holds doi:10.2307/2169427, a review of Skocpol's book) lists the reviewer first and the book's author second: those
    names are not the book's authors (found 2026-11-11 in the two-author book sample). Rewrites
    SCRATCH/positions.parquet and positions-title.parquet without them; the full tables are kept as
    base-all-positions.parquet / title-all-positions.parquet, the dropped rows as *-dropped-positions.parquet."""
    import shutil
    import pyarrow.parquet as pq
    db = duck()
    S, G = SCRATCH, GRAPH
    db.execute(f"""CREATE TABLE book AS SELECT key FROM '{G}/work.parquet' WHERE kind = 'book'
                   OR (kind = 'other' AND len(list_filter(anchors, x -> x LIKE 'lccn:%' OR x LIKE 'hnet-book:%')) > 0)""")
    for tab, full, dropped, oa in (('positions.parquet', 'base-all-positions.parquet', 'base-dropped-positions.parquet', 'oa'),
                                   ('positions-title.parquet', 'title-all-positions.parquet', 'title-dropped-positions.parquet', 'oa-title')):
        if not (S / full).exists():
            shutil.copy(S / tab, S / full)
        db.execute(f"CREATE OR REPLACE TABLE t AS SELECT work oa, any_value(type) AS type FROM read_json('{S}/{oa}/*.jsonl', columns={{'work': 'VARCHAR', 'type': 'VARCHAR'}}) GROUP BY 1")
        cond = """p.oa_work <> '' AND p.work IN (SELECT key FROM book) AND coalesce(t.type, '') NOT IN ('book', 'edited-book', 'monograph')"""
        keep = db.execute(f"SELECT p.* FROM '{S / full}' p LEFT JOIN t ON t.oa = p.oa_work WHERE NOT ({cond}) ORDER BY p.pid").fetch_arrow_table()
        drop = db.execute(f"SELECT p.*, t.type oa_type FROM '{S / full}' p LEFT JOIN t ON t.oa = p.oa_work WHERE {cond}").fetch_arrow_table()
        pq.write_table(keep, S / tab)
        pq.write_table(drop, S / dropped)
        print(tab, 'kept', keep.num_rows, 'dropped', drop.num_rows, 'on', len(set(drop.column('work').to_pylist())), 'books',
              Counter(drop.column('oa_type').to_pylist()).most_common(5))


# ---------------------------------------------------------------- name-only authors of works whose author list was not read

# 2026-11-12 (owner's probe: Jim Clifford p-24137, "Greater London's Rapid Growth" in A Mighty Capital under Threat,
# in OpenAlex and Crossref without his ORCID). The class: a work the graph holds (or a chapter of a volume it holds) whose
# printed author list names a keyed person by name only and was never read by a linker:
#   - unkeyed works with an id (doi:, openalex:, ojs:): the works of keyed people found through one co-author's ORCID
#     (author-works: the other printed authors), the Crossref / Crossref-metadata / journal-metadata / OpenAlex matches of
#     cited works (cited-works works with no author rows; JSTOR-note matches), with their OpenAlex, Crossref, JSTOR or OJS
#     records;
#   - keyed works with a DOI or OpenAlex anchor that the positions of the 11-11 run did not cover (records found since);
#   - the chapters of volumes the graph holds with key-log volume editors and a book DOI, listed by Crossref under the
#     volume's title (one targeted Crossref call per volume, `nameonly-siblings`): only chapters whose DOI extends the
#     volume's DOI, or that carry its ISBN, are read; those not in the graph enter it only when a printed author is
#     credited to a key.
# Every position goes through the same rule (rule_wp, guard) as the work-people positions. Facts added for this class
# (FACTS_NAMEONLY, each admitted only if it holds on the masked-gold and namesake tests; see nameonly-report):
#   coauthor-network  a person credited on the same work by the key log or by an identifier is the candidate's
#                     key-log co-editor, advisor or student (co-author is the existing 'coauthor' fact);
#   volume-network    a person credited (key log) as editor of the chapter's volume, or (key log / identifier) on another
#                     chapter of it, is the candidate's key-log co-author, co-editor, advisor or student;
#   volume-editor     the candidate is a key-log editor of the chapter's volume (an introduction, a chapter of one's own
#                     volume).
# Outputs: NAMEONLY scratch (positions, results, tests), data/graph/name-only/ (credits.csv.gz, chapters.csv.gz),
# data/identifiers/name-only-credits-2026-11-12/ (report.json, links, audit sample).

WP_BASE = Path(os.environ.get('WP_BASE', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/workpeople'))   # the 11-11 positions
AW_FETCH = ROOT / 'build/openalex-author-works-2026-11-11'
CR_META_WORKS = Path('/mnt/e/crossref-meta-2026-11-11/works')
CR_CONTAINERS = ROOT / 'build/crossref-containers-2026-11-11'
CR_BOOKS = ROOT / 'build/crossref-volume-editors-2026-11-11'
CR_SIBLINGS = ROOT / 'build/crossref-volume-chapters-2026-11-12'
JM_OAI = ROOT / 'build/journal-meta-2026-11-11/oai'
NO_OUT = ROOT / 'data/identifiers/name-only-credits-2026-11-12'
NO_TABLE = ROOT / 'data/graph/name-only'
FACTS_NAMEONLY = ('coauthor-network', 'coauthor-colleague', 'volume-network', 'volume-editor')
# facts that may single out one of several dated candidates (rule_wp, ONE_NETWORK_FACT): ties of people, not topic, not
# an OpenAlex profile
NETWORK_FACTS = ('coauthor', 'inst') + FACTS_NAMEONLY + ('topic',)   # topic: 2026-11-12 owner ruling (supports only)
CR_DOI_ANY = re.compile(r'"DOI":\s*"([^"]+)"')
UA_GENERIC = 'historiography-kg/0.1'      # no contact address (privacy guard, 2026-11-12)


def _cr_any(args):
    """Crossref records (one JSON object per line) whose top-level DOI is wanted -> [(doi, authors, kind, title, year,
    container, isbn)]"""
    path, want_file = args
    want = set(open(want_file).read().split())
    out = []
    op = gzip.open if str(path).endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            m = CR_DOI_ANY.search(line)
            if not m:
                continue
            d = None
            if m.group(1).lower() not in want:
                if '"_doi"' not in line:
                    continue
                d = json.loads(line)
                if (d.get('_doi') or '').lower() not in want:
                    continue
            d = d or json.loads(line)
            doi = (d.get('DOI') or d.get('_doi') or '').lower()
            if doi not in want:
                continue
            out.append(dict(doi=doi, authors=cr_authors(d), type=d.get('type'), title=((d.get('title') or [''])[0] or '')[:300],
                            year=cr_year(d), container=((d.get('container-title') or [''])[0] or '')[:300],
                            isbn=[re.sub(r'[^0-9X]', '', x) for x in d.get('ISBN') or []]))
    return out


def cr_authors(d):
    au = []
    for a in d.get('author') or []:
        nm = ' '.join(x for x in (a.get('given'), a.get('family')) if x) or a.get('name') or ''
        au.append(dict(name=nm, orcid=(a.get('ORCID') or '').rsplit('/', 1)[-1],
                       aff=[x.get('name') for x in a.get('affiliation') or [] if x.get('name')][:2]))
    return au


def cr_year(d):
    for k in ('issued', 'published-print', 'published-online', 'published'):
        try:
            return int(d[k]['date-parts'][0][0])
        except Exception:
            continue
    return None


def nameonly_targets(db, S):
    """works whose printed author list no linker has read -> S/targets.parquet (work, kind, year, journal, title, ids)"""
    G = GRAPH
    db.execute(f"CREATE OR REPLACE TABLE oldpos AS SELECT DISTINCT work FROM '{WP_BASE}/positions*.parquet'")
    # works the cited-works author linker read (by their cited-works id, which is the node key unless the log holds it)
    db.execute(f"""CREATE OR REPLACE TABLE cwa AS SELECT DISTINCT work FROM read_csv('{ROOT / 'data/graph/cited-works/authors.csv.gz'}',
                   all_varchar=true)""")
    db.execute(f"""CREATE OR REPLACE TABLE tg AS SELECT key AS work, resolution, kind, year, journal, label AS title, anchors
            FROM '{G}/work.parquet' w
            WHERE ((resolution = 'unkeyed' AND (key LIKE 'doi:%' OR key LIKE 'openalex:%' OR key LIKE 'ojs:%'))
                   OR (resolution <> 'unkeyed' AND kind <> 'thesis'
                       AND len(list_filter(anchors, x -> x LIKE 'doi:%' OR x LIKE 'openalex:%')) > 0
                       AND key NOT IN (SELECT work FROM oldpos)))
              AND key NOT IN (SELECT work FROM cwa)""")
    db.execute("""DELETE FROM tg WHERE work IN (SELECT DISTINCT work FROM (SELECT work, unnest(anchors) a FROM tg)
                  WHERE a IN (SELECT work FROM cwa))""")
    print(db.execute("SELECT resolution = 'unkeyed', kind, count(*) FROM tg GROUP BY ALL ORDER BY 3 DESC").fetchall(), flush=True)
    db.execute(f"COPY tg TO '{S}/targets.parquet'")


def nameonly_extract(args):
    """records for the targets: OpenAlex (History harvest, DOI lookup, the author-works ORCID fetch), Crossref (metadata
    harvest, chapter and book fetches, the reference harvest, the volume-chapter fetch), JSTOR metadata, OJS records"""
    import subprocess
    S = SCRATCH
    S.mkdir(parents=True, exist_ok=True)
    db = duck()
    if not (S / 'targets.parquet').exists() or args.retarget:
        nameonly_targets(db, S)
    db.execute(f"CREATE OR REPLACE TABLE tg AS SELECT * FROM '{S}/targets.parquet'")
    db.execute("""CREATE OR REPLACE TABLE ids AS SELECT DISTINCT work, a FROM (SELECT work, unnest(list_append(anchors, work)) a FROM tg)
                  WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%' OR a LIKE 'ojs:%'""")
    # OpenAlex work ids: anchors, the author-works table, and the authorship rows by DOI
    db.execute(f"""CREATE OR REPLACE TABLE oaw AS
            SELECT DISTINCT substr(a, 10) oa FROM ids WHERE a LIKE 'openalex:%'
            UNION SELECT DISTINCT openalex FROM read_csv('{ROOT / 'data/graph/author-works/works.csv.gz'}', all_varchar=true)
                  WHERE ('doi:' || lower(doi)) IN (SELECT a FROM ids) OR id IN (SELECT a FROM ids)
            UNION SELECT DISTINCT r.work FROM read_parquet('{OA_ROWS}', union_by_name=true) r
                  WHERE r.doi <> '' AND ('doi:' || lower(r.doi)) IN (SELECT a FROM ids)""")
    want = [w[1:] for (w,) in db.execute("SELECT oa FROM oaw WHERE oa LIKE 'W%'").fetchall()]
    print(len(want), 'OpenAlex ids wanted', flush=True)
    (S / 'want-oa.txt').write_text('\n'.join(want))
    out = S / 'oa'
    out.mkdir(parents=True, exist_ok=True)
    if not args.skip_oa:
        jobs = [(p, str(S / 'want-oa.txt'), str(out / (p.parent.name + '-' + p.name.replace('.jsonl.gz', '.jsonl'))))
                for p in sorted(HARVEST.glob('*.jsonl.gz')) + sorted(DOILOOK.glob('part-*.jsonl.gz'))]
        with mp.get_context('fork').Pool(args.workers) as pool:
            print('OpenAlex harvest records', sum(n for _, n in pool.imap_unordered(_oa_one, jobs)), flush=True)
        got = set()
        for fn in out.glob('*.jsonl'):
            for line in open(fn, encoding='utf-8'):
                got.add(line[10:40].split('"')[0][1:])
        (S / 'want-oa2.txt').write_text('\n'.join(w for w in want if w not in got))
        # the author-works ORCID fetch: works outside the History harvest (named doi-lookup-* so that the History
        # population's rarity does not speak for them: guard 'outside-history-rarity-only')
        jobs = [(p, str(S / 'want-oa2.txt'), str(out / ('doi-lookup-aw-' + p.name.replace('.jsonl.gz', '.jsonl'))))
                for p in sorted(AW_FETCH.glob('batch-*.jsonl.gz'))]
        with mp.get_context('fork').Pool(args.workers) as pool:
            print('OpenAlex author-works records', sum(n for _, n in pool.imap_unordered(_oa_one, jobs)), flush=True)
    # which DOIs have an OpenAlex record now
    have = set()
    for fn in out.glob('*.jsonl'):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            if r['doi']:
                have.add(r['doi'])
            have.add('W:' + r['work'])
    dois = [a[4:].lower() for (a,) in db.execute("SELECT DISTINCT a FROM ids WHERE a LIKE 'doi:%'").fetchall()]
    rest = [d for d in dois if d not in have]
    print(len(dois), 'DOIs;', len(rest), 'without an OpenAlex record', flush=True)
    (S / 'want-cr.txt').write_text('\n'.join(rest))
    if not args.skip_cr:
        files = sorted(CR_META_WORKS.glob('*.jsonl.gz')) + sorted(CR_CONTAINERS.glob('*.jsonl')) + sorted(CR_BOOKS.glob('*.jsonl'))
        if not args.skip_refs:
            files += sorted(CROSSREF.glob('journal_*.jsonl.gz'))
        recs = {}
        with mp.get_context('fork').Pool(args.workers) as pool:
            for n, o in enumerate(pool.imap_unordered(_cr_any, [(f, str(S / 'want-cr.txt')) for f in files], chunksize=8)):
                for r in o:
                    if r['doi'] not in recs or len(r['authors']) > len(recs[r['doi']]['authors']):
                        recs[r['doi']] = r
                if n % 2000 == 0:
                    print('crossref files', n, len(recs), flush=True)
        with open(S / 'crossref.jsonl', 'w', encoding='utf-8') as f:
            for r in recs.values():
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(len(recs), 'Crossref records', flush=True)
    # JSTOR metadata for 10.2307 DOIs still without a record
    cr_have = set()
    if (S / 'crossref.jsonl').exists():
        for line in open(S / 'crossref.jsonl', encoding='utf-8'):
            r = json.loads(line)
            if r['authors']:
                cr_have.add(r['doi'])
    jrest = {d for d in rest if d.startswith('10.2307/') and d not in cr_have}
    if not args.skip_jstor and jrest:
        import orjson
        c = sqlite3.connect(f'file:{JSTOR_RECORDS}?mode=ro', uri=True)
        keep = {iid: doi.strip().lower() for iid, doi in c.execute("SELECT item_id, doi FROM records WHERE doi IS NOT NULL")
                if doi.strip().lower() in jrest}
        print(len(keep), 'JSTOR records wanted', flush=True)
        p = subprocess.Popen(['zcat', JSTOR_META], stdout=subprocess.PIPE, bufsize=1 << 20)
        with open(S / 'jstor.jsonl', 'w', encoding='utf-8') as o:
            for line in p.stdout:
                d = orjson.loads(line)
                iid = d.get('item_id')
                if iid not in keep:
                    continue
                cr = sorted(d.get('creators') or [], key=lambda x: x.get('order') or 0)
                names = []
                for x in cr:
                    fn = re.sub(r'<[^>]+>[^<]*</[^>]+>', ' ', x.get('first_name') or '').strip()
                    ln = re.sub(r'<[^>]+>[^<]*</[^>]+>', ' ', x.get('last_name') or '').strip()
                    if ln or fn:
                        names.append((fn + ' ' + ln).strip())
                o.write(json.dumps(dict(doi=keep[iid], iid=iid, names=names), ensure_ascii=False) + '\n')
    # OJS records (journal-metadata harvest) of ojs: works
    want_ojs = {a for (a,) in db.execute("SELECT DISTINCT a FROM ids WHERE a LIKE 'ojs:%'").fetchall()}
    if want_ojs:
        with open(S / 'ojs.jsonl', 'w', encoding='utf-8') as o:
            for fn in sorted(JM_OAI.glob('*')):
                op = gzip.open if fn.name.endswith('.gz') else open
                with op(fn, 'rt', encoding='utf-8') as f:
                    for line in f:
                        d = json.loads(line)
                        if d.get('sid') in want_ojs and d.get('authors_are_full_names'):
                            o.write(json.dumps(dict(sid=d['sid'], names=[x for x in d.get('authors') or [] if x and x.strip(', ')]),
                                               ensure_ascii=False) + '\n')
    print('extract done', flush=True)


class CrossrefRefused(Exception):
    pass


class PoliteCrossref:
    """One request at a time, at most one per `gap` seconds, a generic client name and no contact address (a local
    privacy guard refuses requests carrying it). A 429 or 403 stops the run: it is written to `refusals` and raised,
    never retried or worked around. Other errors are retried twice with a pause."""

    def __init__(self, refusals, gap=1.0):
        self.refusals, self.gap, self.last, self.calls = Path(refusals), gap, 0.0, 0

    def get(self, url):
        import time
        import urllib.error
        import urllib.request
        status = 'error'
        for attempt in range(3):
            wait = self.last + self.gap - time.time()
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.calls += 1
            try:
                req = urllib.request.Request(url, headers={'User-Agent': UA_GENERIC})
                with urllib.request.urlopen(req, timeout=60) as r:
                    return 'ok', json.loads(r.read())['message']
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    rec = dict(at=time.strftime('%Y-%m-%dT%H:%M:%S'), code=e.code, url=url, calls=self.calls,
                               retry_after=e.headers.get('Retry-After') if e.headers else None)
                    with open(self.refusals, 'a') as f:
                        f.write(json.dumps(rec) + '\n')
                    raise CrossrefRefused(rec)
                if e.code == 404:
                    return 'not-found', None
                status = f'error:{str(e)[:80]}'
            except Exception as e:
                status = f'error:{str(e)[:80]}'
            time.sleep(5 * (attempt + 1))
        return status, None


def sibling_targets(db, G, tier):
    """volumes to fetch, in priority order -> [(key, label, year, dois, priority)]
    tier keylog: volumes with key-log editors (EDITED, AUTHORED volume-editor) and chapters in the graph;
    tier linked: volumes whose editors are linked only (EDITED evidence linked with role volume-editor, author-editor or
    unknown; AUTHORED volume-editor), chapters in the graph or kind book.
    The book DOI is the volume's own doi: anchor, else the one container DOI its chapters' records give.
    Priority 0: a chapter of the volume has a key-log author, or the volume (or a chapter) is cited by 5+ theses;
    then a stable random order."""
    db.execute(f"""CREATE OR REPLACE TABLE ed_k AS SELECT DISTINCT "to" v FROM {keylog(G, 'edited')}
                   UNION SELECT DISTINCT "to" FROM {keylog(G, 'authored')} WHERE role = 'volume-editor'""")
    db.execute(f"""CREATE OR REPLACE TABLE ed_l AS SELECT DISTINCT "to" v FROM '{G}/edited.parquet'
                   WHERE evidence = 'linked' AND coalesce(role, 'unknown') IN ('volume-editor', 'author-editor', 'unknown')
                   UNION SELECT DISTINCT "to" FROM '{G}/authored.parquet' WHERE evidence = 'linked' AND role = 'volume-editor'""")
    db.execute(f"""CREATE OR REPLACE TABLE cdoi AS SELECT volume_work v, any_value('doi:' || lower(container_doi)) d
            FROM read_csv('{ROOT / 'data/graph/work-containers.csv.gz'}', all_varchar=true)
            WHERE container_doi IS NOT NULL AND volume_work IS NOT NULL GROUP BY 1 HAVING count(DISTINCT lower(container_doi)) = 1""")
    db.execute(f"""CREATE OR REPLACE TABLE pv AS SELECT DISTINCT "to" v FROM '{G}/part_of.parquet'""")
    if tier == 'keylog':
        sel = "w.key IN (SELECT v FROM pv) AND w.key IN (SELECT v FROM ed_k)"
    else:
        sel = ("(w.key IN (SELECT v FROM pv) OR w.kind = 'book') AND w.key IN (SELECT v FROM ed_l) "
               "AND w.key NOT IN (SELECT v FROM ed_k)")
    db.execute(f"""CREATE OR REPLACE TABLE vols AS SELECT w.key, w.label, w.year,
                CASE WHEN len(list_filter(w.anchors, x -> x LIKE 'doi:%')) > 0
                THEN list_filter(w.anchors, x -> x LIKE 'doi:%') ELSE [c.d] END dois
            FROM '{G}/work.parquet' w LEFT JOIN cdoi c ON c.v = w.key
            WHERE {sel} AND (len(list_filter(w.anchors, x -> x LIKE 'doi:%')) > 0 OR c.d IS NOT NULL)""")
    db.execute(f"""CREATE OR REPLACE TABLE pri AS
            WITH ch AS (SELECT p."from" c, p."to" v FROM '{G}/part_of.parquet' p JOIN vols ON vols.key = p."to"),
                 ka AS (SELECT DISTINCT ch.v FROM ch JOIN {keylog(G, 'authored')} a ON a."to" = ch.c WHERE coalesce(a.role, 'author') = 'author'),
                 th AS (SELECT x.v, count(DISTINCT t."from") n FROM (SELECT key v, key w FROM vols UNION ALL SELECT v, c FROM ch) x
                        JOIN '{G}/cites.parquet' t ON t."to" = x.w WHERE t.source LIKE '%thesis%' GROUP BY 1)
            SELECT vols.key, (vols.key IN (SELECT v FROM ka)) has_ka, coalesce(th.n, 0) theses
            FROM vols LEFT JOIN th ON th.v = vols.key""")
    import hashlib
    rows = db.execute("SELECT v.key, v.label, v.year, v.dois, p.has_ka, p.theses FROM vols v JOIN pri p USING (key)").fetchall()
    out = []
    for key, label, year, dois, ka, th in rows:
        pr = 0 if (ka or th >= 5) else 1
        out.append((pr, hashlib.md5(key.encode()).hexdigest(), key, label, year, dois, ka, th))
    out.sort()
    return out


def nameonly_siblings(args):
    """Chapters of volumes the graph holds with editors and a book DOI, found by Crossref under the volume's title
    (query.container-title within the book DOI's prefix; the chapters are then kept only by DOI or ISBN, see
    sibling_chapters; one call per volume; resumable: records of the first trial query, an exact container-title filter,
    have no 'query' field and are not counted as done; build/crossref-volume-chapters-2026-11-12/part-NNN.jsonl).
    --tier keylog: volumes with key-log editors (the 11-12 list); --tier linked: volumes whose editors are linked only
    (pass seven), capped by --max. Priority first (sibling_targets), then a stable random order. Polite: PoliteCrossref
    (one call at a time, at most one a second, generic client name, no contact address; stops on 429/403, recorded in
    refusals.jsonl)."""
    import urllib.parse
    db = duck()
    G = GRAPH
    CR_SIBLINGS.mkdir(parents=True, exist_ok=True)
    vols = sibling_targets(db, G, args.tier)
    done = set()
    for fn in CR_SIBLINGS.glob('part-*.jsonl'):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            if r.get('query') == 'container-title-in-prefix' and not str(r.get('status', '')).startswith('error'):
                done.add(r['volume'])
    first = [k for k in (args.first or '').split(',') if k]
    todo = [v for v in vols if v[2] not in done]
    todo.sort(key=lambda v: (v[2] not in first, v[0], v[1]))
    todo = todo[:args.max]
    print(args.tier, len(vols), 'volumes;', sum(v[2] in done for v in vols), 'done;', len(todo), 'to fetch;',
          sum(v[0] == 0 for v in todo), 'priority', flush=True)
    part = CR_SIBLINGS / f'part-{len(list(CR_SIBLINGS.glob("part-*.jsonl"))):03d}.jsonl'
    cr = PoliteCrossref(CR_SIBLINGS / 'refusals.jsonl', gap=max(1.0, args.gap))
    n = 0
    with open(part, 'a', encoding='utf-8') as o:
        for pr, _h, key, label, year, dois, ka, th in todo:
            title = re.split(r'\s+/\s+|:\s', label or '')[0].strip()
            base = dict(volume=key, title=title, year=year, dois=dois, query='container-title-in-prefix', tier=args.tier,
                        priority=pr)
            if len(title) < 4:
                o.write(json.dumps(dict(base, status='no-title', items=[])) + '\n')
                continue
            prefix = dois[0][4:].split('/')[0]
            q = urllib.parse.urlencode({'query.container-title': title, 'filter': f'prefix:{prefix}', 'rows': 100,
                                        'select': 'DOI,type,title,author,editor,container-title,ISBN,issued,publisher'})
            try:
                status, msg = cr.get(f'https://api.crossref.org/works?{q}')
            except CrossrefRefused as e:
                print('refused, stopping:', e, flush=True)
                break
            o.write(json.dumps(dict(base, status=status, items=(msg or {}).get('items') or []), ensure_ascii=False) + '\n')
            o.flush()
            n += 1
            if n % 100 == 0:
                print(n, 'volumes', cr.calls, 'calls', flush=True)
    print('volumes', n, 'calls', cr.calls, flush=True)


def sibling_chapters(G, db):
    """the fetched chapter lists -> {chapter doi: dict(volume, title, year, authors, kind)} for chapters whose DOI
    extends the volume's DOI (next character not a letter or digit) or that carry the volume's ISBN"""
    isbn = {k: re.sub(r'[^0-9X]', '', (i or '').upper()) for k, i in db.execute(f"SELECT key, isbn FROM '{G}/work.parquet' WHERE isbn IS NOT NULL").fetchall()}
    out = {}
    for fn in sorted(CR_SIBLINGS.glob('part-*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            vd = [d[4:].lower() for d in r.get('dois') or []]
            for it in r.get('items') or []:
                doi = (it.get('DOI') or '').lower()
                if not doi or doi in vd or it.get('type') not in ('book-chapter', 'book-section', 'book-part', 'reference-entry', 'other'):
                    continue
                ok = any(doi.startswith(v) and len(doi) > len(v) and not doi[len(v)].isalnum() for v in vd)
                basis = 'chapter-doi'
                if not ok and isbn.get(r['volume']):
                    ok = isbn[r['volume']] in {re.sub(r'[^0-9X]', '', x.upper()) for x in it.get('ISBN') or []}
                    basis = 'isbn'
                if not ok:
                    continue
                t = ((it.get('title') or [''])[0] or '').strip()
                if not it.get('author') or re.match(r'(?i)^(front|back) matter|^(table of )?contents$|^index$|^notes$|^bibliography$', t):
                    continue
                out[doi] = dict(volume=r['volume'], title=t[:300], year=cr_year(it), authors=cr_authors(it), kind='chapter',
                                publisher=it.get('publisher') or '', basis=basis)
    return out


# identifier credits used as a work's known authors: an ORCID that OpenAlex put on its author profile (not printed on
# the work) is not one (2026-11-12: OpenAlex profiles merge namesakes; Andrew Watson p-21351)
KNOWN_EXACT_SQL = "(a.evidence = 'keylog' OR (a.state = 'exact' AND coalesce(a.source, '') <> 'author-works:openalex-author-orcid'))"


def volume_people_rows(db, G, chap, extra=None):
    """[dict(work=chapter, key, how, volume)]: key-log editors of the chapter's volume (EDITED, AUTHORED volume-editor) and
    the key-log / identifier authors of its other chapters"""
    vol_of = defaultdict(set)
    for c, v in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/part_of.parquet'").fetchall():
        if c in chap:
            vol_of[c].add(v)
    for c, v in (extra or {}).items():
        vol_of[c].add(v)
    vols = sorted({v for vs in vol_of.values() for v in vs})
    db.register('vv', db.execute('SELECT unnest(?) AS v', [vols]).df())
    ved = defaultdict(set)
    for k, v in db.execute(f"""SELECT "from", "to" FROM {keylog(G, 'edited')} JOIN vv ON vv.v = "to"
            UNION SELECT "from", "to" FROM {keylog(G, 'authored')} JOIN vv ON vv.v = "to" WHERE role = 'volume-editor'""").fetchall():
        ved[v].add(k)
    vch = defaultdict(set)
    for k, c, v in db.execute(f"""SELECT a."from", p."from", p."to" FROM '{G}/part_of.parquet' p JOIN vv ON vv.v = p."to"
            JOIN '{G}/authored.parquet' a ON a."to" = p."from" WHERE {KNOWN_EXACT_SQL}""").fetchall():
        vch[v].add((k, c))
    vp = []
    for c, vs in vol_of.items():
        for v in vs:
            for k in ved.get(v, ()):
                vp.append(dict(work=c, key=k, how='volume-editor', volume=v))
            for k, c2 in vch.get(v, ()):
                if c2 != c:
                    vp.append(dict(work=c, key=k, how='other-chapter', volume=v))
    return vp


def volume_people_cmd(args):
    """S/volume-people.parquet for the chapters among S/positions*.parquet (the 11-11 positions: link --new-facts)"""
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = duck()
    chap = {w for (w,) in db.execute(f"""SELECT DISTINCT p.work FROM '{SCRATCH}/positions*.parquet' p
            JOIN '{GRAPH}/work.parquet' w ON w.key = p.work WHERE w.kind = 'chapter'""").fetchall()}
    vp = volume_people_rows(db, GRAPH, chap)
    pq.write_table(pa.Table.from_pylist(vp or [dict(work='', key='', how='', volume='')]), SCRATCH / 'volume-people.parquet')
    print(len(chap), 'chapters,', len(vp), 'rows')


def nameonly_positions(args):
    """S/positions.parquet (role author, the work-people schema) for the targets and the fetched sibling chapters, with
    `credited` set where a printed name agrees with a person the graph already credits on the work by the key log or
    an identifier (the gold rows); names agreeing with a person credited there by a rule are dropped (already linked).
    Also S/credited-extra.parquet (work, key: identifier credits, read as the work's known authors) and
    S/volume-people.parquet (chapter, key, how: key-log editors of its volume, key-log or identifier authors of its other
    chapters)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    S, G = SCRATCH, GRAPH
    db = duck()
    db.execute(f"CREATE OR REPLACE TABLE tg AS SELECT * FROM '{S}/targets.parquet'")
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    orcid_of = defaultdict(set)
    for k, o in db.execute(f"SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'orcid:%'").fetchall():
        orcid_of[k].add(o[6:])
    work = {k: (kind, year, journal, title) for k, kind, year, journal, title in
            db.execute("SELECT work, kind, year, journal, title FROM tg").fetchall()}
    id_work = defaultdict(set)
    for w, a in db.execute("SELECT DISTINCT work, a FROM (SELECT work, unnest(list_append(anchors, work)) a FROM tg)").fetchall():
        id_work[a.lower() if a.startswith('doi:') else a].add(w)
    # credits on the targets: key log or identifier (gold), rule (already linked)
    sib = sibling_chapters(G, db)
    known = {}
    for d in db.execute(f"SELECT key FROM '{G}/work.parquet' WHERE key LIKE 'doi:%'").fetchall():
        known[d[0]] = 1
    for a, k in db.execute(f"""SELECT a, key FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a LIKE 'doi:%'""").fetchall():
        known[a.lower()] = k
    # chapters an earlier export of this class added to the graph count as not held (they exist only through it)
    for (c,) in db.execute(f"""SELECT DISTINCT "from" FROM '{G}/part_of.parquet' WHERE source = 'name-only-volume'""").fetchall():
        known.pop(c, None)
    new_sib = {d: v for d, v in sib.items() if ('doi:' + d) not in known}
    print(len(sib), 'sibling chapters;', len(new_sib), 'not in the graph', flush=True)
    keys = sorted(work)
    db.register('kk', db.execute('SELECT unnest(?) AS key', [keys]).df())
    gold_cr, rule_cr = defaultdict(set), defaultdict(set)
    # this class's own earlier credits (source name-only:*, loaded by an earlier build) are neither gold nor 'already linked'
    for k, w, known in db.execute(f"""SELECT a."from", a."to", {KNOWN_EXACT_SQL} FROM '{G}/authored.parquet' a
            JOIN kk ON kk.key = a."to" WHERE coalesce(a.source, '') NOT LIKE 'name-only:%'""").fetchall():
        (gold_cr if known else rule_cr)[w].add(k)
    extra = [dict(work=w, key=k) for w, ks in gold_cr.items() for k in ks]
    # positions from the records
    rows = []
    stats = Counter()

    def add(role_src, w, i, n, nm, orcid='', oa_author='', rors=(), insts=(), raw_aff=(), oa_work='', inst=''):
        kind, year, journal, title = work[w]
        row = dict(role='author', source=role_src, work=w, pos=i, n_auth=n, name=nm, year=year, journal=journal or '',
                   kind=kind or '', title=(title or '')[:200], orcid=orcid or '', oa_author=oa_author or '', rors=list(rors),
                   insts=list(insts), raw_aff=list(raw_aff), oa_work=oa_work, inst_printed=(inst or '')[:200], inst_ror='',
                   inst_ror_name='', sig_conf=0.0, credited='', credited_how='')
        ks = gold_cr.get(w, ())
        hit = [k for k in ks if row['orcid'] and row['orcid'] in orcid_of.get(k, ())]
        if hit:
            row.update(credited=hit[0], credited_how='orcid')
        else:
            best = None
            for k in ks:
                lev = agree_level(nm, label.get(k, ''))
                if lev and (best is None or ('full', 'variant', 'initial').index(lev) < ('full', 'variant', 'initial').index(best[1])):
                    best = (k, lev)
            if best:
                row.update(credited=best[0], credited_how='name:' + best[1])
            elif any(agree_level(nm, label.get(k, '')) for k in rule_cr.get(w, ())):
                stats['dropped_already_linked_by_rule'] += 1
                return
        rows.append(row)
    done = set()
    # OpenAlex records first (the most authors when two)
    best = {}
    for fn in sorted((S / 'oa').glob('*.jsonl')):
        for line in open(fn, encoding='utf-8'):
            r = json.loads(line)
            if 'authorships' not in r:      # oa/doi-lookup-extra.jsonl (nameonly-extra) lists ids only, for the outside set
                continue
            ws = set(id_work.get('openalex:' + r['work'], ())) | (set(id_work.get('doi:' + r['doi'], ())) if r['doi'] else set())
            for w in ws:
                if w not in best or len(r['authorships']) > len(best[w]['authorships']):
                    best[w] = r
    refs = {}
    book_like = ('book', 'edited-book', 'monograph')
    for w, r in best.items():
        if work[w][0] == 'book' and (r.get('type') or '') not in book_like:
            stats['dropped_book_with_nonbook_record'] += 1     # title_filter: a review record on a book key
            continue
        done.add(w)
        refs[r['work']] = r['refs']
        for a in r['authorships']:
            nm = a['name'] or a['raw'] or ''
            if a['raw'] and forms(nm) and initial_only(forms(nm)[0][2]) and forms(a['raw']) and not initial_only(forms(a['raw'])[0][2]):
                nm = a['raw']
            if nm:
                add('openalex', w, a['pos'], len(r['authorships']), nm, a['orcid'], a['author'], a['rors'], a['insts'], a['raw_aff'], r['work'])
    stats['works_openalex'] = len(done)
    # Crossref
    if (S / 'crossref.jsonl').exists():
        for line in open(S / 'crossref.jsonl', encoding='utf-8'):
            r = json.loads(line)
            for w in id_work.get('doi:' + r['doi'], ()):
                if w in done or not r['authors']:
                    continue
                if work[w][0] == 'book' and r['type'] not in ('book', 'monograph', 'edited-book', 'reference-book'):
                    stats['dropped_book_with_nonbook_record'] += 1
                    continue
                done.add(w)
                stats['works_crossref'] += 1
                for i, a in enumerate(r['authors']):
                    if a['name']:
                        add('crossref', w, i, len(r['authors']), a['name'], a['orcid'], raw_aff=a['aff'], inst=(a['aff'] or [''])[0])
    if (S / 'jstor.jsonl').exists():
        for line in open(S / 'jstor.jsonl', encoding='utf-8'):
            r = json.loads(line)
            for w in id_work.get('doi:' + r['doi'], ()):
                if w in done or not r['names']:
                    continue
                done.add(w)
                stats['works_jstor'] += 1
                for i, nm in enumerate(r['names']):
                    add('jstor', w, i, len(r['names']), nm)
    if (S / 'ojs.jsonl').exists():
        for line in open(S / 'ojs.jsonl', encoding='utf-8'):
            r = json.loads(line)
            for w in id_work.get(r['sid'], ()):
                if w in done or not r['names']:
                    continue
                done.add(w)
                stats['works_ojs'] += 1
                for i, nm in enumerate(r['names']):
                    add('ojs', w, i, len(r['names']), nm)
    # sibling chapters not in the graph: works of their own (unkeyed doi: ids), positions source crossref-volume
    sib_rows = []
    vyear = dict(db.execute(f"SELECT key, year FROM '{G}/work.parquet' WHERE key IN (SELECT unnest(?))", [sorted({v['volume'] for v in new_sib.values()})]).fetchall())
    for d, v in new_sib.items():
        w = 'doi:' + d
        work[w] = ('chapter', v['year'] or vyear.get(v['volume']), None, v['title'])
        sib_rows.append(dict(id=w, doi=d, title=v['title'], year=v['year'] or vyear.get(v['volume']), kind='chapter',
                             volume_work=v['volume'], volume_basis=v['basis'], publisher=v['publisher'], n_authors=len(v['authors']),
                             authors=json.dumps([dict(pos=i, name=a['name'], orcid=a['orcid'], aff=a['aff']) for i, a in enumerate(v['authors'])],
                                                ensure_ascii=False)))
        stats['works_crossref_volume'] += 1
        for i, a in enumerate(v['authors']):
            if a['name']:
                add('crossref-volume', w, i, len(v['authors']), a['name'], a['orcid'], raw_aff=a['aff'], inst=(a['aff'] or [''])[0])
    stats['target_works'] = len(keys)
    stats['works_without_record'] = len(set(keys) - done)
    for i, r in enumerate(rows):
        r['pid'] = 10_000_000 + i          # apart from the 11-11 pids
    # one credited key per position (the better agreement keeps it), as in positions()
    by = defaultdict(list)
    for i, r in enumerate(rows):
        if r['credited']:
            by[r['work'], r['credited']].append(i)
    rank = lambda r: (0 if r['credited_how'] == 'orcid' else 1 + ('full', 'variant', 'initial').index(r['credited_how'][5:]), r['pos'])
    for ids in by.values():
        for i in sorted(ids, key=lambda i: rank(rows[i]))[1:]:
            rows[i]['credited'], rows[i]['credited_how'] = '', ''
    schema = pq.read_schema(WP_BASE / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), S / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist(extra or [dict(work='', key='')]), S / 'credited-extra.parquet')
    pq.write_table(pa.Table.from_pylist(sib_rows or [dict(id='', doi='', title='', year=None, kind='', volume_work='', volume_basis='', publisher='',
                                                          n_authors=0, authors='')]), S / 'sibling-chapters.parquet')
    with open(S / 'oa-refs.jsonl', 'w') as f:
        for k, v in refs.items():
            if v:
                f.write(json.dumps([k, v]) + '\n')
    # people on each chapter's volume: key-log editors of the volume, key-log / identifier authors of its other chapters
    vp = volume_people_rows(db, G, {w for w in work if work[w][0] == 'chapter'}, {'doi:' + d: v['volume'] for d, v in new_sib.items()})
    pq.write_table(pa.Table.from_pylist(vp or [dict(work='', key='', how='', volume='')]), S / 'volume-people.parquet')
    stats['positions'] = len(rows)
    stats['positions_credited_gold'] = sum(1 for r in rows if r['credited'])
    stats['volume_people_rows'] = len(vp)
    print(json.dumps(dict(stats), indent=1), flush=True)
    (S / 'positions-stats.json').write_text(json.dumps(dict(stats), indent=1) + '\n')


def _facts_of(sig):
    out = set()
    for t in (sig or '').split():
        f = t.split(':')[0]
        if f in ('inst', 'coauthor', 'oa-author-tie', 'selfcite', 'student-thesis-cites', 'journal', 'own-thesis-cites',
                 'inst-name', 'topic') + FACTS_NAMEONLY:
            out.add(f)
    return out


def nameonly_report(args):
    """NO_OUT/report.json: the class (positions with a name-compatible key), states, branches, the gold and namesake
    tests by branch and by fact, the ablation against a run without FACTS_NAMEONLY (S/*-base.parquet, if present), and
    NO_OUT/audit-sample.csv (40 linked rows for reading)."""
    db = duck()
    S, G = SCRATCH, GRAPH
    NO_OUT.mkdir(parents=True, exist_ok=True)
    q = lambda sql: db.execute(sql).fetchall()
    db.execute(f"""CREATE TABLE allp AS SELECT p.*, coalesce(r.state, CASE WHEN p.credited <> '' THEN 'credited' END) state,
            r.key, r.branch, r.candidates, r.n_candidates, r.signals, r.already_credited
            FROM '{S}/positions.parquet' p LEFT JOIN '{S}/results.parquet' r USING (pid)""")
    stats = json.loads((S / 'positions-stats.json').read_text())
    rep = dict(date='2026-11-12', graph=str(G), what=(
        'printed author positions on works whose author list no linker had read (unkeyed works with an id, keyed works '
        'outside the 11-11 positions, chapters of key-log edited volumes listed by Crossref); see link_work_people.py, '
        'section name-only'), extraction=stats)
    rep['targets'] = {f'{u}|{k}': n for u, k, n in q(f"""SELECT CASE WHEN resolution = 'unkeyed' THEN 'unkeyed' ELSE 'keyed' END, kind, count(*)
            FROM '{S}/targets.parquet' GROUP BY ALL ORDER BY 3 DESC""")}
    rep['positions_by_source_state'] = {f'{a}|{b}': n for a, b, n in q("SELECT source, state, count(*) FROM allp GROUP BY ALL ORDER BY 1, 3 DESC")}
    named = "state IN ('exact', 'linked', 'possible', 'ambiguous') OR branch IN ('only-date-excluded', 'only-proven-namesakes', 'author-of-reviewed-book', 'same-title-as-own-book')"
    c = q(f"""SELECT count(*), count(DISTINCT work), count(*) FILTER (WHERE {named}), count(DISTINCT work) FILTER (WHERE {named}),
              count(*) FILTER (WHERE state IN ('exact', 'linked') AND NOT already_credited),
              count(DISTINCT work) FILTER (WHERE state IN ('exact', 'linked') AND NOT already_credited),
              count(*) FILTER (WHERE state IN ('possible', 'ambiguous')), count(DISTINCT work) FILTER (WHERE state IN ('possible', 'ambiguous'))
           FROM allp WHERE state <> 'credited'""")[0]
    rep['class'] = dict(
        uncredited_positions=c[0], works=c[1],
        positions_naming_a_keyed_person_by_name=c[2], works_naming_a_keyed_person=c[3],
        credited_now_exact_or_linked=c[4], works_credited_now=c[5],
        open_possible_or_ambiguous=c[6], works_open=c[7],
        note=('a position names a keyed person when at least one key bears a compatible name before the date test '
              '(states exact/linked/possible/ambiguous, and none when every such key was ruled out by dates, a proven '
              'namesake, or the book-author check); exact = an ORCID printed on the record is on the key'))
    rep['by_state_branch'] = {f'{a}|{b}': n for a, b, n in q("SELECT state, branch, count(*) FROM allp WHERE state NOT IN ('credited') GROUP BY ALL ORDER BY 1, 3 DESC")}
    rep['linked_by_fact'] = dict(Counter(f for (sig,) in q("SELECT signals FROM allp WHERE state = 'linked' AND NOT already_credited")
                                         for f in _facts_of(sig)))
    orc = {k for (k,) in q(f"SELECT key FROM '{G}/person.parquet' WHERE len(list_filter(anchors, x -> x LIKE 'orcid:%')) > 0")}
    lk_rows = q("SELECT key, signals, branch FROM allp WHERE state = 'linked' AND NOT already_credited")
    rep['linked_by_person_orcid'] = dict(with_orcid=sum(1 for k, _, _ in lk_rows if k in orc),
                                         without_orcid=sum(1 for k, _, _ in lk_rows if k not in orc))
    t_only = [k for k, sig, br in lk_rows if _facts_of(sig) == {'topic'}]
    rep['linked_resting_on_topic_alone'] = dict(positions=len(t_only), with_orcid=sum(1 for k in t_only if k in orc),
                                                without_orcid=sum(1 for k in t_only if k not in orc))
    rep['linked_without_fact_by_branch'] = dict(Counter(br for sig, br in q("SELECT signals, branch FROM allp WHERE state = 'linked' AND NOT already_credited")
                                                        if not _facts_of(sig)))
    # ---- gold (masked: the credit, its ORCID and what came from that work hidden) and namesake tests
    def tests(tag=''):
        gold = q(f"SELECT state, key, true, cls, branch, sig, half, how FROM '{S}/gold{tag}.parquet' WHERE dup")
        ns = q(f"SELECT test, false_link, branch, sig, state FROM '{S}/namesake{tag}.parquet'")
        out = dict(gold_rows=len(gold))
        lk = [g for g in gold if g[0] == 'linked']
        right = [g for g in lk if g[3] in ('right', 'dup')]
        out['gold'] = dict(linked=len(lk), right_or_duplicate_key=len(right), wrong=len(lk) - len(right),
                           precision=round(len(right) / len(lk), 4) if lk else None, recall=round(len(right) / len(gold), 4) if gold else None)
        out['gold_by_how_credited'] = {}
        for how in sorted({g[7].split(':')[0] for g in gold}):
            gg = [g for g in gold if g[7].split(':')[0] == how]
            l2 = [g for g in gg if g[0] == 'linked']
            r2 = [g for g in l2 if g[3] in ('right', 'dup')]
            out['gold_by_how_credited'][how] = dict(rows=len(gg), linked=len(l2), right=len(r2), recall=round(len(r2) / len(gg), 4) if gg else None,
                                                    precision=round(len(r2) / len(l2), 4) if l2 else None)
        byf = defaultdict(lambda: [0, 0])
        for g in lk:
            fs = _facts_of(g[5]) or {'(no fact: rarity)'}
            for f in fs:
                byf[f][0] += 1
                byf[f][1] += g[3] in ('right', 'dup')
        out['gold_by_fact'] = {f: dict(linked=a, right=b, precision=round(b / a, 4) if a else None, recall=round(b / len(gold), 4))
                               for f, (a, b) in sorted(byf.items())}
        # links that rest on one fact alone (second-fact branches with that fact only)
        alone = defaultdict(lambda: [0, 0])
        for g in lk:
            fs = _facts_of(g[5])
            if g[4] in ('unique-second-fact', 'several-one-survives') and len(fs) == 1:
                f = next(iter(fs))
                alone[f][0] += 1
                alone[f][1] += g[3] in ('right', 'dup')
        out['gold_links_resting_on_one_fact'] = {f: dict(linked=a, right=b, precision=round(b / a, 4) if a else None) for f, (a, b) in sorted(alone.items())}
        byb = defaultdict(lambda: [0, 0])
        for g in lk:
            byb[g[4]][0] += 1
            byb[g[4]][1] += g[3] in ('right', 'dup')
        out['gold_by_branch'] = {b: dict(linked=x, right=y, precision=round(y / x, 4)) for b, (x, y) in sorted(byb.items())}
        out['gold_not_linked'] = dict(Counter(f'{g[0]}|{g[4]}' for g in gold if g[0] != 'linked').most_common(15))
        out['namesake'] = {t: dict(rows=sum(1 for x in ns if x[0] == t), false_links=sum(1 for x in ns if x[0] == t and x[1]))
                           for t in sorted({x[0] for x in ns})}
        nf = Counter()
        for x in ns:
            if x[1]:
                for f in _facts_of(x[3]) or {'(no fact: rarity)'}:
                    nf[f] += 1
        out['namesake_false_links_by_fact'] = dict(nf)
        out['namesake_false_links_by_branch'] = dict(Counter(x[2] for x in ns if x[1]))
        return out
    rep['tests'] = tests()
    if (S / 'gold-base.parquet').exists():
        rep['tests_without_new_facts'] = tests('-base')
        d = q(f"""SELECT count(*) FROM '{S}/results.parquet' r JOIN '{S}/results-base.parquet' b USING (pid)
                 WHERE r.state = 'linked' AND b.state <> 'linked'""")[0][0]
        d2 = q(f"""SELECT count(*) FROM '{S}/results.parquet' r JOIN '{S}/results-base.parquet' b USING (pid)
                 WHERE r.state <> 'linked' AND b.state = 'linked'""")[0][0]
        d3 = q(f"""SELECT count(*) FROM '{S}/results.parquet' r JOIN '{S}/results-base.parquet' b USING (pid)
                 WHERE r.state = 'linked' AND b.state = 'linked' AND r.key <> b.key""")[0][0]
        rep['ablation'] = dict(linked_only_with_new_facts=d, linked_only_without=d2, linked_to_another_key=d3)
    # ---- OpenAlex author ids that span two keyed people (is the tie fact safe?)
    t = q(f"""WITH t AS (SELECT DISTINCT r.author, r.person FROM read_parquet('{OA_ROWS}', union_by_name=true) r
                JOIN {keylog(G, 'authored')} au ON au."from" = r.person AND au."to" = r.graph_work
                WHERE r.tie LIKE '%work%' AND r.person <> '' AND r.author <> '')
            SELECT count(*), count(*) FILTER (WHERE n >= 2), sum(n) FILTER (WHERE n >= 2) FROM (SELECT author, count(*) n FROM t GROUP BY 1)""")[0]
    rep['openalex_author_ids'] = dict(tied_to_keys_by_keylog_credits=t[0], tied_to_two_or_more_keys=t[1], keys_on_those=t[2],
                                      share=round(t[1] / t[0], 4) if t[0] else None,
                                      note='ids tied to two or more keys are dropped from the oa-author-tie fact (WPPeople.ties)')
    (NO_OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    # ---- 40 linked rows for reading
    db.execute("SELECT setseed(0.1212)")
    rows = q("""SELECT pid, source, work, name, year, journal, kind, title, inst_printed, raw_aff, branch, key, signals FROM allp
                WHERE state = 'linked' AND NOT already_credited ORDER BY random() LIMIT 40""")
    rows += q("""SELECT pid, source, work, name, year, journal, kind, title, inst_printed, raw_aff, branch, key, signals FROM allp
                WHERE state = 'linked' AND NOT already_credited AND signals LIKE '%topic:%' ORDER BY random() LIMIT 40""")
    rows = [r for r in rows if r[10] != 'identifier']
    seen_ = set()
    rows = [r for r in rows if not (r[0] in seen_ or seen_.add(r[0]))]
    out = []
    for pid, src, w, nm, y, j, kind, title, inst, raw, br, k, sig in rows:
        lab, an = db.execute(f"SELECT label, anchors FROM '{G}/person.parquet' WHERE key = ?", [k]).fetchone()
        ws = db.execute(f"""SELECT w.year, w.kind, coalesce(w.journal, ''), left(w.label, 60) FROM {keylog(G, 'authored')} a
                JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE a."from" = ? ORDER BY w.year NULLS LAST LIMIT 8""", [k]).fetchall()
        af = db.execute(f"""SELECT i.label, a.source, a.first_year, a.last_year FROM '{G}/affiliated_with.parquet' a
                JOIN '{G}/institution.parquet' i ON i.key = a."to" WHERE a."from" = ? LIMIT 5""", [k]).fetchall()
        out.append(dict(pid=pid, source=src, work=w, printed=nm, year=y, kind=kind, journal=j, title=(title or '')[:100],
                        printed_institution=inst or '; '.join(raw or [])[:100], branch=br, signals=sig, key=k, key_label=lab,
                        key_ids=' '.join(a for a in an if a.split(':')[0] in ('lcnaf', 'orcid', 'wd', 'aha-phd')),
                        key_works=' | '.join(f'{y_} {kd} {j_[:25]} {t_}' for y_, kd, j_, t_ in ws),
                        key_affiliations=' | '.join(f'{l} ({s_} {a}-{b})' for l, s_, a, b in af)))
    with open(NO_OUT / 'audit-sample.csv', 'w', newline='', encoding='utf-8') as f:
        w_ = csv.DictWriter(f, fieldnames=list(out[0]))
        w_.writeheader()
        w_.writerows(out)
    print(json.dumps({k: rep[k] for k in ('class', 'linked_by_fact', 'linked_without_fact_by_branch', 'openalex_author_ids')}, indent=1))
    print(json.dumps(rep['tests'], indent=1))
    if 'ablation' in rep:
        print(json.dumps(rep['ablation']), json.dumps(rep['tests_without_new_facts']['gold']), json.dumps(rep['tests_without_new_facts']['namesake']))


def nameonly_export(args):
    """data/graph/name-only/credits.csv.gz (exact, linked, possible and ambiguous positions; the build loads exact and
    linked as AUTHORED evidence linked, possible as author_candidates, and counts ambiguous), chapters.csv.gz (the
    sibling chapters the graph did not hold that have an exact or linked position, or (pass seven) a possible position with
    one candidate: they become unkeyed chapter nodes with
    a PART_OF link to their volume), and NO_OUT/links/ (every uncredited position, `none` included, for the record)."""
    db = duck()
    S = SCRATCH
    q = f"""SELECT p.work, p.role, p.pos AS position, p.n_auth AS n_authors, p.name AS printed_name, p.inst_printed AS printed_institution,
               p.source, concat_ws(';', CASE WHEN p.orcid <> '' THEN 'orcid:' || p.orcid END,
               CASE WHEN p.oa_author <> '' THEN 'openalex:' || p.oa_author END) AS source_person_id, p.year,
               r.state, r.key AS person_key, r.candidates, r.n_candidates, r.branch, r.signals
            FROM '{S}/results.parquet' r JOIN '{S}/positions*.parquet' p USING (pid) WHERE NOT r.already_credited"""
    cols = ['work', 'role', 'position', 'n_authors', 'printed_name', 'printed_institution', 'source', 'source_person_id', 'year',
            'state', 'person_key', 'candidates', 'n_candidates', 'branch', 'signals']

    def rows(where):
        cur = db.execute(q + where + ' ORDER BY p.work, p.pos')
        while True:
            b = cur.fetchmany(20000)
            if not b:
                break
            for r in b:
                yield dict(zip(cols, r))
    NO_TABLE.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(NO_TABLE / 'credits.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows(" AND r.state IN ('exact', 'linked', 'possible', 'ambiguous')"):
            w.writerow(r)
            n += 1
    print('credits', n)
    keep = {w for (w,) in db.execute(f"""SELECT DISTINCT p.work FROM '{S}/results.parquet' r JOIN '{S}/positions.parquet' p USING (pid)
            WHERE (r.state IN ('exact', 'linked') OR (r.state = 'possible' AND r.n_candidates = 1)) AND p.source = 'crossref-volume'""").fetchall()}
    # pass seven: also a chapter whose author is one dated, name-compatible key without a confirming fact ('possible', one
    # candidate): the chapter is a node in its volume and the person an unconfirmed candidate on it, never credited
    ccols = ['id', 'doi', 'title', 'year', 'kind', 'volume_work', 'volume_basis', 'publisher', 'n_authors', 'authors']
    m = 0
    with gzip.open(NO_TABLE / 'chapters.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(ccols)
        for r in db.execute(f"SELECT {', '.join(ccols)} FROM '{S}/sibling-chapters.parquet' WHERE id <> '' ORDER BY id").fetchall():
            if r[0] in keep:
                w.writerow(r)
                m += 1
    print('chapters', m)
    parts = write_parts(NO_OUT / 'links', rows(''), cols)
    print('links', [(p.name, p.stat().st_size) for p in parts])


# 2026-11-12 (integration pass five): cited works whose printed authors no linker had read after the name-only pass.
# Class: data/graph/cited-works/authors.csv.gz has no rows for the sources crossref-meta, crossref, journal-meta,
# lc-translations and recent-books; the name-only pass read most of them (their records were found), but not the
# recent books (exported after it) nor the journal-metadata works whose only record is the journal harvest's own
# (build/journal-meta-2026-11-11: OpenAlex and OJS records with full names; Crossref records there print family names
# only and stay a counted residue). LC works (lc-translations, lc-full without authors) are credited by their LC main
# entry's authority instead (scripts/lc_catalogue_credits.py), not here.
RB_CROSSWALK = ROOT / 'data/identifiers/cited-works-recent-books-2026-11-12/crosswalk.csv.gz'
JM_RECORDS = ROOT / 'build/journal-meta-2026-11-11'
RB_NAME = re.compile(r'^(?P<fam>[^,\[]+?)(?:,\s*(?P<giv>[^\[]+?))?\s*(?:\[(?P<orcid>[0-9X-]{19})\])?$')


def recent_book_names(s):
    """'Luby, Brittany; Smith, A. B. [0000-0001-2345-6789]' -> [(name 'Given Family', orcid)]"""
    out = []
    for part in (s or '').split(';'):
        part = part.strip()
        if not part:
            continue
        m = RB_NAME.match(part)
        if not m:
            out.append((part, ''))
            continue
        nm = ' '.join(x for x in ((m.group('giv') or '').strip(), m.group('fam').strip()) if x)
        out.append((nm, m.group('orcid') or ''))
    return out


def nameonly_extra(args):
    """S/positions-extra.parquet: positions (the name-only schema, pid from 20,000,000) of the recent-books crosswalk's
    printed authors and of journal-metadata works whose OpenAlex / OJS record in the journal harvest prints full names,
    for works that have no position in S/positions.parquet and no row in cited-works/authors.csv.gz. Recent books are
    looked up with no subject filter, so their OpenAlex ids (or 'CR:<doi>') are listed in S/oa/doi-lookup-extra.jsonl:
    the guard 'outside-history-rarity-only' applies (a name rare in the History population says little outside it).
    Then: link --nameonly --gold-no-oa --topic-min 20, nameonly-report, nameonly-export (all reading positions*.parquet)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    S, G = SCRATCH, GRAPH
    db = duck()
    stats = Counter()
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    keyof = {}
    for a, k in db.execute(f"""SELECT a, key FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed')
                              WHERE a LIKE 'doi:%' OR a LIKE 'openalex:%' OR a LIKE 'ojs:%'""").fetchall():
        keyof[a.lower() if a.startswith('doi:') else a] = k
    have_pos = {w for (w,) in db.execute(f"SELECT DISTINCT work FROM '{S}/positions.parquet'").fetchall()}
    cwa = {w for (w,) in db.execute(f"""SELECT DISTINCT work FROM read_csv('{ROOT / 'data/graph/cited-works/authors.csv.gz'}',
                                         all_varchar=true)""").fetchall()}
    cw = {r[0]: r for r in db.execute(f"""SELECT id, source, title, year, kind, container, alias_ids FROM
            read_csv('{ROOT / 'data/graph/cited-works/works.csv.gz'}', all_varchar=true)
            WHERE source IN ('recent-books', 'journal-meta')""").fetchall()}
    credits = defaultdict(list)                  # node -> [(key, known)] credits already on it (not name-only)
    for k, w, known in db.execute(f"""SELECT a."from", a."to", {KNOWN_EXACT_SQL} FROM '{G}/authored.parquet' a
            WHERE coalesce(a.source, '') NOT LIKE 'name-only:%' AND a."to" IN (SELECT unnest(?))""",
                                  [sorted({keyof.get(i.lower() if i.startswith('doi:') else i, i) for i in cw})]).fetchall():
        credits[w].append((k, known))
    rows, outside, targets = [], [], []

    def node_of(wid, aliases):
        for x in [wid] + [a for a in (aliases or '').split(';') if a]:
            k = keyof.get(x.lower() if x.startswith('doi:') else x)
            if k:
                return k
        return wid

    def add(src, w, i, n, nm, orcid, meta, oa_work=''):
        title, year, kind, journal = meta
        row = dict(role='author', source=src, work=w, pos=i, n_auth=n, name=nm, year=year, journal=journal or '',
                   kind=kind or '', title=(title or '')[:200], orcid=orcid or '', oa_author='', rors=[], insts=[], raw_aff=[],
                   oa_work=oa_work, inst_printed='', inst_ror='', inst_ror_name='', sig_conf=0.0, credited='', credited_how='')
        best = None
        for k, known in credits.get(w, ()):
            lev = agree_level(nm, label.get(k, ''))
            if lev and known and (best is None or ('full', 'variant', 'initial').index(lev) < ('full', 'variant', 'initial').index(best[1])):
                best = (k, lev)
            elif lev and not known:
                stats['dropped_already_linked_by_rule'] += 1
                return
        if best:
            row.update(credited=best[0], credited_how='name:' + best[1])
        rows.append(row)
    # recent books
    with gzip.open(RB_CROSSWALK, 'rt', newline='', encoding='utf-8') as fh:
        rb_rows = list(csv.DictReader(fh))
    for r in rb_rows:
        wid = r['id'] if r['id'] in cw else next((a for a in (r['alias_ids'] or '').split(';') if a in cw), None)
        if not wid:
            stats['recent_books_not_exported'] += 1
            continue
        w = node_of(wid, cw[wid][6])
        if w in have_pos or wid in cwa or w in cwa:
            stats['recent_books_already_read'] += 1
            continue
        names = recent_book_names(r['authors'])
        stats['recent_books_editor_names_not_read'] += len(recent_book_names(r['editors']))
        if not names:
            stats['recent_books_no_printed_author'] += 1
            continue
        have_pos.add(w)
        yr = int(r['year']) if (r['year'] or '').isdigit() else None
        meta = (r['title'], yr, 'book', '')
        # the outside list is read by its first 30 characters: a Crossref-only record gets a short stand-in id
        oa_work = r['openalex_id'] or ('CR' + L.hashlib.md5(r['doi'].lower().encode()).hexdigest()[:16] if r['doi'] else '')
        if oa_work:
            outside.append(oa_work)
        targets.append((w, 'unkeyed' if w == wid else 'keyed', 'book', yr, None, r['title'], [wid]))
        stats['recent_books_works'] += 1
        for i, (nm, orc) in enumerate(names):
            add('recent-books', w, i, len(names), nm, orc, meta, oa_work)
    # journal-metadata works whose only record is the journal harvest's own
    want = {}
    for wid, (_, src, title, year, kind, container, aliases) in cw.items():
        if src != 'journal-meta':
            continue
        w = node_of(wid, aliases)
        if w in have_pos or wid in cwa or w in cwa:
            stats['journal_meta_already_read'] += 1
            continue
        want[wid] = (w, (title, int(year) if (year or '').isdigit() else None, kind, container))
    seen = set()
    jm_files = [JM_FULLER / 'fuller.jsonl'] if (JM_FULLER / 'fuller.jsonl').exists() else []
    for sub in ('openalex', 'oai', 'crossref'):
        jm_files += sorted((JM_RECORDS / sub).glob('*'))
    for fn in jm_files:
            op = gzip.open if fn.name.endswith('.gz') else open
            with op(fn, 'rt', encoding='utf-8') as f:
                for line in f:
                    d = json.loads(line)
                    sid = d.get('sid')
                    ids = [sid] + (['doi:' + d['doi'].lower()] if d.get('doi') else [])
                    wid = next((x for x in ids if x in want), None)
                    if not wid or wid in seen:
                        continue
                    names = [x for x in d.get('authors') or [] if x and x.strip(', ')]
                    if not names:
                        continue
                    if d.get('basis'):
                        stats['journal_meta_fuller_record|' + d['basis'].split(':')[0]] += 1
                    if not d.get('authors_are_full_names'):
                        stats['journal_meta_family_name_only'] += 1      # Crossref records here print family names only
                        continue
                    seen.add(wid)
                    w, meta = want[wid]
                    targets.append((w, 'unkeyed' if w == wid else 'keyed', meta[2], meta[1], meta[3], meta[0], [wid]))
                    stats['journal_meta_works'] += 1
                    for i, nm in enumerate(names):
                        add('journal-meta-doi' if d.get('basis') else 'journal-meta',
                            w, i, len(names), nm, '', meta)
    stats['journal_meta_no_full_name_record'] = len(set(want) - seen)
    for i, r in enumerate(rows):
        r['pid'] = 20_000_000 + i
    schema = pq.read_schema(S / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), S / 'positions-extra.parquet')
    (S / 'oa').mkdir(exist_ok=True)
    with open(S / 'oa' / 'doi-lookup-extra.jsonl', 'w') as f:
        for o in outside:
            f.write(json.dumps({'work': o}) + '\n')
    stats['positions'] = len(rows)
    stats['positions_credited_gold'] = sum(1 for r in rows if r['credited'])
    print(json.dumps(dict(stats), indent=1), flush=True)
    (S / 'positions-extra-stats.json').write_text(json.dumps(dict(stats), indent=1) + '\n')


JM_FULLER = ROOT / 'build/journal-meta-fuller-2026-11-12'     # pass seven: fuller names for family-name-only records


def family_only_works(db, S):
    """journal-metadata cited works whose only record prints family names (the journal harvest's Crossref records) and that
    no other record we hold gives a position for (S/positions*.parquet: the OpenAlex harvest, DOI lookup and author-works
    fetch, the Crossref metadata / reference / container / book harvests and JSTOR metadata, read by nameonly-extract)
    -> {doi: (node, [family names])}"""
    keyof = {}
    for a, k in db.execute(f"""SELECT a, key FROM (SELECT key, unnest(anchors) a FROM '{GRAPH}/work.parquet' WHERE resolution <> 'unkeyed')
                              WHERE a LIKE 'doi:%'""").fetchall():
        keyof[a.lower()] = k
    have_pos = {w for (w,) in db.execute(f"SELECT DISTINCT work FROM '{S}/positions*.parquet'").fetchall()}
    jm = {}
    for wid, aliases in db.execute(f"""SELECT id, alias_ids FROM read_csv('{ROOT / 'data/graph/cited-works/works.csv.gz'}', all_varchar=true)
                                       WHERE source = 'journal-meta'""").fetchall():
        for x in [wid] + [a for a in (aliases or '').split(';') if a]:
            if x.startswith('doi:'):
                jm[x.lower()] = keyof.get(x.lower(), wid)
    full, fam = set(), {}
    for sub in ('openalex', 'oai', 'crossref'):
        for fn in sorted((JM_RECORDS / sub).glob('*')):
            op = gzip.open if fn.name.endswith('.gz') else open
            with op(fn, 'rt', encoding='utf-8') as f:
                for line in f:
                    d = json.loads(line)
                    doi = 'doi:' + d['doi'].lower() if d.get('doi') else (d.get('sid') or '').lower()
                    if doi not in jm:
                        continue
                    names = [x for x in d.get('authors') or [] if x and x.strip(', ')]
                    if not names:
                        continue
                    if d.get('authors_are_full_names'):
                        full.add(doi)
                    else:
                        fam.setdefault(doi, names)
    return {d: (jm[d], names) for d, names in fam.items() if d not in full and jm[d] not in have_pos}


OA_DOI_RE = re.compile(r'"doi":\s*"https://doi\.org/([^"]+)"')


def _doi_scan_one(args):
    """one OpenAlex or Crossref file -> [(doi, source, [names])] for the wanted DOIs (names as printed: OpenAlex raw author
    names, else display names; Crossref given + family)"""
    path, want_file, kind = args
    want = set(open(want_file).read().split())
    out = []
    op = gzip.open if str(path).endswith('.gz') else open
    rx = OA_DOI_RE if kind == 'openalex' else CR_DOI_ANY
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            m = rx.search(line)
            if not m or ('doi:' + m.group(1).lower()) not in want:
                continue
            d = json.loads(line)
            if kind == 'openalex':
                names = [a.get('raw_author_name') or (a.get('author') or {}).get('display_name') or '' for a in d.get('authorships') or []]
            else:
                names = [a['name'] for a in cr_authors(d)]
            out.append(('doi:' + m.group(1).lower(), f'{kind}:{Path(path).parent.name}', names))
    return out


def nameonly_fuller(args):
    """Family-name-only journal records (pass seven; ARCHITECTURE.md section 8, class 33): for each, a Crossref lookup by
    DOI (PoliteCrossref; at most --max requests; resumable) -> JM_FULLER/crossref-doi.jsonl. A fetched record is used only
    when it prints given names and its family names are the family-only record's, in order (fuller.jsonl, read by
    nameonly-extra as a full-name record). Report JM_FULLER/report.json."""
    import urllib.parse
    S = SCRATCH
    db = duck()
    F = family_only_works(db, S)
    JM_FULLER.mkdir(parents=True, exist_ok=True)
    # records we hold first: the OpenAlex harvest and DOI lookup, the Crossref metadata and reference harvests
    local = {}
    if not args.skip_local:
        want = JM_FULLER / 'want.txt'
        want.write_text('\n'.join(sorted(F)) + '\n')
        jobs = ([(p, str(want), 'openalex') for p in sorted(HARVEST.glob('*.jsonl.gz')) + sorted(DOILOOK.glob('part-*.jsonl.gz'))]
                + [(p, str(want), 'crossref') for p in sorted(CR_META_WORKS.glob('*.jsonl.gz'))])
        with mp.Pool(args.workers) as pool:
            for res in pool.imap_unordered(_doi_scan_one, jobs):
                for doi, src, names in res:
                    local.setdefault(doi, []).append((src, names))
        with open(JM_FULLER / 'local-records.jsonl', 'w', encoding='utf-8') as o:
            for doi, recs in sorted(local.items()):
                o.write(json.dumps(dict(doi=doi, records=recs), ensure_ascii=False) + '\n')
        print(len(jobs), 'files;', len(local), 'family-name-only works with another record held', flush=True)
    raw = JM_FULLER / 'crossref-doi.jsonl'
    done = {}
    if raw.exists():
        for line in open(raw, encoding='utf-8'):
            r = json.loads(line)
            if not str(r.get('status', '')).startswith('error'):
                done[r['doi']] = r
    todo = sorted(d for d in F if d not in done)[:args.max] if args.max else []
    print(len(F), 'family-name-only works;', len(done), 'fetched;', len(todo), 'to fetch', flush=True)
    cr = PoliteCrossref(JM_FULLER / 'refusals.jsonl', gap=max(1.0, args.gap))
    refused = None
    with open(raw, 'a', encoding='utf-8') as o:
        for d in todo:
            try:
                status, msg = cr.get('https://api.crossref.org/works/' + urllib.parse.quote(d[4:], safe='/()._-;:'))
            except CrossrefRefused as e:
                refused = str(e)
                print('refused, stopping:', e, flush=True)
                break
            rec = dict(doi=d, status=status, authors=cr_authors(msg) if msg else [])
            o.write(json.dumps(rec, ensure_ascii=False) + '\n')
            o.flush()
            done[d] = rec
            if cr.calls % 100 == 0:
                print(cr.calls, 'calls', flush=True)
    st = Counter()
    with open(JM_FULLER / 'fuller.jsonl', 'w', encoding='utf-8') as o:
        for d, (node, fams) in sorted(F.items()):
            got = None
            for src, names in local.get(d, ()):
                v = fuller_names(fams, [dict(name=n) for n in names])
                st[f'local|{v[0]}'] += 1
                if v[0] == 'fuller' and not got:
                    got = (v[1], f'local:{src}')
            if got:
                st['fuller|local'] += 1
                o.write(json.dumps(dict(sid=d, doi=d[4:], authors=got[0], authors_are_full_names=True, basis=got[1]),
                                   ensure_ascii=False) + '\n')
                continue
            r = done.get(d)
            if not r:
                st['not_fetched'] += 1
                continue
            if r['status'] != 'ok':
                st[f"status_{r['status'][:20]}"] += 1
                continue
            v = fuller_names(fams, r['authors'])
            st[v[0]] += 1
            if v[0] == 'fuller':
                st['fuller|crossref-doi-lookup'] += 1
                o.write(json.dumps(dict(sid=d, doi=d[4:], authors=v[1], authors_are_full_names=True,
                                        basis='crossref-doi-lookup'), ensure_ascii=False) + '\n')
    rep = dict(family_only_works=len(F), with_another_record_held=len(local), requests=cr.calls, refused=refused,
               outcome=dict(sorted(st.items())))
    (JM_FULLER / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


def _fam_fold(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]', '', s)


def fuller_names(families, authors):
    """(outcome, names): the record's names replace the family-only list when every author has a given name of two or more
    letters or an initial, and the family names agree position by position (folded); else ('still-family-only' |
    'families-differ' | 'no-authors', [])"""
    if not authors:
        return 'no-authors', []
    fam_rec = [_fam_fold(a['name'].split()[-1] if a['name'] else '') for a in authors]
    fam_old = [_fam_fold(f.split(',')[0].split()[-1] if f.split() else '') for f in families]
    if len(fam_rec) != len(fam_old) or any(a != b and not (a.endswith(b) or b.endswith(a)) for a, b in zip(fam_rec, fam_old)):
        return 'families-differ', []
    if any(len(a['name'].split()) < 2 for a in authors):
        return 'still-family-only', []
    return 'fuller', [a['name'] for a in authors]


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('extract')
    a.add_argument('--workers', type=int, default=3)
    a.add_argument('--skip-oa', action='store_true')
    sub.add_parser('positions')
    a = sub.add_parser('link')
    a.add_argument('--limit', type=int, default=0, help='a sample: about 1 work in 2*LIMIT')
    a.add_argument('--gold', type=int, default=20000, help='gold rows per role')
    a.add_argument('--no-dup', action='store_true')
    a.add_argument('--nameonly', action='store_true', help='the name-only class (WP_SCRATCH must point at its scratch)')
    a.add_argument('--facts', default='', help='with --nameonly: the added facts allowed (default FACTS_NAMEONLY)')
    a.add_argument('--gold-no-oa', action='store_true', help='gold and masked-author tests without the OpenAlex author id')
    a.add_argument('--new-facts', action='store_true', help='FACTS_NAMEONLY on the 11-11 positions (run volume-people first)')
    a.add_argument('--no-one-fact', action='store_true', help='without the several-dated-one-fact branch')
    a.add_argument('--topic-min', type=float, default=0.0, help='topic fact at or above this score (0: off)')
    a.add_argument('--adopt', default='', help='pass-eight single-candidate rules that link (comma list; default none: '
                   'their inputs are written to the signals only)')
    a.add_argument('--topicv-min', type=float, default=1e9, help='rule unique-topic-volume: volume-context topic score')
    a.add_argument('--scholar-max-bearers', type=int, default=0, help='rule single-scholar-history-venue: at most this '
                   'many bearers of the name (date-possible LC namesakes + 1, or OpenAlex History ids)')
    a.add_argument('--out-tag', default='', help='suffix of the results / gold / namesake files (a variant run)')
    sub.add_parser('mints')
    sub.add_parser('panel')
    sub.add_parser('audit')
    sub.add_parser('export')
    sub.add_parser('defects')
    sub.add_parser('recheck-cited')
    sub.add_parser('title-filter')
    a = sub.add_parser('contributors')
    a.add_argument('--n', type=int, default=5)
    a = sub.add_parser('titlematch')
    a.add_argument('--workers', type=int, default=3)
    a = sub.add_parser('crossref')
    a.add_argument('--workers', type=int, default=3)
    a = sub.add_parser('report')
    a.add_argument('--limit', type=int, default=0)
    a = sub.add_parser('nameonly-extract')
    a.add_argument('--workers', type=int, default=3)
    a.add_argument('--retarget', action='store_true')
    a.add_argument('--skip-oa', action='store_true')
    a.add_argument('--skip-cr', action='store_true')
    a.add_argument('--skip-refs', action='store_true')
    a.add_argument('--skip-jstor', action='store_true')
    a = sub.add_parser('nameonly-siblings')
    a.add_argument('--max', type=int, default=3000)
    a.add_argument('--gap', type=float, default=1.0, help='seconds between request starts (at least 1)')
    a.add_argument('--tier', choices=('keylog', 'linked'), default='keylog')
    a.add_argument('--first', default='', help='volume keys fetched before the rest (a probe)')
    sub.add_parser('nameonly-positions')
    sub.add_parser('nameonly-report')
    sub.add_parser('volume-people')
    sub.add_parser('nameonly-export')
    sub.add_parser('nameonly-extra')
    a = sub.add_parser('nameonly-fuller')
    a.add_argument('--max', type=int, default=2000, help='Crossref lookups by DOI (0: none)')
    a.add_argument('--workers', type=int, default=3)
    a.add_argument('--skip-local', action='store_true')
    a.add_argument('--gap', type=float, default=1.0)
    args = ap.parse_args()
    {'extract': extract, 'positions': positions, 'link': link, 'report': report, 'mints': mints, 'panel': panel, 'audit': audit, 'export': export, 'crossref': crossref, 'titlematch': titlematch, 'defects': defects,
     'recheck-cited': recheck_cited, 'contributors': contributors,
     'title-filter': title_filter, 'nameonly-extract': nameonly_extract, 'nameonly-siblings': nameonly_siblings,
     'nameonly-positions': nameonly_positions, 'nameonly-report': nameonly_report,
     'nameonly-export': nameonly_export, 'volume-people': volume_people_cmd, 'nameonly-extra': nameonly_extra, 'nameonly-fuller': nameonly_fuller}[args.cmd](args)


if __name__ == '__main__':
    main()
