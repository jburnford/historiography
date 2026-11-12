"""The key log as a queryable graph: Parquet tables and an embedded LadybugDB (Cypher) database (2026-11-02).

The key log (data/identifiers/events-*.jsonl, closed shards gzipped) is the source of truth in git; this builds a local, disposable
view of it that anyone can rebuild from a clean clone. It reads only files tracked in git (it stops if an input
is untracked) and writes to build/graph/ (git-ignored):
- nodes: `Person`, `Work`, `Institution` (active keys; identifiers by scheme as columns, all anchors as a list);
- relations from the log's claims: `AUTHORED`, `EDITED`, `SUPERVISED` (Person -> Work), `PUBLISHED_AS` and
  `REVIEWS` (Work -> Work: a review and the book it reviews), with the claim key and its resolution; claims
  whose endpoints do not resolve to one key each are left out and counted;
- `COEDITED` (Person -> Person, once per pair), derived as COAUTHORED from shared EDITED volumes (and AUTHORED
  credits with role volume-editor, 2026-11-12);
- `PART_OF` (Work -> Work): a chapter and the volume it is in; `EDITOR_OF` (Person -> Person), derived: a
  volume's editor -> each author of a chapter in it (with the chapter and volume keys; user, 2026-11-05);
- `REVIEWED` (Person -> Person), derived: the author of a review -> each author of the book it reviews, with
  the review and book keys (user, 2026-11-02: edges between reviewers and the authors of the books);
- `ADVISED` (Person -> Person), derived: a thesis's supervisor -> its author (with the claim and thesis keys),
  and the log's person-to-person `advised` claims (Wikidata's doctoral advisors where the student's thesis is
  not in the log; thesis empty);
- `COAUTHORED` (Person -> Person, stored once per pair, lower key first), derived: people who authored the same
  works, with the number of works, of distinct titles (an editorial co-signed in many journals has one DOI per
  journal: 147 works, 1 title), the first and last year and the work keys (user, 2026-11-05: a count matters);
- `AWARDED_BY` (Work -> Institution) from the works' `awarded-by:` members;
- `AFFILIATED_WITH` (Person -> Institution): dated affiliations by source (AHA directory and advising, IHR staff
  lists, ORCID, Wikidata, review credits, JSTOR review signatures, LC 373) from data/graph/affiliations.csv.gz
  (scripts/export_affiliations.py; user, 2026-11-08: departments should show the faculty who taught there);
- `POSSIBLY_SAME` (Person -> Person, once per pair, lower key first) from `possible-same:` members: same name and
  fitting timelines, not confirmed (scripts/key_possible_same.py; user, 2026-11-08); dropped once the two merge.
  `likelihood` is 'possible' for those, 'very_likely' from `very-likely-same:` members: an outside reviewer (Terra)
  found strong but inferred evidence that they are one person (user, 2026-11-09: "merge the medium data and just
  create an edge that hedges very_likely"); `not-same:` members drop the edge;
- `CITES` (Work -> Work): a corpus dissertation citing a keyed work (data/graph/cites.csv.gz, exported from
  the corpus by scripts/export_citations.py), and a JSTOR article, review essay or review article citing one in
  its notes (data/graph/jstor-cites.csv.gz, scripts/export_jstor_citations.py; 2026-11-06). `edition` is true when
  the only evidence is a JSTOR note citing a later edition or translation of the work (2026-11-08); counts may
  include or leave these out. Crossref reference lists of journal articles add more (data/graph/crossref-cites.csv.gz,
  scripts/crossref_citations.py; 2026-11-08), above all after the JSTOR runs end (about 2020). A citing article the
  key log does not hold is a Work node from data/graph/crossref-cites/articles/ with key `doi:<doi>` and resolution
  `unkeyed` (two layers: the 4.43M harvested articles are not minted as keys; 2026-11-10). `source` says which
  inputs carry an edge ('thesis', 'thesis-matched', 'jstor', 'crossref', comma-joined; 2026-11-10);
- cited works matched on 2026-11-10 to LC, OpenAlex or Crossref records (data/graph/cited-works/,
  scripts/export_cited_works.py; two layers like the Crossref articles): a Work node keyed `lccn:` / `doi:` /
  `openalex:` with resolution `unkeyed`, unless the key log holds one of the work's identifiers (then that key); the
  dissertations citing them (CITES source 'thesis-matched'); their authors where data/identifiers/
  cited-work-authors-2026-11-10 linked them: `exact` (the source's LC authority or ORCID is on a key) and `linked`
  rows are `LINKED_AUTHORED` (`LINKED_EDITED` for LC editors), Person -> Work, with source and state, in their own
  tables (linked_authored.parquet, linked_edited.parquet): never in AUTHORED/EDITED, which identity scripts read as
  evidence (coordinator 2026-11-10: no self-feeding); the derived tables stay key-log only; `possible` rows are
  `POSSIBLE_AUTHOR` (Person -> Work, one row per candidate, with the number of candidates and the linker's signals),
  never credited. report.json's `linkage` counts the works and citing theses by author state, per source.
- printed people of keyed works linked on 2026-11-11 (data/graph/work-people/, scripts/link_work_people.py): the
  reviewer printed on a review, the authors of a JSTOR article, the co-authors in a work's OpenAlex record. `exact`
  and `linked` rows join LINKED_AUTHORED (source `work-people:<role>`; a reviewer is the author of the review, as in
  the key log), `possible` rows join POSSIBLE_AUTHOR (role column), never AUTHORED. For display, REVIEWED_LINKED and
  COAUTHORED_LINKED are built beside REVIEWED and COAUTHORED (which stay key-log only) from AUTHORED plus these
  credits: only the pairs that need a linked credit, with the number of works resting on one. report.json's
  `linkage.work_people` counts rows by role and state, and `linkage.defects` the gaps each rebuild should shrink.
- 2026-11-11, from data/graph/cited-works (scripts/export_cited_works.py): Crossref metadata matches (source
  `crossref-meta`, two layers like the rest); translations and later editions: a thesis citing one cites the canonical
  (original) work, CITES source `thesis-edition`, `edition` true unless the thesis also cites the work directly,
  `cited_as` = the node it was cited as; the older crosswalks' thesis edge named in `replaces` is dropped, so a moved
  citation counts once; `EDITION_OF` (Work -> Work, edition_of.parquet) from the translation or edition node to the
  original (keys are not merged); compilations as unkeyed `corpus:` works with a LINKED_AUTHORED row (source
  `compilation`);
- 2026-11-11, JSTOR note citations matched to LC/OpenAlex/Crossref/JSTOR-index works (data/graph/jstor-cited-works,
  scripts/export_jstor_cited_works.py): CITES source `jstor-matched`; cited works the log does not hold are unkeyed
  Work nodes (or the cited-works node holding one of their identifiers); an LC main entry whose name authority is on
  one person key is a LINKED_AUTHORED row (source `jstor-matched:lc`, state `exact`). Rows with `cited_as` (a note
  citing a translation or later edition) cite the canonical work: CITES source `jstor-edition`, edition true unless
  the article also cites the work directly, `cited_as` = the node it was cited as;
- 2026-11-11, data/graph/work-people rows with role `contributor` (foreword writers, series editors; exact/linked) are
  `CONTRIBUTED` (Person -> Work, contributed.parquet), never AUTHORED, COAUTHORED or REVIEWED; possible contributors are
  not candidates;
- 2026-11-11, data/graph/author-works (scripts/author_works.py): works by keyed people the graph lacked are unkeyed Work
  nodes (`doi:` / `openalex:`; twins of another version, dataset series and repository or submitted copies of a work
  the table holds in another version are skipped), their ORCID credits AUTHORED rows with evidence linked (source
  `author-works:<basis>`, state exact; held ones author_candidates with a reason); volumes.csv.gz gives unkeyed volume
  nodes (`volume:` / `doi:`, kind book, ISBN, editors as printed); PART_OF has an `evidence` column: the key log's
  claims (`keylog`) and chapter -> volume links from data/graph/work-containers.csv.gz and author-works/works.csv.gz
  (`linked`, source orcid-container / doi-container / author-works-container, `volume_basis`); keyed works get journal and
  issn from data/graph/work-journals.csv.gz where they had none (`journal_source` says from where) and `kind_proposed`
  where a matched record names another kind (`kind` is not changed).
- 2026-11-12 (integration pass four): AUTHORED and EDITED carry `role` and `role_basis` (data/graph/edition-roles.csv.gz,
  scripts/edition_roles.py): EDITED volume-editor / edition-editor / author-editor / translator / introducer /
  series-editor / unknown; AUTHORED 'author' unless the table names translator, introducer, edition-editor,
  series-editor or volume-editor, or data/graph/volume-editors.csv.gz credits the person as the volume's editor (ORCID
  'edited-book' records filed as authorship). Credits with role edition-editor, translator, introducer or series-editor
  are not citations of the person's own work (report `class_15_edition_roles`; 'contributor' joined them on 2026-11-12:
  a qualified editor such as 'cartographic editor', 'associate editor', 'maps edited by', class 23). volume-editors.csv.gz
  (scripts/volume_editors.py) also gives `editors_printed` and EDITED rows with evidence linked (source
  volume-editors:<source>; not for a series editor or contributor of the volume), possible editors as author_candidates
  (role editor); the LC main entries of edition-role works (data/identifiers/edition-roles-2026-11-11/missing-authors)
  are AUTHORED rows (source edition-roles:lc-main-entry); linked credits in
  data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz are demoted to author_candidates (key-log ones
  counted); works get `first_year`, `first_year_catalogue`, `first_year_basis` (data/graph/work-years.csv.gz; `year`
  unchanged); data/graph/edition-canonical-fixes.csv.gz moves the thesis and JSTOR citations of a canonical key that is
  a translation to the original and adds the EDITION_OF edge between them; report `class_17_reprint_years`.
- 2026-11-12 (follow-up): volume-editors.csv.gz rows with state `series-editor` (scripts/volume_editors.py's
  series-editor rule, class 19) are printed only: no EDITED row, not in editors_printed; a linked person is CONTRIBUTED
  (basis series-editor-pattern). The derived edges read the role: only AUTHORED credits with role author make
  COAUTHORED pairs and REVIEWED edges (volume-editor, edition-editor, translator, introducer and series-editor credits
  do not); AUTHORED credits with role volume-editor join COEDITED, which now has `evidence` (keylog: key-log EDITED
  and key-log AUTHORED volume-editor credits; linked: linked EDITED credits with an editor role and linked AUTHORED
  volume-editor credits, lists over 25 skipped) and `linked_works` / `linked_work_keys` as COAUTHORED.
The key-log state comes from the SQLite cache (build/keylog-state.sqlite, scripts/keylog_snapshot.py; 2026-11-10),
caught up to the log's last event first and then read in bulk, so the build no longer replays the whole log (10 GB);
--replay replays it instead (the old path, for checking one against the other).
With --db, the Parquet tables are loaded into a LadybugDB database (build/graph/historiography.lbug), queried in
Cypher:

    MATCH (p:Person)-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) WHERE p.label = 'Benjamin Hoy' RETURN s.label, t.label

    python3 scripts/build_graph.py            # Parquet tables only
    python3 scripts/build_graph.py --db       # and the LadybugDB database
    python3 scripts/build_graph.py --replay --out /tmp/graph-replay   # full log replay (check against the cache build)
    python3 scripts/build_graph.py --out build/graph-check --untracked-ok   # a check build before new tables are in git
    python3 scripts/build_graph.py --out build/graph --untracked-ok         # the live build, same, until they are tracked
"""
import argparse
import csv
import gzip
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import identifiers as I

csv.field_size_limit(1 << 30)   # author-works rows carry the printed authorships as JSON
from identifiers import DEFAULT_DIR, PREDICATES, RETIRED, ROOT, State

OUT = ROOT / 'build/graph'
CITES = ROOT / 'data/graph/cites.csv.gz'
JSTOR_CITES = ROOT / 'data/graph/jstor-cites.csv.gz'   # scripts/export_jstor_citations.py (JSTOR article notes)
CROSSREF_CITES = ROOT / 'data/graph/crossref-cites.csv.gz'   # scripts/crossref_citations.py (Crossref reference lists)
CROSSREF_PARTS = ROOT / 'data/graph/crossref-cites'           # the same in parts (2026-11-10), and articles/: its
CROSSREF_ARTICLES = CROSSREF_PARTS / 'articles'                # unkeyed citing articles (doi, title, year, journal)
AFFILIATIONS = ROOT / 'data/graph/affiliations.csv.gz'  # scripts/export_affiliations.py (dated person -> institution)
CITED = ROOT / 'data/graph/cited-works'   # scripts/export_cited_works.py (2026-11-10): works.csv.gz, cites*.csv.gz,
                                          # authors.csv.gz, report.json (the corpus's citation count)
WORK_PEOPLE = ROOT / 'data/graph/work-people'   # scripts/link_work_people.py (2026-11-11): printed reviewers, JSTOR
                                                # authors and co-authors of keyed works -> person keys (part-NN.csv.gz)
JSTOR_CITED = ROOT / 'data/graph/jstor-cited-works'   # scripts/export_jstor_cited_works.py (2026-11-11): JSTOR notes
                                                    # matched to LC/OpenAlex/Crossref/JSTOR-index works (two layers)
AUTHOR_WORKS = ROOT / 'data/graph/author-works'     # scripts/author_works.py (2026-11-11): works by keyed people absent
                                                    # from the graph, their ORCID credits, and (export_work_containers.py)
                                                    # the unkeyed volumes chapters are in
WORK_CONTAINERS = ROOT / 'data/graph/work-containers.csv.gz'   # export_work_containers.py: chapter -> volume, proposed kind
WORK_JOURNALS = ROOT / 'data/graph/work-journals.csv.gz'       # export_work_containers.py: journal, ISSN, proposed kind
# 2026-11-12 (integration pass four):
VOLUME_EDITORS = ROOT / 'data/graph/volume-editors.csv.gz'     # scripts/volume_editors.py: printed editors of the volumes
                                                               # chapters are in (LC 2016, Crossref), linked to person keys
EDITION_ROLES = ROOT / 'data/graph/edition-roles.csv.gz'       # scripts/edition_roles.py: the role behind each AUTHORED /
                                                               # EDITED credit (author, volume-editor, edition-editor, ...)
