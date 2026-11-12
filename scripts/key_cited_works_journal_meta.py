"""Cited articles -> article metadata of history journals the Crossref metadata harvest lacks (2026-11-11).
Writes a standalone crosswalk; touches neither the key log nor the graph.

After the Crossref metadata matcher (key_cited_works_crossref_meta.py) about half of the frequently cited articles still
unmatched sit in journals the harvest /mnt/e/crossref-meta-2026-11-11 did not hold: Crossref journals whose cited name
did not resolve (RHAF, Hesperia, Vingtième Siècle, the Persée back files: MEFRA, CRAI, L'Homme, BEC, ...) and journals
without Crossref DOIs for their back runs (BC Studies, Chiron, GRBS, New Mexico Historical Review, ...).
scripts/journal_meta_harvest.py fetched their article metadata from documented metadata endpoints (Crossref REST by
ISSN, journal OJS / bepress OAI-PMH, OpenAlex sources) into build/journal-meta-2026-11-11/<source>/ (git-ignored).

  works   the work table with the CURRENT match flag: every crosswalk behind data/graph/cited-works and
          data/graph/cites.csv.gz, combined as export_cited_works.py combines them (the three older crosswalks and the
          translation-check / Qwen-tail ones, LC full, OpenAlex minus its guarded rows, Crossref, Crossref metadata minus
          held and review-like rows, translations/editions moved to an original). Reproduces 41.96% / articles 36.01%.
  index   the raw harvests -> one Parquet index shaped like the Crossref-meta index (plus a side table with the
          stable source id, origin, URL, volume, issue, pages), linked beside the Crossref-meta index (rebuilt with
          key_cited_works_crossref_meta.py index, which has online_only).
  match   the still-open cited articles and chapters, matched with the rules and guards of
          key_cited_works_crossref_meta.py (its run_match is called, not copied: family name, title keys, years within
          one, generic and short titles need the container, no-year matches need six words + container + one
          candidate, notices and other 'Part n' dropped, other venue + other year held, the review-like candidate
          guard, the post-match guard -- a record whose journal does not agree with the corpus container needs a page
          range of five pages or more -- and the back-file online-date pass), over the Crossref-meta records AND the
          new ones. Additions (none with --plain):
          (a) NAMES: corpus container abbreviations / forms rewritten to the journal title (Annales ESC, RHAF, MEFRA,
              CRAI, ...) so the container tests and guards see the journal;
          (b) 'LEVI (Giovanni)' / 'Chartier (Roger)': the French citation form, which the corpus reads as the family
              'levi giovanni', also gets the family 'levi';
          (c) records with no author at all (JSTOR-era Crossref back files; OJS imports without creators): basis
              `whole_title_container_no_record_author` -- whole titles equal (5+ words, not generic), year within one,
              journal = corpus container, not review-like, the only such record.
          As for crossref-meta, review-like matches are flagged and are not counted (or used).

Output data/identifiers/cited-works-journal-meta-2026-11-11/: crosswalk.csv.gz (work_id, id, doi, title, year, type,
journal, source, basis, container_alias, review_like, pages, cited_by_dissertations; `id` = doi:<doi> when the record
has a DOI, else its stable source id: ojs:<host>:<OAI id>, bepress:<host>:<OAI id>, openalex:<W id>), held.csv.gz,
report.json, audit-sample.csv.

    python3 scripts/key_cited_works_journal_meta.py works --scratch <dir>
    python3 scripts/key_cited_works_crossref_meta.py index --scratch <dir2>          # Crossref-meta index
    python3 scripts/key_cited_works_journal_meta.py index --scratch <dir> --crmeta-index <dir2>/index
    python3 scripts/key_cited_works_journal_meta.py match --scratch <dir> --out data/identifiers/cited-works-journal-meta-2026-11-11
"""
import argparse
import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import key_cited_works_crossref_meta as kcm  # noqa: E402  (extends GENERIC at import, as in its own run)
from key_cited_works_crossref_meta import kcr, review_like, pages_of, BY_RE_STRICT  # noqa: E402
from key_cited_works_openalex import (title_key, fams, load_corpus, db_connect, container_agrees,  # noqa: E402
                                      CORPUS)

