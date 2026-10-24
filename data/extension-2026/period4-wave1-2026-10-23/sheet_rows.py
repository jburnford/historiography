#!/usr/bin/env python3
"""Add the revision 1.156 Wikidata rows to data/people-wikidata.json (sixth pass, qlever_label_match_2026-10-23).

Rows come from the packet's `wikidata` list (verdict confirmed / correct / accepted → status accepted;
probable → status accepted with a probable note; ungrounded → skipped) and from the research agents'
identity-note QIDs listed in release/qlever-dates-2026-10-24.json (`extra_person_qids`). Life dates come from
that cache (QLever P569/P570 with precision and rank where the second query succeeded; the first query's
day-truncated values otherwise, marked precision 'unknown').

    python3 data/extension-2026/period4-wave1-2026-10-23/sheet_rows.py [--write]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
METHOD = 'qlever_label_match_2026-10-23'


def life_of(item):
    if not item:
        return None
    def pick(vals):
        if not vals:
            return None, None
        if isinstance(vals[0], str):   # first-query format: date only
            return vals[0], 'unknown'
        pref = [v for v in vals if v[2] == 'PreferredRank'] or vals
        return pref[0][0], pref[0][1]
    b, bp = pick(item.get('birth', []))
    d, dp = pick(item.get('death', []))
    return dict(birth=b, death=d, birth_precision=bp, death_precision=dp,
                source='Wikidata P569/P570 via QLever SPARQL (deprecated excluded; precision read where the query allowed)',
                retrieved='2026-10-24')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    packet = json.loads((HERE / 'release/editorial-additions.json').read_text())
    cache = json.loads((HERE / 'release/qlever-dates-2026-10-24.json').read_text())
    items = cache.get('items') or cache
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    labels = {p['id']: p['label'] for p in graph['people']}
    for p in packet.get('new_people', []):
        labels.setdefault(p['id'], p['label'])
    node_ids = {n['id'] for n in graph['nodes']} | {n['id'] for n in packet['nodes']}
    sheet = json.loads((ROOT / 'data/people-wikidata.json').read_text())
    have = {p['person_id'] for p in sheet['people']}
    rows = []
    checks = {w['person_id']: w for w in packet['wikidata'] if str(w.get('verdict')).lower() in ('confirmed', 'correct', 'accepted', 'probable')}
    for pid, q in cache.get('extra_person_qids', {}).items():
        checks.setdefault(pid, dict(person_id=pid, qid=q, verdict='confirmed', method=METHOD,
                                    statements_seen='QID confirmed by the research agent\'s QLever check recorded in its identity note (evidence files of 2026-10-23).'))
    for pid, w in checks.items():
        if pid in have or pid not in labels:
            print('skip', pid, 'already in sheet' if pid in have else 'no people record')
            continue
        item = items.get(w['qid'], {})
        probable = str(w.get('verdict')).lower() == 'probable'
        rows.append(dict(person_id=pid, node_id=pid if pid in node_ids else None, label=labels[pid], status='accepted',
                         wikidata=dict(qid=w['qid'], label=item.get('label'), description=item.get('description'), method=METHOD,
                                       basis=('Revision 1.156: QLever SPARQL label/alias match among humans with statements read '
                                              '(the WikidataMCP endpoint was down; the REST name search was not used). '
                                              + ('PROBABLE: ' if probable else '') + str(w.get('statements_seen', ''))[:900])),
                         life=life_of(item),
                         notes='Added with revision 1.156 (data/extension-2026/period4-wave1-2026-10-23/<id>/entry-draft.json wikidata_check or the entry draft\'s wikidata_checks).'
                               + (' Verdict probable; review when a second statement is read.' if probable else '')))
    print(len(rows), 'rows to add:', [r['person_id'] for r in rows])
    if args.write:
        sheet['people'].extend(rows)
        sheet['counts']['accepted'] = sum(1 for p in sheet['people'] if p['status'] == 'accepted')
        sheet['method'] += (' Sixth pass, 2026-10-24: the people of revision 1.156 (person entries Stoler, Trouillot, Wolfe, Cronon, Worster and roster '
                            'people grounded by the research agents) were checked by QLever SPARQL label match with statements read '
                            f'(wikidata.method = {METHOD}); dates fetched from QLever.')
        (ROOT / 'data/people-wikidata.json').write_text(json.dumps(sheet, ensure_ascii=False, indent=1) + '\n')
        print('written; accepted =', sheet['counts']['accepted'])


if __name__ == '__main__':
    main()
