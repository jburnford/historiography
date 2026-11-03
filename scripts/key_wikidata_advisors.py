"""Wikidata's doctoral advisors (P184) -> supervision claims in the key log (lesson 6 of the user's probes; 2026-11-03).

The AHA directory names advisors for North American history PhDs only; Wikidata states doctoral advisors for
many others (a UK supervision layer: Eric J. Evans -> E. P. Thompson). Input: the truthy P184 statements for
humans harvested from QLever (scripts/harvest_wikidata_doctoral_advisors.py, P184.tsv.gz). For each statement
whose student and advisor items each anchor exactly one live person key (two different keys):
- when the student authors exactly one doctoral thesis in the log (a work anchored `aha-diss:`, `diss-thesis:`
  or `wrap:`), a `supervised` claim from the advisor to that thesis, unless the advisor already supervises it;
- otherwise an `advised` claim (person -> person, Wikidata's own form), unless one exists.
Claims are anchored `wd-p184:<student QID>:<advisor QID>` and `recorded` (one source). The graph build
derives ADVISED edges (advisor -> student) from both forms.

    python3 scripts/key_wikidata_advisors.py --out data/identifiers/wikidata-advisors-2026-11-03
"""
import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from build_graph import work_kind
from identifiers import DEFAULT_DIR, ROOT, State, materialise

P184 = ROOT / 'data/person-registry/generated/wikidata-doctoral/P184.tsv.gz'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--p184', type=Path, default=P184)
    args = ap.parse_args()
    state = State.load(args.state)
    manifest = json.loads((args.p184.parent / 'manifest.json').read_text())

    def person(q):
        ks = [k for k in state.lookup(f'wd:{q}') if state.keys[k]['type'] == 'person']
        return ks[0] if len(ks) == 1 else None

    theses, supervised, advised = defaultdict(set), set(), set()
    for claim, subj, pred, obj in state.relations():
        if len(subj) != 1 or len(obj) != 1:
            continue
        if pred == 'authored' and state.keys[obj[0]]['type'] == 'work' and work_kind(state.keys[obj[0]]['anchors']) == 'thesis':
            theses[subj[0]].add(obj[0])
        elif pred == 'supervised':
            supervised.add((subj[0], obj[0]))
        elif pred == 'advised':
            advised.add((subj[0], obj[0]))
    report, ops, seen = Counter(), [], set()
    with gzip.open(args.p184, 'rt', newline='', encoding='utf-8') as f:
        rows = sorted({(r['qid'], r['advisor_qid']) for r in csv.DictReader(f, delimiter='\t')})
    for sq, aq in rows:
        s, a = person(sq), person(aq)
        if not s or not a:
            report['student_or_advisor_not_keyed'] += 1
            continue
        if s == a:
            report['same_key'] += 1
            continue
        anchor = f'wd-p184:{sq}:{aq}'
        if anchor in state.anchor or (s, a) in seen:
            report['claim_exists'] += 1
            continue
        seen.add((s, a))
        ts = theses.get(s, set())
        if len(ts) == 1:
            t = next(iter(ts))
            if (a, t) in supervised:
                report['supervised_already'] += 1
                continue
            obj = sorted(x for x in state.keys[t]['anchors'] if x.split(':', 1)[0] in ('aha-diss', 'diss-thesis', 'wrap'))[0]
            rel, report_as = dict(subject=f'wd:{aq}', predicate='supervised', object=obj), 'supervised'
        else:
            if (a, s) in advised:
                report['advised_already'] += 1
                continue
            rel, report_as = dict(subject=f'wd:{aq}', predicate='advised', object=f'wd:{sq}'), 'advised'
            report['advised_student_theses_%s' % ('none' if not ts else 'several')] += 1
        report[report_as] += 1
        ops.append(dict(event='mint', key=f'new:claim-{len(ops)}', type='claim', label='', resolution='recorded',
                        anchors=[anchor], relation=rel,
                        basis=f'Wikidata {sq} states doctoral advisor (P184) {aq} (QLever, {manifest["retrieved"][:10]})'))
    materialise(state, dict(basis='Wikidata doctoral advisors', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="Wikidata's doctoral advisor statements (P184) between keyed people: a supervised claim to the "
              "student's one thesis in the log, else an advised claim", decided_by='build', ops=ops),
        ensure_ascii=False) + '\n')
    summary = dict(statements=len(rows), **dict(sorted(report.items())))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
