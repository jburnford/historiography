"""LC authorities for ORCID keys through the books their own ORCID records claim (2026-11-01). Writes a proposal.

A person's ORCID record lists their works; a book carries an ISBN. LC's catalogue (MDSConnect Books All 2016,
offline index from scripts/lc_bib_index.py) holds the record for that ISBN and names its people with
authority headings. Identity by works on the person's own claim:
- the key has an ORCID anchor and no LC authority; its cached ORCID record (data/orcid-2026-09-21/records)
  lists works with ISBNs;
- an LC record carries one of those ISBNs, and exactly one of its personal-name headings (100/700) is
  compatible with the key's name (identity_routes.compatible and lc_canon_people.given_agrees; a joint book
  takes the closest name);
- the heading resolves to a live, differentiated authority (lc_resolve_authorities.resolve, no variant forms);
- every book that resolves names the same authority (otherwise queued: two LC people of that name).
The authority must not already anchor another key whose name disagrees, nor have been rejected on this key.

    python3 scripts/key_orcid_lc.py --index /mnt/e/lc-bib-2016/index --names /mnt/e/lc-authorities/personal-names.parquet \\
        --out data/identifiers/orcid-lc-2026-11-01
"""
import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from identity_routes import compatible, isbn13
from key_lc_books import label_of, merge_rule
from key_registry import names_compatible
from lc_canon_people import as_credit, closest_names, given_agrees
from lc_resolve_authorities import load_names, resolve
from merge_guard import guarded

RECORDS = ROOT / 'data/orcid-2026-09-21/records'


def orcid_isbns(orcid):
    path = RECORDS / f'{orcid}.json'
    if not path.exists():
        return set()
    r = json.loads(path.read_text())
    out = set()
    for g in ((r.get('activities-summary') or {}).get('works') or {}).get('group', []):
        for e in (g.get('external-ids') or {}).get('external-id', []):
            if e.get('external-id-type') == 'isbn' and (i := isbn13(e.get('external-id-value') or '')):
                out.add(i)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    lc_keys = {k for a, k in state.anchor.items() if a.startswith('lcnaf:')}
    keys = defaultdict(set)                          # isbn -> keys claiming it
    for a, k in state.anchor.items():
        if a.startswith('orcid:') and k not in lc_keys and state.keys[k]['type'] == 'person':
            for i in orcid_isbns(a[6:]):
                keys[i].add(k)
    report = Counter(isbns_claimed=len(keys), keys_with_isbns=len({k for ks in keys.values() for k in ks}))
    db = duckdb.connect()
    db.execute('SET memory_limit = "6GB"')
    db.execute('CREATE TABLE want(isbn VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(i,) for i in keys])
    rows = db.execute(f"""
        WITH r AS (SELECT control, unnest(isbns) AS isbn FROM read_parquet('{args.index}/records-*.parquet'))
        SELECT r.isbn, h.control, h.heading, h.family, h.given, h.fuller, h.uri
        FROM r JOIN want USING (isbn) JOIN read_parquet('{args.index}/headings-*.parquet') h USING (control)
        WHERE h.tag IN ('100', '700')""").fetchall()
    heads = defaultdict(list)                        # (isbn, control) -> headings
    for isbn, control, heading, family, given, fuller, uri in rows:
        heads[isbn, control].append(dict(heading=heading, family=family or '', given=given or '', fuller=fuller or '', uri=uri or ''))
    report['lc_records_found'] = len(heads)
    found = defaultdict(lambda: defaultdict(set))    # key -> heading -> isbns
    for (isbn, control), hs in heads.items():
        for k in keys[isbn]:
            label = state.keys[k]['label']
            fam, comma, giv = label.partition(', ')
            if not comma:
                t = label.split()
                fam, giv = (t[-1], ' '.join(t[:-1])) if len(t) > 1 else (label, '')
            person = as_credit(label)
            match = [(h, [h['given']] + ([h['fuller']] if h['fuller'] else [])) for h in hs
                     if (compatible(person, h['given'], h['family']) and given_agrees(giv, h['given']))
                     or (h['fuller'] and compatible(person, h['fuller'], h['family']) and given_agrees(giv, h['fuller']))]
            match = closest_names(giv, match)
            if len(match) == 1:
                found[k][(match[0][0]['heading'], match[0][0]['uri'])].add(isbn)
    names = load_names(args.names, {u.rstrip('/').split('/')[-1] for hs in found.values() for _, u in hs if u} |
                       _family_lcids(args.names, {h for hs in found.values() for h, _ in hs}))
    by_id = names[0]
    rejected = {(m.split(':', 1)[1], k) for k, ms in state.members.items() for m in ms if m.startswith('lcnaf-rejected:')}
    clusters, queue, by_lc = [], [], defaultdict(list)
    for k, hs in sorted(found.items()):
        lcs = {}
        for (heading, uri), isbns in hs.items():
            lcid, via = resolve(dict(heading=heading, uri=uri), names)
            if lcid and via != 'variant' and not by_id[lcid].get('undifferentiated'):
                lcs.setdefault(lcid, set()).update(isbns)
        if len(lcs) != 1:
            report['several_lcnaf' if lcs else 'heading_not_resolved'] += 1
            if lcs:
                queue.append(dict(kind='orcid_books_several_lcnaf', key=k, label=state.keys[k]['label'], lcnaf=sorted(lcs)))
            continue
        lc, isbns = next(iter(lcs.items()))
        owner = state.anchor.get(f'lcnaf:{lc}')
        label = label_of(by_id[lc]['label'])
        if (lc, k) in rejected or (owner and not names_compatible(label, state.keys[owner]['label'])):
            queue.append(dict(kind='orcid_lcnaf_conflict', key=k, label=state.keys[k]['label'], lcnaf=lc, owner=owner))
            report['conflict'] += 1
            continue
        by_lc[lc].append(k)
        clusters.append(dict(type='person', label=state.keys[k]['label'],
                             anchors={f'lcnaf:{lc}'} | {a for a in state.keys[k]['anchors'] if a.startswith('orcid:')},
                             members=set(), aliases=set(), resolution='established',
                             basis=f'books the ORCID record claims ({", ".join(sorted(isbns)[:3])}) are catalogued by LC under {lc}'))
        report['joined_existing_lc_key' if owner else 'lcnaf_new_to_log'] += 1
    for lc, ks in by_lc.items():
        if len(ks) > 1:
            queue.append(dict(kind='lcnaf_from_several_orcid_keys', lcnaf=lc, keys=ks))
            clusters = [c for c in clusters if f'lcnaf:{lc}' not in c['anchors']]
            report['lcnaf_from_several_orcid_keys'] += 1
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    materialise(state, dict(basis='orcid lc', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="books claimed in the person's ORCID record, catalogued by LC (MDSConnect Books All 2016)", decided_by='build',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(**dict(sorted(report.items())), clusters=len(clusters), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=len(queue) + len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


def _family_lcids(path, headings):
    """LC ids whose authorised label has the family name of one of these headings."""
    db = duckdb.connect()
    db.execute('CREATE TABLE fam(f VARCHAR)')
    db.executemany('INSERT INTO fam VALUES (?)', [(f,) for f in {h.partition(',')[0] for h in headings}])
    return {r[0] for r in db.execute(f"SELECT lcid FROM read_parquet('{path}') WHERE split_part(label, ',', 1) IN (SELECT f FROM fam)").fetchall()}


if __name__ == '__main__':
    main()
