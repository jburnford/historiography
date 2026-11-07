"""Two person keys credited with the same work (authored or edited) under the same name: one person (identity by
works). Both names must give the same spelled-out first name and the same family name; initial-only keys (which
pool namesakes) and keys behind the merge guard are left alone. Writes proposal.json."""
import duckdb, sys, json, re, unicodedata
sys.path.insert(0, 'scripts')
from collections import defaultdict
from identifiers import State, DEFAULT_DIR
from merge_guard import blocked_keys
PIDS = ('lcnaf:', 'wd:', 'orcid:', 'gnd:', 'viaf:', 'isni:', 'idref:')
def fold(x): return unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
def parts(label):
    l = re.sub(r',?\s*\d{4}.*$', '', label).strip()
    l = re.sub(r'\([^)]*\)', '', l).strip(' ,')
    if ', ' in l: fam, giv = l.split(', ', 1)
    else:
        t = l.split(); fam, giv = (t[-1], ' '.join(t[:-1])) if len(t) > 1 else (l, '')
    g = [w for w in re.findall(r'[a-z]+', fold(giv))]
    return fold(fam).strip(), g
db = duckdb.connect()
s = State.load(DEFAULT_DIR); blocked = blocked_keys(s)
L = dict(db.execute("select key,label from 'build/graph/person.parquet'").fetchall())
W = dict(db.execute("select key,label from 'build/graph/work.parquet'").fetchall())
rows = db.execute("""select w, list(distinct p) from (select "to" w, "from" p from 'build/graph/authored.parquet'
                     union select "to", "from" from 'build/graph/edited.parquet') group by w having count(distinct p) > 1""").fetchall()
ops, held, seen = [], [], set()
for w, ps in rows:
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            a, b = sorted((ps[i], ps[j]), key=lambda k: int(k[2:]))
            (fa, ga), (fb, gb) = parts(L[a]), parts(L[b])
            if not fa or fa != fb or not ga or not gb: continue
            if len(ga[0]) < 2 or len(gb[0]) < 2 or ga[0] != gb[0]: continue
            if (a, b) in seen: continue
            seen.add((a, b))
            conf = [x for x in s.keys[a]['anchors'] for y in s.keys[b]['anchors']
                    if x.startswith(PIDS) and y.startswith(PIDS) and x.split(':')[0] == y.split(':')[0] and x != y]
            why = 'merge guard' if {a, b} & blocked else ('conflicting identifiers' if conf else None)
            if not why and len(ga) > 1 and len(gb) > 1 and ga[1][0] != gb[1][0]: why = 'middle names differ'
            rec = dict(a=a, la=L[a], b=b, lb=L[b], work=w, title=W.get(w, '')[:90])
            if why: held.append(dict(rec, why=why)); continue
            ops.append(dict(event='merge', key=b, into=a, basis=f"identity by works: both keys are credited with {w} ('{W.get(w, '')[:80]}') under the same name ({L[a]} / {L[b]}); the older key survives"))
out = 'data/identifiers/shared-work-dups-2026-11-07'
json.dump(dict(basis='same-name keys credited with the same work', decided_by='rule', ops=ops), open(out + '/proposal.json', 'w'), ensure_ascii=False, indent=0)
json.dump(held, open(out + '/held.json', 'w'), ensure_ascii=False, indent=1)
print(len(ops), 'merges', len(held), 'held')
for o in ops: print(' ', o['basis'][:150])
for h in held: print(' H', h['la'], '|', h['lb'], '|', h['why'])
