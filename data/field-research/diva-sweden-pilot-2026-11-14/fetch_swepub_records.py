#!/usr/bin/env python3
"""Fetch SwePub deduplicated JSON-LD records (one GET per record) for the ids in SwePub
Bibliometrics API result files. Polite: one client, >=1.1 s between requests, generic UA,
stops on any 403/429/5xx or a non-JSON (challenge) body. Raw records go to OUTDIR (E:, never git).
Usage: fetch_swepub_records.py OUTDIR result.json [result.json ...]"""
import json, os, sys, time, urllib.parse, urllib.request
BASE = "https://bibliometri.swepub.kb.se/api/v2/bibliometrics/publications/"
UA = "Mozilla/5.0 (compatible; research-metadata-pilot)"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, "fetch.log"), "a")
ids = []
for f in sys.argv[2:]:
    for h in json.load(open(f))["hits"]:
        if h["recordId"] not in ids: ids.append(h["recordId"])
for i, rid in enumerate(ids):
    fn = os.path.join(out, urllib.parse.quote(rid, safe="") + ".json")
    if os.path.exists(fn): continue
    time.sleep(1.1)
    req = urllib.request.Request(BASE + urllib.parse.quote(rid, safe=":"), headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read(); code = r.status
    except urllib.error.HTTPError as e:
        code = e.code; body = b""
    log.write(f"{time.strftime('%FT%TZ', time.gmtime())} {code} {len(body)} {rid}\n"); log.flush()
    if code == 404: continue
    if code != 200: sys.exit(f"stop: HTTP {code} on {rid}")
    try: json.loads(body)
    except Exception: sys.exit(f"stop: non-JSON body on {rid} (challenge?)")
    open(fn, "wb").write(body)
    if i % 100 == 0: print(i, len(ids), flush=True)
print("done", len(ids))
