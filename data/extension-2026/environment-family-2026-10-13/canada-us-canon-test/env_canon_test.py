"""Test: is Canadian environmental-history PhD reading rooted in the American canon?"""
import json, re, csv, sys
from collections import Counter, defaultdict
base = sys.argv[1]
g = json.load(open(base + '/graph.json'))
views = json.load(open(base + '/summary/views.json'))['fields']
env_field_works = {n['id'] for n in views['nodes'] if n['field'] == 9}
diss = {n['id']: n for n in g['nodes'] if n['type'] == 'Dissertation' and n.get('in_analysis')}
works = {n['id']: n for n in g['nodes'] if n['type'] == 'Work'}
persons = {n['id']: n for n in g['nodes'] if n['type'] == 'Person'}
cites = defaultdict(set); authors = defaultdict(set)
for e in g['edges']:
    if e['type'] == 'CITES' and e['source'] in diss: cites[e['source']].add(e['target'])
    elif e['type'] == 'AUTHORED':
        a, b = e['source'], e['target']
        if a in persons: authors[b].add(a)
        else: authors[a].add(b)
kw = re.compile(r'environment|ecolog|wilderness|forest|timber|lumber|river|watershed|water|climat|conservation|wildlife|fish|hunting|park|landscape|soil|drought|pollut|nature|agricult|farm|mining|energy|hydro|dam|fire|animal|beaver|fur trade|land use|resource|disease', re.I)
title_env = {d for d, n in diss.items() if kw.search(n['title'] or '')}
field_env = {d for d in diss if len(cites[d] & env_field_works) >= 3}
ENV = title_env & field_env
print(f'in_analysis PhDs {len(diss)}; title-keyword {len(title_env)}; >=3 env-field works {len(field_env)}; both {len(ENV)}')
US = ['cronon|william', 'worster|donald', 'crosby|alfred w', 'white|richard', 'merchant|carolyn', 'nash|roderick', 'hays|samuel p',
      'carson|rachel', 'leopold|aldo', 'pyne|stephen j', 'marsh|george', 'mcneill|john', 'steinberg|ted', 'hirt|paul w', 'langston|nancy',
      'sellers|christopher c', 'warren|louis s', 'jacoby|karl', 'isenberg|andrew c', 'rome|adam', 'fiege|mark', 'mcevoy|arthur f']
CA = ['innis|harold a', 'lower|arthur', 'wynn|graeme', 'loo|tina', 'cook|ramsay', 'forkey|neil s', 'evenden|matthew', 'macdowell|laurel',
      'maceachern|alan', 'gillis|peter', 'parenteau|bill', 'kheraj|sean r', 'castonguay|stephane', 'sandlos|john', 'piper|liza', 'keeling|arn',
      'dorsey|kurkpatrick', 'harris|cole r', 'gaffield|chad', 'coates|colin m', 'binnema|theodore']
def pkey(pid):
    return pid[2:] if pid.startswith('P:') else pid
keys = {pkey(p) for p in persons}
for k in US + CA:
    if k not in keys: print('missing key', k, [x for x in keys if x.split('|')[0] == k.split('|')[0]][:6])
def cited_people(dset):
    c = Counter()
    for d in dset:
        ppl = set()
        for w in cites[d]: ppl |= {pkey(p) for p in authors.get(w, ())}
        c.update(ppl)
    return c
out = {}
for label, S in [('env_both', ENV), ('env_title', title_env), ('all', set(diss))]:
    c = cited_people(S)
    us_any = sum(1 for d in S if any(pkey(p) in US for w in cites[d] for p in authors.get(w, ())))
    ca_any = sum(1 for d in S if any(pkey(p) in CA for w in cites[d] for p in authors.get(w, ())))
    out[label] = dict(n=len(S), cite_any_us_canon=us_any, cite_any_cdn_canon=ca_any,
                      us=[(k, c[k]) for k in US], ca=[(k, c[k]) for k in CA], top=c.most_common(60))
    print(f'\n== {label}: n={len(S)}; cite any US canon {us_any} ({us_any/len(S):.0%}); any Canadian set {ca_any} ({ca_any/len(S):.0%})')
    print('US :', ', '.join(f'{k.split("|")[0]} {c[k]}' for k in sorted(US, key=lambda k: -c[k])))
    print('CA :', ', '.join(f'{k.split("|")[0]} {c[k]}' for k in sorted(CA, key=lambda k: -c[k])))
# time split for env_both
for lo, hi in [(0, 2004), (2005, 2014), (2015, 2030)]:
    S = {d for d in ENV if lo <= (diss[d].get('year') or 0) <= hi}
    if not S: continue
    c = cited_people(S)
    print(f'\n{lo}-{hi}: n={len(S)} | US', ', '.join(f'{k.split("|")[0]} {c[k]/len(S):.0%}' for k in US[:8]), '| CA', ', '.join(f'{k.split("|")[0]} {c[k]/len(S):.0%}' for k in CA[:6]))
print('\nTop 50 people cited by env_both PhDs:')
for k, n in out['env_both']['top'][:50]: print(f'  {n:3d} {k}')
json.dump(dict(out, env_ids=sorted(ENV)), open(sys.argv[2], 'w'), indent=1)
