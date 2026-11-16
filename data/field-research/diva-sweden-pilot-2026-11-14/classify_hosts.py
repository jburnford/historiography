#!/usr/bin/env python3
"""Classify the full-text link host of every thesis from its robots.txt (metadata requests only).

No PDF or landing page is requested. For each distinct host: one GET of /robots.txt.
Resolver links (doi.org, hdl.handle.net, urn.kb.se) are resolved without touching the repository:
DOIs and handles through the handle proxy JSON API, URNs through the resolver's Location header.

Classes (same rule as data/field-research/dnb-germany-harvest-2026-11-14):
  open         robots allows the link path for '*' and names no AI client with a Disallow
  ai-excluded  robots allows '*' but has a group for a named AI client (GPTBot, ClaudeBot, CCBot ...)
               with a Disallow
  browser      robots disallows the path for '*', or robots could not be read (error, 403/429,
               challenge page), or the host is known to challenge (recorded in the note)
  none         no full-text link on the record
Sweden-only links (Stockholm University Press 'not accessible to users outside Sweden') are
kept as their own route 'sweden-only' whatever robots says.

Usage: classify_hosts.py THESES.csv RAW_DIR OUT_HOSTS.csv OUT_ROUTES.csv REQUEST_LOG"""
import csv, json, re, sys, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from datetime import datetime, timezone

theses_csv, raw, out_hosts, out_routes, log = sys.argv[1:6]
UA = "metadata-pilot/1.0"
AI = ["gptbot", "chatgpt-user", "oai-searchbot", "claudebot", "claude-web", "claude-user", "claude-searchbot",
      "anthropic-ai", "ccbot", "google-extended", "perplexitybot", "bytespider", "applebot-extended",
      "meta-externalagent", "facebookbot", "cohere-ai", "diffbot", "omgili", "amazonbot", "ai2bot", "imagesiftbot"]
RESOLVERS = {"doi.org", "dx.doi.org", "hdl.handle.net", "urn.kb.se", "urn.fi"}
last = [0.0]


def get(url, follow=True):
    wait = 1.1 - (time.time() - last[0])
    if wait > 0:
        time.sleep(wait)
    last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with opener.open(req, timeout=20) as r:
            body = r.read(200000)
            status, final, loc = r.status, r.geturl(), r.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        body, status, final, loc = e.read(20000) if e.fp else b"", e.code, url, e.headers.get("Location", "")
    except Exception as e:  # timeout, DNS, TLS
        body, status, final, loc = b"", "error:" + type(e).__name__, url, ""
    with open(log, "a") as f:
        f.write(f"{stamp} {status} {len(body)} {url}\n")
    return status, body.decode("utf-8", "replace"), final, loc


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def resolve(url):
    p = urllib.parse.urlparse(url)
    if p.netloc in ("doi.org", "dx.doi.org", "hdl.handle.net"):
        hid = urllib.parse.unquote(p.path.lstrip("/"))
        api = ("https://doi.org/api/handles/" if "doi" in p.netloc else "https://hdl.handle.net/api/handles/") + hid
        st, body, _, _ = get(api)
        try:
            for v in json.loads(body).get("values", []):
                if v.get("type") == "URL":
                    return v["data"]["value"]
        except Exception:
            pass
        return ""
    if p.netloc == "urn.kb.se" or p.netloc == "urn.fi":
        st, body, _, loc = get(url, follow=False)
        if loc:
            return loc
        m = re.search(r'href="(https?://[^"]+)"', body)
        return m.group(1) if m else ""
    return ""


CACHE = raw + "/hosts/robots"


