"""Offline sensitivity audit of the landing's journal comparison, with DOI-level counting.

Writes metadata/aggregates only. Source catalogues are opened read-only. A page-length
threshold is a proxy, never a genre decision; title flags are screening clues only.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import duckdb

from practice_families import family_series, load_families

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/evidence-layer'
XR = ROOT / 'data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb'
XS = ROOT / 'data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb'
BORN_DIGITAL = 'journal_supplement_journal_of_digital_history'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def literal(path):
    return "'" + str(path).replace("'", "''") + "'"


def selection():
    return (json.loads((ROOT / 'data/history-journal-profession-review-2026-09-22/selected-journals.json').read_text())['journals']
            + json.loads((ROOT / 'data/history-journals-supplement-2026-09-26/selection.json').read_text())['journals'])


def prepare(db, series):
    db.execute(f'ATTACH {literal(XR)} AS xr (READ_ONLY)')
    db.execute(f'ATTACH {literal(XS)} AS xs (READ_ONLY)')
    db.execute('''CREATE TABLE records AS SELECT * FROM
        (SELECT record_id, doi, title_text, record_type, publication_year AS year,
                page_count, book_citation_title_hint, is_test_record FROM xr.records
         UNION ALL SELECT record_id, doi, title_text, record_type, publication_year,
                page_count, book_citation_title_hint, is_test_record FROM xs.records)
        QUALIFY row_number() OVER (PARTITION BY record_id ORDER BY doi)=1''')
    db.execute('CREATE TABLE memberships AS SELECT DISTINCT record_id, journal_key FROM '
               '(SELECT record_id,journal_key FROM xr.memberships UNION ALL SELECT record_id,journal_key FROM xs.memberships)')
    db.execute(f'CREATE TABLE themes AS SELECT * FROM read_csv({literal(series / "journal_themes.csv")},all_varchar=true)')
    db.execute('CREATE TABLE subject_themes (journal_key VARCHAR,target VARCHAR)')
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    subjects = {n['id']: n['label'] for n in graph['journal_catalogue']['nodes'] if n.get('entry_kind') == 'publication_subject'}
    rows = list(csv.DictReader((DATA / 'practice-crosswalk.csv').open()))
    subjects_cw = {}
    for r in rows:
        if r['source'] == 'journal' and r['axis'] == 'theme' and r['status'] != 'rejected':
            subjects_cw.setdefault(r['source_label'], set()).add(r['target'])
    pairs = sorted({(j['journal_key'], t) for j in selection() for c in j.get('subject_classifications', [])
                    for t in subjects_cw.get(subjects.get(c['subject_id'], c['subject_id']), set())})
    db.executemany('INSERT INTO subject_themes VALUES (?,?)', pairs)
    groups = {n['id'] for n in graph['nodes'] if n.get('entry_kind') == 'group'}
    defs = load_families(DATA / 'families-draft.csv', groups, {r['target'] for r in rows})
    return defs, rows


def run_scenario(db, membership, minimum=10, theme_table='themes', screen_titles=False):
    # Same exception as the production series: JDH has article numbers, not page ranges.
    db.execute('''CREATE OR REPLACE TABLE items AS
        SELECT DISTINCT 'journal' AS source,r.record_id AS item,m.journal_key AS source_label,
               r.year,'research_proxy' AS kind,m.journal_key
        FROM records r JOIN memberships m USING(record_id)
        WHERE r.record_type='journal-article' AND NOT coalesce(r.is_test_record,false)
          AND (r.page_count >= ? OR m.journal_key=?)
          AND (NOT ? OR NOT coalesce(r.book_citation_title_hint,false))''', [minimum, BORN_DIGITAL, screen_titles])
    db.execute(f'''CREATE OR REPLACE TABLE mapped AS
        SELECT DISTINCT i.source,i.item,'theme' AS axis,t.target,'direct' AS status
        FROM items i JOIN {theme_table} t USING(journal_key)''')
    return family_series(db, membership)


def comparisons(scenarios):
    out = []
    for name, result in scenarios.items():
        view = result['views']['all']
        for family in sorted({f for x in scenarios.values() for f in x['views']['all']['families']}):
            bins = view['families'].get(family, {})
            window = lambda a,b: sum(n for y,n in bins.items() if a <= y <= b) / max(1, sum(n for y,n in view['totals'].items() if a <= y <= b))
            old, new = window(1950,1970), window(2000,2020)
            out.append(dict(scenario=name, family=family, share_1950_1974=round(old,6),
                            share_2000_2024=round(new,6), change_percentage_points=round(100*(new-old),4)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--series', default='v17')
    ap.add_argument('--out', type=Path, default=DATA / 'audits/landing-2026-10-10')
    args = ap.parse_args()
    if (args.out / 'summary.json').exists():
        raise SystemExit('Completed audit exists; choose a new --out.')
    series = DATA / 'generated' / args.series
    paths = [XR, XS, series / 'summary.json', series / 'journal_themes.csv', DATA / 'practice-crosswalk.csv',
             DATA / 'families-draft.csv', ROOT / 'historiography-1920-2000.json',
             ROOT / 'data/history-journal-profession-review-2026-09-22/selected-journals.json',
             ROOT / 'data/history-journals-supplement-2026-09-26/selection.json',
             ROOT / 'scripts/practice_families.py', Path(__file__).resolve()]
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    db = duckdb.connect()
    defs, rows = prepare(db, series)
    scenarios = {}
    for name, threshold, theme_table, screen in [('pages_10',10,'themes',False),('pages_8',8,'themes',False),
        ('pages_12',12,'themes',False),('pages_15',15,'themes',False),
        ('subject_mapping_only',10,'subject_themes',False),('screen_book_title_hints',10,'themes',True)]:
        scenarios[name] = run_scenario(db, defs['membership'], threshold, theme_table, screen)
    expected = json.loads((series / 'summary.json').read_text())['families']
    # Every family/bin and the weighted headline must reconcile, not only a grand total.
    baseline = scenarios['pages_10']
    assert json.dumps(baseline['views']['all'],sort_keys=True) == json.dumps(expected['views']['all'],sort_keys=True), 'Published all-journal series does not reconcile'
    assert baseline['strip'] == expected['strip'], 'Published strip does not reconcile'
    run_scenario(db, defs['membership'])
    impacts = db.execute('''SELECT t.target,count(DISTINCT i.item) AS items FROM items i
        JOIN themes t USING(journal_key) WHERE i.year BETWEEN 2000 AND 2024 GROUP BY 1 ORDER BY 2 DESC,1''').fetchall()
    missing_pages = db.execute('''SELECT CASE WHEN year<1950 THEN '1900-1949' WHEN year<2000 THEN '1950-1999'
        ELSE '2000-2024' END AS period,count(*),count(*) FILTER(WHERE page_count IS NULL)
        FROM records WHERE year BETWEEN 1900 AND 2024 AND record_type='journal-article'
        AND NOT coalesce(is_test_record,false) GROUP BY 1 ORDER BY 1''').fetchall()
    # Deterministic stratified screen: six records per period/page band, DOI links only.
    sample = db.execute('''WITH s AS (SELECT doi,title_text,year,page_count,book_citation_title_hint,
        CASE WHEN year<1950 THEN '1900-1949' WHEN year<2000 THEN '1950-1999' ELSE '2000-2024' END AS period,
        CASE WHEN page_count IS NULL THEN 'missing' WHEN page_count<10 THEN 'under_10' ELSE 'at_least_10' END AS band,
        row_number() OVER(PARTITION BY period,band ORDER BY md5(doi)) AS n FROM records
        WHERE year BETWEEN 1900 AND 2024 AND record_type='journal-article' AND NOT coalesce(is_test_record,false))
        SELECT doi,title_text,year,page_count,book_citation_title_hint,period,band FROM s WHERE n<=6 ORDER BY period,band,doi''').fetchall()
    after = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    if before != after:
        raise ValueError('Audit inputs changed during the run')
    args.out.mkdir(parents=True,exist_ok=True)
    trend = comparisons(scenarios)
    for name, records in [('sensitivity.csv',trend),('classification-priorities.csv',
            [dict(target=t,items_2000_2024=n,statuses=';'.join(sorted({r['status'] for r in rows if r['target']==t}))) for t,n in impacts]),
            ('genre-screen.csv',[dict(zip(['doi','title','year','pages','book_title_hint','period','page_band'],r),
                source_url='https://doi.org/'+r[0],genre_decision='unreviewed') for r in sample])]:
        with (args.out / name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    summary = dict(schema_version='1.0',inputs=before,reconciles_published_all_journal_bins=True,
        mapping_status_counts={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
        missing_pagination=[dict(period=p,items=n,missing=m,share=round(m/n,4)) for p,n,m in missing_pages],
        scenarios={name:dict(items=x['strip']['items'],unclaimed_share=round(x['strip']['unclaimed']/max(1,x['strip']['items']),4),
            established_journals=x['established_journals']) for name,x in scenarios.items()},
        sensitivity=trend,genre_sample_items=len(sample),genre_sample_status='metadata_screen_only',
        caveats=['Article length and book-title flags are proxies, not verified genres.',
                 'Subject-only mapping is a sensitivity scenario, not an accepted crosswalk correction.',
                 'Counts are distinct DOI records; they are not necessarily distinct publications.',
                 'Family shares overlap. Established-journal membership can change with the threshold.'])
    (args.out / 'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ['reconciles_published_all_journal_bins','scenarios','missing_pagination']},indent=2))


if __name__ == '__main__':
    main()
