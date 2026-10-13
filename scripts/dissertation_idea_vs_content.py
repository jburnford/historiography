#!/usr/bin/env python3
"""Who is cited for content, and who for frameworks? Readership dispersion across fields.

A scholar cited for content is read by dissertations on their own subject, so their readers
concentrate in one co-citation field. A scholar cited for a framework or big idea is read by
dissertations on unrelated subjects, so their readers spread across fields.

For each person cited by at least --min strict History PhDs (2009-2026), each citing
dissertation is assigned a home field: the co-citation field (summary/views.json) holding most
of the works it cites, excluding the person's own works so they cannot pull the dissertation
into their field. The script reports:
- top-field share and its lift over the field's base rate among all fielded dissertations;
- dispersion, the normalised entropy of home fields (0 = one field, 1 = even over all);
- fields reached, those holding at least 10% of the person's fielded readers.

Readership is the evidence: the method does not read the works. Namesakes share a person key
unless the scholars packet separated them. Writes summary/idea-vs-content.csv and .json in
the dissertation-citations output directory.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--min', type=int, default=40)
    args = ap.parse_args()
    g = json.loads((OUT / 'graph.json').read_text())
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis') and n['year'] and 2009 <= n['year'] <= 2026}
    cites, works_of, citing_of = defaultdict(set), defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            cites[e['source']].add(e['target'])
            citing_of[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'])
    views = json.loads((OUT / 'summary/views.json').read_text())['fields']
    field_of = {n['id']: n['field'] for n in views['nodes'] if n.get('field') is not None}
    labels = {f['id']: f['label'] for f in views['fields']}
    F = sorted(labels)

    def home(d, exclude):
        c = Counter(field_of[w] for w in cites[d] - exclude if w in field_of)
        if not c:
            return None
        (top, k), *rest = c.most_common(2) + [(None, 0)]
        return top if k > rest[0][1] else None  # ties stay unfielded

    base = Counter(h for d in diss if (h := home(d, set())) is not None)
    base_n = sum(base.values())
    rows = []
    for pid, ws in works_of.items():
        readers = set().union(*(citing_of[w] for w in ws)) if ws else set()
        if len(readers) < args.min:
            continue
        homes = Counter(h for d in readers if (h := home(d, ws)) is not None)
        n = sum(homes.values())
        if not n:
            continue
        top, k = homes.most_common(1)[0]
        share = k / n
        ent = -sum((c / n) * math.log(c / n) for c in homes.values()) / math.log(len(F))
        rows.append(dict(person=pid, name=nodes[pid].get('name') or pid, citing_phds=len(readers), fielded=n,
                         top_field=labels[top], top_share=round(share, 3), top_lift=round(share / (base[top] / base_n), 2),
                         dispersion=round(ent, 3), fields_reached=sum(c / n >= 0.10 for c in homes.values())))
    rows.sort(key=lambda r: -r['dispersion'])
    with (OUT / 'summary/idea-vs-content.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (OUT / 'summary/idea-vs-content.json').write_text(json.dumps(dict(
        method=__doc__.strip().splitlines()[0], min_citing=args.min, fields=labels,
        base_home_fields={labels[k]: v for k, v in base.items()}, people=rows), indent=1, ensure_ascii=False))
    print(f'{len(rows)} people with >= {args.min} citing PhDs; fields: {len(F)}')


if __name__ == '__main__':
    main()
