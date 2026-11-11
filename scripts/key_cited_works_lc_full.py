"""Cited books -> the whole LC 2016 book file, for books the key-log crosswalks miss (2026-11-10). Writes a crosswalk.

key_cited_works.py matches a cited book only to LC books already in the key log, that is books whose author
already holds a person key. This script matches the rest of the corpus's cited books (kinds book, book_or_serial,
unstyled, edited_book, thesis_or_book that none of the three existing crosswalks match) against every record in
the offline index of MDSConnect Books All 2016 (scripts/lc_bib_index.py; /mnt/e/lc-bib-2016/index). It writes a
standalone crosswalk beside the log; nothing here is a key-log event, and nothing is minted.

The rule, in the spirit of key_cited_works.py: a cited book is an LC record when one of its listed authors'
family name agrees with the record's and its main title agrees with the record's. Titles are normalised as
key_lc_works.title_key does (accents, apostrophes and punctuation dropped, '&' read as 'and', leading articles
dropped, first ten words), done in SQL here so that both sides go through the same function. Family names are
compared with spaces and hyphens taken out ('De Groot' = 'DeGroot', 'Formanek-Brunell' = 'Formanek Brunell'),
'ae', 'oe', 'ue' read as umlauts ('Koepping' = 'Köpping'). A cited name is parsed as 'Family, Given', 'FAMILY
(Given)', capitalised family words ('- BADINTER Elisabeth'), else the last word. When no whole family name agrees,
a variant may, with the cited initial agreeing (column `name` = variant): the name without leading particles
('Von Greyerz' = 'Greyerz, Kaspar von'), or the first or last word of a compound ('McCall-Newman' = 'McCall',
'Stedman Jones' = 'Jones', LC's 'Wu Hung' = 'Wu').

Title forms, tried in this order; the first that finds any record decides (`basis`, first part):
- `exact`: the cited main title (before the first colon) = the record's 245 $a;
- `whole`: the cited whole title = the record's 245 $a or its $a+$b ('Carl Schurz, a Biography' as cited);
- `lc-comma`: the cited main title = the record's 245 $a up to its first comma, semicolon or '=': records
  before about 1980 put the subtitle after a comma inside $a ('British Columbia, a history', 1958);
- `corpus-comma`: the cited main title up to its first comma or semicolon = the record's 245 $a;
- `both-comma`: both cut at the first comma ('The Crisis of Quebec, 1914-1918' = 'The crisis of Quebec, 1914-18').

Name forms (`basis`, second part), headings before the statement of responsibility:
- `main`: the record's main entry (100);
- `added`: an added entry (700) with an author relator, or without a relator;
- `editor`: an added entry with an editor or compiler relator, or without one where the statement of
  responsibility speaks of editing; other relators (translator, illustrator, former owner) are not used;
- `resp`: no heading carries the family name, but the statement of responsibility (245 $c) names the cited
  author, family name preceded within four words by the cited given name ('Miriam Formanek-Brunell' where LC's
  heading is 'Forman-Brunell, Miriam'); only for cited authors with a given name, titles of two words or more,
  and the exact and whole title forms.

Records found are clustered: records whose matched person (family name and first initial) agree are editions of
one work, and people who share a record are one cluster (a book by Trentmann and Just, both cited, is one work,
not two; an earlier draft held every such co-authored book). One match carries all the cluster's LCCNs, with the earliest year as the work's year (`single` or
`editions`). Several clusters (different people of one family name, or translations credited differently) are
chosen between by the cited whole title (`whole-chosen`) when exactly one cluster has it; otherwise the book
is held. Choosing by a record within two years of the cited year, and by the cited initial alone, were tried and
dropped after the audit (3 wrong in 16 and 3 wrong in 12). Manuscript-collection records ('mm' control numbers) are left out.

Guards, from the audit of 2026-11-10 (audit-sample.csv in the output folder), applied to each candidate record
before the title form is chosen:
- the comma forms need a main title of two words or more and the cited initial equal to the LC heading's
  (an earlier draft matched 'Freedom', 'Cultura' and 'New York, 1966' to other people's books), never the
  statement of responsibility, and `lc-comma` skips collections ('O alienista, e outras histórias');
- a one-word title ('Anais', 'Diefenbaker') needs agreeing initials and the main entry, or subtitles that agree
  for three words or more ('Les hygiénistes: enjeux, modèles et pratiques');
- a match on the part before a comma (`lc-comma`, `both-comma`) whose records differ after it is held
  (volumes, or two books by one person: 'Medical services, general history' / '..., casualties ...');
- a title key of ten words (the cut) needs the longer titles to agree word for word as far as both go
  (Faider's catalogues of the Mons and the Courtrai libraries share their first ten words);
- the statement-of-responsibility route needs a family name of three letters or more and, when the citation
  spells out the given name, that word within four words before the family name;
- a cited 'title' that is an imprint ('São Paulo: Edusp, 2002') with three words or fewer before the colon
  is skipped.

Two flags go beside the basis for the audit: `initial` (agree / differ / unknown: the cited author's given
initial against the matched LC heading's) and `year_fit` (ok / before: the cited year is more than two years
before LC's earliest record of the work).

The author heading is resolved to an LC name authority (personal-names.parquet) when its text is the authorised
heading of exactly one live authority, or the heading with an open date span the authority has since closed, or
a former authorised form kept as a variant with the same family name and dates.

    python3 scripts/key_cited_works_lc_full.py --out data/identifiers/cited-works-lc-full-2026-11-10 \\
        --work /tmp/.../scratchpad/lcfull
"""
import argparse
import csv
import gzip
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
CROSSWALKS = ['data/identifiers/cited-works-2026-11-04', 'data/identifiers/cited-articles-2026-11-03b',
              'data/identifiers/cited-own-works-2026-11-03f']
