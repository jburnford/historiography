"""Scorer-only links for scripts/build_graph.py (2026-11-12; data/graph/scored-links/, written by scripts/score_links.py,
a Fellegi-Sunter scored linkage of printed names to person keys; ARCHITECTURE.md section 8).

Specification (from the scorer's report):
1. the rule linkers' rows stay exactly as they are;
2. a position the scorer links to the same key as the rule adds nothing: the existing linked row gets `score` (AUTHORED /
   EDITED have a `score` column; null elsewhere); a key-log row is counted, not annotated;
3. scorer-only links (decision `link`, no rule link on the position) load as evidence linked, source `scored-links`,
   state `scored`, with the score; author-role positions (author, jstor-author, LC main entry) on a work that reads as
   a review (title 'Review of' / 'Rezension' / 'Reseña' / 'Compte rendu' ..., kind or proposed kind review, or a review in
   data/graph/review-books.csv.gz) are excluded: the scorer linked a reviewed book's author as the review's author in
   a hand-read case (Becher). Pass seven (2026-11-12, scripts/reviewed_authors.py): such a link loads when the review's
   reviewed authors are known (a person credited on the reviewed book, or a printed reviewed-author name) and the
   person is not one of them; it stays excluded when the person is the reviewed author or nobody knows who is;
4. `exact` rows are identifier links the rule path already makes: not loaded again;
5. `review` rows become author_candidates (up to three per position, best scores first; reason `scored-review`, score
   and top fields in signals) where the position has no credit and the person no candidate row on the work;
6. identity scripts read key-log rows only (graph_tables.keylog), so nothing here becomes identity evidence;
7. where the scorer and the rule name different keys for a position, neither is loaded from here and it is counted
   (the rule row, made elsewhere, is left as it is; the scorer's report counted 0 such positions).
Keys are resolved through merges at load (the scorer read the 05:00 and 09:22 builds); pairs the key log holds are
skipped. LC 700 added entries without a role (`added`, `resp`) are not loaded (counted): a 700 may be a translator.
"""
import re
from collections import Counter, defaultdict

REVIEW_TITLE = re.compile(r'(?i)^\s*(review of|reviewed work|rezension|reseña|resena|compte[- ]rendu|recensione|recensão|'
                          r'book review)\b')
AUTHOR_ROLES = ('author', 'jstor-author', 'main')


