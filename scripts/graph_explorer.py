"""Local explorer for the knowledge graph (2026-11-08; user: "a web interface to visualize and explore the graph,
focused on one person and their edges to other nodes; click on other nodes and show the edges from that node").
Reads the graph build (build/graph/*.parquet from scripts/build_graph.py), never the key log or any text.

    python3 scripts/graph_explorer.py build      # build/graph/explorer.duckdb: nodes, sorted edge copies, weights
    python3 scripts/graph_explorer.py serve      # http://localhost:4180/  (builds first if the graph is newer)

API (JSON): /api/search?q=   /api/node?key=   /api/group?key=&rel=&offset=&limit=&sort=weight|year
Weights: a work's weight is the number of works citing it plus reviews of it; a person's is the sum over the works
they authored. Life years are not shown (site rule for living people); the explorer is local for now.
"""
import argparse, json, os, re, sys, threading, time, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = Path(os.environ.get('EXPLORER_GRAPH', ROOT / 'build/graph'))   # another build (a check build) for testing
DB = G / 'explorer.duckdb'
STATIC = ROOT / 'explorer'
EDGES = ['authored', 'cites', 'reviews', 'reviewed', 'supervised', 'advised', 'awarded_by', 'coauthored', 'coedited',
         'edited', 'editor_of', 'part_of', 'published_as', 'possibly_same', 'affiliated_with']
# one edge table per relation (2026-11-11): authored, edited, coauthored and reviewed carry `evidence` ('keylog' or
# 'linked': a rule or identifier credit outside the key log, marked on its row). author_candidates is not an edge: the
# unconfirmed name-compatible people for a work, shown as one collapsed section.
OPTIONAL = ['edition_of',                               # translation/edition node -> canonical work (2026-11-11)
            'author_candidates',
            'contributed',                              # foreword writers, series editors -> work (2026-11-11)
            'awarded', 'prize_candidates',              # Prize -> Person | Work, unconfirmed winners (2026-11-12)
            'same_work']                                # one work under two keys, hidden -> shown (pass seven, class 11)
# columns a newer build adds; an older build gets them as NULL so the explorer still builds against it
ADDED = {'part_of': [('evidence', "'keylog'"), ('source', 'NULL'), ('volume_basis', 'NULL')],
         'author_candidates': [('reason', 'NULL')],
         # the part a person had in the work (2026-11-12, data/graph/edition-roles.csv.gz, volume-editors.csv.gz)
         'authored': [('role', "'author'"), ('role_basis', 'NULL'), ('n_claims', "'1'"), ('claims', 'NULL')],
         'edited': [('role', "'unknown'"), ('role_basis', 'NULL'), ('n_claims', "'1'"), ('claims', 'NULL')],
         # co-editor pairs resting on linked editor credits (2026-11-12)
         'coedited': [('evidence', "'keylog'"), ('linked_works', '0')],
         # reviews of a book found by title or a review-style label (2026-11-12, scripts/review_books.py)
         'reviews': [('evidence', "'keylog'"), ('source', 'NULL')],
         # reviewer -> editor of the reviewed volume (2026-11-13)
         'reviewed': [('target_role', "'author'")]}
WORK_ADDED = ('issn', 'journal_source', 'kind_proposed', 'isbn', 'editors_printed', 'first_year_basis')
WORK_ADDED_INT = ('first_year', 'first_year_catalogue')
# credits under which a person prepared someone else's work (an edition, a translation, an introduction, a series):
# shown apart and never counted as citations of the person's own work (class 15, 2026-11-12)
# 'contributor' (2026-11-12, class 23): a qualified editor of the book ('cartographic editor', 'associate editor',
# 'maps edited by'), not its volume editor
EDITION_ROLES = "('edition-editor','translator','introducer','series-editor','contributor')"
NOT_AUTHOR = "('edition-editor','translator','introducer','series-editor','contributor','volume-editor')"
ROLE_L = ("CASE e.role WHEN 'edition-editor' THEN 'edited this edition' WHEN 'translator' THEN 'translator' "
          "WHEN 'introducer' THEN 'introduction' WHEN 'series-editor' THEN 'series editor' "
          "WHEN 'contributor' THEN 'contributor (associate, assistant, consulting, picture or map editor ...)' ELSE e.role END")
# a thesis citing a translation or later edition is a CITES edge to the canonical work (edition = true unless it also
# cites the work directly; cited_as = the node it was cited as); the canonical work counts the citation
EDITION_D = ("CASE WHEN bool_or(e.edition) OR any_value(e.cited_as) IS NOT NULL THEN 'cited in translation or another edition'"
             " || coalesce(' (as: ' || (SELECT label FROM nodes WHERE key = split_part(any_value(e.cited_as), ';', 1)) || ')', '')"
             " END")
