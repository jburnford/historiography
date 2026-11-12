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
   a hand-read case (Becher);
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


def scored_layer(read_rows, path, person1, resolve, wi, review_works, rels, linked, possible_authors, report):
    """Adds rows to linked['AUTHORED'] / linked['EDITED'] and possible_authors in place."""
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
                or bool(REVIEW_TITLE.search(x.get('label') or '')))
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
        if r['role'] in AUTHOR_ROLES and is_review(w):
            R[f'link|{r["role"]}|work_reads_as_review_excluded'] += 1
            continue
        row = {'from': k, 'to': w, 'claim': f"scored-links:{r['source']}:{r['role']}:{r['position']}", 'resolution': 'linked',
               'source': 'scored-links', 'state': 'scored', 'score': float(r['score']) if r['score'] else None}
        if role:
            row['role'] = role
            row['role_basis'] = 'scored-links:volume-editors'
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
            if r['role'] in AUTHOR_ROLES and is_review(w):
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