def scored_layer(read_rows, path, person1, resolve, wi, review_works, rels, linked, possible_authors, report, ra=None):
    """Adds rows to linked['AUTHORED'] / linked['EDITED'] and possible_authors in place. ra: a
    reviewed_authors.ReviewedAuthors (None: every author-role link on a review stays excluded)."""
    R = Counter()
    have = {name: {(r['from'], r['to']) for r in rels[name]} for name in ('AUTHORED', 'EDITED')}
    lidx = {name: {} for name in ('AUTHORED', 'EDITED')}
    for name in ('AUTHORED', 'EDITED'):
        for r in linked[name]:
            lidx[name].setdefault((r['from'], r['to']), r)
    cand_pairs = {(r['from'], r['to']) for r in possible_authors}
    review_cands = defaultdict(list)
    linked_positions = set()
    add = {'AUTHORED': [], 'EDITED': []}

    def table_of(role, source):
        if role in ('editor',):
            return 'EDITED', ('volume-editor' if source.startswith('ve-') else None)
        if role in AUTHOR_ROLES or role == 'reviewer':
            return 'AUTHORED', None
        return None, None

    def is_review(w):
        x = wi.get(w) or {}
        return (w in review_works or x.get('kind') == 'review' or x.get('kind_proposed') == 'review'
                or bool(REVIEW_TITLE.search(x.get('label') or '')) or (ra is not None and ra.is_review(w)))

    def review_block(k, w):
        """None when the link may load on this review, else the reason it may not"""
        if ra is None or not ra.known(w):
            return 'reviewed_author_unknown'
        why = ra.why(k, w)
        return f'is_reviewed_author:{why}' if why else None
    rows = read_rows(path)
    for r in rows:
        d = r['decision']
        pos = (r['work'], r['role'], r['position'], r['source'])
        if d == 'exact':
            R['exact_not_loaded'] += 1
            continue
        if d not in ('link', 'review'):
            continue
        name, role = table_of(r['role'], r['source'])
        if not name:
            R[f'{d}|role_not_loaded|{r["role"]}'] += 1
            continue
        w, k = resolve(r['work']), person1(r['person_key'])
        if not w or not k:
            R[f'{d}|unresolved'] += 1
            continue
        if d == 'review':
            review_cands[pos].append((float(r['score'] or 0), k, w, r))
            continue
        ruled = r['rule_state'] in ('exact', 'linked')
        rk = person1(r['rule_key']) if ruled else None
        linked_positions.add(pos)
        if ruled and rk != k:
            R['link|rule_names_another_key'] += 1
            continue
        if (k, w) in have[name]:
            R[f'link|{name}|pair_in_keylog'] += 1
            continue
        ex = lidx[name].get((k, w))
        if ex is not None:
            if ex.get('score') is None:
                ex['score'] = float(r['score']) if r['score'] else None
                ex['scored'] = True
            R[f"link|{name}|{'same_as_rule' if ruled else 'pair_already_linked'}|annotated"] += 1
            continue
        if ruled:                          # the rule linked this position to this key but the row is not in the table
            R[f'link|{name}|same_as_rule_row_absent'] += 1
            continue
        review_checked = False
        if r['role'] in AUTHOR_ROLES and is_review(w):
            block = review_block(k, w)
            if block:
                R[f'link|{r["role"]}|review|{block}'] += 1
                continue
            review_checked = True
            R[f'link|{r["role"]}|review|reviewer_checked_loaded'] += 1
        row = {'from': k, 'to': w, 'claim': f"scored-links:{r['source']}:{r['role']}:{r['position']}", 'resolution': 'linked',
               'source': 'scored-links', 'state': 'scored', 'score': float(r['score']) if r['score'] else None}
        if role:
            row['role'] = role
            row['role_basis'] = 'scored-links:volume-editors'
        if review_checked:
            row['role'] = row.get('role') or 'author'
            row['role_basis'] = 'scored-links:reviewer-checked'
        add[name].append(row)
        lidx[name][(k, w)] = row
        R[f'added|{name}|{r["role"]}|{r["source"]}'] += 1
    # review decisions: candidates where the position has no credit
    ncand = 0
    for pos, cs in review_cands.items():
        if pos in linked_positions:
            R['review|position_linked'] += 1
            continue
        n = 0
        for score, k, w, r in sorted(cs, key=lambda x: -x[0]):
            if n >= 3:
                break
            name = 'EDITED' if r['role'] == 'editor' else 'AUTHORED'
            if (k, w) in have[name] or (k, w) in lidx[name]:
                R['review|position_credited'] += 1
                break
            if (k, w) in cand_pairs:
                R['review|candidate_row_exists'] += 1
                continue
            if r['role'] in AUTHOR_ROLES and is_review(w) and review_block(k, w):
                R['review|work_reads_as_review_excluded'] += 1
                continue
            possible_authors.append({'from': k, 'to': w, 'n_candidates': len(cs), 'role': 'editor' if name == 'EDITED' else r['role'],
                                     'signals': f"score={score}; {r['top_fields'] or ''}"[:300], 'source': 'scored-links',
                                     'reason': 'scored-review'})
            cand_pairs.add((k, w))
            n += 1
            ncand += 1
    R['review|candidates_added'] = ncand
    for name in ('AUTHORED', 'EDITED'):
        linked[name] += add[name]
        R[f'added|{name}'] = len(add[name])
    report['scored_links'] = dict(sorted(R.items()))


def classified_layer(read_rows, path, person1, resolve, rels, linked, report, ra=None):
    """Pass eight (2026-11-12): the link classifier's certified links (data/graph/scored-links/classified.csv.gz,
    scripts/score_links.py classifier; final model the calibrated Fellegi-Sunter rule). Only rows with load = True are
    read: 1,424 reviewer positions with several candidates (0 wrong of 685 on the gold test). Each becomes a linked
    AUTHORED row, source `classified-links`, state `classified`, `score` = the classifier's probability. Skipped and
    counted: pairs already credited (key log or any linked loader), positions whose work or key does not resolve, and
    the reviewed-author check (scripts/reviewed_authors.py: a person credited on the reviewed book, or bearing a printed
    reviewed-author name, is never the review's reviewer). No other row of the file is loaded."""
    R = Counter()
    have = {(r['from'], r['to']) for r in rels['AUTHORED']} | {(r['from'], r['to']) for r in rels['EDITED']}
    have |= {(r['from'], r['to']) for r in linked['AUTHORED']} | {(r['from'], r['to']) for r in linked['EDITED']}
    add = []
    for r in read_rows(path):
        if str(r.get('load')).lower() != 'true':
            continue
        R['rows_load_true'] += 1
        role = r['role']
        if role != 'reviewer':
            R[f'skipped_role|{role}'] += 1
            continue
        w, k = resolve(r['work']), person1(r['person_key'])
        if not w or not k:
            R['unresolved'] += 1
            continue
        if (k, w) in have:
            R['pair_already_credited'] += 1
            continue
        if ra is not None:
            why = ra.why(k, w)
            if why:
                R[f'reviewed_author_refused|{why}'] += 1
                continue
        p = float(r['probability']) if r.get('probability') else None
        add.append({'from': k, 'to': w, 'claim': f"classified-links:{role}:{r['position']}", 'resolution': 'linked',
                    'source': 'classified-links', 'state': 'classified', 'score': p, 'role': 'author',
                    'role_basis': f"classified-links:{r.get('stratum') or ''}:{r.get('model') or ''}"[:200]})
        have.add((k, w))
    linked['AUTHORED'] += add
    R['added|AUTHORED'] = len(add)
    report['classified_links'] = dict(sorted(R.items()))