EDITION_OF_D = "any_value(e.relation) || ', ' || any_value(e.theses) || ' citing theses moved to the original'"
# rows resting only on a credit outside the key log are marked; key-log rows carry no note
LINKED_D = ("CASE WHEN bool_or(e.evidence = 'keylog') THEN NULL ELSE "
            "'linked: ' || string_agg(DISTINCT CASE WHEN e.source = 'scored-links' THEN 'scored link (score ' || round(e.score, 1) || ')' WHEN e.source = 'classified-links' THEN 'classified link (p=' || round(e.score, 3) || ')' ELSE "
            "CASE WHEN e.state = 'exact' THEN 'by identifier' WHEN e.role_basis LIKE 'evidence: %' THEN substr(e.role_basis, 11) ELSE 'by rule' END || ' ('"
            " || CASE e.source WHEN 'lc' THEN 'LC' WHEN 'openalex' THEN 'OpenAlex' WHEN 'work-people:reviewer' THEN 'printed reviewer'"
            " WHEN 'work-people:jstor-author' THEN 'JSTOR author' WHEN 'work-people:author' THEN 'OpenAlex/Crossref author list'"
            " WHEN 'volume-editors:crossref' THEN 'Crossref editor list' WHEN 'volume-editors:lc' THEN 'LC editor statement'"
            " WHEN 'edition-roles:lc-main-entry' THEN 'LC main entry'"
            " WHEN 'name-only:openalex' THEN 'OpenAlex author list' WHEN 'name-only:crossref' THEN 'Crossref author list'"
            " WHEN 'name-only:crossref-volume' THEN 'Crossref chapter list of the volume' WHEN 'name-only:jstor' THEN 'JSTOR author list'"
            " WHEN 'name-only:ojs' THEN 'journal OJS author list'"
            " WHEN 'name-only:recent-books' THEN 'Crossref/OpenAlex book record' WHEN 'name-only:journal-meta' THEN 'journal record'"
            " WHEN 'lc-catalogue:100' THEN 'LC main entry' WHEN 'lc-catalogue:700' THEN 'LC added entry'"
            " WHEN 'lc-catalogue:authority-books' THEN 'LC book filed under their name authority'"
            " WHEN 'lc-catalogue:tied-100' THEN 'LC main entry; authority tied by evidence, not yet anchored'"
            " WHEN 'lc-catalogue:tied-700' THEN 'LC added entry; authority tied by evidence, not yet anchored'"
            " WHEN 'lc-catalogue:tied-authority-books' THEN 'LC book filed under a name authority tied by evidence, not yet anchored'"
            " WHEN 'prizes:winner' THEN 'prize winner list' WHEN 'prizes:lc-main-entry' THEN 'LC main entry of the prize work'"
            " ELSE e.source END || ')' || CASE WHEN e.score IS NOT NULL THEN ', scored link agrees (score ' || round(e.score, 1) || ')' ELSE '' END END,"
            " '; ') || '; not a key-log claim' END")
# EDITOR_OF (2026-11-12): the volume, marked when the row rests on a linked PART_OF, editor or author credit
VOLUME_D = ("(SELECT label FROM nodes WHERE key = any_value(e.volume)) || CASE WHEN count(DISTINCT e.volume) > 1 THEN ' and others' ELSE '' END "
            "|| CASE WHEN bool_and(e.evidence = 'linked') THEN ' (linked: a volume link or credit outside the key log)' ELSE '' END")
BOOK_D = ("(SELECT label FROM nodes WHERE key = any_value(e.book)) || CASE WHEN bool_and(e.evidence = 'linked') THEN ' (linked)' ELSE '' END"
          " || CASE WHEN bool_and(e.target_role = 'volume-editor') THEN ' (reviewed the volume they edited)' ELSE '' END")
POSSIBLE_D = ("'unconfirmed: ' || CASE WHEN any_value(e.reason) IS NOT NULL THEN any_value(e.reason) || ' -- not credited' "
              "WHEN any_value(e.n_candidates) = 1 THEN 'name match only (the sole candidate left after the "
              "name and date tests; no confirming fact)' ELSE 'one of ' || any_value(e.n_candidates) || ' candidates for this "
              "name' END || CASE WHEN any_value(e.reason) IS NOT NULL THEN '' ELSE ' -- ' || any_value(e.role) || ' of the work; not credited' END")
# a chapter's volume, as a note on a work row ('in <volume>, edited by <editors>'), from the vol_note table
VOL_D = "(SELECT note FROM vol_note WHERE key = any_value(e.\"to\"))"
# pass seven (class 11): a pair the key log holds two or more claims for is one row, with each claim and its route
CLAIMS_D = ("CASE WHEN max(coalesce(e.n_claims, 1)::INT) > 1 THEN max(e.n_claims) || ' key-log claims, one work: ' "
            "|| any_value(e.claims) END")
# and one work held under two keys (SAME_WORK) is listed once on a person credited on both: the other key is named
ALSO_D = ("(SELECT 'also held as ' || string_agg(coalesce(n.label, '') || ' [' || d.hidden || '; ' || d.basis || ']', ' | ') "
          "FROM dup_hide d JOIN nodes n ON n.key = d.hidden WHERE d.person = $k AND d.shown = any_value(e.\"to\"))")
# class 37: a credit found through a stated alternate family-name form (the form is a source note, never a label or alias)
TIE_D = "CASE WHEN bool_or(e.role_basis LIKE 'name-form-tie:%') THEN substr(any_value(e.role_basis), 16) END"
WORK_ROW_D = f"concat_ws(' · ', {LINKED_D}, {VOL_D}, {CLAIMS_D}, {ALSO_D}, {TIE_D})"
PART_D = ("CASE WHEN bool_or(e.evidence = 'keylog') THEN NULL ELSE 'linked: ' || string_agg(DISTINCT CASE e.source "
          "WHEN 'orcid-container' THEN 'the ORCID record names the volume' WHEN 'doi-container' THEN 'the DOI record names the volume' "
          "WHEN 'author-works-container' THEN 'the OpenAlex/Crossref record names the volume' "
          "WHEN 'name-only-volume' THEN 'Crossref lists the chapter under the volume' ELSE e.source END || ' (' || "
          "CASE e.volume_basis WHEN 'title' THEN 'one volume with that title' WHEN 'book-doi' THEN 'book DOI' "
          "WHEN 'new-unkeyed-volume' THEN 'volume made from the record' WHEN 'main-title' THEN 'main title only' "
          "WHEN 'chapter-doi' THEN 'chapter DOI extends the book DOI' WHEN 'isbn' THEN 'the volume ISBN' "
          "ELSE e.volume_basis END || ')', '; ') || '; not a key-log claim' END")
