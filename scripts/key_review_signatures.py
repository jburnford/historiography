"""Reviewers signed in JSTOR review text -> person keys, by name and institution (2026-11-06). Writes a proposal.

The JSTOR full-text session read the signature at the end (or head) of 251,035 JSTOR book reviews: which of the
review's metadata names is the reviewer, and the institution printed with it (186,188 with an institution, conf >=
0.75; handover data/field-research/jstor-fulltext-2026-11-06/HANDOVER-review-signatures.md). For a review work in
the graph (matched by DOI) whose signed reviewer is not yet credited, the reviewer joins the one key that
- has a name agreeing with the signed name (same family name; first given names agreeing beyond an initial:
  namesake_check_groups.names_agree_strict; full first given names on both), and
- is placed at the signed institution by its own records (key_review_credit_merges.key_institutions: printed
  review credits, H-Soz-Kult signatures, IHR and AHA staff lists, ORCID employment, LC 373, earlier JSTOR
  signatures), institutions agreeing on their distinctive words (key_review_credit_merges.agree).
No other key of that name may be placed there. The name alone never links (Fable's review-route design review,
2026-11-05). The claim is `signature-reviewer:<review work>:<key>` (authored, recorded); a rerun extends a key's
institutions with the reviews linked here.

    python3 scripts/key_review_signatures.py --out data/identifiers/review-signatures-2026-11-06
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_review_credit_merges import agree, jstor_signatures, key_institutions
from key_review_reviewers import family
from namesake_check_groups import given_words, names_agree_strict

GRAPH = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    live = {k: r for k, r in state.keys.items() if r['type'] == 'person' and r['status'] in ('active', 'provisional')}
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    facts = key_institutions(live, db)
    sigs = jstor_signatures()
    by_family = defaultdict(list)
    for k, r in live.items():
        g = given_words(r['label'] or '')
        if g and len(g[0]) > 1:
            by_family[family(r['label'])].append(k)
    works = db.execute(f"""SELECT w.key, w.an, w.year, list(a."from") FILTER (WHERE a."from" IS NOT NULL)
            FROM (SELECT key, year, unnest(anchors) AS an FROM '{GRAPH}/work.parquet' WHERE len(reviewer_names) > 0) w
            LEFT JOIN '{GRAPH}/authored.parquet' a ON a."to" = w.key WHERE w.an LIKE 'doi:%' GROUP BY 1, 2, 3""").fetchall()
    report, ops, sample = Counter(), [], []
    for wk, an, year, credited in works:
        sig = sigs.get(an[4:].lower())
        if not sig:
            continue
        name, institution, y = sig
        report['reviews_signed_with_institution'] += 1
        live_credited = [state.lookup(k) for k in credited or []]
        if any(c and names_agree_strict(name, live[c[0]]['label']) for c in live_credited if c and c[0] in live):
            report['already_credited'] += 1
            continue
        g = given_words(name)
        if not g or len(g[0]) <= 1:
            report['initial_only_signed_name'] += 1
            continue
        cands = [k for k in by_family.get(family(name), []) if names_agree_strict(name, live[k]['label'])]
        if not cands:
            report['no_key_of_that_name'] += 1
            continue
        placed = {k: [f for f in facts.get(k, ()) if agree(institution, f[0])] for k in cands}
        placed = {k: v for k, v in placed.items() if v}
        if not placed:
            report['no_key_placed_there'] += 1
            continue
        if len(placed) > 1:
            report['several_keys_placed_there'] += 1
            continue
        k, why = next(iter(placed.items()))
        anchor = f'signature-reviewer:{wk}:{k}'
        if anchor in state.anchor:
            report['claim_exists'] += 1
            continue
        report['linked'] += 1
        report['by:' + why[0][1].split(' 1')[0].split(' 2')[0]] += 1
        ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                        anchors=[anchor], relation=dict(subject=k, predicate='authored', object=wk),
                        basis=f"JSTOR review ({y or year}) signed {name}, {institution}; the key's own records place "
                              f"{live[k]['label']} there ({why[0][1]}: {why[0][0]}) and no other key of that name"))
        if len(sample) < 80:
            sample.append(dict(review=wk, year=y or year, signed=name, institution=institution, key=k,
                               label=live[k]['label'], facts=why[:3]))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='JSTOR reviewers linked by name and the institution signed under the review', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
