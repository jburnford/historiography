#!/usr/bin/env python3
"""DNB metadata pilot: pull History-classified dissertation records from the
Deutsche Nationalbibliothek SRU service, one publication year at a time.

Network only, polite: one client, one request at a time, >= 1.1 s apart,
generic User-Agent with no contact details. Stops on any HTTP status other
than 200, on a Retry-After header, or on a non-SRU response (captcha / bot wall).
Raw MARC21-xml pages are written to the output directory (bulk drive, never git).

Usage:
  python3 scripts/dnb_history_diss_pilot.py --out /mnt/e/dnb-history-diss-2026-11-14 \
      --from-year 2015 --to-year 2025

The metadata is CC0 1.0 (DNB, "Business model for metadata services",
https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/geschaeftsmodell.html).
"""
import argparse
import datetime as dt
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

SRU = "https://services.dnb.de/sru/dnb"
UA = "metadata-pilot/1.0"
HISTORY = (
    "((sgt=900 or sgt=930 or sgt=940 or sgt=943 or sgt=950 or sgt=960 or sgt=970"
    " or sgt=980 or sgt=990) or (ddc=90* or ddc=93* or ddc=94* or ddc=95* or ddc=96*"
    " or ddc=97* or ddc=98* or ddc=99*))"
)
PAGE = 100
GAP = 1.1


def query_for(year: int) -> str:
    # Same Boolean union as the 2026-11-06 Germany scout, one publication year.
    return f"hss=diss* and jhr={year} and {HISTORY}"


def fetch(url: str, log) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        status = r.status
        retry = r.headers.get("Retry-After")
    log.write(f"{dt.datetime.now(dt.timezone.utc).isoformat()}\t{status}\t{len(body)}\t{time.time()-t0:.2f}s\t{url}\n")
    log.flush()
    if status != 200 or retry:
        sys.exit(f"STOP: status {status}, Retry-After {retry} for {url}")
    if b"searchRetrieveResponse" not in body[:2000]:
        sys.exit(f"STOP: not an SRU response (possible block) for {url}")
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--from-year", type=int, default=2015)
    ap.add_argument("--to-year", type=int, default=2025)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    log = open(out / "requests.log", "a", encoding="utf-8")
    for year in range(a.from_year, a.to_year + 1):
        q = query_for(year)
        start, total = 1, None
        while total is None or start <= total:
            path = out / "raw" / f"{year}-{start:05d}.xml"
            if path.exists():
                body = path.read_bytes()
            else:
                params = {
                    "version": "1.1",
                    "operation": "searchRetrieve",
                    "query": q,
                    "recordSchema": "MARC21-xml",
                    "maximumRecords": str(PAGE),
                    "startRecord": str(start),
                }
                url = SRU + "?" + urllib.parse.urlencode(params)
                body = fetch(url, log)
                path.write_bytes(body)
                time.sleep(GAP)
            m = re.search(rb"<numberOfRecords>(\d+)</numberOfRecords>", body)
            total = int(m.group(1)) if m else 0
            if start == 1:
                print(f"{year}: {total} records", flush=True)
            start += PAGE


if __name__ == "__main__":
    main()
