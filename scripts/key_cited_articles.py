"""Cited articles and chapters -> DOI works in the key log, with their keyed authors (2026-11-03). Writes a proposal.

Candidates for every cited article or chapter with a keyed author (corpus works.csv): JSTOR's records (the local
metadata export, indexed by scripts/jstor_index.py; user, 2026-11-03: "we have jstor data locally") and, where
asked, Crossref's answers (crossref_cited_articles.py, for journals JSTOR does not hold). A cited work is the
record when
- the titles agree: the main titles (before the first colon) are equal once normalised (key_lc_works.title_key),
  or the whole titles are, or one whole title is the other's main title;
- the record's authors include the family name of every keyed author the corpus lists for it;
- the years agree within two (the corpus's year is the cited edition's; online-first and print differ);
- the record is an article or chapter-like type (journal-article, book-chapter, proceedings-article, ...),
  and not a review (Crossref files book reviews under the book's title: the AHA-minted lesson);
- the records passing are one article: same container and year (JSTOR's 10.2307 DOI beside the publisher's
  becomes a second anchor of the work; the publisher's DOI leads).
Then the DOI becomes a work (`doi:<doi>`, lower case; member `year:`), unless a key already holds it, and each
keyed author (the key holding `diss-person:<id>` for an author the corpus lists) gets an `authored` claim
(`cited-authored:<doi>:<person id>`, recorded). Writes crosswalk.csv.gz (work_id, key) for export_citations,
beside the book crosswalk.

    python3 scripts/key_cited_articles.py --out data/identifiers/cited-articles-2026-11-03 \\
        [--jstor /mnt/e/jstor-index.parquet] [--cache /mnt/e/crossref-cited]
"""
import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_cited_works import family_of
from key_lc_works import title_key

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
TYPES = {'journal-article', 'book-chapter', 'proceedings-article', 'book-section', 'book-part', 'reference-entry',
         'posted-content', 'other'}
REVIEW = ('review of', 'book review', 'reviews', 'review:', 'compte rendu', 'resena', 'reseña', 'rezension')


def titles_agree(a, b):
    """Main titles equal, or whole titles, or one whole title is the other's main title."""
    ma, mb = title_key(a.split(':')[0]), title_key(b.split(':')[0])
    wa, wb = title_key(a), title_key(b)
    if not (ma and mb) or len(ma.split()) < 2 and wa != wb:
        return wa == wb and bool(wa)
    return ma == mb or wa == wb or wa == mb or ma == wb


def year_of(item):
    parts = (item.get('issued') or {}).get('date-parts') or [[None]]
    return parts[0][0] if parts and parts[0] else None


def jstor_candidates(index, works, families):
    """work id -> candidate records from the JSTOR index sharing a title key (main or whole title, two words or
    more) and a keyed author's family name, years within two. Joining on title and family together keeps generic
    titles ('Introduction') from pairing every chapter with every other."""
    import pyarrow as pa
    db = duckdb.connect()
    db.execute("SET memory_limit = '4GB'")
    db.execute("SET temp_directory = '/mnt/e/duckdb-tmp'")
    db.execute("SET preserve_insertion_order = false")
    cols = defaultdict(list)
    for w, (_, _, t, y, *_) in works.items():
        keys = {title_key((t or '').split(':')[0]), title_key(t or '')}
        for k in keys:
            if len(k.split()) < 2:
                continue
            for f in families.get(w, ()):
                cols['w'].append(w); cols['k'].append(k); cols['f'].append(f)
                cols['y'].append(int(y) if (y or '').isdigit() else None)
    db.register('cw', pa.table({'w': cols['w'], 'k': cols['k'], 'f': cols['f'], 'y': pa.array(cols['y'], pa.int32())}))
    db.execute("CREATE TABLE ks AS SELECT DISTINCT k FROM cw")
    db.execute(f"""CREATE TABLE j AS SELECT doi, kind, title, year, container, families, main, whole
                   FROM read_parquet('{index}') WHERE kind IN ('article', 'chapter')
                     AND (main IN (SELECT k FROM ks) OR whole IN (SELECT k FROM ks))""")
    db.execute("CREATE TABLE jk AS SELECT doi, main AS k, unnest(families) AS f, year FROM j WHERE main <> '' "
               "UNION SELECT doi, whole, unnest(families), year FROM j WHERE whole <> ''")
    out = defaultdict(list)
    for w, doi, kind, title, year, container, fams in db.execute("""
            SELECT DISTINCT cw.w, j.doi, j.kind, j.title, j.year, j.container, j.families
            FROM cw JOIN jk ON jk.k = cw.k AND jk.f = cw.f JOIN j ON j.doi = jk.doi
            WHERE cw.y IS NULL OR j.year IS NULL OR abs(j.year - cw.y) <= 2""").fetchall():
        out[w].append(dict(doi=doi, title=title, year=year, container=title_key(container or ''), families=set(fams),
                           source='JSTOR'))
    return out


