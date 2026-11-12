"""Edition editors, translators and introducers told from volume editors (ARCHITECTURE.md section 8, class 15; 2026-11-11).

An EDITED credit on a work that has a personal author (an edition of a classic, a translation, a lecture course, a
selection of one writer's letters) is not the relation of editing a volume of chapters by many hands, but the graph
loads both as EDITED and every 'most cited people' count gives the editor the classic's citations (Schluchter for
Weber, Ewald for Foucault's lectures, Lerner for Smith and Tocqueville). This script classifies every EDITED credit
(key log and linked) and the AUTHORED credits that may belong to a translator or introducer, and finds the missing
author of edition-editor works. It writes derived tables only; nothing is applied to the key log.

Roles (column `role`):
- volume-editor: the work is a collective volume: LC gives no personal main entry (or the 100 is itself the editor,
  older cataloguing), the 245 $c names only editors, the title is a festschrift or conference volume, or chapters by
  two or more people are attached to it (PART_OF). Counted as now.
- edition-editor: the work has a personal author who is not the editor: LC main entry (100) is another person in the
  record that asserts the credit; or 245 $c reads 'by X ; edited by Y' / 'X ; selected and edited by Y'; or (no LC
  record) another person holds a key-log AUTHORED credit, or edition_of points to an original authored by someone else.
- translator / introducer: the same, where the person's relator or 245 $c clause names translation or an
  introduction/preface/foreword only.
- author-editor: the person is also the main entry (or holds AUTHORED on the work): keeps authorship; counted as now.
- unknown: no evidence either way (counted).
AUTHORED credits are classified only where they can be wrong in this way (key-log claims not anchored on an LC
author heading, and linked credits) on works with LC records: author | translator | introducer | edition-editor |
absent (the person is nowhere in the LC records of the work and the main entry is someone else: the 'Di Tella' class,
written to data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz) | unknown.

Outputs (ids, metadata and counts only):
- data/graph/edition-roles.csv.gz: person, work, credit, evidence, source, role, basis, records, author_key,
  author_lcnaf, printed_author, author_new (the author has no AUTHORED credit on the work yet).
- data/identifiers/edition-roles-2026-11-11/: missing-authors.csv.gz (proposed linked AUTHORED rows, exact by
  lcnaf), unkeyed-authors.csv.gz, top-losers.csv, top-gainers.csv, audit-sample.csv, report.json.

    python3 scripts/edition_roles.py prepare     # scratch DuckDB from build/graph, the LC index and the key-log cache
    python3 scripts/edition_roles.py classify    # edition-roles.csv.gz + missing authors
    python3 scripts/edition_roles.py report      # citation effects (citing theses), top-50 lists
    python3 scripts/edition_roles.py sample      # stratified audit sample (LC statements; the audit file is local)
"""
import argparse
import csv
import gzip
import json
import os
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from editor_qualifiers import qualified_role  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = Path(os.environ.get('ER_GRAPH', ROOT / 'build/graph'))
LC = Path('/mnt/e/lc-bib-2016/index')
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
CACHE = ROOT / 'build/keylog-state.sqlite'
SCRATCH = Path(os.environ.get('ER_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/editions2'))
DB = SCRATCH / 'base.duckdb'
TABLE = ROOT / 'data/graph/edition-roles.csv.gz'
OUT = ROOT / 'data/identifiers/edition-roles-2026-11-11'
CONFLICTS = ROOT / 'data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz'

AUTHOR_REL = {'author', 'joint author', 'aut', 'joint aut', 'co-author', 'coauthor'}
EDITOR_REL = {'ed', 'editor', 'joint ed', 'joint editor', 'editor of compilation', 'comp', 'compiler', 'joint comp',
              'ed. and tr', 'edt', 'edc', 'eds', 'joint compiler', 'redactor', 'red'}
TRANS_REL = {'tr', 'trl', 'translator', 'joint tr', 'joint translator', 'ed. and tr', 'tr. and ed'}
INTRO_REL = re.compile(r'introduction|preface|foreword|afterword|^aui$|^wpr$|^wac$|^aft$|commentat|^cwt$|annotator|^ann$')
FEST = re.compile(r'(?i)essays? (in|presented|offered|written) (honou?r|memory)|in honou?r of|festschrift|in memoriam|'
                  r'm[ée]langes|hommage|homenaje|homenagem|studies (presented|in honou?r)|studi in onore|'
                  r'conference|symposium|colloqu|proceedings|congress|congr[eè]s|workshop|seminar|tagung|jornadas|encuentro')
SERIES = re.compile(r'(?i)consulting editor|series editor|general editors?\b|editor[- ]in[- ]chief|series ed\b|advisory editor|'
                    r'directeur de (la )?collection|direction de la collection|coordenador da cole|herausgegeben von der|reihe')
DIRECTOR = re.compile(r'(?i)dire[cç][aã]o|sous la direction|direction|direcci[oó]n|direzione|leitung|coordena[cç][aã]o|organiza[cç][aã]o')
# '\bedit(?!h)': 'Edith' is a name, not a role word (2026-11-12: Edith Wharton, Edith Saurer read as 'edited')
STRICT_EDIT = re.compile(r'(?i)\bedit(?!h)|\bed\.|\beds\.|compil|hrsg|herausg|a cura|cura di|organiz|\borg\.|\bcoord|\bdir\.')
V_TRANS = re.compile(r'(?i)translat|traduc|tradu[zçi]|übers|ubers|vertaal|overs[aæ]t|englished|rendered into')
V_EDIT = re.compile(r'(?i)\bedit(?!h)|\bed\.|\beds\.|compil|select|hrsg|herausg|\bcoord|\bdir\.|sous la dir|bajo la dir|'
                    r'organiz|organis|\borg\.|presentaci|présent|establi|annot|arrang|collect|abridg|gathered|chosen|'
                    r'prepared|edición|edición|edizione|a cura|cura di|introduction, notes|redactie|r[eé]daction|redakt|redig|'
                    r'bearbeit|onder red|pod red')
V_INTRO = re.compile(r'(?i)introduc|introd\.|einf[uü]hr|preface|pr[ée]face|foreword|avant-propos|pref[aá]cio|pr[oó]logo|'
                     r'einleitung|vorwort|nachwort|afterword|postface|commentary')


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def family_of(label):
    """'Lerner, Max' -> 'lerner'; 'François-Xavier Guerra' -> 'guerra'; 'Di Tella, Torcuato S' -> 'di tella'."""
    lab = re.sub(r'\s*\(.*?\)', '', label or '')
    lab = re.sub(r',?\s*\d{3,4}\??-.*$', '', lab).strip(' ,.')
    if ',' in lab:
        fam = lab.split(',')[0]
    else:
        toks = lab.split()
        fam = toks[-1] if toks else ''
        if len(toks) >= 3 and fold(toks[-2]) in {'de', 'da', 'di', 'van', 'von', 'del', 'le', 'la', 'du', 'dos', 'das'}:
            fam = ' '.join(toks[-2:])
    return re.sub(r'[^a-z ]+', ' ', fold(fam)).strip()


