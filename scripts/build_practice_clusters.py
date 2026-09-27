"""Candidate clusters of historical themes from co-occurrence in the practice record.

EVIDENCE-LAYER-PLAN.md, follow-on to component 1 (user: "there are probably clusters including
a social history cluster, a political history cluster, etc."). Clusters are HYPOTHESES for
editorial review: an artifact of signals, weights and algorithm, not ground-truth groupings,
and a description of how practice is organised rather than of intellectual lineage.

Signals (units -> sets of themes, from build_practice_series exports; rollups excluded):
  people  individuals in the person registry (strict + probable), themes of all their credits:
          reviews (network/heading themes) and Crossref articles (journal themes); a pair
          counts only when its themes come from different networks, headings or journals
  rih     Reviews in History reviews, counting a pair only when its two themes come from
          different subject headings (a heading mapped to two themes is not evidence)

Method, fixed before inspecting results:
  weights    NPMI (Bouma 2009) per signal; pair kept if >= MIN_PAIR co-occurrences and NPMI > 0;
             themes need >= MIN_THEME units. Combined graph averages NPMI over the signals
             in which the pair qualifies.
  clusters   Louvain (Blondel et al. 2008; networkx.algorithms.community.louvain_communities),
             resolution 1.0, seed 0.
  stability  BOOTSTRAPS resamples of units (multinomial weights), each clustered with its own
             seed; per-theme stability = mean co-assignment with its cluster-mates.
  held-out   partition from one signal scored on the other: mean NPMI of within- vs
             between-cluster pairs, and adjusted Rand index between single-signal partitions.
  sensitivity  resolution 0.8 and 1.2 compared with 1.0 (adjusted Rand index).
"""
import argparse
import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import duckdb
import networkx as nx
import numpy as np
from networkx.algorithms.community import louvain_communities

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data/evidence-layer/generated"
REGISTRY = ROOT / "data/person-registry/generated"
CROSSREF = ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb"
SUPPLEMENT = ROOT / "data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb"
CROSSWALK = ROOT / "data/evidence-layer/practice-crosswalk.csv"
MIN_PAIR, MIN_THEME, BOOTSTRAPS, RESOLUTION, SEED, STABLE = 10, 30, 200, 1.0, 0, 0.5


def lit(p):
    return "'" + str(p).replace("'", "''") + "'"


def people_units(series, registry):
    """Per individual: theme -> set of sources (H-Net network, RiH heading, or journal). As for
    RiH, a pair counts only if its themes come from different sources, so a single journal or
    heading linked to several themes (e.g. Past & Present) is not co-occurrence evidence."""
    db = duckdb.connect()
    db.execute(f"ATTACH {lit(registry / 'registry.duckdb')} AS rg (READ_ONLY)")
    db.execute(f"ATTACH {lit(CROSSREF)} AS xr (READ_ONLY)")
    db.execute(f"ATTACH {lit(SUPPLEMENT)} AS xs (READ_ONLY)")
    db.execute("CREATE TEMP VIEW x_memberships AS SELECT * FROM xr.memberships UNION ALL SELECT * FROM xs.memberships")
    db.execute(f"CREATE TEMP VIEW rt AS SELECT * FROM read_csv({lit(series / 'review_themes.csv')}, header=true)")
    db.execute(f"CREATE TEMP VIEW jt AS SELECT * FROM read_csv({lit(series / 'journal_themes.csv')}, header=true)")
    rows = db.execute("""
        WITH cred AS (SELECT r.individual_id, o.corpus, o.record_id FROM rg.occurrence_resolution r
                      JOIN rg.occurrences o USING (occurrence_id)
                      WHERE r.individual_id IS NOT NULL AND o.corpus IN ('hnet', 'rih', 'crossref'))
        SELECT DISTINCT c.individual_id, rt.target, rt.source || ':' || rt.source_label
        FROM cred c JOIN rt ON rt.item = c.record_id WHERE c.corpus IN ('hnet', 'rih')
        UNION
        SELECT DISTINCT c.individual_id, jt.target, 'journal:' || m.journal_key FROM cred c
        JOIN x_memberships m ON m.record_id = c.record_id JOIN jt USING (journal_key)
        WHERE c.corpus = 'crossref'""").fetchall()
    units = defaultdict(lambda: defaultdict(set))
    for ind, t, src in rows:
        units[ind][t].add(src)
    out = []
    for themes in units.values():
        pairs = {(a, b) for a, b in itertools.combinations(sorted(themes), 2)
                 if any(x != y for x in themes[a] for y in themes[b])}
        out.append((frozenset(themes), frozenset(pairs)))
    return out


