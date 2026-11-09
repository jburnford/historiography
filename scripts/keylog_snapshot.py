"""A disposable SQLite cache of the key-log state, so an apply stops replaying the whole log (2026-11-09; after three
WSL crashes the user made it the priority: "just make sure we have all the data saved outside of sqlite").

The event log (data/identifiers/events-*.jsonl[.gz], in git) stays the only record. This cache (build/keylog-state.sqlite,
untracked) holds nothing the log doesn't: keys, anchors, aliases, members, relations, the per-prefix counters, and the
log position it reflects (seq, shard, byte offset). It can be deleted at any time; `rebuild` makes it again from the log.

How it stays right:
- an apply appends its events to the log and fsyncs them first, then writes the cache in one transaction;
- opening the cache reads the log from the stored position and applies any events the cache has not seen (a crash
  between the two writes, a shard compressed since), checking that the first of them carries seq + 1; anything that
  does not line up raises SnapshotStale and the caller rebuilds;
- `check` compares a fingerprint of the cache with one of a full replay of the log (identifiers.State.load).

SnapState is identifiers.State with lazy, SQLite-backed maps: State.apply, lookup and materialise run unchanged.
Reads go to an in-memory overlay first, then to SQLite; writes stay in the overlay until flush(). A failed validation
leaves the cache untouched (the overlay is dropped).

    python3 scripts/keylog_snapshot.py rebuild       # full replay -> cache (about 5 GB, a few minutes)
    python3 scripts/keylog_snapshot.py status
    python3 scripts/keylog_snapshot.py check         # cache == full replay?
"""
import argparse, gzip, hashlib, json, sqlite3, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'build/keylog-state.sqlite'
SCHEMA = 1
GONE = object()           # overlay tombstone


class SnapshotStale(RuntimeError):
    pass


