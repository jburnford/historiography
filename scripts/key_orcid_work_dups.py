"""ORCID works that duplicate the claimant's other works -> merges (2026-11-03). Writes a proposal.

key_orcid_works joined a claimed work to the claimant's keyed work of the same title only among works already in
the log, so a work an ORCID record lists twice (once with its DOI, once without: two ORCID entries) became two
works, and a work whose keyed label carries its author ('Ian Milligan, Rebel Youth: ...', an atlas source label)
was not recognised (CV benchmark, Ian Milligan: *Rebel Youth* twice). A work anchored only by `orcid-work:` is the
same work as another work of the same claimant when
- their whole titles agree (key_lc_work_dups.whole_title, after dropping a leading 'Name, ' that names the
  claimant), or one is the other cut short (four words or more: truncated labels), or their main titles agree
  (three words or more) and one of the two has no subtitle (two subtitles under one main title are a series:
  'Wikipédia par l'anecdote : le selfie du macaque' / ': l'article d'Alain Marleix revisité'); never a one-word or
  generic title ('Introduction': one person writes many);
- where both are dated, the years are within two;
- exactly one such work holds a DOI or LCCN (it is kept), or none does (the older key is kept).

    python3 scripts/key_orcid_work_dups.py --out data/identifiers/orcid-work-dups-2026-11-03
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, State, materialise
from key_lc_work_dups import whole_title


GENERIC = {'introduction', 'conclusion', 'conclusions', 'preface', 'foreword', 'afterword', 'epilogue', 'prologue',
           'editorial', 'editor s introduction', 'editors introduction', 'introduccion', 'presentacion', 'presentation',
           'apresentacao', 'einleitung', 'vorwort', 'avant propos', 'book review', 'review', 'acknowledgements'}


def _num(k):
    return int(k[2:])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    works = defaultdict(set)                       # person -> their works
    for _, subj, pred, obj in state.relations():
        if pred in ('authored', 'edited') and len(obj) == 1:
            for p in subj:
                works[p].add(obj[0])

    def year(w):
        ys = [int(m.rsplit(':', 1)[1]) for m in state.members.get(w, ()) if re.match(r'^(year|lc-first-year):\d{4}$', m)]
        return min(ys) if ys else None

    def titles(w, person):
        label = state.keys[w]['label']
        fam = person.split(',')[0] if ',' in person else (person.split() or [''])[-1]
        m = re.match(r'^([^,:]{2,60}),\s+(.+)$', label)
        if m and fam and fam.lower() in m.group(1).lower():
            label = m.group(2)                       # 'Ian Milligan, Rebel Youth' -> 'Rebel Youth'
        whole, main = whole_title(label), whole_title(label.split(':')[0])
        return whole, (main if len(main.split()) >= 3 else None), ':' in label

    def anchored(w):
        return any(a.startswith(('doi:', 'lccn:')) for a in state.keys[w]['anchors'])

    def loose(w):
        schemes = {a.split(':', 1)[0] for a in state.keys[w]['anchors']}
        return schemes == {'orcid-work'}
    into, report = {}, Counter()
    for p, ws in sorted(works.items(), key=lambda kv: _num(kv[0])):
        name = state.keys[p]['label']
        info = {w: (titles(w, name), year(w)) for w in ws}
        for w in sorted(ws, key=_num):
            if not loose(w) or w in into:
                continue
            (whole, main, sub), y = info[w]
            if len(whole.split()) < 2 or whole in GENERIC:
                continue                          # 'Introduction': one person writes many

            def agree(x):
                xw, xm, xs = info[x][0]
                short, long_ = sorted((whole, xw), key=len)
                return (xw == whole
                        or (len(short.split()) >= 4 and long_.startswith(short + ' '))     # a truncated label
                        or (main and xm == main and not (sub and xs)))                     # one has no subtitle
            same = [x for x in ws if x != w and x not in into and agree(x)
                    and not (y and info[x][1] and abs(y - info[x][1]) > 2)]
            if not same:
                continue
            firm = [x for x in same if anchored(x)]
            if len(firm) > 1:
                report['several_anchored_works'] += 1
                continue
            target = firm[0] if firm else min(same + [w], key=_num)
            if target == w:
                continue
            into[w] = target
            report['into_anchored' if firm else 'into_older_orcid_work'] += 1
    ops = [dict(event='merge', key=w, into=t, basis=f'one work listed twice: {state.keys[w]["label"][:110]} = {state.keys[t]["label"][:110]}')
           for w, t in sorted(into.items(), key=lambda kv: _num(kv[0]))]
    # a target merged itself: follow the chain
    for o in ops:
        while o['into'] in into:
            o['into'] = into[o['into']]
    materialise(state, dict(basis='orcid work duplicates', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='ORCID works without a DOI that duplicate the claimant\'s work of the same title', decided_by='build',
        ops=ops), ensure_ascii=False) + '\n')
    report['merged'] = len(ops)
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
