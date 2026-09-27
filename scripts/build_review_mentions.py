"""Review-text mentions: approaches and canonical figures that reviewers invoke.

EVIDENCE-LAYER-PLAN.md component 4, approved 2026-09-26 ("work your way through this list").
Research use of locally held review text (H-Net and Reviews in History, via the upstream
catalog, read-only). Outputs are per-review tags and aggregates. No review text leaves this
machine or enters Git; the audit sample with short snippets is written to generated/ (ignored).

Two tag kinds per review:
  approach  lexicon terms (English, German, French) mapped to atlas entries or `none:` fields,
            e.g. microhistory / Mikrogeschichte -> micro. Counts once per review per target.
  person    atlas people (all 876 roster labels) by full name, plus surname-only matches for a
            curated whitelist of distinctive surnames. A person is not counted in a review whose
            own credits (reviewer, reviewed authors or editors) include that surname: a review
            naming its own book's author is not an invocation.

Aggregates: invoking reviews per target by five-year bin; approach invocations by the
reviews' crosswalk themes (tests the folds: is microhistory invoked in social and cultural
history?); and the top invoked people per decade (the operational canon).
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data/evidence-layer/generated"
UPSTREAM = Path("/home/jic823/hnet-reviews/data/export/catalog.duckdb")
GRAPH = ROOT / "historiography-1920-2000.json"

APPROACHES = {  # target -> patterns (case-insensitive unless (?-i:...))
    "micro": [r"micro-?histor\w*", r"microstori\w*", r"micro-?histoire\w*", r"mikrogeschicht\w*",
              r"alltagsgeschicht\w*", r"history of everyday life"],
    "annales": [r"(?-i:Annales)(?! [A-Z]\w+ (?:de|of)\b)", r"longue dur[ée]e", r"histoire des mentalit[ée]s"],
    "language": [r"linguistic turn", r"post-?structuralis\w*", r"deconstruct\w*"],
    "context": [r"(?-i:Cambridge School)"],
    "subaltern": [r"subaltern"],
    "post": [r"post-?colonial\w*", r"postkolonial\w*"],
    "culture": [r"new cultural history", r"cultural turn", r"neue kulturgeschichte"],
    "social": [r"history from below", r"new social history", r"geschichte von unten"],
    "marx": [r"marxis[mt]\w*", r"historical materialism", r"historischer materialismus"],
    "global": [r"global history", r"globalgeschicht\w*", r"connected histor\w*", r"entangled histor\w*",
               r"verflechtungsgeschicht\w*", r"histoire crois[ée]e"],
    # v1 audit ~5/12: bare "transnational" is mostly an ordinary adjective; v2 keeps approach phrases.
    "none:transnational_history": [r"transnational(?:e|en)? (?:histor\w*|geschicht\w*|approach\w*|perspective\w*|turn|methods?)",
                                   r"histoire transnationale"],
    # v2 audit 7/12: "Transnationalisierung" usually names the historical process, so it is dropped after v2.
    "intersectionality": [r"intersectional\w*", r"intersektional\w*"],
    "spatialhistory": [r"spatial turn", r"(?-i:GIS)\b", r"geographic information system\w*"],
    "oral": [r"oral histor\w*"],
    "quant": [r"cliometric\w*", r"quantitative history", r"quantitative method\w*"],
    "digital_history": [r"digital history", r"digital humanities", r"text[- ]mining", r"distant reading",
                        r"topic model\w*"],
    "conceptual": [r"begriffsgeschicht\w*", r"conceptual history", r"history of concepts"],
    "historyworkshop": [r"(?-i:History Workshop)"],
    # v1 audit ~1/12: "psychoanaly*" mostly caught the history of psychoanalysis as subject.
    "psychohistory": [r"psychohistor\w*", r"psychoanalytic (?:interpretation|reading|approach|perspective|lens)\w*",
                      r"psychoanalytische\w* (?:deutung|interpretation|ansatz|perspektive)\w*"],
    "memory": [r"memory studies", r"lieux de m[ée]moire", r"collective memory", r"ged[äa]chtnisgeschicht\w*",
               r"erinnerungskultur\w*"],
    "gender": [r"gender history", r"geschlechtergeschicht\w*"],
    "environment": [r"environmental history", r"umweltgeschicht\w*"],
    "practice": [r"practice theory", r"habitus"],
    "frankfurt": [r"(?-i:Frankfurt School)", r"critical theory", r"kritische theorie"],
    "bielefeld": [r"(?-i:Gesellschaftsgeschichte)", r"historische sozialwissenschaft\w*", r"(?-i:Sonderweg)"],
    "sts": [r"science and technology studies", r"actor-network", r"akteur-netzwerk\w*"],
    "ssk": [r"sociology of scientific knowledge"],
    "publichistory": [r"public history"],
    "none:social_science_history": [r"social science history"],
    "none:history_of_knowledge": [r"wissensgeschicht\w*", r"history of knowledge"],
    "none:history_of_emotions": [r"history of emotions", r"emotionsgeschicht\w*", r"geschichte der gef[üu]hle"],
}
# Surnames distinctive enough to count alone (otherwise full names only).
# v1 audit removed Kuhn (0/12: other Kuhns), Pinchbeck, Tuchman, Ryle and Dobb (other bearers of the surname).
SURNAMES = ["Foucault", "Braudel", "Febvre", "Labrousse", "Geertz", "Derrida", "Barthes", "Lacan", "Althusser",
            "Nietzsche", "Wittgenstein", "Latour", "Fanon", "Gramsci", "Hobsbawm", "Tawney", "Chartier",
            "Davidoff", "Higginbotham", "Daston", "Lévi-Strauss", "Lukács"]


def lit(p):
    return "'" + str(p).replace("'", "''") + "'"


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()


# Labels whose " / " separates name variants rather than a description.
NAME_VARIANTS = {"Georg / György Lukács": ["Georg Lukács", "György Lukács", "Georg Lukacs", "Gyorgy Lukacs"]}


def names_of(label):
    return NAME_VARIANTS.get(label, [label.split(" / ")[0].strip()])


def name_pattern(name):
    parts = [re.escape(p) for p in name.split()]
    return r"\s+".join(p.replace(r"\.", r"\.\s?") for p in parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--series", default="v14")
    ap.add_argument("--registry", default="v9")
    ap.add_argument("--version", default="mentions-v1")
    ap.add_argument("--limit", type=int, help="scan only the first N reviews (pipeline test)")
    ap.add_argument("--from-tags", type=Path, help="reuse review_tags.parquet from an earlier scan (no rescan)")
    args = ap.parse_args()
    out = GEN / args.version
    if out.exists() and (out / "summary.json").exists():
        raise SystemExit(f"{out} exists; choose a new --version")
    out.mkdir(parents=True, exist_ok=True)
    g = json.loads(GRAPH.read_text())
    labels = {n["id"]: n["label"] for n in g["nodes"]}
    people = {p["id"]: p["label"] for p in g["people"]}
    # Approach regex: one named group per target.
    appr_groups, appr_map = [], {}
    for i, (t, pats) in enumerate(APPROACHES.items()):
        appr_groups.append(f"(?P<a{i}>\\b(?:{'|'.join(pats)}))")
        appr_map[f"a{i}"] = t
    appr_re = re.compile("|".join(appr_groups), re.I)
    # Person regex: alternation of full names and whitelisted surnames; map by folded match text.
    person_by_key, alts = {}, []
    surname_owner = {}
    for pid, label in people.items():
        for name in names_of(label):
            alts.append(name_pattern(name))
            person_by_key[fold(re.sub(r"\s+", " ", name.replace(". ", ".")))] = pid
            last = name.split()[-1]
            if last in SURNAMES:
                surname_owner[last] = pid
    for s in SURNAMES:
        alts.append(re.escape(s))
    alts.sort(key=len, reverse=True)
    person_re = re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])")
    surname_by_fold = {fold(s): p for s, p in surname_owner.items()}

    def person_of(match):
        k = fold(re.sub(r"\s+", " ", match).replace(". ", "."))
        return person_by_key.get(k) or surname_by_fold.get(k)

    up = duckdb.connect(str(UPSTREAM), read_only=True)
    total = up.execute("SELECT count(*) FROM reviews WHERE is_real AND body_text IS NOT NULL").fetchone()[0]
    reviews = [] if args.from_tags else up.execute("""SELECT source, era, review_id, body_text, substr(review_date, -4)
                            FROM reviews WHERE is_real AND body_text IS NOT NULL ORDER BY source, era, review_id"""
                            + (f" LIMIT {int(args.limit)}" if args.limit else "")).fetchall()
    up_sha = hashlib.sha256(UPSTREAM.read_bytes()).hexdigest()
    reg = duckdb.connect(str(ROOT / "data/person-registry/generated" / args.registry / "registry.duckdb"), read_only=True)
    credits = defaultdict(set)
    for rec, name in reg.execute("""SELECT record_id, name FROM occurrences WHERE corpus IN ('hnet', 'rih')""").fetchall():
        for tok in re.split(r"[\s,]+", name or ""):
            if len(tok) > 2:
                credits[rec].add(fold(tok))
    dates = dict(reg.execute("""SELECT record_id, max(record_date) FROM occurrences WHERE corpus IN ('hnet', 'rih')
                               GROUP BY 1""").fetchall())
    themes = defaultdict(set)
    with open(GEN / args.series / "review_themes.csv") as f:
        for r in csv.DictReader(f):
            themes[r["item"]].add(r["target"])

    tags, snippets = [], defaultdict(list)
    for source, era, rid, text, _ in reviews:
        item = f"hnet:review:{era}:{rid}" if source == "hnet" else f"rih:review:{rid}"
        year = (dates.get(item) or "")[:4]
        found_a, found_p = Counter(), Counter()
        for m in appr_re.finditer(text):
            t = appr_map[m.lastgroup]
            found_a[t] += 1
            if len(snippets[t]) < 400:
                snippets[t].append((item, text[max(0, m.start() - 90):m.end() + 90].replace("\n", " ")))
        own = credits.get(item, set())
        for m in person_re.finditer(text):
            pid = person_of(m.group(0))
            if not pid:
                continue
            surname = fold(names_of(people[pid])[0].split()[-1])
            if surname in own:
                continue
            found_p[pid] += 1
            key = "person:" + pid
            if len(snippets[key]) < 60:
                snippets[key].append((item, text[max(0, m.start() - 90):m.end() + 90].replace("\n", " ")))
        for t, c in found_a.items():
            tags.append((item, source, year, "approach", t, c))
        for p, c in found_p.items():
            tags.append((item, source, year, "person", p, c))

    db = duckdb.connect()
    if args.from_tags:
        db.execute(f"CREATE TABLE tags AS SELECT * FROM read_parquet({lit(args.from_tags)})")
    else:
        db.execute("CREATE TABLE tags (item VARCHAR, source VARCHAR, year VARCHAR, kind VARCHAR, target VARCHAR, n INT)")
        db.executemany("INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?)", tags)
        db.execute(f"COPY tags TO {lit(out / 'review_tags.parquet')} (FORMAT parquet)")  # saved before aggregation
        with open(out / "audit-snippets.csv", "w", newline="") as f:  # local only (generated/ is ignored)
            w = csv.writer(f); w.writerow(["target", "item", "snippet", "judgment"])
            for t, rows in sorted(snippets.items()):
                for it, snip in sorted(rows, key=lambda r: hashlib.sha256((r[0] + t).encode()).hexdigest())[:20]:
                    w.writerow([t, it, snip, ""])
    db.execute("CREATE TABLE themes (item VARCHAR, theme VARCHAR)")
    db.executemany("INSERT INTO themes VALUES (?, ?)", [(i, t) for i, ts in themes.items() for t in ts])
    bins = lambda y: f"{int(y) // 5 * 5}-{int(y) // 5 * 5 + 4}" if y.isdigit() else "undated"
    db.create_function("bin5", bins, [str], str)
    appr = db.execute("""SELECT target, count(DISTINCT item) FROM tags WHERE kind = 'approach'
                         GROUP BY 1 ORDER BY 2 DESC, 1""").fetchall()
    appr_bins = db.execute("""SELECT target, bin5(year), count(DISTINCT item) FROM tags WHERE kind = 'approach'
                              GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    by_theme = db.execute("""SELECT t.target, th.theme, count(DISTINCT t.item) FROM tags t JOIN themes th USING (item)
                             WHERE t.kind = 'approach' GROUP BY 1, 2 ORDER BY 1, 3 DESC""").fetchall()
    canon = db.execute("""SELECT decade, target, n FROM (
                              SELECT left(year, 3) || '0s' AS decade, target, count(DISTINCT item) AS n FROM tags
                              WHERE kind = 'person' AND year <> '' GROUP BY 1, 2)
                          QUALIFY row_number() OVER (PARTITION BY decade ORDER BY n DESC, target) <= 15
                          ORDER BY 1, 3 DESC""").fetchall()
    persons_total = db.execute("""SELECT target, count(DISTINCT item) FROM tags WHERE kind = 'person'
                                  GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 40""").fetchall()
    # Lift: share of a theme's scanned reviews invoking the approach, over the approach's overall share.
    db.execute("CREATE TABLE scanned AS SELECT DISTINCT item FROM tags UNION SELECT UNNEST(?::VARCHAR[])",
               [[f"hnet:review:{e}:{r}" if src == "hnet" else f"rih:review:{r}" for src, e, r, _, _ in reviews]])
    theme_size = dict(db.execute("""SELECT theme, count(DISTINCT item) FROM themes WHERE item IN (SELECT item FROM scanned)
                                    GROUP BY 1""").fetchall())
    scanned_n = len(reviews) if reviews else total
    overall = {t: n / scanned_n for t, n in appr}
    theme_top = defaultdict(list)
    for t, th, n in sorted(by_theme, key=lambda r: -(r[2] / max(theme_size.get(r[1], 1), 1))):
        if n >= 15 and len(theme_top[t]) < 6 and overall.get(t):
            share = n / theme_size[th]
            theme_top[t].append({"theme": th, "reviews": n, "theme_reviews": theme_size[th],
                                 "lift": round(share / overall[t], 2)})
    summary = {
        "inputs": {"upstream_catalog_sha256": up_sha, "series": args.series, "registry": args.registry},
        "reviews_scanned": len(reviews) if reviews else total,
        "approach_invocations": [{"target": t, "label": labels.get(t, t), "reviews": n,
                                  "share": round(n / total, 4)} for t, n in appr],
        "approach_by_5yr": defaultdict(dict),
        "approach_top_themes": {t: v for t, v in theme_top.items()},
        "operational_canon_by_decade": defaultdict(list),
        "most_invoked_people": [{"person": people[p], "reviews": n} for p, n in persons_total],
    }
    for t, b, n in appr_bins:
        summary["approach_by_5yr"][t][b] = n
    for d, p, n in canon:
        summary["operational_canon_by_decade"][d].append({"person": people[p], "reviews": n})
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("reviews_scanned",)}))
    print("approaches:", [(x["label"][:28], x["reviews"]) for x in summary["approach_invocations"]])
    print("most invoked:", [(x["person"], x["reviews"]) for x in summary["most_invoked_people"][:25]])


if __name__ == "__main__":
    main()
