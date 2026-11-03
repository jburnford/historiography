"""Wikidata items for keys through their LC authority (PID-PLAN.md section 5; 2026-11-01). Writes a proposal; never mints.

A person key's `lcnaf:` anchor was chosen through the person's works (the LC atlas and canon routes). Wikidata
items cite LC authorities in P244, so an item whose P244 is that authority describes the same person. That
is Wikidata's claim, and P244 can name a namesake's authority (Marion Kaplan), so it is checked:
- exactly one live item gives the authority in P244, and it is a human (P31 Q5);
- the item's English or default (`mul`) label is name-compatible with the key's label (family name and first initial);
- the LC and Wikidata birth years do not disagree by more than two years (both present; early dates are
  often approximate: Langland 1330 / 1332).
LC's own Wikidata link (the authority's `external` closeMatch) is recorded beside it; when LC links a
different item, the key is queued, not attached.

Outcomes:
- the key has no QID: `wd:<QID>` is attached (member `wd-via:lc-p244`);
- the QID already anchors another key: the two keys are one person seen twice. plan() merges them when the
  labels agree in full (key_registry.same_name) and their LC authorities do not differ; otherwise held;
- the key already holds a different QID: queued (one of the two is wrong), unless the two items are one
  person's duplicates in Wikidata (2026-11-01, Erika Dyck): the key's item carries the key's ORCID and no
  LC authority, the other carries the key's LC authority and no other ORCID, and the usual checks pass.
  Then `wd:<QID>` is attached beside it with the member `wd-duplicate:<stub QID>`, and the pair is listed
  in wikidata-duplicates.json (a merge to propose on Wikidata later).

    python3 scripts/key_lc_wikidata.py --names /mnt/e/lc-authorities/personal-names.parquet \\
        --out data/identifiers/lc-wikidata-2026-11-01
"""
import argparse
import hashlib
import json
import re
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


QUERY_VERSION = 'p244-v1'      # bump when the item query below changes; the per-id cache is then rebuilt


def items_for(lcids, cache):
    """LC id -> {QID: dict(labels, births, human)} for live items whose P244 is that id. Results are cached per
    LC id (`p244-by-lc.json`), so a run asks only for ids it has not seen: caching whole batches by query text
    re-asked every batch whenever the set of ids changed (2026-11-01: 1,375 new ids re-ran all ~290 batches)."""
    store = cache / f'{QUERY_VERSION}-by-lc.json'
    known = json.loads(store.read_text()) if store.exists() else {}
    todo = sorted(set(lcids) - set(known))
    for i in range(0, len(todo), 200):
        part = todo[i:i + 200]
        query = """SELECT ?lc ?item ?label ?birth ?human WHERE {
                VALUES ?lc { %s } ?item wdt:P244 ?lc .
                OPTIONAL { ?item rdfs:label ?label FILTER(lang(?label) IN ('en', 'mul')) }
                OPTIONAL { ?item wdt:P569 ?birth }
                BIND(EXISTS { ?item wdt:P31 wd:Q5 } AS ?human) }""" % ' '.join(f'"{x}"' for x in part)
        rows = sparql(query, cache, 'lc-p244-' + hashlib.sha1(query.encode()).hexdigest()[:12])
        for x in part:
            known[x] = []
        for r in rows:
            known[r['lc']['value']].append(r)
        if i % 4000 == 0:
            store.write_text(json.dumps(known))
    store.write_text(json.dumps(known))
    out = defaultdict(dict)
    for lc in lcids:
        for r in known.get(lc, ()):
            q = r['item']['value'].rsplit('/', 1)[-1]
            it = out[lc].setdefault(q, dict(labels=set(), births=set(), human=False))
            if 'label' in r:
                it['labels'].add(r['label']['value'])
            if 'birth' in r and r['birth']['value'][:5].lstrip('-')[:4].isdigit():
                it['births'].add(int(r['birth']['value'].lstrip('-')[:4]))
            it['human'] = it['human'] or r.get('human', {}).get('value') == 'true'
    return out


