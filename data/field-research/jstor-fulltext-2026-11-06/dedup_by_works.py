"""Dedup by works: person keys that share a work title, ranked by citations stranded on the smaller key (2026-11-08).

User, 2026-11-08: "we have the book or journal article titles; can't we use them to merge?" This is the identity-by-
works rule: two keys whose works have the same title are the same person unless they are co-authors.

Read-only, from build/graph (authored, work, person, cites):
- a title is the work label's main-title key (jstor_match_candidates.cited_key), usable only when at least 10
  characters and 2 words;
- a pair of person keys shares a title when they authored works with that title key whose years are both missing or
  within 3 of each other;
- two keys listed on one and the same work key are co-authors, unless their names agree (same family name and
  compatible given names, or a surname variant): then the joint listing is a duplicate attribution ('Davis, Angela'
  and 'Davis, Angela Y.' both on Women, race, & class). Other pairs whose only shared titles are joint works are
  dropped as co-authors;
- titles of reviews ('Review of …', '[Reseña]', 'Compte rendu') are skipped: every reviewer of a book shares them;
- a name check classes every pair (`surname_variant`: the family names differ but one appears in the other name,
  e.g. 'Necochea' / 'Necochea López', 'Pérez-Mallaina' / 'Pérez-Mallaína Bueno'): `same_family` (same folded family name, compatible given names: a duplicate
  candidate), `same_family_given_clash` (same family, given names disagree: e.g. a translator, editor or a
  namesake, review), `other_family` (different family names: married name, transliteration, pen name, or a
  misattributed work, review);
- `pid_clash`: the two keys carry different wd, lcnaf or orcid values (already identified as different people;
  usually a misattributed work).

Citations: distinct citing theses + distinct citing JSTOR articles per key; `stranded` = the smaller key's count.

Output (E:, not committed): /mnt/e/kg-review/dedup-by-works-2026-11-08.parquet, one row per pair:
a, b, label_a, label_b, name_class, pid_clash, shared_titles, examples, cites_a, cites_b, stranded.

    python3 dedup_by_works.py
"""
import os, re, sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jstor_match_candidates as M  # noqa: E402
from dedup_priority import parse, compatible  # noqa: E402

G = '/home/jic823/historiography/build/graph'
OUT = '/mnt/e/kg-review/dedup-by-works-2026-11-08.parquet'
REVIEW_TITLE = re.compile(r'^\s*\[?(review of|reviewed work|compte rendu|rese(ñ|n)a)\b|\[rese(ñ|n)a\]|\breview\]', re.I)


def main():
    db = duckdb.connect(); db.execute("SET memory_limit = '4GB'")
    cnt = dict(db.execute(f"""select au."from", count(distinct c."from") from '{G}/authored.parquet' au
        join '{G}/cites.parquet' c on c."to" = au."to" group by 1""").fetchall())
    people = {k: (l, wd, lc, oc) for k, l, wd, lc, oc in db.execute(f"select key, label, wd, lcnaf, orcid from '{G}/person.parquet'").fetchall()}
    rows = db.execute(f"""select au."from", au."to", w.label, w.year from '{G}/authored.parquet' au
        join '{G}/work.parquet' w on w.key = au."to" where w.kind <> 'review'""").fetchall()
    print('authored rows', len(rows), flush=True)
    by_title = defaultdict(list)      # title key -> [(person, work, year)]
    work_people = defaultdict(set)
    for p, w, label, y in rows:
        work_people[w].add(p)
        if REVIEW_TITLE.search(label or ''):
            continue          # 'Review of X': every reviewer of X shares it
        tk = M.cited_key(label or '')
        if M.usable(tk):
            by_title[tk].append((p, w, y, label))
    pairs = defaultdict(lambda: {'titles': set(), 'ex': []})
    for tk, items in by_title.items():
        persons = {p for p, *_ in items}
        if len(persons) < 2 or len(persons) > 12:     # a very common title ('Introduction to …') proves nothing
            continue
        byp = defaultdict(list)
        for p, w, y, label in items:
            byp[p].append((w, y, label))
        for a, b in combinations(sorted(byp), 2):
            ok = joint_only = False
            for wa, ya, la in byp[a]:
                for wb, yb, lb in byp[b]:
                    if ya and yb and abs(ya - yb) > 3:
                        continue
                    if wa == wb and {a, b} <= work_people[wa]:
                        if not ok:
                            joint_only = True; ok = True; ex = la   # on one work together: co-authors or a duplicate
                        continue
                    ok = True; joint_only = False; ex = la
            if ok:
                d = pairs[(a, b)]; d['titles'].add(tk)
                d['joint'] = d.get('joint', True) and joint_only
                if len(d['ex']) < 3:
                    d['ex'].append(ex[:120])
    out = []
    for (a, b), d in pairs.items():
        la, lb = people.get(a, ('',))[0], people.get(b, ('',))[0]
        fa, ga = parse(la); fb, gb = parse(lb)
        if fa and fa == fb:
            cls = 'same_family' if (compatible(ga, gb) or not ga or not gb) else 'same_family_given_clash'
        elif fa and fb and (fa in re.split(r'[^a-z]+', M.fold(lb) if hasattr(M, 'fold') else lb.lower()) or
                            fb in re.split(r'[^a-z]+', M.fold(la) if hasattr(M, 'fold') else la.lower()) or
                            fa.split('-')[0] == fb.split('-')[0]):
            cls = 'surname_variant'
        else:
            cls = 'other_family'
        clash = any(people.get(a, (None,) * 4)[i] and people.get(b, (None,) * 4)[i] and people[a][i] != people[b][i] for i in (1, 2, 3))
        if d.get('joint') and cls not in ('same_family', 'surname_variant'):
            continue          # listed together on the same works under different names: co-authors
        ca, cb = cnt.get(a, 0), cnt.get(b, 0)
        if cb > ca:
            a, b, la, lb, ca, cb = b, a, lb, la, cb, ca
        out.append((a, b, la, lb, cls, clash, len(d['titles']), d['ex'], ca, cb, cb))
    db.execute("""create table t (a varchar, b varchar, label_a varchar, label_b varchar, name_class varchar, pid_clash boolean,
                  shared_titles int, examples varchar[], cites_a int, cites_b int, stranded int)""")
    db.executemany("insert into t values (?,?,?,?,?,?,?,?,?,?,?)", out)
    db.execute(f"copy (select * from t order by stranded desc) to '{OUT}.tmp' (format parquet)"); os.replace(OUT + '.tmp', OUT)
    print(db.execute("""select name_class, pid_clash, count(*) n_pairs, sum(stranded) stranded_total,
                        count(*) filter (where stranded >= 20) s20, count(*) filter (where stranded >= 5) s5,
                        count(*) filter (where shared_titles >= 2) two_titles from t group by all order by 1, 2""").fetchdf().to_string())
    print(db.execute("""select label_a, label_b, cites_a, cites_b, shared_titles, examples[1] from t
                        where name_class = 'same_family' and not pid_clash order by stranded desc limit 20""").fetchdf().to_string())
    print(db.execute("""select label_a, label_b, cites_a, cites_b, shared_titles, examples[1] from t
                        where name_class = 'surname_variant' and not pid_clash order by stranded desc limit 15""").fetchdf().to_string())


if __name__ == '__main__':
    main()
