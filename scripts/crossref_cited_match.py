#!/usr/bin/env python3
"""Job A (2026-11-17): match the held cited works without a DOI to the Crossref public data file (March 2026).

Runs on spark (6 threads, DuckDB 24 GB). Work folder /mnt/data/jic823/crossref-work-b/a.

  prep   Crossref works of matchable types -> crw.parquet (doi, type, titles, container, ISSN, ISBN, year,
         normalised main title nmain)
  block  target main-title tokens; document frequency of each over Crossref main titles; per target its rarest
         token (tok1) and second rarest (tok2); candidates = Crossref works holding tok1 (and tok2 when the target
         has one) whose type fits the target's kind -> cand.parquet; their contributors -> cand_auth.parquet
  score  python scoring of every candidate (title, subtitle, author family, year, container), one best per target
         with a margin, twins (same record under two DOIs) folded -> results.parquet

Kinds: book targets match Crossref book / monograph / edited-book / reference-book / book-set; article (and other
with a journal, review) match journal-article / proceedings-article; chapter matches book-chapter / book-section /
book-part; thesis matches dissertation; other without a journal matches the book and chapter types.

  python3 -I crossref_cited_match.py prep|block|score|all
"""
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crossref_names import fam_agree, families, main_title, norm_title, strip_leading  # noqa: E402

CR = '/mnt/data/jic823/crossref-2026-parquet'
W = '/mnt/data/jic823/crossref-work-b/a'
IN = '/mnt/data/jic823/crossref-work-b/in'
TYPES = {
    'book': ('book', 'monograph', 'edited-book', 'reference-book', 'book-set'),
    'article': ('journal-article', 'proceedings-article'),
    'chapter': ('book-chapter', 'book-section', 'book-part'),
    'thesis': ('dissertation',),
}
TYPES['other'] = TYPES['book'] + TYPES['chapter']
ALL_TYPES = sorted({t for v in TYPES.values() for t in v})
STOP = ("'the','a','an','le','la','les','l','der','die','das','el','los','las','il','lo','gli','o','os','as','un',"
        "'une','ein','eine','de','het','een','of','and','in','on','for','to','at','by','with','from','et','du','des',"
        "'en','und','im','zur','zum','von','del','di','da','do','dos','e','y','au','aux','its','his','her','their',"
        "'into','or','is'")


def con():
    db = duckdb.connect(f'{W}/work.duckdb')
    db.execute(f"set threads=6; set memory_limit='24GB'; set temp_directory='{W}/tmp'; set preserve_insertion_order=false")
    db.execute(r"""create or replace macro nt(t) as trim(regexp_replace(regexp_replace(regexp_replace(lower(strip_accents(
        replace(replace(replace(replace(replace(replace(replace(regexp_replace(coalesce(t,''), '<[^>]+>', ' ', 'g'),
        'ß','ss'),'æ','ae'),'œ','oe'),'ł','l'),'ø','o'),'đ','d'),'&amp;',' and '))), '&', ' and ', 'g'),
        '[''’`]', '', 'g'), '[^a-z0-9]+', ' ', 'g'))""")
    db.execute(r"""create or replace macro mt(t) as coalesce(nullif(regexp_extract(replace(regexp_replace(coalesce(t,''), '<[^>]+>', ' ', 'g'), '&amp;', '&'),
        '^(.*?)(\s*[:;]\s|\s*[:;]$|\s+=\s+|\s+/\s+|\.\s+[A-Za-z]|\s+[–—-]\s+|$)', 1), ''), t)""")
    db.execute(r"""create or replace macro sl(n) as regexp_replace(n, '^(the|a|an|le|la|les|l|der|die|das|el|los|las|il|lo|gli|o|os|as|un|une|ein|eine|de|het|een) ', '')""")
    return db


def prep():
    db = con()
    types = ','.join(f"'{t}'" for t in ALL_TYPES)
    t0 = time.time()
    db.execute(f"""copy (select doi, type, title, subtitle, container, issn, isbn, publisher, year, n_authors,
                   sl(nt(mt(title))) nmain
            from read_parquet('{CR}/works/*.parquet') where type in ({types}) and title is not null)
            to '{W}/crw.parquet' (format parquet, compression zstd, row_group_size 200000)""")
    print('crw', db.execute(f"select count(*) from '{W}/crw.parquet'").fetchone(), f'{time.time()-t0:.0f}s', flush=True)


