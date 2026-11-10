"""Crossref reference lists -> citing work keys and CITES edges (2026-11-08; see scripts/crossref_references.py).

mint:   every harvested article (Crossref type journal-article) whose DOI the key log does not hold gets a work key
        anchored on the DOI, labelled with its title, `year:` and `journal:` members (as scripts/key_jstor_articles.py
        does for JSTOR items). No person is credited here; the DOI routes do that later.
        Same article, other DOI (2026-11-09, user: CSSH is in JSTOR under 10.2307/..., in Crossref under Cambridge's
        10.1017/...): before minting, the publisher DOI is attached to a graph work that is already this article,
        found by (1) the JSTOR metadata index (/mnt/e/jstor-index.parquet): same journal, year within one, the same
        whole-title key, and one JSTOR item only, whose DOI the key log holds; else (2) the graph's title + author
        family index (the export matcher's work_index): year within one, one article/review/other work. A work that
        already holds a DOI with the same prefix is left alone (two DOIs from one publisher are two records), and a
        work two harvested records point at gets neither (minted as before, counted).
export: each reference of each harvested article is matched to one graph work:
        - 'doi': the reference carries a DOI the graph holds (publisher- or Crossref-matched);
        - otherwise the JSTOR session's matcher (data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py:
          main title key + an author family name, year within one = 'strong'; no year = 'no_year'; a later year =
          'edition' (a reprint or translation, kept with CITES.edition = true); an earlier year is left out).
          Crossref writes the reference author as 'Family Given' ('Clifford Jim'), so the first and the last word of
          the name are both tried, and a hit must be one graph work. The title is article-title, else volume-title
          (series-title for chapters), else nothing: references given only as an unstructured citation string are
          counted, not parsed here.
        Writes data/graph/crossref-cites.csv.gz (citing_work, cited_work, citations, basis), the same shape as the
        JSTOR table; scripts/build_graph.py loads both.

    python3 scripts/crossref_citations.py mint --out data/identifiers/crossref-articles-2026-11-08
    python3 scripts/crossref_citations.py export --out data/graph/crossref-cites.csv.gz
"""
import argparse, collections, csv, glob, gzip, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State, DEFAULT_DIR, materialise  # noqa: E402

RAW = '/mnt/e/crossref-refs-2026-11-08'
JSTOR_INDEX = '/mnt/e/jstor-index.parquet'
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.csv'


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


def mint(args):
    state = State.load(DEFAULT_DIR)
    titles = {r['id']: r['title'] for r in csv.DictReader(open(CATALOGUE, encoding='utf-8'))}
    rep, ops, seen = collections.Counter(), [], set()
    todo = []
    for it in records(args.files):
        rep['records'] += 1
        if it.get('type') != 'journal-article':
            rep['not_journal_article'] += 1; continue
        a = 'doi:' + it['DOI'].strip().lower()
        if a in state.anchor:
            rep['already_keyed'] += 1; continue
        if a in seen:
            rep['duplicate'] += 1; continue
        seen.add(a)
        todo.append(it)
    m = matcher()
    idx, _ = m.work_index()
    jstor = jstor_by_journal({titles.get(it.get('_journal'), (it.get('container-title') or [''])[0]) for it in todo})
    found = {}                                       # DOI anchor -> (key, route)
    for it in todo:
        y, j = year_of(it), titles.get(it.get('_journal'), (it.get('container-title') or [''])[0])
        title = re.sub(r'\s+', ' ', ' '.join(it.get('title') or [])).strip()
        key, why = same_work(it, title, y, j, state, jstor, idx, m) if title else (None, 'no_title')
        if key:
            found['doi:' + it['DOI'].strip().lower()] = (key, why)
        else:
            rep['bridge_' + why] += 1
    per_key = collections.Counter(k for k, _ in found.values())
    for it in todo:
        a = 'doi:' + it['DOI'].strip().lower()
        y, j = year_of(it), titles.get(it.get('_journal'), (it.get('container-title') or [''])[0])
        title = re.sub(r'\s+', ' ', ' '.join(it.get('title') or [])).strip()
        if a in found and per_key[found[a][0]] == 1:
            key, route = found[a]
            ops.append(dict(event='attach', key=key, anchors=[a], aliases=[], members=[],
                            basis=f'the same journal article in {j} ({y}) under the publisher DOI, found by '
                                  f'{route.replace("_", " ")} (scripts/crossref_citations.py)'))
            rep['attached_' + route] += 1
            continue
        if a in found:
            rep['bridge_key_wanted_twice'] += 1
        ops.append(dict(event='mint', key=f'new:{len(ops)}', type='work',
                        label=title[:400] or f'[untitled article in {j}, {y}]', resolution='recorded', anchors=[a],
                        aliases=[], members=[m for m in (f'year:{y}' if y else '', f'journal:{j}' if j else '') if m],
                        basis=f'journal article in {j} ({y}) with a Crossref reference list (cited-references source; '
                              f'scripts/crossref_citations.py)'))
        rep['minted'] += 1
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(basis='journal articles with Crossref reference lists -> work keys', decided_by='rule', ops=ops),
                      ensure_ascii=False) + '\n'
    if len(body) > 50_000_000:
        with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
    else:
        (args.out / 'proposal.json').write_text(body)
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(rep.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(rep.items()))))


def matcher():
    p = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/jstor_match_candidates.py'
    spec = importlib.util.spec_from_file_location('jstor_match_candidates', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def export(args):
    import duckdb
    m = matcher()
    idx, doi_work = m.work_index()
    rep = collections.Counter()
    edges = collections.defaultdict(lambda: [0, set()])         # (citing, cited) -> [references, bases]
    for it in records(args.files):
        citing = doi_work.get(it['DOI'].strip().lower())
        if not citing:
            rep['citing_not_keyed'] += 1; continue
        rep['citing_records'] += 1
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
            e = edges[(citing, hit)]
            e[0] += 1; e[1].add(basis)
    rows = [(a, b, n, 'edition' if bs == {'edition'} else 'match') for (a, b), (n, bs) in sorted(edges.items())]
    with gzip.open(args.out, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['citing_work', 'cited_work', 'citations', 'basis'])
        w.writerows(rows)
    rep['edges'] = len(rows)
    rep['edition_edges'] = sum(r[3] == 'edition' for r in rows)
    rep['citing_works'] = len({r[0] for r in rows}); rep['cited_works'] = len({r[1] for r in rows})
    print(json.dumps(dict(sorted(rep.items()))))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('mint', 'export'))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--files', default='journal_*.jsonl.gz', help='harvest files to read (a pilot: journal_<id>*.jsonl.gz)')
    args = ap.parse_args()
    (mint if args.phase == 'mint' else export)(args)


if __name__ == '__main__':
    main()
