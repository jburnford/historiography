"""JSTOR article citations -> the whole LC 2016 book file, OpenAlex, Crossref and the JSTOR index (2026-11-11).

The JSTOR full-text session's rule parser cut the notes of 93.6k JSTOR history items into 8.6M citation rows
(/mnt/e/jstor-fulltext-2026-11-06/rules/part-*.jsonl.gz and textnotes-rules.jsonl.gz; HANDOVER-match-candidates.md).
jstor_match_candidates.py matched them only to works the key log holds, and export_jstor_citations.py wrote 817k CITES
(data/graph/jstor-cites.csv.gz). This script tries the citations that matched nothing against the three big targets
the dissertation side used on 2026-11-10, with those matchers' own rules, imported and not edited:
- books -> the whole LC 2016 book file (key_cited_works_lc_full: its `build` and its per-work choice run unchanged on
  a work table of JSTOR cited-work forms; see `lc`);
- articles, chapters and books cited 2017 on -> OpenAlex (key_cited_works_openalex: candidates + judge);
- articles and chapters -> Crossref (key_cited_works_crossref: candidates + judge + part/notice/other-venue guards);
- articles and chapters -> JSTOR's own metadata index (/mnt/e/jstor-index.parquet, scripts/jstor_index.py), a fourth
  target judged exactly as the Crossref route and used last (`jstor`; the handover's 'not yet done' route).
- articles and chapters -> the all-years Crossref METADATA harvest (/mnt/e/crossref-meta-2026-11-11; 2026-11-11 evening,
  `crmeta`): key_cited_works_crossref_meta.match_corpus, the thesis-side rules unchanged (review-like guard, post-match
  page/container guard, Érudit online-date pass), on the forms no other route chose; used last, review-like matches
  dropped. One JSTOR-side guard: a short title whose cited container names an edited volume is held.
Nothing here is a key-log event; nothing is minted. Audit 2026-11-11 (build/jstor-cited-audit-2026-11-11, note text,
git-ignored): 250/250 new matches right over 21 strata, plus 25/25 initials-only LC matches with an early cited year.

Input adaptations (only what note citations need):
- a cited-work FORM is (cited kind, title, author list as printed, year); one form row carries `n` = the number of
  distinct citing articles. The matchers see forms, as they saw corpus works.
- short forms the parser could not resolve ('Smith, Making, 45' with no earlier full citation found) are resolved
  here to a full citation in the same article: same first family name (folded, last word) and the short title is a
  prefix of the full title's key, or all its words of four letters or more are in the full title. Unresolved short
  forms whose title has three words or more are themselves tried as forms (kind `short`, books route only, the title
  must equal a record's main title: a short title is usually the main title).
- a given name the parser left at the head of the title ('Stone' + 'L., The family, sex and marriage ...';
  'Easterlin' + 'Richard, "Regional Income Trends ..." in ...') goes back to the author when the citation's authors
  carry no given name; a quoted title after it is the title of an article (or a chapter, with 'in ...' as its
  volume); a trailing '. 1982. Reprint' is cut (clean_form).
- initials-only authors ('Clifford, J.') matched to LC books: the matched LC title must be distinctive: the cited
  main title has three words or more, or the cited year falls within the LC work's record years (two either side).
  A one- or two-word main title with an initials-only author and no agreeing year is held (`initials_short_title`).
- the cited year is not a further guard: a cited year more than two years before the LC work's earliest record
  (`year_fit` = before) is only flagged (LC 2016 often holds the reprint, not the first edition; a draft that held
  these for initials-only authors held 17k forms, 14/14 of a sample right).
- OpenAlex rows pass export_cited_works.py's guards (notice, part markers, another venue in another year).
- precedence when several sources match one form: LC, then Crossref, then OpenAlex (as export_cited_works.py), then
  the JSTOR index, then the Crossref metadata harvest; forms whose identifiers overlap are one cited work.
- the cited work id is the key-log work key when the key log already holds one of the LCCNs or the DOI
  (build/graph/work.parquet anchors), else `lccn:<lccn>` / `doi:<doi>` / `openalex:<W id>`.
- book reviews give no citations (KG-INTEGRATION-PLAN standing rule): their rows are counted but never matched.

Stages (scratch folder holds every intermediate; E: is read only):
    python3 scripts/key_jstor_cited_works_full.py extract  --scratch <dir>
    python3 scripts/key_jstor_cited_works_full.py forms    --scratch <dir>
    python3 scripts/key_jstor_cited_works_full.py lc       --scratch <dir>
    python3 scripts/key_cited_works_openalex.py index --scratch <dir>/oa ; python3 scripts/key_cited_works_crossref.py index --scratch <dir>/cr
    python3 scripts/key_jstor_cited_works_full.py openalex --scratch <dir>
    python3 scripts/key_jstor_cited_works_full.py crossref --scratch <dir>
    python3 scripts/key_jstor_cited_works_full.py jstor    --scratch <dir>
    python3 scripts/key_jstor_cited_works_full.py crmeta   --scratch <dir> --crmeta <key_cited_works_crossref_meta index dir>
    python3 scripts/key_jstor_cited_works_full.py fold     --scratch <dir> --out data/identifiers/jstor-cited-works-2026-11-11
    python3 scripts/key_jstor_cited_works_full.py audit    --scratch <dir> --audit build/jstor-cited-audit-2026-11-11
"""
import argparse
import csv
import glob
import gzip
import hashlib
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data/field-research/jstor-fulltext-2026-11-06'))
from build_dissertation_citation_graph import fold as _fold, title_key as _title_key  # noqa: E402
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

E = '/mnt/e/jstor-fulltext-2026-11-06'
RECORDS = 'file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro'
GRAPH = ROOT / 'build/graph'
JSTOR_CITES = ROOT / 'data/graph/jstor-cites.csv.gz'
MATCHES = f'{E}/match-candidates.parquet'
QWEN = f'{E}/match-candidates-qwen.parquet'
WORK_KINDS = ('book', 'article', 'chapter', 'thesis', 'periodical')
T0 = time.time()


def log(*a):
    print(f'[{round(time.time() - T0)}s]', *a, flush=True)


TMP = None   # --tmp: DuckDB temp folder for every stage (default <scratch>/ddb)


def connect(scratch, path=None):
    tmp = Path(TMP or scratch) / 'ddb'
    tmp.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(path) if path else ':memory:')
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB'; SET temp_directory='{tmp}'; "
              "SET preserve_insertion_order=false; SET enable_progress_bar=false")
    return c


def wait_memory(gb=6):
    while True:
        with open('/proc/meminfo') as f:
            m = {l.split(':')[0]: int(l.split()[1]) for l in f}
        if m['MemAvailable'] / 1e6 >= gb:
            return
        log('waiting for memory', round(m['MemAvailable'] / 1e6, 1), 'GB available')
        time.sleep(60)


def fold(s):
    return _fold(s or '')


def family(label):
    """jstor_match_candidates.family: the last word of the folded family name."""
    label = re.sub(r',?\s+(?:Jr|Sr|II|III|IV)\.?$', '', (label or '').strip())
    part = label.split(',')[0] if ',' in label else (label.split() or [''])[-1]
    words = fold(part).split()
    return words[-1] if words else ''


# ------------------------------------------------------------------------------------------------ extract

def item_meta():
    c = sqlite3.connect(RECORDS, uri=True)
    out = {}
    for item_id, doi, year, genre, subtype, journal in c.execute(
            'select item_id, doi, year, genre, subtype, journal_title from records where included'):
        t = ('review' if subtype == 'book-review' else 'review essay' if subtype in ('review-article', 'review-essay')
             else 'article' if subtype == 'research-article' else 'other')
        out[item_id.split(':')[-1]] = ((doi or '').lower(), year, t, journal)
    return out


def cmd_extract(a):
    """Rule rows -> rows.parquet (one per citation row; parsed bibliographic fields only), with the earlier matcher's
    outcome per row, the item's year/type, and short forms resolved anew."""
    import orjson
    import pyarrow as pa
    import pyarrow.parquet as pq
    S = Path(a.scratch)
    meta = item_meta()
    log('items', len(meta))
    files = sorted(glob.glob(f'{E}/rules/part-*.jsonl.gz')) + [f'{E}/textnotes-rules.jsonl.gz']
    cols = defaultdict(list)
    writer = None
    st = Counter()

    def flush():
        nonlocal writer
        if not cols['iid']:
            return
        t = pa.table({k: pa.array(v, type=SCHEMA[k]) for k, v in cols.items()})
        if writer is None:
            writer = pq.ParquetWriter(S / 'rows.parquet', t.schema, compression='zstd')
        writer.write_table(t)
        cols.clear()

    def emit(iid, src, rows):
        res = resolve_shorts(rows)
        for i, r in enumerate(rows):
            for k, v in (('iid', iid), ('src', src), ('idx', i), ('note', r.get('note')), ('rule', r.get('rule')),
                         ('kind', r.get('kind')), ('conf', r.get('conf')),
                         ('authors', ';'.join(x for x in (r.get('authors') or []) if x)[:500] or None),
                         ('surnames', ';'.join(x for x in (r.get('surnames') or []) if x)[:300] or None),
                         ('editors', edlist(r.get('editors'))),
                         ('title', (r.get('title') or '')[:500] or None), ('container', (r.get('container') or '')[:300] or None),
                         ('year', r.get('year') if isinstance(r.get('year'), int) else None),
                         ('ref', r.get('ref')), ('ref2', res.get(i))):
                cols[k].append(v)
        st['rows'] += len(rows)
        st['resolved_new'] += len(res)

    for fn in files:
        src = 'text' if 'textnotes' in fn else 'list'
        cur, rows = None, []
        with gzip.open(fn, 'rb') as f:
            for line in f:
                r = orjson.loads(line)
                if r['iid'] != cur:
                    if rows:
                        emit(cur, src, rows)
                    cur, rows = r['iid'], []
                rows.append(r)
                if len(cols['iid']) > 500_000:
                    flush()
        if rows:
            emit(cur, src, rows)
        flush()
        log(Path(fn).name, dict(st))
    writer.close()
    # item table
    t = pa.table(dict(iid=list(meta), doi=[v[0] for v in meta.values()], year=pa.array([v[1] for v in meta.values()], pa.int32()),
                      itype=[v[2] for v in meta.values()], journal=[v[3] for v in meta.values()]))
    pq.write_table(t, S / 'items.parquet')
    log('extract done', dict(st))


