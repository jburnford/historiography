"""Harvest Wikidata human -> authority-identifier pairs from QLever, one property per file.

Step 2.1 of IDENTITY-PLAN.md: a bulk crosswalk so that any credit already carrying an
ORCID, VIAF, LCNAF, GND, ISNI, Open Library, Scopus, BnF or IdRef identifier resolves to
a QID by identifier equality, never by name. Truthy (wdt:) values only; deprecated
statements are excluded by QLever's truthy semantics.

Each property is streamed to `<out>/<PID>.tsv.gz` (qid, value), then checked against a
live COUNT taken immediately before the download. Completed properties are recorded in
`manifest.json` with row count, SHA-256 and retrieval time and are skipped on rerun.
One request at a time.
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

ENDPOINT = "https://qlever.dev/api/wikidata"
PROPERTIES = {
    "P496": "orcid",
    "P214": "viaf",
    "P244": "lcnaf",
    "P227": "gnd",
    "P213": "isni",
    "P648": "openlibrary",
    "P1153": "scopus",
    "P268": "bnf",
    "P269": "idref",
}
PREFIX = ("PREFIX wd: <http://www.wikidata.org/entity/> "
          "PREFIX wdt: <http://www.wikidata.org/prop/direct/> ")


def post(query, timeout=1800):
    data = urllib.parse.urlencode({"query": PREFIX + query}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={
        "Accept": "text/tab-separated-values",
        "User-Agent": "historiography-identity-registry/1.0 (research; single worker)",
    })
    return urllib.request.urlopen(req, timeout=timeout)


def count(pid):
    with post(f"SELECT (COUNT(*) AS ?n) WHERE {{ ?h wdt:P31 wd:Q5 ; wdt:{pid} ?v }}", 300) as r:
        return int(r.read().decode().strip().splitlines()[-1])


def harvest(pid, out):
    expected = count(pid)
    tmp = out / f"{pid}.tsv.gz.part"
    rows, digest = 0, hashlib.sha256()
    with post(f"SELECT ?h ?v WHERE {{ ?h wdt:P31 wd:Q5 ; wdt:{pid} ?v }}") as r, \
            gzip.open(tmp, "wt", encoding="utf-8", newline="") as w:
        r.readline()  # header
        w.write("qid\tvalue\n")
        for raw in r:
            line = raw.decode("utf-8").rstrip("\n")
            if not line:
                continue
            h, v = line.split("\t", 1)
            qid = h.strip("<>").rsplit("/", 1)[-1]
            value = v[1:v.rindex('"')] if v.startswith('"') else v
            rec = f"{qid}\t{value}\n"
            w.write(rec)
            digest.update(rec.encode())
            rows += 1
    if rows != expected:
        raise RuntimeError(f"{pid}: downloaded {rows} rows, live count {expected}; kept {tmp}")
    tmp.rename(out / f"{pid}.tsv.gz")
    return {"property": pid, "scheme": PROPERTIES[pid], "rows": rows,
            "rows_sha256": digest.hexdigest(),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "endpoint": ENDPOINT, "filter": "wdt:P31 wd:Q5 (truthy)"}


def harvest_lifespans(out):
    """Birth/death years for humans carrying an Open Library or ORCID ID (plausibility gate)."""
    body = ("{ ?h wdt:P31 wd:Q5 . { ?h wdt:P648 [] } UNION { ?h wdt:P496 [] } } "
            "OPTIONAL { ?h wdt:P569 ?b } OPTIONAL { ?h wdt:P570 ?d }")
    select = "SELECT ?h (MIN(YEAR(?b)) AS ?by) (MAX(YEAR(?d)) AS ?dy) WHERE { " + body + " } GROUP BY ?h"
    with post(f"SELECT (COUNT(DISTINCT ?h) AS ?n) WHERE {{ {body} }}", 600) as r:
        expected = int(r.read().decode().strip().splitlines()[-1])
    rows = 0
    tmp = out / "lifespans.tsv.gz.part"
    with post(select) as r, gzip.open(tmp, "wt", encoding="utf-8") as w:
        r.readline()
        w.write("qid\tbirth_year\tdeath_year\n")
        for raw in r:
            parts = raw.decode("utf-8").rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            year = lambda v: v.split('"')[1] if v.startswith('"') else v
            w.write(f"{parts[0].strip('<>').rsplit('/', 1)[-1]}\t{year(parts[1])}\t{year(parts[2])}\n")
            rows += 1
    if rows != expected:
        raise RuntimeError(f"lifespans: {rows} rows, live count {expected}; kept {tmp}")
    tmp.rename(out / "lifespans.tsv.gz")
    return {"rows": rows, "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "filter": "humans with P648 or P496; min birth year, max death year"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("data/person-registry/generated/wikidata-authorities"))
    ap.add_argument("--only", nargs="*", choices=sorted(PROPERTIES))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for pid in args.only or PROPERTIES:
        if pid in manifest and (args.out / f"{pid}.tsv.gz").exists():
            print(f"{pid}: done ({manifest[pid]['rows']} rows), skipping")
            continue
        t = time.time()
        manifest[pid] = harvest(pid, args.out)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"{pid}: {manifest[pid]['rows']} rows in {time.time() - t:.0f}s", flush=True)
        time.sleep(2)
    lifespan_path = args.out / "lifespans-manifest.json"
    if not (args.out / "lifespans.tsv.gz").exists():
        lifespan_path.write_text(json.dumps(harvest_lifespans(args.out), indent=2) + "\n")
        print("lifespans:", json.loads(lifespan_path.read_text())["rows"], "rows", flush=True)


if __name__ == "__main__":
    main()
