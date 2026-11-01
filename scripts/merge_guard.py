"""Keys that rule merges must not touch (2026-11-01, after the Fable review of the core KG).

A rule merge (`identifiers.plan` with a merge_ok) settles that two keys are one person. It must not settle a
question an earlier slice left open: the LC-to-Wikidata rule merged Robert J. C. Young's ORCID key into
p-4045 'Young, Robert' while the LC canon review still held p-4045 and p-4046 as sharing his authority
(the outcome was right on the works, but a rule decided a held question). So a merge is refused when any
key it would touch is
- a pooled canon name: LC's books disagree about who it is (canon rerun5 `books_disagree`), or a review
  says it holds several people ('Miller, James');
- named in an open identity conflict in any committed review queue under data/identifiers/ (shared LC
  authority, QID on several keys, held merge, key holding a different QID, failed check, canon key claimed
  by several records), unless `review-decisions.json` records the conflict as decided.
Probable links ('probable_dissertation_qid_agrees', 'registry_phd_tie_probable') are open questions, not
conflicts, and do not block. Queues listed in `superseded-queues.json` (a later run of the same build
re-evaluated them) are ignored, and a conflict whose keys now resolve to one key is settled (2026-11-01:
stale items from four AHA runs and three LC-to-Wikidata runs blocked 278 keys).

    from merge_guard import guarded
    ops, assign, held = plan(state, clusters, guarded(state, merge_ok))
"""
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUES = ROOT / 'data/identifiers'
DECISIONS = QUEUES / 'review-decisions.json'
SUPERSEDED = QUEUES / 'superseded-queues.json'
POOLED_RUN = ROOT / 'data/field-research/lc-authorities-2026-10-30/canon-rerun5-2026-10-31/canon-people-lc.csv'
CONFLICTS = {'shared_lcnaf', 'qid_on_several_canon_keys', 'merge_candidate', 'key_holds_different_qid',
             'check_failed', 'qid_agrees_with_atlas_keyed_canon', 'canon_key_claimed_by_several_records',
             'canon_key_claimed_by_several_theses', 'anchor_on_several_records', 'anchor_on_several_theses',
             'anchor_on_several_individuals'}
KEY = re.compile(r'"(p-[1-9][0-9]*)"')
ANCHOR = re.compile(r'"(diss-person:[^"]+|lcnaf:[^"]+|wd:Q[0-9]+|orcid:[^"]+|aha[a-z-]*:[^"]+)"')


def pooled_keys(state):
    """Canon keys that hold several people: LC's books disagree (rerun5 `books_disagree`), or a review says so."""
    pooled = set()
    if POOLED_RUN.exists():
        with POOLED_RUN.open(newline='', encoding='utf-8') as f:
            pooled = {k for r in csv.DictReader(f) if r['outcome'] == 'books_disagree'
                      for k in state.lookup(f"diss-person:{r['graph_key']}")}
    # Pooled by review though LC resolves them: the timeline-canon reading bridge notes that 'Miller, James'
    # also holds James Miller (Democracy is in the Streets) and others.
    return pooled | set(state.lookup('diss-person:miller|james'))


def decided(path=DECISIONS):
    """Conflicts recorded as decided: [{"kind", "keys", "decision", "basis", "date"}]; their keys are released."""
    if not path.exists():
        return set()
    return {(d['kind'], tuple(sorted(d['keys']))) for d in json.loads(path.read_text())}


def conflict_keys(state, queues=QUEUES, decisions=DECISIONS):
    """Current keys named in open identity conflicts in the committed review queues."""
    done, out = decided(decisions), set()
    old = set(json.loads(SUPERSEDED.read_text())['superseded']) if queues == QUEUES and SUPERSEDED.exists() else set()
    for path in sorted(glob.glob(str(queues / '**' / '*queue*.json'), recursive=True)):
        if Path(path).relative_to(queues).as_posix() in old:
            continue
        try:
            items = json.loads(Path(path).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for item in items if isinstance(items, list) else []:
            if item.get('kind') not in CONFLICTS:
                continue
            text = json.dumps(item, ensure_ascii=False)
            keys = {c for k in KEY.findall(text) for c in state.lookup(k)}
            keys |= {state.anchor[a] for a in ANCHOR.findall(text) if a in state.anchor}
            if len(keys) > 1 or item['kind'] not in ('merge_candidate', 'shared_lcnaf', 'qid_on_several_canon_keys'):
                if (item['kind'], tuple(sorted(keys))) not in done:
                    out |= keys
    return out


def blocked_keys(state):
    return pooled_keys(state) | conflict_keys(state)


def guarded(state, merge_ok, blocked=None):
    """merge_ok, refusing any merge that touches a pooled key or a key in an open conflict."""
    blocked = blocked_keys(state) if blocked is None else blocked

    def ok(cluster, keys):
        return not (set(keys) & blocked) and merge_ok(cluster, keys)
    ok.blocked = blocked
    return ok
