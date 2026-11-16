#!/usr/bin/env python3
"""Flatten SwePub JSON-LD thesis records (from fetch_swepub_records.py) into two metadata tables:
theses.csv (one row per thesis) and people.csv (one row per author/supervisor/opponent credit).
Usage: parse_swepub_records.py RECORDS_DIR LIST.json[,LIST.json] OUT_PREFIX"""
import csv, glob, json, os, sys, urllib.parse
recdir, lists, outp = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
hits = {}
for f in lists:
    for h in json.load(open(f))["hits"]:
        hits.setdefault(h["recordId"], h)
ROLE = {"aut": "author", "ths": "supervisor", "supervisor": "supervisor", "sup": "supervisor",
        "opn": "opponent", "org": "org", "edt": "editor", "pbl": "publisher", "exm": "examiner", "oth": "other"}
T, P = [], []
for rid, h in hits.items():
    fn = os.path.join(recdir, urllib.parse.quote(rid, safe="") + ".json")
    if not os.path.exists(fn): continue
    d = json.load(open(fn)); w = d.get("instanceOf", {})
    five = sorted(set(h["classifications"].get("fiveDigitTopics") or []))
    three = sorted(set(h["classifications"].get("threeDigitTopics") or []))
    cls_assigners = set()
    for c in w.get("classification", []):
        a = (c.get("@annotation") or {}).get("assigner", {}).get("@id", "")
        if c.get("code", "").startswith(("601", "50203")): cls_assigners.add("swepub-classifier" if "classifier" in a else "source")
    local_subj = sorted({(s.get("inScheme") or {}).get("code", "") + ":" + "/".join(s.get("prefLabelByLang", {}).values())
                         for s in w.get("subject", []) if s.get("inScheme") and s.get("code")})
    notes = [n.get("label") for n in w.get("hasNote", []) if isinstance(n, dict)]
    diss = d.get("dissertation") or [{}]
    lic = []
    for u in d.get("usageAndAccessPolicy", []) or []:
        lic.append(u.get("@id") or u.get("label") or json.dumps(u, ensure_ascii=False)[:60])
    roles = {}
    for c in w.get("contribution", []):
        ag = c.get("agent", {})
        rcodes = [r.get("@id", "").rsplit("/", 1)[-1] for r in c.get("role", [])] or ["?"]
        role = ROLE.get(rcodes[0], rcodes[0])
        if ag.get("@type") != "Person": continue
        ids = ag.get("identifiedBy", []) or []
        orcid = next((i["value"].rsplit("/", 1)[-1] for i in ids if i.get("@type") == "ORCID"), "")
        local = ";".join(f'{(i.get("source") or {}).get("code","")}:{i.get("value")}' for i in ids if i.get("@type") == "Local")
        affs = []
        for a in c.get("hasAffiliation", []) or []:
            nm = a.get("name") or "/".join((a.get("nameByLang") or {}).values())
            top = [ "/".join((b.get("nameByLang") or {}).values()) for b in a.get("hasAffiliation", []) or []]
            affs.append(", ".join([x for x in [nm] + top if x]))
        roles[role] = roles.get(role, 0) + 1
        P.append({"record_id": rid, "role": role, "role_code": rcodes[0], "family": ag.get("familyName", ""),
                  "given": ag.get("givenName", ""), "life_span": ag.get("lifeSpan", ""),
                  "title": ag.get("termsOfAddress", ""), "orcid": orcid, "local_ids": local,
                  "affiliation": " | ".join(affs)})
    T.append({"record_id": rid, "source": "+".join(h["source"]), "year": h["publicationYear"][:4],
              "defence_date": diss[0].get("date", ""), "title": h["title"], "language": "+".join(h["languages"] or []),
              "ssif5": " ".join(five), "ssif3": " ".join(three), "ssif_assigner": "+".join(sorted(cls_assigners)),
              "autoclassified": h["autoclassified"], "local_subjects": " | ".join(local_subj),
              "n_author": roles.get("author", 0), "n_supervisor": roles.get("supervisor", 0), "n_opponent": roles.get("opponent", 0),
              "open_access": h["openAccess"], "fulltext_url": h.get("electronicLocator") or "",
              "isbn": " ".join(sorted(set(h["ISBN"] or []))), "doi": " ".join(h["DOI"] or []),
              "series": h.get("seriesTitle") or "", "publisher": h.get("publisher") or "",
              "licence": " ".join(lic), "duplicate_ids": " ".join(h.get("duplicateIds") or []),
              "urn": h.get("archiveURI") or ""})
for name, rows in (("theses", T), ("people", P)):
    with open(f"{outp}{name}.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
print(len(T), "theses", len(P), "person credits")
