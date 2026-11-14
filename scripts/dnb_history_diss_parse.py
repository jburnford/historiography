#!/usr/bin/env python3
"""Parse the DNB SRU MARC21-xml pages written by dnb_history_diss_pilot.py into
one flat record per catalogue record (JSON lines), for measurement.

Usage:
  python3 -I scripts/dnb_history_diss_parse.py /mnt/e/dnb-history-diss-2026-11-14/raw \
      /mnt/e/dnb-history-diss-2026-11-14/records.jsonl
"""
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

NS = {"m": "http://www.loc.gov/MARC21/slim"}


def subs(df):
    return [(s.get("code"), (s.text or "").strip()) for s in df.findall("m:subfield", NS)]


def first(sf, code):
    for c, v in sf:
        if c == code:
            return v
    return ""


def gnd_of(sf):
    for c, v in sf:
        if c == "0" and v.startswith("(DE-588)"):
            return v[len("(DE-588)"):]
    return ""


DIS_A = re.compile(r"^(?P<univ>.+?),\s*(?P<type>(Univ\.?, )?(Diss|Habil|Dissertation|Habilitationsschrift)[^,]*),\s*(?P<year>\d{4})")


def parse_record(rec):
    out = {"supervisors": [], "contributors": [], "urls": [], "ddc": [], "sachgruppe": [],
           "isbn": [], "related": []}
    for cf in rec.findall("m:controlfield", NS):
        tag = cf.get("tag")
        if tag == "001":
            out["id"] = cf.text
        elif tag == "008" and cf.text:
            out["year_pub"] = cf.text[7:11]
            out["lang008"] = cf.text[35:38]
            out["country008"] = cf.text[15:18].strip()
    for df in rec.findall("m:datafield", NS):
        tag = df.get("tag")
        sf = subs(df)
        if tag == "020":
            v = first(sf, "a")
            if v:
                out["isbn"].append(v)
        elif tag == "024":
            kind = first(sf, "2")
            out.setdefault(kind or "other_id", first(sf, "a"))
        elif tag == "041":
            out["lang"] = [v for c, v in sf if c == "a"]
        elif tag == "044":
            out["country044"] = first(sf, "c")
        elif tag in ("082", "083"):
            src = first(sf, "2")
            vals = [v for c, v in sf if c == "a"]
            if "sdnb" in src:
                out["sachgruppe"] += vals
            else:
                out["ddc"] += vals
        elif tag == "100":
            out["author"] = first(sf, "a")
            out["author_gnd"] = gnd_of(sf)
            out["author_dates"] = first(sf, "d")
        elif tag == "245":
            out["title"] = first(sf, "a")
            out["subtitle"] = first(sf, "b")
            out["resp"] = first(sf, "c")
        elif tag == "264" and not out.get("publisher"):
            out["publisher"] = first(sf, "b")
            out["place"] = first(sf, "a")
        elif tag == "337":
            out["media"] = first(sf, "b")
        elif tag == "502":
            a, b, c, d = (first(sf, x) for x in "abcd")
            if b or c:
                out["diss_type"], out["univ"], out["degree_year"] = b, c, d
            elif a:
                m = DIS_A.match(a)
                if m:
                    out["diss_type"], out["univ"], out["degree_year"] = m["type"], m["univ"], m["year"]
                else:
                    out["diss_note"] = a
        elif tag in ("700", "710"):
            role = first(sf, "4")
            entry = {"name": first(sf, "a"), "gnd": gnd_of(sf), "dates": first(sf, "d"),
                     "role_text": first(sf, "e"), "role": role, "tag": tag}
            if role == "dgs" or "Betreuer" in entry["role_text"]:
                out["supervisors"].append(entry)
            else:
                out["contributors"].append(entry)
        elif tag == "776":
            w = [v for c, v in sf if c == "w"]
            out["related"].append({"i": first(sf, "i"), "n": first(sf, "n"), "w": w})
        elif tag == "856":
            out["urls"].append({"u": first(sf, "u"), "x": first(sf, "x"), "z": first(sf, "z"),
                                "q": first(sf, "q")})
    return out


def main():
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    seen = set()
    n = 0
    with open(dst, "w", encoding="utf-8") as fo:
        for p in sorted(src.glob("*.xml")):
            year = p.name[:4]
            root = ET.parse(p).getroot()
            for rec in root.iter("{http://www.loc.gov/MARC21/slim}record"):
                r = parse_record(rec)
                r["query_year"] = year
                if r.get("id") in seen:
                    continue
                seen.add(r.get("id"))
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
    print(n, "records")


if __name__ == "__main__":
    main()
