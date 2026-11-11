"""Cited articles -> Crossref journal articles, from the per-journal Crossref harvest on disk (2026-11-10).
Writes a standalone crosswalk; touches neither the key log nor the graph.

Corpus: dissertation-citations works.csv, works of kind article or chapter that no crosswalk holds yet: neither the
earlier crosswalks (the match flag `m` of the `--works` table) nor the OpenAlex one of 2026-11-10 (`--openalex`).
Candidates: the Crossref harvest (/mnt/e/crossref-refs-2026-11-08/journal_*.jsonl.gz, read only; journal articles
with deposited references, published 2000 on, plus CSSH 1900-1999), condensed by `index` into Parquet files of
DOI, title keys, year, type, author family names, journal and ISSN; the reference lists are skipped.

The rules are those of scripts/key_cited_works_openalex.py (imported, not copied: author family + title key + year
within one; generic main titles never match alone; no-year matches need the journal to agree and six words; short
titles need the container; dashes normalised before the title key; titles that read as book reviews are dropped;
several records collapse when they share one DOI or one journal, else the journal decides, else held). The Crossref
record's journal (container-title) plays the OpenAlex source's part. Crossref has no review type, so the review-type
branch never fires; Crossref review records carry the reviewer as author, so the family test keeps them out.

    python3 scripts/key_cited_works_crossref.py index  --scratch <dir>
    python3 scripts/key_cited_works_crossref.py match  --scratch <dir> --works <w.parquet> \\
        --openalex data/identifiers/cited-works-openalex-2026-11-10 --out data/identifiers/cited-works-crossref-2026-11-10
    python3 scripts/key_cited_works_crossref.py agree  --scratch <dir> --works <w.parquet> \\
        --openalex data/identifiers/cited-works-openalex-2026-11-10 --out data/identifiers/cited-works-crossref-2026-11-10
"""
import argparse
import csv
import glob
import gzip
import html
import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import key_cited_works_openalex as oa  # noqa: E402
from key_cited_works_openalex import title_key, fams, judge, candidates, load_corpus, db_connect, band  # noqa: E402

HARVEST = '/mnt/e/crossref-refs-2026-11-08'
GROUPS = 64
TAG = re.compile(r'<[^>]+>')
# Crossref types a cited article can be; journal issues, peer reviews, components and datasets cannot
CR_TYPES = ('journal-article', 'proceedings-article', 'book-chapter', 'other', 'posted-content', 'report',
            'reference-entry', 'monograph', 'book')
NOT_ARTICLE = ('monograph', 'book')       # a cited article is never a Crossref book record
# audit 2026-11-10: 'Building the Internationalist City from Below' (Leupold, ILWCH 2021) took the journal's ADDENDUM
# notice, whose title quotes the article's; notices are separate Crossref records with their own DOIs
NOTICE = re.compile(r'\b(addendum|erratum|errata|corrigendum|corrigenda|correction|retraction|retracted|'
                    r'expression of concern)\b', re.I)


# Generic labels in other languages (agreement check 2026-11-10: 'Apresentação - Teoria e história da historiografia'
# took a Cadernos Pagu 'Apresentação'). Added to the OpenAlex matcher's set at run time; that script is not edited.
oa.GENERIC |= {'apresentacao', 'presentation', 'presentacion', 'presentazione', 'introducao', 'introduccion',
               'introduzione', 'einleitung', 'einfuhrung', 'vorwort', 'avant propos', 'prefacio', 'prefazione',
               'editorial', 'editorial introduction', 'conclusao', 'conclusion generale', 'conclusiones',
               'nota', 'notas', 'resenha', 'resena', 'compte rendu', 'comptes rendus', 'entrevista', 'interview',
               'debat', 'debate', 'dossier', 'liminaire', 'en guise de conclusion', 'postface'}
PART = re.compile(r'\b(?:part|partie|parte|teil|pt)\.?\s*([0-9]+|[ivx]+)\b|\(\s*([0-9]|[ivx]+)\s*\)\s*$', re.I)


