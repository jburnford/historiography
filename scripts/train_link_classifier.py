"""Supervised record-linkage classifier for works-to-people positions (2026-11-12).

Owner (2026-11-12): "I thought we were working toward a machine learning cpu kind of a solution." The scored linker
(scripts/score_links.py, naive Fellegi-Sunter, round two C2) is precise but cannot certify a position where several
name-compatible candidates survive (its multi-candidate threshold is unreachable) or where a single candidate bears a
common name. This script learns, the way census linkers do, a classifier over the same comparison vectors plus set-level
features of the block (number of candidates, rank, margin, runner-up, the other candidates' evidence), trained on
masked key-log gold, simulated absent authors and clerical labels, with thresholds set from held-out error.

Standing rulings: hard exclusions (dates, L.HARD proofs, the reviewed book's author on a review, a disagreeing printed
second given name) stay outside the model: excluded candidates never reach it. Topic, venue, network, cites and prize
features are monotone non-decreasing (topic may support a link, never exclude one). OpenAlex profile ties are not used.

Subcommands
  label-sample    draw new review-band positions for clerical (Opus) labelling, stratified by role, single/multi, name band
  label-dossiers  dossier text for clerical judges (the round-two audit format) and JSONL for a list of positions
  label-merge     clerical verdicts -> data/graph/scored-links/clerical-labels.csv
  features        pair and set-level features for gold, simulated-absent and production blocks -> Parquet
  p9-inputs       (local) position metadata and volume people for the pass-eight/nine evidence features
  p9-features     (Plato) pass-eight/nine evidence of every pair, by link_work_people's own code -> p9-features.parquet
  train           gradient-boosted trees, logistic regression, calibration, thresholds; evaluation; model + manifest
                  (2026-11-13: --qwen-labels adds the Qwen production labels; --sim-absent; pass-nine features)
  score           production decisions -> data/graph/scored-links/classified.csv.gz

Writes no proposal and touches no key log. Local steps stay under 4 GB (score_links.duck: 3 GB, 3 threads); the full
feature, training and scoring passes run as Plato CPU jobs.
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K_SHOW = 5                      # candidates shown per position (highest linkage scores first)
J = Path(os.environ.get('LC_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                        'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/judge'))


# ------------------------------------------------------------------------------------------------ dossier text

ROLE_NOTE = {
    'author': 'printed as an author of this work',
    'jstor-author': 'printed as an author of this JSTOR article',
    'reviewer': 'printed as the REVIEWER who wrote this review (the reviewed book is by someone else)',
    'editor': 'printed as an editor of this volume',
    'main': 'Library of Congress main entry (author heading) of this book',
    'added': 'Library of Congress added entry (joint author, editor or contributor) of this book',
    'resp': 'named in the statement of responsibility of this book',
}
FACT_WORDS = {
    'name': {'full+mid': 'printed name agrees in full, second given name included', 'full+init': 'printed name agrees, second initial agrees',
             'full': 'printed name agrees (first given name and family name)', 'initials2': 'printed initials agree (two initials)',
             'initial': 'printed with an initial only', 'variant': 'printed name is a variant of the key name',
             'surname-variant': 'family name matches through a variant or compound reading'},
    'freq': {'unique': 'no other known bearer of this name', '2-5': '2-5 known bearers of this name', '6-25': '6-25 known bearers of this name (common)',
             '26+': '26+ known bearers of this name (very common)', 'initials': 'name printed with initials only: bearers not countable',
             'unmeasured': 'name frequency not measured'},
    'date': {'pre-phd': 'work is more than 2 years before the PhD', 'phd0-10': 'work 0-10 years after the PhD', 'phd10-25': 'work 10-25 years after the PhD',
             'phd25+': 'work 25+ years after the PhD', 'life': 'work inside the life years', 'death': 'work near or after death year (posthumous possible)',
             'span': 'work inside the span of the key\'s dated works (with slack)', 'weak': 'dates only weakly known', 'undated': 'work undated'},
    'aff': {'same-window': 'printed affiliation matches the key\'s affiliation at that time', 'same-any': 'printed affiliation matches one of the key\'s affiliations (another time)',
            'different': 'printed affiliation differs from the key\'s affiliation at that time'},
    'venue': {'j3+': 'key has 3+ other works in this venue', 'j1-2': 'key has 1-2 other works in this venue'},
    'topic': {'low': 'slight title-word overlap with the key\'s works', 'mid': 'some title-word overlap with the key\'s works',
              'high': 'strong title-word overlap with the key\'s works', 'vhigh': 'very strong title-word overlap with the key\'s works'},
    'neg': {'orcid-differs': 'the work prints an ORCID that is not the key\'s', 'pooled': 'key is marked as pooling several people',
            'inconsistent': 'key has inconsistent dates', 'own-title': 'key wrote a book of the same title (for a review: the reviewed author)'},
}
NET_WORDS = {'net_kl': 'a co-author in the key log is also printed on this work', 'net_ln': 'a linked co-author is printed on this work',
             'net_ced': 'a co-editor of the key is on this work or volume', 'net_edof': 'editor / chapter-author relation with someone on this work or volume',
             'net_adv': 'advisor or student of the key is on this work', 'net_col': 'a co-printed person was the key\'s colleague (same institution, same years)',
             'net_vol': 'a person in the containing volume is in the key\'s network'}


def facts_of(c):
    out = []
    for f in ('name', 'freq', 'date', 'aff', 'venue', 'topic'):
        w = FACT_WORDS[f].get(c.get(f))
        if w:
            out.append(w)
    for f, w in NET_WORDS.items():
        if c.get(f) not in (None, 'none', ''):
            out.append(w)
    if c.get('cites') == 'cites':
        out.append('the work cites the key\'s work or thesis (or is cited by its thesis)')
    w = FACT_WORDS['neg'].get(c.get('neg'))
    if w:
        out.append('AGAINST: ' + w)
    return out


def render(d, letters=True, facts=True):
    """dossier text (the user message the model sees; the sheet Opus judges read)"""
    lines = [f"### {d['item']}",
             f"printed name: {d['printed_name']}",
             f"role: {ROLE_NOTE.get(d['role'], d['role'])}",
             f"work: {d['title'][:220]} | {d['kind']} | {d['year'] or '-'} | venue: {d['venue'] or '-'} | id {d['work']}",
             f"other names printed on the work: {d['other_names'] or '-'}",
             f"printed affiliation: {d['printed_aff'] or '-'}"]
    for j, c in enumerate(d['candidates']):
        tag = f"candidate {chr(65 + j)}: " if letters else 'candidate: '
        lines.append(f"{tag}{c['key']} {c['label']} | ids: {c['ids'] or '-'}")
        lines.append(f"   affiliations: {'; '.join(c['aff'][:5]) or '-'}")
        if c.get('rel'):
            lines.append(f"   advisor/student: {'; '.join(c['rel'][:4])}")
        if c.get('coauth'):
            lines.append(f"   co-authors (key log): {'; '.join(c['coauth'][:6])}")
        if facts:
            lines.append(f"   linkage facts: {'; '.join(c['facts']) or '-'}")
        lines.append(f"   works ({c['works_n']} in the key log; up to 12 shown):")
        lines += ['     ' + x for x in c['works']]
    if d.get('more'):
        lines.append(f"({d['more']} more name-compatible keys with weaker linkage facts are not shown)")
    return '\n'.join(lines)


# ------------------------------------------------------------------------------------------------ local: sampling / export

def _sl():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import score_links as SL
    return SL


def band_of(n, freq, neg):
    single = n == 1 and str(neg) == 'none'
    if not single:
        return 'multi'
    return 'single-common' if freq in ('6-25', '26+', 'initials') else 'single-other'


def role_of(role, tbl):
    if role == 'editor':
        return 'volume-editor'
    if role in ('jstor-author', 'reviewer'):
        return role
    return 'author'


def sample_new(args):
    """600 new review-band positions, weighted toward multi-candidate and common-name strata, across four roles"""
    SL = _sl()
    db = SL.duck()
    D = db.execute(f"""SELECT pid, role, tbl, n, freq, neg, score, runner, decision FROM '{SL.S / 'prod-decided.parquet'}'
                       WHERE decision = 'review'""").df()
    old = set(int(x) for x in db.execute(f"SELECT pid FROM read_csv('{ROOT / 'data/graph/scored-links/audit-author-role.csv'}')").df().pid)
    D = D[~D.pid.isin(old)]
    D['rr'] = [role_of(r, t) for r, t in zip(D.role, D.tbl)]
    D['band'] = [band_of(n, f, g) for n, f, g in zip(D.n, D.freq, D.neg)]
    alloc_role = {'author': 210, 'jstor-author': 130, 'reviewer': 130, 'volume-editor': 130}
    share = {'multi': 0.5, 'single-common': 0.3, 'single-other': 0.2}
    rnd = random.Random(20261112 + 2)
    picks = []
    for rr, nr in alloc_role.items():
        for b, s in share.items():
            idx = list(D[(D.rr == rr) & (D.band == b)].index)
            rnd.shuffle(idx)
            picks += idx[:round(nr * s)]
    A = D.loc[picks].copy()
    A = A.sample(frac=1, random_state=7).reset_index(drop=True)
    A['item'] = [f'N{i:03d}' for i in range(len(A))]
    W = D.groupby(['rr', 'band']).size().rename('prod_n').reset_index()
    A = A.merge(W, on=['rr', 'band'], how='left')
    (J / 'labels').mkdir(parents=True, exist_ok=True)
    A.to_csv(J / 'labels/new-sample.csv', index=False)
    print(len(A), A.groupby(['rr', 'band']).size().unstack())


def export(args):
    """dossiers for the positions of a CSV (columns item, pid; optional candidates_shown = '|'-joined keys to show in that
    order, used for the 420 audited positions so the model sees the keys the Opus judges saw)"""
    import pandas as pd
    SL = _sl()
    db = SL.duck()
    S = SL.S
    A = pd.read_csv(args.positions, dtype={'candidates_shown': str})
    if 'item' not in A:
        A['item'] = A.pid.astype(str)
    if args.limit:
        A = A.head(args.limit)
    out = open(args.out, 'w')
    txt = open(args.text, 'w') if args.text else None
    nchunk = args.chunk
    stats = Counter()
    for c0 in range(0, len(A), nchunk):
        B = A.iloc[c0:c0 + nchunk]
        pids = ','.join(map(str, B.pid))
        cs = db.execute(f"SELECT * EXCLUDE (__index_level_0__) FROM '{S / 'cand-scores2.parquet'}' WHERE pid IN ({pids})").df()
        cs = cs.sort_values(['pid', 'score'], ascending=[True, False])
        csd = {p: g for p, g in cs.groupby('pid')}
        pos = {r['pid']: r for r in db.execute(f"""SELECT pid, work, name, title, year, wjournal, kind, role, insts, raw_aff, source, tbl
                FROM read_parquet(['{S / 'positions.parquet'}', '{S / 'positions-extra.parquet'}'], union_by_name=true)
                WHERE pid IN ({pids})""").df().to_dict('records')}
        want = {}
        for r in B.itertuples():
            g = csd.get(r.pid)
            shown = [k for k in str(getattr(r, 'candidates_shown', '') or '').split('|') if k.startswith('p-')]
            if shown:
                keys = shown
            else:
                keys = list(g.key) if g is not None else []
            want[r.pid] = keys
        allk = {k for ks in want.values() for k in ks}
        info = SL.key_dossier(db, allk)
        works = sorted({p['work'] for p in pos.values()})
        db.register('ww2', pd.DataFrame({'work': works}))
        co = defaultdict(list)
        for w, nm in db.execute(f"""SELECT work, name FROM read_parquet(['{S / 'positions.parquet'}', '{S / 'positions-extra.parquet'}'], union_by_name=true)
                JOIN ww2 USING (work) ORDER BY pos""").fetchall():
            if nm not in co[w]:
                co[w].append(nm)
        for r in B.itertuples():
            p = pos.get(r.pid)
            if p is None:
                stats['no-position'] += 1
                continue
            g = csd.get(r.pid)
            lv = {row['key']: row for row in (g.to_dict('records') if g is not None else [])}
            keys = want[r.pid]
            cands, excl = [], []          # hard exclusions happened upstream (score_links: name block, dates, own book)
            for k in keys:
                d = info.get(k, {})
                lab = d.get('label') or ''
                c = lv.get(k, {})
                ws = d.get('works', [])
                step = max(1, len(ws) // 12)
                cands.append(dict(key=k, label=lab, ids=d.get('ids') or '', aff=d.get('aff', [])[:5], rel=d.get('rel', [])[:4],
                                  coauth=d.get('coauth', [])[:6], works_n=len(ws), works=ws[::step][:12],
                                  facts=facts_of(c), score=None if c.get('score') is None else round(float(c['score']), 3)))
            more = 0
            if not str(getattr(r, 'candidates_shown', '') or '').startswith('p-') and len(cands) > K_SHOW:
                more = len(cands) - K_SHOW
                cands = cands[:K_SHOW]
            stats['excluded'] += len(excl)
            aff = list(p['insts'] if p['insts'] is not None else []) + list(p['raw_aff'] if p['raw_aff'] is not None else [])
            d = dict(item=r.item, pid=int(r.pid), work=p['work'], role=p['role'], tbl=p['tbl'], source=p['source'],
                     printed_name=p['name'], title=(p['title'] or ''), kind=p['kind'], year=None if pd.isna(p['year']) else int(p['year']),
                     venue=p['wjournal'] or '', other_names='; '.join(x for x in co[p['work']] if x != p['name'])[:300],
                     printed_aff='; '.join(aff)[:200], candidates=cands, excluded=excl, more=more)
            out.write(json.dumps(d, ensure_ascii=False) + '\n')
            stats['dossiers'] += 1
            if txt:
                txt.write(render(d, facts=not args.no_facts) + '\n\n')
        print(c0 + len(B), dict(stats), SL.rss(), 'MB', flush=True)
    out.close()
    if txt:
        txt.close()


# ------------------------------------------------------------------------------------------------ prep (local, < 4 GB)

PAIR_COLS = ['pid', 'mode', 'key', 'label', 'name', 'freq', 'date', 'aff', 'network', 'venue', 'topic', 'cites', 'neg',
             'net_kl', 'net_ln', 'net_ced', 'net_edof', 'net_adv', 'net_col', 'net_vol', 'topic_sc', 'bearers', 'lc_others', 'oa_n', 'nco']
POS_COLS = ['pid', 'mode', 'work', 'rule_state', 'rule_key', 'rule_drop_state', 'rule_drop_key', 'gold', 'split', 'imp_key',
            'exact', 'n_live', 'g_status', 'capped']


def prep(args):
    """inputs for the Plato feature job, metadata only: cleaned pair vectors with the naive Fellegi-Sunter score and
    prize facts, position variants with cleaned gold and splits, position metadata, per-key attributes, the round-two
    production decisions (scorer and rule linker), the absent-author shares and the clerical labels"""
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    SL = _sl()
    S, G = SL.S, SL.GRAPH
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    db = SL.duck()
    srcs = [str(S / 'positions.parquet'), str(S / 'positions-extra.parquet')]
    pv = db.execute(f"SELECT {', '.join(POS_COLS)} FROM read_parquet('{S / 'pairs'}/pos-*.parquet', union_by_name=true)").df()
    cd = SL.read_pairs('true', PAIR_COLS)
    print('loaded', len(cd), len(pv), round(time.time() - t0), SL.rss(), 'MB', flush=True)
    stats = SL.clean_gold(db, cd, pv, srcs)
    print('gold clean-up', stats, flush=True)
    wm = json.load(open(S / 'weights-all.json'))['models']['naive']        # round two C2 = naive weights
    cd['fs'], cd['ctx_w'] = SL.score_vec(cd, wm)
    pos_w = dict(zip(pv.pid.values, zip(pv.work.values)))
    cd['prize'] = SL.prize_facts(cd, pos_w)
    # check: production scores equal the round-two production file
    chk = db.execute(f"SELECT pid, key, score FROM '{S / 'cand-scores2.parquet'}' USING SAMPLE 20000 ROWS").df()
    m = chk.merge(cd[cd['mode'].astype(str) == 'prod'][['pid', 'key', 'fs']].assign(key=lambda x: x.key.astype(str)), on=['pid', 'key'])
    stats['fs_check_rows'] = len(m)
    stats['fs_check_maxdiff'] = float((m.score - m.fs).abs().max())
    print('fs check', stats['fs_check_rows'], stats['fs_check_maxdiff'], flush=True)
    for c in cd.columns:
        if hasattr(cd[c], 'cat'):
            cd[c] = cd[c].astype(str)
    pq.write_table(pa.Table.from_pandas(cd, preserve_index=False), out / 'pairs.parquet', compression='zstd')
    pv.to_parquet(out / 'positions.parquet', index=False)
    keys = sorted(set(cd.key))
    del cd
    # position metadata (no titles beyond a review flag; names and work ids for the output table)
    db.execute(f"""COPY (SELECT pid, tbl, role, source, work, pos, n_auth, name AS printed, year, kind, coalesce(route_a, false) AS route_a,
            regexp_matches(coalesce(title, ''), '(?i)^\\s*review of|\\breviews?\\b|besprechung|rezension|reseñas?\\b|recensioni?\\b|comptes? rendus?') AS review_record
            FROM read_parquet({srcs}, union_by_name=true)) TO '{out / 'meta.parquet'}' (FORMAT parquet)""")
    # per-key attributes
    from graph_tables import keylog
    db.register('kk', pd.DataFrame({'key': keys}))
    A = db.execute(f"""SELECT p.key, list_transform(coalesce(p.anchors, []), a -> split_part(a, ':', 1)) AS kinds,
            p.orcid IS NOT NULL AND len(p.orcid) > 0 AS has_orcid FROM '{G}/person.parquet' p JOIN kk USING (key)""").df()
    kinds = [set(x) if x is not None else set() for x in A.kinds]
    A['has_thesis'] = [bool(k & {'diss-person', 'diss-author'}) for k in kinds]
    A['has_aha'] = [bool(k & {'aha', 'aha-phd'}) for k in kinds]
    A['has_directory'] = [bool(k & {'aha', 'ihr'}) for k in kinds]
    A['has_lcnaf'] = ['lcnaf' in k for k in kinds]
    A['has_wd'] = ['wd' in k for k in kinds]
    A['has_review_credit'] = ['review-credit' in k for k in kinds]
    A['only_review_credit'] = [k == {'review-credit'} for k in kinds]
    A['n_ids'] = [len(k - {'review-credit'}) for k in kinds]
    sup = {k for (k,) in db.execute(f"SELECT DISTINCT \"from\" FROM '{G}/supervised.parquet'").fetchall()}
    A['has_supervisor'] = [k in sup or 'repo-advisor' in kk for k, kk in zip(A.key, kinds)]
    rv = {k for (k,) in db.execute(f"SELECT DISTINCT \"from\" FROM '{G}/reviewed.parquet'").fetchall()} if (G / 'reviewed.parquet').exists() else set()
    A['has_review_evidence'] = [k in rv or 'review-credit' in kk for k, kk in zip(A.key, kinds)]
    nw = dict(db.execute(f"SELECT a.\"from\", count(DISTINCT a.\"to\") FROM {keylog(G, 'authored')} a JOIN kk ON kk.key = a.\"from\" GROUP BY 1").fetchall())
    A['n_works'] = A.key.map(nw).fillna(0).astype(int)
    dc = dict(db.execute(f"""SELECT id, country FROM read_csv('{ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'}', all_varchar=true)""").fetchall())
    country = {}
    for k, d in db.execute(f"""SELECT a."from", replace(x, 'diss-thesis:', '') FROM {keylog(G, 'authored')} a JOIN kk ON kk.key = a."from" JOIN
            (SELECT key, unnest(anchors) x FROM '{G}/work.parquet' WHERE kind = 'thesis') t ON t.key = a."to" WHERE x LIKE 'diss-thesis:%'""").fetchall():
        if dc.get(d):
            country[k] = dc[d]
    A['country'] = [country.get(k) or ('US/CA (AHA)' if h else 'unknown') for k, h in zip(A.key, A.has_aha)]
    A.drop(columns=['kinds']).to_parquet(out / 'person-attrs.parquet', index=False)
    # production decisions of round two (scorer C2) and the rule linker, for the head-to-head
    db.execute(f"""COPY (SELECT pid, key, score, runner, n, freq, neg, decision, rule_state, rule_key, rg FROM '{S / 'prod-decided.parquet'}')
            TO '{out / 'prod-decided.parquet'}' (FORMAT parquet)""")
    rep = json.load(open(ROOT / 'data/graph/scored-links/report.json'))
    json.dump(dict(absent_share=rep['absent_share_used'], thresholds_c2=rep['thresholds'], gold_cleanup=stats,
                   graph_snapshot=rep.get('graph_snapshot'), built=time.strftime('%Y-%m-%d %H:%M')), open(out / 'prep.json', 'w'), indent=1)
    import shutil
    shutil.copy(ROOT / 'data/graph/scored-links/clerical-labels.csv', out / 'clerical-labels.csv')
    print('prep done', round(time.time() - t0), 's', SL.rss(), 'MB', flush=True)


