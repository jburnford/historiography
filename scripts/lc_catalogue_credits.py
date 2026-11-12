"""Catalogue books whose LC record names a keyed person and that carry no credit (2026-11-12, integration pass five;
ARCHITECTURE.md section 8, class 30).

A work with an LCCN (a key-log work anchored on it, or an unkeyed `lccn:` node from the cited-works, JSTOR-note or
translation tables) and no AUTHORED or EDITED row of any evidence, whose LC record's main entry (100) or an added
entry (700) is a name authority that is an anchor on exactly one person key, gets an exact linked credit. Probe:
Labelle, *Dispersed but Not Destroyed* (w-1189686, lccn:2013443395, main entry lcnaf:no2013063272 on p-53033) had no
author. Before this script only the edition-roles pass did it (`missing-authors.csv.gz`, for works with an edition
role). Credits are identifier links (the authority is on the key), never key-log claims; identity scripts do not read
them (graph_tables.keylog).

The role of each credit is read from the record with scripts/edition_roles.py's classify_record (and through it
scripts/editor_qualifiers.py), the rules the edition-roles table uses:
- 100 main entry on a key: credit authored; classify_record gives author (AUTHORED), or volume-editor when the 100
  carries an editor relator or the 245 $c makes the main entry an editor (then EDITED, role volume-editor);
- 700 added entry on a key with an author relator ('joint author'), or no relator and a 245 $c clause that names the
  person as an author ('Karl Marx and Friedrich Engels'): AUTHORED author (classify_record, credit authored);
- 700 with an editor relator, or no relator and a 245 $c clause that makes the person an editor or director: EDITED
  with the role classify_record gives (volume-editor when there is no personal main entry; edition-editor,
  translator, introducer, series-editor or contributor otherwise: someone else's work prepared, not counted as own);
- a 700 with a translator / introduction relator, or none and no editing clause: not credited (counted);
- a work whose records give main entries on two different keys, neither named in the other's record: held (counted).

Second part (`measure`): every LC 2016 book whose main entry (100) is an authority on a person key and whose LCCN no
graph work holds: how many books, for how many keys, split by key has ORCID / not and by the key's evidence (thesis,
AHA, directory, supervisor, review). Written to data/identifiers/lc-catalogue-credits-2026-11-12/books-by-authority.csv.gz
(lccn, title, year, person key, lcnaf, evidence flags) and its counts to report.json. Loaded only for keys with
scholarly evidence (a thesis or AHA anchor, a key-log thesis, a directory anchor, supervision, a review): those rows go
to data/graph/lc-books-by-authority.csv.gz and the build makes unkeyed `lccn:` book nodes with an exact linked AUTHORED
credit (source lc-catalogue:authority-books). The full count (primary-source people included) stays measured only.

Since 2026-11-12 (pass six) both parts also read (1) LC records after 2016 fetched through SRU (scripts/lc_sru_recent.py,
build/lc-sru-2026-11-12/index; `record` = lc-sru) and (2) authorities tied to a key by evidence but not yet anchored
(data/graph/lc-authority-ties.csv.gz from scripts/key_lc_authority_ties.py; `link` = tied, linked evidence: the build
loads those credits with source lc-catalogue:tied-<tag> / tied-authority-books and state linked).

Outputs:
- data/graph/lc-credits.csv.gz: work (graph node key), person, credit (authored / edited), role, role_basis, lccn,
  control, lcnaf, heading, tag. The build loads them (evidence linked, source lc-catalogue:<tag>, state exact) where the
  work still has no AUTHORED/EDITED row.
- data/identifiers/lc-catalogue-credits-2026-11-12/report.json, held.csv.gz, audit-sample.csv.

    python3 scripts/lc_catalogue_credits.py credits     # reads build/graph, the LC 2016 index on E: (read-only)
    python3 scripts/lc_catalogue_credits.py measure
"""
import argparse
import csv
import gzip
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edition_roles as ER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = Path(os.environ.get('LCC_GRAPH', ROOT / 'build/graph'))
LC = Path('/mnt/e/lc-bib-2016/index')
SRU = ROOT / 'build/lc-sru-2026-11-12/index'        # scripts/lc_sru_recent.py: LC records after 2016 (SRU)
TIES = ROOT / 'data/graph/lc-authority-ties.csv.gz'   # scripts/key_lc_authority_ties.py: authorities tied by evidence
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
SCRATCH = Path(os.environ.get('LCC_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/lccredits'))
TABLE = ROOT / 'data/graph/lc-credits.csv.gz'
BOOKS = ROOT / 'data/graph/lc-books-by-authority.csv.gz'
OUT = ROOT / 'data/identifiers/lc-catalogue-credits-2026-11-12'


