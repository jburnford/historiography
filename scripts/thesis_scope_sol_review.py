"""Doctoral theses held out of the History corpus, read by the outside reviewer (Sol, 2026-11-19/21, job
7-thesis-scope-holds): releases under existing rulings, and the decision sheet for the classes the user has not ruled.

Input: data/identifiers/sol-review-2026-11-19/7-thesis-scope-holds/{verdicts.jsonl,queue.csv} (latest line per case;
Sol appends superseding lines). Audit: data/field-research/thesis-scope-decision-2026-11-21/audit.csv.

Release rule (RELEASE below; audit 39/40 right on 40 release candidates that passed it, the one miss a philosophy
department now excluded by PHIL): Sol verdict `history`, agrees_with_hold `no`, confidence high, the original hold
ground is not an unruled class (church history, history of religions, philosophy of science), and Sol's department
names a History unit (History, Geschichte, Histoire, Storia, Ancient History ...), not History didactics and not a
philosophy department. Everything else Sol read as History stays held and is listed (held-history-reads.csv).

Writes, in the forms the pipelines read:
  data/field-research/dnb-germany-harvest-2026-11-14/screen-overrides-2026-11-21.csv   (dnb_id, decision, note)
  data/field-research/france-theses-resurvey-2026-11-15/scope-overrides-2026-11-21.csv (nnt, decision, note)
  data/field-research/diva-sweden-pilot-2026-11-14/scope-overrides-2026-11-21.csv      (record_id, decision, note)
and the decision sheet tables in data/field-research/thesis-scope-decision-2026-11-21/ (titles and departments only;
no abstracts).

    python3 scripts/thesis_scope_sol_review.py
"""
import csv
import gzip
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / 'data/identifiers/sol-review-2026-11-19/7-thesis-scope-holds'
FR = ROOT / 'data/field-research'
OUT = FR / 'thesis-scope-decision-2026-11-21'
DNB_TABLE = FR / 'dnb-germany-harvest-2026-11-14/theses.csv.gz'
PROV = 'Sol read 2026-11-19/21, audited'

HIST = re.compile(r'(?i)histor|geschicht|histoire|storia|ancient history|alte geschichte')
UNRULED_HOLD = re.compile(r'(?i)church history|history of religions|philosophy of science')
PHIL = re.compile(r'(?i)Philosophisches Seminar|philosophy of science|philosophie des sciences|Wissenschaftsphilosophie')
ART_UNIT = re.compile(r"(?i)art.history|history.(of|in).art|kunstgeschicht|kunsthistor|histoire de l.art|storia dell.arte|architectur")
DIDACT = re.compile(r'(?i)didact|didakt')
RULING = [  # (pattern on Sol's reason, ruling named in the override note)
    (re.compile(r'(?i)economic.history'), 'economic history counts (ruling 2026-11-17)'),
    (re.compile(r'(?i)history.of.(science|medicine|archaeolog)'), 'history of science counts (ruling 2026-11-16/17)'),
    (re.compile(r'(?i)ancient'), 'ancient history counts unless archaeology (ruling 2026-11-17)'),
    (re.compile(r'(?i)history.of.education'), 'history of education counts (ruling 2026-11-16)'),
]
SOURCE = {'DNB': 'DNB', 'theses.fr': 'theses.fr', 'SwePub / DiVA': 'SwePub', 'Canada user-run register': 'Canada',
          'Canada eligibility overrides': 'Canada', 'Edinburgh': 'Edinburgh', 'Oxford': 'Oxford'}


def load():
    cases = {}
    with open(JOB / 'verdicts.jsonl', encoding='utf-8') as fh:
        for line in fh:
            d = json.loads(line)
            cases[d['case']] = d
    with open(JOB / 'queue.csv', newline='', encoding='utf-8') as fh:
        queue = {r['case']: r for r in csv.DictReader(fh)}
    return cases, queue


def release(d, ground):
    """'release' or the reason a thesis Sol read as History (and the hold as wrong) stays held."""
    if d['verdict'] != 'history' or d.get('agrees_with_hold') != 'no':
        return None
    dept = d.get('department') or ''
    if UNRULED_HOLD.search(ground):
        return 'held: original ground is an unruled class (church history / history of religions / philosophy of science)'
    if d['confidence'] != 'high':
        return 'held: Sol confidence medium'
    if DIDACT.search(dept):
        return 'held: History didactics (screened out as didactics; not ruled as history of education)'
    if PHIL.search(dept):
        return 'held: philosophy department / philosophy of science (not ruled)'
    if not HIST.search(dept) or ART_UNIT.search(dept):
        return 'held: department not a named History unit (economics, Egyptology, faculty only ...)'
    return 'release'


def history_unit(dept):
    dept = dept or ''
    return bool(HIST.search(dept)) and not PHIL.search(dept) and not ART_UNIT.search(dept)


def ruling(d):
    text = d.get('reason') or ''
    return next((r for rx, r in RULING if rx.search(text)), 'History PhD (History unit; rulings 2026-11-16/17)')


def unruled_class(d, ground):
    """The unruled class a held thesis belongs to, for the decision sheet, or None."""
    v = d['verdict']
    if v == 'religion-or-church-history' or (v == 'history' and re.search(r'(?i)church history|history of religions|religious-studies', ground)):
        return 'church history / history of religions'
    if v == 'art-history':
        return 'art history'
    if v == 'philology-or-text-edition':
        return 'philology / text edition'
    if v == 'philosophy' or (v == 'history' and re.search(r'(?i)philosophy of science', ground)) or \
            (v == 'history' and PHIL.search(d.get('department') or '')):
        return 'philosophy / philosophy of science'
    if re.search(r'(?i)History code', ground):
        return 'other-subject doctorate carrying a History code'
    return None