ROOT = Path(__file__).resolve().parent.parent
IDS = ROOT / 'data/identifiers'
HARV = ROOT / 'build/journal-meta-2026-11-11'
OLD = [IDS / 'cited-works-2026-11-04/crosswalk.csv.gz', IDS / 'cited-articles-2026-11-03b/crosswalk.csv.gz',
       IDS / 'cited-own-works-2026-11-03f/crosswalk.csv.gz'] + [
    IDS / f'translation-check-2026-11-03{x}/crosswalk.csv.gz' for x in ('d', 'c', 'b', '')] + [
    IDS / 'qwen-tail-2026-11-04/crosswalk.csv.gz']


def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


# ---------------------------------------------------------------------------------------------------- works table

def matched_now():
    """corpus work_ids matched by the crosswalks behind the graph (as export_cited_works.py combines them)."""
    m = set()
    for p in OLD:
        m.update(r['work_id'] for r in rd(p) if r.get('key'))
    m.update(r['work_id'] for r in rd(IDS / 'cited-works-lc-full-2026-11-10/crosswalk.csv.gz'))
    guarded = {r['work_id'] for r in rd(ROOT / 'data/graph/cited-works/openalex-guarded.csv.gz')}
    m.update(r['work_id'] for r in rd(IDS / 'cited-works-openalex-2026-11-10/crosswalk.csv.gz')
             if r['work_id'] not in guarded)
    m.update(r['work_id'] for r in rd(IDS / 'cited-works-crossref-2026-11-10/crosswalk.csv.gz'))
    cm = IDS / 'cited-works-crossref-meta-2026-11-11'
    held = {r['work_id'] for r in rd(cm / 'held.csv.gz')}
    rl = {r['work_id'] for r in rd(cm / 'match-flags.csv.gz') if r['review_like'] == '1'}
    m.update(r['work_id'] for r in rd(cm / 'crosswalk.csv.gz') if r['work_id'] not in held | rl)
    tr = IDS / 'cited-works-translations-2026-11-11'
    held = {r['work_id'] for r in rd(tr / 'held.csv.gz')}
    m.update(r['work_id'] for r in rd(tr / 'crosswalk.csv.gz')
             if r['work_id'] not in held and r['relation'] in ('translation', 'edition') and r['canonical_id'])
    return m


def cmd_works(a):
    import pyarrow as pa
    db = db_connect(a.scratch)
    m = matched_now()
    db.register('m_arrow', pa.table({'work_id': sorted(m)}))
    db.execute(f"""CREATE TEMP TABLE c AS SELECT s.work_id, count(*) n,
            count(*) FILTER (WHERE d.country = 'BR') br, count(*) FILTER (WHERE d.country = 'CA') ca,
            count(*) FILTER (WHERE d.country = 'GB') gb, count(*) FILTER (WHERE d.country = 'US') us,
            count(*) FILTER (WHERE d.country NOT IN ('BR', 'CA', 'GB', 'US') OR d.country IS NULL) ot
        FROM read_csv('{CORPUS}/strict-citations.csv.gz', all_varchar=true) s
        LEFT JOIN read_csv('{CORPUS}/dissertations.csv', all_varchar=true) d ON d.id = s.dissertation_id
        GROUP BY 1""")
    p = Path(a.scratch) / 'works-now.parquet'
    db.execute(f"""COPY (SELECT c.*, w.kind, TRY_CAST(w.year AS INT) yr, coalesce(trim(w.authors), '') <> '' has_author,
            w.container, c.work_id IN (SELECT work_id FROM m_arrow) m
        FROM c JOIN read_csv('{CORPUS}/works.csv', all_varchar=true) w USING (work_id)) TO '{p}' (FORMAT parquet)""")
    tot = db.execute(f"""SELECT sum(n), sum(n) FILTER (WHERE m), sum(n) FILTER (WHERE kind = 'article'),
        sum(n) FILTER (WHERE kind = 'article' AND m) FROM read_parquet('{p}')""").fetchone()
    print(dict(citations=tot[0], matched=tot[1], rate=round(tot[1] / tot[0], 4), articles=tot[2],
               articles_matched=tot[3], article_rate=round(tot[3] / tot[2], 4)))


