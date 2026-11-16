#!/usr/bin/env python3
"""Harvest one DiVA OAI-PMH set (ListRecords) to OUTDIR, page by page.
Honours DiVA robots.txt Crawl-delay: 10 s between requests. Generic UA, no contact details.
Stops on any non-200, non-XML body or OAI error. Usage: harvest_diva_oai.py OUTDIR SET PREFIX"""
import os, re, sys, time, urllib.parse, urllib.request
BASE = "https://www.diva-portal.org/dice/oai"
UA = "Mozilla/5.0 (compatible; research-metadata-pilot)"
out, setspec, prefix = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, "harvest.log"), "a")
tokfile = os.path.join(out, "resume.token")
tok = open(tokfile).read().strip() if os.path.exists(tokfile) else None
page = len([f for f in os.listdir(out) if f.startswith("page-")])
while True:
    q = {"verb": "ListRecords", "resumptionToken": tok} if tok else {"verb": "ListRecords", "metadataPrefix": prefix, "set": setspec}
    url = BASE + "?" + urllib.parse.urlencode(q)
    time.sleep(10)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180) as r:
            body = r.read(); code = r.status
    except urllib.error.HTTPError as e:
        code, body = e.code, b""
    log.write(f"{time.strftime('%FT%TZ', time.gmtime())} {code} {len(body)} {url}\n"); log.flush()
    if code != 200 or not body.lstrip().startswith(b"<?xml"): sys.exit(f"stop: HTTP {code} / non-XML at page {page}")
    t = body.decode("utf-8", "replace")
    if "<error " in t and "noRecordsMatch" not in t: sys.exit("stop: OAI error " + re.search(r"<error[^<]*", t).group(0))
    page += 1
    open(os.path.join(out, f"page-{page:04d}.xml"), "wb").write(body)
    m = re.search(r"<resumptionToken[^>]*>([^<]+)</resumptionToken>", t)
    if not m: print("done", page); break
    tok = m.group(1); open(tokfile, "w").write(tok)
    if page % 20 == 0: print(page, re.search(r'cursor="(\d+)"', t).group(1), flush=True)
