"""Fetch publisher-deposited abstracts from Crossref for the selected history journals.

User direction, 2026-09-26: lift the earlier "no abstracts" rule for metadata-level method
detection. Abstracts are local research inputs only: gitignored, never published or shown;
only derived tags leave this machine. Coverage is sparse and publisher-skewed (e.g. Annales
22%, AHR <1%, Isis / Taylor & Francis history titles 0), so any abstract-based measure must
report coverage beside it.

Per journal: filter=issn:<all ISSNs>,has-abstract:true,until-pub-date:<cutoff>,
select=DOI,abstract, cursor paging, one worker, one request per second. Saves
generated/abstracts/<journal_key>.jsonl.gz (doi, abstract) and a manifest entry with the
count matched against Crossref's total. Completed journals are skipped on rerun.
"""
import datetime as dt
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTIONS = [ROOT / "data/history-journals-full-2026-09-22/selection.json",
              ROOT / "data/history-journals-supplement-2026-09-26/selection.json"]
OUT = ROOT / "data/evidence-layer/generated/abstracts"
UA = "historiography-research/1.0 (+https://github.com/jburnford/historiography)"


def get(params, tries=6):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                return json.load(r)["message"]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            wait = 15 * (attempt + 1)
            print(f"  retry in {wait}s after {e}", flush=True)
            time.sleep(wait)
    raise RuntimeError("Crossref request failed repeatedly: " + url)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    journals = []
    for sel_path in SELECTIONS:
        sel = json.loads(sel_path.read_text())
        journals += [(j, sel["cutoff"]) for j in sel["journals"]]
    for j, cutoff in journals:
        key = j["key"]
        if manifest.get(key, {}).get("status") == "complete":
            continue
        filt = ",".join("issn:" + i for i in j["issns"]) + f",has-abstract:true,until-pub-date:{cutoff}"
        cursor, rows, total = "*", [], None
        while True:
            m = get({"filter": filt, "select": "DOI,abstract", "rows": 1000, "cursor": cursor})
            total = m["total-results"]
            items = m["items"]
            rows += [{"doi": it["DOI"].lower(), "abstract": it.get("abstract")} for it in items if it.get("abstract")]
            time.sleep(1)
            if not items or not m.get("next-cursor"):
                break
            cursor = m["next-cursor"]
        dois = {r["doi"] for r in rows}
        path = OUT / f"{key}.jsonl.gz"
        with gzip.open(path, "wt", encoding="utf-8") as f:
            for r in sorted(rows, key=lambda r: r["doi"]):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest[key] = {"label": j["label"], "filter": filt, "crossref_total": total, "saved": len(dois),
                         "status": "complete" if len(dois) >= total else "incomplete",
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print(f"{j['label'][:50]}: {len(dois)}/{total}", flush=True)
    done = [v for v in manifest.values() if v["status"] == "complete"]
    print(f"journals complete {len(done)}/{len(journals)}; abstracts {sum(v['saved'] for v in manifest.values())}")


if __name__ == "__main__":
    main()
