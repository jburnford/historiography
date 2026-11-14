"""Co-authors printed on a keyed work who are missing from the graph (2026-11-14; ARCHITECTURE.md section 8, class 43).

Probes (the owner's own papers; never hand-patched):
- w-549919 'Thinking through forests' (Journal of Historical Geography 2026): Crossref prints Jim Clifford and Iva Lučić;
  only Clifford (p-24137) was credited. Lučić stood in the 11-11 co-author mints with two works but the narrowing vetoed
  her mention on w-549919 as an 'OpenAlex error for Iva Peša' (KNOWN_ERRORS in narrow_coauthor_mints.py, a mistake,
  removed 2026-11-14); left with one work and an ORCID only OpenAlex inferred, she was dropped.
- w-703278 'Logging and Settlement beyond the Rapids' (Canadian Historical Review 2025): Crossref and OpenAlex print Jim
  Clifford and Sam Huckerby. The author list WAS loaded (OpenAlex position, state none: no key bears the name); the 11-11
  mints held him (new:p58777) and the narrowing dropped every single-work, name-only person; unkeyed-people.csv.gz lists
  only names with 2+ works or a JSTOR-printed institution, so he is in no file.

The class, graph-wide (measure): key-log works with a DOI whose printed author list (OpenAlex positions as loaded by
link_work_people.py, else the Crossref metadata harvest on E:) has more people than the graph credits + candidates:
  (a) no author list loaded for the work (split: Crossref record held on E: but not loaded / not held anywhere);
  (b) a printed co-author with no key, not minted (reason: veto, narrowing rule, single work, no identifier, ...);
  (c) a printed co-author whose position the linker tied to a key (exact / linked) or to candidates (possible), but no
      AUTHORED or candidate edge for that key on the work in the build.

Mint rule (propose; owner framing 2026-11-14: a person printed as co-author of a keyed person on a work in a history
venue is someone the graph should hold; identity is by works): a printed full name (a written-out given name, never
initials only; not an organisation) with no compatible key (linker state none), on a work with a keyed author (key-log
credit or an ORCID exact), and one of
  O  an ORCID printed on the record (OpenAlex raw_orcid or the Crossref author ORCID);
  G  two or more works with the same full name joined by a shared fact: a shared keyed co-author, the same venue, the
     same OpenAlex author id or the same printed institution ROR;
  H  a single work in a history venue (journal catalogue title or alias) with a keyed co-author.
One key per person: mentions join on a printed ORCID, else only by rule G; a one-work mint stays a one-work key (anchor
`coauthor-mention:<work>:<pos>`) until another fact ties more works. An ORCID that OpenAlex inferred (not printed) is a
member `orcid-inferred:`, not an anchor, unless the person passes G (two works) and the name agrees in full on every
mention (then it is the anchor; a one-work mint keeps it as a member, since an ORCID anchor pulls in every work of the
record). Held: a live key with the same full name (a possible name-form link, not a mint), an ORCID already on a key, a
work whose key-log author matches no printed name, works with more than 25 authors and no ORCID, organisation names,
initial-only names. A key whose name agrees only at variant level (Sam / Samuel) is listed with the mint, never merged.

    python3 scripts/coauthor_gaps.py crossref-index     # E: crossref-meta -> build/coauthor-gaps-2026-11-14/crossref-authors.parquet
    python3 scripts/coauthor_gaps.py measure            # class counts -> OUT/report.json (+ missing-doi list)
    python3 scripts/coauthor_gaps.py sample-fetch [--n 300]   # Crossref /works/{doi} for a random sample of cause (a)
    python3 scripts/coauthor_gaps.py fetch              # the resumable bulk fetch (NOT run 2026-11-14)
    python3 scripts/coauthor_gaps.py propose            # proposal.json, held.csv.gz, sample, dry run
"""
import argparse
import csv
import os
import gzip
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

G = ROOT / 'build/graph'
WP = ROOT / 'build/scratch-relink-2026-11-13/workpeople'      # positions + results of the last full link (2026-11-14 00:09)
SCR = ROOT / 'build/coauthor-gaps-2026-11-14'
OUT = ROOT / 'data/identifiers/coauthor-mints-2026-11-14'
CRMETA = Path('/mnt/e/crossref-meta-2026-11-11/works')
UA = 'historiography-kg/1.0 (research harvest; generic client)'
CAP = 25


def duck():
    import duckdb
    (SCR / 'tmp').mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCR}/tmp'; SET enable_progress_bar=false")
    return db


def cr_authors(rec):
    out = []
    for a in rec.get('author') or []:
        nm = ' '.join(x for x in (a.get('given'), a.get('family')) if x) or a.get('name') or ''
        out.append(dict(name=nm.strip(), given=a.get('given') or '', family=a.get('family') or a.get('name') or '',
                        orcid=(a.get('ORCID') or '').rsplit('/', 1)[-1],
                        aff='; '.join(x.get('name', '') for x in a.get('affiliation') or [] if x.get('name'))[:200]))
    return out


