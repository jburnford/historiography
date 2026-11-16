"""Route 1b: per-record OpenAlex title search for unheld AHA records in a year band (default 1995-2009), for
institutions whose theses OpenAlex does not type as dissertations or does not tie to the institution.
Any work type; the institution is checked in match_all.py (location host lineage, author affiliation lineage,
or a repository host already seen for that institution). Compact results are stored on E:, one line per record."""
import argparse, sys
from common import *
from harvest_openalex import inst_ids

SELECT = 'id,display_name,publication_year,authorships,locations,doi,type'


def compact(w):
    return {'id': w['id'].rsplit('/', 1)[-1], 'title': w.get('display_name'), 'year': w.get('publication_year'),
            'doi': w.get('doi'), 'type': w.get('type'),
            'authors': [a.get('raw_author_name') or (a.get('author') or {}).get('display_name') or '' for a in w.get('authorships') or []],
            'aff': sorted({x for a in w.get('authorships') or [] for i in a.get('institutions') or []
                           for x in [i.get('id', '').rsplit('/', 1)[-1]] + [l.rsplit('/', 1)[-1] for l in i.get('lineage') or []] if x}),
            'locations': [{'pdf': l.get('pdf_url'), 'landing': l.get('landing_page_url'), 'oa': l.get('is_oa'),
                           'version': l.get('version'), 'license': l.get('license'),
                           'source': (l.get('source') or {}).get('display_name'),
                           'source_type': (l.get('source') or {}).get('type'),
                           'host': [h.rsplit('/', 1)[-1] for h in (l.get('source') or {}).get('host_organization_lineage') or []]}
                          for l in w.get('locations') or []]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from-year', type=int, default=1995)
    ap.add_argument('--to-year', type=int, default=2009)
    ap.add_argument('--shard', default='0/1', help='i/n: this process takes records whose index %% n == i')
    args = ap.parse_args()
    si, sn = map(int, args.shard.split('/'))
    u, _ = universe()
    out = CACHE / f'search-{args.from_year}-{args.to_year}.{si}.jsonl'
    done = set()
    for p in CACHE.glob(f'search-{args.from_year}-{args.to_year}*.jsonl'):
        done |= {json.loads(l)['aha_id'] for l in p.read_text().splitlines() if l.strip()}
    todo = [r for r in u if args.from_year <= int(r['year']) <= args.to_year]
    todo = [r for k, r in enumerate(todo) if k % sn == si and r['id'] not in done]
    print(len(todo), 'to search', flush=True)
    with out.open('a') as f:
        for k, r in enumerate(todo):
            ws = [w for w in words(r['title']) if not w.isdigit()][:10]
            if len(ws) < 2:
                f.write(json.dumps({'aha_id': r['id'], 'results': [], 'note': 'title too short'}) + '\n')
                continue
            y = int(r['year'])
            params = {'filter': f"title.search:{' '.join(ws)},publication_year:{y - 3}-{y + 4}", 'per-page': 15, 'select': SELECT}
            try:
                d = openalex('works', params, cache=False)
                res = [compact(w) for w in d.get('results') or []]
                f.write(json.dumps({'aha_id': r['id'], 'results': res}) + '\n')
                f.flush()
            except RuntimeError as e:  # a failed request is not recorded, so a rerun asks again
                print(r['id'], e, flush=True)
            if k % 500 == 0:
                print(k, flush=True)
                f.flush()


if __name__ == '__main__':
    main()
