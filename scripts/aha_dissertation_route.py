"""The registry's `aha_dissertation` route: person -> AHA Directory of History Dissertations record.

A unique AHA name is not a unique person. The directory covers only US and Canadian history
PhDs, so a historian trained elsewhere usually has a North American namesake there (Fritz
Fischer -> Northwestern 1994, Richard J. Evans -> Temple 2018, Mary Douglas -> Harvard 1967).
The name gate therefore only proposes candidates; a link needs an evidence channel:

  title     a known work of the person shares >= 2 content words with the dissertation title
            (one work at a time, stopwords and field-generic words removed)
            When title is the only content evidence and only one shared word is uncommon, the
            link needs timing and no competitor, and stays probable.
  timing    the person's first dated work falls in [PhD year - 3, PhD year + 15]
  book      a known book sharing >= 2 content words appeared within [PhD - 1, PhD + 10]
  school    an ORCID education/qualification entry (or a doctoral-student employment entry)
            names the AHA school, dated at the PhD year or explicitly doctoral
  advisor   the person's Wikidata doctoral advisor (P184), or a reviewed manual link, names an
            advisor listed on the AHA record (manual links must also agree on the school)

Gates that reject a candidate outright: name (exact folded surname, compatible given names),
lifespan (PhD before age 20, after age 65 or after death), and a dated work more than ten years before
the PhD (the namesake signature: Richard J. Evans published in 1976, the Temple PhD is 2018).

Tiers: anchored = (title and timing, or title and book, or two of title/school/advisor) with
no competing candidate; probable = any one channel, or a competing candidate on either side
(another supported individual for the record, or another supported record for the person).
Accepted only through the human ledger data/person-registry/aha-identity-decisions.csv.
Married-name changes, nicknames and family-name-first orders are out of scope.
"""
import csv
import re
from collections import defaultdict

import identity_routes as ir

# Function words (English, French, German, Spanish, Italian) and words generic across the
# AHA's 61,559 titles; content words are what is left with more than three letters.
STOP = set("""
about above across after against along also among amongst around because been before being
below beneath between beyond both could dans des during each eine einer eines from have into
itself just more most much only other others over pour same since some such than that their
them then there these they this those through thus toward towards under unter until upon very
what when where which while whom with within without would your über uber zwischen nach sobre
para como entre desde avec sans leur leurs cette dalla della delle degli also
history histories historical historiography study studies century centuries american america
united states early late modern world during development making case role rise origins life
lives career first great change transformation aspects introduction period years thought
essay essays examination analysis perspective perspectives approach view toward new
university college press volume edition review reviews dissertation thesis
""".split())
COMMON_DF = 300  # a word in more AHA titles than this is common; two common words alone are weak

POSTDOC = re.compile(r"post-?\s?doc", re.I)
DOCTORAL = re.compile(r"ph\.?\s?d|doct|dphil|d\.\s?phil|graduate student|candidate", re.I)
NON_DOCTORAL = re.compile(r"\b(b\.?\s?a|m\.?\s?a|b\.?\s?sc|m\.?\s?sc|m\.?\s?phil|bachelor|master|ll\.?\s?b|j\.?\s?d|"
                          r"licen[cs]|undergrad|postdoc|post-doc|lecturer|professor)\b", re.I)
YEAR = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")


def stem(w):
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def content_words(title):
    if not title or title.strip() == "[No title]":
        return frozenset()
    return frozenset(stem(t) for t in re.split(r"[^a-z]+", ir.fold(title)) if len(t) > 3 and t not in STOP)


def split_aha(dissertator):
    """'Kealey, Gregory S.' -> (['gregory', 's'], ['kealey'])."""
    family, _, given = (dissertator or "").partition(",")
    return ir.tokens(given), ir.tokens(family)


def _tok_ok(a, b):
    return a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))


