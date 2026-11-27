#!/usr/bin/env python3
"""Key-log anchors on dissertation-graph person keys that a rebuild gave to someone else (2026-11-21).

The key log anchors a person on a graph key (`diss-person:<key>`). A graph key is a name key, and a rebuild can
change whose citations it holds: 'rodrigues|jose c' held José Honório Rodrigues's citations on 2026-11-05 (a
QID had pooled him into it) and holds José C. M. Rodrigues's on 2026-11-17, while José Honório is on
'rodrigues|jose'; 'brown|katherine e' held Callum G. Brown's until the pooled keys were split back
(dissertation_person_unpool.py). The canon maps then keyed the wrong circle, or none.

Two classes, both counted over the graph keys the canon maps can show (cited by ``--min`` strict theses in
some scope):

1. **Moved anchors.** The anchored key's display name now disagrees with the person's key-log label in its
   given names (namesake_check_groups.given_names_agree), and exactly one other graph key of the same surname,
   anchored to no one else, agrees with the label in full (names_agree_strict), or received the anchored key's
   works when the pool was split back. That key is the person's: written to
   ``person-key-crosswalk-2026-11-21.csv`` (old_key, new_key, person), which the canon network and its export
   read as a crosswalk until the key log moves the anchor, and proposed as a detach + attach
   (``data/identifiers/canon-anchor-fixes-2026-11-21/moved-anchors.proposal.json``).
2. **Unjoined twins.** An unanchored graph key whose display name agrees with an anchored key's display name
   and with the person's label, with the same first given name written out (or a spelling of it, 'Rafael' /
   'Raphael'), not initial-only: 'Thompson, Edward Palmer' beside E. P. Thompson, 'Bluteau, Rafael' beside
   'Bluteau, Raphael', 'Hsia, Ronnie Po-chia' beside 'Hsia, R. Po-chia'. Name agreement alone never joins
   keys (key_canon_map.py), so these are a proposal only (``twins.proposal.json``: attach the anchor), for review.

Reads the key log read-only (run under a frozen copy for consistency with the maps). Never applies anything.

    python3 scripts/canon_anchor_crosswalk.py [--min 12]
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dissertation_citation_graph import initial_only  # noqa: E402
from dissertation_person_unpool import load_overrides  # noqa: E402
from namesake_check_groups import given_names_agree, given_words, names_agree_strict  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
CROSSWALK = D / 'person-key-crosswalk-2026-11-21.csv'
OUT = ROOT / 'data/identifiers/canon-anchor-fixes-2026-11-21'


def graph_people(minimum):
    """graph key -> (display name, citing strict theses in its largest scope), after the unpool overrides."""
    moved, unpooled = load_overrides(D)
    people = {}
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            n = max(int(v) for c, v in r.items() if c.startswith('cited_by_') and c != 'cited_by_all' and v.isdigit())
            people[r['person_key']] = [r['name'], n]
    for k, u in unpooled.items():
        people[k] = [u['name'], max([int(u['cited_by_dissertations']), *json.loads(u['cited_by_country'] or '{}').values()])]
    gained = defaultdict(Counter)   # old key -> keys that received its works on the split
    for (_, old), new in moved.items():
        gained[old][new] += 1
    return people, {k for k, v in people.items() if v[1] >= minimum}, gained


def spelling(w):
    return re.sub(r'(.)\1', r'\1', w.replace('ph', 'f').replace('th', 't').replace('y', 'i'))


def twin_given(a, b):
    """The same first given name written out in both, allowing spellings ('Rafael' / 'Raphael')."""
    wa, wb = given_words(a), given_words(b)
    return bool(wa and wb) and len(wa[0]) > 1 and len(wb[0]) > 1 and spelling(wa[0]) == spelling(wb[0])


def second_name_conflict(old, lab, new):
    """The anchored key prints the label's first given name with another second one written out or as an initial
    ('José C. M' against 'José Honório'), and the candidate prints the label's second name."""
    wo, wl, wn = given_words(old), given_words(lab), given_words(new)
    if len(wo) < 2 or len(wl) < 2 or len(wn) < 2 or len(wl[0]) < 2 or len(wl[1]) < 2:
        return False
    return (wo[0] == wl[0] and not wl[1].startswith(wo[1]) and wn[0] == wl[0] and wn[1] == wl[1])


