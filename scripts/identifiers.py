"""Internal keys: append-only event log, single locked minter, anchor-based carry-forward (PID-PLAN.md v2).

The authority is the log `data/identifiers/events-NNNN.jsonl`, one JSON event per line, tracked in Git, read
in shard order as one sequence. A shard is closed once it reaches SHARD_BYTES (GitHub refuses files over
100 MB); the minter then opens the next. Closed shards are never edited. Current state is derived from the
log on every read; nothing else is authoritative. Keys are `<prefix>-<n>`, never reused.
Builds and agents never mint directly: they write a proposal (a list of operations) and the minter
applies it under a lock, assigning numbers in order.

Vocabulary
- **anchor**: a strong identifier string that may match a key across builds (`atlas:person:x`,
  `orcid:0000-…`, `wd:Q…`, `lcnaf:n…`, `aha:…`, `doi:…`). An active anchor belongs to one key.
- **member**: any other constituent, e.g. a source occurrence ID. Members never drive matching.
- **alias**: an old or readable name (`slug:geertz`, `edge:edge_001`) that resolves to a key, including
  after the key is retired (lookup follows `replaced_by`).
- **relation**: a claim key minted with `relation: {subject, predicate, object}` states a link between two
  entities (an advisor supervised a thesis; a person authored a work). Its anchors are the source assertions
  (`aha-sup:<record>:<advisor>`), and its endpoints are source anchors (or keys), resolved through the log on
  every read, so a merge or a detached anchor carries through without rewriting the claim.

    python3 scripts/identifiers.py check
    python3 scripts/identifiers.py shard          # one-time: move a legacy events.jsonl to events-0001.jsonl
    python3 scripts/identifiers.py summary
    python3 scripts/identifiers.py lookup slug:geertz
    python3 scripts/identifiers.py apply proposal.json[.gz] [--basis TEXT]
"""
import argparse
import copy
import fcntl
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / 'data/identifiers'
PREFIX = {'person': 'p', 'work': 'w', 'journal': 'j', 'institution': 'i', 'entry': 'e', 'claim': 'c', 'event': 't'}
TYPE_OF = {v: k for k, v in PREFIX.items()}
LIFECYCLE = {'active', 'provisional', 'unsupported', 'merged', 'split', 'withdrawn', 'retyped'}
RETIRED = {'merged', 'split', 'withdrawn', 'retyped'}
RESOLUTION = {'established', 'recorded', 'unresolved', 'editorial'}
# A person is `established` only on a public identifier (LC, Wikidata, ORCID, the atlas, Open Library) or on
# two independent sources agreeing (an AHA record and our harvested thesis; a canon name key and an AHA record
# joined by the published thesis). A person known from one source record (an AHA listing, one harvested
# thesis, an AHA advisor token) is `recorded`: real, but no second source vouches for the identity
# (Fable review, 2026-11-01: 67,693 such people read as established). plan() applies this to clusters that
# claim `established`, and raises a recorded key when later evidence reaches the bar.
PUBLIC_SCHEMES = {'lcnaf', 'wd', 'orcid', 'atlas', 'ol', 'gnd', 'viaf', 'isni', 'idref'}
SOURCE_FAMILY = {'aha-phd': 'aha', 'aha': 'aha', 'aha-diss': 'aha', 'diss-author': 'diss', 'diss-thesis': 'diss',
                 'diss-person': 'diss', 'repo-advisor': 'diss', 'capes-person': 'diss'}
KEY_RE = re.compile(r'^([a-z])-([1-9][0-9]*)$')
SHARD_BYTES = 50_000_000
SHARD_RE = re.compile(r'^events-([0-9]{4})\.jsonl(\.gz)?$')
EVENTS = {'mint', 'attach', 'detach', 'merge', 'split', 'retype', 'withdraw', 'relabel', 'status'}
# Relation predicates, read subject -> object (Fable review 2026-11-01: relations belong in the log, not in
# side files of keys that go stale when a key merges).
PREDICATES = {'supervised': ('person', 'work'), 'authored': ('person', 'work'), 'edited': ('person', 'work'),
              'published_as': ('work', 'work'), 'reviews': ('work', 'work'), 'part_of': ('work', 'work'),
              'advised': ('person', 'person')}