def write(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def main():
    cases, queue = load()
    dnb = {}
    with gzip.open(DNB_TABLE, 'rt', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            dnb[r['dnb_id']] = r
    rel, held_hist = [], []
    for case, d in sorted(cases.items()):
        g = queue[case]['ground_now']
        k = release(d, g)
        if not k:
            continue
        row = dict(case=case, thesis_id=d['thesis_id'], source=SOURCE[d['source']], title=d['title'], year=d.get('year'),
                   university=d.get('university'), department=d.get('department'), hold_was=g,
                   file_status=queue[case]['file_status'], sol_confidence=d['confidence'], decision=k)
        if d['source'] == 'DNB':
            r = dnb.get(d['thesis_id'], {})
            row['dnb_confidence'] = r.get('confidence')
            row['free_link'] = 'yes' if r.get('free_links') else 'no'
        if k == 'release':
            row['ruling'] = ruling(d)
            rel.append(row)
        else:
            held_hist.append(row)

    def note(r):
        return (f"{PROV}: {r['ruling']}: '{r['title'][:160]}' ({r['university']} {r['year']}; department: "
                f"{(r['department'] or '')[:120]}); was held as: {r['hold_was'][:120]}")
    write(FR / 'dnb-germany-harvest-2026-11-14/screen-overrides-2026-11-21.csv', ['dnb_id', 'decision', 'note'],
          [dict(dnb_id=r['thesis_id'], decision='include', note=note(r)) for r in rel if r['source'] == 'DNB'])
    write(FR / 'france-theses-resurvey-2026-11-15/scope-overrides-2026-11-21.csv', ['nnt', 'decision', 'note'],
          [dict(nnt=r['thesis_id'], decision='include', note=note(r)) for r in rel if r['source'] == 'theses.fr'])
    write(FR / 'diva-sweden-pilot-2026-11-14/scope-overrides-2026-11-21.csv', ['record_id', 'decision', 'note'],
          [dict(record_id=r['thesis_id'], decision='include', note=note(r)) for r in rel if r['source'] == 'SwePub'])
    f = ['case', 'source', 'title', 'year', 'university', 'department', 'hold_was', 'ruling', 'decision', 'file_status',
         'dnb_confidence', 'free_link', 'sol_confidence']
    write(OUT / 'released.csv', f, rel)
    write(OUT / 'held-history-reads.csv', f, held_hist)

    # ---- decision sheet: unruled classes --------------------------------------------------------------------
    by_class = defaultdict(list)
    for case, d in sorted(cases.items()):
        c = unruled_class(d, queue[case]['ground_now'])
        if c and release(d, queue[case]['ground_now']) != 'release':
            by_class[c].append(d)
    counts = []
    for c, L in by_class.items():
        n = Counter(SOURCE[d['source']] for d in L)
        hist_unit = sum(1 for d in L if history_unit(d.get('department')))
        counts.append(dict(cls=c, total=len(L), history_unit=hist_unit, sol_read_history=sum(d['verdict'] == 'history' for d in L),
                           borderline=sum(d.get('borderline') == 'yes' for d in L),
                           **{s: n.get(s, 0) for s in ('DNB', 'theses.fr', 'SwePub', 'Canada', 'Edinburgh', 'Oxford')}))
    write(OUT / 'unruled-class-counts.csv', ['cls', 'total', 'history_unit', 'sol_read_history', 'borderline', 'DNB',
                                             'theses.fr', 'SwePub', 'Canada', 'Edinburgh', 'Oxford'], counts)
    theo = re.compile(r'(?i)theolog|divinity|religio|patrolog|bibl|testament|church')
    dep = Counter()
    for c, L in by_class.items():
        for d in L:
            dept = d.get('department') or ''
            dep[(c, 'History unit' if history_unit(dept) else 'theology / religious studies' if theo.search(dept)
                 else 'not established' if not dept.strip() else 'other unit')] += 1
    write(OUT / 'unruled-class-by-department.csv', ['cls', 'department_type', 'theses'],
          [dict(cls=c, department_type=t, theses=n) for (c, t), n in sorted(dep.items())])
    ex = []
    rnd = random.Random(20261121)
    for c, L in sorted(by_class.items()):
        # 15 per class: spread over the sources (each source's share, at least one), then random
        bysrc = defaultdict(list)
        for d in L:
            bysrc[SOURCE[d['source']]].append(d)
        pick = []
        for s, xs in sorted(bysrc.items(), key=lambda x: -len(x[1])):
            k = max(1, round(15 * len(xs) / len(L)))
            pick += rnd.sample(xs, min(k, len(xs)))
        pick = pick[:15]
        for d in pick:
            ex.append(dict(cls=c, source=SOURCE[d['source']], title=d['title'][:200], year=d.get('year'),
                           university=d.get('university'), department=(d.get('department') or '')[:160],
                           history_unit='yes' if history_unit(d.get('department')) else 'no'))
    write(OUT / 'unruled-class-examples.csv', ['cls', 'source', 'title', 'year', 'university', 'department', 'history_unit'], ex)
    rep = dict(cases=len(cases), released=len(rel), released_by_source=dict(Counter(r['source'] for r in rel)),
               released_by_ruling=dict(Counter(r['ruling'] for r in rel)),
               released_file_status=dict(Counter((r['source'], r['file_status'], r.get('free_link', '')) for r in rel).most_common()),
               held_history_reads=dict(Counter(r['decision'] for r in held_hist)),
               unruled={c['cls']: c['total'] for c in counts})
    rep['released_file_status'] = {' / '.join(k): v for k, v in rep['released_file_status'].items()}
    (OUT / 'summary.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
