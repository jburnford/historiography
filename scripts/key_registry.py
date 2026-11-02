"""Key the person registry's established individuals (PID-PLAN.md v2, rollout step 4). Writes a proposal; never mints.

Reads a registry build (data/person-registry/generated/vN/registry.duckdb). One cluster per individual whose
occurrences resolve at the `anchored` or `accepted` tier, plus every individual holding an atlas person:
- anchors: `atlas:person:<id>` (atlas people already keyed; ids the key log does not know are skipped),
  `orcid:<iD>`, and `wd:<QID>` (the registry holds at most one QID per individual); an individual with
  none of these is anchored on its Open Library author record(s) (`ol:<id>`), the only public identifier
  we hold for them (2026-10-31: William J. Turkel had no key);
- members: Open Library authors (`ol:<id>`) when another anchor exists, and Wikidata's LC
  authority for the QID as `lcnaf-wikidata:<id>` (Wikidata's claim, not checked; the Marion Kaplan case
  showed P244 can name a namesake).

Joins to keys made from other routes (section 5: anchors only, plus one agreement rule):
- the anchors above, through `identifiers.plan()`;
- **QID agreement with the canon route**: a canon key whose dissertation QID is title-verified
  (`dissertation-qid:<QID>:<title tier>`) and equals the individual's QID. Two independent routes chose the
  same Wikidata item (the registry through ORCID or Wikidata's own identifiers, the dissertation graph
  through a cited title). The canon key's `diss-person:` anchor joins the cluster, unless the key belongs
  to an atlas person the individual does not carry and the full first and family names differ (queued:
  the dissertation QID can name a namesake, as Ann Elias on Norbert Elias's key). A probable-tier
  dissertation QID only queues the pair for review.
Anchors shared by two individuals (the registry left them apart) are dropped from both and queued, so the
proposal never mints one anchor twice.

    python3 scripts/key_registry.py --registry data/person-registry/generated/v12/registry.duckdb \\
        --out data/identifiers/registry-v12-2026-10-31
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise, plan
from key_canon_map import TITLE_TIERS
from identity_routes import compatible
from lc_canon_people import as_credit, words
from merge_guard import guarded

ESTABLISHED = {'anchored', 'accepted'}


def same_name(a, b):
    """Full first given name and family name agree ('Peter N. Stearns' / 'Peter N Stearns';
    'Armitage, David' / 'David Armitage'), so 'Ann Elias' is not 'Norbert Elias'."""
    def parts(label):
        family, comma, given = label.partition(', ')
        w = words(f'{given} {family}' if comma else label)
        return (w[0], w[-1]) if len(w) >= 2 else None
    pa, pb = parts(a), parts(b)
    return bool(pa and pb and pa == pb and len(pa[0]) > 1)


def names_compatible(a, b):
    """Family name and first initial agree in either direction ('Jo Guldi' / 'Guldi, Joanna'), or one name's
    words contain the other's (mononyms, scripts compatible() cannot read)."""
    def fam_given(label):
        family, comma, given = label.partition(', ')
        if comma:
            return given, family
        t = label.split()
        return (' '.join(t[:-1]), t[-1]) if len(t) > 1 else ('', label)
    wa, wb = set(words(as_credit(a))), set(words(as_credit(b)))
    if not wa or not wb or wa <= wb or wb <= wa:
        return True
    (ga, fa), (gb, fb) = fam_given(a), fam_given(b)
    return bool((gb and compatible(as_credit(a), gb, fb)) or (ga and compatible(as_credit(b), ga, fa)))


def atlas_canon_merge(state, cluster, keys):
    """A rule merge (PID-PLAN section 5.3): one registry individual reaches an atlas person's key and a canon
    key, through its atlas record and a title-verified dissertation QID equal to its own QID, and the names
    agree in full ('Charles E. Rosenberg', keyed from the atlas after the canon map keyed 'Rosenberg,
    Charles E.'). The two keys must not carry different LC authorities."""
    if len(keys) != 2:
        return False
    kinds = {k: {a.split(':', 1)[0] for a in state.keys[k]['anchors']} for k in keys}
    atlas = [k for k in keys if 'atlas' in kinds[k]]
    canon = [k for k in keys if kinds[k] <= {'diss-person', 'lcnaf'}]
    if len(atlas) != 1 or len(canon) != 1 or not same_name(state.keys[atlas[0]]['label'], state.keys[canon[0]]['label']):
        return False
    lcs = [{a for a in state.keys[k]['anchors'] if a.startswith('lcnaf:')} for k in keys]
    return not (lcs[0] and lcs[1] and lcs[0] != lcs[1])


