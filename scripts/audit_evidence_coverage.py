"""Offline audit of selection, venue mapping, title history and visible evidence coverage.

Metadata aggregates only; frozen databases are read-only. Missing deposits do not
establish missing publications, and a proposed title-family mapping is not accepted.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import evidence_inputs

from audit_landing_evidence import DATA, ROOT, XR, XS, prepare, run_scenario, selection, sha

PERIODS = [(1900, 1918), (1919, 1939), (1940, 1949), (1950, 1974), (1975, 1999), (2000, 2024)]


def selected_aliases(journals):
    out = defaultdict(list)
    for j in journals:
        for identity in set(j.get('catalogue_ids', []) + [j['journal_key']]):
            out[identity].append(j['journal_key'])
    return out


def start_observations(node):
    """Publication-start observations only: never holdings dates or MARC sentinels."""
    years = set()
    if isinstance(node.get('publication_start'), int):
        years.add(node['publication_start'])
    for b in node.get('bibliographic_evidence', []):
        for d in b.get('date_observations', []):
            if (d.get('usable_exact_year') and d.get('point') == 'start'
                    and d.get('event_type') == 'publication' and isinstance(d.get('year'), int)):
                years.add(d['year'])
    return sorted(years)


def mapping_gaps(edges, aliases, themes):
    return [dict(edge_id=e['id'], catalogue_id=e['source'], target=e['target'], journal_key=k)
            for e in edges for k in aliases.get(e['source'], [])
            if e['target'] not in themes.get(k, set())]


def coverage_state(raw, articles, proxy, mapped):
    if not raw:
        return 'no_deposits'
    if not mapped:
        return 'deposits_unmapped'
    if not articles:
        return 'no_journal_article_records'
    if not proxy:
        return 'articles_below_proxy_or_missing_pagination'
    return 'mapped_proxy_present'


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                        for k, v in row.items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--series', default='v18')
    ap.add_argument('--methods',default='methods-v4')
    ap.add_argument('--mentions',default='mentions-v3')
    ap.add_argument('--out', type=Path, default=DATA / 'audits/coverage-2026-10-10')
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('Output exists; choose a new --out to preserve completed audits.')
    series = DATA / 'generated' / args.series
    review_path = ROOT / 'data/history-journal-profession-review-2026-09-22/journal-review.json'
    graph_path = ROOT / 'historiography-1920-2000.json'
    mentions_path = DATA / 'generated' / args.mentions / 'summary.json'
    mentions = json.loads(mentions_path.read_text())
    old_review_themes = DATA / 'generated' / mentions['inputs']['series'] / 'review_themes.csv'
    registry = ROOT / 'data/person-registry/generated/v9/registry.duckdb'
    inputs = [XR, XS, registry, graph_path, review_path,
              ROOT / 'data/history-journal-profession-review-2026-09-22/selected-journals.json',
              ROOT / 'data/history-journals-supplement-2026-09-26/selection.json',
              DATA / 'practice-crosswalk.csv', DATA / 'practice-hierarchy.csv', DATA / 'approach-folds.csv',
              DATA / 'families-draft.csv', DATA / 'site-evidence.json', DATA / 'site-people.json',
              series / 'summary.json', series / 'journal_themes.csv', series / 'series.csv',
              series / 'review_themes.csv', old_review_themes, mentions_path,
              DATA / 'generated' / args.methods / 'summary.json', DATA / 'generated' / args.methods / 'practitioners.csv',
              ROOT / 'scripts/build_practice_series.py', ROOT / 'scripts/practice_families.py',
              ROOT / 'scripts/audit_landing_evidence.py', ROOT / 'scripts/build_evidence_asset.py',
              ROOT / 'scripts/build_method_signals.py', ROOT / 'scripts/build_review_mentions.py',
              ROOT / 'site/app.js', ROOT / 'site/landing.mjs', Path(__file__).resolve()]
    inputs += evidence_inputs.input_paths()
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    graph = json.loads(graph_path.read_text())
    catalogue = graph['journal_catalogue']
    periodicals = {n['id']: n for n in catalogue['nodes'] if n['entry_kind'] == 'periodical'}
    groups = {n['id']: n for n in graph['nodes'] if n['entry_kind'] == 'group'}
    journals = selection()
    js = {j['journal_key']: j for j in journals}
    aliases = selected_aliases(journals)
    reviews = json.loads(review_path.read_text())
    review_ids = defaultdict(list)
    for r in reviews:
        for i in r.get('catalogue_ids', []):
            review_ids[i].append(r)
    themes = defaultdict(set)
    for row in csv.DictReader((series / 'journal_themes.csv').open()):
        themes[row['journal_key']].add(row['target'])
    db = duckdb.connect()
    defs, crosswalk = prepare(db, series)
    baseline = run_scenario(db, defs['membership'])
    expected = json.loads((series / 'summary.json').read_text())['families']
    assert json.dumps(baseline['views']['all'], sort_keys=True) == json.dumps(expected['views']['all'], sort_keys=True)
    assert baseline['strip'] == expected['strip']
    db.execute('CREATE TEMP VIEW record_pages AS SELECT record_id,page_raw FROM x_records')
    # All counts below deduplicate DOI record IDs, not title contexts.
    db.execute('''CREATE TABLE journal_stats AS
        SELECT m.journal_key,count(DISTINCT r.record_id) AS raw,
        count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article') AS articles,
        min(r.year) AS first_raw,max(r.year) AS last_raw,
        count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND r.page_count IS NULL) AS missing_page_lengths,
        count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND nullif(trim(p.page_raw),'') IS NULL) AS missing_page_fields,
        count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND r.page_count<10) AS under_10
        FROM records r JOIN memberships m USING(record_id) JOIN record_pages p USING(record_id)
        WHERE NOT coalesce(r.is_test_record,false) GROUP BY 1''')
    stat_result = db.execute('SELECT * FROM journal_stats')
    stats = {r[0]: dict(zip([d[0] for d in stat_result.description], r)) for r in stat_result.fetchall()}
    proxy = {k: dict(proxy=n, first_proxy=a, last_proxy=b) for k,n,a,b in db.execute(
        'SELECT journal_key,count(DISTINCT item),min(year),max(year) FROM items GROUP BY 1').fetchall()}
    years = defaultdict(set)
    for k,y in db.execute('SELECT DISTINCT m.journal_key,r.year FROM records r JOIN memberships m USING(record_id) WHERE r.year IS NOT NULL').fetchall():
        years[k].add(y)
    family_for = defaultdict(set)
    for f,t,_ in defs['membership']:
        family_for[t].add(f)
    journal_rows = []
    for k,j in sorted(js.items()):
        s = stats.get(k, dict(raw=0,articles=0,first_raw=None,last_raw=None,missing_page_lengths=0,missing_page_fields=0,under_10=0))
        p = proxy.get(k, dict(proxy=0,first_proxy=None,last_proxy=None))
        starts = sorted({y for i in j.get('catalogue_ids', []) for y in start_observations(periodicals.get(i, {}))})
        internal = [y for y in range(min(years[k]), min(max(years[k]),2024)+1) if y not in years[k]] if years[k] else []
        journal_rows.append(dict(journal_key=k,label=j['label'],catalogue_ids=j.get('catalogue_ids', []),issns=j.get('issns', []),
            **{a:b for a,b in s.items() if a!='journal_key'}, **p, publication_start_observations=starts,
            later_than_all_start_observations=bool(starts and s['first_raw'] and s['first_raw']>max(starts)),
            raw_before_all_start_observations=bool(starts and s['first_raw'] and s['first_raw']<min(starts)),
            internal_years_without_deposits=internal, themes=sorted(themes[k]),
            families=sorted({f for t in themes[k] for f in family_for[t]}),
            coverage_state=coverage_state(s['raw'],s['articles'],p['proxy'],bool(themes[k]))))
    index = {j['journal_key']:j for j in journal_rows}
    gap_rows = mapping_gaps(catalogue['edges'], aliases, themes)
    venue_rows = []
    for e in catalogue['edges']:
        keys = aliases.get(e['source'], [])
        rs = review_ids.get(e['source'], [])
        venue_rows.append(dict(edge_id=e['id'],label=periodicals[e['source']]['label'],catalogue_id=e['source'],
            target=e['target'],selected_keys=keys,missing_mapping_keys=[k for k in keys if e['target'] not in themes[k]],
            community_groups=sorted({r['working_group'] for r in rs}),
            exclusions=sorted({x for r in rs for x in r.get('exclusions', [])}),
            catalogue_issns=periodicals[e['source']].get('issns', []),
            state='selected' if keys else ('screened_out' if rs else 'outside_identified_inventory')))
    issn_keys = defaultdict(set)
    for j in journals:
        for issn in j.get('issns', []):
            issn_keys[issn].add(j['journal_key'])
    catalogue_rows = []
    for i,n in sorted(periodicals.items()):
        rs = review_ids.get(i, [])
        catalogue_rows.append(dict(catalogue_id=i,label=n['label'],issns=n.get('issns', []),selected_keys=aliases.get(i, []),
            selected_issn_overlaps=sorted({k for issn in n.get('issns', []) for k in issn_keys[issn]}),
            community_groups=sorted({r['working_group'] for r in rs}),
            exclusions=sorted({x for r in rs for x in r.get('exclusions', [])}),
            curated_targets=sorted({e['target'] for e in catalogue['edges'] if e['source']==i}),
            state='selected' if aliases.get(i) else ('screened_out' if rs else 'outside_identified_inventory')))
    title_rows = []
    for t in catalogue['title_relationships']:
        a,b = t['predecessor'],t['successor']
        ak,bk = aliases.get(a, []),aliases.get(b, [])
        at,bt = {v for k in ak for v in themes[k]},{v for k in bk for v in themes[k]}
        title_rows.append(dict(relationship_id=t['id'],predecessor=periodicals[a]['label'],successor=periodicals[b]['label'],
            changed_in=t.get('changed_in',t.get('merged_in')),predecessor_keys=ak,successor_keys=bk,
            predecessor_themes=sorted(at),successor_themes=sorted(bt),
            predecessor_proxy_context_sum=sum(index[k]['proxy'] for k in ak),
            state='selection_gap' if not ak or not bk else ('mapping_difference' if at!=bt else 'same_mapping'),
            source_ids=t['source_ids'],evidence_note=t['evidence_note']))
    field_start=int(re.search(r'recordBars\(e\.journal_items_by_5yr, (\d+)',(ROOT/'site/app.js').read_text()).group(1))
    mobile_limit=re.search(r'recordShares\(f, view\)\.filter\(b => b\.bin >= (\d+)\)',(ROOT/'site/landing.mjs').read_text())
    mobile_start=int(mobile_limit.group(1)) if mobile_limit else 1900
    family_rows = []
    for f in defs['families']:
        keys = sorted(k for k in js if any(f['label'] in family_for[t] for t in themes[k]))
        db.execute('CREATE OR REPLACE TABLE audit_keys AS SELECT unnest(?::VARCHAR[]) AS journal_key',[keys])
        raw = db.execute('''SELECT min(r.year),min(r.year) FILTER(WHERE r.record_type='journal-article'),count(DISTINCT r.record_id),
            count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND r.page_count IS NULL)
            FROM records r JOIN memberships m USING(record_id) JOIN audit_keys k USING(journal_key)
            WHERE r.year BETWEEN 1900 AND 2024 AND NOT coalesce(r.is_test_record,false)''').fetchone()
        p = db.execute('SELECT min(year),count(DISTINCT item) FROM items JOIN audit_keys USING(journal_key) WHERE year BETWEEN 1900 AND 2024').fetchone()
        bins = expected['views']['all']['families'].get(f['label'], {})
        row = dict(family=f['label'],mapped_title_contexts=len(keys),zero_deposit_contexts=sum(not index[k]['raw'] for k in keys),
            first_raw_1900_2024=raw[0],first_article_1900_2024=raw[1],first_proxy_1900_2024=p[0],
            raw_1900_2024=raw[2],missing_article_page_lengths_1900_2024=raw[3],proxy_1900_2024=p[1],
            first_positive_published_bin=min(map(int,bins)) if bins else None,
            proxy_before_1950_hidden_on_mobile=sum(n for b,n in bins.items() if int(b)<min(mobile_start,1950)))
        for a,b in PERIODS:
            row[f'proxy_{a}_{b}'] = db.execute('SELECT count(DISTINCT item) FROM items JOIN audit_keys USING(journal_key) WHERE year BETWEEN ? AND ?',[a,b]).fetchone()[0]
        family_rows.append(row)
    evidence = json.loads((DATA / 'site-evidence.json').read_text())
    entry_rows = []
    for i,n in sorted(groups.items()):
        e = evidence['entries'].get(i,{})
        keys = sorted(k for k in js if i in themes[k])
        bins = e.get('journal_items_by_5yr',{})
        entry_rows.append(dict(entry=i,label=n['label'],status=e.get('status'),mapped_contexts=len(keys),
            zero_deposit_contexts=sum(not index[k]['raw'] for k in keys),
            journal_items_displayed=e.get('journal_items_total',0),reviews_displayed=e.get('reviews_total',0),
            first_journal_bin=min(map(int,bins)) if bins else None,
            items_before_1950_hidden_in_field_chart=sum(v for k,v in bins.items() if int(k)<min(field_start,1950)),
            practised_within=e.get('practised_within',[]),method_signal='method' in e,
            curated_unselected_venues=[v['label'] for v in venue_rows if v['target']==i and not v['selected_keys']],
            curated_mapping_gaps=[v['label'] for v in venue_rows if v['target']==i and v['missing_mapping_keys']]))
    # Check actual changed review mappings before calling mentions-v2 stale.
    def review_pairs(path):
        return {(r['source'],r['item'],r['target']) for r in csv.DictReader(path.open())}
    old_pairs,new_pairs = review_pairs(old_review_themes),review_pairs(series/'review_themes.csv')
    db.execute(f"ATTACH '{str(registry).replace(chr(39),chr(39)*2)}' AS rg (READ_ONLY)")
    method_ids = {r['individual_id'] for r in csv.DictReader((DATA/'generated'/args.methods/'practitioners.csv').open())}
    db.execute('CREATE TABLE method_ids AS SELECT unnest(?::VARCHAR[]) AS individual_id',[sorted(method_ids)])
    method_identity = [dict(corpus=c,status=s,occurrences=n) for c,s,n in db.execute('''SELECT r.corpus,r.status,count(*)
        FROM rg.occurrence_resolution r JOIN method_ids USING(individual_id)
        WHERE r.corpus IN ('atlas','crossref') GROUP BY 1,2 ORDER BY 1,2''').fetchall()]
    duplicate_contexts = db.execute('''SELECT a.journal_key,b.journal_key,count(*) FROM memberships a JOIN memberships b
        ON a.record_id=b.record_id AND a.journal_key<b.journal_key GROUP BY 1,2 ORDER BY 3 DESC''').fetchall()
    drilldowns = []
    for key in ['initial:annales_1929','initial:history_theory','initial:labour_le_travail',
                'journal_e6929b124f9137bc','journal_a60d063c840e1fcd','journal_f33abcd156e85bc9',
                'journal_02eec3b72cd5349d','journal_97cc033e49a4f22b',
                'recovery:military_foundation','recovery:military_institute','recovery:military_affairs',
                'journal_409717ea150ea375','journal_b37c47d6d6bf8912']:
        for a,b in PERIODS:
            values = db.execute('''SELECT count(DISTINCT r.record_id),
                count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article'),
                count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND r.page_count IS NULL),
                count(DISTINCT r.record_id) FILTER(WHERE r.record_type='journal-article' AND nullif(trim(p.page_raw),'') IS NULL),
                count(DISTINCT i.item) FROM records r JOIN memberships m USING(record_id)
                JOIN record_pages p USING(record_id) LEFT JOIN items i ON i.item=r.record_id AND i.journal_key=m.journal_key
                WHERE m.journal_key=? AND r.year BETWEEN ? AND ? AND NOT coalesce(r.is_test_record,false)''',[key,a,b]).fetchone()
            drilldowns.append(dict(journal_key=key,label=js[key]['label'],period=f'{a}-{b}',
                **dict(zip(['raw','articles','missing_page_lengths','missing_page_fields','proxy'],values))))
    result = dict(schema_version='1.0',inputs=before,graph_revision=graph['revision_history'][-1]['version'],
        series=args.series,scope=dict(families=len(family_rows),entries=len(entry_rows),selected_contexts=len(js),
            community_screen=len(reviews),catalogue_periodicals=len(periodicals)),
        reconciles_published_all_journal_bins=True,venue_mapping_gaps=gap_rows,
        venue_edges_outside_selection=sum(not v['selected_keys'] for v in venue_rows),
        distinct_venues_outside_selection=len({v['catalogue_id'] for v in venue_rows if not v['selected_keys']}),
        selected_states={s:sum(j['coverage_state']==s for j in journal_rows) for s in sorted({j['coverage_state'] for j in journal_rows})},
        unmapped_contexts_with_proxy=sum(j['coverage_state']=='deposits_unmapped' and j['proxy']>0 for j in journal_rows),
        title_history_states={s:sum(t['state']==s for t in title_rows) for s in sorted({t['state'] for t in title_rows})},
        contexts_later_than_all_start_observations=sum(j['later_than_all_start_observations'] for j in journal_rows),
        contexts_with_internal_deposit_gaps=sum(bool(j['internal_years_without_deposits']) for j in journal_rows),
        entries_with_pre1950_items_hidden=sum(bool(e['items_before_1950_hidden_in_field_chart']) for e in entry_rows),
        established_title_contexts=baseline['established_journals'],
        overlapping_title_contexts=[dict(first=a,second=b,shared_records=n) for a,b,n in duplicate_contexts],
        mentions_mapping_comparison=dict(referenced_series=mentions['inputs']['series'],current_series=args.series,
            old_pairs=len(old_pairs),current_pairs=len(new_pairs),removed=len(old_pairs-new_pairs),added=len(new_pairs-old_pairs)),
        method_identity_occurrences=method_identity,
        method_summary_has_input_pins='inputs' in json.loads((DATA/'generated'/args.methods/'summary.json').read_text()),
        limitations=['No new harvesting, identity acceptance, crosswalk acceptance or graph changes.',
            'DOI records are not necessarily distinct publications; title contexts are not distinct journals.',
            'No deposits, missing pagination, unmapped deposits and editorial exclusions are different states.',
            'Library date observations can conflict or describe a title phase; gaps require source review.',
            'Title continuation or merger does not automatically justify an identical field mapping.',
            'Method identity counts describe occurrence tiers among pilot practitioner IDs, not distinct people tiers.'])
    after = {str(p.relative_to(ROOT)):sha(p) for p in inputs}
    if before != after:
        raise ValueError('Inputs changed during the audit')
    args.out.mkdir(parents=True)
    for name,rows in [('journal-coverage.csv',journal_rows),('catalogue-selection.csv',catalogue_rows),
                     ('venue-coverage.csv',venue_rows),('title-history.csv',title_rows),
                     ('family-coverage.csv',family_rows),('entry-coverage.csv',entry_rows),('targeted-periods.csv',drilldowns)]:
        write_csv(args.out/name,rows)
    result['outputs'] = {p.name:sha(p) for p in sorted(args.out.glob('*.csv'))}
    (args.out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','outputs','limitations','method_identity_occurrences')},indent=2))


if __name__ == '__main__':
    main()