def rih_units(series):
    by_item = defaultdict(lambda: defaultdict(set))
    with open(series / "review_themes.csv") as f:
        for r in csv.DictReader(f):
            if r["source"] == "rih":
                by_item[r["item"]][r["target"]].add(r["source_label"])
    out = []
    for themes in by_item.values():
        pairs = set()
        for a, b in itertools.combinations(sorted(themes), 2):
            # evidence only if some heading for a differs from some heading for b
            if any(ha != hb for ha in themes[a] for hb in themes[b]):
                pairs.add((a, b))
        out.append((frozenset(themes), frozenset(pairs)))
    return out


class Signal:
    """Units as index arrays so bootstrap counts are weighted bincounts."""

    def __init__(self, name, units, themes):
        self.name, self.themes = name, themes
        idx = {t: i for i, t in enumerate(themes)}
        mu, mt, pu, pp = [], [], [], []
        self.pairs = []
        pair_idx = {}
        for u, (ts, allowed) in enumerate(units):
            tl = sorted(t for t in ts if t in idx)
            for t in tl:
                mu.append(u); mt.append(idx[t])
            for a, b in itertools.combinations(tl, 2):
                if allowed is not None and (a, b) not in allowed:
                    continue
                k = pair_idx.setdefault((a, b), len(self.pairs))
                if k == len(self.pairs):
                    self.pairs.append((a, b))
                pu.append(u); pp.append(k)
        self.n = len(units)
        self.mu, self.mt = np.array(mu, dtype=np.int64), np.array(mt, dtype=np.int64)
        self.pu, self.pp = np.array(pu, dtype=np.int64), np.array(pp, dtype=np.int64)

    def npmi(self, w=None):
        w = np.ones(self.n) if w is None else w
        N = w.sum()
        marg = np.bincount(self.mt, weights=w[self.mu], minlength=len(self.themes))
        co = np.bincount(self.pp, weights=w[self.pu], minlength=len(self.pairs))
        idx = {t: i for i, t in enumerate(self.themes)}
        out = {}
        for k, (a, b) in enumerate(self.pairs):
            ca, cb, cab = marg[idx[a]], marg[idx[b]], co[k]
            if cab < MIN_PAIR or ca < MIN_THEME or cb < MIN_THEME:
                continue
            pab = cab / N
            val = math.log(pab / ((ca / N) * (cb / N))) / -math.log(pab)
            if val > 0:
                out[(a, b)] = (val, int(round(cab)))
        return out, {t: int(round(marg[i])) for i, t in enumerate(self.themes)}


def graph(weight_maps):
    acc = defaultdict(list)
    for wm in weight_maps:
        for pair, (v, _) in wm.items():
            acc[pair].append(v)
    G = nx.Graph()
    for (a, b), vs in acc.items():
        G.add_edge(a, b, weight=sum(vs) / len(vs))
    return G


def partition(G, seed=SEED, resolution=RESOLUTION):
    comms = louvain_communities(G, weight="weight", resolution=resolution, seed=seed)
    return {t: i for i, c in enumerate(sorted(comms, key=lambda c: (-len(c), sorted(c)))) for t in c}


def ari(p, q):
    common = sorted(set(p) & set(q))
    n = len(common)
    if n < 2:
        return None
    cont = defaultdict(int)
    for t in common:
        cont[(p[t], q[t])] += 1
    comb = lambda x: x * (x - 1) / 2
    a = defaultdict(int); b = defaultdict(int)
    for (i, j), v in cont.items():
        a[i] += v; b[j] += v
    s_ij = sum(comb(v) for v in cont.values()); s_a = sum(comb(v) for v in a.values())
    s_b = sum(comb(v) for v in b.values()); exp = s_a * s_b / comb(n)
    mx = (s_a + s_b) / 2
    return round((s_ij - exp) / (mx - exp), 3) if mx != exp else None


