"""Reviewers signed in JSTOR review text -> person keys, by name and institution (2026-11-06). Writes a proposal.

The JSTOR full-text session read the signature at the end (or head) of 251,035 JSTOR book reviews: which of the
review's metadata names is the reviewer, and the institution printed with it (186,188 with an institution, conf >=
0.75; handover data/field-research/jstor-fulltext-2026-11-06/HANDOVER-review-signatures.md). For a review work in
the graph (matched by DOI) whose signed reviewer is not yet credited, the reviewer joins the one key that
- has a name agreeing with the signed name (same family name; first given names agreeing beyond an initial:
  namesake_check_groups.names_agree_strict; full first given names on both), and
- (a review signed with a bare university system, 'University of Wisconsin', counts only for a key with a career
  window covering the review and its own record naming one campus of that system)
- is placed at the signed institution by its own records, with dates (2026-11-07, user: use dates wherever possible):
  the review must fall in the key's career window (no review before age 20 or 8 years before the PhD, none after
  death; career_window.py); a key with no dates needs a dated placing fact within ten years of the review. A bare
  university system ('University of California') places nobody, and reviews this route linked are never placing
  facts (no cascade) — (key_review_credit_merges.key_institutions: printed
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
from career_window import career_windows, in_window
from key_review_credit_merges import agree, dated, is_system, jstor_signatures, key_institutions
from key_review_reviewers import family
from namesake_check_groups import given_words, names_agree_strict
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

GRAPH = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--audit', action='store_true',
                    help='re-decide every signed review under the current rules and withdraw the signature-reviewer '
                         'claims they no longer make (2026-11-07: dated rules after the Fable review)')
    args = ap.parse_args()
    state = State.load(args.state)
    live = {k: r for k, r in state.keys.items() if r['type'] == 'person' and r['status'] in ('active', 'provisional')}
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    facts = key_institutions(live, db, state)
    windows = career_windows(state)
    sigs = jstor_signatures()
    by_family = defaultdict(list)
    for k, r in live.items():
        g = given_words(r['label'] or '')
        if g and len(g[0]) > 1:
            by_family[family(r['label'])].append(k)
    sig_claims = {k for k, v in state.keys.items() if v['type'] == 'claim' and v['status'] not in ('withdrawn', 'merged')
                  and any(a.startswith('signature-reviewer:') for a in v['anchors'])}
    works = db.execute(f"""SELECT w.key, w.an, w.year, list(a."from") FILTER (WHERE a."from" IS NOT NULL{" AND NOT list_contains($1, a.claim)" if args.audit else ""})
            FROM (SELECT key, year, unnest(anchors) AS an FROM '{GRAPH}/work.parquet' WHERE len(reviewer_names) > 0) w
            LEFT JOIN {keylog(GRAPH, 'authored')} a ON a."to" = w.key WHERE w.an LIKE 'doi:%' GROUP BY 1, 2, 3""",
            [sorted(sig_claims)] if args.audit else []).fetchall()
    decided = {}
    doi_of = {wk: an[4:].lower() for wk, an, _, _ in works}
    report, ops, sample = Counter(), [], []
    extra = defaultdict(list)    # pass 2: links pass 1 made, as dated placing facts (one level, never fed again)
    for npass in (1, 2):
        if npass == 2:
            for wk2, k2 in decided.items():
                sig2 = sigs.get(doi_of.get(wk2, ''))
                if sig2 and sig2[2]:
                    extra[k2].append((sig2[1], 'JSTOR signature re-checked', sig2[2], sig2[2]))
            report['pass2_placing_facts'] = sum(map(len, extra.values()))
        for wk, an, year, credited in works:
            sig = sigs.get(an[4:].lower())
            if not sig:
                continue
            name, institution, y = sig
            report['reviews_signed_with_institution'] += 1
            live_credited = [state.lookup(k) for k in credited or []]
            if wk in decided:
                continue
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
            when = y or year
            system = is_system(institution)
            if system:
                # 'University of Wisconsin' (1969): only a key dated by a career window that covers the review, and placed
                # at one campus of that system by its own record, can take it
                cands = [k for k in cands if windows.get(k) and any(x is not None for x in windows[k])]
                if not cands:
                    report['signed_with_a_university_system_only'] += 1
                    continue
            cands = [k for k in cands if in_window(when, windows.get(k))]
            if not cands:
                report['outside_every_career_window'] += 1
                continue
            placed = {k: [f for f in facts.get(k, []) + (extra.get(k, []) if npass == 2 else []) if agree(institution, f[0]) and not is_system(f[0])
                          and dated(when, f, windows.get(k))] for k in cands}
            placed = {k: v for k, v in placed.items() if v}
            if not placed:
                report['no_key_placed_there_then'] += 1
                continue
            if len(placed) > 1:
                report['several_keys_placed_there'] += 1
                continue
            k, why = next(iter(placed.items()))
            decided[wk] = k
            anchor = f'signature-reviewer:{wk}:{k}'
            if anchor in state.anchor:
                report['claim_exists'] += 1
                continue
            report['linked'] += 1
            report[f'linked_pass{npass}'] += 1
            report['by:' + why[0][1].split(' 1')[0].split(' 2')[0]] += 1
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=[anchor], relation=dict(subject=k, predicate='authored', object=wk),
                            basis=f"JSTOR review ({when}) signed {name}, {institution}; the key's own records place "
                                  f"{live[k]['label']} there ({why[0][1]}: {why[0][0]}, "
                                  f"{why[0][2] or '?'}-{why[0][3] or '?'}), the review falls in the key's career window, and no other key of that name"))
            if len(sample) < 80:
                sample.append(dict(review=wk, year=y or year, signed=name, institution=institution, key=k,
                                   label=live[k]['label'], facts=why[:3]))
    if args.audit:
        # withdraw signature claims the dated rules no longer make; keep the new links too (they may replace them)
        for c in sorted(sig_claims):
            r = state.relation[c]
            wk = next(iter(state.lookup(r['object'])), None)
            who = next(iter(state.lookup(r['subject'])), None)
            if wk is None or decided.get(wk) != who:
                ops.append(dict(event='withdraw', key=c, basis=(
                    'signature link re-checked under the dated rules (2026-11-07; user: use dates wherever possible; Fable '
                    'review: no year window, university-system names, links feeding later links): '
                    + ('now credited to another key' if decided.get(wk) else 'no key placed at the signed institution with dates that fit the review (career window, or a dated fact within ten years)'))))
                report['audit_withdrawn'] += 1
            else:
                report['audit_kept'] += 1
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
