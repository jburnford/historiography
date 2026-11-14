"""The classifier's remaining `review` positions as a Qwen labelling queue, in priority order (2026-11-13).

Owner (2026-11-13): go on running Qwen over the rest of the undecided middle. Input: the final classifier's production
file (build/linkclf-2026-11-13/out-final/classified.csv.gz, decision = review) minus the positions Qwen has already read
(data/graph/scored-links/qwen-labels.csv.gz). Tiers (first to last):
  1  the classifier's top candidate holds a thesis / AHA / LC anchor (diss-person, diss-author, aha-phd, aha, lcnaf)
     AND the position's work is cited by a thesis (cites source thesis / thesis-matched); strata other than
     single-unmeasured and single-initials
  2  other single-unique, then single-2-5
  3  other multi, then single-6-25, then single-26+
  4  single-unmeasured, then single-initials (initials-only printed names)
Inside a tier: anchored before not, thesis-cited before not, then position id. Anchors and citations are read from the
graph snapshot the scorer used (SL_SCRATCH/graph), so they match the candidate lists the dossiers show.
Writes (OUT dir): rest-queue.csv (all, ordered, with tier and chunk), rest-NN-positions.csv (item, pid) per chunk of
--chunk positions, rest-sample.csv (label_links_qwen.py `write` sample columns; weight 1: the review set is read in full).
Metadata only.
"""
import argparse
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from label_links_qwen import has_fact  # noqa: E402
ANCH = ('diss-person', 'diss-author', 'aha-phd', 'aha', 'lcnaf')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--classified', default=str(ROOT / 'build/linkclf-2026-11-13/out-final/classified.csv.gz'))
    ap.add_argument('--qwen', default=str(ROOT / 'data/graph/scored-links/qwen-labels.csv.gz'))
    ap.add_argument('--graph', default=str(ROOT / 'build/session-scratch-2026-11-13/scored/graph'))
    ap.add_argument('--decided', default=str(ROOT / 'build/session-scratch-2026-11-13/scored/prod-decided.parquet'))
    ap.add_argument('--out', default=str(ROOT / 'build/linkclf-2026-11-13/qwen-rest'))
    ap.add_argument('--chunk', type=int, default=40000)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    C = pd.read_csv(a.classified, usecols=['position', 'work', 'role', 'printed_name', 'decision', 'person_key', 'stratum'])
    C = C[C.decision == 'review']
    seen = set(pd.read_csv(a.qwen, usecols=['position']).position)
    C = C[~C.position.isin(seen)].copy()
    db = duckdb.connect()
    db.execute("SET memory_limit='3GB'; SET threads=3")
    anch = set(db.execute(f"""SELECT DISTINCT key FROM (SELECT key, unnest(anchors) a FROM '{a.graph}/person.parquet')
                              WHERE split_part(a, ':', 1) IN {ANCH}""").df().key)
    db.register('ww', pd.DataFrame({'work': C.work.unique()}))
    cited = set(db.execute(f"""SELECT DISTINCT c."to" AS work FROM '{a.graph}/cites.parquet' c JOIN ww ON ww.work = c."to"
                               WHERE c.source IN ('thesis', 'thesis-matched')""").df().work)
    C['anchored'] = C.person_key.isin(anch)
    C['thesis_cited'] = C.work.isin(cited)
    order = {'single-unique': (2, 0), 'single-2-5': (2, 1), 'multi': (3, 0), 'single-6-25': (3, 1), 'single-26+': (3, 2),
             'single-unmeasured': (4, 0), 'single-initials': (4, 1)}
    t = C.stratum.map(lambda s: order[s][0])
    sub = C.stratum.map(lambda s: order[s][1])
    top = C.anchored & C.thesis_cited & (t < 4)
    C['tier'] = t.where(~top, 1)
    C['sub'] = sub.where(~top, 0)
    C = C.sort_values(['tier', 'sub', 'anchored', 'thesis_cited', 'position'], ascending=[True, True, False, False, True]).reset_index(drop=True)
    C['chunk'] = C.index // a.chunk + 1
    C['item'] = 'Q' + C.position.astype(str)
    C.drop(columns=['sub', 'decision']).to_csv(out / 'rest-queue.csv', index=False)
    for k, g in C.groupby('chunk'):
        g.rename(columns={'position': 'pid'})[['item', 'pid']].to_csv(out / f'rest-{k:02d}-positions.csv', index=False)
    D = db.execute(f"""SELECT pid, tbl, rg, n, freq, neg, decision, rule_state, rule_key, network, venue, topic, cites, aff
                       FROM '{a.decided}'""").df()
    single = (D.n == 1) & (D.neg.astype(str) == 'none')
    D['nofact'] = single & ~has_fact(D)            # label_links_qwen.sample's definition (training down-weights these)
    S = C.drop(columns=['decision']).rename(columns={'position': 'pid'}).merge(D, on='pid', how='left')
    S['cell'] = 'rest|tier' + S.tier.astype(str) + '|' + S.stratum
    S['band'] = S.stratum
    S['weight'] = 1.0
    S[['item', 'pid', 'cell', 'band', 'rg', 'role', 'tbl', 'n', 'freq', 'decision', 'rule_state', 'rule_key', 'nofact', 'weight']].to_csv(out / 'rest-sample.csv', index=False)
    rep = dict(review_total=int(C.shape[0] + len(seen & set(pd.read_csv(a.classified, usecols=['position', 'decision']).query("decision == 'review'").position))),
               already_read=None, remaining=int(len(C)), chunks=int(C.chunk.max()),
               by_tier={int(k): int(v) for k, v in C.tier.value_counts().sort_index().items()},
               by_tier_stratum={f'{k[0]}|{k[1]}': int(v) for k, v in C.groupby(['tier', 'stratum']).size().items()},
               by_chunk_tier={f'{k[0]:02d}|{k[1]}': int(v) for k, v in C.groupby(['chunk', 'tier']).size().items()},
               anchored=int(C.anchored.sum()), thesis_cited=int(C.thesis_cited.sum()), no_decided_row=int(S.rg.isna().sum()))
    rep['already_read'] = rep['review_total'] - rep['remaining']
    json.dump(rep, open(out / 'rest-queue.json', 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
