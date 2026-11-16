"""Route 1: OpenAlex dissertations per AHA institution (2026-11-16).

For every US AHA institution with unheld records, two cursor-paged OpenAlex listings (project key, cached on E:):
  A  type:dissertation whose repository location is hosted by the institution (source host-organization lineage)
  B  type:dissertation with an author affiliated to the institution and an open-access copy
Both restricted to primary-topic fields Arts & Humanities (12), Social Sciences (33) and Economics (20) where
the full listing is large (> FULL_LIMIT works); small listings are taken whole. Output: one JSONL of compact
works per institution in /mnt/e/us-theses-resurvey-2026-11-16/works/. No repository is contacted."""
import sys
from common import *

FIX = {'Univ. of Arkansas': 'I78715868', 'Univ. of Alabama': 'I17301866', 'Ohio Univ.': 'I4210106879',
       'Rutgers': 'I102322142', 'Univ. of Connecticut, Storrs': 'I140172145', 'Univ. of Maine, Orono': 'I7947594',
       'Washington State Univ., Pullman': 'I72951846', 'Univ. of New Hampshire, Durham': 'I161057412',
       'Montana State Univ., Bozeman': 'I23732399', 'Miami Univ., Ohio': 'I83328450', "Saint John's Univ., NY": 'I142823887',
       'Univ. of South Florida, Tampa': 'I2613432', 'Drew Univ.': 'I177880774',
       'New School, Committee on Historical Studies': 'I102179633'}
FULL_LIMIT = 6000
FIELDS = 'primary_topic.field.id:12|33|20'
SELECT = 'id,display_name,publication_year,authorships,locations,doi,primary_topic'
WORKS = CACHE / 'works'


def inst_ids():
    inst = json.loads((CACHE / 'institutions.json').read_text())
    out = {}
    for name, v in inst.items():
        i = FIX.get(name, v['openalex'])
        if i:
            out[name] = i
    return out


def compact(w):
    return {'id': w['id'].rsplit('/', 1)[-1], 'title': w.get('display_name'), 'year': w.get('publication_year'),
            'doi': w.get('doi'),
            'authors': [a.get('raw_author_name') or (a.get('author') or {}).get('display_name') or '' for a in w.get('authorships') or []],
            'topic': ((w.get('primary_topic') or {}).get('field') or {}).get('display_name'),
            'locations': [{'pdf': l.get('pdf_url'), 'landing': l.get('landing_page_url'), 'oa': l.get('is_oa'),
                           'version': l.get('version'), 'license': l.get('license'),
                           'source': (l.get('source') or {}).get('display_name'),
                           'source_type': (l.get('source') or {}).get('type')} for l in w.get('locations') or []]}


def listing(filt):
    n = openalex('works', {'filter': filt, 'per-page': 1, 'select': 'id'})['meta']['count']
    if n > FULL_LIMIT:
        filt = filt + ',' + FIELDS
    cur, rows = '*', []
    while cur:
        d = openalex('works', {'filter': filt, 'per-page': 200, 'cursor': cur, 'select': SELECT}, cache=False)
        rows += [compact(w) for w in d['results']]
        cur = d['meta'].get('next_cursor')
        if not d['results']:
            break
    return n, filt, rows


def main():
    WORKS.mkdir(exist_ok=True)
    ids = inst_ids()
    log = []
    for name, i in ids.items():
        p = WORKS / f'{i}.jsonl'
        if p.exists():
            continue
        allw = {}
        for lab, f in [('A', f'type:dissertation,locations.source.host_organization_lineage:{i}'),
                       ('B', f'type:dissertation,authorships.institutions.lineage:{i},is_oa:true')]:
            n, used, rows = listing(f)
            log.append({'inst': name, 'openalex': i, 'query': lab, 'count_all': n, 'filter_used': used, 'rows': len(rows)})
            for r in rows:
                r.setdefault('via', lab)
                allw.setdefault(r['id'], r)
        tmp = p.with_suffix('.tmp')
        tmp.write_text(''.join(json.dumps(r) + '\n' for r in allw.values()))
        tmp.rename(p)
        print(name, i, len(allw), flush=True)
    with (CACHE / 'harvest-log.jsonl').open('a') as f:
        for r in log:
            f.write(json.dumps(r) + '\n')


if __name__ == '__main__':
    main()