class LogError(ValueError):
    pass


def open_shard(path):
    """A shard for reading as text, plain or gzipped."""
    path = Path(path)
    return gzip.open(path, 'rt', encoding='utf-8') if path.name.endswith('.gz') else open(path, encoding='utf-8')


def log_dir(path):
    """The log directory for a directory or a legacy `<dir>/events.jsonl` path (older callers pass that)."""
    path = Path(path)
    return path.parent if path.name == 'events.jsonl' else path


def shards(directory):
    """The log's shards in order. Numbers run from 0001 without gaps; a closed shard may be gzipped
    (`events-NNNN.jsonl.gz`, `identifiers.py compress`; 2026-11-03, about 9x smaller in the working tree), never
    both forms of one; a legacy events.jsonl beside shards is refused (the log would be read twice or half)."""
    directory = log_dir(directory)
    found = sorted((p for p in directory.glob('events-*.jsonl*') if SHARD_RE.match(p.name)),
                   key=lambda p: (int(SHARD_RE.match(p.name).group(1)), p.name))
    for n, p in enumerate(found, 1):
        if int(SHARD_RE.match(p.name).group(1)) != n:
            raise LogError(f'{directory}: shard {p.name} out of sequence (expected events-{n:04d}.jsonl, '
                           'or a plain and a compressed copy of one shard)')
    if (directory / 'events.jsonl').exists():
        if found:
            raise LogError(f'{directory}: legacy events.jsonl beside shards')
        return [directory / 'events.jsonl']
    return found


_intern = sys.intern


class Anchors(tuple):
    """A key's anchors or aliases: a tuple (no per-key set; 2026-11-09 memory) that still answers the set operators
    older scripts use on records (pids | rec['anchors'], rec['anchors'] - theirs, & ...); results are plain sets."""
    __slots__ = ()

    def __or__(self, o): return set(self) | set(o)
    def __ror__(self, o): return set(o) | set(self)
    def __and__(self, o): return set(self) & set(o)
    def __rand__(self, o): return set(o) & set(self)
    def __sub__(self, o): return set(self) - set(o)
    def __rsub__(self, o): return set(o) - set(self)
    def union(self, *o): return set(self).union(*o)
    def intersection(self, *o): return set(self).intersection(*o)
    def difference(self, *o): return set(self).difference(*o)
    def isdisjoint(self, o): return set(self).isdisjoint(o)
    def issubset(self, o): return set(self).issubset(o)
    def copy(self): return set(self)


NOTHING = Anchors()


class Rec:
    """One key's record, read like the dict it used to be (rec['label'], rec.get('status'), rec.update(...)), held in
    about a third of the memory (2026-11-09: 4.6M keys made State.load 7.8 GB and three WSL crashes followed): slots
    instead of a dict, interned type/status/resolution, anchors as a tuple, aliases and replaced_by as a shared empty
    tuple until used. Only State changes records; readers see tuples, so `in`, iteration, len() and sorted() work as
    they did on the sets."""
    __slots__ = ('key', 'type', 'label', 'status', 'resolution', 'anchors', 'aliases', 'replaced_by')
    FIELDS = __slots__

    def __init__(self, key, type, label, status, resolution):
        self.key, self.type, self.label = key, _intern(type), label
        self.status, self.resolution = _intern(status), _intern(resolution)
        self.anchors = self.aliases = self.replaced_by = NOTHING

    def __getitem__(self, f):
        if f not in self.FIELDS:
            raise KeyError(f)
        return getattr(self, f)

    def __setitem__(self, f, v):
        if f not in self.FIELDS:
            raise KeyError(f)
        setattr(self, f, _intern(v) if f in ('type', 'status', 'resolution') and isinstance(v, str) else v)

    def get(self, f, default=None):
        return getattr(self, f) if f in self.FIELDS else default

    def update(self, **kw):
        for f, v in kw.items():
            self[f] = v

    def __contains__(self, f):
        return f in self.FIELDS

    def keys(self):
        return list(self.FIELDS)

    def items(self):
        return [(f, getattr(self, f)) for f in self.FIELDS]

    def __iter__(self):
        return iter(self.FIELDS)

    def __eq__(self, other):
        return isinstance(other, Rec) and all(getattr(self, f) == getattr(other, f) for f in self.FIELDS)

    def __repr__(self):
        return 'Rec(' + ', '.join(f'{f}={getattr(self, f)!r}' for f in self.FIELDS) + ')'