KINDS = ('book', 'book_or_serial', 'unstyled', 'edited_book', 'thesis_or_book')
AUTHOR = ('author', 'joint author', 'aut', 'joint aut', 'co-author', 'coauthor', 'jt. auth', 'jt auth', 'jt. author',
          'supposed author', 'creator')
EDITOR = ('ed', 'editor', 'joint ed', 'joint editor', 'editor of compilation', 'comp', 'compiler', 'joint comp', 'cmp',
          'ed. and tr', 'edt', 'ed. & tr', 'jt. ed', 'joint compiler', 'coord', 'comp. and tr', 'joint ed. and tr')
PARTICLES = 'von|van|de|da|du|di|del|della|der|den|des|do|dos|das|la|le|ter|ten|af|al|el|zu|y|e|d|vom|vander|op'
ARTICLES = 'the|a|an|le|la|les|l|der|die|das|el|il|lo|los|las|un|une'
EDITING = (r'\b(edited|editors?|eds?\.|compiled|compilers?|hrsg|herausgegeben|herausgeber|sous la direction|'
           r'dirig[ée]e?s?|[ée]dit[ée]e?s? par|organizad[oa]s?|organiza[çc][ãa]o|org\.|a cura di|coordinad[oa]s?|'
           r'coordenad[oa]s?|coordinated|redactie|redigert|toim\.)')


def K(x):
    """SQL for key_lc_works.title_key."""
    s = (f"trim(regexp_replace(regexp_replace(replace(regexp_replace(lower(strip_accents(coalesce({x},''))),"
         f"'[''’‘ʼ]','','g'),'&',' and '),'[^a-z0-9 ]+',' ','g'),' +',' ','g'))")
    s = f"regexp_replace({s},'^(({ARTICLES}) )+','')"
    return f"regexp_extract({s},'^[^ ]+( [^ ]+){{0,9}}',0)"


def F(x):
    """SQL: a family name compacted ('De Groot' -> 'degroot'), with 'ae', 'oe', 'ue' read as the umlaut's base
    letter so that 'Koepping' = 'Köpping' (applied to both sides alike)."""
    x = f"replace(replace(replace(lower(coalesce({x},'')),'œ','oe'),'æ','ae'),'ß','ss')"
    return (f"regexp_replace(regexp_replace(regexp_replace(strip_accents({x}),'[''’‘ʼ]','','g'),"
            f"'[^a-z0-9]+','','g'),'([aou])e','\\1','g')")


def py_compact(words):
    return re.sub(r'([aou])e', r'\1', ''.join(words))


def family_variants(words):
    """A family name as words -> {compact form: is_variant}: the whole name, and, as variants, the name without
    leading particles ('Von Greyerz' = 'Greyerz, Kaspar von') and the first and the last word of a compound
    ('McCall-Newman' = 'McCall', 'Stedman Jones' = 'Jones', 'Wu Hung' = 'Wu')."""
    out = {}
    if not words:
        return out
    out[py_compact(words)] = False
    parts = set()
    w = list(words)
    while len(w) > 1 and w[0] in PARTICLES.split('|'):
        w = w[1:]
    parts.add(tuple(w))
    if len(words) > 1:
        parts |= {(words[0],), (words[-1],)}
    for p in parts:
        k = py_compact(p)
        if len(k) >= 2 and p[0] not in PARTICLES.split('|') and k not in out:
            out[k] = True
    return out