def load(registry):
    db = duckdb.connect(str(registry), read_only=True)
    rows = db.execute("""
        SELECT s.individual_id, s.people, coalesce(s.qids, []), s.label,
               list_distinct(list(r.status) FILTER (WHERE r.status IS NOT NULL))
        FROM individual_summary s LEFT JOIN resolution r USING (individual_id) GROUP BY ALL""").fetchall()
    qids = {q for r in rows for q in r[2]}
    lc = defaultdict(set)
    db.execute('CREATE TEMP TABLE want(qid VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(q,) for q in qids])
    for q, v in db.execute("SELECT qid, value FROM authority_ids WHERE scheme = 'lcnaf' AND qid IN (SELECT qid FROM want)").fetchall():
        lc[q].add(v)
    return rows, lc


def clusters_for(rows, lc, state, version):
    canon_by_qid, probable_by_qid = defaultdict(set), defaultdict(set)
    for k, ms in state.members.items():
        if state.keys[k]['type'] != 'person' or state.keys[k]['status'] not in ('active', 'provisional'):
            continue
        for m in ms:
            if m.startswith('dissertation-qid:'):
                _, q, tier = m.split(':', 2)
                (canon_by_qid if tier in TITLE_TIERS else probable_by_qid)[q].add(k)
    queue, report, out = [], Counter(), []
    for iid, people, qids, label, statuses in rows:
        atlas = [p.split(':', 1)[1] for p in people if p.startswith('atlas:')]
        if not (set(statuses or ()) & ESTABLISHED) and not atlas:
            report['probable_only_not_keyed'] += 1
            continue
        anchors, members = set(), set()
        for a in atlas:
            if f'atlas:person:{a}' in state.anchor:
                anchors.add(f'atlas:person:{a}')
            else:
                report['atlas_id_unknown_to_key_log'] += 1
        anchors |= {f'orcid:{p.split(":", 1)[1]}' for p in people if p.startswith('orcid:')}
        members |= {p for p in people if p.startswith('ol:')}
        for q in qids:
            anchors.add(f'wd:{q}')
            members |= {f'lcnaf-wikidata:{v}' for v in sorted(lc.get(q, ()))}
            joined = canon_by_qid.get(q, set())
            atlas_of = {k: {a for a in state.keys[k]['anchors'] if a.startswith('atlas:person:')} for k in joined}
            if len(joined) == 1 and atlas_of[k := next(iter(joined))] - anchors \
                    and not same_name(label, state.keys[k]['label']):
                # The key is an atlas person's and this individual is not: the dissertation QID on it was
                # chosen for the canon name and can name a namesake (Norbert Elias's carries Ann Elias's).
                queue.append(dict(kind='qid_agrees_with_atlas_keyed_canon', individual=iid, label=label, qid=q, key=k,
                                  key_label=state.keys[k]['label']))
            elif len(joined) == 1 and not names_compatible(label, state.keys[k]['label']):
                # Any canon key, atlas or not: the grounding's QID can be a namesake's (2026-11-01: Lynn Hunt's
                # key carried Megan Hunt's QID, so Megan Hunt's ORCID joined it; 25 such joins corrected).
                queue.append(dict(kind='qid_agrees_name_differs', individual=iid, label=label, qid=q, key=k,
                                  key_label=state.keys[k]['label']))
            elif len(joined) == 1:
                anchors |= {a for a in state.keys[k]['anchors'] if a.startswith('diss-person:')}
                report['joined_canon_by_qid_agreement'] += 1
            elif len(joined) > 1:
                queue.append(dict(kind='qid_on_several_canon_keys', individual=iid, label=label, qid=q, keys=sorted(joined)))
            for k in sorted(probable_by_qid.get(q, ())):
                queue.append(dict(kind='probable_dissertation_qid_agrees', individual=iid, label=label, qid=q, key=k))
        if not anchors and any(p.startswith('ol:') for p in people):
            # Established through their works with no ORCID or QID (William J. Turkel): the Open Library
            # author record is the only public identifier we hold, so it anchors the key until LC does.
            anchors = {p for p in people if p.startswith('ol:')}
            report['anchored_on_open_library_only'] += 1
        if not anchors:
            report['no_anchor'] += 1
            continue
        out.append(dict(type='person', label=label, anchors=anchors, members=members, aliases=set(),
                        resolution='established', basis=f'person registry {version} individual {iid}'))
    # Individuals reaching one existing key are one person seen twice by the registry (an atlas record and an
    # ORCID record joined through the same canon key): combine them, or plan() would hold the key as a split.
    by_key = defaultdict(list)
    for i, c in enumerate(out):
        for k in {state.anchor[a] for a in c['anchors'] if a in state.anchor}:
            by_key[k].append(i)
    parent = list(range(len(out)))
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for idx in by_key.values():
        for i in idx[1:]:
            parent[root(i)] = root(idx[0])
    groups = defaultdict(list)
    for i in range(len(out)):
        groups[root(i)].append(i)
    combined = []
    for idx in groups.values():
        c = out[idx[0]]
        for i in idx[1:]:
            c['anchors'] |= out[i]['anchors']
            c['members'] |= out[i]['members']
            c['basis'] += '; ' + out[i]['basis'].rsplit(' individual ', 1)[-1]
        if len({state.anchor[a] for a in c['anchors'] if a in state.anchor}) > 1:
            report['combined_reaching_several_keys'] += 1
        report['individuals_combined'] += len(idx) - 1
        combined.append(c)
    out = combined
    # an anchor new to the log must belong to one cluster only
    owners = defaultdict(list)
    for i, c in enumerate(out):
        for a in c['anchors']:
            if a not in state.anchor:
                owners[a].append(i)
    for a, idx in owners.items():
        if len(idx) > 1:
            queue.append(dict(kind='anchor_on_several_individuals', anchor=a, labels=[out[i]['label'] for i in idx]))
            for i in idx:
                out[i]['anchors'].discard(a)
                out[i]['members'].add(f'{a.split(":", 1)[0]}-shared:{a.split(":", 1)[1]}')
            report['shared_anchor_dropped'] += 1
    kept = [c for c in out if c['anchors']]
    report['clusters'] = len(kept)
    return kept, queue, report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--registry', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    version = args.registry.parent.name
    state = State.load(args.state)
    rows, lc = load(args.registry)
    clusters, queue, report = clusters_for(rows, lc, state, version)
    ops, assign, held = plan(state, clusters, guarded(state, lambda c, ks: atlas_canon_merge(state, c, ks), exclude=args.out))
    materialise(state, dict(basis='registry keying', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis=f'person registry {version} established individuals',
                                                            decided_by='build', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(registry=version, individuals=len(rows), **dict(report), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=len(queue) + len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