class State:
    """Current state derived from the event log. `apply` validates one event and mutates the state."""

    def __init__(self):
        self.keys = {}
        self.anchor = {}            # active anchor -> key
        self.alias = {}             # alias -> key (permanent; may point at a retired key)
        self.members = defaultdict(set)
        self.relation = {}          # claim key -> {subject, predicate, object} (endpoints as recorded)
        self.top = Counter()        # highest number minted per prefix
        self.seq = 0

    @classmethod
    def load(cls, path):
        """Load the log in a directory (or a legacy `<dir>/events.jsonl` path); a single file named otherwise
        is read as a whole log."""
        s = cls()
        path = Path(path)
        files = [path] if path.is_file() and path.name != 'events.jsonl' else shards(path)
        for f in files:
            with open_shard(f) as fh:
                for n, line in enumerate(fh, 1):
                    if line.strip():
                        try:
                            s.apply(json.loads(line))
                        except (LogError, json.JSONDecodeError, KeyError) as e:
                            raise LogError(f'{f}:{n}: {e}') from e
        return s

    def _live(self, key):
        k = self.keys.get(key)
        if not k:
            raise LogError(f'unknown key {key}')
        if k['status'] in RETIRED:
            raise LogError(f'{key} is retired ({k["status"]})')
        return k

    def _claim_anchors(self, key, anchors):
        for a in anchors:
            owner = self.anchor.get(a)
            if owner and owner != key:
                raise LogError(f'anchor {a} already belongs to {owner}')
        rec = self.keys[key]
        new = tuple(a for a in dict.fromkeys(anchors) if a not in rec.anchors)
        for a in anchors:
            self.anchor[a] = key
        if new:
            rec.anchors = Anchors(rec.anchors + new)

    def _claim_aliases(self, key, aliases):
        for a in aliases:
            if self.alias.get(a, key) != key:
                raise LogError(f'alias {a} already names {self.alias[a]}')
        rec = self.keys[key]
        new = tuple(a for a in dict.fromkeys(aliases) if a not in rec.aliases)
        for a in aliases:
            self.alias[a] = key
        if new:
            rec.aliases = Anchors(rec.aliases + new)

    def _release(self, key):
        k = self.keys[key]
        for a in k['anchors']:
            if self.anchor.get(a) == key:
                del self.anchor[a]

    def apply(self, ev):
        if ev.get('seq') != self.seq + 1:
            raise LogError(f'sequence {ev.get("seq")} follows {self.seq}')
        kind, key = ev['event'], ev['key']
        if kind not in EVENTS:
            raise LogError(f'unknown event {kind}')
        if kind == 'mint':
            m = KEY_RE.match(key)
            if not m or TYPE_OF.get(m.group(1)) != ev['type']:
                raise LogError(f'bad key {key} for type {ev.get("type")}')
            if key in self.keys or int(m.group(2)) <= self.top[m.group(1)]:
                raise LogError(f'{key} reuses or reorders a number (last {m.group(1)}-{self.top[m.group(1)]})')
            if ev.get('resolution') not in RESOLUTION:
                raise LogError(f'bad resolution {ev.get("resolution")}')
            r = ev.get('relation')
            if r is not None and (ev['type'] != 'claim' or r.get('predicate') not in PREDICATES
                                  or not (r.get('subject') and r.get('object'))):
                raise LogError(f'bad relation on {key}: {r}')
            self.top[m.group(1)] = int(m.group(2))
            self.keys[key] = Rec(key, ev['type'], ev.get('label', ''), ev.get('status', 'active'), ev['resolution'])
            if self.keys[key]['status'] not in LIFECYCLE - RETIRED:
                raise LogError(f'bad initial status for {key}')
            self._claim_anchors(key, ev.get('anchors', []))
            self._claim_aliases(key, ev.get('aliases', []))
            if ev.get('members'):                       # no empty member set per key (members is a defaultdict)
                self.members[key].update(ev['members'])
            if r:
                self.relation[key] = dict(subject=r['subject'], predicate=_intern(r['predicate']), object=r['object'])
        elif kind == 'attach':
            self._live(key)
            self._claim_anchors(key, ev.get('anchors', []))
            self._claim_aliases(key, ev.get('aliases', []))
            if ev.get('members'):
                self.members[key].update(ev['members'])
        elif kind == 'detach':
            k = self._live(key)
            gone = set(ev.get('anchors', []))
            for a in gone:
                if self.anchor.get(a) == key:
                    del self.anchor[a]
            if gone & set(k.anchors):
                k.anchors = Anchors(a for a in k.anchors if a not in gone)
            if ev.get('members') and key in self.members:
                self.members[key].difference_update(ev['members'])
        elif kind == 'merge':
            k, into = self._live(key), self._live(ev['into'])
            if k['type'] != into['type'] or key == ev['into']:
                raise LogError(f'cannot merge {key} into {ev["into"]}')
            anchors = tuple(k['anchors'])
            self._release(key)
            k.update(status='merged', replaced_by=[ev['into']])
            self._claim_anchors(ev['into'], anchors)
            if self.members.get(key):
                self.members[ev['into']] |= self.members[key]
        elif kind in ('split', 'retype'):
            k = self._live(key)
            succ = ev['successors']
            if key in succ or len(set(succ)) != len(succ) or len(succ) != (1 if kind == 'retype' else max(2, len(succ))):
                raise LogError(f'{kind} of {key} needs distinct successors (retype: one; split: two or more)')
            for s in succ:
                t = self._live(s)
                if (t['type'] == k['type']) != (kind == 'split'):
                    raise LogError(f'{kind} successor {s} must have {"the same" if kind == "split" else "another"} type')
            self._release(key)
            k.update(status='split' if kind == 'split' else 'retyped', replaced_by=list(succ))
        elif kind == 'withdraw':
            self._live(key)
            self._release(key)
            self.keys[key]['status'] = 'withdrawn'
        elif kind == 'relabel':
            self._live(key)['label'] = ev['label']
        elif kind == 'status':
            k = self._live(key)
            if ev.get('status') and ev['status'] not in LIFECYCLE - RETIRED:
                raise LogError(f'status event cannot retire ({ev["status"]}); use merge/split/withdraw')
            if ev.get('resolution') and ev['resolution'] not in RESOLUTION:
                raise LogError(f'bad resolution {ev["resolution"]}')
            k['status'] = ev.get('status') or k['status']
            k['resolution'] = ev.get('resolution') or k['resolution']
        self.seq = ev['seq']

    def lookup(self, name):
        """Key for a key, anchor or alias, following retirements to the current key(s)."""
        key = name if name in self.keys else self.anchor.get(name) or self.alias.get(name)
        if not key:
            return []
        out, todo, seen = [], [key], set()
        while todo:
            k = todo.pop()
            if k in seen:
                continue
            seen.add(k)
            nxt = self.keys[k]['replaced_by'] if self.keys[k]['status'] in RETIRED else []
            out.extend([] if nxt else [k])
            todo.extend(nxt)
        return sorted(out)

    def relations(self, predicate=None):
        """Live relation claims with endpoints resolved to current keys: (claim, subject keys, predicate,
        object keys). An endpoint whose anchor was detached resolves to no key (reported, not dropped)."""
        for k, r in self.relation.items():
            if self.keys[k]['status'] in RETIRED or (predicate and r['predicate'] != predicate):
                continue
            yield k, self.lookup(r['subject']), r['predicate'], self.lookup(r['object'])