CONTRIB_D = ("'contributor (' || string_agg(DISTINCT CASE e.basis WHEN 'lc-foreword' THEN 'foreword, by the LC record' "
             "WHEN 'series-foreword-pattern' THEN 'series foreword' "
             "WHEN 'series-editor-pattern' THEN 'series editor (Crossref editor list; publisher pattern)' ELSE e.basis END, '; ') || '); linked, not an author'")

PRIZE_D = ("string_agg(DISTINCT coalesce(e.year::VARCHAR, '') || ' ' || e.honours || CASE WHEN e.state IN ('exact', 'credited', 'matched') "
           "THEN '' ELSE ' (linked: ' || e.state || ', ' || coalesce(e.basis, '') || ')' END, '; ') || ' · ' || any_value(e.source)")
WIN_D = ("string_agg(DISTINCT coalesce(e.year::VARCHAR, '') || CASE WHEN e.state IN ('exact', 'credited', 'matched') THEN '' "
         "WHEN e.state = 'linked' THEN ' (winner linked by rule)' WHEN e.state = 'found' THEN ' (book record found by title and winner)' "
         "WHEN e.state = 'lc' THEN ' (LC record)' WHEN e.state = 'added' THEN ' (known from the prize list only)' ELSE ' (' || e.state || ')' END, ', ')")
PCAND_D = "'unconfirmed winner (' || any_value(e.n_candidates) || ' candidate(s), ' || coalesce(any_value(e.branch), '') || '); not credited'"

REV_D = ("CASE WHEN bool_or(e.evidence = 'keylog') THEN NULL ELSE 'linked: ' || CASE any_value(e.source) "
         "WHEN 'review-books:title' THEN 'an article titled as the book, by another author, within six years' "
         "WHEN 'review-books:label' THEN 'the record prints the reviewed book and its author' ELSE any_value(e.source) END "
         "|| '; not a key-log claim' END")
# Relations shown for each node type: (id, label, edge table, self side, other side, detail SQL over e and o)
# `e` is the edge row, `o` the other node. Rows are grouped by the other node (n = number of edges to it).
REL = {
    'person': [
        ('authored', 'Works authored', 'authored', 'from', 'to', WORK_ROW_D, f"coalesce(e.role, 'author') NOT IN {NOT_AUTHOR} "
         "AND e.\"to\" NOT IN (SELECT hidden FROM dup_hide WHERE person = $k)"),
        ('edited', 'Works edited', None, None, None, None),     # EDITED (not edition roles) + AUTHORED as volume editor
        ('editions_prepared', 'Editions, translations and other contributions they prepared', None, None, None, None),
        ('contributed', 'Forewords and series contributions', 'contributed', 'from', 'to', CONTRIB_D),
        ('supervised', 'Supervised theses', 'supervised', 'from', 'to', None),
        ('students', 'Students', 'advised', 'from', 'to', "(SELECT label FROM nodes WHERE key = any_value(e.thesis))"),
        ('advisors', 'Advisors', 'advised', 'to', 'from', "(SELECT label FROM nodes WHERE key = any_value(e.thesis))"),
        ('reviewed', 'Reviews written (authors of the books reviewed)', 'reviewed', 'from', 'to', BOOK_D),
        ('reviewed_by', 'Reviewed by', 'reviewed', 'to', 'from', BOOK_D),
        ('coauthors', 'Co-authors', 'coauthored', None, None, None),
        ('coeditors', 'Co-editors', 'coedited', None, None, None),
        ('editor_of', 'Edited chapters by', 'editor_of', 'from', 'to', VOLUME_D),
        ('in_volumes_of', 'Chapters in volumes edited by', 'editor_of', 'to', 'from', VOLUME_D),
        ('cited_by_people', 'Cited by (people)', None, None, None, None),
        ('cited_by_works', 'Cited by (works)', None, None, None, None),
        ('cites_people', 'Cites (people)', None, None, None, None),
        ('possibly_same', 'Possibly the same person', 'possibly_same', None, None, None),
        ('affiliations', 'Affiliations', None, None, None, None),
        ('prizes', 'Prizes', 'awarded', 'to', 'from', PRIZE_D, 'e.shown'),
        ('prizes_other', 'Other honours (Wikidata; not history)', 'awarded', 'to', 'from', PRIZE_D, 'NOT e.shown'),
        ('prize_candidates', 'Possible prizes (winner not confirmed)', 'prize_candidates', 'to', 'from', PCAND_D),
        ('candidates', 'Unconfirmed candidates (not credited)', 'author_candidates', 'from', 'to', POSSIBLE_D),
    ],
    'work': [
        ('authors', 'Authors', 'authored', 'to', 'from', LINKED_D, f"coalesce(e.role, 'author') NOT IN {NOT_AUTHOR}"),
        ('editors', 'Editors', None, None, None, None),
        ('edition_people', 'This edition prepared by (editors, translators, introductions, series editors, contributors)', None, None, None, None),
        ('volume_editors', 'Editors of the volume it is in', None, None, None, None),
        ('contributors', 'Contributors (foreword, series editor)', 'contributed', 'to', 'from', CONTRIB_D),
        ('chapter_authors', 'Contributors (authors of its chapters)', None, None, None, None),
        ('supervisors', 'Supervisors', 'supervised', 'to', 'from', None),
        ('awarded_by', 'Degree from', 'awarded_by', 'from', 'to', None),
        ('cites', 'Cites', 'cites', 'from', 'to', None),
        ('cited_by', 'Cited by', 'cites', 'to', 'from', EDITION_D),
        ('editions', 'Editions and translations (EDITION_OF, seen from the original; their citations count here)',
         'edition_of', 'to', 'from', EDITION_OF_D),
        ('edition_of', 'Edition or translation of (EDITION_OF, seen from the edition)',
         'edition_of', 'from', 'to', EDITION_OF_D),
        ('reviews', 'Review of', 'reviews', 'from', 'to', REV_D),
        ('reviewed_in', 'Reviewed in', 'reviews', 'to', 'from', REV_D),
        ('part_of', 'Part of', 'part_of', 'from', 'to', PART_D),
        ('contains', 'Contains (chapters)', 'part_of', 'to', 'from', PART_D),
        ('same_work', 'The same work under another key (listed once on people pages; not merged)', 'same_work', 'from', 'to',
         "any_value(e.basis)"),
        ('same_work_of', 'The same work under another key (listed once on people pages; not merged)', 'same_work', 'to', 'from',
         "any_value(e.basis)"),
        ('published_as', 'Published as', 'published_as', 'from', 'to', None),
        ('published_from', 'Published from', 'published_as', 'to', 'from', None),
        ('prizes', 'Prizes', 'awarded', 'to', 'from', PRIZE_D, 'e.shown'),
        ('prizes_other', 'Other honours (Wikidata; not history)', 'awarded', 'to', 'from', PRIZE_D, 'NOT e.shown'),
        ('candidates', 'Unconfirmed candidates (not credited)', 'author_candidates', 'to', 'from', POSSIBLE_D),
    ],
    'prize': [
        ('winners', 'Winners (by year)', None, None, None, None),
        ('prize_works', 'Winning works (by year)', None, None, None, None),
        ('prize_candidates', 'Unconfirmed winners (not credited)', 'prize_candidates', 'from', 'to', PCAND_D),
    ],
    'institution': [
        ('faculty', 'Faculty and affiliated people', None, None, None, None),
        ('advisors_here', 'Advised PhDs here', None, None, None, None),
        ('theses', 'Theses awarded', 'awarded_by', 'to', 'from', None),
    ],
}
EVIDENCE_TABLES = ('authored', 'edited', 'reviewed', 'coauthored', 'part_of', 'contributed', 'editor_of', 'advised', 'reviews')
# AWARDED rows are all linked (prize facts never come from the key log); not marked per row
LINKS = {'wd': 'https://www.wikidata.org/wiki/{}', 'orcid': 'https://orcid.org/{}',
         'lcnaf': 'https://id.loc.gov/authorities/names/{}', 'viaf': 'https://viaf.org/viaf/{}',
         'gnd': 'https://d-nb.info/gnd/{}', 'isni': 'https://isni.org/isni/{}', 'idref': 'https://www.idref.fr/{}',
         'doi': 'https://doi.org/{}', 'lccn': 'https://lccn.loc.gov/{}', 'ror': 'https://ror.org/{}',
         'ol': 'https://openlibrary.org/authors/{}', 'openalex': 'https://openalex.org/{}'}


