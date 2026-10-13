#!/usr/bin/env python3
"""A historians' family tree from the AHA Directory of History Dissertations.

Each record gives a dissertator and (for about half) one or two advisors with stable AHA ids.
Advisor -> student edges are therefore certain at the record level. Lineages need one more
step: linking an advisor to their OWN dissertation, which the directory records only by name.

Link rule (conservative): an advisor (AHA id, "Given Surname") matches a dissertation whose
dissertator has the same folded surname and a compatible given name (same first name, or same
initial where one side is an initial; a full first-name match beats an initial-only one), completed at least MIN_GAP years before the advisor's
first supervised dissertation. A link is accepted only when exactly one dissertation qualifies;
ambiguous advisors are then settled by subject only when one namesake's title is clearly closest to
the titles of the advisor's own students (TF-IDF cosine at least MIN_TOPIC and at least
TOPIC_MARGIN times the next candidate's); the rest are reported, not guessed.

Writes data/field-research/aha-dissertations-2026-10-13/genealogy/: edges.csv (advisor id ->
student record), advisor-links.csv (advisor id -> own dissertation, with status), lineages.json
(summary statistics, the deepest chains, the largest academic families). Run from anywhere.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'data/field-research/aha-dissertations-2026-10-13'
OUT = DIR / 'genealogy'
MIN_GAP = 3


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z ]+', ' ', s).split()


def split_advisor(name):
    """'Jay Rubenstein' or 'Rubenstein, Jay' -> (surname tokens, given tokens)."""
    if ',' in name:
        sur, giv = name.split(',', 1)
        return fold(sur), fold(giv)
    t = fold(name)
    return (t[-1:], t[:-1]) if t else ([], [])


def given_ok(a, b):
    if not a or not b:
        return False
    x, y = a[0], b[0]
    return x == y or (len(x) == 1 and y.startswith(x)) or (len(y) == 1 and x.startswith(y))


MIN_TOPIC, TOPIC_MARGIN = 0.06, 2.5  # character n-grams (4-6) catch environmental/environmentalists
VEC = None


def topic_scores(cands, kids):
    """Cosine similarity (TF-IDF over all titles) between each candidate's title and the advisor's
    students' titles taken together."""
    from sklearn.metrics.pairwise import cosine_similarity
    a = VEC.transform([r['title'] for r in cands])
    b = VEC.transform([' '.join(k['title'] for k in kids)])
    return [float(x) for x in cosine_similarity(a, b)[:, 0]]


