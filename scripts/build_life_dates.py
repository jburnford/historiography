"""Life dates for the knowledge graph, one row per internal person key (PID-PLAN.md; user 2026-10-30).

Merges every source of birth and death dates the project holds, keyed by the person's internal key
(data/identifiers/events.jsonl):
- `wd`: the Wikidata sheet (data/people-wikidata.json, accepted QIDs; the 2026-10-30 QID review verdict
  is kept as `qid_review`);
- `review`: the sourced living/deceased reviews (data/historian-life-review.json,
  data/theorist-life-review.json);
- `lc`: LC name authorities from the atlas and canon-map routes
  (data/field-research/lc-authorities-2026-10-30/{atlas,canon}), exact tier only, since a candidate may
  be a namesake.

For birth and death separately: when the sources agree on the year, the most precise value is kept and
every agreeing source is listed; when years disagree, the row is flagged `conflict` and all values are
listed for review. The chosen year is the one most sources give; a tie follows source order
(LC 046 > reviewed > Wikidata > LC heading); within the chosen year the most precise value wins.

The graph keeps every date, including living people's. Site exports must apply the living rule
(scripts/historian_life_review.withhold_living_birth): `status` here says `deceased`, `living` (a
sourced review), or `presumed_living` (no death recorded, born within 120 years).

    python3 scripts/build_life_dates.py   # writes data/person-facts/life-dates.csv and summary.json
"""
import csv
import datetime
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import State

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/person-facts'
LC = ROOT / 'data/field-research/lc-authorities-2026-10-30'
PRECISION = {'day': 3, 'month': 2, 'year': 1, 'approximate': 0, 'decade': 0, 'century': 0}
RANK = {'lc_046': 0, 'review': 1, 'wd': 2, 'lc_heading': 3}


def year(v):
    m = re.match(r'^(-?\d{1,4})', str(v or '').lstrip('+'))
    return int(m.group(1)) if m else None


def lc_rows(state):
    for name, fname in (('atlas', 'atlas-people-lc.csv'), ('canon', 'canon-people-lc.csv')):
        path = LC / name / fname
        if not path.exists():
            continue
        with path.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get('tier') != 'exact' or not r.get('key'):
                    continue
                for part in ('birth', 'death'):
                    if r.get(f'{part}_value'):
                        src = 'lc_046' if r[f'{part}_source'] == '046' else 'lc_heading'
                        yield r['key'], part, r[f'{part}_value'], r[f'{part}_precision'], src, f'lcnaf:{r["lcnaf"]}'


def main():
    state = State.load(ROOT / 'data/identifiers/events.jsonl')
    review = {}
    with (ROOT / 'data/field-research/atlas-qid-review-2026-10-30/review.csv').open(newline='', encoding='utf-8') as f:
        review = {r['person_id']: r['verdict'] for r in csv.DictReader(f)}

    def key_of(pid):
        k = state.lookup(f'atlas:person:{pid}')
        return k[0] if len(k) == 1 else None

    facts = defaultdict(list)           # key -> [(part, value, precision, source, ref)]
    status, qid_review = {}, {}
    sheet = json.loads((ROOT / 'data/people-wikidata.json').read_text(encoding='utf-8'))
    for r in sheet['people']:
        if r.get('status') != 'accepted' or not r.get('wikidata') or not (k := key_of(r['person_id'])):
            continue
        qid_review[k] = review.get(r['person_id'], '')
        for part in ('birth', 'death'):
            if (r.get('life') or {}).get(part):
                facts[k].append((part, r['life'][part], r['life'].get(f'{part}_precision') or 'year', 'wd',
                                 f'wd:{r["wikidata"]["qid"]}'))
    for path in ('data/historian-life-review.json', 'data/theorist-life-review.json'):
        for r in json.loads((ROOT / path).read_text(encoding='utf-8'))['people']:
            if not (k := key_of(r['person_id'])):
                continue
            status[k] = r['status']
            if r.get('birth_year') is not None:
                facts[k].append(('birth', str(r['birth_year']), 'year', 'review', path))
            if r['status'] == 'deceased' and (r.get('death_date') or r.get('death_year')):
                facts[k].append(('death', r.get('death_date') or str(r['death_year']),
                                 r.get('death_precision') or 'year', 'review', path))
    for k, part, value, prec, src, ref in lc_rows(state):
        facts[k].append((part, value, prec, src, ref))

    this_year = datetime.date.today().year
    rows, stats = [], Counter()
    for k in sorted(facts, key=lambda x: int(x.split('-')[1])):
        row = dict(key=k, label=state.keys[k]['label'], qid_review=qid_review.get(k, ''))
        for part in ('birth', 'death'):
            vals = [f for f in facts[k] if f[0] == part and year(f[1]) is not None]
            years = {year(v) for _, v, *_ in vals}
            if not vals:
                row.update({part: '', f'{part}_precision': '', f'{part}_sources': '', f'{part}_check': ''})
                continue
            votes = Counter(year(f[1]) for f in vals)          # one vote per source assertion
            top = max(votes.values())
            pool = [f for f in vals if votes[year(f[1])] == top]   # majority year; ties fall to source order
            pool = [f for f in pool if year(f[1]) == year(min(pool, key=lambda f: RANK[f[3]])[1])]
            # A January 1 date is often a year-only placeholder (LC gives 1926-01-01 for Foucault, born
            # 1926-10-15): when another source has a different day in that year, it counts as a year.
            days = {f[1] for f in pool if PRECISION.get(f[2], 0) == 3}
            if len(days) > 1:
                pool = [(f[0], f[1][:4] if f[1].endswith('-01-01') else f[1], 'year' if f[1].endswith('-01-01')
                         else f[2], *f[3:]) for f in pool]
            best = max(pool, key=lambda f: (PRECISION.get(f[2], 0), -RANK[f[3]]))
            day_conflict = len({f[1] for f in pool if PRECISION.get(f[2], 0) == 3}) > 1
            check = ('conflict' if len(years) > 1 else 'day_conflict' if day_conflict else
                     'agree' if len({f[3] for f in vals}) > 1 else 'single_source')
            stats[f'{part}_{check}'] += 1
            row.update({part: best[1], f'{part}_precision': best[2],
                        f'{part}_sources': ' '.join(sorted({f'{f[4]}={f[1]}' for f in vals})), f'{part}_check': check})
        born = year(row['birth'])
        row['status'] = ('deceased' if row['death'] or status.get(k) == 'deceased' else
                         'living' if status.get(k) == 'living' else
                         'deceased' if born is not None and born < this_year - 120 else 'presumed_living')
        stats[row['status']] += 1
        rows.append(row)

    OUT.mkdir(parents=True, exist_ok=True)
    fields = ['key', 'label', 'status', 'birth', 'birth_precision', 'birth_check', 'birth_sources', 'death',
              'death_precision', 'death_check', 'death_sources', 'qid_review']
    with (OUT / 'life-dates.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary = dict(people=len(rows), built=str(datetime.date.today()), **dict(sorted(stats.items())),
                   lc_routes=[p.name for p in (LC / 'atlas', LC / 'canon') if any(p.glob('*-people-lc.csv'))])
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
