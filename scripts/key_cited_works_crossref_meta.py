"""Cited articles -> Crossref journal articles from the all-years METADATA harvest (2026-11-11).
Writes a standalone crosswalk; touches neither the key log nor the graph.

The harvest of 2026-11-08 held only records with deposited references from 2000 on, so the matcher of 2026-11-10
(scripts/key_cited_works_crossref.py) could not reach most pre-2000 articles or journals such as Past & Present.
scripts/crossref_metadata_harvest.py fetched every record of the catalogue's journals and of the journals that
unmatched cited articles name (25+ citations), all years, metadata only (/mnt/e/crossref-meta-2026-11-11/works/).

Corpus: works.csv works of kind article or chapter that NO crosswalk holds: the three older ones, the LC full, OpenAlex
and Crossref crosswalks of 2026-11-10 (a work table with the flag `m`, `--works`).

Rules: those of key_cited_works_crossref.py, which imports key_cited_works_openalex.py (imported here, not copied or
edited): an author family name agrees, the title keys agree (whole, or main title), years within one, generic and short
titles need the container, no-year matches need six words + the container + one candidate, notices (erratum,
addendum) and different 'Part n' markers are dropped, another venue in another year is held, several candidates fall
to the container or are held. One addition here: the Crossref subtitle (a separate field in this harvest) is joined to
the title for the whole-title key.

Book reviews. A complete journal run brings in its book reviews, and a review's Crossref title is often just the
reviewed book's title. Guards:
- scope: only works the corpus files as articles or chapters; a cited BOOK is never matched here;
- the family-name test: Crossref review records carry the REVIEWER as author, so a citation of the book (by its
  author) fails unless the reviewer shares the author's family name;
- `review_like` records: a title with price/pages/ISBN/'Review of' text (REVIEW_RE of the OpenAlex matcher), a title
  carrying a 'By <Name>' / 'Edited by' statement, or a record of one or two pages, are kept only when the corpus
  container agrees with the record's journal (the thesis then cites the piece in that journal, a review or a short
  note). Otherwise they are dropped as candidates (counted in report.json as `review_guard`);
- after the match (audit of 2026-11-11, see guard()): a record whose journal does not agree with the corpus container
  (or the corpus gives none) needs a page range of five pages or more. Reviews in complete runs often carry the
  reviewed book's author among the Crossref authors and no page range, so the family test alone did not keep a book
  the corpus filed as an article (no container) from its review.

Back files dated by digitisation (Érudit and others deposit old volumes with only an online date, e.g. JCHA vol. 1,
1990, dated 2006): a second pass for still-unmatched works takes a record with no print date and an online date two
or more years after the cited year when the whole titles (five words or more), an author family and the journal all
agree and it is the only such record (basis `whole_title_container_online_date`; see online_date_pass()).

Outputs: crosswalk.csv.gz (columns as the 2026-11-10 Crossref crosswalk), held.csv.gz, report.json, and
match-flags.csv.gz (per match: review_like, pages, n_authors, by_statement; for audits).

    python3 scripts/key_cited_works_crossref_meta.py index --scratch <dir>
    python3 scripts/key_cited_works_crossref_meta.py match --scratch <dir> --works <w.parquet> \\
        --out data/identifiers/cited-works-crossref-meta-2026-11-11
"""
import argparse
import csv
import glob
import gzip
import html
import json
import re
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import key_cited_works_crossref as kcr  # noqa: E402  (also extends oa.GENERIC at import)
from key_cited_works_openalex import title_key, fams, judge, candidates, load_corpus, db_connect, band, yband  # noqa: E402
from key_cited_works_openalex import container_agrees, REVIEW_RE, ckey  # noqa: E402

HARVEST = '/mnt/e/crossref-meta-2026-11-11/works'
# section headings that read as titles (audit 2026-11-11: 'Essay Reviews: Commerce and Enlightenment' took the
# journal's 'ESSAY REVIEWS' record); added at run time, the OpenAlex matcher is not edited
kcr.oa.GENERIC |= {'essay reviews', 'review essays', 'book notes', 'short notices', 'notes and comments',
                   'reviews of books', 'book reviews and notices', 'books received', 'recent publications'}