def build():
    t0 = time.time()
    tmp = DB.with_suffix('.tmp')
    tmp.unlink(missing_ok=True)
    db = duckdb.connect(str(tmp))
    db.execute("SET preserve_insertion_order = true")
    for e in EDGES + [x for x in OPTIONAL if (G / f'{x}.parquet').exists()]:
        src = f"'{G}/{e}.parquet'"
        db.execute(f'CREATE TABLE e_{e}_f AS SELECT * FROM {src} ORDER BY "from"')
        db.execute(f'CREATE TABLE e_{e}_t AS SELECT * FROM {src} ORDER BY "to"')
        for col, default in ADDED.get(e, []):
            for side in 'ft':
                db.execute(f'ALTER TABLE e_{e}_{side} ADD COLUMN IF NOT EXISTS {col} VARCHAR DEFAULT {default}')
    db.execute(f"""CREATE TABLE work_w AS SELECT w.key,
        coalesce(c.n, 0) AS cited, coalesce(r.n, 0) AS reviewed
        FROM '{G}/work.parquet' w
        LEFT JOIN (SELECT "to" k, count(*) n FROM e_cites_t GROUP BY 1) c ON c.k = w.key
        LEFT JOIN (SELECT "to" k, count(*) n FROM e_reviews_t GROUP BY 1) r ON r.k = w.key""")
    # one row per (person, work) even when the key log holds two authored claims for it; credits under an edition role
    # (edition editor, translator, introducer, series editor, contributor) are not the person's own work (2026-11-12)
    # one work under two keys (pass seven, class 11): the hidden key of a SAME_WORK pair is not listed or counted for a
    # person credited on both
    if (G / 'same_work.parquet').exists():
        db.execute("""CREATE TABLE dup_hide AS SELECT DISTINCT a."from" AS person, sw."from" AS hidden, sw."to" AS shown, sw.basis
            FROM e_same_work_f sw JOIN e_authored_t a ON a."to" = sw."from" JOIN e_authored_t b ON b."to" = sw."to" AND b."from" = a."from"
            ORDER BY person""")
    else:
        db.execute("CREATE TABLE dup_hide (person VARCHAR, hidden VARCHAR, shown VARCHAR, basis VARCHAR)")
    db.execute(f"""CREATE TABLE person_w AS SELECT a."from" AS key, count(*) works, sum(w.cited) cited, sum(w.reviewed) reviewed
        FROM (SELECT DISTINCT x."from", x."to" FROM e_authored_f x ANTI JOIN dup_hide d ON d.person = x."from" AND d.hidden = x."to"
              WHERE coalesce(x.role, 'author') NOT IN {EDITION_ROLES}) a
        JOIN work_w w ON w.key = a."to" GROUP BY 1""")
    wcols = {r[0] for r in db.execute(f"DESCRIBE SELECT * FROM '{G}/work.parquet'").fetchall()}
    wx = ', '.join([f'w.{c}' if c in wcols else f'NULL::VARCHAR AS {c}' for c in WORK_ADDED]
                   + [f'w.{c}' if c in wcols else f'NULL::INTEGER AS {c}' for c in WORK_ADDED_INT])
    nx = ', '.join([f'NULL::VARCHAR AS {c}' for c in WORK_ADDED] + [f'NULL::INTEGER AS {c}' for c in WORK_ADDED_INT])
    # prizes (2026-11-12): kind = the honours most rows give, year = first year, journal = the awarding body
    prize_sql = (f"""UNION ALL SELECT z.key, 'prize', z.label || CASE WHEN z.shown THEN '' ELSE ' (Wikidata honour)' END,
               z.honours, z.first_year, z.body, 'unkeyed', CASE WHEN z.wd IS NULL THEN []::VARCHAR[] ELSE ['wd:' || z.wd] END,
               z.rows, NULL, NULL, NULL, {nx} FROM '{G}/prize.parquet' z""" if (G / 'prize.parquet').exists() else '')
    db.execute(f"""CREATE TABLE nodes AS
        SELECT p.key, 'person' AS type, p.label, NULL::VARCHAR AS kind, NULL::INTEGER AS year, NULL::VARCHAR AS journal,
               p.resolution, p.anchors, coalesce(s.cited, 0) + coalesce(s.reviewed, 0) AS weight,
               coalesce(s.works, 0) AS works, coalesce(s.cited, 0) AS cited, coalesce(s.reviewed, 0) AS reviewed, {nx}
          FROM '{G}/person.parquet' p LEFT JOIN person_w s ON s.key = p.key
        UNION ALL
        SELECT w.key, 'work', w.label, w.kind, w.year, w.journal, w.resolution, w.anchors, s.cited + s.reviewed,
               NULL, s.cited, s.reviewed, {wx}
          FROM '{G}/work.parquet' w JOIN work_w s ON s.key = w.key
        UNION ALL
        SELECT i.key, 'institution', i.label, NULL, NULL, NULL, i.resolution, i.anchors,
               (SELECT count(*) FROM e_awarded_by_t a WHERE a."to" = i.key), NULL, NULL, NULL, {nx}
          FROM '{G}/institution.parquet' i
        {prize_sql}
        ORDER BY key""")
    # a chapter's volume as one line: 'in <volume> (<year>), edited by <credited editors>; editors as printed: <names>'
    # (credited: EDITED other than edition roles, and AUTHORED credits that are volume editorships; 2026-11-12)
    db.execute(f"""CREATE TABLE vol_note AS
        WITH ed AS (SELECT "from", "to" FROM e_edited_t WHERE coalesce(role, 'unknown') NOT IN {EDITION_ROLES}
                    UNION SELECT "from", "to" FROM e_authored_t WHERE role = 'volume-editor'),
             eds AS (SELECT e."to" AS v, string_agg(DISTINCT p.label, ', ') AS names FROM ed e
                     JOIN nodes p ON p.key = e."from" GROUP BY 1)
        SELECT po."from" AS key, string_agg(DISTINCT 'in ' || v.label || coalesce(' (' || v.year || ')', '')
               || coalesce(', edited by ' || eds.names, '') || coalesce('; editors as printed: ' || v.editors_printed, ''), ' | ') AS note
        FROM e_part_of_f po JOIN nodes v ON v.key = po."to" LEFT JOIN eds ON eds.v = po."to"
        GROUP BY 1 ORDER BY 1""")
    db.execute("""CREATE TABLE search AS SELECT key, type, weight, strip_accents(lower(label)) AS s FROM nodes
                  WHERE type <> 'work' OR weight > 0 OR kind = 'thesis' ORDER BY weight DESC""")
    db.execute("CREATE TABLE anchors AS SELECT lower(unnest(anchors)) AS anchor, key FROM nodes ORDER BY anchor")
    db.execute("DROP TABLE work_w; DROP TABLE person_w")
    # the report is passed as a parameter: its text may hold apostrophes
    db.execute("CREATE TABLE meta AS SELECT now() AS built, ? AS report", [json.dumps(json.load(open(G / 'report.json')))])
    db.close()
    tmp.replace(DB)
    print(f'built {DB} in {time.time() - t0:.0f}s, {DB.stat().st_size / 1e6:.0f} MB')


