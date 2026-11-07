"""Festschrift honorees credited as editors (2026-11-07). LC records a festschrift's honoree as an added entry
(700) without a relator; where the honoree shares a family name with an editor in the statement of
responsibility, the LC works route read the honoree as an editor ('Essays on western history: in honour of
Lewis Gwynne Thomas', edited by Lewis H. Thomas). An `edited` claim is withdrawn when the person's name (first
given name and family) is the name the title honours ('in honour of', 'presented to', 'Festschrift für',
'in memory of', 'hommage à', 'mélanges' ...). Writes proposal.json and the list (honorees.csv)."""
import csv, duckdb, json, re, sys, unicodedata
sys.path.insert(0, 'scripts')
def fold(x): return unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
PHRASE = re.compile(r"(?:in honou?r of|honou?ring|presented to|offered to|dedicated to|in memory of|in memoriam|a tribute to|"
                    r"festschrift (?:fur|for|zum [^:]*? von|honou?ring)?|gedenkschrift fur|essays for|studies for|"
                    r"en hommage a|hommage a|hommages? (?:pour|a)|melanges (?:offerts a)?|recueil d'hommages pour|"
                    r"zum \d+\. geburtstag von|zu ehren von|in onore di)\s+(.*)", re.I)
def honoree(title):
    m = PHRASE.search(fold(title))
    if not m: return ''
    h = re.split(r'\s*(?:[:;/,(]|\bon the occasion\b|\bzum\b|\bon his\b|\bon her\b|\bat\b|\bby\b)', m.group(1))[0]
    return re.sub(r'\b(professor|prof|dr|sir|father|s\.?j|o\.?p)\b\.?', ' ', h).strip(' .')
def person_names(label):
    l = re.sub(r'\([^)]*\)', ' ', label); l = re.sub(r',?\s*\d{4}.*$', '', l).strip(' ,')
    fam, giv = (l.split(', ', 1) + [''])[:2] if ', ' in l else (l.split()[-1], ' '.join(l.split()[:-1]))
    return fold(fam).strip(), [w for w in re.findall(r'[a-z]+', fold(giv))]
db = duckdb.connect()
rows = db.execute("""select e."from", p.label, e."to", w.label, e.claim from 'build/graph/edited.parquet' e
    join 'build/graph/work.parquet' w on w.key = e."to" join 'build/graph/person.parquet' p on p.key = e."from" """).fetchall()
from identifiers import State, DEFAULT_DIR
state = State.load(DEFAULT_DIR)
LC = dict(db.execute("select lcid, label from '/mnt/e/lc-authorities/personal-names.parquet'").fetchall())
hits = []
for f, pl, w, wl, c in rows:
    h = honoree(wl)
    if not h: continue
    hw = h.split()
    fam, giv = person_names(pl)
    if not fam or not giv or not hw: continue
    famw = fam.split()
    # the honoree string ends with the family name (or contains it as the last words) and opens with the first given name
    joined = ' '.join(hw)
    if not re.search(r'\b' + re.escape(fam) + r'$', joined): continue
    first = hw[0]
    if not (first == giv[0] or (len(giv[0]) == 1 and first[0] == giv[0]) or (len(first) == 1 and first == giv[0][0])): continue
    mid_h = [x for x in hw[1:] if x != fam and x not in fam.split()]
    if len(giv) > 1 and mid_h and mid_h[0][0] != giv[1][0]: continue      # Lewis H. Thomas is not Lewis Gwynne Thomas
    if state.keys[c]['status'] in ('withdrawn', 'merged'): continue
    anchors = sorted(state.keys[c]['anchors'])
    if not any(a.startswith('lc-edited:') for a in anchors): continue
    # the LC authority's fuller form decides when the key's label has no middle name ('Thomas, Lewis' is
    # 'Thomas, Lewis H. (Lewis Herbert)'; added after the first run withdrew his claim in error)
    lcid = anchors[0].rsplit(':', 1)[1]
    lc_giv = person_names(LC.get(lcid, pl))[1]
    if len(lc_giv) > 1 and mid_h and mid_h[0][0] != lc_giv[1][0]: continue
    hits.append(dict(person=f, label=pl, work=w, title=wl, honoree=h, claim=c, anchor=anchors[0]))
out = 'data/identifiers/festschrift-honorees-2026-11-07'
with open(out + '/honorees.csv', 'w', newline='') as fh:
    if not hits: raise SystemExit('no honorees')
    wtr = csv.DictWriter(fh, fieldnames=list(hits[0])); wtr.writeheader(); wtr.writerows(hits)
ops = [dict(event='withdraw', key=h['claim'], basis=f"festschrift honoree read as editor: '{h['title'][:120]}' honours {h['label']}; LC's added entry for the honoree carries no relator (festschrift-honorees-2026-11-07)") for h in hits]
json.dump(dict(basis='edited claims withdrawn where the person is the festschrift honoree', decided_by='rule', ops=ops), open(out + '/proposal.json', 'w'), ensure_ascii=False, indent=0)
print(len(rows), 'edited;', len(hits), 'honorees')
import random; random.seed(2)
for h in random.sample(hits, min(40, len(hits))): print(' ', h['label'][:30].ljust(30), '|', h['title'][:100])
