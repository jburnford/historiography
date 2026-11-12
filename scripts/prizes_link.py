"""Prize facts -> person keys and graph works (2026-11-12). Reads data/graph/prizes/prizes.csv.gz (scripts/prizes_harvest.py),
a graph build (WP_GRAPH, default build/graph) and the key-log cache read-only; writes tracked tables beside the prize table
and touches no key log, no proposal and no build.

Winner -> person key (data/graph/prizes/winners.csv.gz), one row per prize row:
  exact      an identifier on the row (Wikidata QID, or the LC / ORCID / GND / VIAF / ISNI / IdRef id Wikidata gives the
             winner) is an anchor on exactly one key (`exact-conflict` when two identifiers point to two keys: nothing linked)
  credited   the prize work matched a graph work (by identifier, or title and author, below) and the winner's name agrees
             with a person the graph already credits on it (key-log claim: branch work-credit:keylog; linked credit:
             work-credit:linked). The identity rests on the work, the project's rule (identity by works)
  linked / possible / ambiguous / none
             scripts/link_work_people.py's rule, imported and not changed (scripts/link_cited_work_authors.py underneath):
             candidates by name agreement (`forms`, `name_level` with its refusals), date elimination against the key's
             career window (event year = the work's year, else the prize year; book prizes leave the window open above as
             the linker does for books), rarity of the name in the LC authority file and OpenAlex History authors, and second
             facts (a co-winner credited on the same work is a key-log co-author, the printed institution agrees with a dated
             affiliation, a thesis the key wrote or supervised cites the prize work). Nothing else is added: the prize itself is
             never a fact, field or topic never decides.
  Printed names are cleaned only of civilities ('M.', 'Mme', 'Prof.', 'R.P.') and of capitals used for family names
  ('Jean-Yves MOLLIER' -> 'Jean-Yves Mollier'); organisations are skipped (state `not-a-person`).

Prize work -> graph work (data/graph/prizes/works.csv.gz), one row per prize row with a printed or Wikidata work:
  id         the row's LCCN / ISBN / DOI (Wikidata P1144, P212, P957, P356; or printed) is an anchor of a graph work
  title      key_lc_works.title_key in SQL (the K() of key_cited_works_lc_full: accents, apostrophes and punctuation dropped,
             '&' read 'and', leading articles dropped, first ten words), on the main title (before ':', or before ';' / '='
             as pre-ISBD LC records print subtitles: 'Roll, Jordan, roll; the world the slaves made', or a '. ' that CHA
             uses as a subtitle mark) and on the whole title, against graph work labels cut at ' / '. A candidate needs
             the winner's family name on the work: a credited person (any evidence) whose family agrees, or the family in the
             label's statement of responsibility or printed editors. One-word main titles ('Dammed') need the whole title to
             agree, or the subtitle's first three words. Several passing works: the established > recorded > unkeyed node
             of the kind the prize names, closest year not after the prize year; the rest listed.
  possible   whole title of four words or more agrees, the work carries no author at all, year within five years before
             the prize: listed, not matched.
Prize works with no graph node -> LC (data/graph/prizes/lc.csv.gz): the LC 2016 bibliographic index (/mnt/e/lc-bib-2016,
read-only; lc_bib_index.py) and the LC SRU book records harvested for H-Net books (/mnt/e/lc-authorities/books.ndjson): main
title key equal and the winner's family name a heading (100/700) or in the statement of responsibility. Kept: LCCN, title,
date, main-entry heading and its authority (`lcnaf:` id when the heading carries an id.loc.gov URI) and the person key that
holds that authority (an exact author link for the loader).

Corpus uptake of prize works without a node: the dissertation corpus's local works table (works.csv: untracked build
artefact, metadata only) by title key and family name; counted, not exported.

    WP_GRAPH=<graph dir> python3 scripts/prizes_link.py link
    WP_GRAPH=<graph dir> python3 scripts/prizes_link.py dammed-class      # the defect class behind Dammed
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
OUT = ROOT / 'data/graph/prizes'
GRAPH = Path(os.environ.get('WP_GRAPH', ROOT / 'build/graph'))
SCR = Path(os.environ.get('PRIZE_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                                           'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/prizes'))
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LC_INDEX = '/mnt/e/lc-bib-2016/index'
LC_BOOKS = '/mnt/e/lc-authorities/books.ndjson'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
CIVIL = re.compile(r"^(?:(?:M|Mme|Mlle|MM|Mmes|Mgr|Me|Dr|Drs|Prof|Pr|Sir|Dame|Rev|R\.\s?P|P|Fr|Sr|Sra|Dra|Lic|Mtro|Mtra|"
                   r"Herr|Frau|Hon|Lord|Lady)\.?\s+)+")
ORG = re.compile(r'(?i)\b(society|soci[ée]t[ée]|association|committee|comit[ée]|museum|mus[ée]e|first nation|council|'
                 r'press|institut|institute|university|universit|college|school|class|club|archives|library|foundation|'
                 r'fondation|project|team|group|staff|students|band|nation\b|inc\.|ltd|revue|journal|editorial|board|'
                 r'department|ministry|government|city of|town of|village|church|parish|federation|network|centre|center)')


def duck():
    import duckdb
    tmp = SCR / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{tmp}'; SET enable_progress_bar=false")
    return db


def clean_name(n):
    n = re.sub(r'\s+', ' ', (n or '').replace('‑', '-')).strip(' ,;.')
    n = CIVIL.sub('', n)
    n = re.sub(r'\s*\((?:eds?|dir|org|coord)\.?\)\s*$', '', n, flags=re.I)
    # run-together initials ('WL Warren', 'EP Thompson') -> 'W. L. Warren'
    n = re.sub(r'^([A-Z]{2,3})(?=\s+[A-Z][a-z])', lambda m: ' '.join(c + '.' for c in m.group(1)), n)
    # capitals as family names ('Jean-Yves MOLLIER', 'BESSIÈRE Gérard')
    ws = n.split()
    if len(ws) >= 2 and any(len(w) > 2 and w.isupper() for w in ws) and not all(w.isupper() for w in ws):
        n = ' '.join(w.title() if len(w) > 1 and w.isupper() else w for w in ws)
    elif ws and all(w.isupper() for w in ws if len(w) > 2):
        n = ' '.join(w.title() if len(w) > 1 else w for w in ws)
    return n


def read_prizes():
    with gzip.open(OUT / 'prizes.csv.gz', 'rt', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def ids_of(s, scheme):
    return [x.split(':', 1)[1] for x in (s or '').split() if x.startswith(scheme + ':')]


def year_of(r):
    y = r.get('year') or ''
    return int(y) if y.isdigit() else None


# ---------------------------------------------------------------- works

def K(x):
    from key_cited_works_lc_full import K as _K
    return _K(x)


def match_works(db, rows, L):
    """-> {row id: dict(state, work, basis, candidates, kind, year)}"""
    import pyarrow as pa
    G = GRAPH
    pr = [r for r in rows if r['work_title'] or r['work_ids']]
    cols = defaultdict(list)
    for r in pr:
        t = re.sub(r'\s+', ' ', r['work_title']).strip(' “”"«»‘’')
        m2 = t.split('. ', 1)[0] if '. ' in t and ':' not in t and len(t.split('. ', 1)[0].split()) >= 2 else ''
        for k, v in (('id', r['id']), ('title', t), ('alt', m2), ('fam', fam_of(r['winner_clean'], L)),
                     ('year', year_of(r) or 0), ('honours', r['honours'])):
            cols[k].append(v)
    db.register('pa_pr', pa.table(dict(cols)))
    db.execute(f"""CREATE OR REPLACE TABLE pr AS SELECT *, {K("regexp_extract(split_part(title, ':', 1), '^[^;=]*')")} mt, {K('title')} wt,
                   CASE WHEN alt <> '' THEN {K('alt')} END altk FROM pa_pr""")
    db.execute("CREATE OR REPLACE TABLE want AS SELECT mt k FROM pr WHERE mt <> '' UNION SELECT wt FROM pr WHERE wt <> '' "
               "UNION SELECT altk FROM pr WHERE altk IS NOT NULL AND altk <> ''")
    lab = "split_part(label, ' / ', 1)"
    db.execute(f"""CREATE OR REPLACE TABLE gw AS SELECT * FROM (
                   SELECT key, label, kind, year, resolution, {K(f"regexp_extract(split_part({lab}, ':', 1), '^[^;=]*')")} mt, {K(lab)} wt
                   FROM '{G}/work.parquet'
                   WHERE label IS NOT NULL) WHERE mt IN (SELECT k FROM want) OR wt IN (SELECT k FROM want)""")
    cand = db.execute("""SELECT pr.id, gw.key, gw.label, gw.kind, gw.year, gw.resolution,
              CASE WHEN pr.wt = gw.wt THEN 'whole' WHEN pr.mt = gw.mt THEN 'main' WHEN pr.mt = gw.wt THEN 'main-whole'
                   WHEN pr.wt = gw.mt THEN 'whole-main' ELSE 'alt' END basis, pr.mt, pr.wt
              FROM pr JOIN gw ON gw.mt = pr.mt OR gw.wt = pr.wt OR gw.wt = pr.mt OR gw.mt = pr.wt
                   OR (pr.altk IS NOT NULL AND (gw.mt = pr.altk OR gw.wt = pr.altk))""").fetchall()
    keys = sorted({c[1] for c in cand})
    db.register('ck', pa.table({'key': keys}))
    credits = defaultdict(list)
    for k, p, ev, lab_ in db.execute(f"""SELECT a."to", a."from", a.evidence, p.label FROM (
            SELECT "from", "to", evidence FROM '{G}/authored.parquet' UNION ALL SELECT "from", "to", evidence FROM '{G}/edited.parquet') a
            JOIN ck ON ck.key = a."to" JOIN '{G}/person.parquet' p ON p.key = a."from" """).fetchall():
        credits[k].append((p, ev, lab_))
    extra = dict(db.execute(f"""SELECT w.key, coalesce(w.editors_printed, '') FROM '{G}/work.parquet' w JOIN ck ON ck.key = w.key""").fetchall())
    # identifiers
    want_ids = {}
    for r in pr:
        for x in r['work_ids'].split():
            if x.split(':', 1)[0] in ('lccn', 'isbn', 'doi'):
                want_ids.setdefault(x.lower() if x.startswith('doi:') else x, set()).add(r['id'])
    id_hits = defaultdict(set)
    if want_ids:
        db.register('wi', pa.table({'a': list(want_ids)}))
        for a, k in db.execute(f"""SELECT a, key FROM (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a IN (SELECT a FROM wi)
                                   UNION SELECT 'isbn:' || i, key FROM (SELECT key, unnest(string_split(isbn, ';')) i FROM '{G}/work.parquet'
                                   WHERE isbn IS NOT NULL) WHERE 'isbn:' || i IN (SELECT a FROM wi)""").fetchall():
            for rid in want_ids[a]:
                id_hits[rid].add(k)
    byrow = defaultdict(list)
    for c in cand:
        byrow[c[0]].append(c)
    rowmap = {r['id']: r for r in pr}
    rank_res = {'established': 0, 'recorded': 1, 'linked': 2, 'unkeyed': 3}
    out = {}
    for rid, r in rowmap.items():
        fam = fam_of(r['winner_clean'], L)
        given = given_of(r['winner_clean'], L)
        hits = sorted(id_hits.get(rid, ()))
        if hits:
            out[rid] = dict(state='matched', work=hits[0], basis='id', candidates='|'.join(hits), n=len(hits))
            continue
        passing, title_only = [], []
        mtw = len((rowmap[rid]['work_title'].split(':')[0]).split())
        for _, key, label, kind, year, res, basis, mt, wt in byrow.get(rid, ()):
            if not mt and not wt:
                continue
            one_word = len((mt or '').split()) <= 1
            if one_word and basis not in ('whole',):
                # 'Dammed' alone is no match; the subtitle's first three words must agree
                sub_p = K_py_words(r['work_title'].split(':', 1)[1] if ':' in r['work_title'] else '')
                sub_g = K_py_words(label.split(' / ')[0].split(':', 1)[1] if ':' in label.split(' / ')[0] else '')
                if len(sub_p) < 3 or sub_p[:3] != sub_g[:3]:
                    continue
            auth = author_agrees(fam, given, credits.get(key, ()), label, extra.get(key, ''), L)
            if auth:
                passing.append((key, label, kind, year, res, basis, auth))
            elif not credits.get(key) and ' / ' not in label and not extra.get(key) and basis == 'whole' and \
                    len((wt or '').split()) >= 4 and year and year_of(r) and year_of(r) - 5 <= year <= year_of(r):
                title_only.append((key, label, kind, year, res, basis, 'no-author-on-work'))
        if passing:
            want_kind = {'book': ('book', 'other'), 'article': ('article', 'other', 'chapter'), 'dissertation': ('thesis',)}.get(r['honours'], ())
            py = year_of(r) or 9999
            passing.sort(key=lambda x: (x[2] not in want_kind, rank_res.get(x[4], 4), 0 if (x[3] or 0) <= py + 1 else 1,
                                        abs(py - (x[3] or py)), x[0]))
            best = passing[0]
            out[rid] = dict(state='matched', work=best[0], basis=f'title-{best[5]}+{best[6]}', candidates='|'.join(x[0] for x in passing),
                            n=len(passing), kind=best[2], wyear=best[3] or '')
        elif title_only:
            out[rid] = dict(state='possible', work='', basis='title-only', candidates='|'.join(x[0] for x in title_only), n=len(title_only))
        else:
            out[rid] = dict(state='none', work='', basis='', candidates='', n=0)
    return out, credits


def K_py_words(t):
    from key_cited_works_lc_full import py_words
    w = py_words(t)
    while w and w[0] in ('the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'):
        w = w[1:]
    return w


def fam_of(name, L):
    f = L.forms(name)
    return f[0][0] if f else ''


def given_of(name, L):
    f = L.forms(name)
    return f[0][2] if f else ()


def author_agrees(fam, given, credits, label, editors, L):
    """the winner's family name (and given name, where both are printed) agrees with a credited person, or the family name
    is in the label's statement of responsibility or the printed editors"""
    if not fam:
        return ''
    for p, ev, plab in credits:
        for f, _, g in L.forms(plab or ''):
            if f == fam and (not given or not g or L.name_level(given, g)):
                return f'credit:{ev}'
    stmt = (label.split(' / ', 1)[1] if ' / ' in label else '') + ' ' + (editors or '')
    if stmt.strip() and re.search(r'\b' + re.escape(fam) + r'\b', L.nfold(stmt)):
        return 'statement'
    return ''


# ---------------------------------------------------------------- people

def build_people(db):
    import link_work_people as WP
    import link_cited_work_authors as L
    L.GRAPH = GRAPH
    WP.GRAPH = GRAPH
    people = WP.WPPeople(db)
    return WP, L, people


def link(args):
    t0 = time.time()
    rows = read_prizes()
    db = duck()
    import link_cited_work_authors as L
    for r in rows:
        r['winner_clean'] = clean_name(r['winner'])
    # 1. works
    wm, credits = match_works(db, rows, L)
    print('works', Counter(v['state'] for v in wm.values()), round(time.time() - t0), flush=True)
    # 2. people
    WP, L, people = build_people(db)
    print('people', len(people.label), round(time.time() - t0), flush=True)
    anchor_key = defaultdict(set)
    for k, an in db.execute(f"SELECT key, anchors FROM '{GRAPH}/person.parquet'").fetchall():
        for a in an or []:
            if a.split(':', 1)[0] in ('wd', 'lcnaf', 'orcid', 'gnd', 'viaf', 'isni', 'idref'):
                anchor_key[a].add(k)
    needed = set()
    for r in rows:
        for f, _, g in L.forms(r['winner_clean'])[:1]:
            needed.add((f, g[0]))
    for lab in people.label.values():
        for f, _, g in L.forms(lab):
            needed.add((f, g[0]))
    pop = L.population_counts(db, needed)
    print('population', round(time.time() - t0), flush=True)
    P = dict(json.loads((ROOT / 'data/identifiers/cited-work-authors-2026-11-10/report.json').read_text())['tuning']['chosen'])
    P['FACTS'] = tuple(P['FACTS'])
    P['XDATE'] = tuple(P['XDATE'])
    L.PARAMS.update({k: v for k, v in P.items() if k in L.PARAMS})
    # theses citing matched works (own-thesis / student-thesis facts)
    mk = sorted({v['work'] for v in wm.values() if v.get('work')})
    import pyarrow as pa
    db.register('mk', pa.table({'key': mk}))
    citers_of = defaultdict(set)
    for w, d in db.execute(f"""SELECT c."to", replace(a, 'diss-thesis:', '') FROM '{GRAPH}/cites.parquet' c
            JOIN (SELECT key, unnest(anchors) a FROM '{GRAPH}/work.parquet' WHERE kind = 'thesis') t ON t.key = c."from"
            WHERE a LIKE 'diss-thesis:%' AND c."to" IN (SELECT key FROM mk)""").fetchall():
        citers_of[w].add(d)
    out = []
    for r in rows:
        nm = r['winner_clean']
        w = wm.get(r['id'], {})
        base = dict(id=r['id'], winner=r['winner'], name_used=nm, work=w.get('work', ''), state='', key='', branch='',
                    candidates='', n_candidates=0, signals='')
        if not nm or ORG.search(nm) or len(nm.split()) < 2:
            out.append(dict(base, state='not-a-person' if nm else 'no-name'))
            continue
        # exact: identifiers on the row
        ids = []
        if r['wd_person']:
            ids.append('wd:' + r['wd_person'])
        for sch in ('lcnaf', 'orcid', 'gnd', 'viaf', 'isni', 'idref'):
            ids += [f'{sch}:{x.replace(" ", "")}' for x in ids_of(r['person_ids'], sch)]
        hit = set()
        for a in ids:
            hit |= anchor_key.get(a, set())
        if len(hit) == 1:
            out.append(dict(base, state='exact', key=next(iter(hit)), branch='identifier:' + ','.join(
                sorted({a.split(':')[0] for a in ids if anchor_key.get(a)})), n_candidates=1))
            continue
        if len(hit) > 1:
            out.append(dict(base, state='exact-conflict', candidates='|'.join(sorted(hit)), n_candidates=len(hit),
                            branch='identifiers-on-several-keys'))
            continue
        # credited on the matched work
        if w.get('work'):
            fams = L.forms(nm)
            ok = []
            for p, ev, plab in credits.get(w['work'], ()):
                for f, _, g in L.forms(plab or ''):
                    if any(f == f0 and L.name_level(g0, g) for f0, _, g0 in fams):
                        ok.append((p, ev))
            ks = sorted({p for p, _ in ok})
            if len(ks) == 1:
                ev = 'keylog' if any(e == 'keylog' for _, e in ok) else 'linked'
                out.append(dict(base, state='credited', key=ks[0], branch=f'work-credit:{ev}:{w["basis"]}', n_candidates=1))
                continue
        # the linker's rule
        y = w.get('wyear') or year_of(r)
        born = next(iter(ids_of(r['person_ids'], 'born')), None)
        died = next(iter(ids_of(r['person_ids'], 'died')), None)
        aff = re.findall(r'affiliation:\s*([^;]+)', r['note'])
        p = dict(src='prize', swork=r['id'], work_id=w.get('work') or r['id'], oa_id='', pos=0, role='prize-winner', name=WP.apos(nm),
                 title=r['work_title'], year=int(y) if y else None, book=r['honours'] == 'book', lc=ids_of(r['person_ids'], 'lcnaf'),
                 lc_how='', orcid=next(iter(ids_of(r['person_ids'], 'orcid')), ''), oa_author='', rors=[], insts=[],
                 raw_aff=aff[:3], citing=0, sb=int(born) if born and born.isdigit() else None,
                 sd=int(died) if died and died.isdigit() else None, initial_check='', venue='', oa_type='')
        p['forms'] = L.forms(p['name'])
        exacts = {k for k, ev, _ in credits.get(w.get('work'), ()) if ev == 'keylog'} if w.get('work') else set()
        fe = L.features(people, p, exacts=exacts, citers_of=citers_of)
        st, k, br, cands, sig = WP.rule_wp(people, p, fe, pop, P)
        out.append(dict(base, state=st, key=k or '', branch=br, candidates='|'.join(cands if st != 'exact' else []),
                        n_candidates=len(cands or []), signals=' '.join(sig)))
    print('winners', Counter(o['state'] for o in out), round(time.time() - t0), flush=True)
    # 3. LC lookups for prize works with no node
    lc = lc_lookup(db, rows, wm, L, people)
    print('lc', len(lc), round(time.time() - t0), flush=True)
    # 4. corpus uptake of prize works (local works.csv)
    uptake = corpus_uptake(db, rows, wm, L)
    write_all(rows, wm, out, lc, uptake, people, db)
    print('done', round(time.time() - t0), flush=True)


def lc_lookup(db, rows, wm, L, people):
    import pyarrow as pa
    todo = [r for r in rows if r['work_title'] and wm.get(r['id'], {}).get('state') != 'matched'
            and r['honours'] in ('book', 'other', 'career', 'dissertation')]
    cols = defaultdict(list)
    for r in todo:
        t = re.sub(r'\s+', ' ', r['work_title']).strip(' “”"«»‘’')
        alt = t.split('. ', 1)[0] if '. ' in t and ':' not in t and len(t.split('. ', 1)[0].split()) >= 2 else t
        cols['id'].append(r['id'])
        cols['title'].append(t)
        cols['alt'].append(alt)
        cols['fam'].append(fam_of(r['winner_clean'], L))
    if not todo:
        return {}
    db.register('pa_lt', pa.table(dict(cols)))
    from key_cited_works_lc_full import F
    db.execute(f"""CREATE OR REPLACE TABLE lt AS SELECT id, title, fam, {K("split_part(title, ':', 1)")} mt, {K('title')} wt,
                   {K('alt')} altk, {F('fam')} famc FROM pa_lt""")
    db.execute("CREATE OR REPLACE TABLE lwant AS SELECT mt k FROM lt UNION SELECT wt FROM lt UNION SELECT altk FROM lt")
    R, H = f"'{LC_INDEX}/records-*.parquet'", f"'{LC_INDEX}/headings-*.parquet'"
    db.execute(f"""CREATE OR REPLACE TABLE lrec AS SELECT * FROM (SELECT trim(control) control, lccn, title, date1, responsibility,
                   publisher, {K('coalesce(title_a, title)')} a, {K('title')} full_ FROM {R} WHERE NOT starts_with(control, 'mm'))
                   WHERE a IN (SELECT k FROM lwant) OR full_ IN (SELECT k FROM lwant)""")
    db.execute(f"""CREATE OR REPLACE TABLE lhead AS SELECT trim(h.control) control, h.tag, h.heading, h.uri, {F('h.family')} famc
                   FROM {H} h WHERE trim(h.control) IN (SELECT control FROM lrec) AND h.tag IN ('100', '700', '110', '710')""")
    hits = db.execute(f"""SELECT lt.id, r.lccn, r.title, r.date1, r.publisher, r.control,
               (SELECT string_agg(h2.heading || '|' || coalesce(h2.uri, ''), ' ;; ') FROM lhead h2 WHERE h2.control = r.control AND h2.tag = '100') main,
               EXISTS (SELECT 1 FROM lhead h WHERE h.control = r.control AND h.famc = lt.famc) heading_fam,
               ({F('r.responsibility')} LIKE '%' || lt.famc || '%') resp_fam
            FROM lt JOIN lrec r ON r.a = lt.mt OR r.full_ = lt.wt OR r.a = lt.altk OR r.full_ = lt.mt
            WHERE lt.famc <> '' """).fetchall()
    lc = defaultdict(list)
    for rid, lccn, title, date1, pub, control, main, hf, rf in hits:
        if not (hf or rf):
            continue
        lc[rid].append(dict(lccn=(lccn or '').strip(), lc_title=title, lc_year=(date1 or '')[:4], publisher=pub or '',
                            main_entry=main or '', source='lc-bib-2016', basis='heading' if hf else 'statement'))
    # LC SRU records of H-Net books (later than 2016)
    want = {}
    for r in todo:
        if r['id'] not in lc:
            want.setdefault(K_py_words(r['work_title'].split(':')[0])[:10].__str__(), []).append(r)
    with open(LC_BOOKS, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            rec = d.get('record') or {}
            if not rec.get('title'):
                continue
            k = K_py_words(rec['title'].split(':')[0].split(' / ')[0])[:10].__str__()
            for r in want.get(k, ()):
                fam = fam_of(r['winner_clean'], L)
                hs = d.get('headings') or []
                if any(L.fam_norm(h.get('family', '')) == fam for h in hs):
                    main = [h for h in hs if h.get('tag') == '100']
                    lc[r['id']].append(dict(lccn=rec.get('lccn', ''), lc_title=rec['title'], lc_year='', publisher='',
                                            main_entry=' ;; '.join(f"{h['heading']}|{h.get('uri', '')}" for h in main),
                                            source='lc-sru-hnet-books', basis='heading'))
    # main-entry heading -> LC name authority: the URI when the record carries one, else the heading text as the
    # authorised label of exactly one live authority (key_cited_works_lc_full's first resolution rule)
    heads = sorted({h['main_entry'].split(' ;; ')[0].split('|')[0].strip().rstrip('.') for hs in lc.values() for h in hs
                    if h['main_entry']})
    auth = defaultdict(set)
    if heads:
        db.register('hd', pa.table({'h': heads}))
        for lcid, label in db.execute(f"""SELECT lcid, rtrim(label, '.') FROM '{LC_NAMES}' WHERE NOT deprecated
                AND NOT coalesce(undifferentiated, false) AND rtrim(label, '.') IN (SELECT h FROM hd)""").fetchall():
            auth[label].add(lcid)
    for rid, hs in lc.items():
        for h in hs:
            m = re.search(r'id\.loc\.gov/authorities/names/(n[a-z]*\d+)', h['main_entry'])
            hd = h['main_entry'].split(' ;; ')[0].split('|')[0].strip().rstrip('.')
            h['lcnaf'] = m.group(1) if m else (next(iter(auth[hd])) if len(auth.get(hd, ())) == 1 else '')
            ks = people.lc_key.get(h['lcnaf'], set()) if h['lcnaf'] else set()
            h['author_key'] = next(iter(ks)) if len(ks) == 1 else ''
    return lc


def corpus_uptake(db, rows, wm, L):
    """prize works (matched or not) -> corpus works by title key + family name; the citing theses (works.csv, local)."""
    import pyarrow as pa
    from key_cited_works_lc_full import F
    pr = [r for r in rows if r['work_title']]
    db.register('pa_cu', pa.table({'id': [r['id'] for r in pr], 'title': [r['work_title'] for r in pr],
                                   'fam': [fam_of(r['winner_clean'], L) for r in pr]}))
    mt = K("split_part(title, ':', 1)")
    db.execute(f"CREATE OR REPLACE TABLE cu AS SELECT id, {mt} mt, {K('title')} wt, {F('fam')} famc FROM pa_cu")
    src = CORPUS / 'works.csv'
    if not src.exists():
        return {}
    mtk = K("split_part(title, ':', 1)")
    db.execute(f"""CREATE OR REPLACE TABLE cw AS SELECT * FROM (SELECT work_id, authors, try_cast(cited_by_dissertations AS INT) n,
                   {mtk} mt, {K('title')} wt FROM read_csv('{src}', all_varchar=true)
                   WHERE kind IN ('book', 'edited_book', 'book_or_serial', 'thesis_or_book', 'unstyled', 'article', 'chapter'))
                   WHERE wt IN (SELECT wt FROM cu) OR mt IN (SELECT mt FROM cu WHERE mt LIKE '% %')""")
    res = db.execute(f"""SELECT id, list(DISTINCT work_id), max(n) FROM (
            SELECT cu.id, w.work_id, w.n, cu.famc, w.authors FROM cu JOIN cw w ON w.wt = cu.wt
            UNION ALL SELECT cu.id, w.work_id, w.n, cu.famc, w.authors FROM cu JOIN cw w ON w.mt = cu.mt WHERE cu.mt LIKE '% %')
            WHERE famc <> '' AND {F('authors')} LIKE '%' || famc || '%' GROUP BY 1""").fetchall()
    return {rid: dict(corpus_works='|'.join(sorted(ws))[:400], citing_theses=n or 0) for rid, ws, n in res}


def write_all(rows, wm, out, lc, uptake, people, db):
    OUT.mkdir(parents=True, exist_ok=True)
    orcid_keys = {k for k, s in people.orcid.items() if s}
    with gzip.open(OUT / 'winners.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        cols = ['id', 'winner', 'name_used', 'state', 'key', 'branch', 'candidates', 'n_candidates', 'work', 'signals']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for o in out:
            w.writerow({c: o.get(c, '') for c in cols})
    rowmap = {r['id']: r for r in rows}
    with gzip.open(OUT / 'works.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        cols = ['id', 'work_title', 'state', 'work', 'basis', 'candidates', 'n_candidates', 'lc_lccn', 'lc_author_key',
                'corpus_citing_theses']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for rid, v in wm.items():
            l0 = (lc.get(rid) or [{}])[0]
            w.writerow(dict(id=rid, work_title=rowmap[rid]['work_title'], state=v['state'], work=v.get('work', ''),
                            basis=v.get('basis', ''), candidates=v.get('candidates', ''), n_candidates=v.get('n', 0),
                            lc_lccn=l0.get('lccn', ''), lc_author_key=l0.get('author_key', ''),
                            corpus_citing_theses=uptake.get(rid, {}).get('citing_theses', '')))
    with gzip.open(OUT / 'lc.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        cols = ['id', 'lccn', 'lc_title', 'lc_year', 'publisher', 'main_entry', 'lcnaf', 'author_key', 'source', 'basis', 'n_records']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for rid, hs in lc.items():
            for h in hs[:5]:
                w.writerow(dict(h, id=rid, n_records=len(hs)))
    # report
    rep_path = OUT / 'report.json'
    rep = json.loads(rep_path.read_text()) if rep_path.exists() else {}
    ost = {o['id']: o for o in out}
    persons = [o for o in out if o['state'] not in ('not-a-person', 'no-name')]
    by_state = Counter(o['state'] for o in persons)
    orc = Counter((o['state'], bool(o['key']) and any(k in orcid_keys for k in o['key'].split(';'))) for o in persons)
    distinct = {}
    for o in persons:
        if o['key']:
            distinct.setdefault(o['state'], set()).add(o['key'])
    wrows = [rid for rid in wm]
    nonode = [rid for rid in wrows if wm[rid]['state'] != 'matched']
    books = [rid for rid in wrows if rowmap[rid]['honours'] == 'book']
    rep['linkage'] = dict(
        graph=str(GRAPH), date='2026-11-12',
        winner_rows=len(out), person_rows=len(persons), not_a_person=sum(1 for o in out if o['state'] == 'not-a-person'),
        winners_by_state=dict(by_state),
        winners_by_state_and_orcid={f'{s}|{"orcid" if h else "no-orcid"}': n for (s, h), n in sorted(orc.items())},
        distinct_keys_by_state={s: len(v) for s, v in distinct.items()},
        winners_by_state_and_source_kind={f'{s}|{k}': n for (s, k), n in sorted(Counter(
            (o['state'], rowmap[o['id']]['source_kind']) for o in persons).items())},
        winners_awarding_body_by_country_state={f'{c}|{s}': n for (c, s), n in sorted(Counter(
            (rowmap[o['id']]['body_country'], o['state']) for o in persons if rowmap[o['id']]['source_kind'] != 'wikidata').items())},
        work_rows=len(wrows), works_by_state=dict(Counter(wm[r]['state'] for r in wrows)),
        works_by_basis=dict(Counter(wm[r].get('basis', '').split('+')[0] for r in wrows if wm[r]['state'] == 'matched')),
        book_rows=len(books), book_rows_matched=sum(1 for r in books if wm[r]['state'] == 'matched'),
        works_by_honours_state={f'{h}|{s}': n for (h, s), n in sorted(Counter((rowmap[r]['honours'], wm[r]['state']) for r in wrows).items())},
        works_by_country_state={f'{c}|{s}': n for (c, s), n in sorted(Counter((rowmap[r]['body_country'], wm[r]['state']) for r in wrows).items())},
        no_node=len(nonode), no_node_with_lc=sum(1 for r in nonode if lc.get(r)),
        no_node_lc_with_author_key=sum(1 for r in nonode if any(h.get('author_key') for h in lc.get(r, ()))),
        no_node_lc_by_source=dict(Counter(lc[r][0]['source'] for r in nonode if lc.get(r))),
        no_node_by_year_band=dict(Counter(('<2017' if (year_of(rowmap[r]) or 0) < 2017 else '2017+') for r in nonode)),
        no_node_with_corpus_citations=sum(1 for r in nonode if uptake.get(r, {}).get('citing_theses')),
        no_node_corpus_citing_theses_max_sum=sum(uptake.get(r, {}).get('citing_theses', 0) for r in nonode),
        matched_with_corpus_citations=sum(1 for r in wrows if wm[r]['state'] == 'matched' and uptake.get(r, {}).get('citing_theses')),
        corpus_uptake_note=('citing theses from the corpus works table (data/field-research/dissertation-citations-2026-10-11/works.csv, '
                            'local and untracked; max of cited_by_dissertations over the corpus works whose title key and author family agree); '
                            'the tracked tables hold only matched works, so the figure cannot come from them'))
    rep_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep['linkage'], indent=1)[:4000])


# ---------------------------------------------------------------- the Dammed class

def dammed_class(args):
    """Corpus-cited books of 2017+ that no matcher holds: count; then a random sample looked up in OpenAlex (title search,
    project key, capped) for how many exist there outside the History/HPS subfields the harvest takes (1202, 1207)."""
    import random
    import urllib.parse
    import urllib.request
    db = duck()
    xw = sorted(str(p) for p in (ROOT / 'data/identifiers').glob('*/crosswalk.csv.gz'))
    xw = [p for p in xw if gzip.open(p, 'rt').readline().startswith('work_id,')]
    db.execute("CREATE TABLE m AS " + ' UNION '.join(f"SELECT work_id FROM read_csv('{p}', all_varchar=true)" for p in xw))
    q = f"""SELECT work_id, title, authors, try_cast(year AS INT) y, try_cast(cited_by_dissertations AS INT) n, kind
            FROM read_csv('{CORPUS / 'works.csv'}', all_varchar=true) WHERE kind IN ('book', 'edited_book')
            AND try_cast(year AS INT) >= 2017 AND work_id NOT IN (SELECT work_id FROM m)"""
    db.execute('CREATE TABLE u AS ' + q)
    tot = db.execute("SELECT count(*), sum(n), count(*) FILTER (WHERE n >= 2), sum(n) FILTER (WHERE n >= 2) FROM u").fetchone()
    all_ = db.execute(f"""SELECT count(*), sum(try_cast(cited_by_dissertations AS INT)) FROM read_csv('{CORPUS / 'works.csv'}', all_varchar=true)
                         WHERE kind IN ('book', 'edited_book') AND try_cast(year AS INT) >= 2017""").fetchone()
    res = dict(crosswalks=len(xw), books_2017_plus=dict(works=all_[0], citations=all_[1]),
               unmatched_books_2017_plus=dict(works=tot[0], citations=tot[1], works_cited_2plus=tot[2], citations_cited_2plus=tot[3]))
    sample = db.execute("SELECT work_id, title, authors, y, n FROM u WHERE n >= 2").fetchall()
    random.Random(12).shuffle(sample)
    sample = sample[:args.sample]
    from openalex_ingest import load_api_key
    key = load_api_key()
    cost = 0.0
    found = Counter()
    rows = []
    for wid, title, authors, y, n in sample:
        if cost >= args.cap:
            break
        fam = (authors or '').split(';')[0].split(',')[0].strip()
        u = 'https://api.openalex.org/works?' + urllib.parse.urlencode(dict(
            search=f'{title.split(":")[0]} {fam}'[:200], per_page=5, filter=f'publication_year:{y - 1}-{y + 1}',
            select='id,title,type,publication_year,primary_topic,authorships', api_key=key))
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'historiography-kg-research/0.1'}), timeout=60)
            cost += float(r.headers.get('X-RateLimit-Cost-USD') or 0.001)
            d = json.load(r)
        except Exception as e:
            rows.append(dict(work_id=wid, outcome='error:' + type(e).__name__))
            continue
        time.sleep(0.2)
        tk = ' '.join(K_py_words(title.split(':')[0])[:6])
        hit = None
        for w in d.get('results', []):
            if ' '.join(K_py_words((w.get('title') or '').split(':')[0])[:6]) == tk and any(
                    fam.lower() in (a['author'].get('display_name') or '').lower() for a in w.get('authorships', [])):
                hit = w
                break
        if not hit:
            outcome = 'not-found'
        else:
            sf = (((hit.get('primary_topic') or {}).get('subfield') or {}).get('id') or '').rsplit('/', 1)[-1]
            outcome = ('in-openalex:history-subfield' if sf in ('1202', '1207') else
                       f'in-openalex:other-subfield' if sf else 'in-openalex:no-topic') + ('' if hit['type'] == 'book' else f':type-{hit["type"]}')
        found[outcome] += 1
        rows.append(dict(work_id=wid, title=title, year=y, citing=n, outcome=outcome,
                         openalex=(hit or {}).get('id', ''), subfield=(((hit or {}).get('primary_topic') or {}).get('subfield') or {}).get('display_name', '')))
    res['openalex_sample'] = dict(size=len(rows), outcomes=dict(found), cost_usd=round(cost, 4))
    (SCR / 'dammed-class-sample.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    rep_path = OUT / 'report.json'
    rep = json.loads(rep_path.read_text()) if rep_path.exists() else {}
    rep['dammed_class'] = res
    rep_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('link')
    a = sub.add_parser('dammed-class')
    a.add_argument('--sample', type=int, default=200)
    a.add_argument('--cap', type=float, default=0.30)
    args = ap.parse_args()
    {'link': link, 'dammed-class': dammed_class}[args.cmd](args)


if __name__ == '__main__':
    main()