# --- proposals ------------------------------------------------------------------------------------------
# A proposal is {"basis": str, "decided_by": "build|rule|review", "ops": [...]}. Ops use the event
# vocabulary; a mint op names a placeholder ("new:<anything>") instead of a key, and later ops in the same
# proposal may refer to that placeholder (e.g. split successors). The minter assigns real numbers.

def withdrawn_claim_anchors(state):
    """Anchors of claims withdrawn on review. A withdraw releases its anchors, so a rerun of the rule that made
    the claim would mint it again; rule and build proposals skip these (2026-11-07: a festschrift honoree's
    editor credit and a namesake's book credit came back on the next LC pass)."""
    return {a for v in state.keys.values() if v['type'] == 'claim' and v['status'] == 'withdrawn' for a in v['anchors']}


def materialise(state, proposal, commit, date, inplace=False):
    """Turn a proposal into numbered events, validated against a scratch copy of the state. Claim mints from a
    rule or build proposal whose anchors were withdrawn on review are dropped (reported on stderr); a review
    proposal may mint them again. inplace=True validates on `state` itself (no deep copy, half the memory): for a
    caller that discards the state afterwards, as apply_proposal does (2026-11-09: the copy doubled an apply to
    ~15 GB on a 4.6M-key log and three WSL crashes followed)."""
    nxt = Counter(state.top)
    names, events, seq = {}, [], state.seq
    ops = proposal['ops']
    if proposal.get('decided_by', 'build') in ('rule', 'build') and any(
            op['event'] == 'mint' and op.get('type') == 'claim' for op in ops):
        gone = withdrawn_claim_anchors(state)
        if gone:
            keep = [op for op in ops if not (op['event'] == 'mint' and op.get('type') == 'claim'
                                             and op.get('decided_by', 'build') != 'review'
                                             and any(a in gone for a in op.get('anchors', [])))]
            if len(keep) < len(ops):
                print(f'skipped {len(ops) - len(keep)} claim mints withdrawn on review', file=sys.stderr)
            ops = keep
    for op in ops:
        if op['event'] == 'mint':
            p = PREFIX[op['type']]
            nxt[p] += 1
            names[op['key']] = f'{p}-{nxt[p]}'

    def real(k):
        return names.get(k, k)
    for op in ops:
        seq += 1
        ev = {k: v for k, v in op.items()}
        ev['key'] = real(op['key'])
        if 'into' in ev:
            ev['into'] = real(ev['into'])
        if 'successors' in ev:
            ev['successors'] = [real(s) for s in ev['successors']]
        if any(str(v).startswith('new:') for v in [ev['key'], ev.get('into', '')] + ev.get('successors', [])):
            raise LogError(f'unresolved placeholder in {op}')
        ev.update(seq=seq, date=date, commit=commit, decided_by=op.get('decided_by', proposal.get('decided_by', 'build')),
                  basis=op.get('basis', proposal.get('basis', '')))
        events.append(dict(sorted(ev.items())))
    scratch = state if inplace else copy.deepcopy(state)
    for ev in events:
        scratch.apply(ev)
    return events, names


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / '.mint.lock', 'w') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def git_commit():
    try:
        return subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def _append(directory, lines, limit):
    """Append lines to the open shard, opening the next whenever the open one has reached `limit` bytes."""
    files = shards(directory)
    if files and files[-1].name == 'events.jsonl':
        raise LogError(f'{directory}: legacy events.jsonl; run `identifiers.py shard` first')
    n = len(files) or 1
    if files and files[-1].name.endswith('.gz'):    # the last shard is closed (compressed): open the next
        n += 1
    path = directory / f'events-{n:04d}.jsonl'
    size = path.stat().st_size if path.exists() else 0
    fh = open(path, 'a', encoding='utf-8')
    try:
        for line in lines:
            if size >= limit:
                fh.flush()
                os.fsync(fh.fileno())
                fh.close()
                n += 1
                path, size = directory / f'events-{n:04d}.jsonl', 0
                fh = open(path, 'a', encoding='utf-8')
            fh.write(line)
            size += len(line.encode('utf-8'))
        fh.flush()
        os.fsync(fh.fileno())
    finally:
        fh.close()


