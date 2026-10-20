#!/usr/bin/env python3
"""Robustness tests for the co-citation fields (dissertation_citation_views.py).

For the base configuration (min_cited 15, resolution 1.5, 40 Louvain runs, 80% consensus)
and for perturbed configurations (resolution 1.0/1.25/1.75/2.0; min_cited 10/20; consensus
70%/90%), each base field is matched to the perturbed field that shares the most of its
works (Jaccard). A field that keeps a high Jaccard across perturbations is a robust
structure; one that splits or dissolves depends on settings.

Per work: the share of base runs in which it sits with its field's core (the anchor work's
community), its strongest co-citation neighbours and their fields, and the fields it is
assigned to under each perturbation. ``--works`` names works to report in detail (title
prefixes). ``--country CC`` tests a country sub-graph (see ``dissertation_scope.py``).
Output: ``field-robustness.json`` in ``audit/`` (main graph) or ``audit/countries/<CC>/``, and a
printed summary.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities

from dissertation_citation_views import fields, load
from dissertation_scope import add_scope_argument, audit_dir, summary_dir


def consensus(G, works, seeds, resolution, keep):
    runs = [louvain_communities(G, weight='weight', resolution=resolution, seed=s) for s in range(seeds)]
    labels = [{w: i for i, c in enumerate(r) for w in c} for r in runs]
    C = nx.Graph()
    C.add_nodes_from(sorted(works))
    C.add_edges_from((a, b) for a, b in G.edges() if sum(l[a] == l[b] for l in labels) / seeds >= keep)
    return [set(c) for c in nx.connected_components(C) if len(c) >= 10], labels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--works', nargs='*', default=['The Middle Ground'])
    add_scope_argument(parser)
    args = parser.parse_args()
    g, nodes, diss, cites, authored, sup = load(args.out, args.country)
    labels_csv = {}
    import csv
    with (summary_dir(args.out, args.country) / 'field-labels.csv').open(newline='') as f:
        labels_csv = {r['anchor_work']: r['label'] for r in csv.DictReader(f)}
    works, count, G, groups, field_of, pos, stability, links = fields(nodes, diss, cites, authored, 15, country=args.country)
    base = [set(gp) for gp in groups]
    names = [labels_csv.get(gp[0], nodes[gp[0]]['title'][:40]) for gp in groups]

    # Per-work stability in the base configuration.
    _, base_labels = consensus(G, works, 40, 1.5, 0.8)
    anchor = {i: gp[0] for i, gp in enumerate(groups)}
    work_stability = {}
    for w in works:
        f = field_of.get(w)
        if f is not None:
            work_stability[w] = sum(l[w] == l[anchor[f]] for l in base_labels) / len(base_labels)

    configs = [('resolution 1.0', 15, 1.0, 0.8), ('resolution 1.25', 15, 1.25, 0.8), ('resolution 1.75', 15, 1.75, 0.8),
               ('resolution 2.0', 15, 2.0, 0.8), ('consensus 70%', 15, 1.5, 0.7), ('consensus 90%', 15, 1.5, 0.9),
               ('min cited 10', 10, 1.5, 0.8), ('min cited 20', 20, 1.5, 0.8)]
    results, assign = {}, defaultdict(dict)
    for name, mc, res, keep in configs:
        if mc == 15:
            W, GG = works, G
        else:
            W, _, GG, *_ = fields(nodes, diss, cites, authored, mc, seeds=2, country=args.country)
        comms, _ = consensus(GG, W, 40, res, keep)
        row = []
        for i, b in enumerate(base):
            best = max(comms, key=lambda c: len(b & c) / len(b | c)) if comms else set()
            jac = len(b & best) / len(b | best) if best else 0
            kept = len(b & best) / len(b)
            row.append(dict(field=names[i], jaccard=round(jac, 2), share_of_field_kept=round(kept, 2), matched_size=len(best)))
        results[name] = row
        for w in works:
            c = next((j for j, cm in enumerate(comms) if w in cm), None)
            if c is None:
                assign[w][name] = 'unclustered'
            else:
                overlap = Counter(field_of[x] for x in comms[c] if x in field_of)
                assign[w][name] = names[overlap.most_common(1)[0][0]] if overlap else 'new field'

    def neighbours(w, k=10):
        nb = sorted(G[w].items(), key=lambda kv: -kv[1]['weight'])[:k]
        return [dict(title=nodes[x]['title'][:70], author=nodes[authored[x][0]]['name'] if authored.get(x) else '',
                     cosine=round(d['weight'], 3), field=names[field_of[x]] if x in field_of else 'unclustered') for x, d in nb]

    detail = {}
    for prefix in args.works:
        for w in sorted(works, key=lambda w: -count[w]):
            if nodes[w]['title'].lower().startswith(prefix.lower()):
                f = field_of.get(w)
                field_votes = Counter(names[field_of[x]] for x in G[w] if x in field_of)
                detail[nodes[w]['title']] = dict(field=names[f] if f is not None else 'unclustered',
                                                  stability=round(work_stability.get(w, 0), 2),
                                                  neighbour_fields=field_votes.most_common(5),
                                                  neighbours=neighbours(w), perturbed=assign[w])
                break

    # Content: what the dissertations engaging each field are about.
    engaged = {i: [d for d in diss if len(cites[d] & b) >= 3] for i, b in enumerate(base)}
    content = {}
    for i, ds in engaged.items():
        inst = Counter(diss[d]['institution'] for d in ds).most_common(5)
        content[names[i]] = dict(engaged=len(ds), institutions=inst,
                                 sample_titles=[diss[d]['title'][:110] for d in sorted(ds, key=lambda d: -len(cites[d] & base[i]))[:12]])
    field_summary = []
    for i, b in enumerate(base):
        stab = [work_stability[w] for w in b]
        robust = [results[c][i]['jaccard'] for c, *_ in configs]
        field_summary.append(dict(field=names[i], works=len(b), mean_work_stability=round(sum(stab) / len(stab), 2),
                                  weak_works=[nodes[w]['title'][:60] for w in sorted(b, key=lambda w: work_stability[w])[:5] if work_stability[w] < 0.6],
                                  min_jaccard=min(robust), mean_jaccard=round(sum(robust) / len(robust), 2)))
    out = dict(base=dict(min_cited=15, resolution=1.5, runs=40, consensus=0.8), fields=field_summary,
               perturbations=results, works=detail, content=content)
    audit = audit_dir(args.out, args.country)
    audit.mkdir(parents=True, exist_ok=True)
    (audit / 'field-robustness.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    for r in field_summary:
        print(f"{r['field'][:48]:48} works {r['works']:3}  stability {r['mean_work_stability']:.2f}  jaccard mean {r['mean_jaccard']:.2f} min {r['min_jaccard']:.2f}")
    print(json.dumps(detail, ensure_ascii=False, indent=1)[:6000])


if __name__ == '__main__':
    main()
