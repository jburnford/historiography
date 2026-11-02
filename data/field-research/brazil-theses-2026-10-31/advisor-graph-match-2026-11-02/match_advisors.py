"""Name-only match of the advisors of the 2,718 Brazilian theses with PDFs against the dissertation
citation graph (cited-people.csv) and the key log (person mints/relabels), 2026-11-02. Rule: same last
surname, same first given name (or initial), other names of the shorter form found in the longer;
initial-only cited forms excluded. Leads, not identities. Run from the repository root."""
import sys, csv, json, glob, collections as C
sys.path.insert(0, 'scripts')
import dissertation_ingest as ing
fold = ing.fold
csv.field_size_limit(10**9)
D = 'data/field-research/dissertation-citations-2026-10-11'
P = {'de', 'da', 'do', 'dos', 'das', 'e'}
cands = list(ing.adapter_brazil_capes(dict(name='b', adapter='brazil_capes', root='data/field-research/brazil-theses-2026-10-31'), ing.D_DEFAULT))

def parts(inv):
    s, _, g = inv.partition(',')
    toks = [t for t in fold(f'{g} {s}').split() if t not in P]
    return toks  # natural order, all name tokens

def compatible(adv_toks, other_toks):
    """Same last surname; same first given name (or its initial); every other name of the shorter form in the longer."""
    if not adv_toks or not other_toks or adv_toks[-1] != other_toks[-1]:
        return False
    a0, o0 = adv_toks[0], other_toks[0]
    if not (a0 == o0 or (len(o0) == 1 and a0.startswith(o0)) or (len(a0) == 1 and o0.startswith(a0))):
        return False
    rest_a, rest_o = adv_toks[1:-1], other_toks[1:-1]
    short, long = (rest_o, rest_a) if len(rest_o) <= len(rest_a) else (rest_a, rest_o)
    return all(any(l == s or (len(s) == 1 and l.startswith(s)) for l in long) for s in short)

adv = {}
cnt = C.Counter()
for c in cands:
    for a in c['entry']['advisors']:
        t = tuple(parts(a))
        if len(t) >= 2:
            adv[t] = a; cnt[t] += 1
by_last = C.defaultdict(list)
with open(f'{D}/cited-people.csv', newline='') as f:
    for r in csv.DictReader(f):
        t = parts(r['name'])
        if len(t) >= 2:
            by_last[t[-1]].append((int(r['cited_by_dissertations'] or 0), r['name'], r['qid'], t))
kl = C.defaultdict(list)
for fp in sorted(glob.glob('data/identifiers/events-*.jsonl')):
    for l in open(fp):
        r = json.loads(l)
        if (r.get('type') == 'person' and r.get('event') == 'mint') or r.get('event') == 'relabel':
            lab = r.get('label') or ''
            t = [x for x in fold(lab if ',' not in lab else lab.split(',', 1)[1] + ' ' + lab.split(',', 1)[0]).split() if x not in P]
            if len(t) >= 2:
                kl[t[-1]].append((r['key'], lab, t))
rows = []
for t, a in adv.items():
    cited = sorted([x for x in by_last.get(t[-1], []) if len(x[3][0]) > 1 and compatible(list(t), x[3])], reverse=True)
    keyed = [x for x in kl.get(t[-1], []) if compatible(list(t), x[2])]
    rows.append(dict(name=a, theses=cnt[t], cited=sum(x[0] for x in cited[:1]), cited_forms=[x[1] for x in cited[:3]],
                     qid=next((x[2] for x in cited if x[2]), ''), keys=sorted({x[0] for x in keyed}), key_labels=[x[1] for x in keyed[:2]]))
N = len(rows)
pct = lambda k: f'{k} ({100*k/N:.0f}%)'
print(f'{N} distinct advisors of the 2,718 Brazilian theses with PDFs')
print('cited in the citation graph:', pct(sum(r['cited'] > 0 for r in rows)), '| by >=5 theses:', pct(sum(r['cited'] >= 5 for r in rows)),
      '| by >=10:', pct(sum(r['cited'] >= 10 for r in rows)), '| with a QID there:', pct(sum(bool(r['qid']) for r in rows)))
print('with a person key in the key log:', pct(sum(bool(r['keys']) for r in rows)), '| of which ambiguous (2+ keys):', sum(len(r['keys']) > 1 for r in rows))
print('\ntop supervisors:')
for r in sorted(rows, key=lambda r: -r['theses'])[:10]:
    print(f"  {r['theses']:3}  {r['name'][:38]:38} cited by {r['cited']:3}  keys {r['keys'][:2]} {r['key_labels'][:1]}")
print('\nmost cited:')
for r in sorted(rows, key=lambda r: -r['cited'])[:10]:
    print(f"  {r['cited']:3}  {r['name'][:38]:38} as {r['cited_forms'][:1]}  keys {r['keys'][:2]} supervised {r['theses']}")
json.dump(rows, open('data/field-research/brazil-theses-2026-10-31/advisor-graph-match-2026-11-02/advisors.json', 'w'), ensure_ascii=False, indent=0)
