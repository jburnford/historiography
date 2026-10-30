"""Internal keys: append-only event log, single locked minter, anchor-based carry-forward (PID-PLAN.md v2).

The authority is `data/identifiers/events.jsonl`, one JSON event per line, tracked in Git. Current state
is derived from it on every read; nothing else is authoritative. Keys are `<prefix>-<n>`, never reused.
Builds and agents never mint directly: they write a proposal (a list of operations) and the minter
applies it under a lock, assigning numbers in order.

Vocabulary
- **anchor**: a strong identifier string that may match a key across builds (`atlas:person:x`,
  `orcid:0000-…`, `wd:Q…`, `lcnaf:n…`, `aha:…`, `doi:…`). An active anchor belongs to one key.
- **member**: any other constituent, e.g. a source occurrence ID. Members never drive matching.
- **alias**: an old or readable name (`slug:geertz`, `edge:edge_001`) that resolves to a key, including
  after the key is retired (lookup follows `replaced_by`).

    python3 scripts/identifiers.py check
    python3 scripts/identifiers.py summary
    python3 scripts/identifiers.py lookup slug:geertz
    python3 scripts/identifiers.py apply proposal.json [--basis TEXT]
"""
import argparse
import copy
import fcntl
import json
import os
import re
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
RESOLUTION = {'established', 'unresolved', 'editorial'}
KEY_RE = re.compile(r'^([a-z])-([1-9][0-9]*)$')
EVENTS = {'mint', 'attach', 'detach', 'merge', 'split', 'retype', 'withdraw', 'relabel', 'status'}


class LogError(ValueError):
    pass


class State:
    """Current state derived from the event log. `apply` validates one event and mutates the state."""

    def __init__(self):
        self.keys = {}
        self.anchor = {}            # active anchor -> key
        self.alias = {}             # alias -> key (permanent; may point at a retired key)
        self.members = defaultdict(set)
        self.top = Counter()        # highest number minted per prefix
        self.seq = 0

    @classmethod
    def load(cls, path):
        s = cls()
        if path.exists():
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if line.strip():
                    try:
                        s.apply(json.loads(line))
                    except (LogError, json.JSONDecodeError, KeyError) as e:
                        raise LogError(f'{path}:{n}: {e}') from e
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
        for a in anchors:
            self.anchor[a] = key
            self.keys[key]['anchors'].add(a)

    def _claim_aliases(self, key, aliases):
        for a in aliases:
            if self.alias.get(a, key) != key:
                raise LogError(f'alias {a} already names {self.alias[a]}')
        for a in aliases:
            self.alias[a] = key
            self.keys[key]['aliases'].add(a)

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
            self.top[m.group(1)] = int(m.group(2))
            self.keys[key] = dict(key=key, type=ev['type'], label=ev.get('label', ''), status=ev.get('status', 'active'),
                                  resolution=ev['resolution'], anchors=set(), aliases=set(), replaced_by=[])
            if self.keys[key]['status'] not in LIFECYCLE - RETIRED:
                raise LogError(f'bad initial status for {key}')
            self._claim_anchors(key, ev.get('anchors', []))
            self._claim_aliases(key, ev.get('aliases', []))
            self.members[key].update(ev.get('members', []))
        elif kind == 'attach':
            self._live(key)
            self._claim_anchors(key, ev.get('anchors', []))
            self._claim_aliases(key, ev.get('aliases', []))
            self.members[key].update(ev.get('members', []))
        elif kind == 'detach':
            k = self._live(key)
            for a in ev.get('anchors', []):
                if self.anchor.get(a) == key:
                    del self.anchor[a]
                k['anchors'].discard(a)
            self.members[key].difference_update(ev.get('members', []))
        elif kind == 'merge':
            k, into = self._live(key), self._live(ev['into'])
            if k['type'] != into['type'] or key == ev['into']:
                raise LogError(f'cannot merge {key} into {ev["into"]}')
            anchors = set(k['anchors'])
            self._release(key)
            k.update(status='merged', replaced_by=[ev['into']])
            self._claim_anchors(ev['into'], anchors)
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


# --- proposals ------------------------------------------------------------------------------------------
# A proposal is {"basis": str, "decided_by": "build|rule|review", "ops": [...]}. Ops use the event
# vocabulary; a mint op names a placeholder ("new:<anything>") instead of a key, and later ops in the same
# proposal may refer to that placeholder (e.g. split successors). The minter assigns real numbers.

def materialise(state, proposal, commit, date):
    """Turn a proposal into numbered events, validated against a scratch copy of the state."""
    nxt = Counter(state.top)
    names, events, seq = {}, [], state.seq
    ops = proposal['ops']
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
    scratch = copy.deepcopy(state)
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


def apply_proposal(directory, proposal, commit=None, date=None):
    """The only writer. Validates the whole proposal, then appends all its events or none."""
    log = directory / 'events.jsonl'
    with locked(directory):
        state = State.load(log)
        events, names = materialise(state, proposal, git_commit() if commit is None else commit,
                                    date or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
        with open(log, 'a') as fh:
            fh.write(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in events))
            fh.flush()
            os.fsync(fh.fileno())
    return names


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
            ops.append(dict(event='mint', key=ph, type=c['type'], label=c.get('label', ''),
                            resolution=c.get('resolution', 'unresolved'), anchors=sorted(c['anchors']),
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
        assign[i] = k
    for k in sorted(held, key=_num):
        if state.keys[k]['status'] == 'active':
            ops.append(dict(event='status', key=k, status='provisional', basis='held for review'))
    return ops, assign, queue


def _num(key):
    p, n = key.split('-')
    return p, int(n)


def check(directory):
    state = State.load(directory / 'events.jsonl')
    by = Counter((k['type'], k['status']) for k in state.keys.values())
    return state, by


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, default=DEFAULT_DIR)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('check')
    sub.add_parser('summary')
    lk = sub.add_parser('lookup')
    lk.add_argument('name')
    ap_ = sub.add_parser('apply')
    ap_.add_argument('proposal', type=Path)
    args = ap.parse_args()
    if args.cmd in ('check', 'summary'):
        state, by = check(args.dir)
        print(f'{state.seq} events, {len(state.keys)} keys, {len(state.anchor)} active anchors, {len(state.alias)} aliases')
        for (t, s), n in sorted(by.items()):
            print(f'  {t:12} {s:12} {n}')
    elif args.cmd == 'lookup':
        state = State.load(args.dir / 'events.jsonl')
        for k in state.lookup(args.name):
            r = state.keys[k]
            print(k, r['type'], r['status'], r['resolution'], r['label'], sorted(r['anchors'])[:8])
    elif args.cmd == 'apply':
        names = apply_proposal(args.dir, json.loads(args.proposal.read_text()))
        print(f'minted {len(names)}')


if __name__ == '__main__':
    sys.exit(main())
