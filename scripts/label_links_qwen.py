"""Qwen3.8-27B as a clerical labeller for works-to-people record linkage (2026-11-12).

Owner (2026-11-12): "you should try ssh nibi"; earlier "we can probably get Qwen 3.8 27b running". The link classifier
(scripts/train_link_classifier.py) trained on masked key-log gold plus simulated absent authors failed on real production
cases (the simulation is unlike production: well-documented keys absorbed namesakes); only 1,020 production positions
carry clerical labels (Opus judges reading dossiers; double-judged agreement 59/60 and 100/100). Census linkers train on
tens of thousands of hand-linked real pairs. This script lets Qwen3.8-27B (FP8, vLLM 0.25, one H100 on Nibi) read the
same dossiers and label production positions, if and only if it matches the Opus labels on the held-out half.

Hard rules, enforced in code before the model sees a case (owner's standing rulings):
  - date-impossible candidates are gone upstream (score_links' date filter and L.HARD proofs; never shown);
  - a printed second given name or second initial that disagrees with the key excludes the key (upstream:
    link_work_people.name_level_wp in the name block);
  - a review's author is the reviewer: on a review, a candidate who wrote the reviewed book is excluded (own_book);
  - OpenAlex author profiles are not shown (the 'openalex' identifier kind is dropped from the ids line);
  - a position whose every candidate is excluded is not-keyed by rule (the model is not asked).
In the prompt: topic may support, never exclude; no nicknames; never infer identity from a name; link only when one
candidate is plausible AND something positive supports it; otherwise cannot-tell or not-keyed as the evidence indicates.

Subcommands
  dossiers   (local, < 4 GB) positions CSV (item, pid[, candidates_shown]) -> dossier JSONL (metadata only)
  sample     (local) the production labelling sample: review band + single-candidate no-fact class + rule links in weak strata
  run        (Nibi, vLLM) dossier JSONL -> verdicts JSONL; greedy pass and/or k sampled passes (candidate order permuted);
             strict JSON by guided decoding (xgrammar); resumable in chunks
  evaluate   (local) verdicts against the clerical labels (fixed dev/test split): agreement, dangerous links, abstentions,
             by stratum, Jeffreys intervals, for each vote policy
  write      (local) production verdicts -> data/graph/scored-links/qwen-labels.csv.gz

Writes no proposal and touches no key log. Never copies thesis text, JSTOR text or notes, or any API key.
"""
import argparse
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
PROMPT_VERSION = 'qll-v1'
K_SHOW = 5
Q = Path(os.environ.get('QL_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                        'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/qwen'))


# ------------------------------------------------------------------------------------------------ hard rules (pure)

def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).lower()


REVIEWISH = re.compile(r'(?i)^\s*review of|\breviews?\b|besprechung|rezension|reseñas?\b|recensioni?\b|comptes? rendus?')


def tnorm(t):
    t = re.sub(r'^\s*(review of|rev\.? of|reseña|compte rendu|besprechung)[:\s]+', '', (t or '').strip(), flags=re.I)
    return ' '.join(re.sub(r'[^a-z0-9 ]+', ' ', fold(t)).split())


def own_book(title, books):
    """the candidate wrote the book the review names: the review title (after 'Review of') begins with one of the
    candidate's key-log book main titles (3+ words, 15+ letters). A title merely containing the book title does not
    count ('Enforcing the English Reformation in Ireland' is not 'The English Reformation')"""
    tt = tnorm(title)
    for b in books:
        bn = tnorm(re.split(r'\s+/\s+|\s*:\s+', b or '')[0])
        if len(bn.split()) >= 3 and len(bn) >= 15 and (tt == bn or tt.startswith(bn + ' ')):
            return b
    return None


def is_reviewish(role, kind, title):
    return role == 'reviewer' or kind == 'review' or bool(REVIEWISH.search(title or ''))


def apply_hard_rules(printed, role, kind, title, cands, books):
    """split candidates into (kept, excluded) by the hard rule that needs the printed record: on a review, a candidate
    who wrote the reviewed book. (Dates and a disagreeing printed second given name or initial are enforced upstream:
    score_links' date filter and link_work_people.name_level_wp; their excluded keys never reach the candidate list.)"""
    keep, excl = [], []
    rv = is_reviewish(role, kind, title)
    for c in cands:
        ob = own_book(title, books.get(c['key'], [])) if rv else None
        if ob:
            excl.append(dict(key=c['key'], label=c['label'], reason=f"wrote the reviewed book ({ob[:80]}); a review's author is the reviewer"))
            continue
        keep.append(c)
    return keep, excl


# ------------------------------------------------------------------------------------------------ prompt, schema, parsing (pure)

SYSTEM = """You are a careful record-linkage clerk for a knowledge graph of scholarship. The graph holds person keys (p-NNN); each key is meant to be one real person. Your task: decide who is the person printed on one work.

You get the work as printed (the printed name, the role of that name, title, kind, year, venue, other names printed on the work, printed affiliation) and the candidate person keys whose names are compatible with the printed name. Every candidate shown has already passed a date test (the work falls inside the candidate's possible career) and a name test. For each candidate you see: identifiers held (lcnaf = Library of Congress authority, wd = Wikidata, orcid, aha-phd = a PhD in the AHA directory, diss-person = a PhD thesis in the corpus, review-credit = a key built from printed review credits, ...), affiliations with sources and years, advisor/student links, co-authors in the graph, and a sample of the candidate's works.

Answer with exactly one decision:
- the key of the candidate who is the printed person (for example "p-1234");
- "not-keyed": the printed person is none of the candidates (a namesake with no key in the graph);
- "cannot-tell": the dossier does not decide (two candidates fit equally, or a candidate and an unkeyed namesake fit equally).

Rules:
1. No false matches: a link to the wrong key is the worst outcome. Link only when one candidate is plausible AND something positive in the dossier supports that candidate (field and period of the work fit the candidate's works, the venue, a co-author, an affiliation, an advisor or student, or a rare name with a compatible career). A rare name with a compatible career is enough; do not be conservative where only one candidate is plausible.
2. When two candidates both fit and nothing separates them, answer "cannot-tell". When the evidence points to someone other than every candidate, answer "not-keyed".
3. Topic or venue overlap may support a link. Lack of topical overlap never excludes a candidate on its own: people change fields and the works shown are only a sample. What can point to a namesake is positive evidence about the printed person: a printed affiliation the candidate never had at that time, co-authors from another profession, or a work that only a member of another profession could have written (for example a clinical, laboratory or engineering paper) when the name is common and the candidate's whole record lies elsewhere.
4. A review's author is the reviewer. Never choose a candidate because he or she wrote the book under review (such candidates were already removed).
5. A printed second given name or second initial that disagrees with a candidate's name excludes that candidate (such candidates were already removed). Do not treat nicknames or short forms as the same name unless the candidate's record shows that form.
6. Shared OpenAlex author profiles are not evidence and are not shown.
7. Never infer identity, nationality, ethnicity or community from a name or the language of a name.
8. Several candidates may be one person split across keys (for example a key built from review credits and a key holding the thesis). If the printed person is one of them and their records are clearly the same person, choose the candidate with the fullest record and list the others in duplicate_keys. Two different people with the same name are not duplicates.
9. In the reason, refer to people as "the candidate", "the author", "the reviewer", "the editor" or by name; do not call them historians.
10. Use only the dossier. In facts, list the specific facts you relied on (short phrases from the dossier). The reason is one sentence.

Return JSON only."""

FACTS_NOTE = ('\n\nEach candidate also has "linkage facts" computed from the graph. "AGAINST:" marks evidence against the candidate; '
              '"no other known bearer of this name" means the name is rare among library authorities and OpenAlex authors; '
              '"26+ known bearers" means very common.')


def schema_for(keys):
    return {
        'type': 'object',
        'properties': {
            'facts': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 5},
            'reason': {'type': 'string'},
            'decision': {'type': 'string', 'enum': list(keys) + ['not-keyed', 'cannot-tell']},
            'confidence': {'type': 'string', 'enum': ['high', 'medium', 'low']},
            'duplicate_keys': {'type': 'array', 'items': {'type': 'string', 'enum': list(keys) or ['none']}, 'maxItems': 4},
        },
        'required': ['facts', 'reason', 'decision', 'confidence', 'duplicate_keys'],
        'additionalProperties': False,
    }