def block():
    db = con()
    t0 = time.time()
    db.execute(f"""create or replace table tg as
        select key, kind, coalesce(least(year, first_year), year) y0, greatest(year, first_year) y1, journal, issn,
               sl(nt(mt(title))) nmain,
               case when kind='book' then 'book' when kind='chapter' then 'chapter' when kind='thesis' then 'thesis'
                    when kind in ('article','review') then 'article'
                    when kind='other' and journal is not null then 'article' else 'other' end cls
        from '{IN}/targets.parquet'""")
    db.execute(f"""create or replace table tt as
        select distinct key, tok from (select key, unnest(string_split(nmain, ' ')) tok from tg)
        where length(tok) >= 3 and tok not in ({STOP})""")
    db.execute(f"""create or replace table df as
        with v as (select distinct tok from tt)
        select tok, count(*) n from (select unnest(string_split(nmain, ' ')) tok from '{W}/crw.parquet')
        where tok in (select tok from v) group by tok""")
    print('df tokens', db.execute('select count(*) from df').fetchone(), f'{time.time()-t0:.0f}s', flush=True)
    db.execute("""create or replace table pick as
        select key, list(tok order by n, tok)[1] tok1, list(tok order by n, tok)[2] tok2, min(n) n1, count(*) ntok
        from tt join df using (tok) group by key""")
    # targets with no token in Crossref at all cannot match; targets whose tokens are all missing are counted
    print('picked', db.execute('select count(*), sum(n1) from pick').fetchone(), flush=True)
    db.execute(f"""create or replace table post as
        select doi, type, year, nmain, tok from (select doi, type, year, nmain,
               unnest(list_distinct(string_split(nmain, ' '))) tok from '{W}/crw.parquet')
        where tok in (select distinct tok1 from pick)""")
    print('postings', db.execute('select count(*) from post').fetchone(), f'{time.time()-t0:.0f}s', flush=True)
    cls_types = ' union all '.join(f"select '{c}' cls, '{t}' type" for c, ts in TYPES.items() for t in ts)
    db.execute(f"create or replace table ct as {cls_types}")
    db.execute(f"""create or replace table cand as
        select g.key, p.doi
        from tg g join pick k using (key) join post p on p.tok = k.tok1
        join ct on ct.cls = g.cls and ct.type = p.type
        where (k.tok2 is null or position(' ' || k.tok2 || ' ' in ' ' || p.nmain || ' ') > 0)
          and (g.cls = 'book' or g.y0 is null or p.year is null or p.year between g.y0 - 2 and g.y1 + 2)""")
    print('candidates', db.execute('select count(*), count(distinct key) from cand').fetchone(),
          f'{time.time()-t0:.0f}s', flush=True)
    db.execute(f"copy (select c.key, w.* exclude (nmain) from cand c join '{W}/crw.parquet' w using (doi)) to '{W}/cand.parquet' (format parquet)")
    db.execute(f"""copy (select a.doi, a.role, a.seq, a.given, a.family, a.name, a.orcid from read_parquet('{CR}/authors/*.parquet') a
              where a.doi in (select distinct doi from cand)) to '{W}/cand_auth.parquet' (format parquet)""")
    db.execute(f"copy (select * from pick) to '{W}/pick.parquet' (format parquet)")
    print('block done', f'{time.time()-t0:.0f}s', flush=True)


# ---------------------------------------------------------------- scoring
def tnorm(t):
    return strip_leading(norm_title(main_title(t or '')))


def sub_of(title, subtitle):
    """Normalised subtitle: Crossref's subtitle field, else the part of the title after the main title."""
    if subtitle:
        return norm_title(subtitle)
    t = title or ''
    m = main_title(t)
    return norm_title(t[len(m):]) if len(m) < len(t) else ''


def sub_rel(a, b):
    from rapidfuzz import fuzz
    if not a or not b:
        return 'missing'
    if a == b:
        return 'same'
    if a.startswith(b) or b.startswith(a) or fuzz.ratio(a, b) >= 90:
        return 'close'
    if fuzz.token_set_ratio(a, b) >= 85:
        return 'close'
    return 'differs'


def jnorm(j):
    return norm_title(j or '').replace('the ', '')


