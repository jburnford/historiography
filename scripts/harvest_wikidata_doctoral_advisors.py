"""Harvest Wikidata doctoral-advisor statements (P184) for humans from QLever.

Input to the registry's `aha_dissertation` route: an AHA dissertation whose listed advisor
matches the person's Wikidata doctoral advisor is "advisor named in a known source" evidence.
Truthy (wdt:) values only. English advisor label where one exists, else none (the route then
cannot use the row). One request, checked against a live COUNT taken just before the download.

Writes data/person-registry/generated/wikidata-doctoral/P184.tsv.gz (qid, advisor_qid,
advisor_label) and manifest.json (rows, SHA-256 of rows, retrieval time). Refuses to overwrite.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

from harvest_wikidata_authorities import ENDPOINT, post

ROOT = Path(__file__).resolve().parents[1]
BODY = "?h wdt:P31 wd:Q5 ; wdt:P184 ?a . OPTIONAL { ?a rdfs:label ?l FILTER(LANG(?l) = \"en\") }"
RDFS = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "data/person-registry/generated/wikidata-doctoral")
    args = ap.parse_args()
    target = args.out / "P184.tsv.gz"
    if target.exists():
        raise SystemExit(f"{target} exists; move it aside to re-harvest")
    args.out.mkdir(parents=True, exist_ok=True)
    with post(RDFS + "SELECT (COUNT(*) AS ?n) WHERE { ?h wdt:P31 wd:Q5 ; wdt:P184 ?a }", 600) as r:
        expected = int(r.read().decode().strip().splitlines()[-1])
    rows, digest, pairs = 0, hashlib.sha256(), set()
    tmp = args.out / "P184.tsv.gz.part"
    with post(RDFS + f"SELECT ?h ?a (SAMPLE(?l) AS ?label) WHERE {{ {BODY} }} GROUP BY ?h ?a") as r, \
            gzip.open(tmp, "wt", encoding="utf-8", newline="") as w:
        r.readline()
        w.write("qid\tadvisor_qid\tadvisor_label\n")
        for raw in r:
            parts = raw.decode("utf-8").rstrip("\n").split("\t")
            if len(parts) < 2 or not parts[0]:
                continue
            q = lambda v: v.strip("<>").rsplit("/", 1)[-1]
            label = parts[2] if len(parts) > 2 else ""
            label = label[1:label.rindex('"')] if label.startswith('"') else ""
            rec = f"{q(parts[0])}\t{q(parts[1])}\t{label.replace(chr(9), ' ')}\n"
            w.write(rec)
            digest.update(rec.encode())
            pairs.add((parts[0], parts[1]))
            rows += 1
    if len(pairs) != expected:
        raise SystemExit(f"P184: {len(pairs)} distinct pairs, live count {expected}; kept {tmp}")
    tmp.rename(target)
    manifest = {"property": "P184", "rows": rows, "rows_sha256": digest.hexdigest(),
                "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "endpoint": ENDPOINT, "filter": "wdt:P31 wd:Q5 (truthy); English advisor label"}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