def stale():
    return not DB.exists() or any(p.stat().st_mtime > DB.stat().st_mtime for p in G.glob('*.parquet'))


UNKEYED = ('doi:', 'lccn:', 'openalex:', 'corpus:', 'ojs:', 'bepress:', 'volume:')


def node_type(key):
    if key.startswith('prize:'):
        return 'prize'
    # unkeyed works: Crossref citing articles, cited works matched to LC/OpenAlex/Crossref (build_graph, 2026-11-10),
    # journal-metadata matches (ojs:, bepress:), author-works and their volumes (volume:; 2026-11-11). Person and
    # institution keys never hold a colon, so any other prefixed key is an unkeyed work too.
    if key.startswith(UNKEYED) or ':' in key:
        return 'work'
    return {'p': 'person', 'w': 'work', 'i': 'institution'}.get(key[:1])


def ids(anchors):
    out = []
    for a in anchors or []:
        s, _, v = a.partition(':')
        out.append(dict(scheme=s, value=v, url=LINKS[s].format(v) if s in LINKS else None))
    return out


ITEM_COLS = 'o.key, o.type, o.kind, o.label, o.year, o.weight, o.resolution, o.kind_proposed'


def item(r):
    return dict(key=r[0], type=r[1], kind=r[2], label=r[3], year=r[4], weight=r[5], resolution=r[6],
                kind_proposed=r[7], n=r[8], detail=r[9] if len(r) > 9 else None)


