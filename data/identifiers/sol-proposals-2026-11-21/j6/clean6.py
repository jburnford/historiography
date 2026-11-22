"""Job 6 (place people): latest verdict per (person, place) -> j6/clean6.jsonl and j6/works6.csv (one row per judged credit,
with the credit's source in the graph: explorer.duckdb e_authored_t, read-only)."""
import csv, json, collections
from pathlib import Path
import duckdb
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / 'data/identifiers/sol-review-2026-11-19/6-place-people'
latest, hist = {}, collections.defaultdict(list)
for line in open(SRC / 'verdicts.jsonl', encoding='utf-8'):
    d = json.loads(line)
    c = d.get('supersedes') or d['case']
    hist[c].append(d['verdict'])
    latest[c] = d
q = list(csv.DictReader(open(SRC / 'queue.csv', encoding='utf-8')))
qk = {(r['person'] if r['place'] == 'Q854' else f"Q16/{r['person']}"): r for r in q}
assert set(qk) == set(latest), (len(set(qk) - set(latest)), len(set(latest) - set(qk)))
c = duckdb.connect(str(ROOT / 'build/graph/explorer.duckdb'), read_only=True)
c.execute("SET memory_limit='1GB'; SET threads=2")
out, wrows = [], []
for case, d in sorted(latest.items()):
    r = qk[case]
    key = r['person']
    lab = c.execute('SELECT label, anchors FROM nodes WHERE key = ?', [key]).fetchone()
    e = {w: (src, claim, ev, role, state) for w, src, claim, ev, role, state in c.execute(
        'SELECT "to", source, claim, evidence, role, state FROM e_authored_t WHERE "from" = ?', [key]).fetchall()}
    rec = dict(case=case, key=key, place=r['place'], rank=int(r['rank']), queue_label=r['label'], work_count=int(r['work_count']),
               graph_label=lab[0] if lab else None, anchors=list(lab[1] or []) if lab else [], verdict=d['verdict'],
               confidence=d['confidence'], scholar_of_place=d.get('scholar_of_place'), reason=d.get('reason'),
               person=d.get('person'), evidence=d.get('evidence'), n_lines=len(hist[case]),
               history=hist[case])
    out.append(rec)
    for w in d.get('works') or []:
        src = e.get(w.get('work'), (None,) * 5)
        wrows.append(dict(case=case, key=key, place=r['place'], verdict=d['verdict'], work=w.get('work'), title=(w.get('title') or '')[:200],
                          year=w.get('year'), theirs=w.get('theirs'), about_place=w.get('about_place'), why=(w.get('why') or '')[:500],
                          credit_source=src[0] or ('keylog' if src[1] else None), claim=src[1], evidence=src[2], role=src[3], state=src[4]))
with open(HERE / 'clean6.jsonl', 'w', encoding='utf-8') as fh:
    for r in out:
        fh.write(json.dumps(r, ensure_ascii=False) + '\n')
with open(HERE / 'works6.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(wrows[0]))
    w.writeheader()
    w.writerows(wrows)
ch = [(k, v) for k, v in hist.items() if len(set(v)) > 1]
with open(HERE / 'repeat-conflicts6.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['case', 'history'])
    w.writerows([(k, ' > '.join(v)) for k, v in sorted(ch)])
print(len(out), 'cases;', len(wrows), 'credits;', len(ch), 'repeat conflicts')
print(collections.Counter(r['verdict'] for r in out))
print(collections.Counter((w['theirs'], w['about_place']) for w in wrows))
print(collections.Counter((w['credit_source'] or 'NONE') for w in wrows if w['theirs'] == 'no').most_common(15))
