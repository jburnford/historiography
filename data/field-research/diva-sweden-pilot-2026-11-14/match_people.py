#!/usr/bin/env python3
"""Match SwePub thesis people (people.csv from parse_swepub_records.py) to existing person keys, read-only.
Routes: (1) ORCID -> orcid: anchor; (2) ORCID -> Wikidata item -> wd: anchor;
(3) name -> Wikidata item with P906/P5587 and same birth year (lifeSpan) -> wd: anchor;
(4) full name + a second fact against graph person labels: birth year in life-years.csv.gz, or a
graph work whose title equals a SwePub thesis title / shares ISBN. Name-only hits are counted, never matched.
Usage: match_people.py PEOPLE.csv THESES.csv EXPLORER.duckdb LIFE_YEARS.csv.gz WD_HUMANS.csv OUT.csv"""
import csv, gzip, re, sys, unicodedata, collections as C
import duckdb
pc, tc, db, ly, wdf, out = sys.argv[1:7]
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]+", " ", s).split()
def key_name(given, family):
    g, f = norm(given), norm(family)
    return (" ".join(f), g[0][0] if g else "", " ".join(g))
people = list(csv.DictReader(open(pc)))
con = duckdb.connect(db, read_only=True)
orc = dict(con.execute("select substr(anchor,7), key from anchors where anchor like 'orcid:%' and key like 'p-%'").fetchall())
wd = dict(con.execute("select substr(anchor,4), key from anchors where anchor like 'wd:%' and key like 'p-%'").fetchall())
labels = con.execute("select key, label from nodes where type='person'").fetchall()
births = {}
with gzip.open(ly, "rt") as f:
    for r in csv.DictReader(f):
        if r["birth"]: births[r["key"]] = r["birth"]
# graph label index: (family, first given) -> keys ; handles "Family, Given, 1950-" and "Given Family"
idx = C.defaultdict(set)
for k, lab in labels:
    lab = re.sub(r",?\s*\d{4}-(\d{4})?\.?$", "", lab or "")
    if "," in lab:
        fam, giv = lab.split(",", 1)
    else:
        parts = lab.split(); fam, giv = (parts[-1] if parts else ""), " ".join(parts[:-1])
    f, g = " ".join(norm(fam)), " ".join(norm(giv))
    if f and g: idx[(f, g)].add(k); idx[(f, g.split()[0])].add(k)
# graph affiliations: person -> set of normalised institution labels
SV = {"uppsala universitet": "uppsala university", "stockholms universitet": "stockholm university",
      "lunds universitet": "lund university", "goteborgs universitet": "university of gothenburg",
      "umea universitet": "umea university", "sodertorns hogskola": "sodertorn university",
      "kungliga tekniska hogskolan": "kth royal institute of technology", "orebro universitet": "orebro university",
      "linkopings universitet": "linkoping university", "linneuniversitetet": "linnaeus university",
      "karlstads universitet": "karlstad university", "mittuniversitetet": "mid sweden university",
      "lulea tekniska universitet": "lulea university of technology", "malmo universitet": "malmo university",
      "forsvarshogskolan": "swedish defence university", "handelshogskolan i stockholm": "stockholm school of economics",
      "sveriges lantbruksuniversitet": "swedish university of agricultural sciences",
      "kobenhavns universitet": "university of copenhagen", "aarhus universitet": "aarhus university",
      "universitetet i oslo": "university of oslo", "universitetet i bergen": "university of bergen",
      "helsingin yliopisto": "university of helsinki", "abo akademi": "abo akademi university"}
CODE = {"uu": "uppsala university", "su": "stockholm university", "lu": "lund university", "gu": "university of gothenburg",
        "umu": "umea university", "sh": "sodertorn university", "kth": "kth royal institute of technology",
        "oru": "orebro university", "liu": "linkoping university", "lnu": "linnaeus university", "kau": "karlstad university",
        "miun": "mid sweden university", "ltu": "lulea university of technology", "mau": "malmo university",
        "fhs": "swedish defence university", "hhs": "stockholm school of economics", "slu": "swedish university of agricultural sciences"}
aff = C.defaultdict(set)
for k, lab in con.execute('select e."from", n.label from e_affiliated_with_f e join nodes n on n.key=e."to"').fetchall():
    aff[k].add(" ".join(norm(lab)))
def insts(p):
    t = " ".join(norm(p["affiliation"])); out = set()
    for sv, en in SV.items():
        if sv in t: out.add(en)
    for c in (p["local_ids"] or "").split(";"):
        c = c.split(":")[0]
        if c in CODE: out.add(CODE[c])
    return t, out
def aff_match(k, p):
    t, ins = insts(p)
    for lab in aff.get(k, ()):
        if lab in ins or (len(lab) >= 12 and lab in t): return True
    return False
# Wikidata humans with Libris/SELIBR/DiVA ids
wdh = list(csv.DictReader(open(wdf)))
wd_by_orcid = {r["orcid"]: r["h"].rsplit("/", 1)[-1].lower() for r in wdh if r["orcid"]}
wd_by_name = C.defaultdict(list)
for r in wdh:
    n = norm(r["label"])
    if len(n) >= 2: wd_by_name[(n[-1], n[0])].append(r)
rows = []
for p in people:
    if p["role"] not in ("author", "supervisor", "assistant_supervisor", "opponent"): continue
    fam, giv = " ".join(norm(p["family"])), " ".join(norm(p["given"]))
    by = (re.match(r"(\d{4})", p["life_span"] or "") or [None, ""])[1] if p["life_span"] else ""
    res, key, via = "", "", ""
    if p["orcid"] and p["orcid"] in orc: key, via = orc[p["orcid"]], "orcid"
    elif p["orcid"] and p["orcid"] in wd_by_orcid and wd_by_orcid[p["orcid"]] in wd: key, via = wd[wd_by_orcid[p["orcid"]]], "orcid->wd"
    if not key and by and fam and giv:
        cands = [r for r in wd_by_name.get((fam.split()[-1], giv.split()[0]), []) if r["birth"] == by]
        ks = {wd.get(r["h"].rsplit("/", 1)[-1].lower()) for r in cands} - {None}
        if len(ks) == 1: key, via = ks.pop(), "name+birth->libris-wd"
    name_keys = idx.get((fam, giv), set()) | (idx.get((fam, giv.split()[0]), set()) if giv else set())
    if not key and name_keys:
        if by:
            ks = {k for k in name_keys if births.get(k) == by}
            if len(ks) == 1: key, via = ks.pop(), "name+birth-year"
        if not key:
            ks = {k for k in name_keys if aff_match(k, p)}
            if len(ks) == 1: key, via = ks.pop(), "name+affiliation"
        if not key: res = f"name-only:{len(name_keys)}"
    rows.append({**{k: p[k] for k in ("record_id", "role", "family", "given", "life_span", "orcid")},
                 "key": key, "via": via, "name_only": res, "has_local_id": bool(p["local_ids"])})
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
# summary on distinct people (role, normalised name + birth/orcid)
def pid(r): return r["orcid"] or (" ".join(norm(r["family"])) + "|" + " ".join(norm(r["given"])))
for role in ("author", "supervisor", "opponent"):
    rr = [r for r in rows if r["role"].endswith(role)]
    d = {}
    for r in rr: d.setdefault(pid(r), r if r["key"] else d.get(pid(r), r))
    m = C.Counter(r["via"] or ("name-only" if r["name_only"] else "new") for r in d.values())
    print(role, "credits", len(rr), "distinct", len(d), dict(m))
