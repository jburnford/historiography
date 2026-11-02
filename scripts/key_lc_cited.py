"""Cited people beyond the canon map -> the key log through their cited works in LC (2026-11-01). Writes a proposal.

Input: shards of `lc_canon_people.py --cited-min 5 --local-index` (cited people with five or more citing
dissertations, below the canon map; each shard's canon-people-lc.csv). A row resolves a dissertation-graph
name key to an LC authority only through the person's own cited books: the same book in LC's catalogue,
under a heading whose name agrees, or LC's own source note citing the book.

One person cluster per LC authority:
- anchor `lcnaf:<id>`; members `diss-person:<name key>` for every name key resolved to it (name keys are
  build artefacts, so they are evidence here, not anchors);
- tier `exact` (a second book, or LC's own note cites the book) keys on its own: it joins the key that
  already holds the authority (Douglas Lorimer, Erika Dyck), or mints one (Joyce Lorimer, cited by 8);
- `candidate_single_book` joins only a key that already holds the authority through another route (two
  routes agree); otherwise it is counted and left;
- `candidate_initials_only` and `candidate_wikidata_disagrees` never key (an initial pools people).
Refused and queued: a key holding the authority whose name is incompatible, or a key that rejected it.

    python3 scripts/key_lc_cited.py --run data/field-research/lc-authorities-2026-10-30/cited-2026-11-01 \\
        --out data/identifiers/lc-cited-2026-11-01
"""
import argparse
import csv
import glob
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, State, materialise, plan
from key_lc_books import label_of
from key_registry import names_compatible


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', type=Path, required=True, help='directory of shard-*/canon-people-lc.csv')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    rows = []
    for path in sorted(glob.glob(str(args.run / 'shard-*' / 'canon-people-lc.csv'))):
        with open(path, newline='', encoding='utf-8') as f:
            rows += [r for r in csv.DictReader(f) if r['outcome'] == 'resolved']
    rejected = {(m.split(':', 1)[1], k) for k, ms in state.members.items() for m in ms if m.startswith('lcnaf-rejected:')}
    by_lc = defaultdict(list)
    for r in rows:
        by_lc[r['lcnaf']].append(r)
    report, queue, clusters = Counter(rows=len(rows)), [], []
    for lc, rs in sorted(by_lc.items()):
        owner = state.anchor.get(f'lcnaf:{lc}')
        tiers = {r['tier'] for r in rs}
        if 'exact' not in tiers and not (owner and 'candidate_single_book' in tiers):
            report['not_keyed_' + '+'.join(sorted(tiers))] += 1
            continue
        keep = [r for r in rs if r['tier'] == 'exact' or (owner and r['tier'] == 'candidate_single_book')]
        label = label_of(keep[0]['lc_label'])
        if owner and ((lc, owner) in rejected or not names_compatible(label, state.keys[owner]['label'])):
            queue.append(dict(kind='cited_lcnaf_key_name_differs' if (lc, owner) not in rejected else 'cited_lcnaf_rejected_on_key',
                              lcnaf=lc, label=label, key=owner, key_label=state.keys[owner]['label'],
                              name_keys=[r['graph_key'] for r in keep]))
            report['queued'] += 1
            continue
        members = {f'diss-person:{r["graph_key"]}' for r in keep}
        report['joined_existing_key' if owner else 'new_key'] += 1
        report['single_book_confirmed_by_existing_key'] += sum(r['tier'] == 'candidate_single_book' for r in keep)
        clusters.append(dict(type='person', label=label, anchors={f'lcnaf:{lc}'}, members=members, aliases=set(),
                             resolution='established',
                             basis=f'cited works in the dissertation graph are LC {lc}\'s books '
                                   f'({", ".join(sorted({r["tier"] for r in keep}))}; {", ".join(r["graph_key"] for r in keep[:3])})'))
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='lc cited', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis=f'cited people resolved to LC through their cited works ({args.run.name})', decided_by='build', ops=ops),
        ensure_ascii=False).encode() + b'\n'))
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held),
                   review_queue=len(queue) + len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
