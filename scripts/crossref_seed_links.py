#!/usr/bin/env python3
"""Seed test (run on spark): look for Crossref works plausibly by thesis-author seeds.

Seeds: DNB thesis authors (data/identifiers/thesis-round-2026-11-16/seeds.csv.gz) and the Mexico-ingest
thesis authors proposed as mints (03-author-mints-mexico.json), joined to dissertations.csv for title,
year and university -> seeds-all.csv (built locally, copied here).

Scope: works in the Crossref history slice (/mnt/data/jic823/crossref-history-slice) plus every Crossref
record of type book / monograph / edited-book / reference-book / book-chapter. Contributor roles author
and editor.

Candidate = folded family name equal (umlaut/ss/accents folded, particles stripped, hyphens as spaces;
Mexican seeds also on the first surname alone, then the given name must match in full), given name
compatible (every full Crossref given token is one of the seed's given tokens; initials agree; never
nicknames), work year in thesis year -3 .. +30.

Evidence (per candidate work):
  title_strong      thesis title and work title(+subtitle) share >=2 rare words and >=60% of the smaller
                    side's idf mass (and idf sum >= 14)                              -> strong
  affil_thesis_univ Crossref affiliation names the thesis university, year thesis-3..+6, full given name led by
                    the seed's first given name, full family, a work in the history slice, at most one ORCID
                    among same-name Crossref authors                                 -> strong
  orcid_of_linked   same ORCID as a work linked strong by the two rules above         -> strong
  affil_weak        thesis university in affiliation but not all of the affil_thesis_univ conditions  -> weak
  topic             shares rare title words with the thesis (idf sum >= 8) but below title_strong -> weak
  name_only         nothing else                                                      -> not linked
An initial-only given name can be linked only by title_strong or orcid_of_linked.

Output: seed-candidates.parquet / .csv.gz, seed-summary.csv, base-rate.csv, stats.json in --out.
"""
import argparse, collections, csv, gzip, json, math, os, re, time, unicodedata

import duckdb

P = "/mnt/data/jic823/crossref-2026-parquet"
SL = "/mnt/data/jic823/crossref-history-slice"
BOOK = "('book','monograph','edited-book','reference-book','book-chapter')"

FOLD_SQL = r"""
create or replace macro fold(x) as trim(regexp_replace(regexp_replace(strip_accents(
   replace(replace(replace(replace(replace(replace(lower(x),'ß','ss'),'ä','ae'),'ö','oe'),'ü','ue'),'-',' '),'‐',' ')),
   '[^a-z ]+',' ','g'),' +',' ','g'));
create or replace macro k2(x) as trim(regexp_replace(
   replace(replace(replace(fold(x),'ae','a'),'oe','o'),'ue','u'),
   '^(von der |von dem |von |van der |van den |van |de la |de los |de las |del |de |zu |vom |zur |da |di |dos |das )','' ));
"""


def fold(x):
    x = (x or "").lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    x = x.replace("-", " ").replace("‐", " ")
    x = "".join(ch for ch in unicodedata.normalize("NFKD", x) if not unicodedata.combining(ch))
    x = re.sub(r"[^a-z ]+", " ", x)
    return re.sub(r" +", " ", x).strip()


def k2tok(t):
    return t.replace("ae", "a").replace("oe", "o").replace("ue", "u")


STOP = set("""a an and are as at be by for from in into is it of on or the to with without about after before
between during under over through toward towards its their his her new study studies history historical
der die das des dem den ein eine einer eines einem und oder in im zum zur von vom mit fur bei als auf aus nach
uber unter zwischen sowie gegen ohne seit bis durch zu am an ist sind wie was beispiel geschichte
el la los las lo un una unos unas y e o u de del al en con por para sobre entre como su sus que se desde hasta
historia historico historica
le les des du et ou au aux dans par pour sur une est son ses leur leurs
dissertation thesis untersuchung studie studien band teil zeit jahrhundert jahrhunderts century siglo siecle
fuer ueber waehrend gegenueber zwischen beitrag beitraege anhand sowie unter besonderer beruecksichtigung
mexico mexicano mexicana siglos xix xvi xvii xviii xx
""".split())


