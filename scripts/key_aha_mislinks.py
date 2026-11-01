"""Repair advisor keys joined to a namesake's dissertation by the AHA genealogy (2026-11-01). Writes a proposal.

key_aha joined each advisor token (`aha:<token>`) to the author of the dissertation the genealogy linked as
their own (`aha-phd:<record>`). `aha_links.doubts` finds links that are doubtful (see there). For each such
link still joined in the log:
- **Repaired by rule** when the key holds nothing else that depends on the link: the token, the record's
  author anchor, and harvested-thesis authors (`diss-author:`) whose thesis is that same dissertation. The
  record's anchors are detached and minted as their own person (labelled with the dissertator), and the
  advisor's key is relabelled with the advisor's name if it carried the dissertator's.
- When the advisor's hyphenated surname is listed in full on another record (`hyphen:<record>`), that
  record's author key merges into the advisor's key (the merge guard permitting).
- **Queued** otherwise: the key holds LC, ORCID, QID or other anchors that came with either side, so a reviewer
  decides (Thomas Kuehn and Hasia Diner, where only the directory's school disagrees).

    python3 scripts/key_aha_mislinks.py --out data/identifiers/aha-mislinks-2026-11-01
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from aha_links import doubts, family_index, fold
from identifiers import DEFAULT_DIR, State, _num, materialise
from key_aha import AHA, DIRECTORY, LINKED
from merge_guard import blocked_keys


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = list(csv.DictReader(f))
    with (AHA / 'genealogy/advisor-links.csv').open(newline='', encoding='utf-8') as f:
        links = list(csv.DictReader(f))
    dir_rows = defaultdict(list)
    with DIRECTORY.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            dir_rows[r['token']].append(r)
    by_id, by_family = {r['id']: r for r in records}, family_index(records)
    blocked = blocked_keys(state)
    ops, queue, rows, report = [], [], [], Counter()
    for l in links:
        if l['status'] not in LINKED or l['own_record'] not in by_id:
            continue
        rec = by_id[l['own_record']]
        why = doubts(l['advisor'], rec, dir_rows[l['advisor_id']], by_family)
        token, author = f'aha:{l["advisor_id"]}', f'aha-phd:{rec["id"]}'
        k = state.anchor.get(token)
        if not why or not k or state.anchor.get(author) != k:
            report['doubtful_not_joined_in_log' if why else 'link_fine'] += 1
            continue
        work = state.lookup(f'aha-diss:{rec["id"]}')
        theirs = {author} | {a for a in state.keys[k]['anchors'] if a.startswith('diss-author:')
                             and state.lookup('diss-thesis:' + a.split(':', 1)[1]) == work}
        rest = state.keys[k]['anchors'] - theirs - {token}
        row = dict(key=k, token=l['advisor_id'], advisor=l['advisor'], record=rec['id'], dissertator=rec['dissertator'],
                   year=rec['year'], department=rec['department'], directory_school=[d['degree_school'] for d in dir_rows[l['advisor_id']]],
                   doubts=why, other_anchors=sorted(rest))
        if rest or k in blocked:
            queue.append(dict(kind='advisor_own_record_doubtful', **row))
            report['queued_key_holds_other_anchors' if rest else 'queued_blocked'] += 1
            continue
        basis = f'AHA record {rec["id"]} ({rec["dissertator"]}, {rec["year"]}) is not advisor {l["advisor"]}\'s dissertation: {", ".join(why)}'
        ops.append(dict(event='detach', key=k, anchors=sorted(theirs), members=[], basis=basis))
        ops.append(dict(event='mint', key=f'new:{rec["id"]}', type='person', label=rec['dissertator'], resolution='recorded',
                        anchors=sorted(theirs), aliases=[], members=[], basis=f'author of AHA dissertation record {rec["id"]}'))
        if fold(state.keys[k]['label']) == fold(rec['dissertator']):
            ops.append(dict(event='relabel', key=k, label=l['advisor'], basis='the advisor\'s name, not the detached dissertator\'s'))
        report['repaired'] += 1
        for d in why:
            if d.startswith('hyphen:'):
                other = state.lookup(f'aha-phd:{d[7:]}')
                if len(other) == 1 and other[0] != k and other[0] not in blocked:
                    keep, gone = sorted([k, other[0]], key=_num)
                    ops.append(dict(event='merge', key=gone, into=keep,
                                    basis=f'AHA record {d[7:]} lists advisor {l["advisor"]} under the full hyphenated surname'))
                    if keep != k:
                        ops.append(dict(event='relabel', key=keep, label=l['advisor'], basis='the advisor\'s name'))
                    report['hyphen_record_merged'] += 1
        rows.append(row)
    materialise(state, dict(basis='aha mislinks', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis='AHA genealogy links to a namesake\'s dissertation',
                                                            decided_by='rule', ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'repaired.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), review_queue=len(queue))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
