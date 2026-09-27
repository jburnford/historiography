"""Method signals: where methods are practised, including inside articles about other things.

EVIDENCE-LAYER-PLAN.md. User, 2026-09-26: "my digital history is spread out in articles about
other things ... I expect this is common." Venue and subject classifications cannot see methods,
so this builds two separate, never-merged measures per method:

  titles         whole-word, case-aware, multilingual lexicon over Crossref titles and subtitles
                 of research-length items. A LOWER BOUND: most method-using articles do not name
                 the method in their title. Precision is audited on a seeded sample.
  practitioners  people identified as practising a method, by (a) work in the method's venues,
                 claimed on their own ORCID record or credited in our Crossref collections, or
                 (b) the atlas roster of the method's entry. We then count their research-length
                 articles in the collection, split into method venues vs elsewhere. This attributes
                 the method to the person, not to each article: an upper-bound kind of measure.

Writes data/evidence-layer/generated/<version>/ (refuses to overwrite): summary.json,
title_hits.csv, practitioners.csv, audit-sample.csv (for precision judgement).
"""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data/evidence-layer/generated"
CATALOGS = [ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb",
            ROOT / "data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb"]
CLAIMS = ROOT / "data/person-registry/generated/orcid-claims/claimed-works.parquet"
GRAPH = ROOT / "historiography-1920-2000.json"
BORN_DIGITAL = {"journal_supplement_journal_of_digital_history"}

# Patterns are applied case-insensitively unless prefixed (?-i:...). Topic words that name a
# subject rather than a method (computers, the internet, AI, algorithms, cartography) are left out.
METHODS = {
    "digital_history": {
        "entries": ["digital_history", "web_history"],
        "title": [r"\bdigital(?:e|en|es|er|ly|i[sz]\w*)?\b", r"\bdigiti[sz]\w*", r"\bnum[ée]riques?\b",
                  r"\btext[- ]?mining\b", r"\btopic model\w*", r"\bmachine learning\b", r"\bcomputational\b",
                  r"\bweb archiv\w*", r"\bborn[- ]digital\b", r"(?-i:\bOCR\b)", r"\boptical character recognition\b",
                  r"\bdistant reading\b", r"\bbig data\b", r"\bnatural language processing\b", r"\bgeoparsing\b",
                  r"\bnetwork analysis\b", r"\bcorpus linguistic\w*"],
        "venues": ["journal of digital history", "current research in digital history", "internet histories",
                   "digital scholarship in the humanities", "literary and linguistic computing",
                   "digital humanities quarterly", "international journal of humanities and arts computing",
                   "programming historian", "historical methods"],
    },
    "quant": {
        "entries": ["quant"],
        # Audit v1 (20/30): bare "statistic*" mostly caught the history of statistics, "regression"
        # caught other senses. v2 requires method phrases.
        "title": [r"\bquantitativ\w*", r"\bquantif\w*", r"\bcliometric\w*", r"\bmicrodata\b", r"\brecord linkage\b",
                  r"\blinked census\b",
                  r"\bstatistical (?:analys[ie]s|methods?|model\w*|approach\w*|evidence|stud(?:y|ies)|investigation\w*)\b",
                  r"\banalyse statistique\b", r"\bregression (?:analys[ie]s|model\w*)\b",
                  r"\beconometric (?:analys[ie]s|model\w*|evidence|approach\w*|stud(?:y|ies)|estimat\w*)\b"],
        "venues": ["historical methods", "cliometrica", "social science history", "historical social research",
                   "historische sozialforschung", "explorations in economic history"],
    },
    "oral": {
        "entries": ["oral"],
        "title": [r"\boral histor\w*", r"\boral testimon\w*", r"\boral tradition\w*", r"\bhistoire orale\b",
                  r"\bhistoria oral\b", r"\bstoria orale\b", r"\bm[üu]ndlich\w*", r"\blife stor(?:y|ies)\b"],
        # Audit v1 (16/30): "interview" caught interviews WITH historians (a journal genre); dropped in v2.
        "venues": ["oral history review", "oral history forum", "words and silences",
                   "historia, antropología y fuentes orales"],
        "venue_exact": ["oral history"],
    },
    "spatialhistory": {
        "entries": ["spatialhistory"],
        "title": [r"(?-i:\bH?GIS\b)", r"\bgeographic(?:al)? information system\w*", r"\bgeospatial\b",
                  r"\bspatial(?:ity|ities|ly)?\b(?! planning| mobility)", r"\bgeoparsing\b"],
        # Audit v1 (24/30): v2 excludes the terms of art "spatial planning" and "spatial mobility".
        "venues": ["journal of historical geography", "historical geography",
                   "international journal of humanities and arts computing"],
    },
    "micro": {
        "entries": ["micro"],
        "title": [r"\bmicro-?histor\w*", r"\bmicrostori\w*", r"\bmicro-?histoire\w*", r"\bmikrogeschicht\w*"],
        "venues": ["quaderni storici", "microhistories"],
    },
}


