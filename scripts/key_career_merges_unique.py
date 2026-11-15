"""Career merges, review tier: ties the class-39 rule did not read (2026-11-14; ARCHITECTURE.md §8, the class row
'thin key held in the career-merge review tier'). Writes a PROPOSAL, never applies.

Probe: Guillaume Teasdale. p-123542 (LC n2012047095, Wikidata, GND, VIAF, ISNI; LC 670 notes cite his books on the
French in North America and his Windsor post) and p-74171 (AHA PhD record, York 2010, "The French of Orchard Country").
key_career_merges.py held the pair in its review tier (`tie-below-strict-bar`): the name is unique (bearers 1), the
group is closed and the dates fit, but the only tie it reads is topic over key-log titles ('french', 3.0 < 6), because
the anchored key holds no key-log work and the rule never reads the LC authority's own notes.

The rerun (key_career_merges.py --keylog-people on the current key log) gives the review tier; for every
`tie-below-strict-bar` row whose seed is an anchored key this script measures further ties between the thin key t and
the anchored key a (and keys already strictly tied to a):
  (a) LC notes of a's `lcnaf:` authorities: an institution named in the note text (after 'at', 'of', in parentheses,
      'Thesis (Ph.D.)--X') that agrees with t's printed institution (thesis institution, AHA department, review-credit
      affiliation); the LC-note titles added to a's topic profile (pass-nine ratio, as in class 39). Topic supports only.
  (b) thesis -> book: t holds a thesis (harvested or AHA) of year T; a holds a book (key-log, or a title in its LC
      notes) dated T..T+15 sharing rare title words (class-40 thresholds: 2+ words of idf >= 6, shared weight >= 16,
      covering half the note title's or the thesis title's weight).
  (c) reviewing: one side holds a History PhD of year T, the other's dated reviews in history venues (journal
      catalogue, H-Net) fall in T-3..T+10.
  (d) a's Wikidata (P69 educated at, P108 employer) or ORCID (education, employment) institutions agree with t's
      institution; read from the harvests on E: (/mnt/e/wikidata-keys-2026-11-14, /mnt/e/orcid-keys-2026-11-14),
      never fetched here.
  (e) unique full name: one bearer (no other date-possible LC authority, OpenAlex History ids <= 1), the only other
      compatible key in the key log is a, both keys history-side, dates fit; nothing else.
Nicknames never count (names_agree is strict); initials-only thin keys never enter; 26+ bearers never promote;
different identifiers, life dates, not-same marks, outside 'different' verdicts and the merge guard block (as in
class 39). Only thin -> anchored merges are proposed; thin-into-thin groups and two-anchored-key rows stay held.

    python3 scripts/key_career_merges_unique.py --graph <graph> [--ctx <pickle of a key_career_merges run>]
"""
import argparse
import csv
import glob
import gzip
import json
import math
import os
import pickle
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
import key_career_merges as K  # noqa: E402
from key_review_credit_merges import agree as inst_agree  # noqa: E402
from key_review_reviewers import journal_key  # noqa: E402
from link_work_people import p9_tokens, p9_terms  # noqa: E402

ROOT = I.ROOT
NOTES = '/mnt/e/lc-authorities/personal-notes.parquet'
ORGS = '/mnt/e/lc-authorities/organisations.parquet'
WD_DIR = Path('/mnt/e/wikidata-keys-2026-11-14')
ORCID_DIR = Path('/mnt/e/orcid-keys-2026-11-14/records')
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.csv'
SCR = K.SCRATCH.parent / 'career-unique'

RARE, MIN_SHARED, COVER = 6.0, 16.0, 0.5          # class 40 thesis-to-book thresholds
BOOK_WINDOW = (0, 15)
REVIEW_WINDOW = (-3, 10)
LC_TOPIC_MIN = 6.0
PROMOTE = 'ABDE'    # hand check 2026-11-14 (sample-checked.csv): A/B/D 58 right, 0 wrong, 2 unclear of 60; E 57/0/3 of 60

INST_PAT = re.compile(
    r"((?:[A-Z][\w.'’&-]*\s+){0,5}(?:University|Univ\.|College|Institute|Polytechnic|Seminary|School)"
    r"(?:\s+(?:of|at|in|for)\s+(?:the\s+)?(?:[A-Z][\w.'’-]*,?\s*){1,5})?"
    r"|(?:Universit[éeyàä]t?|Universidad|Universidade|Università|École|Ecole|Hochschule|Institut)\s+(?:[\w.'’-]+\s*){1,6})")
