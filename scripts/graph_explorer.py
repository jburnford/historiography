"""Local explorer for the knowledge graph (2026-11-08; user: "a web interface to visualize and explore the graph,
focused on one person and their edges to other nodes; click on other nodes and show the edges from that node").
Reads the graph build (build/graph/*.parquet from scripts/build_graph.py), never the key log or any text.

    python3 scripts/graph_explorer.py build      # build/graph/explorer.duckdb: nodes, sorted edge copies, weights
    python3 scripts/graph_explorer.py serve      # http://localhost:4180/  (builds first if the graph is newer)

API (JSON): /api/search?q=   /api/node?key=   /api/group?key=&rel=&offset=&limit=&sort=weight|year
Weights: a work's weight is the number of works citing it plus reviews of it; a person's is the sum over the works
they authored. Life years are not shown (site rule for living people); the explorer is local for now.
"""
import argparse, json, re, sys, threading, time, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
DB = G / 'explorer.duckdb'
STATIC = ROOT / 'explorer'
EDGES = ['authored', 'cites', 'reviews', 'reviewed', 'supervised', 'advised', 'awarded_by', 'coauthored', 'coedited',
         'edited', 'editor_of', 'part_of', 'published_as', 'possibly_same', 'affiliated_with',
         'linked_authored', 'linked_edited', 'possible_author']
# cited works' authors outside the key log (build_graph, 2026-11-10): marked on every row
LINKED_D = ("string_agg(DISTINCT CASE e.state WHEN 'exact' THEN 'linked by identifier' ELSE 'linked by rule' END || ' ('"
            " || CASE e.source WHEN 'lc' THEN 'LC' WHEN 'openalex' THEN 'OpenAlex' ELSE e.source END || '); not a key-log claim', '; ')")
POSSIBLE_D = ("'possible author (' || any_value(e.n_candidates) || ' candidate' || CASE WHEN any_value(e.n_candidates) > 1 "
              "THEN 's' ELSE '' END || '); not credited'")