def given_of(label):
    lab = re.sub(r'\s*\(.*?\)', '', label or '')
    if ',' in lab:
        g = lab.split(',')[1]
    else:
        g = ' '.join(lab.split()[:-1])
    g = re.sub(r'[^a-z ]+', ' ', fold(g)).strip()
    return g


def con(read_only=False):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'tmp').mkdir(exist_ok=True)
    c = duckdb.connect(str(DB), read_only=read_only)
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH / 'tmp'}'; "
              "SET preserve_insertion_order=false; SET max_temp_directory_size='8GB'")
    return c


# ---------------------------------------------------------------- prepare

def prepare(args):
    c = con()
    if args.claims_only:
        return prepare_claims(c)
    c.execute(f"CREATE OR REPLACE TABLE ed AS SELECT * FROM '{G}/edited.parquet'")
    c.execute(f"CREATE OR REPLACE TABLE au AS SELECT * FROM '{G}/authored.parquet'")
    c.execute(f"CREATE OR REPLACE TABLE person AS SELECT key, label, lcnaf, anchors, wd FROM '{G}/person.parquet'")
    c.execute(f"""CREATE OR REPLACE TABLE wk AS SELECT key, label, kind, year, lccn, anchors, resolution, kind_proposed
        FROM '{G}/work.parquet' WHERE key IN (SELECT "to" FROM ed)
        OR (key IN (SELECT "to" FROM au) AND (lccn IS NOT NULL OR len(list_filter(anchors, a -> a LIKE 'lccn:%')) > 0))
        OR key IN (SELECT "from" FROM '{G}/edition_of.parquet') OR key IN (SELECT "to" FROM '{G}/edition_of.parquet')""")
    c.execute("""CREATE OR REPLACE TABLE wlccn AS SELECT DISTINCT key, substr(a, 6) lccn FROM (SELECT key, unnest(anchors) a
                 FROM wk) WHERE a LIKE 'lccn:%' UNION SELECT key, lccn FROM wk WHERE lccn IS NOT NULL""")
    c.execute(f"""CREATE OR REPLACE TABLE rec AS SELECT trim(r.control) control, r.lccn, r.title, r.date1, r.lang,
        r.responsibility, r.publisher FROM '{LC}/records-*.parquet' r
        WHERE trim(r.control) IN (SELECT lccn FROM wlccn) OR r.lccn IN (SELECT lccn FROM wlccn)""")
    c.execute(f"""CREATE OR REPLACE TABLE hd AS SELECT trim(h.control) control, h.pos, h.tag, h.heading, h.family, h.given,
        h.uri, h.dates, h.relators FROM '{LC}/headings-*.parquet' h WHERE trim(h.control) IN (SELECT control FROM rec)""")
    c.execute("""CREATE OR REPLACE TABLE wrec AS SELECT l.key, r.control FROM wlccn l JOIN rec r ON r.control = l.lccn
                 UNION SELECT l.key, r.control FROM wlccn l JOIN rec r ON r.lccn = l.lccn""")
    c.execute("""CREATE OR REPLACE TABLE lccn_ctl AS SELECT control lccn, control FROM rec UNION SELECT lccn, control FROM rec
                 WHERE lccn IS NOT NULL AND lccn <> ''""")
    c.execute(f"""CREATE OR REPLACE TABLE cites AS SELECT "from" src, "to" dst, edition, source, cited_as
                  FROM '{G}/cites.parquet' WHERE source LIKE '%thesis%'""")
    for t in ('edition_of', 'part_of'):
        c.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM '{G}/{t}.parquet'")
    # heading -> LC name authority: $0, else the one live authority whose authorised form is the heading
    c.execute(r"""CREATE OR REPLACE MACRO hnorm(h) AS (
        WITH x AS (SELECT regexp_replace(regexp_replace(replace(coalesce(h, ''), '’', ''''), '\s+', ' ', 'g'),
                                         '\s*,\s*', ', ', 'g') v)
        SELECT CASE WHEN regexp_matches(trim(v, ' ,'), '(\b\w|-)\.$') THEN trim(v, ' ,') ELSE rtrim(trim(v, ' ,'), '.') END FROM x)""")
    c.execute("CREATE OR REPLACE TABLE hn AS SELECT DISTINCT heading, hnorm(heading) n, uri FROM hd")
    c.execute(f"CREATE OR REPLACE TEMP TABLE allnames AS SELECT lcid, label, hnorm(label) n, birth, death, deprecated FROM '{NAMES}'")
    c.execute("""CREATE OR REPLACE TABLE names AS SELECT a.* FROM allnames a SEMI JOIN (SELECT DISTINCT n FROM hn) h ON h.n = a.n""")
    c.execute("""CREATE OR REPLACE TABLE hres AS
        WITH byuri AS (SELECT heading, regexp_extract(uri, '([a-z]+[0-9]+)/?$', 1) lcid FROM hn WHERE uri <> ''),
             bylab AS (SELECT n, list(lcid) ids FROM names WHERE NOT deprecated GROUP BY 1)
        SELECT h.heading, any_value(coalesce(nullif(u.lcid, ''), CASE WHEN len(b.ids) = 1 THEN b.ids[1] END)) lcid
        FROM hn h LEFT JOIN byuri u USING (heading) LEFT JOIN bylab b ON b.n = h.n GROUP BY 1""")
    prepare_claims(c)
    for t in ('ed', 'au', 'wk', 'wrec', 'rec', 'hd', 'hres', 'claim_lc', 'cites'):
        print(t, c.execute(f'SELECT count(*) FROM {t}').fetchone()[0], flush=True)


def prepare_claims(c):
    # the asserting LC records of each key-log claim (anchors lc-edited:<lccn>:<lcid>, lc-authored:...)
    rows = []
    kl = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    for k, a in kl.execute("SELECT key, anchors FROM keys WHERE type = 'claim' AND (anchors LIKE '%lc-edited:%' "
                           "OR anchors LIKE '%lc-authored:%')"):
        for x in json.loads(a):
            if x.startswith(('lc-edited:', 'lc-authored:')):
                kind, lccn, lcid = x.split(':', 2)
                rows.append((k, kind[3:], lccn, lcid))
    import pyarrow as pa
    cl = pa.table({n: [r[i] for r in rows] for i, n in enumerate(('claim', 'role', 'lccn', 'lcid'))})
    c.register('cl_rows', cl)
    c.execute('CREATE OR REPLACE TABLE claim_lc AS SELECT * FROM cl_rows')


# ---------------------------------------------------------------- classify

class LCData:
    def __init__(self, c):
        self.rec = {r[0]: r[1:] for r in c.execute('SELECT control, title, date1, responsibility, lang FROM rec').fetchall()}
        self.heads = defaultdict(list)
        for ctl, pos, tag, h, fam, giv, rel, lcid, dates in c.execute(
                'SELECT control, pos, tag, h.heading, family, given, relators, r.lcid, dates FROM hd h LEFT JOIN hres r USING (heading) '
                'ORDER BY control, pos').fetchall():
            dm = re.search(r'-\s*(?:ca\.\s*|approximately\s*)?(\d{3,4})', dates or '')
            self.heads[ctl].append(dict(pos=pos, tag=tag, heading=h, family=re.sub(r'[^a-z ]+', ' ', fold(fam)).strip(),
                                        given=fold(giv), lcid=lcid or '', death=int(dm.group(1)) if dm else None,
                                        rel={x.strip(' .,').lower() for x in (rel or [])}))
        self.wrec = defaultdict(list)
        for k, ctl in c.execute('SELECT key, control FROM wrec').fetchall():
            self.wrec[k].append(ctl)
        self.ctl_of = defaultdict(set)
        for l, ctl in c.execute('SELECT lccn, control FROM lccn_ctl').fetchall():
            self.ctl_of[l].add(ctl)


