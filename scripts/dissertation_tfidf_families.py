#!/usr/bin/env python3
"""TF-IDF + NMF "families" of sources in the dissertation citation graph (prototype, 2026-10-20).

User idea (2026-10-20): weight each source by the company it keeps in a dissertation's
bibliography, "something like tf-idf", so that families of sources emerge despite the
randomness of any one bibliography. This script is a prototype beside the co-citation
fields of ``dissertation_citation_views.py``; it changes nothing in that pipeline.

Matrix (rows = dissertations, columns = works)
- Rows: strict History PhDs in scope (``in_analysis``; ``--country CC`` for a sub-graph,
  absent = the main graph; see ``dissertation_scope.py``) that cite at least ``--min-works``
  of the column works (default 3; fewer gives no usable mixture).
- Columns: scholarly works cited by at least ``--min-cited`` strict PhDs in scope (default
  15), with the same ``scholarly`` filter as the co-citation fields: no corporate or
  single-name first author, and not cited mainly (>= 50%) as a primary source. At the
  default this is exactly the co-citation field vocabulary (checked at run time).
- Cells: binary citation (a bibliography lists a work once; repetition carries no signal).
- IDF: smoothed, ``ln((1 + N) / (1 + df)) + 1`` (scikit-learn ``TfidfTransformer``), so a
  work cited by 15 PhDs weighs about three times one cited by 400: canonical works that
  everyone cites say little about which family a bibliography belongs to.
- Length: each row is L2-normalised after IDF, so a 600-entry bibliography and a
  60-entry one count equally (TF normalised by bibliography length, measured over the
  column works).

Families
- NMF on the TF-IDF matrix (Frobenius loss, coordinate descent, ``nndsvd`` init, which is
  deterministic). ``W`` (dissertations x families) and ``H`` (families x works).
- Scale-free memberships: a family's contribution to a work is ``colsum(W)_f * H[f, j]``
  and to a dissertation ``W[i, f] * rowsum(H)_f`` (its share of the reconstructed column or
  row). Normalised, these are the soft memberships; normalised entropy (0..1) of a work's
  membership is its bridge score.
- Choosing k: a sweep (``--k-min``..``--k-max`` step ``--k-step``) records reconstruction
  error (and its elbow, by maximum distance from the chord) and bootstrap stability:
  dissertations are resampled with replacement, TF-IDF and NMF are refitted, components are
  matched to the full-data fit by Hungarian assignment on the cosine of their work
  loadings, and the mean matched cosine is reported per k, with the number of families
  reproduced at >= 0.80. Rule: the k that reproduces the most families at >= 0.80, among
  the ks whose mean matched cosine is >= ``--min-mean-stability`` (0.75); ties go to the
  smaller k; if no k qualifies, the most stable k. (A first rule, "largest k at or after the
  elbow with mean >= 0.80", found no qualifying k: the error curve is nearly linear, as is
  usual for sparse binary data, and mean stability never reaches 0.80.) Families whose own
  matched cosine is below 0.6 are flagged ``unstable`` in ``families.json``.
  ``--k`` fixes k (the sweep is then skipped, but the chosen k is still bootstrapped).

Outputs (``summary/tfidf-families/`` for the main graph, ``summary/countries/<CC>/tfidf-families/``):
``families.json``, ``work-profiles.csv``, ``dissertation-mixtures.csv``, ``sweep.csv``,
``comparison.json`` (against the Louvain co-citation fields at their own settings) and
``coupling.json`` (bibliographic coupling of dissertations vs. NMF dominant families).
``--variant NAME`` writes a parameter variant to ``tfidf-families/variants/NAME/`` instead.
Labels are provisional (first-author surnames of the top works plus distinctive title terms,
and the best-matching Louvain field label as a hint); nothing here is an editorial label.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import re
import sys
import time

import networkx as nx
from networkx.algorithms.community import louvain_communities
import numpy as np
from scipy import sparse
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dissertation_citation_views import fields, first_author, load  # noqa: E402
from dissertation_scope import add_scope_argument, in_scope, strict_count, summary_dir  # noqa: E402

DEFAULT_OUT = Path(__file__).resolve().parent.parent / 'data/field-research/dissertation-citations-2026-10-11'
STOP = set('''a an the and or of in on at to for from by with without into over under between among as its his her their our
their is are was were be being been this that these those it how why what who whom which new history histories historical
study studies essays essay reader introduction selected writings papers volume vol ed eds edition part
le la les de des du et en un une au aux pour par sur dans d l à the canada canadian'''.split())


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- matrix
def scholarly_works(nodes, authored, min_cited, country):
    """Same filter as ``fields()`` in dissertation_citation_views.py (copied, not changed)."""
    def scholarly(w):
        n = nodes[w]
        ca = n['cited_as']
        a = first_author(nodes, authored, w)
        return a and a['name_key_kind'] != 'corporate_or_single_name' and ca.get('primary', 0) / (sum(ca.values()) or 1) < 0.5
    return {w for w, n in nodes.items() if n['type'] == 'Work' and strict_count(n, country) >= min_cited and scholarly(w)}


def build_matrix(diss, cites, works, min_works):
    cols = sorted(works)
    col = {w: j for j, w in enumerate(cols)}
    rows, r, c = [], [], []
    for d in sorted(diss):
        hit = sorted(col[w] for w in cites[d] if w in col)
        if len(hit) < min_works:
            continue
        i = len(rows)
        rows.append(d)
        r.extend([i] * len(hit))
        c.extend(hit)
    B = sparse.csr_matrix((np.ones(len(r)), (r, c)), shape=(len(rows), len(cols)))
    return rows, cols, B


def tfidf(B):
    return TfidfTransformer(norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False).fit_transform(B)


def fit_nmf(X, k, seed, init='nndsvd', max_iter=800):
    m = NMF(n_components=k, init=init, random_state=seed, max_iter=max_iter, tol=1e-4, solver='cd', beta_loss='frobenius')
    W = m.fit_transform(X)
    return m, W, m.components_


def unit_rows(H):
    return H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-12)


def match(H_ref, H_new):
    """Hungarian matching of components by cosine of work loadings; returns cosine per reference component."""
    S = unit_rows(H_ref) @ unit_rows(H_new).T
    ri, ci = linear_sum_assignment(-S)
    out = np.zeros(H_ref.shape[0])
    out[ri] = S[ri, ci]
    return out


def bootstrap(B, k, H_ref, n, seed):
    rng = np.random.default_rng(seed)
    sims = []
    for b in range(n):
        idx = rng.integers(0, B.shape[0], B.shape[0])
        _, _, H = fit_nmf(tfidf(B[idx]), k, seed)
        sims.append(match(H_ref, H))
    return np.array(sims)  # n x k


def elbow(ks, errs):
    """Knee by maximum distance from the chord joining the first and last points (normalised axes)."""
    x = (np.array(ks) - ks[0]) / ((ks[-1] - ks[0]) or 1)
    y = (np.array(errs) - errs[-1]) / ((errs[0] - errs[-1]) or 1)
    d = np.abs(y - (1 - x)) / math.sqrt(2)  # chord from (0, 1) to (1, 0)
    return ks[int(np.argmax(d))]


def memberships(W, H):
    work_contrib = W.sum(axis=0)[:, None] * H            # k x works
    diss_contrib = W * H.sum(axis=1)[None, :]            # diss x k
    wp = work_contrib / (work_contrib.sum(axis=0, keepdims=True) + 1e-12)
    dp = diss_contrib / (diss_contrib.sum(axis=1, keepdims=True) + 1e-12)
    return wp.T, dp, work_contrib.sum(axis=0)          # works x k, diss x k, reconstructed column mass


def norm_entropy(P):
    k = P.shape[1]
    Q = np.clip(P, 1e-12, 1)
    return -(P * np.log(Q)).sum(axis=1) / math.log(k)


def title_terms(titles_weights, all_titles_df, n=6):
    score = Counter()
    seen = Counter()
    for t, wgt in titles_weights:
        toks = set(re.findall(r"[a-zà-ÿ]{3,}", (t or '').lower())) - STOP
        for tok in toks:
            score[tok] += wgt
            seen[tok] += 1
    ranked = sorted((tok for tok in score if seen[tok] >= 2), key=lambda tok: -score[tok] / math.sqrt(all_titles_df[tok]))
    return ranked[:n]


def surname(name):
    return (name or '').split(',')[0].strip()


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT, help='dissertation-citations directory (holds graph.json)')
    add_scope_argument(ap)
    ap.add_argument('--min-cited', type=int, default=15)
    ap.add_argument('--min-works', type=int, default=3, help='a dissertation needs this many column works to be a row')
    ap.add_argument('--k', type=int, default=None, help='fix k (skips the sweep)')
    ap.add_argument('--k-min', type=int, default=8)
    ap.add_argument('--k-max', type=int, default=30)
    ap.add_argument('--k-step', type=int, default=2)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--bootstrap', type=int, default=20, help='bootstrap refits per k')
    ap.add_argument('--stability-threshold', type=float, default=0.80, help='a family is reproduced at this matched cosine')
    ap.add_argument('--min-mean-stability', type=float, default=0.75)
    ap.add_argument('--variant', default=None, help='write to tfidf-families/variants/<NAME>/ (for parameter variants)')
    ap.add_argument('--knn', type=int, default=15, help='neighbours per dissertation in the coupling graph')
    ap.add_argument('--bridges', nargs='*', default=['The Middle Ground', 'Imagined Communities', 'Orientalism',
                    'Discipline and Punish', 'The Making of the English Working Class', 'Seeing Like a State',
                    'Gender and the Politics of History', 'Facing East from Indian Country', 'Britons',
                    'The Liberal Order Framework', 'Many Tender Ties', 'Colonizing Bodies'])
    args = ap.parse_args()
    t0 = time.time()
    dest = summary_dir(args.out, args.country) / 'tfidf-families'
    if args.variant:
        dest = dest / 'variants' / args.variant
    dest.mkdir(parents=True, exist_ok=True)

    log('loading graph', args.out / 'graph.json', 'scope', args.country or 'main')
    g, nodes, diss, cites, authored, sup = load(args.out, args.country)
    del g
    works = scholarly_works(nodes, authored, args.min_cited, args.country)
    rows, cols, B = build_matrix(diss, cites, works, args.min_works)
    N, V = B.shape
    log(f'{len(diss)} strict PhDs in scope; {N} rows with >= {args.min_works} column works; {V} works; nnz {B.nnz}')
    X = tfidf(B)
    df = np.asarray(B.sum(axis=0)).ravel()

    # ---- k sweep ------------------------------------------------------------------
    sweep = []
    ks = [args.k] if args.k else list(range(args.k_min, args.k_max + 1, args.k_step))
    fits = {}
    for k in ks:
        m, W, H = fit_nmf(X, k, args.seed)
        sims = bootstrap(B, k, H, args.bootstrap, args.seed + 1) if args.bootstrap else np.ones((1, k))
        per_family = sims.mean(axis=0)
        fits[k] = (m, W, H, per_family)
        row = dict(k=k, reconstruction_error=round(float(m.reconstruction_err_), 4),
                   relative_error=round(float(m.reconstruction_err_ / sparse.linalg.norm(X)), 4),
                   iterations=int(m.n_iter_), stability_mean=round(float(sims.mean()), 3),
                   stability_median_family=round(float(np.median(per_family)), 3),
                   stability_p10_family=round(float(np.quantile(per_family, 0.1)), 3),
                   stability_min_family=round(float(per_family.min()), 3),
                   families_reproduced=int((per_family >= args.stability_threshold).sum()))
        sweep.append(row)
        log('k', k, {kk: v for kk, v in row.items() if kk != 'k'})
    if args.k:
        k_star, k_elbow, rule = args.k, None, 'fixed by --k'
    else:
        k_elbow = elbow(ks, [r['reconstruction_error'] for r in sweep]) if len(ks) > 2 else None
        ok = [r for r in sweep if r['stability_mean'] >= args.min_mean_stability]
        if ok:
            k_star = min(ok, key=lambda r: (-r['families_reproduced'], r['k']))['k']
            rule = (f'most families reproduced at matched cosine >= {args.stability_threshold}, among ks with mean matched cosine '
                    f'>= {args.min_mean_stability}; ties to the smaller k')
        else:
            k_star = max(sweep, key=lambda r: r['stability_mean'])['k']
            rule = f'no k had mean matched cosine >= {args.min_mean_stability}: most stable k'
    with (dest / 'sweep.csv').open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(sweep[0]) + ['elbow', 'chosen'])
        wr.writeheader()
        for r in sweep:
            wr.writerow({**r, 'elbow': r['k'] == k_elbow, 'chosen': r['k'] == k_star})
    log('chosen k', k_star, '|', rule)

    m, W, H, fam_stab = fits[k_star]
    # init sensitivity: random-init refits on the full data, matched to the nndsvd fit
    init_sims = np.array([match(H, fit_nmf(X, k_star, s, init='nndsvda' if s == 0 else 'random')[2]) for s in range(5)])
    wp, dp, col_mass = memberships(W, H)
    work_top = wp.argmax(axis=1)
    order2 = np.argsort(-wp, axis=1)
    went = norm_entropy(wp)
    dom = dp.argmax(axis=1)
    n_rows_works = np.asarray(B.sum(axis=1)).ravel()

    # order families by number of dominated dissertations
    sizes = Counter(dom.tolist())
    fam_order = sorted(range(k_star), key=lambda f: (-sizes.get(f, 0), f))
    remap = {old: new for new, old in enumerate(fam_order)}
    H, W, wp, dp, fam_stab = H[fam_order], W[:, fam_order], wp[:, fam_order], dp[:, fam_order], fam_stab[fam_order]
    init_stab = init_sims[:, fam_order].mean(axis=0)
    work_top = np.array([remap[x] for x in work_top])
    order2 = np.argsort(-wp, axis=1)
    dom = np.array([remap[x] for x in dom])

    count = {w: strict_count(nodes[w], args.country) for w in cols}
    all_titles_df = Counter()
    for w in cols:
        all_titles_df.update(set(re.findall(r"[a-zà-ÿ]{3,}", (nodes[w]['title'] or '').lower())) - STOP)
    fa_name = {w: (first_author(nodes, authored, w) or {}).get('name', '') for w in cols}

    # ---- Louvain fields at their own settings (views.json) -------------------------
    log('Louvain co-citation fields (min_cited 15, as in views.json)')
    lw, lcount, G, groups, field_of, *_ = fields(nodes, diss, cites, authored, 15, country=args.country)
    if args.min_cited == 15:
        assert lw == works, 'scholarly filter drifted from dissertation_citation_views.fields()'
    labels_path = summary_dir(args.out, args.country) / 'field-labels.csv'
    flabel = {}
    if labels_path.exists():
        with labels_path.open(newline='') as f:
            flabel = {r['anchor_work']: r['label'] for r in csv.DictReader(f)}
    lnames = [flabel.get(grp[0], ' · '.join(dict.fromkeys(surname(fa_name.get(w) or (first_author(nodes, authored, w) or {}).get('name', '')) for w in grp[:3])))
              for grp in groups]
    lsets = [set(grp) for grp in groups]
    engaged = [{d for d in rows if len(cites[d] & s) >= 3} for s in lsets]
    col_idx = {w: j for j, w in enumerate(cols)}

    # ---- families -------------------------------------------------------------------
    years = {d: diss[d].get('year') for d in rows}
    bins = lambda y: f'{(y // 5) * 5}-{(y // 5) * 5 + 4}' if y else 'unknown'
    bin_total = Counter(bins(years[d]) for d in rows)
    fams, comp_rows = [], []
    for f in range(k_star):
        top = np.argsort(-H[f])[:25]
        hsum = H[f].sum()
        members = {cols[j] for j in np.where(work_top == f)[0]}
        people = defaultdict(float)
        for j in np.argsort(-H[f])[:300]:
            if fa_name[cols[j]]:
                people[fa_name[cols[j]]] += H[f, j] / hsum
        dominated = [rows[i] for i in np.where(dom == f)[0]]
        yb = Counter(bins(years[d]) for d in dominated)
        yrs = sorted(y for y in (years[d] for d in dominated) if y)
        terms = title_terms([(nodes[cols[j]]['title'], H[f, j]) for j in np.argsort(-H[f])[:40]], all_titles_df)
        # comparison with Louvain
        topset = {cols[j] for j in top}
        by_members = [(len(members & s) / len(members | s) if members | s else 0) for s in lsets]
        by_top = [len(topset & s) / len(topset | s) for s in lsets]
        top_in = [len(topset & s) / len(topset) for s in lsets]
        dset = set(dominated)
        by_diss = [(len(dset & e) / len(dset | e) if dset | e else 0) for e in engaged]
        bm, bt, bd = int(np.argmax(by_members)), int(np.argmax(by_top)), int(np.argmax(by_diss))
        auto = ' · '.join(dict.fromkeys(surname(fa_name[cols[j]]) for j in top[:3]))
        fams.append(dict(
            id=f,
            provisional_label=auto + (' — ' + ', '.join(terms[:4]) if terms else ''),
            label_is_provisional=True,
            louvain_hint=lnames[bm] if by_members[bm] >= 0.2 else None,
            title_terms=terms,
            bootstrap_stability=round(float(fam_stab[f]), 3),
            unstable=bool(fam_stab[f] < 0.6),
            init_stability=round(float(init_stab[f]), 3),
            dominated_dissertations=len(dominated),
            member_works=len(members),
            years=dict(median=yrs[len(yrs) // 2] if yrs else None, by_5yr={b: yb[b] for b in sorted(yb)},
                       share_of_bin={b: round(yb[b] / bin_total[b], 3) for b in sorted(yb) if bin_total[b] >= 30}),
            top_works=[dict(id=cols[j], title=nodes[cols[j]]['title'], first_author=fa_name[cols[j]], year=nodes[cols[j]].get('year'),
                            loading=round(float(H[f, j] / H[f].max()), 3), citing=count[cols[j]],
                            membership=round(float(wp[j, f]), 3)) for j in top],
            top_people=[dict(name=p, loading_share=round(v, 4)) for p, v in sorted(people.items(), key=lambda kv: -kv[1])[:15]],
            top_institutions=Counter(diss[d]['institution'] for d in dominated).most_common(6),
            sample_dissertations=[diss[rows[i]]['title'][:140] for i in np.argsort(-dp[:, f])[:8]],
        ))
        comp_rows.append(dict(
            family=f, label=fams[-1]['provisional_label'], dominated=len(dominated), member_works=len(members),
            best_by_member_works=dict(field=lnames[bm], field_id=bm, jaccard=round(by_members[bm], 3), field_size=len(lsets[bm])),
            best_by_top25=dict(field=lnames[bt], field_id=bt, jaccard=round(by_top[bt], 3), top25_inside=round(top_in[bt], 2)),
            best_by_dissertations=dict(field=lnames[bd], field_id=bd, jaccard=round(by_diss[bd], 3), engaged=len(engaged[bd])),
            top25_spread=[[lnames[i], round(v, 2)] for i, v in sorted(enumerate(top_in), key=lambda t: -t[1]) if v >= 0.12],
        ))
    # reverse view: each Louvain field's best NMF family
    fam_members = [{cols[j] for j in np.where(work_top == f)[0]} for f in range(k_star)]
    reverse = []
    for i, s in enumerate(lsets):
        jac = [len(s & mset) / len(s | mset) for mset in fam_members]
        spread = Counter(int(work_top[col_idx[w]]) for w in s if w in col_idx)
        b = int(np.argmax(jac))
        reverse.append(dict(field=lnames[i], field_id=i, works=len(s), best_family=b, family_label=fams[b]['provisional_label'],
                            jaccard=round(jac[b], 3), work_spread=[[f, n] for f, n in spread.most_common(4)]))

    shared = [w for w in cols if w in field_of]
    ari = adjusted_rand_score([field_of[w] for w in shared], [int(work_top[col_idx[w]]) for w in shared])
    nmi = normalized_mutual_info_score([field_of[w] for w in shared], [int(work_top[col_idx[w]]) for w in shared])
    # Louvain link-split entropy (views.json's link_split) vs NMF entropy
    def link_entropy(w):
        by = Counter()
        for x, d in G[w].items():
            by[field_of.get(x, -1)] += d['weight']
        tot = sum(by.values())
        if not tot:
            return None
        p = np.array([v / tot for v in by.values()])
        return float(-(p * np.log(p)).sum() / math.log(max(2, len(groups) + 1)))
    le = [(went[col_idx[w]], link_entropy(w)) for w in cols if w in G]
    le = [(a, b) for a, b in le if b is not None]
    from scipy.stats import spearmanr
    rho = spearmanr([a for a, _ in le], [b for _, b in le]).statistic if le else None
    unclustered = [w for w in cols if w in lw and w not in field_of]

    def wdesc(w):
        j = col_idx[w]
        return dict(title=nodes[w]['title'], first_author=fa_name[w], citing=count[w], entropy=round(float(went[j]), 3),
                    nmf_top=int(order2[j, 0]), nmf_top_share=round(float(wp[j, order2[j, 0]]), 2),
                    nmf_second=int(order2[j, 1]), nmf_second_share=round(float(wp[j, order2[j, 1]]), 2),
                    louvain=lnames[field_of[w]] if w in field_of else 'unclustered')
    named = {}
    for prefix in args.bridges:
        cand = sorted((w for w in cols if (nodes[w]['title'] or '').lower().startswith(prefix.lower())), key=lambda w: -count[w])
        if cand:
            named[prefix] = wdesc(cand[0])
    bridges = [wdesc(cols[j]) for j in np.argsort(-went) if count[cols[j]] >= 30][:30]
    comparison = dict(
        louvain_settings='min_cited 15, cosine >= 0.12, pair support >= 3, 40 Louvain runs at resolution 1.5, 80% consensus',
        louvain_fields=len(groups), louvain_clustered=sum(len(s) for s in lsets), louvain_vocabulary=len(lw),
        nmf_vocabulary=V, shared_works=len(shared),
        work_assignment_agreement=dict(adjusted_rand=round(float(ari), 3), nmi=round(float(nmi), 3),
                                       note='NMF top family vs Louvain field, over works clustered by Louvain and in the NMF vocabulary'),
        entropy_vs_louvain_link_split_spearman=round(float(rho), 3) if rho is not None else None,
        families=comp_rows, louvain_to_nmf=reverse,
        louvain_unclustered_works=[wdesc(w) for w in sorted(unclustered, key=lambda w: -count[w]) if w in col_idx][:40],
        named_works=named, bridges_top30=bridges)

    # ---- bibliographic coupling ----------------------------------------------------
    log('bibliographic coupling')
    S = (X @ X.T).toarray()
    np.fill_diagonal(S, 0)
    K = nx.Graph()
    K.add_nodes_from(range(N))
    nn = np.argsort(-S, axis=1)[:, :args.knn]
    for i in range(N):
        for j in nn[i]:
            if S[i, j] > 0:
                K.add_edge(i, int(j), weight=float(S[i, j]))
    coupling = dict(knn=args.knn, rows=N)
    for res in (1.0, 1.5):
        comms = louvain_communities(K, weight='weight', resolution=res, seed=args.seed)
        lab = np.zeros(N, int)
        for c, mem in enumerate(sorted(comms, key=len, reverse=True)):
            lab[list(mem)] = c
        tab = []
        for c in range(len(comms)):
            idx = np.where(lab == c)[0]
            if len(idx) < 20:
                continue
            fc = Counter(dom[idx].tolist()).most_common(2)
            tab.append(dict(cluster=c, size=len(idx), main_family=fc[0][0], purity=round(fc[0][1] / len(idx), 2),
                            second=fc[1] if len(fc) > 1 else None))
        coupling[f'louvain_knn_res{res}'] = dict(clusters=len(comms), clusters_ge20=len(tab),
                                                 adjusted_rand=round(float(adjusted_rand_score(dom, lab)), 3),
                                                 nmi=round(float(normalized_mutual_info_score(dom, lab)), 3),
                                                 purity_weighted=round(sum(t['purity'] * t['size'] for t in tab) / max(1, sum(t['size'] for t in tab)), 3),
                                                 table=tab)
    Xd = X.toarray()
    agg = AgglomerativeClustering(n_clusters=k_star, linkage='ward').fit_predict(Xd)
    coupling['ward_k'] = dict(clusters=k_star, adjusted_rand=round(float(adjusted_rand_score(dom, agg)), 3),
                              nmi=round(float(normalized_mutual_info_score(dom, agg)), 3),
                              sizes=sorted(Counter(agg.tolist()).values(), reverse=True))
    # does a dissertation's nearest coupled neighbour share its dominant family?
    nn1 = nn[:, 0]
    base_rate = sum((c / N) ** 2 for c in Counter(dom.tolist()).values())
    coupling['nearest_neighbour_same_family'] = dict(share=round(float((dom[nn1] == dom).mean()), 3), chance=round(base_rate, 3))
    coupling['note'] = 'Dissertation clusters from cosine on TF-IDF rows (bibliographic coupling) against NMF dominant families.'

    # ---- write ------------------------------------------------------------------
    with (dest / 'work-profiles.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'title', 'first_author', 'year', 'citing', 'idf', 'top_family', 'top_share', 'second_family',
                     'second_share', 'entropy', 'louvain_field'] + [f'f{x}' for x in range(k_star)])
        idf = np.log((1 + N) / (1 + df)) + 1
        for j in np.argsort(-went):
            w = cols[j]
            wr.writerow([w, nodes[w]['title'], fa_name[w], nodes[w].get('year'), count[w], round(float(idf[j]), 3),
                         int(order2[j, 0]), round(float(wp[j, order2[j, 0]]), 3), int(order2[j, 1]), round(float(wp[j, order2[j, 1]]), 3),
                         round(float(went[j]), 3), lnames[field_of[w]] if w in field_of else ('unclustered' if w in lw else 'not in Louvain vocabulary')]
                        + [round(float(x), 4) for x in wp[j]])
    with (dest / 'dissertation-mixtures.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['dissertation_id', 'title', 'year', 'institution', 'country', 'column_works', 'dominant_family', 'dominant_share',
                     'entropy'] + [f'f{x}' for x in range(k_star)])
        dent = norm_entropy(dp)
        for i, d in enumerate(rows):
            n = diss[d]
            wr.writerow([d, n['title'], n.get('year'), n.get('institution'), n.get('country'), int(n_rows_works[i]), int(dom[i]),
                         round(float(dp[i, dom[i]]), 3), round(float(dent[i]), 3)] + [round(float(x), 4) for x in dp[i]])
    excluded = sorted(set(diss) - set(rows))
    meta = dict(
        scope=args.country or 'main', generated=time.strftime('%Y-%m-%d'), script='scripts/dissertation_tfidf_families.py',
        strict_dissertations_in_scope=len(diss), rows=N, rows_excluded_lt_min_works=len(diss) - N, works=V,
        excluded_profile=dict(by_institution=Counter(diss[d]['institution'] for d in excluded).most_common(12),
                              by_country=Counter(diss[d].get('country') for d in excluded).most_common(),
                              by_decade=sorted(Counter((diss[d].get('year') or 0) // 10 * 10 for d in excluded).items()),
                              share_by_institution={i: round(sum(diss[d]['institution'] == i for d in excluded) / n, 2)
                                                    for i, n in Counter(diss[d]['institution'] for d in diss).most_common(12)},
                              median_bibliography_entries=sorted(diss[d].get('bibliography_entries') or 0 for d in excluded)[len(excluded) // 2] if excluded else None,
                              median_bibliography_entries_rows=sorted(diss[d].get('bibliography_entries') or 0 for d in rows)[len(rows) // 2]),
        parameters=dict(min_cited=args.min_cited, min_works=args.min_works, seed=args.seed, bootstrap=args.bootstrap,
                        tfidf='binary tf, smoothed idf ln((1+N)/(1+df))+1, row L2 norm',
                        nmf='frobenius, cd solver, nndsvd init, max_iter 800, tol 1e-4'),
        k=k_star, k_rule=rule, elbow=k_elbow, sweep=sweep,
        stability=dict(bootstrap_mean=round(float(fam_stab.mean()), 3), init_random_mean=round(float(init_stab.mean()), 3),
                       note='bootstrap: mean matched cosine of work loadings over resampled refits; init: 4 random-init + 1 nndsvda refit'),
        membership_note='soft memberships are each family\'s share of the reconstructed column (works) or row (dissertations)',
        families=fams)
    (dest / 'families.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
    (dest / 'comparison.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=1) + '\n')
    (dest / 'coupling.json').write_text(json.dumps(coupling, ensure_ascii=False, indent=1) + '\n')

    # ---- printed summary -------------------------------------------------------------
    log(f'k={k_star} rows={N} works={V} stability={fam_stab.mean():.3f} init={init_stab.mean():.3f} ARI={ari:.3f} NMI={nmi:.3f} '
        f'entropy~linksplit rho={rho if rho is None else round(rho, 3)}')
    for fam, c in zip(fams, comp_rows):
        print(f"F{fam['id']:>2} n={fam['dominated_dissertations']:4} stab={fam['bootstrap_stability']:.2f}{'!' if fam['unstable'] else ' '}"
              f"{fam['provisional_label'][:70]:70} | L: {c['best_by_member_works']['field'][:38]} J={c['best_by_member_works']['jaccard']:.2f}"
              f" dJ={c['best_by_dissertations']['jaccard']:.2f}")
        print('     ', ' ; '.join(f"{w['title'][:45]} ({surname(w['first_author'])})" for w in fam['top_works'][:5]))
    print('coupling', json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'table'} if isinstance(v, dict) else v for k, v in coupling.items()}))
    print('named', json.dumps(named, ensure_ascii=False, indent=0)[:4000])
    log(f'done in {time.time() - t0:.0f}s -> {dest}')


if __name__ == '__main__':
    main()
