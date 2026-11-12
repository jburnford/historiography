"""Shared paths and helpers for the canon-paper analyses (2026-11-11). Read-only on every input.

The analyses read a disposable DuckDB file built by 00_base.py in a scratch folder (BASE). Outputs (counts and shares
only) go to out/ (PAPER_OUT overrides; out-2026-11-11-morning/ keeps the first run on build/graph-check). Run order: 00_base.py, then 01_... to 07_... in any order (07 reuses functions of the
others). Every script is runnable on its own once 00_base.py has run:  python3 0N_name.py
"""
import os
import time
from pathlib import Path

import duckdb

ROOT = Path('/home/jic823/historiography')
HERE = Path(__file__).resolve().parent
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
IDS = ROOT / 'data/identifiers'
CITED = ROOT / 'data/graph/cited-works'
FACTS = ROOT / 'data/person-facts'
# The morning run (out-2026-11-11-morning/) read build/graph-check; from the evening rerun the live build is read.
GRAPH = Path(os.environ.get('PAPER_GRAPH', ROOT / 'build/graph'))
KEYLOG_CACHE = ROOT / 'build/keylog-state.sqlite'     # read-only: retired work key -> successor (merges)
SCRATCH = Path(os.environ.get('PAPER_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/paper2'))
BASE = SCRATCH / 'base.duckdb'
OUT = Path(os.environ.get('PAPER_OUT', HERE / 'out'))

# Analysis switches (environment; defaults = the paper's base configuration):
#  PAPER_CREDITS = keylog (default: AUTHORED/EDITED claims of the key log only) | linked (add evidence='linked' credits)
#  PAPER_ROLLUP  = 1 (default: a thesis citing a translation or later edition cites the original work) | 0 (the node the
#                  edition was cited as; an edition that was unmatched before the roll-up stays unmatched)
CREDITS = os.environ.get('PAPER_CREDITS', 'keylog')
ROLLUP = os.environ.get('PAPER_ROLLUP', '1') == '1'
# parsed author keys whose forename is initials only ('smith|j', 'thompson|e') pool many people: dropped from the
# parsed-name routes (corpus person level and route B)
INITIAL_ONLY = r"regexp_matches(person_key, '\|[a-z](\s[a-z])*$')"

COUNTRIES = ['CA', 'US', 'GB', 'FR', 'BR', 'MX']
SMALL = 100          # cells with fewer citing documents than this are flagged


def mem_available_gb():
    with open('/proc/meminfo') as f:
        for line in f:
            if line.startswith('MemAvailable'):
                return int(line.split()[1]) / 1e6
    return 0.0


def wait_memory(need=6.0, timeout=1800):
    """Block until MemAvailable >= need GB (other agents run 4 GB DuckDB jobs); give up after timeout."""
    t0 = time.time()
    while mem_available_gb() < need:
        if time.time() - t0 > timeout:
            raise SystemExit(f'MemAvailable stayed below {need} GB')
        time.sleep(20)


def connect(read_only=True, path=BASE):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / 'tmp').mkdir(exist_ok=True)
    con = duckdb.connect(str(path), read_only=read_only)
    con.execute(f"SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='2GB'; "
                f"SET temp_directory='{SCRATCH / 'tmp'}'; SET preserve_insertion_order=false")
    return con


def out(name):
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT / name


def write(con, sql, name):
    """COPY a query to out/<name>.csv and return its rows."""
    p = out(name + '.csv')
    con.execute(f"COPY ({sql}) TO '{p}' (HEADER, DELIMITER ',')")
    return con.execute(sql).fetchall()


def boot_ratio(num, den, B=500, seed=11):
    """95% interval of sum(num)/sum(den) under a bootstrap over citing documents (one row per document).
    Poisson(1) weights stand in for resampling with replacement (the 'Poisson bootstrap'); returns (lo, hi)."""
    import numpy as np
    num = np.asarray(num, float)
    den = np.asarray(den, float)
    rng = np.random.default_rng(seed)
    vals = np.empty(B)
    for b in range(B):
        w = rng.poisson(1.0, len(num))
        d = (w * den).sum()
        vals[b] = (w * num).sum() / d if d else np.nan
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))


def gini(counts):
    """Gini coefficient (0 = every item cited equally often, 1 = one item takes every citation) of a count vector."""
    import numpy as np
    x = np.sort(np.asarray(counts, float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float('nan')
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def gini_sql(col):
    """Gini of a column of non-negative counts inside an aggregate subquery: 1 - 2*sum(cum share)/n + 1/n form.
    Used as: SELECT {gini_sql('n')} FROM (SELECT n, row_number() over (order by n) i, count(*) over () N ...)"""
    return f"(2.0*sum(i*{col})/(max(N)*sum({col})) - (max(N)+1.0)/max(N))"
