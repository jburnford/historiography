"""Ground the institutions printed in JSTOR review signatures to ROR (2026-11-06), reusing scripts/ground_institutions.py.

Input: /mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz (jstor_review_signatures.py). Strings
printed at least --min times (2: 9,434 strings, 84% of signed institutions). Before matching: role words dropped
('emeritus', 'Assistant Professor, ...'), all-capitals strings put in title case. Countries are open. Forms,
ROR's affiliation matcher, the shared API cache and the acceptance rule are those of ground_institutions.py:
accepted when ROR marks the match `chosen` or its score is >= 0.9 and 0.05 ahead of the next, and every distinctive
word of the string is in the ROR record's names or city; otherwise review.

Output: OUT/signature-institutions.csv (string, rows, ror, ror_name, ror_country, wikidata, score, decision, basis)
and OUT/summary.json. Read-only candidates for the KG session (institution keys i-* carry ROR anchors).

    python3 jstor_ground_signature_institutions.py --out data/field-research/jstor-fulltext-2026-11-06/signature-institutions
"""
import argparse, csv, gzip, json, re, sys, urllib.parse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import ground_institutions as G  # noqa: E402

SIG = '/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz'
ROR = Path('/mnt/e/ror/v2.15-2026-10-20/v2.15-2026-10-20-ror-data.csv')
CACHE = Path('/mnt/e/ror/api-cache')
_FIELD = r"(?:\s+(?:of|in)\s+(?:the\s+)?[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?)?"
ROLE = re.compile(rf"^(?:(?:emerit\w*|retired|(?:assistant|associate|visiting|adjunct|full|distinguished|research)?\s*professor(?:\s+emerit\w*)?{_FIELD}|"
                  rf"(?:senior\s+)?lecturer{_FIELD}|reader{_FIELD}|(?:research\s+|senior\s+)?fellow(?=\s*,)|director(?=\s*,)|"
                  rf"graduate student{_FIELD}|ph\.?\s?d\.? candidate{_FIELD})[\s,]+)+", re.I)


def clean(s):
    s = ROLE.sub('', s.strip())
    if s.isupper():
        s = s.title().replace(' Of ', ' of ').replace(' And ', ' and ').replace(' The ', ' the ').replace(' At ', ' at ')
    return s.strip(' ,;.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min', type=int, default=2)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    for line in gzip.open(SIG, 'rt', encoding='utf-8'):
        r = json.loads(line)
        if r.get('institution'):
            counts[r['institution']] += 1
    ror = G.load_ror(ROR)
    state, out, stats = {'last': 0.0}, [], Counter()
    todo = [(s, n) for s, n in counts.most_common() if n >= args.min]
    for i, (raw, n) in enumerate(todo, 1):
        name = clean(raw)
        forms = [name] + [f for f in G.segments(name) if f != name]
        forms += [x for x in (G.expand(f) for f in list(forms)) if x not in forms]
        best = {}
        for form in forms[:4]:
            body = G.fetch(CACHE, G.API + urllib.parse.quote(form), state)
            for it in (body or {}).get('items', []):
                org = it['organization']['id']
                if org not in best or (it['chosen'], it['score']) > (best[org]['chosen'], best[org]['score']):
                    best[org] = it
        cands = sorted(best.values(), key=lambda it: (-it['chosen'], -it['score']))
        named = [it for it in cands if G.contains(name, ror.get(it['organization']['id'], {}))]
        top = (named or cands or [None])[0]
        rest = [it for it in (named or cands)[1:] if it is not top]
        second = rest[0]['score'] if rest else 0.0
        row = dict(string=raw, cleaned=name, rows=n, ror='', ror_name='', ror_country='', wikidata='', score='', decision='no_match', basis='')
        if top:
            rec = ror.get(top['organization']['id'], {})
            row.update(ror=top['organization']['id'], ror_name=rec.get('name', ''), ror_country=rec.get('country', ''),
                       wikidata=rec.get('wikidata', ''), score=round(top['score'], 3))
            if rec.get('status') != 'active':
                row.update(decision='review', basis=f"ROR record {rec.get('status', 'missing')}")
            elif not G.contains(name, rec):
                row.update(decision='review', basis=f"name not contained; score {top['score']:.2f}")
            elif top['chosen'] or (top['score'] >= 0.9 and top['score'] - second >= 0.05):
                row.update(decision='accepted', basis='chosen' if top['chosen'] else f"score {top['score']:.2f}, next {second:.2f}")
            else:
                row.update(decision='review', basis=f"score {top['score']:.2f}, next {second:.2f}")
        stats[row['decision']] += 1
        out.append(row)
        if i % 500 == 0:
            print(f'{i}/{len(todo)} {dict(stats)}', flush=True)
    tmp = args.out / 'signature-institutions.csv.tmp'
    with tmp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    tmp.replace(args.out / 'signature-institutions.csv')
    rows_by = Counter()
    for r in out:
        rows_by[r['decision']] += r['rows']
    summary = dict(strings=len(out), min_count=args.min, decisions=dict(stats), signatures_by_decision=dict(rows_by),
                   signatures_with_institution=sum(counts.values()),
                   distinct_ror=len({r['ror'] for r in out if r['decision'] == 'accepted'}), ror_dump=ROR.name)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
