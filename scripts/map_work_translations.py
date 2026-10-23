#!/usr/bin/env python3
"""Map translations and editions of a cited work to one work, through Wikidata (QLever).

User (2026-10-22): "we should try to map the translations so they are the same book … at least
at the top of the lists". *Surveiller et punir* and *Discipline and Punish* were two works in the
graph, which splits a work's citations by language and makes cross-country comparison unfair.

For works cited by at least ``--min-cited`` theses whose first author is grounded in Wikidata
(``person-wikidata.jsonl``), the author's Wikidata works (P50) are fetched with their titles in
every language (labels and P1476 title), together with the titles of their editions and
translations (items with P629 'edition or translation of' that work). A graph work matches a
Wikidata work when its main-title key equals one of those title keys, or one is a prefix of the
other of at least three words. A graph work matching more than one Wikidata work is left alone.

Editions and translations that carry their own author statement are folded into the work they are
an edition of (P629) first. Graph works by the same author that match one Wikidata work form a cluster. Output
``work-translations.jsonl``: one row per clustered graph work, with the Wikidata work, the
cluster's canonical work id (the most cited) and the matched titles. The graph builder merges
each cluster into its canonical work. Clusters are identified only through Wikidata: a work not
in Wikidata, or whose translations carry no title there, stays split.
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dissertation_citation_graph import fold, title_key  # noqa: E402
from ground_cited_people_wikidata import literal, post, qid  # noqa: E402

csv.field_size_limit(10 ** 8)


def same_title(a, b):
    short, long_ = sorted((a, b), key=len)
    return a == b or (len(short.split()) >= 3 and long_.startswith(short + ' '))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--min-cited', type=int, default=5)
    args = p.parse_args()
    out = args.out
    person_qid = {}
    for line in (out / 'person-wikidata.jsonl').open():
        r = json.loads(line)
        if r.get('qid'):
            person_qid[r['name']] = r['qid']
    works = []
    for r in csv.DictReader((out / 'works.csv').open(newline='', encoding='utf-8')):
        if int(r['cited_by_dissertations']) < args.min_cited:
            continue
        first = r['authors'].split(';')[0].strip()
        q = person_qid.get(first)
        if q:
            works.append(dict(work_id=r['work_id'], qid=q, title=r['title'], tk=title_key(r['title']).removesuffix('|a'),
                              cited=int(r['cited_by_dissertations'])))
    authors = sorted({w['qid'] for w in works})
    print(f'{len(works)} works cited by >= {args.min_cited} theses with a grounded first author; {len(authors)} authors', flush=True)
    titles = defaultdict(lambda: defaultdict(set))  # author qid -> wikidata work -> title keys
    parent = {}  # edition or translation item (P629) -> the work it is an edition of
    for i in range(0, len(authors), 150):
        vals = ' '.join(f'wd:{q}' for q in authors[i:i + 150])
        rows = post(f"""SELECT ?h ?w ?t WHERE {{ VALUES ?h {{ {vals} }} ?w wdt:P50 ?h .
            {{ ?w rdfs:label ?t }} UNION {{ ?w wdt:P1476 ?t }} UNION {{ ?e wdt:P629 ?w . ?e wdt:P1476 ?t }}
            UNION {{ ?e wdt:P629 ?w . ?e rdfs:label ?t }} }}""")
        for r in rows:
            tk = title_key(literal(r['t']))
            if len(tk) >= 3:
                titles[qid(r['h'])][qid(r['w'])].add(tk)
        for r in post(f"""SELECT ?w ?p WHERE {{ VALUES ?h {{ {vals} }} ?w wdt:P50 ?h . ?w wdt:P629 ?p }}"""):
            parent[qid(r['w'])] = qid(r['p'])
        print(f'  authors {min(i + 150, len(authors))}/{len(authors)}: {len(rows)} title rows', flush=True)

    def root(q, depth=0):
        return root(parent[q], depth + 1) if q in parent and depth < 5 else q
    for aq in titles:  # fold editions that carry their own author statement into their work
        merged = defaultdict(set)
        for wq, tks in titles[aq].items():
            merged[root(wq)] |= tks
        titles[aq] = merged
    match = {}
    for w in works:
        hits = {wq for wq, tks in titles.get(w['qid'], {}).items() if any(same_title(w['tk'], t) for t in tks)}
        if len(hits) == 1:
            match[w['work_id']] = hits.pop()
    clusters = defaultdict(list)
    for w in works:
        if w['work_id'] in match:
            clusters[(w['qid'], match[w['work_id']])].append(w)
    rows = []
    for (aq, wq), ws in clusters.items():
        if len(ws) < 2:
            continue
        canon = max(ws, key=lambda w: w['cited'])
        for w in ws:
            rows.append(dict(work_id=w['work_id'], canonical=canon['work_id'], work_qid=wq, author_qid=aq, title=w['title'],
                             cited_by_dissertations=w['cited']))
    # Clusters merged by an earlier build no longer show as separate works, so keep earlier rows.
    path = out / 'work-translations.jsonl'
    keep = {json.loads(l)['work_id']: json.loads(l) for l in path.open()} if path.exists() else {}
    keep.update({r['work_id']: r for r in rows})
    with path.open('w') as f:
        for r in sorted(keep.values(), key=lambda r: (r['canonical'], -r['cited_by_dissertations'])):
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    n_clusters = len({r['canonical'] for r in rows})
    print(f'matched {len(match)} works to Wikidata; {n_clusters} clusters merge {len(rows)} graph works', flush=True)
    big = sorted({r['canonical'] for r in rows}, key=lambda c: -sum(x['cited_by_dissertations'] for x in rows if x['canonical'] == c))[:25]
    for c in big:
        print('  ' + ' = '.join(f"{x['title'][:45]} ({x['cited_by_dissertations']})" for x in rows if x['canonical'] == c))


if __name__ == '__main__':
    main()
