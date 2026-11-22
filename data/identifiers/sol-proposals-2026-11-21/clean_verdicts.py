"""Step 1: clean the Sol verdict ledgers of 2026-11-19 (jobs 1, 2, 2b, 3, 4, 5) into derived tables.

Sol's files are never edited. For each job: latest line per case (append-only ledgers; corrections carry
`supersedes`), a record of repeats whose verdict changed, checked_at dates after the day the job finished set to that
day (flagged), identifier entries normalised to {value, url}. Jobs 2 and 2b are combined into one mint table; the
four cases both reviewers did are compared and a disagreement is held.

    python3 data/identifiers/sol-proposals-2026-11-21/clean_verdicts.py
"""
import csv, gzip, json, os, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / 'sol-review-2026-11-19'
OUT = HERE / 'clean'
JOBS = ['1-place-authors', '2-mint-list', '2b-mint-list-tail', '3-mixed-profiles', '4-orcid', '5-seed-links']


def job_end(job):
    """The day the job wrote DONE (the latest true checked_at)."""
    return time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(SRC / job / 'DONE')))


def norm_ids(ids):
    if isinstance(ids, dict):
        out = {}
        for k, v in ids.items():
            if isinstance(v, dict):
                v = dict(v)
                if 'id' in v and 'value' not in v:
                    v['value'] = v.pop('id')
            out[k] = v
        return out
    return ids


report = {}
latest_by_job = {}
conflicts = []
for job in JOBS:
    end = job_end(job)
    rows = [json.loads(l) for l in open(SRC / job / 'verdicts.jsonl', encoding='utf-8') if l.strip()]
    hist, latest = {}, {}
    fixed = 0
    for i, d in enumerate(rows, 1):
        d = dict(d)
        d['_line'] = i
        if str(d.get('checked_at', ''))[:10] > end:
            d['checked_at_as_written'] = d['checked_at']
            d['checked_at'] = end
            fixed += 1
        if 'identifiers' in d:
            d['identifiers'] = norm_ids(d['identifiers'])
        hist.setdefault(d['case'], []).append(d)
        latest[d['case']] = d
    n_conf = 0
    for case, hs in hist.items():
        if len(hs) > 1:
            vs = [(h['verdict'], h.get('mint_recommendation')) for h in hs]
            if len(set(vs)) > 1:
                n_conf += 1
                conflicts.append(dict(job=job, case=case, lines='|'.join(str(h['_line']) for h in hs),
                                      verdicts=' -> '.join(f"{v}/{m}" if m else v for v, m in vs),
                                      latest=hs[-1]['verdict'] + (f"/{hs[-1]['mint_recommendation']}" if 'mint_recommendation' in hs[-1] else '')))
        latest[case]['_n_lines'] = len(hs)
    latest_by_job[job] = latest
    c = Counter(d['verdict'] for d in latest.values())
    report[job] = dict(lines=len(rows), cases=len(latest), repeated_cases=sum(len(h) > 1 for h in hist.values()),
                       repeats_with_changed_verdict=n_conf, checked_at_fixed=fixed, job_end=end,
                       by_verdict=dict(c.most_common()))
    if any('mint_recommendation' in d for d in latest.values()):
        report[job]['by_mint'] = dict(Counter(d['mint_recommendation'] for d in latest.values()).most_common())
    with gzip.open(OUT / f'{job}.latest.jsonl.gz', 'wt', encoding='utf-8') as f:
        for d in latest.values():
            f.write(json.dumps(d, ensure_ascii=False) + '\n')

# combined mint table (2 + 2b)
a, b = latest_by_job['2-mint-list'], latest_by_job['2b-mint-list-tail']
both = sorted(set(a) & set(b))
mint = {}
overlap = []
for case in set(a) | set(b):
    da, db = a.get(case), b.get(case)
    d = dict(da or db)
    d['_job'] = '2' if da and not db else '2b' if db and not da else '2+2b'
    if da and db:
        agree = (da['verdict'], da['mint_recommendation']) == (db['verdict'], db['mint_recommendation'])
        overlap.append(dict(case=case, name=da.get('name'), job2=f"{da['verdict']}/{da['mint_recommendation']}",
                            job2b=f"{db['verdict']}/{db['mint_recommendation']}", agree=agree))
        if not agree:
            d['mint_recommendation'] = 'hold'
            d['_held_reason'] = 'the two mint reviewers disagree'
    mint[case] = d
with gzip.open(OUT / 'mint-combined.latest.jsonl.gz', 'wt', encoding='utf-8') as f:
    for d in mint.values():
        f.write(json.dumps(d, ensure_ascii=False) + '\n')
report['mint-combined'] = dict(cases=len(mint), shared_2_2b=len(both), overlap=overlap,
                               by_verdict=dict(Counter(d['verdict'] for d in mint.values()).most_common()),
                               by_mint=dict(Counter(d['mint_recommendation'] for d in mint.values()).most_common()),
                               by_verdict_mint=dict(Counter(f"{d['verdict']}/{d['mint_recommendation']}/{d['confidence']}" for d in mint.values()).most_common()))
# job-1 vs job-2/2b: reused verdicts and independent agreement on shared LC authorities
j1 = latest_by_job['1-place-authors']
shared1 = [c for c in mint if c in j1]
reused = sum(1 for c in shared1 if mint[c].get('reused_verdict'))
agree1 = sum(1 for c in shared1 if mint[c]['verdict'] == j1[c]['verdict'])
report['mint-combined']['shared_with_job1'] = dict(cases=len(shared1), marked_reused=reused, same_class=agree1)

with open(OUT / 'repeat-conflicts.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['job', 'case', 'lines', 'verdicts', 'latest'])
    w.writeheader(); w.writerows(conflicts)
(OUT / 'clean-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
print(json.dumps(report, indent=1, ensure_ascii=False))