RULE_SOURCES = ('work-people:', 'name-only:', 'scored-links')


def _pos_keys(r):
    """position keys of a rule/scorer row from its claim: ('wp', work, role, pos) for work-people:<role>:<pos>,
    ('no', work, source, pos) for name-only:<source>:<pos>; scored-links:<source>:<role>:<pos> gets both (a work's
    printed list is either a work-people or a name-only list)"""
    c = r.get('claim') or ''
    if '@' in c:
        return []
    p = c.split(':')
    if c.startswith('work-people:') and len(p) == 3:
        return [('wp', r['to'], p[1], p[2])]
    if c.startswith('name-only:') and len(p) == 3:
        return [('no', r['to'], p[1], p[2])]
    if c.startswith('scored-links:') and len(p) == 4:
        return [('wp', r['to'], p[2], p[3]), ('no', r['to'], p[1], p[3])]
    return []


def model_layer(read_rows, clf_path, qwen_path, qpos_path, person1, resolve, wi, review_works, rels, linked,
                possible_authors, report, ra=None, conflicts_path=None):
    """2026-11-13: the retrained link classifier's links and Qwen's direct verdicts, evidence linked (never the key log).

    Classifier (data/graph/scored-links/classified.csv.gz, train_link_classifier.py finalize): every decision = link row
    (all roles; replaces pass eight's load = True reviewer subset) becomes a linked AUTHORED row, source
    `classified-links`, state `classified`, score = probability. Qwen (qwen-labels.csv.gz, Qwen3.8-27B, prompt qll-v1,
    policy greedy+sc, no linkage facts; positions placed by qwen-positions.csv.gz): a 'key' verdict becomes a linked
    AUTHORED row, source `qwen-links`, state `qwen`.
    Per position (work, role, list position; the rule linker's row found by its claim):
    - Qwen names a key and a rule/scorer row or the classifier names another key: neither is linked; the rule rows and
      both keys become author_candidates (reason 'qwen-conflict'); listed in conflicts_path;
    - Qwen 'not-keyed': the rule/scorer rows of the position (state linked or scored; identifier links, state exact,
      are kept and counted) return to author_candidates (reason 'qwen-not-keyed'), and a classifier link there is not
      loaded (also a candidate);
    - the classifier names a key another rule/scorer row holds at the position (Qwen silent): not loaded, counted;
    - a pair the key log or any earlier loader credits is not loaded again (counted as already linked, by source);
    - a Qwen position whose key or rule key the key log credits on the work is skipped (the key log credits someone);
    - the reviewed-author check (scripts/reviewed_authors.py) and, for author roles on a work that reads as a review
      whose reviewed authors are unknown, an exclusion, as for the scorer's links.
    'cannot-tell' and 'error' verdicts do nothing. Keys resolve through merges (person1 follows replaced_by)."""
    import csv
    R = Counter()
    keylog = {(r['from'], r['to']) for r in rels['AUTHORED']} | {(r['from'], r['to']) for r in rels['EDITED']}
    credited = keylog | {(r['from'], r['to']) for r in linked['AUTHORED']} | {(r['from'], r['to']) for r in linked['EDITED']}
    idx = defaultdict(list)
    for r in linked['AUTHORED']:
        if (r.get('source') or '').startswith(RULE_SOURCES):
            for pk in _pos_keys(r):
                idx[pk].append(r)

    def is_review(w):
        x = wi.get(w) or {}
        return (w in review_works or x.get('kind') == 'review' or x.get('kind_proposed') == 'review'
                or bool(REVIEW_TITLE.search(x.get('label') or '')) or (ra is not None and ra.is_review(w)))

    def blocked(k, w, role):
        if ra is not None:
            why = ra.why(k, w)
            if why:
                return f'reviewed_author_refused|{why}'
        if role in AUTHOR_ROLES and is_review(w) and (ra is None or not ra.known(w)):
            return 'author_role_on_review_reviewed_author_unknown'
        return None

    def pkey(tbl, w, role, src, pos):
        return ('wp', w, role, str(pos)) if tbl == 'wp' else ('no', w, src, str(pos))

    # Qwen verdicts
    qp = {int(r['position']): r for r in read_rows(qpos_path)} if qpos_path.exists() else {}
    Q = {}
    for r in read_rows(qwen_path):
        pid = int(r['position'])
        p = qp.get(pid)
        d = r['decision']
        R[f"qwen_read|{'key' if d.startswith('p-') else d}"] += 1
        w = resolve(r['work'])
        if not p or not p.get('pos') or not w:
            R['qwen|position_or_work_unresolved'] += 1
            continue
        k = person1(d) if d.startswith('p-') else None
        if d.startswith('p-') and not k:
            R['qwen|key_unresolved'] += 1
            continue
        Q[pid] = dict(d=d, k=k, w=w, role=r['role'], pk=pkey(p['tbl'], w, r['role'], p['list_source'], p['pos']),
                      rk=person1(r['rule_key']) if r.get('rule_key') else None, votes=r.get('votes') or '',
                      conf=r.get('confidence') or '', reason=(r.get('reason') or '')[:200],
                      dups={k2 for x in (r.get('duplicate_keys') or '').split('|') if x and (k2 := person1(x))})
    # classifier links
    C = {}
    for r in read_rows(clf_path):
        if r['decision'] != 'link':
            continue
        R['clf_read|link'] += 1
        w, k = resolve(r['work']), person1(r['person_key'])
        if not w or not k:
            R['clf|unresolved'] += 1
            continue
        C[int(r['position'])] = dict(k=k, w=w, role=r['role'], pk=pkey(r.get('tbl'), w, r['role'], r.get('list_source'), r['pos']),
                                     p=float(r['probability']) if r.get('probability') else None,
                                     basis=f"classified-links:{r.get('stratum') or ''}:{r.get('model') or ''}"[:200])
    demote = {}                        # id(row) -> (row, reason)
    cands = []
    conflicts = []

    def cand(k, w, role, src, why, sig):
        cands.append({'from': k, 'to': w, 'n_candidates': 1, 'signals': sig[:300], 'source': src, 'role': role, 'reason': why})

    # Qwen pass first: it decides conflicts and demotions
    clf_skip = {}
    add_q = []
    for pid, q in Q.items():
        rows = idx.get(q['pk'], [])
        rkeys = {x['from'] for x in rows}
        c = C.get(pid)
        sig = f"Qwen {q['d']} ({q['votes']}, {q['conf']}): {q['reason']}"
        if q['d'] == 'not-keyed':
            if c:
                clf_skip[pid] = 'qwen_not_keyed'
            for x in rows:
                if x.get('state') == 'exact':
                    R['qwen_not_keyed|rule_row_exact_kept'] += 1
                    continue
                demote[id(x)] = (x, 'qwen-not-keyed', sig)
            if not rows:
                R['qwen_not_keyed|no_rule_row'] += 1
            continue
        if not q['k']:
            continue                   # cannot-tell / error
        k, w = q['k'], q['w']
        if (k, w) in keylog or (q['rk'] and (q['rk'], w) in keylog):
            R['qwen_key|keylog_credits_position'] += 1
            if c:
                clf_skip.setdefault(pid, 'keylog_credits_position')
            continue
        other_rule = rkeys - {k}
        if other_rule and other_rule <= q['dups']:     # Qwen named the rule's key as a duplicate of its own: agreement
            R['qwen_key|rule_key_is_qwen_named_duplicate'] += 1
            if c:
                clf_skip.setdefault(pid, 'rule_key_is_qwen_named_duplicate')
            continue
        other_clf = c['k'] if c and c['k'] != k else None
        if other_rule or other_clf:
            R['qwen_key|conflict|' + ('rule' if other_rule else '') + ('+' if other_rule and other_clf else '') + ('classifier' if other_clf else '')] += 1
            for x in rows:
                if x.get('state') == 'exact':
                    R['qwen_key|conflict|rule_row_exact_kept'] += 1
                    continue
                demote[id(x)] = (x, 'qwen-conflict', sig)
            if c:
                clf_skip[pid] = 'conflict_with_qwen'
                if other_clf:
                    cand(other_clf, w, c['role'], 'classified-links', 'qwen-conflict', f"classifier p={c['p']}; {sig}")
            cand(k, w, q['role'], 'qwen-links', 'qwen-conflict', sig)
            conflicts.append(dict(position=pid, work=w, role=q['role'], qwen_key=k, rule_keys=';'.join(sorted(rkeys)),
                                  rule_sources=';'.join(sorted({x.get('source') or '' for x in rows})),
                                  classifier_key=c['k'] if c else '', qwen_votes=q['votes'], qwen_reason=q['reason']))
            continue
        if k in rkeys:
            R['qwen_key|already_linked|' + next(x.get('source') for x in rows if x['from'] == k)] += 1
            continue
        if (k, w) in credited:
            R['qwen_key|pair_already_credited'] += 1
            continue
        b = blocked(k, w, q['role'])
        if b:
            R[f'qwen_key|{b}'] += 1
            if c:
                clf_skip.setdefault(pid, b)
            continue
        if c and c['k'] == k:
            R['qwen_key|classifier_agrees'] += 1
        add_q.append({'from': k, 'to': w, 'claim': f"qwen-links:{q['role']}:{q['pk'][3]}:{pid}", 'resolution': 'linked',
                      'source': 'qwen-links', 'state': 'qwen', 'score': None, 'role': 'author',
                      'role_basis': f"Qwen clerical read, prompt qll-v1 (greedy+sc, votes {q['votes']}, {q['conf']})"})
        credited.add((k, w))
        if c and c['k'] == k:
            clf_skip[pid] = 'qwen_links_same_key'
    R['added|qwen-links'] = len(add_q)
    # classifier pass
    add_c = []
    for pid, c in C.items():
        k, w = c['k'], c['w']
        rows = idx.get(c['pk'], [])
        rkeys = {x['from'] for x in rows}
        if pid in clf_skip:
            R[f"clf|{clf_skip[pid]}"] += 1
            if clf_skip[pid] == 'qwen_not_keyed':
                cand(k, w, c['role'], 'classified-links', 'qwen-not-keyed', f"classifier p={c['p']}; Qwen not-keyed")
            continue
        if k in rkeys:
            R['clf|already_linked|' + next(x.get('source') for x in rows if x['from'] == k)] += 1
            continue
        if rkeys:
            R['clf|rule_names_another_key'] += 1
            continue
        if (k, w) in keylog:
            R['clf|pair_in_keylog'] += 1
            continue
        if (k, w) in credited:
            R['clf|pair_already_credited'] += 1
            continue
        b = blocked(k, w, c['role'])
        if b:
            R[f'clf|{b}'] += 1
            continue
        add_c.append({'from': k, 'to': w, 'claim': f"classified-links:{c['role']}:{c['pk'][3]}:{pid}", 'resolution': 'linked',
                      'source': 'classified-links', 'state': 'classified', 'score': c['p'], 'role': 'author',
                      'role_basis': c['basis']})
        credited.add((k, w))
    R['added|classified-links'] = len(add_c)
    # demotions: the rule rows leave the credits and join the candidates. BUILD_QWEN_DEMOTE_OFF=1 keeps them (counted):
    # a hand check of 20 not-keyed demotions (2026-11-13) found about half of Qwen's not-keyed verdicts wrong (an
    # affiliation from another career stage read as a mismatch)
    import os
    if os.environ.get('BUILD_QWEN_DEMOTE_OFF'):
        R['demotions_switched_off'] = len(demote)
        demote = {}
    for x, why, sig in demote.values():
        cand(x['from'], x['to'], 'author', x.get('source'), why, f"linked credit ({x.get('source')}) returned to the candidates: {sig}")
        R[f"demoted|{why}|{x.get('source')}"] += 1
    gone = set(demote)
    linked['AUTHORED'] = [x for x in linked['AUTHORED'] if id(x) not in gone] + add_q + add_c
    R['demoted'] = len(gone)
    have_c = {(r['from'], r['to']) for r in possible_authors}
    n = 0
    for x in cands:
        if (x['from'], x['to']) not in have_c:
            possible_authors.append(x)
            have_c.add((x['from'], x['to']))
            n += 1
    R['candidates_added'] = n
    R['conflicts'] = len(conflicts)
    if conflicts_path is not None:
        with open(conflicts_path, 'w', newline='', encoding='utf-8') as fh:
            wr = csv.DictWriter(fh, fieldnames=['position', 'work', 'role', 'qwen_key', 'rule_keys', 'rule_sources',
                                                'classifier_key', 'qwen_votes', 'qwen_reason'])
            wr.writeheader()
            wr.writerows(conflicts)
    report['model_links'] = dict(sorted(R.items()))