CAPS = re.compile(r"^[A-ZÀ-ÞĀ-Ž'’-]{2,}$")


def parse_name(a):
    """A cited author string -> (family words, given words). 'Ormsby, Margaret A'; 'RICOEUR (Paul)'; '- BADINTER
    Elisabeth' (the capitalised words are the family name); otherwise the last word ('Ivor J. Sanders')."""
    a = re.sub(r'^[^\w(]+', '', a or '').strip()
    m = re.match(r'^([^(),]+?)\s*\(([^()]+)\)\s*$', a)
    if m and len(m.group(2).split()) <= 3 and not re.search(r'\b(ed|eds|org|orgs|coord|dir|hg|hrsg|comp)\b', m.group(2), re.I):
        return py_words(m.group(1)), py_words(m.group(2))
    if ',' in a:
        fam, given = a.split(',', 1)
        toks = fam.split()
        caps = [t for t in toks if CAPS.match(t)]
        if caps and len(caps) < len(toks):           # 'SAID Edward, W'
            return py_words(' '.join(caps)), py_words(' '.join(t for t in toks if t not in caps) + ' ' + given)
        return py_words(fam), py_words(given)
    toks = a.split()
    caps = [t for t in toks if CAPS.match(t)]
    if caps and len(caps) < len(toks):
        return py_words(' '.join(caps)), py_words(' '.join(t for t in toks if t not in caps))
    return py_words(toks[-1] if toks else ''), py_words(' '.join(toks[:-1]))


def W(x):
    """SQL: words, accents and punctuation dropped, padded with spaces for whole-word search."""
    return (f"' '||trim(regexp_replace(regexp_replace(regexp_replace(lower(strip_accents(coalesce({x},''))),"
            f"'[''’‘ʼ]','','g'),'[^a-z0-9]+',' ','g'),' +',' ','g'))||' '")


def py_words(x):
    x = re.sub(r"['’‘ʼ]", '', x or '').lower().replace('œ', 'oe').replace('æ', 'ae').replace('ß', 'ss')
    x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', x).split()


def band(n):
    return '1' if n == 1 else '2-4' if n < 5 else '5-9' if n < 10 else '10+'


def yband(y):
    if y is None:
        return 'none'
    return ('<1900' if y < 1900 else '1900-69' if y < 1970 else '1970-99' if y < 2000 else '2000-09' if y < 2010
            else '2010-16' if y <= 2016 else '2017+')


