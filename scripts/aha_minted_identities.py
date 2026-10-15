#!/usr/bin/env python3
"""Pilot: historians the registry can establish from an AHA dissertation and their own articles.

The registry's `aha_dissertation` route (scripts/aha_dissertation_route.py) only attaches an AHA
record to an individual the registry already knows (atlas, ORCID, Open Library, Wikidata). A
historian with no ORCID and no Wikidata item, whose only footprint is a dissertation and a few
articles without deposited ORCIDs, stays unresolved on both sides. This pilot treats each
unlinked AHA record (name, year, school, topic) as a candidate local person and asks which
unresolved Crossref credits belong to it.

A credit is name-gated against every AHA record (exact folded family name, compatible given
names), then needs content evidence:

  title        the article title shares >= 2 content words with the dissertation title, at least
               one uncommon in AHA titles (the route's own stopwords and COMMON_DF)
  timing       the article appeared in [PhD - 3, PhD + 15]
  affiliation  the credit's printed affiliation is the PhD school, dated [PhD - 3, PhD + 3]

  anchored     title (two uncommon shared words) + timing, or title + affiliation, with no
               competitor
  probable     title (one uncommon word) + timing, or two uncommon words after PhD + 15 (up to
               + 40), with no competitor
  conflict     the credit is supported for two AHA records (namesakes), or for an AHA record and
               an individual the registry already established

Gate: a credit dated more than ten years before the PhD is never attached (namesake signature).
Records are reported with existing-namesake flags: name-compatible individuals the registry
already holds (with or without ORCID/QID) and name-compatible Wikidata scholars
(data/wikidata/scholars-broad.csv, labels only). A flagged person may already have an identity
the routes did not reach; the flags say so instead of claiming "no ORCID or Wikidata".

Records are classified (kind_of): article (6+ pages, or a single-author record with only a
first page and no review markers), reviewed_book (a later credit on a multi-author record with
only a first page: JSTOR-era review deposits credit the reviewed books' authors after the
reviewer), review (the first credit on such a record, Crossref's book-citation hint, review title
patterns), short, unknown_length. The focus set is a historian with a
dissertation and at least one attached article; a PhD with no publication here is out of scope.

Read-only against a built registry. Writes CSVs and summary.json to --out.

    python3 scripts/aha_minted_identities.py --registry data/person-registry/generated/v12 \
        --out data/person-registry/generated/aha-minted-pilot
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import sqlite3

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aha_dissertation_route as aha  # noqa: E402
import identity_routes as ir  # noqa: E402

CROSSREF = [ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb",
            ROOT / "data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb"]
SCHOLARS = ROOT / "data/wikidata/scholars-broad.csv"
HNET = ROOT / "data/hnet-graph/generated/graph.sqlite"
UNIFIED = ROOT / "data/unified-graph/generated/nodes.csv"
BOOK_ROLES = ("contributor_unspecified", "editor")
REVIEW_TITLE = re.compile(r"^\s*(review|reviewed work|book review|compte rendu|rezension)\b|"
                          r"\bpp\.\s*[xvil\d]|\$\s?\d|£\s?\d|\b\d{3,4}\.\s*pp\b|"
                          r"university press|\bpress,|\bverlag\b|[ée]ditions\b|\(eds?\.?\)|\beds?\.,", re.I)
# Citation-style review titles, case-sensitive: "… by Linh D. Vu", "Eugen Weber. Peasants into
# Frenchmen …", a leading colon (": The Jewish Body …"), "City: Publisher".
REVIEW_CITATION = re.compile(r"\bby [A-Z][\w'’-]+\.?(?: [A-Z]\.)*(?: [A-Z][\w'’-]+)|"
                             r"^[A-Z][\w'’-]+(?: [A-Z]\.)*(?: [A-Z][\w'’-]+){1,3}\. [A-Z]|"
                             r"^\s*:|\b[A-Z][a-z]+(?: [A-Z][a-z]+)?: [A-Z][\w&]+(?: [A-Z][\w&]+)* (?:Press|Books|Publishers)\b")


def kind_of(title, hint, pages, band, position, n_authors, last_page):
    """JSTOR-era Crossref deposits of book reviews credit the reviewer first and the reviewed
    books' authors after, with only a first page: a later credit on such a record is the person's
    own book being reviewed, the first is the review's author."""
    if n_authors > 1 and last_page is None:
        return "reviewed_book" if position > 1 else "review"
    if hint or REVIEW_TITLE.search(title or "") or REVIEW_CITATION.search(title or ""):
        return "review"
    if pages is not None and pages >= 6 or band in ("10-19", "20-39", "40-200"):
        return "article"
    if pages is not None and pages <= 3 or band == "1-3":
        return "short"
    # Single author, first page only, no review markers: in samples almost always an article.
    return "article_unpaged" if last_page is None else "unknown_length"