def tokens(t):
    return [w for w in fold(t).split() if len(w) >= 3 and w not in STOP]


def given_compat(seed_given, cr_given):
    """Return 'full', 'initial' or None. Folded strings."""
    G = [k2tok(t) for t in fold(seed_given).split()]
    C = [k2tok(t) for t in fold(cr_given).split()]
    if not G or not C:
        return None
    Ginit = {g[0] for g in G}
    full = False
    for c in C:
        if len(c) == 1:
            if c not in Ginit:
                return None
        else:
            if c not in G:
                return None
            full = True
    # the first Crossref token must be the seed's first given name or another of its given names (full);
    # an initial-only first token must be the first given initial
    if len(C[0]) == 1 and C[0] != G[0][0]:
        return None
    return "full" if full else "initial"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--inst", required=True, help="institution code -> affiliation regex (csv)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default="/mnt/data/jic823/tools/crossref-extract/seedtest/work.duckdb")
    ap.add_argument("--reuse", action="store_true", help="reuse author pull tables in --work")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    c = duckdb.connect(a.work)
    c.sql("set threads=12; set memory_limit='48GB'; set preserve_insertion_order=false")
    c.sql(f"set temp_directory='{os.path.dirname(a.work)}/_tmp'")
    c.sql(FOLD_SQL)
    seeds = list(csv.DictReader(open(a.seeds)))
    for s in seeds:
        fam, _, giv = s["name"].partition(",")
        s["family"], s["given"] = fam.strip(), giv.strip()
        s["year"] = int(s["year"]) if s["year"] else None
    c.sql("create or replace table seeds_raw (seed_set varchar, seed_id varchar, family varchar, given varchar)")
    c.executemany("insert into seeds_raw values (?,?,?,?)",
                  [(s["seed_set"], s["seed_id"], s["family"], s["given"]) for s in seeds])
    # keys: full family; for MX two-or-more-word families also the first surname
    c.sql("""create or replace table skeys as
       select seed_id, k2(family) fk, 'full_family' variant from seeds_raw
       union select seed_id, k2(split_part(fold(family),' ',1)), 'first_surname' from seeds_raw
         where seed_set='MX' and length(fold(family)) - length(replace(fold(family),' ','')) >= 1""")
    c.execute("""create or replace table sinit as
       select seed_id, list_distinct(list_transform(string_split(fold(given),' '), lambda x: left(x,1))) inits from seeds_raw""")
    have = {r[0] for r in c.execute("select table_name from duckdb_tables()").fetchall()}
    if "am" not in have:
        c.sql(f"""create or replace table am as
          select a.doi, a.role, a.seq, a.given, a.family, a.orcid, a.affiliation, k2(a.family) fk, fold(a.given) fg
          from '{P}/authors/*.parquet' a
          where a.family is not null and a.given is not null and a.role in ('author','editor')
            and k2(a.family) in (select fk from skeys)""")
        print("author pull", c.execute("select count(*) from am").fetchall()[0], round(time.time() - t0), flush=True)
    # prefilter: the Crossref given name starts with an initial of one of the seed's given names
    c.sql("""create or replace table amc as
      select am.doi, k.seed_id, k.variant, am.role, am.given, am.family, am.orcid, am.affiliation
      from am join skeys k on k.fk=am.fk join sinit i on i.seed_id=k.seed_id
      where list_contains(i.inits, left(am.fg,1))""")
    print("prefiltered", c.execute("select count(*) from amc").fetchall()[0], round(time.time() - t0), flush=True)
    if not a.reuse:
        c.sql(f"""create or replace table aw as
          select w.doi, w.type, w.title, w.subtitle, w.container, w.issn, w.isbn, w.publisher, w.year, w.page, w.review_of,
                 (s.doi is not null) in_slice
          from '{P}/works/*.parquet' w left join (select doi from '{SL}/works/*.parquet') s using (doi)
          where w.doi in (select doi from amc)""")
        print("works pull", c.execute("select count(*) from aw").fetchall()[0], round(time.time() - t0), flush=True)
    if not a.reuse:
        # document frequency of title words over the slice + all books/chapters (folded tokens)
        c.sql(f"""create or replace table df as
          with t as (select doi, title, subtitle from '{SL}/works/*.parquet'
                     union select doi, title, subtitle from '{P}/works/*.parquet' where type in {BOOK})
          select tok, count(distinct doi) n from (
            select doi, unnest(string_split(fold(coalesce(title,'')||' '||coalesce(subtitle,'')),' ')) tok from t)
          where length(tok)>=3 group by tok""")
        c.sql(f"""create or replace table dfn as
          select count(*) n from (select doi from '{SL}/works/*.parquet' union select doi from '{P}/works/*.parquet' where type in {BOOK})""")
        print("df", c.execute("select count(*) from df").fetchall()[0], round(time.time() - t0), flush=True)

    N = c.execute("select n from dfn").fetchall()[0][0]
    # idf only for tokens we need
    need = set()
    for s in seeds:
        need.update(tokens(s["title"]))
    wt = c.sql("select doi, coalesce(title,'')||' '||coalesce(subtitle,'') t from aw").fetchall()
    wtok = {}
    for d, t in wt:
        tt = tokens(t)
        wtok[d] = tt
        need.update(tt)
    c.sql("create or replace temp table need (tok varchar)")
    c.executemany("insert into need values (?)", [(x,) for x in need])
    dfm = dict(c.sql("select tok, n from df where tok in (select tok from need)").fetchall())

    def idf(tk):
        return math.log(N / (dfm.get(tk, 0) + 1))

    RARE = math.log(N / 2000.0)   # fewer than ~2,000 titles in the scope carry the word

    def overlap(ta, tb):
        """shared rare title words; a 7-letter prefix match (Wuppertaler / Wuppertal) counts with the idf of the
        commoner of the two words, so a cross-language stem (Universitaeten / universities) adds almost nothing"""
        A, B = set(ta), set(tb)
        if not A or not B:
            return 0, 0.0, 0.0, []
        sh = {x: idf(x) for x in A & B}
        for x in A - set(sh):
            if len(x) >= 7:
                for y in B - set(sh):
                    if len(y) >= 7 and x[:7] == y[:7]:
                        sh[x] = min(idf(x), idf(y))
                        break
        ssum = sum(sh.values())
        ma = sum(idf(x) for x in A)
        mb = sum(idf(x) for x in B)
        nrare = sum(1 for v in sh.values() if v >= RARE)
        return nrare, ssum, ssum / max(1e-9, min(ma, mb)), sorted(sh)

    # institution regexes
    inst = {}
    for r in csv.DictReader(open(a.inst)):
        inst[r["code"]] = re.compile(r["regex"], re.I)

    # seed lookup by key
    sk = collections.defaultdict(list)
    for sid, fk, var in c.sql("select seed_id, fk, variant from skeys").fetchall():
        sk[fk].append((sid, var))
    S = {s["seed_id"]: s for s in seeds}
    works = {r[0]: r for r in c.sql("select * from aw").fetchall()}
    wcols = [d[0] for d in c.execute("select * from aw limit 0").description]
    W = {d: dict(zip(wcols, r)) for d, r in works.items()}

    # base rate: same-name (full given) author rows and distinct ORCIDs across all of Crossref
    base = collections.defaultdict(lambda: {"rows": 0, "rows_in_scope": 0, "orcids": set(), "works_window": 0})
    cand = []
    for doi, sid, var, role, given, family, orcid, aff in c.execute("select * from amc").fetchall():
        if True:
            s = S[sid]
            lvl = given_compat(s["given"], given)
            if not lvl:
                continue
            if var == "first_surname" and lvl != "full":
                continue
            # Crossref family is the full double surname, or only the first one (variant)
            if var == "first_surname" and len(fold(family).split()) > 1:
                continue
            w = W.get(doi)
            if w is None:
                continue
            b = base[sid]
            if lvl == "full":
                b["rows"] += 1
                if orcid:
                    b["orcids"].add(orcid)
            in_scope = bool(w["in_slice"]) or w["type"] in ("book", "monograph", "edited-book", "reference-book", "book-chapter")
            if not in_scope:
                continue
            if lvl == "full":
                b["rows_in_scope"] += 1
            y = w["year"]
            if s["year"] is None or y is None or not (s["year"] - 3 <= y <= s["year"] + 30):
                continue
            if lvl == "full":
                b["works_window"] += 1
            nrare, ssum, frac, sh = overlap(tokens(s["title"]), wtok.get(doi, []))
            rx = inst.get(s["institution"])
            aff_hit = bool(aff and rx and rx.search(fold(aff)))
            cand.append(dict(seed_set=s["seed_set"], seed_id=sid, seed_name=s["name"], seed_gnd=s.get("gnd", ""), seed_given=s["given"],
                             thesis_title=s["title"], thesis_year=s["year"], thesis_univ=s["institution"],
                             doi=doi, role=role, cr_family=family, cr_given=given, name_match=lvl, name_variant=var,
                             orcid=orcid or "", affiliation=aff or "", work_title=w["title"] or "",
                             work_subtitle=w["subtitle"] or "", container=w["container"] or "", year=y,
                             type=w["type"], in_slice=bool(w["in_slice"]), page=w["page"] or "",
                             publisher=w["publisher"] or "",
                             t_rare=nrare, t_idf=round(ssum, 1), t_frac=round(frac, 2), t_shared=" ".join(sh),
                             aff_hit=aff_hit))
    print("candidates", len(cand), round(time.time() - t0), flush=True)

    # evidence
    for r in cand:
        ev = []
        strong_title = r["t_rare"] >= 2 and r["t_frac"] >= 0.6 and r["t_idf"] >= 14
        if strong_title:
            ev.append("title_strong")
        if r["aff_hit"]:
            # strong only when: full name with the seed's first given name first, full family (not the first surname
            # alone), a history venue (the slice's journals) or a slice book, at most one ORCID among same-name
            # authors in Crossref, and the year in thesis -3..+6 (hand check 2026-11-17: Thomas Schmidt astrophysics,
            # Christian Richter media studies, Marco A. Perez mathematics at the thesis university were namesakes)
            b = base.get(r["seed_id"], {})
            first = fold(r["seed_given"]).split()[:1]
            crfirst = fold(r["cr_given"]).split()[:1]
            ok = (r["name_match"] == "full" and r["name_variant"] == "full_family" and crfirst
                  and first and k2tok(crfirst[0]) == k2tok(first[0]) and r["in_slice"]
                  and len(b.get("orcids", ())) <= 1
                  and r["thesis_year"] - 3 <= r["year"] <= r["thesis_year"] + 6)
            ev.append("affil_thesis_univ" if ok else "affil_weak")
        if not strong_title and r["t_idf"] >= 8 and r["t_rare"] >= 1:
            ev.append("topic")
        r["evidence"] = ev
    # ORCID propagation from strong links
    lo = collections.defaultdict(set)
    for r in cand:
        if r["orcid"] and set(r["evidence"]) & {"title_strong", "affil_thesis_univ"}:
            lo[r["seed_id"]].add(r["orcid"])
    for r in cand:
        if r["orcid"] and r["orcid"] in lo[r["seed_id"]] and not set(r["evidence"]) & {"title_strong", "affil_thesis_univ"}:
            r["evidence"].append("orcid_of_linked")
    for r in cand:
        e = set(r["evidence"])
        if e & {"title_strong", "affil_thesis_univ", "orcid_of_linked"}:
            r["link_class"] = "strong"
        elif e & {"affil_weak", "topic"}:
            r["link_class"] = "weak"
        else:
            r["link_class"] = "name_only"
        det = []
        if r["t_shared"]:
            det.append(f"shared title words: {r['t_shared']} (rare {r['t_rare']}, idf {r['t_idf']}, frac {r['t_frac']})")
        if r["aff_hit"]:
            det.append(f"affiliation: {r['affiliation'][:120]}")
        if "orcid_of_linked" in e:
            det.append(f"ORCID {r['orcid']} also on a strong-linked work")
        r["evidence_class"] = "+".join(r["evidence"]) or "name_only"
        r["evidence_detail"] = "; ".join(det)

    # outputs
    cols = ["seed_set", "seed_id", "seed_name", "seed_gnd", "thesis_title", "thesis_year", "thesis_univ", "doi", "role",
            "cr_family", "cr_given", "name_match", "name_variant", "orcid", "work_title", "work_subtitle", "container",
            "year", "type", "in_slice", "page", "publisher", "link_class", "evidence_class", "evidence_detail"]
    rank = {"strong": 0, "weak": 1, "name_only": 2}
    cand.sort(key=lambda r: (r["seed_set"], r["seed_id"], rank[r["link_class"]], r["year"] or 0, r["doi"]))
    with gzip.open(os.path.join(a.out, "seed-candidates.csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(cand)
    per = collections.defaultdict(list)
    for r in cand:
        per[r["seed_id"]].append(r)
    summ = []
    for s in seeds:
        rs = per.get(s["seed_id"], [])
        cls = [r["link_class"] for r in rs]
        b = base.get(s["seed_id"], {"rows": 0, "rows_in_scope": 0, "orcids": set(), "works_window": 0})
        status = ("linked_strong" if "strong" in cls else "linked_weak" if "weak" in cls
                  else "name_only" if cls else "nothing")
        summ.append(dict(seed_set=s["seed_set"], seed_id=s["seed_id"], seed_name=s["name"], thesis_year=s["year"],
                         thesis_univ=s["institution"], thesis_title=s["title"], status=status,
                         n_strong=cls.count("strong"), n_weak=cls.count("weak"), n_name_only=cls.count("name_only"),
                         strong_evidence=" | ".join(sorted({r["evidence_class"] for r in rs if r["link_class"] == "strong"})),
                         same_name_rows_all_crossref=b["rows"], same_name_rows_in_scope=b["rows_in_scope"],
                         same_name_distinct_orcids=len(b["orcids"]), same_name_works_in_window=b["works_window"]))
    with open(os.path.join(a.out, "seed-summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0]))
        w.writeheader()
        w.writerows(summ)
    st = {}
    for ss in ("DNB", "MX"):
        sm = [x for x in summ if x["seed_set"] == ss]
        cs = [r for r in cand if r["seed_set"] == ss]
        st[ss] = dict(seeds=len(sm), status=dict(collections.Counter(x["status"] for x in sm)),
                      candidate_rows=len(cs), rows_by_class=dict(collections.Counter(r["link_class"] for r in cs)),
                      rows_by_evidence=dict(collections.Counter(r["evidence_class"] for r in cs)),
                      seeds_by_strong_evidence=dict(collections.Counter(
                          ev for x in sm for ev in set(x["strong_evidence"].replace("+", " | ").split(" | ")) if ev)),
                      base_rate=dict(
                          seeds_with_2plus_orcids_same_name=sum(1 for x in sm if x["same_name_distinct_orcids"] >= 2),
                          seeds_with_10plus_same_name_rows=sum(1 for x in sm if x["same_name_rows_all_crossref"] >= 10),
                          seeds_with_100plus_same_name_rows=sum(1 for x in sm if x["same_name_rows_all_crossref"] >= 100),
                          seeds_with_5plus_in_window_in_scope=sum(1 for x in sm if x["same_name_works_in_window"] >= 5)))
    st["N_title_docs"] = N
    json.dump(st, open(os.path.join(a.out, "stats.json"), "w"), indent=1)
    print(json.dumps(st, indent=1), round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
