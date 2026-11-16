#!/usr/bin/env python3
"""Counts for SCOPE.md, and the tracked people table. Read-only on everything it reads.

Usage: summarize.py THESES.csv.gz PEOPLE.csv MATCH.csv HOSTS.csv OUT_PEOPLE.csv.gz OUT_SUMMARY.json"""
import csv, gzip, json, re, sys, unicodedata, collections as C

th_f, people_f, match_f, hosts_f, out_people, out_sum = sys.argv[1:7]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


T = list(csv.DictReader(gzip.open(th_f, "rt")))
# second-level duplicates SwePub did not merge: same author surname + same first 40 title characters
seen, dup = {}, {}
for t in sorted(T, key=lambda t: t["record_id"]):
    k = (norm(t["author"].split(",")[0]), norm(t["title"])[:40])
    if k in seen and k[0]:
        dup[t["record_id"]] = seen[k]
    else:
        seen[k] = t["record_id"]
H = [t for t in T if t["screen"] == "history" and t["record_id"] not in dup]
Hhm = [t for t in H if t["confidence"] in ("high", "medium")]
S = {"records": len(T), "unmerged_duplicates": len(dup),
     "screen": {f"{s}/{c}": n for (s, c), n in sorted(C.Counter((t["screen"], t["confidence"]) for t in T
                                                               if t["record_id"] not in dup).items())},
     "history_all": len(H), "history_high_medium": len(Hhm)}
S["history_by_year"] = dict(sorted(C.Counter(t["year"] for t in H).items()))
S["history_by_university"] = dict(C.Counter(t["university"] for t in H).most_common())
S["history_by_language"] = dict(C.Counter(t["language"] for t in H).most_common(8))
S["history_no_601_5digit"] = sum(1 for t in H if not any(c.startswith("601") for c in t["ssif5"].split()))
S["history_autoclassified"] = sum(1 for t in H if t["autoclassified"] == "True")
S["history_local_subject"] = sum(1 for t in H if t["local_subjects"])
S["economic_history_by_year"] = dict(sorted(C.Counter(t["year"] for t in T if t["screen"] == "economic_history"
                                                      and t["record_id"] not in dup).items()))
# access
S["history_route"] = dict(C.Counter(t["route_class"] for t in H).most_common())
S["history_route_kind"] = {f"{a}/{b}": n for (a, b), n in C.Counter((t["route_class"], t["link_kind"]) for t in H).most_common()}
S["history_route_by_host"] = {f"{h}|{c}": n for (h, c), n in
                              C.Counter((t["link_host"], t["route_class"]) for t in H if t["link_host"]).most_common()}
S["history_route_by_university"] = {u: dict(C.Counter(t["route_class"] for t in H if t["university"] == u))
                                    for u in S["history_by_university"]}
S["history_route_by_period"] = {p: dict(C.Counter(t["route_class"] for t in H if lo <= t["year"] <= hi))
                                for p, lo, hi in (("2000-2009", "2000", "2009"), ("2010-2019", "2010", "2019"),
                                                  ("2020-2025", "2020", "2025"))}
# people
P = {(r["record_id"], r["role"], r["family"], r["given"]): r for r in csv.DictReader(open(people_f))}
M = list(csv.DictReader(open(match_f)))
cols = ["record_id", "role", "family", "given", "life_span", "birth_year", "death_year", "title", "orcid", "local_ids",
        "affiliation", "key", "via", "name_only"]
with gzip.open(out_people, "wt", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for m in M:
        p = P[(m["record_id"], m["role"], m["family"], m["given"])]
        w.writerow({**p, "key": m["key"], "via": m["via"], "name_only": m["name_only"]})
hist_ids = {t["record_id"] for t in H}
S["credits_in_history"] = dict(C.Counter(m["role"] for m in M if m["record_id"] in hist_ids))
S["theses_with"] = {
    "supervisor": sum(1 for t in H if int(t["n_supervisor"]) > 0),
    "opponent": sum(1 for t in H if int(t["n_opponent"]) > 0),
    "author_orcid": sum(1 for t in H if t["author_orcid"]),
}
S["theses_with_opponent_by_period"] = {p: f'{sum(1 for t in H if lo <= t["year"] <= hi and int(t["n_opponent"]))}/'
                                          f'{sum(1 for t in H if lo <= t["year"] <= hi)}'
                                       for p, lo, hi in (("2000-2009", "2000", "2009"), ("2010-2019", "2010", "2019"),
                                                         ("2020-2025", "2020", "2025"))}


def pid(m):
    return m["orcid"] or norm(m["family"]) + "|" + norm(m["given"])


roles = {}
for role in ("author", "supervisor", "opponent", "any"):
    d = {}
    for m in M:
        if m["record_id"] not in hist_ids:
            continue
        r = m["role"].replace("assistant_", "")
        if role != "any" and r != role:
            continue
        cur = d.get(pid(m))
        if cur is None or (m["key"] and not cur["key"]):
            d[pid(m)] = m
    c = C.Counter(m["via"] or ("name-only (not matched)" if m["name_only"] else "no hit") for m in d.values())
    keyed = sum(1 for m in d.values() if m["key"])
    roles[role] = {"distinct": len(d), "keyed": keyed, "share": round(keyed / len(d), 3) if d else 0, "by_route": dict(c),
                   "with_orcid": sum(1 for m in d.values() if m["orcid"]),
                   "with_birth_year": sum(1 for m in d.values() if m["life_span"])}
S["people_history"] = roles
S["edges_possible_history"] = {
    "theses_with_keyed_author": sum(1 for t in H if any(m["key"] and m["role"] == "author" for m in M if m["record_id"] == t["record_id"])),
    "supervision_credits_keyed": sum(1 for m in M if m["record_id"] in hist_ids and m["role"].endswith("supervisor") and m["key"]),
    "opponent_credits_keyed": sum(1 for m in M if m["record_id"] in hist_ids and m["role"] == "opponent" and m["key"]),
}
S["hosts"] = [{k: h[k] for k in ("host", "class", "reason", "robots_status", "crawl_delay", "links")}
              for h in csv.DictReader(open(hosts_f))]
json.dump(S, open(out_sum, "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in S.items() if k != "hosts"}, ensure_ascii=False, indent=1))
