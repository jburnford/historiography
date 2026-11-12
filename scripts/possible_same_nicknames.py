"""Possible-same candidates that differ only by a nickname of the first given name (2026-11-12, integration pass five;
ARCHITECTURE.md section 8, class 32). Probe: 'Katie Magee Labelle' (p-179250, one 2011 review) and 'Kathryn Magee
Labelle' (p-53033) were not flagged: scripts/key_possible_same.py groups keys by family name and the first given name
as written, so a nickname ('Katie', 'Bill', 'Steve') never meets the formal name.

The same tests as key_possible_same.py, except that the first given names are different and agree through the
standard nickname table (scripts/nicknames.py nickname_agree):
- same family name; further given names agree (initials compared) where both have them; the canonical name is on at
  most three live keys;
- no identifier scheme (LC, Wikidata, ORCID, VIAF, GND, ISNI, IdRef) on both;
- not already a POSSIBLY_SAME pair, and no `not-same:` mark between them;
- both have dated key-log works (scripts/graph_tables.keylog), and their timelines fit: when life years are known
  (data/person-facts/life-years.csv.gz) every work falls between birth + 18 and death + 10; the two keys' works
  together span no more than fifty years.
Candidates only: a review file, never a key-log proposal, never a merge, and the nickname table is not used by any
linker's refusal of disagreeing names.

    python3 scripts/possible_same_nicknames.py     # reads build/graph and the key-log cache
Writes data/identifiers/possible-same-nicknames-2026-11-12/pairs.csv and report.json.
"""
import csv
import gzip
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_tables import keylog  # noqa: E402
from key_split_dissertation_works import parse, PID  # noqa: E402
from nicknames import nickname_agree, canon  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
CACHE = ROOT / 'build/keylog-state.sqlite'
OUT = ROOT / 'data/identifiers/possible-same-nicknames-2026-11-12'
CAREER = 50


def middle_agree(ga, gb):
    a, b = ga[1:], gb[1:]
    return not (a and b) or a[0][0] == b[0][0]


def main():
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3")
    people = db.execute(f"SELECT key, label, anchors FROM '{G}/person.parquet'").fetchall()
    years = defaultdict(list)
    for k, y in db.execute(f"""SELECT a."from", w.year FROM {keylog(G, 'authored')} a JOIN '{G}/work.parquet' w ON w.key = a."to"
                               WHERE w.year IS NOT NULL""").fetchall():
        years[k].append(y)
    have = {tuple(sorted(p)) for p in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/possibly_same.parquet'").fetchall()}
    kl = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    notsame = set()
    for k, m in kl.execute("SELECT key, member FROM members WHERE member LIKE 'not-same:%'"):
        notsame.add(tuple(sorted((k, m.split(':', 1)[1]))))
    life = {}
    with gzip.open(ROOT / 'data/person-facts/life-years.csv.gz', 'rt', newline='') as f:
        for r in csv.DictReader(f):
            life[r['key']] = (int(r['birth']) if r['birth'] else None, int(r['death']) if r['death'] else None)
    label, schemes = {}, {}
    by = defaultdict(list)                  # (family, one canonical form) -> keys
    for k, lab, anchors in people:
        p = parse(lab)
        if not p:
            continue
        label[k] = lab
        schemes[k] = {a.split(':', 1)[0] for a in anchors or []} & set(PID)
        fam, giv = p
        for c in canon(giv[0]):
            by[(fam, c)].append((k, giv))
    rep = Counter()
    seen, rows = set(), []

    def fits(k, ys):
        b, d = life.get(k, (None, None))
        return all((b is None or y >= b + 18) and (d is None or y <= d + 10) for y in ys)
    for (fam, c), ks in by.items():
        if len({k for k, _ in ks}) > 3:
            rep['canonical_name_on_4_or_more_keys'] += 1
            continue
        for i, (a, ga) in enumerate(ks):
            for b, gb in ks[i + 1:]:
                pair = tuple(sorted((a, b)))
                if a == b or pair in seen:
                    continue
                seen.add(pair)
                if not nickname_agree(ga[0], gb[0]):
                    continue                      # equal first names are key_possible_same.py's
                rep['nickname_pairs'] += 1
                if not middle_agree(ga, gb):
                    rep['middle_initials_differ'] += 1; continue
                if schemes[a] & schemes[b]:
                    rep['identifier_on_both'] += 1; continue
                if pair in have:
                    rep['already_possibly_same'] += 1; continue
                if pair in notsame:
                    rep['not_same_recorded'] += 1; continue
                if not years.get(a) or not years.get(b):
                    rep['undated_side'] += 1; continue
                ys = years[a] + years[b]
                if not (fits(a, ys) and fits(b, ys)):
                    rep['timelines_clash'] += 1; continue
                if max(ys) - min(ys) > CAREER:
                    rep['joint_span_over_a_career'] += 1; continue
                rep['candidate_pairs'] += 1
                rows.append(dict(a=pair[0], b=pair[1], label_a=label[pair[0]], label_b=label[pair[1]],
                                 works_a=f'{min(years[pair[0]])}-{max(years[pair[0]])} ({len(years[pair[0]])})',
                                 works_b=f'{min(years[pair[1]])}-{max(years[pair[1]])} ({len(years[pair[1]])})',
                                 schemes_a=';'.join(sorted(schemes[pair[0]])), schemes_b=';'.join(sorted(schemes[pair[1]])),
                                 basis=f'nickname: {ga[0]} / {gb[0]} ({fam})', verdict=''))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / 'pairs.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['a', 'b'])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r['label_a'], r['label_b'])))
    (OUT / 'report.json').write_text(json.dumps(dict(
        date='2026-11-12', note=('candidates for review only (no key-log proposal): first given names differ but agree through '
                                 'scripts/nicknames.py; other tests as key_possible_same.py with life years and a 50-year joint span'),
        counts=dict(sorted(rep.items()))), indent=1) + '\n')
    print(json.dumps(dict(sorted(rep.items())), indent=1))


if __name__ == '__main__':
    main()
