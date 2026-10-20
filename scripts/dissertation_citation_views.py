#!/usr/bin/env python3
"""Three analytical views of the dissertation citation graph, written as JSON for the HTML page.

All measures use strict History PhDs (``in_analysis``: eligibility ``history_phd`` with a
parsed bibliography), of every country (main graph) or of one country (``--country CC``,
a sub-graph; see ``dissertation_scope.py``), and are shares of dissertations, never raw
counts. Output: ``views.json`` in ``summary/`` or ``summary/countries/<CC>/``.

1. Fields (co-citation). Works cited by at least ``--min-cited`` History PhDs, excluding
   corporate authors and works cited mostly as primary sources, are linked by cosine
   co-citation (pairs cited together by at least 3 dissertations, cosine >= 0.12). Fields
   are the consensus of 40 Louvain runs (resolution 1.5): works stay together only if
   they share a community in at least 80% of runs. A dissertation *engages* a field when
   it cites at least three of its works. Per field: engagement per year (centred
   three-year window, Wilson 95%), and the people its engaged dissertations cite
   (share within the field, and lift over the whole corpus).
2. Supervision. For each dissertation with a recorded supervisor: does its bibliography
   cite the supervisor? Baseline: the share of other History PhDs at the same university
   within five years of the supervisor's students that cite the same person. Also
   supervision chains: students in the corpus who later supervise in it.
3. Universities (2010–2025 only, so institutions are compared over the same years):
   field engagement by university, and each department's distinctive scholars (cited by
   at least 5 of its dissertations, ranked by lift over all other universities).

Field labels are provisional and editable in ``field-labels.csv`` in the same directory
(keyed by the field's anchor work, so they survive re-runs). A scope without a label file
starts from the labels of the other scopes whose anchors it shares.
"""
import argparse
from collections import Counter, defaultdict
import csv
import itertools
import json
import math
from pathlib import Path
import re

import networkx as nx
from networkx.algorithms.community import louvain_communities

from dissertation_scope import add_scope_argument, check_country, in_scope, strict_count, summary_dir


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def load(out, country=None):
    g = json.loads((out / 'graph.json').read_text())
    check_country(g, country)
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k: n for k, n in nodes.items() if in_scope(n, country)}
    cites, authored, sup = defaultdict(set), defaultdict(list), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            cites[e['source']].add(e['target'])
        elif e['type'] == 'AUTHORED':
            authored[e['target']].append(e['source'])
        elif e['type'] == 'SUPERVISED':
            sup[e['target']].add(e['source'])
    return g, nodes, diss, cites, authored, sup


def first_author(nodes, authored, w):
    return nodes[authored[w][0]] if authored.get(w) else None


