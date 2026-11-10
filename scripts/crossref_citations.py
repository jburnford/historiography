"""Crossref reference lists -> CITES edges (2026-11-08; see scripts/crossref_references.py).

Two layers (KG session, 2026-11-10, taking the export over from the Crossref session): the 4.43M harvested articles
are NOT minted as key-log works (that would double the log). A citing article the key log already holds (by DOI)
cites as its work key; any other cites as `doi:<doi>`, and its metadata (title, year, journal) goes to a tracked
table, data/graph/crossref-cites/articles/part-NN.csv.gz, from which scripts/build_graph.py makes it a Work node (key
`doi:<doi>`, resolution `unkeyed`). Once some other record needs the article (an author credit, a review), it gets a
key in the usual way and the build uses the key instead.

bridge: attaches publisher DOIs to graph works that are already the same article (below); nothing is minted. Apply
        its proposal and rebuild the graph before `export`, so those articles cite as their keys.
        Same article, other DOI (2026-11-09, user: CSSH is in JSTOR under 10.2307/..., in Crossref under Cambridge's
        10.1017/...): before minting, the publisher DOI is attached to a graph work that is already this article,
        found by (1) the JSTOR metadata index (/mnt/e/jstor-index.parquet): same journal, year within one, the same
        whole-title key, and one JSTOR item only, whose DOI the key log holds; else (2) the graph's title + author
        family index (the export matcher's work_index): year within one, one article/review/other work. A work that
        already holds a DOI with the same prefix is left alone (two DOIs from one publisher are two records), and a
        work two harvested records point at gets neither (left unkeyed, counted).
export: each reference of each harvested article is matched to one graph work:
        - 'doi': the reference carries a DOI the graph holds (publisher- or Crossref-matched);
        - otherwise the JSTOR session's matcher (data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py:
          main title key + an author family name, year within one = 'strong'; no year = 'no_year'; a later year =
          'edition' (a reprint or translation, kept with CITES.edition = true); an earlier year is left out).
          Crossref writes the reference author as 'Family Given' ('Clifford Jim'), so the first and the last word of
          the name are both tried, and a hit must be one graph work. The title is article-title, else volume-title
          (series-title for chapters), else nothing: references given only as an unstructured citation string are
          counted, not parsed here.
        Writes data/graph/crossref-cites/part-NN.csv.gz (citing_work, cited_work, citations, basis), the shape of the
        JSTOR table, and data/graph/crossref-cites/articles/part-NN.csv.gz (doi, title, year, journal) for the unkeyed
        citing articles with at least one edge, in parts well under GitHub's 100 MB; scripts/build_graph.py loads them.
        Each record's edges stream to work files on E: (--work); DuckDB folds an article harvested twice.

    python3 scripts/crossref_citations.py bridge --out data/identifiers/crossref-bridge-2026-11-10
    python3 scripts/identifiers.py apply data/identifiers/crossref-bridge-2026-11-10/proposal.json && python3 scripts/build_graph.py
    python3 scripts/crossref_citations.py export [--files 'journal_00*.jsonl.gz' --out /tmp/pilot --work /tmp/pilot-work]
"""
import argparse, collections, csv, glob, gzip, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import materialise  # noqa: E402
import keylog_snapshot  # noqa: E402

RAW = '/mnt/e/crossref-refs-2026-11-08'
JSTOR_INDEX = '/mnt/e/jstor-index.parquet'
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.csv'
CITES_OUT = ROOT / 'data/graph/crossref-cites'      # part-NN.csv.gz (citing_work, cited_work, citations, basis)
CITES_PER_PART = 3_000_000                         # about 35 MB gzipped: GitHub refuses files over 100 MB
ARTICLES_PER_PART = 400_000                        # crossref-cites/articles/part-NN.csv.gz (doi, title, year, journal)


def records(pattern='journal_*.jsonl.gz'):
    for p in sorted(glob.glob(f'{RAW}/{pattern}')):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)