# Relations shown for each node type: (id, label, edge table, self side, other side, detail SQL over e and o)
# `e` is the edge row, `o` the other node. Rows are grouped by the other node (n = number of edges to it).
REL = {
    'person': [
        ('authored', 'Wrote', 'authored', 'from', 'to', None),
        ('edited', 'Edited', 'edited', 'from', 'to', None),
        ('linked_authored', 'Wrote (linked, outside the key log)', 'linked_authored', 'from', 'to', LINKED_D),
        ('linked_edited', 'Edited (linked, outside the key log)', 'linked_edited', 'from', 'to', LINKED_D),
        ('possible_author', 'Possibly wrote (not credited)', 'possible_author', 'from', 'to', POSSIBLE_D),
        ('supervised', 'Supervised theses', 'supervised', 'from', 'to', None),
        ('students', 'Students', 'advised', 'from', 'to', "(SELECT label FROM nodes WHERE key = any_value(e.thesis))"),
        ('advisors', 'Advisors', 'advised', 'to', 'from', "(SELECT label FROM nodes WHERE key = any_value(e.thesis))"),
        ('reviewed', 'Reviewed books by', 'reviewed', 'from', 'to', "(SELECT label FROM nodes WHERE key = any_value(e.book))"),
        ('reviewed_by', 'Reviewed by', 'reviewed', 'to', 'from', "(SELECT label FROM nodes WHERE key = any_value(e.book))"),
        ('coauthors', 'Co-authors', 'coauthored', None, None, None),
        ('coeditors', 'Co-editors', 'coedited', None, None, None),
        ('editor_of', 'Edited chapters by', 'editor_of', 'from', 'to', None),
        ('in_volumes_of', 'Chapters in volumes edited by', 'editor_of', 'to', 'from', None),
        ('cited_by_people', 'Cited by (people)', None, None, None, None),
        ('cites_people', 'Cites (people)', None, None, None, None),
        ('possibly_same', 'Possibly the same person', 'possibly_same', None, None, None),
        ('affiliations', 'Affiliations', None, None, None, None),
    ],
    'work': [
        ('authors', 'Authors', 'authored', 'to', 'from', None),
        ('editors', 'Editors', 'edited', 'to', 'from', None),
        ('linked_authors', 'Authors (linked, outside the key log)', 'linked_authored', 'to', 'from', LINKED_D),
        ('linked_editors', 'Editors (linked, outside the key log)', 'linked_edited', 'to', 'from', LINKED_D),
        ('possible_authors', 'Possible authors (not credited)', 'possible_author', 'to', 'from', POSSIBLE_D),
        ('supervisors', 'Supervisors', 'supervised', 'to', 'from', None),
        ('awarded_by', 'Degree from', 'awarded_by', 'from', 'to', None),
        ('cites', 'Cites', 'cites', 'from', 'to', None),
        ('cited_by', 'Cited by', 'cites', 'to', 'from', None),
        ('reviews', 'Review of', 'reviews', 'from', 'to', None),
        ('reviewed_in', 'Reviewed in', 'reviews', 'to', 'from', None),
        ('part_of', 'Part of', 'part_of', 'from', 'to', None),
        ('contains', 'Contains', 'part_of', 'to', 'from', None),
        ('published_as', 'Published as', 'published_as', 'from', 'to', None),
        ('published_from', 'Published from', 'published_as', 'to', 'from', None),
    ],
    'institution': [
        ('faculty', 'Faculty and affiliated people', None, None, None, None),
        ('advisors_here', 'Advised PhDs here', None, None, None, None),
        ('theses', 'Theses awarded', 'awarded_by', 'to', 'from', None),
    ],
}
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
    for e in EDGES:
        src = f"'{G}/{e}.parquet'"
        db.execute(f'CREATE TABLE e_{e}_f AS SELECT * FROM {src} ORDER BY "from"')
        db.execute(f'CREATE TABLE e_{e}_t AS SELECT * FROM {src} ORDER BY "to"')
    db.execute(f"""CREATE TABLE work_w AS SELECT w.key,
        coalesce(c.n, 0) AS cited, coalesce(r.n, 0) AS reviewed
        FROM '{G}/work.parquet' w
        LEFT JOIN (SELECT "to" k, count(*) n FROM e_cites_t GROUP BY 1) c ON c.k = w.key
        LEFT JOIN (SELECT "to" k, count(*) n FROM e_reviews_t GROUP BY 1) r ON r.k = w.key""")
    db.execute("""CREATE TABLE person_w AS SELECT a."from" AS key, count(*) works, sum(w.cited) cited, sum(w.reviewed) reviewed
        FROM e_authored_f a JOIN work_w w ON w.key = a."to" GROUP BY 1""")
    db.execute(f"""CREATE TABLE nodes AS
        SELECT p.key, 'person' AS type, p.label, NULL::VARCHAR AS kind, NULL::INTEGER AS year, NULL::VARCHAR AS journal,
               p.resolution, p.anchors, coalesce(s.cited, 0) + coalesce(s.reviewed, 0) AS weight,
               coalesce(s.works, 0) AS works, coalesce(s.cited, 0) AS cited, coalesce(s.reviewed, 0) AS reviewed
          FROM '{G}/person.parquet' p LEFT JOIN person_w s ON s.key = p.key
        UNION ALL
        SELECT w.key, 'work', w.label, w.kind, w.year, w.journal, w.resolution, w.anchors, s.cited + s.reviewed,
               NULL, s.cited, s.reviewed
          FROM '{G}/work.parquet' w JOIN work_w s ON s.key = w.key
        UNION ALL
        SELECT i.key, 'institution', i.label, NULL, NULL, NULL, i.resolution, i.anchors,
               (SELECT count(*) FROM e_awarded_by_t a WHERE a."to" = i.key), NULL, NULL, NULL
          FROM '{G}/institution.parquet' i
        ORDER BY key""")
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


def node_type(key):
    if key.startswith(('doi:', 'lccn:', 'openalex:')):   # unkeyed works: Crossref citing articles, and cited works
        return 'work'                                       # matched to LC/OpenAlex/Crossref (build_graph, 2026-11-10)
    return {'p': 'person', 'w': 'work', 'i': 'institution'}.get(key[:1])


