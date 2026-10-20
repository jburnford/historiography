#!/usr/bin/env python3
"""Evidence from the History PhD citation graph for the main atlas (read-only on the atlas).

Runs on the main graph or on a country sub-graph (``--country CC``; see
``dissertation_scope.py``). The atlas teaches historiography in Canada, so the atlas
outputs are produced for the CA sub-graph; ``--skip-atlas`` writes only the method
practice tables (used for the main graph).

Writes to ``<out>/summary`` (main graph) or ``<out>/summary/countries/<CC>/``:
- ``atlas-people-crosswalk.csv``: each atlas roster person matched to a citation-graph
  person (by Wikidata QID; else by surname and first name when exactly one roster person
  has them), with History PhDs citing them and the 2000s vs 2018–25 shares.
- ``atlas-gaps.csv``: the most-cited people not in the atlas roster, with the co-citation
  field in which their cited works sit most often. For editorial review only.
- ``field-atlas-crosswalk.csv``: for each co-citation field, the atlas entries whose
  representative figures include the field's most-cited people.
- ``methods.json`` / ``methods-by-period.csv``: share of dissertations whose bibliography
  has a section of each kind (interviews, archives, newspapers, government documents,
  digital sources, images/film/maps, statistics), per year (three-year window, Wilson 95%).

Name matches are candidates, not identities. Nothing here edits the atlas.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import re

from build_dissertation_citation_graph import person_key
from dissertation_scope import add_scope_argument, check_country, in_scope, strict_count, summary_dir

ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    'Oral history / interviews': r'interview|oral|entretien|témoign|temoign|conversation|testimon',
    'Archives / manuscripts': r'archiv|manuscript|fonds|unpublished|inédit|manuscrit',
    'Newspapers / periodicals': r'newspaper|periodical|\bpress\b|journaux|presse|magazine|serial',
    'Government documents': r'government|parliament|official|sessional|gouvernement|officiel|legislat|statut|court|legal',
    'Digital / online sources': r'online|\bweb|digital|internet|electronic|database|numéri|en ligne|website',
    'Images, film and maps': r'film|photograph|image|\bmaps?\b|cartograph|visual|audiovisual|cartes|iconograph|video',
    'Statistics / census': r'census|statistic|recensement|quantitative',
}


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--min-window', type=int, default=30)
    parser.add_argument('--skip-atlas', action='store_true', help='write only methods.json and methods-by-period.csv')
    add_scope_argument(parser)
    args = parser.parse_args()
    out, summary = args.out, summary_dir(args.out, args.country)
    g = json.loads((out / 'graph.json').read_text())
    check_country(g, args.country)
    nodes = {n['id']: n for n in g['nodes']}
    country = args.country
    if not args.skip_atlas:
        atlas_outputs(g, nodes, summary, country)
    methods(out, nodes, summary, country, args.min_window)


def atlas_outputs(g, nodes, summary, country):
    trends = {p['id']: p for p in json.loads((summary / 'trends.json').read_text())['people']}
    views = json.loads((summary / 'views.json').read_text())
    atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    roster = {p['id']: p['label'] for p in atlas['people']}
    qids = {p['person_id']: p['wikidata']['qid'] for p in json.loads((ROOT / 'data/people-wikidata.json').read_text())['people']
            if (p.get('wikidata') or {}).get('qid')}
    by_qid = defaultdict(list)
    for pid, q in qids.items():
        by_qid[q].append(pid)
    by_name = defaultdict(list)
    for pid, label in roster.items():
        k, _ = person_key(label, False)
        if k and '|' in k:
            by_name[(k.split('|')[0], k.split('|')[1].split()[0])].append(pid)
    people = [n for n in g['nodes'] if n['type'] == 'Person' and n['name_key_kind'] != 'corporate_or_single_name']
    match = {}
    for n in people:
        if n.get('qid') in by_qid:
            a, basis = by_qid[n['qid']][0], 'wikidata_qid'
        else:
            sur, given = (n['key'].split('|') + [''])[:2]
            first = given.split()[0] if given else ''
            cands = by_name.get((sur, first), []) if len(first) > 1 else []
            if len(cands) != 1:
                continue
            a, basis = cands[0], 'surname_first_name_candidate'
        if a not in match or strict_count(n, country) > strict_count(match[a][0], country):
            match[a] = (n, basis)
    with (summary / 'atlas-people-crosswalk.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['atlas_person', 'atlas_label', 'graph_person', 'graph_name', 'basis', 'history_phds_citing', 'share_2000_09', 'share_2018_25', 'trend'])
        for a in sorted(roster, key=lambda a: -(strict_count(match[a][0], country) if a in match else -1)):
            n, basis = match.get(a, (None, 'not_found'))
            t = trends.get(n['id'], {}) if n else {}
            w.writerow([a, roster[a], n['id'] if n else '', n['name'] if n else '', basis, strict_count(n, country) if n else 0,
                        t.get('share_2000s', ''), t.get('share_2018_25', ''), t.get('trend', '')])

    # Field of each person's cited works (by work count), for the gap list.
    field_of_work = {n['id']: n['field'] for n in views['fields']['nodes'] if n['field'] is not None}
    labels = {f['id']: f['label'] for f in views['fields']['fields']}
    works_of = defaultdict(list)
    for e in g['edges']:
        if e['type'] == 'AUTHORED':
            works_of[e['source']].append(e['target'])
    matched = {m[0]['id'] for m in match.values()}
    gaps = [n for n in sorted(people, key=lambda n: -strict_count(n, country)) if n['id'] not in matched][:200]
    with (summary / 'atlas-gaps.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['rank', 'name', 'history_phds_citing', 'qid', 'qid_basis', 'trend', 'share_2000_09', 'share_2018_25', 'main_field', 'top_works'])
        for i, n in enumerate(gaps, 1):
            fc = Counter(field_of_work[x] for x in works_of[n['id']] if x in field_of_work)
            top = sorted(works_of[n['id']], key=lambda x: -strict_count(nodes[x], country))[:2]
            t = trends.get(n['id'], {})
            w.writerow([i, n['name'], strict_count(n, country), n.get('qid', ''), n.get('qid_basis', ''), t.get('trend', ''),
                        t.get('share_2000s', ''), t.get('share_2018_25', ''), labels.get(fc.most_common(1)[0][0], '') if fc else '',
                        ' | '.join(nodes[x]['title'] for x in top)])

    # Field ↔ atlas entries: entries whose representative figures name the field's top people.
    entries = [(nd['id'], nd['label'], nd.get('representative_figures_and_works', '') or '') for nd in atlas['nodes']]
    with (summary / 'field-atlas-crosswalk.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['field', 'atlas_entries_naming_its_people', 'field_people_named_in_atlas_entries', 'field_people_not_in_atlas_roster'])
        for fld in views['fields']['fields']:
            hits, named, absent = Counter(), [], []
            for p in fld['people'][:20]:
                # full printed name ('Joan Wallach Scott', 'E. P. Thompson'): surname plus first given name
                if ',' in p['name']:
                    surname, given = [x.strip() for x in p['name'].split(',', 1)]
                else:
                    surname, given = p['name'].split()[-1], ' '.join(p['name'].split()[:-1])
                first = (given.split() or [''])[0].rstrip('.')
                if len(first) > 1:
                    rx = re.compile(r'\b' + re.escape(first) + r'\b[^;,.]{0,25}\b' + re.escape(surname) + r'\b')
                else:
                    rx = re.compile(r'\b' + re.escape(first) + r'\.?\s?(?:[A-Z]\.?\s?){0,2}' + re.escape(surname) + r'\b')
                found = [(eid, lab) for eid, lab, rep in entries if first and rx.search(rep)]
                for eid, lab in found:
                    hits[lab] += 1
                (named if found else absent).append(p['name'])
            w.writerow([fld['label'], '; '.join(f'{lab} ({k})' for lab, k in hits.most_common(6)), '; '.join(named), '; '.join(absent)])

    cov_n = lambda a: strict_count(match[a][0], country)
    print(json.dumps(dict(atlas_people=len(roster), matched=len(match), by_basis=Counter(m[1] for m in match.values()),
                          cited_1=sum(cov_n(a) >= 1 for a in match), cited_10=sum(cov_n(a) >= 10 for a in match),
                          cited_50=sum(cov_n(a) >= 50 for a in match)), indent=1, default=dict))


def methods(out, nodes, summary, country, min_window):
    """Method practice from bibliography section headings."""
    diss = {k[2:]: n for k, n in nodes.items() if in_scope(n, country) and n['year']}
    cats, sectioned = defaultdict(set), set()
    for line in (out / 'entries.jsonl').open():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e['dissertation'] not in diss or len(e['section']) < 2:
            continue
        sec = ' > '.join(e['section'][1:])
        sectioned.add(e['dissertation'])
        for c, rx in METHODS.items():
            if re.search(rx, sec, re.I):
                cats[e['dissertation']].add(c)
    years = list(range(1965, 2026))
    series = {}
    for c in METHODS:
        rows = []
        for y in years:
            win = [d for d in sectioned if abs(diss[d]['year'] - y) <= 1]
            k = sum(c in cats[d] for d in win)
            lo, hi = wilson(k, len(win))
            rows.append(dict(year=y, k=k, n=len(win), share=k / len(win) if win else None, lo=lo, hi=hi, thin=len(win) < min_window))
        series[c] = rows
    (summary / 'methods.json').write_text(json.dumps(dict(
        note='Share of strict History PhDs (with a subheaded bibliography) that have a bibliography section of each kind.',
        dissertations=len(sectioned), series=series), ensure_ascii=False) + '\n')
    periods = [('before 1990', 0, 1989), ('1990s', 1990, 1999), ('2000–09', 2000, 2009), ('2010–17', 2010, 2017), ('2018–25', 2018, 2025)]
    with (summary / 'methods-by-period.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['section_kind'] + [p for p, _, _ in periods])
        w.writerow(['dissertations'] + [sum(lo <= diss[d]['year'] <= hi for d in sectioned) for _, lo, hi in periods])
        for c in METHODS:
            row = [c]
            for _, lo, hi in periods:
                ds = [d for d in sectioned if lo <= diss[d]['year'] <= hi]
                row.append(round(sum(c in cats[d] for d in ds) / len(ds), 3) if ds else '')
            w.writerow(row)
    print(json.dumps(dict(sectioned=len(sectioned))))


if __name__ == '__main__':
    main()
