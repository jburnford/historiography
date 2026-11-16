"""Checks for key_thesis_round.py's proposals (2026-11-16): new theses that may be a thesis the graph already holds
(same family name, title words, years within two), pairs inside the round, and attached keys already authoring a thesis.
Writes duplicates.csv.gz and attached-key-theses.csv.gz into the round folder. Reads build/graph (key-log rows only)."""
import csv, gzip, json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path
import duckdb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_tables import keylog
from aha_links import title_words

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
OUT = Path(sys.argv[1])


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def family(name):
    n = fold(name)
    f = n.split(',')[0] if ',' in n else (n.split() or [''])[-1]
    return re.sub(r'[^a-z]', '', f)


target = {}
for f in OUT.glob('01-works-*.json'):
    for op in json.load(open(f))['ops']:
        if op['event'] == 'attach':
            for a in op['anchors']:
                if a.startswith('diss-thesis:'):
                    target[a[12:]] = op['key']
rows = list(csv.DictReader(gzip.open(OUT / 'author-decisions.csv.gz', 'rt', encoding='utf-8')))
titles = {r['id']: r for r in csv.DictReader(open(ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv', encoding='utf-8'))}
db = duckdb.connect()
th = db.execute(f"""SELECT w.key, w.label, w.year, list(p.label), list(p.key), w.anchors FROM '{G}/work.parquet' w
    LEFT JOIN {keylog(G, 'authored')} a ON a."to" = w.key LEFT JOIN '{G}/person.parquet' p ON p.key = a."from"
    WHERE w.kind = 'thesis' GROUP BY ALL""").fetchall()
by_fam = defaultdict(list)
for wk, label, year, plabels, pkeys, anchors in th:
    for pl in set(x for x in plabels if x):
        by_fam[family(pl)].append((wk, label or '', year, pl, anchors or []))
dups = []
new_by_fam = defaultdict(list)
for r in rows:
    t = titles[r['thesis_id']]
    new_by_fam[family(t['author'])].append(t)
for r in rows:
    t = titles[r['thesis_id']]
    w = title_words(t['title'])
    y = int(t['year']) if t['year'].isdigit() else None
    for wk, label, wy, pl, anchors in by_fam.get(family(t['author']), ()):
        if wk == target.get(t['id']):
            continue
        w2 = title_words(label)
        if not w or not w2:
            continue
        sh = len(w & w2)
        if sh >= 2 and sh >= 0.8 * min(len(w), len(w2)) and (y is None or wy is None or abs(y - wy) <= 2):
            dups.append(dict(thesis_id=t['id'], outcome=r['outcome'], author=t['author'], year=t['year'], title=t['title'][:200],
                             existing_work=wk, existing_label=label[:200], existing_year=wy, existing_author=pl,
                             existing_anchors=';'.join(a for a in anchors if a.startswith(('diss-thesis:', 'aha-diss:')))[:300], scope='graph'))
    for o in new_by_fam.get(family(t['author']), ()):
        if o['id'] <= t['id']:
            continue
        w2 = title_words(o['title'])
        sh = len(w & w2)
        if w and w2 and sh >= 2 and sh >= 0.8 * min(len(w), len(w2)):
            dups.append(dict(thesis_id=t['id'], outcome=r['outcome'], author=t['author'], year=t['year'], title=t['title'][:200],
                             existing_work='new:' + o['id'], existing_label=o['title'][:200], existing_year=o['year'],
                             existing_author=o['author'], existing_anchors='', scope='round'))
with gzip.open(OUT / 'duplicates.csv.gz', 'wt', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(dups[0]) if dups else ['thesis_id'])
    w.writeheader(); w.writerows(dups)
att = [r for r in rows if r['outcome'] == 'attach']
keys = {r['key'] for r in att if r['key']}
db.execute('CREATE TABLE k(x VARCHAR)'); db.executemany('INSERT INTO k VALUES (?)', [(x,) for x in keys])
has = defaultdict(list)
for pk, wk, label, year, anchors in db.execute(f"""SELECT a."from", w.key, w.label, w.year, w.anchors FROM {keylog(G, 'authored')} a
        JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'thesis' AND a."from" IN (SELECT x FROM k)""").fetchall():
    has[pk].append((wk, label, year, anchors))
out = []
for r in att:
    for wk, label, year, anchors in has.get(r['key'], ()):
        if any(a == f"diss-thesis:{r['thesis_id']}" for a in anchors) or wk == target.get(r['thesis_id']):
            continue
        out.append(dict(thesis_id=r['thesis_id'], key=r['key'], route=r['route'][:80], new_title=titles[r['thesis_id']]['title'][:150],
                        new_year=titles[r['thesis_id']]['year'], held_work=wk, held_title=(label or '')[:150], held_year=year,
                        held_anchors=';'.join(a for a in anchors if a.startswith(('diss-thesis:', 'aha-diss:')))))
with gzip.open(OUT / 'attached-key-theses.csv.gz', 'wt', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ['thesis_id'])
    w.writeheader(); w.writerows(out)
from collections import Counter
print(json.dumps(dict(duplicates=Counter((d['scope'], d['outcome']) for d in dups).most_common(),
                      dup_theses=len({d['thesis_id'] for d in dups}),
                      attached_keys_with_other_thesis=len({o['thesis_id'] for o in out})), default=str))
