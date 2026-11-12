"""Build the scratch DuckDB (base.duckdb) every analysis reads. Read-only on all inputs; writes only to SCRATCH.

Corpus side (the denominator): every strict citation (dissertation, cited corpus work), the cited work as cited
(kind, year, how theses label it), and whether a crosswalk matched it, by which route and on which basis. The match
flag reproduces scripts/export_cited_works.py as of 2026-11-11 evening (report.json corpus.matched_after, 41.96%): the
older crosswalks behind data/graph/cites.csv.gz (three + the translation checks + the Qwen tail), else LC full catalogue >
Crossref > OpenAlex (guards, agreement review) > Crossref metadata, else a translation recovered to its original.
cmap gives each matched corpus work two graph keys: gkey (edition roll-up: a translation or later edition -> the
original) and gkey_cited (the node it was matched to as cited). Compilations (corpus: works) are in cmap, not in xw.

Graph side: CITES edges (thesis and JSTOR citing documents), cited work kind/year, credits work -> person (authored,
edited, and the linked credits: separate tables until 2026-11-11, evidence = 'linked' rows since), person roles and labels.
"""
import json

from common import BASE, CITED, CORPUS, FACTS, GRAPH, IDS, KEYLOG_CACHE, connect, out, wait_memory

COMMA = ('lc-comma', 'corpus-comma', 'both-comma')