def readings(name, given, family):
    """(given tokens, family tuple) readings: Crossref's structured split first, then the string."""
    out = []
    if family and given:
        out.append((ir.tokens(given), tuple(ir.tokens(family))))
    out.extend(aha.name_parts(name))
    return [(g, f) for g, f in out if g and f]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261015)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(args.registry / "registry.duckdb"), read_only=True)
    for i, path in enumerate(CROSSREF):
        db.execute(f"ATTACH '{path}' AS x{i} (READ_ONLY)")
    q = lambda s: db.execute(s).fetchall()

    # ---- AHA records: all of them name-gate (namesakes compete); unlinked ones can be minted ----
    recs = {}
    for rid, diss, dept, title, year in q("SELECT aha_id, dissertator, department, title, year FROM aha_dissertations"):
        given, family = aha.split_aha(diss)
        if year and family and given:
            recs[rid] = dict(id=rid, dissertator=diss, department=dept, title=title, year=year,
                             given=given, family=tuple(family), cw=aha.content_words(title))
    linked = {r[0].split(":")[-1]: r[1] for r in q(
        "SELECT occurrence_id, individual_id FROM occurrence_resolution WHERE corpus = 'aha' AND status IS NOT NULL")}
    common = aha.common_words(recs.values())
    by_family = defaultdict(list)
    for r in recs.values():
        by_family[r["family"]].append(r)

    # Existing namesakes from v12's name-gated pairs (people the registry already holds).
    existing = defaultdict(lambda: dict(n=0, with_id=0))
    for rid, n, with_id in q("""
            SELECT c.aha_id, count(DISTINCT c.individual_id),
                   count(DISTINCT CASE WHEN s.has_id THEN c.individual_id END)
            FROM aha_candidates c LEFT JOIN (
                SELECT individual_id, bool_or(node LIKE 'wd:%' OR node LIKE 'orcid:%') AS has_id
                FROM individuals GROUP BY 1) s USING (individual_id)
            GROUP BY 1"""):
        existing[rid] = dict(n=n, with_id=with_id)

    # Wikidata scholars by folded family name (labels only).
    wd_family = defaultdict(list)
    with open(SCHOLARS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for g, fam in aha.name_parts(row["label"]):
                wd_family[fam].append((g, row["qid"], row["label"], row["birth"][:4], row["occupations"]))

    def wd_namesakes(r):
        out = []
        for g, qid, label, birth, occ in wd_family.get(r["family"], ()):
            if aha.given_compatible(g, r["given"]):
                b = int(birth) if birth.lstrip("-").isdigit() else None
                if b is None or b + 20 <= r["year"] <= b + 65:
                    out.append(f"{qid} {label} ({birth or '?'}; {occ[:60]})")
        return sorted(set(out))

    # ---- unresolved Crossref author credits with their record ----
    rows = q("""
        SELECT o.occurrence_id, o.name, o.given_name, o.family_name, o.affiliation, o.venue, o.record_id,
               TRY_CAST(o.record_date AS INT), r.title_text, r.subtitle_text, r.book_citation_title_hint,
               r.page_count, r.length_band, TRY_CAST(split_part(o.occurrence_id, ':', 4) AS INT), a.n, r.last_page
        FROM occurrence_resolution res JOIN occurrences o USING (occurrence_id)
        JOIN (SELECT * FROM x0.records UNION ALL SELECT * FROM x1.records) r ON r.record_id = o.record_id
        JOIN (SELECT record_id, count(*) AS n FROM occurrences WHERE corpus = 'crossref' AND role LIKE '%author%'
              GROUP BY 1) a ON a.record_id = o.record_id
        WHERE res.corpus = 'crossref' AND res.status IS NULL AND o.role LIKE '%author%'""")
    # Credits the registry did resolve, by name: an established individual competing for a record.
    resolved_names = defaultdict(set)
    for name, given, family, ind in q("""
            SELECT o.name, o.given_name, o.family_name, res.individual_id FROM occurrence_resolution res
            JOIN occurrences o USING (occurrence_id)
            WHERE res.corpus = 'crossref' AND res.status IS NOT NULL AND res.individual_id IS NOT NULL"""):
        for g, fam in readings(name, given, family):
            resolved_names[fam].add((tuple(g), ind))

    # Titles of books known to be reviewed: a single-author, first-page-only Crossref record with
    # one of these titles is the person's own book under review (Dyer, NEQ 1934), not an article.
    item_titles = {}
    hn = sqlite3.connect(f"file:{HNET}?mode=ro", uri=True)
    for iid, title, year in hn.execute("SELECT id, title, publication_year FROM items"):
        item_titles[iid] = (title, year)
    for iid, label, data in db.execute(f"""SELECT id, label, data FROM read_csv('{UNIFIED}', header=true,
            all_varchar=true, max_line_size=20000000) WHERE origin = 'reviews_in_history'
            AND kind IN ('bibliographic_item', 'reviewed_item')""").fetchall():
        m = re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", json.loads(data).get("imprint") or "")
        item_titles[iid] = (label, int(m.group(1)) if m else None)
    reviewed_keys = {ir.title_key(t) for t, _ in item_titles.values() if t}
    reviewed_keys |= {ir.title_key(" ".join(t for t in (r[8], r[9]) if t)) for r in rows
                      if r[14] > 1 and r[15] is None}
    reviewed_keys.discard(None)

    # Candidate credits: (occurrence, corpus, name, given, family, affiliation, venue, year, title, kind).
    cands = []
    for occ, name, given, family, affil, venue, rec_id, year, title, sub, hint, pages, band, pos, n_auth, last in rows:
        full = " ".join(t for t in (title, sub) if t)
        kind = kind_of(full, hint, pages, band, pos or 1, n_auth, last)
        if kind == "article_unpaged" and ir.title_key(full) in reviewed_keys:
            kind = "reviewed_book"
        cands.append((occ, "crossref", name, given, family, affil, venue, year, full, kind))
    # H-Net and Reviews in History: book authors/editors by their item (book year when known),
    # reviewers by the items their review covers (review year).
    rec_items = defaultdict(set)
    hr = q("""SELECT o.occurrence_id, o.corpus, o.record_id, o.item_id, o.role, o.name, o.affiliation, o.venue,
                     TRY_CAST(left(o.record_date, 4) AS INT), res.status
              FROM occurrences o JOIN occurrence_resolution res USING (occurrence_id)
              WHERE o.corpus IN ('hnet', 'rih') AND o.role IN ('reviewer', 'contributor_unspecified', 'editor')""")
    for occ, corpus, rec_id, item, role, *_ in hr:
        if item:
            rec_items[rec_id].add(item)
    for occ, corpus, rec_id, item, role, name, affil, venue, year, status in hr:
        if status:
            continue
        items = [item] if role in BOOK_ROLES else sorted(rec_items[rec_id])
        for it in items:
            title, book_year = item_titles.get(it, (None, None))
            if title:
                cands.append((occ, corpus, name, None, None, affil, venue,
                              book_year or year if role in BOOK_ROLES else year, title,
                              "own_book" if role in BOOK_ROLES else "review"))

    pairs = []
    for occ, corpus, name, given, family, affil, venue, year, full, kind in cands:
        cw = aha.content_words(full)
        if not cw:
            continue
        seen = set()
        for g, fam in readings(name, given, family):
            for r in by_family.get(fam, ()):
                if r["id"] in seen or not aha.given_compatible(g, r["given"]):
                    continue
                seen.add(r["id"])
                shared = r["cw"] & cw
                rare = shared - common
                if len(shared) < 2 or not rare:
                    continue
                y = r["year"]
                if year is not None and year < y - 10:
                    gate = "before_phd"
                else:
                    gate = None
                timing = year is not None and y - 3 <= year <= y + 15
                later = year is not None and y + 15 < year <= y + 40
                inst = aha.institution(r["department"])
                aff = bool(affil and year is not None and abs(year - y) <= 3 and ir.org_match(inst, affil))
                if gate:
                    tier = None
                elif len(rare) >= 2 and timing or aff:
                    tier = "anchored"
                elif timing or len(rare) >= 2 and later:
                    tier = "probable"
                else:
                    tier = None
                pairs.append(dict(occurrence_id=occ, corpus=corpus, aha_id=r["id"], name=name, year=year, title=full[:300],
                                  venue=venue, affiliation=affil or "", kind=kind,
                                  shared=" ".join(sorted(shared)), rare=len(rare), timing=timing, later=later,
                                  affiliation_match=aff, gate=gate or "", tier=tier or ""))

    # ---- competition ----
    best = {}
    for p in pairs:
        k = (p["occurrence_id"], p["aha_id"])
        rank = (p["tier"] == "anchored", p["tier"] == "probable", p["rare"])
        if k not in best or rank > best[k][0]:
            best[k] = (rank, p)
    pairs = [p for _, p in best.values()]
    per_credit = defaultdict(set)
    for p in pairs:
        if p["tier"]:
            per_credit[p["occurrence_id"]].add(p["aha_id"])
    for p in pairs:
        if not p["tier"]:
            continue
        if len(per_credit[p["occurrence_id"]]) > 1:
            p["conflict"], p["tier"] = "credit supported for several AHA records", "conflict"
        elif p["aha_id"] in linked:
            # Not minted: the record already belongs to an established individual, which this
            # credit would extend (a separate, simpler route).
            p["conflict"], p["tier"] = "record linked to " + linked[p["aha_id"]], "extends_existing"

    # ---- per-record individuals (unlinked records only) ----
    out_people = []
    by_rec = defaultdict(list)
    for p in pairs:
        if p["tier"] in ("anchored", "probable"):
            by_rec[p["aha_id"]].append(p)
    for rid, ps in by_rec.items():
        r = recs[rid]
        tier = "anchored" if any(p["tier"] == "anchored" for p in ps) else "probable"
        # Distinct works per kind: one article deposited under a JSTOR and a publisher DOI, or
        # one book reviewed in several venues, counts once.
        kinds = Counter(k for k, _ in {(p["kind"] if p["kind"] != "article_unpaged" else "article",
                                         " ".join(ir.tokens(p["title"]))) for p in ps})
        ex = existing[rid]
        wd = wd_namesakes(r)
        # A resolved Crossref credit by a compatible name: the person may already be established.
        est = {ind for g, ind in resolved_names.get(r["family"], ()) if aha.given_compatible(list(g), r["given"])}
        flags = []
        if ex["n"]:
            flags.append(f"{ex['n']} registry namesake(s), {ex['with_id']} with ORCID/QID")
        if est:
            flags.append(f"{len(est)} established individual(s) with compatible Crossref credits")
        if wd:
            flags.append(f"{len(wd)} Wikidata scholar namesake(s)")
        out_people.append(dict(
            aha_id=rid, dissertator=r["dissertator"], school=aha.institution(r["department"]), year=r["year"],
            dissertation=r["title"], tier=tier, credits=len(ps),
            corpora="+".join(sorted({p["corpus"] for p in ps})),
            articles=kinds["article"], books=kinds["reviewed_book"] + kinds["own_book"],
            reviews_written=kinds["review"], short_or_unknown=kinds["short"] + kinds["unknown_length"],
            first_credit=min((p["year"] for p in ps if p["year"]), default=""),
            focus=bool(kinds["article"]), published_book=bool(kinds["reviewed_book"] + kinds["own_book"]), no_namesake_flags=not flags, flags="; ".join(flags),
            wikidata_namesakes=" | ".join(wd[:5]),
            sample_credit=max(ps, key=lambda p: (p["tier"] == "anchored", p["rare"]))["title"][:200]))

    out_people.sort(key=lambda x: (x["dissertator"], x["year"]))
    pair_fields = ["occurrence_id", "corpus", "aha_id", "name", "year", "title", "venue", "affiliation", "kind", "shared",
                   "rare", "timing", "later", "affiliation_match", "gate", "tier", "conflict"]
    with open(args.out / "credit-links.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, pair_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(pairs, key=lambda p: (p["aha_id"], p["year"] or 0)))
    people_fields = list(out_people[0]) if out_people else []
    with open(args.out / "minted-individuals.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, people_fields)
        w.writeheader()
        w.writerows(out_people)

    # Stratified review sample: focus individuals, anchored vs probable, flagged vs clean.
    rng = random.Random(args.seed)
    sample = []
    for tier in ("anchored", "probable"):
        for clean in (True, False):
            pool = [x for x in out_people if x["focus"] and x["tier"] == tier and x["no_namesake_flags"] == clean]
            sample += [dict(x, stratum=f"{tier}/{'clean' if clean else 'flagged'}")
                       for x in rng.sample(pool, min(15, len(pool)))]
    with open(args.out / "review-sample.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["stratum"] + people_fields + ["verdict", "checked_against", "note"])
        w.writeheader()
        w.writerows(sample)

    focus = [x for x in out_people if x["focus"]]
    summary = dict(
        registry=str(args.registry), aha_records=len(recs), aha_linked_in_registry=len(linked),
        unresolved_crossref_author_credits=len(rows),
        candidate_credits_by_corpus=dict(Counter(c[1] for c in cands)),
        attached_by_corpus=dict(Counter(p["corpus"] for v in by_rec.values() for p in v)),
        name_and_topic_pairs=len(pairs),
        pairs_by_tier=dict(Counter(p["tier"] or ("gated:" + p["gate"] if p["gate"] else "unsupported") for p in pairs)),
        credits_attached=sum(len(v) for v in by_rec.values()),
        minted_individuals=len(out_people),
        by_tier=dict(Counter(x["tier"] for x in out_people)),
        focus_with_article=len(focus),
        with_reviewed_book=sum(x["published_book"] for x in out_people),
        article_or_reviewed_book=sum(x["focus"] or x["published_book"] for x in out_people),
        focus_by_tier=dict(Counter(x["tier"] for x in focus)),
        focus_without_namesake_flags=sum(x["no_namesake_flags"] for x in focus),
        focus_clean_by_tier=dict(Counter(x["tier"] for x in focus if x["no_namesake_flags"])),
        credit_kinds=dict(Counter(p["kind"] for v in by_rec.values() for p in v)),
        phd_decades=dict(sorted(Counter(f"{x['year'] // 10 * 10}s" for x in focus).items())),
    )
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
