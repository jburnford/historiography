"""Extract ORCID holders' claimed works from the cached /record JSON into one Parquet table.

IDENTITY-PLAN.md step 2.4. Offline: reads `data/orcid-2026-09-21/records/*.json` (the
cached public records for the Wikidata-historian and journal-derived ORCID sets) and makes
no requests. One row per ORCID work group, keeping every external identifier across the
group's summaries. A claim is added to a record by the person or by a client they
authorised. It is self-attributed, not independently verified.

Also writes `orcid-names.parquet`: given, family, credit and other names per ORCID, for
name-compatibility gates.
"""
import argparse
import glob
import json
import re
from pathlib import Path

import duckdb
import pandas as pd

HNET_SHOWREV = re.compile(r"h-net\.org/reviews/showrev\.php\?id=(\d+)", re.I)
RIH_REVIEW = re.compile(r"reviews\.history\.ac\.uk/review/(\d+)", re.I)


def val(d, *path):
    for p in path:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


def works_rows(orcid, record):
    groups = val(record, "activities-summary", "works", "group") or []
    for g in groups:
        summaries = g.get("work-summary") or []
        if not summaries:
            continue
        s = summaries[0]
        ids, urls = set(), set()
        for w in summaries:
            for e in val(w, "external-ids", "external-id") or []:
                t, v = e.get("external-id-type"), val(e, "external-id-normalized", "value") or e.get("external-id-value")
                if t and v:
                    ids.add((t.lower(), v.strip()))
            u = val(w, "url", "value")
            if u:
                urls.add(u.strip())
        for e in val(g, "external-ids", "external-id") or []:
            t, v = e.get("external-id-type"), val(e, "external-id-normalized", "value") or e.get("external-id-value")
            if t and v:
                ids.add((t.lower(), v.strip()))
        blob = " ".join(sorted(urls) + [v for t, v in ids if t in ("uri", "url", "other-id")])
        hnet = sorted({int(m) for m in HNET_SHOWREV.findall(blob)})
        rih = sorted({int(m) for m in RIH_REVIEW.findall(blob)})
        isbns = sorted({re.sub(r"[^0-9Xx]", "", v).upper() for t, v in ids if t == "isbn"})
        yield {
            "orcid": orcid,
            "put_code": s.get("put-code"),
            "type": s.get("type"),
            "title": val(s, "title", "title", "value"),
            "subtitle": val(s, "title", "subtitle", "value"),
            "year": val(s, "publication-date", "year", "value"),
            "journal": val(s, "journal-title", "value"),
            "source_name": val(s, "source", "source-name", "value"),
            "self_asserted": val(s, "source", "source-orcid", "path") == orcid,
            "urls": sorted(urls),
            "dois": sorted({v.lower() for t, v in ids if t == "doi"}),
            "isbns": [i for i in isbns if len(i) in (10, 13)],
            "hnet_review_ids": hnet,
            "rih_review_ids": rih,
            "n_summaries": len(summaries),
        }


def name_row(orcid, record):
    p = record.get("person") or {}
    others = [val(o, "content") for o in val(p, "other-names", "other-name") or []]
    return {"orcid": orcid,
            "given": val(p, "name", "given-names", "value"),
            "family": val(p, "name", "family-name", "value"),
            "credit": val(p, "name", "credit-name", "value"),
            "other_names": [o for o in others if o]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", type=Path, default=Path("data/orcid-2026-09-21/records"))
    ap.add_argument("--out", type=Path, default=Path("data/person-registry/generated/orcid-claims"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    works, names, bad = [], [], []
    for path in sorted(glob.glob(str(args.records / "*.json"))):
        orcid = Path(path).stem.upper()
        try:
            record = json.loads(Path(path).read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            bad.append(orcid)
            continue
        if not isinstance(record, dict) or "activities-summary" not in record:
            bad.append(orcid)
            continue
        works.extend(works_rows(orcid, record))
        names.append(name_row(orcid, record))
    con = duckdb.connect()
    pd.DataFrame(works).to_parquet(args.out / "claimed-works.parquet", index=False)
    pd.DataFrame(names).to_parquet(args.out / "orcid-names.parquet", index=False)
    summary = con.execute(f"""SELECT count(*), count(DISTINCT orcid),
        count(*) FILTER (WHERE type IN ('book', 'edited-book')),
        count(*) FILTER (WHERE type = 'book-review'),
        count(*) FILTER (WHERE len(hnet_review_ids) > 0), count(*) FILTER (WHERE len(rih_review_ids) > 0),
        count(*) FILTER (WHERE len(isbns) > 0)
        FROM '{args.out / "claimed-works.parquet"}'""").fetchone()
    keys = ["works", "orcids", "books", "book_reviews", "hnet_review_links", "rih_review_links", "with_isbn"]
    report = dict(zip(keys, summary), unreadable_records=len(bad), records=len(names))
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(report)


if __name__ == "__main__":
    main()