def precise_births(qids, cache):
    """QID -> birth years stated to year precision or finer. Wikidata stores a century or decade as a year
    ('20th century' reads 1901 or 2000 through wdt:P569), which is no evidence against LC's year
    (2026-11-02: Otte 1900, Mehta 1901, Niewyk 2000)."""
    out = {q: set() for q in qids}
    qids = sorted(qids)
    for i in range(0, len(qids), 200):
        part = qids[i:i + 200]
        query = """SELECT ?item ?t WHERE { VALUES ?item { %s } ?item p:P569/psv:P569 ?v .
                ?v wikibase:timeValue ?t ; wikibase:timePrecision ?p FILTER(?p >= 9) }""" % ' '.join(f'wd:{q}' for q in part)
        for r in sparql(query, cache, 'births-' + hashlib.sha1(query.encode()).hexdigest()[:12]):
            if r['t']['value'].lstrip('-')[:4].isdigit():
                out[r['item']['value'].rsplit('/', 1)[-1]].add(int(r['t']['value'].lstrip('-')[:4]))
    return out


def item_ids(qids, cache):
    """QID -> dict(orcid=set, lc=set) for the given items."""
    out = {q: dict(orcid=set(), lc=set()) for q in qids}
    qids = sorted(qids)
    for i in range(0, len(qids), 200):
        part = qids[i:i + 200]
        query = """SELECT ?item ?orcid ?lc WHERE { VALUES ?item { %s }
                OPTIONAL { ?item wdt:P496 ?orcid } OPTIONAL { ?item wdt:P244 ?lc } }""" % ' '.join(f'wd:{q}' for q in part)
        for r in sparql(query, cache, 'item-ids-' + hashlib.sha1(query.encode()).hexdigest()[:12]):
            q = r['item']['value'].rsplit('/', 1)[-1]
            if 'orcid' in r:
                out[q]['orcid'].add(r['orcid']['value'])
            if 'lc' in r:
                out[q]['lc'].add(r['lc']['value'])
    return out


HONORIFIC = {'sir', 'dame', 'lord', 'lady', 'mr', 'mrs', 'jr', 'sr', 'st', 'baronet', 'bart', 'rev', 'dr'}


def _words(s):
    from aha_links import fold
    return [w for w in re.findall(r'[a-z]+', fold(s)) if w not in HONORIFIC]


def name_agrees(key_label, item_labels):
    """The key's name and one of the item's labels or aliases agree: identity_routes.compatible (family name
    last, first initial), or, for forms it cannot read, every word of the key's surname among the label's
    words and a spelled-out given name of the key (its fuller form in parentheses included) among them too;
    a key with initials only needs its first initial to open the label's first given name (2026-11-01: 'Ortiz,
    Fernando' / 'Fernando Ortiz Fernández'; 'Highfield, J. R. L. (John Roger Loxdale)' / 'Roger Highfield';
    'Pope, S. W.' is not 'James W Pope')."""
    family, comma, given = key_label.partition(', ')
    if not comma:
        parts = key_label.split()
        family, given = (parts[-1], ' '.join(parts[:-1])) if len(parts) > 1 else (key_label, '')
    if not given:
        return False
    if any(compatible(l, given, family) or compatible(l, given.split()[0], family.split()[-1]) for l in item_labels):
        return True
    fam, giv = set(_words(family)), _words(given)
    full = {g for g in giv if len(g) > 1}
    first = giv[0] if giv else ''
    for l in item_labels:
        lw = _words(l)
        rest = [w for w in lw if w not in fam]
        if fam and fam <= set(lw) and rest:
            if full & set(rest) or (not full and len(first) == 1 and rest[0][0] == first):
                return True
    return False


def item_aliases(qids, cache):
    """QID -> English and default aliases, for items whose labels did not agree."""
    out = defaultdict(set)
    qids = sorted(qids)
    for i in range(0, len(qids), 200):
        part = qids[i:i + 200]
        query = """SELECT ?item ?alias WHERE { VALUES ?item { %s } ?item skos:altLabel ?alias
                FILTER(lang(?alias) IN ('en', 'mul')) }""" % ' '.join(f'wd:{q}' for q in part)
        for r in sparql(query, cache, 'aliases-' + hashlib.sha1(query.encode()).hexdigest()[:12]):
            out[r['item']['value'].rsplit('/', 1)[-1]].add(r['alias']['value'])
    return out