# ------------------------------------------------------------------------------------------------ pass eight / nine evidence

# 2026-11-13: the evidence kinds of link_work_people.py passes eight and nine as features of every pair (single and
# several candidates, every block variant). Computed by link_work_people's own code (Pass9, lc_dated, lc_impossible,
# nameonly_features for the volume context), imported, never edited here. Per pair:
#   p9_lrs   kind 1: likelihood ratio of the work's vocabulary (title, volume title and sibling chapters, journal) under
#            the candidate's key-log profile against all graph titles (positive-only, capped per term)
#   p9_lrf   kind 2: the same over subfield words;  p9_vrep: other key-log works of the candidate in the same journal
#   p9_rv    kind 3: REVIEWED either way with a person credited on the work or its volume (2 key log, 1 linked)
#   p9_ct    citations between the candidate's works and theirs (2 key log on both sides, 1 any);  p9_cca/p9_cck:
#            theses co-citing them (any evidence / key log)
#   p9_prof  profile usable (3+ key-log works or a thesis);  p9_lro: best profile score of an LC namesake authority
#   p9_lcin  undated LC namesakes silent > 25 years in another subject (rule C);  p9_lcdp: LC namesakes the dates do not
#            rule out (lc_others minus date-impossible);  p9_lcact: p9_lcdp minus p9_lcin
# The pair's own work is hidden from the candidate's profile and ties in every mode (HIDE = (work, key)), as the masked
# gold credit is in the linker's tests, so production and gold rows are computed alike.
P9_F = ['p9_lrs', 'p9_lrf', 'p9_vrep', 'p9_rv', 'p9_ct', 'p9_cca', 'p9_cck', 'p9_prof', 'p9_lro', 'p9_lcin', 'p9_lcdp', 'p9_lcact']
P9_SET = ['p9_lrs_other', 'p9_lrs_margin']
P9_MONO = ['p9_lrs', 'p9_lrf', 'p9_vrep', 'p9_rv', 'p9_ct', 'p9_cca', 'p9_cck']
USE_P9 = [True]