def apply_proposal(directory, proposal, commit=None, date=None, limit=SHARD_BYTES):
    """The only writer. Validates the whole proposal, then appends all its events or none."""
    directory = log_dir(directory)
    with locked(directory):
        state = State.load(directory)
        events, names = materialise(state, proposal, git_commit() if commit is None else commit,
                                    date or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), inplace=True)
        _append(directory, [json.dumps(e, ensure_ascii=False) + '\n' for e in events], limit)
    return names


def shard_legacy(directory):
    """One-time move of `events.jsonl` to `events-0001.jsonl` (use `git mv` to keep its history readable)."""
    directory = log_dir(directory)
    with locked(directory):
        legacy = directory / 'events.jsonl'
        if not legacy.exists():
            return None
        if shards(directory) != [legacy]:
            raise LogError(f'{directory}: shards already exist')
        target = directory / 'events-0001.jsonl'
        legacy.rename(target)
        return target


def compress_closed(directory):
    """Gzip every shard but the last (closed shards are never written again; 2026-11-03: 48 MB -> 5.5 MB each).
    The gzipped copy is read back and compared line for line before the plain shard is removed."""
    directory = log_dir(directory)
    done = []
    with locked(directory):
        files = shards(directory)
        for f in files[:-1]:
            if f.name.endswith('.gz'):
                continue
            target = f.with_name(f.name + '.gz')
            with open(f, 'rb') as src, gzip.open(target, 'wb', compresslevel=9) as dst:
                shutil.copyfileobj(src, dst)
            with open(f, 'rb') as a, gzip.open(target, 'rb') as b:
                if a.read() != b.read():
                    target.unlink()
                    raise LogError(f'{target.name}: compressed copy differs; plain shard kept')
            f.unlink()
            done.append(target)
    return done