def score_one(args):
    from rapidfuzz import fuzz
    t, cands, auth = args
    tm = tnorm(t['title'])
    ts = sub_of(t['title'], None)
    tf = set(t['families'] or [])
    y0, y1 = t['y0'], t['y1']
    out = []
    for c in cands:
        cm = tnorm(c['title'])
        cs = sub_of(c['title'], c['subtitle'])
        if not tm or not cm:
            continue
        exact_t = tm == cm
        tsim = 100.0 if exact_t else fuzz.ratio(tm, cm)
        if tsim < 80:
            continue
        srel = sub_rel(ts, cs)
        cfam = set()
        crole = {}
        for a in auth.get(c['doi'], ()):
            for f in (families(f"{a['family']}, {a['given'] or 'x'}") if a['family'] else families(a['name'] or '')):
                cfam.add(f)
                crole.setdefault(f, a['role'])
        fam_hit = sorted(f for f in tf for g in cfam if fam_agree(f, g))
        auth_st = 'agree' if fam_hit else ('no-target-names' if not tf else 'no-crossref-names' if not cfam else 'differs')
        cy = c['year']
        if cy is None or y0 is None:
            dy, yst = None, 'unknown'
        elif y0 - 1 <= cy <= (y1 or y0) + 1:
            dy, yst = 0, 'same'
        elif cy > (y1 or y0) + 1:
            dy, yst = cy - (y1 or y0), 'later'
        else:
            dy, yst = cy - y0, 'earlier'
        jst = 'n/a'
        if t['cls'] == 'article':
            tj, cj = jnorm(t['journal']), jnorm(c['container'])
            ti = set((t['issn'] or '').replace(',', ' ').split())
            ci = set((c['issn'] or '').split())
            if ti and ci and ti & ci:
                jst = 'issn'
            elif tj and cj:
                jst = 'agree' if (tj == cj or fuzz.token_set_ratio(tj, cj) >= 90) else 'differs'
            else:
                jst = 'unknown'
        # class
        cls = None
        reason = []
        year_ok = yst == 'same' or (t['cls'] in ('book', 'other') and yst == 'later')
        if t['cls'] == 'article' and yst not in ('same', 'unknown'):
            year_ok = False
        if (exact_t and srel in ('same', 'missing') and auth_st == 'agree' and yst == 'same'
                and jst in ('n/a', 'issn', 'agree', 'unknown')):
            cls = 'exact'
        elif (tsim >= 92 and srel != 'differs' and auth_st == 'agree' and year_ok and jst != 'differs'):
            cls = 'strong'
        elif tsim >= 85 and srel != 'differs' and (auth_st == 'agree' or (yst == 'same' and jst in ('issn', 'agree'))):
            cls = 'weak'
        if cls is None:
            continue
        sc = tsim * 0.4 + {'same': 15, 'close': 10, 'missing': 5}.get(srel, 0) \
            + {'agree': 30, 'no-target-names': 0, 'no-crossref-names': 0}.get(auth_st, -30) \
            + {'same': 15, 'later': 5, 'unknown': 0}.get(yst, -10) + {'issn': 10, 'agree': 8, 'differs': -10}.get(jst, 0) \
            + (2 if c['type'] in ('book', 'monograph', 'journal-article', 'book-chapter') else 0)
        flags = []
        if yst == 'later' and t['cls'] in ('book', 'other'):
            flags.append('edition-or-reprint')
        if yst == 'earlier':
            flags.append('crossref-earlier')
        if srel == 'close':
            flags.append('subtitle-close')
        out.append(dict(key=t['key'], doi=c['doi'], cls=cls, score=round(sc, 1), tsim=round(tsim, 1), sub=srel,
                        author=auth_st, fam_hit='|'.join(fam_hit), year=yst, dy=dy, journal=jst, flags=flags,
                        cr_type=c['type'], cr_title=c['title'], cr_subtitle=c['subtitle'], cr_year=cy,
                        cr_container=c['container'], cr_publisher=c['publisher'], cr_isbn=c['isbn'],
                        nm=cm, ns=cs, cfam='|'.join(sorted(cfam))))
    if not out:
        return []
    rank = {'exact': 3, 'strong': 2, 'weak': 1}
    out.sort(key=lambda r: (rank[r['cls']], r['score']), reverse=True)
    best = out[0]
    # twins: the same record under another DOI (same main title, subtitle and family set; for articles year within 1;
    # for books any year: other editions of the work, the best year kept, the rest listed)
    def twin(r):
        return (r['nm'] == best['nm'] and (r['ns'] == best['ns'] or not r['ns'] or not best['ns'])
                and r['cfam'] == best['cfam']
                and (t['cls'] in ('book', 'other') or r['cr_year'] is not None and best['cr_year'] is not None
                     and abs(r['cr_year'] - best['cr_year']) <= 1))
    twins = [r for r in out[1:] if twin(r)]
    rest = [r for r in out[1:] if not twin(r)]
    best['twins'] = '|'.join(r['doi'] for r in twins)
    run = rest[0] if rest else None
    best['runner_up'] = run['doi'] if run else None
    best['runner_cls'] = run['cls'] if run else None
    best['runner_score'] = run['score'] if run else None
    margin_ok = run is None or rank[best['cls']] > rank[run['cls']] or best['score'] - run['score'] >= 8
    best['margin_ok'] = margin_ok
    best['n_cands'] = len(out)
    return [best]


