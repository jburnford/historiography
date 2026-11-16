"""Map AHA US institutions (with unheld records) to OpenAlex institution ids and their repository sources.
Writes /mnt/e/.../institutions.json; eyeball-checked list in institutions.csv."""
import collections, csv
from common import *

FIX = {'Graduate Center, CUNY': 'CUNY Graduate Center', 'Rutgers': 'Rutgers University-New Brunswick',
       'Univ. of Texas, Austin': 'University of Texas at Austin', 'Univ. of Wisconsin, Madison': 'University of Wisconsin-Madison',
       'Univ. of North Carolina, Chapel Hill': 'University of North Carolina at Chapel Hill',
       'Univ. of Illinois, Urbana-Champaign': 'University of Illinois Urbana-Champaign',
       'Univ. of Illinois, Chicago': 'University of Illinois Chicago', 'Washington Univ.': 'Washington University in St. Louis',
       'Univ. of Maryland': 'University of Maryland, College Park', 'Univ. of Massachusetts': 'University of Massachusetts Amherst',
       'Loyola Univ.': 'Loyola University Chicago', 'Univ. of Nevada': 'University of Nevada, Reno',
       'Univ. of Hawaii': 'University of Hawaii at Manoa', 'Univ. of Colorado': 'University of Colorado Boulder',
       'Univ. of Nebraska': 'University of Nebraska-Lincoln', 'Univ. of Missouri': 'University of Missouri',
       'Penn State Univ.': 'Pennsylvania State University', 'Univ. of Pittsburgh': 'University of Pittsburgh',
       'Saint John\'s Univ.': "St. John's University", 'Miami Univ.': 'Miami University', 'Univ. of Miami': 'University of Miami',
       'George Peabody Coll.': 'Vanderbilt University', 'Radcliffe Coll.': 'Harvard University',
       'Univ. of Southern Mississippi': 'University of Southern Mississippi', 'Univ. of Louisiana': 'University of Louisiana at Lafayette',
       'Bryn Mawr Coll.': 'Bryn Mawr College', 'Univ. of Washington': 'University of Washington', 'Washington State Univ.': 'Washington State University',
       'Univ. of Akron': 'University of Akron', 'Ohio Univ.': 'Ohio University', 'Univ. of Toledo': 'University of Toledo'}


def search_name(name):
    if name in FIX:
        return FIX[name]
    s = name.replace('Univ.', 'University').replace('Coll.', 'College').replace('Inst.', 'Institute')
    s = s.replace(', State University of New York', '')
    m = re.match(r'University of California, (.*)', s)
    if m:
        return 'University of California, ' + m.group(1)
    return s


def main():
    u, _ = universe()
    n = collections.Counter(r['inst_name'] for r in u)
    out = {}
    for name, cnt in n.most_common():
        if cnt < 5:
            continue
        q = search_name(name)
        d = openalex('institutions', {'search': q, 'filter': 'country_code:US', 'per-page': 5,
                                      'select': 'id,display_name,ror,works_count'})
        res = d.get('results') or []
        best = res[0] if res else None
        srcs = []
        if best:
            sd = openalex('sources', {'filter': f"type:repository,host_organization_lineage:{best['id'].rsplit('/',1)[-1]}",
                                      'per-page': 50, 'select': 'id,display_name,works_count,homepage_url'})
            srcs = sd.get('results') or []
        out[name] = {'unheld': cnt, 'query': q, 'openalex': best and best['id'].rsplit('/', 1)[-1],
                     'oa_name': best and best['display_name'],
                     'sources': [{'id': s['id'].rsplit('/', 1)[-1], 'name': s['display_name'], 'works': s['works_count'],
                                  'home': s.get('homepage_url')} for s in srcs]}
    (CACHE / 'institutions.json').write_text(json.dumps(out, indent=1))
    with (OUT / 'institutions.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['aha_institution', 'unheld_aha', 'openalex_institution', 'openalex_name', 'repository_sources'])
        for k, v in out.items():
            w.writerow([k, v['unheld'], v['openalex'], v['oa_name'], ' | '.join(f"{s['id']} {s['name']} ({s['works']})" for s in v['sources'])])


if __name__ == '__main__':
    main()
