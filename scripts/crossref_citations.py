"""Crossref reference lists -> citing work keys and CITES edges (2026-11-08; see scripts/crossref_references.py).

mint:   every harvested article (Crossref type journal-article) whose DOI the key log does not hold gets a work key
        anchored on the DOI, labelled with its title, `year:` and `journal:` members (as scripts/key_jstor_articles.py
        does for JSTOR items). No person is credited here; the DOI routes do that later.
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
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.csv'


def records():
    for p in sorted(glob.glob(f'{RAW}/journal_*.jsonl.gz')):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)


def year_of(it):
    try:
        return int(it['issued']['date-parts'][0][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def mint(args):
    state = State.load(DEFAULT_DIR)
    titles = {r['id']: r['title'] for r in csv.DictReader(open(CATALOGUE, encoding='utf-8'))}
    rep, ops, seen = collections.Counter(), [], set()
    for it in records():
        rep['records'] += 1
        if it.get('type') != 'journal-article':
            rep['not_journal_article'] += 1; continue
        a = 'doi:' + it['DOI'].strip().lower()
        if a in state.anchor:
            rep['already_keyed'] += 1; continue
        if a in seen:
            rep['duplicate'] += 1; continue
        seen.add(a)
        y, j = year_of(it), titles.get(it.get('_journal'), (it.get('container-title') or [''])[0])
        title = re.sub(r'\s+', ' ', ' '.join(it.get('title') or [])).strip()
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
    for it in records():
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
    args = ap.parse_args()
    (mint if args.phase == 'mint' else export)(args)


if __name__ == '__main__':
    main()
