#!/usr/bin/env python3
"""Parse every fetched SwePub thesis record (fetch_swepub_records.py output) into two metadata tables.
Metadata only: no full text. Read-only on the raw folder.

  theses.csv   one row per SwePub record (a thesis; duplicates across repositories are already
               merged by SwePub into one record with duplicate_ids)
  people.csv   one row per person credit: author, supervisor (ths/supervisor), assistant
               supervisor, opponent

Usage: parse_all_swepub.py RAW_DIR OUT_DIR
  RAW_DIR = /mnt/e/diva-history-theses-2026-11-14 (reads swepub/dt-*.json and swepub/records/)"""
import csv, glob, json, os, re, sys, urllib.parse, collections as C

raw, out = sys.argv[1], sys.argv[2]
hits, lists = {}, C.defaultdict(set)
for f, tag in (("dt-601-2000-2025.json", "601"), ("dt-50203-2000-2025.json", "50203")):
    for h in json.load(open(os.path.join(raw, "swepub", f)))["hits"]:
        hits.setdefault(h["recordId"], h)
        lists[h["recordId"]].add(tag)

ROLE = {"aut": "author", "ths": "supervisor", "supervisor": "supervisor",
        "assistant_supervisor": "assistant_supervisor", "opn": "opponent"}
# institution code -> name (degree-granting universities and colleges seen in the pull)
INST = {"uu": "Uppsala universitet", "su": "Stockholms universitet", "lu": "Lunds universitet",
        "gu": "Göteborgs universitet", "umu": "Umeå universitet", "sh": "Södertörns högskola",
        "lnu": "Linnéuniversitetet", "oru": "Örebro universitet", "kth": "KTH", "kau": "Karlstads universitet",
        "liu": "Linköpings universitet", "ltu": "Luleå tekniska universitet", "miun": "Mittuniversitetet",
        "mau": "Malmö universitet", "slu": "Sveriges lantbruksuniversitet", "chalmers": "Chalmers",
        "hhs": "Handelshögskolan i Stockholm", "fhs": "Försvarshögskolan", "esh": "Enskilda Högskolan Stockholm",
        "ths": "Teologiska högskolan Stockholm", "gih": "Gymnastik- och idrottshögskolan", "du": "Högskolan Dalarna",
        "hb": "Högskolan i Borås", "his": "Högskolan i Skövde", "bth": "Blekinge tekniska högskola",
        "mdh": "Mälardalens universitet", "hj": "Jönköping University", "ki": "Karolinska institutet",
        "uniarts": "Stockholms konstnärliga högskola", "rkh": "Röda Korsets Högskola", "raa": "Riksantikvarieämbetet",
        "hig": "Högskolan i Gävle", "kmh": "Kungl. Musikhögskolan", "konstfack": "Konstfack", "nai": "Nordiska Afrikainstitutet",
        "hh": "Högskolan i Halmstad", "vxu": "Linnéuniversitetet"}
# publisher / series words -> institution (the printed series is the strongest degree-place clue)
SERIES = [("upsalien", "uu"), ("uppsala", "uu"), ("stockholmien", "su"), ("stockholm univ", "su"),
          ("stockholms univ", "su"), ("lund", "lu"), ("gothoburg", "gu"), ("göteborg", "gu"), ("gothenburg", "gu"),
          ("umeå", "umu"), ("umea", "umu"), ("södertörn", "sh"), ("sodertorn", "sh"), ("linnaeus", "lnu"),
          ("linné", "lnu"), ("örebro", "oru"), ("orebro", "oru"), ("karlstad", "kau"), ("linköping", "liu"),
          ("linkoping", "liu"), ("kth", "kth"), ("royal institute of technology", "kth"), ("luleå", "ltu"),
          ("mittuniversitet", "miun"), ("mid sweden", "miun"), ("malmö", "mau"), ("chalmers", "chalmers"),
          ("agriculturae sueciae", "slu"), ("lantbruks", "slu")]
FULL_LABELS = {"fulltext", "full text"}


def urn_codes(d, h):
    codes = []
    uris = [i.get("value", "") for i in d.get("identifiedBy", []) if i.get("@type") == "URI"]
    uris.append(h.get("archiveURI") or "")
    for u in uris:
        m = re.search(r"urn:nbn:se:([a-z]+)[-:]", u)
        if m:
            codes.append(m.group(1))
    return codes


