"""Draw the job-6 audit sample (seed 20261121) and write a reading packet with graph facts (explorer.duckdb, read-only)."""
import csv, json, random, collections
from pathlib import Path
import duckdb
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
R = [json.loads(l) for l in open(HERE / 'clean6.jsonl', encoding='utf-8')]
W = collections.defaultdict(list)
for w in csv.DictReader(open(HERE / 'works6.csv', encoding='utf-8')):
    W[w['case']].append(w)
rng = random.Random(20261121)
by = collections.defaultdict(list)
for r in R:
    by[r['verdict']].append(r)
n = {'some-works-not-theirs': 30, 'two-people-one-key': 99, 'label-defect': 99, 'works-not-about-place': 15, 'sound': 15}
samp = []
for v, k in n.items():
    pool = sorted(by[v], key=lambda r: r['case'])
    samp += pool if k >= len(pool) else rng.sample(pool, k)
c = duckdb.connect(str(ROOT / 'build/graph/explorer.duckdb'), read_only=True)
c.execute("SET memory_limit='1GB'; SET threads=2")
out = open(HERE / 'audit-packet6.txt', 'w', encoding='utf-8')
for r in samp:
    p = r['person'] or {}
    out.write(f"\n## {r['case']} [{r['verdict']}/{r['confidence']}] {r['graph_label']} (queue {r['queue_label']}) rank {r['rank']} scholar={r['scholar_of_place']}\n")
    out.write(f"  anchors: {r['anchors'][:12]}\n  sol person: {p.get('name')} | {p.get('life_years')} | {p.get('field')} | {json.dumps(p.get('identifiers'), ensure_ascii=False)[:400]}\n")
    out.write(f"  reason: {r['reason']}\n")
    for e in (r['evidence'] or [])[:6]:
        out.write(f"   - {e.get('fact','')[:220]} <{e.get('url')}>\n")
    for w in W[r['case']]:
        if r['verdict'] in ('sound',) and w['theirs'] == 'yes' and w['about_place'] == 'yes':
            continue
        a = c.execute('SELECT anchors, kind, year FROM nodes WHERE key = ?', [w['work']]).fetchone()
        doi = [x for x in (a[0] or []) if x.startswith('doi:')][:1] if a else []
        out.write(f"   * {w['work']} {doi} [{a[1] if a else ''} {w['year']}] theirs={w['theirs']} about={w['about_place']} src={w['credit_source']} | {w['title'][:90]}\n       {w['why'][:300]}\n")
    if r['verdict'] == 'sound':
        out.write(f"   ({sum(1 for w in W[r['case']])} credits, all yes/yes shown omitted)\n")
json.dump([r['case'] for r in samp], open(HERE / 'audit-sample6.json', 'w'))
print(len(samp), collections.Counter(r['verdict'] for r in samp))