WORK_YEARS = ROOT / 'data/graph/work-years.csv.gz'             # scripts/work_first_years.py: first publication year
EDITION_FIXES = ROOT / 'data/graph/edition-canonical-fixes.csv.gz'   # work_first_years.py: canonical keys that are
                                                                     # translations while the original is known
ER_DIR = ROOT / 'data/identifiers/edition-roles-2026-11-11'
MISSING_AUTHORS = ER_DIR / 'missing-authors.csv.gz'            # the LC main entry of an edition-role work, keyed: AUTHORED
LC_CONFLICTS = ROOT / 'data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz'   # authored credits on a book
                                                               # whose LC main entry is someone else (not audited)
WY_REPORT = ROOT / 'data/identifiers/work-years-2026-11-11/report.json'
# roles under which a credit is not a citation of the person's own work (class 15): they prepared someone else's work;
# 'contributor' (2026-11-12, class 23): a qualified editor ('cartographic editor', 'associate editor', 'maps edited by')
EDITION_ROLE_SET = ('edition-editor', 'translator', 'introducer', 'series-editor', 'contributor')
# AUTHORED rows keep role 'author' unless edition-roles names one of these (or the volume-editors table credits them)
AUTHORED_ROLES = EDITION_ROLE_SET + ('volume-editor',)
# volume links (PART_OF, evidence linked) loaded by basis: exact title (one candidate), the book DOI, one of several
# title candidates chosen by its EDITED credits or LCCN, the main title (loaded with its basis, to be audited), and a
# new unkeyed volume made from the chapter's own container record. Never ':held' (two or more candidates left).
VOLUME_BASES = ('title', 'book-doi', 'title:edited-or-lccn', 'main-title:edited-or-lccn', 'main-title', 'new-unkeyed-volume')
# CITES sources, as bits (one int per edge in the build: edition-only flag in bit 0, sources above it).
# thesis-edition (2026-11-11): a thesis citing a translation or later edition, carried to the canonical work
# jstor-edition (2026-11-11): a JSTOR note citing a translation or later edition, carried to the canonical work
SRC = (('thesis', 1), ('jstor', 2), ('crossref', 4), ('thesis-matched', 8), ('thesis-edition', 16), ('jstor-matched', 32),
       ('jstor-edition', 64))
THESIS_BITS = 1 | 8 | 16
SCHEMES = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'ror')
PERSON_RELATIONS = ('authored', 'edited', 'supervised')


def require_tracked(paths):
    """Stop unless every input is tracked in git: the build must work from a clean clone."""
    missing = []
    for p in paths:
        r = subprocess.run(['git', 'ls-files', '--error-unmatch', str(p.relative_to(ROOT))], cwd=ROOT,
                           capture_output=True)
        if r.returncode:
            missing.append(str(p.relative_to(ROOT)))
    if missing:
        sys.exit(f'inputs not tracked in git: {missing}')


def first(anchors, scheme):
    vals = sorted(a.split(':', 1)[1] for a in anchors if a.split(':', 1)[0] == scheme)
    return vals[0] if vals else None


def year_of(members, prefix):
    vals = sorted(m.split(':', 1)[1] for m in members if m.startswith(prefix) and m.split(':', 1)[1][:4].isdigit())
    return int(vals[0][:4]) if vals else None


def work_kind(anchors, members=()):
    stated = [m.split(':', 1)[1] for m in members if m.startswith('kind:')]   # a kind stated on review (DOI-only books)
    if len(stated) == 1:
        return stated[0]
    schemes = {a.split(':', 1)[0] for a in anchors}
    if schemes & {'aha-diss', 'diss-thesis', 'wrap'}:
        return 'thesis'
    if schemes & {'hnet-review', 'rih-review'}:
        return 'review'
    if 'lccn' in schemes:
        return 'book'
    if 'doi' in schemes:
        return 'article'          # articles and chapters cited in the corpus (key_cited_articles), and ORCID works
    if 'atlas' in schemes:
        return 'atlas_source'
    return 'other'


# Member prefixes the build reads (works: dates, kind, reviewers, journal, degree-granting institution; people: the
# possibly-same and not-same marks). The cache view loads only these.
MEMBER_PREFIXES = ('year:', 'lc-first-year:', 'kind:', 'reviewer-name:', 'journal:', 'awarded-by:',
                   'possible-same:', 'very-likely-same:', 'not-same:')
NODE_TYPES = ('person', 'work', 'institution')


class ReplayView:
    """The build's reads from a full replay of the log (identifiers.State.load: about 10 GB for 5.5M events)."""

    def __init__(self, directory):
        self.state = State.load(directory)

    def nodes(self):
        """Live person, work and institution keys: (key, type, label, resolution, anchors)."""
        for k, v in self.state.keys.items():
            if v['status'] not in RETIRED and v['type'] in NODE_TYPES:
                yield k, v['type'], v['label'], v['resolution'], v['anchors']

    def members(self, k):
        return self.state.members.get(k, ())

    def relations(self):
        for claim, subj, pred, obj in self.state.relations():
            yield claim, subj, pred, obj, self.state.keys[claim]['resolution']

    def lookup(self, name):
        return self.state.lookup(name)


class CacheView:
    """The same reads from the SQLite cache, in bulk: node records and the needed members in one scan each, relation
    claims in one join; names resolved by indexed lookups, following retirements as State.lookup does. The cache is
    brought up to the log's last event (or rebuilt) under the log lock first; the reads then share one snapshot."""

    def __init__(self, directory):
        import keylog_snapshot as K
        directory = I.log_dir(directory)
        with I.locked(directory):
            st = K.open_state(directory, write=True)
            self.seq = st.seq
            st.con.close()
        self.con = K.connect(K.cache_path(directory), readonly=True)
        self.con.execute('BEGIN')                     # one read snapshot for the whole build
        self.con.execute('SELECT 1 FROM meta LIMIT 1').fetchone()
        seq = int(self.con.execute("SELECT v FROM meta WHERE k = 'seq'").fetchone()[0])
        if seq != self.seq:
            sys.exit(f'key-log cache moved from seq {self.seq} to {seq} while opening; rerun')
        retired = tuple(RETIRED)
        q = ','.join('?' * len(retired))
        # retired key -> its successors (replaced_by), and the live types of non-claim keys: enough to resolve
        # any key name without a query
        self.next = {k: json.loads(rb) for k, rb in
                     self.con.execute(f'SELECT key, replaced_by FROM keys WHERE status IN ({q})', retired)}
        self.type = dict(self.con.execute(f"SELECT key, type FROM keys WHERE type <> 'claim' AND status NOT IN ({q})", retired))
        self.mem = defaultdict(set)
        cond = ' OR '.join(f"member GLOB '{p}*'" for p in MEMBER_PREFIXES)
        for k, m in self.con.execute(f'SELECT key, member FROM members WHERE {cond}'):
            self.mem[k].add(m)
        self._memo = {}

    def nodes(self):
        q = ','.join('?' * len(NODE_TYPES))
        for k, t, label, res, anchors in self.con.execute(
                f'SELECT key, type, label, resolution, anchors FROM keys WHERE type IN ({q}) AND status NOT IN '
                f'({",".join("?" * len(RETIRED))}) ORDER BY key', NODE_TYPES + tuple(RETIRED)):
            yield k, t, label, res, json.loads(anchors)

    def members(self, k):
        return self.mem.get(k, ())

    def relations(self):
        retired = tuple(RETIRED)
        for claim, subj, pred, obj, res in self.con.execute(
                f'SELECT r.claim, r.subject, r.predicate, r.object, k.resolution FROM relation r JOIN keys k ON k.key = r.claim '
                f'WHERE k.status NOT IN ({",".join("?" * len(retired))}) ORDER BY r.claim', retired):
            yield claim, self.lookup(subj), pred, self.lookup(obj), res

    def _key(self, name):
        """The key a name names (a key itself, an active anchor, or an alias), as State.lookup's first step."""
        if name in self.type or name in self.next:
            return name
        c = self.con
        for sql in ('SELECT key FROM keys WHERE key = ?', 'SELECT key FROM anchor WHERE anchor = ?',
                    'SELECT key FROM alias WHERE alias = ?'):
            row = c.execute(sql, (name,)).fetchone()
            if row and row[0]:
                return row[0]
        return None

    def lookup(self, name):
        hit = self._memo.get(name)
        if hit is not None:
            return hit
        key = self._key(name)
        if not key:
            out = []
        else:
            out, todo, seen = [], [key], set()
            while todo:
                k = todo.pop()
                if k in seen:
                    continue
                seen.add(k)
                nxt = self.next.get(k, [])
                out.extend([] if nxt else [k])
                todo.extend(nxt)
            out.sort()
        if len(self._memo) < 3_000_000:
            self._memo[name] = out
        return out


def crossref_cites(cites, parts, state, types, unkeyed, report, schema, cited_as=None):
    """CITES with the Crossref parts (tens of millions of rows) joined in DuckDB, not a Python dict: each distinct name
    is resolved once (State.lookup; an unkeyed citing article is its own node), then the edges are joined, folded with
    the dissertation and JSTOR edges (edition only when every source says edition) and written straight to Parquet."""
    import duckdb
    db = duckdb.connect()
    db.execute(f"SET memory_limit = '4GB'; SET temp_directory = '{OUT}/duckdb-tmp'; SET preserve_insertion_order = false")
    files = [str(p) for p in parts]
    cited_as = cited_as or {}
    db.execute(f"""CREATE TABLE xr AS SELECT citing_work, cited_work, basis = 'edition' AS ed, 4::TINYINT AS src FROM read_csv({files}, header = true,
                   columns = {{'citing_work': 'VARCHAR', 'cited_work': 'VARCHAR', 'citations': 'INTEGER', 'basis': 'VARCHAR'}})""")
    names, keys = [], []
    for (n,) in db.execute('SELECT DISTINCT citing_work FROM xr UNION SELECT DISTINCT cited_work FROM xr').fetchall():
        k = state.lookup(n) or ([n] if n in unkeyed else [])
        if len(k) == 1 and types.get(k[0]) == 'work':
            names.append(n); keys.append(k[0])
    db.register('name_map', pa.table({'name': names, 'key': keys}))
    del names, keys
    db.execute("""CREATE TABLE xr2 AS SELECT m1.key AS a, m2.key AS b, ed, src, NULL::VARCHAR AS ca FROM xr
                  JOIN name_map m1 ON m1.name = xr.citing_work JOIN name_map m2 ON m2.name = xr.cited_work WHERE m1.key <> m2.key""")
    n_xr, n_xr2 = db.execute('SELECT count(*) FROM xr').fetchone()[0], db.execute('SELECT count(*) FROM xr2').fetchone()[0]
    report['crossref_cites_unresolved'] = n_xr - n_xr2
    report['crossref_cites_edition'] = db.execute('SELECT count(*) FROM xr2 WHERE ed').fetchone()[0]
    db.execute('DROP TABLE xr')
    db.register('base', pa.table({'a': [a for a, _ in cites], 'b': [b for _, b in cites],
                                  'ed': [bool(v & 1) for v in cites.values()],
                                  'src': pa.array([v >> 1 for v in cites.values()], pa.int8()),
                                  'ca': pa.array([';'.join(sorted(cited_as[k])) if k in cited_as else None for k in cites],
                                                 pa.string())}))
    report['cites_from_crossref'] = db.execute("""SELECT count(*) FROM (SELECT DISTINCT a, b FROM xr2) x
                                                  ANTI JOIN base USING (a, b)""").fetchone()[0]
    names = ' '.join(f"CASE WHEN m & {b} > 0 THEN '{n}' END," for n, b in SRC).rstrip(',')
    db.execute(f"""COPY (SELECT "from", "to", edition, concat_ws(',', {names}) AS source, cited_as FROM (
                   SELECT a AS "from", b AS "to", bool_and(ed) AS edition, bit_or(src::TINYINT) AS m,
                          string_agg(DISTINCT ca, ';') AS cited_as
                   FROM (SELECT a, b, ed, src, ca FROM base UNION ALL SELECT a, b, ed, src, ca FROM xr2) GROUP BY 1, 2) ORDER BY 1, 2)
                   TO '{OUT}/cites.parquet' (FORMAT parquet)""")
    report['CITES'], report['CITES_edition_only'] = db.execute(
        f"SELECT count(*), count(*) FILTER (WHERE edition) FROM '{OUT}/cites.parquet'").fetchone()
    db.close()
    shutil.rmtree(OUT / 'duckdb-tmp', ignore_errors=True)


def cites_code(edition, src, old=None):
    """An edge's int: bit 0 = edition only (true only while every source says edition), sources above it."""
    if old is None:
        return int(bool(edition)) | src << 1
    return int(bool(old & 1 and edition)) | ((old >> 1) | src) << 1


def source_names(mask):
    return ','.join(n for n, b in SRC if mask & b)