def crossref_candidates(cache):
    out = defaultdict(list)
    path = cache / 'answers.jsonl'
    if not path.exists():
        return out
    with path.open(encoding='utf-8') as f:
        for l in f:
            if not l.strip():
                continue
            a = json.loads(l)
            for it in a['items']:
                t = ' '.join((it.get('title') or [''])[:1] + [': ' + x for x in (it.get('subtitle') or [])[:1]])
                if it.get('type') not in TYPES or not t:
                    continue
                out[a['work_id']].append(dict(
                    doi=it['DOI'].lower(), title=t, year=year_of(it),
                    container=title_key((it.get('container-title') or [''])[0]), source='Crossref',
                    families={family_of(x.get('family') or x.get('name') or '') for x in it.get('author') or []}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--jstor', type=Path, default=Path('/mnt/e/jstor-index.parquet'))
    ap.add_argument('--cache', type=Path, default=Path('/mnt/e/crossref-cited'))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    from crossref_cited_articles import wanted
    works = {r[0]: r for r in wanted(1)}
    db = duckdb.connect()
    db.execute('CREATE TABLE want(w VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(w,) for w in works])
    authors = defaultdict(list)
    for p, w in db.execute(f"SELECT person_key, work_id FROM read_csv('{CORPUS}/authored.csv.gz') WHERE work_id IN (SELECT w FROM want)").fetchall():
        authors[w].append(p)
    keyed_ids = {r[0] for r in duckdb.sql(f"""SELECT DISTINCT substr(a, 13) FROM (SELECT unnest(anchors) AS a
                 FROM '{ROOT / "build/graph/person.parquet"}') WHERE a LIKE 'diss-person:%'""").fetchall()}
    families = {w: {family_of(p.split('|')[0]) for p in ps if p in keyed_ids} for w, ps in authors.items()}
    candidates = jstor_candidates(args.jstor, works, families)     # before the key log is loaded: memory
    state = State.load(args.state)
    for w, items in crossref_candidates(args.cache).items():
        candidates[w] += items
    report, rows, found, also = Counter(works=len(works)), [], {}, defaultdict(set)
    for w in sorted(works):
        _, kind, title, year, container, _, _ = works[w]
        keyed = [p for p in authors[w] if f'diss-person:{p}' in state.anchor]
        if not keyed:
            report['no_keyed_author'] += 1
            continue
        fams = {family_of(p.split('|')[0]) for p in keyed}
        y = int(year) if (year or '').isdigit() else None
        passing = []
        for it in candidates.get(w, ()):
            t = it['title']
            if t.lower().startswith(REVIEW) or not titles_agree(title or '', t) or not fams <= it['families']:
                continue
            if y and it['year'] and abs(it['year'] - y) > 2:
                continue
            passing.append((it['doi'], t, it['year'], it['container'], it['source']))
        groups = {(c, iy) for _, _, iy, c, _ in passing}
        if len(groups) != 1:
            report['several_records' if groups else 'no_record'] += 1
            continue
        # one article under several DOIs (JSTOR's 10.2307 and the publisher's): one work, the publisher's first
        dois = sorted({d for d, *_ in passing}, key=lambda d: (d.startswith('10.2307/'), d))
        doi, t, iy = dois[0], passing[0][1], passing[0][2]
        found.setdefault(doi, []).append((w, t, iy, keyed, sorted({x[4] for x in passing})))
        also[doi] |= set(dois[1:])
        report[f'matched_{kind}'] += 1
        report[f'matched_via_{"+".join(sorted({x[4] for x in passing}))}'] += 1
    # Leads sharing a DOI (two cited forms of one article, each found with the publisher's DOI and JSTOR's)
    # are one work.
    parent = {d: d for d in found}

    def root(d):
        while parent[d] != d:
            parent[d] = parent[parent[d]]
            d = parent[d]
        return d
    owner = {}
    for d in sorted(found):
        for x in sorted({d} | also[d]):
            if x in owner:
                parent[root(d)] = root(owner[x])
            else:
                owner[x] = d
        if f'doi:{d}' in state.anchor:
            k = state.anchor[f'doi:{d}']
            owner.setdefault(k, d)
            parent[root(d)] = root(owner[k])
        for x in also[d]:
            k = state.anchor.get(f'doi:{x}')
            if k:
                if k in owner:
                    parent[root(d)] = root(owner[k])
                else:
                    owner[k] = d
    merged = defaultdict(list)
    for d in sorted(found):
        merged[root(d)].append(d)
    found2, also2 = {}, defaultdict(set)
    for r, ds in merged.items():
        lead = sorted(ds, key=lambda d: (d.startswith('10.2307/'), d))[0]
        found2[lead] = [h for d in ds for h in found[d]]
        also2[lead] = (set(ds) | set().union(*(also[d] for d in ds))) - {lead}
    found, also = found2, also2
    clusters, claims = [], []
    for doi, hits in sorted(found.items()):
        w0, t, iy, _, src = hits[0]
        clusters.append(dict(type='work', label=t[:250], anchors={f'doi:{d}' for d in {doi} | also[doi]}, members={f'year:{iy}'} if iy else set(),
                             aliases=set(), resolution='established', basis=f'{" and ".join(src)} record of a cited work ({w0})'))
        for p in sorted({p for _, _, _, keyed, _ in hits for p in keyed}):
            c = f'cited-authored:{doi}:{p}'
            if c not in state.anchor:
                claims.append(dict(anchor=c, subject=f'diss-person:{p}', object=f'doi:{doi}'))
        rows += [(w, doi) for w, *_ in hits]
    ops, assign, held = plan(state, clusters)
    for i, c in enumerate(claims):
        ops.append(dict(event='mint', key=f'new:claim-{i}', type='claim', label='', resolution='recorded', anchors=[c['anchor']],
                        relation=dict(subject=c['subject'], predicate='authored', object=c['object']),
                        basis='author of the cited work, as the corpus lists it and the JSTOR or Crossref record agrees'))
    materialise(state, dict(basis='cited articles', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='cited articles and chapters matched to their JSTOR or Crossref records (title, keyed authors, year)', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    with gzip.open(args.out / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'key'])
        wr.writerows((w, f'doi:{doi}') for w, doi in rows)
    summary = dict(**dict(sorted(report.items())), dois=len(found),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