# --- carry-forward ----------------------------------------------------------------------------------------

def plan(state, clusters, merge_ok=lambda cluster, keys: False):
    """Section 5 of PID-PLAN v2. `clusters`: dicts with type, anchors, members, label, resolution.

    Returns (proposal ops, assignment per cluster index, review queue). Matching uses anchors only.
    - no anchor hit: mint;
    - one key hit by one cluster: attach the new anchors/members;
    - one cluster hits several keys: merge into the oldest key if merge_ok, else hold;
    - several clusters hit one key: hold (a possible split). Held keys go provisional; nothing fails.
    A cluster may carry `status` (e.g. provisional) and `basis`; they go onto its mint or attach event.
    The output is deterministic for a given state and cluster list, whatever order the members arrive in.
    """
    order = sorted(range(len(clusters)), key=lambda i: (clusters[i]['type'], min(clusters[i]['anchors'], default=''),
                                                        clusters[i].get('label', '')))
    hits = {}
    for i in order:
        c = clusters[i]
        ks = {state.anchor[a] for a in c['anchors'] if a in state.anchor}
        hits[i] = sorted((k for k in ks if state.keys[k]['type'] == c['type']), key=_num)
        if len(hits[i]) < len(ks):
            raise LogError(f'cluster {c.get("label")} has anchors owned by another type')
    claimants = defaultdict(list)
    for i in order:
        for k in hits[i]:
            claimants[k].append(i)
    ops, assign, queue, held = [], {}, [], set()
    for i in order:
        c, ks = clusters[i], hits[i]
        split = [k for k in ks if len(claimants[k]) > 1]
        if split:
            assign[i] = ks[0]
            held.update(ks)
            queue.append(dict(kind='split_candidate', keys=ks, cluster=c.get('label', ''),
                              others=[clusters[j].get('label', '') for k in split for j in claimants[k] if j != i]))
            continue
        if not ks:
            ph = f'new:{i}'
            resolution = c.get('resolution', 'unresolved')
            if resolution == 'established':
                resolution = evidence_tier(c['type'], c['anchors'])
            ops.append(dict(event='mint', key=ph, type=c['type'], label=c.get('label', ''),
                            resolution=resolution, anchors=sorted(c['anchors']),
                            aliases=sorted(c.get('aliases', ())), members=sorted(c.get('members', ())),
                            **({'status': c['status']} if c.get('status') else {}),
                            **({'basis': c['basis']} if c.get('basis') else {})))
            assign[i] = ph
            continue
        if len(ks) > 1:
            if not merge_ok(c, ks):
                assign[i] = ks[0]
                held.update(ks)
                queue.append(dict(kind='merge_candidate', keys=ks, cluster=c.get('label', '')))
                continue
            for k in ks[1:]:
                ops.append(dict(event='merge', key=k, into=ks[0], decided_by='rule',
                                basis='deterministic anchor link joins these keys'))
        k = ks[0]
        owned = set().union(*(state.keys[x]['anchors'] for x in ks))
        new_anchors = sorted(set(c['anchors']) - owned)
        new_aliases = sorted(set(c.get('aliases', ())) - set().union(*(state.keys[x]['aliases'] for x in ks)))
        new_members = sorted(set(c.get('members', ())) - set().union(*(state.members[x] for x in ks)))
        if new_anchors or new_aliases or new_members:
            ops.append(dict(event='attach', key=k, anchors=new_anchors, aliases=new_aliases, members=new_members,
                            **({'basis': c['basis']} if c.get('basis') else {})))
        if (state.keys[k]['resolution'] == 'recorded' and c.get('resolution') == 'established'
                and evidence_tier(c['type'], owned | set(c['anchors'])) == 'established'):
            ops.append(dict(event='status', key=k, resolution='established', decided_by='rule',
                            basis='evidence reached the established bar (a public identifier or a second source)'))
        assign[i] = k
    for k in sorted(held, key=_num):
        if state.keys[k]['status'] == 'active':
            ops.append(dict(event='status', key=k, status='provisional', basis='held for review'))
    return ops, assign, queue


