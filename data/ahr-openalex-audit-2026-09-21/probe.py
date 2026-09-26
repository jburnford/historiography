"""Bounded AHR metadata audit; cache public responses, never credentials."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from openalex_ingest import Client, load_api_key, write_json

WORK = Path(__file__).resolve().parent
client = Client(load_api_key(), WORK / 'cache', max_requests=65)
base = 'primary_location.source.id:S197437610,to_publication_date:2026-09-21'
fields = 'id,doi,title,publication_year,publication_date,type,type_crossref,authorships,biblio,primary_location,open_access,referenced_works,abstract_inverted_index'

def fetch(name, params, endpoint='works'):
    page = client.get(params, endpoint)
    write_json(WORK / (name + '.json'), page)
    print(name, json.dumps(page['meta']), flush=True)
    return page

def grouped(name, filters, group):
    cursor = '*'; pages = []
    while cursor:
        page = fetch(name + '-' + str(len(pages) + 1), {'filter': filters, 'group_by': group, 'per_page': 200, 'cursor': cursor})
        pages.append(page)
        cursor = page['meta']['next_cursor']
    write_json(WORK / (name + '.json'), pages)

def main():
    fetch('source', {'filter': 'issn:0002-8762', 'select': 'id,display_name,issn_l,issn,works_count,counts_by_year', 'per_page': 5}, 'sources')
    grouped('types', base, 'type')
    grouped('all-years', base, 'publication_year')
    reviews = base + ',type:book-review'
    grouped('book-review-years', reviews, 'publication_year')
    for name, extra in [('total',''), ('doi', ',has_doi:true'), ('authors', ',authors_count:>0'),
                        ('institutions', ',institutions_distinct_count:>0'), ('references', ',referenced_works_count:>0'),
                        ('abstracts', ',has_abstract:true'), ('open-access', ',open_access.is_oa:true')]:
        fetch('book-review-count-' + name, {'filter': reviews + extra, 'per_page': 1, 'select': 'id'})
    fetch('book-review-sample', {'filter': reviews, 'sample': 200, 'seed': 21092026, 'per_page': 200, 'select': fields})
    fetch('article-sample', {'filter': base + ',type:article', 'sample': 100, 'seed': 21092026, 'per_page': 100, 'select': fields})
    for year in [1925,1950,1975,2000,2020,2025]:
        fetch('year-' + str(year), {'filter': base + ',publication_year:' + str(year), 'sample': 30, 'seed': 21092026, 'per_page': 30, 'select': fields})
    for name, extra in [('color-blind', ',biblio.volume:98,biblio.issue:5,biblio.first_page:1669'),
                        ('kagan', ',biblio.volume:71,biblio.issue:2,biblio.first_page:522')]:
        fetch('duplicate-check-' + name, {'filter':base + extra, 'per_page':100, 'select':fields})
    dois = ['10.1093/ahr/rhae494','10.1093/ahr/rhae501','10.1093/ahr/rhae637',
            '10.1093/ahr/rhae504','10.1093/ahr/rhae508','10.1093/ahr/rhae505',
            '10.1093/ahr/rhae511','10.1093/ahr/rhae509','10.1093/ahr/rhae499',
            '10.1093/ahr/rhae516']
    fetch('publisher-reviewed-2025', {'filter':'doi:'+'|'.join(dois),'per_page':100,'select':fields})
    fetch('issue-130-1', {'filter':base+',biblio.volume:130,biblio.issue:1','per_page':200,'select':fields})
    write_json(WORK/'request-summary.json', {'network_requests':client.requests,'cache_hits':client.cache_hits})

if __name__ == '__main__':
    main()