def main():
    wait_memory(6)
    if BASE.exists():
        BASE.unlink()
    con = connect(read_only=False)
    C, G = CORPUS, GRAPH
    print('graph folder:', G)

    # ---- theses -----------------------------------------------------------------------------------------------
    con.execute(f"""CREATE TABLE diss AS
        SELECT id, country, institution, TRY_CAST(year AS INT) AS year,
               (TRY_CAST(year AS INT)//10)*10 AS decade,
               CASE WHEN country='CA' AND regexp_matches(coalesce(institution,''),
                    '(?i)laval|montr[eé]al|uqam|sherbrooke|qu[eé]bec|ottawa') THEN 'CA-quebec-or-ottawa'
                    WHEN country='CA' THEN 'CA-other' ELSE country END AS country_detail,
               TRY_CAST(bibliography_entries AS INT) AS bib_entries
        FROM read_csv('{C}/dissertations.csv', all_varchar=true) WHERE in_analysis='True'""")

    # ---- cited corpus works (as cited) ------------------------------------------------------------------------
    con.execute(f"""CREATE TABLE cw AS
        SELECT work_id, kind, TRY_CAST(year AS INT) AS year,
               coalesce(TRY_CAST(json_extract(cited_as,'$.primary') AS INT),0) AS prim,
               coalesce(TRY_CAST(json_extract(cited_as,'$.secondary') AS INT),0) AS sec,
               coalesce(TRY_CAST(json_extract(cited_as,'$.unspecified') AS INT),0) AS unsp,
               title, authors
        FROM read_csv('{C}/works.csv', all_varchar=true)""")
    con.execute("""UPDATE cw SET year=NULL WHERE year<1400 OR year>2026""")

    # ---- strict citations -------------------------------------------------------------------------------------
    con.execute(f"""CREATE TABLE cit AS SELECT dissertation_id AS did, work_id
        FROM read_csv('{C}/strict-citations.csv.gz', all_varchar=true)""")

    # ---- crosswalks: the corpus match as export_cited_works.py (2026-11-11 evening) counts it ---------------------
    # matched = the older crosswalks behind data/graph/cites.csv.gz (three + four translation checks + the Qwen tail),
    # else LC > Crossref > OpenAlex (guards, agreement review) > Crossref metadata (held / review-like dropped), else a
    # translation or later edition recovered to its original (editions.csv.gz). Compilations (corpus: works) are kept
    # apart: report.json counts them only in rate_with_compilations.
    old = [IDS / 'cited-works-2026-11-04/crosswalk.csv.gz', IDS / 'cited-articles-2026-11-03b/crosswalk.csv.gz',
           IDS / 'cited-own-works-2026-11-03f/crosswalk.csv.gz']
    old += [IDS / f'translation-check-2026-11-03{x}/crosswalk.csv.gz' for x in ('d', 'c', 'b', '')]
    old += [IDS / 'qwen-tail-2026-11-04/crosswalk.csv.gz']
    con.execute("CREATE TABLE xold AS " + " UNION ".join(
        f"SELECT work_id, key, {i} AS ord FROM read_csv('{p}', all_varchar=true) WHERE coalesce(key,'')<>''"
        for i, p in enumerate(old)))
    lc, oa, cr = (IDS / f'cited-works-{s}-2026-11-10' for s in ('lc-full', 'openalex', 'crossref'))
    cm = IDS / 'cited-works-crossref-meta-2026-11-11'
    jm = IDS / 'cited-works-journal-meta-2026-11-11'      # 2026-11-12 rerun: journal metadata, last (42.14%)
    rc = lambda p: f"read_csv('{p}', all_varchar=true)"
    # chosen: one row per corpus work (route, basis, ids) in export_cited_works precedence
    con.execute(f"""CREATE TABLE chosen AS
        WITH l AS (SELECT work_id, 'lc-full' route, basis,
                          list_transform(list_filter(string_split(lccns,';'), x -> trim(x)<>''), x -> 'lccn:'||x) ids
                   FROM {rc(lc / 'crosswalk.csv.gz')}),
             c AS (SELECT work_id, 'crossref' route, basis, ['doi:'||lower(doi)] ids FROM {rc(cr / 'crosswalk.csv.gz')}
                   WHERE work_id NOT IN (SELECT work_id FROM l)),
             rv AS (SELECT work_id, right_side FROM read_csv('{cr / 'agreement-review.csv'}', all_varchar=true)),
             df AS (SELECT d.*, coalesce(rv.right_side,'') side FROM {rc(cr / 'agreement-different.csv.gz')} d
                    LEFT JOIN rv USING (work_id)),
             o0 AS (SELECT * FROM {rc(oa / 'crosswalk.csv.gz')}
                    WHERE work_id NOT IN (SELECT work_id FROM l) AND work_id NOT IN (SELECT work_id FROM c)),
             od AS (SELECT o0.work_id, 'crossref' route, df.basis || '+agreement-' || CASE WHEN side='' THEN 'unreviewed'
                           ELSE side END basis,
                           CASE WHEN side='both' THEN ['doi:'||lower(df.cr_doi), 'doi:'||lower(df.oa_doi)]
                                ELSE ['doi:'||lower(df.cr_doi)] END ids
                    FROM o0 JOIN df USING (work_id) WHERE side<>'openalex'),
             o AS (SELECT work_id, 'openalex' route, basis,
                          list_filter([CASE WHEN coalesce(doi,'')<>'' THEN 'doi:'||lower(doi) END,
                                       CASE WHEN coalesce(openalex_id,'')<>'' THEN 'openalex:'||openalex_id END],
                                      x -> x IS NOT NULL) ids
                   FROM o0 WHERE work_id NOT IN (SELECT work_id FROM od)
                     AND work_id NOT IN (SELECT work_id FROM {rc(CITED / 'openalex-guarded.csv.gz')})),
             pre AS (SELECT * FROM l UNION ALL SELECT * FROM c UNION ALL SELECT * FROM od UNION ALL SELECT * FROM o),
             m AS (SELECT work_id, 'crossref-meta' route, basis, ['doi:'||lower(doi)] ids FROM {rc(cm / 'crosswalk.csv.gz')}
                   WHERE work_id NOT IN (SELECT work_id FROM pre)
                     AND work_id NOT IN (SELECT work_id FROM {rc(cm / 'held.csv.gz')})
                     AND work_id NOT IN (SELECT work_id FROM {rc(cm / 'match-flags.csv.gz')} WHERE review_like='1')),
             j AS (SELECT work_id, 'journal-meta' route, basis, [id] ids FROM {rc(jm / 'crosswalk.csv.gz')}
                   WHERE work_id NOT IN (SELECT work_id FROM pre) AND work_id NOT IN (SELECT work_id FROM m)
                     AND work_id NOT IN (SELECT work_id FROM {rc(jm / 'held.csv.gz')}) AND coalesce(review_like,'0')<>'1')
        SELECT * FROM pre UNION ALL SELECT * FROM m UNION ALL SELECT * FROM j""")
    # translations / later editions (after the guards export_cited_works applies) and compilations
    con.execute(f"""CREATE TABLE tx AS SELECT work_id, canonical, cited_as, relation, route, cited_language,
        TRY_CAST(cited_year AS INT) cited_year FROM {rc(CITED / 'editions.csv.gz')}""")
    con.execute(f"""CREATE TABLE xcomp AS SELECT substr(id, 8) work_id, id gkey FROM {rc(CITED / 'works.csv.gz')}
        WHERE id LIKE 'corpus:%'""")
    con.execute(f"""CREATE TABLE xw AS
        WITH a AS (SELECT DISTINCT work_id FROM xold UNION SELECT work_id FROM chosen UNION SELECT work_id FROM tx)
        SELECT a.work_id,
               CASE WHEN o.work_id IS NOT NULL THEN 'older-crosswalks' WHEN n.work_id IS NOT NULL THEN n.route
                    ELSE 'translation-recovered' END AS route,
               CASE WHEN o.work_id IS NOT NULL THEN NULL ELSE n.basis END AS basis,
               (o.work_id IS NULL AND n.route='lc-full' AND split_part(n.basis,'/',1) IN {COMMA}) AS comma,
               (t.work_id IS NOT NULL) AS edition_moved
        FROM a LEFT JOIN (SELECT DISTINCT work_id FROM xold) o USING (work_id)
        LEFT JOIN chosen n USING (work_id) LEFT JOIN (SELECT DISTINCT work_id FROM tx) t USING (work_id)""")

    # ---- graph ------------------------------------------------------------------------------------------------
    con.execute(f"""CREATE TABLE tk AS SELECT key, substr(a, 13) AS did FROM
        (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a LIKE 'diss-thesis:%'""")
    # 2026-11-12 rerun: `year` is the work's first publication year where the build has one (first_year, from
    # data/graph/work-years.csv.gz: LC notes, 008 reprint dates, edition clusters), else the key year; key_year keeps
    # the key's own year (a reprint year for some keys, class 17)
    import pyarrow.parquet as pq
    fy = 'first_year' in pq.read_schema(f'{G}/work.parquet').names
    con.execute(f"""CREATE TABLE gw AS SELECT key, kind, {'coalesce(first_year, year)' if fy else 'year'} AS year,
        year AS key_year, journal, label, resolution,
        CASE WHEN key LIKE 'lccn:%' OR key LIKE 'doi:%' THEN 'unkeyed' ELSE 'keyed' END AS layer
        FROM '{G}/work.parquet'""")
    # source since 2026-11-11: thesis / thesis-matched / thesis-edition / jstor / jstor-matched, comma-joined when one
    # edge has several; every jstor* edge has a JSTOR citing article
    con.execute(f"""CREATE TABLE gc AS SELECT "from" AS src, "to" AS dst, edition, source, cited_as,
        CASE WHEN source LIKE 'jstor%' THEN 'article' ELSE 'thesis' END AS ctype FROM '{G}/cites.parquet'""")
    # citing documents: theses (with corpus metadata) and JSTOR articles (year, journal)
    con.execute("""CREATE TABLE citing AS
        SELECT DISTINCT g.src AS key, 'thesis' AS ctype, d.year, d.country, d.institution, d.id AS did, NULL AS journal
        FROM gc g JOIN tk ON tk.key=g.src JOIN diss d ON d.id=tk.did WHERE g.ctype='thesis'
        UNION ALL
        SELECT DISTINCT g.src, 'article', w.year, NULL, NULL, NULL, w.journal
        FROM gc g LEFT JOIN gw w ON w.key=g.src WHERE g.ctype='article'""")
    import pyarrow.parquet as pq
    if 'role' in pq.read_schema(f'{G}/authored.parquet').names:
        # since 2026-11-12 credits carry a role: edition editors, translators, introducers and series editors prepared
        # someone else's work; how = 'edition_role', left out of hows() so they never count as the person's citations
        er = "('edition-editor','translator','introducer','series-editor','contributor')"  # contributor: 2026-11-12
        con.execute(f"""CREATE TABLE cred AS
            SELECT "from" AS person, "to" AS work, CASE WHEN role IN {er} THEN 'edition_role'
                   WHEN evidence = 'keylog' THEN 'authored' ELSE 'linked_authored' END AS how
              FROM '{G}/authored.parquet'
            UNION ALL SELECT "from", "to", CASE WHEN role IN {er} THEN 'edition_role'
                   WHEN evidence = 'keylog' THEN 'edited' ELSE 'linked_edited' END FROM '{G}/edited.parquet'""")
    elif 'evidence' in pq.read_schema(f'{G}/authored.parquet').names:
        # one table per relation since 2026-11-11: evidence 'keylog' = the key log's credits, 'linked' = rule credits
        con.execute(f"""CREATE TABLE cred AS
            SELECT "from" AS person, "to" AS work, CASE evidence WHEN 'keylog' THEN 'authored' ELSE 'linked_authored' END AS how
              FROM '{G}/authored.parquet'
            UNION ALL SELECT "from", "to", CASE evidence WHEN 'keylog' THEN 'edited' ELSE 'linked_edited' END FROM '{G}/edited.parquet'""")
    else:
        con.execute(f"""CREATE TABLE cred AS
            SELECT "from" AS person, "to" AS work, 'authored' AS how FROM '{G}/authored.parquet'
            UNION ALL SELECT "from", "to", 'edited' FROM '{G}/edited.parquet'
            UNION ALL SELECT "from", "to", 'linked_authored' FROM '{G}/linked_authored.parquet'
            UNION ALL SELECT "from", "to", 'linked_edited' FROM '{G}/linked_edited.parquet'""")
    con.execute(f"""CREATE TABLE person AS SELECT p.key, p.label, p.resolution, p.lcnaf, p.wd, p.orcid,
        r.role, r.confidence, r.signals, l.birth, l.death
        FROM '{G}/person.parquet' p
        LEFT JOIN read_csv('{FACTS}/person-roles.csv.gz', all_varchar=true) r USING (key)
        LEFT JOIN read_csv('{FACTS}/life-years.csv.gz', all_varchar=true) l USING (key)""")
    con.execute(f"""CREATE TABLE supervised AS SELECT "from" AS person, "to" AS thesis FROM '{G}/supervised.parquet'""")
    con.execute(f"""CREATE TABLE advised AS SELECT "from" AS advisor, "to" AS student, thesis FROM '{G}/advised.parquet'""")

    # cited-works ids -> graph key (as build_graph does: a key holding one of its identifiers, else the id) + basis
    con.execute(f"""CREATE TABLE anc AS SELECT a, min(key) AS key, count(DISTINCT key) AS n FROM
        (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a LIKE 'lccn:%' OR a LIKE 'doi:%' OR a LIKE 'openalex:%'
        GROUP BY 1""")
    # cited-works ids -> graph key (as build_graph does: a key holding one of its identifiers, else the id) + basis
    con.execute(f"""CREATE TABLE cwk AS
        WITH w AS (SELECT id, source, basis, split_part(basis,'/',1) IN {COMMA} AND source='lc-full' AS comma,
                          list_distinct([id] || list_transform(list_filter(string_split(coalesce(lccns,''),';'), x -> x<>''),
                                                               x -> 'lccn:'||x)
                                        || list_filter(string_split(coalesce(alias_ids,''),';'), x -> x<>'')) ids
                   FROM read_csv('{CITED}/works.csv.gz', all_varchar=true)),
             u AS (SELECT id, unnest(ids) x FROM w),
             h AS (SELECT u.id, min(anc.key) k, count(DISTINCT anc.key) n FROM u JOIN anc ON anc.a=u.x
                   WHERE anc.key NOT LIKE 'lccn:%' AND anc.key NOT LIKE 'doi:%' AND anc.key NOT LIKE 'openalex:%'
                   GROUP BY u.id)
        SELECT w.id, w.source, w.basis, w.comma, CASE WHEN h.n=1 THEN h.k ELSE w.id END AS gkey
        FROM w LEFT JOIN h USING (id)""")
    con.execute(f"""CREATE TABLE cwid AS SELECT id, unnest(list_distinct([id]
        || list_transform(list_filter(string_split(coalesce(lccns,''),';'), x -> x<>''), x -> 'lccn:'||x)
        || list_filter(string_split(coalesce(alias_ids,''),';'), x -> x<>''))) x
        FROM read_csv('{CITED}/works.csv.gz', all_varchar=true)""")
    # retired work keys (merged since the crosswalks were made) -> the live key, from the key-log cache (read only)
    import sqlite3
    sq = sqlite3.connect(f'file:{KEYLOG_CACHE}?mode=ro', uri=True)
    nxt = {k: json.loads(rb or '[]') for k, rb in sq.execute(
        "SELECT key, replaced_by FROM keys WHERE status IN ('merged','split','withdrawn','retyped') AND key LIKE 'w-%'")}
    sq.close()
    live = {}
    for k in nxt:                       # follow replaced_by to live keys; a split (several live successors) stays unresolved
        todo, seen, res = [k], set(), set()
        while todo:
            c = todo.pop()
            if c in seen:
                continue
            seen.add(c)
            if c in nxt:
                todo.extend(nxt[c])
            else:
                res.add(c)
        if len(res) == 1:
            live[k] = res.pop()
    con.execute('CREATE TABLE ret(key VARCHAR, live VARCHAR)')
    con.executemany('INSERT INTO ret VALUES (?, ?)', list(live.items()))
    # resolver: any name a crosswalk or the editions table gives (a key, a cited-works id, an anchor) -> graph key
    con.execute("""CREATE TABLE names AS SELECT DISTINCT key x FROM xold UNION SELECT unnest(ids) FROM chosen
                   UNION SELECT canonical FROM tx UNION SELECT cited_as FROM tx""")
    con.execute("""CREATE TABLE rslv AS
        WITH cw1 AS (SELECT cwid.x, min(cwk.gkey) g, count(DISTINCT cwk.gkey) n FROM cwid JOIN cwk USING (id) GROUP BY 1)
        SELECT n.x, coalesce(CASE WHEN cw1.n=1 THEN cw1.g END, g.key, a.key, gr.key) gkey,
               CASE WHEN cw1.n=1 THEN 'cited-works' WHEN g.key IS NOT NULL THEN 'graph-key' WHEN a.key IS NOT NULL
                    THEN 'anchor' WHEN gr.key IS NOT NULL THEN 'retired->live' END how
        FROM names n LEFT JOIN cw1 ON cw1.x=n.x LEFT JOIN gw g ON g.key=n.x LEFT JOIN anc a ON a.a=n.x
        LEFT JOIN ret r ON r.key=n.x LEFT JOIN gw gr ON gr.key=r.live""")
    # corpus work -> graph key. gkey_cited = the node the work was matched to as cited (older crosswalks first, all
    # their keys: min kept, the count in n_old_keys; else the chosen crosswalk id); gkey = the same with the edition
    # roll-up: a translation / later edition goes to the original (canonical) work; compilations go to corpus:<work_id>.
    con.execute("""CREATE TABLE cmap AS
        WITH o AS (SELECT x.work_id, min(r.gkey) g, count(DISTINCT r.gkey) n FROM xold x LEFT JOIN rslv r ON r.x=x.key
                   GROUP BY 1),
             nw AS (SELECT c.work_id, min(r.gkey) g, count(DISTINCT r.gkey) n
                    FROM (SELECT work_id, unnest(ids) x FROM chosen) c LEFT JOIN rslv r USING (x) GROUP BY 1),
             t AS (SELECT tx.work_id, r.gkey g FROM tx LEFT JOIN rslv r ON r.x=tx.canonical),
             a AS (SELECT work_id FROM xw UNION SELECT work_id FROM xcomp)
        SELECT a.work_id, CASE WHEN xc.work_id IS NOT NULL AND t.work_id IS NULL THEN 'compilation' ELSE xw.route END route,
               coalesce(xw.comma, false) comma, coalesce(xw.edition_moved, false) edition_moved,
               (xw.work_id IS NOT NULL) AS matched,
               CASE WHEN t.work_id IS NOT NULL THEN (CASE WHEN xw.route='older-crosswalks' THEN o.g ELSE nw.g END)
                    WHEN xc.work_id IS NOT NULL THEN xc.gkey
                    WHEN xw.route='older-crosswalks' THEN o.g ELSE nw.g END AS gkey_cited,
               CASE WHEN t.work_id IS NOT NULL THEN t.g WHEN xc.work_id IS NOT NULL THEN xc.gkey
                    WHEN xw.route='older-crosswalks' THEN o.g ELSE nw.g END AS gkey,
               o.n AS n_old_keys, nw.n AS n_new_keys
        FROM a LEFT JOIN xw USING (work_id) LEFT JOIN xcomp xc USING (work_id) LEFT JOIN o USING (work_id)
        LEFT JOIN nw USING (work_id) LEFT JOIN t USING (work_id)""")
    # 2026-11-12 rerun: canonical keys that are themselves translations while the original is known move to the
    # original, as build_graph does with data/graph/edition-canonical-fixes.csv.gz (a key with two proposals is
    # skipped); roll-up key only (gkey), never gkey_cited
    fixes = CITED.parent / 'edition-canonical-fixes.csv.gz'
    con.execute(f"""CREATE TABLE cfix AS
        WITH f AS (SELECT current_canonical cur, proposed_canonical prop FROM {rc(fixes)}),
             one AS (SELECT cur, min(prop) prop FROM f GROUP BY 1 HAVING count(DISTINCT prop)=1)
        SELECT one.cur, coalesce(g.key, gr.key) prop FROM one LEFT JOIN gw g ON g.key=one.prop
        LEFT JOIN ret r ON r.key=one.prop LEFT JOIN gw gr ON gr.key=r.live""")
    con.execute("""UPDATE cmap SET gkey = cfix.prop FROM cfix WHERE cmap.gkey = cfix.cur AND cfix.prop IS NOT NULL""")

    stats = {}
    for t in ('diss', 'cw', 'cit', 'xold', 'chosen', 'tx', 'xcomp', 'xw', 'tk', 'gw', 'gc', 'citing', 'cred', 'person',
              'supervised', 'advised', 'cwk', 'ret', 'cmap', 'cfix'):
        stats[t] = con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    stats['corpus_matched_rows'] = con.execute('SELECT count(*) FROM cit JOIN xw USING (work_id)').fetchone()[0]
    stats['corpus_rate'] = round(stats['corpus_matched_rows'] / stats['cit'], 4)
    stats['corpus_rows_with_compilations'] = con.execute(
        'SELECT count(*) FROM cit JOIN cmap USING (work_id)').fetchone()[0]
    stats['corpus_rows_by_route'] = dict(con.execute(
        'SELECT route, count(*) FROM cit JOIN cmap USING (work_id) GROUP BY 1 ORDER BY 2 DESC').fetchall())
    stats['corpus_rows_edition_moved'] = con.execute(
        'SELECT count(*) FROM cit JOIN cmap USING (work_id) WHERE edition_moved').fetchone()[0]
    stats['cmap_works_moved_by_canonical_fix'] = con.execute(
        'SELECT count(*) FROM cmap WHERE gkey IN (SELECT prop FROM cfix) AND gkey <> coalesce(gkey_cited, \'\')').fetchone()[0]
    stats['gw_first_year_differs'] = con.execute('SELECT count(*) FROM gw WHERE year <> key_year').fetchone()[0]
    stats['resolver_by_how'] = {str(k): v for k, v in con.execute(
        'SELECT how, count(*) FROM rslv GROUP BY 1 ORDER BY 2 DESC').fetchall()}
    stats['cmap_unmapped_works'] = con.execute('SELECT count(*) FROM cmap WHERE gkey IS NULL').fetchone()[0]
    stats['cmap_unmapped_citations'] = con.execute(
        'SELECT count(*) FROM cit JOIN cmap USING (work_id) WHERE gkey IS NULL').fetchone()[0]
    stats['cmap_gkey_not_a_graph_node'] = con.execute(
        'SELECT count(*) FROM cmap WHERE gkey IS NOT NULL AND gkey NOT IN (SELECT key FROM gw)').fetchone()[0]
    stats['cmap_works_on_several_old_keys'] = con.execute('SELECT count(*) FROM cmap WHERE n_old_keys>1').fetchone()[0]
    # thesis graph pairs rebuilt from the corpus (distinct thesis, graph work) vs the graph's own thesis CITES
    con.execute("""CREATE TEMP TABLE mine AS SELECT DISTINCT tk.key src, m.gkey dst FROM cit JOIN cmap m USING (work_id)
                   JOIN tk ON tk.did=cit.did WHERE m.gkey IS NOT NULL""")
    con.execute("CREATE TEMP TABLE theirs AS SELECT DISTINCT src, dst FROM gc WHERE ctype='thesis'")
    stats['corpus_graph_pairs'] = con.execute('SELECT count(*) FROM mine').fetchone()[0]
    stats['graph_thesis_pairs'] = con.execute('SELECT count(*) FROM theirs').fetchone()[0]
    stats['pairs_in_both'] = con.execute('SELECT count(*) FROM mine JOIN theirs USING (src, dst)').fetchone()[0]
    stats['citing_by_type'] = dict(con.execute('SELECT ctype, count(*) FROM citing GROUP BY 1').fetchall())
    stats['cred_by_how'] = dict(con.execute('SELECT how, count(*) FROM cred GROUP BY 1').fetchall())
    stats['graph_folder'] = str(GRAPH)
    print(json.dumps(stats, indent=1))
    out('00-base-stats.json').write_text(json.dumps(stats, indent=1))
    con.close()


if __name__ == '__main__':
    main()
