#!/usr/bin/env python3
"""Mine the ORCID public API for every ORCID iD in the Wikidata historian set.

Reads the harvest CSV (qid, name, orcid, ...), fetches each ORCID /record from
the public API, caches raw JSON, and emits an enriched CSV with names,
keywords, employers (+ROR), education, country, and works count.

Read-only against ORCID. Resumable: cached records are not re-fetched.

Usage:
    python3 scripts/mine_orcid_records.py \
        [in.csv] [out.csv]
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://pub.orcid.org/v3.0"
UA = "historiography-research/1.0 (mailto:jic823@usask.ca)"
DELAY = 0.22          # ~4.5 req/s, polite for the public API
CACHE = "data/orcid-2026-09-21/records"


def fetch(orcid, retries=4):
    url = f"{BASE}/{orcid}/record"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "404"
            if e.code == 429:                      # rate limited: back off hard
                wait = 10 * (attempt + 1)
                print(f"  429 on {orcid}, sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if attempt == retries - 1:
                return None, f"http{e.code}"
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            if attempt == retries - 1:
                return None, str(e)[:40]
            time.sleep(3 * (attempt + 1))
    return None, "retries"


def extract(rec):
    """Flatten the fields useful for people-grounding."""
    person = rec.get("person") or {}
    name = person.get("name") or {}
    given = (name.get("given-names") or {}).get("value", "") if name else ""
    family = (name.get("family-name") or {}).get("value", "") if name else ""
    credit = (name.get("credit-name") or {}).get("value", "") if name else ""
    kws = [k.get("content", "") for k in
           (person.get("keywords") or {}).get("keyword", [])]
    countries = [(c.get("country") or {}).get("value", "") for c in
                 (person.get("addresses") or {}).get("address", [])]
    bio = bool((person.get("biography") or {}).get("content"))

    acts = rec.get("activities-summary") or {}

    def orgs(section):
        out = []
        for g in (acts.get(section) or {}).get("affiliation-group", []):
            for s in g.get("summaries", []):
                key = section[:-1] + "-summary"   # employment-summary, education-summary
                e = s.get(key, {})
                org = (e.get("organization") or {})
                nm = org.get("name", "")
                ror = ""
                did = (org.get("disambiguated-organization") or {})
                if did.get("disambiguation-source") == "ROR":
                    ror = did.get("disambiguated-organization-identifier", "")
                out.append(f"{nm}~{ror}" if ror else nm)
        return out

    employers = orgs("employments")
    educations = orgs("educations")
    works = len((acts.get("works") or {}).get("group", []))
    return {
        "given": given, "family": family, "credit": credit,
        "keywords": " | ".join(k for k in kws if k),
        "countries": " | ".join(c for c in countries if c),
        "has_bio": bio,
        "employers": " | ".join(employers),
        "educations": " | ".join(educations),
        "works": works,
    }


def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "data/orcid-2026-09-21/wikidata-historians-orcid.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/orcid-2026-09-21/historians-orcid-enriched.csv"
    os.makedirs(CACHE, exist_ok=True)

    with open(inp) as f:
        base = list(csv.DictReader(f))
    print(f"{len(base)} rows to mine", file=sys.stderr)

    fields = ["qid", "name", "orcid", "birth_year", "death_year",
              "wd_employers", "wd_countries",
              "orcid_given", "orcid_family", "orcid_credit",
              "orcid_keywords", "orcid_countries", "orcid_has_bio",
              "orcid_employers", "orcid_educations", "orcid_works", "status"]
    fout = open(out, "w", newline="")
    w = csv.DictWriter(fout, fieldnames=fields)
    w.writeheader()

    done = miss = 0
    for i, row in enumerate(base, 1):
        orcid = (row.get("orcid") or "").strip()
        cachef = os.path.join(CACHE, f"{orcid}.json")
        status = "ok"
        rec = None
        if orcid and os.path.exists(cachef):
            try:
                rec = json.load(open(cachef))
                status = "cache"
            except Exception:
                rec = None
        if rec is None and orcid:
            rec, err = fetch(orcid)
            if rec is not None:
                json.dump(rec, open(cachef, "w"))
            else:
                status = err or "err"
            time.sleep(DELAY)

        e = extract(rec) if rec else {k: "" for k in
              ("given", "family", "credit", "keywords", "countries",
               "has_bio", "employers", "educations", "works")}
        if rec:
            done += 1
        else:
            miss += 1
        w.writerow({
            "qid": row.get("qid", ""), "name": row.get("name", ""),
            "orcid": orcid, "birth_year": row.get("birth_year", ""),
            "death_year": row.get("death_year", ""),
            "wd_employers": row.get("employers", ""),
            "wd_countries": row.get("countries", ""),
            "orcid_given": e["given"], "orcid_family": e["family"],
            "orcid_credit": e["credit"], "orcid_keywords": e["keywords"],
            "orcid_countries": e["countries"], "orcid_has_bio": e["has_bio"],
            "orcid_employers": e["employers"], "orcid_educations": e["educations"],
            "orcid_works": e["works"], "status": status,
        })
        if i % 250 == 0:
            fout.flush()
            print(f"  {i}/{len(base)}  ok={done} miss={miss}", file=sys.stderr)

    fout.close()
    print(f"DONE {len(base)} rows -> {out}  (ok={done}, miss={miss})", file=sys.stderr)


if __name__ == "__main__":
    main()
