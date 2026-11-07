"""Held LC authors x their one same-name twin: the twin's dissertation (AHA record or keyed thesis work) or
authored works against the author's LC books (held_books.py).
A: >= 3 shared words making >= 60% of the shorter title (whole titles), two of them outside common historical
   vocabulary; or the same main title, two or more words, both outside it; book from the year before the PhD on.
B (dissertation only): >= 2 shared distinctive words (outside common vocabulary, 4+ letters) making >= 40% of
   the shorter whole title, the book published from the year before the PhD to fifteen years after."""
import json, re, sys, unicodedata
sys.path.insert(0, 'scripts')
import duckdb
from collections import Counter, defaultdict
from identifiers import State, DEFAULT_DIR
from lc_canon_people import content
S = '/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
COMMON = {'social','political','thought','history','historical','study','studies','economic','american','america','united','states','new','movement','policy','life','century','england','english','british','great','britain','war','politics','culture','cultural','society','development','foreign','relations','early','modern','role','national','government','religion','religious','church','world','origins','rise','age','era','public','people','women','men','state','reform','law','labor','labour','trade','city','press','power','problem','problems','question','idea','ideas','theory','policies','growth','case','years','period','colonial','empire','imperial','revolution','revolutionary','international','europe','european','france','french','germany','german','russia','russian','china','chinese','japan','japanese','canada','canadian','making','north','university','introduction','essays','selected','papers','documents','volume','first','second','south','west','east','western','eastern','southern','northern','history','histories','perspectives','approach','analysis','community','communities','family','families','identity','nation','nationalism','race','gender','class','memory','experience','press','york'}
STOP = {'the','and','of','a','an','in','on','to','for','from','with','by','at','as','its','his','her','their','la','le','les','de','des','du','et','en','une','un','l','d','der','die','das','und','von','zur','zum','im','s','or','is','are','be','was','eds','ed','vol'}
def fold(x): return unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
def ws(t): return {w for w in re.findall(r'[a-z]+', fold(t)) if w not in STOP and len(w) > 1}
def main_eq(a, b):
    m1, m2 = {w for w in content(a) if not w.isdigit()}, {w for w in content(b) if not w.isdigit()}
    return len(m1) >= 2 and m1 == m2 and len(m1 - COMMON) >= 2
def rule_a(a, b):
    c, d = ws(a), ws(b); sh = c & d
    return (len(sh) >= 3 and len(sh) >= 0.6 * min(len(c), len(d)) and len(sh - COMMON) >= 2) or main_eq(a, b)
def rule_b(a, b):
    c, d = ws(a), ws(b); sh = c & d
    dist = {w for w in sh - COMMON if len(w) >= 4}
    return len(dist) >= 2 and len(sh) >= 0.4 * min(len(c), len(d))
state = State.load(DEFAULT_DIR)
held = json.load(open('data/identifiers/review-books-lc-2026-11-07c/held-people.json'))
books = json.load(open(S + 'held-books.json'))
aha = {}
for line in open('data/field-research/aha-dissertations-2026-10-13/records.jsonl'):
    r = json.loads(line); aha['aha-phd:' + r['id']] = (r['title'] or '', r['year'])
db = duckdb.connect(); db.execute('SET enable_progress_bar=false')
works = defaultdict(list)
for k, l, y, kind in db.execute("""select a."from", w.label, w.year, w.kind from 'build/graph/authored.parquet' a
        join 'build/graph/work.parquet' w on w.key = a."to" where not starts_with(w.label, 'Review')""").fetchall():
    works[k].append((l, y, kind))
def evaluate(k, bs):
    diss = [(aha[a][0], aha[a][1]) for a in state.keys[k]['anchors'] if a in aha and aha[a][0] and aha[a][0] != '[No title]']
    diss += [(l, y) for l, y, kind in works[k] if kind == 'thesis']
    other = [(l, y) for l, y, kind in works[k] if kind != 'thesis']
    hit = None
    for bt, by, _ in bs:
        for dt, dy in diss:
            if rule_a(dt, bt) and (not dy or not by or by >= dy - 1): return ('A_diss', dt, bt, dy, by)
            if rule_b(dt, bt) and dy and by and dy - 1 <= by <= dy + 15: hit = hit or ('B_diss', dt, bt, dy, by)
        for ot, oy in other:
            if rule_a(ot, bt): hit = hit or ('A_work', ot, bt, oy, by)
    return hit
res = Counter(); joins = []
for x in held:
    if x['lcnaf'] in state.anchor: res['now_keyed'] += 1; continue
    live = {k for t in x['twins'] for k in state.lookup(t)}
    live = {k for k in live if not any(a.startswith('lcnaf:') for a in state.keys[k]['anchors'])}
    if len(live) < 2: res['one_or_none_without_lcnaf'] += 1; continue
    bs = books.get(x['lcnaf'], [])
    if not bs: res['no_lc_books'] += 1; continue
    hits = {k: h for k in live if (h := evaluate(k, bs))}
    if len(hits) != 1: res[f'hits_{min(len(hits), 2)}'] += 1; continue
    k, hit = next(iter(hits.items()))
    res[hit[0]] += 1
    joins.append(dict(lcnaf=x['lcnaf'], label=x['label'], key=k, key_label=state.keys[k]['label'], rule=hit[0],
                      own=hit[1], book=hit[2], own_year=hit[3], book_year=hit[4], others=sorted(live - {k})))
print(dict(res))
json.dump(joins, open(S + 'twin_book_joins_c.json', 'w'), ensure_ascii=False)
import random; random.seed(9)
for r in ('A_diss', 'A_work', 'B_diss'):
    sel = [j for j in joins if j['rule'] == r]
    print('==', r, len(sel))
    for j in random.sample(sel, min(15, len(sel))):
        print(' ', j['label'][:28], '|', j['key_label'][:20], '|', j['own'][:55], j['own_year'], '||', j['book'][:55], j['book_year'])