def twin(k2, n2, gk, name, lab):
    """Why graph key k2 may be the anchored person under another form, or None: a spelling of the first given
    name ('Rafael' / 'Raphael'); the full middle name of the anchored key's middle initial ('Edward Palmer' /
    'thompson|edward p'); or the label's own name key ('Hsia, Ronnie Po-chia')."""
    from build_dissertation_citation_graph import person_key
    w2, w1 = given_words(n2), given_words(name)
    if w2 and w1 and w2[0] != w1[0] and spelling(w2[0]) == spelling(w1[0]):
        return 'a spelling of the first given name'
    g1 = gk.split('|', 1)[1].split()
    if len(g1) == 2 and len(k2.split('|', 1)[1].split()) == 1 and len(w2) >= 2 and len(w2[1]) > 1 and w2[1][0] == g1[1]:
        return 'the full middle name of the anchored key\'s middle initial'
    wl = given_words(lab)
    if person_key(lab, ',' in lab)[0] == k2 and len(wl) >= 2 and len(w2) >= 2 and all(len(w) > 1 for w in wl[:2]) \
            and w2[:2] == wl[:2]:
        return 'the name key of the person\'s label, printing its two given names'
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--min', type=int, default=12)
    args = ap.parse_args()
    from identifiers import RETIRED, State
    state = State.load(ROOT / 'data/identifiers')
    people, in_scope, gained = graph_people(args.min)
    anchored = {}
    for a, k in state.anchor.items():
        if a.startswith('diss-person:'):
            anchored[a.split(':', 1)[1]] = k
    by_surname = defaultdict(list)
    for gk in in_scope:
        if '|' in gk:
            by_surname[gk.split('|', 1)[0]].append(gk)

    def label(p):
        return re.sub(r'\s*\([^)]*\)|,\s*(?:approximately\s+|active\s+)?\d{3,4}\??-.*$', '', state.keys[p]['label']).strip()

    moves, twins, unresolved = [], [], []
    for gk, p in sorted(anchored.items()):
        if gk not in people or p not in state.keys or state.keys[p].get('status') in RETIRED:
            continue
        lab = label(p)
        name = people[gk][0]
        if given_names_agree(name, lab):
            # 2. unanchored twins of a correctly anchored key
            if gk not in in_scope:
                continue
            for k2 in by_surname[gk.split('|', 1)[0]]:
                if k2 == gk or k2 in anchored or initial_only(k2):
                    continue
                n2 = people[k2][0]
                if given_names_agree(n2, name) and given_names_agree(n2, lab) and (why := twin(k2, n2, gk, name, lab)):
                    twins.append(dict(person=p, label=state.keys[p]['label'], anchored_key=gk, anchored_name=name,
                                      key=k2, name=n2, theses=people[k2][1], why=why))
            continue
        # 1. the anchored key's display name disagrees with the person's label: find where the person went
        if gk not in in_scope and not gained[gk]:
            continue   # off the maps, and not a split pool
        sur = gk.split('|', 1)[0]
        free = [k2 for k2 in by_surname[sur] if k2 != gk and anchored.get(k2, p) == p and not initial_only(k2)]
        via_split = [k2 for k2 in free if gained[gk].get(k2) and given_names_agree(people[k2][0], lab)]
        via_name = [k2 for k2 in free if names_agree_strict(people[k2][0], lab)]
        if len(via_split) == 1:
            moves.append(dict(person=p, label=state.keys[p]['label'], old_key=gk, old_name=name, new_key=via_split[0],
                              new_name=people[via_split[0]][0], theses=people[via_split[0]][1],
                              basis=f'the pooled key was split back; {gained[gk][via_split[0]]} of its works went to this key'))
        elif len(via_name) == 1 and second_name_conflict(name, lab, people[via_name[0]][0]):
            moves.append(dict(person=p, label=state.keys[p]['label'], old_key=gk, old_name=name, new_key=via_name[0],
                              new_name=people[via_name[0]][0], theses=people[via_name[0]][1],
                              basis='the anchored key now prints another person\'s second given name; this key, the only one of '
                                    'the surname agreeing with the label in full, prints the label\'s'))
        elif len(via_name) == 1 and len((given_words(lab) or [''])[0]) > 1:
            # the anchored key may still be the same person in another form ('Mª Fernanda', 'Wm', 'Ted'): attach only
            twins.append(dict(person=p, label=state.keys[p]['label'], anchored_key=gk, anchored_name=name, key=via_name[0],
                              name=people[via_name[0]][0], theses=people[via_name[0]][1],
                              why='the anchored key\'s name disagrees with the label; this key agrees with it in full'))
        else:
            unresolved.append(dict(person=p, label=state.keys[p]['label'], key=gk, name=name,
                                   candidates=sorted(set(via_split) | set(via_name))))
    with CROSSWALK.open('w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['old_key', 'new_key', 'person', 'old_name', 'new_name', 'new_theses', 'basis'])
        for m in moves:
            wr.writerow([m['old_key'], m['new_key'], m['person'], m['old_name'], m['new_name'], m['theses'], m['basis']])
    OUT.mkdir(parents=True, exist_ok=True)
    note = ('NOT APPLIED: a proposal for the user. Canon maps of 2026-11-21 (dissertation graph 2026-11-17, pooled keys split '
            'back by scripts/dissertation_person_unpool.py).')
    ops = []
    for m in moves:
        why = (f"diss-person:{m['old_key']} now names {m['old_name']!r}, not {m['label']!r}; {m['basis']} "
               f"({m['new_name']!r}, {m['theses']} theses)")
        ops.append(dict(event='detach', key=m['person'], anchors=[f"diss-person:{m['old_key']}"], members=[], basis=why))
        ops.append(dict(event='attach', key=m['person'], anchors=[f"diss-person:{m['new_key']}"], basis=why))
    (OUT / 'moved-anchors.proposal.json').write_text(json.dumps(dict(
        basis='Moved dissertation-graph anchors: a graph key the key log anchors to a person now holds another person\'s '
              'citations (a QID-pooled key split back, or a rebuild that renamed keys); the anchor moves to the graph key '
              'that holds the person. Class count in report.json. ' + note,
        decided_by='rule', ops=ops), indent=1, ensure_ascii=False) + '\n')
    tops = [dict(event='attach', key=t['person'], anchors=[f"diss-person:{t['key']}"],
                 basis=f"graph key {t['key']!r} ({t['name']!r}, {t['theses']} theses) beside {t['anchored_name']!r} "
                       f"(diss-person:{t['anchored_key']}), label {t['label']!r}: {t['why']}; name evidence only, for review")
            for t in twins]
    (OUT / 'twins.proposal.json').write_text(json.dumps(dict(
        basis='Unjoined twins: graph keys whose display name is a fuller form or a spelling of a keyed person\'s graph name and '
              'agrees with the key-log label (same first given name written out). Name agreement alone never joins, so each '
              'needs review before an attach. ' + note,
        decided_by='review', ops=tops), indent=1, ensure_ascii=False) + '\n')
    report = dict(min_theses=args.min, graph_keys_in_scope=len(in_scope), anchored_in_scope=sum(k in in_scope for k in anchored),
                  moved_anchors=len(moves), moved_via_split=sum(m['basis'].startswith('the pooled') for m in moves),
                  anchors_naming_someone_else_unresolved=len(unresolved), twins=len(twins),
                  moves=moves, unresolved=unresolved, twin_list=twins)
    (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}, indent=1))


if __name__ == '__main__':
    main()
