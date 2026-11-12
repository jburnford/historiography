"""Career windows for person keys (2026-11-07; user: "we need to use dates where ever possible to help with clean
matches"). The years in which a person can plausibly have published, reviewed or held a post, from the dates the
graph holds on the key:
- life years (data/person-facts/life-years.csv.gz: reviewed life dates, LC, Wikidata): from age 20, to two years
  after death (posthumous publication of reviews is rare; books are not judged here);
- the PhD year (AHA records on the key's `aha-phd:` anchors, and thesis works the key authored): from ten years
  before it, used only when no birth year is known (William Cronon reviewed in 1981, nine years before his 1990 Yale
  PhD; his birth year bounds him better).
A key whose birth year and PhD year contradict each other (PhD before 20 or after 75) gets no window and is listed in
INCONSISTENT: one of its identifiers is likely another person's ('Brody, David' holds a 1968-born LC authority).
A key with none of these has no window (None, None): routes then fall back to their own evidence. A window only
refuses; it never links.

    from career_window import career_windows, in_window
"""
import csv
import gzip
import json
from pathlib import Path

import duckdb
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
GRAPH = ROOT / 'build/graph'
BEFORE_PHD, ADULT, AFTER_DEATH = 10, 20, 2


def career_windows(state):
    """key -> (earliest, latest) active year; either end may be None."""
    aha = {}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        if r.get('year'):
            aha['aha-phd:' + r['id']] = int(r['year'])
    phd = {}
    for k, v in state.keys.items():
        if v['type'] == 'person' and v['status'] in ('active', 'provisional'):
            ys = [aha[a] for a in v['anchors'] if a in aha]
            if ys:
                phd[k] = min(ys)
    for k, y in duckdb.connect().execute(f"""SELECT a."from", min(w.year) FROM {keylog(GRAPH, 'authored')} a
            JOIN '{GRAPH}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'thesis' AND w.year IS NOT NULL GROUP BY 1""").fetchall():
        for c in state.lookup(k):
            phd[c] = min(phd.get(c, y), y)
    life = {}
    with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            b, d = (int(r['birth']) if r['birth'].lstrip('-').isdigit() else None,
                    int(r['death']) if r['death'].lstrip('-').isdigit() else None)
            for c in state.lookup(r['key']):
                life[c] = (b, d)
    out = {}
    global INCONSISTENT
    INCONSISTENT = {}
    for k in set(phd) | set(life):
        b, d = life.get(k, (None, None))
        p = phd.get(k)
        if b is not None and p is not None and not b + 20 <= p <= b + 75:
            INCONSISTENT[k] = (b, p)        # a birth year and a PhD year that cannot both be this person's: no window
            continue
        lo = b + ADULT if b is not None else (p - BEFORE_PHD if p is not None else None)
        out[k] = (lo, d + AFTER_DEATH if d is not None else None)
    return out


INCONSISTENT = {}     # key -> (birth, PhD year) that contradict each other; filled by career_windows()


def in_window(year, window):
    """True unless the year falls outside a known end of the window (unknown years and windows never refuse)."""
    if year is None or window is None:
        return True
    lo, hi = window
    return not ((lo is not None and year < lo) or (hi is not None and year > hi))
