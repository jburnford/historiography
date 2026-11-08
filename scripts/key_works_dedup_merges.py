"""Merges from the JSTOR session's works-based dedup table (2026-11-08; user to that session: "we have the titles; use
them to merge"). /mnt/e/kg-review/dedup-by-works-2026-11-08.parquet pairs person keys that authored works with the
same main title (years within 3; review titles skipped; titles on more than 12 keys skipped; co-authors on one work
key excluded unless the names agree). Identity by works: the shared title is the fact, the name only proposes.

Merged here: pairs classed same_family or surname_variant with no LC/Wikidata/ORCID clash, both keys still live and
distinct, given names compatible (first given names agree in full, middle initials agree), no public identifier scheme
on both, and neither key behind the merge guard. Keys with initials only ('Taylor, A.') are never merged: such a key
pools citations to several people, so its works must be moved one by one, not the key folded into one person; they
are listed in initials.json.

    python3 scripts/key_works_dedup_merges.py --out data/identifiers/works-dedup-2026-11-08
"""
import argparse, collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
from identifiers import State, DEFAULT_DIR, materialise
from merge_guard import blocked_keys
from key_split_dissertation_works import norm, PID
import re

TABLE = '/mnt/e/kg-review/dedup-by-works-2026-11-08.parquet'


def given(label):
    l = re.sub(r'\(.*?\)|,?\s*\d{4}\??-(\d{4})?', '', norm(label)).strip(' ,.')
    g = l.split(',', 1)[1] if ',' in l else ' '.join(l.split()[:-1])
    return [x for x in re.split(r'[\s.\-]+', g) if x]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
    rows = duckdb.connect().execute(f"""SELECT a, b, label_a, label_b, name_class, shared_titles, examples, stranded
        FROM '{TABLE}' WHERE name_class IN ('same_family', 'surname_variant') AND NOT pid_clash ORDER BY stranded DESC""").fetchall()
    rep = collections.Counter(); ops = []; initials = []; merged_into = {}

    def live(k):
        r = state.lookup(k)
        return r[0] if len(r) == 1 and state.keys[r[0]]['status'] in ('active', 'provisional') else None

    def schemes(k):
        return {a.split(':', 1)[0] for a in state.keys[k]['anchors']} & set(PID)

    for a, b, la, lb, cls, n, ex, stranded in rows:
        a, b = live(a), live(b)
        a, b = merged_into.get(a, a), merged_into.get(b, b)
        if not a or not b:
            rep['retired'] += 1; continue
        if a == b:
            rep['already_one_key'] += 1; continue
        ga, gb = given(state.keys[a]['label']), given(state.keys[b]['label'])
        if not ga or not gb or len(ga[0]) < 2 or len(gb[0]) < 2:
            rep['initials_only'] += 1
            initials.append(dict(a=a, b=b, labels=[state.keys[a]['label'], state.keys[b]['label']], titles=list(ex), stranded=stranded))
            continue
        if ga[0] != gb[0] or (len(ga) > 1 and len(gb) > 1 and ga[1][0] != gb[1][0]):
            rep['given_names_differ'] += 1; continue
        if schemes(a) & schemes(b):
            rep['identifier_on_both'] += 1; continue
        if {a, b} & blocked:
            rep['merge_guard'] += 1; continue
        into, away = sorted([a, b], key=lambda k: (-len(schemes(k)), -len(state.keys[k]['anchors']), k))
        ops.append(dict(event='merge', key=away, into=into, decided_by='rule',
                        basis=f'same works: {state.keys[away]["label"]} and {state.keys[into]["label"]} both authored '
                              f'{n} work(s) of the same title, e.g. "{list(ex)[0][:150]}" (JSTOR session dedup_by_works; '
                              f'key_works_dedup_merges)'))
        merged_into[away] = into
        for k, v in list(merged_into.items()):
            if v == away:
                merged_into[k] = into
        rep['merged'] += 1
    materialise(state, dict(basis='works dedup', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    json.dump(dict(basis='merges on shared work titles (scripts/key_works_dedup_merges.py)', decided_by='rule', ops=ops),
              open(args.out / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
    json.dump(initials, open(args.out / 'initials.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(rep), open(args.out / 'report.json', 'w'), indent=1)
    print(json.dumps(dict(rep), indent=1))


if __name__ == '__main__':
    main()