def p9_inputs(args):
    """local, light: what the Plato p9-features job reads beside the classifier inputs: p9-blocks.parquet (pid, mode,
    work, co-credited keys `ex`, gold key), p9-pos.parquet (position metadata: printed name, title, year, journal, kind,
    role: metadata only), p9-scratch/volume-people.parquet (the scorer's volume people) and sibling-chapters.parquet"""
    SL = _sl()
    S = SL.S
    out = Path(args.out)
    (out / 'p9-scratch').mkdir(parents=True, exist_ok=True)
    db = SL.duck()
    db.execute(f"""COPY (SELECT pid, mode, work, coalesce(ex, '') ex, coalesce(gold, '') gold FROM read_parquet('{S / 'pairs'}/pos-*.parquet', union_by_name=true)
            WHERE coalesce(exact, '') = '') TO '{out / 'p9-blocks.parquet'}' (FORMAT parquet)""")
    db.execute(f"""COPY (SELECT pid, tbl, work, name, title, year, coalesce(nullif(wjournal, ''), journal, '') journal, kind, role
            FROM read_parquet(['{S / 'positions.parquet'}', '{S / 'positions-extra.parquet'}'], union_by_name=true)
            WHERE pid IN (SELECT DISTINCT pid FROM '{out / 'p9-blocks.parquet'}')) TO '{out / 'p9-pos.parquet'}' (FORMAT parquet)""")
    db.execute(f"COPY (SELECT work, key, how FROM '{S / 'aux-vp.parquet'}') TO '{out / 'p9-scratch/volume-people.parquet'}' (FORMAT parquet)")
    sib = Path(args.siblings)
    if sib.exists():
        db.execute(f"COPY (SELECT id, volume_work, title FROM '{sib}') TO '{out / 'p9-scratch/sibling-chapters.parquet'}' (FORMAT parquet)")
    for f in ('p9-blocks.parquet', 'p9-pos.parquet'):
        print(f, db.execute(f"SELECT count(*) FROM '{out / f}'").fetchone()[0], flush=True)


_P9W = {}


def _p9_chunk(pids):
    """worker: pass-nine facts of every pair of the given positions (all modes); the Pass9 object is inherited (fork)"""
    W, S9, POS, BLK, PAIRS, LCOWN, P = (_P9W[k] for k in ('W', 'S9', 'POS', 'BLK', 'PAIRS', 'LCOWN', 'P'))
    out = []
    for pid in pids:
        r = POS.get(pid)
        if r is None:
            continue
        p = W.make_pos(dict(source='', oa_work='', work=r['work'], pos=0, role=r['role'], name=r['name'] or '', title=r['title'] or '',
                            year=r['year'], orcid='', oa_author='', rors=[], insts=[], raw_aff=[], inst_ror='', kind=r['kind'] or '',
                            journal=r['journal'] or ''))
        fs_ = p['forms']
        nk = (fs_[0][0], fs_[0][2][0]) if fs_ and fs_[0][2] else None
        book = (r['kind'] or '') == 'book'
        for mode, keys in PAIRS.get(pid, {}).items():
            ex, gold = BLK.get((pid, mode), ('', ''))
            exs = {x for x in ex.split('|') if x}
            hide_gold = gold if mode in ('present', 'imp') else ''
            own_ids = set()
            for k, _ in keys:
                own_ids |= LCOWN.get(k, set())
            imp = 0
            if nk and p['year']:
                imp = sum(1 for lcid, b, d in W.LCD.get(nk, ()) if lcid not in own_ids and W.lc_impossible(b, d, p['year'], book))
            vp = _P9W['VP'].get(r['work'], ())
            ved = _P9W['VED'].get(r['work'], ())
            for k, lc_others in keys:
                if nk is None:
                    out.append((pid, mode, k) + (0.0,) * 10 + (-1.0, -1.0))
                    continue
                oth = {k2: ('ed' if k2 in ved else 'sib') for k2 in vp if k2 != hide_gold}
                for k2 in exs:
                    if k2 != hide_gold:
                        oth.setdefault(k2, 'co')
                fe = dict(p9=dict(w=r['work'], others=oth), name_key=nk)
                W.HIDE[0] = (r['work'], k)
                y = S9.facts(None, p, fe, k, own_ids, P)
                W.HIDE[0] = None
                lco = -1.0 if lc_others is None or lc_others != lc_others else float(lc_others)
                lcdp = -1.0 if lco < 0 else float(max(0, lco - imp))
                lcact = -1.0 if lcdp < 0 else float(max(0, lcdp - y['lc_inactive']))
                out.append((pid, mode, k, y['lrs'], y['lrf'], float(y['vrep']), float(y['rv']), float(y['ct']), float(y['cca']), float(y['cck']),
                            float(y['psz'] >= 3 or bool(y['pth'])), y['lro'], float(y['lc_inactive']), lcdp, lcact))
    return out


def p9_features(args):
    """Plato: pass-eight/nine evidence for every pair of the classifier inputs -> INPUTS/p9-features.parquet"""
    import multiprocessing as mp
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    inp = Path(args.inputs)
    os.environ.setdefault('WP_SCRATCH', str(inp / 'p9-scratch'))
    sys.path.insert(0, str(ROOT / 'scripts'))
    import plato_paths
    import link_work_people as W
    plato_paths.patch()
    t0 = time.time()
    db = W.duck()
    C = pd.read_parquet(inp / 'pairs.parquet', columns=['pid', 'mode', 'key', 'lc_others'])
    if args.sample:
        C = C[(C.pid.values * 2654435761) % 1000 < args.sample * 1000]
    pos = pd.read_parquet(inp / 'p9-pos.parquet')
    pos = pos[pos.pid.isin(set(C.pid))]
    blk = pd.read_parquet(inp / 'p9-blocks.parquet')
    blk = blk[blk.pid.isin(set(C.pid))]
    POS = {int(r['pid']): r for r in pos.to_dict('records')}
    for r in POS.values():
        r['year'] = None if r['year'] is None or r['year'] != r['year'] else int(r['year'])
    BLK = {(int(p), m): (e, g) for p, m, e, g in zip(blk.pid, blk['mode'], blk.ex, blk.gold)}
    PAIRS = defaultdict(lambda: defaultdict(list))
    for p, m, k, lo in zip(C.pid.values, C['mode'].values, C.key.values, C.lc_others.values):
        PAIRS[int(p)][m].append((k, lo))
    PAIRS = {p: dict(v) for p, v in PAIRS.items()}
    print('pairs', len(C), 'positions', len(POS), round(time.time() - t0), 's', flush=True)
    # LC authorities of each candidate key (excluded from the namesakes: own_lc)
    keys = sorted(set(C.key))
    db.register('kk', pd.DataFrame({'key': keys}))
    LCOWN = defaultdict(set)
    for k, an in db.execute(f"SELECT p.key, p.anchors FROM '{W.GRAPH}/person.parquet' p JOIN kk USING (key)").fetchall():
        LCOWN[k] = {a[6:] for a in an or () if a.startswith('lcnaf:')}
    needed = set()
    for r in POS.values():
        fs_ = W.forms(W.apos(r['name'] or ''))
        if fs_ and fs_[0][2]:
            needed.add((fs_[0][0], fs_[0][2][0]))
    W.LCD.clear()
    W.LCD.update(W.lc_dated(db, needed))
    print('LC dated namesakes for', len(W.LCD), 'of', len(needed), 'names', round(time.time() - t0), 's', flush=True)
    feats = W.nameonly_features(db, None, topic_min=0.0)        # only for the volume context (vctx) and volume people
    VED = defaultdict(set)
    for w, k, how in db.execute(f"SELECT work, key, how FROM '{W.SCRATCH}/volume-people.parquet'").fetchall():
        if how == 'volume-editor':
            VED[w].add(k)
    others_all = set()
    for ks in feats.vp.values():
        others_all |= ks
    for e, _ in BLK.values():
        others_all |= {x for x in e.split('|') if x}
    works = {r['work'] for r in POS.values()}
    S9 = W.Pass9(db, None, works, others_all, feats.vctx, needed)
    P = dict(ACT_N=25)
    _P9W.update(W=W, S9=S9, POS=POS, BLK=BLK, PAIRS=PAIRS, LCOWN=LCOWN, P=P, VP=feats.vp, VED=VED)
    print('pass nine ready', round(time.time() - t0), 's', flush=True)
    pids = sorted(PAIRS)
    nproc = int(os.environ.get('SLURM_CPUS_PER_TASK', args.procs))
    chunks = [pids[i:i + 2000] for i in range(0, len(pids), 2000)]
    rows = []
    if nproc > 1:
        with mp.get_context('fork').Pool(nproc) as pool:
            for i, part in enumerate(pool.imap_unordered(_p9_chunk, chunks)):
                rows += part
                if i % 50 == 0:
                    print(i, '/', len(chunks), len(rows), round(time.time() - t0), 's', flush=True)
    else:
        for i, ch in enumerate(chunks):
            rows += _p9_chunk(ch)
    cols = ['pid', 'mode', 'key'] + P9_F
    F = pd.DataFrame(rows, columns=cols)
    for c in P9_F:
        F[c] = F[c].astype('float32')
    pq.write_table(pa.Table.from_pandas(F, preserve_index=False), inp / 'p9-features.parquet', compression='zstd')
    print('written', len(F), 'pairs', {c: round(float((F[c] > 0).mean()), 4) for c in P9_F}, round(time.time() - t0), 's', flush=True)


def p9_set_features(C):
    """block-level pass-nine features: the strongest subject ratio among the other candidates, this one's margin to it"""
    import numpy as np
    g = C.groupby(['mode', 'pid'], sort=False, observed=True)
    v = C.p9_lrs.values
    mx = g.p9_lrs.transform('max').values
    nmx = C.assign(_m=(v >= mx).astype(np.int16)).groupby(['mode', 'pid'], sort=False, observed=True)._m.transform('sum').values
    below = C.assign(_b=np.where(v < mx, v, -np.inf)).groupby(['mode', 'pid'], sort=False, observed=True)._b.transform('max').values
    srt = np.where(nmx > 1, mx, np.where(np.isfinite(below), below, 0.0))
    other = np.where(C.n.values == 1, 0.0, np.where(v >= mx, srt, mx))
    C['p9_lrs_other'] = other.astype(np.float32)
    C['p9_lrs_margin'] = (v - other).astype(np.float32)
    return C


# ------------------------------------------------------------------------------------------------ features (Plato)

ORD = {
    'name': {'surname-variant': 0, 'variant': 1, 'initial': 2, 'initials2': 3, 'full': 4, 'full+init': 5, 'full+mid': 6},
    'aff': {'different': 0, 'absent': 1, 'same-any': 2, 'same-window': 3},
    'network': {'none': 0, 'network1': 1, 'coauthor1': 1, 'multi': 2},
    'net_kl': {'none': 0, '1': 1, '2+': 2},
    'venue': {'none': 0, 'na': 0, 'j1-2': 1, 'j3+': 2},
    'topic': {'none': 0, 'low': 1, 'mid': 2, 'high': 3, 'vhigh': 4},
    'cites': {'none': 0, 'cites': 1},
    'prize': {'none': 0, 'body': 1, 'winner': 2},
}
BIN = ('net_ln', 'net_ced', 'net_edof', 'net_adv', 'net_col', 'net_vol')
CATS = {
    'freq': ['unique', '2-5', '6-25', '26+', 'initials', 'unmeasured'],
    'date': ['pre-phd', 'phd0-10', 'phd10-25', 'phd25+', 'life', 'death', 'span', 'weak', 'undated'],
    'neg': ['none', 'orcid-differs', 'pooled', 'inconsistent', 'own-title'],
    'rg': ['author', 'jstor-author', 'reviewer'],
    'kind': ['article', 'book', 'chapter', 'review', 'other', 'thesis', 'preprint', 'dataset'],
}
# run 1 (job 6020710) used the source table and the role as features: the gold covers only the work-people (wp) and
# name-only (no) tables, so volume editors, catalogue headings and the Crossref residues were unseen categories and
# the model extrapolated (a ceramics chemist linked as editor of a Swift volume at p 0.98). Both are out; links are
# certified only on the tables the gold covers, the rest stay in review.
GOLD_TABLES = ('wp', 'no')
# positive-only evidence (owner: topic may support a link, never exclude one): monotone non-decreasing in the model
MONO_UP = ['aff', 'network', 'net_kl', 'venue', 'topic', 'topic_sc', 'cites', 'prize'] + list(BIN) + ['nco']
PAIR_NUM = ['bearers_l', 'lc_others', 'oa_n_l', 'fs', 'ctx_w']
KEY_ATTR = ['has_orcid', 'has_thesis', 'has_aha', 'has_directory', 'has_lcnaf', 'has_wd', 'has_review_credit', 'only_review_credit',
            'has_supervisor', 'has_review_evidence', 'n_ids', 'n_works_l']
