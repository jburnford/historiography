"""One streaming pass over the Crossref public data file (2026-11-08; user: "if crossref has citations data, we should
pull it all"). The March 2026 file (Academic Torrents b5ee0e10..., 207 GiB, 35,909 jsonl.gz files, ~180M records,
open metadata) sits on E: (/mnt/e/crossref-2026). Two phases, each one read of every file, files in parallel; results
per file go to E: so a run resumes where it stopped. Metadata only.

dois   Graph works without a DOI (ORCID 'other' works, LC books, chapters) get candidate DOIs from Crossref's own
       records: same main title (the JSTOR matcher's cited_key), the record's first or any author's family name on the
       graph work, years within one, compatible types (journal-article -> article/other; book-chapter ->
       other/article; book, monograph, edited-book -> book; dissertation -> thesis), and the title+family pointing
       at exactly one graph work. Why: publishers often deposit a reference as a bare DOI plus the book title
       (Springer's Water History cites Clifford's 'River Lea in West Ham' as 10.2307/j.ctv10tq43d.7 + 'Urban rivers'),
       which only a DOI on our work can catch.
refs   Every record with a reference list: each reference is matched to one graph work by
       - its DOI, when the graph holds it or phase dois proposed it ('doi');
       - else a title: article-title, or a title parsed from the unstructured citation (quoted, or after the
         '(year)' / '. year.' of author-date styles), else volume-title; with the first or last word of the
         reference author as the family name (Crossref writes 'Clifford Jim', 'J Clifford', 'Clifford J'), through
         the JSTOR matcher's lookup ('strong', 'no_year', 'title+year', 'edition?' = later or earlier edition).
       A record with at least one hit is written with its own metadata (DOI, type, title, year, venue, ISSNs,
       authors' family names) and its hits; nothing else is kept.

    python3 scripts/crossref_dump_pass.py dois --workers 3
    python3 scripts/crossref_dump_pass.py refs --workers 3
    python3 scripts/crossref_dump_pass.py summary
"""
import argparse, collections, glob, gzip, importlib.util, json, multiprocessing as mp, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = '/mnt/e/crossref-dl/March 2026 Public Data File from Crossref'
OUT = Path('/mnt/e/crossref-2026/pass')
TYPES = {'journal-article': {'article', 'other'}, 'book-chapter': {'other', 'article'}, 'book': {'book'},
         'monograph': {'book'}, 'edited-book': {'book'}, 'reference-book': {'book'}, 'dissertation': {'thesis'}}

M = IDX = DOI_WORK = NODOI = NEWDOI = None