def crossref_index(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    SCR.mkdir(parents=True, exist_ok=True)
    rows, writer, total = [], None, 0
    schema = pa.schema([('doi', pa.string()), ('n_auth', pa.int32()), ('journal', pa.string()), ('authors', pa.string()),
                        ('page', pa.string())])
    files = sorted(CRMETA.glob('*.jsonl.gz'))
    for i, p in enumerate(files):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                doi = (d.get('DOI') or '').lower()
                if not doi:
                    continue
                au = cr_authors(d)
                rows.append(dict(doi=doi, n_auth=len(au), journal=(d.get('container-title') or [''])[0][:200],
                                 authors=json.dumps(au, ensure_ascii=False), page=(d.get('page') or '')[:40]))
        if len(rows) >= 200_000 or i == len(files) - 1:
            writer = writer or pq.ParquetWriter(SCR / 'crossref-authors.parquet', schema)
            writer.write_table(pa.Table.from_pylist(rows, schema=schema))
            total += len(rows)
            rows = []
            print(i, len(files), total, flush=True)
    writer.close()
    print('records', total)


# ---------------------------------------------------------------- shared loaders

def load_keyed_doi_works(db):
    """key-log works (resolution not unkeyed) with a doi: anchor -> (work, doi, kind, year, journal)"""
    return db.execute(f"""SELECT key, lower(substr(list_filter(anchors, a -> a LIKE 'doi:%')[1], 5)) doi, kind, year, journal
            FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed' AND len(list_filter(anchors, a -> a LIKE 'doi:%')) > 0""").fetchall()


SECTION = re.compile(r'(?i)\s*(?:(?:reviews?|short notices|book notes|notes and comments|books received|comptes?[- ]rendus|'
                     r'recensioni|besprechungen|rezensionen|rese[ñn]as|notices|review section|reviews? of books)\s*(?:[:.]|$)|'
                     r'books?\s*:|review of\b)')


def I_fold(t):
    import unicodedata
    return unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()


def npages(pg):
    """pages of a Crossref 'page' value ('354', '405-432', 'A1-A6'), or None"""
    m = re.fullmatch(r'\s*[A-Za-z]*(\d+)\s*(?:[-–]\s*[A-Za-z]*(\d+))?\s*', pg or '')
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    return b - a + 1 if b >= a else None


def history_journals():
    from key_review_reviewers import journal_key
    out = set()
    with open(ROOT / 'data/journal-catalogue/catalogue.csv', newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            for t in [r['title']] + (r['aliases'] or '').split(' | '):
                jk = journal_key(t) if t else ''
                if jk:
                    out.add(jk)
    return out, journal_key


def graph_people_on(db, table='wk'):
    """work -> set of person keys credited (any evidence, authored or edited) or candidate on it"""
    on = defaultdict(set)
    for k, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE "to" IN (SELECT w FROM {table})
            UNION SELECT "from", "to" FROM '{G}/linked_authored.parquet' WHERE "to" IN (SELECT w FROM {table})
            UNION SELECT "from", "to" FROM '{G}/edited.parquet' WHERE "to" IN (SELECT w FROM {table})
            UNION SELECT "from", "to" FROM '{G}/linked_edited.parquet' WHERE "to" IN (SELECT w FROM {table})
            UNION SELECT "from", "to" FROM '{G}/author_candidates.parquet' WHERE "to" IN (SELECT w FROM {table})
            UNION SELECT "from", "to" FROM '{G}/possible_author.parquet' WHERE "to" IN (SELECT w FROM {table})""").fetchall():
        on[w].add(k)
    return on


def keylog_authored(db, table='wk'):
    on = defaultdict(set)
    for k, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
            AND "to" IN (SELECT w FROM {table})""").fetchall():
        on[w].add(k)
    return on


def load_positions(db, table='wk'):
    """work -> [position dicts] (author roles; OpenAlex first, then Crossref, then OpenAlex title matches)"""
    rows = db.execute(f"""SELECT p.pid, p.role, p.source, p.work, p.pos, p.n_auth, p.name, p.year, p.journal, p.orcid,
            p.oa_author, p.rors, p.raw_aff, p.oa_work, p.credited, coalesce(r.state, CASE WHEN p.credited <> '' THEN 'credited' END) state,
            r.key, r.branch, r.candidates
            FROM read_parquet('{WP}/positions*.parquet', union_by_name=true) p LEFT JOIN '{WP}/results.parquet' r USING (pid)
            WHERE p.role IN ('author', 'jstor-author') AND p.work IN (SELECT w FROM {table})""").fetchall()
    cols = [d[0] for d in db.description]
    by = defaultdict(list)
    for r in rows:
        d = dict(zip(cols, r))
        by[d['work']].append(d)
    # one source per work: the one with most positions (OpenAlex usually), so two sources never double a list
    out = {}
    for w, ps in by.items():
        src = Counter(p['source'] for p in ps)
        best = max(src, key=lambda s: (src[s], s == 'openalex'))
        out[w] = sorted([p for p in ps if p['source'] == best], key=lambda p: p['pos'])
    return out


# ---------------------------------------------------------------- measure

def measure(args):
    db = duck()
    works = load_keyed_doi_works(db)
    print('keyed works with a DOI', len(works), flush=True)
    db.execute('CREATE OR REPLACE TABLE wk AS SELECT unnest(?) w', [[w[0] for w in works]])
    on = graph_people_on(db)
    pos = load_positions(db)
    cr = {}
    if (SCR / 'crossref-authors.parquet').exists():
        db.execute('CREATE OR REPLACE TABLE dk AS SELECT unnest(?) doi', [[w[1] for w in works]])
        for doi, n, au in db.execute(f"""SELECT doi, n_auth, authors FROM '{SCR}/crossref-authors.parquet'
                WHERE doi IN (SELECT doi FROM dk)""").fetchall():
            cr[doi] = (n, au)
    rev_only = {w for (w,) in db.execute(f"""SELECT DISTINCT work FROM read_parquet('{WP}/positions*.parquet', union_by_name=true)
            WHERE role = 'reviewer' AND work IN (SELECT w FROM wk)""").fetchall()}
    reviewish = {w for (w,) in db.execute(f"""SELECT key FROM '{G}/work.parquet' WHERE resolution <> 'unkeyed' AND (kind = 'review'
            OR kind_proposed = 'review' OR regexp_matches(coalesce(label, ''), '(?i)^\\s*(review of|book review|rezension|compte[- ]rendu)'))""").fetchall()}
    rep = Counter()
    missing = []
    reasons_b = Counter()
    gap_works = Counter()
    narrowed = narrowed_index()
    for w, doi, kind, year, journal in works:
        rep['works'] += 1
        ps = pos.get(w)
        n_graph = len(on.get(w, ()))
        if not ps:
            if w in rev_only:
                rep['no_author_list|review-with-reviewer-positions (not a gap)'] += 1
                continue
            if w in reviewish:
                rep['no_author_list|review-record-no-reviewer-printed (not counted)'] += 1
                continue
            if doi in cr:
                n_cr = cr[doi][0]
                rep['a_no_positions|crossref-held-on-E'] += 1
                if n_cr > max(1, n_graph):
                    rep['a_no_positions|crossref-held-on-E|more-printed-than-graph'] += 1
                    gap_works['a-held'] += 1
            else:
                rep['a_no_positions|not-held'] += 1
                missing.append((w, doi, kind, year))
            continue
        n_pr = max(p['n_auth'] or 0 for p in ps)
        rep['with_positions'] += 1
        if n_pr <= n_graph:
            continue
        rep['works_more_printed_than_graph'] += 1
        cause = set()
        for p in ps:
            st = p['state'] or 'none'
            if st == 'credited':
                continue
            if st in ('exact', 'linked') and p['key']:
                ks = set(p['key'].split(';'))
                if not ks & on.get(w, set()):
                    cause.add('c')
                    rep['c_positions_tied_to_key_no_edge'] += 1
                continue
            if st in ('possible', 'ambiguous'):
                cs = set((p['candidates'] or '').split('|')) - {''}
                if cs and not cs & on.get(w, set()):
                    cause.add('c')
                    rep['c_positions_candidates_no_edge'] += 1
                continue
            # state none: printed, no key
            cause.add('b')
            why = narrowed.get((w, p['pos']), 'not-in-11-11-mints')
            reasons_b[why] += 1
        for c in cause:
            gap_works[c] += 1
    rep = dict(rep)
    rep['works_by_cause'] = dict(gap_works)
    rep['b_positions_by_reason'] = dict(reasons_b.most_common())
    SCR.mkdir(parents=True, exist_ok=True)
    with gzip.open(SCR / 'missing-doi.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w_ = csv.writer(f)
        w_.writerow(['work', 'doi', 'kind', 'year'])
        w_.writerows(missing)
    rep['a_missing_by_kind'] = dict(Counter(m[2] for m in missing))
    rep['a_missing_by_prefix_top'] = dict(Counter(m[1].split('/')[0] for m in missing).most_common(15))
    OUT.mkdir(parents=True, exist_ok=True)
    old = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    old['measure'] = rep
    (OUT / 'report.json').write_text(json.dumps(old, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1))


def narrowed_index():
    """(work, pos) -> what became of the mention in the 11-11 mints and their narrowing"""
    base = ROOT / 'data/identifiers/work-people-2026-11-11'
    out = {}
    with gzip.open(base / 'coauthor-mints/proposal.json.gz', 'rt', encoding='utf-8') as f:
        p1 = json.load(f)
    ph_of = {}
    for o in p1['ops']:
        if o['event'] == 'mint' and o['type'] == 'person':
            for a in o['anchors']:
                if a.startswith('coauthor-mention:'):
                    _, w, p = a.split(':')
                    out[(w, int(p))] = 'minted-11-11-then-dropped-by-narrowing:single-work-or-name-only'
                    ph_of[(w, int(p))] = o['key']
    with gzip.open(base / 'coauthor-mints/held.json.gz', 'rt', encoding='utf-8') as f:
        h1 = json.load(f)
    for h in h1['held']:
        if 'work' in h and 'pos' in h:
            out[(h['work'], int(h['pos']))] = 'held-11-11:' + h['reason'][:60]
    for m in h1.get('capped', []):
        out[(m['work'], int(m['pos']))] = 'held-11-11:more-than-25-authors-no-orcid'
    with gzip.open(base / 'coauthor-mints-narrowed/held.json.gz', 'rt', encoding='utf-8') as f:
        h2 = json.load(f)
    held_ph = {h['person']: h['reason'] for h in h2}
    for m, ph in ph_of.items():
        if ph in held_ph:
            out[m] = 'narrowed-held:' + held_ph[ph][:60]
    with gzip.open(base / 'coauthor-mints-narrowed/proposal.json.gz', 'rt', encoding='utf-8') as f:
        p2 = json.load(f)
    for o in p2['ops']:
        if o['event'] == 'mint' and o['type'] == 'person':
            for a in o['anchors']:
                if a.startswith('coauthor-mention:'):
                    _, w, p = a.split(':')
                    out[(w, int(p))] = 'narrowed-proposal-not-applied'
    return out


# ---------------------------------------------------------------- Crossref fetch (sample / resumable bulk)

def _get(url, tries=5):
    back = 2.0
    for _ in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, None
            if e.code in (429, 500, 502, 503, 504):
                ra = e.headers.get('Retry-After')
                time.sleep(float(ra) if ra and ra.isdigit() else back)
                back *= 2
                if e.code == 429 and back > 60:
                    return 429, None
                continue
            return e.code, None
        except Exception:
            time.sleep(back)
            back *= 2
    return 0, None


def fetch_dois(dois, out_path, delay=0.5, stop_on_429=True):
    """one client, one request at a time; resumable: DOIs already in out_path are skipped"""
    done = set()
    if out_path.exists():
        with open(out_path, encoding='utf-8') as f:
            done = {json.loads(l)['doi'] for l in f}
    n = Counter()
    with open(out_path, 'a', encoding='utf-8') as o:
        for doi in dois:
            if doi in done:
                continue
            st, d = _get('https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='/:;()'))
            n[st] += 1
            if st == 429 and stop_on_429:
                print('throttled: stopping', flush=True)
                break
            msg = (d or {}).get('message') or {}
            o.write(json.dumps(dict(doi=doi, status=st, type=msg.get('type'), authors=cr_authors(msg),
                                    journal=(msg.get('container-title') or [''])[0]), ensure_ascii=False) + '\n')
            o.flush()
            time.sleep(delay)
    return n


def sample_fetch(args):
    with gzip.open(SCR / 'missing-doi.csv.gz', 'rt', encoding='utf-8') as f:     # cause (a): no author list, not a review
        rows = list(csv.DictReader(f))
    rnd = random.Random(20261114)
    smp = rnd.sample(rows, min(args.n, len(rows)))
    t0 = time.time()
    n = fetch_dois([r['doi'] for r in smp], SCR / 'sample-fetch.jsonl')
    print('statuses', dict(n), 'seconds', round(time.time() - t0))


def fetch(args):
    """the bulk fetch of cause (a), resumable (one client, 0.5 s between requests, stops on 429). NOT run 2026-11-14."""
    with gzip.open(SCR / 'missing-doi.csv.gz', 'rt', encoding='utf-8') as f:
        dois = [r['doi'] for r in csv.DictReader(f)]
    print(dict(fetch_dois(dois, SCR / 'bulk-fetch.jsonl')))


# ---------------------------------------------------------------- propose

OA_SRC = ROOT / 'build/scratch-2026-11-13/workpeople/oa'        # which E: file holds each OpenAlex record (extract output)


def raw_orcids(oa_works):
    """(oa_work, pos) -> (raw_orcid printed in the record, OpenAlex's author.orcid) for the given OpenAlex works (E:)"""
    from narrow_coauthor_mints import _scan_one, source_file
    import multiprocessing as mp
    cache = SCR / 'raw-orcids.jsonl'
    out = {}
    if cache.exists():
        for line in open(cache, encoding='utf-8'):
            r = json.loads(line)
            out[(r['oa_work'], r['pos'])] = (r['raw_orcid'], r['orcid'])
        have = {w for w, _ in out}
        if oa_works <= have | set(json.loads((SCR / 'raw-orcids-asked.json').read_text())):
            return out
    by_file = defaultdict(list)
    for p in sorted(OA_SRC.glob('*.jsonl')):
        with open(p, encoding='utf-8') as f:
            for line in f:
                w = line[10:40].split('"')[0]
                if w in oa_works:
                    by_file[source_file(p.stem)].append(w)
    print('raw ORCID scan:', len(oa_works), 'records in', len(by_file), 'files', flush=True)
    with open(cache, 'w', encoding='utf-8') as o, mp.get_context('fork').Pool(3) as pool:
        for path, rows in pool.imap_unordered(_scan_one, [(p, ws) for p, ws in by_file.items()]):
            for r in rows:
                o.write(json.dumps(r, ensure_ascii=False) + '\n')
                out[(r['oa_work'], r['pos'])] = (r['raw_orcid'], r['orcid'])
    (SCR / 'raw-orcids-asked.json').write_text(json.dumps(sorted(oa_works)))
    return out


def propose(args):
    import identifiers as I
    from link_cited_work_authors import forms, initial_only, name_level
    from link_work_people import ORG as ORG0, UF, norm_name
    from narrow_coauthor_mints import ORG as ORG1, KNOWN_ERRORS
    from propose_person_dup_merges import strict_agree, name_forms
    db = duck()
    R = Counter()
    st = None
    if not args.no_validate:
        import keylog_snapshot as KS
        st = KS.read_state()
    hist_j, journal_key = history_journals()
    roles = {}
    with gzip.open(ROOT / 'data/person-facts/person-roles.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            roles[r['key']] = (r['role'], r['confidence'])
    hist = {k for k, (r, c) in roles.items() if r == 'historian' and c in ('strong', 'supported')}
    plab, porc = {}, {}
    for k, lab, an in db.execute(f"SELECT key, label, anchors FROM '{G}/person.parquet'").fetchall():
        plab[k] = lab or ''
        for a in an or []:
            if a.startswith('orcid:'):
                porc[a[6:]] = k
    from review_books import main_title as fold_main
    wjournal, wyear, wlabel, wreview, wkind = {}, {}, {}, set(), {}
    for k, j, y, l, kind, kp in db.execute(f"""SELECT key, journal, year, label, kind, kind_proposed FROM '{G}/work.parquet'
            WHERE resolution <> 'unkeyed'""").fetchall():
        wjournal[k], wyear[k], wlabel[k], wkind[k] = j or '', y, l or '', kind
        if kind == 'review' or kp == 'review' or re.match(r'(?i)\s*(review of|book review|rezension|compte[- ]rendu|recension)', l or ''):
            wreview.add(k)
    # a journal record whose title is a book's title is most often a review of that book, and OpenAlex then prints the
    # book's authors as the record's authors ('La société libérale duplessiste', Labour/Le Travail 1995: Emery reviewing
    # Bourque, Duchastel and Beauchemin): never minted from
    book_titles = {m for (t,) in db.execute(f"SELECT label FROM '{G}/work.parquet' WHERE kind = 'book' AND label IS NOT NULL").fetchall()
                   for m in [fold_main(t)] if len(m.split()) >= 2}
    test = os.environ.get('COAUTHOR_TEST_WORKS')     # a light test on a few works: outputs go to SCR/test
    db.execute('CREATE OR REPLACE TABLE wk AS SELECT unnest(?) w', [sorted(test.split(',')) if test else sorted(wjournal)])
    out_dir = SCR / 'test' if test else OUT
    klog = keylog_authored(db)
    pos = load_positions(db)
    contrib = set()
    cp = WP / 'contributors.parquet'
    if cp.exists():
        contrib = {x for (x,) in db.execute(f"SELECT pid FROM '{cp}' WHERE role = 'contributor'").fetchall()}
    # Crossref ORCIDs printed on the record (history journals on E:), by DOI and author position
    wdoi = dict((w, d) for w, d, *_ in load_keyed_doi_works(db))
    cr_orcid, cr_pages = {}, {}
    if (SCR / 'crossref-authors.parquet').exists():
        db.execute('CREATE OR REPLACE TABLE dk AS SELECT unnest(?) doi', [sorted(set(wdoi.values()))])
        for doi, au, pg in db.execute(f"SELECT doi, authors, page FROM '{SCR}/crossref-authors.parquet' WHERE doi IN (SELECT doi FROM dk)").fetchall():
            cr_orcid[doi] = json.loads(au)
            cr_pages[doi] = npages(pg)
    # ---- mentions
    mentions, held = [], []
    def hold(m, reason, **kw):
        R['held|' + reason] += 1
        held.append(dict(work=m['work'], pos=m['pos'], name=m['name'], journal=wjournal.get(m['work'], ''),
                         year=wyear.get(m['work']), reason=reason, **kw))
    for w, ps in pos.items():
        if w in wreview:
            R['works_skipped|review record'] += 1
            continue
        if wkind.get(w) not in ('book', 'thesis') and fold_main(wlabel.get(w, '')) in book_titles:
            R['works_skipped|a journal record with a book title (probably a review)'] += sum(
                1 for p in ps if p['state'] not in ('credited', 'exact', 'linked'))
            continue
        lab_ = wlabel.get(w, '')
        if SECTION.match(lab_) or re.search(r'\s/\s*[A-Z][^/]{3,60}\.?$', lab_):
            # a journal section record ('Reviews', 'Short notices', 'Books: ...', 'Title / Author'): its printed names
            # are the section's contributors or reviewed authors, not co-authors (sample check 2026-11-14)
            R['works_skipped|review or notes section record'] += 1
            continue
        if (wyear.get(w) or 9999) < 1990 and max((p['n_auth'] or 0) for p in ps) >= 5:
            # five or more names on a pre-1990 humanities record are a review or notes section (Social Forces 1926,
            # Italian Studies 1970, Acta Poloniae Historica 1982 in the sample)
            R['works_skipped|pre-1990 record with 5+ names (a section)'] += 1
            continue
        if (cr_pages.get(wdoi.get(w)) or 99) <= 3:
            # a record of one to three pages (Crossref) is a review or a note; OpenAlex often prints a review's book
            # authors as its authors (Labour/Le Travail 36, p. 354: Emery reviewing Bourque, Duchastel, Beauchemin)
            R['works_skipped|three pages or fewer (review or note)'] += 1
            continue
        keyed = set(klog.get(w, ())) | {x for p in ps if p['state'] == 'exact' and p['key'] for x in p['key'].split(';')}
        keyed |= {p['credited'] for p in ps if p['credited']}
        if not keyed:
            continue
        jk = journal_key(wjournal.get(w) or ps[0]['journal'] or '')
        hv = bool(jk) and jk in hist_j
        if not hv and not keyed & hist:
            continue
        matched = {p['credited'] for p in ps if p['credited']} | {x for p in ps if p['state'] in ('exact', 'linked') and p['key']
                                                                  for x in p['key'].split(';')}
        unmatched = set(klog.get(w, ())) - matched
        for p in ps:
            if p['state'] in ('credited', 'exact', 'linked'):
                continue
            if p['pid'] in contrib:
                continue
            m = dict(p, keyed=sorted(keyed), hv=hv, jk=jk)
            R['mentions'] += 1
            if (w, p['pos']) in KNOWN_ERRORS:
                hold(m, 'known-source-error')
                continue
            if p['state'] in ('possible', 'ambiguous'):
                hold(m, 'a key bears a compatible name (linker state possible/ambiguous): a link question, not a mint',
                     candidates=p['candidates'] or '')
                continue
            fs = forms(p['name'] or '')
            if not fs:
                hold(m, 'name not parsed')
                continue
            if ORG0.search(p['name']) or ORG1.search(p['name']):
                hold(m, 'organisation or non-personal name')
                continue
            f_, _, g = fs[0]
            m['fam'], m['g'] = f_, g
            if len(f_) >= 4 and re.search(r'\b' + re.escape(f_) + r'\b', fold_main(wlabel.get(w, '')) + ' ' +
                                         re.sub(r'[^a-z0-9 ]', ' ', I_fold(wlabel.get(w, '')))):
                hold(m, 'the printed name is in the title (the subject, not an author)')
                continue
            last = (p['name'] or '').split()[-1] if (p['name'] or '').split() else ''
            if initial_only(g) or (',' not in p['name'] and len(last.strip('.')) <= 2 and last.strip('.').isalpha()
                                   and last.lower() not in ('da', 'de', 'di', 'do', 'du', 'la', 'le', 'li', 'lu', 'ma', 'wu', 'xu', 'yu', 'ng', 'he', 'hu', 'ye', 'an', 'oh', 'ko', 'so', 'bo', 'ho', 'lo')
                                   or (',' not in p['name'] and last.isupper() and len(last) <= 3)):
                # 'Hutton DA' (Vancouver style: family then initials) reads as given 'Hutton', family 'Da'
                hold(m, 'initials only (a mint needs the printed full name)')
                continue
            if unmatched:
                hold(m, 'a key-log author of the work matches no printed name (the mention may be that author)',
                     unmatched=' '.join(sorted(unmatched)))
                continue
            if (p['n_auth'] or 0) > CAP and not p['orcid']:
                hold(m, f'more than {CAP} authors and no ORCID')
                continue
            mentions.append(m)
    print('mentions to group', len(mentions), flush=True)
    # printed vs inferred ORCIDs
    ro = raw_orcids({m['oa_work'] for m in mentions if m['orcid'] and m['source'] == 'openalex' and m['oa_work']})
    for m in mentions:
        m['printed_orcid'] = ''
        if m['source'] == 'openalex':
            r = ro.get((m['oa_work'], m['pos']))
            if r and r[0]:
                m['printed_orcid'] = r[0]
        elif m['source'] == 'crossref':
            m['printed_orcid'] = m['orcid'] or ''
        if not m['printed_orcid']:                      # the Crossref record of the DOI prints it (same family name)
            for a in cr_orcid.get(wdoi.get(m['work']), []) or []:
                if a['orcid'] and forms(a['name']) and forms(a['name'])[0][0] == m['fam']:
                    m['printed_orcid'] = a['orcid']
        m['inferred_orcid'] = m['orcid'] if m['orcid'] and m['orcid'] != m['printed_orcid'] else ''
    # ---- group: printed ORCID, else full name + a shared fact
    uf = UF()
    by_o, bucket = defaultdict(list), defaultdict(list)
    for i, m in enumerate(mentions):
        uf.find(i)
        if m['printed_orcid']:
            by_o[m['printed_orcid']].append(i)
        bucket[m['fam'], m['g'][0]].append(i)
    for ii in by_o.values():
        for j in ii[1:]:
            uf.union(ii[0], j)
    basis = defaultdict(set)
    for ii in bucket.values():
        if len(ii) < 2:
            continue
        for x in range(len(ii)):
            for y in range(x + 1, len(ii)):
                a, b = mentions[ii[x]], mentions[ii[y]]
                if a['work'] == b['work'] or name_level(a['g'], b['g']) != 'full':
                    continue
                if a['printed_orcid'] and b['printed_orcid'] and a['printed_orcid'] != b['printed_orcid']:
                    continue
                fx = set()
                if set(a['keyed']) & set(b['keyed']):
                    fx.add('keyed-coauthor')
                if a['jk'] and a['jk'] == b['jk']:
                    fx.add('venue')
                if a['oa_author'] and a['oa_author'] == b['oa_author']:
                    fx.add('openalex-author')
                if set(a['rors'] or []) & set(b['rors'] or []):
                    fx.add('institution')
                if a['inferred_orcid'] and a['inferred_orcid'] == b['inferred_orcid']:
                    fx.add('same-inferred-orcid')
                if fx:
                    uf.union(ii[x], ii[y])
                    basis[uf.find(ii[x])] |= fx
    groups = defaultdict(list)
    for i in range(len(mentions)):
        groups[uf.find(i)].append(i)
    gb = defaultdict(set)
    for r_, fx in basis.items():
        gb[uf.find(r_)] |= fx
    # ---- twins: live keys with the same full name (strict) or a variant-level given name
    by_fam = defaultdict(list)
    for k, lab in plab.items():
        for f_, g in name_forms(lab):
            by_fam[f_].append((k, g))
    people, ops = [], []
    printed_all = {m['printed_orcid'] for m in mentions if m['printed_orcid']}
    used_orcid = set()
    for n_, (root, ii) in enumerate(sorted(groups.items())):
        ms = [mentions[i] for i in ii]
        works = sorted({m['work'] for m in ms})
        orc = sorted({m['printed_orcid'] for m in ms if m['printed_orcid']})
        inf = sorted({m['inferred_orcid'] for m in ms if m['inferred_orcid']} - set(orc))
        names = Counter(m['name'] for m in ms)
        lab = max(names, key=lambda x: (names[x], len(x)))
        if len(orc) > 1:
            R['held|two printed ORCIDs in one group'] += 1
            held.append(dict(work=' '.join(works), pos='', name=lab, reason='two printed ORCIDs in one group', orcids=' '.join(orc)))
            continue
        why = ('O' if orc else '') + ('G' if len(works) >= 2 else '') + ('H' if any(m['hv'] for m in ms) else '')
        if not why:
            R['not_covered|single work, no ORCID, not a history venue (co-author of a historian key)'] += 1
            held.append(dict(work=works[0], pos=ms[0]['pos'], name=lab, journal=wjournal.get(works[0], ''), year=wyear.get(works[0]),
                             reason='not covered: one work outside history venues, no printed ORCID'))
            continue
        allfull = all(name_level(ms[0]['g'], m['g']) == 'full' for m in ms)
        # an ORCID OpenAlex inferred anchors only a person who already rests on two works (rule G) with the name in full
        # on every mention; a one-work mint keeps it as a member (an ORCID anchor would pull in every work of the record)
        anchor_orcid = orc[0] if orc else (inf[0] if len(inf) == 1 and allfull and 'G' in why
                                           and inf[0] not in printed_all and inf[0] not in used_orcid else '')
        if anchor_orcid:
            used_orcid.add(anchor_orcid)
        tw_orc = porc.get(anchor_orcid) or next((porc[o] for o in inf if o in porc), None)
        if not tw_orc and st is not None:          # keys newer than the build (the key log itself)
            tw_orc = next((x for o in [anchor_orcid] + inf if o for x in st.lookup('orcid:' + o)), None)
        if tw_orc:
            R['held|ORCID already on a key'] += 1
            held.append(dict(work=' '.join(works), pos='', name=lab, reason='ORCID already on a key (a link, not a mint)', key=tw_orc))
            continue
        strict = sorted({k for f_, g in name_forms(lab) for k, g2 in by_fam.get(f_, ()) if strict_agree(g, g2)})
        if strict:
            R['held|a live key bears the same full name'] += 1
            held.append(dict(work=' '.join(works), pos='', name=lab, reason='a live key bears the same full name (possible name-form link)',
                             key=' '.join(strict[:5]), key_labels=' | '.join(plab[k] for k in strict[:5])))
            continue
        variant = sorted({k for f_, g in name_forms(lab) for k, g2 in by_fam.get(f_, ()) if name_level(g, g2) == 'variant'})
        ph = f'new:p{n_}'
        anchors = ([f'orcid:{anchor_orcid}'] if anchor_orcid else []) + sorted({f"coauthor-mention:{m['work']}:{m['pos']}" for m in ms})
        members = sorted({f"openalex-author:{m['oa_author']}" for m in ms if m['oa_author']}) + \
            [f'orcid-inferred:{o}' for o in inf if o != anchor_orcid]
        cos = sorted({k for m in ms for k in m['keyed']})
        rule = {'O': 'an ORCID printed on the record', 'G': 'the same full name on {} works joined on {}'.format(
                    len(works), ', '.join(sorted(gb.get(root, ())) or ['a printed ORCID'])),
                'H': 'a work in a history venue with a keyed co-author'}
        bas = '; '.join(rule[c] for c in why) + (f'; ORCID {anchor_orcid} inferred by OpenAlex, name in full on every mention'
                                                 if anchor_orcid and not orc else '') + \
            f"; printed co-author of {', '.join(cos[:6])} on {len(works)} work(s); no person key bears a compatible name " \
            '(work-people linker state none); dead end: only the co-authored works (coauthor_gaps.py 2026-11-14)'
        ops.append(dict(event='mint', key=ph, type='person', label=lab, resolution='established' if anchor_orcid else 'recorded',
                        anchors=anchors, aliases=[], members=members, basis=bas))
        for m in sorted(ms, key=lambda m: (m['work'], m['pos'])):
            ops.append(dict(event='mint', key=f"new:c{n_}-{m['pos']}-{m['work']}", type='claim', label='', resolution='recorded',
                            anchors=[f"coauthor-claim:{m['work']}:{m['pos']}"],
                            relation=dict(subject=anchors[0], predicate='authored', object=m['work']),
                            basis=f"author {m['pos'] + 1} of {m['n_auth']} in the {m['source']} record of the work"))
        people.append(dict(ph=ph, label=lab, rule=why, orcid=anchor_orcid, orcid_printed=bool(orc), works=works, coauthors=cos,
                           n_auth=max(m['n_auth'] or 0 for m in ms), variant=variant, facts=sorted(gb.get(root, ())),
                           journals=sorted({wjournal.get(w, '') for w in works}), years=sorted({wyear.get(w) or 0 for w in works})))
    R['people_to_mint'] = len(people)
    R['people_by_rule'] = dict(Counter(p['rule'] for p in people))
    R['people_by_n_works'] = dict(Counter(min(len(p['works']), 5) for p in people))
    R['people_with_variant_name_key'] = sum(1 for p in people if p['variant'])
    R['claims'] = sum(1 for o in ops if o['type'] == 'claim')
    # what the 11-11 narrowed rule would have kept of these (printed ORCID, or 2+ works joined by OpenAlex author id,
    # historian co-author or institution ROR) and what the loosening adds
    old_facts = {'openalex-author', 'institution', 'keyed-coauthor'}
    R['narrowed_rule_would_keep'] = sum(1 for p in people if p['orcid_printed'] or (len(p['works']) >= 2 and set(p['facts']) & old_facts))
    R['added_by_loosening'] = dict(Counter(p['rule'] for p in people if not (p['orcid_printed'] or (len(p['works']) >= 2
                                                                                                  and set(p['facts']) & old_facts))))
    proposal = dict(basis='co-authors printed on keyed works, missing from the graph (owner framing 2026-11-14): printed full name and '
                          'an ORCID on the record, or 2+ works joined by a shared co-author/venue/OpenAlex id/ROR, or one work in a '
                          'history venue with a keyed co-author; one-work mints stay one-work keys; twins held (coauthor_gaps.py)',
                    decided_by='rule', ops=ops)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False) + '\n')
    with gzip.open(out_dir / 'held.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        cols = ['work', 'pos', 'name', 'journal', 'year', 'reason', 'candidates', 'unmatched', 'key', 'key_labels', 'orcids']
        w_ = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w_.writeheader()
        w_.writerows(held)
    with gzip.open(SCR / 'people.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(people, f, ensure_ascii=False)
    # sample: 60 by seed, plus the probes
    import hashlib     # stable under small changes of the population: the 60 lowest hashes of label + works
    smp = sorted(people, key=lambda p: hashlib.md5(('20261114' + p['label'] + ' '.join(p['works'])).encode()).hexdigest())[:60]
    probes = [p for p in people if set(p['works']) & {'w-549919', 'w-703278'}]
    sp = out_dir / 'sample-checked.csv'
    old = {}
    if sp.exists():
        with open(sp, encoding='utf-8') as f:
            old = {r['placeholder'] + r['label']: (r['verdict'], r['note']) for r in csv.DictReader(f)}
    with open(sp, 'w', newline='', encoding='utf-8') as f:
        w_ = csv.writer(f)
        w_.writerow(['placeholder', 'label', 'rule', 'orcid', 'works', 'journals', 'years', 'keyed_coauthors', 'variant_name_keys',
                     'verdict', 'note'])
        for p in probes + [x for x in smp if x not in probes]:
            w_.writerow([p['ph'], p['label'], p['rule'], p['orcid'], ' '.join(p['works'][:6]), ' | '.join(p['journals'][:3])[:150],
                         ' '.join(str(y) for y in p['years'][:6]), ' '.join(f'{k} {plab.get(k, "")}' for k in p['coauthors'][:4])[:200],
                         ' '.join(f'{k} {plab.get(k, "")}' for k in p['variant'][:3]), *old.get(p['ph'] + p['label'], ('', ''))])
    if st is not None:
        R['keylog_seq'] = st.seq
        ev, _ = I.materialise(st, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(ev)
    rep = json.loads((out_dir / 'report.json').read_text()) if (out_dir / 'report.json').exists() else {}
    rep['propose'] = dict(sorted(R.items()))
    rep['propose']['probes'] = [dict(label=p['label'], rule=p['rule'], orcid=p['orcid'], works=p['works']) for p in probes]
    (out_dir / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(rep['propose'], indent=1, default=str))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=['crossref-index', 'measure', 'sample-fetch', 'fetch', 'propose'])
    ap.add_argument('--n', type=int, default=300)
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    dict(propose=propose, measure=measure, fetch=fetch, **{'crossref-index': crossref_index, 'sample-fetch': sample_fetch})[args.cmd](args)


if __name__ == '__main__':
    main()