def year_of(it):
    try:
        return int(it['issued']['date-parts'][0][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def jstor_by_journal(journals):
    """-> {folded journal title: {whole-title key: [(jstor doi, year)]}} from the JSTOR metadata index, for the
    harvested journals only."""
    import duckdb
    from build_dissertation_citation_graph import fold
    want = {fold(j) for j in journals if j}
    db = duckdb.connect(); db.execute("SET memory_limit = '3GB'")
    names = [c for c, in db.execute(f"select distinct container from '{JSTOR_INDEX}' where container is not null").fetchall()
             if fold(c) in want]
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    if names:
        for doi, whole, year, container in db.execute(
                f"select doi, whole, year, container from '{JSTOR_INDEX}' where kind = 'article' and whole is not null "
                f"and container in (select unnest(?))", [names]).fetchall():
            out[fold(container)][whole].append((doi, year))
    return out


def same_work(it, title, y, j, state, jstor, idx, m):
    """-> (live key, route) for a graph work that is this article under another identifier, else (None, reason)."""
    from build_dissertation_citation_graph import fold
    from key_lc_works import title_key
    prefix = it['DOI'].strip().lower().split('/')[0]
    cands = set()
    hits = [d for d, jy in jstor.get(fold(j or ''), {}).get(title_key(title), []) if y and jy and abs(jy - y) <= 1]
    if len(hits) == 1:
        cands = set(state.lookup('doi:' + hits[0]))
        route = 'jstor_doi'
    if not cands:
        tk = m.tkey(title)
        if not m.usable(tk):
            return None, 'title_too_short'
        fams = {m.family(a.get('family') or '') for a in it.get('author') or []} - {''}
        for fam in fams:
            pick, b = m.lookup(idx, tk, fam, y)
            if b == 'strong':
                cands |= {k for k, kind, _ in pick if kind in ('article', 'review', 'other')}
        cands = {c for k in cands for c in state.lookup(k)}
        route = 'title_author_year'
    if not cands:
        return None, 'no_match'
    if len(cands) > 1:
        return None, 'two_works'
    key, = cands
    if any(a.startswith('doi:' + prefix + '/') for a in state.keys[key]['anchors']):
        return None, 'same_prefix_doi'
    return key, route


def slim(it, titles):
    """The fields the bridge needs (the harvest records carry whole reference lists: 23 GB gzipped)."""
    return dict(DOI=it['DOI'], title=re.sub(r'\s+', ' ', ' '.join(it.get('title') or [])).strip(), year=year_of(it),
                journal=titles.get(it.get('_journal'), (it.get('container-title') or [''])[0]),
                author=[{'family': a.get('family')} for a in it.get('author') or []])


def bridge(args):
    state = keylog_snapshot.read_state()        # the SQLite cache, read-only
    titles = {r['id']: r['title'] for r in csv.DictReader(open(CATALOGUE, encoding='utf-8'))}
    rep, ops, seen = collections.Counter(), [], set()
    todo = []
    for it in records(args.files):
        rep['records'] += 1
        if it.get('type') != 'journal-article':
            rep['not_journal_article'] += 1; continue
        a = 'doi:' + it['DOI'].strip().lower()
        if a in seen:
            rep['duplicate'] += 1; continue
        seen.add(a)
        if a in state.anchor:
            rep['already_keyed'] += 1; continue
        todo.append(slim(it, titles))
    del seen
    print(f"{rep['records']:,} records, {len(todo):,} unkeyed journal articles", file=sys.stderr, flush=True)
    m = matcher()
    idx, _ = m.work_index()
    jstor = jstor_by_journal({it['journal'] for it in todo})
    found = {}                                       # DOI anchor -> (key, route)
    for it in todo:
        key, why = same_work(it, it['title'], it['year'], it['journal'], state, jstor, idx, m) if it['title'] else (None, 'no_title')
        if key:
            found['doi:' + it['DOI'].strip().lower()] = (key, why, it['journal'], it['year'])
        else:
            rep['bridge_' + why] += 1
    per_key = collections.Counter(v[0] for v in found.values())
    for a, (key, route, j, y) in found.items():
        if per_key[key] != 1:
            rep['bridge_key_wanted_twice'] += 1; continue
        ops.append(dict(event='attach', key=key, anchors=[a], aliases=[], members=[],
                        basis=f'the same journal article in {j} ({y}) under the publisher DOI, found by '
                              f'{route.replace("_", " ")} (scripts/crossref_citations.py)'))
        rep['attached_' + route] += 1
    rep['left_unkeyed'] = len(todo) - sum(v for k, v in rep.items() if k.startswith('attached_'))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run', inplace=True)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='journal articles with Crossref reference lists: publisher DOIs of works the graph already holds',
        decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(rep.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(rep.items()))))


