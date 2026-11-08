"""Rules that settle held LC authors before outside review (2026-11-08; user: "reduce the number of checks Sol needs
to do with better rules based on looking at the first Sol results"). Items are the held LC authors exported for Sol
(data/identifiers/held-lc-authors-sol-2026-11-07/entries.json: an LC authority, its LC books, and the same-name keys
it was held against). Each candidate key is judged on its own:

A candidate is OUT (the LC authority is recorded as `rejected:lcnaf:<id>` on it) when
- identifiers: the key's Wikidata item carries another LC authority, or the LC author's Wikidata item (P244) has an
  ORCID and the key holds a different one;
- dates: the LC author's birth year (LC heading, else Wikidata at year precision) puts the key's PhD before age 20 or
  after 75, or the LC author died before it;
- given names: both sides give a full first name and they plainly differ (not a prefix, initial, common nickname or
  spelling variant: Zach/Zachary, Bill/William, C. Richard/Richard and Marie/Mary pass);
- an early book: LC's earliest book (after 1905) is more than 15 years before the PhD, and no LC book title shares
  three or more words with the dissertation (Oblinger published his before a late PhD).
A candidate is the SAME person when
- identifiers: the LC author's Wikidata item is the key's, or shares its ORCID or VIAF id;
- works: an LC book is the key's dissertation published, i.e. it appears from one year before to fifteen years after
  the PhD and the titles share three or more content words (stemmed, over 40% of the shorter title), or two words
  that are each rare among the dissertation titles held (25 or fewer): "The Right of Petition in 18th-Century
  Virginia" (1976) and "Popular influence upon public policy: petitioning in eighteenth-century Virginia" (1979).
An item is settled `same` when exactly one candidate is the same and every other is out (an identifier match settles
it whatever the others), and `none` when every candidate is out. Other items go to Sol with the out candidates
removed (entries-for-sol.json, single-candidate items first; items with nine or more candidates left are set aside).

Checked against Sol's first 767 verdicts: the rules settle 179 of the 595 with a definite verdict and agree on all
179 (145 none, 34 same); on 8 of Sol's 'unclear' items they settle 7 none and 1 same (dissertation published).

    python3 scripts/held_lc_rules.py [--fetch]          # --fetch refreshes the Wikidata cache (QLever)
"""
import argparse, collections, glob, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/identifiers/held-lc-authors-sol-2026-11-07'
OUT = D / 'rules-2026-11-08'
STOP = set('the a an of and in on to for with from at by its his her their de la le les des du et el los las y di il '
           'della der die und von zur im au en'.split())
GENERIC = set('new histo study studi polit socia ameri centu ninet eight seven twent sixte early moder life works unite '
              'state natio engli briti frenc europ world some aspec case role perio years betwe durin under towar throu '
              'other first great chang devel'.split())
NUM = {'15th': 'fifteenth', '16th': 'sixteenth', '17th': 'seventeenth', '18th': 'eighteenth', '19th': 'nineteenth',
       '20th': 'twentieth'}
NICK = {'bill': 'william', 'will': 'william', 'bob': 'robert', 'rob': 'robert', 'bobby': 'robert', 'jim': 'james',
        'jimmy': 'james', 'tom': 'thomas', 'dick': 'richard', 'rick': 'richard', 'ted': 'edward', 'ed': 'edward',
        'ned': 'edward', 'jack': 'john', 'peggy': 'margaret', 'meg': 'margaret', 'betsy': 'elizabeth',
        'beth': 'elizabeth', 'liz': 'elizabeth', 'betty': 'elizabeth', 'kate': 'katherine', 'kathy': 'katherine',
        'sue': 'susan', 'chuck': 'charles', 'charlie': 'charles', 'hank': 'henry', 'harry': 'henry',
        'larry': 'lawrence', 'pat': 'patricia', 'patty': 'patricia', 'sandy': 'sandra', 'tony': 'anthony',
        'steve': 'stephen', 'mike': 'michael', 'dave': 'david', 'dan': 'daniel', 'joe': 'joseph', 'ben': 'benjamin',
        'sam': 'samuel', 'fred': 'frederick', 'al': 'albert', 'andy': 'andrew', 'nick': 'nicholas',
        'chris': 'christopher', 'jerry': 'gerald', 'jeff': 'jeffrey', 'greg': 'gregory', 'ken': 'kenneth',
        'ron': 'ronald', 'don': 'donald', 'doug': 'douglas', 'gene': 'eugene', 'walt': 'walter', 'matt': 'matthew',
        'tim': 'timothy', 'jenny': 'jennifer', 'jen': 'jennifer', 'debbie': 'deborah', 'deb': 'deborah',
        'cathy': 'catherine', 'molly': 'mary', 'polly': 'mary', 'sally': 'sarah'}