def heldout(part, other):
    within = [v for (a, b), (v, _) in other.items() if a in part and b in part and part[a] == part[b]]
    between = [v for (a, b), (v, _) in other.items() if a in part and b in part and part[a] != part[b]]
    m = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    return {"within_mean_npmi": m(within), "within_pairs": len(within),
            "between_mean_npmi": m(between), "between_pairs": len(between)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--series", default="v10")
    ap.add_argument("--registry", default="v7")
    ap.add_argument("--version", default="clusters-v1")
    args = ap.parse_args()
    out = GEN / args.version
    if out.exists():
        raise SystemExit(f"{out} exists; choose a new --version")
    series, registry = GEN / args.series, REGISTRY / args.registry
    labels = {}
    with open(CROSSWALK) as f:
        for r in csv.DictReader(f):
            labels[r["target"]] = r["target_label"]
    raw = {"people": people_units(series, registry), "rih": rih_units(series)}
    themes = sorted({t for us in raw.values() for ts, _ in us for t in ts})
    sig = {k: Signal(k, v, themes) for k, v in raw.items()}
    full = {k: s.npmi() for k, s in sig.items()}
    G = graph([w for w, _ in full.values()])
    part = partition(G)
    single = {k: partition(graph([w])) for k, (w, _) in full.items()}

    rng = np.random.default_rng(SEED)
    co = defaultdict(int)
    for b in range(BOOTSTRAPS):
        wms = [s.npmi(rng.multinomial(s.n, np.full(s.n, 1 / s.n)).astype(float))[0] for s in sig.values()]
        pb = partition(graph(wms), seed=b + 1)
        for a, c in itertools.combinations(sorted(pb), 2):
            if pb[a] == pb[c]:
                co[(a, c)] += 1
    stab = {}
    for t, c in part.items():
        mates = [m for m, cm in part.items() if cm == c and m != t]
        stab[t] = round(sum(co[tuple(sorted((t, m)))] for m in mates) / (BOOTSTRAPS * len(mates)), 3) if mates else None

    clusters = []
    for c in sorted(set(part.values())):
        members = sorted((t for t in part if part[t] == c), key=lambda t: -max(full[k][1].get(t, 0) for k in full))
        internal = sorted(((G[a][b]["weight"], a, b) for a, b in itertools.combinations(members, 2) if G.has_edge(a, b)),
                          reverse=True)[:8]
        clusters.append({
            "cluster": c,
            "members": [{"target": t, "label": labels.get(t, t), "stability": stab[t],
                         "units": {k: full[k][1].get(t, 0) for k in full}} for t in members],
            "strongest_internal_pairs": [{"a": labels.get(a, a), "b": labels.get(b, b), "npmi": round(w, 3)}
                                         for w, a, b in internal],
        })
    report = {
        "method": {"MIN_PAIR": MIN_PAIR, "MIN_THEME": MIN_THEME, "BOOTSTRAPS": BOOTSTRAPS, "RESOLUTION": RESOLUTION,
                   "SEED": SEED, "stable_threshold": STABLE, "networkx": nx.__version__,
                   "series": args.series, "registry": args.registry},
        "signals": {k: {"units": sig[k].n, "qualifying_pairs": len(full[k][0])} for k in sig},
        "graph": {"themes": G.number_of_nodes(), "edges": G.number_of_edges(),
                  "themes_without_qualifying_pairs": sorted(set(themes) - set(G.nodes()))},
        "clusters": clusters,
        "validation": {
            "people_partition_scored_on_rih": heldout(single["people"], full["rih"][0]),
            "rih_partition_scored_on_people": heldout(single["rih"], full["people"][0]),
            "ari_people_vs_rih": ari(single["people"], single["rih"]),
            "ari_combined_vs_people": ari(part, single["people"]),
            "ari_combined_vs_rih": ari(part, single["rih"]),
            "resolution_sensitivity_ari": {str(r): ari(part, partition(G, resolution=r)) for r in (0.8, 1.2)},
            "unstable_members": sorted(labels.get(t, t) for t, v in stab.items() if v is not None and v < STABLE),
        },
    }
    out.mkdir(parents=True)
    (out / "clusters.json").write_text(json.dumps(report, indent=2) + "\n")
    with open(out / "pairs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["signal", "a", "b", "npmi", "co_occurrences"])
        for k, (wm, _) in full.items():
            for (a, b), (v, cnt) in sorted(wm.items()):
                w.writerow([k, a, b, round(v, 4), cnt])
    print(json.dumps({k: report[k] for k in ("signals", "graph", "validation")}, indent=1))
    for c in clusters:
        print(f"\n[{c['cluster']}] " + "; ".join(f"{m['label']} ({m['stability']})" for m in c["members"]))


if __name__ == "__main__":
    main()
