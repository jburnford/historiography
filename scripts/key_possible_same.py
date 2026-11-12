"""Possible matches: same-name keys whose timelines fit, recorded as an edge, not a merge (2026-11-08; user: "you
could also create a possible match edge when the names and time lines mostly add up, but you can't confirm").

A pair of live person keys is a possible match when
- they share family name and first given name (full, not an initial), middle initials agree, and the name is on
  at most three live keys;
- no public identifier scheme (LC, Wikidata, ORCID, VIAF, GND, ISNI, IdRef) is on both, and neither key has
  recorded the other's LC authority as a namesake (`rejected:lcnaf:`);
- both have dated works, and their timelines fit: at least 80% of each key's dated works fall inside the other's
  career window (scripts/career_window.py: birth, PhD and death years) and none falls more than ten years outside;
  when neither key has a career window, all their dated works together span no more than fifty years.
Each key gets the member `possible-same:<other key>`; scripts/build_graph.py turns these into POSSIBLY_SAME edges.
Nothing merges here: a possible match is a lead for review (Sol/Terra, hand), and a later merge or a namesake verdict
settles it.

    python3 scripts/key_possible_same.py --out data/identifiers/possible-same-2026-11-08
"""
import argparse, collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
from identifiers import State, DEFAULT_DIR, materialise
from merge_guard import pooled_keys
from career_window import career_windows
from key_split_dissertation_works import parse, PID
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
OUTSIDE, SHARE, CAREER = 10, 0.8, 50


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    state = State.load(DEFAULT_DIR)
    pooled = pooled_keys(state)
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    win = career_windows(state)
    years = collections.defaultdict(list)
    for k, y in duckdb.connect().execute(f"""SELECT a."from", w.year FROM {keylog(G, 'authored')} a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.year IS NOT NULL""").fetchall():
        for c in state.lookup(k):
            years[c].append(y)

    def window(k):
        """The key's career window (birth/PhD/death); a key's own works do not bound where its other works fall."""
        return win.get(k, (None, None))

    def fits(ys, w):
        lo, hi = w
        out = [y for y in ys if (lo is not None and y < lo) or (hi is not None and y > hi)]
        far = [y for y in out if (lo is not None and y < lo - OUTSIDE) or (hi is not None and y > hi + OUTSIDE)]
        return not far and len(out) <= (1 - SHARE) * len(ys)

    def schemes(k):
        return {a.split(':', 1)[0] for a in live[k]['anchors']} & set(PID)

    def lcids(k):
        return {a[6:] for a in live[k]['anchors'] if a.startswith('lcnaf:')}

    def rejected(k):
        return {m[len('rejected:lcnaf:'):] for m in state.members.get(k, ()) if m.startswith('rejected:lcnaf:')}

    by = collections.defaultdict(list)
    for k, v in live.items():
        p = parse(v['label'])
        if p:
            by[(p[0], p[1][0])].append((k, p[1]))
    rep = collections.Counter(); ops = []; sample = []
    for name, ks in by.items():
        if len(ks) < 2:
            continue
        if len(ks) > 3:
            rep['name_on_4_or_more_keys'] += 1; continue
        for i, (a, ga) in enumerate(ks):
            for b, gb in ks[i + 1:]:
                rep['pairs'] += 1
                if len(ga) > 1 and len(gb) > 1 and ga[1][0] != gb[1][0]:
                    rep['middle_initials_differ'] += 1; continue
                if schemes(a) & schemes(b):
                    rep['identifier_on_both'] += 1; continue
                if lcids(a) & rejected(b) or lcids(b) & rejected(a):
                    rep['namesake_recorded'] += 1; continue
                if {a, b} & pooled:
                    rep['pooled_name'] += 1; continue
                if not years.get(a) or not years.get(b):
                    rep['undated_side'] += 1; continue
                if not (fits(years[a], window(b)) and fits(years[b], window(a))):
                    rep['timelines_clash'] += 1; continue
                if window(a) == (None, None) and window(b) == (None, None):
                    ys = years[a] + years[b]
                    if max(ys) - min(ys) > CAREER:        # neither key dated: the joint span must fit one career
                        rep['joint_span_over_a_career'] += 1; continue
                if f'possible-same:{b}' in state.members.get(a, ()):
                    rep['already_recorded'] += 1; continue
                span = lambda k: f'{min(years[k])}–{max(years[k])}'
                basis = (f'possible match, not confirmed: same name ({live[a]["label"]} / {live[b]["label"]}), timelines fit '
                         f'(works {span(a)} and {span(b)}), no identifier conflict (key_possible_same)')
                ops.append(dict(event='attach', key=a, anchors=[], aliases=[], members=[f'possible-same:{b}'], basis=basis))
                ops.append(dict(event='attach', key=b, anchors=[], aliases=[], members=[f'possible-same:{a}'], basis=basis))
                rep['possible_match'] += 1
                if len(sample) < 150:
                    sample.append(dict(a=a, b=b, labels=[live[a]['label'], live[b]['label']], works=[span(a), span(b)],
                                       anchors=[sorted(live[a]['anchors'])[:4], sorted(live[b]['anchors'])[:4]]))
    materialise(state, dict(basis='possible matches', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    json.dump(dict(basis='possible matches: same name, timelines fit, no identifier conflict (scripts/key_possible_same.py)',
                   decided_by='rule', ops=ops), open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
    json.dump(dict(counts=dict(rep), sample=sample), open(args.out / 'report.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(rep), indent=1))


if __name__ == '__main__':
    main()