def permute(d, seed):
    """candidate order for a sample: seed 0 keeps the scored order; others shuffle deterministically by (item, seed)"""
    if seed == 0 or len(d['candidates']) < 2:
        return d
    e = dict(d)
    c = list(d['candidates'])
    random.Random(f"{d['item']}:{seed}").shuffle(c)
    e['candidates'] = c
    return e


def user_message(d, facts, max_chars=14000):
    from train_link_classifier import render
    e = dict(d)
    e['candidates'] = [dict(c, ids=' '.join(x for x in (c.get('ids') or '').split() if not x.startswith('openalex'))) for c in d['candidates']]
    t = render(e, facts=facts)
    if len(t) > max_chars:
        t = t[:max_chars] + '\n[dossier cut]'
    return t + '\n\nWho is the printed person? JSON only.'


def parse_verdict(text, keys):
    """model text -> verdict dict, or None. Strict: one JSON object, decision a shown key / not-keyed / cannot-tell;
    duplicate keys restricted to shown keys other than the decision; facts and reason trimmed"""
    if text is None:
        return None
    t = text.strip()
    if '</think>' in t:
        t = t.split('</think>', 1)[1].strip()
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t)
    try:
        v = json.loads(t)
    except (ValueError, TypeError):
        m = re.search(r'\{.*\}', t, re.S)
        if not m:
            return None
        try:
            v = json.loads(m.group(0))
        except ValueError:
            return None
    if not isinstance(v, dict):
        return None
    dec = str(v.get('decision', '')).strip()
    if dec not in set(keys) | {'not-keyed', 'cannot-tell'}:
        return None
    facts = [str(x)[:200] for x in (v.get('facts') or []) if str(x).strip()][:5] if isinstance(v.get('facts'), list) else []
    dups = [x for x in (v.get('duplicate_keys') or []) if isinstance(x, str) and x in keys and x != dec] if isinstance(v.get('duplicate_keys'), list) else []
    conf = v.get('confidence') if v.get('confidence') in ('high', 'medium', 'low') else 'low'
    return dict(decision=dec, reason=' '.join(str(v.get('reason') or '').split())[:400], facts=facts, confidence=conf,
                duplicate_keys=dups if dec.startswith('p-') else [])