SET_F = ['n', 'rank', 'margin', 'runner_fs', 'best_fs', 'share', 'other_ctx_any', 'other_max_ctx', 'n_close']
POS_F = ['decade', 'review_record', 'n_auth']


# Key attributes (ORCID, identifiers, works held, thesis / AHA / directory / supervisor / review evidence) are kept as
# reporting strata, not as model features: run 2 (job 6020741) showed they separate gold from simulated absents by
# construction (the gold key always holds a key-log credit; the impersonated namesake is a random decade-active key),
# so the model learned that well-documented keys absorb namesakes (probe: a pre-PhD 2004 review linked to p-24137 at
# p 0.93 on has_orcid, has_review_credit and n_ids, Fellegi-Sunter 0.6, no topic, venue or network fact).
KEY_FEATURES = [False]


def feature_names():
    return list(ORD) + list(BIN) + ['topic_sc', 'nco'] + PAIR_NUM + (KEY_ATTR if KEY_FEATURES[0] else []) + SET_F + POS_F + list(CATS) + \
        ((P9_F + P9_SET) if USE_P9[0] else [])


def mono_up():
    return MONO_UP + (P9_MONO if USE_P9[0] else [])


def set_features(F):
    """block (pid, mode) features: candidates surviving, this candidate's rank, margin to the best other candidate,
    the runner-up's score, the evidence share (softmax of the Fellegi-Sunter weights, base 2), whether any other
    candidate holds a positive context fact, the others' strongest context weight, candidates within 2 of the best"""
    import numpy as np
    F.sort_values(['mode', 'pid', 'fs'], ascending=[True, True, False], inplace=True, kind='stable')
    F.reset_index(drop=True, inplace=True)
    g = F.groupby(['mode', 'pid'], sort=False, observed=True)
    F['n'] = g.fs.transform('size').astype(np.int16)
    F['rank'] = g.cumcount().astype(np.int16)
    best = g.fs.transform('max').values
    r1 = np.where(F['rank'].values == 1, F.fs.values, np.nan)
    second = F.assign(_r1=r1).groupby(['mode', 'pid'], sort=False, observed=True)._r1.transform('max').values
    other_best = np.where(F['rank'].values == 0, second, best)
    F['margin'] = np.where(np.isnan(other_best), 30.0, F.fs.values - other_best)
    F['runner_fs'] = np.where(np.isnan(other_best), -30.0, other_best)
    F['best_fs'] = best
    e = np.exp2(np.clip(F.fs.values - best, -60, 0))
    F['share'] = e / F.assign(_e=e).groupby(['mode', 'pid'], sort=False, observed=True)._e.transform('sum').values
    pos = ((F.network.values > 0) | (F.net_kl.values > 0) | (F[list(BIN)].values.sum(1) > 0) | (F.venue.values > 0) | (F.topic.values >= 2)
           | (F.cites.values > 0) | (F.aff.values >= 2) | (F.prize.values > 0)).astype(np.int16)
    F['_pos'] = pos
    F['other_ctx_any'] = (F.groupby(['mode', 'pid'], sort=False, observed=True)._pos.transform('sum').values - pos > 0).astype(np.int8)
    cw = F.ctx_w.values
    F['_cw'] = cw
    mx = F.groupby(['mode', 'pid'], sort=False, observed=True)._cw.transform('max').values
    # strongest context among the others: the max unless this row is the max, then the second
    nmx = F.assign(_m=(cw >= mx).astype(np.int16)).groupby(['mode', 'pid'], sort=False, observed=True)._m.transform('sum').values
    below = F.assign(_b=np.where(cw < mx, cw, -np.inf)).groupby(['mode', 'pid'], sort=False, observed=True)._b.transform('max').values
    srt = np.where(nmx > 1, mx, np.where(np.isfinite(below), below, 0.0))
    F['other_max_ctx'] = np.where(F.n.values == 1, 0.0, np.where(cw >= mx, srt, mx))
    F['_close'] = (F.fs.values >= best - 2).astype(np.int16)
    F['n_close'] = F.groupby(['mode', 'pid'], sort=False, observed=True)._close.transform('sum').values - F._close.values
    F.drop(columns=['_pos', '_cw', '_close'], inplace=True)
    return F