SQL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS keys(key TEXT PRIMARY KEY, type TEXT, label TEXT, status TEXT, resolution TEXT,
                                anchors TEXT, aliases TEXT, replaced_by TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS anchor(anchor TEXT PRIMARY KEY, key TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS alias(alias TEXT PRIMARY KEY, key TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS members(key TEXT, member TEXT, PRIMARY KEY(key, member)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS relation(claim TEXT PRIMARY KEY, subject TEXT, predicate TEXT, object TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS top(prefix TEXT PRIMARY KEY, n INTEGER) WITHOUT ROWID;
"""
INDEXES = "CREATE INDEX IF NOT EXISTS keys_type_status ON keys(type, status);"


def connect(path=DB, readonly=False):
    if readonly:
        con = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=60)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path, timeout=60)
        con.executescript(SQL)
        con.execute('PRAGMA synchronous=NORMAL')
    con.execute('PRAGMA cache_size=-200000')          # 200 MB page cache at most
    return con


def rec_from_row(row):
    key, type_, label, status, resolution, anchors, aliases, replaced_by = row
    r = I.Rec(key, type_, label, status, resolution)
    a = json.loads(anchors)
    r.anchors = I.Anchors(a) if a else I.NOTHING
    a = json.loads(aliases)
    r.aliases = I.Anchors(a) if a else I.NOTHING
    rb = json.loads(replaced_by)
    r.replaced_by = rb if rb else I.NOTHING
    return r


def rec_row(r):
    return (r.key, r.type, r.label, r.status, r.resolution, json.dumps(list(r.anchors), ensure_ascii=False),
            json.dumps(list(r.aliases), ensure_ascii=False), json.dumps(list(r.replaced_by)))


class _Map:
    """key -> value map over one SQLite table, with an overlay of changes (tombstones for deletes)."""

    def __init__(self, con, table, kcol, vcols, decode):
        self.con, self.table, self.kcol, self.vcols, self.decode = con, table, kcol, vcols, decode
        self.over = {}

    def _fetch(self, k):
        row = self.con.execute(f'SELECT {", ".join(self.vcols)} FROM {self.table} WHERE {self.kcol} = ?', (k,)).fetchone()
        return self.decode(row) if row is not None else None

    def get(self, k, default=None):
        if k in self.over:
            v = self.over[k]
            return default if v is GONE else v
        v = self._fetch(k)
        return default if v is None else v

    def __contains__(self, k):
        return self.get(k, GONE) is not GONE

    def __getitem__(self, k):
        v = self.get(k, GONE)
        if v is GONE:
            raise KeyError(k)
        return v

    def __setitem__(self, k, v):
        self.over[k] = v

    def __delitem__(self, k):
        if k not in self:
            raise KeyError(k)
        self.over[k] = GONE

    def items(self):
        seen = set()
        for k, v in self.over.items():
            seen.add(k)
            if v is not GONE:
                yield k, v
        for row in self.con.execute(f'SELECT {self.kcol}, {", ".join(self.vcols)} FROM {self.table} ORDER BY {self.kcol}'):
            if row[0] not in seen:
                yield row[0], self.decode(row[1:])

    def values(self):
        return (v for _, v in self.items())

    def __iter__(self):
        return (k for k, _ in self.items())

    def __len__(self):
        n = self.con.execute(f'SELECT count(*) FROM {self.table}').fetchone()[0]
        for k, v in self.over.items():
            had = self._fetch(k) is not None
            n += (v is not GONE) - had
        return n


class _Keys(_Map):
    """Records fetched for reading are kept in the overlay too: State.apply mutates them in place."""

    def __init__(self, con):
        super().__init__(con, 'keys', 'key', ('key', 'type', 'label', 'status', 'resolution', 'anchors', 'aliases',
                                              'replaced_by'), rec_from_row)

    def get(self, k, default=None):
        if k in self.over:
            v = self.over[k]
            return default if v is GONE else v
        v = self._fetch(k)
        if v is None:
            return default
        self.over[k] = v
        return v


class _Members:
    """defaultdict(set) over the members table: members[k] gives a set (created and kept in the overlay)."""

    def __init__(self, con):
        self.con, self.over = con, {}

    def _load(self, k):
        if k not in self.over:
            self.over[k] = {m for (m,) in self.con.execute('SELECT member FROM members WHERE key = ?', (k,))}
        return self.over[k]

    def __getitem__(self, k):
        return self._load(k)

    def get(self, k, default=None):
        s = self._load(k)
        return s if s else default

    def __contains__(self, k):
        return bool(self._load(k))

    def __setitem__(self, k, v):
        self.over[k] = set(v)

    def items(self):
        seen = set(self.over)
        for k, v in self.over.items():
            if v:
                yield k, v
        cur, cur_key = None, None
        for k, m in self.con.execute('SELECT key, member FROM members ORDER BY key'):
            if k in seen:
                continue
            if k != cur_key:
                if cur_key is not None:
                    yield cur_key, cur
                cur, cur_key = set(), k
            cur.add(m)
        if cur_key is not None:
            yield cur_key, cur


class SnapState(I.State):
    """identifiers.State backed by the cache. Same attributes; reads lazy, writes held until flush()."""

    def __init__(self, con):
        super().__init__()
        self.con = con
        self.keys = _Keys(con)
        self.anchor = _Map(con, 'anchor', 'anchor', ('key',), lambda r: r[0])
        self.alias = _Map(con, 'alias', 'alias', ('key',), lambda r: r[0])
        self.members = _Members(con)
        self.relation = _Map(con, 'relation', 'claim', ('subject', 'predicate', 'object'),
                             lambda r: dict(subject=r[0], predicate=r[1], object=r[2]))
        self.top = Counter(dict(con.execute('SELECT prefix, n FROM top').fetchall()))
        meta = dict(con.execute('SELECT k, v FROM meta').fetchall())
        self.seq = int(meta.get('seq', 0))
        self.pos = json.loads(meta.get('pos', 'null'))
        if meta and int(meta.get('schema', SCHEMA)) != SCHEMA:
            raise SnapshotStale(f'cache schema {meta.get("schema")} != {SCHEMA}')

    def withdrawn_claim_anchors(self):
        out = set()
        for (a,) in self.con.execute("SELECT anchors FROM keys WHERE type = 'claim' AND status = 'withdrawn'"):
            out.update(json.loads(a))
        for k, r in self.keys.over.items():                 # claims withdrawn in this overlay
            if r is not GONE and r.type == 'claim' and r.status == 'withdrawn':
                out.update(r.anchors)
        return out

    def flush(self, pos):
        """Write the overlay and the new log position in one transaction."""
        c = self.con
        with c:
            for k, r in self.keys.over.items():
                c.execute('INSERT OR REPLACE INTO keys VALUES (?,?,?,?,?,?,?,?)', rec_row(r))
            for tbl, col, m in (('anchor', 'anchor', self.anchor), ('alias', 'alias', self.alias)):
                for k, v in m.over.items():
                    if v is GONE:
                        c.execute(f'DELETE FROM {tbl} WHERE {col} = ?', (k,))
                    else:
                        c.execute(f'INSERT OR REPLACE INTO {tbl} VALUES (?, ?)', (k, v))
            for k, s in self.members.over.items():
                c.execute('DELETE FROM members WHERE key = ?', (k,))
                c.executemany('INSERT INTO members VALUES (?, ?)', [(k, m) for m in sorted(s)])
            for k, v in self.relation.over.items():
                if v is GONE:
                    c.execute('DELETE FROM relation WHERE claim = ?', (k,))
                else:
                    c.execute('INSERT OR REPLACE INTO relation VALUES (?,?,?,?)', (k, v['subject'], v['predicate'], v['object']))
            c.executemany('INSERT OR REPLACE INTO top VALUES (?, ?)', list(self.top.items()))
            c.executemany('INSERT OR REPLACE INTO meta VALUES (?, ?)',
                          [('seq', str(self.seq)), ('pos', json.dumps(pos)), ('schema', str(SCHEMA))])
        for m in (self.keys, self.anchor, self.alias, self.relation):
            m.over.clear()
        self.members.over.clear()
        self.pos = pos


def _stem(p):
    return p.name[:-3] if p.name.endswith('.gz') else p.name


def log_end(directory):
    """Position just past the last event: (shard stem, byte offset in its uncompressed text)."""
    files = I.shards(directory)
    if not files:
        return None
    last = files[-1]
    if last.name.endswith('.gz'):
        with gzip.open(last, 'rb') as fh:
            size = sum(len(b) for b in iter(lambda: fh.read(1 << 24), b''))
    else:
        size = last.stat().st_size
    return [_stem(last), size]


def last_seq(directory):
    """seq of the last event in the log (read from the end of the last shard)."""
    files = I.shards(directory)
    if not files:
        return 0
    last = files[-1]
    if last.name.endswith('.gz'):
        line = b''
        with gzip.open(last, 'rb') as fh:
            for line_ in fh:
                if line_.strip():
                    line = line_
    else:
        with open(last, 'rb') as fh:
            fh.seek(0, 2)
            end = fh.tell()
            back = min(end, 1 << 20)
            fh.seek(end - back)
            lines = [l for l in fh.read().splitlines() if l.strip()]
            line = lines[-1] if lines else b''
    return json.loads(line)['seq'] if line else 0


def catch_up(state, directory):
    """Apply the log events written after the cache's position. Returns how many were applied."""
    files = I.shards(directory)
    if state.pos is None:                   # the cache was made from an empty log: read from the first shard
        if state.seq != 0:
            raise SnapshotStale('cache has events but no log position')
        if not files:
            return 0
        i, offset = 0, 0
    else:
        stem, offset = state.pos
        i = next((n for n, f in enumerate(files) if _stem(f) == stem), None)
        if i is None:
            raise SnapshotStale(f'shard {stem} not in the log')
    n = 0
    for j, f in enumerate(files[i:]):
        with I.open_shard(f) as fh:
            if j == 0 and offset:
                if f.name.endswith('.gz'):
                    fh.buffer.read(offset) if hasattr(fh, 'buffer') else fh.read(offset)
                else:
                    fh.seek(offset)
            for line in fh:
                if not line.strip():
                    continue
                ev = json.loads(line)
                if n == 0 and ev.get('seq') != state.seq + 1:
                    raise SnapshotStale(f'log at the cached position has seq {ev.get("seq")}, cache expects {state.seq + 1}')
                state.apply(ev)
                n += 1
    return n


def cache_path(directory):
    """build/keylog-state.sqlite for the project log; <dir>/.state.sqlite for any other (tests, scratch copies)."""
    d = I.log_dir(directory)
    return DB if d.resolve() == I.log_dir(I.DEFAULT_DIR).resolve() else d / '.state.sqlite'


def open_state(directory=I.DEFAULT_DIR, path=None, write=True):
    """The current state from the cache plus any newer log events; rebuild first if the cache is missing or stale.
    With write=True (callers holding the log lock) catch-up events are saved to the cache."""
    directory = I.log_dir(directory)
    path = path or cache_path(directory)
    if not path.exists():
        if not write:
            raise SnapshotStale('no cache')
        rebuild(directory, path)
    con = connect(path, readonly=not write)
    try:
        state = SnapState(con)
        n = catch_up(state, directory)
        if state.seq != last_seq(directory):    # never number new events from a cache that disagrees with the log
            raise SnapshotStale(f'cache at seq {state.seq}, log ends at {last_seq(directory)}')
        if n and write:
            state.flush(log_end(directory))
        return state
    except SnapshotStale:
        con.close()
        if not write:
            raise
        rebuild(directory, path)
        state = SnapState(connect(path))
        catch_up(state, directory)
        if state.seq != last_seq(directory):
            raise I.LogError(f'rebuilt cache at seq {state.seq}, log ends at {last_seq(directory)}')
        return state


def rebuild(directory=I.DEFAULT_DIR, path=None):
    """Full replay of the log into a fresh cache (written beside, then moved into place)."""
    directory = I.log_dir(directory)
    path = path or cache_path(directory)
    t = time.time()
    full = I.State.load(directory)
    pos = log_end(directory)
    tmp = path.with_name(path.name + '.new')
    for p in (tmp, Path(str(tmp) + '-wal'), Path(str(tmp) + '-shm')):
        if p.exists():
            p.unlink()
    con = connect(tmp)
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    with con:
        con.executemany('INSERT INTO keys VALUES (?,?,?,?,?,?,?,?)', (rec_row(r) for r in full.keys.values()))
        con.executemany('INSERT INTO anchor VALUES (?, ?)', full.anchor.items())
        con.executemany('INSERT INTO alias VALUES (?, ?)', full.alias.items())
        con.executemany('INSERT INTO members VALUES (?, ?)', ((k, m) for k, s in full.members.items() for m in s))
        con.executemany('INSERT INTO relation VALUES (?,?,?,?)',
                        ((k, r['subject'], r['predicate'], r['object']) for k, r in full.relation.items()))
        con.executemany('INSERT INTO top VALUES (?, ?)', list(full.top.items()))
        con.executemany('INSERT INTO meta VALUES (?, ?)', [('seq', str(full.seq)), ('pos', json.dumps(pos)),
                                                           ('schema', str(SCHEMA))])
        con.execute(INDEXES)
    con.execute('PRAGMA journal_mode=WAL')
    con.close()
    del full
    for p in (Path(str(path) + '-wal'), Path(str(path) + '-shm')):
        if p.exists():
            p.unlink()
    tmp.replace(path)
    print(f'cache rebuilt from the log in {time.time() - t:.0f}s: seq {pos and json.dumps(pos)}', file=sys.stderr)


def _record_tuple(k, r, members, relation):
    return repr((k, r['type'], r['label'], r['status'], r['resolution'], sorted(r['anchors']), sorted(r['aliases']),
                 list(r['replaced_by']), sorted(members or ()), relation)).encode()


def fingerprint(state):
    """Same fingerprint for a full State and a flushed SnapState: every key record with its members and relation,
    then the anchor and alias maps, the counters and seq. The cache side streams SQL in key order (SQLite's binary
    order is code-point order, as Python's sort), so it holds one row at a time."""
    h = hashlib.sha256()
    if isinstance(state, SnapState):
        if state.keys.over or state.anchor.over or state.members.over:
            raise RuntimeError('flush the cache state before taking its fingerprint')
        q = """SELECT k.key, k.type, k.label, k.status, k.resolution, k.anchors, k.aliases, k.replaced_by,
                      (SELECT json_group_array(member) FROM (SELECT member FROM members m WHERE m.key = k.key ORDER BY member)),
                      r.subject, r.predicate, r.object
               FROM keys k LEFT JOIN relation r ON r.claim = k.key ORDER BY k.key"""
        for row in state.con.execute(q):
            rec = rec_from_row(row[:8])
            rel = dict(subject=row[9], predicate=row[10], object=row[11]) if row[10] is not None else None
            h.update(_record_tuple(row[0], rec, json.loads(row[8]), rel))
        for tbl, col in (('anchor', 'anchor'), ('alias', 'alias')):
            h.update(repr(list(state.con.execute(f'SELECT {col}, key FROM {tbl} ORDER BY {col}'))).encode())
    else:
        for k in sorted(state.keys):
            h.update(_record_tuple(k, state.keys[k], state.members.get(k), state.relation.get(k)))
        for m in (state.anchor, state.alias):
            h.update(repr(sorted(m.items())).encode())
    h.update(repr(sorted(state.top.items())).encode()); h.update(repr(state.seq).encode())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=('rebuild', 'status', 'check'))
    ap.add_argument('--dir', type=Path, default=I.DEFAULT_DIR)
    ap.add_argument('--db', type=Path)
    args = ap.parse_args()
    if args.cmd == 'rebuild':
        with I.locked(I.log_dir(args.dir)):
            rebuild(args.dir, args.db)
    elif args.cmd == 'status':
        con = connect(args.db or cache_path(args.dir), readonly=True)
        meta = dict(con.execute('SELECT k, v FROM meta').fetchall())
        n = con.execute('SELECT count(*) FROM keys').fetchone()[0]
        print(f"cache seq {meta.get('seq')} at {meta.get('pos')}; {n} keys; log ends at {log_end(I.log_dir(args.dir))}")
    else:
        with I.locked(I.log_dir(args.dir)):
            snap = open_state(args.dir, args.db, write=True)
            a = fingerprint(snap)
            seq = snap.seq
            snap.con.close(); del snap
            full = I.State.load(args.dir)
            b = fingerprint(full)
        print(f'seq {seq} / {full.seq}: cache {a[:16]} full replay {b[:16]}', 'MATCH' if a == b and seq == full.seq else 'DIFFER')
        return 0 if a == b else 1


if __name__ == '__main__':
    sys.exit(main())