# ---------------------------------------------------------------------------------------------------- names
# Container names the thesis bibliographies use for journals whose records are in the harvests but which the
# container tests (oa.container_agrees, kcr.abbrev_agrees) do not tie to the journal's title. Key: title_key of the
# corpus container; value: the journal title. Classics abbreviations as in L'Année philologique.
NAMES = {
    'annales esc': 'Annales. Économies, sociétés, civilisations',
    'annales e s c': 'Annales. Économies, sociétés, civilisations',
    'annales economies societes civilisations': 'Annales. Économies, sociétés, civilisations',
    'annales hss': 'Annales. Histoire, Sciences sociales',
    'annales h s s': 'Annales. Histoire, Sciences sociales',
    'rhaf': "Revue d'histoire de l'Amérique française",
    'r h a f': "Revue d'histoire de l'Amérique française",
    'jrs': 'The Journal of Roman Studies',
    'jhs': 'The Journal of Hellenic Studies',
    'cq': 'The Classical Quarterly',
    'aja': 'American Journal of Archaeology',
    'ajph': 'The American Journal of Philology',
    'ajp': 'The American Journal of Philology',
    'bch': 'Bulletin de correspondance hellénique',
    'rea': 'Revue des Études Anciennes',
    'reg': 'Revue des Études Grecques',
    'mefra': "Mélanges de l'École française de Rome. Antiquité",
    'mefrm': "Mélanges de l'École française de Rome. Moyen Âge",
    'crai': "Comptes rendus des séances de l'Académie des inscriptions et belles-lettres",
    'zpe': 'Zeitschrift für Papyrologie und Epigraphik',
    'grbs': 'Greek, Roman and Byzantine Studies',
    'tapa': 'Transactions of the American Philological Association',
    'tapha': 'Transactions of the American Philological Association',
    'cph': 'Classical Philology',
    'hscp': 'Harvard Studies in Classical Philology',
    'hsph': 'Harvard Studies in Classical Philology',
    'pbsr': 'Papers of the British School at Rome',
    'bsa': 'The Annual of the British School at Athens',
    'absa': 'The Annual of the British School at Athens',
    'jea': 'The Journal of Egyptian Archaeology',
    'nc': 'Numismatic Chronicle',
    'num chron': 'Numismatic Chronicle',
    'cj': 'The Classical Journal',
    'clant': 'Classical Antiquity',
    'ant class': "L'Antiquité classique",
    'hssh': 'Histoire sociale/Social history',
    'jcha': 'Journal of the Canadian Historical Association',
}


def alias(cont):
    return NAMES.get(title_key(cont or ''))


# ---------------------------------------------------------------------------------------------------- index

def norm_type(origin, t):
    t = (t or '').lower()
    if origin.startswith('crossref'):
        return t
    if origin == 'openalex':
        return {'article': 'journal-article', 'review': 'journal-article', 'letter': 'other', 'editorial': 'other',
                'other': 'other'}.get(t, 'peer-review')      # book-review, paratext, erratum: never a cited article
    # OAI: OJS section types ('book-review', 'editorial', 'research-article') after the eu-repo terms
    if 'book-rev' in t or 'review' in t.split('|')[-1] and 'peer' not in t:
        return 'peer-review'
    if 'editorial' in t.split('|')[-1]:
        return 'other'
    return 'journal-article'


YEAR = re.compile(r'\b(1[6-9]\d\d|20[0-2]\d)\b')


