"""Atlas people -> LC name authorities through their Wikidata QIDs (P244), checked against the LC index (PID-PLAN.md section 6).

For every accepted QID in data/people-wikidata.json, Wikidata's LC authority ID (P244) is read from the
Wikidata Query Service and checked against the local LC name index (scripts/lc_names_index.py):
- the authority exists, is live (not deprecated) and is not undifferentiated;
- its heading is name-compatible with the atlas label (identity_routes.compatible);
- the LC and Wikidata birth years do not disagree (both present and different = disagreement).

Tiers, matching scripts/lc_canon_people.py so scripts/key_lc_canon.py can apply either run:
- `exact`: the QID was confirmed by the 2026-10-30 QID review, Wikidata gives exactly one P244, and all
  checks pass;
- `candidate_*`: plausible QIDs, several P244 values, name or date disagreement.
Life dates from LC are kept with source and precision; the knowledge graph keeps all of them, and only
site exports drop living people's birth years.

    python3 scripts/lc_atlas_people.py --names /mnt/e/lc-authorities/personal-names.parquet \\
        --out data/field-research/lc-authorities-2026-10-30/atlas
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from identifiers import State
from identity_routes import compatible
from lc_canon_people import as_credit
from lc_resolve_authorities import label_dates, life, load_names
from review_atlas_qids import sparql

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / 'data/people-wikidata.json'
REVIEW = ROOT / 'data/field-research/atlas-qid-review-2026-10-30/review.csv'
# Hand review 2026-10-30: the name or date checks failed only because of atlas label suffixes,
# transliteration, mononyms or pen names, or a one-to-two-year birth discrepancy; LC and Wikidata are the
# same person and the QID was already confirmed. (C. L. R. James has two P244 values and stays a candidate.)
# C. L. R. James: Wikidata lists his authorised heading and the authority for his pseudonym 'J. R. Johnson'
# (LC keeps pseudonyms as separate authorities). The heading is the anchor; the pseudonym is recorded.
PREFERRED = {'clr_james': ('n50028957', 'n95037594 is the pseudonym J. R. Johnson')}
HAND_CONFIRMED = {'white', 'latour', 'rodney', 'sun_tzu', 'talal_asad', 'te_rangi_hiroa', 'gyanendra_pandey',
                  'dharma_kumar', 'alexander_savine', 'valerie_korinek'}


def p244(qids, cache):
    cache.mkdir(parents=True, exist_ok=True)
    out = {q: set() for q in qids}
    qids = sorted(qids)
    for i in range(0, len(qids), 300):
        part = qids[i:i + 300]
        rows = sparql('SELECT ?item ?lc WHERE { VALUES ?item { %s } ?item wdt:P244 ?lc . }'
                      % ' '.join(f'wd:{q}' for q in part), cache, 'p244-' + hashlib.sha1(' '.join(part).encode()).hexdigest()[:12])
        for r in rows:
            out[r['item']['value'].rsplit('/', 1)[-1]].add(r['lc']['value'])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sheet = json.loads(SHEET.read_text(encoding='utf-8'))
    people = [r for r in sheet['people'] if r.get('status') == 'accepted' and r.get('wikidata')]
    with REVIEW.open(newline='', encoding='utf-8') as f:
        review = {r['person_id']: r for r in csv.DictReader(f)}
    state = State.load(ROOT / 'data/identifiers/events.jsonl')
    lc_of = p244({r['wikidata']['qid'] for r in people}, args.out / 'raw')
    names = load_names(args.names, lcids={x for v in lc_of.values() for x in v})
    by_id = names[0]

    rows, stats = [], Counter()
    for r in people:
        pid, qid = r['person_id'], r['wikidata']['qid']
        rv = review.get(pid, {})
        key = state.lookup(f'atlas:person:{pid}')
        lcs = sorted(lc_of.get(qid, ()))
        row = dict(key=key[0] if len(key) == 1 else '', person_id=pid, label=rv.get('atlas_label', pid), qid=qid,
                   qid_verdict=rv.get('verdict', ''), wikidata_p244=' '.join(lcs))
        if not lcs:
            row['outcome'] = 'no_p244'
        else:
            lc = PREFERRED[pid][0] if pid in PREFERRED and PREFERRED[pid][0] in lcs else lcs[0]
            if pid in PREFERRED:
                row['note'] = PREFERRED[pid][1]
            a = by_id.get(lc)
            if not a:
                row['outcome'] = 'p244_not_in_lc_index'
            elif a['deprecated']:
                row['outcome'] = 'p244_deprecated'
            elif a['undifferentiated']:
                row['outcome'] = 'p244_undifferentiated'
            else:
                family, _, given = a['label'].partition(', ')
                given = given.split(', ')[0]
                name_ok = compatible(rv.get('atlas_label') or pid, given.split(' (')[0], family) or \
                    compatible(as_credit(rv.get('atlas_label', '')), given.split(' (')[0], family)
                lf = life(a, label_dates(a['label']))
                wd_birth = (rv.get('birth') or '')[:4].lstrip('+')
                dates_ok = not (lf['birth'][0] and wd_birth and lf['birth'][0] != wd_birth)
                if (len(lcs) == 1 or pid in PREFERRED) and (pid in HAND_CONFIRMED or pid in PREFERRED) \
                        and rv.get('verdict') == 'confirmed':
                    tier = 'exact'
                elif len(lcs) > 1:
                    tier = 'candidate_several_p244'
                elif not name_ok:
                    tier = 'candidate_name_disagrees'
                elif not dates_ok:
                    tier = 'candidate_dates_disagree'
                elif rv.get('verdict') != 'confirmed':
                    tier = 'candidate_plausible_qid'
                else:
                    tier = 'exact'
                row.update(outcome='resolved', lcnaf=lc, lc_label=a['label'], via='wikidata_p244', tier=tier,
                           confirmations=' '.join(c for c, ok in (('reviewed_qid', rv.get('verdict') == 'confirmed'),
                                                                  ('hand_review_2026-10-30', pid in HAND_CONFIRMED or pid in PREFERRED),
                                                                  ('birth_year_agrees', bool(lf['birth'][0] and wd_birth
                                                                                             and dates_ok)))
                                                  if ok),
                           evidence_works='', evidence_title='', wikidata_birth=wd_birth,
                           birth_year=lf['birth'][0], birth_value=lf['birth'][1], birth_source=lf['birth'][2],
                           birth_precision=lf['birth'][3], death_year=lf['death'][0], death_value=lf['death'][1],
                           death_source=lf['death'][2], death_precision=lf['death'][3])
        stats[row.get('tier') or row['outcome']] += 1
        rows.append(row)

    fields = ['key', 'person_id', 'label', 'qid', 'qid_verdict', 'wikidata_p244', 'outcome', 'lcnaf', 'lc_label', 'via',
              'tier', 'confirmations', 'evidence_works', 'evidence_title', 'wikidata_birth', 'birth_year',
              'birth_value', 'birth_source', 'birth_precision', 'death_year', 'death_value', 'death_source',
              'death_precision', 'note']
    with open(args.out / 'atlas-people-lc.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary = dict(people=len(rows), outcomes=dict(stats.most_common()),
                   with_lc_birth_year=sum(1 for r in rows if r.get('birth_year')))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
