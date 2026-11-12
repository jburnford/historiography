"""Verify author-constrained proposals mechanically against LC records and keyed works.

Judgments: judgments/*.psv, lines `work_id|verdict|orig_title|orig_year|conf|note` (verdict T translation,
E edition, C compilation, N not a translation, U unsure). Lines starting with # are skipped.
A T/E proposal counts only when the proposed original (title + author) is an LC record whose main entry
(or author/editor added entry) has the cited author's family name and a compatible initial, or a keyed work
whose label has that title and whose author label carries that family name; and the cited edition's year is
not before the original's first edition (earliest such record). Writes table `verified` in lc.duckdb."""
import csv
import glob
import re
import unicodedata
from pathlib import Path

import duckdb

S = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations')
ART = r'^(the|a|an|le|la|les|l|un|une|der|die|das|ein|eine|el|los|las|lo|il|gli|i|o|os|as|um|uma|en|het|de) '


def nt0(s):
    s = unicodedata.normalize('NFKD', (s or '').replace('œ', 'oe').replace('Œ', 'Oe').replace('æ', 'ae').replace('ß', 'ss')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', re.sub(r"['’ʹʻ]", ' ', s)).strip()


def nt(s):
    return re.sub(ART, '', nt0(s))


def main():
    idx = dict(l.rstrip('\n').split('\t') for l in open(S / 'packets' / 'idx-frozen-min5.tsv'))
    J = []
    for p in sorted(glob.glob(str(S / 'judgments' / '*.psv'))):
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('|')
            parts += [''] * (6 - len(parts))
            wid, verdict, ot, oy, conf, note = [x.strip() for x in parts[:6]]
            wid = idx.get(wid, wid)
            J.append(dict(work_id=wid, verdict=verdict, orig_title=ot, orig_year=oy, conf=conf, note=note, batch=Path(p).name))
    db = duckdb.connect(str(S / 'lc.duckdb'))
    db.execute("SET memory_limit='3GB'; SET threads=3")
    db.execute(f"ATTACH '{S}/t.duckdb' AS t (READ_ONLY)")
    db.execute("CREATE OR REPLACE TEMP TABLE j (work_id VARCHAR, verdict VARCHAR, orig_title VARCHAR, orig_year VARCHAR, conf VARCHAR, note VARCHAR, batch VARCHAR, t1 VARCHAR, t2 VARCHAR)")
    rows = []
    seen = set()
    for r in J:
        if r['work_id'] in seen:
            continue
        seen.add(r['work_id'])
        main_t = re.split(r'\s*[:;=]\s*', r['orig_title'])[0]
        t2 = nt(re.split(r'\s*[,:;=]\s*', r['orig_title'])[0])
        rows.append((r['work_id'], r['verdict'], r['orig_title'], r['orig_year'], r['conf'], r['note'], r['batch'], nt(main_t), t2))
    db.executemany("INSERT INTO j VALUES (?,?,?,?,?,?,?,?,?)", rows)
    db.execute("""CREATE OR REPLACE TEMP TABLE jc AS SELECT j.*, c.fam, c.ini, c.yr AS cited_year, c.tlang, c.n, c.title AS cited_title
                  FROM j JOIN t.ucand c USING (work_id)""")
    # LC hits: same family name, compatible initial, title key equal on either form
    db.execute("""CREATE OR REPLACE TABLE vhits AS
        SELECT jc.work_id, r.id, r.yr, r.lang, r.heading, r.uri, r.title, r.tag
        FROM jc JOIN lcrec r ON split_part(r.ak, '|', 1) = jc.fam AND (jc.ini = '' OR split_part(r.ak, '|', 2) IN ('', jc.ini))
        WHERE jc.verdict IN ('T', 'E') AND jc.t1 <> '' AND (r.tk IN (jc.t1, jc.t2) OR r.tk2 IN (jc.t1, jc.t2)
              OR (length(jc.t1) - length(replace(jc.t1, ' ', '')) >= 2 AND r.tk LIKE jc.t1 || ' %'))""")
    # LC translation clusters whose uniform title (240) is the proposed original, same author family
    db.execute("""CREATE OR REPLACE TABLE vchits AS
        SELECT DISTINCT jc.work_id, c.cluster_id, c.original_lccn, c.original_year, min(c.year) OVER (PARTITION BY jc.work_id, c.cluster_id) AS c_first
        FROM jc JOIN clusters c ON split_part(c.author_key, '|', 1) = jc.fam AND (jc.ini = '' OR split_part(c.author_key, '|', 2) IN ('', jc.ini))
        WHERE jc.verdict IN ('T', 'E') AND jc.t1 <> '' AND c.work_title_key IN (jc.t1, jc.t2) AND c.role <> 'compilation'""")
    # keyed-work hits: label title key equal, an author whose label has the family name
    db.execute("""CREATE OR REPLACE TABLE vkhits AS
        WITH c AS (SELECT jc.work_id, jc.fam, w.key, w.year, w.label FROM jc JOIN wkt w ON w.lk = jc.t1 WHERE jc.verdict IN ('T','E') AND jc.t1 <> ''
                   UNION SELECT jc.work_id, jc.fam, w.key, w.year, w.label FROM jc JOIN wkt w ON w.lk = jc.t2 WHERE jc.verdict IN ('T','E') AND jc.t2 <> '')
        SELECT DISTINCT c.work_id, c.key, c.year, c.label, p.label AS plabel
        FROM c JOIN read_parquet('/home/jic823/historiography/build/graph/authored.parquet') a ON a.to = c.key
        JOIN read_parquet('/home/jic823/historiography/build/graph/person.parquet') p ON p.key = a.from
        WHERE regexp_replace(lower(strip_accents(p.label)), '[^a-z0-9]+', ' ', 'g') LIKE '%' || c.fam || '%'""")
    db.execute("""CREATE OR REPLACE TABLE verified AS
        WITH h AS (SELECT work_id, min(yr) AS lc_first, arg_min(id, yr) AS lc_first_id, count(DISTINCT id) AS lc_n,
                          count(DISTINCT coalesce(nullif(uri, ''), heading)) AS lc_people, list(DISTINCT id) AS lc_ids,
                          arg_min(heading, yr) AS lc_heading, arg_min(title, yr) AS lc_title
                   FROM vhits GROUP BY 1),
             cc AS (SELECT work_id, count(DISTINCT cluster_id) AS n_clusters, arg_min(cluster_id, coalesce(original_year, c_first)) AS cluster_id,
                           min(coalesce(original_year, c_first)) AS c_first FROM vchits GROUP BY 1),
             k AS (SELECT work_id, min(year) AS k_first, list(DISTINCT key) AS keys, arg_min(label, year) AS k_label FROM vkhits GROUP BY 1)
        SELECT jc.*, cc.cluster_id, cc.n_clusters, cc.c_first, h.lc_first, h.lc_first_id, h.lc_n, h.lc_people, h.lc_ids, h.lc_heading, h.lc_title, k.k_first, k.keys, k.k_label,
          CASE WHEN jc.verdict NOT IN ('T', 'E') THEN jc.verdict
               WHEN h.work_id IS NULL AND k.work_id IS NULL AND cc.work_id IS NULL THEN 'fail:no_record'
               WHEN jc.cited_year IS NOT NULL
                    AND jc.cited_year < least(coalesce(h.lc_first, 9999), coalesce(k.k_first, 9999), coalesce(cc.c_first, 9999)) THEN 'fail:cited_before_original'
               WHEN h.lc_people > 1 AND k.work_id IS NULL THEN 'ok:lc_several_people'
               ELSE 'ok' END AS status
        FROM jc LEFT JOIN h USING (work_id) LEFT JOIN k USING (work_id) LEFT JOIN cc USING (work_id)""")
    print(db.execute("SELECT status, verdict, count(*), sum(n) FROM verified GROUP BY ALL ORDER BY 1, 2").fetchall())
    missing = db.execute("SELECT count(*) FROM j ANTI JOIN t.ucand USING (work_id)").fetchone()[0]
    print('judgment rows without candidate:', missing)


if __name__ == '__main__':
    main()