def lcsrc(kind):
    """the LC 2016 index and, when it is there, the SRU index of later records (same columns; SRU rows carry route)"""
    files = [f"'{LC}/{kind}-*.parquet'"]
    if (SRU / f'{kind}-sru.parquet').exists():
        files.append(f"'{SRU}/{kind}-sru.parquet'")
    return f"read_parquet([{', '.join(files)}], union_by_name=true)"


def person_authorities(c):
    """pl: authority -> person key, n keys, link ('anchor': an lcnaf anchor on the key; 'tied': a strong or medium tie
    from key_lc_authority_ties.py on an authority no key holds, linked evidence)"""
    c.execute(f"""CREATE OR REPLACE TABLE pl AS SELECT substr(a, 7) lcid, any_value(key) AS pkey, count(DISTINCT key) AS n,
                  'anchor' AS link FROM (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') WHERE a LIKE 'lcnaf:%' GROUP BY 1""")
    if TIES.exists():
        c.execute(f"""INSERT INTO pl SELECT lcnaf, any_value(person), count(DISTINCT person), 'tied'
                      FROM read_csv('{TIES}', all_varchar=true) WHERE lcnaf NOT IN (SELECT lcid FROM pl) GROUP BY 1""")


def con():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'tmp').mkdir(exist_ok=True)
    c = duckdb.connect(str(SCRATCH / 'lc.duckdb'))
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH / 'tmp'}'; "
              "SET preserve_insertion_order=false")
    return c


def resolve_headings(c):
    """hres: heading -> LC name authority ($0, else the one live authority whose authorised form is the heading), as
    scripts/edition_roles.py prepare"""
    c.execute(r"""CREATE OR REPLACE MACRO hnorm(h) AS (
        WITH x AS (SELECT regexp_replace(regexp_replace(replace(coalesce(h, ''), '’', ''''), '\s+', ' ', 'g'),
                                         '\s*,\s*', ', ', 'g') v)
        SELECT CASE WHEN regexp_matches(trim(v, ' ,'), '(\b\w|-)\.$') THEN trim(v, ' ,') ELSE rtrim(trim(v, ' ,'), '.') END FROM x)""")
    c.execute("CREATE OR REPLACE TABLE hn AS SELECT DISTINCT heading, hnorm(heading) n, uri FROM hd")
    c.execute(f"CREATE OR REPLACE TEMP TABLE allnames AS SELECT lcid, label, hnorm(label) n, birth, death, deprecated FROM '{NAMES}'")
    c.execute("CREATE OR REPLACE TABLE names AS SELECT a.* FROM allnames a SEMI JOIN (SELECT DISTINCT n FROM hn) h ON h.n = a.n")
    c.execute("""CREATE OR REPLACE TABLE hres AS
        WITH byuri AS (SELECT heading, regexp_extract(uri, '([a-z]+[0-9]+)/?$', 1) lcid FROM hn WHERE uri <> ''),
             bylab AS (SELECT n, list(lcid) ids FROM names WHERE NOT deprecated GROUP BY 1)
        SELECT h.heading, any_value(coalesce(nullif(u.lcid, ''), CASE WHEN len(b.ids) = 1 THEN b.ids[1] END)) lcid
        FROM hn h LEFT JOIN byuri u USING (heading) LEFT JOIN bylab b ON b.n = h.n GROUP BY 1""")
    c.execute('DROP TABLE allnames')