def evidence_tier(type_, anchors):
    """`established` or `recorded` for a person's anchors (see RESOLUTION); other types are not tiered."""
    if type_ != 'person':
        return 'established'
    schemes = {a.split(':', 1)[0] for a in anchors}
    if schemes & PUBLIC_SCHEMES or len({SOURCE_FAMILY.get(x, x) for x in schemes}) >= 2:
        return 'established'
    return 'recorded'


def _num(key):
    p, n = key.split('-')
    return p, int(n)


def check(directory):
    state = State.load(directory)
    by = Counter((k['type'], k['status']) for k in state.keys.values())
    return state, by


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, default=DEFAULT_DIR)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('check')
    sub.add_parser('summary')
    sub.add_parser('shard')
    sub.add_parser('compress')
    lk = sub.add_parser('lookup')
    lk.add_argument('name')
    ap_ = sub.add_parser('apply')
    ap_.add_argument('proposal', type=Path)
    args = ap.parse_args()
    if args.cmd in ('check', 'summary'):
        state, by = check(args.dir)
        print(' '.join(f'{p.name}={p.stat().st_size / 1e6:.1f}MB' for p in shards(args.dir)))
        print(f'{state.seq} events, {len(state.keys)} keys, {len(state.anchor)} active anchors, {len(state.alias)} aliases')
        for (t, s), n in sorted(by.items()):
            print(f'  {t:12} {s:12} {n}')
        rel = Counter((p, len(sk) == 1 and len(ok) == 1) for _, sk, p, ok in state.relations())
        for p in sorted({p for p, _ in rel}):
            print(f'  relation     {p:12} {rel[p, True]} resolved, {rel[p, False]} dangling or ambiguous')
    elif args.cmd == 'shard':
        print(shard_legacy(args.dir) or 'no legacy events.jsonl')
    elif args.cmd == 'compress':
        print(' '.join(p.name for p in compress_closed(args.dir)) or 'nothing to compress')
    elif args.cmd == 'lookup':
        state = State.load(args.dir)
        for k in state.lookup(args.name):
            r = state.keys[k]
            print(k, r['type'], r['status'], r['resolution'], r['label'], sorted(r['anchors'])[:8])
    elif args.cmd == 'apply':
        opener = gzip.open if args.proposal.suffix == '.gz' else open     # large proposals are kept as .json.gz
        with opener(args.proposal, 'rt', encoding='utf-8') as fh:
            names = apply_proposal(args.dir, json.load(fh))
        print(f'minted {len(names)}')


if __name__ == '__main__':
    sys.exit(main())
