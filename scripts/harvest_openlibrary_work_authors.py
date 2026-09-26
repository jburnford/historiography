"""Fetch Open Library author keys for every work the upstream book enrichment linked.

IDENTITY-PLAN.md step 2.3. The upstream enrichment saved `ol_work_olid` but not the work's
authors. Open Library's search API accepts a batched `key:(... OR ...)` filter, so 36.6k
works need a few hundred requests instead of one per work. Each page is cached under
`<out>/pages/` by the SHA-256 of its key list; reruns skip cached pages. One request per
second, one worker. Output: `work-authors.tsv.gz` (work, title, subtitle, first year,
author position, author key, author name) plus `manifest.json`.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

UPSTREAM = Path("/home/jic823/hnet-reviews/data/export/catalog.duckdb")
FIELDS = "key,title,subtitle,author_key,author_name,first_publish_year"
UA = "historiography-identity-registry/1.0 (+https://github.com/jburnford/historiography)"


def fetch(keys, tries=4):
    q = "key:(" + " OR ".join(f'"/works/{k}"' for k in keys) + ")"
    url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(
        {"q": q, "fields": FIELDS, "limit": len(keys)})
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 - retry any transport/HTTP failure
            if attempt == tries - 1:
                raise
            time.sleep(10 * (attempt + 1))
            print(f"retry after {e}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("data/person-registry/generated/openlibrary"))
    ap.add_argument("--batch", type=int, default=100)
    args = ap.parse_args()
    pages = args.out / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(UPSTREAM), read_only=True)
    works = [r[0] for r in con.execute(
        "SELECT DISTINCT ol_work_olid FROM books WHERE ol_work_olid IS NOT NULL AND ol_work_olid <> '' ORDER BY 1").fetchall()]
    con.close()
    fetched = 0
    rows, found = [], set()
    for i in range(0, len(works), args.batch):
        keys = works[i:i + args.batch]
        page = pages / (hashlib.sha256("\n".join(keys).encode()).hexdigest() + ".json")
        if not page.exists():
            data = fetch(keys)
            tmp = page.with_suffix(".part")
            tmp.write_text(json.dumps(data, ensure_ascii=False))
            tmp.rename(page)
            fetched += 1
            time.sleep(1)
            if fetched % 25 == 0:
                print(f"{i + len(keys)}/{len(works)} works", flush=True)
        for d in json.loads(page.read_text())["docs"]:
            w = d["key"].rsplit("/", 1)[-1]
            found.add(w)
            for pos, (k, n) in enumerate(zip(d.get("author_key") or [], d.get("author_name") or []), 1):
                rows.append((w, d.get("title") or "", d.get("subtitle") or "",
                             str(d.get("first_publish_year") or ""), pos, k, n))
    with gzip.open(args.out / "work-authors.tsv.gz", "wt", encoding="utf-8") as f:
        f.write("work\ttitle\tsubtitle\tfirst_year\tposition\tauthor_key\tauthor_name\n")
        for r in rows:
            f.write("\t".join(" ".join(str(x).split()) for x in r) + "\n")
    manifest = {"retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "works_requested": len(works), "works_returned": len(found),
                "missing_works": sorted(set(works) - found), "author_rows": len(rows),
                "pages": len(list(pages.glob("*.json"))), "fields": FIELDS}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print({k: v for k, v in manifest.items() if k != "missing_works"}, "missing:", len(manifest["missing_works"]))


if __name__ == "__main__":
    main()
