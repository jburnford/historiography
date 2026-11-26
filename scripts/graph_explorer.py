"""Local explorer for the knowledge graph (2026-11-08; user: "a web interface to visualize and explore the graph,
focused on one person and their edges to other nodes; click on other nodes and show the edges from that node").
Reads the graph build (build/graph/*.parquet from scripts/build_graph.py), never the key log or any text.

    python3 scripts/graph_explorer.py build      # build/graph/explorer.duckdb: nodes, sorted edge copies, weights
    python3 scripts/graph_explorer.py serve      # http://localhost:4180/  (builds first if the graph is newer)

API (JSON): /api/search?q=   /api/node?key=   /api/group?key=&rel=&offset=&limit=&sort=weight|year
/api/compare?a=place:<QID>&b=place:<QID> (two places side by side; the page is #cmp:<QID>+<QID>).
Place pages (key place:<QID>, 2026-11-18) take &children=1 (include the places within it), &kind=, &decade=,
&source=lc|title|review, &fiction=1 (include LC tags that give the setting of a work of fiction; left out by default),
&hist=1 (people list: only people with a history thesis, history-journal article or review in the graph).
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
            'same_work',                                # one work under two keys, hidden -> shown (pass seven, class 11)
            'about_place', 'place_in']                  # place layer: Work -> Place, Place -> Place (2026-11-18)
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
         'reviewed': [('target_role', "'author'")],
         # employment / education / position / affiliation (2026-11-14, scripts/pid_records.py)
         'affiliated_with': [('kind', "'employment'")]}
WORK_ADDED = ('issn', 'journal_source', 'kind_proposed', 'isbn', 'editors_printed', 'first_year_basis', 'variant_titles')
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
            "'linked: ' || string_agg(DISTINCT CASE WHEN e.source = 'scored-links' THEN 'scored link (score ' || round(e.score, 1) || ')' WHEN e.source = 'classified-links' THEN 'classified link (p=' || round(e.score, 3) || ')' WHEN e.source = 'qwen-links' THEN 'Qwen clerical read (' || replace(e.role_basis, 'Qwen clerical read, ', '') || ')' ELSE "
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
          "FROM sw d JOIN nodes n ON n.key = d.hidden WHERE d.shown = any_value(e.\"to\"))")
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
        ('places', 'Places of their works (derived from the works they wrote, not a fact about the person)', None, None, None, None),
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
        ('places', 'Places (what the work is about)', None, None, None, None),
    ],
    'prize': [
        ('winners', 'Winners (by year)', None, None, None, None),
        ('prize_works', 'Winning works (by year)', None, None, None, None),
        ('prize_candidates', 'Unconfirmed winners (not credited)', 'prize_candidates', 'from', 'to', PCAND_D),
    ],
    # places (2026-11-18): works about a place (LC subject headings, read titles, reviews of such books) and the people
    # with works about it, derived from their works (place facts are never asserted of a person)
    'place': [
        ('about', 'Works about this place', None, None, None, None),
        ('people', 'People with works about this place (derived from their works)', None, None, None, None),
        ('catalogued', 'Catalogued authors not yet in the people index (LC main entries of works with no linked author)', None, None, None, None),
        ('wider', 'Wider region: works about a region that contains this place (not about the place itself)', None, None, None, None),
        ('periods', 'Period polities (searched together with this place)', None, None, None, None),
        ('parents', 'Located in', None, None, None, None),
        ('children', 'Places within it', None, None, None, None),
        ('overlaps', 'Crossing its border, and former units partly in it (links only)', None, None, None, None),
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
         'lcnaf': 'https://id.loc.gov/authorities/names/{}', 'lcsh': 'https://id.loc.gov/authorities/subjects/{}', 'viaf': 'https://viaf.org/viaf/{}',
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
    # one work under two keys (class 11): every SAME_WORK pair, hidden -> shown; citations of the hidden key count on the
    # shown work too (distinct citing works; 2026-11-13), the hidden node keeps its own count
    if (G / 'same_work.parquet').exists():
        db.execute(f"""CREATE TABLE sw AS SELECT DISTINCT "from" AS hidden, "to" AS shown, basis FROM '{G}/same_work.parquet' ORDER BY shown""")
    else:
        db.execute("CREATE TABLE sw (hidden VARCHAR, shown VARCHAR, basis VARCHAR)")
    # fetched chapters the name-only loader folded into their keyed twin in the same volume (never nodes; 2026-11-13,
    # data/graph/name-only/chapter-twins.csv.gz): a request for the chapter's DOI shows the keyed work
    tw = ROOT / 'data/graph/name-only/chapter-twins.csv.gz'
    if tw.exists():
        db.execute(f"""CREATE TABLE twin AS SELECT DISTINCT id, keyed_work, doi FROM read_csv('{tw}', all_varchar=true)
                       WHERE id IS NOT NULL AND id <> '' ORDER BY id""")
    else:
        db.execute("CREATE TABLE twin (id VARCHAR, keyed_work VARCHAR, doi VARCHAR)")
    db.execute(f"""CREATE TABLE work_w AS SELECT w.key,
        coalesce(c.n, 0) AS cited, coalesce(r.n, 0) AS reviewed
        FROM '{G}/work.parquet' w
        LEFT JOIN (SELECT k, count(DISTINCT f) n FROM (SELECT "to" k, "from" f FROM e_cites_t
                   UNION ALL SELECT sw.shown, c."from" FROM sw JOIN e_cites_t c ON c."to" = sw.hidden) GROUP BY 1) c ON c.k = w.key
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
    # variant_titles (2026-11-14): other titles of the work kept by a merge (list in work.parquet), shown as one line
    wsql = {'variant_titles': "array_to_string(w.variant_titles, ' | ') AS variant_titles"}
    wx = ', '.join([(wsql.get(c) or f'w.{c}') if c in wcols else f'NULL::VARCHAR AS {c}' for c in WORK_ADDED]
                   + [f'w.{c}' if c in wcols else f'NULL::INTEGER AS {c}' for c in WORK_ADDED_INT])
    nx = ', '.join([f'NULL::VARCHAR AS {c}' for c in WORK_ADDED] + [f'NULL::INTEGER AS {c}' for c in WORK_ADDED_INT])
    # prizes (2026-11-12): kind = the honours most rows give, year = first year, journal = the awarding body
    prize_sql = (f"""UNION ALL SELECT z.key, 'prize', z.label || CASE WHEN z.shown THEN '' ELSE ' (Wikidata honour)' END,
               z.honours, z.first_year, z.body, 'unkeyed', CASE WHEN z.wd IS NULL THEN []::VARCHAR[] ELSE ['wd:' || z.wd] END,
               z.rows, NULL, NULL, NULL, {nx} FROM '{G}/prize.parquet' z""" if (G / 'prize.parquet').exists() else '')
    # places (2026-11-18, scripts/graph_places.py): kind = the place's kind, journal = its country, weight = works about it
    place_sql = (f"""UNION ALL SELECT z.key, 'place', z.label, z.kind, NULL, (SELECT label FROM '{G}/place.parquet' c WHERE c.key = 'place:' || z.country),
               'derived', ['wd:' || z.qid] || CASE WHEN z.lc_id IS NULL THEN []::VARCHAR[] ELSE [CASE WHEN starts_with(z.lc_id, 'sh') THEN 'lcsh:' ELSE 'lcnaf:' END || z.lc_id] END,
               z.works, z.works, NULL, NULL, {nx} FROM '{G}/place.parquet' z""" if (G / 'place.parquet').exists() else '')
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
        {place_sql}
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
    if (G / 'place.parquet').exists():
        # a place's own record, the descendants a 'with places within it' search adds (containment, wider regions over the
        # places they contain), and its period polities (always searched with the territory: British Ceylon -> Sri Lanka)
        db.execute(f"""CREATE TABLE place AS SELECT * FROM '{G}/place.parquet' ORDER BY key""")
        db.execute("""CREATE TABLE place_desc AS WITH RECURSIVE d(anc, des, depth) AS (
              SELECT "to", "from", 1 FROM e_place_in_t WHERE basis IN ('lc-qualifier', 'wd-p131', 'wd-country', 'region-contains (wd-p131)')
                 OR basis LIKE 'period-of%'
              UNION SELECT d.anc, e."from", d.depth + 1 FROM d JOIN e_place_in_t e ON e."to" = d.des
              WHERE d.depth < 6 AND (e.basis IN ('lc-qualifier', 'wd-p131', 'wd-country') OR e.basis LIKE 'period-of%'))
            SELECT anc, des, min(depth) AS depth FROM d WHERE anc <> des GROUP BY 1, 2 ORDER BY anc""")
        db.execute("""CREATE TABLE place_period AS SELECT "to" AS territory, "from" AS period FROM e_place_in_t
                      WHERE basis LIKE 'period-of%' ORDER BY territory""")
        # pw (2026-11-18, for sub-second place pages): one row per (place, work) for the place with its period polities
        # (pscope self) and for the places within it (pscope desc), with the evidence classes, fiction-only flag, kind, year,
        # weight and whether the work has a linked author or a catalogued one
        db.execute("""CREATE TABLE pmap AS SELECT key AS place, key AS member, 'self' AS pscope FROM place
              UNION ALL SELECT territory, period, 'self' FROM place_period
              UNION ALL SELECT d.anc, d.des, 'desc' FROM place_desc d
                        WHERE NOT EXISTS (SELECT 1 FROM place_period p WHERE p.territory = d.anc AND p.period = d.des)
              ORDER BY place""")
        db.execute("""CREATE TEMP TABLE au_any AS SELECT DISTINCT "to" w FROM e_authored_t UNION SELECT DISTINCT "to" FROM e_edited_t""")
        has_pa = (G / 'printed_author.parquet').exists()
        if has_pa:
            db.execute(f"""CREATE TABLE printed AS SELECT * FROM '{G}/printed_author.parquet' ORDER BY work""")
        db.execute(f"""CREATE TABLE pw AS SELECT g.place, g.pscope, g.work, g.lc, g.title, g.review, g.fiction,
                  coalesce(n.kind, 'other') AS kind, n.year, coalesce(n.weight, 0) AS weight, (u.w IS NOT NULL) AS has_author,
                  {'(pr.work IS NOT NULL)' if has_pa else 'false'} AS has_printed
              FROM (SELECT m.place, CASE WHEN bool_or(m.pscope = 'self') THEN 'self' ELSE 'desc' END AS pscope, t."from" AS work,
                       bool_or(starts_with(t.source, 'lc-')) AS lc, bool_or(starts_with(t.source, 'title')) AS title,
                       bool_or(t.source = 'review-of') AS review, bool_and(t.confidence = 'lc-fiction') AS fiction
                    FROM pmap m JOIN e_about_place_t t ON t."to" = m.member GROUP BY m.place, t."from") g
              JOIN nodes n ON n.key = g.work LEFT JOIN au_any u ON u.w = g.work
              {'LEFT JOIN (SELECT DISTINCT work FROM printed) pr ON pr.work = g.work' if has_pa else ''}
              ORDER BY g.place, g.pscope""")
        # an optional people filter, labelled plainly (never 'historians'): a thesis in the corpus, a supervision, a
        # review, an AHA PhD record, or an article in the JSTOR history set or the Crossref history-journal set
        db.execute("""CREATE TABLE hist_person AS SELECT DISTINCT p AS key FROM (
              SELECT a."from" p FROM e_authored_t a JOIN nodes w ON w.key = a."to" WHERE w.kind = 'thesis'
              UNION SELECT "from" FROM e_supervised_f UNION SELECT "from" FROM e_reviewed_f
              UNION SELECT a."from" FROM e_authored_t a JOIN (SELECT DISTINCT "from" w FROM e_cites_f
                     WHERE source LIKE '%jstor%' OR source LIKE '%crossref%') c ON c.w = a."to"
              UNION SELECT key FROM (SELECT key, unnest(anchors) a FROM nodes WHERE type = 'person') WHERE a LIKE 'aha-phd:%')
              ORDER BY 1""")
        db.execute("""CREATE TABLE place_names AS SELECT DISTINCT key, strip_accents(lower(unnest(variants))) AS name, works
                      FROM place ORDER BY name""")
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
    if key.startswith('place:'):
        return 'place'
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