def oai_year(d):
    """OJS dates back issues by their upload (BC Studies No. 1, Winter 1968/69, is dated 2010): the issue's own year,
    the last year in the first dc:source before the page range ('No. 162: ... 1910-2010, Summer 2009; 111-136' ->
    2009), wins over dc:date. bepress records with a volume -> year rule (Canadian Military History) keep theirs."""
    if re.search(r'/vol\d+/iss', d.get('url') or ''):
        return d.get('year')
    first = (d.get('oai_source') or '').split(' ; ')[0]
    first = re.sub(r';\s*\d+\s*[-–]\s*\d+\s*$', '', first)
    ys = YEAR.findall(first)
    return int(ys[-1]) if ys else d.get('year')


def cmd_index(a):
    import pyarrow as pa
    import pyarrow.parquet as pq
    outdir = Path(a.scratch) / 'newindex'
    outdir.mkdir(parents=True, exist_ok=True)
    cols = {k: [] for k in ('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'fams', 'source', 'issn', 'file',
                            'npages', 'nauth', 'by_stmt', 'online_only')}
    side = {k: [] for k in ('id', 'sid', 'origin', 'url', 'volume', 'issue', 'pages', 'raw_type')}
    seq = 900_000_000
    per = Counter()
    # OpenAlex records were fetched by source (locations.source.id), so their journal is that source; their own
    # primary_location is often a repository (DOAJ, LA Referencia) or empty
    jtitle = {k: v['title'] for k, v in json.loads((HARV / 'journals.json').read_text())['journals'].items()}
    for path in sorted(HARV.glob('*/*.jsonl.gz')):
        origin = path.parent.name
        with gzip.open(path, 'rt', encoding='utf-8') as fh:
            for line in fh:
                d = json.loads(line)
                t = d.get('title') or ''
                if not t:
                    continue
                sub = d.get('subtitle') or ''
                full = t + (': ' + sub if sub and title_key(sub) not in title_key(t) else '')
                aus = [x for x in (d.get('authors') or []) if x and x.strip(' ,')]
                fs = set()
                for au in aus[:6]:
                    fs |= fams(au)
                    if not d.get('authors_are_full_names'):
                        k = title_key(au)
                        if k:
                            fs.add(k)
                year = oai_year(d) if origin == 'oai' else d.get('year')
                seq += 1
                per[(origin, path.name.split('.')[0])] += 1
                cols['id'].append(seq)
                cols['doi'].append(d['doi'] if d.get('doi') else d['sid'])
                cols['title'].append(full[:400])
                cols['main'].append(title_key(full.split(':')[0]))
                cols['whole'].append(title_key(full))
                cols['year'].append(year)
                cols['type'].append(norm_type(origin, d.get('type')))
                cols['fams'].append(sorted(fs))
                jn = jtitle.get(path.name.split('.')[0]) if origin == 'openalex' else None
                cols['source'].append((jn or d.get('journal') or '')[:200] or None)
                cols['issn'].append(d.get('issn') or None)
                cols['file'].append(path.name.split('.')[0])
                cols['npages'].append(pages_of(d.get('pages')))
                cols['nauth'].append(len(aus))
                cols['by_stmt'].append(bool(BY_RE_STRICT.search(full)))
                cols['online_only'].append(bool(d.get('online_only')))
                side['id'].append(seq)
                side['sid'].append(d['sid'])
                side['origin'].append(origin)
                side['url'].append(d.get('url'))
                side['volume'].append(str(d.get('volume') or '') or None)
                side['issue'].append(str(d.get('issue') or '') or None)
                side['pages'].append(str(d.get('pages') or '') or None)
                side['raw_type'].append((d.get('type') or '')[:80])
    tab = pa.table({k: (pa.array(v, pa.int16()) if k in ('year', 'nauth') else pa.array(v, pa.int32()) if k == 'npages'
                        else pa.array(v, pa.int64()) if k == 'id' else pa.array(v)) for k, v in cols.items()})
    pq.write_table(tab, outdir / 'new.parquet', compression='zstd')
    pq.write_table(pa.table({k: (pa.array(v, pa.int64()) if k == 'id' else pa.array(v)) for k, v in side.items()}),
                   Path(a.scratch) / 'new-side.parquet', compression='zstd')
    # the match reads <scratch>/index/*.parquet: the Crossref-meta index (with online_only) + this one
    idx = Path(a.scratch) / 'index'
    idx.mkdir(exist_ok=True)
    for p in sorted(Path(a.crmeta_index).glob('*.parquet')):
        q = idx / ('cm_' + p.name)
        if not q.exists():
            q.symlink_to(p)
    q = idx / 'new.parquet'
    if not q.exists():
        q.symlink_to(outdir / 'new.parquet')
    counts = {f'{o}/{f}': n for (o, f), n in sorted(per.items())}
    (Path(a.scratch) / 'newindex-counts.json').write_text(json.dumps(counts, indent=0, ensure_ascii=False))
    print(tab.num_rows, 'records')