class Graph:
    def __init__(self):
        self.db = duckdb.connect(str(DB), read_only=True)
        self.local = threading.local()

    def has(self, table):
        if not hasattr(self, '_tables'):
            self._tables = {r[0] for r in self.cur().execute('SELECT table_name FROM information_schema.tables').fetchall()}
        return f'e_{table}_f' in self._tables

    def cur(self):
        if not hasattr(self.local, 'c'):
            self.local.c = self.db.cursor()
        return self.local.c

    def group_sql(self, rel, key):
        """SQL yielding (other_key, n, detail) rows for one relation of one node."""
        rid, _, table, me, other, detail = rel[:6]
        where = f' AND {rel[6]}' if len(rel) > 6 else ''
        if rid in ('editions', 'edition_of', 'candidates', 'contributed', 'contributors', 'same_work', 'same_work_of') and not self.has(table):
            return 'SELECT NULL k, 0 n, NULL d, 0 lk WHERE false'
        if rid in ('edited', 'editors'):  # EDITED (not an edition role) and AUTHORED credits that are volume editorships
            me, other = ('from', 'to') if rid == 'edited' else ('to', 'from')
            side = 'f' if me == 'from' else 't'
            return (f"""SELECT e."{other}" k, 1 n, concat_ws(' · ', {LINKED_D}, CASE WHEN bool_or(e.how = 'authored')
                        THEN 'editor of the volume (the source record files it as authorship: ' || any_value(e.role_basis) || ')' END) d,
                        bool_and(e.evidence = 'linked')::INT lk FROM (
                        SELECT "from", "to", evidence, state, source, score, role_basis, 'edited' how FROM e_edited_{side}
                         WHERE "{me}" = $k AND coalesce(role, 'unknown') NOT IN {EDITION_ROLES}
                        UNION ALL SELECT "from", "to", evidence, state, source, score, role_basis, 'authored' FROM e_authored_{side}
                         WHERE "{me}" = $k AND role = 'volume-editor') e GROUP BY 1""")
        if rid in ('editions_prepared', 'edition_people'):    # edition editor, translator, introducer, series editor, contributor
            me, other = ('from', 'to') if rid == 'editions_prepared' else ('to', 'from')
            side = 'f' if me == 'from' else 't'
            return (f"""SELECT e."{other}" k, 1 n, concat_ws(' · ', string_agg(DISTINCT {ROLE_L}, ', '), {LINKED_D},
                        'not counted as a citation of their own work') d, bool_and(e.evidence = 'linked')::INT lk FROM (
                        SELECT "from", "to", evidence, state, source, score, role FROM e_authored_{side}
                         WHERE "{me}" = $k AND role IN {EDITION_ROLES}
                        UNION ALL SELECT "from", "to", evidence, state, source, score, role FROM e_edited_{side}
                         WHERE "{me}" = $k AND role IN {EDITION_ROLES}) e GROUP BY 1""")
        if rid == 'volume_editors':       # a chapter's volume(s): credited editors, then unconfirmed candidates
            cand = ("""UNION ALL SELECT ac."from", v.v, 'candidate', NULL, ac.source FROM v JOIN e_author_candidates_t ac
                       ON ac."to" = v.v WHERE ac.role = 'editor'""" if self.has('author_candidates') else '')
            return (f"""WITH v AS (SELECT DISTINCT "to" v FROM e_part_of_f WHERE "from" = $k),
                        c AS (SELECT e."from", v.v, e.evidence, e.state, e.source FROM v JOIN e_edited_t e ON e."to" = v.v
                               WHERE coalesce(e.role, 'unknown') NOT IN {EDITION_ROLES}
                              UNION ALL SELECT e."from", v.v, e.evidence, e.state, e.source FROM v JOIN e_authored_t e
                               ON e."to" = v.v WHERE e.role = 'volume-editor' {cand})
                        SELECT c."from" k, count(DISTINCT c.v) n,
                               string_agg(DISTINCT CASE WHEN c.evidence = 'candidate' THEN 'unconfirmed candidate (name match only; not credited): '
                                          ELSE '' END || 'editor of ' || nv.label
                                          || CASE WHEN c.evidence = 'linked' THEN ' (linked: ' || c.source || ')' ELSE '' END, '; ') d,
                               bool_and(c.evidence <> 'keylog')::INT lk
                        FROM c JOIN nodes nv ON nv.key = c.v GROUP BY 1""")
        if rid == 'coauthors':            # one row per pair; key-log works plus works resting on a linked credit
            cols = ("""works + CASE WHEN evidence = 'keylog' THEN linked_works ELSE 0 END n,
                       (works + CASE WHEN evidence = 'keylog' THEN linked_works ELSE 0 END) || ' works'
                       || CASE WHEN linked_works > 0 THEN ' (' || linked_works || ' through a linked credit)' ELSE '' END
                       || CASE WHEN first_year IS NULL THEN '' ELSE ', ' || first_year || '–' || last_year END d,
                       (evidence = 'linked')::INT lk""")
            return (f"""SELECT "to" k, {cols} FROM e_coauthored_f WHERE "from" = $k
                        UNION SELECT "from", {cols} FROM e_coauthored_t WHERE "to" = $k""")
        if rid == 'coeditors':            # one row per pair, as co-authors (linked pairs since 2026-11-12)
            cols = ("""works + CASE WHEN evidence = 'keylog' THEN linked_works ELSE 0 END n,
                       (works + CASE WHEN evidence = 'keylog' THEN linked_works ELSE 0 END) || ' works'
                       || CASE WHEN linked_works > 0 THEN ' (' || linked_works || ' through a linked credit)' ELSE '' END
                       || CASE WHEN first_year IS NULL THEN '' ELSE ', ' || first_year || '–' || last_year END d,
                       (evidence = 'linked')::INT lk""")
            return (f"""SELECT "to" k, {cols} FROM e_{table}_f WHERE "from" = $k
                        UNION SELECT "from", {cols} FROM e_{table}_t WHERE "to" = $k""")
        if rid in ('winners', 'prize_works'):     # a prize's winners or works, newest first (n = the latest year)
            if not self.has('awarded'):
                return 'SELECT NULL k, 0 n, NULL d, 0 lk WHERE false'
            tgt = 'person' if rid == 'winners' else 'work'
            return (f"""SELECT e."to" k, max(coalesce(e.year, 0)) n, {WIN_D} d, 0 lk FROM e_awarded_f e
                        WHERE e."from" = $k AND e.target = '{tgt}' GROUP BY 1""")
        if rid in ('prizes', 'prizes_other', 'prize_candidates') and not self.has(table):
            return 'SELECT NULL k, 0 n, NULL d, 0 lk WHERE false'
        if rid == 'possibly_same':        # same name, timelines fit, not confirmed (scripts/key_possible_same.py)
            return ('''SELECT "to" k, 1 n, 'same name, timelines fit; not confirmed' d FROM e_possibly_same_f WHERE "from" = $k
                       UNION SELECT "from", 1, 'same name, timelines fit; not confirmed' FROM e_possibly_same_t WHERE "to" = $k''')
        if rid in ('faculty', 'affiliations'):     # dated affiliations, all sources in one line
            me, other = ('to', 'from') if rid == 'faculty' else ('from', 'to')
            side = 't' if me == 'to' else 'f'
            return (f'''SELECT "{other}" k, count(*) n, string_agg(CASE source WHEN 'aha_directory' THEN 'AHA directory'
                        WHEN 'aha_advisor' THEN 'advised PhDs' WHEN 'ihr' THEN 'IHR staff list' WHEN 'orcid' THEN 'ORCID'
                        WHEN 'wikidata' THEN 'Wikidata' WHEN 'review_credit' THEN 'review credit'
                        WHEN 'jstor_signature' THEN 'JSTOR review signature' WHEN 'lc_373' THEN 'LC authority' ELSE source END
                        || CASE WHEN first_year IS NULL AND last_year IS NULL THEN ''
                                WHEN first_year = last_year OR first_year IS NULL THEN ' ' || last_year
                                WHEN last_year IS NULL THEN ' ' || first_year || '–'
                                ELSE ' ' || first_year || '–' || last_year END, '; ' ORDER BY last_year DESC NULLS LAST) d
                        FROM e_affiliated_with_{side} WHERE "{me}" = $k GROUP BY 1''')
        if rid == 'advisors_here':        # supervisors of theses this institution awarded
            return ('''SELECT s."from" k, count(*) n, count(*) || ' theses, ' || min(w.year) || '–' || max(w.year) d
                       FROM e_awarded_by_t a JOIN e_supervised_t s ON s."to" = a."from" JOIN nodes w ON w.key = a."from"
                       WHERE a."to" = $k GROUP BY 1''')
        if rid == 'chapter_authors':      # a volume's contributors: the authors of the chapters PART_OF it
            return ("""SELECT a."from" k, count(DISTINCT a."to") n, count(DISTINCT a."to") || ' chapters'
                       || CASE WHEN bool_and(a.evidence = 'linked') THEN ' (linked author credit)' ELSE '' END d,
                       bool_and(a.evidence = 'linked')::INT lk
                       FROM e_part_of_t p JOIN e_authored_t a ON a."to" = p."from" WHERE p."to" = $k GROUP BY 1""")
        if rid == 'cited_by_people':      # people whose works cite this person's works (key-log and linked authors)
            return (f"""SELECT a2."from" k, count(DISTINCT c."from") n, count(DISTINCT c."from") || ' citing works'
                       || CASE WHEN bool_and(a2.evidence = 'linked') THEN ' (linked author credit)' ELSE '' END d,
                       bool_and(a2.evidence = 'linked')::INT lk
                       FROM e_authored_f a JOIN e_cites_t c ON c."to" = a."to" JOIN e_authored_t a2 ON a2."to" = c."from"
                       WHERE a."from" = $k AND a2."from" <> $k AND coalesce(a.role, 'author') NOT IN {EDITION_ROLES} GROUP BY 1""")
        if rid == 'cited_by_works':       # distinct citing documents (theses, articles), not people
            return (f"""SELECT c."from" k, count(DISTINCT a."to") n, count(DISTINCT a."to") || ' of this person''s works cited' d
                       FROM (SELECT DISTINCT "to" FROM e_authored_f WHERE "from" = $k AND coalesce(role, 'author') NOT IN {EDITION_ROLES}) a
                       JOIN e_cites_t c ON c."to" = a."to" GROUP BY 1""")
        if rid == 'cites_people':         # people whose works this person's works cite
            return (f"""SELECT a2."from" k, count(DISTINCT c."to") n, count(DISTINCT c."to") || ' works cited' d
                       FROM e_authored_f a JOIN e_cites_f c ON c."from" = a."to" JOIN e_authored_t a2 ON a2."to" = c."to"
                       WHERE a."from" = $k AND a2."from" <> $k AND coalesce(a2.role, 'author') NOT IN {EDITION_ROLES} GROUP BY 1""")
        side = 'f' if me == 'from' else 't'
        d = detail or 'NULL'
        # a person and a work once, even when the key log holds two claims for them (2026-11-11)
        n = '1' if table in ('authored', 'edited') else 'count(*)'
        lk = "bool_and(e.evidence = 'linked')::INT" if table in EVIDENCE_TABLES else '0'
        return f'SELECT e."{other}" k, {n} n, {d} d, {lk} lk FROM e_{table}_{side} e WHERE e."{me}" = $k{where} GROUP BY 1'

    def group(self, key, rel, offset=0, limit=12, sort='weight'):
        order = 'o.year DESC NULLS LAST, o.weight DESC' if sort == 'year' else 'g.n DESC, o.weight DESC, o.year DESC NULLS LAST'
        sql = self.group_sql(rel, key)
        if ' lk' not in sql:
            sql = f'SELECT k, n, d, 0 lk FROM ({sql})'
        q = f"""WITH g AS ({sql})
                SELECT {ITEM_COLS}, g.n, g.d, count(*) OVER () AS total, sum(g.lk) OVER () AS linked
                FROM g JOIN nodes o ON o.key = g.k ORDER BY {order}, o.key LIMIT {int(limit)} OFFSET {int(offset)}"""
        rows = self.cur().execute(q, dict(k=key)).fetchall()
        total = rows[0][-2] if rows else (0 if offset == 0 else None)
        self.local.last_linked = int(rows[0][-1] or 0) if rows else 0
        return [item(r[:-2]) for r in rows], total

    def node(self, key, limit=12, sort='weight'):
        r = self.cur().execute("""SELECT key, type, label, kind, year, journal, resolution, anchors, weight, works, cited, reviewed,
                                  kind_proposed, issn, journal_source, isbn, editors_printed,
                                  (SELECT note FROM vol_note WHERE vol_note.key = nodes.key),
                                  first_year, first_year_catalogue, first_year_basis
                                  FROM nodes WHERE key = ?""", [key]).fetchone()
        if not r:
            return None
        n = dict(zip(['key', 'type', 'label', 'kind', 'year', 'journal', 'resolution', 'anchors', 'weight', 'works',
                      'cited', 'reviewed', 'kind_proposed', 'issn', 'journal_source', 'isbn', 'editors_printed',
                      'in_volume', 'first_year', 'first_year_catalogue', 'first_year_basis'], r))
        n['ids'] = ids(n.pop('anchors'))
        if n['type'] == 'work':          # citations that reached this work through a translation or another edition
            n['cited_edition'] = self.cur().execute(
                'SELECT count(*) FROM e_cites_t WHERE "to" = ? AND (edition OR cited_as IS NOT NULL)', [key]).fetchone()[0]
        groups = []
        for rel in REL[n['type']]:
            items, total = self.group(key, rel, 0, limit, sort)
            if total:
                nl = self.local.last_linked
                lab = rel[1] + (f' ({nl} linked)' if nl else '')
                groups.append(dict(id=rel[0], label=lab, total=total, linked=nl, items=items))
        return dict(node=n, groups=groups)

    def search(self, q, limit=24):
        q = q.strip()
        if not q:
            return []
        c = self.cur()
        hits = []
        if re.fullmatch(r'[pwi]-\d+', q):
            hits = [q]
        else:
            a = q.lower()
            if re.fullmatch(r'q\d+', a):
                a = 'wd:' + a.upper().lower()
            elif re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dx]', a):
                a = 'orcid:' + a
            elif re.fullmatch(r'n[bor]?\d{6,}', a):
                a = 'lcnaf:' + a
            elif a.startswith('10.'):
                a = 'doi:' + a
            hits = [k for (k,) in c.execute('SELECT key FROM anchors WHERE anchor = ? LIMIT 5', [a]).fetchall()]
        if not hits:
            toks = [t for t in re.split(r'[\s,]+', c.execute('SELECT strip_accents(lower(?))', [q]).fetchone()[0]) if t]
            where = ' AND '.join('s LIKE ?' for _ in toks)
            args = [f'%{t}%' for t in toks]
            hits = [k for (k,) in c.execute(f"""(SELECT key FROM search WHERE type = 'person' AND {where} LIMIT {limit // 2})
                        UNION ALL (SELECT key FROM search WHERE type <> 'person' AND {where} LIMIT {limit // 2})""",
                                            args + args).fetchall()]
        if not hits:
            return []
        rows = c.execute(f"""SELECT key, type, kind, label, year, weight, resolution, kind_proposed, NULL, NULL FROM nodes
                             WHERE key IN (SELECT unnest(?)) ORDER BY type = 'person' DESC, weight DESC""", [hits]).fetchall()
        return [item(r) for r in rows]