# ---- places (2026-11-18) ----------------------------------------------------------------------------------------
CONTAIN = "('lc-qualifier', 'wd-p131', 'wd-country', 'region-contains (wd-p131)')"
# a work's tag as one badge and a line: LC subject heading, title (hand-checked / rule), review of a book about the place
SRC_BADGE = ("CASE WHEN bool_or(starts_with(a.source, 'lc-')) THEN 'LC' WHEN bool_or(a.source = 'title-checked') THEN 'title (read)' "
             "WHEN bool_or(a.source = 'title-rule') THEN 'title (rule)' WHEN bool_or(a.source = 'title-read-sol') THEN 'title (read)' "
             "WHEN bool_or(a.source = 'title-name') THEN 'title (name)' "
             "ELSE 'review' END")
SRC_LINE = ("string_agg(DISTINCT CASE WHEN starts_with(a.source, 'lc-') THEN 'LC subject: ' || a.heading "
            "|| CASE a.confidence WHEN 'lc-fiction' THEN ' (setting of fiction)' WHEN 'lc-sol' THEN ' (heading grounded by an outside reviewer, audited)' ELSE '' END "
            "WHEN a.source = 'title-checked' THEN 'title, read by hand' WHEN a.source = 'title-rule' THEN 'title: ' || a.heading "
            "WHEN a.source = 'title-read-sol' THEN 'title, read by an outside reviewer (audited)' "
            "WHEN a.source = 'title-name' THEN a.heading || ' (place name in the title, measured against LC headings' "
            "|| CASE a.confidence WHEN 'title-name:low-support' THEN '; low-support tier' ELSE '' END || ')' "
            "ELSE 'review of a book about the place' END "
            "|| CASE WHEN a.\"to\" <> $k THEN ' [' || (SELECT label FROM place WHERE key = a.\"to\") || ']' ELSE '' END, '; ')")