def prepare(c):
    # a credit this script made in an earlier run (source lc-catalogue:*) does not count: the table is rewritten whole
    c.execute(f"""CREATE OR REPLACE TABLE credited AS SELECT DISTINCT "to" w FROM '{G}/authored.parquet'
                  WHERE coalesce(source, '') NOT LIKE 'lc-catalogue:%'
                  UNION SELECT DISTINCT "to" FROM '{G}/edited.parquet' WHERE coalesce(source, '') NOT LIKE 'lc-catalogue:%'""")
    c.execute(f"""CREATE OR REPLACE TABLE wk AS SELECT key, label, kind, year, lccn, anchors, resolution FROM '{G}/work.parquet'
        WHERE (lccn IS NOT NULL OR len(list_filter(anchors, a -> a LIKE 'lccn:%')) > 0) AND key NOT IN (SELECT w FROM credited)""")
    c.execute("""CREATE OR REPLACE TABLE wlccn AS SELECT DISTINCT key, substr(a, 6) lccn FROM (SELECT key, unnest(anchors) a
                 FROM wk) WHERE a LIKE 'lccn:%' UNION SELECT key, lccn FROM wk WHERE lccn IS NOT NULL""")
    c.execute(f"""CREATE OR REPLACE TABLE rec AS SELECT trim(r.control) control, r.lccn, r.title, r.date1, r.lang,
        r.responsibility, r.publisher FROM {lcsrc('records')} r
        WHERE trim(r.control) IN (SELECT lccn FROM wlccn) OR r.lccn IN (SELECT lccn FROM wlccn)""")
    c.execute(f"""CREATE OR REPLACE TABLE hd AS SELECT trim(h.control) control, h.pos, h.tag, h.heading, h.family, h.given,
        h.uri, h.dates, h.relators FROM {lcsrc('headings')} h WHERE trim(h.control) IN (SELECT control FROM rec)""")
    c.execute("""CREATE OR REPLACE TABLE wrec AS SELECT l.key, r.control FROM wlccn l JOIN rec r ON r.control = l.lccn
                 UNION SELECT l.key, r.control FROM wlccn l JOIN rec r ON r.lccn = l.lccn""")
    c.execute("""CREATE OR REPLACE TABLE lccn_ctl AS SELECT control lccn, control FROM rec UNION SELECT lccn, control FROM rec
                 WHERE lccn IS NOT NULL AND lccn <> ''""")
    resolve_headings(c)
    person_authorities(c)
    for t in ('wk', 'wrec', 'rec', 'hd', 'hres', 'pl'):
        print(t, c.execute(f'SELECT count(*) FROM {t}').fetchone()[0], flush=True)


NAME_CHUNK = re.compile(r"^(?:[A-ZÀ-Þ][\w'’.-]*\.?\s*){1,6}$")


def plain_names(resp):
    """the statement of responsibility is only a list of names ('Jay Spaulding and Lidwien Kapteijns'): no role word
    (edited, réunies, bezorgd, director, preface ...) that could make a person named there something other than an author"""
    t = re.sub(r'^\s*(?:by|par|von|por|di|de)\s+', '', (resp or '').strip(' .;'), flags=re.I)
    if not t:
        return False
    chunks = [c.strip() for c in re.split(r'\s*(?:,|;|&|\band\b|\bet\b|\bund\b|\by\b|\be\b)\s*', t) if c.strip()]
    return bool(chunks) and all(NAME_CHUNK.match(c) for c in chunks)


def credit_of(L, ctl, h, resp):
    """(credit, role, basis) for heading h of record ctl, or (None, reason, None)"""
    lcids = {h['lcid']}
    rel = h['rel']
    if h['tag'] == '100':
        r = ER.classify_record(L, ctl, lcids, h['family'], h['given'], 'authored')
        if r['role'] == 'volume-editor':
            return 'edited', 'volume-editor', r['basis']
        if r['role'] in ('author', 'author-editor'):
            return 'authored', 'author', r['basis']
        return None, f"main-entry-{r['role']}", None
    crole = ER.clause_role(resp, h['family'], h['given'])
    if (rel & ER.AUTHOR_REL and not rel & (ER.EDITOR_REL | ER.TRANS_REL)) or (not rel and crole == 'author' and plain_names(resp)):
        # a joint-author relator, or no relator and a plain 245 $c clause naming the person with the main entry
        r = ER.classify_record(L, ctl, lcids, h['family'], h['given'], 'authored')
        return ('authored', 'author', r['basis']) if r['role'] == 'author' else (None, f"700-author-{r['role']}", None)
    if rel & ER.EDITOR_REL or (not rel and crole in ('editor', 'director')):
        r = ER.classify_record(L, ctl, lcids, h['family'], h['given'], 'edited')
        if r['role'] in (None, 'absent', 'unknown'):
            return None, f"700-editor-{r['role']}", None
        return 'edited', 'volume-editor' if r['role'] == 'author-editor' else r['role'], r['basis']
    if rel & ER.TRANS_REL or crole == 'translator':
        return None, '700-translator', None
    if rel and all(ER.INTRO_REL.search(x) for x in rel):
        return None, '700-introducer', None
    return None, f"700-{'relator-' + '/'.join(sorted(rel)) if rel else 'no-role-' + str(crole)}", None


