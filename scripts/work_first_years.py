"""First-publication years for works keyed by a reprint, and the canonical direction of edition clusters
(ARCHITECTURE.md section 8, class 17; 2026-11-11). Derived tables only: `year` is never overwritten.

A work key takes the year of the record it was minted from, which can be a reprint (The Great Plains keyed 2022, Il
principe 1891), so a thesis can 'cite' a work dated after it and age analyses read reprints as new books. This script
collects the evidence of an earlier first publication for every graph work and proposes `first_year`:

- edition-cluster: the earliest year among the work, its EDITION_OF original and the original's other editions;
- lc-edition-group / lc-cluster: the earliest record year of its LC edition group or LC translation cluster
  (data/identifiers/cited-works-translations-2026-11-11; collective uniform titles - Works, Selections - are left out);
- lc-record: the work's own LC records: 008 date1, the original's date in 008 date2 when 008/06 = 'r' (reprint), and
  years in 'Originally published ...' / 'Reprint of ...' notes (500) and 534 (from scripts/lc_bib_notes.py);
- thesis-printed: the earliest year that at least two citing theses print for it (corpus works mapped to the work);
- bounds: the key-log author's birth year (+10) rejects impossible candidates; the author's death year is an upper
  bound for first publication of non-posthumous works and is only flagged (`after_author_death`).

Outputs:
- data/graph/work-years.csv.gz: key, year, first_year, first_year_catalogue (without thesis-printed), basis, sources,
  flags. One row per work with evidence of an earlier first publication (or a death-year flag).
- data/graph/edition-canonical-fixes.csv.gz: edition clusters whose canonical node is a translation while the
  original-language record is known (LC cluster original, or a graph work by the same author with the 240 uniform
  title): cluster, current canonical, proposed canonical, basis, theses citing the current canonical, theses citing it
  in the original language.
- data/identifiers/work-years-2026-11-11/: anachronism report (pairs before/after, by cause), wrong-match candidates,
  audit sample (local), report.json.

Inputs besides build/graph: the canon-paper base (corpus citations, works and their graph keys: cit, cw, diss, cmap;
built by data/field-research/canon-paper-2026-11-11/00_base.py; path in WY_PAPER_BASE), the LC index and the notes
extract (WY_NOTES). Never reads graph.json / graph.graphml / entries.jsonl.

    python3 scripts/work_first_years.py prepare | years | canonical | anachronisms | sample
"""
import argparse
import json
import os
import re
import unicodedata
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
G = Path(os.environ.get('WY_GRAPH', ROOT / 'build/graph'))
SCR = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad')
SCRATCH = Path(os.environ.get('WY_SCRATCH', SCR / 'editions2'))
PAPER = Path(os.environ.get('WY_PAPER_BASE', SCR / 'paper2/base.duckdb'))
NOTES = Path(os.environ.get('WY_NOTES', SCRATCH / 'lc-notes'))
LC = Path('/mnt/e/lc-bib-2016/index')
TR = ROOT / 'data/identifiers/cited-works-translations-2026-11-11'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
YEARS = ROOT / 'data/graph/work-years.csv.gz'
FIXES = ROOT / 'data/graph/edition-canonical-fixes.csv.gz'
OUT = ROOT / 'data/identifiers/work-years-2026-11-11'
DB = SCRATCH / 'years.duckdb'


def con(read_only=False):
    (SCRATCH / 'tmp').mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(DB), read_only=read_only)
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH / 'tmp'}'; "
              "SET preserve_insertion_order=false; SET max_temp_directory_size='8GB'")
    c.create_function('tfold', tfold, ['VARCHAR'], 'VARCHAR', null_handling='special')
    c.create_function('tjac', tjac, ['VARCHAR', 'VARCHAR'], 'DOUBLE', null_handling='special')
    c.create_function('lang_guess', lang_guess, ['VARCHAR'], 'VARCHAR', null_handling='special')
    return c


