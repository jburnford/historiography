"""Outside verdicts (Terra) on POSSIBLY_SAME person pairs -> a review proposal (2026-11-09; queue from
scripts/export_possible_same_review.py, brief data/identifiers/possible-same-review-2026-11-09/BRIEF.md).

- `same` at high confidence: merge the two keys. The survivor is the key holding a public identifier (LC, Wikidata,
  ORCID, GND, VIAF, ISNI, IdRef), else the one more works cite, else the older key; its label stays. Not when both
  hold different LC, Wikidata, ORCID, ISNI or IdRef identifiers (VIAF and GND keep duplicate records, so those don't count), when either key is behind the merge guard (pooled or in an open conflict),
  or when either key is gone (already merged elsewhere): those are listed in held.json.
- `different` at high confidence: both keys drop `possible-same:<other>` and record `not-same:<other>`, so the pair is
  not proposed again.
- everything else (medium, unclear) stays as it is and is listed in held.json for later passes.

    python3 scripts/apply_possible_same_verdicts.py <verdicts.jsonl> [...] --out <dir>
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State, DEFAULT_DIR, PUBLIC_SCHEMES
from merge_guard import blocked_keys

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('verdicts', type=Path, nargs='+')
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
state = State.load(DEFAULT_DIR)
blocked = blocked_keys(state)
ops, held, res = [], [], Counter()
gone = set()


CLASH = {'lcnaf', 'wd', 'orcid', 'idref', 'isni'}   # VIAF and GND hold duplicate records of one person: no clash


def public(k):
    return {a.split(':', 1)[0]: a for a in state.keys[k]['anchors'] if a.split(':', 1)[0] in PUBLIC_SCHEMES}


def num(k):
    m = re.search(r'(\d+)$', k)
    return int(m.group(1)) if m else 10 ** 9


for vf in args.verdicts:
    for line in open(vf):
        v = json.loads(line)
        item = json.loads((vf.parent / v['item'] / 'item.json').read_text())
        a, b = item['a']['key'], item['b']['key']
        src = '; '.join(f"{e['url']} ({e['says'][:120]})" for e in v.get('evidence', [])[:3])
        live = [state.lookup(k) for k in (a, b)]
        if v.get('confidence') != 'high' or v['verdict'] not in ('same', 'different'):
            res[f"held_{v['verdict']}_{v.get('confidence')}"] += 1; held.append(dict(v, why='not high-confidence same/different')); continue
        if any(len(x) != 1 for x in live) or a in gone or b in gone:
            res['held_key_gone'] += 1; held.append(dict(v, why='a key is no longer live (merged or split since the export)')); continue
        ka, kb = live[0][0], live[1][0]
        if ka == kb:
            res['already_one_key'] += 1; continue
        if v['verdict'] == 'different':
            for k, o in ((ka, kb), (kb, ka)):
                ops.append(dict(event='detach', key=k, anchors=[], aliases=[], members=[f'possible-same:{o}']))
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f'not-same:{o}'],
                                basis=f"outside review (Terra, web sources): {k} and {o} are two people: {v['basis'][:300]} Evidence: {src}"[:900]))
            res['different_recorded'] += 1
            continue
        if ka in blocked or kb in blocked:
            res['held_merge_guard'] += 1; held.append(dict(v, why='merge guard (pooled key or open conflict)')); continue
        pa, pb = public(ka), public(kb)
        if any(pa[s] != pb[s] for s in set(pa) & set(pb) & CLASH):
            res['held_identifier_clash'] += 1; held.append(dict(v, why='the keys hold different identifiers of one scheme')); continue
        rank = lambda k, p, side: (bool(p), item[side]['citing_items'], item[side]['n_works'], -num(k))
        into, key = (ka, kb) if rank(ka, pa, 'a') >= rank(kb, pb, 'b') else (kb, ka)
        ops.append(dict(event='merge', key=key, into=into, decided_by='review',
                        basis=f"outside review (Terra, web sources): same person by works: {v['basis'][:300]} Evidence: {src}"[:900]))
        gone.add(key)
        res['same_merged'] += 1
args.out.mkdir(parents=True, exist_ok=True)
json.dump(dict(basis='POSSIBLY_SAME pairs: outside review verdicts (Terra), high confidence only', decided_by='review', ops=ops),
          open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open(args.out / 'held.json', 'w'), ensure_ascii=False, indent=1)
print(dict(res))