def given_compatible(name_given, aha_given):
    """First given names agree (or one is the other's initial); second given names agree when
    both sides have one. A person known by their middle name ('Richard Smith' for 'Smith, John
    Richard') is allowed when the full middle name matches."""
    a, b = name_given, aha_given
    if not a or not b:
        return False
    if _tok_ok(a[0], b[0]):
        return not (len(a) > 1 and len(b) > 1) or _tok_ok(a[1], b[1])
    return len(a[0]) > 1 and len(b) > 1 and a[0] == b[1] or len(b[0]) > 1 and len(a) > 1 and b[0] == a[1]


def name_parts(name):
    """Name string -> list of (given tokens, family-token tuple) readings, 'Given Family' or
    'Family, Given'. Family readings of one to three trailing tokens."""
    if not name:
        return []
    if "," in name:
        family, _, given = name.partition(",")
        g, f = ir.tokens(given), ir.tokens(family)
        return [(g, tuple(f))] if g and f else []
    t = ir.tokens(name)
    return [(t[:-k], tuple(t[-k:])) for k in (1, 2, 3) if len(t) > k]


def name_compatible(name, aha_given, aha_family):
    return any(f == tuple(aha_family) and given_compatible(g, aha_given) for g, f in name_parts(name))


def institution(department):
    """'Univ. of California, Berkeley, Dept. of History' -> 'University of California, Berkeley'."""
    parts = [p.strip() for p in (department or "").split(",")]
    unit = re.compile(r"dept|dépt|department|program|prog\.|school|graduate|committee|faculty|div\.|"
                      r"division|center|centre|histor|humanities|studies", re.I)
    keep = [p for p in parts if p and not unit.search(p)] or parts[:1]
    s = ", ".join(keep)
    return re.sub(r"\bInst\.", "Institute", re.sub(r"\bUniv\.", "University", s))


def parse_atlas_works(works):
    """'The Gender of Breadwinners (1990); "Gender History and Historical Practice" (1995)' ->
    [(title, year, kind)], kind 'book' unless the title is quoted."""
    out = []
    for piece in (works or "").split(";"):
        piece = piece.strip()
        if not piece or piece.lower().startswith("later"):
            continue
        m = re.search(r"\(([^)]*)\)", piece)
        year = None
        if m and YEAR.search(m.group(1)):
            year = int(YEAR.search(m.group(1)).group(1))
        title = piece[:m.start()].strip() if m else piece
        kind = "article" if re.match(r"^[\"“‘']", title) else "book"
        out.append((title.strip("\"“”‘’' "), year, kind))
    return out


def school_entry_ok(entry, phd_year):
    """ORCID affiliation entry (section, org, role, start, end) consistent with a PhD in phd_year."""
    section, _org, role, start, end = entry
    role = role or ""
    doctoral = bool(DOCTORAL.search(role)) and not POSTDOC.search(role)
    if section == "employment" and not doctoral:
        return False
    if not doctoral and NON_DOCTORAL.search(role):
        return False
    if end is not None:
        return phd_year - 1 <= end <= phd_year + 1 or (start is not None and start <= phd_year <= end + 1 and doctoral)
    if start is not None:
        return doctoral and start <= phd_year <= start + 10
    return doctoral


def shares(cw, title, common):
    """Content words shared with a work title, or empty when every shared word is common."""
    shared = cw & content_words(title)
    return shared if shared - common else frozenset()


