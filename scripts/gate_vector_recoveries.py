#!/usr/bin/env python3
"""Gate the vector-search recoveries by name agreement.

Vector search can confidently return a DIFFERENT famous person who merely
shares a surname (W. H. Walsh -> Raoul Walsh; Jenny Garber -> Jennie Garth),
so sitelink count alone is not a safe confidence signal here. Require the
candidate name to (a) contain the roster surname and (b) match the roster
first-name initial. This cleanly separates real recoveries (Hegel, Schumpeter,
Lazarsfeld) from lookalikes.

Reads no-match-vector-candidates.csv, writes no-match-recovered.csv (passing
rows only, with a confidence tier) and prints the reject list for manual review.
"""
import csv
import re
import unicodedata

IN = "data/orcid-2026-09-21/no-match-vector-candidates.csv"
OUT = "data/orcid-2026-09-21/no-match-recovered.csv"

# tokens that are not name content
DROP = {"de", "von", "van", "der", "le", "la", "du", "di", "dos", "das",
        "baron", "sir", "dr", "lord", "st", "the"}


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def tokens(name):
    name = fold(name).replace(".", " ")
    return [t for t in re.split(r"[^a-z0-9]+", name) if t]


def content(toks):
    return [t for t in toks if t not in DROP]


def initials(toks):
    # first non-particle token's first char
    c = content(toks)
    return c[0][0] if c else ""


def agree(roster, cand):
    rt, ct = tokens(roster), tokens(cand)
    if not rt or not ct:
        return False
    r_content, c_content = content(rt), content(ct)
    if not r_content or not c_content:
        return False
    # surname = last content token of the roster label; must appear in candidate
    surname = r_content[-1]
    if len(surname) <= 1:                 # roster surname is itself an initial -> unsafe
        return False
    if surname not in c_content:
        return False
    # first initial must match (handles "G. W. F. Hegel" vs "Georg ... Hegel")
    return initials(rt) == initials(ct)


def main():
    rows = list(csv.DictReader(open(IN)))
    passed, rejected = [], []
    for r in rows:
        if not r["top_qid"]:
            continue
        if agree(r["label"], r["top_name"]):
            passed.append(r)
        else:
            rejected.append(r)

    for r in passed:
        s = int(r["top_sitelinks"] or 0)
        r["confidence"] = "high_recovered" if s >= 3 else \
                          "medium_recovered" if s >= 1 else "low_recovered"

    order = {"high_recovered": 0, "medium_recovered": 1, "low_recovered": 2}
    passed.sort(key=lambda r: (order[r["confidence"]], -int(r["top_sitelinks"] or 0)))
    cols = ["confidence", "id", "label", "top_qid", "top_name", "top_desc",
            "top_sitelinks", "top_occupations", "top_birth", "top_death"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in passed:
            w.writerow({c: r.get(c, "") for c in cols})

    from collections import Counter
    c = Counter(r["confidence"] for r in passed)
    print(f"vector recoveries that PASS the name-agreement gate: {len(passed)} -> {OUT}")
    for k in ("high_recovered", "medium_recovered", "low_recovered"):
        print(f"  {k:18} {c[k]}")
    print("\n  sample passing recoveries:")
    for r in passed[:14]:
        print(f"    {r['label'][:26]:26} -> {r['top_qid']:9} {r['top_name'][:26]:26} sites={r['top_sitelinks']}")
    print(f"\n  REJECTED by gate (name mismatch, -> manual): {len(rejected)}")
    for r in rejected[:12]:
        print(f"    {r['label'][:26]:26} =/= {r['top_name'][:30]}")


if __name__ == "__main__":
    main()