def part_of(title):
    """'... Part 2', '... Partie II', '... (I)' -> '2' / 'ii' / 'i' (title keys stop at ten words, so parts 1 and 2 of
    one article share their keys: Ross, MIH 2021; Kahn and Perkins, Ambix, agreement check 2026-11-10)."""
    m = PART.search(title or '')
    if not m:
        return None
    p = (m.group(1) or m.group(2)).lower()
    return {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6'}.get(p, p)


def abbrev_agrees(c, s):
    """'Top Cogn Sci' ~ 'Topics in Cognitive Science'; 'EcHR' ~ 'Economic History Review' (one short token whose
    letters run in order through the journal's, from its first letter; 'Isis' is not 'CHANCE')."""
    a, b = title_key(c).split(), title_key(s).split()
    if len(a) == 1 and len(a[0]) <= 6:
        letters = ''.join(b)
        if not letters or letters[0] != a[0][0]:
            return False
        it = iter(letters)
        return all(ch in it for ch in a[0])
    i = 0
    for t in a:
        while i < len(b) and not b[i].startswith(t):
            i += 1
        if i == len(b):
            return False
        i += 1
    return bool(a)


def other_venue(c, r):
    """The record sits in another journal than the corpus container AND in another year: a reprint, the journal version
    of a cited working paper or chapter, or another piece (agreement check 2026-11-10: Troen, JAH 1999, took the Israel
    Studies 2000 reprint; Hankins, Isis 1999, took CHANCE 2000)."""
    if not c['container'] or c['year'] is None or r['year'] is None or r['year'] == c['year']:
        return False
    return not (oa.container_agrees(c['container'], r['source'] or '') or abbrev_agrees(c['container'], r['source'] or ''))


def year_of(d):
    for k in ('issued', 'published-print', 'published-online'):
        try:
            return int(d[k]['date-parts'][0][0])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return None


def index_group(args):
    gi, files, outdir, rebuild = args
    import orjson
    import pyarrow as pa
    import pyarrow.parquet as pq
    out = Path(outdir) / f'g{gi:03d}.parquet'
    if out.exists() and not rebuild:
        return gi, -1
    cols = {k: [] for k in ('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'fams', 'source', 'issn', 'file')}
    seq = gi * 10_000_000
    for path in files:
        with gzip.open(path, 'rb') as fh:
            for line in fh:
                d = orjson.loads(line)
                ts = d.get('title') or []
                t = html.unescape(TAG.sub('', ts[0] if ts else '')).strip()   # '&amp;': 30k titles, 219k journals
                t = re.sub(r'\s+', ' ', t)
                if not t or not d.get('DOI'):
                    continue
                fs = set()
                for au in (d.get('author') or [])[:6]:
                    fam = html.unescape(au.get('family') or au.get('name') or '')
                    fs |= fams(fam)
                    k = title_key(fam)
                    if k:
                        fs.add(k)
                seq += 1
                ct = d.get('container-title') or []
                cols['id'].append(seq)
                cols['doi'].append(d['DOI'].lower())
                cols['title'].append(t[:400])
                cols['main'].append(title_key(t.split(':')[0]))
                cols['whole'].append(title_key(t))
                cols['year'].append(year_of(d))
                cols['type'].append(d.get('type'))
                cols['fams'].append(sorted(fs))
                cols['source'].append(html.unescape(ct[0] if ct else '')[:200] or None)
                cols['issn'].append('|'.join(d.get('ISSN') or []) or None)
                cols['file'].append(Path(path).name.split('.')[0])
    tab = pa.table({k: (pa.array(v, pa.int16()) if k == 'year' else pa.array(v)) for k, v in cols.items()})
    tmp = out.with_suffix('.part')
    pq.write_table(tab, tmp, compression='zstd')
    tmp.rename(out)
    return gi, tab.num_rows


def cmd_index(a):
    outdir = Path(a.scratch) / 'index'
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f'{HARVEST}/journal_*.jsonl.gz'))
    groups = [(i, files[i::GROUPS], str(outdir), a.rebuild) for i in range(GROUPS)]
    total = 0
    with Pool(a.procs) as pool:
        for gi, n in pool.imap_unordered(index_group, groups):
            total += max(n, 0)
            print('group', gi, n, total, flush=True)


# ---------------------------------------------------------------- matching

def flag_tables(db, a):
    """w0: the works table with m_oa (OpenAlex crosswalk) and the after-OpenAlex flag m1 = m OR m_oa."""
    oax = Path(a.openalex) / 'crosswalk.csv.gz'
    db.execute(f"""CREATE OR REPLACE TEMP TABLE oax AS SELECT work_id, nullif(lower(doi), '') AS doi
                   FROM read_csv('{oax}', all_varchar=true)""")
    db.execute(f"""CREATE OR REPLACE TEMP TABLE w0 AS SELECT w.*, oax.work_id IS NOT NULL AS m_oa, oax.doi AS oa_doi,
                   (m OR oax.work_id IS NOT NULL) AS m1 FROM read_parquet('{a.works}') w LEFT JOIN oax USING (work_id)""")


def scope_parquet(db, scratch, cond, name):
    """A work table shaped for oa.load_corpus (which takes the works with NOT m, has_author, kind article/chapter or
    book >= 2017): m is rewritten so only the works meeting `cond` (articles/chapters) stay open."""
    p = Path(scratch) / name
    db.execute(f"""COPY (SELECT work_id, n, kind, yr, has_author, br, ca, gb, us, ot,
                   NOT ({cond} AND kind IN ('article', 'chapter')) AS m FROM w0) TO '{p}' (FORMAT parquet)""")
    return str(p)


def run_match(db, a, works_parquet):
    corpus = load_corpus(db, works_parquet)
    print('corpus works in scope', len(corpus), flush=True)
    cands = candidates(db, a.scratch, CR_TYPES, ('article', 'chapter'), 'x')
    print('works with candidates', len(cands), flush=True)
    results, held = {}, []
    for w, cs in cands.items():
        t = corpus[w]['title'] or ''
        cs = [r for r in cs if r['type'] not in NOT_ARTICLE
              and not (NOTICE.search(r['title'] or '') and not NOTICE.search(t))]
        if not cs:
            continue
        c = corpus[w]
        cp = part_of(t)
        cs = [r for r in cs if not (cp and part_of(r['title']) and part_of(r['title']) != cp)]
        if not cs:
            continue
        j = judge(c, cs, False)
        if not j:
            continue
        if j[0] == 'match' and other_venue(c, j[1]):
            j = ('held', 'other_venue_other_year', len(cs))
        a_, b_ = c['whole'] + ' ', (j[1]['whole'] + ' ') if j[0] == 'match' else ''
        if j[0] == 'match' and c['year'] is None and not (a_.startswith(b_) or b_.startswith(a_)):
            # audit 2026-11-10: without a year, a shared main title under two different subtitles ('Contexts for
            # cruciforms: the figurines of Chalcolithic Cyprus' / '...: figurines of prehistoric Cyprus') is held;
            # a record whose title is the start of the other's (Crossref often drops the subtitle; corpus subtitles
            # after a full stop) still matches
            j = ('held', 'no_year_subtitles_differ', len(cs))
        if j[0] == 'match':
            results[w] = (j[1], j[2])
        else:
            held.append((w, corpus[w]['kind'], j[1], j[2], corpus[w]['n']))
    return corpus, results, held


def cmd_match(a):
    db = db_connect(a.scratch)
    flag_tables(db, a)
    wp = scope_parquet(db, a.scratch, 'NOT m1', 'scope-after-oa.parquet')
    corpus, results, held = run_match(db, a, wp)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out / 'crosswalk.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'doi', 'cr_title', 'cr_year', 'cr_type', 'cr_journal', 'basis', 'cited_by_dissertations'])
        for w, (r, basis) in sorted(results.items()):
            wr.writerow([w, r['doi'], r['title'], r['year'], r['type'], r['source'] or '', basis, corpus[w]['n']])
    with gzip.open(out / 'held.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'kind', 'reason', 'candidates', 'cited_by_dissertations'])
        wr.writerows(sorted(held, key=lambda x: -x[4]))
    report(db, a, corpus, results, held, out)


def report(db, a, corpus, results, held, out):
    import pyarrow as pa
    db.register('new_arrow', pa.table({'work_id': list(results), 'basis': [b for _, b in results.values()],
                                       'journal': [r['source'] or '' for r, _ in results.values()]}))
    db.execute("CREATE OR REPLACE TEMP TABLE new AS SELECT * FROM new_arrow")
    db.execute("""CREATE OR REPLACE TEMP TABLE ww AS SELECT w.*, new.basis, new.journal, new.work_id IS NOT NULL AS newm,
        CASE WHEN greatest(br, ca, gb, us, ot) = 0 THEN 'none'
             WHEN br = greatest(br, ca, gb, us, ot) THEN 'BR' WHEN ca = greatest(br, ca, gb, us, ot) THEN 'CA'
             WHEN gb = greatest(br, ca, gb, us, ot) THEN 'GB' WHEN us = greatest(br, ca, gb, us, ot) THEN 'US'
             ELSE 'other' END AS country
        FROM w0 w LEFT JOIN new USING (work_id)""")

    def rates(group, where='true'):
        rows = db.execute(f"""SELECT {group} AS g, count(*) works, sum(n) cites,
                sum(n) FILTER (WHERE m1) before_cites, sum(n) FILTER (WHERE m1 OR newm) after_cites,
                count(*) FILTER (WHERE newm) new_works, sum(n) FILTER (WHERE newm) new_cites
                FROM ww WHERE {where} GROUP BY 1 ORDER BY 3 DESC""").fetchall()
        return {str(g): dict(works=wk, citations=int(c), before=int(b or 0), after=int(af or 0),
                             before_rate=round((b or 0) / c, 4) if c else None,
                             after_rate=round((af or 0) / c, 4) if c else None,
                             new_works=nw, new_citations=int(nc or 0)) for g, wk, c, b, af, nw, nc in rows}

    art = "kind = 'article'"
    scope = "kind IN ('article', 'chapter')"
    rep = {
        'note': ('citations = sum of citing theses (strict) per work; before = matched by the earlier crosswalks or '
                 'the OpenAlex crosswalk of 2026-11-10 (after OpenAlex); after = before or this Crossref crosswalk'),
        'overall': rates("'all'")['all'],
        'by_kind': rates('kind'),
        'articles_by_citing_band': rates("CASE WHEN n = 1 THEN '1' WHEN n < 5 THEN '2-4' WHEN n < 10 THEN '5-9' "
                                         "ELSE '10+' END", art),
        'articles_by_year_band': rates("CASE WHEN yr IS NULL THEN 'unknown' WHEN yr < 1950 THEN 'pre-1950' "
                                       "WHEN yr < 2020 THEN (yr // 10 * 10)::varchar || 's' ELSE '2020s' END", art),
        'articles_by_dominant_country': rates('country', art),
        'chapters_by_citing_band': rates("CASE WHEN n = 1 THEN '1' WHEN n < 5 THEN '2-4' WHEN n < 10 THEN '5-9' "
                                         "ELSE '10+' END", "kind = 'chapter'"),
        'in_scope_by_dominant_country': rates('country', scope),
        'matches_by_basis': {str(b): dict(works=w, citations=int(c)) for b, w, c in db.execute(
            "SELECT basis, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 2 DESC").fetchall()},
        'matches_by_basis_and_kind': {f'{b} / {k}': dict(works=w, citations=int(c)) for b, k, w, c in db.execute(
            "SELECT basis, kind, count(*), sum(n) FROM ww WHERE newm GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()},
        'top_journals_by_citations_gained': [dict(journal=j, works=w, citations=int(c)) for j, w, c in db.execute(
            "SELECT journal, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 3 DESC, 2 DESC LIMIT 40").fetchall()],
        'held': {},
    }
    for w, k, reason, nc, n in held:
        d = rep['held'].setdefault(f'{k} / {reason}', dict(works=0, citations=0))
        d['works'] += 1
        d['citations'] += n
    (out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


def cmd_agree(a):
    """Agreement with OpenAlex: the matcher run on the article/chapter works the OpenAlex crosswalk matched with a DOI
    (and the earlier crosswalks did not). Writes agreement.json and agreement-different.csv.gz."""
    db = db_connect(a.scratch)
    flag_tables(db, a)
    wp = scope_parquet(db, a.scratch, 'NOT m AND m_oa AND oa_doi IS NOT NULL', 'scope-oa-doi.parquet')
    corpus, results, held = run_match(db, a, wp)
    oad = dict(db.execute("SELECT work_id, oa_doi FROM w0 WHERE NOT m AND m_oa AND oa_doi IS NOT NULL "
                          "AND kind IN ('article', 'chapter') AND has_author").fetchall())
    idx = f"{a.scratch}/index/*.parquet"
    in_harvest = {d for d, in db.execute(f"""SELECT DISTINCT i.doi FROM read_parquet('{idx}') i
                  WHERE i.doi IN (SELECT oa_doi FROM w0 WHERE m_oa)""").fetchall()}
    heldw = {w for w, *_ in held}
    tally, diff = {}, []
    for w, d in oad.items():
        if w in results:
            r, basis = results[w]
            k = 'same_doi' if r['doi'] == d else 'different_doi'
            if k == 'different_doi':
                diff.append((w, d, r['doi'], r['title'], r['year'], r['source'], basis, corpus[w]['title'],
                             corpus[w]['year'], corpus[w]['container'], corpus[w]['authors'], corpus[w]['n']))
        elif w in heldw:
            k = 'held'
        else:
            k = 'nothing'
        k += '|oa_doi_in_harvest' if d in in_harvest else '|oa_doi_not_in_harvest'
        tally[k] = tally.get(k, 0) + 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'agreement.json').write_text(json.dumps(dict(works=len(oad), tally=dict(sorted(tally.items()))), indent=1)
                                        + '\n')
    with gzip.open(out / 'agreement-different.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'oa_doi', 'cr_doi', 'cr_title', 'cr_year', 'cr_journal', 'basis', 'title', 'year',
                     'container', 'authors', 'cited_by_dissertations'])
        wr.writerows(diff)
    print(json.dumps(tally, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('index')
    p.add_argument('--scratch', required=True)
    p.add_argument('--procs', type=int, default=3)
    p.add_argument('--rebuild', action='store_true', help='rewrite group files that exist (each replaced by rename)')
    for name in ('match', 'agree'):
        p = sub.add_parser(name)
        p.add_argument('--scratch', required=True)
        p.add_argument('--works', required=True, help='work table with a match flag (work_id, n, kind, yr, has_author, '
                                                     'br, ca, gb, us, ot, m)')
        p.add_argument('--openalex', required=True, help='folder of the OpenAlex crosswalk (crosswalk.csv.gz)')
        p.add_argument('--out', required=True)
    a = ap.parse_args()
    {'index': cmd_index, 'match': cmd_match, 'agree': cmd_agree}[a.cmd](a)


if __name__ == '__main__':
    main()
