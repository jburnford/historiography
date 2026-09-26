"""Offline field coverage and DOI-matched comparison; no review text."""
import csv
import json
from collections import Counter
from pathlib import Path

WORK=Path(__file__).resolve().parent
OA=WORK.parent/'ahr-openalex-audit-2026-09-21'

def read(name):
    return json.loads((WORK/(name+'.json')).read_text())

def field_stats(records):
    checks={
        'title':lambda r:r.get('title'),
        'author':lambda r:r.get('author'),
        'affiliation':lambda r:any(a.get('affiliation') for a in r.get('author',[])),
        'orcid':lambda r:any(a.get('ORCID') for a in r.get('author',[])),
        'volume_issue_page':lambda r:all(r.get(k) for k in ['volume','issue','page']),
        'isbn':lambda r:r.get('ISBN'),
        'relation':lambda r:r.get('relation'),
        'subject':lambda r:r.get('subject'),
        'title_italics_markup':lambda r:'<i>' in ' '.join(r.get('title',[])),
    }
    return {'n':len(records),'fields_present':{k:sum(bool(fn(r)) for r in records) for k,fn in checks.items()},
            'publishers':dict(Counter(r.get('publisher') for r in records)),
            'types':dict(Counter(r.get('type') for r in records))}

def main():
    by_doi={}
    for p in sorted(WORK.glob('doi-batch-*.json')):
        for r in json.loads(p.read_text())['items']:
            if r['DOI'].lower() in by_doi:raise ValueError('Duplicate returned DOI')
            by_doi[r['DOI'].lower()]=r
    requested=read('comparison-dois')
    comparisons={};review_rows=[]
    for cohort in ['book-review-sample','article-sample','publisher-reviewed-2025']:
        original=json.loads((OA/(cohort+'.json')).read_text())['results']
        matched=[];affiliations=Counter()
        for o in original:
            doi=o['doi'].removeprefix('https://doi.org/').lower();r=by_doi.get(doi)
            if not r:continue
            matched.append(r)
            oa_aff=[v for a in o.get('authorships',[]) for v in a.get('raw_affiliation_strings',[])]
            cr_aff=[a.get('name','') for p in r.get('author',[]) for a in p.get('affiliation',[])]
            affiliations['both' if oa_aff and cr_aff else 'openalex_only' if oa_aff else 'crossref_only' if cr_aff else 'neither']+=1
            review_rows.append({'cohort':cohort,'doi':doi,'openalex_id':o['id'],
                'crossref_publisher':r.get('publisher'),'crossref_member':r.get('member'),
                'crossref_type':r.get('type'),'openalex_type':o.get('type'),
                'title':' | '.join(r.get('title',[])),
                'crossref_authors':' | '.join(' '.join(filter(None,[a.get('given'),a.get('family')])) for a in r.get('author',[])),
                'crossref_affiliations':' | '.join(cr_aff),'openalex_raw_affiliations':' | '.join(oa_aff),
                'crossref_orcids':' | '.join(a['ORCID'] for a in r.get('author',[]) if a.get('ORCID'))})
        comparisons[cohort]={**field_stats(matched),'requested':len(original),'affiliation_comparison':dict(affiliations)}
    coverage=read('union-coverage')
    summary={'checked_on':'2026-09-21','scope':'Either AHR ISSN; publication dates through 2026-09-21; bibliographic metadata only.',
             'total_records':coverage['total_results'],'facets':coverage['facets'],
             'counts':{name:read('union-count-'+name)['total_results'] for name in ['affiliation','orcid','relations','ror','oup','oup-articles','oup-affiliation']},
             'comparison_dois_requested':len(requested),'comparison_dois_found':len(by_doi),
             'missing_dois':sorted(set(requested)-set(by_doi)),'comparisons':comparisons,
             'crossref_random_sample':field_stats(read('crossref-sample')['items']),
             'metadata_only':True,'review_classification':'Not supplied by Crossref type for the confirmed reviews.',
             'caveat':'Counts include research articles, duplicate representations, issues and one test record; not unique review counts.'}
    assert sum(coverage['facets']['publisher-name']['values'].values())==coverage['total_results']
    assert sum(coverage['facets']['type-name']['values'].values())==coverage['total_results']
    for p in WORK.glob('*.json'):
        d=json.loads(p.read_text())
        if isinstance(d,dict):
            for r in d.get('items',[]):
                assert not {'abstract','description','body','full_text','reference'} & set(r),p
    (WORK/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with (WORK/'doi-comparison.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(review_rows[0]));writer.writeheader();writer.writerows(review_rows)
    with (WORK/'coverage-by-year.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['publication_year','crossref_records_either_issn'])
        for year,count in sorted(coverage['facets']['published']['values'].items(),key=lambda t:int(t[0])):writer.writerow([year,count])
    print(json.dumps({k:v for k,v in summary.items() if k!='facets'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
