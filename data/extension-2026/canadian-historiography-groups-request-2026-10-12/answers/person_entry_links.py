#!/usr/bin/env python3
"""Which atlas person entries do Canadian History PhDs read with each Canadian group?

The family view draws a person entry only when a relationship edge joins it to a member field,
so person entries without edges are invisible in the Canada family. This measures, for every
atlas person entry, the strict 2009-2026 History PhDs citing them and the share of those PhDs
that engage each Canadian group (citing works by two or more of its anchors, groups.json), with
the lift over that group's base rate. Candidates for evidenced edges, not edges.

Writes answers/person-entry-links.json. Run from anywhere.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
SCHOLARS = ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12'

g = json.loads((OUT / 'graph.json').read_text())
nodes = {n['id']: n for n in g['nodes']}
diss = {k for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis') and n['year'] and 2009 <= n['year'] <= 2026}
N = len(diss)
works_of, citing_of = defaultdict(set), defaultdict(set)
for e in g['edges']:
    if e['type'] == 'CITES' and e['source'] in diss:
        citing_of[e['target']].add(e['source'])
    elif e['type'] == 'AUTHORED':
        works_of[e['source']].add(e['target'])
spec = json.loads((PACKET / 'groups.json').read_text())
cands = {r['name']: r for r in csv.DictReader((SCHOLARS / 'candidates.csv').open())}
dec = {r['person_key']: r for r in csv.DictReader((SCHOLARS / 'identity-decisions.csv').open())}


def citers_of_keys(keys):
    out = set()
    for k in keys:
        bad = {x.strip() for x in (dec.get(k, {}).get('foreign_work_ids') or '').split(';') if x.strip()}
        for w in works_of[k] - bad:
            out |= citing_of[w]
    return out


def engaged(group):
    hits = Counter()
    for name in group['primary'] + group['also']:
        if name in cands:
            for d in citers_of_keys(cands[name]['person_keys'].split('; ')):
                hits[d] += 1
    return {d for d, k in hits.items() if k >= 2}


ENG = {x['id']: engaged(x) for x in spec['groups']}
atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
person_entries = {n['id']: n['label'] for n in atlas['nodes'] if n['entry_kind'] == 'person'}
edges = {(e['source'], e['target']) for e in atlas['edges']} | {(e['target'], e['source']) for e in atlas['edges']}
cross = defaultdict(set)
for r in csv.DictReader((OUT / 'summary/atlas-people-crosswalk.csv').open()):
    if r['atlas_person'] in person_entries and r['graph_person']:
        cross[r['atlas_person']].add(r['graph_person'])

rows = []
for pid, label in person_entries.items():
    c = citers_of_keys(cross.get(pid, ()))
    if not c:
        continue
    for gid, e in ENG.items():
        if not e:
            continue
        share = len(c & e) / len(c)
        rows.append(dict(person=pid, label=label, citing_phds=len(c), group=gid, engaged=len(c & e),
                         share=round(share, 3), lift=round(share / (len(e) / N), 2), has_edge=(pid, gid) in edges))
rows.sort(key=lambda r: (-r['engaged'], -r['lift']))
strong = [r for r in rows if r['citing_phds'] >= 20 and r['engaged'] >= 10 and r['lift'] >= 2.0]
best = {}
for r in rows:  # each person's strongest Canadian group by engaged PhDs, among those with lift >= 2
    if r['lift'] >= 2.0 and r['engaged'] > best.get(r['person'], {}).get('engaged', -1):
        best[r['person']] = r
by_person = defaultdict(list)
for r in rows:
    by_person[r['person']].append(r)
top_major = {pid: sorted(rs, key=lambda r: -r['engaged'])[:4] for pid, rs in by_person.items() if rs[0]['citing_phds'] >= 30}
out = dict(prepared='2026-10-13', phds=N, method=__doc__.strip().splitlines()[0],
           unmatched_person_entries=sorted(set(person_entries) - set(cross)),
           strongest_pair_per_person=sorted(best.values(), key=lambda r: -r['engaged']),
           strong_pairs=strong, top_groups_of_widely_cited=top_major)
(Path(__file__).parent / 'person-entry-links.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f'{N} PhDs; person entries matched {len(cross)}/{len(person_entries)}; strong pairs {len(strong)}')
for r in out['strongest_pair_per_person'][:30]:
    print(f"{r['label'][:24]:24} {r['citing_phds']:4} cite | {r['group']:26} {r['engaged']:3} ({r['share']:.0%}, lift {r['lift']}){' EDGE' if r['has_edge'] else ''}")
print('\nWidely cited person entries (30+ PhDs): their four most-engaged Canadian groups')
for pid, rs in sorted(top_major.items(), key=lambda kv: -kv[1][0]['citing_phds']):
    print(f"{rs[0]['label'][:22]:22} {rs[0]['citing_phds']:4} | " + '; '.join(f"{r['group'].replace('cdn_','')} {r['engaged']} ({r['share']:.0%}, x{r['lift']}){'*' if r['has_edge'] else ''}" for r in rs))
