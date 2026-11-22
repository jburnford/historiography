"""Step 2a: draw the audit samples (seed 20261121), stratified by verdict class.

    python3 data/identifiers/sol-proposals-2026-11-21/draw_samples.py
Writes audit/sample-<job>.json (the sampled cases, latest verdict line each).
"""
import gzip, json, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLEAN, AUDIT = HERE / 'clean', HERE / 'audit'


def load(name):
    return [json.loads(l) for l in gzip.open(CLEAN / f'{name}.latest.jsonl.gz', 'rt', encoding='utf-8')]


def draw(rows, key, plan, seed=20261121):
    rnd = random.Random(seed)
    by = defaultdict(list)
    for r in rows:
        by[key(r)].append(r)
    out = []
    for cls, n in plan.items():
        pool = sorted(by.get(cls, []), key=lambda r: str(r['case']))
        out += [dict(r, _stratum=cls) for r in rnd.sample(pool, min(n, len(pool)))]
    return out


plans = {
    '1-place-authors': (lambda r: r['verdict'], {'scholar': 14, 'official-or-participant': 10, 'journalist-or-popular': 6,
                                               'literary': 5, 'unclear': 5}),
    'mint-combined': (lambda r: r['mint_recommendation'], {'yes': 40, 'no': 20, 'hold': 20}),
    '3-mixed-profiles': (lambda r: r['verdict'], {'mixed': 20, 'two-people-one-key': 14, 'unclear': 5, 'clean': 1}),
    '4-orcid': (lambda r: {'same-person-two-iDs': 'same-person', 'same-person-two-keys': 'same-person'}.get(r['verdict'], r['verdict']),
                {'deposit-error': 30, 'same-person': 20, 'wrong-anchor-on-key': 10}),
    '5-seed-links': (lambda r: r['verdict'], {'yes': 24, 'no': 8, 'unclear': 8}),
}
for name, (key, plan) in plans.items():
    rows = load(name)
    s = draw(rows, key, plan)
    if name == '4-orcid':  # all 8 two-keys merge candidates are in the same-person stratum if drawn; force them in
        have = {r['case'] for r in s}
        extra = [dict(r, _stratum='same-person-two-keys (all)') for r in rows if r['verdict'] == 'same-person-two-keys' and r['case'] not in have]
        s += extra
    (AUDIT / f'sample-{name}.json').write_text(json.dumps(s, ensure_ascii=False, indent=1))
    print(name, len(s))
