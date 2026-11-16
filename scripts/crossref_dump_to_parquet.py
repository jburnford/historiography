#!/usr/bin/env python3
"""Crossref public data file (jsonl.gz shards) -> three slim Parquet tables.

  works/part-NNNN.parquet    one row per DOI
  authors/part-NNNN.parquet  one row per contributor (author, editor, translator, chair)
  refs/part-NNNN.parquet     one row per deposited reference

Run where the dump lives (spark). Reads only; writes under --out. Each part
covers --bundle input shards, is written to a .tmp name and renamed when
complete, so a rerun resumes. No abstracts, licences or links are kept.

  python3 -I crossref_dump_to_parquet.py --src DIR --out DIR --workers 12
"""
import argparse
import gzip
import os
import re
import sys
import time
from multiprocessing import Pool

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

S = pa.string()
WORKS = pa.schema([
    ("doi", S), ("type", S), ("title", S), ("subtitle", S), ("container", S),
    ("short_container", S), ("issn", S), ("isbn", S), ("publisher", S),
    ("member", S), ("prefix", S), ("year", pa.int16()), ("month", pa.int8()),
    ("volume", S), ("issue", S), ("page", S), ("language", S),
    ("n_authors", pa.int32()), ("n_refs", pa.int32()),
    ("reference_count", pa.int32()), ("cited_by", pa.int32()),
    ("has_abstract", pa.bool_()), ("review_of", S), ("shard", pa.int32()),
])
AUTHORS = pa.schema([
    ("doi", S), ("role", S), ("seq", pa.int32()), ("sequence", S),
    ("given", S), ("family", S), ("name", S), ("suffix", S), ("orcid", S),
    ("orcid_authenticated", pa.bool_()), ("affiliation", S), ("ror", S),
])
REFS = pa.schema([
    ("doi", S), ("idx", pa.int32()), ("ref_doi", S), ("doi_asserted_by", S),
    ("unstructured", S), ("author", S), ("year", S), ("article_title", S),
    ("journal_title", S), ("volume_title", S), ("series_title", S),
    ("volume", S), ("issue", S), ("first_page", S), ("isbn", S), ("issn", S),
    ("edition", S),
])
ROLES = ("author", "editor", "translator", "chair")
ORCID = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")