def build(c, args, log):
    tables = {r[0] for r in c.execute('show tables').fetchall()}
    R, H = f"'{args.index}/records-*.parquet'", f"'{args.index}/headings-*.parquet'"
    if 'works' not in tables:
        cw = ' union '.join(f"select work_id from read_csv('{ROOT / d / 'crosswalk.csv.gz'}', all_varchar=true)"
                            for d in CROSSWALKS)
        c.execute(f"""create table works as
            select work_id, cited_by_dissertations::int n, kind, try_cast(year as int) yr, authors, title,
                   case greatest(br,ca,gb,us,ot) when 0 then 'none' when br then 'BR' when us then 'US' when ca then 'CA'
                        when gb then 'GB' else 'other' end dom, br
            from (select *, cited_by_BR::int br, cited_by_CA::int ca, cited_by_GB::int gb, cited_by_US::int us,
                         cited_by_other::int ot
                  from read_csv('{args.corpus / 'works.csv'}', all_varchar=true))""")
        c.execute(f"create table before as {cw}")
        c.execute("alter table works add column m boolean")
        c.execute("update works set m = work_id in (select work_id from before)")
        log('works', c.execute("select count(*), sum(n), sum(n) filter (where m) from works").fetchone())
    if 'u' not in tables:
        c.execute(f"""create table u as select work_id, n, kind, yr, title, authors,
              {K("split_part(title,':',1)")} mt, {K('title')} whole,
              {K("regexp_extract(split_part(title,':',1),'^[^,;]*')")} mtc
            from works where not m and kind in {KINDS}""")
        c.execute("update u set mtc = null where mtc = mt or mtc = ''")
        import pyarrow as pa
        cols = defaultdict(list)
        for w, authors in c.execute("select work_id, authors from u").fetchall():
            seen = set()
            for a in (authors or '').split(';'):
                fam, given = parse_name(a)
                full = py_compact(fam)
                for famc, var in family_variants(fam).items():
                    if (famc, full) in seen:
                        continue
                    seen.add((famc, full))
                    for k, v in (('work_id', w), ('famc', famc), ('famfull', full), ('famw', ' ' + ' '.join(fam) + ' '),
                                 ('init', given[0][0] if given else ''), ('gtok', given[0] if given else ''), ('var', var)):
                        cols[k].append(v)
        c.register('ua_arrow', pa.table(dict(cols)))
        c.execute("create table ua as select * from ua_arrow where famc <> ''")
        c.unregister('ua_arrow')
        log('u', c.execute("select count(*), sum(n) from u").fetchone(), 'authors', c.execute("select count(*) from ua").fetchone())
    if 'lk' not in tables:
        c.execute("create table want as select distinct mt k from u where mt<>'' union select whole from u where whole<>'' "
                  "union select mtc from u where mtc is not null")
        c.execute(f"""create table lk as
            with r as (select trim(control) control, {K('coalesce(title_a,title)')} a, {K('title')} full_,
                              {K("regexp_extract(coalesce(title_a,title),'^[^,;=]*')")} comma
                       from {R} where not starts_with(control, 'mm'))
            select * from (select control, 'a' form, a tk from r union all select control, 'full', full_ from r where full_<>a
                           union all select control, 'comma', comma from r where comma<>a)
            where tk in (select k from want)""")
        log('lk', c.execute("select form, count(*), count(distinct control) from lk group by 1").fetchall())
    if 'lh' not in tables:
        c.execute(f"""create or replace table lrec as select trim(control) control, title, title_a, responsibility,
              case when regexp_matches(date1,'^[0-9]{{4}}$') then date1::int end y, lang
            from {R} where trim(control) in (select distinct control from lk)""")
        fw = f"trim({W('h.family')})"
        strip = f"regexp_replace({fw}, '^(({PARTICLES}) )+', '')"
        c.execute(f"""create table lh0 as select trim(h.control) control, h.pos, h.tag, h.heading, {F('h.family')} famfull,
              list_distinct([{F(strip)}, case when contains({fw}, ' ') then {F(f"split_part({fw}, ' ', 1)")} end,
                             case when contains({fw}, ' ') then {F(f"regexp_extract({fw}, '(\\S+)$', 1)")} end]) vars,
              left(regexp_replace(lower(strip_accents(h.given)),'[^a-z]','','g'),1) init,
              case when h.tag='100' then 'main'
                   when len(list_filter(h.relators, r -> trim(lower(r), ' .,') in {AUTHOR})) > 0 then 'added'
                   when len(list_filter(h.relators, r -> trim(lower(r), ' .,') in {EDITOR})) > 0 then 'editor'
                   when len(h.relators) = 0 and regexp_matches(coalesce(r.responsibility,''), '{EDITING.replace("'", "''")}', 'i')
                        and contains({W('r.responsibility')}, {W('h.family')}) then 'editor'
                   when len(h.relators) = 0 then 'added' end as role
            from {H} h join lrec r on r.control = trim(h.control)""")
        c.execute("delete from lh0 where role is null or famfull = ''")
        c.execute(f"""create table lh as select control, pos, tag, heading, famfull, init, role, famfull famc, false var from lh0
              union select control, pos, tag, heading, famfull, init, role, v, true from (
                select *, unnest(vars) v from lh0) where v is not null and v <> famfull and length(v) >= 2
                and v not in (select unnest(string_split('{PARTICLES}', '|')))""")
        log('lrec', c.execute("select count(*) from lrec").fetchone(), 'lh', c.execute("select count(*) from lh").fetchone())
    if 'cand' not in tables:
        tiers = [("exact", "u.mt = lk.tk and lk.form = 'a'"), ("whole", "u.whole = lk.tk and lk.form in ('a','full')"),
                 ("lc-comma", "u.mt = lk.tk and lk.form = 'comma'"), ("corpus-comma", "u.mtc = lk.tk and lk.form = 'a'"),
                 ("both-comma", "u.mtc = lk.tk and lk.form = 'comma'")]
        parts = [f"""select distinct u.work_id, '{t}' tform, lk.control, lh.role nform, lh.heading, lh.famfull famc, lh.init,
                            ua.famfull cited_fam, (ua.var or lh.var) var
                     from u join lk on {cond} join lh on lh.control = lk.control
                     join ua on ua.work_id = u.work_id and ua.famc = lh.famc""" for t, cond in tiers]
        c.execute("create table cand as " + " union all ".join(parts))
        log('cand heading', c.execute("select tform, nform, count(*), count(distinct work_id) from cand group by all").fetchall())
        # statement-of-responsibility route, only for works no heading reached
        c.execute(f"""create table rw as select control, {W('responsibility')} rs from lrec where coalesce(responsibility,'')<>''""")
        parts = [f"""select distinct u.work_id, '{t}' tform, lk.control, ua.famw, ua.init, ua.gtok, rw.rs
                     from u join lk on {cond} join rw on rw.control = lk.control
                     join ua on ua.work_id = u.work_id and not ua.var and ua.init <> '' and contains(rw.rs, ua.famw)
                     where u.work_id not in (select work_id from cand) and contains(u.mt, ' ')""" for t, cond in tiers[:2]]
        c.execute("create table rcand as " + " union all ".join(parts))
        log('cand resp (raw)', c.execute("select tform, count(*), count(distinct work_id) from rcand group by all").fetchall())


