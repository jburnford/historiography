#!/usr/bin/env python3
"""Measure the DNB History-dissertation pilot pull (records.jsonl from
dnb_history_diss_parse.py): coverage of author/supervisor GND ids, university,
language, online links; join GND ids to the key log cache (read-only).

Usage:
  python3 -I scripts/dnb_history_diss_measure.py RECORDS.jsonl KEYLOG.sqlite OUT_DIR [WD_P227.tsv]

WD_P227.tsv (optional): gnd<TAB>qid pairs from a Wikidata P227 query, used to
reach wd: anchors for GND ids not on a key.
"""
import collections
import csv
import json
import pathlib
import re
import sqlite3
import sys
import urllib.parse


def pct(a, b):
    return f"{a:,} of {b:,} ({100*a/b:.1f}%)" if b else f"{a} of 0"


def main():
    recs = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
    db = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)
    out = pathlib.Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    wd = {}
    if len(sys.argv) > 4:
        for line in open(sys.argv[4], encoding="utf-8"):
            g, q = line.rstrip("\n").split("\t")[:2]
            wd.setdefault(g, set()).add(q)

    rep = {}
    N = len(recs)
    ids = {r["id"] for r in recs}
    rep["records"] = N
    rep["per_query_year"] = dict(sorted(collections.Counter(r["query_year"] for r in recs).items()))
    # print/online pairs inside the pull
    paired = sum(1 for r in recs if any(w.replace("(DE-101)", "") in ids
                                        for x in r["related"] for w in x["w"] if w.startswith("(DE-101)")))
    rep["records_whose_other_edition_is_also_in_pull"] = paired
    rep["media"] = dict(collections.Counter(r.get("media", "") for r in recs))
    rep["author_gnd"] = pct(sum(1 for r in recs if r.get("author_gnd")), N)
    rep["author_present"] = pct(sum(1 for r in recs if r.get("author")), N)
    sup_any = [r for r in recs if r["supervisors"]]
    rep["supervisor_named_700"] = pct(len(sup_any), N)
    rep["supervisor_with_gnd"] = pct(sum(1 for r in recs if any(s["gnd"] for s in r["supervisors"])), N)
    rep["supervisor_in_245c_text_only"] = pct(
        sum(1 for r in recs if not r["supervisors"] and re.search(r"Betreuer|Gutachter|Referent", r.get("resp", ""))), N)
    ss = [s for r in recs for s in r["supervisors"]]
    rep["supervisor_headings"] = len(ss)
    rep["supervisor_headings_with_gnd"] = pct(sum(1 for s in ss if s["gnd"]), len(ss))
    rep["supervisor_by_media"] = {
        m: pct(sum(1 for r in recs if r.get("media") == m and r["supervisors"]),
               sum(1 for r in recs if r.get("media") == m)) for m in ("c", "n")}
    rep["supervisor_by_year"] = {y: pct(sum(1 for r in recs if r["query_year"] == y and r["supervisors"]), n)
                                 for y, n in rep["per_query_year"].items()}
    rep["contributor_roles"] = dict(collections.Counter(f"{c['role']}|{c['role_text']}" for r in recs
                                                        for c in r["contributors"]).most_common(15))
    rep["supervisor_roles"] = dict(collections.Counter(s["role_text"] for s in ss).most_common(8))
    rep["univ_present"] = pct(sum(1 for r in recs if r.get("univ")), N)
    rep["diss_note_unparsed"] = sum(1 for r in recs if r.get("diss_note"))
    rep["diss_type"] = dict(collections.Counter(re.sub(r"[.\s]", "", (r.get("diss_type") or "?"))[:20]
                                                for r in recs).most_common(10))
    de = [r for r in recs if (r.get("country044") or "").startswith("XA-DE")]
    rep["published_in_germany_044"] = pct(len(de), N)
    rep["country044_top"] = dict(collections.Counter((r.get("country044") or "?")[:5] for r in recs).most_common(12))
    def place(u):
        u = re.sub(r"^\s*(Zugl\.?|Zugleich)\s*:?\s*", "", u)
        u = re.split(r",", u)[0]
        u = re.sub(r"\s*\(.*?\)", "", u).strip()
        return u
    univ = collections.Counter(place(r["univ"]) for r in recs if r.get("univ"))
    AT = re.compile(r"Wien|Vienna|Graz|Innsbruck|Salzburg|Klagenfurt|Linz", re.I)
    CH = re.compile(r"Zürich|Zurich|Bern\b|Basel|Luzern|St\. ?Gallen|Genève|Genf|Lausanne|Neuchâtel|Fribourg|Freiburg \(Schweiz\)|Freiburg/Schweiz|Freiburg, Schweiz", re.I)
    OTHER = re.compile(r"Paris|London|Oxford|Cambridge|Leiden|Amsterdam|Utrecht|Groningen|Wrocław|Warszawa|Kraków|Praha|Prag|Firenze|Florenz|Roma|Rom\b|Bologna|Leuven|Gent|Bruxelles|Luxembourg|Tōkyō|Tokyo|Helsinki|Uppsala|Lund|Kopenhagen|København|Budapest|Ljubljana|Bratislava|Brno|Tartu|Riga|Vilnius|Istanbul|Jerusalem|Tel Aviv|New York|Chicago|Toronto|Strasbourg|Straßburg|Lyon|Madrid|Barcelona|Sevilla|Lisboa|Wageningen|Nijmegen|Maastricht|Trento|Bolzano|Bozen|Liechtenstein|Olomouc|Poznań|Toruń|Łódź|Moskva|Sankt-Peterburg|Kyiv|Kiew", re.I)
    cc = collections.Counter()
    for r in recs:
        u = r.get("univ") or r.get("diss_note") or ""
        cc["AT" if AT.search(u) else "CH" if CH.search(u) else "other" if OTHER.search(u) else
           "no place" if not u else "DE (by elimination)"] += 1
    rep["degree_country_estimate"] = dict(cc)
    ids = {r["id"] for r in recs}
    par = {i: i for i in ids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for r in recs:
        for x in r["related"]:
            for w in x["w"]:
                if w.startswith("(DE-101)") and w[8:] in ids:
                    par[find(r["id"])] = find(w[8:])
    rep["works_after_print_online_merge"] = len({find(i) for i in ids})
    rep["degree_places_distinct"] = len(univ)
    rep["degree_places_top30"] = dict(univ.most_common(30))
    dy = collections.Counter()
    for r in recs:
        d = r.get("degree_year") or ""
        try:
            gap = int(r["year_pub"]) - int(d[:4])
            dy["same" if gap == 0 else "pub+1" if gap == 1 else "pub+2..3" if gap in (2, 3) else "pub+4 or more" if gap > 3 else "pub<degree"] += 1
        except Exception:
            dy["no degree year"] += 1
    rep["degree_year_vs_pub_year"] = dict(dy)
    rep["language"] = dict(collections.Counter((r.get("lang") or [r.get("lang008", "?")])[0] for r in recs).most_common(10))
    free = [r for r in recs if any(u["z"] == "kostenfrei" for u in r["urls"])]
    rep["online_free_url"] = pct(len(free), N)
    hosts = collections.Counter()
    for r in free:
        for u in r["urls"]:
            if u["z"] == "kostenfrei":
                hosts[urllib.parse.urlparse(u["u"]).netloc] += 1
    rep["free_url_hosts_top25"] = dict(hosts.most_common(25))
    rep["free_url_hosts_distinct"] = len(hosts)
    rep["has_doi"] = pct(sum(1 for r in recs if r.get("doi")), N)
    rep["has_urn"] = pct(sum(1 for r in recs if r.get("urn")), N)
    rep["has_isbn"] = pct(sum(1 for r in recs if r["isbn"]), N)

    # identity join
    def keyof(anchor):
        row = db.execute("select key from anchor where anchor=?", (anchor,)).fetchone()
        if not row:
            return None
        k = row[0]
        for _ in range(5):  # follow merges (replaced_by is a JSON list)
            st = db.execute("select status, replaced_by from keys where key=?", (k,)).fetchone()
            if not st:
                return None
            nxt = json.loads(st[1]) if st[1] else []
            if st[0] == "merged" and nxt:
                k = nxt[0]
                continue
            return k if st[0] in ("active", "provisional") else None
        return k

    def resolve(g):
        k = keyof("gnd:" + g)
        if k:
            return "gnd", k
        for q in sorted(wd.get(g, ())):
            k = keyof("wd:" + q)
            if k:
                return "wd", k
        return ("wd-no-key" if g in wd else "none"), None

    authors = {r["author_gnd"] for r in recs if r.get("author_gnd")}
    sups = {s["gnd"] for r in recs for s in r["supervisors"] if s["gnd"]}

    def is_ref(c):
        return c["role_text"] == "Gutachter" or c["role"] == "rev"
    refs = {c["gnd"] for r in recs for c in r["contributors"] if is_ref(c) and c["gnd"]}
    rep["referee_headings"] = sum(1 for r in recs for c in r["contributors"] if is_ref(c))
    rep["referee_records"] = pct(sum(1 for r in recs if any(is_ref(c) for c in r["contributors"])), N)
    rep["supervisor_or_referee_records"] = pct(
        sum(1 for r in recs if r["supervisors"] or any(is_ref(c) for c in r["contributors"])), N)
    rep["supervisor_or_referee_with_gnd_records"] = pct(
        sum(1 for r in recs if any(s["gnd"] for s in r["supervisors"])
            or any(is_ref(c) and c["gnd"] for c in r["contributors"])), N)
    res = {}
    for g in authors | sups | refs:
        res[g] = resolve(g)
    for name, s in (("author", authors), ("supervisor", sups), ("referee", refs),
                    ("supervisor_or_referee", sups | refs), ("any_role", authors | sups | refs)):
        c = collections.Counter(res[g][0] for g in s)
        rep[f"{name}_gnd_distinct"] = len(s)
        rep[f"{name}_key_via_gnd_anchor"] = pct(c["gnd"], len(s))
        rep[f"{name}_key_via_wikidata_p227"] = pct(c["wd"], len(s))
        rep[f"{name}_on_wikidata_no_key"] = pct(c["wd-no-key"], len(s))
        rep[f"{name}_not_on_wikidata_no_key"] = pct(c["none"], len(s))
    sup_names_nognd = {s["name"] for r in recs for s in r["supervisors"] if not s["gnd"]}
    rep["supervisor_names_without_gnd_distinct"] = len(sup_names_nognd)
    # theses whose supervisor reaches a key
    rep["records_with_supervisor_on_a_key"] = pct(
        sum(1 for r in recs if any(s["gnd"] and res[s["gnd"]][1] for s in r["supervisors"])), N)
    rep["records_with_supervisor_or_referee_on_a_key"] = pct(
        sum(1 for r in recs if any(s["gnd"] and res[s["gnd"]][1] for s in r["supervisors"])
            or any(is_ref(c) and c["gnd"] and res[c["gnd"]][1] for c in r["contributors"])), N)
    rep["records_with_author_on_a_key"] = pct(
        sum(1 for r in recs if r.get("author_gnd") and res[r["author_gnd"]][1]), N)
    json.dump(rep, open(out / "measure.json", "w"), ensure_ascii=False, indent=1)
    with open(out / "gnd-resolution.tsv", "w", encoding="utf-8") as f:
        for g, (how, k) in sorted(res.items()):
            f.write(f"{g}\t{'A' if g in authors else ''}{'S' if g in sups else ''}{'R' if g in refs else ''}"
                    f"\t{how}\t{k or ''}\n")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