GROUPS = 48
BY_RE = re.compile(r'(?:\.|,|\s)\s*(?:by|edited by|ed\. by|hrsg\. von|par|por|di)\s+[A-Z][a-z]', re.I)
BY_RE_STRICT = re.compile(r'[.,]\s*(?:By|Edited by|Ed\. by|Hrsg\. von)\s+[A-Z]')

CORE = {   # coverage check: title_key forms of the corpus container and of the Crossref journal
    'American Historical Review': ['american historical review'],
    'Past & Present': ['past and present'],
    'Journal of Social History': ['journal of social history'],
    'Canadian Historical Review': ['canadian historical review'],
    'Journal of American History': ['journal of american history'],
    'English Historical Review': ['english historical review'],
    'Gender & History': ['gender and history'],
    'William and Mary Quarterly': ['william and mary quarterly'],
    'Speculum': ['speculum', 'speculum a journal of medieval studies'],
    'Journal of British Studies': ['journal of british studies'],
    'Labour/Le Travail': ['labour le travail', 'labourle travail', 'labour'],
    'History Workshop Journal': ['history workshop journal', 'history workshop'],
    'Annales': ['annales', 'annales esc', 'annales histoire sciences sociales', 'annales economies societes civilisations',
                'annales e s c'],
    'Hispanic American Historical Review': ['hispanic american historical review'],
    'Revista Brasileira de Historia': ['revista brasileira de historia'],
}


def pages_of(p):
    m = re.match(r'^\s*([0-9]+)\s*[-–]\s*([0-9]+)\s*$', p or '')
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if b < a and len(m.group(2)) < len(m.group(1)):          # '1203-5' -> 1205
        b = int(m.group(1)[:len(m.group(1)) - len(m.group(2))] + m.group(2))
    return b - a + 1 if b >= a else None


def index_group(args):
    gi, files, outdir = args
    import orjson
    import pyarrow as pa
    import pyarrow.parquet as pq
    out = Path(outdir) / f'g{gi:03d}.parquet'
    if out.exists():
        return gi, -1
    cols = {k: [] for k in ('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'fams', 'source', 'issn', 'file',
                            'npages', 'nauth', 'by_stmt', 'online_only')}
    seq = gi * 10_000_000
    for path in files:
        with gzip.open(path, 'rb') as fh:
            for line in fh:
                d = orjson.loads(line)
                ts = d.get('title') or []
                t = re.sub(r'\s+', ' ', html.unescape(kcr.TAG.sub('', ts[0] if ts else ''))).strip()
                if not t or not d.get('DOI'):
                    continue
                ss = d.get('subtitle') or []
                sub = re.sub(r'\s+', ' ', html.unescape(kcr.TAG.sub('', ss[0] if ss else ''))).strip()
                full = t + (': ' + sub if sub and title_key(sub) not in title_key(t) else '')
                fs = set()
                aus = d.get('author') or []
                for au in aus[:6]:
                    fam = html.unescape(au.get('family') or au.get('name') or '')
                    fs |= fams(fam)
                    k = title_key(fam)
                    if k:
                        fs.add(k)
                seq += 1
                ct = d.get('container-title') or []
                cols['id'].append(seq)
                cols['doi'].append(d['DOI'].lower())
                cols['title'].append(full[:400])
                cols['main'].append(title_key(full.split(':')[0]))
                cols['whole'].append(title_key(full))
                cols['year'].append(kcr.year_of(d))
                cols['type'].append(d.get('type'))
                cols['fams'].append(sorted(fs))
                cols['source'].append(html.unescape(ct[0] if ct else '')[:200] or None)
                cols['issn'].append('|'.join(d.get('ISSN') or []) or None)
                cols['file'].append(Path(path).name.split('.')[0])
                cols['npages'].append(pages_of(d.get('page')))
                cols['nauth'].append(len(aus))
                cols['by_stmt'].append(bool(BY_RE_STRICT.search(full)))
                cols['online_only'].append('published-print' not in d and 'published-online' in d)
    tab = pa.table({k: (pa.array(v, pa.int16()) if k in ('year', 'nauth') else
                        pa.array(v, pa.int32()) if k == 'npages' else pa.array(v)) for k, v in cols.items()})
    tmp = out.with_suffix('.part')
    pq.write_table(tab, tmp, compression='zstd')
    tmp.rename(out)
    return gi, tab.num_rows


