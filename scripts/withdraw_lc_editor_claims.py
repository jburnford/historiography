"""Withdraw LC editor claims the tightened statement rule no longer supports (2026-11-03). Writes a proposal.

key_lc_works.editor_by_statement made an added entry without a relator an editor when the record's statement of
responsibility (245 $c) spoke of editing and named the person anywhere in it. From 1619f70 the person must be named
in the part of the statement that speaks of editing ('edited by John T. Greenwood ; with Von Hardesty': Hardesty
did not edit). The relations already minted under the loose rule keep their `lc-edited:<lccn>:<lcid>` anchors;
this re-reads each one against the LC index:
- the record's 100/700 heading for the person: the heading with the authority's family name (accents ignored);
- kept when that heading carries an editor relator, or the tightened rule names it an editor;
- otherwise the anchor is detached, and a claim left with no anchor is withdrawn.
An anchor whose record or heading cannot be found is kept and counted (nothing to judge it by).

    python3 scripts/withdraw_lc_editor_claims.py --out data/identifiers/lc-editor-repair-2026-11-03
    python3 scripts/identifiers.py apply data/identifiers/lc-editor-repair-2026-11-03/proposal.json
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise
from key_cited_book_authors import LC_INDEX, LC_NAMES, fold
from key_lc_works import editor_by_statement, role_of


def judge(anchors):
    """{(lccn, lcid)} -> {(lccn, lcid): 'relator' | 'statement' | 'fails' | 'no_record' | 'no_heading'}"""
    db = duckdb.connect()
    db.execute("SET memory_limit = '3GB'")
    db.execute('CREATE TABLE a(lccn VARCHAR, lcid VARCHAR)')
    db.executemany('INSERT INTO a VALUES (?, ?)', sorted(anchors))
    family = dict(db.execute(f"""SELECT lcid, label FROM read_parquet('{LC_NAMES}')
                                 WHERE lcid IN (SELECT DISTINCT lcid FROM a)""").fetchall())
    family = {k: fold(v.split(',')[0]) for k, v in family.items()}
    resp = dict(db.execute(f"""SELECT trim(control), responsibility FROM read_parquet('{LC_INDEX}/records-*.parquet', union_by_name=true)
                               WHERE trim(control) IN (SELECT DISTINCT lccn FROM a)""").fetchall())
    heads = defaultdict(list)
    for control, tag, fam, rel in db.execute(f"""SELECT trim(control), tag, family, relators FROM read_parquet('{LC_INDEX}/headings-*.parquet')
                                                WHERE trim(control) IN (SELECT DISTINCT lccn FROM a) AND tag IN ('100', '700')""").fetchall():
        heads[control].append((tag, fam, rel))
    verdict = {}
    for lccn, lcid in anchors:
        if lccn not in heads:
            verdict[lccn, lcid] = 'no_record'
            continue
        mine = [h for h in heads[lccn] if fold(h[1]) and fold(h[1]) == family.get(lcid)]
        if not mine:
            verdict[lccn, lcid] = 'no_heading'
        elif any(role_of(tag, rel) == 'edited' for tag, _, rel in mine):
            verdict[lccn, lcid] = 'relator'
        elif any(editor_by_statement(tag, rel, fam, resp.get(lccn)) for tag, fam, rel in mine):
            verdict[lccn, lcid] = 'statement'
        else:
            verdict[lccn, lcid] = 'fails'
    return verdict


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    state = State.load(args.state)
    held = {}                                          # claim key -> anchors
    for anchor, key in state.anchor.items():
        if anchor.startswith('lc-edited:'):
            held.setdefault(key, set()).add(anchor)
    verdict = judge({tuple(a.split(':')[1:3]) for anchors in held.values() for a in anchors})
    report, ops, sample = Counter(), [], []
    for key, anchors in sorted(held.items()):
        bad = sorted(a for a in anchors if verdict[tuple(a.split(':')[1:3])] == 'fails')
        for a in anchors:
            report[verdict[tuple(a.split(':')[1:3])]] += 1
        if not bad:
            continue
        if set(bad) == state.keys[key]['anchors']:
            ops.append(dict(event='withdraw', key=key))
            report['claims_withdrawn'] += 1
        else:
            ops.append(dict(event='detach', key=key, anchors=bad))
            report['claims_detached'] += 1
        if len(sample) < 200:
            sample.append(dict(key=key, relation=state.relation.get(key), bad=bad))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="LC editor claim no longer supported: the person is named outside the part of the statement of "
              "responsibility (245 $c) that speaks of editing", decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