# ---------------------------------------------------------------------------------------------------- match

PAREN_NAME = re.compile(r"^\s*([^\s(),;][^(),;]*?)\s*\(([^)]+)\)")
STATS = Counter()


def patched_load_corpus(db, works_parquet):
    """load_corpus, then (a) NAMES and (b) the 'LEVI (Giovanni)' family (extra rows in the ck key table)."""
    import pyarrow as pa
    corpus = load_corpus(db, works_parquet)
    add = {'w': [], 'k': [], 'f': [], 'y': []}
    for w, c in corpus.items():
        al = alias(c['container'])
        if al:
            c['container_raw'], c['container'] = c['container'], al
            STATS['container_alias_works'] += 1
        new = set()
        for au in (c['authors'] or '').split(';'):
            m = PAREN_NAME.match(au)
            if m:
                fam = title_key(m.group(1))
                if fam:
                    new.add(fam)
                    new.add(fam.split()[-1])
        new -= c['fams']
        if new:
            STATS['paren_name_family_works'] += 1
            c['fams'] |= new
            c['paren_fix'] = True
            for k in {c['main'], c['whole'], c['widt']} - {''}:
                for f in new:
                    add['w'].append(w); add['k'].append(k); add['f'].append(f); add['y'].append(c['year'])
    if add['w']:
        db.register('ck_add', pa.table({'w': add['w'], 'k': add['k'], 'f': add['f'],
                                        'y': pa.array(add['y'], pa.int32())}))
        db.execute("INSERT INTO ck SELECT * FROM ck_add")
    return corpus


def no_author_pass(db, a, corpus, results, held):
    """Records without any author: see (c) in the module notes. Basis `whole_title_container_no_record_author`."""
    import pyarrow as pa
    open_w = [w for w, c in corpus.items() if w not in results and c['container'] and c['year'] is not None
              and len(c['whole'].split()) >= 5 and c['whole'] not in kcr.oa.GENERIC]
    db.register('nw_arrow', pa.table({'w': open_w, 'k': [corpus[w]['whole'] for w in open_w],
                                      'y': pa.array([corpus[w]['year'] for w in open_w], pa.int32())}))
    rows = db.execute(f"""SELECT nw.w, r.id, r.doi, r.title, r.main, r.whole, r.year, r.type, r.source, r.npages,
            r.nauth, r.by_stmt FROM nw_arrow nw JOIN read_parquet('{a.scratch}/index/*.parquet') r
            ON r.whole = nw.k AND len(r.fams) = 0 AND abs(r.year - nw.y) <= 1""").fetchall()
    cands = defaultdict(list)
    for w, *rec in rows:
        cands[w].append(rec)
    hw = {h[0] for h in held}
    for w, cs in cands.items():
        c = corpus[w]
        ok = [(dict(zip(('id', 'doi', 'title', 'main', 'whole', 'year', 'type', 'source'), r[:8])), (r[8], r[9], r[10]))
              for r in cs
              if r[6] in kcr.CR_TYPES and r[6] not in kcr.NOT_ARTICLE
              and not review_like(dict(title=r[2]), (r[8], r[9], r[10]))
              and not (kcr.NOTICE.search(r[2] or '') and not kcr.NOTICE.search(c['title'] or ''))
              and not (kcr.part_of(r[2]) and kcr.part_of(r[2]) != kcr.part_of(c['title']))
              and (container_agrees(c['container'], r[7] or '') or kcr.abbrev_agrees(c['container'], r[7] or ''))]
        dois = {r['doi'] for r, _ in ok}
        if len(dois) == 1:
            ok.sort(key=lambda x: (abs(x[0]['year'] - c['year']), x[0]['id']))
            r, x = ok[0]
            results[w] = (r, 'whole_title_container_no_record_author', False, x)
            STATS['no_author_matches'] += 1
            STATS['no_author_matches_previously_held'] += w in hw
        elif len(dois) > 1:
            held.append((w, c['kind'], 'no_record_author_several', len(dois), c['n']))
    held[:] = [h for h in held if h[0] not in results]


