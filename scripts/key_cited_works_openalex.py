"""Cited articles, chapters and recent books -> OpenAlex works, from the OpenAlex History harvest on disk (2026-11-10).
Writes a standalone crosswalk; touches neither the key log nor the graph.

Corpus: dissertation-citations works.csv, the works no crosswalk holds yet (a work table with a match flag, `--works`),
of kind article or chapter, and books whose cited year is 2017 or later (older books go to the Library of Congress
route). Candidates: the harvest (/mnt/e/openalex-history-2026-11-08/history/*.jsonl.gz, read only), condensed by
`index` into a Parquet file of id, doi, title keys, year, type, author family names and source name.

A cited work is the OpenAlex record when
- an author family name agrees (the corpus's family, `key_cited_works.family_of`, against the record's display and raw
  author names: last word, last two words, or the part before a comma);
- the titles agree (`key_lc_works.title_key`): whole titles equal (basis `whole_title`), or main titles (before the
  first colon) equal, or one whole title is the other's main title (basis `main_title`). The work id's own title (the
  original-language form where the corpus keyed a translation) counts as a main title;
- the years agree within one; a missing corpus year only when the whole title runs to six words or more and the record
  is the only candidate and its source agrees with the corpus container (basis `no_year_long_title_container`);
- the record's type fits: articles and chapters against article / book-chapter / review / conference-paper / preprint
  (and book-review on the whole title with the container agreeing: OpenAlex mistypes some articles),
  books against book (OpenAlex files monographs and edited books as `book`). Titles that read as book reviews are
  dropped;
- titles of fewer than three words, or generic ones (Introduction, Preface, Conclusion ...), match only when the
  corpus container agrees with the record's source (basis `short_title_container`), and are held otherwise;
- several passing records collapse to one when they carry at most one distinct DOI (OpenAlex's DOI-less duplicates,
  preprints) or share a source; otherwise a record whose source agrees with the corpus container wins (basis suffix
  `+container_tiebreak`); otherwise the work is held.

Second, separate basis for chapters still unmatched: the containing volume (works.csv container) as an OpenAlex book,
whole or main title of four words or more, year within one, one candidate (`volume_title_year`; `+author` when a
chapter author is among the book's listed authors/editors). Written to chapter-volumes.csv.gz: citing a chapter is not
citing the volume.

    python3 scripts/key_cited_works_openalex.py index  --scratch <dir>
    python3 scripts/key_cited_works_openalex.py match  --scratch <dir> --works <w.parquet> \\
        --out data/identifiers/cited-works-openalex-2026-11-10
"""
import argparse
import csv
import glob
import gzip
import json
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from key_cited_works import family_of  # noqa: E402
from key_lc_works import title_key as _title_key  # noqa: E402

# key_lc_works.title_key drops non-ASCII punctuation outright, so OpenAlex's '1662–1684' (en dash) became '16621684'
# while the corpus's '1662-1684' became '1662 1684' (Glickman, JMH 2015, missed in the first run). Dashes, non-breaking
# spaces and the like become their ASCII forms first, on both sides.
_PUNCT = re.compile(r'[\u2010-\u2015\u2212\u2043\uFE58\uFE63\uFF0D\u00A0\u2000-\u200B\u202F\u205F\u3000/\u2044\u00B7\u2022\u2026]')


def title_key(t):
    return _title_key(_PUNCT.sub(' ', t or ''))

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
HARVEST = '/mnt/e/openalex-history-2026-11-08/history'
ART_TYPES = ('article', 'book-chapter', 'review', 'conference-paper', 'preprint', 'other', 'book-review')
# OpenAlex files some research articles as `book-review` (Hoganson, AHR 2002; Leneman and Mitchison, JSH 1988): such a
# record is taken only on the whole title with the corpus container agreeing (basis suffix `+oa_typed_review`)
BOOK_TYPES = ('book',)
GENERIC = {'introduction', 'preface', 'foreword', 'conclusion', 'conclusions', 'afterword', 'epilogue', 'prologue',
           'editorial', 'review', 'reviews', 'book review', 'book reviews', 'comment', 'commentary', 'response',
           'reply', 'a reply', 'rejoinder', 'notes', 'note', 'acknowledgements', 'acknowledgments', 'index',
           'bibliography', 'overview', 'editors introduction', 'introduction and overview', 'general introduction',
           'forum', 'roundtable', 'obituary', 'in memoriam', 'discussion', 'letters', 'correspondence', 'untitled',
           'review article', 'review essay', 'essay review', 'review articles', 'book review essay', 'state of field',
           'historiographical review', 'research note', 'notes and documents', 'document', 'documents'}
