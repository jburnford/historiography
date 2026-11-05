"""Works Crossref holds under the ORCIDs on person keys -> authorship claims for every keyed author (2026-11-05).

key_orcid_works.py reads what people list in their own ORCID records; many records are empty (Stephane Castonguay's
lists nothing) though publishers deposit the author's ORCID with the DOI. User, 2026-11-05: co-authorship counts
("Stephane and I have co-authored multiple articles"), and his joint article British ghost acres (2022) carries
both ORCIDs in Crossref. So for each live person key's ORCID, Crossref's works filtered by that ORCID
(api.crossref.org/works?filter=orcid:..., cursor paging, cached under --cache) give DOIs with full author lists;
each author whose ORCID a key holds gets an `authored` claim (`crossref-orcid:<doi>:<orcid>`, recorded, subject
`orcid:<orcid>`): the ORCID decides identity, never the name. A DOI no key holds becomes a work (`doi:<doi>`,
members `year:` and `crossref-type:`, label the title). Authors without an ORCID on a key are counted, not linked.
Kept types: journal articles, book chapters, books, edited books, monographs, proceedings articles, reference
entries, dissertations, reports, posted content (preprints) when the person has no other work of that title.

    python3 scripts/key_crossref_orcid.py harvest --cache /mnt/e/crossref-orcid     # resumable, ~4 requests/s
    python3 scripts/key_crossref_orcid.py propose --cache /mnt/e/crossref-orcid --out data/identifiers/crossref-orcid-2026-11-05
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import title_key

GRAPH = ROOT / 'build/graph'
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'
TYPES = {'journal-article', 'book-chapter', 'book', 'edited-book', 'monograph', 'proceedings-article', 'reference-entry',
         'dissertation', 'report', 'posted-content', 'book-part', 'book-section'}


def orcids():
    return sorted({o for (o,) in duckdb.sql(f"SELECT orcid FROM '{GRAPH}/person.parquet' WHERE orcid IS NOT NULL").fetchall()})


def get(url):
    for wait in (0, 5, 30, 120):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
    return None


def cmd_harvest(args):
    args.cache.mkdir(parents=True, exist_ok=True)
    todo = [o for o in orcids() if not (args.cache / f'{o}.json').exists()]
    print(json.dumps(dict(orcids=len(orcids()), todo=len(todo))), flush=True)
    sel = 'DOI,title,author,issued,type,container-title'
    for n, o in enumerate(todo):
        items, cursor = [], '*'
        while True:
            d = get(f'https://api.crossref.org/works?filter=orcid:{o}&rows=1000&select={sel}&cursor={urllib.parse.quote(cursor)}')
            if d is None:
                items = None
                break
            m = d['message']
            items += m['items']
            if len(m['items']) < 1000 or not m.get('next-cursor'):
                break
            cursor = m['next-cursor']
            time.sleep(0.25)
        if items is not None:
            (args.cache / f'{o}.json').write_text(json.dumps(items, ensure_ascii=False))
        if n % 500 == 0:
            print(f'{n}/{len(todo)}', flush=True)
        time.sleep(0.25)


def cmd_propose(args):
    state = State.load(args.state)
    keyed = {a.split(':', 1)[1] for a in state.anchor if a.startswith('orcid:')}
    report, ops, seen, new_work = Counter(), [], set(), {}
    for f in sorted(args.cache.glob('*.json')):
        for it in json.loads(f.read_text()):
            if it.get('type') not in TYPES or not it.get('DOI'):
                report['type_left_out'] += 1
                continue
            doi = it['DOI'].lower()
            title = ((it.get('title') or [''])[0] or '').strip()
            year = ((it.get('issued') or {}).get('date-parts') or [[None]])[0][0]
            authors = [(a.get('ORCID') or '').rstrip('/').split('/')[-1] for a in it.get('author') or []]
            linked = [o for o in authors if o in keyed]
            report['authors_without_keyed_orcid'] += len(authors) - len(linked)
            if not linked:
                continue
            if f'doi:{doi}' not in state.anchor and doi not in new_work:
                new_work[doi] = dict(event='mint', key=f'new:w{len(new_work)}', type='work', label=title[:500],
                                     resolution='recorded', anchors=[f'doi:{doi}'], aliases=[],
                                     members=[m for m in (f'year:{year}' if year else '', f"crossref-type:{it['type']}") if m],
                                     basis='a DOI Crossref holds under the ORCID of a keyed person')
            for o in linked:
                anchor = f'crossref-orcid:{doi}:{o}'
                if anchor in state.anchor or anchor in seen:
                    report['claim_exists'] += 1
                    continue
                seen.add(anchor)
                report['claims'] += 1
                ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[anchor], relation=dict(subject=f'orcid:{o}', predicate='authored', object=f'doi:{doi}'),
                                basis='Crossref lists this ORCID among the work\'s authors'))
    ops = list(new_work.values()) + ops
    report['works_minted'] = len(new_work)
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="works Crossref holds under keyed people's ORCIDs, credited to every author whose ORCID is keyed",
        decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('step', choices=['harvest', 'propose'])
    ap.add_argument('--cache', type=Path, default=Path('/mnt/e/crossref-orcid'))
    ap.add_argument('--out', type=Path)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    a = ap.parse_args()
    {'harvest': cmd_harvest, 'propose': cmd_propose}[a.step](a)