def tfold(t):
    if t is None:
        return None
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    t = re.split(r'\s[:;/=]\s|\s:\s?|:\s|\.\s', t)[0]
    w = re.sub(r"['’]", '', t)
    w = re.sub(r'[^a-z0-9 ]+', ' ', w).split()
    while w and w[0] in {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une', 'o', 'os', 'as'}:
        w = w[1:]
    return ' '.join(w[:8])


def tjac(a, b):
    """Overlap of the folded main titles' word sets (shared words / the smaller set): 'Ganhou, leva!' against the
    printed 'Ganhou, leva! O jogo do bicho ...' is 1."""
    x, y = set((tfold(a) or '').split()), set((tfold(b) or '').split())
    return len(x & y) / min(len(x), len(y)) if x and y else 0.0


STOP = {'en': {'the', 'of', 'and', 'in', 'a', 'to', 'for', 'on', 'from', 'with', 'history', 'its'},
        'fr': {'le', 'la', 'les', 'des', 'du', 'de', 'et', 'en', 'au', 'aux', 'une', 'un', 'histoire', 'dans', 'sur'},
        'pt': {'o', 'a', 'os', 'as', 'do', 'da', 'dos', 'das', 'e', 'em', 'no', 'na', 'uma', 'um', 'historia', 'para', 'sobre'},
        'es': {'el', 'la', 'los', 'las', 'del', 'de', 'y', 'en', 'una', 'un', 'historia', 'para', 'sobre'},
        'de': {'der', 'die', 'das', 'und', 'des', 'im', 'in', 'zur', 'zum', 'ein', 'eine', 'geschichte', 'von', 'uber'},
        'it': {'il', 'lo', 'la', 'i', 'gli', 'le', 'del', 'della', 'dei', 'e', 'di', 'in', 'storia', 'una', 'un'}}


def lang_guess(t):
    """A rough title language from stop words (None when unclear)."""
    w = re.sub(r'[^a-z ]+', ' ', unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()).split()
    if len(w) < 3:
        return None
    sc = sorted(((sum(x in v for x in w), k) for k, v in STOP.items()), reverse=True)
    return sc[0][1] if sc[0][0] >= 1 and sc[0][0] > sc[1][0] else None


def prepare(args):
    c = con()
    c.execute(f"""CREATE OR REPLACE TABLE gw AS SELECT key, label, kind, year, resolution, kind_proposed, anchors
                  FROM '{G}/work.parquet'""")
    c.execute("""CREATE OR REPLACE TABLE wl AS SELECT DISTINCT key, substr(a, 6) lccn FROM (SELECT key, unnest(anchors) a FROM gw)
                 WHERE a LIKE 'lccn:%' UNION SELECT key, substr(key, 6) FROM gw WHERE key LIKE 'lccn:%'""")
    c.execute(f"""CREATE OR REPLACE TABLE lrec AS SELECT trim(control) control, lccn, date1, lang FROM '{LC}/records-*.parquet'
                  WHERE trim(control) IN (SELECT lccn FROM wl) OR lccn IN (SELECT lccn FROM wl)""")
    c.execute("""CREATE OR REPLACE TABLE wrec AS SELECT wl.key, r.control FROM wl JOIN lrec r ON r.control = wl.lccn
                 UNION SELECT wl.key, r.control FROM wl JOIN lrec r ON r.lccn = wl.lccn""")
    c.execute(f"""CREATE OR REPLACE TABLE notes AS SELECT trim(control) control, date_type, date1, date2, lang, lang_orig,
                  translation, uniform, orig_note FROM '{NOTES}/notes-*.parquet' WHERE trim(control) IN (SELECT control FROM lrec)""")
    c.execute(f"CREATE OR REPLACE TABLE eo AS SELECT * FROM '{G}/edition_of.parquet'")
    c.execute(f"CREATE OR REPLACE TABLE rv AS SELECT DISTINCT \"from\" AS key FROM '{G}/reviews.parquet'")
    c.execute(f"""CREATE OR REPLACE TABLE au AS SELECT "from" AS person, "to" AS work, evidence FROM '{G}/authored.parquet'""")
    c.execute(f"CREATE OR REPLACE TABLE life AS SELECT * FROM read_csv('{LIFE}', all_varchar=true)")
    c.execute(f"CREATE OR REPLACE TABLE eg AS SELECT * FROM read_csv('{TR}/lc-edition-groups.csv.gz', all_varchar=true)")
    c.execute(f"CREATE OR REPLACE TABLE lcl AS SELECT * FROM read_csv('{TR}/lc-clusters.csv.gz', all_varchar=true)")
    c.execute(f"ATTACH '{PAPER}' AS p (READ_ONLY)")
    for t in ('cit', 'cw', 'diss', 'cmap'):
        c.execute(f'CREATE OR REPLACE TABLE {t} AS SELECT * FROM p.{t}')
    c.execute('DETACH p')
    for t in ('gw', 'wrec', 'notes', 'eo', 'cit', 'cw', 'cmap'):
        print(t, c.execute(f'SELECT count(*) FROM {t}').fetchone()[0], flush=True)


def years(args):
    c = con()
    yr = "TRY_CAST(substr({0}, 1, 4) AS INT)"
    valid = lambda e: f"({e} BETWEEN 1400 AND 2026)"
    # candidates (key, year, source)
    c.execute(f"""CREATE OR REPLACE TABLE cand AS
        -- edition cluster: original + all its editions
        WITH comp AS (SELECT "to" root, "from" member FROM eo UNION SELECT DISTINCT "to", "to" FROM eo),
             cy AS (SELECT root, min(g.year) y FROM comp JOIN gw g ON g.key = comp.member WHERE {valid('g.year')} GROUP BY 1)
        SELECT comp.member AS key, cy.y AS year, 'edition-cluster' AS source FROM comp JOIN cy USING (root)
        UNION ALL
        -- LC edition groups (same main entry and full title held by several nodes)
        SELECT g.k, m.y, 'lc-edition-group' FROM (
            SELECT heading_key, title_key, min({yr.format('year')}) y FROM eg GROUP BY 1, 2) m
            JOIN (SELECT heading_key, title_key, graph_node AS k FROM eg UNION SELECT heading_key, title_key, group_canonical FROM eg) g
            USING (heading_key, title_key) WHERE {valid('m.y')}
        UNION ALL
        -- LC translation clusters (original / translation / later edition; not collective uniform titles)
        SELECT g.k, m.y, 'lc-cluster' FROM (
            SELECT cluster_id, min({yr.format('year')}) y FROM lcl WHERE role <> 'compilation' GROUP BY 1) m
            JOIN (SELECT cluster_id, graph_node AS k FROM lcl WHERE role <> 'compilation' AND graph_node IS NOT NULL
                  UNION SELECT cluster_id, cluster_canonical AS k FROM lcl WHERE role <> 'compilation' AND cluster_canonical LIKE 'w-%') g
            USING (cluster_id) WHERE {valid('m.y')}
        UNION ALL
        -- the work's own LC records: 008 date1
        SELECT w.key, {yr.format('r.date1')}, 'lc-record' FROM wrec w JOIN lrec r USING (control) WHERE {valid(yr.format('r.date1'))}
        UNION ALL
        -- 008/06 = r: date2 is the original's date
        SELECT w.key, {yr.format('n.date2')}, 'lc-reprint-008' FROM wrec w JOIN notes n USING (control)
            WHERE n.date_type = 'r' AND {valid(yr.format('n.date2'))}
        UNION ALL
        -- 'Originally published ...', 'Reprint of the ... ed.', 534: years in the note earlier than the record's own
        SELECT key, y, 'lc-note' FROM (SELECT w.key, TRY_CAST(regexp_extract(n.orig_note,
                    '(?i)(originally published|first published|first issued|originally issued|first printed|reprint of|reprinted from|publi[ée] (?:pour la premi[eè]re fois|originalement)|534:)[^|]{{0,120}}?\\b(1[4-9][0-9][0-9]|20[01][0-9])\\b', 2) AS INT) y,
                    {yr.format('n.date1')} d1 FROM wrec w JOIN notes n USING (control)
                    WHERE n.orig_note <> '' AND NOT regexp_matches(n.orig_note, '(?i)presented as|thesis|dissertation|th[eè]se|tese'))
            WHERE y < coalesce(d1, 9999)
        UNION ALL
        -- years printed by citing theses: at least two theses (a typo by one thesis does not count)
        SELECT k, y, 'thesis-printed' FROM (
            SELECT m.gkey k, cw.year y, count(DISTINCT cit.did) n FROM cmap m JOIN cw USING (work_id) JOIN cit USING (work_id)
            WHERE m.gkey IS NOT NULL AND {valid('cw.year')} GROUP BY 1, 2
            UNION ALL
            SELECT m.gkey_cited, cw.year, count(DISTINCT cit.did) FROM cmap m JOIN cw USING (work_id) JOIN cit USING (work_id)
            WHERE m.gkey_cited IS NOT NULL AND m.gkey_cited <> coalesce(m.gkey, '') AND {valid('cw.year')} GROUP BY 1, 2)
            WHERE n >= 2""")
    print(c.execute('SELECT source, count(*), count(DISTINCT key) FROM cand GROUP BY 1').fetchall(), flush=True)
    # author bounds: key-log authors' life years (the earliest birth and the latest death among the work's authors)
    c.execute("""CREATE OR REPLACE TABLE wlife AS SELECT a.work AS key, min(TRY_CAST(l.birth AS INT)) birth,
                 max(TRY_CAST(l.death AS INT)) death, bool_and(l.death IS NOT NULL AND l.death <> '') all_dead
                 FROM au a JOIN life l ON l.key = a.person WHERE a.evidence = 'keylog' GROUP BY 1""")
    c.execute("""CREATE OR REPLACE TABLE wy AS
        WITH c2 AS (SELECT c.key, c.year, c.source FROM cand c JOIN gw g ON g.key = c.key LEFT JOIN wlife l ON l.key = c.key
                    WHERE c.year < g.year AND (l.birth IS NULL OR c.year >= l.birth + 10)),
             agg AS (SELECT key, min(year) fy, min(year) FILTER (WHERE source <> 'thesis-printed') fyc,
                     string_agg(DISTINCT source || ':' || year, ';' ORDER BY source || ':' || year) sources FROM c2 GROUP BY 1)
        SELECT g.key, g.year, a.fy first_year, a.fyc first_year_catalogue,
               (SELECT string_agg(DISTINCT c2.source, ';' ORDER BY c2.source) FROM c2 WHERE c2.key = g.key AND c2.year = a.fy) basis, a.sources,
               concat_ws(';',
                 CASE WHEN l.all_dead AND a.fy > l.death + 1 THEN 'first-year-after-author-death' END,
                 CASE WHEN l.all_dead AND g.year > l.death + 1 AND a.fy IS NULL THEN 'key-year-after-author-death' END,
                 CASE WHEN a.fyc IS NULL AND a.fy IS NOT NULL THEN 'thesis-printed-only' END) flags
        FROM gw g LEFT JOIN agg a USING (key) LEFT JOIN wlife l USING (key)
        WHERE a.fy IS NOT NULL OR (l.all_dead AND g.year > l.death + 1)""")
    c.execute(f"COPY (SELECT * FROM wy ORDER BY key) TO '{YEARS}' (HEADER, COMPRESSION gzip)")
    r = c.execute("""SELECT count(*), count(first_year), count(first_year_catalogue),
        count(*) FILTER (WHERE flags LIKE '%thesis-printed-only%'), count(*) FILTER (WHERE flags LIKE '%first-year-after-author-death%'),
        count(*) FILTER (WHERE flags LIKE '%key-year-after-author-death%'), median(year - first_year) FROM wy""").fetchone()
    print(dict(rows=r[0], first_year=r[1], first_year_catalogue=r[2], thesis_printed_only=r[3],
               first_year_after_author_death=r[4], key_year_after_author_death_no_evidence=r[5], median_gap=r[6]))
    by = c.execute("SELECT basis, count(*) FROM wy WHERE first_year IS NOT NULL GROUP BY 1 ORDER BY 2 DESC").fetchall()
    OUT.mkdir(parents=True, exist_ok=True)
    rep = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    rep['work_years'] = dict(rows=r[0], first_year=r[1], first_year_catalogue=r[2], thesis_printed_only=r[3],
                             first_year_after_author_death=r[4], key_year_after_author_death_no_evidence=r[5],
                             median_gap_years=r[6], by_basis=dict(by))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, default=str) + '\n')


