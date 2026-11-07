"""Compare the Qwen note parse (jstor_llm_notes.py answers) with the rule parse (jstor_notes.py) on the same articles.

Resolves the model's back-references (ibid / short / authordate) within each article in note order, then reports the
same outcome classes as the rule pilot, by era, and writes a side-by-side sheet of random pieces for hand audit
(local only: it quotes note text).

    python3 jstor_llm_eval.py REQUESTS.jsonl ANSWERS.jsonl SHEET.txt [N_SHEET]
"""
import json, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jstor_notes as J  # noqa: E402
from build_dissertation_citation_graph import fold, title_key  # noqa: E402

WORK_KINDS = ('book', 'article', 'chapter', 'thesis', 'periodical')


def surname(a):
    a = (a or '').strip()
    return a.split(',')[0].strip() if ',' in a else (a.split()[-1] if a.split() else '')


def resolve(cits):
    """cits in note order -> adds 'ref' (index) for back-references."""
    works, last = [], None
    for i, c in enumerate(cits):
        t = c.get('type')
        if t == 'ibid':
            c['ref'] = last
            continue
        surs = [fold(surname(a)) for a in c.get('authors') or [] if surname(a)]
        if t in ('short', 'authordate'):
            cands = [w for w in works if surs and cits[w]['_sur'] and cits[w]['_sur'][0] == surs[0]]
            if t == 'authordate':
                cands = [w for w in cands if cits[w].get('year') == c.get('year')]
            elif c.get('title'):
                tk = title_key(J.SHORT_TAIL.sub('', c['title']))
                words = set(re.findall(r'[^\W\d_]{4,}', fold(c['title'])))
                cands = [w for w in cands if (title_key(cits[w].get('title') or '').startswith(tk[:25]) or
                                             (words and words <= set(re.findall(r'[^\W\d_]{4,}', fold(cits[w].get('title') or '')))))] or \
                        ([] if len(tk) >= 4 else cands)
            c['ref'] = cands[-1] if cands else None
            if c['ref'] is not None:
                last = c['ref']
            continue
        c['_sur'] = surs
        if t == 'work' and (c.get('title') or c.get('container')):
            works.append(i); last = i
        elif t == 'primary':
            last = i   # 'Ibid.' after an archival citation is that document
    return cits


def outcome(c):
    t = c.get('type')
    if t in ('ibid', 'short', 'authordate'):
        return 'backref_resolved' if c.get('ref') is not None else 'backref_unresolved'
    if t == 'primary' or c.get('kind') == 'primary':
        return 'primary'
    if t == 'work':
        full = bool(c.get('authors')) and bool(c.get('title') or c.get('container')) and bool(c.get('year'))
        return 'full' if full else 'partial'
    return 'other'


def rule_outcome(r):
    k = r['kind']
    if k == 'backref':
        return 'backref_resolved' if r.get('ref') is not None else 'backref_unresolved'
    if k in WORK_KINDS:
        full = bool(r.get('surnames')) and bool(r.get('title') or r.get('container')) and bool(r.get('year'))
        return 'full' if full else 'partial'
    return 'primary' if k in ('primary', 'archival') else 'other'


def main():
    reqs = [json.loads(l) for l in open(sys.argv[1])]
    ans = {a['id']: a for a in map(json.loads, open(sys.argv[2]))}
    sheet_n = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    arts = defaultdict(list)
    for r in reqs:
        arts[r['iid']].append(r)
    L, R = defaultdict(Counter), defaultdict(Counter)
    failed = 0; sheet = []
    for iid, rs in arts.items():
        rs.sort(key=lambda r: r['first'])
        era = rs[0]['era']
        pieces = [p for r in rs for p in r['pieces']]
        cits = []
        for r in rs:
            a = ans.get(r['id'])
            if not a or not a['ok']:
                failed += 1
                continue
            for c in a['citations']:
                if isinstance(c, dict):
                    cits.append(c)
        resolve(cits)
        for c in cits:
            L[era][outcome(c)] += 1; L['all'][outcome(c)] += 1
        rules = J.citations(pieces)
        for r in rules:
            R[era][rule_outcome(r)] += 1; R['all'][rule_outcome(r)] += 1
        for k, p in enumerate(pieces):
            sheet.append((rs[0]['journal'], rs[0]['year'], k, p,
                          [c for c in cits if c.get('p') == k], [r for r in rules if r['note'] == k]))
    print('requests failed:', failed)
    for era in ('all', 'pre1940', '1940-79', '1980+'):
        for name, C in (('rules', R), ('llm', L)):
            t = sum(C[era].values())
            print(f'{era:8} {name:5} {t:6}', {k: f'{v / t:.0%}' for k, v in sorted(C[era].items())})
    random.seed(5)
    with open(sys.argv[3], 'w') as f:
        for j, y, k, p, lc, rc in random.sample(sheet, min(sheet_n, len(sheet))):
            f.write(f'### {j} {y} [{k}]\nRAW: {p[:400]}\n')
            for c in lc:
                f.write(f"  LLM  {c.get('type')}/{c.get('kind')} ref={c.get('ref')} | {'; '.join(c.get('authors') or [])} | {c.get('title')} | "
                        f"{c.get('container')} | {c.get('place')} | {c.get('publisher')} | {c.get('year')}\n")
            for r in rc:
                f.write(f"  RULE {r['rule']}/{r['kind']} ref={r.get('ref')} | {'; '.join(r.get('authors') or [])} | {r.get('title')} | "
                        f"{r.get('container')} | {r.get('year')}\n")


if __name__ == '__main__':
    main()