def ids(anchors):
    out = []
    for a in anchors or []:
        s, _, v = a.partition(':')
        out.append(dict(scheme=s, value=v, url=LINKS[s].format(v) if s in LINKS else None))
    return out


ITEM_COLS = 'o.key, o.type, o.kind, o.label, o.year, o.weight, o.resolution'


def item(r):
    return dict(key=r[0], type=r[1], kind=r[2], label=r[3], year=r[4], weight=r[5], resolution=r[6],
                n=r[7], detail=r[8] if len(r) > 8 else None)


class Graph:
    def __init__(self):
        self.db = duckdb.connect(str(DB), read_only=True)
        self.local = threading.local()

    def cur(self):
        if not hasattr(self.local, 'c'):
            self.local.c = self.db.cursor()
        return self.local.c

    def group_sql(self, rel, key):
        """SQL yielding (other_key, n, detail) rows for one relation of one node."""
        rid, _, table, me, other, detail = rel
        if rid in ('coauthors', 'coeditors'):
            return (f"""SELECT "to" k, works n, CASE WHEN first_year IS NULL THEN works || ' works'
                        ELSE works || ' works, ' || first_year || '–' || last_year END d FROM e_{table}_f WHERE "from" = $k
                        UNION SELECT "from", works, CASE WHEN first_year IS NULL THEN works || ' works'
                        ELSE works || ' works, ' || first_year || '–' || last_year END FROM e_{table}_t WHERE "to" = $k""")
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
        if rid == 'cited_by_people':      # people whose works cite this person's works
            return ("""SELECT a2."from" k, count(DISTINCT c."from") n, count(DISTINCT c."from") || ' citing works' d
                       FROM e_authored_f a JOIN e_cites_t c ON c."to" = a."to" JOIN e_authored_t a2 ON a2."to" = c."from"
                       WHERE a."from" = $k AND a2."from" <> $k GROUP BY 1""")
        if rid == 'cites_people':         # people whose works this person's works cite
            return ("""SELECT a2."from" k, count(DISTINCT c."to") n, count(DISTINCT c."to") || ' works cited' d
                       FROM e_authored_f a JOIN e_cites_f c ON c."from" = a."to" JOIN e_authored_t a2 ON a2."to" = c."to"
                       WHERE a."from" = $k AND a2."from" <> $k GROUP BY 1""")
        side = 'f' if me == 'from' else 't'
        d = detail or 'NULL'
        return f'SELECT e."{other}" k, count(*) n, {d} d FROM e_{table}_{side} e WHERE e."{me}" = $k GROUP BY 1'

    def group(self, key, rel, offset=0, limit=12, sort='weight'):
        order = 'o.year DESC NULLS LAST, o.weight DESC' if sort == 'year' else 'g.n DESC, o.weight DESC, o.year DESC NULLS LAST'
        q = f"""WITH g AS ({self.group_sql(rel, key)})
                SELECT {ITEM_COLS}, g.n, g.d, count(*) OVER () AS total
                FROM g JOIN nodes o ON o.key = g.k ORDER BY {order}, o.key LIMIT {int(limit)} OFFSET {int(offset)}"""
        rows = self.cur().execute(q, dict(k=key)).fetchall()
        total = rows[0][-1] if rows else (0 if offset == 0 else None)
        return [item(r[:-1]) for r in rows], total

    def node(self, key, limit=12, sort='weight'):
        r = self.cur().execute("""SELECT key, type, label, kind, year, journal, resolution, anchors, weight, works, cited, reviewed
                                  FROM nodes WHERE key = ?""", [key]).fetchone()
        if not r:
            return None
        n = dict(zip(['key', 'type', 'label', 'kind', 'year', 'journal', 'resolution', 'anchors', 'weight', 'works',
                      'cited', 'reviewed'], r))
        n['ids'] = ids(n.pop('anchors'))
        groups = []
        for rel in REL[n['type']]:
            items, total = self.group(key, rel, 0, limit, sort)
            if total:
                groups.append(dict(id=rel[0], label=rel[1], total=total, items=items))
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
        rows = c.execute(f"""SELECT key, type, kind, label, year, weight, resolution, NULL, NULL FROM nodes
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