def cmd_match(a):
    db = db_connect(a.scratch)
    src = Path(a.scratch) / 'works-now.parquet'
    p = Path(a.scratch) / 'scope-open.parquet'
    db.execute(f"""COPY (SELECT work_id, n, kind, yr, has_author, br, ca, gb, us, ot,
                   NOT (NOT m AND kind IN ('article', 'chapter')) AS m FROM read_parquet('{src}'))
                   TO '{p}' (FORMAT parquet)""")
    if not a.plain:
        kcm.load_corpus = patched_load_corpus
    corpus, results, held, stats = kcm.run_match(db, a, str(p))
    if not a.plain:
        no_author_pass(db, a, corpus, results, held)
        # audit 2026-11-11: Bassett, 'The Trade of the English East India Company ... Part I: 1623-65' took the record
        # without a part marker; a part marker on the cited side only is held (the converse is kcm.guard's rule)
        for w in [w for w, (r, *_) in results.items() if kcr.part_of(corpus[w]['title']) and not kcr.part_of(r['title'])]:
            held.append((w, corpus[w]['kind'], 'part_only_on_cited_side', 1, corpus[w]['n']))
            del results[w]
            STATS['part_only_on_cited_side_held'] += 1
    stats.update(STATS)
    write(db, a, corpus, results, held, stats)


