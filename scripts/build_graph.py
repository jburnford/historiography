"""The key log as a queryable graph: Parquet tables and an embedded LadybugDB (Cypher) database (2026-11-02).

The key log (data/identifiers/events-*.jsonl, closed shards gzipped) is the source of truth in git; this builds a local, disposable
view of it that anyone can rebuild from a clean clone. It reads only files tracked in git (it stops if an input
is untracked) and writes to build/graph/ (git-ignored):
- nodes: `Person`, `Work`, `Institution` (active keys; identifiers by scheme as columns, all anchors as a list);
- relations from the log's claims: `AUTHORED`, `EDITED`, `SUPERVISED` (Person -> Work), `PUBLISHED_AS` and
  `REVIEWS` (Work -> Work: a review and the book it reviews), with the claim key and its resolution; claims
  whose endpoints do not resolve to one key each are left out and counted;
- `COEDITED` (Person -> Person, once per pair), derived as COAUTHORED from shared EDITED volumes;
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
# CITES sources, as bits (one int per edge in the build: edition-only flag in bit 0, sources above it)
SRC = (('thesis', 1), ('jstor', 2), ('crossref', 4), ('thesis-matched', 8))
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


def crossref_cites(cites, parts, state, types, unkeyed, report, schema):
    """CITES with the Crossref parts (tens of millions of rows) joined in DuckDB, not a Python dict: each distinct name
    is resolved once (State.lookup; an unkeyed citing article is its own node), then the edges are joined, folded with
    the dissertation and JSTOR edges (edition only when every source says edition) and written straight to Parquet."""
    import duckdb
    db = duckdb.connect()
    db.execute(f"SET memory_limit = '4GB'; SET temp_directory = '{OUT}/duckdb-tmp'; SET preserve_insertion_order = false")
    files = [str(p) for p in parts]
    db.execute(f"""CREATE TABLE xr AS SELECT citing_work, cited_work, basis = 'edition' AS ed, 4::TINYINT AS src FROM read_csv({files}, header = true,
                   columns = {{'citing_work': 'VARCHAR', 'cited_work': 'VARCHAR', 'citations': 'INTEGER', 'basis': 'VARCHAR'}})""")
    names, keys = [], []
    for (n,) in db.execute('SELECT DISTINCT citing_work FROM xr UNION SELECT DISTINCT cited_work FROM xr').fetchall():
        k = state.lookup(n) or ([n] if n in unkeyed else [])
        if len(k) == 1 and types.get(k[0]) == 'work':
            names.append(n); keys.append(k[0])
    db.register('name_map', pa.table({'name': names, 'key': keys}))
    del names, keys
    db.execute("""CREATE TABLE xr2 AS SELECT m1.key AS a, m2.key AS b, ed, src FROM xr
                  JOIN name_map m1 ON m1.name = xr.citing_work JOIN name_map m2 ON m2.name = xr.cited_work WHERE m1.key <> m2.key""")
    n_xr, n_xr2 = db.execute('SELECT count(*) FROM xr').fetchone()[0], db.execute('SELECT count(*) FROM xr2').fetchone()[0]
    report['crossref_cites_unresolved'] = n_xr - n_xr2
    report['crossref_cites_edition'] = db.execute('SELECT count(*) FROM xr2 WHERE ed').fetchone()[0]
    db.execute('DROP TABLE xr')
    db.register('base', pa.table({'a': [a for a, _ in cites], 'b': [b for _, b in cites],
                                  'ed': [bool(v & 1) for v in cites.values()],
                                  'src': pa.array([v >> 1 for v in cites.values()], pa.int8())}))
    report['cites_from_crossref'] = db.execute("""SELECT count(*) FROM (SELECT DISTINCT a, b FROM xr2) x
                                                  ANTI JOIN base USING (a, b)""").fetchone()[0]
    names = ' '.join(f"CASE WHEN m & {b} > 0 THEN '{n}' END," for n, b in SRC).rstrip(',')
    db.execute(f"""COPY (SELECT "from", "to", edition, concat_ws(',', {names}) AS source FROM (
                   SELECT a AS "from", b AS "to", bool_and(ed) AS edition, bit_or(src::TINYINT) AS m
                   FROM (SELECT a, b, ed, src FROM base UNION ALL SELECT a, b, ed, src FROM xr2) GROUP BY 1, 2) ORDER BY 1, 2)
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