def read_rows(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def cited_parts(name):
    """data/graph/cited-works/<name>.csv.gz, or its parts <name>/part-NN.csv.gz once a table passes 50 MB."""
    one = CITED / f'{name}.csv.gz'
    return [one] if one.exists() else sorted((CITED / name).glob('part-*.csv.gz'))


def cited_work_nodes(state, types, works, unkeyed, report, index=None):
    """Work nodes for the cited works of data/graph/cited-works (two layers): the key the log gives one of the work's
    identifiers (its id, all its LCCNs, alias DOIs), else the id itself as an unkeyed node. Returns id -> graph key;
    `index` gets every identifier of an unkeyed cited work -> its node (for the JSTOR-matched works)."""
    out = {}
    index = {} if index is None else index
    for path in cited_parts('works'):
        for r in read_rows(path):
            wid = r['id']
            ids = list(dict.fromkeys([wid] + [f'lccn:{x}' for x in r['lccns'].split(';') if x]
                                     + [a for a in r['alias_ids'].split(';') if a]))
            hits = {k for x in ids for k in state.lookup(x) if types.get(k) == 'work'}
            if len(hits) > 1:               # identifiers on several keys: the id's own key, else left out
                hits = {k for k in state.lookup(wid) if types.get(k) == 'work'}
                if len(hits) != 1:
                    report['cited_works_on_several_keys'] += 1
                    continue
            if hits:
                out[wid] = hits.pop()
                report['cited_works_keyed'] += 1
                continue
            node = next((x for x in ids if x in unkeyed), None)     # already a node (a Crossref citing article)
            if node:
                out[wid] = node
                report['cited_works_on_crossref_nodes'] += 1
                continue
            unkeyed.add(wid)
            types[wid] = 'work'
            works.append(dict(key=wid, label=r['title'] or None, resolution='unkeyed', anchors=sorted(ids),
                              kind=r['kind'] or 'other', lccn=r['lccns'].split(';')[0] or None,
                              year=int(r['year']) if r['year'] else None, reviewer_names=[],
                              journal=r['container'] or None))
            out[wid] = wid
            for x in ids:
                index.setdefault(x, wid)
            report['Work_unkeyed_cited_works'] += 1
    return out


def jstor_cited_nodes(state, types, works, unkeyed, index, report):
    """Work nodes for the JSTOR-matched cited works (data/graph/jstor-cited-works/works.csv.gz): the key the log gives
    one of their identifiers, else the cited-works node holding one, else the id as an unkeyed node. Returns id -> graph
    key and graph key -> LC name authority of the main entry (an identifier link, LINKED_AUTHORED source jstor-matched:lc)."""
    out, lc = {}, {}
    for r in read_rows(JSTOR_CITED / 'works.csv.gz'):
        wid = r['id']
        ids = list(dict.fromkeys([wid] + [x for x in r['identifiers'].split(';') if x]))
        hits = {k for x in ids for k in state.lookup(x) if types.get(k) == 'work'}
        if len(hits) > 1:
            hits = {k for k in state.lookup(wid) if types.get(k) == 'work'}
            if len(hits) != 1:
                report['jstor_cited_works_on_several_keys'] += 1
                continue
        if hits:
            out[wid] = hits.pop()
            report['jstor_cited_works_keyed'] += 1
            continue
        node = next((index[x] for x in ids if x in index), None) or next((x for x in ids if x in unkeyed), None)
        if node:
            out[wid] = node
            report['jstor_cited_works_on_cited_works_nodes'] += 1
        else:
            unkeyed.add(wid)
            types[wid] = 'work'
            lccns = [x[5:] for x in ids if x.startswith('lccn:')]
            works.append(dict(key=wid, label=r['title'] or None, resolution='unkeyed', anchors=sorted(ids),
                              kind=r['kind'] or 'other', lccn=lccns[0] if lccns else None,
                              year=int(r['year'][:4]) if r['year'][:4].isdigit() else None, reviewer_names=[],
                              journal=r['container'] or None))
            out[wid] = wid
            report['Work_unkeyed_jstor_cited_works'] += 1
        if r['lc_author'] and '/editor/' not in r['basis']:
            lc.setdefault(out[wid], r['lc_author'])
    return out, lc


STATE_ORDER = ('exact', 'linked', 'possible-one', 'possible-several', 'none')


def cited_authors(state, types, cited_key, rels, report):
    """LINKED_AUTHORED/LINKED_EDITED rows for exact and linked authors (separate tables, never AUTHORED/EDITED),
    POSSIBLE_AUTHOR rows for possible ones, and each cited work's best author state (for the linkage report). Person keys are resolved through merges:
    an exact row by its identifier (lcnaf:/orcid:, current), else the linker's key; possible candidates each."""
    keyed = set(cited_key.values()) - {w for w in cited_key.values() if ':' in w}
    have = {(r['from'], r['to']) for n in ('AUTHORED', 'EDITED') for r in rels[n] if r['to'] in keyed}
    linked = {'AUTHORED': [], 'EDITED': []}
    possible = {}
    best = {}                                       # cited work id -> index in STATE_ORDER
    seen = set()

    def person(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'person'] if name else []
        return ks[0] if len(ks) == 1 else None
    for path in cited_parts('authors'):
        for r in read_rows(path):
            w = cited_key.get(r['work'])
            if not w:
                report['cited_authors_work_unresolved'] += 1
                continue
            st = r['state']
            if st in ('exact', 'linked'):
                k = (person(r['source_person_id']) if st == 'exact' else None) or person(r['person_key'])
                if not k:
                    report[f'cited_authors_{st}_unresolved'] += 1
                    cat = 'none'
                else:
                    cat = st
                    pred = 'EDITED' if r['role'] == 'editor' else 'AUTHORED'
                    if (k, w) in have:
                        report['cited_authors_already_in_log'] += 1
                    elif (pred, k, w) not in seen:
                        seen.add((pred, k, w))
                        linked[pred].append({'from': k, 'to': w, 'claim': f"cited-works:{r['source']}:{st}",
                                             'resolution': 'linked', 'source': r['source'], 'state': st})
            elif st == 'possible':
                cands = sorted({k for c in r['candidates'].split('|') if (k := person(c))})
                if not cands:
                    report['cited_authors_possible_unresolved'] += 1
                cat = 'possible-one' if len(cands) == 1 else 'possible-several' if cands else 'none'
                for k in cands:
                    possible.setdefault((k, w), {'from': k, 'to': w, 'n_candidates': len(cands),
                                                 'signals': r['signals'] or None, 'source': r['source'],
                                                 'role': r['role']})
            else:
                cat = 'none'
            i = STATE_ORDER.index(cat)
            best[r['work']] = min(best.get(r['work'], i), i)
    return linked, list(possible.values()), best


def work_people(state, types, rels, report):
    """AUTHORED rows with evidence linked (exact/linked) and author_candidates rows (possible) from data/graph/work-people;
    works and person keys resolved through merges. A credit the key log already holds is skipped (counted).
    Contributors (role 'contributor': foreword writers, series editors; 2026-11-11) are CONTRIBUTED rows, never authors:
    exact/linked go to the third list, possible and 'contributor-candidate' rows are dropped (counted), so they never
    reach AUTHORED, COAUTHORED, the REVIEWED derivation or author_candidates."""
    have = {(r['from'], r['to']) for r in rels['AUTHORED']}
    linked, possible, seen = [], {}, set()
    contributed, cseen = [], set()
    counts = Counter()

    def one(name, typ):
        ks = [k for k in state.lookup(name) if types.get(k) == typ] if name else []
        return ks[0] if len(ks) == 1 else None
    for path in sorted(WORK_PEOPLE.glob('part-*.csv.gz')):
        for r in read_rows(path):
            w = one(r['work'], 'work')
            role, st = r['role'], r['state']
            if not w:
                counts[f'{role}|work_unresolved'] += 1
                continue
            if role == 'contributor' or st == 'contributor-candidate':
                if st not in ('exact', 'linked') or role != 'contributor':
                    counts[f'{role}|{st}|not_loaded'] += 1
                    continue
                ks = [k for x in r['person_key'].split(';') if (k := one(x, 'person'))]
                if len(set(ks)) != 1:
                    counts[f'{role}|{st}|person_unresolved'] += 1
                    continue
                if (ks[0], w) in have:
                    counts[f'{role}|{st}|also_keylog_author'] += 1
                if (ks[0], w) not in cseen:
                    cseen.add((ks[0], w))
                    counts[f'{role}|{st}'] += 1
                    contributed.append({'from': ks[0], 'to': w, 'claim': f"work-people:contributor:{r['position']}",
                                        'resolution': 'linked', 'evidence': 'linked', 'source': f"work-people:{r['source']}",
                                        'state': st, 'basis': r['branch'] or None})
                continue
            if st in ('exact', 'linked'):
                ks = [k for x in r['person_key'].split(';') if (k := one(x, 'person'))]
                if len(set(ks)) != 1:
                    counts[f'{role}|{st}|person_unresolved'] += 1
                    continue
                k = ks[0]
                if (k, w) in have:
                    counts[f'{role}|{st}|already_in_log'] += 1
                elif (k, w) not in seen:
                    seen.add((k, w))
                    counts[f'{role}|{st}'] += 1
                    linked.append({'from': k, 'to': w, 'claim': f"work-people:{role}:{r['position']}", 'resolution': 'linked',
                                   'source': f'work-people:{role}', 'state': st})
            elif st == 'possible':
                cands = sorted({k for c in r['candidates'].split('|') if (k := one(c, 'person'))})
                counts[f'{role}|possible'] += 1
                for k in cands:
                    if (k, w) not in have:
                        possible.setdefault((k, w), {'from': k, 'to': w, 'n_candidates': len(cands), 'signals': r['signals'] or None,
                                                     'source': f'work-people:{r["source"]}', 'role': role})
    return linked, list(possible.values()), counts, contributed


def work_resolver(state, types, unkeyed, index):
    """name -> graph work node: the key the log gives it (one only), else the cited-works node holding it, else itself
    when it is already an unkeyed node."""
    def resolve(name):
        if not name:
            return None
        ks = [k for k in state.lookup(name) if types.get(k) == 'work']
        if ks:
            return ks[0] if len(ks) == 1 else None
        return index.get(name) or (name if name in unkeyed else None)
    return resolve


def author_work_nodes(state, types, works, wi, unkeyed, resolve, report):
    """Work nodes from data/graph/author-works (2026-11-11): the unkeyed volumes chapters are in (volumes.csv.gz) and
    the works of keyed people the graph lacked (works.csv.gz). An id the graph already holds (keyed or unkeyed) is not
    duplicated: credits and links attach to that node. Skipped works: a twin of another version (twin_of, any basis), a
    dataset series, and a repository copy or submitted version when another version of the same title by the same
    credited person is in the table. Returns id -> node for volumes and works, the volume links (node, volume id, basis),
    and the nodes whose printed author list is longer than 25 (no co-authorship from them)."""
    from author_works import tkey
    vol_key = {}
    for r in read_rows(AUTHOR_WORKS / 'volumes.csv.gz'):
        vid = r['id']
        doi = f"doi:{r['doi'].lower()}" if r['doi'] else None
        ids = list(dict.fromkeys([vid] + ([doi] if doi else [])))
        node = next((n for x in ids if (n := resolve(x))), None)
        if node:
            vol_key[vid] = node
            report['aw_volumes_on_existing_nodes'] += 1
            w = wi.get(node)
            if w is not None:
                if not w.get('isbn') and r['isbn']:
                    w['isbn'] = r['isbn']
                if not w.get('editors_printed') and r['editors']:
                    w['editors_printed'] = r['editors']
            continue
        unkeyed.add(vid)
        types[vid] = 'work'
        w = dict(key=vid, label=r['title'] or None, resolution='unkeyed', anchors=sorted(ids), kind='book', lccn=None,
                 year=int(r['year'][:4]) if r['year'][:4].isdigit() else None, reviewer_names=[], journal=None,
                 isbn=r['isbn'] or None, editors_printed=r['editors'] or None)
        works.append(w)
        wi[vid] = w
        vol_key[vid] = vid
        report['Work_unkeyed_volumes'] += 1
    # credited people per work, for the 'another version' test
    credited = defaultdict(set)
    for r in read_rows(AUTHOR_WORKS / 'authors.csv.gz'):
        if r['state'] == 'credited':
            credited[r['work']].add(r['person_key'])
    REPO = ('repository', 'submitted-version')

    def flags(r):
        return set(filter(None, (r['flags'] or '').split(';')))
    good = set()                                    # (title key, person) of versions that are not repository copies
    for r in read_rows(AUTHOR_WORKS / 'works.csv.gz'):
        f = flags(r)
        if r['twin_of'] or 'dataset-series' in f or f & set(REPO):
            continue
        t = tkey(r['title'])
        good.update((t, p) for p in credited.get(r['id'], ()))
    aw_key, aw_part, long_lists = {}, [], set()
    for r in read_rows(AUTHOR_WORKS / 'works.csv.gz'):
        f = flags(r)
        if r['twin_of']:
            report[f"aw_works_skipped_twin|{r['twin_basis']}"] += 1
            continue
        if 'dataset-series' in f:
            report['aw_works_skipped_dataset_series'] += 1
            continue
        if f & set(REPO):
            t = tkey(r['title'])
            if any((t, p) in good for p in credited.get(r['id'], ())):
                report['aw_works_skipped_repository_or_submitted_with_other_version'] += 1
                continue
        wid = r['id']
        ids = list(dict.fromkeys([wid] + ([f"doi:{r['doi'].lower()}"] if r['doi'] else [])
                                 + ([f"openalex:{r['openalex']}"] if r['openalex'] else [])))
        hits = {n for x in ids if (n := resolve(x))}
        if len(hits) > 1:
            hits = {n for n in [resolve(wid)] if n}
            if len(hits) != 1:
                report['aw_works_on_several_nodes'] += 1
                continue
        if hits:
            node = hits.pop()
            report['aw_works_on_existing_nodes'] += 1
        else:
            node = wid
            unkeyed.add(wid)
            types[wid] = 'work'
            w = dict(key=wid, label=r['title'] or None, resolution='unkeyed', anchors=sorted(ids), kind=r['kind'] or 'other',
                     lccn=None, year=int(r['year'][:4]) if r['year'][:4].isdigit() else None, reviewer_names=[],
                     journal=r['journal'] or None, issn=r['issn_l'] or None,
                     journal_source='author-works' if r['journal'] else None)
            works.append(w)
            wi[wid] = w
            report['Work_unkeyed_author_works'] += 1
            report[f"aw_works_added|{r['kind'] or 'other'}"] += 1
        aw_key[wid] = node
        if (int(r['n_authors']) if r['n_authors'].isdigit() else 0) > 25:
            long_lists.add(node)
        if r['volume_work']:
            aw_part.append((node, r['volume_work'], r['volume_basis'] or ''))
    return vol_key, aw_key, aw_part, long_lists


def author_work_credits(state, types, have, aw_key, resolve, report):
    """AUTHORED rows (evidence linked, source author-works:<basis>, state exact) from author-works/authors.csv.gz and
    existing.csv.gz ('credited': an ORCID on exactly that key), and author_candidates rows for 'held' ones (the ORCID
    credit failed a guard: name_check says which)."""
    linked, cands, seen = [], {}, set()

    def person(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'person'] if name else []
        return ks[0] if len(ks) == 1 else None
    for fname in ('authors.csv.gz', 'existing.csv.gz'):
        for r in read_rows(AUTHOR_WORKS / fname):
            tag = fname.split('.')[0]
            w = aw_key.get(r['work']) if tag == 'authors' else resolve(r['work'])
            if not w:
                report[f'aw_credits_{tag}_work_not_loaded'] += 1
                continue
            k = person(r['person_key'])
            if not k:
                report[f'aw_credits_{tag}_person_unresolved'] += 1
                continue
            src = f"author-works:{r['basis']}"
            if r['state'] == 'credited':
                if (k, w) in have:
                    report[f'aw_credits_{tag}_already_in_log'] += 1
                elif (k, w) not in seen:
                    seen.add((k, w))
                    report[f'aw_credits_{tag}_credited'] += 1
                    linked.append({'from': k, 'to': w, 'claim': f"author-works:{r['basis']}:{r['position']}",
                                   'resolution': 'linked', 'source': src, 'state': 'exact'})
            elif r['state'] == 'held' and (k, w) not in have:
                report[f'aw_credits_{tag}_held'] += 1
                cands.setdefault((k, w), {'from': k, 'to': w, 'n_candidates': 1, 'signals': r['name_check'] or None,
                                          'source': src, 'role': 'author',
                                          'reason': f"held ORCID credit ({'printed ORCID' if r['basis'] == 'raw-orcid' else 'ORCID of the OpenAlex author'}"
                                                    f"; guard: {(r['name_check'] or '').replace(';', ', ')}; printed name: {r['name']})"})
    return linked, list(cands.values())


def volume_links(state, types, rels, vol_key, aw_part, resolve, report):
    """PART_OF rows with evidence linked: a chapter -> its volume, from data/graph/work-containers.csv.gz (keyed chapters;
    source orcid-container or doi-container) and author-works/works.csv.gz (author-works-container); only the bases in
    VOLUME_BASES, the basis kept on the edge. A chapter the key log already places in a volume keeps only that."""
    keyed_from = defaultdict(set)
    for r in rels['PART_OF']:
        keyed_from[r['from']].add(r['to'])
    rows, seen = [], set()

    def add(w, vw, basis, src):
        if basis not in VOLUME_BASES or not vw:
            report[f'part_of_linked_skipped|{basis or "no-basis"}'] += 1
            return
        v = vol_key.get(vw) or resolve(vw)
        if not v:
            report['part_of_linked_volume_unresolved'] += 1
            return
        if v == w:
            report['part_of_linked_self'] += 1
            return
        if w in keyed_from:
            report['part_of_linked_already_in_log' if v in keyed_from[w] else 'part_of_linked_chapter_has_keylog_volume'] += 1
            return
        if (w, v) in seen:
            report['part_of_linked_duplicate'] += 1
            return
        seen.add((w, v))
        report[f'part_of_linked|{src}|{basis}'] += 1
        rows.append({'from': w, 'to': v, 'claim': f'{src}:{basis}', 'resolution': 'linked', 'evidence': 'linked',
                     'source': src, 'volume_basis': basis})
    for r in read_rows(WORK_CONTAINERS):
        ks = [k for k in state.lookup(r['work']) if types.get(k) == 'work']
        if len(ks) != 1:
            report['work_containers_work_unresolved'] += 1
            continue
        add(ks[0], r['volume_work'], r['volume_basis'], 'orcid-container' if r['source'] == 'orcid' else 'doi-container')
    for w, vw, basis in aw_part:
        add(w, vw, basis, 'author-works-container')
    return rows


def work_facts(state, types, wi, report):
    """Journal, ISSN and proposed kind of keyed works from records matched by an exact id (export_work_containers.py):
    journal and issn fill a work with no journal (journal_source = the record's source); kind_proposed is set where the
    source names another kind than the graph's (containers first: a chapter; then journals). `kind` is never changed."""
    def one(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'work']
        return ks[0] if len(ks) == 1 else None
    for r in read_rows(WORK_CONTAINERS):
        k = one(r['work'])
        w = wi.get(k) if k else None
        if w is not None and r['proposed_kind'] and r['proposed_kind'] != w['kind']:
            w['kind_proposed'] = r['proposed_kind']
            report[f"kind_proposed|containers|{w['kind']}->{r['proposed_kind']}"] += 1
    for r in read_rows(WORK_JOURNALS):
        k = one(r['work'])
        w = wi.get(k) if k else None
        if w is None:
            report['work_journals_work_unresolved'] += 1
            continue
        if not w['journal'] and r['journal']:
            w['journal'], w['issn'], w['journal_source'] = r['journal'], r['issn'] or None, r['source']
            report[f"journal_filled|{r['source']}"] += 1
        elif r['journal']:
            report['journal_already_set'] += 1
        if r['proposed_kind'] and r['proposed_kind'] != w['kind']:
            if w.get('kind_proposed') and w['kind_proposed'] != r['proposed_kind']:
                report['kind_proposed_conflict_kept_container'] += 1
            elif not w.get('kind_proposed'):
                w['kind_proposed'] = r['proposed_kind']
                report[f"kind_proposed|journals|{w['kind']}->{r['proposed_kind']}"] += 1


def volume_editors(state, types, resolve, wi, report):
    """data/graph/volume-editors.csv.gz (2026-11-12): editors_printed on the volume node for every row that is not
    `held` (when the node has none); exact, linked and credited rows as candidate EDITED rows (evidence linked, source
    'volume-editors:<source>'; filtered later against AUTHORED, series editors and contributors); possible and
    ambiguous rows as author_candidates (role 'editor'). Rows with state 'series-editor' (the series-editor rule of
    scripts/volume_editors.py, class 19) are printed only: not editors_printed, no EDITED row; where the person key is
    kept (the linker had credited it) they are CONTRIBUTED rows (basis 'series-editor-pattern').
    Returns (rows, candidate rows, series-editor CONTRIBUTED rows)."""
    names, linked, cands, seen, series = defaultdict(list), [], {}, set(), {}

    def one(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'person'] if name else []
        return ks[0] if len(ks) == 1 else None
    for r in read_rows(VOLUME_EDITORS):
        w = resolve(r['volume'])
        if not w:
            report['volume_editors_volume_unresolved'] += 1
            continue
        st = r['state']
        if st == 'series-editor':
            report['volume_editors_series_editor_rows'] += 1
            ks = {k for x in r['person_key'].split(';') if (k := one(x))}
            if len(ks) == 1:
                k = ks.pop()
                series.setdefault((k, w), {'from': k, 'to': w, 'claim': f"volume-editors:series-editor:{r['position']}",
                                           'resolution': 'linked', 'evidence': 'linked',
                                           'source': f"volume-editors:{r['source']}", 'state': 'linked',
                                           'basis': 'series-editor-pattern'})
            elif r['person_key']:
                report['volume_editors_series_editor_person_unresolved'] += 1
            continue
        if st != 'held':                # held: a list of more than six names (a board or the contributors)
            names[w].append(r['printed_name'])
        if st in ('exact', 'linked', 'credited'):
            ks = {k for x in r['person_key'].split(';') if (k := one(x))}
            if len(ks) != 1:
                report['volume_editors_person_unresolved'] += 1
                continue
            k = ks.pop()
            if (k, w) not in seen:
                seen.add((k, w))
                linked.append({'from': k, 'to': w, 'claim': f"volume-editors:{r['source']}:{r['position']}",
                               'resolution': 'linked', 'source': f"volume-editors:{r['source']}", 'state': st,
                               'role': 'volume-editor', 'role_basis': f"volume-editors:{r['source']}:{st}",
                               'vol_id': r['volume']})
        elif st in ('possible', 'ambiguous'):
            cs = sorted({k for c in r['candidates'].split(';') if (k := one(c))})
            for k in cs:
                cands.setdefault((k, w), {'from': k, 'to': w, 'n_candidates': len(cs), 'signals': None,
                                          'source': f"volume-editors:{r['source']}", 'role': 'editor',
                                          'reason': f"printed volume editor '{r['printed_name']}': "
                                                    + ('the sole name-compatible person, no confirming fact' if len(cs) == 1
                                                       else f'one of {len(cs)} name-compatible people')})
    for w, ns in names.items():
        node = wi.get(w)
        if node is not None and not node.get('editors_printed'):
            node['editors_printed'] = '; '.join(dict.fromkeys(ns))
            report['volume_editors_printed_set'] += 1
    report['volume_editors_rows_exact_linked_credited'] = len(linked)
    report['volume_editors_candidate_rows'] = len(cands)
    report['volume_editors_series_editor_contributed'] = len(series)
    return linked, list(cands.values()), list(series.values())


def edition_roles():
    """(person, work, credit) -> (role, basis) from data/graph/edition-roles.csv.gz; where the key log has two claims
    under different evidence and the table two rows, a specific role wins over 'unknown' / 'absent'."""
    out = {}
    for r in read_rows(EDITION_ROLES):
        k = (r['person'], r['work'], r['credit'])
        old = out.get(k)
        if old is None or (old[0] in ('unknown', 'absent') and r['role'] not in ('unknown', 'absent')):
            out[k] = (r['role'], r['basis'] or None)
    return out


def work_years(wi, resolve, report):
    """first_year (earliest evidence: LC notes, reprint 008, edition clusters, printed thesis years),
    first_year_catalogue (catalogue evidence only) and first_year_basis from data/graph/work-years.csv.gz; `year` is
    not changed."""
    for r in read_rows(WORK_YEARS):
        if not r['first_year'] and not r['first_year_catalogue']:
            continue
        w = wi.get(r['key'])
        if w is None:
            n = resolve(r['key'])
            w = wi.get(n) if n else None
        if w is None:
            report['work_years_unresolved'] += 1
            continue
        y = lambda v: int(v[:4]) if v[:4].isdigit() else None
        w['first_year'], w['first_year_catalogue'], w['first_year_basis'] = y(r['first_year']), y(r['first_year_catalogue']), r['basis'] or None
        report['work_years_set'] += 1
        if w['first_year'] is not None and w['first_year'] != w['year']:
            report['work_years_first_year_differs'] += 1


def canonical_fixes(state, types, cited_key, report):
    """data/graph/edition-canonical-fixes.csv.gz: current canonical work -> proposed canonical (the original). A
    current key with two proposals is skipped; chains (a proposal that is itself a current key) are followed."""
    def work(name):
        if name in cited_key:
            return cited_key[name]
        ks = [k for k in state.lookup(name) if types.get(k) == 'work']
        return ks[0] if len(ks) == 1 else None
    props = defaultdict(set)
    rows = {}
    for r in read_rows(EDITION_FIXES):
        a, b = work(r['current_canonical']), work(r['proposed_canonical'])
        if not a or not b or a == b:
            report['edition_canonical_fixes_unresolved'] += 1
            continue
        props[a].add(b)
        rows.setdefault(a, r)
    fix = {}
    for a, bs in props.items():
        if len(bs) > 1:
            report['edition_canonical_fixes_skipped_two_proposals'] += 1
            continue
        fix[a] = next(iter(bs))
    for a in list(fix):                     # follow chains to the end (bounded)
        b, n = fix[a], 0
        while b in fix and n < 10 and fix[b] != a:
            b, n = fix[b], n + 1
        fix[a] = b
    report['edition_canonical_fixes_loaded'] = len(fix)
    return fix, rows


def apply_canonical_fixes(cites, cited_as, fix, report):
    """Move thesis and JSTOR citations of a fixed canonical work (a translation) to the original, as the roll-up of
    translations does: thesis-edition / jstor-edition source, edition true unless the citing work also cites the
    original directly, cited_as = the translation key. Crossref edges (no roll-up) are left alone."""
    move = [(a, b) for (a, b) in cites if b in fix]
    for a, b in move:
        v = cites.pop((a, b))
        ca = cited_as.pop((a, b), set())
        t = fix[b]
        if a == t:
            report['edition_canonical_fix_self_cite_dropped'] += 1
            continue
        src = v >> 1
        nsrc = (16 if src & THESIS_BITS else 0) | (64 if src & (2 | 32 | 64) else 0)
        old = cites.get((a, t))
        report['edition_canonical_fix_cites_moved' if old is None else 'edition_canonical_fix_cites_merged'] += 1
        if src & THESIS_BITS:
            report['edition_canonical_fix_thesis_cites'] += 1
        cites[(a, t)] = cites_code(True, nsrc, old)
        cited_as.setdefault((a, t), set()).update(ca | {b})


def series_editor_measure(ve_rows, publisher_of, er, contributed, report):
    """Crossref editor lists sometimes name series editors. Counted measure: people linked as volume editor through
    Crossref on 3+ volumes of one publisher, and how many of them edition-roles or CONTRIBUTED already flag as series
    editor somewhere."""
    flagged = {p for (p, w, c), (role, _) in er.items() if role == 'series-editor'} | {r['from'] for r in contributed
                                                                                       if (r['basis'] or '').startswith('series')}
    by = defaultdict(set)
    nopub = 0
    for r in ve_rows:
        if r['source'] != 'volume-editors:crossref':
            continue
        pub = publisher_of.get(r['vol_id']) or publisher_of.get(r['to'])
        if not pub:                 # no publisher named: the DOI's registrant and ISBN publisher block (10.1515/9780295...)
            m = re.match(r'doi:(10\.\d+)/(97[89]\d{4})', r['vol_id'])
            pub = f'doi-block {m.group(1)}/{m.group(2)}' if m else None
        if not pub:
            nopub += 1
            continue
        by[r['from'], pub.strip().lower()].add(r['to'])
    many = {k: v for k, v in by.items() if len(v) >= 3}
    people = {p for p, _ in many}
    report['volume_editors_series_risk'] = dict(
        note=('Crossref volume-editor credits (EDITED evidence linked, source volume-editors:crossref) of one person on 3+ '
              'volumes of one publisher (publisher from author-works/volumes.csv.gz and work-containers.csv.gz); '
              'flagged = also a series editor in edition-roles or CONTRIBUTED. After the series-editor rule (rows it flags '
              'are CONTRIBUTED, not counted here; audit in data/graph/volume-editors-report.json series_editor_rule): '
              'mostly serial annuals, yearbooks, reference works and prolific co-editors, which are real editors'),
        crossref_rows=sum(1 for r in ve_rows if r['source'] == 'volume-editors:crossref'),
        crossref_rows_no_publisher=nopub,
        person_publisher_pairs_3plus=len(many), people_3plus=len(people),
        volumes_3plus=sum(len(v) for v in many.values()),
        people_3plus_flagged_series_editor=len(people & flagged),
        top=sorted(([p, pub, len(v)] for (p, pub), v in many.items()), key=lambda x: -x[2])[:15])


def class_measures(out, report):
    """Classes 15 and 17 (ARCHITECTURE.md §8), republished each build from the loaded tables (DuckDB on the Parquet
    just written) and from the edition-roles and work-years reports."""
    import duckdb
    db = duckdb.connect()
    db.execute(f"SET memory_limit = '3GB'; SET threads = 3; SET temp_directory = '{out}/duckdb-tmp'; SET preserve_insertion_order = false")
    ex = "('" + "','".join(EDITION_ROLE_SET) + "')"
    db.execute(f"""CREATE TABLE tw AS SELECT DISTINCT "from" src, "to" dst FROM '{out}/cites.parquet'
                   WHERE source LIKE '%thesis%'""")
    db.execute(f"""CREATE TABLE cred AS SELECT "from" AS person, "to" AS work, 'authored' AS credit, role FROM '{out}/authored.parquet'
                   UNION ALL SELECT "from", "to", 'edited', role FROM '{out}/edited.parquet'""")
    db.execute(f"""CREATE TABLE pt AS SELECT c.person, t.src, bool_or(c.role NOT IN {ex}) own,
                   bool_or(c.credit = 'authored' AND c.role NOT IN {ex}) au FROM cred c JOIN tw t ON t.dst = c.work GROUP BY 1, 2""")
    db.execute("CREATE TABLE rk AS SELECT person, count(*) n, rank() OVER (ORDER BY count(*) DESC) r FROM pt GROUP BY 1")
    c15 = dict(note=('cited people = person keys with a credit on a work a thesis cites (AUTHORED and EDITED, any evidence); '
                     'counting = credits whose role is not edition-editor, translator, introducer, series-editor or contributor (those '
                     'prepared someone else\'s work and are not citations of the person\'s own)'))
    c15['cited_people_all_credits'], c15['cited_people_counting'] = db.execute(
        'SELECT count(DISTINCT person), count(DISTINCT person) FILTER (WHERE own) FROM pt').fetchone()
    c15['person_thesis_pairs_all'], c15['person_thesis_pairs_counting'] = db.execute(
        'SELECT count(*), count(*) FILTER (WHERE own) FROM pt').fetchone()
    c15['top500_half_or_more_via_edition_roles'] = db.execute("""SELECT count(*) FROM (SELECT p.person, count(*) n,
        count(*) FILTER (WHERE NOT own) lost FROM pt p JOIN rk USING (person) WHERE rk.r <= 500 GROUP BY 1) WHERE lost >= 0.5 * n""").fetchone()[0]
    c15['top500_half_or_more_not_authored_counting'] = db.execute("""SELECT count(*) FROM (SELECT p.person, count(*) n,
        count(*) FILTER (WHERE NOT au) e FROM pt p JOIN rk USING (person) WHERE rk.r <= 500 GROUP BY 1) WHERE e >= 0.5 * n""").fetchone()[0]
    c15['credits_by_role'] = {f'{a}:{b}': n for a, b, n in db.execute(
        'SELECT credit, role, count(*) FROM cred GROUP BY 1, 2 ORDER BY 1, 3 DESC').fetchall()}
    try:
        er = json.loads((ER_DIR / 'report.json').read_text())
        c15['edition_roles_report'] = {k: er.get(k) for k in ('top500_half_or_more_via_edition_roles',
                                       'top500_half_or_more_via_any_edited_before', 'theses_with_edition_credit_pairs',
                                       'proposed_authored_rows', 'lc_author_conflicts')}
        c15['edition_roles_report']['audit'] = {k: er.get('audit', {}).get(k) for k in
                                                ('edition_editor_precision_final', 'volume_editor_precision_final')}
    except (OSError, ValueError):
        pass
    db.execute(f"""CREATE TABLE wy AS SELECT key, year, first_year FROM '{out}/work.parquet'""")
    c17 = dict(note='thesis citations (thesis CITES pairs) of a work dated after the thesis year + 1, by the key year and by '
                    'coalesce(first_year, year)')
    c17['thesis_pairs_dated'], c17['after_thesis_by_year'], c17['after_thesis_by_first_year'] = db.execute("""
        SELECT count(*), count(*) FILTER (WHERE w.year > t.year + 1),
               count(*) FILTER (WHERE coalesce(w.first_year, w.year) > t.year + 1)
        FROM tw JOIN wy t ON t.key = tw.src JOIN wy w ON w.key = tw.dst WHERE t.year IS NOT NULL AND w.year IS NOT NULL""").fetchone()
    try:
        wy = json.loads(WY_REPORT.read_text())
        c17['work_years_report'] = dict(anachronisms={k: v for k, v in wy.get('anachronisms', {}).items() if k != 'by_cause'},
                                        canonical_fixes={k: v for k, v in wy.get('canonical_fixes', {}).items()
                                                         if not k.startswith('veyne')})
    except (OSError, ValueError):
        pass
    db.close()
    shutil.rmtree(Path(out) / 'duckdb-tmp', ignore_errors=True)
    report['class_15_edition_roles'] = c15
    report['class_17_reprint_years'] = c17


def defect_counts(works, rels, wp_linked, cites):
    """Gap measures each rebuild should shrink (owner 2026-11-11: keep issues visible; defect classes in
    data/identifiers/work-people-2026-11-11/defect-classes.json)."""
    auth = defaultdict(set)
    claims = Counter()
    for r in rels['AUTHORED']:
        auth[r['to']].add(r['from'])
        claims[r['from'], r['to']] += 1
    lauth = defaultdict(set)
    for r in wp_linked:
        lauth[r['to']].add(r['from'])
    kind = {w['key']: w['kind'] for w in works}
    jstor_citing = {a for (a, b), v in cites.items() if (v >> 1) & (2 | 32 | 64)}   # jstor-edition too (2026-11-12)
    reviews_of = {r['from'] for r in rels['REVIEWS']}
    printed = {w['key'] for w in works if w['reviewer_names']}
    keyed = [w for w in works if w['resolution'] != 'unkeyed']
    return {
        '1_jstor_citing_article_no_author': dict(key_log=sum(1 for w in jstor_citing if not auth.get(w)),
                                                 with_linked=sum(1 for w in jstor_citing if not auth.get(w) and not lauth.get(w)),
                                                 articles=len(jstor_citing)),
        '1b_keyed_article_no_author': dict(key_log=sum(1 for w in keyed if w['kind'] == 'article' and not auth.get(w['key'])),
                                           with_linked=sum(1 for w in keyed if w['kind'] == 'article' and not auth.get(w['key']) and not lauth.get(w['key']))),
        '2_review_printed_reviewer_no_key': dict(key_log=sum(1 for w in printed if not auth.get(w)),
                                                 with_linked=sum(1 for w in printed if not auth.get(w) and not lauth.get(w)),
                                                 reviews=len(reviews_of)),
        '7_person_work_claimed_twice': sum(1 for n in claims.values() if n > 1),
        '8_article_or_other_without_journal': dict(
            key_log=sum(1 for w in keyed if w['kind'] in ('article', 'other') and not (w['journal'] and w.get('journal_source') == 'keylog')),
            with_filled=sum(1 for w in keyed if w['kind'] in ('article', 'other') and not w['journal'])),
        '8b_orcid_record_only_works': sum(1 for w in keyed if w['anchors'] and all(a.startswith('orcid-work:') for a in w['anchors'])),
    }


def write(name, rows, schema):
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, OUT / f'{name}.parquet')
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--db', action='store_true', help='also load the tables into LadybugDB')
    ap.add_argument('--replay', action='store_true', help='replay the whole log instead of reading the SQLite cache')
    ap.add_argument('--out', type=Path, help='write the tables here instead of build/graph (a check build)')
    ap.add_argument('--untracked-ok', action='store_true',
                    help='with --out: read data/graph/cited-works even before it is in git (a check build)')
    args = ap.parse_args()
    global OUT
    if args.out:
        if args.db:
            sys.exit('--db writes build/graph/historiography.lbug; leave --out off')
        OUT = args.out
    elif args.untracked_ok:
        sys.exit('--untracked-ok is for check builds; give --out')
    shards = sorted(args.state.glob('events-*.jsonl*'))
    article_parts = sorted(CROSSREF_ARTICLES.glob('part-*.csv.gz'))
    crossref_parts = ([CROSSREF_CITES] if CROSSREF_CITES.exists() else []) + sorted(CROSSREF_PARTS.glob('part-*.csv.gz'))
    cited_files = cited_parts('works') + cited_parts('cites') + cited_parts('authors')
    cited_files += [CITED / 'report.json'] if cited_files else []
    edition_files = [CITED / 'editions.csv.gz'] if (CITED / 'editions.csv.gz').exists() else []
    jc_files = [JSTOR_CITED / n for n in ('works.csv.gz', 'cites.csv.gz') if (JSTOR_CITED / n).exists()]
    wp_files = sorted(WORK_PEOPLE.glob('part-*.csv.gz'))
    aw_files = [AUTHOR_WORKS / f'{n}.csv.gz' for n in ('works', 'authors', 'existing', 'volumes')]
    aw_files = aw_files if all(p.exists() for p in aw_files) else []
    fact_files = [p for p in (WORK_CONTAINERS, WORK_JOURNALS) if p.exists()]
    fact_files = fact_files if len(fact_files) == 2 else []
    # 2026-11-12: volume editors, edition roles, first years, canonical fixes, missing LC authors, LC author conflicts
    pass4 = {p: p.exists() for p in (VOLUME_EDITORS, EDITION_ROLES, WORK_YEARS, EDITION_FIXES, MISSING_AUTHORS, LC_CONFLICTS)}
    pass4_files = [p for p, ok in pass4.items() if ok]
    require_tracked(shards + [CITES] + [p for p in (JSTOR_CITES, AFFILIATIONS) if p.exists()] + crossref_parts + article_parts
                    + ([] if args.untracked_ok else cited_files + edition_files + jc_files + wp_files + aw_files + fact_files
                       + pass4_files))
    state = ReplayView(args.state) if args.replay else CacheView(args.state)
    OUT.mkdir(parents=True, exist_ok=True)
    report = Counter()

    types = {}
    people, works, insts = [], [], []
    for k, t, label, resolution, anchors in state.nodes():
        types[k] = t
        anchors = sorted(anchors)
        members = state.members(k)
        base = dict(key=k, label=label, resolution=resolution, anchors=anchors)
        if t == 'person':
            people.append(dict(base, **{s: first(anchors, s) for s in SCHEMES if s != 'ror'}))
        elif t == 'work':
            works.append(dict(base, kind=work_kind(anchors, members), lccn=first(anchors, 'lccn'),
                              year=year_of(members, 'year:') or year_of(members, 'lc-first-year:'),
                              # a review's reviewers as printed (key_jstor_reviews: no name-only person keys)
                              reviewer_names=sorted(m.split(':', 1)[1] for m in members if m.startswith('reviewer-name:')),
                              journal=next((m.split(':', 1)[1] for m in members if m.startswith('journal:')), None)))
        elif t == 'institution':
            insts.append(dict(base, ror=first(anchors, 'ror')))
    # unkeyed citing articles (Crossref): a node unless the key log has since keyed the DOI (then the key stands)
    unkeyed = set()
    for part in article_parts:
        with gzip.open(part, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                k = f"doi:{r['doi']}"
                if state.lookup(k) or k in unkeyed:
                    report['crossref_articles_keyed_since'] += 1
                    continue
                unkeyed.add(k)
                types[k] = 'work'
                works.append(dict(key=k, label=r['title'] or None, resolution='unkeyed', anchors=[k], kind='article',
                                  lccn=None, year=int(r['year']) if r['year'] else None, reviewer_names=[],
                                  journal=r['journal'] or None))
    report['Work_unkeyed_articles'] = len(unkeyed)
    # cited works matched 2026-11-10 (data/graph/cited-works): unkeyed Work nodes unless the log holds an identifier
    cited_index = {}
    cited_key = cited_work_nodes(state, types, works, unkeyed, report, cited_index) if cited_files else {}
    # JSTOR notes matched 2026-11-11 (data/graph/jstor-cited-works): unkeyed Work nodes unless held already
    jstor_key, jstor_lc = jstor_cited_nodes(state, types, works, unkeyed, cited_index, report) if jc_files else ({}, {})
    for w in works:                 # where a work's journal comes from (the key log, or the table that made the node)
        if w['journal']:
            w['journal_source'] = w.get('journal_source') or ('keylog' if w['resolution'] != 'unkeyed' else 'node-source')
    wi = {w['key']: w for w in works}
    resolve = work_resolver(state, types, unkeyed, cited_index)
    # works by keyed people absent from the graph and the volumes chapters are in (data/graph/author-works, 2026-11-11)
    vol_key, aw_key, aw_part, aw_long = (author_work_nodes(state, types, works, wi, unkeyed, resolve, report) if aw_files
                                         else ({}, {}, [], set()))
    if fact_files:                  # journal, ISSN, proposed kind of keyed works (export_work_containers.py)
        work_facts(state, types, wi, report)
    if pass4[WORK_YEARS]:           # first publication year beside `year` (2026-11-12)
        work_years(wi, resolve, report)
    # volume editors (2026-11-12): editors_printed on the node now; the EDITED rows are merged with the other credits
    ve_rows, ve_cands, ve_series = volume_editors(state, types, resolve, wi, report) if pass4[VOLUME_EDITORS] else ([], [], [])
    del wi
    s, L = pa.string(), pa.list_(pa.string())
    report['Person'] = write('person', people, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L)] +
                                                        [(x, s) for x in SCHEMES if x != 'ror']))
    report['Work'] = write('work', works, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L),
                                                    ('kind', s), ('lccn', s), ('year', pa.int32()),
                                                    ('reviewer_names', L), ('journal', s), ('issn', s),
                                                    ('journal_source', s), ('kind_proposed', s), ('isbn', s),
                                                    ('editors_printed', s), ('first_year', pa.int32()),
                                                    ('first_year_catalogue', pa.int32()), ('first_year_basis', s)]))
    report['Institution'] = write('institution', insts, pa.schema([('key', s), ('label', s), ('resolution', s),
                                                                  ('anchors', L), ('ror', s)]))

    rels = defaultdict(list)
    for claim, subj, pred, obj, resolution in state.relations():
        if len(subj) != 1 or len(obj) != 1:
            report[f'{pred}_unresolved'] += 1
            continue
        a, b = subj[0], obj[0]
        want = PREDICATES.get(pred, ('person', 'work'))
        if (types.get(a), types.get(b)) != want:
            report[f'{pred}_wrong_types'] += 1
            continue
        rels[pred.upper()].append({'from': a, 'to': b, 'claim': claim, 'resolution': resolution})
    rel_schema = pa.schema([('from', s), ('to', s), ('claim', s), ('resolution', s)])
    # the cited works' authors (exact/linked credited, possible kept apart); the derived tables below read the
    # key log's claims only
    linked, possible_authors, best_state = cited_authors(state, types, cited_key, rels, report) if cited_key else ({}, [], {})
    wp_linked, wp_possible, wp_counts, contributed = work_people(state, types, rels, report) if wp_files else ([], [], Counter(), [])
    if aw_files:
        aw_linked, aw_cands = author_work_credits(state, types, {(r['from'], r['to']) for r in rels['AUTHORED']},
                                                  aw_key, resolve, report)
    else:
        aw_linked, aw_cands = [], []
    if jstor_lc:                    # the LC main entry of a JSTOR-matched unkeyed work, by its name authority id
        linked = dict(linked)
        have = {(x['from'], x['to']) for x in linked.get('AUTHORED', [])}
        add = []
        for w, lcn in jstor_lc.items():
            if ':' not in w:        # a keyed work: authors come from the key log
                continue
            ks = [k for k in state.lookup(f'lcnaf:{lcn}') if types.get(k) == 'person']
            if len(ks) != 1:
                report['jstor_cited_lc_author_unresolved'] += 1
            elif (ks[0], w) not in have:
                have.add((ks[0], w))
                add.append({'from': ks[0], 'to': w, 'claim': 'jstor-matched:lc:exact', 'resolution': 'linked',
                            'source': 'jstor-matched:lc', 'state': 'exact'})
        report['jstor_cited_lc_author_linked'] = len(add)
        linked['AUTHORED'] = list(linked.get('AUTHORED', [])) + add
    if wp_files:
        linked = dict(linked)
        cw_have = {(x['from'], x['to']) for x in linked.get('AUTHORED', [])}
        linked['AUTHORED'] = list(linked.get('AUTHORED', [])) + [r for r in wp_linked if (r['from'], r['to']) not in cw_have]
        pa_have = {(r['from'], r['to']) for r in possible_authors}
        possible_authors = possible_authors + [r for r in wp_possible if (r['from'], r['to']) not in pa_have]
    if aw_files:                    # ORCID credits of the author-works table (2026-11-11)
        linked = dict(linked)
        cw_have = {(x['from'], x['to']) for x in linked.get('AUTHORED', [])}
        linked['AUTHORED'] = list(linked.get('AUTHORED', [])) + [r for r in aw_linked if (r['from'], r['to']) not in cw_have]
        report['aw_credits_already_linked'] = sum(1 for r in aw_linked if (r['from'], r['to']) in cw_have)
        skip = {(r['from'], r['to']) for r in possible_authors} | {(r['from'], r['to']) for r in linked['AUTHORED']}
        possible_authors = possible_authors + [r for r in aw_cands if (r['from'], r['to']) not in skip]
        del cw_have, skip
    # 2026-11-12 (integration pass four): roles of credits, missing LC main-entry authors, LC author conflicts, volume
    # editors. Key-log rows are never dropped or rewritten: the role qualifies a credit, the evidence stays.
    er = edition_roles() if pass4[EDITION_ROLES] else {}
    linked = dict(linked)
    linked['AUTHORED'] = list(linked.get('AUTHORED', []))
    linked['EDITED'] = list(linked.get('EDITED', []))

    def person1(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'person'] if name else []
        return ks[0] if len(ks) == 1 else None
    if pass4[MISSING_AUTHORS]:      # the LC main entry of an edition-role work, keyed but not credited (edition_roles.py)
        have = {(r['from'], r['to']) for r in rels['AUTHORED']} | {(x['from'], x['to']) for x in linked['AUTHORED']}
        add = []
        for r in read_rows(MISSING_AUTHORS):
            k, w = person1(r['person']), resolve(r['work'])
            if not k or not w:
                report['missing_authors_unresolved'] += 1
                continue
            if (k, w) in have:
                report['missing_authors_already_credited'] += 1
                continue
            have.add((k, w))
            add.append({'from': k, 'to': w, 'claim': f"edition-roles:lc-main-entry:{r['lcnaf']}", 'resolution': 'linked',
                        'source': 'edition-roles:lc-main-entry', 'state': 'exact', 'role': 'author',
                        'role_basis': 'lc-main-entry'})
        report['missing_authors_AUTHORED_added'] = len(add)
        linked['AUTHORED'] += add
        del have, add
    if pass4[LC_CONFLICTS]:         # a linked authored credit on a book whose LC main entry is someone else: a candidate
        conf, open_keylog = {}, 0
        for r in read_rows(LC_CONFLICTS):
            if r['evidence'] != 'linked':
                open_keylog += 1
                continue
            k, w = person1(r['person']), resolve(r['work'])
            if k and w:
                conf[k, w] = r
        keep, dem = [], []
        for x in linked['AUTHORED']:
            (dem if (x['from'], x['to']) in conf else keep).append(x)
        linked['AUTHORED'] = keep
        pa_have = {(r['from'], r['to']) for r in possible_authors}
        for x in dem:
            r = conf[x['from'], x['to']]
            if (x['from'], x['to']) not in pa_have:
                possible_authors.append({'from': x['from'], 'to': x['to'], 'n_candidates': 1, 'signals': r['basis'] or None,
                                         'source': x['source'], 'role': 'author',
                                         'reason': f"linked credit ({x['source']}) demoted: the LC main entry is "
                                                   f"{r['lc_main_entry'] or 'another person'} and this person is not in the LC record"})
        report['lc_author_conflicts'] = dict(
            note=('data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz (not audited): linked credits demoted to '
                  'author_candidates; key-log credits left as they are (an open measure)'),
            linked_in_table=len(conf), linked_demoted=len(dem), keylog_open=open_keylog)
        del keep, dem, pa_have, conf
    if ve_series:                   # series editors named in Crossref editor lists (class 19): contributors, not editors
        have_c = {(r['from'], r['to']) for r in contributed}
        add = [r for r in ve_series if (r['from'], r['to']) not in have_c]
        report['volume_editors_series_editor_contributed_added'] = len(add)
        contributed = list(contributed) + add
        del have_c, add
    ve_auth_role, ve_loaded = {}, []
    if ve_rows or ve_cands:         # volume editors: EDITED rows, unless the pair is a series editorship, a contributor,
        # or an AUTHORED credit (then the AUTHORED row gets role volume-editor: ORCID 'edited-book' records)
        auth_pairs = {(r['from'], r['to']) for r in rels['AUTHORED']} | {(x['from'], x['to']) for x in linked['AUTHORED']}
        ed_keylog = {(r['from'], r['to']) for r in rels['EDITED']}
        series = {(p, w) for (p, w, c), (role, _) in er.items() if role == 'series-editor'}
        # CONTRIBUTED pairs and edition-roles 'contributor' credits (a qualified editor of the volume, class 23)
        contrib = {(r['from'], r['to']) for r in contributed} | {(p, w) for (p, w, c), (role, _) in er.items() if role == 'contributor'}
        ed_have = {(x['from'], x['to']) for x in linked['EDITED']}
        for r in ve_rows:
            p = (r['from'], r['to'])
            if p in ed_keylog:
                report['volume_editors_already_keylog_edited'] += 1
            elif p in series or p in contrib:
                report['volume_editors_skipped_series_editor' if p in series else 'volume_editors_skipped_contributor'] += 1
            elif p in auth_pairs:
                ve_auth_role.setdefault(p, r['role_basis'])
                report[f"volume_editors_on_authored|{r['state']}"] += 1
            elif p in ed_have:
                report['volume_editors_already_linked_edited'] += 1
            else:
                ed_have.add(p)
                ve_loaded.append(r)
        linked['EDITED'] += ve_loaded
        report['volume_editors_EDITED_added'] = len(ve_loaded)
        # a person already listed as a candidate author of the volume is listed again as candidate editor (role editor)
        skip = {(r['from'], r['to']) for r in possible_authors if r.get('role') == 'editor'} | auth_pairs | ed_keylog | ed_have
        add = [r for r in ve_cands if (r['from'], r['to']) not in skip]
        report['volume_editors_candidates_added'] = len(add)
        possible_authors = possible_authors + add
        del auth_pairs, ed_keylog, series, contrib, ed_have, skip, add, ve_rows, ve_cands
        publisher_of = {}
        for r in read_rows(AUTHOR_WORKS / 'volumes.csv.gz'):
            if r['publisher']:
                publisher_of[r['id']] = r['publisher']
        for r in read_rows(WORK_CONTAINERS):
            if r['container_publisher'] and r['volume_work']:
                publisher_of.setdefault(r['volume_work'], r['container_publisher'])
        series_editor_measure(ve_loaded, publisher_of, er, contributed, report)
        del publisher_of
    for name in ('SUPERVISED', 'PUBLISHED_AS', 'REVIEWS'):
        report[name] = write(name.lower(), rels[name], rel_schema)
    # PART_OF: the key log's chapter -> volume claims (evidence keylog) and the volume links of 2026-11-11 (evidence
    # linked, source and volume_basis; identity scripts read the keylog rows only, scripts/graph_tables.py)
    part_linked = volume_links(state, types, rels, vol_key, aw_part, resolve, report) if (aw_files and fact_files) else []
    report['PART_OF'] = write('part_of', [dict(r, evidence='keylog', source=None, volume_basis=None) for r in rels['PART_OF']]
                              + part_linked, pa.schema([('from', s), ('to', s), ('claim', s), ('resolution', s), ('evidence', s),
                                                        ('source', s), ('volume_basis', s)]))
    report['PART_OF_by_evidence'] = dict(keylog=len(rels['PART_OF']), linked=len(part_linked))
    del part_linked
    # CONTRIBUTED (Person -> Work): foreword writers and series editors printed on a work (work-people role contributor,
    # exact/linked); never authors (2026-11-11)
    report['CONTRIBUTED'] = write('contributed', contributed, pa.schema([
        ('from', s), ('to', s), ('claim', s), ('resolution', s), ('evidence', s), ('source', s), ('state', s), ('basis', s)]))
    # one edge type per relation (owner, 2026-11-11): AUTHORED and EDITED carry `evidence` -- 'keylog' for the key
    # log's claims, 'linked' for rule/identifier credits outside it (source and state say which). Identity scripts read
    # evidence = 'keylog' only; the linked rows never feed identity work.
    # role and role_basis (2026-11-12): the part a person had in the work. EDITED: edition-roles (default 'unknown';
    # volume-editors rows 'volume-editor'); AUTHORED: 'author' unless edition-roles names translator, introducer,
    # edition-editor, series-editor or volume-editor, or the volume-editors table credits the person as editor of that
    # volume (ORCID 'edited-book' records credited as authorship).
    ev_schema = pa.schema([('from', s), ('to', s), ('claim', s), ('resolution', s), ('evidence', s), ('source', s), ('state', s),
                           ('role', s), ('role_basis', s)])
    role_count = Counter()

    def role_of(name, r):
        f, t = r['from'], r['to']
        if name == 'EDITED':
            if r.get('role'):
                return r['role'], r.get('role_basis')
            x = er.get((f, t, 'edited'))
            return (x[0], x[1]) if x else ('unknown', None)
        x = er.get((f, t, 'authored'))
        if x and x[0] in AUTHORED_ROLES:
            return x
        vb = ve_auth_role.get((f, t))
        if vb:
            if x and x[0] == 'author':      # the LC main entry is the person: kept as author, counted
                role_count['authored_volume_editor_kept_author_by_lc'] += 1
                return x
            return 'volume-editor', vb
        if r.get('role'):
            return r['role'], r.get('role_basis')
        return 'author', (f'{x[0]}:{x[1]}' if x and x[0] != 'author' else (x[1] if x else None))
    # 2026-11-12 (class 22 follow-up): the derived edges read the role. AUTHORED credits under a role other than author
    # make no COAUTHORED pair and no REVIEWED edge; volume-editor credits (keylog or linked) join COEDITED instead;
    # linked EDITED credits as volume editor join COEDITED with evidence linked.
    not_author = {}                 # (person, work) -> role, AUTHORED rows whose role is not author
    linked_coeditor = set()         # (person, work) linked EDITED rows with an editor role (not an edition role)
    for name in ('AUTHORED', 'EDITED'):
        keyed = {(r['from'], r['to']) for r in rels[name]}
        lrows = [r for r in linked.get(name, []) if (r['from'], r['to']) not in keyed]
        report[f'{name}_linked_dropped_as_in_keylog'] = len(linked.get(name, [])) - len(lrows)
        rows_ = []
        for ev, src in (('keylog', rels[name]), ('linked', lrows)):
            for r in src:
                role, basis = role_of(name, r)
                if name == 'AUTHORED' and role not in ('author', 'author-editor'):
                    not_author[r['from'], r['to']] = role
                elif name == 'EDITED' and ev == 'linked' and role in ('volume-editor', 'author-editor', 'unknown'):
                    linked_coeditor.add((r['from'], r['to']))
                role_count[f'{name}|{ev}|{role}'] += 1
                rows_.append({'from': r['from'], 'to': r['to'], 'claim': r['claim'], 'resolution': r['resolution'],
                              'evidence': ev, 'source': r.get('source') if ev == 'linked' else None,
                              'state': r.get('state') if ev == 'linked' else None, 'role': role, 'role_basis': basis})
        report[name] = write(name.lower(), rows_, ev_schema)
        report[f'{name}_by_evidence'] = dict(keylog=len(rels[name]), linked=len(lrows))
        report[f'{name}_by_role'] = {k.split('|', 1)[1]: v for k, v in sorted(role_count.items()) if k.startswith(name + '|')}
        del rows_
    report['authored_volume_editor_kept_author_by_lc'] = role_count['authored_volume_editor_kept_author_by_lc']
    report['edition_roles_rows_loaded'] = len(er)
    del er
    keyed_pairs = {name: {(x['from'], x['to']) for x in rels[name]} for name in ('AUTHORED', 'EDITED')}
    linked = {name: [r for r in linked.get(name, []) if (r['from'], r['to']) not in keyed_pairs[name]] for name in ('AUTHORED', 'EDITED')}
    del keyed_pairs
    # candidate lists are not edges: unconfirmed name-compatible people for a work (never credited)
    cand_rows = write('author_candidates', possible_authors, pa.schema([
        ('from', s), ('to', s), ('n_candidates', pa.int32()), ('signals', s), ('source', s), ('role', s), ('reason', s)]))
    report['candidate_lists'] = dict(author_candidates=cand_rows)
    # authors of a work for the derived edges: AUTHORED credits with role author (2026-11-12); a volume editor,
    # edition editor, translator, introducer or series editor filed as AUTHORED is not a co-author of the work's
    # authors, and a review of the book does not make its reviewer a REVIEWED partner of theirs
    authors = defaultdict(set)
    auth_editors = defaultdict(set)           # key-log AUTHORED credits with role volume-editor: COEDITED
    lauth_editors = defaultdict(set)          # linked ones
    report['derived_not_author_credits'] = dict(Counter(not_author.values()))
    for r in rels['AUTHORED']:
        role = not_author.get((r['from'], r['to']))
        if role is None:
            authors[r['to']].add(r['from'])
        elif role == 'volume-editor':
            auth_editors[r['to']].add(r['from'])
    reviewed = sorted({(a, b, r['from'], r['to']) for r in rels['REVIEWS'] for a in authors[r['from']]
                       for b in authors[r['to']] if a != b})
    lauth_all = defaultdict(set)              # linked credits (cited works, work-people), for the merged derived edges
    for r in linked.get('AUTHORED', []):
        role = not_author.get((r['from'], r['to']))
        if role is None:
            lauth_all[r['to']].add(r['from'])
        elif role == 'volume-editor':
            lauth_editors[r['to']].add(r['from'])
    del not_author
    both_all = {w: authors.get(w, set()) | lauth_all.get(w, set()) for w in set(authors) | set(lauth_all)}
    rl = sorted({(a, b, r['from'], r['to']) for r in rels['REVIEWS'] for a in both_all.get(r['from'], ())
                 for b in both_all.get(r['to'], ()) if a != b} - set(reviewed))
    report['REVIEWED'] = write('reviewed', [{'from': a, 'to': b, 'review': rv, 'book': bk, 'evidence': 'keylog'} for a, b, rv, bk in reviewed]
                               + [{'from': a, 'to': b, 'review': rv, 'book': bk, 'evidence': 'linked'} for a, b, rv, bk in rl],
                               pa.schema([('from', s), ('to', s), ('review', s), ('book', s), ('evidence', s)]))
    report['REVIEWED_by_evidence'] = dict(keylog=len(reviewed), linked=len(rl))
    del rl
    # editor -> contributor: a volume's editors -> the authors of a chapter in it (user, 2026-11-05: editors of
    # books I've published in)
    editors = defaultdict(set)
    for r in rels['EDITED']:
        editors[r['to']].add(r['from'])
    editor_of = sorted({(e, a, r['from'], r['to']) for r in rels['PART_OF'] for e in editors[r['to']]
                        for a in authors[r['from']] if e != a})
    report['EDITOR_OF'] = write('editor_of', [{'from': e, 'to': a, 'chapter': c, 'volume': v} for e, a, c, v in editor_of],
                                pa.schema([('from', s), ('to', s), ('chapter', s), ('volume', s)]))
    # advisor -> student: a supervised thesis's authors, and Wikidata's person-to-person advised claims
    advised = {(r['from'], b): (r['claim'], r['to']) for r in rels['SUPERVISED'] for b in authors[r['to']] if b != r['from']}
    for r in rels['ADVISED']:
        advised.setdefault((r['from'], r['to']), (r['claim'], ''))
    report['ADVISED'] = write('advised', [{'from': a, 'to': b, 'claim': c, 'thesis': t} for (a, b), (c, t) in sorted(advised.items())],
                              pa.schema([('from', s), ('to', s), ('claim', s), ('thesis', s)]))

    # co-authors: people who authored the same works, once per pair, with how many works, the years and the
    # works (user, 2026-11-05: a count matters; several joint articles are an ongoing collaboration, not a one-off)
    year = {w['key']: w['year'] for w in works}
    from key_lc_works import title_key
    title = {w['key']: title_key(re.sub(r'\s+—\s+.*$', '', w['label'] or '')) or w['key'] for w in works}
    shared = defaultdict(set)
    for w, people_of in authors.items():
        for a in people_of:
            for b in people_of:
                if a < b:
                    shared[a, b].add(w)
    rows = []
    for (a, b), ws in sorted(shared.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        rows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                     'first_year': ys[0] if ys else None,
                     'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws)})
    # co-editors: people who edited the same volume, built as COAUTHORED is (user, 2026-11-05: editors in the network)
    # 2026-11-12: the key log's AUTHORED credits with role volume-editor are editors here too (evidence keylog); linked
    # EDITED credits with an editor role and linked AUTHORED credits with role volume-editor make linked pairs, as
    # COAUTHORED does (editor lists over 25 make none)
    eds_of = defaultdict(set)
    for r in rels['EDITED']:
        eds_of[r['to']].add(r['from'])
    for w, ks in auth_editors.items():
        eds_of[w] |= ks
    co_ed = defaultdict(set)
    for w, people_of in eds_of.items():
        for a in people_of:
            for b in people_of:
                if a < b:
                    co_ed[a, b].add(w)
    led_of = defaultdict(set)
    for p, w in linked_coeditor:
        led_of[w].add(p)
    for w, ks in lauth_editors.items():
        led_of[w] |= ks
    lco_ed = defaultdict(set)
    for w, lks in led_of.items():
        allk = eds_of.get(w, set()) | lks
        if len(allk) > 25:
            report['COEDITED_linked_skipped_long_lists'] += 1
            continue
        for a in allk:
            for b in allk:
                if a < b and not (a in eds_of.get(w, ()) and b in eds_of.get(w, ())):
                    lco_ed[a, b].add(w)
    erows = []
    for (a, b), ws in sorted(co_ed.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        lw = lco_ed.pop((a, b), set())
        erows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                      'first_year': ys[0] if ys else None, 'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws),
                      'evidence': 'keylog', 'linked_works': len(lw), 'linked_work_keys': sorted(lw)})
    nled = 0
    for (a, b), ws in sorted(lco_ed.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        erows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                      'first_year': ys[0] if ys else None, 'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws),
                      'evidence': 'linked', 'linked_works': len(ws), 'linked_work_keys': sorted(ws)})
        nled += 1
    report['COEDITED'] = write('coedited', erows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                           ('first_year', pa.int32()), ('last_year', pa.int32()), ('work_keys', L),
                                                           ('evidence', s), ('linked_works', pa.int32()), ('linked_work_keys', L)]))
    report['COEDITED_by_evidence'] = dict(keylog=len(erows) - nled, linked=nled,
                                          keylog_pairs_from_authored_volume_editor_credits=sum(
                                              1 for (a, b), ws in co_ed.items()
                                              if any(a in auth_editors.get(w, ()) or b in auth_editors.get(w, ()) for w in ws)))
    del eds_of, co_ed, led_of, lco_ed, auth_editors, lauth_editors, linked_coeditor
    # COAUTHORED: one row per pair. evidence 'keylog' when the pair shares a key-log work (works, titles, years and
    # work_keys are the key log's alone, as before; linked_works / linked_work_keys add the works that rest on a
    # linked credit); 'linked' when only linked credits join them. Author lists over 25 are no co-authorship (a review
    # section filed as one record).
    lshared = defaultdict(set)
    for w in lauth_all:
        if len(both_all[w]) > 25:
            report['COAUTHORED_linked_skipped_long_lists'] += 1
            continue
        if w in aw_long:            # an author-works record printing more than 25 authors
            report['COAUTHORED_linked_skipped_long_printed_lists'] += 1
            continue
        for a in both_all[w]:
            for b in both_all[w]:
                if a < b and not (a in authors.get(w, ()) and b in authors.get(w, ())):
                    lshared[a, b].add(w)
    for r in rows:
        lw = lshared.pop((r['from'], r['to']), set())
        r.update(evidence='keylog', linked_works=len(lw), linked_work_keys=sorted(lw))
    nlink = 0
    for (a, b), lws in sorted(lshared.items()):
        ys = sorted(y for w in lws if (y := year.get(w)))
        rows.append({'from': a, 'to': b, 'works': len(lws), 'titles': len({title.get(w, w) for w in lws}),
                     'first_year': ys[0] if ys else None, 'last_year': ys[-1] if ys else None, 'work_keys': sorted(lws),
                     'evidence': 'linked', 'linked_works': len(lws), 'linked_work_keys': sorted(lws)})
        nlink += 1
    report['COAUTHORED'] = write('coauthored', rows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                                ('first_year', pa.int32()), ('last_year', pa.int32()),
                                                                ('work_keys', L), ('evidence', s), ('linked_works', pa.int32()),
                                                                ('linked_work_keys', L)]))
    report['COAUTHORED_by_evidence'] = dict(keylog=len(rows) - nlink, linked=nlink,
                                            keylog_pairs_with_linked_works=sum(1 for r in rows if r['evidence'] == 'keylog' and r['linked_works']))
    del lauth_all, both_all, lshared

    awarded = []
    for w in works:
        for m in state.members(w['key']):
            if m.startswith('awarded-by:'):
                i = state.lookup(m.split(':', 1)[1])
                if len(i) == 1 and types.get(i[0]) == 'institution':
                    awarded.append({'from': w['key'], 'to': i[0]})
    report['AWARDED_BY'] = write('awarded_by', awarded, pa.schema([('from', s), ('to', s)]))

    possible = {}                   # (a, b) -> likelihood
    for person in people:
        for m in state.members(person["key"]):
            for prefix, like in (('possible-same:', 'possible'), ('very-likely-same:', 'very_likely')):
                if m.startswith(prefix):
                    o = state.lookup(m.split(':', 1)[1])
                    if len(o) == 1 and o[0] != person["key"] and types.get(o[0]) == 'person':
                        pair = tuple(sorted((person["key"], o[0])))
                        if possible.get(pair) != 'very_likely':
                            possible[pair] = like
    for person in people:           # a recorded 'not the same' outweighs either
        for m in state.members(person["key"]):
            if m.startswith('not-same:'):
                o = state.lookup(m.split(':', 1)[1])
                if len(o) == 1:
                    possible.pop(tuple(sorted((person["key"], o[0]))), None)
    aff = {}
    if AFFILIATIONS.exists():
        with gzip.open(AFFILIATIONS, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                pk, ik = state.lookup(r['person']), state.lookup(r['institution'])
                if len(pk) != 1 or len(ik) != 1 or types.get(pk[0]) != 'person' or types.get(ik[0]) != 'institution':
                    report['affiliations_unresolved'] += 1
                    continue
                yv = lambda v: int(v) if v else None
                akey = (pk[0], ik[0], r['source'])
                old = aff.get(akey)
                y0 = min([v for v in (yv(r['first_year']), old and old['first_year']) if v] or [None])
                y1 = max([v for v in (yv(r['last_year']), old and old['last_year']) if v] or [None])
                aff[akey] = {'from': pk[0], 'to': ik[0], 'source': r['source'], 'first_year': y0, 'last_year': y1,
                            'n': int(r['n']) + (old['n'] if old else 0), 'rank': r['rank'] or (old and old['rank']) or None,
                            'department': r['department'] or (old and old['department']) or None}
    report['AFFILIATED_WITH'] = write('affiliated_with', list(aff.values()), pa.schema([
        ('from', s), ('to', s), ('source', s), ('first_year', pa.int32()), ('last_year', pa.int32()), ('n', pa.int32()),
        ('rank', s), ('department', s)]))
    report['POSSIBLY_SAME'] = write('possibly_same', [{'from': a, 'to': b, 'likelihood': l} for (a, b), l in sorted(possible.items())],
                                    pa.schema([('from', s), ('to', s), ('likelihood', s)]))
    report['POSSIBLY_SAME_very_likely'] = sum(1 for l in possible.values() if l == 'very_likely')

    cites = {}                      # (citing, cited) -> edition only (True) or a direct match (False)
    cited_as = {}                   # (thesis, canonical work) -> the translation/edition nodes it was cited as
    with gzip.open(CITES, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            a, b = state.lookup(f'diss-thesis:{r["dissertation_id"]}'), state.lookup(r['work_key'])
            if len(a) == 1 and len(b) == 1 and types.get(a[0]) == types.get(b[0]) == 'work' and a[0] != b[0]:
                cites[(a[0], b[0])] = cites_code(False, 1, cites.get((a[0], b[0])))
            else:
                report['cites_unresolved'] += 1
    if cited_key:                   # dissertations citing the cited works of data/graph/cited-works
        corpus = json.loads((CITED / 'report.json').read_text())['corpus']
        cat_of = {}                 # graph key -> (source, best author state); works.csv names the source
        for path in cited_parts('works'):
            for r in read_rows(path):
                if r['id'] in cited_key:
                    i = best_state.get(r['id'])
                    cat_of[r['id']] = (r['source'], STATE_ORDER[i] if i is not None else
                                       'not-run' if r['source'].startswith('crossref') or r['source'] == 'journal-meta'
                                       else 'no-author-named')
        works_by, theses_by = Counter(cat_of.values()), defaultdict(set)

        def work_of(name):          # a cited-works id, else a key-log work (the canonical of a translation)
            if name in cited_key:
                return cited_key[name]
            ks = [k for k in state.lookup(name) if types.get(k) == 'work']
            return ks[0] if len(ks) == 1 else None
        later = []                  # translation/edition rows: after every plain row, so 'replaces' sees them all
        for path in cited_parts('cites'):
            for r in read_rows(path):
                a, b = state.lookup(f'diss-thesis:{r["dissertation_id"]}'), work_of(r['work'])
                if len(a) == 1 and b and types.get(a[0]) == 'work' and a[0] != b:
                    if r.get('cited_as'):
                        later.append((a[0], b, r))
                        continue
                    old = cites.get((a[0], b))
                    report['cites_from_cited_works' if old is None else 'cited_works_cites_already'] += 1
                    cites[(a[0], b)] = cites_code(False, 8, old)
                    if r['work'] in cat_of:
                        theses_by[cat_of[r['work']]].add(a[0])
                else:
                    report['cited_works_cites_unresolved'] += 1
        # a thesis citing a translation or later edition cites the canonical work: edition = true (unless the thesis
        # also cites it directly), cited_as = the node it was cited as; the older crosswalks' edge to that node is
        # dropped when no other corpus work of the thesis maps to it (export_cited_works `replaces`), so a moved
        # citation counts once
        for a, b, r in later:
            raw = [x for x in r['cited_as'].split(';') if x]
            prevs = [x for x in (work_of(y) or y for y in raw) if x != b] or raw   # all one key with b: keep the ids
            for x in r['replaces'].split(';'):
                k = work_of(x) if x else None
                if not k:
                    continue
                if cites.get((a, k)) == cites_code(False, 1):      # only the older crosswalks' thesis edge
                    del cites[(a, k)]
                    cited_as.pop((a, k), None)
                    report['edition_older_edge_dropped' if k != b else 'edition_older_edge_to_canonical_replaced'] += 1
                elif k != b:
                    report['edition_older_edge_kept'] += 1
            old = cites.get((a, b))
            report['cites_from_editions' if old is None else 'edition_cites_already'] += 1
            cites[(a, b)] = cites_code(True, 16, old)
            cited_as.setdefault((a, b), set()).update(prevs)
            if r['work'] in cat_of:
                theses_by[cat_of[r['work']]].add(a)
        del later
        thesis_pairs = sum(1 for v in cites.values() if (v >> 1) & THESIS_BITS)
        report['linkage'] = dict(
            note=('cited works matched 2026-11-10 (data/graph/cited-works) by source and by the best state of their '
                  'authors (exact/linked: credited in AUTHORED/EDITED with evidence linked; possible-one/-several: candidates, not credited; none: no keyed '
                  'person fits; no-author-named: no author row; not-run: Crossref works, not yet linked); citing_theses '
                  '= distinct dissertations. thesis_cites_pairs = (dissertation, work) CITES edges from the corpus '
                  '(older crosswalks and this table) over the corpus\'s citations; corpus_rate counts corpus rows '
                  '(export_cited_works report)'),
            by_source={src: {cat: dict(works=works_by[src, cat], citing_theses=len(theses_by[src, cat]))
                             for cat in STATE_ORDER + ('no-author-named', 'not-run') if works_by[src, cat]}
                       for src in sorted({s for s, _ in works_by})},
            corpus_citations=corpus['citations'], thesis_cites_pairs=thesis_pairs,
            thesis_cites_rate=round(thesis_pairs / corpus['citations'], 4),
            corpus_rows_matched=corpus['matched_after'], corpus_rate=corpus['rate_after'],
            corpus_rate_before=corpus['rate_before'],
            # export_cited_works' rate_with_compilations added every compilation row, also the 2,827 already matched;
            # the per-kind with_compilations counts are right (matched or a compilation, once), so their sum is used
            corpus_rate_with_compilations=(round(sum(v['with_compilations'] for v in corpus['by_kind'].values())
                                                 / corpus['citations'], 4) if corpus.get('by_kind') else None),
            corpus_rows_with_compilations=(sum(v['with_compilations'] for v in corpus['by_kind'].values())
                                           if corpus.get('by_kind') else None),
            corpus_rate_with_compilations_as_exported=corpus.get('rate_with_compilations'),
            corpus_moved_to_canonical=corpus.get('moved_citations'),
            corpus_by_kind={k: v['rate_after'] for k, v in corpus.get('by_kind', {}).items()},
            corpus_rate_brazil=corpus.get('by_country', {}).get('BR', {}).get('rate_after'))
        del theses_by
    name = 'jstor'                  # JSTOR articles citing keyed works
    if JSTOR_CITES.exists():
        with gzip.open(JSTOR_CITES, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                a, b = state.lookup(r['citing_work']), state.lookup(r['cited_work'])
                if len(a) == 1 and len(b) == 1 and types.get(a[0]) == types.get(b[0]) == 'work' and a[0] != b[0]:
                    report[f'cites_from_{name}'] += (a[0], b[0]) not in cites
                    ed = r.get('basis') == 'edition'      # cites a later edition or translation of the work
                    cites[(a[0], b[0])] = cites_code(ed, 2, cites.get((a[0], b[0])))
                    report[f'{name}_cites_edition'] += ed
                else:
                    report[f'{name}_cites_unresolved'] += 1
    if jc_files:                    # JSTOR notes matched 2026-11-11 (data/graph/jstor-cited-works)
        def jwork(name):
            if name in jstor_key:
                return jstor_key[name]
            if name in cited_index:
                return cited_index[name]
            ks = [k for k in state.lookup(name) if types.get(k) == 'work']
            return ks[0] if len(ks) == 1 else (name if name in unkeyed else None)
        for r in read_rows(JSTOR_CITED / 'cites.csv.gz'):
            a, b = jwork(r['citing_work']), jwork(r['cited_work'])
            if a and b and a != b:
                old = cites.get((a, b))
                if r.get('cited_as'):   # a note citing a translation or later edition: the canonical work (2026-11-11)
                    raw = [y for y in r['cited_as'].split(';') if y]
                    prevs = [x for x in (jwork(y) or y for y in raw) if x != b] or raw
                    report['cites_from_jstor_edition' if old is None else 'jstor_edition_cites_already'] += 1
                    cites[(a, b)] = cites_code(True, 64, old)
                    cited_as.setdefault((a, b), set()).update(prevs)
                    # the older JSTOR edge (jstor-cites.csv.gz) from this article to the translation/edition node is
                    # the same citation: dropped, as the thesis side's `replaces`, so a moved citation counts once
                    for x in prevs:
                        v = cites.get((a, x))
                        if v is not None and x != b and (v >> 1) == 2:
                            del cites[(a, x)]
                            cited_as.pop((a, x), None)
                            report['jstor_edition_replaced'] += 1
                    continue
                report['cites_from_jstor_matched' if old is None else 'jstor_matched_cites_already'] += 1
                cites[(a, b)] = cites_code(False, 32, old)
            else:
                report['jstor_matched_cites_unresolved'] += 1
    cites_schema = pa.schema([('from', s), ('to', s), ('edition', pa.bool_()), ('source', s), ('cited_as', s)])
    # canonical fixes (2026-11-12): a canonical work that is itself a translation while the original is known; its thesis
    # and JSTOR citations move to the original (as the translation roll-up) and EDITION_OF points to the original
    if pass4[EDITION_FIXES]:
        cfix, cfix_rows = canonical_fixes(state, types, cited_key, report)
        n0 = len(cites)
        apply_canonical_fixes(cites, cited_as, cfix, report)
        report['edition_canonical_fix_cites_pairs_removed'] = n0 - len(cites)
        if isinstance(report.get('linkage'), dict):
            report['linkage']['thesis_cites_pairs_after_canonical_fixes'] = sum(1 for v in cites.values() if (v >> 1) & THESIS_BITS)
    else:
        cfix, cfix_rows = {}, {}
    if edition_files:               # translation/edition node -> canonical work (EDITION_OF; keys are not merged)
        eo = {}
        for (a, b) in cfix.items():  # the fixed canonical -> the original
            r = cfix_rows[a]
            eo[a, b] = {'from': a, 'to': b, 'relation': 'translation', 'route': f"edition-canonical-fix:{r['basis']}",
                        'theses': int(r['theses_citing_current'] or 0)}
        for r in read_rows(CITED / 'editions.csv.gz'):
            b = cited_key.get(r['canonical']) if r['canonical'] in cited_key else (
                (lambda ks: ks[0] if len(ks) == 1 else None)([k for k in state.lookup(r['canonical']) if types.get(k) == 'work']))
            if b in cfix:
                report['edition_of_canonical_fixed'] += 1
                b = cfix[b]
            if not b or r['cited_as'].startswith('corpus:'):
                report['edition_of_skipped' if not b else 'edition_of_unmatched_before'] += 1
                continue
            a = cited_key.get(r['cited_as']) or next(iter([k for k in state.lookup(r['cited_as']) if types.get(k) == 'work'][:1]), None)
            if not a or a == b:
                report['edition_of_same_or_unresolved'] += 1
                continue
            e = eo.setdefault((a, b), {'from': a, 'to': b, 'relation': r['relation'], 'route': r['route'], 'theses': 0})
            e['theses'] += int(r['theses'] or 0)
        report['EDITION_OF'] = write('edition_of', list(eo.values()), pa.schema([
            ('from', s), ('to', s), ('relation', s), ('route', s), ('theses', pa.int32())]))
    if not crossref_parts:
        report['CITES'] = write('cites', [{'from': a, 'to': b, 'edition': bool(v & 1), 'source': source_names(v >> 1),
                                           'cited_as': ';'.join(sorted(cited_as[(a, b)])) if (a, b) in cited_as else None}
                                          for (a, b), v in sorted(cites.items())], cites_schema)
        report['CITES_edition_only'] = sum(v & 1 for v in cites.values())
    else:
        crossref_cites(cites, crossref_parts, state, types, unkeyed, report, cites_schema, cited_as)

    if wp_files:
        lk = report.get('linkage') or {}
        lk['work_people'] = dict(
            note=('printed people of keyed works (data/graph/work-people, scripts/link_work_people.py 2026-11-11): rows by role '
                  'and state as loaded; exact/linked join AUTHORED with evidence linked, possible author_candidates; none rows are not in '
                  'the table (counted in data/identifiers/work-people-2026-11-11/report.json)'),
            loaded={k: v for k, v in sorted(wp_counts.items())})
        lk['defects'] = defect_counts(works, rels, wp_linked, cites)
        report['linkage'] = lk
    del cites, cited_as, works, rels, linked, possible_authors
    class_measures(OUT, report)     # classes 15 and 17 from the tables just written (2026-11-12)
    if args.db:
        load_db(report)
    (OUT / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items())), indent=1))


