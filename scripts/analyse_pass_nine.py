"""Pass nine measurement (ARCHITECTURE.md section 8 class 38) on one or both classes: the three evidence kinds (subject
ratio, subfield / same journal, ties), rule C and their combinations, on masked gold (fire rate on true pairs), the
masked-author namesake test (fire rate on proven namesakes) and the clerical labels; estimated wrong-link share in
production by name band = absent share x namesake fire rate / production fire rate, with its upper 95% bound.
Inputs: link_work_people.py link ... --out-tag=TAG outputs (results/gold/namesake TAG .parquet and positions*.parquet in
the scratch). A run is SCRATCH:TAG:OLDTAG:TABLE; OLDTAG (may be empty) merges the x: signals of an earlier run of the same
positions (the name-only -p9 run lost its pass-eight signals to a bug since fixed).

    python3 scripts/analyse_pass_nine.py --out report.json --sc-positions SC/positions.parquet \
        --run NO_SCRATCH:-p9:-big:no --run WP_SCRATCH:-p9::wp

Written 2026-11-13 from the pass-nine scratch analysis (analyse9.py). Reports each class alone and both pooled.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = str(Path(__file__).resolve().parents[1])
A_SHARE = {'unique': 0.06, '2-5': 0.06, '6-25': 0.29, '26+': 0.40}
db = duckdb.connect()
db.execute("SET memory_limit='6GB'; SET threads=4")
prod, gold, ns, clerical = [], [], [], []


def xparse(sig):
    d = {}
    for t in (sig or '').split():
        if t.startswith('x:'):
            k, _, v = t[2:].partition('=')
            d[k] = v if v else True
    return d

def band(b):
    return 'unique' if b <= 1 else '2-5' if b <= 5 else '6-25' if b <= 25 else '26+'

def upper95(k, n):
    """one-sided 95% Clopper-Pearson upper bound"""
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        # P(X <= k | n, mid)
        s = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k + 1)) if n <= 1000 else None
        if s is None:
            mu, sd = n * mid, math.sqrt(n * mid * (1 - mid))
            s = 0.5 * (1 + math.erf((k + 0.5 - mu) / (sd * math.sqrt(2))))
        if s > 0.05:
            lo = mid
        else:
            hi = mid
    return hi

def wilson(k, n):
    if n == 0:
        return (0.0, 1.0)
    z = 1.96
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0, c - h), min(1, c + h))


def S(sig):
    x = xparse(sig)
    if 'lrs' not in x or 'lco' not in x:
        return None
    f = lambda k, d=0.0: float(x.get(k, d)) if x.get(k) not in (True, None) else d
    lco, lcdp, oa = int(x['lco']), int(x['lcdp']), int(x['oa'])
    return dict(name=x['name'], band=band(max(lco + 1, oa)), lco=lco, lcdp=lcdp, oa=oa, lcact=int(x.get('lcact', lcdp)),
                scholar=bool(x.get('scholar')), venue=x['venue'], win=x['win'], rl=bool(x.get('author-review')),
                rv=int(x['rv']), rvby=x['rvby'], ct=int(x['ct']), cck=int(x['cck']), cca=int(x['cca']), lrs=f('lrs'),
                lrf=f('lrf'), psz=int(x['psz']), pth=x['pth'] == '1', lro=f('lro'), vrep=int(x['vrep']), nothers=int(x['nothers']))


def M(sig):
    m = dict(re.findall(r'x2:(\w+)=(\S+)', sig or ''))
    if 'best' not in m:
        return None
    return dict(best=float(m['best']), second=float(m['second']), bestkey=m['bestkey'], n=int(m['n']))



def xs(sig):
    return ' '.join(t for t in (sig or '').split() if t.startswith('x:'))


def load(runs, SC):
    global clerical
    for scr, tag, OLD, tbl in runs:
        o_r, o_g, o_n = {}, {}, {}
        if OLD:
            o_r = dict(db.execute(f"SELECT pid, signals FROM '{scr}/results{OLD}.parquet'").fetchall())
            o_g = {(a, b): c for a, b, c in db.execute(f"SELECT pid, dup, sig FROM '{scr}/gold{OLD}.parquet'").fetchall()}
            o_n = {(a, b, c): d for a, b, c, d in db.execute(f"SELECT pid, test, proven, sig FROM '{scr}/namesake{OLD}.parquet'").fetchall()}
        for pid, st, key, br, cands, n, sig, already, work, role, pos, kind in db.execute(f"""SELECT r.pid, r.state, r.key, r.branch,
                r.candidates, r.n_candidates, r.signals, r.already_credited, p.work, p.role, p.pos, p.kind
                FROM '{scr}/results{tag}.parquet' r JOIN '{scr}/positions*.parquet' p USING (pid)""").fetchall():
            if already:
                continue
            sig = xs(o_r.get(pid)) + ' ' + (sig or '')
            prod.append(dict(tbl=tbl, pid=pid, state=st, key=key, branch=br, cands=cands, n=n, s=S(sig), m=M(sig), work=work,
                             role=role, pos=pos, kind=kind))
        for pid, role, half, true, st, key, cands, n, br, sig in db.execute(f"""SELECT pid, role, half, "true", state, key, cands, n_live, branch, sig
                FROM '{scr}/gold{tag}.parquet' WHERE dup""").fetchall():
            sig = xs(o_g.get((pid, True))) + ' ' + (sig or '')
            gold.append(dict(tbl=tbl, role=role, half=half, true=true, state=st, cands=cands, n=n, branch=br, s=S(sig), m=M(sig)))
        for pid, test, role, true, proven, st, cands, br, sig in db.execute(f"""SELECT pid, test, role, "true", proven, state, cands, branch, sig
                FROM '{scr}/namesake{tag}.parquet'""").fetchall():
            sig = xs(o_n.get((pid, test, proven))) + ' ' + (sig or '')
            ns.append(dict(tbl=tbl, test=test, role=role, true=true, proven=proven, state=st, cands=cands, branch=br, s=S(sig), m=M(sig),
                           half=None))
    for x in ns:
        x['half'] = int(hashlib.md5((x['true'] or x['proven']).encode()).hexdigest()[:8], 16) % 2

    cl = db.execute(f"""SELECT c.split, c.label_judged, c.duplicate_keys, p.tbl, p.work, p.role, p.pos, c.item
            FROM read_csv('{ROOT}/data/graph/scored-links/clerical-labels.csv') c JOIN '{SC}' p USING (pid)""").fetchall()
    pidx = {(r['tbl'], r['work'], r['role'], r['pos']): r for r in prod}
    clerical = [dict(split=sp, label=lab, dups=set((d or '').replace(';', '|').split('|')) - {''}, r=pidx.get((t, w, ro, po)), item=it)
                for sp, lab, d, t, w, ro, po, it in cl]
    return prod, gold, ns, clerical


def single(r):
    return r['state'] == 'possible' and r['s'] is not None and len((r['cands'] or '').split('|')) == 1


def profok(s):
    return s['psz'] >= 3 or s['pth']


# the three kinds as predicates at named levels
KINDS = {}
for t in (2, 3, 4, 5, 6, 8, 10, 12):
    KINDS[f'K1:lrs>={t}'] = (lambda t: lambda s: not s['rl'] and profok(s) and s['lrs'] >= t)(t)
for t in (1, 2, 3, 4, 6):
    KINDS[f'K2:lrf>={t}'] = (lambda t: lambda s: not s['rl'] and profok(s) and s['lrf'] >= t)(t)
KINDS['K2:vrep>=1'] = lambda s: not s['rl'] and s['vrep'] >= 1
KINDS['K2:vrep>=2'] = lambda s: not s['rl'] and s['vrep'] >= 2
for t in (1, 2, 3):
    KINDS[f'K2:lrf>={t}|vrep'] = (lambda t: lambda s: not s['rl'] and ((profok(s) and s['lrf'] >= t) or s['vrep'] >= 1))(t)
KINDS['K3:review-linked+'] = lambda s: s['rv'] >= 1
KINDS['K3:review-keylog'] = lambda s: s['rv'] >= 2
KINDS['K3:review-editor'] = lambda s: s['rv'] >= 1 and s['rvby'] == 'ed'
KINDS['K3:cites-any'] = lambda s: s['ct'] >= 1
KINDS['K3:cites-keylog'] = lambda s: s['ct'] >= 2
for t in (1, 2, 3, 5, 10):
    KINDS[f'K3:cocite>={t}'] = (lambda t: lambda s: s['cca'] >= t)(t)
KINDS['K3:review|cites'] = lambda s: s['rv'] >= 1 or s['ct'] >= 1
for t in (2, 3, 5):
    KINDS[f'K3:review|cites|cocite>={t}'] = (lambda t: lambda s: s['rv'] >= 1 or s['ct'] >= 1 or s['cca'] >= t)(t)
KINDS['C:active-rare'] = lambda s: s['name'] == 'full' and s['lco'] > 0 and s['lcact'] == 0 and s['oa'] <= 20


def ev(pred, name_full=True, gset=None, nset=None, pset=None):
    ok = (lambda s: pred(s) and (s['name'] == 'full' or not name_full))
    gset = gset if gset is not None else [g for g in gold if single(g)]
    nset = nset if nset is not None else [x for x in ns if x['test'] == 'masked-author' and single(x)]
    pset = pset if pset is not None else [r for r in prod if single(r)]
    res = {}
    gf = [g for g in gset if ok(g['s'])]
    gw = sum(1 for g in gf if g['cands'] != g['true'])
    res['gold'] = dict(eligible=len(gset), fires=len(gf), fire_rate=round(len(gf) / len(gset), 4) if gset else None, wrong=gw,
                       upper95=round(upper95(gw, len(gf)), 4) if gf else None)
    nf = [x for x in nset if ok(x['s'])]
    res['masked_author'] = dict(eligible=len(nset), fires=len(nf), fire_rate=round(len(nf) / len(nset), 5) if nset else None,
                                examples=[(x['proven'], x['true']) for x in nf[:6]])
    on = [x for x in ns if x['test'] == 'orcid-namesake' and single(x)]
    res['orcid_namesake'] = dict(eligible=len(on), fires=sum(1 for x in on if ok(x['s'])))
    dest, tot, tot_up, nfire = {}, 0.0, 0.0, 0
    for b in ('unique', '2-5', '6-25', '26+'):
        pe = [r for r in pset if r['s']['band'] == b]
        pf = sum(1 for r in pe if ok(r['s']))
        ne = [x for x in nset if x['s']['band'] == b]
        ge = [g for g in gset if g['s']['band'] == b]
        k = sum(1 for x in ne if ok(x['s']))
        gk = sum(1 for g in ge if ok(g['s']))
        if not pe:
            continue
        f = pf / len(pe) if pf else 0
        a = A_SHARE[b]
        q, qu = (k / len(ne) if ne else None), upper95(k, len(ne))
        e = min(1.0, a * q / f) if (q is not None and f) else None
        eu = min(1.0, a * qu / f) if f else None
        dest[b] = dict(prod_eligible=len(pe), prod_fires=pf, gold_fire_rate=round(gk / len(ge), 4) if ge else None,
                       masked_eligible=len(ne), masked_fires=k, masked_fire_rate=round(q, 5) if q is not None else None,
                       est=round(e, 4) if e is not None else None, upper95=round(eu, 4) if eu is not None else None)
        if pf:
            tot += (e or 0) * pf
            tot_up += eu * pf
            nfire += pf
    res['by_band'] = dest
    res['production_fires'] = nfire
    res['est_wrong'] = round(tot / nfire, 4) if nfire else None
    res['est_wrong_upper95'] = round(tot_up / nfire, 4) if nfire else None
    for split in ('clerical-dev', 'clerical-test'):
        cs = [c for c in clerical if c['split'] == split and c['r'] and single(c['r']) and ok(c['r']['s'])]
        w = sum(1 for c in cs if not (c['label'] == c['r']['cands'] or c['r']['cands'] in c['dups']))
        res[split] = dict(fires=len(cs), wrong=w, ci95=[round(v, 3) for v in wilson(w, len(cs))])
    return res


def analyse_set():
    out = {}
    gs = [g for g in gold if single(g)]
    nss = [x for x in ns if x['test'] == 'masked-author' and single(x)]
    ps = [r for r in prod if single(r)]
    out['sizes'] = dict(gold_single=len(gs), masked_single=len(nss), production_single=len(ps),
                        profile_ok_production=sum(1 for r in ps if profok(r['s'])),
                        profile_ok_gold=sum(1 for g in gs if profok(g['s'])), profile_ok_masked=sum(1 for x in nss if profok(x['s'])))
    # kinds alone: fire rate on true (gold) vs namesake (masked-author), full printed name
    out['kinds'] = {}
    for nm, pr in KINDS.items():
        r = ev(pr)
        out['kinds'][nm] = r
    # combinations: two of three and all three at chosen levels
    K1L = ['K1:lrs>=3', 'K1:lrs>=4', 'K1:lrs>=6']
    K2L = ['K2:lrf>=1|vrep', 'K2:lrf>=2|vrep', 'K2:lrf>=3']
    K3L = ['K3:review|cites', 'K3:review|cites|cocite>=2', 'K3:review|cites|cocite>=3', 'K3:review-keylog']
    combos = {}
    for a in K1L:
        for b in K2L:
            combos[f'{a} & {b}'] = (lambda a, b: lambda s: KINDS[a](s) and KINDS[b](s))(a, b)
        for c in K3L:
            combos[f'{a} & {c}'] = (lambda a, c: lambda s: KINDS[a](s) and KINDS[c](s))(a, c)
    for b in K2L:
        for c in K3L:
            combos[f'{b} & {c}'] = (lambda b, c: lambda s: KINDS[b](s) and KINDS[c](s))(b, c)
    for a in K1L:
        for b in K2L:
            for c in K3L:
                combos[f'2of3({a},{b},{c})'] = (lambda a, b, c: lambda s: sum((KINDS[a](s), KINDS[b](s), KINDS[c](s))) >= 2)(a, b, c)
        combos[f'all3({a},K2:lrf>=1|vrep,K3:review|cites|cocite>=2)'] = (lambda a: lambda s: KINDS[a](s) and KINDS['K2:lrf>=1|vrep'](s) and KINDS['K3:review|cites|cocite>=2'](s))(a)
    out['combos'] = {nm: ev(pr) for nm, pr in combos.items()}
    # dev / held-out halves for the best combos (by gold+masked half)
    best = sorted(out['combos'].items(), key=lambda kv: (-(kv[1]['production_fires'] or 0)))
    out['combos_halves'] = {}
    for nm, r in best:
        if r['est_wrong_upper95'] is not None and r['est_wrong_upper95'] <= 0.02:
            out['combos_halves'][nm] = {h: ev(combos[nm], gset=[g for g in gs if g['half'] == h], nset=[x for x in nss if x['half'] == h])
                                        for h in (0, 1)}
    # several candidates: profile margin
    mg = [g for g in gold if g['m'] and g['state'] in ('possible', 'ambiguous') and g['true'] in (g['cands'] or '').split('|')]
    mn = [x for x in ns if x['test'] == 'masked-author' and x['m'] and x['state'] in ('possible', 'ambiguous')]
    mp_ = [r for r in prod if r['m'] and r['state'] in ('possible', 'ambiguous')]
    out['multi'] = dict(gold_rows=len(mg), masked_rows=len(mn), production_rows=len(mp_))
    for b_ in (4, 6, 8, 10, 12):
        for s_ in (0.0, 1.0, 2.0):
            g_f = [g for g in mg if g['m']['best'] >= b_ and g['m']['second'] <= s_]
            g_w = sum(1 for g in g_f if g['m']['bestkey'] != g['true'])
            n_f = [x for x in mn if x['m']['best'] >= b_ and x['m']['second'] <= s_]
            out['multi'][f'best>={b_},second<={s_}'] = dict(gold_fires=len(g_f), gold_wrong=g_w,
                gold_upper95=round(upper95(g_w, len(g_f)), 4) if g_f else None, masked_fires=len(n_f), masked_rate=round(len(n_f) / len(mn), 5) if mn else None,
                production_fires=sum(1 for r in mp_ if r['m']['best'] >= b_ and r['m']['second'] <= s_))
    return out


BOUND = 0.005


def meets(r):
    """pooled bound: the production estimate's upper bound and the gold upper bound both <= 0.5%"""
    return (r.get('est_wrong_upper95') is not None and r['est_wrong_upper95'] <= BOUND and r['gold'].get('upper95') is not None
            and r['gold']['upper95'] <= BOUND)