def build_features(inp, sample=0.0):
    """pair rows of every block variant: prod, present (gold, key masked), imp (impersonated namesake) and drop (the
    present block with the true key and its duplicates removed: the realistic absent-author case); numeric encodings,
    key attributes, set-level features"""
    import numpy as np
    import pandas as pd
    t0 = time.time()
    C = pd.read_parquet(inp / 'pairs.parquet')
    PV = pd.read_parquet(inp / 'positions.parquet')
    M = pd.read_parquet(inp / 'meta.parquet')
    A = pd.read_parquet(inp / 'person-attrs.parquet')
    if sample:
        keep = lambda p: (p * 2654435761) % 1000 < sample * 1000       # noqa: E731 (development subsample by pid)
        C, PV = C[keep(C.pid.values)], PV[keep(PV.pid.values)]
    # blocks already linked by an identifier (decision exact) are not the classifier's to decide
    ex = set(zip(PV['mode'][PV.exact.fillna('') != ''], PV.pid[PV.exact.fillna('') != '']))
    C = C[[(m, p) not in ex for m, p in zip(C['mode'].values, C.pid.values)]]
    print('read', len(C), len(PV), 'exact blocks left out', len(ex), round(time.time() - t0), flush=True)
    drop = C[(C['mode'] == 'present') & ~C.label.isin([1, 2, 3])].copy()
    drop['mode'] = 'drop'
    C = pd.concat([C, drop], ignore_index=True)
    del drop
    for f, m in ORD.items():
        C[f] = C[f].astype(str).map(m).fillna(0).astype(np.int8)
    for f in BIN:
        C[f] = (C[f].astype(str) == 'yes').astype(np.int8)
    C['bearers_l'] = np.log1p(C.bearers.fillna(-1).clip(lower=0)).astype(np.float32)
    C.loc[C.bearers.isna(), 'bearers_l'] = -1
    C['oa_n_l'] = np.log1p(C.oa_n.fillna(0)).astype(np.float32)
    C['lc_others'] = C.lc_others.fillna(-1).astype(np.float32)
    C['nco'] = C.nco.fillna(0).astype(np.float32)
    C = C.merge(A, on='key', how='left')
    # the hidden gold credit is a key-log work of the true key: do not count it in that key's work total
    gold_of = dict(zip(PV.pid[PV['mode'] == 'present'], PV.gold[PV['mode'] == 'present']))
    hid = C['mode'].isin(['present']) & (C.key.values == C.pid.map(gold_of).values)
    C['n_works_l'] = np.log1p((C.n_works.fillna(0) - hid.astype(int)).clip(lower=0)).astype(np.float32)
    for b in ['has_orcid', 'has_thesis', 'has_aha', 'has_directory', 'has_lcnaf', 'has_wd', 'has_review_credit', 'only_review_credit',
              'has_supervisor', 'has_review_evidence']:
        C[b] = C[b].fillna(False).astype(np.int8)
    C['n_ids'] = C.n_ids.fillna(0).astype(np.int8)
    C = C.merge(M[['pid', 'tbl', 'role', 'kind', 'year', 'review_record', 'n_auth'] + (['route_a'] if 'route_a' in M else [])], on='pid', how='left')
    C['rg'] = np.where(C.role.isin(['jstor-author', 'reviewer']), C.role, 'author')
    C['gold_table'] = C.tbl.isin(GOLD_TABLES).astype(np.int8)
    C['decade'] = (C.year // 10 * 10).astype('float32')
    C['review_record'] = C.review_record.fillna(False).astype(np.int8)
    C['n_auth'] = C.n_auth.fillna(1).astype(np.float32)
    for f, levels in CATS.items():
        C[f] = pd.Categorical(C[f].astype(str), categories=levels)
    C = set_features(C)
    if USE_P9[0]:
        P9 = pd.read_parquet(inp / 'p9-features.parquet')
        C = C.merge(P9, on=['mode', 'pid', 'key'], how='left')
        # the drop variant is the present block without the true key: the same pairs, the same evidence
        dm = C['mode'].values == 'drop'
        if dm.any():
            pres = P9[P9['mode'] == 'present'].drop(columns=['mode']).set_index(['pid', 'key'])
            j = pres.reindex(pd.MultiIndex.from_arrays([C.pid.values[dm], C.key.values[dm]]))
            for c in P9_F:
                C.loc[dm, c] = j[c].values
        miss = int(C.p9_lrs.isna().sum())
        for c in P9_F:
            C[c] = C[c].fillna(-1.0 if c in ('p9_lcdp', 'p9_lcact') else 0.0).astype(np.float32)
        C = p9_set_features(C)
        print('pass-nine features merged; pairs without them', miss, flush=True)
    print('features', len(C), round(time.time() - t0), 's', flush=True)
    return C, PV, M


# ------------------------------------------------------------------------------------------------ training (Plato)

def strata_of(B):
    """score_links.strata on block rows (the best pair): single-<band> or multi"""
    import numpy as np
    single = (B.n.values == 1) & (B.neg.astype(str).values == 'none')
    return np.where(single, 'single-' + B.freq.astype(str).values, 'multi')


def jeffreys_upper(k, n, q=0.95):
    from scipy.stats import beta
    if n <= 0:
        return 1.0
    return float(beta.ppf(q, k + .5, n - k + .5)) if k < n else 1.0


def wrong_share(d):
    """weighted wrong-link share among linked blocks and its one-sided 95% Jeffreys bound on the Kish effective n"""
    import numpy as np
    L = d[d.link]
    if not len(L):
        return 0.0, 0.0, 0, 0.0
    w = L.w.values
    r = float((w * L.wrong.values).sum() / w.sum())
    neff = w.sum() ** 2 / (w ** 2).sum()
    return r, jeffreys_upper(r * neff, neff), int(len(L)), float(neff)


def train(args):
    """fit the models, calibrate on split 2, choose thresholds on split 2 under the 0.5% bound, evaluate on split 3
    (gold + simulated absents, production-weighted) and on the held-out clerical labels; save model + manifest"""
    import numpy as np
    import pandas as pd
    inp, out = Path(args.inputs), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    KEY_FEATURES[0] = args.key_features
    USE_P9[0] = not args.no_p9 and (inp / 'p9-features.parquet').exists()
    C, PV, M = build_features(inp, args.sample)
    prep_meta = json.load(open(inp / 'prep.json'))
    # ---- block table: one row per (mode, pid)
    PV = PV.copy()
    dv = PV[PV['mode'] == 'present'].copy()
    dv['mode'] = 'drop'
    dv['rule_state'], dv['rule_key'] = dv.rule_drop_state, dv.rule_drop_key
    PV = pd.concat([PV, dv], ignore_index=True)
    # labels of production positions from the clerical sets
    CL = pd.read_csv(inp / 'clerical-labels.csv', dtype=str)
    CL = CL[~CL.label.isin(['cannot-tell', 'disagree'])]
    CL['pid'] = CL.pid.astype('int64')
    same = {int(p): ({l} | {x for x in str(d).split('|') if x.startswith('p-')}) for p, l, d in zip(CL.pid, CL.label, CL.duplicate_keys.fillna(''))}
    lab_of = {int(p): l for p, l in zip(CL.pid, CL.label)}
    csplit = {int(p): s for p, s in zip(CL.pid, CL.split)}
    prod = C['mode'].values == 'prod'
    isc = prod & C.pid.isin(set(lab_of)).values
    lab = C.label.values.astype(np.int64).copy()
    for i in np.nonzero(isc)[0]:
        p, k = int(C.pid.values[i]), C.key.values[i]
        lab[i] = 1 if k == lab_of[p] else 2 if k in same[p] else 0
    # Qwen production labels (2026-11-13): the candidates the labeller saw get 1 (its key), 2 (a duplicate it named) or
    # 0; candidates it did not see stay unlabelled (-1); cannot-tell and errors are left out
    Q = load_qwen(args.qwen_labels, set(lab_of), args) if args.qwen_labels else None
    qsplit = np.full(len(C), '', dtype=object)
    if Q is not None:
        qd = Q.set_index('position')
        isq = prod & C.pid.isin(set(qd.index)).values
        dec, dups, shown, qs = qd.decision.to_dict(), qd.dups.to_dict(), qd.shown.to_dict(), qd.qsplit.to_dict()
        for i in np.nonzero(isq)[0]:
            p, k = int(C.pid.values[i]), C.key.values[i]
            d = dec[p]
            lab[i] = 1 if k == d else 2 if k in dups[p] else 0 if k in shown[p] else -1
            qsplit[i] = qs[p]
    C['y'] = lab
    C['qwen'] = qsplit
    C['clerical'] = np.where(isc, C.pid.map(csplit), '')
    split = dict(zip(zip(PV['mode'], PV.pid), PV.split))
    C['split'] = [split.get((m, p), -1) for m, p in zip(C['mode'].values, C.pid.values)]
    C.loc[C['mode'] == 'drop', 'split'] = C.loc[C['mode'] == 'drop', 'pid'].map(dict(zip(PV.pid[PV['mode'] == 'present'], PV.split[PV['mode'] == 'present'])))
    ra = C.route_a.fillna(False).astype(bool).values if 'route_a' in C else np.zeros(len(C), bool)
    C.loc[ra & (C['mode'].values != 'prod'), 'split'] = -1        # route-a gold is unreliable (decide2 excludes it)
    print('labels', C.groupby('mode').y.value_counts().unstack().fillna(0).astype(int).to_dict(), flush=True)
    # ---- block weights: simulated absents and present gold mixed to each stratum's production absent share
    B = C[C['rank'] == 0][['mode', 'pid', 'n', 'neg', 'freq', 'rg', 'split', 'clerical', 'qwen']].copy()
    B['stratum'] = strata_of(B)
    pres_true = set(zip(C['mode'][C.y == 1], C.pid[C.y == 1]))
    B['present'] = [(m, p) in pres_true for m, p in zip(B['mode'], B.pid)]
    pi = prep_meta['absent_share']
    PB = B[B['mode'] == 'prod']
    nprod = PB.groupby(['rg', 'stratum']).size()
    w = np.zeros(len(B))
    for s in (0, 1, 2, 3):
        for (rg, st), g in B[(B.split == s) & (B['mode'] != 'prod')].groupby(['rg', 'stratum']):
            p = pi.get(rg, {}).get(st, {}).get('pi', 0.5)
            npd = nprod.get((rg, st), 0)
            pr, ab = g.index[g.present.values], g.index[~g.present.values]
            if len(pr):
                w[B.index.get_indexer(pr)] = npd * (1 - p) / len(pr)
            if len(ab):
                w[B.index.get_indexer(ab)] = npd * p / len(ab)
    B['w'] = w
    for s in (0, 1, 2, 3):
        m = (B.split == s) & (B['mode'] != 'prod')
        if m.any() and B.w[m].sum() > 0:
            B.loc[m, 'w'] = B.w[m] / B.w[m].mean()
    B.loc[B.clerical != '', 'w'] = args.clerical_weight
    if args.clerical_mode == 'validate':
        B.loc[B.clerical == 'clerical-dev', 'w'] = 1.0
    # simulated absent authors (the impersonated namesake and the present block without its author) in the training
    # split: kept, down-weighted or dropped (run 3 learned from them that well-documented keys absorb namesakes)
    sim = (B.split == 1) & B['mode'].isin(['imp', 'drop'])
    if args.sim_absent == 'drop':
        B.loc[sim, 'w'] = 0.0
    elif args.sim_absent == 'down':
        B.loc[sim, 'w'] = B.w[sim] * args.sim_absent_weight
    B['pw'] = 0.0
    if Q is not None:
        qd = Q.set_index('position')
        qm = B['mode'].eq('prod') & B.pid.isin(set(qd.index))
        B.loc[qm, 'w'] = B.pid[qm].map(qd.tw).values
        B.loc[qm, 'pw'] = B.pid[qm].map(qd.weight).values
    C = C.merge(B[['mode', 'pid', 'w', 'pw', 'stratum']], on=['mode', 'pid'], how='left')
    trn = ((C.split == 1) & (C['mode'] != 'prod')) | ((C.clerical == 'clerical-dev') & (args.clerical_mode == 'train')) | (C.qwen == 'qwen-train')
    trn &= C.w.values > 0
    trn &= C.y.isin([0, 1]).values
    cal = ((C.split == 2) & (C['mode'] != 'prod')) | (C.qwen == 'qwen-cal')
    tst = (C.split == 3) & (C['mode'] != 'prod')
    feats = feature_names()
    counts = dict(train_pairs=int(trn.sum()), train_pos=int(C[trn].y.sum()), calib_pairs=int(cal.sum()), test_pairs=int(tst.sum()),
                  blocks={f'{m}': int(((B['mode'] == m)).sum()) for m in ('present', 'imp', 'drop', 'prod')},
                  blocks_by_split={str(s): {m: int(((B['mode'] == m) & (B.split == s)).sum()) for m in ('present', 'imp', 'drop')} for s in (0, 1, 2, 3)},
                  absent_blocks_with_candidates={m: int(((B['mode'] == m) & ~B.present).sum()) for m in ('present', 'imp', 'drop')},
                  clerical={s: int((B.clerical == s).sum()) for s in ('clerical-dev', 'clerical-test')},
                  qwen={s: int((B.qwen == s).sum()) for s in ('qwen-train', 'qwen-cal', 'qwen-test')},
                  qwen_linked={s: int(((B.qwen == s) & B.present).sum()) for s in ('qwen-train', 'qwen-cal', 'qwen-test')},
                  sim_absent=dict(mode=args.sim_absent, weight=args.sim_absent_weight, training_blocks=int(sim.sum())),
                  pass_nine_features=USE_P9[0],
                  clerical_class={s: {k: int(v) for k, v in pd.Series([('key' if lab_of[p].startswith('p-') else lab_of[p]) for p in B.pid[B.clerical == s]]).value_counts().items()}
                                  for s in ('clerical-dev', 'clerical-test')})
    print('counts', json.dumps(counts), flush=True)
    X = C[feats]
    mono = [1 if f in mono_up() else 0 for f in feats]
    models = {}
    # (A) one pair model over present and absent blocks
    models['gbt'] = fit_gbt(X[trn], C.y[trn], C.w[trn], mono, feats, args.seed)
    models['logit'] = fit_logit(X[trn], C.y[trn], C.w[trn], feats)
    # (B) two stages: pair model on present blocks only, position model P(author present | best pair) on all blocks
    trp = trn & C['mode'].isin(['present', 'prod']).values & C.groupby(['mode', 'pid']).y.transform('max').eq(1).values
    st1 = fit_gbt(X[trp], C.y[trp], C.w[trp], mono, feats, args.seed)
    raw = {}
    for name, m in models.items():
        raw[name] = predict(m, X)
    p1 = predict(st1, X)
    C['_p1'] = p1
    C['_p1max'] = C.groupby(['mode', 'pid'], observed=True)._p1.transform('max')
    # position model features: the stage-1 best pair's features plus its stage-1 probability
    bestrow = C['_p1'].values >= C['_p1max'].values - 1e-12
    Bt = C[bestrow].drop_duplicates(['mode', 'pid'])
    pres_blocks = C.groupby(['mode', 'pid']).y.max()
    Bt_y = pd.Series([pres_blocks.get((m, p), 0) for m, p in zip(Bt['mode'], Bt.pid)], index=Bt.index).clip(upper=1)
    f2 = feats + ['_p1']
    trb = (((Bt.split == 1) & (Bt['mode'] != 'prod')) | ((Bt.clerical == 'clerical-dev') & (args.clerical_mode == 'train'))
           | (Bt.qwen == 'qwen-train')) & (Bt.w > 0)
    st2 = fit_gbt(Bt.loc[trb, f2], Bt_y[trb], Bt.w[trb], mono + [1], f2, args.seed)
    p2 = dict(zip(zip(Bt['mode'], Bt.pid), predict(st2, Bt[f2])))
    raw['two-stage'] = p1 * np.array([p2.get((m, p), 0.0) for m, p in zip(C['mode'].values, C.pid.values)])
    raw['fs'] = 1 / (1 + np.exp2(-C.fs.values))
    # ---- calibration (isotonic, split 2, weighted), pair level
    from sklearn.isotonic import IsotonicRegression
    calp = {}
    cm = cal & C.y.isin([0, 1]).values
    for name, r in raw.items():
        iso = IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1).fit(r[cm], C.y[cm], sample_weight=C.w[cm])
        calp[name] = iso.predict(r)
    # ---- decisions per block for every model; thresholds on split 2 per (role group, single/multi)
    res = dict(counts=counts, gold_cleanup=prep_meta['gold_cleanup'], seed=args.seed, clerical_weight=args.clerical_weight)
    blocks = {}
    for name, p in calp.items():
        blocks[name] = block_table(C, p)
    th = {}
    for name, BT in blocks.items():
        th[name] = choose_thresholds(BT[(BT.split == 2) & (BT['mode'] != 'prod')], args.bound)
        if args.clerical_mode == 'validate':
            th[name] = validate_on_clerical(BT[BT.clerical == 'clerical-dev'], th[name], args.bound)
        if Q is not None:
            # production-drawn check on the Qwen calibration labels (production weights): can only raise thresholds
            th[name] = validate_on_clerical(BT[BT.qwen == 'qwen-cal'].assign(w=lambda d: d.pw), th[name], args.bound,
                                            weighted=True, tag='_qwen_cal_check')
    res['thresholds'] = th
    # head-to-head on split 3 and clerical-test: rule linker, naive scorer C2, each model
    BT0 = blocks['gbt']
    ev = {}
    for name, BT in blocks.items():
        D = apply_thresholds(BT, th[name])
        ev[name] = dict(test=evaluate_blocks(D[(D.split == 3) & (D['mode'] != 'prod')]),
                        clerical_test=evaluate_blocks(D[D.clerical == 'clerical-test']),
                        clerical_dev=evaluate_blocks(D[D.clerical == 'clerical-dev']),
                        qwen_test=evaluate_blocks(D[D.qwen == 'qwen-test'].assign(w=lambda d: d.pw)))
    for name in ('rule', 'scorer-c2'):
        D = baseline_blocks(BT0, C, PV, inp, name, prep_meta)
        ev[name] = dict(test=evaluate_blocks(D[(D.split == 3) & (D['mode'] != 'prod')]),
                        clerical_test=evaluate_blocks(D[D.clerical == 'clerical-test']),
                        qwen_test=evaluate_blocks(D[D.qwen == 'qwen-test'].assign(w=lambda d: d.pw)))
        if name == 'scorer-c2':
            # the production policy: the scorer's links stand; the classifier adds links where the scorer made none
            F = apply_thresholds(blocks[args.final], th[args.final])
            fk = dict(zip(zip(F['mode'], F.pid), np.where(F.link, F.key, '')))
            lab = dict(zip(zip(C['mode'].values, C.pid.values, C.key.values), C.y.values))
            D2 = D.copy()
            D2['added'] = [(not l) and bool(fk.get((m, p), '')) for l, m, p in zip(D2.link, D2['mode'], D2.pid)]
            D2['key'] = [k if l else fk.get((m, p), '') for k, l, m, p in zip(D2.key, D2.link, D2['mode'], D2.pid)]
            D2['y'] = [lab.get((m, p, k), 0) if k else -1 for m, p, k in zip(D2['mode'], D2.pid, D2.key)]
            D2['link'] = D2.key.astype(str) != ''
            D2['wrong'] = D2.link & (D2.y != 1) & (D2.y != 2)
            ev['scorer+' + args.final] = dict(test=evaluate_blocks(D2[(D2.split == 3) & (D2['mode'] != 'prod')]),
                                             clerical_test=evaluate_blocks(D2[D2.clerical == 'clerical-test']),
                                             added_test=evaluate_blocks(D2[(D2.split == 3) & (D2['mode'] != 'prod') & D2.added]),
                                             added_clerical_test=evaluate_blocks(D2[(D2.clerical == 'clerical-test') & D2.added]),
                                             qwen_test=evaluate_blocks(D2[D2.qwen == 'qwen-test'].assign(w=lambda d: d.pw)),
                                             added_qwen_test=evaluate_blocks(D2[(D2.qwen == 'qwen-test') & D2.added].assign(w=lambda d: d.pw)))
    res['evaluation'] = ev
    best = args.final
    res['final_model'] = best
    # inspectable: importances, partial dependence
    res['importance'] = importance(models['gbt'], feats)
    res['partial_dependence'] = partial_dep(models['gbt'], X[tst].sample(min(5000, int(tst.sum())), random_state=args.seed),
                                            ['fs', 'margin', 'runner_fs', 'n', 'topic', 'name', 'share', 'other_ctx_any'])
    save_models(out, models, st1, st2, feats, mono, f2, raw, C, cm, args)
    # production decisions of the final model
    D = apply_thresholds(blocks[best], th[best])
    prodD = D[D['mode'] == 'prod']
    res['production'] = prodD.decision.value_counts().to_dict()
    res['production_by_stratum'] = {k: v.decision.value_counts().to_dict() for k, v in prodD.groupby('stratum')}
    if Q is not None:
        res['rule_weak_by_qwen'] = rule_weak_by_qwen(args.qwen_labels)
    res['probes'] = probes(args, C, D, M, blocks, th)
    pc = C[C['mode'] == 'prod'][['pid', 'key', 'rank']].copy()
    pc['p'] = calp[best][(C['mode'] == 'prod').values]
    contrib = top_features(models['gbt'] if best == 'gbt' else None, X[(C['mode'] == 'prod').values], feats) if best == 'gbt' else \
        fs_fields(C[C['mode'] == 'prod'], prep_meta)
    pc['top'] = contrib
    write_classified(out, prodD, pc, M)
    keepb = ['mode', 'pid', 'key', 'p', 'p2', 'y', 'has_author', 'split', 'clerical', 'qwen', 'pw', 'w', 'stratum', 'rg', 'role', 'tbl', 'freq', 'n', 'fs', 'margin', 'decision', 'link', 'wrong']
    for name in blocks:
        D = apply_thresholds(blocks[name], th[name])
        D[(D['mode'] != 'prod') & D.split.isin([2, 3]) | (D.clerical != '') | (D.qwen != '')][keepb].to_parquet(out / f'blocks-{name}.parquet', index=False)
    json.dump(res, open(out / 'train-report.json', 'w'), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k in ('counts', 'thresholds', 'production')}, default=float, indent=1))
    for name, e in ev.items():
        print(name, 'TEST', json.dumps(e['test'].get('overall')), '\n   CLERICAL', json.dumps(e['clerical_test'].get('overall')), flush=True)
    print('done', round(time.time() - t0), 's', flush=True)


