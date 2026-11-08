"""Dedup priority: probable duplicate person keys ranked by the citations stranded on the smaller keys (2026-11-08).

User, 2026-11-08: "the more citations on both sides of splits the more important it is we get it right; we can't have
4 foucaults in the knowledge graph; if there are 2 citations and 3 citations then the merge is lower priority".

Read-only, from build/graph:
- citations per person key: distinct citing theses and distinct citing articles that cite any work the key authored
  (authored x cites; distinct items, not edges);
- candidate groups: keys whose labels share the folded family name (last word, as jstor_match_candidates.family) and
  have compatible given names: each given-name token, in order, equals the other or is its initial; keys with no
  given name are left out;
- groups never join keys with different wd, lcnaf or orcid values (different people, already identified);
  `pid_conflict` marks groups whose keys differ only on viaf or gnd (VIAF and GND have duplicate clusters);
- full-name keys group only with the same first given name; an initials-only key ('Taylor, A.') joins a group only
  when exactly one full-name group fits it; otherwise it goes to the ambiguous-initials table
  (dedup-priority-2026-11-08-ambiguous-initials.parquet), ranked by its own citations. `initials_attached` marks keys
  attached by elimination ('Graham, A. J.' to the only A. Graham with a full name): a lead, not a match.

Priority of a group is `stranded`: total citing items minus those of its largest key; `second` is the second-largest
key's count. A 2-vs-3 split has stranded 2; four keys of a much-cited name have thousands.

Output (E:, not committed): /mnt/e/kg-review/dedup-priority-2026-11-08.parquet, one row per group:
group, family, keys, labels, theses, articles (lists aligned with keys), total, largest, second, stranded, n_keys,
pid_conflict, pids. Counts and the top of the list on stdout.

    python3 dedup_priority.py
"""
import os, re, sys, unicodedata
from collections import defaultdict

import duckdb

G = '/home/jic823/historiography/build/graph'
OUT = '/mnt/e/kg-review/dedup-priority-2026-11-08.parquet'
PIDS = ('wd', 'lcnaf', 'orcid', 'viaf', 'gnd')


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def parse(label):
    """-> (family, [given tokens]) from 'Family, Given' or 'Given Family'. A hyphenated family name stays whole
    ('Sherwin-White'); a bracketed full form of the given names replaces the initials ('Hall, A. Rupert (Alfred
    Rupert)' -> alfred rupert)."""
    label = re.sub(r',?\s+(?:jr|sr|ii|iii|iv)\.?$', '', fold(label).strip())
    m = re.search(r'\(([a-z][a-z .-]+)\)', label)
    full = m.group(1) if m and not re.search(r'\d', m.group(1)) else None
    label = re.sub(r'\(.*?\)', ' ', label)
    label = re.sub(r',\s*\d{4}-?(\d{4})?\.?$', '', label.strip())
    if ',' in label:
        fam, giv = label.split(',', 1)
    else:
        parts = label.split()
        if len(parts) < 2:
            return None, []
        fam, giv = parts[-1], ' '.join(parts[:-1])
    if full:
        giv = full
    fam = re.sub(r'[^a-z-]', ' ', fam).split()
    giv = [t for t in re.split(r'[^a-z]+', giv) if t]
    return (fam[-1].strip('-') if fam else None), giv


def compatible(a, b):
    if not a or not b:
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if len(x) == 1 and y.startswith(x) or len(y) == 1 and x.startswith(y):
            continue
        return False
    return True