def main():
    global VEC
    recs = [json.loads(l) for l in (DIR / 'records.jsonl').open()]
    from sklearn.feature_extraction.text import TfidfVectorizer
    VEC = TfidfVectorizer(analyzer='char_wb', ngram_range=(4, 6), min_df=3, sublinear_tf=True).fit([r['title'] for r in recs])
    decided = {d['advisor_id']: d for d in csv.DictReader((OUT / 'identity-decisions.csv').open())} if (OUT / 'identity-decisions.csv').exists() else {}
    by_id = {r['id']: r for r in recs}
    namesakes = []
    by_surname = defaultdict(list)
    for r in recs:
        sur, giv = split_advisor(r['dissertator'])
        if sur:
            by_surname[' '.join(sur)].append((r, giv))
    students, names = defaultdict(list), {}
    for r in recs:
        for aid, name in r['advisors']:
            students[aid].append(r)
            names.setdefault(aid, name)
    links = {}
    status = Counter()
    for aid, name in names.items():
        sur, giv = split_advisor(name)
        first = min((s['year'] for s in students[aid] if s['year']), default=None)
        cands = [(r, g) for r, g in by_surname.get(' '.join(sur), []) if given_ok(giv, g) and r['year'] and first and r['year'] <= first - MIN_GAP]
        exact = [r for r, g in cands if giv and g and giv[0] == g[0] and len(giv[0]) > 1]
        cands = exact if exact else [r for r, _ in cands]  # a full first-name match beats an initial-only match
        if len(cands) > 1:
            namesakes.append(dict(advisor_id=aid, advisor=name, candidates='; '.join(f"{r['id']}:{r['year']}:{r['department']}" for r in cands)))
        st, basis = ('linked', 'unique name and date') if len(cands) == 1 else ('ambiguous', '') if cands else ('not_in_directory', '')
        if aid in decided:  # a recorded decision overrides the automatic rules
            d = decided[aid]
            cands, st, basis = [by_id[d['own_record']]], 'linked_by_decision', f"{d['source']}, {d['date']}: {d['note']}"
            ranked = cands
        elif st == 'ambiguous':  # several namesakes: the one whose subject matches the advisor's students
            scores = topic_scores(cands, students[aid])
            ranked = sorted(zip(scores, cands), key=lambda x: -x[0])
            (s1, best), s2 = ranked[0], ranked[1][0]
            if s1 >= MIN_TOPIC and s1 >= TOPIC_MARGIN * s2:
                cands, st = [best], 'linked_by_topic'
                basis = (f"{len(ranked)} namesakes; title similarity with the students' titles {s1:.2f} "
                         f"against {s2:.2f} for the next candidate")
        status[st] += 1
        links[aid] = dict(advisor_id=aid, advisor=name, first_student_year=first, students=len(students[aid]),
                          status=st, own_record=cands[0]['id'] if len(cands) == 1 else '',
                          own_year=cands[0]['year'] if len(cands) == 1 else '',
                          own_department=cands[0]['department'] if len(cands) == 1 else '',
                          own_advisors='; '.join(n for _, n in cands[0]['advisors']) if len(cands) == 1 else '',
                          candidates=len(cands) if st not in ('linked_by_topic', 'linked_by_decision') else len(ranked), basis=basis)
    # record id -> advisor id when that dissertator is a linked advisor
    advisor_of_record = {l['own_record']: aid for aid, l in links.items() if l['own_record']}
    # parent of an advisor: the advisors of their own dissertation
    parents = {aid: [a for a, _ in next(r for r in recs if r['id'] == l['own_record'])['advisors']]
               for aid, l in links.items() if l['own_record']}

    def depth(aid, seen=()):
        ps = [p for p in parents.get(aid, []) if p not in seen]
        return 1 + max((depth(p, seen + (aid,)) for p in ps), default=0)

    def descendants(aid, seen=None):
        seen = set() if seen is None else seen
        for s in students[aid]:
            child = advisor_of_record.get(s['id'])
            if s['id'] not in seen:
                seen.add(s['id'])
                if child:
                    descendants(child, seen)
        return seen

    OUT.mkdir(exist_ok=True)
    with (OUT / 'edges.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['advisor_id', 'advisor', 'student_record', 'student', 'department', 'year', 'title', 'student_is_advisor_id'])
        for aid, rs in students.items():
            for r in rs:
                w.writerow([aid, names[aid], r['id'], r['dissertator'], r['department'], r['year'], r['title'], advisor_of_record.get(r['id'], '')])
    with (OUT / 'namesakes.csv').open('w', newline='') as f:  # same-name candidates are distinct people
        w = csv.DictWriter(f, fieldnames=['advisor_id', 'advisor', 'candidates'])
        w.writeheader()
        w.writerows(namesakes)
    with (OUT / 'advisor-links.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(next(iter(links.values()))))
        w.writeheader()
        w.writerows(sorted(links.values(), key=lambda l: -l['students']))
    chains = sorted(((depth(a), a) for a in names), reverse=True)[:15]

    def chain(aid):
        out, cur, seen = [], aid, set()
        while cur and cur not in seen:
            seen.add(cur)
            out.append(f"{names[cur]} ({links[cur]['own_year'] or '?'})")
            cur = next(iter(parents.get(cur, [])), None)
        return ' ← '.join(out)
    families = sorted(((len(descendants(a)), a) for a in names), reverse=True)[:25]
    summary = dict(records=len(recs), with_advisor=sum(bool(r['advisors']) for r in recs), advisors=len(names),
                   edges=sum(len(v) for v in students.values()), advisor_links=dict(status),
                   generations_max=chains[0][0] if chains else 0,
                   deepest=[dict(depth=d, chain=chain(a)) for d, a in chains],
                   largest_families=[dict(advisor=names[a], students=len(students[a]), descendants=n, own_year=links[a]['own_year'])
                                     for n, a in families],
                   method=__doc__.strip().splitlines()[0], min_gap=MIN_GAP)
    (OUT / 'lineages.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: summary[k] for k in ('records', 'with_advisor', 'advisors', 'edges', 'advisor_links', 'generations_max')}))
    for c in summary['deepest'][:6]:
        print(c['depth'], c['chain'])
    for f in summary['largest_families'][:12]:
        print(f"{f['advisor']:28} students {f['students']:3}  descendants {f['descendants']:4}  own PhD {f['own_year']}")


if __name__ == '__main__':
    main()