def canonical(args):
    """Clusters whose canonical work is a translation while the original-language record is known."""
    c = con()
    # canonical candidates: thesis-cited works and EDITION_OF targets; their LC records' translation evidence
    c.execute("""CREATE OR REPLACE TABLE cited AS SELECT gkey AS key, count(DISTINCT did) theses FROM cmap JOIN cit USING (work_id)
                 WHERE gkey IS NOT NULL GROUP BY 1""")
    c.execute("""CREATE OR REPLACE TABLE trec AS SELECT w.key, n.control, n.uniform, n.lang, n.lang_orig, n.translation,
                 TRY_CAST(substr(n.date1, 1, 4) AS INT) d1 FROM wrec w JOIN notes n USING (control)
                 WHERE w.key IN (SELECT key FROM cited) AND (n.lang_orig <> '' OR n.translation OR n.uniform <> '')""")
    # (i) LC cluster: the current canonical holds a translation record and the cluster holds an original-language record
    c.execute("""CREATE OR REPLACE TABLE fix1 AS
        SELECT DISTINCT t.cluster_id AS cluster, w.key current_canonical,
               coalesce(o.graph_node, 'lccn:' || o.lccn) proposed_canonical, 'lc-cluster-original:' || o.lccn basis,
               o.lang orig_lang, TRY_CAST(o.year AS INT) orig_year
        FROM lcl t JOIN wl w ON w.lccn = t.lccn JOIN cited ci ON ci.key = w.key
        JOIN lcl o ON o.cluster_id = t.cluster_id AND o.role = 'original' AND o.lang = coalesce(o.original_lang, o.lang)
        WHERE t.role = 'translation' AND coalesce(o.graph_node, '') <> w.key
          AND NOT EXISTS (SELECT 1 FROM wl w2 WHERE w2.key = w.key AND w2.lccn = o.lccn)
          AND NOT EXISTS (SELECT 1 FROM wl w3 JOIN lcl o2 ON o2.lccn = w3.lccn WHERE w3.key = w.key AND o2.role = 'original')""")
    # (ii) no LC original: a graph work by the same key-log author whose title is the 240 uniform title, earlier
    c.execute("""CREATE OR REPLACE TABLE fix2 AS
        WITH u AS (SELECT DISTINCT key, tfold(regexp_replace(uniform, '\\.\\s.*$', '')) ut FROM trec
                   WHERE uniform <> '' AND (lang_orig <> '' OR translation OR regexp_matches(uniform, '\\.\\s+(English|French|German|Spanish|Portuguese|Italian)')))
        SELECT 'uniform:' || u.key AS cluster, u.key current_canonical, o.key proposed_canonical, 'lc-240-uniform-title=graph-work-by-same-author' basis,
               NULL orig_lang, o.year orig_year
        FROM u JOIN au a ON a.work = u.key AND a.evidence = 'keylog' JOIN au b ON b.person = a.person AND b.work <> u.key
        JOIN gw o ON o.key = b.work AND tfold(o.label) = u.ut JOIN gw cur ON cur.key = u.key
        WHERE length(u.ut) >= 8 AND o.kind IN ('book', 'other')
          AND u.key NOT IN (SELECT current_canonical FROM fix1) AND tfold(cur.label) <> u.ut""")
    c.execute("""CREATE OR REPLACE TABLE fixes AS
        SELECT f.*, ci.theses theses_citing_current,
               (SELECT count(DISTINCT cit.did) FROM cmap m JOIN cw USING (work_id) JOIN cit USING (work_id)
                WHERE m.gkey = f.current_canonical AND tfold(cw.title) <> tfold(cur.label)
                  AND (tfold(cw.title) = tfold(pg.label) OR f.orig_lang IS NOT NULL AND tfold(cw.title) = tfold(lo.title))) theses_in_original_language
        FROM (SELECT * FROM fix1 UNION ALL SELECT * FROM fix2) f JOIN cited ci ON ci.key = f.current_canonical
        JOIN gw cur ON cur.key = f.current_canonical LEFT JOIN gw pg ON pg.key = f.proposed_canonical
        LEFT JOIN (SELECT lccn, any_value(title) title FROM lcl GROUP BY 1) lo ON 'lccn:' || lo.lccn = f.proposed_canonical
            OR lo.lccn = split_part(f.basis, ':', 2)""")
    c.execute(f"""COPY (SELECT cluster, current_canonical, proposed_canonical, basis, orig_lang, orig_year, theses_citing_current,
                  theses_in_original_language FROM fixes ORDER BY theses_citing_current DESC) TO '{FIXES}' (HEADER, COMPRESSION gzip)""")
    r = c.execute("""SELECT count(*), count(DISTINCT current_canonical), sum(theses_citing_current), sum(theses_in_original_language),
                     count(*) FILTER (WHERE basis LIKE 'lc-cluster%'), count(*) FILTER (WHERE basis LIKE 'lc-240%') FROM fixes""").fetchone()
    top = c.execute("""SELECT f.current_canonical, cur.label, cur.year, f.proposed_canonical, pg.label, pg.year, f.basis,
                       f.theses_citing_current, f.theses_in_original_language FROM fixes f JOIN gw cur ON cur.key = f.current_canonical
                       LEFT JOIN gw pg ON pg.key = f.proposed_canonical ORDER BY theses_in_original_language DESC, theses_citing_current DESC LIMIT 25""").fetchall()
    for t in top:
        print(t)
    veyne = c.execute("SELECT * FROM fixes WHERE current_canonical = 'w-303604'").fetchall()
    print('veyne', veyne)
    rep = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    rep['canonical_fixes'] = dict(rows=r[0], canonical_works=r[1], theses_citing_current=r[2], theses_in_original_language=r[3],
                                  lc_cluster_basis=r[4], uniform_title_basis=r[5], veyne_w_303604=[list(map(str, v)) for v in veyne])
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, default=str) + '\n')