def _qhash(pid, salt):
    return int(hashlib.md5(f'{salt}:{int(pid)}'.encode()).hexdigest()[:8], 16)


def load_qwen(path, exclude, args):
    """qwen-labels.csv.gz (label_links_qwen.py write, policy greedy+sc) -> one row per decided position: decision (a key
    or not-keyed), duplicates it named, the keys it saw (shown + own-book excluded), training weight `tw`, production
    weight `weight`, split qwen-train / qwen-cal / qwen-test. Positions in the Opus clerical sets are left out (the
    held-out half stays untouched). Label weights (owner, 2026-11-13; the labeller's measured errors were plausible-topic
    links on one candidate with a very common name): a link on a single-candidate position in the 26+ band x qwen_w26;
    a link on a single-candidate position with no positive fact (the linker's has_fact, or no fact stated by Qwen)
    x qwen_wnofact. Held out: a fixed hash share (default 0.125 = 5,000 of the 40,000 sample), the rest 1 in 5 to
    calibration."""
    import numpy as np
    import pandas as pd
    Q = pd.read_csv(path, dtype=str, keep_default_na=False)
    n0 = len(Q)
    Q['position'] = Q.position.astype('int64')
    Q = Q[~Q.position.isin(exclude)].copy()
    dec = Q.decision.astype(str)
    Q = Q[dec.str.startswith('p-') | (dec == 'not-keyed')].copy()
    Q['dups'] = [set(x for x in d.split('|') if x.startswith('p-')) for d in Q.duplicate_keys]
    Q['shown'] = [set(x for x in s_.split('|') if x.startswith('p-')) | {x.split(':')[0] for x in e.split('|') if x.startswith('p-')}
                  for s_, e in zip(Q.candidates_shown, Q.excluded)]
    single = Q.band.astype(str).str.startswith('single').values
    link = Q.decision.str.startswith('p-').values
    nofact = Q.nofact.astype(str).str.lower().isin(['true', '1']).values | (Q.facts.astype(str).str.strip() == '').values
    tw = np.full(len(Q), float(args.qwen_weight))
    tw[single & link & (Q.band.values == 'single-26+')] *= args.qwen_w26
    tw[single & link & nofact] *= args.qwen_wnofact
    Q['tw'] = tw
    Q['weight'] = pd.to_numeric(Q.weight, errors='coerce').fillna(1.0)
    h = np.array([_qhash(p, 'qwen-holdout') % 10000 for p in Q.position])
    h2 = np.array([_qhash(p, 'qwen-cal') % 5 for p in Q.position])
    Q['qsplit'] = np.where(h < args.qwen_holdout * 10000, 'qwen-test', np.where(h2 == 0, 'qwen-cal', 'qwen-train'))
    print('qwen labels', n0, 'rows;', len(Q), 'decided (key or not-keyed) outside the clerical sets;',
          Q.qsplit.value_counts().to_dict(), 'links', int(link.sum()), 'down-weighted', int((tw < args.qwen_weight).sum()), flush=True)
    return Q


def rule_weak_by_qwen(path):
    """the rule linker's existing links in the weak strata (sample cells rule-weak|*): Qwen's verdicts, weighted to
    production (weight = production count / sampled). right = Qwen names the rule's key (or a duplicate of it); wrong =
    another key or not-keyed; undecided = cannot-tell / error (reported, not counted)"""
    import numpy as np
    import pandas as pd
    Q = pd.read_csv(path, dtype=str, keep_default_na=False)
    Q = Q[Q.cell.str.startswith('rule-weak|')].copy()
    if not len(Q):
        return {}
    Q['w'] = pd.to_numeric(Q.weight, errors='coerce').fillna(1.0)
    Q['out'] = ['right' if d == k or k in set(dk.split('|')) else 'undecided' if not (d.startswith('p-') or d == 'not-keyed') else 'wrong'
                for d, k, dk in zip(Q.decision, Q.rule_key, Q.duplicate_keys)]

    def one(g):
        dd = g[g.out != 'undecided']
        if not len(dd):
            return dict(n=int(len(g)), undecided=int(len(g)))
        w = dd.w.values
        r = float((w * (dd.out == 'wrong').values).sum() / w.sum())
        neff = w.sum() ** 2 / (w ** 2).sum()
        return dict(n=int(len(g)), decided=int(len(dd)), undecided=int((g.out == 'undecided').sum()), wrong=int((dd.out == 'wrong').sum()),
                    wrong_not_keyed=int(((dd.out == 'wrong') & (dd.decision == 'not-keyed')).sum()),
                    wrong_share_production=round(r, 4), upper95=round(jeffreys_upper(r * neff, neff), 4),
                    production_links=round(float(g.w.sum())))
    out = dict(overall=one(Q))
    out['by_cell'] = {c: one(g) for c, g in Q.groupby('cell')}
    out['note'] = ("Qwen (greedy+sc) on rule-linked positions sampled from the weak strata; Qwen's own error on the Opus "
                   "held-out half was 0.71% (upper 1.9%) of its links and it abstains on ~9% of Opus links, so 'wrong' here "
                   "includes Qwen's not-keyed on true links (a missed author counts against the rule)")
    return out


def probes(args, C, D, M, blocks, th):
    """the owner's probe positions (never targets): decisions of the final model on every production block where a
    probe key is a candidate, and on the probe works"""
    keys = [k for k in (args.probe_keys or '').split(',') if k]
    works = [w for w in (args.probe_works or '').split(',') if w]
    pc = C[C['mode'] == 'prod'][['pid', 'key', 'fs']]
    pids = set(pc.pid[pc.key.isin(keys)]) | set(M.pid[M.work.isin(works)])
    if not pids:
        return {}
    cand = pc[pc.pid.isin(pids)].sort_values(['pid', 'fs'], ascending=[True, False]).groupby('pid').key.apply(lambda s: '|'.join(s)).to_dict()
    R = D[(D['mode'] == 'prod') & D.pid.isin(pids)][['pid', 'key', 'p', 'p2', 'decision', 'stratum', 'rg', 'multi']].merge(
        M[['pid', 'work', 'role', 'printed']], on='pid', how='left')
    R['candidates'] = R.pid.map(cand)
    R['p'] = R.p.round(4)
    R['p2'] = R.p2.round(4)
    out = {}
    for k in keys:
        g = R[R.candidates.str.contains(k, regex=False)]
        out[k] = dict(positions=int(len(g)), by_cell={c: x.decision.value_counts().to_dict() for c, x in g.groupby(g.rg.astype(str) + '|' + g.multi.astype(str))},
                      linked_to_key=int(((g.decision == 'link') & (g.key == k)).sum()),
                      linked_to_other=int(((g.decision == 'link') & (g.key != k)).sum()),
                      rows=g.head(60).to_dict('records'))
    for w in works:
        out[w] = R[R.work == w].to_dict('records')
    return out


def fit_gbt(X, y, w, mono, feats, seed):
    try:
        import lightgbm as lgb
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.05, num_leaves=63, min_child_samples=50, subsample=0.8,
                               subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, monotone_constraints=mono,
                               monotone_constraints_method='advanced', random_state=seed, n_jobs=int(os.environ.get('SLURM_CPUS_PER_TASK', 4)),
                               verbose=-1)
        m.fit(X, y, sample_weight=w, categorical_feature=[f for f in feats if f in CATS])
        m.kind_ = 'lightgbm'
        return m
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        m = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=63, min_samples_leaf=50, l2_regularization=1.0,
                                           monotonic_cst=mono, categorical_features='from_dtype', random_state=seed)
        m.fit(X, y, sample_weight=w)
        m.kind_ = 'sklearn-hgb'
        return m


def fit_logit(X, y, w, feats):
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.impute import SimpleImputer
    num = [f for f in feats if f not in CATS]
    ct = ColumnTransformer([('num', make_pipeline(SimpleImputer(strategy='median'), StandardScaler()), num),
                            ('cat', OneHotEncoder(handle_unknown='ignore'), [f for f in feats if f in CATS])])
    m = make_pipeline(ct, LogisticRegression(C=0.3, max_iter=2000))
    Xc = X.copy()
    for f in CATS:
        if f in Xc:
            Xc[f] = Xc[f].astype(str)
    m.fit(Xc, y, logisticregression__sample_weight=w)
    m.kind_ = 'logit'
    return m


def predict(m, X):
    if getattr(m, 'kind_', '') == 'logit':
        X = X.copy()
        for f in CATS:
            if f in X:
                X[f] = X[f].astype(str)
    out = []
    for i in range(0, len(X), 500000):
        out.append(m.predict_proba(X.iloc[i:i + 500000])[:, 1])
    import numpy as np
    return np.concatenate(out) if out else np.zeros(0)


