"""Withdraw the authored claims key_cited_articles first minted with the record's source in place of the author
(2026-11-03: 'diss-person:JSTOR', 'diss-person:Crossref'; a tuple gained a field and the author loop read the
source). The DOI works it minted are right and stay. A rerun of key_cited_articles mints the claims anew.

    python3 data/identifiers/cited-articles-2026-11-03/repair-claims.py
    python3 scripts/identifiers.py apply data/identifiers/cited-articles-2026-11-03/repair-proposal.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import RETIRED, State, materialise  # noqa: E402

state = State.load(ROOT / 'data/identifiers')
bad = sorted((k for k, r in state.relation.items() if r['subject'] in ('diss-person:JSTOR', 'diss-person:Crossref')
              and state.keys[k]['status'] not in RETIRED), key=lambda k: int(k[2:]))
ops = [dict(event='withdraw', key=k, basis='claim minted with the record source in place of the author (key_cited_articles bug)')
       for k in bad]
materialise(state, dict(basis='repair', ops=ops), 'dry-run', 'dry-run')
(HERE / 'repair-proposal.json').write_text(json.dumps(dict(
    basis="key_cited_articles' first claims named the record source as author: withdrawn", decided_by='build', ops=ops)) + '\n')
print(len(ops), 'claims withdrawn')
