"""Prize layer for scripts/build_graph.py (2026-11-12, integration pass five; specification in the prize builder's
LOADER-SPEC, summarised in data/graph/README.md and ARCHITECTURE.md section 8, classes 28 and 31).

Inputs (tracked, data/graph/prizes/, written by scripts/prizes_harvest.py and scripts/prizes_link.py, and found.csv.gz by
scripts/key_cited_works_recent_books.py): prizes, winners, works, lc, found.

- Prize nodes (prize.parquet; key prize_id, never in the key log).
- AWARDED (awarded.parquet): Prize -> Person for winners exact / credited / linked; Prize -> Work for matched works and
  for work nodes added here; evidence linked, source '<source_kind>:<body or wikidata>', state, basis, `shown`
  (an awarding body's own list or a field that names history: the explorer's default; Wikidata honours are noisy and
  stay in the table with shown = false). Shortlists, finalists and honourable mentions are not loaded (counted).
- prize_candidates.parquet: possible / ambiguous winners (never an edge).
- Work nodes for prize works without one (awarding-body or history rows only): the found record's id, else an
  `lccn:` node from the LC record (one main entry), else `prizework:<smallest row id>` shared by rows naming the same
  work (folded title, winner family, years within 3). Career and 'other' honours get no prizework node.
- Authorship proposals for prize work targets with no credit (the caller adds them only where the work has no
  AUTHORED or EDITED row): the LC main entry's key (prizes:lc-main-entry, exact) on an added lccn: node; else each
  credited winner (prizes:winner) on a book or dissertation prize (role volume-editor when the title or note says ed./eds./
  dir./edited).
General rules applied here (counted in the report):
- jury text as title: an awarding-body title of 8+ words reading as prose about the work (jury, committee, this book,
  commitment, the author, ...) is replaced by the same winner's title at the same body within one year when exactly
  one such sibling exists (rule `title-from-sibling-row`), else the row names no work;
- one-candidate winner promotion: a winner row left `possible` with exactly one candidate becomes `linked`
  (branch `same-body-credited-name`) when another row of the same awarding body, printing the same folded name, is
  credited (exact / credited / linked) to that same key.
"""
import re
import unicodedata
from collections import Counter, defaultdict

PROSE = re.compile(r"(?i)\b(jury|committee|this (book|study|work|volume|monograph)|the author|commitment|winner|"
                   r"recipient|is awarded|was awarded|we are|congratulat|masterful|compelling|deeply researched)\b")
NOT_WIN = re.compile(r'(?i)short-?list|finalist|honou?rable mention|runner[- ]up|mention honorable|mention honorifique')
EDITED = re.compile(r'(?i)\b(eds?\.|\(dir\.\)|edited by|editors?\b|\(org\.\)|\(coord\.\))')
SHOWN_FIELD = re.compile(r'(?i)histor')


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def prose_title(t):
    return len((t or '').split()) >= 8 and bool(PROSE.search(t or ''))


def shown(r):
    return r['source_kind'] == 'awarding-body' or bool(SHOWN_FIELD.search(r['field'] or ''))