def cmd_index(a):
    outdir = Path(a.scratch) / 'index'
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f'{HARVEST}/*.jsonl.gz'))
    groups = [(i, files[i::GROUPS], str(outdir)) for i in range(GROUPS)]
    total = 0
    with Pool(a.procs) as pool:
        for gi, n in pool.imap_unordered(index_group, groups):
            total += max(n, 0)
            print('group', gi, n, total, flush=True)


def review_like(r, x):
    """x = (npages, nauth, by_stmt) of the record."""
    npages, nauth, by_stmt = x
    return bool(REVIEW_RE.search(r['title'] or '')) or bool(by_stmt) or (npages is not None and npages <= 2)


def sub_words(t):
    parts = (t or '').split(':', 1)
    return set(title_key(parts[1]).split()) if len(parts) == 2 else set()


def guard(c, j, x, ncands):
    """Audit of 2026-11-11 (audit-sample.csv, review-check.csv):
    - a record whose journal does not agree with the corpus container (or the corpus has none) and that has no page
      range or fewer than five pages is held: that is what a complete run's book reviews look like, and a thesis's
      citation of a BOOK the corpus filed as an article (no container) took them (Bourke, 'Dismembering the Male',
      AHR 1997 review; Harmon, 'Indians in the Making', AIQ 1999 review);
    - main-title matches where both titles carry a subtitle and the subtitles share under half their words are held
      (Wilson, 'Treasure and Trade Balances: The Mercantilist Problem' took '...: Further Evidence');
    - main-title matches in another journal than the corpus container are held (Henderson, 'War Psychoses -
      Dementia Praecox in War Time', Review of Neurology and Psychiatry 1918, took his 'War Psychoses: An Analysis of
      202 Cases', Journal of Mental Science 1918);
    - a record marked as one part ('Part 2') of a corpus title without a part marker is held (Aron, 'Social Structure
      and the Ruling Class', BJS 1950, in two parts)."""
    r, basis = j[1], j[2]
    npages = x[0]
    cont_ok = bool(c['container']) and (container_agrees(c['container'], r['source'] or '')
                                        or kcr.abbrev_agrees(c['container'], r['source'] or ''))
    if not cont_ok and (npages is None or npages < 5):
        return ('held', 'no_container_agreement_short_or_unpaged', ncands)
    if basis.startswith('main_title'):
        if c['container'] and not cont_ok:
            return ('held', 'main_title_other_container', ncands)
        a, b = sub_words(c['title']), sub_words(r['title'])
        if a and b and not (a <= b or b <= a) and len(a & b) / len(a | b) < 0.5:   # one subtitle cut short is fine
            return ('held', 'main_title_subtitles_differ', ncands)
    if kcr.part_of(r['title']) and not kcr.part_of(c['title']):
        return ('held', 'part_unspecified', ncands)
    return j


def scope_parquet(db, a, cond, name):
    p = Path(a.scratch) / name
    db.execute(f"""COPY (SELECT work_id, n, kind, yr, has_author, br, ca, gb, us, ot,
                   NOT ({cond} AND kind IN ('article', 'chapter')) AS m FROM read_parquet('{a.works}'))
                   TO '{p}' (FORMAT parquet)""")
    return str(p)


def run_match(db, a, works_parquet):
    corpus = load_corpus(db, works_parquet)
    print('corpus works in scope', len(corpus), flush=True)
    results, held, stats = match_corpus(db, a, corpus)
    return corpus, results, held, stats