def matcher():
    p = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py'
    spec = importlib.util.spec_from_file_location('jstor_match_candidates', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def export(args):
    """Streams: each record's edges and (if unkeyed) its metadata go to work files on E:, then DuckDB folds duplicate
    records (one article in two journal files) and writes the tracked parts. 4.43M records: nothing held in memory
    but the matcher's index."""
    import duckdb
    m = matcher()
    idx, doi_work = m.work_index()
    titles = {r['id']: r['title'] for r in csv.DictReader(open(CATALOGUE, encoding='utf-8'))}
    rep = collections.Counter()
    work = Path(args.work); work.mkdir(parents=True, exist_ok=True)
    ef = gzip.open(work / 'edges-raw.csv.gz', 'wt', newline='', encoding='utf-8')
    af = gzip.open(work / 'articles-raw.csv.gz', 'wt', newline='', encoding='utf-8')
    ew, aw = csv.writer(ef), csv.writer(af)
    ew.writerow(['citing', 'cited', 'n', 'edition']); aw.writerow(['doi', 'title', 'year', 'journal'])
    for it in records(args.files):
        doi = it['DOI'].strip().lower()
        citing = doi_work.get(doi)
        if not citing:
            if it.get('type') != 'journal-article':
                rep['citing_not_keyed_not_article'] += 1; continue
            citing = 'doi:' + doi                               # an unkeyed article: a node from the article table
        local = {}                                              # cited -> [references, edition only]
        for r in it.get('reference') or []:
            rep['references'] += 1
            hit, basis = None, None
            d = (r.get('DOI') or '').strip().lower()
            if d:
                rep['ref_with_doi'] += 1
                if d in doi_work:
                    hit, basis = doi_work[d], 'doi'
            if not hit:
                t = r.get('article-title') or r.get('volume-title') or r.get('series-title')
                au = r.get('author') or ''
                if not t or not au:
                    rep['ref_unstructured_or_no_author' if r.get('unstructured') else 'ref_no_title_or_author'] += 1
                    continue
                tk = m.cited_key(t)
                if not m.usable(tk):
                    rep['ref_title_too_short'] += 1; continue
                words = [w for w in m.fold(re.sub(r'[,.]', ' ', au)).split() if len(w) >= 2]
                try:
                    y = int(str(r.get('year') or '')[:4])
                except ValueError:
                    y = None
                found = {}
                for fam in dict.fromkeys(words[:1] + words[-1:]):
                    pick, b = m.lookup(idx, tk, fam, y)
                    if pick and len(pick) == 1:
                        found[pick[0][0]] = (b, pick[0][2])
                if len(found) != 1:
                    rep['ref_no_unique_match' if not found else 'ref_two_works'] += 1; continue
                (hit, (b, wy)), = found.items()
                if b == 'edition?':
                    if not (y and wy and y > wy):
                        rep['ref_earlier_edition_skipped'] += 1; continue
                    basis = 'edition'
                else:
                    basis = b
            if hit == citing:
                continue
            rep['matched_' + basis] += 1
            e = local.setdefault(hit, [0, True])
            e[0] += 1; e[1] = e[1] and basis == 'edition'
        if not local:
            rep['citing_no_edges'] += 1; continue
        rep['citing_records_unkeyed' if citing.startswith('doi:') else 'citing_records_keyed'] += 1
        ew.writerows((citing, b, n, int(ed)) for b, (n, ed) in local.items())
        if citing.startswith('doi:'):
            aw.writerow((doi, re.sub(r'\s+', ' ', ' '.join(it.get('title') or [])).strip()[:400], year_of(it) or '',
                         titles.get(it.get('_journal'), (it.get('container-title') or [''])[0])))
    ef.close(); af.close()
    print(json.dumps(dict(sorted(rep.items()))), file=sys.stderr, flush=True)
    del idx, doi_work
    db = duckdb.connect(str(work / 'fold.duckdb'))
    db.execute(f"SET memory_limit = '6GB'; SET temp_directory = '{work}/duckdb-tmp'; SET preserve_insertion_order = false")
    db.execute(f"""CREATE OR REPLACE TABLE edges AS SELECT citing AS citing_work, cited AS cited_work, sum(n)::INTEGER AS citations,
                   CASE WHEN bool_and(edition = 1) THEN 'edition' ELSE 'match' END AS basis
                   FROM read_csv('{work}/edges-raw.csv.gz', header=true, all_varchar=false,
                                 columns={{'citing': 'VARCHAR', 'cited': 'VARCHAR', 'n': 'INTEGER', 'edition': 'INTEGER'}})
                   GROUP BY 1, 2""")
    db.execute(f"""CREATE OR REPLACE TABLE articles AS SELECT doi, any_value(title) AS title, min(year) AS year,
                   any_value(journal) AS journal
                   FROM read_csv('{work}/articles-raw.csv.gz', header=true,
                                 columns={{'doi': 'VARCHAR', 'title': 'VARCHAR', 'year': 'INTEGER', 'journal': 'VARCHAR'}})
                   GROUP BY 1""")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    adir = out / 'articles'; adir.mkdir(exist_ok=True)
    for d in (out, adir):
        for old in d.glob('part-*.csv.gz'):
            old.unlink()
    for name, d, order, per in (('edges', out, 'citing_work, cited_work', CITES_PER_PART), ('articles', adir, 'doi', ARTICLES_PER_PART)):
        total = db.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
        for n, off in enumerate(range(0, total, per), 1):
            db.execute(f"""COPY (SELECT * FROM {name} ORDER BY {order} LIMIT {per} OFFSET {off})
                           TO '{d}/part-{n:02d}.csv.gz' (HEADER, COMPRESSION gzip)""")
        rep[f'{name}_parts'] = -(-total // per)
    rep['edges'] = db.execute('SELECT count(*) FROM edges').fetchone()[0]
    rep['edges_from_unkeyed'] = db.execute("SELECT count(*) FROM edges WHERE citing_work LIKE 'doi:%'").fetchone()[0]
    rep['edition_edges'] = db.execute("SELECT count(*) FROM edges WHERE basis = 'edition'").fetchone()[0]
    rep['citing_works'], rep['cited_works'] = db.execute(
        'SELECT count(DISTINCT citing_work), count(DISTINCT cited_work) FROM edges').fetchone()
    rep['unkeyed_citing_articles'] = db.execute('SELECT count(*) FROM articles').fetchone()[0]
    db.close()
    (out / 'report.json').write_text(json.dumps(dict(sorted(rep.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(rep.items()))))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('bridge', 'export'))
    ap.add_argument('--out', type=Path, help='bridge: the proposal folder; export: the parts folder (default data/graph/crossref-cites)')
    ap.add_argument('--work', default='/mnt/e/crossref-export-2026-11-10', help='export: work files on E:')
    ap.add_argument('--files', default='journal_*.jsonl.gz', help='harvest files to read (a pilot: journal_<id>*.jsonl.gz)')
    args = ap.parse_args()
    if args.phase == 'export':
        args.out = args.out or CITES_OUT
    elif not args.out:
        sys.exit('bridge needs --out')
    (bridge if args.phase == 'bridge' else export)(args)


if __name__ == '__main__':
    main()
