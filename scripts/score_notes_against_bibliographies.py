#!/usr/bin/env python3
"""Score notes-reconstructed bibliographies against the theses' own bibliographies.

For theses that have both a parsed closing bibliography and notes, the bibliography is the
reference: a work rebuilt from the notes is *matched* when the bibliography has a work with
the same first-author surname and a title key that is equal, a prefix of the other (3+
words) or near-identical (the graph builder's merge rule). Reported per thesis and overall:

- **precision (lower bound)**: matched note works / note works. A miss can be a notes error,
  a bibliography parse error, or a work the author cited but did not list;
- **recall**: bibliography works found in the notes / citable bibliography works (secondary
  and unspecified sides; primary-source sections are scored apart, since archives are cited
  by shelfmark in notes).

Citable kinds and keys are those of ``build_dissertation_citation_graph.py``.
"""
import argparse
from collections import defaultdict
import difflib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dissertation_citation_graph import CITABLE, fold, title_key  # noqa: E402
from dissertation_names import normalise_first_authors  # noqa: E402


def keyed(e):
    if e['kind'] not in CITABLE or not e.get('surnames') or not e.get('title'):
        return None
    sur, tk = fold(e['surnames'][0]), title_key(e['title'])
    return (sur, tk) if sur and len(tk) >= 3 else None


def same(a, b):
    short, long_ = sorted((a, b), key=len)
    return a == b or (len(short.split()) >= 3 and long_.startswith(short)) or difflib.SequenceMatcher(None, a, b).ratio() > 0.92


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--notes', type=Path, required=True, help='notes-entries file to score')
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--raw-reference', action='store_true', help='score against the bibliography surnames as extracted')
    args = p.parse_args()
    note_works = defaultdict(list)
    for line in args.notes.open():
        e = json.loads(line)
        if (k := keyed(e)):
            note_works[e['dissertation']].append((k, e))
    want = set(note_works)
    bib, raw_bib = defaultdict(list), defaultdict(list)
    for line in (args.out / 'entries.jsonl').open():
        if line.split('"', 4)[3] not in want:  # rows open with {"dissertation": "<id>"
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e['dissertation'] in want:
            raw_bib[e['dissertation']].append(e)
    for did, rows_ in raw_bib.items():
        rows_.sort(key=lambda e: e['n'])
        if not args.raw_reference:  # comma-less names read in the bibliography's own order (dissertation_names.py)
            normalise_first_authors(rows_)
        bib[did] = [(k, e) for e in rows_ if (k := keyed(e))]
    rows = []
    for did, notes in note_works.items():
        ref = bib.get(did, [])
        if len(ref) < 20:
            continue
        by_sur = defaultdict(list)
        for (s, t), e in ref:
            by_sur[s].append((t, e))
        hit_ref = set()
        matched = 0
        misses = []
        for (s, t), e in notes:
            found = next((i for i, (rt, re_) in enumerate(by_sur.get(s, [])) if same(t.removesuffix('|a'), title_key(re_['title']))), None)
            if found is not None:
                matched += 1
                hit_ref.add((s, by_sur[s][found][0]))
            else:
                misses.append(f"{e['surnames'][0]} | {e['title'][:70]} | {e['kind']} | x{e.get('citations')}")
        sec = [(s, t) for (s, t), e in ref if e.get('section_side') != 'primary']
        prim = [(s, t) for (s, t), e in ref if e.get('section_side') == 'primary']
        rows.append(dict(dissertation=did, institution=notes[0][1]['institution'], note_works=len(notes), matched=matched,
                         precision=round(matched / len(notes), 3), bib_secondary=len(set(sec)),
                         recall_secondary=round(len(hit_ref & set(sec)) / max(1, len(set(sec))), 3),
                         recall_primary=round(len(hit_ref & set(prim)) / max(1, len(set(prim))), 3) if prim else None,
                         miss_sample=misses[:8]))
    tot_n = sum(r['note_works'] for r in rows)
    tot_m = sum(r['matched'] for r in rows)
    summary = dict(theses=len(rows), note_works=tot_n, matched=tot_m,
                   precision_pooled=round(tot_m / max(1, tot_n), 3),
                   precision_median=statistics.median(r['precision'] for r in rows) if rows else None,
                   recall_secondary_median=statistics.median(r['recall_secondary'] for r in rows) if rows else None,
                   by_institution_prefix={})
    groups = defaultdict(list)
    for r in rows:
        groups[r['institution'].split(':')[0]].append(r)
    for g, rs in sorted(groups.items()):
        summary['by_institution_prefix'][g] = dict(theses=len(rs), precision_median=statistics.median(r['precision'] for r in rs),
                                                    recall_secondary_median=statistics.median(r['recall_secondary'] for r in rs))
    args.report.write_text(json.dumps(dict(summary=summary, theses=rows), ensure_ascii=False, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
