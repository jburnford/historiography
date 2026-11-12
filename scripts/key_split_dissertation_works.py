"""Split identities joined on the dissertation published (2026-11-08; user, on Christine Grandy p-44187: "use Grandy to
try and identify more split ids"). Grandy is in the graph three times: the AHA dissertation record (York PhD 2008),
an ORCID key with her 2020 article, and an LC authority for the book. Nothing but the name tied them, so no rule merged them.

This route takes every pair of live person keys with the same family name and first given name (full, not an
initial; middle initials compatible; no public identifier scheme on both sides; the name on at most six keys; no key
behind the merge guard) where one key holds an AHA dissertation and the other does not. They merge when the other
key's book or article is the dissertation published: it appears from one year before to fifteen years after the PhD
and the titles share three or more content words (stemmed, over 40% of the shorter title), or two that are each
rare among dissertation titles (the rule tested on Sol's held-LC verdicts, scripts/held_lc_rules.py). Identity by
works: the name only proposes the pair.

    python3 scripts/key_split_dissertation_works.py --out data/identifiers/split-dissertation-works-2026-11-08
"""
import argparse, collections, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
from identifiers import State, DEFAULT_DIR, materialise
from merge_guard import blocked_keys
from held_lc_rules import stems
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
PID = ('lcnaf', 'wd', 'orcid', 'viaf', 'gnd', 'isni', 'idref')


def norm(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def parse(label):
    l = re.sub(r'\(.*?\)|,?\s*\d{4}\??-(\d{4})?|\b(dr|prof|professor|sir|rev)\b\.?', '', norm(label)).strip(' ,.')
    if ',' in l:
        fam, giv = l.split(',', 1)
    else:
        t = l.split()
        if len(t) < 2:
            return None
        fam, giv = t[-1], ' '.join(t[:-1])
    g = [x for x in re.split(r'[\s.\-]+', giv) if x]
    fam = fam.strip()
    return (fam, g) if g and fam and len(g[0]) > 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    state = State.load(DEFAULT_DIR)
    blocked = blocked_keys(state)
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    db = duckdb.connect()
    works = collections.defaultdict(list)
    for k, t, y, kind in db.execute(f"""SELECT a."from", w.label, w.year, w.kind FROM {keylog(G, 'authored')} a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.year IS NOT NULL""").fetchall():
        for c in state.lookup(k):
            works[c].append((t, y, kind))
    by = collections.defaultdict(list)
    for k, v in live.items():
        p = parse(v['label'])
        if p:
            by[(p[0], p[1][0])].append((k, p[1]))
    df = collections.Counter()
    for k in live:
        for t, y, kind in works.get(k, ()):
            if kind == 'thesis':
                df.update(stems(t))

    def schemes(k):
        return {a.split(':', 1)[0] for a in live[k]['anchors']}

    def published(thesis_key, other_key):
        th = [(t, y) for t, y, kind in works.get(thesis_key, ()) if kind == 'thesis']
        for t, ty in th:
            tt = stems(t)
            for bt, by_, kind in works.get(other_key, ()):
                if kind == 'thesis' or norm(bt).startswith('review'):
                    continue
                bb = stems(bt); sh = tt & bb
                if tt and bb and -1 <= by_ - ty <= 15 and len(sh) >= 2 and len(sh) / min(len(tt), len(bb)) >= 0.4 \
                        and (len(sh) >= 3 or max(df[s] for s in sh) <= 25):
                    return t, ty, bt, by_, kind
        return None

    rep = collections.Counter(); found = collections.defaultdict(list)
    for name, ks in by.items():
        if len(ks) < 2:
            continue
        if len(ks) > 6:
            rep['name_on_7_or_more_keys'] += 1; continue
        aha = [(k, g) for k, g in ks if any(a.startswith('aha-phd:') for a in live[k]['anchors'])]
        for a, ga in aha:
            for o, go in ks:
                if o == a or any(x.startswith('aha-phd:') for x in live[o]['anchors']):
                    continue
                if len(ga) > 1 and len(go) > 1 and ga[1][0] != go[1][0]:
                    rep['middle_initials_differ'] += 1; continue
                if schemes(a) & schemes(o) & set(PID):
                    rep['identifier_on_both'] += 1; continue
                ev = published(a, o)
                if not ev:
                    rep['no_work_link'] += 1; continue
                if {a, o} & blocked:
                    rep['merge_guard'] += 1; continue
                found[o].append((a, ev))
    ops, sample = [], []
    clusters = collections.defaultdict(list)          # dissertation key -> [(other key, evidence)]
    for o, hits in found.items():
        if len({a for a, _ in hits}) > 1:
            rep['other_key_matches_two_dissertation_keys'] += 1; continue
        clusters[hits[0][0]].append((o, hits[0][1]))
    for a, members in clusters.items():
        group = [a] + [o for o, _ in members]
        # survivor: the key with more public identifier schemes, then more anchors
        into = sorted(group, key=lambda k: (-len(schemes(k) & set(PID)), -len(live[k]['anchors']), k))[0]
        seen = collections.Counter(x for k in group for x in schemes(k) & set(PID))
        if any(n > 1 for n in seen.values()):        # two of the other keys hold the same identifier scheme
            rep['group_with_clashing_identifiers'] += 1; continue
        for o, (t, ty, bt, by_, kind) in members:
            basis = (f'dissertation published: {live[a]["label"]}\'s thesis "{t[:150]}" ({ty}) and {live[o]["label"]}\'s '
                     f'{kind} "{bt[:150]}" ({by_}) share their title words (key_split_dissertation_works)')
            for away in ([o] if o != into else [a]):
                ops.append(dict(event='merge', key=away, into=into, decided_by='rule', basis=basis))
                rep['merged'] += 1
            if len(sample) < 200:
                sample.append(dict(thesis_key=a, other_key=o, label=live[a]['label'], thesis=[t, ty], work=[bt, by_, kind]))
    materialise(state, dict(basis='split identities: dissertation published', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    json.dump(dict(basis='split identities joined on the dissertation published (scripts/key_split_dissertation_works.py)',
                   decided_by='rule', ops=ops), open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
    json.dump(dict(counts=dict(rep), sample=sample), open(args.out / 'report.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(rep), indent=1))


if __name__ == '__main__':
    main()
