"""Read back a Wikidata pilot batch after the user has run it in QuickStatements, and write a key-log proposal.

For every CREATE block of the batch file: find the new item by its LC id (P244) on the Wikidata Query Service, read
the item (Special:EntityData), and check that the label, description and every statement of the block landed (value,
qualifiers, and at least one reference). Items found once and complete are proposed as `wd:` attaches to the key
(member `wd-via:published-from-key-log`, as the 2026-11-02 batches). Missing items, items found twice (a batch run
twice) and incomplete items are listed and not proposed. The proposal is validated in memory (dry run) and NOT applied.

    python3 scripts/wikidata_pilot_readback.py data/identifiers/wikidata-pilot-2026-11-14/pilot-batch-01.qs
    # optional: --qids extra.csv (lc,qid) when the query service lags behind a fresh run
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/identifiers/wikidata-pilot-2026-11-14'
WDQS = 'https://query.wikidata.org/sparql'
UA = 'kg-research-client/0.1'


def get_json(url, accept='application/json', data=None):
    for t in range(5):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Accept': accept})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 — network: back off, retry, then give up loudly
            print('retry', t, url[:80], e, file=sys.stderr)
            time.sleep(10 * (t + 1))
    raise SystemExit(f'failed: {url[:120]}')


def parse_batch(path):
    blocks, cur = [], None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if line == 'CREATE':
            cur = dict(label=None, desc=None, aliases=[], stmts=[])
            blocks.append(cur)
            continue
        f = line.split('|')
        if f[1] == 'Len':
            cur['label'] = f[2].strip('"')
        elif f[1] == 'Den':
            cur['desc'] = f[2].strip('"')
        elif f[1] == 'Aen':
            cur['aliases'].append(f[2].strip('"'))
        else:
            prop, value, rest = f[1], f[2], f[3:]
            quals = {}
            i = 0
            while i + 1 < len(rest) and rest[i].startswith('P'):
                quals[rest[i]] = rest[i + 1]
                i += 2
            cur['stmts'].append((prop, value, quals))
            if prop == 'P244':
                cur['lc'] = value.strip('"')
    return blocks


def norm(v):
    """QuickStatements value -> comparable string (item id, plain string, or year for a time)."""
    v = v.strip('"')
    m = re.match(r'^\+(\d{4})-', v)
    return m.group(1) if m else v


def snak_value(snak):
    dv = (snak.get('datavalue') or {}).get('value')
    if isinstance(dv, dict):
        if 'id' in dv:
            return dv['id']
        if 'time' in dv:
            return dv['time'][1:5]
    return dv


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('batch', type=Path)
    ap.add_argument('--qids', type=Path, help='csv lc,qid for items the query service does not show yet')
    args = ap.parse_args()
    blocks = parse_batch(args.batch)
    keys = {r['lcnaf']: r for r in csv.DictReader(open(OUT / 'pilot-500.csv', encoding='utf-8'))}
    lcs = [b['lc'] for b in blocks]
    found = {lc: set() for lc in lcs}
    for i in range(0, len(lcs), 100):
        q = 'SELECT ?i ?lc WHERE { VALUES ?lc {%s} ?i <http://www.wikidata.org/prop/direct/P244> ?lc }' % ' '.join(f'"{x}"' for x in lcs[i:i + 100])
        d = get_json(WDQS, 'application/sparql-results+json', urllib.parse.urlencode({'query': q}).encode())
        for b in d['results']['bindings']:
            found[b['lc']['value']].add(b['i']['value'].rsplit('/', 1)[1])
        time.sleep(1)
    if args.qids:
        for r in csv.reader(open(args.qids)):
            if r and r[0] in found:
                found[r[0]].add(r[1])
    rows, ops = [], []
    stem = args.batch.stem
    for b in blocks:
        k = keys.get(b['lc'], {})
        qs = sorted(found[b['lc']])
        row = dict(key=k.get('key', ''), label=b['label'], lcnaf=b['lc'], qid=' '.join(qs), status='', missing='')
        if not qs:
            row['status'] = 'not found'
        elif len(qs) > 1:
            row['status'] = 'several items (merge on Wikidata first)'
        else:
            q = qs[0]
            ent = next(iter(get_json(f'https://www.wikidata.org/wiki/Special:EntityData/{q}.json')['entities'].values()))
            time.sleep(0.5)
            miss = []
            if (ent.get('labels', {}).get('en') or {}).get('value') != b['label']:
                miss.append('label')
            if b['desc'] and (ent.get('descriptions', {}).get('en') or {}).get('value') != b['desc']:
                miss.append('description')
            claims = ent.get('claims', {})
            for prop, value, quals in b['stmts']:
                ok = False
                for c in claims.get(prop, []):
                    if str(snak_value(c['mainsnak'])) != norm(value):
                        continue
                    qok = all(any(str(snak_value(s)) == norm(v) for s in c.get('qualifiers', {}).get(p, [])) for p, v in quals.items()
                              if p.startswith('P'))
                    if qok and c.get('references'):
                        ok = True
                        break
                if not ok:
                    miss.append(f'{prop}={norm(value)}')
            row['missing'] = '; '.join(miss)
            row['status'] = 'complete' if not miss else 'incomplete'
            if not miss and k.get('key'):
                ops.append(dict(event='attach', key=k['key'], anchors=[f'wd:{q}'], aliases=[],
                                members=['wd-via:published-from-key-log'],
                                basis=f"Wikidata {q} created from this key's facts by the user's QuickStatements batch "
                                      f"wikidata-pilot-2026-11-14/{args.batch.name}; read back {time.strftime('%Y-%m-%d')}, "
                                      f"every statement present"))
        rows.append(row)
    with open(OUT / f'{stem}.readback.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    proposal = dict(basis=f'Wikidata items published from the key log (wikidata-pilot-2026-11-14/{args.batch.name}), read back',
                    decided_by='review', ops=ops)
    (OUT / f'{stem}.readback-proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    sys.path.insert(0, str(ROOT / 'scripts'))
    import identifiers as I
    import keylog_snapshot as KS
    I.State.load = lambda *a, **kw: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    events, _ = I.materialise(KS.read_state(), proposal, 'dry-run', 'dry-run', inplace=True)
    from collections import Counter
    print(dict(Counter(r['status'] for r in rows)), '| proposal ops', len(ops), '| dry-run events', len(events),
          '| NOT applied:', OUT / f'{stem}.readback-proposal.json')


if __name__ == '__main__':
    main()