def initial_before(rs, famw, init, gtok=''):
    """The family name in the statement of responsibility, preceded within four words by the cited given name:
    its first word when the citation spells it out ('miriam formanek brunell'), else a word with its initial
    ('f n l poynter'). 2026-11-10 audit: an initial alone let 'Augusto C. da Silva Telles' stand for 'Silva,
    Alberto da Costa e'."""
    words, fam = rs.split(), famw.split()
    for i in range(len(words) - len(fam) + 1):
        if words[i:i + len(fam)] == fam:
            before = words[max(0, i - 4):i]
            if (gtok in before) if len(gtok) > 1 else any(w[0] == init for w in before):
                return True
    return False


def long_key(t):
    """key_lc_works.title_key without the ten-word cut."""
    w = py_words(re.sub(r'\s*&\s*', ' and ', t or ''))
    while w and w[0] in ARTICLES.split('|'):
        w = w[1:]
    return w


def subtitle_agrees(cited_title, lc_title):
    """A one-word main title is safe when the subtitles agree too, three words or more ('Les hygiénistes: enjeux,
    modèles et pratiques'), not when one side has none ('Diefenbaker' for 'Diefenbaker: Leadership Gained')."""
    a, b = long_key(cited_title), long_key(lc_title)
    m = min(len(a), len(b))
    return m >= 3 and a[:m] == b[:m]