def degree_place(d, h, w, persons):
    votes = C.Counter()
    text = " ".join([h.get("publisher") or "", h.get("seriesTitle") or ""] +
                    [t.get("mainTitle", "") for s in d.get("hasSeries", []) or [] for t in s.get("hasTitle", [])]).lower()
    for word, code in SERIES:
        if word in text:
            votes[code] += 3
            break
    for p in persons:
        if p["role"] == "author":
            for c in p["aff_codes"]:
                votes[c] += 2
    for e in d.get("electronicLocator", []) or []:
        m = re.match(r"https?://([a-z]+)\.diva-portal\.org", e.get("uri", ""))
        if m:
            votes[m.group(1)] += 1
    for c in urn_codes(d, h):
        if c != "kb":  # urn:nbn:se:kb is the national library's own namespace, not a degree place
            votes[c] += 1
    rid = h["recordId"]
    m = re.match(r"oai:DiVA\.org:([a-z]+)-", rid)
    if m:
        votes[m.group(1)] += 1
    if rid.startswith("oai:portal.research.lu.se") or rid.startswith("oai:lup.lub.lu.se"):
        votes["lu"] += 2
    if rid.startswith("oai:gup.ub.gu.se"):
        votes["gu"] += 2
    if "chalmers" in rid:
        votes["chalmers"] += 2
    if "slu" in rid:
        votes["slu"] += 2
    if not votes:
        return "", ""
    if "vxu" in votes:  # Växjö universitet merged into Linnéuniversitetet (2010)
        votes["lnu"] += votes.pop("vxu")
    (best, n), *rest = votes.most_common()
    basis = "clear" if not rest or n > rest[0][1] else "tie"
    return best, basis


def org_codes(org):
    """Institution codes on an affiliation: {'source': 'kb.se', 'value': 'uu.se'} (national list) or
    {'source': 'uu.se', 'value': 'Historiska institutionen'} (a department in uu's own list)."""
    out = set()
    for i in org.get("identifiedBy", []) or []:
        src, v = (i.get("source") or {}).get("code", ""), i.get("value", "")
        if src == "kb.se" and v.endswith(".se"):
            out.add(v[:-3])
        elif src.endswith(".se") and src != "kb.se":
            out.add(src[:-3])
    return out


def person(c, rid):
    ag = c.get("agent", {})
    rcode = [r.get("@id", "").rsplit("/", 1)[-1] for r in c.get("role", [])] or ["?"]
    role = ROLE.get(rcode[0])
    if ag.get("@type") != "Person" or not role:
        return None
    ids = ag.get("identifiedBy", []) or []
    orcid = next((i["value"].rsplit("/", 1)[-1] for i in ids if i.get("@type") == "ORCID" and i.get("value")), "")
    local = ";".join(f'{(i.get("source") or {}).get("code", "")}:{i.get("value")}' for i in ids if i.get("@type") == "Local")
    affs, codes = [], set()
    for a in c.get("hasAffiliation", []) or []:
        nm = a.get("name") or "/".join((a.get("nameByLang") or {}).values())
        top = []
        for b in a.get("hasAffiliation", []) or []:
            top.append("/".join((b.get("nameByLang") or {}).values()) or b.get("name", ""))
            codes.update(org_codes(b))
        codes.update(org_codes(a))
        affs.append(", ".join(x for x in [nm] + top if x))
    life = ag.get("lifeSpan", "") or ""
    m = re.match(r"(\d{4})-(\d{4})?", life)
    return {"record_id": rid, "role": role, "role_code": rcode[0], "family": ag.get("familyName", ""),
            "given": ag.get("givenName", ""), "life_span": life, "birth_year": m.group(1) if m else "",
            "death_year": (m.group(2) or "") if m else "", "title": ag.get("termsOfAddress", ""),
            "orcid": orcid, "local_ids": local, "affiliation": " | ".join(affs), "aff_codes": sorted(codes)}


