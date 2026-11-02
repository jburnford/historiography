"""LC book works that are one book split in two -> merges (2026-11-02). Writes a proposal.

key_lc_works.py groups editions by lead person and main title (245 $a). Older records carry the subtitle in
$a after a semicolon or comma, with no $b (*Retreat from China; British policy in the Far East, 1937-1941*
beside *Retreat from China: British policy...*), so one book became two works, and a thesis published as it
matched both (published-as review queue). Two LC works are one book when:
- a keyed person authored or edited both (`authored` / `edited` relations from the LC catalogue);
- their whole titles (statement of responsibility after ' / ' dropped; case, accents, apostrophes,
  punctuation and a leading English article ignored) are the same, word for word.
They merge into the older key.

    python3 scripts/key_lc_work_dups.py --out data/identifiers/lc-work-dups-2026-11-02
"""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, State, materialise


def whole_title(label):
    t = re.sub(r"['’‘ʼ]", '', label.split(' / ')[0])
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    w = re.sub(r'[^a-z0-9 ]+', ' ', t).split()
    while w and w[0] in ('the', 'a', 'an'):
        w = w[1:]
    return ' '.join(w)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    groups = defaultdict(set)                          # (person, whole title) -> LC works
    for _, subj, pred, obj in state.relations():
        if pred not in ('authored', 'edited') or len(obj) != 1:
            continue
        w = obj[0]
        if not any(a.startswith('lccn:') for a in state.keys[w]['anchors']):
            continue
        t = whole_title(state.keys[w]['label'])
        if not t:
            continue
        for p in subj:
            groups[p, t].add(w)
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for ws in groups.values():
        ws = sorted(ws, key=lambda k: int(k[2:]))
        for w in ws[1:]:
            a, b = find(ws[0]), find(w)
            if a != b:
                parent[max(a, b, key=lambda k: int(k[2:]))] = min(a, b, key=lambda k: int(k[2:]))
    ops, report = [], Counter()
    for w in sorted(parent, key=lambda k: int(k[2:])):
        into = find(w)
        ops.append(dict(event='merge', key=w, into=into,
                        basis=f'one LC book catalogued as two works: {state.keys[w]["label"][:120]} = {state.keys[into]["label"][:120]}'))
        report['merged'] += 1
    report['books'] = len({find(w) for w in parent})
    materialise(state, dict(basis='lc work duplicates', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='LC book works by the same keyed person with the same whole title are one book', decided_by='build',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
