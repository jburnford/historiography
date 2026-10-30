"""Build the atlas keying proposal (PID-PLAN.md v2, rollout step 2). Writes a proposal and a report; never mints.

Reads a committed atlas snapshot (default `git show HEAD:historiography-1920-2000.json`), so edits that
other sessions have in progress do not leak in. Run the proposal through `identifiers.py apply` only when
the atlas is quiet and the open decisions in PID-PLAN section 10 are settled.

    python3 scripts/key_atlas.py --out DIR [--rev HEAD] [--state data/identifiers]

Anchors are exact identities only. Atlas QIDs applied in bulk without individual review
(`bulk_roster_match_2026-09-22`) are reported as close matches, not anchors.
"""
import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan

CLOSE_QID_METHODS = {'bulk_roster_match_2026-09-22'}


def doi_of(url):
    m = re.match(r'https?://(?:dx\.)?doi\.org/(10\.\S+)', url or '')
    return m.group(1).lower().rstrip('.') if m else None


def atlas_clusters(g, people_sheet):
    clusters, report = [], defaultdict(Counter)

    def add(type_, label, anchors, aliases=(), resolution='editorial'):
        clusters.append(dict(type=type_, label=label, anchors=set(anchors), aliases=set(aliases), members=set(),
                             resolution=resolution))
        report['clusters'][type_] += 1

    for n in g['nodes']:
        add('entry', n['label'], [f'atlas:entry:{n["id"]}'], [f'entry:{n["id"]}'])
        for ev in (n.get('chronology') or {}).get('events', []):
            add('event', ev.get('label', ''), [f'atlas:chronology:{n["id"]}/{ev["id"]}'])

    qids = {}
    for r in people_sheet.get('people', []):
        if r.get('status') == 'accepted' and r.get('wikidata'):
            method = r['wikidata'].get('method', 'reviewed_mcp')
            strength = 'close' if method in CLOSE_QID_METHODS else 'exact'
            qids[r['person_id']] = (r['wikidata']['qid'], strength)
            report['atlas_qids'][strength] += 1
    claim_people = defaultdict(set)
    for e in g['claim_catalogue']['entities']:
        if e['type'] == 'person' and e.get('legacy_person_id'):
            claim_people[e['legacy_person_id']].add(f'claim-entity:{e["id"]}')
    entry_ids = {n['id'] for n in g['nodes']}
    for p in g['people']:
        qid, strength = qids.get(p['id'], (None, None))
        anchors = [f'atlas:person:{p["id"]}'] + ([f'wd:{qid}'] if strength == 'exact' else [])
        add('person', p['label'], anchors, [f'person:{p["id"]}', *sorted(claim_people.pop(p['id'], ()))],
            resolution='established')
        report['people']['with_person_entry'] += p['id'] in entry_ids
    report['unmatched_claim_people'] = dict(Counter({k: len(v) for k, v in claim_people.items()}))

    for e in g['edges']:
        add('claim', e.get('relationship', '')[:80], [f'atlas:edge:{e["id"]}'], [f'edge:{e["id"]}'])
    for e in g['journal_catalogue']['edges']:
        add('claim', e.get('relationship', '')[:80], [f'atlas:journal-edge:{e["id"]}'], [f'journal-edge:{e["id"]}'])
    for c in g['claim_catalogue']['claims']:
        add('claim', c.get('statement', '')[:80], [f'atlas:claim:{c["id"]}'], [f'claim:{c["id"]}'])

    # Sources are works. Sources sharing a DOI, and claim-catalogue works naming them, are one work.
    by_doi, works = defaultdict(list), []
    for s in g['sources']:
        d = doi_of(s.get('url'))
        if d:
            by_doi[d].append(s)
        else:
            works.append([s])
    works += list(by_doi.values())
    report['sources']['sharing_a_doi'] = sum(len(v) for v in by_doi.values() if len(v) > 1)
    claim_work = defaultdict(set)
    for e in g['claim_catalogue']['entities']:
        if e['type'] == 'work':
            for sid in e.get('legacy_source_ids', []):
                claim_work[sid].add(e['id'])
    for group in works:
        ids = [s['id'] for s in group]
        d = doi_of(group[0].get('url'))
        extra = sorted(set().union(*(claim_work.pop(i, set()) for i in ids)))
        add('work', group[0].get('title', '')[:80], [f'atlas:source:{i}' for i in ids] + ([f'doi:{d}'] if d else []),
            [f'source:{i}' for i in ids] + [f'claim-entity:{x}' for x in extra], resolution='established')
    report['unmatched_claim_works'] = sorted(set().union(*claim_work.values())) if claim_work else []

    issn_owner = defaultdict(list)
    for j in g['journal_catalogue']['nodes']:
        for i in j.get('issns') or []:
            issn_owner[i.upper()].append(j['id'])
    shared = {i for i, v in issn_owner.items() if len(v) > 1}
    report['journals']['issns_shared_by_titles'] = len(shared)
    for j in g['journal_catalogue']['nodes']:
        issns = [f'issn:{i.upper()}' for i in j.get('issns') or [] if i.upper() not in shared]
        add('journal', j['label'], [f'atlas:journal:{j["id"]}', *issns], [f'journal:{j["id"]}'], resolution='established')

    for e in g['claim_catalogue']['entities']:
        report['claim_entity_types'][e['type']] += 1
    report['strand_redirects_not_keyed'] = len(g.get('strand_redirects', []))
    return clusters, report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--rev', default='HEAD')
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    raw = subprocess.run(['git', '-C', str(ROOT), 'show', f'{args.rev}:historiography-1920-2000.json'],
                         capture_output=True, text=True, check=True).stdout
    sheet = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', f'{args.rev}:data/people-wikidata.json'],
                                      capture_output=True, text=True, check=True).stdout)
    clusters, report = atlas_clusters(json.loads(raw), sheet)
    state = State.load(args.state / 'events.jsonl')
    ops, assign, queue = plan(state, clusters)
    events, names = materialise(state, dict(basis=f'atlas keying from {args.rev}', ops=ops), 'dry-run', 'dry-run')
    rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short', args.rev], capture_output=True, text=True).stdout.strip()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis=f'atlas keying from {rev}', decided_by='build', ops=ops),
                                                       ensure_ascii=False, indent=0) + '\n')
    summary = dict(atlas_revision=rev, existing_events=state.seq, ops=Counter(o['event'] for o in ops),
                   would_mint=Counter(e['key'].split('-')[0] for e in events if e['event'] == 'mint'),
                   queue=queue[:50], queue_size=len(queue), **{k: dict(v) if isinstance(v, Counter) else v for k, v in report.items()})
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=dict) + '\n')
    print(json.dumps({k: summary[k] for k in ('atlas_revision', 'ops', 'would_mint', 'queue_size')}, default=dict))


if __name__ == '__main__':
    main()