def fulltext(d, h):
    """First open full-text link: SwePub's own primary locator, else a record locator labelled full text."""
    links = []
    for e in d.get("electronicLocator", []) or []:
        lab = (e.get("label") or "").strip()
        notes = {n.get("label") for n in e.get("hasNote", []) or []}
        uri = e.get("uri", "")
        if not uri:
            continue
        if lab.lower() in FULL_LABELS:
            links.append((uri, "open", lab))
        elif "not accessible to users outside sweden" in lab.lower():
            links.append((uri, "sweden-only", lab))
        elif not lab and ("free" in notes or "primary" in notes):
            links.append((uri, "open", "primary"))
    loc = h.get("electronicLocator") or ""
    # SwePub's primary locator counts only when SwePub flags the record open access; unflagged
    # locators are preview images, errata, summaries or order forms (checked 2026-11-15)
    if (loc and h.get("openAccess") and not loc.startswith("mailto:")
            and not re.search(r"/(PREVIEW|ERRATA|SUMMARY|INSIDE|COVER)\d+\.", loc)
            and not any(u == loc for u, _, _ in links)):
        links.append((loc, "open", "swepub-primary"))
    links.sort(key=lambda x: {"open": 0, "sweden-only": 2}[x[1]])
    return links


T, P = [], []
missing = 0
for rid, h in sorted(hits.items()):
    fn = os.path.join(raw, "swepub", "records", urllib.parse.quote(rid, safe="") + ".json")
    if not os.path.exists(fn):
        missing += 1
        continue
    d = json.load(open(fn))
    w = d.get("instanceOf", {})
    persons = [p for p in (person(c, rid) for c in w.get("contribution", [])) if p]
    five = sorted({c for c in (h["classifications"].get("fiveDigitTopics") or [])})
    three = sorted({c for c in (h["classifications"].get("threeDigitTopics") or [])})
    local = sorted({(s.get("inScheme") or {}).get("code", "") + ":" + "/".join(s.get("prefLabelByLang", {}).values())
                    for s in w.get("subject", []) if (s.get("inScheme") or {}).get("code") not in (None, "svep")})
    svep = sorted({"/".join(s.get("prefLabelByLang", {}).values()) for s in w.get("subject", [])
                   if (s.get("inScheme") or {}).get("code") == "svep"})
    titles = w.get("hasTitle", [{}])
    sub = titles[0].get("subtitle", "") if titles else ""
    inst, basis = degree_place(d, h, w, persons)
    links = fulltext(d, h)
    first = links[0] if links else ("", "", "")
    host = urllib.parse.urlparse(first[0]).netloc.lower() if first[0] else ""
    emb = [u.get("endDate", "") for u in d.get("usageAndAccessPolicy", []) or [] if u.get("@type") == "Embargo"]
    author = next((p for p in persons if p["role"] == "author"), None)
    roles = C.Counter(p["role"] for p in persons)
    diss = d.get("dissertation") or [{}]
    T.append({"record_id": rid, "duplicate_ids": " ".join(h.get("duplicateIds") or []),
              "urn": h.get("archiveURI") or "", "in_list": "+".join(sorted(lists[rid])),
              "source": "+".join(h["source"]),
              "author": f'{author["family"]}, {author["given"]}' if author else "",
              "author_orcid": author["orcid"] if author else "",
              "author_life": author["life_span"] if author else "",
              "title": h["title"], "subtitle": sub, "language": "+".join(h["languages"] or []),
              "year": h["publicationYear"][:4], "defence_date": diss[0].get("date", ""),
              "university_code": inst, "university": INST.get(inst, inst), "university_basis": basis,
              "ssif5": " ".join(five), "ssif3": " ".join(three), "autoclassified": h["autoclassified"],
              "local_subjects": " | ".join(local), "svep": " | ".join(svep),
              "keywords": " | ".join((h.get("keywords") or [])[:12]),
              "n_supervisor": roles["supervisor"], "n_assistant_supervisor": roles["assistant_supervisor"],
              "n_opponent": roles["opponent"], "swepub_open_access": h.get("openAccess"),
              "fulltext_url": first[0], "fulltext_status": first[1], "fulltext_label": first[2],
              "n_fulltext_links": len(links), "host": host, "embargo_end": " ".join(emb),
              "isbn": " ".join(sorted(set(h["ISBN"] or []))), "doi": " ".join(h["DOI"] or []),
              "series": h.get("seriesTitle") or "", "publisher": h.get("publisher") or ""})
    for p in persons:
        p = dict(p)
        p["aff_codes"] = " ".join(p["aff_codes"])
        P.append(p)

os.makedirs(out, exist_ok=True)
for name, rows in (("theses", T), ("people", P)):
    with open(os.path.join(out, f"{name}.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
print(len(T), "theses;", len(P), "person credits;", missing, "list hits without a fetched record")
print(C.Counter(p["role"] for p in P))
