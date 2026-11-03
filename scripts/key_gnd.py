"""GND, Wikidata, VIAF and ISNI for keys through the GND's links to LC (lesson 2 of the user's probes; 2026-11-03).

The GND (Deutsche Nationalbibliothek) states, for many of its person records, the LC authority, Wikidata item,
VIAF cluster and ISNI of the same person (owl:sameAs; scripts/gnd_person_index.py). Wikidata items without
P244 are found this way (Cunfer, Handy, Regehr, Stewart, McCannon, Kitzan: items with a GND id but no LC id),
and every key gains the PIDs LINCS can use as entity URIs. Checks:
- **LC route** (a key with one `lcnaf:`): exactly one GND person record names the authority, a differentiated
  person (Tp), naming no other LC authority; its preferred name agrees with the key's label
  (key_lc_wikidata.name_agrees) and its birth year with LC's (two years either way). Then `gnd:` and, when the
  record names exactly one, `viaf:` and `isni:` are attached (member `gnd-via:lc`).
- **Wikidata through GND**: when the record names exactly one item, and no other GND record names it, the item
  is read on WDQS: a human, a label or alias agreeing with the key's name, no precise birth year more than two
  years off, and no LC authority (P244) and no GND id (P227, the record's older ids allowed) other than the ones in hand. Then `wd:` is attached
  too (member `wd-via:gnd`). An item that fails is queued; the GND ids still attach.
- **Wikidata route** (a key with one `wd:` and no `gnd:`, not reached above): the one GND record naming the item,
  its name agreeing, gives `gnd:`, `viaf:`, `isni:` (member `gnd-via:wd`), and nothing else.
A key already holding a different QID or GND id is queued. VIAF or ISNI ids another key already holds, or two
separate clusters share, are left off (VIAF clusters conflate namesakes). A QID or GND id another key holds, or
two clusters share (an LC key and a Wikidata key that GND ties together), makes the keys one person through two
authorities, merged by key_lc_wikidata's rule (labels compatible, LC authorities not different) behind the
merge guard, else held.

    python3 scripts/key_gnd.py --gnd /mnt/e/gnd/gnd-persons.parquet \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/identifiers/gnd-2026-11-03
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise, plan
from key_lc_wikidata import item_aliases, merge_rule, name_agrees, precise_births
from lc_canon_people import as_credit
from lc_resolve_authorities import label_dates, life, load_names
from merge_guard import guarded
from review_atlas_qids import sparql

ROOT = Path(__file__).resolve().parents[1]


def year(v):
    v = (v or '').lstrip('-')
    return int(v[:4]) if v[:4].isdigit() else None


def gnd_records(path):
    """LC id -> [record], QID -> [record] for the GND's differentiated persons (and LC id -> all records, to see
    an authority named by an undifferentiated name record too)."""
    rows = duckdb.sql(f"SELECT gnd, kind, name, birth, lc, wd, viaf, isni, gnd_alt FROM '{path}'").fetchall()
    by_lc, by_wd = defaultdict(list), defaultdict(list)
    for gnd, kind, name, birth, lc, wd, viaf, isni, alt in rows:
        r = dict(gnd=gnd, kind=kind, name=name, birth=year(birth), lc=lc, wd=wd, viaf=viaf, isni=isni, alt=alt)
        for x in lc:
            by_lc[x].append(r)
        for q in wd:
            by_wd[q].append(r)
    return by_lc, by_wd


def items(qids, cache):
    """QID -> dict(labels, human, lc: P244 values, gnd: P227 values, births)."""
    out = {q: dict(labels=set(), human=False, lc=set(), gnd=set(), births=set()) for q in qids}
    qids = sorted(qids)
    for i in range(0, len(qids), 150):
        part = qids[i:i + 150]
        query = """SELECT ?item ?label ?human ?lc ?gnd ?birth WHERE { VALUES ?item { %s }
                OPTIONAL { ?item rdfs:label ?label FILTER(lang(?label) IN ('en', 'mul', 'de', 'fr')) }
                OPTIONAL { ?item wdt:P244 ?lc } OPTIONAL { ?item wdt:P227 ?gnd } OPTIONAL { ?item wdt:P569 ?birth }
                BIND(EXISTS { ?item wdt:P31 wd:Q5 } AS ?human) }""" % ' '.join(f'wd:{q}' for q in part)
        for r in sparql(query, cache, 'gnd-items-' + hashlib.sha1(query.encode()).hexdigest()[:12]):
            it = out[r['item']['value'].rsplit('/', 1)[-1]]
            for f in ('lc', 'gnd'):
                if f in r:
                    it[f].add(r[f]['value'])
            if 'label' in r:
                it['labels'].add(r['label']['value'])
            if 'birth' in r and year(r['birth']['value']):
                it['births'].add(year(r['birth']['value']))
            it['human'] = it['human'] or r.get('human', {}).get('value') == 'true'
    return out


def off(a, years):
    return bool(a and years and all(abs(a - b) > 2 for b in years))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--gnd', type=Path, required=True)
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/field-research/gnd-2026-11-03/raw')
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    state = State.load(args.state)
    by_lc, by_wd = gnd_records(args.gnd)
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}

    def ids(v, scheme):
        return {a.split(':', 1)[1] for a in v['anchors'] if a.startswith(scheme + ':')}

    report, queue, found, tried = Counter(), [], {}, set()   # found: key -> (record, route)
    lc_keyed = {k: next(iter(ids(v, 'lcnaf'))) for k, v in live.items() if len(ids(v, 'lcnaf')) == 1}
    names = load_names(args.names, set(lc_keyed.values()) & set(by_lc))[0]
    for k, lc in sorted(lc_keyed.items(), key=lambda kv: int(kv[0][2:])):
        v, recs = live[k], by_lc.get(lc, [])
        if not recs:
            report['lc_no_gnd'] += 1
            continue
        tried.add(k)
        tp = [r for r in recs if r['kind'] == 'DifferentiatedPerson']
        problem = ('several_gnd_records_name_lc' if len(recs) > 1 else 'gnd_record_not_differentiated' if not tp
                   else 'gnd_record_names_several_lc' if len(tp[0]['lc']) > 1 else '')
        r = tp[0] if tp else recs[0]
        auth = names.get(lc, {})
        lc_birth = life(auth, label_dates(auth.get('label', ''))).get('birth', (None,))[0] if auth else None
        if not problem and not name_agrees(v['label'], [as_credit(r['name'])]):
            problem = 'name_disagrees'
        if not problem and off(year(str(lc_birth or '')), {r['birth']} - {None}):
            problem = 'birth_disagrees'
        have = ids(v, 'gnd')
        if not problem and have and r['gnd'] not in have:
            problem = 'key_holds_different_gnd'
        if problem:
            queue.append(dict(kind=f'gnd_{problem}' if not problem.startswith('key_') else problem, key=k,
                              label=v['label'], lc=lc, gnd=[x['gnd'] for x in recs], gnd_name=r['name'],
                              gnd_birth=r['birth'], lc_birth=lc_birth))
            report[problem] += 1
            continue
        found[k] = (r, 'lc')
    for k, v in sorted(live.items(), key=lambda kv: int(kv[0][2:])):
        qs = ids(v, 'wd')
        if k in tried or len(qs) != 1 or ids(v, 'gnd'):
            continue
        recs = [r for r in by_wd.get(next(iter(qs)), []) if r['kind'] == 'DifferentiatedPerson']
        if len(recs) != 1:
            report['wd_no_gnd' if not recs else 'wd_several_gnd'] += 1
            continue
        if not name_agrees(v['label'], [as_credit(recs[0]['name'])]):
            report['wd_route_name_disagrees'] += 1
            queue.append(dict(kind='gnd_name_disagrees', key=k, label=v['label'], qid=next(iter(qs)),
                              gnd=recs[0]['gnd'], gnd_name=recs[0]['name']))
            continue
        found[k] = (recs[0], 'wd')
    # Wikidata items the GND names for LC-route keys
    want = {}
    for k, (r, route) in found.items():
        if route == 'lc' and len(r['wd']) == 1 and len(by_wd[r['wd'][0]]) == 1:
            want[k] = r['wd'][0]
        elif route == 'lc' and r['wd']:
            report['gnd_item_ambiguous'] += 1
    info = items(set(want.values()), args.cache)
    weak = {q for k, q in want.items() if not name_agrees(live[k]['label'], info[q]['labels'])}
    for q, aliases in item_aliases(weak, args.cache).items():
        info[q]['labels'] |= aliases
    suspect = {q for k, q in want.items() if off(found[k][0]['birth'], info[q]['births'])}
    for q, years in precise_births(suspect, args.cache).items():
        info[q]['births'] = years
    clusters = []
    for k, (r, route) in sorted(found.items(), key=lambda kv: int(kv[0][2:])):
        v = live[k]
        anchors, members = {f'gnd:{r["gnd"]}'}, {f'gnd-via:{route}'}
        anchors |= {f'lcnaf:{lc_keyed[k]}'} if route == 'lc' else {f'wd:{q}' for q in ids(v, 'wd')}
        for scheme in ('viaf', 'isni'):
            if len(r[scheme]) == 1:
                a = f'{scheme}:{r[scheme][0]}'
                if state.anchor.get(a, k) != k:
                    report[f'{scheme}_on_other_key'] += 1
                else:
                    anchors.add(a)
        basis = f'GND {r["gnd"]} ({r["name"]}) is sameAs ' + (f'LC {lc_keyed[k]}' if route == 'lc' else
                                                              f'Wikidata {next(iter(ids(v, "wd")))}')
        q = want.get(k)
        if q:
            it, have = info[q], ids(v, 'wd')
            rejected = {m[len('rejected:wd:'):] for m in state.members.get(k, ()) if m.startswith('rejected:wd:')}
            problems = [p for p, bad in (
                ('rejected_before', q in rejected),
                ('not_human', not it['human']),
                ('name_disagrees', not name_agrees(v['label'], it['labels'])),
                ('birth_disagrees', off(r['birth'], it['births'])),
                ('item_cites_other_lc', bool(it['lc'] - {lc_keyed[k]})),
                ('item_cites_other_gnd', bool(it['gnd'] - {r['gnd']} - set(r['alt']))),
                ('key_holds_different_qid', bool(have - {q}))) if bad]
            if have == {q}:
                report['same_qid_already'] += 1
            elif problems:
                report['item_check_failed'] += 1
                queue.append(dict(kind='key_holds_different_qid' if 'key_holds_different_qid' in problems else 'gnd_item_check_failed',
                                  key=k, label=v['label'], lc=lc_keyed[k], gnd=r['gnd'], qid=q, key_qids=sorted(have),
                                  item_labels=sorted(it['labels']), problems=problems))
            else:
                anchors.add(f'wd:{q}')
                members.add('wd-via:gnd')
                basis += f' and Wikidata {q}'
                report['qid_attach' if f'wd:{q}' not in state.anchor else 'qid_on_other_key'] += 1
        new = anchors - v['anchors']
        if not new:
            report['nothing_new'] += 1
            continue
        report[f'{route}_route_attach'] += 1
        clusters.append(dict(type='person', label=v['label'], anchors=anchors, members=members, aliases=set(),
                             resolution='established', basis=basis + '; name and birth year agree'))
    # Clusters sharing a GND id or QID are one person seen through two keys (an LC key and a Wikidata key that
    # GND ties together: Brian Cowan, Christabelle Sethna): one cluster, merged by the rule or held. A VIAF or
    # ISNI id two otherwise separate clusters share is left off both (VIAF clusters conflate namesakes).
    parent = list(range(len(clusters)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first = {}
    for i, c in enumerate(clusters):
        for a in sorted(c['anchors']):
            if a.split(':', 1)[0] in ('gnd', 'wd'):
                if a in first:
                    parent[find(i)] = find(first[a])
                else:
                    first[a] = i
    groups = defaultdict(list)
    for i in range(len(clusters)):
        groups[find(i)].append(clusters[i])
    merged = []
    for cs in groups.values():
        c = dict(cs[0], anchors=set().union(*(x['anchors'] for x in cs)), members=set().union(*(x['members'] for x in cs)))
        if len(cs) > 1:
            c['basis'] = ' / '.join(sorted({x['basis'] for x in cs}))
            report['clusters_joined_by_gnd_or_qid'] += len(cs)
        merged.append(c)
    clusters = merged
    owners = defaultdict(list)
    for i, c in enumerate(clusters):
        for a in c['anchors']:
            if a.split(':', 1)[0] in ('viaf', 'isni'):
                owners[a].append(i)
    for a, cs in owners.items():
        if len(cs) > 1:
            queue.append(dict(kind='viaf_or_isni_on_several_individuals', anchor=a, labels=[clusters[i]['label'] for i in cs]))
            report['viaf_isni_left_off'] += 1
            for i in cs:
                clusters[i]['anchors'].discard(a)
    for c in clusters:
        if len({a for a in c['anchors'] if a.startswith('gnd:')}) > 1 or len({a for a in c['anchors'] if a.startswith('wd:')}) > 1:
            queue.append(dict(kind='gnd_cluster_holds_several_ids', label=c['label'], anchors=sorted(c['anchors'])))
            report['cluster_several_ids'] += 1
            c['skip'] = True
    clusters = [c for c in clusters if not c.get('skip')]
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    materialise(state, dict(basis='GND', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="The GND's sameAs links (DNB CC0 person dump, 2026-03-02): GND, VIAF, ISNI and Wikidata ids for keys "
              'through their LC authority or Wikidata item, names and birth years checked', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(keys_with_one_lc=len(lc_keyed), **dict(sorted(report.items())),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held),
                   review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