SCHEMA = None


def edlist(x):
    """`editors` is a list of names or True (the citation says 'ed.' for its authors)."""
    if x is True:
        return 'yes'
    if isinstance(x, list):
        return ';'.join(v for v in x if isinstance(v, str))[:300] or None
    return None


def _schema():
    import pyarrow as pa
    global SCHEMA
    s, i = pa.string(), pa.int32()
    SCHEMA = dict(iid=s, src=s, idx=i, note=i, rule=s, kind=s, conf=pa.float32(), authors=s, surnames=s, editors=s,
                  title=s, container=s, year=i, ref=i, ref2=i)


SHORT_TAIL = re.compile(r'(?:[\s,]*(?:op\.?\s*cit|ouvr?\.?\s*cit|art\.?\s*cit|loc\.?\s*cit|cit)\b\.?.*$)|'
                        r'(?:,\s*(?:[IVXLC]{1,6}|Bd\.\s*\d+|vol\.\s*\d+|t\.\s*[IVXLC\d]+)\s*$)|\s*\.{2,}\s*$|\s*…\s*$', re.I)


def short_words(t):
    return [w for w in re.findall(r'[^\W\d_]{4,}', fold(t))]


def resolve_shorts(rows):
    """Short forms ('short'/'opcit'/'short_quoted' backrefs) the parser left unresolved (ref None) -> the index of a full
    citation in the same article: first family name agrees (folded last word) and the short title is a prefix of the
    full title's key (8+ characters) or its words of 4+ letters all appear in the full title. A full citation is a row
    of a work kind with a title; one that comes later in the article counts too (bibliography-style notes), the
    nearest earlier one first. Several different candidates -> unresolved."""
    out = {}
    fulls = None
    for i, r in enumerate(rows):
        if r.get('kind') != 'backref' or r.get('ref') is not None or r.get('rule', '').replace('idem+', '') not in (
                'short', 'opcit', 'short_quoted'):
            continue
        sur = [family(s) for s in (r.get('surnames') or []) if s]
        t = SHORT_TAIL.sub('', r.get('title') or '').strip(' ,.;:')
        if not sur or not sur[0] or not t:
            continue
        if fulls is None:
            fulls = []
            for j, x in enumerate(rows):
                if x.get('kind') in WORK_KINDS and x.get('title') and x.get('surnames'):
                    fulls.append((j, {family(s) for s in x['surnames'] if s}, _title_key(x['title']), set(short_words(x['title']))))
        tk = _title_key(t)
        ws = set(short_words(t))
        hit = []
        for j, fams, fk, fw in fulls:
            if sur[0] not in fams:
                continue
            if (len(tk) >= 8 and fk.startswith(tk)) or (ws and len(ws) >= 1 and ws <= fw and len(''.join(ws)) >= 6):
                hit.append(j)
        if not hit:
            continue
        before = [j for j in hit if j < i]
        pick = before[-1] if before else hit[0]
        # several different works hit: keep only when they share one title key (the same work cited twice)
        if len({_title_key(rows[j]['title']) for j in hit}) > 1 and not before:
            continue
        if before and len({_title_key(rows[j]['title']) for j in before}) > 1:
            cand = [j for j in before if _title_key(rows[j]['title']).startswith(tk)] if len(tk) >= 8 else []
            if len({_title_key(rows[j]['title']) for j in cand}) != 1:
                continue
            pick = cand[-1]
        out[i] = pick
    return out


# ------------------------------------------------------------------------------------------------ classes and forms

CLASS_SQL = """
CASE
  WHEN tgt <> idx THEN 'repeat'
  WHEN kind = 'backref' AND rule IN ('authordate', 'idem+authordate') THEN 'authordate_unresolved'
  WHEN kind = 'backref' AND title IS NOT NULL AND surnames IS NOT NULL AND ok_title THEN 'short_attemptable'
  WHEN kind = 'backref' AND rule IN ('ibid', 'idem') THEN 'ibid_unresolved'
  WHEN kind = 'backref' THEN 'short_unresolved'
  WHEN kind = 'primary' THEN 'archival'
  WHEN kind = 'web' THEN 'web'
  WHEN kind = 'periodical' THEN 'periodical'
  WHEN kind NOT IN ('book', 'article', 'chapter', 'thesis') AND rule = 'unparsed' THEN 'unparsed'
  WHEN kind NOT IN ('book', 'article', 'chapter', 'thesis') THEN 'commentary_or_other'
  WHEN title IS NULL THEN 'fragment_no_title'
  WHEN surnames IS NULL THEN 'fragment_no_author'
  WHEN NOT ok_title THEN 'title_too_short'
  WHEN exported THEN 'matched'
  WHEN candidate THEN 'matched_ambiguous'
  ELSE 'attemptable_unmatched' END"""
ATTEMPT = ('attemptable_unmatched', 'matched_ambiguous', 'short_attemptable')

# the given name left at the head of the title when the parser cut 'Stone, L., The family, sex and marriage ...' or
# 'Easterlin, Richard, "Regional Income Trends ..." in ...' after the family name (about 190k rows)
LEAD = re.compile(r"^((?:[A-Z]\.\s*-?\s*){1,4}|[A-ZÀ-Ý][a-zà-ÿ]+(?:[\s-][A-ZÀ-Ý][a-zà-ÿ]+)?(?:\s(?:[A-Z]\.\s*){1,3})?)"
                  r"\s*[,.]\s+(?!(?:and|et|und|y|e)\b|&)(.{6,})$")
QUOTED = re.compile(r"""^["“‘'«]\s*(.{6,}?)\s*[,.]?\s*["”’'»](?=[\s,.;:]|$)\s*[,.;:]?\s*(.*)$""")
TAIL = re.compile(r'\.\s+(?:1[5-9]\d\d|20[0-2]\d|Reprint|Repr\.|Trans\.|Translated|Edited|Ed\.|\d(?:st|nd|rd|th) ed).*$')


def clean_form(kind, title, names):
    """-> (kind, title, names, container or None, how). Only where the citation's authors carry no given name (the
    given name went into the title); a quoted title after the lead is taken as the title of an article or chapter."""
    how = None
    cont = None
    if names and all(',' not in n and len(n.split()) == 1 for n in names):
        m = LEAD.match(title)
        if m and not re.match(r'^\d', m.group(2)):
            given, title = m.group(1).strip(), m.group(2)
            names = [f'{names[0]}, {given}'] + names[1:]
            how = 'lead_given'
    q = QUOTED.match(title)
    if q and len(q.group(1).split()) >= 2:
        title, rest = q.group(1).strip(' ,.'), q.group(2)
        how = (how or '') + '+quoted'
        if re.match(r'^in\b', rest, re.I):
            kind, cont = 'chapter', re.sub(r'^in\s+', '', rest, flags=re.I)[:200]
        elif rest and kind == 'book':
            kind, cont = 'article', rest[:200]
    t2 = TAIL.sub('', title)
    if t2 != title and len(t2) >= 6:
        title, how = t2, (how or '') + '+tail'
    return kind, title, names, cont, how


