#!/usr/bin/env python3
"""Coverage of SwePub's SSIF selection against DiVA's local doctoral research subject (forskarutbildningsämne).
Usage: coverage_check.py diva.csv swepub601.json swepub50203.json"""
import csv, json, re, sys, collections as C
diva = list(csv.DictReader(open(sys.argv[1])))
ids = {}
for f, tag in ((sys.argv[2], "601"), (sys.argv[3], "50203")):
    for h in json.load(open(f))["hits"]:
        for i in [h["recordId"]] + (h.get("duplicateIds") or []): ids.setdefault(i, tag)
HIST = re.compile(r":(historia|idéhistoria|idé- och lärdomshistoria|kyrkohistoria|historia med .*|historiedidaktik|teknikhistoria|rättshistoria|historiska studier|vetenskapshistoria|medicinens historia|konsthistoria)$", re.I)
ECON = re.compile(r":ekonomisk historia$", re.I)
out = C.Counter(); miss = []
for x in diva:
    if not ("2000" <= x["year"] <= "2025"): continue
    subs = [s for s in x["local_subjects"].split(" | ") if s]
    kind = "history" if any(HIST.search(s) for s in subs) else "econ" if any(ECON.search(s) for s in subs) else None
    if not kind: continue
    got = ids.get(x["record_id"])
    out[(kind, got or "missing")] += 1
    if not got: miss.append((kind, x["record_id"], x["year"], x["hsv"], x["local_subjects"], x["title"][:90]))
print(sorted(out.items()))
for m in miss: print(m)