HIST_WORD = re.compile(r'\bhistor|\bhistoire|\bgeschicht|\bhistoria', re.I)


def hist_venues():
    out = set()
    with open(CATALOGUE, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            for t in [r['title']] + (r['aliases'] or '').split(' | '):
                jk = journal_key(t) if t else ''
                if jk:
                    out.add(jk)
    return out


def note_insts(text):
    out = []
    for m in INST_PAT.finditer(text or ''):
        s = m.group(1).strip(" ,.;:'’")
        s = re.sub(r"'s\b|’s\b", '', s)
        if len(s) > 6:
            out.append(s)
    for m in re.finditer(r'(?:Thesis|Diss\.?|Dissertation)\s*\((?:Ph\.?\s?D\.?|D\.?\s?Phil\.?|doctoral)\)\s*-+\s*([^,;()]+)', text or '', re.I):
        out.append(m.group(1).strip())
    return out


def load_ctx(args):
    if args.ctx and Path(args.ctx).exists():
        return pickle.load(open(args.ctx, 'rb'))
    ctx = K.main(['--graph', str(args.graph), '--keylog-people', '--no-validate', '--out', str(SCR / 'kcm-out')])
    keep = {k: ctx[k] for k in ('rows', 'thin', 'merges', 'docs_of', 'blocked', 'notsame', 'R')}
    keep['facts'] = ctx['facts']
    keep['need'] = list(ctx['facts'])
    keep['people'] = {k: ctx['people'][k] for k in ctx['facts']}
    keep['nforms'] = {k: ctx['nforms'][k] for k in ctx['facts']}
    keep['TPdf'], keep['TPN'] = dict(ctx['TP'].df), ctx['TP'].N
    if args.ctx:
        pickle.dump(keep, open(args.ctx, 'wb'))
    return keep


class Scorer(K.Topic):
    def __init__(self, df, n):        # noqa: the background is the class-39 run's
        self.df, self.N = df, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--graph', type=Path, default=ROOT / 'build/graph')
    ap.add_argument('--ctx', default=None, help='pickle of the class-39 rerun (written if missing)')
    ap.add_argument('--out', type=Path, default=ROOT / 'data/identifiers/career-merges-unique-2026-11-14')
    ap.add_argument('--validate', action='store_true', help='dry-run the proposals on the key-log cache')
    ap.add_argument('--seed', type=int, default=20261114)
    args = ap.parse_args()
    SCR.mkdir(parents=True, exist_ok=True)
    C = load_ctx(args)
    rows, people, facts, thin, docs_of = C['rows'], C['people'], C['facts'], C['thin'], C['docs_of']
    R = Counter()
    rowmap = {r['thin']: r for r in rows}
    review = [r for r in rows if r.get('tier') == 'review']
    R['review_tier'] = len(review)
    R['review_by_why'] = Counter(r.get('why') for r in review)
    R['rerun_strict_old_rule'] = len(C['merges'])
    TP = Scorer(C['TPdf'], C['TPN'])
    hv = hist_venues()

    def is_hist_venue(v):
        return bool(v) and (v in hv or v.startswith('h-'))

    # rows judged here: below the strict bar, seed an anchored key
    cand = [r for r in review if r.get('why') == 'tie-below-strict-bar']
    R['tie_below_bar'] = len(cand)
    R['tie_below_bar_into_anchored'] = sum(1 for r in cand if r.get('seed') and not thin.get(r['seed']))
    cand = [r for r in cand if r.get('seed') and not thin.get(r['seed'])]
    # members already strictly tied to the same seed
    strict_of = defaultdict(set)
    for t, s in C['merges'].items():
        strict_of[s].add(t)

    seeds = {r['seed'] for r in cand}
    lc_of = {s: [a.split(':', 1)[1] for a in people[s]['anchors'] if a.startswith('lcnaf:')] for s in seeds}
    wd_of = {s: [a.split(':', 1)[1] for a in people[s]['anchors'] if a.startswith('wd:')] for s in seeds}
    orcid_of = {s: [a.split(':', 1)[1] for a in people[s]['anchors'] if a.startswith('orcid:')] for s in seeds}

    # ---- LC notes of the seeds' authorities
    db = duckdb.connect()
    want = sorted({x for v in lc_of.values() for x in v})
    db.execute('CREATE TEMP TABLE w(lcid VARCHAR)')
    db.executemany('INSERT INTO w VALUES (?)', [(x,) for x in want])
    orgs = dict(db.execute(f"SELECT id, label FROM '{ORGS}'").fetchall())
    notes = {}
    for lcid, ns, affs, fields in db.execute(f"SELECT n.lcid, n.notes, n.affiliations, n.fields FROM '{NOTES}' n JOIN w USING (lcid)").fetchall():
        notes[lcid] = (ns or [], [orgs.get(a['org'], '') for a in (affs or []) if a and a.get('org')], fields or [])
    R['seed_lc_authorities'] = len(want)
    R['seed_lc_authorities_with_notes'] = len(notes)
    from key_lc_authority_notes import parse_source, toks, STOPW  # noqa: E402
    from link_cited_work_authors import fam_norm  # noqa: E402

    # ---- idf for thesis-to-book (class 40 tokens), over graph work titles, cached
    idf_p = SCR / 'idf.pkl'
    if idf_p.exists():
        idf, idf_top = pickle.load(open(idf_p, 'rb'))
    else:
        df, n = Counter(), 0
        cur = db.execute(f"SELECT label FROM '{args.graph}/work.parquet' WHERE label IS NOT NULL")
        while True:
            rs = cur.fetchmany(200000)
            if not rs:
                break
            for (t,) in rs:
                n += 1
                df.update(toks(t))
        idf = {w: math.log(n / (1 + d)) for w, d in df.items()}
        idf_top = math.log(n)
        pickle.dump((idf, idf_top), open(idf_p, 'wb'))

    def overlap(a, b):
        ta, tb = toks(a), toks(b)
        w = lambda x: idf.get(x, idf_top)
        sh = ta & tb
        s = sum(w(x) for x in sh)
        wa, wb = sum(w(x) for x in ta) or 1, sum(w(x) for x in tb) or 1
        rare = [x for x in sh if w(x) >= RARE]
        return dict(shared=' '.join(sorted(sh, key=lambda x: -w(x))), w=round(s, 1), n_rare=len(rare),
                    cover=round(max(s / wa, s / wb), 2))

    # ---- Wikidata P69/P108 and ORCID education/employment of the seeds (harvests on E:, read only)
    wd_want = {q for v in wd_of.values() for q in v}
    wd_insts = defaultdict(list)
    items = json.load(open(WD_DIR / 'items.json', encoding='utf-8')) if (WD_DIR / 'items.json').exists() else {}
    for f in sorted(glob.glob(str(WD_DIR / 'batches/*.json.gz'))):
        try:
            d = json.load(gzip.open(f, 'rt', encoding='utf-8'))
        except (OSError, EOFError, json.JSONDecodeError):
            continue
        for s in d.get('stmt', []):
            q = s['q']['value'].rsplit('/', 1)[1]
            if q in wd_want and s['prop']['value'] in ('P69', 'P108'):
                v = s['v']['value'].rsplit('/', 1)[1]
                lab = (items.get(v) or {}).get('label') or ''
                if lab:
                    wd_insts[q].append((s['prop']['value'], lab))
    R['seed_wd_ids'] = len(wd_want)
    R['seed_wd_ids_with_edu_or_employer'] = len(wd_insts)
    orc_want = {o for v in orcid_of.values() for o in v}
    orc_insts = defaultdict(list)
    if ORCID_DIR.exists():
        for f in ORCID_DIR.glob('*/*.json.gz'):
            o = f.name[:-8]
            if o not in orc_want:
                continue
            try:
                d = json.load(gzip.open(f, 'rt', encoding='utf-8'))
            except (OSError, EOFError, json.JSONDecodeError):
                continue
            a = d.get('activities-summary') or {}
            for kind in ('educations', 'employments', 'qualifications'):
                for g in ((a.get(kind) or {}).get('affiliation-group') or []):
                    for sm in g.get('summaries') or []:
                        x = next(iter(sm.values()))
                        nm = ((x.get('organization') or {}).get('name')) or ''
                        if nm:
                            orc_insts[o].append((kind, nm))
    R['seed_orcids'] = len(orc_want)
    R['seed_orcids_with_affiliations'] = len(orc_insts)

    inst_cache = {}
    need_aha = {a.split(':', 1)[1] for r in cand for a in people[r['thin']]['anchors'] if a.startswith('aha-phd:')}
    aha = {}
    for line in open(K.AHA, encoding='utf-8'):
        x = json.loads(line)
        if x['id'] in need_aha and x.get('title') and not x['title'].startswith('[No title'):
            aha[x['id']] = (x['title'], x.get('year'))

    def agree(a, b):
        k = (a, b)
        if k not in inst_cache:
            try:
                inst_cache[k] = bool(a and b and inst_agree(a, b))
            except Exception:
                inst_cache[k] = False
        return inst_cache[k]

    out_rows = []
    for r in cand:
        t, s = r['thin'], r['seed']
        S = [s] + sorted(strict_of.get(s, ()))
        ft = facts[t]
        fS = [facts[k] for k in S if k in facts]
        t_insts = sorted({lab for _, lab, _, _ in ft['insts'] if lab})
        # thin side: titles of theses, PhD year, history side
        t_thesis = [(lab, y) for w, (lab, y, kind, v) in ft['works'].items() if kind == 'thesis']
        T = min(ft['phd']) if ft['phd'] else None
        t_thesis += [aha[a.split(':', 1)[1]] for a in people[t]['anchors']
                     if a.startswith('aha-phd:') and a.split(':', 1)[1] in aha]
        t_reviews = [(y, v) for w, (lab, y, kind, v) in ft['works'].items() if kind == 'review' or lab.lower().startswith('review')]
        t_hist = r['thin_type'] in ('aha', 'thesis') or any(is_hist_venue(v) for (_, _, _, v) in ft['works'].values())
        # anchored side
        s_works = [x for f in fS for x in f['works'].values()]
        s_books = [(lab, y, 'keylog') for (lab, y, kind, v) in s_works if kind == 'book' and y]
        s_notes_txt = []
        s_note_titles = []
        s_note_insts = []
        s_fields = []
        fam = fam_norm(people[s]['label'].split(',')[0]) if ',' in people[s]['label'] else ''
        for lcid in lc_of.get(s, []):
            ns, orgl, fields = notes.get(lcid, ([], [], []))
            s_fields += fields
            for n_ in ns:
                s_notes_txt.append(n_)
                src = n_.split(':: ', 1)[0] if ':: ' in n_ else n_
                p = parse_source(src, fam)
                if p and p[0] != 'other-author':
                    s_note_titles.append((p[1], p[2]))
                    s_books.append((p[1], p[2], 'lc-note'))
                s_note_insts += note_insts(n_)
        S_phd = sorted({y for f in fS for y in f['phd']})
        s_reviews = [(y, v) for (lab, y, kind, v) in s_works if kind == 'review' or lab.lower().startswith('review')]
        s_hist = (any(is_hist_venue(v) for (_, _, _, v) in s_works) or bool(S_phd)
                  or any(HIST_WORD.search(x) for x in s_notes_txt + s_fields)
                  or any(HIST_WORD.search(lab) for f in fS for _, lab, _, _ in f['insts']))
        # (a) LC note institution / topic
        a_inst = ''
        for ti in t_insts:
            for ni in s_note_insts:
                if agree(ti, ni):
                    a_inst = f'{ti} ~ {ni}'
                    break
            if a_inst:
                break
        base = K.Topic.score(TP, docs_of[t], [d for k in S for d in docs_of.get(k, [])])
        note_docs = []
        for ttl, _ in s_note_titles:
            tk = tuple(x for x in p9_tokens(ttl) if x not in K.EXTRA_STOP)
            if tk:
                note_docs.append(p9_terms(tk))
        withn = K.Topic.score(TP, docs_of[t], [d for k in S for d in docs_of.get(k, [])] + note_docs)
        a_topic = round(withn[0] + withn[1], 2)
        # (b) thesis -> book
        b_best = None
        for ttl, ty in t_thesis:
            ty = ty or T
            if not ty:
                continue
            for btl, by, src in s_books:
                if by is None or not (BOOK_WINDOW[0] <= by - ty <= BOOK_WINDOW[1]):
                    continue
                o = overlap(ttl, btl)
                if o['n_rare'] >= 2 and o['w'] >= MIN_SHARED and o['cover'] >= COVER:
                    if not b_best or o['w'] > b_best['w']:
                        b_best = dict(o, book=btl[:90], year=by, src=src, thesis_year=ty)
        # (c) reviewing in history venues near a History PhD on the other side
        c_tie = ''
        if T and r['thin_type'] in ('aha', 'thesis'):
            ys = [y for y, v in s_reviews if y and is_hist_venue(v) and REVIEW_WINDOW[0] <= y - T <= REVIEW_WINDOW[1]]
            if ys:
                c_tie = f'anchored reviews {min(ys)}-{max(ys)} in history venues, PhD {T}'
        elif S_phd and r['thin_type'] == 'review':
            T2 = S_phd[0]
            ys = [y for y, v in t_reviews if y and is_hist_venue(v) and REVIEW_WINDOW[0] <= y - T2 <= REVIEW_WINDOW[1]]
            if ys:
                c_tie = f'thin reviews {min(ys)}-{max(ys)} in history venues, PhD {T2}'
        # (d) Wikidata / ORCID institutions
        d_inst = ''
        ext = [(f'wd:{p}', lab) for q in wd_of.get(s, []) for p, lab in wd_insts.get(q, [])]
        ext += [(f'orcid:{k}', nm) for o in orcid_of.get(s, []) for k, nm in orc_insts.get(o, [])]
        for ti in t_insts:
            for src, lab in ext:
                if agree(ti, lab):
                    d_inst = f'{ti} ~ {lab} ({src})'
                    break
            if d_inst:
                break
        unique = (str(r['bearers']) == '1' and int(r['lc_others']) == 0 and int(r['oa_n']) <= 1
                  and int(r['compatible']) == 1 and int(r['n_group']) == 2)
        o = dict(r)
        o.update(seed_label=people[s]['label'], seed_anchors=' '.join(sorted(people[s]['anchors'])[:6]),
                 t_insts=' | '.join(t_insts)[:200], t_phd=T or '', t_hist=t_hist, s_hist=s_hist,
                 s_lc=' '.join(lc_of.get(s, [])), s_has_notes=bool(s_notes_txt), s_works=len(s_works),
                 a_inst=a_inst[:160], a_topic=a_topic, a_topic_base=round(base[0] + base[1], 2),
                 a_topic_terms=' '.join(x for _, x in withn[2][:5]),
                 b_book=(f"{b_best['book']} ({b_best['year']}, {b_best['src']}; shared {b_best['shared']}; "
                         f"w {b_best['w']}, cover {b_best['cover']})" if b_best else ''),
                 c_review=c_tie, d_inst=d_inst[:160], unique=unique,
                 guard=(t in C['blocked'] or s in C['blocked']),
                 notes_excerpt=' || '.join(s_notes_txt)[:400],
                 t_titles=' | '.join(lab for (lab, _, _, _) in ft['works'].values())[:300],
                 s_titles=' | '.join(lab for (lab, _, _, _) in s_works)[:300])
        out_rows.append(o)
    R['judged'] = len(out_rows)

    def stratum(o):
        if o['band'] == '26+' or o['career'] != 'fits' or o['guard']:
            return 'held:26+/career/guard'
        if o['b_book']:
            return 'B-thesis-book'
        if o['a_inst']:
            return 'A-lc-note-institution'
        if o['d_inst']:
            return 'D-wd-orcid-institution'
        if o['a_topic'] >= LC_TOPIC_MIN and o['a_topic'] > o['a_topic_base'] and o['band'] in ('unique', '2-5'):
            return 'A-lc-note-topic'
        if o['unique'] and o['t_hist'] and o['s_hist']:
            return 'E-unique-name' + ('+review-window' if o['c_review'] else '')
        if o['c_review']:
            return 'C-review-window-only'
        return 'held:no-further-tie'
    for o in out_rows:
        o['stratum'] = stratum(o)
    R['strata'] = Counter(o['stratum'] for o in out_rows)
    R['strata_by_type'] = Counter(f"{o['stratum']}|{o['thin_type']}" for o in out_rows)
    pickle.dump(dict(rows=out_rows, R=R), open(SCR / 'unique-rows.pkl', 'wb'))

    # ---- outputs: documentary ties (A, B, D) -> proposal.json; unique name only (E) -> proposal-unique-name.json
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    cols = ['thin', 'thin_type', 'label', 'seed', 'seed_label', 'stratum', 'band', 'bearers', 'lc_others', 'oa_n',
            'compatible', 'n_group', 'career', 't_insts', 't_phd', 't_hist', 's_hist', 's_lc', 'a_inst', 'a_topic',
            'a_topic_base', 'a_topic_terms', 'b_book', 'c_review', 'd_inst', 't_lrs', 't_lrf', 't_top', 't_venue',
            'seed_anchors']
    prom = [o for o in out_rows if o['stratum'][0] in PROMOTE]
    held = [o for o in out_rows if o['stratum'][0] not in PROMOTE]
    for name, rs in (('promoted.csv.gz', prom), ('held.csv.gz', held)):
        with gzip.open(out / name, 'wt', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            for o in sorted(rs, key=lambda o: (o['stratum'], o['label'])):
                w.writerow(o)
    # rows held for other reasons (two anchored keys, merge guard, thin-into-thin) stay in the class-39 review file
    with gzip.open(out / 'review-tier-now.csv.gz', 'wt', newline='', encoding='utf-8') as fh:
        cc = ['thin', 'thin_type', 'label', 'why', 'seed', 'targets', 'n_group', 'band', 'bearers', 'compatible',
              't_institution', 't_venue', 't_network', 't_lrs', 't_lrf', 't_top']
        w = csv.DictWriter(fh, fieldnames=cc, extrasaction='ignore')
        w.writeheader()
        for r in sorted(review, key=lambda r: r['label']):
            w.writerow(r)

    def basis(o):
        ev = []
        if o['b_book']:
            ev.append(f"thesis -> book: {o['b_book']}")
        if o['a_inst']:
            ev.append(f"LC authority note names the thin key's institution: {o['a_inst']}")
        if o['d_inst']:
            ev.append(f"anchored key's Wikidata/ORCID institution: {o['d_inst']}")
        if o['stratum'] == 'A-lc-note-topic':
            ev.append(f"topic under the anchored key's titles and its LC-note book titles {o['a_topic']} "
                      f"({o['a_topic_terms']})")
        if o['stratum'].startswith('E-'):
            ev.append('unique full name (no other date-possible LC authority, OpenAlex History ids <= 1, no other '
                      'compatible key), both keys history-side')
            if o['c_review']:
                ev.append(o['c_review'])
        return (f"one career on two keys ({out.name}, {o['stratum']}): {o['label']} ({o['thin_type']} key) and "
                f"{o['seed_label']}: full names agree, name group closed (bearers {o['bearers']}), dates fit one "
                f"career; " + '; '.join(ev))[:900]

    for fname, rs, what in (('proposal.json', [o for o in prom if not o['stratum'].startswith('E-')],
                             'documentary tie (LC authority note institution or topic, thesis-to-book, Wikidata/ORCID institution)'),
                            ('proposal-unique-name.json', [o for o in prom if o['stratum'].startswith('E-')],
                             'unique full name, both keys history-side, nothing else')):
        ops = [dict(event='merge', key=o['thin'], into=o['seed'], decided_by='rule', basis=basis(o))
               for o in sorted(rs, key=lambda o: int(o['thin'][2:]))]
        prop = dict(basis=f'career merges from the class-39 review tier ({out.name}; ARCHITECTURE.md §8): {what}; '
                          'thin key into the anchored key', decided_by='rule', ops=ops)
        (out / fname).write_text(json.dumps(prop, ensure_ascii=False, indent=0) + '\n')
        R[f'ops_{fname}'] = len(ops)
    if args.validate:
        import keylog_snapshot as KS
        for fname in ('proposal.json', 'proposal-unique-name.json'):
            state = KS.read_state()
            ev, _ = I.materialise(state, json.load(open(out / fname)), 'dry-run', 'dry-run', inplace=True)
            R[f'dry_run_events_{fname}'] = len(ev)
            del state
        st = KS.read_state()
        both = json.load(open(out / 'proposal.json'))
        both['ops'] += json.load(open(out / 'proposal-unique-name.json'))['ops']
        ev, _ = I.materialise(st, both, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events_both'] = len(ev)
    rep = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sorted(R.items())}
    (out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + '\n')
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main()