def match_corpus(db, a, corpus):
    """The match proper on a loaded corpus (dict + the `scope` and `ck` tables of load_corpus); a.scratch holds index/.
    Split from run_match on 2026-11-11 so the JSTOR note matcher (key_jstor_cited_works_full.py crmeta) runs the same
    rules on its own cited-work forms. -> (results, held, stats)."""
    cands = candidates(db, a.scratch, kcr.CR_TYPES, ('article', 'chapter'), 'x')
    print('works with candidates', len(cands), flush=True)
    ids = sorted({r['id'] for cs in cands.values() for r in cs})
    import pyarrow as pa
    db.register('cid_arrow', pa.table({'id': pa.array(ids, pa.int64())}))
    extra = {i: (p, n, b) for i, p, n, b in db.execute(f"""SELECT id, npages, nauth, by_stmt
        FROM read_parquet('{a.scratch}/index/*.parquet') WHERE id IN (SELECT id FROM cid_arrow)""").fetchall()}
    results, held, stats = {}, [], Counter()
    for w, cs in cands.items():
        c = corpus[w]
        t = c['title'] or ''
        cs = [r for r in cs if r['type'] not in kcr.NOT_ARTICLE
              and not (kcr.NOTICE.search(r['title'] or '') and not kcr.NOTICE.search(t))]
        n0 = len(cs)
        cs = [r for r in cs if not (review_like(r, extra.get(r['id'], (None, 0, False)))
                                    and not REVIEW_RE.search(t)
                                    and not container_agrees(c['container'], r['source'] or ''))]
        if len(cs) < n0:
            stats['review_like_dropped_candidates'] += n0 - len(cs)
            if not cs:
                stats['works_left_without_candidates_by_review_guard'] += 1
        if not cs:
            continue
        cp = kcr.part_of(t)
        cs = [r for r in cs if not (cp and kcr.part_of(r['title']) and kcr.part_of(r['title']) != cp)]
        if not cs:
            continue
        j = judge(c, cs, False)
        if not j:
            continue
        if j[0] == 'match' and kcr.other_venue(c, j[1]):
            j = ('held', 'other_venue_other_year', len(cs))
        a_, b_ = c['whole'] + ' ', (j[1]['whole'] + ' ') if j[0] == 'match' else ''
        if j[0] == 'match' and c['year'] is None and not (a_.startswith(b_) or b_.startswith(a_)):
            j = ('held', 'no_year_subtitles_differ', len(cs))
        if j[0] == 'match':
            j = guard(c, j, extra.get(j[1]['id'], (None, 0, False)), len(cs))
        if j[0] == 'match':
            r = j[1]
            rl = review_like(r, extra.get(r['id'], (None, 0, False)))
            results[w] = (r, j[2], rl, extra.get(r['id'], (None, 0, False)))
        else:
            held.append((w, c['kind'], j[1], j[2], c['n']))
    online_date_pass(db, a, corpus, results, held, stats, extra)
    return results, held, stats


