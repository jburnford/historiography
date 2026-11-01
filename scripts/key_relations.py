"""Relations into the key log as claims (Fable review 2026-11-01, step 3). Writes a proposal; never mints.

One claim per relation, anchored on the source assertion(s) that make it, with endpoints given as the source's
own anchors so they follow every later merge or detach (see `identifiers.State.relations`):
- **supervised**: an AHA advisor token supervised an AHA dissertation (`aha-sup:<record>:<token>`; endpoints
  `aha:<token>` -> `aha-diss:<record>`), from the AHA keying build's supervision.csv. This replaces
  supervision-keys.csv, whose keys went stale as people merged.
- **authored**: the author of a dissertation, from the work's own source records: an AHA record
  (`aha-auth:<record>`: `aha-phd:<record>` -> `aha-diss:<record>`) and a harvested thesis
  (`diss-auth:<id>`: `diss-author:<id>` -> `diss-thesis:<id>`). When one work holds both and both authors
  resolve to one key, the claim holds both assertions and is `established`; when they resolve to two keys,
  both claims are minted (each is true to its source) and the pair is queued as a missed identity join.

Awarding institutions stay as the works' `awarded-by:` members for now (already in the log).

**Duplicates.** When later keying joins the endpoints of two claims (an AHA record and a harvested thesis found
to be one dissertation), the two claims say the same thing: the younger merges into the older, which becomes
`established` (two sources).

    python3 scripts/key_relations.py --supervision data/identifiers/aha-v14-2026-11-01/supervision.csv \\
        --out data/identifiers/relations-2026-11-01
    python3 scripts/identifiers.py apply data/identifiers/relations-2026-11-01/proposal.json.gz
"""
import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

from identifiers import DEFAULT_DIR, PREDICATES, State, _num, materialise


def typed(state, anchor, want):
    ks = state.lookup(anchor)
    return len(ks) == 1 and state.keys[ks[0]]['type'] == want


def wanted(state, supervision):
    """Desired claims: dicts with anchors (source assertions), subject, predicate, object."""
    out, queue, report = [], [], Counter()
    for r in supervision:
        rid, token = r['work'].split(':', 1)[1], r['advisor'].split(':', 1)[1]
        out.append(dict(anchors=[f'aha-sup:{rid}:{token}'], subject=r['advisor'], predicate='supervised', object=r['work']))
    for k, v in state.keys.items():
        if v['type'] != 'work' or v['status'] != 'active':
            continue
        sources = [(f'aha-auth:{a[9:]}', f'aha-phd:{a[9:]}', a) for a in sorted(v['anchors']) if a.startswith('aha-diss:')]
        sources += [(f'diss-auth:{a[12:]}', f'diss-author:{a[12:]}', a) for a in sorted(v['anchors']) if a.startswith('diss-thesis:')]
        if not sources:
            continue
        authors = {tuple(state.lookup(s[1])) for s in sources}
        if len(sources) > 1 and len(authors) == 1:
            out.append(dict(anchors=[s[0] for s in sources], subject=sources[0][1], predicate='authored', object=sources[0][2]))
            report['authored_two_sources_one_key'] += 1
            continue
        if len(sources) > 1:
            queue.append(dict(kind='thesis_authors_on_several_keys', work=k, label=v['label'],
                              authors={s[1]: state.lookup(s[1]) for s in sources}))
        for s in sources:
            out.append(dict(anchors=[s[0]], subject=s[1], predicate='authored', object=s[2]))
    return out, queue, report


def ops_for(state, claims, report):
    ops = []
    for c in claims:
        subj_type, obj_type = PREDICATES[c['predicate']]
        if not (typed(state, c['subject'], subj_type) and typed(state, c['object'], obj_type)):
            report[f'{c["predicate"]}_endpoint_unresolved'] += 1
            continue
        owners = {state.anchor[a] for a in c['anchors'] if a in state.anchor}
        if len(owners) > 1:
            report[f'{c["predicate"]}_assertions_on_several_claims'] += 1
            continue
        resolution = 'established' if len(c['anchors']) > 1 else 'recorded'
        if owners:
            k = owners.pop()
            new = [a for a in c['anchors'] if a not in state.anchor]
            if state.relation.get(k, {}).get('predicate') != c['predicate']:
                report[f'{c["predicate"]}_anchor_on_other_claim'] += 1
            elif new:
                ops.append(dict(event='attach', key=k, anchors=new, aliases=[], members=[],
                                basis='a second source makes the same assertion'))
                if state.keys[k]['resolution'] != 'established':
                    ops.append(dict(event='status', key=k, resolution='established', basis='two sources agree'))
                report[f'{c["predicate"]}_second_source_attached'] += 1
            else:
                report[f'{c["predicate"]}_already_keyed'] += 1
            continue
        ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution=resolution,
                        anchors=c['anchors'], relation=dict(subject=c['subject'], predicate=c['predicate'],
                                                            object=c['object'])))
        report[f'{c["predicate"]}_minted'] += 1
    return ops


def duplicate_ops(state, report):
    seen, ops, raised = {}, [], set()
    for c, subj, pred, obj in sorted(state.relations(), key=lambda x: _num(x[0])):
        if len(subj) != 1 or len(obj) != 1:
            continue
        sig = (subj[0], pred, obj[0])
        if sig not in seen:
            seen[sig] = c
            continue
        keep = seen[sig]
        ops.append(dict(event='merge', key=c, into=keep, basis='the same relation from a second source'))
        report[f'{pred}_duplicate_merged'] += 1
        if state.keys[keep]['resolution'] != 'established' and keep not in raised:
            ops.append(dict(event='status', key=keep, resolution='established', basis='two sources agree'))
            raised.add(keep)
    return ops


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--supervision', type=Path, required=True, help="AHA keying build's supervision.csv")
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with args.supervision.open(encoding='utf-8') as f:
        supervision = list(csv.DictReader(f))
    claims, queue, report = wanted(state, supervision)
    ops = ops_for(state, claims, report)
    ops += duplicate_ops(state, report)
    materialise(state, dict(basis='relations', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis=f'source records: AHA advisor field ({args.supervision.parent.name}); thesis authors',
        decided_by='build', ops=ops), ensure_ascii=False).encode() + b'\n'))
    (args.out / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    summary = dict(supervision_rows=len(supervision), **dict(sorted(report.items())),
                   ops=dict(Counter(o['event'] for o in ops)), review_queue=len(queue))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
