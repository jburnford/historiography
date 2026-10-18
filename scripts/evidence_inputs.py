"""Source-preserving journal inputs and DOI-linked publisher pagination supplements."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = [ROOT/'data/history-journals-full-2026-09-22',
               ROOT/'data/history-journals-supplement-2026-09-26',
               ROOT/'data/history-journals-recovery-2026-10-10',
               ROOT/'data/history-journals-canada-2026-10-12',
               ROOT/'data/history-journals-maritime-2026-10-16']
SELECTIONS = [ROOT/'data/history-journal-profession-review-2026-09-22/selected-journals.json',
              COLLECTIONS[1]/'selection.json', COLLECTIONS[2]/'selection.json', COLLECTIONS[3]/'selection.json',
              COLLECTIONS[4]/'selection.json']
REPAIR = ROOT/'data/evidence-layer/repairs/2026-10-10'
PAGES = REPAIR/'page-ranges.csv'
EXTRA_PAGES = REPAIR/'additional-page-ranges.csv'
BORN_DIGITAL = {'journal_supplement_journal_of_digital_history'}


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def selected_journals():
    return [j for p in SELECTIONS for j in json.loads(p.read_text())['journals']]


def input_paths():
    return [p/'generated/v1/catalog.duckdb' for p in COLLECTIONS] + SELECTIONS + [PAGES,EXTRA_PAGES,REPAIR/"additional-pagination-witness.json",Path(__file__)]


def venue_keys(journals):
    out = {}
    for j in journals:
        for identity in set(j.get('catalogue_ids',[])+[j['journal_key']]):
            out.setdefault(identity,set()).add(j['journal_key'])
    return out


def attach_catalogues(db):
    db.execute("SET threads=4")
    for i,path in enumerate(COLLECTIONS):
        db.execute(f'ATTACH {literal(path/"generated/v1/catalog.duckdb")} AS journal_input_{i} (READ_ONLY)')
    print('Catalogue connections ready',flush=True)
    union = lambda table: ' UNION ALL '.join(f'SELECT *,{i} AS input_order FROM journal_input_{i}.{table}' for i in range(len(COLLECTIONS)))
    db.execute(f'''CREATE TEMP TABLE x_records AS SELECT * EXCLUDE(input_order) FROM ({union('records')})
        QUALIFY row_number() OVER(PARTITION BY record_id ORDER BY input_order)=1''')
    print('Distinct records loaded',flush=True)
    db.execute(f'CREATE TEMP TABLE x_memberships AS SELECT DISTINCT record_id,journal_key FROM ({union("memberships")})')
    db.execute(f'CREATE TEMP TABLE x_journals AS SELECT * EXCLUDE(input_order) FROM ({union("journals")})')
    db.execute('CREATE TEMP TABLE publisher_pages(record_id VARCHAR,first_page BIGINT,last_page BIGINT,page_count BIGINT)')
    rows=[]
    for path in (PAGES,EXTRA_PAGES):
        with path.open() as f:
            rows.extend(csv.DictReader(f))
    seen = {}
    for r in rows:
        if r['status'] != 'metadata_checked':
            continue
        a,b = int(r['first_page']),int(r['last_page'])
        if not (a>0 and a<=b and b-a+1<=200 and r['source_url'].startswith('https://') and len(r['source_sha256'])==64):
            raise ValueError('Invalid sourced pagination assertion')
        value=(r['record_id'],a,b,b-a+1)
        if r['record_id'] in seen and seen[r['record_id']]!=value:
            raise ValueError('Conflicting sourced pagination assertions')
        seen[r['record_id']]=value
    if seen:
        db.executemany('INSERT INTO publisher_pages VALUES (?,?,?,?)',list(seen.values()))
    # Assertions fill unknown lengths only. Deposited ranges always take precedence.
    bad = db.execute('''SELECT p.record_id FROM publisher_pages p JOIN x_records r USING(record_id)
        WHERE (r.first_page IS NOT NULL AND r.first_page<>p.first_page)
        OR (r.page_count IS NOT NULL AND r.page_count<>p.page_count)''').fetchall()
    if bad:
        raise ValueError(f'Pagination supplement conflicts with deposits: {bad[:5]}')
    missing = db.execute('SELECT p.record_id FROM publisher_pages p LEFT JOIN x_records r USING(record_id) WHERE r.record_id IS NULL').fetchall()
    if missing:
        raise ValueError(f'Pagination supplement has unknown DOIs: {missing[:5]}')
    # Issue-sequence lengths (user decision 2026-10-16, record-wide): many older deposits (JSTOR
    # backfiles such as Military Affairs) give only a first page. The next article's first page in
    # the same journal, volume and issue bounds the length. Tested as a >=10-page classifier on
    # 569,765 records with deposited ranges: precision 98.6%, recall 99.4% (pre-1960: 97.1/98.7);
    # exact lengths agree only ~46% (blank pages, plates), so the inferred value is used for the
    # research-length proxy and kept apart by `length_basis`. Deposits and sourced assertions win.
    db.execute('CREATE TEMP TABLE inferred_pages(record_id VARCHAR,inferred_page_count BIGINT)')
    cols={r[0] for r in db.execute('DESCRIBE x_records').fetchall()}
    if {'volume','issue','first_page','page_count'}<=cols:
        db.execute('''INSERT INTO inferred_pages
            WITH k AS (SELECT r.record_id,min(m.journal_key) AS journal_key,any_value(r.volume) AS v,
                              any_value(r.issue) AS i,any_value(r.first_page) AS fp
                       FROM x_records r JOIN x_memberships m USING(record_id)
                       WHERE r.record_type='journal-article' AND NOT coalesce(r.is_test_record,false)
                         AND r.first_page IS NOT NULL AND r.volume IS NOT NULL AND r.issue IS NOT NULL
                       GROUP BY r.record_id),
            s AS (SELECT *,lead(fp) OVER(PARTITION BY journal_key,v,i ORDER BY fp,record_id) AS nxt,
                         count(*) OVER(PARTITION BY journal_key,v,i,fp) AS same_start FROM k)
            SELECT s.record_id,s.nxt-s.fp FROM s JOIN x_records r USING(record_id)
            WHERE r.page_count IS NULL AND s.same_start=1 AND s.nxt>s.fp AND s.nxt-s.fp<=200''')
    db.execute('''CREATE TEMP TABLE x_effective_records AS
        SELECT r.*,coalesce(r.page_count,p.page_count,ip.inferred_page_count) AS effective_page_count,
               CASE WHEN r.page_count IS NOT NULL THEN 'deposited' WHEN p.page_count IS NOT NULL THEN 'publisher_assertion'
                    WHEN ip.inferred_page_count IS NOT NULL THEN 'issue_sequence_inferred' END AS length_basis
        FROM x_records r LEFT JOIN publisher_pages p USING(record_id) LEFT JOIN inferred_pages ip USING(record_id)''')
    db.execute('''CREATE TEMP TABLE x_research AS SELECT record_id FROM x_effective_records
        WHERE record_type='journal-article' AND NOT coalesce(is_test_record,false) AND effective_page_count>=10''')