def main():
    db = duckdb.connect(); db.execute("SET memory_limit = '5GB'")
    cnt = {k: (t, a) for k, t, a in db.execute(f"""
        select au."from", count(distinct c."from") filter (where w.kind = 'thesis'),
               count(distinct c."from") filter (where w.kind = 'article')
        from '{G}/authored.parquet' au join '{G}/cites.parquet' c on c."to" = au."to"
        join '{G}/work.parquet' w on w.key = c."from" group by 1""").fetchall()}
    people = db.execute(f"select key, label, wd, lcnaf, orcid, viaf, gnd from '{G}/person.parquet'").fetchall()
    print('person keys', len(people), 'cited keys', len(cnt), flush=True)
    block = defaultdict(list)
    info = {}
    for key, label, *pids in people:
        fam, giv = parse(label)
        if not fam or not giv or len(fam) < 2:
            continue
        info[key] = (label, giv, dict(zip(PIDS, pids)))
        block[(fam, giv[0][0])].append(key)
    STRONG = ('wd', 'lcnaf', 'orcid')
    def clash(a, b):
        return any(info[a][2][p] and info[b][2][p] and info[a][2][p] != info[b][2][p] for p in STRONG)
    rows = []; amb = []; attached = set()
    for (fam, ini), keys in block.items():
        keys = [k for k in keys if sum(cnt.get(k, (0, 0))) > 0]
        if len(keys) < 2:
            continue
        full = [k for k in keys if len(info[k][1][0]) > 1]
        inits = [k for k in keys if len(info[k][1][0]) == 1]
        # full-name groups: same first given name, compatible rest, no clash on a strong identifier
        groups = []
        for k in sorted(full, key=lambda k: -sum(cnt[k])):
            for g in groups:
                if info[g[0]][1][0] == info[k][1][0] and all(compatible(info[x][1], info[k][1]) and not clash(x, k) for x in g):
                    g.append(k); break
            else:
                groups.append([k])
        # an initials-only key joins the one full-name group it fits; with several fits it is ambiguous
        for k in inits:
            fits = [g for g in groups if all(compatible(info[x][1], info[k][1]) and not clash(x, k) for x in g)]
            if len(fits) == 1:
                fits[0].append(k); attached.add(k)
            elif len(fits) > 1:
                amb.append((fam, k, info[k][0], cnt[k][0], cnt[k][1], [g[0] for g in fits], [info[g[0]][0] for g in fits]))
        for ks in groups:
            if len(ks) < 2:
                continue
            ks.sort(key=lambda k: -sum(cnt[k]))
            tot = [sum(cnt[k]) for k in ks]
            conflict = any(len({info[k][2][p] for k in ks if info[k][2][p]}) > 1 for p in ('viaf', 'gnd'))
            pids = [';'.join(f'{p}:{v}' for p, v in info[k][2].items() if v) for k in ks]
            rows.append((fam, ks, [info[k][0] for k in ks], [cnt[k][0] for k in ks], [cnt[k][1] for k in ks],
                         sum(tot), tot[0], tot[1], sum(tot) - tot[0], len(ks), conflict, pids,
                         [k in attached for k in ks]))
    rows.sort(key=lambda r: -r[8])
    db.execute("""create table g (grp int, family varchar, keys varchar[], labels varchar[], theses int[], articles int[],
                  total int, largest int, second int, stranded int, n_keys int, pid_conflict boolean, pids varchar[],
                  initials_attached boolean[])""")
    db.executemany("insert into g values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [(i,) + r for i, r in enumerate(rows)])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    db.execute(f"copy g to '{OUT}.tmp' (format parquet)"); os.replace(OUT + '.tmp', OUT)
    print(db.execute("""select pid_conflict, count(*) n_groups, sum(n_keys) n_keys_total, sum(stranded) stranded_total,
                        count(*) filter (where stranded >= 100) s100, count(*) filter (where stranded >= 20) s20,
                        count(*) filter (where stranded >= 5) s5 from g group by 1""").fetchdf().to_string())
    print(db.execute("""select labels[1:4] labels, theses[1:4] th, articles[1:4] ar, stranded from g
                        order by stranded desc limit 40""").fetchdf().to_string())
    db.execute("create table a (family varchar, key varchar, label varchar, theses int, articles int, fits varchar[], fit_labels varchar[])")
    db.executemany("insert into a values (?,?,?,?,?,?,?)", amb)
    A = OUT.replace('.parquet', '-ambiguous-initials.parquet')
    db.execute(f"copy (select * from a order by theses + articles desc) to '{A}.tmp' (format parquet)"); os.replace(A + '.tmp', A)
    print('ambiguous initials-only keys', len(amb), 'citing items', sum(x[3] + x[4] for x in amb))
    print(db.execute("select label, theses, articles, len(fits) n_fits, fit_labels[1:3] from a order by theses + articles desc limit 12").fetchdf().to_string())


if __name__ == '__main__':
    main()