def intor(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def prize_layer(read_rows, P, state, types, works, wi, unkeyed, resolve, report):
    """Returns dict(prizes, awarded, candidates, authors) and adds work nodes to `works` / `wi` / `unkeyed`."""
    R = Counter()
    rows = {r['id']: r for r in read_rows(P / 'prizes.csv.gz')}
    win = {r['id']: r for r in read_rows(P / 'winners.csv.gz')}
    wk = {r['id']: r for r in read_rows(P / 'works.csv.gz')}
    lc = defaultdict(list)
    for r in read_rows(P / 'lc.csv.gz'):
        lc[r['id']].append(r)
    found = {r['prize_row']: r for r in read_rows(P / 'found.csv.gz')}

    def person(name):
        ks = [k for k in state.lookup(name) if types.get(k) == 'person'] if name else []
        return ks[0] if len(ks) == 1 else None

    # jury text as title
    title = {i: (r['work_title'] or '').strip() for i, r in rows.items()}
    alias = {}
    by_wb = defaultdict(list)
    for i, r in rows.items():
        if r['source_kind'] == 'awarding-body':
            by_wb[(fold(r['winner']), r['body'])].append(i)
    for i, r in rows.items():
        if r['source_kind'] != 'awarding-body' or not prose_title(title[i]):
            continue
        R['title_prose'] += 1
        y = intor(r['year'])
        sib = {fold(title[j]): j for j in by_wb[(fold(r['winner']), r['body'])] if j != i and title[j]
               and not prose_title(title[j]) and y is not None and intor(rows[j]['year']) is not None
               and abs(intor(rows[j]['year']) - y) <= 1}
        if len(sib) == 1:
            alias[i] = next(iter(sib.values()))
            title[i] = title[alias[i]]
            R['title_from_sibling_row'] += 1
        else:
            title[i] = ''
            R['title_prose_no_sibling'] += 1
    # winners: credited states, plus the one-candidate promotion
    wstate = {}
    cred = defaultdict(set)
    for i, w in win.items():
        if w['state'] in ('exact', 'credited', 'linked'):
            k = person(w['key'])
            if k:
                wstate[i] = (k, w['state'], w['branch'])
                cred[(fold(w['winner']), rows[i]['body'])].add(k)
            else:
                R['winner_key_unresolved'] += 1
    for i, w in win.items():
        if w['state'] == 'possible' and w['n_candidates'] == '1':
            k = person(w['candidates'].split('|')[0])
            if k and k in cred.get((fold(w['winner']), rows[i]['body']), ()):
                wstate[i] = (k, 'linked', 'same-body-credited-name')
                R['winner_promoted_same_body_credited_name'] += 1
    # prize nodes
    pz = {}
    for i, r in rows.items():
        p = pz.setdefault(r['prize_id'], dict(key=r['prize_id'], label=r['prize'], body=r['body'] or None,
                                              body_country=r['body_country'] or None, fields=Counter(), honours=Counter(),
                                              wd=set(), sources=set(), rows=0, years=[], shown=False))
        p['fields'][r['field'] or ''] += 1
        p['honours'][r['honours']] += 1
        if r['wd_prize']:
            p['wd'].add(r['wd_prize'])
        p['sources'].add(r['source_kind'])
        p['rows'] += 1
        if intor(r['year']):
            p['years'].append(intor(r['year']))
        p['shown'] = p['shown'] or shown(r)
    prizes = [dict(key=k, label=p['label'], body=p['body'], body_country=p['body_country'],
                   field=p['fields'].most_common(1)[0][0] or None, honours=p['honours'].most_common(1)[0][0],
                   wd=next(iter(p['wd'])) if len(p['wd']) == 1 else None, sources=';'.join(sorted(p['sources'])),
                   rows=p['rows'], first_year=min(p['years']) if p['years'] else None,
                   last_year=max(p['years']) if p['years'] else None, shown=p['shown']) for k, p in pz.items()]
    # work targets
    target, added = {}, {}

    def add_node(key, label, kind, year, anchors, src, extra=None):
        unkeyed.add(key)
        types[key] = 'work'
        w = dict(key=key, label=label or None, resolution='unkeyed', anchors=sorted(set(anchors)), kind=kind,
                 lccn=next((a[5:] for a in anchors if a.startswith('lccn:')), None), year=year, reviewer_names=[], journal=None)
        if extra:
            w.update(extra)
        works.append(w)
        wi[key] = w
        added[key] = src
        R[f'prize_work_nodes_added_{src}'] += 1
        return key
    groups = {}
    for i in sorted(rows):
        r = rows[i]
        h = r['honours']
        if h not in ('book', 'article', 'dissertation', 'other') or not title[i] or NOT_WIN.search(r['note'] or ''):
            continue
        t = alias.get(i, i)
        m = wk.get(t)
        if m and m['state'] == 'matched' and m['work']:
            n = resolve(m['work'])
            if n:
                target[i] = (n, 'matched', m['basis'])
                continue
            R['matched_work_unresolved'] += 1
        if not shown(r):
            R['prize_work_not_added_not_shown'] += 1
            continue
        f = found.get(t)
        if f:
            ids = [f['id']] + [x for x in (f['alias_ids'] or '').split(';') if x]
            n = next((x for x in (resolve(y) for y in ids) if x), None)
            if not n:
                n = add_node(f['id'], f['title'], {'article': 'article', 'dissertation': 'thesis'}.get(h, 'book'),
                             intor(f['year']), ids, 'found')
            target[i] = (n, 'found', f"{f['source']}:{f['basis']}")
            continue
        L = lc.get(t, [])
        if L and (len(L) == 1 or len({x['main_entry'] for x in L}) == 1):
            x = L[0]
            key = f"lccn:{x['lccn']}"
            n = resolve(key) or (key if key in unkeyed else None)
            if not n:
                n = add_node(key, x['lc_title'], 'book', intor(x['lc_year']), [key], 'lccn')
                if x['author_key']:
                    added[n] = ('lccn', x['author_key'])
            target[i] = (n, 'lc', x['basis'])
            continue
        if h == 'other':
            R['prize_work_other_honours_no_record'] += 1
            continue
        g = (fold(title[i]), fold(r['winner']).split(' ')[-1:][0] if fold(r['winner']) else '')
        y = intor(r['year'])
        hit = next((k for (gk, yy), k in groups.items() if gk == g and y is not None and yy is not None and abs(yy - y) <= 3), None)
        if not hit:
            key = f'prizework:{i}'
            hit = add_node(key, title[i] + (f' / {r["winner"]}' if r['winner'] else ''),
                           {'book': 'book', 'article': 'article', 'dissertation': 'thesis'}[h], y, [key], 'prizeonly',
                           extra=dict(year_basis='prize-year'))
            groups[(g, y)] = hit
        target[i] = (hit, 'added', 'prize-only')
    # AWARDED, candidates, authorship proposals
    awarded, cands, authors = [], [], []
    for i, r in rows.items():
        if NOT_WIN.search(r['note'] or ''):
            R['rows_not_winning'] += 1
            continue
        base = dict(year=intor(r['year']), honours=r['honours'], row=i, evidence='linked',
                    source=f"{r['source_kind']}:{r['body'] or 'wikidata'}", source_url=r['source_url'] or None,
                    note=r['note'] or None, co_winners=r['co_winners'] or None, shown=shown(r))
        ws = wstate.get(i)
        if ws:
            awarded.append(dict(base, **{'from': r['prize_id'], 'to': ws[0], 'target': 'person', 'state': ws[1], 'basis': ws[2]}))
            R[f'AWARDED_person|{ws[1]}'] += 1
        else:
            w = win.get(i)
            st = w['state'] if w else 'missing'
            R[f'winners_unlinked|{st}'] += 1
            if st in ('possible', 'ambiguous'):
                ks = sorted({k for c in re.split(r'[|;]', w['candidates'] or '') if (k := person(c))})
                for k in ks:
                    cands.append({'from': r['prize_id'], 'to': k, 'row': i, 'prize': r['prize'], 'n_candidates': len(ks),
                                  'branch': w['branch'] or None, 'signals': w['signals'] or None, 'shown': shown(r)})
        t = target.get(i)
        if t:
            awarded.append(dict(base, **{'from': r['prize_id'], 'to': t[0], 'target': 'work', 'state': t[1], 'basis': t[2]}))
            R[f'AWARDED_work|{t[1]}'] += 1
            src = added.get(t[0])
            if isinstance(src, tuple):            # an lccn: node added here whose LC main entry is on a key
                k = person(src[1])
                if k:
                    authors.append(dict(person=k, work=t[0], source='prizes:lc-main-entry', state='exact', role='author',
                                        basis='lc-main-entry'))
            if ws and r['honours'] in ('book', 'dissertation'):
                ed = bool(EDITED.search(title[i] + ' ' + (r['note'] or '')))
                authors.append(dict(person=ws[0], work=t[0], source='prizes:winner', state=ws[1],
                                    role='volume-editor' if ed else 'author', basis=f'prize-winner:{ws[2]}'))
    R['prize_nodes'] = len(prizes)
    R['prize_rows'] = len(rows)
    R['prize_candidates'] = len(cands)
    report['prizes'] = dict(sorted(R.items()))
    return dict(prizes=prizes, awarded=awarded, candidates=cands, authors=authors, targets={t[0] for t in target.values()})