def cmd_forms(a):
    """rows.parquet -> cls.parquet (a class per row, its target row, the earlier matcher's outcome) and forms.parquet
    (one row per cited-work form to try; n = distinct citing articles, outside book reviews)."""
    from jstor_match_candidates import cited_key, usable
    S = Path(a.scratch)
    c = connect(S)
    from duckdb.sqltypes import BOOLEAN, VARCHAR
    c.create_function('ok_title', lambda t: bool(t) and usable(cited_key(t)), [VARCHAR], BOOLEAN, null_handling='special')
    # the earlier matcher's candidates, and whether export_jstor_citations.py kept them
    c.execute(f"""CREATE TABLE mc AS SELECT iid::VARCHAR iid, source src, cit idx,
          bool_or((basis IN ('strong', 'title+year', 'doi', 'no_year') AND n_works = 1
                   AND NOT (route = 'online_first' AND coalesce(author_rank, 0) > 0))
               OR (basis = 'edition?' AND n_works = 1 AND cited_year > work_year)) exported,
          any_value(work) FILTER (WHERE n_works = 1) work1
        FROM '{MATCHES}' WHERE cit IS NOT NULL GROUP BY ALL""")
    log('candidates', c.execute('select count(*), sum(exported::int) from mc').fetchone())
    wait_memory()
    c.execute(f"""CREATE TABLE r0 AS SELECT r.*, i.year cyear, coalesce(i.itype, 'not_included') itype,
          CASE WHEN r.kind = 'backref' THEN coalesce(r.ref, r.ref2, r.idx)
               WHEN r.ref IS NOT NULL AND r.kind IN ('book', 'article', 'chapter', 'thesis') THEN r.ref ELSE r.idx END tgt,
          ok_title(r.title) ok_title, mc.idx IS NOT NULL candidate, coalesce(mc.exported, false) exported, mc.work1
        FROM read_parquet('{S}/rows.parquet') r LEFT JOIN read_parquet('{S}/items.parquet') i USING (iid)
        LEFT JOIN mc ON mc.iid = r.iid AND mc.src = r.src AND mc.idx = r.idx""")
    c.execute(f"CREATE TABLE r1 AS SELECT *, {CLASS_SQL} cls FROM r0")
    # a repeat counts for its target; how the repeat got there (parser vs this script's short-form resolution)
    c.execute("""CREATE TABLE cls AS SELECT r1.iid, r1.src, r1.idx, r1.tgt, r1.rule, r1.kind, r1.cls, r1.cyear, r1.itype,
          r1.ref IS NULL AND r1.ref2 IS NOT NULL AND r1.cls = 'repeat' via_new_short,
          t.cls tcls, r1.title, r1.surnames, r1.authors, r1.editors, r1.year, r1.container, t.work1 twork
        FROM r1 LEFT JOIN r1 t ON t.iid = r1.iid AND t.src = r1.src AND t.idx = r1.tgt""")
    c.execute(f"COPY (SELECT * EXCLUDE (title, surnames, authors, editors, container) FROM cls) TO '{S}/cls.parquet' (FORMAT parquet)")
    log('classes', c.execute("select cls, count(*) from cls group by 1 order by 2 desc").fetchall())
    # forms: target rows to try, outside book reviews
    rows = c.execute(f"""SELECT iid, src, idx, cls, kind, title, authors, editors, surnames, year, container
        FROM cls WHERE cls IN {ATTEMPT} AND itype <> 'review'""").fetchall()
    log('attempt rows', len(rows))
    from jstor_match_candidates import CITED_VOLUME
    forms, link = {}, []
    hows = Counter()
    for iid, src, idx, cl, kind, title, authors, editors, surnames, year, cont in rows:
        k = 'short' if cl == 'short_attemptable' else kind
        t = (CITED_VOLUME.sub('', title) or title).strip(' ,.;')
        names = [x for x in (authors or '').split(';') if x]
        if editors and editors != 'yes':
            names += [x for x in editors.split(';') if x and x not in names]
        if not names or k == 'short':
            names = [x for x in (surnames or '').split(';') if x]
        if k != 'short':
            k, t, names, c2, how = clean_form(k, t, names)
            cont = cont or c2
            hows[how] += 1
            if not usable(cited_key(t)):
                hows['unusable_after_cleaning'] += 1
                continue
        au = ';'.join(names[:6])
        h = hashlib.md5(f'{k}|{t}|{au}|{year}|{cont or ""}'.encode()).hexdigest()[:16]
        wid = f'jf-{h}'
        if wid not in forms:
            forms[wid] = [k, t, au, year, cont, set()]
        forms[wid][5].add(iid)
        link.append((iid, src, idx, wid))
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.table(dict(iid=[x[0] for x in link], src=[x[1] for x in link], idx=pa.array([x[2] for x in link], pa.int32()),
                                 form=[x[3] for x in link])), S / 'form-rows.parquet')
    ids = list(forms)
    pq.write_table(pa.table(dict(work_id=ids, kind=[forms[w][0] for w in ids], title=[forms[w][1] for w in ids],
                                 authors=[forms[w][2] for w in ids], year=pa.array([forms[w][3] for w in ids], pa.int32()),
                                 container=[forms[w][4] for w in ids], n=pa.array([len(forms[w][5]) for w in ids], pa.int32()))),
                   S / 'forms.parquet')
    log('forms', len(forms), Counter(v[0] for v in forms.values()), 'cleaning', dict(hows))
    (S / 'forms-report.json').write_text(json.dumps(dict(forms=len(forms), rows=len(link), cleaning=dict(
        (str(k), v) for k, v in hows.items()), kinds=Counter(v[0] for v in forms.values())), indent=1))


# ------------------------------------------------------------------------------------------------ the three matchers

LC_KIND = {'book': 'book', 'thesis': 'thesis_or_book', 'short': 'unstyled'}


def cmd_lc(a):
    """key_cited_works_lc_full run unchanged on the book-like forms: its work table (`works`) is written here first, so
    its `build` skips the dissertation corpus and its main() matches and writes the crosswalk into <scratch>/lc/out."""
    import key_cited_works_lc_full as lcf
    S = Path(a.scratch)
    W = S / 'lc'
    W.mkdir(exist_ok=True)
    wait_memory()
    c = connect(S, W / 'work.duckdb')
    c.execute(f"""CREATE OR REPLACE TABLE works AS SELECT work_id, n, CASE kind WHEN 'book' THEN 'book' WHEN 'thesis' THEN
          'thesis_or_book' ELSE 'unstyled' END kind, year yr, authors, title, 'none' dom, 0 br, false m
        FROM read_parquet('{S}/forms.parquet') WHERE kind IN ('book', 'thesis', 'short')""")
    log('lc works', c.execute('select kind, count(*), sum(n) from works group by 1').fetchall())
    c.close()
    sys.argv = ['key_cited_works_lc_full.py', '--out', str(W / 'out'), '--work', str(W)]
    try:
        lcf.main()
    except TypeError:
        # its report.json counts dissertation citations matched before (the `m` flag), all false here: the crosswalk
        # and held files are written before that step and are all this script reads
        if not (W / 'out/crosswalk.csv.gz').exists():
            raise
        log('LC crosswalk written; the LC matcher report (dissertation before/after) does not apply and is skipped')


def oa_corpus(db, S, kinds, book_from=None):
    """The OpenAlex matcher's corpus (load_corpus's dict and its `scope` and `ck` tables) built from the forms."""
    import pyarrow as pa
    from key_cited_works import family_of
    import key_cited_works_openalex as oa
    cond = ' OR '.join([f"kind IN ({','.join(repr(k) for k in kinds)})"]
                       + ([f"(kind = 'book' AND year >= {book_from})"] if book_from else []))
    rows = db.execute(f"""SELECT work_id, kind, n, authors, title, year, container FROM read_parquet('{S}/forms.parquet')
                          WHERE {cond}""").fetchall()
    corpus, keys = {}, {'w': [], 'k': [], 'f': [], 'y': []}
    for wid, kind, n, authors, title, y, cont in rows:
        fam = set()
        for au in (authors or '').split(';'):
            f = family_of(oa._PUNCT.sub(' ', au)) if au.strip() else ''
            if f:
                fam.add(f)
                fam.add(f.split()[-1])
        main, whole = oa.title_key((title or '').split(':')[0]), oa.title_key(title or '')
        corpus[wid] = dict(kind=kind, n=n, authors=authors, title=title, year=y, container=cont, fams=fam,
                           main=main, whole=whole, widt='')
        for k in {main, whole} - {''}:
            for f in fam:
                keys['w'].append(wid); keys['k'].append(k); keys['f'].append(f); keys['y'].append(y)
    db.register('sc_arrow', pa.table({'work_id': list(corpus), 'kind': [v['kind'] for v in corpus.values()]}))
    db.execute("CREATE OR REPLACE TEMP TABLE scope AS SELECT * FROM sc_arrow")
    db.register('ck_arrow', pa.table({'w': keys['w'], 'k': keys['k'], 'f': keys['f'], 'y': pa.array(keys['y'], pa.int32())}))
    db.execute("CREATE OR REPLACE TEMP TABLE ck AS SELECT * FROM ck_arrow")
    return corpus


def write_rows(path, head, rows):
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


def cmd_openalex(a):
    """key_cited_works_openalex.candidates + judge on article/chapter forms and books cited 2017 on."""
    import key_cited_works_openalex as oa
    S = Path(a.scratch)
    wait_memory()
    db = oa.db_connect(S / 'oa')
    corpus = oa_corpus(db, S, ('article', 'chapter'), book_from=2017)
    log('openalex corpus', len(corpus))
    results, held = {}, []
    for kinds, types, book in ((('article', 'chapter'), oa.ART_TYPES, False), (('book',), oa.BOOK_TYPES, True)):
        cands = oa.candidates(db, str(S / 'oa'), types, kinds, 'x')
        log(kinds, 'forms with candidates', len(cands))
        for w, cs in cands.items():
            j = oa.judge(corpus[w], cs, book)
            if not j:
                continue
            if j[0] == 'match':
                results[w] = (j[1], j[2])
            else:
                held.append((w, corpus[w]['kind'], j[1], j[2], corpus[w]['n']))
    write_rows(S / 'oa-crosswalk.csv.gz', ['work_id', 'openalex_id', 'doi', 'oa_title', 'oa_year', 'oa_type', 'oa_source', 'basis', 'n'],
               ([w, f"W{r['id']}", r['doi'] or '', r['title'], r['year'], r['type'], r['source'] or '', b, corpus[w]['n']]
                for w, (r, b) in results.items()))
    write_rows(S / 'oa-held.csv.gz', ['work_id', 'kind', 'reason', 'candidates', 'n'], held)
    log('openalex matched', len(results), 'held', len(held), Counter(b for _, b in results.values()).most_common(12))