def fields(nodes, diss, cites, authored, min_cited, seeds=40, resolution=1.5, keep=0.8, country=None):
    def scholarly(w):
        n = nodes[w]
        ca = n['cited_as']
        a = first_author(nodes, authored, w)
        return a and a['name_key_kind'] != 'corporate_or_single_name' and ca.get('primary', 0) / (sum(ca.values()) or 1) < 0.5
    works = {w for w, n in nodes.items() if n['type'] == 'Work' and strict_count(n, country) >= min_cited and scholarly(w)}
    count, co = Counter(), Counter()
    for d in diss:
        s = sorted(cites[d] & works)
        count.update(s)
        co.update(itertools.combinations(s, 2))
    G = nx.Graph()
    G.add_nodes_from(sorted(works))  # fixed order: Louvain results depend on insertion order
    for (a, b), k in sorted(co.items()):
        cos = k / math.sqrt(count[a] * count[b])
        if k >= 3 and cos >= 0.12:
            G.add_edge(a, b, weight=cos)
    runs = [louvain_communities(G, weight='weight', resolution=resolution, seed=s) for s in range(seeds)]
    labels = [{w: i for i, c in enumerate(r) for w in c} for r in runs]
    C = nx.Graph()
    C.add_nodes_from(sorted(works))
    C.add_edges_from((a, b) for a, b in G.edges() if sum(l[a] == l[b] for l in labels) / seeds >= keep)
    groups = [sorted(c, key=lambda w: (-count[w], w)) for c in nx.connected_components(C) if len(c) >= 10]
    groups.sort(key=lambda g: (-len(g), g[0]))
    field_of = {w: i for i, grp in enumerate(groups) for w in grp}
    # Field-anchored layout: fields placed by their mutual co-citation, works around their field.
    M = nx.Graph()
    M.add_nodes_from(range(len(groups)))
    for a, b, wt in G.edges(data='weight'):
        fa, fb = field_of.get(a), field_of.get(b)
        if fa is not None and fb is not None and fa != fb:
            M.add_edge(fa, fb, weight=M.get_edge_data(fa, fb, {'weight': 0})['weight'] + wt / (len(groups[fa]) * len(groups[fb])))
    centre = nx.spring_layout(M, weight='weight', seed=7, iterations=500, k=2.2 / math.sqrt(len(groups)))
    pos = {}
    for i, grp in enumerate(groups):
        local = nx.spring_layout(G.subgraph(grp), weight='weight', seed=7, iterations=200)
        r = 0.15 * math.sqrt(len(grp) / 30)
        for w, (x, y) in local.items():
            pos[w] = (centre[i][0] + r * x, centre[i][1] + r * y)
    for w in sorted(works - set(pos)):  # unclustered works: mean position of clustered neighbours
        nb = [pos[n] for n in G.neighbors(w) if n in pos]
        pos[w] = (sum(p[0] for p in nb) / len(nb), sum(p[1] for p in nb) / len(nb)) if nb else (0.0, 0.0)
    xs, ys = sorted(p[0] for p in pos.values()), sorted(p[1] for p in pos.values())
    lo_x, hi_x, lo_y, hi_y = xs[0], xs[-1], ys[0], ys[-1]
    norm = lambda v, lo, hi: min(1.0, max(0.0, (v - lo) / (hi - lo)))
    pos = {w: (norm(x, lo_x, hi_x), norm(y, lo_y, hi_y)) for w, (x, y) in pos.items()}
    stability = sum(len(grp) for grp in groups) / len(works)
    links = sorted(([a, b, d['weight']] for a, b, d in M.edges(data=True)), key=lambda e: -e[2])
    return works, count, G, groups, field_of, pos, stability, links


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--min-cited', type=int, default=15)
    parser.add_argument('--min-window', type=int, default=30)
    add_scope_argument(parser)
    args = parser.parse_args()
    out = args.out
    summary = summary_dir(out, args.country)
    summary.mkdir(parents=True, exist_ok=True)
    g, nodes, diss, cites, authored, sup = load(out, args.country)
    people_of = {d: set().union(*(set(authored.get(w, [])) for w in cites[d])) if cites[d] else set() for d in diss}
    years = list(range(1965, 2026))
    n_year = Counter(n['year'] for n in diss.values() if n['year'])

    # ---- 1. Fields ------------------------------------------------------------------
    works, count, G, groups, field_of, pos, stability, field_links = fields(nodes, diss, cites, authored, args.min_cited, country=args.country)
    label_path = summary / 'field-labels.csv'
    labels = {}
    if label_path.exists():
        with label_path.open(newline='') as f:
            labels = {r['anchor_work']: r['label'] for r in csv.DictReader(f)}
    else:  # a new scope starts from the editorial labels of the other scopes, by shared anchor work
        for other in sorted({out / 'summary' / 'field-labels.csv', *(out / 'summary' / 'countries').glob('*/field-labels.csv')} - {label_path}):
            if other.exists():
                with other.open(newline='') as f:
                    labels.update({r['anchor_work']: r['label'] for r in csv.DictReader(f) if r['anchor_work'] not in labels})
    engaged = {i: {d for d in diss if len(cites[d] & set(grp)) >= 3} for i, grp in enumerate(groups)}
    field_rows = []
    for i, grp in enumerate(groups):
        anchor = grp[0]
        eng = engaged[i]
        series = []
        for y in years:
            win = [d for d in diss if diss[d]['year'] and abs(diss[d]['year'] - y) <= 1]
            k = sum(d in eng for d in win)
            lo, hi = wilson(k, len(win))
            series.append(dict(year=y, k=k, n=len(win), share=k / len(win) if win else None, lo=lo, hi=hi,
                               thin=len(win) < args.min_window))
        pc = Counter(p for d in eng for p in people_of[d])
        overall = Counter(p for d in diss for p in people_of[d])
        top_people = []
        for p, k in pc.most_common(60):
            if nodes[p]['name_key_kind'] == 'corporate_or_single_name':
                continue
            within, base = k / len(eng), overall[p] / len(diss)
            top_people.append(dict(name=nodes[p]['name'], qid=nodes[p].get('qid'), within=round(within, 3),
                                   lift=round(within / base, 1) if base else None))
            if len(top_people) == 20:
                break
        auto = ' · '.join(dict.fromkeys(first_author(nodes, authored, w)['name'].split(',')[0] for w in grp[:3]))
        field_rows.append(dict(id=i, anchor=anchor, label=labels.get(anchor, auto), label_is_provisional=anchor not in labels,
                               works=len(grp), engaged=len(eng), series=series, people=top_people,
                               top_works=[dict(title=nodes[w]['title'], author=first_author(nodes, authored, w)['name'],
                                               year=nodes[w]['year'], cited_by=count[w]) for w in grp[:12]],
                               cx=sum(pos[w][0] for w in grp) / len(grp), cy=sum(pos[w][1] for w in grp) / len(grp)))
    if not label_path.exists():
        with label_path.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['anchor_work', 'label', 'anchor_title'])
            for r in field_rows:
                w.writerow([r['anchor'], r['label'], nodes[r['anchor']]['title']])
    edges = sorted(G.edges(data='weight'), key=lambda e: (-e[2], e[0], e[1]))
    deg, kept = Counter(), []
    for a, b, wt in edges:  # strongest within-field links, at most 3 per work, for drawing
        if field_of.get(a) is None or field_of.get(a) != field_of.get(b):
            continue
        if deg[a] < 3 or deg[b] < 3:
            kept.append([a, b, round(wt, 3)])
            deg[a] += 1
            deg[b] += 1
    def link_profile(w):
        nb = sorted(G[w].items(), key=lambda kv: (-kv[1]['weight'], kv[0]))
        by_field = Counter()
        for x, d in nb:
            by_field[field_of.get(x, -1)] += d['weight']
        total = sum(by_field.values()) or 1
        return ([[x, round(d['weight'], 3)] for x, d in nb[:8]],
                [[f, round(v / total, 2)] for f, v in by_field.most_common(4)])
    map_nodes = []
    for w in works:
        nb, split = link_profile(w)
        map_nodes.append(dict(id=w, x=round(pos[w][0], 4), y=round(pos[w][1], 4), field=field_of.get(w), cited_by=count[w],
                              title=nodes[w]['title'], author=first_author(nodes, authored, w)['name'], year=nodes[w]['year'],
                              neighbours=nb, link_split=split))

    # ---- 2. Supervision ---------------------------------------------------------------
    def compatible(s, p):
        """Supervisor person s and cited person p: same node, or same surname and first name."""
        if s == p:
            return True
        ks, kp = nodes[s].get('key', ''), nodes[p].get('key', '')
        if '|' not in ks or '|' not in kp or ks.split('|')[0] != kp.split('|')[0]:
            return False
        gs, gp = ks.split('|')[1].split(), kp.split('|')[1].split()
        return bool(gs and gp) and (gs[0] == gp[0] or (min(len(gs[0]), len(gp[0])) == 1 and gs[0][0] == gp[0][0]))
    by_surname = defaultdict(set)
    for d in diss:
        for p in people_of[d]:
            by_surname[nodes[p].get('key', '').split('|')[0]].add(p)

    def cites_person(d, s):
        sur = nodes[s].get('key', '').split('|')[0]
        return any(compatible(s, p) for p in people_of[d] if nodes[p].get('key', '').split('|')[0] == sur)
    supervised = [d for d in diss if sup[d]]
    cited_sup = {d: any(cites_person(d, s) for s in sup[d]) for d in supervised}
    sups = defaultdict(list)
    for d in supervised:
        for s in sup[d]:
            sups[s].append(d)
    sup_rows = []
    for s, studs in sups.items():
        inst = Counter(diss[d]['institution'] for d in studs).most_common(1)[0][0]
        ys = [diss[d]['year'] for d in studs if diss[d]['year']]
        peers = [d for d in diss if diss[d]['institution'] == inst and s not in sup[d] and diss[d]['year'] and ys
                 and min(ys) - 5 <= diss[d]['year'] <= max(ys) + 5]
        k = sum(cites_person(d, s) for d in studs)
        kp = sum(cites_person(d, s) for d in peers)
        sup_rows.append(dict(name=nodes[s]['name'], qid=nodes[s].get('qid'), institution=inst, students=len(studs),
                             students_citing=k, share=round(k / len(studs), 3), peers=len(peers),
                             peer_share=round(kp / len(peers), 3) if peers else None,
                             first_year=min(ys) if ys else None, last_year=max(ys) if ys else None))
    sup_rows.sort(key=lambda r: (-r['students'], r['name']))
    wrote = defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'WROTE':
            wrote[e['source']].add(e['target'])
    chains = []
    for s in sups:
        for d in wrote.get(s, ()):
            if d in nodes and sup.get(d):
                for t in sup[d]:
                    chains.append(dict(teacher=nodes[t]['name'], student=nodes[s]['name'],
                                       student_phd=dict(institution=nodes[d]['institution'], year=nodes[d]['year'], title=nodes[d]['title']),
                                       student_supervised=len(sups[s]),
                                       student_cites_teacher=bool(d in diss and cites_person(d, t))))
    chains.sort(key=lambda c: -c['student_supervised'])
    by_inst = defaultdict(lambda: [0, 0])
    for d in supervised:
        by_inst[diss[d]['institution']][0] += 1
        by_inst[diss[d]['institution']][1] += cited_sup[d]
    by_period = defaultdict(lambda: [0, 0])
    for d in supervised:
        y = diss[d]['year'] or 0
        per = 'before 2000' if y < 2000 else '2000–09' if y < 2010 else '2010–17' if y < 2018 else '2018–25'
        by_period[per][0] += 1
        by_period[per][1] += cited_sup[d]
    multi = [r for r in sup_rows if r['students'] >= 3 and r['peer_share'] is not None]
    supervision = dict(
        dissertations=len(diss), with_supervisor=len(supervised), cite_supervisor=sum(cited_sup.values()),
        supervisors=len(sups), supervisors_3plus=len(multi),
        pooled_student_share=round(sum(r['students_citing'] for r in multi) / sum(r['students'] for r in multi), 3),
        mean_peer_share=round(sum(r['peer_share'] for r in multi) / len(multi), 3),
        never_cited=sum(r['students_citing'] == 0 for r in multi),
        by_institution=sorted(([i, v[0], round(v[1] / v[0], 3)] for i, v in by_inst.items() if v[0] >= 10), key=lambda r: -r[2]),
        by_period=[[p, by_period[p][0], round(by_period[p][1] / by_period[p][0], 3)] for p in
                   ('before 2000', '2000–09', '2010–17', '2018–25') if by_period[p][0]],
        supervisors_list=multi, chains=chains)

    # ---- 3. Universities, 2010–2025 -----------------------------------------------------
    recent = {d for d in diss if diss[d]['year'] and 2010 <= diss[d]['year'] <= 2025}
    inst_n = Counter(diss[d]['institution'] for d in recent)
    insts = sorted(i for i, n in inst_n.items() if n >= 25)
    field_matrix = []
    for i in insts:
        ds = [d for d in recent if diss[d]['institution'] == i]
        field_matrix.append(dict(institution=i, n=len(ds),
                                 shares=[round(sum(d in engaged[f] for d in ds) / len(ds), 3) for f in range(len(groups))]))
    overall_recent = [round(sum(d in engaged[f] for d in recent) / len(recent), 3) for f in range(len(groups))]
    distinctive = []
    pc_inst = {i: Counter(p for d in recent if diss[d]['institution'] == i for p in people_of[d]) for i in insts}
    pc_all = Counter(p for d in recent for p in people_of[d])
    faculty = defaultdict(set)  # people who supervise History PhDs at each university (any year)
    for d in diss:
        for s in sup[d]:
            faculty[diss[d]['institution']].add(s)
    for i in insts:
        ni, rows = inst_n[i], []
        for p, k in pc_inst[i].items():
            if k < 5 or nodes[p]['name_key_kind'] == 'corporate_or_single_name':
                continue
            rest_n, rest_k = len(recent) - ni, pc_all[p] - k
            share, elsewhere = k / ni, rest_k / rest_n
            rows.append(dict(name=nodes[p]['name'], citing=k, share=round(share, 3), elsewhere=round(elsewhere, 3),
                             excess=round(share - elsewhere, 3), own_faculty=p in faculty[i]))
        rows.sort(key=lambda r: -r['excess'])
        distinctive.append(dict(institution=i, n=ni,
                                external=[r for r in rows if not r['own_faculty']][:10],
                                own_faculty=[r for r in rows if r['own_faculty']][:8],
                                most_cited=sorted(rows, key=lambda r: -r['share'])[:6]))
    universities = dict(window='2010–2025', institutions=insts, n=[inst_n[i] for i in insts], field_matrix=field_matrix,
                        overall=overall_recent, distinctive=distinctive)

    result = dict(
        field_links=[[a, b, round(w / (field_links[0][2] if field_links else 1), 3)] for a, b, w in field_links if w >= 0.08 * field_links[0][2]],
        fields=dict(min_cited=args.min_cited, works=len(works), clustered=sum(len(x) for x in groups), stability=round(stability, 3),
                    fields=field_rows, nodes=map_nodes, edges=kept, years=years),
        supervision=supervision, universities=universities, min_window=args.min_window,
        note='Strict History PhDs with parsed bibliographies; shares of dissertations.')
    (summary / 'views.json').write_text(json.dumps(result, ensure_ascii=False) + '\n')
    print(json.dumps(dict(fields=len(groups), clustered=result['fields']['clustered'], works=len(works),
                          supervision={k: v for k, v in supervision.items() if not isinstance(v, list)},
                          universities=len(insts)), indent=1))


if __name__ == '__main__':
    main()