def anachronisms(args):
    """Thesis-work pairs where the work is dated 2+ years after the thesis (the canon paper's rule), before and after
    first_year, by cause."""
    c = con()
    c.execute(f"CREATE OR REPLACE TABLE wy AS SELECT * FROM read_csv('{YEARS}', all_varchar=false)")
    c.execute("""CREATE OR REPLACE TABLE pairs AS SELECT cit.did, m.gkey AS key, d.year ty, min(cw.year) printed_min,
                 string_agg(DISTINCT cw.title, ' | ') printed_titles, bool_or(m.edition_moved) edition_moved
                 FROM cit JOIN cmap m USING (work_id) JOIN diss d ON d.id = cit.did JOIN cw USING (work_id)
                 WHERE m.gkey IS NOT NULL AND d.year IS NOT NULL GROUP BY 1, 2, 3""")
    c.execute("""CREATE OR REPLACE TABLE ana AS SELECT p.*, g.year gy, g.label, g.kind, g.resolution, g.kind_proposed,
                 y.first_year, y.first_year_catalogue, y.sources,
                 g.key IN (SELECT key FROM rv) OR g.label ILIKE 'review of%' OR coalesce(g.kind_proposed, '') IN ('review', 'book-review')
                   OR regexp_matches(g.label, '\\((?:[^()]*\\b(?:and|eds?\\.?|by)\\b[^()]*|[A-Z][a-z]+ [A-Z][a-z]+)\\)\\s*(:|$)') review_like
                 FROM pairs p JOIN gw g ON g.key = p.key LEFT JOIN wy y ON y.key = p.key WHERE g.year > p.ty + 1""")
    c.execute("""CREATE OR REPLACE TABLE ana2 AS SELECT *,
        coalesce(first_year_catalogue, gy) <= ty + 1 fixed_catalogue, coalesce(first_year, gy) <= ty + 1 fixed_any,
        tjac(label, split_part(printed_titles, ' | ', 1)) tsim,
        CASE WHEN review_like THEN 'review-keyed-as-book'
             -- a printed title unlike the work's, with no translation or edition evidence: a wrong match even if dated
             -- the thesis prints the title in another language than the work's: an original matched to its
             -- translation's key (or the reverse): the canonical-direction defect, not a date defect
             WHEN tjac(label, split_part(printed_titles, ' | ', 1)) < 0.5 AND printed_min <= ty
                  AND lang_guess(split_part(printed_titles, ' | ', 1)) <> lang_guess(label) THEN 'cross-language-match'
             WHEN tjac(label, split_part(printed_titles, ' | ', 1)) < 0.2 AND NOT edition_moved
                  AND coalesce(sources, '') NOT LIKE '%cluster%' THEN 'wrong-match'
             WHEN coalesce(first_year_catalogue, gy) <= ty + 1 AND key LIKE 'w-%' THEN 'reprint-key'
             WHEN coalesce(first_year_catalogue, gy) <= ty + 1 THEN 'reprint-unkeyed-record'
             WHEN printed_min <= ty AND tjac(label, split_part(printed_titles, ' | ', 1)) >= 0.6 THEN
                  CASE WHEN key LIKE 'doi:%' OR key LIKE 'openalex:%' THEN 'reprint-doi'
                       WHEN key LIKE 'w-%' THEN 'reprint-key-thesis-year-only' ELSE 'reprint-unkeyed-thesis-year-only' END
             -- the thesis itself prints a year after its own date: the thesis is dated early (revised, or a
             -- forthcoming work cited): not a work-year defect
             WHEN printed_min > ty AND tjac(label, split_part(printed_titles, ' | ', 1)) >= 0.6 THEN 'thesis-date-or-forthcoming'
             WHEN gy - ty <= 3 THEN 'near-date'
             ELSE 'wrong-match' END cause FROM ana""")
    tot = c.execute('SELECT count(*) FROM pairs').fetchone()[0]
    r = c.execute("""SELECT count(*), count(DISTINCT key), count(*) FILTER (WHERE NOT fixed_catalogue), count(*) FILTER (WHERE NOT fixed_any)
                     FROM ana2""").fetchone()
    causes = c.execute("""SELECT cause, count(*), count(DISTINCT key), count(*) FILTER (WHERE fixed_any), count(*) FILTER (WHERE fixed_catalogue)
                          FROM ana2 GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    print('pairs', tot, 'anachronistic', r)
    for x in causes:
        print(x)
    OUT.mkdir(parents=True, exist_ok=True)
    c.execute(f"""COPY (SELECT key, label, gy AS year, kind, cause, count(*) pairs, min(ty) first_citing_thesis_year, min(printed_min) printed_min,
                  any_value(first_year) first_year FROM ana2 WHERE cause IN ('wrong-match', 'near-date', 'review-keyed-as-book')
                  GROUP BY ALL ORDER BY pairs DESC) TO '{OUT}/anachronism-hold-candidates.csv' (HEADER)""")
    c.execute(f"""COPY (SELECT cause, count(*) pairs, count(DISTINCT key) works, count(*) FILTER (WHERE fixed_catalogue) fixed_by_catalogue,
                  count(*) FILTER (WHERE fixed_any) fixed_with_thesis_printed FROM ana2 GROUP BY 1 ORDER BY 2 DESC) TO '{OUT}/anachronisms-by-cause.csv' (HEADER)""")
    # the same rule on the graph's own thesis CITES (as the explorer sees them)
    gr = c.execute(f"""WITH t AS (SELECT DISTINCT c."from" th, c."to" w FROM '{G}/cites.parquet' c WHERE c.source LIKE '%thesis%')
        SELECT count(*), count(*) FILTER (WHERE g.year > tg.year + 1),
               count(*) FILTER (WHERE coalesce(y.first_year_catalogue, g.year) > tg.year + 1),
               count(*) FILTER (WHERE coalesce(y.first_year, g.year) > tg.year + 1)
        FROM t JOIN gw g ON g.key = t.w JOIN gw tg ON tg.key = t.th LEFT JOIN wy y ON y.key = t.w""").fetchone()
    rep = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    rep['anachronisms'] = dict(rule='work year > thesis year + 1 (canon paper 08)', corpus_pairs=tot, before=r[0], works=r[1],
                               after_first_year_catalogue=r[2], after_first_year=r[3],
                               by_cause={x[0]: dict(pairs=x[1], works=x[2], fixed_with_thesis_printed=x[3], fixed_by_catalogue=x[4]) for x in causes},
                               graph_thesis_cites=dict(pairs=gr[0], before=gr[1], after_catalogue=gr[2], after_first_year=gr[3]))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, default=str) + '\n')


def sample(args):
    c = con(read_only=True)
    rows = c.execute(f"""SELECT * FROM (SELECT cause, key, label, gy, ty, printed_min, first_year, first_year_catalogue,
        substr(printed_titles, 1, 200) printed, row_number() OVER (PARTITION BY cause ORDER BY hash(key || did || '{args.seed}')) rn
        FROM ana2) WHERE rn <= 7 ORDER BY cause, rn""").fetchall()
    with open(SCRATCH / 'anachronism-audit.tsv', 'w', encoding='utf-8') as f:
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    print(len(rows), SCRATCH / 'anachronism-audit.tsv')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for s in ('prepare', 'years', 'canonical', 'anachronisms'):
        sub.add_parser(s)
    a = sub.add_parser('sample')
    a.add_argument('--seed', default='1')
    args = ap.parse_args()
    {'prepare': prepare, 'years': years, 'canonical': canonical, 'anachronisms': anachronisms, 'sample': sample}[args.cmd](args)


if __name__ == '__main__':
    main()