def block_table(C, p):
    """per block: best candidate and its probability, the runner-up probability, whether the best is right / a
    duplicate / wrong, whether the block holds the author, weights and strata attributes"""
    import numpy as np
    import pandas as pd
    D = pd.DataFrame({'mode': C['mode'].values, 'pid': C.pid.values, 'key': C.key.values, 'p': p, 'y': C.y.values})
    D = D.sort_values(['mode', 'pid', 'p'], ascending=[True, True, False], kind='stable')
    g = D.groupby(['mode', 'pid'], sort=False)
    first = D[g.cumcount().values == 0].copy()
    sec = D[g.cumcount().values == 1][['mode', 'pid', 'p']].rename(columns={'p': 'p2'})
    has = D.assign(_t=(D.y.values == 1)).groupby(['mode', 'pid'], sort=False)._t.max().rename('has_author').reset_index()
    BT = first.merge(sec, on=['mode', 'pid'], how='left').merge(has, on=['mode', 'pid'], how='left')
    BT['p2'] = BT.p2.fillna(0.0)
    attrs = C[C['rank'] == 0][['mode', 'pid', 'split', 'clerical', 'qwen', 'w', 'pw', 'stratum', 'rg', 'role', 'tbl', 'gold_table', 'freq', 'n', 'has_orcid', 'country', 'decade', 'fs', 'margin']]
    BT = BT.merge(attrs, on=['mode', 'pid'], how='left')
    BT['multi'] = np.where(BT.stratum == 'multi', 'multi', 'single')
    BT['rg_multi'] = BT.rg.astype(str) + '|' + BT.multi
    return BT