def evaluate(record, person, common=frozenset()):
    """record: dict(id, year, title, department, advisors[list of names]); person: dict(works[(title,
    year, kind, source)], birth, death, education[(section, org, role, start, end)], wd_advisors[labels],
    manual[(advisor, institution)]). common: words too frequent in AHA titles to carry a match alone.
    Returns None when the record has no year, else a dict with gate, channels, strong, supported."""
    y = record["year"]
    if not y:
        return None
    gate = None
    if person.get("birth") is not None and not person["birth"] + 20 <= y <= person["birth"] + 65:
        gate = "lifespan"
    elif person.get("death") is not None and y > person["death"]:
        gate = "lifespan"
    dated = [w for w in person["works"] if w[1] and 1850 <= w[1] <= 2027]
    first = min((w[1] for w in dated), default=None)
    if gate is None and first is not None and first < y - 10:
        gate = "work_before_phd"
    cw = content_words(record["title"])
    scored = [(shares(cw, w[0], common), w) for w in person["works"]]
    best_shared, best = max(scored, key=lambda s: (len(s[0]), -(s[1][1] or 9999)), default=(frozenset(), None))
    title = len(best_shared) >= 2
    timing = first is not None and y - 3 <= first <= y + 15
    book = next((w for s, w in scored if w[2] == "book" and w[1] and y - 1 <= w[1] <= y + 10 and len(s) >= 2), None)
    # The person's own ORCID record lists this dissertation: near-identical title, year within one.
    thesis = next((w for s, w in scored if w[3] in ("orcid dissertation-thesis", "orcid dissertation")
                   and w[1] and abs(w[1] - y) <= 1 and len(s) >= max(3, (len(cw) + 1) // 2)), None)
    inst = institution(record["department"])
    school = next((e for e in person.get("education", []) if ir.org_match(inst, e[1]) and school_entry_ok(e, y)
                   and (e[4] is not None or first is None or first <= y + 25)), None)
    adv = None
    for a in record.get("advisors") or []:
        for label in person.get("wd_advisors", []):
            if ir.compatible(a, *ir.split_full(label)):
                adv = f"Wikidata P184 {label} = AHA advisor {a}"
        for m_adv, m_inst in person.get("manual", []):
            if ir.compatible(a, *ir.split_full(m_adv)) and ir.org_match(inst, m_inst):
                adv = f"manual link {m_adv} at {m_inst} = AHA advisor {a}"
    # A title match that is the only content evidence (timing aside, since dates are not content;
    # no book, thesis, school or advisor) needs two uncommon shared words in one work. Two common
    # words plus one rare word linked a namesake (David Johnson, Rice 2018: 'native' + 'south').
    # Weak title evidence (one uncommon word) survives only with timing and no competitor
    # (checked in assign_tiers), and then only as probable.
    weak_title = bool(title and not (book or thesis or school or adv)
                      and not any(len(sh - common) >= 2 for sh, _ in scored))
    if weak_title and not timing:
        title, weak_title = False, False
    channels = [c for c, ok in (("title", title), ("timing", title and timing), ("book", book), ("thesis", thesis),
                                ("school", school), ("advisor", adv)) if ok]
    independent = sum(bool(x) for x in (title, school, adv))
    strong = bool((title and (timing or book)) or thesis or independent >= 2) and not weak_title
    evidence = []
    if best_shared:
        evidence.append(f"title shares {sorted(best_shared)} with \"{best[0][:120]}\" ({best[1] or '?'}, {best[3]})")
    evidence.append(f"first dated work {first if first else '?'} vs PhD {y}")
    if book:
        evidence.append(f"book \"{book[0][:120]}\" ({book[1]}) within 10 years")
    if thesis:
        evidence.append(f"ORCID-claimed dissertation \"{thesis[0][:120]}\" ({thesis[1]})")
    if school:
        evidence.append(f"ORCID {school[0]} \"{school[1]}\" {school[2] or ''} "
                        f"{school[3] if school[3] is not None else '?'}-{school[4] if school[4] is not None else '?'}")
    if adv:
        evidence.append(adv)
    return dict(gate=gate, channels=channels if gate is None else [], strong=strong and gate is None,
                supported=gate is None and (independent >= 1 or bool(thesis)), first_work=first,
                shared=len(best_shared), weak_title=weak_title and gate is None,
                evidence="; ".join(evidence) + ("; weak title (one uncommon word)" if weak_title else ""))


def common_words(records, threshold=COMMON_DF):
    df = defaultdict(int)
    for r in records:
        for w in content_words(r["title"]):
            df[w] += 1
    return frozenset(w for w, n in df.items() if n > threshold)


def assign_tiers(proposals):
    """proposals: list of dicts with aha_id, individual_id, supported, strong (and optionally
    weak_title). Sets 'status': anchored / probable / None (unsupported), and 'competitors'.
    A weak-title proposal (one uncommon shared word, title its only content evidence) is dropped
    when any other supported proposal competes for its record or its individual; the tiers are
    then computed over what remains."""
    def competitors(props):
        per_rec, per_ind = defaultdict(set), defaultdict(set)
        for p in props:
            if p["supported"]:
                per_rec[p["aha_id"]].add(p["individual_id"])
                per_ind[p["individual_id"]].add(p["aha_id"])
        return lambda p: len(per_rec[p["aha_id"]]) - 1 + len(per_ind[p["individual_id"]]) - 1

    comp = competitors(proposals)
    for p in proposals:
        if p["supported"] and p.get("weak_title") and comp(p) > 0:
            p["supported"], p["strong"] = False, False
            p["gate"] = "weak_title_competitor"
    comp = competitors(proposals)
    for p in proposals:
        if not p["supported"]:
            p["status"], p["competitors"] = None, 0
            continue
        p["competitors"] = comp(p)
        p["status"] = "anchored" if p["strong"] and p["competitors"] == 0 else "probable"
    return proposals


def read_aha(path):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            given, family = split_aha(r["dissertator"])
            out.append(dict(id=r["id"], dissertator=r["dissertator"], given=given, family=tuple(family),
                            department=r["department"], orgcd=r["orgcd"], title=r["title"],
                            year=int(r["year"]) if r["year"] else None,
                            advisors=[a.strip() for a in r["advisors"].split(";") if a.strip()],
                            advisor_ids=[a.strip() for a in r["advisor_ids"].split(";") if a.strip()]))
    return out


# ---- registry plumbing ---------------------------------------------------------------------
POSITIVE = "('accepted', 'anchored', 'probable')"
NODE_PRIORITY = ("atlas:", "pilot:", "orcid:", "ol:")


def _representative(nodes):
    people = [n for n in nodes if not n.startswith("wd:")]
    return min(people, key=lambda n: (next((i for i, p in enumerate(NODE_PRIORITY) if n.startswith(p)), 9), n))


def gather(db, paths, lit):
    """Read-only: AHA records, name-gated candidate pairs and each candidate individual's evidence."""
    q = db.execute
    recs = {r["id"]: r for r in read_aha(paths["aha_records"]) if r["year"] and r["family"]}
    by_family = defaultdict(list)
    for r in recs.values():
        by_family[r["family"]].append(r)
    names = q(f"""
        SELECT DISTINCT i.individual_id, o.name FROM identity_links l JOIN individuals i ON i.node = l.person_id
          JOIN occurrences o USING (occurrence_id)
          WHERE (l.status IN {POSITIVE} OR o.corpus = 'atlas') AND o.corpus <> 'aha' AND o.name IS NOT NULL
        UNION SELECT i.individual_id, p.label FROM people p JOIN individuals i ON i.node = p.person_id
          WHERE p.label IS NOT NULL AND p.origin NOT IN ('atlas')
        UNION SELECT i.individual_id, trim(coalesce(n.given, '') || ' ' || coalesce(n.family, ''))
          FROM read_parquet({lit(paths['orcid_names'])}) n JOIN individuals i ON i.node = 'orcid:' || n.orcid
        UNION SELECT i.individual_id, unnest(n.other_names)
          FROM read_parquet({lit(paths['orcid_names'])}) n JOIN individuals i ON i.node = 'orcid:' || n.orcid
        """).fetchall()
    pairs = {}
    for ind, name in names:
        for given, family in name_parts(name):
            for r in by_family.get(family, ()):
                if given_compatible(given, r["given"]):
                    pairs.setdefault((ind, r["id"]), name)
    inds = sorted({i for i, _ in pairs})
    q("CREATE TEMP TABLE aha_cand (individual_id VARCHAR)")
    db.executemany("INSERT INTO aha_cand VALUES (?)", [(i,) for i in inds])
    persons = {i: dict(names=set(), works=[], education=[], wd_advisors=[], birth=None, death=None, nodes=[])
               for i in inds}
    for ind, name in names:
        if ind in persons:
            persons[ind]["names"].add(name)
    for ind, node in q("SELECT individual_id, node FROM individuals JOIN aha_cand USING (individual_id)").fetchall():
        persons[ind]["nodes"].append(node)
    works = q(f"""
        SELECT i.individual_id, cb.title, cb.year, 'book', o.corpus
          FROM credit_book cb JOIN identity_links l USING (occurrence_id) JOIN occurrences o USING (occurrence_id)
          JOIN individuals i ON i.node = l.person_id JOIN aha_cand USING (individual_id)
          WHERE l.status IN {POSITIVE}
        UNION SELECT i.individual_id, trim(coalesce(r.title_text, '') || ' ' || coalesce(r.subtitle_text, '')),
               r.publication_year, CASE WHEN r.record_type LIKE 'book%' AND r.record_type <> 'book-chapter'
                                        THEN 'book' ELSE 'article' END, 'crossref'
          FROM identity_links l JOIN occurrences o USING (occurrence_id) JOIN x_records r ON r.record_id = o.record_id
          JOIN individuals i ON i.node = l.person_id JOIN aha_cand USING (individual_id)
          WHERE o.corpus = 'crossref' AND l.status IN {POSITIVE}
        UNION SELECT i.individual_id, trim(coalesce(c.title, '') || ' ' || coalesce(c.subtitle, '')),
               TRY_CAST(left(c.year, 4) AS INT), CASE WHEN c.type IN ('book', 'edited-book') THEN 'book' ELSE 'other' END,
               'orcid ' || c.type
          FROM cw c JOIN individuals i ON i.node = 'orcid:' || c.orcid JOIN aha_cand USING (individual_id)
        """).fetchall()
    for ind, title, year, kind, source in works:
        if title:
            persons[ind]["works"].append((title, year, kind, source))
    node_ind = {n: i for i, p in persons.items() for n in p["nodes"]}
    atlas = __import__("json").loads(paths["atlas_graph"].read_text())
    for node in atlas["nodes"]:
        for rp in node.get("representative_people") or []:
            ind = node_ind.get("atlas:" + rp["person_id"])
            if ind:
                persons[ind]["works"].extend((t, y, k, "atlas") for t, y, k in parse_atlas_works(rp.get("works")))
    for ind, section, org, role, start, end in q(f"""
            SELECT i.individual_id, a.section, a.org, a.role, CAST(a.start_year AS INT), CAST(a.end_year AS INT)
            FROM read_parquet({lit(paths['orcid_affiliations'])}) a JOIN individuals i ON i.node = 'orcid:' || a.orcid
            JOIN aha_cand USING (individual_id) WHERE a.org IS NOT NULL""").fetchall():
        persons[ind]["education"].append((section, org, role, start, end))
    for ind, label in q(f"""
            SELECT DISTINCT i.individual_id, p.advisor_label FROM read_csv({lit(paths['wikidata_p184'])}, delim='\t',
              header=true, quote='', all_varchar=true) p JOIN individuals i ON i.node = 'wd:' || p.qid
            JOIN aha_cand USING (individual_id) WHERE p.advisor_label IS NOT NULL AND p.advisor_label <> ''""").fetchall():
        persons[ind]["wd_advisors"].append(label)
    for ind, birth, death in q("""
            SELECT i.individual_id, min(ls.birth_year), max(ls.death_year) FROM lifespans ls
            JOIN individuals i ON i.node = 'wd:' || ls.qid JOIN aha_cand USING (individual_id) GROUP BY 1""").fetchall():
        persons[ind].update(birth=birth, death=death)
    sheet = __import__("json").loads(paths["atlas_wikidata"].read_text())
    for row in sheet["people"]:
        ind, life = node_ind.get("atlas:" + row["person_id"]), row.get("life") or {}
        if ind:
            for key in ("birth", "death"):
                y = YEAR.match((life.get(key) or "").lstrip("+"))
                if y and persons[ind][key] is None:
                    persons[ind][key] = int(y.group(1))
    manual = list(csv.DictReader(open(paths["aha_manual_links"], newline="", encoding="utf-8")))
    return recs, persons, pairs, manual


def propose(recs, persons, pairs, manual, decisions):
    """Evaluate every name-gated pair, apply the human ledger, assign tiers."""
    props, common = [], common_words(recs.values())
    for (ind, rid), matched in sorted(pairs.items()):
        r, p = recs[rid], persons[ind]
        man = [(m["advisor"], m["institution"]) for m in manual
               if name_compatible(m["student"], r["given"], r["family"])]
        e = evaluate(r, dict(p, manual=man), common)
        props.append(dict(individual_id=ind, aha_id=rid, matched_name=matched, person_id=_representative(p["nodes"]),
                          decision=None, **e))
    node_ind = {n: i for i, p in persons.items() for n in p["nodes"]}
    linked = {}
    for d in decisions:
        ind = node_ind.get(d["person_id"])
        if d["decision"] == "link" and ind:
            linked[d["aha_id"]] = (ind, d)
    rejected = {(d["aha_id"], node_ind.get(d["person_id"])): d for d in decisions if d["decision"] == "reject"}
    for p in props:
        if (p["aha_id"], p["individual_id"]) in rejected:
            p.update(supported=False, strong=False, decision="rejected: " + rejected[(p["aha_id"], p["individual_id"])]["source"])
        elif p["aha_id"] in linked and linked[p["aha_id"]][0] != p["individual_id"]:
            p.update(supported=False, strong=False, decision="record linked to another person by decision")
    assign_tiers(props)
    for p in props:
        if p["aha_id"] in linked and linked[p["aha_id"]][0] == p["individual_id"]:
            d = linked[p["aha_id"]][1]
            p.update(status="accepted", decision=f"{d['source']}, {d['date']}: {d['note']}")
    return props


def write(db, recs_all_path, props, source_sha):
    q = db.execute
    allrecs = read_aha(recs_all_path)
    q("""CREATE TABLE aha_dissertations (aha_id VARCHAR PRIMARY KEY, dissertator VARCHAR, department VARCHAR,
         orgcd VARCHAR, title VARCHAR, year INT, advisors VARCHAR[], advisor_ids VARCHAR[])""")
    db.executemany("INSERT INTO aha_dissertations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   [(r["id"], r["dissertator"], r["department"], r["orgcd"], r["title"], r["year"], r["advisors"],
                     r["advisor_ids"]) for r in allrecs])

    def display(d):
        family, _, given = d.partition(",")
        return f"{given.strip()} {family.strip()}".strip()
    db.executemany("""INSERT INTO occurrences VALUES (?, 'aha', ?, NULL, 'dissertator', ?, ?, ?, ?, ?,
                      'AHA Directory of History Dissertations', ?)""",
                   [("aha:dissertation:" + r["id"], "aha:" + r["id"], display(r["dissertator"]),
                     r["dissertator"].partition(",")[2].strip(), r["dissertator"].partition(",")[0].strip(),
                     r["department"], str(r["year"]) if r["year"] else None, source_sha) for r in allrecs])
    q("""CREATE TABLE aha_candidates (individual_id VARCHAR, aha_id VARCHAR, person_id VARCHAR, matched_name VARCHAR,
         gate VARCHAR, channels VARCHAR[], shared_words INT, first_work INT, competitors INT, status VARCHAR,
         decision VARCHAR, evidence VARCHAR)""")
    db.executemany("INSERT INTO aha_candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   [(p["individual_id"], p["aha_id"], p["person_id"], p["matched_name"], p["gate"], p["channels"],
                     p["shared"], p["first_work"], p["competitors"], p["status"], p["decision"], p["evidence"])
                    for p in props])
    q("""INSERT INTO route_links SELECT 'aha:dissertation:' || aha_id, person_id, status,
         CASE WHEN status = 'accepted' THEN 'aha_identity_decision' ELSE 'aha_dissertation' END,
         array_to_string(channels, '+') || ' | ' || evidence FROM aha_candidates WHERE status IS NOT NULL""")
    q("""INSERT INTO identity_links SELECT 'aha:dissertation:' || aha_id, person_id, status,
         CASE WHEN status = 'accepted' THEN 'aha_identity_decision' ELSE 'aha_dissertation' END,
         CASE WHEN status = 'accepted' THEN decision
              ELSE 'Route: AHA dissertation, name-gated, evidence channels ' || array_to_string(channels, '+') END,
         evidence, NULL, NULL FROM aha_candidates WHERE status IS NOT NULL""")
