#!/usr/bin/env python3
"""Flatten DiVA OAI swepub_mods ListRecords pages into diva-theses.csv: one row per doctoral thesis with
year, publisher org (department), hsv codes, local research subjects, counts of aut/ths/opn and DiVA
authority-person ids. Usage: parse_diva_oai.py PAGES_DIR OUT_CSV"""
import csv, glob, re, sys
import xml.etree.ElementTree as ET
NS = {"o": "http://www.openarchives.org/OAI/2.0/", "m": "http://www.loc.gov/mods/v3"}
X = "{http://www.w3.org/1999/xlink}href"
rows = []
for f in sorted(glob.glob(sys.argv[1] + "/page-*.xml")):
    root = ET.parse(f).getroot()
    for rec in root.iter("{%s}record" % NS["o"]):
        h = rec.find("o:header", NS)
        if h is None or h.get("status") == "deleted": continue
        mods = rec.find(".//m:mods", NS)
        if mods is None: continue
        rid = h.findtext("o:identifier", namespaces=NS)
        genres = [g.text or "" for g in mods.findall("m:genre", NS)]
        year = (mods.findtext("m:originInfo/m:dateIssued", default="", namespaces=NS) or "")[:4]
        title = mods.findtext("m:titleInfo/m:title", default="", namespaces=NS)
        hsv, local = set(), set()
        for s in mods.findall("m:subject", NS):
            a = s.get("authority") or ""
            if a == "hsv": hsv.add(s.get(X) or "")
            elif s.get(X) and s.find("m:genre", NS) is not None and s.get("lang") == "swe":
                local.add(a + ":" + (s.findtext("m:topic", default="", namespaces=NS)))
        cnt = {"aut": 0, "ths": 0, "opn": 0}; auth = {"aut": 0, "ths": 0, "opn": 0}; orc = {"aut": 0, "ths": 0, "opn": 0}
        dept = ""
        for n in mods.findall("m:name", NS):
            r = n.findtext("m:role/m:roleTerm", default="", namespaces=NS)
            if n.get("type") == "corporate" and r == "pbl":
                dept = " / ".join(p.text or "" for p in n.findall("m:namePart", NS))
            if n.get("type") != "personal" or r not in cnt: continue
            cnt[r] += 1
            d = " ".join(x.text or "" for x in n.findall("m:description", NS))
            if "authority-person" in d: auth[r] += 1
            if "orcid" in d.lower(): orc[r] += 1
        lang = mods.findtext("m:language/m:languageTerm", default="", namespaces=NS)
        rows.append({"record_id": rid, "year": year, "genre": "|".join(g for g in genres if g), "lang": lang,
                     "title": title, "hsv": " ".join(sorted(hsv)), "local_subjects": " | ".join(sorted(local)),
                     "publisher_org": dept, **{f"n_{k}": v for k, v in cnt.items()},
                     **{f"auth_{k}": v for k, v in auth.items()}, **{f"orcid_{k}": v for k, v in orc.items()}})
with open(sys.argv[2], "w", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows))