REVIEW_RE = re.compile(r'(\bpp\.?\s*\d|\$\s*\d|\bisbn\b|\bpaper\b.*\d|\bcloth\b|\bxv?i*\s*\+\s*\d|^review of\b|'
                       r'^book review|^compte rendu|^resena|^reseña|^rezension)', re.I)


def fams(name):
    """Family-name variants of an OpenAlex display/raw author name."""
    out = set()
    name = (name or '').strip()
    if not name:
        return out
    if ',' in name:
        name = name.split(',')[0]                         # 'Hall, J.' -> 'Hall'
    w = title_key(name).split()
    if w:
        out.add(w[-1])
        if len(w) >= 3:
            out.add(' '.join(w[-2:]))
    out.discard('')
    return out


def index_file(args):
    path, outdir = args
    import orjson
    import pyarrow as pa
    import pyarrow.parquet as pq
    cols = {k: [] for k in ('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'fams', 'source')}
    with gzip.open(path, 'rb') as fh:
        for line in fh:
            d = orjson.loads(line)
            t = (d.get('title') or d.get('display_name') or '').strip()
            if not t:
                continue
            fs = set()
            for a in (d.get('authorships') or [])[:6]:
                fs |= fams((a.get('author') or {}).get('display_name'))
                fs |= fams(a.get('raw_author_name'))
            pl = d.get('primary_location') or {}
            src = (pl.get('source') or {}).get('display_name') or pl.get('raw_source_name') or ''
            cols['id'].append(int(d['id'].rsplit('/W', 1)[1]))
            cols['doi'].append((d.get('doi') or '').replace('https://doi.org/', '').lower() or None)
            cols['title'].append(t[:400])
            cols['main'].append(title_key(t.split(':')[0]))
            cols['whole'].append(title_key(t))
            cols['year'].append(d.get('publication_year'))
            cols['type'].append(d.get('type'))
            cols['fams'].append(sorted(fs))
            cols['source'].append(src[:200] or None)
    tab = pa.table({k: (pa.array(v, pa.int16()) if k == 'year' else pa.array(v)) for k, v in cols.items()})
    out = Path(outdir) / (Path(path).name.split('.')[0] + '.parquet')
    pq.write_table(tab, out, compression='zstd')
    return path, tab.num_rows


def cmd_index(a):
    outdir = Path(a.scratch) / 'index'
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f'{HARVEST}/*.jsonl.gz'), key=os.path.getsize, reverse=True)
    todo = [(f, str(outdir)) for f in files if not (outdir / (Path(f).name.split('.')[0] + '.parquet')).exists()]
    total = 0
    with Pool(a.procs) as pool:
        for p, n in pool.imap_unordered(index_file, todo):
            total += n
            print(Path(p).name, n, total, flush=True)


# ---------------------------------------------------------------- matching

def ckey(s):
    """Container/source key: title_key without stop words, for a loose agreement test."""
    s = re.sub(r"['’‘ʼ]", ' ', s or '')                  # "Revue d’histoire" and OpenAlex's "Revue d histoire" agree
    w = [x for x in title_key(s).split() if len(x) > 1 and x not in {
        'of', 'and', 'the', 'for', 'de', 'la', 'des', 'et', 'du', 'journal', 'revue', 'review', 'in', 'on'}]
    return ' '.join(w)


def container_agrees(c, s):
    a, b = ckey(c), ckey(s)
    if not a or not b:
        return False
    return a == b or (min(len(a), len(b)) >= 5 and (a in b or b in a))