def write(db, a, corpus, results, held, stats):
    import pyarrow as pa
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    side = {}
    sp = Path(a.scratch) / 'new-side.parquet'
    db.register('rid', pa.table({'id': pa.array([r['id'] for r, *_ in results.values()], pa.int64())}))
    if sp.exists():
        for i, sid, origin in db.execute(f"""SELECT id, sid, origin FROM read_parquet('{sp}')
                                            WHERE id IN (SELECT id FROM rid)""").fetchall():
            side[i] = (sid, origin)
    rows = []
    for w, (r, basis, rl, x) in sorted(results.items()):
        origin = side[r['id']][1] if r['id'] in side else 'crossref-meta'
        doi = r['doi'] if (r['doi'] or '').startswith('10.') else ''
        rid = f'doi:{doi}' if doi else r['doi']
        rows.append([w, rid, doi, r['title'], r['year'], r['type'], r['source'] or '', origin, basis,
                     int(bool(corpus[w].get('container_raw'))), int(bool(corpus[w].get('paren_fix'))), int(bool(rl)),
                     x[0] if x[0] is not None else '', corpus[w]['n']])
    with gzip.open(out / 'crosswalk.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'id', 'doi', 'title', 'year', 'type', 'journal', 'source', 'basis', 'container_alias',
                     'french_name_family', 'review_like', 'pages', 'cited_by_dissertations'])
        wr.writerows(rows)
    with gzip.open(out / 'held.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'kind', 'reason', 'candidates', 'cited_by_dissertations'])
        wr.writerows(sorted(held, key=lambda x: -x[4]))
    report(db, a, corpus, rows, held, stats, out)


def report(db, a, corpus, rows, held, stats, out):
    import pyarrow as pa
    use = [r for r in rows if not r[11]]                       # review-like matches are not used (as crossref-meta)
    db.register('new_arrow', pa.table({'work_id': [r[0] for r in use], 'basis': [r[8] for r in use],
                                       'origin': [r[7] for r in use], 'journal': [r[6] for r in use],
                                       'alias': [r[9] for r in use]}))
    db.execute(f"""CREATE OR REPLACE TEMP TABLE ww AS SELECT w.*, new.basis, new.origin, new.journal, new.alias,
        new.work_id IS NOT NULL AS newm FROM read_parquet('{a.scratch}/works-now.parquet') w LEFT JOIN new_arrow new
        USING (work_id)""")

    def rates(group, where='true'):
        res = db.execute(f"""SELECT {group} AS g, count(*), sum(n), sum(n) FILTER (WHERE m),
                sum(n) FILTER (WHERE m OR newm), count(*) FILTER (WHERE newm), sum(n) FILTER (WHERE newm)
                FROM ww WHERE {where} GROUP BY 1 ORDER BY 1""").fetchall()
        return {str(g): dict(works=wk, citations=int(c), before=int(b or 0), after=int(af or 0),
                             before_rate=round((b or 0) / c, 4), after_rate=round((af or 0) / c, 4),
                             new_works=nw, new_citations=int(nc or 0)) for g, wk, c, b, af, nw, nc in res}
    rep = dict(
        note=('citations = rows of strict-citations.csv.gz; before = matched by every crosswalk behind '
              'data/graph/cited-works and data/graph/cites.csv.gz as export_cited_works.py combines them; '
              'after = before or this crosswalk (review-like matches excluded, as for crossref-meta)'),
        overall=rates("'all'")['all'], by_kind=rates('kind'),
        matches_by_basis={str(b): dict(works=w, citations=int(c)) for b, w, c in db.execute(
            "SELECT basis, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 3 DESC").fetchall()},
        matches_by_source={str(b): dict(works=w, citations=int(c)) for b, w, c in db.execute(
            "SELECT origin, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 3 DESC").fetchall()},
        matches_by_source_and_basis={f'{o} / {b}': dict(works=w, citations=int(c)) for o, b, w, c in db.execute(
            "SELECT origin, basis, count(*), sum(n) FROM ww WHERE newm GROUP BY 1, 2 ORDER BY 4 DESC").fetchall()},
        container_alias_matches={str(k): dict(works=w, citations=int(c)) for k, w, c in db.execute(
            "SELECT alias, count(*), sum(n) FROM ww WHERE newm GROUP BY 1").fetchall()},
        review_like_matches_not_used=sum(1 for r in rows if r[11]),
        stats=dict(stats),
        top_journals_by_citations_gained=[dict(journal=j, works=w, citations=int(c)) for j, w, c in db.execute(
            "SELECT journal, count(*), sum(n) FROM ww WHERE newm GROUP BY 1 ORDER BY 3 DESC LIMIT 80").fetchall()],
        held={})
    for w, k, reason, nc, n in held:
        d = rep['held'].setdefault(f'{k} / {reason}', dict(works=0, citations=0))
        d['works'] += 1
        d['citations'] += n
    (out / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: rep[k] for k in ('overall', 'matches_by_basis', 'matches_by_source', 'container_alias_matches',
                                          'review_like_matches_not_used', 'stats')}, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for c in ('works', 'index', 'match'):
        p = sub.add_parser(c)
        p.add_argument('--scratch', required=True)
        if c == 'index':
            p.add_argument('--crmeta-index', required=True)
        if c == 'match':
            p.add_argument('--out', required=True)
            p.add_argument('--plain', action='store_true', help='no NAMES / paren-name / no-author additions')
    a = ap.parse_args()
    {'works': cmd_works, 'index': cmd_index, 'match': cmd_match}[a.cmd](a)


if __name__ == '__main__':
    main()