def norm(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def stems(s):
    s = norm(s)
    for a, b in NUM.items():
        s = s.replace(a, b)
    return {w[:5] for w in re.findall(r'[a-z]{3,}', s) if w not in STOP} - GENERIC


def year(y):
    y = str(y or '')[:4]
    return int(y) if y.isdigit() else None


def given(label):
    p = norm(label).split(',')
    return p[1].strip() if len(p) > 1 else ''


def name_conflict(lcg, cg):
    def split(g):
        w = [t for t in re.split(r'[\s.\-()0-9]+', g) if t]
        return w, next((t for t in w if len(t) > 1), None)
    lw, lf = split(lcg); cw, cf = split(cg)
    if not lw or not cw:
        return False
    if not lf or not cf:      # initials only on one side: conflict only if no initial matches anywhere
        a, b = lw[0][0], cw[0][0]
        return not (a == b or any(t[0] == b for t in lw) or any(t[0] == a for t in cw))
    if any(cf == t or t.startswith(cf) or cf.startswith(t) or NICK.get(cf) == t or NICK.get(t) == cf
           or (cf[:3] == t[:3] and len(set(cf) ^ set(t)) <= 3) for t in lw if len(t) > 1):   # Marie/Mary, Anni/Anne
        return False
    return not (len(lw[0]) == 1 and cf[0] == lw[0])


def qlever(q):
    for t in range(6):
        try:
            req = urllib.request.Request('https://qlever.dev/api/wikidata', data=urllib.parse.urlencode({'query': q}).encode(),
                                         headers={'Accept': 'application/sparql-results+json',
                                                  'User-Agent': 'historiography-kg/1.0 (research)'})
            return json.load(urllib.request.urlopen(req, timeout=120))['results']['bindings']
        except Exception as e:
            print('retry', e, file=sys.stderr); time.sleep(10 * (t + 1))
    raise SystemExit('QLever failed')


def fetch_wikidata(items):
    P = ('PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> '
         'PREFIX wikibase: <http://wikiba.se/ontology#> PREFIX p: <http://www.wikidata.org/prop/> '
         'PREFIX psv: <http://www.wikidata.org/prop/statement/value/> ')
    lcids = sorted({x['item'][6:] for x in items})
    qids = sorted({a[3:] for x in items for c in x['candidates'] for a in c['anchors'] if a.startswith('wd:')})
    lc2wd, wd2lc, life = {}, {}, {}
    for i in range(0, len(lcids), 400):
        vs = ' '.join(f'"{l}"' for l in lcids[i:i + 400])
        for b in qlever(P + 'SELECT ?lc ?item ?orcid ?viaf WHERE { VALUES ?lc {%s} ?item wdt:P244 ?lc . '
                        'OPTIONAL{?item wdt:P496 ?orcid} OPTIONAL{?item wdt:P214 ?viaf} }' % vs):
            d = lc2wd.setdefault(b['lc']['value'], {'qid': [], 'orcid': [], 'viaf': []})
            for f, k in (('item', 'qid'), ('orcid', 'orcid'), ('viaf', 'viaf')):
                if f in b:
                    v = b[f]['value'].rsplit('/', 1)[-1]
                    if v not in d[k]:
                        d[k].append(v)
    for i in range(0, len(qids), 400):
        vs = ' '.join(f'wd:{q}' for q in qids[i:i + 400])
        for b in qlever(P + 'SELECT ?item ?lc WHERE { VALUES ?item {%s} ?item wdt:P244 ?lc }' % vs):
            wd2lc.setdefault(b['item']['value'].rsplit('/', 1)[1], []).append(b['lc']['value'])
    qs = sorted({q for d in lc2wd.values() for q in d['qid']})
    for i in range(0, len(qs), 400):
        vs = ' '.join(f'wd:{q}' for q in qs[i:i + 400])
        for b in qlever(P + 'SELECT ?item ?pp ?t WHERE { VALUES ?item {%s} VALUES ?pp {p:P569 p:P570} ?item ?pp ?st . '
                        '?st psv:P569|psv:P570 ?v . ?v wikibase:timeValue ?t ; wikibase:timePrecision ?pr . '
                        'FILTER(?pr >= 9) }' % vs):
            t = b['t']['value']
            if not t.startswith('-'):
                life.setdefault(b['item']['value'].rsplit('/', 1)[1], {})['b' if b['pp']['value'].endswith('P569') else 'd'] = int(t[:4])
    return dict(fetched=time.strftime('%Y-%m-%d'), source='Wikidata via QLever: P244, P496, P214, P569/P570 at year precision',
                lc2wd=lc2wd, wd2lc=wd2lc, life=life)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--check', action='store_true', help='score the rules on the items Sol has judged; write nothing')
    args = ap.parse_args()
    items = json.load(open(D / 'entries.json'))
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / 'wikidata.json'
    if args.fetch or not cache.exists():
        json.dump(fetch_wikidata(items), open(cache, 'w'), ensure_ascii=False, indent=0)
    W = json.load(open(cache))
    sol = {}
    for f in glob.glob(str(D / '*verdicts*.jsonl')):
        for l in open(f):
            v = json.loads(l); sol[v['item']] = v
    df = collections.Counter()
    for t in {a['title'] for x in items for c in x['candidates'] for a in c['aha_dissertations']}:
        df.update(stems(t))

    def lc_dates(x):
        lab = x['lc'].get('label', '')
        m = re.search(r'(\d{4})\??-(\d{4})?', lab)
        b = year(x['lc'].get('birth')) or (int(m.group(1)) if m else None)
        d = year(x['lc'].get('death')) or (int(m.group(2)) if m and m.group(2) else None)
        for q in W['lc2wd'].get(x['item'][6:], {}).get('qid', []):
            b = b or W['life'].get(q, {}).get('b'); d = d or W['life'].get(q, {}).get('d')
        return b, d

    def title_match(x, c, lo=-1, hi=15, need3=False):
        for t, ty in [(a['title'], a['year']) for a in c['aha_dissertations']] + [(w[0], w[1]) for w in c['works'] if w[2] == 'thesis']:
            tt = stems(t)
            for bt, by in x['lc_books']:
                bb = stems(bt); sh = tt & bb; by = year(by)
                if not (tt and bb and ty and by and lo <= by - ty <= hi):
                    continue
                if need3 and len(sh) >= 3:
                    return bt, by, t, ty
                if not need3 and len(sh) >= 2 and len(sh) / min(len(tt), len(bb)) >= 0.4 and (len(sh) >= 3 or max(df[s] for s in sh) <= 25):
                    return bt, by, t, ty
        return None

    def judge(x, c):
        lcid = x['item'][6:]; an = set(c['anchors']); w = W['lc2wd'].get(lcid, {})
        lcwd = 'Wikidata ' + '/'.join(w.get('qid', []))
        if any('wd:' + q in an for q in w.get('qid', [])):
            return 'same', f'LC {lcid} is on the key\'s Wikidata item ({lcwd}, P244)', 'identifier'
        if any('orcid:' + o in an for o in w.get('orcid', [])):
            return 'same', f'the LC author\'s {lcwd} (P244 {lcid}) has the key\'s ORCID', 'identifier'
        if any('viaf:' + v in an for v in w.get('viaf', [])):
            return 'same', f'the LC author\'s {lcwd} (P244 {lcid}) has the key\'s VIAF id', 'identifier'
        for a in an:
            if a.startswith('wd:') and W['wd2lc'].get(a[3:]) and lcid not in W['wd2lc'][a[3:]]:
                return 'none', f'the key\'s Wikidata item {a[3:]} carries another LC authority ({", ".join(W["wd2lc"][a[3:]])})', 'identifier'
        if w.get('orcid') and any(a.startswith('orcid:') for a in an):
            return 'none', f'the LC author\'s {lcwd} has ORCID {", ".join(w["orcid"])}; the key holds another', 'identifier'
        b, d = lc_dates(x)
        phds = [a['year'] for a in c['aha_dissertations'] if a.get('year')] + [y for _, y, k in c['works'] if k == 'thesis' and y]
        phd = min(phds) if phds else None
        if b and phd and not 20 <= phd - b <= 75:
            return 'none', f'LC author born {b}; the key\'s PhD is {phd} (age {phd - b})', 'dates'
        if d and phd and d < phd:
            return 'none', f'LC author died {d}, before the key\'s PhD ({phd})', 'dates'
        if name_conflict(given(x['lc']['label']), given(c['label'])):
            return 'none', f'given names differ: LC "{x["lc"]["label"]}", key "{c["label"]}"', 'names'
        s = title_match(x, c)
        if s:
            return 'same', 'LC book "%s" (%s) is the dissertation "%s" (%s) published' % (s[0][:150], s[1], s[2][:150], s[3]), 'works'
        if title_match(x, c, -200, 200, need3=True):
            return None, None, None
        by = sorted(y for y in (year(y) for _, y in x['lc_books']) if y and y > 1905)
        if phd and by and by[0] < phd - 15:
            return 'none', f'LC\'s earliest book is {by[0]}, {phd - by[0]} years before the key\'s PhD ({phd})', 'dates'
        return None, None, None

    if args.check:
        tab, bad = collections.Counter(), []
        for x in items:
            v = sol.get(x['item'])
            if not v:
                continue
            js = [(c, *judge(x, c)) for c in x['candidates']]
            same = [j for j in js if j[1] == 'same']; live = [j for j in js if j[1] != 'none']
            r = ('same', same[0][0]['key']) if len(same) == 1 and (len(live) == 1 or same[0][3] == 'identifier') else ('none', None) if not live else (None, None)
            tab[f"rule {r[0]} / Sol {v['verdict']} {v.get('confidence')}"] += 1
            if r[0] and v['verdict'] != 'unclear' and (r[0] != v['verdict'] or (r[0] == 'same' and r[1] != v['key'])):
                bad.append((x['lc']['label'], r, v['verdict'], v.get('key')))
        print(json.dumps(dict(sorted(tab.items())), indent=1)); print('disagreements', bad)
        return
    state = State.load(DEFAULT_DIR); blocked = blocked_keys(state)
    ops, decisions, for_sol, setaside = [], [], [], []
    res = collections.Counter()
    for x in items:
        if x['item'] in sol:
            res['sol_already'] += 1; continue
        if x['item'] in state.anchor:
            res['already_keyed'] += 1; continue
        js = [(c, *judge(x, c)) for c in x['candidates']]
        same = [j for j in js if j[1] == 'same']; live = [j for j in js if j[1] != 'none']
        verdict = None
        if len(same) == 1 and (len(live) == 1 or same[0][3] == 'identifier'):
            verdict = 'same'
        elif not live:
            verdict = 'none'
        decisions.append(dict(item=x['item'], lc=x['lc']['label'], verdict=verdict,
                              candidates=[dict(key=c['key'], label=c['label'], judged=v, rule=r, why=why) for c, v, why, r in js]))
        lc_url = f'https://id.loc.gov/authorities/names/{x["item"][6:]}'
        if verdict == 'same':
            c, _, why, rule = same[0]
            k = (state.lookup(c['key']) or [None])[0]
            if not k or k in blocked or any(a.startswith('lcnaf:') for a in state.keys[k]['anchors']):
                res['same_guard_or_has_lc'] += 1; for_sol.append(x); continue
            ops.append(dict(event='attach', key=k, anchors=[x['item']], aliases=[], members=[],
                            basis=f'held LC author settled by rule ({rule}): {why}. Other candidates ruled out on dates, '
                                  f'names or identifiers. {lc_url}'[:900]))
            res[f'same_{rule}'] += 1
        # rejections: every candidate ruled out (whether or not the item is settled)
        for c, v, why, rule in js:
            if v == 'none':
                for k in state.lookup(c['key']):
                    ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f'rejected:lcnaf:{x["item"][6:]}'],
                                    basis=f'held LC author ruled out by rule ({rule}): {why}. {lc_url}'[:900]))
                res[f'candidate_out_{rule}'] += 1
        if verdict == 'none':
            res['none'] += 1
        elif verdict is None:
            rest = dict(x, candidates=[c for c, v, _, _ in js if v != 'none'])
            (setaside if len(rest['candidates']) >= 9 else for_sol).append(rest)
    for_sol.sort(key=lambda x: (len(x['candidates']), -len(x['lc_books'])))
    json.dump(dict(basis='held LC authors: rules from the first 767 Sol verdicts (scripts/held_lc_rules.py)',
                   decided_by='rule', ops=ops), open(OUT / 'proposal.json', 'w'), ensure_ascii=False, indent=0)
    with open(OUT / 'decisions.jsonl', 'w') as fh:
        for d in decisions:
            fh.write(json.dumps(d, ensure_ascii=False) + '\n')
    json.dump(for_sol, open(OUT / 'entries-for-sol.json', 'w'), ensure_ascii=False)
    json.dump(setaside, open(OUT / 'set-aside-9plus-candidates.json', 'w'), ensure_ascii=False)
    res.update(for_sol=len(for_sol), set_aside=len(setaside), ops=len(ops),
               sol_candidates=sum(len(x['candidates']) for x in for_sol))
    print(json.dumps(dict(res), indent=1))


if __name__ == '__main__':
    main()
