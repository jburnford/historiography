"""Held LC authors (scripts/export_held_lc_authors.py items) settled by the earlier title rules before outside review:
the LC author's books vs each candidate key's dissertation (AHA) or works. Exactly one candidate must match.
Rules as review-books-lc-twins-2026-11-07c/twin_books_probe.py (A: agreeing titles; B: two distinctive shared title
words with the book within fifteen years of the PhD)."""
import json, re, sys, unicodedata
sys.path.insert(0, 'scripts')
from collections import Counter
from lc_canon_people import content
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys
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

items = [json.loads(l) for l in open(sys.argv[1])]
state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
def yr(v):
    m = re.match(r'(\d{4})', str(v or '')); return int(m.group(1)) if m else None
def evaluate(c, books):
    diss = [(d['title'], d['year']) for d in c['aha_dissertations'] if d['title'] and d['title'] != '[No title]']
    diss += [(t, y) for t, y, k in c['works'] if k == 'thesis']
    other = [(t, y) for t, y, k in c['works'] if k != 'thesis']
    hit = None
    for bt, by in books:
        by = yr(by)
        for dt, dy in diss:
            if rule_a(dt, bt) and (not dy or not by or by >= dy - 1): return ('A_diss', dt, bt, dy, by)
            if rule_b(dt, bt) and dy and by and dy - 1 <= by <= dy + 15: hit = hit or ('B_diss', dt, bt, dy, by)
        for ot, oy in other:
            if rule_a(ot, bt): hit = hit or ('A_work', ot, bt, oy, by)
    return hit
res, ops, rest = Counter(), [], []
WHY = {'A_diss': 'is its dissertation as published (titles agree)', 'B_diss': 'is its dissertation as published (two or more distinctive title words shared, the book within fifteen years of the PhD)', 'A_work': 'is a work this key holds by another route (titles agree)'}
for it in items:
    books = [(t, y) for t, y in it['lc_books']] + [(s.split(',')[0].split(':')[0], (re.findall(r'\d{4}', s) or [None])[0]) for s in it['lc']['sources'] if re.search(r'\d{4}', s)]
    hits = {c['key']: h for c in it['candidates'] if (h := evaluate(c, books))}
    if len(hits) == 1:
        k, h = next(iter(hits.items()))
        if k in blocked or any(a.startswith('lcnaf:') for a in state.keys[k]['anchors']):
            res['held_guard_or_has_lc'] += 1; rest.append(it); continue
        res[h[0]] += 1
        ops.append(dict(event='attach', key=k, anchors=[it['item']], aliases=[], members=[],
                        basis=f"LC authority {it['item']} ({it['lc']['label']}): its book '{h[2][:80]}' ({h[4]}) {WHY[h[0]]}: '{h[1][:80]}' ({h[3]}); identity by works"))
    else:
        res[f'hits_{min(len(hits), 2)}'] += 1; rest.append(it)
print(dict(res))
json.dump(dict(basis='held LC authors joined to the one candidate key whose dissertation or work their LC book is', decided_by='rule', ops=ops),
          open('data/identifiers/held-lc-authors-by-books-2026-11-07/proposal.json', 'w'), ensure_ascii=False, indent=0)
with open(sys.argv[3], 'w') as f:
    for it in rest: f.write(json.dumps(it, ensure_ascii=False) + '\n')
import random; random.seed(5)
for o in random.sample(ops, min(15, len(ops))): print(o['basis'][:220])
