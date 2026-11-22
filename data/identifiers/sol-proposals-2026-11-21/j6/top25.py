"""Top-25 people on the Sri Lanka (Q854) and Canada (Q16) place pages, now and after the job-6 corrections.

Mirrors graph_explorer.py place_group('people'): pw rows for the place (with the places within it, as the job-6 queue
did: children=1), fiction settings left out, authored edges whose role is not an edition role; people ranked by the number
of distinct works. 'After' removes the credits in 06a (demote) and 06b (withdraw), the work tags in
data/graph/places/tag-removals.csv, and (shown separately) the role-review credits of 06c whose role the explorer leaves
out (translator, foreword/introduction, edition of primary texts). Read-only on build/graph/explorer.duckdb.

    python3 data/identifiers/sol-proposals-2026-11-21/j6/top25.py > j6/top25.md
"""
import csv, json, sys
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = HERE.parents[3]
EDITION_ROLES = ('edition-editor', 'translator', 'introducer', 'series-editor', 'contributor')
c = duckdb.connect(str(ROOT / 'build/graph/explorer.duckdb'), read_only=True)
c.execute("SET memory_limit='1GB'; SET threads=2")
drop = {(r['person'], r['work']) for f in ('06a-place-people-credits.csv', '06b-place-people-withdraw.csv')
        for r in csv.DictReader(open(OUT / f, encoding='utf-8'))}
# corrections already proposed elsewhere and not yet applied: the Morgan file (place-demo-fixes-2026-11-18) and 03 (its
# person column holds names, so rows are matched through the key label)
drop |= {(r['person'], r['work']) for r in csv.DictReader(open(ROOT / 'data/identifiers/place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv', encoding='utf-8'))}
_by_label = {}
for k, l in c.execute("SELECT key, label FROM nodes WHERE type = 'person'").fetchall():
    _by_label.setdefault(l, []).append(k)
for r in csv.DictReader(open(OUT / '03-mixed-profile-credits.csv', encoding='utf-8')):
    for k in _by_label.get(r['person'], [])[:1] if len(_by_label.get(r['person'], [])) == 1 else []:
        drop.add((k, r['work']))
role_out = {(r['person'], r['work']) for r in csv.DictReader(open(OUT / '06c-place-people-role-review.csv', encoding='utf-8'))
            if not r['cause'].startswith('role: editor')}
tagrm = {(r['work'], 'place:' + r['qid']) for r in csv.DictReader(open(ROOT / 'data/graph/places/tag-removals.csv', encoding='utf-8'))}
sol = {}
for line in open(ROOT / 'data/identifiers/sol-review-2026-11-19/6-place-people/verdicts.jsonl', encoding='utf-8'):
    d = json.loads(line)
    sol[d.get('supersedes') or d['case']] = d


def ranking(place, after, roles=False):
    rows = c.execute(f"""SELECT au."from", x.work, x.place FROM pw x JOIN e_authored_t au ON au."to" = x.work
                         WHERE x.place = $k AND NOT x.fiction AND coalesce(au.role, 'author') NOT IN {EDITION_ROLES}""",
                     dict(k=place)).fetchall()
    # pw has one row per (place page, work); the tag removals act on the work's own tags, so a work drops from the page
    # only when every tag that put it there is removed
    tags = {}
    if after:
        for w, to in c.execute(f"""SELECT a."from", a."to" FROM e_about_place_t a WHERE a."from" IN (SELECT DISTINCT work FROM pw WHERE place = $k)
                                   AND (a."to" = $k OR a."to" IN (SELECT des FROM place_desc WHERE anc = $k)
                                        OR a."to" IN (SELECT period FROM place_period WHERE territory = $k))""", dict(k=place)).fetchall():
            tags.setdefault(w, set()).add(to)
    n = {}
    for p, w, _ in rows:
        if after:
            if (p, w) in drop or (roles and (p, w) in role_out):
                continue
            if w in tags and all((w, t) in tagrm for t in tags[w]):
                continue
        n.setdefault(p, set()).add(w)
    lab = dict(c.execute('SELECT key, label FROM nodes WHERE key IN (SELECT unnest($p))', dict(p=list(n))).fetchall())
    wt = dict(c.execute('SELECT key, weight FROM nodes WHERE key IN (SELECT unnest($p))', dict(p=list(n))).fetchall())
    return [(p, lab.get(p), len(ws)) for p, ws in sorted(n.items(), key=lambda kv: (-len(kv[1]), -(wt.get(kv[0]) or 0), kv[0]))]


for place, q in (('place:Q854', 'Q854'), ('place:Q16', 'Q16')):
    now, aft, aft2 = ranking(place, False), ranking(place, True), ranking(place, True, roles=True)
    rank_now = {p: i + 1 for i, (p, _, _) in enumerate(now)}
    n_now = {p: k for p, _, k in now}
    n_aft2 = {p: k for p, _, k in aft2}
    print(f'\n### {q}: top 25 after the corrections (works now -> after; rank now)\n')
    print('| rank | person | key | works now | after | + role review | rank now | Sol: scholar of place | Sol verdict |')
    print('| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |')
    for i, (p, l, k) in enumerate(aft[:25], 1):
        s = sol.get(p if q == 'Q854' else f'Q16/{p}', {})
        print(f"| {i} | {l} | {p} | {n_now.get(p, 0)} | {k} | {n_aft2.get(p, 0)} | {rank_now.get(p, '-')} | {s.get('scholar_of_place', 'not queued')} | {s.get('verdict', '')} |")
    gone = [(p, l, k) for p, l, k in now[:25] if p not in {x[0] for x in aft[:25]}]
    if gone:
        print('\nLeave the top 25: ' + '; '.join(f"{l} ({p}, {k} -> {dict((a, b) for a, _, b in aft).get(p, 0)})" for p, l, k in gone))