def cmd_crossref(a):
    """key_cited_works_crossref's run_match logic (candidates + judge + its part/notice/other-venue guards) on the
    article/chapter forms. Run on all of them, not only the ones OpenAlex missed: the fold prefers Crossref."""
    import key_cited_works_crossref as kcr
    S = Path(a.scratch)
    wait_memory()
    db = kcr.db_connect(S / 'cr')
    corpus = oa_corpus(db, S, ('article', 'chapter'))
    log('crossref corpus', len(corpus))
    cands = kcr.candidates(db, str(S / 'cr'), kcr.CR_TYPES, ('article', 'chapter'), 'x')
    log('forms with candidates', len(cands))
    results, held = cr_judge_all(kcr, corpus, cands)
    write_rows(S / 'cr-crosswalk.csv.gz', ['work_id', 'doi', 'cr_title', 'cr_year', 'cr_type', 'cr_journal', 'basis', 'n'],
               ([w, r['doi'], r['title'], r['year'], r['type'], r['source'] or '', b, corpus[w]['n']]
                for w, (r, b) in results.items()))
    write_rows(S / 'cr-held.csv.gz', ['work_id', 'kind', 'reason', 'candidates', 'n'], held)
    log('crossref matched', len(results), 'held', len(held), Counter(b for _, b in results.values()).most_common(12))


def cmd_jstor(a):
    """A fourth target for articles and chapters: JSTOR's own metadata index (/mnt/e/jstor-index.parquet, made by
    scripts/jstor_index.py: title keys, year, container, creators' families), judged exactly as the Crossref route
    (key_cited_works_openalex.judge with the Crossref matcher's part/notice/other-venue guards). Only the index rows
    sharing a title key with a form are copied to <scratch>/js/index (scratch is small). Used last in the fold: it adds
    only where LC, Crossref and OpenAlex found nothing."""
    import key_cited_works_crossref as kcr
    S = Path(a.scratch)
    J = S / 'js'
    (J / 'index').mkdir(parents=True, exist_ok=True)
    wait_memory()
    db = kcr.db_connect(J)
    corpus = oa_corpus(db, S, ('article', 'chapter'))
    db.execute("CREATE OR REPLACE TEMP TABLE ks0 AS SELECT DISTINCT k FROM ck")
    db.execute(f"""COPY (SELECT row_number() OVER () AS id, doi, title, main, whole, year::SMALLINT AS year,
            CASE kind WHEN 'chapter' THEN 'book-chapter' ELSE kind END AS type, families AS fams, container AS source
          FROM read_parquet('/mnt/e/jstor-index.parquet')
          WHERE kind IN ('article', 'chapter') AND (main IN (SELECT k FROM ks0) OR whole IN (SELECT k FROM ks0)))
        TO '{J}/index/j.parquet' (FORMAT parquet)""")
    log('jstor index rows kept', db.execute(f"SELECT count(*) FROM '{J}/index/j.parquet'").fetchone())
    cands = kcr.candidates(db, str(J), ('article', 'book-chapter'), ('article', 'chapter'), 'x')
    log('forms with candidates', len(cands))
    results, held = cr_judge_all(kcr, corpus, cands)
    write_rows(S / 'js-crosswalk.csv.gz', ['work_id', 'doi', 'js_title', 'js_year', 'js_type', 'js_journal', 'basis', 'n'],
               ([w, r['doi'], r['title'], r['year'], r['type'], r['source'] or '', b, corpus[w]['n']]
                for w, (r, b) in results.items()))
    write_rows(S / 'js-held.csv.gz', ['work_id', 'kind', 'reason', 'candidates', 'n'], held)
    log('jstor matched', len(results), 'held', len(held), Counter(b for _, b in results.values()).most_common(12))


EDITED_VOLUME = re.compile(r"(?:\beds?\.|\beds\b|\bedited\b|\bhrsg\b|\bdir\.|\(dir\)|\bedition\b|\b\d+(?:nd|rd|th|e)\s+[eé]d)", re.I)


def cmd_crmeta(a):
    """A fifth target for articles and chapters (2026-11-11, evening): the all-years Crossref METADATA harvest
    (/mnt/e/crossref-meta-2026-11-11, indexed by key_cited_works_crossref_meta.py index into <crmeta>/index). Its
    match_corpus runs unchanged (candidates + judge + the part/notice/other-venue guards + the review-like candidate
    guard + the post-match guard + the Érudit online-date pass) on the article/chapter forms that no earlier route
    chose (<scratch>/chosen.parquet of the last fold). Used last in the fold; review-like matches and held rows are
    never used there (as export_cited_works.py does for the thesis side)."""
    import types as _types
    import pyarrow as pa
    import key_cited_works_crossref_meta as kcm
    S = Path(a.scratch)
    wait_memory()
    db = connect(S)
    corpus = oa_corpus(db, S, ('article', 'chapter'))
    done = {r[0] for r in db.execute(f"""SELECT form FROM read_parquet('{S}/chosen.parquet')
                                          WHERE source <> 'crossref-meta'""").fetchall()}
    for w in [w for w in corpus if w in done]:
        del corpus[w]
    db.register('open_arrow', pa.table({'w': list(corpus)}))
    db.execute("DELETE FROM scope WHERE work_id NOT IN (SELECT w FROM open_arrow)")
    db.execute("DELETE FROM ck WHERE w NOT IN (SELECT w FROM open_arrow)")
    log('crossref-meta corpus (article/chapter forms no route chose)', len(corpus))
    results, held, stats = kcm.match_corpus(db, _types.SimpleNamespace(scratch=a.crmeta), corpus)
    # JSTOR-side guard (audit 2026-11-11, build/jstor-cited-audit-crmeta-2026-11-11: 26/27 short-title matches right):
    # a short title whose cited container names an edited volume ('eds.', 'edited by', '2nd ed.', 'dir.') agreed with a
    # journal only through the loose container test ('The Industrial Revolution' in Floud and McCloskey, eds., The
    # Economic History of Britain since 1700 took an Economic History Review record of that title): held
    for w in [w for w, v in results.items() if v[1].startswith('short_title') and EDITED_VOLUME.search(corpus[w]['container'] or '')]:
        held.append((w, corpus[w]['kind'], 'short_title_edited_volume', 1, corpus[w]['n']))
        del results[w]
        stats['short_title_edited_volume_held'] += 1
    write_rows(S / 'cm-crosswalk.csv.gz', ['work_id', 'doi', 'cr_title', 'cr_year', 'cr_type', 'cr_journal', 'basis',
                                           'review_like', 'pages', 'n'],
               ([w, r['doi'], r['title'], r['year'], r['type'], r['source'] or '', b, int(rl),
                 x[0] if x[0] is not None else '', corpus[w]['n']] for w, (r, b, rl, x) in results.items()))
    write_rows(S / 'cm-held.csv.gz', ['work_id', 'kind', 'reason', 'candidates', 'n'], held)
    log('crossref-meta matched', len(results), 'held', len(held), dict(stats),
        Counter(v[1] for v in results.values()).most_common(12), 'review_like', sum(v[2] for v in results.values()))


def cr_judge_all(kcr, corpus, cands):
    """key_cited_works_crossref.run_match's loop: candidates -> (results, held)."""
    results, held = {}, []
    for w, cs in cands.items():          # as key_cited_works_crossref.run_match
        t = corpus[w]['title'] or ''
        cs = [r for r in cs if r['type'] not in kcr.NOT_ARTICLE
              and not (kcr.NOTICE.search(r['title'] or '') and not kcr.NOTICE.search(t))]
        if not cs:
            continue
        c = corpus[w]
        cp = kcr.part_of(t)
        cs = [r for r in cs if not (cp and kcr.part_of(r['title']) and kcr.part_of(r['title']) != cp)]
        if not cs:
            continue
        j = kcr.judge(c, cs, False)
        if not j:
            continue
        if j[0] == 'match' and kcr.other_venue(c, j[1]):
            j = ('held', 'other_venue_other_year', len(cs))
        a_, b_ = c['whole'] + ' ', (j[1]['whole'] + ' ') if j[0] == 'match' else ''
        if j[0] == 'match' and c['year'] is None and not (a_.startswith(b_) or b_.startswith(a_)):
            j = ('held', 'no_year_subtitles_differ', len(cs))
        if j[0] == 'match':
            results[w] = (j[1], j[2])
        else:
            held.append((w, corpus[w]['kind'], j[1], j[2], corpus[w]['n']))
    return results, held


# ------------------------------------------------------------------------------------------------ fold