def score():
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = con()
    t0 = time.time()
    tg = {r[0]: dict(key=r[0], cls=r[1], y0=r[2], y1=r[3], journal=r[4], issn=r[5]) for r in
          db.execute('select key, cls, y0, y1, journal, issn from tg').fetchall()}
    for k, title, fams, german, cited, kind in db.execute(
            f"select key, title, families, german, cited, kind from '{IN}/targets.parquet'").fetchall():
        tg[k].update(title=title, families=fams, german=german, cited=cited, kind=kind)
    # prefilter in SQL: keep a candidate only if its main title can reach rapidfuzz ratio 80 with the target's
    # (Levenshtein <= 0.2 * (len a + len b) is a superset of indel ratio >= 80)
    db.execute(f"""create or replace table cf as
        select c.key, c.doi, c.type, c.title, c.subtitle, c.container, c.issn, c.isbn, c.publisher, c.year,
               hash(c.key) % 12 part
        from '{W}/cand.parquet' c join tg g using (key)
        where sl(nt(mt(c.title))) = g.nmain
           or levenshtein(sl(nt(mt(c.title))), g.nmain) <= 0.2 * (length(sl(nt(mt(c.title)))) + length(g.nmain))""")
    print('prefiltered', db.execute('select count(*), count(distinct key) from cf').fetchone(), f'{time.time()-t0:.0f}s', flush=True)
    db.execute(f"""create or replace table ca as select doi, role, given, family, name from '{W}/cand_auth.parquet'
                   where role in ('author','editor') and doi in (select doi from cf)""")
    res = []
    for part in range(12):
        cands = defaultdict(list)
        cur = db.execute(f"select key, doi, type, title, subtitle, container, issn, isbn, publisher, year from cf where part = {part}")
        names = [d[0] for d in cur.description]
        for r in cur.fetchall():
            d = dict(zip(names, r))
            cands[d['key']].append(d)
        auth = defaultdict(list)
        for doi, role, given, family, name in db.execute(
                f"select * from ca where doi in (select doi from cf where part = {part})").fetchall():
            auth[doi].append(dict(role=role, given=given, family=family, name=name))
        jobs = [(tg[k], cs, {c['doi']: auth.get(c['doi'], []) for c in cs}) for k, cs in cands.items()]
        del cands, auth
        with Pool(6) as pool:
            for r in pool.imap_unordered(score_one, jobs, chunksize=200):
                res.extend(r)
        print('part', part, len(jobs), 'targets; results so far', len(res), f'{time.time()-t0:.0f}s', flush=True)
        del jobs
    for r in res:
        t = tg[r['key']]
        r.update(german=t['german'], cited=t['cited'], kind=t['kind'], t_title=t['title'], t_year=t['y0'],
                 t_families='|'.join(t['families'] or []), t_journal=t['journal'])
        r['flags'] = ';'.join(r['flags'])
        r.pop('nm'); r.pop('ns')
    pq.write_table(pa.Table.from_pylist(res), f'{W}/results.parquet', compression='zstd')
    print('results', len(res), f'{time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    os.makedirs(f'{W}/tmp', exist_ok=True)
    cmd = sys.argv[1]
    for step in (('prep', 'block', 'score') if cmd == 'all' else (cmd,)):
        globals()[step]()