def classify(host, sample_path):
    import os
    url = f"https://{host}/robots.txt"
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, host + ".json")
    if os.path.exists(cf):
        st, body = json.load(open(cf))
    else:
        st, body, final, _ = get(url)
        json.dump([st, body], open(cf, "w"))
    low = body.lower()
    if st != 200:
        if st == 404:
            return "open", "no robots.txt (404): nothing disallowed", st, "", ""
        return "browser", f"robots.txt not readable ({st})", st, "", ""
    if "<html" in low[:500]:
        if any(w in low for w in ("challenge", "anubis", "cf-chl", "captcha", "just a moment")):
            return "browser", "challenge page instead of robots.txt", st, "", ""
        return "open", "robots.txt answers with an HTML page (no robots file): nothing disallowed", st, "", ""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.splitlines())
    delay = rp.crawl_delay("*") or ""
    groups, cur, rules = [], [], []
    for line in body.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            if rules:
                groups.append((cur, rules)); cur, rules = [], []
            cur.append(v.lower())
        elif k in ("disallow", "allow", "crawl-delay"):
            rules.append((k, v))
    if cur:
        groups.append((cur, rules))
    named = sorted({a for agents, rr in groups for a in agents for ai in AI
                    if ai in a and any(k == "disallow" and v for k, v in rr)})
    star = " ; ".join(f"{k}: {v}" for agents, rr in groups if "*" in agents for k, v in rr)
    if not rp.can_fetch("*", f"https://{host}{sample_path}"):
        return "browser", f"robots disallows {sample_path} for *", st, star, delay
    if named:
        return "ai-excluded", "allows *; disallows named AI clients: " + ", ".join(named), st, star, delay
    return "open", "robots allows the link path for *; no named AI client excluded", st, star, delay


rows = list(csv.DictReader(open(theses_csv)))
resolved = {}
for r in rows:
    if r["host"] in RESOLVERS and r["fulltext_url"]:
        url = r["fulltext_url"]
        for hop in range(2):  # a DOI may point at a URN, which points at the repository
            nxt = resolve(url)
            if not nxt:
                break
            url = nxt
            if urllib.parse.urlparse(url).netloc.lower() not in RESOLVERS:
                break
        resolved[r["record_id"]] = url if url != r["fulltext_url"] else ""
targets = {}
for r in rows:
    url = resolved.get(r["record_id"]) or r["fulltext_url"]
    host = urllib.parse.urlparse(url).netloc.lower() if url else ""
    targets[r["record_id"]] = (url, host)
hosts = {}
for rid, (url, host) in targets.items():
    if host and host not in RESOLVERS:
        hosts.setdefault(host, {"links": 0, "sample": url})
        hosts[host]["links"] += 1
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
out = []
for host, h in sorted(hosts.items(), key=lambda x: -x[1]["links"]):
    path = urllib.parse.urlparse(h["sample"]).path or "/"
    cls, reason, st, star, delay = classify(host, path)
    if host.endswith("diva-portal.org") and cls == "open":
        reason += "; DiVA web pages are known to sit behind bot protection (not tested here)"
    out.append({"host": host, "class": cls, "reason": reason, "robots_url": f"https://{host}/robots.txt",
                "robots_status": st, "rule_text_star": star[:600], "crawl_delay": delay, "checked": now,
                "links": h["links"], "sample_url": h["sample"]})
with open(out_hosts, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
cls = {h["host"]: h["class"] for h in out}
with open(out_routes, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["record_id", "resolved_link", "link_host", "link_kind", "route_class"]); w.writeheader()
    for r in rows:
        url, host = targets[r["record_id"]]
        if not r["fulltext_url"]:
            c = "none"
        elif r["fulltext_status"] == "sweden-only":
            c = "sweden-only"
        elif host in RESOLVERS or not host:
            c = "unresolved"
        else:
            c = cls.get(host, "browser")
        kind = ("" if not url else "file" if re.search(r"(/smash/get/|/ws/files/|/bitstream/|/files/|\.pdf$|/download)", url, re.I)
                else "landing")
        w.writerow({"record_id": r["record_id"], "resolved_link": url if url != r["fulltext_url"] else "",
                    "link_host": host, "link_kind": kind, "route_class": c})
print(len(out), "hosts;", sum(1 for v in resolved.values() if v), "of", len(resolved), "resolver links resolved")
