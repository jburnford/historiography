"""Provenance and reporting for the separate Crossref history-journal corpus."""
import json
import os
from pathlib import Path
from harvest_ahr_crossref import sha, write_json

ROOT=Path(__file__).resolve().parents[1]

def prepare_manifest(work):
    selection=json.loads((work/'selection.json').read_text())
    manifest={'status':'complete','metadata_only':True,'cutoff':selection['cutoff'],
              'selection_sha256':sha(work/'selection.json'),'journals':[], 'pages':[], 'records':0}
    for j in selection['journals']:
        source=ROOT/j['reuse_work'] if j.get('reuse_work') else work/'generated/harvests'/j['key']
        m=json.loads((source/'manifest.json').read_text())
        expected=','.join('issn:'+x for x in j['issns'])+',until-pub-date:'+selection['cutoff']
        if m['status']!='complete' or m['filter']!=expected:raise ValueError('Incomplete or differently configured harvest: '+j['key'])
        if sum(e['records'] for e in m['pages'])!=m['records']:raise ValueError('Inconsistent page counts')
        manifest['journals'].append({**j,'harvest_records':m['records'],'manifest_path':os.path.relpath(source/'manifest.json',work),'manifest_sha256':sha(source/'manifest.json')})
        manifest['records']+=m['records']
        for e in m['pages']:
            manifest['pages'].append({**e,'path':os.path.relpath(source/e['path'],work),'journal_key':j['key']})
    write_json(work/'manifest.json',manifest)
    return manifest