def db_connect(scratch):
    import duckdb
    tmp = Path(scratch) / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB'")
    db.execute(f"SET temp_directory='{tmp}'; SET preserve_insertion_order=false")
    return db


def load_corpus(db, works_parquet):
    """Unmatched works in scope, with authors/title/year/container from works.csv."""
    import pyarrow as pa
    db.execute(f"""CREATE TEMP TABLE scope AS SELECT work_id, n, kind, yr, br, ca, gb, us, ot FROM read_parquet('{works_parquet}')
                   WHERE NOT m AND has_author AND (kind IN ('article', 'chapter') OR (kind = 'book' AND yr >= 2017))""")
    rows = db.execute(f"""SELECT s.work_id, s.kind, s.n, w.authors, w.title, w.year, w.container
        FROM scope s JOIN read_csv('{CORPUS}/works.csv', all_varchar=true) w USING (work_id)""").fetchall()
    corpus, keys = {}, {'w': [], 'k': [], 'f': [], 'y': []}
    for wid, kind, n, authors, title, year, cont in rows:
        fam = set()
        for au in (authors or '').split(';'):
            f = family_of(_PUNCT.sub(' ', au)) if au.strip() else ''
            if f:
                fam.add(f)
                fam.add(f.split()[-1])
        y = int(year) if (year or '').isdigit() else None
        main, whole = title_key((title or '').split(':')[0]), title_key(title or '')
        widt = wid.split('|', 1)[1].rsplit('|a', 1)[0] if '|' in wid else ''
        corpus[wid] = dict(kind=kind, n=n, authors=authors, title=title, year=y, container=cont, fams=fam,
                           main=main, whole=whole, widt=widt)
        for k in {main, whole, widt} - {''}:
            for f in fam:
                keys['w'].append(wid); keys['k'].append(k); keys['f'].append(f); keys['y'].append(y)
    db.register('ck_arrow', pa.table({'w': keys['w'], 'k': keys['k'], 'f': keys['f'],
                                      'y': pa.array(keys['y'], pa.int32())}))
    db.execute("CREATE TEMP TABLE ck AS SELECT * FROM ck_arrow")
    return corpus


