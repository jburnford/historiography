#!/usr/bin/env python3
"""Job 3, step 1 (run on spark): resolve the citing-journal list to Crossref ISSNs and container titles.

Input: job3-journals.json (the 405 journals of data/history-journal-profession-review-2026-09-22/selected-journals
with include_in_working_selection True, their ISSNs from selected-journals.json plus the Canadian / 2026-09-21 registry
selections; and the economic-history-titled rows of data/field-research/crossref-dump-2026-11-16/journal-coverage.csv).

For every journal-article record in Crossref, container titles are grouped by normalised first/second ISSN. A journal
resolves when one of its ISSNs carries journal-article records and the container title there agrees with the label
or an alias (normalised: lower case, accents folded, leading article dropped, '&' = 'and', punctuation removed):
  exact      the normalised title equals the label/alias
  close      one contains the other (3+ words), they share >= 80% of words, or the main title (before ':', '. ',
             ' - ') of one equals the other (Edad Media / Edad Media. Revista de Historia)
  differs    the ISSN carries records but no container title agrees -> listed, NOT used (no guessing)
  absent     no journal-article record under the ISSNs; then the label is looked up by exact normalised container
             title: one ISSN group with that title -> 'title_only' (listed with publisher and years, used), several ->
             'ambiguous' (listed, not used); with no exact hit the same by main title of containers with 50+
             records -> 'main_title_only' (Kritika / Kritika: Explorations in ...; listed, used); none -> 'unresolved'
Within a resolved ISSN, only records whose container title agrees (same rule) are used when the ISSN also carries
other containers (an ISSN shared by two journals, e.g. a predecessor title): 'mixed' in the report.
Writes journals-resolved.csv, issn-containers.csv (all containers seen under the journals' ISSNs).
"""
import csv, html, json, re, sys, unicodedata
import duckdb

P = "/mnt/data/jic823/crossref-2026-parquet"
T = "/mnt/data/jic823/tools/crossref-extract/cites"


def norm(t):
    t = re.sub(r"<html_ent[^>]*>", " and ", t or "")
    t = html.unescape(html.unescape(t))
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.lower().replace("&", " and ").replace("æ", "ae").replace("œ", "oe").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    t = "".join(ch for ch in unicodedata.normalize("NFKD", t) if not unicodedata.combining(ch))
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    w = t.split()
    while w and w[0] in ("the", "la", "le", "les", "l", "el", "il", "der", "die", "das"):
        w = w[1:]
    return " ".join(w)


def main_title(raw):
    return norm(re.split(r"[:.]\s|\s[-–—]\s", raw or "", maxsplit=1)[0])


def agree(a, b):
    ma, mb = main_title(a), main_title(b)
    a, b = norm(a), norm(b)
    if not a or not b:
        return None
    if a == b or a.replace(" ", "") == b.replace(" ", ""):
        return "exact"
    if (mb and mb == a) or (ma and ma == b):
        return "close"
    if (len(a.split()) >= 3 and a in b) or (len(b.split()) >= 3 and b in a):
        return "close"
    A, B = set(a.split()), set(b.split())
    if len(A) >= 2 and len(B) >= 2 and len(A & B) / max(len(A), len(B)) >= 0.8:
        return "close"
    return None


