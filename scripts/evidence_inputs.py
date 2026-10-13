"""Source-preserving journal inputs and DOI-linked publisher pagination supplements."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = [ROOT/'data/history-journals-full-2026-09-22',
               ROOT/'data/history-journals-supplement-2026-09-26',
               ROOT/'data/history-journals-recovery-2026-10-10',
               ROOT/'data/history-journals-canada-2026-10-12']
SELECTIONS = [ROOT/'data/history-journal-profession-review-2026-09-22/selected-journals.json',
              COLLECTIONS[1]/'selection.json', COLLECTIONS[2]/'selection.json', COLLECTIONS[3]/'selection.json']
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
    db.execute('''CREATE TEMP TABLE x_effective_records AS SELECT r.*,coalesce(r.page_count,p.page_count) AS effective_page_count
        FROM x_records r LEFT JOIN publisher_pages p USING(record_id)''')
    db.execute('''CREATE TEMP TABLE x_research AS SELECT record_id FROM x_effective_records
        WHERE record_type='journal-article' AND NOT coalesce(is_test_record,false) AND effective_page_count>=10''')
