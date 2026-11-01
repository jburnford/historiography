"""Identity tier and match strength on existing person keys (2026-11-01, after the Fable review). Writes a proposal.

1. **Tier.** Person keys minted `established` whose anchors do not reach the bar in `identifiers.evidence_tier`
   (a public identifier, or two independent sources) get a `status` event to `recorded`. From now on plan()
   applies the tier itself and raises a key when later evidence reaches the bar.
2. **Strength.** A `wd:` anchor is a `close` match, not an exact one, when the registry reached the QID only
   through Wikidata's Open Library link (P648, about 97.5% right in the v12 benchmark) and nothing else on
   the key confirms it: no LC route (`wd-via:lc-p244`), no title-verified dissertation link, no atlas
   entry. It gets the member `close:wd:<QID>`, so an export writes skos:closeMatch, not owl:sameAs.

    python3 scripts/key_tiers.py --registry data/person-registry/generated/v14/registry.duckdb \\
        --out data/identifiers/tiers-2026-11-01
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, evidence_tier, materialise
from key_canon_map import TITLE_TIERS


def p648_only(registry):
    db = duckdb.connect(str(registry), read_only=True)
    bases = defaultdict(set)
    for b, basis in db.execute("SELECT b, basis FROM person_links WHERE b LIKE 'wd:%'").fetchall():
        bases[b].add(basis)
    return {q for q, bs in bases.items() if bs == {'wikidata_P648'}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--registry', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    weak = p648_only(args.registry)
    ops, report = [], Counter()
    for k in sorted(state.keys, key=lambda x: (x[0], int(x[2:]))):
        v = state.keys[k]
        if v['type'] != 'person' or v['status'] not in ('active', 'provisional'):
            continue
        if v['resolution'] == 'established' and evidence_tier('person', v['anchors']) == 'recorded':
            ops.append(dict(event='status', key=k, resolution='recorded', decided_by='rule',
                            basis='one source record only: no public identifier, no second source'))
            report['to_recorded'] += 1
        members = state.members[k]
        atlas = any(a.startswith('atlas:') for a in v['anchors'])
        for a in sorted(x for x in v['anchors'] if x.startswith('wd:')):
            q = a[3:]
            confirmed = atlas or 'wd-via:lc-p244' in members or any(
                m.startswith(f'dissertation-qid:{q}:') and m.rsplit(':', 1)[1] in TITLE_TIERS for m in members)
            if a in weak and not confirmed and f'close:{a}' not in members:
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f'close:{a}'], decided_by='rule',
                                basis='QID reached only through Wikidata P648 (Open Library); close match'))
                report['wd_close'] += 1
            elif a in weak:
                report['wd_p648_but_confirmed'] += 1
    materialise(state, dict(basis='tiers', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='identity tier (recorded vs established) and close-match QIDs', decided_by='rule', ops=ops),
        ensure_ascii=False) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
