#!/usr/bin/env python3
"""Evidence packet: scholars Canadian History PhDs cite most, for full treatment in the atlas.

The atlas teaches historiography in Canada (user, 2026-10-12). This lists everyone cited by at
least ``--min-phds`` strict History PhDs completed 2009-2026, the years in which both large
programmes (Toronto and York) are in the corpus. For each person it gives the evidence an atlas
editor needs: citing PhDs and universities, early vs late share, most-cited works, co-citation
field, current atlas status, and the atlas entries whose rosters the same theses cite most
(lift over all theses), as a placement hint.

Identity decisions come from the packet's ``identity-decisions.csv``: mixed records lose their
foreign works, split records merge, and Wikidata IDs are corrected. Reads the citation graph and
the atlas read-only; writes ``candidates.csv`` and ``candidates.json`` into the packet folder.
Nothing here edits the atlas: entries are made through reviewed revision batches.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EARLY, LATE = (2009, 2014), (2020, 2026)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='dissertation citation output directory')
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--first-year', type=int, default=2009)
    parser.add_argument('--last-year', type=int, default=2026)
    parser.add_argument('--min-phds', type=int, default=50)
    parser.add_argument('--country', default='CA', help="country sub-graph (default CA; '' = main graph of all countries)")
    args = parser.parse_args()
    g = json.loads((args.out / 'graph.json').read_text())
    nodes = {n['id']: n for n in g['nodes']}
    # in_analysis is the main graph's strict set (all countries, 2026-10-20); this packet is Canadian.
    scoped = lambda n: n['type'] == 'Dissertation' and n.get('in_analysis') and (not args.country or n.get('country', 'CA') == args.country)
    diss = {k: n for k, n in nodes.items() if scoped(n) and n['year'] and args.first_year <= n['year'] <= args.last_year}
    every = {k: n for k, n in nodes.items() if scoped(n)}
    cites, works_of = defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in every:
            cites[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'])

    # Identity decisions: drop foreign works, merge split records, correct QIDs.
    decisions = {}
    with (args.packet / 'identity-decisions.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            decisions[r['person_key']] = r
    members = defaultdict(set)
    for k, r in decisions.items():
        target = r['decision'].split(':', 1)[1] if r['decision'].startswith('merge_into:') else k
        members[target].add(k)
    person_works = {}
    for head, keys in members.items():
        ws = set()
        for k in keys:
            foreign = {x.strip() for x in (decisions[k].get('foreign_work_ids') or '').split(';') if x.strip()}
            ws |= works_of[k] - foreign
        person_works[head] = ws
    for k, r in decisions.items():  # foreign works that belong to another listed person ('Seigneurial System' -> Cole Harris)
        if r.get('move_to'):
            person_works.setdefault(r['move_to'], set()).update(x.strip() for x in r['move_work_ids'].split(';') if x.strip())

    def citing(ws, pool):
        return {d for w in ws for d in cites[w] if d in pool}

    # Atlas status and rosters.
    atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    full = {p['id'] for p in atlas['people'] if p.get('node_id')}
    labels = {n['id']: n['label'] for n in atlas['nodes']}
    roster_of = defaultdict(set)
    for n in atlas['nodes']:
        for p in n.get('representative_people') or []:
            roster_of[p['person_id']].add(n['id'])
    sheet = {p['wikidata']['qid']: p['person_id'] for p in json.loads((ROOT / 'data/people-wikidata.json').read_text())['people']
             if (p.get('wikidata') or {}).get('qid')}
    xw = {}
    with (args.out / 'summary/atlas-people-crosswalk.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['graph_person']:
                xw[r['graph_person']] = r['atlas_person']
    # Entry rosters as graph people, for the placement hint.
    entry_people = defaultdict(set)
    for gp, ap in xw.items():
        for e in roster_of.get(ap, ()):
            entry_people[e].add(gp)
    entry_citing = {e: citing(set().union(*(works_of[p] for p in ps)), diss) for e, ps in entry_people.items()}
    views = json.loads((args.out / 'summary/views.json').read_text())
    field_label = {f['id']: f['label'] for f in views['fields']['fields']}
    work_field = {n['id']: field_label[n['field']] for n in views['fields']['nodes'] if n.get('field') is not None}

    early = {d for d in diss if EARLY[0] <= diss[d]['year'] <= EARLY[1]}
    late = {d for d in diss if LATE[0] <= diss[d]['year'] <= LATE[1]}
    rows = []
    for head, ws in person_works.items():
        c = citing(ws, diss)
        if len(c) < args.min_phds:
            continue
        r = decisions[head]
        qid = r.get('corrected_qid') or (nodes[head].get('qid') if r.get('qid_status') in ('correct', '') else '') or ''
        ap = sheet.get(qid) or next((xw[k] for k in members[head] if k in xw), None)
        status = 'full_entry' if ap in full else 'roster_only' if ap else 'not_in_atlas'
        top = sorted(ws, key=lambda w: -len(cites[w] & diss.keys()))[:5]
        fields = Counter(work_field[w] for w in ws if w in work_field)
        hints = []
        for e, ec in entry_citing.items():
            if e in roster_of.get(ap, set()) or len(ec) < 20:
                continue
            both = len(c & ec)
            lift = (both / len(c)) / (len(ec) / len(diss))
            if both >= 10 and lift >= 1.5:
                hints.append((lift, both, e))
        hints.sort(reverse=True)
        e_share, l_share = len(c & early) / len(early), len(c & late) / len(late)
        n = len(c)
        rows.append(dict(
            tier='100+' if n >= 100 else '75-99' if n >= 75 else f'{args.min_phds}-74',
            name=r.get('display_name') or nodes[head].get('name'), person_keys='; '.join(sorted(members[head])), qid=qid,
            qid_status=r.get('qid_status', ''), qid_candidate=r.get('qid_checked', '') if r.get('qid_status') == 'uncertain' else '', person_type=r.get('person_type', ''), description=r.get('description', ''),
            history_phds_2009_2026=n, share=round(n / len(diss), 4), universities=len({diss[d]['institution'] for d in c}),
            toronto_york=len([d for d in c if diss[d]['institution'] in ('toronto', 'york')]),
            share_2009_14=round(e_share, 4), share_2020_26=round(l_share, 4),
            trend='rising' if l_share > e_share * 1.25 else 'falling' if l_share < e_share * 0.8 else 'steady',
            history_phds_all_years=len(citing(ws, every)),
            cocitation_field=fields.most_common(1)[0][0] if fields else '',
            atlas_status=status, atlas_person=ap or '',
            atlas_roster_entries='; '.join(labels[e] for e in sorted(roster_of.get(ap, ())) if e in labels),
            placement_hints='; '.join(f'{labels.get(e, e)} (lift {l:.1f}, {b} theses)' for l, b, e in hints[:4]),
            top_works=' | '.join(f"{nodes[w]['title']} ({nodes[w].get('year') or 'n.d.'}; {len(cites[w] & diss.keys())})" for w in top),
            identity_notes=r.get('notes', '')))
    rows.sort(key=lambda r: -r['history_phds_2009_2026'])
    cols = list(rows[0])
    with (args.packet / 'candidates.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (args.packet / 'candidates.json').write_text(json.dumps(dict(
        description=__doc__.split('\n\n')[0], period=[args.first_year, args.last_year], dissertations=len(diss),
        min_phds=args.min_phds, counts=dict(Counter(r['atlas_status'] for r in rows)),
        tiers={t: dict(Counter(r['atlas_status'] for r in rows if r['tier'] == t)) for t in sorted({r['tier'] for r in rows})},
        person_types=dict(Counter(r['person_type'] for r in rows)), candidates=rows), indent=1, ensure_ascii=False))
    print(len(rows), dict(Counter(r['atlas_status'] for r in rows)), dict(Counter(r['person_type'] for r in rows)))


if __name__ == '__main__':
    main()