def vote(answers, policy):
    """answers: list of decisions (strings). Policies:
       first       the first answer (the greedy pass when it comes first)
       majority    a key needs a strict majority and no vote for another key; otherwise cannot-tell if any key was
                   named; otherwise the majority non-link answer (tie -> cannot-tell)
       unanimous   a key needs every vote; any split involving a key -> cannot-tell; non-link answers as majority"""
    a = [x for x in answers if x and x != 'error']
    if not a:
        return 'error'
    if policy == 'first':
        return a[0]
    c = Counter(a)
    keys = [k for k in c if k.startswith('p-')]
    if len(keys) == 1:
        k = keys[0]
        if (policy == 'unanimous' and c[k] == len(a)) or (policy == 'majority' and c[k] * 2 > len(a)):
            return k
        return 'cannot-tell'
    if len(keys) > 1:
        return 'cannot-tell'
    if c['not-keyed'] > c['cannot-tell']:
        return 'not-keyed'
    return 'cannot-tell'


def outcome(label, dups, dec):
    """cell of (Opus label, Qwen decision): right-link, dangerous (Qwen key where Opus says another key or not-keyed),
    link-on-undecided (Opus cannot-tell / disagree), missed (Qwen abstains where Opus links), agree-nolink, nolink-other"""
    same = {label} | {x for x in str(dups or '').split('|') if x.startswith('p-')}
    if dec.startswith('p-'):
        if label.startswith('p-'):
            return 'right-link' if dec in same else 'dangerous'
        return 'dangerous' if label == 'not-keyed' else 'link-on-undecided'
    if label.startswith('p-'):
        return 'missed'
    return 'agree-nolink' if dec == label else 'nolink-other'


def jeffreys(k, n, q=0.95):
    """two-sided Jeffreys interval (central q)"""
    from scipy.stats import beta
    if n <= 0:
        return (None, None)
    lo = float(beta.ppf((1 - q) / 2, k + .5, n - k + .5)) if k > 0 else 0.0
    hi = float(beta.ppf(1 - (1 - q) / 2, k + .5, n - k + .5)) if k < n else 1.0
    return (round(lo, 4), round(hi, 4))


# ------------------------------------------------------------------------------------------------ local: dossiers

def _sl():
    import score_links as SL
    return SL