GRAPH = None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if not u.path.startswith('/api/'):
            return super().do_GET()
        p = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == '/api/search':
                return self.send_json(GRAPH.search(p.get('q', '')))
            if u.path == '/api/node':
                r = GRAPH.node(p.get('key', ''), int(p.get('limit', 12)), p.get('sort', 'weight'))
                return self.send_json(r) if r else self.send_json(dict(error='no such node'), 404)
            if u.path == '/api/group':
                key = p['key']; t = node_type(key)
                rel = next(r for r in REL[t] if r[0] == p['rel'])
                items, total = GRAPH.group(key, rel, int(p.get('offset', 0)), min(int(p.get('limit', 50)), 500),
                                           p.get('sort', 'weight'))
                return self.send_json(dict(items=items, total=total))
            if u.path == '/api/meta':
                built, report = GRAPH.cur().execute('SELECT built, report FROM meta').fetchone()
                return self.send_json(dict(built=built, report=json.loads(report)))
            self.send_json(dict(error='unknown endpoint'), 404)
        except Exception as e:
            self.send_json(dict(error=str(e)), 500)


def main():
    global GRAPH
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['build', 'serve'])
    ap.add_argument('--port', type=int, default=4180)
    args = ap.parse_args()
    if args.cmd == 'build' or stale():
        build()
    if args.cmd == 'serve':
        GRAPH = Graph()
        print(f'graph explorer on http://localhost:{args.port}/', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
