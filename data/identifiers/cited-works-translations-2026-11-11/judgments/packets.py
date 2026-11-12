"""Judgment packets: unmatched cited works whose title language differs from the author's LC language profile,
with the author's LC titles in other languages ranked by similarity. Writes packets/packet-NNN.tsv (100 rows each).
Usage: packets.py MIN_CITED"""
import sys
from collections import defaultdict
from pathlib import Path

import duckdb
from rapidfuzz import fuzz

S = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations')
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 5


def main():
    db = duckdb.connect(str(S / 'lc.duckdb'))
    db.execute("SET memory_limit='3GB'; SET threads=3")
    db.execute(f"ATTACH '{S}/t.duckdb' AS t (READ_ONLY)")
    db.execute(f"CREATE OR REPLACE TEMP TABLE c AS SELECT * FROM t.ucand WHERE n >= {MIN}")
    prof = defaultdict(dict)
    for ak, lang, n in db.execute("SELECT a.ak, lang, n FROM aprof a SEMI JOIN c ON c.ak = a.ak").fetchall():
        prof[ak][lang] = n
    titles = defaultdict(list)
    for ak, tk2, title, yr, lang, n in db.execute(
            """SELECT r.ak, tk2, arg_min(title, yr), min(yr), arg_min(lang, yr), count(*) FROM lcrec r SEMI JOIN c ON c.ak = r.ak
               WHERE tag = '100' GROUP BY r.ak, tk2""").fetchall():
        titles[ak].append((tk2, title, yr, lang, n))
    rows = db.execute("SELECT work_id, n, authors, title, yr, tlang, br, ca, gb, us, oth, ak FROM c ORDER BY n DESC, work_id").fetchall()
    out = []
    for wid, n, authors, title, yr, tlang, br, ca, gb, us, oth, ak in rows:
        p = prof.get(ak, {})
        tot = sum(p.values())
        top = max(p, key=p.get) if p else ''
        other = [x for x in titles.get(ak, []) if x[3] != tlang]
        other.sort(key=lambda x: -fuzz.token_set_ratio((title or "").lower(), (x[1] or "").lower()))
        cand = ' || '.join('%s (%s,%s)' % ((x[1] or '')[:70], x[2], x[3]) for x in other[:3])
        flag = 'X' if (tlang and top and top != tlang) else ('?' if not tlang or not top else '=')
        out.append((flag, wid, n, authors[:40] if authors else '', title[:90] if title else '', yr, tlang,
                    f'{top}:{p.get(top, 0)}/{tot}', max([('BR', br), ('CA', ca), ('GB', gb), ('US', us), ('oth', oth)], key=lambda x: x[1] or 0)[0], cand))
    (S / 'packets').mkdir(exist_ok=True)
    allp = S / 'packets' / f'all-min{MIN}.tsv'
    with open(allp, 'w') as f:
        for r in out:
            f.write('\t'.join('' if v is None else str(v) for v in r) + '\n')
    from collections import Counter
    print(Counter(r[0] for r in out), len(out))


if __name__ == '__main__':
    main()