def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def intor(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def lc_guard(form, m, years):
    """JSTOR-side guard on an LC book match (see the docstring): -> None (keep) or a held reason.
    form: (kind, title, authors, year); m: the LC crosswalk row; years: the LC records' years of the cluster."""
    import key_cited_works_lc_full as lcf
    kind, title, authors, cy = form
    tform = m['basis'].split('/')[0]
    if kind == 'short' and tform not in ('exact', 'whole'):
        return 'short_form_title_form'
    hf = lcf.py_compact(lcf.py_words(m['lc_author_heading'].split(',')[0])) if m['lc_author_heading'] else ''
    given = None
    for au in (authors or '').split(';'):
        fam, g = lcf.parse_name(au)
        if hf and (lcf.py_compact(fam) == hf or hf in lcf.family_variants(fam)):
            given = g
            break
    if given is None:   # matched through a variant or the statement of responsibility: the first cited author
        given = lcf.parse_name((authors or '').split(';')[0])[1]
    spelled = any(len(w) > 1 for w in given)
    main_words = len(lcf.long_key((title or '').split(':')[0]))
    year_ok = bool(cy and years and min(years) - 2 <= cy <= max(years) + 2)
    if kind == 'short':
        return None if main_words >= 3 else 'short_form_title_under_3_words'
    if spelled:
        return None
    if main_words < 3 and not year_ok:
        return 'initials_short_title'
    # a first draft also held initials-only matches whose cited year is 3+ years before LC's earliest record
    # (17k forms); 14/14 of a sample were right (LC 2016 holds the reprint: Gilboy, Gooch, Robertson), so the cited
    # year is only a flag (`year_fit`) when the main title has three words or more
    return None


def cmd_fold(a):
    import key_cited_works_lc_full as lcf  # noqa: F401  (guards use it)
    import export_cited_works as ecw
    import key_cited_works_crossref as kcr
    S = Path(a.scratch)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    wait_memory()
    c = connect(S)
    R = Counter()
    forms = {w: (k, t, au, y, cont, n) for w, k, t, au, y, cont, n in c.execute(
        f"SELECT work_id, kind, title, authors, year, container, n FROM read_parquet('{S}/forms.parquet')").fetchall()}
    # LC record years of every matched LCCN
    lcx = list(rd(S / 'lc/out/crosswalk.csv.gz'))
    lcc = duckdb.connect(str(S / 'lc/work.duckdb'), read_only=True)
    ly = dict(lcc.execute('SELECT control, y FROM lrec').fetchall())
    lcc.close()
    chosen, held = {}, []
    for m in lcx:
        w = m['work_id']
        f = forms[w]
        ctl = [x for x in m['lccns'].split(';') if x]
        reason = lc_guard(f[:4], m, [ly[x] for x in ctl if ly.get(x)])
        if reason:
            R['lc_held_' + reason] += 1
            held.append((w, 'lc-full', reason, f[5], ';'.join(f'lccn:{x}' for x in ctl[:5]), m['lc_title'][:150]))
            continue
        chosen[w] = dict(ids=[f'lccn:{x}' for x in ctl], source='lc-full', basis=m['basis'], title=m['lc_title'],
                         year=intor(m['lc_year']), kind='book', container='', author=m['lc_author_heading'],
                         author_uri=m['lc_author_uri'], initial=m['initial'], year_fit=m['year_fit'])
    for h in rd(S / 'lc/out/held.csv.gz'):
        held.append((h['work_id'], 'lc-full', 'lc_' + h['title_form'] + '_several_people', forms[h['work_id']][5], '', ''))
    R['lc_rows'] = len(lcx)
    for r in rd(S / 'cr-crosswalk.csv.gz'):
        w = r['work_id']
        if w in chosen:
            R['crossref_also_lc'] += 1
            continue
        chosen[w] = dict(ids=[f"doi:{r['doi'].lower()}"], source='crossref', basis=r['basis'], title=r['cr_title'],
                         year=intor(r['cr_year']), kind=ecw.cr_kind(r['cr_type']), container=r['cr_journal'])
    for r in rd(S / 'oa-crosswalk.csv.gz'):
        w = r['work_id']
        if w in chosen:
            R['openalex_also_' + chosen[w]['source']] += 1
            continue
        k, t, au, y, cont, n = forms[w]
        rt = r['oa_title'] or ''
        cp, rp = kcr.part_of(t), kcr.part_of(rt)
        guard = None
        if kcr.NOTICE.search(rt) and not kcr.NOTICE.search(t):
            guard = 'notice'
        elif cp and rp and cp != rp:
            guard = 'part_differs'
        elif (k == 'article' or k == 'chapter' and r['oa_type'] == 'article') and kcr.other_venue(
                dict(container=cont, year=y), dict(year=intor(r['oa_year']), source=r['oa_source'])) \
                and ecw.named_venue(r['oa_source']) and not ecw.venue_words_shared(cont, r['oa_source']):
            guard = 'other_venue_other_year'
        if guard:
            R['openalex_guard_' + guard] += 1
            held.append((w, 'openalex', guard, n, f"doi:{r['doi']}" if r['doi'] else f"openalex:{r['openalex_id']}", rt[:150]))
            continue
        doi = (r['doi'] or '').lower()
        chosen[w] = dict(ids=([f'doi:{doi}'] if doi else []) + [f"openalex:{r['openalex_id']}"], source='openalex',
                         basis=r['basis'], title=rt, year=intor(r['oa_year']), kind=ecw.oa_kind(r['oa_type']),
                         container=r['oa_source'])
    if (S / 'js-crosswalk.csv.gz').exists():
        for r in rd(S / 'js-crosswalk.csv.gz'):
            w = r['work_id']
            if w in chosen:
                R['jstor_index_also_' + chosen[w]['source']] += 1
                continue
            chosen[w] = dict(ids=[f"doi:{r['doi'].lower()}"], source='jstor-index', basis=r['basis'], title=r['js_title'],
                             year=intor(r['js_year']), kind=ecw.oa_kind(r['js_type']), container=r['js_journal'])
    if (S / 'cm-crosswalk.csv.gz').exists():     # Crossref metadata harvest (crmeta stage): last; review-like dropped
        for r in rd(S / 'cm-crosswalk.csv.gz'):
            w = r['work_id']
            if w in chosen:
                R['crossref_meta_also_' + chosen[w]['source']] += 1
                continue
            if r['review_like'] == '1':
                R['crossref_meta_review_like_dropped'] += 1
                held.append((w, 'crossref-meta', 'review_like', forms[w][5], f"doi:{r['doi'].lower()}", r['cr_title'][:150]))
                continue
            chosen[w] = dict(ids=[f"doi:{r['doi'].lower()}"], source='crossref-meta', basis=r['basis'], title=r['cr_title'],
                             year=intor(r['cr_year']), kind=ecw.cr_kind(r['cr_type']), container=r['cr_journal'])
            R['crossref_meta_used'] += 1
    for src, fn in (('openalex', 'oa-held.csv.gz'), ('crossref', 'cr-held.csv.gz'), ('jstor-index', 'js-held.csv.gz'),
                    ('crossref-meta', 'cm-held.csv.gz')):
        if not (S / fn).exists():
            continue
        for h in rd(S / fn):
            if h['work_id'] not in chosen:
                held.append((h['work_id'], src, h['reason'], forms[h['work_id']][5], '', ''))
    log('chosen forms', len(chosen), Counter(v['source'] for v in chosen.values()))

    # ---- ids: the key-log key when the log holds an identifier, else the dissertation layer's unkeyed id, else ours
    import pyarrow as pa
    allids = sorted({x for v in chosen.values() for x in v['ids']})
    c.register('ids_arrow', pa.table({'id': allids}))
    amap = defaultdict(list)
    for a_, key, res in c.execute(f"""SELECT a, key, resolution FROM (SELECT key, resolution, unnest(anchors) a
            FROM '{GRAPH}/work.parquet') WHERE a IN (SELECT id FROM ids_arrow)""").fetchall():
        amap[a_].append((res == 'unkeyed', key))
    for v in chosen.values():
        hits = sorted({h for x in v['ids'] for h in amap.get(x, [])})
        if hits:
            v['cid'] = hits[0][1]
            v['held_by'] = 'key' if not hits[0][0] else 'unkeyed_layer'
            if len({k for u, k in hits if not u}) > 1:
                R['several_keys_first_taken'] += 1
        else:
            wid = v['ids'][0]
            if wid.startswith('openalex:') and any(x.startswith('doi:') for x in v['ids']):
                wid = next(x for x in v['ids'] if x.startswith('doi:'))
            v['cid'] = wid
            v['held_by'] = 'new'
    # forms whose identifiers overlap are one cited work (as export_cited_works): union by shared id
    uf = ecw.UF()
    for v in chosen.values():
        for x in v['ids']:
            uf.union(v['cid'], x)
    comp = {}
    for v in chosen.values():
        root = uf.find(v['cid'])
        if root not in comp or (v['held_by'] != 'new', ) > (comp[root]['held_by'] != 'new', ):
            comp[root] = v
    for v in chosen.values():
        v['cid'] = comp[uf.find(v['cid'])]['cid']
    R['cited_works'] = len({v['cid'] for v in chosen.values()})
    pq_write(S / 'chosen.parquet', [dict(form=w, cid=v['cid'], source=v['source'], basis=v['basis'], held_by=v['held_by'],
                                         title=v['title'], year=v['year'], kind=v['kind'], container=v.get('container') or '',
                                         author=v.get('author') or '', author_uri=v.get('author_uri') or '',
                                         initial=v.get('initial') or '', year_fit=v.get('year_fit') or '',
                                         ids=';'.join(v['ids'])) for w, v in chosen.items()])
    finish(a, c, S, out, chosen, held, R)


def pq_write(path, rows):
    import pyarrow as pa
    import pyarrow.parquet as pq
    keys = list(rows[0])
    pq.write_table(pa.table({k: [r[k] for r in rows] for k in keys}), path)


DECADE = "CASE WHEN {y} IS NULL THEN 'unknown' WHEN {y} < 1900 THEN 'pre-1900' ELSE ({y} // 10 * 10)::VARCHAR || 's' END"
SRC_RANK = {'lc-full': 0, 'crossref': 1, 'openalex': 2, 'jstor-index': 3, 'crossref-meta': 4}


def finish(a, c, S, out, chosen, held, R):
    import pyarrow as pa
    rep = {'note': ('rows = citation rows of the JSTOR rule parser (rules/part-*, textnotes-rules); a row that refers back '
                    '(Ibid., short form, author-date) counts for its full citation; citations = rows, pairs = distinct '
                    '(citing article, cited work); before = data/graph/jstor-cites.csv.gz as built into '
                    'build/graph/cites.parquet (source jstor, edition rows included); after = before + this crosswalk')}
    c.execute(f"CREATE OR REPLACE TABLE cls AS SELECT * FROM read_parquet('{S}/cls.parquet')")
    c.execute(f"CREATE OR REPLACE TABLE items AS SELECT * FROM read_parquet('{S}/items.parquet')")
    # citing keys: the item's DOI anchor in the graph
    c.execute(f"""CREATE OR REPLACE TABLE citing AS SELECT i.iid, i.year, i.itype,
          coalesce(k.wkey, CASE WHEN i.doi <> '' THEN 'doi:' || i.doi END, 'jstor:' || i.iid) citing,
          k.wkey IS NOT NULL keyed
        FROM items i LEFT JOIN (SELECT substr(a, 5) doi, min(key) AS wkey FROM (SELECT key, unnest(anchors) a
             FROM '{GRAPH}/work.parquet' WHERE resolution <> 'unkeyed') WHERE a LIKE 'doi:%' GROUP BY 1) k ON k.doi = i.doi
        WHERE i.iid IN (SELECT DISTINCT iid FROM cls)""")
    c.execute(f"""CREATE OR REPLACE TABLE before AS SELECT "from" citing, "to" cited, bool_and(edition) edition
                  FROM '{GRAPH}/cites.parquet' WHERE list_contains(string_split(source, ','), 'jstor') GROUP BY 1, 2""")
    # (the source token 'jstor' exactly: since 2026-11-11 the build also carries 'jstor-matched', this table's own edges)
    # weights: rows pointing at each target row
    c.execute("""CREATE OR REPLACE TABLE wt AS SELECT iid, src, tgt idx, count(*) w,
                   count(*) FILTER (WHERE via_new_short) w_new_short FROM cls GROUP BY 1, 2, 3""")
    ch = [dict(form=w, cid=v['cid'], source=v['source'], basis=v['basis'], held_by=v['held_by']) for w, v in chosen.items()]
    c.register('ch_arrow', pa.table({k: [x[k] for x in ch] for k in ch[0]}))
    c.execute("CREATE OR REPLACE TABLE ch AS SELECT * FROM ch_arrow")
    c.execute(f"""CREATE OR REPLACE TABLE newrows AS SELECT fr.iid, fr.src, fr.idx, ch.*, wt.w, wt.w_new_short, ci.citing,
          ci.year cyear, ci.itype, cl.cls
        FROM read_parquet('{S}/form-rows.parquet') fr JOIN ch ON ch.form = fr.form
        JOIN wt USING (iid, src, idx) JOIN citing ci USING (iid)
        JOIN cls cl ON cl.iid = fr.iid AND cl.src = fr.src AND cl.idx = fr.idx""")
    # one cited work per pair; the best source (LC, Crossref, OpenAlex) names the pair's source and basis
    c.execute("""CREATE OR REPLACE TABLE newpairs AS SELECT citing, cid, sum(w)::INT AS citations,
          arg_min(source, CASE source WHEN 'lc-full' THEN 0 WHEN 'crossref' THEN 1 WHEN 'openalex' THEN 2
                                      WHEN 'jstor-index' THEN 3 ELSE 4 END) AS source,
          arg_min(basis, CASE source WHEN 'lc-full' THEN 0 WHEN 'crossref' THEN 1 WHEN 'openalex' THEN 2
                                     WHEN 'jstor-index' THEN 3 ELSE 4 END) AS basis,
          any_value(held_by) AS held_by, count(DISTINCT iid) AS iids,
          bool_and(cls = 'short_attemptable') AS only_short, bool_or(cls = 'matched_ambiguous') AS from_ambiguous
        FROM newrows GROUP BY 1, 2""")
    c.execute("""CREATE OR REPLACE TABLE np AS SELECT n.*, b.cited IS NOT NULL in_before, b.edition before_edition
                 FROM newpairs n LEFT JOIN before b ON b.citing = n.citing AND b.cited = n.cid""")
    R['pairs_matched_here'] = c.execute('select count(*) from np').fetchone()[0]
    R['pairs_already_in_jstor_cites'] = c.execute('select count(*) from np where in_before').fetchone()[0]
    R['pairs_new'] = c.execute('select count(*) from np where not in_before').fetchone()[0]
    R['citing_self_dropped'] = c.execute('select count(*) from np where citing = cid').fetchone()[0]
    c.execute("DELETE FROM np WHERE citing = cid")
    c.execute(f"COPY newrows TO '{S}/newrows.parquet' (FORMAT parquet)")
    c.execute(f"COPY np TO '{S}/np.parquet' (FORMAT parquet)")

    # ---- outputs ------------------------------------------------------------------------------------------------
    rows = c.execute("""SELECT citing, cid, source, basis, citations, in_before, held_by FROM np
                        ORDER BY citing, cid""").fetchall()
    write_rows(out / 'crosswalk.csv.gz', ['citing_work', 'cited_work', 'source', 'basis', 'citations', 'in_jstor_cites',
                                          'cited_held_by'], rows)
    wk = {}
    for w, v in chosen.items():
        x = wk.get(v['cid'])
        if x is None or SRC_RANK[v['source']] < SRC_RANK[x['source']]:
            wk[v['cid']] = v
    cnt = dict(c.execute('SELECT cid, count(DISTINCT citing) FROM np GROUP BY 1').fetchall())
    write_rows(out / 'works.csv.gz', ['id', 'catalogue_title', 'year', 'kind', 'container', 'identifiers', 'source', 'basis',
                                      'held_by', 'lc_author_heading', 'lc_author_uri', 'citing_articles'],
               sorted(([k, v['title'], v['year'] or '', v['kind'], v.get('container') or '', ';'.join(v['ids']), v['source'],
                        v['basis'], v['held_by'], v.get('author') or '', v.get('author_uri') or '', cnt.get(k, 0)]
                       for k, v in wk.items() if cnt.get(k)), key=lambda r: (-r[-1], r[0])))
    held.sort(key=lambda h: (-h[3], h[0]))
    write_rows(out / 'held.csv.gz', ['form_id', 'source', 'reason', 'citing_articles', 'candidate_ids', 'candidate_catalogue_title'],
               held)
    hc = Counter()
    for h in held:
        hc[f'{h[1]} / {h[2]}'] += 1
    rep['held'] = dict(hc.most_common())

    # ---- denominator ----------------------------------------------------------------------------------------------
    eff = "CASE WHEN cls = 'repeat' THEN coalesce(tcls, 'repeat_of_unknown') ELSE cls END"
    grp = (f"CASE WHEN {eff} = 'matched' THEN 'a_matched' WHEN {eff} IN {ATTEMPT} THEN 'b_attemptable' "
           "ELSE 'c_not_attemptable' END")
    newset = "(SELECT DISTINCT iid, src, idx FROM newrows)"
    c.execute(f"""CREATE OR REPLACE TABLE den AS SELECT cl.*, {eff} eff, {grp} grp,
          (cl.tgt = cl.idx) is_full, n.iid IS NOT NULL now_matched
        FROM cls cl LEFT JOIN {newset} n ON n.iid = cl.iid AND n.src = cl.src AND n.idx = cl.tgt""")

    def tab(by, where='true'):
        out_ = {}
        for g, grp_, rows_, full, now in c.execute(f"""SELECT {by} g, grp, count(*), count(*) FILTER (WHERE is_full),
                count(*) FILTER (WHERE now_matched) FROM den WHERE {where} GROUP BY 1, 2 ORDER BY 1, 2""").fetchall():
            d = out_.setdefault(str(g), {})
            d[grp_] = dict(rows=rows_, full_citations=full, rows_matched_now=now)
        return out_
    rep['denominator'] = dict(
        by_class={k: dict(rows=r, full_citations=f) for k, r, f in c.execute(
            "SELECT eff, count(*), count(*) FILTER (WHERE is_full) FROM den GROUP BY 1 ORDER BY 2 DESC").fetchall()},
        groups=tab("'all'")['all'],
        by_item_type=tab('itype'),
        by_decade=tab(DECADE.format(y='cyear')),
        repeats=dict(c.execute("""SELECT CASE WHEN via_new_short THEN 'short form resolved here' ELSE 'resolved by the parser' END,
                                   count(*) FROM den WHERE cls = 'repeat' GROUP BY 1""").fetchall()),
        note=('a_matched = the earlier matcher found and the export kept a graph work; b_attemptable = parsed with an '
              'author and a usable title and not exported (unmatched, matched only ambiguously, or an unresolved short '
              'form of 3+ title words); c = archival/primary, Ibid./author-date with nothing to resolve to, fragments '
              '(no author or no title), unparsed or commentary, titles too short, newspapers/periodicals, web. Rows '
              'that refer back count in the group of their full citation. Book-review items are counted but never '
              'matched (they give no citations).'))
    short = c.execute("""SELECT d.tcls, count(*), count(*) FILTER (WHERE d.now_matched) FROM den d
                         WHERE d.via_new_short GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    rep['short_form_resolution'] = dict(
        rows_resolved_here=sum(x[1] for x in short),
        by_target_class={k: dict(rows=n, target_matched_now=m) for k, n, m in short},
        direct_short_form_matches=c.execute("""SELECT count(*), count(DISTINCT (iid, cid)) FROM newrows
                                                WHERE cls = 'short_attemptable'""").fetchone(),
        pairs_only_from_short_forms_new=c.execute('SELECT count(*) FROM np WHERE only_short AND NOT in_before').fetchone()[0],
        citations_added_to_already_matched_pairs=c.execute(
            "SELECT count(*) FROM den WHERE via_new_short AND tcls = 'matched'").fetchone()[0])

    # ---- before / after --------------------------------------------------------------------------------------------
    c.execute("""CREATE OR REPLACE TABLE per AS SELECT ci.iid, ci.citing, ci.year, ci.itype,
          coalesce(b.pairs, 0) before_pairs, coalesce(n.pairs, 0) new_pairs, coalesce(n.cites, 0) new_cites
        FROM citing ci
        LEFT JOIN (SELECT citing, count(*) pairs FROM before GROUP BY 1) b USING (citing)
        LEFT JOIN (SELECT citing, count(*) pairs, sum(citations) cites FROM np WHERE NOT in_before GROUP BY 1) n USING (citing)""")
    c.execute(f"""CREATE OR REPLACE TABLE rowsum AS SELECT iid, count(*) FILTER (WHERE grp = 'a_matched') before_rows,
          count(*) FILTER (WHERE grp = 'a_matched' OR now_matched) after_rows, count(*) all_rows FROM den GROUP BY 1""")

    def ba(by, where="itype <> 'review'"):
        o = {}
        for g, arts, bp, ap, br, ar, allr, mb, ma, mb1, ma1 in c.execute(f"""SELECT {by} g, count(*), sum(before_pairs),
                sum(before_pairs + new_pairs), sum(before_rows), sum(after_rows), sum(all_rows),
                median(before_pairs), median(before_pairs + new_pairs),
                median(before_pairs) FILTER (WHERE before_pairs > 0), median(before_pairs + new_pairs) FILTER (WHERE before_pairs + new_pairs > 0)
              FROM per JOIN rowsum USING (iid) WHERE {where} GROUP BY 1 ORDER BY 1""").fetchall():
            o[str(g)] = dict(articles=arts, pairs_before=int(bp), pairs_after=int(ap), rows=int(allr),
                             rows_matched_before=int(br), rows_matched_after=int(ar),
                             row_rate_before=round(br / allr, 4) if allr else None, row_rate_after=round(ar / allr, 4) if allr else None,
                             median_pairs_per_article_before=mb, median_pairs_per_article_after=ma,
                             median_pairs_before_matched_articles=mb1, median_pairs_after_matched_articles=ma1)
        return o
    rep['before_after'] = dict(
        all=ba("'all'")['all'], by_item_type=ba('itype', 'true'), by_decade=ba(DECADE.format(y='year')),
        mean_pairs_per_article=c.execute("""SELECT round(avg(before_pairs), 2), round(avg(before_pairs + new_pairs), 2),
            round(avg(before_pairs) FILTER (WHERE before_pairs > 0), 2),
            round(avg(before_pairs + new_pairs) FILTER (WHERE before_pairs + new_pairs > 0), 2)
            FROM per WHERE itype <> 'review'""").fetchone(),
        mean_note='[all non-review items with parsed notes before, after; items with 1+ match before, after]',
        citing_keyed=c.execute("SELECT keyed, count(*) FROM citing GROUP BY 1").fetchall())
    rep['new_by_source_basis'] = {f'{s} | {b}': dict(pairs=p, citations=int(n), cited_works=w) for s, b, p, n, w in c.execute(
        """SELECT source, basis, count(*), sum(citations), count(DISTINCT cid) FROM np WHERE NOT in_before
           GROUP BY 1, 2 ORDER BY 3 DESC""").fetchall()}
    rep['new_by_source'] = {s: dict(pairs=p, citations=int(n), cited_works=w) for s, p, n, w in c.execute(
        "SELECT source, count(*), sum(citations), count(DISTINCT cid) FROM np WHERE NOT in_before GROUP BY 1 ORDER BY 2 DESC").fetchall()}
    rep['new_by_cited_held_by'] = dict(c.execute(
        "SELECT source || ' | ' || held_by, count(*) FROM np WHERE NOT in_before GROUP BY 1 ORDER BY 2 DESC").fetchall())
    rep['new_from_previously_ambiguous_rows'] = c.execute(
        "SELECT count(*) FROM np WHERE NOT in_before AND from_ambiguous").fetchone()[0]
    canon(c, rep, chosen)
    audit = Path(a.audit) / 'audit-summary.json'
    if audit.exists():                    # counts only (the sample itself, with note text, stays in build/)
        rep['audit'] = json.loads(audit.read_text())
    audit2 = ROOT / 'build/jstor-cited-audit-crmeta-2026-11-11/audit-summary.json'
    if audit2.exists():                   # the Crossref metadata route's audit (crmeta stage)
        rep['audit_crossref_meta'] = json.loads(audit2.read_text())
    rep['counts'] = dict(sorted(R.items()))
    (out / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n')
    log(json.dumps(rep['before_after']['all']), json.dumps(rep['counts']))


def canon(c, rep, chosen):
    """Top works and authors by citing articles gained, and the JSTOR-side canon before/after."""
    import pyarrow as pa
    c.execute(f"""CREATE OR REPLACE TABLE wl AS SELECT key, label, year, kind FROM '{GRAPH}/work.parquet'""")
    wk = {}
    for v in chosen.values():
        x = wk.get(v['cid'])
        if x is None or SRC_RANK[v['source']] < SRC_RANK[x['source']]:
            wk[v['cid']] = v
    ids = list(wk)
    c.register('wk_arrow', pa.table(dict(cid=ids, title=[wk[k]['title'] for k in ids], year=[wk[k]['year'] for k in ids],
                                         source=[wk[k]['source'] for k in ids], heading=[wk[k].get('author') or '' for k in ids],
                                         uri=[(wk[k].get('author_uri') or '').rsplit('/', 1)[-1] for k in ids])))
    c.execute("CREATE OR REPLACE TABLE wk AS SELECT * FROM wk_arrow")
    c.execute("""CREATE OR REPLACE TABLE after AS SELECT citing, cited FROM before
                 UNION SELECT citing, cid FROM np WHERE NOT in_before""")
    # people of a cited work: keyed authors/editors (authored/edited), else the LC heading (its authority's key if any)
    # authors; editors only for works with no author (a key pooling editions of Smith's Wealth of Nations carries its
    # editors Campbell, Skinner, Lerner, McCulloch: they are not the cited author)
    c.execute(f"""CREATE OR REPLACE TABLE wp AS
        SELECT "to" AS work, "from" AS person FROM {keylog(GRAPH, 'authored')}
        UNION SELECT "to", "from" FROM {keylog(GRAPH, 'edited')}
          WHERE "to" NOT IN (SELECT "to" FROM {keylog(GRAPH, 'authored')})""")
    c.execute(f"""CREATE OR REPLACE TABLE lcp AS SELECT wk.cid AS work, coalesce(p.key, 'lc-heading:' || wk.heading) AS person
        FROM wk LEFT JOIN '{GRAPH}/person.parquet' p ON wk.uri <> '' AND p.lcnaf = wk.uri
        WHERE wk.heading <> '' AND wk.cid NOT IN (SELECT work FROM wp)""")
    c.execute("CREATE OR REPLACE TABLE wpp AS SELECT * FROM wp UNION SELECT * FROM lcp")
    c.execute(f"CREATE OR REPLACE TABLE pl AS SELECT key, label FROM '{GRAPH}/person.parquet'")

    def label_sql(x):
        return f"coalesce((SELECT label FROM wl WHERE key = {x}), (SELECT title FROM wk WHERE cid = {x}))"
    top_w = c.execute(f"""WITH g AS (SELECT cid, count(DISTINCT citing) gained, any_value(source) AS source FROM np
                                     WHERE NOT in_before GROUP BY 1),
                         b AS (SELECT cited, count(DISTINCT citing) n FROM before GROUP BY 1)
        SELECT g.cid, {label_sql('g.cid')}, coalesce((SELECT year FROM wl WHERE key = g.cid), (SELECT year FROM wk WHERE cid = g.cid)),
               g.source, coalesce(b.n, 0), g.gained
        FROM g LEFT JOIN b ON b.cited = g.cid ORDER BY gained DESC, cid LIMIT 100""").fetchall()
    rep['top_works_gained'] = [dict(work=k, title=t, year=y, source=s, citing_before=b, citing_gained=n)
                               for k, t, y, s, b, n in top_w]
    top_a = c.execute("""WITH bb AS (SELECT p.person, count(DISTINCT b.citing) n FROM before b JOIN wpp p ON p.work = b.cited GROUP BY 1),
             aa AS (SELECT p.person, count(DISTINCT a.citing) n FROM after a JOIN wpp p ON p.work = a.cited GROUP BY 1)
        SELECT aa.person, coalesce((SELECT label FROM pl WHERE key = aa.person), replace(aa.person, 'lc-heading:', '')),
               coalesce(bb.n, 0), aa.n, aa.n - coalesce(bb.n, 0) g
        FROM aa LEFT JOIN bb USING (person) ORDER BY g DESC, aa.person LIMIT 100""").fetchall()
    rep['top_authors_gained'] = [dict(person=k, label=l, citing_before=b, citing_after=a_, gained=g) for k, l, b, a_, g in top_a]

    def ranks(table, unit_sql, n=50):
        return c.execute(f"""SELECT unit, n, rank() OVER (ORDER BY n DESC) r FROM (
            SELECT {unit_sql} unit, count(DISTINCT citing) n FROM {table} x GROUP BY 1) ORDER BY n DESC, unit""").fetchall()
    for name, unit, table_b, table_a, lab in (
            ('works', 'cited', 'before', 'after', label_sql),
            ('authors', 'person', '(SELECT b.citing, p.person FROM before b JOIN wpp p ON p.work = b.cited)',
             '(SELECT a.citing, p.person FROM after a JOIN wpp p ON p.work = a.cited)',
             lambda x: f"coalesce((SELECT label FROM pl WHERE key = {x}), replace({x}, 'lc-heading:', ''))")):
        rb = {u: (n, r) for u, n, r in ranks(table_b, unit)}
        ra = ranks(table_a, unit)
        top = []
        for u, n, r in ra[:60]:
            lb = c.execute(f"SELECT {lab('$1')}", [u]).fetchone()[0]
            b = rb.get(u, (0, None))
            top.append(dict(unit=u, label=lb, citing_after=n, rank_after=r, citing_before=b[0], rank_before=b[1]))
        rep[f'canon_{name}_top60_after'] = top
        ra_rank = {u: r for u, n, r in ra}
        risers = sorted(((rb.get(u, (0, 10 ** 6))[1] - ra_rank[u], u) for u, n, r in ra[:200]), reverse=True)[:25]
        rep[f'canon_{name}_biggest_risers_into_top200'] = [
            dict(unit=u, label=c.execute(f"SELECT {lab('$1')}", [u]).fetchone()[0], rank_before=rb.get(u, (0, None))[1],
                 rank_after=ra_rank[u]) for _, u in risers]
        tb = {u for u, n, r in ranks(table_b, unit)[:100]}
        ta = {u for u, n, r in ra[:100]}
        rep[f'canon_{name}_top100_overlap'] = len(tb & ta)


# ------------------------------------------------------------------------------------------------ audit

def stratum(source, basis, initials, initial, year_fit, cls, how):
    """Audit strata: the riskier branches each get their own stratum, the first that applies."""
    if cls == 'short_attemptable':
        return f'{source} | short form'
    if how and 'lead_given' in how:
        return f'{source} | given name cut from the title'
    if source == 'lc-full':
        tf, nf = basis.split('/')[:2]
        if initial in ('differ', 'unknown'):
            return f'lc | initial {initial}'
        if year_fit == 'before':
            return 'lc | cited year before LC'
        if tf not in ('exact', 'whole'):
            return 'lc | comma title forms'
        if nf != 'main':
            return 'lc | added/editor/resp heading'
        return 'lc | exact-whole main, ' + ('initials only' if initials else 'given name spelled')
    if basis in ('whole_title', 'main_title'):
        return f'{source} | {basis}'
    return f'{source} | other bases'


def cmd_audit(a):
    """A stratified sample of new pairs (not in jstor-cites) with the note piece and the catalogue record, for a hand
    check. Writes <audit>/sample.csv (note text: build/ only, never data/). `--n` rows in all (default 250)."""
    import key_cited_works_lc_full as lcf
    import random
    S = Path(a.scratch)
    A = Path(a.audit)
    A.mkdir(parents=True, exist_ok=True)
    c = connect(S)
    rows = c.execute(f"""SELECT n.iid, n.src, n.idx, n.form, n.cid, n.source, n.basis, n.held_by, n.cls, n.citing, r.note,
            f.kind, f.title, f.authors, f.year, f.container, ch.title, ch.year, ch.author, ch.ids, ch.container, ch.kind,
            ch.initial, ch.year_fit, r.kind, r.title, r.authors
        FROM read_parquet('{S}/newrows.parquet') n JOIN read_parquet('{S}/np.parquet') p
             ON p.citing = n.citing AND p.cid = n.cid AND NOT p.in_before AND p.source = n.source
        JOIN read_parquet('{S}/rows.parquet') r ON r.iid = n.iid AND r.src = n.src AND r.idx = n.idx
        JOIN read_parquet('{S}/forms.parquet') f ON f.work_id = n.form
        JOIN read_parquet('{S}/chosen.parquet') ch ON ch.form = n.form""").fetchall()
    log('candidate rows', len(rows))
    by = defaultdict(list)
    for r in rows:
        given = [lcf.parse_name(x)[1] for x in (r[13] or '').split(';') if x]
        initials = not any(len(w) > 1 for g in given for w in g)
        how = clean_form(r[24] or 'book', r[25] or '', [x for x in (r[26] or '').split(';') if x])[4] if r[25] else None
        by[stratum(r[5], r[6], initials, r[22], r[23], r[8], how)].append(r)
    rnd = random.Random(20261111)
    quota = {k: 0 for k in by}           # equal shares across strata, small strata give theirs away
    left = a.n
    while left > 0 and any(quota[k] < len(by[k]) for k in by):
        for k in sorted(by):
            if left and quota[k] < len(by[k]):
                quota[k] += 1
                left -= 1
    (A / 'strata.json').write_text(json.dumps({k: dict(new_rows=len(v), sampled=quota[k]) for k, v in sorted(by.items())}, indent=1))
    sample = []
    for k, v in sorted(by.items()):
        seen = set()
        rnd.shuffle(v)
        for r in v:
            if (r[4], r[9]) in seen:
                continue
            seen.add((r[4], r[9]))
            sample.append((k, r))
            if len(seen) >= min(quota[k], len(v)):
                break
    want = defaultdict(set)
    for k, r in sample:
        want[(r[0], r[1])].add(r[10])
    text = {}
    for fn, field, src in ((f'{E}/references.jsonl.gz', 'references', 'list'), (f'{E}/textnotes-pieces.jsonl.gz', 'pieces', 'text')):
        ids = {i for i, s in want if s == src}
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'\{"iid": "([^"]+)"', line)
                if not m or m.group(1) not in ids:
                    continue
                d = json.loads(line)
                for n in want[(d['iid'], src)]:
                    p = d[field][n] if n is not None and n < len(d[field]) else ''
                    text[(d['iid'], src, n)] = (p if isinstance(p, str) else json.dumps(p))[:700]
    with open(A / 'sample.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['n', 'stratum', 'verdict', 'why', 'iid', 'cited_work', 'source', 'basis', 'held_by', 'row_class',
                    'cited_kind', 'cited_authors', 'cited_title', 'cited_year', 'cited_container', 'note_piece',
                    'cat_title', 'cat_year', 'cat_author', 'cat_container', 'cat_ids'])
        for i, (k, r) in enumerate(sample):
            w.writerow([i + 1, k, '', '', r[0], r[4], r[5], r[6], r[7], r[8], r[11], r[13], r[12], r[14], r[15],
                        text.get((r[0], r[1], r[10]), ''), r[16], r[17], r[18], r[20], r[19][:200]])
    log('sample', len(sample), dict(Counter(k for k, _ in sample)))


# ------------------------------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd')
    ap.add_argument('--scratch', required=True)
    ap.add_argument('--out', default=str(ROOT / 'data/identifiers/jstor-cited-works-2026-11-11'))
    ap.add_argument('--audit', default=str(ROOT / 'build/jstor-cited-audit-2026-11-11'))
    ap.add_argument('--n', type=int, default=250)
    ap.add_argument('--crmeta', help='folder holding index/ of key_cited_works_crossref_meta.py index (crmeta stage)')
    ap.add_argument('--tmp', help='DuckDB temp folder (default the scratch folder)')
    a = ap.parse_args()
    _schema()
    globals()['TMP'] = a.tmp
    Path(a.scratch).mkdir(parents=True, exist_ok=True)
    globals()['cmd_' + a.cmd](a)


if __name__ == '__main__':
    main()
