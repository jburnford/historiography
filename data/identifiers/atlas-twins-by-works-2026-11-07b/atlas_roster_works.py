"""Atlas people x same-name twins, second pass (2026-11-07): the atlas's own attribution of works.
Each atlas node lists representative_people (person_id, works, source_ids) and strands (person_ids, works,
source_ids); the cited sources there are the person's own work. A pair joins when the partner already authored or
edited that work (same key via atlas:source lookup) or a work whose title agrees with the citation's title
(>= 3 shared content words making >= 60% of the shorter title, two of them outside common historical vocabulary)
and whose year is within one of the citation's year. Only sources whose citation names the person's family name
before the title are used. PID conflicts (different wd/lcnaf/orcid/...) are skipped."""
import json, sys, re, unicodedata
sys.path.insert(0, 'scripts'); sys.path.insert(0, 'data/identifiers/aha-phd-by-works-2026-11-07')
import duckdb
from collections import Counter, defaultdict
from identifiers import State, DEFAULT_DIR
from lc_canon_people import content
S = '/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
COMMON = {'social','political','thought','history','historical','study','studies','economic','american','america','united','states','new','movement','policy','life','century','england','english','british','great','britain','war','politics','culture','cultural','society','development','foreign','relations','early','modern','role','national','government','religion','religious','church','world','origins','rise','age','era','public','people','women','men','state','reform','law','labor','labour','trade','city','press','power','problem','problems','question','idea','ideas','theory','policies','growth','case','years','period','colonial','empire','imperial','revolution','revolutionary','international','europe','european','france','french','germany','german','russia','russian','china','chinese','japan','japanese','canada','canadian','making','north','press','university'}
STOP = {'the','and','of','a','an','in','on','to','for','from','with','by','at','as','its','his','her','their','la','le','les','de','des','du','et','en','une','un','l','d','der','die','das','und','von','zur','zum','im','s','or','is','are','be','was','eds','ed','vol'}
def cw(t):
    t = fold(re.split(r'\s\(|\(', t or '')[0])
    return {w for w in re.findall(r"[a-z]+", t) if w not in STOP and len(w) > 1}
def agree(a, b, ya=None, yb=None):
    c, d = cw(a), cw(b)
    sh = c & d
    if len(sh - COMMON) >= 2 and len(sh) >= 3 and len(sh) >= 0.6 * min(len(c), len(d)): return True
    m1, m2 = {w for w in content(a) if not w.isdigit()}, {w for w in content(b) if not w.isdigit()}
    return bool(ya and yb and abs(ya - yb) <= 1 and m1 == m2 and len(m1 - COMMON) >= 2)
def fold(x): return unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
pairs = json.load(open(S + 'atlas_pairs.json'))
g = json.load(open('docs/data/graph.json'))
src = {s['id']: (s.get('citation') or s.get('title') or '') for s in g['sources']}
pid_of_atlas = {p['id']: p['label'] for p in g['people']}
own = defaultdict(set)
for n in g['nodes']:
    for r in n.get('representative_people') or []:
        for sid in r.get('source_ids') or []: own[r['person_id']].add(sid)
    for s in n.get('strands') or []:
        if len(s.get('person_ids') or []) == 1:
            for sid in s.get('source_ids') or []: own[s['person_ids'][0]].add(sid)
state = State.load(DEFAULT_DIR)
db = duckdb.connect(); db.execute('SET enable_progress_bar=false')
P = {k: a for k, a in db.execute("select key, anchors from 'build/graph/person.parquet'").fetchall()}
auth = defaultdict(set)
for f, t in db.execute("""select "from","to" from 'build/graph/authored.parquet' union select "from","to" from 'build/graph/edited.parquet'""").fetchall(): auth[f].add(t)
W = {k: (l, y) for k, l, y in db.execute("select key, label, year from 'build/graph/work.parquet'").fetchall()}
def cit_title(c, family):
    f = fold(c); i = f.find(family)
    if i < 0 or i > 60: return None
    rest = c[i + len(family):]
    rest = re.sub(r'^[^A-Za-zÀ-ɏ]*([A-Z][a-z]+\.?\s*)*[,.]\s*', '', rest) if rest[:2] in (', ',) else rest.lstrip(', ')
    m = re.search(r'\((?:[^()]*?)(1[89]\d\d|20\d\d)\)|(1[89]\d\d|20\d\d)', c)
    yr = int(m.group(1) or m.group(2)) if m else None
    return rest[:160], yr
res = Counter(); joins = []; by_atlas = defaultdict(list)
for p in pairs:
    if p['pid_conflict']: res['pid_conflict'] += 1; continue
    aid = next(x.split(':', 2)[2] for x in P[p['atlas']] if x.startswith('atlas:person:'))
    fam = fold(p['label']).split()[-1]
    sids = own.get(aid, set())
    if not sids: res['no_roster_source'] += 1; continue
    pw = auth.get(p['partner'], set())
    hit = None
    for sid in sorted(sids):
        ct = cit_title(src.get(sid, ''), fam)
        if not ct: continue
        keyed = set(state.lookup('atlas:source:' + sid))
        if keyed & pw: hit = ('shared', sid, W[next(iter(keyed & pw))][0][:60]); break
        t, yr = ct
        for w in pw:
            wl, wy = W.get(w, ('', None))
            if wl.startswith('Review of'): continue
            if agree(t, wl, yr, wy) and (not yr or not wy or abs(yr - wy) <= 1 or wy > yr):
                hit = ('title', sid, wl[:60], t[:60]); break
        if hit: break
    res[hit[0] if hit else 'no_match'] += 1
    if hit: by_atlas[p['atlas']].append((p['partner'], p['plabel'], hit))
print(dict(res), len(by_atlas))
for a, v in list(by_atlas.items()):
    for x in v: joins.append((a, x[0], x[1], x[2]))
json.dump(joins, open(S + 'atlas_roster_joins.json', 'w'))
import random; random.seed(2)
for j in random.sample(joins, min(30, len(joins))): print(j)