IMPRINT = re.compile(r':\s*[^:]*,\s*(1[5-9]|20)\d\d\W*$')     # 'São Paulo: Edusp, 2002' as the title
COLLECTION = re.compile(r'^[^,;]*[,;]\s*(and|e|et|und|y)\s+(other|outr|autre|andere|otr)', re.I)
NAMEFORMS = ['main', 'added', 'editor', 'resp']


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True, help='scratch folder for the DuckDB work file and temp')
    ap.add_argument('--corpus', type=Path, default=CORPUS)
    ap.add_argument('--index', default='/mnt/e/lc-bib-2016/index')
    ap.add_argument('--names', default='/mnt/e/lc-authorities/personal-names.parquet')
    ap.add_argument('--fresh', action='store_true', help='rebuild the work tables')
    args = ap.parse_args()
    t0 = time.time()

    def log(*a):
        print(f'[{round(time.time() - t0)}s]', *a, flush=True)

    args.work.mkdir(parents=True, exist_ok=True)
    db = args.work / 'work.duckdb'
    if args.fresh and db.exists():
        db.unlink()
    c = duckdb.connect(str(db))
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{args.work}/ddb'; "
              "SET max_temp_directory_size='2GB'; SET preserve_insertion_order=false")
    build(c, args, log)

    # --- choose per work -------------------------------------------------------------------------------------
    recs = {r[0]: r[1:] for r in c.execute(
        f"select control, title, y, {K('title')}, {K('coalesce(title_a,title)')}, coalesce(title_a,title) from lrec").fetchall()}
    info = {r[0]: r[1:] for r in c.execute("select work_id, n, kind, yr, whole, mt, title, authors, mtc from u").fetchall()}
    inits = defaultdict(dict)                          # work -> cited family (compact) -> cited initial
    for w, famfull, init in c.execute("select work_id, famfull, init from ua").fetchall():
        inits[w].setdefault(famfull, init)
    order = ['exact', 'whole', 'lc-comma', 'corpus-comma', 'both-comma']
    # candidate: (tier rank, name form, control, heading, LC family, LC initial, name variant?, cited family)
    cands = defaultdict(list)
    for w, tf, ctl, nf, heading, famc, init, cited, var in c.execute(
            "select work_id, tform, control, nform, heading, famc, init, cited_fam, var from cand").fetchall():
        cands[w].append((order.index(tf), nf, ctl, heading, famc, init or '', var, cited))
    log('heading candidates for', len(cands), 'works')
    first100 = dict(c.execute("select control, any_value(heading) from lh where tag='100' group by 1").fetchall())
    for w, tf, ctl, famw, init, gtok, rs in c.execute("select work_id, tform, control, famw, init, gtok, rs from rcand").fetchall():
        if len(famw.strip()) < 3:
            continue
        if initial_before(rs, famw, init, gtok):
            fam = py_compact(famw.split())
            cands[w].append((order.index(tf), 'resp', ctl, first100.get(ctl, ''), 'resp:' + fam, init, False, fam))
    log('with responsibility candidates', len(cands), 'works')

    def keep(w, x):
        """Guards from the 2026-11-10 audit (audit-sample.csv)."""
        tier, nf, ctl, _, famc, init, var, cited = x
        n, kind, yr, whole, mt, title, authors, mtc = info[w]
        cited_init = inits[w].get(cited, '')
        key = mt if tier in (0, 2) else whole if tier == 1 else mtc if tier == 4 else recs[ctl][3]
        agree = bool(init and init == cited_init) or nf == 'resp'
        if tier >= 2:                                  # comma forms: two words or more, initials agree
            if len(key.split()) < 2 or not agree or nf == 'resp':
                return False                           # 'New York, 1966' is not Clyde H. Smith's 'New York'
            if tier in (2, 4) and COLLECTION.match(recs[ctl][4] or ''):
                return False                           # 'O alienista, e outras histórias' is not 'O alienista'
        if var and not agree:                          # a name variant needs the initial too
            return False
        if len(key.split()) == 1 and not (agree and (nf == 'main' or subtitle_agrees(title, recs[ctl][0]))):
            return False                               # one-word titles: the main entry, or the subtitle agreeing
        if len(key.split()) == 10:                     # the ten-word cut: the longer titles must still agree
            cited_t = long_key(title if tier == 1 else title.split(':')[0])
            lc = long_key(recs[ctl][4] if tier in (0, 3) else recs[ctl][0])
            m = min(len(cited_t), len(lc))
            if cited_t[:m] != lc[:m]:
                return False
        return True

    matches, held, report = [], [], Counter()
    for w in list(cands):
        n, kind, yr, whole, mt, title, authors, mtc = info[w]
        if IMPRINT.search(title or '') and len(mt.split()) <= 3:
            report['imprint_title_skipped'] += 1       # 'New York: St. Martin's Press, 1979' as the title
            continue
        pool = [x for x in cands[w] if keep(w, x)]
        if not pool:
            report['all_candidates_guarded'] += 1
            continue
        pool = [x for x in pool if x[1] != 'resp'] or pool
        pool = [x for x in pool if not x[6]] or pool   # the whole family name before a variant of it
        top = min(x[0] for x in pool)
        pool = [x for x in pool if x[0] == top]
        # people: (LC family, initial); a heading without an initial joins the one person of its family that has one
        people = {(x[4], x[5]) for x in pool}
        alias = {}
        for f, i in people:
            if i == '':
                sib = [p for p in people if p[0] == f and p[1] != '']
                if len(sib) == 1:
                    alias[f, i] = sib[0]
        # clusters: records joined by a shared person, people joined by a shared record (a book by Trentmann
        # and Just is one cluster, not two)
        parent = {}

        def find(z):
            while parent.setdefault(z, z) != z:
                parent[z] = parent[parent[z]]
                z = parent[z]
            return z
        for x in pool:
            pk = alias.get((x[4], x[5]), (x[4], x[5]))
            parent[find(('r', x[2]))] = find(('p',) + pk)
        clusters = defaultdict(dict)                   # root -> control -> (nform, heading, variant?, person, cited fam)
        for x in pool:
            root = find(('r', x[2]))
            pk = alias.get((x[4], x[5]), (x[4], x[5]))
            prev = clusters[root].get(x[2])
            if prev is None or NAMEFORMS.index(x[1]) < NAMEFORMS.index(prev[0]):
                clusters[root][x[2]] = (x[1], x[3], x[6], pk, x[7])
        keys = list(clusters)
        choice = 'single' if len(keys) == 1 else None
        if len(keys) > 1:
            same = [k for k in keys if any(recs[x][2] == whole or recs[x][3] == whole for x in clusters[k])]
            if len(same) == 1:
                keys, choice = same, 'whole-chosen'
            # choosing by year (two years either side) was dropped after the audit too: 3 wrong in 16 ('Romney
            # Marsh' 1998 took Eddison's 2000 'Romney Marsh: survival on a frontier'; 'João do Rio'); 81 books held
            # choosing by initial alone was dropped after the audit: 'Silva, Maria' took Marcos da Silva's book,
            # 'Romero, José Luis' José Rubén Romero's 'Obras completas'
        if not choice:
            held.append((w, n, kind, yr, order[top], len(keys), ' || '.join(
                '; '.join(f"{x} {recs[x][1] or ''} {(recs[x][0] or '')[:70]} [{clusters[k][x][1]}]" for x in sorted(clusters[k])[:3])
                for k in keys[:6])))
            report['held'] += 1
            continue
        cl = clusters[keys[0]]
        if top in (2, 4) and len({recs[x][3] for x in cl}) > 1:
            # matched on the part before a comma, the records' titles differ after it: volumes or different books
            # by one person ('Medical services, general history' and 'Medical services, casualties ...')
            held.append((w, n, kind, yr, order[top], 1, '; '.join(f"{x} {recs[x][1] or ''} {(recs[x][0] or '')[:70]}"
                                                                    for x in sorted(cl)[:4])))
            report['held_comma_titles_differ'] += 1
            continue
        ctls = sorted(cl, key=lambda x: (recs[x][1] or 9999, x))
        if choice == 'single' and len(ctls) > 1:
            choice = 'editions'
        nf = min((v[0] for v in cl.values()), key=NAMEFORMS.index)
        heading = next((cl[x][1] for x in ctls if cl[x][0] == nf and cl[x][1]), '') or next((cl[x][1] for x in ctls if cl[x][1]), '')
        years = [recs[x][1] for x in ctls if recs[x][1]]
        first = min(years) if years else None
        if nf == 'resp':
            initial = 'agree'
        else:
            ci = [(v[3][1], inits[w].get(v[4], '')) for v in cl.values() if v[0] != 'resp']
            initial = ('agree' if any(a and a == b for a, b in ci) else
                       'differ' if any(a and b and a != b for a, b in ci) else 'unknown')
        year_fit = 'unknown' if not (yr and first) else 'before' if yr < first - 2 else 'ok'
        matches.append(dict(work_id=w, lccns=';'.join(ctls), lc_title=(recs[ctls[0]][0] or '').strip(' /:;,.')[:250],
                            lc_year=first or '', lc_author_heading=heading, lc_author_uri='',
                            basis=f'{order[top]}/{nf}/{choice}', n_lc_records=len(ctls), cited_by_dissertations=n,
                            initial=initial, year_fit=year_fit,
                            name='variant' if all(v[2] for v in cl.values()) else 'whole'))
    log('matched', len(matches), 'held', len(held))

    # --- authority URIs for matched headings -----------------------------------------------------------------
    hs = sorted({m['lc_author_heading'] for m in matches if m['lc_author_heading']})
    c.execute("create or replace temp table mh(heading varchar)")
    c.executemany("insert into mh values (?)", [(h,) for h in hs])
    NH = ("regexp_replace(regexp_replace(trim(regexp_replace(replace({x},'’',''''),'\\s+',' ','g'),' ,'),"
          "'\\s*,\\s*',', ','g'),'([^ -][^ .])\\.$','\\1')")
    c.execute(f"""create or replace temp table nm as select lcid, {NH.format(x='label')} lab,
                   regexp_replace({NH.format(x='label')}, '(\\d{{4}})-\\d{{4}}$', '\\1-') openlab
                 from read_parquet('{args.names}') where not deprecated and not undifferentiated""")
    # a former authorised form LC keeps as a variant: same family name, and the heading's dates are the
    # authority's ('Ormsby, Margaret Anchoretta, 1909-' for 'Ormsby, Margaret A. (Margaret Anchoretta), 1909-')
    c.execute(f"""create or replace temp table nv as select lcid, lab, {NH.format(x='v')} var from (
                   select lcid, {NH.format(x='label')} lab, unnest(variants) v from read_parquet('{args.names}')
                   where not deprecated and not undifferentiated)""")
    uri, via = {}, Counter()
    for h, l1, l2, l3 in c.execute(f"""with m as (select heading, {NH.format(x='heading')} nh,
                 regexp_extract({NH.format(x='heading')}, '(\\d{{4}}-(\\d{{4}})?)$', 1) d from mh)
            select heading, (select list(lcid) from nm where lab = m.nh),
                   (select list(lcid) from nm where openlab = m.nh and lab <> m.nh),
                   (select list(lcid) from nv where var = m.nh and m.d <> '' and contains(nv.lab, m.d)
                      and lower(split_part(nv.lab, ',', 1)) = lower(split_part(m.nh, ',', 1)))
            from m""").fetchall():
        for name, ids in (('label', l1), ('since_closed', l2), ('former_form', l3)):
            if ids:
                if len(set(ids)) == 1:
                    uri[h] = f'http://id.loc.gov/authorities/names/{ids[0]}'
                    via[name] += 1
                break
    for m in matches:
        m['lc_author_uri'] = uri.get(m['lc_author_heading'], '')
    log('headings', len(hs), 'with authority', len(uri))

    # --- write -----------------------------------------------------------------------------------------------
    args.out.mkdir(parents=True, exist_ok=True)
    cols = ['work_id', 'lccns', 'lc_title', 'lc_year', 'lc_author_heading', 'lc_author_uri', 'basis', 'n_lc_records',
            'cited_by_dissertations', 'initial', 'year_fit', 'name']
    matches.sort(key=lambda m: (-m['cited_by_dissertations'], m['work_id']))
    with gzip.open(args.out / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, cols)
        wr.writeheader()
        wr.writerows(matches)
    held.sort(key=lambda h: (-h[1], h[0]))
    with gzip.open(args.out / 'held.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'cited_by_dissertations', 'kind', 'year', 'title_form', 'n_candidates', 'candidates'])
        wr.writerows(held)

    # --- report ----------------------------------------------------------------------------------------------
    c.execute("create or replace temp table nw(work_id varchar, basis varchar)")
    c.executemany("insert into nw values (?, ?)", [(m['work_id'], m['basis']) for m in matches])
    c.execute("create or replace temp table r as select works.*, nw.basis is not null as isnew from works left join nw using (work_id)")
    tot = c.execute("select sum(n), sum(n) filter (where m), sum(n) filter (where m or isnew) from r").fetchone()

    def rates(where, by):
        out = {}
        for g, cites, b, a in c.execute(f"""select {by} g, sum(n), coalesce(sum(n) filter (where m),0),
                coalesce(sum(n) filter (where m or isnew),0) from r where {where} group by 1 order by 1""").fetchall():
            out[str(g)] = dict(citations=int(cites), before_pct=round(100 * b / cites, 1) if cites else None,
                               after_pct=round(100 * a / cites, 1) if cites else None, new_citations=int(a - b))
        return out
    B = "case when n=1 then '1' when n<5 then '2-4' when n<10 then '5-9' else '10+' end"
    Y = ("case when yr is null then 'none' when yr<1900 then '<1900' when yr<1970 then '1900-69' when yr<2000 then '1970-99' "
         "when yr<2010 then '2000-09' when yr<=2016 then '2010-16' else '2017+' end")
    bk = f"kind in {KINDS}"
    bc = Counter()
    for m in matches:
        bc[m['basis']] += m['cited_by_dissertations']
    rep = dict(
        all_citations=dict(citations=int(tot[0]), before=int(tot[1]), after=int(tot[2]),
                           before_pct=round(100 * tot[1] / tot[0], 1), after_pct=round(100 * tot[2] / tot[0], 1)),
        by_kind=rates('true', 'kind'),
        books_by_citing_band=rates("kind='book'", B), bookish_by_citing_band=rates(bk, B),
        books_by_year_band=rates("kind='book'", Y), bookish_by_year_band=rates(bk, Y),
        books_by_dominant_country=rates("kind='book'", 'dom'), bookish_by_dominant_country=rates(bk, 'dom'),
        new_matches=len(matches), new_matched_citations=sum(m['cited_by_dissertations'] for m in matches), held=len(held),
        held_citations=sum(h[1] for h in held), guards=dict(report),
        by_basis={b: dict(works=x, citations=bc[b]) for b, x in Counter(m['basis'] for m in matches).most_common()},
        by_title_form=dict(Counter(m['basis'].split('/')[0] for m in matches)),
        by_name_form=dict(Counter(m['basis'].split('/')[1] for m in matches)),
        by_choice=dict(Counter(m['basis'].split('/')[2] for m in matches)),
        by_initial=dict(Counter(m['initial'] for m in matches)), by_name=dict(Counter(m['name'] for m in matches)), by_year_fit=dict(Counter(m['year_fit'] for m in matches)),
        author_headings=dict(distinct=len(hs), with_authority_uri=len(uri), uri_via=dict(via), without=len(hs) - len(uri),
                             matches_with_uri=sum(1 for m in matches if m['lc_author_uri'])),
        lc_index=args.index, crosswalks_before=CROSSWALKS,
    )
    (args.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    log(json.dumps(rep['all_citations']), json.dumps(rep['by_title_form']), json.dumps(rep['by_name_form']))


if __name__ == '__main__':
    main()