def credits(args):
    c = con()
    prepare(c)
    L = ER.LCData(c)
    pkey = {lcid: key for lcid, key, n in c.execute('SELECT lcid, pkey, n FROM pl').fetchall() if n == 1}
    plink = dict(c.execute('SELECT lcid, link FROM pl').fetchall())
    sru = {r[0] for r in c.execute(f"SELECT DISTINCT trim(control) FROM '{SRU}/records-sru.parquet'").fetchall()} \
        if (SRU / 'records-sru.parquet').exists() else set()
    rep = Counter()
    rows, held = [], []
    wkinfo = {k: (lab, kind, res) for k, lab, kind, res in c.execute('SELECT key, label, kind, resolution FROM wk').fetchall()}
    rep['works_with_lccn_no_credit'] = len(wkinfo)
    rep['works_with_lccn_no_credit_keyed'] = sum(1 for v in wkinfo.values() if v[2] != 'unkeyed')
    rep['works_with_an_lc_record'] = len(L.wrec)
    for w, ctls in L.wrec.items():
        found = {}                                   # (person, credit) -> row
        main_keys = defaultdict(set)                 # person key from a 100 -> records
        named = defaultdict(set)                     # record -> keys named in it (100 / 700)
        for ctl in sorted(set(ctls)):
            title, date1, resp, lang = L.rec.get(ctl, ('', '', '', ''))
            for h in L.heads.get(ctl, []):
                if h['tag'] not in ('100', '700') or not h['lcid']:
                    continue
                k = pkey.get(h['lcid'])
                if not k:
                    continue
                named[ctl].add(k)
                cr, role, basis = credit_of(L, ctl, h, resp)
                if not cr:
                    rep[f'not_credited|{role}'] += 1
                    continue
                if h['tag'] == '100' and cr == 'authored':
                    main_keys[k].add(ctl)
                found.setdefault((k, cr), dict(work=w, person=k, credit=cr, role=role, role_basis=basis, lccn=ctl, control=ctl,
                                               lcnaf=h['lcid'], heading=h['heading'], tag=h['tag'],
                                               link=plink.get(h['lcid'], 'anchor'), record='lc-sru' if ctl in sru else 'lc2016'))
        if len(main_keys) > 1:
            # two main entries on different keys: fine when each record names the other key too (co-authors), else held
            ks = set(main_keys)
            if not all(ks <= named[ctl] for ctl in set(ctls) if named[ctl] & ks):
                held.append(dict(work=w, label=wkinfo[w][0], keys=';'.join(sorted(ks)), records=';'.join(sorted(set(ctls)))))
                rep['held_two_main_entries'] += 1
                continue
        for r in found.values():
            rows.append(r)
            rep[f"credit|{r['credit']}|{r['role']}"] += 1
            rep[f"credit_on|{'unkeyed' if wkinfo[w][2] == 'unkeyed' else 'keyed'}"] += 1
            rep[f"credit_by|{r['link']}|{r['record']}"] += 1
    rep['works_credited'] = len({r['work'] for r in rows})
    rep['works_credited_keyed'] = len({r['work'] for r in rows if wkinfo[r['work']][2] != 'unkeyed'})
    rep['people_credited'] = len({r['person'] for r in rows})
    cols = ['work', 'person', 'credit', 'role', 'role_basis', 'lccn', 'control', 'lcnaf', 'heading', 'tag', 'link', 'record']
    with gzip.open(TABLE, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for r in sorted(rows, key=lambda r: (r['work'], r['person'], r['credit'])):
            wr.writerow({k: r[k] for k in cols})
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / 'held.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['work', 'label', 'keys', 'records'])
        wr.writeheader()
        wr.writerows(held)
    rnd = random.Random(1112)
    sample = rnd.sample(rows, min(40, len(rows)))
    with open(OUT / 'audit-sample.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['work', 'work_label', 'person', 'person_label', 'credit', 'role', 'role_basis', 'heading', 'tag',
                     'lc_title', 'lc_statement', 'verdict'])
        plab = dict(c.execute(f"SELECT key, label FROM '{G}/person.parquet' WHERE key IN (SELECT unnest(?))",
                              [sorted({r['person'] for r in sample})]).fetchall())
        for r in sample:
            t, d1, resp, lang = L.rec.get(r['control'], ('', '', '', ''))
            wr.writerow([r['work'], wkinfo[r['work']][0], r['person'], plab.get(r['person'], ''), r['credit'], r['role'],
                         r['role_basis'], r['heading'], r['tag'], t, resp, ''])
    old = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    old['credits'] = dict(sorted(rep.items()))
    old['credits_note'] = ('works with an LCCN and no AUTHORED/EDITED row in the build read (any evidence); LC 2016 '
                           'bibliographic index; a heading credits a person only when its authority is an anchor on one key')
    (OUT / 'report.json').write_text(json.dumps(old, indent=1) + '\n')
    print(json.dumps(dict(sorted(rep.items())), indent=1))