def matcher():
    p = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py'
    spec = importlib.util.spec_from_file_location('jstor_match_candidates', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def setup(phase):
    """Built once in the parent before the workers fork (copy-on-write)."""
    global M, IDX, DOI_WORK, NODOI, NEWDOI
    M = matcher()
    IDX, DOI_WORK = M.work_index()
    NODOI = {k for v in IDX.values() if isinstance(v, list) for k, _, _ in v} - set(DOI_WORK.values())
    NEWDOI = {}
    if phase == 'refs':
        p = OUT / 'doi-assignments.json'
        NEWDOI = json.loads(p.read_text()) if p.exists() else {}


def year_of(it):
    for k in ('issued', 'published-print', 'published-online', 'created'):
        try:
            return int(it[k]['date-parts'][0][0])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return None


def families(it):
    return [M.fold(a.get('family') or a.get('name') or '').split()[-1:] for a in it.get('author') or [] if a]


def one_work(tk, fams, year, kinds=None, nodoi_only=False):
    """-> (work, basis, work_year) when the title + some family points at exactly one graph work."""
    found = {}
    for fam in dict.fromkeys(f for f in fams if f and len(f) >= 2):
        pick, b = M.lookup(IDX, tk, fam, year)
        if not pick or len(pick) != 1:
            continue
        key, kind, wy = pick[0]
        if kinds is not None and kind not in kinds:
            continue
        if nodoi_only and key not in NODOI:
            continue
        found[key] = (b, wy)
    if len(found) != 1:
        return None
    (key, (b, wy)), = found.items()
    return key, b, wy


QUOTED = re.compile(r'["“‘«]([^"”’»]{8,}?)[,.]?["”’»]')
AUTHOR_DATE = re.compile(r'\(\s*(\d{4})[a-z]?\s*\)\.?\s*([^.?!]{8,}?[.?!])')     # 'Clifford J (2012) The River Lea ...'
CHICAGO_AD = re.compile(r'^[^0-9]{3,150}?\.\s*(\d{4})[a-z]?\.\s*([^.?!]{8,}?[.?!])')  # 'Clifford, Jim. 2017. West Ham ...'


def parse_unstructured(u):
    q = QUOTED.search(u)
    if q:
        return q.group(1)
    for rx in (AUTHOR_DATE, CHICAGO_AD):
        m = rx.search(u)
        if m:
            return m.group(2)
    return None


def ref_hit(r):
    d = (r.get('DOI') or '').strip().lower()
    if d:
        w = DOI_WORK.get(d) or NEWDOI.get(d)
        if w:
            return w, 'doi', None
    au = r.get('author') or ''
    u = r.get('unstructured') or ''
    if not au and u:
        au = re.split(r'[,(.]', u, maxsplit=1)[0]
    words = [w for w in M.fold(au).split() if len(w) >= 2]
    if not words:
        return None
    fams = words[:1] + words[-1:]
    try:
        y = int(str(r.get('year') or '')[:4])
    except ValueError:
        m = re.search(r'\b(1[5-9]\d\d|20[0-2]\d)\b', u)
        y = int(m.group(1)) if m else None
    for t in (r.get('article-title'), parse_unstructured(u) if u else None, r.get('volume-title'), r.get('series-title')):
        if not t:
            continue
        tk = M.cited_key(t)
        if not M.usable(tk):
            continue
        h = one_work(tk, fams, y)
        if h:
            key, b, wy = h
            if b == 'edition?':
                b = 'edition' if (y and wy and y > wy) else 'edition_earlier'
            return key, b, y
    return None


def do_file(task):
    phase, path = task
    dest = OUT / phase / (Path(path).name.replace('.jsonl.gz', '.jsonl'))
    if dest.exists():
        return 0
    out = []
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            for line in f:
                it = json.loads(line)
                if phase == 'dois':
                    d = (it.get('DOI') or '').lower()
                    kinds = TYPES.get(it.get('type'))
                    if not d or d in DOI_WORK or not kinds or not it.get('title'):
                        continue
                    tk = M.cited_key(it['title'][0])
                    if not M.usable(tk):
                        continue
                    h = one_work(tk, [x[0] for x in families(it) if x], year_of(it), kinds, nodoi_only=True)
                    if h and h[1] in ('strong', 'title+year'):
                        out.append(dict(doi=d, work=h[0], basis=h[1], type=it.get('type'), year=year_of(it),
                                        title=it['title'][0][:300]))
                else:
                    refs = it.get('reference') or []
                    if not refs:
                        continue
                    hits = []
                    for i, r in enumerate(refs):
                        h = ref_hit(r)
                        if h:
                            hits.append([i, h[0], h[1], h[2]])
                    if hits:
                        out.append(dict(doi=(it.get('DOI') or '').lower(), type=it.get('type'), year=year_of(it),
                                        title=(it.get('title') or [''])[0][:400],
                                        venue=(it.get('container-title') or [''])[0][:200], issn=it.get('ISSN') or [],
                                        families=[x[0] for x in families(it) if x][:12], n_refs=len(refs), hits=hits))
    except (EOFError, OSError, gzip.BadGzipFile) as e:   # a file still downloading or truncated: retry next run
        return -1
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.part')
    with open(tmp, 'w', encoding='utf-8') as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + '\n')
    os.replace(tmp, dest)
    return len(out)


def summary():
    rep = collections.Counter()
    for p in glob.glob(str(OUT / 'dois' / '*.jsonl')):
        for line in open(p, encoding='utf-8'):
            rep['doi_candidates'] += 1
    by_work = collections.defaultdict(set)
    for p in glob.glob(str(OUT / 'dois' / '*.jsonl')):
        for line in open(p, encoding='utf-8'):
            o = json.loads(line); by_work[o['work']].add(o['doi'])
    # a work answering to more than three DOIs is ambiguous (several editions or a common title): none assigned
    assign = {d: w for w, ds in by_work.items() if len(ds) <= 3 for d in ds}
    rep['works_given_doi'] = sum(1 for ds in by_work.values() if len(ds) <= 3)
    rep['works_ambiguous'] = sum(1 for ds in by_work.values() if len(ds) > 3)
    (OUT / 'doi-assignments.json').write_text(json.dumps(assign))
    for p in glob.glob(str(OUT / 'refs' / '*.jsonl')):
        for line in open(p, encoding='utf-8'):
            o = json.loads(line)
            rep['citing_records'] += 1
            for _, _, b, _ in o['hits']:
                rep['hits_' + b] += 1
    print(json.dumps(dict(sorted(rep.items())), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('dois', 'refs', 'summary'))
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--limit', type=int, help='first N files (pilot)')
    args = ap.parse_args()
    if args.phase == 'summary':
        return summary()
    t0 = time.time()
    setup(args.phase)
    files = sorted(glob.glob(f'{DUMP}/*.jsonl.gz'), key=lambda p: int(Path(p).name.split('.')[0]))
    if args.limit:
        files = files[:args.limit]
    print(f'index ready in {time.time() - t0:.0f}s; {len(files)} files', flush=True)
    done = bad = n = 0
    ctx = mp.get_context('fork')
    with ctx.Pool(args.workers) as pool:
        for r in pool.imap_unordered(do_file, [(args.phase, f) for f in files], chunksize=4):
            done += 1
            if r < 0:
                bad += 1
            else:
                n += r
            if done % 500 == 0:
                print(f'{done}/{len(files)} files, {n} rows, {bad} unreadable, {time.time() - t0:.0f}s', flush=True)
    print(f'done: {done} files, {n} rows, {bad} unreadable (rerun to retry), {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