def main():
    global prod, gold, ns, clerical
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sc-positions', required=True, help="the scorer's positions (pid, tbl, work, role, pos) for the clerical labels")
    ap.add_argument('--run', action='append', required=True, help='SCRATCH:TAG:OLDTAG:TABLE')
    a = ap.parse_args()
    runs = [tuple(r.split(':')) for r in a.run]
    load(runs, a.sc_positions)
    allp, allg, alln, allc = prod[:], gold[:], ns[:], clerical[:]
    res = {}
    classes = sorted({t for _, _, _, t in runs})
    for t in classes + (['pooled'] if len(classes) > 1 else []):
        keep = (lambda r: True) if t == 'pooled' else (lambda r, t=t: r['tbl'] == t)
        prod[:] = [r for r in allp if keep(r)]
        gold[:] = [r for r in allg if keep(r)]
        ns[:] = [r for r in alln if keep(r)]
        clerical[:] = [c for c in allc if c['r'] is None or keep(c['r'])]
        res[t] = analyse_set()
        print(t, res[t]['sizes'], flush=True)
    res['meets_bound'] = {t: sorted(nm for grp in ('kinds', 'combos') for nm, r in res[t][grp].items() if meets(r)) for t in res}
    res['runs'] = a.run
    json.dump(res, open(a.out, 'w'), indent=1, default=str)
    print('written', a.out, json.dumps(res['meets_bound']))


if __name__ == '__main__':
    main()