def cited_work_nodes(state, types, works, unkeyed, report):
    """Work nodes for the cited works of data/graph/cited-works (two layers): the key the log gives one of the work's
    identifiers (its id, all its LCCNs, alias DOIs), else the id itself as an unkeyed node. Returns id -> graph key."""
    out = {}
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
            report['Work_unkeyed_cited_works'] += 1
    return out


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
    require_tracked(shards + [CITES] + [p for p in (JSTOR_CITES, AFFILIATIONS) if p.exists()] + crossref_parts + article_parts
                    + ([] if args.untracked_ok else cited_files))
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
    cited_key = cited_work_nodes(state, types, works, unkeyed, report) if cited_files else {}
    s, L = pa.string(), pa.list_(pa.string())
    report['Person'] = write('person', people, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L)] +
                                                        [(x, s) for x in SCHEMES if x != 'ror']))
    report['Work'] = write('work', works, pa.schema([('key', s), ('label', s), ('resolution', s), ('anchors', L),
                                                    ('kind', s), ('lccn', s), ('year', pa.int32()),
                                                    ('reviewer_names', L), ('journal', s)]))
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
    for name in ('AUTHORED', 'EDITED', 'SUPERVISED', 'PUBLISHED_AS', 'REVIEWS', 'PART_OF'):
        report[name] = write(name.lower(), rels[name], rel_schema)
    linked_schema = pa.schema([('from', s), ('to', s), ('claim', s), ('resolution', s), ('source', s), ('state', s)])
    for name in ('AUTHORED', 'EDITED'):
        report[f'LINKED_{name}'] = write(f'linked_{name.lower()}', linked.get(name, []), linked_schema)
    report['POSSIBLE_AUTHOR'] = write('possible_author', possible_authors, pa.schema([
        ('from', s), ('to', s), ('n_candidates', pa.int32()), ('signals', s), ('source', s), ('role', s)]))
    authors = defaultdict(set)
    for r in rels['AUTHORED']:
        authors[r['to']].add(r['from'])
    reviewed = sorted({(a, b, r['from'], r['to']) for r in rels['REVIEWS'] for a in authors[r['from']]
                       for b in authors[r['to']] if a != b})
    report['REVIEWED'] = write('reviewed', [{'from': a, 'to': b, 'review': rv, 'book': bk} for a, b, rv, bk in reviewed],
                               pa.schema([('from', s), ('to', s), ('review', s), ('book', s)]))
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
    eds_of = defaultdict(set)
    for r in rels['EDITED']:
        eds_of[r['to']].add(r['from'])
    co_ed = defaultdict(set)
    for w, people_of in eds_of.items():
        for a in people_of:
            for b in people_of:
                if a < b:
                    co_ed[a, b].add(w)
    erows = []
    for (a, b), ws in sorted(co_ed.items()):
        ys = sorted(y for w in ws if (y := year.get(w)))
        erows.append({'from': a, 'to': b, 'works': len(ws), 'titles': len({title.get(w, w) for w in ws}),
                      'first_year': ys[0] if ys else None, 'last_year': ys[-1] if ys else None, 'work_keys': sorted(ws)})
    report['COEDITED'] = write('coedited', erows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                           ('first_year', pa.int32()), ('last_year', pa.int32()), ('work_keys', L)]))
    report['COAUTHORED'] = write('coauthored', rows, pa.schema([('from', s), ('to', s), ('works', pa.int32()), ('titles', pa.int32()),
                                                                ('first_year', pa.int32()), ('last_year', pa.int32()),
                                                                ('work_keys', L)]))

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
                                       'not-run' if r['source'] == 'crossref' else 'no-author-named')
        works_by, theses_by = Counter(cat_of.values()), defaultdict(set)
        for path in cited_parts('cites'):
            for r in read_rows(path):
                a, b = state.lookup(f'diss-thesis:{r["dissertation_id"]}'), cited_key.get(r['work'])
                if len(a) == 1 and b and types.get(a[0]) == 'work' and a[0] != b:
                    old = cites.get((a[0], b))
                    report['cites_from_cited_works' if old is None else 'cited_works_cites_already'] += 1
                    cites[(a[0], b)] = cites_code(False, 8, old)
                    theses_by[cat_of[r['work']]].add(a[0])
                else:
                    report['cited_works_cites_unresolved'] += 1
        thesis_pairs = sum(1 for v in cites.values() if (v >> 1) & 9)
        report['linkage'] = dict(
            note=('cited works matched 2026-11-10 (data/graph/cited-works) by source and by the best state of their '
                  'authors (exact/linked: credited in LINKED_AUTHORED/LINKED_EDITED, not in AUTHORED/EDITED; possible-one/-several: candidates, not credited; none: no keyed '
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
            corpus_rate_before=corpus['rate_before'])
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
    cites_schema = pa.schema([('from', s), ('to', s), ('edition', pa.bool_()), ('source', s)])
    if not crossref_parts:
        report['CITES'] = write('cites', [{'from': a, 'to': b, 'edition': bool(v & 1), 'source': source_names(v >> 1)}
                                          for (a, b), v in sorted(cites.items())], cites_schema)
        report['CITES_edition_only'] = sum(v & 1 for v in cites.values())
    else:
        crossref_cites(cites, crossref_parts, state, types, unkeyed, report, cites_schema)

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
                 'lccn STRING, year INT32, reviewer_names STRING[], journal STRING, PRIMARY KEY (key))')
    conn.execute('CREATE NODE TABLE Institution(key STRING, label STRING, resolution STRING, anchors STRING[], '
                 'ror STRING, PRIMARY KEY (key))')
    for name in ('AUTHORED', 'EDITED', 'SUPERVISED'):
        conn.execute(f'CREATE REL TABLE {name}(FROM Person TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PUBLISHED_AS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE REVIEWS(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE PART_OF(FROM Work TO Work, claim STRING, resolution STRING)')
    conn.execute('CREATE REL TABLE EDITOR_OF(FROM Person TO Person, chapter STRING, volume STRING)')
    conn.execute('CREATE REL TABLE REVIEWED(FROM Person TO Person, review STRING, book STRING)')
    conn.execute('CREATE REL TABLE ADVISED(FROM Person TO Person, claim STRING, thesis STRING)')
    conn.execute('CREATE REL TABLE COEDITED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[])')
    conn.execute('CREATE REL TABLE COAUTHORED(FROM Person TO Person, works INT32, titles INT32, first_year INT32, last_year INT32, '
                 'work_keys STRING[])')
    conn.execute('CREATE REL TABLE AWARDED_BY(FROM Work TO Institution)')
    conn.execute('CREATE REL TABLE POSSIBLY_SAME(FROM Person TO Person, likelihood STRING)')
    conn.execute('CREATE REL TABLE AFFILIATED_WITH(FROM Person TO Institution, source STRING, first_year INT32, '
                 'last_year INT32, n INT32, rank STRING, department STRING)')
    conn.execute('CREATE REL TABLE CITES(FROM Work TO Work, edition BOOL, source STRING)')
    for name in ('LINKED_AUTHORED', 'LINKED_EDITED'):
        conn.execute(f'CREATE REL TABLE {name}(FROM Person TO Work, claim STRING, resolution STRING, source STRING, state STRING)')
    conn.execute('CREATE REL TABLE POSSIBLE_AUTHOR(FROM Person TO Work, n_candidates INT32, signals STRING, source STRING, '
                 'role STRING)')
    for table, file in (('Person', 'person'), ('Work', 'work'), ('Institution', 'institution'),
                        ('AUTHORED', 'authored'), ('EDITED', 'edited'), ('SUPERVISED', 'supervised'),
                        ('PUBLISHED_AS', 'published_as'), ('REVIEWS', 'reviews'), ('PART_OF', 'part_of'), ('EDITOR_OF', 'editor_of'), ('REVIEWED', 'reviewed'), ('ADVISED', 'advised'),
                        ('COAUTHORED', 'coauthored'), ('COEDITED', 'coedited'),
                        ('AWARDED_BY', 'awarded_by'), ('POSSIBLY_SAME', 'possibly_same'), ('AFFILIATED_WITH', 'affiliated_with'),
                        ('CITES', 'cites'), ('POSSIBLE_AUTHOR', 'possible_author'),
                        ('LINKED_AUTHORED', 'linked_authored'), ('LINKED_EDITED', 'linked_edited')):
        conn.execute(f"COPY {table} FROM '{OUT / (file + '.parquet')}'")
    report['db'] = str(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
