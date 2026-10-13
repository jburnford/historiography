#!/usr/bin/env python3
"""Identify the first authors of cited works from title evidence in the project's catalogues.

A bibliography that prints "Miller, J.R." still names the work, so the author can be
found where that work is catalogued with a fuller name or an identifier. Each Work in
``graph.json`` (first-author surname plus main title) is matched on the same surname and
main-title key against:

- Crossref history-journal articles (contributors, with deposited ORCIDs),
- ORCID self-claimed works (claimant's ORCID and name),
- Open Library work authors (author key),
- H-Net reviewed items (credited names, registry-resolved where possible).

Identifiers map to Wikidata through the person registry's ``authority_ids``; registry
occurrences carry its resolved individual. A work receives an identity only when every
matching identifier points to one person; otherwise the candidates are listed as
ambiguous. Output: ``work-authorities.jsonl``.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3

import duckdb

from build_dissertation_citation_graph import fold, title_key

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/person-registry/generated'
CROSSREF = [ROOT / 'data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb',
            ROOT / 'data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb']
HNET = ROOT / 'data/hnet-graph/generated/graph.sqlite'


def surname_of(full):
    toks = fold(full).split()
    return toks[-1] if toks else ''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--registry', type=Path, default=max(REGISTRY.glob('v*/registry.duckdb'), key=lambda p: int(p.parent.name[1:])))
    args = parser.parse_args()
    graph = json.loads((args.out / 'graph.json').read_text())
    wanted = {}
    for n in graph['nodes']:
        if n['type'] == 'Work':
            sur, tk = n['id'][2:].split('|')[:2]  # a trailing '|a' marks article/chapter works
            wanted[(sur, tk)] = n
    titles = {tk for _, tk in wanted}
    print(f'{len(wanted)} works to match', flush=True)

    hits = defaultdict(list)

    def offer(source, title, family, full, year, **ids):
        tk = title_key(title)
        if tk not in titles:
            return
        key = (fold(family) if family else surname_of(full), tk)
        if key in wanted:
            hits[key].append(dict(source=source, name=full, year=year, **{k: v for k, v in ids.items() if v}))

    for path in CROSSREF:
        con = duckdb.connect(str(path), read_only=True)
        for title, given, family, name, orcid, credit, year in con.execute(
                """SELECT r.title_text, c.given_name, c.family_name, c.name, c.orcid, c.credit_id, r.publication_year
                   FROM contributors c JOIN records r USING (record_id) WHERE r.title_text IS NOT NULL""").fetchall():
            offer('crossref', title, family, name or f'{given or ""} {family or ""}'.strip(), year,
                  orcid=(orcid or '').rsplit('/', 1)[-1].upper() or None, occurrence_id=credit)
        con.close()
    print('crossref done', sum(map(len, hits.values())), flush=True)

    con = duckdb.connect()
    names = {o: (g, f) for o, g, f in con.execute(
        f"SELECT orcid, given, family FROM read_parquet('{REGISTRY}/orcid-claims/orcid-names.parquet')").fetchall()}
    for orcid, title, year in con.execute(
            f"SELECT orcid, title, year FROM read_parquet('{REGISTRY}/orcid-claims/claimed-works.parquet') WHERE title IS NOT NULL").fetchall():
        given, family = names.get(orcid, (None, None))
        if family:
            offer('orcid_claim', title, family, f'{given or ""} {family}'.strip(), year, orcid=orcid.upper())
    for title, year, akey, aname in con.execute(
            f"SELECT title, first_year, author_key, author_name FROM read_csv('{REGISTRY}/openlibrary/work-authors.tsv.gz', delim='\t', header=true)").fetchall():
        if aname:
            offer('openlibrary', title, None, aname, year, openlibrary=akey)
    hn = sqlite3.connect(f'file:{HNET}?mode=ro', uri=True)
    for title, year, name, mid in hn.execute(
            """SELECT i.title, i.publication_year, m.name, m.id FROM items i JOIN mentions m ON m.item_id = i.id
               WHERE m.role IN ('contributor_unspecified', 'author', 'editor')"""):
        offer('hnet', title, None, name, year, occurrence_id=mid)
    print('all sources done', sum(map(len, hits.values())), flush=True)

    reg = duckdb.connect(str(args.registry), read_only=True)
    occ_ids = sorted({h['occurrence_id'] for hs in hits.values() for h in hs if h.get('occurrence_id')})
    resolved = {}
    if occ_ids:
        reg.execute('CREATE TEMP TABLE want (occurrence_id VARCHAR)')
        reg.executemany('INSERT INTO want VALUES (?)', [(o,) for o in occ_ids])
        for occ, ind, status, qids in reg.execute(
                """SELECT o.occurrence_id, o.individual_id, o.status, s.qids FROM occurrence_resolution o
                   JOIN want USING (occurrence_id) LEFT JOIN individual_summary s USING (individual_id)
                   WHERE o.individual_id IS NOT NULL""").fetchall():
            resolved[occ] = dict(individual=ind, tier=status, qids=qids or [])
    auth = defaultdict(set)
    for scheme, field in (('orcid', 'orcid'), ('openlibrary', 'openlibrary')):
        vals = sorted({h[field] for hs in hits.values() for h in hs if h.get(field)})
        if vals:
            reg.execute(f'CREATE OR REPLACE TEMP TABLE v (value VARCHAR)')
            reg.executemany('INSERT INTO v VALUES (?)', [(x,) for x in vals])
            for qid, value in reg.execute(f"SELECT a.qid, a.value FROM authority_ids a JOIN v USING (value) WHERE a.scheme = '{scheme}'").fetchall():
                auth[(scheme, value)].add(qid)

    with (args.out / 'work-authorities.jsonl').open('w') as f:
        stats = defaultdict(int)
        for key, hs in hits.items():
            node = wanted[key]
            if node['year'] and node['kind'] == 'article':
                hs = [h for h in hs if not h.get('year') or abs(int(str(h['year'])[:4]) - node['year']) <= 2] or []
            if not hs:
                continue
            # Hits are one person when they share an identifier or the same full name;
            # a work is ambiguous only if its hits keep two persons apart.
            parent = list(range(len(hs)))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            owner = {}
            for i, h in enumerate(hs):
                qids = set()
                if h.get('occurrence_id') in resolved:
                    h['registry'] = resolved[h['occurrence_id']]
                    qids |= set(h['registry']['qids'])
                for scheme in ('orcid', 'openlibrary'):
                    if h.get(scheme):
                        qids |= auth.get((scheme, h[scheme]), set())
                h['qids'] = sorted(qids)
                ids = {('qid', q) for q in qids}
                if h.get('registry'):
                    ids.add(('registry', h['registry']['individual']))
                if h.get('orcid'):
                    ids |= {('orcid', h['orcid']), ('registry', 'orcid:' + h['orcid'])}
                if h.get('openlibrary'):
                    ids |= {('openlibrary', h['openlibrary']), ('registry', 'ol:' + h['openlibrary'])}
                given = fold(h['name']).split()
                if len(given) >= 2 and len(given[0]) > 1:
                    ids.add(('name', ' '.join(given)))
                h['ids'] = ids
                for x in ids:
                    if x in owner:
                        parent[find(i)] = find(owner[x])
                    else:
                        owner[x] = i
            groups = defaultdict(list)
            for i, h in enumerate(hs):
                groups[find(i)].append(h)
            people = []
            for members in groups.values():
                ids = set().union(*(m['ids'] for m in members))
                qids = sorted(v for k, v in ids if k == 'qid')
                strong = qids or sorted(v for k, v in ids if k in ('registry', 'orcid', 'openlibrary'))
                if strong:
                    people.append(dict(qids=qids, ids=sorted(v for k, v in ids if k != 'name'),
                                       sources=sorted({m['source'] for m in members})))
            full = [h['name'] for h in hs if len(fold(h['name']).split()) >= 2 and len(fold(h['name']).split()[0]) > 1]
            record = dict(work_id=node['id'], title=node['title'], matches=len(hs), sources=sorted({h['source'] for h in hs}),
                          names=sorted(set(h['name'] for h in hs)), full_name=max(set(full), key=full.count) if full else None)
            if len(people) == 1 and len(people[0]['qids']) <= 1:
                pr = people[0]
                record['identity'] = dict(qid=pr['qids'][0] if pr['qids'] else None, ids=pr['ids'], sources=pr['sources'])
                stats['identified_qid' if pr['qids'] else 'identified_without_qid'] += 1
            elif people:
                record['ambiguous'] = people
                stats['ambiguous'] += 1
            else:
                stats['names_only'] += 1
            f.write(json.dumps(record, ensure_ascii=False, default=list) + '\n')
    stats['works_matched'] = sum(1 for k in hits if hits[k])
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