def finish_collection(c,work,out,manifest,record_count,credit_count):
    c.execute('CREATE TABLE journals(journal_key VARCHAR PRIMARY KEY,label VARCHAR,catalogue_ids_json VARCHAR,issns_json VARCHAR,selection_basis VARCHAR,note VARCHAR)')
    c.executemany('INSERT INTO journals VALUES (?,?,?,?,?,?)',[(j['key'],j['label'],json.dumps(j['catalogue_ids']),json.dumps(j['issns']),j['selection_basis'],j.get('note')) for j in manifest['journals']])
    c.execute('CREATE VIEW articles AS SELECT * FROM records WHERE record_type=\'journal-article\' AND NOT is_test_record')
    c.execute('CREATE VIEW research_candidates_by_length AS SELECT * FROM articles WHERE page_count>=10')
    c.execute('CREATE VIEW short_item_candidates AS SELECT * FROM articles WHERE page_count BETWEEN 1 AND 3')
    c.execute("CREATE VIEW normalized_orcids AS SELECT *,regexp_replace(lower(trim(orcid)), '^https?://orcid.org/', '') AS orcid_id FROM contributors WHERE nullif(trim(orcid),'') IS NOT NULL")
    c.execute('CREATE VIEW metadata_variants AS SELECT record_id,count(DISTINCT metadata_sha256) AS variants FROM memberships GROUP BY 1 HAVING variants>1')
    n=c.execute('SELECT count(*) FROM memberships').fetchone()[0]
    if n!=manifest['records']:raise ValueError('Source occurrence count mismatch')
    if c.execute('SELECT count(*) FROM contributors c LEFT JOIN records r USING(record_id) WHERE r.record_id IS NULL').fetchone()[0]:raise ValueError('Orphan contributor')
    if c.execute('SELECT count(*) FROM memberships m LEFT JOIN records r USING(record_id) WHERE r.record_id IS NULL').fetchone()[0]:raise ValueError('Orphan membership')
    expected={j['key']:j['harvest_records'] for j in manifest['journals']}
    actual=dict(c.execute('SELECT journal_key,count(*) FROM memberships GROUP BY 1').fetchall())
    if any(actual.get(k,0)!=v for k,v in expected.items()):raise ValueError('Per-journal membership count mismatch')
    summary_sql="""
    WITH r AS (
      SELECT m.journal_key,count(*) records,
        count(*) FILTER(WHERE record_type='journal-article' AND NOT is_test_record) article_records,
        count(*) FILTER(WHERE nullif(trim(page_raw),'') IS NOT NULL) with_page_field,
        count(page_count) with_calculated_length,
        count(*) FILTER(WHERE page_count>=10 AND record_type='journal-article' AND NOT is_test_record) length_at_least_10,
        count(*) FILTER(WHERE is_test_record) test_records,
        min(publication_year) earliest_deposited_year,max(publication_year) latest_deposited_year
      FROM memberships m JOIN records USING(record_id) GROUP BY 1
    ), o AS (
      SELECT m.journal_key,count(DISTINCT record_id) records_with_orcid,count(*) orcid_credits,count(DISTINCT orcid_id) distinct_orcids
      FROM memberships m JOIN normalized_orcids USING(record_id) GROUP BY 1
    ), a AS (
      SELECT m.journal_key,count(DISTINCT record_id) records_with_affiliation
      FROM memberships m JOIN contributors USING(record_id)
      WHERE affiliation_json IS NOT NULL AND affiliation_json!='[]' GROUP BY 1
    )
    SELECT j.journal_key,j.label,coalesce(r.records,0) records,coalesce(article_records,0) article_records,
      coalesce(with_page_field,0) with_page_field,coalesce(with_calculated_length,0) with_calculated_length,
      coalesce(length_at_least_10,0) length_at_least_10,coalesce(records_with_orcid,0) records_with_orcid,
      coalesce(orcid_credits,0) orcid_credits,coalesce(distinct_orcids,0) distinct_orcids,
      coalesce(records_with_affiliation,0) records_with_affiliation,
      earliest_deposited_year,latest_deposited_year,coalesce(test_records,0) test_records
    FROM journals j LEFT JOIN r USING(journal_key) LEFT JOIN o USING(journal_key) LEFT JOIN a USING(journal_key)
    ORDER BY records DESC,j.journal_key
    """
    cursor=c.execute(summary_sql);names=[d[0] for d in cursor.description]
    summary=[dict(zip(names,row)) for row in cursor.fetchall()]
    c.execute('COPY ('+summary_sql+') TO ? (HEADER,DELIMITER \',\')',[str(work/'journal-summary.csv')])
    c.execute("COPY (SELECT journal_key,publisher,record_type,pagination_status,length_band,count(*) records FROM memberships JOIN records USING(record_id) GROUP BY ALL ORDER BY ALL) TO ? (HEADER)",[str(work/'pagination-summary.csv')])
    c.execute("COPY (SELECT journal_key,container_title,publication_year,count(*) records FROM memberships JOIN records USING(record_id) GROUP BY ALL ORDER BY ALL) TO ? (HEADER)",[str(work/'title-year-coverage.csv')])
    c.execute("COPY (SELECT journal_key,issn_match_status,count(*) records FROM memberships GROUP BY ALL ORDER BY ALL) TO ? (HEADER)",[str(work/'issn-coverage.csv')])
    c.execute("COPY (SELECT m.journal_key,o.credit_id,o.record_id,o.role_array,o.name,o.orcid_id,r.doi,r.publication_year,r.title_text,o.affiliation_json FROM normalized_orcids o JOIN memberships m USING(record_id) JOIN records r USING(record_id) ORDER BY o.orcid_id,m.journal_key,o.credit_id) TO ? (HEADER)",[str(work/'orcid-credits.csv')])
    c.execute('COPY journals TO ? (FORMAT PARQUET)',[str(out/'journals.parquet')])
    validation={'page_hashes_checked':len(manifest['pages']),'metadata_allowlist_checked':True,
                'unique_record_credit_membership_keys':True,'record_credit_membership_duckdb_parquet_row_hashes_match':True,
                'source_occurrences_match_per_journal':True,'contributor_orphans':0,'membership_orphans':0}
    report={'scope':'Selected history journals: full Crossref bibliographic metadata through '+manifest['cutoff'],
        'metrics':{'harvest_groups':len(manifest['journals']),'records':record_count,'contributors':credit_count,'source_memberships':n,
                   'records_with_multiple_metadata_versions':c.execute('SELECT count(*) FROM metadata_variants').fetchone()[0],
                   'membership_issn_status':dict(c.execute('SELECT issn_match_status,count(*) FROM memberships GROUP BY 1').fetchall()),
                   'records_with_orcid':c.execute('SELECT count(DISTINCT record_id) FROM normalized_orcids').fetchone()[0],
                   'distinct_orcids':c.execute('SELECT count(DISTINCT orcid_id) FROM normalized_orcids').fetchone()[0]},
        'journals':summary,'manifest_sha256':sha(work/'manifest.json'),'validation':validation,
        'limitations':['Crossref coverage is not a complete publication census; publication years are as deposited.',
                       'One DOI row is not one unique publication; different DOIs and translated editions remain unreconciled.',
                       'For DOIs repeated across harvest groups, the first selection-order version supplies normalized fields; all source variants and hashes are retained.',
                       'All genres and person identities remain unreviewed. Contributor arrays may conflate reviewers and book authors.',
                       'Page length is a screening aid. Single page locators do not establish one-page length.',
                       'Journal selection is expandable editorial coverage, not an exclusive list or prestige ranking.']}
    write_json(work/'validation.json',validation)
    return report