def measure(args):
    """LC books by an authority on a person key that the graph lacks (not loaded)"""
    c = con()
    person_authorities(c)
    c.execute(f"""CREATE OR REPLACE TABLE pev AS SELECT key, orcid IS NOT NULL has_orcid,
            len(list_filter(anchors, a -> a LIKE 'aha-phd:%' OR a LIKE 'diss-author:%' OR a LIKE 'capes-person:%')) > 0 thesis_or_aha,
            len(list_filter(anchors, a -> a LIKE 'ihr:%' OR a LIKE 'aha:%' OR a LIKE 'repo-advisor:%')) > 0 directory,
            len(list_filter(anchors, a -> a LIKE 'review-credit%')) > 0 review_anchor
            FROM '{G}/person.parquet'""")
    c.execute(f"""CREATE OR REPLACE TABLE pev2 AS SELECT p.*,
            p.key IN (SELECT "from" FROM '{G}/supervised.parquet') supervisor,
            p.key IN (SELECT "from" FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
                      WHERE a.evidence = 'keylog' AND w.kind = 'review') reviewer,
            p.key IN (SELECT "from" FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
                      WHERE a.evidence = 'keylog' AND w.kind = 'thesis') thesis_author
            FROM pev p""")
    # the lccn: nodes an earlier run of this table added are not 'held by the graph' (the table is rewritten whole)
    prev = f"(SELECT 'lccn:' || lccn FROM read_csv('{BOOKS}', all_varchar=true))" if BOOKS.exists() else "(SELECT NULL)"
    c.execute(f"""CREATE OR REPLACE TABLE glccn AS SELECT DISTINCT substr(a, 6) lccn FROM (SELECT key, unnest(anchors) a FROM
                  '{G}/work.parquet' WHERE NOT (resolution = 'unkeyed' AND key IN {prev})) WHERE a LIKE 'lccn:%'
                  UNION SELECT lccn FROM '{G}/work.parquet' WHERE lccn IS NOT NULL AND NOT (resolution = 'unkeyed' AND key IN {prev})""")
    # the authority of each LC 100: $0, else the unique authorised label (resolve only headings of keyed authorities' labels)
    c.execute(f"""CREATE OR REPLACE TABLE hd AS SELECT trim(h.control) control, h.pos, h.tag, h.heading, h.family, h.given, h.uri,
                  h.dates, h.relators FROM {lcsrc('headings')} h WHERE h.tag = '100'""")
    resolve_headings(c)
    c.execute(f"""CREATE OR REPLACE TABLE bk AS SELECT trim(r.control) control, r.lccn, r.title, r.date1, h.heading, x.lcid,
            pl.pkey AS person, pl.link, {"CASE WHEN r.route IS NULL THEN 'lc2016' ELSE 'lc-sru' END" if (SRU / 'records-sru.parquet').exists() else "'lc2016'"} AS record
            FROM hd h JOIN hres x USING (heading) JOIN pl ON pl.lcid = x.lcid AND pl.n = 1
            JOIN {lcsrc('records')} r ON trim(r.control) = h.control
            WHERE trim(r.control) NOT IN (SELECT lccn FROM glccn) AND coalesce(r.lccn, '') NOT IN (SELECT lccn FROM glccn)
              AND NOT list_has_any(h.relators, ['ed', 'editor', 'comp', 'compiler', 'tr', 'translator'])""")
    q = lambda s: c.execute(s).fetchall()
    rep = {}
    rep['books'], rep['keys'] = q('SELECT count(DISTINCT control), count(DISTINCT person) FROM bk')[0]
    rows = q("""SELECT p.has_orcid, (p.thesis_or_aha OR p.thesis_author) thesis, p.directory, p.supervisor, (p.reviewer OR p.review_anchor) reviewer,
                count(DISTINCT b.control), count(DISTINCT b.person) FROM bk b JOIN pev2 p ON p.key = b.person GROUP BY ALL ORDER BY 6 DESC""")
    rep['by_evidence'] = [dict(has_orcid=a, thesis_or_aha=b_, directory=d, supervisor=s, reviewer=r, books=n, keys=k)
                          for a, b_, d, s, r, n, k in rows]
    sc = q("""SELECT p.has_orcid, count(DISTINCT b.control), count(DISTINCT b.person) FROM bk b JOIN pev2 p ON p.key = b.person GROUP BY 1""")
    rep['by_orcid'] = {('orcid' if a else 'no_orcid'): dict(books=n, keys=k) for a, n, k in sc}
    ev = q("""SELECT count(DISTINCT b.control), count(DISTINCT b.person) FROM bk b JOIN pev2 p ON p.key = b.person
              WHERE p.thesis_or_aha OR p.thesis_author OR p.directory OR p.supervisor OR p.reviewer OR p.review_anchor""")[0]
    rep['restricted_to_scholarly_evidence'] = dict(books=ev[0], keys=ev[1],
                                                   rule='key has a thesis or AHA anchor, a key-log thesis, a directory anchor, '
                                                        'supervises a thesis, or a key-log review / review-credit anchor')
    big = q("""SELECT person, count(DISTINCT control) n FROM bk GROUP BY 1 ORDER BY 2 DESC LIMIT 15""")
    rep['most_books'] = big
    rep['per_key_quantiles'] = q("SELECT quantile_cont(n, [0.5, 0.9, 0.99]) FROM (SELECT person, count(DISTINCT control) n FROM bk GROUP BY 1)")[0][0]
    OUT.mkdir(parents=True, exist_ok=True)
    c.execute(f"""COPY (SELECT b.control lccn, b.title, b.date1 AS year, b.person, b.lcid AS lcnaf, p.has_orcid,
                  (p.thesis_or_aha OR p.thesis_author) thesis, p.directory, p.supervisor, (p.reviewer OR p.review_anchor) reviewer
                  FROM bk b JOIN pev2 p ON p.key = b.person ORDER BY b.person, b.control)
                  TO '{OUT / 'books-by-authority.csv.gz'}' (HEADER, COMPRESSION gzip)""")
    # the restricted set is loaded (data/graph/lc-books-by-authority.csv.gz): keys with scholarly evidence only, so the
    # authors of primary sources (Voltaire, Lope de Vega, Gorky: hundreds of LC books each) do not pull in their editions
    rep['by_link_and_record'] = q("""SELECT b.link, b.record, count(DISTINCT b.control), count(DISTINCT b.person) FROM bk b
        JOIN pev2 p ON p.key = b.person WHERE p.thesis_or_aha OR p.thesis_author OR p.directory OR p.supervisor OR p.reviewer
        OR p.review_anchor GROUP BY ALL ORDER BY ALL""")
    c.execute(f"""COPY (SELECT b.control lccn, any_value(b.title) title, any_value(b.date1) AS year, b.person, any_value(b.lcid) lcnaf,
                  any_value(b.link) link, any_value(b.record) record
                  FROM bk b JOIN pev2 p ON p.key = b.person
                  WHERE p.thesis_or_aha OR p.thesis_author OR p.directory OR p.supervisor OR p.reviewer OR p.review_anchor
                  GROUP BY b.control, b.person ORDER BY b.person, b.control) TO '{BOOKS}' (HEADER, COMPRESSION gzip)""")
    old = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    old['books_by_authority'] = rep
    old['books_by_authority_note'] = ('LC 2016 books whose 100 main entry (no editor/compiler/translator relator) is an '
                                      'authority on one person key and whose LCCN no graph work holds; measured, not loaded')
    (OUT / 'report.json').write_text(json.dumps(old, indent=1, default=str) + '\n')
    print(json.dumps(rep, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('credits')
    sub.add_parser('measure')
    a = ap.parse_args()
    {'credits': credits, 'measure': measure}[a.cmd](a)


if __name__ == '__main__':
    main()