def first(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def s(v):
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    return v or None


def issued(rec):
    for k in ("issued", "published", "published-print", "published-online", "created"):
        dp = (rec.get(k) or {}).get("date-parts") or []
        if dp and dp[0] and dp[0][0]:
            p = dp[0]
            try:
                y = int(p[0])
                m = int(p[1]) if len(p) > 1 and p[1] else None
            except (TypeError, ValueError):
                continue
            if 0 < y < 3000:
                return y, (m if m and 0 < m < 13 else None)
    return None, None


def review_of(rec):
    rel = rec.get("relation") or {}
    out = []
    for k in ("is-review-of", "reviews"):
        for r in rel.get(k) or []:
            if r.get("id"):
                out.append(str(r["id"]))
    return " | ".join(out) or None


def rows(rec, shard, W, A, R):
    doi = s(rec.get("DOI"))
    if not doi:
        return
    doi = doi.lower()
    refs = rec.get("reference") or []
    y, m = issued(rec)
    na = 0
    for role in ROLES:
        for i, p in enumerate(rec.get(role) or []):
            if not isinstance(p, dict):
                continue
            na += role == "author"
            aff = p.get("affiliation") or []
            names = [a.get("name") for a in aff if isinstance(a, dict) and a.get("name")]
            rors = []
            for a in aff:
                for ident in (a.get("id") or []) if isinstance(a, dict) else []:
                    if isinstance(ident, dict) and ident.get("id-type") == "ROR":
                        rors.append(str(ident.get("id")))
            o = ORCID.search(p.get("ORCID") or "")
            A.append((doi, role, i, s(p.get("sequence")), s(p.get("given")),
                      s(p.get("family")), s(p.get("name")), s(p.get("suffix")),
                      o.group(1) if o else None,
                      p.get("authenticated-orcid") if o else None,
                      " | ".join(names) or None, " | ".join(rors) or None))
    for i, r in enumerate(refs):
        if not isinstance(r, dict):
            continue
        rd = s(r.get("DOI"))
        R.append((doi, i, rd.lower() if rd else None, s(r.get("doi-asserted-by")),
                  s(r.get("unstructured")), s(r.get("author")), s(r.get("year")),
                  s(r.get("article-title")), s(r.get("journal-title")),
                  s(r.get("volume-title")), s(r.get("series-title")),
                  s(r.get("volume")), s(r.get("issue")), s(r.get("first-page")),
                  s(r.get("ISBN")), s(r.get("ISSN")), s(r.get("edition"))))
    W.append((doi, s(rec.get("type")), s(first(rec.get("title"))),
              s(first(rec.get("subtitle"))), s(first(rec.get("container-title"))),
              s(first(rec.get("short-container-title"))),
              " ".join(rec.get("ISSN") or []) or None,
              " ".join(rec.get("ISBN") or []) or None, s(rec.get("publisher")),
              s(rec.get("member")), s(rec.get("prefix")), y, m,
              s(rec.get("volume")), s(rec.get("issue")), s(rec.get("page")),
              s(rec.get("language")), na, len(refs),
              rec.get("reference-count"), rec.get("is-referenced-by-count"),
              bool(rec.get("abstract")), review_of(rec), shard))


def table(buf, schema):
    cols = list(zip(*buf)) if buf else [[] for _ in schema]
    return pa.table([pa.array(c, type=f.type) for c, f in zip(cols, schema)], schema=schema)


def bundle(job):
    part, shards, src, out = job
    names = {k: os.path.join(out, k, f"part-{part:04d}.parquet") for k in ("works", "authors", "refs")}
    if all(os.path.exists(p) for p in names.values()):
        return part, 0, 0, 0, 0
    schemas = {"works": WORKS, "authors": AUTHORS, "refs": REFS}
    writers = {k: pq.ParquetWriter(names[k] + ".tmp", schemas[k], compression="zstd") for k in names}
    nw = na = nr = bad = 0
    for shard in shards:
        W, A, R = [], [], []
        try:
            with gzip.open(os.path.join(src, f"{shard}.jsonl.gz"), "rb") as fh:
                for line in fh:
                    try:
                        rec = orjson.loads(line)
                    except orjson.JSONDecodeError:
                        bad += 1
                        continue
                    rows(rec, shard, W, A, R)
        except (OSError, EOFError) as exc:
            for w in writers.values():
                w.close()
            return part, -1, 0, 0, f"shard {shard}: {exc}"
        writers["works"].write_table(table(W, WORKS))
        writers["authors"].write_table(table(A, AUTHORS))
        writers["refs"].write_table(table(R, REFS))
        nw += len(W); na += len(A); nr += len(R)
    for k, w in writers.items():
        w.close()
    for k in names:
        os.replace(names[k] + ".tmp", names[k])
    return part, nw, na, nr, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--bundle", type=int, default=100)
    ap.add_argument("--limit", type=int, default=0, help="only the first N shards (test)")
    a = ap.parse_args()
    shards = sorted(int(f[:-9]) for f in os.listdir(a.src) if re.fullmatch(r"\d+\.jsonl\.gz", f))
    if a.limit:
        shards = shards[:a.limit]
    for k in ("works", "authors", "refs"):
        os.makedirs(os.path.join(a.out, k), exist_ok=True)
    jobs = [(i // a.bundle, shards[i:i + a.bundle], a.src, a.out) for i in range(0, len(shards), a.bundle)]
    print(f"{len(shards)} shards, {len(jobs)} parts, {a.workers} workers", flush=True)
    t0 = time.time(); tw = ta = tr = 0; done = 0; failed = []
    with Pool(a.workers) as pool:
        for part, nw, na, nr, bad in pool.imap_unordered(bundle, jobs):
            done += 1
            if nw < 0:
                failed.append((part, bad))
                print(f"FAILED part {part}: {bad}", flush=True)
                continue
            tw += nw; ta += na; tr += nr
            print(f"part {part:04d} done {done}/{len(jobs)} works {tw:,} authors {ta:,} refs {tr:,} "
                  f"bad-lines {bad} {time.time() - t0:,.0f}s", flush=True)
    print(f"FINISHED works {tw:,} authors {ta:,} refs {tr:,} failed-parts {len(failed)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
