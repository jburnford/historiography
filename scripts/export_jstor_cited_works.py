"""JSTOR article -> cited work matches of 2026-11-11 -> a tracked two-layer table (2026-11-11).

scripts/key_jstor_cited_works_full.py matched the parsed JSTOR note citations to LC 2016 books, OpenAlex, Crossref and
the JSTOR index (data/identifiers/jstor-cited-works-2026-11-11/: crosswalk.csv.gz, works.csv.gz, report.json). Under
the two-layer rule nothing is minted: the build adds CITES with source `jstor-matched` and, for cited works the key log
does not hold, Work nodes keyed by their identifier (resolution `unkeyed`), unless the cited-works layer
(data/graph/cited-works) already has the work.

Writes data/graph/jstor-cited-works/ (gzipped CSV, each file under 50 MB):
- cites.csv.gz   citing_work (key or doi:), cited_work (key, lccn:, doi:, openalex:), source (lc-full / openalex /
                 crossref / jstor-index / crossref-meta, or translation / edition), basis, citations (note rows, short forms
                 counted with their full citation), cited_as
                 Translations and later editions (2026-11-11), as the thesis side (export_cited_works.py): where the matched
                 work is a translation or later edition in data/graph/cited-works/editions.csv.gz (its `cited_as` node, or
                 any identifier of that node), the citation goes to the canonical work: source = relation (translation /
                 edition), basis = route, cited_as = the node it was matched to; several moved works of one article that
                 share a canonical are one row (relations, routes and nodes ';'-joined, citations summed). A node the
                 table gives two canonicals is not moved. No `replaces`: the moved row is the jstor-matched row itself.
- works.csv.gz   the cited works the key log does not hold (held_by new / unkeyed_layer): id, title, year, kind,
                 container, identifiers (';'), source, basis, lc_author (the LC name authority id of the LC main
                 entry, for an identifier link; no name text), citing_articles
- report.json
Only ids, catalogue metadata and edges: no JSTOR note text, no full text, no held candidates.

    python3 scripts/export_jstor_cited_works.py
"""
import argparse
import csv
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import ROOT  # noqa: E402

SRC = ROOT / 'data/identifiers/jstor-cited-works-2026-11-11'
CITED = ROOT / 'data/graph/cited-works'
OUT = ROOT / 'data/graph/jstor-cited-works'
MAX_BYTES = 50_000_000


def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def write_csv(path, header, rows, report):
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        n = 0
        for r in rows:
            w.writerow(r)
            n += 1
    size = path.stat().st_size
    if size >= MAX_BYTES:
        sys.exit(f'{path.name} is {size / 1e6:.0f} MB: split it into parts before committing')
    report['files'][path.name] = dict(rows=n, bytes=size)


def edition_index():
    """identifier -> set of (canonical, relation, route) for every translation/edition node of
    data/graph/cited-works/editions.csv.gz (rows whose cited_as is a node, not corpus:<work_id>), over the node id and
    every identifier the cited-works table gives that node (its LCCNs and alias ids)."""
    node_ids = {}
    for r in rd(CITED / 'works.csv.gz'):
        node_ids[r['id']] = [f'lccn:{x}' for x in r['lccns'].split(';') if x] + [x for x in r['alias_ids'].split(';') if x]
    out = {}
    for r in rd(CITED / 'editions.csv.gz'):
        a = r['cited_as']
        if a.startswith('corpus:') or not r['canonical'] or a == r['canonical']:
            continue
        for x in [a] + node_ids.get(a, []):
            if x != r['canonical']:
                out.setdefault(x, set()).add((r['canonical'], r['relation'], r['route']))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--src', type=Path, default=SRC)
    ap.add_argument('--out', type=Path, default=OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {'files': {}}
    c = Counter()
    jworks = {r['id']: r for r in rd(args.src / 'works.csv.gz')}
    canon_of = edition_index()
    cites, epairs = [], {}
    for r in rd(args.src / 'crosswalk.csv.gz'):
        if r['citing_work'] == r['cited_work']:
            c['self_dropped'] += 1
            continue
        b = r['cited_work']
        ids = [b] + [x for x in (jworks.get(b, {}).get('identifiers') or '').split(';') if x]
        hit = set().union(*(canon_of.get(x, set()) for x in ids))
        cans = {h[0] for h in hit}
        if len(cans) == 1 and not cans & {b, r['citing_work']}:
            can = cans.pop()
            e = epairs.setdefault((r['citing_work'], can), dict(rel=set(), route=set(), cited_as=set(), n=0))
            e['rel'].update(h[1] for h in hit)
            e['route'].update(h[2] for h in hit)
            e['cited_as'].add(b)
            e['n'] += int(r['citations'] or 0)
            c[f"edition_moved|{r['source']}"] += 1
            continue
        if len(cans) > 1:
            c['edition_several_canonicals_not_moved'] += 1
        c[f"cites|{r['source']}"] += 1
        cites.append((r['citing_work'], b, r['source'], r['basis'], r['citations'], ''))
    c['edition_pairs'] = len(epairs)
    c['edition_pairs_also_cited_directly'] = len(epairs.keys() & {(a, b) for a, b, *_ in cites})
    cites += [(a, b, ';'.join(sorted(e['rel'])), ';'.join(sorted(e['route'])), str(e['n']), ';'.join(sorted(e['cited_as'])))
              for (a, b), e in epairs.items()]
    cites.sort()
    write_csv(args.out / 'cites.csv.gz', ['citing_work', 'cited_work', 'source', 'basis', 'citations', 'cited_as'], cites,
              report)
    wanted = {b for _, b, *_ in cites} | {x for *_, ca in cites for x in ca.split(';') if x}   # edition nodes stay
    works = []
    for r in jworks.values():
        c[f"works|{r['held_by']}"] += 1
        if r['held_by'] == 'key' or r['id'] not in wanted:
            continue
        uri = r['lc_author_uri'] or ''
        lc = uri.rstrip('/').rsplit('/', 1)[-1] if '/authorities/names/' in uri else ''
        works.append((r['id'], r['catalogue_title'], r['year'], r['kind'], r['container'], r['identifiers'], r['source'],
                      r['basis'], lc, r['citing_articles']))
    works.sort()
    write_csv(args.out / 'works.csv.gz', ['id', 'title', 'year', 'kind', 'container', 'identifiers', 'source', 'basis',
                                          'lc_author', 'citing_articles'], works, report)
    report['counts'] = dict(sorted(c.items()))
    report['note'] = ('from data/identifiers/jstor-cited-works-2026-11-11 (scripts/key_jstor_cited_works_full.py); the '
                      'build loads cites as CITES source jstor-matched and works as unkeyed Work nodes unless the key log '
                      'or data/graph/cited-works holds one of their identifiers; rows with cited_as are citations of a '
                      'translation or later edition moved to the canonical work (data/graph/cited-works/editions.csv.gz), '
                      'as the thesis side')
    (args.out / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
