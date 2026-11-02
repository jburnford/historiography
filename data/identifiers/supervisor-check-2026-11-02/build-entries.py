"""Groups of AHA supervisors for the Sol check of their candidate PID keys (2026-11-02).

Input: aha-career-2026-11-02e/candidates.json (supervisors without a public ID whose candidate key, or an
unkeyed LC authority of that name, the career route could not confirm). Each entry carries the supervisor's
AHA evidence (own dissertation or directory PhD school, up to six students with school, year and title) and
each candidate (key name, QID, ORCID, LC id, the career facts found). Entries are grouped eight to a folder
(one Sol agent per group), supervisors with most students first. Writes groups.json here.

    python3 data/identifiers/supervisor-check-2026-11-02/build-entries.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State  # noqa: E402

GROUP = 8
ORDER = ['one_fact', 'no_fact_agrees', 'item_states_no_career', 'age_disagrees', 'several_candidate_keys_join']
state = State.load(ROOT / 'data/identifiers')
cands = json.loads((ROOT / 'data/identifiers/aha-career-2026-11-02e/candidates.json').read_text())
with (ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.csv').open(newline='', encoding='utf-8') as f:
    recs = list(csv.DictReader(f))
by_token = defaultdict(list)
for r in recs:
    for t in (r['advisor_ids'] or '').split(';'):
        if t.strip():
            by_token[t.strip()].append(r)
entries = []
for c in cands:
    k = c['key']
    if k not in state.keys or state.keys[k]['status'] not in ('active', 'provisional'):
        continue
    tokens = [a[4:] for a in state.keys[k]['anchors'] if a.startswith('aha:')]
    studs = sorted((r for t in tokens for r in by_token[t]), key=lambda r: r['year'], reverse=True)
    entries.append(dict(
        id=k, supervisor=c['label'], aha_advisor_ids=tokens, outcome_of_automatic_check=c['outcome'],
        own_phd=c['own_dissertations'], students_total=c['students'],
        students=[dict(student=r['dissertator'], school=r['department'], year=r['year'], title=r['title'][:150]) for r in studs[:6]],
        candidates=[dict(graph_key=x['key'], name=x['label'], wikidata=x.get('qid'), orcid=x.get('orcid'), lc=x.get('lcnaf'),
                         facts_agreeing=dict(phd_school=x['phd_school'], employer=x['employer_schools']), age_ok=x['age_ok'])
                    for x in c['candidates']]))
entries.sort(key=lambda e: (ORDER.index(e['outcome_of_automatic_check']) if e['outcome_of_automatic_check'] in ORDER else 9, -e['students_total']))
groups = [dict(id=f'g{i // GROUP + 1:04d}', entries=entries[i:i + GROUP]) for i in range(0, len(entries), GROUP)]
(HERE / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
print(len(entries), 'supervisors,', len(groups), 'groups')