def online_date_pass(db, a, corpus, results, held, stats, extra):
    """Back files dated by their digitisation. Some publishers deposited old volumes with only an online date, the
    day the back file went up (Érudit: Wien, 'Selling Beaver Skins ...', JCHA vol. 1, 1990, is dated 2006-02-09;
    Lavoie, Recherches sociographiques vol. 12, 1971, 2005-04-12), so the year test drops them. Here, for works still
    unmatched: the record has no print date and an online date two years or more after the cited year, the WHOLE titles
    agree and run to five words or more, an author family agrees, the record's journal agrees with the corpus
    container, it is not review-like, and it is the only such record. Basis `whole_title_container_online_date`."""
    import pyarrow as pa
    open_w = [w for w, c in corpus.items() if w not in results and c['year'] is not None and c['container']
              and len(c['whole'].split()) >= 5]
    db.register('ow_arrow', pa.table({'w': open_w}))
    rows = db.execute(f"""WITH r AS (SELECT id, doi, title, main, whole, year, type, source, fams, npages, nauth, by_stmt
            FROM read_parquet('{a.scratch}/index/*.parquet') WHERE online_only
            AND whole IN (SELECT k FROM ck WHERE w IN (SELECT w FROM ow_arrow)))
        SELECT DISTINCT ck.w, r.id, r.doi, r.title, r.main, r.whole, r.year, r.type, r.source, r.npages, r.nauth, r.by_stmt
        FROM ck JOIN r ON r.whole = ck.k AND list_contains(r.fams, ck.f) AND r.year >= ck.y + 2
        WHERE ck.w IN (SELECT w FROM ow_arrow)""").fetchall()
    cands = {}
    for w, *rec in rows:
        cands.setdefault(w, []).append(rec)
    for w, cs in cands.items():
        c = corpus[w]
        ok = [dict(zip(('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'source'), r[:8])) for r in cs
              if r[4] == c['whole'] and r[6] not in kcr.NOT_ARTICLE
              and not review_like(dict(title=r[2]), (r[8], r[9], r[10]))
              and not (kcr.NOTICE.search(r[2] or '') and not kcr.NOTICE.search(c['title'] or ''))
              and (container_agrees(c['container'], r[7] or '') or kcr.abbrev_agrees(c['container'], r[7] or ''))]
        if len({r['doi'] for r in ok}) == 1:
            r = ok[0]
            results[w] = (r, 'whole_title_container_online_date', False, (None, 0, False))
            stats['online_date_matches'] += 1
        elif ok:
            held.append((w, c['kind'], 'online_date_several', len(ok), c['n']))


def cmd_match(a):
    db = db_connect(a.scratch)
    wp = scope_parquet(db, a, 'NOT m', 'scope-unmatched.parquet')
    corpus, results, held, stats = run_match(db, a, wp)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out / 'crosswalk.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'doi', 'cr_title', 'cr_year', 'cr_type', 'cr_journal', 'basis', 'cited_by_dissertations'])
        for w, (r, basis, rl, x) in sorted(results.items()):
            wr.writerow([w, r['doi'], r['title'], r['year'], r['type'], r['source'] or '', basis, corpus[w]['n']])
    # side file for audit: the review-like flag and page count of each match (not part of the crosswalk format)
    with gzip.open(out / 'match-flags.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'review_like', 'pages', 'n_authors', 'by_statement'])
        for w, (r, basis, rl, x) in sorted(results.items()):
            wr.writerow([w, int(rl), x[0] if x[0] is not None else '', x[1], int(bool(x[2]))])
    with gzip.open(out / 'held.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'kind', 'reason', 'candidates', 'cited_by_dissertations'])
        wr.writerows(sorted(held, key=lambda x: -x[4]))
    report(db, a, corpus, results, held, stats, out)


def report(db, a, corpus, results, held, stats, out):
    import pyarrow as pa
    db.register('new_arrow', pa.table({'work_id': list(results), 'basis': [v[1] for v in results.values()],
                                       'journal': [v[0]['source'] or '' for v in results.values()],
                                       'review_like': [v[2] for v in results.values()]}))
    db.execute("CREATE OR REPLACE TEMP TABLE new AS SELECT * FROM new_arrow")
    db.execute(f"""CREATE OR REPLACE TEMP TABLE ww AS SELECT w.*, new.basis, new.journal, new.review_like,
        new.work_id IS NOT NULL AS newm,
        CASE WHEN greatest(br, ca, gb, us, ot) = 0 THEN 'none'
             WHEN br = greatest(br, ca, gb, us, ot) THEN 'BR' WHEN ca = greatest(br, ca, gb, us, ot) THEN 'CA'
             WHEN gb = greatest(br, ca, gb, us, ot) THEN 'GB' WHEN us = greatest(br, ca, gb, us, ot) THEN 'US'
             ELSE 'other' END AS country
        FROM read_parquet('{a.works}') w LEFT JOIN new USING (work_id)""")

    def rates(group, where='true'):
        rows = db.execute(f"""SELECT {group} AS g, count(*) works, sum(n) cites,
                sum(n) FILTER (WHERE m) before_cites, sum(n) FILTER (WHERE m OR newm) after_cites,
                count(*) FILTER (WHERE newm) new_works, sum(n) FILTER (WHERE newm) new_cites
                FROM ww WHERE {where} GROUP BY 1 ORDER BY 1""").fetchall()
        return {str(g): dict(works=wk, citations=int(c), before=int(b or 0), after=int(af or 0),
                             before_rate=round((b or 0) / c, 4) if c else None,
                             after_rate=round((af or 0) / c, 4) if c else None,
                             new_works=nw, new_citations=int(nc or 0)) for g, wk, c, b, af, nw, nc in rows}

    art = "kind = 'article'"
    yb = ("CASE WHEN yr IS NULL THEN 'unknown' WHEN yr < 1950 THEN 'pre-1950' "
          "WHEN yr < 2020 THEN (yr // 10 * 10)::varchar || 's' ELSE '2020s' END")
    cb = "CASE WHEN n = 1 THEN '1' WHEN n < 5 THEN '2-4' WHEN n < 10 THEN '5-9' ELSE '10+' END"
    rep = {
        'note': ('citations = sum of citing theses (strict) per work; before = matched by any crosswalk through '
                 '2026-11-10 (cited-works-2026-11-04, cited-articles-2026-11-03b, cited-own-works-2026-11-03f, '
                 'cited-works-lc-full/openalex/crossref-2026-11-10); after = before or this crosswalk'),
        'overall': rates("'all'")['all'],
        'by_kind': rates('kind'),
        'articles_by_citing_band': rates(cb, art),
        'articles_by_year_band': rates(yb, art),
        'articles_by_dominant_country': rates('country', art),
        'chapters_by_citing_band': rates(cb, "kind = 'chapter'"),
        'chapters_by_year_band': rates(yb, "kind = 'chapter'"),
        'matches_by_basis': {str(b): dict(works=w, citations=int(c)) for b, w, c in db.execute(
            "SELECT basis, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 2 DESC").fetchall()},
        'matches_by_basis_and_kind': {f'{b} / {k}': dict(works=w, citations=int(c)) for b, k, w, c in db.execute(
            "SELECT basis, kind, count(*), sum(n) FROM ww WHERE newm GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()},
        'matches_by_basis_and_year_band': {f'{b} / {y}': dict(works=w, citations=int(c)) for b, y, w, c in db.execute(
            f"SELECT basis, {yb}, count(*), sum(n) FROM ww WHERE newm GROUP BY 1, 2 ORDER BY 1, 2").fetchall()},
        'review_like_matches': {str(k): dict(works=w, citations=int(c)) for k, w, c in db.execute(
            "SELECT review_like, count(*), sum(n) FROM ww WHERE newm GROUP BY 1").fetchall()},
        'review_guard': dict(stats),
        'top_journals_by_citations_gained': [dict(journal=j, works=w, citations=int(c)) for j, w, c in db.execute(
            "SELECT journal, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 3 DESC, 2 DESC LIMIT 60").fetchall()],
        'held': {},
        'core_journals': core_coverage(db, a, results),
    }
    for w, k, reason, nc, n in held:
        d = rep['held'].setdefault(f'{k} / {reason}', dict(works=0, citations=0))
        d['works'] += 1
        d['citations'] += n
    (out / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: rep[k] for k in ('overall', 'by_kind', 'articles_by_year_band', 'matches_by_basis',
                                          'review_like_matches', 'review_guard', 'core_journals')}, indent=1))


def core_coverage(db, a, results):
    """Per core journal: Crossref records harvested (all / before 2000), and the corpus articles whose container is
    that journal (title_key of the container in the journal's forms): citations, matched before, after."""
    meta = Path(HARVEST).parent
    counts = json.loads((meta / 'counts.json').read_text())
    by_file = {k: v for k, v in db.execute(f"""SELECT file, count(*) FROM read_parquet('{a.scratch}/index/*.parquet')
                                               GROUP BY 1""").fetchall()}
    pre = {k: v for k, v in db.execute(f"""SELECT file, count(*) FROM read_parquet('{a.scratch}/index/*.parquet')
                                           WHERE year < 2000 GROUP BY 1""").fetchall()}
    rows = db.execute(f"""SELECT w.work_id, w.container, ww.n, ww.m FROM ww JOIN read_csv(
        '{kcr.oa.CORPUS}/works.csv', all_varchar=true) w USING (work_id) WHERE ww.kind = 'article'
        AND coalesce(w.container, '') <> ''""").fetchall()
    keyed = {}
    for wid, cont, n, m in rows:
        keyed.setdefault(title_key(cont), []).append((wid, n, m))
    out = {}
    for name, forms in CORE.items():
        jids = [jid for jid, v in counts.items() if title_key(v['title']) in forms
                or title_key(v['title'].split(':')[0]) in forms or title_key(v['title'].split('.')[0]) in forms]
        recs = sum(by_file.get(j, 0) for j in jids)
        cites = before = after = 0
        for f in forms:
            for wid, n, m in keyed.get(f, []):
                cites += n
                before += n if m else 0
                after += n if (m or wid in results) else 0
        out[name] = dict(crossref_journals=[counts[j]['title'] for j in jids], crossref_total=sum(counts[j]['total'] for j in jids),
                         harvested=recs, harvested_pre2000=sum(pre.get(j, 0) for j in jids), corpus_article_citations=cites,
                         matched_before=before, matched_after=after,
                         before_rate=round(before / cites, 4) if cites else None,
                         after_rate=round(after / cites, 4) if cites else None)
    return out


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
