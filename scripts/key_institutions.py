"""Key institutions (PID-PLAN.md section 3 and rollout step 5). Writes a proposal and a report; never mints.

Reads the ROR grounding (scripts/ground_institutions.py -> data/field-research/institutions-2026-10-31/
institution-strings.csv). Every ROR organisation that an `accepted` or `reviewed` name reaches becomes one
institution cluster:
- anchor `ror:<id>` (the ROR identifier without its https://ror.org/ prefix);
- aliases: the dissertation graph's `I:` slugs, as `diss-inst:<slug>` ('diss-inst:york', 'diss-inst:uk:oxford');
- members: every source name that reached it, as `inst-name:<name>`, and ROR's own Wikidata link as
  `ror-wikidata:<QID>` (ROR's claim, not checked here).
All are `established`: ROR is the public identifier. Names still in review or without a match get no key.

    python3 scripts/key_institutions.py --out DIR [--state data/identifiers]
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan

GROUNDING = ROOT / 'data/field-research/institutions-2026-10-31/institution-strings.csv'


def clusters_from(rows):
    by = defaultdict(lambda: dict(names=set(), slugs=set(), label='', wikidata=''))
    for r in rows:
        if r['decision'] not in ('accepted', 'reviewed') or not r['ror']:
            continue
        c = by[r['ror'].rsplit('/', 1)[-1]]
        c['label'], c['wikidata'] = r['ror_name'], r['wikidata']
        c['names'].add(r['string'])
        c['slugs'].update(r['diss_slugs'].split())
    clusters = []
    for ror, c in sorted(by.items()):
        members = {f'inst-name:{n}' for n in c['names']} | ({f'ror-wikidata:{c["wikidata"]}'} if c['wikidata'] else set())
        clusters.append(dict(type='institution', label=c['label'], anchors={f'ror:{ror}'},
                             aliases={f'diss-inst:{s}' for s in c['slugs']}, members=members,
                             resolution='established', basis='ROR grounding of source institution names (2026-10-31)'))
    return clusters


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    with GROUNDING.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    clusters = clusters_from(rows)
    state = State.load(args.state)
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='institution keying', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis='institution keying from the ROR grounding of 2026-10-31',
                                                            decided_by='build', ops=ops), ensure_ascii=False) + '\n')
    summary = dict(institutions=len(clusters), ops=dict(Counter(o['event'] for o in ops)), held=len(held),
                   with_dissertation_slug=sum(1 for c in clusters if c['aliases']),
                   with_ror_wikidata=sum(1 for c in clusters if any(m.startswith('ror-wikidata:') for m in c['members'])),
                   names=sum(len([m for m in c['members'] if m.startswith('inst-name:')]) for c in clusters))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
