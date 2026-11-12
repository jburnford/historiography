"""Editors of the volumes that chapters are in (2026-11-11).

The graph places 367k chapters in their volumes (PART_OF, key log and linked), but most volumes carry no EDITED credit
and no printed editors, so a chapter author's page cannot say who edited the book. This script finds the printed
editors of those volumes and links them to person keys with the existing linker (scripts/link_work_people.py, which
imports the rule of scripts/link_cited_work_authors.py): no new identity rule.

Sources of printed editors, in order of precedence:
  lc        LC 2016 bibliographic records (/mnt/e/lc-bib-2016/index, read-only) matched to the volume by LCCN anchor,
            ISBN, or normalised title + year (one record only): 700 headings whose relator says editor/compiler, and
            names in an 'edited by' / 'editors' clause of 245 $c. A name only in a foreword / introduction / series
            editor clause or relator is not an editor (the contributors step's phrases).
  crossref  Crossref REST records: the book DOI (the volume's own DOI, or the one a chapter DOI implies by the publisher
            patterns of scripts/export_work_containers.book_doi_candidates), else one chapter record of the volume
            (the resumable chapter fetch of export_work_containers.py, same raw folder): its `editor` list.
  (OpenAlex records carry no editors, so it is not a source here.)

2026-11-12: the 245 $c parser no longer takes a name whose role word is qualified by another job ('Graeme Wynn,
cartographic editor', 'picture', 'associate', 'assistant', 'consulting', 'executive' ... editor; 'co-', 'joint',
'volume', 'guest', 'book' and 'coordinating' keep the editor role) or that edited a part of the book ('maps edited by',
'bibliography edited by'), and splits 'X, editor, Y, consulting editor' into one clause per role word. The export applies
the series-editor rule (series_editor_flags) to Crossref rows: those rows get state 'series-editor' (printed only; the
build loads a linked person as CONTRIBUTED, never EDITED); hand judgments in
data/identifiers/volume-editors-2026-11-12/series-editor-audit.csv; the same rule over the other editor credits of the
last build is counted in the report (series_editor_rule.keylog_and_edition_roles_check).

Linking: one position per printed editor; scripts/link_work_people.py's WPPeople, features, rule_wp and guard, role
'editor', book=True (a book credit's date window). Positive facts are the linker's own: an LC heading resolving to an
LC authority that is a key's lcnaf anchor (exact; the heading rule of link_cited_work_authors.load_sources), a
co-author tie with a keyed author of the volume's chapters or another editor of it (the 'coauthor' fact, `exacts` =
those keys), dated institution (none printed here), rarity and dates. Gold: printed editors of volumes whose EDITED
credits (key log) agree by name, decided with that credit and the facts from that volume hidden (HIDE), as in
link_work_people.link.

    python3 scripts/volume_editors.py targets     # class counts, volumes and the Crossref fetch lists (scratch)
    python3 scripts/volume_editors.py fetch [--max 60000]   # Crossref REST, <=3 req/s, raw under build/
    python3 scripts/volume_editors.py lc          # LC records -> printed editors (scratch)
    python3 scripts/volume_editors.py positions   # printed editors -> positions (scratch)
    python3 scripts/volume_editors.py link        # linker + masked gold
    python3 scripts/volume_editors.py export      # data/graph/volume-editors.csv.gz + volume-editors-report.json
    python3 scripts/volume_editors.py series      # report: key-log AUTHORED chapter claims of a volume's series editor

Reads a copy of build/graph (VE_GRAPH) so a concurrent rebuild cannot change the inputs mid-run. Writes no proposal and
touches no key log.
"""
import argparse
import collections
import csv
import gzip
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SCR = Path(os.environ.get('VE_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                          'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/editors'))
G = Path(os.environ.get('VE_GRAPH', SCR / 'graph'))
os.environ.setdefault('WP_GRAPH', str(G))
os.environ.setdefault('WP_SCRATCH', str(SCR / 'wp'))
CR_BOOKS = ROOT / 'build/crossref-volume-editors-2026-11-11'
CR_CHAPTERS = ROOT / 'build/crossref-containers-2026-11-11'      # export_work_containers.py crossref (resumable)
LC_REC = '/mnt/e/lc-bib-2016/index/records-*.parquet'
LC_HEAD = '/mnt/e/lc-bib-2016/index/headings-*.parquet'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
OUT = ROOT / 'data/graph/volume-editors.csv.gz'
REPORT = ROOT / 'data/graph/volume-editors-report.json'
AUDIT = ROOT / 'data/identifiers/volume-editors-2026-11-12/series-editor-audit.csv'   # hand judgments of the rule
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography; mailto:jic823@usask.ca)'


def duck():
    import duckdb
    (SCR / 'duck').mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET enable_progress_bar=false; SET temp_directory='{SCR}/duck'")
    return db


def jl(p):
    if not Path(p).exists():
        return
    with open(p, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:      # the last line of a file still being written
                    continue


def norm_doi(d):
    return (d or '').strip().lower().replace('https://doi.org/', '').replace('http://dx.doi.org/', '')


# ---------------------------------------------------------------- targets

def targets(args):
    from export_work_containers import book_doi_candidates
    db = duck()
    db.execute(f"""CREATE TABLE vol AS
        WITH ch AS (SELECT "to" v, count(DISTINCT "from") n_ch FROM '{G}/part_of.parquet' GROUP BY 1),
        ca AS (SELECT p."to" v, count(DISTINCT a."from") n_auth, count(DISTINCT a."from") FILTER (WHERE a.evidence = 'keylog') n_auth_kl
               FROM '{G}/part_of.parquet' p JOIN '{G}/authored.parquet' a ON a."to" = p."from" GROUP BY 1),
        ed AS (SELECT "to" v, count(DISTINCT "from") n_ed, count(DISTINCT "from") FILTER (WHERE evidence = 'keylog') n_ed_kl
               FROM '{G}/edited.parquet' GROUP BY 1),
        va AS (SELECT "to" v, count(DISTINCT "from") n_va FROM '{G}/authored.parquet' GROUP BY 1)
        SELECT w.key, w.resolution, w.kind, w.year, w.label, w.isbn, w.editors_printed, w.anchors, ch.n_ch,
               coalesce(ca.n_auth, 0) n_auth, coalesce(ca.n_auth_kl, 0) n_auth_kl, coalesce(ed.n_ed, 0) n_ed,
               coalesce(ed.n_ed_kl, 0) n_ed_kl, coalesce(va.n_va, 0) n_vol_authors
        FROM ch JOIN '{G}/work.parquet' w ON w.key = ch.v LEFT JOIN ca ON ca.v = ch.v LEFT JOIN ed ON ed.v = ch.v
        LEFT JOIN va ON va.v = ch.v""")
    db.execute(f"COPY vol TO '{SCR}/volumes.parquet' (FORMAT parquet)")
    # chapter DOIs of every volume
    db.execute(f"""COPY (SELECT DISTINCT p."to" v, lower(replace(x.a, 'doi:', '')) d FROM '{G}/part_of.parquet' p
            JOIN (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') x ON x.key = p."from" WHERE x.a LIKE 'doi:%'
            UNION SELECT p."to", lower(substr(p."from", 5)) FROM '{G}/part_of.parquet' p WHERE p."from" LIKE 'doi:%')
            TO '{SCR}/chapter-dois.parquet' (FORMAT parquet)""")
    rep = class_counts(db, 'vol')
    print(json.dumps(rep, indent=1))
    # Crossref lists: book DOIs (own, or implied by a chapter DOI) for the class, then a sample of gold volumes
    chd = collections.defaultdict(set)
    for v, d in db.execute(f"SELECT v, d FROM '{SCR}/chapter-dois.parquet'").fetchall():
        chd[v].add(d)
    books, gold_books, chap = [], [], []
    for k, an, n_ed, pr, n_ed_kl in db.execute("SELECT key, anchors, n_ed, editors_printed, n_ed_kl FROM vol ORDER BY n_ch DESC, key").fetchall():
        own = sorted({a[4:].lower() for a in an or [] if a.startswith('doi:')} | ({k[4:].lower()} if k.startswith('doi:') else set()))
        der = sorted({b for d in chd.get(k, ()) for b in book_doi_candidates(d)} - set(own))
        bd = (own + der)[:2]
        in_class = n_ed == 0 and not pr
        if in_class:
            if bd:
                books += [(k, d, 'own' if d in own else 'derived') for d in bd[:1]]
            elif chd.get(k):
                chap.append((k, sorted(chd[k])[0]))
        elif n_ed_kl and bd:
            gold_books.append((k, bd[0], 'own' if bd[0] in own else 'derived'))
    with open(SCR / 'fetch-books.tsv', 'w') as f:
        for r in books:
            f.write('\t'.join(r) + '\n')
    with open(SCR / 'fetch-gold-books.tsv', 'w') as f:
        for r in gold_books:
            f.write('\t'.join(r) + '\n')
    with open(SCR / 'fetch-chapters.tsv', 'w') as f:
        for r in chap:
            f.write('\t'.join(r) + '\n')
    print('book DOIs', len(books), 'gold book DOIs', len(gold_books), 'chapter-only volumes', len(chap))
    rep['fetch_lists'] = dict(book_dois=len(books), gold_book_dois=len(gold_books), chapter_only_volumes=len(chap))
    (SCR / 'class-before.json').write_text(json.dumps(rep, indent=1))


def class_counts(db, t, editor_sql="n_ed = 0 AND coalesce(editors_printed, '') = ''"):
    q = lambda s: db.execute(s).fetchall()
    band = "CASE WHEN n_auth = 0 THEN '0' WHEN n_auth = 1 THEN '1' WHEN n_auth <= 3 THEN '2-3' ELSE '4+' END"
    rep = dict(volumes_with_chapters=q(f"SELECT count(*) FROM {t}")[0][0])
    rep['no_editor'] = {('unkeyed' if u else 'keyed'): n for u, n in q(
        f"SELECT resolution = 'unkeyed', count(*) FROM {t} WHERE {editor_sql} GROUP BY 1")}
    rep['no_editor_by_keyed_chapter_authors'] = {f"{'unkeyed' if u else 'keyed'}|{b}": n for u, b, n in q(
        f"SELECT resolution = 'unkeyed', {band} b, count(*) FROM {t} WHERE {editor_sql} GROUP BY ALL ORDER BY ALL")}
    rep['no_editor_volume_has_authored_credit'] = {('unkeyed' if u else 'keyed'): n for u, n in q(
        f"SELECT resolution = 'unkeyed', count(*) FROM {t} WHERE {editor_sql} AND n_vol_authors > 0 GROUP BY 1")}
    return rep


def targets2(args):
    """second book DOI for class volumes whose first book record gave no editor (404, another type, another title,
    or no editor list): the volume's other own DOI or a DOI its chapter DOIs imply (a repository DOI such as
    10.11575/prism/... is often the volume's own anchor while the publisher's book DOI is implied by its chapters)"""
    from export_work_containers import book_doi_candidates
    db = duck()
    chd = collections.defaultdict(set)
    for v, d in db.execute(f"SELECT v, d FROM '{SCR}/chapter-dois.parquet'").fetchall():
        chd[v].add(d)
    first = {}
    for line in open(SCR / 'fetch-books.tsv'):
        v, d, how = line.rstrip('\n').split('\t')
        first[v] = d
    got = {}
    for p in sorted(CR_BOOKS.glob('part-*.jsonl')):
        for it in jl(p):
            got[it['_doi']] = bool(it.get('editor')) and it.get('type') in BOOK_TYPES
    out = []
    for k, an in db.execute(f"SELECT key, anchors FROM '{SCR}/volumes.parquet' WHERE n_ed = 0 AND coalesce(editors_printed, '') = ''").fetchall():
        d1 = first.get(k)
        if not d1 or d1 not in got or got[d1]:
            continue
        own = sorted({a[4:].lower() for a in an or [] if a.startswith('doi:')} | ({k[4:].lower()} if k.startswith('doi:') else set()))
        der = sorted({b for d in chd.get(k, ()) for b in book_doi_candidates(d)})
        rest = [d for d in own + der if d != d1]
        if rest:
            out.append((k, rest[0], 'own2' if rest[0] in own else 'derived'))
    with open(SCR / 'fetch-books2.tsv', 'w') as f:
        for r in out:
            f.write('\t'.join(r) + '\n')
    print(len(out), 'second book DOIs')


# ---------------------------------------------------------------- Crossref fetch

class Rate:
    def __init__(self, per_s):
        self.gap, self.lock, self.last = 1.0 / per_s, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            t = time.time()
            w = self.last + self.gap - t
            if w > 0:
                time.sleep(w)
            self.last = time.time()


def get(url, rate, stats):
    for i in range(6):
        rate.wait()
        stats['requests'] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return json.load(r).get('message')
        except Exception as e:
            code = getattr(e, 'code', None)
            if code == 404:
                return {'_missing': True}
            stats[f'error-{code}'] += 1
            time.sleep(min(120, 3 * 2 ** i))
    return None


def fetch(args):
    """book DOIs (class, then gold), then the remaining chapter DOIs of export_work_containers' list whose volume is in
    the class and has no book DOI; at most args.max requests; 3 threads behind one 3/s limiter"""
    from concurrent.futures import ThreadPoolExecutor
    CR_BOOKS.mkdir(parents=True, exist_ok=True)
    done_b = {r['_doi'] for p in CR_BOOKS.glob('part-*.jsonl') for r in jl(p)}
    done_c = {r['_doi'] for p in CR_CHAPTERS.glob('part-*.jsonl') for r in jl(p)}
    todo = []
    for fn, kind in (('fetch-books.tsv', 'book'), ('fetch-gold-books.tsv', 'book'), ('fetch-books2.tsv', 'book'), ('fetch-chapters.tsv', 'chapter')):
        if not (SCR / fn).exists():
            continue
        for line in open(SCR / fn):
            v, d = line.rstrip('\n').split('\t')[:2]
            if d not in (done_b if kind == 'book' else done_c):
                todo.append((kind, d))
    seen = set()
    todo = [x for x in todo if not (x in seen or seen.add(x))]
    print(len(todo), 'to fetch;', len(done_b), 'books and', len(done_c), 'chapters held', flush=True)
    todo = todo[:args.max]
    rate, stats = Rate(args.rate), collections.Counter()
    nb = len(list(CR_BOOKS.glob('part-*.jsonl')))
    nc = len(list(CR_CHAPTERS.glob('part-*.jsonl')))
    ob = open(CR_BOOKS / f'part-{nb:03d}.jsonl', 'a', encoding='utf-8')
    oc = open(CR_CHAPTERS / f'part-{nc:03d}.jsonl', 'a', encoding='utf-8')
    lock = threading.Lock()

    def one(x):
        kind, d = x
        rec = get('https://api.crossref.org/works/' + urllib.parse.quote(d, safe='/') + '?mailto=jic823@usask.ca', rate, stats)
        if rec is None:
            stats['failed'] += 1
            return
        rec['_doi'] = d
        with lock:
            (ob if kind == 'book' else oc).write(json.dumps(rec, ensure_ascii=False) + '\n')
            stats[kind] += 1
            n = stats['book'] + stats['chapter']
            if n % 500 == 0:
                ob.flush(); oc.flush()
                print(n, dict(stats), time.strftime('%H:%M:%S'), flush=True)
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(one, todo))
    ob.close(); oc.close()
    print('done', dict(stats), flush=True)
    (SCR / f'fetch-stats-{int(time.time())}.json').write_text(json.dumps(dict(stats)))


# ---------------------------------------------------------------- LC 2016 records

LEAD_ART = re.compile(r'^(the|a|an|le|la|les|l|der|die|das|el|los|las|il|lo|gli|une|un|de)\s+')
EDIT_REL = re.compile(r'(?i)^(editor|editor of compilation|ed|ed\.|edt|joint ed|joint editor|compiler|comp|com|comp\.|editor and compiler)$')
SERIES_PHRASE = re.compile(r'(?i)series (?:general )?editor|general editors?|editor[- ]in[- ]chief|managing editor|editorial (?:board|committee|director)')
EDIT_WORD = re.compile(r'(?i)\b(edited|compiled|edit[eé] par|herausgegeben|hrsg|a cura di|editado|editores?|editors?|eds?\.|coordinated|coordonn[ée]e?s? par|sous la direction de|dir\.)')


def lnorm(t):
    import unicodedata
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'\s*&\s*', ' and ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t).strip()
    return LEAD_ART.sub('', t)


def split_names(seg):
    seg = seg.split(' = ')[0]          # a parallel statement of responsibility in another language
    seg = re.sub(r'\([^)]*\)?', ' ', seg)                                   # '(professor of ..., London School ...)'
    seg = re.sub(r'(?i)^\s*(?:and\s+)?(?:edited|compiled)\s+by\s+', '', seg)
    # a following sentence names other roles ('Ferd Williams. Assistant editors: B. Baron'; 'Contributors: ...')
    seg = re.split(r'\.\s+(?=[A-Z][\w ]{0,30}:)|\s+(?:with|unter Mitarbeit|in collaboration)\b', seg)[0]
    seg = re.sub(r'(?i)\[|\]|\bet al\.?|\(eds?\.?\)|\beds?\.$|\beditors?$|\bcompilers?$', ' ', seg)
    out = []
    for part in re.split(r',\s*(?:and\s+)?|\s+and\s+|\s*&\s*|\s+et\s+|\s+und\s+|\s+y\s+|\s+e\s+|\s+i\s+|\s+og\s+|\s+en\s+', seg):
        part = re.sub(r'(?i)^\s*(?:by|par|von|di|por|de|durch)\s+', '', part).strip(' .;:')
        if 2 <= len(part) <= 60 and ':' not in part and re.search(r'[A-Za-zÀ-ÿ]{2}', part) and len(part.split()) >= 2 and not re.search(
                r'(?i)\b(introduction|foreword|preface|translat|illustrat|contributions?|assistance|collaboration|others|university|press|society|institute|committee)\b', part):
            out.append(part)
    return out


# 2026-11-12: a role word before 'editor' that names another job ('Graeme Wynn, cartographic editor', 'picture editor',
# 'assistant editor') or a part of the book that is not the volume ('maps edited by', 'series edited by'): the name is
# not the volume's editor. Words that keep the plain editor role:
EDITOR_QUALIFIER_OK = {'co', 'joint', 'volume', 'guest', 'book', 'coordinating', 'director', 'y', 'and', 'the', 'others', 'al'}
NOT_VOLUME_PART = re.compile(r'(?i)\b(series|maps?|cartograph\w*|illustrations?|photographs?|pictures?|plates|music|index|'
                             r'indexes|appendix|appendices|bibliograph\w*|glossary|gazetteer|atlas|charts?|figures)\b')


def edit_clause_names(resp):
    """names the 245 $c gives as editors or compilers: 'edited by X and Y', 'X and Y, editors', 'X (ed.)'; never a
    series or general editor, never a name only in a foreword / introduction / translation clause, never an editor
    whose role word is qualified by another job ('X, cartographic editor', 'Y, picture editor', 'Z, assistant editor')
    or who edited a part of the book ('maps edited by X', 'series edited by Y')"""
    names = []
    for clause in re.split(r'\s*;\s*|\s+/\s+|\.\s+(?=[A-Z][\w ]{0,30}:)', resp or ''):
        if SERIES_PHRASE.search(clause) or not EDIT_WORD.search(clause):
            continue
        m = re.search(r'(?i)\b(?:edited|compiled|coordinated|edit[eé] par|herausgegeben|hrsg\.?|a cura di|editado|coordonn[ée]e?s? par|sous la direction de)'
                      r'(?:\s*,?\s*(?:and\s+)?(?:with\s+)?(?:an?\s+)?(?:new\s+)?(?:introduction|introductions|preface|foreword|notes|commentary|annotations?)[a-z ,]*?)?\s*(?:by|von|par|da|por|de)?\s+(.+)$', clause)
        if m and not re.search(r'(?i)translat', clause[:m.start(1)]):
            # the part of the book the verb governs: 'Maps edited by X' / 'series edited by Y' (the words before the verb)
            if NOT_VOLUME_PART.search(clause[:m.start()]):
                continue
            names += split_names(re.split(r'(?i)\s+with\s+|\s+in collaboration\s+|\s+assisted\s+', m.group(1))[0])
            continue
        # 'Frederick F. Wherry, editor, Juliet Schor, consulting editor': one sub-clause per role word
        parts = re.split(r'(?i)(?<=\beditor)\s*,\s*(?=[A-ZÀ-Ý])|(?<=\beditors)\s*,\s*(?=[A-ZÀ-Ý])', clause)
        for sub in parts:
            m = re.match(r'(?i)^\s*(.+?)[,(]?\s*\(?(?:editors?|eds?\.?|compilers?|comps?\.?|editores|[ée]diteurs?|hrsg\.?|dir\.?|coords?\.?)\)?\s*\.?\s*$', sub)
            if not m:
                continue
            # lower-case words just before the role word qualify it ('cartographic editor'): another job unless 'co-',
            # 'joint', 'volume', 'guest', 'book', 'coordinating'
            tail = re.search(r'((?:\b[a-z][a-z-]*\s*)+)$', m.group(1).rstrip(' ,('))
            if tail and any(w.strip('-') not in EDITOR_QUALIFIER_OK for w in tail.group(1).split()):
                continue
            names += split_names(m.group(1))
    return names


def isbn10(x):
    core = x[3:12]
    s = sum((10 - i) * int(c) for i, c in enumerate(core))
    c = (11 - s % 11) % 11
    return core + ('x' if c == 10 else str(c))


def lc(args):
    """printed editors of the volumes from LC 2016 records matched by LCCN anchor, ISBN, or title + year"""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from link_cited_work_authors import heading_dates, yr
    from link_work_people import agree_level, apos, CONTRIB_PHRASE, CONTRIB_RELATOR
    db = duck()
    vols = db.execute(f"SELECT key, label, year, isbn, anchors FROM '{SCR}/volumes.parquet'").fetchall()
    keys = []
    for k, lab, y, isbn, an in vols:
        an = an or []
        for a in an:
            if a.startswith('lccn:'):
                keys.append((k, 'lccn', a[5:], y))
        isb = {re.sub(r'[^0-9x]', '', x.lower()) for x in (isbn or '').split(';') if x.strip()}
        isb |= {re.sub(r'[^0-9x]', '', a[5:].lower()) for a in an if a.startswith('isbn:')}
        isb |= {isbn10(x) for x in isb if len(x) == 13 and x.startswith('978')}
        for x in isb:
            if len(x) in (10, 13):
                keys.append((k, 'isbn', x, y))
        full = lnorm(re.split(r'\s+/\s+', lab or '')[0])
        main = lnorm(re.split(r'[:.?!]\s', (lab or '') + ' ', maxsplit=1)[0])
        if len(full) >= 12 and len(full.split()) >= 2:
            keys.append((k, 'title', full, y))
        if main != full and len(main.split()) >= 4:
            keys.append((k, 'main-title', main, y))
    db.register('vk_df', pa.table({'key': [r[0] for r in keys], 'how': [r[1] for r in keys], 'val': [r[2] for r in keys],
                                   'year': pa.array([r[3] for r in keys], pa.int32())}))
    db.execute("CREATE TABLE vk AS SELECT * FROM vk_df")
    print(db.execute("SELECT how, count(*), count(DISTINCT key) FROM vk GROUP BY 1").fetchall(), flush=True)
    # LC side (records with a match key only)
    db.execute(f"""CREATE TABLE rec AS SELECT control, lccn, isbns, title, title_a, TRY_CAST(date1 AS INTEGER) y, responsibility
                   FROM '{LC_REC}'""")
    norm = lambda col: (f"ltrim(regexp_replace(trim(regexp_replace(lower(strip_accents(replace({col}, '&', ' and '))), '[^a-z0-9]+', ' ', 'g')), "
                        "'^(the|a|an|le|la|les|l|der|die|das|el|los|las|il|lo|gli|une|un|de) ', ''))")
    db.execute(f"CREATE TABLE rn AS SELECT control, y, {norm('title')} ft, {norm('title_a')} ma FROM rec")
    db.execute("""CREATE TABLE m AS
        SELECT vk.key, 'lccn' how, r.control FROM vk JOIN rec r ON r.lccn = vk.val WHERE vk.how = 'lccn'
        UNION SELECT vk.key, 'isbn', r.control FROM vk JOIN (SELECT control, lower(regexp_replace(unnest(isbns), '[^0-9Xx]', '', 'g')) i FROM rec) r
              ON r.i = vk.val WHERE vk.how = 'isbn'
        UNION SELECT vk.key, 'title', rn.control FROM vk JOIN rn ON rn.ft = vk.val AND abs(rn.y - vk.year) <= 1 WHERE vk.how = 'title'
        UNION SELECT vk.key, 'title', rn.control FROM vk JOIN rn ON rn.ma = vk.val AND abs(rn.y - vk.year) <= 1 WHERE vk.how = 'title'
        UNION SELECT vk.key, 'main-title', rn.control FROM vk JOIN rn ON rn.ma = vk.val AND abs(rn.y - vk.year) <= 1 WHERE vk.how = 'main-title'""")
    # precedence: lccn, isbn, title (one record), main-title (one record)
    db.execute("""CREATE TABLE pick AS WITH c AS (SELECT key, how, count(DISTINCT control) n FROM m GROUP BY 1, 2),
        best AS (SELECT key, min(CASE how WHEN 'lccn' THEN 1 WHEN 'isbn' THEN 2 WHEN 'title' THEN 3 ELSE 4 END) r FROM c
                 WHERE how IN ('lccn', 'isbn') OR n = 1 GROUP BY 1)
        SELECT DISTINCT m.key, m.how, m.control FROM m JOIN best ON best.key = m.key
        AND best.r = CASE m.how WHEN 'lccn' THEN 1 WHEN 'isbn' THEN 2 WHEN 'title' THEN 3 ELSE 4 END""")
    print(db.execute("SELECT how, count(DISTINCT key), count(*) FROM pick GROUP BY 1").fetchall(), flush=True)
    db.execute(f"COPY pick TO '{SCR}/lc-matched.parquet' (FORMAT parquet)")
    recs = {c: (resp, t, y) for c, resp, t, y in db.execute(
        "SELECT r.control, r.responsibility, r.title, r.y FROM rec r WHERE r.control IN (SELECT control FROM pick)").fetchall()}
    heads = collections.defaultdict(list)
    for c, pos, tag, h, rel in db.execute(f"""SELECT control, pos, tag, heading, relators FROM '{LC_HEAD}'
            WHERE control IN (SELECT control FROM pick) AND tag IN ('100', '700') ORDER BY control, pos""").fetchall():
        heads[c].append((tag, h, rel or []))
    picks = collections.defaultdict(list)
    for k, how, c in db.execute("SELECT key, how, control FROM pick").fetchall():
        picks[k].append((how, c))
    vlab = {k: lab for k, lab, *_ in vols}
    isbn_mismatch = 0
    from author_works import tkey, main_key

    def same_title_lc(a, b):
        a = re.split(r'\s+/\s+', a or '')[0]
        ta, tb = tkey(a), tkey(b)
        if not ta or not tb:
            return False
        if ta == tb or main_key(a) == main_key(b) or ta.startswith(tb + ' ') or tb.startswith(ta + ' '):
            return True
        wa, wb = set(ta.split()), set(tb.split())
        return len(wa & wb) / max(1, min(len(wa), len(wb))) >= 0.8
    rows = []
    for k, ps in picks.items():
        seen = []
        for how, c in sorted(ps, key=lambda x: x[1]):
            resp, title, y = recs.get(c, ('', '', None))
            if how == 'isbn' and not same_title_lc(vlab.get(k, ''), title):
                # the ISBN printed with a chapter names the book, but this volume node bears another title (often the
                # series': 'Late Medieval and Early Modern Studies'): the record's editors are not this node's
                isbn_mismatch += 1
                continue
            clause = edit_clause_names(resp)
            contrib = [p.strip() for cl in re.split(r';', resp or '') for seg in CONTRIB_PHRASE.findall(cl) for p in re.split(r',|\band\b|&', seg) if p.strip()]
            got = []
            for tag, h, rel in heads.get(c, ()):
                if tag != '700':
                    continue
                is_ed_rel = any(EDIT_REL.match(r.strip(' .,')) for r in rel)
                is_contrib_rel = any(CONTRIB_RELATOR.search(r) for r in rel) and not is_ed_rel
                in_clause = any(agree_level(apos(h), apos(n)) in ('full', 'variant', 'initial') for n in clause)
                in_contrib = any(agree_level(apos(h), apos(n)) in ('full', 'variant', 'initial') for n in contrib)
                if is_contrib_rel:
                    continue
                if is_ed_rel and in_contrib and not in_clause:
                    continue
                if is_ed_rel or (not rel and in_clause):
                    got.append((h, 'lc-700' + (':relator' if is_ed_rel else ':245c')))
            for n in clause:
                if not any(agree_level(apos(n), apos(h)) in ('full', 'variant', 'initial') for h, _ in got):
                    if not any(agree_level(apos(n), apos(h)) in ('full', 'variant', 'initial') for t_, h, r_ in heads.get(c, ()) if t_ == '100'):
                        got.append((n, 'lc-245c'))
            for h, basis in got:
                if any(agree_level(apos(h), apos(x)) in ('full', 'variant') for x, *_ in seen):
                    continue
                seen.append((h, basis, how, c, resp))
        for i, (h, basis, how, c, resp) in enumerate(seen):
            rows.append(dict(volume=k, position=i, printed_name=h, source='lc', basis=f'{basis};match:{how};control:{c}',
                             lc_resp=(resp or '')[:300]))
    pq.write_table(pa.Table.from_pylist(rows), SCR / 'lc-editors.parquet')
    print(len(rows), 'editor names on', len({r['volume'] for r in rows}), 'volumes;', len(picks), 'volumes matched to LC;',
          isbn_mismatch, 'ISBN matches dropped (record title is not the volume title)', flush=True)
    (SCR / 'lc-stats.json').write_text(json.dumps(dict(isbn_title_mismatch_dropped=isbn_mismatch, volumes_matched=len(picks),
                                                       volumes_with_editors=len({r['volume'] for r in rows}), names=len(rows))))
    print(collections.Counter(r['basis'].split(';')[0] for r in rows), collections.Counter(r['basis'].split(';')[1] for r in rows))


# ---------------------------------------------------------------- Crossref editors

BOOK_TYPES = {'book', 'edited-book', 'monograph', 'reference-book'}
LONG_LIST = 6


def crossref_editors():
    """volume -> dict(source detail, type, title, isbn, editors [(name, orcid)]) from the book record, else a chapter
    record of the volume (Crossref chapter records copy the book's editors when they carry any)"""
    from export_work_containers import cr_row
    from author_works import tkey, main_key
    db = duck()
    vtitle = {k: (lab, y) for k, lab, y in db.execute(f"SELECT key, label, year FROM '{SCR}/volumes.parquet'").fetchall()}
    book_vol = collections.defaultdict(set)
    for fn in ('fetch-books.tsv', 'fetch-gold-books.tsv', 'fetch-books2.tsv'):
        if not (SCR / fn).exists():
            continue
        for line in open(SCR / fn):
            v, d, how = line.rstrip('\n').split('\t')
            book_vol[d].add((v, how))
    ch_vol = collections.defaultdict(set)
    for v, d in db.execute(f"SELECT v, d FROM '{SCR}/chapter-dois.parquet'").fetchall():
        ch_vol[d].add(v)

    def same_title(a, b):
        ta, tb = tkey(a), tkey(b)
        if not ta or not tb:
            return False
        if ta == tb or main_key(a) == main_key(b) or ta.startswith(tb + ' ') or tb.startswith(ta + ' '):
            return True
        wa, wb = set(ta.split()), set(tb.split())
        return len(wa & wb) / max(1, min(len(wa), len(wb))) >= 0.8

    out, stats = {}, collections.Counter()
    for p in sorted(CR_BOOKS.glob('part-*.jsonl')):
        for it in jl(p):
            for v, how in book_vol.get(it['_doi'], ()):
                if it.get('_missing'):
                    stats['book-404'] += 1
                    continue
                if it.get('type') not in BOOK_TYPES:
                    stats[f"book-type-{it.get('type')}"] += 1
                    continue
                r = cr_row(it)
                lab = vtitle.get(v, ('', None))[0]
                if not same_title(r['title'] or '', lab) and not same_title(' '.join(it.get('title') or []) + ' ' + ' '.join(it.get('subtitle') or []), lab):
                    if not how.startswith('own'):
                        stats['book-title-mismatch-derived-dropped'] += 1
                        continue
                    # the volume's own DOI names this book: the node's label is what differs (a series or section title
                    # from the chapter's record: 'Boston Studies in the Philosophy of Science'); counted, kept
                    stats['book-title-differs-own-doi-kept'] += 1
                eds = [(nm, (e.get('ORCID') or '').rsplit('/', 1)[-1]) for nm, e in zip(r['editors'], it.get('editor') or []) if nm]
                if v in out and out[v]['editors'] and not eds:
                    continue
                out[v] = dict(detail=f'crossref-book:{how}:{it["_doi"]}', type=it.get('type'), editors=eds, isbn=r['isbn'], year=r['year'])
                stats['book-editors' if eds else f"book-no-editor-{it.get('type')}"] += 1
    for p in sorted(CR_CHAPTERS.glob('part-*.jsonl')):
        for it in jl(p):
            if it.get('_missing'):
                continue
            for v in ch_vol.get(it['_doi'], ()):
                if v in out and out[v]['editors']:
                    continue
                r = cr_row(it)
                lab = vtitle.get(v, ('', None))[0]
                if r['container'] and not same_title(r['container'], lab):
                    stats['chapter-container-mismatch'] += 1
                    continue
                eds = [(nm, (e.get('ORCID') or '').rsplit('/', 1)[-1]) for nm, e in zip(r['editors'], it.get('editor') or []) if nm]
                if eds or v not in out:
                    out[v] = dict(detail=f'crossref-chapter:{it["_doi"]}', type='chapter-record', editors=eds, isbn=r['isbn'], year=r['year'])
                stats['chapter-editors' if eds else 'chapter-no-editor'] += 1
    return out, stats


# ---------------------------------------------------------------- positions

MIXED = collections.Counter()


def crossref_list(eds):
    """Crossref book records of some publishers (the De Gruyter-hosted ones) list the chapter contributors under
    `editor` after the editors, and repeat an editor who also wrote a chapter: in a list with a repeated name, the
    repeated names are the editors and the rest are dropped; a list of more than LONG_LIST names with no repeat is kept
    whole and held in link. -> (editors, basis note)"""
    from link_work_people import agree_level, apos
    seen, rep = [], []
    for nm, orc in eds:
        if any(agree_level(apos(nm), apos(x)) == 'full' for x, _ in seen):
            if not any(agree_level(apos(nm), apos(x)) == 'full' for x, _ in rep):
                rep.append((nm, orc))
            continue
        seen.append((nm, orc))
    if rep and len(eds) > 3:
        keep = [x for x in seen if any(agree_level(apos(x[0]), apos(r)) == 'full' for r, _ in rep)]
        MIXED['lists'] += 1
        MIXED['names_dropped'] += len(seen) - len(keep)
        return keep, f';mixed-list:{len(keep)}-of-{len(seen)}-repeated-names-kept'
    return seen, ''

def positions(args):
    """one row per printed editor of a volume: LC first, else Crossref; with the LC authority of a 700 heading (the
    heading rule of link_cited_work_authors.load_sources: URI, else the heading equal to one authority label), the
    ORCID Crossref prints, and the key-log credits the name agrees with"""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from link_cited_work_authors import heading_dates, yr
    from link_work_people import agree_level, apos
    db = duck()
    vol = {r[0]: r for r in db.execute(f"""SELECT key, resolution, kind, year, label, n_ch, n_auth, n_ed, editors_printed
            FROM '{SCR}/volumes.parquet'""").fetchall()}
    lcrows = collections.defaultdict(list)
    for r in db.execute(f"SELECT volume, position, printed_name, basis, lc_resp FROM '{SCR}/lc-editors.parquet' ORDER BY volume, position").fetchall():
        lcrows[r[0]].append(r)
    cr, cstats = crossref_editors()
    print('crossref', dict(cstats), flush=True)
    # printed editors already on the volume (author-works volumes table)
    rows = []
    for v, (_, res, kind, y, lab, n_ch, n_auth, n_ed, pr) in vol.items():
        if lcrows.get(v):
            for _, i, nm, basis, resp in lcrows[v]:
                rows.append(dict(work=v, pos=i, n_auth=len(lcrows[v]), name=nm, source='lc', basis=basis, orcid='', year=y))
        elif v in cr and cr[v]['editors']:
            eds, extra = crossref_list(cr[v]['editors'])
            for i, (nm, orc) in enumerate(eds):
                rows.append(dict(work=v, pos=i, n_auth=len(eds), name=nm, source='crossref', basis=cr[v]['detail'] + extra,
                                 orcid=orc or '', year=y or cr[v]['year']))
        elif pr:
            eds = [x.strip() for x in pr.split(';') if x.strip()]
            for i, nm in enumerate(eds):
                rows.append(dict(work=v, pos=i, n_auth=len(eds), name=nm, source='printed', basis='work.editors_printed', orcid='', year=y))
    # volumes with a record that names no editor (LC record / Crossref book record) : monograph evidence for the report
    nofound = {v: cr[v]['type'] for v in cr if not cr[v]['editors'] and not lcrows.get(v)}
    (SCR / 'crossref-no-editor.json').write_text(json.dumps(nofound))
    # LC authority of each heading
    heads = sorted({re.sub(r'[.,\s]+$', '', r['name']) for r in rows if r['source'] == 'lc' and ',' in r['name']})
    db.register('hd', pa.table({'label': heads}))
    by_label = collections.defaultdict(list)
    for lcid, label, b, d in db.execute(f"SELECT n.lcid, hd.label, n.birth, n.death FROM '{LC_NAMES}' n JOIN hd ON n.label = hd.label WHERE NOT n.deprecated").fetchall():
        by_label[label].append((lcid, yr(b), yr(d)))
    # key-log credits on the volume
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    orcid_of = collections.defaultdict(set)
    for k, o in db.execute(f"SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'orcid:%'").fetchall():
        orcid_of[k].add(o[6:])
    wanted = {r['work'] for r in rows}
    db.register('ww', pa.table({'w': sorted(wanted)}))
    credits = collections.defaultdict(list)     # volume -> [(key, relation, evidence)]
    for rel in ('edited', 'authored'):
        for k, w, ev in db.execute(f"""SELECT DISTINCT "from", "to", evidence FROM '{G}/{rel}.parquet' WHERE "to" IN (SELECT w FROM ww)""").fetchall():
            credits[w].append((k, rel, ev))
    order = ('full', 'variant', 'initial')
    for i, r in enumerate(rows):
        r['pid'] = i
        h = re.sub(r'[.,\s]+$', '', r['name'])
        c = by_label.get(h, []) if r['source'] == 'lc' else []
        r['lc'] = [c[0][0]] if len(c) == 1 else []
        hb, hd_ = heading_dates(r['name']) if r['source'] == 'lc' else (None, None)
        r['sb'] = (c[0][1] if len(c) == 1 else None) or hb
        r['sd'] = (c[0][2] if len(c) == 1 else None) or hd_
        r['name_plain'] = re.sub(r',?\s*(\(|\d{3,4}\??-|b\. |d\. ).*$', '', r['name']).strip() if r['source'] == 'lc' else r['name']
        best = None
        for k, rel, ev in credits.get(r['work'], ()):
            if r['orcid'] and r['orcid'] in orcid_of.get(k, ()):
                lev = 'orcid'
            else:
                lev = agree_level(apos(r['name_plain']), apos(label.get(k, '')))
            if not lev:
                continue
            rank = (0 if lev == 'orcid' else 1 + order.index(lev), 0 if rel == 'edited' else 1, 0 if ev == 'keylog' else 1)
            if best is None or rank < best[0]:
                best = (rank, k, rel, ev, lev)
        r['credited'] = best[1] if best else ''
        r['credited_how'] = f'{best[2]}:{best[3]}:{best[4]}' if best else ''
    # one position per credited key per volume (the better agreement keeps it)
    by = collections.defaultdict(list)
    for r in rows:
        if r['credited']:
            by[r['work'], r['credited']].append(r)
    for rs in by.values():
        for r in sorted(rs, key=lambda r: (r['credited_how'].endswith('orcid') is False, r['pos']))[1:]:
            r['credited'], r['credited_how'] = '', ''
    cstats.update({f'mixed-{k}': v for k, v in MIXED.items()})
    (SCR / 'crossref-stats.json').write_text(json.dumps(dict(cstats), indent=1))
    pq.write_table(pa.Table.from_pylist(rows), SCR / 'positions.parquet')
    print(len(rows), 'positions on', len(wanted), 'volumes', collections.Counter(r['source'] for r in rows),
          collections.Counter(r['credited_how'].rsplit(':', 1)[0] for r in rows if r['credited']), flush=True)


# ---------------------------------------------------------------- link

def link(args):
    import random
    import pyarrow as pa
    import pyarrow.parquet as pq
    import link_cited_work_authors as L
    L.GRAPH = G
    import link_work_people as W
    from graph_tables import keylog
    from link_cited_work_authors import forms
    t0 = time.time()
    db = W.duck()
    people = W.WPPeople(db)
    print('people', round(time.time() - t0), flush=True)
    T = pq.read_table(SCR / 'positions.parquet').to_pylist()
    works = {r['work'] for r in T}
    db.register('ww', pa.table({'w': sorted(works)}))
    # the volume's own key-log credits and its chapters' key-log authors: the 'coauthor' fact's known people
    vol_keys = collections.defaultdict(set)
    for k, w in db.execute(f"""SELECT "from", "to" FROM {keylog(G, 'authored')} WHERE "to" IN (SELECT w FROM ww)
            UNION SELECT "from", "to" FROM {keylog(G, 'edited')} WHERE "to" IN (SELECT w FROM ww)""").fetchall():
        vol_keys[w].add(k)
    chap_keys = collections.defaultdict(set)
    for k, w in db.execute(f"""SELECT DISTINCT a."from", p."to" FROM '{G}/part_of.parquet' p JOIN {keylog(G, 'authored')} a ON a."to" = p."from"
            WHERE p."to" IN (SELECT w FROM ww)""").fetchall():
        chap_keys[w].add(k)
    chap_any = collections.defaultdict(set)      # any evidence: a diagnostic signal only
    for k, w in db.execute(f"""SELECT DISTINCT a."from", p."to" FROM '{G}/part_of.parquet' p JOIN '{G}/authored.parquet' a ON a."to" = p."from"
            WHERE p."to" IN (SELECT w FROM ww)""").fetchall():
        chap_any[w].add(k)
    citers_of = collections.defaultdict(set)
    for w, d in db.execute(f"""SELECT c."to", replace(a, 'diss-thesis:', '') FROM '{G}/cites.parquet' c
            JOIN (SELECT key, unnest(anchors) a FROM '{G}/work.parquet' WHERE kind = 'thesis') t ON t.key = c."from"
            WHERE a LIKE 'diss-thesis:%' AND c."to" IN (SELECT w FROM ww)""").fetchall():
        citers_of[w].add(d)
    needed = set()
    for r in T:
        for f, _, g in forms(W.apos(r['name_plain']))[:1]:
            needed.add((f, g[0]))
    for lab in people.label.values():
        for f, _, g in forms(lab):
            needed.add((f, g[0]))
    pop = L.population_counts(db, needed)
    print('population', round(time.time() - t0), flush=True)
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'] = tuple(P['FACTS'])
    P['XDATE'] = tuple(P['XDATE'])
    L.PARAMS.update({k: v for k, v in P.items() if k in L.PARAMS})
    vinfo = {k: (lab, kind) for k, lab, kind in db.execute(f"SELECT key, label, kind FROM '{SCR}/volumes.parquet'").fetchall()}

    def make_pos(r):
        p = dict(src='lc' if r['source'] == 'lc' else 'crossref', swork=r['work'], work_id=r['work'], oa_id='', pos=r['pos'],
                 role='editor', name=W.apos(r['name_plain']), title=vinfo.get(r['work'], ('', ''))[0], year=r['year'], book=True,
                 lc=list(r['lc'] or []), lc_how='heading', orcid=r['orcid'] or '', oa_author='', rors=[], insts=[], raw_aff=[],
                 citing=0, sb=r['sb'], sd=r['sd'], initial_check='', venue='', oa_type='')
        p['forms'] = forms(p['name'])
        return p

    def guard_row(r):
        return dict(work=r['work'], title=vinfo.get(r['work'], ('', ''))[0], kind='book', role='editor', name=r['name_plain'], oa_work='')

    def decide(r, mask=None, drop_key=None):
        p = make_pos(r)
        ex = (vol_keys.get(r['work'], set()) | chap_keys.get(r['work'], set())) - ({drop_key} if drop_key else set())
        fe = L.features(people, p, mask=mask, exacts=ex, citers_of=citers_of)
        st, k, br, cands, sig = W.rule_wp(people, p, fe, pop, P)
        st, k, br, sig = W.guard(guard_row(r), st, k, br, sig, fe, P, {}, {}, set())
        return st, k, br, cands, sig, fe
    out = []
    for n, r in enumerate(T):
        if r['n_auth'] > LONG_LIST and not r['credited']:
            # more than six printed editors: an editorial board or a reference work's section editors; printed only
            out.append(dict(pid=r['pid'], state='held', key='', branch=f'editor-list-over-{LONG_LIST}', candidates='',
                            n_candidates=0, signals=''))
            continue
        if r['credited']:
            out.append(dict(pid=r['pid'], state='credited', key=r['credited'], branch='credited:' + r['credited_how'], candidates='',
                            n_candidates=0, signals=''))
            continue
        st, k, br, cands, sig, fe = decide(r)
        live = cands if st != 'exact' else []
        extra = []
        if k is None and live:
            hit = [c for c in live if c in chap_any.get(r['work'], ())]
            if hit:
                extra.append('chapter-author-on-volume=' + '|'.join(hit))
        out.append(dict(pid=r['pid'], state=st, key=k or '', branch=br, candidates='|'.join(live), n_candidates=len(live),
                        signals=' '.join(sig + extra)))
        if n % 20000 == 0:
            print(n, round(time.time() - t0), flush=True)
    pq.write_table(pa.Table.from_pylist(out), SCR / 'results.parquet')
    # masked gold: positions whose name agrees with a key-log EDITED or AUTHORED credit on the volume
    gold = []
    rnd = random.Random(11)
    gs = [r for r in T if r['credited'] and r['credited_how'].split(':')[1] == 'keylog']
    rnd.shuffle(gs)
    def judge(k, g):
        """a link to another key: 'dup' when it is the same person on two keys by the linker's test (names agree, no
        conflicting LC authority or ORCID, no not-same mark: link_work_people.link's judge), else 'wrong'"""
        fk, fg = forms(people.label.get(k, '')), forms(people.label.get(g, ''))
        if not any(a[0] == b[0] and W.name_level(a[2], b[2]) for a in fk for b in fg):
            return 'wrong'
        for d in (people.lcnaf, people.orcid):
            if d.get(k) and d.get(g) and not d[k] & d[g]:
                return 'wrong'
        if g in people.not_same.get(k, ()):
            return 'wrong'
        return 'dup'
    ns = []
    for r in gs[:args.gold]:
        g = r['credited']
        by_orcid = r['credited_how'].endswith('orcid')
        hid = {i for i in (r['lc'] or []) if g in people.lc_key.get(i, ())}
        # 'authority-known': the source's LC authority stays (it excludes keys holding another one); 'no-authority': the
        # key's matching authority and the source's are both hidden (the strict test, as link_cited_work_authors' gold)
        for mode, keep in (('authority-known', True), ('no-authority', False)):
            if mode == 'authority-known' and not r['lc']:
                continue
            W.HIDE[0] = (r['work'], g)
            m = dict(key=g, orcid={r['orcid']} if by_orcid else set(), lc=hid, src_orcid=not by_orcid, src_lc=keep)
            st, k, br, cands, sig, fe = decide(r, mask=m, drop_key=g)
            W.HIDE[0] = None
            cls = '' if st not in ('linked', 'exact') else 'right' if g in (k or '').split(';') else judge(k.split(';')[0], g)
            gold.append(dict(pid=r['pid'], mode=mode, how=r['credited_how'], source=r['source'], true=g, state=st, key=k or '',
                             branch=br, cls=cls, true_listed=g in (cands or []), n_live=len(cands or []), name=r['name'],
                             year=r['year'], sig=' '.join(sig)))
            if mode != 'no-authority':
                continue
            # masked author: another name-compatible key proven a different person from g (identifiers, birth or PhD
            # years, not-same mark); drop g, hide the other key's identifiers: a link to it is a false link
            b1 = people.life.get(g, (None,))[0]
            for k2 in list(fe['cands']):
                if k2 == g:
                    continue
                b2 = people.life.get(k2, (None,))[0]
                p1, p2 = people.phd.get(g), people.phd.get(k2)
                if not ((people.lcnaf.get(g) and people.lcnaf.get(k2) and not people.lcnaf[g] & people.lcnaf[k2])
                        or (people.orcid.get(g) and people.orcid.get(k2) and not people.orcid[g] & people.orcid[k2])
                        or (b1 and b2 and abs(b1 - b2) > 1) or (p1 and p2 and abs(p1 - p2) > 1) or k2 in people.not_same.get(g, ())):
                    continue
                W.HIDE[0] = (r['work'], g)
                m2 = dict(drop={g}, key=k2, lc=set(people.lcnaf.get(k2, ())), orcid=set(people.orcid.get(k2, ())), src_orcid=False, src_lc=False)
                st2, kk, br2, _, sig2, _ = decide(r, mask=m2, drop_key=g)
                W.HIDE[0] = None
                ns.append(dict(pid=r['pid'], proven=k2, true=g, state=st2, key=kk or '', branch=br2,
                               false_link=st2 in ('linked', 'exact') and k2 in (kk or '').split(';'), name=r['name'], year=r['year']))
    if ns:
        pq.write_table(pa.Table.from_pylist(ns), SCR / 'namesake.parquet')
    pq.write_table(pa.Table.from_pylist(gold), SCR / 'gold.parquet')
    print('done', round(time.time() - t0), collections.Counter(o['state'] for o in out),
          collections.Counter((g['mode'], g['state'], g['cls']) for g in gold), len(ns), sum(x['false_link'] for x in ns), flush=True)


# ---------------------------------------------------------------- series editors in Crossref editor lists (2026-11-12)

SERIES_TYPES = ('book', 'monograph', 'edited-book')
SERIES_MIN_BOOKS = 2        # books of one publisher on which the person is printed as editor beside a printed author
SERIES_COMPANION_MIN = 3    # books needed before the person's other listings at that publisher (after another editor) follow


def series_editor_flags(rows):
    """The series-editor rule (ARCHITECTURE.md section 8, class 19). A monograph has no volume editor: a Crossref book
    record that prints one or two authors (none of them also among its editors) and names someone else as `editor`
    names a series editor or an edition editor. The editor is taken as a series editor when the same person (person key
    when linked, else the printed name) is printed that way on SERIES_MIN_BOOKS or more books of one publisher whose
    printed authors differ (Cronon on the Weyerhaeuser Environmental Books). Where the pattern holds on
    SERIES_COMPANION_MIN or more books making up at least half of that person's books at the publisher, the person's
    other listings there after another editor are series listings too ('Conservation in the Progressive Era', edited by
    Stradling, Cronon listed second).
    Not used, because they misfire alone: a repeated editor name (serial annuals and yearbooks keep one editor: Polin,
    History of Universities), the Crossref type (edited volumes typed 'monograph'), records printing three or more
    'authors' (edited-book records list chapter authors there), LC records matched by title only (another book of the
    same title), and the graph's AUTHORED credits on the volume (chapter authors and co-editors filed as authors).
    rows: dicts with idx, volume, position, who, publisher, rec_type, authors, editors (the record's lists; empty when the
    row's record is not a book-level Crossref record). Returns {idx: (flag, detail)}; flag 'printed-author' or
    'listed-after'."""
    from link_work_people import agree_level, apos
    ag = lambda a, b: agree_level(apos(a), apos(b)) in ('full', 'variant', 'initial')
    nn = lambda s: re.sub(r'[^a-z]+', ' ', apos(s or '').lower()).strip()
    facts = {}
    for r in rows:
        if r.get('rec_type') not in SERIES_TYPES:
            continue
        au = [a for a in r['authors'] if a and not any(ag(a, e) for e in r['editors'])]
        printed = au if 1 <= len(au) <= 2 and len(r['authors']) <= 2 else []
        first_other = bool(r['editors']) and not ag(r['editors'][0], r['name'])
        facts[r['idx']] = (printed, first_other)
    groups = collections.defaultdict(list)
    for r in rows:
        if r['idx'] in facts:
            groups[r['who'], nn(r['publisher'])].append(r)
    out = {}
    for (who, pub), rs in groups.items():
        if not pub:
            continue
        pv = {r['volume']: nn(facts[r['idx']][0][0]) for r in rs if facts[r['idx']][0]}
        if len(pv) < SERIES_MIN_BOOKS or len(set(pv.values())) < SERIES_MIN_BOOKS:
            continue
        vols = {r['volume'] for r in rs}
        companion = len(pv) >= SERIES_COMPANION_MIN and 2 * len(pv) >= len(vols)
        detail = f"printed as editor on {len(pv)} books of {rs[0]['publisher']} by {len(set(pv.values()))} different printed authors"
        for r in rs:
            printed, first_other = facts[r['idx']]
            if printed:
                out[r['idx']] = ('printed-author', f"record prints author {'; '.join(printed)}; {detail}")
            elif companion and first_other and r['position'] > 0:
                out[r['idx']] = ('listed-after', f"listed after {r['editors'][0]}; {detail}")
    return out


def crossref_book_records():
    """book-level Crossref records held (build/crossref-volume-editors-2026-11-11): doi -> type, publisher, printed
    author and editor names"""
    recs = {}
    for p in sorted(CR_BOOKS.glob('part-*.jsonl')):
        for it in jl(p):
            if it.get('_missing'):
                continue
            nm = lambda e: ' '.join(x for x in (e.get('given'), e.get('family')) if x) or e.get('name') or ''
            recs[it['_doi']] = dict(type=it.get('type'), publisher=it.get('publisher') or '',
                                    authors=[nm(a) for a in it.get('author') or []], editors=[nm(e) for e in it.get('editor') or []])
    return recs


def series_rule_rows(out, recs):
    """the rule's input rows from the export rows (Crossref rows whose record is a book-level record)"""
    from link_work_people import apos
    rows = []
    for i, r in enumerate(out):
        if r['source'] != 'crossref':
            continue
        m = re.match(r'crossref-book:[a-z0-9]+:(10\.\S+?)(?:;|$)', r['basis'])
        rec = recs.get(m.group(1)) if m else None
        if not rec:
            continue
        who = r['person_key'] if r['state'] in ('exact', 'linked', 'credited') and r['person_key'] else \
            'name:' + re.sub(r'[^a-z]+', ' ', apos(r['printed_name']).lower()).strip()
        rows.append(dict(idx=i, volume=r['volume'], position=int(r['position']), name=r['printed_name'], who=who,
                         publisher=rec['publisher'], rec_type=rec['type'], authors=rec['authors'], editors=rec['editors']))
    return rows


def series_check_credits(rule_rows, flags, recs):
    """the same rule over the other editor credits of the last graph build (build/graph: key-log and edition-roles
    EDITED credits, and AUTHORED credits with role volume-editor; not the volume-editors rows): volumes with a held
    book-level Crossref record (the fetch lists of `targets`), the person printed as editor on it. Counted only."""
    from link_work_people import agree_level, apos
    bg = ROOT / 'build/graph'
    db = duck()
    vol_doi = {}
    for fn in ('fetch-books.tsv', 'fetch-gold-books.tsv', 'fetch-books2.tsv'):
        if (SCR / fn).exists():
            for line in open(SCR / fn):
                v, d, _ = line.rstrip('\n').split('\t')
                if d in recs:
                    vol_doi.setdefault(v, d)
    label = dict(db.execute(f"SELECT key, label FROM '{bg}/person.parquet'").fetchall())
    cred = db.execute(f"""SELECT "from", "to", 'edited', evidence, role FROM '{bg}/edited.parquet'
                          WHERE coalesce(source, '') NOT LIKE 'volume-editors%'
                          UNION ALL SELECT "from", "to", 'authored', evidence, role FROM '{bg}/authored.parquet'
                          WHERE role = 'volume-editor'""").fetchall()
    plain = lambda l: (lambda s: (s.split(',', 1)[1].strip() + ' ' + s.split(',', 1)[0].strip()) if ',' in s else s)(
        re.sub(r',?\s*(\(|\d{3,4}\??-|b\. |d\. ).*$', '', l or '').strip(' .,'))
    rows, meta = list(rule_rows), {}
    n0 = max([r['idx'] for r in rows], default=0) + 1
    for i, (k, w, c, ev, role) in enumerate(cred):
        d = vol_doi.get(w)
        if not d:
            continue
        rec = recs[d]
        nm = plain(label.get(k, ''))
        if not any(agree_level(apos(e), apos(nm)) in ('full', 'variant', 'initial') for e in rec['editors']):
            continue            # the record does not print the person as editor: the rule says nothing
        pos = next(j for j, e in enumerate(rec['editors']) if agree_level(apos(e), apos(nm)) in ('full', 'variant', 'initial'))
        rows.append(dict(idx=n0 + i, volume=w, position=pos, name=nm, who=k, publisher=rec['publisher'], rec_type=rec['type'],
                         authors=rec['authors'], editors=rec['editors']))
        meta[n0 + i] = (k, w, c, ev, role)
    fl = series_editor_flags(rows)
    hit = collections.Counter(f'{c}|{ev}|{role}' for i, (k, w, c, ev, role) in meta.items() if i in fl)
    return dict(note=('the rule applied to the other editor credits of the last build (key-log and edition-roles EDITED, '
                      'AUTHORED role volume-editor) on volumes with a held book-level Crossref record printing the person as '
                      'editor; counted, nothing changed'),
                credits_on_volumes_with_a_record=sum(1 for k, w, *_ in cred if w in vol_doi),
                credits_printed_as_editor_on_the_record=len(meta), flagged=dict(hit),
                flagged_pairs=[dict(person=meta[i][0], work=meta[i][1], credit=meta[i][2], evidence=meta[i][3], role=meta[i][4],
                                    detail=fl[i][1]) for i in sorted(fl) if i in meta][:50])


# ---------------------------------------------------------------- export

PROBES = ['w-2333986', 'w-916866', 'doi:10.1093/oxfordhb/9780197502679.001.0001', 'volume:56de888d833b',
          'w-1115644', 'w-88030', 'doi:10.1515/9780295803807']


def export(args):
    db = duck()
    db.execute(f"""CREATE TABLE r AS SELECT p.work volume, p.pos AS "position", p.name printed_name, p.source, p.basis src_basis,
            p.orcid, p.credited, p.credited_how, x.state, x.key, x.branch, x.candidates, x.n_candidates, x.signals
            FROM '{SCR}/positions.parquet' p JOIN '{SCR}/results.parquet' x USING (pid)""")
    rows = db.execute("SELECT * FROM r ORDER BY volume, \"position\"").fetchall()
    cols = [d[0] for d in db.description]
    out = []
    for t in rows:
        r = dict(zip(cols, t))
        basis = r['src_basis']
        if r['state'] == 'credited':
            basis += f"; name agrees with the volume's {r['credited_how'].replace(':', ' ', 1)} credit"
        else:
            basis += f"; linker {r['branch']}" + (f" [{r['signals']}]" if r['signals'] else '')
        if r['orcid']:
            basis += f"; orcid {r['orcid']}"
        out.append(dict(volume=r['volume'], position=r['position'], printed_name=r['printed_name'], source=r['source'],
                        state=r['state'], person_key=r['key'] or '', candidates=(r['candidates'] or '').replace('|', ';'),
                        basis=basis))
    # series editors (class 19): state 'series-editor'; the person key stays only where the linker credited it
    # (exact / linked / credited), so the build can load the pair as CONTRIBUTED; never an EDITED row
    recs = crossref_book_records()
    rule_rows = series_rule_rows(out, recs)
    flags = series_editor_flags(rule_rows)
    series_before = collections.Counter()
    for i, (flag, detail) in flags.items():
        r = out[i]
        series_before[f"{flag}|{r['state']}"] += 1
        if r['state'] not in ('exact', 'linked', 'credited'):
            r['person_key'] = ''
        r['basis'] += f"; series-editor rule ({flag}): {detail}; was {r['state']}"
        r['state'] = 'series-editor'
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['volume', 'position', 'printed_name', 'source', 'state', 'person_key', 'candidates', 'basis'])
        w.writeheader()
        w.writerows(out)
    q = lambda s: db.execute(s).fetchall()
    rep = dict(made_by='scripts/volume_editors.py export', date='2026-11-11', rows=len(out))
    rep['class_before'] = json.loads((SCR / 'class-before.json').read_text())
    rep['rows_by_source_state'] = {f'{a}|{b}': n for a, b, n in q("SELECT source, state, count(*) FROM r GROUP BY ALL ORDER BY ALL")}
    rep['volumes_by_source'] = dict(q("SELECT source, count(DISTINCT volume) FROM r GROUP BY 1"))
    rep['credited_how'] = dict(q("SELECT credited_how, count(*) FROM r WHERE state = 'credited' GROUP BY 1 ORDER BY 2 DESC"))
    rep['branches'] = {f'{a}|{b}': n for a, b, n in q("SELECT state, branch, count(*) FROM r WHERE state <> 'credited' GROUP BY ALL ORDER BY 3 DESC LIMIT 40")}
    rep['rows_by_source_state_after_series_rule'] = dict(sorted(collections.Counter(f"{r['source']}|{r['state']}" for r in out).items()))
    rep['series_editor_rule'] = dict(
        note=('class 19: Crossref book records printing one or two authors and naming the person as editor, on 2+ books of '
              'one publisher by different printed authors (series_editor_flags); rows set to state series-editor (printed '
              'only, not editors_printed, no EDITED row; loaded as CONTRIBUTED where the linker had credited a person)'),
        rows=len(flags), by_flag_and_former_state=dict(sorted(series_before.items())),
        people_or_names=len({x['who'] for x in rule_rows if x['idx'] in flags}),
        crossref_rows_with_a_book_record=len(rule_rows))
    if AUDIT.exists():
        a = list(csv.DictReader(open(AUDIT, encoding='utf-8')))
        by = collections.defaultdict(collections.Counter)
        for x in a:
            by[x['stratum']][x['judgment']] += 1
        rep['series_editor_rule']['audit'] = dict(file=str(AUDIT.relative_to(ROOT)), judgments={k: dict(v) for k, v in by.items()})
    try:
        rep['series_editor_rule']['keylog_and_edition_roles_check'] = series_check_credits(rule_rows, flags, recs)
    except Exception as e:          # needs a graph build with roles
        rep['series_editor_rule']['keylog_and_edition_roles_check'] = f'not run: {e}'
    rep['possible_one_candidate'] = q("SELECT count(*) FROM r WHERE state = 'possible' AND n_candidates = 1")[0][0]
    rep['chapter_author_signal'] = dict(note='possible/ambiguous rows whose candidate is also a credited author of a chapter of the volume '
                                             '(diagnostic only: not a rule of the linker, so it decides nothing)',
                                        rows=q("SELECT count(*) FROM r WHERE signals LIKE '%chapter-author-on-volume%'")[0][0])
    # class after: EDITED (existing + exact/linked/credited rows here) and printed editors (existing + every row here)
    db.execute(f"CREATE TABLE v AS SELECT * FROM '{SCR}/volumes.parquet'")
    db.execute("""CREATE TABLE v2 AS SELECT v.*, coalesce(e.n_new, 0) n_new_ed, coalesce(e.n_rows, 0) n_rows FROM v LEFT JOIN
        (SELECT volume, count(DISTINCT key) FILTER (WHERE state IN ('exact', 'linked') OR (state = 'credited' AND credited_how NOT LIKE 'edited:%')) n_new,
                count(*) FILTER (WHERE state <> 'held') n_rows FROM r GROUP BY 1) e ON e.volume = v.key""")
    rep['class_after'] = dict(
        no_printed_editor_and_no_edited=class_counts(db, 'v2', "n_ed = 0 AND n_new_ed = 0 AND coalesce(editors_printed, '') = '' AND n_rows = 0"),
        no_edited_credit=class_counts(db, 'v2', "n_ed = 0 AND n_new_ed = 0"))
    # what is known about the volumes still without editors
    lcm = {k for (k,) in q(f"SELECT DISTINCT key FROM '{SCR}/lc-matched.parquet'")} if (SCR / 'lc-matched.parquet').exists() else set()
    crno = json.loads((SCR / 'crossref-no-editor.json').read_text())
    left = [k for (k,) in q("SELECT key FROM v2 WHERE n_ed = 0 AND coalesce(editors_printed, '') = '' AND n_rows = 0")]
    rep['class_after']['remaining_record_names_no_editor'] = dict(
        lc_record=sum(1 for k in left if k in lcm), crossref_book_monograph=sum(1 for k in left if crno.get(k) == 'monograph' and k not in lcm),
        crossref_book_edited_book_no_list=sum(1 for k in left if crno.get(k) == 'edited-book' and k not in lcm),
        crossref_book_book_or_reference=sum(1 for k in left if crno.get(k) in ('book', 'reference-book') and k not in lcm),
        crossref_chapter_record_only=sum(1 for k in left if crno.get(k) == 'chapter-record' and k not in lcm),
        no_record=sum(1 for k in left if k not in lcm and k not in crno))
    # gold
    if (SCR / 'gold.parquet').exists():
        gq = lambda s: q(s.replace('GOLD', f"'{SCR}/gold.parquet'"))
        def prec(where=''):
            n, lk, right, dup, wrong, listed = gq(f"""SELECT count(*), count(*) FILTER (WHERE state IN ('exact', 'linked')),
                count(*) FILTER (WHERE cls = 'right'), count(*) FILTER (WHERE cls = 'dup'), count(*) FILTER (WHERE cls = 'wrong'),
                count(*) FILTER (WHERE state = 'possible' AND true_listed) FROM GOLD {where}""")[0]
            return dict(rows=n, linked_or_exact=lk, right=right, duplicate_key_of_true=dup, wrong=wrong,
                        precision_same_key=round(right / lk, 4) if lk else None,
                        precision_same_person=round((right + dup) / lk, 4) if lk else None,
                        recall=round(right / n, 4) if n else None, possible_with_true_listed=listed)
        rep['gold'] = dict(note="printed editors whose name agrees with a key-log EDITED or AUTHORED credit on the volume; decided with "
                                "that credit hidden (the key's ORCID if it was the match, the volume's facts) as link_work_people.link does",
                           strict_no_authority=prec("WHERE mode = 'no-authority'"),
                           lc_authority_known=prec("WHERE mode = 'authority-known'"),
                           by_credit={h: prec(f"WHERE mode = 'no-authority' AND how LIKE '{h}%'") for h in ('edited:keylog', 'authored:keylog')},
                           by_source={s: prec(f"WHERE mode = 'no-authority' AND source = '{s}'") for s in ('lc', 'crossref')},
                           states=dict(gq("SELECT state, count(*) FROM GOLD WHERE mode = 'no-authority' GROUP BY 1 ORDER BY 2 DESC")),
                           linked_branches=dict(gq("SELECT branch || '|' || cls, count(*) FROM GOLD WHERE mode = 'no-authority' AND state IN ('linked','exact') GROUP BY 1 ORDER BY 2 DESC")),
                           wrong_examples=[dict(zip(('name', 'true', 'linked', 'branch', 'year'), x)) for x in
                                           gq("SELECT name, \"true\", key, branch, year FROM GOLD WHERE cls = 'wrong' AND mode = 'no-authority' LIMIT 15")])
        if (SCR / 'namesake.parquet').exists():
            n, fl = q(f"SELECT count(*), count(*) FILTER (WHERE false_link) FROM '{SCR}/namesake.parquet'")[0]
            rep['gold']['masked_author_namesake'] = dict(note='true key dropped, a name-compatible key proven a different person '
                                                         'offered in its place: a link to it is false', rows=n, false_links=fl)
    rep['probes'] = {}
    for k in PROBES:
        rep['probes'][k] = [{c: r[c] for c in ('printed_name', 'source', 'state', 'person_key', 'candidates')}
                            for r in out if r['volume'] == k]
    if (SCR / 'crossref-stats.json').exists():
        rep['crossref_records'] = json.loads((SCR / 'crossref-stats.json').read_text())
    if (SCR / 'lc-stats.json').exists():
        rep['lc_records'] = json.loads((SCR / 'lc-stats.json').read_text())
    if (SCR / 'series-report.json').exists():
        sr = json.loads((SCR / 'series-report.json').read_text())
        sr.pop('file', None)
        rep['series_editor_chapter_claims'] = sr
    nb = sum(1 for p in CR_BOOKS.glob('part-*.jsonl') for _ in open(p))
    nc = sum(1 for p in CR_CHAPTERS.glob('part-*.jsonl') for _ in open(p))
    rep['crossref_requests'] = dict(book_records_held=nb, chapter_records_held=nc,
                                    note='one GET per record (404s kept as _missing); chapter records 12,134 were held before this run; '
                                         'raw responses under build/crossref-volume-editors-2026-11-11 and build/crossref-containers-2026-11-11')
    rep['openalex'] = 'not used: OpenAlex work records carry no editor list; no requests, no cost'
    REPORT.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: rep[k] for k in ('rows', 'rows_by_source_state', 'class_after', 'probes')}, indent=1, ensure_ascii=False))
    print(json.dumps(rep.get('gold'), indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- series editors credited with chapters (report only)

FRONT = re.compile(r'(?i)^\s*(foreword|forward|preface|introduction to the series|series (?:editor.?s )?(?:foreword|preface|introduction))\b')


def series(args):
    """Key-log AUTHORED claims on chapters whose author is the volume's series editor or foreword writer, not its
    author: the contributors step's flags (data/identifiers/work-people-2026-11-11/contributor-claims/claims.csv and
    CONTRIBUTED edges: person + book, person + publisher group) carried down to the chapters of the flagged person's
    books in that group. A chapter's volume: PART_OF (any evidence) or the book DOI its DOI extends ('-NNN' / '.NNN').
    Kinds: 'other-author chapter' (the person is credited on no other way with the volume), 'series front matter' (the
    same chapter title credited to the person in three or more volumes: the series list), 'foreword' (front matter
    the series editor did write: not proposed for withdrawal)."""
    db = duck()
    claims = list(csv.DictReader(open(ROOT / 'data/identifiers/work-people-2026-11-11/contributor-claims/claims.csv', encoding='utf-8')))
    flag_book = {(r['person'], r['work']) for r in claims}
    flag_group = {(r['person'], r['group']) for r in claims if r['basis'] == 'series-foreword-pattern' and r['group'] not in ('', 'unknown')}
    for k, w in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/contributed.parquet'").fetchall():
        flag_book.add((k, w))
    people = {k for k, _ in flag_book} | {k for k, _ in flag_group}
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    import pyarrow as pa
    db.register('pp', pa.table({'k': sorted(people)}))
    rows = db.execute(f"""SELECT a."from", a."to", a.claim, w.label, w.anchors FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
            WHERE a.evidence = 'keylog' AND a."from" IN (SELECT k FROM pp) AND w.kind IN ('chapter', 'other', 'article')""").fetchall()
    vol_of = collections.defaultdict(set)
    for c, v in db.execute(f"""SELECT "from", "to" FROM '{G}/part_of.parquet' WHERE "from" IN (SELECT "to" FROM '{G}/authored.parquet'
            WHERE evidence = 'keylog' AND "from" IN (SELECT k FROM pp))""").fetchall():
        vol_of[c].add(v)
    book_doi = {}
    for w, a in db.execute(f"""SELECT key, a FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet' WHERE kind IN ('book', 'other'))
            WHERE a LIKE 'doi:%'""").fetchall():
        book_doi.setdefault(a[4:].lower(), w)
    on_vol = set()
    for k, v in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE "from" IN (SELECT k FROM pp)
            UNION SELECT "from", "to" FROM '{G}/edited.parquet' WHERE "from" IN (SELECT k FROM pp)""").fetchall():
        on_vol.add((k, v))
    # the volume's other people: credits on it (any evidence) and the printed editors found here
    vol_people = collections.defaultdict(set)
    for k, v in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' UNION SELECT "from", "to" FROM '{G}/edited.parquet'""").fetchall():
        vol_people[v].add(k)
    printed = collections.defaultdict(list)
    if (SCR / 'positions.parquet').exists():
        for v, nm in db.execute(f"SELECT work, name_plain FROM '{SCR}/positions.parquet'").fetchall():
            printed[v].append(nm)
    from link_work_people import agree_level, apos
    cand = []
    for k, c, cl, title, an in rows:
        dois = [a[4:].lower() for a in an or [] if a.startswith('doi:')]
        vols = set(vol_of.get(c, ()))
        groups = set()
        for d in dois:
            m = re.match(r'^(.+?)[-.](?:ch-?)?\d{1,4}$', d)
            if m:
                groups.add(d.split('/')[0])
                if m.group(1) in book_doi:
                    vols.add(book_doi[m.group(1)])
        why = None
        if any((k, v) in flag_book for v in vols):
            why = 'contributor-of-volume'
        elif any((k, g) in flag_group for g in groups) and dois:
            why = 'series-editor-in-publisher-group'
        if not why:
            continue
        if any((k, v) in on_vol for v in vols):
            continue        # credited on the volume itself as author or editor: not this class
        if any(agree_level(apos(label.get(k, '')), apos(n)) in ('full', 'variant', 'initial') for v in vols for n in printed.get(v, ())):
            continue        # a printed editor of the volume
        others = any(vol_people.get(v, set()) - {k} for v in vols) or any(printed.get(v) for v in vols)
        cand.append(dict(claim=cl, person=k, label=label.get(k, ''), chapter=c, title=title or '', volumes=';'.join(sorted(vols)),
                         doi=';'.join(dois), why=why, volume_has_other_people=bool(others)))
    rep_t = collections.Counter((r['person'], re.sub(r'[^a-z]+', ' ', (r['title'] or '').lower()).strip()) for r in cand)
    for r in cand:
        t = re.sub(r'[^a-z]+', ' ', (r['title'] or '').lower()).strip()
        r['kind'] = ('foreword' if FRONT.match(r['title']) else 'series front matter' if rep_t[r['person'], t] >= 3 else
                     'other-author chapter' if r['volume_has_other_people'] else 'unclear: volume has no known author or editor')
    out = SCR / 'series-editor-chapter-claims.csv'
    with open(out, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['claim', 'person', 'label', 'chapter', 'title', 'volumes', 'doi', 'why', 'volume_has_other_people', 'kind'])
        wr.writeheader()
        wr.writerows(cand)
    already = {r['claim'] for r in claims}
    rep = dict(claims=len(cand), by_kind=dict(collections.Counter(r['kind'] for r in cand)),
               by_why=dict(collections.Counter(r['why'] for r in cand)),
               withdrawable=sum(1 for r in cand if r['kind'] in ('other-author chapter', 'series front matter')),
               withdrawable_not_in_existing_proposal=sum(1 for r in cand if r['kind'] in ('other-author chapter', 'series front matter') and r['claim'] not in already),
               people=len({r['person'] for r in cand if r['kind'] in ('other-author chapter', 'series front matter')}),
               top_people=collections.Counter(f"{r['person']} {r['label']}" for r in cand if r['kind'] in ('other-author chapter', 'series front matter')).most_common(15),
               file=str(out))
    (SCR / 'series-report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('targets')
    sp.add_parser('targets2')
    sp.add_parser('lc')
    sp.add_parser('positions')
    sp.add_parser('series')
    sp.add_parser('export')
    l = sp.add_parser('link'); l.add_argument('--gold', type=int, default=4000)
    f = sp.add_parser('fetch'); f.add_argument('--max', type=int, default=60000); f.add_argument('--rate', type=float, default=3.0)
    a = ap.parse_args()
    dict(targets=targets, targets2=targets2, fetch=fetch, lc=lc, positions=positions, link=link, series=series, export=export)[a.cmd](a)


if __name__ == '__main__':
    main()
