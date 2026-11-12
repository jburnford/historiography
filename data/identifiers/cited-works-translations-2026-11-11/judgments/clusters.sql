SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB';
SET temp_directory='/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations/tmp';
CREATE OR REPLACE MACRO nt0(s) AS trim(regexp_replace(regexp_replace(lower(strip_accents(coalesce(s,''))), '[''’ʹʻ]', ' ', 'g'), '[^a-z0-9]+', ' ', 'g'));
CREATE OR REPLACE MACRO nt(s) AS regexp_replace(nt0(s), '^(the|a|an|le|la|les|l|un|une|der|die|das|ein|eine|el|los|las|lo|il|gli|i|o|os|as|um|uma|en|het|de) ', '');
CREATE OR REPLACE MACRO akey(h) AS nt0(split_part(h, ',', 1)) || '|' || left(nt0(split_part(h, ',', 2)), 1);
CREATE OR REPLACE MACRO lcid(lccn, control) AS coalesce(nullif(lccn, ''), control);

CREATE OR REPLACE TABLE mx AS SELECT *, lcid(lccn, control) AS id, akey(main) AS ak FROM read_parquet('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations/marcx/*.parquet');

-- collective uniform titles: no single original
CREATE OR REPLACE TABLE collective AS SELECT unnest(['works','poems','short stories','correspondence','essays','plays','novels','selected works',
  'prose works','articles','speeches','letters','diaries','sermons','tales','songs','lectures','interviews','writings','selected writings',
  'philosophical works','political works','miscellaneous works','journals','memoirs','autobiographical writings','complete works','fragments',
  'notebooks','papers','addresses','novellas','stories']) AS t;

-- translation / edition evidence on 100-entry records
CREATE OR REPLACE TABLE ev AS
WITH base AS (
  SELECT id, ak, main, main_uri, date1, lang, title, title_a, u_tag, u_a, u_l, u_k, u_np, l041h, ind041, notes, edition,
    nullif(trim(regexp_extract(notes, '(?i)^\s*translation of:?\s+(.+?)(\s*/.*|\s+;;.*)?$', 1), ' .'), '') AS note_t
  FROM mx WHERE main_tag = '100' AND ak <> '|')
SELECT *, CASE
    WHEN u_tag = '240' AND (u_k ILIKE 'selection%' OR nt(u_a) IN (SELECT t FROM collective)) THEN 'compilation'
    WHEN u_tag = '240' AND u_l <> '' AND u_np = '' THEN 'translation'
    WHEN u_tag = '240' AND u_l <> '' AND u_np <> '' THEN 'translation-part'
    WHEN u_tag = '240' AND u_l = '' AND l041h <> '' THEN 'translation'
    WHEN u_tag = '240' AND u_l = '' THEN 'edition'
    WHEN note_t IS NOT NULL AND length(note_t) > 2 THEN 'translation'
    ELSE NULL END AS evidence,
  CASE WHEN u_tag = '240' THEN 'u240' WHEN note_t IS NOT NULL THEN 'note500' END AS ev_basis,
  nt(CASE WHEN u_tag = '240' THEN u_a ELSE note_t END) AS ont
FROM base;
DELETE FROM ev WHERE evidence IS NULL OR ont = '';
-- a 240 without $l equal to the record's own title is just a uniform-title echo
DELETE FROM ev WHERE evidence = 'edition' AND ont = nt(title_a);

-- the works with a translation (cluster seeds)
CREATE OR REPLACE TABLE seeds AS SELECT DISTINCT ak, ont FROM ev WHERE evidence IN ('translation', 'translation-part', 'compilation');

-- every LC record by the same main-entry author whose title is the uniform title (originals, same-title editions)
CREATE OR REPLACE TABLE same_title AS
SELECT lcid(r.lccn, r.control) AS id, akey(h.heading) AS ak, h.heading AS main, h.uri AS main_uri, r.date1, r.lang, r.title, r.title_a, nt(r.title_a) AS ont
FROM read_parquet('/mnt/e/lc-bib-2016/index/records-*.parquet') r
JOIN read_parquet('/mnt/e/lc-bib-2016/index/headings-*.parquet') h ON h.control = r.control AND h.tag = '100'
WHERE (akey(h.heading), nt(r.title_a)) IN (SELECT (ak, ont) FROM seeds);

-- membership
CREATE OR REPLACE TABLE members AS
SELECT DISTINCT ON (id) * FROM (
  SELECT id, ak, ont, main, main_uri, date1, lang, title, evidence AS ev_kind, ev_basis, u_l, l041h, 1 AS pri FROM ev
   WHERE (ak, ont) IN (SELECT (ak, ont) FROM seeds)
  UNION ALL
  SELECT id, ak, ont, main, main_uri, date1, lang, title, 'same-title', 'title_a', '', '', 2 FROM same_title)
ORDER BY id, pri;

-- original language: from 041 $h of the translations, else the language of the earliest same-title record
CREATE OR REPLACE TABLE clang AS
WITH h AS (SELECT ak, ont, split_part(l041h, ';', 1) AS l, count(*) n FROM members WHERE ev_kind LIKE 'translation%' AND l041h <> '' GROUP BY ALL),
     h1 AS (SELECT ak, ont, arg_max(l, n) AS l FROM h GROUP BY ALL),
     s AS (SELECT ak, ont, arg_min(lang, TRY_CAST(date1 AS INT)) AS l FROM members WHERE ev_kind = 'same-title' GROUP BY ALL)
SELECT k.ak, k.ont, coalesce(h1.l, s.l) AS olang, h1.l IS NOT NULL AS from041 FROM seeds k LEFT JOIN h1 USING (ak, ont) LEFT JOIN s USING (ak, ont);

CREATE OR REPLACE TABLE clusters AS
WITH m AS (SELECT m.*, c.olang, (SELECT bool_or(ev_kind='compilation') FROM members x WHERE x.ak=m.ak AND x.ont=m.ont) AS comp FROM members m JOIN clang c USING (ak, ont)),
     orig AS (SELECT ak, ont, arg_min(id, TRY_CAST(date1 AS INT)) AS orig_id, min(TRY_CAST(date1 AS INT)) AS orig_year
              FROM m WHERE ev_kind IN ('same-title', 'edition') AND lang = olang GROUP BY ALL)
SELECT 'lcw:' || md5(m.ak || '#' || m.ont)[:12] AS cluster_id, m.id AS lccn, m.ak AS author_key, m.main AS author_heading, m.ont AS work_title_key,
  m.title, TRY_CAST(m.date1 AS INT) AS year, m.lang, m.olang AS original_lang,
  CASE WHEN m.ev_kind = 'compilation' THEN 'compilation'
       WHEN m.id = o.orig_id THEN 'original'
       WHEN m.ev_kind LIKE 'translation%' OR (m.lang <> m.olang AND m.lang <> '' AND m.olang IS NOT NULL) THEN 'translation'
       ELSE 'later edition' END AS role,
  CASE WHEN m.ev_kind IN ('translation', 'translation-part', 'compilation', 'edition') THEN m.ev_basis || ':' || m.ev_kind ELSE 'same-title' END AS basis,
  o.orig_id AS original_lccn, o.orig_year AS original_year
FROM m LEFT JOIN orig o USING (ak, ont);