def dossiers(args):
    """dossier JSONL for the positions of a CSV (item, pid; optional candidates_shown: '|'-joined keys shown in that
    order, as the Opus judges saw them). Candidates come from the round-two candidate scores (date-surviving, name-block
    keys); the hard rules then remove keys; the top K_SHOW by score are shown"""
    import pandas as pd
    from train_link_classifier import facts_of
    from graph_tables import keylog
    SL = _sl()
    db = SL.duck()
    S = SL.S
    A = pd.read_csv(args.positions, dtype={'candidates_shown': str})
    if 'item' not in A:
        A['item'] = A.pid.astype(str)
    if args.limit:
        A = A.head(args.limit)
    op = gzip.open if args.out.endswith('.gz') else open
    out = op(args.out, 'wt', encoding='utf-8')
    stats = Counter()
    t0 = time.time()
    for c0 in range(0, len(A), args.chunk):
        B = A.iloc[c0:c0 + args.chunk]
        db.register('pp', pd.DataFrame({'pid': B.pid.astype('int64').values}))
        cs = db.execute(f"SELECT c.* EXCLUDE (__index_level_0__) FROM '{S / 'cand-scores2.parquet'}' c JOIN pp USING (pid)").df()
        cs = cs.sort_values(['pid', 'score'], ascending=[True, False])
        csd = {p: g for p, g in cs.groupby('pid')}
        pos = {r['pid']: r for r in db.execute(f"""SELECT x.pid, work, name, title, year, wjournal, kind, role, insts, raw_aff, source, tbl
                FROM read_parquet(['{S / 'positions.parquet'}', '{S / 'positions-extra.parquet'}'], union_by_name=true) x JOIN pp USING (pid)""").df().to_dict('records')}
        want = {}
        for r in B.itertuples():
            shown = [k for k in str(getattr(r, 'candidates_shown', '') or '').split('|') if k.startswith('p-')]
            g = csd.get(r.pid)
            want[r.pid] = shown or (list(g.key) if g is not None else [])
        allk = sorted({k for ks in want.values() for k in ks})
        db.register('kk', pd.DataFrame({'key': allk}))       # SL.dossier / key_dossier read the registered kk
        info = SL.key_dossier(db, allk)
        books = defaultdict(list)
        db.register('kk2', pd.DataFrame({'key': allk}))
        for k, t in db.execute(f"""SELECT a."from", w.label FROM {keylog(SL.GRAPH, 'authored')} a JOIN kk2 ON kk2.key = a."from"
                JOIN '{SL.GRAPH}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'book'""").fetchall():
            books[k].append(t)
        db.register('ww2', pd.DataFrame({'work': sorted({p['work'] for p in pos.values()})}))
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
            cands = []
            for k in want[r.pid]:
                d = info.get(k, {})
                c = lv.get(k, {})
                ws = d.get('works', [])
                step = max(1, len(ws) // 12)
                cands.append(dict(key=k, label=d.get('label') or '', ids=d.get('ids') or '', aff=d.get('aff', [])[:5], rel=d.get('rel', [])[:4],
                                  coauth=d.get('coauth', [])[:6], works_n=len(ws), works=ws[::step][:12], facts=facts_of(c),
                                  score=None if c.get('score') is None else round(float(c['score']), 3)))
            kept, excl = apply_hard_rules(p['name'], p['role'], p['kind'], p['title'], cands, books)
            more = 0
            if len(kept) > K_SHOW:
                more = len(kept) - K_SHOW
                kept = kept[:K_SHOW]
            stats['excluded'] += len(excl)
            stats['all-excluded'] += int(not kept)
            aff = list(p['insts'] if p['insts'] is not None else []) + list(p['raw_aff'] if p['raw_aff'] is not None else [])
            d = dict(item=str(r.item), pid=int(r.pid), work=p['work'], role=p['role'], tbl=p['tbl'], source=p['source'],
                     printed_name=p['name'], title=(p['title'] or ''), kind=p['kind'], year=None if pd.isna(p['year']) else int(p['year']),
                     venue=p['wjournal'] or '', other_names='; '.join(x for x in co[p['work']] if x != p['name'])[:300],
                     printed_aff='; '.join(aff)[:200], candidates=kept, excluded=excl, more=more)
            out.write(json.dumps(d, ensure_ascii=False) + '\n')
            stats['dossiers'] += 1
        print(c0 + len(B), dict(stats), round(time.time() - t0), 's', SL.rss(), 'MB', flush=True)
    out.close()


# ------------------------------------------------------------------------------------------------ local: production sample

WEAK = ('6-25', '26+')


def has_fact(df):
    """a positive context fact on the best pair (the classifier's set-level definition: network, venue, topic mid+,
    cites, affiliation match)"""
    return ((df.network.astype(str) != 'none') | (df.venue.astype(str).isin(['j1-2', 'j3+'])) |
            (df.topic.astype(str).isin(['mid', 'high', 'vhigh'])) | (df.cites.astype(str) == 'cites') |
            (df.aff.astype(str).isin(['same-window', 'same-any'])))


def sample(args):
    """production positions to label (classifier production blocks only: work-people and name-only tables, not exact):
    review band and the single-candidate no-fact class, weighted toward author-role multi-candidate, single no-fact and
    weak name bands; plus rule-linked positions in weak strata (6-25 / 26+ bearers with no positive fact; initials only).
    Excludes the clerical positions. Writes item,pid,stratum,cell,weight (weight = production count / sampled count)"""
    import numpy as np
    import pandas as pd
    SL = _sl()
    db = SL.duck()
    D = db.execute(f"""SELECT pid, role, tbl, rg, n, freq, neg, score, decision, rule_state, rule_key, network, venue, topic, cites, aff, ctx_w
                       FROM '{SL.S / 'prod-decided.parquet'}' WHERE decision IN ('review', 'none', 'link') AND tbl IN ('wp', 'no')""").df()
    cl = set(pd.read_csv(ROOT / 'data/graph/scored-links/clerical-labels.csv', usecols=['pid']).pid.astype('int64'))
    D = D[~D.pid.isin(cl)].copy()
    single = (D.n == 1) & (D.neg.astype(str) == 'none')
    fact = has_fact(D)
    D['band'] = np.where(single, 'single-' + D.freq.astype(str), 'multi')
    D['nofact'] = single & ~fact
    cell = np.full(len(D), '', dtype=object)
    rv = D.decision == 'review'
    # review band by role group and band
    cell = np.where(rv, 'review|' + D.rg.astype(str) + '|' + D.band, cell)
    # single-candidate no-fact class outside the review band (rule possible, scorer none)
    sc = (D.rule_state == 'possible') & D.nofact & ~rv & (D.decision != 'link')
    cell = np.where(sc, 'single-nofact|' + D.rg.astype(str) + '|' + D.band, cell)
    # rule links in weak strata
    wk = (D.rule_state == 'linked') & single & (((D.freq.astype(str).isin(WEAK)) & ~fact) | (D.freq.astype(str) == 'initials'))
    cell = np.where(wk, 'rule-weak|' + D.rg.astype(str) + '|' + np.where(D.freq.astype(str) == 'initials', 'initials', D.freq.astype(str) + '-nofact'), cell)
    D['cell'] = cell
    D = D[D.cell != '']
    # allocation: relative weights per cell family, then proportional to sqrt(production count) inside a family
    fam_total = {'review': args.n * 0.62, 'single-nofact': args.n * 0.38}
    up = {'author|multi': 3.0, 'author|single-6-25': 2.0, 'author|single-26+': 2.0, 'author|single-initials': 2.0,
          'jstor-author|multi': 1.5, 'reviewer|multi': 1.0}
    rnd = np.random.default_rng(20261112 + 3)
    picks = []
    alloc = {}
    for fam, tot in fam_total.items():
        cells = D[D.cell.str.startswith(fam + '|')].groupby('cell').size()
        w = pd.Series({c: np.sqrt(n) * (up.get('|'.join(c.split('|')[1:]), 1.0) if fam == 'review' else (2.0 if c.split('|')[2] in ('single-6-25', 'single-26+', 'single-initials') else 1.0))
                       for c, n in cells.items()})
        a = (w / w.sum() * tot).round().astype(int).clip(upper=cells)
        alloc.update(a.to_dict())
    rw = D[D.cell.str.startswith('rule-weak|')].groupby('cell').size()
    a = (np.sqrt(rw) / np.sqrt(rw).sum() * args.n_rule).round().astype(int).clip(upper=rw)
    alloc.update(a.to_dict())
    for c, k in alloc.items():
        idx = D.index[D.cell == c].values
        picks.append(D.loc[rnd.choice(idx, size=int(k), replace=False)].assign(weight=len(idx) / max(1, k)))
    P = pd.concat(picks)
    P = P.sample(frac=1, random_state=11).reset_index(drop=True)
    P['item'] = 'Q' + P.pid.astype(str)
    P[['item', 'pid', 'cell', 'band', 'rg', 'role', 'tbl', 'n', 'freq', 'decision', 'rule_state', 'rule_key', 'nofact', 'weight']].to_csv(args.out, index=False)
    print(len(P), json.dumps({k: int(v) for k, v in sorted(alloc.items())}, indent=0))


# ------------------------------------------------------------------------------------------------ Nibi: run

def run(args):
    """offline vLLM over dossier JSONL. Requests per dossier: the greedy pass (seed 0: scored order, temperature 0) when
    --greedy, and --samples sampled passes (seeds 1..k: candidate order shuffled, --temperature). Positions with no
    candidate left after the hard rules are not-keyed by rule. Output JSONL rows: item, pid, pass, decision, reason,
    facts, confidence, duplicate_keys, raw (when unparsed), model, prompt; resumable (answered (item, pass) skipped)"""
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    out = Path(args.out)
    done = set()
    if out.exists():
        for line in open(out):
            try:
                v = json.loads(line)
                done.add((v['item'], v['pass']))
            except ValueError:
                pass
    op = gzip.open if args.dossiers.endswith('.gz') else open
    D = [json.loads(line) for line in op(args.dossiers, 'rt', encoding='utf-8')]
    if args.only:
        only = set(open(args.only).read().split())
        D = [d for d in D if d['item'] in only]
    passes = ([0] if args.greedy else []) + list(range(1, args.samples + 1))
    todo, rule_rows = [], []
    for d in D:
        for p in passes:
            if (d['item'], p) in done:
                continue
            if not d['candidates']:
                if p == passes[0]:
                    rule_rows.append(dict(item=d['item'], pid=d['pid'], **{'pass': p}, decision='not-keyed', rule=True, confidence='high',
                                          reason='every name-compatible key was excluded by a hard rule', duplicate_keys=[],
                                          facts=[x['reason'] for x in d.get('excluded', [])][:5]))
                continue
            if p > 0 and len(d['candidates']) < 2 and args.temperature == 0:
                continue
            todo.append((d, p))
    print('dossiers', len(D), 'todo', len(todo), 'done', len(done), 'rule', len(rule_rows), flush=True)
    meta = dict(model=args.model_name, prompt=PROMPT_VERSION + ('+facts' if args.facts else ''))
    with open(out, 'a') as f:
        for r in rule_rows:
            f.write(json.dumps(dict(r, **meta), ensure_ascii=False) + '\n')
    if not todo:
        return
    llm = LLM(model=args.model, max_model_len=args.max_model_len, gpu_memory_utilization=0.90, max_num_seqs=args.max_num_seqs,
              limit_mm_per_prompt={'image': 0, 'video': 0}, enable_prefix_caching=args.prefix_caching)
    system = SYSTEM + (FACTS_NOTE if args.facts else '')
    kw = {'chat_template_kwargs': {'enable_thinking': False}}
    t0 = time.time()
    n = 0
    for c0 in range(0, len(todo), args.chunk):
        ch = todo[c0:c0 + args.chunk]
        msgs, sps, keysets = [], [], []
        for d, p in ch:
            e = permute(d, p)
            keys = [c['key'] for c in e['candidates']]
            keysets.append(keys)
            msgs.append([{'role': 'system', 'content': system}, {'role': 'user', 'content': user_message(e, args.facts)}])
            so = StructuredOutputsParams(json=schema_for(keys)) if not args.no_guided else None
            sps.append(SamplingParams(temperature=0.0 if p == 0 else args.temperature, top_p=1.0 if p == 0 else 0.95,
                                      max_tokens=args.max_tokens, seed=None if p == 0 else hash((d['item'], p)) % (2 ** 31),
                                      structured_outputs=so))
        outs = llm.chat(msgs, sps, use_tqdm=False, **kw)
        with open(out, 'a') as f:
            for (d, p), o, keys in zip(ch, outs, keysets):
                txt = o.outputs[0].text
                v = parse_verdict(txt, keys)
                row = dict(item=d['item'], pid=d['pid'], **{'pass': p}, **meta, ntok=len(o.prompt_token_ids or []))
                row.update(v if v else dict(decision='error', raw=txt[:600]))
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        n += len(ch)
        el = time.time() - t0
        print(f'{n} / {len(todo)}  {el:.0f}s  {n / el:.2f}/s', flush=True)
    print('finished', n, round(time.time() - t0), 's', flush=True)


# ------------------------------------------------------------------------------------------------ local: evaluation

def load_verdicts(paths):
    """{item: {pass: verdict}} from one or more verdict JSONL files (later rows win)"""
    V = defaultdict(dict)
    for fn in paths:
        op = gzip.open if str(fn).endswith('.gz') else open
        with op(fn, 'rt') as f:
            for line in f:
                v = json.loads(line)
                V[v['item']][v['pass']] = v
    return V


def decide(ps, policy):
    """combine passes of one item: 'greedy' (pass 0), 'sc-majority' / 'sc-unanimous' (sampled passes 1..k),
    'greedy+sc' (the greedy link stands only when a strict majority of samples agrees; otherwise cannot-tell;
    greedy non-links stand)"""
    rule = next((v for v in ps.values() if v.get('rule')), None)
    if rule:
        return 'not-keyed', '1/1'
    g = ps.get(0, {}).get('decision')
    smp = [ps[p]['decision'] for p in sorted(ps) if p > 0]
    if policy == 'greedy':
        return (g or 'error'), '1/1'
    if policy.startswith('sc-'):
        if not smp:                     # single-candidate items at temperature 0 have no samples: the greedy answer
            return (g or 'error'), '1/1'
        dec = vote(smp, policy[3:])
        return dec, f"{sum(1 for x in smp if x == dec)}/{len(smp)}"
    if policy == 'greedy+sc':
        if not smp or not (g or '').startswith('p-'):
            return (g or 'error'), '1/1'
        k = sum(1 for x in smp if x == g)
        return (g if k * 2 > len(smp) else 'cannot-tell'), f'{k}/{len(smp)}'
    raise ValueError(policy)


def clerical_frame():
    import pandas as pd
    SL = _sl()
    db = SL.duck()
    L = pd.read_csv(ROOT / 'data/graph/scored-links/clerical-labels.csv', dtype=str)
    meta = db.execute(f"""SELECT pid, role AS prole, tbl, rg, n, freq, neg, score, decision, rule_state, rule_key
                          FROM '{SL.S / 'prod-decided.parquet'}' WHERE pid IN ({','.join(L.pid)})""").df()
    meta['pid'] = meta.pid.astype(str)
    L = L.merge(meta, on='pid', how='left')
    single = (L.n == 1) & (L.neg.astype(str) == 'none')
    L['multi'] = ['single' if s else 'multi' for s in single]
    L['nband'] = [f if s else 'multi' for f, s in zip(L.freq.astype(str), single)]
    L['rr'] = L.role
    return L


def evaluate(args):
    import pandas as pd
    L = clerical_frame()
    if args.split != 'all':
        L = L[L.split == args.split]
    V = load_verdicts(args.verdicts.split(','))
    D = {}
    if args.dossiers:
        op = gzip.open if args.dossiers.endswith('.gz') else open
        for line in op(args.dossiers, 'rt'):
            d = json.loads(line)
            D[d['item']] = d
    L = L[L['item'].isin(V)].copy()
    res = dict(n=len(L), split=args.split, verdicts=args.verdicts)
    # the hard rules removed the key Opus chose?
    if D:
        L['label_excluded'] = [lab in {x['key'] for x in D[i].get('excluded', [])} if i in D else False for i, lab in zip(L['item'], L.label)]
        res['opus_key_removed_by_hard_rule'] = L[L.label_excluded][['item', 'label', 'printed_name']].to_dict('records')

    def block(g):
        links = int(g.dec.str.startswith('p-').sum())
        dang = int((g.out == 'dangerous').sum())
        undec = int((g.out == 'link-on-undecided').sum())
        lk = int(g.label.str.startswith('p-').sum())
        missed = int((g.out == 'missed').sum())
        decided = g[~g.label.isin(['cannot-tell', 'disagree'])]
        return dict(n=int(len(g)), agree=round(float(g.agree.mean()), 3) if len(g) else None,
                    agree_decided=round(float(decided.agree.mean()), 3) if len(decided) else None,
                    links=links, dangerous=dang, dangerous_rate=round(dang / links, 4) if links else None, dangerous_ci95=jeffreys(dang, links),
                    links_on_opus_undecided=undec, opus_links=lk, missed=missed, abstain_rate=round(missed / lk, 4) if lk else None,
                    recall=round(1 - missed / lk, 3) if lk else None, errors=int((g.dec == 'error').sum()))
    for pol in args.policies.split(','):
        g = L.copy()
        dv = [decide(V[i], pol) for i in g['item']]
        g['dec'] = [x[0] for x in dv]
        g['votes'] = [x[1] for x in dv]
        g['out'] = [outcome(a, b, c) for a, b, c in zip(g.label, g.duplicate_keys.fillna(''), g.dec)]
        g['agree'] = [(c in ({a} | {x for x in str(b).split('|') if x})) for a, b, c in zip(g.label, g.duplicate_keys.fillna(''), g.dec)]
        r = dict(overall=block(g))
        for col in ('set', 'multi', 'nband', 'rr'):
            r['by_' + col] = {str(k): block(x) for k, x in g.groupby(col)}
        r['confusion'] = pd.crosstab(g.label.map(lambda x: 'key' if x.startswith('p-') else x),
                                     g.out).to_dict()
        r['dangerous_items'] = g[g.out == 'dangerous'][['item', 'printed_name', 'label', 'dec', 'votes']].to_dict('records')
        res[pol] = r
        if args.out_rows:
            g.assign(policy=pol).to_csv(f"{args.out_rows}.{pol}.csv", index=False)
    s = {p: res[p]['overall'] for p in args.policies.split(',')}
    print(json.dumps(s, indent=1))
    if args.out:
        json.dump(res, open(args.out, 'w'), indent=1, default=str)


# ------------------------------------------------------------------------------------------------ local: write

def write(args):
    """production verdicts -> qwen-labels.csv.gz: position, work, role, printed name, candidates shown, decision, reason,
    facts, model, prompt version, votes (policy), the sample cell and weight"""
    import pandas as pd
    V = load_verdicts(args.verdicts.split(','))
    P = pd.read_csv(args.sample, dtype={'item': str})
    op = gzip.open if args.dossiers.endswith('.gz') else open
    rows = []
    for line in op(args.dossiers, 'rt'):
        d = json.loads(line)
        ps = V.get(d['item'])
        if not ps:
            continue
        dec, votes = decide(ps, args.policy)
        first = ps.get(0) or ps[min(ps)]
        src = next((v for v in ps.values() if v.get('decision') == dec), first)
        rows.append(dict(item=d['item'], position=d['pid'], work=d['work'], role=d['role'], tbl=d['tbl'], printed_name=d['printed_name'],
                         candidates_shown='|'.join(c['key'] for c in d['candidates']),
                         excluded='|'.join(f"{x['key']}:own-book" for x in d.get('excluded', [])),
                         decision=dec, confidence=src.get('confidence'), duplicate_keys='|'.join(src.get('duplicate_keys') or []),
                         reason=(src.get('reason') or '')[:400], facts=' | '.join(src.get('facts') or [])[:600],
                         model=first.get('model'), prompt_version=first.get('prompt'), policy=args.policy, votes=votes,
                         passes='|'.join(f"{p}:{ps[p].get('decision')}" for p in sorted(ps))))
    W = pd.DataFrame(rows).merge(P[['item', 'cell', 'band', 'rg', 'n', 'freq', 'decision', 'rule_state', 'rule_key', 'nofact', 'weight']]
                                 .rename(columns={'decision': 'scorer_decision'}), on='item', how='left')
    W = W.sort_values('position')
    W.to_csv(args.out, index=False, compression='gzip')
    print(len(W), W.decision.map(lambda x: 'key' if str(x).startswith('p-') else x).value_counts().to_dict())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('dossiers')
    a.add_argument('--positions', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--limit', type=int)
    a.add_argument('--chunk', type=int, default=4000)
    a = sub.add_parser('sample')
    a.add_argument('--out', required=True)
    a.add_argument('--n', type=int, default=38000)
    a.add_argument('--n-rule', type=int, default=2000)
    a = sub.add_parser('run')
    a.add_argument('--dossiers', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--model', required=True)
    a.add_argument('--model-name', default='Qwen3.8-27B-FP8')
    a.add_argument('--greedy', action='store_true')
    a.add_argument('--samples', type=int, default=0)
    a.add_argument('--temperature', type=float, default=0.7)
    a.add_argument('--facts', action='store_true', help='show the computed linkage facts (the Opus judges did not see them)')
    a.add_argument('--no-guided', action='store_true')
    a.add_argument('--only')
    a.add_argument('--chunk', type=int, default=1500)
    a.add_argument('--max-tokens', type=int, default=450)
    a.add_argument('--max-model-len', type=int, default=8192)
    a.add_argument('--max-num-seqs', type=int, default=256)
    a.add_argument('--prefix-caching', action='store_true')
    a = sub.add_parser('evaluate')
    a.add_argument('--verdicts', required=True)
    a.add_argument('--dossiers')
    a.add_argument('--split', default='clerical-dev')
    a.add_argument('--policies', default='greedy,sc-majority,sc-unanimous,greedy+sc')
    a.add_argument('--out')
    a.add_argument('--out-rows')
    a = sub.add_parser('write')
    a.add_argument('--verdicts', required=True)
    a.add_argument('--dossiers', required=True)
    a.add_argument('--sample', required=True)
    a.add_argument('--policy', default='greedy')
    a.add_argument('--out', default=str(ROOT / 'data/graph/scored-links/qwen-labels.csv.gz'))
    args = ap.parse_args()
    {'dossiers': dossiers, 'sample': sample, 'run': run, 'evaluate': evaluate, 'write': write}[args.cmd](args)


if __name__ == '__main__':
    main()