def main():
    J = json.load(open(f"{T}/job3-journals.json"))
    c = duckdb.connect()
    c.sql("set threads=12; set memory_limit='48GB'; set preserve_insertion_order=false")
    import os
    if os.path.exists(f"{T}/all-containers.parquet"):
        c.sql(f"create table cont as select * from '{T}/all-containers.parquet'")
    else:
      c.sql(f"""create table cont as
      select replace(upper(split_part(issn,' ',1)),'-','') i1, replace(upper(split_part(issn,' ',2)),'-','') i2,
             container, any_value(publisher) publisher, count(*) n, count(*) filter (where n_refs>0) n_refs, min(year) y0, max(year) y1
      from '{P}/works/*.parquet' where type='journal-article' and issn is not null group by all""")
      c.sql(f"copy cont to '{T}/all-containers.parquet' (format parquet)")
    rows = c.sql("select * from cont").fetchall()
    by_issn, by_title, by_main = {}, {}, {}
    for i1, i2, cont, pub, n, nr, y0, y1 in rows:
        for i in {i1, i2} - {""}:
            by_issn.setdefault(i, []).append((cont, pub, n, nr, y0, y1, i1, i2))
        by_title.setdefault(norm(cont), []).append((i1, i2, cont, pub, n, nr, y0, y1))
        if n >= 50:
            by_main.setdefault(main_title(cont), []).append((i1, i2, cont, pub, n, nr, y0, y1))
    out, controws = [], []
    for j in J:
        iss = sorted({x.replace("-", "").upper() for x in j["issns"] if x})
        names = [j["label"]] + list(j.get("aliases") or [])
        groups = [g for i in iss for g in by_issn.get(i, [])]
        seen = {}
        for g in groups:
            seen[(g[0], g[6], g[7])] = g
        groups = list(seen.values())
        agreeing, other = [], []
        for g in groups:
            lv = [agree(nm, g[0]) for nm in names]
            lv = "exact" if "exact" in lv else "close" if "close" in lv else None
            (agreeing if lv else other).append((lv, g))
            controws.append(dict(jid=j["jid"], label=j["label"], issn_pair=f"{g[6]} {g[7]}".strip(), container=g[0],
                                 publisher=g[1], articles=g[2], with_refs=g[3], y0=g[4], y1=g[5], agrees=lv or ""))
        use_issns, status, note = [], "", ""
        if agreeing:
            status = "exact" if any(l == "exact" for l, _ in agreeing) else "close"
            if other:
                status += "+mixed"
                note = "; ".join(sorted({g[0] for _, g in other}))[:300]
            use_issns = iss
        elif groups:
            status = "differs"
            note = "; ".join(sorted({g[0] for g in groups}))[:300]
        else:
            hits = []
            for nm in names:
                hits += by_title.get(norm(nm), [])
            hits = list({(h[0], h[1], h[2]): h for h in hits}.values())
            how = "title_only"
            if not hits:
                for nm in names:
                    hits += by_main.get(norm(nm), [])
                hits = list({(h[0], h[1], h[2]): h for h in hits}.values())
                how = "main_title_only"
            if len(hits) == 1:
                status = how
                h = hits[0]
                use_issns = [x for x in (h[0], h[1]) if x]
                note = f"{h[2]} | {h[3]} | {h[4]} records {h[6]}-{h[7]}"
            elif len(hits) > 1:
                status = "ambiguous"
                note = " || ".join(f"{h[0]} {h[1]} {h[2]} | {h[3]} | {h[4]}" for h in hits)[:400]
            else:
                status = "unresolved"
        n_art = sum(g[2] for l, g in agreeing) if agreeing else 0
        n_ref = sum(g[3] for l, g in agreeing) if agreeing else 0
        if status in ("title_only", "main_title_only"):
            n_art, n_ref = hits[0][4], hits[0][5]
        out.append(dict(jid=j["jid"], label=j["label"], source=j["source"], group=j.get("group", ""),
                        issns_listed=" ".join(iss), status=status, issns_used=" ".join(use_issns),
                        containers_used=" | ".join(sorted({g[0] for _, g in agreeing}))[:300] if agreeing else
                        (hits[0][2] if status in ("title_only", "main_title_only") else ""),
                        articles=n_art, with_refs=n_ref, note=note))
    with open(f"{T}/journals-resolved.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    with open(f"{T}/issn-containers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(controws[0]))
        w.writeheader(); w.writerows(controws)
    from collections import Counter
    print(Counter((o["source"], o["status"]) for o in out))


if __name__ == "__main__":
    main()
