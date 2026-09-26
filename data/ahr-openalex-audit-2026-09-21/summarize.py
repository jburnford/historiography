"""Reproduce coverage statistics from the saved OpenAlex responses, offline."""
import csv
import json
from collections import Counter
from pathlib import Path

WORK = Path(__file__).resolve().parent

def read(name):
    return json.loads((WORK / (name + '.json')).read_text())

def groups(name):
    return {r['key'].rsplit('/', 1)[-1]: r['count'] for p in read(name) for r in p['group_by']}

def sample_stats(name):
    records = read(name)['results']
    authors = lambda r: r.get('authorships') or []
    predicates = {
        'doi': lambda r: r.get('doi'),
        'title': lambda r: r.get('title'),
        'raw_name': lambda r: any(a.get('raw_author_name') for a in authors(r)),
        'any_author_id': lambda r: any(a['author'].get('id') for a in authors(r)),
        'any_orcid': lambda r: any(a['author'].get('orcid') for a in authors(r)),
        'raw_affiliation': lambda r: any(a.get('raw_affiliation_strings') for a in authors(r)),
        'institution': lambda r: any(a.get('institutions') for a in authors(r)),
        'volume_issue_first_page': lambda r: all(r['biblio'].get(k) for k in ['volume','issue','first_page']),
        'abstract_field': lambda r: r.get('abstract_inverted_index'),
        'references': lambda r: r.get('referenced_works'),
    }
    return {'n': len(records), 'present': {k:sum(bool(f(r)) for r in records) for k,f in predicates.items()},
            'authorship_counts': dict(Counter(len(authors(r)) for r in records))}

def main():
    all_years, review_years = groups('all-years'), groups('book-review-years')
    counts = {key:read('book-review-count-'+key)['meta']['count'] for key in
              ['total','doi','authors','institutions','references','abstracts','open-access']}
    publisher = read('publisher-reviewed-2025')['results']
    # Nine selected entries explicitly confirmed in the OUP issue's featured
    # reviews / reviews sections. The tenth API lookup is supplementary only.
    publisher = [r for r in publisher if not r['doi'].endswith('/rhae516')]
    output = {'scope':{'source_id':'S197437610','issns':['0002-8762','1937-5239'],
                       'through_date':'2026-09-21','location_filter':'primary_location.source.id',
                       'year_min':min(map(int,all_years)),'year_max':max(map(int,all_years))},
              'indexed_records':sum(all_years.values()),'types':groups('types'),
              'book_review_field_counts':counts,
              'samples':{name:sample_stats(name) for name in ['book-review-sample','article-sample']},
              'publisher_selected_reviews':{'count':len(publisher),'types':dict(Counter(r['type'] for r in publisher)),
                   'source':'https://academic.oup.com/ahr/issue/130/1','dois':[r['doi'] for r in publisher]},
              'limitations':['Indexed records are not deduplicated review counts.',
                             'Book-review type misses confirmed reviews, particularly recent ones.',
                             'Authorships can mix reviewer and reviewed author; IDs are not verified identities.',
                             'Abstract-field presence does not establish an abstract or review-text availability.',
                             'Institution mappings can be wrong; preserve raw affiliation text.',
                             'No publisher-archive completeness denominator was measured.']}
    assert sum(output['types'].values()) == output['indexed_records']
    assert sum(review_years.values()) == counts['total']
    with (WORK/'coverage-by-year.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['publication_year','all_indexed_records','book_review_label'])
        for year in sorted(all_years,key=int):writer.writerow([year,all_years[year],review_years.get(year,0)])
    (WORK/'summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