def merge_rule(state):
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
    return merge_ok


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
    # aliases only for the items whose labels do not agree with their key's name
    weak = {q for k, lc in keyed.items() for q, it in found.get(lc, {}).items()
            if len(found[lc]) == 1 and not name_agrees(state.keys[k]['label'], it['labels'])}
    for q, aliases in item_aliases(weak, args.cache).items():
        for items in found.values():
            if q in items:
                items[q]['labels'] |= aliases
    def lc_birth_of(lc):
        auth = names.get(lc, {})
        return life(auth, label_dates(auth.get('label', ''))).get('birth', (None,))[0] if auth else None

    def disagrees(lc_birth, births):
        return bool(lc_birth and births and all(abs(int(lc_birth) - b) > 2 for b in births))

    # a disagreeing birth year is re-read at its stated precision; centuries and decades drop out
    suspect = {q for lc in set(keyed.values()) for q, it in found.get(lc, {}).items() if disagrees(lc_birth_of(lc), it['births'])}
    for q, years in precise_births(suspect, args.cache).items():
        for items in found.values():
            if q in items:
                items[q]['births'] = years
    report, queue, clusters, pending, duplicates = Counter(), [], [], [], []
    for k, lc in sorted(keyed.items(), key=lambda kv: int(kv[0][2:])):
        rec = state.keys[k]
        have = {a[3:] for a in rec['anchors'] if a.startswith('wd:')}
        rejected = {m[len('rejected:wd:'):] for m in state.members.get(k, ()) if m.startswith('rejected:wd:')}
        items = {q: it for q, it in found.get(lc, {}).items() if q not in rejected}
        report['rejected_item_skipped'] += len(found.get(lc, {})) - len(items)
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
        if have and q in have:
            report['same_qid_already'] += 1
            continue
        if have:
            pending.append((k, lc, q, it, have))
            continue
        lc_birth = lc_birth_of(lc)
        problems = []
        if not it['human']:
            problems.append('not_human')
        if not name_agrees(rec['label'], it['labels']):
            problems.append('name_disagrees')
        if disagrees(lc_birth, it['births']):
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
    ids = item_ids({q for _, _, q, _, have in pending} | {x for _, _, _, _, have in pending for x in have}, args.cache)
    for k, lc, q, it, have in pending:
        rec = state.keys[k]
        orcids = {a[6:] for a in rec['anchors'] if a.startswith('orcid:')}
        stubs = [h for h in have if ids[h]['orcid'] & orcids and not ids[h]['lc']]
        auth = names.get(lc, {})
        lc_birth = lc_birth_of(lc)
        ok = (len(stubs) == len(have) and ids[q]['lc'] == {lc} and not (ids[q]['orcid'] - orcids) and it['human']
              and name_agrees(rec['label'], it['labels'])
              and not disagrees(lc_birth, it['births']))
        if not ok:
            report['different_qid_on_key'] += 1
            queue.append(dict(kind='key_holds_different_qid', key=k, label=rec['label'], lc=lc, qid=q, key_qids=sorted(have)))
            continue
        report['wikidata_duplicate_items'] += 1
        duplicates.append(dict(key=k, label=rec['label'], orcid_stub=sorted(have), lc_item=q, lc=lc, orcid=sorted(orcids)))
        clusters.append(dict(type='person', label=rec['label'], anchors={f'lcnaf:{lc}', f'wd:{q}'},
                             members={'wd-via:lc-p244'} | {f'wd-duplicate:{h}' for h in have}, aliases=set(),
                             resolution='established',
                             basis=f'Wikidata {q} cites LC {lc} (P244); the key\'s item {", ".join(sorted(have))} carries its ORCID and '
                                   f'no LC authority: duplicate items of one person'))
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

    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    materialise(state, dict(basis='LC to Wikidata', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='Wikidata items citing the key\'s LC authority (P244), name and birth year checked', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(keys_with_one_lc=len(keyed), **dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'wikidata-duplicates.json').write_text(json.dumps(duplicates, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
