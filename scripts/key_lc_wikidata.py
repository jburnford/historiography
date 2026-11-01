"""Wikidata items for keys through their LC authority (PID-PLAN.md section 5; 2026-11-01). Writes a proposal; never mints.

A person key's `lcnaf:` anchor was chosen through the person's works (the LC atlas and canon routes). Wikidata
items cite LC authorities in P244, so an item whose P244 is that authority describes the same person. That
is Wikidata's claim, and P244 can name a namesake's authority (Marion Kaplan), so it is checked:
- exactly one live item gives the authority in P244, and it is a human (P31 Q5);
- the item's English or default (`mul`) label is name-compatible with the key's label (family name and first initial);
- the LC and Wikidata birth years do not disagree by more than one year (both present).
LC's own Wikidata link (the authority's `external` closeMatch) is recorded beside it; when LC links a
different item, the key is queued, not attached.

Outcomes:
- the key has no QID: `wd:<QID>` is attached (member `wd-via:lc-p244`);
- the QID already anchors another key: the two keys are one person seen twice. plan() merges them when the
  labels agree in full (key_registry.same_name) and their LC authorities do not differ; otherwise held;
- the key already holds a different QID: queued (one of the two is wrong).

    python3 scripts/key_lc_wikidata.py --names /mnt/e/lc-authorities/personal-names.parquet \\
        --out data/identifiers/lc-wikidata-2026-11-01
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, State, materialise, plan
from identity_routes import compatible
from key_registry import same_name
from lc_canon_people import as_credit
from lc_resolve_authorities import label_dates, life, load_names
from merge_guard import guarded
from review_atlas_qids import sparql

ROOT = Path(__file__).resolve().parents[1]


def items_for(lcids, cache):
    """LC id -> {QID: dict(labels, births, human)} for live items whose P244 is that id."""
    out = defaultdict(dict)
    lcids = sorted(lcids)
    for i in range(0, len(lcids), 200):
        part = lcids[i:i + 200]
        query = """SELECT ?lc ?item ?label ?birth ?human WHERE {
                VALUES ?lc { %s } ?item wdt:P244 ?lc .
                OPTIONAL { ?item rdfs:label ?label FILTER(lang(?label) IN ('en', 'mul')) }
                OPTIONAL { ?item wdt:P569 ?birth }
                BIND(EXISTS { ?item wdt:P31 wd:Q5 } AS ?human) }""" % ' '.join(f'"{x}"' for x in part)
        # cached by the query text, so a changed query is asked again
        rows = sparql(query, cache, 'lc-p244-' + hashlib.sha1(query.encode()).hexdigest()[:12])
        for r in rows:
            q = r['item']['value'].rsplit('/', 1)[-1]
            it = out[r['lc']['value']].setdefault(q, dict(labels=set(), births=set(), human=False))
            if 'label' in r:
                it['labels'].add(r['label']['value'])
            if 'birth' in r and r['birth']['value'][:5].lstrip('-')[:4].isdigit():
                it['births'].add(int(r['birth']['value'].lstrip('-')[:4]))
            it['human'] = it['human'] or r.get('human', {}).get('value') == 'true'
    return out


def name_agrees(key_label, item_labels):
    family, comma, given = key_label.partition(', ')
    if not comma:
        parts = key_label.split()
        family, given = (parts[-1], ' '.join(parts[:-1])) if len(parts) > 1 else (key_label, '')
    return any(compatible(l, given, family) or compatible(l, given.split()[0] if given else '', family.split()[-1])
               for l in item_labels if given)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/field-research/lc-authorities-2026-10-30/lc-wikidata/raw')
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    state = State.load(args.state)
    keyed = {}
    for k, v in state.keys.items():
        if v['type'] == 'person' and v['status'] in ('active', 'provisional'):
            lcs = [a[6:] for a in v['anchors'] if a.startswith('lcnaf:')]
            if len(lcs) == 1:
                keyed[k] = lcs[0]
    names = load_names(args.names, set(keyed.values()))[0]
    found = items_for(set(keyed.values()), args.cache)
    report, queue, clusters = Counter(), [], []
    for k, lc in sorted(keyed.items(), key=lambda kv: int(kv[0][2:])):
        rec = state.keys[k]
        have = {a[3:] for a in rec['anchors'] if a.startswith('wd:')}
        items = {q: it for q, it in found.get(lc, {}).items()}
        auth = names.get(lc, {})
        lc_link = {e.rsplit('/', 1)[-1] for e in auth.get('external') or [] if 'wikidata.org' in e}
        if not items:
            report['no_item_cites_lc' if not have else 'has_qid_no_item_cites_lc'] += 1
            continue
        if len(items) > 1:
            queue.append(dict(kind='several_items_cite_lc', key=k, label=rec['label'], lc=lc, qids=sorted(items)))
            report['several_items'] += 1
            continue
        q, it = next(iter(items.items()))
        if have:
            report['same_qid_already' if q in have else 'different_qid_on_key'] += 1
            if q not in have:
                queue.append(dict(kind='key_holds_different_qid', key=k, label=rec['label'], lc=lc, qid=q, key_qids=sorted(have)))
            continue
        lc_birth = life(auth, label_dates(auth.get('label', ''))).get('birth', (None,))[0] if auth else None
        problems = []
        if not it['human']:
            problems.append('not_human')
        if not name_agrees(rec['label'], it['labels']):
            problems.append('name_disagrees')
        if lc_birth and it['births'] and all(abs(int(lc_birth) - b) > 1 for b in it['births']):
            problems.append('birth_disagrees')
        if lc_link and q not in lc_link:
            problems.append('lc_links_other_item')
        if problems:
            queue.append(dict(kind='check_failed', key=k, label=rec['label'], lc=lc, qid=q, item_labels=sorted(it['labels']),
                              item_births=sorted(it['births']), lc_birth=lc_birth, problems=problems))
            report['check_failed'] += 1
            continue
        report['attach' if f'wd:{q}' not in state.anchor else 'qid_on_other_key'] += 1
        if lc_link:
            report['lc_also_links_it'] += 1
        clusters.append(dict(type='person', label=rec['label'], anchors={f'lcnaf:{lc}', f'wd:{q}'},
                             members={'wd-via:lc-p244'}, aliases=set(), resolution='established',
                             basis=f'Wikidata {q} cites LC {lc} (P244); name and birth year agree'))
    # One item citing two LC authorities held by two keys (LC holds duplicate records, or one is a namesake's):
    # neither key takes the QID; queued.
    by_qid = defaultdict(list)
    for c in clusters:
        by_qid[next(a for a in c['anchors'] if a.startswith('wd:'))].append(c)
    for q, cs in by_qid.items():
        if len(cs) > 1:
            queue.append(dict(kind='item_cites_several_lc_keys', qid=q[3:], labels=[c['label'] for c in cs],
                              lc=sorted(a for c in cs for a in c['anchors'] if a.startswith('lcnaf:'))))
            report['item_cites_several_lc_keys'] += 1
    clusters = [c for cs in by_qid.values() if len(cs) == 1 for c in cs]

    def merge_ok(cluster, keys):
        """The LC authority's key and the QID's key: two independent identifications (LC through the works,
        the QID through its own route) that Wikidata ties together. One person when the labels are compatible
        (family name and first initial: 'Maitland, Frederic William' / 'Maitland, F. W.') and their LC
        authorities do not differ (the QID's key has none, or the same one)."""
        if len(keys) != 2:
            return False
        a, b = (state.keys[k]['label'] for k in keys)
        if not (same_name(a, b) or (name_agrees(a, [as_credit(b)]) and name_agrees(b, [as_credit(a)]))):
            return False
        lcs = set().union(*({a for a in state.keys[k]['anchors'] if a.startswith('lcnaf:')} for k in keys))
        return len(lcs) <= 1
    ops, assign, held = plan(state, clusters, guarded(state, merge_ok))
    materialise(state, dict(basis='LC to Wikidata', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='Wikidata items citing the key\'s LC authority (P244), name and birth year checked', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(keys_with_one_lc=len(keyed), **dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