PLACE_OPTS = {'children': ('0', '1'), 'source': ('', 'lc', 'title', 'review')}


def place_set(opts):
    """SQL for the place keys a place page covers: the place, its period polities, and (toggle) the places within it."""
    kids = 'UNION SELECT des FROM place_desc WHERE anc = $k' if opts.get('children') == '1' else ''
    return f'(SELECT $k UNION SELECT period FROM place_period WHERE territory = $k {kids})'


def work_filter(opts, alias='w'):
    """Kind, decade and source filters of a place page, as SQL over the work node `alias` and the tag `a`."""
    out = []
    if re.fullmatch(r'[a-z_]+', opts.get('kind') or ''):
        out.append(f"coalesce({alias}.kind, 'other') = '{opts['kind']}'")
    if re.fullmatch(r'\d{4}', opts.get('decade') or ''):
        d = int(opts['decade'])
        out.append(f'{alias}.year BETWEEN {d} AND {d + 9}')
    elif opts.get('decade') == 'none':
        out.append(f'{alias}.year IS NULL')
    if opts.get('fiction') != '1':     # LC tags that give the setting of a work of fiction ($v Fiction) are left out
        out.append("a.confidence <> 'lc-fiction'")       # unless asked for (&fiction=1; demo default, 2026-11-18)
    src = opts.get('source') or ''
    if src == 'lc':
        out.append("starts_with(a.source, 'lc-')")
    elif src == 'title':
        out.append("starts_with(a.source, 'title')")
    elif src == 'review':
        out.append("a.source = 'review-of'")
    return (' AND ' + ' AND '.join(out)) if out else ''


def pw_where(opts, alias='x'):
    """The precomputed place-work table `pw` (explorer build) filtered for a place page: the place and its period polities
    (pscope self), with the places within it on the toggle (pscope desc); kind, decade, evidence; fiction settings left
    out unless &fiction=1."""
    out = [f'{alias}.place = $k']
    if opts.get('children') != '1':
        out.append(f"{alias}.pscope = 'self'")
    if re.fullmatch(r'[a-z_]+', opts.get('kind') or ''):
        out.append(f"{alias}.kind = '{opts['kind']}'")
    if re.fullmatch(r'\d{4}', opts.get('decade') or ''):
        d = int(opts['decade'])
        out.append(f'{alias}.year BETWEEN {d} AND {d + 9}')
    elif opts.get('decade') == 'none':
        out.append(f'{alias}.year IS NULL')
    if opts.get('source') in ('lc', 'title', 'review'):
        out.append(f"{alias}.{opts['source']}")
    if opts.get('fiction') != '1':
        out.append(f'NOT {alias}.fiction')
    return ' AND '.join(out)


