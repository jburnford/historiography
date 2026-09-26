#!/usr/bin/env python3
"""Mine the ORCID public API for the journal-derived historian ORCIDs.

Richer than mine_orcid_records.py (which was tuned for a QID crosswalk): this
captures a profession profile -- name variants, country, keywords, homepage,
external-id cross-links, current + all employment (org/ROR/dept/role/dates),
education, works (count + latest year + type breakdown), and counts of
peer-reviews, memberships, services, distinctions, fundings, plus account
claimed/last-modified.

Reads an input CSV with an `orcid` column. Read-only against ORCID. Resumable:
raw JSON cached per iD (cache shared with the Wikidata-set run).

Usage:
    python3 scripts/mine_journal_orcids.py [in.csv] [out.csv]
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
CACHE = "data/orcid-2026-09-21/records"


def fetch(orcid, retries=4):
    req = urllib.request.Request(f"{BASE}/{orcid}/record",
        headers={"Accept": "application/json", "User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
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


def affiliations(acts, section, key):
    """Yield (org, ror, dept, role, start_year, end_year) per affiliation."""
    for g in (acts.get(section) or {}).get("affiliation-group", []):
        for s in g.get("summaries", []):
            e = s.get(key, {})
            org = e.get("organization") or {}
            did = org.get("disambiguated-organization") or {}
            ror = did.get("disambiguated-organization-identifier", "") \
                if did.get("disambiguation-source") == "ROR" else ""
            sd, ed = e.get("start-date") or {}, e.get("end-date") or {}
            yield (org.get("name", ""), ror, e.get("department-name", "") or "",
                   e.get("role-title", "") or "",
                   val(sd.get("year")), val(ed.get("year")))


def extract(rec):
    person = rec.get("person") or {}
    name = person.get("name") or {}
    acts = rec.get("activities-summary") or {}
    hist = rec.get("history") or {}

    othernames = [val(o) for o in (person.get("other-names") or {}).get("other-name", [])]
    kws = [k.get("content", "") for k in (person.get("keywords") or {}).get("keyword", [])]
    countries = [(a.get("country") or {}).get("value", "") for a in
                 (person.get("addresses") or {}).get("address", [])]
    urls = [val(u.get("url")) for u in
            (person.get("researcher-urls") or {}).get("researcher-url", [])]
    extids = [f"{e.get('external-id-type')}:{e.get('external-id-value')}" for e in
              (person.get("external-identifiers") or {}).get("external-identifier", [])]

    emps = list(affiliations(acts, "employments", "employment-summary"))
    # current employer = one with no end year, else the latest-starting
    current = [e for e in emps if not e[5]]
    cur = (current or sorted(emps, key=lambda e: e[4] or "", reverse=True) or [("",)*6])[0]
    edus = list(affiliations(acts, "educations", "education-summary"))

    wgroups = (acts.get("works") or {}).get("group", [])
    wyears, wtypes = [], Counter()
    for grp in wgroups:
        ws = (grp.get("work-summary") or [{}])[0]
        y = ((ws.get("publication-date") or {}).get("year") or {}).get("value", "")
        if y:
            wyears.append(y)
        if ws.get("type"):
            wtypes[ws["type"]] += 1

    def n(sec, sub="affiliation-group"):
        return len((acts.get(sec) or {}).get(sub, []))

    return {
        "given": val(name.get("given-names")),
        "family": val(name.get("family-name")),
        "credit": val(name.get("credit-name")),
        "other_names": " | ".join(o for o in othernames if o),
        "country": " | ".join(c for c in countries if c),
        "keywords": " | ".join(k for k in kws if k),
        "has_bio": bool((person.get("biography") or {}).get("content")),
        "homepage": urls[0] if urls else "",
        "ext_ids": " | ".join(extids),
        "current_employer": cur[0], "current_ror": cur[1],
        "current_dept": cur[2], "current_role": cur[3], "current_start": cur[4],
        "all_employers": " | ".join(f"{e[0]}~{e[1]}" if e[1] else e[0] for e in emps),
        "educations": " | ".join(e[0] for e in edus),
        "works": len(wgroups),
        "latest_work_year": max(wyears) if wyears else "",
        "work_types": ";".join(f"{t}:{c}" for t, c in wtypes.most_common()),
        "peer_reviews": n("peer-reviews", "group"),
        "memberships": n("memberships"), "services": n("services"),
        "distinctions": n("distinctions"), "fundings": n("fundings", "group"),
        "claimed": (hist.get("claimed") if isinstance(hist.get("claimed"), bool) else ""),
        "last_modified": val(hist.get("last-modified-date")),
    }


EMPTY = {k: "" for k in ("given", "family", "credit", "other_names", "country",
    "keywords", "has_bio", "homepage", "ext_ids", "current_employer",
    "current_ror", "current_dept", "current_role", "current_start",
    "all_employers", "educations", "works", "latest_work_year", "work_types",
    "peer_reviews", "memberships", "services", "distinctions", "fundings",
    "claimed", "last_modified")}


def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "data/orcid-2026-09-21/journal-orcids-netnew.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/orcid-2026-09-21/journal-orcids-enriched.csv"
    os.makedirs(CACHE, exist_ok=True)
    rows = list(csv.DictReader(open(inp)))
    print(f"{len(rows)} ORCIDs to mine", file=sys.stderr, flush=True)

    base_fields = list(rows[0].keys()) if rows else ["orcid"]
    fields = base_fields + list(EMPTY.keys()) + ["status"]
    fout = open(out, "w", newline="")
    w = csv.DictWriter(fout, fieldnames=fields)
    w.writeheader()

    ok = miss = 0
    for i, row in enumerate(rows, 1):
        orcid = (row.get("orcid") or "").strip()
        cf = os.path.join(CACHE, f"{orcid}.json")
        rec, status = None, "ok"
        if orcid and os.path.exists(cf):
            try:
                rec = json.load(open(cf)); status = "cache"
            except Exception:
                rec = None
        if rec is None and orcid:
            rec, status = fetch(orcid)
            if rec is not None:
                json.dump(rec, open(cf, "w"))
            time.sleep(DELAY)
        e = extract(rec) if rec else dict(EMPTY)
        if rec: ok += 1
        else: miss += 1
        w.writerow({**row, **e, "status": status})
        if i % 500 == 0:
            fout.flush()
            print(f"  {i}/{len(rows)} ok={ok} miss={miss}", file=sys.stderr, flush=True)
    fout.close()
    print(f"DONE {len(rows)} -> {out} (ok={ok}, miss={miss})", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
