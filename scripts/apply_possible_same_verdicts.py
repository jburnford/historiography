"""Outside verdicts (Terra) on POSSIBLY_SAME person pairs -> a review proposal (2026-11-09; queue from
scripts/export_possible_same_review.py, brief data/identifiers/possible-same-review-2026-11-09/BRIEF.md).

- `same` at high confidence: merge the two keys. The survivor is the key holding a public identifier (LC, Wikidata,
  ORCID, GND, VIAF, ISNI, IdRef), else the one more works cite, else the older key; its label stays. Not when both
  hold different LC, Wikidata, ORCID, ISNI or IdRef identifiers (VIAF and GND keep duplicate records, so those don't count), when either key is behind the merge guard (pooled or in an open conflict),
  or when either key is gone (already merged elsewhere): those are listed in held.json.
- `different` at high confidence: both keys drop `possible-same:<other>` and record `not-same:<other>`, so the pair is
  not proposed again.
- `same` at medium confidence (strong but inferred: thesis and book titles and the university line up): merged like
  high, unless Terra's own wording says a key is mixed or needs splitting (held). User, 2026-11-09, after the KG
  session read the top 25 by joint citations and a random 25 of the 801 medium 'same' verdicts (all one person;
  dissertation-to-book, ORCID, or a review byline's institution at the review date matching the scholar's post):
  "merge all that are the same person". (Earlier the same day they became `very-likely-same:` edges; those stay
  on the merged key, where they point at itself and the build ignores them.) --hedge-medium restores the edge.
- everything else (medium `different`, `unclear`) stays as it is and is listed in held.json for later passes.
--medium-only processes only the medium `same` verdicts (for batches applied before the rule).
The merge guard here ignores single-key Wikidata checks (an LC-to-Wikidata check that failed on birth year or name, a
GND link to a different QID): a pair merge neither settles nor depends on them, and they stay open on the merged key
(user, 2026-11-10, releasing 18 held pairs). A held 'merge candidate' item on the very pair is settled by recording
the Terra verdict in review-decisions.json.

    python3 scripts/apply_possible_same_verdicts.py <verdicts.jsonl> [...] --out <dir>
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State, DEFAULT_DIR, PUBLIC_SCHEMES
from merge_guard import SINGLE_KEY_CHECKS, blocked_keys
import keylog_snapshot

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('verdicts', type=Path, nargs='+')
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--medium-only', action='store_true')
ap.add_argument('--hedge-medium', action='store_true', help="medium 'same' as very-likely-same edges, not merges")
args = ap.parse_args()
state = keylog_snapshot.read_state()  # the SQLite cache (2026-11-09)
blocked = blocked_keys(state, ignore_single=SINGLE_KEY_CHECKS)
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
        medium_same = v['verdict'] == 'same' and v.get('confidence') == 'medium'
        if args.medium_only and not medium_same:
            continue
        text = v['basis'] + ' ' + ' '.join(e.get('says', '') for e in v.get('evidence', []))
        if medium_same and (re.search(r'mixed key|needs? split|splitting|conflat|two different (people|scholars)', text, re.I) or re.search(r'a different [A-Z][a-z]+ [A-Z]', text)):
            res['held_medium_same_mixed_key'] += 1; held.append(dict(v, why="medium same, but Terra says a key is mixed")); continue
        if medium_same and not args.hedge_medium:
            v = dict(v, confidence='high', basis='medium confidence, merged by the 2026-11-09 review rule: ' + v['basis'])
            medium_same = False
        if medium_same:
            if any(len(x) != 1 for x in live):
                res['held_key_gone'] += 1; held.append(dict(v, why='a key is no longer live')); continue
            ka, kb = live[0][0], live[1][0]
            if ka == kb:
                res['already_one_key'] += 1; continue
            for k, o in ((ka, kb), (kb, ka)):
                ops.append(dict(event='detach', key=k, anchors=[], aliases=[], members=[f'possible-same:{o}']))
                ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f'very-likely-same:{o}'],
                                basis=f"outside review (Terra, web sources), medium confidence: very likely one person with {o}: {v['basis'][:300]} Evidence: {src}"[:900]))
            res['very_likely_recorded'] += 1
            continue
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
