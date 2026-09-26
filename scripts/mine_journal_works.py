#!/usr/bin/env python3
"""Two-stage ORCID mine for the journal-derived historians: profession profile
PLUS full works detail (BibTeX, abstract, co-authors).

Per person:
  1. /record            -> profile + FULL bio text + Level-1 work summaries
  2. /works/{putcodes}  -> Level-2 detail: citation (BibTeX), short-description
                           (abstract), contributors (co-authors), language

Both raw JSON payloads are cached (records/ and works/) so the flatten step can
be re-run without re-fetching. Emits two tables:
  - journal-profiles.csv : one row per person (incl. bio text, works/bibtex/abstract counts)
  - journal-works.csv     : one row per work (title, journal, year, type, doi, bibtex, abstract, coauthors)

Read-only against ORCID. Resumable. Usage:
    python3 scripts/mine_journal_works.py [in.csv] [profiles.csv] [works.csv]
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = "https://pub.orcid.org/v3.0"
UA = "historiography-research/1.0 (mailto:jic823@usask.ca)"
DELAY = 0.22
REC_CACHE = "data/orcid-2026-09-21/records"
WORK_CACHE = "data/orcid-2026-09-21/works"
csv.field_size_limit(10_000_000)


def get(url, retries=4):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url=req, timeout=60) as r:
                return json.load(r), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "404"
            if e.code == 429:
                time.sleep(10 * (attempt + 1)); continue
            if attempt == retries - 1:
                return None, f"http{e.code}"
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            if attempt == retries - 1:
                return None, str(e)[:30]
            time.sleep(3 * (attempt + 1))
    return None, "retries"


def val(x):
    return (x or {}).get("value", "") if isinstance(x, dict) else ""


def doi_of(work_or_summary):
    for e in ((work_or_summary.get("external-ids") or {}).get("external-id") or []):
        if (e.get("external-id-type") or "").lower() == "doi":
            return e.get("external-id-value", "")
    return ""


def cached_json(path):
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            return None
    return None


def profile(rec):
    person = rec.get("person") or {}
    name = person.get("name") or {}
    acts = rec.get("activities-summary") or {}
    hist = rec.get("history") or {}
    bio = (person.get("biography") or {}).get("content") or ""
    kws = [k.get("content", "") for k in (person.get("keywords") or {}).get("keyword", [])]
    countries = [(a.get("country") or {}).get("value", "") for a in
                 (person.get("addresses") or {}).get("address", [])]
    urls = [val(u.get("url")) for u in
            (person.get("researcher-urls") or {}).get("researcher-url", [])]
    extids = [f"{e.get('external-id-type')}:{e.get('external-id-value')}" for e in
              (person.get("external-identifiers") or {}).get("external-identifier", [])]
    emps = []
    for g in (acts.get("employments") or {}).get("affiliation-group", []):
        for s in g.get("summaries", []):
            e = s.get("employment-summary", {})
            org = e.get("organization") or {}
            did = org.get("disambiguated-organization") or {}
            ror = did.get("disambiguated-organization-identifier", "") \
                if did.get("disambiguation-source") == "ROR" else ""
            emps.append((org.get("name", ""), ror, e.get("department-name", "") or "",
                         e.get("role-title", "") or "",
                         val((e.get("start-date") or {}).get("year")),
                         val((e.get("end-date") or {}).get("year"))))
    cur = ([e for e in emps if not e[5]] or
           sorted(emps, key=lambda e: e[4] or "", reverse=True) or [("",)*6])[0]
    return {
        "given": val(name.get("given-names")), "family": val(name.get("family-name")),
        "credit": val(name.get("credit-name")),
        "country": " | ".join(c for c in countries if c),
        "keywords": " | ".join(k for k in kws if k),
        "bio": bio.replace("\r", " ").replace("\n", " ").strip(),
        "homepage": urls[0] if urls else "", "ext_ids": " | ".join(extids),
        "current_employer": cur[0], "current_ror": cur[1],
        "current_dept": cur[2], "current_role": cur[3], "current_start": cur[4],
        "all_employers": " | ".join(f"{e[0]}~{e[1]}" if e[1] else e[0] for e in emps),
        "claimed": hist.get("claimed") if isinstance(hist.get("claimed"), bool) else "",
    }


def work_summaries(rec):
    """(put_code, year, type, title, journal, doi, url) for each grouped work."""
    out = []
    for g in ((rec.get("activities-summary") or {}).get("works") or {}).get("group", []):
        ws = (g.get("work-summary") or [{}])[0]
        out.append({
            "put_code": ws.get("put-code"),
            "year": ((ws.get("publication-date") or {}).get("year") or {}).get("value", ""),
            "type": ws.get("type", ""),
            "title": val((ws.get("title") or {}).get("title")),
            "journal": val(ws.get("journal-title")),
            "doi": doi_of(ws), "url": val(ws.get("url")),
        })
    return out


def fetch_works_detail(orcid, put_codes):
    """Batch /works/{codes} (<=100 per call), cached. Returns {put_code: detail}."""
    cf = os.path.join(WORK_CACHE, f"{orcid}.json")
    cached = cached_json(cf)
    if cached is not None:
        bulk = cached.get("bulk", [])
    else:
        bulk = []
        for i in range(0, len(put_codes), 100):
            chunk = ",".join(str(c) for c in put_codes[i:i + 100])
            d, _ = get(f"{BASE}/{orcid}/works/{chunk}")
            time.sleep(DELAY)
            if d:
                bulk.extend(d.get("bulk", []))
        json.dump({"bulk": bulk}, open(cf, "w"))
    detail = {}
    for item in bulk:
        w = item.get("work") or {}
        pc = w.get("put-code")
        cit = w.get("citation") or {}
        cons = (w.get("contributors") or {}).get("contributor", [])
        detail[pc] = {
            "citation_type": cit.get("citation-type", ""),
            "citation_value": (cit.get("citation-value") or "").replace("\r", " ").replace("\n", " "),
            "abstract": (w.get("short-description") or "").replace("\r", " ").replace("\n", " "),
            "coauthors": " | ".join(val(c.get("credit-name")) for c in cons if val(c.get("credit-name"))),
            "language": w.get("language-code", "") or "",
        }
    return detail


def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "data/orcid-2026-09-21/journal-orcids-netnew.csv"
    pout = sys.argv[2] if len(sys.argv) > 2 else "data/orcid-2026-09-21/journal-profiles.csv"
    wout = sys.argv[3] if len(sys.argv) > 3 else "data/orcid-2026-09-21/journal-works.csv"
    os.makedirs(REC_CACHE, exist_ok=True)
    os.makedirs(WORK_CACHE, exist_ok=True)
    rows = list(csv.DictReader(open(inp)))
    print(f"{len(rows)} ORCIDs to mine (records + works detail)", file=sys.stderr, flush=True)

    pcols = (list(rows[0].keys()) if rows else ["orcid"]) + [
        "given", "family", "credit", "country", "keywords", "bio", "homepage",
        "ext_ids", "current_employer", "current_ror", "current_dept",
        "current_role", "current_start", "all_employers", "claimed",
        "n_works", "latest_year", "work_types", "n_bibtex", "n_abstract", "status"]
    wcols = ["orcid", "name", "put_code", "year", "type", "title", "journal",
             "doi", "url", "citation_type", "bibtex", "abstract", "coauthors", "language"]
    pf = open(pout, "w", newline=""); pw = csv.DictWriter(pf, fieldnames=pcols); pw.writeheader()
    wf = open(wout, "w", newline=""); ww = csv.DictWriter(wf, fieldnames=wcols); ww.writeheader()

    ok = miss = total_works = 0
    for i, row in enumerate(rows, 1):
        orcid = (row.get("orcid") or "").strip()
        rcf = os.path.join(REC_CACHE, f"{orcid}.json")
        rec = cached_json(rcf); status = "cache" if rec else "ok"
        if rec is None and orcid:
            rec, status = get(f"{BASE}/{orcid}/record")
            if rec:
                json.dump(rec, open(rcf, "w"))
            time.sleep(DELAY)
        if not rec:
            miss += 1
            pw.writerow({**row, **{c: "" for c in pcols if c not in row}, "status": status})
            continue
        ok += 1
        prof = profile(rec)
        summ = work_summaries(rec)
        codes = [s["put_code"] for s in summ if s["put_code"] is not None]
        detail = fetch_works_detail(orcid, codes) if codes else {}
        name = f"{prof['given']} {prof['family']}".strip() or prof["credit"]
        years, types, nbib, nabs = [], Counter(), 0, 0
        for s in summ:
            d = detail.get(s["put_code"], {})
            if s["year"]: years.append(s["year"])
            if s["type"]: types[s["type"]] += 1
            is_bib = "bibtex" in (d.get("citation_type", "") or "").lower()
            if is_bib: nbib += 1
            if d.get("abstract"): nabs += 1
            ww.writerow({
                "orcid": orcid, "name": name, "put_code": s["put_code"],
                "year": s["year"], "type": s["type"], "title": s["title"],
                "journal": s["journal"], "doi": s["doi"], "url": s["url"],
                "citation_type": d.get("citation_type", ""),
                "bibtex": d.get("citation_value", "") if is_bib else "",
                "abstract": d.get("abstract", ""), "coauthors": d.get("coauthors", ""),
                "language": d.get("language", ""),
            })
            total_works += 1
        pw.writerow({**row, **prof, "n_works": len(summ),
                     "latest_year": max(years) if years else "",
                     "work_types": ";".join(f"{t}:{c}" for t, c in types.most_common()),
                     "n_bibtex": nbib, "n_abstract": nabs, "status": status})
        if i % 300 == 0:
            pf.flush(); wf.flush()
            print(f"  {i}/{len(rows)} people  ok={ok} miss={miss} works={total_works}",
                  file=sys.stderr, flush=True)
    pf.close(); wf.close()
    print(f"DONE people={len(rows)} ok={ok} miss={miss} works={total_works}\n"
          f"  -> {pout}\n  -> {wout}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