def candidates(db, scratch, types, kinds, out_name):
    """(work_id -> list of candidate records) for corpus works of `kinds`, OpenAlex records of `types`, sharing a title
    key and a family name, year within one (or missing corpus year)."""
    idx = f"{scratch}/index/*.parquet"
    tl = ','.join(f"'{t}'" for t in types)
    kl = ','.join(f"'{k}'" for k in kinds)
    db.execute(f"""CREATE OR REPLACE TEMP TABLE ks AS SELECT DISTINCT k FROM ck JOIN scope s ON s.work_id = ck.w
                   WHERE s.kind IN ({kl})""")
    db.execute(f"""CREATE OR REPLACE TEMP TABLE oa AS SELECT id, doi, title, main, whole, year, type, fams, source
                   FROM read_parquet('{idx}') WHERE type IN ({tl})
                   AND (main IN (SELECT k FROM ks) OR whole IN (SELECT k FROM ks))""")
    db.execute("""CREATE OR REPLACE TEMP TABLE oak AS SELECT DISTINCT id, k, f, year FROM (
                    SELECT id, main AS k, unnest(fams) AS f, year FROM oa WHERE main <> ''
                    UNION ALL SELECT id, whole AS k, unnest(fams) AS f, year FROM oa WHERE whole <> '')""")
    rows = db.execute(f"""SELECT DISTINCT ck.w, oa.id, oa.doi, oa.title, oa.main, oa.whole, oa.year, oa.type, oa.source
        FROM ck JOIN scope s ON s.work_id = ck.w AND s.kind IN ({kl})
        JOIN oak ON oak.k = ck.k AND oak.f = ck.f AND (ck.y IS NULL OR abs(oak.year - ck.y) <= 1)
        JOIN oa ON oa.id = oak.id""").fetchall()
    out = {}
    for w, *rec in rows:
        out.setdefault(w, []).append(dict(zip(('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'source'), rec)))
    return out


def title_mode(c, r):
    """A main title that is a generic label ('Review Article: ...', 'Introduction: ...') never carries a match on its
    own: only the whole title does (audit 2026-11-10: 'Review Article: Chrodegang ...' took another review article)."""
    if c['whole'] and c['whole'] == r['whole']:
        return 'whole_title'
    cm = c['main'] if c['main'] not in GENERIC else ''
    rm = r['main'] if r['main'] not in GENERIC else ''
    if (cm and cm in (rm, r['whole'])) or (c['whole'] and c['whole'] == rm) \
            or (c['widt'] and c['widt'] not in GENERIC and c['widt'] in (rm, r['whole'])):
        return 'main_title'
    return None


def judge(c, cands, book):
    """-> ('match', record, basis) | ('held', reason, n candidates) | None."""
    short = len(c['whole'].split()) < 3 or c['main'] in GENERIC or c['whole'] in GENERIC
    ok = []
    for r in cands:
        tm = title_mode(c, r)
        if not tm:
            continue
        if REVIEW_RE.search(r['title'] or '') and not REVIEW_RE.search(c['title'] or ''):
            continue
        if tm == 'main_title' and len(c['main'].split()) < 2 and c['whole'] != r['whole']:
            continue                                          # 'Introduction: ...' main titles say nothing
        cont = container_agrees(c['container'], r['source'])
        if r['type'] == 'book-review' and not (tm == 'whole_title' and cont):
            continue
        if short and not cont:
            continue
        ok.append((r, tm, cont))
    if not ok:
        short_cands = short and any(title_mode(c, r) for r in cands)
        return ('held', 'short_title_no_container', len(cands)) if short_cands else None
    if c['year'] is None:
        # audit 2026-11-10: without a year, title + family alone took a review of the cited book (Moret); the
        # container must agree as well
        if len(c['whole'].split()) < 6 or len({r['id'] for r, *_ in ok}) > 1 or not ok[0][2]:
            return ('held', 'no_year', len(ok))
    dois = {r['doi'] for r, *_ in ok if r['doi']}
    srcs = {ckey(r['source']) for r, *_ in ok}
    suffix = ''
    if len(ok) > 1 and len(dois) > 1 and len(srcs) > 1:
        agree = [x for x in ok if x[2]]
        if agree and len({r['doi'] for r, *_ in agree if r['doi']}) <= 1:
            ok, suffix = agree, '+container_tiebreak'
        else:
            return ('held', 'several_candidates', len(ok))
    # lead: whole-title agreement, container agreement, has a DOI, year closest, not a preprint
    ok.sort(key=lambda x: (x[1] != 'whole_title', not x[2], x[0]['doi'] is None,
                           abs((x[0]['year'] or 0) - (c['year'] or x[0]['year'] or 0)), x[0]['type'] in ('preprint', 'book-review'),
                           x[0]['id']))
    r, tm, cont = ok[0]
    if r['type'] == 'book-review':
        suffix += '+oa_typed_review'
    if short:
        basis = 'short_title_container'
    elif c['year'] is None:
        basis = 'no_year_long_title_container'
    else:
        basis = tm
    return ('match', r, ('book_' if book else '') + basis + suffix)


def volume_candidates(db, scratch, corpus, chapters):
    import pyarrow as pa
    ws, ks, ys = [], [], []
    for w in chapters:
        c = corpus[w]
        if not c['container']:
            continue
        for k in {title_key(c['container']), title_key(c['container'].split(':')[0])}:
            if len(k.split()) >= 4:
                ws.append(w); ks.append(k); ys.append(c['year'])
    db.register('vk_arrow', pa.table({'w': ws, 'k': ks, 'y': pa.array(ys, pa.int32())}))
    db.execute("CREATE OR REPLACE TEMP TABLE vk AS SELECT * FROM vk_arrow")
    rows = db.execute(f"""SELECT DISTINCT vk.w, o.id, o.doi, o.title, o.main, o.whole, o.year, o.type, o.source, o.fams
        FROM vk JOIN read_parquet('{scratch}/index/*.parquet') o
          ON (o.whole = vk.k OR o.main = vk.k) AND o.type = 'book' AND vk.y IS NOT NULL AND abs(o.year - vk.y) <= 1
        """).fetchall()
    out = {}
    for w, *rec in rows:
        out.setdefault(w, []).append(dict(zip(('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'source', 'fams'),
                                              rec)))
    return out


def judge_volume(c, cands):
    ck_w, ck_m = title_key(c['container']), title_key(c['container'].split(':')[0])
    ok = [r for r in cands if r['whole'] == ck_w or r['main'] == ck_m or r['whole'] == ck_m or r['main'] == ck_w]
    if not ok:
        return None
    ids = {r['id'] for r in ok}
    dois = {r['doi'] for r in ok if r['doi']}
    if len(ids) > 1 and len(dois) > 1:
        return ('held', 'volume_several_candidates', len(ok))
    ok.sort(key=lambda r: (r['whole'] != ck_w, r['doi'] is None, r['id']))
    r = ok[0]
    author = bool(c['fams'] & set(r['fams'] or ()))
    return ('match', r, 'volume_title_year' + ('+author' if author else ''))


def band(n):
    return '1' if n == 1 else '2-4' if n < 5 else '5-9' if n < 10 else '10+'


def yband(y):
    if y is None:
        return 'unknown'
    return 'pre-1950' if y < 1950 else f'{y // 10 * 10}s' if y < 2020 else '2020s'


def cmd_match(a):
    db = db_connect(a.scratch)
    corpus = load_corpus(db, a.works)
    print('corpus works in scope', len(corpus), flush=True)
    results, held = {}, []
    for kinds, types, book in ((('article', 'chapter'), ART_TYPES, False), (('book',), BOOK_TYPES, True)):
        cands = candidates(db, a.scratch, types, kinds, 'x')
        print(kinds, 'works with candidates', len(cands), flush=True)
        for w, cs in cands.items():
            j = judge(corpus[w], cs, book)
            if not j:
                continue
            if j[0] == 'match':
                results[w] = (j[1], j[2])
            else:
                held.append((w, corpus[w]['kind'], j[1], j[2], corpus[w]['n']))
    chapters = [w for w, c in corpus.items() if c['kind'] == 'chapter' and w not in results]
    vols, vheld = {}, []
    for w, cs in volume_candidates(db, a.scratch, corpus, chapters).items():
        j = judge_volume(corpus[w], cs)
        if j and j[0] == 'match':
            vols[w] = (j[1], j[2])
        elif j:
            held.append((w, 'chapter', j[1], j[2], corpus[w]['n']))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    head = ['work_id', 'openalex_id', 'doi', 'oa_title', 'oa_year', 'oa_type', 'oa_source', 'basis',
            'cited_by_dissertations']
    for name, res in (('crosswalk.csv.gz', results), ('chapter-volumes.csv.gz', vols)):
        with gzip.open(out / name, 'wt', newline='') as fh:
            wr = csv.writer(fh)
            wr.writerow(head)
            for w, (r, basis) in sorted(results_items(res, corpus)):
                wr.writerow([w, f"W{r['id']}", r['doi'] or '', r['title'], r['year'], r['type'], r['source'] or '',
                             basis, corpus[w]['n']])
    with gzip.open(out / 'held.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'kind', 'reason', 'candidates', 'cited_by_dissertations'])
        wr.writerows(sorted(held, key=lambda x: -x[4]))
    report(db, a, corpus, results, vols, held, out)


def results_items(res, corpus):
    return [(w, v) for w, v in res.items()]


def report(db, a, corpus, results, vols, held, out):
    import pyarrow as pa
    db.register('new_arrow', pa.table({'work_id': list(results), 'basis': [b for _, b in results.values()]}))
    db.execute("CREATE OR REPLACE TEMP TABLE new AS SELECT * FROM new_arrow")
    db.execute(f"""CREATE OR REPLACE TEMP TABLE ww AS SELECT w.*, new.basis, new.work_id IS NOT NULL AS newm,
        CASE WHEN greatest(br, ca, gb, us, ot) = 0 THEN 'none'
             WHEN br = greatest(br, ca, gb, us, ot) THEN 'BR' WHEN ca = greatest(br, ca, gb, us, ot) THEN 'CA'
             WHEN gb = greatest(br, ca, gb, us, ot) THEN 'GB' WHEN us = greatest(br, ca, gb, us, ot) THEN 'US'
             ELSE 'other' END AS country,
        CASE WHEN kind = 'book' AND yr >= 2017 THEN 'book_2017+' ELSE kind END AS k2
        FROM read_parquet('{a.works}') w LEFT JOIN new USING (work_id)""")

    def rates(group):
        rows = db.execute(f"""SELECT {group} AS g, count(*) works, sum(n) cites,
                sum(n) FILTER (WHERE m) before_cites, sum(n) FILTER (WHERE m OR newm) after_cites,
                count(*) FILTER (WHERE newm) new_works, sum(n) FILTER (WHERE newm) new_cites
                FROM ww GROUP BY 1 ORDER BY 3 DESC""").fetchall()
        return {str(g): dict(works=wk, citations=int(c), before=int(b or 0), after=int(af or 0),
                             before_rate=round((b or 0) / c, 4) if c else None, after_rate=round((af or 0) / c, 4) if c else None,
                             new_works=nw, new_citations=int(nc or 0)) for g, wk, c, b, af, nw, nc in rows}

    scope = "k2 IN ('article', 'chapter', 'book_2017+')"
    rep = {
        'note': 'citations = sum of citing theses (strict) per work; before = matched by existing crosswalks',
        'overall': rates("'all'")['all'],
        'by_kind': rates('k2'),
        'in_scope_by_citing_band': rates(f"CASE WHEN NOT {scope} THEN 'out of scope' WHEN n = 1 THEN '1' WHEN n < 5 THEN '2-4' "
                                         "WHEN n < 10 THEN '5-9' ELSE '10+' END"),
        'in_scope_by_year_band': rates(f"CASE WHEN NOT {scope} THEN 'out of scope' WHEN yr IS NULL THEN 'unknown' "
                                       "WHEN yr < 1950 THEN 'pre-1950' WHEN yr < 2020 THEN (yr // 10 * 10)::varchar || 's' "
                                       "ELSE '2020s' END"),
        'in_scope_by_dominant_country': rates(f"CASE WHEN NOT {scope} THEN 'out of scope' ELSE country END"),
        'matches_by_basis': {str(b): dict(works=w, citations=int(c)) for b, w, c in db.execute(
            "SELECT basis, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 2 DESC").fetchall()},
        'matches_by_basis_and_kind': {f'{b} / {k}': dict(works=w, citations=int(c)) for b, k, w, c in db.execute(
            "SELECT basis, k2, count(*), sum(n) FROM ww WHERE newm GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()},
        'chapter_volumes': {},
        'held': {},
    }
    for w, (r, b) in vols.items():
        d = rep['chapter_volumes'].setdefault(b, dict(works=0, citations=0))
        d['works'] += 1
        d['citations'] += corpus[w]['n']
    for w, k, reason, nc, n in held:
        d = rep['held'].setdefault(f'{k} / {reason}', dict(works=0, citations=0))
        d['works'] += 1
        d['citations'] += n
    (out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('index')
    p.add_argument('--scratch', required=True)
    p.add_argument('--procs', type=int, default=3)
    p = sub.add_parser('match')
    p.add_argument('--scratch', required=True)
    p.add_argument('--works', required=True, help='work table with a match flag (work_id, n, kind, yr, has_author, '
                                                 'br, ca, gb, us, ot, m)')
    p.add_argument('--out', required=True)
    a = ap.parse_args()
    {'index': cmd_index, 'match': cmd_match}[a.cmd](a)


if __name__ == '__main__':
    main()
