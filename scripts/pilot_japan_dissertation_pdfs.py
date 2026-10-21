#!/usr/bin/env python3
"""Pilot check of declared full-text files for Japanese History doctoral theses.

Picks up to N records per repository host (top hosts by open full text among
history-labelled records, or hosts given with --hosts), checks robots.txt for
each host, downloads the declared files (full text and, for comparison, the
summary files of a few summary-only records) and verifies %PDF / %%EOF /
pdfinfo page count. No bulk download: --max-total caps the pilot (default 20
records).

Output PDFs: data/field-research/dissertation-citations-2026-10-11/pdf/japan/<slug>/
Log:         P/logs/pilot-pdfs.jsonl and P/pilot-pdfs.csv

Politeness: >= 5 s between requests to any one repository host, robots.txt
honoured (including Crawl-delay), stop a host on 403/429 or a challenge page.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

UA = "HistoriographyMetadataHarvest/1.0 (public dissertation metadata research)"
PDF_ROOT = Path("data/field-research/dissertation-citations-2026-10-11/pdf/japan")
HOST_DELAY = 5.0


class HostGate:
    def __init__(self):
        self.robots = {}
        self.last = collections.defaultdict(float)
        self.blocked = set()

    def robot(self, host):
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            url = f"https://{host}/robots.txt"
            try:
                self.wait(host, HOST_DELAY)
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    rp.parse(r.read().decode("utf-8", "replace").splitlines())
                status = "ok"
            except urllib.error.HTTPError as e:
                status = f"http {e.code}"
                rp.parse([] if e.code == 404 else ["User-agent: *", "Disallow: /"])
            except Exception as e:  # noqa: BLE001
                status = f"error {e}"
                rp.parse(["User-agent: *", "Disallow: /"])
            delay = rp.crawl_delay(UA) or rp.crawl_delay("*") or 0
            self.robots[host] = (rp, max(HOST_DELAY, float(delay)), status)
        return self.robots[host]

    def wait(self, host, delay):
        w = self.last[host] + delay - time.time()
        if w > 0:
            time.sleep(w)
        self.last[host] = time.time()


def pdfinfo_pages(path):
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        return int(m.group(1)) if m else None
    except Exception:  # noqa: BLE001
        return None


DSPACE7_UI = re.compile(r"^(https://[^/]+)/bitstreams/([0-9a-f-]{36})/download$")


def fetch(gate, url, dest):
    # DSpace 7 UI download links return an HTML shell; the REST content URL serves the file
    m = DSPACE7_UI.match(url)
    if m:
        url = f"{m.group(1)}/server/api/core/bitstreams/{m.group(2)}/content"
    host = urllib.parse.urlparse(url).netloc
    if host in gate.blocked:
        return {"status": "host_blocked"}
    rp, delay, rstatus = gate.robot(host)
    if not rp.can_fetch(UA, url):
        return {"status": "robots_disallowed", "robots": rstatus}
    gate.wait(host, delay)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            ctype = r.headers.get("Content-Type")
            final = r.geturl()
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            gate.blocked.add(host)
        return {"status": f"http_{e.code}", "retry_after": e.headers.get("Retry-After")}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)[:200]}
    res = {"status": "fetched", "content_type": ctype, "final_url": final, "bytes": len(data),
           "is_pdf": data[:5] == b"%PDF-", "has_eof": b"%%EOF" in data[-2048:]}
    if not res["is_pdf"]:
        head = data[:400].decode("utf-8", "replace").lower()
        res["status"] = "not_pdf"
        res["login_or_challenge"] = bool(re.search(r"login|shibboleth|captcha|challenge|anubis|sign in", head))
        if res["login_or_challenge"]:
            gate.blocked.add(host)
        return res
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    res["path"] = str(dest)
    res["sha256"] = hashlib.sha256(data).hexdigest()
    res["pages"] = pdfinfo_pages(dest)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="P (folder with records.jsonl)")
    ap.add_argument("--hosts", nargs="*", help="repository hosts to pilot (default: top 5)")
    ap.add_argument("--per-host", type=int, default=4)
    ap.add_argument("--max-total", type=int, default=20)
    ap.add_argument("--ids", nargs="*", help="retry only these record ids (within --hosts)")
    a = ap.parse_args()
    out = Path(a.out)
    rows = [json.loads(l) for l in open(out / "records.jsonl", encoding="utf-8")]
    hist = [r for r in rows if r["history_label"] == "history"]

    def host_of(r):
        urls = [f["url"] for f in r["files"]] or [r["item_url"] or ""]
        return urllib.parse.urlparse(urls[0]).netloc

    recent = [r for r in hist if (r["year"] or 0) >= 2013 and r["files"]]
    by_host = collections.defaultdict(list)
    for r in recent:
        by_host[host_of(r)].append(r)
    # default: the five repositories with the most History records (all years)
    allc = collections.Counter(host_of(r) for r in hist if r["files"])
    hosts = a.hosts or [h for h, _ in allc.most_common(5)]
    only_ids = set(a.ids or [])
    gate = HostGate()
    log = open(out / "logs" / "pilot-pdfs.jsonl", "a", encoding="utf-8")
    table = []
    total = 0
    order = {"open_fulltext_declared": 0, "fulltext_declared_restricted": 0, "files_unlabelled": 1,
             "summary_only": 2}
    for h in hosts:
        cands = sorted(by_host.get(h, []), key=lambda r: (order.get(r["access_category"], 3),
                                                            -(r["year"] or 0), r["id"]))
        picks, seen_cat = [], collections.Counter()
        for r in cands:  # at most 2 per access category, spread over categories
            if seen_cat[r["access_category"]] < 2 and len(picks) < a.per_host:
                picks.append(r)
                seen_cat[r["access_category"]] += 1
        for r in cands:
            if len(picks) >= a.per_host:
                break
            if r not in picks:
                picks.append(r)
        if only_ids:
            picks = [r for r in by_host.get(h, []) if r["id"] in only_ids]
        for r in picks:
            if total >= a.max_total:
                break
            total += 1
            for i, f in enumerate(r["files"][:4]):
                u, kind = f["url"], f["kind"]
                safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", r["id"])
                dest = PDF_ROOT / r["institution"] / f"{safe}__{i}_{kind}.pdf"
                res = fetch(gate, u, dest)
                row = {"at": datetime.now(timezone.utc).isoformat(), "id": r["id"],
                       "institution": r["institution"], "grantor": r["grantor"], "host": h,
                       "year": r["year"], "title": r["title"], "mode": r["access_category"],
                       "declared_kind": kind, "object_type": f["object_type"], "file_label": f["label"],
                       "url": u, "robots": gate.robots.get(urllib.parse.urlparse(u).netloc, (None, None, None))[2],
                       **res}
                log.write(json.dumps(row, ensure_ascii=False) + "\n")
                log.flush()
                table.append(row)
                print(json.dumps({k: row.get(k) for k in ("institution", "id", "mode", "declared_kind", "status",
                                                          "pages", "is_pdf", "has_eof", "bytes")},
                                 ensure_ascii=False), flush=True)
    with open(out / "pilot-pdfs.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["institution", "grantor", "host", "id", "year", "title", "mode", "declared_kind", "object_type",
                "file_label", "url",
                "status", "content_type", "bytes", "is_pdf", "has_eof", "pages", "sha256", "path", "robots"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in table:
            w.writerow(row)


if __name__ == "__main__":
    main()