def load_db(report):
    import ladybug as lb
    path = OUT / 'historiography.lbug'
    if path.exists():
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    for side in (path.with_suffix('.lbug.wal'),):
        if side.exists():
            side.unlink()
    conn = lb.Connection(lb.Database(str(path)))
    ids = 'anchors STRING[], lcnaf STRING, wd STRING, orcid STRING, gnd STRING, viaf STRING, isni STRING, idref STRING'
    conn.execute(f'CREATE NODE TABLE Person(key STRING, label STRING, resolution STRING, {ids}, PRIMARY KEY (key))')
    conn.execute('CREATE NODE TABLE Work(key STRING, label STRING, resolution STRING, anchors STRING[], kind STRING, '
                 'lccn STRING, year INT32, reviewer_names STRING[], journal STRING, issn STRING, journal_source STRING, '
                 'kind_proposed STRING, isbn STRING, editors_printed STRING, first_year INT32, first_year_catalogue INT32, '
                 'first_year_basis STRING, PRIMARY KEY (key))')
    conn.execute('CREATE NODE TABLE Institution(key STRING, label STRING, resolution STRING, anchors STRING[], '
                 'ror STRING, PRIMARY KEY (key))')
    for name in ('AUTHORED', 'EDITED'):
        conn.execute(f'CREATE REL TABLE {name}(FROM Person TO Work, claim STRING, resolution STRING, evidence STRING, '
                     'source STRING, state STRING, role STRING, role_basis STRING)')
    conn.execute('CREATE REL TABLE SUPERVISED(FROM Person TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PUBLISHED_AS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE REVIEWS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PART_OF(FROM Work TO Work, claim STRING, resolution STRING, evidence STRING, '
                 'source STRING, volume_basis STRING)')
    conn.execute('CREATE REL TABLE CONTRIBUTED(FROM Person TO Work, claim STRING, resolution STRING, evidence STRING, '
                 'source STRING, state STRING, basis STRING)')
    conn.execute('CREATE REL TABLE EDITOR_OF(FROM Person TO Person, chapter STRING, volume STRING)')
    conn.execute('CREATE REL TABLE REVIEWED(FROM Person TO Person, review STRING, book STRING, evidence STRING)')
    conn.execute('CREATE REL TABLE ADVISED(FROM Person TO Person, claim STRING, thesis STRING)')
    conn.execute('CREATE REL TABLE COEDITED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[])')
    conn.execute('CREATE REL TABLE COAUTHORED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[], evidence STRING, linked_works INT32, linked_work_keys STRING[])')
    conn.execute('CREATE REL TABLE AWARDED_BY(FROM Work TO Institution)')
    conn.execute('CREATE REL TABLE POSSIBLY_SAME(FROM Person TO Person, likelihood STRING)')
    conn.execute('CREATE REL TABLE AFFILIATED_WITH(FROM Person TO Institution, source STRING, first_year INT32, '
                 'last_year INT32, n INT32, rank STRING, department STRING)')
    conn.execute('CREATE REL TABLE CITES(FROM Work TO Work, edition BOOL, source STRING, cited_as STRING)')
    if (OUT / 'edition_of.parquet').exists():
        conn.execute('CREATE REL TABLE EDITION_OF(FROM Work TO Work, relation STRING, route STRING, theses INT32)')
    for table, file in (('Person', 'person'), ('Work', 'work'), ('Institution', 'institution'),
                        ('AUTHORED', 'authored'), ('EDITED', 'edited'), ('SUPERVISED', 'supervised'),
                        ('PUBLISHED_AS', 'published_as'), ('REVIEWS', 'reviews'), ('PART_OF', 'part_of'), ('EDITOR_OF', 'editor_of'), ('REVIEWED', 'reviewed'), ('ADVISED', 'advised'),
                        ('COAUTHORED', 'coauthored'), ('COEDITED', 'coedited'),
                        ('AWARDED_BY', 'awarded_by'), ('POSSIBLY_SAME', 'possibly_same'), ('AFFILIATED_WITH', 'affiliated_with'),
                        ('CITES', 'cites'), ('CONTRIBUTED', 'contributed')):
        conn.execute(f"COPY {table} FROM '{OUT / (file + '.parquet')}'")
    if (OUT / 'edition_of.parquet').exists():
        conn.execute(f"COPY EDITION_OF FROM '{OUT / 'edition_of.parquet'}'")
    report['db'] = str(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