def lit(p):
    return "'" + str(p).replace("'", "''") + "'"


def compile_method(spec):
    return [re.compile(p, re.I) for p in spec["title"]]


def venue_match(spec, journal):
    j = (journal or "").strip().lower()
    return any(v in j for v in spec["venues"]) or j in spec.get("venue_exact", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", default="v9")
    ap.add_argument("--version", default="methods-v1")
    ap.add_argument("--audit-seed", default="audit-2026-09-26", help="use a fresh seed to re-audit a revised lexicon")
    args = ap.parse_args()
    out = GEN / args.version
    if out.exists():
        raise SystemExit(f"{out} exists; choose a new --version")
    db = duckdb.connect()
    db.execute(f"ATTACH {lit(ROOT / 'data/person-registry/generated' / args.registry / 'registry.duckdb')} AS rg (READ_ONLY)")
    for i, c in enumerate(CATALOGS):
        db.execute(f"ATTACH {lit(c)} AS x{i} (READ_ONLY)")
    union = lambda t: " UNION ALL ".join(f"SELECT * FROM x{i}.{t}" for i in range(len(CATALOGS)))
    db.execute(f"CREATE TEMP VIEW recs AS {union('records')}")
    db.execute(f"CREATE TEMP VIEW mem AS {union('memberships')}")
    db.execute(f"CREATE TEMP VIEW jn AS {union('journals')}")
    db.execute("CREATE TEMP VIEW research AS " + " UNION ".join(
        f"SELECT record_id FROM x{i}.research_candidates_by_length" for i in range(len(CATALOGS))))
    # One row per research item with its (first) journal.
    items = db.execute("""
        SELECT r.record_id, lower(r.doi), coalesce(r.title_text, '') || ' ' || coalesce(r.subtitle_text, ''),
               TRY_CAST(r.publication_year AS INT), any_value(j.label), any_value(m.journal_key)
        FROM recs r JOIN mem m USING (record_id) JOIN jn j USING (journal_key)
        WHERE NOT coalesce(r.is_test_record, false)
          AND (r.record_id IN (SELECT record_id FROM research)
               OR (m.journal_key IN (SELECT UNNEST(?::VARCHAR[])) AND r.record_type = 'journal-article'))
        GROUP BY 1, 2, 3, 4""", [sorted(BORN_DIGITAL)]).fetchall()
    compiled = {m: compile_method(s) for m, s in METHODS.items()}
    # Abstracts (harvest_crossref_abstracts.py), if present: a separate measure with its coverage,
    # never used to correct the title count. HTML/JATS tags are stripped before matching.
    abstracts = {}
    adir = GEN / "abstracts"
    if (adir / "manifest.json").exists():
        import gzip
        for fpath in adir.glob("*.jsonl.gz"):
            with gzip.open(fpath, "rt", encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    abstracts[r["doi"]] = re.sub(r"<[^>]+>", " ", r["abstract"] or "")
    abstract_hits = defaultdict(set)
    with_abstract = 0
    for rid, doi, title, year, journal, jkey in items:
        a = abstracts.get(doi)
        if a:
            with_abstract += 1
            for m, pats in compiled.items():
                if any(p.search(a) for p in pats):
                    abstract_hits[m].add(rid)
    hits = []
    for rid, doi, title, year, journal, jkey in items:
        for m, pats in compiled.items():
            matched = sorted({p.pattern for p in pats if p.search(title)})
            if matched:
                hits.append((m, rid, doi, year, journal, title.strip(), "|".join(matched)))

    # Practitioners. (a) venue work claimed on ORCID or credited in our collections; (b) atlas rosters.
    claims = db.execute(f"SELECT orcid, journal FROM read_parquet({lit(CLAIMS)}) WHERE journal IS NOT NULL").fetchall()
    orcid_ind = dict(db.execute("SELECT substr(node, 7), individual_id FROM rg.individuals WHERE node LIKE 'orcid:%'").fetchall())
    credits = db.execute("""
        SELECT r.individual_id, o.record_id FROM rg.occurrence_resolution r JOIN rg.occurrences o USING (occurrence_id)
        WHERE o.corpus = 'crossref' AND r.individual_id IS NOT NULL""").fetchall()
    item_journal = {rid: journal for rid, _, _, _, journal, _ in items}
    item_year = {rid: year for rid, _, _, year, _, _ in items}
    by_ind = defaultdict(set)
    for ind, rid in credits:
        if rid in item_journal:
            by_ind[ind].add(rid)
    g = json.loads(GRAPH.read_text())
    atlas_ind = dict(db.execute("""SELECT substr(occurrence_id, 14), individual_id FROM rg.occurrence_resolution
                                   WHERE corpus = 'atlas' AND individual_id IS NOT NULL""").fetchall())
    roster = defaultdict(set)
    for n in g["nodes"]:
        ids = {p["person_id"] for p in n.get("representative_people") or []}
        ids |= {pid for s in n.get("strands") or [] for pid in s.get("person_ids") or []}
        roster[n["id"]] = ids

    summary, prac_rows = {}, []
    for m, spec in METHODS.items():
        pr = defaultdict(set)
        for orcid, journal in claims:
            if venue_match(spec, journal) and orcid.upper() in orcid_ind:
                pr[orcid_ind[orcid.upper()]].add("orcid_claim_venue")
        for ind, rids in by_ind.items():
            if any(venue_match(spec, item_journal[r]) for r in rids):
                pr[ind].add("collection_venue_credit")
        for e in spec["entries"]:
            for pid in roster.get(e, ()):
                if pid in atlas_ind:
                    pr[atlas_ind[pid]].add("atlas_roster:" + e)
        in_venue = elsewhere = 0
        per_year = defaultdict(lambda: [0, 0])
        for ind, bases in pr.items():
            rids = by_ind.get(ind, set())
            v = sum(1 for r in rids if venue_match(spec, item_journal[r]))
            in_venue += v
            elsewhere += len(rids) - v
            for r in rids:
                y = item_year.get(r)
                if y:
                    per_year[y][0 if venue_match(spec, item_journal[r]) else 1] += 1
            prac_rows.append((m, ind, "|".join(sorted(bases)), len(rids), v))
        mh = [h for h in hits if h[0] == m]
        title_ids = {h[1] for h in mh}
        summary[m] = {
            "title_hits_research_items": len(mh),
            "abstract": {"research_items_with_abstract": with_abstract,
                         "abstract_hits": len(abstract_hits[m]),
                         "abstract_hits_not_in_title": len(abstract_hits[m] - title_ids),
                         "title_or_abstract_hits": len(title_ids | abstract_hits[m])} if abstracts else None,
            "title_hits_by_decade": {f"{d}s": sum(1 for h in mh if h[3] and h[3] // 10 * 10 == d)
                                     for d in range(1950, 2030, 10)},
            "practitioners": len(pr),
            "practitioners_by_basis": {b: sum(1 for s in pr.values() if any(x.startswith(b) for x in s))
                                       for b in ("orcid_claim_venue", "collection_venue_credit", "atlas_roster")},
            "practitioner_research_items": in_venue + elsewhere,
            "practitioner_items_in_method_venues": in_venue,
            "practitioner_items_elsewhere": elsewhere,
            "share_elsewhere": round(elsewhere / (in_venue + elsewhere), 3) if in_venue + elsewhere else None,
            "practitioner_items_by_decade_venue_vs_elsewhere": {
                f"{d}s": [sum(per_year[y][0] for y in per_year if y // 10 * 10 == d),
                          sum(per_year[y][1] for y in per_year if y // 10 * 10 == d)] for d in range(1950, 2030, 10)},
        }
    out.mkdir(parents=True)
    with open(out / "title_hits.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "record_id", "doi", "year", "journal", "title", "patterns"]); w.writerows(hits)
    with open(out / "practitioners.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "individual_id", "bases", "research_items", "in_method_venues"]); w.writerows(prac_rows)
    # Seeded audit sample: 30 title hits per method, deterministic by hash of record id.
    with open(out / "audit-sample.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "year", "journal", "title", "patterns", "judgment"])
        for m in METHODS:
            mh = sorted((h for h in hits if h[0] == m),
                        key=lambda h: hashlib.sha256((h[1] + args.audit_seed).encode()).hexdigest())[:30]
            for h in mh:
                w.writerow([m, h[3], h[4], h[5][:200], h[6], ""])
    (out / "summary.json").write_text(json.dumps({"research_items": len(items), "methods": summary}, indent=2) + "\n")
    print(json.dumps({"research_items": len(items), **{m: {k: v for k, v in s.items() if "decade" not in k}
                                                        for m, s in summary.items()}}, indent=1))


if __name__ == "__main__":
    main()