HIST_LABEL = 'people with a history thesis, history-journal article or review in the graph'


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

    def has_table(self, name):
        self.has('')
        return name in self._tables

    def cur(self):
        if not hasattr(self.local, 'c'):
            self.local.c = self.db.cursor()
        return self.local.c

    def group_sql(self, rel, key):
        """SQL yielding (other_key, n, detail) rows for one relation of one node."""
        rid, _, table, me, other, detail = rel[:6]
        where = f' AND {rel[6]}' if len(rel) > 6 else ''
        opts = getattr(self.local, 'opts', None) or {}
        if rid == 'places':                 # a work's places, or the places of a person's works (derived)
            if not self.has('about_place'):
                return 'SELECT NULL k, 0 n, NULL d, 0 lk WHERE false'
            if node_type(key) == 'work':
                return (f"""SELECT a."to" k, 1 n, {SRC_BADGE} || '|' || {SRC_LINE.replace('$k', 'a."to"')} d, 0 lk
                           FROM e_about_place_f a WHERE a."from" = $k GROUP BY 1""")
            return (f"""SELECT a."to" k, count(DISTINCT a."from") n, count(DISTINCT a."from") || ' of their works: '
                       || string_agg(DISTINCT left(w.label, 70), '; ') d, 0 lk
                       FROM (SELECT DISTINCT "to" FROM e_authored_f WHERE "from" = $k AND coalesce(role, 'author') NOT IN {EDITION_ROLES}) au
                       JOIN e_about_place_f a ON a."from" = au."to" JOIN nodes w ON w.key = a."from" GROUP BY 1""")
        if rid in ('about', 'people', 'wider'):
            ps = place_set(opts)
            if rid == 'wider':              # works about the regions that contain it, not already on the page
                ps = f"""(SELECT "to" FROM e_place_in_f WHERE "from" = $k AND basis LIKE 'region-contains%')"""
                own = f'AND a."from" NOT IN (SELECT "from" FROM e_about_place_t WHERE "to" IN {place_set(dict(children="1"))})'
            else:
                own = ''
            wf = work_filter(opts)
            if rid in ('about', 'wider'):
                return (f"""SELECT a."from" k, 1 n, {SRC_BADGE} || '|' || {SRC_LINE} d, 0 lk
                           FROM e_about_place_t a JOIN nodes w ON w.key = a."from" WHERE a."to" IN {ps} {own} {wf} GROUP BY 1""")
            return (f"""WITH ws AS (SELECT DISTINCT a."from" AS work FROM e_about_place_t a JOIN nodes w ON w.key = a."from"
                                   WHERE a."to" IN {ps} {wf})
                       SELECT au."from" k, count(DISTINCT au."to") n, count(DISTINCT au."to") || CASE WHEN count(DISTINCT au."to") = 1
                              THEN ' work' ELSE ' works' END || ' about the place'
                              || CASE WHEN bool_and(au.evidence = 'linked') THEN ' (linked author credits)' ELSE '' END d,
                              bool_and(au.evidence = 'linked')::INT lk
                       FROM ws JOIN e_authored_t au ON au."to" = ws.work
                       WHERE coalesce(au.role, 'author') NOT IN {EDITION_ROLES} GROUP BY 1""")
        if rid in ('periods', 'parents', 'children', 'overlaps'):
            if not self.has('place_in'):
                return 'SELECT NULL k, 0 n, NULL d, 0 lk WHERE false'
            basis_d = ("CASE WHEN basis LIKE 'period-of%' THEN 'period polity' WHEN basis LIKE 'region-contains%' THEN 'wider region' "
                       "WHEN basis LIKE 'overlaps%' THEN 'crosses the border' WHEN basis = 'part-predecessor' THEN 'former unit, partly succeeded' "
                       "ELSE 'within' END || ' (' || basis || ')'")
            if rid == 'periods':
                q = f"SELECT \"from\" k, 1 n, {basis_d} d FROM e_place_in_t WHERE \"to\" = $k AND basis LIKE 'period-of%'"
            elif rid == 'parents':
                q = (f"SELECT \"to\" k, 1 n, {basis_d} d FROM e_place_in_f WHERE \"from\" = $k "
                     f"AND (basis IN {CONTAIN} OR basis LIKE 'period-of%')")
            elif rid == 'children':
                q = f"SELECT \"from\" k, 1 n, {basis_d} d FROM e_place_in_t WHERE \"to\" = $k AND basis IN {CONTAIN}"
            else:
                q = (f"SELECT \"to\" k, 1 n, {basis_d} d FROM e_place_in_f WHERE \"from\" = $k AND (basis LIKE 'overlaps%' OR basis = 'part-predecessor') "
                     f"UNION SELECT \"from\", 1, {basis_d} FROM e_place_in_t WHERE \"to\" = $k AND (basis LIKE 'overlaps%' OR basis = 'part-predecessor')")
            return f'SELECT k, n, d, 0 lk FROM ({q})'
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
                        SELECT "from", "to", evidence, state, source, score, role, role_basis FROM e_authored_{side}
                         WHERE "{me}" = $k AND role IN {EDITION_ROLES}
                        UNION ALL SELECT "from", "to", evidence, state, source, score, role, role_basis FROM e_edited_{side}
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
            return (f'''SELECT "{other}" k, count(*) n, string_agg(CASE kind WHEN 'education' THEN 'education: '
                        WHEN 'position' THEN 'position: ' ELSE '' END || CASE source WHEN 'aha_directory' THEN 'AHA directory'
                        WHEN 'aha_advisor' THEN 'advised PhDs' WHEN 'ihr' THEN 'IHR staff list' WHEN 'orcid' THEN 'ORCID'
                        WHEN 'wikidata' THEN 'Wikidata' WHEN 'review_credit' THEN 'review credit'
                        WHEN 'jstor_signature' THEN 'JSTOR review signature' WHEN 'lc_373' THEN 'LC authority' ELSE source END
                        || CASE WHEN source IN ('orcid', 'wikidata') AND coalesce(rank, '') <> ''
                                THEN ' (' || left(rank, 80) || ')' ELSE '' END
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
        if rid == 'cited_by':             # a work's citing works, with those citing its other key (SAME_WORK hidden)
            return (f"""SELECT e."from" k, 1 n, concat_ws(' · ', {EDITION_D}, CASE WHEN bool_and(e."to" <> $k)
                        THEN 'cites it as ' || any_value(e."to") END) d, 0 lk
                        FROM e_cites_t e WHERE e."to" = $k OR e."to" IN (SELECT hidden FROM sw WHERE shown = $k) GROUP BY 1""")
        if rid == 'cited_by_people':      # people whose works cite this person's works (key-log and linked authors)
            return (f"""SELECT a2."from" k, count(DISTINCT c."from") n, count(DISTINCT c."from") || ' citing works'
                       || CASE WHEN bool_and(a2.evidence = 'linked') THEN ' (linked author credit)' ELSE '' END d,
                       bool_and(a2.evidence = 'linked')::INT lk
                       FROM (SELECT "to" FROM e_authored_f WHERE "from" = $k AND coalesce(role, 'author') NOT IN {EDITION_ROLES}
                             UNION SELECT sw.hidden FROM e_authored_f x JOIN sw ON sw.shown = x."to"
                             WHERE x."from" = $k AND coalesce(x.role, 'author') NOT IN {EDITION_ROLES}) a
                       JOIN e_cites_t c ON c."to" = a."to" JOIN e_authored_t a2 ON a2."to" = c."from"
                       WHERE a2."from" <> $k GROUP BY 1""")
        if rid == 'cited_by_works':       # distinct citing documents (theses, articles), not people
            return (f"""SELECT c."from" k, count(DISTINCT a."to") n, count(DISTINCT a."to") || ' of this person''s works cited' d
                       FROM (SELECT DISTINCT coalesce(sw.shown, x."to") "to", x."to" AS held FROM (
                               SELECT "to" FROM e_authored_f WHERE "from" = $k AND coalesce(role, 'author') NOT IN {EDITION_ROLES}
                               UNION SELECT sw.hidden FROM e_authored_f y JOIN sw ON sw.shown = y."to"
                               WHERE y."from" = $k AND coalesce(y.role, 'author') NOT IN {EDITION_ROLES}) x
                             LEFT JOIN sw ON sw.hidden = x."to" AND sw.shown IN (SELECT "to" FROM e_authored_f WHERE "from" = $k)) a
                       JOIN e_cites_t c ON c."to" = a.held GROUP BY 1""")
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
        if node_type(key) == 'place' and rel[0] in ('about', 'people', 'wider', 'catalogued') and self.has_table('pw'):
            return self.place_group(key, rel[0], offset, limit, sort, getattr(self.local, 'opts', None) or {})
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
        items = [item(r[:-2]) for r in rows]
        if rel[0] == 'people' and node_type(key) == 'place' and items:
            # each person's works about the place, as evidence (expandable on the page)
            opts = getattr(self.local, 'opts', None) or {}
            ws = self.cur().execute(f"""SELECT au."from", w.key, w.label, w.year, w.kind,
                       {SRC_BADGE} AS badge FROM e_about_place_t a JOIN nodes w ON w.key = a."from"
                       JOIN e_authored_t au ON au."to" = a."from"
                       WHERE a."to" IN {place_set(opts)} {work_filter(opts)} AND au."from" IN (SELECT unnest($p))
                         AND coalesce(au.role, 'author') NOT IN {EDITION_ROLES}
                       GROUP BY ALL ORDER BY w.year NULLS LAST""".replace('GROUP BY ALL', 'GROUP BY au."from", w.key, w.label, w.year, w.kind'),
                       dict(k=key, p=[i['key'] for i in items])).fetchall()
            by = {}
            for pk, wk, wl, wy, wkind, badge in ws:
                by.setdefault(pk, []).append(dict(key=wk, label=wl, year=wy, kind=wkind, source=badge))
            for i in items:
                i['works'] = by.get(i['key'], [])[:40]
        return items, total

    def place_group(self, key, rid, offset, limit, sort, opts):
        """Place-page lists from the precomputed table pw (2026-11-18, under a second): works, people (derived from their
        works), catalogued authors not yet in the people index, and the wider-region band."""
        c, lim = self.cur(), f'LIMIT {int(limit)} OFFSET {int(offset)}'
        where = pw_where(opts)
        self.local.last_linked = 0
        if rid in ('about', 'wider'):
            if rid == 'wider':
                where = (pw_where(dict(opts, children='0')).replace('x.place = $k', """x.place IN (SELECT "to" FROM e_place_in_f
                         WHERE "from" = $k AND basis LIKE 'region-contains%')""")
                         + " AND x.work NOT IN (SELECT work FROM pw WHERE place = $k)")
            order = 'x.year DESC NULLS LAST, x.weight DESC' if sort == 'year' else 'x.weight DESC, x.year DESC NULLS LAST'
            rows = c.execute(f"""SELECT DISTINCT x.work, x.weight, x.year, count(*) OVER () FROM (SELECT DISTINCT work, weight, year FROM pw x
                                 WHERE {where}) x ORDER BY {order}, x.work {lim}""", dict(k=key)).fetchall()
            total = rows[0][3] if rows else (0 if offset == 0 else None)
            keys = [r[0] for r in rows]
            members = ("(SELECT \"to\" FROM e_place_in_f WHERE \"from\" = $k AND basis LIKE 'region-contains%')" if rid == 'wider' else
                       f"(SELECT member FROM pmap WHERE place = $k {'' if opts.get('children') == '1' else "AND pscope = 'self'"})")
            det = dict(c.execute(f"""SELECT a."from", {SRC_BADGE} || '|' || {SRC_LINE}
                                     FROM e_about_place_t a WHERE a."from" IN (SELECT unnest($w)) AND a."to" IN {members}
                                     GROUP BY 1""", dict(w=keys, k=key)).fetchall())
            cat = dict(c.execute("""SELECT work, coalesce(nullif(printed, ''), heading) FROM printed WHERE work IN (SELECT unnest($w))""",
                                 dict(w=keys)).fetchall()) if self.has_table('printed') else {}
            nodes = {r[0]: r for r in c.execute(f"""SELECT {ITEM_COLS.replace('o.', '')}, NULL, NULL FROM nodes WHERE key IN (SELECT unnest($w))""",
                                                dict(w=keys)).fetchall()}
            items = []
            for k in keys:
                it = item(nodes[k])
                it['n'] = 1
                d = det.get(k, '')
                if k in cat:
                    d += ' · author as catalogued (not linked): ' + cat[k]
                it['detail'] = d
                items.append(it)
            return items, total
        if rid == 'people':
            hist = 'AND au."from" IN (SELECT key FROM hist_person)' if opts.get('hist') == '1' else ''
            rows = c.execute(f"""WITH g AS (SELECT au."from" k, count(DISTINCT x.work) n, bool_and(au.evidence = 'linked') lk
                                   FROM pw x JOIN e_authored_t au ON au."to" = x.work
                                   WHERE {where} AND coalesce(au.role, 'author') NOT IN {EDITION_ROLES} {hist} GROUP BY 1)
                                 SELECT {ITEM_COLS}, g.n, g.n || CASE WHEN g.n = 1 THEN ' work' ELSE ' works' END || ' about the place'
                                        || CASE WHEN g.lk THEN ' (linked author credits)' ELSE '' END,
                                        count(*) OVER (), sum(g.lk::INT) OVER (), (g.k IN (SELECT key FROM hist_person))
                                 FROM g JOIN nodes o ON o.key = g.k ORDER BY g.n DESC, o.weight DESC, o.key {lim}""", dict(k=key)).fetchall()
            total = rows[0][-3] if rows else (0 if offset == 0 else None)
            self.local.last_linked = int(rows[0][-2] or 0) if rows else 0
            items = []
            for r in rows:
                it = item(r[:-3])
                it['hist'] = bool(r[-1])
                items.append(it)
            if items:
                ws = c.execute(f"""SELECT au."from", w.key, w.label, w.year, w.kind, CASE WHEN x.lc THEN 'LC' WHEN x.title THEN 'title'
                                   ELSE 'review' END FROM pw x JOIN e_authored_t au ON au."to" = x.work JOIN nodes w ON w.key = x.work
                                   WHERE {where} AND au."from" IN (SELECT unnest($p)) AND coalesce(au.role, 'author') NOT IN {EDITION_ROLES}
                                   ORDER BY w.year NULLS LAST""", dict(k=key, p=[i['key'] for i in items])).fetchall()
                by = {}
                for pk, wk, wl, wy, wkind, badge in ws:
                    lst = by.setdefault(pk, [])
                    if all(x['key'] != wk for x in lst):
                        lst.append(dict(key=wk, label=wl, year=wy, kind=wkind, source=badge))
                for i in items:
                    i['works'] = by.get(i['key'], [])[:40]
            return items, total
        # catalogued authors not yet in the people index: LC main entries of works with no linked author
        if not self.has_table('printed'):
            return [], 0
        rows = c.execute(f"""WITH g AS (SELECT coalesce(p.lcnaf, 'heading:' || p.heading) gk, any_value(p.heading) heading,
                                   any_value(p.lcnaf) lcnaf, any_value(p.state) state, count(DISTINCT x.work) n, list(DISTINCT x.work) works
                                   FROM pw x JOIN printed p ON p.work = x.work WHERE {where} GROUP BY 1)
                             SELECT gk, heading, lcnaf, state, n, works, count(*) OVER () FROM g ORDER BY n DESC, heading {lim}""",
                         dict(k=key)).fetchall()
        total = rows[0][-1] if rows else (0 if offset == 0 else None)
        wl = {r[0]: r for r in c.execute("SELECT key, label, year, kind FROM nodes WHERE key IN (SELECT unnest($w))",
                                          dict(w=[w for r in rows for w in r[5][:40]])).fetchall()}
        items = []
        for gk, heading, lcnaf, state, n, works, _ in rows:
            items.append(dict(key=None, type='catalogued', kind=None, label=(heading or '').rstrip(' .'), year=None, weight=n,
                              resolution=None, kind_proposed=None, n=n, lcnaf=lcnaf, state=state,
                              detail=f"{n} work{'s' if n != 1 else ''} about the place; LC main entry"
                                     + (f' (LC authority {lcnaf}' + ('' if state != 'on-key' else ', on a person key: credit pending') + ')' if lcnaf else ', no LC authority found'),
                              works=sorted([dict(key=w, label=wl[w][1], year=wl[w][2], kind=wl[w][3], source='LC') for w in works[:40] if w in wl],
                                           key=lambda x: x['year'] or 0)))
        return items, total

    def place_summary(self, key, opts):
        """Header facts of a place page from pw: identifiers, period of, counts (the place with its period polities; with
        the places within it; works with no linked author; fiction settings left out), and the filter breakdowns."""
        c = self.cur()
        r = c.execute("""SELECT qid, kind, lc_id, lc_heading, (SELECT label FROM place x WHERE x.key = 'place:' || p.country),
                            period_of, (SELECT label FROM place x WHERE x.key = 'place:' || p.period_of), variants, sitelinks
                            FROM place p WHERE key = ?""", [key]).fetchone()
        out = dict(zip(['qid', 'place_kind', 'lc_id', 'lc_heading', 'country', 'period_of', 'period_of_label', 'variants',
                        'sitelinks'], r))
        out['variants'] = (out['variants'] or [])[:30]
        fic = '' if opts.get('fiction') == '1' else 'AND NOT fiction'
        cnt = c.execute(f"""SELECT count(DISTINCT work) FILTER (WHERE pscope = 'self' {fic}),
                   count(DISTINCT work) FILTER (WHERE pscope = 'self' AND NOT has_author {fic}),
                   count(DISTINCT work) FILTER (WHERE true {fic}), count(DISTINCT work) FILTER (WHERE NOT has_author {fic}),
                   count(DISTINCT work) FILTER (WHERE fiction AND pscope = 'self'),
                   count(DISTINCT work) FILTER (WHERE pscope = 'self' AND NOT has_author AND has_printed {fic})
                   FROM pw WHERE place = $k""", dict(k=key)).fetchone()
        (out['works'], out['works_no_author'], out['works_with_children'], out['works_with_children_no_author'],
         out['works_fiction'], out['works_catalogued_author']) = cnt
        out['children_places'] = c.execute('SELECT count(*) FROM place_desc WHERE anc = ?', [key]).fetchone()[0]
        w0 = pw_where(dict(children=opts.get('children'), fiction=opts.get('fiction')))
        out['by_kind'] = c.execute(f"SELECT kind, count(DISTINCT work) FROM pw x WHERE {w0} GROUP BY 1 ORDER BY 2 DESC", dict(k=key)).fetchall()
        out['by_decade'] = c.execute(f"""SELECT CASE WHEN year IS NULL THEN 'none' ELSE (year // 10 * 10)::VARCHAR END d, count(DISTINCT work)
                                         FROM pw x WHERE {w0} GROUP BY 1 ORDER BY 1""", dict(k=key)).fetchall()
        out['by_source'] = [(s, c.execute(f'SELECT count(DISTINCT work) FROM pw x WHERE {w0} AND x.{s}', dict(k=key)).fetchone()[0])
                            for s in ('lc', 'title', 'review')]
        out['wider'] = c.execute("""SELECT p.key, p.label, (SELECT count(DISTINCT work) FROM pw WHERE pw.place = p.key AND pscope = 'self' AND NOT fiction)
                       FROM e_place_in_f r JOIN place p ON p.key = r."to" WHERE r."from" = $k AND r.basis LIKE 'region-contains%'
                       ORDER BY 3 DESC""", dict(k=key)).fetchall()
        out['hist_label'] = HIST_LABEL
        out['opts'] = opts
        return out

    def place_summary_old(self, key, opts):
        """Header facts of a place page: identifiers, period of, counts (direct, with places within, without a linked
        author, wider region), and the works by kind, decade and source for the filters."""
        c = self.cur()
        r = c.execute("""SELECT qid, kind, lc_id, lc_heading, (SELECT label FROM place x WHERE x.key = 'place:' || p.country),
                            period_of, (SELECT label FROM place x WHERE x.key = 'place:' || p.period_of), variants, sitelinks
                            FROM place p WHERE key = ?""", [key]).fetchone()
        out = dict(zip(['qid', 'place_kind', 'lc_id', 'lc_heading', 'country', 'period_of', 'period_of_label', 'variants',
                        'sitelinks'], r))
        out['variants'] = (out['variants'] or [])[:30]

        def cnt(ps, extra=''):
            return c.execute(f'''SELECT count(DISTINCT a."from"),
                       count(DISTINCT a."from") FILTER (WHERE NOT EXISTS (SELECT 1 FROM e_authored_t au WHERE au."to" = a."from")
                                                            AND NOT EXISTS (SELECT 1 FROM e_edited_t ed WHERE ed."to" = a."from"))
                       FROM e_about_place_t a JOIN nodes w ON w.key = a."from" WHERE a."to" IN {ps} {extra}''', dict(k=key)).fetchone()
        out['works'], out['works_no_author'] = cnt(place_set({}))
        out['works_with_children'], out['works_with_children_no_author'] = cnt(place_set(dict(children='1')))
        out['children_places'] = c.execute('SELECT count(*) FROM place_desc WHERE anc = ?', [key]).fetchone()[0]
        ps = place_set(opts)
        out['by_kind'] = c.execute(f'''SELECT coalesce(w.kind, 'other'), count(DISTINCT a."from") FROM e_about_place_t a
                       JOIN nodes w ON w.key = a."from" WHERE a."to" IN {ps} GROUP BY 1 ORDER BY 2 DESC''', dict(k=key)).fetchall()
        out['by_decade'] = c.execute(f'''SELECT CASE WHEN w.year IS NULL THEN 'none' ELSE (w.year // 10 * 10)::VARCHAR END d,
                       count(DISTINCT a."from") FROM e_about_place_t a JOIN nodes w ON w.key = a."from" WHERE a."to" IN {ps}
                       GROUP BY 1 ORDER BY 1''', dict(k=key)).fetchall()
        out['by_source'] = c.execute(f'''SELECT CASE WHEN starts_with(a.source, 'lc-') THEN 'lc' WHEN starts_with(a.source, 'title')
                       THEN 'title' ELSE 'review' END, count(DISTINCT a."from") FROM e_about_place_t a WHERE a."to" IN {ps}
                       GROUP BY 1 ORDER BY 2 DESC''', dict(k=key)).fetchall()
        out['wider'] = c.execute(f'''SELECT p.key, p.label, count(DISTINCT a."from") FROM e_place_in_f r JOIN place p ON p.key = r."to"
                       LEFT JOIN e_about_place_t a ON a."to" = r."to" WHERE r."from" = $k AND r.basis LIKE 'region-contains%'
                       GROUP BY 1, 2 ORDER BY 3 DESC''', dict(k=key)).fetchall()
        out['opts'] = opts
        return out

    # shared frames for a comparison of two places (2026-11-18): subject words in the LC headings and titles of the works
    FRAMES = [
        ('empire, colonies, Commonwealth', r'(?i)\b(colon(y|ies|ial)|imperial|empire|commonwealth|dominion)'),
        ('plantations, tea, coffee, sugar', r'(?i)\b(plantation|tea\b|coffee|sugar|cinnamon|rubber)'),
        ('migration, settlement, diaspora', r'(?i)(emigration|immigra|migra|diaspora|settler|land settlement)'),
        ('missions, missionaries', r'(?i)\bmission(s|ar)'),
        ('railways', r'(?i)(railroad|railway)'),
        ('census, statistics, population', r'(?i)(census|statistic|population)'),
        ('education, schools', r'(?i)(education|school)'),
        ('medicine, public health', r'(?i)(medic|health|disease|hospital)'),
        ('agriculture, land', r'(?i)(agricultur|farm|land tenure|peasant)'),
        ('trade, commerce', r'(?i)\b(trade|commerce|merchant)'),
        ('politics, government', r'(?i)(politics and government|political|parliament|elections)'),
        ('women, gender', r'(?i)\b(women|gender)'),
        ('war, military', r'(?i)\b(war|military|army|navy)\b'),
    ]

    def compare(self, a, b, opts, limit=40):
        """Two places side by side (the Ceylon-Canada connection): people with works about both, works tagged to both,
        citations between the two sets, and the shared frames in the LC headings and titles of each set. Counts first."""
        c = self.cur()
        wa, wb = pw_where(opts).replace('$k', '$a'), pw_where(opts).replace('$k', '$b')
        c.execute(f'''CREATE OR REPLACE TEMP TABLE cmp_w AS
            SELECT DISTINCT 'a' AS side, x.work FROM pw x WHERE {wa}
            UNION SELECT DISTINCT 'b', x.work FROM pw x WHERE {wb}''', dict(a=a, b=b))
        c.execute(f'''CREATE OR REPLACE TEMP TABLE cmp_p AS SELECT au."from" AS person, w.side, au."to" AS work FROM cmp_w w
            JOIN e_authored_t au ON au."to" = w.work WHERE coalesce(au.role, 'author') NOT IN {EDITION_ROLES}''')
        lab = dict(c.execute('SELECT key, label FROM nodes WHERE key IN (?, ?)', [a, b]).fetchall())
        out = dict(a=a, b=b, a_label=lab.get(a, a), b_label=lab.get(b, b), opts=opts)
        out['works_a'], out['works_b'], out['works_both'] = c.execute('''SELECT count(DISTINCT work) FILTER (WHERE side = 'a'),
            count(DISTINCT work) FILTER (WHERE side = 'b'), (SELECT count(*) FROM (SELECT work FROM cmp_w GROUP BY 1 HAVING count(DISTINCT side) = 2))
            FROM cmp_w''').fetchone()
        out['people_a'], out['people_b'] = c.execute('''SELECT count(DISTINCT person) FILTER (WHERE side = 'a'),
            count(DISTINCT person) FILTER (WHERE side = 'b') FROM cmp_p''').fetchone()
        both = c.execute(f'''SELECT p.person, n.label, count(DISTINCT p.work) FILTER (WHERE side = 'a') na,
                   count(DISTINCT p.work) FILTER (WHERE side = 'b') nb FROM cmp_p p JOIN nodes n ON n.key = p.person
                   GROUP BY 1, 2 HAVING count(DISTINCT side) = 2 ORDER BY least(na, nb) DESC, na + nb DESC, 2''').fetchall()
        out['people_both_total'] = len(both)
        works = {}
        for pk, wk, wl, wy, side in c.execute('''SELECT p.person, p.work, w.label, w.year, p.side FROM cmp_p p JOIN nodes w ON w.key = p.work
                   WHERE p.person IN (SELECT unnest($ps)) ORDER BY w.year NULLS LAST''', dict(ps=[x[0] for x in both[:limit]])).fetchall():
            works.setdefault(pk, {'a': [], 'b': []})[side].append(dict(key=wk, label=wl, year=wy))
        out['people_both'] = [dict(key=k, label=l, na=na, nb=nb, works=works.get(k, {'a': [], 'b': []})) for k, l, na, nb in both[:limit]]
        out['works_both_list'] = [dict(key=k, label=l, year=y, kind=kd) for k, l, y, kd in c.execute('''SELECT w.key, w.label, w.year, w.kind
                   FROM (SELECT work FROM cmp_w GROUP BY 1 HAVING count(DISTINCT side) = 2) x JOIN nodes w ON w.key = x.work
                   ORDER BY w.year NULLS LAST LIMIT 200''').fetchall()]
        cites = c.execute('''SELECT ca.side, ci."from", f.label, f.year, ci."to", t.label, t.year FROM cmp_w ca
                   JOIN e_cites_f ci ON ci."from" = ca.work JOIN cmp_w cb ON cb.work = ci."to" AND cb.side <> ca.side
                   JOIN nodes f ON f.key = ci."from" JOIN nodes t ON t.key = ci."to"
                   WHERE NOT EXISTS (SELECT 1 FROM cmp_w x WHERE x.work = ci."from" AND x.side <> ca.side)
                     AND NOT EXISTS (SELECT 1 FROM cmp_w y WHERE y.work = ci."to" AND y.side = ca.side)
                   ORDER BY f.year NULLS LAST''').fetchall()
        out['cites_a_to_b'] = sum(1 for r in cites if r[0] == 'a')
        out['cites_b_to_a'] = sum(1 for r in cites if r[0] == 'b')
        out['cites'] = [dict(direction=r[0] + '>' + ('b' if r[0] == 'a' else 'a'), citing=dict(key=r[1], label=r[2], year=r[3]),
                             cited=dict(key=r[4], label=r[5], year=r[6])) for r in cites[:200]]
        # frames: the subject words in the LC heading strings and the titles of each side's works
        texts = c.execute(f'''SELECT w.side, w.work, string_agg(DISTINCT coalesce(a.heading, ''), ' ; ') || ' ; ' || any_value(n.label)
                   FROM cmp_w w JOIN nodes n ON n.key = w.work LEFT JOIN e_about_place_f a ON a."from" = w.work GROUP BY 1, 2''').fetchall()
        frames = []
        for name, rx in self.FRAMES:
            r = re.compile(rx)
            na = sum(1 for sd, _, t in texts if sd == 'a' and r.search(t or ''))
            nb = sum(1 for sd, _, t in texts if sd == 'b' and r.search(t or ''))
            frames.append(dict(frame=name, a=na, b=nb,
                               a_share=round(100 * na / max(1, out['works_a']), 1), b_share=round(100 * nb / max(1, out['works_b']), 1)))
        out['frames'] = frames
        # works per decade on each side (a time profile)
        out['decades'] = [dict(decade=d, a=na, b=nb) for d, na, nb in c.execute('''SELECT (w.year // 10 * 10) d,
                   count(DISTINCT x.work) FILTER (WHERE x.side = 'a'), count(DISTINCT x.work) FILTER (WHERE x.side = 'b')
                   FROM cmp_w x JOIN nodes w ON w.key = x.work WHERE w.year BETWEEN 1500 AND 2030 GROUP BY 1 ORDER BY 1''').fetchall()]
        return out

    def node(self, key, limit=12, sort='weight'):
        # an unkeyed record of a keyed work (SAME_WORK hidden -> shown, class 11) is shown as the keyed work
        to = self.cur().execute("""SELECT sw.shown, sw.basis FROM sw JOIN nodes h ON h.key = sw.hidden AND h.resolution = 'unkeyed'
                                    JOIN nodes s ON s.key = sw.shown AND s.resolution <> 'unkeyed'
                                    WHERE sw.hidden = ? ORDER BY sw.shown LIMIT 1""", [key]).fetchone()
        if to:
            out = self.node(to[0], limit, sort)
            if out:
                out['node']['requested'] = key
                out['node']['requested_note'] = f'{key} is the same work, held as {to[0]} ({to[1]})'
                return out
        if self.has_table('twin'):
            tw = self.cur().execute("""SELECT t.keyed_work FROM twin t JOIN nodes n ON n.key = t.keyed_work
                                        WHERE t.id = ? AND NOT EXISTS (SELECT 1 FROM nodes x WHERE x.key = t.id) LIMIT 1""", [key]).fetchone()
            if tw:
                out = self.node(tw[0], limit, sort)
                if out:
                    out['node']['requested'] = key
                    out['node']['requested_note'] = (f'{key} is the same chapter, held as {tw[0]} (fetched record of a keyed '
                                                     'chapter in the same volume; its printed authors are read on the keyed chapter)')
                    return out
        r = self.cur().execute("""SELECT key, type, label, kind, year, journal, resolution, anchors, weight, works, cited, reviewed,
                                  kind_proposed, issn, journal_source, isbn, editors_printed,
                                  (SELECT note FROM vol_note WHERE vol_note.key = nodes.key),
                                  first_year, first_year_catalogue, first_year_basis, variant_titles
                                  FROM nodes WHERE key = ?""", [key]).fetchone()
        if not r:
            return None
        n = dict(zip(['key', 'type', 'label', 'kind', 'year', 'journal', 'resolution', 'anchors', 'weight', 'works',
                      'cited', 'reviewed', 'kind_proposed', 'issn', 'journal_source', 'isbn', 'editors_printed',
                      'in_volume', 'first_year', 'first_year_catalogue', 'first_year_basis', 'variant_titles'], r))
        n['ids'] = ids(n.pop('anchors'))
        if n['type'] == 'place':
            n['place'] = self.place_summary(key, getattr(self.local, 'opts', None) or {})
        if n['type'] == 'work' and self.has_table('printed'):   # author as catalogued (LC record; display only, not a link)
            pr = self.cur().execute('SELECT heading, printed, lcnaf, person, state FROM printed WHERE work = ?', [key]).fetchone()
            if pr:
                n['catalogued'] = dict(zip(['heading', 'printed', 'lcnaf', 'person', 'state'], pr))
        if n['type'] == 'work':          # identifiers of its other keys (SAME_WORK hidden), 'also held as'
            have = {(i['scheme'], i['value'].lower()) for i in n['ids']}
            for h, anc in self.cur().execute("""SELECT sw.hidden, n.anchors FROM sw JOIN nodes n ON n.key = sw.hidden
                                                WHERE sw.shown = ? ORDER BY 1""", [key]).fetchall():
                for i in ids(anc):
                    if (i['scheme'], i['value'].lower()) not in have and i['scheme'] in ('doi', 'openalex', 'lccn', 'isbn'):
                        have.add((i['scheme'], i['value'].lower()))
                        n['ids'].append(dict(i, also_held_as=h))
            if self.has_table('twin'):
                for tid, doi in self.cur().execute("SELECT id, doi FROM twin WHERE keyed_work = ? ORDER BY 1", [key]).fetchall():
                    if doi and ('doi', doi.lower()) not in have:
                        have.add(('doi', doi.lower()))
                        n['ids'].append(dict(scheme='doi', value=doi, url=f'https://doi.org/{doi}', also_held_as=tid))
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
        places = []
        if self.has_table('place_names') and not re.fullmatch(r'[pwi]-\d+', q):
            # a place by any of its names ('Ceylon' finds Sri Lanka through its period polities); exact names first
            ql = c.execute('SELECT strip_accents(lower(?))', [q]).fetchone()[0]
            places = [k for (k,) in c.execute("""SELECT key FROM (SELECT key, min(CASE WHEN name = $q THEN 0 ELSE 1 END) e, max(works) w
                         FROM place_names WHERE name = $q OR (length($q) >= 3 AND starts_with(name, $q)) GROUP BY 1)
                         ORDER BY e, w DESC LIMIT 6""", dict(q=ql)).fetchall()]
        if not hits:
            toks = [t for t in re.split(r'[\s,]+', c.execute('SELECT strip_accents(lower(?))', [q]).fetchone()[0]) if t]
            where = ' AND '.join('s LIKE ?' for _ in toks)
            args = [f'%{t}%' for t in toks]
            hits = [k for (k,) in c.execute(f"""(SELECT key FROM search WHERE type = 'person' AND {where} LIMIT {limit // 2})
                        UNION ALL (SELECT key FROM search WHERE type <> 'person' AND {where} LIMIT {limit // 2})""",
                                            args + args).fetchall()]
        hits = [h for h in hits if h not in places]
        if not hits and not places:
            return []
        rows = c.execute(f"""SELECT key, type, kind, label, year, weight, resolution, kind_proposed, NULL, NULL FROM nodes
                             WHERE key IN (SELECT unnest(?)) ORDER BY type = 'person' DESC, weight DESC""", [hits]).fetchall()
        prow = {r[0]: r for r in c.execute("""SELECT key, type, kind, label, year, weight, resolution, kind_proposed, NULL, NULL
                                                FROM nodes WHERE key IN (SELECT unnest(?))""", [places]).fetchall()}
        return [item(prow[k]) for k in places if k in prow] + [item(r) for r in rows]


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
        GRAPH.local.opts = {k: p[k] for k in ('children', 'kind', 'decade', 'source', 'fiction', 'hist') if p.get(k)}   # place-page filters
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
            if u.path == '/api/compare':      # two places: /api/compare?a=place:Q854&b=place:Q16[&children=1...]
                return self.send_json(GRAPH.compare(p['a'], p['b'], GRAPH.local.opts))
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
