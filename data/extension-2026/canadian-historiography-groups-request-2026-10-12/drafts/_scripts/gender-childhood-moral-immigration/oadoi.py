import sys,json
sys.path.insert(0,'.')
from vc import get, oa_abs
for doi in sys.argv[1:]:
    d=get('https://api.openalex.org/works/doi:'+doi+'?mailto=jic823@usask.ca')
    print('##',doi,'|',d.get('display_name'),'|',d.get('publication_year'),'|',(d.get('primary_location') or {}).get('landing_page_url'))
    print('   ',(oa_abs(d.get('abstract_inverted_index')) or 'NO ABSTRACT')[:1400])