def choose_thresholds(T, bound):
    """per (role group, single/multi): the (t_link, t_other) with the highest weighted recall whose wrong-link share
    has a one-sided 95% upper bound <= bound on the calibration blocks"""
    import numpy as np
    grid_l = np.round(np.r_[np.arange(0.50, 0.95, 0.025), np.arange(0.95, 1.0001, 0.005)], 4)
    grid_o = [0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
    out = {}
    for (rg, mu), g in T.groupby(['rg', 'multi']):
        best = None
        for to in grid_o:
            for tl in grid_l:
                link = (g.p.values >= tl) & (g.p2.values < to) & (g.gold_table.values == 1)
                d = g.assign(link=link, wrong=link & (g.y.values != 1) & (g.y.values != 2))
                r, up, n, neff = wrong_share(d)
                if n == 0 or up > bound:
                    continue
                rec = float((g.w.values * (link & (g.y.values >= 1) & (g.y.values <= 2))).sum() / max(1e-9, (g.w.values * g.has_author.values).sum()))
                if best is None or rec > best['recall']:
                    best = dict(t_link=round(float(tl), 4), t_other=to, recall=round(rec, 4), wrong=round(r, 5), upper=round(up, 5), links=n, neff=round(neff, 1))
        out[f'{rg}|{mu}'] = best or dict(t_link=2.0, t_other=0.0, recall=0.0, note='no threshold meets the bound')
    return out


def validate_on_clerical(V, th, bound, step=0.005, weighted=False, tag='_clerical_dev_check'):
    """production-drawn check of gold-calibrated thresholds: while the clerical-dev links (positions not used in
    training) hold wrong links above the bound, raise the single-candidate link thresholds of the groups that made
    them (owner's bound; the clerical set is too small to set thresholds alone, so it can only make them stricter)"""
    th = json.loads(json.dumps(th))
    for _ in range(200):
        D = apply_thresholds(V, th)
        L = D[D.link]
        if not len(L) or (float((L.w * L.wrong).sum() / max(1e-12, L.w.sum())) if weighted else L.wrong.mean()) <= bound:
            break
        bad = L[L.wrong].groupby(['rg', 'multi']).size()
        for (rg, mu), _n in bad.items():
            t = th[f'{rg}|{mu}']
            t['t_link'] = round(min(2.0, t['t_link'] + step), 4)
            t['raised_by_clerical'] = True
    D = apply_thresholds(V, th)
    th[tag] = dict(links=int(D.link.sum()), wrong=int(D.wrong.sum()))
    return th


def apply_thresholds(BT, th, t_review=0.2):
    import numpy as np
    th = {k: v for k, v in th.items() if not k.startswith('_')}
    tl = np.array([th.get(f'{r}|{m}', {}).get('t_link', 2.0) for r, m in zip(BT.rg, BT.multi)])
    to = np.array([th.get(f'{r}|{m}', {}).get('t_other', 0.0) for r, m in zip(BT.rg, BT.multi)])
    link = (BT.p.values >= tl) & (BT.p2.values < to) & (BT.gold_table.values == 1)
    D = BT.copy()
    D['link'] = link
    D['decision'] = np.where(link, 'link', np.where(BT.p.values >= t_review, 'review', 'none'))
    D['wrong'] = link & (D.y.values != 1) & (D.y.values != 2)
    return D


def evaluate_blocks(D):
    """overall and per stratum: links, weighted wrong share with its upper bound, recall of present authors"""
    out = {}

    def one(g):
        r, up, n, neff = wrong_share(g)
        hw = (g.w * g.has_author).sum()
        rec = float((g.w * (g.link & (g.y >= 1) & (g.y <= 2))).sum() / hw) if hw > 0 else None
        return dict(blocks=int(len(g)), links=n, wrong_links=int(g.wrong.sum()), wrong_share=round(r, 5), upper95=round(up, 5),
                    recall=None if rec is None else round(rec, 4), authors_present=int(g.has_author.sum()))
    if not len(D):
        return {}
    out['overall'] = one(D)
    for col in ('multi', 'stratum', 'role', 'has_orcid', 'country', 'decade', 'rg', 'rg_multi'):
        out['by_' + col] = {str(k): one(g) for k, g in D.groupby(col)}
    return out


def baseline_blocks(BT0, C, PV, inp, name, prep_meta):
    """the same blocks decided by the rule linker (its state on that variant) or the round-two naive scorer (C2
    thresholds on the Fellegi-Sunter score); the block's labels and weights from the classifier table"""
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    D = BT0.drop(columns=['key', 'p', 'p2', 'y']).copy()
    lab = dict(zip(zip(C['mode'].values, C.pid.values, C.key.values), C.y.values))
    if name == 'rule':
        rk = dict(zip(zip(PV['mode'], PV.pid), zip(PV.rule_state.fillna(''), PV.rule_key.fillna(''))))
        keys = []
        for m, p in zip(D['mode'], D.pid):
            st, k = rk.get((m, p), ('', ''))
            keys.append(k if st in ('linked', 'exact') and k else '')
    else:
        import score_links as SL
        th = prep_meta['thresholds_c2']
        top = C[C['rank'] == 0][['mode', 'pid', 'key', 'fs', 'runner_fs', 'n', 'neg', 'freq', 'role', 'review_record', 'ctx_w']].rename(columns={'fs': 'score', 'runner_fs': 'runner'})
        top.loc[top.runner <= -30, 'runner'] = np.nan
        top['neg'] = top.neg.astype(str)
        top['freq'] = top.freq.astype(str)
        SL.MARGIN_RULE[0] = True
        dec = SL.decision(top, th)
        kk = dict(zip(zip(top['mode'], top.pid), np.where(dec == 'link', top.key.values, '')))
        keys = [kk.get((m, p), '') for m, p in zip(D['mode'], D.pid)]
    D['key'] = keys
    D['y'] = [lab.get((m, p, k), 0) if k else -1 for m, p, k in zip(D['mode'], D.pid, D.key)]
    D['link'] = D.key.astype(str) != ''
    D['wrong'] = D.link & (D.y != 1) & (D.y != 2)
    return D


def importance(m, feats):
    try:
        imp = m.booster_.feature_importance(importance_type='gain')
    except Exception:
        return {}
    tot = imp.sum() or 1
    return {f: round(float(v / tot), 4) for f, v in sorted(zip(feats, imp), key=lambda x: -x[1])}


def partial_dep(m, Xs, fs):
    """mean predicted probability with one feature set to each of its observed quantiles (others as observed)"""
    import numpy as np
    out = {}
    for f in fs:
        vals = np.unique(np.nanquantile(Xs[f].astype(float), [0, .1, .25, .5, .75, .9, 1])) if f not in CATS else []
        row = {}
        for v in vals:
            X2 = Xs.copy()
            X2[f] = v
            row[str(round(float(v), 3))] = round(float(predict(m, X2).mean()), 4)
        out[f] = row
    return out


FS_FIELDS = ('name', 'freq', 'date', 'aff', 'network', 'venue', 'topic', 'cites', 'neg')


def fs_fields(P, prep_meta):
    """for the calibrated Fellegi-Sunter policy: the comparison levels that carry the most weight (as the scorer's
    links.csv.gz top_fields), from the encoded levels kept in the pairs table"""
    out = []
    lev = {f: P[f].astype(str).values for f in ('freq', 'date', 'neg')}
    for i in range(len(P)):
        parts = [f'freq={lev["freq"][i]}', f'date={lev["date"][i]}']
        for f, nm in (('topic', 'topic'), ('venue', 'venue'), ('network', 'network'), ('aff', 'aff'), ('cites', 'cites')):
            v = P[f].values[i]
            if (f == 'aff' and v >= 2) or (f != 'aff' and v > 0):
                parts.append(f'{nm}+')
        if lev['neg'][i] != 'none':
            parts.append('neg=' + lev['neg'][i])
        out.append('; '.join(parts))
    return out


def top_features(m, X, feats, k=3):
    """per production pair: the three features that raise its log-odds most (LightGBM contributions)"""
    import numpy as np
    if m is None or getattr(m, 'kind_', '') != 'lightgbm':
        return [''] * len(X)
    out = []
    for i in range(0, len(X), 200000):
        c = m.predict(X.iloc[i:i + 200000], pred_contrib=True)[:, :-1]
        idx = np.argsort(-c, axis=1)[:, :k]
        out += ['; '.join(f'{feats[j]}:{c[r, j]:+.2f}' for j in idx[r] if c[r, j] > 0) for r in range(len(c))]
    return out


def save_models(out, models, st1, st2, feats, mono, f2, raw, C, cm, args):
    import pickle
    for name, m in list(models.items()) + [('stage1', st1), ('stage2', st2)]:
        if getattr(m, 'kind_', '') == 'lightgbm':
            m.booster_.save_model(str(out / f'model-{name}.txt'))
        with open(out / f'model-{name}.pkl', 'wb') as f:
            pickle.dump(m, f)
    man = dict(features=feats, monotone_up=[f for f, s in zip(feats, mono) if s], categorical=list(CATS), stage2_features=f2,
               seed=args.seed, clerical_weight=args.clerical_weight, bound=args.bound, final=args.final,
               model_kind={n: getattr(m, 'kind_', '') for n, m in models.items()},
               training='gold splits by hidden key (score_links.split_of): 0 Fellegi-Sunter weights, 1 train, 2 calibration + thresholds, '
                        '3 test; clerical-dev labels validate thresholds (or train at the clerical weight); clerical-test never used before the '
                        'final evaluation; Qwen production labels (when given): qwen-train in training at their label weights, qwen-cal in '
                        'calibration and as a threshold check (production weights), qwen-test (5,000 positions) held out',
               qwen_labels=dict(path=args.qwen_labels, md5=hashlib.md5(Path(args.qwen_labels).read_bytes()).hexdigest()) if args.qwen_labels else None,
               qwen_weights=dict(base=args.qwen_weight, band26=args.qwen_w26, nofact=args.qwen_wnofact, holdout=args.qwen_holdout),
               sim_absent=dict(mode=args.sim_absent, weight=args.sim_absent_weight), pass_nine_features=USE_P9[0],
               inputs={p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in sorted(Path(args.inputs).glob('*')) if p.is_file() and p.stat().st_size < 2e9},
               built=time.strftime('%Y-%m-%d %H:%M'))
    json.dump(man, open(out / 'manifest.json', 'w'), indent=1)


def write_classified(out, D, pc, M):
    """production decisions (link and review; positions below the review bar are left out): position, work, role,
    printed name, decision, person key, probability, runner-up probability, top features"""
    import pandas as pd
    top = pc.set_index(['pid', 'key']).top.to_dict()
    o = D[D.decision.isin(['link', 'review'])][['pid', 'key', 'p', 'p2', 'decision', 'stratum', 'fs', 'margin']].merge(M[['pid', 'work', 'role', 'printed', 'pos']], on='pid', how='left')
    o['top_features'] = [top.get((p, k), '') for p, k in zip(o.pid, o.key)]
    o['fs'] = o.fs.round(3)
    o['margin'] = o.margin.round(3)
    o = o.rename(columns={'pid': 'position', 'key': 'person_key', 'p': 'probability', 'p2': 'runner_up_probability', 'printed': 'printed_name'})
    o['probability'] = o.probability.round(4)
    o['runner_up_probability'] = o.runner_up_probability.round(4)
    o = o.rename(columns={'fs': 'fs_score', 'margin': 'fs_margin'})
    o = o[['position', 'work', 'role', 'pos', 'printed_name', 'decision', 'person_key', 'probability', 'runner_up_probability', 'fs_score', 'fs_margin',
           'stratum', 'top_features']]
    o.sort_values('position').to_csv(out / 'classified.csv.gz', index=False, compression='gzip')


def finalize(args):
    """production table for the loader: the classifier's decisions beside the round-two scorer's; `load` marks the
    classifier links the scorer did not make whose stratum passes the bound on the gold test as additions
    (scorer + classifier policy, added links only: upper 95% bound <= bound, 300+ links); everything else the classifier
    links but cannot certify as an addition stays a candidate. Writes data/graph/scored-links/classified.csv.gz,
    classifier-report.json and classifier-manifest.json"""
    import pandas as pd
    R, out = Path(args.run), ROOT / 'data/graph/scored-links'
    rep = json.load(open(R / 'train-report.json'))
    man = json.load(open(R / 'manifest.json'))
    best = rep['final_model']
    add = rep['evaluation'][f'scorer+{best}']['added_test']['by_stratum']
    ok = sorted(s for s, v in add.items() if v['links'] >= args.min_links and v['upper95'] <= args.bound)
    c = pd.read_csv(R / 'classified.csv.gz')
    d = pd.read_parquet(Path(args.inputs) / 'prod-decided.parquet', columns=['pid', 'decision', 'key'])
    d = d.rename(columns={'pid': 'position', 'decision': 'scorer_decision', 'key': 'scorer_key'})
    c = c.merge(d, on='position', how='left')
    c['load'] = (c.decision == 'link') & (c.scorer_decision != 'link') & c.stratum.isin(ok)
    c['model'] = f"{best} {man['built']} seed {man['seed']}"
    c.to_csv(out / 'classified.csv.gz', index=False, compression='gzip')
    summ = dict(final_model=best, certified_addition_strata=ok, bound=args.bound, min_links=args.min_links,
                rows=int(len(c)), decisions=c.decision.value_counts().to_dict(),
                load=int(c.load.sum()), load_by_role_stratum={f'{r}|{s}': int(n) for (r, s), n in c[c.load].groupby(['role', 'stratum']).size().items()},
                classifier_links_also_scorer_links=int(((c.decision == 'link') & (c.scorer_decision == 'link')).sum()),
                classifier_links_not_certified=int(((c.decision == 'link') & (c.scorer_decision != 'link') & ~c.load).sum()),
                scorer_links_in_classifier_review=int(((c.decision == 'review') & (c.scorer_decision == 'link')).sum()))
    rep['finalize'] = summ
    json.dump(rep, open(out / 'classifier-report.json', 'w'), indent=1, default=float)
    json.dump(man, open(out / 'classifier-manifest.json', 'w'), indent=1)
    print(json.dumps(summ, indent=1))


def read_verdicts(fn):
    """clerical verdict CSV (item, verdict, confidence, duplicate_keys, reason); an unquoted comma in the reason is
    joined back"""
    rows = []
    with open(fn, newline='') as f:
        r = csv.reader(f)
        next(r)
        for x in r:
            if len(x) >= 5:
                rows.append(dict(item=x[0], verdict=x[1].strip(), confidence=x[2], duplicate_keys=x[3], reason=','.join(x[4:]).strip()))
    return rows


def final_verdict(ks, dups):
    """two judges: the same key (or one names the other's key as a duplicate) -> that key; otherwise the cautious
    answer, as in round two: cannot-tell if either said so, else not-keyed if either said so, else disagree"""
    if len(ks) == 1 or ks[0] == ks[1] or (ks[0].startswith('p-') and ks[1].startswith('p-') and (ks[0] in dups or ks[1] in dups)):
        return ks[0]
    return 'cannot-tell' if 'cannot-tell' in ks else 'not-keyed' if 'not-keyed' in ks else 'disagree'


ROLE_ERROR = {'A025', 'A263', 'A352', 'N192', 'N196', 'N295'}   # read 2026-11-12 from the judges' reasons and the dossiers


def label_merge(args):
    """round-three clerical verdicts -> data/graph/scored-links/clerical-labels.csv (the 420 of round two and the new
    positions in one file, with the fixed split: half of each set held out for the final test)"""
    import pandas as pd
    lab = Path(args.labels)
    D = {}
    for line in open(lab / 'new-dossiers.jsonl'):
        d = json.loads(line)
        D[d['item']] = d
    smp = pd.read_csv(lab / 'new-sample.csv', dtype={'pid': str})
    V = defaultdict(list)
    for b in sorted(lab.glob('verdicts-*.csv')):
        for r in read_verdicts(b):
            c = D[r['item']]['candidates']
            v = r['verdict']
            k = c['ABCDE'.index(v)]['key'] if v in 'ABCDE' and len(v) == 1 and 'ABCDE'.index(v) < len(c) else v
            V[r['item']].append(dict(r, key=k, judge=b.stem.split('-')[1]))
    rows = []
    for it, vs in sorted(V.items()):
        ks = [v['key'] for v in vs]
        dups = {x for v in vs for x in (v['duplicate_keys'] or '').split('|') if x.startswith('p-')}
        fin = final_verdict(ks, dups)
        d = D[it]
        rows.append(dict(item=it, pid=d['pid'], work=d['work'], role=d['role'], printed_name=d['printed_name'], title=d['title'][:200],
                         year=d['year'], candidates_shown='|'.join(c['key'] for c in d['candidates']),
                         verdicts='|'.join(ks), judges='|'.join(v['judge'] for v in vs), label=fin,
                         confidence='|'.join(v['confidence'] for v in vs), duplicate_keys='|'.join(sorted(dups - {fin})),
                         reason=vs[0]['reason'], set='round3'))
    N = pd.DataFrame(rows).merge(smp[['item', 'rr', 'band', 'prod_n']], on='item', how='left')
    # round two (420): same columns
    a = pd.read_csv(ROOT / 'data/graph/scored-links/audit-author-role.csv', dtype=str)
    a['label'] = [k if f in ('A', 'B', 'C', 'D') else f for f, k in zip(a.final, a.judged_key)]
    a['role'] = 'author'
    a['set'] = 'round2'
    a = a.rename(columns={'stratum': 'band_r2'})
    A = pd.concat([a[['item', 'pid', 'work', 'role', 'printed_name', 'title', 'year', 'candidates_shown', 'verdicts', 'judges', 'label',
                      'confidence', 'duplicate_keys', 'reason', 'set']], N], ignore_index=True)
    # fixed split: half of each set held out for the final test (by item hash), never used to fit or choose anything
    # review records whose printed name is the reviewed book's author (the judges named the key of that author): ruling 5,
    # a review's author is the reviewer, so a credit to that key is wrong; label not-keyed, the judged key kept
    A['label_judged'] = A.label
    A['role_error'] = A['item'].isin(ROLE_ERROR)
    A.loc[A.role_error, 'label'] = 'not-keyed'
    A['split'] = ['clerical-test' if int(hashlib.md5(('lc:' + i).encode()).hexdigest()[:8], 16) % 2 else 'clerical-dev' for i in A['item']]
    A.to_csv(args.out, index=False)
    dbl = N[N.judges.str.contains(r'\|')]
    agree = sum(1 for v in dbl.verdicts if len(set(v.split('|'))) == 1)
    print(len(A), A.groupby(['set', 'split']).size().to_dict(), 'round-3 double', len(dbl), 'agree (same key)', agree,
          'agree incl. duplicates', int((~dbl.label.isin(['disagree', 'cannot-tell', 'not-keyed']) | dbl.verdicts.map(lambda v: len(set(v.split('|'))) == 1)).sum()))
    print(A.groupby('set').label.apply(lambda s: s.map(lambda x: 'key' if x.startswith('p-') else x).value_counts().to_dict()).to_dict())
    print(dbl[dbl.verdicts.map(lambda v: len(set(v.split('|'))) > 1)][['item', 'verdicts', 'label', 'reason']].to_string())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('label-sample')
    a = sub.add_parser('label-dossiers')
    a.add_argument('--positions', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--text')
    a.add_argument('--no-facts', action='store_true')
    a.add_argument('--limit', type=int)
    a.add_argument('--chunk', type=int, default=5000)
    a = sub.add_parser('label-merge')
    a.add_argument('--labels', default=str(J / 'labels'))
    a.add_argument('--out', default=str(ROOT / 'data/graph/scored-links/clerical-labels.csv'))
    a = sub.add_parser('prep')
    a.add_argument('--out', default=str(J / 'clf-inputs'))
    a = sub.add_parser('train')
    a.add_argument('--inputs', default=str(J / 'clf-inputs'))
    a.add_argument('--out', default=str(J / 'clf-out'))
    a.add_argument('--seed', type=int, default=20261112)
    a.add_argument('--bound', type=float, default=0.005)
    a.add_argument('--clerical-weight', type=float, default=20.0)
    a.add_argument('--final', default='gbt')
    a.add_argument('--clerical-mode', default='validate', choices=['validate', 'train'])
    a.add_argument('--key-features', action='store_true', help='use key attributes as features (run 2; confounded)')
    a.add_argument('--sample', type=float, default=0.0, help='development: keep this share of positions (by pid hash)')
    a.add_argument('--qwen-labels', help='qwen-labels.csv.gz (label_links_qwen.py write): production training labels')
    a.add_argument('--qwen-weight', type=float, default=1.0)
    a.add_argument('--qwen-w26', type=float, default=0.3, help='x weight of single-candidate links in the 26+ name band')
    a.add_argument('--qwen-wnofact', type=float, default=0.5, help='x weight of single-candidate links with no positive fact')
    a.add_argument('--qwen-holdout', type=float, default=0.125, help='held-out share of the Qwen positions (5,000 of 40,000)')
    a.add_argument('--sim-absent', default='down', choices=['keep', 'down', 'drop'],
                   help='simulated absent-author blocks (imp, drop) in the training split')
    a.add_argument('--sim-absent-weight', type=float, default=0.1)
    a.add_argument('--no-p9', action='store_true', help='leave out the pass-eight/nine evidence features')
    a.add_argument('--probe-keys', default='p-4256,p-24137')
    a.add_argument('--probe-works', default='doi:10.2307/j.ctvxkn5q7.4')
    a = sub.add_parser('p9-inputs')
    a.add_argument('--out', default=str(J / 'clf-inputs'))
    a.add_argument('--siblings', default=str(J.parent / 'nameonly8' / 'sibling-chapters.parquet'))
    a = sub.add_parser('p9-features')
    a.add_argument('--inputs', default=str(J / 'clf-inputs'))
    a.add_argument('--procs', type=int, default=4)
    a.add_argument('--sample', type=float, default=0.0)
    a = sub.add_parser('finalize')
    a.add_argument('--run', required=True, help='folder with train-report.json, manifest.json, classified.csv.gz')
    a.add_argument('--inputs', default=str(J / 'clf-inputs'))
    a.add_argument('--bound', type=float, default=0.005)
    a.add_argument('--min-links', type=int, default=300)
    args = ap.parse_args()
    if args.cmd == 'finalize':
        return finalize(args)
    {'label-sample': sample_new, 'label-dossiers': export, 'label-merge': label_merge, 'prep': prep, 'train': train,
     'p9-inputs': p9_inputs, 'p9-features': p9_features}[args.cmd](args)


if __name__ == '__main__':
    main()