def find_person(heads, lcids, fam, giv):
    """The heading of the person in a record: by authority, else same family name and compatible first given name."""
    for h in heads:
        if h['lcid'] and h['lcid'] in lcids:
            return h
    if not fam:
        return None
    fams = {fam, fam.split()[-1]} if fam else set()      # 'de almeida' (label order) is 'Almeida' in the heading
    for h in heads:
        if (h['family'] in fams or h['family'].split()[-1:] == fam.split()[-1:]) and (not giv or not h['given'] or h['given'][:1] == giv[:1]):
            return h
    return None


PARTICLES = {'de', 'da', 'di', 'do', 'dos', 'das', 'del', 'van', 'von', 'der', 'den', 'la', 'le', 'du', 'des', 'y', 'e', 'ten', 'ter'}
CONJ = {'and', 'und', 'et', 'e', 'y', 'with', 'avec', 'mit', 'com', 'con', '&', 'i.e.', 'u.', 'en'}


def _asc(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()


def _role_word(t):
    t = t.lower()
    return bool(SERIES.search(t) or DIRECTOR.search(t) or V_TRANS.search(t) or V_EDIT.search(t) or V_INTRO.search(t)
                or t in {'with', 'by', 'and', 'new', 'an', 'a', 'the', 'consulting', 'general', 'series', 'advisory', 'chief',
                         'senior', 'volume', 'textual', 'assistant', 'associate', 'managing'})


# 'ed.' / 'eds.' only in lower case and not before a name ('Ed. Lemoine' is Edouard Lemoine)
NOUN_ROLE = re.compile(r'(?<![A-Za-z])((?i:editors?|compilers?)|eds?\.(?!\s*[A-Z][a-z]))(?![a-z])')
LIST_WORDS = PARTICLES | {'and', 'und', 'et', 'y', 'e', '&', 'jr', 'sr', 'jr.', 'sr.'}


def noun_role_after(rest):
    """The role noun that follows a name in its clause and governs it (2026-11-12, class 23): 'plain' ('X, editor';
    'X and Y, editors'), 'other' ('X, cartographic editor'; 'X, Y, assistant editors'), 'series' ('X, consulting
    editor') or None (no role noun follows, or other words stand between). The nearest role noun governs:
    'Frederick F. Wherry, editor, Juliet Schor, consulting editor' -> Wherry plain."""
    m = NOUN_ROLE.search(rest)
    if not m or re.match(r'(?i)\s*(by|von|par|de|di|por)\b', rest[m.end():]):
        return None                        # 'Ed. by William Crookes': a verb, not a role after a name
    lead = rest[:m.start()]
    singular = not re.match(r'(?i)(editors|compilers|eds\.)', m.group(1))
    q = []
    h = re.search(r'([A-Za-z]+)-$', lead)  # 'co-editor', 'photo-editor'
    if h:
        q, lead = [h.group(1)], lead[:h.start()]
    while True:                            # lower-case words just before the noun ('cartographic', 'assistant')
        w = re.search(r'([a-z][a-z-]*)\s*$', lead)
        if not w or w.group(1) in LIST_WORDS:
            break
        q.insert(0, w.group(1))
        lead = lead[:w.start()]
    # the text between the name and the role: names, initials, 'and', commas only, ending in a comma or bracket
    if not re.fullmatch(r"[\w\s.,'’&()\[\]-]*?[,(\[]\s*", lead):
        return None
    if any(t[:1].islower() and t.lower() not in LIST_WORDS for t in re.findall(r"[A-Za-z][A-Za-z'.-]*", lead)):
        return None                        # 'Reid with Graeme Wynn, cartographic editor': not a list of names
    # a singular role after a list is the last name's: 'Newt Gingrich, William R. Forstchen and Albert S. Haner,
    # contributing editor' (Jr., Sr. and roman numerals are part of the name)
    if singular and re.search(r',|\band\b|&|\bund\b|\bet\b', re.sub(r'^\s*,?\s*(jr|sr|[ivx]+)\.?', '', lead, flags=re.I).rstrip(' ,([')):
        return None
    return qualified_role(' '.join(q) + ' ', 'editor') or 'plain' if q else 'plain'


def names_an_editor(resp):
    """the statement names someone as the volume's editor (plain, or a general / series editor): 'edited by ...',
    'X, editor', 'general editor, Y'. Without one, a qualified editor ('Candace S. Greene, proceedings editor', 'Clarence
    C. Walton, contributing editor') is the nearest thing to the volume's editor and keeps the earlier role."""
    for m in re.finditer(r'(?i)(?<![a-z])(editors?|edited|compiled|compilers?)(?![a-z])', resp or ''):
        if qualified_role(resp[:m.start()], m.group(1)) != 'other':
            return True
    return False


def role_first(clause):
    """The clause opens with its role ('editor, Arthur M. Schlesinger', 'General editor: ...', 'edited by ...', 'Maps
    edited by ...'): a role after a later name belongs to the next name, not to the one before it."""
    return bool(re.match(r'^\W*(?:[A-Za-z][a-z-]*\s+)?(?:[a-z][a-z-]*\s+){0,2}(?i:editors?\b|edited\b|compiled\b|compilers?\b|eds?\.)', clause))


def clause_role(resp, fam, giv='', strict=False):
    """The role 245 $c gives the person (by family name): series-editor / director / translator / editor /
    introducer / author / None. The governing phrase is the text between the previous name and this one (the
    person's given names and name particles dropped; a bare 'and' passes to the phrase before the previous name):
    'edited ... by Edwin Cannan ... with an introduction by Max Lerner' -> introducer;
    'herausgegeben von Wolfgang J. Mommsen und Wolfgang Schluchter' -> editor; 'Karl Marx and Friedrich Engels' -> author."""
    if not resp or not fam:
        return None
    for cl in re.split(r';|(?<=[a-z]{3})\.\s+(?=[A-Z][a-z]{2,})', resp):
        a = _asc(cl)
        ms = list(re.finditer(r'(^|[^a-z])' + re.escape(fam) + r'([^a-z]|$)', a.lower()))
        if giv:      # the occurrence whose given name agrees ('Aeron Haynie' is not 'Haynie, Charles A.')
            g1 = next((w for w in re.findall(r'[a-z]+', _asc(giv).lower()) if w not in PARTICLES), '')

            def given_agrees(m):
                # the capitalised tokens (and particles) just before the family name; one of them is the first
                # given name, or its initial ('Sérgio Buarque de Holanda', 'J. Mommsen')
                t = re.findall(r"[A-Za-z][A-Za-z'.]*", a[:m.start() + len(m.group(1))])
                run = []
                while t and (t[-1][:1].isupper() or t[-1].lower() in PARTICLES):
                    run.append(t.pop())
                run = [x.lower().rstrip('.') for x in run if x.lower() not in PARTICLES]
                return not g1 or any(x == g1 or (len(x) == 1 and x == g1[:1]) or (len(x) > 1 and g1.startswith(x)) for x in run)
            ms = [m for m in ms if given_agrees(m)]
        if not ms:
            continue
        m = ms[0]
        post = a[m.end() - len(m.group(2)):][:60]
        rest = a[m.end() - len(m.group(2)):]
        # 2026-11-12 (class 23): in a clause that opens with a name, the nearest role noun after the name governs it; a
        # qualifier naming another job ('Graeme Wynn, cartographic editor', 'Mitchell A. McNutt, picture editor') is
        # not editing the volume. In a clause that opens with its role ('editor-in-chief, Edwin R.A. Seligman,
        # associate editor, Alvin Johnson') the role before the name governs (the phrase below)
        gov = None if role_first(a) else noun_role_after(rest)
        if gov == 'other':
            return 'qualified-editor'
        if gov == 'series':
            return 'series-editor'
        # 'Henry J. Aaron and Michael J. Boskin, editors', 'A, B, C (Hrsg.)': a role after the list covers every name
        if re.search(r'(?i)[,(]\s*\[?(eds\.|editors|editores|editoras|organizadores|organizadoras|orgs\.|coords\.|coordinadores|'
                     r'coordenadores|coordenadoras|coordinateurs|hrsg\.?\)|hg\.?\)|dirs\.|compilers|comps\.|herausgeber)', rest) and \
                re.match(r"(?i)^[\w\s.,'’&-]*?(\band\b|\bund\b|\bet\b|\be\b|\by\b|&|,)", rest):
            return 'editor'
        if re.search(r'(?i)(collaboration|mitarbeit|contribu(tions?|tors?|ted)|beitr[aä]ge|assisted|colabora|collaborazione|essays by|textes de|texts by|'
                     r'contributi di|contribuciones|autores|auteurs)', a[:m.start()][-100:]) or re.match(r'(?i)^[\w\s.]{0,30}?(\.\.\.\s*)?\[?(and others|et al|u\.a\.|e outros|y otros)', rest0 := a[m.end() - len(m.group(2)):]):
            return 'contributor'
        if gov == 'plain':
            return 'editor'
        if re.search(r'(?i)[,;(]\s*(general|series|consulting|advisory)\s+editors?\b', rest0) and \
                re.match(r"(?i)^[\w\s.,'’&-]*?(\band\b|&|,)", rest0):
            return 'series-editor'
        if re.search(r'(?i)[,(]\s*\[?(ed|eds|editor|editors|éd|éds|org|orgs|coord|coords|hrsg|hg|dir|dirs|comp|comps)\.?\]?\)?\s*($|[=:;])', _asc(rest0)):
            return 'editor'
        if re.match(r'(?i)^\s*(,\s*(jr|sr|[ivx]+)\.?\s*)?[,(]\s*\[?([a-z-]+\s+(and\s+)?){0,2}(ed\.|eds\.|editor|editors|editora|organizador|organizadora|organizadores|'
                    r'orgs?\.|coord|comp\.|compiler|hrsg|dir\.|trad\.|tr\.|translator|redac|redakt)', post):
            m2 = re.search(r'(?i)(trad\.|tr\.|translator)', post)
            return 'translator' if m2 and not re.search(r'(?i)ed\.|editor|organiz|hrsg|coord|comp', post[:m2.start()]) else 'editor'
        tm = list(re.finditer(r"[A-Za-z][A-Za-z'.-]*|&", a[:m.start() + len(m.group(1))]))
        toks = [x.group() for x in tm]
        k = len(toks)

        def skip_name(k):
            while k and (toks[k - 1][:1].isupper() or toks[k - 1].lower() in PARTICLES) and not _role_word(toks[k - 1]):
                k -= 1
            return k
        k = skip_name(k)                              # the person's own given names, initials and particles
        phrase = []
        while k:
            t = toks[k - 1]
            if t[:1].isupper() and not _role_word(t) and t.lower() not in CONJ:
                if all(x.lower() in CONJ or x.lower() in PARTICLES for x in phrase):   # 'A, B and C': a list
                    phrase = []                       # 'Mommsen und Schluchter': inherit the phrase before Mommsen
                    k = skip_name(k)
                    continue
                break
            phrase.insert(0, t)
            k -= 1
        ph = ' '.join(phrase).lower()
        # 2026-11-12 (class 23): the role word of the phrase with the words just before it in the text ('cartographic
        # editor, Graeme Wynn'; 'Assistant editor, Sabine Freitag'; 'Maps edited by ...'; 'bibliography edited by ...')
        for i, t in enumerate(phrase):
            rw = re.match(r'(?i)^(?:([a-z]+)-)?(editors?|edited|compiled|compilers?)$', t)
            if rw:
                if rw.group(1) and rw.group(2).lower().startswith(('edited', 'compiled')):
                    j = None                  # 're-edited', 'co-edited': the verb is still editing
                elif rw.group(1):
                    j = qualified_role(rw.group(1) + ' ', 'editor')
                else:
                    j = qualified_role(a[:tm[k + i].start()], rw.group(2))
                if j == 'other':
                    return 'qualified-editor'
                if j == 'series':
                    return 'series-editor'
                break
        if SERIES.search(ph):
            return 'series-editor'
        if DIRECTOR.search(ph):
            return 'director'
        if V_TRANS.search(ph):
            return 'translator'
        if (STRICT_EDIT if strict else V_EDIT).search(ph):
            return 'editor'
        if V_INTRO.search(ph):
            return 'introducer'
        return 'author'
    return None


def first_clause_author(resp, fam, heads=()):
    """'by Karl Marx ; edited by ...' / 'Adam Smith ; edited by ...': the first clause names one person who is not the
    editor and carries no role verb -> that person is the work's author."""
    if not resp:
        return None
    parts = re.split(r'\s;\s|;\s', resp)
    if len(parts) < 2:
        return None
    first = parts[0].strip(' .[]')
    f = fold(first)
    if V_EDIT.search(f) or V_TRANS.search(f) or V_INTRO.search(f) or (fam and fam in f):
        return None
    by = bool(re.match(r'(?i)^\[?by\]?\s+', first))
    first = re.sub(r'(?i)^\[?by\]?\s+', '', first).strip(' .,[]')
    if not first or re.search(r'(?i),|\band\b|&|\bet\b|\bund\b|\by\b|\be\b|others|al\.|\[', first):
        return None
    if not re.match(r"^[A-ZÀ-Þ][\w'’.\-]+(\s+[A-ZÀ-Þa-z][\w'’.\-]*){%d,4}$" % (0 if by else 1), first):
        return None
    if not any(V_EDIT.search(p) or V_TRANS.search(p) or V_INTRO.search(p) for p in parts[1:]):
        return None
    # 'Andrés Solimano ; con Felipe Sáez, Caroline Moser, editores': the first name is one of the editors
    if any(re.match(r'(?i)^\s*\[?(con|with|mit|avec|and|und|e|y)\b', p) for p in parts[1:]):
        return None
    # 'Hermann Düringer ; Jochen-Christoph Kaiser (Hrsg.)': a role in brackets after the names covers both
    if re.search(r'(?i)\((hrsg|hg|eds?|orgs?|coords?|dirs?|comps?|editors?)\.?\)', resp):
        return None
    # the named author must be a personal heading of the record (not a corporate body, a project, a conference)
    ff = fold(first)
    if not any(h['family'] and h['family'] != fam and re.search(r'(^|[^a-z])' + re.escape(h['family']) + r'([^a-z]|$)', ff) for h in heads):
        return None
    return first


def classify_record(L, ctl, lcids, fam, giv, credit):
    heads = L.heads.get(ctl, [])
    title, date1, resp, lang = L.rec.get(ctl, ('', '', '', ''))
    mains = [h for h in heads if h['tag'] == '100']
    me = find_person(heads, lcids, fam, giv)
    crole = clause_role(resp, fam)
    main = mains[0] if mains else None
    res = dict(role=None, basis=None, main=main, me=me)
    if main and me is not None and me['pos'] == main['pos']:
        if main['rel'] & EDITOR_REL and not main['rel'] & AUTHOR_REL:
            res.update(role='volume-editor', basis='lc-100-is-editor')
        else:
            res.update(role='author-editor' if credit == 'edited' else 'author', basis='lc-main-entry-is-person')
        return res
    if crole == 'qualified-editor' and (main or names_an_editor(resp)):
        # 2026-11-12 (class 23): 'cartographic editor', 'picture editor', 'assistant editor', 'maps edited by': another
        # job on the book, not editing the volume (and not authorship): role contributor, not counted as own work.
        # Only where the book has an author (main entry) or the statement names another editor of the volume
        res.update(role='contributor', basis='lc-245c-qualified-editor')
        return res
    if main and main['rel'] & EDITOR_REL and not main['rel'] & AUTHOR_REL:
        res.update(role='volume-editor', basis='lc-100-is-editor')
        return res
    if main and clause_role(resp, main['family'], main['given'], strict=True) in ('editor', 'director', 'series-editor', 'introducer'):
        # older records put the general editor of a collective work in 100 without a relator ('sob a direção de
        # Sérgio Buarque de Holanda'): the volume is collective
        res.update(role='series-editor' if crole == 'series-editor' else 'volume-editor', basis='lc-100-is-editor-by-245c')
        return res
    if crole == 'series-editor':
        res.update(role='series-editor', basis='lc-245c-series-editor')
        return res
    if main:
        rel = me['rel'] if me else set()
        if crole == 'author' and not rel & (EDITOR_REL | TRANS_REL) and not (rel and all(INTRO_REL.search(r) for r in rel)):
            # named in a plain clause with the main entry ('Karl Marx and Friedrich Engels'): a co-author
            res.update(role='author' if credit == 'authored' else 'author-editor', basis='lc-245c-coauthor')
            return res
        if me and rel & AUTHOR_REL and not rel & (EDITOR_REL | TRANS_REL):
            res.update(role='author' if credit == 'authored' else 'author-editor', basis='lc-700-author')
            return res
        if rel & TRANS_REL or (not rel & EDITOR_REL and crole == 'translator'):
            res.update(role='translator', basis='lc-relator-translator' if rel & TRANS_REL else 'lc-245c-translator')
        elif (rel and all(INTRO_REL.search(r) for r in rel)) or (not rel & EDITOR_REL and crole == 'introducer'):
            res.update(role='introducer', basis='lc-relator-introduction' if rel else 'lc-245c-introduction')
        elif me is None and crole is None:
            res.update(role='absent', basis='lc-main-entry-other;person-not-in-record')
        elif credit == 'authored' and crole == 'author' and not rel:
            res.update(role='author', basis='lc-245c-author')
        else:
            res.update(role='edition-editor', basis='lc-main-entry-other')
        return res
    # no personal main entry
    if credit == 'edited' and crole == 'contributor':
        res.update(role='unknown', basis='lc-245c-contributor')       # a contributor credited as an editor
        return res
    if credit == 'edited' and crole == 'author' and me is not None and not me['rel'] & (EDITOR_REL | TRANS_REL):
        res.update(role='author-editor', basis='lc-245c-coauthor')     # named in a plain clause: a co-author
        return res
    fa = None if FEST.search(title or '') else first_clause_author(resp, fam, heads)
    if fa:
        res.update(role='edition-editor' if crole != 'translator' else 'translator', basis='lc-245c-by-author', printed=fa)
        return res
    if me is None and crole is None and credit == 'authored':
        res.update(role='unknown', basis='lc-no-main-entry;person-not-in-record')
        return res
    if credit == 'authored':
        rel = me['rel'] if me else set()
        if rel & TRANS_REL or crole == 'translator':
            res.update(role='translator', basis='lc-no-main-entry;translator')
        elif rel & EDITOR_REL or crole == 'editor':
            res.update(role='volume-editor', basis='lc-no-main-entry;editor-credited-as-author')
        else:
            res.update(role='author', basis='lc-no-main-entry;named')
        return res
    # tried and dropped after the hand audit of 2026-11-11 (precision too low): a 100 compiler dead 30+ years before
    # the edition (6/8 right), one or two 700 writers dead 30+ years before it (8/17), 'by X' in the title (1/6)
    if FEST.search(title or ''):
        res.update(role='volume-editor', basis='lc-no-main-entry;festschrift-or-conference')
    elif me is not None and me['rel'] & TRANS_REL and not me['rel'] & EDITOR_REL:
        res.update(role='translator', basis='lc-no-main-entry;translator')
    else:
        res.update(role='volume-editor', basis='lc-no-main-entry')
    return res


PRIORITY = ['author-editor', 'author', 'edition-editor', 'translator', 'introducer', 'series-editor', 'contributor', 'volume-editor',
            'absent', 'unknown']


def classify(args):
    c = con(read_only=True)
    L = LCData(c)
    print('LC data loaded', flush=True)
    plab, plc = {}, defaultdict(set)
    key_of_lcid = defaultdict(set)
    for k, lab, lcnaf, anchors in c.execute('SELECT key, label, lcnaf, anchors FROM person').fetchall():
        plab[k] = lab
        ids = {a[6:] for a in anchors or [] if a.startswith('lcnaf:')} | ({lcnaf} if lcnaf else set())
        plc[k] = ids
        for i in ids:
            key_of_lcid[i].add(k)
    wlab = {k: (lab, kind, y) for k, lab, kind, y in c.execute('SELECT key, label, kind, year FROM wk').fetchall()}
    claim_ctl = defaultdict(set)
    for cl, l in c.execute('SELECT claim, lccn FROM claim_lc').fetchall():
        claim_ctl[cl] |= L.ctl_of.get(l, set())
    authors = defaultdict(set)            # work -> persons with AUTHORED (any evidence)
    authors_kl = defaultdict(set)
    for p, w, ev in c.execute('SELECT "from", "to", evidence FROM au WHERE "to" IN (SELECT key FROM wk)').fetchall():
        authors[w].add(p)
        if ev == 'keylog':
            authors_kl[w].add(p)
    chap_auth = defaultdict(set)          # volume -> distinct chapter authors
    for v, p in c.execute('SELECT po."to", a."from" FROM part_of po JOIN au a ON a."to" = po."from" '
                          'WHERE po."to" IN (SELECT "to" FROM ed)').fetchall():
        chap_auth[v].add(p)
    orig_of = defaultdict(set)
    for f, t in c.execute('SELECT "from", "to" FROM edition_of').fetchall():
        orig_of[f].add(t)

    def graph_role(p, w):
        others = authors_kl.get(w, set()) - {p}
        if len(chap_auth.get(w, set()) - {p}) >= 2:
            return 'volume-editor', 'graph-chapters-by-several', None
        if p in authors.get(w, set()):
            return 'author-editor', 'graph-also-authored', None
        if others:      # audit 2026-11-11: 0 of 6 right (co-editors of ORCID-sourced volumes typed as authors)
            return 'unknown', 'graph-other-keylog-author', None
        for o in orig_of.get(w, ()):
            oa = authors_kl.get(o, set()) - {p}
            if oa:
                return 'edition-editor', 'graph-edition-of-authored-original', sorted(oa)[0]
        if FEST.search((wlab.get(w) or ('',))[0] or ''):
            return 'volume-editor', 'title-festschrift-or-conference', None
        return 'unknown', 'no-evidence', None

    out = []
    credits = c.execute('SELECT "from", "to", claim, evidence, source, state, \'edited\' FROM ed').fetchall()
    credits += c.execute("""SELECT a."from", a."to", a.claim, a.evidence, a.source, a.state, 'authored' FROM au a
        JOIN (SELECT DISTINCT key FROM wrec) w ON w.key = a."to"
        WHERE a.evidence = 'linked' OR a.claim NOT IN (SELECT claim FROM claim_lc)""").fetchall()
    print(len(credits), 'credits', flush=True)
    for p, w, claim, ev, src, st, credit in credits:
        lab = plab.get(p, '')
        fam, giv = family_of(lab), given_of(lab)
        ctls = claim_ctl.get(claim) or set(L.wrec.get(w, ()))
        asserted = bool(claim_ctl.get(claim))
        rr = [classify_record(L, ctl, plc.get(p, set()), fam, giv, credit) for ctl in sorted(ctls) if ctl in L.rec]
        rr = [r for r in rr if r['role']]
        row = dict(person=p, work=w, credit=credit, evidence=ev, source=src or '', role='unknown', basis='',
                   records=len(rr), author_key='', author_lcnaf='', printed_author='', author_new='')
        if rr:
            roles = Counter(r['role'] for r in rr)
            if credit == 'edited' and 'author-editor' in roles:
                role = 'author-editor'
            elif credit == 'authored' and 'author' in roles:
                role = 'author'
            elif len(roles) > 1 and 'volume-editor' in roles and roles.keys() & {'edition-editor', 'translator', 'introducer', 'series-editor', 'contributor'}:
                role = 'unknown'      # the work's records disagree (audit: pooled keys, catalogues): not decided
            else:
                top = max(roles.values())
                role = min((r for r, n in roles.items() if n == top), key=PRIORITY.index)
            pick = [r for r in rr if r['role'] == role] or rr
            bases = Counter(r['basis'] for r in pick)
            row['role'] = role
            row['basis'] = bases.most_common(1)[0][0] + ('' if len(roles) == 1 else ';mixed') + ('' if asserted or credit == 'authored' else ';work-records')
            mains = [r['main'] for r in pick if r.get('main') and (r['basis'] in ('lc-100-compiler-long-dead', 'lc-700-historical-author')
                     or not (r['main']['rel'] & EDITOR_REL and not r['main']['rel'] & AUTHOR_REL))]
            # the book's own author (LC main entry): also behind a series editor or a contributor (2026-11-12)
            if role in ('edition-editor', 'translator', 'introducer', 'absent', 'series-editor', 'contributor') and mains:
                m = Counter((x['lcid'], x['heading']) for x in mains).most_common(1)[0][0]
                row['author_lcnaf'], row['printed_author'] = m[0], m[1]
                ks = key_of_lcid.get(m[0], set()) if m[0] else set()
                if len(ks) == 1:
                    row['author_key'] = next(iter(ks))
            elif role in ('edition-editor', 'translator') and any(r.get('printed') for r in pick):
                row['printed_author'] = next(r['printed'] for r in pick if r.get('printed'))
            # graph check: an LC 'volume' whose graph work is an edition of an authored original
            if credit == 'edited' and role == 'volume-editor' and row['basis'].startswith('lc-no-main-entry') and not row['basis'].startswith('lc-no-main-entry;fest'):
                g = graph_role(p, w)
                if g[0] == 'edition-editor' and g[1] == 'graph-edition-of-authored-original':
                    row['role'], row['basis'], row['author_key'] = g[0], g[1] + ';lc-no-main-entry', g[2]
        elif credit == 'edited':
            role, basis, ak = graph_role(p, w)
            row.update(role=role, basis=basis, author_key=ak or '')
        else:
            continue
        if credit == 'edited' and row['role'] == 'absent':
            row['role'], row['basis'] = 'edition-editor', 'lc-main-entry-other;editor-not-found-in-record'
        if row['author_key']:
            row['author_new'] = 'no' if row['author_key'] in authors.get(w, set()) else 'yes'
        if row['author_key'] == p:          # the 'other' main entry resolves to the same key: the person is the author
            row.update(role='author-editor' if credit == 'edited' else 'author', basis=row['basis'] + ';same-key',
                       author_key='', author_new='')
        out.append(row)
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    seen, uniq = set(), []
    for r in out:              # one row per person, work, credit kind and evidence (the key log can hold two claims)
        k = (r['person'], r['work'], r['credit'], r['evidence'])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    out = uniq
    cols = list(out[0])
    with gzip.open(TABLE, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        wr.writerows(sorted(out, key=lambda r: (r['credit'], r['person'], r['work'])))
    cnt = Counter((r['credit'], r['role']) for r in out)
    print(json.dumps({f'{a}:{b}': n for (a, b), n in sorted(cnt.items())}, indent=1), flush=True)


# ---------------------------------------------------------------- report

def report(args):
    c = con()
    c.execute(f"CREATE OR REPLACE TABLE er AS SELECT * FROM read_csv('{TABLE}', all_varchar=true)")
    rep = {}
    rep['credits_by_role'] = {f'{a}:{b}': n for a, b, n in c.execute(
        "SELECT credit, role, count(*) FROM er GROUP BY 1, 2 ORDER BY 1, 3 DESC").fetchall()}
    rep['edited_by_role_and_evidence'] = {f'{a}:{b}': n for a, b, n in c.execute(
        "SELECT role, evidence, count(*) FROM er WHERE credit='edited' GROUP BY 1, 2 ORDER BY 1, 2").fetchall()}
    rep['edited_by_basis'] = {f'{a}|{b}': n for a, b, n in c.execute(
        "SELECT role, basis, count(*) FROM er WHERE credit='edited' GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()}
    rep['authored_by_basis'] = {f'{a}|{b}': n for a, b, n in c.execute(
        "SELECT role, basis, count(*) FROM er WHERE credit='authored' GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()}
    rep['edited_total'] = c.execute('SELECT count(*) FROM ed').fetchone()[0]
    # credits: all AUTHORED + EDITED (key log and linked); 'after' drops edition roles
    c.execute("""CREATE OR REPLACE TEMP TABLE cred AS
        SELECT a."from" AS person, a."to" AS work, 'authored' AS credit, coalesce(er.role, 'author') AS role FROM au a
          LEFT JOIN er ON er.person = a."from" AND er.work = a."to" AND er.credit = 'authored'
        UNION ALL SELECT e."from", e."to", 'edited', coalesce(er.role, 'unknown') FROM ed e
          LEFT JOIN er ON er.person = e."from" AND er.work = e."to" AND er.credit = 'edited'""")
    EXCL = "('edition-editor','translator','introducer','series-editor','contributor')"
    c.execute("CREATE OR REPLACE TEMP TABLE tw AS SELECT DISTINCT src, dst FROM cites")
    c.execute(f"""CREATE OR REPLACE TEMP TABLE pt AS SELECT c.person, t.src, bool_or(c.role NOT IN {EXCL}) own,
                  bool_or(c.role IN {EXCL}) via_edition FROM cred c JOIN tw t ON t.dst = c.work GROUP BY 1, 2""")
    rep['theses_with_edition_credit_pairs'] = c.execute(
        "SELECT count(*) FILTER (WHERE via_edition AND NOT own), count(*) FILTER (WHERE via_edition) FROM pt").fetchone()
    losers = c.execute("""SELECT p.person, pe.label, count(*) theses_before, count(*) FILTER (WHERE own) theses_after,
            count(*) FILTER (WHERE NOT own) lost, pe.lcnaf, pe.wd FROM pt p JOIN person pe ON pe.key = p.person
            GROUP BY ALL HAVING count(*) FILTER (WHERE NOT own) > 0 ORDER BY lost DESC, p.person LIMIT 200""").df()
    # rank among all people before
    c.execute("CREATE OR REPLACE TEMP TABLE rk AS SELECT person, count(*) n, rank() OVER (ORDER BY count(*) DESC) r FROM pt GROUP BY 1")
    top500 = c.execute(f"""SELECT count(*) FROM (SELECT p.person, count(*) n, count(*) FILTER (WHERE NOT own) lost
        FROM pt p JOIN rk USING (person) WHERE rk.r <= 500 GROUP BY 1) WHERE lost >= 0.5 * n""").fetchone()[0]
    rep['top500_half_or_more_via_edition_roles'] = top500
    rep['top500_half_or_more_via_any_edited_before'] = c.execute("""
        WITH x AS (SELECT c.person, t.src, bool_or(c.credit = 'authored') au FROM cred c JOIN tw t ON t.dst = c.work GROUP BY 1, 2)
        SELECT count(*) FROM (SELECT person, count(*) n, count(*) FILTER (WHERE NOT au) e FROM x JOIN rk USING (person)
        WHERE rk.r <= 500 GROUP BY 1) WHERE e >= 0.5 * n""").fetchone()[0]
    # gainers: proposed AUTHORED rows to the real author
    c.execute("""CREATE OR REPLACE TEMP TABLE newau AS SELECT DISTINCT author_key AS person, work FROM er
                 WHERE author_new = 'yes' AND role IN ('edition-editor','translator','introducer','series-editor','contributor') AND coalesce(author_key, '') <> ''""")
    c.execute("""CREATE OR REPLACE TEMP TABLE before_a AS SELECT DISTINCT c.person, t.src FROM cred c JOIN tw t ON t.dst = c.work
                 WHERE c.role NOT IN ('edition-editor','translator','introducer','series-editor','contributor')""")
    gain = c.execute("""SELECT n.person, pe.label, count(DISTINCT t.src) theses_via_new,
            count(DISTINCT t.src) FILTER (WHERE b.src IS NULL) theses_gained,
            (SELECT count(*) FROM before_a x WHERE x.person = n.person) theses_before, count(DISTINCT n.work) works
            FROM newau n JOIN tw t ON t.dst = n.work JOIN person pe ON pe.key = n.person
            LEFT JOIN before_a b ON b.person = n.person AND b.src = t.src
            GROUP BY ALL ORDER BY theses_gained DESC, theses_via_new DESC LIMIT 200""").df()
    # the real authors of the works whose editors lose the citation: theses on those works, and how many reach
    # the author only through the proposed AUTHORED row
    real = c.execute("""WITH ew AS (SELECT DISTINCT author_key AS person, work FROM er WHERE coalesce(author_key, '') <> ''
                            AND role IN ('edition-editor','translator','introducer','series-editor','contributor'))
        SELECT ew.person, pe.label, count(DISTINCT t.src) theses_on_edition_works,
               count(DISTINCT t.src) FILTER (WHERE b.src IS NULL) theses_new_to_author, count(DISTINCT ew.work) works,
               bool_or(ew.work IN (SELECT work FROM newau WHERE person = ew.person)) gets_new_row
        FROM ew JOIN tw t ON t.dst = ew.work JOIN person pe ON pe.key = ew.person
        LEFT JOIN before_a b ON b.person = ew.person AND b.src = t.src
        GROUP BY ALL ORDER BY theses_on_edition_works DESC LIMIT 200""").df()
    real.head(50).to_csv(OUT / 'top-real-authors.csv', index=False)
    rep['top_real_authors_15'] = real.head(15)[['person', 'label', 'theses_on_edition_works', 'theses_new_to_author']].values.tolist()
    rep['edition_credit_theses_already_reaching_author'] = c.execute("""
        WITH ew AS (SELECT DISTINCT author_key AS person, work FROM er WHERE coalesce(author_key, '') <> ''
                    AND role IN ('edition-editor','translator','introducer','series-editor','contributor'))
        SELECT count(DISTINCT (ew.person, t.src)), count(DISTINCT (ew.person, t.src)) FILTER (WHERE b.src IS NOT NULL)
        FROM ew JOIN tw t ON t.dst = ew.work LEFT JOIN before_a b ON b.person = ew.person AND b.src = t.src""").fetchone()
    rep['proposed_authored_rows'] = c.execute('SELECT count(*), count(DISTINCT person), count(DISTINCT work) FROM newau').fetchone()
    rep['thesis_citations_on_works_with_new_author'] = c.execute(
        'SELECT count(*) FROM tw WHERE dst IN (SELECT work FROM newau)').fetchone()[0]
    # edition-role works with no author credit at all: keyed (proposed) / not keyed (printed only) / no LC author
    c.execute("""CREATE OR REPLACE TEMP TABLE erw AS SELECT work, any_value(author_key) ak, any_value(printed_author) pa,
                 any_value(author_lcnaf) al FROM er WHERE credit = 'edited' AND role IN ('edition-editor','translator','introducer')
                 GROUP BY 1""")
    rep['edition_role_works'] = c.execute("""SELECT count(*),
        count(*) FILTER (WHERE work NOT IN (SELECT "to" FROM au)),
        count(*) FILTER (WHERE work NOT IN (SELECT "to" FROM au) AND coalesce(ak, '') <> ''),
        count(*) FILTER (WHERE work NOT IN (SELECT "to" FROM au) AND coalesce(ak, '') = '' AND coalesce(pa, '') <> ''),
        count(*) FILTER (WHERE work NOT IN (SELECT "to" FROM au) AND coalesce(ak, '') = '' AND coalesce(pa, '') = '') FROM erw""").fetchone()
    rep['edition_role_works_cols'] = ['works', 'no_authored_credit', 'author_keyed', 'author_not_keyed_printed', 'no_author_found']
    unk = c.execute("""SELECT pa printed_author, al author_lcnaf, count(DISTINCT e.work) works, count(DISTINCT t.src) theses
        FROM erw e LEFT JOIN tw t ON t.dst = e.work WHERE e.work NOT IN (SELECT "to" FROM au) AND coalesce(ak, '') = '' AND coalesce(pa, '') <> ''
        GROUP BY 1, 2 ORDER BY theses DESC, works DESC""").df()
    rep['unkeyed_authors'] = dict(people=len(unk), with_citing_theses=int((unk.theses > 0).sum()),
                                  two_plus_theses=int((unk.theses >= 2).sum()), theses_pairs=int(unk.theses.sum()))
    newrows = c.execute("""SELECT n.person, n.work, 'lc-main-entry' AS basis, 'exact' AS state, e.author_lcnaf AS lcnaf,
        string_agg(DISTINCT e.person, ';') via_editors FROM newau n JOIN er e ON e.author_key = n.person AND e.work = n.work
        GROUP BY ALL ORDER BY 1, 2""").df()
    OUT.mkdir(parents=True, exist_ok=True)
    newrows.to_csv(OUT / 'missing-authors.csv.gz', index=False)
    unk.to_csv(OUT / 'unkeyed-authors.csv.gz', index=False)
    losers.head(50).to_csv(OUT / 'top-losers.csv', index=False)
    gain.head(50).to_csv(OUT / 'top-gainers.csv', index=False)
    rep['top_losers_15'] = losers.head(15)[['person', 'label', 'theses_before', 'theses_after', 'lost']].values.tolist()
    rep['top_gainers_15'] = gain.head(15)[['person', 'label', 'theses_before', 'theses_gained', 'theses_via_new']].values.tolist()
    # Di Tella class: AUTHORED on books where LC main entry is someone else and the person is not in the record
    conf = c.execute("""SELECT e.person, pe.label, e.work, w.label title, w.year, e.evidence, e.source, e.printed_author lc_main_entry,
        e.author_key lc_main_key, e.basis, (SELECT count(DISTINCT src) FROM tw WHERE dst = e.work) theses,
        'hold as candidate: the LC record names another author and not this person' recommendation
        FROM er e JOIN person pe ON pe.key = e.person JOIN wk w ON w.key = e.work
        WHERE e.credit = 'authored' AND e.role = 'absent' ORDER BY theses DESC""").df()
    CONFLICTS.parent.mkdir(parents=True, exist_ok=True)
    conf.to_csv(CONFLICTS, index=False)
    rep['lc_author_conflicts'] = dict(rows=len(conf), linked=int((conf.evidence == 'linked').sum()),
                                      keylog=int((conf.evidence == 'keylog').sum()),
                                      by_source=conf.groupby(conf.source.fillna('')).size().to_dict(),
                                      thesis_pairs=int(conf.theses.sum()))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, default=str, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if not k.startswith('edited_by_basis') and k != 'authored_by_basis'},
                     indent=1, default=str, ensure_ascii=False))


# ---------------------------------------------------------------- audit sample

def sample(args):
    """60 edition-editor and 60 volume-editor EDITED credits (15 each for translator, introducer, series-editor),
    stratified by basis (equal shares per basis, at least one), with the LC statements of the asserting records, for
    hand judgement. Local file in the scratch folder (catalogue text)."""
    import random
    c = con(read_only=True)
    L = LCData(c)
    plab = dict(c.execute('SELECT key, label FROM person').fetchall())
    wlab = dict(c.execute('SELECT key, label FROM wk').fetchall())
    claim_ctl = defaultdict(set)
    for cl, l in c.execute('SELECT claim, lccn FROM claim_lc').fetchall():
        claim_ctl[cl] |= L.ctl_of.get(l, set())
    pw_claims = defaultdict(set)
    for p, w, cl in c.execute('SELECT "from", "to", claim FROM ed').fetchall():
        pw_claims[p, w].add(cl)
    rows = list(csv.DictReader(gzip.open(TABLE, 'rt', encoding='utf-8')))
    rows = [r for r in rows if r['credit'] == 'edited']
    rnd = random.Random(args.seed)
    picked = []
    for role, n_total in (('edition-editor', 60), ('volume-editor', 60), ('translator', 15), ('introducer', 15), ('series-editor', 15)):
        by = defaultdict(list)
        for r in rows:
            if r['role'] == role:
                by[r['basis']].append(r)
        bases = sorted(by, key=lambda b: -len(by[b]))
        per = max(1, n_total // max(1, len(bases)))
        left = n_total
        for i, b in enumerate(bases):
            k = min(len(by[b]), per if i < len(bases) - 1 else left, left)
            if k <= 0:
                break
            picked += rnd.sample(by[b], k)
            left -= k
        if left > 0:                      # fill from the largest basis
            rest = [r for r in by[bases[0]] if r not in picked] if bases else []
            picked += rnd.sample(rest, min(left, len(rest)))
    with open(SCRATCH / 'audit-sample.tsv', 'w', encoding='utf-8') as f:
        f.write('n\trole\tbasis\tperson\tlabel\twork\ttitle\tlc\tprinted_author\tauthor_key\n')
        for n, r in enumerate(picked, 1):
            ctls = set()
            for cl in pw_claims.get((r['person'], r['work']), ()):
                ctls |= claim_ctl.get(cl, set())
            ctls = ctls or set(L.wrec.get(r['work'], ()))
            lc = ' || '.join(f"{ctl}: {L.rec.get(ctl, ('', '', '', ''))[2]} [" + '; '.join(
                f"{h['tag']} {h['heading']} ({'/'.join(sorted(h['rel']))})" for h in L.heads.get(ctl, [])) + ']' for ctl in sorted(ctls)[:3])
            f.write('\t'.join(str(x).replace('\t', ' ').replace('\n', ' ') for x in (
                n, r['role'], r['basis'], r['person'], plab.get(r['person'], ''), r['work'], wlab.get(r['work'], ''), lc,
                r['printed_author'], r['author_key'])) + '\n')
    print(len(picked), 'rows ->', SCRATCH / 'audit-sample.tsv')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('prepare')
    a.add_argument('--claims-only', action='store_true')
    sub.add_parser('classify')
    sub.add_parser('report')
    a = sub.add_parser('sample')
    a.add_argument('--seed', type=int, default=7)
    args = ap.parse_args()
    {'prepare': prepare, 'classify': classify, 'report': report, 'sample': sample}[args.cmd](args)


if __name__ == '__main__':
    main()
